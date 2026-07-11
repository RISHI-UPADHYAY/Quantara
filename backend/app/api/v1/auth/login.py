from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.schemas.user import UserLogin, Token
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.security import create_access_token
from app.dependencies.database import get_db

router = APIRouter()

@router.post( 
    "/login",
    response_model = Token,
    status_code = status.HTTP_200_OK,
)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):

    user_repository = UserRepository(db)
    auth_service = AuthService(user_repository)

    try:
        user = auth_service.authenticate_user(user_credentials.email, user_credentials.password)
    
    except ValueError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail=  "Invalid email or password")

    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer") 