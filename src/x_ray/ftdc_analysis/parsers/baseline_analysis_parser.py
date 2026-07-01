"""Parser for FTDC baseline analysis results."""

import base64
from html import escape
from pathlib import Path
from typing import Any, Optional

from x_ray.ftdc_analysis.parsers.base_parser import BaseParser

_CHART_WIDTH = 480
_CHART_HEIGHT = 50


def _chart_img(chart_path: str, alt: str, output_folder: Optional[str] = None) -> str:
    if chart_path.endswith(".png"):
        src = chart_path
        if output_folder is not None:
            resolved = Path(output_folder) / chart_path
            if resolved.is_file():
                data = resolved.read_bytes()
                b64 = base64.b64encode(data).decode("ascii")
                src = f"data:image/png;base64,{b64}"
        return (
            f'<img src="{src}" width="{_CHART_WIDTH}" height="{_CHART_HEIGHT}"'
            f' alt="{escape(alt)}">'
        )
    return f"![{alt}]({chart_path})"


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
                        "Me",
                        "State",
                    ],
                    "rows": [
                        [
                            item["member"],
                            item["myself"],
                            _chart_img(item["chart"], f'{item["metric"]} bar chart', output_folder),
                        ]
                        for item in data
                    ],
                }
            ]

        rows = [
            [
                f'{item["metric"]} ({item["unit"]})',
                round(item["peak"], 2),
                round(item["average"], 2),
                _chart_img(item["chart"], f'{item["metric"]} bar chart', output_folder),
            ]
            for item in data
        ]
        return [
            {
                "type": "table",
                "caption": kwargs.get("caption", "Baseline Analysis"),
                "header": [
                    {"text": "Metric", "align": "left"},
                    "Peak",
                    "Average",
                    "Chart",
                ],
                "rows": rows,
            }
        ]
