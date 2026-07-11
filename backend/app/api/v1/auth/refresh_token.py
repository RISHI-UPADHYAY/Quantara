from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.auth import RefreshTokenRequest, Token
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository

router = APIRouter()

@router.post(
    "/refresh",
    response_model = Token,
    status_code = status.HTTP_200_OK
)
def refresh(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)

    auth_service = AuthService(user_repository, refresh_token_repository)

    try:
        tokens = auth_service.refresh_tokens(request.refresh_token)

        return Token(**tokens)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))