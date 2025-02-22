import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import aiofiles
from simba.core.config import settings
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)

# Use the base_dir from settings
UPLOAD_DIR = settings.paths.base_dir / settings.paths.upload_dir
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def save_file_locally(file: UploadFile, store_path: Path) -> None:
    """Save uploaded file to local storage asynchronously"""
    store_path.mkdir(parents=True, exist_ok=True)
    file_path = store_path / file.filename
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    await file.seek(0)  #
def delete_file_locally(file_path: Path):
    """
    Deletes the file from the local filesystem
    """
    if os.path.exists(file_path):
        os.remove(file_path)    
    return True

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
