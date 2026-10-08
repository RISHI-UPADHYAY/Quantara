from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.auth import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.schemas.research_workspace import (
    ResearchWorkspaceCreateRequest,
    ResearchWorkspaceListResponse,
    ResearchWorkspaceResponse,
    ResearchWorkspaceUpdateRequest,
)
from app.services.research.research_workspace_service import (
    ResearchWorkspaceService,
)


router = APIRouter()


def _to_response(workspace) -> ResearchWorkspaceResponse:
    return ResearchWorkspaceResponse(
        id=workspace.id,
        organization_id=workspace.organization_id,
        project_id=workspace.project_id,
        dataset_id=workspace.dataset_id,
        dataset_version_id=workspace.dataset_version_id,
        name=workspace.name,
        description=workspace.description,
        status=workspace.status,
        symbols=workspace.symbols or [],
        analysis_config=workspace.analysis_config or {},
        created_by=workspace.created_by,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


@router.post(
    "/{organization_id}/projects/{project_id}/research-workspaces",
    response_model=ResearchWorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_workspace(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ResearchWorkspaceCreateRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
):
    service = ResearchWorkspaceService(db)

    try:
        workspace = service.create_workspace(
            organization_id=organization_id,
            project_id=project_id,
            created_by=membership.user_id,
            name=payload.name,
            description=payload.description,
            dataset_id=payload.dataset_id,
            dataset_version_id=payload.dataset_version_id,
            symbols=payload.symbols,
            analysis_config=payload.analysis_config,
        )
        db.commit()
        db.refresh(workspace)

        return _to_response(workspace)

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{organization_id}/projects/{project_id}/research-workspaces",
    response_model=ResearchWorkspaceListResponse,
    status_code=status.HTTP_200_OK,
)
def list_research_workspaces(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
):
    service = ResearchWorkspaceService(db)

    workspaces = service.list_workspaces(
        organization_id=organization_id,
        project_id=project_id,
    )

    return ResearchWorkspaceListResponse(
        workspaces=[_to_response(workspace) for workspace in workspaces],
        total=len(workspaces),
    )


@router.get(
    "/{organization_id}/projects/{project_id}/research-workspaces/{workspace_id}",
    response_model=ResearchWorkspaceResponse,
    status_code=status.HTTP_200_OK,
)
def get_research_workspace(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
):
    service = ResearchWorkspaceService(db)

    workspace = service.get_workspace(
        organization_id=organization_id,
        project_id=project_id,
        workspace_id=workspace_id,
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research workspace not found.",
        )

    return _to_response(workspace)


@router.patch(
    "/{organization_id}/projects/{project_id}/research-workspaces/{workspace_id}",
    response_model=ResearchWorkspaceResponse,
    status_code=status.HTTP_200_OK,
)
def update_research_workspace(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    payload: ResearchWorkspaceUpdateRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
):
    service = ResearchWorkspaceService(db)

    try:
        workspace = service.update_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            dataset_id=payload.dataset_id,
            dataset_version_id=payload.dataset_version_id,
            status=payload.status,
            symbols=payload.symbols,
            analysis_config=payload.analysis_config,
        )
        db.commit()
        db.refresh(workspace)

        return _to_response(workspace)

    except ValueError as exc:
        db.rollback()

        if str(exc) == "Research workspace not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{organization_id}/projects/{project_id}/research-workspaces/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_research_workspace(
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    workspace_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN, 
            ROLE_ANALYST,
        )
    ),
):
    service = ResearchWorkspaceService(db)

    try:
        service.delete_workspace(
            organization_id=organization_id,
            project_id=project_id,
            workspace_id=workspace_id,
        )
        db.commit()

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc