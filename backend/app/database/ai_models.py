from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class AIAnalysisModel(Base):
    """
    Stores Gemini security analyses associated
    with existing Wazuh security events.
    """

    __tablename__ = "ai_analyses"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_ai_analyses_status",
        ),
    )

    # Unique AI analysis identifier
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # References the original Wazuh event
    event_id: Mapped[int] = mapped_column(
        ForeignKey("security_events.id"),
        nullable=False,
        index=True,
    )

    # AI processing status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Gemini-generated analysis fields
    event_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    threat_type: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    ai_severity: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommended_actions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # When this analysis record was created
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    