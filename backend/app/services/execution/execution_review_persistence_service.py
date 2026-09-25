from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.repositories.execution_review_issue_repository import (
    ExecutionReviewIssueRepository,
)
from app.schemas.tca import ExecutionReviewItem


class ExecutionReviewPersistenceService:

    def __init__(
        self,
        db: Session,
    ):

        self.db = db
        self.respository = ExecutionReviewIssueRepository(db)


    def sync_review_item(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        item: ExecutionReviewItem,
    ) -> None:

        for issue in item.issues: 

            existing = self.respository.get_by_identity(
                organization_id=organization_id,
                project_id=project_id,
                order_id=item.order_id,
                dataset_version_id=dataset_version_id,
                issue_code=issue.code,
            )

            if existing is None:

                self.respository.create(
                    organization_id=organization_id,
                    project_id=project_id,
                    order_id=item.order_id,
                    dataset_id=dataset_id,
                    dataset_version_id=dataset_version_id,
                    issue_code=issue.code,
                    severity=issue.severity,
                    status="OPEN",
                    metric=issue.metric,
                    observed_value=issue.observed_value,
                    threshold=issue.threshold,
                    message=issue.message,
                    evidence=issue.evidence,
                    recommendations=issue.recommendations,
                )

            else:

                self.respository.update_from_detection(
                    existing,
                    severity=issue.severity,
                    metric=issue.metric,
                    observed_value=issue.observed_value,
                    threshold=issue.threshold,
                    message=issue.message,
                    evidence=issue.evidence,
                    recommendations=issue.recommendations,
                )


    def sync_review_queue(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        items: list[ExecutionReviewItem],
    ) -> None:

        for item in items:

            self.sync_review_item(
                organization_id=organization_id,
                project_id=project_id,
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                item=item,
            )

        self.respository.commit()