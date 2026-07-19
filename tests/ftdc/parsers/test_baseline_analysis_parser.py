import base64

from x_ray.ftdc_analysis.parsers.baseline_analysis_parser import BaselineAnalysisParser, _chart_img


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
                "Peak / Average",
                "Warning / Critical Threshold",
                {"text": "Chart", "sortable": False},
            ],
            "rows": [
                [
                    "CPU user (%)",
                    "12.35 / 4.57",
                    "\u2014",
                    "![CPU user bar chart](charts/ftdc-baseline-analysis-cpu-user.svg)",
                ]
            ],
        }
    ]


def test_parse_outputs_warning_and_critical_thresholds():
    parsed = BaselineAnalysisParser().parse(
        [
            {
                "metric": "CPU user",
                "peak": 97,
                "average": 42,
                "warning_threshold": 85,
                "critical_threshold": 95,
                "unit": "%",
                "chart": "charts/cpu-user.svg",
                "chart_type": "line",
            }
        ]
    )

    assert parsed[0]["rows"][0][2] == "85 / 95"


def test_parse_can_omit_threshold_column():
    parsed = BaselineAnalysisParser().parse(
        [
            {
                "metric": "Query operations",
                "peak": 20,
                "average": 15,
                "unit": "ops/s",
                "chart": "charts/query.svg",
                "chart_type": "line",
            }
        ],
        show_thresholds=False,
    )

    assert parsed[0]["header"] == [
        {"text": "Metric", "align": "left"},
        "Peak / Average",
        {"text": "Chart", "sortable": False},
    ]
    assert parsed[0]["rows"][0] == [
        "Query operations (ops/s)",
        "20 / 15",
        "![Query operations line chart](charts/query.svg)",
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
                {"text": "Me", "sortable": False},
                {"text": "State", "sortable": False},
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


def test_chart_img_embeds_png_as_base64_when_output_folder_provided(tmp_path):
    png = tmp_path / "charts" / "test.png"
    png.parent.mkdir()
    png.write_bytes(bytes(range(256)))

    result = _chart_img("charts/test.png", "Test alt", output_folder=str(tmp_path))

    expected_data = base64.b64encode(bytes(range(256))).decode("ascii")
    assert result == (f'<img src="data:image/png;base64,{expected_data}"' ' width="500" height="150" alt="Test alt">')


def test_chart_img_falls_back_to_relative_path_when_png_missing(tmp_path):
    result = _chart_img("charts/missing.png", "Missing", output_folder=str(tmp_path))

    assert result == ('<img src="charts/missing.png" width="500" height="150" alt="Missing">')


def test_chart_img_uses_relative_path_without_output_folder():
    result = _chart_img("charts/foo.png", "No folder")

    assert result == ('<img src="charts/foo.png" width="500" height="150" alt="No folder">')


def test_chart_img_uses_custom_dimensions():
    result = _chart_img("charts/member.png", "Member state", width=450, height=50)

    assert result == ('<img src="charts/member.png" width="450" height="50" alt="Member state">')


def test_chart_img_keeps_markdown_syntax_for_svg():
    result = _chart_img("charts/foo.svg", "SVG chart")

    assert result == "![SVG chart](charts/foo.svg)"


def test_parse_embeds_png_with_output_folder(tmp_path):
    png_data = bytes(range(256))
    png = tmp_path / "charts" / "ftdc-baseline-analysis-cpu-user.png"
    png.parent.mkdir()
    png.write_bytes(png_data)

    parsed = BaselineAnalysisParser().parse(
        [
            {
                "metric": "CPU user",
                "peak": 12.345,
                "average": 4.567,
                "unit": "%",
                "chart": "charts/ftdc-baseline-analysis-cpu-user.png",
            }
        ],
        output_folder=str(tmp_path),
    )

    expected_data = base64.b64encode(png_data).decode("ascii")
    expected_img = (
        f'<img src="data:image/png;base64,{expected_data}"' ' width="500" height="150" alt="CPU user bar chart">'
    )
    assert parsed[0]["rows"][0][3] == expected_img


def test_parse_uses_line_chart_alt_text():
    parsed = BaselineAnalysisParser().parse(
        [
            {
                "metric": "CPU user",
                "peak": 12.345,
                "average": 4.567,
                "unit": "%",
                "chart": "charts/ftdc-baseline-analysis-cpu-user.svg",
                "chart_type": "line",
            }
        ]
    )

    assert parsed[0]["rows"][0][3] == ("![CPU user line chart](charts/ftdc-baseline-analysis-cpu-user.svg)")
