from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session 

from app.database.connection import get_db
from app.database import models
from app.schemas.event import SecurityEventCreate, SecurityEventResponse

router = APIRouter()

@router.post(
    "/",
    response_model=SecurityEventResponse,
    status_code=201,
    tags=["Security Events"],
)

def create_event(
    event: SecurityEventCreate,
    db: Session = Depends(get_db),
):
    db_event = models.SecurityEventModel(
        timestamp=event.timestamp,
        rule_id=event.rule_id,
        description=event.description,
        severity=event.severity,
        source_ip=event.source_ip,
        raw_event=event.raw_event,
    )

    try:
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save security event.",
        ) from exc

@router.get(
        "/",
        response_model=list[SecurityEventResponse],
        tags=["Security Events"],
    )

def list_events(db: Session = Depends(get_db)):
    """Retrieve all stored security events."""
    return (
    db.query(models.SecurityEventModel)
    .order_by(models.SecurityEventModel.id.desc())
    .all()
)

@router.get(
    "/{event_id}",
    response_model = SecurityEventResponse,
    tags=["Security Events"],
)

def get_event(
    event_id: int,
    db: Session = Depends(get_db),
):

    """Retrieve one security event by its ID."""
    db_event = (
        db.query(models.SecurityEventModel)
        .filter(models.SecurityEventModel.id == event_id)
        .first()
    )

    if db_event is None:
        raise HTTPException(
            status_code=404,
            detail=f"Security event with ID {event_id} not found."
        )

    return db_event