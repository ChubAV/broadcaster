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

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import backfill_account_phones as script  # noqa: E402

from app.database import Base  # noqa: E402
from app.models.messenger_account import MessengerAccount  # noqa: E402
from app.models.user import User  # noqa: E402
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
        await session.execute(
            text("UPDATE messenger_accounts SET phone_is_manual = 1 WHERE id = :id"),
            {"id": flag_only},
        )
        await session.commit()
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
