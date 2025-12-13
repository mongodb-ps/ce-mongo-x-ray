from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
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

        def get_host_info(block):
            self._host_info = block.get("output", {})

        def process_build_info():
            test_result, _ = self._host_info_rule.apply([self._host_info], extra_info={"host": self._hostname})
            self.append_test_results(test_result)
            test_result, _ = self._numa_rule.apply(
                self._host_info, extra_info={"version": self._server_version, "host": self._hostname}
            )
            self.append_test_results(test_result)
            # self.captured_sample = self._host_info

        self.watch_one(GMD_EVENTS.HOST_INFO, get_host_info)
        self.watch_all({GMD_EVENTS.HOST_INFO, GMD_EVENTS.SERVER_BUILD_INFO}, process_build_info)

    def review_results_markdown(self, output):
        data = self._host_info
        if data is None:
            return
        host = data.get("system", {}).get("hostname", "unknown_host")
        parsed_output = self._host_info_parser.markdown([(host, data)])
        output.write(parsed_output)
