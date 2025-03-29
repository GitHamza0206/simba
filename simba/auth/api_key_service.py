"""
Service for managing API keys in the Simba application.
"""
import hashlib
import logging
import secrets
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status

from simba.models.api_key import APIKey, APIKeyInfo, APIKeyResponse, APIKeyCreate
from simba.database.postgres import PostgresDB
from simba.auth.role_service import RoleService

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys."""
    
    # Key constants
    KEY_LENGTH = 32  # 32 bytes = 256 bits
    PREFIX_LENGTH = 8  # First 8 chars displayed to users
    
    @staticmethod
    def _generate_key() -> str:
        """
        Generate a random API key.
        
        Returns:
            str: A random API key
        """
        # Generate a random key with strong entropy
        # Using secrets module which is designed for cryptographic use
        raw_key = secrets.token_hex(APIKeyService.KEY_LENGTH)
        
        return raw_key
    
    @staticmethod
    def _hash_key(key: str) -> str:
        """
        Hash an API key for storage.
        
        Args:
            key: The raw API key
            
        Returns:
            str: The hashed API key
        """
        # Use SHA-256 for secure hashing
        return hashlib.sha256(key.encode()).hexdigest()
    
    @classmethod
    def create_key(cls, user_id: UUID, key_data: APIKeyCreate) -> APIKeyResponse:
        """
        Create a new API key.
        
        Args:
            user_id: User ID that owns this key
            key_data: API key data
            
        Returns:
            APIKeyResponse: Created API key with the full key value
        """
        try:
            # Generate a new random key
            raw_key = cls._generate_key()
            key_hash = cls._hash_key(raw_key)
            key_prefix = raw_key[:cls.PREFIX_LENGTH]
            
            # Validate roles
            role_service = RoleService()
            for role_name in key_data.roles:
                role = role_service.get_role_by_name(role_name)
                if not role:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Role '{role_name}' does not exist"
                    )
            
            # Insert into database
            row = PostgresDB.fetch_one("""
                INSERT INTO api_keys 
                (key, key_prefix, user_id, name, roles, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, key_prefix, name, roles, created_at, expires_at
            """, (
                key_hash, 
                key_prefix, 
                str(user_id), 
                key_data.name, 
                json.dumps(key_data.roles), 
                key_data.expires_at
            ))
            
            # Return the response with the raw key (this is the only time it will be visible)
            return APIKeyResponse(
                id=row['id'],
                key=raw_key,
                key_prefix=row['key_prefix'],
                name=row['name'],
                roles=row['roles'],
                created_at=row['created_at'],
                expires_at=row['expires_at']
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key"
            )
    
    @staticmethod
    def get_keys(user_id: UUID) -> List[APIKeyInfo]:
        """
        Get all API keys for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[APIKeyInfo]: List of API keys
        """
        try:
            # Query API keys for user
            rows = PostgresDB.fetch_all("""
                SELECT id, key_prefix, name, roles, created_at, last_used, is_active, expires_at
                FROM api_keys
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (str(user_id),))
            
            # Convert rows to APIKeyInfo objects
            api_keys = []
            for row in rows:
                # Parse the roles JSON if it's a string
                roles = row['roles']
                if isinstance(roles, str):
                    try:
                        roles = json.loads(roles)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse roles JSON: {roles}")
                        roles = []
                
                api_keys.append(APIKeyInfo(
                    id=row['id'],
                    key_prefix=row['key_prefix'],
                    name=row['name'],
                    roles=roles,
                    created_at=row['created_at'],
                    last_used=row['last_used'],
                    is_active=row['is_active'],
                    expires_at=row['expires_at']
                ))
            
            return api_keys
        except Exception as e:
            logger.error(f"Failed to get API keys: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch API keys"
            )
    
    @staticmethod
    def delete_key(user_id: UUID, key_id: UUID) -> bool:
        """
        Delete an API key.
        
        Args:
            user_id: User ID
            key_id: API key ID
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            # Delete API key
            result = PostgresDB.execute_query("""
                DELETE FROM api_keys
                WHERE id = %s AND user_id = %s
            """, (str(key_id), str(user_id)))
            
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key"
            )
    
    @staticmethod
    def deactivate_key(user_id: UUID, key_id: UUID) -> bool:
        """
        Deactivate an API key.
        
        Args:
            user_id: User ID
            key_id: API key ID
            
        Returns:
            bool: True if key was deactivated, False otherwise
        """
        try:
            # Deactivate API key
            result = PostgresDB.execute_query("""
                UPDATE api_keys
                SET is_active = FALSE
                WHERE id = %s AND user_id = %s
            """, (str(key_id), str(user_id)))
            
            return result > 0
        except Exception as e:
            logger.error(f"Failed to deactivate API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate API key"
            )
    
    @staticmethod
    def validate_key(api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return user information.
        
        Args:
            api_key: Raw API key
            
        Returns:
            Optional[Dict[str, Any]]: User data if key is valid, None otherwise
        """
        try:
            # Hash the key before comparing
            key_hash = APIKeyService._hash_key(api_key)
            
            # Find the key in the database
            row = PostgresDB.fetch_one("""
                SELECT id, user_id, roles, is_active, expires_at
                FROM api_keys
                WHERE key = %s
            """, (key_hash,))
            
            if not row:
                logger.warning("API key not found")
                return None
            
            # Check if key is active
            if not row['is_active']:
                logger.warning("API key is inactive")
                return None
            
            # Check if key is expired
            if row['expires_at'] and row['expires_at'] < datetime.now():
                logger.warning("API key has expired")
                return None
            
            # Update last used timestamp
            PostgresDB.execute_query("""
                UPDATE api_keys
                SET last_used = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (row['id'],))
            
            # Parse roles if needed
            roles = row['roles']
            if isinstance(roles, str):
                try:
                    roles = json.loads(roles)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse roles JSON: {roles}")
                    roles = []
            
            # Get user data
            user = {
                "id": row['user_id'],
                "email": f"api-key-{row['id']}@api.internal",  # Virtual email
                "metadata": {
                    "is_api_key": True,
                    "api_key_id": row['id']
                },
                "roles": roles
            }
            
            return user
            
        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return None 