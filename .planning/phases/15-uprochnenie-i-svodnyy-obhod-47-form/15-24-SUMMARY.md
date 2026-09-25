---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 24
subsystem: testing
tags: [prohibitions-census, registry, record-mode, confirmation-panel, modal, htmx, alpine, criterion-6, g-1, d-05, d-16, pytest]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-22 — несколько правил в строке реестра и режим `--record`; план 15-13 — мера покрытия D-05 (строка `10-35#1` частично, `:3444`)"
  - phase: 10-rychag-components-modal-html
    provides: "девять запретов `product-invariant` о поведении панели подтверждения и правила суиты о панели (`test_components.py`, `test_hx_location_destinations.py`, `test_htmx_gates.py`)"
provides:
  - "девять строк группы «поведение панели подтверждения» в реестре — `enforced`, у каждой правило, покрасневшее на синтетическом нарушении ИМЕННО её формулировки"
  - "модуль `tests/test_templates/test_confirmation_panel_invariants.py`: 6 правил на непокрытое и 6 контролей на синтетике, `PANEL_AFTER_REQUEST_EXPRESSION`, `PANEL_TRANSPORT_BRANCH`, `PANEL_TRANSPORT_BRANCH_NOTE`"
affects: [15-25, 15-26, 15-27, 15-28, 15-29, 15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 8305
  tasks: 2
  commits: 3
plan_head_before: 758bf6b63442b50cb94baaaaf8e025761c3f5868

tech-stack:
  added: []
  patterns:
    - "Замер направления до записи: временная правка шаблона или страничного модуля, прогон правила-кандидата, `git checkout -- <файл>`, `git diff --exit-code -- app/` пуст"
    - "Частичное покрытие выявлено двумя мутациями строки: одна краснит действующее правило, другая (то же нарушение формулировки другим способом) — нет; новое правило пишется ровно на вторую"

key-files:
  created:
    - tests/test_templates/test_confirmation_panel_invariants.py
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-24: 3 из 9 строк (`10-02#0`, `10-05#0`, `10-31#2`) держатся действующими правилами целиком, замер — мутацией шаблона; 6 строк — действующим правилом плюс новым правилом на остаток либо одним новым (`10-07#1`)"
  - "15-24: `10-31#2` записан с правилом полноты собственных выходов `test_every_own_response_exit_of_a_converted_handler_is_declared`: отказ по происхождению, проведённый через слой ответа (путь, которым 10-31 называет отмену свойства), краснит его, а правило панели на такой правке зелено"
  - "15-24: `10-13#1` сверх ветки перехода держит новое правило на ВСЕ шаблоны: `const` в инлайн-скрипте подменяемого фрагмента `accounts/partials/connect_status.html` не краснил ни одно действующее правило"
  - "15-24: ни одна из девяти строк не передана плану 15-32: замещённых формулировок нет (у `10-27#0` пометка, выбранная планом 10-27, стоит в дереве, и её тело позднейшие планы уточнили, но не отменили), правил, красных на дереве, нет"

patterns-established:
  - "Модуль правил группы: каждое правило называет тождество запрета в докстринге, разборщик принимает исходник параметром, у каждого правила есть контроль на синтетической копии"

requirements-completed: []

coverage:
  - id: D1
    description: "Три строки, которые суита уже держала целиком (`10-02#0`, `10-05#0`, `10-31#2`), записаны `enforced` с правилами, покрасневшими на мутации дерева"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_the_panel_stays_open_when_the_server_refused_on_either_transport"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_the_panel_stays_open_when_the_exchange_never_completed_on_either_transport"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_own_response_exit_of_a_converted_handler_is_declared"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
    human_judgment: false
  - id: D2
    description: "Модуль `test_confirmation_panel_invariants.py`: 6 правил на непокрытое (10-35#1, 10-02#1, 10-27#0, 10-07#0, 10-07#1, 10-13#1) и 6 контролей; каждое правило покраснело на мутации дерева, вердикт RED-верба `RED_EVIDENCE_OK`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_confirmation_panel_invariants.py (12 passed)"
        status: pass
      - kind: other
        ref: "node .claude/gsd-core/bin/gsd-tools.cjs check tdd-red-evidence <запись> → RED_EVIDENCE_OK ×7"
        status: pass
    human_judgment: false
  - id: D3
    description: "Верность суждения «правило держит ВЕСЬ предмет формулировки» по каждой из девяти строк"
    verification: []
    human_judgment: true
    rationale: "Направление замерено машиной, но выбор синтетического нарушения — «минимальное нарушение ИМЕННО этой формулировки» — суждение исполнителя; полнота перечня способов нарушить формулировку машиной не выводится (D-33 плана 15-13). Проверяет верификатор фазы по таблице этой сводки"

duration: 15min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 24: Принуждение девяти запретов поведения панели подтверждения Summary

**Все девять запретов `product-invariant` о поведении панели подтверждения записаны в реестре `enforced`. Три держатся действующими правилами, и это доказано мутацией шаблона. Шесть держатся действующим правилом плюс новым правилом на ту часть, которую действующее пропускало при замеренном нарушении, либо одним новым правилом. Новые правила — в `tests/test_templates/test_confirmation_panel_invariants.py` (6 правил, 6 контролей), каждое покраснело на мутации дерева. Чекпойнту 15-32 не передано ничего; `app/` не правился.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-25T13:06:21Z
- **Completed:** 2026-09-25T13:21:34Z
- **Tasks:** 2
- **Files modified:** 2 (новый модуль правил, реестр)

## Таблица строк: правило → замер направления → строка отказа → запись

Все замеры — временная правка файла дерева, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/` пуст (проверено после каждой группы). Команда прогона: `uv run pytest -q -p no:randomly <файл>::<правило>`.

| Строка | Правило(а) записи | Синтетическое нарушение (правка дерева) | Строка отказа | Запись |
|---|---|---|---|---|
| `10-02#0` панель не закрывается при неуспешном обмене | `test_components.py::test_the_panel_stays_open_when_the_server_refused_on_either_transport`; `…::test_the_panel_stays_open_when_the_exchange_never_completed_on_either_transport` | мутация A: выражение `modal.html` → `sending = false; hide()` | `FAILED …::test_the_panel_stays_open_when_the_server_refused_on_either_transport` («при ОТКАЗЕ СЕРВЕРА панель закрылась…»), `FAILED …::…never_completed…` («при НЕСОСТОЯВШЕМСЯ ОБМЕНЕ … панель закрылась»); `3 failed` | задача 1, `enforced` |
| `10-05#0` выражение не закрывает панель безусловно | те же два + `…::test_the_panel_closes_only_on_a_successful_exchange` | мутация A | два отказа выше + `FAILED …::test_the_panel_closes_only_on_a_successful_exchange` («выражение завершения запроса не читает признак успешности события»); `3 failed` | задача 1, `enforced` |
| `10-31#2` свойство «панель открыта на отказе» не отменяется | `…::test_the_panel_stays_open_when_the_server_refused_on_either_transport`; `test_htmx_gates.py::test_every_own_response_exit_of_a_converted_handler_is_declared` | мутация A (половина панели); мутация G: в `app/pages/accounts.py::accounts_delete` `return Response(status_code=403)` → `return await respond(request, redirect="/accounts")` — отказ по происхождению проведён через слой ответа, то есть путь, которым 10-31 (в) называет отмену свойства | A — см. выше; G — `FAILED …::test_every_own_response_exit_of_a_converted_handler_is_declared`, `ОБЪЯВЛЕН, НО ЗАМЕРОМ НЕ НАЙДЕН: app/pages/accounts.py::accounts_delete`; правило панели на G — `1 passed` (не видит) | задача 1, `enforced` |
| `10-02#1` второе определение успеха по коду не заводится | `…::test_the_panel_closes_only_on_a_successful_exchange`; **новое** `test_confirmation_panel_invariants.py::test_the_panel_closing_branch_reads_no_response_code` | мутация B-replace: `$event.detail.successful` → `$event.detail.xhr.status &lt; 400`; B-add: `($event.detail.successful &amp;&amp; $event.detail.xhr.status &lt; 300)` | B-replace: действующее — `1 failed`; **B-add: действующее — `1 passed` (частично)**; новое на B-add — `FAILED …::test_the_panel_closing_branch_reads_no_response_code`, «ветвь закрытия панели читает код ответа ['.status']» | задача 2, `enforced` |
| `10-07#0` отказ не отключается и не выпадает из обхода по Tab | `…::test_the_cancel_button_stays_available_while_the_dismissal_is_gated`; **новое** `…::test_the_cancel_button_stays_in_the_tab_traversal` | мутация C: у кнопки отказа `tabindex="-1"` / `x-bind:disabled="sending"` / `inert`; перечислитель ловушки `button:not([disabled])` → `button[type=submit]:not([disabled])` | `tabindex`, `disabled` — действующее `FAILED` («кнопка ОТКАЗА получила ['tabindex']…»); **`inert` и ловушка — действующие `2 passed` (частично)**; новое: `inert` → «у кнопки отказа атрибут 'inert'», ловушка → «перечислитель ловушки фокуса не накрывает кнопку отказа» | задача 2, `enforced` |
| `10-07#1` клиентская отмена летящего запроса не вводится | **новое** `…::test_no_client_side_abort_of_a_request_in_flight` | мутация r5: форме панели дописан `hx-sync="closest form:abort"` | `FAILED …::test_no_client_side_abort_of_a_request_in_flight`, «components/modal.html: синхронизация 'closest form:abort'» | задача 2, `enforced` |
| `10-13#1` штатное действие не сносит молча клиентский слой | `test_hx_location_destinations.py::test_the_editor_script_survives_a_second_execution_in_the_same_realm`; `…::test_no_transition_destination_declares_a_top_level_binding_inline`; **новое** `…::test_no_template_declares_a_top_level_binding_in_an_inline_script` | мутация E: `const EDITOR_REEXEC_PROBE = 1;` перед обёрткой скрипта `ads/form.html`; мутация F: `const FRAGMENT_REEXEC_PROBE = 1;` в инлайн-скрипт подменяемого фрагмента `accounts/partials/connect_status.html` | E — оба действующих `FAILED` («SyntaxError: Identifier 'EDITOR_REEXEC_PROBE' has already been declared»; «ads/form.html:157: const EDITOR_REEXEC_PROBE»); **F — действующее статическое `1 passed` (частично)**; новое на F — `FAILED …::test_no_template_declares_a_top_level_binding_in_an_inline_script` | задача 2, `enforced` |
| `10-27#0` ветвь условия не удаляется, выбрана пометка | `test_components.py::test_the_panel_closes_on_the_location_transport`; **новое** `…::test_the_transport_branch_of_the_panel_condition_stays_with_its_note` | мутация D-delete: дизъюнкт `|| ($event.detail.xhr &amp;&amp; …getResponseHeader('HX-Location'))` удалён; D-replace: заменён на `|| ($event.detail.xhr &amp;&amp; $event.detail.xhr.status === 204)` | D-delete — действующее `FAILED` («не обращается к объекту запроса события»); **D-replace — действующее `1 passed` (частично)**; новое на D-replace — «в условии закрытия панели нет ветви транспорта» | задача 2, `enforced` |
| `10-35#1` выражение `x-on:htmx:after-request` не правится, панель открыта на отказе | `…::test_the_panel_stays_open_when_the_server_refused_on_either_transport` (запись 15-13); **новое** `…::test_the_panel_after_request_expression_is_the_declared_literal` | мутация r1: правка без смены поведения (`sending = false;  if`, второй пробел) | новое — `FAILED`, «D-12 ПЕРЕОТКРЫТ: выражение завершения запроса формы панели ПРАВЛЕНО»; непокрытость действующего записана планом 15-13 | задача 2, `enforced` (из `partially-enforced`) |

## Передано плану 15-32

**Ничего.** Ни одна из девяти формулировок не описывает состояние, отменённое позднейшим записанным решением. Принуждение ни одной не требует отката одобренной работы, и ни одно правило, написанное по формулировке, не красно на дереве. Проверено отдельно:
- `10-27#0`: план 10-27 выбрал пометку вместо удаления. Позднейшие правки уточнили её тело: IN-02 опровергнут замером, ссылки переведены на имена (план 10-46). Сама пометка стоит перед формой, и запрет удаления ветви не тронут. Новое правило сличает только заголовок пометки, а истинность тела стережёт `test_the_transition_response_is_assembled_in_one_declared_place`.
- `10-02#1`: дизъюнкт транспорта (план 10-05) читает заголовок, а не код ответа. `10-05-SUMMARY.md` называет его именованным изъятием по транспорту, поэтому новое правило его не ловит, и формулировка им не замещена.

## Accomplishments

- Задача 1: замер направления по шести строкам. `10-02#0`, `10-05#0` и `10-31#2` записаны `enforced`. У `10-02#1`, `10-07#0`, `10-27#0` и `10-13#1` найдено по нарушению, на котором действующее правило зелено, и эти строки переданы задаче 2 с названной частью.
- Задача 2: новый модуль из 6 правил с 6 контролями. Он ввозит `_all_templates` и `_strip_comments` из `test_htmx_markup_gates.py`, `_top_level_bindings_of_template` из `test_hx_location_destinations.py` и `VENDORED_JS_FILES` из `test_components.py`. Своего обхода шаблонов и своего перечня вендоренных файлов в модуле нет. Докстринг модуля составлен по форме D-16: предмет, тождество каждого правила, ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ с границами по строкам.
- Реестр: у `product-invariant` было `enforced 2 / partially-enforced 9 / unresolved 58`, стало `11 / 8 / 51`. Сумма области решений осталась 321, биекция в согласии. Дифф реестра — ровно 9 строк.

## Task Commits

1. **Задача 1: замер направления по действующим правилам** — `2a60dd33` (chore): 3 строки записаны `enforced`.
2. **Задача 2: новые правила на непокрытое** — `cee814b5` (test): модуль правил. `b9dda400` (chore): 6 строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-24)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`: гейт TDD на таком плане инертен. Продукт по плану не правится, поэтому цикла «красный тест → правка продукта → зелёный» здесь нет и быть не может: правила описывают дерево, а не меняют его. **RED каждого правила измерен так, как требует владелец (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Действующие правила** (задача 1 и половины строк задачи 2): мутации A–G дерева, строки отказа — в таблице выше. Каждая мутация отменена `git checkout -- <файл>`, `git diff --exit-code -- app/` пуст.
- **Новые правила** (задача 2): семь мутаций дерева r1, r2, r3, r4a, r4b, r5, r6 — по одной на правило, у `10-07#0` две. Каждая дала `FAILED tests/test_templates/test_confirmation_panel_invariants.py::<правило>`, итоговая строка `1 failed`, `exit=1`; причинные литералы — в таблице. Прогоны писали `--junit-xml`. Одноразовый скрипт в scratchpad (не в дереве) перевёл их в запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP. `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`) на всех семи.
- **Контроли на синтетике** (в модуле): каждый утверждает, что копия с нарушением названа, а исправное дерево — нет, и все зелены. Для `10-07#1` точность показана отдельно: `hx-sync="this:drop"`, очередь и закомментированный `hx-sync="…:abort"` не ловятся.
- Коммит `test(15-24)` предшествует записям второй задачи; коммита `feat(15-24)` нет, потому что продукт не правился. REFACTOR нет.

## Files Created/Modified

- `tests/test_templates/test_confirmation_panel_invariants.py` — новый модуль правил группы (481 строка).
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 9 строк, только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Где действующее правило ловит часть нарушений формулировки, а часть нет, строка пишется с обоими правилами.
- Правило `10-13#1` сознательно строже предмета: оно запрещает объявление верхнего уровня в инлайн-скрипте любого шаблона, а не только подменяемого повторно. Сегодня таких объявлений ноль, замер по всем шести шаблонам со скриптами.
- `10-31#2` держится на двух уровнях — выражение панели и форма отказа сервера, — и оба уровня названы правилами.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Строки `10-27#0` и `10-13#1` получили действующее правило в записи, хотя план ждал для них только нового**
- **Found during:** задача 1 (протокол строки, шаг 2: «сперва искать действующее правило»)
- **Issue:** план предполагал новое правило для `10-27#0` и не опознал предмета `10-13#1`. Замер нашёл действующие правила. Удаление дизъюнкта краснит `test_the_panel_closes_on_the_location_transport`, а скрипт экрана-цели держат два правила `test_hx_location_destinations.py`. Но на второй форме нарушения каждое из них зелено: у `10-27#0` дизъюнкт заменён условием по коду 204, у `10-13#1` `const` стоит во фрагменте.
- **Fix:** строка пишется с действующим правилом и новым правилом на остаток — так, как протокол велит при частичном покрытии.
- **Files modified:** модуль правил, реестр
- **Verification:** мутации D и F, строки отказа в таблице
- **Committed in:** `cee814b5`, `b9dda400`

**2. [Rule 2 - Missing critical] Правило полноты собственных выходов в записи `10-31#2`**
- **Found during:** задача 1
- **Issue:** формулировка ссылается на 10-31, где отмена свойства названа следствием перевода отказа по происхождению на слой ответа. На такой правке правило панели зелено: форма события отказа у него без заголовка перехода.
- **Fix:** в запись добавлено `test_every_own_response_exit_of_a_converted_handler_is_declared`, его красный замерен мутацией G
- **Committed in:** `2a60dd33`

---

**Total deviations:** 2 auto-fixed (2 Rule 2)
**Impact on plan:** обе поправки добавляют к записи правило, доказанное замером. Правка продукта не понадобилась, и ни одна формулировка не облегчена.

## Issues Encountered

- `-k "panel or cancel or modal_guard"` из `<verify>` задачи 1 выбрал `27 passed, 65 deselected`, выборка непуста.
- Шаблон панели цитирует в комментарии прежнюю форму атрибута (`x-on:htmx:after-request="sending = false"`). Разборщик нового модуля поэтому читает исходник без комментариев, иначе нашёл бы два выражения. Та же цитата видна в выводе замера B и не мешает правилам `test_components.py`: они разбирают отрисовку.

## Verification

- `uv run pytest tests/test_templates/test_confirmation_panel_invariants.py -q -p no:randomly` → `12 passed`.
- `uv run pytest tests/test_templates/ -q -p no:randomly` → `379 passed`.
- `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` → `184 passed`.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed`.
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие».
- `--breakdown` → «сумма по диспозициям области решений: 321»; `product-invariant: enforced 11 (3), partially-enforced 8 (8), unresolved 51 (1)`; частичных строк без `permit_scope_uncovered` — 8.
- `grep -c 'ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ'` в модуле → `1`. `git diff --exit-code -- app/` → пусто; `git diff <plan_head_before>..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись: в модуле нет утверждений 302, вызовов целей перехода и пар деградации. Новый `import yaml` не заведён.
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют каталоги `tests/test_templates/` и `tests/test_planning/` целиком и три гейта страниц. Окна в WINDOWS.md для этого не открыто.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-25…15-31 проходят свои группы тем же протоколом. Образец — две мутации на строку: одна проверяет, что действующее правило краснеет, другая ищет форму нарушения, на которой оно зелено.
- Остаток `product-invariant`: 8 частичных строк и 51 неразобранная (`enforcement-required`) ждут следующих планов партии.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_templates/test_confirmation_panel_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 2a60dd33, cee814b5, b9dda400 (ledger `758bf6b6..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*
