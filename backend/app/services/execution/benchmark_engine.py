from __future__ import annotations

import uuid
from decimal import Decimal

import pandas as pd
from fastapi import HTTPException, status

from app.models.execution_order import ExecutionOrder
from app.repositories.execution_order_repository import ExecutionOrderRepository


class BenchmarkEngine:
    """
    Benchmark engine for execution-quality analysis.

    Arrival price is defined as the first valid market price at or after
    the order's submission timestamp.
    """

    PRICE_COLUMNS = (
        "price",
        "close",
        "last",
        "mid",
        "mid_price",
    )

    TIMESTAMP_COLUMNS = (
        "timestamp",
        "datetime",
        "date",
        "time",
    )

    SYMBOL_COLUMNS = (
        "symbol",
        "ticker",
    )

    def __init__(
        self,
        order_repository: ExecutionOrderRepository,
    ):
        self.order_repository = order_repository


    def calculate_arrival_price(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        order_id: uuid.UUID,
        market_data: pd.DataFrame,
    ) -> dict:
        """
        Calculate  the arrival price for an execution order.

        Arrival price = first valid market observation for the order's symbol at
        or after submitted_at.
        """

        order = self.order_repository.get_by_id_in_project(
            order_id=order_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution order not found."
            )

        if market_data.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Market data is empty.",
            )

        dataframe = self._normalize_market_data(market_data)

        timestamp_column = self._resolve_column(
            dataframe,
            self.TIMESTAMP_COLUMNS,
        )

        price_column = self._resolve_column(
            dataframe,
            self.PRICE_COLUMNS,
        )

        symbol_column = self._resolve_column(
            dataframe,
            self.SYMBOL_COLUMNS,
        )

        dataframe[timestamp_column] = pd.to_datetime(
            dataframe[timestamp_column],
            utc=True,
            errors="coerce",
        )

        dataframe[price_column] = pd.to_numeric(
            dataframe[price_column],
            errors="coerce",        
        )

        dataframe = dataframe.dropna(
            subset=[timestamp_column, price_column]
        )

        dataframe = dataframe[dataframe[price_column] > 0]

        if symbol_column is not None:
            dataframe = dataframe[
                dataframe[symbol_column]
                .astype(str)
                .str.upper()
                == order.symbol.upper()
            ]

        if dataframe.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    f"No valid market data found for symbol "
                    f"{order.symbol}"
                )
            )

        submitted_at = pd.Timestamp(order.submitted_at)

        if submitted_at.tzinfo is None:
            submitted_at = submitted_at.tz_localize("UTC")

        else:
            submitted_at = submitted_at.tz_convert("UTC")

        dataframe = dataframe[
            dataframe[timestamp_column] >= submitted_at
        ].sort_values(timestamp_column)

        if dataframe.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No market-data observation exists at or after the order submission timestamp."
            )

        first_observation = dataframe.iloc[0]

        arrival_price = Decimal(
            str(first_observation[price_column])
        )

        arrival_timestamp = first_observation[timestamp_column]

        return {
            "order_id": str(order.id),
            "symbol": order.symbol,
            "side": order.side,
            "submitted_at": order.submitted_at.isoformat(),
            "arrival_timestamp": arrival_timestamp.isoformat(),
            "arrival_price": float(arrival_price),
            "price_column": price_column,
            "market_data_rows_considered": len(dataframe),
        }

    def calculate_market_vwap(
        self,
        *,
        order_symbol: pd.DataFrame,
        market_data: pd.DataFrame,
        start_timestamp: pd.Timestamp,
        end_timestamp: pd.Timestamp,
    ) -> dict:
        """
        Calculate market VWAP for a symbol over a time interval.

        VWAP = sum(price * volume) / sum(volume)
        """

        if market_data.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Market data is empty.",
            )

        dataframe = self._normalize_market_data(market_data)

        timestamp_column = self._resolve_column(
            dataframe,
            self.TIMESTAMP_COLUMNS,
        )

        price_column = self._resolve_column(
            dataframe,
            self.PRICE_COLUMNS,
        )

        volume_column = self._resolve_column(
            dataframe,
            ("volume", "quantity", "qty"),
        )

        dataframe[timestamp_column] = pd.to_datetime(
            dataframe[timestamp_column],
            utc=True,
            errors="coerce",
        )

        dataframe[price_column] = pd.to_numeric(
            dataframe[price_column],
            errors="coerce",
        )

        dataframe[volume_column] = pd.to_numeric(
            dataframe[volume_column],
            errors="coerce",
        )

        dataframe = dataframe.dropna(
            subset=[
                timestamp_column,
                price_column,
                volume_column,
            ]
        )

        dataframe = dataframe[
            (dataframe[price_column] > 0)
            & (dataframe[volume_column] > 0)
        ]

        symbol_column = self._resolve_optional_column(
            dataframe,
            self.SYMBOL_COLUMNS,
        )

        if symbol_column is not None:
            dataframe = dataframe[
                dataframe[symbol_column]
                .astype(str)
                .str.upper()
                == order_symbol.upper()
            ]

        start_timestamp = pd.Timestamp(start_timestamp)

        if start_timestamp.tzinfo is None:
            start_timestamp = start_timestamp.tz_localize("UTC")

        else:
            start_timestamp = start_timestamp.tz_convert("UTC")

        end_timestamp = pd.Timestamp(end_timestamp)

        if end_timestamp.tzinfo is None:
            end_timestamp = end_timestamp.tz_localize("UTC")

        else:
            end_timestamp = end_timestamp.tz_convert("UTC")

        dataframe = dataframe[
            (dataframe[timestamp_column] >= start_timestamp)
            & (dataframe[timestamp_column] <= end_timestamp)
        ]

        if dataframe.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No valid market data found in the requested VWAP interval."
            )

        total_volume = dataframe[volume_column].sum()

        if total_volume <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Market-data volume must be greater than zero.",
            )

        vwap = (
            dataframe[price_column] * dataframe[volume_column]
        ).sum() / total_volume

        return {
            "symbol": order_symbol,
            "start_timestamp": start_timestamp.isoformat(),
            "end_timestamp": end_timestamp.isoformat(),
            "vwap": float(vwap),
            "total_volume": float(total_volume),
            "market_data_rows": len(dataframe),
        }

    def calculate_market_twap(
        self,
        *,
        order_symbol: str,
        market_data: pd.DataFrame,
        start_timestamp: pd.Timestamp,
        end_timestamp: pd.Timestamp,
    ) -> dict:
        """
        Calculate market TWAP for a symbol over a time interval.

        Each valid market observation receives equal weight.
        """

        if market_data.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Market data is empty.",
            )

        dataframe = self._normalize_market_data(market_data)

        timestamp_column = self._resolve_column(
            dataframe,
            self.TIMESTAMP_COLUMNS,
        )

        price_column = self._resolve_column(
            dataframe,
            self.PRICE_COLUMNS,
        )

        dataframe[timestamp_column] = pd.to_datetime(
            dataframe[timestamp_column],
            utc=True,
            errors="coerce",
        )

        dataframe[price_column] = pd.to_numeric(
            dataframe[price_column],
            errors="coerce",
        )

        dataframe = dataframe.dropna(
            subset=[
                timestamp_column,
                price_column,
            ]
        )

        dataframe = dataframe[
            dataframe[price_column] > 0
        ]

        symbol_column = self._resolve_optional_column(
            dataframe,
            self.SYMBOL_COLUMNS,
        )

        if symbol_column is not None:
            dataframe = dataframe[
                dataframe[symbol_column]
                .astype(str)
                .str.upper()
                == order_symbol.upper()
            ]

        start_timestamp = pd.Timestamp(start_timestamp)

        if start_timestamp.tzinfo is None:
            start_timestamp = start_timestamp.tz_localize("UTC")

        else:
            start_timestamp = start_timestamp.tz_convert("UTC")

        end_timestamp = pd.Timestamp(end_timestamp)

        if end_timestamp.tzinfo is None:
            end_timestamp = end_timestamp.tz_localize("UTC")

        else: 
            end_timestamp = end_timestamp.tz_convert("UTC")

        dataframe = dataframe[
            (dataframe[timestamp_column] >= start_timestamp)
            & (dataframe[timestamp_column] <= end_timestamp)
        ]

        if dataframe.empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="No valid market data found in the requested TWAP interval.",
            )

        twap = dataframe[price_column].mean()

        return {
            "symbol": order_symbol,
            "start_timestamp": start_timestamp.isoformat(),
            "end_timestamp": end_timestamp.isoformat(),
            "twap": float(twap),
            "market_data_rows": len(dataframe),
        }


    @staticmethod
    def _normalize_market_data(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        result = dataframe.copy()

        result.columns = [
            str(column).strip().lower()
            for column in result.columns 
        ]

        return result


    @staticmethod
    def _resolve_column(
        dataframe: pd.DataFrame,
        candidates: tuple[str, ...],
    ) -> str:
        for column in candidates:
            if column in dataframe.columns:
                return column

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Market data is missing a required column. Expected one of: {', '.join(candidates)}."
        )


    @staticmethod
    def _resolve_optional_column(
        dataframe: pd.DataFrame,
        candidates: tuple[str, ...],
    ) -> str | None:
        for column in candidates:
            if column in dataframe.columns:
                return column

        return None