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


class HostInfoRule(BaseRule):
    def apply(self, data, **kwargs):
        """Check the host information for any issues.
        Args:
            data (object): The result from `hostInfo` command.
            extra_info (dict, optional): Extra information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        test_results = []
        set_name = kwargs.get("extra_info", {}).get("set_name", "unknown")
        hardware_info = [
            {
                "cores": host_info["system"]["numCores"],
                "memLimitMB": host_info["system"]["memLimitMB"],
            }
            for host_info in data
        ]

        cores = {info["cores"] for info in hardware_info}
        mem_limits = {info["memLimitMB"] for info in hardware_info}

        if len(cores) > 1 or len(mem_limits) > 1:
            issue = create_issue(
                ISSUE.HOSTS_DIFFERENT_HARDWARE,
                host="cluster",
                params={"set_name": set_name},
            )
            test_results.append(issue)

        return test_results, data
