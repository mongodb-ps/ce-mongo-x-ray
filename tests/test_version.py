"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from x_ray.version import Version


def test_version_comparison():
    v1 = Version.parse("1.2.3")
    v2 = Version([1, 2, 4])
    v3 = Version.parse("1.3.0")
    v4 = Version.parse("2.0.0")
    v5 = Version.parse("1.2.3")

    assert v1 < v2
    assert v3 < v4
    assert v1 == v5
    assert v4 > v1
    assert v3 >= v2
    assert v2 <= v4
    assert v1 < "1.2.4"
    assert v3 > [1, 2, 9]
