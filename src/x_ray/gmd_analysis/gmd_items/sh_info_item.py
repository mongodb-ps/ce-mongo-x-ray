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
from x_ray.gmd_analysis.parsers.sh_details_parser import SHDetailsParser
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.parsers.sh_overview_parser import SHOverviewParser
from x_ray.healthcheck.rules.shard_mongos_rule import ShardMongosRule


class SHInfoItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Sharded Cluster Architecture"
        self.description: str = "Collects and analyzes sharded cluster information from GMD logs."
        self._shards: Optional[list] = None
        self._routers: Optional[list] = None
        self._csrs: Optional[str] = None
        self._converted_routers: Optional[dict] = None
        self._exec_time = None
        self._shard_mongos_rule: BaseRule = ShardMongosRule(config)

        def get_shards(block):
            self._shards = block.get("output", {})

        def get_routers(block):
            self._routers = block.get("output", {})
            self._exec_time = block["ts"]["end"]
            # convert to the format required by the rule
            all_mongos = [
                {
                    "host": mongos["_id"],
                    "pingLatencySec": (self._exec_time - mongos["ping"]).total_seconds(),
                    "lastPing": mongos["ping"],
                }
                for mongos in self._routers
            ]
            test_result, _ = self._shard_mongos_rule.apply(all_mongos)
            self.append_test_results(test_result)
            self._converted_routers = {mongos["host"]: mongos for mongos in all_mongos}

        def get_server_status(block):
            self._csrs = block.get("output", {}).get("sharding", {}).get("configsvrConnectionString", "")

        self.watch_one(GMD_EVENTS.ROUTERS, get_routers)
        self.watch_one(GMD_EVENTS.SHARDS, get_shards)
        self.watch_one(GMD_EVENTS.SERVER_STATUS_INFO, get_server_status)

    def review_results_markdown(self, output: TextIO) -> None:
        # Type assertions: if all events fired, these should not be None
        assert self._shards is not None, f"GMD subsection {GMD_EVENTS.SHARDS.value} should be available for review."
        assert self._routers is not None, f"GMD subsection {GMD_EVENTS.ROUTERS.value} should be available for review."
        assert (
            self._csrs is not None
        ), f"GMD subsection {GMD_EVENTS.SERVER_STATUS_INFO.value} should be available for review."

        # Convert the data to the format required by the markdown parser
        data = {
            "type": "SH",
            "map": {
                "mongos": {"members": self._routers},
            }
            | {shard["_id"]: shard for shard in self._shards},
            "rawResult": self._converted_routers,
        }
        parser: BaseParser = SHOverviewParser()
        output.write(parser.markdown(data))
        parser = SHDetailsParser()
        output.write(
            parser.markdown(
                {
                    "shards": self._shards,
                    "csrs": self._csrs,
                }
            )
        )
