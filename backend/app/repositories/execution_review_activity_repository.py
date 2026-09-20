from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.execution_review_activity import ExecutionReviewActivity


class ExecutionReviewActivityRepository:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db


    def create_comment(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        review_issue_id: uuid.UUID,
        author_id: uuid.UUID,
        comment: str,
    ) -> ExecutionReviewActivity:

        activity = ExecutionReviewActivity(
            organization_id=organization_id,
            project_id=project_id,
            review_issue_id=review_issue_id,
            author_id=author_id,
            activity_type="COMMENT",
            comment=comment,
            activity_metadata=None,
        )

        self.db.add(activity)

        return activity


    def list_for_issue(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        review_issue_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExecutionReviewActivity]:

        statement = (
            select(ExecutionReviewActivity).where(
                ExecutionReviewActivity.organization_id == organization_id,
                ExecutionReviewActivity.project_id == project_id,
                ExecutionReviewActivity.review_issue_id == review_issue_id,
            ).order_by(
                ExecutionReviewActivity.created_at.desc()
            )
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(statement).all())


    def count_for_issue(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        review_issue_id: uuid.UUID,
    ) -> int:

        statement = (
            select(func.count())
            .select_from(ExecutionReviewActivity)
            .where(
                ExecutionReviewActivity.organization_id == organization_id,
                ExecutionReviewActivity.project_id == project_id,
                ExecutionReviewActivity.review_issue_id == review_issue_id,
            )
        )

        return self.db.scalar(statement) or 0