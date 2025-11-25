from libs.healthcheck.issues import ISSUE
from libs.healthcheck.rules.shard_balance_rule import ShardBalanceRule

DATA_IMBALANCED_SHARDING = {
    "ns": "foo.bar1",
    "shards": {
        "shard0000": {
            "size": 1000000,
            "count": 1000,
            "storageSize": 2000000,
            "nindexes": 2,
            "totalIndexSize": 500000,
            "totalSize": 2500000,
        },
        "shard0001": {
            "size": 3000000,
            "count": 3000,
            "storageSize": 6000000,
            "nindexes": 2,
            "totalIndexSize": 1500000,
            "totalSize": 7500000,
        },
    },
}
DATA_IMBALANCED_SHARDING_2 = {
    "ns": "foo.bar1",
    "shards": {
        "shard0000": {
            "size": 1000000,
            "count": 1000,
            "storageSize": 2000000,
            "nindexes": 2,
            "totalIndexSize": 500000,
            "totalSize": 2500000,
        },
    },
}

DATA_BALANCED_SHARDING = {
    "ns": "foo.bar2",
    "shards": {
        "shard0000": {
            "size": 2000000,
            "count": 2100,
            "storageSize": 4000000,
            "nindexes": 2,
            "totalIndexSize": 1000000,
            "totalSize": 5000000,
        },
        "shard0001": {
            "size": 2100000,
            "count": 2000,
            "storageSize": 4000000,
            "nindexes": 2,
            "totalIndexSize": 1000000,
            "totalSize": 5000000,
        },
    },
}

config = {"sharding_imbalance_percentage": 0.1}
extra_info = {"shards": ["shard0000", "shard0001"]}


def test_shard_balance_rule_imbalanced():
    rule = ShardBalanceRule(config)
    issues, parsed_data = rule.apply(DATA_IMBALANCED_SHARDING, extra_info=extra_info)
    assert len(issues) == 1
    issue = issues[0]
    assert issue["id"] == ISSUE.IMBALANCED_SHARDING
    assert issue["host"] == "cluster"
    assert parsed_data == {
        "shard0000": {
            "size": 1000000,
            "count": 1000,
            "avgObjSize": 0,
            "storageSize": 2000000,
            "nindexes": 2,
            "totalIndexSize": 500000,
            "totalSize": 2500000,
        },
        "shard0001": {
            "size": 3000000,
            "count": 3000,
            "avgObjSize": 0,
            "storageSize": 6000000,
            "nindexes": 2,
            "totalIndexSize": 1500000,
            "totalSize": 7500000,
        },
    }


def test_shard_balance_rule_single_shard():
    rule = ShardBalanceRule(config)
    issues, parsed_data = rule.apply(DATA_IMBALANCED_SHARDING_2, extra_info=extra_info)
    assert len(issues) == 1
    issue = issues[0]
    assert issue["id"] == ISSUE.IMBALANCED_SHARDING
    assert issue["host"] == "cluster"
    assert parsed_data == {
        "shard0000": {
            "size": 1000000,
            "count": 1000,
            "avgObjSize": 0,
            "storageSize": 2000000,
            "nindexes": 2,
            "totalIndexSize": 500000,
            "totalSize": 2500000,
        },
    }


def test_shard_balance_rule_balanced():
    rule = ShardBalanceRule(config)
    issues, parsed_data = rule.apply(DATA_BALANCED_SHARDING, extra_info=extra_info)
    assert len(issues) == 0
    assert parsed_data == {
        "shard0000": {
            "size": 2000000,
            "count": 2100,
            "avgObjSize": 0,
            "storageSize": 4000000,
            "nindexes": 2,
            "totalIndexSize": 1000000,
            "totalSize": 5000000,
        },
        "shard0001": {
            "size": 2100000,
            "count": 2000,
            "avgObjSize": 0,
            "storageSize": 4000000,
            "nindexes": 2,
            "totalIndexSize": 1000000,
            "totalSize": 5000000,
        },
    }
