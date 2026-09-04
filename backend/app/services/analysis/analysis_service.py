from __future__ import annotations

import uuid

from typing import Any

import pandas as pd

from app.models.analysis_run import AnalysisRun
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.services.analysis.beta_analyzer import BetaAnalyzer
from app.services.analysis.correlation_analyzer import CorrelationAnalyzer
from app.services.analysis.covariance_analyzer import CovarianceAnalyzer
from app.services.analysis.drawdown_analyzer import DrawdownAnalyzer
from app.services.analysis.price_range_analyzer import PriceRangeAnalyzer
from app.services.analysis.return_analyzer import ReturnAnalyzer
from app.services.analysis.volatility_analyzer import VolatilityAnalyzer
from app.services.analysis.volume_analyzer import VolumeAnalyzer
from app.services.analysis.sharpe_analyzer import SharpeAnalyzer
from app.services.analysis.sortino_analyzer import SortinoAnalyzer
from app.services.analysis.var_analyzer import VaRAnalyzer
from app.services.analysis.cvar_analyzer import CVaRAnalyzer


class AnalysisService:
    """
    Orchestrate Quantara market-data analyses.

    Responsibilities:
        - validate analysis type
        - create persistent AnalysisRun
        - execute the appropriate analyzer
        - manage analysis lifecycle
        - persist successful results
        - persist failures
    """

    ANALYZERS = {
        "return": ReturnAnalyzer,
        "returns": ReturnAnalyzer,

        "volatility": VolatilityAnalyzer,

        "drawdown": DrawdownAnalyzer,

        "volume": VolumeAnalyzer,

        "price_range": PriceRangeAnalyzer,
        "price-range": PriceRangeAnalyzer,

        "correlation": CorrelationAnalyzer,

        "covariance": CovarianceAnalyzer,

        "beta": BetaAnalyzer,

        "sharpe": SharpeAnalyzer,

        "sortino": SortinoAnalyzer,

        "var": VaRAnalyzer,
        "value_at_risk": VaRAnalyzer,

        "cvar": CVaRAnalyzer,
        "expected_shortfall": CVaRAnalyzer,
        "expected-shortfall": CVaRAnalyzer,
    }


    def __init__(
        self,
        repository: AnalysisRunRepository,
    ):

        self.repository = repository


    def run(
        self,
        *,
        dataframe: pd.DataFrame,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID,
        analysis_type: str,
        created_by: uuid.UUID,
        **parameters: Any,
    ) -> AnalysisRun:

        normalized_analysis_type = self._normalize_analysis_type(
            analysis_type
        )

        analyzer_class = self._get_analyzer(
            normalized_analysis_type
        )

        analysis_run = self.repository.create(
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            analysis_type=normalized_analysis_type,
            created_by=created_by,
            row_count=len(dataframe),
        )

        try:
            self.repository.mark_running(
                analysis_run
            )

            analyzer = analyzer_class()

            result = self._execute_analyzer(
                analyzer=analyzer,
                analysis_type=normalized_analysis_type,
                dataframe=dataframe,
                parameters=parameters,
            )

            self.repository.mark_completed(
                analysis_run,
                result=result,
                row_count=len(dataframe),
            )

            return analysis_run

        except Exception as exc:

            self.repository.mark_failed(
                analysis_run,
                error_message=str(exc),
            )

            raise


    @staticmethod
    def _execute_analyzer(
        *,
        analyzer: Any,
        analysis_type: str,
        dataframe: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:

        if analysis_type == "volatility":
            periods_per_year = parameters.get(
                "periods_per_year",
                VolatilityAnalyzer.DEFAULT_PERIODS_PER_YEAR,
            )

            return analyzer.analyze(
                dataframe,
                periods_per_year=periods_per_year,
            )

        if analysis_type == "sharpe":

            periods_per_year = parameters.get(
                "periods_per_year",
                252,
            )

            risk_free_rate = parameters.get(
                "risk_free_rate",
                0.0,
            )

            asset_symbol = parameters.get(
                "asset_symbol"
            )

            return analyzer.analyze(
                dataframe,
                periods_per_year=periods_per_year,
                risk_free_rate=risk_free_rate,
                symbol=asset_symbol,
            )

        if analysis_type == "beta":

            asset_symbol = parameters.get(
                "asset_symbol"
            )

            benchmark_symbol = parameters.get(
                "benchmark_symbol"
            )

            if not asset_symbol:
                raise ValueError(
                    "asset_symbol is required for beta analysis."
                )

            if not benchmark_symbol:
                raise ValueError(
                    "benchmark_symbol is required for beta analysis."
                )

            return analyzer.analyze(
                dataframe,
                asset_symbol=asset_symbol,
                benchmark_symbol=benchmark_symbol,
            )

        if analysis_type == "sortino":

            periods_per_year = parameters.get(
                "periods_per_year",
                SortinoAnalyzer.DEFAULT_PERIODS_PER_YEAR,
            )

            risk_free_rate = parameters.get(
                "risk_free_rate",
                SortinoAnalyzer.DEFAULT_RISK_FREE_RATE,
            )

            target_return = parameters.get(
                "target_return"
            )

            symbol = parameters.get(
                "symbol"
            )

            return analyzer.analyze(
                dataframe,
                periods_per_year=periods_per_year,
                risk_free_rate=risk_free_rate,
                target_return=target_return,
                symbol=symbol,
            )

        if analysis_type in {"var", "value_at_risk"}:
            confidence_level = parameters.get(
                "confidence_level",
                0.95,
            )

            method = parameters.get(
                "method",
                "historical",
            )

            periods_per_year = parameters.get(
                "periods_per_year",
                252,
            )

            symbol = parameters.get("symbol")

            return analyzer.analyze(
                dataframe,
                confidence_level=confidence_level,
                method=method,
                periods_per_year=periods_per_year,
                symbol=symbol,
            )

        if analysis_type in {"cvar", "expected_shortfall"}:
            symbol = parameters.get("symbol")

            if not symbol:
                raise ValueError(
                    "symbol is required for CVaR analysis."
                )

            confidence_level = parameters.get(
                "confidence_level",
                CVaRAnalyzer.DEFAULT_CONFIDENCE_LEVEL,
            )

            periods_per_year = parameters.get(
                "periods_per_year",
                CVaRAnalyzer.DEFAULT_PERIODS_PER_YEAR,
            )

            return analyzer.analyze(
                dataframe,
                symbol=symbol,
                confidence_level=confidence_level,
                periods_per_year=periods_per_year,
            )

        if analysis_type in {
            "return",
            "drawdown",
            "volume",
            "price_range",
            "correlation",
            "covariance",
        }:
            return analyzer.analyze(dataframe)


        raise ValueError(
            f"Unsupported analysis type: {analysis_type}"
        )


    @classmethod
    def _normalize_analysis_type(
        cls,
        analysis_type: str,
    ) -> str:

        if not isinstance(analysis_type, str):
            raise TypeError(
                "analysis_type must be a string."
            )

        normalized = analysis_type.strip().lower()

        if not normalized:
            raise ValueError(
                "analysis_type cannot be empty."
            )

        #Normalize aliases to canonical names.
        aliases = {
            "returns": "return",
            "price-range": "price_range",
            "value_at_risk": "var",
            "expected-shortfall": "expected_shortfall",
        }

        normalized = aliases.get(
            normalized,
            normalized,
        )

        return normalized


    @classmethod
    def _get_analyzer(
        cls,
        analysis_type: str,
    ) -> type:

        analyzer_class = cls.ANALYZERS.get(
            analysis_type
        )

        if analyzer_class is None:
            supported = ", ".join(
                sorted(
                    {
                        "return",
                        "volatility",
                        "drawdown",
                        "volume",
                        "price_range",
                        "correlation",
                        "covariance",
                        "beta",
                        "sharpe",
                        "sortino",
                    }
                )
            )

            raise ValueError(
                f"Unsupported analysis type '{analysis_type}'. Supported analysis types: {supported}"
            )

        return analyzer_class