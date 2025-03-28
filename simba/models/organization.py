from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class OrganizationBase(BaseModel):
    """Base organization model with common fields."""

    name: str = Field(..., description="Organization name")


class OrganizationCreate(OrganizationBase):
    """Model for organization creation."""

    pass


class Organization(OrganizationBase):
    """Model for an organization in the system."""

    id: str = Field(..., description="Organization ID")
    created_at: datetime = Field(..., description="Organization creation timestamp")
    created_by: str = Field(..., description="ID of the user who created the organization")

    class Config:
        from_attributes = True


class OrganizationMemberBase(BaseModel):
    """Base organization member model with common fields."""

    user_id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    role: str = Field(..., description="Member role in the organization")


class OrganizationMember(OrganizationMemberBase):
    """Model for an organization member."""

    id: str = Field(..., description="Member ID")
    organization_id: str = Field(..., description="Organization ID")
    joined_at: datetime = Field(..., description="Timestamp when the user joined the organization")

    class Config:
        from_attributes = True


class OrganizationMemberInvite(BaseModel):
    """Model for inviting a member to an organization."""

    email: EmailStr = Field(..., description="Email of the user to invite")
    role: Literal["owner", "admin", "member", "viewer"] = Field(
        "member", description="Role to assign to the invited user"
    )


class OrganizationMemberUpdate(BaseModel):
    """Model for updating an organization member's role."""

    role: Literal["owner", "admin", "member", "viewer", "none"] = Field(
        ..., description="New role for the member"
    )


class OrganizationWithMembers(Organization):
    """Organization model with associated members."""

    members: List[OrganizationMember] = Field(
        default_factory=list, description="Organization members"
    )
