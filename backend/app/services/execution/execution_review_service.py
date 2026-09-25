from __future__ import annotations

from app.schemas.tca import (
    ExecutionReviewIssue,
    ExecutionReviewItem,
    ExecutionReviewSummary,
    ExecutionReviewResponse,
    TCABatchResponse,
)


class ExecutionReviewService:
    """
    Converts TCA batch into an actionable execution-review queue.

    TCA remains the source of truth for execution measurements.
    This service only identifies executions requiring human attention.
    """

    SEVERITY_ORDER = {
        "CRITICAL": 3,
        "HIGH": 2,
        "MEDIUM": 1,
    }

    def build_review_queue(
        self,
        batch_response: TCABatchResponse,
    ) -> ExecutionReviewResponse:

        items: list[ExecutionReviewItem] = []

        issue_counts_by_code: dict[str, int] = {}

        issues_by_severity = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
        }

        orders_by_severity = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
        }

        analyzed = 0
        failed = 0

        for batch_result in batch_response.results:

            if batch_result.result is None:
                failed += 1
                continue

            analyzed += 1

            result = batch_result.result

            issues = self._build_issues(
                result=result,
                outlier_flags=batch_result.outlier_flags,
            )

            issues = self._apply_order_severity(
                issues
            )

            if not issues:
                continue

            # --------------------------------------------------
            # Count issues
            # --------------------------------------------------

            for issue in issues:

                issue_counts_by_code[issue.code] = (
                    issue_counts_by_code.get(issue.code, 0) + 1
                )

                issues_by_severity[issue.severity] += 1

            # --------------------------------------------------
            # Determine the order's queue severity
            # --------------------------------------------------

            highest_severity = max(
                issues,
                key=lambda issue: self.SEVERITY_ORDER[
                    issue.severity
                ],
            ).severity

            orders_by_severity[highest_severity] += 1

            # --------------------------------------------------
            # Build review item
            # --------------------------------------------------

            order = result.order
            execution = result.execution
            shortfall = result.implementation_shortfall
            diagnoses = result.execution_diagnoses

            overall_status = (
                diagnoses.overall_status
                if diagnoses is not None
                else "NEEDS_ATTENTION"
            )

            items.append(
                ExecutionReviewItem(
                    order_id=order.order_id,
                    symbol=order.symbol,
                    side=order.side,
                    ordered_quantity=order.ordered_quantity,
                    executed_quantity=order.executed_quantity,
                    gross_notional=execution.gross_notional,
                    total_shortfall=shortfall.total_shortfall,
                    explicit_costs=(
                        execution.commission
                        + execution.fees
                    ),
                    overall_status=overall_status,
                    issues=issues,
                )
            )

        # ------------------------------------------------------
        # Highest-priority executions first
        # ------------------------------------------------------

        items.sort(
            key=self._item_priority,
            reverse=True,
        )

        # ------------------------------------------------------
        # Total issue count
        # ------------------------------------------------------

        total_issues = sum(
            issues_by_severity.values()
        )

        return ExecutionReviewResponse(
            summary=ExecutionReviewSummary(
                requested=batch_response.summary.requested,
                analyzed=analyzed,
                failed=failed,
                orders_requiring_attention=len(items),
                orders_by_severity=orders_by_severity,
                total_issues=total_issues,
                issues_by_severity=issues_by_severity,
                issue_counts_by_code=issue_counts_by_code,
            ),
            items=items,
        )


    def _build_issues(
        self,
        *,
        result,
        outlier_flags,
    ) -> list[ExecutionReviewIssue]:

        issues: list[ExecutionReviewIssue] = []

        diagnosis_map = {}

        if result.execution_diagnoses is not None:
            diagnosis_map = {
                diagnosis.code: diagnosis
                for diagnosis in result.execution_diagnoses.diagnoses
            }

        for flag in outlier_flags:

            diagnosis = diagnosis_map.get(flag.code)

            severity = self._resolve_issue_severity(
                flag=flag,
                diagnosis=diagnosis,
            )

            if severity is None:
                severity = "MEDIUM"

            recommendations: list[str] = []

            if result.execution_recommendations:
                recommendations = [
                    action
                    for recommendation
                    in result.execution_recommendations
                    if recommendation.diagnosis_code == flag.code
                    for action in recommendation.suggested_actions
                ]

            evidence = dict(
                diagnosis.evidence
                if diagnosis is not None
                else {}
            )

            evidence.update(
                {
                    "observed_value": flag.observed_value,
                    "threshold": flag.threshold,
                }
            )

            issues.append(
                ExecutionReviewIssue(
                    code=flag.code,
                    severity=severity,
                    metric=flag.metric,
                    observed_value=flag.observed_value,
                    threshold=flag.threshold,
                    message=(
                        diagnosis.message
                        if diagnosis is not None
                        else flag.reason
                    ),
                    evidence=evidence,
                    recommendations=recommendations,
                )
            )

        # A diagnosis can contain a material issue even if the batch outlier rules did not produce a corresponding flag
        flagged_codes = {
            issue.code
            for issue in issues
        }

        if result.execution_diagnoses is not None:

            for diagnosis in result.execution_diagnoses.diagnoses:

                if diagnosis.code in flagged_codes:
                    continue

                # WORSE_THAN_MARKET_VWAP is the canonical review issue for VWAP underperformance. POOR_VWAP_PERFORMANCE is retained as supporting TCA diagnosis evidence.
                if (
                    diagnosis.code == "POOR_VWAP_PERFORMANCE"
                    and "WORSE_THAN_MARKET_VWAP" in flagged_codes
                ): 
                    continue

                severity = self._resolve_severity(
                    diagnosis.severity
                ) 

                if severity is None:
                    continue

                recommendations = [
                    action
                    for recommendation
                    in result.execution_recommendations
                    if recommendation.diagnosis_code == diagnosis.code
                    for action in recommendation.suggested_actions
                ]

                observed_value = self._extract_observed_value(
                    diagnosis.evidence
                )

                threshold = self._extract_threshold(
                    diagnosis.evidence
                )

                if observed_value is None:
                    continue

                issues.append(
                    ExecutionReviewIssue(
                        code=diagnosis.code,
                        severity=severity,
                        metric=self._metric_for_diagnosis(
                            diagnosis.code
                        ),
                        observed_value=observed_value,
                        threshold=threshold,
                        message=diagnosis.message,
                        evidence=diagnosis.evidence,
                        recommendations=recommendations,
                    )
                )

        issues.sort(
            key=lambda issue: self.SEVERITY_ORDER[
                issue.severity
            ],
            reverse=True,
        )

        return issues


    def _item_priority(
        self,
        item: ExecutionReviewItem,
    ) -> int:

        if not item.issues:
            return 0

        return max(
            self.SEVERITY_ORDER[issue.severity]
            for issue in item.issues
        )


    def _resolve_issue_severity(
        self,
        *,
        flag,
        diagnosis,
    ) -> str:

        if diagnosis is not None:
            diagnosis_severity = self._resolve_severity(
                diagnosis.severity
            )

            if diagnosis_severity == "CRITICAL":
                return "CRITICAL"

        return "MEDIUM"


    def _apply_order_severity(
        self,
        issues: list[ExecutionReviewIssue],
    ) -> list[ExecutionReviewIssue]:

        issue_count = len(issues)

        if issue_count >= 3:
            severity = "CRITICAL"

        elif issue_count == 2:
            severity = "HIGH"

        else:
            severity = "MEDIUM"

        return [
            issue.model_copy(
                update= {
                    "severity": severity,
                }
            )
            for issue in issues
        ]


    @staticmethod
    def _resolve_severity(
        severity: str | None,
    ) -> str | None:

        if severity in {
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }:
            return severity

        return None


    @staticmethod
    def _extract_observed_value(
        evidence: dict[str, float | str],
    ) -> float | None:

        preferred_keys = (
            "slippage_percentage",
            "vwap_deviation_percentage",
            "shortfall_percentage",
            "market_impact_percentage",
            "explicit_cost_percentage",
        )

        for key in preferred_keys:

            value = evidence.get(key)

            if value is not None:
                return float(value)

        return None


    @staticmethod
    def _extract_threshold(
        evidence: dict[str, float | str],
    ) -> float | None:

        value = evidence.get("threshold")

        if value is None:
            return None

        return float(value)


    @staticmethod
    def _metric_for_diagnosis(
        code: str,
    ) -> str:

        mapping = {
            "HIGH_SLIPPAGE": "slippage_percentage",
            "POOR_VWAP_PERCENTAGE": (
                "vwap_deviation_percentage"
            ),
            "HIGH_IMPLEMENTATION_SHORTFALL": (
                "shortfall_percentage"
            ),
            "HIGH_MARKET_IMPACT": (
                "market_impact_percentage"
            ),
            "HIGH_TRANSACTION_COSTS": (
                "explicit_cost_percentage"
            ),
        }

        return mapping.get(
            code,
            "execution_metric",
        )