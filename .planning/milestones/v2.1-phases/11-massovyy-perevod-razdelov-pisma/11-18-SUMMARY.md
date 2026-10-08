---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 18
subsystem: ui
tags: [htmx, fastapi, jinja2, form_wrapper, respond_field_error, max, accounts]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "respond_field_error и правило 422 со свопом (11-08, 11-09), пустой 400 на отказ валидации фреймворка (11-07), пустой реестр HX-Retarget/HX-Reswap (11-10), реестр пар транспортов (11-01…11-17)"
provides:
  - "accounts/includes/max_connect_step.html — единственный источник разметки шага мастера MAX для страницы, фрагмента успеха и фрагмента 422"
  - "accounts_connect_max_start на слое ответа: htmx — содержимое #max-connect-step, без htmx — 302 /accounts, нет сессии — переход на /login"
  - "второй авторский 422 вехи: телефон из пробелов на обоих транспортах с эхом присланного значения"
  - "_max_step_markup(step, qr_code, error, phone) — сборка шага окружением шаблонов"
  - "NOT_YET_CONVERTED_COUNT = 14: остаток ровно предмет Фаз 13 и 14"
affects: [11-19, 11-20, phase-13-qr-wizard, phase-14-auth]

actuals:
  tokens: 13365   # chars/4 по git diff e6884a8..HEAD (53460 символов)
  tasks: 2
  commits: 3
plan_head_before: e6884a83f4d8dacedc2c6549b523eb05594a844c

tech-stack:
  added: []
  patterns:
    - "Постоянный контейнер шага — сама flex-колонка страницы, если в подменяемое содержимое обязан входить узел вне карточки"
    - "Эхо свободного текста в 422 доказывается на той же сборке тела, что собирает фрагмент, когда HTTP-путь до ветки враждебного значения не доводит"

key-files:
  created:
    - app/templates/accounts/includes/max_connect_step.html
    - tests/test_pages/test_max_connect_transport.py
  modified:
    - app/pages/accounts.py
    - app/templates/accounts/connect_max.html
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_htmx_preserved.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_components.py
    - tests/test_templates/test_htmx_inventory.py
    - tests/test_templates/test_htmx_markup_security.py

key-decisions:
  - "id max-connect-step стоит на самой колонке .connect-shell, а не на обёртке внутри карточки: алерт ошибки в дереве стоит ВНЕ карточки, а в подменяемое содержимое он входить обязан; обёртка внутри карточки перенесла бы алерт в тело карточки, отдельная обёртка сняла бы flex-промежуток 14px"
  - "Адрес деградации успеха — /accounts, проверено по коду: connecting → syncing переводит только опрос accounts_connect_max_status, GET /accounts/connect/max удаляет аккаунты connecting, /accounts показывает аккаунты любого статуса (запрос без фильтра статуса)"
  - "Экранирование эха доказано на _max_step_markup с враждебным значением: значение из одних пробелов не может нести разметку, поэтому HTTP-путём враждебное значение до 422 не доезжает; отдельное правило утверждает, что непустое враждебное значение не попадает в ответ старта"
  - "Отсутствующее поле phone идёт той же веткой 422, а не пустым 400 фреймворка: обработчик читает форму сам, поля в сигнатуре нет — поведение прежнее, авторский 422 на другие классы валидации не расширен"
  - "Класс раскладки connect-step__form переехал с тега формы на внутренний узел — приём includes/profile_settings.html"

patterns-established:
  - "Пятисекундное ожидание моста подменяется в тестах точечно (только delay == 5), и запрос этого ожидания утверждается — продовый sleep не снят"

requirements-completed: [FORM-08, FORM-03]

coverage:
  - id: D1
    description: "Шаг мастера MAX во включаемом шаблоне; вынос не изменил страницу (пять ветвей отрисовки совпали с прежними с точностью до пробелов)"
    requirement: "FORM-03"
    verification:
      - kind: automated_ui
        ref: "uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_htmx_preserved.py tests/test_templates/ -q (после задачи 1)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Старт MAX на htmx — 200 и содержимое #max-connect-step (QR с узлом опроса либо ошибка моста), без <!DOCTYPE; пятисекундное ожидание запрашивается"
    requirement: "FORM-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_max_start_over_htmx_returns_the_step_container"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[старт подключения MAX — успех / нет сессии]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Телефон из пробелов — 422 на обоих транспортах с текстом «Введите номер телефона» и эхом значения; цель 422 = цель успеха"
    requirement: "FORM-08"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_an_empty_phone_answers_422_with_the_echo_on_both_transports"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_max_connect_transport.py#test_the_phone_echo_is_autoescaped_in_the_step_markup"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_a_hostile_phone_never_reaches_the_response_raw"
        status: pass
    human_judgment: false
  - id: D4
    description: "Без htmx успешный старт — 302 /accounts, аккаунт connecting виден на экране приземления и не удалён"
    requirement: "FORM-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_max_connect_transport.py#test_max_start_without_htmx_lands_on_the_accounts_list"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере: индикатор и блокировка кнопки видны ~5 с, затем QR без перезагрузки и опрос статуса раз в 3 с; номер из пробелов (required снят в DevTools) перерисовывает шаг с ошибкой и значением, плашки аварии нет"
    verification: []
    human_judgment: true
    rationale: "Ручной UAT фазы, пункт 5 (accounts): видимость индикатора, блокировка и живой опрос в браузере автоматикой не утверждаются"

duration: 80min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 18: Мастер MAX — фрагмент шага и второй авторский 422 Summary

**Старт подключения MAX отвечает на htmx содержимым постоянного контейнера `#max-connect-step` из одного включаемого шаблона, без htmx приземляет 302 на `/accounts`, а телефон из пробелов отвечает 422 на обоих транспортах с эхом значения через автоэкранирование поля; `NOT_YET_CONVERTED_COUNT` 15 → 14.**

## Performance

- **Duration:** 80 min
- **Started:** 2026-09-17T03:10:44Z
- **Completed:** 2026-09-17T04:30:58Z
- **Tasks:** 2
- **Files modified:** 13 (2 созданы, 11 изменены)

## Accomplishments

- Шаг мастера MAX (алерт ошибки + карточка со всеми ветками) вынесен в `accounts/includes/max_connect_step.html`. До и после выноса я снял отрисовку пяти ветвей (шаг телефона GET, QR с картинкой, QR без картинки, отказ моста, пустой телефон). Все пять совпали по токенам, различие только в пробелах.
- `accounts_connect_max_start` переведён на слой ответа. Нет сессии → `respond(redirect="/login")`. Пустой телефон → `respond_field_error(page=…, fragment=…)`. Финальный выход → `respond(redirect="/accounts", fragment=_step)`. `RedirectResponse` в обработчике 0. `asyncio.sleep(5)` на месте.
- Форма телефона переведена на `form_wrapper(target='#max-connect-step', swap='innerHTML')`, встроенный обработчик отправки снят. Во всём дереве шаблонов встроенных обработчиков отправки больше нет, и перечень `KNOWN_SUBMIT_HANDLER_FILES` пуст.
- Литерал `status_code=422` в `app/*.py` по-прежнему один: `app/pages/htmx.py`. `SERVER_SIDE_VALIDATION_RESPONSES` не двигался, `test_htmx_response_contract.py` зелёный. Реестр `HX-Retarget`/`HX-Reswap` пуст, потому что цель 422 совпадает с целью успеха.
- Остаток `NOT_YET_CONVERTED` — 14 ключей. Список снят обходом `_backlog(_pages_sources())`, а не взят из числа:
  - `app/pages/accounts.py`: `accounts_connect_tg_user_complete`, `accounts_connect_tg_user_refresh_qr`, `accounts_connect_tg_user_start_qr`, `accounts_connect_tg_user_verify_2fa` (Фаза 13);
  - `app/pages/auth.py`: `forgot_password_resend_code`, `forgot_password_reset`, `forgot_password_send_code`, `forgot_password_verify`, `login_submit`, `register_complete`, `register_resend_code`, `register_send_code`, `register_verify`, `stop_impersonation` (Фаза 14).

## Task Commits

1. **Задача 1: шаг мастера MAX во включаемом шаблоне** — `2c25159` (refactor)
2. **Задача 2 RED: транспорт старта MAX** — `49e1379` (test)
3. **Задача 2 GREEN: фрагмент шага и второй авторский 422** — `7ef10a0` (feat)

REFACTOR-коммита у задачи 2 нет: после GREEN чистить было нечего.

## TDD Gate Compliance

- **RED** `49e1379`. Команда: `uv run pytest tests/test_pages/test_max_connect_transport.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py -p no:cacheprovider -q --junitxml=…`, rc=1, 97 тестов, 7 падений. Проверил четыре целевых теста через `check tdd-red-evidence`, у всех `RED_EVIDENCE_OK`:
  - `test_max_start_over_htmx_returns_the_step_container`: «слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ».
  - `test_an_empty_phone_answers_422_with_the_echo_on_both_transports`: `assert 200 == 422`.
  - `test_the_phone_echo_is_autoescaped_in_the_step_markup`: «у модуля аккаунтов нет сборки шага мастера MAX».
  - `test_max_start_without_htmx_lands_on_the_accounts_list`: `assert 200 == 302`.

  Ещё три падения: две пары MAX («путь деградации ответил 200 вместо 302» и «ЦЕЛЫЙ ДОКУМЕНТ») и реестр пар `43 == 41`.

  Причины в дереве: `RedirectResponse` на `accounts.py:550`, `TemplateResponse` со статусом 200 на пустом телефоне (`:556`), полностраничный `TemplateResponse` на `:608`.

  Первый прогон дал на тесте экранирования `ImportError`, а это INVALID_RED. Я превратил отсутствие сборки в утверждение (`getattr` + `assert`) и перезапустил. Номер 7/97 выше — из второго прогона.

  `test_a_hostile_phone_never_reaches_the_response_raw` зелёный и на RED. Это ожидаемо: он стережёт свойство, которое уже было верно до перевода, а не новое поведение.
- **GREEN** `7ef10a0`. После перевода `test_max_connect_transport.py` зелёный: 5 тестов, включая все 4 целевых.
- Коммит `refactor(11-18)` предшествует `test(11-18)`, потому что это задача 1 (не TDD, чистый вынос). Порядок RED → GREEN у задачи 2 не нарушен.

## Files Created/Modified

- `app/templates/accounts/includes/max_connect_step.html` — единственный источник разметки шага. Форма телефона на `form_wrapper`, поле `phone` с `value=phone or ''`.
- `app/templates/accounts/connect_max.html` — `<div class="connect-shell" id="max-connect-step">` и `include`.
- `app/pages/accounts.py` — `MAX_CONNECT_STEP_TEMPLATE`, `MAX_EMPTY_PHONE_ERROR`, `_max_step_markup`, перевод `accounts_connect_max_start` с докстрингом (адрес деградации и его основание).
- `tests/test_pages/test_max_connect_transport.py` — 5 тестов. Подмена `max_bridge` глушит только ожидание в 5 с и записывает задержки.
- `tests/test_pages/test_htmx_post_pairs.py` — посев и два случая MAX, 41 → 43.
- `tests/test_pages/test_htmx_gates.py` — ключ снят из `NOT_YET_CONVERTED` (15 → 14, сводная летопись фазы словами) и добавлен во `FRAGMENT_RESPONSE_HANDLERS` (11 → 12).
- `tests/test_templates/test_htmx_markup_gates.py` — вызывающий в двух кортежах. Числа: скрытые вызывающие 21 → 22, параметрические 6 → 7, блоки вызова 13 → 14.
- `tests/test_pages/test_hx_location_destinations.py` — 71 → 72.
- `tests/test_pages/test_responsive_markup.py`, `tests/test_pages/test_htmx_preserved.py`, `tests/test_templates/test_components.py`, `tests/test_templates/test_htmx_inventory.py`, `tests/test_templates/test_htmx_markup_security.py` — см. отклонения.

## Decisions Made

- **Адрес деградации без JS: `/accounts`, проверено по коду.** Строку `connecting` пишут только старты (`accounts.py:402`, `:581`). Переводит `connecting → syncing` только `accounts_connect_max_status` (опрос htmx), других переходов в `app/` нет. `accounts_connect_max_page` удаляет `connecting`/`sync_failed`. `accounts_list` выбирает аккаунты без фильтра статуса, и `list.html` рисует `id="account-row-N"` в ветке `else`. Прочтение планировщика подтвердилось. Тест проверяет, что аккаунт виден на `/accounts` и после приземления не удалён.
- **Сохранность атрибутов снята рендером.** Проверил, какие атрибуты шага, читаемые CSS или Alpine, пережили переезд:
  - `data-*`, `x-*`, `@…`, `:…`: ноль до перевода, ноль после.
  - `class="connect-step__form"`: переехал на внутренний узел.
  - `class`/`id`/`type`/`name`/`required` у поля и кнопки: без изменений.
  - `method`: стал строчным `post` (печатает макрос).
  - Добавились `hx-post`, `hx-target="#max-connect-step"`, `hx-swap="innerHTML"`, `hx-disabled-elt`, `hx-indicator` и узел `span.form-busy`.

  Внутри цели нет ни `x-data`, ни панелей подтверждения.
- **D-12(в) не тронут.** Шаблон мастера карточкой аккаунта не является, три копии разметки карточки не менялись.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - неверная посылка плана] Контейнер шага — сама колонка `.connect-shell`, а не обёртка внутри карточки**
- **Found during:** Задача 1
- **Issue:** План называет алерт ошибки «содержимым карточки» и ставит обёртку `#max-connect-step` внутрь карточки. В дереве алерт стоит вне карточки, прямым ребёнком flex-колонки `.connect-shell` (`gap: 14px`). Фрагмент ответа обязан нести алерт (ошибка моста, ошибка поля). Обёртка внутри карточки перенесла бы алерт в тело карточки, а отдельная обёртка вокруг алерта и карточки сняла бы промежуток.
- **Fix:** Включаемый шаблон несёт алерт и карточку целиком, `id="max-connect-step"` стоит на самом `.connect-shell`.
- **Files modified:** `app/templates/accounts/connect_max.html`, `app/templates/accounts/includes/max_connect_step.html`
- **Verification:** Отрисовка пяти ветвей до и после выноса совпала по токенам. Все критерии приёмки плана (`grep -n 'id="max-connect-step"'` — одна строка) выполнены.
- **Committed in:** `2c25159`, `7ef10a0`

**2. [Rule 3 - блокирующее] Инвентари, привязанные к файлам, переключены на включаемый шаблон (задача 1)**
- **Found during:** Задача 1. Прогон `tests/test_templates/` дал 5 падений.
- **Issue:** Утверждение плана «суиты разметки зелены без правки ожиданий» верно для трёх названных суит. Но `test_htmx_inventory.py` (`POLL_SITES`, `PERMANENT_POLLS`) и `test_components.py` (`KNOWN_SUBMIT_HANDLER_FILES`) ключуют места по ФАЙЛУ, а разметка переехала в другой файл без изменений.
- **Fix:** Ключи переименованы на `accounts/includes/max_connect_step.html`. Числа (2 места опроса, 1 обработчик) не двигались.
- **Files modified:** `tests/test_templates/test_htmx_inventory.py`, `tests/test_templates/test_components.py`
- **Committed in:** `2c25159`

**3. [Rule 3 - блокирующее] Правки ожиданий, которые сдвинул перевод (задача 2), вне списка файлов плана**
- `test_components.py`: `KNOWN_SUBMIT_HANDLER_FILES` → `frozenset()`, с записью летописи. Обработчик снят по плану, двусторонний обход поймает любой новый.
- `test_responsive_markup.py::test_accounts_connect_max_form_contract`: регулярка метода с `re.IGNORECASE`, потому что `form_wrapper` печатает `method="post"`. Маршрут, глагол и имя поля по-прежнему утверждаются.
- `test_htmx_preserved.py::test_swap_anchors_present`: старт MAX отправляется с `HX-Request`, так как без него ответ теперь 302 и якоря в теле нет по построению.
- `test_htmx_markup_security.py`: дополнение прозы о числе встроенных обработчиков событий. Проза не утверждается тестом.
- **Committed in:** `7ef10a0`

**4. [Rule 3 - блокирующее] `HX_LOCATION_DESTINATION_CALLS_DECLARED` 71 → 72 — счётчик, который план не назвал**
- **Found during:** Задача 2, прогон соседних суит после перевода
- **Issue:** Выход «нет сессии» стал вызовом `respond` без фрагмента (`accounts.py:606 → /login`).
- **Fix:** Число поставлено прогоном отказа «вызовов слоя ответа БЕЗ фрагмента найдено 72, а объявлено 71», с записью летописи. Карта назначений не двинулась.
- **Files modified:** `tests/test_pages/test_hx_location_destinations.py`
- **Committed in:** `7ef10a0`

**5. [Rule 2 - доказательство угрозы T-11-31] Экранирование эха доказано на сборке тела, плюс отдельное правило для HTTP-пути**
- **Issue:** Ветка 422 достижима только значением из пробелов, а оно разметку нести не может. Враждебный HTTP-запрос до 422 не доезжает, поэтому доказательство «эхо в 422 экранировано» по HTTP невыполнимо.
- **Fix:** `test_the_phone_echo_is_autoescaped_in_the_step_markup` рендерит `_max_step_markup(step="phone", phone=HOSTILE)`, то есть ту же функцию, что собирает тело 422. Утверждается: сырых `<script>alert(1)</script>` и `" onfocus="alert(2)"` нет, экранированная форма `&lt;script&gt;…` есть, цель подмены на месте. `test_a_hostile_phone_never_reaches_the_response_raw` проверяет, что непустое враждебное значение не попадает в ответ старта. `|safe` и `Markup(` в обоих шаблонах шага — 0 вхождений.
- **Committed in:** `49e1379`, `7ef10a0`

---

**Total deviations:** 5 авто-исправлений: 1 неверная посылка плана (Rule 1), 3 блокирующих (Rule 3), 1 доказательство угрозы (Rule 2).
**Impact on plan:** Поведение ровно то, что назначил план. Отступления касаются места идентификатора контейнера и ожиданий тестов, которые двигаются вместе с переездом разметки. Числа поставлены прогонами отказов.

## Issues Encountered

- **Прогоны.** Один прогон соседних суит (13 модулей) превысил 600 с на переднем плане и был автоматически уведён в фон. Он завершился: 1 падение (счётчик из отклонения 4), 653 зелёных.
- **Полная суита** `uv run pytest tests/ -q --deselect tests/test_planning` завершилась: **3345 passed, 1 failed, 44 deselected**, 36 мин 12 с. Единственное падение — `tests/test_pages/test_admin_panel.py::test_the_overview_error_number_matches_the_users_own_dashboard` с `assert '2' == '1'`, прогон около 04:10 UTC. Это известное ночное окно (00:00–05:00 UTC, окна 14/27/79/85). Не чинилось, `app/pages/admin.py`, `app/pages/dashboard.py`, `app/application/analytics/send_analytics.py` не тронуты. Убитых прогонов не было.
- **Суита `tests/test_templates/`** прогнана целиком после GREEN, вместе с page-суитами плана: 481 passed. Базовый прогон до плана — 474; прибавка 7 = 5 тестов транспорта + 2 случая пар.
- Счётчики, которые могли сдвинуться, прогнаны и не двинулись: `SERVER_SIDE_VALIDATION_RESPONSES` (`test_htmx_response_contract.py`), `NOTICE_WRITE_PLACES` (`test_notices_channel.py`), `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED` (`test_account_groups.py`), `HX_HEADER_WRITES` и реестр точечных заголовков (`test_htmx_gates.py`).
- **Видимое следствие для UAT.** `span.form-busy` (inline-block 8px) стоит после внутреннего узла колонки, как у формы настроек профиля. Проверить на пункте 5, не появился ли лишний отступ под кнопкой «Продолжить».

## Known Stubs

Нет.

## User Setup Required

Нет — внешних сервисов план не касается.

## Next Phase Readiness

- Все двенадцать обработчиков фазы на слое ответа. Следующий план 11-19 — закрытие окна 51.
- Ручной UAT фазы, пункт 5 (accounts, мастер MAX), записан в `<human-check>` задачи 2 и остаётся верификатору.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

## Self-Check: PASSED

- FOUND: `app/templates/accounts/includes/max_connect_step.html`, `tests/test_pages/test_max_connect_transport.py`, `11-18-SUMMARY.md`
- FOUND: `2c25159`, `49e1379`, `7ef10a0`, `48763b1`
