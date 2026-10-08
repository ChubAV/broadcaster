---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 19
subsystem: ui
tags: [fastapi, htmx, identifiers, gates, window-51, d-07]

requires:
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "PostIdPath и id_in_column (11-02); снятие входов schedules/ads/admin/accounts (11-02, 11-06, 11-11, 11-17)"
provides:
  - "Пять последних POST-входов окна 51 (тумблер и удаление группы аккаунта, повтор отправки) на PostIdPath с проверкой первым использованием"
  - "VALIDATION_REFUSAL_DIVERGENCES пуст, DECLARED = 0, со сводной летописью 23 → 16 → 14 → 8 → 5 → 0"
  - "Правило пустоты test_no_page_post_input_keeps_a_framework_bound со сличением обхода с _post_handlers и POST_HANDLERS"
  - "Контроли реестра окна 51 (полнота, модуль целиком, обоснования, авторство, пустота) на синтетических входах и записях"
affects: [11-20, window-51, phase-15]

actuals:
  tokens: 23000
  tasks: 2
  commits: 4
plan_head_before: 56e9348cb0f6267a42bf17ff89fc197751d6cff6

tech-stack:
  added: []
  patterns:
    - "Скан замера возвращает пару (входы, обойдённые обработчики); пустота доказывается сличением обхода с независимым разборщиком"
    - "Контроль реестра на синтетическом модуле через _sources_with(tmp_path, {}, …) с антивакуумной правильной парой"

key-files:
  created: []
  modified:
    - app/pages/account_groups.py
    - app/pages/history.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_history_retry.py
    - tests/test_pages/test_htmx_post_pairs.py

key-decisions:
  - "У тумблера и удаления группы ветка «нет» одна (тройной WHERE не нашёл строки), и её адрес собран из account_id пути. Величина вне колонки приземляется на /accounts/{значение}/groups, а не на /accounts. Переход на /accounts выдал бы эту ветку различием заголовка (D-04/D-13)."
  - "Окно 51 в .planning/WINDOWS.md этот план не закрывает: закрытие командой реестра — задача 3 плана 11-20. Пробная отметка была сделана и откачена до коммита."

patterns-established:
  - "Правило пустоты реестра: жалобы помощника на настоящем дереве пусты, обход непуст, совпадает с независимым обходом и объявленным числом"

requirements-completed: [FORM-08]

coverage:
  - id: D1
    description: "Пять входов (account_groups toggle/delete × account_id/group_id, history retry × log_id) проверяют идентификатор первым использованием; величина вне колонки идёт веткой «нет» обработчика"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_post_identifier_is_checked_before_its_first_use"
        status: pass
    human_judgment: false
  - id: D2
    description: "Вне колонки, «нет» и «чужое» неотличимы на обоих транспортах (статус, заголовок перехода, тело), строки не тронуты"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_out_of_column_is_indistinguishable_from_missing_and_foreign"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_out_of_column_is_indistinguishable_from_missing_and_foreign"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_out_of_column_is_indistinguishable_from_missing_and_foreign"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (5 случаев вне колонки)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Реестр окна 51 пуст (DECLARED = 0); пустота не вакуумна: обход сличён с _post_handlers и POST_HANDLERS = 36, синтетический вход с границей краснит помощник поимённо"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_no_page_post_input_keeps_a_framework_bound"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_synthetic_bounded_input_reddens_the_emptiness_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
    human_judgment: false
  - id: D4
    description: "Правила полноты, обоснований и авторства реестра сохраняют зубы на синтетических входах и записях"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_shortened_exception_list_reddens_the_completeness_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_dropping_a_whole_module_reddens_the_completeness_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_an_empty_rationale_reddens_the_rationale_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_self_minted_decision_reddens_the_divergence_authorship_rule"
        status: pass
    human_judgment: false

duration: 67min
completed: 2026-09-17
status: complete
---

# Phase 11 Plan 19: Окно 51 закрыто работой Summary

**Тумблер и удаление группы аккаунта и повтор отправки переведены на `PostIdPath` с проверкой `id_in_column` первым использованием. Реестр расхождений окна 51 опустел (5 → 0). Пустота доказана сличением обхода и синтетическим входом с границей.**

## Performance

- **Duration:** 67 min (из них ~37 min — полный прогон суиты)
- **Started:** 2026-09-17T05:14:12Z
- **Completed:** 2026-09-17T06:21:32Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- **Пять входов.**
  - `account_groups_toggle` и `account_groups_delete`: оба параметра пути теперь на `PostIdPath`.
  - `history_retry`: `log_id` на `PostIdPath`.
  - Проверка стоит до первой выборки. У удаления и повтора — после сверки источника, у тумблера сразу за гардом входа: сверки источника у него нет.
  - Ложный результат не заводит своей ветки, а идёт существующей веткой «нет». У тумблера и удаления это «тройной `WHERE` не нашёл строки», у повтора — «записи нет».
- **Неотличимость проверена целиком, а не по коду.** Сравниваются статус, `location`/`HX-Location` и тело на обоих транспортах.
  - Тумблер: группа вне колонки = группы нет = группа чужая (302/204 на `/accounts/{A}/groups`). Аккаунт вне колонки = аккаунта нет, с точностью до величины в адресе.
  - Удаление: группа вне колонки = группы нет = группа чужая. Это одинаковый фрагмент с узлами снятия из целого пути, путь заменён меткой. Аккаунт вне колонки = аккаунта нет. Ни одна строка не удалена.
  - Повтор: вне колонки = записи нет = запись чужая (302/204 на `/history`, пустое тело). Очередь пуста, слот удержания не армирован.
- **Реестр окна 51 пуст.**
  - `VALIDATION_REFUSAL_DIVERGENCES = ()`, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0`, сводная летопись 23 → 16 → 14 → 8 → 5 → 0.
  - `LIFTING_CONDITION_VALIDATION_REFUSAL` получил поколение «исполнено».
  - Тип записи и правила полноты, обоснований и авторства остались.
- **Пустота не вакуумна.** `test_no_page_post_input_keeps_a_framework_bound` проверяет три вещи:
  - замер обошёл непустое множество POST-обработчиков;
  - оно совпадает с независимым обходом `_post_handlers` (разборщик G-1);
  - их число равно `POST_HANDLERS = 36`.

  Жалоб `_framework_bound_complaints` при этом нет. Помощник краснеет на синтетическом входе в двух записях границы: встроенной `Path(ge=1)` и ввезённой GET-`IdPath` на POST. Тот же обработчик на `PostIdPath` молчит.
- **Контроли на синтетике.** Три контроля опирались на боевые записи. Они переведены на синтетические входы и записи раньше, чем реестр опустел (задача 1). Добавлен отсутствовавший контроль авторства. У каждого контроля сначала прогоняется заведомо правильная пара.

## Task Commits

1. **Задача 1: контроли реестра окна 51 на синтетических входах**
   - `e092c5b` (test, RED)
   - `f837a83` (feat, GREEN): `_framework_bound_scan`, `_framework_bound_complaints`, `_framework_bound_visited_handlers`. Реестр на 5 записях, `test_htmx_gates.py` 48 passed.
2. **Задача 2: пять входов и пустота реестра**
   - `705c782` (test, RED)
   - `146d96c` (feat, GREEN)

**Plan metadata:** отдельными docs-коммитами (SUMMARY, затем STATE/ROADMAP).

## Files Created/Modified

- `app/pages/account_groups.py`: тумблер и удаление на `PostIdPath`, `id_in_column` до тройного `WHERE`. У удаления аккаунт вне колонки не доходит до `_current_listing_has_a_row`.
- `app/pages/history.py`: повтор на `PostIdPath`, `id_in_column` между сверкой источника и `db.get`.
- `tests/test_pages/test_htmx_gates.py`:
  - скан с множеством обойдённых обработчиков;
  - помощник и правило пустоты;
  - пять синтетических контролей;
  - реестр пуст, число 0 с летописью.
- `tests/test_pages/test_identifier_bounds.py`: `outside` у пяти строк матрицы. Поле форматируется подстановками адреса (`{value}`, `{account}`), потому что адрес ветки «нет» собран из пути.
- `tests/test_pages/test_account_groups.py`: две проверки неотличимости (тумблер, удаление).
- `tests/test_pages/test_history_retry.py`: проверка неотличимости повтора.
- `tests/test_pages/test_htmx_post_pairs.py`: пять случаев пар вне колонки, `POST_PAIR_CASES_DECLARED` 43 → 48. Число поставлено прогоном: `случаев пар в реестре 48, объявлено 43`.

## Decisions Made

- **Адрес приземления вне колонки у групп — из пути, а не `/accounts`.** План в `read_first` называл ветку «аккаунта нет» (`redirect="/accounts"`), но у тумблера и удаления её нет. Эта ветка есть только у GET порции. Ветка «нет» у POST одна, и её адрес — `_screen_url(account_id, term)`. Если бы величина вне колонки уезжала на `/accounts`, её можно было бы отличить от несуществующего аккаунта из той же колонки (`/accounts/987654/groups`). Это нарушило бы D-04/D-13, поэтому выбран адрес из пути.
- **Окно 51 в реестре `.planning/WINDOWS.md` не закрыто этим планом.** Задача 3 плана 11-20 прямо требует закрыть его командой `windows fixed 51` и проверяет это грепом. В `files_modified` плана 11-19 `WINDOWS.md` нет. Я выполнил команду и дописал основание, затем прочитал 11-20 и откатил правку до коммита (`git checkout -- .planning/WINDOWS.md`). Окно 51 остаётся `open`. Работа, которая его закрывает, — коммит `146d96c`: реестр пуст, правило пустоты не вакуумно.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Ленивое чтение атрибута после `expire_all` в новых тестах групп**
- **Found during:** задача 2, GREEN.
- **Issue:** `own.id`/`foreign.id` читались после `db_session.expire_all()`, и это давало `MissingGreenlet`. Основные утверждения неотличимости к этому месту уже прошли.
- **Fix:** идентификаторы снимаются до запросов, состояние строк проверяется выборкой.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Committed in:** `146d96c`

**2. [Rule 1 — Plan text] Ветка «аккаунта нет» у POST-обработчиков групп не существует**
- **Found during:** задача 2. Решение и основание — в Decisions Made. Строки матрицы и случаи пар утверждают адрес из пути.

**3. [Scope] Число переходов не двинулось**
- `tests/test_pages/test_hx_location_destinations.py` из `files_modified` не правился. Новых вызовов `respond` нет: ложный результат идёт существующими ветками. `HX_LOCATION_DESTINATION_CALLS_DECLARED = 72` зелено.

**4. [Acceptance selector] Селектор `-k` задачи 2 не выбирает синтетический контроль**
- Критерий `-k "framework_bound or validation_refusal or divergence"` не выбирает `test_control_a_synthetic_bounded_input_reddens_the_emptiness_rule`: в его имени нет ни одной из подстрок. Контроль прогнан отдельным узлом: 1 passed. Имя, заданное планом, не менялось.

---

**Total deviations:** 1 исправление теста, 1 расхождение текста плана с деревом, 2 замечания об объёме и селекторе.
**Impact on plan:** предмет не расширен; неотличимость D-04 сохранена точнее, чем предписывал текст.

## TDD Gate Compliance

- **Задача 1.**
  - **RED** `e092c5b`. Команда `uv run pytest tests/test_pages/test_htmx_gates.py -p no:cacheprovider -q`, rc=1: 48 тестов, 3 падения. Все три — синтетические контроли, упавшие на `assert visited == independent`: «ЗАМЕР ГРАНИЦ ОБОШЁЛ НЕ ТЕ ОБРАБОТЧИКИ… замер [], независимый обход ['app/pages/synthetic_window_51.py::synthetic_act']».
  - Причина в дереве — заглушки `_framework_bound_visited_handlers` → `return set()` и `_framework_bound_complaints` → `return []`.
  - `check tdd-red-evidence` дал `RED_EVIDENCE_OK` для `test_control_a_synthetic_bounded_input_reddens_the_emptiness_rule` и `test_control_a_shortened_exception_list_reddens_the_completeness_rule`.
  - **GREEN** `f837a83`: 48 passed.
- **Задача 2.**
  - **RED** `705c782`. Команда `uv run pytest` по `test_htmx_gates.py`, `test_identifier_bounds.py`, `test_account_groups.py`, `test_history_retry.py` и `test_htmx_post_pairs.py`, rc=1: 329 тестов, 11 падений:
    - `test_no_page_post_input_keeps_a_framework_bound`: пять жалоб «ВХОД POST-ОБРАБОТЧИКА НЕСЁТ ГРАНИЦУ ФРЕЙМВОРКА… (псевдоним IdPath)»;
    - матрица: «Несогласных строк 15 из 81», то есть ровно 5 входов × 3 величины, все `422`;
    - три проверки неотличимости, например `'группа вне колонки': ((422, None, '{"detail":…'), (400, None, ''))`;
    - пять случаев пар: `assert 422 == 302`;
    - реестр пар: `assert 48 == 43`.
  - Причина в дереве — `IdPath` (`Path(ge=1, le=ID_MAX)`) на пяти входах.
  - `RED_EVIDENCE_OK` для `test_no_page_post_input_keeps_a_framework_bound`, `test_every_bounded_input_refuses_a_value_outside_the_column`, `test_toggle_out_of_column_is_indistinguishable_from_missing_and_foreign` и `test_retry_out_of_column_is_indistinguishable_from_missing_and_foreign`.
  - **GREEN** `146d96c`: набор проверки задачи 404 passed.
  - Сдвиг числа реестра снят отдельными прогонами на переведённом дереве:
    - помощник полноты на прежнем перечне из `705c782` дал ровно пять жалоб «ОБЪЯВЛЕН, НО ЗАМЕРОМ НЕ НАЙДЕН»;
    - правило числа при прежнем `5` дало `assert 0 == 5`.
- REFACTOR-коммитов нет.

## Verification

- `uv run pytest` по `test_htmx_gates.py`, `test_identifier_bounds.py`, `test_account_groups.py`, `test_history_retry.py`, `test_confirm_delete_transport.py`, `test_htmx_post_pairs.py` и `test_hx_location_destinations.py`: 404 passed.
- `-k "checked_before_its_first_use"`: 1 passed.
- `tests/test_routes/test_schedules_api_identifier_bounds.py`: 19 passed (JSON-API не тронут, D-07).
- `uv run python -m compileall -q app main.py tests`: OK.
- **Полный прогон** `uv run pytest tests/ -q` на `146d96c`: **3401 passed**, rc=0, 37 мин. Прогон не прерывался. Известный ночной красный тест админки не встретился: время прогона 05:44–06:21 UTC.
- `graphify update .`: выполнено.
- Грепы: `^VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0$` — одна строка; `_ValidationRefusalDivergence(` в перечне — 0.
- 422 GET-курсора в `test_account_groups.py` не тронут.

## Issues Encountered

- Замечание, не дефект: адрес приземления пути деградации для аккаунта вне колонки — `/accounts/2147483648/groups`. Следующий GET по нему отвечает `422` по контракту GET (граница на сигнатуре, вне окна 51). У несуществующего аккаунта из колонки GET уводит на `/accounts`. Второй шаг различает только диапазон величины, который публичен, а не наличие или владение строкой. Сам POST-ответ неотличим.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Готово для 11-20: окно 51 можно отметить `fixed` командой реестра. Работа — `146d96c`, доказательство — правило пустоты и синтетический контроль.
- Требование FORM-08 остаётся `Pending` в REQUIREMENTS.md до верификации фазы.

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-17*

## Self-Check: PASSED

- Файлы на месте: `app/pages/account_groups.py`, `app/pages/history.py`, `tests/test_pages/test_htmx_gates.py`, SUMMARY.
- Коммиты найдены: `e092c5b`, `f837a83`, `705c782`, `146d96c`, `a936dfc` (SUMMARY).
- `git rev-list --count 56e9348..146d96c` = 4 (задачные коммиты); `tests/test_planning/` после правок STATE/ROADMAP: 44 passed.
