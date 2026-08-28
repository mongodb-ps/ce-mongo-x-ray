"""
Copyright (c) 2026 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.

Core shared utilities used by more than one analysis module. These helpers
are generic (severity levels, JSON serialisation, markdown id slugs) and live
in the core ``mongo_x_ray`` package so that the analysis modules (healthcheck, gmd,
log, ftdc) do not have to import from each other.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional

from mongo_x_ray.utils import to_ejson


class SEVERITY(Enum):
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


def to_json(obj, indent: Optional[int] = 0):
    cls_maps = [
        {"class": SEVERITY, "func": lambda o: o.name},
        {"class": datetime, "func": lambda o: o.isoformat()},
    ]
    return to_ejson(obj, indent=indent, cls_maps=cls_maps)


def str_to_md_id(string: str) -> str:
    md_id = string.lower()
    md_id = md_id.replace(" ", "-")
    md_id = re.sub(r"[^a-z0-9\-_]", "", md_id)
    md_id = re.sub(r"\-+", "-", md_id)
    md_id = md_id.strip("-")
    return md_id
