"""Reusable chart rendering for FTDC analysis reports."""

import re
from datetime import datetime, timedelta
from html import escape
from math import isfinite
from pathlib import Path
from typing import Literal, Mapping, Optional, Sequence, Union

BAR_COLORS = frozenset({"blue", "gray", "green", "red", "yellow"})
DEFAULT_CHART_WIDTH = 500
DEFAULT_CHART_HEIGHT = 150
MEMBER_STATE_CHART_WIDTH = 500
MEMBER_STATE_CHART_HEIGHT = 50

_BAR_COLOR_HEX: dict[Optional[str], str] = {
    None: "#0072b2",
    "green": "#009e73",
    "yellow": "#e69f00",
    "red": "#cc3311",
    "blue": "#0072b2",
    "gray": "#667085",
}

_TEXT_COLOR = "#57606a"
_AXIS_COLOR = "#8c959f"
_GRID_COLOR = "#d0d7de"
_X_GRID_SPACING = 100
_Y_GRID_SPACING = 50

_LEFT, _RIGHT, _TOP, _BOTTOM = 52, 28, 8, 24


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


def _line_class(
    value: float,
    thresholds: Optional[tuple[float, float]],
    value_colors: Optional[Mapping[float, str]],
) -> str:
    color = _bar_color_name(value, thresholds, value_colors)
    return f"metric-line metric-line-{color}" if color is not None else "metric-line"


def _exceeds_threshold(
    value: float,
    thresholds: Optional[tuple[float, float]],
) -> bool:
    return thresholds is not None and value > thresholds[0]


def _grid_offsets(length: int, spacing: int) -> range:
    return range(0, max(0, int(length)) + 1, spacing)


def _draw_png(
    output_path: Path,
    points: Sequence[tuple[datetime, float]],
    width: int,
    height: int,
    thresholds: Optional[tuple[float, float]],
    value_colors: Optional[Mapping[float, str]],
    chart_type: Literal["bar", "line"],
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

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8 * scale)
    except OSError:
        font = ImageFont.load_default()

    start_time = points[0][0] if points else None
    end_time = points[-1][0] if points else None
    duration = (end_time - start_time).total_seconds() if start_time is not None and end_time is not None else 0

    for offset in _grid_offsets(plot_height, _Y_GRID_SPACING * scale):
        ratio = offset / plot_height
        y = top + plot_height - offset
        draw.line([(left, y), (render_width - right, y)], fill=_GRID_COLOR)
        draw.text(
            (left - 6 * scale, y),
            str(round(scale_max * ratio, 2)),
            fill=_TEXT_COLOR,
            font=font,
            anchor="rm",
        )

    if start_time is not None:
        for offset in _grid_offsets(plot_width, _X_GRID_SPACING * scale):
            ratio = offset / plot_width
            x = left + offset
            tick_time = start_time + timedelta(seconds=duration * ratio)
            draw.line([(x, top), (x, top + plot_height)], fill=_GRID_COLOR)
            draw.text(
                (x, top + plot_height + 4 * scale),
                tick_time.strftime("%H:%M:%S"),
                fill=_TEXT_COLOR,
                font=font,
                anchor="ma",
            )

    draw.line(
        [(left, top), (left, top + plot_height)],
        fill=_AXIS_COLOR,
    )
    draw.line(
        [(left, top + plot_height), (render_width - right, top + plot_height)],
        fill=_AXIS_COLOR,
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
    count = len(points)
    coordinates = []
    for timestamp, value in points:
        x_ratio = (timestamp - start_time).total_seconds() / duration if duration > 0 else 0.5
        x = left + x_ratio * plot_width
        bar_h = (value / scale_max) * plot_height
        y = top + plot_height - bar_h
        coordinates.append((x, y, value))

    if chart_type == "line":
        if len(coordinates) == 1:
            x, y, value = coordinates[0]
            color_name = _bar_color_name(value, thresholds, value_colors)
            color = _BAR_COLOR_HEX[color_name]
            radius = 2 * scale
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
        for previous, current in zip(coordinates, coordinates[1:]):
            color_name = _bar_color_name(current[2], thresholds, value_colors)
            draw.line([previous[:2], current[:2]], fill=_BAR_COLOR_HEX[color_name], width=2 * scale)
        for x, y, value in coordinates:
            if not _exceeds_threshold(value, thresholds):
                continue
            color_name = _bar_color_name(value, thresholds, value_colors)
            radius = 3 * scale
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=_BAR_COLOR_HEX[color_name],
            )
        img.save(output_path, "PNG")
        return

    bar_width = max(1, plot_width / count - 1)
    for x, y, value in coordinates:
        x = max(left + bar_width / 2, min(render_width - right - bar_width / 2, x))
        x -= bar_width / 2
        bar_h = top + plot_height - y
        color_name = _bar_color_name(value, thresholds, value_colors)
        hex_color = _BAR_COLOR_HEX[color_name]
        draw.rectangle(
            [x, y, x + bar_width, y + bar_h],
            fill=hex_color,
        )
    for x, y, value in coordinates:
        if not _exceeds_threshold(value, thresholds):
            continue
        x = max(left + bar_width / 2, min(render_width - right - bar_width / 2, x))
        color_name = _bar_color_name(value, thresholds, value_colors)
        radius = 3 * scale
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=_BAR_COLOR_HEX[color_name],
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
    width: int = DEFAULT_CHART_WIDTH,
    height: int = DEFAULT_CHART_HEIGHT,
    image_format: Literal["png", "svg"] = "png",
    chart_type: Literal["bar", "line"] = "bar",
) -> str:
    """Render a time-series chart and return its relative path.

    By default the chart is saved as a PNG image. Pass ``image_format="svg"``
    to keep the SVG source file instead.
    """
    if image_format not in ("png", "svg"):
        raise ValueError(f"unsupported image format: {image_format!r}")
    if chart_type not in ("bar", "line"):
        raise ValueError(f"unsupported chart type: {chart_type!r}")
    if width <= _LEFT + _RIGHT or height <= _TOP + _BOTTOM:
        raise ValueError("chart dimensions are too small for axes and labels")
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
        _draw_png(output_path, points, width, height, parsed_thresholds, parsed_value_colors, chart_type)
        return relative_path.as_posix()

    left, right, top, bottom = _LEFT, _RIGHT, _TOP, _BOTTOM
    plot_width = width - left - right
    plot_height = height - top - bottom
    values = [value for _, value in points]
    y_max = max(values, default=0.0)
    scale_max = y_max if y_max > 0 else 1.0

    marks = ""
    if points:
        start_time = points[0][0]
        end_time = points[-1][0]
        duration = (end_time - start_time).total_seconds()
        coordinates = []
        for timestamp, value in points:
            x_ratio = (timestamp - start_time).total_seconds() / duration if duration > 0 else 0.5
            x = left + x_ratio * plot_width
            bar_h = (value / scale_max) * plot_height
            y = top + plot_height - bar_h
            coordinates.append((x, y, value))
        if chart_type == "line":
            if len(coordinates) == 1:
                x, y, value = coordinates[0]
                marks = f'<circle class="{_line_class(value, parsed_thresholds, parsed_value_colors)}" '
                marks += f'cx="{x:.2f}" cy="{y:.2f}" r="2"/>'
            else:
                for previous, current in zip(coordinates, coordinates[1:]):
                    line_class = _line_class(current[2], parsed_thresholds, parsed_value_colors)
                    marks += (
                        f'<line class="{line_class}" x1="{previous[0]:.2f}" y1="{previous[1]:.2f}" '
                        f'x2="{current[0]:.2f}" y2="{current[1]:.2f}"/>'
                    )
            for x, y, value in coordinates:
                if not _exceeds_threshold(value, parsed_thresholds):
                    continue
                color_name = _bar_color_name(value, parsed_thresholds, parsed_value_colors)
                marks += (
                    f'<circle class="metric-threshold-point metric-threshold-point-{color_name}" '
                    f'cx="{x:.2f}" cy="{y:.2f}" r="3"/>'
                )
        else:
            count = len(points)
            bar_width = max(1, plot_width / count - 1)
            for x, y, value in coordinates:
                x = max(left + bar_width / 2, min(width - right - bar_width / 2, x))
                x -= bar_width / 2
                bar_h = top + plot_height - y
                bar_class = _bar_class(value, parsed_thresholds, parsed_value_colors)
                marks += (
                    f'<rect class="{bar_class}" x="{x:.2f}" y="{y:.2f}" '
                    f'width="{bar_width:.2f}" height="{bar_h:.2f}"/>'
                )
            for x, y, value in coordinates:
                if not _exceeds_threshold(value, parsed_thresholds):
                    continue
                x = max(left + bar_width / 2, min(width - right - bar_width / 2, x))
                color_name = _bar_color_name(value, parsed_thresholds, parsed_value_colors)
                marks += (
                    f'<circle class="metric-threshold-point metric-threshold-point-{color_name}" '
                    f'cx="{x:.2f}" cy="{y:.2f}" r="3"/>'
                )
    else:
        marks = (
            f'<text x="{left + plot_width / 2:.2f}" y="{top + plot_height / 2:.2f}" '
            'text-anchor="middle">No data available</text>'
        )

    grid = ""
    start_time = points[0][0] if points else None
    end_time = points[-1][0] if points else None
    duration = (end_time - start_time).total_seconds() if start_time is not None and end_time is not None else 0
    for offset in _grid_offsets(plot_height, _Y_GRID_SPACING):
        ratio = offset / plot_height
        y = top + plot_height - offset
        grid += f'<line class="metric-grid" x1="{left}" y1="{y:.2f}" ' f'x2="{width - right}" y2="{y:.2f}"/>'
        grid += (
            f'<text class="metric-y-label" x="{left - 6}" y="{y + 3:.2f}" '
            f'text-anchor="end">{round(scale_max * ratio, 2)}</text>'
        )

    if start_time is not None:
        for offset in _grid_offsets(plot_width, _X_GRID_SPACING):
            ratio = offset / plot_width
            x = left + offset
            tick_time = start_time + timedelta(seconds=duration * ratio)
            grid += f'<line class="metric-grid" x1="{x:.2f}" y1="{top}" ' f'x2="{x:.2f}" y2="{top + plot_height}"/>'
            grid += (
                f'<text class="metric-x-label" x="{x:.2f}" y="{top + plot_height + 12}" '
                f'text-anchor="middle">{tick_time.strftime("%H:%M:%S")}</text>'
            )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(metric)} {chart_type} chart">'
        "<style>"
        "text{font:9px sans-serif;fill:#57606a}"
        f".metric-bar{{fill:{_BAR_COLOR_HEX[None]}}}"
        f".metric-bar-green{{fill:{_BAR_COLOR_HEX['green']}}}"
        f".metric-bar-yellow{{fill:{_BAR_COLOR_HEX['yellow']}}}"
        f".metric-bar-red{{fill:{_BAR_COLOR_HEX['red']}}}"
        f".metric-bar-blue{{fill:{_BAR_COLOR_HEX['blue']}}}"
        f".metric-bar-gray{{fill:{_BAR_COLOR_HEX['gray']}}}"
        f".metric-line{{fill:{_BAR_COLOR_HEX[None]};stroke:{_BAR_COLOR_HEX[None]};stroke-width:2}}"
        f".metric-line-green{{fill:{_BAR_COLOR_HEX['green']};stroke:{_BAR_COLOR_HEX['green']}}}"
        f".metric-line-yellow{{fill:{_BAR_COLOR_HEX['yellow']};stroke:{_BAR_COLOR_HEX['yellow']}}}"
        f".metric-line-red{{fill:{_BAR_COLOR_HEX['red']};stroke:{_BAR_COLOR_HEX['red']}}}"
        f".metric-line-blue{{fill:{_BAR_COLOR_HEX['blue']};stroke:{_BAR_COLOR_HEX['blue']}}}"
        f".metric-line-gray{{fill:{_BAR_COLOR_HEX['gray']};stroke:{_BAR_COLOR_HEX['gray']}}}"
        f".metric-threshold-point{{fill:{_BAR_COLOR_HEX[None]}}}"
        f".metric-threshold-point-green{{fill:{_BAR_COLOR_HEX['green']}}}"
        f".metric-threshold-point-yellow{{fill:{_BAR_COLOR_HEX['yellow']}}}"
        f".metric-threshold-point-red{{fill:{_BAR_COLOR_HEX['red']}}}"
        f".metric-threshold-point-blue{{fill:{_BAR_COLOR_HEX['blue']}}}"
        f".metric-threshold-point-gray{{fill:{_BAR_COLOR_HEX['gray']}}}"
        ".metric-grid{stroke:#d0d7de;stroke-width:1}"
        "</style>"
        f"{grid}"
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#8c959f"/>'
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width - right}" '
        f'y2="{top + plot_height}" stroke="#8c959f"/>'
        f"{marks}</svg>"
    )
    output_path.write_text(svg, encoding="utf-8")
    return relative_path.as_posix()
