from typing import Any

class DataQualityReportBuilder:

    def build(self, profile: dict[str, Any]) -> dict[str, Any]:

        checks: list[dict[str, Any]] = []

        checks.append(
            self._ohlc_check(profile)
        )

        checks.append(
            self._volume_check(profile)
        )

        checks.append(
            self._timestamp_check(profile)
        )

        checks.append(
            self._frequency_check(profile)
        )

        score = self._calculate_score(checks)

        return {
            "quality_score": score,
            "status": self._status_from_score(score),
            "research_ready": score >= 95,
            "checks": checks,
        }

    def _ohlc_check(self, profile: dict[str, Any]) -> dict[str, Any]:
        ohlc = profile.get("ohlc")

        if ohlc is None:
            return {
                "name": "ohlc_integrity",
                "status": "not_applicable",
                "severity": "info",
                "score": None,
                "message": "OHLC columns were not detected.",
            }

        invalid_rows = ohlc["invalid_ohlc_rows"]
        negative_rows = ohlc["negative_price_rows"]
        zero_rows = ohlc["zero_price_rows"]

        issue_count = (
            invalid_rows
            + negative_rows
            + zero_rows
        )

        if issue_count == 0:
            return {
                "name": "ohlc_integrity",
                "status": "pass",
                "severity": "info",
                "score": 100,
                "message": "OHLC relationships are valid.",
            }

        return {
            "name": "ohlc_integrity",
            "status": "fail",
            "severity": "critical",
            "score": 0,
            "message": (
                f"{issue_count} OHLC integrity issues detected."
            ),
        }

    def _volume_check(self, profile: dict[str, Any]) -> dict[str, Any]:
        volume = profile.get("volume")

        if volume is None:
            return {
                "name": "volume_integrity",
                "status": "not_applicable",
                "severity": "info",
                "score": None,
                "message": "Volume  column was not detected.",
            }

        negative_rows = volume["negative_volume_rows"]

        if negative_rows == 0:
            return {
                "name": "volume_integrity",
                "status": "pass",
                "severity": "info",
                "score": 100,
                "message": "No negative volume values detected.",
            }

        return {
            "name": "volume_integrity",
            "status": "fail",
            "severity": "high",
            "score": 0,
            "message": (
                f"{negative_rows} neagtive volume values detected.",
            )
        }

    def _timestamp_check(self, profile: dict[str, Any]) -> dict[str, Any]:

        timestamps = profile.get("timestamps")

        if timestamps is None:
            return {
                "name": "timestamp_integrity",
                "status": "not_applicable",
                "severity": "info",
                "score": None,
                "message": "Timestamp column was not detected.",
            }

        issues = (
            timestamps["invalid_timestamp_rows"]
            + timestamps["duplicate_timestamps"]
            + timestamps["out_of_order_rows"]
        )

        if issues == 0:
            return {
                "name": "timestamp_integrity",
                "status": "pass",
                "severity": "info",
                "score": 100,
                "message": "Timestamp sequence is valid.",
            }

        return {
            "name": "timestamp_integrity",
            "status": "fail",
            "severity": "critical",
            "score": 0,
            "message": (
                f"{issues} timestamp integrity issues detected.",
            )
        }

    def _frequency_check(self, profile: dict[str, Any]) -> dict[str, Any]:

        frequency = profile.get("frequency")

        if not frequency:
            return {
                "name": "frequency_consistency",
                "status": "not_applicable",
                "severity": "info",
                "score": None,
                "message": "Frequency could not be determined.",
            }

        gap_count = frequency.get("gap_count", 0)

        if gap_count == 0:
            return {
                "name": "frequency_consistency",
                "status": "pass",
                "severity": "info",
                "score": 100,
                "message": "No frequency gaps detected.",
            }

        if gap_count <= 2:
            return {
                "name": "frequency_consistency",
                "status": "warning",
                "severity": "warning",
                "score": 80,
                "message": f"{gap_count} frequency gap(s) detected.",
            }

        return {
            "name": "frequency_consistency",
            "status": "fail",
            "severity": "error",
            "score": 50,
            "message": (
                f"{gap_count} frequency gaps detected."
            ),
        }

    @staticmethod
    def _calculate_score(checks: list[dict[str, Any]]) -> float:

        applicable_checks = [
            check
            for check in checks
            if check.get("score") is not None
        ]

        if not applicable_checks:
            return 0.0

        total = sum(
            check["score"]
            for check in checks
        )

        return round(
            total / len(applicable_checks),
            2,
        )

    @staticmethod
    def _status_from_score(score: float) -> str:

        if score >= 95:
            return "excellent"

        if score >= 85:
            return "good"

        if score >= 70:
            return "warning"

        return "poor"