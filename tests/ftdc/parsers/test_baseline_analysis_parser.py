import base64
from pathlib import Path

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


def test_chart_img_embeds_png_as_base64_when_output_folder_provided(tmp_path):
    png = tmp_path / "charts" / "test.png"
    png.parent.mkdir()
    png.write_bytes(bytes(range(256)))

    result = _chart_img("charts/test.png", "Test alt", output_folder=str(tmp_path))

    expected_data = base64.b64encode(bytes(range(256))).decode("ascii")
    assert result == (
        f'<img src="data:image/png;base64,{expected_data}"'
        ' width="480" height="50" alt="Test alt">'
    )


def test_chart_img_falls_back_to_relative_path_when_png_missing(tmp_path):
    result = _chart_img("charts/missing.png", "Missing", output_folder=str(tmp_path))

    assert result == (
        '<img src="charts/missing.png" width="480" height="50" alt="Missing">'
    )


def test_chart_img_uses_relative_path_without_output_folder():
    result = _chart_img("charts/foo.png", "No folder")

    assert result == (
        '<img src="charts/foo.png" width="480" height="50" alt="No folder">'
    )


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
        f'<img src="data:image/png;base64,{expected_data}"'
        ' width="480" height="50" alt="CPU user bar chart">'
    )
    assert parsed[0]["rows"][0][3] == expected_img
