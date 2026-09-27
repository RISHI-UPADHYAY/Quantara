from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionDataImportResponse(BaseModel):
    dataset_version_id: UUID

    requested_rows: int = Field(
        ge=0,
    )

    orders_created: int = Field(
        ge=0,
    )

    orders_skipped: int = Field(
        ge=0,
    )

    fills_created: int = Field(
        ge=0,
    )

    fills_skipped: int = Field(
        ge=0,
    )

    errors: list[str] = Field(
        default_factory=list,
    )

    warnings: list[str] = Field(
        default_factory=list,
    ) 