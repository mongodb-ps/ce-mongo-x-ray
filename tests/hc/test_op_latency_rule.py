from x_ray.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from x_ray.healthcheck.rules.op_latency_rule import OpLatencyRule
from x_ray.healthcheck.shared import SEVERITY

DATA_WITH_HIGH_LATENCY = {
    "latencyStats": {
        "reads": {"latency": 250, "ops": 2},
        "writes": {"latency": 300, "ops": 1},
        "commands": {"latency": 100, "ops": 2},
        "transactions": {"latency": 400, "ops": 2},
    }
}
DATA_WITH_NORMAL_LATENCY = {
    "latencyStats": {
        "reads": {"latency": 50, "ops": 2},
        "writes": {"latency": 80, "ops": 1},
        "commands": {"latency": 40, "ops": 2},
        "transactions": {"latency": 60, "ops": 2},
    }
}
config = {"op_latency_ms": 100}


def test_op_latency_rule():
    rule = OpLatencyRule(config)
    results, latency_data = rule.apply(DATA_WITH_HIGH_LATENCY)
    assert len(results) == 3

    read_issue = results[0]
    assert read_issue["id"] == ISSUE.HIGH_READ_LATENCY
    assert read_issue["severity"] == SEVERITY.MEDIUM
    assert read_issue["title"] == ISSUE_MSG_MAP[ISSUE.HIGH_READ_LATENCY]["title"]

    write_issue = results[1]
    assert write_issue["id"] == ISSUE.HIGH_WRITE_LATENCY
    assert write_issue["severity"] == SEVERITY.MEDIUM
    assert write_issue["title"] == ISSUE_MSG_MAP[ISSUE.HIGH_WRITE_LATENCY]["title"]

    transaction_issue = results[2]
    assert transaction_issue["id"] == ISSUE.HIGH_TRANSACTION_LATENCY
    assert transaction_issue["severity"] == SEVERITY.MEDIUM
    assert transaction_issue["title"] == ISSUE_MSG_MAP[ISSUE.HIGH_TRANSACTION_LATENCY]["title"]

    assert latency_data["latencyStats"]["reads_latency"] == 125.0
    assert latency_data["latencyStats"]["writes_latency"] == 300.0
    assert latency_data["latencyStats"]["commands_latency"] == 50.0
    assert latency_data["latencyStats"]["transactions_latency"] == 200.0


def test_op_latency_rule_no_issues():
    rule = OpLatencyRule(config)
    results, latency_data = rule.apply(DATA_WITH_NORMAL_LATENCY)
    assert len(results) == 0

    assert latency_data["latencyStats"]["reads_latency"] == 25.0
    assert latency_data["latencyStats"]["writes_latency"] == 80.0
    assert latency_data["latencyStats"]["commands_latency"] == 20.0
    assert latency_data["latencyStats"]["transactions_latency"] == 30.0
