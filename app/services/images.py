"""Пережатие загруженного изображения и его миниатюра (issue #40).

Модуль НЕЙТРАЛЕН к транспорту: он получает байты и возвращает байты, ничего не
знает ни о HTTP, ни о хранилище и своих исключений в коды ответа не переводит.
Так сделано потому, что решение «какой отказ каким кодом» принадлежит маршруту,
а решение «что мы вообще способны произвести» — этому файлу, и сливать их в одно
означало бы, что второй вызывающий унаследует чужую политику ответов.

ПОЧЕМУ ПОТОЛОК ЧИСЛА ТОЧЕК СНИМАЕТСЯ С ЗАГОЛОВКА, А НЕ ПОСЛЕ ДЕКОДИРОВАНИЯ.
До этой задачи проект СОЗНАТЕЛЬНО не открывал недоверенный файл декодером — это
записано в шапке `app/routes/uploads.py` прямым текстом. Запрет снят здесь не
потому, что риск исчез, а потому, что он ограничен явным пределом. Заголовок
изображения ЗАЯВЛЯЕТ размеры, и заявить он может любые: файл в четыре килобайта
объявляет 30000x30000 и превращается в 3,6 ГБ распакованных пикселей ровно в тот
момент, когда его начинают декодировать. `Image.open()` заголовок читает, но
пиксели не распаковывает, поэтому проверка размеров стоит МЕЖДУ открытием и
`load()` — единственное место, где она вообще что-то стоит. Проверка размера
ТЕЛА (`max_image_size_mb`) от этого не спасает и не отменяется: она измеряет
сжатый файл, а бомба и есть маленький сжатый файл.

Число `MAX_DECODED_PIXELS` выведено из ПАМЯТИ, а не из вкуса. 30 млн точек в
RGBA — это около 120 МБ на один запрос, а боевой артефакт держит один
uvicorn-воркер без политики перезапуска (`docker-compose.prod.yml`), то есть OOM
на этом пути кладёт весь продукт, а не один запрос. 30 млн проходит любая
24-мегапиксельная камера и любой телефонный снимок обычного режима;
50-мегапиксельный снимок отвергается, и текст отказа на маршруте говорит об этом
прямо, не предлагая «выбрать другой формат» — формат тут ни при чём.

ПОЧЕМУ ДЛЯ JPEG ВЫЗЫВАЕТСЯ `draft()`, А ДЛЯ PNG АНАЛОГА НЕТ. JPEG хранит
картинку блоками частот, и его декодер умеет отдать её уменьшенной в 2, 4 или 8
раз прямо на этапе DCT, если заранее сказать, какой размер нужен. Целевой размер
известен — 1920, — поэтому для крупных снимков пик памяти и время декодирования
падают на порядок, и потолок выше перестаёт быть ЕДИНСТВЕННОЙ защитой: он
остаётся границей, но обычный путь до неё больше не доходит. `draft()` при этом
никогда не отдаёт размер МЕНЬШЕ запрошенного, поэтому последующее уменьшение до
точного предела остаётся корректным. PNG сжат построчно и такой возможности не
имеет вовсе — там работает только потолок, и это осознанная асимметрия, а не
недоделка.

ПОЧЕМУ EXIF СНАЧАЛА ПРИМЕНЯЕТСЯ, А ПОТОМ СНИМАЕТСЯ. Тег ориентации — это не
поворот, а ПРОСЬБА повернуть, адресованная читателю. Три варианта обращения с
ним дают три разных дефекта: оставить как есть — и снимок с телефона уйдёт в
рассылку лежащим на боку у всех, кто просьбу не читает; применить и сохранить
тег — и те, кто читает, повернут картинку второй раз; снять не применив — то же
самое, что первое. Поэтому поворот выполняется НАД ПИКСЕЛЯМИ, а метаданные в
сохранённые байты не переносятся вовсе. Побочный, но названный эффект — тот
самый, ради которого это записано отдельным абзацем: сегодня снимок уезжает в
ПУБЛИЧНЫЙ бакет вместе с координатами съёмки и серийным номером камеры
(T-Q40-05), а публичный там означает «по прямой ссылке, без единой проверки».

ПОЧЕМУ PNG БЕЗ НАСТОЯЩЕЙ АЛЬФЫ СТАНОВИТСЯ JPEG. Фотография, сохранённая как PNG,
весит в разы больше при том же содержимом — это ровно та жалоба, из которой
выросла issue #40, и оставить её нетронутой значило бы закрыть задачу наполовину.
Обратное решение (пережимать в JPEG всё подряд) отвергнуто: логотип с
прозрачным фоном, залитый белым, приходит в рассылку испорченным, и заметно это
становится в чужой группе. Признак поэтому снимается с ФАКТИЧЕСКОГО канала
прозрачности, а не с имени режима: RGBA без единого прозрачного пикселя — это
фотография, а палитровый PNG с прозрачностью в служебном блоке канала `A` не
имеет вовсе, хотя прозрачность в нём настоящая.
"""

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

# Потолок числа точек. Разбор числа — в шапке модуля: он про память одного
# воркера, а не про «достаточно большое разрешение».
MAX_DECODED_PIXELS = 30_000_000

# Предел для картинки, уходящей в рассылку (D-3). Мессенджеры пережимают её на
# своей стороне в любом случае, поэтому всё, что хранится сверх этого предела,
# не увидит никто, а оплачено будет хранилищем и трафиком.
DELIVERY_MAX_EDGE = 1920
DELIVERY_JPEG_QUALITY = 85

# Предел миниатюры. Интерфейс рисует вложение плиткой 96 px и аватаркой 32 px,
# так что 480 покрывает и экраны с двойной плотностью, и предпросмотр.
THUMB_MAX_EDGE = 480
THUMB_JPEG_QUALITY = 75

# Форматы, которые модуль способен ПРОИЗВЕСТИ. Список совпадает с тем, что
# принимает маршрут загрузки (issue #39), но выписан здесь ОТДЕЛЬНО и намеренно:
# полагаться на то, что вызывающий уже проверил сигнатуру, — значит согласиться,
# что первый же новый вызывающий положит в хранилище формат, которого не
# отправляет ни один мессенджер.
_SUPPORTED_FORMATS = frozenset({"JPEG", "PNG"})

_JPEG = "JPEG"
_PNG = "PNG"
_FORMAT_CONTENT_TYPES = {_JPEG: "image/jpeg", _PNG: "image/png"}
# Расширение JPEG приводится к `.jpg`, а не к `.jpeg`: форма ключа объекта
# должна быть одной, а Telethon выводит тип медиа из расширения в имени файла.
_FORMAT_EXTENSIONS = {_JPEG: ".jpg", _PNG: ".png"}


class ImageTooLarge(Exception):
    """В изображении больше точек, чем модуль соглашается декодировать."""


class ImageUnreadable(Exception):
    """Байты не разбираются в изображение поддерживаемого формата.

    Отдельный тип, а не общий с ``ImageTooLarge``, потому что пользователю про
    эти два случая надо сказать РАЗНОЕ: повреждённому файлу подходит совет
    «выберите другой», а корректному снимку на 50 Мп он был бы советом мимо
    причины.
    """


@dataclass(frozen=True)
class PreparedImage:
    """Оба объекта одной загрузки и общее для них описание формата.

    Тип один на сжатую версию и миниатюру намеренно: правило формата у них
    общее (P-6), поэтому расширение производного ключа верно по построению, а не
    по договорённости между двумя местами кода.
    """

    delivery: bytes
    thumbnail: bytes
    content_type: str
    extension: str


def _has_real_alpha(image: Image.Image) -> bool:
    """Есть ли в изображении хотя бы один не полностью непрозрачный пиксель.

    Признак снимается с фактического канала прозрачности. Палитровый режим
    канала ``A`` не имеет, и прозрачность живёт у него в служебном блоке
    ``transparency`` — такой PNG приводится к RGBA специально, иначе логотип с
    прозрачным фоном был бы объявлен фотографией и залит белым необратимо.
    """
    if image.mode == "P":
        if "transparency" not in image.info:
            return False
        probe = image.convert("RGBA")
    elif "A" in image.getbands():
        probe = image
    else:
        return False

    return probe.getchannel("A").getextrema()[0] < 255


def _fit_long_edge(image: Image.Image, max_edge: int) -> Image.Image:
    """Уменьшить изображение до предела длинной стороны, НИКОГДА не увеличивая.

    Целевой размер считается от длинной стороны и присваивается ей ТОЧНО, а не
    получается округлением обеих: `thumbnail()` из Pillow даёт по длинной
    стороне то `max_edge`, то `max_edge - 1` в зависимости от соотношения, и
    утверждение «длинная сторона равна 1920» на нём было бы недоказуемым.
    """
    width, height = image.size
    if max(width, height) <= max_edge:
        return image

    if width >= height:
        target = (max_edge, max(1, round(height * max_edge / width)))
    else:
        target = (max(1, round(width * max_edge / height)), max_edge)

    return image.resize(target, Image.Resampling.LANCZOS)


def _normalise_mode(image: Image.Image, keeps_alpha: bool) -> Image.Image:
    """Привести режим к тому, в котором изображение будет уменьшаться и кодироваться.

    ПРИВЕДЕНИЕ ИДЁТ ДО УМЕНЬШЕНИЯ, И ЭТО НЕ ПЕРЕСТАНОВКА РАДИ ПОРЯДКА. Pillow
    отказывается применять качественные фильтры к палитровому режиму: `resize`
    для режимов `P` и `1` ВСЕГДА берёт ближайшего соседа, потому что
    интерполировать номера цветов в палитре бессмысленно. Логотип, уменьшенный
    ближайшим соседом с 1200 px до 480, приходит с рваными краями — то есть
    задача, затеянная ради вида и веса картинок, портила бы ровно те картинки, у
    которых палитра и заведена. После приведения к RGB/RGBA фильтр работает как
    задумано.

    Прозрачность, которая по правилу формата не сохраняется, подкладывается на
    БЕЛЫЙ фон, а не отбрасывается: простое ``convert("RGB")`` сняло бы канал
    тихо, и прозрачные места стали бы чёрными — увидел бы это пользователь уже в
    чужой группе.

    Режим `L` сохраняется как есть: JPEG умеет хранить полутоновое изображение
    одним каналом, и приведение к RGB утроило бы вес чёрно-белого снимка на
    ровном месте.
    """
    if keeps_alpha:
        return image if image.mode == "RGBA" else image.convert("RGBA")

    has_alpha = "A" in image.getbands() or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background

    if image.mode in ("RGB", "L"):
        return image

    return image.convert("RGB")


def _encode(image: Image.Image, target_format: str, quality: int) -> bytes:
    """Закодировать изображение БЕЗ метаданных.

    Ни ``exif=``, ни цветовой профиль в сохранение не передаются: Pillow берёт
    их только из явных аргументов, поэтому отсутствие аргумента и есть снятие
    секции. Утверждение закреплено тестом на сами байты, а не на этот
    комментарий.
    """
    buffer = io.BytesIO()
    if target_format == _JPEG:
        image.save(
            buffer, format=_JPEG, quality=quality, optimize=True, progressive=True
        )
    else:
        image.save(buffer, format=_PNG, optimize=True)
    return buffer.getvalue()


def prepare_upload(content: bytes) -> PreparedImage:
    """Сжать загруженное изображение и построить его миниатюру.

    ПОРЯДОК ШАГОВ — ЧАСТЬ КОНТРАКТА, а не деталь реализации:

    1. открыть ЗАГОЛОВОК (пиксели при этом не распаковываются);
    2. убедиться, что формат — один из пары JPEG/PNG;
    3. снять заявленные размеры и сверить с ``MAX_DECODED_PIXELS``;
    4. для JPEG сообщить декодеру целевой размер (``draft``);
    5. декодировать;
    6. применить ориентацию из EXIF к пикселям;
    7. определить наличие НАСТОЯЩЕЙ альфы и выбрать формат;
    8. привести режим к RGB/RGBA/L — ДО уменьшения, иначе палитровому
       изображению не достанется качественного фильтра;
    9. уменьшить до ``DELIVERY_MAX_EDGE``, никогда не увеличивая, и закодировать;
    10. уменьшить ЕЁ ЖЕ до ``THUMB_MAX_EDGE`` и закодировать миниатюру.

    Шаг 3 стоит перед шагом 5, и это единственная причина, по которой открывать
    недоверенный файл здесь вообще допустимо. Шаг 10 идёт от уже уменьшенного
    изображения: второго декодирования исходных байтов не происходит ни при
    каких входах — одна распаковка, два кодирования.

    Поднимает ``ImageTooLarge`` при превышении потолка и ``ImageUnreadable``,
    если байты не разбираются в изображение поддерживаемого формата. Оба отказа
    случаются ДО того, как что-либо уходит в хранилище: функция чистая и в
    хранилище не пишет вовсе.
    """
    try:
        with Image.open(io.BytesIO(content)) as opened:
            source_format = opened.format
            if source_format not in _SUPPORTED_FORMATS:
                raise ImageUnreadable(f"unsupported format: {source_format!r}")

            width, height = opened.size
            if width * height > MAX_DECODED_PIXELS:
                # Отказ ДО `load()`: ниже этой строки заявленные размеры
                # превратились бы в выделенную память.
                raise ImageTooLarge(f"{width}x{height} exceeds {MAX_DECODED_PIXELS}")

            if source_format == _JPEG:
                opened.draft(None, (DELIVERY_MAX_EDGE, DELIVERY_MAX_EDGE))

            # exif_transpose поворачивает ПИКСЕЛИ и возвращает копию, живущую
            # отдельно от закрываемого файлового объекта.
            image = ImageOps.exif_transpose(opened)
    except Image.DecompressionBombError as exc:
        # Второй рубеж за явным потолком, а не замена ему: собственная проверка
        # стоит ниже встроенной, и порог у Pillow свой.
        raise ImageTooLarge(str(exc)) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageUnreadable(str(exc)) from exc

    keeps_alpha = source_format == _PNG and _has_real_alpha(image)
    target_format = _PNG if keeps_alpha else _JPEG

    image = _normalise_mode(image, keeps_alpha)
    delivery_image = _fit_long_edge(image, DELIVERY_MAX_EDGE)
    delivery = _encode(delivery_image, target_format, DELIVERY_JPEG_QUALITY)

    thumbnail_image = _fit_long_edge(delivery_image, THUMB_MAX_EDGE)
    thumbnail = _encode(thumbnail_image, target_format, THUMB_JPEG_QUALITY)

    return PreparedImage(
        delivery=delivery,
        thumbnail=thumbnail,
        content_type=_FORMAT_CONTENT_TYPES[target_format],
        extension=_FORMAT_EXTENSIONS[target_format],
    )


# --- Соседний вход: пересборка УЖЕ ЛЕЖАЩЕГО объекта ---------------------------
#
# ЧЕМ ЭТОТ ВХОД ОТЛИЧАЕТСЯ ОТ `prepare_upload` И ПОЧЕМУ РАЗНИЦА ИМЕННО ТАКАЯ.
# `prepare_upload` обслуживает НОВУЮ загрузку, и ключ объекта в этот момент ещё
# только сочиняется: расширение можно переписать, потому что никто его пока не
# видел. У объекта, который уже лежит в хранилище, ключ РОЗДАН — он записан в
# `Ad.images`, вставлен в готовые адреса внутри `SendLog.ad_images` и уходит в
# мессенджеры. Поэтому здесь формат исходного объекта СОХРАНЯЕТСЯ: сохранить
# JPEG-байты под именем на `.png` значило бы развести расширение с содержимым и
# воспроизвести issue #39 (Telethon выводит тип медиа из расширения), а сменить
# ключ значило бы осиротить адреса, уже лежащие в истории. Экономия на
# непрозрачном PNG при этом теряется — это названная плата, а не недосмотр.
#
# Второе отличие: кодирование включается РЕШЕНИЕМ ВЫЗЫВАЮЩЕГО, а не происходит
# всегда. `prepare_upload` кодирует безусловно, и это верно для входа, о котором
# ничего не известно. Прогнать через кодек снимок, который и так 1200 px, значит
# пережать уже сжатое: вес почти не изменится, а поколение потеряется —
# добавятся артефакты. Поэтому оба продукта — уменьшенный объект и миниатюра —
# запрашиваются флагами по отдельности, и «не запрашивалось» отличимо от
# «получилось пусто».


@dataclass(frozen=True)
class ImageProbe:
    """Формат и ЗАЯВЛЕННЫЕ размеры изображения, снятые с заголовка."""

    format: str
    width: int
    height: int

    @property
    def long_edge(self) -> int:
        return max(self.width, self.height)


@dataclass(frozen=True)
class RebuiltImage:
    """Продукты пересборки существующего объекта.

    ``None`` означает «не запрашивалось» и это НЕ то же самое, что пустые байты:
    вызывающий по этому различию решает, писать ли под соответствующим ключом
    вообще, и пустые байты он бы записал.
    """

    delivery: bytes | None
    thumbnail: bytes | None
    content_type: str


def probe_image(header: bytes) -> ImageProbe:
    """Снять формат и размеры с ЗАГОЛОВКА, не распаковывая пиксели.

    Между ``Image.open()`` и возвратом нет ни одного вызова, который потребовал
    бы пикселей, — потому функция и годится для первых килобайт объекта, а не
    для его полного тела. Именно на этом стоит вся дисциплина трафика
    обслуживающего прогона: объект, по которому решено ничего не делать, стоит
    одного диапазонного чтения.

    Поднимает ``ImageUnreadable``, если формат вне пары JPEG/PNG или байты не
    разбираются, и ``ImageTooLarge``, если произведение ЗАЯВЛЕННЫХ сторон
    превышает ``MAX_DECODED_PIXELS``. Объект в хранилище — не более доверенный
    вход, чем тело запроса: потолок тот же и порядок тот же.
    """
    try:
        with Image.open(io.BytesIO(header)) as opened:
            source_format = opened.format
            if source_format not in _SUPPORTED_FORMATS:
                raise ImageUnreadable(f"unsupported format: {source_format!r}")

            width, height = opened.size
            if width * height > MAX_DECODED_PIXELS:
                raise ImageTooLarge(f"{width}x{height} exceeds {MAX_DECODED_PIXELS}")

            return ImageProbe(format=source_format, width=width, height=height)
    except Image.DecompressionBombError as exc:
        raise ImageTooLarge(str(exc)) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageUnreadable(str(exc)) from exc


def rebuild_stored_image(
    content: bytes, *, resize: bool, thumbnail: bool
) -> RebuiltImage:
    """Пересобрать объект, УЖЕ лежащий в хранилище, БЕЗ смены формата.

    ПОРЯДОК ШАГОВ — ЧАСТЬ КОНТРАКТА:

    1. открыть заголовок и убедиться, что формат — один из пары JPEG/PNG;
    2. сверить потолок точек ПОВТОРНО, уже на полных байтах: заголовок,
       прочитанный диапазонным запросом, мог заявить одно, а тело нести другое,
       и доверять первой проверке значило бы декодировать по обещанию;
    3. для JPEG сообщить декодеру целевой размер (``draft``);
    4. декодировать;
    5. применить ориентацию из EXIF к пикселям;
    6. определить наличие настоящей альфы и привести режим;
    7. построить запрошенное флагами.

    Миниатюра строится от УЖЕ уменьшенного изображения, когда уменьшение
    запрашивалось, и от приведённого исходного, когда нет: второго
    декодирования исходных байтов не происходит ни при каких входах.

    Вызов с обоими флагами ``False`` — ошибка вызывающего: работы для функции
    нет, и она вернёт обе позиции пустыми.
    """
    try:
        with Image.open(io.BytesIO(content)) as opened:
            source_format = opened.format
            if source_format not in _SUPPORTED_FORMATS:
                raise ImageUnreadable(f"unsupported format: {source_format!r}")

            width, height = opened.size
            if width * height > MAX_DECODED_PIXELS:
                raise ImageTooLarge(f"{width}x{height} exceeds {MAX_DECODED_PIXELS}")

            if source_format == _JPEG:
                target_edge = DELIVERY_MAX_EDGE if resize else THUMB_MAX_EDGE
                opened.draft(None, (target_edge, target_edge))

            image = ImageOps.exif_transpose(opened)
    except Image.DecompressionBombError as exc:
        raise ImageTooLarge(str(exc)) from exc
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise ImageUnreadable(str(exc)) from exc

    # Целевой формат равен формату ИСХОДНОГО объекта и ничему другому — здесь и
    # живёт расхождение с `prepare_upload`, разобранное в шапке раздела.
    target_format = source_format

    # Проверка альфы нужна и там, где формат не меняется. Без неё палитровый PNG
    # был бы приведён к четырёхканальному RGBA и после пересборки мог бы
    # ВЫРАСТИ — то есть прогон, затеянный ради экономии места, сделал бы хуже, а
    # логотип с прозрачным фоном был бы залит белым необратимо.
    keeps_alpha = source_format == _PNG and _has_real_alpha(image)
    image = _normalise_mode(image, keeps_alpha)

    delivery: bytes | None = None
    delivery_image = image
    if resize:
        delivery_image = _fit_long_edge(image, DELIVERY_MAX_EDGE)
        delivery = _encode(delivery_image, target_format, DELIVERY_JPEG_QUALITY)

    thumbnail_bytes: bytes | None = None
    if thumbnail:
        thumbnail_image = _fit_long_edge(delivery_image, THUMB_MAX_EDGE)
        thumbnail_bytes = _encode(thumbnail_image, target_format, THUMB_JPEG_QUALITY)

    return RebuiltImage(
        delivery=delivery,
        thumbnail=thumbnail_bytes,
        content_type=_FORMAT_CONTENT_TYPES[target_format],
    )
