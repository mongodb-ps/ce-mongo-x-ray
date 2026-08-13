"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

# Render the HTML log report (generated from misc/example.log) in a headless
# browser and verify the key UI elements exist. The outline, charts, copy
# buttons and syntax highlighting are all created dynamically by JavaScript,
# hence the need for Playwright.
import os
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("playwright")  # pylint: disable=wrong-import-position

from x_ray.log_analysis.framework import Framework as LogAnalysisFramework
from x_ray.utils import load_config

# Playwright fixtures are named after their injected value (browser, page,
# report_html), so parameters and fixture locals shadow the outer fixture
# function names, and the importorskip/lazy-playwright-import ordering is
# deliberate: the whole module is skipped when Chromium is missing — the
# idiomatic pytest patterns.
# pylint: disable=redefined-outer-name,wrong-import-position


def _log_samples():
    custom = os.environ.get("LOG_SAMPLE")
    if custom:
        # The integration-test target passes the mongos and mongod logs.
        return custom.split(os.pathsep)
    return ["example-rs.log", "example-sh.log", "example-mongos.log"]


EXAMPLE_LOGS = _log_samples()

EXPECTED_SECTIONS = [
    "Connection Rate",
    "Log Rate Analysis",
    "Slow Rate",
    "Client Metadata",
    "Top Slow Operations",
    "Slow Operations Chart",
    "Member State Trace",
    "Warning/Error/Fatal Logs",
    "Basic Info",
]


@pytest.fixture(scope="module", params=EXAMPLE_LOGS)
def report_html(request, tmp_path_factory):
    """Generate the HTML report from a sample log."""
    log_file = Path(request.param)
    if not log_file.is_absolute():
        log_file = Path(__file__).resolve().parent.parent.parent / "misc" / request.param
    assert log_file.is_file(), f"Missing sample log: {log_file}"
    output_dir = tmp_path_factory.mktemp("report")
    config = load_config(None)["log"]
    framework = LogAnalysisFramework(str(log_file), deepcopy(config))
    framework.run_logs_analysis("default", output_folder=f"{output_dir}/")
    framework.output_results(
        output_folder=f"{output_dir}/", fmt="html", open_browser=False
    )
    html_files = list(output_dir.rglob("report.html"))
    assert html_files, "report.html was not generated"
    return request.param, html_files[0]


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            pytest.skip(f"Chromium is not installed for Playwright: {exc}")
        yield browser
        browser.close()


@pytest.fixture(scope="module")
def page(browser, report_html):
    """Load the report and wait for the dynamically generated outline."""
    page = browser.new_page()
    page.goto(report_html[1].resolve().as_uri(), wait_until="load")
    # The outline nav is built from h2/h3 headings by JavaScript on load.
    page.wait_for_selector("#outline ul a")
    yield page
    page.close()


@pytest.mark.integration
def test_report_title(page):
    assert page.title() == "Log Analysis Report"


@pytest.mark.integration
def test_all_sections_rendered(page):
    headings = [h.inner_text() for h in page.locator("h2").all()]
    for section in EXPECTED_SECTIONS:
        assert section in headings, f"Missing report section: {section}"


@pytest.mark.integration
def test_outline_contains_links_to_all_sections(page):
    outline_links = page.locator("#outline a").all_inner_texts()
    for section in EXPECTED_SECTIONS:
        assert section in outline_links, f"Outline is missing a link to: {section}"


@pytest.mark.integration
def test_outline_toggle_buttons(page):
    assert page.locator("#collapse-outline").count() == 1
    assert page.locator("#expand-outline").count() == 1


@pytest.mark.integration
def test_markdown_tables_rendered(page):
    # Info is rendered as a list; the table-based items are WEF, TopSlow, ClientMetadata.
    assert page.locator("table").count() >= 3


@pytest.mark.integration
def test_wef_table_has_rows(page):
    table = page.locator("table", has_text="Known Risks")
    assert table.count() == 1
    assert table.locator("tbody tr").count() >= 1


@pytest.mark.integration
def test_top_slow_table_has_rows(page):
    table = page.locator("table", has_text="Plan Summary")
    assert table.count() == 1
    assert table.locator("tbody tr").count() >= 1


@pytest.mark.integration
def test_client_metadata_table_has_rows(page):
    table = page.locator("table", has_text="Client IPs")
    assert table.count() == 1
    assert table.locator("tbody tr").count() >= 1


@pytest.mark.integration
def test_reset_button_for_log_rate(page):
    assert page.locator("input#reset_LogRateItem").count() == 1


@pytest.mark.integration
def test_copy_table_buttons_added(page):
    # addTableCopyButtons() wraps every table with a copy button once the
    # highlight.js CDN script has loaded (it runs at the end of script.js).
    page.wait_for_selector(".table-copy-button")
    assert page.locator(".table-copy-button").count() >= 3


@pytest.mark.integration
def test_code_highlighting_applied(page):
    page.wait_for_selector("code.hljs")
    assert page.locator("code.hljs").count() >= 1


@pytest.mark.integration
def test_charts_rendered(page):
    # Chart.js creates the charts asynchronously; wait until every visible
    # canvas has been given a size by the renderer.
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('canvas'))"
        ".filter(c => c.offsetParent !== null)"
        ".every(c => c.clientWidth > 0)"
    )
    assert page.locator("canvas").count() >= 5


@pytest.mark.integration
def test_wef_anchor_reveals_sample(page):
    # Clicking a WEF code anchor reveals the sample log line in the code block.
    # The JSON code blocks appear in report order: TopSlow, SlowChart, WEF, Info.
    table = page.locator("table", has_text="Known Risks")
    sample_code = page.locator("pre code.language-json").nth(2)
    before = sample_code.inner_text()
    assert "Click error code" in before
    table.locator("tbody tr a").first.click()
    after = sample_code.inner_text()
    assert after != before
    assert '"id"' in after and '"msg"' in after
