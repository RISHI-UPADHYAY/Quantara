from typing import Any


class NormalizationReportBuilder:

    def build(
        self,
        report: dict[str, Any],
    ) -> dict[str, Any]:

        type_normalization = report.get(
            "type_normalization",
            {},
        )

        conversion_errors = type_normalization.get(
            "conversion_errors",
            {},
        )

        total_conversion_errors = sum(
            conversion_errors.values()
        )

        column_mapping = report.get(
            "column_mapping",
            {},
        )

        timestamp_normalization = report.get(
            "timestamp_normalization",
            {},
        )

        return {
            "original_columns": report.get(
                "original_columns",
                [],
            ),
            "column_mapping": column_mapping,
            "type_normalization": type_normalization,
            "timestamp_normalization": timestamp_normalization,
            "row_count": report.get(
                "row_count",
                0,
            ),
            "column_count": report.get(
                "column_count",
                0,
            ),
            "conversion_errors": {
                "total": total_conversion_errors,
                "by_column": conversion_errors,
            },
        }