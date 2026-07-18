from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import pytest

from x_ray.ftdc_analysis.charts import write_bar_chart


def test_bar_chart_defaults_to_png(tmp_path):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chart = tmp_path / write_bar_chart(tmp_path, "PNG default test", [(timestamp, 10.0)])
    assert chart.suffix == ".png"
    assert chart.exists()
    header = chart.read_bytes()[:8]
    assert header == b"\x89PNG\r\n\x1a\n"


def test_chart_defaults_to_150_pixel_height(tmp_path):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    chart = tmp_path / write_bar_chart(tmp_path, "Height test", [(timestamp, 10.0)], image_format="svg")
    root = ElementTree.parse(chart).getroot()

    assert root.attrib["height"] == "150"
    assert root.attrib["viewBox"] == "0 0 500 150"


def test_chart_uses_high_contrast_palette(tmp_path):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    chart = tmp_path / write_bar_chart(
        tmp_path,
        "Palette test",
        [(timestamp, 10.0)],
        image_format="svg",
    )
    style = ElementTree.parse(chart).getroot().find("{http://www.w3.org/2000/svg}style")

    assert style is not None
    assert all(color in style.text for color in ("#0072b2", "#009e73", "#e69f00", "#cc3311", "#667085"))


def test_line_chart_draws_colored_segments(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 5.0),
        (start + timedelta(seconds=1), 15.0),
        (start + timedelta(seconds=2), 25.0),
    ]

    chart = tmp_path / write_bar_chart(
        tmp_path,
        "Line test",
        points,
        thresholds=(10, 20),
        image_format="svg",
        chart_type="line",
    )
    root = ElementTree.parse(chart).getroot()
    lines = root.findall(".//{http://www.w3.org/2000/svg}line")
    data_lines = [line for line in lines if line.attrib.get("class", "").startswith("metric-line")]
    threshold_points = [
        point
        for point in root.findall(".//{http://www.w3.org/2000/svg}circle")
        if point.attrib.get("class", "").startswith("metric-threshold-point")
    ]

    assert [line.attrib["class"] for line in data_lines] == [
        "metric-line metric-line-yellow",
        "metric-line metric-line-red",
    ]
    assert [(point.attrib["class"], point.attrib["cx"], point.attrib["r"]) for point in threshold_points] == [
        ("metric-threshold-point metric-threshold-point-yellow", "262.00", "3"),
        ("metric-threshold-point metric-threshold-point-red", "472.00", "3"),
    ]
    assert root.attrib["aria-label"] == "Line test line chart"


def test_chart_spaces_grid_lines_by_pixels(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 0.0),
        (start + timedelta(seconds=4), 20.0),
    ]

    chart = tmp_path / write_bar_chart(tmp_path, "Grid test", points, image_format="svg")
    root = ElementTree.parse(chart).getroot()
    grid_lines = root.findall(".//{http://www.w3.org/2000/svg}line[@class='metric-grid']")
    horizontal = [line for line in grid_lines if line.attrib["y1"] == line.attrib["y2"]]
    vertical = [line for line in grid_lines if line.attrib["x1"] == line.attrib["x2"]]
    x_labels = root.findall(".//{http://www.w3.org/2000/svg}text[@class='metric-x-label']")
    y_labels = root.findall(".//{http://www.w3.org/2000/svg}text[@class='metric-y-label']")

    assert len(horizontal) == 3
    assert len(vertical) == 5
    assert [float(line.attrib["x1"]) for line in vertical] == [52, 152, 252, 352, 452]
    assert [float(line.attrib["y1"]) for line in horizontal] == [126, 76, 26]
    assert [label.text for label in x_labels] == [
        "00:00:00",
        "00:00:00",
        "00:00:01",
        "00:00:02",
        "00:00:03",
    ]
    assert [label.text for label in y_labels] == ["0.0", "8.47", "16.95"]


def test_chart_supports_custom_dimensions(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [(start, 0.0), (start + timedelta(seconds=6), 20.0)]

    chart = tmp_path / write_bar_chart(
        tmp_path,
        "Custom size",
        points,
        image_format="svg",
        width=680,
        height=232,
    )
    root = ElementTree.parse(chart).getroot()
    grid_lines = root.findall(".//{http://www.w3.org/2000/svg}line[@class='metric-grid']")
    horizontal = [line for line in grid_lines if line.attrib["y1"] == line.attrib["y2"]]
    vertical = [line for line in grid_lines if line.attrib["x1"] == line.attrib["x2"]]

    assert root.attrib["width"] == "680"
    assert root.attrib["height"] == "232"
    assert len(horizontal) == 5
    assert len(vertical) == 7


def test_bar_chart_uses_threshold_colors(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 9.0),
        (start + timedelta(seconds=1), 10.0),
        (start + timedelta(seconds=2), 15.0),
        (start + timedelta(seconds=3), 20.0),
        (start + timedelta(seconds=4), 21.0),
    ]

    chart = tmp_path / write_bar_chart(tmp_path, "Threshold test", points, thresholds=(10, 20), image_format="svg")
    bars = ElementTree.parse(chart).getroot().findall(".//{http://www.w3.org/2000/svg}rect")

    assert [bar.attrib["class"] for bar in bars] == [
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-red",
    ]
    threshold_points = ElementTree.parse(chart).getroot().findall(".//{http://www.w3.org/2000/svg}circle")
    assert [
        (point.attrib["class"], point.attrib["cx"], point.attrib["cy"], point.attrib["r"]) for point in threshold_points
    ] == [
        ("metric-threshold-point metric-threshold-point-yellow", "262.00", "41.71", "3"),
        ("metric-threshold-point metric-threshold-point-yellow", "367.00", "13.62", "3"),
        ("metric-threshold-point metric-threshold-point-red", "430.50", "8.00", "3"),
    ]


def test_bar_chart_keeps_current_color_without_thresholds(tmp_path):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    chart = tmp_path / write_bar_chart(tmp_path, "Default color test", [(timestamp, 10.0)], image_format="svg")
    bar = ElementTree.parse(chart).getroot().find(".//{http://www.w3.org/2000/svg}rect")

    assert bar is not None
    assert bar.attrib["class"] == "metric-bar"
    assert chart.name == "ftdc-baseline-analysis-default-color-test.svg"


def test_bar_chart_uses_value_colors(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 1.0),
        (start + timedelta(seconds=1), 2.0),
        (start + timedelta(seconds=2), 7.0),
        (start + timedelta(seconds=3), 3.0),
    ]

    chart = tmp_path / write_bar_chart(
        tmp_path,
        "Categorical test",
        points,
        value_colors={1: "green", 2: "yellow", 7: "blue", 3: "gray"},
        image_format="svg",
    )
    bars = ElementTree.parse(chart).getroot().findall(".//{http://www.w3.org/2000/svg}rect")

    assert [bar.attrib["class"] for bar in bars] == [
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-blue",
        "metric-bar metric-bar-gray",
    ]


def test_bar_chart_rejects_invalid_image_format(tmp_path):
    with pytest.raises(ValueError, match="unsupported image format"):
        write_bar_chart(tmp_path, "Bad format", [], image_format="jpg")


def test_chart_rejects_invalid_chart_type(tmp_path):
    with pytest.raises(ValueError, match="unsupported chart type"):
        write_bar_chart(tmp_path, "Bad chart", [], chart_type="pie")


@pytest.mark.parametrize(("width", "height"), [(80, 150), (450, 32)])
def test_chart_rejects_dimensions_too_small_for_axes(tmp_path, width, height):
    with pytest.raises(ValueError, match="chart dimensions"):
        write_bar_chart(tmp_path, "Bad dimensions", [], width=width, height=height)


@pytest.mark.parametrize(
    "thresholds",
    [
        [10],
        [10, 20, 30],
        [20, 10],
        [10, 10],
        [10, float("inf")],
        ["low", "high"],
        True,
    ],
)
def test_bar_chart_rejects_invalid_thresholds(tmp_path, thresholds):
    with pytest.raises(ValueError, match="chart thresholds"):
        write_bar_chart(tmp_path, "Invalid thresholds", [], thresholds=thresholds)


@pytest.mark.parametrize(
    "value_colors",
    [
        [(1, "green")],
        {True: "green"},
        {float("inf"): "green"},
        {"primary": "green"},
        {1: "purple"},
    ],
)
def test_bar_chart_rejects_invalid_value_colors(tmp_path, value_colors):
    with pytest.raises(ValueError, match="chart value colors"):
        write_bar_chart(tmp_path, "Invalid value colors", [], value_colors=value_colors)


def test_bar_chart_rejects_thresholds_with_value_colors(tmp_path):
    with pytest.raises(ValueError, match="cannot be combined"):
        write_bar_chart(
            tmp_path,
            "Ambiguous colors",
            [],
            thresholds=(10, 20),
            value_colors={1: "green"},
        )
