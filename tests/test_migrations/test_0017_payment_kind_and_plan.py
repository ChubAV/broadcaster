"""Round-trip ревизии 0017: предмет покупки, тариф и снятие NOT NULL с счётчика.

Файл существует по той же причине, что `test_0016_send_logs_user_sent_at.py` и
`test_0014_sync_result_columns.py`: суита строит схему через
`Base.metadata.create_all` (tests/conftest.py) и о существовании Alembic не
знает, поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте. Совпадение
моделей и ревизии здесь не предполагается — оно проверяется.

Проверяемого у 0017 больше, чем у соседних ревизий, и ровно потому, что она
единственная в фазе НЕ additive: она ослабляет ограничение на существующей
колонке (`messages_count` перестаёт быть NOT NULL) и заполняет новую колонку у
уже лежащих строк. Обе операции переписывают таблицу на SQLite и обязаны
пережить откат без потери строк — иначе выкат на боевую базу необратим (T-05-14).

**Файловая база, а не база в памяти.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает
`asyncio.run`; внутри уже работающего цикла pytest-asyncio это упало бы
RuntimeError.

**Стартовая ревизия `0016` и целевая `0017` названы явно.** Прогон от нуля на
SQLite до цели не доходит: ревизия 0005 использует `op.drop_constraint`, а
Alembic на SQLite поднимает на нём `NotImplementedError` («No support for ALTER
of constraints in SQLite dialect»). Это свойство ЧУЖИХ ревизий, к 0017 отношения
не имеющее. Поэтому тест сам приводит базу в состояние «схема `payments` на
ревизии 0016 + строка в ней», отмечает это штампом и запускает НАСТОЯЩИЕ
`upgrade`/`downgrade`. Подвижное имя головы истории целью не берётся: оно
перестанет означать эту ревизию при следующем пополнении истории.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

# Таблица платежей в том виде, в каком её застаёт ревизия 0017: `kind` и `plan`
# ещё нет, `messages_count` ещё NOT NULL. Состав колонок сверен по
# `app/models/payment.py`.
PAYMENTS_AT_0016 = """
CREATE TABLE payments (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    yookassa_payment_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    amount_value VARCHAR(50) NOT NULL,
    amount_currency VARCHAR(10) NOT NULL,
    messages_count INTEGER NOT NULL,
    package_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at DATETIME
);

CREATE INDEX ix_payments_user_id ON payments (user_id);
CREATE UNIQUE INDEX ix_payments_yookassa_payment_id ON payments (yookassa_payment_id);
"""

# Платёж за пакет сообщений, лежащий в таблице ДО ревизии. Другого предмета
# покупки до 0017 в таблице физически быть не могло — на этом стоит backfill.
INSERT_OLD_PAYMENT = (
    "INSERT INTO payments "
    "(id, user_id, yookassa_payment_id, status, amount_value, amount_currency, "
    " messages_count, package_name, created_at, confirmed_at) "
    "VALUES (1, 7, 'yoo_old_1', 'succeeded', '149.00', 'RUB', "
    "        100, '100 сообщений', '2026-08-01 12:00:00', '2026-08-01 12:05:00')"
)

INSERT_SUBSCRIPTION_PAYMENT = (
    "INSERT INTO payments "
    "(id, user_id, yookassa_payment_id, status, amount_value, amount_currency, "
    " messages_count, package_name, kind, plan) "
    "VALUES (2, 7, 'yoo_sub_1', 'pending', '1490.00', 'RUB', "
    "        NULL, NULL, 'subscription', 'basic')"
)


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
def db_at_0016(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `payments` на ревизии 0016, одной строкой и штампом 0016."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(PAYMENTS_AT_0016)
        conn.execute(INSERT_OLD_PAYMENT)
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
    command.stamp(config, "0016")
    return config, db_path


def test_upgrade_adds_kind_and_plan(db_at_0016):
    """Обе колонки появляются: `kind` обязательная, `plan` — нет.

    `plan` nullable не по недосмотру: у платежа за пакет сообщений тарифа нет
    вовсе, и пустая строка вместо NULL читалась бы как «тариф с пустым именем».
    """
    config, db_path = db_at_0016

    command.upgrade(config, "0017")

    columns = _columns(db_path, "payments")
    assert "kind" in columns
    assert "plan" in columns
    assert columns["kind"]["notnull"] == 1
    assert columns["plan"]["notnull"] == 0


def test_upgrade_backfills_kind_for_rows_written_before_the_revision(db_at_0016):
    """Строка, лежавшая в таблице ДО ревизии, получает kind='package'.

    Это и есть тот backfill, ради которого отдельный UPDATE не писался:
    `ADD COLUMN ... NOT NULL DEFAULT 'package'` проставляет значение всем
    существующим строкам самим определением колонки. Значение верное по
    построению — платежей за подписку до 0017 в таблице быть не могло.
    """
    config, db_path = db_at_0016

    command.upgrade(config, "0017")

    assert _scalar(db_path, "SELECT kind FROM payments WHERE id = 1") == "package"
    assert _scalar(db_path, "SELECT plan FROM payments WHERE id = 1") is None


def test_messages_count_rejects_null_before_the_upgrade(db_at_0016):
    """До ревизии счётчик сообщений NULL не принимал.

    Половина утверждения о снятии NOT NULL. Без неё парный тест ниже прошёл бы
    и на схеме, где ограничения не было изначально, — то есть не доказывал бы,
    что ревизия что-то изменила.
    """
    config, db_path = db_at_0016

    assert _columns(db_path, "payments")["messages_count"]["notnull"] == 1
    with pytest.raises(sqlite3.IntegrityError):
        _execute(
            db_path,
            "INSERT INTO payments "
            "(id, user_id, yookassa_payment_id, status, amount_value, "
            " amount_currency, messages_count) "
            "VALUES (99, 7, 'yoo_null', 'pending', '1490.00', 'RUB', NULL)",
        )


def test_messages_count_accepts_null_after_the_upgrade(db_at_0016):
    """После ревизии платёж за подписку без счётчика сообщений вставляется.

    Проверяется И объявление (`PRAGMA table_info`), И настоящая вставка: у
    SQLite ослабление ограничения делается пересозданием таблицы (batch-режим),
    и объявление, разошедшееся с поведением, — ровно тот дефект, который здесь
    ловится.
    """
    config, db_path = db_at_0016

    command.upgrade(config, "0017")

    assert _columns(db_path, "payments")["messages_count"]["notnull"] == 0
    _execute(db_path, INSERT_SUBSCRIPTION_PAYMENT)
    assert _scalar(db_path, "SELECT messages_count FROM payments WHERE id = 2") is None
    assert _scalar(db_path, "SELECT plan FROM payments WHERE id = 2") == "basic"


def test_downgrade_removes_the_columns_and_restores_not_null(db_at_0016):
    """Откат симметричен: колонок нет, ограничение вернулось."""
    config, db_path = db_at_0016
    command.upgrade(config, "0017")

    command.downgrade(config, "0016")

    columns = _columns(db_path, "payments")
    assert "kind" not in columns
    assert "plan" not in columns
    assert columns["messages_count"]["notnull"] == 1


def test_rows_survive_upgrade_and_downgrade(db_at_0016):
    """Платёж, записанный ДО ревизии, переживает и накат, и откат.

    Утверждение не декоративное: `payments` — журнал того, что произошло с
    деньгами, а обе операции ревизии на SQLite пересоздают таблицу. Молчаливая
    потеря строки обнаружилась бы уже после наката на бой, когда откатывать
    поздно (T-05-14).
    """
    config, db_path = db_at_0016
    before = _rows(db_path, "SELECT * FROM payments ORDER BY id")

    command.upgrade(config, "0017")
    after_upgrade = _rows(db_path, "SELECT * FROM payments ORDER BY id")
    assert len(after_upgrade) == 1
    # Сверяются колонки, существовавшие ДО ревизии: новых в снимке `before` нет.
    for column, value in before[0].items():
        assert after_upgrade[0][column] == value, column

    command.downgrade(config, "0016")
    assert _rows(db_path, "SELECT * FROM payments ORDER BY id") == before


def test_revision_0017_continues_0016():
    """0017 продолжает 0016 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является (та же оговорка — в `test_0013_ad_status.py`; редакция, называвшая
    имя, уже однажды упала при пополнении истории).
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0017").down_revision == "0016"
