from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_SUPER_ADMIN,
    can_manage_role,
)
from app.dependencies.auth import require_role
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRoleUpdate, UserAdminResponse

router = APIRouter()

@router.patch(
    "/{user_id}/role",
    response_model=UserAdminResponse,
)
def update_user_role(user_id: UUID, role_update: UserRoleUpdate, current_user: User = Depends(require_role(ROLE_ADMIN, ROLE_SUPER_ADMIN)), db: Session = Depends(get_db)):
    user_repository = UserRepository(db)

    target_user = user_repository.get_user_by_id(user_id)

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not can_manage_role(current_user.role, role_update.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to assign this role"
        )

    updated_user = user_repository.update_user_role(
        target_user,
        role_update.role,
    )

    return updated_user