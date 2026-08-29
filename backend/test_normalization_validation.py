from pathlib import Path
from pprint import pprint

from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)
from app.services.normalization.normalization_validator import (
    NormalizationValidator,
)


def main():
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
            f"Test dataset not found: {sample_file}"
        )

    normalizer = MarketDataNormalizer()
    validator = NormalizationValidator()

    dataframe, normalization_report = normalizer.normalize(
        sample_file
    )

    validation_report = validator.validate(
        dataframe=dataframe
    )

    print()
    print("==============================")
    print("QUANTARA NORMALIZATION VALIDATION")
    print("==============================")

    print("\nNORMALIZED DTYPES:")
    pprint(
        {
            column: str(dtype)
            for column, dtype in dataframe.dtypes.items()
        }
    )

    print("\nNORMALIZED DATA:")
    print(dataframe)

    print("\nNORMALIZATION REPORT:")
    pprint(normalization_report)

    print("\nVALIDATION REPORT:")
    pprint(validation_report)


if __name__ == "__main__":
    main()