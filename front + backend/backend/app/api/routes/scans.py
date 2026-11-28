from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import models
from app.database.connection import get_db

router = APIRouter()


class ScanRequest(BaseModel):
    """What the front end sends when the user clicks "New scan"."""

    target: str = Field(min_length=1, max_length=2000)


@router.post("/", status_code=202, tags=["Scans"])
def start_scan(
    request: ScanRequest,
    db: Session = Depends(get_db),
):
    """Record a request to scan an MCP server.

    The scanner itself is not part of this backend yet. This saves the request
    with status "queued" so a scanner worker can pick it up later; its results
    come back through the events endpoints and show up under /servers.
    """
    db_scan = models.ScanRequestModel(target=request.target.strip())

    try:
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save scan request.",
        ) from exc

    return {
        "ok": True,
        "id": db_scan.id,
        "status": db_scan.status,
        "message": f"Scan queued for {db_scan.target}",
    }
