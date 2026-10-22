import pytest 

from app.services.wazuh import parse_wazuh_alert


def test_parse_wazuh_alert():
    alert = {
        "timestamp": "2026-10-21T10:30:00Z",
        "rule": {
            "id": "5710",
            "description": "Multiple failed login attempts",
            "level": 8,
        },
        "data": {
            "scrip": "192.168.1.50",
        },
    }
    event = parse_wazuh_alert(alert)

    assert event.rule_id == "5710"
    assert event.description == "Multiple failed login attempts"
    assert event.severity == 8 
    assert event.source_ip == "192.168.1.50"
    assert event.raw_event == alert 

def test_parse_wazuh_alert_rejects_missing_rule_id():
    alert = {
        "rule": {
            "description": "Test alert",
            "level": 5,
        }
    }

    with pytest.raises(ValueError, match="rule ID"):
        parse_wazuh_alert(alert)