"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.rules.version_eol_rule import VersionEOLRule
from x_ray.healthcheck.parsers.build_info_parser import BuildInfoParser
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items
from x_ray.utils import yellow
from x_ray.version import Version


class BuildInfoItem(BaseItem):
    """Build Info Check Item Module. Used to check MongoDB server build information."""

    def __init__(self, output_folder: str, config: dict = None):
        super().__init__(output_folder, config)
        self._name = "Build Information"
        self._description = "Collects & review server build information.\n\n"
        self._description += "- Whether the server is running a supported version.\n"
        self._version_eol_rule = VersionEOLRule(config)

    def test(self, *args, **kwargs):
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        def func_node(set_name, node, **kwargs):
            host = node["host"]
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {host} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            client = node["client"]
            raw_result = client.admin.command("buildInfo")
            test_result, _ = self._version_eol_rule.apply(raw_result, extra_info={"host": host})
            running_version = Version(raw_result.get("versionArray", None))
            node["version"] = running_version
            self.append_test_results(test_result)

            return test_result, raw_result

        raw_result = enum_all_nodes(
            nodes,
            func_mongos_member=func_node,
            func_rs_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )

        self.captured_sample = raw_result

    @property
    def review_result_markdown(self):
        result = self.captured_sample
        build_infos = []

        def func_node(name, node, **kwargs):
            raw_result = node.get("rawResult", {})
            host = node["host"]
            build_infos.append((name, host, raw_result))

        enum_result_items(
            result,
            func_mongos_member=func_node,
            func_rs_member=func_node,
            func_shard_member=func_node,
            func_config_member=func_node,
        )
        parser = BuildInfoParser()

        return parser.markdown(build_infos, caller=self.__class__.__name__)
