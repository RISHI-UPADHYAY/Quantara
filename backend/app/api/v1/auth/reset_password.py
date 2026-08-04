from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db

from app.schemas.password_reset import ResetPasswordRequest

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository

from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):

    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))
    try:
        return auth_service.reset_password(
            request.token,
            request.new_password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )