from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database connection import Base
from app.database.models import SecurityEventModel
from app.services.pipeline import process_wazuh_alert


def create_test_database():
    """Create an islate in-memory database for testing."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False, 
    )

    Base.metadata.create_all(bind=engine)

    return TestingSessionLocal

def test_process_wazuh_alert():
    TestingSessionLocal = create_test_database()

    with TestingSessionLocal() as db:
        alert = {
            "timestamp": "2026-10-21T10:30:00Z",
            "rule": {
                "id": "5710",
                "decription": "Multiple failed login attempts",
                "level": 8,
            },
            "data": {}
        }