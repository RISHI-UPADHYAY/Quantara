from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.research_workspace import ResearchWorkspace


class ResearchWorkspaceRespository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    def create(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        created_by: uuid.UUID,
        name: str,
        description: str | None = None,
        dataset_id: uuid.UUID | None = None,
        dataset_version_id: uuid.UUID | None = None,
        status: str = "draft",
        symbols: list[str] | None = None,
        analysis_config: dict | None = None,
    ) -> ResearchWorkspace:

        workspace = ResearchWorkspace(
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            name=name,
            description=description,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            status=status,
            symbols=symbols or [],
            analysis_config=analysis_config or {},
        )

        self.db.add(workspace)
        self.db.flush()
        self.db.refresh(workspace)

        return workspace


    def get_by_id(
        self,
        *,
        workspace_id: uuid.UUID,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> ResearchWorkspace | None:

        statement = select(ResearchWorkspace).where(
            ResearchWorkspace.id == workspace_id,
            ResearchWorkspace.organization_id == organization_id,
            ResearchWorkspace.project_id == project_id,
        )

        return self.db.scalar(statement)


    def list_by_project(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[ResearchWorkspace]:

        statement = (
            select(ResearchWorkspace).where(
                ResearchWorkspace.organization_id == organization_id,
                ResearchWorkspace.project_id == project_id,
            )
            .order_by(ResearchWorkspace.updated_at.desc())
        )

        return list(self.db.scalars(statement).all())


    def update(
        self,
        workspace: ResearchWorkspace,
        *,
        name: str | None = None,
        description: str | None = None,
        dataset_id: uuid.UUID | None = None,
        dataset_version_id: uuid.UUID | None = None,
        status: str | None = None,
        symbols: list[str] | None = None,
        analysis_config: dict | None = None,
    ) -> ResearchWorkspace:

        if name is not None:
            workspace.name = name

        if description is not None:
            workspace.description = description

        if dataset_id is not None:
            workspace.dataset_id = dataset_id

        if dataset_version_id is not None:
            workspace.dataset_version_id = dataset_version_id

        if status is not None:
            workspace.status = status

        if symbols is not None:
            workspace.symbols = symbols

        if analysis_config is not None:
            workspace.analysis_config = analysis_config

        self.db.flush()
        self.db.refresh(workspace)

        return workspace


    def delete(
        self,
        workspace: ResearchWorkspace,
    ) -> None:

        self.db.delete(workspace)
        self.db.flush()