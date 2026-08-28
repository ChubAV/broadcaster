"""Round-trip ревизии 0021: потолок незакрытых подписочных намерений в СХЕМЕ.

Файл существует по той же причине, что `test_0018_subscriptions_unique_user.py`:
суита строит схему через `Base.metadata.create_all` (tests/conftest.py) и о
существовании Alembic не знает, поэтому текст ревизии не исполняется НИ В ОДНОМ
обычном тесте. Совпадение модели и ревизии здесь не предполагается — проверяется.

Проверяемого у 0021 больше, чем у чисто аддитивных ревизий, потому что она
МЕНЯЕТ ДАННЫЕ ДЕНЕЖНОЙ ТАБЛИЦЫ: перед созданием индекса она переводит лишние
незакрытые намерения в статус `expired`. Правило выбора выжившей — продуктовое
решение, принятое миграцией («новейшее», `MAX(created_at)`, ничьи разрываются
наибольшим `id`), и оно обязано проверяться, а не подразумеваться: неверно
выбранная выжившая строка увела бы в просрочку намерение, созданное за минуту
до деплоя.

⚠️ ВТОРОЙ ПРЕДМЕТ ПРОВЕРКИ — ПЕРЕЖИВАНИЕ BATCH-ПЕРЕСОЗДАНИЯ. Снятие `NOT NULL`
с `yookassa_payment_id` идёт через `op.batch_alter_table`, который на SQLite
ПЕРЕСОЗДАЁТ таблицу целиком. Уникальность идентификатора платежа — защита от
подделки повторного уведомления, и её молчаливая потеря при пересоздании
обнаружилась бы только на боевом приёме денег (T-08-15).

**Файловая база, а не база в памяти.** Alembic открывает собственное соединение
(alembic/env.py создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия `0020` и целевая `0021` названы явно.** Прогон от нуля на
SQLite до цели не доходит: ревизия `0005` использует `op.drop_constraint`, а
Alembic на SQLite поднимает на нём `NotImplementedError`. Это свойство ЧУЖИХ
ревизий, к `0021` отношения не имеющее. Поэтому тест сам приводит базу в
состояние «схема `payments` на ревизии `0020` + строки в ней», отмечает это
штампом и запускает НАСТОЯЩИЕ `upgrade`/`downgrade`.

⚠️ ПО КАКИМ РЕВИЗИЯМ СОБРАН СНИМОК СХЕМЫ — НАЗЫВАЕТСЯ ЗДЕСЬ, А НЕ ВЫВОДИТСЯ.
Таблица `payments` заводится ревизией `0009_add_message_balance_and_payment_tables.py`
(НЕ `0001_initial_schema.py`: там её нет вовсе), `0017_payment_kind_and_plan.py`
добавляет `kind` и `plan` и снимает `NOT NULL` с `messages_count`,
`0019_payment_switch_authorized.py` добавляет `switch_authorized`. Ревизия
`0020_flat_subscription.py` таблицу платежей не трогает.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

REVISION_FILE = (
    REPO_ROOT / "alembic" / "versions" / "0021_payments_open_intent_index.py"
)

INDEX_NAME = "uq_payments_open_subscription_intent"

# Уникальный индекс идентификатора платежа в том виде, в каком его заводит
# ревизия `0009`: `Column(..., unique=True, index=True)` даёт ОДИН уникальный
# индекс с именем `ix_<таблица>_<колонка>`, а не отдельные constraint и индекс.
PAYMENT_ID_INDEX = "ix_payments_yookassa_payment_id"

# Таблица платежей в том виде, в каком её застаёт ревизия `0021`.
PAYMENTS_AT_0020 = """
CREATE TABLE payments (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    yookassa_payment_id VARCHAR(255) NOT NULL,
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

CREATE UNIQUE INDEX ix_payments_yookassa_payment_id
    ON payments (yookassa_payment_id);

CREATE INDEX ix_payments_user_id ON payments (user_id);
"""

# Пользователь 7 — ДУБЛЬ: три незакрытых подписочных намерения, новейшее — id=3.
# Пользователь 8 — одно незакрытое намерение, трогать его нечем.
# Пользователь 9 — незакрытое намерение плюс УЖЕ проведённый платёж и платёж за
#                  ПАКЕТ: ни один из двух зачистка трогать не имеет права.
SEED_ROWS = """
INSERT INTO payments
    (id, user_id, yookassa_payment_id, status, amount_value, kind, created_at)
VALUES
    (1, 7, 'yoo-1', 'pending',   '1490.00', 'subscription', '2026-08-01 10:00:00'),
    (2, 7, 'yoo-2', 'pending',   '1490.00', 'subscription', '2026-08-02 10:00:00'),
    (3, 7, 'yoo-3', 'pending',   '1490.00', 'subscription', '2026-08-03 10:00:00'),
    (4, 8, 'yoo-4', 'pending',   '1490.00', 'subscription', '2026-08-04 10:00:00'),
    (5, 9, 'yoo-5', 'pending',   '1490.00', 'subscription', '2026-08-05 10:00:00'),
    (6, 9, 'yoo-6', 'succeeded', '1490.00', 'subscription', '2026-08-06 10:00:00'),
    (7, 9, 'yoo-7', 'pending',   '500.00',  'package',      '2026-08-07 10:00:00');
"""

# Ничья по времени рождения у пользователя 11: разрывается наибольшим id.
SEED_TIE = """
INSERT INTO payments
    (id, user_id, yookassa_payment_id, status, amount_value, kind, created_at)
VALUES
    (10, 11, 'yoo-10', 'pending', '1490.00', 'subscription', '2026-08-09 10:00:00'),
    (11, 11, 'yoo-11', 'pending', '1490.00', 'subscription', '2026-08-09 10:00:00');
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


def _notnull(db_path: Path, table: str, column: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        for row in conn.execute(f"PRAGMA table_info({table})"):
            if row[1] == column:
                return row[3]
    finally:
        conn.close()
    raise AssertionError(f"колонки {table}.{column} нет вовсе")


def _insert(
    row_id: int,
    user_id: int,
    *,
    status: str = "pending",
    kind: str = "subscription",
    payment_id: str | None = None,
) -> str:
    """INSERT одной строки платежа. `payment_id=None` даёт SQL-литерал NULL."""
    value = "NULL" if payment_id is None else f"'{payment_id}'"
    return (
        "INSERT INTO payments "
        "(id, user_id, yookassa_payment_id, status, amount_value, kind, created_at) "
        f"VALUES ({row_id}, {user_id}, {value}, '{status}', '1490.00', '{kind}', "
        "'2026-08-20 10:00:00')"
    )


@pytest.fixture
def db_at_0020(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `payments` на ревизии 0020, строками и штампом 0020."""
    db_path = tmp_path / "migration.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(PAYMENTS_AT_0020)
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
    command.stamp(config, "0020")
    return config, db_path


def test_a_second_open_intent_is_accepted_before_the_upgrade(db_at_0020):
    """До ревизии второе незакрытое намерение вставлялось — это и был дефект.

    Половина утверждения об ограничении. Без неё парный тест ниже прошёл бы и на
    схеме, где ограничение существовало изначально, — то есть не доказывал бы,
    что ревизия что-то изменила.
    """
    _, db_path = db_at_0020

    _execute(db_path, _insert(90, user_id=8, payment_id="yoo-90"))

    assert (
        _scalar(
            db_path,
            "SELECT COUNT(*) FROM payments "
            "WHERE user_id = 8 AND kind = 'subscription' AND status = 'pending'",
        )
        == 2
    )


def test_upgrade_creates_the_partial_unique_index(db_at_0020):
    """Индекс появляется, он УНИКАЛЬНЫЙ и он ЧАСТИЧНЫЙ.

    Частичность проверяется не только именем: уникальность на всю колонку
    `user_id` заперла бы пользователя навсегда — ни одного проведённого платежа
    он бы больше не совершил.
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    assert INDEX_NAME in _indexes(db_path, "payments")
    sql = _scalar(
        db_path,
        f"SELECT sql FROM sqlite_master WHERE type='index' AND name='{INDEX_NAME}'",
    )
    assert "UNIQUE" in sql.upper(), f"индекс не уникальный: {sql}"
    assert "WHERE" in sql.upper(), f"индекс не частичный: {sql}"
    assert "kind" in sql and "status" in sql


def test_upgrade_rejects_a_second_open_subscription_intent(db_at_0020):
    """После наката второе незакрытое намерение отвергает СУБД, а не приложение.

    Это и есть требование PAY-01: потолок становится свойством СХЕМЫ. Прикладная
    проверка две одновременные отправки пропускала обе.

    ⚠️ ИМЕНИ ОГРАНИЧЕНИЯ В ТЕКСТЕ ОТКАЗА НА SQLITE НЕТ, И ЭТО ПРОВЕРЕНО, А НЕ
    ПРЕДПОЛОЖЕНО. SQLite сообщает `UNIQUE constraint failed: payments.user_id` —
    то есть КОЛОНКУ, а не индекс; имя индекса приводит только PostgreSQL
    (`duplicate key value violates unique constraint "..."`). Утверждение здесь
    поэтому написано про КОЛОНКУ: оно правдиво на том диалекте, по которому
    идёт суита.

    ⚠️ ЧИТАТЬ ПЕРЕД ПЛАНОМ 08-05. Разбор отказа «по имени ограничения» на суите
    не заработает НИКОГДА: имени в тексте нет. Дословный прецедент проекта
    другой и дичному тексту не доверяет вовсе — `_extend_subscription`
    (app/services/payment_service.py) ловит `IntegrityError`, ПЕРЕЧИТЫВАЕТ
    состояние и, если чужой строки не нашлось, поднимает тот же объект заново.
    Этот приём диалекта не касается и переносится сюда без правок.
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    with pytest.raises(sqlite3.IntegrityError) as failure:
        _execute(db_path, _insert(90, user_id=8, payment_id="yoo-90"))
    assert "payments.user_id" in str(failure.value), (
        "отказ пришёл не от нового индекса: " + str(failure.value)
    )


def test_the_index_is_partial_and_lets_the_neighbours_through(db_at_0020):
    """Предикат ЧАСТИЧНЫЙ: проведённый, просроченный и пакетный проходят.

    ⚠️ `expired` ИСКЛЮЧЁН ПРЕДИКАТОМ НАМЕРЕННО (D-01). Строка в этом статусе
    остаётся оплачиваемой и зачисляемой, и запрещать рядом с ней новое намерение
    значило бы запереть человека, чьё старое намерение сняла зачистка.
    """
    config, db_path = db_at_0020
    command.upgrade(config, "0021")

    _execute(db_path, _insert(90, user_id=8, status="succeeded", payment_id="yoo-90"))
    _execute(db_path, _insert(91, user_id=8, status="expired", payment_id="yoo-91"))
    _execute(db_path, _insert(92, user_id=8, kind="package", payment_id="yoo-92"))

    assert _scalar(db_path, "SELECT COUNT(*) FROM payments WHERE user_id = 8") == 4


def test_backfill_keeps_the_newest_open_intent(db_at_0020):
    """ПРОДУКТОВОЕ ПРАВИЛО ЗАЧИСТКИ: выживает НОВЕЙШЕЕ намерение.

    Правило выбрано так, потому что намерение, созданное за минуту до деплоя,
    обязано продолжать читаться как «в обработке», а не мелькнуть просроченным.
    Проверяется именно оно, а не просто «осталась одна строка»: «одна» вышла бы
    и при неверном выборе.
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    open_rows = _rows(
        db_path,
        "SELECT id FROM payments WHERE user_id = 7 "
        "AND kind = 'subscription' AND status = 'pending' ORDER BY id",
    )
    assert [row["id"] for row in open_rows] == [3], (
        "выжило не новейшее намерение — правило нарушено"
    )
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 1") == "expired"
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 2") == "expired"


def test_backfill_breaks_an_exact_tie_by_highest_id(db_at_0020):
    """Ничья по времени рождения разрывается НАИБОЛЬШИМ id — детерминированно.

    Без явного разрыва ничьей исход зависел бы от плана выполнения запроса: один
    и тот же прогон на боевой базе и на её копии мог бы оставить РАЗНЫЕ строки, и
    расхождение обнаружилось бы уже после наката.
    """
    config, db_path = db_at_0020
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SEED_TIE)
        conn.commit()
    finally:
        conn.close()

    command.upgrade(config, "0021")

    open_rows = _rows(
        db_path,
        "SELECT id FROM payments WHERE user_id = 11 "
        "AND kind = 'subscription' AND status = 'pending'",
    )
    assert [row["id"] for row in open_rows] == [11]


def test_backfill_expires_rather_than_deletes(db_at_0020):
    """Лишняя строка ПЕРЕВОДИТСЯ, а не удаляется: денежный журнал не теряет строк.

    `payments` — след денег. Удалить строку намерения значило бы стереть след
    попытки оплаты, а по такой ссылке человек ещё может заплатить: `expired` не
    входит в терминальные статусы, и уведомление на неё будет принято.
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    assert _scalar(db_path, "SELECT COUNT(*) FROM payments") == 7


def test_backfill_leaves_other_users_and_other_kinds_alone(db_at_0020):
    """Чужие строки, проведённые платежи и пакеты зачисткой не тронуты."""
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 4") == "pending"
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 5") == "pending"
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 6") == "succeeded"
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 7") == "pending"


def test_upgrade_on_clean_data_changes_no_row(db_at_0020):
    """На базе без дублей зачистка не трогает ни одной строки.

    Ноль тронутых строк — тоже свидетельство, и оно уходит в журнал наката.
    """
    config, db_path = db_at_0020
    _execute(db_path, "UPDATE payments SET status = 'expired' WHERE id IN (1, 2)")
    before = _rows(db_path, "SELECT * FROM payments ORDER BY id")

    command.upgrade(config, "0021")

    assert _rows(db_path, "SELECT * FROM payments ORDER BY id") == before


def test_upgrade_makes_the_payment_id_nullable_and_null_rows_coexist(db_at_0020):
    """Колонка идентификатора принимает NULL, и несколько резервов сосуществуют.

    Под порядок «резерв → сеть → дозапись» (план 08-05) строка вставляется ДО
    обращения к ЮKassa. Оба диалекта считают `NULL` различными, поэтому
    уникальность колонки резервам не мешает — второе намерение отвергает НОВЫЙ
    частичный индекс, а не этот.
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    assert _notnull(db_path, "payments", "yookassa_payment_id") == 0
    _execute(db_path, _insert(90, user_id=8, status="expired", payment_id=None))
    _execute(db_path, _insert(91, user_id=8, status="expired", payment_id=None))

    assert (
        _scalar(
            db_path,
            "SELECT COUNT(*) FROM payments WHERE yookassa_payment_id IS NULL",
        )
        == 2
    )


def test_the_unique_index_on_the_payment_id_survives_the_batch_recreate(db_at_0020):
    """⚠️ BATCH-РЕЖИМ ПЕРЕСОЗДАЁТ ТАБЛИЦУ — УНИКАЛЬНОСТЬ ОБЯЗАНА ЕГО ПЕРЕЖИТЬ.

    Уникальность `yookassa_payment_id` — защита от повторной обработки одного
    уведомления. Её молчаливая потеря при пересоздании таблицы обнаружилась бы
    только на боевом приёме денег (T-08-15).
    """
    config, db_path = db_at_0020

    command.upgrade(config, "0021")

    assert PAYMENT_ID_INDEX in _indexes(db_path, "payments")
    _execute(db_path, _insert(90, user_id=8, status="expired", payment_id="yoo-90"))
    with pytest.raises(sqlite3.IntegrityError):
        _execute(db_path, _insert(91, user_id=8, status="expired", payment_id="yoo-90"))


def test_downgrade_drops_the_index_and_accepts_a_second_intent_again(db_at_0020):
    """Откат возвращает СХЕМУ: индекса нет, второе намерение вставляется."""
    config, db_path = db_at_0020
    command.upgrade(config, "0021")

    command.downgrade(config, "0020")

    assert INDEX_NAME not in _indexes(db_path, "payments")
    _execute(db_path, _insert(90, user_id=8, payment_id="yoo-90"))
    assert (
        _scalar(
            db_path,
            "SELECT COUNT(*) FROM payments "
            "WHERE user_id = 8 AND kind = 'subscription' AND status = 'pending'",
        )
        == 2
    )


def test_downgrade_does_not_restore_the_expired_rows(db_at_0020):
    """⚠️ ОДНОСТОРОННОСТЬ ЗАКРЕПЛЕНА ТЕСТОМ, А НЕ ТОЛЬКО ДОКСТРИНГОМ.

    Тест фиксирует ФАКТ, а не объявляет его желаемым: строка 1, переведённая
    накатом, после отката остаётся `expired` — знание о том, какие строки были
    тронуты, ревизия нигде не сохраняет. Тот же класс необратимости, что у
    `0013` и `0018`. Если однажды появится ревизия, умеющая откатывать это
    по-настоящему, падение ЭТОГО теста будет верным сигналом.
    """
    config, db_path = db_at_0020
    command.upgrade(config, "0021")
    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 1") == "expired"

    command.downgrade(config, "0020")

    assert _scalar(db_path, "SELECT status FROM payments WHERE id = 1") == "expired"


def test_rows_survive_upgrade_and_downgrade(db_at_0020):
    """Ни одна строка платежа не потеряна ни накатом, ни откатом.

    Утверждение не декоративное: `payments` — след денег, а зачистка ревизии
    трогает данные, и таблицу дополнительно ПЕРЕСОЗДАЁТ batch-режим. Молчаливая
    пропажа строки обнаружилась бы уже после наката на бой, когда откатывать
    поздно.
    """
    config, db_path = db_at_0020
    ids_before = [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ]

    command.upgrade(config, "0021")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ] == ids_before

    command.downgrade(config, "0020")
    assert [
        row["id"] for row in _rows(db_path, "SELECT id FROM payments ORDER BY id")
    ] == ids_before


def test_revision_0021_continues_0020():
    """0021 продолжает 0020 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))
    heads = script.get_heads()

    assert len(heads) == 1, heads
    assert script.get_revision("0021").down_revision == "0020"


def test_the_backfill_runs_before_the_index_is_created():
    """ПОРЯДОК ШАГОВ — НЕСУЩЕЕ СВОЙСТВО, И ОН ЧИТАЕТСЯ ИЗ ИСХОДНИКА.

    Создание уникального индекса на грязных данных оборвало бы проход
    невыкаченной очереди ПОСЕРЕДИНЕ — в состоянии, из которого нет ни пути
    вперёд, ни отката назад по уже применённым ревизиям (T-08-17). Порядок
    утверждается номерами строк, потому что на чистой тестовой базе оба порядка
    дали бы одинаковый результат — то есть поведением он здесь не ловится.
    """
    lines = REVISION_FILE.read_text().splitlines()
    backfill = next(
        i for i, line in enumerate(lines) if "_EXPIRE_OLDER_INTENTS" in line and "connection.execute" in line
    )
    create_index = next(i for i, line in enumerate(lines) if "op.create_index" in line)

    assert backfill < create_index, "индекс создаётся ДО зачистки — порядок нарушен"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013/0014/0017/0018.

    Импорт из `app.*` связал бы уже применённую миграцию с текущим кодом, и
    переименование константы задним числом изменило бы смысл давно выполненного
    шага. Проверяется РАЗБОРОМ ДЕРЕВА, а не подстрокой: `import app` встречается
    в комментариях и докстрингах ревизии, которые запрета не нарушают.
    """
    import ast

    tree = ast.parse(REVISION_FILE.read_text())
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    offenders = [name for name in imported if name == "app" or name.startswith("app.")]
    assert not offenders, offenders
