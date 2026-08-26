from typing import Any

import pandas as pd


class VolumeAnalyzer:

    PRICE_COLUMNS = {
        "open",
        "high",
        "low",
        "close",
    }

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]: 

        self._validate_input(dataframe)

        volume = dataframe["volume"]

        volume_count = len(volume)

        if volume_count == 0:
            return self._empty_result()

        zero_volume_count = int(
            (volume == 0).sum()
        )

        negative_volume_count = int(
            (volume < 0).sum()
        )

        mean_volume = float(
            volume.mean()
        )

        median_volume = float(
            volume.median()
        )

        min_volume = float(
            volume.min()
        )

        max_volume = float(
            volume.max()
        )

        std_volume = float(
            float(volume.std())
            if volume_count > 1
            else 0.0
        )

        total_volume = float(
            volume.sum()
        )

        coefficient_of_variation = (
            float(std_volume / mean_volume)
            if mean_volume != 0
            else 0.0
        )

        return {
            "volume_column": "volume",
            "row_count": len(dataframe),
            "volume_count": volume_count,
            "statistics": {
                "mean": mean_volume,
                "median": median_volume,
                "min": min_volume,
                "max": max_volume,
                "std": std_volume,
                "total": total_volume,
            },
            "activity": {
                "zero_volume_count": zero_volume_count,
                "negative_volume_count": negative_volume_count,
                "coefficient_of_variation": coefficient_of_variation,
            },
        }


    @staticmethod
    def _validate_input(
        dataframe: pd.DataFrame,
    ) -> None:

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):
            raise TypeError(
                "Input must be a pandas DataFrame."
            )

        if dataframe.empty:
            raise ValueError(
                "Input DataFrame cannot be empty."
            )

        if "volume" not in dataframe.columns:
            raise ValueError(
                "Required column 'volume' is missing."
            )

        volume = dataframe["volume"]

        numeric_volume = pd.to_numeric(
            volume,
            errors="coerce",
        )

        if numeric_volume.isna().any():
            raise ValueError(
                "Volume contains invalid or null values."
            )

        if (numeric_volume < 0).any():
            raise ValueError(
                "Volume values cannot be negative."
            )

        if not pd.api.types.is_numeric_dtype(
            volume
        ):
            raise ValueError(
                "Volume column must contain numeric values."
            )


    @staticmethod
    def _empty_result() -> dict[str, Any]:
    
        return {
            "volume_column": "volume",
            "row_count": 0,
            "volume_count": 0,
            "statistics": {
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std": 0.0,
                "total": 0.0,
            },
            "activity": {
                "zero_volume_count": 0,
                "negative_volume_count": 0,
                "coefficient_of_variation": 0.0,
            }
        }