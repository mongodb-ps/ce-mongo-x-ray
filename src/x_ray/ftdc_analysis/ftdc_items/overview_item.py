"""Peak and average values for key FTDC host metrics."""

from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean

from pyftdc import FTDCReader

from x_ray.ftdc_analysis.ftdc_items.base_item import BaseItem
from x_ray.ftdc_analysis.parsers.overview_parser import OverviewParser


class OverviewItem(BaseItem):
    """Summarize CPU utilization and storage operation rates."""

    _CPU_USER = "systemMetrics.cpu.user_ms"
    _CPU_SYSTEM = "systemMetrics.cpu.system_ms"
    _CPU_CORES = "systemMetrics.cpu.num_cores_available_to_process"

    def __init__(self, output_folder: str, config: dict, **kwargs) -> None:
        super().__init__(output_folder, config, **kwargs)
        self._start_time = kwargs.get("start_time") or datetime.min.replace(tzinfo=timezone.utc)
        self._end_time = kwargs.get("end_time") or datetime.max.replace(tzinfo=timezone.utc)
        self._max_gap = float(config.get("max_sample_gap_seconds", 5))
        self._sample_rate = float(config.get("sample_rate", 1.0))
        self._series: dict[str, dict[datetime, float]] = {}
        self._disk_metrics: set[str] = set()
        self._results: list[dict] = []

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
            target.update((point.timestamp, float(point.value)) for point in points)

    def finalize_analysis(self) -> None:
        self._results = [
            self._summary("CPU user", self._cpu_rates(self._CPU_USER), "%"),
            self._summary("CPU system", self._cpu_rates(self._CPU_SYSTEM), "%"),
            self._summary("IOPS", self._iops_rates(), "ops/s"),
        ]

    def _cpu_rates(self, metric: str) -> list[float]:
        counters = self._series.get(metric, {})
        cores = self._series.get(self._CPU_CORES, {})
        timestamps = sorted(set(counters) & set(cores))
        rates: list[float] = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed_ms = (current - previous).total_seconds() * 1000
            delta = counters[current] - counters[previous]
            core_count = cores[current]
            if self._valid_interval(elapsed_ms / 1000, delta) and core_count > 0:
                rates.append(100 * delta / (elapsed_ms * core_count))
        return rates

    def _iops_rates(self) -> list[float]:
        totals: dict[datetime, float] = {}
        for metric in self._disk_metrics:
            for timestamp, value in self._series.get(metric, {}).items():
                totals[timestamp] = totals.get(timestamp, 0) + value

        timestamps = sorted(totals)
        rates: list[float] = []
        for previous, current in zip(timestamps, timestamps[1:]):
            elapsed = (current - previous).total_seconds()
            delta = totals[current] - totals[previous]
            if self._valid_interval(elapsed, delta):
                rates.append(delta / elapsed)
        return rates

    def _valid_interval(self, elapsed: float, delta: float) -> bool:
        return 0 < elapsed <= self._max_gap and delta >= 0

    @staticmethod
    def _summary(metric: str, values: list[float], unit: str) -> dict:
        return {
            "metric": metric,
            "peak": max(values, default=0.0),
            "average": fmean(values) if values else 0.0,
            "unit": unit,
        }

    def review_results_markdown(self, output) -> None:
        output.write("## FTDC Overview\n\n")
        output.write(OverviewParser().markdown(self._results))
