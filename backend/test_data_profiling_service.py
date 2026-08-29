from pathlib import Path
from pprint import pprint

from app.services.profiling.data_profiling_service import (
    DataProfilingService,
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

    profiler = DataProfilingService()

    result = profiler.profile(CSV_PATH)

    print()
    print("==============================")
    print("QUANTARA DATA PROFILING")
    print("==============================")

    print()
    print("FILE:")
    pprint(result["file"])

    print()
    print("STRUCTURE:")
    pprint(result["structure"])

    print()
    print("FINANCIAL:")
    pprint(result["financial"])

    print()
    print("QUALITY:")
    pprint(result["quality"])

    print()
    print("RECOMMENDATIONS:")

    for recommendation in result["recommendations"]:
        pprint(recommendation)

    print()
    print("RESEARCH READINESS:")
    pprint(result["research_readiness"])


if __name__ == "__main__":
    main()