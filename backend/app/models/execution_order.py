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


class ExecutionOrder(Base): 
    __tablename__ = "execution_orders"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_execution_order_quantity_positive",
        ),
        CheckConstraint(
            "limit_price IS NULL OR limit_price >= 0",
            name="ck_execution_order_limit_price_non_negative",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "projects.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    external_order_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    client_order_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    quantity: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    order_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    limit_price: Mapped[float | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )

    strategy: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    algorithm: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    venue: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    fills: Mapped[list["ExecutionFill"]] = relationship(
        "ExecutionFill",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="ExecutionFill.executed_at",
    )