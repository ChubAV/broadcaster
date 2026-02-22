from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.config import Settings
from app.dependencies import get_current_user_id, get_settings
from app.services.s3 import upload_file_to_s3

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

    # Generate unique key
    filename = f"{uuid4().hex}_{file.filename}"
    key = f"{user_id}/{filename}"

    # Upload to S3
    await upload_file_to_s3(
        content=content,
        key=key,
        content_type=file.content_type,
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket=settings.s3_bucket_name,
        region=settings.s3_region,
    )

    return {"path": key}
