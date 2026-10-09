from __future__ import annotations

import uuid
from typing import Any

from app.models.analysis_run import AnalysisRun
from app.services.research.research_insights_service import ResearchInsightsService


class ResearchReportService:
    """
    Generate an institutional research report from a completed AnalysisRun.

    The report is derived entirely from deterministic Quantara analysis
    results and provenance. No financial metrics are recalculated here.
    """

    REPORT_SCHEMA_VERSION = 1

    def generate(
        self,
        *,
        analysis_run: AnalysisRun,
        findings: list[dict[str, Any]] | None = None,
        executive_summary: str | None = None,
    ) -> dict[str, Any]:

        if analysis_run.status != "completed":
            raise ValueError(
                "Research reports can only be generated from completed analysis runs."
            )

        if analysis_run.result is None:
            raise ValueError(
                "Analysis run does not contain a completed result."
            )

        if findings is None:
            findings = self._generate_findings(analysis_run)

        result = analysis_run.result or {}
        return_count = result.get("return_count")

        data_limitations = []

        if isinstance(return_count, int) and return_count < 30:
            data_limitations.append(
                {
                    "category": "data_quality",
                    "title": "Limited observation sample",
                    "description": (
                        f"The analysis contains {return_count} return "
                        "observations. Treat statistical conclusions "
                        "cautiously because the sample is limited."
                    ),
                    "severity": "warning",
                }
            )

        if executive_summary is None:
            descriptions = [
                finding["description"]
                for finding in findings
                if finding.get("description")
            ]

            executive_summary = (
                " ".join(descriptions)
                if descriptions
                else (
                    f"The {analysis_run.analysis_type} analysis "
                    "completed successfully. Review the persisted "
                    "results and limitations before drawing conclusions."
                )
            )

        risk_considerations = [
            finding
            for finding in findings
            if finding.get("category") == "risk"
        ]

        data_limitations = [
            finding
            for finding in findings
            if finding.get("category") == "data_quality"
        ]

        result = analysis_run.result or {}
        return_count = result.get("return_count")

        if isinstance(return_count, int) and not isinstance(return_count, bool):
            if return_count < 30:
                data_limitations.append(
                    {
                        "category": "data_quality",
                        "title": "Limited observation sample",
                        "description": (
                            f"The analysis contains {return_count} return "
                            "observations. Treat statistical conclusions "
                            "cautiously because the sample is limited."
                        ),
                        "severity": "warning",
                    }
                )

        return {
            "report_id": uuid.uuid4(),
            "analysis_run_id": analysis_run.id,
            "title": self._build_title(analysis_run),
            "analysis_type": analysis_run.analysis_type,
            "organization_id": analysis_run.organization_id,
            "project_id": analysis_run.project_id,
            "dataset_id": analysis_run.dataset_id,
            "dataset_version_id": analysis_run.dataset_version_id,
            "executive_summary": executive_summary,
            "methodology": self._build_methodology(
                analysis_run,
            ),
            "results": analysis_run.result,
            "findings": findings,
            "risk_concentration": risk_considerations,
            "data_limitations": data_limitations,
            "reproducibility": self._build_reproducibility(
                analysis_run,
            ),
            "metadata": {
                "schema_version": self.REPORT_SCHEMA_VERSION,
                "generated_by": "quantara-research-report",
            },
        }


    @staticmethod
    def _build_title(
        analysis_run: AnalysisRun,
    ) -> str:

        return (
            f"{analysis_run.analysis_type.replace('_', ' ').title()} "
            "Research Report"
        )


    @staticmethod
    def _build_methodology(
        analysis_run: AnalysisRun,
    ) -> dict[str, Any]:

        return {
            "analysis_type": analysis_run.analysis_type,
            "parameters": analysis_run.parameters,
            "configuration": analysis_run.configuration,
            "row_count": analysis_run.row_count,
        }


    @staticmethod
    def _build_reproducibility(
        analysis_run: AnalysisRun,
    ) -> dict[str, Any]:

        return {
            "dataset_version_id": str(
                analysis_run.dataset_version_id
            ),
            "analysis_run_id": str(
                analysis_run.id,
            ),
            "reproduced_from_id": (
                str(analysis_run.reproduced_from_id)
                if analysis_run.reproduced_from_id
                else None
            ),
            "provenance": analysis_run.provenance or {},
        }


    @staticmethod
    def _generate_findings(
        analysis_run: AnalysisRun,
    ) -> list[dict[str, Any]]:

        result = analysis_run.result or {}

        analysis_type = analysis_run.analysis_type.strip().lower()

        analysis_keys = {
            "return": "returns",
            "returns": "returns",
            "volatility": "volatility",
            "drawdown": "drawdown",
            "correlation": "correlation",
            "covariance": "covariance",
            "beta": "beta",
        }

        key = analysis_keys.get(analysis_type)

        analyses = {}
        if key:
            analyses[key] = result

        context_result = {
            "context": {
                "analyses": analyses,
                "data_quality": {},
            }
        }

        findings = ResearchInsightsService().generate(
            context_result=context_result,
        )

        return findings