from datetime import datetime, timezone

from x_ray.__main__ import setup_parser


def test_ftdc_accepts_optional_utc_range():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data", "2026-06-17T10:00:00Z", "2026-06-17T11:00:00+00:00"])

    assert args.start_time == datetime(2026, 6, 17, 10, tzinfo=timezone.utc)
    assert args.end_time == datetime(2026, 6, 17, 11, tzinfo=timezone.utc)


def test_ftdc_range_defaults_to_none():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data"])

    assert args.start_time is None
    assert args.end_time is None
    assert args.rate == 0.1


def test_ftdc_accepts_sample_rate():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data", "-r", "0.25"])

    assert args.rate == 0.25
