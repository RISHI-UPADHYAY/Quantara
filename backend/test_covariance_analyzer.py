from pprint import pprint

import pandas as pd

from app.services.analysis.covariance_analyzer import CovarianceAnalyzer


def create_test_dataframe() -> pd.DataFrame:
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
            "close": [
                100,
                101,
                102,
                103,
                104,
                200,
                202,
                204,
                206,
                208,
            ],
        }
    )


def main() -> None:
    print("=" * 30)
    print("QUANTARA COVARIANCE ANALYSIS")
    print("=" * 30)

    dataframe = create_test_dataframe()

    print("\nTEST DATA:")
    print(dataframe)

    analyzer = CovarianceAnalyzer()

    result = analyzer.analyze(dataframe)

    print("\nCOVARIANCE ANALYSIS:")
    pprint(result)

    assert result["row_count"] == 10
    assert result["symbol_count"] == 2
    assert result["symbols"] == [
        "BANKNIFTY",
        "NIFTY50",
    ]

    assert result["return_count"] == 4

    assert result["covariance_method"] == "sample"

    matrix = result["covariance_matrix"]

    assert matrix["BANKNIFTY"]["BANKNIFTY"] is not None
    assert matrix["NIFTY50"]["NIFTY50"] is not None
    assert matrix["BANKNIFTY"]["NIFTY50"] is not None
    assert matrix["NIFTY50"]["BANKNIFTY"] is not None

    assert (
        matrix["BANKNIFTY"]["NIFTY50"]
        == matrix["NIFTY50"]["BANKNIFTY"]
    )

    assert result["relationships"]["pair_count"] == 1

    print("\n" + "=" * 30)
    print("COVARIANCE ANALYZER TEST PASSED")
    print("=" * 30)


if __name__ == "__main__":
    main()