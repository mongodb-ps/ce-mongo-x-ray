from x_ray.ftdc_analysis.parsers.baseline_analysis_parser import BaselineAnalysisParser


def test_parse_baseline_analysis_table():
    parsed = BaselineAnalysisParser().parse(
        [
            {
                "metric": "CPU user",
                "peak": 12.345,
                "average": 4.567,
                "unit": "%",
                "chart": "charts/ftdc-baseline-analysis-cpu-user.svg",
            }
        ]
    )

    assert parsed == [
        {
            "type": "table",
            "caption": "Baseline Analysis",
            "header": [
                {"text": "Metric", "align": "left"},
                "Peak",
                "Average",
                "Chart",
            ],
            "rows": [
                [
                    "CPU user (%)",
                    12.35,
                    4.57,
                    "![CPU user bar chart](charts/ftdc-baseline-analysis-cpu-user.svg)",
                ]
            ],
        }
    ]


def test_parse_member_state_table_without_peak_and_average():
    parsed = BaselineAnalysisParser().parse(
        [
            {
                "member": "0",
                "metric": "Replica set member state (0)",
                "myself": "Yes",
                "chart": "charts/ftdc-baseline-analysis-rs-member-state-0.svg",
            }
        ],
        member_state=True,
    )

    assert parsed == [
        {
            "type": "table",
            "caption": "Member State",
            "header": [
                {"text": "Member", "align": "left"},
                "Me",
                "State",
            ],
            "rows": [
                [
                    "0",
                    "Yes",
                    "![Replica set member state (0) bar chart](charts/ftdc-baseline-analysis-rs-member-state-0.svg)",
                ]
            ],
        }
    ]
