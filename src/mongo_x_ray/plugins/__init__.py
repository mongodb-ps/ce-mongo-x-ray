"""Command plugin discovery.

Command plugins are registered by ``mongo-x-ray-*`` distributions through the
``mongo_x_ray.plugins`` entry-point group (e.g. ``mongo-x-ray-ftdc``,
``mongo-x-ray-hc``, ``mongo-x-ray-log``, ``mongo-x-ray-gmd``). There are no
built-in plugins in the core distribution; every command comes from an
installed plugin package.

For development a ``plugins/`` folder next to the core package can hold local
checkouts (symlinks or clones of the plugin repositories). Plugins found there
are preferred over installed entry-point plugins with the same name, so all
components can be developed and tested from a single core checkout.
"""

import importlib
import logging
import os
import sys
from importlib.metadata import entry_points
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


def _load_local_plugin(package_dir: Path) -> type[Plugin] | None:
    """Import a plugin package from a local checkout and return its Plugin class."""
    src_dir = package_dir / "src"
    if not src_dir.is_dir():
        return None
    for candidate in sorted(src_dir.iterdir()):
        if not candidate.is_dir() or not candidate.name.startswith("mongo_x_ray"):
            continue
        if candidate.name.endswith(".egg-info") or not (candidate / "plugin.py").is_file():
            continue
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        try:
            module = importlib.import_module(f"{candidate.name}.plugin")
        except Exception as exc:  # pylint: disable=broad-exception-caught
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
    entry-point plugins with the same name.
    """
    plugins: dict[str, Plugin] = {}
    for plugin_cls in BUILTIN_PLUGINS:
        plugins[plugin_cls.name] = plugin_cls()

    local_dir = _plugins_folder()
    if local_dir.is_dir():
        # Put every local checkout's src/ on sys.path before importing any of
        # them, so plugins can import sibling local plugins regardless of the
        # folder scan order (e.g. gmd depends on hc but sorts before it).
        for entry in sorted(local_dir.iterdir()):
            if entry.is_dir():
                src_dir = entry / "src"
                if src_dir.is_dir() and str(src_dir) not in sys.path:
                    sys.path.insert(0, str(src_dir))
        for entry in sorted(local_dir.iterdir()):
            if not entry.is_dir():
                continue
            plugin_cls = _load_local_plugin(entry)
            if plugin_cls is not None:
                logger.debug("Using local plugin %r from %s", plugin_cls.name, entry)
                plugins[plugin_cls.name] = plugin_cls()

    for ep in entry_points(group=ENTRY_POINT_GROUP):
        plugin_cls = ep.load()
        if plugin_cls.name not in plugins:
            plugins[plugin_cls.name] = plugin_cls()
    return plugins
