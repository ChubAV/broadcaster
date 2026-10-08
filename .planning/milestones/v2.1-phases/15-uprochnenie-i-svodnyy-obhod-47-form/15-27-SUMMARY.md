---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 27
subsystem: testing
tags: [prohibitions-census, registry, record-mode, failure-banner, htmx-error-banner, third-handler, response-reads, criterion-6, g-1, d-16, pytest]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-24 — протокол строки; план 15-26 — образец замера мутацией дерева; план 15-22 — режим `--record`; план 15-19 — имена органов снятия («Отказ сервера: скрыть сообщение» / «Обрыв связи: скрыть сообщение»)"
  - phase: 10-rychag-components-modal-html
    provides: "десять запретов `product-invariant` о сценарии и текстах плашек отказа; третий обработчик (план 10-49), ветвь `A` выхода у плашки (план 10-57)"
provides:
  - "десять строк группы «сценарий и тексты плашек отказа» — `enforced`; у каждой правило, покрасневшее на временной правке шаблона по формулировке ИМЕННО этой строки"
  - "модуль `tests/test_pages/test_failure_banner_invariants.py`: 4 правила, 4 контроля; `FAILURE_BANNER_TEXTS`, `THIRD_HANDLER_BODY` (+ `THIRD_HANDLER_HOST`, `THIRD_HANDLER_PARAMS`, `THIRD_HANDLER_POSITION`), `FAILURE_BANNER_RESPONSE_READS`, `FAILURE_BANNER_RESPONSE_PRESENCE_TESTS`"
  - "три замещённые строки (`10-33#1`, `10-35#0`, `10-56#5`) переданы чекпойнту плана 15-32 поимённо, с обеими формулировками"
affects: [15-28, 15-29, 15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 11571
  tasks: 2
  commits: 3
plan_head_before: efa40b88236b1574e98aaa5560bc9c6d7b5cfeb3

tech-stack:
  added: []
  patterns:
    - "Правило посимвольного равенства одного обработчика читает только его регистрацию (узел, событие, параметр, тело, позицию в блоке признака однократности), а тела соседних обработчиков не сличает; контроль точности правит соседнее тело и требует зелени"
    - "Закрытый перечень обращений к объекту события: каждое вхождение имени параметра любой функции сценария (и глобального `event`) есть либо чтение из перечня, либо проверка наличия в положении условия; привязка к другому имени, скобки, вызов и `arguments` названы"

key-files:
  created:
    - tests/test_pages/test_failure_banner_invariants.py
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-27: четыре строки (`10-53#1`, `10-57#1`, `10-57#2`, `10-57#4`) держат действующие правила целиком — каждое покраснело на прямом нарушении (удаление третьего обработчика, `hx-on`, новый `x-data`, снятый сброс органа снятия)"
  - "15-27: правило текстов читает первый аргумент `alert(...)` и текст узла вне тегов, а не строку узла — правка `aria-label` (план 15-19) его не краснит, это замерено и на копии, и на дереве (m11)"
  - "15-27: правило третьего обработчика утверждает узел, позицию (третья в блоке признака однократности), параметр и тело посимвольно; тела двух других обработчиков (правленных планом 10-57 решением владельца, ветвь `A`) не сличает"
  - "15-27: половину «строка узла обрыва связи — одна строка с вызовом макроса» держит новое правило: вызов, закрытый на следующей строке при тексте на месте (m7b), оставлял действующее правило основ зелёным"
  - "15-27: `10-33#1`, `10-35#0`, `10-56#5` переданы чекпойнту 15-32 как ЗАМЕЩЁННЫЕ; их прежние диспозиции не тронуты. Записи `10-33#1`/`10-35#0` (`partially-enforced`) называют правило, которое сегодня утверждает 3 обработчика против формулировки «остаётся 2»"

patterns-established:
  - "Для запрета «X не правится ни на символ» при законно правленных соседях правило сличает только X и несёт контроль точности на правке соседа"

requirements-completed: []

coverage:
  - id: D1
    description: "Четыре строки (`10-53#1`, `10-57#1`, `10-57#2`, `10-57#4`) записаны `enforced` действующими правилами, покрасневшими на мутациях m1, m1b, m8, m8b, m9, m10, m10b"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_carries_every_measured_handler"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_is_cleared_by_a_successful_exchange"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_criterion_three_holds_by_the_numbers"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_no_markup_declares_request_parameters_or_event_handlers"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_client_state_nodes_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_a_dismissed_banner_returns_on_the_next_failure"
        status: pass
    human_judgment: false
  - id: D2
    description: "Модуль `test_failure_banner_invariants.py`: 4 правила и 4 контроля; каждое новое правило покраснело на мутации шаблона, на которой действующие правила зелены; RED-верб `RED_EVIDENCE_OK` на всех 16 прогонах новых правил; шесть строк записаны `enforced`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_failure_banner_invariants.py (8 passed)"
        status: pass
      - kind: other
        ref: "node .claude/gsd-core/bin/gsd-tools.cjs check tdd-red-evidence <запись> → RED_EVIDENCE_OK ×31 (14 действующих + 16 новых + 1 основ на m6c)"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
      - kind: integration
        ref: "uv run pytest <новый модуль> tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_shell.py tests/test_templates/ tests/test_planning/ -q -p no:randomly → 970 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Передача `10-33#1`, `10-35#0`, `10-56#5` чекпойнту 15-32 и верность суждения «правило держит ВЕСЬ предмет формулировки» по десяти записанным строкам"
    verification: []
    human_judgment: true
    rationale: "Снятие замещённых формулировок (D-30/D-32) и судьба прежних частичных записей `10-33#1`/`10-35#0` — решения владельца. Выбор синтетического нарушения «ИМЕННО этой формулировки» — суждение исполнителя: полноту перечня способов нарушения машина не выводит (D-33 плана 15-13)"

duration: 34min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 27: Принуждение десяти запретов о сценарии и текстах плашек отказа Summary

**Все десять запретов `product-invariant` группы «сценарий и тексты плашек отказа» записаны в реестре `enforced`. Четыре (`10-53#1`, `10-57#1`, `10-57#2`, `10-57#4`) держат действующие правила целиком. Шесть держатся новыми правилами модуля `tests/test_pages/test_failure_banner_invariants.py` (часть — вместе с действующими): тексты обеих плашек посимвольно, строка узла обрыва связи с вызовом макроса целиком, третий обработчик (узел, позиция, параметр, тело) посимвольно, закрытый перечень чтений объекта события. Каждое правило записи покраснело на временной правке шаблона по формулировке своей строки. Замещённые `10-33#1`, `10-35#0`, `10-56#5` не записаны и переданы плану 15-32. `app/` не правился.**

## Performance

- **Duration:** 34 min (из них 13.5 мин — прогон целевых модулей и гейтов)
- **Started:** 2026-09-25T18:31:36Z
- **Completed:** 2026-09-25T19:05:13Z
- **Tasks:** 2
- **Files modified:** 2 (новый модуль правил, реестр)

## Замер направления

Каждая мутация — временная правка `app/templates/includes/htmx_error_banner.html` (у m2d — ещё и `base.html`). Порядок: запись, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/`. Драйвер в scratchpad проверял последнее после каждой мутации, и каждый раз было `clean=True`. Если якорь подмены не единствен, драйвер отказывает до правки: у m6c якорь «увидеть настоящее состояние» нашёлся дважды, второй раз — в комментарии шаблона, и мутацию переписали на полный литерал текста. Команда: `uv run pytest -q -p no:randomly --junit-xml=… <цель>`. Широкий прогон действующих правил шёл по `test_shell.py` и `test_banner_dismiss.py` с `-k "banner or failure or dismiss or …"` (67 тестов) плюс `test_criterion_three_holds_by_the_numbers`, `test_no_markup_declares_request_parameters_or_event_handlers` и `test_the_number_of_client_state_nodes_is_the_declared_one`.

| Мутация | Правка | Действующие правила | Новые правила |
|---|---|---|---|
| m1 | третий обработчик удалён | `11 failed` — среди них `carries_every_measured_handler` («в сценарии нет обработчика(ов) ('htmx:afterRequest',)»), `is_cleared_by_a_successful_exchange`, `test_criterion_three_holds_by_the_numbers` («УТВЕРЖДЕНИЕ 5 ИЗ 5 … найдено 2, объявлено 3») | третий: «регистраций `htmx:afterRequest` в сценарии 0» |
| m1b | тело третьего без двух `setAttribute` (зарегистрирован, но ничего не гасит) | `3 failed`: `is_cleared_by_a_successful_exchange` («ПЛАШКА ОТКАЗА ПЕРЕЖИЛА УСПЕШНЫЙ ОБМЕН») и два его контроля | — |
| m2a | третий вынесен за блок признака однократности | `1 failed`: `registers_its_handlers_once_per_body` («два исполнения дали 4 регистраций вместо 3») | третий: «ПЕРЕНЕСЁН за пределы блока признака однократности» |
| m2b | узел `document` вместо `document.body` | `9 failed`: `guard_lives_on_the_node_it_wires` («слушатели вешаются на ['document', 'document.body']»); у остальных восьми отказ гарнира (`TypeError: document.addEventListener is not a function`) — это не названная причина | третий: «ПЕРЕНЕСЁН на узел `document`» |
| m2c | третий зарегистрирован первым в блоке | **`67 passed`** | третий: «ПЕРЕНЕСЁН в порядке регистрации … позиция 0 … ожидалось: позиция 2» |
| m2d | третий перенесён в `<script>` шаблона `base.html` | `12 failed`, в том числе `test_failure_banner_has_single_source` («найдено: ['base.html', …]») | третий: «регистраций … 0» |
| m3 | `!event.detail.successful` → `event.detail.successful !== true` (поведение в гарнире то же) | **`67 passed`** | третий: «ТЕЛО ТРЕТЬЕГО ОБРАБОТЧИКА ИЗМЕНЕНО с символа 26» |
| m3b | `{ return; }` → `{return;}` (только пробелы) | **`67 passed`** | третий: «ИЗМЕНЕНО с символа 53» |
| m3c | правка тела ПЕРВОГО обработчика (контроль точности) | `67 passed` | правило третьего **зелено** (как и должно) |
| m4 | `server.innerHTML = server.innerHTML` | `touches_no_markup_sink`: «появился сток разметки ('innerHTML',)» | — |
| m5 | `event.detail.xhr.responseText` | `touches_no_markup_sink`: «сценарий начал читать ТЕЛО пришедшего ответа» | чтения: «`event.detail.xhr.responseText` — … вне закрытого перечня» |
| m5b | `event.detail.xhr.getResponseHeader('X-Reason')` | `2 failed` только отказом гарнира (`TypeError: event.detail.xhr.getResponseHeader is not a function`) — **не названная причина**; `touches_no_markup_sink` зелено | чтения: «`event.detail.xhr.getResponseHeader(…` — обращение скобками или вызов на объекте события» |
| m5c | `event.detail.xhr.response` | **`67 passed`** | чтения: «`event.detail.xhr.response` — … вне закрытого перечня» |
| m5d | `var reply = event.detail.xhr; … reply.statusText` | **`67 passed`** | чтения: «`event.detail.xhr` — … вне закрытого перечня … (проверки наличия — только в условии)» |
| m6 | «через минуту» → «через минутку» (текст отказа сервера) | **`67 passed`** | тексты: «#htmx-failure-server: ТЕКСТ ПЛАШКИ ИЗМЕНЁН» |
| m6b | «Проверьте соединение» → «Проверьте подключение» (основы и единственный совет на месте) | **`67 passed`** | тексты: «#htmx-failure-network: ТЕКСТ ПЛАШКИ ИЗМЕНЁН» |
| m6c | «настоящее состояние» → «актуальное состояние» | `the_network_banner_names_the_screen_server_divergence`: «нет основ ('настоящ',)» | тексты: «ТЕКСТ ПЛАШКИ ИЗМЕНЁН» |
| m7 | текст обрыва связи перенесён на следующую строку | `the_network_banner_names_the_screen_server_divergence`: «нет основ ('экран', 'серв', 'обнов', 'настоящ')» | строка: «НЕ НЕСЁТ ВЫЗОВА МАКРОСА ЦЕЛИКОМ» |
| m7b | текст на месте, вызов закрыт на следующей строке (`',\n'error') }}`) | **`67 passed`** | строка: «НЕ НЕСЁТ ВЫЗОВА МАКРОСА ЦЕЛИКОМ» |
| m8 / m8b | `hx-on::after-request="…"` / `hx-on="…"` на узле обрыва связи | `test_criterion_three_holds_by_the_numbers` («УТВЕРЖДЕНИЕ 3 ИЗ 5 … объявлен НОЛЬ»), `test_no_markup_declares_request_parameters_or_event_handlers` | — |
| m9 | новый узел `<div x-data="{ seen: false }" hidden>` | `test_criterion_three_holds_by_the_numbers` («УТВЕРЖДЕНИЕ 4 ИЗ 5 … найдено 25, объявлено 24»), `test_the_number_of_client_state_nodes_is_the_declared_one` | — |
| m10 / m10b | снят сброс органа снятия отказа сервера / обрыва связи | `test_a_dismissed_banner_returns_on_the_next_failure`: «#htmx-failure-server (network): состояние органа снятия НЕ СБРОШЕНО новым отказом» | — |
| m11 | `aria-label` органа обрыва связи изменён (контроль точности) | — | все три правила модуля **зелены** (`3 passed`) |

## Таблица строк

| Строка | Формулировка (сокращённо) | Правило(а) записи | Замер, давший красное | Запись |
|---|---|---|---|---|
| `10-53#1` | третий обработчик не откатывается ни в одной из двух ветвей | `test_shell.py::test_the_failure_banner_carries_every_measured_handler`; `…::test_the_failure_banner_is_cleared_by_a_successful_exchange` | m1 (оба), m1b (второе) | задача 1, `enforced` |
| `10-57#1` | атрибута `hx-on`, `hx-on::…` не заводится ни одного | `test_components.py::test_criterion_three_holds_by_the_numbers`; `test_htmx_markup_security.py::test_no_markup_declares_request_parameters_or_event_handlers` | m8, m8b (оба) | задача 1, `enforced` |
| `10-57#2` | нового узла клиентского состояния не заводится | `test_criterion_three_holds_by_the_numbers`; `test_htmx_markup_gates.py::test_the_number_of_client_state_nodes_is_the_declared_one` | m9 (оба) | задача 1, `enforced` |
| `10-57#4` | снятие плашки не отключает канал до конца сессии | `test_shell.py::test_a_dismissed_banner_returns_on_the_next_failure` | m10, m10b | задача 1, `enforced` |
| `10-49#1` | сценарий не получает стока разметки и не читает из ответа ничего, кроме признаков состояния | `test_shell.py::test_the_failure_banner_touches_no_markup_sink`; **новое** `…::test_the_banner_script_reads_only_state_signals_from_the_response` | действующее: m4, m5; **новое: m5b, m5c, m5d** (там действующее зелено), m5 | задача 2, `enforced` |
| `10-49#2` | тексты обеих заготовок не правятся; смысл второй фразы стерегут основы | `test_shell.py::test_the_network_banner_names_the_screen_server_divergence`; **новое** `…::test_both_failure_banner_texts_are_unchanged` | m6c (оба); **m6, m6b — только новое** | задача 2, `enforced` |
| `10-52#0` | третий обработчик не откатывается и не правится ни на символ | **новое** `…::test_the_third_failure_handler_body_is_unchanged`; `carries_every_measured_handler`; `is_cleared_by_a_successful_exchange` | откат m1 (все три); **m3, m3b — только новое** | задача 2, `enforced` |
| `10-57#3` | третий обработчик не откатывается, не переносится и не правится ни на символ | те же три | откат m1; перенос m2a, m2b, m2d (новое вместе с действующими), **m2c — только новое**; правка m3, m3b — только новое | задача 2, `enforced` |
| `10-56#6` | тексты обеих плашек не правятся; строка узла обрыва связи — одна строка с вызовом макроса | **новые** `…::test_both_failure_banner_texts_are_unchanged`, `…::test_the_network_banner_node_stays_one_line_with_its_macro_call`; `test_shell.py::test_the_network_banner_names_the_screen_server_divergence` | тексты: m6, m6b (новое); строка: m7 (действующее и новое), **m7b — только новое** | задача 2, `enforced` |
| `10-57#7` | то же, «находка `UI-3` отложена, текст не трогается вовсе» | те же три | те же | задача 2, `enforced` |

## Передано плану 15-32

Не записаны этим планом. Прежние диспозиции не тронуты (`--list`: `10-33#1`, `10-35#0` — `partially-enforced`, `10-56#5` — `unresolved`).

**1. `10-33#1` — формулировка замещена.**
- Формулировка: «третий обработчик НЕ ЗАВОДИТСЯ и число зарегистрированных обработчиков не сдвигается: `FAILURE_BANNER_HANDLERS_MEASURED` остаётся равным 2, сценарий включения не правится ни на строку».
- Замещена формулировкой `10-52#0`: «ТРЕТИЙ ОБРАБОТЧИК В `app/templates/includes/htmx_error_banner.html` НЕ ОТКАТЫВАЕТСЯ И НЕ ПРАВИТСЯ НИ НА СИМВОЛ: он закрывает настоящий дефект `G-10-5` …» — и тем же у `10-53#1` и `10-57#3`. Третий обработчик завёл план 10-49 (`4e24d61b`, 2026-09-11). В дереве три регистрации, `FAILURE_BANNER_HANDLERS_MEASURED = 3` (`test_shell.py`: «ЧИСЛО ПЕРЕСНЯТО 2 → 3 (план 10-49)»).
- ⚠️ Прежняя запись строки — `partially-enforced` с правилом `test_the_failure_banner_registers_its_handlers_once_per_body`. Это правило сегодня утверждает **3** регистрации, против формулировки «остаётся равным 2». Запись называет правило, которое держит противоположное формулировке состояние. Правило по формулировке красно на дереве (m1 показывает обратное: удаление третьего краснит правило, записанное за «третий не заводится»).

**2. `10-35#0` — формулировка замещена.**
- Формулировка: «ТРЕТИЙ ОБРАБОТЧИК НЕ ЗАВОДИТСЯ: сценарий `includes/htmx_error_banner.html` не правится ни на строку, число зарегистрированных обработчиков остаётся прежним, и снятие заготовок живёт ВНУТРИ уже существующего `show()`».
- Замещена тем же планом 10-49 и формулировками `10-52#0`, `10-53#1`, `10-57#3` (цитата выше). Половину «не правится ни на строку» замещает ещё и план 10-57 (см. п. 3). Прежняя запись — `partially-enforced` с тем же правилом счёта: тот же разрыв, что в п. 1.

**3. `10-56#5` — половина формулировки замещена.**
- Формулировка: «СЦЕНАРИЙ ЗАГОТОВОК НЕ ПРАВИТСЯ НИ НА СТРОКУ, И ТРЕТИЙ ОБРАБОТЧИК (`:227-233`) НЕ ТРОГАЕТСЯ НИ НА СИМВОЛ … Выход у плашки заводит план 10-57 — и делает это ПОСЛЕ останова владельца, а не заодно».
- Чем замещена: план 10-57 (`1753c10c`, 2026-09-13; формулировка `10-57#3` «…предмет настоящего плана — ВЫХОД у плашки, а не ревизия чужой правки») добавил по одной строке сброса органа снятия в тела ДВУХ ДРУГИХ обработчиков. Решение владельца — ветвь `A`, третья запись блока `overrides` отчёта `10-VERIFICATION.md`; в шаблоне это записано абзацем «⚠️ ДВЕ ДОБАВЛЕННЫЕ СТРОКИ СЦЕНАРИЯ …».
- Замер: правило «сценарий не правится ни на строку» красно на дереве (строки `server_close.checked = false` и `network_close.checked = false`). Половину «третий обработчик не трогается ни на символ» держит `test_the_third_failure_handler_body_is_unchanged` (m3, m3b), и она записана строками `10-52#0`/`10-57#3`. Решение за владельцем: снять формулировку как замещённую (D-30/D-32) либо переформулировать её в уцелевшую половину.

## Accomplishments

- Задача 1: 23 мутации шаблона. Четыре строки записаны `enforced` действующими правилами, каждое из которых покраснело по названной причине: 14 целевых прогонов, RED-верб `RED_EVIDENCE_OK` на всех. У остальных шести строк найдены формы нарушения, на которых действующие правила зелены (m2c, m3, m3b, m5b, m5c, m5d, m6, m6b, m7b), и они переданы задаче 2.
- Задача 2: модуль `tests/test_pages/test_failure_banner_invariants.py` — 4 правила и 4 контроля. Из `test_shell.py` ввезены `_failure_banner_path`, `_failure_banner_source`, `_failure_banner_script`, `_network_banner_line`, `_scratch_banner`, `_without_comments`, `FAILURE_BANNER_IDS`, `FAILURE_BANNER_OWNER`, `FAILURE_BANNER_SUCCESS_EVENT`, `FAILURE_BANNER_HANDLERS_MEASURED`; второго разбора шаблона модуль не заводит. Свой в нём только разбор регистраций сценария (маска строк и комментариев, парные скобки). Докстринг составлен по форме D-16: предмет с тождествами, замещённые состояния названы, «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» по каждой строке.
- Реестр: `product-invariant` было `enforced 31 / partially-enforced 8 / unresolved 31`, стало `41 / 6 / 23`. Сумма по диспозициям области решений — 321, биекция в согласии. Дифф реестра — ровно 10 строк.

## Task Commits

1. **Задача 1: замер по действующим правилам** — `844a94fc` (chore): четыре строки записаны `enforced`.
2. **Задача 2: новые правила** — `5e042e08` (test): модуль правил; `8a14f5d6` (chore): шесть строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-27)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`, поэтому гейт TDD на нём инертен. Продукт не правится, и цикла «красный тест → правка продукта → зелёный» здесь нет. **RED каждой строки измерен по правилу владельца (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Действующие правила:** 14 целевых прогонов (`red.sh <мутация> <правило>` в scratchpad) на m1, m1b, m4, m5, m7, m8, m8b, m9, m10, m10b; у каждого `FAILED …::<правило>`, `1 failed, 1 warning`, `exit=1`. Причинные литералы — в таблице замера. m5b прогонялся широко: два правила упали отказом гарнира (`TypeError … getResponseHeader is not a function`). Это не названная причина, и уликой RED для действующих правил m5b **не** заявлен.
- **Новые правила:** 16 целевых прогонов: тексты — m6, m6b, m6c; строка — m7, m7b; третий — m1, m2a, m2b, m2c, m2d, m3, m3b; чтения — m5, m5b, m5c, m5d. Плюс основы на m6c. Каждый прогон дал `FAILED tests/test_pages/test_failure_banner_invariants.py::<правило>`, `1 failed, 1 warning`, `exit=1`. Прогоны писали `--junit-xml`. Одноразовый скрипт scratchpad (`junit2red.py`, не в дереве) перевёл их в запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP. `check tdd-red-evidence` (путь записи абсолютный) дал `RED_EVIDENCE_OK` / `target_test_failed` на всех 31 записях.
- **Контроли точности на дереве:** m3c (правка тела другого обработчика) и m11 (правка `aria-label`) оставили все три правила модуля зелёными.
- **Контроли на синтетике** (в модуле): копии с правкой текста каждой плашки, с лишним текстом в узле, с изменённым `aria-label` (зелено); с разбитым вызовом макроса; с правкой на символ и на пробел, переставленным, вынесенным, перевешенным на `document` и удалённым третьим обработчиком, с правкой тела другого обработчика (зелено); с `getResponseHeader(`, `.response`, привязкой `xhr` к имени, скобками и `arguments`. Каждый контроль сначала утверждает, что боевое дерево по его правилу чисто. Все контроли зелены.
- Коммит `test(15-27)` предшествует записям второй задачи. Коммита `feat(15-27)` нет: продукт не правился. REFACTOR не было.

## Files Created/Modified

- `tests/test_pages/test_failure_banner_invariants.py` — новый модуль правил группы (748 строк).
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 10 строк, записаны только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Тексты объявлены литералами, снятыми с дерева. Текст отказа сервера стоит с 08-04, текст обрыва связи — с 09-04; сличено по истории файла: `alert('…'` одинаков на `37cff81d`, `efe9cb6e` и HEAD. Прежний довод `NETWORK_BANNER_DIVERGENCE` («фраза целиком охраняла бы буквы») верен для правила смысла и остаётся в силе. Буквы стерегут запреты Фазы 10 (`10-57#7`: «находка `UI-3` … отложена, и текст поэтому не трогается вовсе»). Смена текста — новое решение владельца вместе с литералом; это названо в докстринге.
- Тело третьего обработчика байт-в-байт то же, что заведено планом 10-49 (`git show 4e24d61b:<шаблон>` против дерева — различий нет).
- В правило третьего вошла ПОЗИЦИЯ в блоке признака однократности («третий»). Иначе перестановка регистраций (m2c) — перенос по букве `10-57#3` — оставалась бы зелёной у всех правил.
- Правило чтений требует непустого перечня найденных чтений, а не равенства перечню. Пропажа чтения (откат третьего вместе с `detail.successful`) — не чтение сверх признаков, и красить за неё это правило значило бы красить за чужой предмет. Равенство перечню дереву утверждает контроль.
- Строки `10-49#2`/`10-56#6`/`10-57#7` записаны вместе с правилом основ `test_the_network_banner_names_the_screen_server_divergence`: оно покраснело на правке текста (m6c) и на переносе текста (m7).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Четвёртое правило — строка узла обрыва связи**
- **Found during:** задача 1 (m7b)
- **Issue:** план поручал половину «строка узла — одна строка с вызовом макроса» действующему `_network_banner_line`. Вызов, закрытый на следующей строке при тексте на месте, оставлял его зелёным (`67 passed`).
- **Fix:** по протоколу строки при частичном покрытии — новое правило `test_the_network_banner_node_stays_one_line_with_its_macro_call` с контролем; строки `10-56#6`/`10-57#7` записаны с ним.
- **Files modified:** модуль правил
- **Commit:** `5e042e08`, `8a14f5d6`

**2. [Rule 1 - Bug] Антивакуум правила чтений краснил за чужой предмет**
- **Found during:** задача 2, замер направления новых правил до коммита
- **Issue:** первая редакция требовала равенства найденных чтений перечню. На m1/m2d (третий обработчик удалён или перенесён, а с ним пропало `detail.successful`) правило чтений краснело, хотя чтения сверх признаков не было.
- **Fix:** правило требует непустого перечня найденных чтений; равенство дереву перенесено в контроль. После правки m1/m2d краснят только правило третьего обработчика (перепроверено).
- **Files modified:** `tests/test_pages/test_failure_banner_invariants.py` (до коммита)
- **Commit:** `5e042e08`

**3. [Rule 1 - Bug] Контроли на поломанном дереве печатали вводящий в заблуждение отказ**
- **Found during:** задача 2, тот же замер
- **Issue:** на m2a контроль точности третьего обработчика отказывал сообщением «правило краснеет на правке тела ДРУГОГО обработчика», хотя красным было само дерево.
- **Fix:** каждый контроль сначала утверждает, что боевое дерево по его правилу чисто, и называет это отдельным сообщением.
- **Commit:** `5e042e08`

---

**Total deviations:** 3 auto-fixed (1 Rule 2, 2 Rule 1 — в правилах до коммита). Три строки переданы чекпойнту замером планирования, как план и предписывал.
**Impact on plan:** записи несут только правила с замеренным красным. Продукт не правился, ни одна формулировка не облегчена, замещённые строки не тронуты.

## Issues Encountered

- У m6c якорь «увидеть настоящее состояние» встретился в шаблоне дважды (второй раз — в комментарии-докстринге). Драйвер отказал до правки, `app/` остался чистым. Мутацию переписали на полный литерал текста.
- m2b и m5b краснят часть действующих поведенческих правил только отказом гарнира (стаб без `document.addEventListener` / без `getResponseHeader`). Как держащие строку они не засчитаны.

## Verification

- `uv run pytest tests/test_pages/test_failure_banner_invariants.py -q -p no:randomly` → `8 passed`.
- `uv run pytest tests/test_pages/test_failure_banner_invariants.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_shell.py tests/test_templates/ tests/test_planning/ -q -p no:randomly` → `970 passed`, `exit=0` (811 с). Прогон шёл на дереве с модулем в том виде, в каком он закоммичен в `5e042e08`. Записи реестра после этого `tests/test_pages/` и `tests/test_templates/` не касаются.
- `<verify>` задачи 1 на исходном дереве (`efa40b88`) → `45 passed, 292 deselected`.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` после записей задачи 1; вместе с модулем правил — `148 passed` после записей задачи 2.
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие»; `--breakdown` → `product-invariant: enforced 41 (5), partially-enforced 6 (6), unresolved 23 (1)`, «сумма по диспозициям области решений: 321».
- `--list --phase 10 --class product-invariant`: десять строк группы несут `disposition=enforced`; `10-33#1`, `10-35#0` — `partially-enforced`, `10-56#5` — `unresolved` (прежние, не тронуты).
- `grep -c 'ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ'` → `1`. `git diff --exit-code -- app/` → пусто, `git diff efa40b88..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись. В модуле нет HTTP-вызовов, утверждений `status_code == 302`, целей перехода и имён `*_degrades_without_htmx`. `PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — гейты зелены в прогоне выше. Нового `import yaml` нет.
- `graphify update .` выполнен после правки кода.
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют новый модуль, `test_shell.py`, три гейта страниц (`test_htmx_gates.py`, `test_htmx_post_pairs.py`, `test_hx_location_destinations.py`), каталоги `tests/test_templates/` и `tests/test_planning/` целиком. Окна в WINDOWS.md для этого не открыто.

## Known Stubs

None — модуль заглушек не содержит; тексты и тело — литералы, снятые с дерева.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-28…15-31 проходят свои группы тем же протоколом. Образец этого плана: для запрета «X не правится ни на символ» при законно правленных соседях правило сличает только X и несёт контроль точности на правке соседа. Для запрета «не переносится» — замерять перестановку, вынос за охрану, другой узел и другой файл по отдельности.
- Остаток `product-invariant`: 6 частичных и 23 неразобранные строки. Пять строк переданы 15-32: две — планом 15-26, три — этим.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_pages/test_failure_banner_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 844a94fc, 5e042e08, 8a14f5d6 (ledger `efa40b88..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*
