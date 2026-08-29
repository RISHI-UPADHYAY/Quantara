from pprint import pprint

import pandas as pd

from app.services.normalization.normalization_validator import (
NormalizationValidator,
)

def build_base_dataframe() -> pd.DataFrame:
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
"symbol": pd.Series(
[
"NIFTY50",
"NIFTY50",
"NIFTY50",
"NIFTY50",
"NIFTY50",
],
dtype="string",
),
"open": [26000, 26005, 26010, 26015, 26020],
"high": [26010, 26020, 26025, 26030, 26025],
"low": [25990, 26000, 26005, 26010, 26015],
"close": [26005, 26015, 26020, 26025, 26020],
"volume": [1000, 1100, 1050, 1200, 900],
}
)

def main() -> None:
print("=" * 60)
print("QUANTARA NORMALIZATION VALIDATOR - INVALID DATA TESTS")
print("=" * 60)

```
validator = NormalizationValidator()

base_dataframe = build_base_dataframe()

test_cases = []

# ---------------------------------------------------------
# CASE 1: Missing required column
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe = dataframe.drop(columns=["volume"])

test_cases.append(
    (
        "Missing required column: volume",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 2: Null value in required field
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe["close"] = dataframe["close"].astype("object")
dataframe.loc[0, "close"] = None

test_cases.append(
    (
        "Null value in required field: close",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 3: Invalid numeric value
#
# Convert the column to object first because pandas will
# otherwise reject assigning a string into an int64 column.
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe["open"] = dataframe["open"].astype("object")
dataframe.loc[0, "open"] = "INVALID"

test_cases.append(
    (
        "Invalid numeric value in open",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 4: Duplicate timestamp
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[1, "timestamp"] = dataframe.loc[0, "timestamp"]

test_cases.append(
    (
        "Duplicate timestamp",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 5: Out-of-order timestamp
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[2, "timestamp"] = pd.Timestamp(
    "2026-01-01 09:14:00"
)

test_cases.append(
    (
        "Out-of-order timestamp",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 6: Empty symbol
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe["symbol"] = dataframe["symbol"].astype("object")
dataframe.loc[0, "symbol"] = ""

test_cases.append(
    (
        "Empty symbol",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 7: Negative price
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "open"] = -100

test_cases.append(
    (
        "Negative open price",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 8: Zero price
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "close"] = 0

test_cases.append(
    (
        "Zero close price",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 9: Invalid OHLC relationship
#
# high must be >= open, close, low
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "high"] = 25000

test_cases.append(
    (
        "Invalid OHLC relationship",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 10: Low greater than high
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "low"] = 27000

test_cases.append(
    (
        "Low greater than high",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 11: Negative volume
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "volume"] = -500

test_cases.append(
    (
        "Negative volume",
        dataframe,
    )
)

# ---------------------------------------------------------
# CASE 12: Zero volume
# ---------------------------------------------------------
dataframe = base_dataframe.copy()
dataframe.loc[0, "volume"] = 0

test_cases.append(
    (
        "Zero volume",
        dataframe,
    )
)

# ---------------------------------------------------------
# Execute test cases
# ---------------------------------------------------------
passed = 0
failed = 0

for index, (name, dataframe) in enumerate(
    test_cases,
    start=1,
):
    print()
    print("-" * 60)
    print(f"TEST {index}: {name}")
    print("-" * 60)

    try:
        report = validator.validate(dataframe)

        pprint(report)

        if report["valid"]:
            print("RESULT: FAIL")
            print(
                "Expected validation failure, "
                "but validator returned valid=True."
            )
            failed += 1

        else:
            print("RESULT: PASS")
            print(
                f"Errors: {report['error_count']}, "
                f"Warnings: {report['warning_count']}"
            )
            passed += 1

    except Exception as exc:
        print("RESULT: FAIL")
        print(f"Validator raised unexpected exception: {exc}")
        failed += 1

# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------
print()
print("=" * 60)
print("INVALID DATA TEST SUMMARY")
print("=" * 60)

print(f"Total tests : {len(test_cases)}")
print(f"Passed      : {passed}")
print(f"Failed      : {failed}")

if failed == 0:
    print()
    print("ALL INVALID DATA TESTS PASSED.")
else:
    print()
    print("SOME INVALID DATA TESTS FAILED.")

    raise AssertionError(
        f"{failed} invalid-data test(s) failed."
    )
```

if name == "main":
    main()
