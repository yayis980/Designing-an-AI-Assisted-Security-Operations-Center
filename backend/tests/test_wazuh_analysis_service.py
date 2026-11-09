from unittest.mock import Mock

import pytest

from app.ai import wazuh_analysis_service as service
from app.ai.llm_schemas import SecurityAnalysis


# Simulated Wazuh security alert
SAMPLE_ALERT = {
    "timestamp": "2026-11-08T10:30:00Z",
    "rule": {
        "id": "5710",
        "description": "Multiple failed SSH login attempts",
        "level": 8,
    },
    "data": {
        "srcip": "192.168.1.50",
    },
}


def test_successful_wazuh_analysis(monkeypatch):

    expected_analysis = SecurityAnalysis(
        event_description="Multiple failed SSH logins",
        threat_type="Potential brute-force attack",
        severity="low",
        summary="Repeated authentication failures detected.",
        recommended_actions=[
            "Review authentication logs",
        ],
    )

    mock_analyzer = Mock(return_value=expected_analysis)

    monkeypatch.setattr(
        service,
        "analyze_wazuh_event",
        mock_analyzer,
    )

    result = service.analyze_wazuh_alert(SAMPLE_ALERT)

    assert result.ai_status == "completed"
    assert result.ai_analysis == expected_analysis
    assert result.event.rule_id == "5710"
    assert result.event.severity == 8

    mock_analyzer.assert_called_once()


def test_gemini_failure_preserves_event(monkeypatch):

    mock_analyzer = Mock(
        side_effect=RuntimeError("Gemini unavailable")
    )

    monkeypatch.setattr(
        service,
        "analyze_wazuh_event",
        mock_analyzer,
    )

    result = service.analyze_wazuh_alert(SAMPLE_ALERT)

    assert result.ai_status == "failed"
    assert result.ai_analysis is None

    # Original Wazuh information remains available
    assert result.event.rule_id == "5710"
    assert result.event.severity == 8
    assert result.event.description == (
        "Multiple failed SSH login attempts"
    )


def test_invalid_wazuh_alert():

    invalid_alert = {
        "rule": {
            "description": "Missing rule ID",
            "level": 5,
        }
    }

    with pytest.raises(ValueError, match="rule ID"):
        service.analyze_wazuh_alert(invalid_alert)