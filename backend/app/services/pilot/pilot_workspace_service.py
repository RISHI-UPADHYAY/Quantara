from __future__ import annotations

import uuid
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import (
    DatasetVersionRepository,
)
from app.repositories.execution_fill_repository import (
    ExecutionFillRepository,
)
from app.repositories.execution_order_repository import (
    ExecutionOrderRepository,
)
from app.repositories.execution_review_issue_repository import (
    ExecutionReviewIssueRepository,
)
from app.schemas.pilot_workspace import (
    PilotWorkspaceBreakdownItem,
    PilotWorkspaceDatasetContext,
    PilotWorkspaceExceptionSummary,
    PilotWorkspaceExecutionSummary,
    PilotWorkspaceOverviewResponse,
    PilotWorkspacePeriod,
    PilotWorkspaceQualitySummary,
    PilotWorkspaceRecentReview,
)
from app.services.execution.execution_analytics_service import (
    ExecutionAnalyticsService,
)
from app.services.execution.market_data_loader import (
    ExecutionMarketDataLoader,
)


class PilotWorkspaceService:
    """
    Aggregation/orchestration service for the Quantara pilot workspace.

    The workspace does not implement its own TCA logic.

    It consumes:
        - execution orders
        - execution fills
        - market-data datasets
        - execution analytics
        - persisted execution review issues

    Existing execution services remain responsible for detailed TCA
    and execution-quality calculations.
    """

    def __init__(
        self,
        *,
        db: Session,
    ):
        self.db = db

        self.dataset_repository = DatasetRepository(db)
        self.dataset_version_repository = DatasetVersionRepository(db)

        self.order_repository = ExecutionOrderRepository(db)
        self.fill_repository = ExecutionFillRepository(db)

        self.review_repository = ExecutionReviewIssueRepository(db)

        self.market_data_loader = ExecutionMarketDataLoader(
            storage_root=Path(__file__).resolve().parents[3] / "storage"
        )

        self.analytics_service = ExecutionAnalyticsService(
            order_repository=self.order_repository,
            fill_repository=self.fill_repository,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_overview(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> PilotWorkspaceOverviewResponse:

        orders = self.order_repository.list_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        orders = self._filter_orders_by_period(
            orders=orders,
            start_time=start_time,
            end_time=end_time,
        )

        market_data_context = self._get_market_data_context(
            organization_id=organization_id,
            project_id=project_id,
        )

        analytics = None

        if market_data_context["storage_uri"] is not None:
            market_data = self.market_data_loader.load(
                market_data_context["storage_uri"]
            )

            analytics = self.analytics_service.analyze(
                organization_id=organization_id,
                project_id=project_id,
                market_data=market_data,
                start_time=start_time,
                end_time=end_time,
                limit=max(len(orders), 100),
            )

        execution = self._build_execution_summary(
            orders=orders,
            analytics=analytics,
        )

        quality = self._build_quality_summary(
            analytics=analytics,
        )

        exceptions = self._build_exception_summary(
            organization_id=organization_id,
            project_id=project_id,
        )

        top_symbols = self._build_breakdown(
            orders=orders,
            dimension="symbol",
            organization_id=organization_id,
            project_id=project_id,
            market_data=market_data,
            start_time=start_time,
            end_time=end_time,
        )[:10]

        top_venues = self._build_breakdown(
            orders=orders,
            dimension="venue",
            organization_id=organization_id,
            project_id=project_id,
            market_data=market_data,
            start_time=start_time,
            end_time=end_time,
        )[:10]

        recent_reviews = self._build_recent_reviews(
            organization_id=organization_id,
            project_id=project_id,
        )

        period_start = (
            start_time
            if start_time is not None
            else self._earliest_order_time(orders)
        )

        period_end = (
            end_time
            if end_time is not None
            else self._latest_order_time(orders)
        )

        return PilotWorkspaceOverviewResponse(
            organization_id=organization_id,
            project_id=project_id,
            period=PilotWorkspacePeriod(
                start=period_start,
                end=period_end,
            ),
            execution=execution,
            quality=quality,
            exceptions=exceptions,
            top_symbols=top_symbols,
            top_venues=top_venues,
            recent_reviews=recent_reviews,
            market_data=PilotWorkspaceDatasetContext(
                dataset_id=market_data_context["dataset_id"],
                dataset_version_id=market_data_context[
                    "dataset_version_id"
                ],
                version=market_data_context["version"],
            ),
        )

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def _get_market_data_context(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> dict[str, Any]:

        datasets = self.dataset_repository.get_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        market_datasets = [
            dataset
            for dataset in datasets
            if dataset.dataset_type == "market_data"
        ]

        if not market_datasets:
            return {
                "dataset_id": None,
                "dataset_version_id": None,
                "version": None,
                "storage_uri": None,
            }

        market_dataset = market_datasets[0]

        market_dataset_version = (
            self.dataset_version_repository.get_latest_version(
                market_dataset.id
            )
        )

        if market_dataset_version is None:
            return {
                "dataset_id": market_dataset.id,
                "dataset_version_id": None,
                "version": None,
                "storage_uri": None,
            }

        storage_uri = (
            market_dataset_version.storage_uri
            or market_dataset.storage_uri
        )

        return {
            "dataset_id": market_dataset.id,
            "dataset_version_id": market_dataset_version.id,
            "version": market_dataset_version.version,
            "storage_uri": storage_uri,
        }

    # ------------------------------------------------------------------
    # Execution summary
    # ------------------------------------------------------------------

    def _build_execution_summary(
        self,
        *,
        orders: list[Any],
        analytics: dict[str, Any] | None,
    ) -> PilotWorkspaceExecutionSummary:

        filled_orders = 0
        partially_filled_orders = 0
        unfilled_orders = 0

        ordered_quantity = 0.0
        executed_quantity = 0.0
        total_notional = 0.0

        for order in orders:

            ordered = self._to_float(
                getattr(order, "quantity", None)
            )

            ordered_quantity += ordered

            fills = getattr(order, "fills", None) or []

            executed = sum(
                self._to_float(
                    getattr(fill, "quantity", None)
                )
                for fill in fills
            )

            executed_quantity += executed

            total_notional += sum(
                self._to_float(
                    getattr(fill, "price", None)
                )
                * self._to_float(
                    getattr(fill, "quantity", None)
                )
                for fill in fills
            )

            order_status = (
                str(getattr(order, "status", "") or "")
                .strip()
                .lower()
            )

            if order_status == "filled":
                filled_orders += 1

            elif order_status == "partially_filled":
                partially_filled_orders += 1

            elif order_status in {
                "pending",
                "open",
                "cancelled",
                "rejected",
            }:
                unfilled_orders += 1

            elif ordered > 0:
                # Fallback for legacy/imported records whose status
                # does not match the canonical execution statuses.

                if executed >= ordered:
                    filled_orders += 1

                elif executed > 0:
                    partially_filled_orders += 1

                else: 
                    unfilled_orders += 1

        fill_rate = (
            (executed_quantity / ordered_quantity) * 100
            if ordered_quantity > 0
            else 0.0
        )

        analyzed_orders = 0
        failed_orders = 0
        tca_requested_orders = 0
        tca_coverage_percentage = 0.0

        weighted_slippage_percentage = None
        weighted_shortfall_percentage = None
        weighted_vwap_deviation_percentage = None

        if analytics is not None:
            summary = analytics.get("summary", {})

            analyzed_orders = int(
                summary.get("analyzed", 0) or 0
            )

            failed_orders = int(
                summary.get("failed", 0) or 0
            )

            tca_requested_orders = analyzed_orders + failed_orders

            tca_coverage_percentage = (
                (analyzed_orders / tca_requested_orders) * 100
                if tca_requested_orders > 0
                else 0.0
            )

            weighted_slippage_percentage = self._to_optional_float(
                summary.get("weighted_slippage_percentage")
            )

            weighted_shortfall_percentage = self._to_optional_float(
                summary.get("weighted_shortfall_percentage")
            )

            weighted_vwap_deviation_percentage = self._to_optional_float(
                summary.get("weighted_vwap_deviation_percentage")
            )

        return PilotWorkspaceExecutionSummary(
            orders=len(orders),
            filled_orders=filled_orders,
            partially_filled_orders=partially_filled_orders,
            unfilled_orders=unfilled_orders,
            fill_rate=fill_rate,
            ordered_quantity=ordered_quantity,
            executed_quantity=executed_quantity,
            total_notional=total_notional,
            average_slippage_percentage=None,
            weighted_slippage_percentage=weighted_slippage_percentage,
            average_shortfall_percentage=None,
            weighted_shortfall_percentage=weighted_shortfall_percentage,
            average_vwap_deviation_percentage=None,
            weighted_vwap_deviation_percentage=weighted_vwap_deviation_percentage,
            analyzed_orders=analyzed_orders,
            failed_orders=failed_orders,
            tca_requested_orders=tca_requested_orders,
            tca_coverage_percentage=tca_coverage_percentage,
        )

    # ------------------------------------------------------------------
    # Quality summary
    # ------------------------------------------------------------------

    def _build_quality_summary(
        self,
        *,
        analytics: dict[str, Any] | None,
    ) -> PilotWorkspaceQualitySummary:

        if analytics is None:
            return PilotWorkspaceQualitySummary()

        summary = analytics.get("summary", {})

        analyzed_orders = int(
            summary.get("analyzed", 0) or 0
        )

        coverage_percentage = (
            (
                analyzed_orders / (
                    analyzed_orders + int(summary.get("failed", 0) or 0)
                )
            ) * 100
            if (analyzed_orders + int(summary.get("failed", 0) or 0)) > 0
            else 0.0
        )

        average_quality_score = self._to_optional_float(
            summary.get("average_execution_quality_score")
        )

        if average_quality_score is None:
            return PilotWorkspaceQualitySummary(
                analyzed_orders=analyzed_orders,
                coverage_percentage=coverage_percentage,
                unknown=analyzed_orders,
            )

        if average_quality_score >= 90:
            excellent = analyzed_orders
            good = fair = poor = unknown = 0

        elif average_quality_score >= 75:
            excellent = fair = poor = unknown = 0
            good = analyzed_orders

        elif average_quality_score >= 60:
            excellent = good = fair = unknown = 0
            poor = analyzed_orders

        return PilotWorkspaceQualitySummary(
            analyzed_orders=analyzed_orders,
            coverage_percentage=coverage_percentage,
            excellent=excellent,
            good=good,
            fair=fair,
            poor=poor,
            unknown=unknown,
        )

    # ------------------------------------------------------------------
    # Exception summary
    # ------------------------------------------------------------------

    def _build_exception_summary(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> PilotWorkspaceExceptionSummary:

        summary = PilotWorkspaceExceptionSummary()

        total = self.review_repository.count_for_project(
            organization_id=organization_id,
            project_id=project_id,
        )

        summary.total = total

        statuses = (
            "OPEN",
            "ACKNOWLEDGED",
            "IN_REVIEW",
            "RESOLVED",
            "IGNORED",
        )

        for status in statuses:

            count = self.review_repository.count_for_project(
                organization_id=organization_id,
                project_id=project_id,
                status=status,
            )

            if status == "OPEN":
                summary.open = count

            elif status == "ACKNOWLEDGED":
                summary.acknowledged = count

            elif status == "IN_REVIEW":
                summary.in_review = count

            elif status == "RESOLVED":
                summary.resolved = count

            elif status == "IGNORED":
                summary.ignored = count

        severities = (
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        )

        for severity in severities:

            count = self.review_repository.count_for_project(
                organization_id=organization_id,
                project_id=project_id,
                severity=severity,
            )

            if severity == "MEDIUM":
                summary.medium = count

            elif severity == "HIGH":
                summary.high = count

            elif severity == "CRITICAL":
                summary.critical = count

        return summary

    # ------------------------------------------------------------------
    # Symbol / venue breakdown
    # ------------------------------------------------------------------

    def _build_breakdown(
        self,
        *,
        orders: list[Any],
        dimension: str,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        market_data: Any | None,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[PilotWorkspaceBreakdownItem]:

        grouped: dict[str, list[Any]] = defaultdict(list)

        for order in orders:

            if dimension == "symbol":
                name = getattr(order, "symbol", None) or "UNKNOWN"

            elif dimension == "venue":
                name = getattr(order, "venue", None) or "UNKNOWN"

            else:
                name = "UNKNOWN"

            grouped[str(name)].append(order)

        breakdowns: list[PilotWorkspaceBreakdownItem] = []

        for name, group_orders in grouped.items():

            ordered_quantity = 0.0
            executed_quantity = 0.0
            total_notional = 0.0

            for order in group_orders:

                ordered_quantity += self._to_float(
                    getattr(order, "quantity", None)
                )

                fills = getattr(order, "fills", None) or []

                executed_quantity += sum(
                    self._to_float(
                        getattr(fill, "quantity", None)
                    )
                    for fill in fills
                )

                total_notional += sum(
                    self._to_float(
                        getattr(fill, "price", None)
                    )
                    * self._to_float(
                        getattr(fill, "quantity", None)
                    )
                    for fill in fills
                )

            fill_rate = (
                (executed_quantity / ordered_quantity) * 100
                if ordered_quantity > 0
                else 0.0
            )

            analyzed_orders = 0
            weighted_slippage_percentage = None
            weighted_shortfall_percentage = None
            weighted_vwap_deviation_percentage = None

            if market_data is not None and group_orders:
                analytics = self.analytics_service.analyze(
                    organization_id=organization_id,
                    project_id=project_id,
                    market_data=market_data,
                    symbol=name if dimension == "symbol" else None,
                    venue=name if dimension == "venue" else None,
                    start_time=start_time,
                    end_time=end_time,
                    limit=max(len(group_orders), 100),
                )

                summary = analytics.get("summary", {})

                analyzed_orders = int(
                    summary.get("analyzed", 0) or 0
                )

                weighted_slippage_percentage = (
                    self._to_optional_float(
                        summary.get(
                            "weighted_slippage_percentage"
                        )
                    )
                )

                weighted_shortfall_percentage = (
                    self._to_optional_float(
                        summary.get(
                            "weighted_shortfall_percentage"
                        )
                    )
                ) 

                weighted_vwap_deviation_percentage = (
                    self._to_optional_float(
                        summary.get(
                            "weighted_vwap_deviation_percentage"
                        )
                    )
                )

            breakdowns.append(
                PilotWorkspaceBreakdownItem(
                    name=name,
                    orders=len(group_orders),
                    analyzed_orders=analyzed_orders,
                    total_notional=total_notional,
                    fill_rate=fill_rate,
                    weighted_slippage_percentage=weighted_slippage_percentage,
                    weighted_shortfall_percentage=weighted_shortfall_percentage,
                    weighted_vwap_deviation_percentage=weighted_vwap_deviation_percentage,
                )
            )

        breakdowns.sort(
            key=lambda item: item.total_notional,
            reverse=True,
        )

        return breakdowns




    # ------------------------------------------------------------------
    # Recent reviews
    # ------------------------------------------------------------------

    def _build_recent_reviews(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[PilotWorkspaceRecentReview]:

        issues = self.review_repository.list_for_project(
            organization_id=organization_id,
            project_id=project_id,
            limit=10,
            offset=0,
        )

        return [
            PilotWorkspaceRecentReview(
                id=issue.id,
                order_id=issue.order_id,
                issue_code=issue.issue_code,
                severity=issue.severity,
                status=issue.status,
                metric=issue.metric,
                observed_value=(
                    self._to_float(
                        issue.observed_value
                    )
                    if issue.observed_value is not None
                    else None
                ),
                threshold_value=(
                    self._to_float(
                        issue.threshold
                    )
                    if issue.threshold is not None
                    else None
                ),
                message=issue.message,
                assigned_to=issue.assigned_to,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
            )
            for issue in issues
        ]

    # ------------------------------------------------------------------
    # Period filtering
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_orders_by_period(
        *,
        orders: list[Any],
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> list[Any]:

        if start_time is None and end_time is None:
            return orders

        filtered = []

        for order in orders:

            submitted_at = getattr(
                order,
                "submitted_at",
                None,
            )

            if submitted_at is None:
                continue

            if (
                start_time is not None
                and submitted_at < start_time
            ):
                continue

            if (
                end_time is not None
                and submitted_at > end_time
            ):
                continue

            filtered.append(order)

        return filtered

    # ------------------------------------------------------------------
    # Time helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _earliest_order_time(
        orders: list[Any],
    ) -> datetime | None:

        timestamps = [
            order.submitted_at
            for order in orders
            if getattr(order, "submitted_at", None)
            is not None
        ]

        if not timestamps:
            return None

        return min(timestamps)

    @staticmethod
    def _latest_order_time(
        orders: list[Any],
    ) -> datetime | None:

        timestamps = [
            order.submitted_at
            for order in orders
            if getattr(order, "submitted_at", None)
            is not None
        ]

        if not timestamps:
            return None

        return max(timestamps)

    # ------------------------------------------------------------------
    # Numeric helper
    # ------------------------------------------------------------------

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float:

        if value is None:
            return 0.0

        try:
            return float(value)

        except (TypeError, ValueError):
            return 0.0


    @staticmethod

    def _to_optional_float(
        value: Any,
    ) -> float | None:
        
        if value is None:
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None