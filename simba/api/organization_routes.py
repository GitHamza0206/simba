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
from simba.auth.organization_service import OrganizationService

logger = logging.getLogger(__name__)

# Create router
organization_router = APIRouter(
    prefix="/organizations",
    tags=["organizations"]
)

@organization_router.get(
    "",
    response_model=List[Organization],
    summary="Get all organizations for the current user",
    description="Retrieve all organizations that the authenticated user is a member of"
)
async def get_organizations(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all organizations for the current user.
    
    Args:
        current_user: The authenticated user making the request
        
    Returns:
        List of organizations the user is a member of
    """
    try:
        # Get organizations for the current user
        organizations = await OrganizationService.get_organizations_for_user(
            user_id=current_user.id
        )
        return organizations
    except Exception as e:
        logger.error(f"Failed to get organizations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )

@organization_router.post(
    "",
    response_model=Organization,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
    description="Create a new organization and make the current user the owner"
)
async def create_organization(
    organization: OrganizationCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new organization.
    
    Args:
        organization: The organization to create
        current_user: The authenticated user making the request
        
    Returns:
        The created organization
    """
    try:
        # Create the organization and make the current user the owner
        organization = await OrganizationService.create_organization(
            name=organization.name,
            created_by=current_user.id
        )
        return organization
    except Exception as e:
        logger.error(f"Failed to create organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization"
        )

@organization_router.get(
    "/{org_id}",
    response_model=Organization,
    summary="Get organization by ID",
    description="Retrieve an organization by its ID, if the user is a member"
)
async def get_organization(
    org_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get an organization by ID.
    
    Args:
        org_id: The ID of the organization to retrieve
        current_user: The authenticated user making the request
        
    Returns:
        The organization if found and the user is a member
    """
    try:
        # Check if the user is a member of the organization
        is_member = await OrganizationService.is_org_member(
            org_id=org_id,
            user_id=current_user.id
        )
        
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Get the organization
        organization = await OrganizationService.get_organization_by_id(
            org_id=org_id
        )
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return organization
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization"
        )

@organization_router.get(
    "/{org_id}/members",
    response_model=List[OrganizationMember],
    summary="Get organization members",
    description="Retrieve all members of an organization, if the user is a member"
)
async def get_organization_members(
    org_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all members of an organization.
    
    Args:
        org_id: The ID of the organization
        current_user: The authenticated user making the request
        
    Returns:
        List of organization members
    """
    try:
        # Check if the user is a member of the organization
        is_member = await OrganizationService.is_org_member(
            org_id=org_id,
            user_id=current_user.id
        )
        
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Get the organization members
        members = await OrganizationService.get_organization_members(
            org_id=org_id
        )
        
        return members
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get organization members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization members"
        )

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
    current_user: UserResponse = Depends(get_current_user)
):
    """Invite a user to an organization.
    
    Args:
        org_id: The ID of the organization
        invite: The invitation details
        current_user: The authenticated user making the request
        
    Returns:
        The invited member
    """
    try:
        # Check if the user is a member of the organization
        user_role = await OrganizationService.get_user_role_in_org(
            org_id=org_id,
            user_id=current_user.id
        )
        
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Check if the user has appropriate permissions
        if user_role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to invite members"
            )
        
        # Invite the member
        member = await OrganizationService.invite_member(
            org_id=org_id,
            email=invite.email,
            role=invite.role,
            inviter_id=current_user.id
        )
        
        return member
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to invite member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite member"
        )

# Helper function to check owner permissions and get target member
async def _check_owner_and_get_target_member(
    org_id: str, target_member_id: str, current_user_id: str
) -> Tuple[OrganizationMember, List[OrganizationMember]]:
    """
    Checks if the current user is an owner of the organization,
    fetches the target member, and returns the target member and all members.

    Raises HTTPException for permission errors or if the member is not found.
    """
    user_role = await OrganizationService.get_user_role_in_org(
        org_id=org_id, user_id=current_user_id
    )

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    # Ensure the user performing the action is an owner
    if user_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can modify member roles or remove members",
        )

    # Fetch all members to find the target and check owner constraints later
    members = await OrganizationService.get_organization_members(org_id=org_id)
    target_member = next((m for m in members if m.id == target_member_id), None)

    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Target member not found"
        )

    return target_member, members

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
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a member's role in an organization.
    
    Args:
        org_id: The ID of the organization
        member_id: The ID of the member to update
        update: The update details
        current_user: The authenticated user making the request
        
    Returns:
        The updated member
    """
    try:
        # Check permissions and get the member to update + all members
        member_to_update, members = await _check_owner_and_get_target_member(
            org_id, member_id, current_user.id
        )

        # If member is an owner, only allow role change if there's at least one other owner
        if member_to_update.role == "owner" and update.role != "owner":
            owners = [m for m in members if m.role == "owner"]
            if len(owners) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change the role of the only owner"
                )

        # Update the member's role
        updated_member = await OrganizationService.update_member_role(
            org_id=org_id,
            member_id=member_id,
            new_role=update.role
        )

        if not updated_member:
            # This might occur if the member was deleted between checks, though unlikely.
            # Or if OrganizationService.update_member_role returns None on failure.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update member role, member might no longer exist."
            )

        return updated_member
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to update member role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update member role"
        )

@organization_router.delete(
    "/{org_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from an organization",
    description="Remove a member from an organization, if the current user is an owner"
)
async def remove_member(
    org_id: str,
    member_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Remove a member from an organization.
    
    Args:
        org_id: The ID of the organization
        member_id: The ID of the member to remove
        current_user: The authenticated user making the request
        
    Returns:
        No content
    """
    try:
        # Check permissions and get the member to remove + all members
        member_to_remove, members = await _check_owner_and_get_target_member(
            org_id, member_id, current_user.id
        )

        # If member is an owner, only allow removal if there's at least one other owner
        if member_to_remove.role == "owner":
            owners = [m for m in members if m.role == "owner"]
            if len(owners) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the only owner"
                )

        # Remove the member
        success = await OrganizationService.remove_member(
            org_id=org_id,
            member_id=member_id
        )

        if not success:
             # This might occur if the member was deleted between checks, though unlikely.
             # Or if OrganizationService.remove_member returns False on failure.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to remove member, member might no longer exist."
            )
        # Return No Content on success implicitly via status_code=204
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to remove member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        ) 