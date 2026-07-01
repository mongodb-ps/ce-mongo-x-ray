"""Reusable chart rendering for FTDC analysis reports."""

import re
from datetime import datetime
from html import escape
from math import isfinite
from pathlib import Path
from typing import Literal, Mapping, Optional, Sequence, Union

BAR_COLORS = frozenset({"blue", "gray", "green", "red", "yellow"})

_BAR_COLOR_HEX: dict[Optional[str], str] = {
    None: "#0969da",
    "green": "#1a7f37",
    "yellow": "#bf8700",
    "red": "#cf222e",
    "blue": "#0969da",
    "gray": "#656d76",
}

_TEXT_COLOR = "#57606a"
_AXIS_COLOR = "#8c959f"

_LEFT, _RIGHT, _TOP, _BOTTOM = 52, 12, 8, 12


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


def _bar_color_name(
    value: float,
    thresholds: Optional[tuple[float, float]],
    value_colors: Optional[Mapping[float, str]],
) -> Optional[str]:
    if value_colors is not None:
        return value_colors.get(value)
    if thresholds is None:
        return None
    lower, upper = thresholds
    if value <= lower:
        return "green"
    if value > upper:
        return "red"
    return "yellow"


def _draw_png(
    output_path: Path,
    points: Sequence[tuple[datetime, float]],
    width: int,
    height: int,
    thresholds: Optional[tuple[float, float]],
    value_colors: Optional[Mapping[float, str]],
    scale: int = 2,
) -> None:
    from PIL import Image, ImageDraw, ImageFont  # pylint: disable=import-outside-toplevel

    left = _LEFT * scale
    right = _RIGHT * scale
    top = _TOP * scale
    bottom = _BOTTOM * scale
    render_width = width * scale
    render_height = height * scale
    plot_width = render_width - left - right
    plot_height = render_height - top - bottom
    values = [value for _, value in points]
    y_max = max(values, default=0.0)
    scale_max = y_max if y_max > 0 else 1.0

    img = Image.new("RGBA", (render_width, render_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    draw.line(
        [(left, top), (left, top + plot_height)],
        fill=_AXIS_COLOR,
    )
    draw.line(
        [(left, top + plot_height), (render_width - right, top + plot_height)],
        fill=_AXIS_COLOR,
    )

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9 * scale)
    except OSError:
        font = ImageFont.load_default()

    peak_label = str(round(y_max, 2))
    draw.text(
        (left - 6 * scale, top),
        peak_label,
        fill=_TEXT_COLOR,
        font=font,
        anchor="ra",
    )
    draw.text(
        (left - 6 * scale, top + plot_height),
        "0",
        fill=_TEXT_COLOR,
        font=font,
        anchor="ra",
    )

    if not points:
        draw.text(
            (left + plot_width / 2, top + plot_height / 2),
            "No data available",
            fill=_TEXT_COLOR,
            font=font,
            anchor="mm",
        )
        img.save(output_path, "PNG")
        return

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
        color_name = _bar_color_name(value, thresholds, value_colors)
        hex_color = _BAR_COLOR_HEX[color_name]
        draw.rectangle(
            [x, y, x + bar_width, y + bar_h],
            fill=hex_color,
        )

    img.save(output_path, "PNG")


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
    image_format: Literal["png", "svg"] = "png",
) -> str:
    """Render a time-series bar chart and return its relative path.

    By default the chart is saved as a PNG image. Pass ``image_format="svg"``
    to keep the SVG source file instead.
    """
    if image_format not in ("png", "svg"):
        raise ValueError(f"unsupported image format: {image_format!r}")
    output_folder = Path(output_folder)
    if thresholds is not None and value_colors is not None:
        raise ValueError("chart thresholds and value colors cannot be combined")
    parsed_thresholds = _parse_thresholds(thresholds)
    parsed_value_colors = _parse_value_colors(value_colors)
    chart_folder = output_folder / "charts"
    chart_folder.mkdir(parents=True, exist_ok=True)
    slug = slug or re.sub(r"[^a-z0-9]+", "-", metric.lower()).strip("-")
    relative_path = Path("charts") / f"{filename_prefix}-{slug}.{image_format}"
    output_path = output_folder / relative_path

    if image_format == "png":
        _draw_png(output_path, points, width, height, parsed_thresholds, parsed_value_colors)
        return relative_path.as_posix()

    left, right, top, bottom = _LEFT, _RIGHT, _TOP, _BOTTOM
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
                f'<rect class="{bar_class}" x="{x:.2f}" y="{y:.2f}" '
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
    output_path.write_text(svg, encoding="utf-8")
    return relative_path.as_posix()
