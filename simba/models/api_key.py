"""
API Key model for authentication without username/password.
"""
from datetime import datetime
from typing import List, Optional, Union, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class APIKey(BaseModel):
    """
    API Key model for authentication without username/password.
    """
    id: Optional[UUID] = None
    key: Optional[str] = None  # Only present when creating a new key
    key_prefix: str = Field(..., description="First few characters of key for display/identification")
    user_id: UUID = Field(..., description="Associated virtual user ID")
    tenant_id: Optional[UUID] = Field(None, description="Associated tenant ID")
    name: str = Field(..., description="User-friendly name for the API key")
    roles: List[str] = Field(default_factory=list, description="Associated roles")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")
    is_active: bool = Field(True, description="Whether the key is active")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        """Parse roles from various formats."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v


class APIKeyCreate(BaseModel):
    """
    API Key creation request model.
    """
    name: str = Field(..., description="User-friendly name for the API key")
    tenant_id: Optional[UUID] = Field(None, description="Associated tenant ID")
    roles: List[str] = Field(default_factory=list, description="Associated roles")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class APIKeyResponse(BaseModel):
    """
    API Key response model with the actual key value.
    Returned only once when the key is created.
    """
    id: UUID
    key: str
    key_prefix: str
    tenant_id: Optional[UUID] = None
    name: str
    roles: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        """Parse roles from various formats."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v


class APIKeyInfo(BaseModel):
    """
    API Key info model without the actual key value.
    Used for listing existing keys.
    """
    id: UUID
    key_prefix: str
    tenant_id: Optional[UUID] = None
    name: str
    roles: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool
    expires_at: Optional[datetime] = None
    
    @validator('roles', pre=True)
    def parse_roles(cls, v):
        """Parse roles from various formats."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v 