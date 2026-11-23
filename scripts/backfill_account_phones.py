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

from sqlalchemy import exists, select

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
    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply: ...


@dataclass
class RunSummary:
    counts: collections.Counter = field(default_factory=collections.Counter)


async def run(
    session_factory, options: RunOptions, sources: Mapping[str, AccountSource]
) -> RunSummary:
    return RunSummary()
