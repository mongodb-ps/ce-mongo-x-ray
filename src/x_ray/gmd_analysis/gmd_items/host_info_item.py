from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.host_info_parser import HostInfoParser
from x_ray.healthcheck.rules.host_info_rule import HostInfoRule


class HostInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name = "Host Information"
        self.description = "Collects and analyzes host information from GMD logs."
        self._host_info_rule = HostInfoRule(config)
        self._host_info_parser = HostInfoParser()

    def test(self, block):
        super().test(block)
        if block.get("subsection", "") != "host_info":
            return
        output = block.get("output", {})
        test_result, _ = self._host_info_rule.apply([output])
        self.append_test_results(test_result)
        self.captured_sample = output

    def review_results_markdown(self, output):
        super().review_results_markdown(output)
        data = self.captured_sample
        host = data.get("system", {}).get("hostname", "unknown_host")
        parsed_output = self._host_info_parser.markdown([(host, data)])
        output.write(parsed_output)
