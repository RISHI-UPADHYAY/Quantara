from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken

class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_refresh_token(self, user_id, token_hash: str, expires_at: datetime, device_name: str | None = None, ip_address: str | None = None) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id = user_id,
            token_hash = token_hash,
            expires_at = expires_at,
            device_name = device_name,
            ip_address = ip_address
        )

        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token
    
    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )
    
    def revoke_token(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.revoked = True

        self.db.commit()
        self.db.refresh(refresh_token)

        return refresh_token
    
    def revoke_all_for_user(self, user_id: UUID) -> None:
        (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .update({"revoked": True})
        )

        self.db.commit()
    
    def is_token_valid(self, refresh_token: RefreshToken | None) -> bool:
        if refresh_token is None:
            return False
        if refresh_token.revoked:
            return False
        if refresh_token.expires_at <= datetime.now(timezone.utc):
            return False
        return True

    def delete_expired_tokens(self) ->None:
        (
            self.db.query(RefreshToken)
            .filter(RefreshToken.expires_at <= datetime.now(timezone.utc))
            .delete()
        )

        self.db.commit()