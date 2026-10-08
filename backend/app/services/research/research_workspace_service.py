from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.research_workspace import ResearchWorkspace
from app.repositories.research_workspace_repository import ResearchWorkspaceRespository
from app.repositories.dataset_repository import DatasetRepository


class ResearchWorkspaceService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
        self.workspace_repository = ResearchWorkspaceRespository(db)
        self.dataset_repository = DatasetRepository(db)


    def create_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        created_by: uuid.UUID,
        name: str,
        description: str | None = None,
        dataset_id: uuid.UUID | None = None,
        dataset_version_id: uuid.UUID | None = None,
        symbols: list[str] | None = None,
        analysis_config: dict[str, Any] | None = None,
    ) -> ResearchWorkspace:

        self._validate_dataset_context(
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
        )

        normalized_symbols = self._normalize_symbols(symbols)

        return self.workspace_repository.create(
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            name=name.strip(),
            description=description.strip() if description else None,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            symbols=normalized_symbols,
            analysis_config=analysis_config or {},
        )


    def get_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> ResearchWorkspace | None:

        return self.workspace_repository.get_by_id(
            workspace_id=workspace_id,
            organization_id=organization_id,
            project_id=project_id,
        )


    def list_workspaces(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[ResearchWorkspace]:

        return self.workspace_repository.list_by_project(
            organization_id=organization_id,
            project_id=project_id,
        )


    def update_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        dataset_id: uuid.UUID | None = None,
        dataset_version_id: uuid.UUID | None = None,
        status: str | None = None,
        symbols: list[str] | None = None,
        analysis_config: dict[str, Any] | None = None,
    ) -> ResearchWorkspace:

        workspace = self.get_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        if workspace is None:
            raise ValueError(
                "Research workspace not found."
            )

        effective_dataset_id = (
            dataset_id
            if dataset_id is not None
            else workspace.dataset_id
        )

        effective_dataset_version_id = (
            dataset_version_id
            if dataset_version_id is not None
            else workspace.dataset_version_id
        )

        self._validate_dataset_context(
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=effective_dataset_id,
            dataset_version_id=effective_dataset_version_id,
        )

        normalized_symbols = (
            self._normalize_symbols(symbols)
            if symbols is not None
            else None
        )

        return self.workspace_repository.update(
            workspace=workspace,
            name=name.strip() if name is not None else None,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            status=status.strip() if status is not None else None,
            symbols=normalized_symbols,
            analysis_config=analysis_config,
        )


    def delete_workspace(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> None:

        workspace = self.get_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )

        if workspace is None:
            raise ValueError(
                "Research workspace not found."
            )

        self.workspace_repository.delete(workspace)


    def _validate_dataset_context(
        self,
        *,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        dataset_version_id: uuid.UUID | None,
    ) -> None:

        if dataset_version_id is not None and dataset_id is None:
            raise ValueError(
                "dataset_id is required when dataset_version_id is provided."
            )

        if dataset_id is None:
            return

        dataset = self.dataset_repository.get_by_id_in_project(
            dataset_id=dataset_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if dataset is None:
            raise ValueError(
                "Dataset not found."
            )

        if dataset_version_id is None:
            return

        versions = list(getattr(
            dataset, 
            "versions",
            [],
        ) or [])

        if not any(
            version.id == dataset_version_id
            for version in versions
        ):
            raise ValueError(
                "Dataset version does not belong to the selected dataset."
            )


    @staticmethod
    def _normalize_symbols(
        symbols: list[str] | None,
    ) -> list[str]:
        if not symbols:
            return []

        normalized = {
            symbol.strip().upper()
            for symbol in symbols
            if symbol and symbol.strip()
        }

        return sorted(normalized)