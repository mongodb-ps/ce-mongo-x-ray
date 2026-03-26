from typing import Any

from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.build_info_parser import BuildInfoParser
from x_ray.healthcheck.rules.version_eol_rule import VersionEOLRule


class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Build Information"
        self._build_info: dict[str, Any] = {}
        self._rules["version_eol"] = VersionEOLRule(config)

        def get_build_info(block):
            self._build_info = block.get("output", {})

        def process_build_info():
            test_result, _ = self._rules["version_eol"].apply(self._build_info, extra_info={"host": self._hostname})
            self.append_test_results(test_result)
            # self.captured_sample = self._build_info

        self.watch_one(GMD_EVENTS.SERVER_BUILD_INFO, get_build_info)
        self.watch_all({GMD_EVENTS.SERVER_BUILD_INFO, GMD_EVENTS.HOST_INFO}, process_build_info)

    def review_results_markdown(self, output) -> None:
        data = self._build_info
        assert data is not None, f"GMD subsection {GMD_EVENTS.SERVER_BUILD_INFO.value} should be available for review."
        parser: BaseParser = BuildInfoParser()
        parsed_output = parser.markdown([(self._set_name, self._hostname, data)], caller=self.__class__.__name__)
        output.write(parsed_output)
