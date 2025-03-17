import logging
from typing import Dict, List, Optional, Tuple, Any
import os
from datetime import datetime
from uuid import uuid4

import asyncpg
from asyncpg import Connection
from fastapi import HTTPException, status

from simba.auth.supabase_client import get_supabase_client
from simba.auth.role_service import RoleService
from simba.models.organization import Organization, OrganizationMember, OrganizationWithMembers
from simba.core.config import settings

logger = logging.getLogger(__name__)

class OrganizationService:
    """Service for managing organizations and their members."""
    
    @staticmethod
    async def get_db_connection() -> Connection:
        """Get a database connection.
        
        Returns:
            asyncpg.Connection: Database connection
        """
        try:
            # Get Supabase connection string from settings
            connection_string = f"postgresql://{settings.supabase.db_user}:{settings.supabase.db_password}@{settings.supabase.db_host}:{settings.supabase.db_port}/{settings.supabase.db_name}"
            
            # Connect to the database
            connection = await asyncpg.connect(connection_string)
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection failed"
            )
    
    @staticmethod
    async def get_organizations_for_user(user_id: str) -> List[Organization]:
        """Get all organizations for a specific user.
        
        Args:
            user_id (str): The ID of the user
            
        Returns:
            List[Organization]: List of organizations the user is a member of
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Query all organizations where the user is a member
            rows = await conn.fetch("""
                SELECT o.id, o.name, o.created_at, o.created_by
                FROM organizations o
                JOIN organization_members om ON o.id = om.organization_id
                WHERE om.user_id = $1
            """, user_id)
            
            await conn.close()
            
            # Map rows to Organization models
            organizations = [
                Organization(
                    id=row["id"],
                    name=row["name"],
                    created_at=row["created_at"],
                    created_by=row["created_by"]
                )
                for row in rows
            ]
            
            return organizations
        except Exception as e:
            logger.error(f"Failed to get organizations for user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organizations"
            )
    
    @staticmethod
    async def get_organization_by_id(org_id: str) -> Optional[Organization]:
        """Get organization by ID.
        
        Args:
            org_id (str): The ID of the organization
            
        Returns:
            Optional[Organization]: Organization if found, None otherwise
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Query the organization
            row = await conn.fetchrow("""
                SELECT id, name, created_at, created_by
                FROM organizations
                WHERE id = $1
            """, org_id)
            
            await conn.close()
            
            if not row:
                return None
            
            return Organization(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"],
                created_by=row["created_by"]
            )
        except Exception as e:
            logger.error(f"Failed to get organization by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization"
            )
    
    @staticmethod
    async def create_organization(name: str, created_by: str) -> Organization:
        """Create a new organization and make the creator the owner.
        
        Args:
            name (str): The name of the organization
            created_by (str): The ID of the user creating the organization
            
        Returns:
            Organization: The created organization
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Start a transaction
            async with conn.transaction():
                # Generate a new UUID for the organization
                org_id = str(uuid4())
                created_at = datetime.now()
                
                # Insert the organization
                await conn.execute("""
                    INSERT INTO organizations (id, name, created_at, created_by)
                    VALUES ($1, $2, $3, $4)
                """, org_id, name, created_at, created_by)
                
                # Get user email
                user_row = await conn.fetchrow("""
                    SELECT email FROM auth.users WHERE id = $1
                """, created_by)
                
                if not user_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                email = user_row["email"]
                
                # Generate a new UUID for the member
                member_id = str(uuid4())
                
                # Add the creator as an owner
                await conn.execute("""
                    INSERT INTO organization_members (id, organization_id, user_id, email, role, joined_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, member_id, org_id, created_by, email, "owner", created_at)
            
            await conn.close()
            
            return Organization(
                id=org_id,
                name=name,
                created_at=created_at,
                created_by=created_by
            )
        except Exception as e:
            logger.error(f"Failed to create organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
    
    @staticmethod
    async def get_organization_members(org_id: str) -> List[OrganizationMember]:
        """Get all members of an organization.
        
        Args:
            org_id (str): The ID of the organization
            
        Returns:
            List[OrganizationMember]: List of organization members
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Query all members of the organization
            rows = await conn.fetch("""
                SELECT id, organization_id, user_id, email, role, joined_at
                FROM organization_members
                WHERE organization_id = $1
            """, org_id)
            
            await conn.close()
            
            # Map rows to OrganizationMember models
            members = [
                OrganizationMember(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    user_id=row["user_id"],
                    email=row["email"],
                    role=row["role"],
                    joined_at=row["joined_at"]
                )
                for row in rows
            ]
            
            return members
        except Exception as e:
            logger.error(f"Failed to get organization members: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization members"
            )
    
    @staticmethod
    async def is_org_member(org_id: str, user_id: str) -> bool:
        """Check if a user is a member of an organization.
        
        Args:
            org_id (str): The ID of the organization
            user_id (str): The ID of the user
            
        Returns:
            bool: True if the user is a member, False otherwise
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Check if the user is a member of the organization
            row = await conn.fetchrow("""
                SELECT 1
                FROM organization_members
                WHERE organization_id = $1 AND user_id = $2
            """, org_id, user_id)
            
            await conn.close()
            
            return row is not None
        except Exception as e:
            logger.error(f"Failed to check organization membership: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check organization membership"
            )
    
    @staticmethod
    async def get_user_role_in_org(org_id: str, user_id: str) -> Optional[str]:
        """Get the role of a user in an organization.
        
        Args:
            org_id (str): The ID of the organization
            user_id (str): The ID of the user
            
        Returns:
            Optional[str]: The role of the user in the organization if found, None otherwise
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Get the user's role in the organization
            row = await conn.fetchrow("""
                SELECT role
                FROM organization_members
                WHERE organization_id = $1 AND user_id = $2
            """, org_id, user_id)
            
            await conn.close()
            
            if not row:
                return None
            
            return row["role"]
        except Exception as e:
            logger.error(f"Failed to get user role in organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user role in organization"
            )
    
    @staticmethod
    async def invite_member(org_id: str, email: str, role: str, inviter_id: str) -> OrganizationMember:
        """Invite a member to an organization.
        
        Args:
            org_id (str): The ID of the organization
            email (str): The email of the user to invite
            role (str): The role to assign to the user
            inviter_id (str): The ID of the user sending the invitation
            
        Returns:
            OrganizationMember: The invited member
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Start a transaction
            async with conn.transaction():
                # Check if the organization exists
                org_row = await conn.fetchrow("""
                    SELECT 1 FROM organizations WHERE id = $1
                """, org_id)
                
                if not org_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organization not found"
                    )
                
                # Get the user's ID if they already exist
                user_row = await conn.fetchrow("""
                    SELECT id FROM auth.users WHERE email = $1
                """, email)
                
                user_id = user_row["id"] if user_row else None
                
                # Check if the user is already a member
                if user_id:
                    existing_member = await conn.fetchrow("""
                        SELECT 1 FROM organization_members
                        WHERE organization_id = $1 AND user_id = $2
                    """, org_id, user_id)
                    
                    if existing_member:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User is already a member of this organization"
                        )
                
                # Check if the email is already invited
                existing_invite = await conn.fetchrow("""
                    SELECT 1 FROM organization_members
                    WHERE organization_id = $1 AND email = $2 AND user_id IS NULL
                """, org_id, email)
                
                if existing_invite:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User is already invited to this organization"
                    )
                
                # Generate a new UUID for the member
                member_id = str(uuid4())
                joined_at = datetime.now()
                
                # Insert the member
                await conn.execute("""
                    INSERT INTO organization_members (id, organization_id, user_id, email, role, joined_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, member_id, org_id, user_id, email, role, joined_at)
            
            await conn.close()
            
            return OrganizationMember(
                id=member_id,
                organization_id=org_id,
                user_id=user_id if user_id else "",
                email=email,
                role=role,
                joined_at=joined_at
            )
        except Exception as e:
            logger.error(f"Failed to invite member to organization: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite member to organization"
            )
    
    @staticmethod
    async def update_member_role(org_id: str, member_id: str, new_role: str) -> Optional[OrganizationMember]:
        """Update a member's role in an organization.
        
        Args:
            org_id (str): The ID of the organization
            member_id (str): The ID of the member
            new_role (str): The new role to assign
            
        Returns:
            Optional[OrganizationMember]: The updated member if found, None otherwise
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Start a transaction
            async with conn.transaction():
                # Check if the member exists
                member_row = await conn.fetchrow("""
                    SELECT id, organization_id, user_id, email, role, joined_at
                    FROM organization_members
                    WHERE id = $1 AND organization_id = $2
                """, member_id, org_id)
                
                if not member_row:
                    return None
                
                # Update the member's role
                await conn.execute("""
                    UPDATE organization_members
                    SET role = $1
                    WHERE id = $2 AND organization_id = $3
                """, new_role, member_id, org_id)
                
                # Get the updated member
                updated_row = await conn.fetchrow("""
                    SELECT id, organization_id, user_id, email, role, joined_at
                    FROM organization_members
                    WHERE id = $1 AND organization_id = $2
                """, member_id, org_id)
            
            await conn.close()
            
            return OrganizationMember(
                id=updated_row["id"],
                organization_id=updated_row["organization_id"],
                user_id=updated_row["user_id"],
                email=updated_row["email"],
                role=updated_row["role"],
                joined_at=updated_row["joined_at"]
            )
        except Exception as e:
            logger.error(f"Failed to update member role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member role"
            )
    
    @staticmethod
    async def remove_member(org_id: str, member_id: str) -> bool:
        """Remove a member from an organization.
        
        Args:
            org_id (str): The ID of the organization
            member_id (str): The ID of the member
            
        Returns:
            bool: True if the member was removed, False otherwise
        """
        try:
            conn = await OrganizationService.get_db_connection()
            
            # Start a transaction
            async with conn.transaction():
                # Check if the member exists
                member_row = await conn.fetchrow("""
                    SELECT 1
                    FROM organization_members
                    WHERE id = $1 AND organization_id = $2
                """, member_id, org_id)
                
                if not member_row:
                    return False
                
                # Remove the member
                await conn.execute("""
                    DELETE FROM organization_members
                    WHERE id = $1 AND organization_id = $2
                """, member_id, org_id)
            
            await conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Failed to remove member from organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member from organization"
            ) 