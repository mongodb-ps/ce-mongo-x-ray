from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from libs.healthcheck.rules.data_size_rule import DataSizeRule
from libs.healthcheck.shared import SEVERITY

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
