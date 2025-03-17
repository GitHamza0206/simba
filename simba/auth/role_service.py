import logging
from typing import Dict, List, Optional, Tuple, Any
import os

import asyncpg
from asyncpg import Connection
from fastapi import HTTPException, status

from simba.auth.supabase_client import get_supabase_client
from simba.models.role import Role, Permission, RoleWithPermissions, UserRole
from simba.core.config import settings

logger = logging.getLogger(__name__)

class RoleService:
    """Service for managing roles and permissions."""
    
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
    async def get_roles() -> List[Role]:
        """Get all roles.
        
        Returns:
            List[Role]: List of roles
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query all roles
            rows = await conn.fetch("""
                SELECT id, name, description, created_at
                FROM roles
                ORDER BY name
            """)
            
            await conn.close()
            
            # Convert rows to Role objects
            roles = [
                Role(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            return roles
        except Exception as e:
            logger.error(f"Failed to get roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch roles"
            )
    
    @staticmethod
    async def get_role_by_id(role_id: int) -> Optional[Role]:
        """Get a role by ID.
        
        Args:
            role_id: Role ID
        
        Returns:
            Optional[Role]: Role if found, None otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query role by ID
            row = await conn.fetchrow("""
                SELECT id, name, description, created_at
                FROM roles
                WHERE id = $1
            """, role_id)
            
            await conn.close()
            
            if not row:
                return None
            
            return Role(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at']
            )
        except Exception as e:
            logger.error(f"Failed to get role by ID: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch role"
            )
    
    @staticmethod
    async def get_role_by_name(role_name: str) -> Optional[Role]:
        """Get a role by name.
        
        Args:
            role_name: Role name
        
        Returns:
            Optional[Role]: Role if found, None otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query role by name
            row = await conn.fetchrow("""
                SELECT id, name, description, created_at
                FROM roles
                WHERE name = $1
            """, role_name)
            
            await conn.close()
            
            if not row:
                return None
            
            return Role(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at']
            )
        except Exception as e:
            logger.error(f"Failed to get role by name: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch role"
            )
    
    @staticmethod
    async def create_role(name: str, description: Optional[str] = None) -> Role:
        """Create a new role.
        
        Args:
            name: Role name
            description: Role description
        
        Returns:
            Role: Created role
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Check if role already exists
            existing = await conn.fetchrow("SELECT id FROM roles WHERE name = $1", name)
            if existing:
                await conn.close()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{name}' already exists"
                )
            
            # Insert new role
            row = await conn.fetchrow("""
                INSERT INTO roles (name, description)
                VALUES ($1, $2)
                RETURNING id, name, description, created_at
            """, name, description)
            
            await conn.close()
            
            return Role(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at']
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role"
            )
    
    @staticmethod
    async def update_role(role_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Optional[Role]:
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
                return await RoleService.get_role_by_id(role_id)
            
            conn = await RoleService.get_db_connection()
            
            # Check if role exists
            existing = await conn.fetchrow("SELECT id FROM roles WHERE id = $1", role_id)
            if not existing:
                await conn.close()
                return None
            
            updates = []
            params = [role_id]
            
            if name:
                # Check if name is already taken by another role
                name_check = await conn.fetchrow("SELECT id FROM roles WHERE name = $1 AND id != $2", name, role_id)
                if name_check:
                    await conn.close()
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Role with name '{name}' already exists"
                    )
                updates.append(f"name = ${len(params) + 1}")
                params.append(name)
            
            if description is not None:  # Allow empty description
                updates.append(f"description = ${len(params) + 1}")
                params.append(description)
            
            # Update role
            query = f"""
                UPDATE roles
                SET {', '.join(updates)}
                WHERE id = $1
                RETURNING id, name, description, created_at
            """
            
            row = await conn.fetchrow(query, *params)
            
            await conn.close()
            
            return Role(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                created_at=row['created_at']
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
    
    @staticmethod
    async def delete_role(role_id: int) -> bool:
        """Delete a role.
        
        Args:
            role_id: Role ID
        
        Returns:
            bool: True if role was deleted, False otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Delete role
            result = await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
            
            await conn.close()
            
            return "DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to delete role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role"
            )
    
    @staticmethod
    async def get_user_roles(user_id: str) -> List[Role]:
        """Get roles for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List[Role]: List of user roles
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query user roles
            rows = await conn.fetch("""
                SELECT r.id, r.name, r.description, r.created_at
                FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = $1
                ORDER BY r.name
            """, user_id)
            
            await conn.close()
            
            # Convert rows to Role objects
            roles = [
                Role(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
            
            return roles
        except Exception as e:
            logger.error(f"Failed to get user roles: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user roles"
            )
    
    @staticmethod
    async def assign_role_to_user(user_id: str, role_id: int) -> UserRole:
        """Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
        
        Returns:
            UserRole: Created user role
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Check if role exists
            role = await conn.fetchrow("SELECT id FROM roles WHERE id = $1", role_id)
            if not role:
                await conn.close()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role with ID {role_id} not found"
                )
            
            # Check if user exists by checking Supabase auth
            # This is just a placeholder. In a real app, you'd check if the user exists
            # in the auth.users table or via the Supabase admin API
            
            # Check if user already has this role
            existing = await conn.fetchrow(
                "SELECT user_id, role_id FROM user_roles WHERE user_id = $1 AND role_id = $2",
                user_id, role_id
            )
            
            if existing:
                # User already has this role
                await conn.close()
                return UserRole(user_id=user_id, role_id=role_id)
            
            # Assign role to user
            await conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                user_id, role_id
            )
            
            await conn.close()
            
            return UserRole(user_id=user_id, role_id=role_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign role to user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role to user"
            )
    
    @staticmethod
    async def remove_role_from_user(user_id: str, role_id: int) -> bool:
        """Remove a role from a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
        
        Returns:
            bool: True if role was removed, False otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Remove role from user
            result = await conn.execute(
                "DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2",
                user_id, role_id
            )
            
            await conn.close()
            
            return "DELETE 1" in result
        except Exception as e:
            logger.error(f"Failed to remove role from user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove role from user"
            )
    
    @staticmethod
    async def has_role(user_id: str, role_name: str) -> bool:
        """Check if a user has a specific role.
        
        Args:
            user_id: User ID
            role_name: Role name
        
        Returns:
            bool: True if user has the role, False otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Check if user has role
            result = await conn.fetchval(
                "SELECT user_has_role($1, $2)",
                user_id, role_name
            )
            
            await conn.close()
            
            return result
        except Exception as e:
            logger.error(f"Failed to check if user has role: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check user role"
            )
    
    @staticmethod
    async def has_permission(user_id: str, permission_name: str) -> bool:
        """Check if a user has a specific permission.
        
        Args:
            user_id: User ID
            permission_name: Permission name
        
        Returns:
            bool: True if user has the permission, False otherwise
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Check if user has permission
            result = await conn.fetchval(
                "SELECT user_has_permission($1, $2)",
                user_id, permission_name
            )
            
            await conn.close()
            
            return result
        except Exception as e:
            logger.error(f"Failed to check if user has permission: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check user permission"
            )
    
    @staticmethod
    async def get_permissions() -> List[Permission]:
        """Get all permissions.
        
        Returns:
            List[Permission]: List of permissions
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query all permissions
            rows = await conn.fetch("""
                SELECT id, name, description
                FROM permissions
                ORDER BY name
            """)
            
            await conn.close()
            
            # Convert rows to Permission objects
            permissions = [
                Permission(
                    id=row['id'],
                    name=row['name'],
                    description=row['description']
                )
                for row in rows
            ]
            
            return permissions
        except Exception as e:
            logger.error(f"Failed to get permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch permissions"
            )
    
    @staticmethod
    async def get_role_permissions(role_id: int) -> List[Permission]:
        """Get permissions for a role.
        
        Args:
            role_id: Role ID
        
        Returns:
            List[Permission]: List of role permissions
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query role permissions
            rows = await conn.fetch("""
                SELECT p.id, p.name, p.description
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                WHERE rp.role_id = $1
                ORDER BY p.name
            """, role_id)
            
            await conn.close()
            
            # Convert rows to Permission objects
            permissions = [
                Permission(
                    id=row['id'],
                    name=row['name'],
                    description=row['description']
                )
                for row in rows
            ]
            
            return permissions
        except Exception as e:
            logger.error(f"Failed to get role permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch role permissions"
            )
    
    @staticmethod
    async def get_user_permissions(user_id: str) -> List[Permission]:
        """Get permissions for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List[Permission]: List of user permissions
        """
        try:
            conn = await RoleService.get_db_connection()
            
            # Query user permissions
            rows = await conn.fetch("""
                SELECT DISTINCT p.id, p.name, p.description
                FROM permissions p
                JOIN role_permissions rp ON rp.permission_id = p.id
                JOIN user_roles ur ON ur.role_id = rp.role_id
                WHERE ur.user_id = $1
                ORDER BY p.name
            """, user_id)
            
            await conn.close()
            
            # Convert rows to Permission objects
            permissions = [
                Permission(
                    id=row['id'],
                    name=row['name'],
                    description=row['description']
                )
                for row in rows
            ]
            
            return permissions
        except Exception as e:
            logger.error(f"Failed to get user permissions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user permissions"
            ) 