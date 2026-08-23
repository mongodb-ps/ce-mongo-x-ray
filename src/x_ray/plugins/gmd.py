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

from x_ray.gmd_analysis.framework import Framework
from x_ray.plugin import Plugin, open_report
from x_ray.utils import load_config

logger = logging.getLogger(__name__)


class GmdPlugin(Plugin):
    name = "gmd"
    help = "Analyze a getMongoData output file"
    description = """
Analyze the JSON output produced by MongoDB's getMongoData script.

The input is a getMongoData JSON file.
"""
    epilog = """
Examples:
  x-ray gmd /path/to/getMongoData-output.json
  x-ray gmd /path/to/getMongoData-output.json -f html -o /path/to/output/
"""

    def add_arguments(self, parser):
        parser.add_argument("gmd_file", help="Path to the getMongoData output JSON file.")
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

    def run(self, args) -> int:
        """Run the getMongoData analysis command."""
        gmd_file = Path(args.gmd_file)
        if not gmd_file.is_file():
            logger.error("getMongoData output file not found: %s", gmd_file)
            return 1

        try:
            config = load_config(args.config)["gmd"]
        except FileNotFoundError:
            logger.error("Config file not found: %s", args.config)
            logger.info("Please provide a valid path to config.json.")
            return 1
        except KeyError:
            logger.error("GMD configuration is missing from the config file.")
            return 1

        output_folder = args.output if args.output.endswith("/") else f"{args.output}/"
        framework = Framework(str(gmd_file), deepcopy(config))
        framework.run_gmd_analysis(args.checkset, output_folder=output_folder)
        framework.output_results(output_folder=output_folder, fmt=args.format, open_browser=False)
        open_report(framework, output_folder, args.format, args.no_browser)
        return 0
