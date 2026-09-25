from __future__ import annotations


class ExecutionRecommendationEngine:
    """
    Deterministic, rules-based recommendation derived from TCA diagnoses.

    Recommendations are analyst investigation steps-not automatic trading
    instructions. A diagnoses is a signal to investigate, not proof of cause.
    """

    _RULES: dict[str, dict] = {
        "HIGH_SLIPPAGE": {
            "title": "Investigate elevated slippage",
            "rationale": (
                "Execution cost relative to the arrival price  exceeded "
                "the configured slippage threshold."
            ),
            "suggested_actions": [
                "Review fill-level prices and timestamps against the arrival price.",
                "Compare slippage across similar orders, symbols, and time windows.",
                "Check whether execution timing or market conditions explain the deviation.",
            ],
        },
        "POOR_VWAP_PERFORMANCE": {
            "title": "Review performance against market VWAP",
            "rationale": (
                "The execution price was materially worse than market VWAP "
                "over the measured execution window."
            ),
            "suggested_actions": [
                "Review fill timing relative to the market VWAP path.",
                "Compare VWAP performance across similar orders and execution windows.",
                "Check that the benchmark window and market data are appropriate.",
            ],
        },
        "HIGH_IMPLEMENTATION_SHORTFALL": {
            "title": "Break down implementation shortfall",
            "rationale": (
                "Implementation shortfall exceeded the configured threshold."
            ),
            "suggested_actions": [
                "Separate price shortfall from commission and fees.",
                "Review fill timing and price deviations from the arrival benchmark.",
                "Compare shortfall across similar orders and execution conditions.",
            ],
        },
        "HIGH_MARKET_IMPACT": {
            "title": "Investigate adverse market movement.",
            "rationale": (
                "The market moved adversely during the execution window. "
                "This does not establish that the order caused the movement."
            ),
            "suggested_actions": [
                "Review the market-price path during the execution window.",
                "Compare the movement with market-wide or sector conditions.",
                "Compare similar orders before drawing conclusions about order impact.",
            ],
        },
        "HIGH_TRANSACTION_COSTS": {
            "title": "Review explicit transaction costs",
            "rationale": (
                "Commissions and fees exceeded the configured transaction-cost threshold."
            ),
            "suggested_actions": [
                "Verify commissions and fees recorded for each fill.",
                "Compare venue-level costs and applicable fee schedules.",
                "Review whether the cost assumptions match the executed order.",
            ],
        },
    }


    
    def generate_recommendations(
        self,
        *,
        execution_evidence_set: dict,
    ) -> list[dict]:
        """Generate recommendations from categorized evidence findings."""
        if not isinstance(execution_evidence_set, dict):
            return []

        categories = (
            "cost_issues",
            "execution_conditions",
            "positive_findings",
        )

        recommendations: list[dict] = []

        for category in categories:
            findings = execution_evidence_set.get(category, [])

            if not isinstance(findings, list):
                continue

            for finding in findings:
                if not isinstance(finding, dict):
                    continue

                diagnosis_code = finding.get("code")
                if not isinstance(diagnosis_code, str):
                    continue

                if diagnosis_code == "GOOD_EXECUTION":
                    continue

                rule = self._RULES.get(diagnosis_code)
                if rule is None:
                    continue

                severity = finding.get("severity", "INFO")

                recommendations.append(
                    {
                        "diagnosis_code": diagnosis_code,
                        "severity": severity,
                        "priority": self._priority_for_severity(severity),
                        "title": rule["title"],
                        "rationale": rule["rationale"],
                        "suggested_actions": list(
                            rule["suggested_actions"]
                        ),
                    }
                )

        return recommendations


    @staticmethod
    def _priority_for_severity(
        severity: str,
    ) -> str:
        if severity == "CRITICAL":
            return "URGENT"

        if severity == "HIGH":
            return "HIGH"

        if severity == "MEDIUM":
            return "NORMAL"

        return "LOW"