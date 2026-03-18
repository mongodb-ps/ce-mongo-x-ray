"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from typing import Any, Optional

from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.security_parser import SecurityParser
from x_ray.healthcheck.rules.security_rule import SecurityRule


class SecurityItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Security Information"
        self.description: str = "Collects and analyzes security information from GMD logs."
        self._command_line_opts: Optional[dict] = None
        self._is_master: Optional[dict[str, Any]] = None
        self._host_info: Optional[dict[str, Any]] = None
        self._hostname = None
        self._set_name = None
        self._security_rule: SecurityRule = SecurityRule(config)

        def get_is_master(block):
            self._is_master = block.get("output", {})

        def get_host_info(block):
            self._host_info = block.get("output", {})

        def get_command_line_opts(block):
            self._command_line_opts = block.get("output", {})

        def analyze_security():
            self._set_name = self._is_master.get("setName", "mongos")
            self._hostname = self._is_master.get("me", self._host_info["system"]["hostname"])
            test_result, _ = self._security_rule.apply(self._command_line_opts, extra_info={"host": self._hostname})
            self.append_test_results(test_result)

        self.watch_one(GMD_EVENTS.COMMAND_LINE_INFO, get_command_line_opts)
        self.watch_one(GMD_EVENTS.ISMASTER, get_is_master)
        self.watch_one(GMD_EVENTS.HOST_INFO, get_host_info)
        self.watch_all(
            {
                GMD_EVENTS.COMMAND_LINE_INFO,
                GMD_EVENTS.ISMASTER,
                GMD_EVENTS.HOST_INFO,
            },
            analyze_security,
        )

    def review_results_markdown(self, output) -> None:
        assert self._is_master is not None, "IsMaster data should be available for review."
        assert self._host_info is not None, "Host info data should be available for review."
        assert self._hostname is not None, "Hostname should be available for review."
        assert self._set_name is not None, "Set name should be available for review."
        assert self._command_line_opts is not None, "Command line options should be available for review."
        parser: BaseParser = SecurityParser()
        parsed_output = parser.markdown(
            [
                {
                    "set_name": self._set_name,
                    "host": self._hostname,
                    "command_line_opts": self._command_line_opts,
                }
            ]
        )
        output.write(parsed_output)
