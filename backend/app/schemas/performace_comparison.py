from __future__ import annotations

from pydantic import BaseModel, Field


class PerformanceComparisonRequest(BaseModel):
    file_path: str
    symbols: list[str] = Field(
        min_length=2,
        description="Symbols to compare.",
    )
    periods_per_year: int = Field(
        default=252,
        gt=0,
        description="Number of periods used for annualized volatility.",
    )