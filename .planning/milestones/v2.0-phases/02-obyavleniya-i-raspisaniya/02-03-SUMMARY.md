---
phase: 02-obyavleniya-i-raspisaniya
plan: 03
subsystem: database
tags: [alembic, sqlalchemy, pydantic, jinja2, celery, sqlite, postgres]

# Dependency graph
requires:
  - phase: 02-01
    provides: "Зелёная базовая линия суиты, `_env_file=None` в тестовых Settings, синглтон Jinja `templates` в app/pages/common.py"
  - phase: 02-02
    provides: "own_image_keys на всех четырёх путях записи вложений, _owns_ad_and_account на создании/правке расписаний — инварианты, которые этот план не трогал"
provides:
  - "Состояние объявления `Ad.status` (черновик / опубликовано) во всех шести слоях: схема, модель, доменный подбор расписаний, страничный слой, JSON-API, шаблон списка"
  - "app/constants.py как единственный источник значений состояния (AD_STATUS_DRAFT, AD_STATUS_PUBLISHED, AD_STATUSES)"
  - "Ревизия Alembic 0013 (АВТОРСКАЯ, НЕ ПРИМЕНЁННАЯ — см. раздел «Отложенный выкат»)"
  - "Пропуск черновиков планировщиком со сдвигом next_run_at (D-01, T-02-12)"
  - "effective_ad_status — безопасный дефолт «всё, кроме опубликованного, считается черновиком»"
  - "Первый в проекте тест, реально исполняющий ревизию Alembic (tests/test_migrations/)"
  - "Jinja-глобалы AD_STATUS_DRAFT / AD_STATUS_PUBLISHED для макросов"
affects: [02-04, 02-05, 02-06, 02-07]

actuals:
  tokens: 34600
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Состояние домена — строковая константа из app/constants.py, а не sa.Enum"
    - "Безопасный дефолт состояния: неизвестное значение трактуется как черновик и на отправке, и в рендере"
    - "Пропуск в доменном цикле веткой со сдвигом next_run_at, а не условием в WHERE"
    - "Round-trip тест ревизии Alembic на временной файловой SQLite со штампом стартовой ревизии"

key-files:
  created:
    - alembic/versions/0013_ad_status.py
    - tests/test_application/test_collect_due_draft.py
    - tests/test_pages/test_ads_status.py
    - tests/test_migrations/__init__.py
    - tests/test_migrations/test_0013_ad_status.py
  modified:
    - app/constants.py
    - app/models/ad.py
    - app/application/scheduling/use_cases.py
    - app/routes/ads.py
    - app/pages/ads.py
    - app/pages/common.py
    - app/pages/dashboard.py
    - app/pages/schedules.py
    - app/templates/ads/includes/ad_card.html
    - app/templates/ads/form.html

key-decisions:
  - "Ревизия 0013 НЕ применена ни к какой живой базе — решение пользователя `defer` на блокирующем чекпойнте Задачи 1"
  - "Пропуск черновика реализован веткой со сдвигом next_run_at, а не условием в WHERE: фильтр в WHERE оставил бы next_run_at в прошлом и при публикации вызвал бы залп пропущенных отправок"
  - "Безопасный дефолт односторонний: нераспознанное состояние трактуется как черновик и планировщиком, и шаблоном"
  - "Значения состояния — строки, а не sa.Enum: sa.Enum на PostgreSQL завёл бы именованный тип БД, который downgrade обязан удалять отдельным шагом (прецедента в проекте нет)"
  - "Ревизия 0013 выписывает литерал 'published' сама, а не импортирует его из app.constants: миграция описывает схему на свой момент времени"
  - "Дублирующая проверка в send_message_once пишет SendLog со статусом 'fail', а не новым словом: журнал читают четыре шаблона, и незнакомое значение отрисовалось бы сырой латиницей"
  - "app/pages/ads.py принимает status необязательным полем формы и при его отсутствии состояние не трогает: сохранение текста не должно молча публиковать черновик"
  - "Round-trip тест стартует со штампа 0012, а не с base: ревизия 0005 (чужая) на SQLite падает NotImplementedError на op.drop_constraint"

patterns-established:
  - "Единственный источник значений состояния: app/constants.py читают модель, домен, схемы API и шаблон через Jinja-глобал"
  - "Ревизия Alembic покрывается round-trip тестом на временной файловой SQLite; тест синхронный, потому что alembic/env.py вызывает asyncio.run"
  - "Проверка состояния в доменном цикле выражена через effective_ad_status, а не сравнением с литералом на месте"

requirements-completed: [ADS-04]

coverage:
  - id: D1
    description: "Объявление имеет состояние «черновик» / «опубликовано»; умолчание — опубликовано"
    requirement: ADS-04
    verification:
      - kind: unit
        ref: "tests/test_models/test_ad.py#test_ad_default_values"
        status: pass
      - kind: unit
        ref: "tests/test_models/test_ad.py#test_ad_can_be_draft"
        status: pass
      - kind: unit
        ref: "tests/test_constants.py#test_ad_status_literals"
        status: pass
    human_judgment: false
  - id: D2
    description: "Черновик визуально отличим в списке /ads: бейдж «Черновик» (warning) против «Опубликовано» (success)"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_ads_list_shows_draft_badge"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_ads_list_shows_published_badge"
        status: pass
    human_judgment: true
    rationale: "Тест утверждает наличие строки в HTML, но не то, что бейдж читается как предупреждение и виден в реальной раскладке колонки. Цвет, контраст и положение ячейки — предмет визуальной проверки."
  - id: D3
    description: "Нераспознанное значение состояния отображается как «Черновик», а не сырой строкой (UI-SPEC E15 error)"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_ads_list_unrecognised_status_falls_back_to_draft"
        status: pass
    human_judgment: false
  - id: D4
    description: "Планировщик не выбирает к отправке расписания объявлений-черновиков (D-01)"
    requirement: ADS-04
    verification:
      - kind: unit
        ref: "tests/test_application/test_collect_due_draft.py#test_draft_schedule_produces_no_dispatch_task"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_collect_due_draft.py#test_published_schedule_still_dispatches"
        status: pass
    human_judgment: false
  - id: D5
    description: "Пропуск черновика сдвигает next_run_at вперёд — публикация не вызывает залпа пропущенных отправок"
    requirement: ADS-04
    verification:
      - kind: unit
        ref: "tests/test_application/test_collect_due_draft.py#test_draft_schedule_next_run_at_moves_forward"
        status: pass
    human_judgment: false
  - id: D6
    description: "/dashboard, /api/ads, /schedules/new и /schedules/{id}/edit отвечают 200 после снятия старого флага — ни один из восьми читателей не забыт"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_dashboard_counts_ads"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_api_ads_exposes_status"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_schedules_new_page_alive"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_schedules_edit_page_alive"
        status: pass
    human_judgment: false
  - id: D7
    description: "Произвольная строка в состояние через JSON-API отклоняется валидацией (T-02-11)"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_status.py#test_api_ads_update_rejects_unknown_status"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_ads_status.py#test_api_literal_matches_constants"
        status: pass
    human_judgment: false
  - id: D8
    description: "Ревизия 0013 применяется и откатывается: upgrade и downgrade проверены автоматическим тестом"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0013_ad_status.py#test_upgrade_publishes_rows_that_existed_before"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0013_ad_status.py#test_downgrade_restores_legacy_column_and_removes_status"
        status: pass
    human_judgment: false
  - id: D9
    description: "Ревизия 0013 ПРИМЕНЕНА к рабочей базе разработки (`just upgrade`), приложение видит колонку ads.status"
    requirement: ADS-04
    verification: []
    human_judgment: true
    rationale: "ОТЛОЖЕНО решением пользователя (`defer`) на блокирующем чекпойнте Задачи 1. Ни одна миграция не применялась ни к какой живой базе. Критерий НЕ выполнен и не должен считаться выполненным — см. раздел «Отложенный выкат ревизии 0013»."

# Metrics
duration: 32min
completed: 2026-08-10
status: complete
---

# Phase 02 Plan 03: Состояние объявления сквозным срезом — Summary

**Состояние объявления (`draft` / `published`) проведено через все шесть слоёв одним коммитом: ревизия Alembic 0013, `Ad.status` вместо `Ad.is_active`, восемь читателей снятого флага, пропуск черновиков планировщиком со сдвигом `next_run_at` и бейдж в списке — при этом ревизия НЕ применена ни к одной живой базе по решению пользователя.**

---

## ⚠️ ОТЛОЖЕННЫЙ ВЫКАТ РЕВИЗИИ 0013 — ЧИТАТЬ ПЕРЕД ПЛАНАМИ 02-04…02-07

**Ревизия `alembic/versions/0013_ad_status.py` написана, закоммичена и покрыта автоматическим round-trip тестом, но НЕ ПРИМЕНЕНА НИ К КАКОЙ ЖИВОЙ БАЗЕ ДАННЫХ.**

**Это решение человека, а не пропуск исполнителя.** На блокирующем чекпойнте Задачи 1 (`checkpoint:decision`, вариант `defer`) пользователь выбрал отложить выкат. Причина: на хосте работает полный продоподобный стек (`web-broadcaster`, celery-воркеры, `nginx-broadcaster` на портах 80/443, `certbot`), и не удалось подтвердить, что `DATABASE_URL` указывает на одноразовую базу. Ревизия `0013` **удаляет колонку `ads.is_active`**, а `downgrade` не восстанавливает её значения — какое объявление было черновиком, после отката узнать неоткуда. Применение такой ревизии — операция владельца базы, выполняемая его собственным путём выката.

**Что из-за этого НЕ выполнено:**

| Критерий плана | Статус |
|---|---|
| `just upgrade` выполнен | **НЕ ВЫПОЛНЕН — отложено** |
| `uv run alembic current` печатает `0013` | **НЕ ПРОВЕРЕН — требует достижимой базы** |
| `uv run alembic heads` печатает ровно одну голову | ✅ выполнен (`0013 (head)`; команда читает каталог ревизий, к базе не подключается) |
| Round-trip тест `upgrade`/`downgrade` | ✅ выполнен (`tests/test_migrations/test_0013_ad_status.py`, 6 тестов) |

**Что человеку нужно сделать, чтобы применить ревизию:**

1. Убедиться, что `DATABASE_URL` указывает на ту базу, которую вы намерены изменить (боевую или разработческую — но осознанно).
2. Снять дамп таблицы объявлений — единственный способ пережить откат без потери сведений о черновиках:
   `pg_dump -t ads "$DATABASE_URL" > ads_before_0013.sql`
3. Применить ревизию: `just upgrade` (= `uv run alembic upgrade head`).
4. Проверить: `uv run alembic current` должен напечатать `0013 (head)`.

**Последствие для следующих планов.** Планы 02-04…02-07 будут работать против базы, в схеме которой колонки `ads.status` ещё нет, а `ads.is_active` ещё есть. Полная суита при этом зелёная — она строит схему через `Base.metadata.create_all` из модели и о ревизиях не знает (`tests/conftest.py`). Но **приложение, запущенное против неприменённой базы, упадёт ошибкой SQL на каждом чтении `ads`**: модель уже спрашивает `ads.status`. Любая ручная проверка (UAT) на живом стенде до шага 3 бессмысленна.

---

## Performance

- **Duration:** ~32 min
- **Started:** 2026-08-10T11:30:00Z (примерно; первый коммит — 11:47:47Z)
- **Completed:** 2026-08-10T12:02:00Z
- **Tasks:** 3 (1 — решение `defer`, 2 — исполнена полностью, 3 — исполнена частично)
- **Files modified:** 20 (5 создано, 15 изменено)

## Accomplishments

- **Состояние объявления работает во всех шести слоях одним коммитом.** Схема (ревизия 0013), модель (`Ad.status`), доменный подбор расписаний, страничный слой, публичный JSON-API и шаблон карточки правятся вместе: разделив их, мы оставили бы промежуточное состояние, в котором `/api/ads` отвечает 500, а `/dashboard` и обе страницы расписаний падают ошибкой SQL.
- **D-01 закрыт с прохибицией.** Черновик не выбирается планировщиком, и его `next_run_at` **сдвигается вперёд**, а не остаётся в прошлом. Это и есть содержательная часть: фильтр в `WHERE` тоже не создал бы задач, но при публикации черновика расписание выстрелило бы всеми накопленными пропущенными слотами — тихой рассылкой задним числом в чужие Telegram/WhatsApp/MAX-группы, которую нельзя отозвать.
- **Все восемь читателей снятого флага переведены**, включая двух, которых нет ни в одном списке `02-CONTEXT.md`: счётчик на `/dashboard` и публичный контракт `/api/ads` (`AdResponse`, `UpdateAdRequest`). Живость каждого закреплена тестом на код ответа.
- **Первый в проекте тест, реально исполняющий ревизию Alembic.** До сих пор ни один тест не импортировал и не запускал Alembic: суита строит схему из модели. Ревизия, чей `downgrade` объявлен необратимым по данным, не может быть первой, чей текст никто не запускал.
- **Безопасный дефолт сделан односторонним.** Нераспознанное значение состояния трактуется как черновик и планировщиком, и шаблоном. Асимметрия сознательная: лишний бейдж «Черновик» — мелкая неточность, отправленное объявление с неизвестным состоянием — необратимая рассылка.

## Task Commits

1. **Задача 1: Подтвердить момент прохождения необратимой двери** — решение `defer`, кода не порождает (см. раздел «Отложенный выкат»)
2. **Задача 2: Состояние объявления сквозным срезом** — `d074cab` (test, RED) → `832365c` (feat, GREEN)
3. **Задача 3: Round-trip тест ревизии 0013** — артефакт `tests/test_migrations/` создан в `d074cab` и доведён до зелёного в `832365c`; часть A (`just upgrade`) отложена

_Плановый цикл TDD соблюдён: `test(...)` перед `feat(...)`. См. «Отклонения», п. 1 — почему у Задачи 2 два коммита, а не один._

## Files Created/Modified

**Создано:**
- `alembic/versions/0013_ad_status.py` — единственное изменение схемы фазы: добавление `ads.status`, индекс `ix_ads_status`, снятие `ads.is_active`
- `tests/test_application/test_collect_due_draft.py` — регрессия D-01 рядом с боевой диспетчеризацией, включая утверждение о сдвиге `next_run_at`
- `tests/test_pages/test_ads_status.py` — бейдж, безопасный дефолт, живость всех восьми читателей, отказ JSON-API на неизвестном значении
- `tests/test_migrations/__init__.py`, `tests/test_migrations/test_0013_ad_status.py` — round-trip ревизии на временной файловой SQLite

**Изменено:**
- `app/constants.py` — `AD_STATUS_DRAFT`, `AD_STATUS_PUBLISHED`, `AD_STATUSES`
- `app/models/ad.py` — `status: Mapped[str]` с индексом и умолчанием «опубликовано»; `is_active` и импорт `Boolean` сняты
- `app/application/scheduling/use_cases.py` — `effective_ad_status`, ветка пропуска в `collect_due_schedules`, дублирующая проверка в `send_message_once`
- `app/routes/ads.py` — `UpdateAdRequest.status: Literal["draft", "published"] | None`, `AdResponse.status: str`
- `app/pages/ads.py` — параметр формы `is_active` снят, `status` принимается необязательным и проверяется по `AD_STATUSES`
- `app/pages/common.py` — Jinja-глобалы `AD_STATUS_DRAFT` / `AD_STATUS_PUBLISHED`
- `app/pages/dashboard.py` — счётчик объявлений на `Ad.status == AD_STATUS_PUBLISHED`
- `app/pages/schedules.py` — фильтры выбора объявлений в `schedules_new` и `schedules_edit`
- `app/templates/ads/includes/ad_card.html` — ячейка состояния с безопасным дефолтом
- `app/templates/ads/form.html` — тумблер активности снят (D-04), комментарий приведён в соответствие
- `tests/test_constants.py`, `tests/test_models/test_ad.py`, `tests/test_routes/test_ads.py`, `tests/test_pages/test_ads_image_ownership.py`, `tests/test_pages/test_schedule_creation_path_exists.py` — переведены на новое поле

## Decisions Made

1. **Пропуск черновика — ветка со сдвигом `next_run_at`, не условие в `WHERE`.** Единственная реализация, при которой публикация черновика не вызывает залпа пропущенных отправок. Закреплено отдельным тестом, который и есть проверка прохибиции плана.

2. **Безопасный дефолт односторонний.** `effective_ad_status` возвращает «опубликовано» только для точного совпадения; всё прочее — черновик. Одна функция обслуживает и планировщик, и защиту в глубину; шаблон повторяет то же условие (`ad.status == AD_STATUS_PUBLISHED`), а не проверку на черновик.

3. **`send_message_once` пишет `SendLog` со статусом `"fail"`, а не новым словом.** Журнал отправок читают четыре шаблона (`history/`, `dashboard/`, `admin/`), и незнакомое значение отрисовалось бы там сырой латиницей через ветку-заглушку. Отправки не было — `"fail"` честен, причина названа в `error_message` (`Ad {id} is a draft`). Новое слово статуса потребовало бы правки четырёх шаблонов и CSS, то есть выхода за список файлов плана.

4. **Ревизия выписывает литерал `"published"` сама.** Импорт из `app.constants` связал бы уже применённую миграцию с текущим кодом: переименование константы задним числом изменило бы смысл давно выполненного шага. Расхождение ловит round-trip тест, который сравнивает результат ревизии с ожидаемым значением.

5. **Форма редактора принимает `status` необязательным.** По D-04 переключателя публикации в макете нет, поле не приходит — и состояние не трогается. Сохранение текста не должно молча публиковать черновик. Значение вне `AD_STATUSES` отбрасывается по той же причине, что и на JSON-входе.

6. **Round-trip тест стартует со штампа `0012`, а не с `base`.** Прогон от нуля на SQLite не доходит до `0013`: чужая ревизия `0005` вызывает `op.drop_constraint`, на котором Alembic под SQLite поднимает `NotImplementedError`. Тест сам приводит базу в состояние схемы `0012`, штампует его и запускает настоящие `upgrade`/`downgrade` — каждая операция самой `0013` исполняется, ничего не обходится. Починка `0005` — чужая ревизия и выход за границы плана.

## Deviations from Plan

### 1. [Процедурное] Задача 2 закоммичена двумя коммитами вместо одного

- **Найдено:** на старте Задачи 2
- **Ситуация:** `<action>` требует одного коммита, а тип плана (`type: tdd`) требует последовательности `test(...)` → `feat(...)`.
- **Разрешение:** RED-коммит `d074cab` содержит **только тесты**; вся реализация — в одном коммите `832365c`. Обоснование плана («разделение оставляет промежуточное состояние, в котором `/api/ads` отвечает 500») касается разделения *реализации*, а она не разделена. Коммит с одними лишь падающими тестами приложение не ломает.
- **Проверка:** `git log` содержит `test(...)` перед `feat(...)`; `832365c` меняет все восемь читателей одновременно.

### 2. [Rule 3 — Blocking] Добавлены Jinja-глобалы в `app/pages/common.py` (файла нет в списке плана)

- **Найдено:** во время Задачи 2, при правке `ad_card.html`
- **Проблема:** `key_links` плана требует, чтобы шаблон ссылался на `AD_STATUS_PUBLISHED`, а `app/constants.py` оставался единственным источником значения. Карточка объявления — **макрос**, а импортированным макросам Jinja контекст вызывающего не передаёт: значение не доехало бы ни переменной шаблона, ни контекстом ответа.
- **Исправление:** `AD_STATUS_DRAFT` и `AD_STATUS_PUBLISHED` зарегистрированы глобалами окружения по образцу `nav_items` / `admin_nav_item`. Конструирования `Settings` на импорте не добавлено — инвариант 02-01 не нарушен.
- **Файлы:** `app/pages/common.py`
- **Проверка:** `tests/test_pages/test_ads_status.py` (три теста на бейдж) — зелёные; полная суита зелёная.
- **Committed in:** `832365c`

### 3. [Область] Тесты, конструирующие `Ad(is_active=...)`, переведены на новое поле

- **Найдено:** во время Задачи 2
- **Проблема:** `tests/test_pages/test_schedule_creation_path_exists.py` (страховочная сетка SC-3), `tests/test_routes/test_ads.py` и `tests/test_pages/test_ads_image_ownership.py` обращались к снятому полю. План перечисляет только первые два файла тестов.
- **Исправление:** сетке SC-3 задано `status=AD_STATUS_PUBLISHED` явно — на черновике страница `/schedules/new` не предложила бы ни одного объявления и сетка зазеленела бы вакуумно. Из `_form` в тесте владения вложениями убран неиспользуемый параметр.
- **Проверка:** `tests/test_pages/test_schedule_creation_path_exists.py` зелёный, как того требует `<ordering_contract>`.
- **Committed in:** `d074cab`

---

**Total deviations:** 3 (1 процедурная, 1 Rule 3 — blocking, 1 расширение области на смежные тесты)
**Impact on plan:** Ни одна не расширяет объём работ. Отклонение 2 — единственный способ выполнить `key_links` плана; отклонения 1 и 3 — следствия ограничений инструментов и полноты списка файлов.

## Issues Encountered

1. **`alembic upgrade head` от `base` не проходит на SQLite.** Ревизия `0005` вызывает `op.drop_constraint`, на котором Alembic под SQLite поднимает `NotImplementedError`. Это свойство чужой ревизии, к `0013` отношения не имеющее; чинить её — выйти за границы плана. Обойдено штампом `0012` в фикстуре теста (см. «Решения», п. 6) и объяснено в докстринге теста, чтобы следующий читатель не принял это за небрежность.

2. **`ScriptDirectory.get_heads()` возвращает список, а не кортеж.** Собственное утверждение теста было неверным; исправлено в GREEN-коммите.

## Known Stubs

Отсутствуют. Все написанные пути подключены к данным; заглушек и `TODO` план не оставил.

## Threat Flags

Новых поверхностей вне `<threat_model>` плана не появилось. Все пять диспозиций `mitigate` реализованы:

| Угроза | Реализация |
|---|---|
| T-02-11 | `Literal["draft", "published"]` в `UpdateAdRequest` + тест соответствия литералов `AD_STATUSES` |
| T-02-12 | ветка со сдвигом `next_run_at`, тест `test_draft_schedule_next_run_at_moves_forward` |
| T-02-13 | дублирующая проверка в `send_message_once` |
| T-02-14 | миграция и оба фильтра `app/pages/schedules.py` одним коммитом; сетка SC-3 зелёная |
| T-02-15 | `AdResponse` и `UpdateAdRequest` правятся тем же коммитом; живость `/api/ads` закреплена тестом |

`T-02-16` (`accept`) — потеря сведений о черновиках при откате — объявлена комментарием в ревизии и зафиксирована тестом `test_downgrade_restores_legacy_column_and_removes_status`, чтобы потеря не выглядела дефектом.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/ -q` | ✅ **742 passed** (базовая линия 712 + 30 новых) |
| `uv run pytest tests/test_application tests/test_pages/test_ads_status.py tests/test_models/test_ad.py tests/test_constants.py tests/test_routes/test_ads.py tests/test_pages/test_schedule_creation_path_exists.py tests/test_worker_tasks.py -q` | ✅ 67 passed |
| `grep -c 'is_active' app/models/ad.py` | ✅ `0` |
| `grep -rn 'Ad\.is_active' app/` | ✅ пусто |
| `grep -rn 'ad\.is_active' app/templates/` | ✅ пусто |
| `alembic/versions/0013_ad_status.py` содержит `revision = "0013"` / `down_revision = "0012"` | ✅ |
| Ревизия содержит `ВНИМАНИЕ: откат необратимо теряет данные` | ✅ |
| `app/routes/ads.py` содержит `Literal` на входном значении состояния | ✅ |
| `AD_STATUS_DRAFT` в ветке пропуска, а не в `select(` | ✅ строка 96 |
| `uv run alembic heads` | ✅ `0013 (head)` — одна голова |
| `git diff --stat app/messengers/` | ✅ пусто — протоколы отправки не тронуты |
| `just upgrade` | ⛔ **ОТЛОЖЕНО решением пользователя** |
| `uv run alembic current` | ⛔ **НЕ ПРОВЕРЕНО** — требует достижимой базы |

## User Setup Required

**Да — один обязательный шаг.** Ревизия `0013` требует применения к базе рукой владельца. Полная процедура — в разделе «Отложенный выкат ревизии 0013» выше. Кратко: снять дамп таблицы `ads`, выполнить `just upgrade`, проверить `uv run alembic current`.

Дополнительно (не блокирует): в основном рабочем каталоге стоит обновить граф знаний — `graphify update .`. В worktree это не сделано намеренно: `graphify-out/` в `.gitignore`, и сборка ~59 МБ в одноразовом worktree была бы выброшена вместе с ним.

## Next Phase Readiness

**Готово для планов 02-04…02-07:**
- `app/constants.py` — единственный источник значений состояния; читать оттуда, литералы не выписывать
- `effective_ad_status` в `app/application/scheduling/use_cases.py` — использовать для любой новой проверки состояния, чтобы безопасный дефолт не разъехался
- Jinja-глобалы `AD_STATUS_DRAFT` / `AD_STATUS_PUBLISHED` доступны любому шаблону и макросу
- `tests/test_migrations/` — образец round-trip теста, если фаза заведёт ещё одну ревизию
- Страницы `/schedules/new` и `/schedules/{id}/edit` живы и переведены на новое поле; их сносит план 02-06, не раньше

**Блокирующее замечание:** до применения ревизии (шаг из «User Setup Required») любая ручная проверка на живом стенде невозможна — модель спрашивает `ads.status`, которой в базе ещё нет. Автоматическая суита от этого не зависит и остаётся единственным достоверным сигналом до выката.

## Self-Check: PASSED

Проверено на диске и в истории git, а не по памяти:

**Файлы созданы** — все шесть присутствуют: `alembic/versions/0013_ad_status.py`, `tests/test_application/test_collect_due_draft.py`, `tests/test_pages/test_ads_status.py`, `tests/test_migrations/__init__.py`, `tests/test_migrations/test_0013_ad_status.py`, `.planning/phases/02-obyavleniya-i-raspisaniya/02-03-SUMMARY.md`.

**Коммиты существуют** — `d074cab` (test), `832365c` (feat), `549e1a1` (docs); все на ветке агента, база `896c994` не переписана.

**Рабочее дерево чистое** — неотслеживаемых и незакоммиченных файлов нет.

**Не выполнено намеренно (не дефект):** ревизия `0013` не применена ни к какой базе; `uv run alembic current` не запускался. Оба — прямое следствие решения пользователя `defer`, зафиксированного выше отдельным разделом и помеченного в `coverage` как `D9` с `human_judgment: true`.

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-10*
