"""Command plugin discovery.

Command plugins are registered by ``mongo-x-ray-*`` distributions through the
``mongo_x_ray.plugins`` entry-point group (e.g. ``mongo-x-ray-ftdc``,
``mongo-x-ray-hc``, ``mongo-x-ray-log``, ``mongo-x-ray-gmd``). There are no
built-in plugins in the core distribution; every command comes from an
installed plugin package.

For development a ``plugins/`` folder next to the core package can hold local
checkouts (symlinks or clones of the plugin repositories). Plugins found there
are preferred over installed entry-point plugins with the same name, so all
components can be developed and tested from a single core checkout. Library
plugins without a CLI command are detected the same way: their ``src/`` is put
on ``sys.path`` so the other plugins import the local checkout instead of the
installed one. (``mongo-x-ray-risk`` is a hybrid: it ships the ``ingest``
command while the analysis plugins still import it as a library for risk
enrichment.)

Installed plugins are gated on a trusted install origin: the ``mongo_x_ray.plugins``
entry-point group is an open namespace, so any package (even one not named
``mongo-x-ray-*``) could register a command. Origins are checked *before* the
entry point is imported, so untrusted code is never executed: local editable
installs, git checkouts under ``TRUSTED_GIT_OWNERS``, and PyPI/archive
installs of allowlisted names (``KNOWN_PLUGINS``) are trusted; everything
else is skipped with a warning unless ``MONGO_X_RAY_TRUST_ALL_PLUGINS=1``.
"""

import importlib
import json
import logging
import os
import re
import sys
from importlib.metadata import Distribution, distributions
from pathlib import Path

from mongo_x_ray.plugin import ENTRY_POINT_GROUP, Plugin
from mongo_x_ray.utils import yellow

logger = logging.getLogger(__name__)

BUILTIN_PLUGINS: list[type[Plugin]] = []

#: Optional override for the dev ``plugins/`` folder (mainly for tests).
PLUGINS_DIR_ENV = "MONGO_X_RAY_PLUGINS"

#: Canonical plugin distribution names (used for the PyPI/archive trust path).
KNOWN_PLUGINS = frozenset(
    {
        "mongo-x-ray-ftdc",
        "mongo-x-ray-log",
        "mongo-x-ray-gmd",
        "mongo-x-ray-hc",
        "mongo-x-ray-risk",
    }
)

#: Git owners whose plugin repositories are trusted install origins.
TRUSTED_GIT_OWNERS = frozenset({"mongodb-ps", "zhangyaoxing"})

#: Set to 1 to load installed plugins from any origin without warning.
TRUST_ALL_ENV = "MONGO_X_RAY_TRUST_ALL_PLUGINS"


def _plugins_folder() -> Path:
    """Return the dev ``plugins/`` folder holding local plugin checkouts."""
    override = os.environ.get(PLUGINS_DIR_ENV)
    if override:
        return Path(override)
    # src/mongo_x_ray/plugins/__init__.py -> core repository root
    return Path(__file__).resolve().parent.parent.parent.parent / "plugins"


def _local_import_packages(package_dir: Path) -> list[Path]:
    """Return the ``mongo_x_ray_*`` import packages under ``package_dir/src``."""
    src_dir = package_dir / "src"
    if not src_dir.is_dir():
        return []
    return [
        candidate
        for candidate in sorted(src_dir.iterdir())
        if candidate.is_dir() and candidate.name.startswith("mongo_x_ray") and not candidate.name.endswith(".egg-info")
    ]


def _load_local_plugin(package_dir: Path) -> type[Plugin] | None:
    """Import a command plugin from a local checkout and return its Plugin class."""
    for candidate in _local_import_packages(package_dir):
        if not (candidate / "plugin.py").is_file():
            continue
        src_dir = candidate.parent
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        try:
            module = importlib.import_module(f"{candidate.name}.plugin")
        except Exception as exc:
            logger.warning("Skipping plugin checkout %s: %s", candidate, exc)
            continue
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Plugin) and obj is not Plugin:
                return obj
    return None


def _dist_origin(dist: Distribution) -> str:
    """Return a short human-readable install origin for a distribution.

    Reads pip's ``direct_url.json`` (PEP 610) when present: local editable
    installs, VCS checkouts and archives are reported distinctly. Anything
    else is reported as unknown.
    """
    try:
        raw = dist.read_text("direct_url.json")
    except Exception:
        raw = None
    if not raw:
        return "unknown (no direct_url.json)"
    try:
        info = json.loads(raw)
    except Exception:
        return "unknown (unparsable direct_url.json)"
    url = info.get("url", "")
    if info.get("dir_info", {}).get("editable"):
        return f"local editable: {url}"
    vcs = info.get("vcs_info", {}).get("vcs")
    if vcs:
        return f"vcs({vcs}): {url}"
    return f"archive: {url}"


def _is_trusted(dist_name: str, origin: str) -> bool:
    """Whether an installed distribution is an allowed plugin source.

    Trusted sources:
    - local editable installs (an explicit developer action);
    - git checkouts hosted under ``TRUSTED_GIT_OWNERS`` (the owner is the
      trust anchor — a GitHub URL cannot be squatted);
    - archive/index installs (e.g. from PyPI) of names in ``KNOWN_PLUGINS``.
      PyPI names are globally unique, so once the official plugin occupies
      the name, an index install of that name is the official package; the
      allowlist keeps typosquats under look-alike names out.

    Anything else is refused. Set ``TRUST_ALL_ENV`` to bypass the check.
    """
    if os.environ.get(TRUST_ALL_ENV):
        return True
    if origin.startswith("local editable"):
        return True
    match = re.search(r"github\.com[/:]([^/]+)/([^/#?]+)", origin)
    if match and match.group(1) in TRUSTED_GIT_OWNERS:
        return True
    if origin.startswith(("archive:", "unknown (")):
        return dist_name in KNOWN_PLUGINS
    return False


def _local_checkout_srcs() -> list[Path]:
    """Return the resolved ``src/`` dirs of the local plugin checkouts."""
    local_dir = _plugins_folder()
    if not local_dir.is_dir():
        return []
    return [entry.resolve() for entry in local_dir.iterdir() if (entry / "src").is_dir()]


def _dist_from_local_checkout(dist: Distribution, checkout_srcs: list[Path]) -> bool:
    """Whether a distribution lives inside a local plugin checkout.

    ``pip install -e`` leaves a ``*.egg-info`` build artifact in the
    checkout's ``src/``, which ``distributions()`` then reports as a separate
    distribution without PEP 610 origin metadata. Those are the same code as
    the (already trusted) local checkout, so they are ignored here.
    """
    if not checkout_srcs:
        return False
    try:
        located = Path(str(dist.locate_file(""))).resolve()
    except Exception:
        return False
    return any(located == src or located.is_relative_to(src) for src in checkout_srcs)


def discover_plugins() -> dict[str, Plugin]:
    """Return the command plugins keyed by subcommand name.

    Local checkouts under ``plugins/`` take precedence over installed
    entry-point plugins with the same name. Library packages without a CLI
    command (e.g. a knowledge base) are detected and put on ``sys.path`` too.
    Installed entry points are gated on a trusted install origin *before*
    import, so untrusted distributions are skipped without executing them.
    """
    plugins: dict[str, Plugin] = {}
    for plugin_cls in BUILTIN_PLUGINS:
        plugins[plugin_cls.name] = plugin_cls()

    local_dir = _plugins_folder()
    if local_dir.is_dir():
        checkouts = sorted(entry for entry in local_dir.iterdir() if entry.is_dir())
        # Put every local checkout's src/ on sys.path before importing any of
        # them, so plugins can import sibling local plugins (including library
        # plugins such as the risk register) regardless of the folder scan
        # order (e.g. gmd depends on hc but sorts before it).
        for entry in checkouts:
            src_dir = entry / "src"
            if src_dir.is_dir() and str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
        # Report detected library packages (no plugin.py) as local checkouts too.
        for entry in checkouts:
            for pkg in _local_import_packages(entry):
                if not (pkg / "plugin.py").is_file():
                    logger.debug("Using local library package %r from %s", pkg.name, entry)
        for entry in checkouts:
            plugin_cls = _load_local_plugin(entry)
            if plugin_cls is not None:
                logger.debug("Using local plugin %r from %s", plugin_cls.name, entry)
                plugins[plugin_cls.name] = plugin_cls()

    # Installed entry-point plugins, gated on a trusted install origin so that
    # untrusted code is never imported. Build artifacts of the local checkouts
    # (src/*.egg-info) are ignored — they are the same code, already loaded
    # through the trusted local path above.
    checkout_srcs = _local_checkout_srcs()
    for dist in distributions():
        if _dist_from_local_checkout(dist, checkout_srcs):
            continue
        dist_name = _dist_metadata(dist, "Name")
        origin = _dist_origin(dist)
        for ep in dist.entry_points:
            if ep.group != ENTRY_POINT_GROUP:
                continue
            if not _is_trusted(dist_name, origin):
                logger.warning(
                    yellow("Skipping untrusted plugin %r (%s from %s) — set %s=1 to allow"),
                    ep.name,
                    dist_name,
                    origin,
                    TRUST_ALL_ENV,
                )
                continue
            plugin_cls = ep.load()
            if plugin_cls.name not in plugins:
                plugins[plugin_cls.name] = plugin_cls()
    return plugins


def _local_checkout_description(checkout: Path, short: str) -> str:
    """Best-effort description from a local checkout's pyproject.toml."""
    pyproject = checkout / "pyproject.toml"
    if pyproject.is_file():
        match = re.search(
            r'^description\s*=\s*"([^"]+)"',
            pyproject.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if match:
            return match.group(1)
    return short


def _dist_metadata(dist: Distribution, key: str, default: str = "") -> str:
    """Read one ``email.message.Message`` header from a distribution's metadata.

    ``dist.metadata`` is typed as ``PackageMetadata`` which does not declare
    ``.get()``, so fall back to subscript access and tolerate a missing header.
    """
    try:
        value = dist.metadata[key]
    except KeyError:
        return default
    return value if isinstance(value, str) else default


def discover_library_plugins() -> dict[str, str]:
    """Return library plugins (no CLI command): ``{short_name: description}``.

    Library plugins are ``mongo-x-ray-*`` packages that register no command
    in the ``mongo_x_ray.plugins`` entry-point group. They are found either
    installed or as a local checkout under ``plugins/``.
    """
    library: dict[str, str] = {}
    checkout_srcs = _local_checkout_srcs()
    for dist in distributions():
        if _dist_from_local_checkout(dist, checkout_srcs):
            continue
        name = _dist_metadata(dist, "Name")
        if not name.startswith("mongo-x-ray-") or name == "mongo-x-ray":
            continue
        if any(ep.group == ENTRY_POINT_GROUP for ep in dist.entry_points):
            continue
        origin = _dist_origin(dist)
        if not _is_trusted(name, origin):
            logger.warning(
                yellow("Untrusted library plugin %r (%s) — set %s=1 to allow"),
                name,
                origin,
                TRUST_ALL_ENV,
            )
        library[name[len("mongo-x-ray-") :]] = _dist_metadata(dist, "Summary", name)

    local_dir = _plugins_folder()
    if local_dir.is_dir():
        for entry in sorted(p for p in local_dir.iterdir() if p.is_dir()):
            for pkg in _local_import_packages(entry):
                if (pkg / "plugin.py").is_file():
                    continue
                short = pkg.name[len("mongo_x_ray_") :]
                if short not in library:
                    library[short] = _local_checkout_description(entry, short)
    return library
