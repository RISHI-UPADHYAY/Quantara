from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone

from app.models.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) :


        users = self.db.query(User).all()

        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )
        
    def create_user(self, name: str, email: str, password_hash: str) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user
    
    def get_user_by_id(self, user_id: UUID) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_all_users(self) -> list[User]:
        return self.db.query(User).all()
    
    def update_password(self, user, password_hash: str):
        user.password_hash = password_hash

        self.db.commit()
        self.db.refresh(user)

        return user
    
    def save_reset_token(self, user: User, token_hash: str, expires_at):
        user.reset_password_token = token_hash
        user.reset_password_expire = expires_at

        self.db.commit()
        self.db.refresh(user)

        return user
    
    def get_user_by_reset_token(self, token_hash: str):
        return (
            self.db.query(User)
            .filter(User.reset_password_token == token_hash)
            .first()
        )
    
    def clear_reset_token(self, user: User):
        user.reset_password_token = None
        user.reset_password_expire = None

        self.db.commit()
        self.db.refresh(user)

        return user

    def set_email_verification(self, user, token_hash: str, expires_at: datetime):
        user.email_verification_token = token_hash
        user.email_verification_expire = expires_at

        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user_by_email_verification_token(self, token: str):

        return (
            self.db.query(User)
            .filter(User.email_verification_token == token)
            .first()
        )

    def verify_email(self, user: User) -> User:
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expire=  None

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_user_role(self, user: User, role: str) -> User:
        user.role = role

        self.db.commit()
        self.db.refresh(user)

        return user