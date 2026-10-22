from app.services.wazuh_parser import parse_wazuh_alert

def test_parse_wazuh_alert():
    alert = {
        "timestamp: "2026-10-21T10:30:00Z",
        "rule": {
            "id": "5710",
            "description": "Multiple failed login attempts",
            "level": 8,
        },
        "data": {
            "scrip": "192.168.1.50"
        }
    }