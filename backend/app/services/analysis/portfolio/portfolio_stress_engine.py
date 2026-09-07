from __future__ import annotations

from typing import Any

import pandas as pd
import numpy  as np

from app.services.analysis.portfolio.portfolio_validator import (
    PortfolioValidationError,
    PortfolioValidator,
)
from app.services.analysis.scenario.scenario_resolver import (
    ScenarioResolver,
)


class PortfolioStressEngine:
    """
    Portfolio-level deterministic stress and scenario analysis engine.

    Version 1 supports user-defined asset price shocks.

    A scenario is represented as:
        {
            "AAPL": -0.10,
            "MSFT": -0.15,
            "NVDA": -0.25,
        }
    where each value represents the hypothetical percentage price change for that asset.
    """

    def analyze(
        self,
        holdings: pd.DataFrame,
        shocks: dict[str, Any],
        symbol_column: str = "symbol",
        weight_column: str = "weight",
        scenario_name: str = "Custom Scenario",
    ) -> dict[str, Any]:

        PortfolioValidator.validate_holdings(
            holdings=holdings,
            symbol_column=symbol_column,
            weight_column=weight_column,
        )

        self._validate_shocks(shocks)

        symbols = (
            holdings[symbol_column]
            .astype(str)
            .str.strip()
            .tolist()
        )

        weights = holdings[weight_column].astype(float).to_numpy()

        normalized_shocks = {
            str(symbol).strip(): float(shock)
            for symbol, shock in shocks.items()
        }

        self._validate_scenario_symbols(
            portfolio_symbols=symbols,
            scenario_symbols=list(normalized_shocks.keys()),
        )

        asset_impacts: list[dict[str, Any]] = []

        total_impact = 0.0

        for symbol, weight in zip(symbols, weights):
            shock = normalized_shocks.get(symbol, 0.0)

            contribution = float(weight * shock)
            total_impact += contribution

            asset_impacts.append(
                {
                    "symbol": symbol,
                    "weight": float(weight),
                    "shock": shock,
                    "portfolio_impact": contribution,
                    "portfolio_impact_percent": contribution * 100.0,
                }
            )

        stressed_weights = self._calculate_stressed_weights(
            holdings=holdings,
            shocks=normalized_shocks,
            symbol_column=symbol_column,
            weight_column=weight_column,
        )

        return {
            "scenario": {
                "name": scenario_name,
                "type": "deterministic_price_shock",
                "asset_count": len(normalized_shocks),
                "shocks": normalized_shocks,
            },
            "portfolio": {
                "total_impact": float(total_impact),
                "total_impact_percent": float(total_impact * 100.00),
                "direction": (
                    "loss"
                    if total_impact < 0
                    else "gain"
                    if total_impact > 0
                    else "neutral"
                ),
            },
            "asset_impacts": asset_impacts,
            "stressed_weights": stressed_weights,
        }

    def analyze_scenario(
        self,
        holdings: pd.DataFrame,
        scenario_id: str,
        symbol_column: str = "symbol",
        weight_column: str = "weight",
    ) -> dict[str, Any]:
        """
        Analyze a portfolio under a predefined named scenario.
        """

        scenario = ScenarioResolver.resolve(scenario_id)

        result = self.analyze(
            holdings=holdings,
            shocks=dict(scenario.shocks),
            symbol_column=symbol_column,
            weight_column=weight_column,
            scenario_name=scenario.name,
        )

        result["scenario"]["id"] = scenario_id
        result["scenario"]["description"] = scenario.description

        return result


    @staticmethod
    def _validate_shocks(
        shocks: dict[str, Any],
    ) -> None:
        if not isinstance(shocks, dict):
            raise PortfolioValidationError(
                "shocks must be a dictionary."
            )

        if not shocks:
            raise PortfolioValidationError(
                "At least one scenario shock is required."
            )

        for symbol, shock in shocks.items():
            if not isinstance(symbol, str) or not symbol.strip():
                raise PortfolioValidationError(
                    "Scenario shock symbols must be non-empty strings."
                )

            if(
                not isinstance(shock, (int, float))
                or isinstance(shock, bool)
            ):
                raise PortfolioValidationError(
                    f"Scenario shock for {symbol} must be a number."
                )

            if not np.isfinite(float(shock)):
                raise PortfolioValidationError(
                    f"Scenario shock for {symbol} must be finite."
                )

            if float(shock) <= -1.0:
                raise PortfolioValidationError(
                    f"Scenario shock for {symbol} must be greater than -100%."
                )


    @staticmethod
    def _validate_scenario_symbols(
        portfolio_symbols: list[str],
        scenario_symbols: list[str],
    ) -> None:
        portfolio_set = set(portfolio_symbols)
        unknowns_symbols = sorted(
            set(scenario_symbols) - portfolio_set
        )

        if unknowns_symbols:
            raise PortfolioValidationError(
                f"Scenario contains symbols not present in the portfolio: {unknowns_symbols}"
            )


    @staticmethod
    def _calculate_stressed_weights(
        holdings: pd.DataFrame,
        shocks: dict[str, Any],
        symbol_column: str,
        weight_column: str,
    ) -> dict[str, float]:
        symbols = (
            holdings[symbol_column]
            .astype(str)
            .str.strip()
            .tolist()
        )

        weights = holdings[weight_column].astype(float).to_numpy()

        stressed_values = {}

        for symbol, weight in zip(symbols, weights):
            shock = shocks.get(symbol, 0.0)

            stressed_values[symbol] = float(
                weight * (1.0 + shock)
            )

        total_stressed_value = sum(stressed_values.values())

        if total_stressed_value <= 0.0:
            raise PortfolioValidationError(
                "Scenario produces a non-positive portfolio value."
            )

        normalized_weights = {
            symbol: float(value / total_stressed_value)
            for symbol, value in stressed_values.items()
        }

        return normalized_weights