"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.shard_key_parser import ShardKeyParser
from x_ray.healthcheck.rules.shard_balance_rule import ShardBalanceRule
from x_ray.healthcheck.rules.shard_key_rule import ShardKeyRule
from x_ray.healthcheck.shared import (
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
)


class ShardKeyItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Shard Key Information"
        self._description = "Collects and reviews shard key configuration for collections in a sharded cluster.\n\n"
        self._description += "- Whether the shard key is set to `{_id: 1}` or `{_id: -1}`.\n"
        self._description += "- Whether collections are imbalanced."
        self._shard_key_rule = ShardKeyRule(config)
        self._shard_balance_rule = ShardBalanceRule(config)

    def test(self, *args, **kwargs):
        """
        Main test method to gather shard key information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)
        if nodes["type"] == "RS":
            self._logger.info("Cluster is not a sharded cluster. Skip...")
            return

        def func_sh_cluster(name, node, **kwargs):
            client = node["client"]
            collections = list(client.config.collections.find({"_id": {"$ne": "config.system.sessions"}}))
            shards = [doc["_id"] for doc in client.config.shards.find()]
            test_result = []
            raw_result = {"shardedCollections": collections, "stats": {}}
            for c in collections:
                # Check if the collection is using `{_id: 1}` as shard key
                ns = c["_id"]
                result1, _ = self._shard_key_rule.apply(c)
                test_result.extend(result1)
                # Gather sharding stats
                db_name, coll_name = ns.split(".")
                stats = client[db_name].command("collStats", coll_name)
                result2, parsed_data = self._shard_balance_rule.apply(stats, extra_info={"shards": shards})
                test_result.extend(result2)
                raw_result["stats"][ns] = parsed_data

            self.append_test_results(test_result)
            return test_result, raw_result

        result = enum_all_nodes(nodes, func_sh_cluster=func_sh_cluster)

        self.captured_sample = result

    @property
    def review_result_markdown(self) -> str:
        result = self.captured_sample
        output: list = []

        def func_cluster(set_name, node, **kwargs) -> None:
            raw_result = node["rawResult"]
            parser: BaseParser = ShardKeyParser()
            output.append(parser.markdown(raw_result))

        enum_result_items(result, func_sh_cluster=func_cluster)

        return "\n\n".join(output)
