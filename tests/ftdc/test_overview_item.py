from datetime import datetime, timedelta, timezone
from io import StringIO
from xml.etree import ElementTree

import pytest
from pyftdc import DataPoint

from x_ray.ftdc_analysis.ftdc_items.overview_item import OverviewItem
from x_ray.ftdc_analysis.shared import (
    CPU_METRICS,
    DERIVED_METRIC_NAMES,
    DISK_METRICS,
    MEMORY_METRICS,
    MOUNT_METRICS,
    OPCOUNTER_METRICS,
    OP_LATENCY_METRICS,
    TCMALLOC_METRICS,
    WIREDTIGER_CACHE_METRICS,
)


def test_default_sample_rate_uses_total_ingest_files(tmp_path):
    item = OverviewItem(str(tmp_path), {}, total_ingest_files=4)

    assert item._sample_rate == 0.25


def test_configured_sample_rate_overrides_ingest_file_default(tmp_path):
    item = OverviewItem(str(tmp_path), {"sample_rate": 0.5}, total_ingest_files=4)

    assert item._sample_rate == 0.5


def test_default_sample_rate_handles_no_ingest_files(tmp_path):
    item = OverviewItem(str(tmp_path), {}, total_ingest_files=0)

    assert item._sample_rate == 1.0


def test_bar_chart_uses_threshold_colors(tmp_path):
    item = OverviewItem(str(tmp_path), {})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 9.0),
        (start + timedelta(seconds=1), 10.0),
        (start + timedelta(seconds=2), 15.0),
        (start + timedelta(seconds=3), 20.0),
        (start + timedelta(seconds=4), 21.0),
    ]

    chart = tmp_path / item._write_chart("Threshold test", points, thresholds=(10, 20))
    bars = ElementTree.parse(chart).getroot().findall(".//{http://www.w3.org/2000/svg}rect")

    assert [bar.attrib["class"] for bar in bars] == [
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-red",
    ]


def test_bar_chart_keeps_current_color_without_thresholds(tmp_path):
    item = OverviewItem(str(tmp_path), {})
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    chart = tmp_path / item._write_chart("Default color test", [(timestamp, 10.0)])
    bar = ElementTree.parse(chart).getroot().find(".//{http://www.w3.org/2000/svg}rect")

    assert bar is not None
    assert bar.attrib["class"] == "metric-bar"


def test_overview_passes_metric_specific_thresholds_to_charts(tmp_path, monkeypatch):
    item = OverviewItem(str(tmp_path), {})
    item._disk_queue_metrics = {"disk.queue": "sda"}
    item._mount_metrics = {
        "/data": {
            "free": "mount.free",
            "capacity": "mount.capacity",
        }
    }
    chart_thresholds = {}

    def write_chart(metric, points, *, slug=None, thresholds=None):
        chart_thresholds[metric] = thresholds
        return f"charts/{slug or metric}.svg"

    monkeypatch.setattr(item, "_write_chart", write_chart)

    item.finalize_analysis()

    assert chart_thresholds[DERIVED_METRIC_NAMES["system_memory_utilization"]] == (85, 95)
    assert chart_thresholds[DERIVED_METRIC_NAMES["memory_fragmentation_ratio"]] == (15, 25)
    assert chart_thresholds[CPU_METRICS["user"].name] == (85, 95)
    assert chart_thresholds[CPU_METRICS["iowait"].name] == (10, 20)
    assert chart_thresholds[CPU_METRICS["system"].name] == (20, 30)
    assert chart_thresholds[DERIVED_METRIC_NAMES["cache_fill"]] == (80, 95)
    assert chart_thresholds[DERIVED_METRIC_NAMES["cache_dirty"]] == (15, 20)
    assert chart_thresholds[f'{DISK_METRICS["io_in_progress"].name} (sda)'] == (1, 2)
    assert chart_thresholds[f'{DERIVED_METRIC_NAMES["disk_utilization"]} (/data)'] == (80, 90)
    assert chart_thresholds[f'{MOUNT_METRICS["free"].name} (/data)'] is None
    assert chart_thresholds[OPCOUNTER_METRICS["query"].name] is None


@pytest.mark.parametrize(
    "thresholds",
    [
        [10],
        [10, 20, 30],
        [20, 10],
        [10, 10],
        [10, float("inf")],
        ["low", "high"],
        True,
    ],
)
def test_bar_chart_rejects_invalid_thresholds(tmp_path, thresholds):
    item = OverviewItem(str(tmp_path), {})

    with pytest.raises(ValueError, match="chart thresholds"):
        item._write_chart("Invalid thresholds", [], thresholds=thresholds)


def test_analyze_uses_batched_pyftdc_api_and_discovers_devices(tmp_path, monkeypatch):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    calls = []

    class Reader:
        def __init__(self, source):
            assert source == tmp_path / "metrics.test"

        def list_metrics(self):
            return [
                CPU_METRICS["user"].key,
                CPU_METRICS["system"].key,
                CPU_METRICS["available_cores"].key,
                "systemMetrics.disks.sda.io_in_progress",
                "systemMetrics.mounts./data/db.free",
                "systemMetrics.mounts./data/db.capacity",
                "systemMetrics.mounts./proc/acpi.free",
                "unrelated.metric",
            ]

        def get_mongodb_config(self):
            return {"net": {"port": 27017}}

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
        CPU_METRICS["user"].key,
        CPU_METRICS["system"].key,
        CPU_METRICS["available_cores"].key,
        "systemMetrics.disks.sda.io_in_progress",
        "systemMetrics.mounts./data/db.free",
        "systemMetrics.mounts./data/db.capacity",
    }
    assert calls[0][3] == 0.5
    assert calls[0][1] is None
    assert calls[0][2] is None
    assert "unrelated.metric" not in item._series
    assert item._disk_queue_metrics == {"systemMetrics.disks.sda.io_in_progress": "sda"}
    assert item._mount_metrics == {
        "/data/db": {
            "free": "systemMetrics.mounts./data/db.free",
            "capacity": "systemMetrics.mounts./data/db.capacity",
        }
    }
    assert item._capture_start == timestamp
    assert item._capture_end == timestamp
    assert item._mongodb_config == {"net": {"port": 27017}}


def test_mount_detection_excludes_virtual_and_container_bind_mounts():
    assert OverviewItem._is_data_volume_mount("/")
    assert OverviewItem._is_data_volume_mount("/data/db")
    assert OverviewItem._is_data_volume_mount("/var/lib/mongodb")
    assert not OverviewItem._is_data_volume_mount("/dev/shm")
    assert not OverviewItem._is_data_volume_mount("/proc/acpi")
    assert not OverviewItem._is_data_volume_mount("/sys/firmware")
    assert not OverviewItem._is_data_volume_mount("/etc/hosts")


def test_overview_calculates_requested_sections(tmp_path):
    item = OverviewItem(str(tmp_path), {"max_sample_gap_seconds": 5})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    middle = start + timedelta(seconds=1)
    end = middle + timedelta(seconds=1)
    gib = 1024**3
    item._series = {
        OPCOUNTER_METRICS["query"].key: {start: 100, middle: 110, end: 130},
        OP_LATENCY_METRICS["reads"]["ops"].key: {start: 100, middle: 110, end: 130},
        OP_LATENCY_METRICS["reads"]["latency"].key: {start: 100_000, middle: 130_000, end: 210_000},
        OP_LATENCY_METRICS["writes"]["ops"].key: {start: 50, middle: 55, end: 65},
        OP_LATENCY_METRICS["writes"]["latency"].key: {start: 40_000, middle: 50_000, end: 80_000},
        CPU_METRICS["available_cores"].key: {start: 2, middle: 2, end: 2},
        CPU_METRICS["user"].key: {start: 1000, middle: 1200, end: 1600},
        CPU_METRICS["system"].key: {start: 500, middle: 600, end: 800},
        CPU_METRICS["iowait"].key: {start: 100, middle: 140, end: 200},
        MEMORY_METRICS["total"].key: {start: 1000, middle: 1000, end: 1000},
        MEMORY_METRICS["available"].key: {start: 400, middle: 350, end: 300},
        TCMALLOC_METRICS["heap_size"].key: {start: 100, middle: 100, end: 100},
        TCMALLOC_METRICS["current_allocated_bytes"].key: {start: 70, middle: 65, end: 60},
        WIREDTIGER_CACHE_METRICS["bytes_maximum"].key: {start: 100, middle: 100, end: 100},
        WIREDTIGER_CACHE_METRICS["bytes_current"].key: {start: 70, middle: 75, end: 80},
        WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"].key: {start: 10, middle: 15, end: 20},
        "systemMetrics.disks.sda.io_in_progress": {start: 2, middle: 3, end: 4},
        "systemMetrics.disks.sdb.io_in_progress": {start: 1, middle: 2, end: 3},
        "systemMetrics.mounts./.free": {start: 2 * gib, middle: 1.5 * gib, end: gib},
        "systemMetrics.mounts./.capacity": {start: 4 * gib, middle: 4 * gib, end: 4 * gib},
        "systemMetrics.mounts./data/db.free": {start: 4 * gib, middle: 3 * gib, end: 2 * gib},
        "systemMetrics.mounts./data/db.capacity": {start: 8 * gib, middle: 8 * gib, end: 8 * gib},
    }
    item._disk_queue_metrics = {
        "systemMetrics.disks.sda.io_in_progress": "sda",
        "systemMetrics.disks.sdb.io_in_progress": "sdb",
    }
    item._mount_metrics = {
        "/": {
            "free": "systemMetrics.mounts./.free",
            "capacity": "systemMetrics.mounts./.capacity",
        },
        "/data/db": {
            "free": "systemMetrics.mounts./data/db.free",
            "capacity": "systemMetrics.mounts./data/db.capacity",
        },
    }

    item.finalize_analysis()

    assert list(item._results) == [
        "Workload",
        "Ops and Latencies",
        "Performance",
    ]
    workload = item._results["Workload"]
    assert [result["metric"] for result in workload] == [metric.name for metric in OPCOUNTER_METRICS.values()]
    assert workload[0]["peak"] == 20
    assert workload[0]["average"] == 15

    reads, read_latency, writes, write_latency = item._results["Ops and Latencies"]
    assert (reads["peak"], reads["average"]) == (20, 15)
    assert (read_latency["peak"], read_latency["average"]) == (4, 3.5)
    assert (writes["peak"], writes["average"]) == (10, 7.5)
    assert (write_latency["peak"], write_latency["average"]) == (3, 2.5)

    performance = {result["metric"]: result for result in item._results["Performance"]}
    assert performance[DERIVED_METRIC_NAMES["system_memory_utilization"]]["peak"] == 70
    assert performance[DERIVED_METRIC_NAMES["memory_fragmentation_ratio"]]["average"] == 35
    assert performance[CPU_METRICS["user"].name]["peak"] == 20
    assert performance[CPU_METRICS["system"].name]["average"] == pytest.approx(7.5)
    assert performance[CPU_METRICS["iowait"].name]["peak"] == 3
    assert performance[DERIVED_METRIC_NAMES["cache_fill"]]["average"] == 75
    assert performance[DERIVED_METRIC_NAMES["cache_dirty"]]["peak"] == 20
    assert performance[f'{DISK_METRICS["io_in_progress"].name} (sda)']["average"] == 3
    assert performance[f'{DISK_METRICS["io_in_progress"].name} (sdb)']["average"] == 2
    assert performance[f'{MOUNT_METRICS["free"].name} (/)']["average"] == 1.5
    assert performance[f'{DERIVED_METRIC_NAMES["disk_utilization"]} (/)']["average"] == 62.5
    assert performance[f'{DERIVED_METRIC_NAMES["disk_utilization"]} (/data/db)']["peak"] == 75
    assert (
        performance[f'{MOUNT_METRICS["free"].name} (/data/db)']["chart"] == "charts/ftdc-overview-disk-free-data-db.svg"
    )

    chart_paths = [tmp_path / result["chart"] for results in item._results.values() for result in results]
    assert all(chart.is_file() for chart in chart_paths)
    for chart in chart_paths:
        assert ElementTree.parse(chart).getroot().tag == "{http://www.w3.org/2000/svg}svg"


def test_overview_ignores_counter_resets_and_large_gaps(tmp_path):
    item = OverviewItem(str(tmp_path), {"max_sample_gap_seconds": 2})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    late = start + timedelta(seconds=10)
    item._series = {
        CPU_METRICS["available_cores"].key: {start: 2, late: 2},
        CPU_METRICS["user"].key: {start: 100, late: 50},
        OPCOUNTER_METRICS["query"].key: {start: 100, late: 50},
    }

    item.finalize_analysis()

    assert item._results["Workload"][0]["peak"] == 0
    assert item._results["Performance"][2]["peak"] == 0


def test_overview_displays_capture_metadata_config_and_sections(tmp_path):
    item = OverviewItem(
        str(tmp_path),
        {"max_sample_gap_seconds": 15, "sample_rate": 0.25},
        total_ingest_files=4,
    )
    item._capture_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item._capture_end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    item._mongodb_config = {
        "net": {"bindIp": "*"},
        "security": {"authorization": "enabled"},
    }
    item.finalize_analysis()
    output = StringIO()

    item.review_results_markdown(output, section_number=1)

    report = output.getvalue()
    assert "Capture timespan: `2026-01-01T00:00:00+00:00` to `2026-01-02T00:00:00+00:00`" in report
    assert "Sample rate: `0.25`" in report
    assert 'MongoDB configuration:\n\n```json\n{\n  "net": {\n    "bindIp": "*"\n  },' in report
    assert '"security": {\n    "authorization": "enabled"\n  }\n}\n```' in report
    assert "## 1 FTDC Overview" in report
    assert "### 1.1 Workload" in report
    assert "### 1.2 Ops and Latencies" in report
    assert "### 1.3 Performance" in report
    assert "#### Overview" not in report
