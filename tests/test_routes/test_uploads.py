import io
import re

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi import UploadFile as FastAPIUploadFile
from httpx import AsyncClient, ASGITransport
from PIL import Image
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.main import create_app
from app.services.image_keys import own_image_keys, thumb_key
from app.services.images import DELIVERY_MAX_EDGE, MAX_DECODED_PIXELS
from app.routes.uploads import (
    _IMAGE_SIGNATURES,
    FALLBACK_FILENAME,
    MAX_FILENAME_LENGTH,
    OVERSIZED_IMAGE_MESSAGE,
    UNSUPPORTED_IMAGE_MESSAGE,
    retarget_extension,
    safe_filename,
    sniff_image,
)


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
    """Минимальные байты, начинающиеся с сигнатуры JPEG (SOI + APP0).

    ⚠️ Эти байты НЕ ДЕКОДИРУЮТСЯ. Для проверок ``sniff_image`` этого хватало —
    там читаются первые три байта, — но с issue #40 обработчик изображение
    ещё и открывает, поэтому по HTTP-пути такой вход означает отказ, а не
    приём. Построитель сохранён и получил СВОЙ тест
    (``test_upload_rejects_signature_without_a_decodable_image``): «сигнатура
    верна, картинки нет» — отдельный класс входа, и терять его нельзя.
    """
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00" + b"\x00" * 16


# --- issue #40: НАСТОЯЩИЕ изображения для HTTP-пути ---------------------------
#
# Построители живут ЗДЕСЬ, а не импортируются из tests/test_services/test_images.py,
# намеренно: тестовый модуль не библиотека, и импорт одного из другого связал бы
# два файла порядком сборки и превратил бы вспомогательную функцию в неявный
# публичный контракт. Общего у них только приём — набирать крупную картинку
# вставками плитки, потому что поэлементный обход 4000x3000 на чистом Python
# стоил бы десятки секунд каждого прогона суиты.
_TILE_EDGE = 64


def _real_image(size, mode="RGB"):
    """Картинка с изменяющимся содержимым: заливка сжимается почти в ноль."""
    width, height = size
    tile_size = (min(width, _TILE_EDGE), min(height, _TILE_EDGE))
    tile = Image.new(mode, tile_size)
    pixels = tile.load()
    for x in range(tile_size[0]):
        for y in range(tile_size[1]):
            value = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
            pixels[x, y] = value if mode == "RGB" else (*value, 255)

    image = Image.new(mode, size)
    for left in range(0, width, tile_size[0]):
        for top in range(0, height, tile_size[1]):
            image.paste(tile, (left, top))
    return image


def _encode(image, fmt, **kwargs) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **kwargs)
    return buffer.getvalue()


def make_real_jpeg_bytes(size=(4000, 3000)) -> bytes:
    return _encode(_real_image(size), "JPEG")


def make_real_png_bytes(size=(600, 400)) -> bytes:
    """PNG БЕЗ канала прозрачности — по D-4 такой уезжает в хранилище JPEG'ом."""
    return _encode(_real_image(size), "PNG")


def make_real_png_with_alpha_bytes(size=(600, 400)) -> bytes:
    """PNG с настоящей альфой — по D-4 остаётся PNG."""
    image = _real_image(size, mode="RGBA")
    image.putpixel((0, 0), (255, 255, 255, 0))
    return _encode(image, "PNG")


def make_declared_huge_png_bytes(width: int, height: int) -> bytes:
    """PNG, ЗАЯВЛЯЮЩИЙ огромные размеры при крошечном теле (T-Q40-01).

    Настоящая форма декомпрессионной бомбы, а не просто большой файл: предел
    ``max_image_size_mb`` меряет сжатое тело и такой вход пропускает, поэтому
    отказать обязан потолок числа точек, снятый с ЗАГОЛОВКА до декодирования.
    """
    import struct
    import zlib

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        crc = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + payload + crc

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00" * 16))
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + chunk(b"IEND", b"")


def _decode(payload: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(payload))
    image.load()
    return image


def make_gif_bytes(version: bytes = b"89a"):
    """Минимальные байты GIF заданной версии (``87a`` или ``89a``).

    Вход для доказательства ОТКАЗА, а не приёма (issue #39). Построитель
    сохранён именно потому, что отказ надо проверять на настоящих байтах
    формата: мусор отвергается по другой причине и ничего о GIF не доказывает.
    """
    return b"GIF" + version + b"\x01\x00\x01\x00\x00\x00\x00" + b"\x00" * 8


def make_webp_bytes():
    """Байты WebP: ``RIFF``, четыре байта размера, затем ``WEBP``.

    Вход для доказательства ОТКАЗА, а не приёма (issue #39). Байты остаются
    заведомо корректным WebP — иначе тест доказывал бы отказ дефектному файлу,
    тогда как проверяется отказ безупречному.
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
    png_bytes = make_real_png_bytes()
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
    #
    # ⚠️ Утверждение снимается с ПЕРВОГО вызова, а не с последнего (issue #40).
    # `call_args` — это последний вызов, а последним теперь идёт МИНИАТЮРА, и её
    # ключ по построению начинается с приставки, то есть заведомо не равен
    # возвращённому. Прежняя запись после этой задачи меряла бы не то, что
    # утверждает.
    assert mock_s3.call_args_list[0].kwargs["key"] == key


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_valid_image(mock_s3, upload_client, upload_auth_headers):
    """Приём картинки: два объекта в хранилище, и ни один не равен присланному.

    ⚠️ ДВА ПРЕЖНИХ УТВЕРЖДЕНИЯ ОТМЕНЕНЫ СОЗНАТЕЛЬНО (issue #40), и заменены, а
    не выброшены:

    * ``call_kwargs["content"] == png_bytes`` утверждало БАЙТОВОЕ РАВЕНСТВО
      сохранённого присланному. Ровно это правило и отменяет задача: оригинал не
      хранится ни под каким ключом (D-2), в бакет уходит пережатая версия.
      Замена утверждает то, что теперь истинно и ценно: сохранённое всё ещё
      РАЗБИРАЕТСЯ в изображение, то есть пережатие картинку не испортило.
    * ``mock_s3.assert_called_once()`` утверждало единственность объекта. Их
      теперь два — сжатая версия и её миниатюра (D-1), — и замена утверждает
      именно два, а не «хотя бы один»: счёт «хотя бы» пропустил бы потерю
      миниатюры молча.

    Имя `test_image` в ключе сохраняется, а вот расширение — нет: PNG без
    настоящей альфы уходит JPEG'ом, и ключ обязан описывать те байты, что под
    ним лежат (P-5).
    """
    png_bytes = make_real_png_bytes()

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test_image.png", png_bytes, "image/png")},
        headers=upload_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "test_image" in data["path"]

    assert mock_s3.call_count == 2, "сохранены не оба объекта: сжатая версия и миниатюра"
    call_kwargs = mock_s3.call_args_list[0].kwargs
    assert call_kwargs["content"] != png_bytes, "в хранилище ушли исходные байты"
    assert _decode(call_kwargs["content"]).size == (600, 400)
    assert call_kwargs["content_type"] == "image/jpeg"
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
    """Upload should work with cookie-based auth (used by web UI).

    ⚠️ Утверждение о ключе снято с имени файла БЕЗ РАСШИРЕНИЯ (issue #40).
    Прежнее ``"cookie_image.png" in path`` перестало быть истинным не потому,
    что имя потерялось, а потому, что PNG без настоящей альфы сохраняется JPEG
    ом и расширение в ключе приводится к сохранённому формату (P-5). Проверяемое
    свойство — «имя файла доезжает до ключа» — сохранено целиком; из него убрана
    ровно та часть, которую задача изменила намеренно.
    """
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

    png_bytes = make_real_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("cookie_image.png", png_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "cookie_image" in data["path"]


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
        # Ни одну из трёх строк ниже распознать больше нечем, и различение
        # версий GIF или метки внутри RIFF тут ни при чём: обоих контейнеров
        # нет в таблице сигнатур целиком. Случаи оставлены как проверка того,
        # что сужение таблицы не породило совпадения по чужому префиксу.
        b"GIF88a" + b"\x00" * 16,
        b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"\x00" * 16,
        b"RIFF",
    ],
)
def test_sniff_image_rejects_non_images(content):
    assert sniff_image(content) is None


# --- Issue #39: форматы, которые не переживают ОТПРАВКУ ------------------------
#
# Отказ здесь наступает по причине, не имеющей отношения к CR-02: на входе
# честные, корректные изображения. Разбор по мессенджерам — в комментарии над
# ``_IMAGE_SIGNATURES`` в ``app/routes/uploads.py``.


@pytest.mark.parametrize(
    "make_bytes",
    [
        lambda: make_gif_bytes(b"87a"),
        lambda: make_gif_bytes(b"89a"),
        make_webp_bytes,
    ],
    ids=["gif87a", "gif89a", "webp"],
)
def test_sniff_image_rejects_formats_no_messenger_can_send(make_bytes):
    """Настоящие картинки, которых не отправить обычным изображением, отвергаются.

    Отдельный тест, а не дописывание в ``test_sniff_image_rejects_non_images``,
    намеренно. Тот отвергает НЕ-изображения, и его причина — вектор CR-02:
    содержимое способно исполниться. Здесь на входе безупречные картинки, а
    причина другая: WebP Telethon соберёт стикером, а не фотографией, и для
    WhatsApp ``image/webp`` — тоже mimetype стикера; GIF не является ни годной
    статической картинкой для WhatsApp, ни фотографией для Telegram. Слив обеих
    причин в одну параметризацию стёр бы это различие, и пропажа любой из них
    перестала бы быть заметной.
    """
    assert sniff_image(make_bytes()) is None


def test_supported_formats_and_refusal_text_stay_in_step():
    """Таблица сигнатур и текст отказа называют одно и то же множество форматов.

    Ловит расхождение, которое иначе тихо доживает до пользователя: формат
    вернули в таблицу (или убрали из неё), а строку, которую человек читает,
    поправить забыли. Утверждение идёт на множество ТИПОВ, а не на число
    записей: одному формату может отвечать несколько сигнатур, и счёт записей
    измерял бы устройство таблицы вместо набора форматов.
    """
    assert {mime for _, mime in _IMAGE_SIGNATURES} == {"image/jpeg", "image/png"}
    assert "JPEG" in UNSUPPORTED_IMAGE_MESSAGE
    assert "PNG" in UNSUPPORTED_IMAGE_MESSAGE
    assert "WebP" not in UNSUPPORTED_IMAGE_MESSAGE
    assert "GIF" not in UNSUPPORTED_IMAGE_MESSAGE


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_bytes,expected",
    [
        # ⚠️ Для PNG БЕЗ настоящей альфы ожидание стало ``image/jpeg``, и это
        # СЛЕДСТВИЕ ПРАВИЛА ФОРМАТА (D-4), а не послабление приёма: файл принят
        # именно как PNG — распознавание по содержимому не тронуто, — но в
        # хранилище кладётся то, что из него произведено. PNG с настоящей альфой
        # рядом доказывает, что правило избирательно, а не «всё в JPEG».
        (make_real_png_bytes, "image/jpeg"),
        (make_real_png_with_alpha_bytes, "image/png"),
        (lambda: make_real_jpeg_bytes((600, 400)), "image/jpeg"),
    ],
    ids=["png-opaque", "png-alpha", "jpeg"],
)
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_accepts_each_supported_format(
    mock_s3, make_bytes, expected, upload_client, upload_auth_headers
):
    """Оба поддерживаемых формата принимаются по содержимому.

    ⚠️ Параметризация переведена на НАСТОЯЩИЕ изображения (issue #40): прежняя
    шла через ``make_jpeg_bytes``, который декодироваться не может вовсе, и
    после этой задачи меряла бы отказ вместо приёма.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        # Заголовок типа заведомо неверный: приём должен опираться на содержимое.
        files={"file": ("payload.bin", make_bytes(), "application/octet-stream")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    # Оба объекта уходят с одним типом: правило формата у них общее (P-6).
    assert [call.kwargs["content_type"] for call in mock_s3.call_args_list] == [
        expected,
        expected,
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make_bytes",
    [
        lambda: make_gif_bytes(b"87a"),
        lambda: make_gif_bytes(b"89a"),
        make_webp_bytes,
    ],
    ids=["gif87a", "gif89a", "webp"],
)
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_rejects_formats_no_messenger_can_send(
    mock_s3, make_bytes, upload_client, upload_auth_headers
):
    """Issue #39: отказ наступает на ЗАГРУЗКЕ и до обращения к хранилищу.

    Заголовок типа заведомо неверный: отказ, как и приём, опирается на
    содержимое, а не на слово клиента. ``assert_not_called`` обязателен — один
    лишь код 400 доказывает мало, его возвращает и превышение размера; смысл
    правки в том, что такой файл в хранилище не попадает вовсе.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("payload.bin", make_bytes(), "application/octet-stream")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == UNSUPPORTED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


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

    ⚠️ Ожидаемое значение сдвинулось с ``image/png`` на ``image/jpeg`` из-за
    ПРАВИЛА ФОРМАТА (D-4), а НЕ из-за ослабления CR-02. Проверяемое свойство
    даже усилилось: прежде тип брался от РАСПОЗНАННОГО содержимого, теперь — от
    ФАКТИЧЕСКИ СОХРАНЁННЫХ байтов, которые произведены самим приложением. Это
    строго у́же прежнего: подконтрольного отправителю значения на этом пути не
    остаётся ни на одном шаге. Заголовок ``image/svg+xml`` в запросе — прежний,
    и он по-прежнему не влияет ни на что.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("real.png", make_real_png_bytes(), "image/svg+xml")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert mock_s3.call_args_list[0].kwargs["content_type"] == "image/jpeg"
    assert "svg" not in mock_s3.call_args_list[0].kwargs["content_type"]


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


# --- Issue #40: сжатие на входе и миниатюра для интерфейса ---------------------
#
# Одна загрузка перестала быть одним объектом. Проверяется поэтому не «ответ
# 200», а СОСТАВ обращений к хранилищу: что объектов ровно два, что первый —
# пережатая версия под возвращённым ключом, что второй — миниатюра под ключом с
# приставкой, и что присланных байтов нет ни в одном из них.


# --- P-5: расширение ключа описывает те байты, что под ним лежат ---------------


def test_retarget_extension_replaces_a_known_extension():
    assert retarget_extension("photo.png", ".jpg") == "photo.jpg"
    assert retarget_extension("photo.jpeg", ".jpg") == "photo.jpg"
    assert retarget_extension("photo.jpg", ".png") == "photo.png"


def test_retarget_extension_ignores_case_of_the_source_extension():
    """``.PNG`` и ``.png`` — одно и то же расширение.

    Сравнение с учётом регистра оставило бы ключ вида ``photo.PNG.jpg``: имя
    файла приходит от клиента, и регистр в нём подконтролен ему же.
    """
    assert retarget_extension("photo.PNG", ".jpg") == "photo.jpg"
    assert retarget_extension("photo.JPEG", ".jpg") == "photo.jpg"


def test_retarget_extension_appends_when_there_is_nothing_to_replace():
    assert retarget_extension("photo", ".jpg") == "photo.jpg"
    assert retarget_extension("archive.tar", ".png") == "archive.tar.png"


def test_retarget_extension_keeps_the_key_form_intact():
    """Результат остаётся в наборе образца ключа и в пределе длины (T-Q40-03).

    Усечение идёт по ОСНОВЕ имени, а не по готовой строке: обрезка после
    приписывания срезала бы само расширение, ключ перестал бы описывать свои
    байты, и Telethon собрал бы медиа не того типа — та же поломка, что в
    issue #39.
    """
    long_name = safe_filename("a" * 300 + ".png")
    result = retarget_extension(long_name, ".jpg")

    assert len(result) <= MAX_FILENAME_LENGTH
    assert result.endswith(".jpg")
    assert SAFE_FILENAME_CHARS.match(result), result


def test_retarget_extension_falls_back_on_a_bare_extension():
    """Имя, состоящее из одного расширения, не оставляет пустой основы.

    Пустая основа дала бы ключ, оканчивающийся на подчёркивание с расширением
    сразу за ним, — форма, которой маршрут загрузки никогда не порождал.
    """
    assert retarget_extension(".png", ".jpg") == f"{FALLBACK_FILENAME}.jpg"


# --- D-1, D-2: один файл — два объекта, оригинала среди них нет ----------------


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_stores_exactly_the_delivery_image_and_its_thumbnail(
    mock_s3, upload_client, upload_auth_headers
):
    """Ровно два объекта: сжатая версия под ключом и миниатюра под приставкой."""
    payload = make_real_jpeg_bytes((4000, 3000))

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.jpg", payload, "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    key = response.json()["path"]

    assert mock_s3.call_count == 2
    delivery, thumbnail = mock_s3.call_args_list
    assert delivery.kwargs["key"] == key
    assert thumbnail.kwargs["key"] == thumb_key(key)
    assert _decode(thumbnail.kwargs["content"]).size[0] <= DELIVERY_MAX_EDGE


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_stored_image_is_reduced_to_the_delivery_limit(
    mock_s3, upload_client, upload_auth_headers
):
    """Снимок 4000x3000 доезжает до бакета с длинной стороной 1920 (D-3)."""
    payload = make_real_jpeg_bytes((4000, 3000))

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.jpg", payload, "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    stored = mock_s3.call_args_list[0].kwargs["content"]
    assert _decode(stored).size == (DELIVERY_MAX_EDGE, 1440)


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_original_bytes_reach_no_object_at_all(
    mock_s3, upload_client, upload_auth_headers
):
    """Оригинал не хранится ни под каким ключом (D-2).

    Утверждение идёт по ОБОИМ вызовам: «первый не равен присланному» оставило бы
    возможность положить оригинал вторым объектом «на всякий случай», а решение
    владельца это запрещает прямо.
    """
    payload = make_real_jpeg_bytes((4000, 3000))

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.jpg", payload, "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    stored = [call.kwargs["content"] for call in mock_s3.call_args_list]
    assert payload not in stored
    assert all(len(content) < len(payload) for content in stored)


# --- Границы задачи: форма ключа и запрет на производный ключ ------------------


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_returned_key_still_passes_the_ownership_check(
    mock_s3, upload_client, upload_auth_headers
):
    """Ключ после смены формата всё ещё проходит ``own_image_keys`` (T-Q40-03).

    Это и есть цена, которую задача обязана НЕ заплатить: приведи она расширение
    неаккуратно, эндпоинт возвращал бы ключ, который сохранение объявления
    отвергает, — загрузка «удалась», а прикрепить результат нельзя.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.png", make_real_png_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    key = response.json()["path"]
    user_id = int(key.split("/", 1)[0])

    assert own_image_keys([key], user_id, 10) == [key]


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_the_thumbnail_key_is_refused_by_the_ownership_check(
    mock_s3, upload_client, upload_auth_headers
):
    """T-Q40-04: миниатюру нельзя прикрепить к объявлению как вложение.

    Ключ берётся из ФАКТИЧЕСКОГО второго обращения к хранилищу, а не строится в
    теле теста: иначе проверялось бы правило, а не то, что маршрут ему следует.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.png", make_real_png_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    key = response.json()["path"]
    user_id = int(key.split("/", 1)[0])
    thumbnail_key = mock_s3.call_args_list[1].kwargs["key"]

    with pytest.raises(HTTPException) as exc_info:
        own_image_keys([thumbnail_key], user_id, 10)
    assert exc_info.value.status_code == 400


# --- D-4 и P-5 на HTTP-пути ----------------------------------------------------


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_png_without_alpha_is_stored_as_jpeg_with_a_jpg_key(
    mock_s3, upload_client, upload_auth_headers
):
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.png", make_real_png_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["path"].endswith(".jpg")
    assert _decode(mock_s3.call_args_list[0].kwargs["content"]).format == "JPEG"


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_png_with_alpha_is_stored_as_png(
    mock_s3, upload_client, upload_auth_headers
):
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("logo.png", make_real_png_with_alpha_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["path"].endswith(".png")
    assert _decode(mock_s3.call_args_list[0].kwargs["content"]).format == "PNG"


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_jpeg_key_extension_is_normalised(
    mock_s3, upload_client, upload_auth_headers
):
    """``photo.jpeg`` даёт ключ на ``.jpg`` — приведение БЕЗУСЛОВНО (P-5).

    Формат при этом не менялся: инвариант «расширение ключа описывает байты» не
    делает исключения для случая, когда байты остались прежнего формата, иначе
    форм ключа стало бы две.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.jpeg", make_real_jpeg_bytes((600, 400)), "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["path"].endswith(".jpg")


# --- T-Q40-01: отказ по потолку числа точек -----------------------------------


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_rejects_a_decompression_bomb_before_touching_storage(
    mock_s3, upload_client, upload_auth_headers
):
    """Крошечный файл с огромными заявленными размерами отвергается 400.

    ``assert_not_called`` обязателен: один лишь код 400 доказывает мало — его
    возвращает и превышение размера тела, — а смысл потолка в том, что такой
    файл не декодируется и в хранилище не попадает вовсе.
    """
    payload = make_declared_huge_png_bytes(8000, 8000)
    assert 8000 * 8000 > MAX_DECODED_PIXELS
    assert len(payload) < 1024, "тело перестало быть крошечным — это уже не бомба"

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("bomb.png", payload, "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == OVERSIZED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


def test_the_pixel_ceiling_message_does_not_talk_about_formats():
    """Отказ по числу точек называет СВОЮ причину (P-9).

    Файл корректен, и совет «выберите другой формат» был бы советом мимо
    причины — ровно тот класс неправды, из-за которого в шапке ``uploads.py``
    написан абзац про WebP.
    """
    assert OVERSIZED_IMAGE_MESSAGE != UNSUPPORTED_IMAGE_MESSAGE
    assert "JPEG" not in OVERSIZED_IMAGE_MESSAGE
    assert "PNG" not in OVERSIZED_IMAGE_MESSAGE
    assert "разрешение" in OVERSIZED_IMAGE_MESSAGE


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_upload_rejects_signature_without_a_decodable_image(
    mock_s3, upload_client, upload_auth_headers
):
    """Сигнатура верна, картинки нет — отказ 400 и пустое хранилище.

    Вход — ``make_jpeg_bytes()``, тот самый построитель, которым до issue #40
    доказывался ПРИЁМ. Класс входа никуда не делся, изменился ответ на него:
    распознавание по первым байтам такой файл пропускает, а декодер — нет.
    """
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.jpg", make_jpeg_bytes(), "image/jpeg")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == UNSUPPORTED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


# --- P-7: провал миниатюры запрос не проваливает -------------------------------


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_thumbnail_failure_leaves_the_upload_successful(
    mock_s3, upload_client, upload_auth_headers
):
    """Не сохранилась миниатюра — загрузка всё равно удалась (P-7).

    Миниатюра нужна для СКОРОСТИ показа, а не для отправки. Обратное решение
    стоило бы пользователю потерянной загрузки из-за объекта, без которого
    интерфейс и так обязан работать: механизм отката на полноразмерный адрес
    существует ради ключей, загруженных до этой задачи (D-6), и этот случай он
    закрывает бесплатно.
    """
    mock_s3.side_effect = [None, RuntimeError("bucket refused the thumbnail")]

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.png", make_real_png_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["path"]
    assert mock_s3.call_count == 2


@pytest.mark.asyncio
@patch("app.routes.uploads.upload_file_to_s3", new_callable=AsyncMock)
async def test_delivery_failure_still_answers_bad_gateway(
    mock_s3, upload_client, upload_auth_headers
):
    """Провал сжатой версии — по-прежнему 502, и миниатюра не пишется.

    Парный к предыдущему: без него послабление для миниатюры со временем
    расползлось бы на оба объекта, и пользователь получал бы 200 на загрузку,
    которой в хранилище нет.
    """
    mock_s3.side_effect = RuntimeError("bucket is down")

    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("photo.png", make_real_png_bytes(), "image/png")},
        headers=upload_auth_headers,
    )

    assert response.status_code == 502
    assert mock_s3.call_count == 1
