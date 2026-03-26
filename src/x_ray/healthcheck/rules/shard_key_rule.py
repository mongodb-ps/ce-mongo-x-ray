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


class ShardKeyRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._rule_desc.append("Checks for shard keys that are only on the _id field.")

    def apply(self, data: dict, **kwargs) -> tuple:
        """Check shard key configurations for issues.

        Args:
            data (dict): One document from `config.collections`.
            extra_info (dict, optional): Extra information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        test_results = []
        ns = data["_id"]
        key = data["key"]
        v = key.get("_id", None)
        if v in [-1, 1] and len(key.keys()) == 1:
            issue = create_issue(
                ISSUE.IMPROPER_SHARD_KEY,
                host="cluster",
                params={
                    "ns": ns,
                    "shard_key": f"{{_id: {v}}}",
                },
            )
            test_results.append(issue)
        return test_results, data
