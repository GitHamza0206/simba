import os
from pathlib import Path
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from core.config import settings

class FolderCreate(BaseModel):
    name: str
    parent_path: str = "/"

class FolderMove(BaseModel):
    document_id: str
    folder_id: str

class Folder(BaseModel):
    id: str
    name: str
    path: str
    created_at: str
    parent_folder: Optional[str] = None

def create_folder(folder_name: str, parent_path: str = "/") -> Folder:
    """Create a new folder"""
    try:
        # Sanitize folder name
        folder_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_'))
        
        # Create folder path
        folder_path = settings.paths.uploads_dir / folder_name
        
        # Check if folder already exists
        if folder_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Folder {folder_name} already exists in this location"
            )
        
        # Create folder
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Create folder metadata
        folder_metadata = Folder(
            id=str(uuid.uuid4()),
            name=folder_name,
            path=folder_name,
            created_at=datetime.now().isoformat(),
            parent_folder=None if parent_path == "/" else parent_path
        )
        
        return folder_metadata
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating folder: {str(e)}"
        )

def get_folders() -> List[Folder]:
    """Get all folders"""
    try:
        folders = []
        base_path = settings.paths.uploads_dir
        
        # Only get immediate children folders
        for item in base_path.iterdir():
            if item.is_dir():
                folders.append(Folder(
                    id=str(uuid.uuid4()),
                    name=item.name,
                    path=str(item.relative_to(base_path)),
                    created_at=datetime.fromtimestamp(item.stat().st_ctime).isoformat(),
                    parent_folder=None
                ))
        
        return folders
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching folders: {str(e)}"
        )

def delete_folder(folder_id: str) -> bool:
    """Delete a folder"""
    try:
        folder = next((f for f in get_folders() if f.id == folder_id), None)
        if not folder:
            raise HTTPException(
                status_code=404,
                detail=f"Folder {folder_id} not found"
            )
        
        folder_path = settings.paths.uploads_dir / folder.path
        if folder_path.exists():
            # Remove folder and contents
            import shutil
            shutil.rmtree(folder_path)
        
        return True
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting folder: {str(e)}"
        )

def move_to_folder(file_path: str, folder_id: str) -> str:
    """Move a file to a folder"""
    try:
        # Get target folder
        folder = next((f for f in get_folders() if f.id == folder_id), None)
        if not folder:
            raise HTTPException(
                status_code=404,
                detail=f"Folder {folder_id} not found"
            )
        
        # Create Path objects
        src_path = Path(file_path)
        dest_path = settings.paths.uploads_dir / folder.path / src_path.name
        
        # Move file
        os.rename(src_path, dest_path)
        
        return str(dest_path)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error moving file: {str(e)}"
        )

