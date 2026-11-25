import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database.models import SecurityEventModel
from app.database.ai_models import AIAnalysisModel


@pytest.fixture
def db():
    """
    Create an isolated in-memory SQLite database.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def create_sample_event(db):
    """Create a synthetic Wazuh security event."""

    event = SecurityEventModel(
        rule_id="5710",
        description="Multiple failed SSH login attempts",
        severity=8,
        source_ip="192.168.1.50",
        raw_event={},
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def test_save_ai_analysis(db):
    """Verify AI analysis can be stored and retrieved."""

    event = create_sample_event(db)

    analysis = AIAnalysisModel(
        event_id=event.id,
        status="completed",
        event_description="Multiple failed SSH logins",
        threat_type="Potential brute-force attack",
        ai_severity="low",
        summary="Repeated SSH authentication failures detected.",
        recommended_actions=[
            "Review authentication logs",
            "Investigate source IP addresses",
        ],
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    saved = db.get(AIAnalysisModel, analysis.id)

    assert saved is not None
    assert saved.event_id == event.id
    assert saved.status == "completed"
    assert saved.ai_severity == "low"

    assert len(saved.recommended_actions) == 2

    # Original Wazuh severity must remain unchanged
    original_event = db.get(SecurityEventModel, event.id)

    assert original_event.severity == 8


def test_failed_ai_analysis(db):
    """Verify a failed AI analysis can be recorded."""

    event = create_sample_event(db)

    analysis = AIAnalysisModel(
        event_id=event.id,
        status="failed",
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    saved = db.get(AIAnalysisModel, analysis.id)

    assert saved is not None
    assert saved.status == "failed"
    assert saved.ai_severity is None
    assert saved.recommended_actions == []
    