"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import html as html_mod

from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.check_items.base_item import colorize_severity
from x_ray.shared import SEVERITY


class SummaryItem:
    def __init__(self) -> None:
        self._summary_severity: dict[SEVERITY, int] = {
            SEVERITY.HIGH: 0,
            SEVERITY.MEDIUM: 0,
            SEVERITY.LOW: 0,
            SEVERITY.INFO: 0,
        }
        self._summary_title: dict[str, int] = {}
        self._title_risk: dict[str, dict] = {}

    def summarize(self, items: list[BaseItem]) -> None:
        for item in items:
            for result in item.test_result:
                severity = result.get("severity", SEVERITY.INFO)
                if severity in self._summary_severity:
                    self._summary_severity[severity] += 1
                else:
                    self._summary_severity[severity] = 1
                title = result.get("title", "Untitled")
                if title in self._summary_title:
                    self._summary_title[title] += 1
                else:
                    self._summary_title[title] = 1
                mr = result.get("matched_risk")
                if mr:
                    self._title_risk[title] = mr

    def overview(self, output) -> None:
        def format_header(severity: SEVERITY):
            return f"<b style='color: {colorize_severity(severity)}'>{severity.name}</b>"

        output.write("#### By Severity\n\n")
        output.write(
            f"|{format_header(SEVERITY.HIGH)}{{200}}|{format_header(SEVERITY.MEDIUM)}{{200}}|{format_header(SEVERITY.LOW)}{{200}}|{format_header(SEVERITY.INFO)}{{200}}|\n"
        )
        output.write("|:---:|:---:|:---:|:---:|\n")
        output.write(
            f"|{self._summary_severity[SEVERITY.HIGH]}|{self._summary_severity[SEVERITY.MEDIUM]}|{self._summary_severity[SEVERITY.LOW]}|{self._summary_severity[SEVERITY.INFO]}|\n\n"
        )
        output.write("#### By Category\n\n")
        output.write(
            '| <span data-sortable="true">Category</span>{300} '
            '| <span data-sortable="true">Count</span>{100} '
            '| <span data-sortable="false">Known Risks</span>{150} |\n'
        )
        output.write("|---:|:---:|:---|\n")
        for title, count in self._summary_title.items():
            risk_html = ""
            mr = self._title_risk.get(title)
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
            output.write(f'|{title}|<span data-sort-value="{count}"><strong>{count}</strong></span>|{risk_html}|\n')
        output.write("\n")
