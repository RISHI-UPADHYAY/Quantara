from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAdminResponse
from app.core.permissions import ROLE_ADMIN
from app.dependencies.auth import require_role

router = APIRouter()

@router.get(
    "",
    response_model=list[UserAdminResponse],
)
def list_users(current_admin: User = Depends(require_role(ROLE_ADMIN)), db: Session = Depends(get_db)):
    user_repository = UserRepository(db)

    return user_repository.get_all_users()