from pathlib import Path

import pandas as pd

class CSVProfiler:

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

        return {
            "row_count": int(len(dataframe)),
            "column_count": int(len(dataframe.columns)),
            "columns": self._profile_columns(dataframe),
            "duplicate_rows": int(dataframe.duplicated().sum()),
            "missing_cells": int(dataframe.isna().sum().sum()),
            "memory_usage_bytes": int(dataframe.memory_usage(deep=True).sum()),
        }

    def _profile_columns(self, dataframe: pd.DataFrame) -> list[dict]:
        columns = []

        for column in dataframe.columns:

            series = dataframe[column]

            profile = {
                "name": str(column),
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "null_percentage": float(series.isna().mean() * 100),
                "unique_count": int(series.nunique(dropna=True)),
            }

            if pd.api.types.is_numeric_dtype(series):

                profile.update(
                    {
                        "min": self._safe_float(series.min()),
                        "max": self._safe_float(series.max()),
                        "mean": self._safe_float(series.mean()),
                        "std": self._safe_float(series.std()),
                    }
                )

            columns.append(profile)
        return columns

    @staticmethod
    def _safe_float(value):

        if pd.isna(value):
            return None

        return float(value)