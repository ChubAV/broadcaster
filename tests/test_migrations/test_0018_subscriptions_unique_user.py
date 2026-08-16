"""Round-trip ревизии 0018: одна активная подписка на пользователя + зачистка дублей.

Файл существует по той же причине, что `test_0017_payment_kind_and_plan.py`:
суита строит схему через `Base.metadata.create_all` (tests/conftest.py) и о
существовании Alembic не знает, поэтому текст ревизии не исполняется НИ В ОДНОМ
обычном тесте. Совпадение модели и ревизии здесь не предполагается — проверяется.

Проверяемого у 0018 больше, чем у чисто аддитивных ревизий, потому что она
МЕНЯЕТ ДАННЫЕ: перед созданием индекса она деактивирует лишние строки. Правило
выбора выжившей — продуктовое решение, принятое миграцией («срок дальше», ничьи
разрываются наибольшим `id`), и оно обязано проверяться, а не подразумеваться:
неверно выбранная выжившая строка отняла бы у пользователя оплаченный срок молча.

**Файловая база, а не база в памяти.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия `0017` и целевая `0018` названы явно.** Прогон от нуля на
SQLite до цели не доходит: ревизия 0005 использует `op.drop_constraint`, а
Alembic на SQLite поднимает на нём `NotImplementedError`. Это свойство ЧУЖИХ
ревизий, к 0018 отношения не имеющее. Поэтому тест сам приводит базу в состояние
«схема `subscriptions` на ревизии 0017 + строки в ней», отмечает это штампом и
запускает НАСТОЯЩИЕ `upgrade`/`downgrade`.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

INDEX_NAME = "uq_subscriptions_active_user"

# Таблица подписок в том виде, в каком её застаёт ревизия 0018: ни одна ревизия
# между 0001 и 0017 её не трогала. Состав колонок сверен по
# `alembic/versions/0001_initial_schema.py` и `app/models/subscription.py`.
SUBSCRIPTIONS_AT_0017 = """
CREATE TABLE subscriptions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT (true),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""

# Пользователь 7 — ДУБЛЬ: две активные строки, срок у id=2 дальше.
# Пользователь 8 — одна активная строка, трогать её нечем.
# Пользователь 9 — активная строка плюс УЖЕ деактивированная история: зачистка
#                  не имеет права ни воскресить историю, ни снять активную.
SEED_ROWS = """
INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) VALUES
    (1, 7, 'basic', '2026-09-01 00:00:00', true),
    (2, 7, 'pro',   '2026-11-01 00:00:00', true),
    (3, 8, 'basic', '2026-10-01 00:00:00', true),
    (4, 9, 'basic', '2026-12-01 00:00:00', true),
    (5, 9, 'free',  '2026-01-01 00:00:00', false);
"""

# Ничья по сроку у пользователя 11: разрывается наибольшим id.
SEED_TIE = """
INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) VALUES
    (10, 11, 'basic', '2026-10-01 00:00:00', true),
    (11, 11, 'pro',   '2026-10-01 00:00:00', true);
"""


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


def _indexes(db_path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        return {row["name"] for row in conn.execute(f"PRAGMA index_list({table})")}
    finally:
        conn.close()


def _insert_active(user_id: int, row_id: int, expires: str = "2027-01-01 00:00:00") -> str:
    return (
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        f"VALUES ({row_id}, {user_id}, 'basic', '{expires}', true)"
    )


@pytest.fixture
def db_at_0017(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `subscriptions` на ревизии 0017, строками и штампом 0017."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SUBSCRIPTIONS_AT_0017)
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
    command.stamp(config, "0017")
    return config, db_path


def test_a_second_active_subscription_is_accepted_before_the_upgrade(db_at_0017):
    """До ревизии вторая активная строка вставлялась — это и был дефект.

    Половина утверждения об ограничении. Без неё парный тест ниже прошёл бы и на
    схеме, где ограничение существовало изначально, — то есть не доказывал бы,
    что ревизия что-то изменила.
    """
    _, db_path = db_at_0017

    _execute(db_path, _insert_active(user_id=8, row_id=90))

    assert _scalar(db_path, "SELECT COUNT(*) FROM subscriptions WHERE user_id = 8") == 2


def test_upgrade_creates_the_partial_unique_index(db_at_0017):
    """Индекс появляется и он ЧАСТИЧНЫЙ — по условию `is_active`.

    Частичность проверяется не только именем: уникальность на всю колонку
    заперла бы пользователя 9, у которого рядом с активной строкой лежит уже
    деактивированная история. Она лежит в фикстуре именно ради этой проверки.
    """
    config, db_path = db_at_0017

    command.upgrade(config, "0018")

    assert INDEX_NAME in _indexes(db_path, "subscriptions")
    sql = _scalar(
        db_path,
        f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{INDEX_NAME}'",
    )
    assert "WHERE" in sql.upper(), f"индекс не частичный: {sql}"
    assert "is_active" in sql


def test_upgrade_rejects_a_second_active_subscription(db_at_0017):
    """После наката вторую активную строку отвергает СУБД, а не приложение."""
    config, db_path = db_at_0017

    command.upgrade(config, "0018")

    with pytest.raises(sqlite3.IntegrityError):
        _execute(db_path, _insert_active(user_id=8, row_id=90))


def test_upgrade_still_accepts_an_inactive_row(db_at_0017):
    """История подписок не заперта: деактивированных строк можно сколько угодно."""
    config, db_path = db_at_0017
    command.upgrade(config, "0018")

    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (91, 8, 'basic', '2027-01-01 00:00:00', false)",
    )
    _execute(
        db_path,
        "INSERT INTO subscriptions (id, user_id, plan, expires_at, is_active) "
        "VALUES (92, 8, 'pro', '2027-02-01 00:00:00', false)",
    )

    assert _scalar(db_path, "SELECT COUNT(*) FROM subscriptions WHERE user_id = 8") == 3


def test_backfill_keeps_the_row_with_the_furthest_expiry(db_at_0017):
    """ПРОДУКТОВОЕ ПРАВИЛО ЗАЧИСТКИ: выживает строка с БОЛЬШИМ сроком.

    Правило выбрано в сторону пользователя: дубль возник по вине платформы, и
    отнимать за это оплаченный срок нельзя. Проверяется именно оно, а не просто
    «осталась одна строка»: «одна» вышла бы и при неверном выборе.
    """
    config, db_path = db_at_0017

    command.upgrade(config, "0018")

    active = _rows(
        db_path,
        "SELECT id, plan, expires_at FROM subscriptions "
        "WHERE user_id = 7 AND is_active ORDER BY id",
    )
    assert len(active) == 1, active
    assert active[0]["id"] == 2, "выжила строка с БЛИЖНИМ сроком — правило нарушено"
    assert active[0]["plan"] == "pro"


def test_backfill_deactivates_rather_than_deletes(db_at_0017):
    """Лишняя строка ДЕАКТИВИРУЕТСЯ, а не удаляется: журнал не теряет строк.

    Отличие от ревизии 0015, которая дубли групп именно удаляла. Там дубль был
    следом дефекта синхронизации и данных пользователя не нёс; здесь строка
    подписки — след оплаты, и стирать её нечем оправдать.
    """
    config, db_path = db_at_0017

    command.upgrade(config, "0018")

    assert _scalar(db_path, "SELECT COUNT(*) FROM subscriptions") == 5
    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 1") == 0


def test_backfill_leaves_untouched_users_alone(db_at_0017):
    """Пользователь без дублей не задет, а его деактивированная история не воскресла."""
    config, db_path = db_at_0017

    command.upgrade(config, "0018")

    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 3") == 1
    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 4") == 1
    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 5") == 0


def test_backfill_breaks_an_exact_tie_by_highest_id(db_at_0017):
    """Ничья по сроку разрывается НАИБОЛЬШИМ id — детерминированно.

    Без явного разрыва ничьей исход зависел бы от плана выполнения запроса: один
    и тот же прогон на боевой базе и на её копии мог бы оставить РАЗНЫЕ строки, и
    расхождение обнаружилось бы уже после наката.
    """
    config, db_path = db_at_0017
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SEED_TIE)
        conn.commit()
    finally:
        conn.close()

    command.upgrade(config, "0018")

    active = _rows(
        db_path, "SELECT id FROM subscriptions WHERE user_id = 11 AND is_active"
    )
    assert [row["id"] for row in active] == [11]


def test_upgrade_on_clean_data_changes_nothing(db_at_0017):
    """На базе без дублей зачистка не трогает ни одной строки.

    Сегодня это и есть ожидаемое состояние боевой базы: подписки в проде не
    создавались вовсе, потому что колонок `payments.kind` / `plan` там ещё нет.
    """
    config, db_path = db_at_0017
    _execute(db_path, "UPDATE subscriptions SET is_active = false WHERE id = 1")
    before = _rows(db_path, "SELECT * FROM subscriptions ORDER BY id")

    command.upgrade(config, "0018")

    assert _rows(db_path, "SELECT * FROM subscriptions ORDER BY id") == before


def test_downgrade_drops_the_index_and_accepts_a_second_row_again(db_at_0017):
    """Откат возвращает СХЕМУ: индекса нет, вторая активная строка вставляется."""
    config, db_path = db_at_0017
    command.upgrade(config, "0018")

    command.downgrade(config, "0017")

    assert INDEX_NAME not in _indexes(db_path, "subscriptions")
    _execute(db_path, _insert_active(user_id=8, row_id=90))
    assert _scalar(db_path, "SELECT COUNT(*) FROM subscriptions WHERE user_id = 8") == 2


def test_downgrade_does_not_restore_the_deactivated_rows(db_at_0017):
    """⚠️ ОДНОСТОРОННОСТЬ ЗАКРЕПЛЕНА ТЕСТОМ, А НЕ ТОЛЬКО ДОКСТРИНГОМ.

    Тест фиксирует ФАКТ, а не объявляет его желаемым: строка 1, деактивированная
    накатом, после отката остаётся деактивированной — знание о том, какие строки
    были тронуты, ревизия нигде не сохраняет. Тот же класс необратимости, что у
    `0013`. Если однажды появится ревизия, умеющая откатывать это по-настоящему,
    падение ЭТОГО теста будет верным сигналом, что поведение изменилось.
    """
    config, db_path = db_at_0017
    command.upgrade(config, "0018")
    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 1") == 0

    command.downgrade(config, "0017")

    assert _scalar(db_path, "SELECT is_active FROM subscriptions WHERE id = 1") == 0


def test_rows_survive_upgrade_and_downgrade(db_at_0017):
    """Ни одна строка подписки не потеряна ни накатом, ни откатом.

    Утверждение не декоративное: `subscriptions` — след оплат, а зачистка
    ревизии трогает данные. Молчаливая пропажа строки обнаружилась бы уже после
    наката на бой, когда откатывать поздно (T-05-14).
    """
    config, db_path = db_at_0017
    ids_before = [row["id"] for row in _rows(db_path, "SELECT id FROM subscriptions ORDER BY id")]

    command.upgrade(config, "0018")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM subscriptions ORDER BY id")
    ] == ids_before

    command.downgrade(config, "0017")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM subscriptions ORDER BY id")
    ] == ids_before


def test_revision_0018_continues_0017():
    """0018 продолжает 0017 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0018").down_revision == "0017"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013/0014/0017.

    Импорт из `app.*` связал бы уже применённую миграцию с текущим кодом, и
    переименование константы задним числом изменило бы смысл давно выполненного
    шага.
    """
    source = (
        REPO_ROOT / "alembic" / "versions" / "0018_subscriptions_unique_user.py"
    ).read_text()

    assert "from app." not in source
    assert "import app" not in source
