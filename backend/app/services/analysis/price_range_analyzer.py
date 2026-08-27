from __future__ import annotations

from typing import Any

import pandas as pd


class PriceRangeAnalyzer:
    """
    Analyze intrabar price ranges from normalized market data.

    Absolute range:
        high - low

    Range percentage:
        (high - low) / close

    The analyzer returns statistics for both measurements separately.
    """

    REQUIRED_COLUMNS = ("open", "high", "low", "close")

    def analyze(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        self._validate_input(dataframe)

        ranges = (
            dataframe["high"].astype(float)
            - dataframe["low"].astype(float)
        )

        close_prices = dataframe["close"].astype(float)

        range_percentages = ranges / close_prices

        return {
            "row_count": int(len(dataframe)),
            "price_columns": {
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
            },
            "range_statistics": {
                "mean": float(ranges.mean()),
                "median": float(ranges.median()),
                "min": float(ranges.min()),
                "max": float(ranges.max()),
                "std": self._std(ranges),
            },
            "range_percentage_statistics": {
                "mean": float(range_percentages.mean()),
                "median": float(range_percentages.median()),
                "min": float(range_percentages.min()),
                "max": float(range_percentages.max()),
                "std": self._std(range_percentages),
            },
            "activity": {
                "average_range": float(ranges.mean()),
                "average_range_percentage": float(range_percentages.mean()),
                "maximum_range": float(ranges.max()),
                "maximum_range_percentage": float(range_percentages.max()),
                "zero_range_count": int((ranges == 0).sum()),
            },
        }

    @staticmethod
    def _validate_input(dataframe: pd.DataFrame) -> None:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame.")

        if dataframe.empty:
            raise ValueError("Input DataFrame cannot be empty.")

        missing_columns = [
            column
            for column in PriceRangeAnalyzer.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Required columns are missing: {missing_columns}"
            )

        for column in PriceRangeAnalyzer.REQUIRED_COLUMNS:
            numeric_values = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

            if numeric_values.isna().any():
                raise ValueError(
                    f"{column.capitalize()} contains invalid or null values."
                )

        close_prices = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if (close_prices <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )

        high_prices = pd.to_numeric(
            dataframe["high"],
            errors="coerce",
        )

        low_prices = pd.to_numeric(
            dataframe["low"],
            errors="coerce",
        )

        open_prices = pd.to_numeric(
            dataframe["open"],
            errors="coerce",
        )

        if (high_prices < low_prices).any():
            raise ValueError(
                "High prices cannot be lower than low prices."
            )

        if (
            (open_prices > high_prices)
            | (open_prices < low_prices)
        ).any():
            raise ValueError(
                "Open prices must fall within the high-low range."
            )

        if (
            (close_prices > high_prices)
            | (close_prices < low_prices)
        ).any():
            raise ValueError(
                "Close prices must fall within the high-low range."
            )

    @staticmethod
    def _std(series: pd.Series) -> float:
        """
        Return population standard deviation.

        For a single observation, return 0.0 instead of NaN so that
        analyzer output remains deterministic and JSON-friendly.
        """
        if len(series) <= 1:
            return 0.0

        return float(series.std(ddof=0))