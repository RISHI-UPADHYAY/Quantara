from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import HTTPException, status


class ExecutionMarketDataLoader:
    """
    Load canonical Quantara market data refereneced by a DatasetVersion.
    """

    def __init__(
        self,
        storage_root: Path,
    ):
        self.storage_root = storage_root.resolve()


    def load(
        self,
        storage_uri: str,
    ) -> pd.DataFrame:

        path = (self.storage_root / storage_uri).resolve()

        if(
            path != self.storage_root
            and self.storage_root not in path.parents
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid market-data storage path.",
            )

        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market-data files not found",
            )

        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Market-data storage URI is not a file."
            )

        suffix = path.suffix.lower()

        try:
            if suffix == ".csv":
                return pd.read_csv(path)

            if suffix in {".parquet", ".pq"}:
                return pd.read_parquet(path)

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load market data: {exc}",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported market-data format. Supported formats: CSV and Parquet."
        )