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
