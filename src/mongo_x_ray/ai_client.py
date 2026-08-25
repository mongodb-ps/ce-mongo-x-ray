"""Shared OpenAI-compatible client for the AI features of the analysis plugins.

The FTDC and log plugins build their own prompts and call :func:`complete` so
every AI request shares the same client and credentials
(``OPENAI_API_KEY`` / ``OPENAI_BASE_URL`` / ``AI_MODEL``).
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam


_logger = logging.getLogger(__name__)

_AI_MODEL = os.getenv("AI_MODEL", "gpt-4o")

#: Public alias for the configured model name (used by the plugins for logging).
GPT_MODEL = _AI_MODEL


def get_client() -> tuple[OpenAI | None, str]:
    """Return an OpenAI-compatible client if an API key is configured.

    Returns ``(None, model)`` when AI is disabled (no key or the ``openai``
    package is missing) so callers can bail out early.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        _logger.warning("OPENAI_API_KEY not set; AI analysis disabled")
        return None, _AI_MODEL
    base_url = os.getenv("OPENAI_BASE_URL", "")
    try:
        from openai import OpenAI
    except ImportError:
        _logger.warning("openai package not installed; AI analysis disabled")
        return None, _AI_MODEL
    return OpenAI(api_key=api_key, base_url=base_url or None), _AI_MODEL


def complete(prompt: str, system: str | None = None) -> str | None:
    """Send *prompt* to the configured model and return the completion text.

    Args:
        prompt: The user message to send.
        system: Optional system message sent before the user message.

    Returns:
        The completion text, or ``None`` when AI is disabled or the request
        fails.
    """
    client, model = get_client()
    if client is None:
        return None
    messages: list[ChatCompletionMessageParam] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
    except Exception:
        _logger.exception("AI request failed")
        return None
