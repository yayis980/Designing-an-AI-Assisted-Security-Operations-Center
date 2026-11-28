from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import models
from app.database.connection import get_db
from app.services.servers import build_servers

router = APIRouter()


@router.get("/", tags=["Servers"])
def list_servers(db: Session = Depends(get_db)):
    """Scanned servers with their findings, built from the stored events."""
    events = (
        db.query(models.SecurityEventModel)
        .order_by(models.SecurityEventModel.id.desc())
        .all()
    )
    return build_servers(events)
