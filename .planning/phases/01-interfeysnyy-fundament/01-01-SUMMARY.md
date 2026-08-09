---
phase: 01-interfeysnyy-fundament
plan: 01
subsystem: ui
tags: [jinja2, fastapi, staticfiles, htmx, alpinejs, css-tokens, woff2, sqlalchemy]

# Dependency graph
requires: []
provides:
  - "Раздача статики: /static смонтирован через StaticFiles с name=static"
  - "app/static/css/app.css — дизайн-токены :root, дословные keyframes, три медиазапроса, адаптивные примитивы"
  - "Новый шелл app/templates/base.html на атрибутах data-shell / data-side / data-nav / data-quota / data-user / data-tabs / data-head / data-body"
  - "get_shell_context(db, user) — публичный контракт живых данных шелла (D-09/D-19)"
  - "load_shell_context — router-level async-зависимость, кладёт шелл в request.state.shell"
  - "Контракт «страница → шелл»: блоки page_title / page_subtitle / page_actions"
  - "NAV_ITEMS — единый источник состава навигации (D-11)"
  - "Вендоренные htmx 1.9.10 и Alpine 3.13.3, 22 self-hosted woff2"
  - "Фикстуры authed_client / admin_client для cookie-авторизации page-роутов"
affects: [02-komponenty, 03-htmx-etalon, 04-dashboard, 05-istoriya, 06-admin-vorkery, 07-tarify, 08-svodnaya-proverka]

actuals:
  tokens: 14712
  tasks: 3
  commits: 3

tech-stack:
  added: [htmx 1.9.10 (vendored), Alpine.js 3.13.3 (vendored), IBM Plex Sans, IBM Plex Mono, Space Grotesk]
  patterns:
    - "Router-level async Depends вместо контекст-процессора Starlette (они синхронны в 0.52.1)"
    - "Скалярные подзапросы в одном SELECT для агрегатов шелла"
    - "Атрибутные селекторы data-* вместо utility-классов"
    - "Состав навигации — один список в Python, два цикла в шаблоне"

key-files:
  created:
    - app/static/.gitkeep
    - app/static/css/app.css
    - app/static/js/htmx.min.js
    - app/static/js/alpine.min.js
    - app/static/fonts/ (22 woff2)
    - tests/test_pages/test_shell.py
  modified:
    - app/main.py
    - app/pages/common.py
    - app/pages/__init__.py
    - app/templates/base.html
    - tests/conftest.py
    - tests/test_routes/test_schedules_profile_timezone.py

key-decisions:
  - "Задача 1 (D-19, one-way): выбран вариант rename-to-sessions — источник MessengerAccount.status из БД сохранён, ключи контракта названы sessions_online / sessions_total"
  - "quota.used считается по журналу списаний BalanceTransaction за текущий период, limit = used + остаток баланса"
  - "get_shell_context читает MessageBalance без get_or_create_balance — рендер страницы не пишет в БД"
  - "Активный пункт помечается is-active только в сайдбаре; нижние табы используют aria-current"
  - "Основная текстовая гарнитура — IBM Plex Sans (кириллица), Space Grotesk оставлен только для --font-display"

patterns-established:
  - "Живые данные шелла: одна async-зависимость роутера → request.state.shell, ноль правок в 26 обработчиках"
  - "Контракт «страница → шелл» через блоки Jinja (page_title / page_subtitle / page_actions), а не через переменные контекста"
  - "Адаптивный примитив [data-area=\"meta\"] вместо селектора по подстроке инлайн-стиля"
  - "asset_version как глобал окружения Jinja — инвалидация кэша без build-шага"

requirements-completed: [UI-01, UI-02, UI-03, UI-06]

coverage:
  - id: D1
    description: "Своя статика вместо CDN: /static отдаёт app.css с токенами, htmx и Alpine"
    requirement: "UI-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_app_css_served"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_static_js_served"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_no_external_cdn"
        status: pass
    human_judgment: false
  - id: D2
    description: "Страница рендерится в новом шелле макета (data-shell / data-side / data-nav / data-head / data-body / data-tabs)"
    requirement: "UI-02"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_profile_renders_new_shell"
        status: pass
    human_judgment: false
  - id: D3
    description: "Единая навигация с подсветкой активного раздела, сохранённым пунктом «Группы» и админ-блоком только для админа"
    requirement: "UI-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_active_nav_highlight"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_admin_nav_hidden_for_regular_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_admin_nav_visible_for_admin"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_nav_keeps_groups_and_links"
        status: pass
    human_judgment: false
  - id: D4
    description: "Живые данные шелла: счётчики меню, виджет квоты, индикатор сессий мессенджеров"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_shell_live_data"
        status: pass
    human_judgment: false
  - id: D5
    description: "Адаптивные примитивы и нижние табы в разметке шелла"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_mobile_tabs_present"
        status: pass
    human_judgment: false
  - id: D6
    description: "Шрифты со своего домена, основной текстовый стек с кириллицей"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_fonts_served"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_app_css_declares_fonts"
        status: pass
    human_judgment: true
    rationale: "Автотест доказывает, что файлы раздаются и объявлены, но не то, что длинные русские строки действительно набраны IBM Plex Sans, а не системным фолбэком — это видно только глазом (human-check Задачи 3)"
  - id: D7
    description: "Визуальная сверка шелла с макетом и поведение нижних табов на ширине <860px и на реальном устройстве"
    verification: []
    human_judgment: true
    rationale: "env(safe-area-inset-bottom) ведёт себя только на железе; соответствие макету — судейское решение (пункты 5-6 <verification> плана)"

# Metrics
duration: 30min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 01: Сквозной срез интерфейсного фундамента — Summary

**Собственная раздача статики, дизайн-токены в `:root`, полностью переписанный шелл `base.html` на атрибутах макета и контракт живых данных `get_shell_context()` — один вертикальный путь от статики до теста, доказанный на `/profile`.**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-08-09T09:30:00Z
- **Completed:** 2026-08-09T09:59:52Z
- **Tasks:** 3 (Задача 1 — решение пользователя, Задачи 2-3 — реализация)
- **Files modified:** 8 текстовых + 24 бинарных ассета

## Accomplishments

- **Три внешние зависимости рантайма устранены.** Tailwind CDN, внешний сервис шрифтов и unpkg-ссылки на htmx/Alpine удалены из `base.html`; htmx 1.9.10 (47 755 Б) и Alpine 3.13.3 (43 441 Б) вендорены, 22 woff2 (276 352 Б) раздаются со своего домена.
- **`app.css` — 626 строк:** токены `:root`, выведенные из частотной таблицы 490 инлайн-стилей макета; дословно перенесённые пять `@keyframes` и три медиазапроса с адаптивными примитивами `[data-row]` / `[data-rowhead]` / `[data-grow]` / `[data-hrow]`; 39 правил `@font-face`.
- **Шелл переписан целиком** по анатомии макета (строки 304-381), при этом три имени блоков `title` / `body` / `content` сохранены дословно — все 29 наследующих шаблонов продолжают собираться.
- **Навигация выписана один раз.** Было 26 копий одной ссылки в трёх местах (сайдбар, слайд-овер, табы) — стало один список `NAV_ITEMS` в Python и два цикла в шаблоне. Бургер и слайд-овер на Alpine удалены целиком (D-12).
- **Живые данные приходят из одной точки.** `load_shell_context` как router-level `Depends` кладёт результат в `request.state.shell`; ни один из 26 словарей контекста не тронут.
- **Тест-каркас Wave 0:** 12 тестов, покрывающих UI-01, UI-02, UI-03, UI-06; фикстуры `authed_client` / `admin_client` инкапсулируют cookie-авторизацию, которая раньше копировалась в каждый тест.
- **Регрессий нет:** 393 существующих теста зелёные, суммарно 405.

## Task Commits

1. **Задача 2 (RED): тест-каркас и фикстуры** — `b2c73fd` (test)
2. **Задача 2 (GREEN): сквозной срез — статика, токены, шелл, живые данные** — `150ea44` (feat)
3. **Задача 3: шрифты — self-host и кириллический стек** — `d6f3e66` (feat)

Задача 1 — `checkpoint:decision`, разрешена пользователем до старта этого агента; собственного коммита не производит, её результат вплавлен в `150ea44`.

## Files Created/Modified

**Создано**
- `app/static/.gitkeep` — гарантия существования каталога в git: `StaticFiles(directory=...)` бросает исключение при монтировании, а `conftest.py` вызывает `create_app()` в каждом тесте.
- `app/static/css/app.css` (626 строк) — токены, шрифты, дословный блок макета, стили шелла.
- `app/static/js/htmx.min.js`, `app/static/js/alpine.min.js` — вендоренные рантаймы (D-05).
- `app/static/fonts/*.woff2` (22 файла) — IBM Plex Mono ×15, Space Grotesk ×3, IBM Plex Sans ×4.
- `tests/test_pages/test_shell.py` (12 тестов).

**Изменено**
- `app/main.py` — `_static_dir` и `app.mount("/static", StaticFiles(...), name="static")` сразу после `add_middleware`.
- `app/pages/common.py` (+166 строк) — `get_shell_context`, `NAV_ITEMS`, `ADMIN_NAV_ITEM`, `nav_label`, глобал `asset_version`.
- `app/pages/__init__.py` — `load_shell_context` и `APIRouter(dependencies=[...])`.
- `app/templates/base.html` — переписан (279 строк изменений, из них 193 удаления).
- `tests/conftest.py` — `authed_client`, `admin_client`.
- `tests/test_routes/test_schedules_profile_timezone.py` — позиционная проверка заменена точной (см. деviations).

## Decisions Made

### Задача 1 (D-19, one-way) — утверждённый контракт: `rename-to-sessions`

**Это решение фиксируется дословно: Фазы 4 (DASH-05) и 6 обязаны переиспользовать именно эти имена, а не изобретать свои.**

Источник оставлен без изменений — `MessengerAccount.status` из БД, **никогда** Docker SDK / перечисление контейнеров воркеров. Ключи-индикаторы переименованы в терминологию сессий, потому что значение измеряет состояние сессии мессенджера, а не состояние Docker-контейнера, и публичное имя контракта не должно обещать больше, чем измеряет.

Реализованная форма — `app/pages/common.py`:

```python
async def get_shell_context(db: AsyncSession, user: User | None) -> dict
```

- `user is None` → `{}` (ранний возврат, ноль запросов — страницы входа);
- иначе ключи:
  - `nav_counts` — `{"ads": int, "accounts": int, "schedules": int, "history": int}`
  - `quota` — `{"plan": str, "used": int, "limit": int, "percent": int, "expires_at": datetime | None}`
  - `sessions_online` — `int`, число `MessengerAccount` пользователя со `status == "active"`
  - `sessions_total` — `int`, общее число `MessengerAccount` пользователя

**Публичные имена — `sessions_online` / `sessions_total`, а не `workers_online` / `workers_total`.** Переименование распространено на: ключи словаря, атрибуты разметки в `data-head` (`data-sessions`, `data-sessions-online`, `data-sessions-total`), CSS-класс (`.session-pill` / `.session-dot` / `.session-label` вместо `.worker-pill`), тест `test_shell_live_data` и список `<artifacts_produced>` плана.

**Пользовательская подпись оставлена как в макете** — «воркеров онлайн · N». Переименованы только идентификаторы контракта. Фаза 4 сможет добавить рядом настоящий контейнерный показатель, не ломая контракт.

### Прочие решения

- **`quota.used` считается по журналу списаний.** `BalanceTransaction` с `amount < 0` за период с `MessageBalance.free_balance_reset_at` — это точная величина, каждое списание пишет строку. `limit = used + остаток`, `percent = round(used/limit*100)` с ограничением 0..100. При `is_unlimited` → `limit = 0`, `percent = 0`, в разметке «∞». Модели «использовано/лимит» в проекте не было; изобретать четырёхосевые лимиты Фазы 7 здесь не стали.
- **Чтение баланса без записи.** Взят прямой `select(MessageBalance)`, а не `get_or_create_balance` — последний делает `db.add` + `flush`, а рендер страницы не должен писать в БД.
- **Шесть агрегатов — один round-trip.** Счётчики и сессии посчитаны скалярными подзапросами в одном `SELECT`, потому что зависимость выполняется на каждом page-запросе.
- **`is-active` только в сайдбаре.** Нижние табы помечают активный пункт через `aria-current="page"`, поэтому признак `is-active` встречается на странице ровно один раз — как требует критерий UI-03.
- **Ссылка «Выйти» продублирована в табах.** На ширине ≤860px `data-user` скрыт медиазапросом, и без дубля выход стал бы недостижим с мобильного.
- **Имена файлов шрифтов.** `ibm-plex-mono-{400,500,600}-{cyrillic-ext,cyrillic,vietnamese,latin-ext,latin}.woff2` (15), `space-grotesk-{vietnamese,latin-ext,latin}.woff2` (3 — один файл обслуживает все четыре веса, поэтому веса в имени нет), `ibm-plex-sans-{cyrillic-ext,cyrillic,latin-ext,latin}.woff2` (4).
- **Итоговые имена токенов** зафиксированы в `:root`: поверхности `--bg` / `--surface-side` / `--surface` / `--surface-pill` / `--surface-input`; границы `--border-hair` / `--border-soft` / `--border-muted` / `--border-side` / `--border` / `--border-pill` / `--border-input` / `--border-control` / `--border-control-strong` / `--border-dashed`; текст `--text` / `--text-bright` / `--text-secondary` / `--text-tertiary` / `--text-muted` / `--text-faint` / `--text-dim` / `--text-on-accent`; акцент `--accent` / `--accent-cta` / `--accent-link` / `--accent-link-hover` / `--focus-ring`; статусы `--ok` / `--warn` / `--danger` / `--info`; радиусы `--r-xs` … `--r-2xl` / `--r-pill` / `--r-circle`; кегли `--fs-2xs` … `--fs-2xl` / `--fs-h1` / `--fs-h2` / `--fs-h3`; гарнитуры `--font-sans` / `--font-mono` / `--font-display`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] У модели `Schedule` нет поля `user_id`**
- **Found during:** Задача 2 (слой 5, счётчики шелла)
- **Issue:** План предписывал считать расписания как `select(func.count()).where(Schedule.user_id == user.id)`. Такого поля у модели нет: принадлежность расписания пользователю идёт через `Ad`.
- **Fix:** Счётчик переписан на `join(Ad, Schedule.ad_id == Ad.id).where(Ad.user_id == user.id)` — ровно как во всех четырёх запросах `app/pages/schedules.py:230,284,339,377`.
- **Files modified:** `app/pages/common.py`
- **Verification:** `test_shell_live_data` (счётчики отрисованы числами), полная суита зелёная.
- **Committed in:** `150ea44`

**2. [Rule 3 - Blocking] Позиционная проверка в существующем тесте ломалась новым шеллом**
- **Found during:** Задача 2 (прогон полной суиты)
- **Issue:** `test_new_schedule_form_uses_user_timezone_by_default` проверял `'selected' in html.split('Europe/Moscow')[1]`. Новый шелл показывает таймзону пользователя в блоке `data-user` **выше** формы, поэтому первое вхождение строки стало относиться к шеллу, а не к `<option>`. Это ровно Pitfall 8 из `01-RESEARCH.md`.
- **Fix:** Проверка заменена на точную — `assert '<option value="Europe/Moscow" selected' in html`, то есть на ту же формулировку, что уже используется в `tests/test_pages/test_profile.py:42`. Покрытие не ослаблено: новое утверждение строго сильнее (проверяет именно тот `<option>`, а не «что идёт после строки»).
- **Files modified:** `tests/test_routes/test_schedules_profile_timezone.py`
- **Verification:** `uv run pytest tests/ -q` → 403 passed на момент фикса.
- **Committed in:** `150ea44`

**3. [Rule 3 - Blocking] Литеральные критерии приёмки ловили упоминания в комментариях**
- **Found during:** Задача 2 (проверка критериев приёмки)
- **Issue:** Критерии `grep -c 'list_worker_containers' app/pages/common.py == 0` и `grep -c 'style-hover' app/static/css/app.css == 0` падали из-за пояснительных комментариев, которые называли запрещённые идентификаторы, объясняя, почему они не используются.
- **Fix:** Комментарии перефразированы («перечисление контейнеров воркеров», «псевдо-атрибуты наведения») — смысл сохранён, литеральные критерии выполняются.
- **Files modified:** `app/pages/common.py`, `app/static/css/app.css`
- **Verification:** оба `grep -c` возвращают 0.
- **Committed in:** `150ea44`

**4. [Rule 3 - Blocking] Тест Задачи 2 запрещал `@font-face`, тест Задачи 3 его требует**
- **Found during:** Задача 3
- **Issue:** `test_app_css_served` из `<behavior>` Задачи 2 содержал утверждение «`@font-face` отсутствует пока (проверяется в Задаче 3)». Задача 3 добавляет `@font-face` в тот же файл — два теста стали бы взаимоисключающими.
- **Fix:** Временное утверждение удалено из `test_app_css_served` при добавлении `test_app_css_declares_fonts`. Это предусмотренный планом переход, а не ослабление проверки: наличие `@font-face` теперь проверяется строго.
- **Files modified:** `tests/test_pages/test_shell.py`
- **Verification:** 12 тестов `test_shell.py` зелёные.
- **Committed in:** `d6f3e66`

### Расхождения с буквой критериев приёмки (не автофиксы)

**`grep -c 'href="/groups"' app/templates/base.html` возвращает 0.** Критерий предполагал, что ссылки навигации выписаны в шаблоне литералами. Но соседнее требование того же плана — «навигация выписывается ОДИН раз циклом», и состав меню вынесен в `app/pages/common.py::NAV_ITEMS`. Эквивалентная литеральная проверка теперь `grep -c '"href": "/groups"' app/pages/common.py` → 1 (строка 64). Поведение проверяется строже, чем grep: `test_nav_keeps_groups_and_links` утверждает наличие `href="/groups"` и `href="/dashboard"` в **отрендеренной** выдаче. Запрет «MUST NOT удалять пункт «Группы»» соблюдён.

**Переименование `.worker-pill` → `.session-pill`.** Класс перечислен в `<artifacts_produced>` плана как `.worker-pill`; решение Задачи 1 требует, чтобы имена контракта несли терминологию сессий. Победило решение пользователя. Актуальные CSS-имена: `.session-pill`, `.session-dot`, `.session-dot.is-online`, `.session-label`.

**Добавлены имена, которых не было в плане:** `.brand` / `.brand-mark` / `.brand-name`, `.nav-dot` / `.nav-label` / `.nav-tag` / `.nav-sep`, `.quota-head` / `.quota-plan` / `.quota-label` / `.quota-track` / `.quota-fill` / `.quota-link`, `.user-meta` / `.user-name` / `.user-tz` / `.user-logout`, `.tab-item`, `[data-main]`, `.head-titles` / `.head-title` / `.head-subtitle` / `.head-actions`, токен `--fs-2xl`. Все — следствие требования «инлайн-стили макета в шаблоны не копировать».

---

**Total deviations:** 4 автофикса (1 баг, 3 блокирующих) + 3 задокументированных расхождения с буквой критериев.
**Impact on plan:** Скоупкрипа нет. Все автофиксы обязательны для корректности; расхождения — следствие явных требований самого плана и решения пользователя по Задаче 1.

## Issues Encountered

- **IBM Plex Sans нет в манифесте макета.** План это предусматривал: в манифесте лежат только IBM Plex Mono (15 файлов) и Space Grotesk (3 файла). У Space Grotesk объявлены лишь `latin`, `latin-ext` и `vietnamese` — кириллического файла физически нет, что подтверждает D-17/Pitfall 1. Четыре кириллических и латинских подмножества IBM Plex Sans догружены один раз и закоммичены; внешних шрифтовых запросов в рантайме не осталось (`grep -c 'fonts.googleapis.com' app/static/css/app.css` → 0).
- **Структура `@font-face`.** Проверить, вариативные ли woff2, было нечем (`fontTools` в окружении нет, а новых зависимостей D-02 не допускает). Поэтому структура обеих исходных таблиц перенесена дословно — одно правило на (гарнитура, вес, подмножество), 39 правил на 22 файла. Это гарантированно совпадает с поведением источников истины и не требует догадок.

## Known Stubs

Нет. Все элементы шелла подключены к живым данным: счётчики, квота и индикатор сессий читают `request.state.shell`, наполняемый реальными запросами к БД.

Осознанно неполным остаётся **оформление старых страниц**: `base.html` больше не подключает Tailwind, и старая разметка ссылается на utility-классы, которых нет. Это прямо принятый компромисс D-06, а не заглушка — критерий D-07 требует работоспособности после каждого плана, а не визуальной законченности. Тело `profile.html` мигрирует в Плане 05.

## Threat Flags

Новых поверхностей за пределами `<threat_model>` не появилось. Статус митигаций:

| Threat ID | Статус | Чем закрыт |
|-----------|--------|-----------|
| T-01-01 | mitigated | `StaticFiles` из Starlette (ETag, Range, защита от выхода за каталог), смонтирован **только** `app/static`; своего `FileResponse`-роута нет |
| T-01-02 | mitigated | `/admin` внутри `{% if is_admin %}`; `test_admin_nav_hidden_for_regular_user` + `test_admin_nav_visible_for_admin` |
| T-01-03 | mitigated | Autoescape Jinja2 не отключается нигде в новом шелле; в разметку уходят только текст, числа и булевы |
| T-01-04 | mitigated | Источник — БД; перечисление контейнеров воркеров не вызывается (`grep -c` → 0); при `user is None` — ноль запросов; шесть агрегатов в одном round-trip |
| T-01-05 | mitigated | Версии зафиксированы точно, файлы в git; размеры совпали с ожидаемыми (47 755 Б и 43 441 Б) |
| T-01-06 | accept | Не вносится этой фазой; логика входа не тронута |
| T-01-SC | mitigated | Ни одного `npm install` / нового Python-пакета; всё вендорено файлами |

Отметка для бэклога: 22 woff2 (276 КБ) и два JS (91 КБ) попадают в git как бинарные ассеты. Это осознанное следствие запрета build-шага (D-02).

## User Setup Required

None — внешняя конфигурация не требуется.

## Next Phase Readiness

**Готово к Плану 02 (библиотека компонентов):**
- Токены `:root` и адаптивные примитивы `[data-row]` / `[data-rowhead]` / `[data-grow]` / `[data-hrow]` / `[data-area="meta"]` доступны всем последующим планам.
- Контракт «страница → шелл» определён один раз: `page_title` / `page_subtitle` / `page_actions`. Планам разделов не нужно изобретать свой способ рендера заголовка.
- `auth_base.html` (D-08) **не создан** — это работа Плана 02; сейчас семь auth-страниц по-прежнему переопределяют `{% block body %}`, обходя `{% if user %}`, и работают.

**Открытые пункты, требующие человека (перенесены в end-of-phase проверку, `human_verify_mode: end-of-phase`):**
- Ручная сверка шелла с `design/new_broadcaster_design.unpacked.html`, строки 304-381.
- Нижние табы на ширине <860px и на реальном устройстве — `env(safe-area-inset-bottom)` ведёт себя только на железе.
- Проверка, что длинные русские строки набраны IBM Plex Sans, а не системным фолбэком (human-check Задачи 3).

**Что учесть Фазам 4 и 6:** контракт называется `sessions_online` / `sessions_total`. Настоящий контейнерный показатель, если он понадобится, добавляется **рядом** новым ключом и не переиспользует эти имена.

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
