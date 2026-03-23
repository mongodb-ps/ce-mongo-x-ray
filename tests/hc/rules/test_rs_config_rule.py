"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.rs_config_rule import RSConfigRule
from x_ray.healthcheck.shared import SEVERITY

CONFIG_INSUFFICIENT_VOTING_MEMBERS = {
    "config": {
        "_id": "shard01",
        "version": 2,
        "term": 558,
        "members": [
            {
                "_id": 0,
                "host": "localhost:30018",
                "arbiterOnly": False,
                "buildIndexes": True,
                "hidden": False,
                "priority": 1,
                "tags": {},
                "secondaryDelaySecs": 0,
                "votes": 1,
            }
        ],
    }
}

CONFIG_EVEN_VOTING_MEMBERS = {
    "config": {
        "_id": "shard01",
        "version": 2,
        "term": 558,
        "members": [
            {
                "_id": 0,
                "host": "localhost:30018",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 1,
                "host": "localhost:30019",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 2,
                "host": "localhost:30020",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 3,
                "host": "localhost:30021",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
        ],
    }
}

CONFIG_DELAYED_MEMBER = {
    "config": {
        "_id": "shard01",
        "version": 2,
        "term": 558,
        "members": [
            {
                "_id": 0,
                "host": "localhost:30018",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 1,
                "host": "localhost:30019",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 3600,
                "votes": 1,
            },
            {
                "_id": 2,
                "host": "localhost:30020",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
        ],
    }
}

CONFIG_ARBITER_MEMBER = {
    "config": {
        "_id": "shard01",
        "version": 2,
        "term": 558,
        "members": [
            {
                "_id": 0,
                "host": "localhost:30018",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 1,
                "host": "localhost:30019",
                "arbiterOnly": True,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
            {
                "_id": 2,
                "host": "localhost:30020",
                "arbiterOnly": False,
                "hidden": False,
                "priority": 1,
                "secondaryDelaySecs": 0,
                "votes": 1,
            },
        ],
    }
}


def test_insufficient_voting_members():
    rule = RSConfigRule({})

    result, _ = rule.apply(CONFIG_INSUFFICIENT_VOTING_MEMBERS, extra_info={"host": "cluster"})
    assert result is not None
    assert result[0]["id"] == ISSUE.INSUFFICIENT_VOTING_MEMBERS
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.INSUFFICIENT_VOTING_MEMBERS]["title"]
    assert result[0]["host"] == "cluster"
    assert _ == CONFIG_INSUFFICIENT_VOTING_MEMBERS


def test_even_voting_members():
    rule = RSConfigRule({})

    result, _ = rule.apply(CONFIG_EVEN_VOTING_MEMBERS, extra_info={"host": "cluster"})
    assert result is not None
    assert result[0]["id"] == ISSUE.EVEN_VOTING_MEMBERS
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.EVEN_VOTING_MEMBERS]["title"]
    assert result[0]["host"] == "cluster"
    assert _ == CONFIG_EVEN_VOTING_MEMBERS


def test_delayed_member():
    rule = RSConfigRule({})

    result, _ = rule.apply(CONFIG_DELAYED_MEMBER, extra_info={"host": "cluster"})
    assert result is not None
    assert len(result) == 4
    assert result[0]["id"] == ISSUE.DELAYED_VOTING_MEMBER
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.DELAYED_VOTING_MEMBER]["title"]
    assert result[0]["host"] == "localhost:30019"
    assert _ == CONFIG_DELAYED_MEMBER

    assert result[1]["id"] == ISSUE.DELAYED_ELECTABLE_MEMBER
    assert result[1]["severity"] == SEVERITY.HIGH
    assert result[1]["title"] == ISSUE_MSG_MAP[ISSUE.DELAYED_ELECTABLE_MEMBER]["title"]
    assert result[1]["host"] == "localhost:30019"
    assert _ == CONFIG_DELAYED_MEMBER

    assert result[2]["id"] == ISSUE.DELAYED_NON_HIDDEN_MEMBER
    assert result[2]["severity"] == SEVERITY.HIGH
    assert result[2]["title"] == ISSUE_MSG_MAP[ISSUE.DELAYED_NON_HIDDEN_MEMBER]["title"]
    assert result[2]["host"] == "localhost:30019"
    assert _ == CONFIG_DELAYED_MEMBER

    assert result[3]["id"] == ISSUE.DELAYED_SECONDARY_MEMBER
    assert result[3]["severity"] == SEVERITY.LOW
    assert result[3]["title"] == ISSUE_MSG_MAP[ISSUE.DELAYED_SECONDARY_MEMBER]["title"]
    assert result[3]["host"] == "localhost:30019"
    assert _ == CONFIG_DELAYED_MEMBER
