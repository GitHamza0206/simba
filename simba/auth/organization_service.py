import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import HTTPException, status

from simba.auth.role_service import RoleService
from simba.database.postgres import PostgresDB
from simba.models.organization import Organization, OrganizationMember, OrganizationWithMembers

logger = logging.getLogger(__name__)


class OrganizationService:
    """Service for managing organizations and their members."""

    @staticmethod
    def get_organizations_for_user(user_id: str) -> List[Organization]:
        """Get all organizations for a specific user.

        Args:
            user_id (str): The ID of the user

        Returns:
            List[Organization]: List of organizations the user is a member of
        """
        try:
            # Query all organizations where the user is a member
            rows = PostgresDB.fetch_all(
                """
                SELECT o.id, o.name, o.created_at, o.created_by
                FROM organizations o
                JOIN organization_members om ON o.id = om.organization_id
                WHERE om.user_id = %s
            """,
                (user_id,),
            )

            # Map rows to Organization models
            organizations = [
                Organization(
                    id=row["id"],
                    name=row["name"],
                    created_at=row["created_at"],
                    created_by=row["created_by"],
                )
                for row in rows
            ]

            return organizations
        except Exception as e:
            logger.error(f"Failed to get organizations for user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organizations",
            )

    @staticmethod
    def get_organization_by_id(org_id: str) -> Optional[Organization]:
        """Get organization by ID.

        Args:
            org_id (str): The ID of the organization

        Returns:
            Optional[Organization]: Organization if found, None otherwise
        """
        try:
            # Query the organization
            row = PostgresDB.fetch_one(
                """
                SELECT id, name, created_at, created_by
                FROM organizations
                WHERE id = %s
            """,
                (org_id,),
            )

            if not row:
                return None

            return Organization(
                id=row["id"],
                name=row["name"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
        except Exception as e:
            logger.error(f"Failed to get organization by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization",
            )

    @staticmethod
    def create_organization(name: str, created_by: str) -> Organization:
        """Create a new organization and make the creator the owner.

        Args:
            name (str): The name of the organization
            created_by (str): The ID of the user creating the organization

        Returns:
            Organization: The created organization
        """
        try:
            conn = PostgresDB.get_connection()
            try:
                # Generate a new UUID for the organization
                org_id = str(uuid4())
                created_at = datetime.now()

                # Insert the organization
                with conn.cursor() as cursor:
                    # Insert the organization
                    cursor.execute(
                        """
                        INSERT INTO organizations (id, name, created_at, created_by)
                        VALUES (%s, %s, %s, %s)
                    """,
                        (org_id, name, created_at, created_by),
                    )

                    # Get user email
                    cursor.execute(
                        """
                        SELECT email FROM auth.users WHERE id = %s
                    """,
                        (created_by,),
                    )
                    user_row = cursor.fetchone()

                    if not user_row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                        )

                    email = user_row["email"]

                    # Generate a new UUID for the member
                    member_id = str(uuid4())

                    # Add the creator as an owner
                    cursor.execute(
                        """
                        INSERT INTO organization_members (id, organization_id, user_id, email, role, joined_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (member_id, org_id, created_by, email, "owner", created_at),
                    )

                # Commit the transaction
                conn.commit()

                return Organization(
                    id=org_id, name=name, created_at=created_at, created_by=created_by
                )
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to create organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization",
            )

    @staticmethod
    def get_organization_members(org_id: str) -> List[OrganizationMember]:
        """Get all members of an organization.

        Args:
            org_id (str): The ID of the organization

        Returns:
            List[OrganizationMember]: List of organization members
        """
        try:
            # Query all members of the organization
            rows = PostgresDB.fetch_all(
                """
                SELECT id, organization_id, user_id, email, role, joined_at
                FROM organization_members
                WHERE organization_id = %s
            """,
                (org_id,),
            )

            # Map rows to OrganizationMember models
            members = [
                OrganizationMember(
                    id=row["id"],
                    organization_id=row["organization_id"],
                    user_id=row["user_id"],
                    email=row["email"],
                    role=row["role"],
                    joined_at=row["joined_at"],
                )
                for row in rows
            ]

            return members
        except Exception as e:
            logger.error(f"Failed to get organization members: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve organization members",
            )

    @staticmethod
    def is_org_member(org_id: str, user_id: str) -> bool:
        """Check if a user is a member of an organization.

        Args:
            org_id (str): The ID of the organization
            user_id (str): The ID of the user

        Returns:
            bool: True if the user is a member, False otherwise
        """
        try:
            # Check if the user is a member of the organization
            row = PostgresDB.fetch_one(
                """
                SELECT 1
                FROM organization_members
                WHERE organization_id = %s AND user_id = %s
            """,
                (org_id, user_id),
            )

            return row is not None
        except Exception as e:
            logger.error(f"Failed to check organization membership: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check organization membership",
            )

    @staticmethod
    def get_user_role_in_org(org_id: str, user_id: str) -> Optional[str]:
        """Get the role of a user in an organization.

        Args:
            org_id (str): The ID of the organization
            user_id (str): The ID of the user

        Returns:
            Optional[str]: The role of the user in the organization if found, None otherwise
        """
        try:
            # Get the user's role in the organization
            row = PostgresDB.fetch_one(
                """
                SELECT role
                FROM organization_members
                WHERE organization_id = %s AND user_id = %s
            """,
                (org_id, user_id),
            )

            if not row:
                return None

            return row["role"]
        except Exception as e:
            logger.error(f"Failed to get user role in organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user role in organization",
            )

    @staticmethod
    def invite_member(org_id: str, email: str, role: str, inviter_id: str) -> OrganizationMember:
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
            conn = PostgresDB.get_connection()
            try:
                with conn.cursor() as cursor:
                    # Check if the organization exists
                    cursor.execute(
                        """
                        SELECT 1 FROM organizations WHERE id = %s
                    """,
                        (org_id,),
                    )
                    org_row = cursor.fetchone()

                    if not org_row:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
                        )

                    # Get the user's ID if they already exist
                    cursor.execute(
                        """
                        SELECT id FROM auth.users WHERE email = %s
                    """,
                        (email,),
                    )
                    user_row = cursor.fetchone()

                    user_id = user_row["id"] if user_row else None

                    # Check if the user is already a member
                    if user_id:
                        cursor.execute(
                            """
                            SELECT 1 FROM organization_members
                            WHERE organization_id = %s AND user_id = %s
                        """,
                            (org_id, user_id),
                        )
                        existing_member = cursor.fetchone()

                        if existing_member:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="User is already a member of this organization",
                            )

                    # Check if the email is already invited
                    cursor.execute(
                        """
                        SELECT 1 FROM organization_members
                        WHERE organization_id = %s AND email = %s AND user_id IS NULL
                    """,
                        (org_id, email),
                    )
                    existing_invite = cursor.fetchone()

                    if existing_invite:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="User is already invited to this organization",
                        )

                    # Generate a new UUID for the member
                    member_id = str(uuid4())
                    joined_at = datetime.now()

                    # Insert the member
                    cursor.execute(
                        """
                        INSERT INTO organization_members (id, organization_id, user_id, email, role, joined_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                        (member_id, org_id, user_id, email, role, joined_at),
                    )

                # Commit the transaction
                conn.commit()

                return OrganizationMember(
                    id=member_id,
                    organization_id=org_id,
                    user_id=user_id if user_id else "",
                    email=email,
                    role=role,
                    joined_at=joined_at,
                )
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to invite member to organization: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to invite member to organization",
            )

    @staticmethod
    def update_member_role(
        org_id: str, member_id: str, new_role: str
    ) -> Optional[OrganizationMember]:
        """Update a member's role in an organization.

        Args:
            org_id (str): The ID of the organization
            member_id (str): The ID of the member
            new_role (str): The new role to assign

        Returns:
            Optional[OrganizationMember]: The updated member if found, None otherwise
        """
        try:
            conn = PostgresDB.get_connection()
            try:
                with conn.cursor() as cursor:
                    # Check if the member exists
                    cursor.execute(
                        """
                        SELECT id, organization_id, user_id, email, role, joined_at
                        FROM organization_members
                        WHERE id = %s AND organization_id = %s
                    """,
                        (member_id, org_id),
                    )
                    member_row = cursor.fetchone()

                    if not member_row:
                        return None

                    # Update the member's role
                    cursor.execute(
                        """
                        UPDATE organization_members
                        SET role = %s
                        WHERE id = %s AND organization_id = %s
                    """,
                        (new_role, member_id, org_id),
                    )

                    # Get the updated member
                    cursor.execute(
                        """
                        SELECT id, organization_id, user_id, email, role, joined_at
                        FROM organization_members
                        WHERE id = %s AND organization_id = %s
                    """,
                        (member_id, org_id),
                    )
                    updated_row = cursor.fetchone()

                # Commit the transaction
                conn.commit()

                return OrganizationMember(
                    id=updated_row["id"],
                    organization_id=updated_row["organization_id"],
                    user_id=updated_row["user_id"],
                    email=updated_row["email"],
                    role=updated_row["role"],
                    joined_at=updated_row["joined_at"],
                )
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Failed to update member role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update member role",
            )

    @staticmethod
    def remove_member(org_id: str, member_id: str) -> bool:
        """Remove a member from an organization.

        Args:
            org_id (str): The ID of the organization
            member_id (str): The ID of the member

        Returns:
            bool: True if the member was removed, False otherwise
        """
        try:
            # Check if the member exists and then remove them
            result = PostgresDB.execute_query(
                """
                DELETE FROM organization_members
                WHERE id = %s AND organization_id = %s
                AND EXISTS (
                    SELECT 1 FROM organization_members
                    WHERE id = %s AND organization_id = %s
                )
            """,
                (member_id, org_id, member_id, org_id),
            )

            return result > 0
        except Exception as e:
            logger.error(f"Failed to remove member from organization: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove member from organization",
            )
