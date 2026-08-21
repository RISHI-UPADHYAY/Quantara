from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter()

@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(data: OrganizationCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    repository = OrganizationRepository(db)

    existing = repository.get_by_slug(data.slug)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists",
        )

    return repository.create(
        name=data.name,
        slug=data.slug,
        user_id=current_user.id,
    )