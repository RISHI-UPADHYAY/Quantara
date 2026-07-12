from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import LogoutRequest, MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK
)
def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(
        UserRepository(db),
        RefreshTokenRepository(db)
    )
    try:
        return auth_service.logout(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))