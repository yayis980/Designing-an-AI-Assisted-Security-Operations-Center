from typing import Any

from sqlalchemy.orm import Session

from app.database.models import SecurityEventModel
from app.services.wazuh import parse_wazuh_alert


def process_wazuh_alert(
        alert: dict[str, Any],
        db: Session, 
) -> SecurityEventModel:
    """PArse a Wazuh alert and persist it in the database."""

    event = parse_wazuh_alert(alert)

    db_event = SecurityEventModel(
        timestamp = event.timestamp,
        rule_id = event.rule_id,
        description=event.description,
        severity = event.severity,
        source_ip = event.source_ip,
        raw_event=event.raw_event,
    )

    try: 
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event

    except Exception:
        db.rollback()
        raise