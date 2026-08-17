from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_admin_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserAdminResponse

router = APIRouter()

@router.get(
    "",
    response_model=list[UserAdminResponse],
)
def list_users(current_admin: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    user_repository = UserRepository(db)

    return user_repository.get_all_users()