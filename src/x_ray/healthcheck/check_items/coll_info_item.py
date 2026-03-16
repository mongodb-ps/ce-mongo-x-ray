"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from pymongo.errors import OperationFailure

from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.coll_overview_parser import CollOverviewParser
from x_ray.healthcheck.parsers.coll_stats_parser import CollStatsParser
from x_ray.healthcheck.rules.data_size_rule import DataSizeRule
from x_ray.healthcheck.rules.fragmentation_rule import FragmentationRule
from x_ray.healthcheck.rules.op_latency_rule import OpLatencyRule
from x_ray.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
    get_collections,
)
from x_ray.utils import yellow, escape_markdown, format_size


class CollInfoItem(BaseItem):
    """
    This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
    """

    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Collection Information"
        self._description = "Collects & review collection statistics.\n\n"
        self._description += "- Whether average object size is too big.\n"
        self._description += "- Whether collections are big enough for sharding.\n"
        self._description += "- Whether collections and indexes are fragmented.\n"
        self._description += "- Whether operation latency exceeds thresholds.\n"
        self._data_size_rule = DataSizeRule(config)
        self._fragmentation_rule = FragmentationRule(config)
        self._op_latency_rule = OpLatencyRule(config)

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        def enum_collections(name, node, func, colls, **kwargs):
            client = node["client"]
            latency = node.get("pingLatencySec", 0)
            host = node["host"] if "host" in node else "cluster"
            if latency > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(f"Skip {host} because it has been irresponsive for {latency / 60:.2f} minutes.")
                )
                return None, None
            raw_result = []
            test_result = []
            for db_name, coll_names in colls.items():
                for coll_name in coll_names:
                    self._logger.debug("Gathering stats for collection: `%s.%s`", db_name, coll_name)
                    args = {"storageStats": {}}
                    args["latencyStats"] = {"histograms": True}
                    try:
                        stats = client[db_name].get_collection(coll_name).aggregate([{"$collStats": args}]).next()
                    except OperationFailure as e:
                        if e.code == 26:
                            self._logger.debug(
                                "Collection `%s.%s` does not exist. This is expected because the collections may not exist on all shards.",
                                db_name,
                                coll_name,
                            )
                        else:
                            self._logger.error(
                                "Failed to get stats for collection `%s.%s`: %s", db_name, coll_name, str(e)
                            )
                        continue
                    t_result, r_result = func(host, stats, **kwargs)
                    test_result.extend(t_result)
                    raw_result.append(r_result)

            self.append_test_results(test_result)
            return test_result, raw_result

        def func_overview(host, stats, **kwargs):
            # Check data size
            test_result, _ = self._data_size_rule.apply(stats, extra_info={"host": host})
            return test_result, stats

        def func_node(host, stats, **kwargs):
            ns = stats["ns"]
            test_result = []
            # Check fragmentation
            result_1, frag_data = self._fragmentation_rule.apply(stats, extra_info={"host": host})
            test_result.extend(result_1)
            # Check operation latency
            result_2, latency_data = self._op_latency_rule.apply(stats, extra_info={"host": host})
            test_result.extend(result_2)

            return test_result, frag_data | latency_data | {"ns": ns, "stats": stats}

        nodes = discover_nodes(client, parsed_uri)
        colls = get_collections(client)
        result = enum_all_nodes(
            nodes,
            func_sh_cluster=lambda name, node, **kwargs: enum_collections(
                name, node, func_overview, colls=colls, **kwargs
            ),
            func_rs_cluster=lambda name, node, **kwargs: enum_collections(
                name, node, func_overview, colls=colls, **kwargs
            ),
            func_rs_member=lambda name, node, **kwargs: enum_collections(name, node, func_node, colls=colls, **kwargs),
            func_shard_member=lambda name, node, **kwargs: enum_collections(
                name, node, func_node, colls=colls, **kwargs
            ),
        )
        self.captured_sample = result

    @property
    def review_result_markdown(self) -> str:
        result = self.captured_sample
        output: list[str] = []

        def func_overview(set_name, node, **kwargs) -> None:
            parser: BaseParser = CollOverviewParser()
            output.append(parser.markdown(node.get("rawResult", None)))

        def func_node(set_name, node, **kwargs) -> None:
            host = node["host"] if "host" in node else "cluster"
            parser: BaseParser = CollStatsParser()
            output.append(
                parser.markdown(
                    node.get("rawResult", None),
                    host=host,
                    set_name=set_name,
                ),
            )

        enum_result_items(
            result,
            func_sh_cluster=func_overview,
            func_rs_cluster=func_overview,
            func_rs_member=func_node,
            func_shard_member=func_node,
        )
        return "\n\n".join(output)
