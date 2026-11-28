"""Turn stored security events into the "servers" the scanner front end shows.

The database only stores flat security events. The front end wants them grouped:

    server
      └── findings  (one finding per stored event)

How an event becomes a finding:
  * The scanner puts its details inside the event's `raw_event` (the "EVENT SENT
    TO WAZUH" box in the UI): server, tool, category, evidence, recommendation...
  * Events are grouped into a server by `raw_event["server"]`.
  * Anything the scanner did not send is left empty ("-" or 0). Nothing is invented.
"""

from typing import Any

from app.database.models import SecurityEventModel

# Used when an event does not say which server it came from.
UNKNOWN_SERVER = "unknown-server"

SEVERITIES = ["Critical", "High", "Medium", "Low"]

# How much each finding adds to a server's risk score (capped at 100).
SEVERITY_WEIGHT = {"Critical": 40, "High": 25, "Medium": 10, "Low": 3}


def _get(raw_event: dict[str, Any], key: str, default: Any = None) -> Any:
    """Read a field from raw_event, also looking inside Wazuh's "data" block."""
    if key in raw_event:
        return raw_event[key]
    data = raw_event.get("data")
    if isinstance(data, dict) and key in data:
        return data[key]
    return default


def severity_label(event: SecurityEventModel) -> str:
    """Pick Critical / High / Medium / Low for one event."""
    # 1) The scanner may already have named the severity.
    named = str(_get(event.raw_event or {}, "severity", "")).capitalize()
    if named in SEVERITIES:
        return named
    # 2) Otherwise use the Wazuh level (0-15) stored on the event.
    if event.severity >= 13:
        return "Critical"
    if event.severity >= 10:
        return "High"
    if event.severity >= 7:
        return "Medium"
    return "Low"


def build_finding(event: SecurityEventModel) -> dict[str, Any]:
    """One stored event -> one finding card."""
    raw = event.raw_event or {}
    evidence = _get(raw, "evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}

    return {
        "id": f"F-{event.id}",
        "severity": severity_label(event),
        "title": event.description,
        "tool": _get(raw, "tool", "-"),
        "category": _get(raw, "category", "-"),
        "rule_id": event.rule_id,
        "confidence": _get(raw, "confidence", "-"),
        "summary": _get(raw, "summary", event.description),
        "evidence": {
            "static": evidence.get("static", "-"),
            "runtime": evidence.get("runtime", "-"),
            "ai": evidence.get("ai", "-"),
        },
        "recommendation": _get(raw, "recommendation", "-"),
    }


def _risk_score(findings: list[dict[str, Any]]) -> int:
    return min(100, sum(SEVERITY_WEIGHT[f["severity"]] for f in findings))


def _count_evidence(findings: list[dict[str, Any]], kind: str) -> int:
    """How many findings carry evidence of this kind (static / runtime / ai)."""
    return sum(1 for f in findings if f["evidence"][kind] != "-")


def build_server(name: str, events: list[SecurityEventModel]) -> dict[str, Any]:
    """All events of one server -> one server card with its findings."""
    findings = [build_finding(e) for e in events]
    # Worst findings first so the UI selects the most serious one.
    findings.sort(key=lambda f: SEVERITIES.index(f["severity"]))

    # Optional server-level details the scanner may include in any of its events.
    def server_detail(key: str, default: Any) -> Any:
        for event in events:
            value = _get(event.raw_event or {}, key)
            if value is not None:
                return value
        return default

    tools = {f["tool"] for f in findings if f["tool"] != "-"}

    return {
        "id": name,
        "name": name,
        "description": server_detail("server_description", "-"),
        "risk_score": server_detail("risk_score", _risk_score(findings)),
        "tools_count": server_detail("tools_count", len(tools)),
        "permissions_count": server_detail("permissions_count", 0),
        "static_hits": _count_evidence(findings, "static"),
        "sandbox_runs": server_detail("sandbox_runs", _count_evidence(findings, "runtime")),
        "canary_hits": server_detail("canary_hits", 0),
        "ai_notes": _count_evidence(findings, "ai"),
        "scan_time": server_detail("scan_time", "-"),
        "findings": findings,
    }


def build_servers(events: list[SecurityEventModel]) -> list[dict[str, Any]]:
    """Group every stored event by server, riskiest server first."""
    grouped: dict[str, list[SecurityEventModel]] = {}
    for event in events:
        name = _get(event.raw_event or {}, "server", UNKNOWN_SERVER)
        grouped.setdefault(str(name), []).append(event)

    servers = [build_server(name, group) for name, group in grouped.items()]
    servers.sort(key=lambda s: s["risk_score"], reverse=True)
    return servers
