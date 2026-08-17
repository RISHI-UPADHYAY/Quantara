from fastapi import Depends, APIRouter

from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get(
    "/me",
    response_model = UserResponse
)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user