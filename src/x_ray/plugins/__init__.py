"""Built-in command plugins and plugin discovery.

The ``x_ray.plugins`` entry-point group lets additional ``x-ray-*``
distributions register their own command plugins; the built-in plugins
(log, gmd, healthcheck) are registered here explicitly so the CLI also
works from a source checkout without installed metadata. Other plugins
(e.g. ``x-ray-ftdc``) are discovered through the entry-point group.
"""

from importlib.metadata import entry_points

from x_ray.plugin import ENTRY_POINT_GROUP, Plugin
from x_ray.plugins.gmd import GmdPlugin
from x_ray.plugins.healthcheck import HealthcheckPlugin
from x_ray.plugins.log import LogPlugin

BUILTIN_PLUGINS = [LogPlugin, GmdPlugin, HealthcheckPlugin]


def discover_plugins() -> dict[str, Plugin]:
    """Return the installed command plugins keyed by subcommand name."""
    plugins: dict[str, Plugin] = {}
    for plugin_cls in BUILTIN_PLUGINS:
        plugins[plugin_cls.name] = plugin_cls()
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        plugin_cls = ep.load()
        plugins[plugin_cls.name] = plugin_cls()
    return plugins
