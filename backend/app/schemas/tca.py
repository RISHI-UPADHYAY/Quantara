from __future__ import annotations

import uuid

from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.schemas.execution import ExecutionOrderResponse, ExecutionFillResponse


FindingCategory = Literal[
    "COST_ISSUE",
    "EXECUTION_CONDITION",
    "POSITIVE_FINDING",
]

PreflightSeverity = Literal["ERROR", "WARNING", "INFO"]

PreflightStatus = Literal["READY", "READY_WITH_WARNINGS", "BLOCKED"]


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

class TCAPreflightFinding(BaseModel):
    code: str
    severity: PreflightSeverity
    message: str
    evidence: dict[str, str | int | float | bool] = Field(
        default_factory=dict
    )

class TCAPreflightOrderResult(BaseModel):
    order_id: uuid.UUID
    status: PreflightStatus
    findings: list[TCAPreflightFinding] = Field(
        default_factory=list
    )

class TCAPreflightSummary(BaseModel):
    requested: int
    ready: int 
    ready_with_warnings: int
    blocked: int
    total_errors: int
    total_warnings: int

class TCAPreflightResponse(BaseModel):
    summary: TCAPreflightSummary
    results: list[TCAPreflightOrderResult]

class TCABatchOrderError(BaseModel):
    status_code: int
    detail: str

class TCABatchOrderResult(BaseModel):
    order_id: uuid.UUID
    result: TCAResponse | None = None
    error: TCABatchOrderError | None = None
    outlier_flags: list[TCABatchOutlierFlag] = Field(
        default_factory=list
    )


class TCABatchSummary(BaseModel):
    requested: int
    succeeded: int
    failed: int

    total_ordered_quantity: float
    total_executed_quantity: float
    total_gross_notional: float
    total_explicit_costs: float

    fully_filled: int
    partially_filled: int

    orders_with_outliers: int
    total_outlier_flags: int
    outlier_counts_by_code: dict[str, int]

class TCABatchResponse(BaseModel):
    summary: TCABatchSummary
    results: list[TCABatchOrderResult]


class TCABatchOutlierFlag(BaseModel):
    code: str
    metric: str
    observed_value: float
    threshold: float
    reason: str


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


class ExecutionReviewIssue(BaseModel):
    code: str
    severity: Literal["MEDIUM", "HIGH", "CRITICAL"]
    metric: str
    observed_value: float
    threshold: float | None = None
    message: str
    evidence: dict[str, float] = Field(
        default_factory=dict
    )
    recommendations: list[str] = Field(
        default_factory=list
    )


class ExecutionReviewItem(BaseModel):
    order_id: uuid.UUID
    symbol: str
    side: str

    ordered_quantity: float
    executed_quantity: float

    gross_notional: float
    total_shortfall: float | None = None
    explicit_costs: float

    overall_status: str

    issues: list[ExecutionReviewIssue] = Field(
        default_factory=list
    )


class ExecutionReviewSummary(BaseModel):
    requested: int
    analyzed: int
    failed: int

    orders_requiring_attention: int

    orders_by_severity: dict[str, int] = Field(
        default_factory=dict
    )

    total_issues: int

    issues_by_severity: dict[str, int] = Field(
        default_factory=dict
    )

    issue_counts_by_code: dict[str, int] = Field(
        default_factory=dict
    )


class ExecutionReviewResponse(BaseModel):
    summary: ExecutionReviewSummary
    items: list[ExecutionReviewItem] = Field(
        default_factory=list
    )


class ExecutionReviewQueueItem(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID

    issue_code: str
    severity: Literal["MEDIUM", "HIGH", "CRITICAL"]
    status: Literal[
        "OPEN",
        "ACKNOWLEDGED",
        "IN_REVIEW",
        "RESOLVED",
        "IGNORED",
    ]

    metric: str
    observed_value: float
    threshold: float | None

    message: str
    evidence: dict
    recommendations: list

    assigned_to: uuid.UUID | None

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ExecutionReviewQueueResponse(BaseModel):
    items: list[ExecutionReviewQueueItem]
    total: int
    limit: int
    offset: int

class ExecutionReviewUpdateRequest(BaseModel):
    status: Literal[
        "OPEN",
        "ACKNOWLEDGED",
        "IN_REVIEW",
        "RESOLVED",
        "IGNORED",
    ] | None = None

    assigned_to: uuid.UUID | None = None


class ExecutionReviewInvestigationResponse(BaseModel):
    issue: ExecutionReviewQueueItem
    order: ExecutionOrderResponse
    fills: list[ExecutionFillResponse]

    tca: TCAResponse


class ExecutionReviewCommentCreateRequest(BaseModel):
    comment: str = Field(
        min_length=1,
        max_length=5000,
    )


class ExecutionReviewCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_issue_id: uuid.UUID
    author_id: uuid.UUID | None
    activity_type: str
    comment: str | None
    metadata: dict | None
    created_at: datetime

    @classmethod
    def from_activity(cls, activity):
        return cls(
            id=activity.id,
            review_issue_id=activity.review_issue_id,
            author_id=activity.author_id,
            activity_type=activity.activity_type,
            comment=activity.comment,
            metadata=activity.activity_metadata,
            created_at=activity.created_at,
        )


class ExecutionReviewCommentListResponse(BaseModel):
    items: list[ExecutionReviewCommentResponse]
    total: int