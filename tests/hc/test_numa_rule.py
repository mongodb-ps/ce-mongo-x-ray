from libs.healthcheck.issues import ISSUE
from libs.healthcheck.rules.numa_rule import NumaRule
from libs.healthcheck.shared import SEVERITY
from libs.version import Version

DATA_DISABLED = {"system": {"numaEnabled": False}}

DATA_ENABLED = {"system": {"numaEnabled": True}}

VERSION_7_0 = Version.parse("6.0.2")
VERSION_8_0 = Version.parse("8.0.15")


def test_numa_rule_disabled_on_7_0():
    rule = NumaRule({})
    issues, _ = rule.apply(DATA_DISABLED, extra_info={"host": "localhost", "version": VERSION_7_0})
    assert len(issues) == 0


def test_numa_rule_enabled_on_7_0():
    rule = NumaRule({})
    issues, _ = rule.apply(DATA_ENABLED, extra_info={"host": "localhost", "version": VERSION_7_0})
    assert len(issues) == 1
    assert issues[0]["id"] == ISSUE.NUMA_ENABLED
    assert issues[0]["severity"] == SEVERITY.HIGH


def test_numa_rule_enabled_on_8_0():
    rule = NumaRule({})
    issues, _ = rule.apply(DATA_ENABLED, extra_info={"host": "localhost", "version": VERSION_8_0})
    assert len(issues) == 0


def test_numa_rule_disabled_on_8_0():
    rule = NumaRule({})
    issues, _ = rule.apply(DATA_DISABLED, extra_info={"host": "localhost", "version": VERSION_8_0})
    assert len(issues) == 1
    assert issues[0]["id"] == ISSUE.NUMA_DISABLED
    assert issues[0]["severity"] == SEVERITY.LOW
