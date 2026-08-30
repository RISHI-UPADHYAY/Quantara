from typing import Any

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    file_path: str


class VolatilityAnalysisRequest(BaseModel):
    file_path: str
    periods_per_year: int = Field(
        default=252,
        gt=0,
    )


class AnalysisResponse(BaseModel):
    model_config= {
        'from_attributes': True,
    }

    result: dict[str, Any]


class BetaAnalysisRequest(BaseModel):
    file_path: str
    asset_symbol: str
    benchmark_symbol: str