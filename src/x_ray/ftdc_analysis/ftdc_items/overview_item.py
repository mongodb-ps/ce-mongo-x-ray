"""Peak and average values for key FTDC host metrics."""

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


class OverviewItem(BaseItem):
    """Summarize CPU utilization and storage operation rates."""

    _WIDTH = 480
    _HEIGHT = 50
    _CPU_USER = "systemMetrics.cpu.user_ms"
    _CPU_SYSTEM = "systemMetrics.cpu.system_ms"
    _CPU_CORES = "systemMetrics.cpu.num_cores_available_to_process"

    def __init__(self, output_folder: str, config: dict, **kwargs) -> None:
        super().__init__(output_folder, config, **kwargs)
        self._start_time = kwargs.get("start_time")
        self._end_time = kwargs.get("end_time")
        self._max_gap = float(config.get("max_sample_gap_seconds", 5))
        total_ingest_files = int(kwargs.get("total_ingest_files", 1))
        default_sample_rate = 1 / total_ingest_files if total_ingest_files > 0 else 1.0
        self._sample_rate = float(config.get("sample_rate", default_sample_rate))
        self._series: dict[str, dict[datetime, float]] = {}
        self._disk_metrics: set[str] = set()
        self._results: list[dict] = []
        self._capture_start: Optional[datetime] = None
        self._capture_end: Optional[datetime] = None

    def analyze(self, file_path: Path) -> None:
        reader = FTDCReader(file_path)
        available = set(reader.list_metrics())
        wanted = {self._CPU_USER, self._CPU_SYSTEM, self._CPU_CORES}
        wanted.update(
            metric
            for metric in available
            if metric.startswith("systemMetrics.disks.") and (metric.endswith(".reads") or metric.endswith(".writes"))
        )
        wanted.intersection_update(available)
        if not wanted:
            return

        series = reader.get_metric(
            wanted,
            self._start_time,
            self._end_time,
            sample_rate=self._sample_rate,
        )
        for metric, points in series.items():
            if metric.startswith("systemMetrics.disks."):
                self._disk_metrics.add(metric)
            target = self._series.setdefault(metric, {})
            for point in points:
                target[point.timestamp] = float(point.value)
                if self._capture_start is None or point.timestamp < self._capture_start:
                    self._capture_start = point.timestamp
                if self._capture_end is None or point.timestamp > self._capture_end:
                    self._capture_end = point.timestamp

    def finalize_analysis(self) -> None:
        cpu_user = self._cpu_rates(self._CPU_USER)
        cpu_system = self._cpu_rates(self._CPU_SYSTEM)
        iops = self._iops_rates()
        self._results = [
            self._summary("CPU user", cpu_user, "%"),
            self._summary("CPU system", cpu_system, "%"),
            self._summary("IOPS", iops, "ops/s"),
        ]

    def _cpu_rates(self, metric: str) -> list[tuple[datetime, float]]:
        counters = self._series.get(metric, {})
        cores = self._series.get(self._CPU_CORES, {})
        timestamps = sorted(set(counters) & set(cores))
        rates: list[tuple[datetime, float]] = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed_ms = (current - previous).total_seconds() * 1000
            delta = counters[current] - counters[previous]
            core_count = cores[current]
            if self._valid_interval(elapsed_ms / 1000, delta) and core_count > 0:
                value = 100 * delta / (elapsed_ms * core_count)
                if isfinite(value):
                    rates.append((current, value))
        return rates

    def _iops_rates(self) -> list[tuple[datetime, float]]:
        totals: dict[datetime, float] = {}
        for metric in self._disk_metrics:
            for timestamp, value in self._series.get(metric, {}).items():
                totals[timestamp] = totals.get(timestamp, 0) + value

        timestamps = sorted(totals)
        rates: list[tuple[datetime, float]] = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed = (current - previous).total_seconds()
            delta = totals[current] - totals[previous]
            if self._valid_interval(elapsed, delta):
                value = delta / elapsed
                if isfinite(value):
                    rates.append((current, value))
        return rates

    def _valid_interval(self, elapsed: float, delta: float) -> bool:
        return 0 < elapsed <= self._max_gap and delta >= 0

    def _summary(self, metric: str, points: list[tuple[datetime, float]], unit: str) -> dict:
        values = [value for _, value in points]
        return {
            "metric": metric,
            "peak": max(values, default=0.0),
            "average": fmean(values) if values else 0.0,
            "unit": unit,
            "chart": self._write_chart(metric, points, unit),
        }

    def _write_chart(self, metric: str, points: list[tuple[datetime, float]], unit: str) -> str:
        chart_folder = self.output_folder / "charts"
        chart_folder.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", metric.lower()).strip("-")
        relative_path = Path("charts") / f"ftdc-overview-{slug}.svg"

        width, height = self._WIDTH, self._HEIGHT
        left, right, top, bottom = 52, 12, 8, 12
        plot_width = width - left - right
        plot_height = height - top - bottom
        values = [value for _, value in points]
        y_max = max(values, default=0.0)
        scale_max = y_max if y_max > 0 else 1.0

        polyline = ""
        if points:
            start_time = points[0][0]
            end_time = points[-1][0]
            duration = (end_time - start_time).total_seconds()
            coordinates = []
            for timestamp, value in points:
                x_ratio = (timestamp - start_time).total_seconds() / duration if duration > 0 else 0.5
                x = left + x_ratio * plot_width
                y = top + plot_height - (value / scale_max) * plot_height
                coordinates.append(f"{x:.2f},{y:.2f}")
            polyline = (
                '<polyline class="metric-line" fill="none" stroke-width="1" '
                f'stroke-linejoin="round" points="{" ".join(coordinates)}"/>'
            )
        else:
            polyline = (
                f'<text x="{left + plot_width / 2:.2f}" y="{top + plot_height / 2:.2f}" '
                'text-anchor="middle">No data available</text>'
            )

        peak_label = escape(f"{round(y_max, 2)}{unit}")
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(metric)} line chart">'
            "<style>"
            "text{font:11px sans-serif;fill:#57606a}"
            ".metric-line{stroke:#0969da}"
            "@media (prefers-color-scheme:dark){.metric-line{stroke:#58a6ff}}"
            "</style>"
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#8c959f"/>'
            f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
            f'y2="{top + plot_height}" stroke="#8c959f"/>'
            f'<text x="{left - 6}" y="{top + 4}" text-anchor="end">{peak_label}</text>'
            f'<text x="{left - 6}" y="{top + plot_height + 4}" text-anchor="end">0{escape(unit)}</text>'
            f"{polyline}</svg>"
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
        output.write(OverviewParser().markdown(self._results))
