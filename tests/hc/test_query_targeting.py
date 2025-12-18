"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.query_targeting_rule import QueryTargetingRule

DATA_TARGETING_NORMAL = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50,
            "scannedObjects": 80,
        },
        "document": {"returned": 10},
    }
}

DATA_TARGETING_HIGH = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50000,
            "scannedObjects": 80000,
        },
        "document": {"returned": 10},
    }
}

DATA_TARGETING_EXCEPTION = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50000,
            "scannedObjects": 80000,
        },
        "document": {"returned": 0},
    }
}


config = {
    "query_targeting": 1000,
    "query_targeting_obj": 1000,
}


def test_query_targeting_normal():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_NORMAL, extra_info={"host": "localhost"})
    assert len(issues) == 0
    assert parsed_data["scanned/returned"] == 5.0
    assert parsed_data["scanned_obj/returned"] == 8.0


def test_query_targeting_high():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_HIGH, extra_info={"host": "localhost"})
    assert len(issues) == 2
    assert issues[0]["id"] == ISSUE.POOR_QUERY_TARGETING_KEYS
    assert issues[1]["id"] == ISSUE.POOR_QUERY_TARGETING_OBJECTS
    assert parsed_data["scanned/returned"] == 5000.0
    assert parsed_data["scanned_obj/returned"] == 8000.0


def test_query_targeting_exception():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_EXCEPTION, extra_info={"host": "localhost"})
    assert len(issues) == 2
    assert issues[0]["id"] == ISSUE.POOR_QUERY_TARGETING_KEYS
    assert issues[1]["id"] == ISSUE.POOR_QUERY_TARGETING_OBJECTS
    assert parsed_data["scanned/returned"] == 50000
    assert parsed_data["scanned_obj/returned"] == 80000
