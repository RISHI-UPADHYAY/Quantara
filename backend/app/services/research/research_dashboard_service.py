from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from sqlalchemy import func

from app.schemas.research_dashboard import (
    ResearchAnalysisCoverage,
    ResearchDashboardRunSummary,
    ResearchLatestActivity,
)

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

        all_runs = self.analysis_repository.list_all_by_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        coverage_by_type: dict[str, dict[str, Any]] = {}
        latest_completed_by_type: dict[str, AnalysisRun] = {}

        for run in all_runs:
            analysis_type = run.analysis_type
            run_status = str(run.status).lower()

            if analysis_type not in coverage_by_type:
                coverage_by_type[analysis_type] = {
                    "analysis_type": analysis_type,
                    "total_runs": 0,
                    "completed_runs": 0,
                    "failed_runs": 0,
                    "running_runs": 0,
                    "pending_runs": 0,
                    "latest_status": run_status,
                    "latest_run_at": run.created_at,
                }

            coverage = coverage_by_type[analysis_type]
            coverage["total_runs"] += 1

            status_key = f"{run_status}_runs"
            if status_key in coverage:
                coverage[status_key] += 1

            if run.status == "completed":
                latest_completed_by_type.setdefault(
                    analysis_type,
                    run,
                )

        analysis_coverage = [
            ResearchAnalysisCoverage(**item)
            for item in coverage_by_type.values()
        ]

        latest_completed_analyses = [
            ResearchDashboardRunSummary.model_validate(run)
            for run in latest_completed_by_type.values()
        ]

        latest_activity = (
            ResearchLatestActivity.model_validate(all_runs[0])
            if all_runs
            else None
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
            "analysis_coverage": analysis_coverage,
            "latest_completed_analyses": latest_completed_analyses,
            "latest_activity": latest_activity,
        }