# Phase 16: Хранение номера, нормализация и единый писатель - Pattern Map

**Mapped:** 2026-10-08
**Files analyzed:** 17 (новые и правимые)
**Analogs found:** 16 / 17 (у JS-токенизатора гейта приватности аналога нет)

Все пути ниже — отслеживаемые git исходники (проверено `git ls-files`). Номера строк сняты с текущего дерева ветки `gsd/phase-16-…`.

## File Classification

| Новый/правимый файл | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `alembic/versions/0023_messenger_account_phone.py` | migration | DDL (batch, CHECK) | `alembic/versions/0022_schedules_active_requires_next_run.py` (+ `0014_sync_result_and_group_missing.py` — колонки `messenger_accounts`) | exact |
| `app/models/messenger_account.py` (правка) | model | CRUD | `app/models/schedule.py:40-57` (константы CHECK + `__table_args__`) | exact |
| `app/services/phone.py` | utility (чистые функции) | transform | `app/services/schedule_rules.py` (нейтральный модуль правил, шапка-обоснование) | role-match |
| `app/application/accounts/phone.py` | service (сценарий, единый писатель) | CRUD, условная запись | `app/application/accounts/use_cases.py:69-89` + `app/services/payment_service.py:811-845` (`_claim_payment`, `_mirror_claim`) | exact |
| `tests/test_migrations/test_0023_messenger_account_phone.py` | test (migration) | file-I/O (файловая SQLite) | `tests/test_migrations/test_0022_schedules_active_requires_next_run.py` | exact |
| `tests/test_migrations/test_model_matches_head.py` (расширение) | test (migration) | file-I/O | сам файл: `test_every_mapped_payment_column_exists_at_head` (`:298-319`), контроль `:281-295` | exact |
| `tests/test_services/test_phone.py` | test (unit, табличный) | transform | `tests/test_services/test_schedule_rules_gate.py` / `pytest.mark.parametrize` из `test_0022:248-270` | role-match |
| `tests/test_application/test_account_phone_writer.py` | test (unit, `db_session`) | CRUD | `tests/test_application/test_account_deletion_schedules.py`, `test_group_resync.py` (шапка-спецификация) | role-match |
| `tests/test_application/test_account_phone_race.py` | test (integration) | конкурентная запись | `tests/test_services/test_payment_concurrency.py:80-136` | exact |
| `tests/test_application/test_phone_single_writer_gate.py` | test (AST-гейт) | batch (обход дерева) | `tests/test_application/test_no_metering_remains.py:83-135,245-262` + `test_declared_invariants.py` (AST, потолок) | exact |
| `tests/test_phone_privacy_gate.py` | test (AST + JS-гейт) | batch | Python-половина — те же; JS-половина — **аналога нет** | partial |
| `tests/test_planning/test_deferred_items_are_idempotent.py` (правка) | test (records) | file-I/O | сам файл, `_require_live_phases` `:168-181` | exact |
| `tests/test_planning/test_requirement_completion_follows_verification.py` (правка) | test (records) | file-I/O | сам файл, `:99`, `:205`, `:999-1046`, `_fake_planning_root` `:470-530` | exact |
| `tests/test_planning/test_state_progress_matches_roadmap.py` (правка) | test (records) | file-I/O | сам файл, `roadmap_plan_counts` `:69`, правило `:312-355`, синтет. контроли `:506-545` | exact |
| реестр запретов (сев) `.planning/milestones/v2.1-phases/15-…/15-prohibitions-registry.yaml` | config (records) | batch | `scripts/prohibitions_census.py --seed-registry` (`:755` `seed_registry`, CLI `:1773-1779`) | штатное средство |
| `pyproject.toml` / `uv.lock` | config | — | `just add` (justfile:58-60) | штатное средство |

## Pattern Assignments

### `alembic/versions/0023_messenger_account_phone.py` (migration)

**Аналог:** `alembic/versions/0022_schedules_active_requires_next_run.py`; колонки — `0014_sync_result_and_group_missing.py:30-57`.

**Шапка и литералы** (0022:160-180; правило «не импортировать `app.*`» — 0014:33-36):
```python
"""…ЗАЧЕМ / ПОЧЕМУ В СХЕМЕ… (длинный русский докстринг; назвать границу PG-ветки — не исполнялась, A1)

Revision ID: 0023
Revises: 0022
"""
from alembic import op
import sqlalchemy as sa

revision = "0023"
down_revision = "0022"

TABLE = "messenger_accounts"
CONSTRAINT_NAME = "ck_messenger_accounts_manual_requires_phone"   # дискреция
# Дословно то же стоит в app/models/messenger_account.py; совпадение сверяет тест.
CONDITION = "NOT (phone_is_manual AND phone IS NULL)"
```

**Явный состав для `copy_from`** (образец `_schedules(*, with_constraint)` 0022:185-243). Для `messenger_accounts` на `0022` состав (RESEARCH §Ревизия, из `0001:56-75` + `0014:40-47`): `id` PK; `user_id Integer ForeignKey("users.id", ondelete="CASCADE") NOT NULL`; `type String(20) NOT NULL`; `credentials Text NOT NULL`; `session_data Text NULL`; `status String(20) NOT NULL server_default="disconnected"`; `created_at DateTime(timezone=True) server_default=sa.func.now() NOT NULL`; `last_synced_at DateTime(timezone=True) NULL`; `last_sync_result Text NULL`. Индексов нет. Параметры функции: `with_new: bool, with_constraint: bool`.

**Ветки диалектов** (0022:263-289):
```python
def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        op.add_column(TABLE, sa.Column("phone", sa.String(16), nullable=True))
        op.add_column(TABLE, sa.Column("phone_is_manual", sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
        op.create_check_constraint(CONSTRAINT_NAME, TABLE, CONDITION)
    else:
        with op.batch_alter_table(TABLE, copy_from=_accounts(with_new=False, with_constraint=False)) as batch_op:
            batch_op.add_column(...phone...)
            batch_op.add_column(...phone_is_manual...)
            batch_op.create_check_constraint(CONSTRAINT_NAME, CONDITION)

def downgrade():  # обратный порядок; SQLite — copy_from=_accounts(with_new=True, with_constraint=True)
    ...drop_constraint(CONSTRAINT_NAME, type_="check"); drop_column("phone_is_manual"); drop_column("phone")
```
Зачистки данных нет (колонки новые), поэтому блок `_COUNT_DEAD_ROWS`/`log.info` из 0022 не переносится. Без `copy_from` теряется `ON DELETE CASCADE` у `user_id` (0022:115-125).

---

### `app/models/messenger_account.py` (model, правка)

**Аналог:** `app/models/schedule.py:40-57`:
```python
# Текст условия ДОСЛОВНО повторён в ревизии `0022` строкой — …
# Совпадение двух половин проверяется тестами …
ACTIVE_REQUIRES_NEXT_RUN = "NOT (is_active AND next_run_at IS NULL)"
ACTIVE_REQUIRES_NEXT_RUN_NAME = "ck_schedules_active_requires_next_run"

class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = (
        CheckConstraint(ACTIVE_REQUIRES_NEXT_RUN, name=ACTIVE_REQUIRES_NEXT_RUN_NAME),
    )
```
**Стиль колонок с комментарием-обоснованием** — в самом файле, `last_synced_at` (строки 20-29): абзац «D-NN: …», затем `Mapped[... | None] = mapped_column(..., nullable=True)`. Новые: `phone: Mapped[str | None] = mapped_column(String(16), nullable=True)`, `phone_is_manual: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())`. Импорт расширить: `from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, false, func`.

---

### `app/services/phone.py` (utility, transform)

**Аналог:** `app/services/schedule_rules.py:1-40` — нейтральный модуль правил: длинная русская шапка (ЧТО модуль решает и что оставляет вызывающему; «правило одно, политика у входа своя» — ровно разделение `normalize_manual` бросает / `normalize_reported` отдаёт `None`), функции-предикаты без БД. Для `phone.py` БД не нужна вовсе — импорты только `phonenumbers` и stdlib.

**Ядро** — из RESEARCH §Code Examples (замерено), без аналога в коде:
```python
n = phonenumbers.parse(text, "RU")          # NumberParseException → PhoneError("…") по-русски
if n.extension: raise PhoneError(...)
if phonenumbers.is_possible_number_with_reason(n) != phonenumbers.ValidationResult.IS_POSSIBLE:
    raise PhoneError("Не похоже на номер телефона. Пример: +7 999 123-45-67")
```
Автопуть — правило RESEARCH:263 (bool отсечь, `str().strip()`, снять `+`, только цифры 5…15, `parse("+"+s, None)`); показ — `format_number(..., INTERNATIONAL)`, на `NumberParseException` — как есть; маска — RESEARCH §Маска D-10 (код страны из `n.country_code`).

---

### `app/application/accounts/phone.py` (service, единый писатель)

**Аналог 1 — форма слоя:** `app/application/accounts/use_cases.py`
Импорты (`:1-12`):
```python
from __future__ import annotations
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.messenger_account import MessengerAccount
```
Сценарий, `session` первым аргументом, не коммитит (`:69-89`):
```python
async def detach_schedules_from_account(session: AsyncSession, account_id: int) -> int:
    """… Не коммитит: транзакцией владеет вызывающая сторона …"""
    result = await session.execute(
        update(Schedule)
        .where(Schedule.account_id == account_id)
        .values(is_active=False, next_run_at=None, account_id=None)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount or 0
```
**Аналог 2 — compare-and-swap:** `app/services/payment_service.py:811-839` (`_claim_payment`) — докстринг «ЭТО COMPARE-AND-SWAP, А НЕ ПРОВЕРКА С ПОСЛЕДУЮЩЕЙ ЗАПИСЬЮ… РАБОТАЕТ ОДИНАКОВО НА PostgreSQL И НА SQLite» переносится по смыслу; условие в том же операторе:
```python
.where(MessengerAccount.id == account_id,
       MessengerAccount.phone.is_(None),
       MessengerAccount.phone_is_manual.is_(False))
.values(phone=e164)
.execution_options(synchronize_session=False)
return PhoneWrite.WRITTEN if result.rowcount == 1 else PhoneWrite.KEPT
```
**Отзеркаливание на объект** (`record_reported_phone`): `_mirror_claim` `:842-…` — `set_committed_value`, а не присваивание (иначе второй UPDATE на коммите и нарушение гейта D-13).
**Очистка** — один `UPDATE … values(phone=None, phone_is_manual=False)`: CHECK отвергает очистку одной колонкой.

---

### `tests/test_migrations/test_0023_messenger_account_phone.py`

**Аналог:** `tests/test_migrations/test_0022_schedules_active_requires_next_run.py` (537 строк).
- Импорты `:81-86`: `sqlite3`, `Path`, `pytest`, `from alembic import command`, `from alembic.config import Config`.
- Помощники `:147-190`: `_rows`, `_execute`, `_indexes(db_path, table)`, `_delete_rules(db_path, table)`, `_insert` — копировать.
- Фикстура `:192-214` (переименовать в `db_at_0022`, снимок `users`, `messenger_accounts` полного состава, `groups`, `ads`, `schedules`):
```python
@pytest.fixture
def db_at_0021(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    db_path = tmp_path / "migration_0022.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEDULES_AT_0021); conn.executescript(SEED_ROWS); conn.commit()
    finally:
        conn.close()
    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL … без этого ревизия ушла бы на ЖИВУЮ базу.
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0021")
    return config, db_path
```
- Три законные пары — `@pytest.mark.parametrize` `:248-270`; CHECK на UPDATE — `:273-290`; FK — `:402-418` (`_delete_rules(...) == {...}`); round-trip — `:421-441`; сверка с моделью через `importlib.util.spec_from_file_location` — `:479-500`; одна голова истории — `:503+`. Предметы 1–7 — RESEARCH §Тест ревизии.

---

### `tests/test_migrations/test_model_matches_head.py` (расширение)

- Снимок `messenger_accounts` (`:174-179`, 4 колонки) заменить полным составом на `0019` (RESEARCH:336) с летописью в комментарии над `SCHEMA_AT_START` (`:102`): прежняя граница «только колонки, без которых таблица не создаётся» названа и заменена с причиной (`no such column: messenger_accounts.session_data`).
- Новая проверка по образцу `:298-319`:
```python
mapped = {column.name for column in MessengerAccount.__table__.columns}
actual = _table_columns(db_at_head, "messenger_accounts")
absent = missing_columns(mapped, actual)
assert not absent, (...)
```
- Контроль-отрицание по образцу `:281-295`: `missing_columns(mapped, mapped - {"phone"}) == ["phone"]`.
- Шапку «ГРАНИЦА ОБЪЁМА… ОДНА таблица» переписать с летописью («было `payments`, стало две»).

---

### `tests/test_services/test_phone.py` (unit, табличный)

Аналог формы — `pytest.mark.parametrize` с поимёнными строками (`test_0022:248-256`). Строки — RESEARCH:213-289 и Validation Map SC3 поимённо (включая О-1: ручной `+888 0123 4567` → `PhoneError`, ручной `88801234567` → `+78801234567` закреплено явно). Шапка-спецификация в стиле `tests/test_application/test_group_resync.py:1-22` («ключевое утверждение файла — …»).

---

### `tests/test_application/test_account_phone_writer.py` (unit, `db_session`)

Аналог — `tests/test_application/test_account_deletion_schedules.py` (сценарий `detach_schedules_from_account` на фикстуре `db_session` из `tests/conftest.py`) и шапка `test_group_resync.py:1-22`. Последовательные случаи — RESEARCH:378; CHECK на `create_all` ловится `IntegrityError` (`pytest.raises(sqlalchemy.exc.IntegrityError)`).

---

### `tests/test_application/test_account_phone_race.py` (integration)

**Аналог:** `tests/test_services/test_payment_concurrency.py`.
Фикстура `:80-87`:
```python
@pytest_asyncio.fixture
async def sessions(tmp_path):
    """Фабрика НЕЗАВИСИМЫХ сессий поверх ОДНОЙ файловой базы."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'concurrency.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()
```
Подмена `execute` `:119-136`:
```python
def _interleave_after_first_read(session, second_delivery):
    original = session.execute
    fired = {"done": False}
    async def wrapper(*args, **kwargs):
        result = await original(*args, **kwargs)
        if not fired["done"]:
            fired["done"] = True
            await second_delivery()
        return result
    session.execute = wrapper
```
Отличия для фазы 16 (RESEARCH:357-377): ручная запись ПЕРЕД k-м `execute` (не после), позиции `1…N` из измеренного `N` плюс `0` (после коммита); флаг `fired` утверждается в каждой позиции (ловушка вакуума); отрицание — тестовая `read_check_write` через тот же помощник, позиция 2 обязана дать `('+79990000002', True)`. Сид — по образцу `_seed(factory, …)` `:90-110` (User + MessengerAccount, `commit`, `refresh`).

---

### `tests/test_application/test_phone_single_writer_gate.py` (AST-гейт D-13)

**Аналог:** `tests/test_application/test_no_metering_remains.py`.
Обход дерева параметром `root` (`:83-92`):
```python
def application_sources(root: Path) -> list[Path]:
    """Все исходники приложения — ОБХОДОМ каталога, а не перечнем. … натравить на СИНТЕТИЧЕСКОЕ дерево."""
    return sorted(root.rglob("*.py"))
```
Находки строкой «файл :: что» (`:95-104`), основной тест `assert hits == [], (... "\n".join(...))` (`:107-115`), подложенный файл в `tmp_path` (`:118-135`), антивакуум `test_the_gate_reads_a_real_and_non_empty_tree` (`:245-262`: `len(sources) > N`, нужные модули в множестве — здесь `app/application/accounts/phone.py` существует и несёт `update(` с `phone`).
AST-обход и синтетические исходники как зубы — `tests/test_application/test_declared_invariants.py:222-300` (`ast.parse`, `ast.walk`, `isinstance(node, (ast.FunctionDef, …))`). Реестр `PHONE_WRITER_EXCEPTIONS: dict[str, str]` по образцу `FORBIDDEN_NAMES` (`:60-80`: пары «что → причина»). Предикат (5 видов) — RESEARCH:393.

---

### `tests/test_phone_privacy_gate.py` (AST + JS-гейт PHONE-21)

Python-половина — те же аналоги, что у гейта писателя (обход с `root`, синтетика, антивакуум по каждому из четырёх деревьев). Потолок реестра `PHONE_LOG_EXCEPTIONS` = 0 по образцу `WITHOUT_WITNESS_CEILING = 20` (`test_declared_invariants.py:97`) и `MANUAL_FETCH_CEILING_AT_PHASE_08 = 0` / `_ceiling_offence` (`tests/test_templates/test_htmx_inventory.py:1102-1108,1216,2012-2016`). Предикат — RESEARCH:405-415. JS-токенизатор — см. «No Analog Found». Модуль кладётся в корень `tests/` рядом с `tests/test_logging_config.py`.

---

### Записи `tests/test_planning/*` (правки, план волны 1)

- **`test_deferred_items_are_idempotent.py`** — развилка по образцу `_require_live_phases` (`:168-181`): `pytest.skip("…причина…")` при законной пустоте («живых кандидатов нет»), красное при «кандидат есть, не опознан» (`anchor_is_required` `:158-166`). Синтетика — в `tmp_path`.
- **`test_requirement_completion_follows_verification.py`** — `REQUIREMENT_ROWS_DECLARED = 44` (`:99`) → карта `{"v2.1": 44, "v2.2": 21}` по `_record_milestone(text)` (`:205`) со строкой летописи; правило `:434-446`. Пропуск «нет Complete и нет отчётов» в `:778-800` (ветвление через `pytest.skip`, не `assert … is None` — мета-гейт `test_planning_gates_are_independent_of_the_live_verdict.py`). Литералы `"FORM-01"`/`"QUAL-04"` в `:999-1046` → вывод субъектов из поданной записи (вариант (а) RESEARCH:526), как обосновано у `_flipped_flag` `:948-962`. Синтетический корень — `_fake_planning_root` `:470-530`.
- **`test_state_progress_matches_roadmap.py`** — антивакуум `:312-355` условить на `roadmap_plan_counts` (`:69`) `total > 0`; синтетические контроли по образцу `:506-545` (`test_the_prose_helper_catches_a_stale_prose_line`, `…_finds_nothing_when_no_prose_is_recognised`).
- **Сев реестра** — последней задачей: `uv run python scripts/prohibitions_census.py --seed-registry` (идемпотентен, `:39`, `seed_registry` `:755`), строка летописи «с 2026-10-08 несёт и строки v2.2» в шапку реестра (О-2). После сева состав `must_haves.prohibitions` планов не менять.

### `pyproject.toml` / `uv.lock`

`just add phonenumberslite==9.0.41` (= `uv add`), за `checkpoint:human-verify` (вердикт SUS). Ручной правки `dependencies` (`pyproject.toml:7-…`, алфавитный список) не делать.

## Shared Patterns

### Не коммитить в сценарии
**Источник:** `app/application/accounts/use_cases.py:80-81`, `group_resync.py:27-28`. **Применять:** все три писателя.

### Условная запись вместо read-check-write
**Источник:** `app/services/payment_service.py:811-839`. **Применять:** `fill_reported_phone`, `record_reported_phone`; тест гонки и отрицание.

### Константа условия в модели = строка в ревизии, сверка тестом
**Источник:** `app/models/schedule.py:40-57` ↔ `alembic/versions/0022_…:172-177` ↔ `test_0022_…:479-500`. **Применять:** модель, `0023`, `test_0023_*`.

### Явный `DATABASE_URL` в тестах ревизий
**Источник:** `test_0022_…:205-213`, `test_model_matches_head.py:257-266`. **Применять:** оба теста ревизий (без подмены ушло бы на живую базу).

### Сквозной гейт: обход с `root`, подложенный файл, антивакуум, реестр с причиной
**Источник:** `tests/test_application/test_no_metering_remains.py:83-135,245-262`; потолок — `test_declared_invariants.py:97`. **Применять:** гейт писателя и гейт приватности.

### Пропуск только с названной причиной
**Источник:** `tests/test_planning/test_deferred_items_are_idempotent.py:168-181`. **Применять:** все правки записей.

### Русские докстринги-обоснования «⚠️ … ЗАЧЕМ»
Повсюду в аналогах (`0022`, `_claim_payment`, тесты). Применять во всех новых модулях.

## No Analog Found

| Файл | Роль | Поток | Причина |
|---|---|---|---|
| JS-половина `tests/test_phone_privacy_gate.py` | test (токенизатор JS) | batch | В проекте нет разбора JS из Python; парсера нет. Использовать RESEARCH:407 (регэксп вызова, баланс скобок, `${…}` идёт в код) и синтетические контроли |
| ядро `app/services/phone.py` | utility | transform | `phonenumbers` в проекте впервые; брать RESEARCH §Нормализация / §Code Examples |

## Metadata

**Analog search scope:** `alembic/versions/`, `app/models/`, `app/services/`, `app/application/accounts/`, `tests/test_migrations/`, `tests/test_services/`, `tests/test_application/`, `tests/test_templates/`, `tests/test_planning/`, `scripts/`
**Files scanned:** ~20
**Pattern extraction date:** 2026-10-08
