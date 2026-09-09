from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.execution_fill import ExecutionFill 
from app.models.execution_order import ExecutionOrder
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository


class ExecutionService:

    def __init__(self, db: Session):
        self.db = db
        self.order_repository = ExecutionOrderRepository(db)
        self.fill_repository = ExecutionFillRepository(db)


    def create_order(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        created_by: uuid.UUID,
        external_order_id: str | None,
        client_order_id: str | None,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        limit_price: float | None,
        strategy: str | None,
        algorithm: str | None,
        venue: str | None,
        order_status: str,
        submitted_at: datetime,
        completed_at: datetime | None,
    ) -> ExecutionOrder:

        if external_order_id:
            existing = self.order_repository.get_by_external_order_id(
                external_order_id=external_order_id,
                organization_id=organization_id,
                project_id=project_id,
            )

            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Execution order with this external_order_id already exists."
                )

        if client_order_id:
            existing = self.order_repository.get_by_client_order_id(
                client_order_id=client_order_id,
                organization_id=organization_id,
                project_id=project_id,
            )

            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Execution order with this client_order_id already exists",
                )

        return self.order_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            external_order_id=external_order_id,
            client_order_id=client_order_id,
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            strategy=strategy,
            algorithm=algorithm,
            venue=venue,
            status=order_status,
            submitted_at=submitted_at,
            completed_at=completed_at,
        )


    def create_fill(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        external_fill_id: str | None,
        price: float,
        quantity: float,
        venue: str | None,
        executed_at: datetime,
        commission: float | None,
        fees: float | None,
    ) -> ExecutionFill:

        order = self.order_repository.get_by_id_in_project_for_update(
            order_id=order_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution order not found."
            )

        if order.status in {
            "cancelled",
            "rejected",
            "filled",
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot add fill to order with status '{order.status}'.",
            )

        if external_fill_id:
            existing = self.fill_repository.get_by_external_fill_id(
                external_fill_id=external_fill_id,
                execution_order_id=order.id,
            )

            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Execution fill with this external_fill_id already exists."
                )

        existing_fills = self.fill_repository.list_by_order(
            execution_order_id=order.id,
        )

        filled_quantity = sum(
            float(fill.quantity)
            for fill in existing_fills
        )

        new_filled_quantity = filled_quantity + quantity

        if new_filled_quantity > float(order.quantity):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Fill quantity exceeds remaining order quantity. "
                    f"Order quantity={float(order.quantity)}, "
                    f"already filled={filled_quantity}, "
                    f"requested fill={quantity}"
                ),
            )

        try:
            fill = self.fill_repository.create(
                execution_order_id=order.id,
                external_fill_id=external_fill_id,
                price=price,
                quantity=quantity,
                venue=venue,
                executed_at=executed_at,
                commission=commission,
                fees=fees,
            )

            new_filled_quantity = filled_quantity + quantity

            if new_filled_quantity == float(order.quantity):
                self.order_repository.update_status(
                    order=order,
                    status="filled",
                    completed_at=datetime.now(timezone.utc),
                )

            else:
                self.order_repository.update_status(
                    order=order,
                    status="partially_filled",
                    completed_at=None,
                )

            self.db.commit()

            return fill

        except Exception:
            self.db.rollback()
            raise