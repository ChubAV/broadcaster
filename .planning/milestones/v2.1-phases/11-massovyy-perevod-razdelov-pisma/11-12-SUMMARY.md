---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 12
subsystem: ui
tags: [htmx, fastapi, jinja2, admin, oob, form_wrapper]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "план 11-11 — состояние карточки пользователя во включаемых шаблонах user_actions / user_block_badge / user_access_tile; проверка идентификатора первым использованием у admin_toggle_block"
provides:
  - "admin_toggle_block на respond(): фрагмент содержимого #user-actions + внеполосные #user-block-badge и #user-access-tile; переходы для «пользователя нет»/вне колонки и «себя»"
  - "постоянные id user-actions, user-block-badge, user-access-tile на admin/user_detail.html"
  - "app/templates/admin/partials/user_actions_response.html"
  - "DECISION_OWNER_D08 и первая решённая владельцем запись OWN_RESPONSE_EXITS"
  - "форма блокировки на form_wrapper(target='#user-actions', swap='innerHTML')"
affects: [11-13, 11-20, phase-11-verification, uat-item-5]

actuals:
  tokens: 10610
  tasks: 2
  commits: 3
plan_head_before: 4be8d6572f7dbbcaa94635c1d44a58511c237a1e

tech-stack:
  added: []
  patterns:
    - "Тумблер над чужой учётной записью: основное тело — содержимое блока действий, прочие места состояния — внеполосными узлами innerHTML из тех же включаемых шаблонов"
    - "Пустая постоянная обёртка во флекс-колонке — display: contents, чтобы не давать зазора"
    - "Решённое владельцем состояние записи реестра — константой со ссылкой D-NN, а не свободной строкой"

key-files:
  created:
    - app/templates/admin/partials/user_actions_response.html
  modified:
    - app/pages/admin.py
    - app/templates/admin/user_detail.html
    - app/templates/admin/includes/user_actions.html
    - app/static/css/app.css
    - tests/test_pages/test_admin_panel.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Голый 403 на провале сверки источника у admin_toggle_block остался (D-08 владельца). Запись OWN_RESPONSE_EXITS стоит в состоянии DECISION_OWNER_D08, которое называет D-08 и проходит правило авторства."
  - "_OWN_RESPONSE_PRICE получил второе поколение, а не переписан. Опровергнута только часть следствия (3) «плашка не рисуется»: слушатель htmx:responseError пропускает лишь 422, и немой 403 поднимает общую плашку. Префикс строки не изменился, и правило обоснований по-прежнему узнаёт цену."
  - "id получили блок действий и две области состояния, у которых есть потребитель-своп (прочтение D-03 рядом с D-02). worker_row.html и queue_row.html не тронуты."
  - "Пустая обёртка бейджа получила display: contents в app.css. Иначе во флекс-колонке личности у каждого незаблокированного появлялся бы зазор 3px."
  - "Форма бесплатного доступа в user_actions.html не переведена: её обработчик ещё отвечает перенаправлением. Её переводит план 11-13."

patterns-established:
  - "Ответ тумблера карточки: include содержимого блока + плоские узлы hx-swap-oob=\"innerHTML:#…\" с include тех же шаблонов"

requirements-completed: [FORM-03, FORM-04]

coverage:
  - id: D1
    description: "Блокировка на htmx отвечает 200: содержимое #user-actions с подписью по новому состоянию и внеполосные бейдж и плитка, без панелей подтверждения. Без htmx — прежний 302."
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_block_toggle_over_htmx_refreshes_every_place_of_the_state"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[admin_toggle_block-блокировка пользователя — успех]"
        status: pass
    human_judgment: false
  - id: D2
    description: "«Пользователя нет», величина вне колонки и «себя»: на htmx 204 + HX-Location на тот же адрес, что и 302."
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (три случая admin_toggle_block, переход)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Голый 403 остался и объявлен записью OWN_RESPONSE_EXITS в состоянии DECISION_OWNER_D08; OWN_RESPONSE_EXITS_DECLARED = 10."
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_own_response_exit_of_a_converted_handler_is_declared"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_no_own_response_exit_claims_a_decision_the_owner_did_not_make"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_destructive_admin_actions_refuse_a_foreign_origin"
        status: pass
    human_judgment: false
  - id: D4
    description: "Форма блокировки на form_wrapper с целью #user-actions и innerHTML; гейты разметки (G-7, G-9, G-11, G-12) зелёные."
    requirement: FORM-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере десять нажатий подряд без перезагрузки: подпись, бейдж и плитка согласованы, панели входа и удаления открываются и не множатся (UAT фазы, пункт 5)."
    verification: []
    human_judgment: true
    rationale: "Переинициализация Alpine и отсутствие копящихся слушателей после свапа видны только в живом браузере; тест утверждает отсутствие панелей в ответе, но не поведение DOM."

duration: 34min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 12: Блокировка пользователя на слое ответа Summary

**Блокировка из карточки пользователя на htmx отвечает содержимым `#user-actions` и внеполосными бейджем и плиткой доступа. Разметка берётся из тех же включаемых шаблонов, что рисуют страницу. Голый 403 отказа по источнику объявлен изъятием по решению владельца D-08.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-16T18:01:48Z
- **Completed:** 2026-09-16T18:35:33Z
- **Tasks:** 2
- **Files modified:** 10 (1 created)

## Accomplishments

- `admin_toggle_block` теперь идёт через `respond()`.
  - Успех: фрагмент, собранный шаблоном `admin/partials/user_actions_response.html`. Вид доступа собирается теми же `_active_subscriptions_by_user` и `_access_view` под ключом `target_access`.
  - «Пользователя нет», величина вне колонки и «себя» отвечают переходом.
  - Без htmx ответ прежний: 302 на `/admin/users/{id}`.
- На `admin/user_detail.html` появились три постоянные обёртки: `id="user-actions"` на `data-actions`, `<span id="user-block-badge">` в строке личности и `<div id="user-access-tile">` внутри карточки плитки. Сверено до и после в двух состояниях: изменились только сами обёртки и пробельные символы.
- Отказ по источнику остаётся голым 403 и объявлен в `OWN_RESPONSE_EXITS`.
  - Состояние записи — `DECISION_OWNER_D08`.
  - Основание — недостижимость из интерфейса на htmx-пути.
  - Цена названа словами: плашка «Действие не выполнено. Попробуйте ещё раз через минуту.» даёт неверный совет.
- Форма блокировки переведена на `form_wrapper(action=…, target='#user-actions', swap='innerHTML')`. Формы бесплатного доступа, входа под пользователем и удаления не тронуты.

## Task Commits

1. **Задача 1 RED: тест обновления трёх мест и четыре пары транспортов** — `dba64de` (test)
2. **Задача 1 GREEN: блокировка на слое ответа, обёртки, шаблон ответа, изъятие D-08** — `389e4b6` (feat)
3. **Задача 2: форма блокировки на обёртке** — `b73fdfb` (feat)

## TDD Gate Compliance

- **RED** (`dba64de`): целевой тест — `test_block_toggle_over_htmx_refreshes_every_place_of_the_state`.
  - Итог прогона: `5 failed, 3 passed`, rc=1.
  - Упал целевой тест: `блокировка на слое письма ответила 302 вместо 200`.
  - Упали четыре случая пары `admin_toggle_block`, у каждого `слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ`.
  - Причина в коде: `return RedirectResponse(url=f"/admin/users/{user_id}", status_code=302)` в `app/pages/admin.py`.
  - Запись собрана механически из JUnit XML прогона. `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`).
- **GREEN** (`389e4b6`): до записи в реестрах тот же прогон покраснел ровно на правилах счёта и полноты. Все тексты отказов дословно перенесены в летописи:
  - `стало 19, а в файле записано 20`;
  - `найдено 10, объявлено 9`;
  - `НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::admin_toggle_block (вид Response(status_code=403))`;
  - `вызовов … БЕЗ фрагмента найдено 54, а объявлено 52`;
  - `внеполосных блоков найдено 19, объявлено 17`.
  - После записей проверочный набор задачи дал `324 passed`.
- REFACTOR-коммита нет. Задача 2 не TDD: её числа поставлены прогонами покрасневших разметочных правил.

## Files Created/Modified

- `app/pages/admin.py` — `admin_toggle_block` идёт через `respond()` со сборщиком `_fragment`.
- `app/templates/admin/partials/user_actions_response.html` (новый) — плоское тело: include блока действий и два узла `innerHTML`. В шапке названы узлы и записано прочтение D-03.
- `app/templates/admin/user_detail.html` — три постоянные обёртки.
- `app/templates/admin/includes/user_actions.html` — форма блокировки идёт через `form_wrapper`.
- `app/static/css/app.css` — `[data-identity-meta] > #user-block-badge { display: contents; }`.
- `tests/test_pages/test_admin_panel.py` — новый поведенческий тест.
- `tests/test_pages/test_htmx_post_pairs.py` — четыре случая, 21 → 25.
- `tests/test_pages/test_htmx_gates.py` — изменены реестры:
  - `NOT_YET_CONVERTED` 20 → 19;
  - `FRAGMENT_RESPONSE_HANDLERS` 9 → 10;
  - добавлена константа `DECISION_OWNER_D08`;
  - второе поколение `_OWN_RESPONSE_PRICE`;
  - новая запись `OWN_RESPONSE_EXITS`, 9 → 10.
- `tests/test_pages/test_hx_location_destinations.py` — 52 → 54.
- `tests/test_templates/test_htmx_markup_gates.py` — счётчики:
  - `OOB_BLOCKS` 17 → 19;
  - скрытые вызывающие 15 → 16;
  - вызывающие параметрических целей 5 → 6;
  - блоки вызова обёртки 6 → 7.

## Decisions Made

См. `key-decisions` во frontmatter. Главное:
- Изъятие D-08 записано ссылкой на решение владельца, а не придумано планом.
- Устаревшую часть общей цены D-08 не стёрли: она названа опровергнутой новым поколением.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Пустая обёртка бейджа давала лишний зазор в колонке личности**
- **Found during:** задача 1
- **Issue:** `[data-identity-meta]` — флекс-колонка с `gap: 3px`. Пустой `<span id="user-block-badge">` у каждого незаблокированного пользователя стал бы флекс-элементом и добавил зазор под адресом. Вывод страницы перестал бы совпадать с прежним по виду.
- **Fix:** правило `display: contents` для обёртки в `app/static/css/app.css`. Файл не был в `files_modified` плана.
- **Files modified:** `app/static/css/app.css`
- **Verification:** `tests/test_templates/` и соседние страницы (`test_responsive_markup`, `test_shell`, `test_admin_users`) — `640 passed`.
- **Committed in:** `389e4b6`

**2. [Rule 1 - Bug] Общая цена `_OWN_RESPONSE_PRICE` расходилась с измеренным поведением плашки**
- **Found during:** задача 1 (план предусматривал эту проверку)
- **Issue:** следствие (3) утверждало «плашка не рисуется», а `htmx_error_banner.html` исключает только 422.
- **Fix:** к строке дописано второе поколение, которое называет опровергнутую часть. Префикс, по которому правило узнаёт цену, прежний.
- **Files modified:** `tests/test_pages/test_htmx_gates.py`
- **Committed in:** `389e4b6`

---

**Total deviations:** 2 auto-fixed (оба Rule 1).
**Impact on plan:** правка стилей нужна, чтобы вид страницы не изменился. Вторая правка ожидалась по плану. Объём не вырос.

## Issues Encountered

- Полную суиту `tests/` исполнитель не запускал: хост с ограниченной памятью, прогон займёт десятки минут. Полный прогон делает оркестратор. Вместо неё прошли три набора:
  - проверочный набор задачи 1 — `324 passed`;
  - `tests/test_templates/` вместе с `test_admin_users`, `test_responsive_markup`, `test_shell` после задачи 1 — `640 passed`;
  - проверочный набор задачи 2 — `368 passed`.
  - После задачи 2 ещё раз: `tests/test_templates/` вместе с `test_hx_location_destinations`, `test_confirm_delete_transport`, `test_identifier_bounds`, `test_blocked_user`, `test_origin_guard_on_destructive_routes`, `test_admin_users` — `384 passed`.
- Ни один прогон не был убит.
- Известный красный `test_the_overview_error_number_matches_the_users_own_dashboard` (окно 00:00–05:00 UTC) не встретился: работа шла в 18:01–18:35 UTC.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 11-13 переводит тумблер бесплатного доступа. Обёртки `#user-actions` и `#user-access-tile` уже есть, и шаблон ответа можно переиспользовать или расширить.
- D-08 называет `admin_toggle_free_access` среди трёх обработчиков. Его запись встанет в то же состояние `DECISION_OWNER_D08`.
- Ручной UAT фазы, пункт 5: десять нажатий подряд, панели не множатся.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED
