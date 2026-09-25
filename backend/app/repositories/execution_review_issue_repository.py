from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.execution_review_issue import ExecutionReviewIssue


class ExecutionReviewIssueRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    def get_by_id(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        issue_id: uuid.UUID,
    ) -> ExecutionReviewIssue | None:

        statement = select(ExecutionReviewIssue).where(
            ExecutionReviewIssue.id == issue_id,
            ExecutionReviewIssue.organization_id == organization_id,
            ExecutionReviewIssue.project_id == project_id,
        )

        return self.db.scalar(statement)


    def get_by_identity(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        issue_code: str,
    ) -> ExecutionReviewIssue | None:

        return self.db.scalar(
            select(ExecutionReviewIssue).where(
                ExecutionReviewIssue.organization_id == organization_id,
                ExecutionReviewIssue.project_id == project_id,
                ExecutionReviewIssue.order_id == order_id,
                ExecutionReviewIssue.dataset_version_id == dataset_version_id,
                ExecutionReviewIssue.issue_code == issue_code,
            )
        )


    def create(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        issue_code: str,
        severity: str,
        status: str,
        metric: str,
        observed_value: float,
        threshold: float | None,
        message: str,
        evidence: dict,
        recommendations: list,
    ) -> ExecutionReviewIssue:

        issue = ExecutionReviewIssue(
            organization_id=organization_id,
            project_id=project_id,
            order_id=order_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            issue_code=issue_code,
            severity=severity,
            status=status,
            metric=metric,
            observed_value=observed_value,
            threshold=threshold,
            message=message,
            evidence=evidence,
            recommendations=recommendations,
        )

        self.db.add(issue)
        self.db.flush()

        return issue


    def update_from_detection(
        self,
        issue: ExecutionReviewIssue,
        *,
        severity: str,
        metric: str,
        observed_value: float,
        threshold: float | None,
        message: str,
        evidence: dict,
        recommendations: list,
    ) -> ExecutionReviewIssue:

        issue.severity = severity
        issue.metric = metric
        issue.observed_value = observed_value
        issue.threshold = threshold
        issue.message = message
        issue.evidence = evidence
        issue.recommendations = recommendations
        issue.updated_at = datetime.now(timezone.utc)

        self.db.flush()

        return issue


    def list_for_project(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        status: str | None = None,
        severity: str | None = None,
        issue_code: str | None = None,
        order_id: str | None = None,
        assigned_to: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionReviewIssue]:

        statement = select(ExecutionReviewIssue).where(
            ExecutionReviewIssue.organization_id == organization_id,
            ExecutionReviewIssue.project_id == project_id,
        )

        if status is not None:
            statement = statement.where(
                ExecutionReviewIssue.status == status
            )

        if severity is not None:
            statement = statement.where(
                ExecutionReviewIssue.severity == severity
            )

        if issue_code is not None:
            statement = statement.where(
                ExecutionReviewIssue.issue_code == issue_code
            )

        if order_id is not None:
            statement = statement.where(
                ExecutionReviewIssue.order_id == order_id
            )

        if assigned_to is not None:
            statement = statement.where(
                ExecutionReviewIssue.assigned_to == assigned_to
            )

        statement = (
            statement.order_by(
                ExecutionReviewIssue.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        return list(
            self.db.scalars(statement).all()
        )


    def count_for_project(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        status: str | None = None,
        severity: str | None = None,
        issue_code: str | None = None,
        order_id: uuid.UUID | None = None,
        assigned_to: uuid.UUID | None = None,
    ) -> int:

        statement = select(
            func.count(ExecutionReviewIssue.id)
        ).where(
            ExecutionReviewIssue.organization_id == organization_id,
            ExecutionReviewIssue.project_id == project_id,
        )

        if status is not None:
            statement = statement.where(
                ExecutionReviewIssue.status == status
            )

        if severity is not None:
            statement = statement.where(
                ExecutionReviewIssue.severity == severity
            )

        if issue_code is not None:
            statement = statement.where(
                ExecutionReviewIssue.issue_code == issue_code
            )

        if order_id is not None:
            statement = statement.where(
                ExecutionReviewIssue.order_id == order_id
            )

        if assigned_to is not None:
            statement = statement.where(
                ExecutionReviewIssue.assigned_to == assigned_to
            )

        return self.db.scalar(statement) or 0


    def update_workflow(
        self,
        *,
        issue: ExecutionReviewIssue,
        status: str | None = None,
        assigned_to: uuid.UUID | None = None,
        resolved_at: datetime | None = None,
    ) -> ExecutionReviewIssue:

        if status is not None:
            issue.status = status

        if assigned_to is not None:
            issue.assigned_to = assigned_to

        if resolved_at is not None:
            issue.resolved_at = resolved_at

        issue.updated_at = datetime.now(timezone.utc)

        self.db.add(issue)

        return issue


    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()