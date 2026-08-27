from __future__ import annotations

import math

import pandas as pd

from app.services.analysis.price_range_analyzer import PriceRangeAnalyzer


def run_test(
    analyzer: PriceRangeAnalyzer,
    name: str,
    dataframe,
    expected_exception: type[Exception] | None = None,
    expected_message: str | None = None,
    assertions=None,
) -> None:
    print("-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    try:
        result = analyzer.analyze(dataframe)

        if expected_exception is not None:
            print("RESULT: FAILED")
            print(
                f"Expected {expected_exception.__name__}, "
                "but no exception was raised."
            )
            raise AssertionError(
                f"{name}: expected {expected_exception.__name__}"
            )

        if assertions is not None:
            assertions(result)

        print("RESULT: PASSED")
        print(result)

    except Exception as exc:
        if expected_exception is None:
            print("RESULT: FAILED")
            print(f"Unexpected exception: {type(exc).__name__}")
            print(f"Message: {exc}")
            raise

        if not isinstance(exc, expected_exception):
            print("RESULT: FAILED")
            print(
                f"Expected exception: {expected_exception.__name__}\n"
                f"Actual exception: {type(exc).__name__}\n"
                f"Message: {exc}"
            )
            raise AssertionError(
                f"{name}: unexpected exception type"
            ) from exc

        if expected_message and expected_message not in str(exc):
            print("RESULT: FAILED")
            print(f"Expected message containing: {expected_message}")
            print(f"Actual message: {exc}")
            raise AssertionError(
                f"{name}: unexpected exception message"
            ) from exc

        print("RESULT: PASSED")
        print(f"Raised: {type(exc).__name__}")
        print(f"Message: {exc}")


def base_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-01-01 09:15:00",
                    "2026-01-01 09:16:00",
                    "2026-01-01 09:17:00",
                    "2026-01-01 09:18:00",
                    "2026-01-01 09:20:00",
                ]
            ),
            "symbol": [
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
            ],
            "open": [26000, 26005, 26010, 26015, 26020],
            "high": [26010, 26020, 26025, 26030, 26025],
            "low": [25990, 26000, 26005, 26010, 26015],
            "close": [26005, 26015, 26020, 26025, 26020],
            "volume": [1000, 1100, 1050, 1200, 900],
        }
    )


def assert_single_row(result: dict) -> None:
    assert result["row_count"] == 1

    assert result["range_statistics"]["mean"] == 20.0
    assert result["range_statistics"]["median"] == 20.0
    assert result["range_statistics"]["min"] == 20.0
    assert result["range_statistics"]["max"] == 20.0
    assert result["range_statistics"]["std"] == 0.0

    assert result["range_percentage_statistics"]["std"] == 0.0

    assert result["activity"]["average_range"] == 20.0
    assert result["activity"]["maximum_range"] == 20.0
    assert result["activity"]["zero_range_count"] == 0


def assert_zero_range(result: dict) -> None:
    assert result["row_count"] == 1

    assert result["range_statistics"]["mean"] == 0.0
    assert result["range_statistics"]["median"] == 0.0
    assert result["range_statistics"]["min"] == 0.0
    assert result["range_statistics"]["max"] == 0.0
    assert result["range_statistics"]["std"] == 0.0

    assert result["range_percentage_statistics"]["mean"] == 0.0
    assert result["range_percentage_statistics"]["median"] == 0.0
    assert result["range_percentage_statistics"]["min"] == 0.0
    assert result["range_percentage_statistics"]["max"] == 0.0
    assert result["range_percentage_statistics"]["std"] == 0.0

    assert result["activity"]["zero_range_count"] == 1


def assert_valid_result(result: dict) -> None:
    assert result["row_count"] == 5

    range_stats = result["range_statistics"]

    assert range_stats["mean"] == 18.0
    assert range_stats["median"] == 20.0
    assert range_stats["min"] == 10.0
    assert range_stats["max"] == 20.0
    assert math.isclose(
        range_stats["std"],
        4.0,
        rel_tol=1e-12,
        abs_tol=1e-12,
    )

    percentage_stats = result["range_percentage_statistics"]

    assert percentage_stats["min"] > 0.0
    assert percentage_stats["max"] > percentage_stats["min"]
    assert percentage_stats["mean"] > 0.0

    assert result["activity"]["average_range"] == 18.0
    assert result["activity"]["maximum_range"] == 20.0
    assert result["activity"]["zero_range_count"] == 0


def main() -> None:
    analyzer = PriceRangeAnalyzer()

    print("=" * 60)
    print("QUANTARA PRICE RANGE ANALYZER - FAILURE TESTS")
    print("=" * 60)

    # ---------------------------------------------------------
    # Empty DataFrame
    # ---------------------------------------------------------
    run_test(
        analyzer,
        "Empty DataFrame",
        pd.DataFrame(),
        expected_exception=ValueError,
        expected_message="Input DataFrame cannot be empty.",
    )

    # ---------------------------------------------------------
    # Non-DataFrame input
    # ---------------------------------------------------------
    run_test(
        analyzer,
        "Non-DataFrame input",
        {"close": [100]},
        expected_exception=TypeError,
        expected_message="Input must be a pandas DataFrame.",
    )

    # ---------------------------------------------------------
    # Missing open column
    # ---------------------------------------------------------
    dataframe = base_dataframe().drop(columns=["open"])

    run_test(
        analyzer,
        "Missing open column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing:",
    )

    # ---------------------------------------------------------
    # Missing high column
    # ---------------------------------------------------------
    dataframe = base_dataframe().drop(columns=["high"])

    run_test(
        analyzer,
        "Missing high column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing:",
    )

    # ---------------------------------------------------------
    # Missing low column
    # ---------------------------------------------------------
    dataframe = base_dataframe().drop(columns=["low"])

    run_test(
        analyzer,
        "Missing low column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing:",
    )

    # ---------------------------------------------------------
    # Missing close column
    # ---------------------------------------------------------
    dataframe = base_dataframe().drop(columns=["close"])

    run_test(
        analyzer,
        "Missing close column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing:",
    )

    # ---------------------------------------------------------
    # Null open
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["open"] = dataframe["open"].astype(object)
    dataframe.loc[0, "open"] = None

    run_test(
        analyzer,
        "Null open price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Open contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Null high
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["high"] = dataframe["high"].astype(object)
    dataframe.loc[0, "high"] = None

    run_test(
        analyzer,
        "Null high price",
        dataframe,
        expected_exception=ValueError,
        expected_message="High contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Null low
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["low"] = dataframe["low"].astype(object)
    dataframe.loc[0, "low"] = None

    run_test(
        analyzer,
        "Null low price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Low contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Null close
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["close"] = dataframe["close"].astype(object)
    dataframe.loc[0, "close"] = None

    run_test(
        analyzer,
        "Null close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Non-numeric open
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["open"] = dataframe["open"].astype(object)
    dataframe.loc[0, "open"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric open price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Open contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Non-numeric high
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["high"] = dataframe["high"].astype(object)
    dataframe.loc[0, "high"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric high price",
        dataframe,
        expected_exception=ValueError,
        expected_message="High contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Non-numeric low
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["low"] = dataframe["low"].astype(object)
    dataframe.loc[0, "low"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric low price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Low contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Non-numeric close
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe["close"] = dataframe["close"].astype(object)
    dataframe.loc[0, "close"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close contains invalid or null values.",
    )

    # ---------------------------------------------------------
    # Zero close
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "close"] = 0

    run_test(
        analyzer,
        "Zero close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must be greater than zero.",
    )

    # ---------------------------------------------------------
    # Negative close
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "close"] = -100

    run_test(
        analyzer,
        "Negative close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must be greater than zero.",
    )

    # ---------------------------------------------------------
    # High lower than low
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "high"] = 25980

    run_test(
        analyzer,
        "High lower than low",
        dataframe,
        expected_exception=ValueError,
        expected_message="High prices cannot be lower than low prices.",
    )

    # ---------------------------------------------------------
    # Open above high
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "open"] = 26020

    run_test(
        analyzer,
        "Open above high",
        dataframe,
        expected_exception=ValueError,
        expected_message="Open prices must fall within the high-low range.",
    )

    # ---------------------------------------------------------
    # Open below low
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "open"] = 25980

    run_test(
        analyzer,
        "Open below low",
        dataframe,
        expected_exception=ValueError,
        expected_message="Open prices must fall within the high-low range.",
    )

    # ---------------------------------------------------------
    # Close above high
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "close"] = 26020

    run_test(
        analyzer,
        "Close above high",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must fall within the high-low range.",
    )

    # ---------------------------------------------------------
    # Close below low
    # ---------------------------------------------------------
    dataframe = base_dataframe()
    dataframe.loc[0, "close"] = 25980

    run_test(
        analyzer,
        "Close below low",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must fall within the high-low range.",
    )

    # ---------------------------------------------------------
    # Single-row DataFrame
    # ---------------------------------------------------------
    dataframe = base_dataframe().iloc[[0]].copy()

    run_test(
        analyzer,
        "Single-row DataFrame",
        dataframe,
        assertions=assert_single_row,
    )

    # ---------------------------------------------------------
    # Zero-range candle
    # ---------------------------------------------------------
    dataframe = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-01-01 09:15:00"]),
            "symbol": ["NIFTY50"],
            "open": [26000],
            "high": [26000],
            "low": [26000],
            "close": [26000],
            "volume": [1000],
        }
    )

    run_test(
        analyzer,
        "Zero-range candle",
        dataframe,
        assertions=assert_zero_range,
    )

    # ---------------------------------------------------------
    # Valid DataFrame
    # ---------------------------------------------------------
    dataframe = base_dataframe()

    run_test(
        analyzer,
        "Valid DataFrame",
        dataframe,
        assertions=assert_valid_result,
    )

    print("=" * 60)
    print("ALL PRICE RANGE ANALYZER FAILURE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()