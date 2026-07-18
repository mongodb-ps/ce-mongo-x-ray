from datetime import datetime, timezone
from pathlib import Path

from x_ray.gmd_analysis.framework import Framework as GMDFramework
from x_ray.healthcheck.framework import Framework as HealthCheckFramework
from x_ray.log_analysis.framework import Framework as LogFramework


def _fake_pdf_conversion(html_file, pdf_file):
    assert Path(html_file).is_file()
    Path(pdf_file).write_bytes(b"%PDF-1.7")


def _assert_all_report_formats(output_folder):
    assert (output_folder / "report.md").is_file()
    html_text = (output_folder / "report.html").read_text(encoding="utf-8")
    assert "@page" in html_text
    assert "size: landscape" in html_text
    assert (output_folder / "report.pdf").read_bytes().startswith(b"%PDF")


def test_healthcheck_pdf_format_writes_all_reports(tmp_path, monkeypatch):
    output_folder = tmp_path / "healthcheck"
    output_folder.mkdir()
    monkeypatch.setattr("x_ray.healthcheck.framework.env", "development")
    monkeypatch.setattr("x_ray.healthcheck.framework.html_to_pdf", _fake_pdf_conversion)
    framework = HealthCheckFramework(
        {
            "checksets": {"default": {"items": []}},
            "item_config": {},
            "template": "healthcheck/full.html",
        }
    )

    framework.output_results(output_folder=f"{output_folder}/", fmt="pdf")

    _assert_all_report_formats(output_folder)


def test_log_pdf_format_writes_all_reports(tmp_path, monkeypatch):
    output_folder = tmp_path / "log"
    monkeypatch.setattr("x_ray.log_analysis.framework.env", "development")
    monkeypatch.setattr("x_ray.log_analysis.framework.html_to_pdf", _fake_pdf_conversion)
    framework = LogFramework(
        "/var/log/mongodb/mongod.log",
        {
            "logsets": {"default": {"items": []}},
            "item_config": {},
            "template": "log/full.html",
        },
    )
    framework._log_start = datetime(2026, 7, 3, tzinfo=timezone.utc)
    framework._log_end = datetime(2026, 7, 3, 1, tzinfo=timezone.utc)

    framework.output_results(output_folder=f"{output_folder}/", fmt="pdf")

    _assert_all_report_formats(output_folder)


def test_gmd_pdf_format_writes_all_reports(tmp_path, monkeypatch):
    output_folder = tmp_path / "gmd"
    monkeypatch.setattr("x_ray.gmd_analysis.framework.env", "development")
    monkeypatch.setattr("x_ray.gmd_analysis.framework.html_to_pdf", _fake_pdf_conversion)
    framework = GMDFramework(
        "/tmp/getMongoData.json",
        {
            "gmdsets": {"default": {"items": []}},
            "item_config": {},
            "template": "gmd/full.html",
        },
    )

    framework.output_results(output_folder=f"{output_folder}/", fmt="pdf")

    _assert_all_report_formats(output_folder)
