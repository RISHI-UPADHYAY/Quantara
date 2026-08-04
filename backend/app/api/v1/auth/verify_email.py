from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.email_verification import VerifyEmailResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository

router = APIRouter()

@router.post(
    "/verify-email",
    status_code=status.HTTP_200_OK,
)
def verify_email(request: VerifyEmailResponse, db: Session = Depends(get_db)):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    auth_service = AuthService(user_repository, refresh_token_repository)

    try:
        auth_service.verify_email(request.token)

        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )