"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import html as html_mod
import logging
from typing import TextIO

from x_ray.framework import BaseFramework
from x_ray.healthcheck.shared import irresponsive_nodes
from x_ray.shared import str_to_md_id
from x_ray.utils import bold, green, load_classes, yellow

logger = logging.getLogger(__name__)

CHECKLIST_CLASSES = load_classes("x_ray.healthcheck.check_items")


class Framework(BaseFramework):
    template_module = "healthcheck"

    def run_checks(self, checkset_name: str, *_args, **kwargs):
        self._set_name = checkset_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the checkset based on the name
        checksets = self._config.get("checksets", {})
        if checkset_name not in checksets:
            self._logger.warning(
                yellow(f"Checkset '{checkset_name}' not found in configuration. Using default checkset.")
            )
            checkset_name = "default"
        cs = checksets[checkset_name]
        self._logger.info("Running checkset: %s", bold(green(checkset_name)))

        # The information gathered can be huge sometimes, we always save the information to the file immediately after using.
        # The test result, however, will be kept in memory until the end of the run.
        # The result of each check item will be persisted to a file in the output folder.
        for item_name in cs.get("items", []):
            item_cls = CHECKLIST_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"Check item '{item_name}' not found. Skipping."))
                continue
            # The config for the item can be specified in the `item_config` section, under the item class name.
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(str(batch_folder), item_config)
            self._logger.info("Running check item: %s", bold(green(item.name)))
            item.test(**kwargs)
            self._items.append(item)

    def _render_markdown(self, output: TextIO) -> None:
        output.write("# Deployment Health Check\n\n")
        # Display irresponsive nodes
        output.write("## Overview\n\n")
        output.write("### By Severity\n\n")
        output.write(
            "|<span style='color: red;'>HIGH</span>{200}|<span style='color: orange;'>MEDIUM</span>{200}|<span style='color: green;'>LOW</span>{200}|<span style='color: gray;'>INFO</span>{200}|\n"
        )
        output.write("|---|---|---|---|\n")
        all_test_result = []
        for item in self._items:
            all_test_result.extend(item.test_result["items"])
        all_severity = [result["severity"].name for result in all_test_result]
        high_count = all_severity.count("HIGH")
        medium_count = all_severity.count("MEDIUM")
        low_count = all_severity.count("LOW")
        info_count = all_severity.count("INFO")
        output.write(f"|{high_count}|{medium_count}|{low_count}|{info_count}|\n\n")
        output.write("### By Category\n\n")
        all_categories = [result["title"] for result in all_test_result]
        category_counts = {category: all_categories.count(category) for category in set(all_categories)}

        # Enrich test results with matched risks from the risk register
        try:
            from x_ray.risk_register.db import enrich_test_results  # pylint: disable=import-outside-toplevel

            matched = enrich_test_results(all_test_result)
            if matched:
                self._logger.info(green(f"Matched {matched} issues to known risks"))
        except Exception:  # pylint: disable=broad-exception-caught
            self._logger.debug("Risk register matching not available", exc_info=True)

        # Build category → matched_risk lookup
        cat_risks = {}
        for r in all_test_result:
            mr = r.get("matched_risk")
            if mr and r.get("title"):
                cat_risks[r["title"]] = mr

        output.write(
            '| <span data-sortable="true">Category</span>{300} | <span data-sortable="true">Count</span>{100} | <span data-sortable="false">Known Risks</span>{150} |\n'
        )
        output.write("|---:|:---:|:---|\n")
        for category, count in category_counts.items():
            risk_html = ""
            mr = cat_risks.get(category)
            if mr:
                rid = html_mod.escape(str(mr.get("id", "")))
                rname = html_mod.escape(str(mr.get("name", "")))
                rdesc = html_mod.escape(str(mr.get("description", "")))
                risk_html = (
                    f'<span class="risk-badge">RISK-{rid}'
                    f'<span class="risk-tooltip">'
                    f'<span class="risk-name">{rname}</span>'
                    f"{rdesc}</span></span>"
                )
            output.write(f'|{category}|<span data-sort-value="{count}"><strong>{count}</strong></span>|{risk_html}|\n')
        output.write("\n")
        if len(irresponsive_nodes) > 0:
            output.write("The following nodes have been detected as irresponsive during the checks:\n\n")
            for node in irresponsive_nodes:
                output.write(f"- `{node['host']}`\n")
            output.write(
                "\n**<span style='color: red;'>All checks against the above nodes have been skipped.</span>**\n"
            )
        output.write("## 1 Review Test Results\n\n")
        for i, item in enumerate(self._items):
            title = f"1.{i + 1} {item.name}"
            review_title = f"2.{i + 1} Review {item.name}"
            review_title_id = str_to_md_id(review_title)
            output.write(f"### {title}\n\n")
            output.write(f"{item.description}\n\n")
            output.write(f"[Review Raw Results &rarr;](#{review_title_id})\n\n")
            output.write(item.test_result_markdown)

        output.write("## 2 Review Raw Results\n\n")
        for i, item in enumerate(self._items):
            # The link to the related test result
            title = f"1.{i + 1} {item.name}"
            title_id = str_to_md_id(title)
            review_title = f"2.{i + 1} Review {item.name}"
            output.write(f"### {review_title}\n\n")
            output.write(f"[&larr; Review Test Results](#{title_id})\n\n")
            output.write(item.review_result_markdown)
