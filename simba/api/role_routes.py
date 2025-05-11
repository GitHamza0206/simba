import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from simba.api.middleware.auth import get_current_user, require_role, require_permission
from simba.auth.role_service import RoleService
from simba.models.role import Role, RoleCreate, RoleUpdate, Permission, UserRoleCreate, UserRole

logger = logging.getLogger(__name__)

# FastAPI router
role_router = APIRouter(
    prefix=f"/roles",
    tags=["roles"],
)

@role_router.get("/", response_model=List[Role], status_code=status.HTTP_200_OK)
async def get_roles(
    current_user: dict = Depends(get_current_user)
):
    """Get all roles.
    
    This endpoint allows any authenticated user to retrieve all roles.
    This is useful during bootstrapping when no user has specific permissions yet.
    
    Returns:
        List[Role]: List of roles
    """
    try:
        roles =  RoleService.get_roles()
        return roles
    except Exception as e:
        logger.error(f"Failed to get roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch roles"
        )

@role_router.get("/permissions", response_model=List[Permission])
async def get_permissions(
    current_user: dict = Depends(require_permission("roles:read"))
):
    """Get all permissions.
    
    Args:
        current_user: Current user with 'roles:read' permission
        
    Returns:
        List[Permission]: List of permissions
    """
    try:
        permissions = RoleService.get_permissions()
        return permissions
    except Exception as e:
        logger.error(f"Failed to get permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch permissions"
        )

@role_router.get("/user/{user_id}", response_model=List[Role])
async def get_user_roles(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get roles for a user.
    
    Args:
        user_id: User ID
        current_user: Current user (must be the same user or have 'roles:read' permission)
        
    Returns:
        List[Role]: List of user roles
    """
    try:
        # Allow users to see their own roles, or admins to see anyone's
        if user_id != current_user.get("id"):
            # Check if user has permission to read roles
            has_permission = RoleService.has_permission(current_user.get("id"), "roles:read")
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only view your own roles"
                )
        
        roles = RoleService.get_user_roles(user_id)
        return roles
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user roles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user roles"
        )

@role_router.get("/user/{user_id}/permissions", response_model=List[Permission])
async def get_user_permissions(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get permissions for a user.
    
    Args:
        user_id: User ID
        current_user: Current user (must be the same user or have 'roles:read' permission)
        
    Returns:
        List[Permission]: List of user permissions
    """
    try:
        # Allow users to see their own permissions, or admins to see anyone's
        if user_id != current_user.get("id"):
            # Check if user has permission to read roles
            has_permission = RoleService.has_permission(current_user.get("id"), "roles:read")
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You can only view your own permissions"
                )
        
        permissions = RoleService.get_user_permissions(user_id)
        return permissions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user permissions"
        )

@role_router.get("/{role_id}", response_model=Role)
async def get_role(
    role_id: int,
    current_user: dict = Depends(require_permission("roles:read"))
):
    """Get a role by ID.
    
    Args:
        role_id: Role ID
        current_user: Current user with 'roles:read' permission
        
    Returns:
        Role: Role details
    """
    try:
        role =  RoleService.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        return role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch role"
        )

@role_router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role: RoleCreate,
    current_user: dict = Depends(require_permission("roles:write"))
):
    """Create a new role.
    
    Args:
        role: Role data
        current_user: Current user with 'roles:write' permission
        
    Returns:
        Role: Created role
    """
    try:
        created_role = await RoleService.create_role(
            name=role.name,
            description=role.description
        )
        return created_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )

@role_router.put("/{role_id}", response_model=Role)
async def update_role(
    role_id: int,
    role: RoleUpdate,
    current_user: dict = Depends(require_permission("roles:write"))
):
    """Update a role.
    
    Args:
        role_id: Role ID
        role: Role update data
        current_user: Current user with 'roles:write' permission
        
    Returns:
        Role: Updated role
    """
    try:
        updated_role = await RoleService.update_role(
            role_id=role_id,
            name=role.name,
            description=role.description
        )
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        return updated_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )

@role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: dict = Depends(require_permission("roles:delete"))
):
    """Delete a role.
    
    Args:
        role_id: Role ID
        current_user: Current user with 'roles:delete' permission
    """
    try:
        # Check if role exists
        role = await RoleService.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        # Delete role
        deleted = await RoleService.delete_role(role_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete role with ID {role_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete role: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role"
        )

@role_router.get("/{role_id}/permissions", response_model=List[Permission])
async def get_role_permissions(
    role_id: int,
    current_user: dict = Depends(require_permission("roles:read"))
):
    """Get permissions for a role.
    
    Args:
        role_id: Role ID
        current_user: Current user with 'roles:read' permission
        
    Returns:
        List[Permission]: List of role permissions
    """
    try:
        # Check if role exists
        role = RoleService.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        permissions = RoleService.get_role_permissions(role_id)
        return permissions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get role permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch role permissions"
        )

@role_router.post("/user/{user_id}", response_model=UserRole)
async def assign_role_to_user(
    user_id: str,
    role_data: UserRoleCreate,
    current_user: dict = Depends(require_permission("roles:write"))
):
    """Assign a role to a user.
    
    Args:
        user_id: User ID
        role_data: Role assignment data
        current_user: Current user with 'roles:write' permission
        
    Returns:
        UserRole: Created user role
    """
    try:
        user_role = RoleService.assign_role_to_user(
            user_id=user_id,
            role_id=role_data.role_id
        )
        return user_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign role to user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role to user"
        )

@role_router.delete("/user/{user_id}/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: str,
    role_id: int,
    current_user: dict = Depends(require_permission("roles:write"))
):
    """Remove a role from a user.
    
    Args:
        user_id: User ID
        role_id: Role ID
        current_user: Current user with 'roles:write' permission
    """
    try:
        # Check if role exists
        role = await RoleService.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found"
            )
        
        # Remove role from user
        removed = await RoleService.remove_role_from_user(user_id, role_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User does not have role with ID {role_id}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove role from user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role from user"
        )

@role_router.post(
    "/bootstrap/{user_id}",
    status_code=status.HTTP_200_OK,
)
async def bootstrap_admin(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Bootstrap a user with admin role.
    
    This endpoint should only be used during initial setup.
    It allows assigning the admin role to a user.
    
    Args:
    -----
    user_id: ID of the user to make admin
    current_user: Current authenticated user
    
    Returns:
    --------
    Dict: Message indicating success
    """
    try:
        # Security check: Only allow a user to bootstrap themselves or if they are already an admin
        if current_user.get("id") != user_id:
            # Check if the current user is an admin
            is_admin = RoleService.has_role(current_user.get("id"), "admin")
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Only admins can bootstrap other users"
                )
        
        # Get the admin role
        admin_role = RoleService.get_role_by_name("admin")
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin role not found"
            )
        
        # Assign the admin role to the user
        RoleService.assign_role_to_user(user_id, admin_role.id)
        
        return {"message": f"User {user_id} has been assigned the admin role"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bootstrap admin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bootstrap admin role"
        ) 