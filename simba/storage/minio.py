import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from simba.core.config import settings
from simba.storage.base import StorageProvider

logger = logging.getLogger(__name__)


class MinIOStorageProvider(StorageProvider):
    """MinIO storage provider"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.client = Minio(
            settings.storage.minio_endpoint,
            access_key=settings.storage.minio_access_key,
            secret_key=settings.storage.minio_secret_key,
            secure=settings.storage.minio_secure
        )
        self.bucket = settings.storage.minio_bucket
        
        # Create bucket if it doesn't exist
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            
        # Create temp directory if it doesn't exist
        self.temp_dir = Path(settings.paths.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Map of S3 paths to local paths
        self.path_mapping: Dict[str, Path] = {}
    
    async def save_file(self, file_path: Path, file: UploadFile) -> Path:
        """Save a file to MinIO storage"""
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
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=open(local_file_path, "rb"),
                length=local_file_path.stat().st_size,
                content_type=file.content_type
            )
            
            # Reset file pointer for subsequent reads
            await file.seek(0)
            
            # Store mapping between S3 path and local path
            self.path_mapping[str(file_path)] = local_file_path
            
            return local_file_path
            
        except Exception as e:
            logger.error(f"Error saving file to MinIO: {str(e)}")
            raise
    
    async def get_file(self, file_path: Path) -> Optional[bytes]:
        """Retrieve a file from MinIO storage"""
        try:
            # Check if we have a local copy first
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    with open(local_path, "rb") as f:
                        return f.read()
            
            # If not, get from MinIO
            object_name = str(file_path).replace("\\", "/")
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            return response.read()
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            logger.error(f"Error retrieving file from MinIO: {str(e)}")
            raise
    
    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file from MinIO storage"""
        try:
            # Delete from MinIO
            object_name = str(file_path).replace("\\", "/")
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            # Delete local copy if exists
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    os.remove(local_path)
                del self.path_mapping[str(file_path)]
                
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"Error deleting file from MinIO: {str(e)}")
            return False
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists in MinIO storage"""
        try:
            # Check local first
            if str(file_path) in self.path_mapping:
                local_path = self.path_mapping[str(file_path)]
                if local_path.exists():
                    return True
            
            # Check MinIO
            object_name = str(file_path).replace("\\", "/")
            self.client.stat_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"Error checking file existence in MinIO: {str(e)}")
            return False 