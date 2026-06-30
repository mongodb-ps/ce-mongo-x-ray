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
        self._disk_queue_metrics: set[str] = set()
        self._mount_free_metrics: dict[str, str] = {}
        self._results: dict[str, list[dict]] = {}
        self._capture_start: Optional[datetime] = None
        self._capture_end: Optional[datetime] = None

    def analyze(self, file_path: Path) -> None:
        reader = FTDCReader(file_path)
        available = set(reader.list_metrics())
        wanted = OVERVIEW_STATIC_METRICS & available

        for metric in available:
            if metric.startswith(DISK_METRIC_PREFIX) and metric.endswith(f'.{DISK_METRICS["io_in_progress"]}'):
                wanted.add(metric)
                self._disk_queue_metrics.add(metric)
            mount_point = self._mount_point(metric)
            if mount_point is not None and self._is_data_volume_mount(mount_point):
                wanted.add(metric)
                self._mount_free_metrics[metric] = mount_point

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
    def _mount_point(metric: str) -> Optional[str]:
        prefix = MOUNT_METRIC_PREFIX
        suffix = f'.{MOUNT_METRICS["free"]}'
        if metric.startswith(prefix) and metric.endswith(suffix):
            return metric[len(prefix) : -len(suffix)]
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
            self._summary(name.capitalize(), self._counter_rate(metric), "ops/s")
            for name, metric in OPCOUNTER_METRICS.items()
        ]

        read_write = []
        for operation in ("reads", "writes"):
            metrics = OP_LATENCY_METRICS[operation]
            label = operation.capitalize()
            read_write.extend(
                [
                    self._summary(label, self._counter_rate(metrics["ops"]), "ops/s"),
                    self._summary(
                        f"{label[:-1]} latency",
                        self._average_latency(metrics["ops"], metrics["latency"]),
                        "ms/op",
                    ),
                ]
            )

        performance = [
            self._summary(
                "System memory utilization",
                self._ratio(MEMORY_METRICS["total"], MEMORY_METRICS["available"], subtract=True),
                "%",
            ),
            self._summary(
                "Memory fragmentation ratio",
                self._ratio(
                    TCMALLOC_METRICS["heap_size"],
                    TCMALLOC_METRICS["current_allocated_bytes"],
                    subtract=True,
                ),
                "%",
            ),
            self._summary("CPU user", self._cpu_rates(CPU_METRICS["user"]), "%"),
            self._summary("CPU system", self._cpu_rates(CPU_METRICS["system"]), "%"),
            self._summary("I/O wait", self._cpu_rates(CPU_METRICS["iowait"]), "%"),
            self._summary(
                "Cache fill",
                self._ratio(
                    WIREDTIGER_CACHE_METRICS["bytes_maximum"],
                    WIREDTIGER_CACHE_METRICS["bytes_current"],
                ),
                "%",
            ),
            self._summary(
                "Cache dirty",
                self._ratio(
                    WIREDTIGER_CACHE_METRICS["bytes_maximum"],
                    WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"],
                ),
                "%",
            ),
            self._summary("Disk queue length", self._aggregate_gauges(self._disk_queue_metrics), "requests"),
        ]
        used_mount_slugs: set[str] = set()
        for metric, mount_point in sorted(self._mount_free_metrics.items(), key=lambda item: item[1]):
            points = [
                (timestamp, value / (1024**3))
                for timestamp, value in sorted(self._series.get(metric, {}).items())
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
                    f"Disk free ({display_mount})",
                    points,
                    "GiB",
                    slug=f"disk-free-{slug}",
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
        cores = self._series.get(CPU_METRICS["available_cores"], {})
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

    def _aggregate_gauges(self, metrics: set[str]) -> list[tuple[datetime, float]]:
        totals: dict[datetime, float] = {}
        for metric in metrics:
            for timestamp, value in self._series.get(metric, {}).items():
                totals[timestamp] = totals.get(timestamp, 0) + value
        return [(timestamp, value) for timestamp, value in sorted(totals.items()) if isfinite(value)]

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

    def review_results_markdown(self, output) -> None:
        output.write("## FTDC Overview\n\n")
        if self._capture_start is not None and self._capture_end is not None:
            start = self._capture_start.isoformat()
            end = self._capture_end.isoformat()
            output.write(f"Capture timespan: `{start}` to `{end}`\n\n")
        else:
            output.write("Capture timespan: _No data available._\n\n")
        output.write(f"Sample rate: `{self._sample_rate:.6g}`\n\n")
        parser = OverviewParser()
        for section, results in self._results.items():
            output.write(f"### {section}\n\n")
            output.write(parser.markdown(results, caption=None))
