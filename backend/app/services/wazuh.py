from typing import Any

from app.schemas.event import SecurityEventCreate

def parse_wazuh_alert(alert: dict[str, Any]) -> SecurityEventCreate:
    """Convert a Wazuh JSON alert into the SOC event schema."""

    rule = alert.get("rule") or {}
    data = alert.get("data") or {}

    rule_id = rule.get("id") or alert.get("rule_id")
    description = rule.get("description") or alert.get("description") 
    severity = rule.get("level", alert.get("severity", 0))

    if rule_id is None or description is None: 
        raise ValueError(
            "Wazuh alert must contian a rule ID and description."
        )
    event_data = {
        "rule_id": str(rule_id),
        "description": str(description),
        "severity": severity, 
        "source_ip": (
            data.get("srcip")
            or data.get("source_ip")
            or alert.get("source_ip")
        ),
        "raw_event": alert,
    }

    timestamp = alert.get("timestamp") or alert.get("@timestamp")
    if timestamp:
        event_data["timestamp"] = timestamp

    return SecurityEventCreate.model_validate(event_data)