from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class SortinoAnalyzer:
    """
    Calculate the Sortino ratio for a financial time series.

    The Sortino ratio measures risk-adjusted return using only
    downside volatility rather than total volatility.

    Formula:

        Sortino = Annualized Excess Return / Annualized Downside Deviation

    The analyzer expects either:

        - a single `close` column, or
        - a single numeric price column.

    Optional parameters:

        periods_per_year:
            Number of periods in a year. Default: 252.

        risk_free_rate:
            Annualized risk-free rate. Default: 0.0.

        target_return:
            Annualized minimum acceptable return (MAR).
            If omitted, the annualized risk-free rate is used.
    """

    DEFAULT_PERIODS_PER_YEAR = 252
    DEFAULT_RISK_FREE_RATE = 0.0

    def analyze(
        self,
        dataframe: pd.DataFrame,
        *,
        periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
        risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
        target_return: float | None = None,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate Sortino ratio and supporting statistics.
        """

        self._validate_dataframe(dataframe)
        self._validate_parameters(
            periods_per_year=periods_per_year,
            risk_free_rate=risk_free_rate,
            target_return=target_return,
        )

        price_series = self._extract_price_series(dataframe)

        returns = price_series.pct_change().dropna()

        if returns.empty:
            raise ValueError(
                "At least two valid price observations are required."
            )

        if not np.isfinite(returns.to_numpy()).all():
            raise ValueError(
                "Price data produced non-finite returns."
            )

        periodic_risk_free_rate = (
            (1.0 + risk_free_rate) ** (1.0 / periods_per_year)
        ) - 1.0

        if target_return is None:
            periodic_target_return = periodic_risk_free_rate
        else:
            periodic_target_return = (
                (1.0 + target_return) ** (1.0 / periods_per_year)
            ) - 1.0

        excess_returns = returns - periodic_risk_free_rate

        downside_returns = returns - periodic_target_return
        downside_returns = downside_returns[
            downside_returns < 0
        ]

        if downside_returns.empty:
            downside_deviation = 0.0
        else:
            downside_deviation = float(
                np.sqrt(
                    np.mean(
                        np.square(downside_returns)
                    )
                )
            )

        mean_return = float(returns.mean())
        mean_excess_return = float(excess_returns.mean())

        annualized_return = float(
            (1.0 + mean_return) ** periods_per_year - 1.0
        )

        annualized_excess_return = float(
            (1.0 + mean_excess_return) ** periods_per_year - 1.0
        )

        annualized_downside_deviation = float(
            downside_deviation * np.sqrt(periods_per_year)
        )

        if annualized_downside_deviation == 0.0:
            if annualized_excess_return > 0:
                sortino_ratio = float("inf")
            elif annualized_excess_return < 0:
                sortino_ratio = float("-inf")
            else:
                sortino_ratio = 0.0
        else:
            sortino_ratio = float(
                annualized_excess_return
                / annualized_downside_deviation
            )

        return {
            "symbol": symbol,
            "return_count": int(len(returns)),
            "periods_per_year": periods_per_year,
            "risk_free_rate": risk_free_rate,
            "target_return": (
                risk_free_rate
                if target_return is None
                else target_return
            ),
            "periodic_risk_free_rate": periodic_risk_free_rate,
            "periodic_target_return": periodic_target_return,
            "mean_return": mean_return,
            "mean_excess_return": mean_excess_return,
            "downside_return_count": int(len(downside_returns)),
            "periodic_downside_deviation": downside_deviation,
            "annualized_return": annualized_return,
            "annualized_excess_return": annualized_excess_return,
            "annualized_downside_deviation": (
                annualized_downside_deviation
            ),
            "sortino_ratio": sortino_ratio,
        }

    @staticmethod
    def _validate_dataframe(
        dataframe: pd.DataFrame,
    ) -> None:

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "dataframe must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame cannot be empty."
            )

    @staticmethod
    def _validate_parameters(
        *,
        periods_per_year: int,
        risk_free_rate: float,
        target_return: float | None,
    ) -> None:

        if (
            not isinstance(periods_per_year, int)
            or isinstance(periods_per_year, bool)
        ):
            raise TypeError(
                "periods_per_year must be an integer."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be greater than zero."
            )

        if not np.isfinite(risk_free_rate):
            raise ValueError(
                "risk_free_rate must be finite."
            )

        if target_return is not None and not np.isfinite(
            target_return
        ):
            raise ValueError(
                "target_return must be finite."
            )

    @staticmethod
    def _extract_price_series(
        dataframe: pd.DataFrame,
    ) -> pd.Series:

        if "close" in dataframe.columns:
            series = dataframe["close"]
        elif "Close" in dataframe.columns:
            series = dataframe["Close"]
        else:
            numeric_columns = dataframe.select_dtypes(
                include="number"
            ).columns

            if len(numeric_columns) != 1:
                raise ValueError(
                    "Unable to determine price column. "
                    "Provide a DataFrame with a 'close' column "
                    "or exactly one numeric column."
                )

            series = dataframe[numeric_columns[0]]

        series = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if series.empty:
            raise ValueError(
                "Price column contains no valid numeric values."
            )

        if (series <= 0).any():
            raise ValueError(
                "Price values must be greater than zero."
            )

        return series.astype(float)