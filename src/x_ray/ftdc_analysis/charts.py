"""Reusable chart rendering for FTDC analysis reports."""

import re
from datetime import datetime
from html import escape
from math import isfinite
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

BAR_COLORS = frozenset({"blue", "gray", "green", "red", "yellow"})


def _parse_thresholds(
    thresholds: Optional[tuple[float, float]],
) -> Optional[tuple[float, float]]:
    if thresholds is None:
        return None
    if not isinstance(thresholds, (list, tuple)) or len(thresholds) != 2:
        raise ValueError("chart thresholds must contain exactly two numbers")
    if any(isinstance(threshold, bool) for threshold in thresholds):
        raise ValueError("chart thresholds must contain exactly two numbers")
    try:
        lower, upper = (float(threshold) for threshold in thresholds)
    except (TypeError, ValueError) as exc:
        raise ValueError("chart thresholds must contain exactly two numbers") from exc
    if not isfinite(lower) or not isfinite(upper) or lower >= upper:
        raise ValueError("chart thresholds must be finite and ordered from lowest to highest")
    return lower, upper


def _parse_value_colors(
    value_colors: Optional[Mapping[float, str]],
) -> Optional[dict[float, str]]:
    if value_colors is None:
        return None
    if not isinstance(value_colors, Mapping):
        raise ValueError("chart value colors must map finite numbers to supported colors")

    parsed = {}
    for value, color in value_colors.items():
        if isinstance(value, bool):
            raise ValueError("chart value colors must map finite numbers to supported colors")
        try:
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("chart value colors must map finite numbers to supported colors") from exc
        if not isfinite(numeric_value) or color not in BAR_COLORS:
            raise ValueError("chart value colors must map finite numbers to supported colors")
        parsed[numeric_value] = color
    return parsed


def _bar_class(
    value: float,
    thresholds: Optional[tuple[float, float]],
    value_colors: Optional[Mapping[float, str]],
) -> str:
    if value_colors is not None:
        color = value_colors.get(value)
        return f"metric-bar metric-bar-{color}" if color is not None else "metric-bar"
    if thresholds is None:
        return "metric-bar"
    lower, upper = thresholds
    if value <= lower:
        return "metric-bar metric-bar-green"
    if value > upper:
        return "metric-bar metric-bar-red"
    return "metric-bar metric-bar-yellow"


def write_bar_chart(
    output_folder: Union[Path, str],
    metric: str,
    points: Sequence[tuple[datetime, float]],
    *,
    slug: Optional[str] = None,
    thresholds: Optional[tuple[float, float]] = None,
    value_colors: Optional[Mapping[float, str]] = None,
    filename_prefix: str = "ftdc-baseline-analysis",
    width: int = 480,
    height: int = 50,
) -> str:
    """Render a time-series bar chart as SVG and return its relative path."""
    output_folder = Path(output_folder)
    if thresholds is not None and value_colors is not None:
        raise ValueError("chart thresholds and value colors cannot be combined")
    parsed_thresholds = _parse_thresholds(thresholds)
    parsed_value_colors = _parse_value_colors(value_colors)
    chart_folder = output_folder / "charts"
    chart_folder.mkdir(parents=True, exist_ok=True)
    slug = slug or re.sub(r"[^a-z0-9]+", "-", metric.lower()).strip("-")
    relative_path = Path("charts") / f"{filename_prefix}-{slug}.svg"

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
            bar_class = _bar_class(value, parsed_thresholds, parsed_value_colors)
            bars += (
                f'<rect class="{bar_class}" x="{x:.2f}" y="{y:.2f}" ' f'width="{bar_width:.2f}" height="{bar_h:.2f}"/>'
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
        ".metric-bar-green{fill:green}"
        ".metric-bar-yellow{fill:yellow}"
        ".metric-bar-red{fill:red}"
        ".metric-bar-blue{fill:blue}"
        ".metric-bar-gray{fill:gray}"
        "</style>"
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#8c959f"/>'
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
        f'y2="{top + plot_height}" stroke="#8c959f"/>'
        f'<text x="{left - 6}" y="{top + 4}" text-anchor="end">{peak_label}</text>'
        f'<text x="{left - 6}" y="{top + plot_height + 4}" text-anchor="end">0</text>'
        f"{bars}</svg>"
    )
    (output_folder / relative_path).write_text(svg, encoding="utf-8")
    return relative_path.as_posix()
