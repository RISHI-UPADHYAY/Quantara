from typing import Any

import pandas as pd


class TypeNormalizer:

    NUMERIC_COLUMNS = {
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    def normalize(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:

        dataframe = dataframe.copy()

        conversions: dict[str, Any] = {}
        conversion_errors: dict[str, int] = {}

        for column in self.NUMERIC_COLUMNS:

            if column not in dataframe.columns:
                continue

            original = dataframe[column]

            converted = pd.to_numeric(
                original,
                errors="coerce",
            )

            errors = int(
                (
                    original.notna()
                    & converted.isna()
                ).sum()
            )

            dataframe[column] = converted

            conversions[column] = str(
                dataframe[column].dtype
            )

            conversion_errors[column] = errors

        return dataframe, {
            "numeric_conversions": conversions,
            "conversion_errors": conversion_errors,
        }