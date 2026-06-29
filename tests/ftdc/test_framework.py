from datetime import datetime, timezone
from pathlib import Path

from x_ray.ftdc_analysis.framework import Framework


def test_empty_checkset_writes_reports(tmp_path, monkeypatch):
    monkeypatch.setattr("x_ray.ftdc_analysis.framework.env", "development")
    input_file = tmp_path / "metrics"
    input_file.write_bytes(b"")
    output_folder = tmp_path / "output"
    config = {
        "ftdcsets": {"default": {"items": []}},
        "item_config": {},
        "template": "ftdc/full.html",
    }

    framework = Framework(str(input_file), config)
    framework.run_ftdc_analysis("default", output_folder=str(output_folder))
    framework.output_results(output_folder=str(output_folder), fmt="html")

    report = Path(output_folder, "report.md")
    assert report.is_file()
    assert "No FTDC analysis items are configured" in report.read_text(encoding="utf-8")
    assert Path(output_folder, "report.html").is_file()


def test_input_files_use_filename_end_times(tmp_path):
    names = [
        "metrics.2026-06-17T10-00-00Z-00000",
        "metrics.2026-06-17T11-00-00Z-00000",
        "metrics.2026-06-17T12-00-00Z-00000",
    ]
    for name in names:
        (tmp_path / name).touch()
    config = {"ftdcsets": {"default": {"items": []}}}
    framework = Framework(
        str(tmp_path),
        config,
        start_time=datetime(2026, 6, 17, 10, 30, tzinfo=timezone.utc),
        end_time=datetime(2026, 6, 17, 11, 30, tzinfo=timezone.utc),
    )

    assert [path.name for path in framework._input_files()] == names[1:]
