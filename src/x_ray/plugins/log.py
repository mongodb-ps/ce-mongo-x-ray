"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import logging
from copy import deepcopy
from pathlib import Path

from x_ray.log_analysis.framework import Framework
from x_ray.plugin import Plugin, discover_paths, open_report, utc_iso_datetime
from x_ray.utils import bold, green, load_config

logger = logging.getLogger(__name__)


class LogPlugin(Plugin):
    name = "log"
    help = "Analyze MongoDB log files"
    description = """
Analyze MongoDB log files to identify patterns, issues, and optimization opportunities.

This command will process MongoDB log files and provide insights including:
- Slow query analysis
- Error pattern detection
- Connection statistics
- Operation distribution
- Index usage suggestions

The analysis will be output in the format specified (HTML or Markdown).
"""
    epilog = """
Examples:
  x-ray log /var/log/mongodb/mongod.log
  x-ray log /var/log/mongodb/ 2026-07-20T08:00:00Z 2026-07-20T10:00:00Z
  x-ray log /path/to/mongod.log -f html -o /path/to/output/
"""

    def add_arguments(self, parser):
        parser.add_argument("log_file", help="Path to the MongoDB log file or a folder of log files to analyze")
        parser.add_argument(
            "start_time",
            nargs="?",
            type=utc_iso_datetime,
            help="Inclusive UTC start time in ISO-8601 format. Defaults to the first log line.",
        )
        parser.add_argument(
            "end_time",
            nargs="?",
            type=utc_iso_datetime,
            help="Inclusive UTC end time in ISO-8601 format. Defaults to the last log line.",
        )
        parser.add_argument("-s", "--checkset", help='Checkset to run. Defaults to "default".', type=str, default="default")
        parser.add_argument("-o", "--output", help='Output folder path. Defaults to "output/".', type=str, default="output/")
        parser.add_argument(
            "-f",
            "--format",
            help='Output format (markdown/html/pdf). PDF also generates Markdown and HTML. Defaults to "html".',
            type=str,
            default="html",
            choices=["markdown", "html", "pdf"],
        )
        parser.add_argument("--no-browser", help="Do not open the generated report in the browser.", action="store_true")
        parser.add_argument(
            "-r",
            "--rate",
            help="Log sampling rate (e.g., 1 for all logs, 0.1 for 10%% logs). Defaults to 1.",
            type=float,
            default=1.0,
        )
        parser.add_argument("--top", help="Top N slow queries. Defaults to 10.", type=int, default=10)
        parser.add_argument(
            "--discover",
            help="Recursively search the given path for a folder containing log files.",
            action="store_true",
            default=False,
        )

    def run(self, args) -> int:
        """Run the log analysis command."""
        log_path = Path(args.log_file)
        if args.discover:
            discovered = discover_paths(log_path, "*.log*")
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
            framework = Framework(
                str(log_path_item),
                deepcopy(config),
                start_time=args.start_time,
                end_time=args.end_time,
            )
            framework.run_logs_analysis(args.checkset, output_folder=output_folder)
            framework.output_results(output_folder=output_folder, fmt=args.format, open_browser=False)
            open_report(framework, output_folder, args.format, args.no_browser)
        return 0
