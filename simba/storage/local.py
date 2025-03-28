import os
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from simba.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_path: Path, file: UploadFile) -> Path:
        """Save a file to local storage"""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = await file.read()
        with open(full_path, "wb") as f:
            f.write(content)

        return full_path

    async def get_file(self, file_path: Path) -> Optional[bytes]:
        """Retrieve a file from local storage"""
        full_path = self.base_path / file_path
        if not full_path.exists():
            return None

        with open(full_path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file from local storage"""
        full_path = self.base_path / file_path
        if not full_path.exists():
            return False

        try:
            os.remove(full_path)
            return True
        except Exception:
            return False

    async def file_exists(self, file_path: Path) -> bool:
        """Check if a file exists in local storage"""
        full_path = self.base_path / file_path
        return full_path.exists()
