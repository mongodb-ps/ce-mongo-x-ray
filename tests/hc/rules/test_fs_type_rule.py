"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.fs_type_rule import FSTypeRule
from x_ray.healthcheck.shared import SEVERITY


def _data(db_path, mounts):
    return {
        "hostInfo": {"extra": {"mountInfo": mounts}},
        "serverCmdLineOpts": {"parsed": {"storage": {"dbPath": db_path}}},
    }


def test_fs_type_rule_xfs_no_issue():
    rule = FSTypeRule()
    data = _data(
        "/data/db",
        [
            {"mountPoint": "/", "type": "ext4", "options": "rw,relatime"},
            {"mountPoint": "/data", "type": "xfs", "options": "rw,noatime"},
        ],
    )

    issues, parsed_data = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 0
    assert parsed_data == data


def test_fs_type_rule_ext4_without_noatime():
    rule = FSTypeRule()
    data = _data(
        "/data/db",
        [
            {"mountPoint": "/data", "type": "ext4", "options": "rw,relatime"},
        ],
    )

    issues, _ = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 2
    assert issues[0]["id"] == ISSUE.FS_TYPE_EXT4
    assert issues[0]["host"] == "localhost:27017"
    assert issues[0]["severity"] == SEVERITY.MEDIUM
    assert issues[1]["id"] == ISSUE.FS_TYPE_EXT4_NOATIME
    assert issues[1]["host"] == "localhost:27017"
    assert issues[1]["severity"] == SEVERITY.MEDIUM


def test_fs_type_rule_ext4_with_noatime():
    rule = FSTypeRule()
    data = _data(
        "/data/db",
        [
            {"mountPoint": "/data", "type": "ext4", "options": "rw,noatime"},
        ],
    )

    issues, _ = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 1
    assert issues[0]["id"] == ISSUE.FS_TYPE_EXT4


def test_fs_type_rule_unsupported_type():
    rule = FSTypeRule()
    data = _data(
        "/data/db",
        [
            {"mountPoint": "/data", "type": "zfs", "options": "rw,noatime"},
        ],
    )

    issues, _ = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 1
    assert issues[0]["id"] == ISSUE.FS_TYPE
    assert issues[0]["severity"] == SEVERITY.HIGH


def test_fs_type_rule_supports_nested_extra():
    rule = FSTypeRule()
    data = {
        "hostInfo": {
            "extra": {
                "extra": {
                    "mountInfo": [
                        {"mountPoint": "/data", "type": "xfs", "options": "rw,noatime"},
                    ]
                }
            }
        },
        "serverCmdLineOpts": {"parsed": {"storage": {"dbPath": "/data/db"}}},
    }

    issues, _ = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 0


def test_fs_type_rule_no_db_path_no_issue():
    rule = FSTypeRule()
    data = {
        "hostInfo": {
            "extra": {
                "mountInfo": [
                    {"mountPoint": "/", "type": "ext4", "options": "rw,relatime"},
                ]
            }
        },
        "serverCmdLineOpts": {"parsed": {}},
    }

    issues, parsed_data = rule.apply(data, extra_info={"host": "localhost:27017"})

    assert len(issues) == 0
    assert parsed_data == data
