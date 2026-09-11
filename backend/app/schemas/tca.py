from __future__ import annotations

import uuid

from pydantic import BaseModel   



class TCAMarketDataInput(BaseModel):
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID


class TCARequest(BaseModel):
    market_data: TCAMarketDataInput


class TCAOrderResult(BaseModel):
    order_id: uuid.UUID
    symbol: str
    side: str
    ordered_quantity: float
    executed_quantity: float
    remaining_quantity: float
    fill_count: int


class TCABenchmarkResult(BaseModel):
    arrival_price: float | None = None  
    arrival_timestamp: str | None = None
    market_vwap: float | None = None
    market_twap: float | None = None


class TCAExecutionResult(BaseModel):
    average_execution_price: float
    execution_vwap: float
    gross_notional: float
    commission: float
    fees: float
    cost_per_share: float
    net_execution_cost: float


class TCASlippageResult(BaseModel):
    price: float | None = None
    percentage: float | None = None
    total: float | None = None


class TCAResponse(BaseModel):
    order: TCAOrderResult
    benchmarks: TCABenchmarkResult
    execution: TCAExecutionResult
    slippage: TCASlippageResult
    is_fully_filled: bool