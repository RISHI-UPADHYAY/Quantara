from __future__ import annotations

import math

import pandas as pd


class SharpeAnalyzer:
    """
    Calculates the Sharpe ratio from periodic asset prices.

    Expected DataFrame columns:
        - timestamp
        - symbol
        - close
    The analyzer calculates:
        - periodic returns
        - annualized return
        - annualized volatility
        - Sharpe ratio
        - return statistics
    """

    def analyze(
        self,
        dataframe: pd.DataFrame,
        *,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.0,
        symbol: str | None = None,
    ) -> dict:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                "DataFrame must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "DataFrame is empty."
            )

        if periods_per_year <= 0: 
            raise ValueError(
                "periods_per_year must be greater than zero."
            )

        if not math.isfinite(risk_free_rate):
            raise ValueError(   
                "risk_free_rate must be a finite number."
            )

        data = dataframe.copy()

        required_columns = {
            "timestamp",
            "close",
        }

        missing_columns = required_columns - set(data.columns)

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {sorted(missing_columns)}"
            )

        if symbol is not None:
            if "symbol" not in data.columns:
                raise ValueError(
                    "Symbol column is required when symbol is provided."
                )

            data = data[data["symbol"] == symbol].copy()

            if data.empty:
                raise ValueError(
                    f"No data found for symbol: {symbol}"
                )

        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            errors="coerce",
        )

        data["close"] = pd.to_numeric(
            data["close"],
            errors="coerce",
        )

        data = data.dropna(
            subset=["timestamp", "close"]
        )

        if data.empty:
            raise ValueError(
                "No valid timestamp/close observations found"
            )

        data = (
            data.sort_values("timestamp")
            .drop_duplicates(
                subset=["timestamp"],
                keep="last",
            )
        )

        if len(data) < 2:
            raise ValueError(
                "At least two price observations are required."
            )

        if (data["close"] <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )

        data["return"] = data["close"].pct_change()

        returns = data["return"].dropna()

        if returns.empty:
            raise ValueError(
                "Unable to calculate returns"
            )

        if len(returns) < 2:
            raise ValueError(
                "At least two return observations are required"
            )

        if not pd.Series(
            returns.apply(math.isfinite),
            index=returns.index,
        ).all():
            raise ValueError(
                "Returns contain non-finite values"
            )

        #Convert annual risk free rate into periodic risk-free rate.
        periodic_risk_free_rate = (
            (1.0 + risk_free_rate) ** (1.0 / periods_per_year)
        ) - 1.0

        excess_returns = returns - periodic_risk_free_rate

        mean_excess_return = float(excess_returns.mean())

        periodic_volatility = float(
            excess_returns.std(ddof=1)
        )

        annualized_return = float(
            (1.0 + returns.mean()) * periods_per_year - 1.0
        )

        annualized_volatility = float(
            returns.std(ddof=1) * math.sqrt(periods_per_year)
        )

        annualized_excess_return = float(
            mean_excess_return * periods_per_year
        )

        if periodic_volatility == 0.0:
            sharpe_ratio = None

        else:
            sharpe_ratio = float(
                mean_excess_return
                / periodic_volatility
                * math.sqrt(periods_per_year)
            )

        return {
            "symbol": symbol,
            "return_count": int(len(returns)),
            "periods_per_year": periods_per_year,
            "risk_free_rate": float(risk_free_rate),
            "periodic_risk_free_rate": float(periodic_risk_free_rate),
            "mean_return": float(returns.mean()),
            "mean_excess_return": mean_excess_return,
            "periodic_volatility": periodic_volatility,
            "annualized_return": annualized_return,
            "annualized_excess_return": annualized_excess_return,
            "annualized_volatility": annualized_volatility,
            "sharpe_ratio": sharpe_ratio,
        }