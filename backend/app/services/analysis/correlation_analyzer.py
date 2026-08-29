from __future__ import annotations

from itertools import combinations
from typing import Any

import pandas as pd


class CorrelationAnalyzer:
    """
    Analyze Pearson correlations between symbol returns.

    Input requirements:
        - timestamp
        - symbol
        - close

    Returns are calculated independently for each symbol and then
    aligned by timestamp before correlation analysis.
    """

    REQUIRED_COLUMNS = ["timestamp", "symbol", "close"]

    def analyze(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        """
        Calculate Pearson correlations between symbol returns.
        """

        # ------------------------------------------------------------
        # 1. Validate input structure
        # ------------------------------------------------------------

        self._validate_input(dataframe)

        dataframe = dataframe.copy()

        # ------------------------------------------------------------
        # 2. Normalize and validate values
        # ------------------------------------------------------------

        self._normalize_timestamp(dataframe)
        self._validate_values(dataframe)

        # ------------------------------------------------------------
        # 3. Sort chronologically within each symbol
        # ------------------------------------------------------------

        dataframe = (
            dataframe
            .sort_values(["symbol", "timestamp"])
            .reset_index(drop=True)
        )

        symbols = sorted(
            dataframe["symbol"].unique().tolist()
        )

        # ------------------------------------------------------------
        # 4. Calculate aligned returns
        # ------------------------------------------------------------

        returns = self._calculate_returns(dataframe)

        # No return observations at all.
        #
        # This is different from a constant-price series.
        # A constant-price series produces valid zero returns.
        if returns.empty:
            raise ValueError(
                "Insufficient observations for return calculation."
            )

        # ------------------------------------------------------------
        # 5. Calculate Pearson correlation
        # ------------------------------------------------------------

        correlation_matrix = returns.corr(
            method="pearson"
        )

        correlation_matrix = correlation_matrix.reindex(
            index=symbols,
            columns=symbols,
        )

        # ------------------------------------------------------------
        # 6. Extract strongest relationships
        # ------------------------------------------------------------

        relationships = self._extract_relationships(
            correlation_matrix,
            symbols,
        )

        # ------------------------------------------------------------
        # 7. Return serialized result
        # ------------------------------------------------------------

        return {
            "row_count": len(dataframe),
            "symbol_count": len(symbols),
            "symbols": symbols,
            "return_count": len(returns),
            "correlation_method": "pearson",
            "correlation_matrix": self._matrix_to_dict(
                correlation_matrix
            ),
            "relationships": relationships,
        }

    # ================================================================
    # VALIDATION
    # ================================================================

    def _validate_input(
        self,
        dataframe: pd.DataFrame,
    ) -> None:
        """
        Validate the input object and required columns.
        """

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
        """
        Convert timestamps to pandas datetime.

        Invalid values become NaT and are rejected during validation.
        """

        # Already datetime-like: don't unnecessarily re-parse.
        if pd.api.types.is_datetime64_any_dtype(
            dataframe["timestamp"]
        ):
            return

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
        )

    def _validate_values(
        self,
        dataframe: pd.DataFrame,
    ) -> None:
        """
        Validate timestamp, symbol, close and duplicate observations.
        """

        # ------------------------------------------------------------
        # Timestamp
        # ------------------------------------------------------------

        if dataframe["timestamp"].isna().any():
            raise ValueError(
                "Timestamp contains invalid or null values."
            )

        # ------------------------------------------------------------
        # Symbol
        # ------------------------------------------------------------

        if dataframe["symbol"].isna().any():
            raise ValueError(
                "Symbol contains invalid or null values."
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

        # ------------------------------------------------------------
        # Close
        # ------------------------------------------------------------

        close = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if close.isna().any():
            raise ValueError(
                "Close contains invalid or null values."
            )

        dataframe["close"] = close

        if (dataframe["close"] <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )

        # ------------------------------------------------------------
        # Duplicate timestamp-symbol observations
        # ------------------------------------------------------------

        duplicates = dataframe.duplicated(
            subset=["timestamp", "symbol"],
            keep=False,
        )

        if duplicates.any():
            raise ValueError(
                "Duplicate timestamp-symbol observations detected."
            )

    # ================================================================
    # RETURN CALCULATION
    # ================================================================

    def _calculate_returns(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate simple percentage returns.

        Important:
            Constant-price series are valid.

        Example:
            100, 100, 100, 100, 100

        produces:
            0, 0, 0, 0

        Pearson correlation between two constant series is
        mathematically undefined, so pandas will represent it
        as NaN. That is handled later rather than rejecting the
        input dataset.
        """

        working = dataframe[
            ["timestamp", "symbol", "close"]
        ].copy()

        working = working.sort_values(
            ["symbol", "timestamp"]
        )

        # ------------------------------------------------------------
        # Calculate simple percentage returns per symbol
        # ------------------------------------------------------------

        working["return"] = (
            working
            .groupby(
                "symbol",
                sort=False,
            )["close"]
            .pct_change(fill_method=None)
        )

        # Remove the first observation of every symbol.
        working = working[
            working["return"].notna()
        ]

        # No returns means there wasn't enough data for even one
        # observation per symbol.
        if working.empty:
            return pd.DataFrame()

        # ------------------------------------------------------------
        # Pivot into:
        #
        # timestamp | SYMBOL_A | SYMBOL_B | ...
        #
        # ------------------------------------------------------------

        returns = working.pivot(
            index="timestamp",
            columns="symbol",
            values="return",
        )

        # ------------------------------------------------------------
        # Correlation requires aligned observations.
        #
        # Keep only timestamps where every symbol has a return.
        # ------------------------------------------------------------

        returns = returns.dropna(
            axis=0,
            how="any",
        )

        return returns

    # ================================================================
    # RELATIONSHIPS
    # ================================================================

    def _extract_relationships(
        self,
        correlation_matrix: pd.DataFrame,
        symbols: list[str],
    ) -> dict[str, Any]:
        """
        Extract strongest positive and negative relationships.

        Every possible symbol pair contributes to pair_count,
        including pairs whose Pearson correlation is undefined.

        Undefined correlations are represented by None.
        """

        all_pairs: list[dict[str, Any]] = []
        valid_pairs: list[dict[str, Any]] = []

        # ------------------------------------------------------------
        # Build every unique symbol pair
        # ------------------------------------------------------------

        for symbol_a, symbol_b in combinations(
            symbols,
            2,
        ):
            correlation = correlation_matrix.loc[
                symbol_a,
                symbol_b,
            ]

            if pd.isna(correlation):
                pair = {
                    "symbol_a": symbol_a,
                    "symbol_b": symbol_b,
                    "correlation": None,
                }
            else:
                pair = {
                    "symbol_a": symbol_a,
                    "symbol_b": symbol_b,
                    "correlation": float(correlation),
                }

                valid_pairs.append(pair)

            all_pairs.append(pair)

        # ------------------------------------------------------------
        # No symbol pairs
        #
        # Example:
        #   only NIFTY50 exists
        # ------------------------------------------------------------

        if not all_pairs:
            return {
                "strongest_positive": None,
                "strongest_negative": None,
                "pair_count": 0,
            }

        # ------------------------------------------------------------
        # There are pairs, but all correlations are undefined.
        #
        # Example:
        #   NIFTY50 = constant
        #   BANKNIFTY = constant
        #
        # pair_count must still be 1.
        # ------------------------------------------------------------

        if not valid_pairs:
            return {
                "strongest_positive": None,
                "strongest_negative": None,
                "pair_count": len(all_pairs),
            }

        # ------------------------------------------------------------
        # Strongest positive relationship
        # ------------------------------------------------------------

        strongest_positive = max(
            valid_pairs,
            key=lambda pair: pair["correlation"],
        )

        # ------------------------------------------------------------
        # Strongest negative relationship
        # ------------------------------------------------------------

        strongest_negative = min(
            valid_pairs,
            key=lambda pair: pair["correlation"],
        )

        return {
            "strongest_positive": strongest_positive,
            "strongest_negative": strongest_negative,
            "pair_count": len(all_pairs),
        }

    # ================================================================
    # SERIALIZATION
    # ================================================================

    def _matrix_to_dict(
        self,
        correlation_matrix: pd.DataFrame,
    ) -> dict[str, dict[str, float | None]]:
        """
        Convert pandas correlation matrix into JSON-safe dictionaries.

        NaN correlations become None.
        """

        result: dict[str, dict[str, float | None]] = {}

        for row_symbol in correlation_matrix.index:

            result[row_symbol] = {}

            for column_symbol in correlation_matrix.columns:

                value = correlation_matrix.loc[
                    row_symbol,
                    column_symbol,
                ]

                if pd.isna(value):
                    result[row_symbol][column_symbol] = None
                else:
                    result[row_symbol][column_symbol] = float(value)

        return result