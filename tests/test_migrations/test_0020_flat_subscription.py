"""Round-trip ревизии 0020: плоская подписка, снятие валюты сообщений, бесплатный доступ.

⚠️ ЭТОТ ФАЙЛ — ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ТЕКСТ РЕВИЗИИ ВООБЩЕ ИСПОЛНЯЕТСЯ. Суита
строит схему через `Base.metadata.create_all` (`tests/conftest.py`) и о
существовании Alembic не знает: полторы тысячи её тестов могут быть зелёными при
ревизии, которая на боевой базе оборвётся на первом же операторе. Совпадение
модели и ревизии здесь не предполагается — проверяется.

Значимость round-trip у ЭТОЙ ревизии выше, чем у соседних, по двум причинам.
Первая: она НЕОБРАТИМА ПО ДАННЫМ — снимает тариф каждой подписки и две таблицы
учёта сообщений, и откат вернёт схему, но не значения. Вторая: она правит ДАННЫЕ
трёх популяций, а не только схему, и неверная классификация популяции проявилась
бы у пользователя, а не в прогоне.

⚠️ БОЕВАЯ БАЗА ПРОВЕРЕНА `alembic current` 2026-08-21 И СТОИТ НА `0019` — то есть
на текущей голове репозитория. Очередь невыкаченных ПУСТА, и `0020` применится на
ближайшем выкате первой и единственной. Это РАСХОДИТСЯ с записью в
`.planning/STATE.md` (и с докстрингами ревизий `0018`/`0019`), где сказано про
`0012` и семь невыкаченных: очередь `0013`…`0019` уже пройдена. Тест
`test_the_revision_names_its_place_in_the_unapplied_queue` закрепляет ФАКТ, а не
запись документа — именно потому, что неверное число он закрепил бы как правду.

**Файловая база, а не база в памяти.** Alembic открывает собственное соединение
(`alembic/env.py` создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия `0019` и целевая `0020` названы явно.** Прогон от нуля на
SQLite до цели не доходит: ревизия `0005` использует `op.drop_constraint`, на
котором Alembic под SQLite поднимает `NotImplementedError`. Это свойство ЧУЖИХ
ревизий, к `0020` отношения не имеющее. Поэтому тест сам приводит базу в
состояние «схема на ревизии 0019 + посев трёх популяций», отмечает это штампом и
запускает НАСТОЯЩИЕ `upgrade`/`downgrade`.
"""

import ast
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
REVISION_PATH = REPO_ROOT / "alembic" / "versions" / "0020_flat_subscription.py"

COLUMN_PLAN = "plan"
COLUMN_FREE_ACCESS = "has_free_access"

# Длина пробного окна. Выписана здесь литералом ПО ТОЙ ЖЕ ПРИЧИНЕ, по которой она
# выписана в самой ревизии: тест обязан проверять шаг, выполненный на бою, а не
# сегодняшнее значение `app.constants.TRIAL_DAYS`. Разойдись они — падение этого
# теста и есть верный сигнал, что кто-то поменял константу, не тронув ревизию.
TRIAL_DAYS = 5

# Схема на момент ревизии 0019. Состав колонок сверен по
# `0001_initial_schema.py` (таблицы `users` и `subscriptions`),
# `0009_add_message_balance_and_payment_tables.py` (обе таблицы валюты сообщений
# и `payments`), `0010_add_is_unlimited.py` (колонка безлимита),
# `0017_payment_kind_and_plan.py` (`kind`, `plan`, снятие NOT NULL с
# `messages_count`), `0018_subscriptions_unique_user.py` (частичный уникальный
# индекс) и `0019_payment_switch_authorized.py` (`switch_authorized`).
#
# ⚠️ ЧАСТИЧНЫЙ ИНДЕКС ВОСПРОИЗВОДИТСЯ ДОСЛОВНО, А НЕ ОПУСКАЕТСЯ. Без него тест
# `test_the_active_subscription_index_does_not_hold_the_plan_column` проверял бы
# пустоту, а вставка популяции без подписки прошла бы там, где на бою упала бы.
SCHEMA_AT_0019 = """
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE subscriptions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX uq_subscriptions_active_user
    ON subscriptions (user_id) WHERE is_active;

CREATE TABLE message_balances (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    balance INTEGER NOT NULL DEFAULT 0,
    free_balance_reset_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_unlimited BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE balance_transactions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    payment_id VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE payments (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    yookassa_payment_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    amount_value VARCHAR(50) NOT NULL,
    amount_currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
    messages_count INTEGER,
    package_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at DATETIME,
    kind VARCHAR(50) NOT NULL DEFAULT 'package',
    plan VARCHAR(50),
    switch_authorized BOOLEAN
);
"""

# ЧЕТЫРЕ ПОЛЬЗОВАТЕЛЯ, ТРИ ПОПУЛЯЦИИ.
#
#   1 — П-о-1: строки подписки нет вовсе. Ревизия обязана её ВСТАВИТЬ.
#   2 — П-о-2: активная строка бесплатного тарифа, срок далеко в будущем.
#       Ревизия обязана ПЕРЕСТАВИТЬ срок на окно от момента исполнения — в данном
#       случае НАЗАД, и это верно: бесплатный срок не покупался.
#   3 — П-о-3: активная строка платного тарифа со сроком В ПРОШЛОМ. Ревизия НЕ
#       трогает его («переносится без пересчёта» — D-G).
#   4 — П-о-3 на ГРАНИЦЕ: активная строка платного тарифа со сроком РОВНО в
#       момент исполнения. Проставляется тестом отдельно, потому что «ровно» надо
#       вычислить в момент прогона, а не записать литералом.
#
# У пользователя 1 есть ДЕАКТИВИРОВАННАЯ строка истории: без неё «нет активной
# строки» было бы неотличимо от «нет ни одной строки», и условие вставки,
# написанное по сроку вместо активности, зеленело бы на этом посеве.
SEED_USERS = """
INSERT INTO users (id, email, name) VALUES
    (1, 'nobody@test.com',  'Без подписки'),
    (2, 'free@test.com',    'Бесплатный'),
    (3, 'paid@test.com',    'Платящий'),
    (4, 'edge@test.com',    'На границе');
"""

SEED_PAYMENTS = """
INSERT INTO payments
    (id, user_id, yookassa_payment_id, status, amount_value, amount_currency,
     messages_count, package_name, kind, plan)
VALUES
    (1, 3, 'yoo_sub', 'succeeded', '4900.00', 'RUB', NULL, NULL,          'subscription', 'pro'),
    (2, 2, 'yoo_pkg', 'succeeded', '149.00',  'RUB', 100,  '100 messages', 'package',      NULL);
"""

SEED_CURRENCY = """
INSERT INTO message_balances (id, user_id, balance, is_unlimited)
VALUES (1, 2, 42, true);

INSERT INTO balance_transactions (id, user_id, amount, balance_after, type)
VALUES (1, 2, 100, 142, 'purchase');
"""


def _columns(db_path: Path, table: str) -> dict[str, sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return {
            row["name"]: row for row in conn.execute(f"PRAGMA table_info({table})")
        }
    finally:
        conn.close()


def _tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        conn.close()


def _rows(db_path: Path, sql: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql)]
    finally:
        conn.close()


def _scalar(db_path: Path, sql: str):
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(sql).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _execute(db_path: Path, sql: str, params: tuple = ()) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _expiry_of(db_path: Path, user_id: int) -> datetime:
    """Срок активной строки пользователя, приведённый к UTC.

    SQLite отдаёт `DATETIME` наивным, и сравнение с aware-датой упало бы
    TypeError — тем же способом, каким это лечит `normalize_utc` в приложении.
    """
    raw = _scalar(
        db_path,
        f"SELECT expires_at FROM subscriptions WHERE user_id = {user_id} AND is_active",
    )
    assert raw is not None, f"у пользователя {user_id} нет активной строки"
    parsed = datetime.fromisoformat(str(raw))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _revision_source() -> str:
    return REVISION_PATH.read_text(encoding="utf-8")


@pytest.fixture
def db_at_0019(tmp_path: Path, monkeypatch) -> tuple[Config, Path, datetime]:
    """База со схемой на ревизии 0019, посевом трёх популяций и штампом 0019.

    Третьим элементом возвращается момент, снятый НЕПОСРЕДСТВЕННО перед выдачей
    фикстуры: он служит нижней границей «момента исполнения ревизии». Сравнивать
    с ним, а не с `datetime.now()` в теле теста, обязательно — между фикстурой и
    утверждением проходит настоящий прогон Alembic, и его длительность попала бы
    в допуск.
    """
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_AT_0019)
        conn.executescript(SEED_USERS)
        conn.executescript(SEED_PAYMENTS)
        conn.executescript(SEED_CURRENCY)
        conn.commit()
    finally:
        conn.close()

    far_future = datetime(2099, 1, 1, tzinfo=timezone.utc)
    long_past = datetime(2020, 1, 1, tzinfo=timezone.utc)

    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (10, 1, 'free', ?, false)",
        (long_past.isoformat(),),
    )
    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (20, 2, 'free', ?, true)",
        (far_future.isoformat(),),
    )
    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (30, 3, 'pro', ?, true)",
        (long_past.isoformat(),),
    )

    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL любому значению из alembic.ini. Переменная
    # подменяется ЯВНО: без этого ревизия ушла бы на адрес из окружения
    # разработчика — то есть на живую базу.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0019")
    return config, db_path, datetime.now(timezone.utc)


# --- 1-2: схема до и после ----------------------------------------------------


def test_the_plan_column_and_both_currency_tables_exist_before_the_upgrade(db_at_0019):
    """Половина утверждения о ревизии: ДО наката всё три предмета на месте.

    Без неё парные проверки ниже зеленели бы и на схеме, где ни колонки, ни
    таблиц не было изначально, — то есть не доказывали бы, что ревизия что-то
    сняла.
    """
    _, db_path, _ = db_at_0019

    assert COLUMN_PLAN in _columns(db_path, "subscriptions")
    assert "message_balances" in _tables(db_path)
    assert "balance_transactions" in _tables(db_path)
    assert COLUMN_FREE_ACCESS not in _columns(db_path, "subscriptions")


def test_the_upgrade_drops_three_things_and_adds_the_free_access_flag(db_at_0019):
    """После наката тарифа и обеих таблиц нет, а признак доступа есть и НЕ NULL.

    Форма новой колонки проверяется ПО СХЕМЕ, а не по тексту ревизии: `NOT NULL`
    со значением по умолчанию, соответствующим лжи, — это то, что делает признак
    определённым у КАЖДОЙ строки, включая вставленные в обход ORM самой ревизией.
    """
    config, db_path, _ = db_at_0019

    command.upgrade(config, "0020")

    columns = _columns(db_path, "subscriptions")
    assert COLUMN_PLAN not in columns
    assert "message_balances" not in _tables(db_path)
    assert "balance_transactions" not in _tables(db_path)

    assert COLUMN_FREE_ACCESS in columns
    assert columns[COLUMN_FREE_ACCESS]["notnull"] == 1, "признак допускает NULL"
    assert columns[COLUMN_FREE_ACCESS]["dflt_value"] == "'0'", columns[
        COLUMN_FREE_ACCESS
    ]["dflt_value"]

    assert _scalar(db_path, f"SELECT {COLUMN_FREE_ACCESS} FROM subscriptions") == 0


# --- 3-6: три популяции и граница --------------------------------------------


def test_a_user_without_a_subscription_row_is_given_one(db_at_0019):
    """П-о-1: пользователю без активной строки ВСТАВЛЕНА строка с пробным окном.

    Это самая дорогая из трёх операций: без неё выкат мгновенно отрезал бы от
    продукта большинство — до плоской модели строка заводилась ТОЛЬКО
    подтверждённым платежом. Деактивированная строка истории у этого
    пользователя есть, и она НЕ считается: условие смотрит на активность.
    """
    config, db_path, before = db_at_0019
    assert (
        _scalar(db_path, "SELECT COUNT(*) FROM subscriptions WHERE user_id = 1 AND is_active")
        == 0
    ), "посев неверен: у П-о-1 уже есть активная строка"

    command.upgrade(config, "0020")

    granted = _expiry_of(db_path, 1)
    assert granted >= before + timedelta(days=TRIAL_DAYS)
    assert granted <= datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)

    # Строка истории не воскрешена и не переписана — вставлена ВТОРАЯ.
    assert _scalar(db_path, "SELECT COUNT(*) FROM subscriptions WHERE user_id = 1") == 2
    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 10") == 0


def test_a_free_plan_row_gets_the_trial_window_from_the_moment_of_the_run(db_at_0019):
    """П-о-2: активной бесплатной строке срок ПЕРЕСТАВЛЕН на окно от исполнения.

    Посев даёт этой строке срок в 2099 году, то есть заведомо ДАЛЬШЕ окна:
    переставленный срок обязан оказаться БЛИЖЕ прежнего. Посей мы срок в
    прошлом — тест зеленел бы и на реализации, которая только продлевает.
    """
    config, db_path, before = db_at_0019

    command.upgrade(config, "0020")

    moved = _expiry_of(db_path, 2)
    assert moved >= before + timedelta(days=TRIAL_DAYS)
    assert moved <= datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS)
    assert moved < datetime(2099, 1, 1, tzinfo=timezone.utc), (
        "срок бесплатной строки не тронут — операция П-о-2 не исполнилась"
    )


def test_a_paid_row_keeps_its_date_even_when_it_is_already_in_the_past(db_at_0019):
    """П-о-3: платной строке срок НЕ тронут, в том числе просроченный (D-G).

    ⚠️ УТВЕРЖДАЕТСЯ РАВЕНСТВО ПРЕЖНЕЙ ДАТЕ, А НЕ «НЕ ПРОБНОЕ ОКНО». Платящему
    нельзя ни отнять оплаченное, ни подарить окно: и то и другое — решение о
    чужих деньгах, принятое миграцией. Срок в прошлом посеян намеренно: соблазн
    «починить» просроченную платную строку выглядит добром и им не является.
    """
    config, db_path, _ = db_at_0019

    command.upgrade(config, "0020")

    assert _expiry_of(db_path, 3) == datetime(2020, 1, 1, tzinfo=timezone.utc)


def test_a_row_expiring_exactly_at_the_moment_of_the_run_counts_as_expired(db_at_0019):
    """⚠️ ГРАНИЦА ЗАКРЫТА В ПОЛЬЗУ ИСТЕЧЕНИЯ, И ЭТО ЗАКРЕПЛЕНО, А НЕ ОБЪЯВЛЕНО.

    Строка с `expires_at`, равным моменту исполнения, живой НЕ считается —
    `subscription_is_live` сравнивает СТРОГО. Ревизия обязана согласиться с
    предикатом: разойдись они на строгости, человек, чья секунда совпала с
    миграцией, получил бы от миграции один ответ, а от продукта противоположный.

    Проверяется наблюдаемое следствие: платная строка на границе НЕ получает
    пробного окна (её не сочли «истёкшей и потому подлежащей окну») и НЕ
    сохраняется как купленная сверх срока — она остаётся ровно там, где была, и
    доступ по ней закрыт.
    """
    config, db_path, _ = db_at_0019
    edge = datetime.now(timezone.utc).replace(microsecond=0)
    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (40, 4, 'pro', ?, true)",
        (edge.isoformat(),),
    )

    command.upgrade(config, "0020")

    after = _expiry_of(db_path, 4)
    assert after == edge, "срок строки на границе изменён ревизией"
    assert after < datetime.now(timezone.utc), (
        "строка на границе осталась живой — граница закрыта не в ту сторону"
    )


# --- 7-8: журнал денег и односторонность --------------------------------------


def test_no_payment_row_is_lost_by_the_upgrade_or_the_downgrade(db_at_0019):
    """Журнал платежей не теряет ни строки ни накатом, ни откатом (D-H).

    Утверждение не декоративное: `payments` — след ДЕНЕГ, и молчаливая пропажа
    строки обнаружилась бы уже после наката на бой, когда откатывать поздно.
    Проверяются не только идентификаторы, но и колонки, описывающие ПРОДАННОЕ:
    вид, тариф платежа и количество сообщений остаются как записаны — ревизия не
    имеет права переписать историю сделок задним числом.
    """
    config, db_path, _ = db_at_0019
    before = _rows(
        db_path,
        "SELECT id, kind, plan, messages_count, amount_value FROM payments ORDER BY id",
    )
    assert before, "посев журнала платежей пуст — тест проверял бы ничто"

    command.upgrade(config, "0020")
    assert (
        _rows(
            db_path,
            "SELECT id, kind, plan, messages_count, amount_value FROM payments ORDER BY id",
        )
        == before
    )

    command.downgrade(config, "0019")
    assert (
        _rows(
            db_path,
            "SELECT id, kind, plan, messages_count, amount_value FROM payments ORDER BY id",
        )
        == before
    )


def test_the_downgrade_restores_the_schema_and_none_of_the_three_losses(db_at_0019):
    """⚠️ ОДНОСТОРОННОСТЬ ЗАКРЕПЛЕНА ТЕСТОМ, А НЕ ТОЛЬКО ДОКСТРИНГОМ.

    Тест фиксирует ФАКТ, а не объявляет его желаемым: откат возвращает колонку
    тарифа и обе таблицы, но тариф у КАЖДОЙ строки становится бесплатным (включая
    плативших), а таблицы возвращаются ПУСТЫМИ. Если однажды появится ревизия,
    умеющая это откатывать по-настоящему, падение ЭТОГО теста будет верным
    сигналом, что поведение изменилось, а не поломкой.
    """
    config, db_path, _ = db_at_0019
    command.upgrade(config, "0020")

    command.downgrade(config, "0019")

    columns = _columns(db_path, "subscriptions")
    assert COLUMN_PLAN in columns, "откат не вернул колонку тарифа"
    assert COLUMN_FREE_ACCESS not in columns, "откат не снял признак доступа"
    assert {"message_balances", "balance_transactions"} <= _tables(db_path)

    # Потеря 1: тариф платившего пользователя 3 не вернулся.
    assert _scalar(db_path, "SELECT plan FROM subscriptions WHERE id = 30") == "free"
    # Потери 2 и 3: обе таблицы пусты.
    assert _scalar(db_path, "SELECT COUNT(*) FROM message_balances") == 0
    assert _scalar(db_path, "SELECT COUNT(*) FROM balance_transactions") == 0


def test_the_downgrade_restores_the_currency_tables_as_of_0019_not_0009(db_at_0019):
    """Откат возвращает состав колонок на момент `0019`, а не на момент `0009`.

    Колонка безлимита добавлена в таблицу остатка ревизией `0010`. Откат,
    вернувший состав ревизии, заводившей таблицу, оставил бы базу в состоянии,
    которого в истории проекта не существовало ни секунды, — и следующий откат,
    до `0009`, упал бы на снятии колонки, которой нет.
    """
    config, db_path, _ = db_at_0019
    before = set(_columns(db_path, "message_balances"))
    before_journal = set(_columns(db_path, "balance_transactions"))

    command.upgrade(config, "0020")
    command.downgrade(config, "0019")

    assert set(_columns(db_path, "message_balances")) == before
    assert set(_columns(db_path, "balance_transactions")) == before_journal


# --- 9-14: утверждения о самой ревизии ----------------------------------------


def test_revision_0020_continues_0019():
    """0020 продолжает 0019 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0020").down_revision == "0019"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013/0014/0017.

    Импорт из `app.*` связал бы уже применённую миграцию с текущим кодом, и
    переименование атрибута задним числом изменило бы смысл давно выполненного
    шага. Здесь у правила есть и второе основание: ревизия снимает МОДЕЛИ, из
    которых могла бы импортировать, — файл, импортирующий удалённый модуль, не
    собрался бы вовсе.
    """
    source = _revision_source()

    assert "from app." not in source
    assert "import app" not in source


def test_the_revision_names_its_place_in_the_unapplied_queue():
    """⚠️ ЧИТАТЕЛЬ РЕВИЗИИ УЗНАЁТ СОСТОЯНИЕ ОЧЕРЕДИ ИЗ НЕЁ САМОЙ.

    Боевая база проверена `alembic current` 2026-08-21 и стоит на `0019` —
    очередь невыкаченных ПУСТА, и эта ревизия применится на ближайшем выкате.
    Человек, открывший файл перед выкатом, обязан прочесть это на месте:
    планировочные документы он в этот момент не открывает, а записанное в них
    число (`0012`, семь невыкаченных) на эту дату уже неверно.

    ⚠️ ЗАКРЕПЛЯЕТСЯ ФАКТ, А НЕ ЧИСЛО ИЗ ДОКУМЕНТА, И ЭТО ВЕСЬ СМЫСЛ ЭТОГО ТЕСТА.
    Конвенция требует, чтобы ревизия называла своё место; тест превращает
    названное в утверждение — поэтому неверное число он закрепил бы как правду.
    """
    source = _revision_source()

    assert "0019" in source, "ревизия не называет ревизию, на которой стоит бой"
    assert "2026-08-21" in source, "ревизия не называет дату проверки боевой базы"
    assert "alembic current" in source, (
        "ревизия не называет, ЧЕМ получено состояние очереди — читатель не сможет "
        "перепроверить"
    )


def test_the_revision_does_not_use_batch_mode():
    """`batch_alter_table` здесь не нужен, и его отсутствие — утверждение.

    PostgreSQL снимает колонку нативно; SQLite умеет `DROP COLUMN` с версии 3.35.
    Batch-режим пересоздавал бы таблицу подписок целиком — лишний риск на
    таблице, которую эта же ревизия и правит тремя операциями над данными.
    """
    assert "batch_alter_table(" not in _revision_source()


def _module_string_constants(tree: ast.AST) -> dict[str, str]:
    """Модульные константы вида `ИМЯ = "строка"` — чтобы разрешать аргументы.

    Ревизия по правилу проекта выписывает имена таблиц и колонок КОНСТАНТАМИ, а
    не голыми литералами в вызовах. Без разрешения имён проверка порядка искала
    бы литерал там, где стоит ссылка, и молча ничего не находила бы — то есть
    была бы зелёной всегда.
    """
    resolved: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                resolved[target.id] = node.value.value
    return resolved


def _argument_value(argument: ast.AST, constants: dict[str, str]) -> str | None:
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    if isinstance(argument, ast.Name):
        return constants.get(argument.id)
    return None


def _upgrade_body_positions() -> tuple[int, int]:
    """Позиции первой операции над данными и снятия колонки тарифа в `upgrade`.

    Считаются по СИНТАКСИЧЕСКОМУ ДЕРЕВУ, а не поиском подстроки: подстрока
    нашлась бы и в докстринге, и в комментарии, и порядок «объяснения» выдала бы
    за порядок операций.
    """
    tree = ast.parse(_revision_source())
    constants = _module_string_constants(tree)
    upgrade = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade"
    )

    first_data_op = None
    drop_plan = None
    for node in ast.walk(upgrade):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue

        if func.attr == "execute":
            if first_data_op is None or node.lineno < first_data_op:
                first_data_op = node.lineno

        if (
            func.attr == "drop_column"
            and isinstance(func.value, ast.Name)
            and func.value.id == "op"
        ):
            values = [_argument_value(item, constants) for item in node.args]
            if COLUMN_PLAN in values:
                drop_plan = node.lineno

    assert first_data_op is not None, "в накате нет ни одной операции над данными"
    assert drop_plan is not None, "в накате нет снятия колонки тарифа"
    return first_data_op, drop_plan


def test_the_order_check_resolves_names_and_would_see_a_swap():
    """НЕГАТИВНЫЙ КОНТРОЛЬ: у проверки порядка есть зубы, и это доказывает машина.

    Без него `test_every_data_operation_runs_before_the_plan_column_is_dropped`
    зеленел бы и при разборе, который не находит НИ ОДНОЙ операции: помощник
    падал бы на своих же `assert`, а не сообщал бы о порядке. Здесь разбирается
    СИНТЕТИЧЕСКИЙ исходник с ОБРАТНЫМ порядком, и требуется, чтобы разрешение
    имён нашло оба вызова и увидело перестановку.
    """
    synthetic = (
        'COLUMN_PLAN = "plan"\n'
        "def upgrade():\n"
        '    op.drop_column("subscriptions", COLUMN_PLAN)\n'
        "    connection.execute(_RESET_FREE_EXPIRY)\n"
    )
    tree = ast.parse(synthetic)
    constants = _module_string_constants(tree)

    assert constants["COLUMN_PLAN"] == COLUMN_PLAN, (
        "разрешение модульных констант не работает — проверка порядка искала бы "
        "литерал там, где стоит ссылка, и была бы зелёной всегда"
    )

    upgrade = tree.body[1]
    calls = [node for node in ast.walk(upgrade) if isinstance(node, ast.Call)]
    drop = next(
        node
        for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "drop_column"
    )
    data = next(
        node
        for node in calls
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute"
    )

    assert COLUMN_PLAN in [_argument_value(item, constants) for item in drop.args]
    assert drop.lineno < data.lineno, (
        "синтетический образец не воспроизводит перестановку — контроль пуст"
    )


def test_every_data_operation_runs_before_the_plan_column_is_dropped():
    """⚠️ ПОРЯДОК НЕСУЩИЙ: правка данных ДО снятия колонки, и это необратимо.

    Уронив колонку первой, отличить бесплатного подписчика от платящего было бы
    НЕЧЕМ — второго места, где тариф записан, у подписки нет. Перестановка двух
    операторов выглядела бы безобидной и стоила бы платящим их сроков, поэтому
    порядок закреплён машиной, а не абзацем.
    """
    first_data_op, drop_plan = _upgrade_body_positions()

    assert first_data_op < drop_plan, (
        f"первая операция над данными на строке {first_data_op}, снятие колонки "
        f"тарифа на строке {drop_plan} — порядок обратный несущему"
    )


def test_the_revision_performs_no_operation_on_the_payment_journal():
    """Журнал платежей не тронут НИ ОДНОЙ операцией (решение D-H, T-05.1-10).

    Проверяются два множества, и оба выводятся из дерева: аргументы вызовов `op.*`
    (схемные операции) и тексты `sa.text` (операции над данными). Греп по всему
    файлу здесь не годится — имя таблицы стоит в докстринге и в предупреждении
    отката, и оба места ОБЯЗАНЫ его называть.
    """
    tree = ast.parse(_revision_source())
    touched: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_op_call = (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "op"
        )
        is_sa_text = (
            isinstance(func, ast.Attribute)
            and func.attr == "text"
            and isinstance(func.value, ast.Name)
            and func.value.id == "sa"
        )
        if not (is_op_call or is_sa_text):
            continue
        for argument in node.args:
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                if "payments" in argument.value:
                    touched.append(f"строка {node.lineno}: {argument.value[:60]}")

    assert not touched, (
        "ревизия обращается к журналу платежей:\n" + "\n".join(touched)
    )


def test_the_active_subscription_index_does_not_hold_the_plan_column(db_at_0019):
    """Колонка тарифа не участвует в частичном уникальном индексе — иначе SQLite
    откажет в её снятии.

    Проверяется на ЖИВОЙ базе фикстуры, а не по тексту ревизии `0018`: предмет
    утверждения — то, что увидит SQLite в момент `DROP COLUMN`, а не то, что
    написано в файле, который эту схему когда-то создал.
    """
    _, db_path, _ = db_at_0019

    indexed = [
        row["name"]
        for row in _rows(db_path, "PRAGMA index_info(uq_subscriptions_active_user)")
    ]

    assert indexed == ["user_id"], indexed
    assert COLUMN_PLAN not in indexed


def test_the_model_and_the_revision_agree_on_the_columns(db_at_0019):
    """Модель и ревизия описывают ОДНУ таблицу, а не две похожие.

    Суита строит схему через `Base.metadata.create_all`, поэтому расхождение
    модели с ревизией она не увидит ни одним обычным тестом: у неё колонка
    появится всегда, а на боевой базе — только если ревизия её добавила. Именно
    это утверждение и связывает снятие атрибута модели с ревизией в ОДИН коммит:
    в любом промежутке между ними оно красное.
    """
    from app.models.subscription import Subscription

    config, db_path, _ = db_at_0019

    command.upgrade(config, "0020")

    assert set(_columns(db_path, "subscriptions")) == set(
        Subscription.__table__.c.keys()
    )
