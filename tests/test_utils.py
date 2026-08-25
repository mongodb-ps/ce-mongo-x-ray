"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from importlib.resources import files

from mongo_x_ray.utils import load_classes

# Each test imports the exact helper it exercises so the function under test is
# explicit; the pattern is deliberate across this module.
# pylint: disable=import-outside-toplevel


def test_load_config():
    from mongo_x_ray.utils import load_config

    config_file = files("mongo_x_ray") / "config.json"
    config = load_config(config_file)
    assert "log" in config
    assert "healthcheck" in config


def test_truncate_content():
    from mongo_x_ray.utils import truncate_content

    content = "This is a test log message for truncation."
    truncated = truncate_content(content, max_words=5)
    assert truncated == "This is a test log ..."


def test_tooltip_html():
    from mongo_x_ray.utils import tooltip_html

    full = "This is the full content"
    truncated = "This is..."
    html = tooltip_html(full, truncated)
    assert 'data-tip="This is the full content"' in html
    assert ">This is...</span>" in html


def test_load_classes():
    classes = load_classes("mongo_x_ray.parsers")
    assert "BaseParser" in classes


def test_format_size():
    from mongo_x_ray.utils import format_size

    assert format_size(1023) == "1023.00 B"
    assert format_size(2048) == "2.00 KB"
    assert format_size(5 * 1024 * 1024) == "5.00 MB"
    assert format_size(3 * 1024 * 1024 * 1024) == "3.00 GB"
    assert format_size(7 * 1024 * 1024 * 1024 * 1024) == "7.00 TB"
    assert format_size(9 * 1024 * 1024 * 1024 * 1024 * 1024) == "9.00 PB"


def test_escape_markdown():
    from mongo_x_ray.utils import escape_markdown

    text = "This_is*some`markdown|text<with>special_chars"
    escaped = escape_markdown(text)
    assert escaped == "This\\_is\\*some\\`markdown\\|text&lt;with&gt;special\\_chars"


def test_escape_markdown_newlines():
    from mongo_x_ray.utils import escape_markdown

    assert escape_markdown("line1\nline2") == "line1<br>line2"
    assert escape_markdown("line1\r\nline2\rline3") == "line1<br>line2<br>line3"
    assert escape_markdown("single line") == "single line"
    # The <br> generated from newlines must not be re-escaped by the "<"/">" rules
    assert escape_markdown("a<b\nc>d") == "a&lt;b<br>c&gt;d"


def test_format_json_md():
    from mongo_x_ray.utils import format_json_md

    data = {"key": "value", "number": 123}
    md = format_json_md(data)
    assert md == '{<br>&nbsp;&nbsp;"key":&nbsp;"value",<br>&nbsp;&nbsp;"number":&nbsp;123<br>}'
    md = format_json_md(data, indent=0)
    assert md == '{"key": "value","number": 123}'


def test_to_ejson():
    from datetime import datetime
    from enum import Enum

    from mongo_x_ray.utils import to_ejson

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    data = {"color": Color.RED, "value": 42}
    json_str = to_ejson(data, indent=None)
    assert json_str == '{"color": "RED", "value": 42}'

    cls_maps = [{"class": datetime, "func": lambda o: o.isoformat()}]
    now = datetime.now()
    data = {"timestamp": now}
    json_str = to_ejson(data, indent=None, cls_maps=cls_maps)
    assert f'{{"timestamp": "{now.isoformat()}"}}' == json_str

    json_str = to_ejson({"a": 1, "b": 2})
    assert json_str == '{\n  "a": 1,\n  "b": 2\n}'

    json_str = to_ejson({"a": 1, "b": 2}, indent=4)
    assert json_str == '{\n    "a": 1,\n    "b": 2\n}'


def test_json_hash():
    from mongo_x_ray.utils import json_hash

    data = {"a": 1, "b": 2}
    hash1 = json_hash(data)
    assert hash1 == "EC55C9EC4B598E6F"
    hash2 = json_hash(data, digest_size=4)
    assert hash2 == "C5F6113B"


def test_inject_assets_injects_pie_label_settings():
    from mongo_x_ray.utils import inject_assets

    template = "<html><head>{{ style }}{{ pre_script }}{{ script }}</head><body></body></html>"
    output = inject_assets(template, "hc")
    assert "var PIE_LABEL_LENGTH = 40;" in output
    assert "var PIE_LABEL_PER_SIDE = 15;" in output
    assert "PIE_LABEL_LENGTH || 0" in output or "PIE_LABEL_LENGTH||0" in output
    assert "PIE_LABEL_PER_SIDE || 15" in output or "PIE_LABEL_PER_SIDE||15" in output
    assert "PIE_LABEL_THRESHOLD" not in output
