from typing import Any

import numpy as np
import pandas as pd

class ReturnAnalyzer:

    PRICE_COLUMN = "close"

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate_input(dataframe)

        prices = pd.to_numeric(
            dataframe[self.PRICE_COLUMN],
            errors="coerce",
        )

        returns = prices.pct_change()

        log_returns = np.log(
            prices / prices.shift(1)
        )

        valid_returns = returns.dropna()
        valid_log_returns = log_returns.dropna()

        return {
            "row_count": int(len(dataframe)),
            "price_column": self.PRICE_COLUMN,
            "return_count": int(len(valid_returns)),
            "returns": {
                "mean": self._statistic(valid_returns.mean()),
                "std": self._statistic(valid_returns.std()),
                "min": self._statistic(valid_returns.min()),
                "max": self._statistic(valid_returns.max()),
                "median": self._statistic(valid_returns.median()),
            },
            "log_returns": {
                "mean": self._statistic(
                    valid_log_returns.mean()
                ),
                "std": self._statistic(
                    valid_log_returns.std()
                ),
                "min": self._statistic(
                    valid_log_returns.min()
                ),
                "max": self._statistic(
                    valid_log_returns.max()
                ),
                "median": self._statistic(
                    valid_log_returns.median()
                ),
            },
            "cumulative_return": self._calculate_cummulative_return(
                prices
            ),
        }


    @staticmethod
    def _validate_input(
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

        if "close" not in dataframe.columns:
            raise ValueError(
                "Required column 'close' is missing."
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
    def _calculate_cummulative_return(
        prices: pd.Series,
    ) -> float:

        if len(prices) < 2:
            return 0.0

        first_price = float(prices.iloc[0])
        last_price = float(prices.iloc[-1])

        return float(
            (last_price / first_price) - 1.0
        )


    @staticmethod
    def _statistic(
        value: Any,
    ) -> float:

        if pd.isna(value):
            return 0.0

        return float(value)