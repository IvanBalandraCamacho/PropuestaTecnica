"""
Schemas para autenticación.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base schema for User."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Schema for login."""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str  # user_id
    exp: datetime
