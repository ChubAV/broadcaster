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
import dataclasses
import enum
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.messengers.base import reported_phone_from_status
from app.models.messenger_account import MessengerAccount
from app.services import max_container_manager, wa_container_manager
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

# Менеджеры контейнеров воркеров: читаются только список и порт, подъёма здесь нет.
CONTAINER_MANAGERS = {"wa": wa_container_manager, "max": max_container_manager}

STATUS_TIMEOUT = httpx.Timeout(10.0, connect=3.0)

# Окна ожидания поднятого по флагу воркера (усмотрение 4 исследования). WA ждёт
# `/health` до 90 с и спрашивает `/status` один раз; MAX ждёт `/health` до 30 с и затем
# опрашивает `/status` до `connected: true` — счётом попыток, не часами.
WA_READY_TIMEOUT = 90.0
MAX_READY_TIMEOUT = 30.0
MAX_CONNECT_ATTEMPTS = 45
MAX_POLL_INTERVAL = 2.0

NOTE_NOT_CONNECTED = "не подключён"

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
    wake: bool = False


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
    return SourceReply(WRITE_OUTCOMES[written], reported=reply.reported, note=reply.note)


def _preview(reply: SourceReply) -> SourceReply:
    """Режим просмотра: писатель не вызывается ни в каком виде (D-06)."""
    if normalize_reported(reply.reported) is None:
        return SourceReply(Outcome.NO_NUMBER, note=reply.note)
    return SourceReply(Outcome.FILLED, reported=reply.reported, note=reply.note)


def queue_key(kind: str, account_id: int) -> str:
    """Ключ очереди работы воркера — тот же, что читают `manage_wa_containers` / `manage_max_containers`."""
    return f"{kind}:queue:{account_id}"


class WorkerStatusSource:
    """Источник номера WA / MAX: собственный запрос `/status` работающего воркера.

    «Работает ли воркер» решает ТОЛЬКО Docker: контейнер `<тип>-worker-<id>` со
    статусом `running`. Адрес строится из имени контейнера, и аккаунт без
    работающего контейнера получает исход «воркер недоступен» без единого запроса
    и без подъёма контейнера (D-04). Адаптеры WA/MAX здесь намеренно не
    используются: без явного адреса они сами будят остановленный воркер, а их
    метод «свой номер» сливает «недоступен», «сессия мертва» и «номера нет» в одно
    `None`. Источник номера прежний — поле `phone` ответа `/status`.

    Список контейнеров читается один раз на экземпляр (то есть на тип за прогон);
    отказ Docker запоминается и становится исходом каждого аккаунта типа.
    Источник ничего не печатает: в заметки идут только имя класса, код ответа или
    фраза таблицы (тело ответа и текст исключения номер несли бы в вывод).
    """

    def __init__(
        self,
        kind: str,
        *,
        list_containers=None,
        transport=None,
        start=None,
        stop=None,
        wait_ready=None,
        running_now=None,
        queue_len=None,
        sleep=None,
    ) -> None:
        if kind not in CONTAINER_MANAGERS:
            raise ValueError(f"неизвестный тип воркера: {kind!r}")
        self._kind = kind
        self._manager = CONTAINER_MANAGERS[kind]
        self._list_containers = list_containers or self._manager.list_worker_containers
        self._transport = transport
        self._start = start or self._manager.start_container
        self._stop = stop or self._manager.stop_container
        self._wait_ready = wait_ready or self._manager.wait_for_container_ready
        self._running_now = running_now or self._manager.get_container_endpoint
        self._queue_len = queue_len
        self._sleep = sleep or asyncio.sleep
        self._loaded = False
        self._running: dict[int, str] = {}
        self._docker_error: str | None = None

    async def _load(self) -> None:
        """Один вызов списка контейнеров за прогон; результат или отказ кэшируются."""
        if self._loaded:
            return
        self._loaded = True
        try:
            containers = await asyncio.to_thread(self._list_containers)
        except Exception as exc:  # noqa: BLE001 — отказ Docker — исход аккаунтов, не прогона
            self._docker_error = type(exc).__name__
            return
        self._running = {
            c["account_id"]: c["name"]
            for c in containers
            if c["status"] == "running" and isinstance(c["account_id"], int)
        }

    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply:
        await self._load()
        if self._docker_error is not None:
            return SourceReply(Outcome.UNREACHABLE, note=f"Docker недоступен: {self._docker_error}")
        name = self._running.get(row.id)
        if name is not None:
            return await self._ask(f"http://{name}:{self._manager.DEFAULT_PORT}", row.id)
        if not options.wake or options.dry_run:
            # D-06: под просмотром подъёма нет при любом флаге.
            return SourceReply(Outcome.UNREACHABLE, note="воркер не запущен")
        return await self._wake(row)

    async def _wake(self, row: AccountRow) -> SourceReply:
        """Условия подъёма (O-1 (а)): статус `active`, очередь прочитана и пуста, не работает.

        Любое неисполненное условие — «воркер недоступен» без подъёма. Сужение D-12
        по статусу действует только на этом пути: путь по умолчанию статус не смотрит.
        """
        if row.status != "active":
            return SourceReply(Outcome.UNREACHABLE, note="воркер не запущен; статус не active — не будится")
        try:
            length = await asyncio.to_thread(self._queue_len, row.id) if self._queue_len else None
        except Exception:  # noqa: BLE001 — очередь не прочитана: не будить
            length = None
        if length is None:
            return SourceReply(Outcome.UNREACHABLE, note="очередь не прочитана — не будится")
        if length != 0:
            return SourceReply(Outcome.UNREACHABLE, note="в очереди есть задачи — не будится")
        # Контейнер мог подняться чужими руками между списком и подъёмом: такой
        # опрашивается и не гасится никогда (D-16).
        endpoint = await asyncio.to_thread(self._running_now, row.id)
        if endpoint is not None:
            return await self._ask(endpoint, row.id)
        return await self._wake_and_ask(row)

    async def _wake_and_ask(self, row: AccountRow) -> SourceReply:
        """Подъём, ожидание, опрос; поднятый контейнер гасится в `finally` (D-16)."""
        started = False
        left = ""
        try:
            endpoint = await asyncio.to_thread(self._start, row.id)
            if endpoint is None:
                reply = SourceReply(Outcome.UNREACHABLE, note="подъём не удался")
            else:
                started = True
                timeout = WA_READY_TIMEOUT if self._kind == "wa" else MAX_READY_TIMEOUT
                ready = await asyncio.to_thread(self._wait_ready, row.id, timeout=timeout)
                if not ready:
                    reply = SourceReply(Outcome.UNREACHABLE, note="воркер поднят, но не ответил")
                elif self._kind == "wa":
                    reply = await self._ask(endpoint, row.id)
                else:
                    reply = await self._ask_until_connected(endpoint, row.id)
        finally:
            if started:
                left = await self._stop_if_idle(row.id)
        if left:
            note = f"{reply.note}; {left}" if reply.note else left
            reply = dataclasses.replace(reply, note=note)
        return reply

    async def _ask_until_connected(self, endpoint: str, account_id: int) -> SourceReply:
        """MAX после готовности `/health`: опрос `/status` до `connected: true`.

        HTTP поднимается сразу, а `connected` остаётся `false` до подключения сессии,
        поэтому «не подключён» — повод спросить снова. Счёт — по попыткам, без часов:
        пауза `MAX_POLL_INTERVAL` между попытками и ни одной после последней. Любой
        другой ответ (номер, «номера нет», «сессия мертва», отказ транспорта) заканчивает опрос.
        """
        for attempt in range(MAX_CONNECT_ATTEMPTS):
            reply = await self._ask(endpoint, account_id)
            if reply.outcome is not Outcome.UNREACHABLE or reply.note != NOTE_NOT_CONNECTED:
                return reply
            if attempt < MAX_CONNECT_ATTEMPTS - 1:
                await self._sleep(MAX_POLL_INTERVAL)
        return reply

    async def _stop_if_idle(self, account_id: int) -> str:
        """Погасить поднятый контейнер, если очередь всё ещё пуста; иначе — заметка, почему оставлен."""
        try:
            length = await asyncio.to_thread(self._queue_len, account_id) if self._queue_len else None
        except Exception:  # noqa: BLE001 — очередь не прочитана: не гасить
            length = None
        if length is None:
            return (
                "контейнер оставлен: очередь не прочитана, "
                "проверьте just wa-workers / just max-workers"
            )
        if length != 0:
            return "контейнер оставлен: в очереди появились задачи"
        try:
            await asyncio.to_thread(self._stop, account_id)
        except Exception as exc:  # noqa: BLE001 — отказ остановки не прячет ответ воркера
            return (
                f"контейнер оставлен: остановка не удалась ({type(exc).__name__}), "
                "проверьте just wa-workers / just max-workers"
            )
        return ""

    async def _ask(self, endpoint: str, account_id: int) -> SourceReply:
        """Один запрос `/status`; любой отказ — «воркер недоступен» без текста ответа."""
        try:
            async with httpx.AsyncClient(
                timeout=STATUS_TIMEOUT, transport=self._transport
            ) as client:
                response = await client.get(f"{endpoint}/api/sessions/{account_id}/status")
        except httpx.HTTPError as exc:
            return SourceReply(Outcome.UNREACHABLE, note=type(exc).__name__)
        if response.status_code != 200:
            return SourceReply(Outcome.UNREACHABLE, note=f"ответ {response.status_code}")
        try:
            body = response.json()
        except ValueError:
            return SourceReply(Outcome.UNREACHABLE, note="ответ не JSON")
        return classify_status(body)


def classify_status(body: object) -> SourceReply:
    """Тело `/status` -> ответ источника (таблица A6 исследования фазы).

    `connected` принимается только как настоящее `true`: строка `"true"` или
    число — это не подключение. Номер берётся лишь у подключённой сессии.
    """
    if not isinstance(body, dict):
        return SourceReply(Outcome.UNREACHABLE, note="ответ не объект")
    if body.get("connected") is not True:
        if body.get("exists") is False:
            return SourceReply(Outcome.DEAD_SESSION, note="сессии нет")
        return SourceReply(Outcome.UNREACHABLE, note=NOTE_NOT_CONNECTED)
    if "phone" not in body:
        return SourceReply(Outcome.NO_NUMBER, note="образ воркера без поля phone")
    reported = reported_phone_from_status(body)
    if reported is None:
        return SourceReply(Outcome.NO_NUMBER)
    return SourceReply(None, reported=reported)


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
