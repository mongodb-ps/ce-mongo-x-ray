from x_ray.ftdc_analysis.parsers.overview_parser import OverviewParser


def test_parse_overview_table():
    parsed = OverviewParser().parse([{"metric": "CPU user", "peak": 12.345, "average": 4.567, "unit": "%"}])

    assert parsed == [
        {
            "type": "table",
            "caption": "Overview",
            "header": [
                {"text": "Metric", "align": "left"},
                "Peak",
                "Average",
                "Unit",
            ],
            "rows": [["CPU user", 12.35, 4.57, "%"]],
        }
    ]
