from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class ResearchDashboardRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_type: str
    status: str
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    reproduced_from_id: uuid.UUID | None = None
    row_count: int | None = None
    result: dict | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ResearchAnalysisCoverage(BaseModel):
    analysis_type: str
    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    running_runs: int = 0
    pending_runs: int = 0
    latest_status: str | None = None
    latest_run_at: datetime | None = None


class ResearchLatestActivity(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_type: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None 


class ResearchDashboardSummary(BaseModel):
    workspace_id: uuid.UUID
    workspace_name: str
    workspace_status: str
    dataset_id: uuid.UUID | None
    dataset_version_id: uuid.UUID | None
    symbols: list[str] = Field(
        default_factory=list,
    )

    total_runs: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    running_runs: int = 0
    pending_runs: int = 0

    recent_runs: list[ResearchDashboardRunSummary] = Field(
        default_factory=list,
    ) 

    analysis_coverage: list[ResearchAnalysisCoverage] = Field(
        default_factory=list,
    )
    latest_completed_analyses: list[ResearchDashboardRunSummary] = Field(
        default_factory=list,
    )
    latest_activity: ResearchLatestActivity | None = None