"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime, timezone
from typing import TextIO

from x_ray.framework import BaseFramework
from x_ray.gmd_analysis.gmd_items.summary_item import SummaryItem
from x_ray.gmd_analysis.shared import load_json
from x_ray.shared import str_to_md_id, to_json
from x_ray.utils import bold, cyan, env, green, load_classes, red, yellow

GMD_CLASSES = load_classes("x_ray.gmd_analysis.gmd_items")


class Framework(BaseFramework):
    template_module = "gmd"

    def __init__(self, file_path: str, config: dict):
        super().__init__(config)
        self._file_path = file_path
        self._logger.debug(to_json(self._config))
        self._log_start = None
        self._log_end = None
        if env == "development":
            self._logger.info(yellow("Running in development mode."))

    def run_gmd_analysis(self, gmd_set_name: str, *_args, **kwargs):
        self._set_name = gmd_set_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the gmd checkset based on the name
        gmdsets = self._config.get("gmdsets", {})
        if gmd_set_name not in gmdsets:
            self._logger.warning(yellow(f"GMD checkset '{gmd_set_name}' not found in configuration. Using default."))
            gmd_set_name = "default"
        gmdset = gmdsets[gmd_set_name]
        self._logger.info("Running GMD checkset: %s", bold(cyan(gmd_set_name)))

        self._items = []
        for item_name in gmdset.get("items", []):
            item_cls = GMD_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"GMD item '{item_name}' not found. Skipping."))
                continue
            # The config for the item can be specified in the `item_config` section, under the item class name.
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(str(batch_folder), item_config)
            self._items.append(item)
            self._logger.info("GMD analyze item loaded: %s", bold(cyan(item_name)))
        gmd_output = self._file_path

        # Read the getMongoData output and parse the whole content.
        with open(gmd_output, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            try:
                objects = load_json(content)
            except Exception as ex:  # pylint: disable=broad-exception-caught
                self._logger.error(red(f"Failed to parse the getMongoData output as JSON: {ex}"))
                return

            self._logger.info("Ingesting %s objects from getMongoData output...", green(str(len(objects))))

            for i, obj in enumerate(objects):
                if (i + 1) % 10000 == 0:
                    self._logger.info("%s objects ingested...", green(str(i + 1)))
                for item in self._items:
                    try:
                        item.test(obj)
                    except Exception as e:  # pylint: disable=broad-exception-caught
                        self._logger.warning(yellow(f"GMD analysis item '{item.name}' failed: {e}"))
                        continue

            for item in self._items:
                try:
                    item.finalize_analysis()
                except Exception as e:  # pylint: disable=broad-exception-caught
                    self._logger.warning(yellow(f"GMD analysis item '{item.name}' finalization failed: {e}"))
                    continue

    def _render_markdown(self, output: TextIO) -> None:
        output.write("# getMongoData Analysis Report\n")
        output.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
        output.write(f"File path: `{self._file_path}`\n\n")
        output.write("## 1 Review Test Results\n\n")
        output.write("### Overview\n\n")
        # Enrich all test results with matched risks before building summary
        for item in self._items:
            try:
                from x_ray.risk_register import enrich_test_results  # pylint: disable=import-outside-toplevel
                enrich_test_results(item._test_result)  # pylint: disable=protected-access
            except Exception:  # pylint: disable=broad-exception-caught
                self._logger.debug("Risk register matching not available", exc_info=True)
        summary_item = SummaryItem()
        summary_item.summarize(self._items)
        summary_item.overview(output)
        for i, item in enumerate(self._items):
            if item._in_complete_flag:  # pylint: disable=protected-access
                self._logger.warning(
                    yellow(f"GMD item '{item.name}' is incomplete because of too many databases/collections.")
                )
            try:
                title = f"1.{i + 1} {item.name}"
                review_title = f"2.{i + 1} Review {item.name}"
                review_title_id = str_to_md_id(review_title)
                output.write(f"### {title}\n\n")
                output.write(f"{item.description}\n\n")
                output.write(f"[Review Raw Results &rarr;](#{review_title_id})\n\n")
                item.test_result_markdown(output)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(yellow(f"Failed to generate markdown for GMD item '{item.name}': {e}"))
                continue

        output.write("## 2 Review Raw Results\n\n")
        for i, item in enumerate(self._items):
            try:
                title = f"1.{i + 1} {item.name}"
                title_id = str_to_md_id(title)
                review_title = f"2.{i + 1} Review {item.name}"
                output.write(f"### {review_title}\n\n")
                output.write(f"[&larr; Review Test Results](#{title_id})\n\n")
                item.review_results_markdown(output)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(yellow(f"Failed to generate review markdown for GMD item '{item.name}': {e}"))
                continue
