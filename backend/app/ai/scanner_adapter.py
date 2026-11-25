from .finding_schemas import ScannerFinding
from .llm_analyzer import analyze_finding
from .llm_schemas import SecurityAnalysis


def analyze_scanner_finding(
    finding: ScannerFinding
) -> SecurityAnalysis:
    """
    Analyze a security finding from an MCP scanner.

    Converts structured scanner findings into JSON
    and sends them to the Gemini analyzer.
    """

    # Convert scanner finding to JSON
    finding_json = finding.model_dump_json(exclude_none=True)

    # Send finding to Gemini
    return analyze_finding(finding_json)
