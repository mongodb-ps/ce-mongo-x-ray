"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.log_analysis.log_items.base_item import BaseItem


class SlowChartItem(BaseItem):
    """Generate a scatter plot showing slow operations over time,
    with each point representing a slow query colored by namespace."""

    def __init__(self, output_folder, config):
        super().__init__(output_folder, config, show_reset=True)
        self.name = "Slow Operations Chart"
        self.description = "Generate a scatter plot showing slow operations over time, with each point representing a slow query colored by namespace."
        self._cache = None

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id != 51803:  # Slow query
            return
        self._cache = log_line
        self._write_output()
        self._cache = None

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f'<div id="links_{self.__class__.__name__}" markdown="1">\n')
        f.write(f"[Duration Chart](#canvas_{self.__class__.__name__}_duration)")
        f.write(f" | [Scanned Chart](#canvas_{self.__class__.__name__}_scanned)")
        f.write(f" | [Scanned Objects Chart](#canvas_{self.__class__.__name__}_scannedObj)")
        f.write("</div>\n")
        f.write(f'<canvas id="canvas_{self.__class__.__name__}_duration" height="200"></canvas>\n')
        f.write(
            f'<canvas id="canvas_{self.__class__.__name__}_scanned" height="200" style="display: none;"></canvas>\n'
        )
        f.write(
            f'<canvas id="canvas_{self.__class__.__name__}_scannedObj" height="200" style="display: none;"></canvas>\n'
        )
        f.write(f'<div id="positioner_{self.__class__.__name__}"></div>\n')
        f.write("```json\n")
        f.write("// Click data points to review original log line...\n")
        f.write("```\n")
