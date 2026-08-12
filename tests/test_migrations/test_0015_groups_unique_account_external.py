"""Round-trip ревизии 0015: схлопывание дублей и уникальность (account, external).

Файл существует по той же причине, что `test_0014_sync_result_columns.py`:
суита строит схему через `Base.metadata.create_all` и о существовании Alembic
не знает, поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте.

Ключевое утверждение файла — не «ограничение появилось», а
`test_duplicate_rows_are_merged_not_just_deleted`: ревизия единственный раз во
всём проекте удаляет строки таблицы `groups`, и цена ошибки здесь —
молчаливая потеря пользовательского решения. Поэтому проверяется не факт
схлопывания, а КАЖДОЕ правило слияния по отдельности: выживает первая строка,
выживает выключенность, выживает самая ранняя пометка пропажи.

Стартовая точка — `0014`, целевая — `0015`, обе названы явно: прогон от нуля
на SQLite не доходит до цели (ревизия 0005 использует `op.drop_constraint`,
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

# Таблица в том виде, в каком её застаёт ревизия 0015: `missing_since` уже
# добавлена ревизией 0014, уникального ограничения ещё нет.
SCHEMA_AT_0014 = """
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
    missing_since DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""

INSERT_GROUP = (
    "INSERT INTO groups "
    "(id, user_id, account_id, messenger_type, group_external_id, name, "
    " is_active, missing_since) "
    "VALUES (?, ?, ?, 'wa', ?, ?, ?, ?)"
)


def _rows(db_path: Path, sql: str, *params):
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(sql, params)]
    finally:
        conn.close()


def _make_db(tmp_path: Path, monkeypatch, groups) -> tuple[Config, Path]:
    """База со схемой 0014, переданными строками и штампом 0014."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_AT_0014)
        conn.executemany(INSERT_GROUP, groups)
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL любому значению из alembic.ini.
    # Переменная подменяется ЯВНО: без этого ревизия ушла бы на адрес из
    # окружения разработчика — то есть на живую базу.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0014")
    return config, db_path


def test_upgrade_makes_the_pair_unique(tmp_path, monkeypatch):
    """После ревизии второй INSERT той же пары падает.

    Проверяется поведение, а не имя ограничения: именно отказ вставки и есть
    та гарантия, ради которой ревизия написана.
    """
    config, db_path = _make_db(
        tmp_path, monkeypatch, [(1, 1, 1, "g1", "Одна", 1, None)]
    )

    command.upgrade(config, "0015")

    conn = sqlite3.connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(INSERT_GROUP, (2, 1, 1, "g1", "Одна", 1, None))
    finally:
        conn.close()


def test_same_external_id_in_another_account_survives(tmp_path, monkeypatch):
    """Ограничение скоупится аккаунтом: чужая группа с тем же id остаётся.

    Внешний идентификатор уникален внутри мессенджера, но не внутри нашей базы
    (T-03-06): у другого пользователя может лежать группа с тем же
    `group_external_id`, и её ревизия удалить не имеет права.
    """
    config, db_path = _make_db(
        tmp_path,
        monkeypatch,
        [
            (1, 1, 1, "g1", "Моя", 1, None),
            (2, 2, 2, "g1", "Чужая", 1, None),
        ],
    )

    command.upgrade(config, "0015")

    assert len(_rows(db_path, "SELECT id FROM groups")) == 2


def test_duplicate_rows_are_merged_not_just_deleted(tmp_path, monkeypatch):
    """Схлопывание сохраняет каждое пользовательское решение.

    Дубль — след дефекта, а не данные пользователя: две строки описывают ОДНУ
    группу мессенджера. Но решения, принятые пользователем на любой из них,
    потерять нельзя, поэтому проверяются все три правила слияния сразу.
    """
    config, db_path = _make_db(
        tmp_path,
        monkeypatch,
        [
            # Выжившая: наименьший id, включена, пометки нет.
            (1, 1, 1, "g1", "Первая", 1, None),
            # Дубль с ВЫКЛЮЧЕННОСТЬЮ и БОЛЕЕ РАННЕЙ пометкой пропажи.
            (2, 1, 1, "g1", "Она же", 0, "2026-01-01 00:00:00"),
            # Ещё дубль с ПОЗДНЕЙ пометкой — она проиграть обязана.
            (3, 1, 1, "g1", "И снова она", 1, "2026-05-01 00:00:00"),
            # Соседняя группа того же аккаунта дублей не имеет — не трогается.
            (4, 1, 1, "g2", "Другая", 1, None),
        ],
    )

    command.upgrade(config, "0015")

    rows = {row["id"]: row for row in _rows(db_path, "SELECT * FROM groups")}
    assert set(rows) == {1, 4}, "выживает строка с наименьшим id"

    survivor = rows[1]
    assert survivor["is_active"] == 0, (
        "выключенность обязана пережить схлопывание: направление ошибки "
        "выбирается в сторону НЕотправки"
    )
    assert survivor["missing_since"] == "2026-01-01 00:00:00", (
        "подпись «не найдена с …» обязана называть ПЕРВУЮ пропажу"
    )
    assert survivor["name"] == "Первая"

    untouched = rows[4]
    assert (untouched["is_active"], untouched["missing_since"]) == (1, None)


def test_group_without_duplicates_keeps_its_disabled_state(tmp_path, monkeypatch):
    """Слияние выключенности не задевает одиночные строки.

    Оператор переноса выключенности отбирает строки по `HAVING COUNT(*) > 1`;
    промах в этом условии выключил бы группы, которых дефект не касался.
    """
    config, db_path = _make_db(
        tmp_path,
        monkeypatch,
        [
            (1, 1, 1, "g1", "Включена", 1, None),
            (2, 1, 1, "g2", "Выключена", 0, None),
        ],
    )

    command.upgrade(config, "0015")

    rows = {row["id"]: row for row in _rows(db_path, "SELECT * FROM groups")}
    assert rows[1]["is_active"] == 1
    assert rows[2]["is_active"] == 0


def test_downgrade_removes_the_constraint(tmp_path, monkeypatch):
    """Откат снимает ограничение и не роняет остальную таблицу."""
    config, db_path = _make_db(
        tmp_path, monkeypatch, [(1, 1, 1, "g1", "Одна", 1, None)]
    )
    command.upgrade(config, "0015")

    command.downgrade(config, "-1")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(INSERT_GROUP, (2, 1, 1, "g1", "Одна", 1, None))
        conn.commit()
    finally:
        conn.close()

    assert len(_rows(db_path, "SELECT id FROM groups")) == 2
    # Колонки соседней семантики откат не трогает.
    columns = {
        row["name"]
        for row in _rows(db_path, "SELECT name FROM pragma_table_info('groups')")
    }
    assert {"missing_since", "last_error", "error_at", "is_active"} <= columns


def test_revision_0015_continues_0014():
    """0015 продолжает 0014 — история остаётся одной линией."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))

    assert script.get_revision("0015").down_revision == "0014"
    assert "0015" in script.get_heads()
