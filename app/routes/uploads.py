import re
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.config import Settings
from app.dependencies import get_current_user_id, get_settings
from app.services.s3 import upload_file_to_s3

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Клиентское имя файла из составного запроса полностью подконтрольно отправителю
# и участвует в построении ключа объекта: без нормализации сегменты пути в имени
# выводят ключ за префикс пользователя, то есть в чужую область того же хранилища.
_PATH_SEPARATORS = re.compile(r"[\\/]")
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")
MAX_FILENAME_LENGTH = 100
FALLBACK_FILENAME = "upload"


def safe_filename(filename: str | None) -> str:
    """Свести клиентское имя файла к безопасному звену ключа объекта.

    Сегменты пути отбрасываются целиком (остаётся только последнее звено), всё
    вне набора «латинские буквы, цифры, точка, дефис, подчёркивание» заменяется
    на подчёркивание, результат обрезается до ``MAX_FILENAME_LENGTH``.

    Обрезка идёт ПОСЛЕ замены намеренно: усечение до неё могло бы оставить
    половину заменяемой последовательности. Если после нормализации не осталось
    ничего, возвращается непустое значение по умолчанию — пустое звено сделало бы
    ключ оканчивающимся на подчёркивание и неотличимым от соседних.
    """
    if not filename:
        return FALLBACK_FILENAME

    last_segment = _PATH_SEPARATORS.split(filename)[-1]
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", last_segment)[:MAX_FILENAME_LENGTH]
    return cleaned or FALLBACK_FILENAME


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

    # Generate unique key. Формат ключа прежний — идентификатор пользователя,
    # слеш, шестнадцатеричный токен, подчёркивание, имя; меняется только то, что
    # имя нормализуется. Уже сохранённые ключи не переименовываются.
    filename = f"{uuid4().hex}_{safe_filename(file.filename)}"
    key = f"{user_id}/{filename}"

    # Upload to S3
    try:
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload image to storage",
        )

    return {"path": key}
