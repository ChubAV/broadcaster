---
phase: 04-dashbord-i-istoriya
plan: 02
subsystem: database
tags: [alembic, postgresql, sqlite, migrations, index, send_logs, tdd]

# Dependency graph
requires:
  - phase: 03-gruppy-akkaunta
    provides: "Ревизия 0015 — текущий head очереди невыкаченных ревизий, к которому цепляется 0016"
  - phase: 02-obyavleniya-i-raspisaniya
    provides: "Образец миграционного теста (test_0013_ad_status.py): файловая SQLite, синхронный тест, штамп стартовой ревизии"
provides:
  - "Ревизия Alembic 0016 — составной индекс ix_send_logs_user_id_sent_at на send_logs (user_id, sent_at)"
  - "Миграционный тест ревизии 0016 с фикстурой db_at_0015"
  - "Устойчивая формулировка проверки головы ревизий: количество голов, а не имя"
affects: [dashboard, history, send_analytics, будущие ревизии Alembic]

actuals:
  tokens: 7150
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Индексная ревизия отдельным шагом: докстринг обязан назвать размен по блокировкам и статус «оптимизация, а не предусловие»"
    - "Проверка головы ревизий утверждает КОЛИЧЕСТВО голов, а не имя — имя меняется с каждой новой ревизией"

key-files:
  created:
    - alembic/versions/0016_send_logs_user_sent_at.py
    - tests/test_migrations/test_0016_send_logs_user_sent_at.py
  modified:
    - tests/test_migrations/test_0015_groups_unique_account_external.py

key-decisions:
  - "Одиночные индексы ix_send_logs_user_id, ix_send_logs_task_id и ix_send_logs_sent_at ревизия НЕ снимает — составной их не покрывает, снятие было бы отдельным решением"
  - "Порядок колонок индекса задан формой запроса: равенство (user_id) первым, диапазон (sent_at) вторым"
  - "CREATE INDEX берётся обычный, а не CONCURRENTLY: размен принят по сегодняшним объёмам, неблокирующее построение выписано готовым следующим шагом"
  - "Накат ревизии на целевую базу планом НЕ выполняется — это решение владельца"

patterns-established:
  - "Проверка головы ревизий по количеству, а не по имени: test_0013 и test_0014 уже писались так, test_0015 отступил и потому сломался при пополнении истории"

requirements-completed: [DASH-01, DASH-04, HIST-01, HIST-03]

coverage:
  - id: D1
    description: "Ревизия 0016 создаёт составной индекс ix_send_logs_user_id_sent_at на send_logs (user_id, sent_at)"
    requirement: "DASH-01"
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_upgrade_creates_composite_index"
        status: pass
    human_judgment: false
  - id: D2
    description: "downgrade снимает составной индекс и не трогает строки журнала отправок"
    requirement: "HIST-01"
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_downgrade_removes_composite_index"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_rows_survive_upgrade_and_downgrade"
        status: pass
    human_judgment: false
  - id: D3
    description: "Одиночные индексы user_id, task_id и sent_at переживают ревизию — она добавляет, а не заменяет"
    requirement: "HIST-03"
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_upgrade_keeps_the_single_column_indexes"
        status: pass
    human_judgment: false
  - id: D4
    description: "История ревизий остаётся одной линией: 0016 продолжает 0015, голова одна"
    requirement: "DASH-04"
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_0016_send_logs_user_sent_at.py#test_revision_0016_continues_0015"
        status: pass
      - kind: other
        ref: "uv run alembic heads → '0016 (head)'"
        status: pass
    human_judgment: false
  - id: D5
    description: "Применение ревизии на целевую PostgreSQL не создаёт заметного окна недоступности записи в send_logs"
    verification: []
    human_judgment: true
    rationale: "Боевой PostgreSQL в этом окружении отсутствует, размер send_logs здесь неизмерим; суита идёт по SQLite, где блокировок PostgreSQL не существует. Размер окна — наблюдение владельца в момент наката, который планом не выполняется."

duration: 10min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 02: Составной индекс (user_id, sent_at) на send_logs — Summary

**Ревизия Alembic 0016 создаёт составной индекс `ix_send_logs_user_id_sent_at`, закрывающий форму запроса «мои записи в окне времени» одним проходом вместо выбора планировщиком одного из двух одиночных индексов; накат на целевую базу оставлен решением владельца.**

## Performance

- **Duration:** ~10 мин
- **Started:** 2026-08-14T05:12Z (приблизительно)
- **Completed:** 2026-08-14T05:22Z
- **Tasks:** 2 из 2
- **Files modified:** 3 (2 создано, 1 изменён)

## Accomplishments

- Ревизия `0016` с `down_revision = "0015"`: `upgrade` создаёт составной индекс, `downgrade` его снимает, ни одна строка не переписывается. Очередь невыкаченных ревизий 0013-0015 не переставлена и не схлопнута.
- Докстринг ревизии называет все три обязательные вещи: зачем составной индекс (форма запроса и потеря половины селективности на одиночных), размен по блокировкам (`SHARE` на самой растущей таблице системы, `CONCURRENTLY` в ревизии без транзакции — готовый следующий шаг) и статус «оптимизация, а не предусловие».
- Миграционный тест из пяти проверок, исполняющий текст ревизии по-настоящему на файловой SQLite: индекс появляется, исчезает на откате, одиночные индексы выживают, строка переживает round-trip, линия ревизий не разветвилась.
- Побочно устранена мина замедленного действия в тесте ревизии 0015 — он утверждал ИМЯ головы и обязан был сломаться при любом пополнении истории миграций.

## Task Commits

1. **Task 1: Миграционный тест ревизии 0016 (RED)** — `ebf1dba` (test)
2. **Task 2: Ревизия 0016 — составной индекс (GREEN)** — `66c8f5e` (feat)

RED зафиксирован до перехода к задаче 2: все пять тестов падали с `alembic.util.exc.CommandError: Can't locate revision identified by '0016'` — то есть по отсутствию самой цели, а не по ошибке в тесте.

## Files Created/Modified

- `alembic/versions/0016_send_logs_user_sent_at.py` — ревизия 0016: `INDEX_NAME = "ix_send_logs_user_id_sent_at"`, `op.create_index(INDEX_NAME, "send_logs", ["user_id", "sent_at"])` в `upgrade`, `op.drop_index(..., table_name="send_logs")` в `downgrade`
- `tests/test_migrations/test_0016_send_logs_user_sent_at.py` — фикстура `db_at_0015` (файловая SQLite, DDL `send_logs` на состояние 0015 с тремя одиночными индексами, одна строка, `command.stamp(config, "0015")`) и пять тестов round-trip
- `tests/test_migrations/test_0015_groups_unique_account_external.py` — проверка головы переведена с имени на количество (см. Deviations)

## Decisions Made

- **Одиночные индексы не снимаются.** Составной индекс не покрывает доступ по одному только `sent_at` (сводки по всем пользователям) и по `task_id` (поиск записи по идентификатору задачи). Ревизия добавляет, а не заменяет; снятие было бы отдельным решением с собственным обоснованием. Закреплено тестом `test_upgrade_keeps_the_single_column_indexes`.
- **Порядок колонок — `(user_id, sent_at)`, а не наоборот.** Равенство идёт первым, диапазон вторым: при обратном порядке вторая колонка индекса перестаёт сужать поиск.
- **`CREATE INDEX` обычный, а не `CONCURRENTLY`.** Неблокирующее построение требует ревизии без транзакции и умеет оставлять индекс в состоянии `INVALID` при обрыве, что чинится вручную. Размен принят по сегодняшним объёмам и выписан в докстринге вместе с готовым следующим шагом.
- **Тест утверждает количество голов, а не имя головы.** Имя головы меняется с каждой новой ревизией и свойством истории не является; ловить нужно ветвление.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Тест ревизии 0015 утверждал ИМЯ головы и сломался от появления 0016**

- **Found during:** Task 2 (первый зелёный прогон `uv run pytest tests/test_migrations/ -q`)
- **Issue:** `test_revision_0015_continues_0014` содержал `assert "0015" in script.get_heads()`. Это утверждение верно ровно до следующей ревизии: как только появилась 0016, голова стала `['0016']` и тест упал — при том, что проверяемое им свойство (0015 продолжает 0014, линия не разветвилась) не нарушено ничем. Дефект в самой формулировке проверки, а не в новой ревизии: соседние `test_0013_ad_status.py:190` и `test_0014_sync_result_columns.py:179` писались правильно — через `len(heads) == 1` — и докстринг `test_0013` эту оговорку проговаривает прямым текстом («имя головы меняется с каждой новой ревизией и потому свойством истории не является»). `test_0015` от установленного образца отступил.
- **Fix:** `assert "0015" in script.get_heads()` заменён на `assert len(script.get_heads()) == 1`, докстринг теста объясняет, почему имя не проверяется. Продолжение линии по-прежнему проверяется собственной сцепкой ревизии (`down_revision == "0014"`), которая от пополнения истории не зависит. Та же мина убрана из НОВОГО теста 0016 до её первого срабатывания: `assert heads == ["0016"]` снят, оставлены `len(heads) == 1` и `down_revision == "0015"`.
- **Files modified:** `tests/test_migrations/test_0015_groups_unique_account_external.py`, `tests/test_migrations/test_0016_send_logs_user_sent_at.py`
- **Verification:** `uv run pytest tests/test_migrations/ -q` → 23 passed
- **Committed in:** `66c8f5e` (в составе коммита задачи 2)

Оба файла лежат внутри `tests/test_migrations/`, то есть внутри границы, заданной критерием приёмки «ни один файл вне `alembic/versions/` и `tests/test_migrations/` этим планом не изменён».

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Починка обязательна — без неё suite остаётся красной, а причина красноты не в новой ревизии. Расширения области нет: правка держит ровно то же утверждение в формулировке, не зависящей от продолжения истории миграций.

## Issues Encountered

None — задачи прошли по плану.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_migrations/ -q` | 23 passed |
| `uv run alembic heads` | `0016 (head)` — ровно одна голова |
| `uv run pytest tests/ -q --collect-only` | 1099 tests collected, ошибок импорта нет |
| RED зафиксирован до GREEN | exit 1, `Can't locate revision identified by '0016'` |

## User Setup Required

None — внешних сервисов ревизия не касается.

⚠️ **Накат на целевую базу — решение владельца, планом НЕ выполнено.** Состояние на момент завершения плана:

- Целевая база остаётся на ревизии `0012` (блокер из STATE.md, тянется с Фазы 2).
- `alembic upgrade head` прогонит на ней ЧЕТЫРЕ ревизии: `0013` (снимает колонку `ads.is_active` с боевыми данными, downgrade необратим по данным), `0014`, `0015` (единственная ревизия проекта, удаляющая строки `groups`, и берущая `ACCESS EXCLUSIVE` на этой таблице) и `0016` (берёт `SHARE` на `send_logs`, блокируя запись на время построения индекса).
- Ревизия `0016` — оптимизация, а не предусловие: дашборд и история обязаны работать и до её наката, на существующих одиночных индексах. Откладывание наката не ломает ни одного сценария фазы.
- Утверждение «применение ревизии не создаёт заметного окна недоступности записи» проверке в этом окружении не поддаётся (боевого PostgreSQL нет, размер `send_logs` неизмерим) и вынесено в coverage `D5` как требующее наблюдения владельца.

## Next Phase Readiness

- Индекс доступен планам фазы, работающим с выборками `send_logs` по пользователю и окну времени; корректность их запросов от наката ревизии не зависит.
- Блокеров для последующих волн фазы 04 план не создаёт.
- Единственный незакрытый вопрос — момент наката ревизий `0013`-`0016` на целевую базу.

## Self-Check: PASSED

Файлы на месте: `alembic/versions/0016_send_logs_user_sent_at.py`,
`tests/test_migrations/test_0016_send_logs_user_sent_at.py`,
`.planning/phases/04-dashbord-i-istoriya/04-02-SUMMARY.md`.
Коммиты в истории: `ebf1dba`, `66c8f5e`. Дерево чистое, удалённых файлов ни в одном коммите нет.

---
*Phase: 04-dashbord-i-istoriya*
*Plan: 02*
*Completed: 2026-08-14*
