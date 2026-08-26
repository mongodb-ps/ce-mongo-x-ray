"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

# Run the health check against a live MongoDB deployment and render the
# generated HTML report in a headless browser to verify the key UI elements
# exist. The outline, charts, copy buttons and syntax highlighting are all
# created dynamically by JavaScript, hence the need for Playwright.
import os
from copy import deepcopy

import pytest

pytest.importorskip("playwright")  # pylint: disable=wrong-import-position

from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

from x_ray.healthcheck.framework import Framework as HealthCheckFramework
from x_ray.utils import load_config

# Playwright fixtures are named after their injected value (browser, page,
# report_html), so parameters and fixture locals shadow the outer fixture
# function names, and the importorskip/lazy-playwright-import ordering is
# deliberate: the whole module is skipped when Chromium is missing — the
# idiomatic pytest patterns.
# pylint: disable=redefined-outer-name,wrong-import-position

HC_URI = os.environ.get("HC_URI", "mongodb://localhost:47017")

HC_ITEMS = [
    "Build Information",
    "Cluster Information",
    "Server Status Information",
    "Shard Key Information",
    "Host Information",
    "Authentication & Security",
    "Collection Information",
    "Index Information",
]

EXPECTED_SECTIONS = [
    "Overview",
    "By Severity",
    "By Category",
    "1 Review Test Results",
    "2 Review Raw Results",
] + [
    f"{part}{name}" for i, name in enumerate(HC_ITEMS, 1) for part in (f"1.{i} ", f"2.{i} Review ")
]


@pytest.fixture(scope="module")
def report_html(tmp_path_factory):
    """Run the health check against HC_URI and generate the HTML report."""
    client = MongoClient(HC_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        client.close()
        pytest.skip(f"Cannot connect to MongoDB at {HC_URI}: {exc}")

    output_dir = tmp_path_factory.mktemp("report")
    config = load_config(None)["healthcheck"]
    framework = HealthCheckFramework(deepcopy(config))
    framework.run_checks(
        "default", client=client, output_folder=f"{output_dir}/", parsed_uri=parse_uri(HC_URI)
    )
    framework.output_results(output_folder=f"{output_dir}/", fmt="html", open_browser=False)
    client.close()
    html_files = list(output_dir.rglob("report.html"))
    assert html_files, "report.html was not generated"
    return html_files[0]


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright  # pylint: disable=import-outside-toplevel

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            pytest.skip(f"Chromium is not installed for Playwright: {exc}")
            return  # unreachable — pytest.skip raises; keeps CodeQL's dataflow happy
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
    assert page.title() == "Healthcheck Report"


@pytest.mark.integration
def test_all_sections_rendered(page):
    h1 = [h.inner_text() for h in page.locator("h1").all()]
    assert h1 == ["Deployment Health Check"]
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
    # The Overview section always emits the By Severity and By Category tables.
    assert page.locator("table").count() >= 2


@pytest.mark.integration
def test_overview_severity_table(page):
    table = page.locator("table", has_text="HIGH").first
    headers = table.locator("thead th").all_inner_texts()
    for severity in ("HIGH", "MEDIUM", "LOW", "INFO"):
        assert severity in headers


@pytest.mark.integration
def test_overview_category_table(page):
    table = page.locator("table", has_text="Known Risks").first
    headers = table.locator("thead th").all_inner_texts()
    for header in ("Category", "Count", "Known Risks"):
        assert header in headers


@pytest.mark.integration
def test_copy_table_buttons_added(page):
    # addTableCopyButtons() wraps every table with a copy button once the
    # highlight.js CDN script has loaded (it runs at the end of script.js).
    page.wait_for_selector(".table-copy-button")
    assert page.locator(".table-copy-button").count() >= 2


@pytest.mark.integration
def test_code_highlighting_applied(page):
    page.wait_for_selector("code.hljs")
    assert page.locator("code.hljs").count() >= 1


@pytest.mark.integration
def test_charts_rendered(page):
    # Chart.js creates the canvas elements asynchronously; wait until every
    # visible canvas has been given a size by the renderer.
    page.wait_for_selector("canvas")
    page.wait_for_function(
        "() => Array.from(document.querySelectorAll('canvas'))"
        ".filter(c => c.offsetParent !== null)"
        ".every(c => c.clientWidth > 0)"
    )
    assert page.locator("canvas").count() >= 1
