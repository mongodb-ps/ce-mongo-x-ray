"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.rs_status_rule import RSStatusRule
from x_ray.healthcheck.shared import SEVERITY
from bson import Timestamp

RS_STATUS_NO_PRIMARY = {
    "set": "shard01",
    "members": [
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 2, "optime": {"ts": Timestamp(1763932730, 1)}}
    ],
}

RS_UNHEALTHY_MEMBER = {
    "set": "shard01",
    "members": [
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 1, "optime": {"ts": Timestamp(1763932730, 1)}},
        {"_id": 1, "name": "localhost:30018", "health": 1, "state": 6, "optime": {"ts": Timestamp(1763932730, 1)}},
    ],
}

RS_INITIALIZING_MEMBER = {
    "set": "shard01",
    "members": [
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 1, "optime": {"ts": Timestamp(1763932730, 1)}},
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 5, "optime": {"ts": Timestamp(1763932730, 1)}},
    ],
}

RS_STATUS_LAGGED_MEMBER = {
    "set": "shard01",
    "members": [
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 1, "optime": {"ts": Timestamp(1763932730, 1)}},
        {"_id": 1, "name": "localhost:30019", "health": 1, "state": 2, "optime": {"ts": Timestamp(1763931106, 1)}},
        {"_id": 2, "name": "localhost:30020", "health": 1, "state": 2, "optime": {"ts": Timestamp(1763931106, 1)}},
    ],
}

RS_STATUS_NORMAL = {
    "set": "shard01",
    "members": [
        {"_id": 0, "name": "localhost:30018", "health": 1, "state": 1, "optime": {"ts": Timestamp(1763931106, 1)}},
        {"_id": 1, "name": "localhost:30019", "health": 1, "state": 2, "optime": {"ts": Timestamp(1763931106, 1)}},
        {"_id": 2, "name": "localhost:30020", "health": 1, "state": 2, "optime": {"ts": Timestamp(1763931106, 1)}},
    ],
}
config = {"replication_lag_seconds": 60, "oplog_window_hours": 48}


def test_no_primary():
    rule = RSStatusRule(config)

    # Test with no primary
    result, _ = rule.apply(RS_STATUS_NO_PRIMARY, extra_info={"host": "cluster"})
    assert result is not None
    assert result[0]["id"] == ISSUE.NO_PRIMARY
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.NO_PRIMARY]["title"]
    assert result[0]["host"] == "cluster"
    assert _ == RS_STATUS_NO_PRIMARY


def test_unhealthy_member():
    rule = RSStatusRule(config)

    # Test with unhealthy member
    result, _ = rule.apply(RS_UNHEALTHY_MEMBER, extra_info={"host": "cluster"})
    assert result is not None
    assert result[0]["id"] == ISSUE.UNHEALTHY_MEMBER
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.UNHEALTHY_MEMBER]["title"]
    assert result[0]["host"] == "localhost:30018"
    assert _ == RS_UNHEALTHY_MEMBER


def test_initializing_member():
    rule = RSStatusRule(config)

    # Test with initializing member
    result, _ = rule.apply(RS_INITIALIZING_MEMBER, extra_info={"host": "cluster"})
    assert result is not None
    assert result[0]["id"] == ISSUE.INITIALIZING_MEMBER
    assert result[0]["severity"] == SEVERITY.LOW
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.INITIALIZING_MEMBER]["title"]
    assert result[0]["host"] == "localhost:30018"
    assert _ == RS_INITIALIZING_MEMBER


def test_lagged_member():
    rule = RSStatusRule(config)

    # Test with lagged member
    result, _ = rule.apply(RS_STATUS_LAGGED_MEMBER, extra_info={"host": "cluster"})
    assert result is not None
    assert len(result) == 2
    assert result[0]["id"] == ISSUE.DELAYED_MEMBER
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.DELAYED_MEMBER]["title"]
    assert result[0]["host"] == "localhost:30019"


def test_normal_status():
    rule = RSStatusRule(config)

    # Test with normal status
    result, _ = rule.apply(RS_STATUS_NORMAL, extra_info={"host": "cluster"})
    assert result is not None
    assert len(result) == 0
