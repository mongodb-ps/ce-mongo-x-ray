from x_ray.gmd_analysis.gmd_items.base_item import BaseItem, get_version
from x_ray.healthcheck.parsers.host_info_parser import HostInfoParser
from x_ray.healthcheck.rules.host_info_rule import HostInfoRule
from x_ray.healthcheck.rules.numa_rule import NumaRule


class HostInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name = "Host Information"
        self.description = "Collects and analyzes host information from GMD logs."
        self._host_info = None
        self._host_info_rule = HostInfoRule(config)
        self._numa_rule = NumaRule(config)
        self._host_info_parser = HostInfoParser()

    def test(self, block):
        subsection = block.get("subsection", "")
        if subsection == "host_info":
            self._host_info = block.get("output", {})
        elif subsection == "server_build_info":
            version = get_version(block)
            if version is not None:
                self._server_version = version
        else:
            return
        if not self._host_info or not self._server_version:
            return
        test_result, _ = self._host_info_rule.apply([self._host_info])
        self.append_test_results(test_result)
        test_result, _ = self._numa_rule.apply(self._host_info, extra_info={"version": self._server_version})
        self.append_test_results(test_result)
        self.captured_sample = self._host_info

    def review_results_markdown(self, output):
        super().review_results_markdown(output)
        data = self.captured_sample
        host = data.get("system", {}).get("hostname", "unknown_host")
        parsed_output = self._host_info_parser.markdown([(host, data)])
        output.write(parsed_output)
