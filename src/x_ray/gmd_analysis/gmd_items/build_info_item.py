from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
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

        def get_build_info(block):
            self._build_info = block.get("output", {})

        def process_build_info():
            test_result, _ = self._version_eol_rule.apply(self._build_info, extra_info={"host": self._hostname})
            self.append_test_results(test_result)
            self.captured_sample = self._build_info

        self.subscribe_one(GMD_EVENTS.SERVER_BUILD_INFO, get_build_info)
        self.subscribe_all({GMD_EVENTS.SERVER_BUILD_INFO, GMD_EVENTS.HOST_INFO}, process_build_info)

    def review_results_markdown(self, output):
        data = self.captured_sample
        parsed_output = self._build_info_parser.markdown(
            [(self._set_name, self._hostname, data)], caller=self.__class__.__name__
        )
        output.write(parsed_output)
