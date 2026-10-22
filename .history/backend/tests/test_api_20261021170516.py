from fastapi.testclient import TestClient

from app.main import app 

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "soc-backend",
    }

def test_create_event():
    response = client.post(
        "api/v1/events",
        json={
            "rule_id": "5710",
            "description": "Multiple failed login attempts",
            "severity": 8, 
            "source_ip": "192.168.1.50",
            "raw_event": {
                "source": "automated_test",
                "event_type": "authentication_failure",
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["rule_id"] == "5710"
    assert response.json()["severity"] == 8
    assert "id" in response.json()

def test_list_events():
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_exisiting_event():
    create_response = client.post(
        "/api/v1/events",
        json = {
            "rule_id": "5710",
            "description": "Test event for retrieval",
            "severity": 8,
            "source_ip": "192.168.1.50"
        },
    )

    event_id = create_response.json()["id"]
        response = client.get(f"/api/v1/events/{event_id}")

    assert response.status_code == 200 
    assert response.json()["id"] == event_id