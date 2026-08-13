"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

# Render the HTML report generated from the FTDC sample in a headless browser
# and verify the key UI elements exist. The outline, copy buttons, metadata
# tabs and syntax highlighting are created dynamically by JavaScript, hence
# the need for Playwright.
import os
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("playwright")

from x_ray.ftdc_analysis.framework import Framework as FTDCAnalysisFramework
from x_ray.utils import load_config

FTDC_SAMPLE = os.environ.get("FTDC_SAMPLE", "metrics.2026-07-29T06-50-11Z-00000")

EXPECTED_SECTIONS = [
    "1 Baseline Analysis",
    "1.1 Workload",
    "1.2 Ops and Latencies",
    "1.3 Performance",
    "2 Metadata Review",
]


@pytest.fixture(scope="module")
def report_html(tmp_path_factory):
    """Generate the HTML report from the FTDC sample."""
    data_file = Path(FTDC_SAMPLE)
    if not data_file.is_absolute():
        data_file = Path(__file__).resolve().parent.parent.parent / "misc" / FTDC_SAMPLE
    assert data_file.is_file(), f"Missing sample data: {data_file}"
    # The FTDC framework ingests every `metrics.*` file in a directory and
    # skips `.interim`/`.tmp` files, so copy the sample under a finalized name.
    dest_name = data_file.name
    if dest_name.endswith(".interim") or dest_name.endswith(".tmp"):
        dest_name = dest_name.rsplit(".", 1)[0] + ".copy"
    input_dir = tmp_path_factory.mktemp("ftdc")
    shutil.copy(data_file, input_dir / dest_name)
    output_dir = tmp_path_factory.mktemp("report")
    config = load_config(None)["ftdc"]
    framework = FTDCAnalysisFramework(str(input_dir), deepcopy(config))
    framework.run_ftdc_analysis("default", output_folder=f"{output_dir}/")
    framework.output_results(output_folder=f"{output_dir}/", fmt="html", open_browser=False)
    html_files = list(output_dir.rglob("report.html"))
    assert html_files, "report.html was not generated"
    return html_files[0]


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:
            pytest.skip(f"Chromium is not installed for Playwright: {exc}")
        yield browser
        browser.close()


@pytest.fixture(scope="module")
def page(browser, report_html):
    """Load the report and wait for the dynamically generated outline."""
    page = browser.new_page()
    page.goto(report_html.resolve().as_uri(), wait_until="load")
    # The outline nav is built from h2/h3 headings by JavaScript on load.
    page.wait_for_selector("#outline ul a")
    yield page
    page.close()


@pytest.mark.integration
def test_report_title(page):
    assert page.title() == "FTDC Analysis Report"


@pytest.mark.integration
def test_all_sections_rendered(page):
    h1 = [h.inner_text() for h in page.locator("h1").all()]
    assert h1 == ["FTDC Analysis Report"]
    headings = [h.inner_text() for h in page.locator("h2, h3").all()]
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
    # The table count depends on how much data the captured metrics file has
    # (fresh clusters and shards can be sparse), but at least the Workload
    # table is always emitted.
    assert page.locator("table").count() >= 1


@pytest.mark.integration
def test_charts_rendered(page):
    # FTDC charts are pre-rendered as inline <img> elements (base64 PNGs).
    assert page.locator("img").count() >= 1


@pytest.mark.integration
def test_copy_table_buttons_added(page):
    # addTableCopyButtons() wraps every table with a copy button once the
    # highlight.js CDN script has loaded (it runs at the end of script.js).
    page.wait_for_selector(".table-copy-button")
    assert page.locator(".table-copy-button").count() >= 1


@pytest.mark.integration
def test_metadata_tabs_rendered(page):
    assert page.locator(".metadata-tab-btn").count() == 7
    assert page.locator(".metadata-tab-pane").count() == 7


@pytest.mark.integration
def test_metadata_tab_switching(page):
    page.locator(".metadata-tab-btn").nth(1).click()
    active = page.locator(".metadata-tab-pane.active")
    assert active.count() == 1
    assert active.get_attribute("id") == "metadata-tabs-startup-args"


@pytest.mark.integration
def test_code_highlighting_applied(page):
    # The metadata code blocks sit inside tab panes, most of which are hidden,
    # so wait for the highlight class to be attached rather than visible.
    page.wait_for_selector("code.hljs", state="attached")
    assert page.locator("code.hljs").count() >= 1
