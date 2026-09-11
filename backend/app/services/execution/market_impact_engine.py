from __future__ import annotations

from decimal import Decimal
from typing import Literal


class MarketImpactEngine:
    """
    Calculate a side-adjusted market-impact proxy.

    Quantara v1 definition:
        Market Impact Proxy = side-adjusted movement from arrival price
        to the market price at the end of execution.

    Positive values represent adverse market movement.
    Negative values represent favourable market movement.

    BUY:
        end_market_price > arrival_price -> positive impact

    SELL:
        end_market_price < arrival_price -> negative impact

    This is a market-movement proxy, not a casual estimate of price impact caused by the trader's own order.
    """


    def calculate_market_impact(
        self,
        *,
        side: Literal["buy", "sell"],
        arrival_price: float | Decimal,
        end_market_price: float | Decimal,
        executed_quantity: float | Decimal,
    ) -> dict:

        arrival = Decimal(str(arrival_price))
        end_price = Decimal(str(end_market_price))
        quantity = Decimal(str(executed_quantity))

        if side not in {"buy", "sell"}:
            raise ValueError(
                f"Unsupported execution side: {side}."
            )

        if arrival <= 0:
            raise ValueError(
                "Arrival price must be greater than zero."
            ) 

        if end_price <= 0:
            raise ValueError(
                "End market price must be greater than zero."
            )

        if quantity <= 0:
            raise ValueError(
                "Executed quantity must be greater than zero."
            )

        if side == "buy":
            impact_per_share = end_price - arrival

        else:
            impact_per_share = arrival - end_price

        total_impact = impact_per_share * quantity

        percentage_impact = (
            impact_per_share / arrival
        ) * Decimal("100")

        return {
            "side": side,
            "arrival_price": float(arrival),
            "end_market_price": float(end_price),
            "executed_quantity": float(quantity),
            "impact_per_share": float(impact_per_share),
            "percentage_impact": float(percentage_impact),
            "total_impact": float(total_impact),
        }