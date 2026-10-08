"""Ревизия 0023: колонки номера аккаунта и «ручной без номера невозможен».

ПРЕДМЕТ — НАСТОЯЩИЕ `upgrade` И `downgrade` РЕВИЗИИ, а не схема суиты. Остальная
суита строит таблицы из модели (`Base.metadata.create_all`) и расхождения модели
с очередью ревизий не видит по построению; здесь исполняется сама ревизия на
файловой SQLite со схемой на `0022`.

ЧТО ДОКАЗЫВАЕТСЯ, ПОИМЁННО:

  1. до ревизии колонок нет, после — у КАЖДОЙ строки номер «неизвестен»
     (`phone IS NULL`, `phone_is_manual = 0`), в том числе у MAX, чей номер
     лежит в `credentials`; сами `credentials` не тронуты (D-01);
  2. CHECK `ck_messenger_accounts_manual_requires_phone` отвергает «ручной без
     номера» при INSERT и при UPDATE с обеих сторон и принимает три законные
     пары (D-03);
  3. уникальности по номеру нет: два аккаунта с одним номером сосуществуют, а
     индексов у таблицы нет вовсе (D-02);
  4. пересоздание таблицы batch-режимом не теряет правил `ON DELETE` — ни
     собственного (`user_id` CASCADE), ни у детей (`groups` CASCADE,
     `schedules` SET NULL) — ни на upgrade, ни на downgrade;
  5. downgrade возвращает таблицу ровно прежней: `PRAGMA table_info` совпадает,
     строки целы, ограничения нет;
  6. условие и имя ограничения в ревизии дословно равны константам модели;
     ревизия продолжает `0022` одной линией и ничего не ввозит из `app.*`.

ТРИ РЕШЕНИЯ, ПОВТОРЁННЫЕ У `test_0022_schedules_active_requires_next_run.py`.
Причины переписаны сюда, а не заменены ссылкой: файл, объясняющий себя ссылкой
на соседа, теряет объяснение при первой же правке соседа.

**Файловая база, а не база в памяти.** Alembic открывает СОБСТВЕННОЕ соединение
(`alembic/env.py` создаёт свой async-движок), а SQLite в памяти между
соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает
`asyncio.run`; внутри работающего цикла pytest-asyncio это упало бы.

**Стартовая ревизия отмечена штампом.** Прогон от нуля на SQLite до `0022` не
доходит (`0005` использует `op.drop_constraint`, которого Alembic под SQLite не
умеет) — свойство ЧУЖИХ ревизий. Поэтому фикстура сама приводит базу к схеме
на `0022`, штампует её и запускает настоящие `command.upgrade` / `downgrade`.

⚠️ `DATABASE_URL` ПОДМЕНЯЕТСЯ ЯВНО. `alembic/env.py` предпочитает переменную
окружения любому значению из `alembic.ini`, а `.env` хоста указывает на ЖИВУЮ
базу. Без `monkeypatch.setenv` ревизия ушла бы туда.

СНИМОК СХЕМЫ НА `0022`. `messenger_accounts` — полного состава по
`0001_initial_schema.py` и `0014_sync_result_and_group_missing.py`; DDL выписан
в той форме, в которой его рендерит сам Alembic на SQLite (`DEFAULT
(CURRENT_TIMESTAMP)`, `PRIMARY KEY (id)`), иначе сверка `PRAGMA table_info` до и
после отката сравнивала бы разницу двух способов записи, а не действие ревизии.
`users`, `ads`, `groups`, `schedules` лежат в снимке ради внешних ключей: дети
нужны, чтобы проверить, что пересоздание родителя не трогает их правил.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
REVISION_FILE = REPO_ROOT / "alembic" / "versions" / "0023_messenger_account_phone.py"

CONSTRAINT_NAME = "ck_messenger_accounts_manual_requires_phone"
NUMBER = "+79991234567"
MAX_CREDENTIALS = '{"phone": "+79991234567"}'

SCHEMA_AT_0022 = """
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE messenger_accounts (
    id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    credentials TEXT NOT NULL,
    session_data TEXT,
    status VARCHAR(20) DEFAULT 'disconnected' NOT NULL,
    created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
    last_synced_at DATETIME,
    last_sync_result TEXT,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE ads (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL
);

CREATE TABLE groups (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES messenger_accounts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE schedules (
    id INTEGER NOT NULL PRIMARY KEY,
    ad_id INTEGER NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES messenger_accounts(id) ON DELETE SET NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    next_run_at DATETIME
);
"""

# Три аккаунта трёх мессенджеров. MAX (id=3) — главный предмет D-01: его номер,
# введённый при подключении, уже лежит в `credentials`, и ревизия обязана его НЕ
# переносить — номер станет известен только через писателя (Фаза 20).
SEED_ROWS = f"""
INSERT INTO users (id, email, name) VALUES (1, 'owner@test.com', 'Владелец');

INSERT INTO messenger_accounts (id, user_id, type, credentials, session_data, status)
VALUES
    (1, 1, 'tg_user', 'tg-cred', 'sess', 'active'),
    (2, 1, 'wa',      'wa-cred', NULL,   'active'),
    (3, 1, 'max',     '{MAX_CREDENTIALS}', NULL, 'disconnected');

INSERT INTO ads (id, user_id, title) VALUES (1, 1, 'Объявление');
INSERT INTO groups (id, user_id, account_id, name) VALUES (1, 1, 1, 'Группа');
INSERT INTO schedules (id, ad_id, account_id, is_active, next_run_at)
VALUES (1, 1, 3, 0, NULL);
"""

ACCOUNT_ROWS = (
    "SELECT id, user_id, type, credentials, session_data, status, created_at, "
    "last_synced_at, last_sync_result FROM messenger_accounts ORDER BY id"
)


def _rows(db_path: Path, sql: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql)]
    finally:
        conn.close()


def _execute(db_path: Path, sql: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


def _columns(db_path: Path, table: str) -> set[str]:
    return {row["name"] for row in _rows(db_path, f"PRAGMA table_info({table})")}


def _table_info(db_path: Path, table: str) -> list[tuple]:
    conn = sqlite3.connect(db_path)
    try:
        return list(conn.execute(f"PRAGMA table_info({table})"))
    finally:
        conn.close()


def _indexes(db_path: Path, table: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        return [row[1] for row in conn.execute(f"PRAGMA index_list({table})")]
    finally:
        conn.close()


def _delete_rules(db_path: Path, table: str) -> dict[str, str]:
    """Правило `ON DELETE` по каждой колонке-ссылке — из PRAGMA, а не из DDL."""
    conn = sqlite3.connect(db_path)
    try:
        return {row[3]: row[6] for row in conn.execute(f"PRAGMA foreign_key_list({table})")}
    finally:
        conn.close()


def _insert_account(row_id: int, *, phone: str | None, is_manual: int) -> str:
    value = "NULL" if phone is None else f"'{phone}'"
    return (
        "INSERT INTO messenger_accounts "
        "(id, user_id, type, credentials, status, phone, phone_is_manual) "
        f"VALUES ({row_id}, 1, 'tg_user', 'cred', 'active', {value}, {is_manual})"
    )


def _load_revision():
    import importlib.util

    spec = importlib.util.spec_from_file_location("revision_0023", REVISION_FILE)
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    return revision


@pytest.fixture
def db_at_0022(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой на ревизии 0022, тремя аккаунтами и штампом 0022."""
    db_path = tmp_path / "migration_0023.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_AT_0022)
        conn.executescript(SEED_ROWS)
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL любому значению из alembic.ini. Переменная
    # подменяется ЯВНО: без этого ревизия ушла бы на адрес из окружения
    # разработчика — то есть на ЖИВУЮ базу.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0022")
    return config, db_path


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 1 — колонки и «неизвестен» у каждой строки
# ─────────────────────────────────────────────────────────────────────────────


def test_the_columns_are_absent_before_the_upgrade(db_at_0022):
    """Половина утверждения о колонках: до ревизии их нет.

    Без неё парный тест ниже зеленел бы и на схеме, где колонки существовали
    изначально, — то есть не доказывал бы, что их завела ИМЕННО ЭТА ревизия.
    """
    _, db_path = db_at_0022

    assert not {"phone", "phone_is_manual"} & _columns(db_path, "messenger_accounts")


def test_after_the_upgrade_every_account_is_unknown(db_at_0022):
    """⚠️ D-01: РЕВИЗИЯ НОМЕРОВ НЕ ПЕРЕНОСИТ И НЕ УГАДЫВАЕТ.

    У КАЖДОЙ строки после наката номер «неизвестен». Главная строка — MAX
    (id=3): номер в её `credentials` лежит прямо перед ревизией, и соблазн
    «заодно перенести» — ровно то, что запрещено: номер в колонку пишет только
    модуль-писатель (D-13), перенос MAX — дозаполнение Фазы 20.
    """
    config, db_path = db_at_0022

    command.upgrade(config, "0023")

    assert _rows(
        db_path,
        "SELECT id, phone, phone_is_manual, credentials FROM messenger_accounts ORDER BY id",
    ) == [
        {"id": 1, "phone": None, "phone_is_manual": 0, "credentials": "tg-cred"},
        {"id": 2, "phone": None, "phone_is_manual": 0, "credentials": "wa-cred"},
        {"id": 3, "phone": None, "phone_is_manual": 0, "credentials": MAX_CREDENTIALS},
    ]


def test_the_upgrade_changes_no_existing_value(db_at_0022):
    """Пересоздание таблицы переносит прежние колонки всех строк без изменений."""
    config, db_path = db_at_0022
    before = _rows(db_path, ACCOUNT_ROWS)

    command.upgrade(config, "0023")

    assert _rows(db_path, ACCOUNT_ROWS) == before


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 2 — ограничение
# ─────────────────────────────────────────────────────────────────────────────


def test_the_check_refuses_a_manual_flag_without_a_number(db_at_0022):
    """⚠️ ГЛАВНОЕ: «ручной без номера» не принимает САМА ТАБЛИЦА — с трёх сторон.

    INSERT; UPDATE, поднимающий признак у строки без номера; UPDATE, стирающий
    номер под поднятым признаком. Последнее значит, что очистка обязана менять
    обе колонки одним оператором. Текст отказа обязан назвать ограничение по
    имени — безымянный отказ на бою не разобрать.
    """
    config, db_path = db_at_0022
    command.upgrade(config, "0023")

    with pytest.raises(sqlite3.IntegrityError) as on_insert:
        _execute(db_path, _insert_account(50, phone=None, is_manual=1))
    assert CONSTRAINT_NAME in str(on_insert.value)

    with pytest.raises(sqlite3.IntegrityError) as on_raise:
        _execute(db_path, "UPDATE messenger_accounts SET phone_is_manual = 1 WHERE id = 1")
    assert CONSTRAINT_NAME in str(on_raise.value)

    _execute(
        db_path,
        f"UPDATE messenger_accounts SET phone = '{NUMBER}', phone_is_manual = 1 WHERE id = 2",
    )
    with pytest.raises(sqlite3.IntegrityError) as on_erase:
        _execute(db_path, "UPDATE messenger_accounts SET phone = NULL WHERE id = 2")
    assert CONSTRAINT_NAME in str(on_erase.value)

    # Очистка ОДНИМ оператором законна — после неё автоисточники снова вправе
    # писать (PHONE-10).
    _execute(
        db_path,
        "UPDATE messenger_accounts SET phone = NULL, phone_is_manual = 0 WHERE id = 2",
    )
    assert _rows(
        db_path, "SELECT phone, phone_is_manual FROM messenger_accounts WHERE id = 2"
    ) == [{"phone": None, "phone_is_manual": 0}]


@pytest.mark.parametrize(
    "phone,is_manual",
    [
        pytest.param(None, 0, id="unknown"),
        pytest.param(NUMBER, 0, id="reported"),
        pytest.param(NUMBER, 1, id="manual"),
    ],
)
def test_the_three_legal_pairs_pass_the_upgraded_schema(db_at_0022, phone, is_manual):
    """⚠️ БЕЗ ЭТОГО ТЕСТА ОГРАНИЧЕНИЕ «ЗАПРЕТИТЬ ВСЁ» БЫЛО БЫ ЗЕЛЁНЫМ."""
    config, db_path = db_at_0022
    command.upgrade(config, "0023")

    _execute(db_path, _insert_account(50, phone=phone, is_manual=is_manual))

    assert _rows(
        db_path, "SELECT phone, phone_is_manual FROM messenger_accounts WHERE id = 50"
    ) == [{"phone": phone, "phone_is_manual": is_manual}]


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 3 — уникальности нет
# ─────────────────────────────────────────────────────────────────────────────


def test_two_accounts_with_one_number_coexist_and_no_index_exists(db_at_0022):
    """D-02: один SIM законно даёт TG + WA + MAX; TG при пересканировании — новую строку.

    Проверяется и поведение (две строки с одним номером), и отсутствие любого
    индекса у таблицы: уникальное ограничение на SQLite видно как
    `sqlite_autoindex_*`, и пустой перечень исключает его вместе с обычным.
    """
    config, db_path = db_at_0022
    command.upgrade(config, "0023")

    _execute(db_path, f"UPDATE messenger_accounts SET phone = '{NUMBER}' WHERE id IN (1, 2)")

    assert _rows(
        db_path, f"SELECT id FROM messenger_accounts WHERE phone = '{NUMBER}' ORDER BY id"
    ) == [{"id": 1}, {"id": 2}]
    assert _indexes(db_path, "messenger_accounts") == []


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 4 — переживание пересоздания таблицы
# ─────────────────────────────────────────────────────────────────────────────


EXPECTED_DELETE_RULES = {
    "messenger_accounts": {"user_id": "CASCADE"},
    "groups": {"user_id": "CASCADE", "account_id": "CASCADE"},
    "schedules": {"ad_id": "CASCADE", "account_id": "SET NULL"},
}


def _all_delete_rules(db_path: Path) -> dict[str, dict[str, str]]:
    return {table: _delete_rules(db_path, table) for table in EXPECTED_DELETE_RULES}


def test_the_on_delete_rules_survive_the_recreate(db_at_0022):
    """⚠️ ОТРАЖЕНИЕ SQLITE ТЕРЯЕТ `ON DELETE` МОЛЧА — ИЗМЕРЕНО НА `0022`.

    Потеря `user_id ... ON DELETE CASCADE` оставляла бы сиротские аккаунты
    удалённого пользователя. Правила детей проверяются тоже: пересоздание
    родителя меняет таблицу, на которую они ссылаются, и сохранность их ссылок
    и строк — утверждение, а не предположение. Оба прохода.
    """
    config, db_path = db_at_0022
    links = "SELECT g.id AS group_id, g.account_id AS group_account, s.account_id AS schedule_account FROM groups g, schedules s"
    before_links = _rows(db_path, links)

    command.upgrade(config, "0023")
    assert _all_delete_rules(db_path) == EXPECTED_DELETE_RULES
    assert _rows(db_path, links) == before_links

    command.downgrade(config, "0022")
    assert _all_delete_rules(db_path) == EXPECTED_DELETE_RULES
    assert _rows(db_path, links) == before_links == [
        {"group_id": 1, "group_account": 1, "schedule_account": 3}
    ]


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 5 — обратный проход
# ─────────────────────────────────────────────────────────────────────────────


def test_downgrade_restores_the_exact_table(db_at_0022):
    """Откат снимает ровно две колонки и ограничение — и больше ничего (D-01).

    Сверяется `PRAGMA table_info` целиком (порядок, типы, NOT NULL, умолчания,
    первичный ключ), строки и отсутствие ограничения — последнее поведением:
    «ручной без номера» снова нечего запрещать, потому что колонок нет, а
    вставка прежней формы проходит.
    """
    config, db_path = db_at_0022
    info_before = _table_info(db_path, "messenger_accounts")
    rows_before = _rows(db_path, ACCOUNT_ROWS)

    command.upgrade(config, "0023")
    command.downgrade(config, "0022")

    assert _table_info(db_path, "messenger_accounts") == info_before
    assert _rows(db_path, ACCOUNT_ROWS) == rows_before
    ddl = _rows(
        db_path,
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'messenger_accounts'",
    )[0]["sql"]
    assert CONSTRAINT_NAME not in ddl
    assert "ON DELETE CASCADE" in ddl


# ─────────────────────────────────────────────────────────────────────────────
# ШОВ МОДЕЛИ И РЕВИЗИИ
# ─────────────────────────────────────────────────────────────────────────────


def test_the_revision_condition_matches_the_model_word_for_word():
    """⚠️ ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ДВЕ ПОЛОВИНЫ ВООБЩЕ СВЕРЯЮТСЯ.

    Ревизия не импортирует из `app.*`, поэтому условие выписано в ней строкой.
    Разойдись два текста, ограничение на бою запрещало бы не то, что модель
    обещает суите, и суита на `create_all` об этом молчала бы.
    """
    from app.models.messenger_account import (
        MANUAL_REQUIRES_PHONE,
        MANUAL_REQUIRES_PHONE_NAME,
    )

    revision = _load_revision()

    assert revision.CONDITION == MANUAL_REQUIRES_PHONE
    assert revision.CONSTRAINT_NAME == MANUAL_REQUIRES_PHONE_NAME


def test_revision_0023_continues_0022():
    """0023 продолжает 0022 — история ревизий остаётся одной линией.

    Проверяется КОЛИЧЕСТВО голов, а не имя головы: имя меняется с каждой новой
    ревизией и свойством истории не является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))

    assert len(script.get_heads()) == 1, script.get_heads()
    assert script.get_revision("0023").down_revision == "0022"
    assert _load_revision().down_revision == "0022"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013…0022.

    Проверяется РАЗБОРОМ ДЕРЕВА, а не подстрокой: `app.` встречается в
    докстринге ревизии, который запрета не нарушает.
    """
    import ast

    tree = ast.parse(REVISION_FILE.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    offenders = [name for name in imported if name == "app" or name.startswith("app.")]
    assert not offenders, offenders
