"""Дозаполнить номер существующих аккаунтов без номера из источника мессенджера.

ФОРМЫ ВЫЗОВА
    uv run python scripts/backfill_account_phones.py --dry-run
    uv run python scripts/backfill_account_phones.py --type wa --account-id <id>
    just backfill-phones --dry-run
    just prod-backfill-phones --dry-run --account-id <id>

ЗАПУСК БЕЗ ФЛАГОВ ПИШЕТ НОМЕРА В БАЗУ — в отличие от `collect_group_info.py` и
`recompress_attachments.py`, где запись включается флагом `--apply`. Здесь `--apply`
нет: посмотреть без записи — `--dry-run` (решение владельца D-08). Рецепты `just`
помечены `WRITES by default`, справка и первая строка вывода говорят то же.

Скрипт берёт аккаунты, у которых номер неизвестен и не указан вручную, опрашивает
по одному источник их мессенджера и записывает сообщённый номер ТОЛЬКО через
единого писателя Фазы 16 (`fill_reported_phone`), коммитя каждый аккаунт отдельно.
Повторный запуск идемпотентен и ручные номера не трогает.

ЧЕГО СКРИПТ НЕ ДЕЛАЕТ НИКОГДА. Статус аккаунта и прочие колонки он не меняет;
признак «указан вручную» не ставит; строку сессии назад в базу не пишет; не трогает
`phone.txt` и тома сессий; не переносит «номер из формы» MAX из `credentials`
(решения владельца O-2 (а), O-3 (а)). Номер в открытом виде не печатает — только
маской. Настройку журнала приложения не подключает: вывод идёт через `print` в
маскированной форме.

ИСТОЧНИКИ. WhatsApp и MAX: поле `phone` ответа `/status` работающего воркера аккаунта.
Остановленный воркер скрипт сам не поднимает; только с `--wake` — и тогда только
аккаунты в статусе `active` с пустой очередью, по одному, после опроса воркер гасится.
Telegram: короткое подключение изнутри процесса скрипта, строго по одному аккаунту,
занятые рассылкой пропускаются. Telegram опрашивается ТОЛЬКО из боевого контейнера
`web` — флаг `--telegram-from-container` передаёт рецепт `prod-backfill-phones`; без
него аккаунты Telegram получают исход «воркер недоступен», а клиент Telethon не
строится (иначе локальный `.env`, указывающий на боевую базу, открыл бы второй адрес
той же сессии).

ПРЕДУПРЕЖДЕНИЕ О `--wake`. Подъём воркера — это вход в WhatsApp / MAX с сохранённой
сессией. Если мессенджер ответит кодом 401 / 403 / 405, воркер САМ удалит файлы
сессии аккаунта. `--wake` несовместим с `--dry-run`: просмотр не поднимает контейнеры.

КОДЫ ВЫХОДА. 0 — прогон дошёл до конца (в том числе при исходах «номера нет»,
«воркер недоступен», «занят»); 1 — отказ базы или сборки источников, строка
`Прогон прерван: <имя класса>`; 2 — ошибка аргументов.

ПОРЯДОК ВЫКАТА (для владельца; в разработке не исполняется). Образ приложения → образы
воркеров WA и MAX → перезапуск работающих воркеров → `just prod-backfill-phones
--dry-run --account-id <id>` по одному аккаунту каждого типа → прогон с записью.
Запускать порциями (`--type`, `--account-id`, `--limit`). Скрипт попадает в боевой
`web` только после пересборки образа: код в контейнер не монтируется. После обрыва
прогона с `--wake` проверить `just wa-workers` и `just max-workers`: поднятый воркер
мог остаться запущенным.

НОМЕР, ВВЕДЁННЫЙ В ФОРМУ MAX, хранится как автоматический и скриптом не исправляется —
только ручной правкой (ревью 19, IN-03). Поручение о переносе `credentials` в
`16-CONTEXT.md` (D-01) и комментарий в `app/models/messenger_account.py` устарели
(O-3 (а)); в этой фазе они не правятся.
"""

import argparse
import asyncio
import collections
import dataclasses
import enum
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import redis
from sqlalchemy import select
from telethon import TelegramClient
from telethon import errors as telethon_errors
from telethon.sessions import StringSession

from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.config import get_settings
from app.database import get_engine, get_session_factory
from app.messengers.base import reported_phone_from_status
from app.messengers.telegram_user import reported_phone_of
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

# Пауза после каждого TG-аккаунта, у которого строился клиент: против FloodWait на
# длинных прогонах, не для защиты ключа авторизации (его защищает строгая очерёдность).
TELEGRAM_PAUSE = 1.0

# Признак «занят» (D-09): задача отправки TG-сообщения и её очередь — те же, что в
# `app/worker/celery_app.py` (`task_routes`); `account_id` — третий аргумент задачи
# (`send_telegram_message(self, ad_id, group_id, account_id, schedule_id)`). Расхождение
# с боевым путём ловят тесты `test_busy_probe_constants_match_the_send_task`.
SEND_TASK = "app.worker.tasks.send_telegram_message"
TELEGRAM_QUEUE = "telegram"
ACCOUNT_ARG_INDEX = 2

# Ожидание ответов воркеров на `inspect`, секунды (допущение A8 RESEARCH).
INSPECT_TIMEOUT = 2.0

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


def parse_session(credentials: object) -> StringSession | None:
    """Строка сессии Telethon без сети; `None` — сессии нет или она не разбирается.

    Пустая строка дала бы пустую сессию, и Telethon при подключении выпустил бы
    НОВЫЙ ключ авторизации — поэтому пустое и пробельное отсеивается здесь, до
    построения клиента. Разбор идёт без сети, так что любой его отказ — «строка
    негодна», а не сбой источника.
    """
    if not isinstance(credentials, str) or not credentials.strip():
        return None
    try:
        return StringSession(credentials)
    except Exception:  # noqa: BLE001 — разбор без сети: любой отказ значит «негодна»
        return None


class TelegramSource:
    """Источник номера Telegram: короткое подключение изнутри процесса скрипта.

    Клиент строится внедряемой фабрикой с `receive_updates=False`: интерактивный
    вход не вызывается, обновления не принимаются, строка сессии назад в базу не
    пишется. Порядок до сети: разбор строки сессии, наличие `api_id` / `api_hash`,
    признак «занят» (D-09, отказ в закрытую) — и только затем клиент. Параллельных
    подключений нет: аккаунты опрашивает цикл ядра по одному.
    """

    def __init__(self, *, api_id, api_hash, busy_probe, client_factory, pause=TELEGRAM_PAUSE):
        self._api_id = api_id
        self._api_hash = api_hash
        self._busy_probe = busy_probe
        self._client_factory = client_factory
        self._pause = pause

    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply:
        session = parse_session(row.credentials)
        if session is None:
            return SourceReply(Outcome.DEAD_SESSION, note="строка сессии пуста или не разбирается")
        if not self._api_id or not self._api_hash:
            return SourceReply(
                Outcome.UNREACHABLE, note="TELEGRAM_API_ID / TELEGRAM_API_HASH не заданы"
            )
        try:
            busy = await self._busy_probe(row.id)
        except Exception as exc:  # noqa: BLE001 — признак не определён: отказ в закрытую
            return SourceReply(
                Outcome.BUSY, note=f"статус рассылки не определён: {type(exc).__name__}"
            )
        if busy is None:
            return SourceReply(Outcome.BUSY, note="статус рассылки не определён")
        if busy:
            return SourceReply(Outcome.BUSY, note="идёт рассылка")
        client = self._client_factory(session, self._api_id, self._api_hash, receive_updates=False)
        try:
            await client.connect()
            if not await client.is_user_authorized():
                reply = SourceReply(Outcome.DEAD_SESSION, note="не авторизована")
            else:
                me = await client.get_me()
                if me is None:
                    reply = SourceReply(Outcome.DEAD_SESSION, note="не авторизована")
                else:
                    reported = reported_phone_of(me)
                    if reported is None:
                        reply = SourceReply(Outcome.NO_NUMBER)
                    else:
                        reply = SourceReply(None, reported=reported)
        except telethon_errors.AuthKeyError as exc:
            # В том числе AuthKeyDuplicatedError: сервер уже отозвал этот ключ (D-17).
            reply = SourceReply(Outcome.DEAD_SESSION, note=type(exc).__name__)
        except telethon_errors.UnauthorizedError as exc:
            reply = SourceReply(Outcome.DEAD_SESSION, note=type(exc).__name__)
        except (telethon_errors.FloodWaitError, OSError, TimeoutError) as exc:
            # У Telegram воркера нет: «источник недоступен». Текст исключения не кладётся.
            reply = SourceReply(Outcome.UNREACHABLE, note=type(exc).__name__)
        finally:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001 — отказ отключения исход не меняет
                pass
        if self._pause > 0:
            await asyncio.sleep(self._pause)
        return reply


def _account_of(args: object) -> int | None:
    """`account_id` из аргументов задачи отправки; `None` — аргументы нечитаемы."""
    if not isinstance(args, (list, tuple)) or len(args) <= ACCOUNT_ARG_INDEX:
        return None
    account = args[ACCOUNT_ARG_INDEX]
    if isinstance(account, bool) or not isinstance(account, int):
        return None
    return account


class TelegramBusyProbe:
    """Признак «TG-аккаунт занят рассылкой» (D-09): `True` / `False` / `None`.

    «Занят» — это задача отправки (`SEND_TASK`) аккаунта: выполняемая или
    предзагруженная воркером (снимок `inspect().active()` и `.reserved()`) либо ещё
    ждущая в списке Redis очереди `TELEGRAM_QUEUE`. Скрипт только читает: команды
    `inspect` и `LRANGE`; ничего не извлекает, не отзывает и не чистит.

    Отказ в закрытую: `None` («не определено», вызывающий считает аккаунт занятым)
    вместо `False` на любой неопределённости — нет ответа инспектора, не ответил ни
    один воркер очереди `telegram` (пустой снимок от `default` не доказывает
    «не занят»), отказ Redis, нечитаемое сообщение или аргументы задачи отправки.
    Цена ошибки «не занят» необратима (ключ авторизации), цена «занят» — повторный
    прогон. `timeout` — ожидание ответов воркеров; боевая фабрика инспектора
    (план 20-06) строит `inspect(timeout=...)` с ним.
    """

    def __init__(self, *, inspector_factory, redis_client, timeout: float = INSPECT_TIMEOUT):
        self._inspector_factory = inspector_factory
        self._redis = redis_client
        self.timeout = timeout
        # Состав воркеров очереди `telegram` — один раз за прогон; снимок задач — на каждый аккаунт.
        self._telegram_workers: list[str] | None = None

    async def __call__(self, account_id: int) -> bool | None:
        return await asyncio.to_thread(self._check, account_id)

    def _queue_workers(self, inspector) -> list[str] | None:
        if self._telegram_workers is None:
            queues = inspector.active_queues()
            if not isinstance(queues, dict) or not queues:
                return None
            workers = [
                worker
                for worker, consumed in queues.items()
                if any(
                    isinstance(queue, dict) and queue.get("name") == TELEGRAM_QUEUE
                    for queue in consumed
                )
            ]
            if not workers:
                return None
            self._telegram_workers = workers
        return self._telegram_workers

    def _check(self, account_id: int) -> bool | None:
        try:
            inspector = self._inspector_factory()
            workers = self._queue_workers(inspector)
            if workers is None:
                return None
            active = inspector.active()
            reserved = inspector.reserved()
            if not isinstance(active, dict) or not isinstance(reserved, dict):
                return None
            if any(worker not in active or worker not in reserved for worker in workers):
                return None
            unknown = False
            for snapshot in (active, reserved):
                for tasks in snapshot.values():
                    for task in tasks:
                        if task.get("name") != SEND_TASK:
                            continue
                        owner = _account_of(task.get("args"))
                        if owner is None:
                            unknown = True
                        elif owner == account_id:
                            return True
            for item in self._redis.lrange(TELEGRAM_QUEUE, 0, -1):
                try:
                    headers = json.loads(item)["headers"]
                    if headers.get("task") != SEND_TASK:
                        continue
                    owner = _account_of(json.loads(headers["argsrepr"]))
                except Exception:  # noqa: BLE001 — сообщение нечитаемо: чьё оно, неизвестно
                    unknown = True
                    continue
                if owner is None:
                    unknown = True
                elif owner == account_id:
                    return True
            return None if unknown else False
        except Exception:  # noqa: BLE001 — любая неопределённость значит «занят» (D-09)
            return None


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Дозаполнить номера аккаунтов без номера. ЗАПУСК БЕЗ ФЛАГОВ ПИШЕТ В БАЗУ; "
            "посмотреть без записи — --dry-run."
        ),
        epilog=(
            "Порядок: сначала --dry-run --account-id по одному аккаунту каждого типа, "
            "затем запись порциями (--type, --account-id, --limit). После обрыва "
            "прогона с --wake проверьте `just wa-workers` и `just max-workers`."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "только показать, что было бы записано: ничего не пишет и не поднимает "
            "контейнеры; Telegram и работающие воркеры опрашиваются"
        ),
    )
    parser.add_argument(
        "--wake",
        action="store_true",
        help=(
            "поднять остановленные воркеры WA/MAX аккаунтов active с пустой очередью "
            "по одному, опросить и погасить; это вход в WhatsApp/MAX: воркер сам удалит "
            "файлы сессии, если мессенджер ответит 401/403/405; несовместим с --dry-run"
        ),
    )
    parser.add_argument(
        "--type",
        action="append",
        dest="kinds",
        choices=KINDS,
        help="только этот тип аккаунтов; флаг можно повторять",
    )
    parser.add_argument("--account-id", type=int, help="только аккаунт с этим id")
    parser.add_argument(
        "--limit", type=int, help="не больше стольких аккаунтов (после фильтров, по возрастанию id)"
    )
    parser.add_argument(
        "--telegram-from-container",
        action="store_true",
        help=(
            "опрашивать Telegram: флаг передаёт рецепт prod-backfill-phones изнутри "
            "боевого контейнера web; без него аккаунты Telegram не опрашиваются"
        ),
    )
    return parser


def options_from(args: argparse.Namespace) -> RunOptions:
    return RunOptions(
        dry_run=args.dry_run,
        kinds=tuple(args.kinds) if args.kinds else KINDS,
        account_id=args.account_id,
        limit=args.limit,
        wake=args.wake,
    )


class TelegramOutsideContainerSource:
    """Источник Telegram вне боевого контейнера: не опрашивает и клиента не строит.

    Локальный `.env`, указывающий на боевую базу, иначе дал бы второй адрес той же
    сессии (допущение A1 исследования): боевой путь открывает только
    `prod-backfill-phones`, который передаёт `--telegram-from-container`.
    """

    async def poll(self, row: AccountRow, options: RunOptions) -> SourceReply:
        return SourceReply(
            Outcome.UNREACHABLE,
            note="Telegram опрашивается только из боевого контейнера: just prod-backfill-phones",
        )


def build_sources(settings, *, telegram_from_container: bool) -> dict[str, AccountSource]:
    """Боевые источники по типам; сборка ни к чему не подключается.

    Клиент Redis ленив — соединение открывается при первом запросе. Приложение
    Celery ввозится ТОЛЬКО на пути Telegram и внутри функции: его создание читает
    настройки, а `--help` и ввоз скрипта тестами не должны требовать `.env`.
    """
    redis_client = redis.from_url(settings.redis_url)
    sources: dict[str, AccountSource] = {
        "wa": WorkerStatusSource(
            "wa", queue_len=lambda account_id: redis_client.llen(queue_key("wa", account_id))
        ),
        "max": WorkerStatusSource(
            "max", queue_len=lambda account_id: redis_client.llen(queue_key("max", account_id))
        ),
    }
    if telegram_from_container:
        from app.worker.celery_app import celery

        sources["tg_user"] = TelegramSource(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
            busy_probe=TelegramBusyProbe(
                inspector_factory=lambda: celery.control.inspect(timeout=INSPECT_TIMEOUT),
                redis_client=redis_client,
            ),
            client_factory=TelegramClient,
        )
    else:
        sources["tg_user"] = TelegramOutsideContainerSource()
    return sources


async def amain(argv: list[str] | None = None, *, session_factory=None, sources=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Отказы аргументов — ДО любой работы: ни базы, ни источников, ни вывода (код 2).
    if args.wake and args.dry_run:
        parser.error("--wake несовместим с --dry-run: просмотр не поднимает контейнеры")
    if args.account_id is not None and args.account_id <= 0:
        parser.error("--account-id должен быть положительным целым")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit должен быть положительным целым")
    options = options_from(args)

    engine = None
    try:
        if session_factory is None:
            engine = get_engine(get_settings().database_url)
            session_factory = get_session_factory(engine)
        if sources is None:
            sources = build_sources(
                get_settings(), telegram_from_container=args.telegram_from_container
            )
        await run(session_factory, options, sources)
    except Exception as exc:  # noqa: BLE001 — только имя класса: текст может нести секрет
        print(f"Прогон прерван: {type(exc).__name__}")
        return 1
    finally:
        if engine is not None:
            await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
