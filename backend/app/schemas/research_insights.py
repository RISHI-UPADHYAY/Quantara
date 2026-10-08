from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ResearchInsight(BaseModel):
    category: str = Field(
        description=(
            "Insight category, such as performance, risk, relationship, "
            "benchmark, data_quality or summary."
        ),
    )

    title: str = Field(
        min_length=1,
        description="Short title describing the insight.",
    )

    description: str = Field(
        min_length=1,
        description="Research-oriented explanation of the insight.",
    )

    severity: str = Field(
        default="info",
        description=(
            "Insight importance level: info, positive, warning or critical."
        ),
    )

    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Deterministic Quantara evidence supporrting the insight.",
    )



class ResearchInsightsRequest(BaseModel):
    file_path: str = Field(
        description="Path to the dataset file inside Quantara storage.",
    )

    dataset_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional dataset version used for generating insights.",
    )

    symbols: list[str] | None = Field(
        default=None,
        description="Optional symbols to focus the insights on.",
    )

    periods_per_year: int = Field(
        default=252,
        gt=0,
        description="Number of periods used for annualized risk calculations.",
    )

    include_ai_summary: bool = Field(
        default=True,
        description="Whether to generate an AI-written overall research summary.",
    )



class ResearchInsightsResponse(BaseModel):
    dataset_id: uuid.UUID

    dataset_version_id: uuid.UUID

    symbols: list[str] = Field(
        default_factory=list,
    )

    insights: list[ResearchInsight] = Field(
        default_factory=list,
    )

    ai_summary: str | None = None

    provider: str | None = None

    context: dict[str, Any] = Field(
        default_factory=dict,
    )