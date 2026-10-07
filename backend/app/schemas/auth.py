from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid unique email address")
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")

class UserLogin(BaseModel):
    email_or_username: str = Field(..., description="Email address or username")
    password: str = Field(..., description="Account password")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class TokenPayload(BaseModel):
    sub: str
    exp: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

Token.model_rebuild()
