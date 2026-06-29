from x_ray.ftdc_analysis.parsers.overview_parser import OverviewParser


def test_parse_overview_table():
    parsed = OverviewParser().parse(
        [
            {
                "metric": "CPU user",
                "peak": 12.345,
                "average": 4.567,
                "unit": "%",
                "chart": "charts/ftdc-overview-cpu-user.svg",
            }
        ]
    )

    assert parsed == [
        {
            "type": "table",
            "caption": "Overview",
            "header": [
                {"text": "Metric", "align": "left"},
                "Peak",
                "Average",
                "Chart",
            ],
            "rows": [
                [
                    "CPU user",
                    "12.35%",
                    "4.57%",
                    "![CPU user line chart](charts/ftdc-overview-cpu-user.svg)",
                ]
            ],
        }
    ]
