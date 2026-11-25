from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.ai.finding_schemas import ScannerFinding


class ScannerFindingResponse(ScannerFinding):
    """API response for a stored MCP scanner finding."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class ScannerAIAnalysisResponse(BaseModel):
    """API response containing Gemini's security analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    finding_db_id: int
    status: str

    event_description: str | None = None
    threat_type: str | None = None
    ai_severity: str | None = None
    summary: str | None = None

    recommended_actions: list[str]

    created_at: datetime

