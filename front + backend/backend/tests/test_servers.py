from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_servers_group_events_into_findings():
    client.post(
        "/api/v1/events",
        json={
            "rule_id": "100210",
            "description": "Tool behavior does not match its declared purpose",
            "severity": 12,
            "raw_event": {
                "source": "mcp-scanner",
                "server": "test-server",
                "tool": "get_metrics",
                "category": "Behavioral mismatch",
                "evidence": {"static": "s", "runtime": "r", "ai": "a"},
                "recommendation": "Do not deploy.",
            },
        },
    )

    response = client.get("/api/v1/servers/")
    assert response.status_code == 200

    server = next(s for s in response.json() if s["name"] == "test-server")
    finding = server["findings"][0]
    assert finding["severity"] == "High"  # Wazuh level 12
    assert finding["tool"] == "get_metrics"
    assert finding["evidence"]["runtime"] == "r"
    assert server["tools_count"] == 1
    assert server["risk_score"] == 25


def test_event_without_server_goes_to_unknown_server():
    client.post(
        "/api/v1/events",
        json={"rule_id": "5710", "description": "Failed login", "severity": 3},
    )
    names = [s["name"] for s in client.get("/api/v1/servers/").json()]
    assert "unknown-server" in names


def test_start_scan_is_queued():
    response = client.post("/api/v1/scans/", json={"target": "./my-mcp-server"})
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
