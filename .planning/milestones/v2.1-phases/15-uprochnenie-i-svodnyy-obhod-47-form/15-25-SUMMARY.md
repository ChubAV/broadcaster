---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 25
subsystem: testing
tags: [prohibitions-census, registry, record-mode, confirmation-panel, modal, htmx, jinja, criterion-6, g-1, d-05, d-16, pytest]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-24 — протокол строки и модуль `tests/test_templates/test_confirmation_panel_invariants.py`; план 15-22 — режим `--record`"
  - phase: 10-rychag-components-modal-html
    provides: "десять запретов `product-invariant` об устройстве рычага `components/modal.html` и мест подтверждения; гейт связки D-07 и инвентарь панели"
provides:
  - "десять строк группы «устройство рычага и мест подтверждения» в реестре — `enforced`; у каждой правило, покрасневшее на мутации дерева по формулировке ИМЕННО этой строки"
  - "в модуле 15-24 — 7 новых правил и 7 контролей: `hx-confirm`, признак отправки на триггере, место панели по всем вызовам и целям подмены, пустое состояние редактора во фрагменте, `id` панели из выбранной сервером величины, входы макроса панели, фокусируемость настойчивой области"
affects: [15-26, 15-27, 15-28, 15-29, 15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 18716
  tasks: 2
  commits: 3
plan_head_before: a239e6c833a309c3ee13904c58c2386cec08bb59

tech-stack:
  added: []
  patterns:
    - "Цепь предков панели собирается по тексту шаблонов: места вызова макроса, включения и блок раскладки (`extends`). Цели подмены — узлы, чью разметку ответ сносит (`innerHTML`/`outerHTML`/`delete`/`textContent`/внеполосное `true`); стратегии вставки не в счёт"
    - "Входы макроса утверждаются тремя дорогами: литерал сигнатуры исходника, `arguments`/`catch_kwargs`/`catch_varargs` собранного макроса (`ENV.from_string`), `jinja2.meta.find_undeclared_variables` шаблона"
    - "Выражение `id` вызова панели разбирается до величины: через косвенное имя (`MODAL_OPEN_EVENT_INDIRECTIONS`) и через параметр объемлющего макроса к его местам вызова"

key-files:
  created: []
  modified:
    - tests/test_templates/test_confirmation_panel_invariants.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-25: `10-02#3` держат действующие правила целиком — счёт II связки и гейт сличения копий D-16; перевод формы панели на `form_wrapper` краснит оба по этой причине"
  - "15-25: пять строк (`10-01#0`, `10-01#1`, `10-01#4`, `10-01#5`, `10-09#2`) записаны действующим правилом плюс новым правилом на ту форму нарушения, на которой действующее зелено; `10-03#2` — четырьмя правилами (транспорт и гейт фрагментных обработчиков держат «не фрагментом», враждебный идентификатор и новое правило держат ключ)"
  - "15-25: `10-01#2`, `10-02#2`, `10-09#3` записаны только новыми правилами: кандидаты планирования на замеренном нарушении зелены (гейт связки, инвентарь и правило площадки согласны с сигнатурой, выросшей вместе с вызывающими)"
  - "15-25: под «признаком отправки» строки `10-01#0` понимается любой атрибут, с которым htmx шлёт запрос сам: `hx-get/post/put/patch/delete` в обоих написаниях и `hx-boost`; `hx-boost` запрещён во всём дереве, потому что предка триггера через цепь включений разбор по тексту не собирает"
  - "15-25: ни одна из десяти строк не передана плану 15-32 — замещённых формулировок нет, правил, красных на дереве, нет"

patterns-established:
  - "Правило места по всем местам: перечень мест не переписывается — вызовы панели сверяются с `_modal_calls` гейта связки, основы `id` — с ввезённым `MODAL_OPEN_EVENT_NAMES_CALLED`, число триггеров — с `MODAL_TRIGGER_FORMS` и `MODAL_PLACES`"

requirements-completed: []

coverage:
  - id: D1
    description: "Строка `10-02#3` записана `enforced` действующими правилами, покрасневшими на переводе формы панели на `form_wrapper`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_modal_linkage_count_ii_the_component_has_exactly_one_post_form_equal_to_its_action"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_panel_quality_properties_match_the_form_wrapper"
        status: pass
    human_judgment: false
  - id: D2
    description: "Семь новых правил и семь контролей в `test_confirmation_panel_invariants.py`; каждое правило покраснело на мутации дерева, RED-верб `RED_EVIDENCE_OK` на всех семи"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_confirmation_panel_invariants.py (26 passed)"
        status: pass
      - kind: other
        ref: "node .claude/gsd-core/bin/gsd-tools.cjs check tdd-red-evidence <запись> → RED_EVIDENCE_OK ×7"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
    human_judgment: false
  - id: D3
    description: "Верность суждения «правило держит ВЕСЬ предмет формулировки» по каждой из десяти строк"
    verification: []
    human_judgment: true
    rationale: "Направление замерено машиной, но выбор синтетического нарушения — «минимальное нарушение ИМЕННО этой формулировки» — суждение исполнителя; полноту перечня способов нарушить формулировку машина не выводит (D-33 плана 15-13). Проверяет верификатор фазы по таблице этой сводки"

duration: 95min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 25: Принуждение десяти запретов устройства рычага и мест подтверждения Summary

**Все десять запретов `product-invariant` об устройстве рычага `components/modal.html` и мест подтверждения записаны в реестре `enforced`. `10-02#3` держат действующие правила. Девять строк держатся новыми правилами, у пяти из них вместе с действующим правилом и у `10-03#2` вместе с тремя. Новые правила покрывают то, на чём действующие оставались зелёными: `hx-confirm`, признак отправки кроме `hx-post`, место панели по всем вызовам и целям подмены, пустое состояние редактора во фрагменте, очищенный идентификатор задачи в ключе, параметр с умолчанием в сигнатуре, фокусируемость через сценарий. Плану 15-32 не передано ничего; `app/` не правился.**

## Performance

- **Duration:** 95 min (включает четыре прогона по 12 мин на мутациях области уведомлений и панели)
- **Started:** 2026-09-25T14:07:21Z
- **Completed:** 2026-09-25T15:42Z
- **Tasks:** 2
- **Files modified:** 2 (модуль правил группы, реестр)

## Таблица строк: правило → замер направления → строка отказа → запись

Каждый замер — временная правка файла дерева, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/` пуст (проверено после каждого замера драйвером в scratchpad). Команда прогона: `uv run pytest -q -p no:randomly [--junit-xml=…] <файл>::<правило> …`. Мутации r1–r7 проверяют новые правила, остальные — действующие.

| Строка | Правило(а) записи | Мутация дерева | Строка отказа | Запись |
|---|---|---|---|---|
| `10-01#0` форма-триггер признака отправки htmx не получает | `test_editor_schedules.py::test_the_trigger_form_never_carries_the_htmx_post`; **новое** `test_confirmation_panel_invariants.py::test_no_confirmation_trigger_form_carries_an_htmx_send_attribute` | триггер `ads/includes/ad_card.html`: `hx-post=`, `data-hx-post=`, `hx-delete=` (r2), `hx-boost="true"` (r2b) | `hx-post`/`data-hx-post` — действующее `FAILED` («форма-триггер несёт признак отправки htmx…»); **`hx-delete` и `hx-boost` — действующее `1 passed`, и 592 правила `tests/test_templates/`+`test_htmx_gates.py`+`test_editor_schedules.py` зелены**; новое на r2 — `FAILED …::test_no_confirmation_trigger_form_carries_an_htmx_send_attribute`, «ads/includes/ad_card.html#0: hx-delete»; на r2b — «hx-boost (наследуется формами-потомками)» | задача 2, `enforced` |
| `10-01#1` панель снаружи любой цели подмены | `test_account_groups.py::test_confirm_panel_lives_outside_the_row`; **новое** `…::test_every_confirmation_panel_lives_outside_every_swap_target` | r3: `admin/workers.html` — закрывающий `</div>` контейнера опроса `#admin-workers` перенесён за цикл панелей; r3b: `account_groups/includes/group_row.html` — панель перенесена внутрь строки `#group-row-{id}` | r3: **действующее `1 passed` (другой экран)**; новое `FAILED`, «admin/workers.html (цепь до base.html): панель внутри <div id="admin-workers" hx-get=…> — он сам цель своего запроса»; r3b: оба `FAILED` («панель подтверждения оказалась ВНУТРИ строки списка»; «…его id `group-row-{}` — цель подмены») | задача 2, `enforced` |
| `10-01#2` `hx-confirm` не вводится | **новое** `…::test_no_template_carries_hx_confirm` | r1: триггеру `ads/includes/ad_card.html` дописан `hx-confirm="Удалить объявление?"` | `FAILED …::test_no_template_carries_hx_confirm`, «ads/includes/ad_card.html: hx-confirm»; все прочие 476 правил `tests/test_templates/`+`test_htmx_gates.py` на r1 зелены (подтверждает замер оркестратора) | задача 2, `enforced` |
| `10-01#4` второго пустого состояния редактора во фрагменте нет; опустевший список — `HX-Location` | `test_editor_schedules.py::test_the_last_schedule_goes_to_location`; **новое** `…::test_the_editor_empty_state_is_never_instantiated_in_a_fragment` | половина `HX-Location`: условие `app/pages/schedules.py` сужено до `if not returns_to_editor:`; половина фрагмента (r4): в узел счётчика `ads/partials/sched_delete_response.html` дописано `{% if schedules_count == 0 %}{{ empty_state('Расписаний пока нет — …') }}{% endif %}` | `HX-Location`: действующее `FAILED`, `assert 200 == 204`; **r4: действующее `1 passed`, и 653 правила `tests/test_templates/`+`test_editor_schedules.py`+`test_confirm_delete_transport.py`+`test_htmx_gates.py` зелены**; новое на r4 — `FAILED`, «ads/partials/sched_delete_response.html: пустые состояния ('Расписаний пока нет — …',)» | задача 2, `enforced` |
| `10-01#5` `id` панели — величина, выбранная сервером | `test_admin_panel.py::test_a_queue_task_id_never_reaches_a_dom_identifier`; **новое** `…::test_every_panel_id_is_a_value_the_server_chose` | ключ очереди из `row.task_id` (сырого); r5: из `row.task_id\|urlencode\|replace('%', '')\|replace('/', '')`; r5b: `ads/form.html` — `id='ad-del-' ~ ad.title` (и событие триггера так же) | сырой: действующее `FAILED` («ключ события собран не только из выбранных сервером величин…»); **r5: действующее `1 passed`, и 347 правил `test_admin_panel.py`+`test_htmx_markup_gates.py`+`test_components.py` зелены; r5b: действующее места не видит (из 802 правил покраснело одно, `test_editor_delete_form_degrades_without_alpine`, на литерале `modal-open-ad-del-{id}`, то есть не по этой причине)**; новое: r5 — «admin/queue.html: id `queue_drop_modal_id(entry.account, row.task_id\|urlencode…)`», r5b — «ads/form.html: id `'ad-del-' ~ ad.title` — `ad.title`» | задача 2, `enforced` |
| `10-02#2` параметр площадки приземления не заводится | **новое** `…::test_the_panel_macro_takes_exactly_its_declared_inputs` | r6: сигнатуре `modal` дописан `landing="notice"`, `land()` читает `getElementById('{{ landing }}')` | **кандидаты зелены**: `test_the_focus_landing_is_declared_once_and_called_twice`, `test_modal_site_inventory`, `test_modal_linkage_count_iv_…` — `3 passed`; весь `tests/test_templates/` — `391 passed`, краснеют только новое правило и его контроль; новое — `FAILED`, «сигнатура 'id, …, confirm_variant="danger", landing="notice"', объявлена …» | задача 2, `enforced` |
| `10-02#3` форма панели не переводится на макрос-обёртку | `test_htmx_markup_gates.py::test_modal_linkage_count_ii_the_component_has_exactly_one_post_form_equal_to_its_action`; `…::test_the_panel_quality_properties_match_the_form_wrapper` | сырой `<form class="modal__form" …>` заменён на `{% call form_wrapper(action) %}`, `</form>` на `{% endcall %}` | оба `FAILED`: «СЧЁТ II: форм компонента `components/modal.html` с `hx-post` 0, объявлено 1: [] — форма модалки потеряла `hx-post`…»; «в макросе 0 форм, а не одна…»; всего `34 failed` в двух модулях | задача 1, `enforced` |
| `10-03#2` снятие задачи не фрагментом; ключ из позиции строки | `test_confirm_delete_transport.py::test_every_confirmed_delete_route_answers_both_transports`; `test_htmx_gates.py::test_the_number_of_fragment_response_handlers_is_the_declared_one`; `test_admin_panel.py::test_a_queue_task_id_never_reaches_a_dom_identifier`; **новое** `…::test_every_panel_id_is_a_value_the_server_chose` | половина «не фрагментом»: успешному выходу `admin_drop_task` дан `fragment=` (`respond(…, fragment=_fragment)`); половина ключа: сырой идентификатор задачи и r5 | фрагмент: `FAILED …[admin_drop_task-задача-снята]`, «снятие задачи из очереди отправки: слою письма ответили 200 вместо 204…»; `FAILED …::test_the_number_of_fragment_response_handlers_is_the_declared_one`, «обработчиков, отдающих фрагмент, найдено 26, объявлено 25»; ключ — как у `10-01#5` (r5: враждебный зелен, новое красно) | задача 2, `enforced` |
| `10-09#2` настойчивая область не получает фокусируемости | `test_components.py::test_the_landing_region_exists_in_the_shell_of_both_apps`; **новое** `…::test_the_alert_region_never_becomes_programmatically_focusable` | `tabindex="-1"` на теге `#notice-alert` в `includes/notice_area.html`; внеполосный узел `includes/notice_oob.html` заменён узлом `id="notice-alert" tabindex="-1" hx-swap-oob="true"`; скрытый `<span x-init="…getElementById('notice-alert').tabIndex = -1">`; r7: та же строка в `show()` панели | тег: действующее `FAILED` («признак фокусируемости появился и на НАСТОЙЧИВОЙ области…»); внеполосный узел: краснеют гейты долгоживущих областей (`test_the_notice_regions_are_replaced_by_content_not_by_node` и ещё 4); `x-init`: краснеют только счётчики узлов состояния (`test_the_number_of_client_state_nodes_is_the_declared_one`), то есть не по этой причине; **r7: 681 правило `tests/test_templates/`+`test_shell.py`+`test_notices_channel.py` зелено**; новое на r7 — «components/modal.html: к области обращаются по идентификатору вне тега и селектора подмены (1)» | задача 2, `enforced` |
| `10-09#3` новых параметров макросу панели нет | **новое** `…::test_the_panel_macro_takes_exactly_its_declared_inputs` | r6b: сигнатуре `modal` дописан `size="md"` | **кандидаты зелены**: `test_modal_site_inventory`, `test_modal_linkage_count_iv_…`, `test_the_panel_verb_is_a_literal_and_not_a_parameter` — `3 passed`; весь `tests/test_templates/` — `391 passed`, краснеют только новое правило и его контроль | задача 2, `enforced` |

### Что понимается под «признаком отправки» (`10-01#0`)

Формулировка говорит о признаке, с которым форма уходит через htmx вместо того, чтобы открыть панель. Такой признак — любой атрибут, с которым htmx шлёт запрос сам: `hx-get`, `hx-post`, `hx-put`, `hx-patch`, `hx-delete` в написаниях `hx-` и `data-hx-`, а также `hx-boost`, который превращает обычную отправку формы в запрос htmx. Действующее правило ищет подстроку `hx-post` и поэтому держит `hx-post` и `data-hx-post`. `hx-delete`/`hx-put`/`hx-patch`/`hx-get` и `hx-boost` оно пропускает — этот остаток держит новое правило. `hx-boost` наследуется потомками, поэтому он запрещён во всём дереве (сегодня его ноль).

## Передано плану 15-32

**Ничего.** Ни одна из десяти формулировок не описывает состояние, которое отменило позднейшее записанное решение. Ни одна не требует отката одобренной работы, и ни одно правило, написанное по формулировке, не красно на дереве. Проверено отдельно:
- `10-03#2`: ключ исхода очереди свела Фаза 11 (план 11-14), и это касается соседней строки `10-03#1`. Запрет перевода на фрагмент и ключ из позиции строки на дереве стоят: в обработчике есть пометка «ТРАНСПОРТ ОСТАЁТСЯ ПЕРЕХОДОМ (D-06/D-09 Фазы 10)», у макроса `queue_drop_modal_id(entry.account, loop.index0)`.
- `10-01#0`: в формулировке «18 мест диспетчеризации», и мест по-прежнему 18 (`MODAL_TRIGGER_FORMS`, `MODAL_PLACES`).
- `10-02#3`, `10-09#3`: сигнатура в дереве ровно та, что оставил план 10-09 после снятия параметра глагола.

## Accomplishments

- Задача 1: замер направления по всем десяти строкам (таблица выше). `10-02#3` записан `enforced` двумя действующими правилами. По девяти строкам найдена форма нарушения, на которой действующие правила зелены, либо таких правил нет вовсе; эти строки переданы задаче 2 с названной частью.
- Задача 2: в модуль плана 15-24 добавлены семь правил и семь контролей. Модуль ввозит `ENV`, `MODAL_COMPONENT`, `MODAL_PLACES`, `MODAL_SIGNATURE_RE` из `test_components.py` и `_modal_calls`, `_modal_trigger_forms`, `_id_stem`, `MODAL_TRIGGER_FORMS`, `MODAL_OPEN_EVENT_NAMES_CALLED`, `MODAL_OPEN_EVENT_INDIRECTIONS` с разборщиками из `test_htmx_markup_gates.py`. Перечня мест модуль не переписывает. Докстринг модуля дополнен вторым предметом с тождествами строк и границами «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» по каждой новой строке (заголовок по-прежнему один).
- Правило места (`10-01#1`) собирает 19 цепей предков для 11 вызовов панели. Цепи доходят до `base.html` либо до шаблона-фрагмента, который никто не включает. Проверяются 24 скелета идентификаторов целей подмены и узлы-цели собственных запросов. Сегодня нарушений ноль.
- Реестр: `product-invariant` было `enforced 11 / partially-enforced 8 / unresolved 51`, стало `21 / 8 / 41`. Сумма по диспозициям — 321, биекция в согласии. Дифф реестра — ровно 10 строк.

## Task Commits

1. **Задача 1: замер направления по действующим правилам** — `048edab5` (chore): `10-02#3` записан `enforced`.
2. **Задача 2: новые правила группы рычага** — `f0cbf430` (test): семь правил и семь контролей. `f939b8c0` (chore): девять строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-25)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute`, режим `workflow.tdd_mode: true`: гейт TDD на таком плане инертен. Продукт по плану не правится, поэтому цикла «красный тест → правка продукта → зелёный» здесь нет. **RED каждой строки измерен так, как требует владелец (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Действующие правила:** мутации дерева, строки отказа — в таблице. Каждая мутация отменена `git checkout -- <файл>`, после каждой `git diff --exit-code -- app/` пуст.
- **Новые правила:** семь мутаций дерева r1–r7, по одной на правило (r5 служит двум строкам, r6 — двум). Каждая дала `FAILED tests/test_templates/test_confirmation_panel_invariants.py::<правило>` со строкой `1 failed` и `exit=1` (у r3, r5 и r7 — `1 failed, 1 passed`, где зелёное — действующее правило, прогнанное рядом). Причинные литералы — в таблице. Прогоны писали `--junit-xml`. Одноразовый скрипт в scratchpad (не в дереве) переводил их в запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP. `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`) на всех семи.
- **Точность на дополнительных мутациях:** r2b (`hx-boost`), r3b (панель в строке группы), r5b (`ad.title`), r6b (`size="md"`) — новое правило красно, и названо то место, которое мутация и затронула.
- **Контроли на синтетике** (в модуле): каждый утверждает, что копия с нарушением названа, а исправное дерево или точная копия — нет. Все зелены.
- Коммит `test(15-25)` предшествует записям второй задачи. Коммита `feat(15-25)` нет, потому что продукт не правился. REFACTOR не было.

## Files Created/Modified

- `tests/test_templates/test_confirmation_panel_invariants.py` — семь правил группы рычага и семь контролей, 1045 строк добавлено (модуль — 1522 строки).
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 10 строк, записаны только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Правило места панели сильнее, чем предлагал план. План предлагал «вызов панели не лежит внутри цели формы-триггера того же места». Правило берёт ЛЮБУЮ цель, которую сносит любой ответ дерева: внеполосные узлы, `hx-target`, цель `form_wrapper`, узлы-цели собственного запроса. Цепь предков идёт через макросы, включения и раскладку, потому что панель почти везде вызвана на верхнем уровне макроса карточки, и в одном файле предков у неё нет.
- Правило `id` панели разбирает выражение до величины и не довольствуется враждебными данными на одном экране. Очищенный идентификатор задачи проходит любую проверку по символам, но остаётся «переводом ключа на идентификатор задачи», а это запрещено решением WR-04.
- Входы макроса утверждаются тремя дорогами. Сигнатура одна не держит параметр, вернувшийся через `kwargs` или через имя контекста — а именно так параметр «возвращается под другим именем» (слова `10-09#3`).
- В правиле пустого состояния законные пустые состояния фрагментов объявлены поимённо (`EDITOR_FRAGMENT_EMPTY_STATES`, одно место, снято с дерева). `sched_card.html` законно печатает пустое состояние «нет аккаунта», поэтому запрет самого макроса `empty_state` во фрагментах краснил бы дерево.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Строка `10-09#2` получила новое правило, хотя план ждал только замера кандидата**
- **Found during:** задача 1
- **Issue:** кандидат `test_the_landing_region_exists_in_the_shell_of_both_apps` краснеет на `tabindex` в теге области. Строка в `show()` панели, ставящая `tabIndex` узлу по идентификатору, зелена у всех 681 правила трёх модулей (r7).
- **Fix:** новое правило `test_the_alert_region_never_becomes_programmatically_focusable` с контролем. Строка записана с обоими правилами.
- **Files modified:** модуль правил, реестр
- **Commit:** `f0cbf430`, `f939b8c0`

**2. [Rule 2 - Missing critical] Строка `10-03#2` получила новое правило на ключ**
- **Found during:** задача 1
- **Issue:** половину «не фрагментом» держат два действующих правила. Ключ держит правило враждебного идентификатора, но на идентификаторе задачи, очищенном `urlencode` и срезкой `%` и `/`, оно зелено (r5, 347 правил).
- **Fix:** правило `id` панели (общее с `10-01#5`) разбирает косвенное имя `queue_drop_modal_id` до аргумента позиции. Запись несёт четыре правила.
- **Commit:** `f0cbf430`, `f939b8c0`

**3. [Rule 1 - Bug] Драйвер замеров передавал код выхода числом в `argv`**
- **Found during:** задача 2, первые прогоны r1/r2
- **Issue:** одноразовый драйвер scratchpad падал до записи RED-улики. Мутации при этом были отменены (`app clean after revert=True`).
- **Fix:** `str(run.returncode)`; r1 и r2 прогнаны заново, верб дал `RED_EVIDENCE_OK`. Файлов дерева поправка не касается.

---

**Total deviations:** 3 auto-fixed (2 Rule 2, 1 Rule 1 в одноразовом инструменте)
**Impact on plan:** первые две поправки добавляют к записи правило, доказанное замером. Правка продукта не понадобилась, и ни одна формулировка не облегчена.

## Issues Encountered

- Две первые формы мутации `10-01#4` (новый внеполосный узел; пустое состояние в узле счётчика без условия) краснили правила по другой причине: счётчик внеполосных блоков и посимвольное сличение линейки. Остаток показала третья форма — условное пустое состояние внутри существующего узла. Первые две в таблицу как доказательство не взяты.
- Две формы `10-09#2` (новый узел `x-data`, внеполосная подмена узлом) краснят действующие гейты по иной причине. Форма в существующем выражении (`show()`) показала остаток.
- Прогоны по 12 мин с мутациями уходили в фон (предел инструмента — 10 мин). Параллельных прогонов pytest не было: следующий шаг всегда ждал отмены мутации (`git status --short app/` пуст).

## Verification

- `uv run pytest tests/test_templates/test_confirmation_panel_invariants.py -q -p no:randomly` → `26 passed`.
- `uv run pytest tests/test_templates/ -q -p no:randomly` → `393 passed` (было 379: +14).
- `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` → `184 passed`.
- Проверка уровня плана `uv run pytest tests/test_templates/ tests/test_pages/test_editor_schedules.py tests/test_pages/test_account_groups.py tests/test_planning/ -q -p no:randomly` → `813 passed`, `EXIT=0`.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` (после каждой группы записей).
- `<verify>` задачи 1 (`-k "modal or trigger or panel or landing or linkage"`) → `73 passed, 424 deselected`; выборка непуста.
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие»; `--breakdown` → `product-invariant: enforced 21 (3), partially-enforced 8 (8), unresolved 41 (1)`, «сумма по диспозициям области решений: 321».
- `grep -c 'def test_no_template_carries_hx_confirm'` → `1`; `grep -c 'ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ'` → `1`; `git diff --exit-code -- app/` → пусто; `git diff a239e6c8..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись: в модуле нет утверждений 302, вызовов целей перехода и пар деградации (`PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — прогоны гейтов страниц зелены). Новый `import yaml` не заведён (новые ввозы — `ast`, `typing.NamedTuple`, `jinja2.meta`).
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют каталоги `tests/test_templates/` и `tests/test_planning/` целиком, три гейта страниц и `test_editor_schedules.py` с `test_account_groups.py`. Окна в WINDOWS.md для этого не открыто.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-26…15-31 проходят свои группы тем же протоколом. Образец этого плана: действующее правило краснеет на прямой форме нарушения, и нужно искать форму, которая обходит его разборщик — другой глагол, другое место цепи, очищенное значение, параметр с умолчанием, сценарий вместо атрибута.
- Остаток `product-invariant`: 8 частичных строк и 41 неразобранная (`enforcement-required`).
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_templates/test_confirmation_panel_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: 048edab5, f0cbf430, f939b8c0 (ledger `a239e6c8..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*
