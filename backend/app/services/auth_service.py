from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone
from uuid import UUID 

from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserCreate
from app.models.user import User
from app.services.email_service import EmailService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_refresh_token,
    get_refresh_token_expiry,
    hash_password, 
    verify_password
)
from app.core.security import (
    generate_password_reset_token,
    hash_password_reset_token,
    get_password_reset_expiry
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
    
    def get_active_sessions(self, user):
        sessions = self.refresh_token_repository.get_active_sessions(user.id)

        return {"sessions": sessions}
    
    def revoke_session(self, user: User, session_id: uuid):
        session = self.refresh_token_repository.get_by_id(session_id)

        if session is None:
            raise ValueError("Session not found")
        
        if session.user_id != user.id:
            raise ValueError("You do not have permission to revoke this session")
        
        if session.revoked:
            raise ValueError("Session already revoked")
        
        self.refresh_token_repository.revoke_token(session)
        return {"message": "Session revoked successfully"}
    
    def change_password(self, user, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        if verify_password(new_password, user.password_hash):
            raise ValueError("New password must be different from the current password")
        
        new_password_hash = hash_password(new_password)

        self.user_repository.update_password(user, new_password_hash)

        self.refresh_token_repository.revoke_all_for_user(user.id)

        return {"message": "Password changed successfully. Please login again."}
    
    def forgot_password(self, email: set):
        user = self.user_repository.get_user_by_email(email)

        if user is None:
            return
        
        reset_token = generate_password_reset_token()

        reset_token_hash = hash_password_reset_token(reset_token)

        self.user_repository.save_reset_token(
            user=user,
            token_hash=reset_token_hash,
            expires_at=get_password_reset_expiry()
        )

        EmailService().send_password_reset_email(
            email=user.email,
            reset_token=reset_token
        )

    def reset_password(self, token: str, new_password: str):
        #Hash incoming token
        token_hash = hash_password_reset_token(token)

        #Find User
        user = self.user_repository.get_user_by_reset_token(token_hash)

        if user is None:
            raise ValueError("Invalid reset token")

        #Check expiry
        if(user.reset_password_expire is None or user.reset_password_expire < datetime.now(timezone.utc)):
            raise ValueError("Reset token has expired")

        #Update Password
        user.password_hash = hash_password(new_password)

        #Remove reset token
        self.user_repository.clear_reset_token(user)

        #Revoke every login session
        self.refresh_token_repository.revoke_all_for_user(user.id)

        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)

        return {"message": "Password has been reset successfully"}