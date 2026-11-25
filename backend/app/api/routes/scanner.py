from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.scanner_models import (
    ScannerFindingModel,
    ScannerAIAnalysisModel,
)

from app.ai.finding_schemas import ScannerFinding
from app.ai.scanner_persistence import (
    save_scanner_finding,
    analyze_saved_finding,
)

from app.schemas.scanner import (
    ScannerFindingResponse,
    ScannerAIAnalysisResponse,
)


router = APIRouter(tags=["MCP Scanner"])


@router.post(
    "/findings",
    response_model=ScannerFindingResponse,
    status_code=201,
)
def create_scanner_finding(
    finding: ScannerFinding,
    db: Session = Depends(get_db),
):
    """Receive and save an MCP scanner finding."""

    try:
        return save_scanner_finding(finding, db)

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to save scanner finding.",
        ) from exc


@router.get(
    "/findings",
    response_model=list[ScannerFindingResponse],
)
def list_scanner_findings(
    db: Session = Depends(get_db),
):
    """Retrieve stored MCP scanner findings."""

    return (
        db.query(ScannerFindingModel)
        .order_by(ScannerFindingModel.id.desc())
        .all()
    )


@router.get(
    "/findings/{finding_db_id}",
    response_model=ScannerFindingResponse,
)
def get_scanner_finding(
    finding_db_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a specific MCP scanner finding."""

    finding = db.get(ScannerFindingModel, finding_db_id)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Scanner finding not found.",
        )

    return finding


# This endpoint performs analysis synchronously so the HTTP request remains open while Gemini processes the finding, 
# (This means a temporaty Gemini outage will not delete the original finding)
@router.post(
    "/findings/{finding_db_id}/analyze",
    response_model=ScannerAIAnalysisResponse,
)
def analyze_scanner_finding_endpoint(
    finding_db_id: int,
    db: Session = Depends(get_db),
):
    """Analyze a stored MCP finding using Gemini."""

    finding = db.get(ScannerFindingModel, finding_db_id)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Scanner finding not found.",
        )

    try:
        analysis = analyze_saved_finding(
            finding_db_id,
            db,
        )

        return analysis

    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to store AI analysis.",
        ) from exc


#This endpoint retrieves previously saved analyses without contacting Gemini
@router.get(
    "/findings/{finding_db_id}/analyses",
    response_model=list[ScannerAIAnalysisResponse],
)
def get_scanner_analyses(
    finding_db_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve AI analyses associated with an MCP finding."""

    finding = db.get(ScannerFindingModel, finding_db_id)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Scanner finding not found.",
        )

    analyses = (
        db.query(ScannerAIAnalysisModel)
        .filter(
            ScannerAIAnalysisModel.finding_db_id == finding_db_id
        )
        .order_by(ScannerAIAnalysisModel.id.desc())
        .all()
    )

    return analyses