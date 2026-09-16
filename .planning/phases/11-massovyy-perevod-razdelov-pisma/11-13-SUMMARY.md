---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 13
subsystem: ui
tags: [htmx, fastapi, jinja2, admin, oob, form_wrapper, billing-cache]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "план 11-12 — шаблон ответа admin/partials/user_actions_response.html, постоянные обёртки #user-actions / #user-block-badge / #user-access-tile, константа DECISION_OWNER_D08"
provides:
  - "admin_toggle_free_access на respond(): фрагмент блока действий с внеполосными бейджем и плиткой доступа; «пользователя нет» и «строки подписки нет» — переходом"
  - "общая сборка ответа обоих тумблеров карточки — _user_actions_response в app/pages/admin.py"
  - "сброс кэша вердикта до вызова слоя; порядок стережёт test_free_access_fragment_is_assembled_after_the_access_cache_is_dropped"
  - "OWN_RESPONSE_EXITS: 11 записей, все в состоянии DECISION_OWNER_D08"
  - "форма бесплатного доступа на form_wrapper(target='#user-actions', swap='innerHTML')"
affects: [11-15, 11-20, phase-11-verification, uat-item-5, window-63]

actuals:
  tokens: 6352
  tasks: 2
  commits: 3
plan_head_before: df3b3848f66a433ab46fbdae2da7e79b6b05e2e3

tech-stack:
  added: []
  patterns:
    - "Порядок «сброс кэша до сборки фрагмента» утверждается журналом вызовов через подмену имён модуля, а не значением в разметке"
    - "Один ответ на несколько тумблеров одной области — модульная сборка, которую зовут нульарные ленивые _fragment обработчиков"

key-files:
  created: []
  modified:
    - app/pages/admin.py
    - app/pages/htmx.py
    - app/templates/admin/includes/user_actions.html
    - tests/test_pages/test_admin_panel.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Сборка ответа вынесена из admin_toggle_block в модульную _user_actions_response, и оба тумблера зовут её из своих ленивых _fragment. Шаблон ответа тот же, что у 11-12. Второй копии нет ни шаблона, ни сборки."
  - "Порядок кэша доказан журналом вызовов. Плитка читает строку подписки через _access_view, а не кэш вердикта, поэтому тест по одному значению ∞ зеленел и на мутанте «сборка до сброса». Проверка журнала на том же мутанте покраснела."
  - "Девять прежних записей OWN_RESPONSE_EXITS переведены в DECISION_OWNER_D08. D-08 называет их множеством («к девяти записям OWN_RESPONSE_EXITS»). У DECISION_OWNER_D08 и LIFTING_CONDITION_OWN_RESPONSE прежний текст сохранён, новые поколения дописаны. Окно 63 не тронуто и остаётся open."
  - "Второе поколение докстринга app/pages/htmx.py: выходов теперь одиннадцать, форма решена D-08. Прежний абзац про «ДЕВЯТЬ… ЖДЁТ ВЛАДЕЛЬЦА» не стёрт и назван устаревшим."

patterns-established:
  - "Модульная сборка ответа карточки пользователя: _user_actions_response(db, target_user, admin)"

requirements-completed: [FORM-03, FORM-04]

coverage:
  - id: D1
    description: "Бесплатный доступ на htmx отвечает 200: содержимое #user-actions с «Снять бесплатный доступ», внеполосная плитка показывает ∞, внеполосный бейдж, без панелей подтверждения и без документа. Без htmx — прежний 302 на /admin/users/{id}."
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_free_access_toggle_over_htmx_refreshes_the_access_tile"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[admin_toggle_free_access-бесплатный доступ — успех]"
        status: pass
    human_judgment: false
  - id: D2
    description: "«Строки подписки нет» → /admin/users/{id}, «пользователя нет» → /admin/users; на htmx 204 + HX-Location на тот же адрес, что 302. Журнал free_access_toggle_without_subscription прежний."
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (два случая admin_toggle_free_access, переход)"
        status: pass
      - kind: integration
        ref: "tests/test_admin.py#test_the_free_access_toggle_survives_a_user_without_a_subscription_row"
        status: pass
    human_judgment: false
  - id: D3
    description: "Плитка во фрагменте собирается после invalidate_access_cache. Мутант с обратным порядком краснит проверку."
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_free_access_fragment_is_assembled_after_the_access_cache_is_dropped"
        status: pass
      - kind: integration
        ref: "tests/test_admin.py#test_granting_free_access_invalidates_the_access_verdict_cache"
        status: pass
    human_judgment: false
  - id: D4
    description: "Голый 403 объявлен записью OWN_RESPONSE_EXITS с DECISION_OWNER_D08; все 11 записей решены D-08; OWN_RESPONSE_EXITS_DECLARED = 11; NOT_YET_CONVERTED_COUNT = 18; FRAGMENT_RESPONSE_HANDLERS_DECLARED = 11."
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py -k 'own_response or decision or backlog or three_sets or fragment_response'"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_destructive_admin_actions_refuse_a_foreign_origin"
        status: pass
    human_judgment: false
  - id: D5
    description: "Форма бесплатного доступа на form_wrapper с целью #user-actions и innerHTML; разметочные гейты зелёные, блоки вызова обёртки 7 → 8."
    requirement: FORM-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "В браузере десяток нажатий «Заблокировать/Разблокировать» и «Выдать/Снять бесплатный доступ» подряд без перезагрузки: подписи, бейдж и плитка согласованы; панели входа и удаления открываются и не множатся (UAT фазы, пункт 5)."
    verification: []
    human_judgment: true
    rationale: "Переинициализация Alpine после свапа и отсутствие копящихся панелей видны только в живом браузере. Тесты проверяют ответ сервера, но не поведение DOM."

duration: 34min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 13: Бесплатный доступ на слое ответа Summary

**Тумблер бесплатного доступа в карточке пользователя на htmx отвечает тем же фрагментом блока действий, что блокировка. Кэш вердикта сбрасывается до сборки плитки, и этот порядок проверяет тест, который краснеет на обратном порядке. Решение владельца D-08 проставлено всем одиннадцати записям реестра собственных выходов.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-16T19:16:23Z
- **Completed:** 2026-09-16T19:50:23Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- `admin_toggle_free_access` теперь идёт через `respond()`.
  - Порядок в обработчике: сверка источника (голый 403, не тронута), граница идентификатора, выборка строки подписки, инверсия признака, `commit`, журнал `free_access_toggled`, `invalidate_access_cache`. Только после этого вызывается `respond(..., fragment=_fragment)`, а сам `_fragment` исполняется внутри слоя.
  - «Пользователя нет» и «строки подписки нет» отвечают переходом: на htmx 204 + `HX-Location`, без htmx 302 на тот же адрес. Журнал `free_access_toggle_without_subscription` пишется до ответа.
- Сборка ответа вынесена в `_user_actions_response(db, target_user, admin)`. Её зовут оба тумблера. Шаблон тот же, что в 11-12: `admin/partials/user_actions_response.html`.
- Порядок кэша проверен мутацией. В мутанте `invalidate_access_cache` переставлен после `respond`, и `test_free_access_fragment_is_assembled_after_the_access_cache_is_dropped` покраснел с журналом `['access_view', 'invalidate:2']`. На том же мутанте тест значения `∞` остался зелёным: плитка читает строку подписки, а не кэш. Исходник восстановлен копией, `_mutant` в дереве не осталось.
- Реестр `OWN_RESPONSE_EXITS`:
  - добавлена запись бесплатного доступа в состоянии `DECISION_OWNER_D08`;
  - девять прежних записей переведены в `DECISION_OWNER_D08`;
  - `LIFTING_CONDITION_OWN_RESPONSE` и граница `DECISION_OWNER_D08` получили новые поколения, прежний текст сохранён.
- Докстринг `app/pages/htmx.py` получил второе поколение первого абзаца.
- Форма бесплатного доступа переведена на `form_wrapper(target='#user-actions', swap='innerHTML')`. Теперь в файле два вызова с `target='#user-actions'`.

## Task Commits

1. **Задача 1 RED: тест плитки, тест порядка кэша, три пары транспортов** — `d4ccd24` (test)
2. **Задача 1 GREEN: обработчик на слое ответа, общая сборка, реестр D-08, поколение докстринга** — `4c86a56` (feat)
3. **Задача 2: форма бесплатного доступа на обёртке** — `124cb9e` (feat)

## TDD Gate Compliance

- **RED** (`d4ccd24`). Целевой тест — `test_free_access_toggle_over_htmx_refreshes_the_access_tile`.
  - Прогон связки: `5 failed, 2 passed`, rc=1. Упали оба новых теста админки и три случая пары `admin_toggle_free_access` (`слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ`).
  - Отказ целевого теста: `выдача бесплатного доступа на слое письма ответила 302 вместо 200`.
  - Причина в коде: `return RedirectResponse(url=location, status_code=302)`, `app/pages/admin.py:1713` на дереве RED.
  - Запись собрана из JUnit XML прогона двух тестов админки (`2 failed`, rc=1). `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`).
  - Первая попытка вернула `INVALID_RED` (`nonzero_exit_without_test_failure`). Причина — ошибка в моём конвертере: `tc.find('failure') or tc.find('error')`, а элемент без детей ложен. После исправления на `is not None` запись прошла.
  - Число пар поставлено прогоном до коммита: `случаев пар в реестре 28, объявлено 25`.
- **GREEN** (`4c86a56`). До записей в реестрах прогон четырёх модулей гейтов дал `8 failed, 212 passed`. Упали ровно правила счёта и полноты, их отказы перенесены в летописи дословно:
  - `число непереведённых обработчиков стало 18, а в файле записано 19` и отказ `test_the_three_sets_do_not_overlap`;
  - `обработчиков, отдающих фрагмент, найдено 11, объявлено 10`;
  - `НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/admin.py::admin_toggle_free_access (вид Response(status_code=403))`. Это и есть покраснение правила полноты реестра на втором тумблере до записи;
  - после записи и до правки числа: `собственных выходов переведённых обработчиков объявлено 11, а число говорит 10`;
  - `вызовов слоя ответа БЕЗ фрагмента найдено 56, а объявлено 54`.
  - После записей проверочный набор задачи вместе с `tests/test_admin.py` дал `246 passed`.
- REFACTOR-коммита нет: вынос `_user_actions_response` вошёл в GREEN. Задача 2 не TDD, её число поставлено прогоном покрасневшего разметочного правила.

## Files Created/Modified

- `app/pages/admin.py`:
  - новая `_user_actions_response`;
  - `admin_toggle_block` зовёт её из своего `_fragment`;
  - `admin_toggle_free_access` переведён на `respond()`.
- `app/pages/htmx.py` — второе поколение первого абзаца докстринга.
- `app/templates/admin/includes/user_actions.html` — форма бесплатного доступа на обёртке, поколение шапки.
- `tests/test_pages/test_admin_panel.py` — два новых теста: плитка и порядок кэша.
- `tests/test_pages/test_htmx_post_pairs.py` — три случая, 25 → 28. Строка подписки заводится посевом явно.
- `tests/test_pages/test_htmx_gates.py`:
  - `NOT_YET_CONVERTED` 19 → 18;
  - `FRAGMENT_RESPONSE_HANDLERS` 10 → 11;
  - `OWN_RESPONSE_EXITS` 10 → 11, все записи в `DECISION_OWNER_D08`;
  - поколения `LIFTING_CONDITION_OWN_RESPONSE` и границы `DECISION_OWNER_D08`.
- `tests/test_pages/test_hx_location_destinations.py` — 54 → 56.
- `tests/test_templates/test_htmx_markup_gates.py` — `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 7 → 8, поколение в обосновании параметрической цели `form_wrapper`.

## Decisions Made

См. `key-decisions` во frontmatter. Главное:
- Второй копии ответа не появилось: тот же шаблон и одна сборка.
- Решённое состояние у девяти прежних записей опирается на текст D-08 («к девяти записям `OWN_RESPONSE_EXITS`»). План его не выдумывал.
- Окно 63 не закрыто и не снято. D-08 закрывает только его часть «решение о форме».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Отдельный тест порядка «сброс кэша до сборки плитки»**
- **Found during:** задача 1
- **Issue:** план требовал доказать порядок тестом на `∞` в плитке. Плитка читает строку подписки через `_access_view`, а не кэш вердикта. Поэтому такой тест не отличает правильный порядок от обратного, и мутант это подтвердил.
- **Fix:** добавлен `test_free_access_fragment_is_assembled_after_the_access_cache_is_dropped`. Он подменяет `invalidate_access_cache` и `_access_view` в `app.pages.admin` и сверяет журнал вызовов.
- **Files modified:** `tests/test_pages/test_admin_panel.py`
- **Verification:** зелёный на дереве; красный на мутанте с обратным порядком.
- **Committed in:** `d4ccd24`

**2. [Rule 1 - Bug] Сборка ответа была бы второй копией**
- **Found during:** задача 1
- **Issue:** повтор вложенного `_fragment` блокировки в тумблере бесплатного доступа дал бы две копии сборки одного ответа.
- **Fix:** сборка вынесена в модульную `_user_actions_response`, и её зовут оба обработчика. Вложенные `_fragment` оставлены, потому что разбор гейтов узнаёт фрагментный обработчик по аргументу `fragment=` и пропускает вложенные сборщики.
- **Files modified:** `app/pages/admin.py`
- **Verification:** `test_block_toggle_over_htmx_refreshes_every_place_of_the_state` и пары блокировки зелёные, гейты htmx зелёные.
- **Committed in:** `4c86a56`

**3. [Rule 1 - Bug] Устаревшая прозa о непереведённой форме бесплатного доступа**
- **Found during:** задача 2
- **Issue:** обоснование параметрической цели `form_wrapper` утверждало, что форма бесплатного доступа не переведена.
- **Fix:** дописано второе поколение, прежний текст сохранён.
- **Files modified:** `tests/test_templates/test_htmx_markup_gates.py`
- **Committed in:** `124cb9e`

---

**Total deviations:** 3 auto-fixed (1 Rule 2, 2 Rule 1).
**Impact on plan:** все три правки держат замысел плана (порядок кэша, один ответ, достоверная проза). Объём не вырос.

## Issues Encountered

- Полную суиту `tests/` исполнитель не запускал: хост с ограниченной памятью. Полный прогон делает оркестратор. Прошли наборы:
  - проверочный набор задачи 1 вместе с `tests/test_admin.py` — `246 passed`;
  - соседние гейты, читающие `admin.py` или `htmx.py` (`test_admin_users`, `test_confirm_delete_transport`, `test_htmx_response_contract`, `test_htmx_response_layer`, `test_htmx_validation_sink`, `test_identifier_bounds`, `test_impersonation_gate`, `test_notices_surface`, `test_origin_guard_on_destructive_routes`, `test_prose_names_live_symbols`, `test_responsive_markup`, `tests/test_application/test_admin_uses_analytics.py`, `test_no_metering_remains.py`) — `348 passed`;
  - проверочный набор задачи 2 — `304 passed`; селектор `swap_target or two_roles or client_state` — `12 passed`; `compileall` чист;
  - `tests/test_templates/` целиком вместе с `test_shell`, `test_account_groups`, `test_profile` после задачи 2 — `612 passed`, rc=0, 13:58.
- Ни один прогон не был убит. Последний набор превысил лимит инструмента в 600 с и был переведён в фон самим инструментом. Я дождался его завершения, код выхода 0.
- Известный красный `test_the_overview_error_number_matches_the_users_own_dashboard` не встретился: работа шла в 19:16–19:50 UTC.
- `graphify update .` выполнен.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Оба тумблера карточки пользователя на слое ответа. Раздел `admin` продолжают следующие планы порядка D-15.
- Третья запись, которую D-08 называет поимённо (`subscribe_to_plan`), приземлится планом 11-15. Она встанет в `DECISION_OWNER_D08`, `OWN_RESPONSE_EXITS_DECLARED` станет 12.
- Окно 63 остаётся `open`.
- Ручной UAT фазы, пункт 5: десять нажатий обоих тумблеров подряд, панели не множатся.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED
