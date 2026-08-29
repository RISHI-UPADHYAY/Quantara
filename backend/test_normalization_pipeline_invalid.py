from pathlib import Path
from pprint import pprint
import tempfile

import pandas as pd

from app.services.normalization.normalization_pipeline import (
    NormalizationPipeline,
)


BASE_DIR = Path(__file__).resolve().parent
VALID_FILE = (
    BASE_DIR
    / "storage"
    / "profiling"
    / "test"
    / "nifty_sample.csv"
)


def run_case(
    pipeline: NormalizationPipeline,
    name: str,
    dataframe: pd.DataFrame,
):
    print()
    print("-" * 60)
    print(f"TEST: {name}")
    print("-" * 60)

    with tempfile.NamedTemporaryFile(
        suffix=".csv",
        delete=False,
    ) as temporary_file:

        file_path = Path(
            temporary_file.name
        )

    try:
        dataframe.to_csv(
            file_path,
            index=False,
        )

        result = pipeline.process(
            file_path
        )

        print("STATUS:")
        print(result["status"])

        print()
        print("VALIDATION:")
        pprint(result["validation"])

        return result

    finally:
        file_path.unlink(
            missing_ok=True
        )


def main():

    pipeline = NormalizationPipeline()

    valid_dataframe = pd.read_csv(
        VALID_FILE
    )

    print()
    print("=" * 60)
    print("QUANTARA NORMALIZATION PIPELINE - FAILURE TESTS")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Missing required column
    # ---------------------------------------------------------

    dataframe = valid_dataframe.drop(
        columns=["close"]
    )

    result = run_case(
        pipeline,
        "Missing required column",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 2. Invalid numeric value
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe["open"] = dataframe["open"].astype(
        "object"
    )

    dataframe.loc[0, "open"] = "INVALID"

    result = run_case(
        pipeline,
        "Invalid numeric value",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 3. Invalid timestamp
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe["timestamp"] = dataframe[
        "timestamp"
    ].astype("object")

    dataframe.loc[0, "timestamp"] = (
        "NOT_A_TIMESTAMP"
    )

    result = run_case(
        pipeline,
        "Invalid timestamp",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 4. Duplicate timestamp
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[1, "timestamp"] = (
        dataframe.loc[0, "timestamp"]
    )

    result = run_case(
        pipeline,
        "Duplicate timestamp",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 5. Out-of-order timestamp
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "timestamp"], dataframe.loc[
        1, "timestamp"
    ] = (
        dataframe.loc[1, "timestamp"],
        dataframe.loc[0, "timestamp"],
    )

    result = run_case(
        pipeline,
        "Out-of-order timestamps",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 6. Empty symbol
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe["symbol"] = dataframe[
        "symbol"
    ].astype("object")

    dataframe.loc[0, "symbol"] = ""

    result = run_case(
        pipeline,
        "Empty symbol",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 7. Negative price
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "open"] = -100

    result = run_case(
        pipeline,
        "Negative price",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 8. Zero price
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "open"] = 0

    result = run_case(
        pipeline,
        "Zero price",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 9. Invalid OHLC relationship
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "high"] = 25900

    result = run_case(
        pipeline,
        "Invalid OHLC relationship",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 10. Negative volume
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "volume"] = -500

    result = run_case(
        pipeline,
        "Negative volume",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 11. Zero volume
    # ---------------------------------------------------------

    dataframe = valid_dataframe.copy()

    dataframe.loc[0, "volume"] = 0

    result = run_case(
        pipeline,
        "Zero volume",
        dataframe,
    )

    assert result["status"] == "invalid"
    assert result["validation"]["valid"] is False

    # ---------------------------------------------------------
    # 12. Missing file
    # ---------------------------------------------------------

    print()
    print("-" * 60)
    print("TEST: Missing file")
    print("-" * 60)

    missing_file = (
        BASE_DIR
        / "storage"
        / "profiling"
        / "test"
        / "does_not_exist.csv"
    )

    try:
        pipeline.process(
            missing_file
        )

        raise AssertionError(
            "Expected FileNotFoundError"
        )

    except FileNotFoundError as error:

        print(
            f"PASS: {error}"
        )

    # ---------------------------------------------------------
    # 13. Directory instead of file
    # ---------------------------------------------------------

    print()
    print("-" * 60)
    print("TEST: Directory instead of file")
    print("-" * 60)

    directory_path = (
        BASE_DIR
        / "storage"
        / "profiling"
        / "test"
    )

    try:
        pipeline.process(
            directory_path
        )

        raise AssertionError(
            "Expected ValueError"
        )

    except ValueError as error:

        print(
            f"PASS: {error}"
        )

    # ---------------------------------------------------------
    # 14. Non-CSV file
    # ---------------------------------------------------------

    print()
    print("-" * 60)
    print("TEST: Non-CSV file")
    print("-" * 60)

    with tempfile.NamedTemporaryFile(
        suffix=".txt",
        delete=False,
    ) as temporary_file:

        non_csv_path = Path(
            temporary_file.name
        )

    try:
        non_csv_path.write_text(
            "not a csv file"
        )

        try:
            pipeline.process(
                non_csv_path
            )

            raise AssertionError(
                "Expected ValueError"
            )

        except ValueError as error:

            print(
                f"PASS: {error}"
            )

    finally:
        non_csv_path.unlink(
            missing_ok=True
        )

    print()
    print("=" * 60)
    print("ALL FAILURE-PATH TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()