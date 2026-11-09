import pytest
from unittest.mock import Mock
from pydantic import ValidationError

from backend.app.ai import llm_analyzer


# Simulated Gemini response
VALID_RESPONSE = """
{
    "event_description": "5 failed SSH logins in one minute",
    "threat_type": "Potential brute-force attack",
    "severity": "low",
    "summary": "Several failed SSH authentication attempts detected.",
    "recommended_actions": [
        "Review authentication logs",
        "Investigate source IP addresses"
    ]
}
"""


@pytest.fixture
def mock_gemini(monkeypatch):
    """Replace the real Gemini client with a mock."""

    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")

    mock_client = Mock()

    monkeypatch.setattr(
        llm_analyzer.genai,
        "Client",
        lambda api_key: mock_client
    )

    return mock_client


def test_valid_security_analysis(mock_gemini):
    """Test that Gemini returns valid security analysis."""

    mock_gemini.models.generate_content.return_value.text = VALID_RESPONSE

    result = llm_analyzer.analyze_finding(
        "5 failed SSH logins in one minute"
    )

    assert result.severity == "low"
    assert result.threat_type == "Potential brute-force attack"
    assert len(result.recommended_actions) == 2


def test_missing_api_key(monkeypatch):
    """Test that a missing API key produces an error."""

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        llm_analyzer.analyze_finding("Test finding")


def test_empty_gemini_response(mock_gemini):
    """Test that an empty Gemini response is rejected."""

    mock_gemini.models.generate_content.return_value.text = None

    with pytest.raises(ValueError, match="empty response"):
        llm_analyzer.analyze_finding("Test finding")


def test_invalid_severity(mock_gemini):
    """Test that invalid severity values are rejected."""

    invalid_response = VALID_RESPONSE.replace(
        '"severity": "low"',
        '"severity": "extreme"'
    )

    mock_gemini.models.generate_content.return_value.text = invalid_response

    with pytest.raises(ValidationError):
        llm_analyzer.analyze_finding("Test finding")
        