import uuid
from datetime import datetime
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

class AnalysisRunRequest(BaseModel):
    file_path: str
    dataset_version_id: uuid.UUID

    analysis_type: str = Field(
        min_length=1,
        max_length=100,
    )
    asset_symbol: str | None = None
    benchmark_symbol: str | None = None


class AnalysisRunResponse(BaseModel):
    model_config = {
        "from_attributes": True,
    }

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    analysis_type: str
    status: str
    result: dict[str, Any] | None   
    error_message: str | None   
    row_count: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime


class SharpeAnalysisRequest(BaseModel):
    file_path: str
    asset_symbol: str | None = None
    periods_per_year: int = Field(
        default=252,
        gt=0,
    )
    risk_free_rate: float = 0.0