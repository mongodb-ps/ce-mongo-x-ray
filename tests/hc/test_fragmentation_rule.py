from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from libs.healthcheck.rules.fragmentation_rule import FragmentationRule
from libs.healthcheck.shared import SEVERITY

DATA_WITH_HIGH_FRAGMENTATION = {
    "ns": "test.fragmented_collection",
    "storageStats": {
        "storageSize": 10 * 1024**3,  # 10 GB
        "wiredTiger": {
            "block-manager": {
                "file bytes available for reuse": 6 * 1024**3,  # 6 GB
            }
        },
        "indexDetails": {
            "index_1": {
                "block-manager": {
                    "file bytes available for reuse": 3 * 1024**3,  # 3 GB
                    "file size in bytes": 5 * 1024**3,  # 5 GB
                }
            },
            "index_2": {
                "block-manager": {
                    "file bytes available for reuse": 0.5 * 1024**3,  # 500 MB
                    "file size in bytes": 2 * 1024**3,  # 2 GB
                }
            },
        },
    },
}

DATA_WITH_NORMAL_FRAGMENTATION = {
    "ns": "test.normal_collection",
    "storageStats": {
        "storageSize": 10 * 1024**3,  # 10 GB
        "wiredTiger": {
            "block-manager": {
                "file bytes available for reuse": 2 * 1024**3,  # 2 GB
            }
        },
        "indexDetails": {
            "index_1": {
                "block-manager": {
                    "file bytes available for reuse": 1 * 1024**3,  # 1 GB
                    "file size in bytes": 5 * 1024**3,  # 5 GB
                }
            }
        },
    },
}

config = {
    "fragmentation_ratio": 0.5,  # 50%
}


def test_high_fragmentation():
    rule = FragmentationRule(thresholds=config)
    results, frag_data = rule.apply(DATA_WITH_HIGH_FRAGMENTATION)
    assert len(results) == 2  # 1 collection + 1 indexes
    collection_issue = results[0]
    assert collection_issue["id"] == ISSUE.HIGH_COLLECTION_FRAGMENTATION
    assert collection_issue["severity"] == SEVERITY.MEDIUM
    assert collection_issue["title"] == ISSUE_MSG_MAP[ISSUE.HIGH_COLLECTION_FRAGMENTATION]["title"]

    index_issue_1 = results[1]
    assert index_issue_1["id"] == ISSUE.HIGH_INDEX_FRAGMENTATION
    assert index_issue_1["severity"] == SEVERITY.MEDIUM
    assert index_issue_1["title"] == ISSUE_MSG_MAP[ISSUE.HIGH_INDEX_FRAGMENTATION]["title"]
    assert frag_data["collFragmentation"]["collectionFragmentation"] == 0.6
    assert frag_data["indexFragmentations"][0]["fragmentation"] == 0.6
    assert frag_data["indexFragmentations"][1]["fragmentation"] == 0.25


def test_normal_fragmentation():
    rule = FragmentationRule(thresholds=config)
    results, frag_data = rule.apply(DATA_WITH_NORMAL_FRAGMENTATION)
    assert len(results) == 0  # No issues
    assert frag_data["collFragmentation"]["collectionFragmentation"] == 0.2
    assert frag_data["indexFragmentations"][0]["fragmentation"] == 0.2
