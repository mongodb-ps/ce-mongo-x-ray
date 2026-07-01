"""Parser for FTDC baseline analysis results."""

from typing import Any

from x_ray.ftdc_analysis.parsers.base_parser import BaseParser


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
                        "Myself",
                        "State",
                    ],
                    "rows": [
                        [
                            item["member"],
                            item["myself"],
                            (
                                f'<span style="background-color: {item["color"]}; '
                                f'color: {item["text_color"]}; padding: 0.15em 0.45em; '
                                f'border-radius: 0.25em; font-weight: 600;">{item["state"]}</span>'
                            ),
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
                f'![{item["metric"]} bar chart]({item["chart"]})',
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
