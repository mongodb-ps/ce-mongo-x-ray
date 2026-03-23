"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from time import sleep
from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.cache_parser import CacheParser
from x_ray.healthcheck.parsers.conn_parser import ConnParser
from x_ray.healthcheck.parsers.opcounter_parser import OpcounterParser
from x_ray.healthcheck.parsers.query_targeting_parser import QueryTargetingParser
from x_ray.healthcheck.rules.cache_rule import CacheRule
from x_ray.healthcheck.rules.connections_rule import ConnectionsRule
from x_ray.healthcheck.rules.query_targeting_rule import QueryTargetingRule
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items
from x_ray.utils import green, yellow

SERVER_STATUS_INTERVAL = 5


class ServerStatusItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Server Status Information"
        self._description = "Collects and reviews server status metrics.\n\n"
        self._description += "- Whether used/total connection ratio is too high.\n"
        self._description += "- Whether query targeting is poor.\n"
        self._description += "- Whether the cache read into rate is too high.\n"
        self._description += "- Whether updates ratio is too high.\n"
        self._description += "- Whether dirty data ratio is too high.\n"
        self._description += "- Whether cache fill ratio is too high.\n"
        self._query_targeting_rule = QueryTargetingRule(config)
        self._connections_rule = ConnectionsRule(config)
        self._cache_rule = CacheRule(config)

    def test(self, *args, **kwargs):
        """
        Run the server status test.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        def func_first_req(set_name, node, server_status):
            # First request do nothing but return the server status as is.
            # The test will be in the 2nd request.
            return [], {"server_status": server_status}

        def func_2nd_req(set_name, node, server_status):
            host = node["host"]
            test_result1, raw_result1 = self._connections_rule.apply(server_status, extra_info={"host": host})
            test_result2, raw_result2 = (
                self._query_targeting_rule.apply(server_status, extra_info={"host": host})
                if set_name != "mongos"
                else ([], None)
            )
            test_result = test_result1 + test_result2
            self.append_test_results(test_result)
            raw_result = {"connections": raw_result1, "query_targeting": raw_result2, "server_status": server_status}

            return test_result, raw_result

        def enumerator(set_name, node, **kwargs):
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            client = node["client"]
            server_status = client.admin.command("serverStatus")
            func_req = kwargs.get("func_req")
            test_result, raw_result = func_req(set_name, node, server_status)
            return test_result, raw_result

        nodes = discover_nodes(client, parsed_uri)

        def func_all_first(set_name, node, **kwargs):
            return enumerator(set_name, node, func_req=func_first_req, **kwargs)

        result1 = enum_all_nodes(
            nodes,
            func_mongos_member=func_all_first,
            func_rs_member=func_all_first,
            func_shard_member=func_all_first,
            func_config_member=func_all_first,
        )
        # Sleep for 5s to capture next status.
        self._logger.info("Sleep %s to capture next server status.", green(f"{SERVER_STATUS_INTERVAL} seconds"))
        sleep(SERVER_STATUS_INTERVAL)

        def func_all_2nd(set_name, node, **kwargs):
            return enumerator(set_name, node, func_req=func_2nd_req, **kwargs)

        result2 = enum_all_nodes(
            nodes,
            func_mongos_member=func_all_2nd,
            func_rs_member=func_all_2nd,
            func_shard_member=func_all_2nd,
            func_config_member=func_all_2nd,
        )

        # These metrics needs to compare 2 `serverStatus` results
        cache = {}

        def func_data_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if not raw_result:
                cache[host] = {
                    "setName": set_name,
                    "host": host,
                    "cacheSize": "n/a",
                    "inCacheSize": "n/a",
                    "readInto": "n/a",
                    "writtenFrom": "n/a",
                }
                return

            if host not in cache:
                # Enumerating result1
                cache[host] = raw_result
            else:
                # Enumerating result2
                test_result, parsed_data = self._cache_rule.apply(
                    raw_result["server_status"],
                    extra_info={"host": host, "server_status": cache[host]["server_status"]},
                )
                self.append_test_results(test_result)
                # Attach the test result and raw result to the original result.
                node["testResult"].extend(test_result)
                node["rawResult"]["cache"] = parsed_data

        enum_result_items(
            result1,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )
        enum_result_items(
            result2,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )

        op_counters = {}

        def func_all_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            if not raw_result:
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": "n/a",
                    "query": "n/a",
                    "update": "n/a",
                    "delete": "n/a",
                    "command": "n/a",
                    "getmore": "n/a",
                }
                return
            ops = raw_result["server_status"]["opcounters"]
            if host not in op_counters:
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": ops.get("insert", 0),
                    "query": ops.get("query", 0),
                    "update": ops.get("update", 0),
                    "delete": ops.get("delete", 0),
                    "command": ops.get("command", 0),
                    "getmore": ops.get("getmore", 0),
                }
            else:
                op_counters[host] = {
                    "set_name": set_name,
                    "host": host,
                    "insert": (ops["insert"] - op_counters[host]["insert"]) / SERVER_STATUS_INTERVAL,
                    "query": (ops["query"] - op_counters[host]["query"]) / SERVER_STATUS_INTERVAL,
                    "update": (ops["update"] - op_counters[host]["update"]) / SERVER_STATUS_INTERVAL,
                    "delete": (ops["delete"] - op_counters[host]["delete"]) / SERVER_STATUS_INTERVAL,
                    "command": (ops["command"] - op_counters[host]["command"]) / SERVER_STATUS_INTERVAL,
                    "getmore": (ops["getmore"] - op_counters[host]["getmore"]) / SERVER_STATUS_INTERVAL,
                }
                node["rawResult"]["op_counters"] = op_counters[host]

        enum_result_items(
            result1,
            func_mongos_member=func_all_member,
            func_rs_member=func_all_member,
            func_shard_member=func_all_member,
            func_config_member=func_all_member,
        )
        enum_result_items(
            result2,
            func_mongos_member=func_all_member,
            func_rs_member=func_all_member,
            func_shard_member=func_all_member,
            func_config_member=func_all_member,
        )
        self.captured_sample = [result1, result2]

    @property
    def review_result_markdown(self) -> str:
        result = self.captured_sample
        result2 = result[1]
        output: list[str] = []
        conns: list = []
        ops: list = []

        def func_all_members(set_name, node, **kwargs) -> None:
            raw_result = node.get("rawResult", {})
            host: str = node["host"]
            conns.append(
                {
                    "set_name": set_name,
                    "host": host,
                    "connections": raw_result.get("connections", None) if raw_result else None,
                }
            )
            ops.append(
                {
                    "set_name": set_name,
                    "host": host,
                    "op_counters": raw_result.get("op_counters", None) if raw_result else None,
                }
            )

        enum_result_items(
            result2,
            func_mongos_member=func_all_members,
            func_rs_member=func_all_members,
            func_shard_member=func_all_members,
            func_config_member=func_all_members,
        )
        conn_parser: BaseParser = ConnParser()
        output.append(conn_parser.markdown(conns))
        ops_parser: BaseParser = OpcounterParser()
        output.append(ops_parser.markdown(ops))

        qts: list = []
        caches: list = []

        def func_data_member(set_name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            qts.append(
                {
                    "set_name": set_name,
                    "host": host,
                    "query_targeting": raw_result.get("query_targeting", None) if raw_result else None,
                }
            )
            caches.append(
                {
                    "set_name": set_name,
                    "host": host,
                    "cache": raw_result.get("cache", None) if raw_result else None,
                }
            )

        enum_result_items(
            result2,
            func_rs_member=func_data_member,
            func_shard_member=func_data_member,
            func_config_member=func_data_member,
        )
        qt_parser: BaseParser = QueryTargetingParser()
        output.append(qt_parser.markdown(qts))

        cache_parser: BaseParser = CacheParser()
        output.append(cache_parser.markdown(caches))

        return "\n\n".join(output)
