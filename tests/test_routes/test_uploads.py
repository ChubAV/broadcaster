import re

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi import UploadFile as FastAPIUploadFile
from httpx import AsyncClient, ASGITransport
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.routes.uploads import safe_filename, sniff_image


@pytest_asyncio.fixture
async def upload_settings():
    return Settings(
        _env_file=None,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
        s3_endpoint_url="https://s3.example.com",
        s3_access_key="AKID",
        s3_secret_key="SECRET",
        s3_bucket_name="test-bucket",
        s3_public_url="https://cdn.example.com/test-bucket",
    )


@pytest_asyncio.fixture
async def upload_client(db_session, upload_settings):
    app = create_app(settings=upload_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: upload_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def upload_auth_headers(upload_client):
    """Register a user and return auth headers for the upload client."""
    await upload_client.post("/api/auth/register", json={
        "email": "uploader@test.com",
        "password": "testpass123",
        "name": "Upload User",
    })
    resp = await upload_client.post("/api/auth/login", json={
        "email": "uploader@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_png_bytes():
    """Create a minimal valid 1x1 PNG image in bytes."""
    import struct
    import zlib

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    raw_data = b"\x00\x00\x00\x00"  # filter byte + 1 pixel RGB
    idat = chunk(b"IDAT", zlib.compress(raw_data))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def make_jpeg_bytes():
    """Минимальные байты, начинающиеся с сигнатуры JPEG (SOI + APP0)."""
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00" + b"\x00" * 16


def make_gif_bytes(version: bytes = b"89a"):
    """Минимальные байты GIF заданной версии (``87a`` или ``89a``)."""
    return b"GIF" + version + b"\x01\x00\x01\x00\x00\x00\x00" + b"\x00" * 8


def make_webp_bytes():
    """Байты WebP: ``RIFF``, четыре байта размера, затем ``WEBP``.

    Байты 4..8 — длина файла; они произвольны и намеренно НЕ нулевые, чтобы
    проверка не могла случайно опереться на них вместо метки формата.
    """
    return b"RIFF" + b"\x24\x00\x00\x00" + b"WEBP" + b"VP8 " + b"\x00" * 16


# Вектор CR-02: SVG — тоже «изображение», но исполняемое. Отданный браузеру с
# origin хранилища, он выполняет свой скрипт в его контексте.
SVG_BYTES = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
    b"<script>alert(1)</script></svg>"
)


# --- CR-01: нормализация клиентского имени файла ------------------------------
#
# Клиентское имя файла в составном запросе полностью подконтрольно отправителю и
# участвует в построении ключа объекта хранилища. Без нормализации сегменты пути
# в имени выводят ключ за префикс пользователя, то есть в чужую область того же
# хранилища. Функция проверяется напрямую, без HTTP: у неё определённые вход и
# выход, и классы входов проверяются каждый отдельно.

SAFE_FILENAME_CHARS = re.compile(r"^[A-Za-z0-9._-]+$")


def test_safe_filename_keeps_plain_name():
    assert safe_filename("test_image.png") == "test_image.png"
    assert safe_filename("photo-01.JPEG") == "photo-01.JPEG"


def test_safe_filename_strips_path_components():
    result = safe_filename("../../etc/passwd.png")

    assert "/" not in result
    assert "\\" not in result
    assert result == "passwd.png"
    assert safe_filename("..\\..\\windows\\evil.png") == "evil.png"
    assert "/" not in safe_filename("/absolute/path/img.png")


def test_safe_filename_drops_quotes_and_spaces():
    result = safe_filename('x" onerror="alert(1)<img>.png')

    assert SAFE_FILENAME_CHARS.match(result), result
    assert '"' not in result
    assert " " not in result
    assert "<" not in result
    assert ">" not in result


def test_safe_filename_falls_back_on_empty():
    assert safe_filename("") != ""
    assert safe_filename(None) != ""
    # Имя, от которого после нормализации не остаётся ни одного звена пути.
    assert safe_filename("../") != ""


def test_safe_filename_truncates():
    result = safe_filename("a" * 300 + ".png")

    assert len(result) <= 100
    assert SAFE_FILENAME_CHARS.match(result), result


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_key_stays_inside_user_prefix(
    mock_s3, upload_client, upload_auth_headers
):
    """Ключ объекта не выходит за префикс пользователя ни при каком имени файла."""
    png_bytes = make_png_bytes()
    hostile = '../../evil x" onerror="alert(1)>.png'

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": (hostile, png_bytes, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    key = response.json()["path"]
    assert re.fullmatch(r"\d+/[0-9a-f]{32}_[A-Za-z0-9._-]+", key), key
    # Ключ, ушедший в хранилище, — тот же самый, что вернулся клиенту.
    assert mock_s3.call_args.kwargs["key"] == key


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_valid_image(mock_s3, upload_client, upload_auth_headers):
    mock_s3.return_value = "1/abc_test_image.png"
    png_bytes = make_png_bytes()

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test_image.png", png_bytes, "image/png")},
        headers=upload_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "test_image.png" in data["path"]

    # Verify S3 was called
    mock_s3.assert_called_once()
    call_kwargs = mock_s3.call_args.kwargs
    assert call_kwargs["content"] == png_bytes
    assert call_kwargs["content_type"] == "image/png"
    assert call_kwargs["bucket"] == "test-bucket"


@pytest.mark.asyncio
async def test_upload_non_image_file(upload_client, upload_auth_headers):
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("document.txt", b"hello world", "text/plain")},
        headers=upload_auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_unauthenticated(upload_client):
    png_bytes = make_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test.png", png_bytes, "image/png")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_image_with_cookie_auth(mock_s3, upload_client):
    """Upload should work with cookie-based auth (used by web UI)."""
    mock_s3.return_value = "1/abc_cookie_image.png"
    await upload_client.post("/api/auth/register", json={
        "email": "cookie@test.com",
        "password": "testpass123",
        "name": "Cookie User",
    })
    resp = await upload_client.post("/api/auth/login", json={
        "email": "cookie@test.com",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    upload_client.cookies.set("access_token", token)

    png_bytes = make_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("cookie_image.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "cookie_image.png" in data["path"]


# --- CR-02: тип изображения определяется по содержимому ------------------------
#
# Заголовок типа в составном запросе подконтролен отправителю ровно так же, как
# имя файла: он тип ОБЪЯВЛЯЕТ, но не доказывает. SVG, принятый под видом PNG,
# исполняет свой скрипт на origin хранилища — это и есть вектор CR-02. Поэтому
# тип берётся из первых байтов содержимого, а присланный заголовок игнорируется.


@pytest.mark.parametrize(
    "make_bytes,expected",
    [
        (make_png_bytes, "image/png"),
        (make_jpeg_bytes, "image/jpeg"),
        (lambda: make_gif_bytes(b"87a"), "image/gif"),
        (lambda: make_gif_bytes(b"89a"), "image/gif"),
        (make_webp_bytes, "image/webp"),
    ],
)
def test_sniff_image_recognises_supported_formats(make_bytes, expected):
    assert sniff_image(make_bytes()) == expected


@pytest.mark.parametrize(
    "content",
    [
        SVG_BYTES,
        b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'/>",
        b"hello world",
        b"",
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3",
        b"GIF88a" + b"\x00" * 16,  # похоже на GIF, но версия не та
        b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"\x00" * 16,  # RIFF, но не WebP
        b"RIFF",  # обрывок: длины и метки формата нет вовсе
    ],
)
def test_sniff_image_rejects_non_images(content):
    assert sniff_image(content) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_bytes,expected",
    [
        (make_png_bytes, "image/png"),
        (make_jpeg_bytes, "image/jpeg"),
        (lambda: make_gif_bytes(b"87a"), "image/gif"),
        (lambda: make_gif_bytes(b"89a"), "image/gif"),
        (make_webp_bytes, "image/webp"),
    ],
)
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_accepts_each_supported_format(
    mock_s3, make_bytes, expected, upload_client, upload_auth_headers
):
    """Каждый из четырёх поддерживаемых форматов принимается по содержимому."""
    response = await upload_client.post(
        "/api/uploads/image",
        # Заголовок типа заведомо неверный: приём должен опираться на содержимое.
        files={"file": ("payload.bin", make_bytes(), "application/octet-stream")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert mock_s3.call_args.kwargs["content_type"] == expected


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_rejects_svg_declared_as_png(
    mock_s3, upload_client, upload_auth_headers
):
    """CR-02: SVG с заголовком ``image/png`` отклоняется и в хранилище не уходит."""
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("logo.png", SVG_BYTES, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert "JPEG" in response.json()["detail"]
    mock_s3.assert_not_called()


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_rejects_non_image_declared_as_image(
    mock_s3, upload_client, upload_auth_headers
):
    """Произвольные байты не проходят ни под каким заголовком типа."""
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("payload.jpg", b"not an image at all", "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    mock_s3.assert_not_called()


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_stores_sniffed_content_type_not_client_header(
    mock_s3, upload_client, upload_auth_headers
):
    """В хранилище уходит распознанный тип, а не присланный клиентом.

    Иначе объект лёг бы в S3 с подконтрольным отправителю ``Content-Type`` и
    отдавался бы браузеру с ним же — вектор CR-02 сохранился бы на выдаче.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("real.png", make_png_bytes(), "image/svg+xml")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert mock_s3.call_args.kwargs["content_type"] == "image/png"


# --- WR-02: предел размера ограничивает ПРИНИМАЕМОЕ, а не только сохраняемое ---
#
# Предел применялся ПОСЛЕ того, как всё тело уже прочитано в память одним
# `await file.read()` без аргумента. `max_image_size_mb` поэтому ограничивал то,
# что СОХРАНЯЕТСЯ, а не то, что ПРИНИМАЕТСЯ: любой аутентифицированный клиент
# заставлял ASGI-воркер удерживать в памяти тело произвольного размера, и путь
# отказа платил ту же цену.
#
# Утверждать один лишь код 400 на превышении бесполезно — он возвращается и на
# дефектном коде. Измеряется поэтому ОБЪЁМ ЧТЕНИЯ.


@pytest_asyncio.fixture
async def oversize_settings(upload_settings):
    """Настройки загрузки с пределом размера 1 МБ.

    Тот же объект, что получает приложение и обработчик: `upload_client` и
    `upload_auth_headers` зависят от той же фикстуры. Дефолтные 5 МБ заставили
    бы держать в тесте лишние мегабайты; предел берётся из настроек, а не из
    литерала, поэтому понизить его достаточно здесь.
    """
    upload_settings.max_image_size_mb = 1
    return upload_settings


def make_oversized_png_bytes(size: int) -> bytes:
    """Тело заданного размера, начинающееся с сигнатуры PNG.

    Сигнатура обязательна: на дефектном коде распознавание типа стоит ВЫШЕ
    проверки размера, и без неё тест померил бы отказ по типу, а не по размеру.
    """
    signature = b"\x89PNG\r\n\x1a\n"
    return signature + b"\x00" * (size - len(signature))


# Аргумента размера не было вовсе — это не то же самое, что явный `read(-1)`.
_NO_SIZE_ARGUMENT = object()


def test_read_measurement_targets_the_class_the_handler_receives():
    """Обёртка чтения накладывается на ТОТ класс, что приходит в обработчик.

    `fastapi.UploadFile` в установленной версии — НЕ тот же класс, а подкласс
    `starlette.datastructures.UploadFile`, и он переопределяет ``read``,
    передавая размер в базовый метод ЯВНО. Приди в обработчик экземпляр
    подкласса, вызов ``await file.read()`` без аргумента дошёл бы до обёртки уже
    с ``size=-1``, и утверждение «обработчик не читал без ограничения размера»
    перестало бы что-либо измерять, оставшись зелёным при полностью
    забуференном теле.

    Поэтому обёртка кладётся на БАЗОВЫЙ класс — его метод в конечном счёте
    вызывают оба, — а то, что в обработчик приходит именно базовый, не
    предполагается, а измеряется в ``test_oversized_upload_is_not_buffered_whole``.
    """
    assert issubclass(FastAPIUploadFile, StarletteUploadFile)


@pytest.fixture
def recorded_reads(monkeypatch):
    """Записывать каждое чтение загруженного файла.

    Для каждого вызова запоминается запрошенный размер порции (``None`` —
    аргумента не было вовсе), число фактически возвращённых байтов и класс
    объекта, у которого вызвали чтение.
    """
    calls: list[tuple[int | None, int, type]] = []
    original = StarletteUploadFile.read

    async def recording_read(self, size=_NO_SIZE_ARGUMENT):
        if size is _NO_SIZE_ARGUMENT:
            chunk = await original(self)
            calls.append((None, len(chunk), type(self)))
        else:
            chunk = await original(self, size)
            calls.append((size, len(chunk), type(self)))
        return chunk

    monkeypatch.setattr(StarletteUploadFile, "read", recording_read)
    return calls


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_oversized_upload_is_not_buffered_whole(
    mock_s3, oversize_settings, upload_client, upload_auth_headers, recorded_reads
):
    """Превышение предела ПРЕРЫВАЕТ чтение, а не проверяется после него."""
    max_bytes = oversize_settings.max_image_size_mb * 1024 * 1024
    body = make_oversized_png_bytes(3 * 1024 * 1024)

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("big.png", body, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert "File size exceeds" in response.json()["detail"]
    mock_s3.assert_not_called()

    assert recorded_reads, "обработчик не прочитал ни байта — измерять нечего"
    # «Аргумента не было» различимо только у базового класса: подкласс FastAPI
    # передаёт размер в базовый метод явно. Факт измеряется, а не предполагается.
    assert {cls for _, _, cls in recorded_reads} == {StarletteUploadFile}, (
        "чтение пришло не от того класса, на который наложена обёртка — "
        "различить «без аргумента» и «read(-1)» больше нельзя"
    )
    requested = [size for size, _, _ in recorded_reads]
    assert None not in requested, (
        "обработчик запросил содержимое БЕЗ ограничения размера: всё тело "
        f"оказалось в памяти (запрошенные размеры: {requested})"
    )
    total = sum(length for _, length, _ in recorded_reads)
    # Одна порция сверх предела неизбежна: превышение обнаруживается ровно тем
    # блоком, который его создал. Больше одной означает, что чтение не прервалось.
    assert total <= max_bytes + max(requested), (
        f"прочитано {total} байт при пределе {max_bytes}: чтение не прервалось"
    )


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_oversized_upload_is_refused_with_size_message(
    mock_s3, oversize_settings, upload_client, upload_auth_headers
):
    """Страж формулировки: текст и код отказа по размеру не меняются.

    Зелен и до правки, и после: он закрепляет ответ, а не воспроизводит дефект.
    Дефект — в объёме чтения, и его меряет тест выше.
    """
    body = make_oversized_png_bytes(3 * 1024 * 1024)

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("big.png", body, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"File size exceeds {oversize_settings.max_image_size_mb}MB limit"
    )
    mock_s3.assert_not_called()
