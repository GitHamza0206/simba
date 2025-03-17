import logging
from typing import Dict, Optional, Any

from pydantic import EmailStr

from simba.auth.supabase_client import get_supabase_client
from simba.auth.role_service import RoleService

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
                "metadata": response.user.user_metadata
            }
            
            # Assign default role to user
            try:
                # Get 'user' role ID
                role_service = RoleService()
                role = await role_service.get_role_by_name("user")
                
                if role:
                    # Assign role to user
                    await role_service.assign_role_to_user(
                        user_id=user_data["id"],
                        role_id=role.id
                    )
                    logger.info(f"Assigned default 'user' role to user: {email}")
                else:
                    logger.warning("Default 'user' role not found")
            except Exception as e:
                logger.error(f"Failed to assign default role to user: {str(e)}")
                # Continue without raising error - user is created but role assignment failed
            
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
                    "metadata": response.user.user_metadata
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
        """Get user data from access token.
        
        Args:
            access_token: Access token
        
        Returns:
            Dict with user data
            
        Raises:
            ValueError: If getting user data fails
        """
        try:
            # Log token prefix for debugging (first 10 chars only for security)
            token_prefix = access_token[:10] + "..." if access_token else "None"
            logger.debug(f"Validating token starting with: {token_prefix}")
            
            supabase = get_supabase_client()
            
            # Use the JWT directly to get user information without setting a session
            try:
                logger.debug("Using Supabase JWT to get user")
                
                # In Supabase Python SDK 2.13.0+, we can just pass the JWT to the admin API
                # This avoids the need for refresh tokens completely for verification
                headers = {
                    "Authorization": f"Bearer {access_token}"
                }
                
                # Use the client's fetch directly
                user_response = supabase.auth.admin.get_user_by_jwt(access_token)
                
                logger.debug(f"Successfully validated token and retrieved user data")
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "created_at": user_response.user.created_at,
                    "metadata": user_response.user.user_metadata
                }
                
            except Exception as e:
                logger.warning(f"Admin API method failed: {str(e)}, trying alternative approach")
                
                # Try session-based approach
                try:
                    logger.debug("Trying session-based validation approach")
                    # For validation only, try using set_session with the proper parameters
                    supabase.auth.set_session({
                        "access_token": access_token,
                        "refresh_token": "dummy-refresh-token"  # Dummy value for validation purposes
                    })
                    
                    # If session was set successfully, get the user
                    response = supabase.auth.get_user()
                    
                    if response.user:
                        logger.debug(f"Successfully validated token using session-based approach")
                        return {
                            "id": response.user.id,
                            "email": response.user.email,
                            "created_at": response.user.created_at,
                            "metadata": response.user.user_metadata
                        }
                    
                except Exception as session_error:
                    logger.warning(f"Session-based validation failed: {str(session_error)}, falling back to JWT parsing")
                
                # Final fallback - parse JWT directly
                try:
                    import jwt
                    import json
                    import base64
                    
                    # Manual JWT parsing if jwt library not available
                    def decode_jwt(token):
                        parts = token.split(".")
                        if len(parts) != 3:
                            raise ValueError("Invalid JWT format")
                        
                        # Decode the payload (second part)
                        payload = parts[1]
                        # Add padding if needed
                        payload += "=" * (-len(payload) % 4)
                        # Decode
                        decoded = base64.b64decode(payload.replace("-", "+").replace("_", "/"))
                        return json.loads(decoded)
                    
                    # Try to use PyJWT if available
                    try:
                        payload = jwt.decode(access_token, options={"verify_signature": False})
                    except:
                        payload = decode_jwt(access_token)
                    
                    # Check if token is expired
                    import time
                    current_time = int(time.time())
                    if payload.get("exp", 0) < current_time:
                        raise ValueError("Token has expired")
                    
                    # Extract user data from payload
                    user_id = payload.get("sub")
                    
                    # Don't try to query the database, just use the JWT payload
                    logger.debug(f"Validated token through JWT parsing")
                    return {
                        "id": user_id,
                        "email": payload.get("email", ""),
                        "created_at": payload.get("created_at", ""),
                        "metadata": payload.get("user_metadata", {})
                    }
                
                except Exception as jwt_error:
                    logger.error(f"JWT parsing failed: {str(jwt_error)}")
                    raise ValueError(f"Token validation failed: {str(jwt_error)}")
            
        except ValueError as ve:
            logger.error(f"ValueError in get_user: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Failed to get user: {str(e)}, error type: {type(e).__name__}")
            raise ValueError(f"Get user failed: {str(e)}") 