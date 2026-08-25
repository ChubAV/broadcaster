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
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import recompress_attachments as script  # noqa: E402

from app.models.ad import Ad  # noqa: E402
from app.services.image_keys import thumb_key  # noqa: E402
from app.services.images import (  # noqa: E402
    DELIVERY_MAX_EDGE,
    THUMB_MAX_EDGE,
    RebuiltImage,
)
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


# --- разбор пропусков: четыре причины, не пять --------------------------------


def test_the_skip_breakdown_has_exactly_four_reasons():
    """Машинная форма решения D-1: пятая причина не появится незамеченной.

    Пятая причина заметки — «сохранённый адрес не разобрался в ключ» — здесь
    беспредметна: ключи берутся только из объявлений, и обратного разбора адреса
    в скрипте нет. Счётчик под неё был бы путём, по которому никто не пройдёт.
    """
    assert len(script.SKIP_REASONS) == 4
    assert len(set(script.SKIP_REASONS)) == 4
    assert set(script.Report().skips) == set(script.SKIP_REASONS)


@pytest.mark.asyncio
async def test_an_image_within_the_delivery_limit_is_not_re_encoded(db_session):
    """Уже маленькое не пережимается, и обе причины пропуска названы.

    Тест держит сразу и первую причину, и второе решение D-3: прогнать через
    кодек снимок, который и так 800 px, значит потерять поколение, не убавив
    веса.
    """
    store = FakeStore()
    original = make_jpeg((800, 600))
    store.seed(KEY, original)
    store.seed(thumb_key(KEY), make_jpeg((400, 300)))
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert store.puts == []
    assert store.objects[KEY] == original
    assert report.skips[script.SKIP_ALREADY_WITHIN_LIMIT] == 1
    assert report.skips[script.SKIP_THUMBNAIL_EXISTS] == 1
    assert report.processed == 0


@pytest.mark.asyncio
async def test_a_thumbnail_is_built_for_an_image_within_the_limit(db_session):
    """Вторая половина доказательства независимости решений."""
    store = FakeStore()
    original = make_jpeg((800, 600))
    store.seed(KEY, original)
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert len(store.puts) == 1
    assert store.puts[0][0] == thumb_key(KEY)
    assert store.objects[KEY] == original
    assert report.skips[script.SKIP_ALREADY_WITHIN_LIMIT] == 1
    assert report.skips[script.SKIP_THUMBNAIL_EXISTS] == 0


@pytest.mark.asyncio
async def test_an_image_over_the_limit_with_a_thumbnail_is_only_re_encoded(db_session):
    """Первая половина доказательства независимости решений."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    store.seed(thumb_key(KEY), make_jpeg((400, 300)))
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert len(store.puts) == 1
    assert store.puts[0][0] == KEY
    assert report.skips[script.SKIP_THUMBNAIL_EXISTS] == 1
    assert report.skips[script.SKIP_ALREADY_WITHIN_LIMIT] == 0


@pytest.mark.asyncio
async def test_an_unsupported_format_survives_the_run_untouched(db_session):
    """Расхождение №3: чужой формат пропускается И называется в отчёте.

    issue #39 сузила приём до JPEG и PNG только 2026-08-25 — всё, что загружено
    раньше, могло быть GIF или WebP. Такое объявление уже сегодня ломает
    отправку в Telegram, и этот прогон может обнаружить дефект первым.
    """
    store = FakeStore()
    gif_key = "7/0123456789abcdef0123456789abcdef_animation.gif"
    original = make_gif((40, 30))
    store.seed(gif_key, original, "image/gif")
    await seed_ad(db_session, [gif_key])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert store.puts == []
    assert store.objects[gif_key] == original
    assert report.skips[script.SKIP_UNSUPPORTED_FORMAT] == 1
    assert gif_key in report.unsupported_examples
    assert gif_key in script.format_report(report)


@pytest.mark.asyncio
async def test_an_image_over_the_pixel_ceiling_is_skipped_without_a_full_read(db_session):
    """Расхождение №4: потолок пикселей действует и на объект из хранилища."""
    store = FakeStore()
    bomb_key = "7/0123456789abcdef0123456789abcdef_bomb.png"
    store.seed(bomb_key, make_declared_huge_png(8000, 5000), "image/png")
    await seed_ad(db_session, [bomb_key])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert report.skips[script.SKIP_OVER_PIXEL_CEILING] == 1
    assert store.puts == []
    assert store.reads == []


@pytest.mark.asyncio
async def test_a_skipped_object_costs_one_ranged_read_and_no_full_read(db_session):
    """Машинная форма требования о трафике (T-QH-06)."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((800, 600)))
    store.seed(thumb_key(KEY), make_jpeg((400, 300)))
    await seed_ad(db_session, [KEY])

    await script.recompress_attachments(db_session, store, apply=False)

    assert len(store.head_reads) == 1
    assert store.head_reads[0][0] == KEY
    assert store.reads == []


@pytest.mark.asyncio
async def test_a_short_header_falls_back_to_one_full_read(db_session, monkeypatch):
    """Короткий заголовок — не повод объявить исправный снимок битым.

    У JPEG маркер размеров стоит ЗА секциями метаданных, и диапазон может его не
    захватить. Без отката отчёт врал бы ровно там, где обязан не врать.
    """
    monkeypatch.setattr(script, "HEAD_READ_BYTES", 8)
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert report.skips[script.SKIP_UNSUPPORTED_FORMAT] == 0
    assert store.reads == [KEY]
    assert report.processed == 1
    assert len(store.puts) == 2


@pytest.mark.asyncio
async def test_a_missing_object_is_reported_as_an_error_not_as_a_skip(db_session):
    """Отсутствие объекта — ошибка с названным ключом, и прогон продолжается."""
    store = FakeStore()
    missing_key = "7/0123456789abcdef0123456789abcdef_gone.jpg"
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [missing_key, KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert all(count == 0 for count in report.skips.values())
    assert len(report.errors) == 1
    assert report.errors[0][0] == missing_key
    assert report.processed == 1


@pytest.mark.asyncio
async def test_a_rebuilt_object_that_grew_is_not_written(db_session, monkeypatch):
    """Пересборка, не уменьшившая объект, в хранилище не кладётся.

    Настоящими пикселями ветка практически недостижима: снимок, уменьшенный до
    1920 и перекодированный, уменьшается почти всегда. Предмет теста —
    СРАВНЕНИЕ ПЕРЕД ЗАПИСЬЮ, а не поведение кодировщика, поэтому кодировщик и
    подменяется двойником: искать реальный вход, который растёт, значило бы
    проверять Pillow, а не скрипт.
    """
    store = FakeStore()
    original = make_jpeg((3000, 2000))
    store.seed(KEY, original)
    await seed_ad(db_session, [KEY])

    inflated = script.rebuild_stored_image(original, resize=True, thumbnail=True)

    def _grown(content, *, resize, thumbnail):
        return RebuiltImage(
            delivery=b"x" * (len(content) + 1) if resize else None,
            thumbnail=inflated.thumbnail if thumbnail else None,
            content_type=inflated.content_type,
        )

    monkeypatch.setattr(script, "rebuild_stored_image", _grown)

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert report.errors == []
    assert [key for key, _, _ in store.puts] == [thumb_key(KEY)]
    assert report.not_shrunk == 1
    assert all(count == 0 for count in report.skips.values())
    assert store.objects[KEY] == original


@pytest.mark.asyncio
async def test_the_report_names_every_required_number(db_session):
    """Отчёт содержит всё, без чего решение о запуске с записью не принять."""
    store = FakeStore()
    gif_key = "7/0123456789abcdef0123456789abcdef_animation.gif"
    store.seed(KEY, make_jpeg((3000, 2000)))
    store.seed(gif_key, make_gif((40, 30)), "image/gif")
    await seed_ad(db_session, [KEY, gif_key])

    report = await script.recompress_attachments(db_session, store, apply=False)
    text = script.format_report(report, apply=False)

    assert "Объём до" in text
    assert "Объём после" in text
    assert "Экономия" in text
    assert "%" in text
    for reason in script.SKIP_REASONS:
        assert reason in text
    assert gif_key in text
    assert "--apply" in text


def test_the_report_survives_an_empty_run():
    """Нулевой объём «до» не приводит к делению на ноль."""
    assert "0.0%" in script.format_report(script.Report())


# --- идемпотентность и прохибиции ---------------------------------------------


@pytest.mark.asyncio
async def test_a_second_apply_run_writes_nothing(db_session):
    """Идемпотентность доказывается НУЛЁМ записей, а не совпадением счётчиков.

    Счётчики совпали бы и при повторной записи тех же байтов — то есть при
    втором пережатии уже пережатого, которое и есть потеря поколения.
    """
    oversized_no_thumb = "7/00000000000000000000000000000001_a.jpg"
    within_no_thumb = "7/00000000000000000000000000000002_b.jpg"
    oversized_with_thumb = "7/00000000000000000000000000000003_c.jpg"

    store = FakeStore()
    store.seed(oversized_no_thumb, make_jpeg((3000, 2000)))
    store.seed(within_no_thumb, make_jpeg((800, 600)))
    store.seed(oversized_with_thumb, make_jpeg((2600, 1800)))
    store.seed(thumb_key(oversized_with_thumb), make_jpeg((400, 300)))

    await seed_ad(db_session, [oversized_no_thumb])
    await seed_ad(db_session, [within_no_thumb])
    await seed_ad(db_session, [oversized_with_thumb])

    first = await script.recompress_attachments(db_session, store, apply=True)
    assert store.puts, "первый прогон обязан что-то записать, иначе тест беспредметен"
    assert first.errors == []

    store.puts.clear()

    second = await script.recompress_attachments(db_session, store, apply=True)

    assert store.puts == []
    assert second.errors == []
    assert second.processed == 0


@pytest.mark.asyncio
async def test_the_run_never_touches_the_database(db_session):
    """Первый критерий закрытия заметки: ключи до и после прогона равны."""
    from app.models.send_log import SendLog

    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])

    db_session.add(
        SendLog(
            user_id=7,
            ad_id=1,
            group_id=1,
            status="ok",
            ad_title="Заголовок",
            ad_images=["https://cdn.example.com/bucket/" + KEY],
        )
    )
    await db_session.commit()

    ads_before = list((await db_session.execute(select(Ad.images))).scalars().all())
    logs_before = list(
        (await db_session.execute(select(SendLog.ad_images))).scalars().all()
    )

    await script.recompress_attachments(db_session, store, apply=True)

    db_session.expire_all()
    ads_after = list((await db_session.execute(select(Ad.images))).scalars().all())
    logs_after = list(
        (await db_session.execute(select(SendLog.ad_images))).scalars().all()
    )

    assert ads_after == ads_before
    assert logs_after == logs_before


@pytest.mark.asyncio
async def test_history_only_keys_are_never_collected(db_session):
    """Машинная форма решения D-1: источник ключей ровно один."""
    from app.models.send_log import SendLog

    history_only = "7/00000000000000000000000000000009_history.jpg"
    await seed_ad(db_session, [KEY])
    db_session.add(
        SendLog(
            user_id=7,
            ad_id=1,
            group_id=1,
            status="ok",
            ad_images=["https://cdn.example.com/bucket/" + history_only],
        )
    )
    await db_session.commit()

    keys = await script.collect_attachment_keys(db_session)

    assert keys == [KEY]


@pytest.mark.asyncio
async def test_the_same_key_in_two_ads_is_processed_once(db_session):
    """Один ключ в двух объявлениях — один объект в хранилище, одна обработка."""
    store = FakeStore()
    store.seed(KEY, make_jpeg((3000, 2000)))
    await seed_ad(db_session, [KEY])
    await seed_ad(db_session, [KEY])

    report = await script.recompress_attachments(db_session, store, apply=True)

    assert report.scanned == 1
    assert report.processed == 1
    assert len(store.puts) == 2


# --- прохибиции, проверяемые по ИСХОДНИКУ -------------------------------------
#
# Запрещённые имена перечислены ЗДЕСЬ, а не комментарием внутри скрипта, и это
# не стилевое предпочтение: прохибиция, названная внутри проверяемого файла,
# сама себя нарушила бы для любой текстовой проверки — файл содержал бы искомую
# строку в объяснении того, что её здесь нет. По той же причине в тексте скрипта
# прохибиции изложены описательной прозой, без имён вызовов хранилища.

_SCRIPT_SOURCE = Path(script.__file__).read_text(encoding="utf-8")

_DESTRUCTIVE_STORAGE_CALLS = (
    "delete_object",
    "delete_objects",
    "delete_bucket",
    "remove_object",
    "abort_multipart_upload",
    ".delete(",
)

_MESSENGER_IMPORTS = (
    "app.messengers",
    "from app.messengers",
    "import app.messengers",
)

_TRANSACTION_CLOSERS = (
    "session.commit",
    ".commit()",
    "session.flush",
    "session.add(",
    "session.delete(",
)


def test_the_script_source_declares_no_destructive_storage_call():
    """«Ничего не удаляет» доказывается ОТСУТСТВИЕМ пути, а не зелёным тестом.

    Тест, который просто не прошёл по удаляющей ветке, доказывал бы лишь то, что
    вход до неё не довёл. Здесь утверждается, что ветки нет вовсе.
    """
    for name in _DESTRUCTIVE_STORAGE_CALLS:
        assert name not in _SCRIPT_SOURCE, name


def test_the_script_source_declares_no_messenger_import():
    for name in _MESSENGER_IMPORTS:
        assert name not in _SCRIPT_SOURCE, name


def test_the_script_never_commits_a_transaction():
    """Сессия используется только на чтение: закрепления транзакции в файле нет."""
    for name in _TRANSACTION_CLOSERS:
        assert name not in _SCRIPT_SOURCE, name
