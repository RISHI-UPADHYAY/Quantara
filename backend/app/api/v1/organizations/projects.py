from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.models.organization_member import OrganizationMember
from app.repositories.project_repository import  ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse

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