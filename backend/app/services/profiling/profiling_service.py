from pathlib import Path

from app.services.profiling.csv_profiler import CSVProfiler
from app.services.profiling.financial_profiler import FinancialDataProfiler
from app.services.profiling.quality_report import DataQualityReportBuilder

class ProfilingService:

    def __init__(self):
        self.csv_profiler = CSVProfiler()
        self.financial_profiler = FinancialDataProfiler()
        self.quality_report_builder = DataQualityReportBuilder()


    def profile(self, file_path: Path) -> dict:
        """
        Run the complete profiling pipeline for a CSV dataset.

        Pipeline:
            CSV -> Structural profiling -> Financial/market-data profiling -> Quality analysis -> Unified profiling result
        """ 

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        if file_path.suffix.lower() != ".csv":
            raise ValueError(
                "Only CSV files are currently supported."
            )

        structural_profile = self.csv_profiler.profile(
            file_path
        )

        financial_profile = self.financial_profiler.profile(
            file_path
        )

        quality_report = self.quality_report_builder.build(
            financial_profile
        )

        return {
            "file": {
                "name": file_path.name,
                "size_bytes": file_path.stat().st_size,
            },
            "structure": structural_profile,
            "financial": financial_profile,
            "quality": quality_report,
        }