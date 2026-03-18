from typing import Any, Optional

from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.healthcheck.rules.query_targeting_rule import QueryTargetingRule
from x_ray.healthcheck.rules.connections_rule import ConnectionsRule
from x_ray.healthcheck.rules.cache_rule import CacheRule
from x_ray.healthcheck.parsers.cache_parser import CacheParser
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.parsers.query_targeting_parser import QueryTargetingParser
from x_ray.healthcheck.parsers.conn_parser import ConnParser


class ServerStatusItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Server Status"
        self.description: str = "Collects and analyzes server status information from GMD logs."
        self._server_status: Optional[dict[str, Any]] = None
        self._is_master: Optional[dict[str, Any]] = None
        self._host_info: Optional[dict[str, Any]] = None
        self._query_targeting: Optional[dict[str, Any]] = None
        self._connections: Optional[dict[str, Any]] = None
        self._wt_cache: Optional[dict[str, Any]] = None
        self._hostname = None
        self._set_name = None
        self._query_targeting_rule = QueryTargetingRule(config)
        self._connections_rule = ConnectionsRule(config)
        self._cache_rule = CacheRule(config)

        def get_server_status(block):
            self._server_status = block.get("output", {})

        def get_is_master(block):
            self._is_master = block.get("output", {})

        def get_host_info(block):
            self._host_info = block.get("output", {})

        def process_server_status():
            self._set_name = self._is_master.get("setName", "mongos")
            self._hostname = self._is_master.get("me", self._host_info["system"]["hostname"])
            if self._server_status["process"] == "mongod":
                test_result, self._query_targeting = self._query_targeting_rule.apply(
                    self._server_status, extra_info={"host": self._hostname}
                )
                self.append_test_results(test_result)
                test_result, self._wt_cache = self._cache_rule.apply(
                    self._server_status, extra_info={"host": self._hostname}
                )
                self.append_test_results(test_result)
            test_result, self._connections = self._connections_rule.apply(
                self._server_status, extra_info={"host": self._hostname}
            )
            self.append_test_results(test_result)

        self.watch_one(GMD_EVENTS.SERVER_STATUS_INFO, get_server_status)
        self.watch_one(GMD_EVENTS.ISMASTER, get_is_master)
        self.watch_one(GMD_EVENTS.HOST_INFO, get_host_info)

        self.watch_all(
            {GMD_EVENTS.SERVER_STATUS_INFO, GMD_EVENTS.ISMASTER, GMD_EVENTS.HOST_INFO}, process_server_status
        )

    def review_results_markdown(self, output) -> None:
        assert self._server_status is not None, "Server status data should be available for review."
        assert self._is_master is not None, "IsMaster data should be available for review."
        assert self._host_info is not None, "Host info data should be available for review."
        assert self._hostname is not None, "Hostname should be available for review."
        assert self._set_name is not None, "Set name should be available for review."

        if self._query_targeting is not None:
            parser: BaseParser = QueryTargetingParser()
            parsed: str = parser.markdown(
                [
                    {
                        "set_name": self._set_name,
                        "host": self._hostname,
                        "query_targeting": self._query_targeting,
                    }
                ]
            )
            output.write(parsed)

        parser = ConnParser()
        parsed_output = parser.markdown(
            [
                {
                    "set_name": self._set_name,
                    "host": self._hostname,
                    "connections": self._connections,
                }
            ]
        )
        output.write(parsed_output)

        if self._wt_cache is not None:
            parser = CacheParser()
            parsed_output = parser.markdown(
                [
                    {
                        "set_name": self._set_name,
                        "host": self._hostname,
                        "cache": self._wt_cache,
                    }
                ]
            )
            output.write(parsed_output)
