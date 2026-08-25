"""Скрипт обслуживания вложений, загруженных до issue #40.

Проверяется ЯДРО скрипта, а не боевой прогон: хранилище подменяется двойником в
памяти, база — фикстурой ``db_session``. Двойник ведёт три журнала — диапазонные
чтения, полные чтения и записи, — и именно журналы, а не счётчики отчёта, служат
доказательством там, где предмет проверки есть ДЕЙСТВИЕ: «сухой прогон ничего не
пишет» и «пропущенный объект не выкачивается» на счётчиках недоказуемы, потому
что счётчик совпал бы и при записи, и при выкачивании.

Картинки строятся Pillow'ом НАСТОЯЩИМИ байтами: скрипт их декодирует, уменьшает
и кодирует обратно, и на имитации сигнатуры не работал бы ни один тест.
"""

import io
import struct
import sys
import zlib
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import recompress_attachments as script  # noqa: E402

from app.models.ad import Ad  # noqa: E402
from app.services.image_keys import thumb_key  # noqa: E402
from app.services.images import DELIVERY_MAX_EDGE, THUMB_MAX_EDGE  # noqa: E402
from app.services.s3 import ObjectHead  # noqa: E402


# --- строительство входных байтов ---------------------------------------------
#
# Плитка та же, что в `tests/test_services/test_images.py`, и по той же причине:
# поэлементный обход 3000x2000 на чистом Python стоил бы десятки секунд каждому
# прогону суиты ради единственного нужного свойства — чтобы данные не сжимались
# в ноль.

_TILE_EDGE = 64


def _gradient(size: tuple[int, int], mode: str = "RGB") -> Image.Image:
    width, height = size
    tile_size = (min(width, _TILE_EDGE), min(height, _TILE_EDGE))
    tile = Image.new(mode, tile_size)
    pixels = tile.load()
    for x in range(tile_size[0]):
        for y in range(tile_size[1]):
            value = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
            pixels[x, y] = value if mode == "RGB" else (*value, 255)

    if tile_size == size:
        return tile

    image = Image.new(mode, size)
    for left in range(0, width, tile_size[0]):
        for top in range(0, height, tile_size[1]):
            image.paste(tile, (left, top))
    return image


def _encode(image: Image.Image, fmt: str, **kwargs) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format=fmt, **kwargs)
    return buffer.getvalue()


def make_jpeg(size: tuple[int, int] = (3000, 2000)) -> bytes:
    return _encode(_gradient(size), "JPEG", quality=95)


def make_png(size: tuple[int, int] = (40, 30)) -> bytes:
    return _encode(_gradient(size), "PNG")


def make_gif(size: tuple[int, int] = (40, 30)) -> bytes:
    return _encode(_gradient(size).convert("P", palette=Image.Palette.ADAPTIVE), "GIF")


def make_declared_huge_png(width: int, height: int) -> bytes:
    """PNG, ЗАЯВЛЯЮЩИЙ огромные размеры при крошечном теле."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        crc = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + payload + crc

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00" * 16))
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + chunk(b"IEND", b"")


def open_bytes(payload: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(payload))
    image.load()
    return image


# --- двойник хранилища --------------------------------------------------------


class FakeStore:
    """Хранилище в памяти, ведущее журналы обращений.

    Журналы и есть предмет утверждений о трафике и о записи. `head_reads` и
    `reads` разделены намеренно: требование «полное тело читается только у тех,
    по кому решена работа» формулируется как «`reads` пуст», и слить их в один
    журнал значило бы потерять само требование.
    """

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}
        self.head_reads: list[tuple[str, int]] = []
        self.reads: list[str] = []
        self.puts: list[tuple[str, bytes, str]] = []
        self.exists_calls: list[str] = []

    def seed(self, key: str, content: bytes, content_type: str = "image/jpeg") -> None:
        self.objects[key] = content
        self.content_types[key] = content_type

    async def head_bytes(self, key: str, size: int) -> ObjectHead | None:
        self.head_reads.append((key, size))
        content = self.objects.get(key)
        if content is None:
            return None
        return ObjectHead(body=content[:size], size=len(content))

    async def read(self, key: str) -> bytes | None:
        self.reads.append(key)
        return self.objects.get(key)

    async def object_exists(self, key: str) -> bool:
        self.exists_calls.append(key)
        return key in self.objects

    async def put(self, key: str, content: bytes, content_type: str) -> None:
        self.puts.append((key, content, content_type))
        self.objects[key] = content
        self.content_types[key] = content_type


KEY = "7/0123456789abcdef0123456789abcdef_photo.jpg"


async def seed_ad(session, images: list[str], user_id: int = 7) -> Ad:
    ad = Ad(user_id=user_id, title="Заголовок", text="Текст", images=images)
    session.add(ad)
    await session.commit()
    await session.refresh(ad)
    return ad


# --- сквозной путь ------------------------------------------------------------


@pytest.mark.asyncio
async def test_an_oversized_attachment_is_rebuilt_under_the_same_key(db_session):
    """Объект сверх предела получает пережатие и миниатюру под ТЕМИ ЖЕ ключами."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])

    await script.recompress_attachments(db_session, store, apply=True)

    assert len(store.puts) == 2, store.puts

    delivery_key, delivery_bytes, delivery_type = store.puts[0]
    assert delivery_key == KEY
    assert max(open_bytes(delivery_bytes).size) == DELIVERY_MAX_EDGE
    assert open_bytes(delivery_bytes).format == "JPEG"
    assert delivery_type == "image/jpeg"

    thumbnail_key, thumbnail_bytes, _ = store.puts[1]
    assert thumbnail_key == thumb_key(KEY)
    assert max(open_bytes(thumbnail_bytes).size) <= THUMB_MAX_EDGE
    assert open_bytes(thumbnail_bytes).format == "JPEG"

    stored = (await db_session.get(Ad, 1)).images
    assert stored == [KEY]


@pytest.mark.asyncio
async def test_a_dry_run_writes_nothing(db_session):
    """Сухой прогон не пишет ничего, но отчёт по нему решение принять позволяет."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=False)

    assert store.puts == []
    assert report.bytes_before > 0
    assert report.bytes_after > 0
    assert report.processed == 1


@pytest.mark.asyncio
async def test_the_thumbnail_is_built_under_the_derived_key(db_session):
    """Ключ миниатюры выводится `thumb_key`, а не сочиняется скриптом."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])

    await script.recompress_attachments(db_session, store, apply=True)

    assert thumb_key(KEY) in store.objects
