"""Сжатие загружаемого изображения и его миниатюра — issue #40.

Проверяется ЧИСТАЯ функция, а не HTTP-путь: у ``prepare_upload`` определённые
вход и выход, и каждый класс входов проверяется отдельно. Сквозной путь
эндпоинта закрыт в ``tests/test_routes/test_uploads.py`` — там измеряется, что
объектов в хранилище стало два, а здесь — что именно в них лежит.

Входные картинки строятся Pillow'ом прямо здесь, НАСТОЯЩИМИ байтами. Имитация
сигнатуры (как ``make_jpeg_bytes`` в тестах маршрута) для этого файла не
годится в принципе: она проверяла бы распознавание по первым байтам, а речь
идёт о декодировании, повороте и пережатии — то есть о том, чего у имитации
нет.

⚠️ Декомпрессионная бомба строится РУКАМИ, а не Pillow'ом: её суть — огромные
размеры, ОБЪЯВЛЕННЫЕ в заголовке крошечного файла. Сохранить такую картинку
Pillow'ом означало бы сначала выделить под неё память в самом тесте, то есть
воспроизвести ровно тот отказ, от которого защищается проверяемый код.
"""

import io
import struct
import zlib

import pytest
from PIL import Image

from app.services.images import (
    DELIVERY_MAX_EDGE,
    MAX_DECODED_PIXELS,
    THUMB_MAX_EDGE,
    ImageTooLarge,
    ImageUnreadable,
    prepare_upload,
)


# Сторона плитки, из которой набирается крупная картинка. Поэлементный обход
# 4000x3000 на чистом Python занимает десятки секунд — это цена, которую платил
# бы КАЖДЫЙ прогон суиты ради данных, от которых нужно одно свойство: чтобы они
# не сжимались в ноль. Плитка строится поэлементно один раз, дальше картинка
# набирается вставками, и стоимость перестаёт зависеть от разрешения.
_TILE_EDGE = 64


def _gradient(size: tuple[int, int], mode: str = "RGB") -> Image.Image:
    """Картинка с изменяющимся содержимым, а не заливка одним цветом.

    Заливка сжимается почти в ноль любым кодеком и на любом разрешении,
    поэтому утверждение «миниатюра весит меньше сжатой версии» на ней зеленело
    бы случайно — или падало бы на служебных заголовках, которые у крошечного
    файла весят больше самих данных.
    """
    width, height = size
    tile_size = (min(width, _TILE_EDGE), min(height, _TILE_EDGE))
    tile = Image.new(mode, tile_size)
    pixels = tile.load()
    for x in range(tile_size[0]):
        for y in range(tile_size[1]):
            value = ((x * 7) % 256, (y * 11) % 256, ((x + y) * 13) % 256)
            if mode == "RGB":
                pixels[x, y] = value
            elif mode == "RGBA":
                pixels[x, y] = (*value, 255)
            else:  # pragma: no cover - режимы вне пары в тестах не строятся
                raise AssertionError(mode)

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


def make_jpeg(size: tuple[int, int] = (40, 30), **kwargs) -> bytes:
    return _encode(_gradient(size), "JPEG", **kwargs)


def make_png(size: tuple[int, int] = (40, 30)) -> bytes:
    return _encode(_gradient(size), "PNG")


def make_png_with_alpha(size: tuple[int, int] = (40, 30)) -> bytes:
    """PNG, у которого хотя бы один пиксель непрозрачен НЕ ПОЛНОСТЬЮ."""
    image = _gradient(size, mode="RGBA")
    image.putpixel((0, 0), (255, 255, 255, 0))
    return _encode(image, "PNG")


def make_png_opaque_alpha_channel(size: tuple[int, int] = (40, 30)) -> bytes:
    """PNG С каналом прозрачности, но БЕЗ единого прозрачного пикселя.

    Ровно тот случай, ради которого признак снимается с фактического канала, а
    не с имени режима: наличие канала альфы о прозрачности не говорит ничего.
    """
    return _encode(_gradient(size, mode="RGBA"), "PNG")


def make_palette_png_with_transparency(size: tuple[int, int] = (40, 30)) -> bytes:
    """Палитровый PNG с прозрачностью в служебном блоке, а не в канале.

    Режим ``P`` канала ``A`` не имеет вовсе, и признак, снятый с имени режима,
    объявил бы такую картинку непрозрачной — а пережатие в JPEG залило бы
    прозрачные места белым необратимо.
    """
    image = _gradient(size).convert("P", palette=Image.Palette.ADAPTIVE, colors=16)
    return _encode(image, "PNG", transparency=0)


def make_declared_huge_png(width: int, height: int) -> bytes:
    """PNG, ЗАЯВЛЯЮЩИЙ огромные размеры при крошечном теле.

    Настоящая форма декомпрессионной бомбы: заголовок читается без выделения
    памяти под картинку, поэтому потолок обязан срабатывать ДО ``load()``.
    Данные пикселей заведомо неполны — если проверка размеров пропустит такой
    файл дальше, отказ придёт от декодера, и тест это различает по типу
    исключения.
    """

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        crc = struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + payload + crc

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00" * 16))
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + chunk(b"IEND", b"")


def _open(payload: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(payload))
    image.load()
    return image


# --- D-3: предел длинной стороны и запрет увеличения --------------------------


def test_large_image_is_reduced_to_the_delivery_limit():
    """Снимок 4000x3000 доезжает до хранилища с длинной стороной ровно 1920.

    Число утверждается ТОЧНО, а не неравенством: «не больше 1920» осталось бы
    зелёным и при сжатии до 200 px, то есть не отличило бы выполненное правило
    от испорченной картинки.
    """
    prepared = prepare_upload(make_jpeg((4000, 3000)))

    delivery = _open(prepared.delivery)
    assert max(delivery.size) == DELIVERY_MAX_EDGE
    assert delivery.size == (1920, 1440), delivery.size


def test_small_image_is_never_upscaled():
    """Картинка меньше предела сохраняется в своих размерах, до пикселя (D-3)."""
    prepared = prepare_upload(make_jpeg((800, 600)))

    assert _open(prepared.delivery).size == (800, 600)


def test_portrait_orientation_limits_the_long_edge_not_the_width():
    """Предел применяется к ДЛИННОЙ стороне, какой бы из двух она ни была."""
    prepared = prepare_upload(make_jpeg((1500, 3000)))

    assert _open(prepared.delivery).size == (960, DELIVERY_MAX_EDGE)


# --- D-4: правило формата -----------------------------------------------------


def test_jpeg_stays_jpeg():
    prepared = prepare_upload(make_jpeg((2000, 1000)))

    assert prepared.content_type == "image/jpeg"
    assert prepared.extension == ".jpg"
    assert _open(prepared.delivery).format == "JPEG"


def test_png_without_real_alpha_becomes_jpeg():
    """Фотография, сохранённая как PNG, уходит в хранилище JPEG'ом (D-4).

    Это и есть жалоба, из которой выросла issue #40: то же содержимое в PNG
    весит в разы больше, а мессенджер всё равно пережимает его на своей
    стороне.
    """
    prepared = prepare_upload(make_png((2000, 1000)))

    assert prepared.content_type == "image/jpeg"
    assert prepared.extension == ".jpg"
    assert _open(prepared.delivery).format == "JPEG"


def test_png_with_real_alpha_stays_png():
    prepared = prepare_upload(make_png_with_alpha((2000, 1000)))

    assert prepared.content_type == "image/png"
    assert prepared.extension == ".png"
    delivery = _open(prepared.delivery)
    assert delivery.format == "PNG"
    assert "A" in delivery.getbands()


def test_png_with_a_fully_opaque_alpha_channel_becomes_jpeg():
    """Канал прозрачности сам по себе прозрачностью не является.

    Признак снимается с ФАКТИЧЕСКОГО содержимого канала: иначе любой снимок,
    сохранённый в RGBA, оставался бы PNG навсегда, и правило D-4 не работало бы
    ровно там, где оно нужнее всего.
    """
    prepared = prepare_upload(make_png_opaque_alpha_channel((2000, 1000)))

    assert prepared.content_type == "image/jpeg"
    assert prepared.extension == ".jpg"


def test_palette_png_with_transparency_stays_png():
    """Прозрачность палитрового PNG живёт в служебном блоке, а не в канале."""
    prepared = prepare_upload(make_palette_png_with_transparency((600, 400)))

    assert prepared.content_type == "image/png"
    assert prepared.extension == ".png"


def test_alpha_that_survives_the_rule_keeps_its_transparency():
    """Настоящая альфа доживает до сохранённых байтов, а не заливается фоном.

    Тихая потеря канала даёт сплошной фон там, где пользователь видел
    прозрачность: картинка уезжает в рассылку испорченной, и узнаёт он об этом
    после отправки.
    """
    opaque = Image.new("RGBA", (600, 400), (10, 20, 30, 255))
    opaque.putpixel((0, 0), (0, 0, 0, 0))

    prepared = prepare_upload(_encode(opaque, "PNG"))

    assert prepared.content_type == "image/png"
    delivery = _open(prepared.delivery)
    assert delivery.getchannel("A").getextrema()[0] == 0


# --- T-Q40-05: EXIF применяется к пикселям и снимается с байтов ----------------


def test_exif_orientation_is_applied_to_the_pixels():
    """Тег ориентации 6 меняет стороны местами — поворот выполнен, а не обещан."""
    exif = Image.Exif()
    exif[0x0112] = 6  # Orientation: повернуть на 90 градусов по часовой стрелке
    payload = make_jpeg((400, 200), exif=exif)

    prepared = prepare_upload(payload)

    assert _open(prepared.delivery).size == (200, 400)


def test_exif_section_is_stripped_from_stored_bytes():
    """В сохранённых байтах нет секции Exif (T-Q40-05).

    Сегодня снимок с телефона уезжает в ПУБЛИЧНЫЙ бакет вместе с координатами
    съёмки и серийным номером камеры. Оставить тег ориентации после поворота
    было бы вторым дефектом: читатель, уважающий тег, повернул бы картинку
    второй раз.
    """
    exif = Image.Exif()
    exif[0x0112] = 6
    exif[0x010F] = "CameraMaker"
    payload = make_jpeg((400, 200), exif=exif)
    assert b"Exif" in payload, "во входных байтах Exif нет — тест меряет не то"

    prepared = prepare_upload(payload)

    assert b"Exif" not in prepared.delivery
    assert b"CameraMaker" not in prepared.delivery
    assert b"Exif" not in prepared.thumbnail


# --- T-Q40-01: потолок числа точек --------------------------------------------


def test_image_over_the_pixel_ceiling_is_refused():
    """Отказ приходит ИМЕННО от потолка, а не от сломанного декодера.

    Размеры выбраны выше нашего потолка и ниже встроенного предела Pillow:
    сработать обязана собственная проверка, и сработать ДО ``load()`` — тело
    файла заведомо неполно, и до декодирования дело дойти не должно.
    """
    payload = make_declared_huge_png(8000, 8000)
    assert 8000 * 8000 > MAX_DECODED_PIXELS

    with pytest.raises(ImageTooLarge):
        prepare_upload(payload)


def test_pillow_decompression_bomb_is_reported_as_too_large():
    """Второй рубеж: отказ самого Pillow приводится к тому же исключению.

    Иначе вызывающий получил бы исключение чужого типа и ответил бы 500 там,
    где по смыслу отказ — 400.
    """
    with pytest.raises(ImageTooLarge):
        prepare_upload(make_declared_huge_png(30000, 30000))


def test_image_just_under_the_ceiling_is_accepted():
    """Парный тест: без него предыдущие зеленели бы при отказе ВСЕМУ подряд."""
    prepared = prepare_upload(make_jpeg((400, 300)))

    assert prepared.delivery


# --- нечитаемое и непроизводимое ----------------------------------------------


def test_signature_without_a_decodable_image_is_unreadable():
    """Байты с сигнатурой JPEG, но без картинки, — отдельный класс отказа.

    Пользователю про повреждённый файл и про слишком большой надо сказать
    разное, поэтому исключений два, а не одно.
    """
    payload = b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00" + b"\x00" * 16

    with pytest.raises(ImageUnreadable):
        prepare_upload(payload)


def test_empty_content_is_unreadable():
    with pytest.raises(ImageUnreadable):
        prepare_upload(b"")


@pytest.mark.parametrize("fmt", ["GIF", "WEBP", "BMP"])
def test_correct_image_of_an_unsupported_format_is_refused(fmt):
    """Служба сама решает, что она способна ПРОИЗВЕСТИ (D-5).

    Опираться на то, что вызывающий уже проверил сигнатуру, нельзя: правило
    приёма и правило производства разъехались бы молча, и первый же новый
    вызывающий получил бы в хранилище формат, которого не отправляет ни один
    мессенджер.
    """
    payload = _encode(_gradient((40, 30)), fmt)

    with pytest.raises(ImageUnreadable):
        prepare_upload(payload)


# --- P-6: миниатюра ------------------------------------------------------------


def test_thumbnail_fits_the_thumb_limit():
    prepared = prepare_upload(make_jpeg((4000, 3000)))

    thumbnail = _open(prepared.thumbnail)
    assert max(thumbnail.size) == THUMB_MAX_EDGE
    assert thumbnail.size == (480, 360), thumbnail.size


def test_thumbnail_shares_the_format_of_the_delivery_image():
    """Правило формата одно на оба объекта (P-6).

    Иначе расширение производного ключа описывало бы не те байты, что под ним
    лежат, — тот же класс расхождения, из-за которого расширение ключа
    приводится к формату безусловно.
    """
    for payload, expected in (
        (make_jpeg((2000, 1000)), "JPEG"),
        (make_png((2000, 1000)), "JPEG"),
        (make_png_with_alpha((2000, 1000)), "PNG"),
    ):
        prepared = prepare_upload(payload)
        assert _open(prepared.thumbnail).format == expected
        assert _open(prepared.delivery).format == expected


def test_thumbnail_is_lighter_than_the_delivery_image():
    """Ради этого миниатюра и существует: браузер качает её, а не оригинал."""
    prepared = prepare_upload(make_jpeg((4000, 3000)))

    assert len(prepared.thumbnail) < len(prepared.delivery)


def test_thumbnail_of_a_small_image_is_not_upscaled():
    """Правило «не увеличивать» действует и на миниатюру."""
    prepared = prepare_upload(make_jpeg((200, 150)))

    assert _open(prepared.thumbnail).size == (200, 150)


def test_delivery_bytes_differ_from_the_submitted_bytes():
    """Оригинал не хранится ни под каким ключом (D-2).

    Утверждение на НЕРАВЕНСТВО байтов — единственное, что отличает «пережали»
    от «пропустили как есть»: размеры у мелкой картинки совпадают и там, и там.
    """
    payload = make_png((2000, 1000))
    prepared = prepare_upload(payload)

    assert prepared.delivery != payload
    assert prepared.thumbnail != payload
