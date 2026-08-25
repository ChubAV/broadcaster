---
phase: 02-obyavleniya-i-raspisaniya
plan: 01
subsystem: testing
tags: [pytest, pydantic-settings, jinja2, fastapi, dependency-injection]

requires:
  - phase: 01-interfejsnyj-fundament
    provides: Новый шелл, макросы ads/includes/ad_card.html и ads/form.html, тестовые фикстуры client/authed_client/db_session
provides:
  - Зелёная базовая линия фазы 2 — 662 passed и с `.env`, и без него
  - Изоляция тестовых `Settings` от `.env` разработчика (`_env_file=None` во всех 18 конструированиях)
  - `bind_image_url_globals(settings)` — шаблонные глобалы изображений привязаны к настройкам приложения (D-21)
  - Первый рендер-тест редактора объявления `/ads/new` и `/ads/{id}/edit`
  - Страховочная сетка SC-3 — проверяемый факт, что путь создания расписания жив в каждом коммите фазы
affects: [02-02, 02-03, 02-04, 02-05, 02-06, 02-07]

actuals:
  tokens: 7100
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Тестовые Settings строятся с `_env_file=None` — окружение разработчика в суиту не протекает"
    - "Шаблонные глобалы, зависящие от настроек, привязываются в create_app, а не вызывают get_settings() на месте"
    - "Страховочная сетка на дизъюнкции путей: тест переживает переезд функциональности между экранами"

key-files:
  created:
    - tests/test_pages/test_ads_editor.py
    - tests/test_pages/test_schedule_creation_path_exists.py
  modified:
    - app/pages/common.py
    - app/main.py
    - tests/conftest.py
    - tests/test_pages/test_shell.py

key-decisions:
  - "`_env_file=None` в тестах вместо правки `app/config.py` — продовое поведение `model_config` не тронуто"
  - "Привязка глобалов через `create_app` вместо параметрической инъекции: `ad_card` — макрос, контекст вызывающего Jinja ему не передаёт"
  - "Сетка SC-3 утверждает дизъюнкцию путей, а не конкретный маршрут — иначе она краснела бы ровно тогда, когда переезд идёт по плану"
  - "`requirements-completed` оставлен пустым: ADS-04 и ADS-06 этим планом не реализуются, их владелец — план 02-04"

patterns-established:
  - "Изоляция конфигурации в тестах: любое `Settings(...)` в `tests/` передаёт `_env_file=None` — проверяется AST-обходом, а не грепом по строке"
  - "Настройко-зависимые шаблонные глобалы: `bind_image_url_globals(settings)` вызывается из `create_app`; на импорте модуля Settings не конструируется"
  - "Страховочная сетка на межплановый переезд: тест утверждает «хотя бы один путь жив», а не конкретную реализацию"

requirements-completed: []

coverage:
  - id: D1
    description: "Тестовые Settings изолированы от `.env` разработчика во всех 12 модулях"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_config.py tests/test_config_s3.py tests/test_e2e.py tests/test_main.py tests/test_routes/test_groups_bulk.py tests/test_routes/test_sync_groups.py tests/test_routes/test_tg_user_auth.py tests/test_routes/test_uploads.py tests/test_routes/test_wa_sync_status.py tests/test_services/test_messenger_factory.py -q"
        status: pass
      - kind: other
        ref: "AST-обход tests/**/*.py: вызовов Settings() без _env_file — 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Шаблонные глобалы изображений привязаны к настройкам приложения; импорт app.pages.common не конструирует Settings (D-21, T-02-02)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_ads_editor.py#test_image_base_url_comes_from_app_settings"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_ads_editor.py#test_editor_s3_public_url_global_comes_from_app_settings"
        status: pass
      - kind: other
        ref: "импорт app.pages.common из временного каталога без .env и без DATABASE_URL/SECRET_KEY: 0 конструирований Settings, exit 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "`/ads/new` и `/ads/{id}/edit` покрыты рендер-тестом на реальных данных (T-02-03)"
    requirement: ADS-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_ads_new_renders"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_ads_edit_renders_own_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_all_pages_render_new_shell[/ads/new]"
        status: pass
    human_judgment: false
  - id: D4
    description: "Владение объявлением при открытии редактора закреплено регрессионным контрактом (T-02-04)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_ads_edit_foreign_ad_is_not_served"
        status: pass
    human_judgment: false
  - id: D5
    description: "Страховочная сетка SC-3: путь создания расписания жив в любом коммите фазы"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_creation_path_exists.py#test_schedule_creation_path_exists"
        status: pass
    human_judgment: false
  - id: D6
    description: "Базовая линия фазы: полный прогон суиты зелёный в обеих конфигурациях окружения"
    verification:
      - kind: unit
        ref: "uv run pytest tests/ -q (с .env): 662 passed"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/ -q (без .env): 662 passed"
        status: pass
    human_judgment: false

duration: 46min
completed: 2026-08-10
status: complete
---

# Phase 2 Plan 01: Зелёная база и рендер-тест редактора Summary

**`_env_file=None` во всех тестовых `Settings` плюс `bind_image_url_globals(settings)` в `create_app` — суита выросла с 652 до 662 тестов и стала зелёной независимо от наличия `.env`, а `/ads/new` и `/ads/{id}/edit` впервые покрыты рендер-тестом.**

## Performance

- **Duration:** ~46 min
- **Started:** 2026-08-10T07:41:00Z
- **Completed:** 2026-08-10T08:27:00Z
- **Tasks:** 2
- **Files modified:** 16 (2 создано, 14 изменено)

## Accomplishments

- **Обе половины дефекта закрыты.** До плана конфигурации взаимно исключали друг друга: с `.env` рендерился редактор, но суита была красной; без `.env` суита была зелёной, но редактор отдавал 500. Теперь обе конфигурации дают 662 passed.
- **Дефект воспроизведён, а не принят на веру.** В воркдире `.env` нет, поэтому заявленные исследованием 25 failed + 3 errors на нём не воспроизводились. Синтетический `.env` с типовыми dev-значениями дал **26 failed + 3 errors** — после правки те же модули дают 49 passed.
- **`/ads/new` вернулся в сплошной обход шелла.** Известное ограничение из Плана 08 Фазы 1 снято: страница участвует в `SHELL_ROUTES` наравне с остальными (4 параметризованных теста).
- **Сетка SC-3 существует и зелёная** — обещание «пользователь ни в один момент выката не остаётся без возможности создать расписание» стало проверяемым фактом.

## Task Commits

1. **Задача 1: Изолировать тестовые настройки от `.env` разработчика** — `8a17aa7` (test)
2. **Задача 2 (TDD RED): падающие рендер-тесты редактора и сетка SC-3** — `2785f03` (test)
3. **Задача 2 (TDD GREEN): привязать глобалы изображений к настройкам приложения** — `5771a50` (feat)

REFACTOR-коммита нет: после GREEN чистить было нечего.

## Files Created/Modified

**Создано:**
- `tests/test_pages/test_ads_editor.py` — 6 тестов: рендер `/ads/new`, рендер `/ads/{id}/edit` на реальных данных, отказ по чужому объявлению, привязка базового URL изображений к настройкам приложения (для `get_image_url` и для `s3_public_url()`).
- `tests/test_pages/test_schedule_creation_path_exists.py` — сетка SC-3 на дизъюнкции: `/schedules/new` отвечает 200 **или** редактор объявления содержит форму создания расписания.

**Изменено:**
- `app/pages/common.py` — три глобала (`get_image_url`, `resolve_image_url`, `s3_public_url`) больше не вызывают `get_settings()`; введены `bind_image_url_globals(settings)` и внутренний `_bind_image_url_globals(base_url)`; на импорте регистрируется безопасный дефолт с пустым базовым URL. Импорт `get_settings` удалён как ставший неиспользуемым.
- `app/main.py` — `bind_image_url_globals(settings)` вызывается в `create_app` сразу после разрешения настроек.
- `tests/conftest.py`, `tests/test_config.py`, `tests/test_config_s3.py`, `tests/test_e2e.py`, `tests/test_main.py`, `tests/test_routes/test_groups_bulk.py`, `tests/test_routes/test_sync_groups.py`, `tests/test_routes/test_tg_user_auth.py`, `tests/test_routes/test_uploads.py`, `tests/test_routes/test_wa_sync_status.py`, `tests/test_services/test_messenger_factory.py` — `_env_file=None` в каждом конструировании `Settings` (18 мест).
- `tests/test_pages/test_shell.py` — `/ads/new` добавлен в `SHELL_ROUTES`; устаревший комментарий про 500 переписан.

## Decisions Made

- **`_env_file=None` в тестах, а не правка `app/config.py`.** Продовое `model_config = {"env_file": ".env", ...}` осталось нетронутым — меняется только тестовое окружение. Продовый код в Задаче 1 не трогался вовсе.
- **`test_log_level_override` тоже получил `_env_file=None`.** Тест проверяет чтение переменных окружения (`os.environ`), а не dotenv-файла; `_env_file=None` отключает только файл, поэтому предмет теста сохранён. Причина записана комментарием «why» в коде. Отдельного исключения, предусмотренного планом, не потребовалось: теста на чтение файла окружения в суите нет.
- **Привязка глобалов через `create_app`, а не параметрическая инъекция из `02-PATTERNS.md`.** `ad_card` — макрос, а импортированным макросам Jinja контекст вызывающего не передаёт; параметрическая форма потребовала бы менять сигнатуру макроса и все его вызовы в `ads/list.html` и `ads/partial_cards.html`. Решение записано комментарием «why» в `app/pages/common.py`.
- **`requirements-completed` оставлен пустым.** Frontmatter плана объявляет `requirements: [ADS-04, ADS-06]`, но этот план не реализует ни черновик с автосохранением, ни предпросмотр — по `<ordering_contract>` их владелец план 02-04. Отметка о выполнении здесь исказила бы трассируемость. `REQUIREMENTS.md` не изменялся.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Удалён ставший неиспользуемым импорт `get_settings` в `app/pages/common.py`**
- **Found during:** Задача 2 (Часть A)
- **Issue:** После снятия трёх глобалов с `get_settings()` импорт остался мёртвым. Критерий приёмки требует, чтобы `get_settings()` не вызывался в области регистрации глобалов; висящий импорт вводил бы в заблуждение относительно того, читает ли модуль окружение.
- **Fix:** `from app.config import Settings, get_settings` → `from app.config import Settings`. Предварительно проверено грепом, что ни один модуль не реэкспортирует `get_settings` из `app.pages.common` (11 импортирующих модулей берут только `templates`, `check_is_admin`, `get_user_from_cookie`, `get_shell_context`).
- **Files modified:** `app/pages/common.py`
- **Verification:** Полная суита 662 passed; импорт модуля из каталога без `.env` даёт 0 конструирований `Settings`.
- **Committed in:** `5771a50`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Правка в границах файла, объявленного планом. Расширения объёма нет.

## Issues Encountered

- **Заявленный дефект не воспроизводился в воркдире.** `.env` не отслеживается git и в изолированный worktree не попадает, поэтому исходный прогон дал 652 passed — базовая линия исследования (25 failed + 3 errors) выглядела бы опровергнутой. Разрешено воспроизведением: синтетический `.env` с типовыми dev-значениями (SMTP-хост, `s3_public_url`, `admin_email`, `telegram_api_id`) дал 26 failed + 3 errors, то есть тот же дефект той же природы. После правки — 49 passed на тех же модулях. Файл удалён по завершении; в коммитах его нет (`.env` в `.gitignore`).
- **Формулировка критерия приёмки Задачи 1 неисполнима буквально.** Критерий `grep -rn "Settings(" tests/ | grep -v "_env_file"` построчный, а все конструирования в проекте многострочные: `Settings(` и `_env_file=None` физически на разных строках, поэтому грep всегда вернул бы все 18 строк. Проверено намерение, а не буква: AST-обход всех файлов `tests/` подтвердил, что вызовов `Settings(...)` без ключевого аргумента `_env_file` — ноль.
- **Утверждение плана про `ValidationError` на импорте `app/pages/common.py` неточно.** Три глобала были лямбдами, поэтому `Settings()` конструировался лениво — на рендере, а не на импорте; импорт модуля падал бы только при неленивом обращении. Наблюдаемое следствие ровно то, что описывал план (`/ads/new` → 500 без `.env`), и требуемая правка та же. Инвариант «на импорте `app.pages.common` не конструируется ни одного `Settings`» проверен явно ловушкой на `Settings.__init__` и выполняется.

## Known Stubs

Отсутствуют. Заглушек, TODO/FIXME, пропущенных тестов и неисполненных `<verify>` в изменённых файлах нет.

## Threat Flags

Новой security-релевантной поверхности не появилось: план не добавляет ни маршрутов, ни путей аутентификации, ни доступа к файлам, ни изменений схемы. Диспозиции `mitigate` из `<threat_model>` закрыты — T-02-01 Задачей 1, T-02-02/T-02-03/T-02-04 Задачей 2.

## TDD Gate Compliance

Задача 2 исполнена по циклу RED → GREEN.

- **RED:** `2785f03` (`test(...)`). Без `.env` — 4 failed (`/ads/new` отдавал 500), с `.env` — 2 failed (базовый URL приезжал из окружения). Тесты падали по назначенной причине, а не по ошибке в самих тестах.
- **GREEN:** `5771a50` (`feat(...)`). 6 passed в обеих конфигурациях.
- **REFACTOR:** не потребовался, коммита нет.

Сетка SC-3 (`test_schedule_creation_path_exists.py`) в RED-прогоне была зелёной — и это её штатное состояние: она сторожит инвариант, который уже выполняется и обязан продолжать выполняться, а не ведёт разработку. Правило fail-fast к ней неприменимо.

## User Setup Required

None — внешние сервисы не настраиваются, пакеты не устанавливались.

## Next Phase Readiness

- **Базовая линия зафиксирована: 662 passed.** С этого момента `<verify>` любой последующей задачи фазы что-то доказывает — регрессию своего плана можно отличить от унаследованной.
- **План 02-02** (долги Фазы 1: CR-01, CR-02, WR-01) может стартовать: правки лягут на стабильный код.
- **План 02-04** получает рендер-тест редактора как точку опоры для переделки экрана.
- **Планы 02-05 и 02-06** обязаны держать `tests/test_pages/test_schedule_creation_path_exists.py` зелёным. При переносе создания расписания на собственный адрес пополнить `SCHEDULE_CREATE_ACTIONS` в этом файле, а не ослаблять утверждение.
- **Ограничение, оставленное сознательно:** `templates` — модульный синглтон, общий на процесс, поэтому привязка глобалов глобальна и последний `create_app` выигрывает. Для боя (одно приложение на процесс) и для тестов, создающих приложение в фикстуре, этого достаточно. Разведение окружений Jinja по приложениям — архитектурная правка за границами плана; записано комментарием в `app/pages/common.py`.
- **ADS-04 и ADS-06 не закрыты** этим планом и в `REQUIREMENTS.md` не отмечены — владелец план 02-04.

## Self-Check: PASSED

- `tests/test_pages/test_ads_editor.py` — FOUND
- `tests/test_pages/test_schedule_creation_path_exists.py` — FOUND
- `app/pages/common.py` — FOUND, содержит `def bind_image_url_globals`
- `app/main.py` — FOUND, содержит вызов `bind_image_url_globals(settings)`
- Коммит `8a17aa7` — FOUND
- Коммит `2785f03` — FOUND
- Коммит `5771a50` — FOUND

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-10*
