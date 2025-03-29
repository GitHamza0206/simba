"""
API routes for managing API keys.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from simba.models.api_key import APIKeyCreate, APIKeyResponse, APIKeyInfo
from simba.auth.api_key_service import APIKeyService
from simba.api.middleware.auth import get_current_user, require_role

logger = logging.getLogger(__name__)

# FastAPI router
api_key_router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
)


@api_key_router.post("", status_code=status.HTTP_201_CREATED, response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new API key for the current user.
    
    Args:
        key_data: API key data
        current_user: Current authenticated user
        
    Returns:
        APIKeyResponse: Created API key with the full key value
    """
    try:
        # Get user ID from current user
        user_id = UUID(current_user.get("id"))
        
        # Create new API key
        key = APIKeyService.create_key(user_id, key_data)
        
        return key
    except Exception as e:
        logger.error(f"Failed to create API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )


@api_key_router.get("", status_code=status.HTTP_200_OK, response_model=List[APIKeyInfo])
async def get_api_keys(
    current_user: dict = Depends(get_current_user),
):
    """
    Get all API keys for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List[APIKeyInfo]: List of API keys
    """
    try:
        # Get user ID from current user
        user_id = UUID(current_user.get("id"))
        
        # Get API keys
        keys = APIKeyService.get_keys(user_id)
        
        return keys
    except Exception as e:
        logger.error(f"Failed to get API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API keys"
        )


@api_key_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete an API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
    """
    try:
        # Get user ID from current user
        user_id = UUID(current_user.get("id"))
        
        # Delete API key
        success = APIKeyService.delete_key(user_id, key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key"
        )


@api_key_router.post("/{key_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_api_key(
    key_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Deactivate an API key.
    
    Args:
        key_id: API key ID
        current_user: Current authenticated user
    """
    try:
        # Get user ID from current user
        user_id = UUID(current_user.get("id"))
        
        # Deactivate API key
        success = APIKeyService.deactivate_key(user_id, key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
            
        return {"success": True, "message": "API key deactivated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate API key"
        )


@api_key_router.get("/test", status_code=status.HTTP_200_OK)
async def test_api_key(
    current_user: dict = Depends(get_current_user),
):
    """
    Test endpoint to verify API key authentication is working.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with user information
    """
    is_api_key = current_user.get("metadata", {}).get("is_api_key", False)
    
    return {
        "authenticated": True,
        "user_id": current_user.get("id"),
        "email": current_user.get("email"),
        "is_api_key": is_api_key,
        "api_key_id": current_user.get("metadata", {}).get("api_key_id") if is_api_key else None,
        "roles": current_user.get("roles", [])
    } 