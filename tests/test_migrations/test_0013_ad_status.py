"""Round-trip ревизии 0013: upgrade и downgrade прогоняются по-настоящему.

Единственная автоматическая проверка ревизии в проекте. Аналога нет: суита
строит схему через `Base.metadata.create_all` (tests/conftest.py) и о
существовании Alembic не знает вовсе — то есть ни одна ревизия до сих пор не
исполнялась ни в одном тесте. Ревизия 0013 снимает колонку с боевыми данными,
и её `downgrade` объявлен необратимым по данным, поэтому она не может быть
первой, чей текст никто не запускал.

**Файловая база, а не `:memory:`.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite в памяти между
соединениями не живёт.

**Тест синхронный.** `alembic/env.py` в online-режиме вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Почему стартовая точка — 0012, а не `base`.** Прогон `upgrade head` от нуля
на SQLite не доходит до 0013: ревизия 0005 вызывает `op.drop_constraint`, а
Alembic на SQLite поднимает на нём `NotImplementedError` («No support for ALTER
of constraints in SQLite dialect»). Это свойство ЧУЖИХ ревизий, к 0013
отношения не имеющее, и чинить его здесь — выйти за границы плана. Поэтому
тест сам приводит базу в состояние «схема таблицы объявлений на ревизии 0012 +
строка в ней», отмечает это состояние штампом 0012 и дальше запускает
НАСТОЯЩИЕ `upgrade`/`downgrade` — так, что каждая операция самой ревизии 0013
исполняется, а не обходится.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

# Схема таблицы объявлений в том виде, в каком её застаёт ревизия 0013:
# булев флаг активности ещё на месте, колонки состояния ещё нет.
ADS_TABLE_AT_0012 = """
CREATE TABLE ads (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    images JSON,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""


def _columns(db_path: Path) -> dict[str, sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return {row["name"]: row for row in conn.execute("PRAGMA table_info(ads)")}
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
def db_at_0012(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой ревизии 0012, одной строкой и штампом 0012."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(ADS_TABLE_AT_0012)
        conn.execute(
            "INSERT INTO ads (id, user_id, title, text, images, is_active) "
            "VALUES (1, 1, 'Существующее объявление', 'Текст', '[]', 1)"
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
    command.stamp(config, "0012")
    return config, db_path


def test_upgrade_adds_status_column_not_null(db_at_0012):
    config, db_path = db_at_0012

    command.upgrade(config, "head")

    columns = _columns(db_path)
    assert "status" in columns
    assert columns["status"]["notnull"] == 1


def test_upgrade_publishes_rows_that_existed_before(db_at_0012):
    """D-02: существующие записи после миграции опубликованы.

    Строка вставлена ДО применения ревизии — заполнение обеспечивает
    `server_default`, отдельного UPDATE в ревизии нет.
    """
    config, db_path = db_at_0012

    command.upgrade(config, "head")

    assert _scalar(db_path, "SELECT status FROM ads WHERE id = 1") == "published"


def test_upgrade_drops_legacy_activity_column(db_at_0012):
    config, db_path = db_at_0012

    command.upgrade(config, "head")

    assert "is_active" not in _columns(db_path)


def test_upgrade_creates_status_index(db_at_0012):
    config, db_path = db_at_0012

    command.upgrade(config, "head")

    assert (
        _scalar(
            db_path,
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='ix_ads_status'",
        )
        == "ix_ads_status"
    )


def test_downgrade_restores_legacy_column_and_removes_status(db_at_0012):
    """Откат исполняется целиком, а не только импортируется.

    Что откат НЕ восстанавливает — значения: какое объявление было черновиком,
    после downgrade узнать неоткуда, все строки возвращаются активными. Это
    принято пользователем в D-02 (T-02-16) и объявлено комментарием в ревизии;
    тест фиксирует именно такое поведение, чтобы потеря не выглядела дефектом.
    """
    config, db_path = db_at_0012
    command.upgrade(config, "head")

    command.downgrade(config, "-1")

    columns = _columns(db_path)
    assert "status" not in columns
    assert "is_active" in columns
    assert _scalar(db_path, "SELECT is_active FROM ads WHERE id = 1") == 1
    assert (
        _scalar(
            db_path,
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='ix_ads_status'",
        )
        is None
    )


def test_revision_chain_has_single_head():
    """Ветвления ревизий не возникло: 0013 продолжает 0012."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert list(heads) == ["0013"], heads
    assert script.get_revision("0013").down_revision == "0012"
