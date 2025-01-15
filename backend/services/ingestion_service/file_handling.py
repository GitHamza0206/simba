import os
import json
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile, HTTPException
from core.config import settings

# Use the base_dir from settings
UPLOAD_DIR = settings.paths.base_dir / settings.paths.upload_dir
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_file_locally(file: UploadFile) -> Path:
    """
    Saves the uploaded file to a unique directory under UPLOAD_DIR 
    and returns the path to the newly created directory.
    """
    # Create a unique folder name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"{timestamp}_{file.filename}".replace(".", "_")
    folder_path = UPLOAD_DIR / folder_name
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
    
    metadata_path = folder_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as meta_file:
        json.dump(metadata, meta_file, indent=2, ensure_ascii=False)

    return folder_path
