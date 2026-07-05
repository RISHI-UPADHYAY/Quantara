from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.core.security import hash_pasword

class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)
    
    def register_user(self, user_data: UserCreate):
        existing_user = self.user_repository.get_user_by_email(user_data.email)

        if existing_user :
            raise ValueError("Email already registered")

        password_hash = hash_pasword(user_data.password)

        return self.user_repository.create_user(
            name=user_data.name,
            email=user_data.email,
            password_hash=password_hash
        )