from datetime import datetime, timezone
from pathlib import Path
import tempfile

import pytest

from x_ray.__main__ import _discover_paths, setup_parser


def test_ftdc_accepts_optional_utc_range():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data", "2026-06-17T10:00:00Z", "2026-06-17T11:00:00+00:00"])

    assert args.start_time == datetime(2026, 6, 17, 10, tzinfo=timezone.utc)
    assert args.end_time == datetime(2026, 6, 17, 11, tzinfo=timezone.utc)


def test_ftdc_range_and_sample_rate_default_to_none():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data"])

    assert args.start_time is None
    assert args.end_time is None
    assert args.rate is None


def test_ftdc_accepts_sample_rate():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data", "-r", "0.25"])

    assert args.rate == 0.25


def test_ftdc_accepts_pdf_format():
    args = setup_parser().parse_args(["ftdc", "/diagnostic.data", "-f", "pdf"])

    assert args.format == "pdf"


def test_log_accepts_discover_flag():
    args = setup_parser().parse_args(["log", "/tmp/logs", "--discover"])

    assert args.discover is True


def test_ftdc_accepts_discover_flag():
    args = setup_parser().parse_args(["ftdc", "/tmp/data", "--discover"])

    assert args.discover is True


def test_discover_defaults_to_false():
    args = setup_parser().parse_args(["log", "/tmp/logs"])
    assert args.discover is False

    args = setup_parser().parse_args(["ftdc", "/tmp/data"])
    assert args.discover is False


def test_discover_paths_finds_log_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / "deep" / "logs"
        nested.mkdir(parents=True)
        (nested / "mongod.log").touch()
        (root / "other" / "empty").mkdir(parents=True)

        result = _discover_paths(root, "*.log*")
        assert result == [nested]


def test_discover_paths_finds_ftdc_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / "a" / "b" / "diagnostic.data"
        nested.mkdir(parents=True)
        (nested / "metrics.2024-01-01T00-00-00Z").touch()
        (root / "other").mkdir()

        result = _discover_paths(root, "metrics.*")
        assert result == [nested]


def test_discover_paths_returns_empty_when_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "empty").mkdir()

        result = _discover_paths(root, "*.log*")
        assert result == []


def test_discover_paths_returns_all_matches():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        dir_a = root / "dir_a"
        dir_b = root / "deep" / "dir_b"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)
        (dir_a / "mongod.log").touch()
        (dir_b / "mongod.log").touch()

        result = _discover_paths(root, "*.log*")
        assert len(result) == 2
        assert dir_a in result
        assert dir_b in result
        # shallowest first
        assert result[0] == dir_a
        assert result[1] == dir_b


@pytest.mark.parametrize(
    "arguments",
    [
        ["healthcheck", "mongodb://localhost:27017", "-f", "pdf"],
        ["log", "/var/log/mongodb/mongod.log", "-f", "pdf"],
        ["gmd", "/tmp/getMongoData.json", "-f", "pdf"],
    ],
)
def test_other_modules_accept_pdf_format(arguments):
    args = setup_parser().parse_args(arguments)

    assert args.format == "pdf"
