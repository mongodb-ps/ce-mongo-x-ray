"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.check_items.base_item import colorize_severity
from x_ray.healthcheck.shared import SEVERITY
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem


class SummaryItem:
    def __init__(self):
        self.summary = {
            SEVERITY.HIGH: 0,
            SEVERITY.MEDIUM: 0,
            SEVERITY.LOW: 0,
            SEVERITY.INFO: 0,
        }

    def summarize(self, items: list[BaseItem]) -> None:
        for item in items:
            for result in item.test_result:
                severity = result.get("severity", SEVERITY.INFO)
                if severity in self.summary:
                    self.summary[severity] += 1
                else:
                    self.summary[severity] = 1

    def overview(self, output) -> None:
        def format_header(severity: SEVERITY):
            return f"<b style='color: {colorize_severity(severity)}'>{severity.name}</b>"

        output.write(
            f"|{format_header(SEVERITY.HIGH)}|{format_header(SEVERITY.MEDIUM)}|{format_header(SEVERITY.LOW)}|{format_header(SEVERITY.INFO)}|\n"
        )
        output.write("|:---:|:---:|:---:|:---:|\n")
        output.write(
            f"|{self.summary[SEVERITY.HIGH]}|{self.summary[SEVERITY.MEDIUM]}|{self.summary[SEVERITY.LOW]}|{self.summary[SEVERITY.INFO]}|\n\n"
        )
