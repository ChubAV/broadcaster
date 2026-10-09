"""Единственный писатель номера телефона аккаунта (D-12, D-13).

ЗДЕСЬ — И ТОЛЬКО ЗДЕСЬ — НОМЕР ПОПАДАЕТ В КОЛОНКУ. Правило, ради которого
существует признак «указан вручную», одно: номер, который пользователь ввёл
сам, автоматический источник не затирает (D-07). Это правило держится, пока
писатель один. Второй писатель — мастер подключения, скрипт дозаполнения,
обработчик формы — со своей записью в колонку обходит его разом, и никакой
тест этого модуля такого обхода не заметит. Поэтому все пути записи сведены
сюда, а гейт плана 16-06 краснит суиту на любой записи номера вне этого файла.

ПОЧЕМУ УСЛОВИЕ ЖИВЁТ В САМОМ ОПЕРАТОРЕ. Автоисточник пишет одним условным
UPDATE: «записать номер, если номера ещё нет и он не ручной». Проверка и
запись — один оператор, поэтому между ними нет промежутка, в который
пользователь мог бы успеть сохранить ручной номер. Порядок решает СУБД, а не
Python: атомарность отдельного оператора одинаково дают и PostgreSQL, и SQLite,
на которой живёт суита, поэтому гонку можно проверить тестом (а блокировку
строки — нельзя: SQLite её игнорирует). Пара «прочитать номер, решить в
Python, записать» оставляла бы ровно такой промежуток: ручной номер,
сохранённый между чтением и записью, затирался бы автономером, а признак
«ручной» оставался бы поднятым над чужим номером. Тест гонки
`tests/test_application/test_account_phone_race.py` показывает эту потерю на
такой паре и её отсутствие здесь.

ЧТО МОДУЛЬ ДЕЛАЕТ:
- автоисточник для существующей строки (`fill_reported_phone`) и для только
  что созданной строки мастера (`record_reported_phone`) заполняют только
  неизвестный номер и НИКОГДА не ставят признак «ручной»;
- ручная запись (`set_manual_phone`) пишет всегда и ставит признак; очистка
  возвращает строку в «неизвестен» ОДНИМ оператором по обеим колонкам — CHECK
  `ck_messenger_accounts_manual_requires_phone` отвергает признак без номера,
  так что очистка одной колонки упала бы на нём.

ОТСУТСТВИЕ СТРОКИ НАЗЫВАЕТСЯ, А НЕ СКРЫВАЕТСЯ (ревью WR-05). Автоисточник
называет его исходом `PhoneWrite.MISSING`, ручная запись — `LookupError`.
Формы разные, потому что разные вызывающие: автоисточник зовут пакетом мастер
Фазы 19 и скрипт Фазы 20, и «строки нет» там — исход в счёте итогов
(«заполнено / ручной / номера нет / …»), а не авария; ручную запись зовёт
форма Фазы 18 для ОДНОЙ строки, и отсутствие там отвечает так же, как
несуществующий аккаунт. Общее у них одно: ни один писатель не выдаёт
отсутствие строки за другой исход.

ЧЕГО МОДУЛЬ НЕ ДЕЛАЕТ:
- не присваивает номер атрибуту ORM-объекта: запись идёт только операторами
  UPDATE, а на новый объект мастера значение кладётся как уже сохранённое
  (`set_committed_value`), чтобы ORM не выдала на коммите второй UPDATE;
- не коммитит: транзакцией владеет вызывающий (мастер Фазы 19, скрипт Фазы 20,
  форма Фазы 18);
- не проверяет владельца аккаунта: принимает только `account_id`, а проверку
  «аккаунт принадлежит пользователю» делает вызывающая страница Фазы 18;
- не пишет номер в журнал и не кладёт его в текст исключения (PHONE-21, D-11).

ОБЪЕКТ ТОЙ ЖЕ СЕССИИ УСТАРЕВАЕТ. Операторы идут с `synchronize_session=False`
— мимо identity map, исход берётся по числу затронутых строк. Загруженный в ту
же сессию объект аккаунта до `refresh` показывает прежний номер; исключение —
объект, переданный в `record_reported_phone`: ему записанное значение
отзеркаливается.
"""

from __future__ import annotations

import enum

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from app.models.messenger_account import MessengerAccount
from app.services.phone import normalize_manual, normalize_reported

ACCOUNT_NOT_IN_SESSION = "аккаунт не добавлен в сессию: после flush у него нет id"


class PhoneWrite(enum.Enum):
    """Исход записи автоисточника.

    `WRITTEN` — номер записан. `KEPT` — не ошибка: строка есть, номер в ней уже
    есть или он указан вручную; в гонке это и есть «пользователь успел первым».
    `MISSING` — строки с таким id нет (аккаунт удалён): отдельный исход в итоге
    скрипта дозаполнения Фазы 20, а не «оставлено». `UNPARSEABLE` — источник
    прислал мусор, к базе писатель не обращался.

    До плана 16-08 `KEPT` покрывал и отсутствие строки (ревью WR-05: Фаза 20
    посчитала бы удалённый аккаунт ручным).
    """

    WRITTEN = "written"
    KEPT = "kept"
    MISSING = "missing"
    UNPARSEABLE = "unparseable"


async def _fill_if_unknown(session: AsyncSession, account_id: int, e164: str) -> PhoneWrite:
    """Один условный UPDATE: номер пишется, только если его нет и он не ручной.

    Если оператор не тронул ни одной строки, второй оператор — проба
    существования строки — ТОЛЬКО классифицирует этот нулевой исход: `KEPT`
    (строка есть) или `MISSING` (строки нет, ревью WR-05). Проба идёт ПОСЛЕ
    записи и запись от неё не зависит, поэтому промежутка «прочитать — решить —
    записать» не появляется (D-07): на пути записи оператор по-прежнему один, и
    тест гонки этого изменения не замечает. Проба идёт через `session.execute`,
    а не `session.scalar`: стенд гонки и счётчики теста писателя видят
    операторы через `execute`, и проба мимо него стала бы им невидимой.
    Строку, удалённую между записью и пробой, проба честно называет `MISSING`.
    """
    result = await session.execute(
        update(MessengerAccount)
        .where(
            MessengerAccount.id == account_id,
            MessengerAccount.phone.is_(None),
            MessengerAccount.phone_is_manual.is_(False),
        )
        .values(phone=e164)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 1:
        return PhoneWrite.WRITTEN
    probe = await session.execute(
        select(exists().where(MessengerAccount.id == account_id))
    )
    return PhoneWrite.KEPT if probe.scalar() else PhoneWrite.MISSING


async def fill_reported_phone(session: AsyncSession, account_id: int, raw: object) -> PhoneWrite:
    """Автоисточник для существующей строки (дозаполнение, опрос воркера).

    Мусор от источника — `UNPARSEABLE` без обращения к базе: номер остаётся
    неизвестным, вход аккаунта из-за сбоя источника не падает.
    """
    e164 = normalize_reported(raw)
    if e164 is None:
        return PhoneWrite.UNPARSEABLE
    return await _fill_if_unknown(session, account_id, e164)


async def record_reported_phone(
    session: AsyncSession, account: MessengerAccount, raw: object
) -> PhoneWrite:
    """Автоисточник для строки, которую мастер подключения только что создал.

    Строка без `id` сначала сбрасывается в базу, затем пишется тем же условным
    оператором. При `WRITTEN` значение кладётся на объект как уже сохранённое:
    вызывающий видит номер без `refresh`, а объект не становится грязным.

    Объект, не добавленный в сессию, `flush` не вставляет, и `id` у него
    остаётся `None`. Прежде писатель исполнял UPDATE по `id IS NULL` и молча
    возвращал `KEPT` (ревью WR-05); теперь это громкий `ValueError` с текстом
    `ACCOUNT_NOT_IN_SESSION` до любого оператора — мастер Фазы 19 с забытым
    `session.add` узнаёт об ошибке сразу. Это ошибка вызывающего, а не исход.
    """
    e164 = normalize_reported(raw)
    if e164 is None:
        return PhoneWrite.UNPARSEABLE
    if account.id is None:
        await session.flush()
    if account.id is None:
        raise ValueError(ACCOUNT_NOT_IN_SESSION)
    outcome = await _fill_if_unknown(session, account.id, e164)
    if outcome is PhoneWrite.WRITTEN:
        set_committed_value(account, "phone", e164)
    return outcome


async def set_manual_phone(session: AsyncSession, account_id: int, text: str | None) -> str | None:
    """Ручная запись и очистка номера (форма Фазы 18). Возвращает сохранённое.

    `None`, пустая или пробельная строка — очистка: «неизвестен» одним
    оператором по обеим колонкам, после чего автоисточники снова вправе писать
    (PHONE-10). Иначе ввод нормализуется, и неверный ввод поднимает `PhoneError`
    ДО обращения к базе. Строки с таким `account_id` нет — `LookupError`.
    """
    statement = update(MessengerAccount).where(MessengerAccount.id == account_id)
    if text is None or not text.strip():
        e164 = None
        statement = statement.values(phone=None, phone_is_manual=False)
    else:
        e164 = normalize_manual(text)
        statement = statement.values(phone=e164, phone_is_manual=True)
    result = await session.execute(
        statement.execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise LookupError(f"аккаунт {account_id} не найден")
    return e164
