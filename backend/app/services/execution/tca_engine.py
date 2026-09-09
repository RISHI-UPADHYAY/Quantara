from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status

from app.models.execution_fill import ExecutionFill
from app.models.execution_order import ExecutionOrder
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository


class TCAEngine:

    def __init__(
        self,
        order_repository: ExecutionOrderRepository,
        fill_repository: ExecutionFillRepository,
    ):
        self.order_repository = order_repository
        self.fill_repository = fill_repository


    def calculate_execution_statistics(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
    ) -> dict:

        order = self.order_repository.get_by_id_in_project(
            order_id=order_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution order not found."
            )

        fills = self.fill_repository.list_by_order(
            execution_order_id=order.id,
        )

        if not fills:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Cannot calculate TCA for an order withn no fills."
            )

        order_quantity = Decimal(str(order.quantity))

        executed_quantity = sum(
            (Decimal(str(fill.quantity)) for fill in fills),
            Decimal("0"),
        )

        gross_notional = sum(
            (
                Decimal(str(fill.price))
                * Decimal(str(fill.quantity))
                for fill in fills
            ),
            Decimal("0"),
        )

        commission = sum(
            (
                Decimal(str(fill.commission))
                for fill in fills
                if fill.commission is not None
            ),
            Decimal("0"),
        )

        fees = sum(
            (
                Decimal(str(fill.fees))
                for fill in fills
                if fill.fees is not None
            ),
            Decimal("0"),
        )

        if executed_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Executed quantity must be greater then zero."
            )

        average_execution_price = (
            gross_notional / executed_quantity
        )

        total_cost = commission + fees

        cost_per_share = total_cost / executed_quantity

        net_execution_cost = gross_notional + total_cost

        remaining_quantity = (
            order_quantity - executed_quantity
        )

        return {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side,
            "ordered_quantity": float(order_quantity),
            "executed_quantity": float(executed_quantity),
            "remaining_quantity": float(remaining_quantity),
            "fill_count": len(fills),
            "average_execution_price": float(average_execution_price),
            "execution_vwap": float(average_execution_price),
            "gross_notional": float(gross_notional),
            "commission": float(commission),
            "fees": float(fees),
            "cost_per_share": float(cost_per_share),
            "net_execution_cost": float(net_execution_cost),
            "is_fully_filled": executed_quantity == order_quantity,
        }