"""Command plugin discovery.

Command plugins are registered by ``mongo-x-ray-*`` distributions through the
``mongo_x_ray.plugins`` entry-point group (e.g. ``mongo-x-ray-ftdc``,
``mongo-x-ray-healthcheck``, ``mongo-x-ray-log``, ``mongo-x-ray-gmd``). There
are no built-in plugins in the core distribution; every command comes from an
installed plugin package.
"""

from importlib.metadata import entry_points

from mongo_x_ray.plugin import ENTRY_POINT_GROUP, Plugin

BUILTIN_PLUGINS: list[type[Plugin]] = []


def discover_plugins() -> dict[str, Plugin]:
    """Return the installed command plugins keyed by subcommand name."""
    plugins: dict[str, Plugin] = {}
    for plugin_cls in BUILTIN_PLUGINS:
        plugins[plugin_cls.name] = plugin_cls()
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        plugin_cls = ep.load()
        plugins[plugin_cls.name] = plugin_cls()
    return plugins
