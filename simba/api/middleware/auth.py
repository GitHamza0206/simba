import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from simba.auth.auth_service import AuthService
from simba.auth.role_service import RoleService

logger = logging.getLogger(__name__)

# Security scheme for bearer tokens
http_bearer = HTTPBearer()


async def get_current_user(bearer_credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    """Get the current user from the Authorization header.

    Args:
        bearer_credentials: Bearer token from Authorization header

    Returns:
        dict: User data

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get user from token
        token = bearer_credentials.credentials
        user = await AuthService.get_user(token)
        return user
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(role: str):
    """Dependency for role-based access control.

    Args:
        role: Required role

    Returns:
        callable: Dependency function
    """

    async def dependency(current_user: dict = Depends(get_current_user)):
        user_id = current_user.get("id")

        try:
            # Check if user has the required role
            has_role = RoleService.has_role(user_id, role)

            if not has_role:
                logger.warning(f"Access denied: User {user_id} does not have role {role}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Role '{role}' required",
                )

            return current_user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Role check error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify role",
            )

    return dependency


def require_permission(permission: str):
    """Dependency for permission-based access control.

    Args:
        permission: Required permission

    Returns:
        callable: Dependency function
    """

    async def dependency(current_user: dict = Depends(get_current_user)):
        user_id = current_user.get("id")

        try:
            # Check if user has the required permission
            has_permission = RoleService.has_permission(user_id, permission)

            if not has_permission:
                logger.warning(
                    f"Access denied: User {user_id} does not have permission {permission}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: Permission '{permission}' required",
                )

            return current_user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify permission",
            )

    return dependency
