from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter()

@router.post(
    "/register",
    response_model = UserResponse,
    status_code = status.HTTP_201_CREATED,
)

def register(user:UserCreate, db: Session=Depends(get_db)):
    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)

    try:
        return auth_service.register_user(user)
    except ValueError as e:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail=str(e),
        )