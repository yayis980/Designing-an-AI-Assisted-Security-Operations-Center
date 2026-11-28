import json

from .finding_schemas import ScannerFinding
from .data_sanitizer import sanitize_finding
from .llm_analyzer import analyze_finding
from .llm_schemas import SecurityAnalysis

def analyze_scanner_finding(
    finding: ScannerFinding
) -> SecurityAnalysis:
    """
    Sanitize scanner findings before sending to Gemini.
    """

    # Create a sanitized copy
    sanitized = sanitize_finding(finding)

    # Convert sanitized data to JSON
    finding_json = json.dumps(sanitized)

    # Send only sanitized data to Gemini
    return analyze_finding(finding_json)

