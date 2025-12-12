from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.rules.oplog_window_rule import OplogWindowRule
from x_ray.healthcheck.rules.rs_config_rule import RSConfigRule
from x_ray.healthcheck.rules.rs_status_rule import RSStatusRule
from x_ray.healthcheck.rules.shard_mongos_rule import ShardMongosRule
from x_ray.healthcheck.parsers.sh_overview_parser import SHOverviewParser
from x_ray.healthcheck.parsers.rs_overview_parser import RSOverviewParser
from x_ray.healthcheck.parsers.rs_details_parser import RSDetailsParser
from x_ray.healthcheck.shared import (
    MAX_MONGOS_PING_LATENCY,
    enum_all_nodes,
    discover_nodes,
    enum_result_items,
)
from x_ray.utils import yellow, escape_markdown


class ClusterItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Cluster Information"
        self._description = "Collects and reviews cluster configuration and status.\n\n"
        self._description += "- The following items apply to replica set, shards and CSRS:\n"
        self._description += "    - Replication status check.\n"
        self._description += "    - Replication config check.\n"
        self._description += "    - Oplog window check (Both `oplogMinRetentionHours` and oplog size are considered).\n"
        self._description += "- Whether there are irresponsive mongos nodes.\n"
        self._description += "- Whether active mongos nodes are enough.\n"
        self._rs_status_rule = RSStatusRule(config)
        self._rs_config_rule = RSConfigRule(config)
        self._shard_mongos_rule = ShardMongosRule(config)
        self._oplog_window_rule = OplogWindowRule(config)

    def _check_rs(self, set_name, node, **kwargs):
        """
        Run the cluster level checks
        """
        client = node["client"]
        latency = node.get("pingLatencySec", 0)
        if latency > MAX_MONGOS_PING_LATENCY:
            self._logger.warning(
                yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
            )
            return None, None
        test_result = []
        replset_status = client.admin.command("replSetGetStatus")
        replset_config = client.admin.command("replSetGetConfig")
        raw_result = {
            "replsetStatus": replset_status,
            "replsetConfig": replset_config,
        }

        # Check replica set status and config
        result, _ = self._rs_status_rule.apply(replset_status)
        test_result.extend(result)
        result, _ = self._rs_config_rule.apply(replset_config)
        test_result.extend(result)

        self.append_test_results(test_result)

        return test_result, raw_result

    def _check_sh(self, set_name, node, **kwargs):
        """
        Check if the sharded cluster is available and connected.
        """
        test_result, _ = self._shard_mongos_rule.apply(node["map"]["mongos"]["members"])
        self.append_test_results(test_result)
        raw_result = {
            mongos["host"]: {
                "pingLatencySec": mongos["pingLatencySec"],
                "lastPing": mongos["lastPing"],
            }
            for mongos in node["map"]["mongos"]["members"]
        }
        return test_result, raw_result

    def _check_rs_member(self, set_name, node, **kwargs):
        """
        Run the replica set member level checks
        """
        test_result = []
        client = node["client"]
        latency = node.get("pingLatencySec", 0)
        if latency > MAX_MONGOS_PING_LATENCY:
            self._logger.warning(
                yellow(f"Skip {node['host']} because it has been irresponsive for {latency / 60:.2f} minutes.")
            )
            return None, None
        # Gather oplog information
        stats = client.local.command("collStats", "oplog.rs")
        server_status = client.admin.command("serverStatus")
        last_oplog = next(client.local.oplog.rs.find().sort("$natural", -1).limit(1))["ts"].time
        first_oplog = next(client.local.oplog.rs.find().sort("$natural", 1).limit(1))["ts"].time
        test_result, parsed_data = self._oplog_window_rule.apply(
            {
                "stats": stats,
                "serverStatus": server_status,
                "firstOplogEntry": first_oplog,
                "lastOplogEntry": last_oplog,
            },
            extra_info={"host": node["host"]},
        )

        self.append_test_results(test_result)

        return test_result, {
            "oplogInfo": {
                "oplogStats": {
                    "size": stats["size"],
                    "count": stats["count"],
                    "storageSize": stats["storageSize"],
                    "maxSize": stats["maxSize"],
                    "averageObjectSize": stats["avgObjSize"],
                },
            }
            | parsed_data
        }

    def test(self, *args, **kwargs):
        """
        Main test method to gather sharded cluster information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)
        result = enum_all_nodes(
            nodes,
            func_rs_cluster=self._check_rs,
            func_sh_cluster=self._check_sh,
            func_rs_member=self._check_rs_member,
            func_shard=self._check_rs,
            func_shard_member=self._check_rs_member,
            func_config=self._check_rs,
            func_config_member=self._check_rs_member,
        )

        self.captured_sample = result

    @property
    def review_result_markdown(self):
        result = self.captured_sample
        output = ""
        rs_configs = []
        rs_infos = []

        def func_sh(_, result, **kwargs):
            nonlocal output
            parser = SHOverviewParser()
            output += parser.markdown(result)

        def func_rs(set_name, result, **kwargs):
            raw_result = result["rawResult"]
            if raw_result is None:
                rs_config = None
                rs_status = None
            else:
                rs_config = raw_result["replsetConfig"]["config"]
                rs_status = raw_result["replsetStatus"]
            oplog_info = {}
            for m in result["members"]:
                r_result = m.get("rawResult", None)
                oplog_info[m["host"]] = {
                    "configured_retention_hours": (
                        "N/A"
                        if r_result is None
                        else round(r_result.get("oplogInfo", {}).get("configured_retention_hours", 0), 2)
                    ),
                    "current_retention_hours": (
                        "N/A"
                        if r_result is None
                        else round(r_result.get("oplogInfo", {}).get("current_retention_hours", 0), 2)
                    ),
                }
            rs_configs.append((set_name, rs_config))
            rs_infos.append(
                {"set_name": set_name, "rs_config": rs_config, "rs_status": rs_status, "oplog_info": oplog_info}
            )

        enum_result_items(
            result,
            func_sh_cluster=func_sh,
            func_rs_cluster=func_rs,
            func_shard=func_rs,
            func_config=func_rs,
        )

        if len(rs_configs) > 0:
            parser = RSOverviewParser()
            output += parser.markdown(rs_configs)
        for rs_info in rs_infos:
            parser = RSDetailsParser()
            output += parser.markdown(rs_info)

        return output
