from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    last_login_at: datetime | None


class AuthOut(BaseModel):
    admin: AdminOut
    access_token: str
    token_type: str = "bearer"
