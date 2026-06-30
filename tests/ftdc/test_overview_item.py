from datetime import datetime, timedelta, timezone
from io import StringIO
from xml.etree import ElementTree

import pytest
from pyftdc import DataPoint

from x_ray.ftdc_analysis.ftdc_items.overview_item import OverviewItem
from x_ray.ftdc_analysis.shared import (
    CPU_METRICS,
    MEMORY_METRICS,
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


def test_analyze_uses_batched_pyftdc_api_and_discovers_devices(tmp_path, monkeypatch):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    calls = []

    class Reader:
        def __init__(self, source):
            assert source == tmp_path / "metrics.test"

        def list_metrics(self):
            return [
                CPU_METRICS["user"],
                CPU_METRICS["system"],
                CPU_METRICS["available_cores"],
                "systemMetrics.disks.sda.io_in_progress",
                "systemMetrics.mounts./data/db.free",
                "systemMetrics.mounts./proc/acpi.free",
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
        CPU_METRICS["user"],
        CPU_METRICS["system"],
        CPU_METRICS["available_cores"],
        "systemMetrics.disks.sda.io_in_progress",
        "systemMetrics.mounts./data/db.free",
    }
    assert calls[0][3] == 0.5
    assert calls[0][1] is None
    assert calls[0][2] is None
    assert "unrelated.metric" not in item._series
    assert item._disk_queue_metrics == {"systemMetrics.disks.sda.io_in_progress"}
    assert item._mount_free_metrics == {"systemMetrics.mounts./data/db.free": "/data/db"}
    assert item._capture_start == timestamp
    assert item._capture_end == timestamp


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
        OPCOUNTER_METRICS["query"]: {start: 100, middle: 110, end: 130},
        OP_LATENCY_METRICS["reads"]["ops"]: {start: 100, middle: 110, end: 130},
        OP_LATENCY_METRICS["reads"]["latency"]: {start: 100_000, middle: 130_000, end: 210_000},
        OP_LATENCY_METRICS["writes"]["ops"]: {start: 50, middle: 55, end: 65},
        OP_LATENCY_METRICS["writes"]["latency"]: {start: 40_000, middle: 50_000, end: 80_000},
        CPU_METRICS["available_cores"]: {start: 2, middle: 2, end: 2},
        CPU_METRICS["user"]: {start: 1000, middle: 1200, end: 1600},
        CPU_METRICS["system"]: {start: 500, middle: 600, end: 800},
        CPU_METRICS["iowait"]: {start: 100, middle: 140, end: 200},
        MEMORY_METRICS["total"]: {start: 1000, middle: 1000, end: 1000},
        MEMORY_METRICS["available"]: {start: 400, middle: 350, end: 300},
        TCMALLOC_METRICS["heap_size"]: {start: 100, middle: 100, end: 100},
        TCMALLOC_METRICS["current_allocated_bytes"]: {start: 70, middle: 65, end: 60},
        WIREDTIGER_CACHE_METRICS["bytes_maximum"]: {start: 100, middle: 100, end: 100},
        WIREDTIGER_CACHE_METRICS["bytes_current"]: {start: 70, middle: 75, end: 80},
        WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"]: {start: 10, middle: 15, end: 20},
        "systemMetrics.disks.sda.io_in_progress": {start: 2, middle: 3, end: 4},
        "systemMetrics.disks.sdb.io_in_progress": {start: 1, middle: 2, end: 3},
        "systemMetrics.mounts./.free": {start: 2 * gib, middle: 1.5 * gib, end: gib},
        "systemMetrics.mounts./data/db.free": {start: 4 * gib, middle: 3 * gib, end: 2 * gib},
    }
    item._disk_queue_metrics = {
        "systemMetrics.disks.sda.io_in_progress",
        "systemMetrics.disks.sdb.io_in_progress",
    }
    item._mount_free_metrics = {
        "systemMetrics.mounts./.free": "/",
        "systemMetrics.mounts./data/db.free": "/data/db",
    }

    item.finalize_analysis()

    assert list(item._results) == [
        "Workload",
        "Read/Write Operations and Latencies",
        "Performance",
    ]
    workload = item._results["Workload"]
    assert [result["metric"] for result in workload] == [
        "Query",
        "Insert",
        "Update",
        "Delete",
        "Command",
        "Getmore",
    ]
    assert workload[0]["peak"] == 20
    assert workload[0]["average"] == 15

    reads, read_latency, writes, write_latency = item._results["Read/Write Operations and Latencies"]
    assert (reads["peak"], reads["average"]) == (20, 15)
    assert (read_latency["peak"], read_latency["average"]) == (4, 3.5)
    assert (writes["peak"], writes["average"]) == (10, 7.5)
    assert (write_latency["peak"], write_latency["average"]) == (3, 2.5)

    performance = {result["metric"]: result for result in item._results["Performance"]}
    assert performance["System memory utilization"]["peak"] == 70
    assert performance["Memory fragmentation ratio"]["average"] == 35
    assert performance["CPU user"]["peak"] == 20
    assert performance["CPU system"]["average"] == pytest.approx(7.5)
    assert performance["I/O wait"]["peak"] == 3
    assert performance["Cache fill"]["average"] == 75
    assert performance["Cache dirty"]["peak"] == 20
    assert performance["Disk queue length"]["average"] == 5
    assert performance["Disk free (/)"]["average"] == 1.5
    assert performance["Disk free (/data/db)"]["chart"] == "charts/ftdc-overview-disk-free-data-db.svg"

    chart_paths = [tmp_path / result["chart"] for results in item._results.values() for result in results]
    assert all(chart.is_file() for chart in chart_paths)
    for chart in chart_paths:
        assert ElementTree.parse(chart).getroot().tag == "{http://www.w3.org/2000/svg}svg"


def test_overview_ignores_counter_resets_and_large_gaps(tmp_path):
    item = OverviewItem(str(tmp_path), {"max_sample_gap_seconds": 2})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    late = start + timedelta(seconds=10)
    item._series = {
        CPU_METRICS["available_cores"]: {start: 2, late: 2},
        CPU_METRICS["user"]: {start: 100, late: 50},
        OPCOUNTER_METRICS["query"]: {start: 100, late: 50},
    }

    item.finalize_analysis()

    assert item._results["Workload"][0]["peak"] == 0
    assert item._results["Performance"][2]["peak"] == 0


def test_overview_displays_capture_metadata_and_sections(tmp_path):
    item = OverviewItem(str(tmp_path), {}, total_ingest_files=4)
    item._capture_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item._capture_end = datetime(2026, 1, 2, tzinfo=timezone.utc)
    item.finalize_analysis()
    output = StringIO()

    item.review_results_markdown(output)

    report = output.getvalue()
    assert "Capture timespan: `2026-01-01T00:00:00+00:00` to `2026-01-02T00:00:00+00:00`" in report
    assert "Sample rate: `0.25`" in report
    assert "### Workload" in report
    assert "### Read/Write Operations and Latencies" in report
    assert "### Performance" in report
    assert "#### Overview" not in report
