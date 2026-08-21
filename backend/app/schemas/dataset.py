from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DatasetCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    asset_class: str = Field(
        min_length=2,
        max_length=50,
    )

    market: str = Field(
        min_length=2,
        max_length=50,
    )

    frequency: str = Field(
        min_length=1,
        max_length=30,
    )

    source: str = Field(
        min_length=2,
        max_length=150,
    )

    storage_uri: str | None = None


class DatasetResponse(BaseModel):
    id: UUID
    organization_id: UUID
    project_id: UUID

    name: str
    description: str | None

    asset_class: str
    market: str
    frequency: str
    source: str

    storage_uri: str | None

    is_archived: bool

    created_by: UUID

    model_config = ConfigDict(
        from_attributes=True
    )