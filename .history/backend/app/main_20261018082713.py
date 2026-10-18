from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, get_db
from app.database import models
from app.schemas.event import SecurityEventCreate, SecurityEventResponse

app = FastAPI(
    title="AI-Assisted Securirty Operations Center API",
    description=(
        "Backend API for security ingenstion, "
        "processin, and analysis"
    ),
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

@app.get("api/v1/health", tags =["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "soc-backend",
    }

@app.post(
    "api/v1/events",
    response_model=SecurityEventResponse,
    status_code=201,
    tags=["Security Events"],
)

def create_event(
    event: SecurityEventCreate,
    db: Session = Depends(get_db),
):

    db_event = models.SecurityEventModel(
        timestamp= event.timestamp,
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
            detail="Failed to save security event."
        ) from exc 