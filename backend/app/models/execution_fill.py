from __future__ import annotations

import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ExecutionFill(Base):
    __tablename__ = "execution_fills"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_execution_fill_quantity_positive",
        ),
        CheckConstraint(
            "price >= 0",
            name="ck_execution_fill_price_non_negative",
        ),
        CheckConstraint(
            "commission IS NULL OR commission >= 0",
            name="ck_execution_fill_commission_non_negative",
        ),
        CheckConstraint(
            "fees IS NULL OR fees >= 0",
            name="ck_execution_fill_fees_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    execution_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "execution_orders.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    external_fill_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    price: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    quantity: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    venue: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    commission: Mapped[float | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )

    fees: Mapped[float | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    order: Mapped["ExecutionOrder"] = relationship(
        "ExecutionOrder",
        back_populates="fills",
    )