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
    current_user: dict = Depends(get_current_user)
):
    """Get all organizations for the current user.
    
    Args:
        current_user: The authenticated user making the request
        
    Returns:
        List of organizations the user is a member of
    """
    try:
        # RLS will automatically filter to only show organizations where user is a member
        supabase = get_supabase_client()
        response = supabase.table('organizations').select('*').execute()
        
        if hasattr(response, 'error') and response.error:
            logger.error(f"Supabase error: {response.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organizations"
            )
            
        return response.data
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
    current_user: dict = Depends(get_current_user)
):
    """Create a new organization.
    
    Args:
        organization: The organization to create
        current_user: The authenticated user making the request
        
    Returns:
        The created organization
    """
    try:
        supabase = get_supabase_client()
        
        # Generate a new UUID for the organization
        org_id = str(uuid4())
        
        # Insert organization record (RLS enforces that created_by = auth.uid())
        org_response = supabase.table('organizations').insert({
            'id': org_id,
            'name': organization.name,
            'created_by': current_user.get("id")
        }).execute()
        
        if hasattr(org_response, 'error') and org_response.error:
            logger.error(f"Supabase error: {org_response.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
        
        # Add current user as owner
        member_id = str(uuid4())
        member_response = supabase.table('organization_members').insert({
            'id': member_id,
            'organization_id': org_id,
            'user_id': current_user.get("id"),
            'email': current_user.get("email"),
            'role': 'owner'
        }).execute()
        
        if hasattr(member_response, 'error') and member_response.error:
            logger.error(f"Supabase error: {member_response.error}")
            # Try to clean up the organization we just created
            supabase.table('organizations').delete().eq('id', org_id).execute()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user as organization owner"
            )
        
        return org_response.data[0]
    except HTTPException:
        raise
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
    current_user: dict = Depends(get_current_user)
):
    """Get an organization by ID.
    
    Args:
        org_id: The ID of the organization to retrieve
        current_user: The authenticated user making the request
        
    Returns:
        The organization if found and the user is a member
    """
    try:
        # RLS will automatically check if user is a member of this organization
        supabase = get_supabase_client()
        response = supabase.table('organizations').select('*').eq('id', org_id).single().execute()
        
        # Handle not found or permission denied
        if hasattr(response, 'error') and response.error:
            if "not found" in str(response.error).lower() or response.data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Organization not found"
                )
            
            # If error isn't "not found", then it might be a permissions issue
            logger.error(f"Supabase error: {response.error}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
        
        # Return the organization
        return response.data
    except HTTPException:
        raise
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
    current_user: dict = Depends(get_current_user)
):
    """Get all members of an organization.
    
    Args:
        org_id: The ID of the organization
        current_user: The authenticated user making the request
        
    Returns:
        List of organization members
    """
    try:
        # RLS will automatically check if user is a member of this organization
        supabase = get_supabase_client()
        response = supabase.table('organization_members').select('*').eq('organization_id', org_id).execute()
        
        # If the response is empty because user isn't a member, we'll get an empty list not an error
        # We can specifically check if the user is a member of the org first
        is_member_check = supabase.table('organization_members').select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.get("id")) \
            .single().execute()
            
        if hasattr(is_member_check, 'error') or not is_member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
            
        return response.data
    except HTTPException:
        raise
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
    current_user: dict = Depends(get_current_user)
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
        supabase = get_supabase_client()
        
        # Check if the user has appropriate permissions (owner or admin)
        role_check = supabase.table('organization_members').select('role') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.get("id")) \
            .single().execute()
            
        if hasattr(role_check, 'error') or not role_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
            
        user_role = role_check.data.get('role')
        if user_role not in ['owner', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to invite members"
            )
        
        # Check if the email is already a member
        existing_check = supabase.table('organization_members').select('id') \
            .eq('organization_id', org_id) \
            .eq('email', invite.email) \
            .single().execute()
            
        if not hasattr(existing_check, 'error') and existing_check.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already a member of the organization"
            )
        
        # Create the invitation (RLS automatically enforces permissions)
        member_id = str(uuid4())
        invite_response = supabase.table('organization_members').insert({
            'id': member_id,
            'organization_id': org_id,
            'email': invite.email,
            'role': invite.role,
            'user_id': None  # Will be filled when user accepts invitation
        }).execute()
        
        if hasattr(invite_response, 'error') and invite_response.error:
            logger.error(f"Supabase error: {invite_response.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite member"
            )
        
        # TODO: Send invitation email to the user
        
        return invite_response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invite member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invite member"
        )

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
    current_user: dict = Depends(get_current_user)
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
        supabase = get_supabase_client()
        
        # Check if the current user is an owner (RLS will handle permissions)
        role_check = supabase.table('organization_members').select('role') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.get("id")) \
            .single().execute()
            
        if hasattr(role_check, 'error') or not role_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
            
        user_role = role_check.data.get('role')
        if user_role != 'owner':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners can modify member roles"
            )
            
        # Get the member to update
        member_to_update = supabase.table('organization_members').select('*') \
            .eq('id', member_id) \
            .eq('organization_id', org_id) \
            .single().execute()
            
        if hasattr(member_to_update, 'error') or not member_to_update.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Target member not found"
            )
            
        # If member is an owner, only allow role change if there's at least one other owner
        if member_to_update.data.get('role') == 'owner' and update.role != 'owner':
            # Count owners in this organization
            owners_count = supabase.table('organization_members').select('id', 'count') \
                .eq('organization_id', org_id) \
                .eq('role', 'owner') \
                .execute()
                
            if not hasattr(owners_count, 'error') and owners_count.count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change the role of the only owner"
                )
        
        # Update the member's role (RLS will enforce permissions)
        updated_member = supabase.table('organization_members').update({
            'role': update.role
        }).eq('id', member_id).eq('organization_id', org_id).single().execute()
        
        if hasattr(updated_member, 'error') or not updated_member.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update member role"
            )
            
        return updated_member.data
    except HTTPException:
        raise
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
    current_user: dict = Depends(get_current_user)
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
        supabase = get_supabase_client()
        
        # Check if the current user is an owner
        role_check = supabase.table('organization_members').select('role') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.get("id")) \
            .single().execute()
            
        if hasattr(role_check, 'error') or not role_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization"
            )
            
        user_role = role_check.data.get('role')
        if user_role != 'owner':
            # Check if user is trying to remove themselves
            if member_id != role_check.data.get('id'):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only owners can remove members"
                )
        
        # Get the member to remove
        member_to_remove = supabase.table('organization_members').select('*') \
            .eq('id', member_id) \
            .eq('organization_id', org_id) \
            .single().execute()
            
        if hasattr(member_to_remove, 'error') or not member_to_remove.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target member not found"
            )
            
        # If member is an owner, only allow removal if there's at least one other owner
        if member_to_remove.data.get('role') == 'owner':
            # Count owners in this organization
            owners_query = supabase.table('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .eq('role', 'owner') \
                .execute()
                
            owners_count = owners_query.count
            if owners_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the only owner"
                )
        
        # Delete the member (RLS will enforce permissions)
        result = supabase.table('organization_members').delete() \
            .eq('id', member_id) \
            .eq('organization_id', org_id) \
            .execute()
            
        if hasattr(result, 'error'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member"
            )
        
        # Return No Content on success implicitly via status_code=204
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove member"
        ) 