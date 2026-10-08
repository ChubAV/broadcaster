---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 14
subsystem: ui
tags: [htmx, notices, admin, queue, gates, records]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-11: адрес ветки идентификатора вне колонки у снятия задачи (/admin/queue с частным ключом исхода) — третье из трёх мест записи"
  - phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
    provides: "закрытый реестр уведомлений, области шелла, гейт снятых написаний RETIRED_QUERY_KEYS (D-09, D-10, D-12)"
provides:
  - "четыре кода реестра исходов снятия задачи: QUEUE_DROP_REMOVED / MISSING / UNAVAILABLE / NO_QUEUE"
  - "QUEUE_DROP_NOTICE_CODES в app/pages/admin.py: исход сервиса → код реестра"
  - "admin_drop_task отвечает respond(notice=…) на всех трёх выходах; admin_queue не читает параметр исхода"
  - "шестой элемент RETIRED_QUERY_KEYS с летописью и отрицательным контролем на новом ключе"
affects: [11-15, 11-16, 11-17, 11-18, 11-19, 11-20, 15-gate-09]

actuals:
  tokens: 8400
  tasks: 2
  commits: 4
plan_head_before: baaefa93f58a4746243bc3c0d6cc0d6a2a313b04

tech-stack:
  added: []
  patterns:
    - "Частный словарь исходов замещается кодами реестра с посимвольным переносом текста И варианта; модуль раздела держит только отображение исхода сервиса в код"
    - "RED гейта снятого написания измеряется на дереве ДО перевода во временном рабочем каталоге с новым файлом гейта, а не git stash"

key-files:
  created: []
  modified:
    - app/pages/notices.py
    - app/pages/admin.py
    - app/templates/admin/queue.html
    - app/templates/includes/notice_area.html
    - app/pages/billing.py
    - tests/test_pages/test_confirm_delete_transport.py
    - tests/test_pages/test_admin_panel.py
    - tests/test_pages/test_notices_registry.py
    - tests/test_pages/test_notices_channel.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_components.py
    - .planning/PROJECT.md

key-decisions:
  - "11-14: исход «у аккаунта нет очереди» в QUEUE_DROP_NOTICE_CODES не входит — сервис его не выдаёт, код называет ветка обработчика до обращения к сервису"
  - "11-14: варианты предупреждения у «задача уже ушла» и «у аккаунта нет очереди» НЕ сменены на ошибку, хотя теперь эти отказы едут в площадку приземления фокуса — D-10 переносит текст И вариант; запись шапки notice_area.html и PANEL_REFUSAL_CODES получили поколение, а новое утверждение измеряется перечнем PANEL_POLITE_REFUSAL_CODES"
  - "11-14: транспорт снятия задачи остаётся переходом (HX-Location), queue_row.html не тронут — ключ панели очереди остаётся позицией строки (D-06/D-09 Фазы 10, WR-04, D-03)"

patterns-established:
  - "Запись, ставшая шире поведения из-за правки плана, получает поколение в том же коммите, что и правка, и её новое утверждение закрепляется перечнем, а не прозой"

requirements-completed: [FORM-04]

coverage:
  - id: D1
    description: "Снятие задачи приземляет на /admin/queue с кодом реестра ?notice= на обоих транспортах (302 без htmx; 204 и HX-Location с htmx) во всех четырёх исходах и в ветке идентификатора вне колонки"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_confirm_delete_transport.py#test_every_confirmed_delete_route_answers_both_transports[admin_drop_task-*]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_confirm_delete_transport.py#test_a_missing_identifier_is_answered_exactly_like_a_success[admin_drop_task]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
    human_judgment: false
  - id: D2
    description: "Исход снятия рисуется общей областью уведомлений шелла, страница по старому ключу не рисует ничего"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_a_dropped_queue_task_is_announced_by_the_shell_notice_area"
        status: pass
    human_judgment: false
  - id: D3
    description: "Четыре текста и варианта перенесены в реестр посимвольно; частный словарь и место отрисовки сняты"
    requirement: FORM-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_notices_registry.py#test_every_moved_text_matches_its_source_character_for_character"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_registry.py#test_the_moved_queue_drop_outcomes_keep_their_variants"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_registry.py#test_the_registry_carries_every_declared_code"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ноль вхождений ?result= в app/, утверждённый гейтом снятых написаний с доказанными зубами"
    requirement: FORM-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_notices_channel.py#test_no_retired_query_key_remains[?result=]"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_channel.py#test_control_negative_a_returned_queue_outcome_key_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D5
    description: "Комментарий billing.py, докстринг notices.py и пункт §Active PROJECT.md говорят то, что сделано"
    verification:
      - kind: other
        ref: "grep -n 'ЧЕТЫРЕ' app/pages/billing.py; grep -n '11-14' .planning/PROJECT.md; uv run pytest tests/test_planning/ -q"
        status: pass
    human_judgment: true
    rationale: "Истинность прозы записи (что прежняя формулировка названа, а не стёрта, и новая не шире сделанного) грепом не судится — нужен читатель"
  - id: D6
    description: "Исход снятия задачи виден администратору на живой странице очереди после htmx-перехода (плашка и её тон в области шелла)"
    verification: []
    human_judgment: true
    rationale: "Отрисовка после подмены тела документа по HX-Location в браузере тестами на httpx не наблюдается; приземление фокуса на пути перехода отложено GATE-09 Фазы 15"

duration: 57min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 14: Свод исходов снятия задачи из очереди в закрытый реестр уведомлений Summary

**Шестой частный микро-контракт адресной строки сведён: четыре исхода снятия задачи — коды `app/pages/notices.py` с посимвольно перенесёнными текстами и вариантами, `admin_drop_task` отвечает `respond(notice=…)`, частный словарь и место отрисовки на `admin/queue.html` сняты, `?result=` в `app/` — ноль под гейтом `RETIRED_QUERY_KEYS` с доказанными зубами.**

## Performance

- **Duration:** 57 min
- **Started:** 2026-09-16T20:31:07Z
- **Completed:** 2026-09-16T21:28:16Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Все три места записи частного ключа переведены, включая самое новое: ветку идентификатора вне колонки из плана 11-11 (`app/pages/admin.py:1157` на `baaefa9`, адрес `/admin/queue` с ключом `unknown_account`). Замер до плана: `grep -rn '?result=' app/` = 3; после: 0.
- `QUEUE_DROP_REMOVED` / `QUEUE_DROP_MISSING` / `QUEUE_DROP_UNAVAILABLE` / `QUEUE_DROP_NO_QUEUE` заведены с текстами и вариантами (success / warning / error / warning), скопированными символ в символ из снятого `QUEUE_DROP_RESULTS`. Посимвольное равенство утверждают `MOVED_TEXTS` (11 → 15 строк) и новое правило вариантов.
- `QUEUE_DROP_NOTICE_CODES` отображает исход сервиса в код; адрес с кодом собирает только `_with_notice`. Журналы `queue_task_drop_failed`/`queue_task_dropped` не тронуты.
- `admin_queue` больше не принимает параметр исхода; в `admin/queue.html` на месте блока отрисовки — однострочный комментарий Jinja.
- Транспорт остался переходом: `admin/includes/queue_row.html` не тронут, id и макросов не получил (D-03, WR-04).
- Гейт снятых написаний: шестой ключ `?result=` с летописью, плюс отрицательный контроль, который подставляет старое написание в модуль админки в памяти.
- `billing.py`: прежний абзац «Три частных реестра… Копий не осталось ни одной» сохранён и назван устаревшим; дописано, что реестров было ЧЕТЫРЕ и что с плана 11-14 копий не осталось. Пункт §Active в `PROJECT.md` отмечен `[x]` со ссылкой на план.

## Task Commits

1. **Задача 1 RED: случаи снятия задачи ждут кодов реестра** — `69a6e26` (test)
2. **Задача 1 GREEN: коды реестра, перевод обработчика, снятие словаря и отрисовки** — `d285954` (feat)
3. **Задача 2 RED: гейт снятых написаний с шестым ключом и контролем** — `cdaffab` (test)
4. **Задача 2 GREEN: записи приведены к истине** — `5f4653f` (feat)

**Plan metadata:** отдельным коммитом `docs(11-14)` после этой сводки.

## TDD Gate Compliance

- **Задача 1 RED** (`69a6e26`): прогон `test_confirm_delete_transport.py test_admin_panel.py test_notices_registry.py test_identifier_bounds.py` дал `11 failed, 216 passed`. Все 11 падений причинные, по сообщениям из JUnit: адрес `'/admin/queue?result=removed'` вместо `'/admin/queue?notice=queue_drop_removed'` (×4 исхода, ветка отсутствующего идентификатора, регрессия админки, строка матрицы границы), а также «пропавшие: queue_drop_*» и «записи нет в реестре вовсе» для правил реестра. Записи RED построены из JUnit XML и переведены в TAP (227 тестов, 216 pass, 11 fail); `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`) для `test_a_dropped_queue_task_is_announced_by_the_shell_notice_area` и для `test_a_missing_identifier_is_answered_exactly_like_a_success[admin_drop_task]`. Код выхода 1 выведен из JUnit (failures=11, errors=0), потому что вывод прогона шёл через фильтр.
- **Задача 2 RED** (`cdaffab`): на текущем дереве гейт зелёный по замыслу плана, ведь старое написание сняла задача 1. Поэтому RED измерен на ДЕРЕВЕ ДО ПЕРЕВОДА. Для этого создан временный отсоединённый рабочий каталог `git worktree` на `69a6e26`, где в `app/pages/admin.py` 3 вхождения `?result=`. Туда скопирован новый файл гейта, прогон шёл интерпретатором проекта. Результат: `FAILED tests/test_pages/test_notices_channel.py::test_no_retired_query_key_remains[?result=]`, `1 failed, 5 passed`, rc=1, сообщение «снятое написание '?result=' вернулось в ['app/pages/admin.py']». `check tdd-red-evidence` вернул `RED_EVIDENCE_OK`. Рабочий каталог удалён (`git worktree remove`), основное дерево не трогалось, `git stash` не использовался. На настоящем дереве после плана: `[?result=]` PASSED, новый отрицательный контроль PASSED. Контроль сначала утверждает, что в настоящем модуле старого написания нет, и только потом подставляет его в память и ждёт попадания ровно в `app/pages/admin.py`. Значит, ноль не вакуумный: скан действительно читает модуль, где ключ жил.
- GREEN-коммиты `d285954` и `5f4653f` идут после своих RED-коммитов.

## Files Created/Modified

- `app/pages/notices.py`: четыре кода и записи; докстринг называет шестое снятое написание описательно.
- `app/pages/admin.py`: `QUEUE_DROP_RESULTS` заменён на `QUEUE_DROP_NOTICE_CODES`, три выхода переведены на `respond(notice=…)`, у комментария о шестом микро-контракте поколение «сведён планом 11-14», у `admin_queue` снят параметр исхода.
- `app/templates/admin/queue.html`: снято собственное место отрисовки исхода.
- `app/templates/includes/notice_area.html`: пункт «оба кода отказа… несут вариант ошибки» получил поколение (см. отклонения).
- `app/pages/billing.py`: абзац о частных реестрах получил поколение «их было ЧЕТЫРЕ».
- `tests/test_pages/test_confirm_delete_transport.py`: случаи снятия переведены на `outcome_key="notice"` и константы реестра, неиспользуемый ввоз `DROP_*` снят, старая запись о ключе помечена устаревшей.
- `tests/test_pages/test_admin_panel.py`: регрессия «исход рисует область шелла, старый ключ не рисует ничего».
- `tests/test_pages/test_notices_registry.py`: `DECLARED_CODES` +4, `MOVED_TEXTS` +4, новое правило вариантов, число записей 15 → 19.
- `tests/test_pages/test_notices_channel.py`: `RETIRED_QUERY_KEYS` +`?result=` с летописью и контроль на новом ключе.
- `tests/test_pages/test_identifier_bounds.py`: ожидание `outside` у строки снятия задачи переведено на код реестра.
- `tests/test_pages/test_hx_location_destinations.py`: в докстринге пример ключа теперь `?notice=…`.
- `tests/test_templates/test_components.py`: в `PANEL_REFUSAL_CODES` добавлен `QUEUE_DROP_UNAVAILABLE`, новый перечень `PANEL_POLITE_REFUSAL_CODES` утверждается тем же правилом.
- `.planning/PROJECT.md`: пункт §Active закрыт ссылкой на план 11-14.

## Decisions Made

См. `key-decisions` во frontmatter. Главное: у двух исходов вариант предупреждения сохранён, потому что D-10 переносит его вместе с текстом. Цену этого решения шапка области уведомлений теперь называет прямо, а не прячет.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Строка матрицы границы идентификатора ждала старый адрес**
- **Found during:** Задача 1 (RED)
- **Issue:** `tests/test_pages/test_identifier_bounds.py` (в `files_modified` плана его нет) утверждал `outside="302 /admin/queue?result=unknown_account"`. Перевод ветки план 11-11 заранее отдал этому плану (запись в `test_htmx_gates.py`).
- **Fix:** ожидание переведено на `302 /admin/queue?notice=queue_drop_no_queue` в RED-коммите.
- **Files modified:** tests/test_pages/test_identifier_bounds.py
- **Verification:** RED — строка несогласна («Несогласных строк 3 из 81»); GREEN — правило зелёное.
- **Committed in:** `69a6e26`

**2. [Rule 3 - Blocking] Реестровые перечни и счётчик записей, которых план не называл**
- **Found during:** Задача 1
- **Issue:** `DECLARED_CODES` требует равенства состава реестра. Число записей в `test_every_code_is_distinct_and_the_index_loses_nothing` было 15, и первая строка его докстринга ещё до плана отставала от числа («Четырнадцать»).
- **Fix:** +4 кода в перечень, +4 копии текстов в `MOVED_TEXTS`, правило вариантов. Число 15 → 19 поставлено прогоном покрасневшего правила («записей в реестре 19, ожидалось 15»), с летописью. Отставший докстринг исправлен с пометкой.
- **Files modified:** tests/test_pages/test_notices_registry.py
- **Committed in:** `69a6e26` (перечни), `d285954` (число)

**3. [Rule 1 - Bug / records] Запись шапки области уведомлений стала шире поведения из-за этого плана**
- **Found during:** Задача 1, при чтении шапки `includes/notice_area.html` перед прогоном `tests/test_templates/`
- **Issue:** запись утверждала, что на пути перехода панель подтверждения способна выдать ровно два кода отказа (перезапуск воркера) и оба несут вариант ошибки, то есть в площадку приземления фокуса не попадают. Комментарий у `PANEL_REFUSAL_CODES` называл перезапуск «единственным подтверждением, чей обработчик уводит человека с кодом исхода». С этим планом кодом уводит и снятие задачи: у него три кода отказа, и два из них с вариантом предупреждения едут в вежливую область, то есть В ПЛОЩАДКУ. Гейты при этом оставались зелёными: правило читает перечень, который об этом не знал.
- **Fix:** обеим записям дописано поколение, прежние формулировки процитированы, а не стёрты. `QUEUE_DROP_UNAVAILABLE` добавлен в `PANEL_REFUSAL_CODES`. Новый перечень `PANEL_POLITE_REFUSAL_CODES` утверждает, что два отказа-предупреждения действительно не несут варианта ошибки. Сами варианты не менялись: D-10 это запрещает.
- **Files modified:** app/templates/includes/notice_area.html, tests/test_templates/test_components.py
- **Verification:** `tests/test_templates/` 218 passed до правки и после неё; полный прогон зелёный.
- **Committed in:** `d285954`

**4. [Rule 2 - Records] Докстринг `notices.py` называл снятых написаний пять**
- **Found during:** Задача 2
- **Fix:** дописана строка о шестом, названном описательно, без литерала: гейт читает `app/` текстом.
- **Committed in:** `5f4653f`

---

**Total deviations:** 4 auto-fixed (2 blocking, 1 records bug, 1 records completeness)
**Impact on plan:** все правки нужны, чтобы тесты и записи совпадали с деревом после свода. Транспорт, `queue_row.html` и тексты не менялись.

## Issues Encountered

- `tests/test_pages/test_htmx_gates.py:3024` в летописи Фазы 11 (план 11-11) приводит старый адрес ветки со словами «адрес этой ветки переводит план 11-14». Это верная историческая запись в `tests/`, гейт её не видит, поэтому она не правилась.
- Известное окно `test_the_overview_error_number_matches_the_users_own_dashboard` (00:00–05:00 UTC) не встретилось: прогоны шли в 20:31–21:27 UTC.

## Verification

- Проверочный набор задачи 1 (`test_confirm_delete_transport`, `test_admin_panel`, `test_notices_registry`, `test_notices_surface`, `test_hx_location_destinations`, `test_htmx_gates`, `test_htmx_post_pairs`, а также `test_identifier_bounds` и `test_notices_channel`): 379 passed + 1 падение счётчика, исправленное (отклонение 2); после исправления `test_notices_registry` 15 passed, `-k drop` 5 passed.
- `tests/test_templates/` полностью: 218 passed. После правки `test_components.py` вместе с `test_notices_channel.py` и `test_admin_panel.py`: 403 passed.
- Задача 2: `test_notices_channel.py tests/test_planning/ test_billing_section.py` 160 passed; после правки докстринга реестра `test_notices_channel test_notices_registry tests/test_planning/` 116 passed.
- Счётчики, которые правка могла сдвинуть: `NOTICE_WRITE_PLACES` (4) не сдвинулся, потому что новые выходы передают код параметром и адрес руками не склеивают; `HX_LOCATION_DESTINATION_CALLS_DECLARED` не сдвинулся (правило зелёное); `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` зелёный.
- **Полный прогон `uv run pytest tests/`** на `5f4653f`: **3340 passed, rc=0, 36 мин 22 с** (запущен штатным фоновым режимом, не прерывался).
- `graphify update .` выполнен.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Готово к 11-15. Раздел `admin` больше не держит ни одного частного ключа исхода.
- Требование FORM-04 в REQUIREMENTS.md оставлено `Pending`: верификация Фазы 11 не пройдена.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED
