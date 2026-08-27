from pathlib import Path
from pprint import pprint

from app.services.normalization.market_data_normalizer import MarketDataNormalizer
from app.services.analysis.price_range_analyzer import PriceRangeAnalyzer


def main():
    print("==============================")
    print("QUANTARA PRICE RANGE ANALYSIS")
    print("==============================")

    base_dir = Path(__file__).resolve().parent
    sample_file = (
        base_dir
        / "storage"
        / "profiling"
        / "test"
        / "nifty_sample.csv"
    )

    if not sample_file.exists():
        raise FileNotFoundError(
            f"Sample file not found: {sample_file}"
        )

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    normalizer = MarketDataNormalizer()

    dataframe, normalization_report = normalizer.normalize(
        sample_file
    )

    print("\nNORMALIZED DTYPES:")
    print(dataframe.dtypes.astype(str).to_dict())

    print("\nNORMALIZED DATA:")
    print(dataframe)

    # ---------------------------------------------------------
    # PRICE RANGE ANALYSIS
    # ---------------------------------------------------------

    analyzer = PriceRangeAnalyzer()

    result = analyzer.analyze(dataframe)

    print("\nPRICE RANGE ANALYSIS:")
    pprint(result)

    # ---------------------------------------------------------
    # STRUCTURAL ASSERTIONS
    # ---------------------------------------------------------

    assert result["row_count"] == 5

    assert result["price_columns"] == {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
    }

    # ---------------------------------------------------------
    # EXPECTED ABSOLUTE RANGES
    #
    # 26010 - 25990 = 20
    # 26020 - 26000 = 20
    # 26025 - 26005 = 20
    # 26030 - 26010 = 20
    # 26025 - 26015 = 10
    # ---------------------------------------------------------

    expected_ranges = [
        20.0,
        20.0,
        20.0,
        20.0,
        10.0,
    ]

    assert len(expected_ranges) == result["row_count"]

    assert result["range_statistics"]["mean"] == 18.0
    assert result["range_statistics"]["median"] == 20.0
    assert result["range_statistics"]["min"] == 10.0
    assert result["range_statistics"]["max"] == 20.0

    # ---------------------------------------------------------
    # RANGE PERCENTAGE
    # ---------------------------------------------------------

    expected_range_percentages = [
        20 / 26005,
        20 / 26015,
        20 / 26020,
        20 / 26025,
        10 / 26020,
    ]

    expected_mean_percentage = (
        sum(expected_range_percentages)
        / len(expected_range_percentages)
    )

    actual_mean_percentage = (
        result["range_percentage_statistics"]["mean"]
    )

    assert abs(
        actual_mean_percentage - expected_mean_percentage
    ) < 1e-12

    # ---------------------------------------------------------
    # ACTIVITY
    # ---------------------------------------------------------

    assert result["activity"]["zero_range_count"] == 0
    assert result["activity"]["average_range"] == 18.0
    assert result["activity"]["maximum_range"] == 20.0

    print("\n==============================")
    print("PRICE RANGE ANALYZER TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()