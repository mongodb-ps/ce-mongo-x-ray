from libs.healthcheck.issues import ISSUE
from libs.healthcheck.rules.query_targeting_rule import QueryTargetingRule

DATA_TARGETING_NORMAL = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50,
            "scannedObjects": 80,
        },
        "document": {"returned": 10},
    }
}

DATA_TARGETING_HIGH = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50000,
            "scannedObjects": 80000,
        },
        "document": {"returned": 10},
    }
}

DATA_TARGETING_EXCEPTION = {
    "metrics": {
        "queryExecutor": {
            "scanned": 50000,
            "scannedObjects": 80000,
        },
        "document": {"returned": 0},
    }
}


config = {
    "query_targeting": 1000,
    "query_targeting_obj": 1000,
}


def test_query_targeting_normal():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_NORMAL, extra_info={"host": "localhost"})
    assert len(issues) == 0
    assert parsed_data["scanned/returned"] == 5.0
    assert parsed_data["scanned_obj/returned"] == 8.0


def test_query_targeting_high():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_HIGH, extra_info={"host": "localhost"})
    assert len(issues) == 2
    assert issues[0]["id"] == ISSUE.POOR_QUERY_TARGETING_KEYS
    assert issues[1]["id"] == ISSUE.POOR_QUERY_TARGETING_OBJECTS
    assert parsed_data["scanned/returned"] == 5000.0
    assert parsed_data["scanned_obj/returned"] == 8000.0


def test_query_targeting_exception():
    rule = QueryTargetingRule(config)
    issues, parsed_data = rule.apply(DATA_TARGETING_EXCEPTION, extra_info={"host": "localhost"})
    assert len(issues) == 2
    assert issues[0]["id"] == ISSUE.POOR_QUERY_TARGETING_KEYS
    assert issues[1]["id"] == ISSUE.POOR_QUERY_TARGETING_OBJECTS
    assert parsed_data["scanned/returned"] == 50000
    assert parsed_data["scanned_obj/returned"] == 80000
