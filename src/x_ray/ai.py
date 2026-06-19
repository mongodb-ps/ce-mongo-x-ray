"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

"""AI-related functions for analyzing MongoDB log lines."""

import logging
import os
from openai import OpenAI
from x_ray.utils import ai_key

GPT_MODEL = "gpt-4o-mini"  # Use gpt-4o-mini for faster and cheaper responses
MAX_TOKENS = 256

logger = logging.getLogger(__name__)


def analyze_log_line_gpt(log_line):
    """Analyze a MongoDB log line using OpenAI GPT API."""
    if ai_key == "":
        logger.warning("No AI API key found. Skipping AI analysis.")
        return ""

    # Support custom base_url for Azure OpenAI or other services
    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(
        api_key=ai_key,
        base_url=base_url if base_url else None,
    )

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a MongoDB export. Analyze MongoDB log messages and tell me the reason in max 200 words.",
                },
                {"role": "user", "content": str(log_line)},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.3,  # Lower temperature for more focused responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Failed to analyze log line with GPT: %s", e)
        return ""
