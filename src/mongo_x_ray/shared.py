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


# LeafyGreen "Sparkle" icon (mongodb/leafygreen-ui, packages/icon/src/glyphs),
# the design system's marker for AI-generated content. Reports inline it in front
# of every AI note.
AI_ICON = (
    '<svg class="ai-icon" viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">'
    '<path d="M6.27334 2.89343L5.27501 5.88842C5.1749 6.18877 4.93922 6.42445 4.63887 6.52456L1.64388 7.52289'
    "C1.18537 7.67573 1.18537 8.32427 1.64388 8.47711L4.63887 9.47544C4.93922 9.57555 5.1749 9.81123 5.27501 10.1116"
    "L6.27334 13.1066C6.42618 13.5651 7.07472 13.5651 7.22756 13.1066L8.22589 10.1116C8.326 9.81123 8.56168 9.57555 "
    "8.86203 9.47544L11.857 8.47711C12.3155 8.32427 12.3155 7.67573 11.857 7.52289L8.86203 6.52456"
    'C8.56168 6.42445 8.326 6.18877 8.22589 5.88842L7.22756 2.89343C7.07472 2.43492 6.42618 2.43492 6.27334 2.89343Z"/>'
    '<path d="M12.5469 1.17194L12.3158 1.8651C12.2157 2.16545 11.98 2.40113 11.6797 2.50125L10.9865 2.7323'
    "C10.7573 2.80872 10.7573 3.13299 10.9865 3.20941L11.6797 3.44046C11.98 3.54058 12.2157 3.77626 12.3158 4.0766"
    "L12.5469 4.76977C12.6233 4.99902 12.9476 4.99902 13.024 4.76977L13.255 4.0766C13.3552 3.77626 13.5908 3.54058 "
    "13.8912 3.44046L14.5843 3.20941C14.8136 3.13299 14.8136 2.80872 14.5843 2.7323L13.8912 2.50125"
    'C13.5908 2.40113 13.3552 2.16545 13.255 1.8651L13.024 1.17194C12.9476 0.942687 12.6233 0.942687 12.5469 1.17194Z"/>'
    '<path d="M12.5469 11.2302L12.3158 11.9234C12.2157 12.2237 11.98 12.4594 11.6797 12.5595L10.9865 12.7906'
    "C10.7573 12.867 10.7573 13.1913 10.9865 13.2677L11.6797 13.4988C11.98 13.5989 12.2157 13.8346 12.3158 14.1349"
    "L12.5469 14.8281C12.6233 15.0573 12.9476 15.0573 13.024 14.8281L13.255 14.1349C13.3552 13.8346 13.5908 13.5989 "
    "13.8912 13.4988L14.5843 13.2677C14.8136 13.1913 14.8136 12.867 14.5843 12.7906L13.8912 12.5595"
    'C13.5908 12.4594 13.3552 12.2237 13.255 11.9234L13.024 11.2302C12.9476 11.001 12.6233 11.001 12.5469 11.2302Z"/>'
    "</svg>"
)


def severity_badge(severity: SEVERITY) -> str:
    """Render a severity as an inline Badge (MongoDB design system).

    High is red, medium yellow, low green and info light gray; the look lives in
    `.severity-badge` in the report stylesheets so a template can restyle it.
    """
    return f'<span class="severity-badge severity-{severity.name.lower()}">{severity.name}</span>'


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
