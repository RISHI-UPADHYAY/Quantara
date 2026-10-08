from __future__ import annotations

from typing import Any

import pandas as pd


class VisualizationService:
    """
    Transform market-data observations into chart-ready
    time-series points.

    Supported chart types:
        - price
        - cumulative_return
        - drawdown
        - volatility
        - volume
    """

    SUPPORTED_CHART_TYPES = {
        "price",
        "cumulative_return",
        "drawdown",
        "volatility",
        "volume",
    }

    def build(
        self,
        dataframe: pd.DataFrame,
        symbols: list[str],
        chart_type: str,
        periods_per_year: int = 252,
    ) -> dict[str, Any]:

        self._validate_input(
            dataframe=dataframe,
            symbols=symbols,
            chart_type=chart_type,
            periods_per_year=periods_per_year,
        )

        dataframe = dataframe.copy()

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        dataframe["symbol"] = (
            dataframe["symbol"]
            .astype(str)
            .str.strip()
        )

        dataframe = dataframe[
            dataframe["symbol"].isin(symbols)
        ].copy()

        dataframe = (
            dataframe
            .sort_values(["symbol", "timestamp"])
            .reset_index(drop=True)
        )

        points: list[dict[str, Any]] = []

        for symbol in symbols:
            symbol_data = dataframe[
                dataframe["symbol"] == symbol
            ].copy()

            if symbol_data.empty:
                continue

            symbol_points = self._build_symbol_points(
                dataframe=symbol_data,
                symbol=symbol,
                chart_type=chart_type,
                periods_per_year=periods_per_year,
            )

            points.extend(symbol_points)

        return {
            "chart_type": chart_type,
            "symbols": symbols,
            "periods_per_year": periods_per_year,
            "points": points,
        }


    def _build_symbol_points(
        self,
        dataframe: pd.DataFrame,
        symbol: str,
        chart_type: str,
        periods_per_year: int,
    ) -> list[dict[str,  Any]]:

        timestamps = dataframe["timestamp"]

        if chart_type == "price":
            values = dataframe["close"]

        elif chart_type == "volume":
            values = dataframe["volume"]

        elif chart_type == "cumulative_return":
            returns = dataframe["close"].pct_change()
            values = (1.0 + returns.fillna(0.0)).cumprod() - 1.0

        elif chart_type == "drawdown":
            running_peak = dataframe["close"].cummax()
            values = (
                dataframe["close"] / running_peak
            ) - 1.0

        elif chart_type == "volatility":
            returns = dataframe["close"].pct_change()

            values = (
                returns
                .rolling(window=20, min_periods=2)
                .std()
                * (periods_per_year ** 0.5)
            )

        else:

            raise ValueError(
                f"Unsupported chart type: {chart_type}"
            )

        result: list[dict[str, Any]] = []

        for timestamp, value in zip(
            timestamps,
            values,
        ):

            if pd.isna(value):
                continue

            result.append(
                {
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "value": float(value),
                }
            )

        return result


    @classmethod
    def _validate_input(
        cls,
        dataframe: pd.DataFrame,
        symbols: list[str],
        chart_type: str,
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

        if chart_type == "volume":
            required_columns.add("volume")

        missing_columns = (
            required_columns
            - set(dataframe.columns)
        )

        if missing_columns:
            raise ValueError(
                "Required columns are missing: "
                + ", ".join(
                    sorted(missing_columns)
                )
            )

        if not symbols:
            raise ValueError(
                "At least one symbol is required."
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

        if chart_type not in cls.SUPPORTED_CHART_TYPES:
            raise ValueError(
                "Unsupported chart type. Supported types: "
                + ", ".join(
                    sorted(cls.SUPPORTED_CHART_TYPES)
                )
            )

        if not isinstance(
            periods_per_year,
            int,
        ) or isinstance(
            periods_per_year, 
            bool,
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
                "Timestamp column contains valid or null values."
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

        if chart_type == "volume":
            volume = pd.to_numeric(
                dataframe["volume"],
                errors="coerce",
            )

            if volume.isna().any():
                raise ValueError(
                    "Volume contains invalid or null values."
                ) 

            if (volume < 0).any():
                raise ValueError(
                    "Volume cannot be negative."
                )