import logging

from sqlalchemy.orm import Session

from app.ai.finding_schemas import ScannerFinding
from app.ai.scanner_adapter import analyze_scanner_finding
from app.database.scanner_models import (
    ScannerFindingModel,
    ScannerAIAnalysisModel,
)


logger = logging.getLogger(__name__)


def save_scanner_finding(
    finding: ScannerFinding,
    db: Session,
) -> ScannerFindingModel:
    """Save an MCP scanner finding to the database."""

    db_finding = ScannerFindingModel(
        finding_id=finding.finding_id,
        source=finding.source,
        target=finding.target,
        tool_name=finding.tool_name,
        category=finding.category,
        title=finding.title,
        description=finding.description,
        scanner_severity=(
            str(finding.scanner_severity)
            if finding.scanner_severity is not None
            else None
        ),
        evidence=finding.evidence,
    )

    try:
        db.add(db_finding)
        db.commit()
        db.refresh(db_finding)

    except Exception:
        db.rollback()
        raise

    return db_finding


def analyze_saved_finding(
    finding_db_id: int,
    db: Session,
) -> ScannerAIAnalysisModel:
    """Analyze a stored finding and persist Gemini's response."""

    # Retrieve the original scanner finding
    db_finding = db.get(ScannerFindingModel, finding_db_id)

    if db_finding is None:
        raise ValueError("Scanner finding not found.")

    # Create a pending AI analysis record
    db_analysis = ScannerAIAnalysisModel(
        finding_db_id=db_finding.id,
        status="pending",
    )

    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    # Convert stored data back into our Pydantic schema
    finding = ScannerFinding(
        finding_id=db_finding.finding_id,
        source=db_finding.source,
        target=db_finding.target,
        tool_name=db_finding.tool_name,
        category=db_finding.category,
        title=db_finding.title,
        description=db_finding.description,
        scanner_severity=db_finding.scanner_severity,
        evidence=db_finding.evidence,
    )

    try:
        # Send security finding to Gemini
        result = analyze_scanner_finding(finding)

    except Exception as error:
        logger.warning(
            "AI analysis failed: %s",
            type(error).__name__,
        )

        db_analysis.status = "failed"

    else:
        # Store Gemini's structured response
        db_analysis.status = "completed"

        db_analysis.event_description = result.event_description
        db_analysis.threat_type = result.threat_type
        db_analysis.ai_severity = result.severity
        db_analysis.summary = result.summary
        db_analysis.recommended_actions = result.recommended_actions

    try:
        db.commit()
        db.refresh(db_analysis)

    except Exception:
        db.rollback()
        raise

    return db_analysis
