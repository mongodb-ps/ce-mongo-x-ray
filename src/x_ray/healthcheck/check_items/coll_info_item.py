"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""

from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.rules.data_size_rule import DataSizeRule
from x_ray.healthcheck.rules.fragmentation_rule import FragmentationRule
from x_ray.healthcheck.rules.op_latency_rule import OpLatencyRule
from x_ray.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
)
from x_ray.utils import yellow, escape_markdown, format_size


class CollInfoItem(BaseItem):
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

        def enum_collections(name, node, func, **kwargs):
            client = node["client"]
            latency = node.get("pingLatencySec", 0)
            host = node["host"] if "host" in node else "cluster"
            if latency > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(f"Skip {host} because it has been irresponsive for {latency / 60:.2f} minutes.")
                )
                return None, None
            dbs = client.admin.command("listDatabases").get("databases", [])
            raw_result = []
            test_result = []
            for db_obj in dbs:
                db_name = db_obj.get("name")
                if db_name in ["admin", "local", "config"]:
                    self._logger.debug("Skipping system database: %s", db_name)
                    continue
                db = client[db_name]
                collections = db.list_collections()

                for coll_info in collections:
                    coll_name = coll_info.get("name")
                    coll_type = coll_info.get("type", "collection")
                    # TODO: support timeseries collections
                    if coll_type != "collection":
                        self._logger.debug(
                            "Skipping non-collection type: %s (%s)",
                            coll_name,
                            coll_type,
                        )
                        continue
                    if coll_name.startswith("system."):
                        self._logger.debug("Skipping system collection: %s.%s", db_name, coll_name)
                        continue
                    self._logger.debug("Gathering stats for collection: `%s.%s`", db_name, coll_name)

                    args = {"storageStats": {}}
                    args["latencyStats"] = {"histograms": True}
                    stats = db.get_collection(coll_name).aggregate([{"$collStats": args}]).next()
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
        result = enum_all_nodes(
            nodes,
            func_sh_cluster=lambda name, node, **kwargs: enum_collections(name, node, func_overview, **kwargs),
            func_rs_cluster=lambda name, node, **kwargs: enum_collections(name, node, func_overview, **kwargs),
            func_rs_member=lambda name, node, **kwargs: enum_collections(name, node, func_node, **kwargs),
            func_shard_member=lambda name, node, **kwargs: enum_collections(name, node, func_node, **kwargs),
        )
        self.captured_sample = result

    @property
    def review_result(self):
        result = self.captured_sample
        data = []
        stats_table = {
            "type": "table",
            "caption": "Storage Stats",
            "columns": [
                {"name": "Namespace", "type": "string"},
                {"name": "Size", "type": "string"},
                {"name": "Storage Size", "type": "string"},
                {"name": "Avg Object Size", "type": "string"},
                {"name": "Total Index Size", "type": "string"},
                {"name": "Index / Storage", "type": "decimal"},
            ],
            "rows": [],
        }
        frag_table = {
            "type": "table",
            "caption": "Storage Fragmentation",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Collection Fragmentation", "type": "string"},
                {"name": "Index Fragmentation", "type": "decimal", "align": "left"},
            ],
            "rows": [],
        }
        latency_table = {
            "type": "table",
            "caption": "Operation Latency",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Host", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Read Latency", "type": "string"},
                {"name": "Write Latency", "type": "decimal"},
                {"name": "Command Latency", "type": "decimal"},
                {"name": "Transaction Latency", "type": "decimal"},
            ],
            "rows": [],
        }
        data_sizes = {}
        data_frag = []
        data_latency = []
        data.append(stats_table)
        data.append({"type": "chart", "data": data_sizes})
        data.append(frag_table)
        data.append({"type": "chart", "data": data_frag})
        data.append(latency_table)
        data.append({"type": "chart", "data": data_latency})

        def func_overview(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            if raw_result is None:
                stats_table["rows"].append(["n/a", "n/a", "n/a", "n/a", "n/a", "n/a"])
                return
            for stats in raw_result:
                ns = stats["ns"]
                storage_stats = stats.get("storageStats", {})
                size = storage_stats.get("size", 0)
                storage_size = storage_stats.get("storageSize", 0)
                avg_obj_size = storage_stats.get("avgObjSize", 0)
                total_index_size = storage_stats.get("totalIndexSize", 0)
                index_data_ratio = round(total_index_size / storage_size, 4) if size > 0 else 0
                stats_table["rows"].append(
                    [
                        escape_markdown(ns),
                        format_size(size),
                        format_size(storage_size),
                        format_size(avg_obj_size),
                        format_size(total_index_size),
                        f"{index_data_ratio:.2%}",
                    ]
                )
                data_sizes[ns] = {"size": size, "index_size": total_index_size}

        def func_node(set_name, node, **kwargs):
            raw_result = node["rawResult"]
            host = node["host"]
            if raw_result is None:
                frag_table["rows"].append([host, "n/a", "n/a", "n/a"])
                return
            for stats in raw_result:
                ns = stats["ns"]
                # Fragmentation visualization
                coll_frag = stats.get("collFragmentation", {}).get("fragmentation", 0)
                index_frags = stats.get("indexFragmentations", [])
                total_reusable_size = 0
                total_index_size = 0
                index_details = []
                for index in index_frags:
                    total_reusable_size += index.get("reusable", 0)
                    total_index_size += index.get("totalSize", 0)
                    index_name = escape_markdown(index.get("indexName", ""))
                    fragmentation = index.get("fragmentation", 0)
                    index_details.append(f"{index_name}: {fragmentation:.2%}")
                index_frag = round(total_reusable_size / total_index_size, 4) if total_index_size > 0 else 0
                frag_table["rows"].append(
                    [
                        escape_markdown(set_name),
                        host,
                        escape_markdown(ns),
                        f"{coll_frag:.2%}",
                        f"{index_frag:.2%}<br/><pre>{'<br/>'.join(index_details)}</pre>",
                    ]
                )
                label = f"{set_name}/{host}"
                data_frag.append(
                    {
                        "label": label,
                        "ns": ns,
                        "collFrag": coll_frag,
                        "indexFrag": index_frag,
                    }
                )
                # Latency visualization
                avg_reads_latency = stats.get("latencyStats", {}).get("reads_latency", 0)
                avg_writes_latency = stats.get("latencyStats", {}).get("writes_latency", 0)
                avg_commands_latency = stats.get("latencyStats", {}).get("commands_latency", 0)
                avg_transactions_latency = stats.get("latencyStats", {}).get("transactions_latency", 0)
                latency_table["rows"].append(
                    [
                        escape_markdown(set_name),
                        host,
                        escape_markdown(ns),
                        f"{avg_reads_latency:.2f}ms",
                        f"{avg_writes_latency:.2f}ms",
                        f"{avg_commands_latency:.2f}ms",
                        f"{avg_transactions_latency:.2f}ms",
                    ]
                )
                data_latency.append(
                    {
                        "label": label,
                        "ns": ns,
                        "readsLatency": avg_reads_latency,
                        "writesLatency": avg_writes_latency,
                        "commandsLatency": avg_commands_latency,
                        "transactionsLatency": avg_transactions_latency,
                    }
                )

        enum_result_items(
            result,
            func_sh_cluster=func_overview,
            func_rs_cluster=func_overview,
            func_rs_member=func_node,
            func_shard_member=func_node,
        )

        return {"title": self.name, "description": self.description, "data": data}
