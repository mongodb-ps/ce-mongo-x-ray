from datetime import datetime
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.index_rule import IndexRule

DATA_INDEX_PROBLEM = [
    {
        "name": "x_1_y_1",
        "key": {"x": 1, "y": 1},
        "host": "localhost:30021",
        "accesses": {"ops": 0, "since": datetime.strptime("2025-09-23T22:48:14.300Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        "shard": "shard02",
        "spec": {"v": 2, "key": {"x": 1, "y": 1}, "name": "x_1_y_1"},
    },
    {
        "name": "y_1",
        "key": {"y": 1},
        "host": "localhost:30021",
        "accesses": {"ops": 0, "since": datetime.strptime("2025-09-23T22:48:14.300Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        "shard": "shard02",
        "spec": {"v": 2, "key": {"y": 1}, "name": "y_1"},
    },
    {
        "name": "y_1_x_1",
        "key": {"y": 1, "x": 1},
        "host": "localhost:30021",
        "accesses": {"ops": 0, "since": datetime.strptime("2025-09-23T22:48:14.300Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        "shard": "shard02",
        "spec": {"v": 2, "key": {"y": 1, "x": 1}, "name": "y_1_x_1", "sparse": True},
    },
    {
        "name": "x_1",
        "key": {"x": 1},
        "host": "localhost:30021",
        "accesses": {"ops": 0, "since": datetime.strptime("2025-09-23T22:48:14.300Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        "shard": "shard02",
        "spec": {"v": 2, "key": {"x": 1}, "name": "x_1"},
    },
    {
        "name": "_id_",
        "key": {"_id": 1},
        "host": "localhost:30021",
        "accesses": {"ops": 0, "since": datetime.strptime("2025-09-23T22:48:14.300Z", "%Y-%m-%dT%H:%M:%S.%fZ")},
        "shard": "shard02",
        "spec": {"v": 2, "key": {"_id": 1}, "name": "_id_"},
    },
]


def test_index_rule():
    rule = IndexRule(
        thresholds={
            "num_indexes": 3,
            "unused_index_days": 30,
        }
    )
    issues, _ = rule.apply(
        data=DATA_INDEX_PROBLEM,
        extra_info={"host": "localhost:30021", "ns": "test.collection"},
        check_items=["num_indexes", "unused_indexes", "redundant_indexes"],
    )
    assert len(issues) == 7
    issue_ids = {issue["id"] for issue in issues}
    assert ISSUE.TOO_MANY_INDEXES in issue_ids
    assert ISSUE.UNUSED_INDEX in issue_ids
    assert ISSUE.REDUNDANT_INDEX in issue_ids
