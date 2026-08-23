"""Built-in command plugins and plugin discovery.

The ``x_ray.plugins`` entry-point group lets additional ``x-ray-*``
distributions register their own command plugins; the built-in plugins
(log, ftdc) are registered here explicitly so the CLI also works from a
source checkout without installed metadata.
"""

from importlib.metadata import entry_points

from x_ray.plugin import ENTRY_POINT_GROUP, Plugin
from x_ray.plugins.ftdc import FtdcPlugin
from x_ray.plugins.log import LogPlugin

BUILTIN_PLUGINS = [LogPlugin, FtdcPlugin]


def discover_plugins() -> dict[str, Plugin]:
    """Return the installed command plugins keyed by subcommand name."""
    plugins: dict[str, Plugin] = {}
    for plugin_cls in BUILTIN_PLUGINS:
        plugins[plugin_cls.name] = plugin_cls()
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        plugin_cls = ep.load()
        plugins[plugin_cls.name] = plugin_cls()
    return plugins
