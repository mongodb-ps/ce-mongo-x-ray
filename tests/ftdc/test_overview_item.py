from datetime import datetime, timedelta, timezone

import pytest

from x_ray.ftdc_analysis.ftdc_items.overview_item import OverviewItem


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
