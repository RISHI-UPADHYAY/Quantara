from typing import Any

import pandas as pd


class TimestampNormalizer:

    def normalize(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:

        dataframe = dataframe.copy()

        if "timestamp" not in dataframe.columns:
            return dataframe, {
                "timestamp_column_present": False,
                "invalid_timestamp_count": 0,
            }

        original = dataframe["timestamp"]

        timestamps = pd.to_datetime(
            original, 
            errors="coerce",
        )

        invalid_count = int(
            timestamps.isna().sum()
        )

        dataframe["timestamp"] = timestamps

        return dataframe, {
            "timestamp_column_present": True,
            "invalid_timestamp_count": invalid_count,
            "timezone": None,
        }