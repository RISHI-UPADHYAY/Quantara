from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.password_reset import ForgotPasswordRequest
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/forgot-password",
    status_code = status.HTTP_200_OK
)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    auth_service.forgot_password(request.email)

    return {"message": "If an account with that email exists, a password reset link has been sent."}