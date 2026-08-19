from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.project_repository import  ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.dependencies.auth import get_current_active_user
from app.dependencies.organization import get_current_organization
from app.models.organization import Organization
from app.models.user import User

router = APIRouter()

@router.post(
    "/{organization_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(orgainzation_id: UUID, data: ProjectCreate, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN, ROLE_ANALYST)), db: Session = Depends(get_db)):

    repository = ProjectRepository(db)

    existing = repository.get_by_slug(
        organization_id=orgainzation_id,
        slug=data.slug,
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project slug already exists in this organization",
        )

    return repository.create(
        organization_id=orgainzation_id,
        name=data.name,
        slug=data.slug,
        description=data.description,
        created_by=membership.user_id,
    )

@router.get(
    "/{organization_id}/projects",
    response_model=list[ProjectResponse],
)
def list_projects(organization_id: UUID, organization: Organization = Depends(get_current_organization), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):

    repository = ProjectRepository(db)

    return repository.get_by_organization(
        organization_id
    )

@router.get(
    "/{organization_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
def get_project(organization_id: UUID, project_id: UUID, organization: Organization = Depends(get_current_organization), db: Session = Depends(get_db)):
    repository = ProjectRepository(db)

    project = repository.get_by_id_in_organization(
        project_id=project_id,
        organization_id=organization_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.patch(
    "/{organization_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
def update_project(organization_id: UUID, project_id: UUID, data: ProjectUpdate, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    repository = ProjectRepository(db)

    project = repository.get_by_id_in_organization(
        project_id=project_id,
        organization_id=organization_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return repository.update(
        project=project,
        name=data.name,
        description=data.description,
    )

@router.delete(
    "/{organization_id}/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_project(organization_id: UUID, project_id: UUID, membership: OrganizationMember = Depends(require_organization_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    repository = ProjectRepository(db)

    project = repository.get_by_id_in_organization(
        project_id=project_id,
        organization_id=organization_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    repository.delete(project)