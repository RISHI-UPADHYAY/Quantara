from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResearchRunComparisonRequest(BaseModel):
    baseline_run_id: uuid.UUID
    comparison_run_id: uuid.UUID

    @model_validator(mode="after")
    def validate_distinct_runs(self):
        if self.baseline_run_id == self.comparison_run_id:
            raise ValueError("The two run IDs must be different.")
        return self


class ResearchComparedRun(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    analysis_type: str
    status: str
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    created_at: datetime
    completed_at: datetime | None = None


class ResearchMetricComparison(BaseModel):
    metric_path: str
    baseline_value: int | float
    comparison_value: int | float
    difference: float
    percentage_change: float | None = None


class ResearchRunComparisonResponse(BaseModel):
    baseline: ResearchComparedRun
    comparison: ResearchComparedRun

    shared_metrics: list[ResearchMetricComparison] = Field(
        default_factory=list
    )
    baseline_only_metrics: dict[str, Any] = Field(
        default_factory=dict
    )
    comparison_only_metrics: dict[str, Any] = Field(
        default_factory=dict
    )