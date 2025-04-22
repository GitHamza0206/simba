from typing import Dict, Optional, Any
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr = Field(..., description="User email address")

class UserCreate(UserBase):
    """Model for user creation."""
    password: str = Field(..., description="User password")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional user metadata")

class UserLogin(UserBase):
    """Model for user login."""
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    """Model for user response."""
    id: str = Field(..., description="User ID")
    created_at: Optional[datetime] = Field(None, description="User creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="User metadata")
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Model for token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_at: Optional[int] = Field(None, description="Token expiration timestamp")

class AuthResponse(BaseModel):
    """Combined auth response model."""
    user: UserResponse
    token: TokenResponse 