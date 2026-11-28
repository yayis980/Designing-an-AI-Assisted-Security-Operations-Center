import json

from ..schemas.event import SecurityEvent
from .llm_analyzer import analyze_finding
from .llm_schemas import SecurityAnalysis


def analyze_wazuh_event(event: SecurityEvent) -> SecurityAnalysis:
    """
    Convert a normalized Wazuh security event into
    a format suitable for Gemini analysis.
    """

    # Build a minimal security finding
    finding = {
        "source": "Wazuh",
        "rule_id": event.rule_id,
        "description": event.description,
        "wazuh_rule_level": event.severity,
    }

    # Convert the security finding to a JSON string
    finding_text = json.dumps(finding)

    # Send the finding to Gemini for analysis
    return analyze_finding(finding_text)