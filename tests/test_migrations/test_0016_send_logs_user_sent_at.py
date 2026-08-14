"""Round-trip ревизии 0016: составной индекс (user_id, sent_at) на send_logs.

Файл существует по той же причине, что `test_0013_ad_status.py` и
`test_0015_groups_unique_account_external.py`: суита строит схему через
`Base.metadata.create_all` (tests/conftest.py) и о существовании Alembic не
знает, поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте.

Что здесь проверяется и что НЕ проверяется. Ревизия — оптимизация, а не
предусловие: дашборд и история обязаны работать и до её наката, поэтому
утверждения о скорости запросов файл не делает и делать не может (планировщик
SQLite не тот, что у боевого PostgreSQL). Проверяется ровно то, что от
индексной ревизии зависит по-настоящему: индекс появляется на `upgrade`,
исчезает на `downgrade`, СТРОКИ при этом не трогаются, а линия ревизий не
разветвилась.

**Файловая база, а не `:memory:`.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite в памяти между
соединениями не живёт.

**Тест синхронный.** `alembic/env.py` в online-режиме вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая точка — `0015`, целевая — `0016`, обе названы явно.** Прогон от
нуля на SQLite до цели не доходит: ревизия 0005 использует
`op.drop_constraint`, а Alembic на SQLite поднимает на нём `NotImplementedError`
(«No support for ALTER of constraints in SQLite dialect»). Это свойство ЧУЖИХ
ревизий, к 0016 отношения не имеющее. Поэтому тест сам приводит базу в
состояние «схема `send_logs` на ревизии 0015 + строка в ней», отмечает это
штампом 0015 и запускает НАСТОЯЩИЕ `upgrade`/`downgrade`. Имя `head` целью не
берётся: оно перестанет означать эту ревизию при следующем пополнении истории.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

INDEX_NAME = "ix_send_logs_user_id_sent_at"

# Таблица журнала отправок в том виде, в каком её застаёт ревизия 0016: снапшоты
# контента добавлены ревизией 0005, `task_id` — ревизией 0006, три ОДИНОЧНЫХ
# индекса (`user_id`, `task_id`, `sent_at`) уже на месте, составного ещё нет.
# Состав колонок сверен по `app/models/send_log.py`.
SEND_LOGS_AT_0015 = """
CREATE TABLE send_logs (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    schedule_id INTEGER,
    ad_id INTEGER,
    group_id INTEGER,
    ad_title VARCHAR(255),
    ad_text TEXT,
    ad_images JSON,
    group_name VARCHAR(255),
    messenger_type VARCHAR(20),
    task_id VARCHAR(50),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX ix_send_logs_user_id ON send_logs (user_id);
CREATE INDEX ix_send_logs_task_id ON send_logs (task_id);
CREATE INDEX ix_send_logs_sent_at ON send_logs (sent_at);
"""

INSERT_SEND_LOG = (
    "INSERT INTO send_logs "
    "(id, user_id, schedule_id, ad_id, group_id, ad_title, ad_text, ad_images, "
    " group_name, messenger_type, task_id, status, error_message, sent_at) "
    "VALUES (1, 7, 3, 4, 5, 'Объявление', 'Текст', '[]', 'Группа', 'tg', "
    "        'task-1', 'sent', NULL, '2026-08-01 12:00:00')"
)


def _index_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        return {row[0] for row in rows}
    finally:
        conn.close()


def _rows(db_path: Path, sql: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql)]
    finally:
        conn.close()


@pytest.fixture
def db_at_0015(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `send_logs` на ревизии 0015, одной строкой и штампом 0015."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SEND_LOGS_AT_0015)
        conn.execute(INSERT_SEND_LOG)
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
    command.stamp(config, "0015")
    return config, db_path


def test_upgrade_creates_composite_index(db_at_0015):
    """Составной индекс появляется — ради него ревизия и написана."""
    config, db_path = db_at_0015

    command.upgrade(config, "0016")

    assert INDEX_NAME in _index_names(db_path)


def test_upgrade_keeps_the_single_column_indexes(db_at_0015):
    """Одиночные индексы ревизия НЕ снимает.

    Составной индекс покрывает запросы вида «мои записи в окне времени», но не
    отменяет доступ по одному только `sent_at` (сводки по всем пользователям) и
    по `task_id` (поиск записи по идентификатору задачи). Ревизия — добавление,
    а не замена; снятие одиночных индексов было бы отдельным решением с
    собственным обоснованием.
    """
    config, db_path = db_at_0015

    command.upgrade(config, "0016")

    assert {
        "ix_send_logs_user_id",
        "ix_send_logs_task_id",
        "ix_send_logs_sent_at",
    } <= _index_names(db_path)


def test_downgrade_removes_composite_index(db_at_0015):
    """Откат снимает ровно тот индекс, что ревизия создала."""
    config, db_path = db_at_0015
    command.upgrade(config, "0016")

    command.downgrade(config, "0015")

    assert INDEX_NAME not in _index_names(db_path)


def test_rows_survive_upgrade_and_downgrade(db_at_0015):
    """Строка, вставленная ДО апгрейда, переживает и upgrade, и downgrade.

    Утверждение не декоративное: индексная ревизия не имеет права переписывать
    данные, а `send_logs` — самая растущая таблица системы, и молчаливая потеря
    журнала отправок обнаружилась бы уже после наката на бой.
    """
    config, db_path = db_at_0015
    before = _rows(db_path, "SELECT * FROM send_logs ORDER BY id")

    command.upgrade(config, "0016")
    assert _rows(db_path, "SELECT * FROM send_logs ORDER BY id") == before

    command.downgrade(config, "0015")
    assert _rows(db_path, "SELECT * FROM send_logs ORDER BY id") == before


def test_revision_0016_continues_0015():
    """0016 продолжает 0015 — история ревизий остаётся одной линией.

    Ветвление ломает `alembic upgrade head` сразу для всех, поэтому проверяется
    КОЛИЧЕСТВО голов, а не имя головы: имя меняется с каждой новой ревизией и
    свойством истории не является (та же оговорка — в `test_0013_ad_status.py`;
    редакция, называвшая имя, уже однажды упала при пополнении истории).
    Продолжение линии этой ревизией проверяется её собственной сцепкой: 0016
    продолжает 0015, а значит очередь невыкаченных 0013-0015 не переставлена.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0016").down_revision == "0015"
