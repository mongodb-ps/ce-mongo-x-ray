from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.build_info_parser import BuildInfoParser
from x_ray.healthcheck.rules.version_eol_rule import VersionEOLRule


class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name = "Build Information"
        self.description = "Collects and analyzes build information from GMD logs."
        self._build_info = {}
        self._version_eol_rule = VersionEOLRule(config)
        self._build_info_parser = BuildInfoParser()

    def test(self, block):
        super().test(block)
        sub_section = block.get("subsection", "")
        if sub_section not in ["server_build_info", "host_info"]:
            return
        if sub_section == "server_build_info":
            self._build_info = block.get("output", {})
        if not self._hostname or not self._build_info:
            return
        test_result, _ = self._version_eol_rule.apply(self._build_info, extra_info={"host": self._hostname})
        self.append_test_results(test_result)
        self.captured_sample = self._build_info

    def review_results_markdown(self, output):
        data = self.captured_sample
        parsed_output = self._build_info_parser.markdown(
            [(self._set_name, self._hostname, data)], caller=self.__class__.__name__
        )
        output.write(parsed_output)
