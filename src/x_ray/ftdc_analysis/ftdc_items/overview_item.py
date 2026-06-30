"""Workload, latency, and host performance summaries for FTDC captures."""

import re
from datetime import datetime
from html import escape
from math import isfinite
from pathlib import Path
from statistics import fmean
from typing import Optional

from pyftdc import FTDCReader

from x_ray.ftdc_analysis.ftdc_items.base_item import BaseItem
from x_ray.ftdc_analysis.parsers.overview_parser import OverviewParser
from x_ray.ftdc_analysis.shared import (
    CPU_METRICS,
    DERIVED_METRIC_NAMES,
    DISK_METRIC_PREFIX,
    DISK_METRICS,
    MEMORY_METRICS,
    MOUNT_METRIC_PREFIX,
    MOUNT_METRICS,
    OPCOUNTER_METRICS,
    OP_LATENCY_METRICS,
    OVERVIEW_STATIC_METRICS,
    TCMALLOC_METRICS,
    WIREDTIGER_CACHE_METRICS,
)


class OverviewItem(BaseItem):
    """Summarize the workload and performance represented by an FTDC capture."""

    _WIDTH = 480
    _HEIGHT = 50

    def __init__(self, output_folder: str, config: dict, **kwargs) -> None:
        super().__init__(output_folder, config, **kwargs)
        self._start_time = kwargs.get("start_time")
        self._end_time = kwargs.get("end_time")
        self._max_gap = float(config.get("max_sample_gap_seconds", 5))
        total_ingest_files = int(kwargs.get("total_ingest_files", 1))
        default_sample_rate = 1 / total_ingest_files if total_ingest_files > 0 else 1.0
        self._sample_rate = float(config.get("sample_rate", default_sample_rate))
        self._series: dict[str, dict[datetime, float]] = {}
        self._disk_queue_metrics: dict[str, str] = {}
        self._mount_metrics: dict[str, dict[str, str]] = {}
        self._results: dict[str, list[dict]] = {}
        self._capture_start: Optional[datetime] = None
        self._capture_end: Optional[datetime] = None

    def analyze(self, file_path: Path) -> None:
        reader = FTDCReader(file_path)
        available = set(reader.list_metrics())
        wanted = OVERVIEW_STATIC_METRICS & available

        for metric in available:
            block_device = self._block_device(metric)
            if block_device is not None:
                wanted.add(metric)
                self._disk_queue_metrics[metric] = block_device
            mount_metric = self._mount_metric(metric)
            if mount_metric is not None and self._is_data_volume_mount(mount_metric[0]):
                mount_point, field = mount_metric
                wanted.add(metric)
                self._mount_metrics.setdefault(mount_point, {})[field] = metric

        if not wanted:
            return

        series = reader.get_metric(
            wanted,
            self._start_time,
            self._end_time,
            sample_rate=self._sample_rate,
        )
        for metric, points in series.items():
            target = self._series.setdefault(metric, {})
            for point in points:
                target[point.timestamp] = float(point.value)
                if self._capture_start is None or point.timestamp < self._capture_start:
                    self._capture_start = point.timestamp
                if self._capture_end is None or point.timestamp > self._capture_end:
                    self._capture_end = point.timestamp

    @staticmethod
    def _block_device(metric: str) -> Optional[str]:
        suffix = f'.{DISK_METRICS["io_in_progress"].key}'
        if metric.startswith(DISK_METRIC_PREFIX) and metric.endswith(suffix):
            return metric[len(DISK_METRIC_PREFIX) : -len(suffix)]
        return None

    @staticmethod
    def _mount_metric(metric: str) -> Optional[tuple[str, str]]:
        if not metric.startswith(MOUNT_METRIC_PREFIX):
            return None
        for field in ("free", "capacity"):
            suffix = f".{MOUNT_METRICS[field].key}"
            if metric.endswith(suffix):
                return metric[len(MOUNT_METRIC_PREFIX) : -len(suffix)], field
        return None

    @staticmethod
    def _is_data_volume_mount(mount_point: str) -> bool:
        """Exclude virtual filesystems and common container file bind mounts."""
        virtual_roots = ("/dev", "/proc", "/sys")
        if any(mount_point == root or mount_point.startswith(f"{root}/") for root in virtual_roots):
            return False
        return mount_point not in {"/etc/hostname", "/etc/hosts", "/etc/resolv.conf"}

    def finalize_analysis(self) -> None:
        workload = [
            self._summary(metric.name, self._counter_rate(metric.key), "ops/s") for metric in OPCOUNTER_METRICS.values()
        ]

        read_write = []
        for operation in ("reads", "writes"):
            metrics = OP_LATENCY_METRICS[operation]
            read_write.extend(
                [
                    self._summary(
                        metrics["ops"].name,
                        self._counter_rate(metrics["ops"].key),
                        "ops/s",
                    ),
                    self._summary(
                        metrics["latency"].name,
                        self._average_latency(metrics["ops"].key, metrics["latency"].key),
                        "ms/op",
                    ),
                ]
            )

        performance = [
            self._summary(
                DERIVED_METRIC_NAMES["system_memory_utilization"],
                self._ratio(
                    MEMORY_METRICS["total"].key,
                    MEMORY_METRICS["available"].key,
                    subtract=True,
                ),
                "%",
            ),
            self._summary(
                DERIVED_METRIC_NAMES["memory_fragmentation_ratio"],
                self._ratio(
                    TCMALLOC_METRICS["heap_size"].key,
                    TCMALLOC_METRICS["current_allocated_bytes"].key,
                    subtract=True,
                ),
                "%",
            ),
            self._summary(CPU_METRICS["user"].name, self._cpu_rates(CPU_METRICS["user"].key), "%"),
            self._summary(CPU_METRICS["system"].name, self._cpu_rates(CPU_METRICS["system"].key), "%"),
            self._summary(CPU_METRICS["iowait"].name, self._cpu_rates(CPU_METRICS["iowait"].key), "%"),
            self._summary(
                DERIVED_METRIC_NAMES["cache_fill"],
                self._ratio(
                    WIREDTIGER_CACHE_METRICS["bytes_maximum"].key,
                    WIREDTIGER_CACHE_METRICS["bytes_current"].key,
                ),
                "%",
            ),
            self._summary(
                DERIVED_METRIC_NAMES["cache_dirty"],
                self._ratio(
                    WIREDTIGER_CACHE_METRICS["bytes_maximum"].key,
                    WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"].key,
                ),
                "%",
            ),
        ]
        for metric, block_device in sorted(self._disk_queue_metrics.items(), key=lambda item: item[1]):
            points = [
                (timestamp, value)
                for timestamp, value in sorted(self._series.get(metric, {}).items())
                if isfinite(value)
            ]
            performance.append(
                self._summary(
                    f'{DISK_METRICS["io_in_progress"].name} ({block_device})',
                    points,
                    "requests",
                    slug=f"disk-queue-length-{self._mount_slug(block_device)}",
                )
            )

        used_mount_slugs: set[str] = set()
        for mount_point, metrics in sorted(self._mount_metrics.items()):
            free_points = [
                (timestamp, value / (1024**3))
                for timestamp, value in sorted(self._series.get(metrics.get("free", ""), {}).items())
                if isfinite(value)
            ]
            display_mount = mount_point or "/"
            slug = self._mount_slug(display_mount)
            base_slug = slug
            suffix = 2
            while slug in used_mount_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_mount_slugs.add(slug)
            performance.append(
                self._summary(
                    f'{MOUNT_METRICS["free"].name} ({display_mount})',
                    free_points,
                    "GiB",
                    slug=f"disk-free-{slug}",
                )
            )
            performance.append(
                self._summary(
                    f'{DERIVED_METRIC_NAMES["disk_utilization"]} ({display_mount})',
                    self._ratio(
                        metrics.get("capacity", ""),
                        metrics.get("free", ""),
                        subtract=True,
                    ),
                    "%",
                    slug=f"disk-utilization-{slug}",
                )
            )

        self._results = {
            "Workload": workload,
            "Read/Write Operations and Latencies": read_write,
            "Performance": performance,
        }

    @staticmethod
    def _mount_slug(mount_point: str) -> str:
        if mount_point == "/":
            return "root"
        return re.sub(r"[^a-z0-9]+", "-", mount_point.lower()).strip("-") or "root"

    def _counter_rate(self, metric: str) -> list[tuple[datetime, float]]:
        points = self._series.get(metric, {})
        timestamps = sorted(points)
        rates = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed = (current - previous).total_seconds()
            delta = points[current] - points[previous]
            if self._valid_interval(elapsed, delta):
                value = delta / elapsed
                if isfinite(value):
                    rates.append((current, value))
        return rates

    def _average_latency(self, ops_metric: str, latency_metric: str) -> list[tuple[datetime, float]]:
        ops = self._series.get(ops_metric, {})
        latency = self._series.get(latency_metric, {})
        timestamps = sorted(set(ops) & set(latency))
        points = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed = (current - previous).total_seconds()
            operation_count = ops[current] - ops[previous]
            latency_micros = latency[current] - latency[previous]
            if self._valid_interval(elapsed, operation_count) and operation_count > 0 and latency_micros >= 0:
                value = latency_micros / operation_count / 1000
                if isfinite(value):
                    points.append((current, value))
        return points

    def _ratio(self, denominator_metric: str, numerator_metric: str, *, subtract: bool = False):
        denominator = self._series.get(denominator_metric, {})
        numerator = self._series.get(numerator_metric, {})
        points = []
        for timestamp in sorted(set(denominator) & set(numerator)):
            total = denominator[timestamp]
            used = total - numerator[timestamp] if subtract else numerator[timestamp]
            if total > 0:
                value = 100 * used / total
                if isfinite(value):
                    points.append((timestamp, value))
        return points

    def _cpu_rates(self, metric: str) -> list[tuple[datetime, float]]:
        counters = self._series.get(metric, {})
        cores = self._series.get(CPU_METRICS["available_cores"].key, {})
        timestamps = sorted(set(counters) & set(cores))
        rates = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed_ms = (current - previous).total_seconds() * 1000
            delta = counters[current] - counters[previous]
            core_count = cores[current]
            if self._valid_interval(elapsed_ms / 1000, delta) and core_count > 0:
                value = 100 * delta / (elapsed_ms * core_count)
                if isfinite(value):
                    rates.append((current, value))
        return rates

    def _valid_interval(self, elapsed: float, delta: float) -> bool:
        return 0 < elapsed <= self._max_gap and delta >= 0

    def _summary(
        self,
        metric: str,
        points: list[tuple[datetime, float]],
        unit: str,
        *,
        slug: Optional[str] = None,
    ) -> dict:
        values = [value for _, value in points]
        return {
            "metric": metric,
            "peak": max(values, default=0.0),
            "average": fmean(values) if values else 0.0,
            "unit": unit,
            "chart": self._write_chart(metric, points, slug=slug),
        }

    def _write_chart(
        self,
        metric: str,
        points: list[tuple[datetime, float]],
        *,
        slug: Optional[str] = None,
    ) -> str:
        chart_folder = self.output_folder / "charts"
        chart_folder.mkdir(parents=True, exist_ok=True)
        slug = slug or re.sub(r"[^a-z0-9]+", "-", metric.lower()).strip("-")
        relative_path = Path("charts") / f"ftdc-overview-{slug}.svg"

        width, height = self._WIDTH, self._HEIGHT
        left, right, top, bottom = 52, 12, 8, 12
        plot_width = width - left - right
        plot_height = height - top - bottom
        values = [value for _, value in points]
        y_max = max(values, default=0.0)
        scale_max = y_max if y_max > 0 else 1.0

        bars = ""
        if points:
            start_time = points[0][0]
            end_time = points[-1][0]
            duration = (end_time - start_time).total_seconds()
            count = len(points)
            bar_width = max(1, plot_width / count - 1)
            for timestamp, value in points:
                x_ratio = (timestamp - start_time).total_seconds() / duration if duration > 0 else 0.5
                x = left + x_ratio * plot_width - bar_width / 2
                bar_h = (value / scale_max) * plot_height
                y = top + plot_height - bar_h
                bars += (
                    f'<rect class="metric-bar" x="{x:.2f}" y="{y:.2f}" '
                    f'width="{bar_width:.2f}" height="{bar_h:.2f}"/>'
                )
        else:
            bars = (
                f'<text x="{left + plot_width / 2:.2f}" y="{top + plot_height / 2:.2f}" '
                'text-anchor="middle">No data available</text>'
            )

        peak_label = round(y_max, 2)
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(metric)} bar chart">'
            "<style>"
            "text{font:9px sans-serif;fill:#57606a}"
            ".metric-bar{fill:#0969da}"
            "@media (prefers-color-scheme:dark){.metric-bar{fill:#58a6ff}}"
            "</style>"
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#8c959f"/>'
            f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
            f'y2="{top + plot_height}" stroke="#8c959f"/>'
            f'<text x="{left - 6}" y="{top + 4}" text-anchor="end">{peak_label}</text>'
            f'<text x="{left - 6}" y="{top + plot_height + 4}" text-anchor="end">0</text>'
            f"{bars}</svg>"
        )
        (self.output_folder / relative_path).write_text(svg, encoding="utf-8")
        return relative_path.as_posix()

    def review_results_markdown(self, output, section_number: int = 1) -> None:
        output.write(f"## {section_number}. FTDC Overview\n\n")
        if self._capture_start is not None and self._capture_end is not None:
            start = self._capture_start.isoformat()
            end = self._capture_end.isoformat()
            output.write(f"Capture timespan: `{start}` to `{end}`\n\n")
        else:
            output.write("Capture timespan: _No data available._\n\n")
        output.write(f"Sample rate: `{self._sample_rate:.6g}`\n\n")
        parser = OverviewParser()
        for subsection_number, (section, results) in enumerate(self._results.items(), start=1):
            output.write(f"### {section_number}.{subsection_number}. {section}\n\n")
            output.write(parser.markdown(results, caption=None))
