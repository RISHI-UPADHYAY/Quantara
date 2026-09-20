from __future__ import annotations

from pathlib import Path

import csv
import json

import uuid
from datetime import datetime, timezone

from io import StringIO

from typing import Literal

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.dependencies.auth import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.organization import require_organization_role
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.models.organization_member import OrganizationMember
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.repositories.execution_review_issue_repository import ExecutionReviewIssueRepository
from app.schemas.execution import (
    ExecutionFillCreateRequest,
    ExecutionFillResponse,
    ExecutionOrderCreateRequest,
    ExecutionOrderResponse,
)
from app.schemas.tca import (
    TCARequest, 
    TCAResponse,
    TCABatchRequest,
    TCABatchOrderError,
    TCABatchOrderResult,
    TCABatchSummary,
    TCABatchResponse,
    TCABatchOutlierFlag,
    TCAPreflightResponse,
    TCAPreflightSummary,
    ExecutionReviewResponse,
    ExecutionReviewQueueResponse,
    ExecutionReviewQueueItem,
    ExecutionReviewUpdateRequest,
    ExecutionReviewInvestigationResponse,
)
from app.services.execution import (
    ExecutionService, 
    TCAEngine, 
    ExecutionMarketDataLoader, 
    ExecutionReviewService,
)
from app.services.execution.tca_preflight import TCAPreflightService
from app.services.execution.execution_review_persistence_service import ExecutionReviewPersistenceService


ALLOWED_REVIEW_TRANSITIONS = {
    "OPEN": {"ACKNOWLEDGED", "IN_REVIEW", "IGNORED"},
    "ACKNOWLEDGED": {"IN_REVIEW", "RESOLVED", "IGNORED"},
    "IN_REVIEW": {"RESOLVED", "IGNORED"},
    "RESOLVED": set(),
    "IGNORED": set(),
}


router = APIRouter()

@router.post(
    "/{organization_id}/projects/{project_id}/execution/orders",
    response_model=ExecutionOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_execution_order(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    request: ExecutionOrderCreateRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    service = ExecutionService(db)

    return service.create_order(
        organization_id=organization_id,
        project_id=project_id,
        created_by=membership.user_id,
        external_order_id=request.external_order_id,
        client_order_id=request.client_order_id,
        symbol=request.symbol,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=request.limit_price,
        strategy=request.strategy,
        algorithm=request.algorithm,
        venue=request.venue,
        order_status=request.status,
        submitted_at=request.submitted_at,
        completed_at=request.completed_at,
    )



@router.get(
    "/{organization_id}/projects/{project_id}/execution/orders",
    response_model=list[ExecutionOrderResponse],
    status_code=status.HTTP_200_OK,
)
def list_execution_orders(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    symbol: str | None = Query(default=None),
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    repository = ExecutionOrderRepository(db)

    if symbol:
        return repository.list_by_symbol(
            organization_id=organization_id,
            project_id=project_id,
            symbol=symbol.upper(),
        )

    if status_filter:
        return repository.list_by_status(
            organization_id=organization_id,
            project_id=project_id,
            status=status_filter,
        )

    return repository.list_by_project(
        organization_id=organization_id,
        project_id=project_id,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/execution/orders/{order_id}",
    response_model=ExecutionOrderResponse,
    status_code=status.HTTP_200_OK,
)
def get_execution_order(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    order_id: uuid.UUID ,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    repository = ExecutionOrderRepository(db)

    order = repository.get_by_id_in_project(
        order_id=order_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution order not found",
        )

    return order


@router.patch(
    "/{organization_id}/projects/{project_id}/execution/orders/{order_id}/status",
    response_model=ExecutionOrderResponse,
    status_code=status.HTTP_200_OK,
)
def update_execution_order_status(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    order_id: uuid.UUID,
    new_status: Literal[
        "pending",
        "open",
        "partially_filled",
        "filled",
        "cancelled",
        "rejected",
    ] = Query(
        ...,
        min_length=1,
        max_length=30,
    ),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
): 

    repository = ExecutionOrderRepository(db)

    order = repository.get_by_id_in_project(
        organization_id=organization_id,
        project_id=project_id,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution order not found",
        )

    completed_at = None

    if new_status in {
        "filled",
        "cancelled",
        "rejected",
    }: 
        completed_at = datetime.now(timezone.utc)

    return repository.update_status(
        order=order,
        status=new_status,
        completed_at=completed_at,
    )


@router.post(
    "/{organization_id}/projects/{project_id}/execution/orders/{order_id}/fills",
    response_model=ExecutionFillResponse,
    status_code=status.HTTP_201_CREATED,    
)
def create_execution_fill(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    order_id: uuid.UUID,
    request: ExecutionFillCreateRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    service = ExecutionService(db)

    return service.create_fill(
        organization_id=organization_id,
        project_id=project_id,
        order_id=order_id,
        external_fill_id=request.external_fill_id,
        price=request.price,
        quantity=request.quantity,
        venue=request.venue,
        executed_at=request.executed_at,
        commission=request.commission,
        fees=request.fees,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/execution/orders/{order_id}/fills",
    response_model=list[ExecutionFillResponse],
    status_code=status.HTTP_200_OK,
)
def list_execution_fills(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    order_id: uuid.UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    order_repository = ExecutionOrderRepository(db)

    order = order_repository.get_by_id_in_project(
        order_id=order_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution order not found",
        )

    fill_repository = ExecutionFillRepository(db)

    return fill_repository.list_by_order(
        execution_order_id=order.id,
    )


def _build_tca_response(result: dict) -> dict:
    return {
        "order": {
            "order_id": result["order_id"],
            "symbol": result["symbol"],
            "side": result["side"],
            "ordered_quantity": result["ordered_quantity"],
            "executed_quantity": result["executed_quantity"],
            "remaining_quantity": result["remaining_quantity"],
            "fill_count": result["fill_count"],
        },
        "benchmarks": {
            "arrival_price": result["arrival_price"],
            "arrival_timestamp": result["arrival_timestamp"],
            "market_vwap": result["market_vwap"],
            "market_vwap_unavailable_reason": (
                result["market_vwap_unavailable_reason"]
            ),
            "market_twap": result["market_twap"],
        },
        "execution": {
            "average_execution_price": result["average_execution_price"],
            "execution_vwap": result["execution_vwap"],
            "gross_notional": result["gross_notional"],
            "commission": result["commission"],
            "fees": result["fees"],
            "cost_per_share": result["cost_per_share"],
            "net_execution_cost": result["net_execution_cost"],
        },
        "slippage": {
            "price": result["price_slippage"],
            "percentage": result["percentage_slippage"],
            "total": result["total_slippage"],
        },
        "implementation_shortfall": {
            "price_shortfall": result["price_shortfall"],
            "percentage_shortfall": result["percentage_shortfall"],
            "explicit_costs": result["explicit_costs"],
            "total_shortfall": result["total_shortfall"],
        },
        "market_impact": {
            "measure": "arrival_to_end_market_price_change",
            "interpretation": (
                "Market movement during the execution window; "
                "this does not establish causal market impact from the order."
            ),
            "end_market_price": result["end_market_price"],
            "market_impact_timestamp": result["market_impact_timestamp"],
            "impact_per_share": result["market_impact_per_share"],
            "percentage": result["percentage_market_impact"],
            "total": result["total_market_impact"],
        },
        "execution_quality": result["execution_quality"],
        "execution_quality_unavailable_reason": (
            result.get("execution_quality_unavailable_reason")
        ),
        "execution_diagnoses": result["execution_diagnoses"],
        "execution_diagnoses_unavailable_reason": (
            result.get("execution_diagnoses_unavailable_reason")
        ),
        "execution_evidence_set": result["execution_evidence_set"],
        "execution_recommendations": result["execution_recommendations"],
        "is_fully_filled": result["is_fully_filled"],
    }

#Quantara v1 review heuristics. Percentage values are expressed in percentage points (e.g. 0.10 means 0.10% not 10%).
BATCH_OUTLIER_THRESHOLDS = {
    "slippage_percentage": 0.10,
    "vwap_deviation_percentage": 0.10,
    "shortfall_percentage": 0.15,
    "explicit_cost_percentage": 0.05,
}

def _build_batch_outlier_flags(
    response_data: dict,
) -> list[TCABatchOutlierFlag]:

    flags: list[TCABatchOutlierFlag] = []

    order = response_data["order"]
    benchmarks = response_data["benchmarks"]
    execution = response_data["execution"]
    slippage = response_data["slippage"]
    shortfall = response_data["implementation_shortfall"]

    def add_flag(
        code: str,
        metric: str,
        observed_value: float,
        threshold: float,
        reason: str,
    ) -> None:
        flags.append(
            TCABatchOutlierFlag(
                code=code,
                metric=metric,
                observed_value=observed_value,
                threshold=threshold,
                reason=reason,
            )
        )

    #Slippage is already side-aware in the TCA result.
    slippage_pct = slippage["percentage"]
    threshold = BATCH_OUTLIER_THRESHOLDS["slippage_percentage"]

    if slippage_pct is not None and slippage_pct > threshold:
        add_flag(
            code="HIGH_SLIPPAGE",
            metric="slippage_percentage",
            observed_value=slippage_pct,
            threshold=threshold,
            reason=(
                f"Adverse slippage of {slippage_pct:.4f}% exceeds "
                f"the v1 review threshold of {threshold:.4f}%."
            ),
        )

    #Comapare execution VWAP with market VWAP, accounting for side.
    market_vwap = benchmarks["market_vwap"]
    execution_vwap = execution["execution_vwap"]
    side = order["side"].lower()

    if (
        market_vwap is not None
        and market_vwap > 0
        and execution_vwap is not None
        and side in {"buy", "sell"}
    ):
        direction = 1 if side == "buy" else -1
        vwap_deviation_pct = (
            direction
            * (execution_vwap - market_vwap)
            / market_vwap
            * 100
        )

        threshold = BATCH_OUTLIER_THRESHOLDS["vwap_deviation_percentage"]

        if vwap_deviation_pct > threshold:
            add_flag(
                code="WORSE_THAN_MARKET_VWAP",
                metric="vwap_deviation_percentage",
                observed_value=vwap_deviation_pct,
                threshold=threshold,
                reason=(
                    f"Execution was {vwap_deviation_pct:.4f}% worse "
                    f"than market VWAP, exceeding the v1 review "
                    f"threshold of {threshold:.4f}%."
                ),
            )

    shortfall_pct = shortfall["percentage_shortfall"]
    threshold = BATCH_OUTLIER_THRESHOLDS["shortfall_percentage"]

    if shortfall_pct is not None and shortfall_pct > threshold:
        add_flag(
            code="HIGH_IMPLEMENTATION_SHORTFALL",
            metric="shortfall_percentage",
            observed_value=shortfall_pct,
            threshold=threshold,
            reason=(
                f"Implementation shortfall of {shortfall_pct:.4f}% "
                f"exceeds the v1 review threshold of "
                f"{threshold:.4f}%."
            ),
        )

    gross_notional = execution["gross_notional"]
    commission = execution["commission"] or 0.0
    fees = execution["fees"] or 0.0
    explicit_costs = commission + fees

    if gross_notional is not None and gross_notional > 0:
        explicit_cost_pct = explicit_costs / gross_notional * 100
        threshold = BATCH_OUTLIER_THRESHOLDS["explicit_cost_percentage"]

        if explicit_cost_pct > threshold:
            add_flag(
                code="HIGH_EXPLICIT_COSTS",
                metric="explicit_cost_percentage",
                observed_value=explicit_cost_pct,
                threshold=threshold,
                reason=(
                    f"Explicit costs of {explicit_cost_pct:.4f}% of "
                    f"gross notional exceed the v1 review threshold "
                    f"of {threshold:.4f}%."
                ),
            )

    return flags


@router.post(
    "/{organization_id}/projects/{project_id}/execution/orders/{order_id}/tca",
    response_model=TCAResponse,
    status_code=status.HTTP_200_OK,
)
def calculate_execution_tca(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    order_id: uuid.UUID,
    request: TCARequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    dataset_repository = DatasetRepository(db)
    dataset_version_repository = DatasetVersionRepository(db)

    dataset = dataset_repository.get_by_id_in_project(
        dataset_id=request.market_data.dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset not found."
        )

    dataset_version = dataset_version_repository.get_by_id_for_dataset(
        dataset_version_id=request.market_data.dataset_version_id,
        dataset_id=dataset.id,
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset version not found."
        )

    if dataset_version.storage_uri is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Market-data dataset version has no storage URI."
        )

    market_data = ExecutionMarketDataLoader(
        storage_root=(
            Path(__file__).resolve().parents[4] / "storage"
        ),
    ).load(dataset_version.storage_uri)

    order_repository = ExecutionOrderRepository(db)
    fill_repository = ExecutionFillRepository(db)

    engine = TCAEngine(
        order_repository=order_repository,
        fill_repository=fill_repository,
    )

    result = engine.calculate_execution_statistics(
        organization_id=organization_id,
        project_id=project_id,
        order_id=order_id,
        market_data=market_data,
    )

    return _build_tca_response(result)


@router.post(
    "/{organization_id}/projects/{project_id}/execution/tca/batch",
    response_model=TCABatchResponse,
    status_code=status.HTTP_200_OK,
)
def calculate_execution_tca_batch(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    request: TCABatchRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    #Reject duplicate IDs rather than analyzing the same order twice.
    if len(request.order_ids) != len(set(request.order_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="order_ids must not contain duplicates."
        )

    dataset_repository = DatasetRepository(db)
    dataset_version_repository = DatasetVersionRepository(db)

    dataset = dataset_repository.get_by_id_in_project(
        dataset_id=request.market_data.dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset not found.",
        )

    dataset_version = dataset_version_repository.get_by_id_for_dataset(
        dataset_version_id=request.market_data.dataset_version_id,
        dataset_id=dataset.id,
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset version not found.",
        )

    if dataset_version.storage_uri is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Market-data dataset version has no storage URI.",
        )

    #Load market data once for the entire batch
    market_data = ExecutionMarketDataLoader(
        storage_root=(
            Path(__file__).resolve().parents[4] / "storage"
        ),
    ).load(dataset_version.storage_uri)

    engine = TCAEngine(
        order_repository=ExecutionOrderRepository(db),
        fill_repository=ExecutionFillRepository(db),
    )

    results: list[TCABatchOrderResult] = []
    succeeded = 0
    failed = 0

    total_ordered_quantity = 0.0
    total_executed_quantity = 0.0
    total_gross_notional = 0.0
    total_explicit_costs = 0.0

    fully_filled = 0
    partially_filled = 0

    orders_with_outliers = 0
    total_outlier_flags = 0
    outlier_counts_by_code: dict[str, int] = {}

    for order_id in request.order_ids:
        try:
            result = engine.calculate_execution_statistics(
                organization_id=organization_id,
                project_id=project_id,
                order_id=order_id,
                market_data=market_data,
            )

            response_data = _build_tca_response(result)
            outlier_flags = _build_batch_outlier_flags(response_data)

            if outlier_flags:
                orders_with_outliers += 1

            total_outlier_flags += len(outlier_flags)

            for flag in outlier_flags:
                outlier_counts_by_code[flag.code] = (
                    outlier_counts_by_code.get(flag.code, 0) + 1
                ) 

            results.append(
                TCABatchOrderResult(
                    order_id=order_id,
                    result=response_data,
                    error=None,
                    outlier_flags=outlier_flags,
                )
            )

            succeeded += 1

            total_ordered_quantity += response_data["order"]["ordered_quantity"]
            total_executed_quantity += response_data["order"]["executed_quantity"]
            total_gross_notional += response_data["execution"]["gross_notional"]
            commission = response_data["execution"]["commission"] or 0.0
            fees = response_data["execution"]["fees"] or 0.0
            total_explicit_costs += commission + fees

            if response_data["is_fully_filled"]:
                fully_filled += 1

            elif response_data["order"]["executed_quantity"] > 0:
                partially_filled += 1

        except HTTPException as exc:
            #Expected per-order errors (e.g. order not found or no fills)
            #should not prevent the remaining orders from being analyzed.
            results.append(
                TCABatchOrderResult(
                    order_id=order_id,
                    error=TCABatchOrderError(
                        status_code=exc.status_code,
                        detail=str(exc.detail),
                    ),
                )
            )
            failed += 1

    return TCABatchResponse(
        summary=TCABatchSummary(
            requested=len(request.order_ids),
            succeeded=succeeded,
            failed=failed,
            total_ordered_quantity=total_ordered_quantity,
            total_executed_quantity=total_executed_quantity,
            total_gross_notional=total_gross_notional,
            total_explicit_costs=total_explicit_costs,
            fully_filled=fully_filled,
            partially_filled=partially_filled,
            orders_with_outliers=orders_with_outliers,
            total_outlier_flags=total_outlier_flags,
            outlier_counts_by_code=outlier_counts_by_code,
        ),
        results=results,
    )


@router.post(
    "/{organization_id}/projects/{project_id}/execution/tca/batch/export",
    status_code=status.HTTP_200_OK,
)
def export_execution_tca_batch_csv(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    request: TCABatchRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    batch_response = calculate_execution_tca_batch(
        organization_id=organization_id,
        project_id=project_id,
        request=request,
        membership=membership,
        db=db,
    )

    #The batch response is a Pydantic model.
    if hasattr(batch_response, "model_dump"):
        batch_data = batch_response.model_dump(mode="json")

    else:
        batch_data = batch_response.dict()

    output = StringIO()
    writer = csv.writer(output)

    headers = [
        "order_id",
        "status",
        "error_status_code",
        "error_detail",
        "symbol",
        "side",
        "ordered_quantity",
        "executed_quantity",
        "remaining_quantity",
        "fill_count",
        "arrival_price",
        "arrival_timestamp",
        "market_vwap",
        "market_vwap_unavailable_reason",
        "market_twap",
        "average_execution_price",
        "execution_vwap",
        "gross_notional",
        "commission",
        "fees",
        "cost_per_share",
        "net_execution_cost",
        "slippage_price",
        "slippage_percentage",
        "total_slippage",
        "price_shortfall",
        "percentage_shortfall",
        "explicit_costs",
        "total_shortfall",
        "end_market_price",
        "market_impact_timestamp",
        "impact_per_share",
        "market_impact_percentage",
        "total_market_impact",
        "execution_quality",
        "execution_diagnoses",
        "execution_evidence_set",
        "execution_recommendations",
        "outlier_flags",
        "outlier_count",
        "is_fully_filled",
    ]
    writer.writerow(headers)

    def json_cell(value):
        """Keep nested objects in a single CSV cell."""
        if value is None:
            return ""

        return json.dumps(value, ensure_ascii=False)

    def safe_cell(value):
        """
        Reduce spreadsheet formula-injection risk for text cells.
        Numeric values remain numeric.
        """

        if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + value

        return value

    for item in batch_data["results"]:
        result = item.get("result")
        error = item.get("error")

        if result is None:
            writer.writerow([
                safe_cell(str(item.get("order_id", ""))),
                "failed",
                error.get("status_code", "") if error else "",
                safe_cell(error.get("detail", "") if error else ""),
                *([""] * (len(headers) - 4)),
            ])

            continue

        order = result.get("order", {})
        benchmarks = result.get("benchmarks", {})
        execution = result.get("execution", {})
        slippage = result.get("slippage", {})
        shortfall = result.get("implementation_shortfall", {})
        market_impact = result.get("market_impact", {})

        outlier_flags = item.get("outlier_flags") or []

        writer.writerow([
            safe_cell(str(item.get("order_id", ""))),
            "succeeded",
            "",
            "",
            safe_cell(order.get("symbol", "")),
            safe_cell(order.get("side", "")),
            order.get("ordered_quantity", ""),
            order.get("executed_quantity", ""),
            order.get("remaining_quantity", ""),
            order.get("fill_count", ""),
            benchmarks.get("arrival_price", ""),
            benchmarks.get("arrival_timestamp", ""),
            benchmarks.get("market_vwap", ""),
            safe_cell(benchmarks.get("market_vwap_unavailable_reason") or ""),
            benchmarks.get("market_twap", ""),
            execution.get("average_execution_price", ""),
            execution.get("execution_vwap", ""),
            execution.get("gross_notional", ""),
            execution.get("commission", ""),
            execution.get("fees", ""),
            execution.get("cost_per_share", ""),
            execution.get("net_execution_cost", ""),
            slippage.get("price", ""),
            slippage.get("percentage", ""),
            slippage.get("total", ""),
            shortfall.get("price_shortfall", ""),
            shortfall.get("percentage_shortfall", ""),
            shortfall.get("explicit_costs", ""),
            shortfall.get("total_shortfall", ""),
            market_impact.get("end_market_price", ""),
            market_impact.get("market_impact_timestamp", ""),
            market_impact.get("impact_per_share", ""),
            market_impact.get("percentage", ""),
            market_impact.get("total", ""),
            json_cell(result.get("execution_quality")),
            json_cell(result.get("execution_diagnoses")),
            json_cell(result.get("execution_evidence_set")),
            json_cell(result.get("execution_recommendations")),
            json_cell(outlier_flags),
            len(outlier_flags),
            result.get("is_fully_filled", ""),
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="quantara_batch_tca.csv"'
            )
        },
    )


@router.post(
    "/{organization_id}/projects/{project_id}/execution/tca/batch/preflight",
    response_model=TCAPreflightResponse,
    status_code=status.HTTP_200_OK,
)
def preflight_execution_tca_batch(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    request: TCABatchRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    

    if len(request.order_ids) != len(set(request.order_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="order_ids must not contain duplicates.",
        )

    dataset_repository = DatasetRepository(db)
    dataset_version_repository = DatasetVersionRepository(db)

    dataset = dataset_repository.get_by_id_in_project(
        dataset_id=request.market_data.dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset not found.",
        )

    dataset_version = dataset_version_repository.get_by_id_for_dataset(
        dataset_version_id=request.market_data.dataset_version_id,
        dataset_id=dataset.id,
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset version not found.",
        )

    if dataset_version.storage_uri is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Market-data dataset version has no storage URI.",
        )

    market_data = ExecutionMarketDataLoader(
        storage_root=Path(__file__).resolve().parents[4] / "storage",
    ).load(dataset_version.storage_uri)

    service = TCAPreflightService(
        order_repository=ExecutionOrderRepository(db),
        fill_repository=ExecutionFillRepository(db),
    )

    results = [
        service.check_order(
            organization_id=organization_id,
            project_id=project_id,
            order_id=order_id,
            market_data=market_data,
        )
        for order_id in request.order_ids
    ]

    return TCAPreflightResponse(
        summary=TCAPreflightSummary(
            requested=len(results),
            ready=sum(r.status == "READY" for r in results),
            ready_with_warnings=sum(
                r.status == "READY_WITH_WARNINGS" for r in results
            ),
            blocked=sum(
                r.status == "BLOCKED" for r in results
            ),
            total_errors=sum(
                f.severity == "ERROR"
                for r in results
                for f in r.findings
            ),
            total_warnings=sum(
                f.severity == "WARNING"
                for r in results
                for f in r.findings
            ),
        ),
        results=results,
    )


@router.post(
    "/{organization_id}/projects/{project_id}/execution/tca/batch/review",
    response_model=ExecutionReviewResponse,
    status_code=status.HTTP_200_OK,
)
def review_execution_tca_batch(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    request: TCABatchRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    batch_response = calculate_execution_tca_batch(
        organization_id=organization_id,
        project_id=project_id,
        request=request,
        membership=membership,
        db=db,
    )

    review_service = ExecutionReviewService()

    review_response = (
        review_service.build_review_queue(
            batch_response=batch_response,
        )
    )

    persistence_service = ExecutionReviewPersistenceService(db)

    persistence_service.sync_review_queue(
        organization_id=organization_id,
        project_id=project_id,
        dataset_id=request.market_data.dataset_id,
        dataset_version_id=request.market_data.dataset_version_id,
        items=review_response.items,
    )

    return review_response


@router.get(
    "/{organization_id}/projects/{project_id}/execution/review",
    response_model=ExecutionReviewQueueResponse,
    status_code=status.HTTP_200_OK,
)
def list_execution_review_queue(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    status_filter: Literal[
        "OPEN",
        "ACKNOWLEDGED",
        "IN_REVIEW",
        "RESOLVED",
        "IGNORED",
    ] | None = Query(
        default=None,
        alias="status",
    ),
    severity: Literal[
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] | None = Query(
        default=None,
    ),
    issue_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    order_id: uuid.UUID | None = Query(default=None),
    assigned_to: uuid.UUID | None = Query(default=None),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    repository = ExecutionReviewIssueRepository(db)

    issues = repository.list_for_project(
        organization_id=organization_id,
        project_id=project_id,
        status=status_filter,
        severity=severity,
        issue_code=issue_code,
        order_id=order_id,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset,
    )

    total = repository.count_for_project(
        organization_id=organization_id,
        project_id=project_id,
        status=status_filter,
        severity=severity,
        issue_code=issue_code,
        order_id=order_id,
        assigned_to=assigned_to,
    )

    items = [
        ExecutionReviewQueueItem.model_validate(issue)
        for issue in issues
    ]

    return ExecutionReviewQueueResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{organization_id}/projects/{project_id}/execution/review/{issue_id}",
    response_model=ExecutionReviewQueueItem,
    status_code=status.HTTP_200_OK,
)
def get_execution_review_issue(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    repository = ExecutionReviewIssueRepository(db)

    issue = repository.get_by_id(
        organization_id=organization_id,
        project_id=project_id,
        issue_id=issue_id,
    )

    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution review issue not found.",
        )

    return ExecutionReviewQueueItem.model_validate(issue)


@router.patch(
    "/{organization_id}/projects/{project_id}/execution/review/{issue_id}",
    response_model=ExecutionReviewQueueItem,
    status_code=status.HTTP_200_OK,
)
def update_execution_review_issue(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    update: ExecutionReviewUpdateRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    repository = ExecutionReviewIssueRepository(db)

    issue = repository.get_by_id(
        organization_id=organization_id,
        project_id=project_id,
        issue_id=issue_id,
    )

    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution review issue not found.",
        )

    if update.status is None and update.assigned_to is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one workflow field must be provided.",
        )

    if update.assigned_to is not None:
        assigned_membership = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == update.assigned_to,
            )
        )

        if assigned_membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned user is not a member of this organization.",
            )

        if assigned_membership.role not in {
            ROLE_ADMIN,
            ROLE_ANALYST,
        }:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Execution review issues can only be assigned to organization "
                    "admins or analysts."
                ),
            )

    if update.status is not None:
        current_status = issue.status

        if update.status != current_status:
            allowed_statuses = ALLOWED_REVIEW_TRANSITIONS[current_status]

            if update.status not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Invalid review status transition: "
                        f"{current_status} -> {update.status}" 
                    ),
                )

    resolved_at = None

    if update.status in {"RESOLVED", "IGNORED"}:
        resolved_at = datetime.now(timezone.utc)

    updated_issue = repository.update_workflow(
        issue=issue,
        status=update.status,
        assigned_to=update.assigned_to,
        resolved_at=resolved_at,
    )

    repository.commit()

    repository.db.refresh(updated_issue)

    return ExecutionReviewQueueItem.model_validate(updated_issue)


@router.get(
    "/{organization_id}/projects/{project_id}/execution/review/{issue_id}/investigation",
    response_model=ExecutionReviewInvestigationResponse,
    status_code=status.HTTP_200_OK,
)
def get_execution_review_investigation(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    issue_id: uuid.UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    review_repository = ExecutionReviewIssueRepository(db)

    issue = review_repository.get_by_id(
        organization_id=organization_id,
        project_id=project_id,
        issue_id=issue_id,
    )

    if issue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution review issue not found.",
        )

    order_repository = ExecutionOrderRepository(db)

    order = order_repository.get_by_id_in_project(
        organization_id=organization_id,
        project_id=project_id,
        order_id=issue.order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution order not found.",
        )

    fill_repository = ExecutionFillRepository(db)

    fills = fill_repository.list_by_order(
        execution_order_id=order.id,
    )

    dataset_repository = DatasetRepository(db)
    dataset_version_repository = DatasetVersionRepository(db)

    dataset = dataset_repository.get_by_id_in_project(
        dataset_id=issue.dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset not found.",
        )

    dataset_version = (
        dataset_version_repository.get_by_id_for_dataset(
            dataset_version_id=issue.dataset_version_id,
            dataset_id=dataset.id,
        )
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Market-data dataset version not found.",
        )

    if dataset_version.storage_uri is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Market-data dataset version has no storage URI.",
        )

    market_data = ExecutionMarketDataLoader(
        storage_root=Path(
            __file__
        ).resolve().parents[4] / "storage",
    ).load(
        dataset_version.storage_uri,
    )

    engine = TCAEngine(
        order_repository=order_repository,
        fill_repository=fill_repository,
    )

    result = engine.calculate_execution_statistics(
        organization_id=organization_id,
        project_id=project_id,
        order_id=order.id,
        market_data=market_data,
    )

    tca_response = TCAResponse.model_validate(
        _build_tca_response(result)
    )

    return ExecutionReviewInvestigationResponse(
        issue=ExecutionReviewQueueItem.model_validate(issue),
        order=ExecutionOrderResponse.model_validate(order),
        fills=[
            ExecutionFillResponse.model_validate(fill)
            for fill in fills
        ],
        tca=tca_response,
    )