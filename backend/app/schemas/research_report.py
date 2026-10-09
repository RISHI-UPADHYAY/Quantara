from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ResearchReportResponse(BaseModel):
    report_id: uuid.UUID
    analysis_run_id: uuid.UUID

    title: str
    analysis_type: str  

    organization_id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID

    executive_summary: str | None = None

    methodology: dict[str, Any] = Field(
        default_factory=dict,
    )

    results: dict[str, Any] = Field(
        default_factory=dict,
    )

    findings: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    risk_considerations: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    data_limitations: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    reproducibility: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )