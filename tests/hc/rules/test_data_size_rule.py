"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.data_size_rule import DataSizeRule
from x_ray.healthcheck.shared import SEVERITY

DATA_WITH_LARGE_SIZE = {
    "ns": "test.large_collection",
    "storageStats": {
        "size": 3 * 1024**3,  # 3 GB
        "avgObjSize": 32 * 1024,  # 32 KB
        "indexDetails": {},
        "wiredTiger": {},
    },
}

DATA_WITH_NORMAL_SIZE = {
    "ns": "test.large_collection",
    "storageStats": {
        "size": 1 * 1024**3,  # 1 GB
        "avgObjSize": 8 * 1024,  # 8 KB
        "indexDetails": {},
        "wiredTiger": {},
    },
}

config = {"collection_size_gb": 2, "obj_size_kb": 16}

# Sharded collection: aggregate size exceeds threshold, but no single shard does
SHARDED_DATA_NORMAL = {
    "ns": "test.sharded_collection",
    "sharded": True,
    "shards": {
        "shard01": {
            "size": 1 * 1024**3,  # 1 GB
            "avgObjSize": 8 * 1024,  # 8 KB
        },
        "shard02": {
            "size": 1.5 * 1024**3,  # 1.5 GB
            "avgObjSize": 8 * 1024,  # 8 KB
        },
    },
    "storageStats": {
        "size": 2.5 * 1024**3,  # 2.5 GB aggregate (would exceed if checked as whole)
    },
}

# Sharded collection: one shard exceeds threshold
SHARDED_DATA_LARGE = {
    "ns": "test.sharded_collection",
    "sharded": True,
    "shards": {
        "shard01": {
            "size": 1 * 1024**3,  # 1 GB
            "avgObjSize": 8 * 1024,  # 8 KB
        },
        "shard02": {
            "size": 3 * 1024**3,  # 3 GB
            "avgObjSize": 32 * 1024,  # 32 KB
        },
    },
    "storageStats": {
        "size": 4 * 1024**3,  # 4 GB aggregate
    },
}


def test_data_size_rule_large():
    rule = DataSizeRule(config)
    results, parsed_data = rule.apply(DATA_WITH_LARGE_SIZE)

    assert len(results) == 2

    issue1 = results[0]
    assert issue1["id"] == ISSUE.COLLECTION_TOO_LARGE
    assert issue1["severity"] == SEVERITY.LOW
    assert issue1["title"] == ISSUE_MSG_MAP[ISSUE.COLLECTION_TOO_LARGE]["title"]

    issue2 = results[1]
    assert issue2["id"] == ISSUE.AVG_OBJECT_SIZE_TOO_LARGE
    assert issue2["severity"] == SEVERITY.LOW
    assert issue2["title"] == ISSUE_MSG_MAP[ISSUE.AVG_OBJECT_SIZE_TOO_LARGE]["title"]


def test_data_size_rule_normal():
    rule = DataSizeRule(config)
    results, parsed_data = rule.apply(DATA_WITH_NORMAL_SIZE)

    assert len(results) == 0


def test_data_size_rule_sharded_normal():
    """Aggregate size exceeds threshold, but no single shard does — no issues expected."""
    rule = DataSizeRule(config)
    results, parsed_data = rule.apply(SHARDED_DATA_NORMAL)

    assert len(results) == 0


def test_data_size_rule_sharded_large():
    """One shard exceeds threshold — issues expected only for that shard."""
    rule = DataSizeRule(config)
    results, parsed_data = rule.apply(SHARDED_DATA_LARGE)

    assert len(results) == 2
    assert all(r["host"] == "shard02" for r in results)

    issue1 = results[0]
    assert issue1["id"] == ISSUE.COLLECTION_TOO_LARGE_SHARDED
    assert issue1["host"] == "shard02"
    assert "shard02" in issue1["description"]

    issue2 = results[1]
    assert issue2["id"] == ISSUE.AVG_OBJECT_SIZE_TOO_LARGE
    assert issue2["host"] == "shard02"
