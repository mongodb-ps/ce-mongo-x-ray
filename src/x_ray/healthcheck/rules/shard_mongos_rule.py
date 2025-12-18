"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY
from x_ray.healthcheck.issues import ISSUE, create_issue


class ShardMongosRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the sharded cluster mongos nodes for any issues.

        Args:
            data (object): The sharded cluster status data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        test_result = []
        active_mongos = []
        for mongos in data:
            if mongos.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                issue = create_issue(
                    ISSUE.IRRESPONSIVE_MONGOS,
                    host=mongos["host"],
                    params={"host": mongos["host"], "ping_latency": round(mongos["pingLatencySec"])},
                )
                test_result.append(issue)
            else:
                active_mongos.append(mongos["host"])

        if len(active_mongos) == 0:
            issue = create_issue(ISSUE.NO_ACTIVE_MONGOS, host="cluster")
            test_result.append(issue)
        if len(active_mongos) == 1:
            issue = create_issue(ISSUE.SINGLE_MONGOS, host="cluster", params={"mongos": active_mongos[0]})
            test_result.append(issue)
        return test_result, data
