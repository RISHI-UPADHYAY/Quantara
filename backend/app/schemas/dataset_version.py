from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetVersionCreate(BaseModel):
    storage_uri: str | None = None  
    row_count: int | None = None    
    checksum: str | None = None
    schema_hash: str | None = None  


class DatasetVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    version: int
    status: str
    storage_uri: str | None
    row_count: int | None
    checksum: str | None
    schema_hash: str | None
    created_by: UUID
    created_at: datetime