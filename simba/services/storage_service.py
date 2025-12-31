"""MinIO storage service for file management."""

from datetime import timedelta
from functools import lru_cache
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from simba.core.config import settings


@lru_cache
def get_minio_client() -> Minio:
    """Get cached MinIO client instance."""
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    """Create the bucket if it doesn't exist."""
    client = get_minio_client()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_file(file_data: bytes, object_key: str, content_type: str) -> str:
    """Upload a file to MinIO.

    Args:
        file_data: File content as bytes.
        object_key: The object key (path) in MinIO.
        content_type: MIME type of the file.

    Returns:
        The object key of the uploaded file.
    """
    client = get_minio_client()
    ensure_bucket()

    client.put_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
        data=BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )

    return object_key


def download_file(object_key: str) -> bytes:
    """Download a file from MinIO.

    Args:
        object_key: The object key (path) in MinIO.

    Returns:
        File content as bytes.
    """
    client = get_minio_client()

    response = client.get_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
    )

    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_file(object_key: str) -> None:
    """Delete a file from MinIO.

    Args:
        object_key: The object key (path) in MinIO.
    """
    client = get_minio_client()

    client.remove_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
    )


def get_presigned_url(object_key: str, expires: timedelta = timedelta(hours=1)) -> str:
    """Generate a presigned URL for direct file download.

    Args:
        object_key: The object key (path) in MinIO.
        expires: URL expiration time. Default is 1 hour.

    Returns:
        Presigned URL string.
    """
    client = get_minio_client()

    return client.presigned_get_object(
        bucket_name=settings.minio_bucket,
        object_name=object_key,
        expires=expires,
    )


def file_exists(object_key: str) -> bool:
    """Check if a file exists in MinIO.

    Args:
        object_key: The object key (path) in MinIO.

    Returns:
        True if file exists, False otherwise.
    """
    client = get_minio_client()

    try:
        client.stat_object(
            bucket_name=settings.minio_bucket,
            object_name=object_key,
        )
        return True
    except S3Error:
        return False
