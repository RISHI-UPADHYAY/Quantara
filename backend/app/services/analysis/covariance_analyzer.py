from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd


class CovarianceAnalyzer:
    """
    Analyze return covariance between multiple symbols.

    The analyzer:
        - validates market-data input
        - normalizes timestamps
        - validates symbols and close prices
        - sorts observations chronologically
        - calculates simple percentage returns
        - aligns returns across symbols
        - calculates the sample covariance matrix
        - extracts strongest positive/negative covariance relationships
        - serializes NaN values safely as None
    """

    REQUIRED_COLUMNS = ["timestamp", "symbol", "close"]

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:
        """
        Calculate the sample covariance matrix between symbol returns.
        """

        self._validate_input(dataframe)

        dataframe = dataframe.copy()

        self._normalize_timestamp(dataframe)
        self._validate_values(dataframe)

        #Always calculate returns chrnologically per symbol.
        dataframe = dataframe.sort_values(
            ["symbol", "timestamp"]
        ).reset_index(drop=True)

        symbols = sorted(
            dataframe["symbol"].unique().tolist()
        )

        returns = self._calculate_returns(dataframe)

        if returns.empty:
            raise ValueError(
                "Insufficient observations for return calculation."
            )

        if len(returns) < 2:
            raise ValueError(
                "Insufficient observations for covariance analysis."
            )

        covariance_matrix = returns.cov()

        covariance_matrix = covariance_matrix.reindex(
            index=symbols,
            columns=symbols,
        )

        relationships = self._extract_relationships(
            covariance_matrix,
            symbols,
        )

        return {
            "row_count": len(dataframe),
            "symbol_count": len(symbols),
            "symbols": symbols,
            "return_count": len(returns),
            "covariance_method": "sample",
            "covariance_matrix": self._matrix_to_dict(
                covariance_matrix
            ),
            "relationships": relationships,
        }


    def _validate_input(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Input must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Input DataFrame cannot be empty."
            )

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Required columns are missing: {missing_columns}"
            )


    def _normalize_timestamp(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
        )


    def _validate_values(
        self,
        dataframe: pd.DataFrame,
    ) -> None:

        if dataframe["timestamp"].isna().any():
            raise ValueError(
                "Timestamp contains invalid or null values."
            )

        if dataframe["symbol"].isna().any():
            raise ValueError(
                "Symbol contains invalid or null values"
            )

        if not dataframe["symbol"].map(
            lambda value: isinstance(value, str)
        ).all():
            raise ValueError(
                "Symbol contains invalid or null values."
            )

        if dataframe["symbol"].map(
            lambda value: not value.strip()
        ).any():
            raise ValueError(
                "Symbol contains invalid or null values."
            )

        dataframe["symbol"] = (
            dataframe["symbol"]
            .str.strip()
        )

        close = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if close.isna().any():
            raise ValueError(
                "Close contains invalid or null values."
            )

        dataframe["close"] = close

        if not np.isfinite(
            dataframe["close"].to_numpy()
        ).all():
            raise ValueError(
                "Close contains invalid or null values."
            )

        if (dataframe["close"] <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )

        duplicates = dataframe.duplicated(
            subset=["timestamp", "symbol"],
            keep=False,
        )

        if duplicates.any():
            raise ValueError(
                "Duplicate timestamp-symbol observations detected."
            )


    def _calculate_returns(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate simple percentage returns.

        Returns are calculated independently for each symbol and 
        subsequently aligned by timestamp.
        """

        working = dataframe[
            ["timestamp", "symbol", "close"]
        ].copy()

        working = working.sort_values(
            ["symbol", "timestamp"]
        )

        working["return"] = (
            working
            .groupby("symbol", sort=False)["close"]
            .pct_change(fill_method=None)
        )

        #Remove first observation for every symbol.
        working = working[
            working["return"].notna()
        ]

        if working.empty:
            raise ValueError(
                "Insufficient observations for return calculation."
            )

        returns = working.pivot(
            index="timestamp",
            columns="symbol",
            values="return"
        )

        returns = returns.dropna(
            axis=0,
            how="any",
        )

        if returns.empty:
            raise ValueError(
                "Insufficient observations for return calculation."
            )

        return returns


    def _extract_relationships(
        self,
        covariance_matrix: pd.DataFrame,
        symbols: list[str],
    ) -> dict[str, Any]:

        pairs: list[dict[str, Any]] = []

        for symbol_a, symbol_b in combinations(
            symbols,
            2,
        ):
            covariance = covariance_matrix.loc[
                symbol_a,
                symbol_b,
            ]

            if pd.isna(covariance):
                continue

            pairs.append(
                {
                    "symbol_a": symbol_a,
                    "symbol_b": symbol_b,
                    "covariance": float(covariance),
                }
            )

        if not pairs:
            return {
                "strongest_positive": None,
                "strongest_negative": None,
                "pair_count": 0,
            }

        strongest_positive = max(
            pairs,
            key=lambda pair: pair["covariance"],
        )

        strongest_negative = min(
            pairs,
            key=lambda pair: pair["covariance"],
        )

        return {
            "strongest_positive": strongest_positive,
            "strongest_negative": strongest_negative,
            "pair_count": len(pairs),
        }


    def _matrix_to_dict(
        self,
        covariance_matrix: pd.DataFrame,
    ) -> dict[str, dict[str, float | None]]:

        result: dict[str, dict[str, float | None]] = {}

        for row_symbol in covariance_matrix.index:

            result[row_symbol] = {}

            for column_symbol in covariance_matrix.columns:

                value = covariance_matrix.loc[
                    row_symbol,
                    column_symbol,
                ]

                if pd.isna(value):
                    result[row_symbol][column_symbol] = None

                else:
                    result[row_symbol][column_symbol] = float(value)

        return result