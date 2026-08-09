---
phase: 01-interfeysnyy-fundament
verified: 2026-08-09T21:20:00Z
status: human_needed
score: 8/9 must-haves verified
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/5
  gaps_closed:
    - "SC-3 — модальные окна: браузерный confirm() удалён из проекта полностью, все 14 мест подтверждения переведены на компонент components/modal.html"
    - "SC-5 — подписи колонок: макрос cell() получил параметр label, 61 вызов с подписью в 9 шаблонах разделов, страховочная сетка наблюдаемо краснеет"
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "billing/balance.html оставляет колонки «Тип» и «Описание» без подписи на 860px"
    addressed_in: "Phase 5"
    evidence: "ROADMAP.md Phase 5 «Тарифы», Success Criterion 4: «Раздел тарифов пригоден к использованию на мобильных ширинах»"
  - truth: "admin/groups_info.html оставляет колонки «Канал» и «Обновлено» без подписи на 860px"
    addressed_in: "Phase 6"
    evidence: "ROADMAP.md Phase 6 «Админ-панель», Success Criterion 5: «все подразделы админ-панели пригодны к использованию на мобильных ширинах»"
  - truth: "app/templates/billing/plans.html не подключён ни к одному маршруту"
    addressed_in: "Phase 5"
    evidence: "ROADMAP.md Phase 5 Requirements: BILL-05, BILL-06, BILL-07 — продление подписки, четыре оси лимитов, история платежей"
  - truth: "Шаблонные глобалы s3_public_url / get_image_url / resolve_image_url вызывают get_settings() в обход подмены зависимостей"
    addressed_in: "Phase 2"
    evidence: "deferred-items.md: отнесено к Фазе 2 (ADS-07, редактор объявления); подтверждено здесь как средовое ограничение тестов, а не дефект рантайма"
behavior_unverified_items:
  - truth: "Модальное окно закрывается по Esc, удерживает фокус внутри панели, возвращает фокус на элемент-триггер и ставит начальный фокус на «Отмена»"
    test: "Открыть /ads, нажать «Удалить» у объявления, нажать Tab несколько раз, затем Esc"
    expected: "При открытии фокус на «Отмена», а не на «Удалить»; Tab не выходит за пределы панели; Esc закрывает окно; фокус возвращается на кнопку, которая окно открыла"
    why_human: "Инвариант целиком в рантайме Alpine (x-on:keydown.escape.window, trap() через $refs.panel). Разметка, обработчики и x-ref присутствуют и подключены, но в проекте нет инфраструктуры исполнения JS — grep -rn 'playwright|selenium|pyppeteer|jsdom' по tests/ и pyproject.toml пуст. Проверка присутствия символов порядок фокуса увидеть не может"
human_verification:
  - test: "Открыть /ads, нажать «Удалить» у объявления, Tab несколько раз, затем Esc"
    expected: "Начальный фокус на «Отмена», фокус заперт в панели, Esc закрывает, фокус возвращается на кнопку-триггер"
    why_human: "Рантайм Alpine; в проекте нет теста, исполняющего JS"
  - test: "Открыть /accounts, /ads, /schedules, /groups, /dashboard, /admin/users при ширине окна 375px"
    expected: "Строки перестраиваются в карточки, шапка колонок исчезает, вместо неё у каждого значения появляется подпись колонки, сайдбар сменяется нижними табами"
    why_human: "Визуальный рендеринг медиазапросов; правила CSS и атрибуты разметки проверены, фактическая отрисовка — нет. Совпадает с пунктом покрытия D8"
  - test: "Открыть /billing и /admin/groups-info при ширине 375px и оценить, понятно ли назначение колонок «Тип», «Описание», «Канал», «Обновлено»"
    expected: "Значения этих колонок (бейдж типа операции, свободный текст описания, бейдж канала, дата) читаются без подписи; если нет — подписи дописываются в Фазе 5 и Фазе 6 соответственно"
    why_human: "Наблюдение T-13-09, переданное Планом 13 явным запретом записывать его как принятую базовую линию. Суждение о самоочевидности значения визуальное"
  - test: "Пройти мастер подключения WhatsApp и MAX до появления QR-кода и дождаться смены статуса"
    expected: "Блок #wa-status / #max-status обновляется на месте без перезагрузки страницы, оформление совпадает с переверстанными мастерами"
    why_human: "GET /accounts/connect/wa/status и /accounts/connect/max/status требуют живых WA Bridge и MAX worker; HTTP-покрытия у них нет"
  - test: "Просмотреть /login, /register, /forgot-password и внутренние страницы на предмет соответствия макету new_broadcaster_design.html"
    expected: "Единый визуальный язык, тёмная тема, кириллица в основной гарнитуре без системного фолбэка"
    why_human: "Визуальное соответствие макету программно не проверяется"
  - test: "Закрыть два BLOCKER'а из 01-REVIEW.md (CR-01 — отсутствие проверки владения ad_id/account_id в расписаниях; CR-02 — доверие клиентскому Content-Type при загрузке, хранение и открытие image/svg+xml)"
    expected: "Решение разработчика: чинить в этой фазе, вынести в отдельную задачу или в Фазу 2"
    why_human: "Гейт код-ревью открыт (status: issues_found, critical: 2). Цели этой фазы не блокирует, но ship — блокирует"
---

# Phase 1: Интерфейсный фундамент — Verification Report

**Phase Goal:** Всё приложение отрисовывается через новый шелл и единую дизайн-систему из макета, а последующие фазы получают готовый набор переиспользуемых компонентов и адаптивных примитивов.
**Verified:** 2026-08-09T21:20:00Z
**Status:** human_needed
**Re-verification:** Yes — после закрытия пробелов планами 01-09 … 01-13

## Goal Achievement

### Observable Truths

Первые пять — Success Criteria из ROADMAP.md (контракт). Пункты 6-9 добавлены из
`must_haves.truths` планов 01-02, 01-03, 01-06, 01-11, 01-12 и объём не сужают.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Каждая существующая страница открывается в новом шелле `base.html` — ни одна не осталась на старом layout'е | ✓ VERIFIED | 58 шаблонов, 29 наследуют шелл (`22 × extends "base.html"`, `7 × extends "auth_base.html"`), остальные 29 — компоненты (13), макросы строк (5), HTMX-партиалы (7), два шелла, `includes/messenger_icon.html`, `accounts/partials/connect_status.html`. Все 36 целей `TemplateResponse` из `app/pages/` и `app/routes/` сопоставлены. `auth_base.html:23` тянет тот же `app.css` — auth-экраны на тех же токенах (D-08). **Проба WR-02 выполнена лично:** `/ads/new` и `/ads/{id}/edit` — единственные страницы без покрытия в суите — отдают 200 и содержат `data-shell`, `data-nav`, `data-head`, `is-active`; 500 воспроизводится ТОЛЬКО при пустом окружении (`ValidationError: database_url, secret_key`), в рантайме с переменными окружения страница рендерится |
| 2 | Пользователь на любой странице видит единую навигацию, текущий раздел подсвечен | ✓ VERIFIED | `NAV_ITEMS` объявлен один раз в `app/pages/common.py`, обходится циклом и в `data-nav` (`base.html:34-46`), и в `data-tabs` (`base.html:83-88`). 30 обработчиков в 9 модулях `app/pages/` передают `active_page`, покрывая все ключи (`ads`, `accounts`, `groups`, `schedules`, `history`, `billing`, `dashboard`, `profile`, `admin`). Сайдбар ставит `is-active` + `aria-current`, табы — только `aria-current`, поэтому счёт `is-active == 1` устойчив. Переходы остались `<a href>` — запрет Плана 01 на кнопки с JS соблюдён. `tests/test_pages/test_shell.py` + `test_htmx_preserved.py`: 94 passed |
| 3 | Кнопки, поля, таблицы, карточки, бейджи, **модальные окна** и пустые состояния выглядят одинаково во всех разделах | ✓ VERIFIED (пробел закрыт) | `grep -rn 'confirm(' app/templates` → **0 совпадений**. Единственный оставшийся инлайн-обработчик отправки — `accounts/connect_max.html:34`, защита от двойной отправки, не диалог. 14 точек `modal-open-*` в 8 шаблонах на одном механизме: accounts/list 3, accounts/partial_cards 3, accounts/partials/sync_status_card 3, groups/includes/group_row 1, groups/list 1 (массовое), schedules/includes/schedule_row 1, ads/includes/ad_card 1, admin/user_detail 1. `components/modal.html` — настоящий диалог: `role="dialog"`, `aria-modal`, `aria-labelledby`, ловушка фокуса по `$refs.panel`, Esc, клик по оверлею, начальный фокус на «Отмена», внутри — реальная `<form method action>`. Подключение компонентов: button 32 файла, card 20, badge 19, table 19, field 18, mono 15, alert 12, empty_state 11, modal 7, filters 5, toggle 5. Сырых `<table>/<tr>/<td>` — 0 |
| 4 | Как минимум одно взаимодействие обновляет интерфейс на месте через HTMX/Alpine | ✓ VERIFIED | 13 сентинелов `hx-trigger="revealed"` в 6 разделах; опрос статуса синхронизации `every 5s` + `hx-swap="outerHTML"` на `#account-row-{id}`; опрос подключения WA/MAX `every 3s` на `#wa-status` / `#max-status`. Поведенческие, а не присутствие атрибутов: `test_infinite_scroll_chain` (сентинел второй страницы несёт больший offset), `test_infinite_scroll_keeps_filters`, `test_sync_polling_stops`, `test_sync_polling_continues_while_syncing`, `test_swap_anchors_present`, `test_partial_without_layout_param_ok` — все зелёные |
| 5 | Каждая переведённая страница пригодна на мобильных ширинах: табличные данные переключаются на карточное представление | ✓ VERIFIED (пробел закрыт) | Механизм: `app.css:479-487` на 860px переводит `[data-row]` в flex-wrap-карточку, `[data-grow]` в полную ширину, скрывает `[data-rowhead]`; `app.css:1143-1149` ровно там же проявляет `[data-cell-label]`; `[data-hrow]` перестраивается в одну колонку на 1080px. Примитив подписи теперь В БИБЛИОТЕКЕ: `components/table.html:44,46` — параметр `label` макроса `cell`. 61 вызов `cell(… label=…)` в 9 шаблонах разделов (было 3). Из 9 шаблонов с `rowhead` семь подписаны полностью, два — частично (см. Deferred). **Наблюдаемое покраснение проверено лично** — см. Behavioral Spot-Checks |
| 6 | Удаление остаётся возможным при недоступном Alpine: форма отправляется на прежний маршрут прежним методом | ✓ VERIFIED | 12 из 13 подтверждений одной сущности обёрнуты в реальную `<form method="POST" action="/…/delete">` с `x-on:submit.prevent` — без Alpine `prevent` не срабатывает и форма уходит обычным POST. Проверено HTTP-тестами на отрендеренной странице, а не грепом исходника: `test_groups_delete_form_degrades_without_alpine`, `test_schedules_delete_form_degrades_without_alpine`, `test_ads_delete_form_degrades_without_alpine`, `test_admin_user_delete_form_degrades_without_alpine`. Исключение — массовое удаление групп (WR-04), которое и до фазы было целиком на JS: регрессии нет |
| 7 | Массовое удаление подтверждает ровно тот набор групп, который будет удалён | ✓ VERIFIED | `groups/list.html:111-133`: `.group-checkbox:checked` читается РОВНО один раз, набор материализуется скрытыми полями внутри формы самой панели и счётчик пишется из того же массива — всё ДО `$dispatch`. Код прямолинейный и синхронный, поэтому чтение исходника здесь и есть чтение поведения. Порядок закреплён `test_groups_bulk_modal_confirms_exact_set` (индексы `read < ids_written < dispatch`). Независимо прослежено код-ревью: «no TOCTOU or set-mismatch bug»; внедряемые поля не несут класс `.group-checkbox` и не могут вернуться в выборку |
| 8 | Самоостанавливающийся опрос статуса синхронизации цел | ✓ VERIFIED | `accounts/partials/sync_status_card.html:46` — `hx-get`/`hx-trigger`/`hx-swap` стоят ВНУТРИ `{% if status == 'syncing' %}`, поэтому ответ с иным статусом приходит без атрибутов и опрос гаснет сам. Подтверждено поведением: `test_sync_polling_stops` и `test_sync_polling_continues_while_syncing` зелёные. Якорь `#account-row-{id}` и запрос стоят на одном элементе; панель подтверждения — СОСЕДНИЙ элемент (`accounts/list.html:134`), поэтому `outerHTML`-подмена строки её не уносит |
| 9 | Модальное окно закрывается по Esc, удерживает фокус внутри панели, возвращает фокус на триггер, начальный фокус на «Отмена» | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Разметка и обработчики присутствуют и подключены (`modal.html:54-62`: `show()` запоминает `document.activeElement` и через `$nextTick` фокусирует `$refs.cancel`; `hide()` возвращает фокус; `trap()` фильтрует по `offsetParent !== null`). Но это инвариант ПОРЯДКА фокуса в рантайме, а не присутствие символа. Инфраструктуры исполнения JS в проекте нет: `grep -rn 'playwright\|selenium\|pyppeteer\|jsdom' tests/ pyproject.toml` пуст. Ни один тест этот порядок не исполняет → человеку |

**Score:** 8/9 truths verified (1 present, behavior-unverified)

### Deferred Items

Не пробелы: явно закреплены за более поздними фазами этой вехи.

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | `billing/balance.html`: «Тип» и «Описание» без подписи на 860px | Phase 5 | ROADMAP Phase 5 SC-4: «Раздел тарифов пригоден к использованию на мобильных ширинах» |
| 2 | `admin/groups_info.html`: «Канал» и «Обновлено» без подписи на 860px | Phase 6 | ROADMAP Phase 6 SC-5: «все подразделы админ-панели пригодны к использованию на мобильных ширинах» |
| 3 | `billing/plans.html` без маршрута | Phase 5 | ROADMAP Phase 5 Requirements: BILL-05, BILL-06, BILL-07 |
| 4 | Шаблонные глобалы в обход `dependency_overrides` | Phase 2 | `deferred-items.md`, ADS-07 |

**Почему это отсрочка, а не принятая базовая линия** (запрет Плана 01-13 соблюдён): в обоих шаблонах подписаны ровно те колонки, где значение без подписи бессмысленно, — числовые (`Кол-во`, `Баланс`, `Участников`, `Админов`). Без подписи остались бейдж типа операции, бейдж канала, дата и свободный текст описания, то есть самоописывающиеся значения. Ровно тот отказ, который зафиксировала прошлая верификация — «12 · 3 · 87% · 09.08 14:22 · —» без единой подписи — устранён везде. Остаток передан поимённо (T-13-09) и продублирован пунктом человеческой проверки.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `app/static/css/app.css` | Токены `:root`, стили шелла, медиазапросы | ✓ VERIFIED | 1149 строк, 53 токена в `:root`, медиазапросы 1080/900/860 + `prefers-reduced-motion` |
| `app/templates/base.html` | Новый шелл: `data-shell`/`data-nav`/`data-tabs`/`data-head` | ✓ VERIFIED | 128 строк, все примитивы на месте, `is-active` + `aria-current` |
| `app/templates/auth_base.html` | Auth-шелл без сайдбара на тех же токенах | ✓ VERIFIED | 40 строк, тот же `app.css`, наследуют 7 экранов |
| `app/pages/common.py` | `get_shell_context`, `NAV_ITEMS`, `asset_version` | ✓ VERIFIED | 249 строк, единственный источник навигации |
| `app/templates/components/*.html` (13) | Библиотека макросов | ✓ VERIFIED | Все 13 подключены минимум из одного шаблона; ни `\|safe`, ни `autoescape false`, ни `Markup(` |
| `app/templates/components/modal.html` | Диалог с ловушкой фокуса и Esc | ✓ VERIFIED | 77 строк, реальная форма, слот `caller()`, 7 потребителей, 14 точек вызова |
| `app/templates/components/table.html` | `rowhead` / `row_open` / `cell(label=…)` | ✓ VERIFIED | 49 строк, `label` — последний параметр (позиционные вызовы не сдвинулись), эмитит `<span data-cell-label>` |
| `app/static/js/htmx.min.js`, `alpine.min.js` | Вендоренные библиотеки (D-05) | ✓ VERIFIED | 47 755 и 43 441 байт; в шаблонах ноль внешних `https://` |
| `tests/test_pages/test_responsive_markup.py` | Страховочные сетки SC-3 и SC-5 | ✓ VERIFIED | 3075 строк; сетки наблюдаемо краснеют (см. ниже) |
| `tests/test_templates/test_components.py` | Контракт панели подтверждения и инвентаризации исключений | ✓ VERIFIED | 896 строк |
| `app/templates/billing/plans.html` | Раздел тарифов | ⚠️ ORPHANED | Ни один роут не рендерит; отнесено к Фазе 5 |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `base.html` | `app/static/css/app.css` | `url_for('static', …)?v={{ asset_version }}` | ✓ WIRED | `base.html:11`, `auth_base.html:23` |
| `app/pages/*.py` | `base.html` | `active_page` в контексте | ✓ WIRED | 30 передач, 9 ключей |
| `components/table.html` | `app.css` | атрибут `data-cell-label` | ✓ WIRED | Правило `app.css:1133` + `1143-1149` селектирует ровно эмитируемый атрибут |
| `accounts/list.html` | `components/modal.html` | `modal-open-acc-del-{id}` | ✓ WIRED | Панель — сосед строки, не её потомок: `outerHTML`-подмена строки её не уносит |
| `accounts/partials/sync_status_card.html` | `accounts/list.html` | тот же `modal-open-acc-del-{id}` | ✓ WIRED | Блок подмены сам панель не рендерит (одна панель на аккаунт, дублей с общим id нет), но диспатчит то же событие |
| `groups/list.html` | `components/modal.html` | слот `caller()` для скрытых полей набора | ✓ WIRED | Блочный вызов `{% call modal(...) %}`, поля внутри формы панели |
| `groups/includes/group_row.html` | `groups/partial_cards.html` | один макрос строки | ✓ WIRED | Правка макроса закрывает и список, и порцию прокрутки |
| `app/main.py` | `app/static/` | `app.mount(..., StaticFiles(...))` | ✓ WIRED | Каталог существует, оба JS-файла на месте |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `accounts/list.html` | `accounts`, `account_stats` | `app/pages/accounts.py` — репозиторий | Да | ✓ FLOWING |
| `base.html` (счётчики, квота, воркеры) | `request.state.shell` | `get_shell_context(db, user)` | Да | ✓ FLOWING |
| `billing/balance.html` | `transactions` | `app/pages/billing.py` | Да (тест засевает и утверждает отрисовку строки) | ✓ FLOWING |
| `dashboard.html` | `recent_sends` | `app/pages/dashboard.py` | Да | ✓ FLOWING |
| `billing/plans.html` | — | нет роута | Нет | ✗ DISCONNECTED (deferred → Phase 5) |

### Behavioral Spot-Checks

Ключевое: обе страховочные сетки проверены на ИСКУССТВЕННО внесённом нарушении в
одноразовом worktree, а не приняты на слово SUMMARY.

| Behavior | Command | Result | Status |
|---|---|---|---|
| Полная суита в чистом окружении | `git worktree add --detach /tmp/verify-wt HEAD && pytest tests/ -q` | `646 passed in 311s` | ✓ PASS |
| Сетка SC-5 краснеет на снятой подписи | Удалён один `label=` в `schedules/includes/schedule_row.html` → `pytest -k "cell_label or rowhead_titles or schedules_cell_labels"` | `2 failed, 18 passed` (`test_schedules_cell_labels_present`, `test_rowhead_titles_are_covered_by_labels[schedules/list.html]`) | ✓ PASS |
| Сетка SC-5 краснеет на новом шаблоне с шапкой и без подписей | Добавлен синтетический `synthetic_probe.html` с `rowhead` без `label=` | `test_every_rowhead_template_has_cell_labels` и `test_rowhead_pages_all_have_a_parametrization_entry` FAILED | ✓ PASS |
| Сетка SC-3 краснеет на возвращённом `confirm()` | Заменён `x-on:submit.prevent="$dispatch(...)"` на `onsubmit="return confirm(…)"` в `group_row.html` | **6 тестов FAILED** независимо друг от друга: `test_groups_delete_uses_modal`, `test_groups_bulk_delete_uses_modal`, `test_no_rendered_page_calls_browser_dialog`, `test_no_template_calls_browser_dialog`, `test_only_known_non_dialog_submit_handlers_remain`, `test_modal_site_inventory` | ✓ PASS |
| `/ads/new` рендерится в шелле (WR-02) | Проба `authed_client.get("/ads/new")` c `DATABASE_URL`/`SECRET_KEY` в окружении | 200; `data-shell`, `data-nav`, `data-head`, `is-active` присутствуют; `confirm(` отсутствует | ✓ PASS |
| `/ads/{id}/edit` рендерится в шелле | Та же проба с засеянным объявлением | 200; `data-shell`, `is-active` присутствуют | ✓ PASS |
| `/ads/new` при ПУСТОМ окружении | Та же проба без переменных окружения | 500 — `ValidationError: database_url, secret_key` в `get_settings()` из `common.py:38` | ℹ️ Средовое, не дефект вёрстки (deferred → Phase 2) |
| Рантайм модалки (Esc/фокус) | — | Инфраструктуры исполнения JS в проекте нет | ? SKIP → человеку |

Worktrees `/tmp/verify-wt` и `/tmp/verify-wt2` удалены, рабочее дерево не изменялось
(`git worktree list` → только `/source/broadcaster`).

### Probe Execution

Конвенциональных `scripts/*/tests/probe-*.sh` в проекте нет, и ни один PLAN/SUMMARY
фазы probe-скриптов не объявляет. Роль проб выполняют pytest-тесты выше.

| Probe | Command | Result | Status |
|---|---|---|---|
| — | — | — | N/A (проб не объявлено) |

### Requirements Coverage

Объединение `requirements:` по всем 13 планам = {UI-01 … UI-06}. REQUIREMENTS.md
относит к Phase 1 ровно UI-01 … UI-06. **Осиротевших требований нет.**

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| UI-01 | 01, 02, 08 | Единый набор дизайн-токенов из макета | ✓ SATISFIED | `app.css:22` — 53 токена в `:root`; ноль внешних CDN; шрифты вендорены |
| UI-02 | 01, 02, 08, 10 | Все страницы через новый шелл `base.html` | ✓ SATISFIED | 29 шаблонов наследуют шелл; 36 целей `TemplateResponse` сопоставлены; `/ads/new` и `/ads/{id}/edit` проверены пробой |
| UI-03 | 01, 08 | Единая навигация с подсветкой активного раздела | ✓ SATISFIED | `NAV_ITEMS` в одном месте; `is-active` + `aria-current`; 30 передач `active_page` |
| UI-04 | 02-13 | Общие элементы в переиспользуемых Jinja2-компонентах | ✓ SATISFIED | 13 компонентов; модалка закрыта планами 11-13; сырых `<table>` — 0 |
| UI-05 | 03-06, 08 | Точечные обновления через HTMX/Alpine | ✓ SATISFIED | 13 сентинелов прокрутки, самоостанавливающийся опрос, 6 поведенческих тестов |
| UI-06 | 01-09, 11-13 | Адаптивные примитивы, применяемые во всех разделах | ✓ SATISFIED | `data-row`/`data-hrow`/`data-grow`/`data-rowhead`/`data-cell-label` в CSS и в 9 шаблонах разделов; частичное покрытие подписями в 2 шаблонах отнесено к Фазам 5 и 6 |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` | — | **Ноль совпадений** по `app/templates`, `app/static/css`, `app/pages`, `app/routes/uploads.py`, `tests/test_pages`, `tests/test_templates` |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | — | Ноль совпадений |
| — | — | «заглушка» / «coming soon» / «not implemented» | — | Ноль совпадений |
| `app/pages/schedules.py` | CR-01 | Нет проверки владения `ad_id` / `account_id` | ⚠️ WARNING для цели фазы, 🛑 для ship | Межарендная утечка объявления и списание с баланса жертвы. Цель фазы (шелл + дизайн-система) не блокирует, гейт код-ревью — блокирует |
| `app/routes/uploads.py` | CR-02 | Клиентский `Content-Type` не проверяется, `image/svg+xml` сохраняется и открывается по `<a target="_blank">` | ⚠️ WARNING для цели фазы, 🛑 для ship | Незакрытый вектор инъекции; тот же вывод |
| `app/templates/groups/list.html` | 58-59 | Массовое действие без деградации без JS (WR-04) | ℹ️ INFO | Не регрессия: путь и до фазы был целиком на JS |
| `app/pages/common.py` | 36-38 | Глобалы шаблонов в обход внедрения зависимостей (WR-02) | ⚠️ WARNING | `ads/form.html` не покрыт HTTP-сметом; страница проверена пробой вручную. Отнесено к Фазе 2 |

### Human Verification Required

#### 1. Рантайм модального окна

**Test:** Открыть `/ads`, нажать «Удалить» у объявления, нажать Tab несколько раз, затем Esc.
**Expected:** При открытии фокус на «Отмена», а не на «Удалить»; Tab не выходит за пределы панели; Esc закрывает окно; фокус возвращается на кнопку-триггер.
**Why human:** Инвариант порядка фокуса живёт целиком в рантайме Alpine. В проекте нет ни playwright, ни selenium, ни jsdom — ни один тест не исполняет JS.

#### 2. Карточное представление на 375px

**Test:** Открыть `/accounts`, `/ads`, `/schedules`, `/groups`, `/dashboard`, `/admin/users` при ширине окна 375px.
**Expected:** Строки перестраиваются в карточки, шапка колонок исчезает, у каждого значения появляется подпись колонки, сайдбар сменяется нижними табами.
**Why human:** Визуальная отрисовка медиазапросов. Правила CSS и атрибуты разметки проверены, фактический рендеринг — нет (пункт покрытия D8).

#### 3. Самоочевидность неподписанных колонок (T-13-09)

**Test:** Открыть `/billing` и `/admin/groups-info` при ширине 375px.
**Expected:** Значения колонок «Тип», «Описание», «Канал», «Обновлено» читаются без подписи (бейдж, свободный текст, бейдж, дата). Если нет — подписи дописываются в Фазе 5 и Фазе 6.
**Why human:** Суждение о самоочевидности визуальное. План 13 явно запретил записывать это как принятую базовую линию.

#### 4. Мастера подключения WhatsApp и MAX

**Test:** Пройти мастер до появления QR-кода и дождаться смены статуса.
**Expected:** Блок `#wa-status` / `#max-status` обновляется на месте без перезагрузки.
**Why human:** Требует живых WA Bridge и MAX worker; HTTP-покрытия нет.

#### 5. Соответствие макету

**Test:** Просмотреть `/login`, `/register`, `/forgot-password` и внутренние страницы против `new_broadcaster_design.html`.
**Expected:** Единый визуальный язык, тёмная тема, кириллица в основной гарнитуре без системного фолбэка.
**Why human:** Визуальное соответствие программно не проверяется.

#### 6. Решение по двум BLOCKER'ам код-ревью

**Test:** Прочитать CR-01 и CR-02 в `01-REVIEW.md` и решить: чинить здесь, вынести в отдельную задачу или в Фазу 2.
**Expected:** Явное решение разработчика.
**Why human:** Гейт код-ревью открыт (`status: issues_found`, `critical: 2`). Цель фазы не блокирует, ship — блокирует.

### Gaps Summary

**Пробелов нет.** Оба пробела прошлой верификации закрыты и закрытие подтверждено
не пересказом SUMMARY, а наблюдением:

- **SC-3 закрыт.** Браузерный `confirm()` исчез из `app/templates/` полностью (0 совпадений).
  Все 14 мест подтверждения удаления работают через один компонент `components/modal.html`.
  Компонент настоящий: `role="dialog"`, `aria-modal`, ловушка фокуса, Esc, начальный фокус на
  отказе, внутри — реальная форма с прежним маршрутом и методом, поэтому без Alpine страница
  деградирует до обычного POST (проверено HTTP-тестами на 4 разделах). Сетка не декоративная:
  возвращённый вручную `confirm()` уронил **шесть независимых тестов**.
- **SC-5 закрыт.** Примитив подписи переехал в библиотеку (`cell(label=…)`), 61 подписанный
  вызов в 9 шаблонах разделов против 3 шаблонов раньше. Медиазапрос 860px, скрывающий шапку
  колонок, и правило, проявляющее подпись, — один и тот же брейкпоинт. Сетка краснеет и на
  снятой подписи в существующем шаблоне, и на новом шаблоне с шапкой без подписей.

**Открытые вопросы, требующие человека, а не доработки:** рантайм фокуса модалки и
визуальная проверка на 375px принципиально недостижимы для этого окружения — браузера нет,
инфраструктуры исполнения JS в проекте нет. Это единственная причина статуса `human_needed`,
а не `passed`.

**Отдельно, вне границ цели фазы:** гейт код-ревью открыт с двумя BLOCKER'ами
(CR-01, CR-02). Они не мешают приложению отрисовываться через новый шелл и дизайн-систему,
поэтому цель фазы считается достигнутой, но перед ship их придётся закрыть или явно отложить.

---

_Verified: 2026-08-09T21:20:00Z_
_Verifier: Claude (gsd-verifier)_
