---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 16
subsystem: ui
tags: [htmx, fastapi, jinja2, accounts, hx-location, form_wrapper]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "слой ответа respond() с веткой HX-Location (Фаза 8), реестр пар POST_PAIR_CASES (11-01), form_wrapper без цели (11-15)"
provides:
  - "accounts_retry_sync на respond(): три выхода переходом (/login, /accounts, /accounts/{id}/groups) на обоих транспортах"
  - "три копии формы повторной синхронизации на form_wrapper без цели подмены"
  - "test_retry_sync_over_htmx_lands_by_a_location_header и четыре случая реестра пар"
affects: [11-17, 11-18, 11-19, 11-20]

actuals:
  tokens: 7200
  tasks: 2
  commits: 3
plan_head_before: a8bf7854f8ef4ed88846a88ca32ff13837597d9f

tech-stack:
  added: []
  patterns:
    - "Навигационное действие раздела accounts: все выходы через respond(redirect=...), форма на form_wrapper без target (hx-swap=none)"
    - "Сохранность атрибутов формы при переходе на обёртку доказывается рендером до/после, а не рассуждением"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/accounts/partials/sync_status_card.html
    - tests/test_routes/test_wa_sync_status.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Повторная синхронизация — переход, а не фрагмент (D-02): все три выхода respond(redirect=...), на htmx 204 + HX-Location посимвольно на адреса 302"
  - "Заявку _SYNC_IN_FLIGHT accounts_retry_sync не занимает (проверено по коду: занимает только accounts_sync_groups) — освобождать на выходах HX-Location нечего"
  - "Пары: добавлен четвёртый случай «аккаунт чужой» (T-11-29) сверх трёх в §behavior — край назван в edge_coverage_fallback плана как покрываемый этим планом"
  - "Три копии формы правлены в месте, в макрос не сведены (D-12(в)); старая форма несла только action и method — переносить на обёртку-предка было нечего (замер рендером)"

patterns-established:
  - "Форма в узле, подменяемом опросом (sync_status_card.html), на обёртке без цели — не новая цель свопа; называется комментарием"

requirements-completed: [FORM-04]

coverage:
  - id: D1
    description: "Повторная синхронизация на htmx отвечает 204 + HX-Location на экран групп; без htmx 302 туда же; мост, статус syncing и задача Celery до ответа"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_routes/test_wa_sync_status.py#test_retry_sync_over_htmx_lands_by_a_location_header"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_wa_sync_status.py#test_retry_sync_resets_status"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пары транспортов: успех, аккаунта нет, аккаунт чужой, нет сессии — все LOCATION посимвольно на адрес 302"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[accounts_retry_sync-*]"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_converted_handler_has_a_pair"
        status: pass
    human_judgment: false
  - id: D3
    description: "Три копии формы повторной синхронизации на form_wrapper без цели подмены; атрибуты старой формы и кнопка сохранены"
    requirement: FORM-04
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (77 passed; -k 'disabled_elt or component_macro or swap_target' 14 passed)"
        status: pass
      - kind: other
        ref: "рендер /accounts, /accounts/partial, /accounts/{id}/sync-status до и после: lost attrs [], button identical True"
        status: pass
    human_judgment: false
  - id: D4
    description: "Числа прогонами: NOT_YET_CONVERTED 17→16, пары 33→37, вызовы перехода 60→63, скрытые вызывающие 17→20, блоки вызова обёртки 9→12"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_backlog_matches_the_declared_count"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_hx_location_destinations.py"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_hidden_callers_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере «Повторить» переводит на экран групп без перезагрузки, Back не предлагает повторить POST; опрос account-row-N и панели удаления не множатся после десятков действий"
    verification: []
    human_judgment: true
    rationale: "Поведение истории браузера и накопление панелей Alpine после многих swap тестами не утверждается — ручной UAT фазы, пункты 5 и 7"

duration: 46min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 16: Повторная синхронизация на HX-Location Summary

**`accounts_retry_sync` отвечает переходом на экран групп на обоих транспортах (htmx: 204 + `HX-Location`, без htmx: прежний 302), а три несведённые копии её формы идут через `form_wrapper` без цели подмены.**

## Performance

- **Duration:** 46 min
- **Started:** 2026-09-16T23:55:44Z
- **Completed:** 2026-09-17T00:41:12Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- **Обработчик.** У `accounts_retry_sync` три выхода, все через `await respond(request, redirect=…)`: «нет сессии» → `/login`, аккаунт не найден (включая чужой и не `wa`/`max`) → `/accounts`, успех → `/accounts/{id}/groups`. Порядок не изменился: `retry_sync` моста, статус `syncing`, коммит и `send_task` Celery выполняются до ответа. `RedirectResponse` в обработчике: 0.
- **Заявка на синхронизацию.** Проверено по коду: `_claim_sync_slot` зовёт только `accounts_sync_groups` (план 11-17). Повторная синхронизация заявку не берёт, поэтому выход через `HX-Location` не может пропустить её освобождение. Это записано в докстринге.
- **Разметка.** Все три копии (`accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`) — `{% call form_wrapper(action=…) %}` с прежней кнопкой, цели нет (`hx-swap="none"`). В `sync_status_card.html` комментарий объясняет, что форма стоит внутри узла, который подменяет опрос, и это не новая цель свопа. Форма удаления, панели подтверждения и опрос `account-row-N` не тронуты.
- **Атрибуты сверены рендером, а не на словах.** `/accounts`, `/accounts/partial` и `/accounts/{id}/sync-status` отрисованы до и после правки для аккаунта в `sync_failed`. До правки у формы было только `{action, method}`: атрибутов `data-*`, `x-*`, `@…` и `:…` нет, переносить на обёртку-предка нечего. После правки: `lost attrs: []`, значения не изменились, `button identical: True` во всех трёх копиях. CSS адресует `.acct-card__actions form` и `form[action$="/delete"]` — `action` обёртка печатает.

## Task Commits

1. **Задача 1 RED: пара на заголовке перехода и четыре случая реестра** — `b944dd1` (test)
2. **Задача 1 GREEN: повторная синхронизация на слое ответа** — `c1cf4cf` (feat)
3. **Задача 2: три копии формы на form_wrapper** — `35aac92` (feat)

## TDD Gate Compliance

- **RED.** Прогон `pytest tests/test_routes/test_wa_sync_status.py tests/test_pages/test_htmx_post_pairs.py -k "location_header or retry_sync or number_of_pair"`: 7 тестов, 6 падений, 1 зелёный (`test_retry_sync_resets_status`). Упали: целевой тест `assert 302 == 204`, четыре случая пар на половине htmx («слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ»), при этом их половины 302 прошли с верным адресом, и число реестра `37 == 33`. Причина в дереве: три литерала `RedirectResponse` в `accounts.py:723/734/752`. Запись собрана из JUnit XML в TAP, `check tdd-red-evidence` вернул `RED_EVIDENCE_OK`.
- **GREEN.** `feat(11-16)` `c1cf4cf` идёт после `test(11-16)` `b944dd1`: 133 теста проверочного набора задачи 1 прошли. REFACTOR не понадобился.

## Числа (каждое поставлено прогоном покрасневшего правила, в летописи — дословный текст отказа)

| Константа | Было → стало | Отказ |
|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | 17 → 16 | `число непереведённых обработчиков стало 16, а в файле записано 17` |
| `POST_PAIR_CASES_DECLARED` | 33 → 37 | `случаев пар в реестре 37, объявлено 33` |
| `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 60 → 63 | `вызовов слоя ответа БЕЗ фрагмента найдено 63, а объявлено 60`; карта назначений не изменилась |
| `MACRO_DEFINITION_SITES_CALLERS_DECLARED` | 17 → 20 | `за перечнем мест определения макросов спрятано вызывающих 20, объявлено 17` (кортеж +3 файла) |
| `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 9 → 12 | `блоков вызова макроса-обёртки разобрано 12, объявлено 9` |

Прибавки по разметке — три, а не одна: сканер считает файлы и блоки вызова, а копий три, и они не сведены (D-12(в)). Цель блокировки у всех трёх общая: компонент кнопки печатает `type="submit"`, поэтому записи в перечне исключений не нужны.

## Files Created/Modified

- `app/pages/accounts.py` — `accounts_retry_sync` на `respond()`, докстринг объясняет, почему заявку освобождать не нужно.
- `app/templates/accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html` — импорт и вызов `form_wrapper`.
- `tests/test_routes/test_wa_sync_status.py` — `test_retry_sync_over_htmx_lands_by_a_location_header` (обе половины на отдельных аккаунтах; проверяются мост, статус и аргументы `send_task`).
- `tests/test_pages/test_htmx_post_pairs.py` — посев и четыре случая `ACCOUNTS_RETRY_SYNC` с подменой моста и очереди; число с летописью.
- `tests/test_pages/test_htmx_gates.py` — ключ снят из `NOT_YET_CONVERTED`, 17 → 16 с летописью.
- `tests/test_pages/test_hx_location_destinations.py` — 60 → 63 с летописью.
- `tests/test_templates/test_htmx_markup_gates.py` — три вызывающих в кортеже обёртки, 17 → 20 и 9 → 12 с летописью.

## Decisions Made

См. `key-decisions` во frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Вызов `respond` без `await`**
- **Found during:** задача 1, GREEN
- **Issue:** `respond` асинхронный; первая правка вернула корутину, и FastAPI ответил 500 (`'coroutine' object is not iterable`). Упали и прежний `test_retry_sync_resets_status`, и половины 302 пар.
- **Fix:** `return await respond(...)` на всех трёх выходах — так же, как в соседних обработчиках.
- **Files modified:** `app/pages/accounts.py`
- **Verification:** проверочный набор задачи 1 — 133 passed.
- **Committed in:** `c1cf4cf`

**2. [Rule 2 - Missing Critical] Четвёртый случай пар «аккаунт чужой»**
- **Found during:** задача 1, RED
- **Issue:** §behavior называет три случая, но `edge_coverage_fallback` плана относит чужой аккаунт к краям этого плана, а T-11-29 (mitigate) требует, чтобы «не найден» уходил на `/accounts` на обоих транспортах.
- **Fix:** добавлен случай `повторная синхронизация — аккаунт чужой`, поэтому реестр вырос 33 → 37, а не до 36.
- **Files modified:** `tests/test_pages/test_htmx_post_pairs.py`
- **Committed in:** `b944dd1`, `c1cf4cf`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical).
**Impact on plan:** обе правки нужны для корректности; объём работы не вырос.

## Issues Encountered

- **Широкий прогон** `tests/test_pages/ tests/test_routes/ tests/test_messengers/` (00:08–00:41 UTC): `1 failed, 2178 passed` за 33:05. Единственный отказ — `tests/test_pages/test_admin_panel.py::test_the_overview_error_number_matches_the_users_own_dashboard`. Это известное ночное окно 00:00–05:00 UTC (обзор считает скользящие 24 часа, дашборд — календарный день читателя; окна 14, 27, 79, 85). Отказ был и до плана, этот план его не вызвал; `admin.py`, `dashboard.py` и `send_analytics.py` не тронуты. Полную суиту целиком исполнитель не запускал — её гоняет оркестратор.
- `tests/test_templates/` целиком: 218 passed. `compileall` без ошибок. Прогоны не прерывались сторожем памяти.
- Номера строк в замере рендера (`parent`) в скрипте сравнения считались неверно; на вывод это не влияет, сравнивались только атрибуты формы и её содержимое.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 11-17 (синхронизация групп, `accounts_sync_groups` с заявкой `_SYNC_IN_FLIGHT`/`finally`) начинает с `NOT_YET_CONVERTED_COUNT = 16`, реестра пар 37 и вызовов перехода 63.
- Ручной UAT фазы, пункты 5 и 7 (раздел accounts: «Повторить», Back, накопление панелей), не проведён — это backstop end-of-phase.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

## Self-Check: PASSED
