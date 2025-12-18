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
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the NUMA node configuration for any issues.

        Args:
            data (object): The `hostInfo` command result.
            extra_info (dict): Additional information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        version = kwargs.get("extra_info", {}).get("version", None)
        test_result = []
        enum_enabled = data.get("system").get("numaEnabled", None)
        if enum_enabled and version <= "7.0":
            issue = create_issue(ISSUE.NUMA_ENABLED, host, params={"version": version, "host": host})
            test_result.append(issue)
        if not enum_enabled and version >= "8.0":
            issue = create_issue(ISSUE.NUMA_DISABLED, host, params={"version": version, "host": host})
            test_result.append(issue)

        return test_result, data
