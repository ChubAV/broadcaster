---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 04
subsystem: testing
tags: [pytest, ast, htmx, templates, inventory-gate, fetch-03]

requires:
  - phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
    provides: "ноль `fetch(` в шаблонах (план 13-01) и долг 13-05 о счёте простых атрибутов-обработчиков"
  - phase: 08
    provides: "группа G-22 — убывающий счётчик `MANUAL_FETCH_*`, сеть `MANUAL_FETCH_CALL`, обход `_manual_fetch_places`"
provides:
  - "ЗАПРЕТ FETCH-03 `test_fetch_prohibition_forbids_manual_request_assembly_in_templates` — отсутствие предмета, а не равенство числу"
  - "летопись имени `test_no_manual_fetch_remains`, утверждаемая разбором `ast`"
  - "инвентарь простых атрибутов-обработчиков события: 1 место, `components/thumb.html#0` (`onerror`)"
affects: [15-verification, GATE-08-chronicle, FETCH-03]

actuals:
  tokens: 8932
  tasks: 2
  commits: 4
plan_head_before: ea13b3bd11962941fc1a03ea36b233cfd186e079

tech-stack:
  added: []
  patterns:
    - "запрет рядом со счётчиком: другой речевой акт над той же сетью, зелень запрета всегда в паре с непустотой вселенной"
    - "RED инвентаря: перечень мест объявлен пустым, чтобы правило назвало место, которое сеть видит"
    - "летопись имени мерится определениями `ast`, а не текстом — абзац не называет свидетеля сам"

key-files:
  created: []
  modified:
    - tests/test_templates/test_htmx_inventory.py

key-decisions:
  - "Имя функции-запрета `test_fetch_prohibition_forbids_manual_request_assembly_in_templates` — не равно объявленному `test_no_manual_fetch_remains`, называет речевой акт"
  - "`_strip_comments` переиспользован из этого же модуля (:318), а не импортирован из `test_htmx_markup_gates.py` — одноимённый дубль с тем же телом"
  - "`import ast` локально в помощнике: импорт в шапке сдвинул бы номера строк, цитируемые летописью `REQUIREMENTS.md` §GATE-08"
  - "Разность «сырой текст / без комментариев» утверждена на грубом грепе `onerror` (1 → 0), а несущесть вырезания для самой сети — синтетикой: сеть с `=` сегодняшними комментариями не обманывается"

requirements-completed: [FETCH-03]

coverage:
  - id: D1
    description: "ЗАПРЕТ ручной сборки запроса в `app/templates/` сформулирован как отсутствие предмета, с непустотой вселенной в том же правиле"
    requirement: FETCH-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_fetch_prohibition_forbids_manual_request_assembly_in_templates"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_negative_a_synthetic_manual_fetch_breaks_the_fetch_prohibition"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_positive_the_untouched_tree_keeps_the_fetch_prohibition_silent"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_positive_an_empty_tree_satisfies_the_fetch_prohibition_only_vacuously"
        status: pass
    human_judgment: false
  - id: D2
    description: "Точность сети запрета: `.fetch(`, `_fetch(`, `-fetch(`, `prefetch(` — по 0 находок, голый `fetch(` — 1"
    requirement: FETCH-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_precision_the_fetch_prohibition_net_ignores_four_lookalike_forms"
        status: pass
    human_judgment: false
  - id: D3
    description: "Летопись имени `test_no_manual_fetch_remains`: не определено нигде, три правила G-22 и функция-запрет определены в модуле (замер `ast`)"
    requirement: FETCH-03
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_fetch_prohibition_name_chronicle_is_measured_by_the_syntax_tree"
        status: pass
    human_judgment: false
  - id: D4
    description: "Инвентарь простых атрибутов-обработчиков события: ровно 1 место `components/thumb.html#0` (`onerror`) с основанием; счёт без комментариев; перечень 8 имён объявлен числом"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_inline_event_attribute_places_are_the_declared_ones"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_inline_event_attribute_count_ignores_comments"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_inline_event_attribute_net_covers_the_declared_event_names"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_negative_a_synthetic_onclick_grows_the_inline_event_attribute_count"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_positive_the_untouched_tree_keeps_the_inline_event_attribute_count"
        status: pass
    human_judgment: false
  - id: D5
    description: "Находка об отметке `[x]` GATE-08 записана в докстринге группы; отметка не снята"
    verification: []
    human_judgment: true
    rationale: "Верность формулировки находки и то, что отметка следует вердикту отчёта своей фазы, — суждение владельца; правило этого не утверждает"

duration: 13min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 04: ЗАПРЕТ FETCH-03 и инвентарь атрибутов-обработчиков Summary

**Запрет `test_fetch_prohibition_forbids_manual_request_assembly_in_templates` (отсутствие предмета над переиспользованной сетью G-22, с непустотой вселенной и тремя контролями от вакуума), летопись имени `test_no_manual_fetch_remains`, измеренная `ast`, и инвентарь простых атрибутов-обработчиков: одно место `components/thumb.html#0` (`onerror`)**

## Performance

- **Duration:** 13 min
- **Started:** 2026-09-24T07:32:47Z
- **Completed:** 2026-09-24T07:45:30Z
- **Tasks:** 2
- **Files modified:** 1 (код); записи: `.planning/REQUIREMENTS.md`, `.planning/WINDOWS.md` — коммитом записи

## Accomplishments

- **Имя функции-запрета:** `tests/test_templates/test_htmx_inventory.py::test_fetch_prohibition_forbids_manual_request_assembly_in_templates`. Её утверждение — `assert not found` по `_manual_fetch_places(_template_sources())`, а не `len(found) == MANUAL_FETCH_PLACES`. Непустота вселенной (> 50 шаблонов, на дереве 113) утверждается тем же правилом.
- **Числа контроля точности сети:** `.fetch(` → 0, `_fetch(` → 0, `-fetch(` → 0, `prefetch(` → 0; голый `fetch(` → 1 (`synthetic/bare.html#0`). Отказ называет просочившуюся форму.
- **Контроли от вакуума:** синтетический ключ `synthetic/fetch_prohibition_probe.html` (`assert key not in sources`, `assert changed != sources`, запрет находит и называет `…#0`, `assert not (not found)`); положительный на неизменённом дереве; пустота (`{}` и дерево из одного шаблона) засекается порогом вселенной.
- **Летопись имени `test_no_manual_fetch_remains`** (в баннере группы FETCH-03, форма D-30/D-32):
  - имя объявлено в `REQUIREMENTS.md` §GATE-08 и в критерии 2 ROADMAP §Phase 15;
  - замер 2026-09-23 (планирование, `15-RESEARCH.md` §Ф-06): вхождений в `tests/` — НОЛЬ;
  - перезамер 2026-09-24: текстовых вхождений одно (комментарий D-05 в `test_plan_prohibitions_census.py`, план 15-01), определений — НОЛЬ; поэтому летопись мерится определениями `ast`;
  - до Фазы 15 принуждение жило тремя правилами G-22: `test_manual_request_assembly_never_grows` (:1159), `test_manual_request_assembly_matches_the_declared_count` (:1176), `test_the_declared_manual_fetch_ceiling_never_rises` (:1201), и это был счётчик, а не запрет;
  - теперь имя закрыто функцией-запретом, названной выше;
  - дословно: «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: …Записи разведки (`.planning/research/*`) НЕ ПРАВЯТСЯ.»
- **Отметка `[x]` у GATE-08 НЕ снималась.** Находка записана отдельным абзацем баннера: формально отметка законна, по существу это «зелено вакуумом». Адресат правки записи — план `15-06`, который её сделал (`REQUIREMENTS.md:73-74`). Этот план дописал в конец строки 73 только имя функции (handoff, window 100).
- **Инвентарь атрибутов-обработчиков:** `INLINE_EVENT_ATTRIBUTE_PLACES = 1`. Единственное место — `components/thumb.html#0` → `onerror`, с основанием: подменяет упавшую миниатюру полным изображением и снимает себя первым действием. Перечень имён `INLINE_EVENT_NAMES` содержит 8 имён (`INLINE_EVENT_NAMES_DECLARED = 8`). Счёт идёт по исходнику без комментариев, разметка не тронута.
- Потолок Фазы 8 (`MANUAL_FETCH_CEILING_AT_PHASE_08`) не тронут: вхождений в файле 7 до и 7 после. Во всех четырёх коммитах задач только добавления: 0 строк с одиночным `-`, 618 вставок.

## Task Commits

1. **Задача 1 RED: летопись имени мерится `ast` до появления запрета** — `b8b084a7` (test)
2. **Задача 1 GREEN: запрет FETCH-03 и четыре контроля** — `f047d904` (feat)
3. **Задача 2 RED: инвентарь с пустым перечнем мест** — `8aebd852` (test)
4. **Задача 2 GREEN: объявлено место `thumb.html#0` с основанием** — `6db1a6b3` (feat)

**Plan metadata:** коммит сводки (этот) и коммит записи (STATE/ROADMAP/REQUIREMENTS/WINDOWS)

## Files Created/Modified

- `tests/test_templates/test_htmx_inventory.py` — две новые группы после G-22:
  - **группа FETCH-03:** `FETCH_PROHIBITION_RULE`, `FETCH_PROHIBITION_DECLARED_NAME`, `MANUAL_FETCH_COUNTER_RULES`, `_suite_sources`, `_defined_functions`, `FETCH_PROHIBITION_UNIVERSE_FLOOR`, `_fetch_prohibition_universe_offence`, `FETCH_NET_LOOKALIKES`, 6 правил;
  - **группа инвентаря:** `InlineEventSite`, `INLINE_EVENT_NAMES(_DECLARED)`, `INLINE_EVENT_ATTRIBUTE`, `NAIVE_ONERROR_GREP`, `INLINE_EVENT_ATTRIBUTE_PLACES`, `INLINE_EVENT_ATTRIBUTE_SITES`, `_inline_event_attribute_places`, 5 правил.

## Decisions Made

- Имя запрета называет речевой акт и не равно объявленному имени, иначе расхождение было бы закрыто подгонкой.
- Границу `app/static/` закрывают правила, названные по имени:
  - `test_components.py::test_criterion_three_holds_by_the_numbers` — множество вендоренных сценариев;
  - `test_shell.py::test_vendored_htmx_is_the_declared_artifact` — SHA-384 htmx.

  Байтового закрепления `alpine.min.js` в суите нет (замер), и это записано в «ЧЕГО ЭТА ГРУППА НЕ УТВЕРЖДАЕТ».
- Изъятия инвентаря названы по имени:
  - `hx-on:` / `hx-vals='js:'` закрывает `test_htmx_markup_security.py::test_no_markup_declares_request_parameters_or_event_handlers` (GATE-07);
  - `x-on:` / `@` отсечены просмотром назад по объявлению;
  - имена вне перечня 8 сетью не видны; сеть «`on` + любое имя» на дереве дала то же одно место.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `_strip_comments` не импортирован, а переиспользован из самого модуля**
- **Found during:** Задача 2
- **Issue:** План велит импортировать `_strip_comments` из `test_htmx_markup_gates.py:365`. Но `test_htmx_inventory.py` уже определяет одноимённую функцию с тем же телом и порядком (`:318`), и импорт затенил бы её.
- **Fix:** Используется модульная функция; своего `re.sub` не написано. `grep -c _strip_comments` = 11.
- **Committed in:** `8aebd852`

**2. [Rule 1 - Замер] Посылка о `modal.html` уточнена измерением**
- **Found during:** Задача 2
- **Issue:** План утверждает, что «наивная сеть» на `modal.html` даёт 1, а без комментариев 0. Замер показал три вещи:
  - сеть `on(…)=`, требующая `=`, даёт на `modal.html` 0 и на сыром тексте;
  - «1 → 0» верно только для грубого грепа слова `onerror`;
  - грубый греп всего перечня имён даёт на `modal.html` 2 — ещё `xhr.onload` на `:126`, которого замер плана не называл.
- **Fix:** Правило утверждает измеренные числа: `onerror` 1 → 0 с разностью 1, перечень 2 → 0, сеть 0 → 0. Несущесть вырезания для самой сети доказана синтетикой: комментарий с `onerror="…"` и `onclick="…"` даёт 2 на сыром тексте и 0 без комментариев.
- **Committed in:** `8aebd852`

**3. [Rule 1 - Согласованность ключа] Ключ места `components/thumb.html#0`, а не `#1`**
- **Issue:** План пишет `#1`, но ключи модуля нумеруются с нуля (`ads/form.html#0`, `_poll_fragments`, `_manual_fetch_places`).
- **Fix:** Ключ `#0` — та же форма, что у соседних инвентарей.

**4. [Rule 1 - Замер] Базовые числа селекторов верификации**
- **Issue:** План считал, что `-k "no_manual_request_assembly or fetch_prohibition or manual_fetch"` уже выбирает 6 тестов, а `-k control` — 5. Замер до правки: 3 и 7 (правила G-22 под эти подстроки не попадают).
- **Fix:** Пороги выполнены замером после правки: 9 (≥ 9) и 13 (≥ 8). Файл: 30 (≥ 19), `tests/test_templates/`: 286 (≥ 236).

**5. [Rule 1 - Замер] «Вхождений имени НОЛЬ» устарело к исполнению**
- **Issue:** Комментарий группы D-05 плана 15-01 цитирует `test_no_manual_fetch_remains`, так что текстовых вхождений уже одно.
- **Fix:** Летопись записывает оба замера и мерит определения `ast`. Дополнительно утверждается, что текстовые вхождения есть: греп нашёл бы «свидетеля» в самой летописи.

**6. [Rule 2 - Сохранность ссылок] `import ast` локально**
- **Issue:** Импорт в шапке сдвинул бы все номера строк, цитируемые в `REQUIREMENTS.md` §GATE-08.
- **Fix:** Импорт стоит внутри `_defined_functions`, и это записано в её докстринге. Проверено: `:1108`, `:1111`, `:1159`, `:1176`, `:1201` указывают на те же строки.

**7. [Handoff оркестратора] Имя функции дописано в летопись GATE-08, window 100 закрыто**
- В конец строки `.planning/REQUIREMENTS.md:73` добавлено предложение «Имя вписано по сводке плана `15-04`…» с путём модуля и именем функции. Формулировки плана 15-06 не тронуты: старая строка сохранена префиксом байт в байт.
- Window 100 закрыто вербом `gsd-tools windows fixed 100`.
- Обе правки идут в коммит записи, а не в коммиты задач: критерий «`git show --name-only HEAD` не содержит `REQUIREMENTS.md`» для коммитов задач выполнен.

---

**Total deviations:** 6 auto-fixed (1 blocking, 4 замер/согласованность, 1 сохранность ссылок) + 1 handoff.
**Impact on plan:** Правила утверждают измеренное, а не пересказ плана. Область не расширена, разметка не тронута.

## TDD Gate Compliance

- **Задача 1:**
  - RED: `b8b084a7 test(15-04)`. Целевое правило `test_fetch_prohibition_name_chronicle_is_measured_by_the_syntax_tree` упало на утверждении: «функция-запрет FETCH-03 `…` определена в [], ожидалось ['test_templates/test_htmx_inventory.py']». Три предыдущих утверждения прошли. Junit-xml того же прогона сведён в TAP, `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`, 4 tests / 1 fail).
  - GREEN: `f047d904 feat(15-04)`.
- **Задача 2:**
  - RED: `8aebd852 test(15-04)`. Целевое правило `test_inline_event_attribute_places_are_the_declared_ones` упало на утверждении «найдено, но не объявлено {'components/thumb.html#0': 'onerror'}». → `RED_EVIDENCE_OK` (5 tests / 1 fail).
  - GREEN: `6db1a6b3 feat(15-04)`.
- REFACTOR не понадобился. Скрипт перевода в TAP не закоммичен.
- Мутационная проверка в памяти: при ослеплённой сети запрет остаётся зелёным, а синтетический контроль и контроль точности краснеют. Наивная сеть краснит контроль точности и называет форму `.fetch(`. Пустая вселенная краснит сам запрет.

## Issues Encountered

- `requirements.ready-ids 15-04-PLAN.md FETCH-03` (read-only) → `{"ready": ["FETCH-03"], "blocked": []}`. По указанию оркестратора `requirements.mark-complete` НЕ вызывался: FETCH-03 остаётся `[ ]` / `Pending` до вердикта верификации фазы 15.
- Полная суита планом не обещается (`<verification>`: «Полная суита в этом плане НЕ обещается»), поэтому окна о подмене не заводилось. Прогнаны:
  - целевой модуль: 30 passed;
  - `tests/test_templates/`: 286 passed;
  - `tests/test_planning/`: 78 passed;
  - `compileall`: без вывода.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- FETCH-03 машинно закрыт запретом. Отметку требования ставит закрытие фазы по вердикту.
- Верность формулировки находки об отметке GATE-08 — суждение владельца (D5 в `coverage`).

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `tests/test_templates/test_htmx_inventory.py`
- FOUND commits: `b8b084a7`, `f047d904`, `8aebd852`, `6db1a6b3`
- `git rev-list --count ea13b3bd..HEAD` = 4 (до коммитов записи)
