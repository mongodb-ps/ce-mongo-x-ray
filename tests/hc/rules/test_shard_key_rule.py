"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.shard_key_rule import ShardKeyRule

DATA_IMPROPER_SHARD_KEY = {
    "_id": "foo.bar3",
    "key": {"_id": 1},
    "unique": False,
}

DATA_NORMAL_SHARD_KEY = {
    "_id": "foo.bar4",
    "key": {"user_id": 1},
    "unique": False,
}


def test_shard_key_rule_improper_key():
    rule = ShardKeyRule()
    issues, parsed_data = rule.apply(DATA_IMPROPER_SHARD_KEY)
    assert len(issues) == 1
    issue = issues[0]
    assert issue["id"] == ISSUE.IMPROPER_SHARD_KEY
    assert issue["host"] == "cluster"
    assert parsed_data == DATA_IMPROPER_SHARD_KEY


def test_shard_key_rule_normal_key():
    rule = ShardKeyRule()
    issues, parsed_data = rule.apply(DATA_NORMAL_SHARD_KEY)
    assert len(issues) == 0
    assert parsed_data == DATA_NORMAL_SHARD_KEY
