from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PilotWorkspacePeriod(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class PilotWorkspaceExecutionSummary(BaseModel):
    orders: int = 0
    filled_orders: int = 0
    partially_filled_orders: int = 0
    unfilled_orders: int = 0

    fill_rate: float = 0.0

    ordered_quantity: float = 0.0
    executed_quantity: float = 0.0

    total_notional: float = 0.0

    average_slippage_percentage: float | None = None
    weighted_slippage_percentage: float | None = None   

    average_shortfall_percentage: float | None = None
    weighted_shortfall_percentage: float | None = None

    average_vwap_deviation_percentage: float | None = None
    weighted_vwap_deviation_percentage: float | None = None

    analyzed_orders: int = 0
    failed_orders: int = 0

    tca_requested_orders: int = 0
    tca_coverage_percentage: float = 0.0


class PilotWorkspaceQualitySummary(BaseModel):
    analyzed_orders: int = 0
    coverage_percentage: float = 0.0

    excellent: int = 0
    good: int = 0
    fair: int = 0
    poor: int = 0
    unknown: int = 0


class PilotWorkspaceExceptionSummary(BaseModel):
    total: int = 0

    open: int = 0
    acknowledged: int = 0
    in_review: int = 0
    resolved: int = 0
    ignored: int = 0

    medium: int = 0
    high: int = 0
    critical: int = 0


class PilotWorkspaceBreakdownItem(BaseModel):
    name: str
    orders: int = 0
    analyzed_orders: int = 0
    total_notional: float = 0.0

    fill_rate: float = 0.0

    weighted_slippage_percentage: float | None = None
    weighted_shortfall_percentage: float | None = None
    weighted_vwap_deviation_percentage: float | None = None


class PilotWorkspaceRecentReview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID

    issue_code: str
    severity: str   
    status: str

    metric: str | None = None   
    observed_value: float | None = None
    threshold_value: float | None = None

    message: str | None = None

    assigned_to: uuid.UUID | None = None

    created_at: datetime
    updated_at: datetime


class PilotWorkspaceDatasetContext(BaseModel):
    dataset_id: uuid.UUID | None = None
    dataset_version_id: uuid.UUID | None = None
    version: int | None = None


class PilotWorkspaceOverviewResponse(BaseModel):
    organization_id: uuid.UUID
    project_id: uuid.UUID

    period: PilotWorkspacePeriod
    
    execution: PilotWorkspaceExecutionSummary

    quality: PilotWorkspaceQualitySummary

    exceptions: PilotWorkspaceExceptionSummary

    top_symbols: list[PilotWorkspaceBreakdownItem] = Field(
        default_factory=list
    )

    top_venues: list[PilotWorkspaceBreakdownItem] = Field(
        default_factory=list
    )

    recent_reviews: list[PilotWorkspaceRecentReview] = Field(
        default_factory=list
    )

    market_data: PilotWorkspaceDatasetContext = Field(
        default_factory=PilotWorkspaceDatasetContext
    )