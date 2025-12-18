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


class ConnectionsRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._used_connection_ratio = thresholds.get("used_connection_ratio", 0.8)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check the connections usage for any issues.

        Args:
            data (object): The result from `serverStatus` command.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_result = []
        connections = data.get("connections", {})
        available = connections.get("available", 0)
        current = connections.get("current", 0)
        total = available + current
        if current / total > self._used_connection_ratio:
            issue = create_issue(
                ISSUE.HIGH_CONNECTION_USAGE_RATIO,
                host=host,
                params={
                    "current": current,
                    "total": total,
                    "used_connection_ratio": self._used_connection_ratio * 100,
                },
            )
            test_result.append(issue)

        return test_result, connections
