from pathlib import Path

from app.services.profiling.market_data_quality import MarketDataQualityAnalyzer

import pandas as pd

class FinancialDataProfiler:

    OHLC_COLUMNS = {
        "open",
        "high",
        "low",
        "close",
    }

    VOLUME_COLUMNS = {
        "volume",
        "vol",
    }

    TIMESTAMP_COLUMNS = {
        "timestamp",
        "datetime",
        "date",
        "time",
    }

    def __init__(self):
        self.quality_analyzer = MarketDataQualityAnalyzer()

    def profile(self, file_path: Path) -> dict:

        if not file_path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"Path is not a file: {file_path}"
            )

        if file_path.suffix.lower() != ".csv":
            raise ValueError(
                "Only CSV files are supported"
            )

        dataframe = pd.read_csv(file_path)

        columns = {
            str(column).strip().lower()
            for column in dataframe.columns
        }

        has_ohlc = self.OHLC_COLUMNS.issubset(columns)
        has_volume = bool(
            self.VOLUME_COLUMNS.intersection(columns)
        )

        timestamp_column = self._find_timestamp_column(dataframe)

        report = {
            "is_market_data": has_ohlc,
            "has_ohlcv": has_ohlc and has_volume,
            "timestamp_column": timestamp_column,
            "ohlc": None,
            "volume": None,
            "timestamps": None,
            "frequency": None,
        }

        if has_ohlc:
            report["ohlc"] = self._check_ohlc_integrity(dataframe)

        if has_volume:
            report["volume"] = self._check_volume(
                dataframe,
                columns,
            )

        if timestamp_column:
            report["timestamps"] = self._check_timestamps(
                dataframe,
                timestamp_column,
            )

            report["frequency"] = (
                self.quality_analyzer.analyze_frequency(
                    dataframe,
                    timestamp_column,
                )
            )

        return report

    def _find_timestamp_column(self, dataframe: pd.DataFrame) -> str | None:
        for column in dataframe.columns:
            normalized = str(column).strip().lower()

            if normalized in self.TIMESTAMP_COLUMNS:
                return str(column)

        return None

    def _check_ohlc_integrity(self, dataframe: pd.DataFrame) -> dict:
        open_column = self._find_column(
            dataframe,
            "open",
        )

        high_column = self._find_column(
            dataframe,
            "high",
        )

        low_column = self._find_column(
            dataframe,
            "low",
        )

        close_column = self._find_column(
            dataframe,
            "close",
        )

        open_series = pd.to_numeric(
            dataframe[open_column],
            errors="coerce",
        )

        high_series = pd.to_numeric(
            dataframe[high_column],
            errors="coerce",
        )

        low_series = pd.to_numeric(
            dataframe[low_column],
            errors="coerce",
        )

        close_series = pd.to_numeric(
            dataframe[close_column],
            errors="coerce",
        )

        invalid_rows = (
            (low_series > open_series)
            | (low_series > close_series)
            | (high_series < open_series)
            | (high_series < close_series)
            | (low_series > high_series)
        )

        negative_price_rows = (
            (open_series < 0)
            | (high_series < 0)
            | (low_series < 0)
            | (close_series < 0)
        )

        zero_price_rows = (
            (open_series == 0)
            | (high_series == 0)
            | (low_series == 0)
            | (close_series == 0)
        )

        return {
            "invalid_ohlc_rows": int(
                invalid_rows.sum()
            ),
            "negative_price_rows": int(
                negative_price_rows.sum()
            ),
            "zero_price_rows": int(
                zero_price_rows.sum()
            ),
        }

    def _check_volume(self, dataframe: pd.DataFrame, columns: set[str]) -> dict:
        volume_column = next(
            column
            for column in dataframe.columns
            if str(column).strip().lower() in self.VOLUME_COLUMNS
        )

        volume = pd.to_numeric(
            dataframe[volume_column],
            errors="coerce",
        )

        negative_volume_rows = volume < 0
        zero_volume_rows = volume == 0

        return {
            "column": str(volume_column),
            "negative_volume_rows": int(
                negative_volume_rows.sum()
            ),
            "zero_volume_rows": int(
                zero_volume_rows.sum()
            ),
        }

    def _check_timestamps(self, dataframe: pd.DataFrame, timestamp_column: str) -> dict:
        timestamps = pd.to_datetime(
            dataframe[timestamp_column],
            errors="coerce",
        )

        invalid_timestamp_rows = timestamps.isna()

        valid_timestamps = timestamps.dropna()

        duplicate_timestamps = int(
            valid_timestamps.duplicated().sum()
        )

        out_of_order_rows = 0

        if len(valid_timestamps) > 1:
            differences = valid_timestamps.diff()

            out_of_order_rows = int(
                (differences < pd.Timedelta(0)).sum()
            )

        return {
            "invalid_timestamp_rows": int(
                invalid_timestamp_rows.sum()
            ),
            "duplicate_timestamps":duplicate_timestamps,
            "out_of_order_rows": out_of_order_rows,
            "min_timestamp": (
                valid_timestamps.min().isoformat()
                if not valid_timestamps.empty
                else None
            ),
            "max_timestamp": (
                valid_timestamps.max().isoformat()
                if not valid_timestamps.empty
                else None
            ),
        }

    @staticmethod
    def _find_column(dataframe: pd.DataFrame, target: str) -> str:

        for column in dataframe.columns:
            if str(column).strip().lower() == target:
                return str(column)

        raise ValueError(
            f"Required column not found: {target}"
        )