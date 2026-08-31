"""
Copyright (c) 2026 MongoDB Inc.

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
from mongo_x_ray.plugins import discover_library_plugins, discover_plugins

logger = logging.getLogger(__name__)


def setup_parser():
    """Build the command-line parser from the discovered command plugins."""
    plugins = discover_plugins()

    # The subcommands (and their names/aliases) are already listed by argparse
    # in the positional arguments section, so the epilog only adds the library
    # plugins and a pointer to per-command help.
    epilog = ""
    if not plugins:
        epilog += "No plugins installed. Install a mongo-x-ray-* plugin to enable commands.\n"
    library = discover_library_plugins()
    if library:
        library_lines = "\n".join(f"  {name:<14} {description}" for name, description in sorted(library.items()))
        epilog += f"Library plugins (no CLI command):\n{library_lines}\n"
    epilog += "Run 'x-ray <command> --help' for usage and examples of a specific command."
    parser = argparse.ArgumentParser(
        prog="x-ray",
        description=(
            "MongoDB analysis and diagnostics. The available commands are provided "
            "by the mongo-x-ray-* plugins (installed, or local checkouts under "
            "plugins/)."
        ),
        epilog=epilog,
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
        subparser.add_argument(
            "--version",
            dest="plugin_version",
            action="store_true",
            help=f"Show the {plugin.name} plugin version and exit.",
        )

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


def _plugin_version_requested(argv: list[str]) -> Plugin | None:
    """Return the plugin for an ``x-ray <command> ... --version`` invocation.

    This runs before argparse so commands with required positional arguments
    (e.g. ``ftdc_path``) can still report their version. The ``--version`` flag
    only counts when it appears *after* the subcommand; a top-level
    ``-v``/``--version`` before the subcommand still reports the core version.
    """
    if "--version" not in argv:
        return None
    command: str | None = None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in ("-c", "--config"):
            i += 2
            continue
        if arg.startswith("-"):
            i += 1
            continue
        command = arg
        break
    if command is None or "--version" not in argv[i + 1 :]:
        return None
    return resolve_plugin(discover_plugins(), command)


def main():
    _original_excepthook = sys.excepthook

    def _quiet_excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            logger.info("KeyboardInterrupt received.")
            sys.exit(130)
        _original_excepthook(exc_type, exc_value, exc_tb)

    sys.excepthook = _quiet_excepthook

    # Handle `x-ray <command> --version` before argparse validates the
    # command's required positional arguments.
    version_plugin = _plugin_version_requested(sys.argv)
    if version_plugin is not None:
        print(version_plugin.version())
        return 0

    parser = setup_parser()
    args = parser.parse_args()

    if args.command:
        plugins = discover_plugins()
        plugin = resolve_plugin(plugins, args.command)
        if plugin is None:
            logger.error("Unknown command: %s", args.command)
            return 1
        # x-ray <command> --version shows the plugin's own version.
        if args.plugin_version:
            print(plugin.version())
            return 0
        if args.quiet:
            logger.setLevel(logging.FATAL)
        return plugin.run(args)

    # --version without a command shows the core version.
    if args.version:
        return version_command(args)

    parser.error("the following arguments are required: command")
    return 2  # unreachable: parser.error() raises SystemExit(2)


if __name__ == "__main__":
    # freeze_support must be called before any subprocesses are spawned, and
    # only when running as a frozen executable (PyInstaller) — keeping it here
    # ensures it runs before main() without executing on import.
    import multiprocessing

    multiprocessing.freeze_support()

    raise SystemExit(main())
