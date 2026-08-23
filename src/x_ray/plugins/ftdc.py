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

from x_ray.ftdc_analysis.framework import Framework
from x_ray.plugin import Plugin, discover_paths, open_report, sample_rate, utc_iso_datetime
from x_ray.utils import bold, green, load_config

logger = logging.getLogger(__name__)


class FtdcPlugin(Plugin):
    name = "ftdc"
    help = "Analyze MongoDB FTDC files"
    description = """
Analyze MongoDB Full Time Diagnostic Data Capture (FTDC) files.

The input is a directory containing FTDC files.
"""
    epilog = """
Examples:
  x-ray ftdc /var/lib/mongo/diagnostic.data
  x-ray ftdc /var/lib/mongo/diagnostic.data 2026-06-17T08:00:00Z 2026-06-17T10:00:00Z
"""

    def add_arguments(self, parser):
        parser.add_argument("ftdc_path", help="Path to a directory containing FTDC files.")
        parser.add_argument(
            "start_time",
            nargs="?",
            type=utc_iso_datetime,
            help="Inclusive UTC start time in ISO-8601 format. Defaults to the first data point.",
        )
        parser.add_argument(
            "end_time",
            nargs="?",
            type=utc_iso_datetime,
            help="Inclusive UTC end time in ISO-8601 format. Defaults to the last data point.",
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
            "--svg",
            help="Reference SVG charts in the report instead of converting them to PNG.",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-r",
            "--rate",
            help="FTDC sampling rate. Defaults to 1 divided by the number of ingested files.",
            type=sample_rate,
            default=None,
        )
        parser.add_argument(
            "--discover",
            help="Recursively search the given path for a folder containing FTDC files.",
            action="store_true",
            default=False,
        )

    def run(self, args) -> int:
        """Run the FTDC analysis command."""
        ftdc_path = Path(args.ftdc_path)
        if args.discover:
            discovered = discover_paths(ftdc_path, "metrics.*")
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
            framework = Framework(
                str(ftdc_path_item),
                deepcopy(config),
                start_time=args.start_time,
                end_time=args.end_time,
                image_format="svg" if args.svg else "png",
            )
            framework.run_ftdc_analysis(args.checkset, output_folder=output_folder)
            framework.output_results(output_folder=output_folder, fmt=args.format, open_browser=False)
            open_report(framework, output_folder, args.format, args.no_browser)
        return 0
