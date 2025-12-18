"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES. 
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION. 
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""
from datetime import datetime
from x_ray.version import Version
from x_ray.log_analysis.shared import to_json


def test_to_json():
    dt = datetime(2024, 6, 1, 12, 30, 45)
    v = Version.parse("1.2.3")
    obj = {"timestamp": dt, "message": "Test log", "version": v}
    json_str = to_json(obj)
    assert json_str == '{"timestamp": "2024-06-01T12:30:45", "message": "Test log", "version": "1.2.3"}'
    json_str_indented = to_json(obj, indent=2)
    expected_indented = """{
  "timestamp": "2024-06-01T12:30:45",
  "message": "Test log",
  "version": "1.2.3"
}"""
    assert json_str_indented == expected_indented
