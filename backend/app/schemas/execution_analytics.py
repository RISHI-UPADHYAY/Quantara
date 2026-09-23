from __future__ import annotations

import uuid

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from app.schemas.tca import TCAMarketDataInput


class ExecutionAnalyticsRequest(BaseModel):
    market_data: TCAMarketDataInput

    symbol: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    side: Literal["buy", "sell"] | None = None

    strategy: str | None = Field(
        default=None,
        max_length=100,
    )

    algorithm: str | None = Field(
        default=None,
        max_length=100,
    )

    venue: str | None = Field(
        default=None,
        max_length=100,
    )

    start_time: datetime | None = None
    end_time: datetime | None = None

    limit: int = Field(
        default=100,
        ge=1,
        le=500,
    )


class ExecutionAnalyticsFailedOrder(BaseModel):
    order_id: uuid.UUID
    status_code: int
    detail: str


class ExecutionAnalyticsBreakdown(BaseModel):
    key: str

    orders: int
    executed_orders: int

    total_ordered_quantity: float
    total_executed_quantity: float
    fill_rate_percentage: float

    total_gross_notional: float
    total_explicit_costs: float
    explicit_cost_percentage: float

    weighted_slippage_percentage: float | None = None
    weighted_shortfall_percentage: float | None = None
    weighted_vwap_deviation_percentage: float | None = None

    average_execution_quality_score: float | None = None

    orders_with_exceptions: int
    total_exceptions: int
    issue_counts_by_code: dict[str, int]


class ExecutionAnalyticsSummary(BaseModel):
    requested: int
    analyzed: int
    failed: int

    total_ordered_quantity: float
    total_executed_quantity: float
    fill_rate_percentage: float

    total_gross_notional: float
    total_explicit_costs: float
    explicit_cost_percentage: float

    weighted_slippage_percentage: float | None = None
    weighted_shortfall_percentage: float | None = None
    weighted_vwap_deviation_percentage: float | None = None

    average_execution_quality_score: float | None = None

    orders_with_exceptions: int
    total_exceptions: int

    issue_counts_by_code: dict[str, int]


class ExecutionAnalyticsResponse(BaseModel):
    filters: dict

    summary: ExecutionAnalyticsSummary

    by_symbol: list[ExecutionAnalyticsBreakdown]
    by_side: list[ExecutionAnalyticsBreakdown]
    by_venue: list[ExecutionAnalyticsBreakdown]
    by_date: list[ExecutionAnalyticsBreakdown]

    failed_orders: list[ExecutionAnalyticsFailedOrder] 