import json
from unittest.mock import Mock

from backend.app.ai import scanner_adapter
from backend.app.ai.finding_schemas import ScannerFinding
from backend.app.ai.llm_schemas import SecurityAnalysis


def test_scanner_adapter(monkeypatch):

    # Simulated MCP scanner finding
    finding = ScannerFinding(
        finding_id="MCP-001",
        source="mcp_runtime",
        target="ran-diagnostics",
        tool_name="get_radio_metrics",
        category="behavioral_mismatch",
        title="Unexpected filesystem access",
        description=(
            "An MCP tool accessed configuration files "
            "outside its declared scope."
        ),
        scanner_severity="high",
        evidence=[
            "Sandbox detected unauthorized file access."
        ],
    )

    # Simulated Gemini response
    expected_analysis = SecurityAnalysis(
        event_description="Unauthorized filesystem access",
        threat_type="Potential excessive permissions",
        severity="high",
        summary="The tool accessed files outside its declared scope.",
        recommended_actions=[
            "Review tool permissions",
            "Restrict filesystem access",
        ],
    )

    # Mock Gemini to avoid API requests
    mock_analyzer = Mock(return_value=expected_analysis)

    monkeypatch.setattr(
        scanner_adapter,
        "analyze_finding",
        mock_analyzer,
    )

    # Run analysis
    result = scanner_adapter.analyze_scanner_finding(finding)

    # Validate results
    assert result == expected_analysis
    assert result.severity == "high"

    # Verify scanner findings were forwarded
    mock_analyzer.assert_called_once()

    sent_finding = json.loads(
        mock_analyzer.call_args.args[0]
    )

    assert sent_finding["finding_id"] == "MCP-001"
    assert sent_finding["tool_name"] == "get_radio_metrics"
    assert sent_finding["scanner_severity"] == "high"
    assert len(sent_finding["evidence"]) == 1
    