"""Гонка автоисточника и ручной записи номера (критерий 4, PHONE-02, D-08, D-16).

ЧТО ДОКАЗЫВАЕТСЯ. Соседний `test_account_phone_writer.py` проверяет правило
«ручной номер автоисточник не затирает» ПОСЛЕДОВАТЕЛЬНО. Здесь — НАЛОЖЕНИЕ:
пользователь сохраняет ручной номер В ТОТ МОМЕНТ, когда автоисточник (мастер
подключения, скрипт дозаполнения) уже начал свою запись. Исход обязан решать
сам оператор записи, а не порядок, в котором две стороны дошли до базы.

**Файловая SQLite, а не база в памяти.** Две стороны гонки — два соединения,
а содержимое базы в оперативной памяти между соединениями не сохраняется
(довод `tests/test_services/test_payment_concurrency.py`).

**Наложение задаётся детерминированно, а не `asyncio.gather`.** Параллельный
запуск дал бы недетерминированный порядок и «database is locked» — тест, который
иногда зелёный, хуже отсутствующего. Порядок задаётся подменой `execute` у
СЕССИИ автоисточника: перед её k-м оператором ручная запись выполняется ДРУГОЙ
сессией целиком, с коммитом. Подменяется метод сессии, а не крючок в боевом
коде: сеамов для тестов в `app/` не добавляется. Блокировок это не задевает:
pysqlite открывает транзакцию на первом операторе ЗАПИСИ, поэтому до своего
UPDATE автоисточник ничего не держит. Позиция «после оператора записи и до
коммита» не берётся по той же причине наоборот: автоисточник уже держит
блокировку записи, и ручная сессия ждала бы «database is locked».

**Позиции берутся из ИЗМЕРЕННОГО числа операторов писателя.** `N` снимается
прогоном без вклинивания; позиции — `1…N` (перед k-м оператором) и `0` (после
коммита автоисточника). Боевой писатель отдаёт один оператор, отрицание — два.

**ЛОВУШКА ВАКУУМА — ПОЧЕМУ В КАЖДОЙ ПОЗИЦИИ УТВЕРЖДАЕТСЯ «РУЧНАЯ ЗАПИСЬ
СОСТОЯЛАСЬ».** Позиция за пределами операторов писателя молча не срабатывает:
ручной записи не было вовсе, итог «автономер, не ручной» выглядит законным, и
тест зеленеет, ничего не проверив. Поэтому каждый исход несёт флаг
`manual_fired`, а `race_violations` называет позицию без ручной записи
вакуумом, а не успехом.

**Контроль-отрицание (D-08).** `read_check_write` — писатель «прочитать,
проверить в Python, записать», функция ТЕСТА, в `app/` её нет. Он проходит через
ТОТ ЖЕ помощник `run_interleaved`, что и боевой `fill_reported_phone`, и теряет
ручной номер ровно в позиции 2 — между чтением и записью: итог — чужой номер под
поднятым признаком «ручной». Если боевой писатель когда-нибудь «упростят» до
такой пары, правило боевого писателя покраснеет так же, как краснеет отрицание.
"""

import itertools
from dataclasses import dataclass

import pytest
import pytest_asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.accounts.phone import (
    PhoneWrite,
    fill_reported_phone,
    set_manual_phone,
)
from app.database import Base
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.services.phone import normalize_reported

MANUAL_TEXT = "+7 999 000-00-01"
MANUAL_E164 = "+79990000001"
AUTO_RAW = "79990000002"
AUTO_E164 = "+79990000002"
EXPECTED_FINAL = (MANUAL_E164, True)

_SEED_NUMBERS = itertools.count(1)


@dataclass(frozen=True)
class RaceOutcome:
    """Исход одной позиции вклинивания.

    `position` — 0 (ручная запись после коммита автоисточника) или k (перед
    k-м оператором автоисточника); `manual_fired` — ручная запись действительно
    выполнена; `final` — `(phone, phone_is_manual)` строки после обеих сторон;
    `statements` — сколько операторов отдал писатель.
    """

    position: int
    manual_fired: bool
    final: tuple
    statements: int


@pytest_asyncio.fixture
async def sessions(tmp_path):
    """Фабрика НЕЗАВИСИМЫХ сессий поверх ОДНОЙ файловой базы."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def _seed(factory) -> int:
    """Новый аккаунт с неизвестным номером `(NULL, false)`; возвращает его id."""
    async with factory() as session:
        user = User(email=f"race-{next(_SEED_NUMBERS)}@t.com", password_hash="h", name="T")
        session.add(user)
        await session.flush()
        account = MessengerAccount(
            user_id=user.id, type="tg_user", credentials="creds", status="active"
        )
        session.add(account)
        await session.commit()
        return account.id


async def _final(factory, account_id: int) -> tuple:
    async with factory() as session:
        result = await session.execute(
            select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
                MessengerAccount.id == account_id
            )
        )
        return tuple(result.one())


async def read_check_write(session: AsyncSession, account_id: int, raw: object) -> PhoneWrite:
    """ОТРИЦАНИЕ: прочитать, проверить в Python, записать безусловно.

    Оба оператора идут через `session.execute`, поэтому помощник может
    вклиниться между ними. Ровно эта форма запрещена боевому писателю.
    """
    e164 = normalize_reported(raw)
    if e164 is None:
        return PhoneWrite.UNPARSEABLE
    current = (
        await session.execute(
            select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
                MessengerAccount.id == account_id
            )
        )
    ).one()
    if current.phone is not None or current.phone_is_manual:
        return PhoneWrite.KEPT
    await session.execute(
        update(MessengerAccount)
        .where(MessengerAccount.id == account_id)
        .values(phone=e164)
        .execution_options(synchronize_session=False)
    )
    return PhoneWrite.WRITTEN


async def run_interleaved(factory, account_id: int, writer, position: int) -> RaceOutcome:
    """Автоисточник `writer` и ручная запись другой сессией в позиции `position`.

    `position >= 1` — ручная запись с коммитом перед `position`-м оператором
    автоисточника; `0` — после коммита автоисточника. Позиция, до которой
    писатель не дошёл, ручную запись не вызывает: `manual_fired` останется
    ложным, и это вакуум, а не успех.
    """
    fired = {"manual": False}
    count = {"n": 0}

    async def manual_write():
        async with factory() as manual:
            await set_manual_phone(manual, account_id, MANUAL_TEXT)
            await manual.commit()
        fired["manual"] = True

    async with factory() as auto:
        original = auto.execute

        async def interleaving(*args, **kwargs):
            count["n"] += 1
            if count["n"] == position:
                await manual_write()
            return await original(*args, **kwargs)

        auto.execute = interleaving
        await writer(auto, account_id, AUTO_RAW)
        await auto.commit()

    if position == 0:
        await manual_write()

    return RaceOutcome(
        position=position,
        manual_fired=fired["manual"],
        final=await _final(factory, account_id),
        statements=count["n"],
    )


async def measure_statements(factory, writer) -> int:
    """Число операторов писателя — тот же прогон без вклинивания, свежий посев.

    Позиция `-1` не совпадает ни с одним номером оператора и не равна нулю, так
    что ручная запись не выполняется вовсе.
    """
    account_id = await _seed(factory)
    outcome = await run_interleaved(factory, account_id, writer, -1)
    assert outcome.manual_fired is False
    return outcome.statements


async def _outcomes(factory, writer, positions) -> list[RaceOutcome]:
    outcomes = []
    for position in positions:
        account_id = await _seed(factory)
        outcomes.append(await run_interleaved(factory, account_id, writer, position))
    return outcomes


def race_violations(outcomes: list[RaceOutcome]) -> list[str]:
    """Заготовка RED: нарушений не называет."""
    return []


@pytest.mark.asyncio
async def test_control_read_check_write_loses_the_manual_number_between_read_and_write(
    sessions,
):
    """ОТРИЦАНИЕ краснеет по-настоящему: позиция 2 теряет ручной номер.

    Между чтением и безусловной записью пользователь сохранил ручной номер;
    запись поверх ставит чужой номер под поднятым признаком «ручной».
    """
    statements = await measure_statements(sessions, read_check_write)
    assert statements == 2, f"отрицание отдало {statements} операторов, а не 2"

    outcomes = await _outcomes(sessions, read_check_write, range(statements + 1))
    assert [o.position for o in outcomes] == [0, 1, 2]
    assert all(o.manual_fired for o in outcomes), outcomes

    violations = race_violations(outcomes)

    assert [v.split(":")[0] for v in violations] == ["позиция 2"], violations
    assert outcomes[2].final == (AUTO_E164, True)


@pytest.mark.asyncio
async def test_the_production_writer_keeps_the_manual_number_in_every_position(sessions):
    """Боевой писатель держит ручной номер во ВСЕХ измеренных позициях."""
    statements = await measure_statements(sessions, fill_reported_phone)
    assert statements >= 1, "боевой писатель не отдал ни одного оператора"

    outcomes = await _outcomes(sessions, fill_reported_phone, range(statements + 1))

    assert [o.position for o in outcomes] == list(range(statements + 1))
    assert race_violations(outcomes) == []
    for outcome in outcomes:
        assert outcome.manual_fired is True, f"позиция {outcome.position}: вакуум"
        assert outcome.final == EXPECTED_FINAL, outcome


@pytest.mark.asyncio
async def test_control_a_position_beyond_the_writer_statements_is_named_as_vacuum(sessions):
    """Позиция за пределами операторов писателя — вакуум, а не успех."""
    statements = await measure_statements(sessions, fill_reported_phone)
    beyond = statements + 1

    [outcome] = await _outcomes(sessions, fill_reported_phone, [beyond])

    assert outcome.manual_fired is False
    violations = race_violations([outcome])
    assert len(violations) == 1, violations
    assert violations[0].startswith(f"позиция {beyond}:"), violations
    assert "вакуум" in violations[0], violations


@pytest.mark.asyncio
async def test_the_race_runs_on_one_file_database_with_independent_sessions(sessions, tmp_path):
    """Стенд честен: файл в `tmp_path`, ручная сессия — не сессия автоисточника."""
    database = sessions.kw["bind"].url.database
    assert database != ":memory:"
    assert database == str(tmp_path / "race.db")

    opened: list[AsyncSession] = []

    def recording_factory():
        session = sessions()
        opened.append(session)
        return session

    seen: dict = {}

    async def observed_writer(session, account_id, raw):
        seen["auto"] = session
        return await fill_reported_phone(session, account_id, raw)

    account_id = await _seed(sessions)
    outcome = await run_interleaved(recording_factory, account_id, observed_writer, 1)

    assert outcome.manual_fired is True
    assert opened[0] is seen["auto"]
    manual = opened[1]
    assert manual is not seen["auto"]
    assert len({id(s) for s in opened}) == len(opened) == 3
