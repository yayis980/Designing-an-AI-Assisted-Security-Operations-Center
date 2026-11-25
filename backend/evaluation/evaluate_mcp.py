from backend.app.ai.finding_schemas import ScannerFinding
from backend.app.ai.scanner_adapter import analyze_scanner_finding


def main():

    # Simulated MCP security finding
    finding = ScannerFinding(
        finding_id="MCP-001",
        source="mcp_runtime",
        target="ran-diagnostics",
        tool_name="get_radio_metrics",
        category="behavioral_mismatch",
        title="Unexpected filesystem access",
        description=(
            "An MCP tool declared as read-only attempted "
            "to access configuration files outside its "
            "authorized directory."
        ),
        scanner_severity="high",
        evidence=[
            "Sandbox monitoring detected an attempt to "
            "access a synthetic configuration file "
            "outside the permitted directory."
        ],
    )

    print("Testing MCP Security Analysis...\n")

    # Send the actual request to Gemini
    analysis = analyze_scanner_finding(finding)

    # Display the validated JSON
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
    