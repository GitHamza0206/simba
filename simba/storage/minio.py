import os
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error

from simba.core.config import settings
from simba.storage.base import StorageProvider


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
    
    async def save_file(self, file_path: Path, file: UploadFile) -> Path:
        """Save a file to MinIO storage"""
        try:
            # Read file content
            content = await file.read()
            
            # Convert path to object name
            object_name = str(file_path).replace("\\", "/")
            
            # Upload to MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=content,
                length=len(content),
                content_type=file.content_type
            )
            
            return file_path
            
        except S3Error as e:
            logger.error(f"Error saving file to MinIO: {str(e)}")
            raise
    
    async def get_file(self, file_path: Path) -> Optional[bytes]:
        """Retrieve a file from MinIO storage"""
        try:
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
            object_name = str(file_path).replace("\\", "/")
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"Error deleting file from MinIO: {str(e)}")
            return False
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists in MinIO storage"""
        try:
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