from __future__ import annotations

import uuid

from typing import Literal
from pydantic import BaseModel, Field


FindingCategory = Literal[
    "COST_ISSUE",
    "EXECUTION_CONDITION",
    "POSITIVE_FINDING",
]


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
    market_vwap_unavailable_reason: str | None = None
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



class TCAImplementationShortfallResult(BaseModel):
    price_shortfall: float | None = None
    percentage_shortfall: float | None = None
    explicit_costs: float | None = None 
    total_shortfall: float | None = None 


class TCAMarketImpactResult(BaseModel):
    measure: Literal["arrival_to_end_market_price_change"] = (
        "arrival_to_end_market_price_change"
    )
    interpretation: str = (
        "Market movement during the execution window; "
        "this does not establish causal market impact from the order."
    )
    end_market_price: float | None = None
    market_impact_timestamp: str | None = None
    impact_per_share: float | None = None
    percentage: float | None = None 
    total: float | None = None


class TCAExecutionQualityComponentResult(BaseModel):
    score: float
    weight: float
    percentage: float


class TCAExecutionDiagnosisItem(BaseModel):
    code: str
    severity: str
    message: str
    evidence: dict[str, float | str]


class TCAExecutionDiagnosesResult(BaseModel):
    overall_status: str 
    diagnoses: list[TCAExecutionDiagnosisItem]


class TCAExecutionQualityResult(BaseModel):
    score: float
    rating: str
    components: dict[str, TCAExecutionQualityComponentResult]


class TCAExecutionRecommendationItem(BaseModel):
    diagnosis_code: str
    severity: str
    priority: str
    title: str
    rationale: str
    suggested_actions: list[str]


class TCAExecutionRecommendationsResult(BaseModel): 
    recommendations: list[TCAExecutionRecommendationItem]


class TCAExecutionFinding(BaseModel):
    code: str   
    category: FindingCategory
    severity: str
    message: str
    evidence: dict[str, float | str] = Field(
        default_factory=dict
    )

class TCAExecutionEvidenceSet(BaseModel):
    overall_status: str
    cost_issues: list[TCAExecutionFinding] = Field(
        default_factory=list
    )
    execution_conditions: list[TCAExecutionFinding] = Field(
        default_factory=list
    )
    positive_findings: list[TCAExecutionFinding] = Field(
        default_factory=list
    )

class TCABatchRequest(BaseModel):
    market_data: TCAMarketDataInput
    order_ids: list[uuid.UUID] = Field(
        min_length=1,
        max_length=100
    )

class TCABatchOrderError(BaseModel):
    status_code: int
    detail: str

class TCABatchOrderResult(BaseModel):
    order_id: uuid.UUID
    result: TCAResponse | None = None
    error: TCABatchOrderError | None = None


class TCABatchSummary(BaseModel):
    requested: int
    succeeded: int
    failed: int

class TCABatchResponse(BaseModel):
    summary: TCABatchSummary
    results: list[TCABatchOrderResult]


class TCAResponse(BaseModel):
    order: TCAOrderResult
    benchmarks: TCABenchmarkResult
    execution: TCAExecutionResult
    slippage: TCASlippageResult
    implementation_shortfall: TCAImplementationShortfallResult
    market_impact: TCAMarketImpactResult
    execution_quality: TCAExecutionQualityResult | None = None
    execution_quality_unavailable_reason: str | None = None
    execution_diagnoses: TCAExecutionDiagnosesResult | None = None
    execution_diagnoses_unavailable_reason: str | None = None
    execution_recommendations: list[TCAExecutionRecommendationItem] = Field(default_factory=list)
    execution_evidence_set: TCAExecutionEvidenceSet | None = None
    is_fully_filled: bool