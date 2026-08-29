from pprint import pprint

import pandas as pd

from app.services.analysis.volume_analyzer import VolumeAnalyzer


def run_test(
    analyzer: VolumeAnalyzer,
    name: str,
    dataframe,
    expected_exception=None,
    expected_message=None,
):
    print()
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
    print("QUANTARA VOLUME ANALYZER - FAILURE TESTS")
    print("=" * 60)

    analyzer = VolumeAnalyzer()

    valid_data = pd.DataFrame(
        {
            "volume": [
                1000,
                1100,
                1050,
                1200,
                900,
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
        expected_message=(
            "Input DataFrame cannot be empty."
        ),
    )

    # ---------------------------------------------------------
    # Non-DataFrame input
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Non-DataFrame input",
        [
            {"volume": 1000},
            {"volume": 1100},
        ],
        expected_exception=TypeError,
        expected_message=(
            "Input must be a pandas DataFrame."
        ),
    )

    # ---------------------------------------------------------
    # Missing volume column
    # ---------------------------------------------------------

    run_test(
        analyzer,
        "Missing volume column",
        pd.DataFrame(
            {
                "close": [
                    26005,
                    26015,
                ]
            }
        ),
        expected_exception=ValueError,
        expected_message=(
            "Required column 'volume' is missing."
        ),
    )

    # ---------------------------------------------------------
    # Null volume
    # ---------------------------------------------------------

    null_volume = valid_data.copy()

    # Convert to object first so pandas does not reject
    # assigning None into an integer column.
    null_volume["volume"] = (
        null_volume["volume"].astype(object)
    )

    null_volume.loc[2, "volume"] = None

    run_test(
        analyzer,
        "Null volume",
        null_volume,
        expected_exception=ValueError,
        expected_message=(
            "Volume contains invalid or null values."
        ),
    )

    # ---------------------------------------------------------
    # Non-numeric volume
    # ---------------------------------------------------------

    non_numeric_volume = valid_data.copy()

    non_numeric_volume["volume"] = (
        non_numeric_volume["volume"].astype(object)
    )

    non_numeric_volume.loc[2, "volume"] = "INVALID"

    run_test(
        analyzer,
        "Non-numeric volume",
        non_numeric_volume,
        expected_exception=ValueError,
        expected_message=(
            "Volume contains invalid or null values."
        ),
    )

    # ---------------------------------------------------------
    # Negative volume
    # ---------------------------------------------------------

    negative_volume = valid_data.copy()

    negative_volume.loc[2, "volume"] = -100

    run_test(
        analyzer,
        "Negative volume",
        negative_volume,
        expected_exception=ValueError,
        expected_message=(
            "Volume values cannot be negative."
        ),
    )

    # ---------------------------------------------------------
    # Zero volume
    # Zero volume is valid and should be reported.
    # ---------------------------------------------------------

    zero_volume = valid_data.copy()

    zero_volume.loc[2, "volume"] = 0

    result = run_test(
        analyzer,
        "Zero volume",
        zero_volume,
    )

    assert result is not None
    assert result["volume_count"] == 5
    assert result["activity"]["zero_volume_count"] == 1
    assert result["activity"]["negative_volume_count"] == 0

    # ---------------------------------------------------------
    # Single-row DataFrame
    # ---------------------------------------------------------

    single_row = pd.DataFrame(
        {
            "volume": [1000],
        }
    )

    result = run_test(
        analyzer,
        "Single-row DataFrame",
        single_row,
    )

    assert result is not None
    assert result["row_count"] == 1
    assert result["volume_count"] == 1

    assert result["statistics"]["mean"] == 1000.0
    assert result["statistics"]["median"] == 1000.0
    assert result["statistics"]["min"] == 1000.0
    assert result["statistics"]["max"] == 1000.0
    assert result["statistics"]["std"] == 0.0
    assert result["statistics"]["total"] == 1000.0

    assert (
        result["activity"]["zero_volume_count"] == 0
    )

    assert (
        result["activity"]["negative_volume_count"] == 0
    )

    assert (
        result["activity"]["coefficient_of_variation"]
        == 0.0
    )

    # ---------------------------------------------------------
    # Valid DataFrame
    # ---------------------------------------------------------

    result = run_test(
        analyzer,
        "Valid DataFrame",
        valid_data,
    )

    assert result is not None

    assert result["volume_column"] == "volume"
    assert result["row_count"] == 5
    assert result["volume_count"] == 5

    statistics = result["statistics"]

    assert statistics["mean"] == 1050.0
    assert statistics["median"] == 1050.0
    assert statistics["min"] == 900.0
    assert statistics["max"] == 1200.0
    assert statistics["total"] == 5250.0

    assert (
        statistics["std"]
        == 111.80339887498948
    )

    activity = result["activity"]

    assert activity["zero_volume_count"] == 0
    assert activity["negative_volume_count"] == 0

    assert (
        activity["coefficient_of_variation"]
        == 0.10647942749998998
    )

    print()
    print("=" * 60)
    print("ALL VOLUME ANALYZER FAILURE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()