"""Round-trip ревизии 0014: три additive nullable-колонки и симметричный откат.

Файл существует по той же причине, что и `test_0013_ad_status.py`: суита
строит схему через `Base.metadata.create_all` и о существовании Alembic не
знает, поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте. Совпадение
моделей и ревизии здесь не предполагается — оно проверяется.

Ключевое утверждение файла — `test_upgrade_adds_only_nullable_columns`. Целевая
база стоит на ревизии `0012` (STATE.md) и ближайший выкат будет прыжком
`0012 → 0014`; ревизия обязана добавлять колонки, не переписывая существующие
строки. Ровно поэтому фикстура вставляет строки ДО миграции и проверяет, что
после неё в новых колонках NULL, а не значение по умолчанию: появление
`server_default` превратило бы дешёвый ALTER в переписывание таблицы и стёрло бы
разницу между «синхронизация не выполнялась» и «синк дал ноль групп».

Стартовая точка — `0013`, целевая — `0014`, обе названы явно: прогон от нуля на
SQLite не доходит до цели (ревизия 0005 использует `op.drop_constraint`,
неподдерживаемый диалектом), а `head` перестанет быть именем этой ревизии при
следующем пополнении истории.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

# Обе таблицы в том виде, в каком их застаёт ревизия 0014: новых колонок ещё
# нет, всё остальное на месте.
SCHEMA_AT_0013 = """
CREATE TABLE messenger_accounts (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL,
    credentials TEXT NOT NULL,
    session_data TEXT,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE TABLE groups (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    messenger_type VARCHAR(20) NOT NULL,
    group_external_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    last_error TEXT,
    error_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""

NEW_COLUMNS = [
    ("messenger_accounts", "last_synced_at"),
    ("messenger_accounts", "last_sync_result"),
    ("groups", "missing_since"),
]


def _columns(db_path: Path, table: str) -> dict[str, sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return {
            row["name"]: row
            for row in conn.execute(f"PRAGMA table_info({table})")
        }
    finally:
        conn.close()


def _scalar(db_path: Path, sql: str):
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(sql).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


@pytest.fixture
def db_at_0013(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой ревизии 0013, строками в обеих таблицах и штампом 0013."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_AT_0013)
        conn.execute(
            "INSERT INTO messenger_accounts "
            "(id, user_id, type, credentials, status) "
            "VALUES (1, 1, 'wa', 'cred', 'active')"
        )
        conn.execute(
            "INSERT INTO groups "
            "(id, user_id, account_id, messenger_type, group_external_id, name) "
            "VALUES (1, 1, 1, 'wa', 'g1', 'Существующая группа')"
        )
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
    command.stamp(config, "0013")
    return config, db_path


def test_upgrade_adds_only_nullable_columns(db_at_0013):
    """Три колонки появляются nullable и без значения по умолчанию."""
    config, db_path = db_at_0013

    command.upgrade(config, "0014")

    for table, column in NEW_COLUMNS:
        columns = _columns(db_path, table)
        assert column in columns, (table, column)
        assert columns[column]["notnull"] == 0, (table, column)
        assert columns[column]["dflt_value"] is None, (table, column)


def test_existing_rows_survive_with_null(db_at_0013):
    """Существующие строки не переписываются: в новых колонках NULL.

    NULL здесь содержателен — он означает «синхронизация ещё не выполнялась» и
    обязан отличаться от нулевых счётчиков.
    """
    config, db_path = db_at_0013

    command.upgrade(config, "0014")

    assert _scalar(db_path, "SELECT COUNT(*) FROM messenger_accounts") == 1
    assert _scalar(db_path, "SELECT COUNT(*) FROM groups") == 1
    assert _scalar(db_path, "SELECT last_synced_at FROM messenger_accounts WHERE id = 1") is None
    assert _scalar(db_path, "SELECT last_sync_result FROM messenger_accounts WHERE id = 1") is None
    assert _scalar(db_path, "SELECT missing_since FROM groups WHERE id = 1") is None
    assert _scalar(db_path, "SELECT name FROM groups WHERE id = 1") == "Существующая группа"


def test_downgrade_removes_all_three_columns(db_at_0013):
    """Откат симметричен: снимаются ровно те три колонки, что были добавлены."""
    config, db_path = db_at_0013
    command.upgrade(config, "0014")

    command.downgrade(config, "-1")

    for table, column in NEW_COLUMNS:
        assert column not in _columns(db_path, table), (table, column)
    # Соседние колонки той же семантики (ошибки ОТПРАВКИ) откат не трогает.
    groups_columns = _columns(db_path, "groups")
    assert "last_error" in groups_columns
    assert "error_at" in groups_columns
    assert _scalar(db_path, "SELECT COUNT(*) FROM groups") == 1


def test_revision_0014_continues_0013():
    """0014 продолжает 0013 — прыжок 0012 → 0014 остаётся одной линией."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))

    assert script.get_revision("0014").down_revision == "0013"
    assert "0014" in script.get_heads()
