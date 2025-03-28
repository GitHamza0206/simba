from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from fastapi import UploadFile


class StorageProvider(ABC):
    """Base class for storage providers"""

    @abstractmethod
    async def save_file(self, file_path: Path, file: UploadFile) -> Path:
        """Save a file to storage

        Args:
            file_path: The path where the file should be saved
            file: The file to save

        Returns:
            Path: The actual path where the file was saved
        """
        pass

    @abstractmethod
    async def get_file(self, file_path: Path) -> Optional[bytes]:
        """Retrieve a file from storage

        Args:
            file_path: The path of the file to retrieve

        Returns:
            Optional[bytes]: The file contents if found, None otherwise
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file from storage

        Args:
            file_path: The path of the file to delete

        Returns:
            bool: True if file was deleted, False otherwise
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists in storage

        Args:
            file_path: The path to check

        Returns:
            bool: True if file exists, False otherwise
        """
        pass
