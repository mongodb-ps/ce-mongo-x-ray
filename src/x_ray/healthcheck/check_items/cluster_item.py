from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.rules.oplog_window_rule import OplogWindowRule
from x_ray.healthcheck.rules.rs_config_rule import RSConfigRule
from x_ray.healthcheck.rules.rs_status_rule import RSStatusRule
from x_ray.healthcheck.rules.shard_mongos_rule import ShardMongosRule
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
    def review_result(
        self,
    ):
        result = self.captured_sample
        data = []
        sh_overview = {
            "type": "table",
            "caption": "Sharded Cluster Overview",
            "columns": [
                {"name": "#Shards", "type": "integer"},
                {"name": "#Mongos", "type": "integer"},
                {"name": "#Active mongos", "type": "integer"},
            ],
            "rows": [],
        }
        rs_overview = {
            "type": "table",
            "caption": f"{'Components' if result['type'] == 'SH' else 'Replica Set'} Overview",
            "columns": [
                {"name": "Name", "type": "string"},
                {"name": "#Members", "type": "integer"},
                {"name": "#Voting Members", "type": "integer"},
                {"name": "#Arbiters", "type": "integer"},
                {"name": "#Hidden Members", "type": "integer"},
            ],
            "rows": [],
        }
        mongos_details = {
            "type": "table",
            "caption": "Component Details - `mongos`",
            "columns": [
                {"name": "Host", "type": "string"},
                {"name": "Ping Latency (sec)", "type": "integer"},
                {"name": "Last Ping", "type": "boolean"},
            ],
            "rows": [],
        }
        if result["type"] == "SH":
            data.append(sh_overview)
        data.append(rs_overview)
        if result["type"] == "SH":
            data.append(mongos_details)

        def func_sh(name, result, **kwargs):
            raw_result = result["rawResult"]
            if raw_result is None:
                mongos_details["rows"].append(["n/a", "n/a", "n/a"])
                return
            component_names = result["map"].keys()
            shards = sum(1 for name in component_names if name not in ["mongos", "config"])
            mongos = len(result["map"]["mongos"]["members"])
            active_mongos = 0
            for host, info in raw_result.items():
                ping_latency = info.get("pingLatencySec", 0)
                last_ping = info.get("lastPing", False)
                mongos_details["rows"].append([host, ping_latency, last_ping])
                if ping_latency < MAX_MONGOS_PING_LATENCY:
                    active_mongos += 1
            sh_overview["rows"].append([shards, mongos, active_mongos])

        def func_rs(set_name, result, **kwargs):
            raw_result = result["rawResult"]
            if raw_result is None:
                return
            repl_config = raw_result["replsetConfig"]["config"]
            members = repl_config["members"]
            num_members = len(members)
            num_voting = sum(1 for m in members if m["votes"] > 0)
            num_arbiters = sum(1 for m in members if m["arbiterOnly"])
            num_hidden = sum(1 for m in members if m["hidden"])
            rs_overview["rows"].append(
                [
                    escape_markdown(set_name),
                    num_members,
                    num_voting,
                    num_arbiters,
                    num_hidden,
                ]
            )
            oplog_info = {}
            for m in result["members"]:
                r_result = m.get("rawResult", {})
                if r_result is None:
                    oplog_info[m["host"]] = {
                        "min_retention_hours": "n/a",
                        "current_retention_hours": "n/a",
                    }
                else:
                    oplog_info[m["host"]] = {
                        "min_retention_hours": round(
                            r_result.get("oplogInfo", {}).get("oplogMinRetentionHours", 0),
                            2,
                        ),
                        "current_retention_hours": round(
                            r_result.get("oplogInfo", {}).get("currentRetentionHours", 0),
                            2,
                        ),
                    }

            repl_status = result["rawResult"]["replsetStatus"]
            latest_optime = max(m["optime"]["ts"] for m in repl_status["members"])
            member_delay = {m["name"]: (latest_optime.time - m["optime"]["ts"].time) for m in repl_status["members"]}
            table_details = {
                "type": "table",
                "caption": f"Component Details - `{set_name}`",
                "columns": [
                    {"name": "Host", "type": "string"},
                    {"name": "_id", "type": "integer"},
                    {"name": "Arbiter", "type": "boolean"},
                    {"name": "Build Indexes", "type": "boolean"},
                    {"name": "Hidden", "type": "boolean"},
                    {"name": "Priority", "type": "integer"},
                    {"name": "Votes", "type": "integer"},
                    {"name": "Configured Delay (sec)", "type": "integer"},
                    {"name": "Current Delay (sec)", "type": "integer"},
                    {"name": "Oplog Window Hours", "type": "integer"},
                ],
                "rows": [],
            }
            for m in members:
                member_host = m["host"]
                min_retention_hours = oplog_info[member_host]["min_retention_hours"]
                current_retention_hours = oplog_info[member_host]["current_retention_hours"]
                if min_retention_hours in [0, "n/a"]:
                    retention_hours = current_retention_hours
                else:
                    retention_hours = max(min_retention_hours, current_retention_hours)
                table_details["rows"].append(
                    [
                        member_host,
                        m["_id"],
                        m["arbiterOnly"],
                        m["buildIndexes"],
                        m["hidden"],
                        m["priority"],
                        m["votes"],
                        m.get("secondaryDelaySecs", m.get("slaveDelay", 0)),
                        (member_delay[member_host] if member_host in member_delay else "n/a"),
                        retention_hours,
                    ]
                )
            data.append(table_details)

        enum_result_items(
            result,
            func_sh_cluster=func_sh,
            func_rs_cluster=func_rs,
            func_shard=func_rs,
            func_config=func_rs,
        )
        return {"name": self.name, "description": self.description, "data": data}
