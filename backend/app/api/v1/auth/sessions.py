from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.session import SessionListResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.get(
    "/sessions",
    response_model = SessionListResponse
)
def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    return auth_service.get_active_sessions(current_user)