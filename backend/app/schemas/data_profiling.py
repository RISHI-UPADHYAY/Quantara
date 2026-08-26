from typing import Any

from pydantic import BaseModel, ConfigDict


class DataProfilingRequest(BaseModel):
    file_path: str

class DataProfilingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file: dict[str, Any]
    structure: dict[str, Any]
    financial: dict[str, Any]
    quality: dict[str, Any]
    recommendations: list[dict[str, Any]]
    research_readiness: dict[str, Any]  