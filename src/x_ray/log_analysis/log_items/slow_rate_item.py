"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime
import math
from x_ray.log_analysis.log_items.base_item import BaseItem


class SlowRateItem(BaseItem):
    """Analyze slow query rates from log lines."""

    def __init__(self, output_folder: str, config):
        super().__init__(output_folder, config, show_reset=True)
        self._cache = None
        self.name = "Slow Rate"
        self.description = "Analyse the rate of slow queries."

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id != 51803:  # Slow query
            return
        time = log_line.get("t")
        ts = math.floor(time.timestamp())
        time_min = datetime.fromtimestamp(ts - (ts % 60))

        if self._cache is None or self._cache["time"] != time_min:
            if self._cache is not None:
                # New minute, write previous minute's data
                self._write_output()
            # First time or new minute bucket
            self._cache = {"time": time_min, "total_slow_ms": 0, "count": 0, "byNs": {}}

        attr = log_line.get("attr", {})
        slow_ms = attr.get("durationMillis", 0)
        ns = attr.get("ns", "unknown")
        self._cache["count"] += 1
        self._cache["total_slow_ms"] += slow_ms
        if ns not in self._cache["byNs"]:
            self._cache["byNs"][ns] = {"count": 0, "total_slow_ms": 0}
        self._cache["byNs"][ns]["count"] += 1
        self._cache["byNs"][ns]["total_slow_ms"] += slow_ms

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f'<canvas id="canvas_{self.__class__.__name__}" width="400" height="200"></canvas>\n')
        f.write(f'<div class="pie"><canvas id="canvas_{self.__class__.__name__}_byns" height="200"></canvas></div>\n')
        f.write(
            f'<div class="pie"><canvas id="canvas_{self.__class__.__name__}_byns_ms" height="200"></canvas></div>\n'
        )
