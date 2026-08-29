
from pprint import pprint

import pandas as pd

from app.services.analysis.volatility_analyzer import (
    VolatilityAnalyzer,
)


def run_test(
    analyzer: VolatilityAnalyzer,
    name: str,
    dataframe,
    expected_exception=None,
    expected_message=None,
    periods_per_year=252,
):
    print()
    print("-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    try:
        result = analyzer.analyze(
            dataframe,
            periods_per_year=periods_per_year,
        )

        if expected_exception is not None:
            print("RESULT: FAILED")
            print(
                f"Expected {expected_exception.__name__}, "
                "but no exception was raised."
            )
            raise AssertionError(
                f"{name}: expected "
                f"{expected_exception.__name__}"
            )

        print("RESULT: PASSED")
        pprint(result)

        return result

    except Exception as exc:
        if expected_exception is None:
            print("RESULT: FAILED")
            raise

        if not isinstance(exc, expected_exception):
            print("RESULT: FAILED")
            print(
                f"Expected: {expected_exception.__name__}"
            )
            print(
                f"Raised:   {type(exc).__name__}"
            )
            print(f"Message:  {exc}")
            raise AssertionError(
                f"{name}: unexpected exception type"
            ) from exc

        if (
            expected_message is not None
            and expected_message not in str(exc)
        ):
            print("RESULT: FAILED")
            print(
                f"Expected message containing: "
                f"{expected_message}"
            )
            print(f"Actual message: {exc}")
            raise AssertionError(
                f"{name}: unexpected exception message"
            ) from exc

        print("RESULT: PASSED")
        print(f"Raised: {type(exc).__name__}")
        print(f"Message: {exc}")

        return None


def main():
    print()
    print("=" * 60)
    print("QUANTARA VOLATILITY ANALYZER - FAILURE TESTS")
    print("=" * 60)

    analyzer = VolatilityAnalyzer()

    valid_data = pd.DataFrame(
        {
            "close": [
                26005,
                26015,
                26020,
                26025,
                26020,
            ]
        }
    )

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
        [
            {"close": 26005},
            {"close": 26015},
        ],
        expected_exception=TypeError,
        expected_message="Input must be a pandas DataFrame.",
    )

    # ---------------------------------------------------------
    # Missing close column
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Missing close column",
        pd.DataFrame(
            {
                "open": [26000, 26005],
                "high": [26010, 26020],
            }
        ),
        expected_exception=ValueError,
        expected_message="Required column 'close' is missing.",
    )

    # ---------------------------------------------------------
    # Null close price
    # ---------------------------------------------------------

    null_close = valid_data.copy()
    null_close.loc[2, "close"] = None

    run_test(
        analyzer,
        "Null close price",
        null_close,
        expected_exception=ValueError,
        expected_message=(
            "Close price contains invalid or null values."
        ),
    )

    # ---------------------------------------------------------
    # Non-numeric close price
    # ---------------------------------------------------------

    non_numeric_close = valid_data.copy()
    non_numeric_close["close"] = (
        non_numeric_close["close"]
        .astype(object)
    )
    non_numeric_close.loc[2, "close"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric close price",
        non_numeric_close,
        expected_exception=ValueError,
        expected_message=(
            "Close price contains invalid or null values."
        ),
    )

    # ---------------------------------------------------------
    # Zero close price
    # ---------------------------------------------------------

    zero_close = valid_data.copy()
    zero_close.loc[2, "close"] = 0

    run_test(
        analyzer,
        "Zero close price",
        zero_close,
        expected_exception=ValueError,
        expected_message=(
            "Close prices must be greater than zero."
        ),
    )

    # ---------------------------------------------------------
    # Negative close price
    # ---------------------------------------------------------

    negative_close = valid_data.copy()
    negative_close.loc[2, "close"] = -100

    run_test(
        analyzer,
        "Negative close price",
        negative_close,
        expected_exception=ValueError,
        expected_message=(
            "Close prices must be greater than zero."
        ),
    )

    # ---------------------------------------------------------
    # Invalid periods_per_year: zero
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Zero periods_per_year",
        valid_data,
        expected_exception=ValueError,
        expected_message=(
            "periods_per_year must be greater than zero."
        ),
        periods_per_year=0,
    )

    # ---------------------------------------------------------
    # Invalid periods_per_year: negative
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Negative periods_per_year",
        valid_data,
        expected_exception=ValueError,
        expected_message=(
            "periods_per_year must be greater than zero."
        ),
        periods_per_year=-252,
    )

    # ---------------------------------------------------------
    # Invalid periods_per_year: non-integer
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Non-integer periods_per_year",
        valid_data,
        expected_exception=TypeError,
        expected_message=(
            "periods_per_year must be an integer."
        ),
        periods_per_year=252.5,
    )

    # ---------------------------------------------------------
    # Single-row DataFrame
    # ---------------------------------------------------------

    single_row = pd.DataFrame(
        {
            "close": [26005],
        }
    )

    result = run_test(
        analyzer,
        "Single-row DataFrame",
        single_row,
    )

    assert result is not None
    assert result["row_count"] == 1
    assert result["return_count"] == 0
    assert result["volatility"]["periodic"] == 0.0
    assert result["volatility"]["annualized"] == 0.0

    # ---------------------------------------------------------
    # Valid DataFrame
    # ---------------------------------------------------------

    result = run_test(
        analyzer,
        "Valid DataFrame",
        valid_data,
    )

    assert result is not None

    assert result["row_count"] == 5
    assert result["return_count"] == 4
    assert result["price_column"] == "close"
    assert result["periods_per_year"] == 252

    assert (
        result["volatility"]["periodic"] >= 0
    )

    assert (
        result["volatility"]["annualized"] >= 0
    )

    # ---------------------------------------------------------
    # Custom annualization
    # ---------------------------------------------------------

    result_252 = analyzer.analyze(
        valid_data,
        periods_per_year=252,
    )

    result_365 = analyzer.analyze(
        valid_data,
        periods_per_year=365,
    )

    assert (
        result_365["volatility"]["annualized"]
        > result_252["volatility"]["annualized"]
    )

    print()
    print("=" * 60)
    print("ALL VOLATILITY ANALYZER FAILURE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

