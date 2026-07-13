from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: UUID
    device_name: str | None
    ip_address: str | None
    created_at: datetime
    expires_at: datetime

class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]