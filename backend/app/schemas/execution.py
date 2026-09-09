from __future__ import annotations

import uuid

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionOrderCreateRequest(BaseModel):
    external_order_id: str | None = Field(
        default=None,
        max_length=150,
    )
    client_order_id: str | None = Field(
        default=None,
        max_length=150,
    )
    symbol: str = Field(
        min_length=1,
        max_length=50,
    )
    side: Literal["buy", "sell"]
    quantity: float = Field(
        gt=0,
    )
    order_type: Literal[
        "market",
        "limit",
        "stop",
        "stop_limit",
    ]
    limit_price: float | None = Field(
        default=None,
        ge=0,
    )
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
    status: Literal[
        "pending",
        "open",
        "partially_filled",
        "filled",
        "cancelled",
        "rejected",
    ] = "pending"
    submitted_at: datetime
    completed_at: datetime | None = None


class ExecutionOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID

    external_order_id: str | None
    client_order_id: str | None

    symbol: str
    side: str
    quantity: float
    order_type: str
    limit_price: float | None

    strategy: str | None
    algorithm: str | None
    venue: str | None

    status: str
    submitted_at: datetime
    completed_at: datetime | None

    created_by: uuid.UUID
    created_at: datetime


class ExecutionFillCreateRequest(BaseModel):
    external_fill_id: str | None = Field(
        default=None,
        max_length=150,
    )
    price: float = Field(
        ge=0,
    )
    quantity: float = Field(
        gt=0,
    )
    venue: str | None = Field(
        default=None,
        max_length=100,
    )
    executed_at: datetime
    commission: float | None = Field(
        default=None,
        ge=0,
    )
    fees: float | None = Field(
        default=None,
        ge=0,
    )


class ExecutionFillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_order_id: uuid.UUID

    external_fill_id: str | None

    price: float
    quantity: float

    venue: str | None
    executed_at: datetime

    commission: float | None
    fees: float | None

    created_at: datetime