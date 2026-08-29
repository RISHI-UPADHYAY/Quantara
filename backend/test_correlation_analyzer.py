from pprint import pprint

import pandas as pd

from app.services.analysis.correlation_analyzer import (
    CorrelationAnalyzer,
)


def create_test_data() -> pd.DataFrame:
    """
    Create deterministic multi-symbol market data.

    BANKNIFTY is intentionally constructed as a scaled copy
    of NIFTY50 so that their returns have perfect positive
    correlation.
    """

    timestamps = pd.date_range(
        "2026-01-01 09:15:00",
        periods=5,
        freq="min",
    )

    nifty50 = pd.DataFrame(
        {
            "timestamp": timestamps,
            "symbol": "NIFTY50",
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100, 101, 102, 103, 104],
            "volume": [1000, 1100, 1050, 1200, 900],
        }
    )

    banknifty = nifty50.copy()

    banknifty["symbol"] = "BANKNIFTY"

    banknifty["open"] *= 2
    banknifty["high"] *= 2
    banknifty["low"] *= 2
    banknifty["close"] *= 2
    banknifty["volume"] *= 2

    return pd.concat(
        [nifty50, banknifty],
        ignore_index=True,
    )


def main() -> None:
    print("==============================")
    print("QUANTARA CORRELATION ANALYSIS")
    print("==============================")

    dataframe = create_test_data()

    print("\nTEST DATA:")
    print(dataframe)

    print("\nDTYPES:")
    print(dataframe.dtypes.astype(str).to_dict())

    analyzer = CorrelationAnalyzer()

    result = analyzer.analyze(dataframe)

    print("\nCORRELATION ANALYSIS:")
    pprint(result)

    # ---------------------------------------------------------
    # BASIC STRUCTURE
    # ---------------------------------------------------------

    assert result["row_count"] == 10

    assert result["symbol_count"] == 2

    assert set(result["symbols"]) == {
        "NIFTY50",
        "BANKNIFTY",
    }

    assert result["correlation_method"] == "pearson"

    assert result["return_count"] > 0

    # ---------------------------------------------------------
    # CORRELATION MATRIX
    # ---------------------------------------------------------

    matrix = result["correlation_matrix"]

    assert "NIFTY50" in matrix
    assert "BANKNIFTY" in matrix

    assert "NIFTY50" in matrix["NIFTY50"]
    assert "BANKNIFTY" in matrix["BANKNIFTY"]

    # Diagonal correlations must be 1.
    assert matrix["NIFTY50"]["NIFTY50"] == 1.0
    assert matrix["BANKNIFTY"]["BANKNIFTY"] == 1.0

    # BANKNIFTY is a scaled copy of NIFTY50.
    correlation = matrix["NIFTY50"]["BANKNIFTY"]

    assert abs(correlation - 1.0) < 1e-12

    # Matrix must be symmetric.
    reverse_correlation = (
        matrix["BANKNIFTY"]["NIFTY50"]
    )

    assert abs(
        correlation - reverse_correlation
    ) < 1e-12

    # ---------------------------------------------------------
    # RELATIONSHIP ANALYSIS
    # ---------------------------------------------------------

    relationships = result["relationships"]

    assert relationships["pair_count"] == 1

    strongest_positive = (
        relationships["strongest_positive"]
    )

    assert strongest_positive is not None

    assert {
        strongest_positive["symbol_a"],
        strongest_positive["symbol_b"],
    } == {
        "NIFTY50",
        "BANKNIFTY",
    }

    assert abs(
        strongest_positive["correlation"] - 1.0
    ) < 1e-12

    strongest_negative = (
        relationships["strongest_negative"]
    )

    assert strongest_negative is not None

    assert {
        strongest_negative["symbol_a"],
        strongest_negative["symbol_b"],
    } == {
        "NIFTY50",
        "BANKNIFTY",
    }

    # ---------------------------------------------------------
    # SINGLE SYMBOL TEST
    # ---------------------------------------------------------

    single_symbol_data = dataframe[
        dataframe["symbol"] == "NIFTY50"
    ].copy()

    single_result = analyzer.analyze(
        single_symbol_data
    )

    assert single_result["symbol_count"] == 1

    assert single_result["relationships"][
        "pair_count"
    ] == 0

    assert single_result["relationships"][
        "strongest_positive"
    ] is None

    assert single_result["relationships"][
        "strongest_negative"
    ] is None

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    print("\n==============================")
    print("CORRELATION ANALYZER TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()