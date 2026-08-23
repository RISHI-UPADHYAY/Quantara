import pandas as pd


class MarketDataQualityAnalyzer:

    def analyze_frequency(
        self,
        dataframe: pd.DataFrame,
        timestamp_column: str,
    ) -> dict:

        timestamps = pd.to_datetime(
            dataframe[timestamp_column],
            errors="coerce",
        ).dropna()

        timestamps = timestamps.sort_values()

        if len(timestamps) < 2:
            return {
                "observed_frequency_seconds": None,
                "median_interval_seconds": None,
                "gap_count": 0,
                "gaps": [],
            }

        differences = timestamps.diff().dropna()

        median_interval = differences.median()

        gaps = []

        for index in range(1, len(timestamps)):

            previous_timestamp = timestamps.iloc[index - 1]
            current_timestamp = timestamps.iloc[index]

            difference = (
                current_timestamp - previous_timestamp
            )

            if difference > median_interval * 1.5:

                gaps.append(
                    {
                        "previous_timestamp": (
                            previous_timestamp.isoformat()
                        ),
                        "current_timestamp": (
                            current_timestamp.isoformat()
                        ),
                        "gap_seconds": int(
                            difference.total_seconds()
                        ),
                    }
                )

        return {
            "observed_frequency_seconds": int(
                median_interval.total_seconds()
            ),
            "median_interval_seconds": int(
                median_interval.total_seconds()
            ),
            "gap_count": len(gaps),
            "gaps": gaps,
        }