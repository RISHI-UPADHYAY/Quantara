from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.schemas.user import UserLogin, Token
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.security import create_access_token
from app.dependencies.database import get_db
from app.repositories.refresh_token_repository import RefreshTokenRepository

router = APIRouter()

@router.post( 
    "/login",
    response_model = Token,
    status_code = status.HTTP_200_OK,
)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):

    user_repository = UserRepository(db)
    refresh_token_repository = RefreshTokenRepository(db)
    
    auth_service = AuthService(user_repository, refresh_token_repository)

    try:
        tokens = auth_service.login(user_credentials.email, user_credentials.password)
        return Token(**tokens)
    
    except ValueError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail=  "Invalid email or password")
