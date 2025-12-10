from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.shard_mongos_rule import ShardMongosRule
from x_ray.healthcheck.shared import SEVERITY
from datetime import datetime, timezone
from x_ray.version import Version

MONGOS_IRRESPONSIVE = [
    {
        "host": "M-QTFH0WFXLG:30017",
        "pingLatencySec": 0.975336,
        "lastPing": datetime(2025, 11, 23, 22, 28, 19, 79000, tzinfo=timezone.utc),
        "version": Version([5, 0, 19, 0]),
    },
    {
        "host": "M-QTFH0WFXLG:30028",
        "client": None,
        "pingLatencySec": 8846940,
        "lastPing": datetime(2025, 8, 13, 12, 59, 19, 978000, tzinfo=timezone.utc),
    },
]

MONGOS_NO_ACTIVE = [
    {
        "host": "M-QTFH0WFXLG:30028",
        "client": None,
        "pingLatencySec": 8846940,
        "lastPing": datetime(2025, 8, 13, 12, 59, 19, 978000, tzinfo=timezone.utc),
    }
]


def test_irresponsive_mongos():
    rule = ShardMongosRule()
    results, _ = rule.apply(MONGOS_IRRESPONSIVE)
    assert len(results) == 2
    assert results[0]["id"] == ISSUE.IRRESPONSIVE_MONGOS
    assert results[0]["severity"] == SEVERITY.LOW
    assert results[0]["title"] == ISSUE_MSG_MAP[ISSUE.IRRESPONSIVE_MONGOS]["title"]
    assert results[0]["host"] == "M-QTFH0WFXLG:30028"
    assert results[1]["id"] == ISSUE.SINGLE_MONGOS
    assert results[1]["severity"] == SEVERITY.HIGH
    assert results[1]["title"] == ISSUE_MSG_MAP[ISSUE.SINGLE_MONGOS]["title"]
    assert results[1]["host"] == "cluster"
    assert _ == MONGOS_IRRESPONSIVE


def test_no_active_mongos():
    rule = ShardMongosRule()
    results, _ = rule.apply(MONGOS_NO_ACTIVE)
    assert len(results) == 2

    assert results[0]["id"] == ISSUE.IRRESPONSIVE_MONGOS
    assert results[0]["severity"] == SEVERITY.LOW
    assert results[0]["title"] == ISSUE_MSG_MAP[ISSUE.IRRESPONSIVE_MONGOS]["title"]
    assert results[0]["host"] == "M-QTFH0WFXLG:30028"

    assert results[1]["id"] == ISSUE.NO_ACTIVE_MONGOS
    assert results[1]["severity"] == SEVERITY.HIGH
    assert results[1]["title"] == ISSUE_MSG_MAP[ISSUE.NO_ACTIVE_MONGOS]["title"]
    assert results[1]["host"] == "cluster"
    assert _ == MONGOS_NO_ACTIVE
