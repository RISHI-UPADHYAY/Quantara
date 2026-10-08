from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchWorkspaceCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Name of the research workspace.",
    )

    description: str | None = Field(
        default=None,
        description="Optional description of the research workspace."
    )

    dataset_id: uuid.UUID | None = Field(
        default=None,
        description="Optional dataset attached to the workspace.",
    )

    dataset_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional dataset version attached to the workspace.",
    )

    symbols: list[str] = Field(
        default_factory=list,
        description="Symbols selected for research.",
    )

    analysis_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for analyses performed in the workspace.",
    )


class ResearchWorkspaceUpdateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Updated workspace name.",
    )
    
    description: str | None = Field(
        default=None,
        description="Updated workspace description."
    )
    
    dataset_id: uuid.UUID | None = Field(
        default=None,
        description="Updated dataset attached to the workspace.",
    )
    
    dataset_version_id: uuid.UUID | None = Field(
        default=None,
        description="Updated dataset version attached to the workspace.",
    )

    status: str | None = Field(
        default=None,
        max_length=30,
        description="Updated dataset version attached to the workspace."
    )
    
    symbols: list[str] = Field(
        default_factory=list,
        description="Updated symbols selected for research.",
    )
    
    analysis_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Updated analysis configuration.",
    )


class ResearchWorkspaceResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    dataset_version_id: uuid.UUID
    name: str | None = None
    description: str | None
    status: str
    symbols: list[str]
    analysis_config: dict[str, Any]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ResearchWorkspaceListResponse(BaseModel):
    workspaces: list[ResearchWorkspaceResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)