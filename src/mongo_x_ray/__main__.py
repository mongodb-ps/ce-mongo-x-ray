"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import argparse
import logging
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from mongo_x_ray.plugin import Plugin
from mongo_x_ray.plugins import discover_plugins

logger = logging.getLogger(__name__)


def setup_parser():
    """Build the command-line parser from the discovered command plugins."""
    plugins = discover_plugins()

    def _command_line(name, plugin):
        label = name if not plugin.aliases else f"{name} ({', '.join(plugin.aliases)})"
        return f"  {label:<20} {plugin.help}"

    if plugins:
        command_lines = "\n".join(_command_line(name, plugin) for name, plugin in sorted(plugins.items()))
    else:
        command_lines = "  (none - install a mongo-x-ray-* plugin)"
    parser = argparse.ArgumentParser(
        prog="x-ray",
        description=(
            "MongoDB analysis and diagnostics. The available commands are provided "
            "by the mongo-x-ray-* plugins (installed, or local checkouts under "
            "plugins/)."
        ),
        epilog=f"""
Available commands (from the installed mongo-x-ray-* plugins):
{command_lines}

Run 'x-ray <command> --help' for usage and examples of a specific command.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-q",
        "--quiet",
        help='Quiet mode. Defaults to "false".',
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--config",
        help='Path to configuration file. Defaults to "config.json".',
        type=str,
        default=None,
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Show the version of x-ray and exit.",
        action="store_true",
        default=False,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute", required=False)
    for plugin in plugins.values():
        subparser = subparsers.add_parser(
            plugin.name,
            aliases=plugin.aliases,
            help=plugin.help,
            description=plugin.description,
            epilog=plugin.epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        plugin.add_arguments(subparser)

    return parser


def version_command(_args):
    """Print current package version."""
    try:
        # Distribution name matches [project].name in pyproject.toml
        print(pkg_version("mongo-x-ray"))
    except PackageNotFoundError:
        # Fallback for source tree without installed metadata
        print("development")
    return 0


def resolve_plugin(plugins: dict[str, Plugin], command: str) -> Plugin | None:
    """Return the plugin for *command*, following subcommand aliases."""
    plugin = plugins.get(command)
    if plugin is None:
        plugin = next((p for p in plugins.values() if command in p.aliases), None)
    return plugin


def main():
    _original_excepthook = sys.excepthook

    def _quiet_excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("KeyboardInterrupt received.")
            sys.exit(130)
        _original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = _quiet_excepthook

    parser = setup_parser()
    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        return version_command(args)

    # Require command if --version not specified
    if not args.command:
        parser.error("the following arguments are required: command")

    if args.quiet:
        logger.setLevel(logging.FATAL)

    plugins = discover_plugins()
    plugin = resolve_plugin(plugins, args.command)
    if plugin is None:
        logger.error("Unknown command: %s", args.command)
        return 1
    return plugin.run(args)


if __name__ == "__main__":
    # freeze_support must be called before any subprocesses are spawned, and
    # only when running as a frozen executable (PyInstaller) — keeping it here
    # ensures it runs before main() without executing on import.
    import multiprocessing

    multiprocessing.freeze_support()

    raise SystemExit(main())
