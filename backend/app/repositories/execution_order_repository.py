from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution_order import ExecutionOrder


class ExecutionOrderRepository:

    def __init__(self, db: Session):
        self.db = db


    def create(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        created_by: uuid.UUID,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str,
        submitted_at,
        external_order_id: str | None = None,
        client_order_id: str | None = None,
        limit_price: float | None = None,
        strategy: str | None = None,
        algorithm: str | None = None,
        venue: str | None = None,
        status: str = "pending",
        completed_at = None,
    ) -> ExecutionOrder:

        order = ExecutionOrder(
            organization_id=organization_id,
            project_id=project_id,
            external_order_id=external_order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            strategy=strategy,
            algorithm=algorithm,
            venue=venue,
            status=status,
            submitted_at=submitted_at,
            completed_at=completed_at,
            created_by=created_by,
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order


    def get_by_id(
        self,
        order_id: uuid.UUID,
    ) -> ExecutionOrder | None:

        statement = select(ExecutionOrder).where(
            ExecutionOrder.id == order_id
        )

        return self.db.scalar(statement)


    def get_by_id_in_project(
        self,
        *,
        order_id: uuid.UUID,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ExecutionOrder | None:

        statement = select(ExecutionOrder).where(
            ExecutionOrder.id == order_id,
            ExecutionOrder.organization_id == organization_id,
            ExecutionOrder.project_id == project_id,
        )

        return self.db.scalar(statement)


    def get_by_external_order_id(
        self,
        *,
        external_order_id: uuid.UUID,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ExecutionOrder | None:

        statement = select(ExecutionOrder).where(
            ExecutionOrder.external_order_id == external_order_id,
            ExecutionOrder.organization_id == organization_id,
            ExecutionOrder.project_id == project_id,
        ) 

        return self.db.scalar(statement)


    def get_by_client_order_id(
        self,
        *,
        client_order_id: str,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ExecutionOrder | None:

        statement = select(ExecutionOrder).where(
            ExecutionOrder.client_order_id == client_order_id,
            ExecutionOrder.organization_id == organization_id,
            ExecutionOrder.project_id == project_id,
        )

        return self.db.scalar(statement)


    def list_by_project(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[ExecutionOrder]:

        statement = (
            select(ExecutionOrder).where(
                ExecutionOrder.organization_id == organization_id,
                ExecutionOrder.project_id == project_id,
            ).order_by(
                ExecutionOrder.submitted_at.desc()
            )
        )

        return list(self.db.scalars(statement).all())


    def list_by_symbol(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        symbol: str,
    ) -> list[ExecutionOrder]:

        statement = (
            select(ExecutionOrder).where(
                ExecutionOrder.organization_id == organization_id,
                ExecutionOrder.project_id == project_id,
                ExecutionOrder.symbol == symbol,
            ).order_by(
                ExecutionOrder.submitted_at.desc()
            )
        )

        return list(self.db.scalars(statement).all())


    def list_by_status(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        status: str,
    ) -> list[ExecutionOrder]:

        statement = (
            select(ExecutionOrder).where(
                ExecutionOrder.organization_id == organization_id,
                ExecutionOrder.project_id == project_id,
                ExecutionOrder.status == status,
            ).order_by(
                ExecutionOrder.submitted_at.desc()
            )
        )

        return list(self.db.scalars(statement).all())


    def update_status(
        self,
        *,
        order: ExecutionOrder,
        status: str,
        completed_at = None,
    ) -> ExecutionOrder:

        order.status = status
        order.completed_at = completed_at

        self.db.commit()
        self.db.refresh(order)

        return order