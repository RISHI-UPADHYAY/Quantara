from typing import Any

import pandas as pd


class ColumnMapper:

    COLUMN_ALIASES = {
        "timestamp": {
            "timestamp",
            "datetime",
            "date_time",
            "date",
            "time",
            "ts",
        },
        "symbol": {
            "symbol",
            "ticker",
            "instrument",
            "security",
            "asset",
        },
        "open": {
            "open",
            "open_price",
            "opening_price",
        },
        "high": {
            "high",
            "high_price",
            "highest_price",
        },
        "low": {
            "low",
            "low_price",
            "lowest_price",
        },
        "close": {
            "close",
            "close_price",
            "closing_price",
            "last",
            "last_price",
        },
        "volume": {
            "volume",
            "vol",
            "traded_volume",
        },
    }


    def map_columns(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:

        rename_map: dict[str, str] = {}
        unmapped_columns: list[str] = []
        mapped_columns: dict[str, Any] = {}

        used_targets: set[str] = set()

        for column in dataframe.columns:

            original  = str(column)
            normalized = (
                original
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

            target = self._find_target(normalized)

            if target is None:
                unmapped_columns.append(original)
                continue

            if target in used_targets:
                raise ValueError(
                    f"Multiple columns map to canonical column '{target}'"
                )

            rename_map[original] = target
            mapped_columns[original] = target
            used_targets.add(target)

        normalized_dataframe = dataframe.rename(
            columns=rename_map
        )

        report = {
            "mapped_columns": mapped_columns,
            "unmapped_columns": unmapped_columns,
            "canonical_columns": list(
                normalized_dataframe.columns
            ),
        }

        return normalized_dataframe, report


    def _find_target(self, column: str) -> str | None:

        for target, aliases in self.COLUMN_ALIASES.items():

            if column in aliases:
                return target

        return None