from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password
from app.models.user import User

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def register_user(self, user_data: UserCreate):
        existing_user = self.user_repository.get_user_by_email(user_data.email)

        if existing_user :
            raise ValueError("Email already registered")

        password_hash = hash_password(user_data.password)

        return self.user_repository.create_user(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash
        )
    
    def authenticate_user(self, email: str, password: str) -> User:

        user = self.user_repository.get_user_by_email(email)
        

        if user is None:
            raise ValueError("Invalid email or password")
        
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid user or password")
        
        return user