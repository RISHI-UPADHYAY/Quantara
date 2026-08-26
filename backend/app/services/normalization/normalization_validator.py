from typing import Any

import pandas as pd


class NormalizationValidator:

    REQUIRED_COLUMNS = {
        "timestamp",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    PRICE_COLUMNS = {
        "open",
        "high",
        "low",
        "close",
    }

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        checks: list[dict[str, Any]] = []

        checks.append(
            self._check_required_columns(dataframe)
        )

        checks.append(
            self._check_null_values(dataframe)
        )

        checks.append(
            self._check_numeric_columns(dataframe)
        )

        checks.append(
            self._check_timestamp(dataframe)
        )

        checks.append(
            self._check_symbols(dataframe)
        )

        checks.append(
            self._check_ohlc_integrity(dataframe)
        )

        checks.append(
            self._check_volume(dataframe)
        )

        errors = [
            check
            for check in checks
            if check["status"] == "fail"
        ]

        warnings = [
            check
            for check in checks
            if check["status"] == "warning"
        ]

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "checks": checks,
        }


    def _check_required_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        columns = {
            str(column).strip().lower()
            for column in dataframe.columns
        }

        missing = sorted(
            self.REQUIRED_COLUMNS - columns
        )

        if missing:
            return {
                "name": "required_columns",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Required columns are missing."
                ),
                "details": {
                    "missing_columns": missing,
                },
            }

        return {
            "name": "required_columns",
            "status": "pass",
            "severity": "info",
            "message": (
                "All required columns are present."
            ),
            "details": {
                "missing_columns": [],
            },
        }


    def _check_null_values(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        required_present = [
            column
            for column in self.REQUIRED_COLUMNS
            if column in dataframe.columns
        ]

        null_counts = {
            column: int(dataframe[column].isna().sum())
            for column in required_present
        }

        total_nulls = sum(
            null_counts.values()
        )

        columns_with_nulls = {
            column: count
            for column, count in null_counts.items()
            if count > 0
        }

        if total_nulls > 0:
            return {
                "name": "required_field_nulls",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{total_nulls} null value(s) detected in required fields."
                ),
                "details": {
                    "null_counts": columns_with_nulls,
                },
            }

        return {
            "name": "required_field_nulls",
            "status": "pass",
            "severity": "info",
            "message": (
                "No null values detected in required fields."
            ),
            "details": {
                "null_counts": {},
            },
        }


    def _check_numeric_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        numeric_columns = (
            self.PRICE_COLUMNS
            | {"volume"}
        )

        missing_columns = (
            numeric_columns - set(dataframe.columns)
        )

        if missing_columns: 
            return {
                "name": "numeric_types",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Required numeric columns are missing."
                ),
                "details": {
                    "missing_columns": sorted(
                        missing_columns
                    ),
                },
            }

        invalid_columns: dict[str, int] = {}

        for column in numeric_columns:

            invalid_count = int(
                pd.to_numeric(
                    dataframe[column],
                    errors="coerce",
                ).isna().sum()
            )

            if invalid_count > 0:
                invalid_columns[column] = (
                    invalid_count
                )

        if invalid_columns:
            return {
                "name": "numeric_types",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Invalid numeric values detected."
                ),
                "details": {
                    "invalid_counts": invalid_columns,
                },
            }

        return {
            "name": "numeric_types",
            "status": "pass",
            "severity": "info",
            "message": (
                "All required numeric fields contain valid numeric values."
            ),
            "details": {
                "invalid_counts": {},
            },
        }


    def _check_timestamp(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        if "timestamp" not in dataframe.columns:
            return {
                "name": "timestamp_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Timestamp column is missing."
                ),
            }

        timestamps = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
        )

        invalid_count = int(
            timestamps.isna().sum()
        )

        if invalid_count > 0:
            return {
                "name": "timestamp_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{invalid_count} invalid timestamp(s) detected."
                ),
                "details": {
                    "invalid_timestamp_count": invalid_count,
                },
            }

        duplicate_count = int(  
            timestamps.duplicated().sum()
        )

        out_of_order_count = 0

        if len(timestamps) > 1:
            differences = timestamps.diff()

            out_of_order_count = int(
                (differences < pd.Timedelta(0)).sum()
            ) 

        if duplicate_count > 0:
            return {
                "name": "timestamp_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{duplicate_count} duplicate timestamp(s) detected."
                ),
                "details": {
                    "duplicate_timestamps": duplicate_count,
                    "out_of_order_rows": out_of_order_count,
                },
            }

        if out_of_order_count > 0:
            return {
                "name": "timestamp_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{out_of_order_count} out-of-order timestamp(s) detected."
                ),
                "details": {
                    "duplicate_timestamps": duplicate_count,
                    "out_of_order_rows": out_of_order_count,
                },
            }

        return {
            "name": "timestamp_integrity",
            "status": "pass",
            "severity": "info",
            "message": (
                "Timestamp sequence is valid."
            ),
            "details": {
                "duplicate_timestamps": 0,
                "out_of_order_rows": 0,
            },
        }


    def _check_symbols(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        if "symbol" not in dataframe.columns:
            return {
                "name": "symbol_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Symbol column is missing."
                ),
            }

        symbols = (
            dataframe["symbol"]
            .astype("string")
            .str.strip()
        )

        empty_count = int(
            symbols.isna().sum()
            + (symbols == "").sum()
        )

        if empty_count > 0:
            return {
                "name": "symbol_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{empty_count} empty symbol value(s) detected."
                ),
                "details": {
                    "empty_symbol_count": empty_count,
                },
            }

        return {
            "name": "symbol_integrity",
            "status": "pass",
            "severity": "info",
            "message": (
                "All symbol values are valid."
            ),
            "details": {
                "empty_symbol_count": 0,
                "unique_symbol_count": int(
                    symbols.nunique()
                ),
            },
        }


    def _check_ohlc_integrity(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        required = self.PRICE_COLUMNS

        if not required.issubset(
            dataframe.columns
        ):
            return {
                "name": "ohlc_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Required OHLC columns are missing."
                ),
            }

        open_series = pd.to_numeric(
            dataframe["open"],
            errors="coerce",
        )

        high_series = pd.to_numeric(
            dataframe["high"],
            errors="coerce",
        )

        low_series = pd.to_numeric(
            dataframe["low"],
            errors="coerce",
        )

        close_series = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        invalid_relationships = (
            (high_series < open_series)
            | (high_series < close_series)
            | (low_series > open_series)
            | (low_series > close_series)
            | (low_series > high_series)
        )

        negative_prices = (
            (open_series < 0)
            | (high_series < 0)
            | (low_series < 0)
            | (close_series < 0)
        )

        zero_prices = (
            (open_series == 0)
            | (high_series == 0)
            | (low_series == 0)
            | (close_series == 0)
        )

        invalid_count = int(
            invalid_relationships.sum()
        )

        negative_count = int(
            negative_prices.sum()
        )

        zero_count = int(
            zero_prices.sum()
        )

        if (
            invalid_count > 0
            or negative_count > 0
            or zero_count > 0
        ):
            return {
                "name": "ohlc_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Invalid OHLC values detected."
                ),
                "details": {
                    "invalid_ohlc_rows": invalid_count,
                    "negative_price_rows": negative_count,
                    "zero_price_rows": zero_count,
                },
            }

        return {
            "name": "ohlc_integrity",
            "status": "pass",
            "severity": "info",
            "message": (
                "OHLC relationships and prices are valid."
            ),
            "details": {
                "invalid_ohlc_rows": 0,
                "negative_price_rows": 0,
                "zero_price_rows": 0,
            },
        }


    def _check_volume(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        if "volume" not in dataframe.columns:
            return {
                "name": "volume_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    "Volume column is missing."
                ),
            }

        volume = pd.to_numeric(
            dataframe["volume"],
            errors="coerce",
        )

        negative_count = int(
            (volume < 0).sum()
        )

        if negative_count > 0:
            return {
                "name": "volume_integrity",
                "status": "fail",
                "severity": "error",
                "message": (
                    f"{negative_count} negative volume value(s) detected."
                ),
                "details": {
                    "negative_volume_rows": negative_count,
                },
            }

        return {
            "name": "volume_integrity",
            "status": "pass",
            "severity": "info",
            "message": (
                "Volume values are valid."
            ),
            "details": {
                "negative_volume_rows": 0,
                "zero_volume_rows": int(
                    (volume == 0).sum()
                ),
            },
        }