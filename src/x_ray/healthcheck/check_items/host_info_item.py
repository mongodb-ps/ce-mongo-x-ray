from x_ray.healthcheck.check_items.base_item import BaseItem
from x_ray.healthcheck.parsers.host_info_parser import HostInfoParser
from x_ray.healthcheck.rules.host_info_rule import HostInfoRule
from x_ray.healthcheck.rules.numa_rule import NumaRule
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY, discover_nodes, enum_all_nodes, enum_result_items
from x_ray.utils import yellow, format_size


class HostInfoItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Host Information"
        self._description = "Collects and reviews host hardware and OS information.  \n"
        self._description += "- Whether the hosts are using the same hardware.\n\n"
        self._description += "- Whether NUMA is enabled on the hosts.\n"
        self._host_info_rule = HostInfoRule(config)
        self._numa_rule = NumaRule(config)

    def test(self, *args, **kwargs):
        """
        Main test method to gather host information.
        """
        client = kwargs.get("client")
        parsed_uri = kwargs.get("parsed_uri")
        nodes = discover_nodes(client, parsed_uri)

        host_infos = {}

        def func_single(name, node, **kwargs):
            client = node["client"]
            version = node.get("version", None)
            if "pingLatencySec" in node and node["pingLatencySec"] > MAX_MONGOS_PING_LATENCY:
                self._logger.warning(
                    yellow(
                        f"Skip {node['host']} because it has been irresponsive for {node['pingLatencySec'] / 60:.2f} minutes."
                    )
                )
                return None, None
            host_info = client.admin.command("hostInfo")
            test_result, _ = self._numa_rule.apply(host_info, extra_info={"host": node["host"], "version": version})
            if name not in host_infos:
                host_infos[name] = []
            host_infos[name].append(host_info)
            return test_result, host_info

        result = enum_all_nodes(
            nodes,
            func_rs_member=func_single,
            func_mongos_member=func_single,
            func_shard_member=func_single,
            func_config_member=func_single,
        )
        for set_name, info in host_infos.items():
            test_result, _ = self._host_info_rule.apply(info, extra_info={"set_name": set_name})
            cluster_map = result["map"]
            if set_name not in cluster_map:
                cluster = cluster_map["config"]
            else:
                cluster = cluster_map[set_name]
            cluster["testResult"] = test_result

        self.captured_sample = result

    @property
    def review_result_markdown(self):
        """
        Review the gathered host information.
        """
        result = self.captured_sample
        host_infos = []

        def func_component(name, node, **kwargs):
            members = node["members"]
            host_infos.extend([(m["host"], m["rawResult"]) for m in members])

        enum_result_items(
            result,
            func_rs_cluster=func_component,
            func_all_mongos=func_component,
            func_shard=func_component,
            func_config=func_component,
        )
        parser = HostInfoParser()

        return parser.markdown(host_infos, caller=self.__class__.__name__)
