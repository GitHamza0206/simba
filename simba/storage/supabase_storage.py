import logging
import os
from pathlib import Path
from typing import Optional, Dict

from fastapi import UploadFile
from supabase import Client
from storage3.exceptions import StorageApiError

from simba.core.config import settings
from simba.storage.base import StorageProvider
from simba.auth.supabase_client import SupabaseClientSingleton

logger = logging.getLogger(__name__)


class SupabaseStorageProvider(StorageProvider):
    """Supabase storage provider"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.client: Client = SupabaseClientSingleton.get_instance()
        self.bucket = settings.storage.supabase_bucket
        
        # Check if bucket exists, if not log a warning
        try:
            self.client.storage.get_bucket(self.bucket)
            logger.info(f"Using existing Supabase bucket: {self.bucket}")
        except StorageApiError as e:
            logger.warning(f"Error checking bucket existence: {str(e)}")
            # Check if the error message indicates bucket doesn't exist
            if "not found" in str(e).lower():
                logger.warning(
                    f"Bucket {self.bucket} does not exist. Please create it in the Supabase dashboard "
                    "with appropriate RLS policies. Using default bucket 'simba-bucket' instead."
                )
                self.bucket = settings.storage.supabase_bucket
            else:
                logger.error(f"Error checking bucket existence: {str(e)}")
                raise
            
        # Create temp directory if it doesn't exist
        self.temp_dir = Path(settings.paths.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Map of storage paths to local paths
        self.path_mapping: Dict[str, Path] = {}
    
    async def save_file(self, file_path: Path, file: UploadFile) -> Path:
        """Save a file to Supabase storage"""
        try:
            # Convert path to object name
            object_name = str(file_path).replace("\\", "/")
            
            # Create a temporary file locally first
            local_file_path = self.temp_dir / file_path.name
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read file content
            content = await file.read()
            
            # Save locally
            with open(local_file_path, "wb") as f:
                f.write(content)
            
            # Upload to Supabase
            with open(local_file_path, "rb") as f:
                self.client.storage.from_(self.bucket).upload(
                    object_name,
                    f,
                    {"content-type": file.content_type}
                )
            
            # Reset file pointer for subsequent reads
            await file.seek(0)
            
            # Store mapping between storage path and local path
            self.path_mapping[str(file_path)] = local_file_path
            
            return local_file_path
            
        except Exception as e:
            logger.error(f"Error saving file to Supabase: {str(e)}")
            raise
    
    async def get_file(self, file_path: Path) -> Optional[bytes]:
        """Retrieve a file from Supabase storage"""
        try:
            # Check if we have a local copy first
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        return f.read()
            
            # If not, get from Supabase
            object_name = str(file_path).replace("\\", "/")
            response = self.client.storage.from_(self.bucket).download(object_name)
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving file from Supabase: {str(e)}")
            return None
    
    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file from Supabase storage"""
        try:
            # Delete from Supabase
            object_name = str(file_path).replace("\\", "/")
            self.client.storage.from_(self.bucket).remove([object_name])
            
            # Delete local copy if exists
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    os.remove(local_path)
                del self.path_mapping[str(file_path)]
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {str(e)}")
            return False
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists in Supabase storage"""
        try:
            # Check local first
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    return True
            
            # Check Supabase
            object_name = str(file_path).replace("\\", "/")
            self.client.storage.from_(self.bucket).get_public_url(object_name)
            return True
            
        except Exception as e:
            logger.error(f"Error checking file existence in Supabase: {str(e)}")
            return False 