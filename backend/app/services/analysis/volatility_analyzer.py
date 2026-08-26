from typing import Any

import numpy as np
import pandas as pd


class VolatilityAnalyzer:

    PRICE_COLUMN = "close"

    #Number of observations used to analyze volatility.
    #This is configurable so the analyzer can support differnt market frequencies later.

    DEFAULT_PERIODS_PER_YEAR = 252

    def analyze(
        self,
        dataframe: pd.DataFrame,
        periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    ) -> dict[str, Any]:

        self._validate_input(
            dataframe, 
            periods_per_year,
        )

        prices = pd.to_numeric(
            dataframe[self.PRICE_COLUMN],
            errors="coerce",
        )

        returns = prices.pct_change().dropna()

        if returns.empty:
            return {
                "row_count": int(len(dataframe)),
                "price_column": self.PRICE_COLUMN,
                "return_count": 0,
                "periods_per_year": periods_per_year,
                "volatility": {
                    "periodic": 0.0,
                    "annualized": 0.0,
                },
                "return_statistics": {
                    "mean": 0.0,
                    "std": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                },
            }

        periodic_volatility = float(
            returns.std()
        )

        annualized_volatility = float(
            periodic_volatility
            * np.sqrt(periods_per_year)
        )

        return {
            "row_count": int(len(dataframe)),
            "price_column": self.PRICE_COLUMN,
            "return_count": int(len(returns)),
            "periods_per_year": int(periods_per_year),
            "volatility": {
                "periodic": periodic_volatility,
                "annualized": annualized_volatility,
            },
            "return_statistics": {
                "mean": self._statistic(
                    returns.mean()
                ),
                "std": self._statistic(
                    returns.std()
                ),
                "min": self._statistic(
                    returns.min()
                ),
                "max": self._statistic(
                    returns.max()
                ),
            },
        }


    @staticmethod
    def _validate_input(
        dataframe: pd.DataFrame,
        periods_per_year: int,
    ) -> None:

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Input must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Input DataFrame cannot be empty."
            )

        if "close" not in dataframe.columns:
            raise ValueError(
                "Required column 'close' is missing."
            )

        if not isinstance(
            periods_per_year,
            (int, np.integer),
        ):

            raise TypeError(
                "periods_per_year must be an integer."
            )

        if periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be greater than zero."
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


    @staticmethod
    def _statistic(
        value: Any,
    ) -> float:

        if pd.isna(value):
            return 0.0

        return float(value)