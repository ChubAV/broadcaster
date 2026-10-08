---
phase: 14-avtorizatsiya-na-htmx
plan: 01
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, hx-redirect, 422, tdd]

requires:
  - phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
    provides: слой ответа `app/pages/htmx.py` (`_local_path`, `_with_notice`, `_require_registered_notice`), области уведомления шелла
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: `respond_field_error` (422 на обоих транспортах), `redirect_external` (форма выхода HX-Redirect), реестр пар `POST_PAIR_CASES`
  - phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
    provides: приём «шаг включаемым шаблоном + постоянный якорь + innerHTML»
provides:
  - "`redirect_internal` — выход полной перезагрузки на локальный адрес (302 без htmx, 204 + HX-Redirect с ним)"
  - "постоянный якорь `#auth-step` второго шелла после областей уведомления"
  - "реестр экранов `AUTH_SCREENS` / `AuthScreen`, обёртка ответа-фрагмента `auth/includes/step_response.html` с `<title>` верхним узлом, `_screen_markup`, `_screen_builders`"
  - "экран входа включаемым шаблоном `auth/includes/login_step.html` через `form_wrapper`"
  - "`login_submit` на выходах слоя: 422 + эхо email, успех полной загрузкой с cookie на возвращённом объекте"
  - "узнавание «переведённого» по закрытому семейству `RESPONSE_LAYER_EXITS` с тремя контролями зубов"
  - "ветка пар `FULL_LOAD`, личность `ANONYMOUS`, поле `_PairCase.sets_session_cookie`"
  - "модуль `tests/test_pages/test_auth_transport.py` (8 правил)"
affects: [14-02, 14-03, 14-04, 14-05, 14-06, 14-07]

actuals:
  tokens: 26300
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "экран авторизации = запись AUTH_SCREENS + включаемый шаблон <screen>_step.html; фрагмент — step_response.html (<title> + include)"
    - "успех со сменой личности: response = await redirect_internal(...); set_session_cookie(response, ...); return response"
    - "ошибка поля экрана: page, fragment = _screen_builders(request, screen, **ctx); return await respond_field_error(...)"

key-files:
  created:
    - app/templates/auth/includes/login_step.html
    - app/templates/auth/includes/step_response.html
    - tests/test_pages/test_auth_transport.py
  modified:
    - app/pages/htmx.py
    - app/pages/auth.py
    - app/templates/auth_base.html
    - app/templates/auth/login.html
    - app/static/css/app.css
    - tests/test_pages/test_htmx_response_layer.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_blocked_user.py
    - tests/test_pages/test_password_reset.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Выход полной перезагрузки — отдельная функция `redirect_internal`, а не параметр `respond()`; cookie ставит вызывающий на возвращённый объект"
  - "Якорь `#auth-step` стоит ПОСЛЕ `#notice`/`#notice-alert` и плашки аварии; визуальный порядок задаёт CSS (`display: contents` + `order`)"
  - "Узнавание «переведённого» — по ИМЕНИ из закрытого семейства `RESPONSE_LAYER_EXITS`, а не по приставке; `RESPONSE_CALL` остаётся"
  - "`DEGRADATION_MARKERS` разметочного гейта пополнен выходами слоя — иначе `POST /login` стал бы «фрагментным» маршрутом"
  - "Форма экранирования кавычки в эхе — `&#34;` (допущение A5 RESEARCH подтверждено первым прогоном)"

patterns-established:
  - "Экран второго шелла: одна разметка на страницу и фрагмент, `<title>` фрагмента из записи реестра, сличаемый с блоком title страницы правилом суиты"
  - "Пароль в контекст экрана не передаётся: `_screen_builders` отвергает ключ `password` исключением без подстановки значения"

requirements-completed: [SIGN-01, SIGN-02, SIGN-03]

coverage:
  - id: D1
    description: "Неверный пароль — 422 на обоих транспортах: страница без htmx, фрагмент с `<title>` верхним узлом с htmx; email в `value=`, пароля и cookie нет"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_wrong_password_redraws_the_login_screen_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_hostile_email_comes_back_escaped_on_both_transports"
        status: pass
    human_judgment: false
  - id: D2
    description: "Заблокированный с верным паролем — 422, `BLOCKED_LOGIN_ERROR`, email в поле, cookie нет на обоих транспортах"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_blocked_user_is_refused_with_422_and_no_cookie_on_both_transports"
        status: pass
    human_judgment: false
  - id: D3
    description: "Верный пароль — 302 без htmx; 204 + `HX-Redirect: /dashboard` без `HX-Location` с cookie на том же ответе; кабинет открывается следующим запросом"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_login_path_walks_from_a_wrong_password_to_the_dashboard"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[login_submit-вход — верный пароль]"
        status: pass
    human_judgment: false
  - id: D4
    description: "Постоянный якорь `#auth-step` после областей уведомления; форма входа из `form_wrapper` с `hx-target=#auth-step`, `innerHTML`; код исхода переживает ошибку входа"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_login_page_puts_the_step_anchor_after_the_notice_regions"
        status: pass
    human_judgment: false
  - id: D5
    description: "Выход `redirect_internal`: 302/204 + HX-Redirect, код исхода в адресе, отказ на внешнем/кириллическом/многострочном адресе и незнакомом коде"
    requirement: SIGN-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_an_internal_full_load_never_leaves_the_site_or_carries_unencodable_text"
        status: pass
    human_judgment: false
  - id: D6
    description: "Гейты узнают переведённым обработчик на любом выходе семейства; похожее имя не переводит; числа поставлены прогоном"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_handler_answering_only_by_a_full_load_is_converted"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_lookalike_exit_name_does_not_convert_a_handler"
        status: pass
    human_judgment: false
  - id: D7
    description: "Карточка авторизации выглядит как до перевода (подзаголовок под брендом, без сдвига); в браузере вкладка «Вход — Broadcaster», email остаётся, верный пароль уводит в кабинет и сменяет cookie"
    requirement: SIGN-01
    verification: []
    human_judgment: true
    rationale: "Визуальная раскладка и поведение браузера (заголовок вкладки, полная навигация, менеджер паролей) сервером не измеряются — UI-ревью и ручной UAT фазы (критерий 4)"

duration: 73min
completed: 2026-09-22
status: complete
plan_head_before: fd69a26a2d9b0a301f54900a65ff3df9610ad738
commits: 5
---

# Phase 14 Plan 01: Трасер входа на htmx — Summary

**Вход страничной формой переведён на слой ответа за постоянным якорем `#auth-step`: неверный пароль — 422 с эхом email на обоих транспортах, верный — 302 или 204 + `HX-Redirect: /dashboard` с cookie на том же ответе, через новый выход `redirect_internal`.**

## Performance

- **Duration:** 73 min
- **Started:** 2026-09-22T10:40:25Z
- **Completed:** 2026-09-22T11:53:30Z
- **Tasks:** 3 (трасер + 2 расширения)
- **Files modified:** 14 (3 новых, 11 изменённых) — ровно объявленные планом

## Accomplishments
- Архитектура фазы доказана на одном пути: якорь шелла → экран включаемым шаблоном → ответ-фрагмент с `<title>` верхним узлом → `respond_field_error` (422) / `redirect_internal` (полная перезагрузка) → cookie на возвращённом объекте.
- `redirect_internal` в `app/pages/htmx.py`: адрес через `_with_notice` → `_local_path`, код исхода через `_require_registered_notice`, ровно один заголовок перехода.
- `app/pages/auth.py`: `AUTH_STEP_RESPONSE_TEMPLATE`, `AuthScreen`, `AUTH_SCREENS` (ключ `login`), `_screen_markup`, `_screen_builders` (отвергает `password`); оба прежних возврата `login_submit` сняты (D-14), порядок «пароль → блокировка → cookie» и тексты прежние (D-15).
- Гейты: `RESPONSE_LAYER_EXITS` и три контроля; `NOT_YET_CONVERTED_COUNT` 10 → 9, `HX_HEADER_WRITES` 5 → 6 (+ `SAFE_BY_NAME`), `POST_PAIR_CASES_DECLARED` 58 → 59, `PAIRED_302_ASSERTIONS_DECLARED` 167 → 176, скрытые вызывающие 24 → 25, параметрические 9 → 10, блоки вызова 19 → 20, `FRAGMENT_ROUTES_DECLARED` 11 → 11 (движения нет, замер). Каждое число поставлено прогоном покрасневшего правила, летопись «Фаза 14, план 14-01» у каждого.

## Task Commits

1. **Задача 1 (трасер): сквозной срез входа** — RED `ca66794f` (test), GREEN `bfe43f98` (feat)
2. **Задача 2: гейты узнают вход переведённым** — RED `be3444e8` (test), GREEN `e74f8b63` (test: record — правки только в тестах)
3. **Задача 3: перечни разметки и вёрстка якоря** — `05d1e283` (test: record)

**Plan metadata:** коммит `docs(14-01)` с этим файлом, STATE.md и ROADMAP.md.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 (трасер) | `ca66794f` | `assert 200 == 422` в `test_the_login_path_walks_from_a_wrong_password_to_the_dashboard`; вывод содержит строку `FAILED tests/test_pages/test_auth_transport.py::test_the_login_path_walks_from_a_wrong_password_to_the_dashboard` и итог `1 failed, 7 deselected` — все три совпадения `<tdd_notes>` | `bfe43f98` |
| 2 | `be3444e8` | `assert 'app/pages/profile.py::a_route_leaving_by_a_full_load' in {…}` в `test_control_a_handler_answering_only_by_a_full_load_is_converted` (и то же для выхода ошибки поля); `2 failed, 1 passed` | `e74f8b63` |

- RED-улика обеих задач проверена штатным вербом: `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`). Запись собрана из `--junit-xml` того же прогона, перегнанного в TAP скриптом в scratchpad (не закоммичен).
- **Честная оговорка по задаче 2:** четыре правила `redirect_internal` в `test_htmx_response_layer.py` зелены уже на RED-коммите — выход построен трасером задачи 1 (без него срез не проходил). Это правила контракта готового выхода, а не RED; RED задачи 2 — контроли узнавания. Контроль похожего имени (`lookalike`) зелен до GREEN по построению: он доказывает, что расширение НЕ должно его переводить.
- Задача 3 не `tdd="true"` — RED не требовался; числа поставлены прогоном покрасневших правил.
- Гейт-валидация истории: `test(14-01)` и `feat(14-01)` присутствуют; `refactor(14-01)` нет (не требовался).

## Tracer feedback gate

Строка 3 цепочки (интерактивно, `end-of-phase`, `<verify>` только `<automated>`): после `bfe43f98` весь `<verify>` трасера перезапущен — `8 passed`, отбор `walks_from_a_wrong_password or title_matches` — `2 passed`, `compileall` молчит. Трасер зелен от начала до конца — расширение начато без чекпоинта.

## Full suite

`uv run pytest tests/ -q -p no:randomly` — старт **2026-09-22T11:13:05Z** (вне окна 00:00–05:00 UTC админ-обзора), конец 11:53:09Z: **3541 passed, 0 failed, 998 warnings in 2394.15s (0:39:54)**. `tests/test_planning` в прогон входит (в `pyproject.toml` нет отбора по маркерам). Регистров, покрасневших вне названных планом, прогон не показал.

## Files Created/Modified
- `app/pages/htmx.py` — `redirect_internal` + строка шапки модуля о шестом виде выхода
- `app/pages/auth.py` — реестр экранов, сборщики, перевод `login_submit`
- `app/templates/auth_base.html` — якорь `#auth-step`, переходный блок подзаголовка внутри него
- `app/templates/auth/login.html` — страница = включение экрана
- `app/templates/auth/includes/login_step.html` — единственная разметка экрана входа
- `app/templates/auth/includes/step_response.html` — обёртка ответа-фрагмента
- `app/static/css/app.css` — `.auth-step { display: contents; }`, `order` бренда и подзаголовка
- `tests/test_pages/test_auth_transport.py` — 8 правил входа
- `tests/test_pages/test_htmx_response_layer.py` — 4 правила выхода (8 случаев с параметризацией)
- `tests/test_pages/test_htmx_gates.py` — семейство выходов, три контроля, сдвиги перечней
- `tests/test_pages/test_htmx_post_pairs.py` — ветка `FULL_LOAD`, случай входа, синтетический контроль
- `tests/test_pages/test_blocked_user.py`, `tests/test_pages/test_password_reset.py` — 200 → 422 (D-03)
- `tests/test_templates/test_htmx_markup_gates.py` — признак деградации, вызывающие, `auth-step` долгоживущий

## Decisions Made
- Решения из Claude's Discretion приняты так, как записал план (якорь, раскладка шаблонов, отдельная функция выхода, без `autofocus`).
- Эхо: форма экранирования `&#34;&gt;&lt;script&gt;…` — подтверждена первым прогоном (A5).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug, отозвано в той же сессии] Условный абзац подзаголовка в шелле**
- **Found during:** Задача 1
- **Issue:** опасение, что пустой `<p class="auth-subtitle">` переведённого экрана займёт промежуток карточки.
- **Fix:** сначала напечатан условно (`self.auth_subtitle()|trim`), затем в задаче 3 возвращён к буквальной форме плана: в `app.css` уже есть `.auth-subtitle:empty { display: none; }`, и пустой абзац промежутка не занимает.
- **Files modified:** `app/templates/auth_base.html`
- **Committed in:** `bfe43f98` (условно), `05d1e283` (возврат к плану)

**2. [Порядок утверждений трасера] Проверка якоря после статуса**
- **Found during:** Задача 1 (RED)
- **Issue:** `<behavior>` перечисляет «ровно одно `id="auth-step"`» раньше 422, а `<tdd_notes>` требует причинный литерал `assert 200 == 422` — при прежнем порядке RED был бы `assert 0 == 1`.
- **Fix:** ответ `GET /login` сохраняется, утверждение числа якорей стоит сразу после проверки 422. Ни одно утверждение `<behavior>` не снято.
- **Committed in:** `ca66794f`

**3. [Команда полного прогона] `-p no:randomly`**
- Полный прогон шёл с `-p no:randomly` (как все `<verify>` плана); в остальном — `uv run pytest tests/ -q`.

---

**Total deviations:** 3 (1 отозванная правка, 2 оформления). **Impact:** поведение и объём — как в плане; 14 файлов, ни одного сверх объявленных.

## Issues Encountered
- Прогноз `PAIRED_302_ASSERTIONS_DECLARED` («+8 прежних плюс новые») совпал с замером: +9 (восемь прежних и половина деградации успеха в `test_auth_transport.py`).
- Утверждения 200/302 о входе в модулях, не названных планом, прогон не покраснил: помощники входа суиты ходят без признака htmx и по-прежнему получают 302.

## Known Stubs

None — экран входа получает данные от обработчика; пустое `email` на `GET /login` — нормальное начальное состояние поля.

## Threat Flags

None — новых поверхностей сверх `<threat_model>` нет: T-14-01…T-14-06 закрыты правилами `test_auth_transport.py`, `test_htmx_response_layer.py` и записью `SAFE_BY_NAME`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 14-02 (регистрация) садится на готовое: `AUTH_SCREENS`, `_screen_builders`, `step_response.html`, якорь, ветка `FULL_LOAD`. Ему остаются `respond_screen` (выход «200, экран сменился»), ветка `SCREEN` и пополнение `RESPONSE_LAYER_EXITS` / `DEGRADATION_MARKERS` именем нового выхода.
- SIGN-01…03 НЕ отмечены Complete: их объявляют планы 14-02…14-07, у которых ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*

## Self-Check: PASSED
