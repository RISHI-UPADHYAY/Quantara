from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ResearchCopilotRequest(BaseModel):
    file_path: str = Field(
        description="Path to the dataset file inside Quantara storage.",
    )

    question: str = Field(
        min_length=3,
        max_length=4000,
        description="Research question to answer.",
    )

    dataset_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional dataset version used for the research context.",
    )

    symbols: list[str] | None = Field(
        default=None,
        description="Optional symbols to focus the research on.",
    )

    periods_per_year: int = Field(
        default=252,
        gt=0,
        description="Number of periods used for annualized risk calculations.",
    )



class ResearchEvidence(BaseModel):
    source: str
    metric: str
    value: Any = None
    interpretation: str | None = None



class ResearchCopilotResponse(BaseModel):
    question: str
    answer: str

    provider: str

    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID

    symbols: list[str] = Field(
        default_factory=list,
    )

    evidence: list[ResearchEvidence] = Field(
        default_factory=list,
    )

    context: dict[str, Any] = Field(
        default_factory=dict,
    )