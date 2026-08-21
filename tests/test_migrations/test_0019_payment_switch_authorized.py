"""Round-trip ревизии 0019: записанный ответ гарда смены тарифа на платеже.

Файл существует по той же причине, что `test_0017_payment_kind_and_plan.py` и
`test_0018_subscriptions_unique_user.py`: суита строит схему через
`Base.metadata.create_all` (tests/conftest.py) и о существовании Alembic не знает,
поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте. Совпадение модели
и ревизии здесь не предполагается — проверяется.

Значимость round-trip у этой ревизии выше обычного, и причина не в её сложности,
а в её адресате. Накатить её на боевую базу сегодня нельзя: та стоит на `0012`
решением владельца (D-26), и `0019` встаёт СЕДЬМОЙ в очередь невыкаченных.
`uv run alembic upgrade head` в среде исполнителя тоже не проходит — локального
PostgreSQL нет. Значит единственное место, где текст ревизии вообще исполняется
настоящим Alembic, — этот файл, и он обязан исполнять именно `upgrade` и
`downgrade`, а не проверять их глазами.

**Файловая база, а не база в памяти.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия `0018` и целевая `0019` названы явно.** Прогон от нуля на
SQLite до цели не доходит: ревизия 0005 использует `op.drop_constraint`, а
Alembic на SQLite поднимает на нём `NotImplementedError`. Это свойство ЧУЖИХ
ревизий, к 0019 отношения не имеющее. Поэтому тест сам приводит базу в состояние
«схема `payments` на ревизии 0018 + строки в ней», отмечает это штампом и
запускает НАСТОЯЩИЕ `upgrade`/`downgrade`.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

COLUMN_NAME = "switch_authorized"

# Таблица платежей в том виде, в каком её застаёт ревизия 0019. Состав колонок
# сверен по `alembic/versions/0009_add_message_balance_and_payment_tables.py`
# (исходная таблица), `alembic/versions/0017_payment_kind_and_plan.py` (`kind`,
# `plan`, снятие NOT NULL с `messages_count`) и `app/models/payment.py`. Ревизия
# 0018 таблицу `payments` не трогает вовсе — она про `subscriptions`.
PAYMENTS_AT_0018 = """
CREATE TABLE payments (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    yookassa_payment_id VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    amount_value VARCHAR(50) NOT NULL,
    amount_currency VARCHAR(10) NOT NULL DEFAULT 'RUB',
    messages_count INTEGER,
    package_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at DATETIME,
    kind VARCHAR(50) NOT NULL DEFAULT 'package',
    plan VARCHAR(50)
);
"""

# Строка 1 — пакетный платёж, строка 2 — подписочный. Обе заведены ДО ревизии,
# то есть правила о смене тарифа у них никто не спрашивал.
SEED_ROWS = """
INSERT INTO payments
    (id, user_id, yookassa_payment_id, status, amount_value, amount_currency,
     messages_count, package_name, kind, plan)
VALUES
    (1, 7, 'yoo_pkg',  'succeeded', '149.00',  'RUB', 100,  '100 messages', 'package', NULL),
    (2, 7, 'yoo_sub',  'succeeded', '4900.00', 'RUB', NULL, NULL,           'subscription', 'pro');
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


def _execute(db_path: Path, sql: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def db_at_0018(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `payments` на ревизии 0018, строками и штампом 0018."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(PAYMENTS_AT_0018)
        conn.executescript(SEED_ROWS)
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL любому значению из alembic.ini. Переменная
    # подменяется ЯВНО: без этого ревизия ушла бы на адрес из окружения
    # разработчика — то есть на живую базу.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0018")
    return config, db_path


def test_the_column_is_absent_before_the_upgrade(db_at_0018):
    """Половина утверждения о ревизии: ДО наката колонки нет.

    Без неё парный тест ниже прошёл бы и на схеме, где колонка существовала
    изначально, — то есть не доказывал бы, что ревизия что-то изменила.
    """
    _, db_path = db_at_0018

    assert COLUMN_NAME not in _columns(db_path, "payments")


def test_upgrade_adds_a_nullable_column(db_at_0018):
    """После наката колонка есть и ДОПУСКАЕТ NULL.

    Nullable проверяется, а не подразумевается: `NOT NULL` здесь означал бы, что
    каждой существующей строке проставлен ответ правила, которого у неё никогда
    не было.
    """
    config, db_path = db_at_0018

    command.upgrade(config, "0019")

    columns = _columns(db_path, "payments")
    assert COLUMN_NAME in columns
    assert columns[COLUMN_NAME]["notnull"] == 0, "колонка объявлена NOT NULL"


def test_upgrade_leaves_existing_rows_without_a_recorded_answer(db_at_0018):
    """⚠️ СУЩЕСТВУЮЩИЕ СТРОКИ ПОЛУЧАЮТ NULL, А НЕ ЗНАЧЕНИЕ.

    Это и есть предмет решения «без `server_default`», и проверяется он именно
    здесь. Умолчание проставило бы каждой строке факт, которого не было: `false`
    записал бы отказ, которого не случалось, `true` — разрешение, которого никто
    не давал. Обе неправды неотличимы постфактум от настоящего ответа.
    """
    config, db_path = db_at_0018

    command.upgrade(config, "0019")

    recorded = _rows(
        db_path, f"SELECT id, {COLUMN_NAME} FROM payments ORDER BY id"
    )
    assert [row[COLUMN_NAME] for row in recorded] == [None, None], recorded


def test_upgrade_has_no_default_on_the_column(db_at_0018):
    """У колонки нет `server_default` — проверяется по схеме, а не по тексту.

    Парный к предыдущему: тот держит уже существующие строки, этот — строки,
    которые будут вставлены ПОСЛЕ наката необновлённым кодом. Умолчание на
    уровне СУБД дало бы им ответ правила, которого никто не спрашивал.
    """
    config, db_path = db_at_0018

    command.upgrade(config, "0019")

    assert _columns(db_path, "payments")[COLUMN_NAME]["dflt_value"] is None

    _execute(
        db_path,
        "INSERT INTO payments "
        "(id, user_id, yookassa_payment_id, status, amount_value, "
        " amount_currency, kind) "
        "VALUES (90, 7, 'yoo_new', 'pending', '1490.00', 'RUB', 'subscription')",
    )
    assert _scalar(db_path, f"SELECT {COLUMN_NAME} FROM payments WHERE id = 90") is None


def test_the_column_accepts_all_three_values(db_at_0018):
    """Значений три, а не два, и схема обязана вмещать каждое.

    `false` через форму сегодня недостижим — отказ возвращает 302 ДО создания
    платежа, — но колонка обязана уметь его выразить: иначе следующий писатель
    выразит отказ через NULL, и «спросили и отвергли» станет неотличимо от «не
    спрашивали».
    """
    config, db_path = db_at_0018
    command.upgrade(config, "0019")

    _execute(db_path, f"UPDATE payments SET {COLUMN_NAME} = true WHERE id = 1")
    _execute(db_path, f"UPDATE payments SET {COLUMN_NAME} = false WHERE id = 2")

    assert _scalar(db_path, f"SELECT {COLUMN_NAME} FROM payments WHERE id = 1") == 1
    assert _scalar(db_path, f"SELECT {COLUMN_NAME} FROM payments WHERE id = 2") == 0


def test_downgrade_drops_the_column(db_at_0018):
    """Откат возвращает СХЕМУ в состояние `0018`: колонки снова нет."""
    config, db_path = db_at_0018
    command.upgrade(config, "0019")
    assert COLUMN_NAME in _columns(db_path, "payments")

    command.downgrade(config, "0018")

    assert COLUMN_NAME not in _columns(db_path, "payments")


def test_downgrade_loses_the_recorded_answers(db_at_0018):
    """⚠️ ПОТЕРЯ ДАННЫХ ЗАКРЕПЛЕНА ТЕСТОМ, А НЕ ТОЛЬКО ДОКСТРИНГОМ.

    Тест фиксирует ФАКТ, а не объявляет его желаемым: записанное разрешение
    после отката и повторного наката не возвращается, потому что второго места,
    где ответ гарда хранится, по замыслу решения D-28 не существует. Если
    однажды появится ревизия, умеющая это откатывать по-настоящему, падение
    ЭТОГО теста будет верным сигналом, что поведение изменилось.
    """
    config, db_path = db_at_0018
    command.upgrade(config, "0019")
    _execute(db_path, f"UPDATE payments SET {COLUMN_NAME} = true WHERE id = 2")

    command.downgrade(config, "0018")
    command.upgrade(config, "0019")

    assert _scalar(db_path, f"SELECT {COLUMN_NAME} FROM payments WHERE id = 2") is None


def test_rows_survive_upgrade_and_downgrade(db_at_0018):
    """Ни одна строка платежа не потеряна ни накатом, ни откатом.

    Утверждение не декоративное: `payments` — след ДЕНЕГ, и молчаливая пропажа
    строки обнаружилась бы уже после наката на бой, когда откатывать поздно.
    """
    config, db_path = db_at_0018
    ids_before = [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ]

    command.upgrade(config, "0019")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ] == ids_before

    command.downgrade(config, "0018")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ] == ids_before


def test_the_model_and_the_revision_agree_on_the_columns(db_at_0018):
    """Модель и ревизия описывают ОДНУ таблицу, а не две похожие.

    Суита строит схему через `Base.metadata.create_all`, поэтому расхождение
    модели с ревизией она не увидит ни одним обычным тестом: у неё колонка
    появится всегда, а на боевой базе — только если ревизия её добавила.
    """
    from app.models.payment import Payment

    config, db_path = db_at_0018

    command.upgrade(config, "0019")

    assert set(_columns(db_path, "payments")) == set(Payment.__table__.c.keys())


def test_revision_0019_continues_0018():
    """0019 продолжает 0018 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0019").down_revision == "0018"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013/0014/0017.

    Импорт из `app.*` связал бы уже применённую миграцию с текущим кодом, и
    переименование атрибута задним числом изменило бы смысл давно выполненного
    шага.
    """
    source = (
        REPO_ROOT / "alembic" / "versions" / "0019_payment_switch_authorized.py"
    ).read_text(encoding="utf-8")

    assert "from app." not in source
    assert "import app" not in source


def test_the_revision_names_its_place_in_the_unapplied_queue():
    """⚠️ ЧИТАТЕЛЬ РЕВИЗИИ УЗНАЁТ ПРО D-26 ИЗ НЕЁ САМОЙ, А НЕ ИЗ STATE.md.

    Боевая база стоит на `0012`, и эта ревизия встаёт седьмой в очередь
    невыкаченных. Человек, открывший файл ревизии перед выкатом, обязан прочесть
    это на месте: планировочные документы он в этот момент не открывает.
    """
    source = (
        REPO_ROOT / "alembic" / "versions" / "0019_payment_switch_authorized.py"
    ).read_text(encoding="utf-8")

    assert "0012" in source, "ревизия не называет своё место в очереди"


def test_the_revision_does_not_use_batch_mode():
    """`batch_alter_table` здесь не нужен, и его отсутствие — утверждение.

    Ревизии `0017` он понадобился из-за `alter_column`, которого SQLite не умеет
    вовсе. Чистый `ADD COLUMN ... NULL` SQLite умеет сам, и batch-режим
    пересоздавал бы таблицу платежей без единой причины — лишний риск на
    таблице, которая является следом денег.
    """
    source = (
        REPO_ROOT / "alembic" / "versions" / "0019_payment_switch_authorized.py"
    ).read_text(encoding="utf-8")

    assert "batch_alter_table(" not in source
