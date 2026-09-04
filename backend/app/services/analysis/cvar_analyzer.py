from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class CVaRAnalyzer:
    """
    Historical Conditional Value at Risk(CVaR),
    also known as Expected Shortfall (ES).

    CVaR measures the average loss in the worst
    (1 - confidence_level) portion of returns.
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.95
    DEFAULT_PERIODS_PER_YEAR = 252

    def analyze(
        self, 
        dataframe: pd.DataFrame,
        *,
        symbol: str,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
        periods_per_year: int = DEFAULT_PERIODS_PER_YEAR,
    ) -> dict[str, Any]:

        self._validate_inputs(
            dataframe=dataframe,
            symbol=symbol,
            confidence_level=confidence_level,
            periods_per_year=periods_per_year,
        )

        prices = self._extract_prices(dataframe, symbol)
        returns = prices.pct_change().dropna()

        if returns.empty:
            raise ValueError(
                f"Insufficient price data for CVaR analysis of '{symbol}'."
            )

        returns_array = returns.to_numpy(dtype=float)

        if not np.all(np.isfinite(returns_array)):
            raise ValueError(
                f"Price data for '{symbol}' contains non-finite returns."
            )

        return_count = len(returns_array)

        if return_count < 2:
            raise ValueError(
                f"At least 2 valid returns are required for CVaR analysis of '{symbol}'."
            )

        tail_probability = 1.0 - confidence_level

        #Historical VaR threshold
        var_quantile = np.quantile(
            returns_array,
            tail_probability,
        )

        #Returns below/equal to the VaR return threshold constitute the historical tail.
        tail_returns = returns_array[returns_array <= var_quantile]

        if len(tail_returns) == 0:
            raise ValueError(
                "Unable to identify tail observation for CVaR calculation."
            )

        #Convert return loss into a positive risk number.
        cvar = -float(np.mean(tail_returns))

        #Historical VaR represented as a positive loss.
        var = -float(var_quantile)

        mean_return = float(np.mean(returns_array))
        return_volatility = float(
            np.std(returns_array, ddof=1)
        ) if return_count > 1 else 0.0

        return {
            "symbol": symbol,
            "method": "historical",
            "confidence_level": confidence_level,
            "tail_probability": tail_probability,
            "return_count": return_count,
            "tail_return_count": len(tail_returns),
            "periods_per_year": periods_per_year,
            "mean_return": mean_return,
            "return_volatility": return_volatility,
            "var": var,
            "var_percent": var * 100.0,
            "cvar": cvar,
            "cvar_percent": cvar * 100.0,
        }


    @staticmethod
    def _validate_inputs(
        *, 
        dataframe: pd.DataFrame,
        symbol: str,
        confidence_level: float,
        periods_per_year: int,
    ) -> None:

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "Dataframe must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame cannot be empty."
            )

        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError(
                "Symbol must be a non-empty string."
            )

        if not 0.0 < confidence_level < 1.0:
            raise ValueError(
                "confidence_level must be between 0 and 1."
            )

        if not isinstance(periods_per_year, int) or periods_per_year <= 0:
            raise ValueError(
                "periods_per_year must be a positive integer."
            )


    @staticmethod
    def _extract_prices(
        dataframe: pd.DataFrame,
        symbol: str,
    ) -> pd.Series:

        if symbol not in dataframe.columns:
            raise ValueError(
                f"Symbol '{symbol}' not found in dataframe columns."
            )

        prices = pd.to_numeric(
            dataframe[symbol],
            errors="coerce",
        ).dropna()

        if prices.empty:
            raise ValueError(
                f"No valid price observations found for '{symbol}'."
            )

        if (prices <= 0).any():
            raise ValueError(
                f"Price series for '{symbol}' must contain only positive values."
            )

        return prices