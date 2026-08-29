
from pathlib import Path
from pprint import pprint

from app.services.analysis.volatility_analyzer import (
    VolatilityAnalyzer,
)
from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)


def main():

    print()
    print("=" * 30)
    print("QUANTARA VOLATILITY ANALYSIS")
    print("=" * 30)

    # ---------------------------------------------------------
    # Load and normalize market data
    # ---------------------------------------------------------

    file_path = Path(
        "storage/test/nifty_sample.csv"
    )

    normalizer = MarketDataNormalizer()

    dataframe, normalization_report = (
        normalizer.normalize(file_path)
    )

    # ---------------------------------------------------------
    # Run volatility analysis
    # ---------------------------------------------------------

    analyzer = VolatilityAnalyzer()

    report = analyzer.analyze(
        dataframe
    )

    # ---------------------------------------------------------
    # Display results
    # ---------------------------------------------------------

    print()
    print("NORMALIZED DTYPES:")
    pprint(
        {
            column: str(dtype)
            for column, dtype
            in dataframe.dtypes.items()
        }
    )

    print()
    print("VOLATILITY ANALYSIS:")
    pprint(report)

    # ---------------------------------------------------------
    # Basic assertions
    # ---------------------------------------------------------

    assert report["row_count"] == 5

    assert report["price_column"] == "close"

    assert report["return_count"] == 4

    assert report["periods_per_year"] == 252

    assert (
        report["volatility"]["periodic"] >= 0
    )

    assert (
        report["volatility"]["annualized"] >= 0
    )

    assert (
        report["volatility"]["annualized"]
        >= report["volatility"]["periodic"]
    )

    assert (
        report["return_statistics"]["min"]
        <= report["return_statistics"]["max"]
    )

    print()
    print("=" * 30)
    print("VOLATILITY ANALYZER TEST PASSED")
    print("=" * 30)


if __name__ == "__main__":
    main()

