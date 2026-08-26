from typing import Any

import pandas as pd


class DrawdownAnalyzer:

    def analyze(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, Any]:

        self._validate_input(dataframe)

        close = dataframe["close"].astype(float)

        row_count = len(dataframe)

        if row_count == 1:
            return self._single_row_result(
                float(close.iloc[0])
            )

        cumulative_returns = (
            close / close.iloc[0]
        )

        running_peak = (
            cumulative_returns.cummax()
        )

        drawdown = (
            cumulative_returns / running_peak
        ) - 1.0

        maximum_drawdown = float(
            drawdown.min()
        )

        maximum_drawdown_percentage = (
            maximum_drawdown * 100.0
        )

        maximum_drawdown_index = (
            drawdown.idxmin()
        )

        peak_before_drawdown = (
            running_peak.loc[
                maximum_drawdown_index
            ]
        )

        peak_index = (
            cumulative_returns.loc[
                :maximum_drawdown_index
            ].idxmax()
        )

        recovery_index = self._find_recovery_index(
            cumulative_returns,
            peak_before_drawdown,
            maximum_drawdown_index,
        )

        if recovery_index is None:
            recovery_duration = None

        else:
            recovery_duration = int(
                recovery_index - peak_index
            )

        drawdown_duration = self._calculate_max_duration(
            drawdown
        )

        return {
            "price_column": "close",
            "row_count": row_count,
            "drawdown": {
                "maximum": maximum_drawdown,
                "maximum_percentage": (
                    maximum_drawdown_percentage
                ),
                "maximum_index": int(
                    maximum_drawdown_index
                ),
                "maximum_duration": (
                    drawdown_duration
                ),
                "recovered": (
                    recovery_index is not None
                ),
                "recovery_index": (
                    int(recovery_index)
                    if recovery_index is not None
                    else None
                ),
                "recovery_duration": (
                    recovery_duration
                ),
            },
            "equity": {
                "initial": float(close.iloc[0]),
                "final": float(close.iloc[-1]),
                "peak": float(close.max()),
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

        if "close" not in dataframe.columns:
            raise ValueError(
                "Required column 'close' is missing."
            )

        close = pd.to_numeric(
            dataframe["close"],
            errors="coerce",
        )

        if close.isna().any():
            raise ValueError(
                "Close price contains invalid or null values."
            )

        if (close <= 0).any():
            raise ValueError(
                "Close prices must be greater than zero."
            )


    @staticmethod
    def _find_recovery_index(
        cumulative_returns: pd.Series,
        peak_value: float,
        maximum_drawdown_index: int,
    ) -> int | None:

        recovery = cumulative_returns.loc[
            maximum_drawdown_index:
        ]

        recovered = recovery[
            recovery >= peak_value
        ]

        if recovered.empty:
            return None

        return int(recovered.index[0])


    @staticmethod
    def _calculate_max_duration(
        drawdown: pd.Series,
    ) -> int:

        current_duration = 0
        maximum_duration = 0

        for value in drawdown:

            if value < 0:
                current_duration += 1
                maximum_duration = max(
                    maximum_duration,
                    current_duration,
                )
            else:
                current_duration = 0

        return int(maximum_duration)


    @staticmethod
    def _single_row_result(
        initial_price: float,
    ) -> dict[str, Any]:

        return {
            "price_column": "close",
            "row_count": 1,
            "drawdown": {
                "maximum": 0.0,
                "maximum_percentage": 0.0,
                "maximum_index": 0,
                "maximum_duration": 0,
                "recovered": True,
                "recovery_index": 0,
                "recovery_duration": 0,            
            },
            "equity": {
                "initial": initial_price,
                "final": initial_price,
                "peak": initial_price,
            },
        }