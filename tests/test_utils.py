"""
Copyright (c) 2026 MongoDB Inc.

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


def test_inject_assets_applies_the_theme_stylesheet():
    from mongo_x_ray.utils import inject_assets

    template = "<html><head>{{ style }}{{ pre_script }}{{ script }}</head><body></body></html>"
    output = inject_assets(template, "healthcheck", theme="mongodb")

    # templates/css/mongodb.css is appended after the shared styles so it can
    # restyle them.
    assert "--lg-green-base" in output
    assert output.index("--bgColor-muted") < output.index("--lg-green-base")


def test_inject_assets_without_theme_keeps_the_default_look():
    from mongo_x_ray.utils import inject_assets

    template = "<html><head>{{ style }}{{ pre_script }}{{ script }}</head><body></body></html>"
    output = inject_assets(template, "healthcheck")

    assert "--lg-green-base" not in output


def test_inject_assets_ignores_an_unknown_theme():
    from mongo_x_ray.utils import inject_assets

    template = "<html><head>{{ style }}{{ pre_script }}{{ script }}</head><body></body></html>"
    output = inject_assets(template, "healthcheck", theme="no-such-theme")

    assert "--lg-green-base" not in output
    assert "<style>" in output


def test_print_styles_hide_the_outline_without_reserving_its_column():
    from pathlib import Path

    from mongo_x_ray.utils import get_script_path

    templates = Path(get_script_path("templates"))
    for name in ("shared.raw.css", "mongodb.raw.css"):
        css = (templates / "css" / name).read_text(encoding="utf-8")
        print_block = css[css.index("@media print") :]
        assert "#outline," in print_block, name
        # Hidden and out of the layout: no renderer may keep its 280px column.
        assert "display: none !important" in print_block, name
        assert "width: 0 !important" in print_block, name
        # The content must start at the page edge, not after the sidebar.
        assert "margin: 0 !important" in print_block, name


def test_shared_js_removes_the_outline_while_printing():
    from pathlib import Path

    from mongo_x_ray.utils import get_script_path

    js = (Path(get_script_path("templates")) / "js" / "post_common.raw.js").read_text(encoding="utf-8")

    assert 'addEventListener("beforeprint"' in js
    assert 'addEventListener("afterprint"' in js


def test_mongodb_theme_uses_the_leafygreen_tokens():
    from pathlib import Path

    from mongo_x_ray.utils import get_script_path

    css = (Path(get_script_path("templates")) / "css" / "mongodb.raw.css").read_text(encoding="utf-8")

    # Values taken from mongodb/leafygreen-ui (palette, side-nav, table, tabs).
    assert "--lg-green-dark2: #00684a;" in css
    assert "--lg-green-green" not in css
    assert "--lg-side-nav-width: 220px;" in css
    assert "outline-h3" in css
    assert ".chart-tabs" in css
    assert ".metadata-tab-btn" in css
    # MongoDB black page with a light content card, like mongodb.design
    assert "background: var(--lg-black)" in css
    assert ".outline-header" in css


def test_shared_js_bundles_the_outline_toggle_and_no_section_tabs():
    from pathlib import Path

    from mongo_x_ray.utils import get_script_path, inject_assets

    js_dir = Path(get_script_path("templates")) / "js"
    outline = (js_dir / "post_outline.raw.js").read_text(encoding="utf-8")
    # The layout belongs to the stylesheets, not to inline margins.
    assert 'classList.add("outline-collapsed")' in outline
    assert "document.body.style.margin" not in outline

    # No generic section tabs: the modules keep their own tab widgets (log chart
    # tabs, ftdc metadata tabs) and the theme styles those.
    assert not (js_dir / "post_tabs.raw.js").exists()
    template = "<html><head>{{ style }}{{ pre_script }}</head><body>{{ script }}</body></html>"
    assert "report-tabs" not in inject_assets(template, "healthcheck", theme="mongodb")


def test_table_copy_button_carries_the_table_icon():
    from pathlib import Path

    from mongo_x_ray.utils import get_script_path

    templates = Path(get_script_path("templates"))
    js = (templates / "js" / "post_table_copy.raw.js").read_text(encoding="utf-8")
    # LeafyGreen "Table" glyph before the label, kept while the label changes.
    assert "TABLE_COPY_ICON" in js
    assert "M1 3.25C1 2.55964" in js
    assert "table-copy-label" in js
    assert 'setTableCopyLabel(button, "Copy Table")' in js

    css = (templates / "css" / "shared.raw.css").read_text(encoding="utf-8")
    assert ".table-copy-button svg {" in css
    assert "width: 14px;" in css


def test_env_file_is_loaded_without_overriding_the_environment(monkeypatch, tmp_path):
    import os

    from mongo_x_ray.env import load_env_file

    (tmp_path / ".env").write_text("XRAY_TEST_FROM_FILE=from-file\nXRAY_TEST_FROM_SHELL=from-file\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XRAY_TEST_FROM_SHELL", "from-shell")
    monkeypatch.delenv("XRAY_TEST_FROM_FILE", raising=False)

    loaded = load_env_file()

    assert loaded == tmp_path / ".env"
    assert os.environ["XRAY_TEST_FROM_FILE"] == "from-file"
    # Values already in the environment win (VS Code `envFile`, CI, `export`).
    assert os.environ["XRAY_TEST_FROM_SHELL"] == "from-shell"


def test_env_file_search_walks_up_from_the_working_directory(monkeypatch, tmp_path):
    import os

    from mongo_x_ray.env import load_env_file

    (tmp_path / ".env").write_text("XRAY_TEST_WALK_UP=1\n", encoding="utf-8")
    nested = tmp_path / "reports" / "2026-11-21"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("XRAY_TEST_WALK_UP", raising=False)

    assert load_env_file() == tmp_path / ".env"
    assert os.environ["XRAY_TEST_WALK_UP"] == "1"


def test_importing_the_package_loads_the_env_file(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    import mongo_x_ray

    (tmp_path / ".env").write_text("XRAY_TEST_IMPORT=loaded\n", encoding="utf-8")
    package_parent = str(Path(mongo_x_ray.__file__).resolve().parent.parent)

    result = subprocess.run(
        [sys.executable, "-c", "import mongo_x_ray, os; print(os.environ.get('XRAY_TEST_IMPORT'))"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": package_parent},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "loaded"


def test_ai_client_loads_the_env_before_it_snapshots_the_model():
    from pathlib import Path

    import mongo_x_ray.ai_client as ai_client

    # A run outside VS Code has no `envFile`: the module must load `.env` itself,
    # before `_AI_MODEL` is read (it is a module-level snapshot).
    source = Path(ai_client.__file__).read_text(encoding="utf-8")
    assert "load_env_file()" in source
    assert source.index("load_env_file()") < source.index("_AI_MODEL = os.getenv")
    assert ai_client.GPT_MODEL == ai_client._AI_MODEL
