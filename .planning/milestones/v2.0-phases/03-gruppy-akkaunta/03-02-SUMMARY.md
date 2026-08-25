---
phase: 03-gruppy-akkaunta
plan: 02
subsystem: database
tags: [alembic, postgres, models, application-layer, resync, tdd]

# Dependency graph
requires:
  - phase: 02-03
    provides: "Ревизия 0013 — предшественник в линии миграций"
  - phase: 02-12
    provides: "Прецедент одноразовой базы: контейнер на 127.0.0.1:55432 и guard по hostname/port/dbname"
provides:
  - "Колонки messenger_accounts.last_synced_at и messenger_accounts.last_sync_result (D-12)"
  - "Колонка groups.missing_since — пометка «не найдена при синке» (D-11)"
  - "Ревизия 0014, доказано применённая и откаченная на настоящей PostgreSQL"
  - "apply_group_resync — единственная реализация переинвентаризации для трёх мест вызова"
  - "record_sync_failure — запись неудавшегося синка той же формой, что удавшегося"
  - "parse_sync_result — чтение результата с защитой от мусора"
  - "GroupResyncResult — DTO счётчиков found/created/renamed/missing/error"
affects:
  - "03-04: три места вызова синка переходят на хелпер"
  - "03-06: экран групп читает last_synced_at и last_sync_result"

actuals:
  tokens: 62000
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Результат синка хранится Text-колонкой с JSON-строкой, а не sa.JSON: SQLite в тестах и PostgreSQL в проде ведут Text одинаково"
    - "Прохибиция выражается отсутствием имени в модуле и проверяется grep-ом: is_active в group_resync.py не встречается вовсе"
    - "Round-trip ревизии называет целевую ревизию явно, а не head: имя головы меняется с каждой новой ревизией"
    - "Тест колонки перечитывает строку новым объектом, а не refresh: присваивание немаппленного имени переживает refresh и зеленит тест без колонки в схеме"

key-files:
  created:
    - alembic/versions/0014_sync_result_and_group_missing.py
    - app/application/accounts/group_resync.py
    - tests/test_models/test_sync_result_columns.py
    - tests/test_application/test_group_resync.py
    - tests/test_migrations/test_0014_sync_result_columns.py
  modified:
    - app/models/messenger_account.py
    - app/models/group.py
    - app/application/accounts/dto.py
    - tests/test_migrations/test_0013_ad_status.py

key-decisions:
  - "last_sync_result — Text с JSON-строкой {found,new,renamed,missing,error} (разрешение дискреции D-12, допущение A1 RESEARCH)"
  - "groups.missing_since — nullable DateTime, а не булев is_missing (допущение A2): даёт бесплатную подпись «не найдена с …»"
  - "Ключ счётчика новых групп в JSON называется new, поле DTO — created: new в Python занято иным смыслом"
  - "Время ПЕРВОЙ пропажи не перетирается повторным синком: подпись обязана говорить, когда группа исчезла"
  - "Одноразовая база — отдельный контейнер broadcaster-disposable-0014, контейнер плана 02-12 не тронут: он содержит реальные объявления владельца"
  - "Проверка ветвления ревизий утверждает «голова одна», а не «голова называется 0013»"

requirements-completed: [GRP-07]

# Metrics
duration: 42min
completed: 2026-08-12
status: complete
---

# Phase 03 Plan 02: Схема и логика результата синхронизации — Summary

**Аккаунт получил время и результат последнего синка, группа — пометку «не найдена при синке», а трижды скопированный блок only-add заменён одним хелпером полной переинвентаризации; ревизия `0014` доказано применена и откачена на настоящей PostgreSQL, целевая база осталась на `0012`.**

---

## Что построено

| Артефакт | Содержание |
|---|---|
| `messenger_accounts.last_synced_at` | tz-aware DateTime, nullable — время последнего синка (D-12) |
| `messenger_accounts.last_sync_result` | Text, nullable — JSON-строка `{found, new, renamed, missing, error}` |
| `groups.missing_since` | tz-aware DateTime, nullable — «не найдена при последней синхронизации» (D-11) |
| `alembic/versions/0014_sync_result_and_group_missing.py` | Ревизия `0014`, `down_revision = "0013"`, три `add_column` / три `drop_column` |
| `app/application/accounts/group_resync.py` | `apply_group_resync`, `record_sync_failure`, `parse_sync_result` |
| `GroupResyncResult` в `dto.py` | Счётчики `found`/`created`/`renamed`/`missing`/`error` |

---

## Task 1 — колонки результата синка и ревизия 0014 (TDD)

**RED** (`160086d`): шесть тестов в `tests/test_models/test_sync_result_columns.py`, все падали.

Три из шести на первом прогоне **прошли ошибочно** и были переписаны до реализации — правило fail-fast сработало. Причина: объект SQLAlchemy остаётся обычным объектом Python, присваивание немаппленного имени проходит молча и переживает `refresh`, потому что тот обновляет только маппленные колонки. Тест зеленел бы и БЕЗ колонки в схеме, то есть не проверял бы ровно то, ради чего написан. Заменено на `expunge_all` + повторную выборку новым объектом. После правки — 6 падений из 6.

Отдельно добавлено утверждение о типах, снятое с `__table__`: суита идёт на SQLite, где `String(20)` и `Text` неотличимы по поведению и длина не проверяется вовсе. Без этой проверки `last_sync_result` мог бы уехать в `String(255)` и обрезать текст ошибки только в проде.

**GREEN** (`d48d79f`): колонки объявлены в моделях формой из `app/models/group.py`, создана ревизия `0014`.

| Критерий | Результат |
|---|---|
| `grep 'last_synced_at' app/models/messenger_account.py` | ✅ |
| `grep 'last_sync_result' app/models/messenger_account.py` | ✅ |
| `grep 'missing_since' app/models/group.py` | ✅ |
| `revision = "0014"` / `down_revision = "0013"` | ✅ по одному вхождению |
| `grep -c 'op.add_column'` | **3** |
| `grep -c 'op.drop_column'` | **3** |
| `grep -v '^#' … \| grep -c 'server_default'` | **0** |
| `uv run alembic heads` | `0014 (head)` |
| `uv run pytest tests/test_models/test_sync_result_columns.py -q` | 6 passed |

---

## Task 2 — применение ревизии на одноразовой базе

**Precondition проверена до любых действий:** `docker version` → код 0; порт `127.0.0.1:55432` свободен (контейнер плана 02-12 `broadcaster-disposable-0013` существует, но остановлен 25 часов назад).

**Контейнер плана 02-12 НЕ переиспользован и не запускался:** по его собственному SUMMARY он содержит реальное содержимое объявлений владельца. Поднят отдельный:

```
docker run -d --name broadcaster-disposable-0014 \
  -e POSTGRES_USER=disposable -e POSTGRES_PASSWORD=disposable \
  -e POSTGRES_DB=broadcaster_disposable_0014 \
  -p 127.0.0.1:55432:5432 postgres:18-alpine
```

### Guard по адресу

Перед каждой командой миграции сравнивались ровно три поля эффективного `DATABASE_URL` — hostname, port, dbname. Guard не принят на веру, а **проверен на отказ**:

```
$ DATABASE_URL=<адрес целевой базы> … guard.py
  hostname=192.168.0.9 port=5432 dbname=broadcaster
GUARD REFUSED: адрес не одноразовый — ожидалось 127.0.0.1:55432/broadcaster_disposable_0014
exit=1

$ DATABASE_URL=<одноразовый> … guard.py
  hostname=127.0.0.1 port=55432 dbname=broadcaster_disposable_0014
GUARD OK — адрес одноразовый, целевая база этой командой не адресуется
```

### Шаг 1 — прогон всей цепочки

```
$ DATABASE_URL=<одноразовый> uv run alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
…
INFO  [alembic.runtime.migration] Running upgrade 0012 -> 0013, ads.status вместо ads.is_active
INFO  [alembic.runtime.migration] Running upgrade 0013 -> 0014, Результат синхронизации на аккаунте и пометка пропавшей группы
```

### Шаг 2 — `alembic current`, критерий приёмки

```
$ DATABASE_URL=<одноразовый> uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0014 (head)
```

### Шаг 3 — сравнение колонок в `information_schema.columns`

```
table.column                             data_type                    is_nullable
messenger_accounts.last_synced_at        timestamp with time zone     YES
messenger_accounts.last_sync_result      text                         YES
groups.missing_since                     timestamp with time zone     YES
columns_found=3 of 3
all_nullable=True
```

### Шаг 4 — откат: симметрия доказана, а не заявлена

```
$ DATABASE_URL=<одноразовый> uv run alembic downgrade 0013
INFO  Running downgrade 0014 -> 0013, Результат синхронизации на аккаунте и пометка пропавшей группы

$ … columns.py
messenger_accounts.last_synced_at        ОТСУТСТВУЕТ
messenger_accounts.last_sync_result      ОТСУТСТВУЕТ
groups.missing_since                     ОТСУТСТВУЕТ
columns_found=0 of 3

$ … uv run alembic current
0013
```

### Шаг 5 — возврат на 0014

```
$ DATABASE_URL=<одноразовый> uv run alembic upgrade head
INFO  Running upgrade 0013 -> 0014, …
```

### Оффлайн-генерация SQL — доказательство «строго additive nullable»

```
$ uv run alembic upgrade 0013:0014 --sql
ALTER TABLE messenger_accounts ADD COLUMN last_synced_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE messenger_accounts ADD COLUMN last_sync_result TEXT;
ALTER TABLE groups ADD COLUMN missing_since TIMESTAMP WITH TIME ZONE;

$ uv run alembic downgrade 0014:0013 --sql
ALTER TABLE groups DROP COLUMN missing_since;
```

Ни `DEFAULT`, ни `NOT NULL` ни в одной из трёх инструкций — прыжок `0012 → 0014` не переписывает существующие строки.

### Целевая база

**Не адресована ни одной командой.** Её адрес встречается в журнале выполнения ровно один раз — в проверке того, что guard на нём ОТКАЗЫВАЕТ; соединения по этому адресу не открывалось. Целевая база остаётся на ревизии `0012`; выкат `0013` и `0014` — решение владельца, зафиксированное блокером STATE.md.

### Работающий стек

Ни один контейнер стека не останавливался, не перезапускался и не перенастраивался. `web-broadcaster`, `nginx-broadcaster`, `celery-*`, `flower-broadcaster`, `certbot-broadcaster` — те же аптаймы (19 часов) до и после. Наблюдавшийся churn `wa-worker-*` / `max-worker-*` — собственное поведение стека (`wa_container_manager` из задач Celery), команд в их адрес не подавалось. Единственные команды `docker` касались `broadcaster-disposable-0014`.

**Одноразовый контейнер остановлен, но не удалён** (стоит на `0014`). Снести: `docker rm -f broadcaster-disposable-0014`.

---

## Task 3 — хелпер полной переинвентаризации (TDD)

**RED** (`2b22643`): 20 тестов, падение на импорте — ни модуля, ни DTO не существовало.

**GREEN** (`c092459`): `app/application/accounts/group_resync.py` + `GroupResyncResult`.

Все пять веток переинвентаризации закреплены тестами:

| Ветка | Тест | Результат |
|---|---|---|
| Новая | `test_new_groups_are_created_enabled` | created=3, found=3, все включены |
| Переименованная | `test_renamed_group_updates_name` | renamed=1, имя обновлено |
| Неизменившаяся | `test_unchanged_group_is_not_counted_as_renamed` | created=0, renamed=0 |
| Пропавшая | `test_missing_group_is_marked_not_deleted` | missing=1, строка на месте, `missing_since` заполнено |
| Вернувшаяся | `test_returned_group_loses_missing_mark` | `missing_since` → None |

Плюс: идемпотентность повторного вызова (created=0, renamed=0, missing=0), пустой ответ (missing=3, ни одна строка не удалена), дубли `id` в ответе (одна строка), возврат удалённой пользователем группы (D-10), T-03-06 (чужая группа с тем же `external_id` не тронута), отсутствие commit внутри хелпера, запись результата на аккаунт, `record_sync_failure`, деградация `parse_sync_result` на пяти видах мусора.

| Критерий | Результат |
|---|---|
| `async def apply_group_resync(` / `async def record_sync_failure(` / `def parse_sync_result(` | ✅ по одному |
| `class GroupResyncResult` в `dto.py` | ✅ |
| `grep -v '^#' … \| grep -c 'session.delete'` | **0** — хелпер не удаляет строк |
| `grep -v '^#' … \| grep -c 'is_active'` | **0** — имени нет в модуле вовсе |
| `uv run pytest tests/test_models/ tests/test_application/test_group_resync.py -q` | 51 passed |

Прохибиция D-11 выражена **отсутствием имени `is_active` во всём модуле** — форма, которую можно проверить grep-ом, а не только прочитать.

---

## Отклонения от плана

### 1. [Rule 1 — Bug] Ревизия 0014 уронила все шесть тестов `test_0013_ad_status.py`

- **Найдено:** на полном прогоне суиты после Task 3
- **Проблема:** файл гнал `command.upgrade(config, "head")`, а его фикстура строит ТОЛЬКО таблицу объявлений. Пока `0013` была головой, это работало; с появлением `0014` прогон дошёл до неё и упёрся в отсутствующие `messenger_accounts` и `groups`. Шестой тест падал отдельно: `assert list(heads) == ["0013"]`.
- **Исправление:** целевая ревизия названа явно (`"0013"`) — файл проверяет ОДНУ ревизию и не обязан тащить в фикстуру продолжение истории. Проверка ветвления переписана на утверждение «голова одна»: имя головы меняется с каждой новой ревизией и свойством истории миграций не является, а ловить нужно именно ветвление.
- **Компенсация утраченной привязки:** сама по себе замена ослабила покрытие — исчезло единственное автоматическое утверждение о положении новой ревизии в цепочке. Добавлен `tests/test_migrations/test_0014_sync_result_columns.py` (4 теста): три колонки появляются nullable и **без значения по умолчанию**, существующие строки переживают миграцию с NULL, откат снимает ровно их и не трогает соседние `last_error`/`error_at`, `0014` продолжает `0013`.
- **Файлы:** `tests/test_migrations/test_0013_ad_status.py`, `tests/test_migrations/test_0014_sync_result_columns.py`
- **Commit:** `e4c9399`

### 2. [Rule 1 — Bug] Три собственных теста Task 1 прошли ошибочно в фазе RED

- **Найдено:** на первом прогоне RED (до реализации)
- **Проблема:** тесты писались через `refresh`, а присваивание немаппленного имени объекту SQLAlchemy проходит молча и `refresh` его не стирает. Тесты зеленели бы без колонок в схеме.
- **Исправление:** `expunge_all` + повторная выборка новым объектом; добавлено утверждение о типах с `__table__`. После правки — 6 падений из 6, то есть настоящий RED.
- **Файл:** `tests/test_models/test_sync_result_columns.py` (правка внутри того же RED-коммита `160086d`)

### 3. [Rule 1 — Bug] Два собственных теста Task 3 падали по дефектам теста, не реализации

- **Найдено:** на первом прогоне GREEN (18 из 20 прошли)
- **Проблема 1:** `test_manually_deleted_group_returns_as_new` сравнивал id новой строки с id удалённой — SQLite переиспользует rowid, и утверждение говорило о движке, а не о нашей логике. **Исправление:** уликой сделано состояние — удаляемая группа несёт `is_active=False` и заполненный `missing_since`, новая обязана прийти включённой и без пометки.
- **Проблема 2:** `test_helper_does_not_commit` обращался к `account.id` ПОСЛЕ отката; откат обесценивает атрибуты, и обращение полезло в базу за перезагрузкой в синхронном контексте (`MissingGreenlet`). **Исправление:** id снимается до отката.
- **Файл:** `tests/test_application/test_group_resync.py` (правки вошли в GREEN-коммит `c092459`)

**Итого отклонений:** 3, все Rule 1. Ни одно не расширяет объём плана и ни одно не меняет решений D-10/D-11/D-12.

---

## Verification

| Проверка | Результат |
|---|---|
| `uv run alembic heads` — единственная голова `0014` | ✅ `0014 (head)` |
| Применение `0014` на настоящей PostgreSQL | ✅ `0013 -> 0014`, `alembic current` = `0014 (head)` |
| Три колонки в `information_schema.columns`, все nullable | ✅ 3 из 3, `all_nullable=True` |
| Откат `0014 → 0013` и исчезновение колонок | ✅ `columns_found=0 of 3` |
| Оффлайн-SQL: три ADD COLUMN без DEFAULT и NOT NULL | ✅ |
| Целевая база не тронута | ✅ ни одного соединения по её адресу |
| Работающий стек не потревожен | ✅ те же аптаймы |
| `uv run pytest tests/test_application/test_group_resync.py tests/test_models/test_sync_result_columns.py -q` | ✅ 26 passed |
| `uv run pytest tests/ -q` — суита не деградировала | ✅ **925 passed, 0 failed** (было 895; +30 новых) |

---

## Success criteria

| Критерий | Результат |
|---|---|
| GRP-07 (частично): результат синка имеет место хранения, переживающее перезаход, и вычисляется одной функцией | ✅ колонки + `apply_group_resync` |
| D-10, D-11, D-12 реализованы и закреплены тестами на всех пяти ветках | ✅ пять веток + идемпотентность + пустой ответ |
| Ревизия `0014` безопасна для прыжка `0012 → 0014` | ✅ доказано оффлайн-SQL и прогоном на PostgreSQL |

---

## Known Stubs

Отсутствуют. Все три публичные функции модуля реализованы полностью и покрыты тестами; заглушек, TODO и пустых веток план не оставил.

Не является заглушкой, но подлежит учёту: **хелпер пока никем не вызывается.** Три места вызова (страничный TG-обработчик и две Celery-таски) переходят на него планом 03-04 — так и задумано плановой последовательностью: точка истины создаётся ДО того, как её начнут вызывать.

---

## Threat Flags

Новых поверхностей вне `<threat_model>` плана не появилось. Диспозиции `mitigate`:

| Угроза | Реализация |
|---|---|
| T-03-06 (выборка существующих групп) | Двойной WHERE `Group.account_id == account.id AND Group.user_id == account.user_id`; закреплено `test_foreign_group_with_same_external_id_untouched` — чужая группа с тем же `external_id` не обновляется и в счётчики не попадает |
| T-03-08 (`last_sync_result` как JSON-строка) | `parse_sync_result` возвращает `None` на пустом значении, битом JSON и несловарном верхнем уровне; пять видов мусора в параметризованном тесте |
| T-03-09 (ревизия `0014`) | Только additive nullable, без значений по умолчанию и без data-migration; применение доказано на одноразовой базе с guard-ом, проверенным на отказ; целевая база не адресована |

---

## Открытые допущения (переданы дальше, не разрешены)

- Зондирование границ по GRP-07 вернуло `unclassified`. Категория границ требования остаётся открытым предположением планировщика и подлежит человеческому просмотру при верификации фазы — исполнитель её не разрешал.
- Формы A1 (`Text` с JSON-строкой) и A2 (`missing_since` как nullable DateTime) реализованы как разрешённые планом дискреции D-12. Цена смены после выката — одна дополнительная ревизия.

---

## Next Phase Readiness

- План 03-04 получает готовую точку вызова: `apply_group_resync(session, account, fetched, messenger_type=...)` принимает ровно тот формат, что уже отдают `messenger.get_groups()` и поле `groups` ответа `get_sync_status()`; commit остаётся за вызывающим.
- План 03-06 получает `parse_sync_result` и обе колонки аккаунта: `last_synced_at IS NULL` отличимо от нулевых счётчиков, битое значение даёт `None`, а не исключение.
- Блокер выката остаётся: целевая база на `0012`, очередь `0013` + `0014`. Оба шага доказано применяются подряд одним прогоном.

---

## Self-Check: PASSED

Проверено на диске и в git, а не по памяти:

**Файлы созданы** — все пять: `alembic/versions/0014_sync_result_and_group_missing.py`, `app/application/accounts/group_resync.py`, `tests/test_models/test_sync_result_columns.py`, `tests/test_application/test_group_resync.py`, `tests/test_migrations/test_0014_sync_result_columns.py`.

**Коммиты существуют** — `160086d`, `d48d79f`, `2b22643`, `c092459`, `e4c9399` присутствуют в `git log`.

**Удалений файлов нет** — ни один коммит плана не содержит удалённых файлов.

**Общие артефакты не тронуты** — `STATE.md` и `ROADMAP.md` этим планом не изменялись (worktree-режим, запись за оркестратором).

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-12*
