import uuid 
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IngestionCreate(BaseModel):
    dataset_version_id: uuid.UUID
    source_filename: str
    storage_key: str
    file_size_bytes: int
    checksum: str | None = None


class IngestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    status: str
    source_filename: str
    storage_key: str
    file_size_bytes: int
    checksum: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime


class IngestionFailRequest(BaseModel):
    error_message: str = Field(
        min_length=1,
        max_length=5000,
    )