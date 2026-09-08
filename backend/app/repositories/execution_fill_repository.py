from __future__ import annotations      

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.execution_fill import ExecutionFill
from app.models.execution_order import ExecutionOrder


class ExecutionFillRepository:

    def __init__(self, db: Session):
        self.db = db


    def create(
        self,
        *,
        execution_order_id: uuid.UUID,
        price: float,
        quantity: float,
        executed_at,
        external_fill_id: str | None = None,
        venue: str | None = None,
        commission: float | None = None,
        fees: float | None = None,
    ) -> ExecutionFill:

        fill = ExecutionFill(
            execution_order_id=execution_order_id,
            external_fill_id=external_fill_id,
            price=price,
            quantity=quantity,
            venue=venue,
            executed_at=executed_at,
            commission=commission,
            fees=fees,
        )

        self.db.add(fill)
        self.db.commit()
        self.db.refresh(fill)

        return fill


    def get_by_id(
        self,
        fill_id: uuid.UUID,
    ) -> ExecutionFill | None:

        statement = select(ExecutionFill).where(
            ExecutionFill.id == fill_id,
        )

        return self.db.scalar(statement)


    def get_by_id_for_order(
        self,
        *,
        fill_id: uuid.UUID,
        execution_order_id: uuid.UUID,
    ) -> ExecutionFill | None:

        statement = select(ExecutionFill).where(
            ExecutionFill.id == fill_id,
            ExecutionFill.execution_order_id == execution_order_id,
        )

        return self.db.scalar(statement)


    def get_by_external_fill_id(
        self,
        *,
        external_fill_id: str,
        execution_order_id: uuid.UUID,
    ) -> ExecutionFill | None:

        statement = select(ExecutionFill).where(
            ExecutionFill.external_fill_id == external_fill_id,
            ExecutionFill.execution_order_id == execution_order_id,
        )

        return self.db.scalar(statement)


    def list_by_order(
        self,
        *,
        execution_order_id: uuid.UUID,
    ) -> list[ExecutionFill]:

        statement = (
            select(ExecutionFill).where(
                ExecutionFill.execution_order_id == execution_order_id,
            ).order_by(
                ExecutionFill.executed_at.desc()
            )
        )

        return list(self.db.scalars(statement).all())


    def list_by_project(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[ExecutionFill]:

        statement = (
            select(ExecutionFill).join(
                ExecutionOrder,
                ExecutionOrder.id == ExecutionFill.execution_order_id,
            ).where(
                ExecutionOrder.organization_id == organization_id,
                ExecutionOrder.project_id == project_id,
            ).order_by(
                ExecutionFill.executed_at.desc()
            )
        )

        return list(self.db.scalars(statement).all())