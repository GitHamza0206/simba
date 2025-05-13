import logging
from typing import Dict, Optional, Any

from pydantic import EmailStr

from simba.auth.supabase_client import get_supabase_client
from simba.auth.role_service import RoleService
from simba.database.postgres import PostgresDB

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations with Supabase."""
    
    @staticmethod
    async def sign_up(email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Register a new user with Supabase.
        
        Args:
            email: User email
            password: User password
            user_metadata: Additional user metadata
        
        Returns:
            Dict with user data
            
        Raises:
            ValueError: If signup fails
        """
        user_metadata = user_metadata or {}
        
        try:
            supabase = get_supabase_client()
            
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if hasattr(response, 'error') and response.error:
                raise ValueError(f"Failed to sign up: {response.error.message}")
            
            logger.info(f"User signed up successfully: {email}")
            
            # Get user data from response
            user_data = {
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "metadata": response.user.user_metadata,
            }
            
            # Assign default role to user
            try:
                # First try to get 'user' role ID
                role_service = RoleService()
                role = role_service.get_role_by_name("admin")
                
                if role:
                    # Assign role to user
                    role_service.assign_role_to_user(
                        user_id=user_data["id"],
                        role_id=role.id
                    )
                    
                    # Now get the role and permissions
                    user_data["roles"] = [role] 
                    user_data["permissions"] = role_service.get_role_permissions(role.id)
                    
                    logger.info(f"Assigned default '{role.name}' role to user: {email}")
                else:
                    logger.error("No default roles ('user' or 'admin') found in the database")
                    raise ValueError("Failed to assign default role - no roles found in database")
            except Exception as e:
                logger.error(f"Failed to assign default role to user: {str(e)}")
                raise ValueError(f"Failed to assign default role: {str(e)}")
            
            return user_data
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to sign up: {str(e)}")
            raise ValueError(f"Sign up failed: {str(e)}")
    
    @staticmethod
    async def sign_in(email: str, password: str) -> Dict[str, Any]:
        """Sign in a user with Supabase.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict with user data and session tokens
            
        Raises:
            ValueError: If signin fails
        """
        try:
            supabase = get_supabase_client()
            
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if hasattr(response, 'error') and response.error:
                raise ValueError(f"Failed to sign in: {response.error.message}")
            
            logger.info(f"User signed in successfully: {email}")
            
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at,
                    "metadata": response.user.user_metadata,
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at
                }
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to sign in: {str(e)}")
            raise ValueError(f"Sign in failed: {str(e)}")
    
    @staticmethod
    async def sign_out(access_token: Optional[str] = None) -> None:
        """Sign out a user from Supabase.
        
        Args:
            access_token: User access token (optional)
        
        Raises:
            ValueError: If signout fails
        """
        try:
            supabase = get_supabase_client()
            
            if access_token:
                # Sign out specific session
                response = supabase.auth.sign_out(access_token)
            else:
                # Sign out current session
                response = supabase.auth.sign_out()
            
            if hasattr(response, 'error') and response.error:
                raise ValueError(f"Failed to sign out: {response.error.message}")
            
            logger.info("User signed out successfully")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to sign out: {str(e)}")
            raise ValueError(f"Sign out failed: {str(e)}")
    
    @staticmethod
    async def reset_password(email: str) -> None:
        """Send password reset email to a user.
        
        Args:
            email: User email
        
        Raises:
            ValueError: If password reset fails
        """
        try:
            supabase = get_supabase_client()
            
            response = supabase.auth.reset_password_email(email)
            
            if hasattr(response, 'error') and response.error:
                raise ValueError(f"Failed to send password reset email: {response.error.message}")
            
            logger.info(f"Password reset email sent to: {email}")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to reset password: {str(e)}")
            raise ValueError(f"Password reset failed: {str(e)}")
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, str]:
        """Refresh an authentication token.
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            Dict with new access and refresh tokens
            
        Raises:
            ValueError: If token refresh fails
        """
        try:
            supabase = get_supabase_client()
            
            response = supabase.auth.refresh_session(refresh_token)
            
            if hasattr(response, 'error') and response.error:
                raise ValueError(f"Failed to refresh token: {response.error.message}")
            
            logger.info("Token refreshed successfully")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to refresh token: {str(e)}")
            raise ValueError(f"Token refresh failed: {str(e)}")
    
    @staticmethod
    async def get_user(access_token: str) -> Dict[str, Any]:
        """Get user data from access token by validating it with Supabase.
        
        Args:
            access_token: Access token
        
        Returns:
            Dict with user data
            
        Raises:
            ValueError: If getting user data fails or token is invalid
        """
        try:
            token_prefix = access_token[:10] + "..." if access_token else "None"
            logger.debug(f"Attempting to validate token and get user via Supabase: {token_prefix}")

            supabase = get_supabase_client()
            response = supabase.auth.get_user(access_token) # Use Supabase client to validate token

            if not response or not hasattr(response, 'user') or not response.user:
                logger.warning("Supabase validation failed or no user returned for token.")
                raise ValueError("Invalid or expired token, or user not found.")

            logger.info(f"Successfully validated token and retrieved user: {response.user.email}")
            
            # Return user information in the expected format
            return {
                "id": str(response.user.id), # Ensure ID is string
                "email": response.user.email,
                "created_at": response.user.created_at.isoformat() if response.user.created_at else None,
                "metadata": response.user.user_metadata or {} 
            }
            
        except ValueError as ve: # Catch specific ValueErrors we raise
            logger.error(f"Validation error in get_user: {str(ve)}")
            raise
        except Exception as e: # Catch other exceptions, e.g., from Supabase client
            logger.error(f"Failed to get user via Supabase: {str(e)}, error type: {type(e).__name__}")
            raise ValueError(f"Get user failed: Supabase validation error - {str(e)}") 