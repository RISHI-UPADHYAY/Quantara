from __future__ import annotations

from decimal import Decimal
from typing import Literal


class ImplementationShortfallEngine:
    """
    Calculate implementation shortfall realtive to the arrival price.

    Positive values represent execution costs.
    Negative values represent favourable execution.

    For BUY:
        execution > arrival -> positive shortfall

    For SELL:
        execution < arrival -> negative shortfall

    Total implementation shortfall includes explicit execution costs such as 
    commission and fees. 
    """

    def calculate(
        self,
        *,
        side: Literal["buy", "sell"],
        arrival_price: float | Decimal,
        execution_price: float | Decimal,
        executed_quantity: float | Decimal,
        commission: float | Decimal = 0,
        fees: float | Decimal = 0,
    ) -> dict:

        arrival = Decimal(str(arrival_price))
        execution = Decimal(str(execution_price))
        quantity = Decimal(str(executed_quantity))
        commission_amount = Decimal(str(commission))
        fees_amount = Decimal(str(fees))

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

        if quantity <= 0:
            raise ValueError(
                "Executed quantity must be greater than zero."
            )

        if commission_amount < 0:
            raise ValueError(
                "Commission cannot be negative."
            )

        if fees_amount < 0: 
            raise ValueError(
                "Fees cannot be negative."
            )

        if side == "buy":
            price_shortfall_per_share = execution - arrival

        else:
            price_shortfall_per_share = arrival - execution

        price_shortfall = (
            price_shortfall_per_share * quantity
        )

        explicit_costs = (
            commission_amount + fees_amount
        )

        total_shortfall = (
            price_shortfall + explicit_costs
        )

        notional_at_arrival = arrival * quantity

        percentage_shortfall = (
            total_shortfall / notional_at_arrival
        ) * Decimal("100")


        return {
            "side": side,
            "arrival_price": arrival_price,
            "execution_quantity": executed_quantity,
            "executed_quantity": executed_quantity,
            "price_shortfall_per_share": float(
                price_shortfall_per_share
            ),
            "price_shortfall": float(price_shortfall),
            "commission": float(commission_amount),
            "fees": float(fees_amount),
            "explicit_costs": float(explicit_costs),
            "total_shortfall": float(total_shortfall),
            "percentage_shortfall": float(percentage_shortfall),
        }