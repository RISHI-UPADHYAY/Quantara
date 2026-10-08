from __future__ import annotations

from pathlib import Path

from typing import Any

import pandas as pd

from app.services.analysis.beta_analyzer import BetaAnalyzer
from app.services.analysis.correlation_analyzer import CorrelationAnalyzer
from app.services.analysis.covariance_analyzer import CovarianceAnalyzer
from app.services.analysis.drawdown_analyzer import DrawdownAnalyzer
from app.services.analysis.return_analyzer import ReturnAnalyzer
from app.services.analysis.volatility_analyzer import VolatilityAnalyzer
from app.services.profiling.data_profiling_service import DataProfilingService



class ResearchContextService:
    """
    Build deterministic research context for the AI Research Copilot.

    This service does not call an LLM.

    Its responsibility is to transform Quantara's market data and deterministic
    analytics into structured evidence that an LLM can reason over without directly relying on raw, unverified claims.
    """

    def build(
        self,
        *,
        dataframe: pd.DataFrame,
        question: str,
        file_path: str | None = None,
        symbols: list[str] | None = None,
        periods_per_year: int = 252,
    ) -> dict[str, Any]:

        if not isinstance(dataframe, pd.DataFrame):
            raise ValueError(
                "dataframe must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Research context cannot be built from empty data."
            )

        if not question or not question.strip():
            raise ValueError(
                "Research question cannot be empty."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be greater than zero."
            )

        dataframe = self._prepare_dataframe(dataframe)

        available_symbols = self._extract_symbols(dataframe)

        selected_symbols = self._select_symbols(
            available_symbols=available_symbols,
            requested_symbols=symbols,
        )

        filtered_dataframe = dataframe

        if selected_symbols:
            filtered_dataframe = dataframe[
                dataframe["symbol"].isin(selected_symbols)
            ].copy()

        if filtered_dataframe.empty:
            raise ValueError(
                "No market-data rows remain after symbol filtering."
            )

        evidence: list[dict[str, Any]] = []

        context: dict[str, Any] = {
            "question": question.strip(),
            "file_path": file_path,
            "row_count": int(len(filtered_dataframe)),
            "columns": list(filtered_dataframe.columns),
            "symbols": selected_symbols,
            "available_symbols": available_symbols,
            "periods_per_year": periods_per_year,
            "time_range": self._build_time_range(filtered_dataframe),
            "analyses": {},
            "data_quality": {},
        }

        returns_result = self._run_returns(filtered_dataframe)
        context["analyses"]["returns"] = returns_result
        self._add_return_evidence(evidence, returns_result)

        volatility_result = self._run_volatility(
            filtered_dataframe,
            periods_per_year,
        )

        context["analyses"]["volatility"] = volatility_result
        self._add_volatility_evidence(evidence, volatility_result)

        drawdown_result = self._run_drawdown(filtered_dataframe)
        context["analyses"]["drawdown"] = drawdown_result
        self._add_drawdown_evidence(evidence, drawdown_result)

        if len(selected_symbols) >= 2:
            correlation_result = self._run_correlation(
                filtered_dataframe,
            )

            context["analyses"]["correlation"] = correlation_result
            self._add_relationship_evidence(
                evidence,
                correlation_result,
                metric="correlation",
            )

            covariance_result = self._run_covariance(
                filtered_dataframe,
            )
            context["analyses"]["covariance"] = covariance_result
            self._add_relationship_evidence(
                evidence,
                covariance_result,
                metric="covariance",
            )

            beta_results = self._run_beta_comparisons(
                filtered_dataframe,
                selected_symbols,
            )

            context["analyses"]["beta"] = beta_results

            for beta_result in beta_results:
                evidence.append(
                    {
                        "source": "BetaAnalyzer",
                        "metric": "beta",
                        "value": beta_result,
                        "interpretation": (
                            f"{beta_result['asset_symbol']} beta relative to "
                            f"{beta_result['benchmark_symbol']}."
                        ),
                    }
                )

        context["data_quality"] = self._build_quality_context(
            filtered_dataframe,
            file_path,
        )

        context["evidence_count"] = len(evidence)

        return {
            "question": question.strip(),
            "context": context,
            "evidence": evidence,
        }


    @staticmethod
    def _prepare_dataframe(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        dataframe = dataframe.copy()

        #Normalize common column aliases to Quantara's canonical names.
        column_aliases = {
            "timestamps": "timestamp",
            "time": "timestamp",
            "datetime": "timestamp",
            "date": "timestamp",
            "price": "close",
        }

        rename_map: dict[str, str] = {}

        for source, target in column_aliases.items():
            if source in dataframe.columns and target not in dataframe.columns:
                rename_map[source] = target

        if rename_map:
            dataframe = dataframe.rename(
                columns=rename_map,
            )

        required_columns = {
            "timestamp",
            "close",
        }

        missing_columns = required_columns.difference(dataframe.columns)

        if missing_columns:
            raise ValueError(
                "Research context requires columns: "
                + ", ".join(sorted(required_columns))
                + ". Missing: "
                + ", ".join(sorted(missing_columns))
            )

        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise ValueError(
                "Timestamp column contains invalid or null values."
            )

        dataframe["timestamp"] = timestamp

        dataframe["close"] = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if dataframe["close"].isna().any():
            raise ValueError(
                "Close price column contains invalid or null values."
            )

        if (dataframe["close"] <= 0).any():
            raise ValueError(
                "Close price column must contain only positive values."
            )

        if "symbol" not in dataframe.columns:
            dataframe["symbol"] = "UNKNOWN"

        dataframe["symbol"] = dataframe["symbol"].astype(str).str.strip()

        if dataframe["symbol"].eq("").any():
            raise ValueError(
                "Symbol column contains empty values."
            )

        return (
            dataframe
            .sort_values(
                ["symbol", "timestamp"],
                kind="stable",
            )
            .reset_index(drop=True)
        )


    @staticmethod
    def _extract_symbols(
        dataframe: pd.DataFrame,
    ) -> list[str]:
        return sorted(
            {
                str(symbol)
                for symbol in dataframe["symbol"].dropna().unique()
            }
        )


    @staticmethod
    def _select_symbols(
        *,
        available_symbols: list[str],
        requested_symbols: list[str] | None,
    ) -> list[str]:

        if not requested_symbols:
            return available_symbols

        normalized_requested = []

        for symbol in requested_symbols:
            normalized = str(symbol).strip()

            if normalized and normalized not in normalized_requested:
                normalized_requested.append(normalized)

        unavailable = [
            symbol
            for symbol in normalized_requested
            if symbol not in available_symbols
        ]

        if unavailable:
            raise ValueError(
                "Requested symbols were not found in the dataset: "
                + ", ".join(unavailable)
            )

        return normalized_requested


    @staticmethod
    def _build_time_range(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        timestamps = dataframe["timestamp"]

        return {
            "first_timestamp": timestamps.min(),
            "last_timestamp": timestamps.max(),
        }


    @staticmethod
    def _run_returns(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        return ReturnAnalyzer().analyze(dataframe)


    @staticmethod
    def _run_volatility(
        dataframe: pd.DataFrame,
        periods_per_year: int,
    ) -> dict[str, Any]:

        return VolatilityAnalyzer().analyze(
            dataframe=dataframe,
            periods_per_year=periods_per_year,
        )


    @staticmethod
    def _run_drawdown(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        return DrawdownAnalyzer().analyze(dataframe)



    @staticmethod
    def _run_correlation(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        return CorrelationAnalyzer().analyze(dataframe)


    @staticmethod
    def _run_covariance(
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        return CovarianceAnalyzer().analyze(dataframe)


    @staticmethod
    def _run_beta_comparisons(
        dataframe: pd.DataFrame,
        symbols: list[str],
    ) -> list[dict[str, Any]]:

        results: list[dict[str, Any]] = []

        if len(symbols) < 2:
            return results

        benchmark_symbol = symbols[0]

        for asset_symbol in symbols[1:]:
            try:
                result = BetaAnalyzer().analyze(
                    dataframe=dataframe,
                    asset_symbol=asset_symbol,
                    benchmark_symbol=benchmark_symbol,
                )

                results.append(result)

            except (ValueError, TypeError):
                continue

        return results


    @staticmethod
    def _build_quality_context(
        dataframe: pd.DataFrame,
        file_path: str | None,
    ) -> dict[str, Any]:

        if not file_path:
            return {
                "available": False,
                "reason": (
                    "A source file path was not supplied, so the full "
                    "data-profiling pipeline was not executed."
                ),
            }

        try:
            profile = DataProfilingService().profile(
                file_path=Path(file_path),
            )

            return {
                "available": True,
                "quality": profile.get(
                    "quality",
                    {},
                ),
                "research_readiness": profile.get(
                    "research_readiness",
                    {},
                ),
                "recommendations": profile.get(
                    "recommendations",
                    [],
                ),
            }

        except Exception as exc:
            return {
                "available": False,
                "reason": (
                    "Data-quality profiling could not be completed."
                ),
                "error": str(exc),
                "row_count": int(len(dataframe)),
            }


    @staticmethod
    def _add_return_evidence(
        evidence: list[dict[str, Any]],
        result: dict[str, Any],
    ) -> None:

        evidence.append(
            {
                "source": "ReturnAnalyzer",
                "metric": "cumulative_return",
                "value": result.get("cumulative_return"),
                "interpretation": (
                    "Cumulative simple return over the analyzed period."
                ),
            }
        )

        evidence.append(
            {
                "source": "ReturnAnalyzer",
                "metric": "return_statistics",
                "value": result.get("returns", {}),
                "interpretation": (
                    "Distribution statistics for periodic returns."
                ),
            }
        )


    @staticmethod
    def _add_volatility_evidence(
        evidence: list[dict[str, Any]],
        result: dict[str, Any],
    ) -> None:

        volatility = result.get(
            "volatility",
            {},
        )

        evidence.append(
            {
                "source": "VolatilityAnalyzer",
                "metric": "annualized_volatility",
                "value": volatility.get("annualized"),
                "interpretation": (
                    "Annualized volatility using the requested periods_per_year convention."
                ),
            }
        )


    @staticmethod
    def _add_drawdown_evidence(
        evidence: list[dict[str, Any]],
        result: dict[str, Any],
    ) -> None:

        drawdown = result.get(
            "drawdown",
            {},
        )

        evidence.append(
            {
                "source": "DrawdownAnalyzer",
                "metric": "maximum_drawdown_percentage",
                "value": drawdown.get(
                    "maximum_percentage"    
                ),
                "interpretation": (
                    "Maximum peak-to-trough drawdown during the analyzed period."
                ),
            }
        )

    
    @staticmethod
    def _add_relationship_evidence(
        evidence: list[dict[str, Any]],
        result: dict[str, Any],
        *,
        metric: str,
    ) -> None:

        strongest_positive = result.get(
            "strongest_positive",
        )

        strongest_negative = result.get(
            "strongest_negative",
        )

        if strongest_positive is not None:

            evidence.append(
                {
                    "source": (
                        "CorrelationAnalyzer"
                        if metric == "correlation"
                        else "CovarianceAnalyzer"
                    ),
                    "metric": f"strongest_positive_{metric}",
                    "value": strongest_positive,
                    "interpretation": (
                        f"Strongest positive {metric} relationship "
                        "identified by Quantara."
                    ),
                }
            )

        if strongest_negative is not None:
            evidence.append(
                {
                    "source": (
                        "CorrelationAnalyzer"
                        if metric == "correlation"
                        else "CovarianceAnalyzer"
                    ),
                    "metric": f"strongest_negative_{metric}",
                    "value": strongest_negative,
                    "interpretation": (
                        f"Strongest negative {metric} relationship "
                        "identified by Quantara."
                    )
                }
            )