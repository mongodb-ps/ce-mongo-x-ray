"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.numa_rule import NumaRule
from x_ray.healthcheck.shared import SEVERITY
from x_ray.version import Version

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
