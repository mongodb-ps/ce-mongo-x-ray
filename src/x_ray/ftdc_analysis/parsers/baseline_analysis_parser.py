"""Parser for FTDC baseline analysis results."""

import base64
from html import escape
from pathlib import Path
from typing import Any, Optional

from x_ray.ftdc_analysis.charts import DEFAULT_CHART_HEIGHT, DEFAULT_CHART_WIDTH
from x_ray.ftdc_analysis.parsers.base_parser import BaseParser


def _chart_img(
    chart_path: str,
    alt: str,
    output_folder: Optional[str] = None,
    width: int = DEFAULT_CHART_WIDTH,
    height: int = DEFAULT_CHART_HEIGHT,
) -> str:
    if chart_path.endswith(".png"):
        src = chart_path
        if output_folder is not None:
            resolved = Path(output_folder) / chart_path
            if resolved.is_file():
                data = resolved.read_bytes()
                b64 = base64.b64encode(data).decode("ascii")
                src = f"data:image/png;base64,{b64}"
        return f'<img src="{src}" width="{width}" height="{height}"' f' alt="{escape(alt)}">'
    return f"![{alt}]({chart_path})"


def _thresholds(item: dict) -> str:
    warning = item.get("warning_threshold")
    critical = item.get("critical_threshold")
    if warning is None and critical is None:
        return "\u2014"
    if critical is None:
        return str(round(warning, 2))
    return f"{round(warning, 2)} / {round(critical, 2)}"


class BaselineAnalysisParser(BaseParser):
    """Convert baseline analysis metric summaries to a report table."""

    def parse(self, data: Any, **kwargs) -> list:
        output_folder = kwargs.get("output_folder")
        if kwargs.get("member_state"):
            return [
                {
                    "type": "table",
                    "caption": kwargs.get("caption", "Member State"),
                    "header": [
                        {"text": "Member", "align": "left"},
                        {"text": "Me", "sortable": False},
                        {"text": "State", "sortable": False},
                    ],
                    "rows": [
                        [
                            item["member"],
                            item["myself"],
                            _chart_img(
                                item["chart"],
                                f'{item["metric"]} {item.get("chart_type", "bar")} chart',
                                output_folder,
                                item.get("chart_width", DEFAULT_CHART_WIDTH),
                                item.get("chart_height", DEFAULT_CHART_HEIGHT),
                            ),
                        ]
                        for item in data
                    ],
                }
            ]

        show_thresholds = kwargs.get("show_thresholds", True)
        rows = []
        for item in data:
            row = [
                f'{item["metric"]} ({item["unit"]})',
                f'{round(item["peak"], 2)} / {round(item["average"], 2)}',
            ]
            if show_thresholds:
                row.append(_thresholds(item))
            row.append(
                _chart_img(
                    item["chart"],
                    f'{item["metric"]} {item.get("chart_type", "bar")} chart',
                    output_folder,
                    item.get("chart_width", DEFAULT_CHART_WIDTH),
                    item.get("chart_height", DEFAULT_CHART_HEIGHT),
                )
            )
            rows.append(row)
        header = [
            {"text": "Metric", "align": "left"},
            "Peak / Average",
        ]
        if show_thresholds:
            header.append("Warning / Critical Threshold")
        header.append({"text": "Chart", "sortable": False})
        return [
            {
                "type": "table",
                "caption": kwargs.get("caption", "Baseline Analysis"),
                "header": header,
                "rows": rows,
            }
        ]
