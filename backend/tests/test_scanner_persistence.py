import pytest
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.database import models, ai_models, scanner_models

from app.ai.finding_schemas import ScannerFinding
from app.ai.llm_schemas import SecurityAnalysis
from app.ai import scanner_persistence


@pytest.fixture
def db():
    """Create an isolated in-memory SQLite database."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


@pytest.fixture
def sample_finding():
    """Create a synthetic MCP scanner finding."""

    return ScannerFinding(
        finding_id="MCP-001",
        source="mcp_runtime",
        target="ran-diagnostics",
        tool_name="get_radio_metrics",
        category="behavioral_mismatch",
        title="Unexpected filesystem access",
        description=(
            "An MCP tool attempted to access files "
            "outside its authorized directory."
        ),
        scanner_severity="high",
        evidence=[
            "Sandbox detected unauthorized access attempt."
        ],
    )


def test_save_scanner_finding(db, sample_finding):

    saved = scanner_persistence.save_scanner_finding(
        sample_finding,
        db,
    )

    assert saved.id is not None
    assert saved.finding_id == "MCP-001"
    assert saved.scanner_severity == "high"

    # Verify the finding exists in the database
    retrieved = db.get(
        scanner_models.ScannerFindingModel,
        saved.id,
    )

    assert retrieved is not None
    assert retrieved.tool_name == "get_radio_metrics"


def test_save_gemini_analysis(db, sample_finding, monkeypatch):

    saved = scanner_persistence.save_scanner_finding(
        sample_finding,
        db,
    )

    expected_analysis = SecurityAnalysis(
        event_description="Unexpected filesystem access",
        threat_type="Potential unauthorized file access",
        severity="medium",
        summary="The MCP tool attempted unauthorized access.",
        recommended_actions=[
            "Review tool permissions",
            "Investigate filesystem activity",
        ],
    )

    mock_analyzer = Mock(return_value=expected_analysis)

    monkeypatch.setattr(
        scanner_persistence,
        "analyze_scanner_finding",
        mock_analyzer,
    )

    result = scanner_persistence.analyze_saved_finding(
        saved.id,
        db,
    )

    assert result.status == "completed"
    assert result.ai_severity == "medium"
    assert result.finding_db_id == saved.id
    assert len(result.recommended_actions) == 2

    mock_analyzer.assert_called_once()

    # Verify the analysis was actually persisted
    retrieved = db.get(
        scanner_models.ScannerAIAnalysisModel,
        result.id,
    )

    assert retrieved is not None
    assert retrieved.summary == expected_analysis.summary


def test_gemini_failure_preserves_finding(
    db,
    sample_finding,
    monkeypatch,
):

    saved = scanner_persistence.save_scanner_finding(
        sample_finding,
        db,
    )

    mock_analyzer = Mock(
        side_effect=RuntimeError("Gemini unavailable")
    )

    monkeypatch.setattr(
        scanner_persistence,
        "analyze_scanner_finding",
        mock_analyzer,
    )

    result = scanner_persistence.analyze_saved_finding(
        saved.id,
        db,
    )

    assert result.status == "failed"

    # Verify original scanner finding still exists
    original = db.get(
        scanner_models.ScannerFindingModel,
        saved.id,
    )

    assert original is not None
    assert original.finding_id == "MCP-001"
    assert original.scanner_severity == "high"
    