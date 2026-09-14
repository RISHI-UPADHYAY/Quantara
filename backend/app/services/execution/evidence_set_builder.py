
from typing import Any


class EvidenceSetBuilder:
    """Groups diagnosis findings into a structured execution evidence set."""

    COST_ISSUE_CODES = {
        "HIGH_SLIPPAGE",
        "POOR_VWAP_PERFORMANCE",
        "HIGH_IMPLEMENTATION_SHORTFALL",
        "HIGH_TRANSACTION_COSTS",
    }

    EXECUTION_CONDITION_CODES = {
        "HIGH_MARKET_IMPACT",
    }

    POSITIVE_FINDING_CODES = {
        "GOOD_EXECUTION",
    }

    def build(
        self,
        execution_diagnoses: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(execution_diagnoses, dict):
            return self._empty_evidence_set()

        grouped: dict[str, list[dict[str, Any]]] = {
            "cost_issues": [],
            "execution_conditions": [],
            "positive_findings": [],
        }

        diagnoses = execution_diagnoses.get("diagnoses", [])
        if not isinstance(diagnoses, list):
            diagnoses = []

        for diagnosis in diagnoses:
            if not isinstance(diagnosis, dict):
                continue

            code = diagnosis.get("code")
            if not isinstance(code, str):
                continue

            category = self._category_for(code)
            if category is None:
                continue

            finding = {
                "code": code,
                "category": category,
                "severity": diagnosis.get("severity", "INFO"),
                "message": diagnosis.get("message", ""),
                "evidence": diagnosis.get("evidence", {}),
            }

            if category == "COST_ISSUE":
                grouped["cost_issues"].append(finding)
            elif category == "EXECUTION_CONDITION":
                grouped["execution_conditions"].append(finding)
            else:
                grouped["positive_findings"].append(finding)

        return {
            "overall_status": execution_diagnoses.get(
                "overall_status",
                "UNKNOWN",
            ),
            **grouped,
        }

    def _category_for(self, code: str) -> str | None:
        if code in self.COST_ISSUE_CODES:
            return "COST_ISSUE"

        if code in self.EXECUTION_CONDITION_CODES:
            return "EXECUTION_CONDITION"

        if code in self.POSITIVE_FINDING_CODES:
            return "POSITIVE_FINDING"

        return None

    @staticmethod
    def _empty_evidence_set() -> dict[str, Any]:
        return {
            "overall_status": "UNKNOWN",
            "cost_issues": [],
            "execution_conditions": [],
            "positive_findings": [],
        }