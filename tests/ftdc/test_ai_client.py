"""Tests for the AI client used with FTDC analysis."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from x_ray.ai_client import _build_section_prompt, analyze_ftdc_overview, analyze_ftdc_section


def test_analyze_ftdc_section_returns_none_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = analyze_ftdc_section("1.1 Workload", [])
    assert result is None


def test_analyze_ftdc_section_calls_openai_with_correct_prompt():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Analysis result"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("x_ray.ai_client._get_client", return_value=(mock_client, "gpt-4o")):
        metrics = [
            {
                "metric": "query ops/s",
                "unit": "ops/s",
                "peak": 100.5,
                "average": 50.2,
                "values": [10.0, 20.0, 30.0],
            },
            {
                "metric": "insert ops/s",
                "unit": "ops/s",
                "peak": 50.0,
                "average": 25.0,
                "values": [5.0, 10.0, 15.0],
            },
        ]
        result = analyze_ftdc_section("1.1 Workload", metrics)

    assert result == "Analysis result"
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o"
    messages = call_args.kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert "1.1 Workload" in messages[0]["content"]
    assert "query ops/s" in messages[0]["content"]
    assert "[10.0, 20.0, 30.0]" in messages[0]["content"]


def test_analyze_ftdc_section_respects_custom_model():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "ok"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("x_ray.ai_client._get_client", return_value=(mock_client, "custom-model")):
        analyze_ftdc_section("1.2 Ops and Latencies", [])

    assert mock_client.chat.completions.create.call_args.kwargs["model"] == "custom-model"


def test_analyze_ftdc_section_returns_none_on_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("API down")

    with patch("x_ray.ai_client._get_client", return_value=(mock_client, "gpt-4o")):
        result = analyze_ftdc_section("1.1 Workload", [{"metric": "test", "values": [1.0]}])

    assert result is None


def test_build_section_prompt_includes_all_metrics():
    metrics = [
        {
            "metric": "query ops/s",
            "unit": "ops/s",
            "peak": 1500.0,
            "average": 300.0,
            "values": [10.0, 20.0],
        },
    ]
    prompt = _build_section_prompt("1.1 Workload", metrics)

    assert "1.1 Workload" in prompt
    assert "query ops/s" in prompt
    assert "ops/s" in prompt
    assert "1500.0" in prompt
    assert "300.0" in prompt
    assert "[10.0, 20.0]" in prompt
    assert "MongoDB FTDC" in prompt


def test_analyze_ftdc_overview_calls_openai_with_all_metrics():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Workload and latency are correlated."
    mock_client.chat.completions.create.return_value = mock_response

    with patch("x_ray.ai_client._get_client", return_value=(mock_client, "gpt-4o")):
        metrics = [
            {"metric": "query ops/s", "unit": "ops/s", "peak": 100.0, "average": 50.0, "values": [1, 2]},
            {"metric": "reads latency", "unit": "ms/op", "peak": 5.0, "average": 2.0, "values": [0.5, 1.0]},
        ]
        result = analyze_ftdc_overview(metrics)

    assert result == "Workload and latency are correlated."
    call_args = mock_client.chat.completions.create.call_args
    content = call_args.kwargs["messages"][0]["content"]
    assert "Cross-Section Overview" in content
    assert "query ops/s" in content
    assert "reads latency" in content
