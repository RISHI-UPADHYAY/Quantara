from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_active_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationResponse

router = APIRouter()

@router.get(
    "",
    response_model=list[OrganizationResponse],
)
def list_my_organizations(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    repository = OrganizationRepository(db)

    return repository.get_user_organizations(
        current_user.id
    )