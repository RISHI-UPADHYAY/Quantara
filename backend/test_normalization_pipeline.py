from pathlib import Path
from pprint import pprint

from app.services.normalization.normalization_pipeline import (
    NormalizationPipeline,
)


def main():

    file_path = Path(
        "storage/profiling/test/nifty_sample.csv"
    )

    pipeline = NormalizationPipeline()

    result = pipeline.process(
        file_path
    )

    print()
    print("=" * 30)
    print("QUANTARA NORMALIZATION PIPELINE")
    print("=" * 30)

    print()
    print("STATUS:")
    print(result["status"])

    print()
    print("NORMALIZED DTYPES:")
    pprint(
        {
            column: str(dtype)
            for column, dtype
            in result["data"].dtypes.items()
        }
    )

    print()
    print("NORMALIZED DATA:")
    print(result["data"])

    print()
    print("NORMALIZATION:")
    pprint(result["normalization"])

    print()
    print("VALIDATION:")
    pprint(result["validation"])


if __name__ == "__main__":
    main()