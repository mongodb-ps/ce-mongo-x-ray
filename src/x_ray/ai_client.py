"""OpenAI-compatible API client for FTDC chart analysis."""

from __future__ import annotations

import json
import logging
import os

_logger = logging.getLogger(__name__)

_AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")


def _get_client():
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
    metrics_data: list[dict],
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


def _build_section_prompt(section_title: str, metrics_data: list[dict]) -> str:
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
