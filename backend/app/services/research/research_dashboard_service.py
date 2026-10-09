from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from sqlalchemy import func

from app.models.analysis_run import AnalysisRun
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.services.research.research_workspace_service import ResearchWorkspaceService


class ResearchDashboardService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.workspace_service = ResearchWorkspaceService(db)
        self.analysis_repository = AnalysisRunRepository(db)


    def get_dashboard(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any] | None:

        workspace = self.workspace_service.get_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        if workspace is None:
            return None

        base_query = self.db.query(AnalysisRun).filter(
            AnalysisRun.organization_id == organization_id,
            AnalysisRun.project_id == project_id,
            AnalysisRun.research_workspace_id == workspace_id,
        )

        total_runs = base_query.with_entities(
            func.count(AnalysisRun.id)
        ).scalar() or 0

        status_counts = (
            base_query.with_entities(
                AnalysisRun.status,
                func.count(AnalysisRun.id),
            )
            .group_by(AnalysisRun.status)
            .all()
        )

        counts = {
            str(run_status).lower(): count
            for run_status, count in status_counts
        }

        recent_runs = self.analysis_repository.list_by_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
        )

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_status": workspace.status,
            "dataset_id": workspace.dataset_id,
            "dataset_version_id": workspace.dataset_version_id,
            "symbols": workspace.symbols or [],
            "total_runs": total_runs,
            "completed_runs": counts.get("completed", 0),
            "failed_runs": counts.get("failed", 0),
            "running_runs": counts.get("running", 0),
            "pending_runs": counts.get("pending", 0),
            "recent_runs": recent_runs,
        }