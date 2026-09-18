from __future__ import annotations

import uuid
from decimal import Decimal

import pandas as pd
from fastapi import HTTPException

from app.repositories.execution_order_repository import ExecutionOrderRepository
from app.repositories.execution_fill_repository import ExecutionFillRepository
from app.services.execution.benchmark_engine import BenchmarkEngine
from app.schemas.tca import (
    TCAPreflightFinding,
    TCAPreflightOrderResult,
)


class TCAPreflightService:

    def __init__(
        self,
        *,
        order_repository: ExecutionOrderRepository,
        fill_repository: ExecutionFillRepository,
    ):
        self.order_repository = order_repository
        self.fill_repository = fill_repository
        self.benchmark_engine = BenchmarkEngine(
            order_repository=order_repository,
        )


    @staticmethod
    def _finding(
        code: str,
        severity: str,
        message: str,
        **evidence,
    ) -> TCAPreflightFinding:

        return TCAPreflightFinding(
            code=code,
            severity=severity,
            message=message,
            evidence=evidence,
        )


    def check_order(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        market_data: pd.DataFrame,
    ) -> TCAPreflightOrderResult:

        findings: list[TCAPreflightFinding] = []

        order = self.order_repository.get_by_id_in_project(
            order_id=order_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if order is None:
            findings.append(
                self._finding(
                    "ORDER_NOT_FOUND",
                    "ERROR",
                    "Order was not found in the requested organization and project.",
                )
            )

            return TCAPreflightOrderResult(
                order_id=order_id,
                status="BLOCKED",
                findings=findings,
            )

        fills = self.fill_repository.list_by_order(
            execution_order_id=order.id,
        )

        if not fills:
            findings.append(
                self._finding(
                    "NO_FILLS",
                    "ERROR",
                    "The order has no fills; TCA cannot be calculated."
                )
            )

        else:
            ordered_qty = Decimal(str(order.quantity))
            executed_qty = sum(
                (Decimal(str(fill.quantity)) for fill in fills),
                Decimal("0"),
            )

            if executed_qty <= 0:
                findings.append(
                    self._finding(
                        "NON_POSITIVE_EXECUTED_QUANTITY",
                        "ERROR",
                        "Aggregate executed quantity must be greater than zero.",
                        executed_quantity=float(executed_qty),
                    )
                )

            if executed_qty > ordered_qty:
                findings.append(
                    self._finding(
                        "OVERFILLED_ORDER",
                        "ERROR",
                        "Aggregate fill quantity exceeds the order quantity.",
                        ordered_quantity=float(ordered_qty),
                        executed_quantity=float(executed_qty),
                    )
                )

            submitted_at = pd.Timestamp(order.submitted_at)

            if submitted_at.tzinfo is None:
                submitted_at = submitted_at.tz_localize("UTC")

            else:
                submitted_at = submitted_at.tz_convert("UTC")

            completed_at = (
                pd.Timestamp(order.completed_at)
                if order.completed_at is not None
                else None
            )

            if completed_at is not None:
                if completed_at.tzinfo is None:
                    completed_at = completed_at.tz_localize("UTC")

                else:
                    completed_at = completed_at.tz_convert("UTC")

            for fill in fills:
                fill_at = pd.Timestamp(fill.executed_at)

                if fill_at.tzinfo is None:
                    fill_at = fill_at.tz_localize("UTC")

                else:
                    fill_at = fill_at.tz_convert("UTC")

                if fill_at < submitted_at:
                    findings.append(
                        self._finding(
                            "FILL_BEFORE_SUBMISSION",
                            "ERROR",
                            "A fill timestamp is earlier than the order submission timestamp.",
                            fill_id=str(fill.id),
                            executed_at=fill_at.isoformat(),
                            submitted_at=submitted_at.isoformat(),
                        )
                    )

                if completed_at is not None and fill_at > completed_at:
                    findings.append(
                        self._finding(
                            "FILL_AFTER_COMPLETION",
                            "WARNING",
                            "A fill timestamp is later than the recorded order completion timestamp.",
                            fill_id=str(fill.id),
                            executed_at=fill_at.isoformat(),
                            completed_at=completed_at.isoformat(),
                        )
                    )


        if market_data is None or market_data.empty:
            findings.append(
                self._finding(
                    "EMPTY_MARKET_DATA",
                    "ERROR",
                    "The selected market-data dataset is empty.",
                )
            )

        else:

            #These calls use the same validation/column resolution as TCA

            try:
                self.benchmark_engine.calculate_arrival_price(
                    organization_id=organization_id,
                    project_id=project_id,
                    order_id=order_id,
                    market_data=market_data,
                )

            except HTTPException as exc:
                findings.append(
                    self._finding(
                        "ARRIVAL_PRICE_UNAVAILABLE",
                        "ERROR",
                        str(exc.detail),
                    )
                )

            if fills:
                start_at = pd.Timestamp(order.submitted_at)
                end_at = pd.Timestamp(max(fill.executed_at for fill in fills))

                try:
                    vwap_result = self.benchmark_engine.calculate_market_vwap(
                        order_symbol=order.symbol,
                        market_data=market_data,
                        start_timestamp=start_at,
                        end_timestamp=end_at,
                    )

                    if vwap_result.get("vwap") is None:
                        findings.append(
                            self._finding(
                                "MARKET_VWAP_UNAVAILABLE",
                                "WARNING",
                                vwap_result.get(
                                    "unavailable_reason",
                                    "Market VWAP could not be calculated.",
                                ),
                            )
                        )

                except HTTPException as exc:
                    findings.append(
                        self._finding(
                            "MARKET_VWAP_UNAVAILABLE",
                            "WARNING",
                            str(exc.detail),
                        )
                    )

                try:
                    twap_result = self.benchmark_engine.calculate_market_twap(
                        order_symbol=order.symbol,
                        market_data=market_data,
                        start_timestamp=start_at,
                        end_timestamp=end_at,
                    )

                    if twap_result.get("twap") is None:
                        findings.append(
                            self._finding(
                                "MARKET_TWAP_UNAVAILABLE",
                                "WARNING",
                                twap_result.get(
                                    "unavailable_reason",
                                    "Market TWAP could not be calculated.",
                                ),
                            )
                        )

                except HTTPException as exc:
                    findings.append(
                        self._finding(
                            "MARKET_TWAP_UNAVAILABLE",
                            "WARNING",
                            str(exc.detail),
                        )
                    )

        if any(f.severity == "ERROR" for f in findings):
            result_status = "BLOCKED"

        elif findings:
            result_status = "READY_WITH_WARNINGS"

        else:
            result_status = "READY"

        return TCAPreflightOrderResult(
            order_id=order_id,
            status=result_status,
            findings=findings,
        )