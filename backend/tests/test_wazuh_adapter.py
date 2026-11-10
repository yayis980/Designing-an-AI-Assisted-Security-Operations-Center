import json
from unittest.mock import Mock

from backend.app.ai import wazuh_adapter
from backend.app.ai.llm_schemas import SecurityAnalysis
from backend.app.schemas.event import SecurityEventCreate


def test_wazuh_adapter(monkeypatch):

    # Create a simulated normalized Wazuh event
    event = SecurityEventCreate(
        rule_id="5710",
        description="Five failed SSH logins within one minute",
        severity=8,
        source_ip="192.168.1.50",
        raw_event={"secret": "do-not-send"},
    )

    # Create a simulated Gemini analysis
    expected_analysis = SecurityAnalysis(
        event_description="Five failed SSH logins",
        threat_type="Potential brute-force attack",
        severity="low",
        summary="Repeated failed SSH authentication attempts.",
        recommended_actions=[
            "Review authentication logs",
            "Investigate repeated login failures",
        ],
    )

    # Mock the Gemini analyzer to avoid real API calls
    mock_analyzer = Mock(return_value=expected_analysis)

    monkeypatch.setattr(
        wazuh_adapter,
        "analyze_finding",
        mock_analyzer,
    )

    # Analyze the normalized event
    result = wazuh_adapter.analyze_wazuh_event(event)

    # Verify Gemini's structured result is returned
    assert result == expected_analysis
    assert result.severity == "low"

    # Verify only intended fields are forwarded
    mock_analyzer.assert_called_once()

    sent_finding = json.loads(
        mock_analyzer.call_args.args[0]
    )

    assert sent_finding["rule_id"] == "5710"
    assert sent_finding["wazuh_rule_level"] == 8

    # Verify sensitive fields were not forwarded
    assert "source_ip" not in sent_finding
    assert "raw_event" not in sent_finding
    