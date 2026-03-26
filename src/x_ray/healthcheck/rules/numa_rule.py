"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class NumaRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._rule_desc.append("Checks if NUMA is correctly configured based on MongoDB version.")

    def apply(self, data: dict, **kwargs) -> tuple:
        """Check the NUMA node configuration for any issues.

        Args:
            data (dict): The `hostInfo` command result.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        version = kwargs.get("extra_info", {}).get("version", None)
        test_result = []
        assert (
            version is not None
        ), "Version information is required for NUMA check. Run BuildInfoItem before this check."
        numa_enabled = data.get("system", {}).get("numaEnabled", None)
        if numa_enabled is not None and numa_enabled and version <= "7.0":
            issue = create_issue(ISSUE.NUMA_ENABLED, host, params={"version": version, "host": host})
            test_result.append(issue)
        if numa_enabled is not None and not numa_enabled and version >= "8.0":
            issue = create_issue(ISSUE.NUMA_DISABLED, host, params={"version": version, "host": host})
            test_result.append(issue)

        return test_result, data
