from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.oplog_window_rule import OplogWindowRule
from x_ray.healthcheck.shared import SEVERITY

DATA_WITH_SMALL_OPLOG_WINDOW = {
    "serverStatus": {
        "oplogTruncation": {"oplogMinRetentionHours": 36},
    },
    "firstOplogEntry": 1716449733,
    "lastOplogEntry": 1716536133,  # 24 hours later
}

DATA_WITH_SMALL_OPLOG_WINDOW_2 = {
    "serverStatus": {
        "oplogTruncation": {"oplogMinRetentionHours": 12},
    },
    "firstOplogEntry": 1716449733,
    "lastOplogEntry": 1716536133,  # 24 hours later
}

DATA_WITH_SMALL_OPLOG_WINDOW_3 = {
    "serverStatus": {
        "oplogTruncation": {"oplogMinRetentionHours": 12},
    },
    "timeDelta": 86400,  # 24 hours in seconds
}

DATA_NORMAL_OPLOG_WINDOW = {
    "serverStatus": {
        "oplogTruncation": {"oplogMinRetentionHours": 72},
    },
    "firstOplogEntry": 1716449733,
    "lastOplogEntry": 1716536133,  # 24 hours later
}

DATA_NORMAL_OPLOG_WINDOW_2 = {
    "serverStatus": {
        "oplogTruncation": {"oplogMinRetentionHours": 24},
    },
    "firstOplogEntry": 1716449733,
    "lastOplogEntry": 1716708933,  # 72 hours later
}

config = {"oplog_window_hours": 48}


def test_oplog_window_rule_small_window():
    rule = OplogWindowRule(config)
    results, parsed_data = rule.apply(DATA_WITH_SMALL_OPLOG_WINDOW)

    assert len(results) == 1
    issue = results[0]
    assert issue["id"] == ISSUE.OPLOG_WINDOW_TOO_SMALL
    assert issue["severity"] == SEVERITY.HIGH
    assert issue["title"] == ISSUE_MSG_MAP[ISSUE.OPLOG_WINDOW_TOO_SMALL]["title"]
    assert parsed_data["configured_retention_hours"] == 36
    assert parsed_data["current_retention_hours"] == 24
    assert parsed_data["effective_retention_hours"] == 36

    results, parsed_data = rule.apply(DATA_WITH_SMALL_OPLOG_WINDOW_2)
    assert len(results) == 1
    issue = results[0]
    assert issue["id"] == ISSUE.OPLOG_WINDOW_TOO_SMALL
    assert issue["severity"] == SEVERITY.HIGH
    assert issue["title"] == ISSUE_MSG_MAP[ISSUE.OPLOG_WINDOW_TOO_SMALL]["title"]
    assert parsed_data["configured_retention_hours"] == 12
    assert parsed_data["current_retention_hours"] == 24
    assert parsed_data["effective_retention_hours"] == 24

    results, parsed_data = rule.apply(DATA_WITH_SMALL_OPLOG_WINDOW_3)
    assert len(results) == 1
    issue = results[0]
    assert issue["id"] == ISSUE.OPLOG_WINDOW_TOO_SMALL
    assert issue["severity"] == SEVERITY.HIGH
    assert issue["title"] == ISSUE_MSG_MAP[ISSUE.OPLOG_WINDOW_TOO_SMALL]["title"]
    assert parsed_data["configured_retention_hours"] == 12
    assert parsed_data["current_retention_hours"] == 24
    assert parsed_data["effective_retention_hours"] == 24


def test_oplog_window_rule_normal_window():
    rule = OplogWindowRule(config)
    results, parsed_data = rule.apply(DATA_NORMAL_OPLOG_WINDOW)
    assert len(results) == 0
    assert parsed_data["configured_retention_hours"] == 72
    assert parsed_data["current_retention_hours"] == 24
    assert parsed_data["effective_retention_hours"] == 72

    results, parsed_data = rule.apply(DATA_NORMAL_OPLOG_WINDOW_2)
    assert len(results) == 0
    assert parsed_data["configured_retention_hours"] == 24
    assert parsed_data["current_retention_hours"] == 72
    assert parsed_data["effective_retention_hours"] == 72
