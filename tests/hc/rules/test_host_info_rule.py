"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.host_info_rule import HostInfoRule
from x_ray.healthcheck.shared import SEVERITY

DATA_HOST_INFO_SAME_HARDWARE = [
    {
        "system": {"numCores": 4, "memLimitMB": 8192},
    },
    {
        "system": {"numCores": 4, "memLimitMB": 8192},
    },
    {
        "system": {"numCores": 4, "memLimitMB": 8192},
    },
]


DATA_HOST_INFO_DIFF_HARDWARE = [
    {
        "system": {"numCores": 4, "memLimitMB": 8192},
    },
    {
        "system": {"numCores": 8, "memLimitMB": 16384},
    },
    {
        "system": {"numCores": 4, "memLimitMB": 8192},
    },
]


def test_host_info_rule_same_hardware():
    rule = HostInfoRule()
    issues, _ = rule.apply(DATA_HOST_INFO_SAME_HARDWARE, extra_info={"set_name": "rs0"})
    assert len(issues) == 0


def test_host_info_rule_diff_hardware():
    rule = HostInfoRule()
    issues, _ = rule.apply(DATA_HOST_INFO_DIFF_HARDWARE, extra_info={"set_name": "rs0"})
    assert len(issues) == 1
    assert issues[0]["id"] == ISSUE.HOSTS_DIFFERENT_HARDWARE
    assert issues[0]["host"] == "cluster"
    assert issues[0]["severity"] == SEVERITY.LOW
