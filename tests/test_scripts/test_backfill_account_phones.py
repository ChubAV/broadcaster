"""Скрипт дозаполнения номеров существующих аккаунтов (Фаза 20, PHONE-17, PHONE-18).

Проверяется ЯДРО скрипта `run(...)`, а не боевой прогон: источник номера — двойник,
записи в базе — настоящая файловая SQLite. База файловая, а не `:memory:`, потому
что ядро открывает отдельную сессию на каждый аккаунт, а у базы в памяти каждое
соединение получает свою; по той же причине вторая независимая сессия (ручной
номер, введённый во время опроса) возможна только на файле.

Доказательство ДЕЙСТВИЯ — журналы двойников (`RecordingSource.calls`, журнал
считающей обёртки писателя) и строки базы, прочитанные новой сессией, а не счётчики
отчёта: счётчик совпал бы и при записи, и при отказе от неё.

Тест не касается ни Docker, ни Telegram, ни сети, ни настоящей базы приложения.
"""

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from docker.errors import DockerException
from telethon import errors as telethon_errors
from telethon.crypto import AuthKey
from telethon.sessions import StringSession
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import backfill_account_phones as script  # noqa: E402

from app.database import Base  # noqa: E402
from app.models.messenger_account import MessengerAccount  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import max_container_manager, wa_container_manager  # noqa: E402
from tests.account_label_support import seed_account  # noqa: E402

REPORTED = "79991234567"
STORED = "+79991234567"
MASKED = "+7 *** ***-**-67"


@pytest_asyncio.fixture
async def factory(tmp_path):
    """Фабрика НЕЗАВИСИМЫХ сессий поверх ОДНОЙ файловой базы."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'backfill.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _seed_user(factory) -> int:
    async with factory() as session:
        user = User(email="backfill@t.com", password_hash="h", name="T")
        session.add(user)
        await session.commit()
        return user.id


async def _seed(factory, user_id: int, kind: str, **kw) -> int:
    async with factory() as session:
        return await seed_account(session, user_id, kind, **kw)


async def _columns(factory, account_id: int) -> tuple:
    async with factory() as session:
        result = await session.execute(
            select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
                MessengerAccount.id == account_id
            )
        )
        return tuple(result.one())


async def _snapshot(factory) -> list[tuple]:
    """Все строки аккаунтов: всё, что скрипту не позволено менять, плюс номер."""
    async with factory() as session:
        result = await session.execute(
            select(
                MessengerAccount.id,
                MessengerAccount.type,
                MessengerAccount.user_id,
                MessengerAccount.status,
                MessengerAccount.credentials,
                MessengerAccount.phone,
                MessengerAccount.phone_is_manual,
            ).order_by(MessengerAccount.id)
        )
        return [tuple(row) for row in result.all()]


class RecordingSource:
    """Двойник источника: ответы по id, ответ по умолчанию, журнал опросов.

    `before_reply(row)` — необязательный асинхронный крюк: выполняется после
    того, как опрос зафиксирован в журнале, и до ответа (здесь тест вклинивает
    вторую сессию, пока «источник думает»).
    """

    def __init__(self, replies=None, default=None, before_reply=None):
        self.replies = dict(replies or {})
        self.default = default or script.SourceReply(outcome=None, reported=REPORTED)
        self.before_reply = before_reply
        self.calls: list[int] = []

    async def poll(self, row, options):
        self.calls.append(row.id)
        if self.before_reply is not None:
            await self.before_reply(row)
        reply = self.replies.get(row.id, self.default)
        if isinstance(reply, BaseException):
            raise reply
        return reply


# --- трасер: значение источника -> писатель -> коммит -> маска -> итог ---------


@pytest.mark.asyncio
async def test_tracer_a_reported_number_is_written_committed_and_printed_masked(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")
    source = RecordingSource(
        {account_id: script.SourceReply(outcome=None, reported=REPORTED)}
    )

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert await _columns(factory, account_id) == (STORED, False), (
        "номер не записан писателем Фазы 16"
    )
    assert summary.counts[script.Outcome.FILLED] == 1
    assert source.calls == [account_id]
    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("РЕЖИМ ЗАПИСИ")
    assert f"#{account_id} wa: заполнено {MASKED}" in out
    assert "  заполнено: 1" in out
    assert "Всего: 1" in out


# --- критерии 1-2 и D-06 -------------------------------------------------------


def _count_writer(monkeypatch) -> list[int]:
    """Считающая обёртка писателя в ядре скрипта: журнал `account_id` вызовов (D-06).

    Настоящий писатель берётся ДО подмены и вызывается внутри обёртки, поэтому
    прогон записи с обёрткой ведёт себя как без неё. Ноль вызовов в просмотре
    значит что-то лишь рядом с положительным контролем — прогоном записи с той
    же обёрткой, где вызов на каждый аккаунт обязан появиться. Помощник
    переиспользует план 20-07, определять его заново нельзя.
    """
    calls: list[int] = []
    real = script.fill_reported_phone

    async def counting(session, account_id, raw):
        calls.append(account_id)
        return await real(session, account_id, raw)

    monkeypatch.setattr(script, "fill_reported_phone", counting)
    return calls


@pytest.mark.asyncio
async def test_selection_skips_manual_and_filled_and_ignores_status(factory):
    user_id = await _seed_user(factory)
    ids = [
        await _seed(factory, user_id, "wa", status=status)
        for status in ("active", "disconnected", "sync_failed", "connecting")
    ]
    filled = await _seed(factory, user_id, "wa", phone="79990000001")
    manual = await _seed(factory, user_id, "wa", manual_phone="+7 999 000-00-02")
    # Признак «вручную» при пустом номере: ограничение таблицы такую строку не
    # допускает, поэтому она строится в обход него. Условие выборки на признак
    # отдельно от условия на номер, и без этой строки его удаление осталось бы
    # незамеченным: номер у ручного аккаунта и так не пуст.
    flag_only = await _seed(factory, user_id, "wa")
    async with factory() as session:
        await session.execute(text("PRAGMA ignore_check_constraints = ON"))
        try:
            await session.execute(
                text("UPDATE messenger_accounts SET phone_is_manual = 1 WHERE id = :id"),
                {"id": flag_only},
            )
            await session.commit()
        finally:
            # Запрет `10-55#9`: `rollback()` первой строкой `finally`, иначе отказ
            # посева маскируется `PendingRollbackError`-ом.
            await session.rollback()
            await session.execute(text("PRAGMA ignore_check_constraints = OFF"))
    assert await _columns(factory, flag_only) == (None, True)
    watched = (filled, manual, flag_only)
    before = {i: await _columns(factory, i) for i in watched}
    source = RecordingSource()

    await script.run(factory, script.RunOptions(), {"wa": source})

    assert source.calls == sorted(ids)
    assert {i: await _columns(factory, i) for i in watched} == before
    for account_id in ids:
        assert await _columns(factory, account_id) == (STORED, False)


@pytest.mark.asyncio
async def test_selection_filters_by_kind_account_and_limit(factory):
    user_id = await _seed_user(factory)
    wa_1 = await _seed(factory, user_id, "wa")
    tg_1 = await _seed(factory, user_id, "tg_user")
    wa_2 = await _seed(factory, user_id, "wa")
    max_1 = await _seed(factory, user_id, "max")
    wa_3 = await _seed(factory, user_id, "wa")

    def every(source):
        return {"wa": source, "tg_user": source, "max": source}

    only_wa = RecordingSource()
    await script.run(factory, script.RunOptions(kinds=("wa",), dry_run=True), every(only_wa))
    assert only_wa.calls == [wa_1, wa_2, wa_3]

    one = RecordingSource()
    await script.run(factory, script.RunOptions(account_id=max_1, dry_run=True), every(one))
    assert one.calls == [max_1]

    limited = RecordingSource()
    await script.run(factory, script.RunOptions(limit=2, dry_run=True), every(limited))
    assert limited.calls == [wa_1, tg_1]

    limited_wa = RecordingSource()
    await script.run(
        factory, script.RunOptions(kinds=("wa",), limit=2, dry_run=True), every(limited_wa)
    )
    assert limited_wa.calls == [wa_1, wa_2]

    no_source = RecordingSource()
    await script.run(factory, script.RunOptions(dry_run=True), {"wa": no_source})
    assert no_source.calls == [wa_1, wa_2, wa_3]


@pytest.mark.asyncio
async def test_status_unchanged_by_any_outcome(factory):
    user_id = await _seed_user(factory)
    statuses = ("active", "disconnected", "sync_failed", "connecting", "active", "disconnected")
    ids = [await _seed(factory, user_id, "wa", status=s) for s in statuses]
    outcomes = script.Outcome
    replies = {
        ids[0]: script.SourceReply(outcome=None, reported=REPORTED),
        ids[1]: script.SourceReply(outcome=outcomes.NO_NUMBER),
        ids[2]: script.SourceReply(outcome=outcomes.DEAD_SESSION),
        ids[3]: script.SourceReply(outcome=outcomes.UNREACHABLE),
        ids[4]: script.SourceReply(outcome=outcomes.BUSY),
        ids[5]: RuntimeError("boom"),
    }
    before = await _snapshot(factory)

    await script.run(factory, script.RunOptions(), {"wa": RecordingSource(replies)})

    after = await _snapshot(factory)
    assert [r[:5] for r in after] == [r[:5] for r in before]
    assert [r[5] for r in after] == [STORED, None, None, None, None, None]
    assert all(r[6] is False for r in after)


@pytest.mark.asyncio
async def test_idempotent_second_run_changes_nothing(factory, capsys):
    user_id = await _seed_user(factory)
    ids = [await _seed(factory, user_id, "wa") for _ in range(2)]
    source = RecordingSource()
    await script.run(factory, script.RunOptions(), {"wa": source})
    assert source.calls == ids
    after_first = await _snapshot(factory)
    capsys.readouterr()
    source.calls.clear()

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert source.calls == []
    assert await _snapshot(factory) == after_first
    assert "Всего: 0" in capsys.readouterr().out
    assert sum(summary.counts.values()) == 0


@pytest.mark.asyncio
async def test_manual_entered_during_the_run_is_kept(factory):
    from app.application.accounts.phone import set_manual_phone

    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")

    async def owner_types_a_number(row):
        async with factory() as other:
            await set_manual_phone(other, row.id, "+7 999 000-11-22")
            await other.commit()

    source = RecordingSource(before_reply=owner_types_a_number)

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert await _columns(factory, account_id) == ("+79990001122", True)
    assert summary.counts[script.Outcome.KEPT] == 1
    assert summary.counts[script.Outcome.FILLED] == 0


@pytest.mark.asyncio
async def test_account_deleted_during_the_run_is_counted_gone(factory):
    from sqlalchemy import delete

    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")

    async def account_is_removed(row):
        async with factory() as other:
            await other.execute(delete(MessengerAccount).where(MessengerAccount.id == row.id))
            await other.commit()

    source = RecordingSource(before_reply=account_is_removed)

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert account_id in source.calls
    assert summary.counts[script.Outcome.ACCOUNT_GONE] == 1
    assert summary.counts[script.Outcome.KEPT] == 0
    assert await _snapshot(factory) == []


@pytest.mark.asyncio
async def test_one_failing_account_does_not_stop_or_undo_the_run(factory, capsys):
    user_id = await _seed_user(factory)
    first, second, third = [await _seed(factory, user_id, "wa") for _ in range(3)]
    source = RecordingSource({second: RuntimeError("secret detail 79991234567")})

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert await _columns(factory, first) == (STORED, False)
    assert await _columns(factory, second) == (None, False)
    assert await _columns(factory, third) == (STORED, False)
    assert summary.counts[script.Outcome.FAILED] == 1
    assert summary.counts[script.Outcome.FILLED] == 2
    out = capsys.readouterr().out
    assert f"#{second} wa: сбой по аккаунту (RuntimeError)" in out
    assert "secret detail" not in out
    assert REPORTED not in out


@pytest.mark.asyncio
async def test_one_failing_account_in_the_writer_does_not_stop_or_undo_the_run(
    factory, monkeypatch
):
    user_id = await _seed_user(factory)
    first, second, third = [await _seed(factory, user_id, "wa") for _ in range(3)]
    real = script.fill_reported_phone

    async def failing_on_second(session, account_id, raw):
        if account_id == second:
            raise ValueError("writer broke")
        return await real(session, account_id, raw)

    monkeypatch.setattr(script, "fill_reported_phone", failing_on_second)

    summary = await script.run(factory, script.RunOptions(), {"wa": RecordingSource()})

    assert await _columns(factory, first) == (STORED, False)
    assert await _columns(factory, second) == (None, False)
    assert await _columns(factory, third) == (STORED, False)
    assert summary.counts[script.Outcome.FAILED] == 1
    assert summary.counts[script.Outcome.FILLED] == 2


@pytest.mark.asyncio
async def test_one_failing_account_cancellation_is_not_swallowed_and_keeps_written(factory):
    import asyncio

    user_id = await _seed_user(factory)
    first, second = [await _seed(factory, user_id, "wa") for _ in range(2)]
    source = RecordingSource({second: asyncio.CancelledError()})

    with pytest.raises(asyncio.CancelledError):
        await script.run(factory, script.RunOptions(), {"wa": source})

    assert await _columns(factory, first) == (STORED, False)
    assert await _columns(factory, second) == (None, False)


@pytest.mark.asyncio
async def test_a_source_claiming_the_core_outcome_filled_is_a_failed_account(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")
    source = RecordingSource({account_id: script.SourceReply(outcome=script.Outcome.FILLED)})

    summary = await script.run(factory, script.RunOptions(), {"wa": source})

    assert summary.counts[script.Outcome.FAILED] == 1
    assert await _columns(factory, account_id) == (None, False)
    assert f"#{account_id} wa: сбой по аккаунту (InvalidSourceReply)" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_dry_run_never_calls_the_writer(factory, monkeypatch, capsys):
    user_id = await _seed_user(factory)
    ids = [await _seed(factory, user_id, "wa") for _ in range(3)]
    source = RecordingSource()
    calls = _count_writer(monkeypatch)
    before = await _snapshot(factory)

    summary = await script.run(factory, script.RunOptions(dry_run=True), {"wa": source})

    assert calls == [], "просмотр вызвал писатель Фазы 16"
    assert source.calls == ids
    assert await _snapshot(factory) == before
    assert summary.counts[script.Outcome.FILLED] == 3
    out = capsys.readouterr().out
    for account_id in ids:
        assert f"#{account_id} wa: было бы заполнено {MASKED}" in out

    # Положительный контроль обёртки: тот же прогон без просмотра обязан её вызвать.
    await script.run(factory, script.RunOptions(), {"wa": source})
    assert calls == ids
    for account_id in ids:
        assert await _columns(factory, account_id) == (STORED, False)


# --- источник WA / MAX: Docker только читается, номер — собственный запрос /status ---


@pytest.fixture(autouse=True)
def _no_real_docker(monkeypatch):
    """Страж: тест не трогает настоящий Docker (T-20-06).

    Клиент Docker обоих менеджеров подменён заглушкой, пишущей в журнал и
    поднимающей `RuntimeError`. Источник ловит отказ списка контейнеров, поэтому
    обращение к настоящему Docker могло бы пройти незамеченным внутри источника:
    потому утверждение стоит на разборке и краснеет самостоятельно.
    """
    journal: list[str] = []

    def forbidden():
        journal.append("docker.from_env")
        raise RuntimeError("настоящий Docker в тесте запрещён")

    monkeypatch.setattr(wa_container_manager, "_get_docker_client", forbidden)
    monkeypatch.setattr(max_container_manager, "_get_docker_client", forbidden)
    yield journal
    assert not journal, "тест обратился к настоящему Docker"


def _container(kind: str, account_id: int, status: str = "running") -> dict:
    return {
        "account_id": account_id,
        "name": f"{kind}-worker-{account_id}",
        "status": status,
        "short_id": "s",
    }


def _listing(containers, journal=None):
    """Двойник `list_worker_containers`: отдаёт список, считает вызовы."""

    def list_containers():
        if journal is not None:
            journal.append("list")
        if isinstance(containers, BaseException):
            raise containers
        return list(containers)

    return list_containers


def _status_url(kind: str, account_id: int) -> str:
    return f"http://{kind}-worker-{account_id}:3000/api/sessions/{account_id}/status"


def _status_transport(responses, journal):
    """`httpx.MockTransport`: по адресу — заданный ответ или исключение транспорта.

    Значение: `dict` — тело JSON с кодом 200; `Exception` — поднимается как отказ
    транспорта; `(код, байты)` — ответ как есть. Адрес вне таблицы — ошибка теста.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        journal.append(url)
        spec = responses[url]
        if isinstance(spec, BaseException):
            raise spec
        if isinstance(spec, tuple):
            status, content = spec
            return httpx.Response(status, content=content)
        return httpx.Response(200, json=spec)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_tracer_running_worker_status_fills_the_number(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")
    requests: list[str] = []
    transport = _status_transport(
        {
            _status_url("wa", account_id): {
                "connected": True,
                "exists": True,
                "syncState": "ready",
                "phone": REPORTED,
            }
        },
        requests,
    )
    source = script.WorkerStatusSource(
        "wa", list_containers=_listing([_container("wa", account_id)]), transport=transport
    )

    await script.run(factory, script.RunOptions(), {"wa": source})

    assert await _columns(factory, account_id) == (STORED, False), (
        "номер работающего воркера не записан"
    )
    assert requests == [_status_url("wa", account_id)]
    assert f"#{account_id} wa: заполнено {MASKED}" in capsys.readouterr().out


# --- таблица A6 для WA и MAX, край precision, отказы транспорта -----------------

WORKER_KINDS = pytest.mark.parametrize("kind", ["wa", "max"])


async def _poll_one_running(factory, kind: str, spec):
    """Один аккаунт `kind` с работающим контейнером; воркер отвечает `spec`.

    Возвращает `(id, колонки, итог, журнал запросов)` — всё читается из базы и
    вывода, а не из внутренностей источника.
    """
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind)
    requests: list[str] = []
    transport = _status_transport({_status_url(kind, account_id): spec}, requests)
    source = script.WorkerStatusSource(
        kind, list_containers=_listing([_container(kind, account_id)]), transport=transport
    )
    summary = await script.run(factory, script.RunOptions(), {kind: source})
    return account_id, await _columns(factory, account_id), summary, requests


def _line(out: str, account_id: int, kind: str) -> str:
    return next(ln for ln in out.splitlines() if ln.startswith(f"#{account_id} {kind}:"))


STATUS_TABLE = [
    pytest.param([], script.Outcome.UNREACHABLE, "ответ не объект", id="not-an-object"),
    pytest.param(
        {"connected": False, "exists": False},
        script.Outcome.DEAD_SESSION,
        "сессии нет",
        id="dead-session",
    ),
    pytest.param(
        {"connected": False, "exists": True},
        script.Outcome.UNREACHABLE,
        "не подключён",
        id="not-connected",
    ),
    pytest.param(
        {"connected": "true", "exists": True, "phone": REPORTED},
        script.Outcome.UNREACHABLE,
        "не подключён",
        id="string-true-is-not-connected",
    ),
    pytest.param(
        {"connected": True, "exists": True},
        script.Outcome.NO_NUMBER,
        "образ воркера без поля phone",
        id="old-image-without-phone-field",
    ),
    pytest.param(
        {"connected": True, "exists": True, "phone": None},
        script.Outcome.NO_NUMBER,
        "",
        id="phone-null",
    ),
    pytest.param(
        {"connected": True, "exists": True, "phone": ""},
        script.Outcome.NO_NUMBER,
        "",
        id="phone-empty",
    ),
    pytest.param(
        {"connected": True, "exists": True, "phone": "мусор"},
        script.Outcome.NO_NUMBER,
        "",
        id="phone-unparseable",
    ),
    pytest.param(
        {"connected": True, "exists": True, "phone": REPORTED},
        script.Outcome.FILLED,
        "",
        id="phone-good",
    ),
]


@WORKER_KINDS
@pytest.mark.parametrize(("body", "outcome", "note"), STATUS_TABLE)
@pytest.mark.asyncio
async def test_classify_status_table(factory, capsys, kind, body, outcome, note):
    account_id, columns, summary, requests = await _poll_one_running(factory, kind, body)

    out = capsys.readouterr().out
    assert summary.counts[outcome] == 1, (
        f"исход {outcome.value} не получен: {_line(out, account_id, kind)}"
    )
    assert sum(summary.counts.values()) == 1
    if outcome is script.Outcome.FILLED:
        assert columns == (STORED, False)
        assert _line(out, account_id, kind) == f"#{account_id} {kind}: заполнено {MASKED}"
    else:
        assert columns == (None, False)
        suffix = f" ({note})" if note else ""
        assert _line(out, account_id, kind) == f"#{account_id} {kind}: {outcome.value}{suffix}"
    assert len(requests) == 1


PRECISION = [
    pytest.param(79991234567, STORED, script.Outcome.FILLED, id="integer-is-exact"),
    pytest.param(79991234567.0, None, script.Outcome.NO_NUMBER, id="float-is-no-number"),
    pytest.param(True, None, script.Outcome.NO_NUMBER, id="bool-is-no-number"),
]


@WORKER_KINDS
@pytest.mark.parametrize(("value", "stored", "outcome"), PRECISION)
@pytest.mark.asyncio
async def test_classify_status_precision_of_the_phone_field(factory, kind, value, stored, outcome):
    """Край precision PHONE-19: целое из JSON пишется точно, дробное и `true` — не номер."""
    body = {"connected": True, "exists": True, "phone": value}

    _, columns, summary, _ = await _poll_one_running(factory, kind, body)

    assert columns == (stored, False)
    assert summary.counts[outcome] == 1


SECRET = "secret-79991234567"

TRANSPORT_FAILURES = [
    pytest.param(httpx.ConnectError(SECRET), "ConnectError", id="connect-error"),
    pytest.param(httpx.ReadTimeout(SECRET), "ReadTimeout", id="read-timeout"),
    pytest.param((503, SECRET.encode()), "ответ 503", id="status-503"),
    pytest.param((200, f"не json {SECRET}".encode()), "ответ не JSON", id="body-not-json"),
]


@WORKER_KINDS
@pytest.mark.parametrize(("spec", "note"), TRANSPORT_FAILURES)
@pytest.mark.asyncio
async def test_classify_status_transport_failures_are_unreachable(
    factory, capsys, kind, spec, note
):
    account_id, columns, summary, _ = await _poll_one_running(factory, kind, spec)

    out = capsys.readouterr().out
    assert summary.counts[script.Outcome.UNREACHABLE] == 1
    assert columns == (None, False)
    assert _line(out, account_id, kind) == f"#{account_id} {kind}: воркер недоступен ({note})"
    assert SECRET not in out, "в вывод попал текст исключения или тело ответа воркера"
    assert "79991234567" not in out


# --- путь по умолчанию не будит воркеры ---------------------------------------

NO_NUMBER_BODY = {"connected": True, "exists": True, "phone": None}
GOOD_BODY = {"connected": True, "exists": True, "phone": REPORTED}


def _patch_wake_paths():
    """Четыре пути подъёма контейнера: менеджеры обоих типов и помощники адаптеров."""
    return [
        patch("app.services.wa_container_manager.start_container"),
        patch("app.services.max_container_manager.start_container"),
        patch("app.messengers.whatsapp.ensure_wa_container"),
        patch("app.messengers.max.ensure_max_container"),
    ]


@pytest.mark.asyncio
async def test_default_polls_only_running_workers(factory, capsys):
    user_id = await _seed_user(factory)
    running = await _seed(factory, user_id, "wa")
    exited = await _seed(factory, user_id, "wa")
    no_container = await _seed(factory, user_id, "wa")
    restarting = await _seed(factory, user_id, "max")
    requests: list[str] = []
    transport = _status_transport({_status_url("wa", running): NO_NUMBER_BODY}, requests)
    sources = {
        "wa": script.WorkerStatusSource(
            "wa",
            list_containers=_listing(
                [_container("wa", running), _container("wa", exited, "exited")]
            ),
            transport=transport,
        ),
        "max": script.WorkerStatusSource(
            "max",
            list_containers=_listing([_container("max", restarting, "restarting")]),
            transport=transport,
        ),
    }

    await script.run(factory, script.RunOptions(), sources)

    assert requests == [_status_url("wa", running)], "опрошен не только работающий воркер"
    out = capsys.readouterr().out
    assert f"#{running} wa: номера нет" in out
    for account_id, kind in ((exited, "wa"), (no_container, "wa"), (restarting, "max")):
        assert _line(out, account_id, kind) == (
            f"#{account_id} {kind}: воркер недоступен (воркер не запущен)"
        )


@pytest.mark.asyncio
async def test_docker_listing_is_read_once_per_kind(factory):
    user_id = await _seed_user(factory)
    wa_ids = [await _seed(factory, user_id, "wa") for _ in range(3)]
    max_ids = [await _seed(factory, user_id, "max") for _ in range(2)]
    requests: list[str] = []
    responses = {_status_url("wa", i): NO_NUMBER_BODY for i in wa_ids}
    responses.update({_status_url("max", i): NO_NUMBER_BODY for i in max_ids})
    transport = _status_transport(responses, requests)
    wa_listing: list[str] = []
    max_listing: list[str] = []
    sources = {
        "wa": script.WorkerStatusSource(
            "wa",
            list_containers=_listing([_container("wa", i) for i in wa_ids], wa_listing),
            transport=transport,
        ),
        "max": script.WorkerStatusSource(
            "max",
            list_containers=_listing([_container("max", i) for i in max_ids], max_listing),
            transport=transport,
        ),
    }

    await script.run(factory, script.RunOptions(), sources)

    assert len(requests) == 5
    assert wa_listing == ["list"], "список контейнеров wa прочитан не один раз"
    assert max_listing == ["list"], "список контейнеров max прочитан не один раз"


@pytest.mark.asyncio
async def test_docker_unavailable_is_a_per_account_outcome(factory, capsys):
    user_id = await _seed_user(factory)
    wa_ids = [await _seed(factory, user_id, "wa") for _ in range(2)]
    max_id = await _seed(factory, user_id, "max")
    requests: list[str] = []
    transport = _status_transport({_status_url("max", max_id): GOOD_BODY}, requests)
    sources = {
        "wa": script.WorkerStatusSource(
            "wa",
            list_containers=_listing(DockerException("secret-79991234567")),
            transport=transport,
        ),
        "max": script.WorkerStatusSource(
            "max", list_containers=_listing([_container("max", max_id)]), transport=transport
        ),
    }

    summary = await script.run(factory, script.RunOptions(), sources)

    out = capsys.readouterr().out
    for account_id in wa_ids:
        assert _line(out, account_id, "wa") == (
            f"#{account_id} wa: воркер недоступен (Docker недоступен: DockerException)"
        )
        assert await _columns(factory, account_id) == (None, False)
    assert summary.counts[script.Outcome.UNREACHABLE] == 2
    assert summary.counts[script.Outcome.FILLED] == 1
    assert await _columns(factory, max_id) == (STORED, False)
    assert "secret-79991234567" not in out
    assert requests == [_status_url("max", max_id)]


@pytest.mark.asyncio
async def test_never_wakes_through_adapters(factory):
    user_id = await _seed_user(factory)
    wa_running = await _seed(factory, user_id, "wa")
    wa_stopped = await _seed(factory, user_id, "wa")
    max_running = await _seed(factory, user_id, "max")
    max_stopped = await _seed(factory, user_id, "max")
    requests: list[str] = []
    transport = _status_transport(
        {_status_url("wa", wa_running): GOOD_BODY, _status_url("max", max_running): GOOD_BODY},
        requests,
    )

    def sources():
        return {
            "wa": script.WorkerStatusSource(
                "wa",
                list_containers=_listing(
                    [_container("wa", wa_running), _container("wa", wa_stopped, "exited")]
                ),
                transport=transport,
            ),
            "max": script.WorkerStatusSource(
                "max",
                list_containers=_listing(
                    [_container("max", max_running), _container("max", max_stopped, "created")]
                ),
                transport=transport,
            ),
        }

    patches = _patch_wake_paths()
    mocks = [p.start() for p in patches]
    try:
        # Просмотр идёт первым: он ничего не пишет, и оба прогона видят тех же кандидатов.
        await script.run(factory, script.RunOptions(dry_run=True), sources())
        await script.run(factory, script.RunOptions(), sources())
    finally:
        for p in patches:
            p.stop()

    assert len(requests) == 4, "оба прогона обязаны опросить оба работающих воркера"
    wa_start, max_start, wa_ensure, max_ensure = mocks
    wa_start.assert_not_called()
    max_start.assert_not_called()
    wa_ensure.assert_not_called()
    max_ensure.assert_not_called()


@pytest.mark.asyncio
async def test_dry_run_starts_no_container(factory, capsys):
    user_id = await _seed_user(factory)
    wa_running = await _seed(factory, user_id, "wa")
    max_stopped = await _seed(factory, user_id, "max")
    requests: list[str] = []
    transport = _status_transport({_status_url("wa", wa_running): GOOD_BODY}, requests)
    sources = {
        "wa": script.WorkerStatusSource(
            "wa", list_containers=_listing([_container("wa", wa_running)]), transport=transport
        ),
        "max": script.WorkerStatusSource(
            "max",
            list_containers=_listing([_container("max", max_stopped, "exited")]),
            transport=transport,
        ),
    }
    before = await _snapshot(factory)
    patches = _patch_wake_paths()
    mocks = [p.start() for p in patches]
    try:
        await script.run(factory, script.RunOptions(dry_run=True), sources)
    finally:
        for p in patches:
            p.stop()

    out = capsys.readouterr().out
    assert f"#{wa_running} wa: было бы заполнено {MASKED}" in out
    assert _line(out, max_stopped, "max") == (
        f"#{max_stopped} max: воркер недоступен (воркер не запущен)"
    )
    assert await _snapshot(factory) == before
    assert requests == [_status_url("wa", wa_running)]
    wa_start, max_start, wa_ensure, max_ensure = mocks
    wa_start.assert_not_called()
    max_start.assert_not_called()
    wa_ensure.assert_not_called()
    max_ensure.assert_not_called()


@pytest.mark.asyncio
async def test_running_max_not_connected_is_polled_once(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "max")
    requests: list[str] = []
    transport = _status_transport(
        {_status_url("max", account_id): {"connected": False, "exists": True}}, requests
    )
    source = script.WorkerStatusSource(
        "max", list_containers=_listing([_container("max", account_id)]), transport=transport
    )

    await script.run(factory, script.RunOptions(), {"max": source})

    assert requests == [_status_url("max", account_id)], "долгий опрос на пути по умолчанию"
    assert _line(capsys.readouterr().out, account_id, "max") == (
        f"#{account_id} max: воркер недоступен (не подключён)"
    )


# --- подъём остановленного воркера по флагу (O-1 (а), D-04, D-16) ---------------


def _wake_doubles(
    events,
    *,
    kind: str = "wa",
    queue=0,
    running_now=None,
    start_endpoint="default",
    ready=True,
    replies=None,
    sleeps=None,
):
    """Двойники подъёма с ОБЩИМ журналом `events`: ни Docker, ни Redis, ни сети.

    Журнал: `("start", id)`, `("wait", id, timeout)`, `("ask", id)`, `("stop", id)`.
    `queue` — число (всегда), список (очередное чтение; последний элемент
    повторяется; исключение в списке поднимается) или `None` (подключения к
    Redis нет). `ready` — `bool` или исключение для `wait_ready`. `replies` —
    `id -> тело` или `id -> список тел` (очередной запрос; исчерпание — ошибка
    теста после записи в журнал). `sleeps` — журнал пауз опроса MAX.
    """
    reads = iter(range(10**6))
    sequence = queue if isinstance(queue, list) else [queue]

    def queue_len(account_id):
        value = sequence[min(next(reads), len(sequence) - 1)]
        if isinstance(value, BaseException):
            raise value
        return value

    def start(account_id):
        events.append(("start", account_id))
        if start_endpoint == "default":
            return f"http://{kind}-worker-{account_id}:3000"
        return start_endpoint

    def stop(account_id):
        events.append(("stop", account_id))
        return True

    def wait_ready(account_id, *, timeout):
        events.append(("wait", account_id, timeout))
        if isinstance(ready, BaseException):
            raise ready
        return ready

    def endpoint_now(account_id):
        return running_now

    asked: dict[int, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        account_id = int(request.url.path.split("/")[3])
        events.append(("ask", account_id))
        spec = (replies or {}).get(account_id, GOOD_BODY)
        if isinstance(spec, list):
            index = asked.get(account_id, 0)
            asked[account_id] = index + 1
            assert index < len(spec), f"запрос №{index + 1} сверх заданных ответов"
            spec = spec[index]
        if isinstance(spec, BaseException):
            raise spec
        return httpx.Response(200, json=spec)

    async def sleep(seconds):
        if sleeps is not None:
            sleeps.append(seconds)

    return {
        "start": start,
        "stop": stop,
        "wait_ready": wait_ready,
        "running_now": endpoint_now,
        "queue_len": None if queue is None else queue_len,
        "sleep": sleep,
        "transport": httpx.MockTransport(handler),
    }


@pytest.mark.asyncio
async def test_tracer_wake_starts_polls_and_stops_a_stopped_worker(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa", status="active")
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        "wa",
        list_containers=_listing([_container("wa", account_id, "exited")]),
        **_wake_doubles(events, replies={account_id: GOOD_BODY}),
    )

    await script.run(factory, script.RunOptions(wake=True), {"wa": source})

    assert await _columns(factory, account_id) == (STORED, False), (
        "поднятый по флагу воркер не дал номер"
    )
    assert events == [
        ("start", account_id),
        ("wait", account_id, 90.0),
        ("ask", account_id),
        ("stop", account_id),
    ]
    assert f"#{account_id} wa: заполнено {MASKED}" in capsys.readouterr().out


READY_WINDOWS = {"wa": 90.0, "max": 30.0}


def _chain(steps, account_id: int, kind: str) -> list[tuple]:
    """Журнал, который даёт цепочка шагов подъёма для одного аккаунта."""
    named = {
        "start": ("start", account_id),
        "wait": ("wait", account_id, READY_WINDOWS[kind]),
        "ask": ("ask", account_id),
        "stop": ("stop", account_id),
    }
    return [named[step] for step in steps]


FULL = ("start", "wait", "ask", "stop")
WAKE_CASES = [
    pytest.param("connecting", {}, (), "статус не active", id="status-connecting"),
    pytest.param("disconnected", {}, (), "статус не active", id="status-disconnected"),
    pytest.param("sync_failed", {}, (), "статус не active", id="status-sync-failed"),
    pytest.param("active", {"queue": 1}, (), "в очереди есть задачи", id="queue-one"),
    pytest.param("active", {"queue": 0}, FULL, MASKED, id="queue-zero-wakes"),
    pytest.param(
        "active",
        {"queue": ConnectionError("redis")},
        (),
        "очередь не прочитана",
        id="queue-unreadable",
    ),
    pytest.param("active", {"queue": None}, (), "очередь не прочитана", id="no-redis"),
    pytest.param(
        "active",
        {"running_now": "ENDPOINT"},
        ("ask",),
        MASKED,
        id="already-running-is-asked-not-started",
    ),
    pytest.param(
        "active",
        {"start_endpoint": None},
        ("start",),
        "подъём не удался",
        id="start-refused-no-stop",
    ),
    pytest.param(
        "active",
        {"ready": False},
        ("start", "wait", "stop"),
        "воркер поднят, но не ответил",
        id="not-ready-no-ask-but-stop",
    ),
]


@WORKER_KINDS
@pytest.mark.parametrize(("status", "spec", "steps", "fragment"), WAKE_CASES)
@pytest.mark.asyncio
async def test_wake_conditions_matrix(factory, capsys, kind, status, spec, steps, fragment):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind, status=status)
    spec = dict(spec)
    if spec.get("running_now") == "ENDPOINT":
        spec["running_now"] = f"http://{kind}-worker-{account_id}:3000"
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        kind,
        list_containers=_listing([_container(kind, account_id, "exited")]),
        **_wake_doubles(events, kind=kind, **spec),
    )

    await script.run(factory, script.RunOptions(wake=True), {kind: source})

    assert events == _chain(steps, account_id, kind), "журнал подъёма не по условиям O-1"
    assert fragment in _line(capsys.readouterr().out, account_id, kind)
    expected = (STORED, False) if fragment == MASKED else (None, False)
    assert await _columns(factory, account_id) == expected


@WORKER_KINDS
@pytest.mark.asyncio
async def test_wake_never_stops_a_container_it_did_not_start(factory, kind):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind)
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        kind,
        list_containers=_listing([_container(kind, account_id, "running")]),
        **_wake_doubles(events, kind=kind),
    )

    await script.run(factory, script.RunOptions(wake=True), {kind: source})

    assert events == [("ask", account_id)], "чужой работающий контейнер не гасится и не поднимается"


QUEUE_AFTER = [
    pytest.param([0, 1], "контейнер оставлен", id="tasks-appeared"),
    pytest.param([0, ConnectionError("redis")], "just wa-workers", id="unreadable-after"),
]


@WORKER_KINDS
@pytest.mark.parametrize(("queue", "fragment"), QUEUE_AFTER)
@pytest.mark.asyncio
async def test_wake_leaves_the_container_when_the_queue_filled(
    factory, capsys, kind, queue, fragment
):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind)
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        kind,
        list_containers=_listing([_container(kind, account_id, "exited")]),
        **_wake_doubles(events, kind=kind, queue=queue),
    )

    await script.run(factory, script.RunOptions(wake=True), {kind: source})

    assert events == _chain(("start", "wait", "ask"), account_id, kind), (
        "контейнер погашен при непустой или непрочитанной очереди"
    )
    assert fragment in _line(capsys.readouterr().out, account_id, kind)
    assert await _columns(factory, account_id) == (STORED, False)


@WORKER_KINDS
@pytest.mark.asyncio
async def test_wake_with_dry_run_in_the_core_starts_nothing(factory, capsys, kind):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind)
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        kind,
        list_containers=_listing([_container(kind, account_id, "exited")]),
        **_wake_doubles(events, kind=kind),
    )
    before = await _snapshot(factory)

    await script.run(factory, script.RunOptions(dry_run=True, wake=True), {kind: source})

    assert events == [], "под просмотром поднят, опрошен или погашен контейнер"
    assert _line(capsys.readouterr().out, account_id, kind) == (
        f"#{account_id} {kind}: воркер недоступен (воркер не запущен)"
    )
    assert await _snapshot(factory) == before


@pytest.mark.asyncio
async def test_wake_one_container_at_a_time(factory):
    user_id = await _seed_user(factory)
    first = await _seed(factory, user_id, "wa")
    second = await _seed(factory, user_id, "wa")
    containers = [_container("wa", first, "exited"), _container("wa", second, "exited")]

    def sources(events):
        return {
            "wa": script.WorkerStatusSource(
                "wa", list_containers=_listing(containers), **_wake_doubles(events)
            )
        }

    # Без флага — первым: аккаунты ещё без номера, то есть кандидаты, и подъёма нет.
    idle: list[tuple] = []
    summary = await script.run(factory, script.RunOptions(), sources(idle))
    assert summary.counts[script.Outcome.UNREACHABLE] == 2, "без флага аккаунты не опрошены"
    assert idle == [], "без флага поднят контейнер"

    events: list[tuple] = []
    await script.run(factory, script.RunOptions(wake=True), sources(events))

    assert events == [
        *_chain(FULL, first, "wa"),
        *_chain(FULL, second, "wa"),
    ], "контейнеры подняты не строго по одному"


# --- опрос MAX до подключения, окна ожидания, отказы и отмена -------------------

NOT_CONNECTED = {"connected": False, "exists": True}
DEAD = {"connected": False, "exists": False}
ATTEMPTS = script.MAX_CONNECT_ATTEMPTS

MAX_POLL_CASES = [
    pytest.param(
        [NOT_CONNECTED] * (ATTEMPTS - 1) + [GOOD_BODY],
        ATTEMPTS,
        (STORED, False),
        "заполнено",
        id="connected-on-45th",
    ),
    pytest.param(
        [NOT_CONNECTED] * ATTEMPTS,
        ATTEMPTS,
        (None, False),
        "воркер недоступен (не подключён)",
        id="never-connected-45-asks",
    ),
    pytest.param(
        [NOT_CONNECTED, NOT_CONNECTED, DEAD],
        3,
        (None, False),
        "сессия мертва",
        id="dead-session-ends-the-poll",
    ),
]


@pytest.mark.parametrize(("replies", "asks", "columns", "fragment"), MAX_POLL_CASES)
@pytest.mark.asyncio
async def test_wake_max_polls_until_connected_within_attempts(
    factory, capsys, replies, asks, columns, fragment
):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "max")
    events: list[tuple] = []
    sleeps: list[float] = []
    source = script.WorkerStatusSource(
        "max",
        list_containers=_listing([_container("max", account_id, "exited")]),
        **_wake_doubles(events, kind="max", replies={account_id: replies}, sleeps=sleeps),
    )

    await script.run(factory, script.RunOptions(wake=True), {"max": source})

    assert await _columns(factory, account_id) == columns, "MAX не дождался подключения"
    assert events == [
        ("start", account_id),
        ("wait", account_id, 30.0),
        *[("ask", account_id)] * asks,
        ("stop", account_id),
    ], "число запросов опроса MAX не по границе 45"
    assert sleeps == [script.MAX_POLL_INTERVAL] * (asks - 1)
    assert fragment in _line(capsys.readouterr().out, account_id, "max")


@pytest.mark.asyncio
async def test_wake_wa_and_max_ready_windows(factory):
    user_id = await _seed_user(factory)
    wa_id = await _seed(factory, user_id, "wa")
    max_id = await _seed(factory, user_id, "max")
    wa_events: list[tuple] = []
    max_events: list[tuple] = []
    sources = {
        "wa": script.WorkerStatusSource(
            "wa",
            list_containers=_listing([_container("wa", wa_id, "exited")]),
            **_wake_doubles(wa_events, replies={wa_id: [NOT_CONNECTED]}),
        ),
        "max": script.WorkerStatusSource(
            "max",
            list_containers=_listing([_container("max", max_id, "exited")]),
            **_wake_doubles(max_events, kind="max", replies={max_id: [GOOD_BODY]}),
        ),
    }

    await script.run(factory, script.RunOptions(wake=True), sources)

    # WA: окно 90 с и ровно один запрос, даже если воркер ответил «не подключён».
    assert wa_events == _chain(FULL, wa_id, "wa")
    assert ("wait", wa_id, 90.0) in wa_events
    assert ("wait", max_id, 30.0) in max_events
    assert max_events == _chain(FULL, max_id, "max")


WAKE_FAILURES = [
    pytest.param(
        {"replies": "ConnectError"},
        ("start", "wait", "ask", "stop"),
        "воркер недоступен (ConnectError)",
        id="transport-refused",
    ),
    pytest.param(
        {"ready": RuntimeError("boom-79991234567")},
        ("start", "wait", "stop"),
        "сбой по аккаунту (RuntimeError)",
        id="wait-raised",
    ),
    pytest.param(
        {"ready": asyncio.CancelledError()},
        ("start", "wait", "stop"),
        None,
        id="cancelled",
    ),
]


@WORKER_KINDS
@pytest.mark.parametrize(("spec", "steps", "line"), WAKE_FAILURES)
@pytest.mark.asyncio
async def test_wake_stops_the_container_on_failure_and_cancellation(
    factory, capsys, kind, spec, steps, line
):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, kind)
    spec = dict(spec)
    if spec.get("replies") == "ConnectError":
        spec["replies"] = {account_id: httpx.ConnectError("refused")}
    events: list[tuple] = []
    source = script.WorkerStatusSource(
        kind,
        list_containers=_listing([_container(kind, account_id, "exited")]),
        **_wake_doubles(events, kind=kind, **spec),
    )

    if line is None:
        # Отмена проходит наружу из `run`, но поднятый контейнер всё равно гасится.
        with pytest.raises(asyncio.CancelledError):
            await script.run(factory, script.RunOptions(wake=True), {kind: source})
    else:
        await script.run(factory, script.RunOptions(wake=True), {kind: source})
        out = capsys.readouterr().out
        assert _line(out, account_id, kind) == f"#{account_id} {kind}: {line}"
        assert "79991234567" not in out

    assert events == _chain(steps, account_id, kind), "поднятый контейнер не погашен"
    assert await _columns(factory, account_id) == (None, False)


@pytest.mark.asyncio
async def test_wake_stop_failure_keeps_the_number_and_names_the_container(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed(factory, user_id, "wa")
    events: list[tuple] = []
    doubles = _wake_doubles(events)

    def stop_refused(account_id):
        events.append(("stop", account_id))
        raise RuntimeError("docker-secret-79991234567")

    doubles["stop"] = stop_refused
    source = script.WorkerStatusSource(
        "wa", list_containers=_listing([_container("wa", account_id, "exited")]), **doubles
    )

    await script.run(factory, script.RunOptions(wake=True), {"wa": source})

    out = capsys.readouterr().out
    assert await _columns(factory, account_id) == (STORED, False), "отказ остановки спрятал номер"
    assert "остановка не удалась (RuntimeError)" in _line(out, account_id, "wa")
    assert "docker-secret-79991234567" not in out


# --- источник Telegram: короткое последовательное подключение без обновлений ---------


def _valid_session_string() -> str:
    """Годная строка сессии Telethon, построенная без сети (ключ из нулей)."""
    session = StringSession()
    session.set_dc(2, "149.154.167.51", 443)
    session.auth_key = AuthKey(bytes(256))
    return session.save()


async def _seed_tg(factory, user_id: int, credentials: str | None = None) -> int:
    """Аккаунт `tg_user` со строкой сессии: годной по умолчанию, иначе — переданной."""
    account_id = await _seed(factory, user_id, "tg_user")
    value = _valid_session_string() if credentials is None else credentials
    async with factory() as session:
        await session.execute(
            update(MessengerAccount)
            .where(MessengerAccount.id == account_id)
            .values(credentials=value)
        )
        await session.commit()
    return account_id


class FakeTelegramClient:
    """Двойник клиента Telethon: журнал вызовов и общий счётчик подключений.

    `world` — общее состояние прогона (`TelegramWorld`): журнал событий
    `(событие, id)`, `open_now` / `max_open` — сколько клиентов подключено
    одновременно (инкремент в начале `connect`, декремент в `disconnect`).
    `start` и `check_connection` — `AsyncMock`: интерактивный вход и давняя
    проверка соединения адаптера не должны вызываться вовсе.
    """

    def __init__(self, world, session, api_id, api_hash, receive_updates):
        self.world = world
        self.session = session
        self.api_id = api_id
        self.api_hash = api_hash
        self.receive_updates = receive_updates
        self.tag = len(world.clients) + 1
        self.start = AsyncMock()
        self.check_connection = AsyncMock()
        self.calls: list[str] = []

    async def _step(self, name: str):
        self.calls.append(name)
        self.world.events.append((name, self.tag))
        if self.world.scenario.get("yield_loop"):
            await asyncio.sleep(0)
        raised = self.world.scenario.get("raise_on", {}).get(name)
        if raised is not None:
            raise raised

    async def connect(self):
        self.world.open_now += 1
        self.world.max_open = max(self.world.max_open, self.world.open_now)
        await self._step("connect")

    async def is_user_authorized(self):
        await self._step("is_user_authorized")
        return self.world.scenario.get("authorized", True)

    async def get_me(self):
        await self._step("get_me")
        return self.world.scenario.get("me", SimpleNamespace(phone=REPORTED))

    async def disconnect(self):
        self.world.open_now -= 1
        await self._step("disconnect")


class TelegramWorld:
    """Общее состояние двойников клиента: фабрика, журнал, счётчик, сценарий."""

    def __init__(self, **scenario):
        self.scenario = scenario
        self.events: list[tuple] = []
        self.clients: list[FakeTelegramClient] = []
        self.open_now = 0
        self.max_open = 0

    def factory(self, session, api_id, api_hash, *, receive_updates):
        client = FakeTelegramClient(self, session, api_id, api_hash, receive_updates)
        self.clients.append(client)
        return client


def _busy_probe(answer=False):
    """Двойник признака «занят»: журнал `account_id`; ответ — значение или исключение."""
    asked: list[int] = []

    async def probe(account_id):
        asked.append(account_id)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    probe.asked = asked
    return probe


def _telegram_source(world, probe=None, **kw):
    kw.setdefault("api_id", 1)
    kw.setdefault("api_hash", "h")
    return script.TelegramSource(
        busy_probe=probe or _busy_probe(False),
        client_factory=world.factory,
        pause=0.0,
        **kw,
    )


@pytest.mark.asyncio
async def test_tracer_telegram_number_reaches_the_writer_without_updates(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld()
    probe = _busy_probe(False)
    source = _telegram_source(world, probe)

    await script.run(factory, script.RunOptions(), {"tg_user": source})

    assert await _columns(factory, account_id) == (STORED, False), "номер Telegram не записан"
    assert len(world.clients) == 1
    client = world.clients[0]
    assert client.receive_updates is False
    assert (client.api_id, client.api_hash) == (1, "h")
    assert client.calls == ["connect", "is_user_authorized", "get_me", "disconnect"]
    client.start.assert_not_called()
    client.check_connection.assert_not_called()
    assert probe.asked == [account_id]
    out = capsys.readouterr().out
    assert f"#{account_id} tg_user: заполнено {MASKED}" in out


# --- карта исходов Telethon по классам, строка сессии до сети (D-17) ----------------

_FULL_CALLS = ["connect", "is_user_authorized", "get_me", "disconnect"]

TELEGRAM_OUTCOMES = [
    pytest.param(
        {"raise_on": {"connect": telethon_errors.AuthKeyDuplicatedError(request=None)}},
        "сессия мертва (AuthKeyDuplicatedError)",
        ["connect", "disconnect"],
        id="auth-key-duplicated",
    ),
    pytest.param(
        {"raise_on": {"connect": telethon_errors.SessionRevokedError(request=None)}},
        "сессия мертва (SessionRevokedError)",
        ["connect", "disconnect"],
        id="session-revoked",
    ),
    pytest.param(
        {"raise_on": {"get_me": telethon_errors.SessionRevokedError(request=None)}},
        "сессия мертва (SessionRevokedError)",
        _FULL_CALLS,
        id="session-revoked-on-get-me",
    ),
    pytest.param(
        {"raise_on": {"connect": telethon_errors.FloodWaitError(request=None, capture=30)}},
        "воркер недоступен (FloodWaitError)",
        ["connect", "disconnect"],
        id="flood-wait",
    ),
    pytest.param(
        {"raise_on": {"connect": OSError("net-down")}},
        "воркер недоступен (OSError)",
        ["connect", "disconnect"],
        id="os-error",
    ),
    pytest.param(
        {"raise_on": {"is_user_authorized": TimeoutError("slow")}},
        "воркер недоступен (TimeoutError)",
        ["connect", "is_user_authorized", "disconnect"],
        id="timeout",
    ),
    pytest.param(
        {"authorized": False},
        "сессия мертва (не авторизована)",
        ["connect", "is_user_authorized", "disconnect"],
        id="not-authorized",
    ),
    pytest.param(
        {"me": None},
        "сессия мертва (не авторизована)",
        _FULL_CALLS,
        id="get-me-none",
    ),
    pytest.param(
        {"me": SimpleNamespace(phone=None)},
        "номера нет",
        _FULL_CALLS,
        id="user-without-a-number",
    ),
    pytest.param(
        {"raise_on": {"get_me": RuntimeError("boom")}},
        "сбой по аккаунту (RuntimeError)",
        _FULL_CALLS,
        id="other-exception",
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario, line, calls", TELEGRAM_OUTCOMES)
async def test_telegram_outcomes_map(factory, capsys, scenario, line, calls):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld(**scenario)

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world)})

    out = capsys.readouterr().out
    assert _line(out, account_id, "tg_user") == f"#{account_id} tg_user: {line}", (
        "исход Telethon назван не по карте A3 (AuthKeyDuplicated не названа мёртвой сессией)"
    )
    client = world.clients[0]
    assert client.calls == calls, "disconnect не ожидался ровно один раз на этом пути"
    client.start.assert_not_called()
    client.check_connection.assert_not_called()
    assert await _columns(factory, account_id) == (None, False)
    assert world.open_now == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("credentials", ["", "   ", "pending", "creds", "1abc"])
async def test_telegram_bad_session_string_never_connects(factory, capsys, credentials):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id, credentials)
    world = TelegramWorld()
    probe = _busy_probe(False)

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world, probe)})

    out = capsys.readouterr().out
    assert _line(out, account_id, "tg_user").startswith(f"#{account_id} tg_user: сессия мертва")
    assert world.clients == [], "клиент построен из негодной строки сессии"
    assert probe.asked == [], "признак «занят» опрошен для негодной строки сессии"


@pytest.mark.asyncio
async def test_telegram_disconnect_awaited_on_every_path(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld(raise_on={"disconnect": OSError("close-failed")})

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world)})

    assert await _columns(factory, account_id) == (STORED, False), (
        "отказ отключения изменил исход"
    )
    assert world.clients[0].calls == _FULL_CALLS
    out = capsys.readouterr().out
    assert f"#{account_id} tg_user: заполнено {MASKED}" in out


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "creds", [{"api_id": 0, "api_hash": "h"}, {"api_id": 1, "api_hash": ""}], ids=["id", "hash"]
)
async def test_telegram_missing_api_credentials_never_connect(factory, capsys, creds):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld()
    probe = _busy_probe(False)

    await script.run(
        factory, script.RunOptions(), {"tg_user": _telegram_source(world, probe, **creds)}
    )

    out = capsys.readouterr().out
    assert _line(out, account_id, "tg_user").startswith(f"#{account_id} tg_user: воркер недоступен")
    assert world.clients == []


@pytest.mark.asyncio
async def test_telegram_output_carries_no_session_or_exception_text(factory, capsys):
    user_id = await _seed_user(factory)
    session_string = _valid_session_string()
    account_id = await _seed_tg(factory, user_id, session_string)
    world = TelegramWorld(raise_on={"connect": OSError("secret-79991234567")})

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world)})

    out = capsys.readouterr().out
    assert session_string not in out
    assert "secret-79991234567" not in out
    assert "79991234567" not in out
    assert f"#{account_id} tg_user: воркер недоступен (OSError)" in out


# --- занятые пропускаются в закрытую, строго по одному, просмотр (D-09, D-05) ------


@pytest.mark.asyncio
async def test_telegram_busy_account_is_never_connected(factory, capsys):
    user_id = await _seed_user(factory)
    busy_id = await _seed_tg(factory, user_id)
    free_id = await _seed_tg(factory, user_id)
    asked: list[int] = []

    async def probe(account_id):
        asked.append(account_id)
        return account_id == busy_id

    world = TelegramWorld()

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world, probe)})

    out = capsys.readouterr().out
    assert _line(out, busy_id, "tg_user") == f"#{busy_id} tg_user: занят, повторите позже (идёт рассылка)"
    assert asked == [busy_id, free_id]
    assert len(world.clients) == 1, "фабрика вызвана для занятого аккаунта"
    assert world.events == [(name, 1) for name in _FULL_CALLS], "connect ожидался для занятого"
    assert await _columns(factory, busy_id) == (None, False)
    assert await _columns(factory, free_id) == (STORED, False)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answer, note",
    [
        pytest.param(None, "статус рассылки не определён", id="none"),
        pytest.param(
            ConnectionError("redis-secret-79991234567"),
            "статус рассылки не определён: ConnectionError",
            id="raises",
        ),
    ],
)
async def test_telegram_busy_unknown_fails_closed(factory, capsys, answer, note):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld()

    await script.run(
        factory, script.RunOptions(), {"tg_user": _telegram_source(world, _busy_probe(answer))}
    )

    out = capsys.readouterr().out
    assert _line(out, account_id, "tg_user") == f"#{account_id} tg_user: занят, повторите позже ({note})"
    assert world.clients == [], "неопределённый признак не остановил подключение"
    assert await _columns(factory, account_id) == (None, False)
    assert "redis-secret-79991234567" not in out


@pytest.mark.asyncio
async def test_telegram_sequential_one_client_at_a_time(factory):
    user_id = await _seed_user(factory)
    for _ in range(3):
        await _seed_tg(factory, user_id)
    world = TelegramWorld(yield_loop=True)

    await script.run(factory, script.RunOptions(), {"tg_user": _telegram_source(world)})

    assert len(world.clients) == 3
    assert world.max_open == 1, "одновременно подключено больше одного клиента Telegram"
    assert world.events == [(name, tag) for tag in (1, 2, 3) for name in _FULL_CALLS], (
        "disconnect не дождались до следующего connect"
    )


@pytest.mark.asyncio
async def test_telegram_dry_run_polls_but_writes_nothing(factory, capsys):
    user_id = await _seed_user(factory)
    account_id = await _seed_tg(factory, user_id)
    world = TelegramWorld()
    before = await _snapshot(factory)

    await script.run(
        factory, script.RunOptions(dry_run=True), {"tg_user": _telegram_source(world)}
    )

    out = capsys.readouterr().out
    assert out.splitlines()[0].startswith("РЕЖИМ ПРОСМОТРА")
    assert f"#{account_id} tg_user: было бы заполнено {MASKED}" in out
    assert world.events == [(name, 1) for name in _FULL_CALLS], "просмотр не опросил Telegram"
    assert await _snapshot(factory) == before, "просмотр изменил строки аккаунтов"
