"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime, timezone
from dateutil import parser

from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.rules.index_rule import IndexRule
from x_ray.healthcheck.parsers.index_info_parser import IndexInfoParser


class IndexInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Index Information"
        self.description: str = "Collects and analyzes index information from GMD logs."
        self._ns_indexes: list = []
        self._index_stats: dict = {}
        self._index_rule = IndexRule(config)

        def _get_indexes(block) -> None:
            output: dict = block.get("output", {})
            cmdParams: dict = block.get("commandParameters", {})
            self._ns_indexes.append(
                {"ns": f"{cmdParams.get('db', '')}.{cmdParams.get('collection', '')}", "specs": output}
            )

        def _get_index_stats(block) -> None:
            output: dict = block.get("output", {})
            ns = output.get("cursor", {}).get("ns", "")
            index_stats = output.get("cursor", {}).get("firstBatch", [])
            self._index_stats[ns] = {
                "ns": ns,
                "capture_time": block.get("ts", {}).get("start", "").replace(tzinfo=timezone.utc),
                "index_stats": [
                    {
                        "ops": stat.get("stats", 0)[0]["accesses"],
                        "since": parser.parse(stat.get("stats", "")[0]["since"]),
                        "key": stat.get("key", {}),
                    }
                    for stat in index_stats
                ],
            }

        self.watch_one(GMD_EVENTS.INDEXES, _get_indexes)
        self.watch_one(GMD_EVENTS.INDEX_STATS, _get_index_stats)

    def test_result_markdown(self, output) -> None:
        # construct index structure so we can reuse indexRule for analysis.
        for ns_info in self._ns_indexes:
            ns = ns_info.get("ns", "")
            indexes: list = list([{"spec": spec} for spec in ns_info.get("specs", [])])
            test_results, _ = self._index_rule.apply(
                indexes,
                extra_info={"host": self._hostname, "ns": ns},
                check_items=["num_indexes", "redundant_indexes"],
            )
            self.append_test_results(test_results)
        super().test_result_markdown(output)

    def review_results_markdown(self, output) -> None:
        # construct index structure so we can reuse index info parser for visualization.
        indexes = []
        for ns_info in self._ns_indexes:
            ns = ns_info.get("ns", "")
            stats = self._index_stats.get(ns, {})
            capture_time = stats.get("capture_time", datetime.now().isoformat())
            ns_stats: dict = {
                "ns": ns,
                "captureTime": capture_time,
                "indexStats": [],
            }
            for spec in ns_info.get("specs", []):
                key: dict = spec.get("key", {})
                matched_stats: dict = next(
                    (stat for stat in stats.get("index_stats", []) if stat.get("key", {}) == key), {}
                )
                index = {
                    "name": spec.get("name", ""),
                    "key": key,
                    "host": self._hostname,
                    "accesses": {
                        "ops": matched_stats.get("ops", 0),
                        "since": matched_stats.get("since", datetime.now()),
                    },
                    "spec": spec,
                }
                ns_stats["indexStats"].append(index)
                indexes.append(ns_stats)
        index_parser: BaseParser = IndexInfoParser()
        parsed_data = index_parser.markdown(indexes, set_name="cluster")
        output.write(parsed_data)
