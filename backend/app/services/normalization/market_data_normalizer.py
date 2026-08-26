from pathlib import Path
from typing import Any

import pandas as pd

from app.services.normalization.column_mapper import ColumnMapper
from app.services.normalization.type_normalizer import TypeNormalizer
from app.services.normalization.timestamp_normalizer import TimestampNormalizer


class MarketDataNormalizer:

    def __init__(self):
        self.column_mapper = ColumnMapper()
        self.type_normalizer = TypeNormalizer()
        self.timestamp_normalizer = TimestampNormalizer()


    def normalize(
        self,
        file_path: Path,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:

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

        dataframe = pd.read_csv(
            file_path
        )

        original_columns = [
            str(column)
            for column in dataframe.columns
        ]

        dataframe, column_report = (
            self.column_mapper.map_columns(
                dataframe
            )
        )

        dataframe, type_report = (
            self.type_normalizer.normalize(
                dataframe
            )
        )

        dataframe, timestamp_report = (
            self.timestamp_normalizer.normalize(
                dataframe
            )
        )

        dataframe = self._normalize_symbol(
            dataframe
        )

        report = {
            "original_columns": original_columns,
            "column_mapping": column_report,
            "type_normalization": type_report,
            "timestamp_normalization": timestamp_report,
            "row_count": len(dataframe),
            "column_count": len(dataframe.columns),
        }

        return dataframe, report


    @staticmethod
    def _normalize_symbol(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if "symbol" not in dataframe.columns:
            return dataframe

        dataframe["symbol"] = (
            dataframe["symbol"]
            .astype("string")
            .str.strip()
        )

        return dataframe