from datetime import datetime, timezone 

from sqlalchemy import DataTime, Integer, JSON, string
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base

class SecurityEventModel(Base):
    """Database model for normalized security events."""

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True, 
        index=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

     rule_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False, 
    )

    severity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    source_ip: Mapped[str | None] = mapped_column(
        String(45)
        nullable=True,
        index=True,
    )

    raw_event: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default= dict,
    )