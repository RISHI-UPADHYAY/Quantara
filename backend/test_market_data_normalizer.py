from pathlib import Path
from pprint import pprint

from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)
from app.services.normalization.normalization_report import (
    NormalizationReportBuilder,
)


BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = (
    BASE_DIR
    / "storage"
    / "profiling"
    / "test"
    / "nifty_sample.csv"
)


def main() -> None:

    normalizer = MarketDataNormalizer()

    dataframe, report = normalizer.normalize(
        CSV_PATH
    )

    report_builder = (
        NormalizationReportBuilder()
    )

    normalization_report = (
        report_builder.build(report)
    )

    print()
    print("==============================")
    print("QUANTARA NORMALIZATION")
    print("==============================")

    print()
    print("NORMALIZED COLUMNS:")
    print(
        list(dataframe.columns)
    )

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
    print("NORMALIZED DATA:")
    print(dataframe)

    print()
    print("NORMALIZATION REPORT:")
    pprint(normalization_report)


if __name__ == "__main__":
    main()