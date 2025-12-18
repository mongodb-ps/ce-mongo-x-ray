"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.connections_rule import ConnectionsRule


DATA_CONNECTIONS_NORMAL = {
    "connections": {
        "current": 50,
        "available": 950,
    }
}

DATA_CONNECTIONS_HIGH_USAGE = {
    "connections": {
        "current": 900,
        "available": 100,
    }
}

config = {"used_connection_ratio": 0.8}


def test_connections_rule_no_issue():
    rule = ConnectionsRule(thresholds=config)
    issues, parsed_data = rule.apply(DATA_CONNECTIONS_NORMAL, extra_info={"host": "localhost:27017"})
    assert len(issues) == 0
    assert parsed_data == DATA_CONNECTIONS_NORMAL["connections"]


def test_connections_rule_high_usage():
    rule = ConnectionsRule(thresholds=config)
    issues, parsed_data = rule.apply(DATA_CONNECTIONS_HIGH_USAGE, extra_info={"host": "localhost:27017"})
    assert len(issues) == 1
    issue = issues[0]
    assert issue["id"] == ISSUE.HIGH_CONNECTION_USAGE_RATIO
    assert issue["host"] == "localhost:27017"
    assert parsed_data == DATA_CONNECTIONS_HIGH_USAGE["connections"]
