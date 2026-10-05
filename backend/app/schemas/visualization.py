from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VisualizationRequest(BaseModel):
    file_path: str
    symbols: list[str] = Field(
        min_length=1,
        description="Symbols to include in the visualization.",
    )
    chart_type: str = Field(
        description=(
            "Visualization type: price, cumulative_return, "
            "drawdown, volatility or volume."
        ),
    )
    periods_per_year: int = Field(
        default=252,
        gt=0,
        description="Periods used for annualized volatility.",
    )


class VisualizationPoint(BaseModel):
    timestamp: Any
    symbol: str
    value: float | None = None


class VisualizationResponse(BaseModel):
    chart_type: str
    symbols: list[str]
    periods_per_year: int
    points: list[VisualizationPoint]