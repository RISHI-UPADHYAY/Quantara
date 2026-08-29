"""
Quantara - Correlation Analyzer Failure / Edge Case Tests

Run from:
    backend/

Command:
    python test_correlation_analyzer_invalid.py
"""

from datetime import datetime

import numpy as np
import pandas as pd

from app.services.analysis.correlation_analyzer import CorrelationAnalyzer


# ---------------------------------------------------------------------------
# BASE TEST DATA
# ---------------------------------------------------------------------------

def create_valid_dataframe() -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01 09:15:00",
        periods=5,
        freq="min",
    )

    return pd.DataFrame(
        {
            "timestamp": list(timestamps) + list(timestamps),
            "symbol": [
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
                "NIFTY50",
                "BANKNIFTY",
                "BANKNIFTY",
                "BANKNIFTY",
                "BANKNIFTY",
                "BANKNIFTY",
            ],
            "open": [
                100, 101, 102, 103, 104,
                200, 202, 204, 206, 208,
            ],
            "high": [
                101, 102, 103, 104, 105,
                202, 204, 206, 208, 210,
            ],
            "low": [
                99, 100, 101, 102, 103,
                198, 200, 202, 204, 206,
            ],
            "close": [
                100, 101, 102, 103, 104,
                200, 202, 204, 206, 208,
            ],
            "volume": [
                1000, 1100, 1050, 1200, 900,
                2000, 2200, 2100, 2400, 1800,
            ],
        }
    )


def create_single_symbol_dataframe() -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01 09:15:00",
        periods=5,
        freq="min",
    )

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "symbol": ["NIFTY50"] * 5,
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100, 101, 102, 103, 104],
            "volume": [1000, 1100, 1050, 1200, 900],
        }
    )


def create_constant_price_dataframe() -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-01 09:15:00",
        periods=10,
        freq="min",
    )

    return pd.DataFrame(
        {
            "timestamp": list(timestamps),
            "symbol": ["NIFTY50"] * 5 + ["BANKNIFTY"] * 5,
            "open": [100] * 5 + [200] * 5,
            "high": [101] * 5 + [201] * 5,
            "low": [99] * 5 + [199] * 5,
            "close": [100] * 5 + [200] * 5,
            "volume": [1000] * 10,
        }
    )


# ---------------------------------------------------------------------------
# TEST RUNNER
# ---------------------------------------------------------------------------

def run_test(
    name,
    dataframe,
    expected_exception=None,
    expected_message=None,
    validate_result=None,
):
    print("-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    analyzer = CorrelationAnalyzer()

    try:
        result = analyzer.analyze(dataframe)

        if expected_exception is not None:
            print("RESULT: FAILED")
            print(
                f"Expected exception: "
                f"{expected_exception.__name__}"
            )
            raise AssertionError(
                f"{name}: expected {expected_exception.__name__}"
            )

        if validate_result is not None:
            validate_result(result)

        print("RESULT: PASSED")
        print(result)

    except Exception as exc:
        if expected_exception is None:
            print("RESULT: FAILED")
            raise

        if not isinstance(exc, expected_exception):
            print("RESULT: FAILED")
            print(f"Expected: {expected_exception.__name__}")
            print(f"Actual: {type(exc).__name__}")
            raise AssertionError(
                f"{name}: unexpected exception type"
            ) from exc

        if (
            expected_message is not None
            and expected_message not in str(exc)
        ):
            print("RESULT: FAILED")
            print(f"Expected message containing: {expected_message}")
            print(f"Actual message: {exc}")
            raise AssertionError(
                f"{name}: unexpected exception message"
            ) from exc

        print("RESULT: PASSED")
        print(f"Raised: {type(exc).__name__}")
        print(f"Message: {exc}")


# ---------------------------------------------------------------------------
# RESULT VALIDATORS
# ---------------------------------------------------------------------------

def validate_single_symbol_result(result):
    assert result["symbol_count"] == 1
    assert result["symbols"] == ["NIFTY50"]
    assert result["relationships"]["pair_count"] == 0
    assert result["return_count"] == 4


def validate_valid_result(result):
    assert result["row_count"] == 10
    assert result["symbol_count"] == 2
    assert result["symbols"] == ["BANKNIFTY", "NIFTY50"]
    assert result["correlation_method"] == "pearson"

    matrix = result["correlation_matrix"]

    assert "NIFTY50" in matrix
    assert "BANKNIFTY" in matrix

    assert matrix["NIFTY50"]["NIFTY50"] == 1.0
    assert matrix["BANKNIFTY"]["BANKNIFTY"] == 1.0

    assert result["relationships"]["pair_count"] == 1
    assert result["return_count"] == 4


def validate_constant_price_result(result):
    assert result["symbol_count"] == 2
    assert result["relationships"]["pair_count"] == 1


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("QUANTARA CORRELATION ANALYZER - FAILURE TESTS")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # 1. Empty DataFrame
    # -----------------------------------------------------------------------

    run_test(
        "Empty DataFrame",
        pd.DataFrame(),
        expected_exception=ValueError,
        expected_message="Input DataFrame cannot be empty.",
    )

    # -----------------------------------------------------------------------
    # 2. Non-DataFrame input
    # -----------------------------------------------------------------------

    run_test(
        "Non-DataFrame input",
        ["not", "a", "dataframe"],
        expected_exception=TypeError,
        expected_message="Input must be a pandas DataFrame.",
    )

    # -----------------------------------------------------------------------
    # 3. Missing timestamp
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe().drop(columns=["timestamp"])

    run_test(
        "Missing timestamp column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing: ['timestamp']",
    )

    # -----------------------------------------------------------------------
    # 4. Missing symbol
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe().drop(columns=["symbol"])

    run_test(
        "Missing symbol column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing: ['symbol']",
    )

    # -----------------------------------------------------------------------
    # 5. Missing close
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe().drop(columns=["close"])

    run_test(
        "Missing close column",
        dataframe,
        expected_exception=ValueError,
        expected_message="Required columns are missing: ['close']",
    )

    # -----------------------------------------------------------------------
    # 6. Null timestamp
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "timestamp"] = pd.NaT

    run_test(
        "Null timestamp",
        dataframe,
        expected_exception=ValueError,
        expected_message="Timestamp contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 7. Invalid timestamp
    #
    # IMPORTANT:
    # Convert to object first so pandas allows the invalid string.
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe["timestamp"] = dataframe["timestamp"].astype(object)
    dataframe.loc[0, "timestamp"] = "INVALID"

    run_test(
        "Non-datetime timestamp",
        dataframe,
        expected_exception=ValueError,
        expected_message="Timestamp contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 8. Null symbol
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "symbol"] = None

    run_test(
        "Null symbol",
        dataframe,
        expected_exception=ValueError,
        expected_message="Symbol contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 9. Empty symbol
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "symbol"] = ""

    run_test(
        "Empty symbol",
        dataframe,
        expected_exception=ValueError,
        expected_message="Symbol contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 10. Non-string symbol
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe["symbol"] = dataframe["symbol"].astype(object)
    dataframe.loc[0, "symbol"] = 12345

    run_test(
        "Non-string symbol",
        dataframe,
        expected_exception=ValueError,
        expected_message="Symbol contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 11. Null close
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "close"] = np.nan

    run_test(
        "Null close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 12. Non-numeric close
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe["close"] = dataframe["close"].astype(object)
    dataframe.loc[0, "close"] = "INVALID"

    run_test(
        "Non-numeric close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close contains invalid or null values.",
    )

    # -----------------------------------------------------------------------
    # 13. Zero close
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "close"] = 0

    run_test(
        "Zero close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must be greater than zero.",
    )

    # -----------------------------------------------------------------------
    # 14. Negative close
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()
    dataframe.loc[0, "close"] = -100

    run_test(
        "Negative close price",
        dataframe,
        expected_exception=ValueError,
        expected_message="Close prices must be greater than zero.",
    )

    # -----------------------------------------------------------------------
    # 15. Duplicate timestamp + symbol observations
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()

    duplicate_row = dataframe.iloc[[0]].copy()

    dataframe = pd.concat(
        [dataframe, duplicate_row],
        ignore_index=True,
    )

    run_test(
        "Duplicate timestamp-symbol observation",
        dataframe,
        expected_exception=ValueError,
        expected_message="Duplicate timestamp-symbol observations",
    )

    # -----------------------------------------------------------------------
    # 16. Unsorted timestamps
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()

    dataframe = pd.concat(
        [
            dataframe.iloc[5:6],
            dataframe.iloc[:5],
            dataframe.iloc[6:],
        ],
        ignore_index=True,
    )

    # This is intentionally tested as a valid dataset if the analyzer
    # internally sorts observations by timestamp.
    run_test(
        "Unsorted timestamps",
        dataframe,
        validate_result=validate_valid_result,
    )

    # -----------------------------------------------------------------------
    # 17. Single symbol
    # -----------------------------------------------------------------------

    dataframe = create_single_symbol_dataframe()

    run_test(
        "Single symbol",
        dataframe,
        validate_result=validate_single_symbol_result,
    )

    # -----------------------------------------------------------------------
    # 18. Two symbols with insufficient observations
    # -----------------------------------------------------------------------

    timestamps = pd.date_range(
        "2026-01-01 09:15:00",
        periods=2,
        freq="min",
    )

    dataframe = pd.DataFrame(
        {
            "timestamp": [
                timestamps[0],
                timestamps[0],
            ],
            "symbol": [
                "NIFTY50",
                "BANKNIFTY",
            ],
            "open": [100, 200],
            "high": [101, 201],
            "low": [99, 199],
            "close": [100, 200],
            "volume": [1000, 2000],
        }
    )

    run_test(
        "Insufficient observations for returns",
        dataframe,
        expected_exception=ValueError,
        expected_message="Insufficient",
    )

    # -----------------------------------------------------------------------
    # 19. Constant prices
    # -----------------------------------------------------------------------

    dataframe = create_constant_price_dataframe()

    run_test(
        "Constant prices",
        dataframe,
        validate_result=validate_constant_price_result,
    )

    # -----------------------------------------------------------------------
    # 20. Valid DataFrame
    # -----------------------------------------------------------------------

    dataframe = create_valid_dataframe()

    run_test(
        "Valid DataFrame",
        dataframe,
        validate_result=validate_valid_result,
    )

    print("=" * 60)
    print("ALL CORRELATION ANALYZER FAILURE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

