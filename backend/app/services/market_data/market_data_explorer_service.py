from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.repositories.dataset_repository import DatasetRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.schemas.market_data_explorer import (
    MarketDataExplorerInstrument,
    MarketDataExplorerMetadata,
    MarketDataExplorerQuality,
    MarketDataExplorerResponse,
    MarketDataExplorerRow,
)
from app.services.profiling.data_profiling_service import DataProfilingService


class MarketDataExplorerService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.dataset_repository = DatasetRepository(db)
        self.dataset_version_repository = DatasetVersionRepository(db)
        self.profiling_service = DataProfilingService()


    def explore(
        self,
        *,
        organization_id,
        project_id,
        dataset_id,
        version: int | None = None,
        symbol: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> MarketDataExplorerResponse:

        if page < 1:
            raise ValueError(
                "Page must be greater than or equal to 1"
            )

        if page_size < 1 or page_size > 500:
            raise ValueError(
                "Page size must be between 1 and 500"
            )

        if start_date and end_date and start_date > end_date:
            raise ValueError(
                "Start date must be earlier than or equal to end date"
            )

        dataset = self.dataset_repository.get_by_id_in_project(
            dataset_id=dataset_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if dataset is None:
            raise ValueError(
                "Dataset not found"
            )

        if version is None:
            dataset_version = self.dataset_version_repository.get_latest_version(
                dataset_id=dataset_id,
            )

        else:
            dataset_version = self.dataset_version_repository.get_version(
                dataset_id=dataset_id,
                version=version,
            )

        if dataset_version is None:
            raise ValueError(
                "Dataset version not found"
            )

        file_path = self._resolve_storage_path(dataset_version.storage_uri)

        dataframe = self._load_dataframe(file_path)

        profile = self.profiling_service.profile(
            file_path,
        )

        timestamp_column = self._find_column(
            dataframe,
            {"timestamp", "datetime", "data", "time"},
        )

        symbol_column = self._find_column(
            dataframe,
            {"symbol", "ticker", "instrument"},
        )

        if timestamp_column is None:
            raise ValueError(
                "Market data requires a timestamp column"
            )

        dataframe[timestamp_column] = pd.to_datetime(
            dataframe[timestamp_column],
            errors="coerce",
            utc=True,
        )

        dataframe = dataframe.dropna(subset=[timestamp_column])

        dataframe = dataframe.sort_values(
            by=timestamp_column,
            kind="stable",
        )

        if symbol and symbol_column:
            dataframe = dataframe[
                dataframe[symbol_column].astype(str).str.upper()
                == symbol.upper()
            ]

        if start_date:
            start_timestamp = self._normalize_datetime(start_date)

            dataframe = dataframe[
                dataframe[timestamp_column] >= start_timestamp
            ]

        if end_date:
            end_timestamp = self._normalize_datetime(end_date)


            dataframe = dataframe[
                dataframe[timestamp_column] <= end_timestamp
            ]

        instruments = self._build_instruments(
            dataframe=dataframe,
            timestamp_column=timestamp_column,
            symbol_column=symbol_column,
        )

        quality = self._build_quality(
            profile.get("quality", {}),
        )

        total_rows = len(dataframe)

        total_pages = (
            (total_rows + page_size - 1) // page_size
            if total_rows
            else 0
        )

        offset = (page - 1) * page_size

        page_dataframe = dataframe.iloc[
            offset : offset + page_size
        ]

        rows = self._build_rows(
            dataframe=page_dataframe,
            timestamp_column=timestamp_column,
            symbol_column=symbol_column,
        )

        metadata = self._build_metadata(
            dataset=dataset,
            dataset_version=dataset_version,
            dataframe=dataframe,
            timestamp_column=timestamp_column,
            symbol_column=symbol_column,
        )

        return MarketDataExplorerResponse(
            metadata=metadata,
            quality=quality,
            instruments=instruments,
            rows=rows,
            page=page,
            page_size=page_size,
            total_rows=total_rows,
            total_pages=total_pages,
        )

    @staticmethod
    def _resolve_storage_path(
        storage_uri: str,
    ) -> Path:
        if not storage_uri:
            raise ValueError(
                "Dataset version does not have a storage URI"
            )

        storage_root = (
            Path(__file__).resolve().parents[3] / "storage"
        ).resolve()

        path = (storage_root / storage_uri).resolve()

        if (
            path != storage_root
            and storage_root not in path.parents
        ):

            raise ValueError(
                "Invalid market-data storage path"
            )

        if not path.exists():
            raise ValueError(
                "Dataset source file not found"
            )

        if not path.is_file():
            raise ValueError(
                "Dataset source path is not a file"
            )

        return path


    @staticmethod
    def _load_dataframe(
        file_path: Path,
    ) -> pd.DataFrame:

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            return pd.read_csv(file_path)

        if suffix in {".parquet", ".pq"}:
            return pd.read_parquet(file_path)

        raise ValueError(
            f"Unsupported dataset format: {file_path.suffix}"
        )


    @staticmethod
    def _find_column(
        dataframe: pd.DataFrame,
        candidates: set[str],
    ) -> str | None:

        normalized = {
            str(column).strip().lower(): column
            for column in dataframe.columns
        }

        for candidate in candidates:
            if candidate in normalized:
                return normalized[candidate]

        return None


    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> pd.Timestamp:

        timestamp = pd.Timestamp(value)

        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")

        else:
            timestamp = timestamp.tz_convert("UTC")

        return timestamp


    @staticmethod
    def _build_instruments(
        *,
        dataframe: pd.DataFrame,
        timestamp_column: str,
        symbol_column: str | None,
    ) -> list[MarketDataExplorerInstrument]:

        if symbol_column is None:
            if dataframe.empty:
                return []

            return [
                MarketDataExplorerInstrument(
                    symbol="UNKNOWN",
                    row_count=len(dataframe),
                    first_timestamp=dataframe[timestamp_column].min(),
                    last_timestamp=dataframe[timestamp_column].max(),               
                )
            ]

        instruments: list[MarketDataExplorerInstrument] = []

        grouped = dataframe.groupby(
            symbol_column,
            dropna=False,
        )

        for raw_symbol, group in grouped:
            symbol = str(raw_symbol)

            instruments.append(
                MarketDataExplorerInstrument(
                    symbol=symbol,
                    row_count=len(group),
                    first_timestamp=group[timestamp_column].min(),
                    last_timestamp=group[timestamp_column].max(),
                )
            )

        instruments.sort(
            key=lambda item: item.symbol
        )

        return instruments


    @staticmethod
    def _build_quality(
        quality_report: dict[str, Any],
    ) -> MarketDataExplorerQuality:

        return MarketDataExplorerQuality(
            quality_score=quality_report.get(
                "quality_score"
            ),
            status=quality_report.get(
                "status"
            ),
            research_ready=quality_report.get(
                "research_ready"
            ),
            checks=quality_report.get(
                "checks",
                [],
            ),
        )


    @staticmethod
    def _build_rows(
        *,
        dataframe: pd.DataFrame,
        timestamp_column: str,
        symbol_column: str | None,
    ) -> list[MarketDataExplorerRow]:

        open_column = MarketDataExplorerService._find_column(
            dataframe,
            {"open"},
        )

        high_column = MarketDataExplorerService._find_column(
            dataframe,
            {"high"},
        )

        low_column = MarketDataExplorerService._find_column(
            dataframe,
            {"low"},
        )

        close_column = MarketDataExplorerService._find_column(
            dataframe,
            {"close", "price"},
        )

        volume_column = MarketDataExplorerService._find_column(
            dataframe,
            {"volume", "vol"},
        )

        rows: list[MarketDataExplorerRow] = []

        for _, record in dataframe.iterrows():
            rows.append(
                MarketDataExplorerRow(
                    timestamp=record[timestamp_column].to_pydatetime(),
                    symbol=(
                        str(record[symbol_column])
                        if symbol_column
                        and pd.notna(record[symbol_column])
                        else None
                    ),
                    open=MarketDataExplorerService._to_float(
                        record[open_column]
                        if open_column
                        else None
                    ),
                    high=MarketDataExplorerService._to_float(
                        record[high_column]
                        if high_column 
                        else None
                    ),
                    low=MarketDataExplorerService._to_float(
                        record[low_column]
                        if low_column
                        else None   
                    ),
                    close=MarketDataExplorerService._to_float(
                        record[close_column]
                        if close_column
                        else None
                    ),
                    volume=MarketDataExplorerService._to_float(
                        record[volume_column]
                        if volume_column
                        else None
                    ),
                )
            )

        return rows


    @staticmethod
    def _to_float(
        value: Any,
    ) -> float | None:

        if value is None or pd.isna(value):
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None


    @staticmethod
    def _build_metadata(
        *,
        dataset,
        dataset_version,
        dataframe: pd.DataFrame,
        timestamp_column: str,
        symbol_column: str | None,
    ) -> MarketDataExplorerMetadata:

        first_timestamp = (
            dataframe[timestamp_column].min()
            if not dataframe.empty
            else None
        )

        last_timestamp = (
            dataframe[timestamp_column].max()
            if not dataframe.empty
            else None
        )

        frequency = None

        if not dataframe.empty and len(dataframe) > 1:
            timestamps = (
                dataframe[timestamp_column]
                .sort_values()
                .dropna()
            )

            intervals = timestamps.diff().dropna()

            if not intervals.empty:
                median_interval = intervals.median()

                frequency = {
                    "observed_frequency_seconds": (
                        median_interval.total_seconds()
                    ),
                    "median_interval_seconds": (
                        median_interval.total_seconds()
                    ),
                }

        return MarketDataExplorerMetadata(
            dataset_id=dataset.id,
            dataset_version_id=dataset_version.id,
            version=dataset_version.version,
            dataset_name=dataset.name,
            dataset_type=None,
            row_count=len(dataframe),
            columns=[
                str(column)
                for column in dataframe.columns
            ],
            timestamp_column=timestamp_column,
            symbol_column=symbol_column,
            frequency=frequency,
            first_timestamp=(
                first_timestamp.to_pydatetime()
                if first_timestamp is not None
                else None
            ),
            last_timestamp=(
                last_timestamp.to_pydatetime()
                if last_timestamp is not None
                else None
            )
        )