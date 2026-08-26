from pprint import pprint

import pandas as pd

from app.services.analysis.drawdown_analyzer import (
    DrawdownAnalyzer,
)


def run_test(
    analyzer: DrawdownAnalyzer,
    name: str,
    dataframe,
    expected_exception: type[Exception] | None = None,
    expected_message: str | None = None,
) -> None:

    print("\n" + "-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    try:
        result = analyzer.analyze(dataframe)

        if expected_exception is not None:
            print("RESULT: FAILED")
            print(
                f"Expected: {expected_exception.__name__}"
            )
            raise AssertionError(
                f"{name}: expected "
                f"{expected_exception.__name__}"
            )

        print("RESULT: PASSED")
        pprint(result)

    except Exception as exc:

        if expected_exception is None:
            print("RESULT: FAILED")
            raise

        if not isinstance(exc, expected_exception):
            print("RESULT: FAILED")
            print(
                f"Expected exception: "
                f"{expected_exception.__name__}"
            )
            print(
                f"Actual exception: "
                f"{type(exc).__name__}"
            )
            raise

        if (
            expected_message is not None
            and expected_message not in str(exc)
        ):
            print("RESULT: FAILED")
            print(
                f"Expected message containing: "
                f"{expected_message}"
            )
            print(
                f"Actual message: {exc}"
            )
            raise AssertionError(
                f"{name}: unexpected exception message"
            )

        print("RESULT: PASSED")
        print(
            f"Raised: {type(exc).__name__}"
        )
        print(f"Message: {exc}")


def main() -> None:

    print("=" * 60)
    print("QUANTARA DRAWDOWN ANALYZER - FAILURE TESTS")
    print("=" * 60)

    analyzer = DrawdownAnalyzer()

    # --------------------------------------------------
    # Base valid data
    # --------------------------------------------------

    valid_dataframe = pd.DataFrame(
        {
            "close": [
                100,
                110,
                105,
                90,
                95,
                115,
            ]
        }
    )

    # --------------------------------------------------
    # Empty DataFrame
    # --------------------------------------------------

    run_test(
        analyzer,
        "Empty DataFrame",
        pd.DataFrame(),
        ValueError,
        "Input DataFrame cannot be empty.",
    )

    # --------------------------------------------------
    # Non-DataFrame input
    # --------------------------------------------------

    run_test(
        analyzer,
        "Non-DataFrame input",
        [100, 110, 105],
        TypeError,
        "Input must be a pandas DataFrame.",
    )

    # --------------------------------------------------
    # Missing close column
    # --------------------------------------------------

    run_test(
        analyzer,
        "Missing close column",
        pd.DataFrame(
            {
                "open": [100, 101, 102],
            }
        ),
        ValueError,
        "Required column 'close' is missing.",
    )

    # --------------------------------------------------
    # Null close price
    # --------------------------------------------------

    null_dataframe = valid_dataframe.copy()

    null_dataframe.loc[2, "close"] = None

    run_test(
        analyzer,
        "Null close price",
        null_dataframe,
        ValueError,
        "Close price contains invalid or null values.",
    )

    # --------------------------------------------------
    # Non-numeric close price
    # --------------------------------------------------

    non_numeric_dataframe = valid_dataframe.copy()

    non_numeric_dataframe["close"] = (
        non_numeric_dataframe["close"]
        .astype(object)
    )

    non_numeric_dataframe.loc[2, "close"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric close price",
        non_numeric_dataframe,
        ValueError,
        "Close price contains invalid or null values.",
    )

    # --------------------------------------------------
    # Zero close price
    # --------------------------------------------------

    zero_price_dataframe = valid_dataframe.copy()

    zero_price_dataframe.loc[2, "close"] = 0

    run_test(
        analyzer,
        "Zero close price",
        zero_price_dataframe,
        ValueError,
        "Close prices must be greater than zero.",
    )

    # --------------------------------------------------
    # Negative close price
    # --------------------------------------------------

    negative_price_dataframe = valid_dataframe.copy()

    negative_price_dataframe.loc[2, "close"] = -10

    run_test(
        analyzer,
        "Negative close price",
        negative_price_dataframe,
        ValueError,
        "Close prices must be greater than zero.",
    )

    # --------------------------------------------------
    # Single-row DataFrame
    # --------------------------------------------------

    single_row_dataframe = pd.DataFrame(
        {
            "close": [100],
        }
    )

    print("\n" + "-" * 60)
    print("TEST: Single-row DataFrame")
    print("-" * 60)

    result = analyzer.analyze(
        single_row_dataframe
    )

    print("RESULT: PASSED")
    pprint(result)

    assert result["row_count"] == 1

    assert result["drawdown"]["maximum"] == 0.0
    assert (
        result["drawdown"]["maximum_percentage"]
        == 0.0
    )
    assert (
        result["drawdown"]["maximum_duration"]
        == 0
    )
    assert result["drawdown"]["recovered"] is True
    assert result["drawdown"]["recovery_index"] == 0
    assert result["drawdown"]["recovery_duration"] == 0

    assert result["equity"]["initial"] == 100.0
    assert result["equity"]["final"] == 100.0
    assert result["equity"]["peak"] == 100.0

    # --------------------------------------------------
    # Drawdown with recovery
    # --------------------------------------------------

    recovery_dataframe = pd.DataFrame(
        {
            "close": [
                100,
                110,
                90,
                105,
                110,
                115,
            ]
        }
    )

    print("\n" + "-" * 60)
    print("TEST: Drawdown with recovery")
    print("-" * 60)

    result = analyzer.analyze(
        recovery_dataframe
    )

    print("RESULT: PASSED")
    pprint(result)

    assert result["drawdown"]["maximum"] < 0.0
    assert (
        result["drawdown"]["maximum_percentage"]
        < 0.0
    )

    assert result["drawdown"]["recovered"] is True
    assert (
        result["drawdown"]["recovery_index"]
        is not None
    )

    assert (
        result["drawdown"]["recovery_duration"]
        is not None
    )

    # --------------------------------------------------
    # Drawdown without recovery
    # --------------------------------------------------

    no_recovery_dataframe = pd.DataFrame(
        {
            "close": [
                100,
                110,
                90,
                95,
                100,
            ]
        }
    )

    print("\n" + "-" * 60)
    print("TEST: Drawdown without recovery")
    print("-" * 60)

    result = analyzer.analyze(
        no_recovery_dataframe
    )

    print("RESULT: PASSED")
    pprint(result)

    assert result["drawdown"]["maximum"] < 0.0
    assert (
        result["drawdown"]["recovered"]
        is False
    )

    assert (
        result["drawdown"]["recovery_index"]
        is None
    )

    assert (
        result["drawdown"]["recovery_duration"]
        is None
    )

    # --------------------------------------------------
    # Valid DataFrame
    # --------------------------------------------------

    run_test(
        analyzer,
        "Valid DataFrame",
        valid_dataframe,
    )

    print("\n" + "=" * 60)
    print(
        "ALL DRAWDOWN ANALYZER FAILURE TESTS PASSED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()