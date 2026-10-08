from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketDataExplorerInstrument(BaseModel):
    symbol: str
    row_count: int = 0
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None



class MarketDataExplorerQuality(BaseModel):
    quality_score: float | None = None
    status: str | None = None
    research_ready: bool | None = None
    checks: list[dict[str, Any]] = Field(
        default_factory=list
    )


class MarketDataExplorerMetadata(BaseModel):
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    version: int
    dataset_name: str
    dataset_type: str | None = None
    row_count: int
    columns: list[str]
    timestamp_column: str | None = None
    symbol_column: str | None = None
    frequency: dict[str, Any] | None = None
    first_timestamp: datetime | None = None 
    last_timestamp: datetime | None = None


class MarketDataExplorerRow(BaseModel):
    timestamp: datetime
    symbol: str | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None


class MarketDataExplorerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metadata: MarketDataExplorerMetadata
    quality: MarketDataExplorerQuality
    instruments: list[MarketDataExplorerInstrument] = Field(
        default_factory=list
    )
    rows: list[MarketDataExplorerRow] = Field(
        default_factory=list
    )
    page: int = 1
    page_size: int = 50
    total_rows: int = 0
    total_pages: int = 0 