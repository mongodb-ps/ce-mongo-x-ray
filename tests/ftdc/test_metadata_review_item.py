from datetime import datetime, timezone
from io import StringIO

import pytest
from pyftdc import FTDCError

from x_ray.ftdc_analysis.ftdc_items.metadata_review_item import (
    _METADATA_TABS,
    _resolve_path,
    MetadataReviewItem,
)
from x_ray.utils import load_classes


def test_resolve_path_extracts_nested_value():
    doc = {"a": {"b": {"c": 42}}}
    assert _resolve_path(doc, "a.b.c") == 42


def test_resolve_path_returns_none_for_missing_key():
    doc = {"a": 1}
    assert _resolve_path(doc, "a.b") is None


def test_resolve_path_returns_none_for_non_dict_intermediate():
    doc = {"a": 1}
    assert _resolve_path(doc, "a.b.c") is None


def test_resolve_path_handles_empty_dict():
    assert _resolve_path({}, "a") is None


def test_item_skips_analyze_after_first_successful_read(tmp_path, monkeypatch):
    item = MetadataReviewItem(str(tmp_path), {})
    first_meta = {"buildInfo": {"version": "8.0.0"}}
    second_meta = {"buildInfo": {"version": "9.0.0"}}
    call_count = 0

    class Reader:
        def __init__(self, source):
            nonlocal call_count
            call_count += 1

        def get_metadata(self):
            return first_meta if call_count == 1 else second_meta

    monkeypatch.setattr(
        "x_ray.ftdc_analysis.ftdc_items.metadata_review_item.FTDCReader",
        Reader,
    )
    item.analyze(tmp_path / "metrics.2026-01-01T00-00-00Z")
    item.analyze(tmp_path / "metrics.2026-01-01T00-01-00Z")

    assert call_count == 1
    assert item._raw_metadata == first_meta


def test_item_handles_missing_metadata_gracefully(tmp_path, monkeypatch):
    item = MetadataReviewItem(str(tmp_path), {})

    class Reader:
        def __init__(self, source):
            pass

        def get_metadata(self):
            raise FTDCError("no metadata")

    monkeypatch.setattr(
        "x_ray.ftdc_analysis.ftdc_items.metadata_review_item.FTDCReader",
        Reader,
    )
    item.analyze(tmp_path / "metrics.test")

    assert item._raw_metadata is None


def test_review_results_renders_tabbed_html(tmp_path):
    item = MetadataReviewItem(str(tmp_path), {})
    item._raw_metadata = {
        "getCmdLineOpts": {
            "parsed": {"net": {"port": 27017}},
            "argv": ["mongod", "--port", "27017"],
        },
        "buildInfo": {"version": "8.0.0"},
        "hostInfo": {"system": {"hostname": "test-host"}},
        "ulimits": {"nofile": {"soft": 64000}},
        "sysMaxOpenFiles": 65536,
    }
    output = StringIO()

    item.review_results_markdown(output, section_number=2)

    report = output.getvalue()
    assert "## 2 Metadata Review" in report
    assert 'id="metadata-tabs"' in report
    for tab_key, label, _dotted in _METADATA_TABS:
        assert f'data-tab="metadata-tabs-{tab_key}"' in report
        assert f">{label}<" in report
        assert f'id="metadata-tabs-{tab_key}"' in report
    assert '"port"' in report and "27017" in report
    assert '"mongod"' in report
    assert '"version"' in report and '"8.0.0"' in report
    assert '"hostname"' in report and '"test-host"' in report
    assert '"nofile"' in report
    assert "65536" in report
    assert "metadata-tab-btn active" in report
    assert "metadata-tab-pane active" in report
    assert '<pre><code class="language-json">' in report


def test_review_results_shows_not_available_for_missing_metadata_keys(tmp_path):
    item = MetadataReviewItem(str(tmp_path), {})
    item._raw_metadata = {}
    output = StringIO()

    item.review_results_markdown(output, section_number=1)
    report = output.getvalue()

    assert report.count("_Not available._") == len(_METADATA_TABS)


def test_review_results_handles_no_raw_metadata(tmp_path):
    item = MetadataReviewItem(str(tmp_path), {})
    item._raw_metadata = None
    output = StringIO()

    item.review_results_markdown(output, section_number=1)
    report = output.getvalue()

    assert "_No metadata available._" in report
    assert "metadata-tabs" not in report


def test_item_name_returns_class_name():
    item = MetadataReviewItem("/tmp", {})
    assert item.name == "MetadataReviewItem"


def test_class_is_discovered_by_load_classes():
    classes = load_classes("x_ray.ftdc_analysis.ftdc_items")
    assert "MetadataReviewItem" in classes
    assert classes["MetadataReviewItem"] is MetadataReviewItem
