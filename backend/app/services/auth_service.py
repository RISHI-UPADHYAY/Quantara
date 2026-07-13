from sqlalchemy.orm import Session
import uuid

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserCreate
from app.models.user import User
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiry,
    hash_password, 
    verify_password
)

class AuthService:
    def __init__(self, user_repository: UserRepository, refresh_token_repository: RefreshTokenRepository):
        self.user_repository = user_repository
        self.refresh_token_repository = refresh_token_repository
    
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
    
    def login(self, email: str, password: str):
        #Authenticate user
        user = self.authenticate_user(email, password)

        #Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})

        refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": str(uuid.uuid4())})

        #Hash refresh token before storing
        refresh_token_hash = hash_refresh_token(refresh_token)

        #Store refresh token in database
        self.refresh_token_repository.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=get_refresh_token_expiry(),
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def logout(self, refresh_token: str):
        payload = decode_refresh_token(refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token")
        
        token_hash = hash_refresh_token(refresh_token)

        stored_token = (
            self.refresh_token_repository
            .get_refresh_token_by_hash(token_hash)
        )

        if stored_token is None:
            raise ValueError("Refresh token not found")
        
        if stored_token.revoked:
            raise ValueError("Refresh token already revoked")

        self.refresh_token_repository.revoke_token(stored_token)

        return {"message": "Logged out successfully"}

    def logout_all(self, user):
        self.refresh_token_repository.revoke_all_for_user(user.id)

        return {"message": "Logged out from all devices successfully"} 
    
    def refresh_tokens(self, refresh_token: str):
        #Decode the refresh token
        payload = decode_refresh_token(refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token")
        
        #Extract claims
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if user_id is None or jti is None:
            raise ValueError("Invalid refresh token")
        
        #Hash incoming refresh token
        refresh_token_hash = hash_refresh_token(refresh_token)

        #Look up token in DB
        stored_token = (
            self.refresh_token_repository
            .get_refresh_token_by_hash(refresh_token_hash)
        )

        #Validate token
        if not self.refresh_token_repository.is_token_valid(stored_token):
            raise ValueError("Refresh token is invalid or expired")
        
        #Load user
        user = self.user_repository.get_user_by_id(user_id)

        if user is None:
            raise ValueError("User not found")
        
        #Generate new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})

        new_refresh_token = create_refresh_token(data={"sub": str(user.id), "jti": str(uuid.uuid4())})

        #Hash new refresh token
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)
        
        #Revoke old refresh token
        self.refresh_token_repository.revoke_token(stored_token)

        #Store new refresh token
        self.refresh_token_repository.create_refresh_token(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=get_refresh_token_expiry(),
        )


        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }