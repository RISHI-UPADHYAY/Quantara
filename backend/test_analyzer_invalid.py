
from pprint import pprint

import pandas as pd

from app.services.analysis.return_analyzer import ReturnAnalyzer


def run_test(
    name: str,
    dataframe,
    expected_exception: type[Exception] | None = None,
):
    print()
    print("-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    analyzer = ReturnAnalyzer()

    try:
        report = analyzer.analyze(dataframe)

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
        pprint(report)

    except Exception as exc:
        if expected_exception is None:
            print("RESULT: FAILED")
            raise

        if not isinstance(exc, expected_exception):
            print("RESULT: FAILED")
            print(
                f"Expected {expected_exception.__name__}, "
                f"got {type(exc).__name__}: {exc}"
            )
            raise

        print("RESULT: PASSED")
        print(f"Raised: {type(exc).__name__}")
        print(f"Message: {exc}")


def main():

    print()
    print("=" * 60)
    print("QUANTARA RETURN ANALYZER - FAILURE TESTS")
    print("=" * 60)

    valid_dataframe = pd.DataFrame(
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
            "close": [
                26005,
                26015,
                26020,
                26025,
                26020,
            ],
        }
    )

    # ---------------------------------------------------------
    # 1. Empty DataFrame
    # ---------------------------------------------------------

    run_test(
        "Empty DataFrame",
        pd.DataFrame(),
        ValueError,
    )

    # ---------------------------------------------------------
    # 2. Invalid input type
    # ---------------------------------------------------------

    run_test(
        "Non-DataFrame input",
        [26005, 26015, 26020],
        TypeError,
    )

    # ---------------------------------------------------------
    # 3. Missing close column
    # ---------------------------------------------------------

    missing_close = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 09:15:00",
                "2026-01-01 09:16:00",
            ],
            "open": [26000, 26005],
        }
    )

    run_test(
        "Missing close column",
        missing_close,
        ValueError,
    )

    # ---------------------------------------------------------
    # 4. Null close value
    # ---------------------------------------------------------

    null_close = valid_dataframe.copy()

    null_close.loc[2, "close"] = None

    run_test(
        "Null close price",
        null_close,
        ValueError,
    )

    # ---------------------------------------------------------
    # 5. Invalid numeric close value
    # ---------------------------------------------------------

    invalid_numeric = valid_dataframe.copy()

    invalid_numeric["close"] = (
        invalid_numeric["close"]
        .astype(object)
    )

    invalid_numeric.loc[2, "close"] = "INVALID"

    run_test(
        "Non-numeric close price",
        invalid_numeric,
        ValueError,
    )

    # ---------------------------------------------------------
    # 6. Zero close price
    # ---------------------------------------------------------

    zero_price = valid_dataframe.copy()

    zero_price.loc[2, "close"] = 0

    run_test(
        "Zero close price",
        zero_price,
        ValueError,
    )

    # ---------------------------------------------------------
    # 7. Negative close price
    # ---------------------------------------------------------

    negative_price = valid_dataframe.copy()

    negative_price.loc[2, "close"] = -26020

    run_test(
        "Negative close price",
        negative_price,
        ValueError,
    )

    # ---------------------------------------------------------
    # 8. Single-row DataFrame
    # ---------------------------------------------------------

    single_row = pd.DataFrame(
        {
            "close": [26005],
        }
    )

    run_test(
        "Single-row DataFrame",
        single_row,
    )

    # ---------------------------------------------------------
    # 9. Valid DataFrame
    # ---------------------------------------------------------

    run_test(
        "Valid DataFrame",
        valid_dataframe,
    )

    print()
    print("=" * 60)
    print("ALL RETURN ANALYZER FAILURE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

