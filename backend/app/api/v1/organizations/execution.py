from __future__ import annotations

from pathlib import Path

import uuid
from datetime import datetime, timezone

from typing import Literal

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.organization import require_organization_role
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.models.organization_member import OrganizationMember
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.schemas.execution import (
    ExecutionFillCreateRequest,
    ExecutionFillResponse,
    ExecutionOrderCreateRequest,
    ExecutionOrderResponse,
)
from app.schemas.tca import TCARequest, TCAResponse
from app.services.execution import ExecutionService, TCAEngine, ExecutionMarketDataLoader


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
        "is_fully_filled": result["is_fully_filled"],
    }