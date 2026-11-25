from pydantic import BaseModel, Field


class ScannerFinding(BaseModel):

    finding_id: str

    source: str

    target: str

    tool_name: str | None = None

    category: str

    title: str

    description: str

    scanner_severity: str | int | None = None

    evidence: list[str] = Field(default_factory=list)
    