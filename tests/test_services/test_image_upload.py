"""Не-транспортная половина загрузки: распознавание, нормализация, запись объекта.

Утверждения переехали сюда из суиты снятого JSON-входа загрузки (Фаза 12, план
12-05, G-8). Переезд — не переписывание: каждое утверждение сохранило СВОЙ
предмет, своё имя и своё адресное сообщение; изменился только вход, через который
оно подано. Прежде предметом был HTTP-запрос к исчезнувшему адресу, теперь —
`store_upload` и три чистые функции рядом с ним. Утверждения О МАРШРУТЕ (коды,
фрагмент, владение ключом) уехали в `tests/test_pages/test_ads_image_upload.py`.

Форма модуля взята у соседа по каталогу `test_image_keys.py`: чистые утверждения,
без клиентских фикстур, ожидания на ИМПОРТИРОВАННЫХ именах сервиса. Тест на
литерале сравнивал бы модуль сам с собой и зеленел бы ровно тогда, когда человек
получал бы не тот текст, что здесь написан.

⚠️ ЗАПИСЬ ОБЪЕКТА ПОДМЕНЯЕТСЯ ПО АДРЕСУ `app.services.image_upload.upload_file_to_s3`.
Цель патча привязана к ИМЕНИ МОДУЛЯ, и промах даёт `AttributeError`, а не
осмысленный отказ (G-8) — переезд имени обязан ронять этот файл вслух.
"""

import io
import re

import pytest
from fastapi import HTTPException
from fastapi import UploadFile as FastAPIUploadFile
from PIL import Image
from starlette.datastructures import UploadFile as StarletteUploadFile
from unittest.mock import AsyncMock, patch

from app.config import Settings
from app.services.image_keys import own_image_keys, thumb_key
from app.services.images import DELIVERY_MAX_EDGE, MAX_DECODED_PIXELS
from app.services.image_upload import (
    _IMAGE_SIGNATURES,
    Accepted,
    FALLBACK_FILENAME,
    MAX_FILENAME_LENGTH,
    OVERSIZED_IMAGE_MESSAGE,
    UNSUPPORTED_IMAGE_MESSAGE,
    UPLOAD_CHUNK_SIZE,
    Rejected,
    retarget_extension,
    safe_filename,
    sniff_image,
    store_upload,
)

# Владелец, под чьим идентификатором строится ключ объекта. Значение любое
# положительное: сервис его не проверяет — проверку владения делает
# `own_image_keys` при сохранении объявления, — но первым звеном ключа он идёт, и
# утверждения о форме ключа его читают.
OWNER_ID = 7


@pytest.fixture
def upload_settings() -> Settings:
    """Настройки с заполненными параметрами хранилища.

    Тот же набор, что получал снятый вход: сервис передаёт эти значения в запись
    объекта, и утверждения о бакете их читают. `_env_file=None` обязателен —
    иначе фикстура наследует боевые S3-параметры рабочего каталога.
    """
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


def an_upload(
    content: bytes,
    filename: str | None = "photo.png",
    cls: type[StarletteUploadFile] = StarletteUploadFile,
) -> StarletteUploadFile:
    """Файловая часть составного запроса ровно того рода, что приходит сервису.

    Класс параметрический намеренно: в сервис приезжает то, что собрал разбор
    составного запроса, и разбор этот отдаёт БАЗОВЫЙ класс, тогда как объявление
    обработчика типизировано подклассом FastAPI. Утверждение об объёме чтения
    ниже меряет оба, а не предполагает один — см. его докстринг.
    """
    return cls(file=io.BytesIO(content), filename=filename, size=len(content))


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
    там читаются первые три байта, — но с issue #40 приём изображение ещё и
    открывает, поэтому такой вход означает отказ, а не приём. Построитель
    сохранён и получил СВОЙ тест
    (``test_store_upload_rejects_signature_without_a_decodable_image``):
    «сигнатура верна, картинки нет» — отдельный класс входа, и терять его нельзя.
    """
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00" + b"\x00" * 16


# --- issue #40: НАСТОЯЩИЕ изображения для пути приёма -------------------------
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
# хранилища. Функция проверяется напрямую: у неё определённые вход и выход, и
# классы входов проверяются каждый отдельно.

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
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_key_stays_inside_user_prefix(mock_s3, upload_settings):
    """Ключ объекта не выходит за префикс пользователя ни при каком имени файла."""
    hostile = '../../evil x" onerror="alert(1)>.png'

    result = await store_upload(
        an_upload(make_real_png_bytes(), hostile),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    key = result.key
    assert re.fullmatch(r"\d+/[0-9a-f]{32}_[A-Za-z0-9._-]+", key), key
    # Ключ, ушедший в хранилище, — тот же самый, что вернул сервис.
    #
    # ⚠️ Утверждение снимается с ПЕРВОГО вызова, а не с последнего (issue #40).
    # `call_args` — это последний вызов, а последним теперь идёт МИНИАТЮРА, и её
    # ключ по построению начинается с приставки, то есть заведомо не равен
    # возвращённому. Прежняя запись после этой задачи меряла бы не то, что
    # утверждает.
    assert mock_s3.call_args_list[0].kwargs["key"] == key


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_accepts_a_valid_image(mock_s3, upload_settings):
    """Приём картинки: два объекта в хранилище, и ни один не равен присланному.

    ⚠️ ДВА ПРЕЖНИХ УТВЕРЖДЕНИЯ ОТМЕНЕНЫ СОЗНАТЕЛЬНО (issue #40), и заменены, а
    не выброшены:

    * ``call_kwargs["content"] == png_bytes`` утверждало БАЙТОВОЕ РАВЕНСТВО
      сохранённого присланному. Ровно это правило и отменила задача: оригинал не
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

    result = await store_upload(
        an_upload(png_bytes, "test_image.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    assert "test_image" in result.key

    assert mock_s3.call_count == 2, "сохранены не оба объекта: сжатая версия и миниатюра"
    call_kwargs = mock_s3.call_args_list[0].kwargs
    assert call_kwargs["content"] != png_bytes, "в хранилище ушли исходные байты"
    assert _decode(call_kwargs["content"]).size == (600, 400)
    assert call_kwargs["content_type"] == "image/jpeg"
    assert call_kwargs["bucket"] == "test-bucket"


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_a_plain_text_file(mock_s3, upload_settings):
    """Текстовый файл отвергается, и в хранилище не уходит ничего."""
    result = await store_upload(
        an_upload(b"hello world", "document.txt"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    assert result.reason == UNSUPPORTED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


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
# таблицей сигнатур самого сервиса приёма загрузки.


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
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_accepts_each_supported_format(
    mock_s3, make_bytes, expected, upload_settings
):
    """Оба поддерживаемых формата принимаются по содержимому.

    ⚠️ Параметризация переведена на НАСТОЯЩИЕ изображения (issue #40): прежняя
    шла через ``make_jpeg_bytes``, который декодироваться не может вовсе, и
    после той задачи меряла бы отказ вместо приёма.

    Имя части заведомо не описывает содержимого — приём должен опираться на
    первые байты, а не на клиентское имя и не на присланный заголовок типа.
    """
    result = await store_upload(
        an_upload(make_bytes(), "payload.bin"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
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
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_formats_no_messenger_can_send(
    mock_s3, make_bytes, upload_settings
):
    """Issue #39: отказ наступает на ПРИЁМЕ и до обращения к хранилищу.

    ``assert_not_called`` обязателен — одна лишь форма отказа доказывает мало,
    её возвращает и превышение размера; смысл правки в том, что такой файл в
    хранилище не попадает вовсе.
    """
    result = await store_upload(
        an_upload(make_bytes(), "payload.bin"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    assert result.reason == UNSUPPORTED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_svg_whatever_the_name_claims(
    mock_s3, upload_settings
):
    """CR-02: SVG под именем PNG отклоняется и в хранилище не уходит."""
    result = await store_upload(
        an_upload(SVG_BYTES, "logo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    assert "JPEG" in result.reason
    mock_s3.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_non_image_under_an_image_name(
    mock_s3, upload_settings
):
    """Произвольные байты не проходят ни под каким именем файла."""
    result = await store_upload(
        an_upload(b"not an image at all", "payload.jpg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    mock_s3.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_stores_the_sniffed_content_type(mock_s3, upload_settings):
    """В хранилище уходит распознанный тип, а не заявленный именем файла.

    Иначе объект лёг бы в S3 с подконтрольным отправителю ``Content-Type`` и
    отдавался бы браузеру с ним же — вектор CR-02 сохранился бы на выдаче.

    ⚠️ Ожидаемое значение сдвинулось с ``image/png`` на ``image/jpeg`` из-за
    ПРАВИЛА ФОРМАТА (D-4), а НЕ из-за ослабления CR-02. Проверяемое свойство
    даже усилилось: прежде тип брался от РАСПОЗНАННОГО содержимого, теперь — от
    ФАКТИЧЕСКИ СОХРАНЁННЫХ байтов, которые произведены самим приложением. Это
    строго у́же прежнего: подконтрольного отправителю значения на этом пути не
    остаётся ни на одном шаге.
    """
    result = await store_upload(
        an_upload(make_real_png_bytes(), "real.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
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
# Утверждать одну лишь форму отказа на превышении бесполезно — её возвращает и
# дефектный код. Измеряется поэтому ОБЪЁМ ЧТЕНИЯ.


@pytest.fixture
def oversize_settings(upload_settings) -> Settings:
    """Настройки загрузки с пределом размера 1 МБ.

    Дефолтные 5 МБ заставили бы держать в тесте лишние мегабайты; предел берётся
    из настроек, а не из литерала, поэтому понизить его достаточно здесь.
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
    """Обёртка чтения накладывается на ТОТ класс, что приходит в сервис.

    `fastapi.UploadFile` в установленной версии — НЕ тот же класс, а подкласс
    `starlette.datastructures.UploadFile`, и он переопределяет ``read``,
    передавая размер в базовый метод ЯВНО. Приди в сервис экземпляр подкласса,
    вызов ``await file.read()`` без аргумента дошёл бы до обёртки уже с
    ``size=-1``, и утверждение «сервис не читал без ограничения размера»
    перестало бы что-либо измерять, оставшись зелёным при полностью
    забуференном теле.

    Поэтому обёртка кладётся на БАЗОВЫЙ класс — его метод в конечном счёте
    вызывают оба, — а то, что оба класса меряются, обеспечено параметризацией
    ``test_oversized_body_is_not_buffered_whole``.
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
@pytest.mark.parametrize(
    "upload_class",
    [StarletteUploadFile, FastAPIUploadFile],
    ids=["starlette-base", "fastapi-subclass"],
)
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_oversized_body_is_not_buffered_whole(
    mock_s3, upload_class, oversize_settings, recorded_reads
):
    """Превышение предела ПРЕРЫВАЕТ чтение, а не проверяется после него.

    ⚠️ ОБА КЛАССА МЕРЯЮТСЯ, А НЕ ОДИН, И ЭТО НЕ ИЗЛИШЕСТВО. Разбор составного
    запроса отдаёт БАЗОВЫЙ класс, а объявление обработчика типизировано
    подклассом FastAPI, который передаёт размер в базовый метод явно. Мерь тест
    только базовый — и «аргумента не было» осталось бы различимым, но лишь для
    того класса, который в сервис приезжает СЕГОДНЯ; мерь только подкласс — и
    различать стало бы нечего вовсе (см. докстринг
    ``test_read_measurement_targets_the_class_the_handler_receives``).
    """
    max_bytes = oversize_settings.max_image_size_mb * 1024 * 1024
    body = make_oversized_png_bytes(3 * 1024 * 1024)

    result = await store_upload(
        an_upload(body, "big.png", cls=upload_class),
        user_id=OWNER_ID,
        settings=oversize_settings,
    )

    assert isinstance(result, Rejected), result
    assert "File size exceeds" in result.reason
    mock_s3.assert_not_called()

    assert recorded_reads, "сервис не прочитал ни байта — измерять нечего"
    requested = [size for size, _, _ in recorded_reads]
    assert None not in requested, (
        "сервис запросил содержимое БЕЗ ограничения размера: всё тело "
        f"оказалось в памяти (запрошенные размеры: {requested})"
    )
    total = sum(length for _, length, _ in recorded_reads)
    # Одна порция сверх предела неизбежна: превышение обнаруживается ровно тем
    # блоком, который его создал. Больше одной означает, что чтение не прервалось.
    assert total <= max_bytes + max(requested), (
        f"прочитано {total} байт при пределе {max_bytes}: чтение не прервалось"
    )
    assert set(requested) == {UPLOAD_CHUNK_SIZE}, (
        f"порции запрошены размерами {sorted(set(requested))} вместо объявленного "
        f"{UPLOAD_CHUNK_SIZE}: размер порции перестал быть тем, что объявлен"
    )


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_oversized_body_is_refused_with_size_message(mock_s3, oversize_settings):
    """Страж формулировки: текст отказа по размеру не меняется.

    Зелен и до правки, и после: он закрепляет ответ, а не воспроизводит дефект.
    Дефект — в объёме чтения, и его меряет тест выше.
    """
    body = make_oversized_png_bytes(3 * 1024 * 1024)

    result = await store_upload(
        an_upload(body, "big.png"),
        user_id=OWNER_ID,
        settings=oversize_settings,
    )

    assert isinstance(result, Rejected), result
    assert result.reason == (
        f"File size exceeds {oversize_settings.max_image_size_mb}MB limit"
    )
    assert result.display_name == "big.png"
    mock_s3.assert_not_called()


# --- Issue #40: сжатие на входе и миниатюра для интерфейса ---------------------
#
# Одна загрузка перестала быть одним объектом. Проверяется поэтому не форма
# результата, а СОСТАВ обращений к хранилищу: что объектов ровно два, что первый —
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
    сразу за ним, — форма, которой приём загрузки никогда не порождал.
    """
    assert retarget_extension(".png", ".jpg") == f"{FALLBACK_FILENAME}.jpg"


# --- D-1, D-2: один файл — два объекта, оригинала среди них нет ----------------


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_stores_exactly_the_delivery_image_and_its_thumbnail(
    mock_s3, upload_settings
):
    """Ровно два объекта: сжатая версия под ключом и миниатюра под приставкой."""
    result = await store_upload(
        an_upload(make_real_jpeg_bytes((4000, 3000)), "photo.jpg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result

    assert mock_s3.call_count == 2
    delivery, thumbnail = mock_s3.call_args_list
    assert delivery.kwargs["key"] == result.key
    assert thumbnail.kwargs["key"] == thumb_key(result.key)
    assert _decode(thumbnail.kwargs["content"]).size[0] <= DELIVERY_MAX_EDGE


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_stored_image_is_reduced_to_the_delivery_limit(mock_s3, upload_settings):
    """Снимок 4000x3000 доезжает до бакета с длинной стороной 1920 (D-3)."""
    result = await store_upload(
        an_upload(make_real_jpeg_bytes((4000, 3000)), "photo.jpg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    stored = mock_s3.call_args_list[0].kwargs["content"]
    assert _decode(stored).size == (DELIVERY_MAX_EDGE, 1440)


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_original_bytes_reach_no_object_at_all(mock_s3, upload_settings):
    """Оригинал не хранится ни под каким ключом (D-2).

    Утверждение идёт по ОБОИМ вызовам: «первый не равен присланному» оставило бы
    возможность положить оригинал вторым объектом «на всякий случай», а решение
    владельца это запрещает прямо.
    """
    payload = make_real_jpeg_bytes((4000, 3000))

    result = await store_upload(
        an_upload(payload, "photo.jpg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    stored = [call.kwargs["content"] for call in mock_s3.call_args_list]
    assert payload not in stored
    assert all(len(content) < len(payload) for content in stored)


# --- Границы задачи: форма ключа и запрет на производный ключ ------------------


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_returned_key_still_passes_the_ownership_check(mock_s3, upload_settings):
    """Ключ после смены формата всё ещё проходит ``own_image_keys`` (T-Q40-03).

    Это и есть цена, которую задача обязана НЕ заплатить: приведи она расширение
    неаккуратно, приём возвращал бы ключ, который сохранение объявления
    отвергает, — загрузка «удалась», а прикрепить результат нельзя.
    """
    result = await store_upload(
        an_upload(make_real_png_bytes(), "photo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    user_id = int(result.key.split("/", 1)[0])

    assert own_image_keys([result.key], user_id, 10) == [result.key]


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_the_thumbnail_key_is_refused_by_the_ownership_check(
    mock_s3, upload_settings
):
    """T-Q40-04: миниатюру нельзя прикрепить к объявлению как вложение.

    Ключ берётся из ФАКТИЧЕСКОГО второго обращения к хранилищу, а не строится в
    теле теста: иначе проверялось бы правило, а не то, что приём ему следует.
    """
    result = await store_upload(
        an_upload(make_real_png_bytes(), "photo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    user_id = int(result.key.split("/", 1)[0])
    thumbnail_key = mock_s3.call_args_list[1].kwargs["key"]

    with pytest.raises(HTTPException) as exc_info:
        own_image_keys([thumbnail_key], user_id, 10)
    assert exc_info.value.status_code == 400


# --- D-4 и P-5 на пути приёма --------------------------------------------------


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_png_without_alpha_is_stored_as_jpeg_with_a_jpg_key(
    mock_s3, upload_settings
):
    result = await store_upload(
        an_upload(make_real_png_bytes(), "photo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    assert result.key.endswith(".jpg")
    assert _decode(mock_s3.call_args_list[0].kwargs["content"]).format == "JPEG"


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_png_with_alpha_is_stored_as_png(mock_s3, upload_settings):
    result = await store_upload(
        an_upload(make_real_png_with_alpha_bytes(), "logo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    assert result.key.endswith(".png")
    assert _decode(mock_s3.call_args_list[0].kwargs["content"]).format == "PNG"


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_jpeg_key_extension_is_normalised(mock_s3, upload_settings):
    """``photo.jpeg`` даёт ключ на ``.jpg`` — приведение БЕЗУСЛОВНО (P-5).

    Формат при этом не менялся: инвариант «расширение ключа описывает байты» не
    делает исключения для случая, когда байты остались прежнего формата, иначе
    форм ключа стало бы две.
    """
    result = await store_upload(
        an_upload(make_real_jpeg_bytes((600, 400)), "photo.jpeg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    assert result.key.endswith(".jpg")


# --- T-Q40-01: отказ по потолку числа точек -----------------------------------


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_a_decompression_bomb_before_touching_storage(
    mock_s3, upload_settings
):
    """Крошечный файл с огромными заявленными размерами отвергается.

    ``assert_not_called`` обязателен: одна лишь форма отказа доказывает мало —
    её возвращает и превышение размера тела, — а смысл потолка в том, что такой
    файл не декодируется и в хранилище не попадает вовсе.
    """
    payload = make_declared_huge_png_bytes(8000, 8000)
    assert 8000 * 8000 > MAX_DECODED_PIXELS
    assert len(payload) < 1024, "тело перестало быть крошечным — это уже не бомба"

    result = await store_upload(
        an_upload(payload, "bomb.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    assert result.reason == OVERSIZED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


def test_the_pixel_ceiling_message_does_not_talk_about_formats():
    """Отказ по числу точек называет СВОЮ причину (P-9).

    Файл корректен, и совет «выберите другой формат» был бы советом мимо
    причины — ровно тот класс неправды, из-за которого в шапке сервиса приёма
    написан абзац про WebP.
    """
    assert OVERSIZED_IMAGE_MESSAGE != UNSUPPORTED_IMAGE_MESSAGE
    assert "JPEG" not in OVERSIZED_IMAGE_MESSAGE
    assert "PNG" not in OVERSIZED_IMAGE_MESSAGE
    assert "разрешение" in OVERSIZED_IMAGE_MESSAGE


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_store_upload_rejects_signature_without_a_decodable_image(
    mock_s3, upload_settings
):
    """Сигнатура верна, картинки нет — отказ и пустое хранилище.

    Вход — ``make_jpeg_bytes()``, тот самый построитель, которым до issue #40
    доказывался ПРИЁМ. Класс входа никуда не делся, изменился ответ на него:
    распознавание по первым байтам такой файл пропускает, а декодер — нет.
    """
    result = await store_upload(
        an_upload(make_jpeg_bytes(), "photo.jpg"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Rejected), result
    assert result.reason == UNSUPPORTED_IMAGE_MESSAGE
    mock_s3.assert_not_called()


# --- P-7: провал миниатюры приём не проваливает --------------------------------


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_thumbnail_failure_leaves_the_upload_accepted(mock_s3, upload_settings):
    """Не сохранилась миниатюра — загрузка всё равно удалась (P-7).

    Миниатюра нужна для СКОРОСТИ показа, а не для отправки. Обратное решение
    стоило бы пользователю потерянной загрузки из-за объекта, без которого
    интерфейс и так обязан работать: механизм отката на полноразмерный адрес
    существует ради ключей, загруженных до этой задачи (D-6), и этот случай он
    закрывает бесплатно.
    """
    mock_s3.side_effect = [None, RuntimeError("bucket refused the thumbnail")]

    result = await store_upload(
        an_upload(make_real_png_bytes(), "photo.png"),
        user_id=OWNER_ID,
        settings=upload_settings,
    )

    assert isinstance(result, Accepted), result
    assert result.key
    assert mock_s3.call_count == 2


@pytest.mark.asyncio
@patch("app.services.image_upload.upload_file_to_s3", new_callable=AsyncMock)
async def test_delivery_failure_raises_bad_gateway(mock_s3, upload_settings):
    """Провал сжатой версии — исключение 502, и миниатюра не пишется.

    Парный к предыдущему: без него послабление для миниатюры со временем
    расползлось бы на оба объекта, и пользователь получал бы удачную загрузку,
    которой в хранилище нет.

    ⚠️ ФОРМА ЗДЕСЬ ИСКЛЮЧЕНИЕ, А НЕ ``Rejected``, И ЭТО РЕШЕНИЕ СЕРВИСА: провал
    записи есть отказ ИНФРАСТРУКТУРЫ, а не отказ файлу, и строка «ваш файл не
    подошёл» сказала бы человеку неправду. Что видит на этом человек по HTTP —
    предмет утверждения в суите маршрута.
    """
    mock_s3.side_effect = RuntimeError("bucket is down")

    with pytest.raises(HTTPException) as exc_info:
        await store_upload(
            an_upload(make_real_png_bytes(), "photo.png"),
            user_id=OWNER_ID,
            settings=upload_settings,
        )

    assert exc_info.value.status_code == 502
    assert mock_s3.call_count == 1
