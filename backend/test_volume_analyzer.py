from pathlib import Path
from pprint import pprint

from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)
from app.services.analysis.volume_analyzer import VolumeAnalyzer


def main() -> None:
    base_dir = Path(__file__).resolve().parent

    file_path = (
        base_dir
        / "storage"
        / "test"
        / "nifty_sample.csv"
    )

    normalizer = MarketDataNormalizer()
    analyzer = VolumeAnalyzer()

    dataframe, normalization_report = (
        normalizer.normalize(file_path)
    )

    print("=" * 30)
    print("QUANTARA VOLUME ANALYSIS")
    print("=" * 30)

    print("\nNORMALIZED DTYPES:")
    pprint(
        {
            column: str(dtype)
            for column, dtype in dataframe.dtypes.items()
        }
    )

    print("\nNORMALIZED DATA:")
    print(dataframe)

    result = analyzer.analyze(dataframe)

    print("\nVOLUME ANALYSIS:")
    pprint(result)

    assert result["volume_column"] == "volume"
    assert result["row_count"] == 5
    assert result["volume_count"] == 5

    statistics = result["statistics"]

    assert statistics["mean"] == 1050.0
    assert statistics["median"] == 1050.0
    assert statistics["min"] == 900.0
    assert statistics["max"] == 1200.0
    assert statistics["total"] == 5250.0

    activity = result["activity"]

    assert activity["zero_volume_count"] == 0
    assert activity["negative_volume_count"] == 0

    print("\n" + "=" * 30)
    print("VOLUME ANALYZER TEST PASSED")
    print("=" * 30)


if __name__ == "__main__":
    main()