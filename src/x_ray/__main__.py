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
import os
import re
import shutil
import webbrowser
from copy import deepcopy
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as pkg_version
from getpass import getpass
from pathlib import Path
from pymongo import MongoClient
from pymongo.uri_parser import parse_uri
from x_ray.utils import bold, green, load_config
from x_ray.healthcheck.framework import Framework as HealthCheckFramework
from x_ray.log_analysis.framework import Framework as LogAnalysisFramework
from x_ray.gmd_analysis.framework import Framework as GMDAnalysisFramework
from x_ray.ftdc_analysis.framework import Framework as FTDCAnalysisFramework

logger = logging.getLogger(__name__)


def _discover_paths(root: Path, glob_pattern: str) -> list[Path]:
    """Recursively search *root* for all directories containing files matching *glob_pattern*.

    Returns a list of directory paths, sorted by depth (shallowest first).
    """
    found: dict[str, Path] = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for f in filenames:
            if Path(f).match(glob_pattern):
                found[str(dirpath)] = Path(dirpath)
                break  # one match per directory is enough
    return sorted(found.values(), key=lambda p: (len(p.relative_to(root).parts), str(p)))


_ILLEGAL_FILENAME_RE = re.compile(r'[<>:"/\\|?*]')


def _sanitize_filename(name: str) -> str:
    """Replace characters illegal in Windows filenames with underscores."""
    return _ILLEGAL_FILENAME_RE.sub("_", name).strip(". ")


def _rename_with_hostname(batch_folder: str, framework) -> str:
    """Rename *batch_folder* to include the hostname prefix if available.

    Returns the final folder path (renamed or original).
    """
    hostname = framework.hostname
    if hostname is None:
        return batch_folder
    batch_path = Path(batch_folder)
    if not batch_path.is_dir():
        return batch_folder
    safe_hostname = _sanitize_filename(hostname)
    if not safe_hostname:
        return batch_folder
    new_name = f"{safe_hostname}-{batch_path.name}"
    new_path = batch_path.parent / new_name
    shutil.move(str(batch_path), str(new_path))
    logger.info("Renamed output folder to: %s", green(new_name))
    return str(new_path)


def utc_iso_datetime(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalize it to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def sample_rate(value: str) -> float:
    """Parse a sampling rate in the interval (0, 1]."""
    try:
        rate = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid sample rate: {value}") from exc
    if not 0 < rate <= 1:
        raise argparse.ArgumentTypeError("sample rate must be greater than 0 and at most 1")
    return rate


def setup_parser():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="X-Ray project for MongoDB analysis and diagnostics.",
        epilog="""
Examples:
  x-ray healthcheck mongodb://localhost:27017 -f html
  x-ray hc -s comprehensive -o /path/to/output/
  x-ray log /var/log/mongodb/mongod.log
  x-ray gmd /path/to/getMongoData_output.json
  x-ray ftdc /path/to/diagnostic.data

For more information on specific commands, use:
  x-ray healthcheck --help
  x-ray log --help
  x-ray gmd --help
  x-ray ftdc --help
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

    # Health check module
    hc_description = """
    Run comprehensive health checks on MongoDB deployments including replica sets and sharded clusters (Standalone instance is NOT supported!).
    The results will be output in the format specified (HTML or Markdown).
    """

    hc_epilog = """
    Examples:
      x-ray healthcheck mongodb://localhost:27017
      x-ray hc mongodb://user:password@mongodb0.example.com:27017/?authSource=admin
      x-ray hc -s default -f html -o /path/to/output/
    """

    hc_parser = subparsers.add_parser(
        "healthcheck",
        aliases=["hc"],
        help="Run health checks on MongoDB cluster",
        description=hc_description,
        epilog=hc_epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hc_parser.add_argument(
        "uri",
        nargs="?",
        help="MongoDB database URI. If not provided, you will be prompted to enter it.",
        type=str,
    )
    hc_parser.add_argument(
        "-s",
        "--checkset",
        help='Checkset to run. Defaults to "default".',
        type=str,
        default="default",
    )
    hc_parser.add_argument(
        "-o",
        "--output",
        help='Output folder path. Defaults to "output/".',
        type=str,
        default="output/",
    )
    hc_parser.add_argument(
        "-f",
        "--format",
        help='Output format (markdown/html/pdf). PDF also generates Markdown and HTML. Defaults to "html".',
        type=str,
        default="html",
        choices=["markdown", "html", "pdf"],
    )

    # Log analysis module
    log_description = """
    Analyze MongoDB log files to identify patterns, issues, and optimization opportunities.
    
    This command will process MongoDB log files and provide insights including:
    - Slow query analysis
    - Error pattern detection
    - Connection statistics
    - Operation distribution
    - Index usage suggestions
    
    The analysis will be output in the format specified (HTML or Markdown).
    """

    log_epilog = """
    Examples:
      x-ray log /var/log/mongodb/mongod.log
      x-ray log /var/log/mongodb/ 2026-07-20T08:00:00Z 2026-07-20T10:00:00Z
      x-ray log /path/to/mongod.log -f html -o /path/to/output/
    """

    log_parser = subparsers.add_parser(
        "log",
        help="Analyze MongoDB log files",
        description=log_description,
        epilog=log_epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    log_parser.add_argument("log_file", help="Path to the MongoDB log file or a folder of log files to analyze")
    log_parser.add_argument(
        "start_time",
        nargs="?",
        type=utc_iso_datetime,
        help="Inclusive UTC start time in ISO-8601 format. Defaults to the first log line.",
    )
    log_parser.add_argument(
        "end_time",
        nargs="?",
        type=utc_iso_datetime,
        help="Inclusive UTC end time in ISO-8601 format. Defaults to the last log line.",
    )
    log_parser.add_argument(
        "-s",
        "--checkset",
        help='Checkset to run. Defaults to "default".',
        type=str,
        default="default",
    )
    log_parser.add_argument(
        "-o",
        "--output",
        help='Output folder path. Defaults to "output/".',
        type=str,
        default="output/",
    )
    log_parser.add_argument(
        "-f",
        "--format",
        help='Output format (markdown/html/pdf). PDF also generates Markdown and HTML. Defaults to "html".',
        type=str,
        default="html",
        choices=["markdown", "html", "pdf"],
    )
    log_parser.add_argument(
        "-r",
        "--rate",
        help="Log sampling rate (e.g., 1 for all logs, 0.1 for 10% logs). Defaults to 1.",
        type=float,
        default=1.0,
    )
    log_parser.add_argument("--top", help="Top N slow queries. Defaults to 10.", type=int, default=10)
    log_parser.add_argument(
        "--discover",
        help="Recursively search the given path for a folder containing log files.",
        action="store_true",
        default=False,
    )

    gmd_epilog = """
    Examples:
      x-ray gmd /misc/getMongoData-output.json
      x-ray gmd /misc/getMongoData-output.json -f html -o /path/to/output/
    """

    gmd_parser = subparsers.add_parser(
        "gmd",
        help="Analyze getMongoData output files",
        description=log_description,
        epilog=gmd_epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gmd_parser.add_argument("gmd_file", help="Path to the getMongoData output file.")
    gmd_parser.add_argument(
        "-s",
        "--checkset",
        help='Checkset to run. Defaults to "default".',
        type=str,
        default="default",
    )
    gmd_parser.add_argument(
        "-o",
        "--output",
        help='Output folder path. Defaults to "output/".',
        type=str,
        default="output/",
    )
    gmd_parser.add_argument(
        "-f",
        "--format",
        help='Output format (markdown/html/pdf). PDF also generates Markdown and HTML. Defaults to "html".',
        type=str,
        default="html",
        choices=["markdown", "html", "pdf"],
    )

    # FTDC analysis module
    ftdc_description = """
    Analyze MongoDB Full Time Diagnostic Data Capture (FTDC) files.

    The input is a directory containing FTDC files.
    """
    ftdc_epilog = """
    Examples:
      x-ray ftdc /var/lib/mongo/diagnostic.data
      x-ray ftdc /var/lib/mongo/diagnostic.data 2026-06-17T08:00:00Z 2026-06-17T10:00:00Z
    """
    ftdc_parser = subparsers.add_parser(
        "ftdc",
        help="Analyze MongoDB FTDC files",
        description=ftdc_description,
        epilog=ftdc_epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ftdc_parser.add_argument("ftdc_path", help="Path to a directory containing FTDC files.")
    ftdc_parser.add_argument(
        "start_time",
        nargs="?",
        type=utc_iso_datetime,
        help="Inclusive UTC start time in ISO-8601 format. Defaults to the first data point.",
    )
    ftdc_parser.add_argument(
        "end_time",
        nargs="?",
        type=utc_iso_datetime,
        help="Inclusive UTC end time in ISO-8601 format. Defaults to the last data point.",
    )
    ftdc_parser.add_argument(
        "-s", "--checkset", help='Checkset to run. Defaults to "default".', type=str, default="default"
    )
    ftdc_parser.add_argument(
        "-o", "--output", help='Output folder path. Defaults to "output/".', type=str, default="output/"
    )
    ftdc_parser.add_argument(
        "-f",
        "--format",
        help='Output format (markdown/html/pdf). PDF also generates Markdown and HTML. Defaults to "html".',
        type=str,
        default="html",
        choices=["markdown", "html", "pdf"],
    )
    ftdc_parser.add_argument(
        "--svg",
        help="Reference SVG charts in the report instead of converting them to PNG.",
        action="store_true",
        default=False,
    )
    ftdc_parser.add_argument(
        "-r",
        "--rate",
        help="FTDC sampling rate. Defaults to 1 divided by the number of ingested files.",
        type=sample_rate,
        default=None,
    )
    ftdc_parser.add_argument(
        "--discover",
        help="Recursively search the given path for a folder containing FTDC files.",
        action="store_true",
        default=False,
    )

    return parser


def health_check_command(args):
    """Health check command"""
    uri = args.uri
    if uri is None:
        uri = input("Enter MongoDB URI: ")
    parsed_uri = parse_uri(uri)
    if parsed_uri["username"] is None or parsed_uri["password"] is None:
        username = input("Enter MongoDB username: ")
        password = getpass("Enter MongoDB password: ")
        parsed_uri["username"] = username
        parsed_uri["password"] = password
        client = MongoClient(uri, username=username, password=password)
    else:
        client = MongoClient(uri)
    try:
        config = load_config(args.config)["healthcheck"]
    except FileNotFoundError:
        logger.error("Config file not found: %s", args.config)
        logger.info("Please provide a valid path to config.json.")
        return 1

    checkset = args.checkset
    output_folder = args.output if args.output.endswith("/") else f"{args.output}/"
    framework = HealthCheckFramework(config)
    framework.run_checks(checkset, client=client, output_folder=output_folder, parsed_uri=parsed_uri)
    framework.output_results(output_folder=output_folder, fmt=args.format)
    return 0


def log_analysis_command(args):
    """Log analysis command"""
    log_path = Path(args.log_file)
    if args.discover:
        discovered = _discover_paths(log_path, "*.log*")
        if not discovered:
            logger.error("No folder containing log files (*.log*) found under: %s", args.log_file)
            return 1
        logger.info(bold(green(f"Discovered {len(discovered)} log folder(s) to process:")))
        for i, d in enumerate(discovered, 1):
            logger.info("  %d. %s", i, str(d))
    else:
        discovered = [log_path]

    if args.start_time and args.end_time and args.start_time > args.end_time:
        logger.error("Log start time must be before or equal to end time.")
        return 1

    try:
        config = load_config(args.config)["log"]
        config["sample_rate"] = args.rate
        config["item_config"]["TopSlowItem"]["top"] = args.top
    except FileNotFoundError:
        logger.error("Config file not found: %s", args.config)
        logger.info("Please provide a valid path to config.json.")
        return 1

    for log_path_item in discovered:
        if not log_path_item.exists():
            logger.error("Log path not found: %s", log_path_item)
            return 1
        logger.info("Analyzing log: %s", str(log_path_item))
        output_folder = args.output if args.output.endswith("/") else f"{args.output}/"
        framework = LogAnalysisFramework(
            str(log_path_item),
            deepcopy(config),
            start_time=args.start_time,
            end_time=args.end_time,
        )
        framework.run_logs_analysis(args.checkset, output_folder=output_folder)
        framework.output_results(output_folder=output_folder, fmt=args.format, open_browser=False)
        batch_folder = str(framework._get_output_folder(output_folder))
        final_folder = _rename_with_hostname(batch_folder, framework)
        if args.format in {"html", "pdf"}:
            html_file = Path(final_folder) / "report.html"
            if html_file.exists():
                webbrowser.open(f"file://{html_file.resolve()}")
    return 0


def gmd_alalysis_command(args):
    """getMongoData analysis command"""
    if not Path(args.gmd_file).is_file():
        logger.error("getMongoData output file not found: %s", args.gmd_file)
        return 1
    logger.info("Analyzing getMongoData output file: %s", args.gmd_file)
    try:
        config = load_config(args.config)["gmd"]
    except FileNotFoundError:
        logger.error("Config file not found: %s", args.config)
        logger.info("Please provide a valid path to config.json.")
        return 1

    checkset = args.checkset
    output_folder = args.output if args.output.endswith("/") else f"{args.output}/"
    framework = GMDAnalysisFramework(args.gmd_file, config)
    framework.run_gmd_analysis(checkset, output_folder=output_folder)
    framework.output_results(output_folder=output_folder, fmt=args.format)
    return 0


def ftdc_analysis_command(args):
    """FTDC analysis command."""
    ftdc_path = Path(args.ftdc_path)
    if args.discover:
        discovered = _discover_paths(ftdc_path, "metrics.*")
        if not discovered:
            logger.error("No folder containing FTDC files (metrics.*) found under: %s", args.ftdc_path)
            return 1
        logger.info(bold(green(f"Discovered {len(discovered)} FTDC folder(s) to process:")))
        for i, d in enumerate(discovered, 1):
            logger.info("  %d. %s", i, str(d))
    else:
        discovered = [ftdc_path]

    if args.start_time and args.end_time and args.start_time > args.end_time:
        logger.error("FTDC start time must be before or equal to end time.")
        return 1

    try:
        config = load_config(args.config)["ftdc"]
        if args.rate is not None:
            config.setdefault("item_config", {}).setdefault("BaselineAnalysisItem", {})["sample_rate"] = args.rate
    except FileNotFoundError:
        logger.error("Config file not found: %s", args.config)
        logger.info("Please provide a valid path to config.json.")
        return 1
    except KeyError:
        logger.error("FTDC configuration is missing from the config file.")
        return 1

    for ftdc_path_item in discovered:
        if not ftdc_path_item.is_dir():
            logger.error("FTDC folder not found: %s", ftdc_path_item)
            return 1
        logger.info("Analyzing FTDC data: %s", str(ftdc_path_item))
        output_folder = args.output if args.output.endswith("/") else f"{args.output}/"
        framework = FTDCAnalysisFramework(
            str(ftdc_path_item),
            deepcopy(config),
            start_time=args.start_time,
            end_time=args.end_time,
            image_format="svg" if args.svg else "png",
        )
        framework.run_ftdc_analysis(args.checkset, output_folder=output_folder)
        framework.output_results(output_folder=output_folder, fmt=args.format, open_browser=False)
        batch_folder = str(framework._get_output_folder(output_folder))
        final_folder = _rename_with_hostname(batch_folder, framework)
        if args.format in {"html", "pdf"}:
            html_file = Path(final_folder) / "report.html"
            if html_file.exists():
                webbrowser.open(f"file://{html_file.resolve()}")
    return 0


def version_command(_args):
    """Print current package version"""
    try:
        # Distribution name matches [project].name in pyproject.toml
        print(pkg_version("mongo-x-ray"))
    except PackageNotFoundError:
        # Fallback for source tree without installed metadata
        print("development")
    return 0


def main():
    parser = setup_parser()
    args = parser.parse_args()

    # Handle --version flag
    if "version" in args and args.version:
        return version_command(args)

    # Require command if --version not specified
    if not args.command:
        parser.error("the following arguments are required: command")

    if args.quiet:
        logger.setLevel(logging.FATAL)

    if args.command in ["healthcheck", "hc"]:
        return health_check_command(args)
    if args.command == "log":
        return log_analysis_command(args)
    if args.command == "gmd":
        return gmd_alalysis_command(args)
    if args.command == "ftdc":
        return ftdc_analysis_command(args)

    logger.error("Unknown command: %s", args.command)
    return 1


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    raise SystemExit(main())
