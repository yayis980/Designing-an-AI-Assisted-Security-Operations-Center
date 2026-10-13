from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field 

class SecurityEvent(BaseModel):
    """Normalized security event used by the SOC backend."""

    model_config = ConfigDict(extra="allow")

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    rule_id: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2000)
    severity: int = Field(ge=0, le=15)
    source_ip: str | None = None
    raw_event: dict[str, Any] = Field(default_factory=dict)

class SecurityEventCreate(SecurityEvent):
    """Schema for events submitted to the API."""

class SecurityEventResponse(SecurityEvent):
    """Schema returned by the API after an evet is stored."""

    id: int