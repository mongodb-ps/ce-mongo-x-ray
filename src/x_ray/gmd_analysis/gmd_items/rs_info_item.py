from x_ray.utils import yellow
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.healthcheck.parsers.rs_details_parser import RSDetailsParser
from x_ray.healthcheck.parsers.rs_overview_parser import RSOverviewParser
from x_ray.healthcheck.rules.rs_status_rule import RSStatusRule
from x_ray.healthcheck.rules.rs_config_rule import RSConfigRule
from x_ray.healthcheck.rules.oplog_window_rule import OplogWindowRule


class RSInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name = "Replica Set Information"
        self.description = "Collects and analyzes replica set information from GMD logs."
        self._rs_status = None
        self._rs_config = None
        self._server_status = None
        self._replication_info = None
        self._oplog_info = None
        self._rs_status_rule = RSStatusRule(config)
        self._rs_config_rule = RSConfigRule(config)
        self._oplog_window_rule = OplogWindowRule(config)

        def get_replica_status(block):
            self._rs_status = block.get("output", {})
            test_result, _ = self._rs_status_rule.apply(self._rs_status)
            self.append_test_results(test_result)

        def get_replica_set_config(block):
            self._rs_config = block.get("output", {})
            test_result, _ = self._rs_config_rule.apply(self._rs_config)
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

    def review_results_markdown(self, output):
        if not self.all_events_fired():
            self._logger.warning(yellow("Not all required GMD blocks were captured. Skipping RSInfoItem review."))
            return
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
