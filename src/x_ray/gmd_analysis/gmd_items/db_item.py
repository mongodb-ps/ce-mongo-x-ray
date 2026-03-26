"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from typing import Any, Optional

from x_ray.gmd_analysis.parsers.db_parser import DBParser
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.gmd_analysis.gmd_items.base_item import BaseItem
from x_ray.healthcheck.parsers.base_parser import BaseParser


class DBItem(BaseItem):
    def __init__(self, output_folder: str, config, **kwargs):
        super().__init__(output_folder, config, **kwargs)
        self.name: str = "Databases"
        self._sharded_databases: Optional[dict[str, Any]] = None
        self._databases: Optional[dict[str, Any]] = None

        def get_sharded_databases(block):
            self._sharded_databases = block.get("output", {})

        def get_databases(block):
            self._databases = block.get("output", {})

        self.watch_one(GMD_EVENTS.SHARDED_DATABASES, get_sharded_databases)
        self.watch_one(GMD_EVENTS.LIST_OF_DATABASES, get_databases)

    def review_results_markdown(self, output) -> None:
        assert (
            self._databases is not None
        ), f"GMD subsection {GMD_EVENTS.LIST_OF_DATABASES.value} should be available for review."
        parser: BaseParser = DBParser()
        parsed_data = parser.markdown({"databases": self._databases, "sharded_databases": self._sharded_databases})
        output.write(parsed_data)
