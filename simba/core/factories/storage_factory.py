from pathlib import Path
from typing import Dict, Type

from simba.core.config import settings
from simba.storage.base import StorageProvider
from simba.storage.local import LocalStorageProvider
from simba.storage.minio import MinIOStorageProvider


class StorageFactory:
    """Factory for creating storage providers"""

    _providers: Dict[str, Type[StorageProvider]] = {
        "local": LocalStorageProvider,
        "minio": MinIOStorageProvider,
    }

    @classmethod
    def get_storage_provider(cls) -> StorageProvider:
        """Get the configured storage provider

        Returns:
            StorageProvider: The configured storage provider instance
        """
        provider_type = settings.storage.provider.lower()
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown storage provider: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(Path(settings.paths.upload_dir))
