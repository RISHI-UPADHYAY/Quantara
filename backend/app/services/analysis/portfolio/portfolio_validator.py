from __future__ import annotations

import pandas as pd 


class PortfolioValidationError(ValueError):
    """
    Raised when portfolio input is invalid.
    """


class PortfolioValidator:
    """
    Validates portfolio holdings and market-price data.
    """

    @staticmethod
    def validate_holdings(
        holdings: pd.DataFrame,
        symbol_column: str = "symbol",
        weight_column: str = "weight",
    ) -> None:

        if not isinstance(holdings, pd.DataFrame):
            raise PortfolioValidationError(
                "Holdings must be provided as a pandas DataFrame."
            )

        if holdings.empty:
            raise PortfolioValidationError(
                "Portfolio holdings cannot be empty."
            )

        required_columns = {symbol_column, weight_column}
        missing = required_columns - set(holdings.columns)

        if missing:
            raise PortfolioValidationError(
                f"Missing required holding columns: {sorted(missing)}"
            )

        if holdings[symbol_column].isna().any():
            raise PortfolioValidationError(
                "Portfolio contains missing symbols."
            )

        if holdings[weight_column].isna().any():
            raise PortfolioValidationError(
                "Portfolio contains missing weights."
            )

        if not pd.api.types.is_numeric_dtype(holdings[weight_column]):
            raise PortfolioValidationError(
                "Portfolio weights must be numeric."
            )

        if (holdings[weight_column] < 0).any():
            raise PortfolioValidationError(
                "Portfolio weights cannot be negative."
            )

        duplicates = (
            holdings.loc[
                holdings[symbol_column].duplicated(),
                symbol_column,
            ]
            .astype(str)
            .tolist()
        )

        if duplicates:
            raise PortfolioValidationError(
                f"Duplcate portfolio symbols found: {duplicates}"
            )

        total_weight = float(holdings[weight_column].sum())

        if total_weight <= 0:
            raise PortfolioValidationError(
                "Portfolio total weight must be greater than zero."
            )

        if abs(total_weight - 1.0) > 1e-6:
            raise PortfolioValidationError(
                f"Porfolio weights must sum to 1.0. Received {total_weight: .10f}"
            )


    @staticmethod
    def validate_price_data(
        prices: pd.DataFrame,
        symbols: list[str],
    ) -> None:
        if not isinstance(prices, pd.DataFrame):
            raise PortfolioValidationError(
                "Price data must be provided as a pandas DataFrame."
            )

        if prices.empty:
            raise PortfolioValidationError(
                "Price data cannot be empty."
            )

        missing_symbols = [
            symbol for symbol in symbols
            if symbol not in prices.columns
        ]

        if missing_symbols:
            raise PortfolioValidationError(
                f"Price data is missing portfolio symbols: {missing_symbols}"
            )

        selected = prices[symbols]

        if selected.isna().all().any():
            invalid_symbols = selected.columns[
                selected.isna().all()
            ].tolist()

            raise PortfolioValidationError(
                f"No usable price data found for symbols: {invalid_symbols}"
            )

        if not all(
            pd.api.types.is_numeric_dtype(selected[column])
            for column in selected.columns
        ):
            raise PortfolioValidationError(
                "Portfolio price columns must be numeric."
            )