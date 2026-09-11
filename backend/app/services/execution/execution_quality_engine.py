from __future__ import annotations

from decimal import Decimal


class ExecutionQualityEngine:
    """
    Calculate a deterministic execution-quality score.

    Quantara v1 scoring model:

        Slippage                 = 35%
        Market VWAP              = 30%
        Implementation Shortfall = 25%
        Market Impact            = 10%

    Scores range from 0 to 100.

    Higher score = better execution quality.
    """

    SLIPPAGE_WEIGHT = Decimal("0.35")
    MARKET_VWAP_WEIGHT = Decimal("0.30")
    SHORTFALL_WEIGHT = Decimal("0.25")
    MARKET_IMPACT_WEIGHT = Decimal("0.10")

    SLIPPAGE_TOLERANCE = Decimal("0.25")
    MARKET_VWAP_TOLERANCE = Decimal("0.25")
    SHORTFALL_TOLERANCE = Decimal("0.50")
    MARKET_IMPACT_TOLERANCE = Decimal("0.25")


    def calculate_execution_quality(
        self,
        *,
        arrival_price: float | Decimal,
        execution_price: float | Decimal,
        market_vwap: float | Decimal,
        total_slippage: float | Decimal,
        total_shortfall: float | Decimal,
        total_market_impact: float | Decimal,
        executed_quantity: float | Decimal,
        side: str,
    ) -> dict:

        arrival = Decimal(str(arrival_price))
        execution = Decimal(str(execution_price))
        market_vwap_price = Decimal(str(market_vwap))
        slippage = Decimal(str(total_slippage))
        shortfall = Decimal(str(total_shortfall))
        market_impact = Decimal(str(total_market_impact))
        quantity = Decimal(str(executed_quantity))


        if side not in {"buy", "sell"}:
            raise ValueError(
                f"Unsupported execution side: {side}."
            )

        if arrival <= 0:
            raise ValueError(
                "Arrival price must be greater than zero."
            )

        if execution <= 0:
            raise ValueError(
                "Execution price must be greater than zero."
            )

        if market_vwap_price <= 0:
            raise ValueError(
                "Market VWAP must be greater than zero."
            )

        if quantity <= 0:
            raise ValueError(
                "Executed quantity must be greater than zero."
            )

        # 1. Slippage component
        slippage_percentage = (
            slippage / (arrival * quantity)
        ) * Decimal("100")

        slippage_score = self._score_from_percentage(
            slippage_percentage,
            self.SLIPPAGE_TOLERANCE,
        )

        # 2. Market VWAP component
        if side == "buy":
            market_vwap_cost = (
                execution - market_vwap_price
            )

        else:
            market_vwap_cost = (
                market_vwap_price - execution
            )

        market_vwap_percentage = (
            market_vwap_cost / market_vwap_price
        ) * Decimal("100")

        market_vwap_score = self._score_from_percentage(
            market_vwap_percentage,
            self.MARKET_VWAP_TOLERANCE,
        )

        # 3. Implementation Shortfall component
        shortfall_percentage = (
            shortfall / (arrival * quantity)
        ) * Decimal("100")

        shortfall_score = self._score_from_percentage(
            shortfall_percentage,
            self.SHORTFALL_TOLERANCE,
        )

        # 4. Market Impact component
        market_impact_percentage = (
            market_impact / (arrival * quantity)
        ) * Decimal("100")

        market_impact_score = self._score_from_percentage(
            market_impact_percentage,
            self.MARKET_IMPACT_TOLERANCE,
        )

        # Overall score
        overall_score = (
            slippage_score * self.SLIPPAGE_WEIGHT
            + market_vwap_score * self.MARKET_VWAP_WEIGHT
            + shortfall_score * self.SHORTFALL_WEIGHT
            + market_impact_score * self.MARKET_IMPACT_WEIGHT
        )

        overall_score = max(
            Decimal("0"),
            min(Decimal("100"), overall_score)
        )

        rating = self._rating_for_score(
            overall_score
        )

        return {
            "score": float(overall_score),
            "rating": rating,
            "components": {
                "slippage": {
                    "score": float(slippage_score),
                    "weight": float(self.SLIPPAGE_WEIGHT),
                    "percentage": float(slippage_percentage),
                },
                "market_vwap": {
                    "score": float(market_vwap_score),
                    "weight": float(self.MARKET_VWAP_WEIGHT),
                    "percentage": float(market_vwap_percentage),
                },
                "implementation_shortfall": {
                    "score": float(shortfall_score),
                    "weight": float(self.SHORTFALL_WEIGHT),
                    "percentage": float(shortfall_percentage),
                },
                "market_impact": {
                    "score": float(market_impact_score),
                    "weight": float(self.MARKET_IMPACT_WEIGHT),
                    "percentage": float(market_impact_percentage),
                },
            },
        }


    @staticmethod
    def _score_from_percentage(
        percentage: Decimal,
        tolerance: Decimal,
    ) -> Decimal:
        """
        Convert adverse percentage cost into a 0-100 score.
        """

        if percentage <= Decimal("0"):
            return Decimal("100")

        penalty = (
            percentage / tolerance
        ) * Decimal("100")

        score = Decimal("100") - penalty

        return max(
            Decimal("0"),
            min(Decimal("100"), score),
        )


    @staticmethod
    def _rating_for_score(
        score: Decimal,
    ) -> str:
        if score >= Decimal("90"):
            return "Excellent"

        if score >= Decimal("75"):
            return "Good"

        if score >= Decimal("60"):
            return "Fair"

        if score >= Decimal("40"):
            return "Poor"

        return "Very Poor"