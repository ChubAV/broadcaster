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
from sqlalchemy import select
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
