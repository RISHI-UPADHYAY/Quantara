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

        if len(timestamps) < 2:
            return {
                "observed_frequency_seconds": None,
                "median_interval_seconds": None,
                "gap_count": 0,
                "gaps": [],
            }

        timestamps = timestamps.sort_values()

        intervals = timestamps.diff().dropna()

        interval_seconds = intervals.dt.total_seconds()

        if interval_seconds.empty:
            return {
                "oberserved_frequency_seconds": None,
                "median_interval_seconds": None,
                "gap_count": 0,
                "gaps": [],
            }

        #The most frequently occuring interval is a better estimate of the expected
        #market-data frequency than the median when gaps are present.
        interval_counts = interval_seconds.value_counts()

        expected_frequency = float(
            interval_counts.index[0]
        )

        median_interval = float(
            interval_seconds.median()
        )

        gaps = []

        for index in range(1, len(timestamps)):

            previous_timestamp = timestamps.iloc[index - 1]
            current_timestamp = timestamps.iloc[index]

            gap_seconds = (
                current_timestamp - previous_timestamp
            ).total_seconds()

            if gap_seconds > expected_frequency:

                gaps.append(
                    {
                        "previous_timestamp": (
                            previous_timestamp.isoformat()
                        ),
                        "current_timestamp": (
                            current_timestamp.isoformat()
                        ),
                        "gap_seconds": int(
                            gap_seconds
                        ),
                    }
                )

        return {
            "observed_frequency_seconds": int(
                expected_frequency
            ),
            "median_interval_seconds": int(
                median_interval
            ),
            "gap_count": len(gaps),
            "gaps": gaps,
        }