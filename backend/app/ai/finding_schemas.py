from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict


class ScannerFinding(BaseModel):

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    finding_id: str = Field(
        min_length=1,
        max_length=100
    )

    source: str = Field(
        min_length=1,
        max_length=100
    )

    target: str = Field(
        min_length=1,
        max_length=200
    )

    tool_name: str | None = Field(
        default=None,
        max_length=200
    )

    category: str = Field(
        min_length=1,
        max_length=100
    )

    title: str = Field(
        min_length=1,
        max_length=200
    )

    description: str = Field(
        min_length=1,
        max_length=4000
    )

    scanner_severity: str | int | None = None

    evidence: list[
        Annotated[
            str,
            Field(min_length=1, max_length=1000)
        ]
    ] = Field(
        default_factory=list,
        max_length=20
    )

    