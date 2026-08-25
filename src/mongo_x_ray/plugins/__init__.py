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
"""

import importlib
import logging
import os
import re
import sys
from importlib.metadata import Distribution, distributions, entry_points
from pathlib import Path

from mongo_x_ray.plugin import ENTRY_POINT_GROUP, Plugin

logger = logging.getLogger(__name__)

BUILTIN_PLUGINS: list[type[Plugin]] = []

#: Optional override for the dev ``plugins/`` folder (mainly for tests).
PLUGINS_DIR_ENV = "MONGO_X_RAY_PLUGINS"


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


def discover_plugins() -> dict[str, Plugin]:
    """Return the command plugins keyed by subcommand name.

    Local checkouts under ``plugins/`` take precedence over installed
    entry-point plugins with the same name. Library packages without a CLI
    command (e.g. a knowledge base) are detected and put on ``sys.path`` too.
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

    for ep in entry_points(group=ENTRY_POINT_GROUP):
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
    for dist in distributions():
        name = _dist_metadata(dist, "Name")
        if not name.startswith("mongo-x-ray-") or name == "mongo-x-ray":
            continue
        if any(ep.group == ENTRY_POINT_GROUP for ep in dist.entry_points):
            continue
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
