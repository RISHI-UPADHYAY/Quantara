from pathlib import Path
from pprint import pprint

from app.services.normalization.market_data_normalizer import (
    MarketDataNormalizer,
)
from app.services.analysis.drawdown_analyzer import (
    DrawdownAnalyzer,
)


BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = (
    BASE_DIR
    / "storage"
    / "test"
    / "nifty_sample.csv"
)


def main() -> None:

    print("==============================")
    print("QUANTARA DRAWDOWN ANALYSIS")
    print("==============================")

    # --------------------------------------------------
    # Normalize market data
    # --------------------------------------------------

    normalizer = MarketDataNormalizer()

    dataframe, normalization_report = (
        normalizer.normalize(DATA_FILE)
    )

    print("\nNORMALIZED DTYPES:")
    pprint(
        {
            column: str(dtype)
            for column, dtype
            in dataframe.dtypes.items()
        }
    )

    print("\nNORMALIZED DATA:")
    print(dataframe)

    # --------------------------------------------------
    # Analyze drawdown
    # --------------------------------------------------

    analyzer = DrawdownAnalyzer()

    result = analyzer.analyze(
        dataframe
    )

    print("\nDRAWDOWN ANALYSIS:")
    pprint(result)

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert result["price_column"] == "close"
    assert result["row_count"] == 5

    assert "drawdown" in result
    assert "equity" in result

    drawdown = result["drawdown"]
    equity = result["equity"]

    assert "maximum" in drawdown
    assert "maximum_percentage" in drawdown
    assert "maximum_index" in drawdown
    assert "maximum_duration" in drawdown
    assert "recovered" in drawdown
    assert "recovery_index" in drawdown
    assert "recovery_duration" in drawdown

    assert "initial" in equity
    assert "final" in equity
    assert "peak" in equity

    assert equity["initial"] == 26005.0
    assert equity["final"] == 26020.0
    assert equity["peak"] == 26025.0

    # The sample reaches a peak and subsequently
    # experiences a drawdown.
    assert drawdown["maximum"] < 0.0
    assert drawdown["maximum_percentage"] < 0.0

    print("\n==============================")
    print("DRAWDOWN ANALYZER TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()