from __future__ import annotations

import uuid
import pandas as pd
from decimal import Decimal

from fastapi import HTTPException, status

from app.services.execution.benchmark_engine import BenchmarkEngine
from app.services.execution.slippage_engine import SlippageEngine   
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.services.execution.implementation_shortfall_engine import ImplementationShortfallEngine
from app.services.execution.market_impact_engine import MarketImpactEngine
from app.services.execution.execution_quality_engine import ExecutionQualityEngine


class TCAEngine:

    def __init__(
        self,
        order_repository: ExecutionOrderRepository,
        fill_repository: ExecutionFillRepository,
        benchmark_engine: BenchmarkEngine | None = None,
        slippage_engine: SlippageEngine | None = None,
        implementation_shortfall_engine: ImplementationShortfallEngine | None = None,
        market_impact_engine: MarketImpactEngine | None = None,
        execution_quality_engine: ExecutionQualityEngine | None = None,
    ):
        self.order_repository = order_repository
        self.fill_repository = fill_repository
        self.benchmark_engine = benchmark_engine or BenchmarkEngine(
            order_repository=order_repository,
        )
        self.slippage_engine = slippage_engine or SlippageEngine()
        self.implementation_shortfall_engine = implementation_shortfall_engine or ImplementationShortfallEngine()
        self.market_impact_engine = market_impact_engine or MarketImpactEngine()
        self.execution_quality_engine = execution_quality_engine or ExecutionQualityEngine()


    def calculate_execution_statistics(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        market_data: pd.DataFrame | None = None,
    ) -> dict:

        order = self.order_repository.get_by_id_in_project(
            order_id=order_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution order not found."
            )

        fills = self.fill_repository.list_by_order(
            execution_order_id=order.id,
        )

        if not fills:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Cannot calculate TCA for an order with no fills."
            )

        order_quantity = Decimal(str(order.quantity))

        executed_quantity = sum(
            (Decimal(str(fill.quantity)) for fill in fills),
            Decimal("0"),
        )

        gross_notional = sum(
            (
                Decimal(str(fill.price))
                * Decimal(str(fill.quantity))
                for fill in fills
            ),
            Decimal("0"),
        )

        commission = sum(
            (
                Decimal(str(fill.commission))
                for fill in fills
                if fill.commission is not None
            ),
            Decimal("0"),
        )

        fees = sum(
            (
                Decimal(str(fill.fees))
                for fill in fills
                if fill.fees is not None
            ),
            Decimal("0"),
        )

        if executed_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Executed quantity must be greater than zero."
            )

        average_execution_price = (
            gross_notional / executed_quantity
        )

        total_cost = commission + fees

        cost_per_share = total_cost / executed_quantity

        net_execution_cost = gross_notional + total_cost

        remaining_quantity = (
            order_quantity - executed_quantity
        )

        arrival_price = None
        arrival_timestamp = None
        market_vwap = None
        market_twap = None
        end_market_price = None
        market_impact_per_share = None
        percentage_market_impact = None
        total_market_impact = None
        market_impact_timestamp = None

        if market_data is not None:
            arrival_result = self.benchmark_engine.calculate_arrival_price(
                organization_id=organization_id,
                project_id=project_id,
                order_id=order_id,
                market_data=market_data,
            )

            arrival_price = arrival_result["arrival_price"]
            arrival_timestamp = arrival_result["arrival_timestamp"]

            start_timestamp = pd.Timestamp(order.submitted_at)
            end_timestamp = pd.Timestamp(
                max(fill.executed_at for fill in fills)
            )

            end_market_result = self.benchmark_engine.calculate_end_market_price(
                order_symbol=order.symbol,
                market_data=market_data,
                end_timestamp=end_timestamp,
            )

            end_market_price = end_market_result["end_market_price"]
            market_impact_timestamp = end_market_result["market_price_timestamp"]

            market_impact_result = self.market_impact_engine.calculate_market_impact(
                side=order.side,
                arrival_price=arrival_price,
                end_market_price=end_market_price,
                executed_quantity=executed_quantity,
            )

            market_impact_per_share = market_impact_result["impact_per_share"]

            percentage_market_impact = market_impact_result["percentage_impact"]

            total_market_impact = market_impact_result["total_impact"]

            vwap_result = self.benchmark_engine.calculate_market_vwap(
                order_symbol=order.symbol,
                market_data=market_data,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )

            twap_result = self.benchmark_engine.calculate_market_twap(
                order_symbol=order.symbol,
                market_data=market_data,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
            )

            market_vwap = vwap_result["vwap"]
            market_twap = twap_result["twap"]

        price_slippage = None
        percentage_slippage = None
        total_slippage = None
        price_shortfall = None
        percentage_shortfall = None
        total_shortfall = None
        explicit_costs = None

        if arrival_price is not None:
            slippage_result = self.slippage_engine.calculate_slippage(
                side=order.side,
                benchmark_price=arrival_price,
                execution_price=average_execution_price,
                executed_quantity=executed_quantity,
            )

            price_slippage = slippage_result["price_slippage"]
            percentage_slippage = slippage_result["percentage_slippage"]
            total_slippage = slippage_result["total_slippage"]

            shortfall_result = self.implementation_shortfall_engine.calculate(
                side=order.side,
                arrival_price=arrival_price,
                execution_price=average_execution_price,
                executed_quantity=executed_quantity,
                commission=commission,
                fees=fees,
            )

            price_shortfall = shortfall_result["price_shortfall"]
            percentage_shortfall = shortfall_result["percentage_shortfall"]
            total_shortfall = shortfall_result["total_shortfall"]
            explicit_costs = shortfall_result["explicit_costs"]

        execution_quality = None

        if (
            arrival_price is not None
            and market_vwap is not None
            and total_slippage is not None
            and total_shortfall is not None
            and total_market_impact is not None
        ):

            execution_quality = self.execution_quality_engine.calculate_execution_quality(
                arrival_price=arrival_price,
                execution_price=average_execution_price,
                market_vwap=market_vwap,
                total_slippage=total_slippage,
                total_shortfall=total_shortfall,
                total_market_impact=total_market_impact,
                executed_quantity=executed_quantity,
                side=order.side,
            )

        return {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side,
            "ordered_quantity": float(order_quantity),
            "executed_quantity": float(executed_quantity),
            "remaining_quantity": float(remaining_quantity),
            "fill_count": len(fills),
            "average_execution_price": float(average_execution_price),
            "execution_vwap": float(average_execution_price),
            "gross_notional": float(gross_notional),
            "commission": float(commission),
            "fees": float(fees),
            "cost_per_share": float(cost_per_share),
            "net_execution_cost": float(net_execution_cost),
            "is_fully_filled": executed_quantity == order_quantity,
            "arrival_price": arrival_price,
            "arrival_timestamp": arrival_timestamp,
            "market_vwap": market_vwap,
            "market_twap": market_twap,
            "price_slippage": price_slippage,
            "percentage_slippage": percentage_slippage,
            "total_slippage": total_slippage,
            "price_shortfall": price_shortfall,
            "percentage_shortfall": percentage_shortfall,
            "total_shortfall": total_shortfall,
            "explicit_costs": explicit_costs,
            "end_market_price": end_market_price,
            "market_impact_timestamp": market_impact_timestamp,
            "market_impact_per_share": market_impact_per_share,
            "percentage_market_impact": percentage_market_impact,
            "total_market_impact": total_market_impact,
            "execution_quality": execution_quality,
        }