"""Единственный писатель номера: последовательные правила (критерий 4, PHONE-02).

Файл — спецификация `app/application/accounts/phone.py`, ЕДИНСТВЕННОГО места,
где номер попадает в колонку (D-12). Правило, ради которого существует признак
`phone_is_manual`, одно: номер, указанный пользователем вручную, автоматический
источник не затирает (D-07). Здесь оно проверено ПОСЛЕДОВАТЕЛЬНО — ручной, затем
автоисточник; автоисточник, затем ручной; очистка, затем автоисточник снова.
Наложение тех же записей в гонке проверяет соседний `test_account_phone_race.py`.

Итог строки каждый раз читается свежим `select` КОЛОНОК, а не атрибутом
загруженного объекта: писатель идёт мимо identity map
(`synchronize_session=False`), и объект той же сессии до `refresh` показывает
старое значение. Чтение колонок отвечает о БАЗЕ, а не о кэше сессии.

Отказы до базы (мусор от автоисточника, неверный ручной ввод) проверяются
счётчиком вызовов `execute` у сессии: «строка не изменилась» доказывает лишь,
что запись не удалась, а ноль операторов — что писатель её и не пытался.

Писатель не коммитит: транзакцией владеет вызывающий (мастер Фазы 19, скрипт
Фазы 20, форма Фазы 18), поэтому последнее правило откатывает запись.
"""

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import Update
from sqlalchemy.sql.selectable import Select

from app.application.accounts import phone as writer_module
from app.application.accounts.phone import (
    ACCOUNT_NOT_IN_SESSION,
    PhoneWrite,
    fill_reported_phone,
    record_reported_phone,
    set_manual_phone,
)
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.services.phone import PhoneError, format_phone

UNKNOWN = (None, False)
AUTO_E164 = "+79991234567"
MANUAL_E164 = "+79990000001"


async def _seed_account(db_session: AsyncSession) -> MessengerAccount:
    user = User(email="phone-writer@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    account = MessengerAccount(
        user_id=user.id, type="tg_user", credentials="creds", status="active"
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


async def _row(db_session: AsyncSession, account_id: int) -> tuple:
    result = await db_session.execute(
        select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
            MessengerAccount.id == account_id
        )
    )
    return tuple(result.one())


def _count_executes(db_session: AsyncSession, monkeypatch) -> dict:
    """Обёртка-счётчик над `execute` сессии: сколько операторов отдал писатель."""
    original = db_session.execute
    calls = {"n": 0}

    async def counting(*args, **kwargs):
        calls["n"] += 1
        return await original(*args, **kwargs)

    monkeypatch.setattr(db_session, "execute", counting)
    return calls


def _record_statements(db_session: AsyncSession, monkeypatch) -> list:
    """Обёртка-запись над `execute` сессии: КАКИЕ операторы и в каком порядке.

    Складывает первый позиционный аргумент каждого вызова. Счётчика мало там,
    где важен порядок: проба существования строки законна только ПОСЛЕ
    условного UPDATE, а не перед ним (D-07).
    """
    original = db_session.execute
    statements: list = []

    async def recording(*args, **kwargs):
        statements.append(args[0] if args else kwargs.get("statement"))
        return await original(*args, **kwargs)

    monkeypatch.setattr(db_session, "execute", recording)
    return statements


async def _add_account(db_session: AsyncSession, user_id: int) -> MessengerAccount:
    """Ещё одна строка с неизвестным номером у уже посеянного пользователя."""
    account = MessengerAccount(
        user_id=user_id, type="tg_user", credentials="creds", status="active"
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account


@pytest.mark.asyncio
async def test_an_automatic_number_fills_an_unknown_account_and_shows_in_display_form(
    db_session: AsyncSession,
):
    """ТРАСЕР: число от мессенджера → колонка E.164 → показ человеку.

    Сквозной срез всех трёх модулей фазы: нормализация 16-02, колонки 16-03 и
    писатель 16-05. Число приходит как `int` (так его отдаёт Telethon).
    """
    account = await _seed_account(db_session)

    outcome = await fill_reported_phone(db_session, account.id, 79991234567)

    assert outcome is PhoneWrite.WRITTEN
    row = await _row(db_session, account.id)
    assert row == (AUTO_E164, False)
    assert format_phone(row[0]) == "+7 999 123-45-67"


@pytest.mark.asyncio
async def test_a_manual_number_survives_a_later_automatic_write(db_session: AsyncSession):
    """Ручной, затем автоисточник: автоисточник отступает, ручной цел (D-07)."""
    account = await _seed_account(db_session)

    stored = await set_manual_phone(db_session, account.id, "8 999 000-00-01")
    outcome = await fill_reported_phone(db_session, account.id, "79991234567")

    assert stored == MANUAL_E164
    assert outcome is PhoneWrite.KEPT
    assert await _row(db_session, account.id) == (MANUAL_E164, True)


@pytest.mark.asyncio
async def test_a_manual_write_replaces_an_automatic_number_and_raises_the_flag(
    db_session: AsyncSession,
):
    """Автоисточник, затем ручной: ручная запись пишет всегда и ставит признак."""
    account = await _seed_account(db_session)

    first = await fill_reported_phone(db_session, account.id, "79991234567")
    stored = await set_manual_phone(db_session, account.id, "8 999 000-00-01")

    assert first is PhoneWrite.WRITTEN
    assert stored == MANUAL_E164
    assert await _row(db_session, account.id) == (MANUAL_E164, True)


@pytest.mark.asyncio
@pytest.mark.parametrize("cleared", ["", "   ", None], ids=["empty", "spaces", "none"])
async def test_clearing_returns_the_unknown_state_and_reopens_automatic_sources(
    db_session: AsyncSession, cleared
):
    """Очистка — «неизвестен» одним оператором, и автоисточник снова вправе писать.

    Обе колонки меняются ВМЕСТЕ: очистка одного номера при поднятом признаке
    отвергается CHECK `ck_messenger_accounts_manual_requires_phone` (PHONE-10).
    """
    account = await _seed_account(db_session)
    await set_manual_phone(db_session, account.id, "8 999 000-00-01")

    stored = await set_manual_phone(db_session, account.id, cleared)

    assert stored is None
    assert await _row(db_session, account.id) == UNKNOWN

    outcome = await fill_reported_phone(db_session, account.id, "79991234567")

    assert outcome is PhoneWrite.WRITTEN
    assert await _row(db_session, account.id) == (AUTO_E164, False)


@pytest.mark.asyncio
async def test_an_unparseable_automatic_number_leaves_the_row_untouched(
    db_session: AsyncSession, monkeypatch
):
    """Мусор от источника: `UNPARSEABLE`, и к базе писатель не обращался вовсе."""
    account = await _seed_account(db_session)
    calls = _count_executes(db_session, monkeypatch)

    outcome = await fill_reported_phone(db_session, account.id, "abc")

    assert outcome is PhoneWrite.UNPARSEABLE
    assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов на мусоре"
    monkeypatch.undo()
    assert await _row(db_session, account.id) == UNKNOWN


@pytest.mark.asyncio
async def test_an_automatic_write_never_replaces_an_automatic_number(db_session: AsyncSession):
    """Уже заполненный автономер второй автоисточник не меняет (`KEPT`)."""
    account = await _seed_account(db_session)

    first = await fill_reported_phone(db_session, account.id, "79991234567")
    second = await fill_reported_phone(db_session, account.id, "79990000002")

    assert first is PhoneWrite.WRITTEN
    assert second is PhoneWrite.KEPT
    assert await _row(db_session, account.id) == (AUTO_E164, False)


@pytest.mark.asyncio
async def test_a_rejected_manual_text_raises_before_the_database_is_touched(
    db_session: AsyncSession, monkeypatch
):
    """Неверный ручной ввод поднимает `PhoneError` до первого оператора."""
    account = await _seed_account(db_session)
    calls = _count_executes(db_session, monkeypatch)

    with pytest.raises(PhoneError):
        await set_manual_phone(db_session, account.id, "123-45-67")

    assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов на неверном вводе"
    monkeypatch.undo()
    assert await _row(db_session, account.id) == UNKNOWN


@pytest.mark.asyncio
async def test_recording_a_new_account_flushes_and_mirrors_the_number(db_session: AsyncSession):
    """Новая строка мастера: писатель сам сбрасывает её в базу и зеркалит номер.

    Зеркало — без второго UPDATE: объект после записи не грязный, иначе ORM на
    коммите повторила бы запись, притворяясь, что её сделал он.
    """
    seeded = await _seed_account(db_session)
    account = MessengerAccount(
        user_id=seeded.user_id, type="wa", credentials="creds", status="active"
    )
    db_session.add(account)
    assert account.id is None

    outcome = await record_reported_phone(db_session, account, "79991234567")

    assert outcome is PhoneWrite.WRITTEN
    assert account.id is not None
    assert account.phone == AUTO_E164
    assert account not in db_session.dirty
    assert await _row(db_session, account.id) == (AUTO_E164, False)


@pytest.mark.asyncio
async def test_recording_keeps_a_manual_number(db_session: AsyncSession):
    """Ручной номер у строки: запись мастера отступает, объект и строка — ручные."""
    account = await _seed_account(db_session)
    await set_manual_phone(db_session, account.id, "8 999 000-00-01")
    await db_session.commit()
    await db_session.refresh(account)

    outcome = await record_reported_phone(db_session, account, "79991234567")

    assert outcome is PhoneWrite.KEPT
    assert (account.phone, account.phone_is_manual) == (MANUAL_E164, True)
    assert await _row(db_session, account.id) == (MANUAL_E164, True)


@pytest.mark.asyncio
async def test_an_automatic_writer_never_marks_the_number_manual(db_session: AsyncSession):
    """После `WRITTEN` признак ручного ложен у обоих автописателей (D-07)."""
    existing = await _seed_account(db_session)
    fresh = MessengerAccount(
        user_id=existing.user_id, type="max", credentials="creds", status="active"
    )
    db_session.add(fresh)

    filled = await fill_reported_phone(db_session, existing.id, "79991234567")
    recorded = await record_reported_phone(db_session, fresh, "79990000002")

    assert (filled, recorded) == (PhoneWrite.WRITTEN, PhoneWrite.WRITTEN)
    assert (await _row(db_session, existing.id))[1] is False
    assert (await _row(db_session, fresh.id))[1] is False


@pytest.mark.asyncio
async def test_setting_a_manual_number_on_a_missing_account_raises(db_session: AsyncSession):
    """Нет строки с таким `account_id` — `LookupError`, а не молчаливый ноль."""
    account = await _seed_account(db_session)

    with pytest.raises(LookupError, match=str(account.id + 1000)):
        await set_manual_phone(db_session, account.id + 1000, "8 999 000-00-01")


@pytest.mark.asyncio
async def test_an_automatic_write_to_a_missing_account_is_named_missing(db_session: AsyncSession):
    """ТРАСЕР WR-05: строки с таким id нет — исход `MISSING`, а не `KEPT`.

    `KEPT` значит «строка есть, номер в ней уже есть или он ручной». Скрипт
    дозаполнения Фазы 20 подводит итог по исходам, и удалённый аккаунт,
    названный `KEPT`, посчитался бы как «пользователь успел первым».
    """
    account = await _seed_account(db_session)

    outcome = await fill_reported_phone(db_session, account.id + 1000, "79991234567")

    assert outcome is PhoneWrite.MISSING, f"отсутствующая строка названа {outcome} (WR-05)"
    assert await _row(db_session, account.id) == UNKNOWN


@pytest.mark.asyncio
async def test_the_existence_probe_runs_only_after_an_update_that_touched_no_row(
    db_session: AsyncSession, monkeypatch
):
    """Проба существования — только классификация нулевого исхода, ПОСЛЕ записи.

    Путь `WRITTEN` — ровно один оператор, условный `Update`: промежутка
    «прочитать — решить — записать» нет (D-07). Пути `KEPT` и `MISSING` — два
    оператора, первым `Update`, вторым `Select` пробы. Проба перед записью
    вернула бы запрещённую пару чтение-проверка-запись.
    """
    seeded = await _seed_account(db_session)
    kept = await _add_account(db_session, seeded.user_id)
    await set_manual_phone(db_session, kept.id, "8 999 000-00-01")

    paths = {}
    for name, account_id in (
        ("written", seeded.id),
        ("kept", kept.id),
        ("missing", seeded.id + 1000),
    ):
        statements = _record_statements(db_session, monkeypatch)
        outcome = await fill_reported_phone(db_session, account_id, "79991234567")
        monkeypatch.undo()
        paths[name] = (outcome, [type(s) for s in statements])

    assert paths["written"] == (PhoneWrite.WRITTEN, [Update]), paths
    assert paths["kept"] == (PhoneWrite.KEPT, [Update, Select]), paths
    assert paths["missing"] == (PhoneWrite.MISSING, [Update, Select]), paths


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw",
    [None, "", "garbage", "79991234567"],
    ids=["none", "empty", "garbage", "parseable"],
)
async def test_recording_an_account_never_added_to_the_session_raises(
    db_session: AsyncSession, monkeypatch, raw
):
    """Мастер забыл `session.add`: громкий `ValueError` при ЛЮБОМ ответе источника.

    Ни одного оператора, `id` остаётся `None` (WR-05, IN-07). До плана 16-08
    писатель исполнял UPDATE `WHERE id IS NULL` и молча возвращал `KEPT`; до
    плана 16-14 проверка стояла после нормализации, и на мусоре (`None`, `''`,
    `'garbage'`) — самом частом пути старого воркера без номера (PHONE-15) —
    писатель молча отвечал `UNPARSEABLE`. Поэтому правило параметризовано и
    неразбираемыми входами, а не только разбираемым номером.
    """
    seeded = await _seed_account(db_session)
    account = MessengerAccount(
        user_id=seeded.user_id, type="wa", credentials="creds", status="active"
    )
    calls = _count_executes(db_session, monkeypatch)

    with pytest.raises(ValueError) as raised:
        await record_reported_phone(db_session, account, raw)

    assert str(raised.value) == ACCOUNT_NOT_IN_SESSION
    assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов вне сессии"
    assert account.id is None


@pytest.mark.asyncio
@pytest.mark.parametrize("where", ["detached", "foreign"])
async def test_recording_an_account_outside_this_session_raises(
    db_session: AsyncSession, monkeypatch, where
):
    """Объект вне сессии писателя — отсоединённый или чужой: отказ, строка цела.

    У такого объекта `id` есть, и прежде писатель исполнял по нему условный
    UPDATE в чужой для объекта сессии и зеркалил значение на объект (IN-07).
    Признак «объект этой сессии» — `inspect(account).session`; у отсоединённого
    (`expunge`) он пуст, у объекта чужой сессии равен той, другой сессии, и оба
    получают `ACCOUNT_NOT_IN_SESSION`.

    Проверке членства база не нужна: она читает только `inspect(account).session`
    и не отдаёт ни одного оператора. Поэтому чужая сессия моделируется новой
    непривязанной `AsyncSession()` (ревью IN-10). Антивакуум строки `foreign`:
    объект действительно в другой сессии, а не просто отсоединён.

    Летопись. До плана 16-19 (ревью IN-10) правило было параметризовано одной
    строкой `detached` под видом матрицы, а случай чужой сессии объяснялся
    ложной причиной: будто вторая сессия к базе `:memory:` в фикстуре не
    гарантирована.
    """
    account = await _seed_account(db_session)
    account_id = account.id
    db_session.expunge(account)
    other = AsyncSession()
    try:
        if where == "foreign":
            other.add(account)
            assert inspect(account).session is other.sync_session, (
                "объект не попал в чужую сессию — строка foreign проверяла бы отсоединённый"
            )
        calls = _count_executes(db_session, monkeypatch)

        with pytest.raises(ValueError) as raised:
            await record_reported_phone(db_session, account, "79991234567")

        assert str(raised.value) == ACCOUNT_NOT_IN_SESSION
        assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов вне сессии ({where})"
    finally:
        await other.close()
    monkeypatch.undo()
    assert await _row(db_session, account_id) == UNKNOWN


@pytest.mark.asyncio
async def test_recording_garbage_for_a_pending_member_issues_nothing(
    db_session: AsyncSession, monkeypatch
):
    """Член сессии, ожидающий вставки, с мусором от источника: базу не трогаем.

    Правило закрепляет выбор механики плана 16-14: проверка членства в сессии
    не отдаёт операторов и не сбрасывает сессию. Вариант «сбросить и проверить
    id до нормализации» сбросил бы ожидающий объект на этом пути (и вставки
    других ожидающих объектов сессии раньше времени) — и правило покраснело бы
    на `account.id`. Путь мусора у члена сессии прежний: старый воркер без
    номера оставляет номер неизвестным, вход не падает (PHONE-15).
    """
    seeded = await _seed_account(db_session)
    account = MessengerAccount(
        user_id=seeded.user_id, type="wa", credentials="creds", status="active"
    )
    db_session.add(account)
    calls = _count_executes(db_session, monkeypatch)

    outcome = await record_reported_phone(db_session, account, None)

    assert outcome is PhoneWrite.UNPARSEABLE
    assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов на мусоре"
    assert account.id is None, "сессия сброшена на пути мусора"


@pytest.mark.asyncio
async def test_each_refusal_of_the_recorder_names_its_own_cause(
    db_session: AsyncSession, monkeypatch
):
    """ТРАСЕР IN-10: каждый отказ `record_reported_phone` называет свою причину.

    Решение владельца О-8 (2026-10-12), ревью IN-10. У писателя две линии
    отказа, и причины у них разные:

    - проверка членства (первая строка писателя): объект не принадлежит сессии
      писателя — не добавлен, отсоединён или живёт в чужой сессии. Текст
      нейтрален и не советует действия: совет «добавьте его через session.add»
      для объекта чужой сессии падает `InvalidRequestError` (замер
      верификатора);
    - вторая линия после `flush`: объект УЖЕ член сессии, но сброс не дал ему
      `id`. Текст о членстве здесь неверен, поэтому у линии своя константа
      `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`.

    Вторая линия достижима: член сессии, ожидающий вставки, при сбросе,
    подменённом пустым, проходит проверку членства и нормализацию и остаётся
    без `id`. Писатель при этом не отдаёт ни одного оператора.
    """
    assert "session.add" not in ACCOUNT_NOT_IN_SESSION, (
        "совет session.add неверен для объекта чужой сессии — там он падает "
        "InvalidRequestError"
    )

    seeded = await _seed_account(db_session)
    account = MessengerAccount(
        user_id=seeded.user_id, type="wa", credentials="creds", status="active"
    )
    db_session.add(account)

    async def flush_that_assigns_no_id(*args, **kwargs):
        return None

    monkeypatch.setattr(db_session, "flush", flush_that_assigns_no_id)
    calls = _count_executes(db_session, monkeypatch)

    with pytest.raises(ValueError) as raised:
        await record_reported_phone(db_session, account, "79991234567")

    assert str(raised.value) == writer_module.ACCOUNT_WITHOUT_ID_AFTER_FLUSH
    assert str(raised.value) != ACCOUNT_NOT_IN_SESSION, (
        "вторая линия называет членство в сессии, а объект уже в сессии"
    )
    assert calls["n"] == 0, f"писатель отдал {calls['n']} операторов на отказе"
    assert account.id is None


@pytest.mark.asyncio
async def test_the_writers_do_not_commit(db_session: AsyncSession):
    """Транзакцией владеет вызывающий: откат возвращает «неизвестен»."""
    account = await _seed_account(db_session)
    account_id = account.id  # после отката объект истёк; id берётся заранее

    outcome = await fill_reported_phone(db_session, account_id, "79991234567")
    assert outcome is PhoneWrite.WRITTEN
    await db_session.rollback()

    assert await _row(db_session, account_id) == UNKNOWN
