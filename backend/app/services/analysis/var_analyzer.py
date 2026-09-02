from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class VaRAnalyzer:
    """
    Calculate Value at Risk (VaR) from historical price data.

    Supported methods:
        - historical
        - parametric

    VaR is expressed as a positive loss magnitude.

    Example:
        confidence_level: 0.95
        VaR = 0.025
    means that the estimated loss threshold is 2.5% at the 
    95% confidence level.
    """

    DEFAULT_CONFIDENCE_LEVEL = 0.95
    DEFAULT_METHOD = "historical"

    SUPPORTED_METHODS = {
        "historical",
        "parametric",
    }

    def analyze(
        self,
        dataframe: pd.DataFrame,
        *,
        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
        method: str = DEFAULT_METHOD,
        periods_per_year: int = 252,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Calculate Value at Risk from price returns.
        """

        self._validate_dataframe(dataframe)

        self._validate_parameters(
            confidence_level=confidence_level,
            method=method,
            periods_per_year=periods_per_year,
        )

        price_series = self._extract_price_series(dataframe)

        returns = price_series.pct_change().dropna()

        if returns.empty:
            raise ValueError(
                "At least two valid price observations are required."
            )

        returns_array = returns.to_numpy(dtype=float)

        if not np.isfinite(returns_array).all():
            raise ValueError(
                "Price data produced non-finite returns."
            )

        if method == "historical":
            var = self._historical_var(
                returns_array,
                confidence_level,
            )

        elif method == "parametric":
            var = self._parametric_var(
                returns_array,
                confidence_level,
            )

        else:
            raise ValueError(
                f"Unsupported VaR method: {method}"
            )

        tail_probability = 1.0 - confidence_level

        var_percent = float(var * 100.0)

        return {
            "symbol": symbol,
            "method": method,
            "confidence_level": confidence_level,
            "tail_probability": tail_probability,
            "return_count": int(len(returns)),
            "periods_per_year": periods_per_year,
            "mean_return": float(returns.mean()),
            "return_volatility": float(returns.std(ddof=1)),
            "var": float(var),
            "var_percent": var_percent,
        }


    @staticmethod
    def _historical_var(
        returns: np.ndarray,
        confidence_level: float,
    ) -> float:
        """
        Historical VaR based on the lower return quantile.
        """

        quantile = np.quantile(
            returns,
            1.0 - confidence_level,
        )

        #Convert negative return threshold into positive loss magnitude.
        return float(max(0.0, -quantile))


    @staticmethod
    def _parametric_var(
        returns: np.ndarray,
        confidence_level: float,
    ) -> float:
        """
        Parametric VaR assuming normally distributed returns.
        """

        mean_return = float(np.mean(returns))
        volatility = float(np.std(returns, ddof=1))

        if volatility == 0.0:
            return float(max(0.0, -mean_return))

        z_score = float(
            VaRAnalyzer._normal_quantile(
                1.0 - confidence_level
            )
        )

        loss_threshold = -(
            mean_return + z_score * volatility
        )

        return float(max(0.0, loss_threshold))


    @staticmethod
    def _normal_quantile(probability: float) -> float:
        """
        Inverse standard normal CDF.

        Uses numpy's available implementation when present,
        otherwise uses the Abramowitz-Stegun approximation.
        """

        try:
            from statistics import NormalDist

            return NormalDist().inv_cdf(probability)

        except (ImportError, AttributeError):
            # Abramowitz-Stegun approximation.
            a1 = -39.6968302866538
            a2 = 220.946098424521
            a3 = -275.928510446969
            a4 = 138.357751867269
            a5 = -30.6647980661472
            a6 = 2.50662827745924

            b1 = -54.4760987982241
            b2 = 161.585836858041
            b3 = -155.698979859887
            b4 = 66.8013118877197
            b5 = -13.2806815528857

            c1 = -0.00778489400243029
            c2 = -0.322396458041136
            c3 = -2.40075827716184
            c4 = -2.54973253934373
            c5 = 4.37466414146497
            c6 = 2.93816398269878

            d1 = 0.00778469570904146
            d2 = 0.32246712907004
            d3 = 2.445134137143
            d4 = 3.75440866190742

            p_low = 0.02425
            p_high = 1.0 - p_low

            if probability < p_low:
                q = np.sqrt(
                    -2.0 * np.log(probability)
                )

                return (
                    (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) 
                    /
                    ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)
                )

            if probability > p_high:
                q = np.sqrt(
                    -2.0 * np.log(1.0 - probability)
                )

                return -(
                    (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) 
                    /
                    ((((d1 * q + d2) * q + d3) * q + d4) * q + 1.0)
                )

            q = probability - 0.5
            r = q * q

            return (
                ((((((a1 * r + a2) * r + a3) * r + a4) * r + a5) * r + a6) *   q)
                /
                (((((b1 * r + b2) * r + b3) * r + b4) * r + b5) * r + 1.0)
            )

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
        confidence_level: float,
        method: str,
        periods_per_year: int,
    ) -> None:

        if not (
            0.0 < confidence_level < 1.0
        ):
            raise ValueError(
                "confidence_level must be between 0 and 1."
            )

        if not isinstance(method, str):
            raise TypeError(
                "method must be a string."
            )

        method = method.strip().lower()

        if method not in VaRAnalyzer.SUPPORTED_METHODS:
            supported = ", ".join(
                sorted(VaRAnalyzer.SUPPORTED_METHODS)
            )

            raise ValueError(
                f"Unsupported VaR method '{method}'. "
                f"Supported methods: {supported}."
            )

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

            series = dataframe[
                numeric_columns[0]
            ]

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