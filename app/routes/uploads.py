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

# Размер порции чтения тела. Одна порция — то, на что предел размера может быть
# превышен, прежде чем чтение прервётся: превышение обнаруживает ровно тот блок,
# который его создал.
UPLOAD_CHUNK_SIZE = 64 * 1024


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
#
# Список закрыт на двух форматах, и закрыт он не разбором самих форматов, а тем,
# что принятый файл обязан пережить ОТПРАВКУ. Загрузка здесь не самоцель:
# картинка уходит в рассылку, и послать её ОБЫЧНЫМ изображением должны уметь все
# три мессенджера сразу. Таких форматов ровно два — JPEG и PNG. С остальными
# происходит следующее:
#
#  * WebP. `app/messengers/telegram_user.py:200-221` кладёт картинку в
#    `io.BytesIO`, берёт `buf.name` из имени файла в URL «чтобы сохранить
#    расширение», и зовёт `client.send_file(..., force_document=False)`. Тип медиа
#    Telethon выводит именно из этого расширения: на `.webp` он собирает
#    документ-СТИКЕР, а стикер Telegram не принимает ни в альбоме, ни с подписью.
#    Это и есть поломка из issue #39. В WhatsApp то же самое с другой стороны:
#    `wa_worker/index.js:453-477` зовёт Baileys как `{ image, mimetype }`, где
#    mimetype — Content-Type сохранённого объекта, а `image/webp` для WhatsApp —
#    mimetype СТИКЕРА, то есть полем `image` уходит не сообщение-картинка.
#  * GIF. Для WhatsApp это не годная статическая картинка — анимацию там ожидают
#    видеофайлом. Для Telegram это не фотография: файл становится анимацией либо
#    документом, что вдобавок ломает смешанный альбом.
#  * MAX (`max_worker/main.py:567-600`) оборачивает файл в `Photo(path=...)` из
#    pymax — растровый путь загрузки фотографии, рассчитанный на JPEG и PNG.
#
# Отказ на этом эндпоинте стоит пользователю одного клика; та же ошибка, дожившая
# до рассылки, стоит несостоявшейся рассылки, и узнаёт о ней пользователь тогда,
# когда чинить уже поздно. Поэтому формат, переживающий загрузку, но не отправку,
# отвергается здесь, а не там. Ни один уже сохранённый объект при этом не
# переписывается: сужение действует на входе и только вперёд.
_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)

# Та же строка дословно лежит в `app/templates/ads/form.html` как
# `UPLOAD_TYPE_ERROR`: обработчик загрузки в редакторе показывает свою копию на
# любом ответе 400 и `detail` из ответа не читает. Совпадение копий держит
# render-тест в `tests/test_pages/test_ads_editor.py`, а не дисциплина.
#
# Придаточное про мессенджеры не украшение: пользователь, чей WebP отвергнут,
# видит заведомо корректное изображение и без объяснения читает отказ как
# поломку сервиса.
UNSUPPORTED_IMAGE_MESSAGE = (
    "Не удалось загрузить: подойдут только изображения JPEG или PNG — "
    "другие форматы принимают не все мессенджеры. Выберите другой файл."
)


def sniff_image(content: bytes) -> str | None:
    """Определить MIME-тип изображения по первым байтам содержимого.

    Возвращает тип для JPEG и PNG либо ``None`` для всего остального. Список
    закрыт: распознаются ровно те два формата, которые названы в тексте отказа,
    и ровно те, которые все три мессенджера отправляют обычной картинкой.

    SVG в список не входит осознанно — это XML-документ, способный нести скрипт,
    и именно он является вектором CR-02.
    """
    for signature, mime in _IMAGE_SIGNATURES:
        if content.startswith(signature):
            return mime

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
    # Чтение ПОРЦИЯМИ с накоплением, а не `await file.read()` без аргумента.
    # Единовременное чтение материализовало бы всё тело до того, как предел
    # вообще проверен: `max_image_size_mb` тогда ограничивает то, что
    # СОХРАНЯЕТСЯ, а не то, что ПРИНИМАЕТСЯ, и любой аутентифицированный клиент
    # заставляет ASGI-воркер удерживать в памяти тело произвольного размера
    # (WR-02). Путь отказа платил ту же цену: распознавание типа стояло выше
    # проверки размера и уже успевало получить всё тело.
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    chunks: list[bytes] = []
    received = 0
    while True:
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        received += len(chunk)
        if received > max_bytes:
            # Прерывание на первом же превышении: остаток тела не читается, и
            # собранные порции не склеиваются вовсе.
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {settings.max_image_size_mb}MB limit",
            )
        chunks.append(chunk)

    content = b"".join(chunks)

    # Тип берётся из содержимого, а не из присланного клиентом заголовка
    # (CR-02). Проверка стоит теперь НИЖЕ предела размера, и это неизбежно: при
    # потоковом чтении предел срабатывает раньше, чем содержимое целиком
    # доступно для распознавания. Следствие наблюдаемо и намеренно — тело,
    # которое одновременно превышает предел и не является изображением, получает
    # отказ по размеру, а не по типу. Оба отказа — код 400, ни один вход не
    # становится мягче.
    content_type = sniff_image(content)
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=UNSUPPORTED_IMAGE_MESSAGE,
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
