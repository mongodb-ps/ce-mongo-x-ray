from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import pytest

from x_ray.ftdc_analysis.charts import write_bar_chart


def test_bar_chart_uses_threshold_colors(tmp_path):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    points = [
        (start, 9.0),
        (start + timedelta(seconds=1), 10.0),
        (start + timedelta(seconds=2), 15.0),
        (start + timedelta(seconds=3), 20.0),
        (start + timedelta(seconds=4), 21.0),
    ]

    chart = tmp_path / write_bar_chart(tmp_path, "Threshold test", points, thresholds=(10, 20))
    bars = ElementTree.parse(chart).getroot().findall(".//{http://www.w3.org/2000/svg}rect")

    assert [bar.attrib["class"] for bar in bars] == [
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-green",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-yellow",
        "metric-bar metric-bar-red",
    ]


def test_bar_chart_keeps_current_color_without_thresholds(tmp_path):
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)

    chart = tmp_path / write_bar_chart(tmp_path, "Default color test", [(timestamp, 10.0)])
    bar = ElementTree.parse(chart).getroot().find(".//{http://www.w3.org/2000/svg}rect")

    assert bar is not None
    assert bar.attrib["class"] == "metric-bar"
    assert chart.name == "ftdc-baseline-analysis-default-color-test.svg"


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
