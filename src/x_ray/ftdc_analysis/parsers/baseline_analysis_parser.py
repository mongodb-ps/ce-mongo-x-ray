"""Parser for FTDC baseline analysis results."""

from html import escape
from typing import Any

from x_ray.ftdc_analysis.parsers.base_parser import BaseParser

_CHART_WIDTH = 480
_CHART_HEIGHT = 50


def _chart_img(chart_path: str, alt: str) -> str:
    if chart_path.endswith(".png"):
        return (
            f'<img src="{chart_path}" width="{_CHART_WIDTH}" height="{_CHART_HEIGHT}"'
            f' alt="{escape(alt)}">'
        )
    return f"![{alt}]({chart_path})"


class BaselineAnalysisParser(BaseParser):
    """Convert baseline analysis metric summaries to a report table."""

    def parse(self, data: Any, **kwargs) -> list:
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
                            _chart_img(item["chart"], f'{item["metric"]} bar chart'),
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
                _chart_img(item["chart"], f'{item["metric"]} bar chart'),
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
