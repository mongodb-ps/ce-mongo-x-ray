"""OpenAI-compatible API client for FTDC chart analysis."""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from openai import OpenAI


class _MetricData(TypedDict):
    metric: str
    unit: str
    peak: float
    average: float
    values: list[float]

_logger = logging.getLogger(__name__)

_AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")


def _get_client() -> tuple[OpenAI | None, str | None]:
    """Return an OpenAI client if the API key is configured, or None."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        _logger.warning("OPENAI_API_KEY not set; AI analysis disabled")
        return None, None
    base_url = os.getenv("OPENAI_BASE_URL", "")
    try:
        from openai import OpenAI
    except ImportError:
        _logger.warning("openai package not installed; AI analysis disabled")
        return None, None
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), _AI_MODEL


def analyze_ftdc_section(
    section_title: str,
    metrics_data: list[_MetricData],
) -> str | None:
    """Send a section's FTDC metrics to the AI for analysis.

    Args:
        section_title: e.g. ``"1.1 Workload"``.
        metrics_data: List of dicts with keys:
            - ``metric``: metric display name
            - ``unit``: unit string (e.g. ``"ops/s"``)
            - ``peak``: peak value
            - ``average``: average value
            - ``values``: list of ~1440 downsampled float values

    Returns:
        AI analysis text, or ``None`` if the AI client is not configured.
    """
    client, model = _get_client()
    if client is None:
        return None

    prompt = _build_section_prompt(section_title, metrics_data)
    _logger.info(
        "Sending AI analysis request for %s (%d metrics, %d chars)",
        section_title,
        len(metrics_data),
        len(prompt),
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception:
        _logger.exception("AI analysis request failed for %s", section_title)
        return None


def _build_section_prompt(section_title: str, metrics_data: list[_MetricData]) -> str:
    """Build the prompt for a single FTDC section."""
    parts = [
        "You are analyzing MongoDB FTDC (Full-Time Diagnostic Data Capture) "
        "metrics from a 24-hour monitoring period.",
        "",
        f"## {section_title}",
        "",
        "Each metric below has ~1440 data points, sampled every 60 seconds "
        "from the raw 1-second FTDC data. Values are provided as a JSON array.",
        "",
    ]

    for entry in metrics_data:
        metric = entry["metric"]
        unit = entry.get("unit", "")
        peak = entry.get("peak", "N/A")
        avg = entry.get("average", "N/A")
        values = entry.get("values", [])

        parts.append(f"### {metric}")
        parts.append(f"- Unit: {unit}")
        parts.append(f"- Peak: {peak}")
        parts.append(f"- Average: {avg}")
        parts.append(f"- Values: {json.dumps(values)}")
        parts.append("")

    parts.extend([
        "Provide a very brief summary (2-3 sentences) indicating whether "
        "these metrics show any potential issues that need attention. "
        "If everything looks normal, simply state that no obvious problems were detected.",
    ])

    return "\n".join(parts)


def analyze_ftdc_overview(metrics_data: list[_MetricData]) -> str | None:
    """Send all metrics from all sections to AI for cross-section correlation analysis.

    Args:
        metrics_data: Combined list of all metrics across all sections.

    Returns:
        AI overview text, or ``None`` if the AI client is not configured.
    """
    client, model = _get_client()
    if client is None:
        return None

    prompt_parts = [
        "You are analyzing MongoDB FTDC metrics from a 24-hour monitoring "
        "period. Below are ALL metrics from every section (Workload, "
        "Ops and Latencies, Performance) combined.",
        "",
        "## Cross-Section Overview",
        "",
        "For each metric, the downsampled values (~1440 points each) and "
        "summary statistics are provided.",
        "",
    ]

    for entry in metrics_data:
        metric = entry["metric"]
        unit = entry.get("unit", "")
        peak = entry.get("peak", "N/A")
        avg = entry.get("average", "N/A")
        values = entry.get("values", [])

        prompt_parts.append(f"### {metric}")
        prompt_parts.append(f"- Unit: {unit}")
        prompt_parts.append(f"- Peak: {peak}")
        prompt_parts.append(f"- Average: {avg}")
        prompt_parts.append(f"- Values: {json.dumps(values)}")
        prompt_parts.append("")

    prompt_parts.extend([
        "Look across ALL the above metrics and provide a brief overview "
        "(2-3 sentences) of any correlations or relationships between "
        "metrics from different sections. For example:",
        "- Does high workload correlate with increased latency?",
        "- Does CPU or memory pressure coincide with cache changes?",
        "- Are there any cascading effects visible across sections?",
        "",
        "If no notable cross-section patterns are found, simply state that.",
    ])

    prompt = "\n".join(prompt_parts)
    _logger.info(
        "Sending AI overview request (%d metrics, %d chars)",
        len(metrics_data),
        len(prompt),
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception:
        _logger.exception("AI overview request failed")
        return None
