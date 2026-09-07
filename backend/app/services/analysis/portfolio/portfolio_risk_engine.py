from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.analysis.cvar_analyzer import CVaRAnalyzer
from app.services.analysis.var_analyzer import VaRAnalyzer

from app.services.analysis.portfolio.portfolio_validator import(
    PortfolioValidationError,
    PortfolioValidator,
)


class PortfolioRiskEngine:
    """
    Portfolio-level risk analytics engine.

    Portfolio Risk Engine v1 focuses on:
        - portfolio return series
        - covariance matrix
        - portfolio volatility
        - basic portfolio statistics

    More advanced metrics will be added incremently.
    """

    def __init__(
        self,
        periods_per_year: int = 252,    
    ) -> None:

        if(
            not isinstance(periods_per_year, int)
            or isinstance(periods_per_year, bool)
            or periods_per_year <= 0
        ):
            raise PortfolioValidationError(
                "periods_per_year must be a positive integer."
            )

        self.periods_per_year = periods_per_year


    def analyze(
        self,
        prices: pd.DataFrame,
        holdings: pd.DataFrame,
        symbol_column: str = "symbol",
        weight_column: str = "weight",
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """
        Calculate portfolio-level risk metrics.

        Parameters:
            prices:
                DataFrame containing historical prices.
                Columns must contain portfolio symbols.
            
            holdings:
                DataFrame containing:
                    symbol
                    weight
            
            confidence_level:
                Confidence level used for historical VaR/CVaR.
                Example: 0.95 = 95% confidence

        Returns:
            dict:
                Portfolio risk analytics.
        """

        PortfolioValidator.validate_holdings(
            holdings=holdings,
            symbol_column=symbol_column,
            weight_column=weight_column,
        )

        self._validate_confidence_level(confidence_level)

        symbols = (
            holdings[symbol_column]
            .astype(str)
            .str.strip()
            .tolist()
        )

        weights = holdings[weight_column].astype(float).to_numpy()

        PortfolioValidator.validate_price_data(
            prices=prices,
            symbols=symbols,
        )

        price_data = prices[symbols].copy()

        returns = self._calculate_returns(price_data)

        if returns.empty:
            raise PortfolioValidationError(
                "insufficient price history to calculate portfolio returns."
            )

        covariance_matrix = returns.cov()

        portfolio_returns = returns.to_numpy() @ weights

        if len(portfolio_returns) < 2:
            raise PortfolioValidationError(
                "At least 2 portfolio return observations are required."
            )

        if not np.isfinite(portfolio_returns).all():
            raise PortfolioValidationError(
                "Portfolio returns contain non-finite values."
            )

        portfolio_mean_return = float(np.mean(portfolio_returns))

        portfolio_volatility = float(
            np.std(
                portfolio_returns,
                ddof=1,
            )
        )

        annualized_return = (
            portfolio_mean_return * self.periods_per_year
        )

        annualized_volatility = (
            portfolio_volatility
            * np.sqrt(self.periods_per_year)
        )

        risk_contribution = self._calculate_risk_contribution(
            covariance_matrix=covariance_matrix,
            weights=weights,
            symbols=symbols,
            portfolio_volatility=portfolio_volatility,
        )

        concentration = self._calculate_concentration(
            symbols=symbols,
            weights=weights,
            risk_contribution=risk_contribution,
        )

        tail_risk = self._calculate_tail_risk(
            portfolio_returns=portfolio_returns,
            confidence_level=confidence_level,
        )

        return {
            "portfolio": {
                "asset_count": len(symbols),
                "symbols": symbols,
                "total_weight": float(weights.sum()),
            },
            "performance": {
                "mean_period_return": portfolio_mean_return,
                "annualized_return": annualized_return,
                "return_count": len(portfolio_returns),
            },
            "risk": {
                "period_volatility": portfolio_volatility,
                "annualized_volatility": annualized_volatility,
            },
            "tail_risk": tail_risk,
            "weights": {
                symbol: float(weight)
                for symbol, weight in zip(symbols, weights)
            },
            "risk_contribution": risk_contribution,
            "concentration": concentration,
            "covariance_matrix": covariance_matrix.to_dict(),
        }


    @staticmethod
    def _calculate_returns(
        prices: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Calculate aligned asset returns.

        Rows containing missing values after return calculation
        are removed so portfolio returns are computed on a common
        observation window.
        """

        returns = prices.pct_change(fill_method=None)

        returns = returns.replace(
            [np.inf, -np.inf],
            np.nan,
        )

        returns = returns.dropna(how="any")

        return returns


    @staticmethod
    def _calculate_tail_risk(
        portfolio_returns: np.ndarray,
        confidence_level: float,
    ) -> dict[str, Any]:
        """
        Calculate historical portfolio VaR and CVaR.

        The existing VaRAnalyzer and CVaRAnalyzer operate on price data. Here we already
        have the portfolio return series, so the mathematical calculation is performed
        directly on that series.

        VaR:
            Positive loss threshold at the specified confidence.
        CVaR:
            Average loss among observations at or beyond VaR.
        """

        returns =  np.asarray(
            portfolio_returns,
            dtype=float,
        )

        if returns.ndim != 1:
            raise PortfolioValidationError(
                "Portfolio returns must be a one-dimensional array."
            )

        if len(returns) < 2:
            raise PortfolioValidationError(
                "At least 2 observations are required for VaR/CVar."
            )

        if not np.isfinite(returns).all():
            raise PortfolioValidationError(
                "Portfolio returns contain non-finite values."
            )

        tail_probability = 1.0 - confidence_level

        var_quantile = float(
            np.quantile(
                returns,
                tail_probability,
            )
        )

        var = max(
            0.0,
            -var_quantile,
        )

        tail_returns = returns[
            returns <= var_quantile
        ]

        if len(tail_returns) == 0:
            raise PortfolioValidationError(
                "Unable to identify tail observations for CVaR"
            )

        cvar = max(
            0.0,
            -float(np.mean(tail_returns)),   
        )

        return {
            "method": "historical",
            "confidence_level": confidence_level,
            "tail_probability": tail_probability,
            "return_count": int(len(returns)),
            "tail_return_count": int(len(tail_returns)),
            "var": float(var),
            "var_percent": float(var * 100.0),
            "cvar": float(cvar),
            "cvar_percent": float(cvar * 100.0),
        }


    @staticmethod
    def _validate_confidence_level(
        confidence_level: float,
    ) -> None:

        if not isinstance(
            confidence_level,
            (int, float),
        ) or isinstance(
            confidence_level,
            bool,
        ):
            raise PortfolioValidationError(
                "confidence_level must be a number."
            )

        if not 0.0 < confidence_level < 1.0:
            raise PortfolioValidationError(
                "confidence_level must be between 0 and 1."
            )


    @staticmethod
    def _calculate_risk_contribution(
        covariance_matrix: pd.DataFrame,
        weights: np.ndarray,
        symbols: list[str],
        portfolio_volatility: float,
    ) -> dict[str, Any]:

        if portfolio_volatility <= 0:
            raise PortfolioValidationError(
                "Portfolio volatility must be greater than zero to calculate risk contribution."
            )

        covariance = covariance_matrix.to_numpy()

        # Sigma * w
        marginal_variance_contribution = covariance @ weights

        # Marginal Contribution to Risk
        marginal_contribution = (
            marginal_variance_contribution
            / portfolio_volatility
        )

        # Component Contribution to Risk
        component_contribution = (
            weights * marginal_contribution
        )

        # Percentage Contribution to Risk
        percentage_contribution = (
            component_contribution
            / portfolio_volatility
        )

        total_component_contribution = float(
            component_contribution.sum()
        )

        total_percentage_contribution = float(
            percentage_contribution.sum()
        )

        return {
            "portfolio_volatility": portfolio_volatility,
            "total_component_contribution": total_component_contribution,
            "total_percentage_contribution": total_percentage_contribution,
            "by_asset": {
                symbol: {
                    "weight": float(weight),
                    "marginal_contribution": float(mrc),
                    "component_contribution": float(crc),
                    "percentage_contribution": float(prc),
                }
                for symbol, weight, mrc, crc, prc in zip(
                    symbols,
                    weights,
                    marginal_contribution,
                    component_contribution,
                    percentage_contribution,
                )
            },
        }


    @staticmethod
    def _calculate_concentration(
        symbols: list[str],
        weights: np.ndarray,
        risk_contribution: dict[str, Any],
    ) -> dict[str, Any]:
        """ HHI
        HHI = sum(weight_i ^ 2)
        For a perfectly equal portfolio of N assets:
            HHI = 1 / N
        For a portfolio concentrated in one asset:
            HHI = 1
        """

        hhi = float(np.sum(weights ** 2))

        #Effective number of positions
        effective_number_of_positions = float(1.0 / hhi)

        #Largest Position
        largest_position_index = int(np.argmax(weights))

        largest_position = {
            "symbol": symbols[largest_position_index],
            "weight": float(weights[largest_position_index]),
        }

        #Top-N concentration
        sorted_weights = np.sort(weights)[::-1]

        top_1_concentration = float(
            sorted_weights[:1].sum()
        )

        top_3_concentration = float(
            sorted_weights[:3].sum()
        )

        top_5_concentration = float(
            sorted_weights[:5].sum()
        )

        #Largest risk contributor
        risk_by_asset = risk_contribution["by_asset"]

        largest_risk_symbol = max(
            risk_by_asset,
            key=lambda symbol: risk_by_asset[symbol]["percentage_contribution"],
        )

        largest_risk_contribution = risk_by_asset[largest_risk_symbol]["percentage_contribution"]

        #Weight vs risk concentration
        risk_weight_ratio = {}

        for symbol in symbols:
            weight = risk_by_asset[symbol]["weight"]
            risk_percentage = risk_by_asset[symbol]["percentage_contribution"]

            if weight > 0:
                risk_weight_ratio[symbol] = float(
                    risk_percentage / weight
                )

            else:
                risk_weight_ratio[symbol] = None

        return {
            "hhi": hhi,
            "effective_number_of_positions": effective_number_of_positions,
            "largest_position": largest_position,
            "top_n_concentration": {
                "top_1": top_1_concentration,
                "top_3": top_3_concentration,
                "top_5": top_5_concentration,
            },
            "largest_risk_contributor": {
                "symbol": largest_risk_symbol,
                "percentage_contribution": float(largest_risk_contribution),
            },
            "risk_to_weight_ratio": risk_weight_ratio,
        }