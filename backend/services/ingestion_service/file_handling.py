import os
import json
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
from core.config import settings
import io

import logging
logger = logging.getLogger(__name__)

# Use the base_dir from settings
UPLOAD_DIR = settings.paths.base_dir / settings.paths.upload_dir
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB




# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_file_locally(file: UploadFile, folder_path: Path) -> Path:
    """
    Saves the uploaded file to a unique directory under UPLOAD_DIR 
    and returns the path to the newly created directory.
    """
    # Ensure folder_path is a Path object
    if isinstance(folder_path, str):
        folder_path = Path(folder_path)
        
    # Create the directory
    folder_path.mkdir(exist_ok=True)

    file_size = 0
    file_path = folder_path / file.filename

    # Reset file pointer to beginning
    file.file.seek(0)

    with open(file_path, "wb") as local_file:
        content = file.file.read()
        file_size = len(content)
        if file_size > MAX_FILE_SIZE:
            # Cleanup folder if file is too large
            for item in folder_path.iterdir():
                item.unlink()
            folder_path.rmdir()
            raise HTTPException(
                status_code=400,
                detail="File size exceeds maximum limit of 200MB"
            )
        local_file.write(content)

    # Reset file pointer for potential future use
    file.file.seek(0)

    size_in_mb = round(file_size / (1024 * 1024), 2)
    metadata = {
        "filename": file.filename,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_size_bytes": file_size,
        "file_size_mb": size_in_mb,
        "folder_path": str(folder_path),
        "file_path": str(file_path),
    }
    
    metadata_path = folder_path / f"{file.filename.split('.')[0]}.json"
    with open(metadata_path, "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, indent=2, ensure_ascii=False)

    return folder_path


def load_file_from_path(file_path: Path) -> UploadFile:
    """
    this functions loads the markdown file from the file_path 
    and returns an UploadFile object

    """
    try:
        file_path_md = file_path.split('.')[0] + '.md'
        if not os.path.exists(file_path_md):
            raise HTTPException(status_code=404, detail="File not found")
        
        with open(file_path_md, "rb") as file:
            content = file.read()
        
        return UploadFile(filename=file_path_md, file=io.BytesIO(content))
    
    except Exception as e:
        logger.error(f"Error loading file from path: {e}")
        raise e
