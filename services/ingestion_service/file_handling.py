import aiofiles

async def save_file_locally(file: UploadFile, store_path: Path) -> None:
    """Save uploaded file to local storage asynchronously"""
    store_path.mkdir(parents=True, exist_ok=True)
    file_path = store_path / file.filename
    
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
    
    await file.seek(0)  # Reset file pointer for subsequent reads