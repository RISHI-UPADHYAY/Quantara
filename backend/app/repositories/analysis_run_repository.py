from __future__ import annotations

import uuid

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun


class AnalysisRunRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        analysis_type: str,
        created_by: uuid.UUID,
        research_workspace_id: uuid.UUID | None = None,
        parameters: dict | None = None,
        configuration: dict | None = None,
        provenance: dict | None = None,
        reproduced_from_id: uuid.UUID | None = None,
        row_count: int | None = None,
    ) -> AnalysisRun:

        analysis_run = AnalysisRun(
            organization_id=organization_id,
            project_id=project_id,
            research_workspace_id=research_workspace_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            analysis_type=analysis_type,
            status="pending",
            created_by=created_by,
            parameters=parameters or {},
            configuration=configuration or {},
            provenance=provenance or {},
            reproduced_from_id=reproduced_from_id,
            row_count=row_count,
        )

        self.db.add(analysis_run)
        self.db.commit()
        self.db.refresh(analysis_run)

        return analysis_run


    def mark_running(
        self,
        analysis_run: AnalysisRun,
    ) -> AnalysisRun:

        analysis_run.status = "running"
        analysis_run.started_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(analysis_run)

        return analysis_run


    def mark_completed(
        self,
        analysis_run: AnalysisRun,
        *,
        result: dict,
        row_count: int | None = None,
    ) -> AnalysisRun:

        analysis_run.status = "completed"
        analysis_run.result = result
        analysis_run.error_message = None
        analysis_run.completed_at = datetime.now(timezone.utc)

        if row_count is not None:
            analysis_run.row_count = row_count

        self.db.commit()
        self.db.refresh(analysis_run)

        return analysis_run


    def mark_failed(
        self,
        analysis_run: AnalysisRun,
        *, 
        error_message: str,
    ) -> AnalysisRun:

        analysis_run.status = "failed"
        analysis_run.error_message = error_message
        analysis_run.completed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(analysis_run)

        return analysis_run


    def get_by_id(
        self,
        analysis_run_id: uuid.UUID,
    ) -> AnalysisRun | None:

        return(
            self.db.query(AnalysisRun)
            .filter(
                AnalysisRun.id == analysis_run_id
            )
            .first()
        )


    def list_by_dataset(
        self,
        *,
        dataset_id: uuid.UUID,
        analysis_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AnalysisRun]:

        query = self.db.query(AnalysisRun).filter(
            AnalysisRun.dataset_id == dataset_id
        )

        if analysis_type is not None:
            query = query.filter(
                AnalysisRun.analysis_type == analysis_type
            )

        if status is not None:
            query = query.filter(
                AnalysisRun.status == status
            )

        return (
            query
            .order_by(
                AnalysisRun.created_at.desc(),
                AnalysisRun.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )


    def list_by_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[AnalysisRun]:

        query = self.db.query(AnalysisRun).filter(
            AnalysisRun.organization_id == organization_id,
            AnalysisRun.project_id == project_id,
            AnalysisRun.research_workspace_id == workspace_id,
        )

        return (
            query.order_by(
                AnalysisRun.created_at.desc(),
                AnalysisRun.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )


    def list_all_by_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> list[AnalysisRun]:

        return (
            self.db.query(AnalysisRun)
            .filter(
                AnalysisRun.organization_id == organization_id,
                AnalysisRun.project_id == project_id,
                AnalysisRun.research_workspace_id == workspace_id,
            )
            .order_by(
                AnalysisRun.created_at.desc(),
                AnalysisRun.id.desc(),
            )
            .all()
        )


    def get_reproduction_source(
        self,
        *,
        analysis_run_id: uuid.UUID,
    ) -> AnalysisRun | None:

        return (
            self.db.query(AnalysisRun)
            .filter(
                AnalysisRun.id == analysis_run_id
            )
            .first()
        )


    def list_reproduction(
        self,
        *,
        analysis_run_id: uuid.UUID,
    ) -> list[AnalysisRun]:

        return (
            self.db.query(AnalysisRun)
            .filter(
                AnalysisRun.reproduced_from_id == analysis_run_id
            )
            .order_by(
                AnalysisRun.created_at.asc()
            )
            .all()
        )