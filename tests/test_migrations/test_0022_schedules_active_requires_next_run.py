"""Round-trip ревизии 0022: «включённое расписание обязано иметь момент запуска» в СХЕМЕ.

Файл существует по той же причине, что `test_0018_subscriptions_unique_user.py` и
`test_0021_payments_open_intent_index.py`: суита строит схему через
`Base.metadata.create_all` (tests/conftest.py) и о существовании Alembic не знает,
поэтому текст ревизии не исполняется НИ В ОДНОМ обычном тесте. Совпадение модели
и ревизии здесь не предполагается — проверяется.

⚠️ И ЭТУ ПАРУ НЕ СВЕРЯЕТ НИКТО ДРУГОЙ. `test_model_matches_head.py` сверяет ОДНУ
таблицу (`payments`) и только СОСТАВ ЕЁ КОЛОНОК — так и написано в его шапке.
Ограничение, объявленное в модели и забытое в очереди ревизий, он не заметил бы
вовсе: на боевой базе такого ограничения просто не было бы, а вся суита при этом
зеленела бы, потому что её схема строится из модели.

ПРОВЕРЯЕМОГО ЗДЕСЬ ТРИ ПРЕДМЕТА, А НЕ ОДИН.

**Первый — само ограничение.** Пара `is_active = true` + `next_run_at IS NULL`
отвергается базой, остальные три пары принимаются. Перечисление законных пар
обязательно: ограничение «запретить всё» прошло бы проверку из одного
отрицательного случая, а задело бы приостановленные расписания — самое частое
состояние таблицы.

**Второй — зачистка ДО создания ограничения.** Ревизия выключает нарушившие
строки, не трогая `days_of_week` и `times_of_day`. Порядок несущий: создание
ограничения на грязных данных оборвало бы проход невыкаченной очереди
ПОСЕРЕДИНЕ. А состав правки продуктовый — выключить, но не дозаполнять и не
удалять, — и он обязан проверяться, а не подразумеваться: дозаполнение
означало бы отправку в дни, которых человек не назначал.

**Третий — ПЕРЕЖИВАНИЕ BATCH-ПЕРЕСОЗДАНИЯ, и он тут самый зубастый.** На SQLite
ограничение добавляется пересозданием таблицы целиком, и пересоздание дважды
теряло существенное МОЛЧА — обе потери найдены измерением, а не рассуждением:

  - на ОТРАЖЕНИИ терялись правила внешних ключей (`ON DELETE SET NULL` на
    `account_id` превращался в `NO ACTION`) — то есть отменялась ревизия `0012`
    и возвращался issue #35: удаление messenger-аккаунта снова уносило бы
    расписания каскадом;

  - после перехода на `copy_from` терялись ОБА ИНДЕКСА, потому что Alembic
    пропускает при пересоздании индексы, заведённые сокращением `index=True`
    (признак `_column_flag` в `alembic/operations/batch.py`). Среди потерянных —
    `ix_schedules_next_run_at`, по которому идёт САМ ОТБОР К ОТПРАВКЕ.

Ни одна из потерь не сопровождалась предупреждением, и ни одну из них не поймал
бы тест, проверяющий только ограничение. Поэтому они проверяются здесь поимённо.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он идёт по SQLite, а бой — PostgreSQL, где
ветка ревизии ДРУГАЯ (`ALTER TABLE ... ADD CONSTRAINT`, без пересоздания и без
участия внешних ключей). Совпадение поведения двух диалектов здесь не
доказывается и доказано быть не может; проверяется то, что проверяемо машиной, а
про боевую ветку сказано в шапке ревизии прямо. Равно и о накате: ревизия
СОЗДАНА и не применена ни к одной базе.

ТРИ РЕШЕНИЯ, ПОВТОРЁННЫЕ У `test_0021`. Причины переписаны целиком, а не
заменены ссылкой: файл, объясняющий себя ссылкой на соседа, теряет объяснение
при первой же правке соседа.

**Файловая база, а не база в памяти.** Alembic открывает СОБСТВЕННОЕ соединение
(`alembic/env.py` создаёт свой async-движок), а содержимое SQLite, живущей в
оперативной памяти, между соединениями не сохраняется.

**Тест синхронный.** `alembic/env.py` в online-режиме сам вызывает `asyncio.run`;
внутри уже работающего цикла pytest-asyncio это упало бы RuntimeError.

**Стартовая ревизия `0021` названа явно и отмечена штампом.** Прогон от нуля на
SQLite до цели не доходит: ревизия `0005` использует `op.drop_constraint`, на
котором Alembic под SQLite поднимает `NotImplementedError`. Это свойство ЧУЖИХ
ревизий, к `0022` отношения не имеющее. Поэтому фикстура сама приводит базу в
состояние «схема `schedules` на ревизии `0021` + строки в ней», штампует её и
запускает НАСТОЯЩИЕ `upgrade`/`downgrade`.

ПО КАКИМ РЕВИЗИЯМ СОБРАН СНИМОК. `0001_initial_schema.py` — сама таблица и оба
индекса; `0002_add_schedule_timezone.py` — `timezone`;
`0012_schedules_account_id_nullable_set_null.py` — `account_id` стал
NULL-совместимым с `ON DELETE SET NULL`. Между `0012` и `0021` таблицу не
трогала ни одна ревизия, поэтому этот же состав и есть её состояние на `0021`.
Таблицы `ads` и `messenger_accounts` лежат в снимке не ради проверки, а чтобы
внешним ключам было на что ссылаться при пересоздании.
"""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"
REVISION_FILE = (
    REPO_ROOT / "alembic" / "versions" / "0022_schedules_active_requires_next_run.py"
)

CONSTRAINT_NAME = "ck_schedules_active_requires_next_run"

SCHEDULES_AT_0021 = """
CREATE TABLE ads (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL
);

CREATE TABLE messenger_accounts (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL
);

CREATE TABLE schedules (
    id INTEGER NOT NULL PRIMARY KEY,
    ad_id INTEGER NOT NULL REFERENCES ads(id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES messenger_accounts(id) ON DELETE SET NULL,
    group_ids JSON NOT NULL DEFAULT '[]',
    days_of_week JSON NOT NULL DEFAULT '[]',
    times_of_day JSON NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT true,
    next_run_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC'
);

CREATE INDEX ix_schedules_is_active ON schedules (is_active);
CREATE INDEX ix_schedules_next_run_at ON schedules (next_run_at);
"""

# Строки подобраны так, чтобы зачистка ОТЛИЧАЛАСЬ от «выключить всё».
# id=1 — форма промышленной строки sched=48: включена, момента запуска нет,
#        дни пусты. Единственная, которую ревизия обязана тронуть.
# id=2 — работающее расписание. Его трогать нельзя ни при каких обстоятельствах.
# id=3 — приостановленное без момента. Законно и до, и после ревизии.
# id=4 — приостановленное С моментом. Вторая законная пара, её легко задеть
#        неаккуратным условием вида `next_run_at IS NULL`.
SEED_ROWS = """
INSERT INTO ads (id, user_id, title) VALUES (1, 1, 'Объявление');
INSERT INTO messenger_accounts (id, user_id, type) VALUES (1, 1, 'tg_user');

INSERT INTO schedules
    (id, ad_id, account_id, group_ids, days_of_week, times_of_day, is_active, next_run_at)
VALUES
    (1, 1, 1, '[1126]', '[]',    '["09:00","15:15"]', 1, NULL),
    (2, 1, 1, '[1126]', '[0,3]', '["09:00"]',         1, '2026-09-12 06:00:00'),
    (3, 1, 1, '[1126]', '[0]',   '["09:00"]',         0, NULL),
    (4, 1, 1, '[1126]', '[0]',   '["09:00"]',         0, '2026-09-12 06:00:00');
"""


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


def _indexes(db_path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA index_list({table})")}
    finally:
        conn.close()


def _delete_rules(db_path: Path, table: str) -> dict[str, str]:
    """Правило `ON DELETE` по каждой колонке-ссылке — из PRAGMA, а не из DDL."""
    conn = sqlite3.connect(db_path)
    try:
        return {row[3]: row[6] for row in conn.execute(f"PRAGMA foreign_key_list({table})")}
    finally:
        conn.close()


def _insert(
    row_id: int, *, is_active: int, next_run_at: str | None = None
) -> str:
    value = "NULL" if next_run_at is None else f"'{next_run_at}'"
    return (
        "INSERT INTO schedules (id, ad_id, account_id, is_active, next_run_at) "
        f"VALUES ({row_id}, 1, 1, {is_active}, {value})"
    )


@pytest.fixture
def db_at_0021(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой `schedules` на ревизии 0021, строками и штампом 0021."""
    db_path = tmp_path / "migration_0022.db"

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEDULES_AT_0021)
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
    command.stamp(config, "0021")
    return config, db_path


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 1 — ограничение
# ─────────────────────────────────────────────────────────────────────────────


def test_a_dead_row_is_accepted_before_the_upgrade(db_at_0021):
    """До ревизии мёртвая строка вставлялась — это и был дефект.

    Половина утверждения об ограничении. Без неё парный тест ниже зеленел бы и
    на схеме, где ограничение существовало изначально, — то есть не доказывал бы,
    что его добавила ИМЕННО ЭТА ревизия.
    """
    _, db_path = db_at_0021

    _execute(db_path, _insert(50, is_active=1, next_run_at=None))

    assert _rows(db_path, "SELECT id FROM schedules WHERE id = 50") == [{"id": 50}]


def test_upgrade_refuses_an_active_schedule_without_a_next_run(db_at_0021):
    """⚠️ ГЛАВНОЕ: после ревизии такую строку не принимает САМА ТАБЛИЦА."""
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        _execute(db_path, _insert(50, is_active=1, next_run_at=None))

    assert CONSTRAINT_NAME in str(excinfo.value)


@pytest.mark.parametrize(
    "is_active,next_run_at,case",
    [
        pytest.param(0, None, "приостановленное без момента запуска", id="paused_null"),
        pytest.param(0, "2026-09-12 06:00:00", "приостановленное с моментом", id="paused_with_next_run"),
        pytest.param(1, "2026-09-12 06:00:00", "работающее расписание", id="active_with_next_run"),
    ],
)
def test_upgrade_keeps_the_three_legal_combinations(
    db_at_0021, is_active, next_run_at, case
):
    """⚠️ БЕЗ ЭТОГО ТЕСТА ОГРАНИЧЕНИЕ «ЗАПРЕТИТЬ ВСЁ» БЫЛО БЫ ЗЕЛЁНЫМ.

    Особенно важна первая строка: приостановленное расписание без момента
    запуска — самое частое состояние в таблице, и ограничение, задевшее его,
    сломало бы тумблер целиком.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")
    _execute(db_path, _insert(50, is_active=is_active, next_run_at=next_run_at))

    assert _rows(db_path, "SELECT id FROM schedules WHERE id = 50") == [{"id": 50}], case


def test_the_constraint_also_bites_on_update(db_at_0021):
    """Запрет держится и на UPDATE, а не только на вставке.

    Живую строку убивает именно обновление: расписание было отправляемым, ему
    обнулили момент запуска, и оно замолчало.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    with pytest.raises(sqlite3.IntegrityError):
        _execute(db_path, "UPDATE schedules SET next_run_at = NULL WHERE id = 2")


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 2 — зачистка
# ─────────────────────────────────────────────────────────────────────────────


def test_backfill_switches_the_dead_row_off(db_at_0021):
    """Нарушившая строка выключается — иначе ревизия не прошла бы вовсе."""
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    assert _rows(db_path, "SELECT is_active FROM schedules WHERE id = 1") == [
        {"is_active": 0}
    ]


def test_backfill_does_not_invent_days_or_times(db_at_0021):
    """⚠️ ПРОДУКТОВОЕ РЕШЕНИЕ: выключить, но НЕ ДОЗАПОЛНЯТЬ и не удалять.

    Угадать задуманные владельцем дни — фабрикация: расписание начало бы слать в
    дни, которых человек не назначал. Оставленные нетронутыми часы и группы и
    есть точка восстановления: человек дозаполняет расписание в редакторе, жмёт
    тумблер, и момент запуска считается обычным путём.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    assert _rows(
        db_path, "SELECT days_of_week, times_of_day, group_ids FROM schedules WHERE id = 1"
    ) == [
        {
            "days_of_week": "[]",
            "times_of_day": '["09:00","15:15"]',
            "group_ids": "[1126]",
        }
    ]


def test_backfill_leaves_every_legal_row_alone(db_at_0021):
    """Зачистка трогает ОДНУ строку из четырёх, а не «выключает всё».

    Работающее расписание (id=2) обязано остаться работающим: ревизия,
    выключившая живую рассылку, стоила бы дороже дефекта, который она чинит.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    assert _rows(
        db_path, "SELECT id, is_active, next_run_at FROM schedules WHERE id > 1 ORDER BY id"
    ) == [
        {"id": 2, "is_active": 1, "next_run_at": "2026-09-12 06:00:00"},
        {"id": 3, "is_active": 0, "next_run_at": None},
        {"id": 4, "is_active": 0, "next_run_at": "2026-09-12 06:00:00"},
    ]


def test_upgrade_on_clean_data_changes_no_row(db_at_0021):
    """На чистой базе ревизия — чистая правка схемы.

    Нарушитель удаляется ДО наката, и после него состав таблицы обязан совпасть
    с исходным до строки. Иначе «зачистка» означала бы побочное действие,
    зависящее не от грязи, а от самого факта наката.
    """
    config, db_path = db_at_0021
    _execute(db_path, "DELETE FROM schedules WHERE id = 1")
    before = _rows(db_path, "SELECT * FROM schedules ORDER BY id")

    command.upgrade(config, "0022")

    assert _rows(db_path, "SELECT * FROM schedules ORDER BY id") == before


def test_the_backfill_runs_before_the_constraint_is_created():
    """ПОРЯДОК ШАГОВ — НЕСУЩЕЕ СВОЙСТВО, И ОН ЧИТАЕТСЯ ИЗ ИСХОДНИКА.

    Создание ограничения на грязных данных оборвало бы проход невыкаченной
    очереди ПОСЕРЕДИНЕ — в состоянии, из которого нет ни пути вперёд, ни отката
    назад по уже применённым ревизиям. Порядок утверждается номерами строк,
    потому что на ЧИСТОЙ тестовой базе оба порядка дали бы одинаковый результат
    — то есть поведением он здесь не ловится.
    """
    lines = REVISION_FILE.read_text(encoding="utf-8").splitlines()
    backfill = next(
        i for i, line in enumerate(lines) if "_DEACTIVATE_DEAD_ROWS" in line and "connection.execute" in line
    )
    create = next(i for i, line in enumerate(lines) if "create_check_constraint" in line)

    assert backfill < create, "ограничение создаётся ДО зачистки — порядок нарушен"


# ─────────────────────────────────────────────────────────────────────────────
# ПРЕДМЕТ 3 — переживание пересоздания таблицы
# ─────────────────────────────────────────────────────────────────────────────


def test_both_indexes_survive_the_batch_recreate(db_at_0021):
    """⚠️ ОБА ИНДЕКСА ТЕРЯЛИСЬ МОЛЧА — ЭТО ИЗМЕРЕНО, А НЕ ПРЕДПОЛОЖЕНО.

    Alembic пропускает при пересоздании индексы, заведённые сокращением
    `index=True` у колонки (признак `_column_flag`). Среди потерянных был
    `ix_schedules_next_run_at` — тот самый, по которому идёт отбор к отправке:
    таблица осталась бы рабочей и молча медленной.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    assert _indexes(db_path, "schedules") >= {
        "ix_schedules_is_active",
        "ix_schedules_next_run_at",
    }


def test_the_on_delete_rules_survive_the_batch_recreate(db_at_0021):
    """⚠️ `ON DELETE SET NULL` ТЕРЯЛСЯ МОЛЧА — ЭТО ОТМЕНА `0012` И ВОЗВРАТ #35.

    Отражение SQLite в SQLAlchemy не переносит `ON DELETE` вовсе, и первая
    версия ревизии, полагавшаяся на отражение, оставляла оба ключа с
    `NO ACTION`. Для `account_id` это значит, что удаление messenger-аккаунта
    снова уносило бы расписания, вместо того чтобы отвязывать их, — ровно то,
    что `0012` запрещала.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")

    assert _delete_rules(db_path, "schedules") == {
        "ad_id": "CASCADE",
        "account_id": "SET NULL",
    }


def test_rows_survive_upgrade_and_downgrade(db_at_0021):
    """Строки переживают оба прохода — пересоздание не теряет данные."""
    config, db_path = db_at_0021
    before = _rows(db_path, "SELECT id, ad_id, account_id, group_ids, days_of_week, times_of_day, timezone FROM schedules ORDER BY id")

    command.upgrade(config, "0022")
    command.downgrade(config, "0021")

    assert _rows(db_path, "SELECT id, ad_id, account_id, group_ids, days_of_week, times_of_day, timezone FROM schedules ORDER BY id") == before


def test_downgrade_drops_the_constraint_and_accepts_a_dead_row_again(db_at_0021):
    """Обратный проход возвращает СХЕМУ — и это проверяется поведением."""
    config, db_path = db_at_0021

    command.upgrade(config, "0022")
    command.downgrade(config, "0021")
    _execute(db_path, _insert(50, is_active=1, next_run_at=None))

    assert _rows(db_path, "SELECT id FROM schedules WHERE id = 50") == [{"id": 50}]


def test_downgrade_does_not_switch_the_backfilled_row_back_on(db_at_0021):
    """⚠️ ОТКАТ ВОЗВРАЩАЕТ СХЕМУ, НО НЕ ДАННЫЕ — тот же класс, что `0018`/`0021`.

    Знанию о том, какие именно строки выключил накат, взяться неоткуда:
    выключенное накатом неотличимо от выключенного человеком. Асимметрия
    закрепляется тестом, чтобы её не приняли за недоделку и не «починили»
    включением всех выключенных строк подряд.
    """
    config, db_path = db_at_0021

    command.upgrade(config, "0022")
    command.downgrade(config, "0021")

    assert _rows(db_path, "SELECT is_active FROM schedules WHERE id = 1") == [
        {"is_active": 0}
    ]


def test_the_indexes_survive_the_downgrade_too(db_at_0021):
    """Обратный проход тоже пересоздаёт таблицу — и тоже обязан их сохранить."""
    config, db_path = db_at_0021

    command.upgrade(config, "0022")
    command.downgrade(config, "0021")

    assert _indexes(db_path, "schedules") >= {
        "ix_schedules_is_active",
        "ix_schedules_next_run_at",
    }


# ─────────────────────────────────────────────────────────────────────────────
# ШОВ МОДЕЛИ И РЕВИЗИИ
# ─────────────────────────────────────────────────────────────────────────────


def test_the_revision_condition_matches_the_model_word_for_word():
    """⚠️ ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ДВЕ ПОЛОВИНЫ ВООБЩЕ СВЕРЯЮТСЯ.

    Ревизия не импортирует из `app.*` — она описывает схему на СВОЙ момент
    времени (правило `0013`/`0017`/`0018`/`0021`), поэтому условие выписано в ней
    строкой. Цена правила — два текста одного условия; плата за неё вносится
    здесь. Разойдись они, ограничение на бою запрещало бы не то, что модель
    обещает суите, и суита об этом молчала бы.
    """
    import importlib.util

    from app.models.schedule import (
        ACTIVE_REQUIRES_NEXT_RUN,
        ACTIVE_REQUIRES_NEXT_RUN_NAME,
    )

    spec = importlib.util.spec_from_file_location("revision_0022", REVISION_FILE)
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)

    assert revision.CONDITION == ACTIVE_REQUIRES_NEXT_RUN
    assert revision.CONSTRAINT_NAME == ACTIVE_REQUIRES_NEXT_RUN_NAME


def test_revision_0022_continues_0021():
    """0022 продолжает 0021 — история ревизий остаётся одной линией.

    Ветвление ломает накат сразу для всех, поэтому проверяется КОЛИЧЕСТВО голов,
    а не имя головы: имя меняется с каждой новой ревизией и свойством истории не
    является.
    """
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(ALEMBIC_INI)))

    assert len(script.get_heads()) == 1, script.get_heads()
    assert script.get_revision("0022").down_revision == "0021"


def test_the_revision_does_not_import_from_the_application():
    """Ревизия описывает схему на СВОЙ момент времени — правило 0013/0017/0018/0021.

    Импорт из `app.*` связал бы уже применённую миграцию с текущим кодом, и
    переименование константы задним числом изменило бы смысл давно выполненного
    шага. Проверяется РАЗБОРОМ ДЕРЕВА, а не подстрокой: `app.` встречается в
    комментариях и докстринге ревизии, которые запрета не нарушают.
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
