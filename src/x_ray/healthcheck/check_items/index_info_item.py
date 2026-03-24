"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime, timezone
from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.index_info_parser import IndexInfoParser
from x_ray.healthcheck.rules.index_rule import IndexRule
from x_ray.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
    get_collections,
)
from x_ray.utils import yellow


class IndexInfoItem(BaseItem):
    """
    This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
    """

    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Index Information"
        self._description = "Collects & review index statistics.\n\n"
        self._description += "- Whether the number of indexes in the collection is too many.\n"
        self._description += "- Whether there are unused indexes in the collection.\n"
        self._description += "- Whether there are redundant indexes in the collection.\n"
        self._index_rule = IndexRule(config)

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        def cluster_check(host, ns, index_stats):
            # Check number of indexes and redundant indexes
            result, _ = self._index_rule.apply(
                index_stats,
                extra_info={"host": host, "ns": ns},
                check_items=["num_indexes", "redundant_indexes"],
            )
            return result

        def node_check(host, ns, index_stats):
            result, _ = self._index_rule.apply(
                index_stats,
                extra_info={
                    "host": host,
                    "ns": ns,
                    "capture_time": datetime.now(),
                },
                check_items=["unused_indexes"],
            )
            return result

        def enum_namespaces(node, func, colls, **kwargs):
            level = kwargs.get("level")
            client = node["client"]
            latency = node.get("pingLatencySec", 0)
            if latency > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
                )
                return None, None
            test_result, raw_result = [], []
            host = node.get("host", "cluster")
            for db_name, coll_names in colls.items():
                for coll_name in coll_names:
                    ns = f"{db_name}.{coll_name}"
                    self._logger.debug(
                        "Gathering index stats of collection `%s` on %s level...",
                        ns,
                        level,
                    )
                    index_stats = list(client[db_name][coll_name].aggregate([{"$indexStats": {}}]))
                    result = func(host, ns, index_stats)
                    test_result.extend(result)
                    raw_result.append(
                        {
                            "ns": ns,
                            "captureTime": datetime.now(timezone.utc),
                            "indexStats": index_stats,
                        }
                    )
            self.append_test_results(test_result)
            return test_result, raw_result

        colls = get_collections(client)
        result = enum_all_nodes(
            nodes,
            func_rs_cluster=lambda name, node, **kwargs: enum_namespaces(node, cluster_check, colls, **kwargs),
            func_sh_cluster=lambda name, node, **kwargs: enum_namespaces(node, cluster_check, colls, **kwargs),
            func_rs_member=lambda name, node, **kwargs: enum_namespaces(node, node_check, colls, **kwargs),
            func_shard_member=lambda name, node, **kwargs: enum_namespaces(node, node_check, colls, **kwargs),
        )

        self.captured_sample = result

    @property
    def review_result_markdown(self) -> str:
        result = self.captured_sample
        output: list[str] = []

        def func_cluster(set_name, node, **kwargs) -> None:
            raw_result = node.get("rawResult", [])
            parser: BaseParser = IndexInfoParser()
            output.append(parser.markdown(raw_result, set_name=set_name))

        enum_result_items(result, func_sh_cluster=func_cluster, func_rs_cluster=func_cluster)
        return "\n\n".join(output)
