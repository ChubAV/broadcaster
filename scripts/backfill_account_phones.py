"""Дозаполнить номер существующих аккаунтов без номера из источника мессенджера.

Скрипт берёт аккаунты, у которых номер неизвестен и не указан вручную, опрашивает
по одному источник их мессенджера и записывает сообщённый номер ТОЛЬКО через
единого писателя Фазы 16 (`fill_reported_phone`), коммитя каждый аккаунт отдельно.

ЧЕГО СКРИПТ НЕ ДЕЛАЕТ. Статус аккаунта, строку сессии и прочие колонки он не
меняет. Признак «указан вручную» не ставит: ручной номер для него неприкосновенен.
Номер в открытом виде не печатает — только маской. Настройку журнала приложения
не подключает: вывод скрипта идёт через `print` в маскированной форме.

Полную шапку с формами вызова и порядком выката допишет оболочка командной строки
(план 20-06).
"""

import asyncio
import collections
import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.models.messenger_account import MessengerAccount
from app.services.phone import mask_phone, normalize_reported


class Outcome(enum.Enum):
    """Исход по одному аккаунту; значения — подписи строк вывода и итога."""

    FILLED = "заполнено"
    KEPT = "ручной / уже заполнен"
    NO_NUMBER = "номера нет"
    DEAD_SESSION = "сессия мертва"
    UNREACHABLE = "воркер недоступен"
    BUSY = "занят, повторите позже"
    ACCOUNT_GONE = "удалён во время прогона"
    FAILED = "сбой по аккаунту"


KINDS = ("tg_user", "wa", "max")

WRITE_OUTCOMES: dict[PhoneWrite, Outcome] = {
    PhoneWrite.WRITTEN: Outcome.FILLED,
    PhoneWrite.KEPT: Outcome.KEPT,
    PhoneWrite.MISSING: Outcome.ACCOUNT_GONE,
    PhoneWrite.UNPARSEABLE: Outcome.NO_NUMBER,
}


@dataclass(frozen=True)
class RunOptions:
    dry_run: bool = False
    kinds: tuple[str, ...] = KINDS
    account_id: int | None = None
    limit: int | None = None


@dataclass(frozen=True)
class AccountRow:
    id: int
    kind: str
    status: str
    credentials: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class SourceReply:
    outcome: Outcome | None
    reported: object = field(default=None, repr=False)
    note: str = ""


class AccountSource(Protocol):
    """Источник номера глазами ядра.

    `SourceReply.outcome` не `None` — исход решён до писателя (сессия мертва,
    воркер недоступен, занят, номера нет). `None` — источник сообщил значение
    `reported`, и решает его единый писатель. Исход «заполнено» принадлежит
    только ядру: источник его не возвращает.
    """

    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply: ...


@dataclass
class RunSummary:
    counts: collections.Counter = field(default_factory=collections.Counter)


async def select_candidates(session_factory, options: RunOptions, kinds) -> list[AccountRow]:
    """Аккаунты без номера и не ручные — при ЛЮБОМ статусе, по возрастанию `id`.

    Выбираются КОЛОНКИ, а не сущности: в сессию скрипта не попадает ни один
    объект `MessengerAccount`, так что менять его нечему (D-12, критерий 1).
    Статус фильтром не служит: отключённому аккаунту номер тоже нужен.
    """
    statement = select(
        MessengerAccount.id,
        MessengerAccount.type,
        MessengerAccount.status,
        MessengerAccount.credentials,
    ).where(
        MessengerAccount.phone.is_(None),
        MessengerAccount.phone_is_manual.is_(False),
        MessengerAccount.type.in_(kinds),
    )
    if options.account_id is not None:
        statement = statement.where(MessengerAccount.id == options.account_id)
    statement = statement.order_by(MessengerAccount.id)
    if options.limit is not None:
        statement = statement.limit(options.limit)
    async with session_factory() as session:
        result = await session.execute(statement)
        return [
            AccountRow(id=r.id, kind=r.type, status=r.status, credentials=r.credentials)
            for r in result.all()
        ]


async def _poll(source: AccountSource, row: AccountRow, options: RunOptions) -> SourceReply:
    """Опрос одного аккаунта: исключение источника — исход аккаунта, не прогона (D-14).

    `BaseException` (отмена, прерывание с клавиатуры) не ловится. В заметку идёт
    только имя класса исключения: текст может нести номер или строку сессии.
    """
    try:
        reply = await source.poll(row, options)
    except Exception as exc:  # noqa: BLE001 — прогон не падает на одном аккаунте
        return SourceReply(Outcome.FAILED, note=type(exc).__name__)
    if reply.outcome is Outcome.FILLED:
        return SourceReply(Outcome.FAILED, note="InvalidSourceReply")
    return reply


async def _write(session_factory, row: AccountRow, reply: SourceReply) -> SourceReply:
    """Запись одного аккаунта: своя сессия, единый писатель, коммит на аккаунт.

    Писатель не коммитит (транзакцией владеет вызывающий), поэтому коммит здесь
    и сразу: записанное раньше не откатывается сбоем следующего аккаунта.
    """
    try:
        async with session_factory() as session:
            try:
                written = await fill_reported_phone(session, row.id, reply.reported)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception as exc:  # noqa: BLE001 — прогон не падает на одном аккаунте
        return SourceReply(Outcome.FAILED, note=type(exc).__name__)
    return SourceReply(WRITE_OUTCOMES[written], reported=reply.reported)


def _preview(reply: SourceReply) -> SourceReply:
    """Режим просмотра: писатель не вызывается ни в каком виде (D-06)."""
    if normalize_reported(reply.reported) is None:
        return SourceReply(Outcome.NO_NUMBER)
    return SourceReply(Outcome.FILLED, reported=reply.reported)


class WorkerStatusSource:
    """Источник номера WA / MAX: собственный запрос `/status` работающего воркера.

    Каркас: наполняется в GREEN (план 20-02).
    """

    def __init__(self, kind: str, *, list_containers=None, transport=None) -> None:
        if kind not in ("wa", "max"):
            raise ValueError(kind)
        self._kind = kind

    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply:
        return SourceReply(Outcome.UNREACHABLE)


def classify_status(body: object) -> SourceReply:
    return SourceReply(Outcome.UNREACHABLE)


async def run(
    session_factory, options: RunOptions, sources: Mapping[str, AccountSource]
) -> RunSummary:
    kinds = tuple(k for k in options.kinds if k in sources)
    rows = await select_candidates(session_factory, options, kinds)

    if options.dry_run:
        print(
            "РЕЖИМ ПРОСМОТРА: ничего не записывается и контейнеры не поднимаются; "
            "Telegram и работающие воркеры опрашиваются"
        )
    else:
        print("РЕЖИМ ЗАПИСИ: запуск без --dry-run записывает номера")
    per_kind = "".join(f"; {k}: {sum(1 for r in rows if r.kind == k)}" for k in kinds)
    print(f"Кандидатов: {len(rows)}{per_kind}")

    summary = RunSummary()
    for row in rows:
        reply = await _poll(sources[row.kind], row, options)
        if reply.outcome is None:
            if options.dry_run:
                reply = _preview(reply)
            else:
                reply = await _write(session_factory, row, reply)
        outcome = reply.outcome
        summary.counts[outcome] += 1
        suffix = f" ({reply.note})" if reply.note else ""
        if outcome is Outcome.FILLED:
            label = f"было бы {Outcome.FILLED.value}" if options.dry_run else Outcome.FILLED.value
            e164 = normalize_reported(reply.reported)
            print(f"#{row.id} {row.kind}: {label} {mask_phone(e164)}{suffix}")
        else:
            print(f"#{row.id} {row.kind}: {outcome.value}{suffix}")

    print("Итог просмотра (ничего не записано):" if options.dry_run else "Итог:")
    for outcome in Outcome:
        print(f"  {outcome.value}: {summary.counts[outcome]}")
    print(f"Всего: {sum(summary.counts.values())}")
    return summary
