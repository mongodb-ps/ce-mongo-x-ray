"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

# Render the HTML report generated from the getMongoData samples in a headless
# browser and verify the key UI elements exist. The outline, copy buttons and
# syntax highlighting are created dynamically by JavaScript, hence the need
# for Playwright.
import os
from copy import deepcopy
from pathlib import Path

import pytest

pytest.importorskip("playwright")

from x_ray.gmd_analysis.framework import Framework as GMDAnalysisFramework
from x_ray.utils import load_config


def _gmd_samples():
    custom = os.environ.get("GMD_SAMPLE")
    if custom:
        return [custom]
    return ["getMongoData-rs.json", "getMongoData-sh.json"]


GMD_SAMPLES = _gmd_samples()

GMD_ITEMS = [
    "Build Information",
    "Host Information",
    "Replica Set Architecture",
    "Sharded Cluster Architecture",
    "Server Status",
    "Security Information",
    "Databases",
    "Collection Information",
    "Index Information",
]

EXPECTED_SECTIONS = ["1 Review Test Results", "2 Review Raw Results"] + [
    f"{part}{name}" for i, name in enumerate(GMD_ITEMS, 1) for part in (f"1.{i} ", f"2.{i} Review ")
]

# The sharded-cluster report has no replica-set info and vice versa. The
# cluster started by prepare_rs.sh is a replica set, so a custom GMD_SAMPLE is
# expected to contain replica-set (and not sharded-cluster) sections.
def _arch_sections():
    custom = os.environ.get("GMD_SAMPLE")
    if custom:
        return {
            custom: {
                "2.3 Review Replica Set Architecture": True,
                "2.4 Review Sharded Cluster Architecture": False,
            }
        }
    return {
        "getMongoData-rs.json": {
            "2.3 Review Replica Set Architecture": True,
            "2.4 Review Sharded Cluster Architecture": False,
        },
        "getMongoData-sh.json": {
            "2.3 Review Replica Set Architecture": False,
            "2.4 Review Sharded Cluster Architecture": True,
        },
    }


ARCH_SECTIONS = _arch_sections()


@pytest.fixture(scope="module", params=GMD_SAMPLES)
def report_html(request, tmp_path_factory):
    """Generate the HTML report from a getMongoData sample."""
    data_file = Path(request.param)
    if not data_file.is_absolute():
        data_file = Path(__file__).resolve().parent.parent.parent / "misc" / request.param
    assert data_file.is_file(), f"Missing sample data: {data_file}"
    output_dir = tmp_path_factory.mktemp("report")
    config = load_config(None)["gmd"]
    framework = GMDAnalysisFramework(str(data_file), deepcopy(config))
    framework.run_gmd_analysis("default", output_folder=f"{output_dir}/")
    framework.output_results(output_folder=f"{output_dir}/", fmt="html", open_browser=False)
    html_files = list(output_dir.rglob("report.html"))
    assert html_files, "report.html was not generated"
    return request.param, html_files[0]


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
    page.goto(report_html[1].resolve().as_uri(), wait_until="load")
    # The outline nav is built from h2/h3 headings by JavaScript in window.onload.
    page.wait_for_selector("#outline ul a")
    yield page
    page.close()


def section_table_count(page, h3_title: str) -> int:
    """Count <table> elements between an h3 and the following h3/h2."""
    return page.evaluate(
        """(title) => {
            const hs = Array.from(document.querySelectorAll("h3"));
            const i = hs.findIndex(h => h.textContent.includes(title));
            if (i === -1) {
                return -1;
            }
            let count = 0;
            for (let el = hs[i].nextElementSibling; el && el.tagName !== "H3" && el.tagName !== "H2"; el = el.nextElementSibling) {
                // addTableCopyButtons() wraps tables in a .table-copy-wrapper div
                if (el.tagName === "TABLE" || el.querySelector("table")) {
                    count++;
                }
            }
            return count;
        }""",
        h3_title,
    )


@pytest.mark.integration
def test_report_title(page):
    assert page.title() == "getMongoData Report"


@pytest.mark.integration
def test_all_sections_rendered(page):
    h1 = [h.inner_text() for h in page.locator("h1").all()]
    assert h1 == ["getMongoData Analysis Report"]
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
    assert page.locator("table").count() >= 10


@pytest.mark.integration
def test_test_result_tables_have_rows(page):
    # Every item emits a test-results table with a Severity column.
    tables = page.locator("table", has_text="Severity")
    assert tables.count() >= 1
    assert tables.first.locator("tbody tr").count() >= 1


@pytest.mark.integration
def test_copy_table_buttons_added(page):
    # addTableCopyButtons() wraps every table with a copy button once the
    # highlight.js CDN script has loaded (it runs in window.onload).
    page.wait_for_selector(".table-copy-button")
    assert page.locator(".table-copy-button").count() >= 10


@pytest.mark.integration
def test_code_highlighting_applied(page):
    page.wait_for_selector("code.hljs")
    assert page.locator("code.hljs").count() >= 1


@pytest.mark.integration
def test_architecture_sections_differ(report_html, page):
    log_name = report_html[0]
    for title, expected in ARCH_SECTIONS[log_name].items():
        count = section_table_count(page, title)
        assert count != -1, f"Section not found: {title}"
        if expected:
            assert count >= 1, f"{title} should contain a table"
        else:
            assert count == 0, f"{title} should be empty"
