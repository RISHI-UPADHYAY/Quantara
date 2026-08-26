from typing import Any

class ResearchReadinessEngine:

    def evaluate(
        self,
        profile: dict[str, Any],
        quality_report: dict[str, Any],
    ) -> dict[str, Any]:

        financial = profile.get("financial", {})
        structure = profile.get("structure", {})

        score = quality_report.get("quality_score", 0)

        limitations: list[dict[str, Any]] = []
        suitable_for: list[str] = []
        requires_review_for: list[str] = []
        not_suitable_for: list[str] = []

        self._evaluate_temporal_integrity(
            financial=financial,
            limitations=limitations,
            requires_review_for=requires_review_for,
            not_suitable_for=not_suitable_for,
        )

        self._evaluate_structure(
            structure=structure,
            limitations=limitations,
        )

        self._evaluate_quality(
            quality_report=quality_report,
            limitations=limitations,
        )

        self._classify_research_suitability(
            score=score,
            limitations=limitations,
            suitable_for=suitable_for,
            requires_review_for=requires_review_for,
            not_suitable_for=not_suitable_for,
        )

        overall_status = self._determine_status(
            score=score,
            limitations=limitations,
        )

        return {
            "overall_status": overall_status,
            "score": score,
            "suitable_for": suitable_for,
            "requires_review_for": requires_review_for,
            "not_suitable_for": not_suitable_for,
            "limitations": limitations,
        }


    def _evaluate_temporal_integrity(
            self,
            financial: dict[str, Any],
            limitations: list[dict[str, Any]],
            requires_review_for: list[str],
            not_suitable_for: list[str],
    ) -> None:

        timestamps = financial.get("timestamps")

        if not timestamps:
            limitations.append({
                "code": "NO_TIMESTAMP",
                "severity": "high",
                "impact": "temporal_analysis",
                "message": (
                    "No timestamp information was detected."
                ),
            })

            not_suitable_for.append(
                "time_series_research"
            )

            return

        if timestamps.get("invalid_timstamps_rows", 0) > 0:
            limitations.append({
                "code": "INVALID_TIMESTAMPS",
                "severity": "high",
                "impact": "temporal_integrity",
                "message": (
                    "Invalid timestamp values are detected."
                ),
            })

            not_suitable_for.append(
                "intraday_research"
            )

        if timestamps.get("duplicate_timestamps", 0) > 0:
            limitations.append({
                "code": "DUPLICATE_TIMESTAMPS",
                "severity": "medium",
                "impact": "temporal_integrity",
                "message": (
                    "Duplicate timestamps were detected."
                ),
            })

            requires_review_for.append(
                "intraday_research"
            )

        if timestamps.get("out_of_order_rows", 0) > 0:
            limitations.append({
                "code": "OUT_OF_ORDER_TIMESTAMPS",
                "severity": "high",
                "impact": "temporal_integrity",
                "message": (
                    "Out-of-order timestamp records were detected."
                ),
            })

            requires_review_for.append(
                "time_series_research"
            )

        frequency = financial.get("frequency")

        if frequency:
            gap_count = frequency.get("gap_count", 0)

            if gap_count > 0:
                limitations.append({
                    "code": "FREQUENCY_GAP",
                    "severity": "medium",
                    "impact": "temporal_continuity",
                    "message": (
                        f"{gap_count} frequency gap(s) were detected."
                    )
                })

                requires_review_for.append(
                    "intraday_research"
                )

                not_suitable_for.append(
                    "high_frequency_research"
                )


    def _evaluate_structure(
            self,
            structure: dict[str, Any],
            limitations: list[dict[str, Any]],
    ) -> None:

        if structure.get("missing_cells", 0) > 0:
            limitations.append({
                "code": "MISSING_DATA",
                "severity": "medium",
                "impact": "dataset_completeness",
                "message": (
                    "Missing cells were detected."
                ),
            })

        if structure.get("duplicate_rows", 0) > 0:
            limitations.append({
                "code": "DUPLICATE_ROWS",
                "severity": "medium",
                "impact": "dataset_integrity",
                "message": (
                    "Duplicate rows were detected."
                ),
            })


    def _evaluate_quality(
            self,
            quality_report: dict[str, Any],
            limitations: list[dict[str, Any]],
    ) -> None:

        for check in quality_report.get("checks", []):
            if check.get("status") == "fail":
                limitations.append({
                    "code": check.get("name"),
                    "severity": "high",
                    "impact": "data_quality",
                    "message": check.get("message"),
                })


    def _classify_research_suitability(
            self,
            score: float,
            limitations: list[dict[str, Any]],
            suitable_for: list[str],
            requires_review_for: list[str],
            not_suitable_for: list[str],
    ) -> None:

        if score >= 90:
            suitable_for.extend([
                "exploratory_research",
                "statistical_analysis",
            ])

        elif score >= 75:
            suitable_for.append(
                "exploratory_research"
            )

        else:
            requires_review_for.append(
                "exploratory_research"
            )


    @staticmethod
    def _determine_status(
        score: float,
        limitations: list[dict[str, Any]],
    ) -> str:

        high_severity = any(
            item.get("severity") == "high"
            for item in limitations
        )

        if high_severity:
            return "restricted"

        if limitations:
            return "conditional"

        if score >= 90:
            return "ready"

        if score >= 75:
            return "conditional"

        return "restricted"