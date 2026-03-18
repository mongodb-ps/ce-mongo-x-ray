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
from x_ray.healthcheck.parsers.security_parser import SecurityParser
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items
from x_ray.utils import yellow
from x_ray.healthcheck.rules.security_rule import SecurityRule


class SecurityItem(BaseItem):
    """
    This module defines a checklist item for collecting and reviewing security-related information in MongoDB.
    """

    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Authentication & Security"
        self._description = "Collects & review security related information.\n\n"
        self._description += "- Whether authorization is enabled.\n"
        self._description += "- Whether log redaction is enabled.\n"
        self._description += "- Whether TLS is enabled and required.\n"
        self._description += "- Whether the bind IP is too permissive.\n"
        self._description += "- Whether the default port is used.\n"
        self._description += "- Whether auditing is enabled.\n"
        self._description += "- Whether encryption at rest is enabled and properly configured.\n"
        self._security_rule = SecurityRule(config)

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")

        nodes = discover_nodes(client, parsed_uri)

        def func_node(name, node, **kwargs):
            client = node["client"]
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            raw_result = client.admin.command("getCmdLineOpts")
            test_result, _ = self._security_rule.apply(raw_result, extra_info={"host": host})
            self.append_test_results(test_result)

            return test_result, raw_result

        result = enum_all_nodes(
            nodes,
            func_rs_member=func_node,
            func_mongos_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )

        self.captured_sample = result

    @property
    def review_result_markdown(self) -> str:
        raw_result = self.captured_sample
        raw_results: list = []

        def func_node(set_name, node, **kwargs):
            raw_results.append(
                {
                    "set_name": set_name,
                    "host": node.get("host"),
                    "command_line_opts": node.get("rawResult"),
                }
            )

        enum_result_items(
            raw_result,
            func_rs_member=func_node,
            func_mongos_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )
        parser: BaseParser = SecurityParser()
        return parser.markdown(raw_results)
