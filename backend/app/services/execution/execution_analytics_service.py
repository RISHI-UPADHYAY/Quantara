from __future__ import annotations

import uuid
from collections import defaultdict

from fastapi import HTTPException

from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.services.execution.tca_engine import TCAEngine


class ExecutionAnalyticsService:

    BATCH_OUTLIER_THRESHOLDS = {
        "slippage_percentage": 0.10,
        "vwap_deviation_percentage": 0.10,
        "shortfall_percentage": 0.15,
        "explicit_cost_percentage": 0.05,
    }

    def __init__(
        self,
        *,
        order_repository: ExecutionOrderRepository,
        fill_repository: ExecutionFillRepository,
    ):

        self.order_repository = order_repository
        self.tca_engine = TCAEngine(
            order_repository=order_repository,
            fill_repository=fill_repository,
        )


    def analyze(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        market_data,
        symbol: str | None = None,
        side: str | None = None,
        strategy: str | None = None,
        algorithm: str | None = None,
        venue: str | None = None,
        start_time = None,
        end_time = None,
        limit: int = 100,
    ) -> dict:

        orders = self.order_repository.list_for_analytics(
            organization_id=organization_id,
            project_id=project_id,
            symbol=symbol,
            side=side,
            strategy=strategy,
            algorithm=algorithm,
            venue=venue,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        results = []
        failed_orders = []

        for order in orders:
            try:
                result = self.tca_engine.calculate_execution_statistics(
                    organization_id=organization_id,
                    project_id=project_id,
                    order_id=order.id,
                    market_data=market_data,
                )

                result["_order"] = order
                result["_exception_codes"] = self._exception_codes(result)

                results.append(result)

            except HTTPException as exc:
                failed_orders.append(
                    {
                        "order_id": order.id,
                        "status_code": exc.status_code,
                        "detail": str(exc.detail),
                    }
                )

        summary = self._aggregate(results)

        return {
            "filters": {
                "symbol": symbol,
                "side": side,
                "strategy": strategy,
                "algorithm": algorithm,
                "venue": venue,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
            },
            "summary": {
                **summary,
                "requested": len(orders),
                "analyzed": len(results),
                "failed": len(failed_orders),
            },
            "by_symbol": self._breakdown(
                results,
                lambda r: r["_order"].symbol,
            ),
            "by_side": self._breakdown(
                results,
                lambda r: r["_order"].side
            ),
            "by_venue": self._breakdown(
                results,
                lambda r: r["_order"].venue or "UNKNOWN",
            ),
            "by_date": self._breakdown(
                results,
                lambda r: r["_order"].submitted_at.date().isoformat(),
            ),
            "failed_orders": failed_orders,
        }


    def _exception_codes(
        self,
        result: dict,
    ) -> list[str]:

        codes = []

        slippage = result.get("percentage_slippage")

        if (
            slippage is not None
            and slippage > self.BATCH_OUTLIER_THRESHOLDS["slippage_percentage"]
        ):

            codes.append("HIGH_SLIPPAGE")

        market_vwap = result.get("market_vwap")
        execution_vwap = result.get("execution_vwap")
        side = result.get("side")

        if (
            market_vwap is not None
            and market_vwap > 0
            and execution_vwap is not None
            and side in  {"buy", "sell"}
        ):

            direction = 1 if side == "buy" else -1

            deviation = (
                direction
                * (execution_vwap - market_vwap)
                / market_vwap
                * 100
            )

            if deviation > self.BATCH_OUTLIER_THRESHOLDS[
                "vwap_deviation_percentage"
            ]: 

                codes.append("WORSE_THAN_MARKET_VWAP")

        shortfall = result.get("percentage_shortfall")

        if (
            shortfall is not None
            and shortfall > self.BATCH_OUTLIER_THRESHOLDS[
                "shortfall_percentage"
            ]
        ):

            codes.append("HIGH_IMPLEMENTATION_SHORTFALL")

        gross_notional = result.get("gross_notional") or 0
        explicit_costs = (
            (result.get("commission") or 0)
            + (result.get("fees") or 0)
        )

        if gross_notional > 0:
            explicit_cost_pct = (
                explicit_costs / gross_notional * 100
            )

            if explicit_cost_pct > self.BATCH_OUTLIER_THRESHOLDS[
                "explicit_cost_percentage"
            ]:

                codes.append("HIGH_IMPLICIT_COSTS")

        return codes


    def _aggregate(
        self,
        results: list[dict],
    ) -> dict:

        ordered_quantity = sum(
            r["ordered_quantity"] for r in results
        )

        executed_quantity = sum(
            r["executed_quantity"] for r in results
        )

        gross_notional = sum(
            r["gross_notional"] for r in results
        )

        explicits_costs = sum(
            (r["commission"] + r["fees"])
            for r in results
        )

        fill_rate = (
            executed_quantity / ordered_quantity * 100
            if ordered_quantity > 0
            else None
        )

        slippage_numerator = 0.0
        slippage_denominator = 0.0

        shortfall_numerator = 0.0
        shortfall_denominator = 0.0

        vwap_numerator = 0.0
        vwap_denominator = 0.0

        quality_weighted_sum = 0.0
        quality_weight = 0.0

        issue_counts = defaultdict(int)
        orders_with_exceptions = 0
        total_exceptions = 0

        for result in results:

            executed = result["executed_quantity"]

            arrival = result.get("arrival_price")

            if arrival is not None and executed > 0:
                denominator = arrival * executed

                slippage_numerator += (
                    result.get("total_slippage") or 0
                )

                slippage_denominator += denominator

                shortfall_numerator += (
                    result.get("total_shortfall") or 0
                )

                shortfall_denominator += denominator

            market_vwap = result.get("market_vwap")
            execution_vwap = result.get("execution_vwap")
            side = result.get("side")

            if (
                market_vwap is not None
                and market_vwap > 0
                and execution_vwap is not None
                and executed > 0
                and side in {"buy", "sell"}
            ):

                direction = 1 if side == "buy" else -1

                vwap_numerator += (
                    direction
                    * (execution_vwap - market_vwap)
                    * executed
                )

                vwap_denominator += (
                    market_vwap * executed
                )

            quality = result.get("execution_quality")

            if quality is not None:
                score = quality.get("score")

                if score is not None and executed > 0:
                    quality_weighted_sum += score * executed
                    quality_weight += executed

            exception_codes = result["_exception_codes"]

            if exception_codes:
                orders_with_exceptions += 1
                total_exceptions += len(exception_codes)

                for code in exception_codes:
                    issue_counts[code] += 1

        return {
            "total_ordered_quantity": ordered_quantity,
            "total_executed_quantity": executed_quantity,
            "fill_rate_percentage": fill_rate or 0.0,
            "total_gross_notional": gross_notional,
            "total_explicit_costs": explicits_costs,
            "explicit_cost_percentage": (
                explicits_costs / gross_notional * 100
                if gross_notional > 0
                else 0.0
            ),
            "weighted_slippage_percentage": (
                slippage_numerator /
                slippage_denominator
                * 100
                if slippage_denominator > 0
                else None
            ),
            "weighted_shortfall_percentage": (
                shortfall_numerator / 
                slippage_denominator
                * 100
                if shortfall_denominator > 0
                else None
            ),
            "weighted_vwap_deviation_percentage": (
                vwap_numerator / 
                vwap_denominator
                * 100
                if vwap_denominator > 0
                else None
            ),
            "average_execution_quality_score": (
                quality_weighted_sum / quality_weight
                if quality_weight > 0
                else None
            ),
            "orders_with_exceptions": orders_with_exceptions,
            "total_exceptions": total_exceptions,
            "issue_counts_by_code": dict(issue_counts),
        }


    def _breakdown(
        self,
        results: list[dict],
        key_function,
    ) -> list[dict]:

        groups = defaultdict(list)

        for result in results:
            groups[key_function(result)].append(result)

        breakdowns = []

        for key, group in sorted(groups.items()):

            aggregate = self._aggregate(group)

            breakdowns.append(
                {
                    "key": key,
                    "orders": len(group),
                    "executed_orders": sum(
                        1
                        for result in group
                        if result["executed_quantity"] > 0
                    ),
                    **aggregate,
                }
            )

            return breakdowns