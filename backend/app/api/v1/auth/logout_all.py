from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.auth_service import AuthService
from app.schemas.auth import MessageResponse

router = APIRouter()

@router.post(
    "/logout-all",
    response_model = MessageResponse,
    status_code = status.HTTP_200_OK
)
def logout_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    auth_service = AuthService(user_repository, refresh_token_repository)

    try:
        return auth_service.logout_all(current_user)
    except ValueError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail=str(e))