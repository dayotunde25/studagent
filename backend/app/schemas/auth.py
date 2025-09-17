"""
Pydantic schemas for authentication.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    display_name: str
    bio: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[str] = None
    role: str = "student"


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for user updates."""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[str] = None
    skills: Optional[str] = None
    role: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    is_active: bool
    created_at: str
    last_active: str

    class Config:
        from_attributes = True


class TokenRefresh(BaseModel):
    """Schema for token refresh."""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)