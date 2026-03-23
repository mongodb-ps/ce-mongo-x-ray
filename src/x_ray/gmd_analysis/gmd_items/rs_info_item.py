"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from typing import Optional, TextIO

from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.parsers.rs_details_parser import RSDetailsParser
from x_ray.healthcheck.parsers.rs_overview_parser import RSOverviewParser
from x_ray.healthcheck.rules.rs_status_rule import RSStatusRule
from x_ray.healthcheck.rules.rs_config_rule import RSConfigRule
from x_ray.healthcheck.rules.oplog_window_rule import OplogWindowRule


class RSInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Replica Set Architecture"
        self.description: str = "Collects and analyzes replica set information from GMD logs."
        self._rs_status: Optional[dict] = None
        self._rs_config: Optional[dict] = None
        self._server_status: Optional[dict] = None
        self._replication_info: Optional[dict] = None
        self._oplog_info: Optional[dict] = None
        self._rs_status_rule: BaseRule = RSStatusRule(config)
        self._rs_config_rule: BaseRule = RSConfigRule(config)
        self._oplog_window_rule: BaseRule = OplogWindowRule(config)

        def get_replica_status(block):
            self._rs_status = block.get("output", {})
            test_result, _ = self._rs_status_rule.apply(self._rs_status)
            self.append_test_results(test_result)

        def get_replica_set_config(block):
            self._rs_config = block.get("output", {})
            # Because the result returned by replsetConfig command has an extra "config" layer,
            # compared to the one returned by rs.conf() in mongo shell.
            # We need to add this layer for the rule to work properly.
            test_result, _ = self._rs_config_rule.apply({"config": self._rs_config})
            self.append_test_results(test_result)

        def get_server_status(block):
            self._server_status = block.get("output", {})

        def get_replica_info(block):
            self._replication_info = block.get("output", {})

        self.watch_one(GMD_EVENTS.REPLICA_STATUS, get_replica_status)
        self.watch_one(GMD_EVENTS.REPLICA_SET_CONFIG, get_replica_set_config)
        self.watch_one(GMD_EVENTS.REPLICA_INFO, get_replica_info)
        self.watch_one(GMD_EVENTS.SERVER_STATUS_INFO, get_server_status)

        def analyze_oplog_window():
            time_delta = self._replication_info.get("timeDiff", 0)
            test_result, self._oplog_info = self._oplog_window_rule.apply(
                {
                    "serverStatus": self._server_status,
                    "timeDelta": time_delta,
                }
            )
            self.append_test_results(test_result)

        oplog_window_events = {
            GMD_EVENTS.SERVER_STATUS_INFO,
            GMD_EVENTS.REPLICA_INFO,
        }
        self.watch_all(oplog_window_events, analyze_oplog_window)

    def review_results_markdown(self, output: TextIO) -> None:
        assert (
            self._rs_config is not None
        ), f"GMD subsection {GMD_EVENTS.REPLICA_SET_CONFIG.value} should be available for review."
        assert (
            self._rs_status is not None
        ), f"GMD subsection {GMD_EVENTS.REPLICA_STATUS.value} should be available for review."
        assert (
            self._replication_info is not None
        ), f"GMD subsection {GMD_EVENTS.REPLICA_INFO.value} should be available for review."
        assert (
            self._server_status is not None
        ), f"GMD subsection {GMD_EVENTS.SERVER_STATUS_INFO.value} should be available for review."
        parsed_output = RSOverviewParser().markdown([(self._rs_config["_id"], self._rs_config)])
        output.write(parsed_output)
        data = {
            "set_name": self._rs_config["_id"],
            "rs_config": self._rs_config,
            "rs_status": self._rs_status,
            "oplog_info": self._oplog_info,
        }
        passed_output = RSDetailsParser().markdown(data)
        output.write(passed_output)
