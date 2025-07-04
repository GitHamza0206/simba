from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


class Permission(BaseModel):
    """Model for a permission in the system."""
    id: Optional[int] = Field(None, description="Permission ID")
    name: str = Field(..., description="Permission name (e.g., 'users:read')")
    description: Optional[str] = Field(None, description="Permission description")
    
    class Config:
        from_attributes = True


class Role(BaseModel):
    """Model for a role in the system."""
    id: Optional[int] = Field(None, description="Role ID")
    name: str = Field(..., description="Role name (e.g., 'admin', 'user')")
    description: Optional[str] = Field(None, description="Role description")
    created_at: Optional[datetime] = Field(None, description="Role creation timestamp")
    
    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    """Model for role creation."""
    name: str = Field(..., description="Role name (e.g., 'admin', 'user')")
    description: Optional[str] = Field(None, description="Role description")


class RoleUpdate(BaseModel):
    """Model for role update."""
    name: Optional[str] = Field(None, description="Role name")
    description: Optional[str] = Field(None, description="Role description")


class RolePermission(BaseModel):
    """Model for a role-permission relationship."""
    role_id: int = Field(..., description="Role ID")
    permission_id: int = Field(..., description="Permission ID")
    
    class Config:
        from_attributes = True


class UserRole(BaseModel):
    """Model for a user-role relationship."""
    user_id: str = Field(..., description="User ID")
    role_id: int = Field(..., description="Role ID")
    organization_id: str = Field(..., description="Organization ID")
    created_at: Optional[datetime] = Field(None, description="Timestamp of role assignment")
    
    class Config:
        from_attributes = True


class UserRoleCreate(BaseModel):
    """Model for assigning a role to a user."""
    role_id: int = Field(..., description="Role ID")
    organization_id: str = Field(..., description="Organization ID")


class RoleWithPermissions(Role):
    """Role model with associated permissions."""
    permissions: List[Permission] = Field(default_factory=list, description="Role permissions")


class UserWithRoles(BaseModel):
    """User model extended with roles."""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    created_at: Optional[datetime] = Field(None, description="User creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="User metadata")
    roles: List[Role] = Field(default_factory=list, description="User roles")
    
    class Config:
        from_attributes = True 