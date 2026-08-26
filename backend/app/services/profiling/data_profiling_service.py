from pathlib import Path
from typing import Any

from app.services.profiling.csv_profiler import CSVProfiler
from app.services.profiling.financial_profiler import FinancialDataProfiler
from app.services.profiling.quality_report import DataQualityReportBuilder
from app.services.profiling.recommendations import DataQualityRecommendationEngine
from app.services.profiling.research_readiness import ResearchReadinessEngine


class DataProfilingService:

    def __init__(self):
        self.csv_profiler = CSVProfiler()
        self.financial_profiler = FinancialDataProfiler()
        self.quality_report_builder = DataQualityReportBuilder()
        self.recommendation_engine = DataQualityRecommendationEngine()
        self.research_readiness_engine = ResearchReadinessEngine()


    def profile(self, file_path: Path) -> dict[str, Any]:

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        structure = self.csv_profiler.profile(
            file_path
        )

        financial = self.financial_profiler.profile(
            file_path
        )

        profile = {
            "file": {
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
            },
            "structure": structure,
            "financial": financial,  

            **financial,    
        }

        quality = self.quality_report_builder.build(
            profile
        )

        recommendations = (
            self.recommendation_engine.generate(
                profile=profile,
                quality_report=quality,
            )
        )

        research_radiness = (
            self.research_readiness_engine.evaluate(
                profile=profile,
                quality_report=quality,
            )
        )

        return {
            "file": profile["file"],
            "structure": structure,
            "financial": financial,
            "quality": quality,
            "recommendations": recommendations,
            "research_readiness": research_radiness,
        }