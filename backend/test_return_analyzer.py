from pprint import pprint

from pathlib import Path

from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)
from app.services.analysis.return_analyzer import (
    ReturnAnalyzer,
)


def main():

    file_path = Path(
        "storage/test/nifty_sample.csv"
    )

    normalizer = MarketDataNormalizer()

    dataframe, normalization_report = (
        normalizer.normalize(file_path)
    )

    analyzer = ReturnAnalyzer()

    report = analyzer.analyze(dataframe)

    print()
    print("=" * 30)
    print("QUANTARA RETURN ANALYSIS")
    print("=" * 30)

    print()
    print("RETURN ANALYSIS:")
    pprint(report)


if __name__ == "__main__":
    main()