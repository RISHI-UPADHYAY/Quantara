from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter()

@router.delete(
    "/sessions/{session_id}",
    response_model = MessageResponse,
    status_code = status.HTTP_200_OK
)
def revoke_session(session_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    auth_service = AuthService(UserRepository(db), RefreshTokenRepository(db))

    try:
        return auth_service.revoke_session(current_user, session_id)
    except ValueError as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))