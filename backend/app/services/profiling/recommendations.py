from typing import Any


class DataQualityRecommendationEngine:

    def generate(
        self,
        profile: dict[str, Any],
        quality_report: dict[str, Any],
    ) -> list[dict[str, Any]]:

        recommendations: list[dict[str, Any]] = []

        recommendations.extend(
            self._recommend_from_quality_checks(
                quality_report.get("checks", [])
            )
        )

        recommendations.extend(
            self._recommend_from_financial_profile(profile)
        )

        recommendations.extend(
            self._recommend_from_structure(profile)
        )

        return self._deduplicate(recommendations)

    def _recommend_from_quality_checks(
        self,
        checks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        recommendations = []

        for check in checks:

            status = check.get("status")
            name = check.get("name")

            if status not in {
                "warning",
                "fail",
                "blocked",
            }:
                continue

            if name == "ohlc_integrity":

                recommendations.append(
                    self._recommendation(
                        category="market_data_integrity",
                        severity="high",
                        code="INVALID_OHLC",
                        title="Invalid OHLC relationships detected",
                        message=(
                            "One or more rows contain inconsistent "
                            "OHLC relationships."
                        ),
                        action=(
                            "Inspect affected rows and correct or remove "
                            "invalid observations before using the dataset "
                            "for quantitative research."
                        ),
                    )
                )

            elif name == "volume_integrity":

                recommendations.append(
                    self._recommendation(
                        category="market_data_integrity",
                        severity="medium",
                        code="INVALID_VOLUME",
                        title="Invalid volume values detected",
                        message=(
                            "Invalid volume values were detected."
                        ),
                        action=(
                            "Validate the source data and determine whether "
                            "invalid volume values should be corrected, "
                            "removed, or treated as missing."
                        ),
                    )
                )

            elif name == "timestamp_integrity":

                recommendations.append(
                    self._recommendation(
                        category="temporal_integrity",
                        severity="high",
                        code="INVALID_TIMESTAMPS",
                        title="Timestamp integrity issue detected",
                        message=(
                            "Duplicate, invalid, or out-of-order "
                            "timestamps were detected."
                        ),
                        action=(
                            "Validate timestamp ordering and uniqueness "
                            "before performing time-series analysis "
                            "or backtesting."
                        ),
                    )
                )

        return recommendations

    def _recommend_from_financial_profile(
        self,
        profile: dict[str, Any],
    ) -> list[dict[str, Any]]:

        recommendations = []

        financial = profile.get(
            "financial",
            profile,
        )

        ohlc = financial.get("ohlc") or {}

        if ohlc.get("invalid_ohlc_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="market_data_integrity",
                    severity="high",
                    code="INVALID_OHLC",
                    title="Invalid OHLC rows detected",
                    message=(
                        f"{ohlc['invalid_ohlc_rows']} row(s) "
                        "contain invalid OHLC relationships."
                    ),
                    action=(
                        "Inspect the affected rows before using "
                        "the dataset for research or backtesting."
                    ),
                )
            )

        if ohlc.get("negative_price_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="price_integrity",
                    severity="critical",
                    code="NEGATIVE_PRICES",
                    title="Negative prices detected",
                    message=(
                        f"{ohlc['negative_price_rows']} row(s) "
                        "contain negative prices."
                    ),
                    action=(
                        "Verify the instrument and source data. "
                        "Do not silently pass negative prices into "
                        "standard equity research pipelines."
                    ),
                )
            )

        if ohlc.get("zero_price_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="price_integrity",
                    severity="high",
                    code="ZERO_PRICES",
                    title="Zero prices detected",
                    message=(
                        f"{ohlc['zero_price_rows']} row(s) "
                        "contain zero prices."
                    ),
                    action=(
                        "Investigate whether zero prices represent "
                        "missing data, corporate actions, market-state "
                        "records, or source corruption."
                    ),
                )
            )

        volume = financial.get("volume") or {}

        if volume.get("negative_volume_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="volume_integrity",
                    severity="high",
                    code="NEGATIVE_VOLUME",
                    title="Negative volume detected",
                    message=(
                        f"{volume['negative_volume_rows']} row(s) "
                        "contain negative volume."
                    ),
                    action=(
                        "Validate the source data and correct or "
                        "remove invalid volume observations."
                    ),
                )
            )

        if volume.get("zero_volume_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="volume_integrity",
                    severity="low",
                    code="ZERO_VOLUME",
                    title="Zero-volume observations detected",
                    message=(
                        f"{volume['zero_volume_rows']} row(s) "
                        "contain zero volume."
                    ),
                    action=(
                        "Determine whether zero volume is valid for "
                        "the instrument and trading session."
                    ),
                )
            )

        timestamps = financial.get("timestamps") or {}

        if timestamps.get("duplicate_timestamps", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="temporal_integrity",
                    severity="high",
                    code="DUPLICATE_TIMESTAMPS",
                    title="Duplicate timestamps detected",
                    message=(
                        f"{timestamps['duplicate_timestamps']} "
                        "duplicate timestamp(s) were detected."
                    ),
                    action=(
                        "Determine whether duplicate timestamps represent "
                        "valid observations or duplicated records."
                    ),
                )
            )

        if timestamps.get("out_of_order_rows", 0) > 0:

            recommendations.append(
                self._recommendation(
                    category="temporal_integrity",
                    severity="high",
                    code="OUT_OF_ORDER_TIMESTAMPS",
                    title="Out-of-order timestamps detected",
                    message=(
                        f"{timestamps['out_of_order_rows']} "
                        "timestamp transition(s) are out of order."
                    ),
                    action=(
                        "Sort and validate the source data before "
                        "performing time-dependent calculations "
                        "or backtests."
                    ),
                )
            )

        frequency = financial.get("frequency") or {}

        gaps = frequency.get("gaps", [])

        if gaps:

            for gap in gaps:

                previous_timestamp = gap.get(
                    "previous_timestamp"
                )

                current_timestamp = gap.get(
                    "current_timestamp"
                )

                gap_seconds = gap.get(
                    "gap_seconds"
                )

                recommendations.append(
                    self._recommendation(
                        category="temporal_integrity",
                        severity="medium",
                        code="FREQUENCY_GAP",
                        title="Frequency inconsistency detected",
                        message=(
                            f"A {gap_seconds}-second interval was "
                            f"detected between "
                            f"{previous_timestamp} and "
                            f"{current_timestamp}."
                        ),
                        action=(
                            "Determine whether this gap is caused by "
                            "market closure, missing records, or "
                            "ingestion loss before using the dataset "
                            "for intraday research."
                        ),
                        details={
                            "previous_timestamp": previous_timestamp,
                            "current_timestamp": current_timestamp,
                            "gap_seconds": gap_seconds,
                            "observed_frequency_seconds": frequency.get(
                                "observed_frequency_seconds"
                            ),
                            "median_interval_seconds": frequency.get(
                                "median_interval_seconds"
                            ),
                        },
                    )
                )

        return recommendations

    def _recommend_from_structure(
        self,
        profile: dict[str, Any],
    ) -> list[dict[str, Any]]:

        recommendations = []

        structure = profile.get("structure")

        if not structure:
            return recommendations

        duplicate_rows = structure.get(
            "duplicate_rows",
            0,
        )

        if duplicate_rows > 0:

            recommendations.append(
                self._recommendation(
                    category="dataset_integrity",
                    severity="high",
                    code="DUPLICATE_ROWS",
                    title="Duplicate rows detected",
                    message=(
                        f"{duplicate_rows} duplicate row(s) "
                        "were detected."
                    ),
                    action=(
                        "Inspect duplicate records and determine "
                        "whether they are legitimate repeated "
                        "observations or duplicate ingestion records."
                    ),
                )
            )

        missing_cells = structure.get(
            "missing_cells",
            0,
        )

        if missing_cells > 0:

            recommendations.append(
                self._recommendation(
                    category="dataset_completeness",
                    severity="high",
                    code="MISSING_VALUES",
                    title="Missing values detected",
                    message=(
                        f"{missing_cells} missing cell(s) "
                        "were detected."
                    ),
                    action=(
                        "Identify affected columns and determine "
                        "whether missing observations should be "
                        "imputed, removed, or retained as missing."
                    ),
                )
            )

        return recommendations

    @staticmethod
    def _recommendation(
        category: str,
        severity: str,
        code: str,
        title: str,
        message: str,
        action: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        return {
            "category": category,
            "severity": severity,
            "code": code,
            "title": title,
            "message": message,
            "action": action,
            "details": details or {},
        }

    @staticmethod
    def _deduplicate(
        recommendations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        seen = set()
        result = []

        for recommendation in recommendations:

            code = recommendation["code"]

            if code in seen:
                continue

            seen.add(code)
            result.append(recommendation)

        return result