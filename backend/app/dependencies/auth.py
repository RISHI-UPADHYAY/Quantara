from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models.user import User
from app.dependencies.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid authentication credentials")
    
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid authentication credentials")
    
    try:
        user_id = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Invalid token")
    
    
    user_repository = UserRepository(db)

    user = user_repository.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "User not found")
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user

def require_role(*required_roles: str):

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:

        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker