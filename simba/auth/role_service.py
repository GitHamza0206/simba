import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from simba.database.postgres import PostgresDB
from simba.models.role import Permission, Role, UserRole

logger = logging.getLogger(__name__)


class RoleService:
    """Service for managing roles and permissions."""

    @staticmethod
    def get_roles() -> List[Role]:
        """Get all roles.

        Returns:
            List[Role]: List of roles
        """
        try:
            # Query all roles using PostgresDB
            rows = PostgresDB.fetch_all(
                """
                SELECT id, name, description, created_at
                FROM roles
                ORDER BY name
            """
            )

            # Convert rows to Role objects
            roles = [
                Role(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            return roles
        except Exception as e:
            logger.error(f"Failed to get roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch roles"
            )

    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """Get a role by ID.

        Args:
            role_id: Role ID

        Returns:
            Optional[Role]: Role if found, None otherwise
        """
        try:
            # Query role by ID using PostgresDB
            row = PostgresDB.fetch_one(
                """
                SELECT id, name, description, created_at
                FROM roles
                WHERE id = %s
            """,
                (role_id,),
            )

            if not row:
                return None

            return Role(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
            )
        except Exception as e:
            logger.error(f"Failed to get role by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch role"
            )

    @staticmethod
    def get_role_by_name(role_name: str) -> Optional[Role]:
        """Get a role by name.

        Args:
            role_name: Role name

        Returns:
            Optional[Role]: Role if found, None otherwise
        """
        try:
            # Query role by name using PostgresDB
            row = PostgresDB.fetch_one(
                """
                SELECT id, name, description, created_at
                FROM roles
                WHERE name = %s
            """,
                (role_name,),
            )

            if not row:
                return None

            return Role(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
            )
        except Exception as e:
            logger.error(f"Failed to get role by name: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch role"
            )

    @staticmethod
    def create_role(name: str, description: Optional[str] = None) -> Role:
        """Create a new role.

        Args:
            name: Role name
            description: Role description

        Returns:
            Role: Created role
        """
        try:
            # Check if role already exists using PostgresDB
            existing = PostgresDB.fetch_one("SELECT id FROM roles WHERE name = %s", (name,))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{name}' already exists",
                )

            # Insert new role using PostgresDB
            row = PostgresDB.fetch_one(
                """
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                RETURNING id, name, description, created_at
            """,
                (name, description),
            )

            return Role(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create role"
            )

    @staticmethod
    def update_role(
        role_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> Optional[Role]:
        """Update a role.

        Args:
            role_id: Role ID
            name: New role name
            description: New role description

        Returns:
            Optional[Role]: Updated role if found, None otherwise
        """
        try:
            if not name and not description:
                return RoleService.get_role_by_id(role_id)

            # Check if role exists using PostgresDB
            existing = PostgresDB.fetch_one("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not existing:
                return None

            updates = []
            params = []

            if name:
                # Check if name is already taken by another role using PostgresDB
                name_check = PostgresDB.fetch_one(
                    "SELECT id FROM roles WHERE name = %s AND id != %s", (name, role_id)
                )
                if name_check:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Role with name '{name}' already exists",
                    )
                updates.append("name = %s")
                params.append(name)

            if description is not None:  # Allow empty description
                updates.append("description = %s")
                params.append(description)

            # Add role_id to params
            params.append(role_id)

            # Update role using PostgresDB
            query = f"""
                UPDATE roles
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, name, description, created_at
            """

            row = PostgresDB.fetch_one(query, tuple(params))

            return Role(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update role"
            )

    @staticmethod
    def delete_role(role_id: int) -> bool:
        """Delete a role.

        Args:
            role_id: Role ID

        Returns:
            bool: True if role was deleted, False otherwise
        """
        try:
            # Delete role using PostgresDB
            result = PostgresDB.execute_query("DELETE FROM roles WHERE id = %s", (role_id,))

            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete role"
            )

    @staticmethod
    def get_user_roles(user_id: str) -> List[Role]:
        """Get all roles for a user.

        Args:
            user_id: User ID

        Returns:
            List[Role]: List of roles assigned to the user
        """
        try:
            # Get roles for user with a JOIN query
            rows = PostgresDB.fetch_all(
                """
                SELECT r.id, r.name, r.description, r.created_at
                FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = %s
                ORDER BY r.name
            """,
                (user_id,),
            )

            # Convert to Role objects
            roles = [
                Role(
                    id=row["id"],
                    name=row["name"],
                    description=row.get("description"),
                    created_at=row.get("created_at"),
                )
                for row in rows
            ]

            return roles
        except Exception as e:
            logger.error(f"Failed to get user roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user roles",
            )

    @staticmethod
    def assign_role_to_user(user_id: str, role_id: int) -> UserRole:
        """Assign a role to a user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            UserRole: Created user role
        """
        try:
            # Check if role exists using PostgresDB
            role = PostgresDB.fetch_one("SELECT id FROM roles WHERE id = %s", (role_id,))
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with ID {role_id} not found",
                )

            # Check if user already has this role using PostgresDB
            existing = PostgresDB.fetch_one(
                "SELECT user_id, role_id FROM user_roles WHERE user_id = %s AND role_id = %s",
                (user_id, role_id),
            )

            if existing:
                # User already has this role
                return UserRole(user_id=user_id, role_id=role_id)

            # Assign role to user using PostgresDB
            PostgresDB.execute_query(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id)
            )

            return UserRole(user_id=user_id, role_id=role_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign role to user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role to user",
            )

    @staticmethod
    def remove_role_from_user(user_id: str, role_id: int) -> bool:
        """Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            bool: True if role was removed, False otherwise
        """
        try:
            # Remove role from user using PostgresDB
            result = PostgresDB.execute_query(
                "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s", (user_id, role_id)
            )

            return result > 0
        except Exception as e:
            logger.error(f"Failed to remove role from user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove role from user",
            )

    @staticmethod
    def has_role(user_id: str, role_name: str) -> bool:
        """Check if a user has a specific role.

        Args:
            user_id: User ID
            role_name: Role name to check

        Returns:
            bool: True if user has the role, False otherwise
        """
        try:
            # Check if user has role with a JOIN query
            row = PostgresDB.fetch_one(
                """
                SELECT 1
                FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = %s AND r.name = %s
                LIMIT 1
            """,
                (user_id, role_name),
            )

            return row is not None
        except Exception as e:
            logger.error(f"Failed to check user role: {str(e)}")
            return False

    @staticmethod
    def has_permission(user_id: str, permission_name: str) -> bool:
        """Check if a user has a specific permission through any of their roles.

        Args:
            user_id: User ID
            permission_name: Permission name to check

        Returns:
            bool: True if user has the permission, False otherwise
        """
        try:
            # Check if user has permission with a JOIN query
            row = PostgresDB.fetch_one(
                """
                SELECT 1
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = %s AND p.name = %s
                LIMIT 1
            """,
                (user_id, permission_name),
            )

            return row is not None
        except Exception as e:
            logger.error(f"Failed to check user permission: {str(e)}")
            return False

    @staticmethod
    def get_permissions() -> List[Permission]:
        """Get all permissions.

        Returns:
            List[Permission]: List of permissions
        """
        try:
            # Query all permissions using PostgresDB
            rows = PostgresDB.fetch_all(
                """
                SELECT id, name, description
                FROM permissions
                ORDER BY name
            """
            )

            # Convert rows to Permission objects
            permissions = [
                Permission(id=row["id"], name=row["name"], description=row["description"])
                for row in rows
            ]

            return permissions
        except Exception as e:
            logger.error(f"Failed to get permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permissions",
            )

    @staticmethod
    def get_role_permissions(role_id: int) -> List[Permission]:
        """Get permissions for a role.

        Args:
            role_id: Role ID

        Returns:
            List[Permission]: List of role permissions
        """
        try:
            # Query role permissions using PostgresDB
            rows = PostgresDB.fetch_all(
                """
                SELECT p.id, p.name, p.description
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role_id = %s
                ORDER BY p.name
            """,
                (role_id,),
            )

            # Convert rows to Permission objects
            permissions = [
                Permission(id=row["id"], name=row["name"], description=row["description"])
                for row in rows
            ]

            return permissions
        except Exception as e:
            logger.error(f"Failed to get role permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch role permissions",
            )

    @staticmethod
    def get_user_permissions(user_id: str) -> List[Permission]:
        """Get all permissions for a user through their roles.

        Args:
            user_id: User ID

        Returns:
            List[Permission]: List of permissions the user has
        """
        try:
            # Get user permissions with a JOIN query
            rows = PostgresDB.fetch_all(
                """
                SELECT DISTINCT p.id, p.name, p.description
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = %s
                ORDER BY p.name
            """,
                (user_id,),
            )

            # Convert to Permission objects
            permissions = [
                Permission(id=row["id"], name=row["name"], description=row.get("description"))
                for row in rows
            ]

            return permissions
        except Exception as e:
            logger.error(f"Failed to get user permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user permissions",
            )
