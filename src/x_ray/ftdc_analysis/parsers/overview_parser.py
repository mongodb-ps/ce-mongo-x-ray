"""Parser for FTDC overview results."""

from typing import Any

from x_ray.ftdc_analysis.parsers.base_parser import BaseParser


class OverviewParser(BaseParser):
    """Convert overview metric summaries to a report table."""

    def parse(self, data: Any, **kwargs) -> list:
        rows = [
            [
                f'{item["metric"]} ({item["unit"]})',
                round(item["peak"], 2),
                round(item["average"], 2),
                f'![{item["metric"]} line chart]({item["chart"]})',
            ]
            for item in data
        ]
        return [
            {
                "type": "table",
                "caption": "Overview",
                "header": [
                    {"text": "Metric", "align": "left"},
                    "Peak",
                    "Average",
                    "Chart",
                ],
                "rows": rows,
            }
        ]
