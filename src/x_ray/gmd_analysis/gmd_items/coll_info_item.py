"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from typing import Any

from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.gmd_analysis.parsers.coll_stats_parser import CollStatsParser
from x_ray.healthcheck.rules.data_size_rule import DataSizeRule
from x_ray.healthcheck.rules.fragmentation_rule import FragmentationRule


class CollInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Collection Information"
        self._collections_stats: list[dict[str, Any]] = []
        self.shard_keys: dict = {}
        self._rules["data_size"] = DataSizeRule(config)
        self._rules["fragmentation"] = FragmentationRule(config)

        def _get_collections_stats(block) -> None:
            # rebuild the collection stats data structure to match the one used in health check for easier review
            output: dict = block.get("output", {})
            wt: dict = output.get("wiredTiger", {})
            block_manager: dict = wt.get("block-manager", {})
            stats: dict = {
                "ns": output.get("ns", ""),
                "storageStats": {
                    "size": output.get("size", 0) * 1024**2,
                    "avgObjSize": output.get("avgObjSize", 0),
                    "storageSize": output.get("storageSize", 0) * 1024**2,
                    "totalIndexSize": output.get("totalIndexSize", 0) * 1024**2,
                    "wiredTiger": {
                        "block-manager": {
                            "file bytes available for reuse": block_manager.get("file bytes available for reuse", 0),
                            "file size in bytes": block_manager.get("file size in bytes", 0),
                        },
                    },
                },
            }
            test_result, _ = self._rules["data_size"].apply(stats, extra_info={"host": "cluster"})
            self.append_test_results(test_result)
            test_result, frag_data = self._rules["fragmentation"].apply(stats, extra_info={"host": "cluster"})
            self.append_test_results(test_result)
            parsed_data = frag_data | output
            self._collections_stats.append(parsed_data)

        def _get_shard_key_info(block) -> None:
            output: dict = block.get("output", {})
            for db in output:
                collections: list = db.get("collections", [])
                for coll in collections:
                    self.shard_keys[coll.get("_id", "")] = coll.get("key", {})

        self.watch_one(GMD_EVENTS.COLLECTION_STATS, _get_collections_stats)
        self.watch_one(GMD_EVENTS.SHARDED_DATABASES, _get_shard_key_info)

    def review_results_markdown(self, output) -> None:
        assert (
            len(self._collections_stats) > 0
        ), f"GMD subsection {GMD_EVENTS.COLLECTION_STATS.value} should be available for review."

        for stats in self._collections_stats:
            ns = stats.get("ns", "")
            shard_key = self.shard_keys.get(ns, {})
            if shard_key:
                stats["shardKey"] = shard_key
        parser: BaseParser = CollStatsParser()
        parsed_data = parser.markdown(self._collections_stats)
        output.write(parsed_data)
