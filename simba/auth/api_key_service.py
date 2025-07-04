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
from simba.auth.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()


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
            # Add debug logging
            logger.info(f"Creating API key for user: {user_id}")
            logger.info(f"Key data: {key_data.model_dump_json()}")
            
            # Generate a new random key
            raw_key = cls._generate_key()
            key_hash = cls._hash_key(raw_key)
            key_prefix = raw_key[:cls.PREFIX_LENGTH]
            
            # Validate roles
            role_service = RoleService()
            for role_name in key_data.roles:
                role = role_service.get_role_by_name(role_name)
                if not role:
                    logger.error(f"Role '{role_name}' does not exist")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Role '{role_name}' does not exist"
                    )
            
            # Prepare data for insert
            insert_data = {
                "key": key_hash,
                "key_prefix": key_prefix,
                "user_id": str(user_id),  # Convert UUID to string to match auth.uid() format
                "tenant_id": str(key_data.tenant_id) if key_data.tenant_id else None,
                "name": key_data.name,
                "roles": key_data.roles,
                "expires_at": key_data.expires_at.isoformat() if key_data.expires_at else None
            }
            
            try:
                # Insert using Supabase client
                result = supabase.table('api_keys').insert(insert_data).execute()
                
                if not result.data:
                    logger.error("Failed to create API key through Supabase")
                    raise Exception("Failed to create API key")
                
                row = result.data[0]
                
                # Return the response with the raw key (this is the only time it will be visible)
                response = APIKeyResponse(
                    id=row['id'],
                    key=raw_key,
                    key_prefix=row['key_prefix'],
                    tenant_id=row['tenant_id'],
                    name=row['name'],
                    roles=row['roles'],
                    created_at=row['created_at'],
                    expires_at=row['expires_at']
                )
                
                logger.info(f"API key created successfully with ID: {response.id}")
                return response
                
            except Exception as db_error:
                logger.error(f"Database error during API key creation: {str(db_error)}")
                raise
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create API key: {str(e)}"
            )
    
    @staticmethod
    def get_keys(user_id: UUID, tenant_id: Optional[UUID] = None) -> List[APIKeyInfo]:
        """
        Get all API keys for a user, optionally filtered by tenant.
        
        Args:
            user_id: User ID
            tenant_id: Optional tenant ID to filter by
            
        Returns:
            List[APIKeyInfo]: List of API keys
        """
        try:
            # Add debug logging
            logger.info(f"Getting API keys for user: {user_id}, tenant: {tenant_id}")
            
            # Build query using Supabase
            query = supabase.table('api_keys').select('*').eq('user_id', str(user_id))
            
            # Add tenant filter if provided
            if tenant_id:
                query = query.eq('tenant_id', str(tenant_id))
                
            # Execute query
            result = query.execute()
            
            if not result.data:
                logger.info(f"No API keys found for user {user_id}")
                return []
            
            # Convert rows to APIKeyInfo objects
            api_keys = []
            for row in result.data:
                logger.info(f"Processing API key: {row.get('id')} with prefix: {row.get('key_prefix')}")
                
                api_keys.append(APIKeyInfo(
                    id=row['id'],
                    key_prefix=row['key_prefix'],
                    tenant_id=row['tenant_id'],
                    name=row['name'],
                    roles=row['roles'],
                    created_at=row['created_at'],
                    last_used=row['last_used'],
                    is_active=row['is_active'],
                    expires_at=row['expires_at']
                ))
            
            logger.info(f"Returning {len(api_keys)} API keys")
            return api_keys
        except Exception as e:
            logger.error(f"Failed to get API keys: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch API keys: {str(e)}"
            )
    
    @staticmethod
    def get_tenant_keys(tenant_id: UUID) -> List[APIKeyInfo]:
        """
        Get all API keys for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List[APIKeyInfo]: List of API keys for the tenant
        """
        try:
            # Query API keys for tenant
            rows = PostgresDB.fetch_all("""
                SELECT id, key_prefix, tenant_id, name, roles, created_at, last_used, is_active, expires_at
                FROM api_keys
                WHERE tenant_id = %s
                ORDER BY created_at DESC
            """, (str(tenant_id),))
            
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
                    tenant_id=row['tenant_id'],
                    name=row['name'],
                    roles=roles,
                    created_at=row['created_at'],
                    last_used=row['last_used'],
                    is_active=row['is_active'],
                    expires_at=row['expires_at']
                ))
            
            return api_keys
        except Exception as e:
            logger.error(f"Failed to get tenant API keys: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch tenant API keys"
            )
    
    @staticmethod
    def delete_key(user_id: UUID, key_id: UUID, tenant_id: Optional[UUID] = None) -> bool:
        """
        Delete an API key.
        
        Args:
            user_id: User ID
            key_id: API key ID
            tenant_id: Optional tenant ID for additional validation
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            # Build the query with potential tenant filter
            query = """
                DELETE FROM api_keys
                WHERE id = %s AND user_id = %s
            """
            params = [str(key_id), str(user_id)]
            
            # Add tenant filter if provided
            if tenant_id:
                query += " AND tenant_id = %s"
                params.append(str(tenant_id))
                
            # Delete API key
            result = PostgresDB.execute_query(query, tuple(params))
            
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key"
            )
    
    @staticmethod
    def delete_tenant_key(tenant_id: UUID, key_id: UUID) -> bool:
        """
        Delete a tenant API key.
        
        Args:
            tenant_id: Tenant ID
            key_id: API key ID
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        try:
            # Delete tenant API key
            result = PostgresDB.execute_query("""
                DELETE FROM api_keys
                WHERE id = %s AND tenant_id = %s
            """, (str(key_id), str(tenant_id)))
            
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete tenant API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete tenant API key"
            )
    
    @staticmethod
    def deactivate_key(user_id: UUID, key_id: UUID, tenant_id: Optional[UUID] = None) -> bool:
        """
        Deactivate an API key.
        
        Args:
            user_id: User ID that owns the key
            key_id: ID of the key to deactivate
            tenant_id: Optional tenant ID for authorization
            
        Returns:
            bool: True if deactivated, False otherwise
        """
        try:
            # Build query to update key
            query = supabase.table('api_keys').update({'is_active': False}).eq('id', str(key_id)).eq('user_id', str(user_id))
            
            # Add tenant scope if needed
            if tenant_id:
                query = query.eq('tenant_id', str(tenant_id))
                
            result = query.execute()
            
            # Check if any row was updated
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to deactivate API key: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate API key"
            )
    
    @staticmethod
    def validate_key(api_key: str, tenant_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return user information if valid.
        
        Args:
            api_key: The API key to validate
            tenant_id: Optional tenant ID to scope the validation
            
        Returns:
            Optional[Dict[str, Any]]: User data if key is valid, else None
        """
        try:
            logger.info("--- Starting API Key Validation ---")
            key_hash = APIKeyService._hash_key(api_key)
            logger.info(f"Hashed incoming API key to: {key_hash}")
            
            query = supabase.table('api_keys').select('*').eq('key', key_hash)
            
            if tenant_id:
                logger.info(f"Scoping query to tenant_id: {tenant_id}")
                query = query.eq('tenant_id', str(tenant_id))

            result = query.execute()
            logger.info(f"Supabase query result: {result.data}")

            if not result.data:
                logger.warning(f"API key with hash {key_hash} not found in database.")
                return None
            
            key_data = result.data[0]
            logger.info(f"Found key data: {key_data}")

            if not key_data.get('is_active', True):
                logger.warning(f"API key {key_data['id']} is inactive.")
                return None

            if key_data.get('expires_at'):
                expires_at = datetime.fromisoformat(key_data['expires_at'])
                if expires_at < datetime.utcnow():
                    logger.warning(f"API key {key_data['id']} has expired.")
                    return None

            user_id = key_data.get('user_id')
            if not user_id:
                logger.error("Key data found but no user_id associated.")
                return None
            
            try:
                # Use the admin client to fetch user details by ID
                logger.info(f"Fetching user details for user_id: {user_id}")
                user_response = supabase.auth.admin.get_user_by_id(user_id)
                user = user_response.user
                logger.info(f"Successfully fetched user: {user.email}")
            except Exception as e:
                logger.error(f"Failed to fetch user by id {user_id}: {str(e)}")
                return None

            # Update last used timestamp (can be done in the background)
            # supabase.table('api_keys').update({'last_used': datetime.utcnow().isoformat()}).eq('id', key_data['id']).execute()

            return {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "metadata": user.user_metadata or {},
                "roles": key_data.get("roles", []),
                "tenant_id": key_data.get("tenant_id"),
            }
        except Exception as e:
            logger.error(f"API key validation failed unexpectedly: {str(e)}")
            return None 