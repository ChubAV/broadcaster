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


# Заголовок типа из составного запроса подконтролен отправителю ровно так же, как
# имя файла: он тип ОБЪЯВЛЯЕТ, но не доказывает. SVG, принятый под видом PNG,
# отдаётся браузеру с origin хранилища и исполняет свой скрипт в его контексте —
# это вектор CR-02. Поэтому тип определяется по первым байтам содержимого, а
# присланный заголовок не используется нигде, включая запись в хранилище.
#
# Проверка написана руками намеренно, без библиотеки: `python-magic` тянет
# системный `libmagic` в Docker-образ; `imghdr` удалён из stdlib в Python 3.13;
# `Pillow` присутствует лишь транзитивно через `qrcode[pil]`, а `Image.open()` на
# недоверенном файле добавил бы вектор decompression bomb ровно тому эндпоинту,
# который здесь чинится.
_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)

# WebP — единственный из четырёх, чья метка формата стоит не в начале: сперва
# `RIFF`, затем четыре байта размера файла (произвольные), и только потом `WEBP`.
_RIFF_MAGIC = b"RIFF"
_WEBP_MAGIC = b"WEBP"

UNSUPPORTED_IMAGE_MESSAGE = (
    "Не удалось загрузить: подойдут только изображения JPEG, PNG, WebP или GIF. "
    "Выберите другой файл."
)


def sniff_image(content: bytes) -> str | None:
    """Определить MIME-тип изображения по первым байтам содержимого.

    Возвращает тип для JPEG, PNG, GIF (обеих версий) и WebP либо ``None`` для
    всего остального. Список закрыт: распознаются ровно те четыре формата,
    которые названы в тексте отказа.

    SVG в список не входит осознанно — это XML-документ, способный нести скрипт,
    и именно он является вектором CR-02.
    """
    for signature, mime in _IMAGE_SIGNATURES:
        if content.startswith(signature):
            return mime

    if content[:4] == _RIFF_MAGIC and content[8:12] == _WEBP_MAGIC:
        return "image/webp"

    return None


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
    # Read file content, then validate the type by its first bytes. Чтение
    # поднято выше проверки типа намеренно: тип берётся из содержимого, а не из
    # присланного клиентом заголовка (CR-02).
    content = await file.read()

    content_type = sniff_image(content)
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UNSUPPORTED_IMAGE_MESSAGE,
        )

    # Validate size
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
            # Распознанный тип, а не присланный клиентом: иначе объект лёг бы в
            # хранилище с подконтрольным отправителю Content-Type и отдавался бы
            # браузеру с ним же — вектор CR-02 пережил бы проверку на входе.
            content_type=content_type,
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
