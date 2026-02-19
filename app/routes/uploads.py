from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.config import Settings
from app.dependencies import get_current_user_id, get_settings

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/image")
async def upload_image(
    file: UploadFile,
    user_id: int = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
):
    # Validate file is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file content and validate size
    content = await file.read()
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.max_image_size_mb}MB limit",
        )

    # Generate unique filename
    filename = f"{uuid4().hex}_{file.filename}"
    user_dir = Path(settings.upload_dir) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_dir / filename
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Return relative path from upload_dir
    relative_path = f"{user_id}/{filename}"
    return {"path": relative_path}
