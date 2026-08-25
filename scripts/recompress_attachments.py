"""Пережать вложения, загруженные ДО issue #40, и построить недостающие миниатюры.

Формы вызова:

    uv run python scripts/recompress_attachments.py           # сухой прогон
    uv run python scripts/recompress_attachments.py --apply    # с записью

ОБЪЁМ ПРОГОНА — ТОЛЬКО ЖИВЫЕ ВЛОЖЕНИЯ. Множество обрабатываемых ключей берётся
из объявлений и ниоткуда больше. Снимок отправленного, который хранит история,
остаётся дословным: его значения прогон не читает как источник ключей и не
правит. Обхода бакета листингом тоже нет — редактор при откреплении вложения
объект в хранилище оставляет осознанно, значит в бакете заведомо лежат объекты,
на которые не ссылается никто, и прогон по листингу зацепил бы их.

СУХОЙ ПРОГОН — УМОЛЧАНИЕ, И ОН СТОИТ РОВНО СТОЛЬКО ЖЕ ТРАФИКА НА ЧТЕНИЕ,
СКОЛЬКО ПРОГОН С ЗАПИСЬЮ. Чтобы отчитаться РАСЧЁТНЫМ объёмом «после», он
выполняет ту же пересборку: иначе строка «после» была бы догадкой. Не делает он
ровно одного — записи в хранилище. Ждать от сухого прогона дешевизны не следует;
ждать от него безопасности — следует.

ЧЕГО ПРОГОН НЕ ДЕЛАЕТ. Он не убирает из хранилища ни одного объекта — ни
исходных, ни осиротевших: чистка бакета есть отдельная задача, и цена ошибки у
неё другая. Он не правит ни одного значения в базе: сессия открывается только на
чтение, транзакция не закрепляется ни на одной ветке. Он не меняет форму ключа и
не переписывает расширение. Он не обращается ни к одному каналу доставки.

ДВА РЕШЕНИЯ ПО КАЖДОМУ ОБЪЕКТУ НЕЗАВИСИМЫ. Пережимать — только если длинная
сторона больше предела доставки. Строить миниатюру — только если производного
объекта нет. Объект в пределах, но без миниатюры, получает миниатюру и не
пережимается; объект сверх предела, но с миниатюрой, пережимается и второй
миниатюры не получает.
"""

import argparse
import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.models.ad import Ad
from app.services.image_keys import thumb_key
from app.services.images import (
    DELIVERY_MAX_EDGE,
    ImageTooLarge,
    ImageUnreadable,
    probe_image,
    rebuild_stored_image,
)
from app.services.s3 import (
    HEAD_READ_BYTES,
    ObjectHead,
    object_exists,
    open_s3_client,
    put_object_bytes,
    read_object,
    read_object_head,
)

# Причины пропуска — ИМЕНОВАННЫЕ и пересчитанные по одной. Тихий пропуск
# неотличим от успеха, поэтому каждый объект, которого прогон не тронул, обязан
# оказаться ровно в одной строке разбора.
#
# ПРИЧИН ЧЕТЫРЕ, А НЕ ПЯТЬ, И ЭТО РЕШЕНИЕ (D-1), А НЕ УПУЩЕНИЕ. Исходная заметка
# перечисляет пятую — «сохранённый адрес не разобрался в ключ», — но она имеет
# смысл только там, где ключи выводятся из готовых адресов истории. Здесь
# множество ключей берётся из объявлений, обратного разбора адреса в ключ в этом
# файле нет ни одной строкой, и завести под такую причину счётчик значило бы
# поселить в коде путь, по которому не пройдёт никто и никогда.
SKIP_ALREADY_WITHIN_LIMIT = "уже в пределах"
SKIP_THUMBNAIL_EXISTS = "миниатюра есть"
SKIP_UNSUPPORTED_FORMAT = "формат не поддерживается"
SKIP_OVER_PIXEL_CEILING = "превышает потолок пикселей"

SKIP_REASONS = (
    SKIP_ALREADY_WITHIN_LIMIT,
    SKIP_THUMBNAIL_EXISTS,
    SKIP_UNSUPPORTED_FORMAT,
    SKIP_OVER_PIXEL_CEILING,
)

# Сколько ключей неподдерживаемого формата показывать в отчёте. Потолок объявлен
# константой и назван в самом тексте отчёта: усечённый список, поданный как
# полный, читался бы как «таких объектов всего трое».
UNSUPPORTED_EXAMPLES_LIMIT = 10


class AttachmentStore(Protocol):
    """Хранилище глазами ядра прогона.

    Протокол существует ради проверяемости: боевой прогон получает реализацию
    над клиентом хранилища, тест — двойник в памяти, и ни одна ветка решений не
    знает, с кем из двоих работает. Методов ровно четыре, и пятого — меняющего
    состав бакета — здесь нет по построению.
    """

    async def head_bytes(self, key: str, size: int) -> ObjectHead | None: ...

    async def read(self, key: str) -> bytes | None: ...

    async def object_exists(self, key: str) -> bool: ...

    async def put(self, key: str, content: bytes, content_type: str) -> None: ...


class S3AttachmentStore:
    """Реализация протокола над ОДНИМ открытым клиентом хранилища.

    Клиент один на весь проход, а не один на объект: объектов сотни, и
    установление соединения на каждый стоило бы больше, чем сама работа.
    """

    def __init__(self, client, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    async def head_bytes(self, key: str, size: int) -> ObjectHead | None:
        return await read_object_head(self._client, self._bucket, key, size)

    async def read(self, key: str) -> bytes | None:
        return await read_object(self._client, self._bucket, key)

    async def object_exists(self, key: str) -> bool:
        return await object_exists(self._client, self._bucket, key)

    async def put(self, key: str, content: bytes, content_type: str) -> None:
        await put_object_bytes(self._client, self._bucket, key, content, content_type)


@dataclass
class Report:
    """Счётчики прогона.

    ``not_shrunk`` сознательно стоит ОТДЕЛЬНО от разбора пропусков и в
    ``skips`` не входит. Это не причина пропуска: объект был выбран в работу,
    прочитан целиком и пересобран — и оставлен прежним только потому, что
    пересобранные байты не оказались меньше исходных. Сложить его со
    счётчиками пропуска значило бы завести пятую причину вопреки D-1 и
    отчитаться о непрочитанном объекте как о прочитанном.
    """

    scanned: int = 0
    processed: int = 0
    bytes_before: int = 0
    bytes_after: int = 0
    thumb_bytes_added: int = 0
    not_shrunk: int = 0
    skips: dict[str, int] = field(
        default_factory=lambda: {reason: 0 for reason in SKIP_REASONS}
    )
    unsupported_examples: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)

    def skip(self, reason: str) -> None:
        self.skips[reason] += 1

    def remember_unsupported(self, key: str) -> None:
        if len(self.unsupported_examples) < UNSUPPORTED_EXAMPLES_LIMIT:
            self.unsupported_examples.append(key)


async def collect_attachment_keys(session) -> list[str]:
    """Ключи вложений всех объявлений, по одному разу каждый.

    ИСТОЧНИК РОВНО ОДИН, И ЭТО РЕШЕНИЕ (D-1), А НЕ НЕДОСМОТР. Ключ, живущий
    только в снимке отправленного, сюда не попадает: снимок остаётся дословным,
    а перезапись объекта на месте меняла бы то, что история показывает задним
    числом.

    Повторы устраняются с сохранением порядка первого появления: один и тот же
    ключ, приложенный к двум объявлениям, есть ОДИН объект в хранилище, и
    обрабатывать его дважды значило бы второй раз пережать уже пережатое.
    """
    result = await session.execute(select(Ad.images))

    keys: list[str] = []
    seen: set[str] = set()
    for images in result.scalars().all():
        if not isinstance(images, list):
            continue
        for value in images:
            if not isinstance(value, str) or not value or value in seen:
                continue
            seen.add(value)
            keys.append(value)

    return keys


async def _process_key(key: str, store: AttachmentStore, report: Report, *, apply: bool) -> None:
    """Разобрать один ключ. Полное тело читается ТОЛЬКО при решении о работе."""
    head = await store.head_bytes(key, HEAD_READ_BYTES)
    if head is None:
        report.errors.append((key, "объекта нет в хранилище"))
        return

    content: bytes | None = None
    try:
        probe = probe_image(head.body)
    except ImageTooLarge:
        # Отказ ДО полного чтения: объект сверх потолка не выкачивается и не
        # декодируется. Хранилище — не более доверенный вход, чем тело запроса.
        report.skip(SKIP_OVER_PIXEL_CEILING)
        return
    except ImageUnreadable:
        if len(head.body) >= head.size:
            # Тело было полным — разбирать больше нечего.
            report.skip(SKIP_UNSUPPORTED_FORMAT)
            report.remember_unsupported(key)
            return

        # Заголовок оказался короче, чем нужно этому файлу: у JPEG маркер
        # размеров стоит за секциями метаданных и мог не поместиться в
        # диапазон. Один откат на полное чтение — и повторный разбор; без него
        # исправный снимок был бы объявлен битым, и отчёт солгал бы ровно там,
        # где обязан не лгать.
        content = await store.read(key)
        if content is None:
            report.errors.append((key, "объект исчез между чтениями"))
            return
        try:
            probe = probe_image(content)
        except ImageTooLarge:
            report.skip(SKIP_OVER_PIXEL_CEILING)
            return
        except ImageUnreadable:
            report.skip(SKIP_UNSUPPORTED_FORMAT)
            report.remember_unsupported(key)
            return

    # Два независимых решения. Счётчики выставляются ОБА, даже когда объект в
    # итоге пропускается по обоим: иначе разбор отчёта отвечал бы на вопрос
    # «почему пропустили» половиной причины.
    needs_resize = probe.long_edge > DELIVERY_MAX_EDGE
    if not needs_resize:
        report.skip(SKIP_ALREADY_WITHIN_LIMIT)

    needs_thumbnail = not await store.object_exists(thumb_key(key))
    if not needs_thumbnail:
        report.skip(SKIP_THUMBNAIL_EXISTS)

    if not needs_resize and not needs_thumbnail:
        return

    if content is None:
        content = await store.read(key)
        if content is None:
            report.errors.append((key, "объект исчез между чтениями"))
            return

    try:
        rebuilt = rebuild_stored_image(
            content, resize=needs_resize, thumbnail=needs_thumbnail
        )
    except ImageTooLarge:
        # Заголовок заявил одно, тело понесло другое — вторая проверка потолка
        # для того и стоит на полных байтах.
        report.skip(SKIP_OVER_PIXEL_CEILING)
        return
    except ImageUnreadable:
        report.skip(SKIP_UNSUPPORTED_FORMAT)
        report.remember_unsupported(key)
        return

    report.processed += 1
    report.bytes_before += len(content)

    size_after = len(content)
    if rebuilt.delivery is not None:
        if len(rebuilt.delivery) < len(content):
            if apply:
                await store.put(key, rebuilt.delivery, rebuilt.content_type)
            size_after = len(rebuilt.delivery)
        else:
            # Пересборка не уменьшила объект — исходные байты остаются на месте.
            # Правило записи, а не причина пропуска: прогон, затеянный ради
            # экономии места, не имеет права его добавлять.
            report.not_shrunk += 1
    report.bytes_after += size_after

    if rebuilt.thumbnail is not None:
        if apply:
            await store.put(thumb_key(key), rebuilt.thumbnail, rebuilt.content_type)
        # Вес миниатюры учитывается ОТДЕЛЬНЫМ полем, а не вычитается из
        # экономии: миниатюра есть новые байты в хранилище, и складывать её с
        # экономией значило бы отчитаться прибылью за расход.
        report.thumb_bytes_added += len(rebuilt.thumbnail)


async def recompress_attachments(session, store: AttachmentStore, *, apply: bool) -> Report:
    """Пройти все ключи вложений по одному и вернуть отчёт.

    Разбор каждого ключа обёрнут перехватом отказов: прогон из сотен объектов не
    имеет права закончиться на одном. Неожиданный отказ хранилища или пересборки
    становится строкой в группе ошибок с названным ключом — молчаливое
    продолжение сделало бы отчёт неотличимым от успешного.
    """
    report = Report()

    for key in await collect_attachment_keys(session):
        report.scanned += 1
        try:
            await _process_key(key, store, report, apply=apply)
        except Exception as exc:  # noqa: BLE001 — прогон не падает на одном ключе
            report.errors.append((key, f"{type(exc).__name__}: {exc}"))

    return report


def _human_bytes(value: int) -> str:
    size = float(value)
    for unit in ("Б", "КиБ", "МиБ", "ГиБ"):
        if size < 1024 or unit == "ГиБ":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ГиБ"


def format_report(report: Report, *, apply: bool = False) -> str:
    """Текст отчёта, по которому можно принять решение о запуске с записью."""
    saved = report.bytes_before - report.bytes_after
    percent = (saved / report.bytes_before * 100) if report.bytes_before else 0.0

    lines = [
        f"Просмотрено ключей вложений: {report.scanned}",
        f"Объектов взято в работу: {report.processed}",
        f"Объём до: {_human_bytes(report.bytes_before)}",
        f"Объём после (расчётный): {_human_bytes(report.bytes_after)}",
        f"Экономия: {_human_bytes(saved)} ({percent:.1f}%)",
        f"Добавлено миниатюрами: {_human_bytes(report.thumb_bytes_added)}",
        "",
        "Пропущено по причинам:",
    ]

    # Разбор рендерится ОБХОДОМ кортежа, а не перечислением строк здесь: две
    # копии перечня разъехались бы, и первым признаком расхождения стала бы
    # недостающая строка в отчёте боевого прогона.
    for reason in SKIP_REASONS:
        lines.append(f"  {reason}: {report.skips[reason]}")

    if report.unsupported_examples:
        lines.append(
            f"  примеры ключей неподдерживаемого формата "
            f"(показано не более {UNSUPPORTED_EXAMPLES_LIMIT}):"
        )
        for key in report.unsupported_examples:
            lines.append(f"    {key}")

    lines.append("")
    lines.append(
        f"Пересобрано без уменьшения объёма (не пропуск, объект оставлен прежним): "
        f"{report.not_shrunk}"
    )

    lines.append("")
    if report.errors:
        lines.append(f"Ошибки ({len(report.errors)}):")
        for key, message in report.errors:
            lines.append(f"  {key}: {message}")
    else:
        lines.append("Ошибок нет.")

    if not apply:
        lines.append("")
        lines.append(
            "Сухой прогон: в хранилище не записано ничего. "
            "Запуск с записью — тот же вызов с флагом --apply."
        )

    return "\n".join(lines)


async def main(apply: bool) -> None:
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        # Сессия здесь ТОЛЬКО ЧИТАЕТ, и закрепления транзакции ниже нет ни на
        # одной ветке. Сказано прямо, потому что иначе следующий читатель примет
        # его отсутствие за забытую строку и добавит.
        async with open_s3_client(
            settings.s3_endpoint_url,
            settings.s3_access_key,
            settings.s3_secret_key,
            settings.s3_region,
        ) as client:
            store = S3AttachmentStore(client, settings.s3_bucket_name)
            # Пересборка вызывается ПРЯМО, без выноса в отдельный поток. Маршрут
            # загрузки уносит ту же работу в поток потому, что его событийный
            # цикл обслуживает другие запросы; здесь цикл не обслуживает ничего,
            # и вынос был бы обрядом.
            report = await recompress_attachments(session, store, apply=apply)

    print(format_report(report, apply=apply))

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Пережать вложения объявлений сверх предела доставки и построить "
            "недостающие миниатюры"
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записывать результат в хранилище (по умолчанию — сухой прогон)",
    )
    args = parser.parse_args()
    asyncio.run(main(apply=args.apply))
