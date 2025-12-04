"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""

from datetime import datetime, timezone
from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.rules.index_rule import IndexRule
from x_ray.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    discover_nodes,
    enum_all_nodes,
    enum_result_items,
)
from x_ray.utils import yellow, escape_markdown, format_json_md


class IndexInfoItem(BaseItem):
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
                index_stats, extra_info={"host": host, "ns": ns}, check_items=["unused_indexes"]
            )
            return result

        def enum_namespaces(node, func, **kwargs):
            level = kwargs.get("level")
            client = node["client"]
            latency = node.get("pingLatencySec", 0)
            if latency > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
                )
                return None, None
            dbs = client.admin.command("listDatabases").get("databases", [])
            test_result, raw_result = [], []
            host = node.get("host", "cluster")
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
                    self._logger.debug(
                        "Gathering index stats of collection `%s.%s` on %s level...",
                        db_name,
                        coll_name,
                        level,
                    )
                    ns = f"{db_name}.{coll_name}"

                    # Check for number of indexes
                    index_stats = list(db[coll_name].aggregate([{"$indexStats": {}}]))
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

        result = enum_all_nodes(
            nodes,
            func_rs_cluster=lambda name, node, **kwargs: enum_namespaces(node, cluster_check, **kwargs),
            func_sh_cluster=lambda name, node, **kwargs: enum_namespaces(node, cluster_check, **kwargs),
            func_rs_member=lambda name, node, **kwargs: enum_namespaces(node, node_check, **kwargs),
            func_shard_member=lambda name, node, **kwargs: enum_namespaces(node, node_check, **kwargs),
        )

        self.captured_sample = result

    @property
    def review_result(self):
        result = self.captured_sample
        # TODO: display access/hour for each node.
        table = {
            "type": "table",
            "caption": "Index Review",
            "columns": [
                {"name": "Component", "type": "string"},
                {"name": "Namespace", "type": "string"},
                {"name": "Name", "type": "string"},
                {"name": "Key", "type": "string", "align": "left"},
                {"name": "Access per Hour", "type": "string"},
            ],
            "rows": [],
        }

        def func_cluster(set_name, node, **kwargs):
            raw_result = node.get("rawResult", [])
            if raw_result is None:
                table["rows"].append(["n/a", "n/a", "n/a", "n/a", "n/a"])
                return
            for item in raw_result:
                ns = item["ns"]
                capture_time = item["captureTime"]
                for stats in item["indexStats"]:
                    component = stats.get("shard", set_name)
                    key_md = format_json_md(stats["key"], indent=None)
                    access = stats["accesses"]
                    ops = access.get("ops", 0)
                    since = access.get("since", None)
                    spec = stats.get("spec", {})
                    options = get_index_options(spec)
                    options_md = f"<pre>{format_json_md(options)}</pre>" if len(options) > 0 else ""
                    access_per_hour = ops / (capture_time - since).total_seconds() / 3600
                    table["rows"].append(
                        [
                            escape_markdown(component),
                            escape_markdown(ns),
                            escape_markdown(stats["name"]),
                            f"`{key_md}`{options_md}",
                            access_per_hour,
                        ]
                    )

        enum_result_items(result, func_sh_cluster=func_cluster, func_rs_cluster=func_cluster)
        return {"name": self.name, "description": self.description, "data": [table]}


def get_index_options(spec):
    options = {}
    for key, value in spec.items():
        if key not in ["key", "name", "v"]:
            options[key] = value
    return options
