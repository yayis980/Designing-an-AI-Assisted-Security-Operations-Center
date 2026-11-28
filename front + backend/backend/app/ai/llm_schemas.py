from typing import Literal
from pydantic import BaseModel, Field


class SecurityAnalysis(BaseModel):
    event_description: str

    threat_type: str

    severity: Literal[
        "informational",
        "low",
        "medium",
        "high",
        "critical"
    ]

    summary: str

    recommended_actions: list[str] = Field(
        description="Defensive actions recommended for the finding"
    )