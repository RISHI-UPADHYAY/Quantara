from __future__ import annotations

from decimal import Decimal
from typing import Literal


class SlippageEngine:
    """
    Calculate execution slippage against a benchmark price.

    Positive slippage represents an execution cost.
    Negative slippage represents favorable execution.

    BUY:
        execution > benchmark -> positive cost

    SELL:
        execution < benchmark -> positive cost
    """

    def calculate_slippage(
        self,
        *,
        side: Literal["buy", "sell"],
        benchmark_price: float | Decimal,
        execution_price: float | Decimal,
        executed_quantity: float | Decimal,
    ) -> dict:
        benchmark = Decimal(str(benchmark_price))
        execution = Decimal(str(execution_price))
        quantity = Decimal(str(executed_quantity))

        if side not in {"buy", "sell"}:
            raise ValueError(f"Unsupported execution side: {side}.")

        if benchmark <= 0:
            raise ValueError(
                "Benchmark price must be greater than zero."
            )

        if execution <= 0:
            raise ValueError(
                "Execution price must be greater than zero."
            )

        if quantity <= 0:
            raise ValueError(
                "Executed quantity must be greater than zero."
            )

        if side == "buy":
            price_slippage = execution - benchmark
        else:
            price_slippage = benchmark - execution

        percentage_slippage = (
            price_slippage / benchmark
        ) * Decimal("100")

        total_slippage = price_slippage * quantity

        return {
            "side": side,
            "benchmark_price": float(benchmark),
            "execution_price": float(execution),
            "executed_quantity": float(quantity),
            "price_slippage": float(price_slippage),
            "percentage_slippage": float(percentage_slippage),
            "total_slippage": float(total_slippage),
        }