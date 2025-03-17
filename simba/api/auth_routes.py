import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from pydantic import BaseModel, EmailStr, Field

from simba.auth.auth_service import AuthService
from simba.core.config import settings

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

@auth_router.post("/swagger-token", status_code=status.HTTP_200_OK)
async def get_swagger_token(request: SwaggerAuthRequest):
    """
    Get an access token for Swagger UI testing.
    This endpoint is specifically for testing the API through Swagger UI.
    """
    try:
        auth_result = await AuthService.sign_in(request.email, request.password)
        return {"access_token": auth_result["session"]["access_token"]}
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@auth_router.post("/debug-token", status_code=status.HTTP_200_OK)
async def debug_token(request: TokenDebugRequest):
    """
    Debug a JWT token to help troubleshoot authentication issues.
    This endpoint helps validate that a token can be processed correctly.
    """
    try:
        # Try to get user with the token
        user = await AuthService.get_user(request.token)
        
        # Return success with user info if token is valid
        return {
            "valid": True,
            "user_id": user["id"],
            "email": user["email"]
        }
    except Exception as e:
        # Return error details if token validation fails
        logger.error(f"Token debug error: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }

@auth_router.get("/diagnostic", response_model=dict)
async def supabase_diagnostic():
    """
    Diagnostic endpoint to check Supabase client version and capabilities.
    """
    import inspect
    import supabase
    from simba.auth.supabase_client import get_supabase_client
    
    try:
        client = get_supabase_client()
        
        # Check version and available methods
        auth_methods = inspect.getmembers(client.auth, predicate=inspect.ismethod)
        auth_method_names = [name for name, _ in auth_methods]
        
        # Check if admin methods exist
        admin_methods = []
        if hasattr(client.auth, 'admin'):
            admin_methods = inspect.getmembers(client.auth.admin, predicate=inspect.ismethod)
            admin_method_names = [name for name, _ in admin_methods]
        else:
            admin_method_names = []
        
        return {
            "status": "success",
            "supabase_version": supabase.__version__,
            "auth_methods": auth_method_names,
            "admin_methods": admin_method_names,
            "has_admin_api": hasattr(client.auth, 'admin'),
            "has_set_session": "set_session" in auth_method_names,
            "has_get_user_by_jwt": "get_user_by_jwt" in admin_method_names if admin_method_names else False
        }
    except Exception as e:
        logging.error(f"Diagnostic error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        } 