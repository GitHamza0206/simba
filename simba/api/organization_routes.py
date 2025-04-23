import logging
from typing import List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from simba.api.middleware.auth import get_current_user
from simba.models.user import UserResponse
from simba.models.organization import (
    Organization, 
    OrganizationCreate, 
    OrganizationMember,
    OrganizationMemberInvite,
    OrganizationMemberUpdate
)
from simba.auth.supabase_client import get_supabase_client
from simba.organizations.organization_service import OrganizationService

logger = logging.getLogger(__name__)

# Create router
organization_router = APIRouter(
    prefix="/organizations",
    tags=["organizations"]
)

def get_organization_service():
    return OrganizationService()

@organization_router.get(
    "",
    response_model=List[Organization],
    summary="Get all organizations for the current user",
    description="Retrieve all organizations that the authenticated user is a member of"
)
async def get_organizations(
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Get all organizations for the current user.
    
    Args:
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        List of organizations the user is a member of
    """
    return await service.get_organizations(current_user.get("id"))

@organization_router.post(
    "",
    response_model=Organization,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
    description="Create a new organization and make the current user the owner"
)
async def create_organization(
    organization: OrganizationCreate,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Create a new organization.
    
    Args:
        organization: The organization to create
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        The created organization
    """
    return await service.create_organization(organization, current_user.get("id"))

@organization_router.get(
    "/{org_id}",
    response_model=Organization,
    summary="Get organization by ID",
    description="Retrieve an organization by its ID, if the user is a member"
)
async def get_organization(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Get an organization by ID.
    
    Args:
        org_id: The ID of the organization to retrieve
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        The organization if found and the user is a member
    """
    return await service.get_organization(org_id, current_user.get("id"))

@organization_router.get(
    "/{org_id}/members",
    response_model=List[OrganizationMember],
    summary="Get organization members",
    description="Retrieve all members of an organization, if the user is a member"
)
async def get_organization_members(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Get all members of an organization.
    
    Args:
        org_id: The ID of the organization
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        List of organization members
    """
    return await service.get_organization_members(org_id, current_user.get("id"))

@organization_router.post(
    "/{org_id}/invite",
    response_model=OrganizationMember,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a member to an organization",
    description="Invite a user to join an organization, if the current user has appropriate permissions"
)
async def invite_member(
    org_id: str,
    invite: OrganizationMemberInvite,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Invite a user to an organization.
    
    Args:
        org_id: The ID of the organization
        invite: The invitation details
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        The invited member
    """
    return await service.invite_member(org_id, invite, current_user.get("id"))

@organization_router.put(
    "/{org_id}/members/{member_id}",
    response_model=OrganizationMember,
    summary="Update a member's role",
    description="Update a member's role in an organization, if the current user is an owner"
)
async def update_member_role(
    org_id: str,
    member_id: str,
    update: OrganizationMemberUpdate,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Update a member's role in an organization.
    
    Args:
        org_id: The ID of the organization
        member_id: The ID of the member to update
        update: The update details
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        The updated member
    """
    return await service.update_member_role(org_id, member_id, update, current_user.get("id"))

@organization_router.delete(
    "/{org_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from an organization",
    description="Remove a member from an organization, if the current user is an owner"
)
async def remove_member(
    org_id: str,
    member_id: str,
    current_user: dict = Depends(get_current_user),
    service: OrganizationService = Depends(get_organization_service)
):
    """Remove a member from an organization.
    
    Args:
        org_id: The ID of the organization
        member_id: The ID of the member to remove
        current_user: The authenticated user making the request
        service: The organization service
        
    Returns:
        No content
    """
    await service.remove_member(org_id, member_id, current_user.get("id")) 