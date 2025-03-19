import logging
from typing import Dict, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from pydantic import BaseModel, EmailStr, Field

from simba.auth.auth_service import AuthService
from simba.auth.role_service import RoleService
from simba.core.config import settings
from simba.models.role import Role, Permission
from simba.api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

# FastAPI router
auth_router = APIRouter(
    prefix=f"/auth",
    tags=["auth"],
)

# Request/Response models
class SignUpRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    metadata: Optional[Dict] = Field(default=None, description="Additional user metadata")

class SignInRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="User email")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")

class SwaggerAuthRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class TokenDebugRequest(BaseModel):
    token: str = Field(..., description="JWT token to debug")

class UserMeResponse(BaseModel):
    id: str
    email: str
    created_at: str
    metadata: Optional[Dict]
    roles: List[Role]
    permissions: List[Permission]

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    """Register a new user"""
    try:
        user = await AuthService.sign_up(
            email=request.email,
            password=request.password,
            user_metadata=request.metadata
        )
        return user
    except ValueError as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@auth_router.post("/signin", status_code=status.HTTP_200_OK)
async def signin(request: SignInRequest):
    """Sign in a user"""
    try:
        result = await AuthService.sign_in(
            email=request.email,
            password=request.password
        )
        
        # Ensure the response has the format expected by the frontend
        if "user" not in result or "session" not in result:
            logger.error(f"Invalid auth response structure: {result}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid authentication response from server"
            )
        
        return result
    except ValueError as e:
        logger.error(f"Signin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during signin: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@auth_router.post("/signout", status_code=status.HTTP_200_OK)
async def signout():
    """Sign out a user"""
    try:
        await AuthService.sign_out()
        return {"message": "Successfully signed out"}
    except ValueError as e:
        logger.error(f"Signout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during signout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@auth_router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest):
    """Request password reset"""
    try:
        await AuthService.reset_password(email=request.email)
        return {"message": "Password reset email sent"}
    except ValueError as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@auth_router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token"""
    try:
        tokens = await AuthService.refresh_token(refresh_token=request.refresh_token)
        return tokens
    except ValueError as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@auth_router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get complete information about the currently authenticated user,
    including their roles and permissions.
    """
    try:
        # Get user's roles and permissions
        role_service = RoleService()
        roles = role_service.get_user_roles(current_user["id"])
        permissions = role_service.get_user_permissions(current_user["id"])
        
        return UserMeResponse(
            id=current_user["id"],
            email=current_user["email"],
            created_at=current_user.get("created_at", ""),
            metadata=current_user.get("metadata", {}),
            roles=roles,
            permissions=permissions
        )
    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        ) 