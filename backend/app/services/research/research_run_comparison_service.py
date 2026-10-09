from __future__ import annotations

import math
import uuid
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.schemas.research_comparison import (
    ResearchComparedRun,
    ResearchMetricComparison,
)
from app.services.research.research_workspace_service import (
    ResearchWorkspaceService,
)


class ResearchRunComparisonService:
    def __init__(self, db: Session):
        self.db = db
        self.analysis_repository = AnalysisRunRepository(db)
        self.workspace_service = ResearchWorkspaceService(db)

    def compare_runs(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        baseline_run_id: uuid.UUID,
        comparison_run_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        workspace = self.workspace_service.get_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        if workspace is None:
            return None

        baseline = self._get_workspace_run(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
            run_id=baseline_run_id,
        )
        comparison = self._get_workspace_run(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
            run_id=comparison_run_id,
        )

        if baseline is None or comparison is None:
            raise LookupError("Analysis run not found in this workspace.")

        if baseline.id == comparison.id:
            raise ValueError("The two run IDs must be different.")

        if (
            str(baseline.status).lower() != "completed"
            or str(comparison.status).lower() != "completed"
        ):
            raise ValueError(
                "Only successfully completed analysis runs can be compared."
            )

        if (
            baseline.analysis_type.strip().lower()
            != comparison.analysis_type.strip().lower()
        ):
            raise ValueError(
                "Analysis runs must have the same analysis type."
            )

        if not isinstance(baseline.result, dict):
            raise ValueError(
                "The baseline run does not contain a valid result object."
            )

        if not isinstance(comparison.result, dict):
            raise ValueError(
                "The comparison run does not contain a valid result object."
            )

        baseline_metrics = self._flatten_numeric_metrics(baseline.result)
        comparison_metrics = self._flatten_numeric_metrics(comparison.result)

        shared_paths = sorted(
            set(baseline_metrics) & set(comparison_metrics)
        )
        baseline_only_paths = sorted(
            set(baseline_metrics) - set(comparison_metrics)
        )
        comparison_only_paths = sorted(
            set(comparison_metrics) - set(baseline_metrics)
        )

        if not shared_paths:
            raise ValueError(
                "The runs have no shared numeric metrics to compare."
            )

        shared_metrics: list[ResearchMetricComparison] = []

        for path in shared_paths:
            baseline_value = baseline_metrics[path]
            comparison_value = comparison_metrics[path]

            difference = comparison_value - baseline_value

            percentage_change = (
                (difference / abs(baseline_value)) * 100
                if baseline_value != 0
                else None
            )

            if not math.isfinite(difference):
                raise ValueError(
                    f"Metric '{path}' produced a non-finite difference."
                )

            if (
                percentage_change is not None
                and not math.isfinite(percentage_change)
            ):
                percentage_change = None

            shared_metrics.append(
                ResearchMetricComparison(
                    metric_path=path,
                    baseline_value=baseline_value,
                    comparison_value=comparison_value,
                    difference=difference,
                    percentage_change=percentage_change,
                )
            )

        return {
            "baseline": ResearchComparedRun.model_validate(baseline),
            "comparison": ResearchComparedRun.model_validate(comparison),
            "shared_metrics": shared_metrics,
            "baseline_only_metrics": {
                path: baseline_metrics[path]
                for path in baseline_only_paths
            },
            "comparison_only_metrics": {
                path: comparison_metrics[path]
                for path in comparison_only_paths
            },
        }

    def _get_workspace_run(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> AnalysisRun | None:
        run = self.analysis_repository.get_by_id(
            analysis_run_id=run_id,
        )

        if run is None:
            return None

        if (
            run.organization_id != organization_id
            or run.project_id != project_id
            or run.research_workspace_id != workspace_id
        ):
            return None

        return run

    @classmethod
    def _flatten_numeric_metrics(
        cls,
        value: Any,
        prefix: str = "$",
    ) -> dict[str, int | float]:
        metrics: dict[str, int | float] = {}

        if isinstance(value, Mapping):
            for key, child in value.items():
                child_prefix = f"{prefix}.{key}"
                metrics.update(
                    cls._flatten_numeric_metrics(child, child_prefix)
                )

        elif isinstance(value, list):
            for index, child in enumerate(value):
                child_prefix = f"{prefix}[{index}]"
                metrics.update(
                    cls._flatten_numeric_metrics(child, child_prefix)
                )

        elif (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ):
            metrics[prefix] = value

        return metrics