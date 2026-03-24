"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime
from x_ray.log_analysis.log_items.base_item import BaseItem


class LogRateItem(BaseItem):
    def __init__(self, output_folder, config) -> None:
        super().__init__(output_folder, config, show_reset=True)
        self._temp_cache: dict = {}
        self.name: str = "Log Rate Analysis"
        self.description: str = (
            "The rate of different logs (grouped by ID) over time. \nOnly showing log IDs that constantly appear."
        )

    def analyze(self, log_line) -> None:
        log_id = log_line["id"]
        timestamp: datetime = log_line["t"]
        minute_bucket = timestamp.replace(second=0, microsecond=0)
        if log_id not in self._temp_cache:
            self._logger.debug("Creating entry for log ID %s at %s", log_id, minute_bucket)
            self._temp_cache[log_id] = {
                "id": log_id,
                "sample": log_line,
                "buckets": [
                    {
                        "time": minute_bucket,
                        "count": 1,
                    }
                ],
            }
        else:
            last_bucket = self._temp_cache[log_id]["buckets"][-1]
            if last_bucket["time"] == minute_bucket:
                last_bucket["count"] += 1
            else:
                self._logger.debug("Creating new bucket for log ID %s at %s", log_id, minute_bucket)
                self._temp_cache[log_id]["buckets"].append(
                    {
                        "time": minute_bucket,
                        "count": 1,
                    }
                )

    def finalize_analysis(self) -> None:
        self._cache = [v for v in self._temp_cache.values() if len(v["buckets"]) > 1]
        super().finalize_analysis()

    def review_results_markdown(self, f) -> None:
        super().review_results_markdown(f)
        f.write(f'<canvas id="canvas_{self.__class__.__name__}" width="400" height="200"></canvas>\n')
