from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class BetaAnalyzer:
    """
    Analyze the sensitivity of an asset's returns relative to 
    a benchmark's returns.

    Beta is calculated as:
        beta = cov(R_asset, R_benchmark) / Var(R_benchmark)

        Input requirements:
            - timestamp
            - symbol
            - close
        The asset and benchmark returns are calculated independently and then aligned by timestamp before beta calculation.
    """

    REQUIRED_COLUMNS = [
        "timestamp",
        "symbol",
        "close",
    ]

    def analyze(
        self,
        dataframe: pd.DataFrame,
        asset_symbol: str,
        benchmark_symbol: str,
    ) -> dict[str, Any]:
        """Calculate the beta of an asset relative to a benchmark."""

        self._validate_input(dataframe)

        dataframe = dataframe.copy()

        asset_symbol = self._validate_symbol(
            asset_symbol,
            "asset_symbol",
        )

        benchmark_symbol = self._validate_symbol(
            benchmark_symbol,
            "benchmark_symbol",
        )

        if asset_symbol == benchmark_symbol:
            raise ValueError(
                "Asset symbol and benchmark symbol must be different."
            )

        self._normalize_timestamp(dataframe)
        self._validate_values(dataframe)

        available_symbols = set(
            dataframe["symbol"].unique()
        )

        if asset_symbol not in available_symbols:
            raise ValueError(
                f"Asset symbol '{asset_symbol}' was not found in the dataset."
            )

        if benchmark_symbol not in available_symbols:
            raise ValueError(
                f"Benchmark symbol '{benchmark_symbol}' was not found in the dataset."
            )

        dataframe = (
            dataframe
            .sort_values(
                ["symbol", "timestamp"]
            ).reset_index(drop=True)
        )

        returns = self._calculate_returns(
            dataframe=dataframe,
            asset_symbol=asset_symbol,
            benchmark_symbol=benchmark_symbol,
        )

        if returns.empty:
            raise ValueError(
                "Insufficient observations for beta analysis."
            )

        if len(returns) < 2:
            raise ValueError(
                "Insufficient observations for beta analysis."
            )

        asset_returns = returns["asset_return"]
        benchmark_returns = returns["benchmark_return"]

        covariance = float(
            asset_returns.cov(
                benchmark_returns
            )
        )

        benchmark_variance = float(
            benchmark_returns.var()
        )

        if not np.isfinite(benchmark_variance):
            raise ValueError(
                "Benchmark return variance is undefined."
            )

        if benchmark_variance <= 0:
            raise ValueError(
                "Benchmark returns have zero variance, beta cannot be calculated."
            )

        beta = covariance / benchmark_variance

        if not np.isfinite(beta):
            raise ValueError(
                "Beta calculation produced an invalid result."
            )

        asset_mean_return = float(
            asset_returns.mean()
        )

        benchmark_mean_return = float(
            benchmark_returns.mean()
        )  

        asset_volatility = float(
            asset_returns.std()
        )

        benchmark_volatility = float(
            benchmark_returns.std()
        )

        return {
            "asset_symbol": asset_symbol,
            "benchmark_symbol": benchmark_symbol,
            "return_count": int(len(returns)),
            "beta": float(beta),
            "covariance": covariance,
            "benchmark_variance": benchmark_variance,
            "asset_return_statistics": {
                "mean": asset_mean_return,
                "volatility": asset_volatility,
            },
            "benchmark_return_statistics": {
                "mean": benchmark_mean_return,
                "volatility": benchmark_volatility,
            },
        }


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


    @staticmethod
    def _validate_symbol(
        symbol: str,
        field_name: str,
    ) -> str:
        """
        Validate and normalize an asset/benchmark symbol.
        """

        if not isinstance(symbol, str):
            raise ValueError(
                f"{field_name} must be string."
            )

        symbol = symbol.strip()

        if not symbol:
            raise ValueError(
                f"{field_name} cannot be empty."
            )

        return symbol


    @staticmethod
    def _normalize_timestamp(
        dataframe: pd.DataFrame,
    ) -> None:
        """
        Convert timestamps to pandas datetime.

        Invalid timestamps become NaT and are rejected during validation.
        """

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
        )


    def _validate_values(
        self,
        dataframe: pd.DataFrame,
    ) -> None:
        """
        Validate timestamps, symbols, prices and duplicates.
        """

        if dataframe["timestamp"].isna().any():
            raise ValueError(
                "Timestamp contains invalid or null values."
            )

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

        close = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if close.isna().any():
            raise ValueError(
                "Close contains invalid or null values."
            )

        if not np.isfinite(
            close.to_numpy()
        ).all():
            raise ValueError(
                "Close contains invalid or null values."
            )

        dataframe["close"] = close

        if (dataframe["close"] <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )

        duplicates = dataframe.duplicated(
            subset=[
                "timestamp",
                "symbol",
            ],
            keep=False,
        )

        if duplicates.any():
            raise ValueError(
                "Duplicate timestamp-symbol observations detected."
            )


    def _calculate_returns(
        self,
        dataframe: pd.DataFrame,
        asset_symbol: str,
        benchmark_symbol: str,
    ) -> pd.DataFrame:
        """
        Calculate simple percentage returns independently for the asset and benchmark and align them by timestamp.
        """

        working = dataframe[
            [
                "timestamp",
                "symbol",
                "close",
            ]
        ].copy()

        working = working.sort_values(
            [
                "symbol",
                "timestamp",
            ]
        )

        working["return"] = (
            working
            .groupby(
                "symbol",
                sort=False,
            )["close"]
            .pct_change(
                fill_method=None
            )
        )

        working = working[
            working["symbol"].isin(
                [
                    asset_symbol,
                    benchmark_symbol,
                ]
            )
        ]

        working = working[
            working["return"].notna()
        ]

        if working.empty:
            return pd.DataFrame()


        returns = working.pivot(
            index="timestamp",
            columns="symbol",
            values="return",
        )

        returns = returns.dropna(
            axis=0,
            how="any",
        )

        if returns.empty:
            return pd.DataFrame()


        return pd.DataFrame(
            {
                "asset_return": returns[
                    asset_symbol
                ],
                "benchmark_return": returns[
                    benchmark_symbol
                ],
            }
        )