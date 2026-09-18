from __future__ import annotations

import uuid

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class ExecutionReviewIssue(Base):

    __tablename__ = "execution_review_issues"

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "order_id",
            "dataset_version_id",
            "issue_code",
            name="uq_execution_review_issue_order_version_code",
        ),
        CheckConstraint(
            "severity IN ('MEDIUM', 'HIGH', 'CRITICAL')",
            name="ck_execution_review_issue_order_version_code",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'ACKNOWLEDGED', 'IN_REVIEW', 'RESOLVED', 'IGNORED')",
            name="ck_execution_review_issue_status",
        ),
        CheckConstraint(
            "threshold IS NULL OR threshold >= 0",
            name="ck_execution_review_issue_threshold_non_negative",
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

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "execution_orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "datasets.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "dataset_versions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    issue_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="OPEN",
        index=True,
    )

    metric: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    observed_value: Mapped[float] = mapped_column(
        Numeric(20, 8),
        nullable=False,
    )

    threshold: Mapped[float | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evidence: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    recommendations: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    order: Mapped["ExecutionOrder"] = relationship(
        "ExecutionOrder",
        back_populates="review_issues",
    )