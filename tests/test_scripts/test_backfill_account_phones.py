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

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
from docker.errors import DockerException
from sqlalchemy import select, text
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
