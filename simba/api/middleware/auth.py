import logging
from typing import Optional, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from simba.auth.auth_service import AuthService
from simba.auth.role_service import RoleService
from simba.auth.api_key_service import APIKeyService

logger = logging.getLogger(__name__)

# Security scheme for bearer tokens
http_bearer = HTTPBearer(auto_error=False)

# Security scheme for API keys
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    api_key: Optional[str] = Depends(api_key_header)
):
    """Get the current user from either JWT bearer token or API key.
    
    Args:
        bearer_credentials: Bearer token from Authorization header
        api_key: API key from X-API-Key header
        
    Returns:
        dict: User data
        
    Raises:
        HTTPException: If authentication fails
    """
    # Check if API key is provided
    if api_key:
        try:
            # Validate API key
            user = APIKeyService.validate_key(api_key)
            if user:
                logger.debug("User authenticated with API key")
                return user
            
            # If API key is invalid, raise exception
            logger.warning("Invalid API key")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        except Exception as e:
            logger.error(f"API key authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
    
    # If bearer token is provided, use it
    if bearer_credentials:
        try:
            # Get user from token
            token = bearer_credentials.credentials
            user = await AuthService.get_user(token)
            logger.debug("User authenticated with bearer token")
            return user
        except Exception as e:
            logger.error(f"Bearer token authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # If neither API key nor bearer token is provided, raise exception
    logger.warning("No authentication credentials provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer, APIKey"},
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
        
        # Check if user is authenticated via API key
        if current_user.get("metadata", {}).get("is_api_key", False):
            # For API keys, check if the key has the required role
            roles = current_user.get("roles", [])
            if role in roles:
                return current_user
            
            logger.warning(f"Access denied: API key does not have role {role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{role}' required",
            )
        
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
        
        # For API keys with fixed permissions, we currently only support role-based checks
        # You might want to extend this to map roles to permissions for API keys
        if current_user.get("metadata", {}).get("is_api_key", False):
            logger.warning(f"Permission check for API key not supported, use role-based checks instead")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API keys currently only support role-based authorization",
            )
        
        try:
            # Check if user has the required permission
            has_permission = RoleService.has_permission(user_id, permission)
            
            if not has_permission:
                logger.warning(f"Access denied: User {user_id} does not have permission {permission}")
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