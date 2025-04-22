import logging
from typing import Optional, Union
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from simba.auth.auth_service import AuthService
from simba.auth.role_service import RoleService
from simba.auth.api_key_service import APIKeyService
from simba.auth.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Security scheme for bearer tokens
http_bearer = HTTPBearer(auto_error=False)

# Security scheme for API keys
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Tenant ID header
tenant_id_header = APIKeyHeader(name="X-Tenant-Id", auto_error=False)

async def get_current_user(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    api_key: Optional[str] = Depends(api_key_header),
    tenant_id: Optional[str] = Depends(tenant_id_header)
):
    """Get the current user from either JWT bearer token or API key.
    
    Args:
        request: FastAPI request object
        bearer_credentials: Bearer token from Authorization header
        api_key: API key from X-API-Key header
        tenant_id: Tenant ID from X-Tenant-Id header
        
    Returns:
        dict: User data
        
    Raises:
        HTTPException: If authentication fails
    """
    # Process tenant_id if provided
    tenant_uuid = None
    if tenant_id:
        try:
            tenant_uuid = UUID(tenant_id)
        except ValueError:
            logger.warning(f"Invalid tenant ID format: {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant ID format",
            )
    
    # Check if API key is provided
    if api_key:
        try:
            # Validate API key with tenant context if available
            user = APIKeyService.validate_key(api_key, tenant_uuid)
            if user:
                logger.debug("User authenticated with API key")
                
                # Add auth_type to user data
                user["auth_type"] = "api_key"
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
    
    # If bearer token is provided, use Supabase auth
    if bearer_credentials:
        try:
            # Get Supabase client
            supabase = get_supabase_client()
            token = bearer_credentials.credentials
            
            # Get user from token
            user_response = supabase.auth.get_user(token)
            if not user_response:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Extract user data
            user_data = {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "auth_type": "jwt",
                "metadata": user_response.user.user_metadata or {},
            }
            
            # Add tenant_id if provided
            if tenant_uuid:
                user_data["tenant_id"] = tenant_uuid
                
            logger.debug("User authenticated with bearer token")
            return user_data
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
        if current_user.get("auth_type") == "api_key":
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

def require_tenant_access(tenant_id_param: Optional[str] = None):
    """Dependency for tenant-based access control.
    
    Args:
        tenant_id_param: Optional tenant ID parameter from path/query
    
    Returns:
        callable: Dependency function
    """
    async def dependency(
        current_user: dict = Depends(get_current_user),
        tenant_id_header: Optional[str] = Depends(tenant_id_header)
    ):
        # Priority: 1. Parameter from path/query, 2. Header, 3. User's default tenant
        tenant_id = None
        
        # Check path/query parameter first
        if tenant_id_param:
            try:
                tenant_id = UUID(tenant_id_param)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid tenant ID format in path parameter",
                )
        # Check header next
        elif tenant_id_header:
            try:
                tenant_id = UUID(tenant_id_header)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid tenant ID format in header",
                )
        # Finally, use user's tenant if available
        elif current_user.get("tenant_id"):
            tenant_id = current_user.get("tenant_id")
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required (either in path, query, header, or user profile)",
            )
        
        # For API keys, verify the key belongs to the tenant
        if current_user.get("auth_type") == "api_key":
            key_tenant_id = current_user.get("tenant_id")
            
            # If key has tenant_id and doesn't match requested tenant
            if key_tenant_id and key_tenant_id != tenant_id:
                logger.warning(f"Tenant mismatch: API key tenant {key_tenant_id} != requested tenant {tenant_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key not authorized for this tenant",
                )
        
        # Add tenant_id to current_user for convenience
        current_user["tenant_id"] = tenant_id
        return current_user
    
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
        if current_user.get("auth_type") == "api_key":
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