from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.event import SecurityEventResponse
from app.services.pipeline import process_wazuh_alert

router = APIRouter()

@router.post(
    "/wazuh",
    response_model=SecurityEventResponse,
    status_code=201,
    tags=["Wazuh Alerts"],
)
def ingest_wazuh_alert(
    alert: dict,
    db: Session = Depends(get_db),
):
    """Recieve a raw Wazuh alert and save it as a normalized event."""

    try:
        return process_wazuh_alert(alert, db)
    except ValueError as exc:
        raise HTTPException(
            status_code = 422,
            detail=str(exc),
        ) from exc
    except Exception as exc: 
        raise HTTPException(
            status_code = 500,
            detail="Failed to process Wazuh alert.",
        ) from exc 
    