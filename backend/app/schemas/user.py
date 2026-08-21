from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID

class UserCreate(BaseModel):
    name:str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserAdminResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    email_verified: bool
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserRoleUpdate(BaseModel):
    role: str