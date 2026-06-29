from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest
from pyftdc import DataPoint

from x_ray.ftdc_analysis.ftdc_items.overview_item import OverviewItem


def test_default_sample_rate_is_ten_percent(tmp_path):
    item = OverviewItem(str(tmp_path), {})

    assert item._sample_rate == 0.1


def test_analyze_uses_batched_pyftdc_api(tmp_path, monkeypatch):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    calls = []

    class Reader:
        def __init__(self, source):
            assert source == tmp_path / "metrics.test"

        def list_metrics(self):
            return [
                OverviewItem._CPU_USER,
                OverviewItem._CPU_SYSTEM,
                OverviewItem._CPU_CORES,
                "systemMetrics.disks.sda.reads",
                "unrelated.metric",
            ]

        def get_metric(self, names, start, end, sample_rate=1.0):
            calls.append((names, start, end, sample_rate))
            return {name: [DataPoint(timestamp=timestamp, value=10)] for name in names}

    monkeypatch.setattr(
        "x_ray.ftdc_analysis.ftdc_items.overview_item.FTDCReader",
        Reader,
    )
    item = OverviewItem(str(tmp_path), {"sample_rate": 0.5})

    item.analyze(tmp_path / "metrics.test")

    requested = calls[0][0]
    assert requested == {
        item._CPU_USER,
        item._CPU_SYSTEM,
        item._CPU_CORES,
        "systemMetrics.disks.sda.reads",
    }
    assert calls[0][3] == 0.5
    assert calls[0][1] is None
    assert calls[0][2] is None
    assert "unrelated.metric" not in item._series
    assert item._capture_start == timestamp
    assert item._capture_end == timestamp


def test_overview_calculates_cpu_and_iops(tmp_path):
    item = OverviewItem(str(tmp_path), {"max_sample_gap_seconds": 5})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    middle = start + timedelta(seconds=1)
    end = middle + timedelta(seconds=1)
    item._series = {
        item._CPU_CORES: {start: 2, middle: 2, end: 2},
        item._CPU_USER: {start: 1000, middle: 1200, end: 1600},
        item._CPU_SYSTEM: {start: 500, middle: 600, end: 800},
        "systemMetrics.disks.sda.reads": {start: 100, middle: 110, end: 130},
        "systemMetrics.disks.sda.writes": {start: 50, middle: 55, end: 65},
    }
    item._disk_metrics = {
        "systemMetrics.disks.sda.reads",
        "systemMetrics.disks.sda.writes",
    }

    item.finalize_analysis()

    assert item._results[0] == {
        "metric": "CPU user",
        "peak": 20.0,
        "average": 15.0,
        "unit": "%",
    }
    assert item._results[1]["peak"] == pytest.approx(10.0)
    assert item._results[1]["average"] == pytest.approx(7.5)
    assert item._results[2] == {
        "metric": "IOPS",
        "peak": 30.0,
        "average": 22.5,
        "unit": "ops/s",
    }


def test_overview_ignores_counter_resets_and_large_gaps(tmp_path):
    item = OverviewItem(str(tmp_path), {"max_sample_gap_seconds": 2})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    late = start + timedelta(seconds=10)
    item._series = {
        item._CPU_CORES: {start: 2, late: 2},
        item._CPU_USER: {start: 100, late: 50},
    }

    item.finalize_analysis()

    assert item._results[0]["peak"] == 0
    assert item._results[0]["average"] == 0


def test_overview_displays_capture_timespan(tmp_path):
    item = OverviewItem(str(tmp_path), {})
    item._capture_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item._capture_end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    output = StringIO()

    item.review_results_markdown(output)

    expected = "Capture timespan: `2026-01-01T00:00:00+00:00` " "to `2026-01-02T00:00:00+00:00`"
    assert expected in output.getvalue()
