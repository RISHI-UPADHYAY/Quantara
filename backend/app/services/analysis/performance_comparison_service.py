from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.analysis.drawdown_analyzer import DrawdownAnalyzer
from app.services.analysis.return_analyzer import ReturnAnalyzer
from app.services.analysis.volatility_analyzer import VolatilityAnalyzer


class PerformanceComparisonService:
    """
    Compare the performance and risk characteristics of multiplt instruments contained in the same market-data DataFrame.

    The service reuses the existing:
        - ReturnAnalyzer
        - VolatilityAnalyzer
        - DrawdownAnalyzer

    Expected input columns:
        timestamp
        symbol
        close

    The API layer may normalize `price` -> `close` before calling this service.
    """

    def compare(
        self,
        dataframe: pd.DataFrame,
        symbols: list[str],
        periods_per_year: int = 252,
    ) -> dict[str, Any]:

        self._validate_input(
            dataframe=dataframe,
            symbols=symbols,
            periods_per_year=periods_per_year,
        )

        available_symbols = set(
            dataframe["symbol"]
            .astype(str)
            .unique()
        )

        missing_symbols = [
            symbol
            for symbol in symbols
            if symbol not in available_symbols
        ]

        if missing_symbols:
            raise ValueError(
                "No data found for symbol(s): "
                + ", ".join(missing_symbols)
            )

        results: list[dict[str, Any]] = []

        for symbol in symbols:
            symbol_data = (
                dataframe[
                    dataframe["symbol"].astype(str) == symbol
                ]
                .copy()
            )

            symbol_data = (
                symbol_data
                .sort_values("timestamp")
                .reset_index(drop=True)
            )

            if len(symbol_data) < 2:
                raise ValueError(
                    f"At least two observations are required "
                    f"for symbol: {symbol}"
                )

            returns_result = ReturnAnalyzer().analyze(
                symbol_data
            )

            volatility_result = VolatilityAnalyzer().analyze(
                symbol_data,
                periods_per_year=periods_per_year,
            )

            drawdown_result = DrawdownAnalyzer().analyze(
                symbol_data
            )

            results.append(
                {
                    "symbol": symbol,
                    "row_count": int(len(symbol_data)),
                    "first_timestamp": (
                        symbol_data["timestamp"].iloc[0]
                    ),
                    "last_timestamp": (
                        symbol_data["timestamp"].iloc[-1]
                    ),
                    "initial_price": float(
                        symbol_data["close"].iloc[0]
                    ),
                    "final_price": float(
                        symbol_data["close"].iloc[-1]
                    ),
                    "cumulative_return": (
                        returns_result["cumulative_return"]
                    ),
                    "return_statistics": (
                        returns_result["returns"]
                    ),
                    "volatility": (
                        volatility_result["volatility"]
                    ),
                    "maximum_drawdown": (
                        drawdown_result["drawdown"]["maximum"]
                    ),
                    "maximum_drawdown_percentage": (
                        drawdown_result["drawdown"]["maximum_percentage"]
                    ),
                }
            )

        return {
            "symbol_count": len(results),
            "periods_per_year": int(
                periods_per_year
            ),
            "comparisons": results,
        }


    @staticmethod
    def _validate_input(
        dataframe: pd.DataFrame,
        symbols: list[str],
        periods_per_year: int,
    ) -> None:

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):
            raise TypeError(
                "Input must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Input DataFrame cannot be empty."
            )

        required_columns = {
            "timestamp",
            "symbol",
            "close",
        }

        missing_columns = (
            required_columns
            - set(dataframe.columns)
        )

        if missing_columns:
            raise ValueError(
                "Required columns are missing: "
                + ", ".join(sorted(missing_columns))
            )

        if not isinstance(symbols, list):
            raise TypeError(
                "symbols must be a list."
            )

        if len(symbols) < 2:
            raise ValueError(
                "At least two symbols are required for performance comparison."
            )

        cleaned_symbols = [
            symbol.strip()
            for symbol in symbols
            if isinstance(symbol, str)
            and symbol.strip()
        ]

        if len(cleaned_symbols) != len(symbols):
            raise ValueError(
                "symbols must contain non-empty strings."
            )

        if len(set(cleaned_symbols)) != len(cleaned_symbols):
            raise ValueError(
                "symbols must be unique."
            )

        if (
            not isinstance(
                periods_per_year,
                int,
            )
            or isinstance(
                periods_per_year,
                bool,
            )
        ):

            raise TypeError(
                "periods_per_year must be an integer."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be greater than zero."
            )

        timestamps = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamps.isna().any():
            raise ValueError(
                "Timestamp column contains invalid or null values."
            )

        prices = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if prices.isna().any():
            raise ValueError(
                "Close price contains invalid or null values."
            )

        if (prices <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )