---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 02
subsystem: ui
tags: [htmx, jinja2, fastapi, gates, tdd, oob-swap]

# Dependency graph
requires:
  - phase: 09-01
    provides: "слой ответа respond() на живом обработчике, count_rule_oob.html, MACRO_DEFINITION_SITES, сканер вызывающих _macro_callers, помощник _group_counts, форма ключа параметрической записи"
  - phase: 08-sloy-otveta-i-geyty-razmetki
    provides: "respond()/location_response(), фикстура htmx_client, девять машинных правил разметки, счётчик отставания NOT_YET_CONVERTED"
provides:
  - "account_groups/partials/delete_response.html — форма ответа БЕЗ основной цели свопа: три внеполосных узла верхнего уровня"
  - "параметр hx_post у макроса панели подтверждения — признак отправки на одном месте из шестнадцати, умолчание не двигается"
  - "account_groups_delete идёт через слой ответа во ВСЕХ ветках — второй переведённый обработчик вехи"
  - "резолюция γ1: _macro_default_value — литеральное умолчание параметра макроса удовлетворяет правилу метода G-3"
  - "ParametricTarget + PARAMETRIC_SWAP_TARGETS — перечень целей подмены, печатаемых параметром макроса"
  - "_classified_target_sites — разбор МЕСТ цели по трём разрядам значения (арифметика мест, а не идентификаторов)"
  - "_swap_declaring_templates — ЕДИНСТВЕННОЕ описание множества «шаблоны, объявляющие цель подмены»; потребитель — правило D-08 плана 09-03"
  - "test_cancel_is_never_disabled — буква QUAL-01 стала машинным правилом с доказанными зубами"
affects: [09-03, 09-04, "Фаза 10 (FORM-06)", "Фаза 11", "Фаза 12 (FETCH-01)"]

# Actuals (#2632) — та же шкала estimateTokens (chars/4) по реализованному диффу.
actuals:
  tokens: 22008
  tasks: 3
  commits: 6

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "опциональный параметр макроса с умолчанием, не меняющим разметку ни на символ (проверяется посимвольным сравнением рендера с эталоном)"
    - "ответ без основной цели свопа: hx-swap=\"none\" на форме, всё содержимое ответа — внеполосные узлы верхнего уровня"
    - "снятие узла внеполосно: hx-swap-oob=\"delete\" с целью по собственному id тега"
    - "ветвление ответа по числам аккаунта, а не по факту нахождения строки — побайтовая неотличимость найденного и не найденного"
    - "γ1: литеральное умолчание параметра из сигнатуры {% macro %} — там и только там, где переопределения вызывающим не бывает"
    - "арифметика МЕСТ по трём разрядам значения вместо сложения мест с идентификаторами"

key-files:
  created:
    - app/templates/account_groups/partials/delete_response.html
  modified:
    - app/templates/components/modal.html
    - app/templates/account_groups/includes/group_row.html
    - app/pages/account_groups.py
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Вопрос G-11 закрыт ИЗМЕРЕНИЕМ: множество целей подмены ПУСТО, пересечение с внеполосными целями ПУСТО, второй перечень («идентификатор в двух ролях по замыслу») НЕ заведён — его несущее утверждение было бы ложью на первой же записи"
  - "PARAMETRIC_SWAP_TARGETS объявлен БЕЗУСЛОВНО и от измерения не зависит: факт «цель печатается параметром» верен независимо от любого пересечения, а от перечня зависит правило D-08 плана 09-03"
  - "Несущее правило считает МЕСТА по трём разрядам, а не складывает места с идентификаторами: на этой фазе равенство сошлось бы случайно, а правило писано для Фаз 10-15"
  - "γ1 применена ТОЛЬКО к методу формы и только потому, что метод не переопределяет ни один вызывающий; на цели блокировки действует правило 3 (поле callers), потому что γ1 молча одобрила бы вызывающего, накрывшего кнопку Отмены"
  - "Правило «кнопка Отмены не блокируется» проверяет ТРИ множества селекторов плюс саму кнопку: без четвёртой половины правило осталось бы зелёным на кнопке, ставшей submit-кнопкой"
  - "Ветвление «список опустел» считается по _group_counts аккаунта из АДРЕСА, а не по найденной строке: иначе чужая группа получала бы отличимый ответ"

patterns-established:
  - "Прозаическая ссылка на литерал, отсутствие которого проверяется грепом, записывается СЛОВАМИ (иначе комментарий о запрете сам его нарушает)"
  - "Инвентарное число правится вместе с записью летописи, объясняющей, из чего оно складывается"
  - "Литерал без имени пересчитывается ИСПОЛНЕНИЕМ каждой фазой, которая двигает соседние числа"

requirements-completed: []

coverage:
  - id: D1
    description: "Удаление группы идёт через htmx: 200, тело без <!DOCTYPE, три внеполосных узла — снятие строки, снятие панели подтверждения, линейка счётчика"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_returns_oob_nodes"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_oob_node_is_a_top_level_node_of_its_response"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_oob_blocks_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D2
    description: "Удаление деградирует без htmx: прежний 302 на экран групп, строка при этом удалена"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_degrades_without_htmx"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_such_form_keeps_its_method_and_action"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_post_attribute_matches_the_action_character_for_character"
        status: pass
    human_judgment: false
  - id: D3
    description: "Опустевший список закрывается 204 + HX-Location на тот же адрес; второй отрисовки пустого состояния нет"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_last_group_goes_to_location"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ответ найденной и не найденной группы совпадает побайтово; чужой account_id в пути не удаляет строку и отвечает неотличимо"
    requirement: QUAL-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_repeated_delete_is_harmless_over_htmx"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_does_not_trust_the_account_id_from_the_url_over_htmx"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_repeated_delete_is_harmless"
        status: pass
    human_judgment: false
  - id: D5
    description: "Умолчание макроса панели подтверждения не сдвинулось ни на символ: рендер без hx_post посимвольно равен эталону, снятому до правки, и не содержит ни одной htmx-подстроки"
    requirement: FORM-02
    verification:
      - kind: other
        ref: "diff рендера modal(**MODAL_ARGS) до и после правки — идентичны, 1878 байт"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py — 33 утверждения панели подтверждения"
        status: pass
    human_judgment: false
  - id: D6
    description: "У переведённого account_groups_delete нет собственного RedirectResponse ни в одной ветке, включая «нет сессии»; счётчик отставания вехи убыл 35 → 34"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_no_converted_handler_builds_its_own_redirect"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_backlog_matches_the_declared_count"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_without_session_goes_to_login"
        status: pass
    human_judgment: false
  - id: D7
    description: "Параметрическая цель подмены объявлена безусловно, ключом по файлу разборщика; поле callers сверено с _macro_callers; несущее правило считает МЕСТА по трём разрядам"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_parametric_swap_target_carries_a_reason"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_parametric_swap_targets_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_declared_parametric_target_is_actually_parametric"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_declared_parametric_caller_actually_calls_the_macro"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_swap_target_is_either_literal_or_declared_parametric"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_an_undeclared_parametric_target_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D8
    description: "_swap_declaring_templates содержит account_groups/includes/group_row.html — предусловие правила D-08 плана 09-03 проверено ЗДЕСЬ"
    verification:
      - kind: other
        ref: "uv run python -c \"... assert 'account_groups/includes/group_row.html' in _swap_declaring_templates(t)\" — измерено, множество {account_groups/includes/group_row.html, components/form_wrapper.html}"
        status: pass
    human_judgment: false
  - id: D9
    description: "Кнопка Отмены не блокируется никогда: правило проверяет три множества селекторов и сам тип кнопки, зубы доказаны и подстановкой, и временной правкой живого дерева"
    requirement: QUAL-01
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_cancel_is_never_disabled"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_disabled_cancel_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D10
    description: "Инвентарные числа сдвинуты и утверждены собственными обходами: HX_POST_PLACES 2→3, OOB_BLOCKS 7→9, MACRO_DEFINITION_SITES_DECLARED 1→2, NOT_YET_CONVERTED_COUNT 35→34, PARAMETRIC_SWAP_TARGETS_DECLARED 0→1; пять чисел подтверждены неподвижными; литерал len(paths) пересчитан исполнением"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_positive_the_untouched_tree_keeps_every_gate_green"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_both_branches_of_the_editor_action_are_extracted"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_positive_the_untouched_source_tree_keeps_every_gate_green"
        status: pass
    human_judgment: false
  - id: D11
    description: "Осиротевшая панель подтверждения после удаления действительно снята со страницы, а после подмены строки тумблером панель не задвоилась; Alpine в оставшихся панелях жив"
    verification: []
    human_judgment: true
    rationale: "httpx не свопает и не собирает внеполосные узлы: тест видит ТЕКСТ ответа, а факт снятия узла, отсутствие задвоения и живость Alpine — свойства браузера. Пункты 3 и 5 (частично) ручного UAT плана 09-04"
  - id: D12
    description: "Индикатор «запрос идёт» на форме панели подтверждения виден при медленном удалении и не мигает при быстром; кнопка подтверждения действительно блокируется, а Отмена остаётся нажимаемой"
    verification: []
    human_judgment: true
    rationale: "Порог 300 мс на глаз и поведение блокировки при реальной сети — свойства браузера; машинно проверено лишь ОБЪЯВЛЕНИЕ селекторов в разметке и порога в стилях. Пункт 6 ручного UAT"

# Metrics
duration: 57 min
completed: 2026-08-29
status: complete
---

# Phase 9 Plan 02: Удаление группы на сквозном контракте формы Summary

**Удаление группы переведено на ответ БЕЗ основной цели свопа — `hx-swap="none"` на форме панели подтверждения и три внеполосных узла в теле, включая снятие осиротевшей панели, — а невидимая для гейта параметрическая цель подмены объявлена перечнем, на котором держится правило границы клиентского состояния плана 09-03.**

## Performance

- **Duration:** 57 min
- **Started:** 2026-08-29T18:17:20Z (прогон предусловия — 70 зелёных)
- **Completed:** 2026-08-29T19:14:15Z
- **Tasks:** 3 из 3
- **Files modified:** 7 (1 создан, 6 изменено)

## Accomplishments

- **Второй путь экрана доказан целиком.** Один и тот же маршрут `/accounts/{a}/groups/{g}/delete` отвечает тремя внеполосными узлами запросу htmx, 204 + `HX-Location` на опустевшем списке и прежним 302 запросу без htmx. Обе половины закреплены парами SP-3, а несущая половина второй — `assert "<!DOCTYPE" not in response.text`.
- **Механизм снятия осиротевшей панели заведён здесь, а не отложен.** Панель сознательно стоит СНАРУЖИ удаляемой строки, поэтому вместе с ней не уезжает; второй OOB-узел снимает её по собственному `id`. Фаза 10 наследует механизм готовым на 16 мест.
- **Умолчание макроса панели подтверждения не сдвинулось ни на символ** — доказано посимвольным сравнением рендера с эталоном, снятым ДО правки, и отсутствием пяти htmx-подстрок в результате.
- **Вопрос G-11 закрыт ИЗМЕРЕНИЕМ, а не допущением** (см. раздел ниже), и решение «второй перечень не заводится» записано с основанием.
- **Буква QUAL-01 «кнопка Отмены не блокируется никогда» стала машинным правилом** с зубами, доказанными дважды: подстановкой в копию дерева и временной правкой живого дерева.
- **Счётчик прогресса вехи убыл во второй раз:** `NOT_YET_CONVERTED_COUNT` 35 → 34.

## Измерение G-11 — дословный вывод команды шага 1

Команда (исполнена на ИТОГОВОМ дереве, после задачи 1):

```
uv run python -c "import sys; sys.path.insert(0,'tests/test_templates'); from test_htmx_markup_gates import _all_templates, _swap_target_ids, _oob_target_ids; t=_all_templates(); print(sorted(_swap_target_ids(t))); print(sorted(_oob_target_ids(t))); print(sorted(_swap_target_ids(t) & _oob_target_ids(t)))"
```

Вывод дословно:

```
[]
['account-groups-count', 'ad-id-field', 'ad-preview', 'ad-summary', 'autosave-indicator', 'group-del-{{ group_id }}', 'group-row-{{ group_id }}', 'notice', 'notice-alert']
[]
```

**Множество целей подмены ПУСТО. Множество внеполосных целей — девять значений. ПЕРЕСЕЧЕНИЕ ПУСТО.**

**Решение: второй перечень — «идентификатор в двух ролях по замыслу» — НЕ ЗАВЕДЁН, и это результат измерения, а не умолчание.** Основание: цель формы тумблера ПАРАМЕТРИЧЕСКАЯ — макрос-обёртка печатает `hx-target="{{ target }}"`, а `_swap_target_ids` кладёт в множество только остаток значения, начинающегося с решётки, — поэтому в множество целей подмены она не попадает вовсе, и столкновения с внеполосной целью снятия строки не возникает. Разведка (§1.1) предсказывала столкновение при допущении, что цель записана в шаблоне ЛИТЕРАЛЬНО; под макросом-обёрткой плана 09-01 допущение не сбылось. Третье, несущее утверждение рекомендации (b) RESEARCH §1.3 — «каждая запись ФАКТИЧЕСКИ лежит в пересечении» — было бы ложью на первой же записи, поэтому перечень не заводится, а `grep -c 'ID_IN_TWO_ROLES_DECLARED'` по файлу гейта возвращает `0`.

Правило G-11 для ЛИТЕРАЛЬНЫХ идентификаторов при этом не ослаблено ничем: `test_no_id_is_both_a_swap_target_and_an_oob_target` не тронут, его контроль продолжает краснеть на `#ad-preview`, и фильтр, отбрасывающий шаблонизированные значения, в `_swap_target_ids` НЕ заведён.

## Инвентарные числа

| Число | Было | Стало | Чем утверждено |
|---|---|---|---|
| `HX_POST_PLACES` | 2 | **3** | `test_the_number_of_htmx_post_places_is_the_declared_one` |
| `OOB_BLOCKS` | 7 | **9** | `test_the_number_of_oob_blocks_is_the_declared_one` |
| `MACRO_DEFINITION_SITES_DECLARED` | 1 | **2** | `test_the_number_of_macro_definition_sites_is_the_declared_one` |
| `NOT_YET_CONVERTED_COUNT` | 35 | **34** | `test_the_backlog_matches_the_declared_count` |
| `PARAMETRIC_SWAP_TARGETS_DECLARED` | — | **1** | `test_the_number_of_parametric_swap_targets_is_the_declared_one` |
| `HX_TARGETS` | 1 | 1 (не двинуто) | `test_the_number_of_swap_targets_is_the_declared_one` |
| `CLIENT_STATE_NODES` | 24 | 24 (не двинуто) | `test_the_number_of_client_state_nodes_is_the_declared_one` |
| `FRAGMENT_ROUTES_DECLARED` | 12 | 12 (не двинуто) | `test_the_number_of_fragment_routes_is_the_declared_one` |
| `HX_HEADER_WRITES` | 2 | 2 (не двинуто) | обход мест записи заголовков |
| `POST_HANDLERS` | 36 | 36 (не двинуто) | `test_every_post_handler_is_classified` |
| `len(paths)` (литерал без имени) | 2 | **2, пересчитано исполнением** | `test_both_branches_of_the_editor_action_are_extracted` |

⚠️ **`NOT_YET_CONVERTED_COUNT` 35 → 34 — это ДВИЖЕНИЕ СЧЁТЧИКА ПРОГРЕССА ВЕХИ, а не правка теста под реализацию.** Текст отказа `test_the_backlog_matches_the_declared_count` написан заранее и прямо требует опустить число и снять переведённый обработчик из перечня, когда очередная фаза его переведёт. Число разделено на два утверждения (рост = регрессия, падение = прогресс) именно затем, чтобы прогресс не читался как поломка. После этого движения оба входа изменения состояния экрана групп аккаунта идут одним слоем ответа, и у G-2 стало два предмета вместо одного.

⚠️ **`len(paths)` ПЕРЕСЧИТАН ИСПОЛНЕНИЕМ ПОВТОРНО и снова остался равен 2.** Мест отправки стало три, но третье — определение макроса панели подтверждения — входит в `MACRO_DEFINITION_SITES` и в `_action_sites` не попадает: адрес подтверждения приходит параметром. Измерено прогоном `_extracted_paths`, а не выведено из ожидания: `['/ads/new', '/ads/{}/edit']`.

## Task Commits

1. **Задача 1 (tdd) — RED: числа, снятие обработчика из отставания, четыре пары SP-3** — `4f38276` (test)
2. **Задача 1 — GREEN: параметр макроса, шаблон ответа, обработчик, резолюция γ1** — `e9faee4` (feat)
3. **Задача 2 (tdd) — RED: пять правил параметрической цели и её контроль** — `566efe6` (test)
4. **Задача 2 — GREEN: перечень, разбор мест по разрядам, `_swap_declaring_templates`** — `5496f4a` (feat)
5. **Задача 3 (tdd) — RED: правило кнопки отказа и его контроль** — `429c47d` (test)
6. **Задача 3 — GREEN: три множества селекторов плюс сам тип кнопки** — `046f545` (feat)

_Порядок RED → GREEN соблюдён в каждой из трёх задач: гейтовая последовательность `test(09-02) → feat(09-02)` присутствует трижды._

## Files Created/Modified

- `app/templates/account_groups/partials/delete_response.html` — **NEW.** Плоское тело: два узла `hx-swap-oob="delete"` (снятие строки и снятие панели, цель — собственный `id` тега) плюс включение узла счётчика. Шапка называет обе цены: неотличимость найденной и не найденной группы и накопление панелей `role="dialog"` без второго узла.
- `app/templates/components/modal.html` — опциональный параметр `hx_post=false` в сигнатуре; условная вставка внутри открывающего тега формы (`hx-post` тем же выражением, что и `action`; `hx-swap="none"`; общее умолчание цели блокировки; селектор индикатора) и условный узел индикатора внутри тела формы. Требование к вызывающему об `id` не ослаблено, докстринг не сокращён.
- `app/templates/account_groups/includes/group_row.html` — вызов панели подтверждения получил `hx_post=true`; форма-триггер удаления и все прежние комментарии не тронуты.
- `app/pages/account_groups.py` — `account_groups_delete` переписан на `respond()` во всех ветках; ветвление по `_group_counts` аккаунта из адреса; нульарная асинхронная `_fragment()`; тройной `WHERE`, чистка расписаний и комментарий «Ответ ОДИНАКОВ…» сохранены дословно.
- `tests/test_pages/test_account_groups.py` — пять новых тестов: деградация без htmx, три внеполосных узла, переход на опустевшем списке, чужой `account_id` под htmx, побайтовое равенство повторного удаления.
- `tests/test_pages/test_htmx_gates.py` — счётчик отставания 35 → 34 с записью летописи; ключ обработчика снят.
- `tests/test_templates/test_htmx_markup_gates.py` — четыре инвентарных числа, запись `MACRO_DEFINITION_SITES`, резолюция γ1 (`_macro_default_value`, `_resolved_attr_value`), `ParametricTarget` + `PARAMETRIC_SWAP_TARGETS` + `PARAMETRIC_SWAP_TARGETS_DECLARED`, `_classified_target_sites`, `_offenders_undeclared_parametric_target`, `_swap_declaring_templates`, `_cancel_button_sites`, `_caller_argument_values`, `_covers_the_cancel_button`, `_offenders_cancel_is_disabled`; шесть новых правил и два новых контроля (17 → 19).

## Decisions Made

- **Область применения γ1 ограничена намеренно и второго экземпляра механизма не заведено.** `_macro_default_value` сводит к литеральному умолчанию только «голое» выражение параметра (`{{ имя }}`) и только там, где переопределения вызывающим не бывает: метод формы панели не переопределяет ни один из шестнадцати вызовов. На цели блокировки действует правило 3 §«Форма ключа параметрической записи» (поле `callers` + сканер `_macro_callers`), потому что правило, зеленеющее по умолчанию макроса, молча одобрило бы вызывающего, передавшего селектор, накрывающий кнопку Отмены.
- **Перечень параметрических целей объявлен БЕЗУСЛОВНО, а не по результату измерения.** Прежняя форма задачи делала его существование условным, а от него зависит правило D-08 плана 09-03 — то есть план волны 3 опирался бы на результат измерения волны 2. Разведены две разные вещи: факт «цель печатается параметром» верен независимо от любого пересечения; факт «идентификатор в двух ролях» решает только судьбу ВТОРОГО перечня.
- **Несущее правило считает МЕСТА, а не идентификаторы.** Сложение «мест = идентификаторов + записей перечня» складывало бы список, множество и ключи словаря; на этой фазе равенство `1 == 0 + 1` сошлось бы случайно. Верная форма разбивает каждое место по значению ровно в один из трёх разрядов, требует, чтобы сумма трёх разрядов равнялась числу мест (незаявленная форма значения замечается, а не относится к остатку), и проверяет вложенность файлов параметрического разряда в ключи перечня. Граница названа честно: ключ — файл, поэтому два параметрических места в одном файле покрываются одной записью, и Фаза 10 обязана эту границу пересмотреть.
- **`_swap_declaring_templates` объявлен ЗДЕСЬ, рядом с перечнем, а не в плане 09-03.** Без второго слагаемого (`callers`) множество сводится к `components/form_wrapper.html` — файлу, в котором `x-data` нет вовсе, — и правило D-08 зеленело бы по построению, а его контроль не покраснел бы ни на чём. Предусловие проверено ЗДЕСЬ исполнением: `{'account_groups/includes/group_row.html', 'components/form_wrapper.html'}`.
- **У правила кнопки отказа ЧЕТЫРЕ половины, а не три.** К трём множествам селекторов добавлена проверка самого типа кнопки: селекторы могли бы остаться прежними, а кнопка — стать submit-кнопкой, и ни один разбор селекторов этого бы не заметил. Ровно этой подстановкой и краснеет контроль.
- **Ветвление «список опустел» считается по числам аккаунта из АДРЕСА.** Для чужой и несуществующей группы `_group_counts` даёт те же числа, что и до запроса, и ветка получается той же, какой она была бы у последнего успешного удаления в этом же аккаунте: различимого признака не появляется ни в статусе, ни в теле, ни в заголовках (T-9-10).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Тест `test_repeated_delete_is_harmless_over_htmx` был зелен по построению в фазе RED**

- **Found during:** Задача 1 (RED)
- **Issue:** Написанный по плану, тест сравнивал два ответа между собой — и проходил ДО реализации: фикстура `htmx_client` следует перенаправлению незаметно, и обоими ответами оказывалась одна и та же целая страница экрана групп, равная себе самой. Тест утверждал бы тавтологию, а про ответ удаления не говорил бы ничего. По правилу fail-fast TDD зелёный тест в фазе RED расследуется, а не принимается (тот же вид отказа, что и отклонение №2 плана 09-01).
- **Fix:** Добавлена несущая половина `assert "<!DOCTYPE" not in first.text` (форма SP-3), после чего тест стал красным до реализации и красным по правильной причине.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Verification:** прогон `-k repeated_delete_is_harmless` до реализации — красный; после — зелёный.
- **Committed in:** `4f38276` (коммит RED задачи 1)

**2. [Rule 1 - Bug] Комментарий-запрет сам нарушал греп критерия приёмки**

- **Found during:** Задача 2 (GREEN, прогон критериев)
- **Issue:** Критерий приёмки требует, чтобы `grep -c 'if "{{" in value: continue'` по файлу гейта возвращал `0` — то есть чтобы фильтр, снимающий правило со всех построчных целей, нигде не был заведён. Комментарий, объяснявший запрет, набирал условие ДОСЛОВНО, и греп возвращал `1`: проверка краснела бы на документации о запрете вместо его нарушения. Это ровно та ловушка, которую план 09-01 записал решением «прозаические ссылки на проверяемые грепом литералы записаны СЛОВАМИ», — здесь она встретилась в обратную сторону.
- **Fix:** Запрет переписан словами («условие, отбрасывающее значение с выражением шаблонизатора»), и причина этого записана рядом абзацем.
- **Files modified:** `tests/test_templates/test_htmx_markup_gates.py`
- **Verification:** `grep -c 'if "{{" in value: continue'` возвращает `0`; тело `_swap_target_ids` фильтра не содержит.
- **Committed in:** `5496f4a` (коммит GREEN задачи 2)

---

**Total deviations:** 2 auto-fixed (2 ошибки в тестовом коде, обе — виды «правило зелено по построению»).
**Impact on plan:** Ни одно отклонение не расширило предмет плана; оба усилили проверки, которые иначе вошли бы в проект тавтологичными. Запреты плана соблюдены: умолчание макроса панели не сдвинулось ни на символ (доказано сравнением рендеров), `hx-confirm` не введён, панель не переехала внутрь строки, второй экземпляр пустого состояния не заведён, требование к вызывающему об `id` не ослаблено, правило G-11 не снято, фильтр в `_swap_target_ids` не добавлен.

## Issues Encountered

- **Полный прогон `tests/test_templates/ tests/test_pages/` занимает ~21 минуту** и дважды упирался в потолок времени одного вызова инструмента. Обойдено запуском в фоне с записью в файл; на результат не влияет.
- **Известный красный `full-suite-ads-editor-order-pollution`** (`.planning/todos/pending/`) в прогонах этого плана НЕ проявился: он про `test_image_base_url_comes_from_app_settings` и виден только в прогоне всей суиты `tests/`. Планом он не втягивается, как и записано в разделе `<verification>`.

## Known Stubs

Заглушек нет. Единственный созданный файл печатает реальные значения: `group_id` приходит сегментом маршрута, `active_groups`/`total_groups` — из `_group_counts()`, а узел линейки включается тот же самый, что и в ответе тумблера.

## Threat Flags

Новой поверхности вне `<threat_model>` плана не появилось. Единственный новый путь — фрагментный ответ уже существовавшего маршрута `POST /accounts/{account_id}/groups/{group_id}/delete`; вердикт доступа (тройной `WHERE`) вычисляется ДО развилки транспорта и сохранён дословно, чистка расписаний идёт прежним методом репозитория, новых мест записи заголовков `HX-*` не заведено (`HX_HEADER_WRITES` остаётся 2 и утверждается тестом). Митигации T-9-07, T-9-10 и T-9-03 реализованы и закреплены тестами (см. `coverage` D3, D4).

## Requirements

`requirements-completed` оставлен **пустым намеренно**, и `REQUIREMENTS.md` этим планом не правился. Все три объявленных идентификатора заявлены также соседними планами фазы, у которых сводки ещё нет:

| ID | Кто ещё заявляет | Готов к отметке |
|----|------------------|-----------------|
| FORM-02 | 09-01 (сводка есть), 09-03 | нет |
| QUAL-01 | 09-01 (сводка есть), 09-03 | нет |
| QUAL-02 | 09-01 (сводка есть), 09-04 | нет |

Отметку делает последний завершивший план фазы — ровно ради этого заведён гейт общих идентификаторов.

## Notes for the Orchestrator

- `STATE.md` и `ROADMAP.md` этим агентом не изменялись (режим worktree).
- Чекпойнтов в плане нет; `human_verify_mode: end-of-phase`, поэтому ручные пункты (D11, D12) уйдут в общий разбор конца фазы через план 09-04.
- Временная проверка зубов правила кнопки отказа выполнена НА ЖИВОМ ДЕРЕВЕ и откачена: `type="button"` у кнопки `x-ref="cancel"` заменён на `type="submit"` ⇒ `-k cancel` покраснел (оба теста), после отката — зелёный. Рабочее дерево чистое, временный файл эталона рендера не коммитился.

## Next Phase Readiness

Готово к плану 09-03:

- `PARAMETRIC_SWAP_TARGETS` объявлен безусловно, его `callers` сверены с `_macro_callers`, и `_swap_declaring_templates` содержит `account_groups/includes/group_row.html` — предусловие правила D-08 проверено ЗДЕСЬ и исполнением, а не описанием. План 09-03 обязан ВЫЗЫВАТЬ `_swap_declaring_templates`, а не пересобирать множество.
- `DISABLED_ELT_EXCEPTIONS` дополнительно читается правилом кнопки отказа: любая новая запись с непустыми `callers` обязана называть переданный селектор в своём обосновании ДОСЛОВНО, иначе правило краснеет.
- Форма ответа «без основной цели свопа + внеполосное снятие» шипнута и наследуема: Фаза 10 получает её готовой на 16 мест, дёрнув один параметр макроса.
- `MACRO_DEFINITION_SITES_DECLARED` = 2; Фаза 10 обязана опустить до 0 либо обосновать заново.

Незакрытое, названное явно:

- Фактическое снятие узлов (`hx-swap-oob="delete"`) машинно не проверяемо: `httpx` внеполосных узлов не собирает. Пункт ручного UAT.
- Пятнадцать оставшихся мест подтверждения по-прежнему уходят полной перезагрузкой — это записанная граница фазы (FORM-06), а не недоделка.

## Self-Check: PASSED

- Созданный файл существует на диске: `app/templates/account_groups/partials/delete_response.html`.
- Шесть коммитов присутствуют в `git log`: `4f38276`, `e9faee4`, `566efe6`, `5496f4a`, `429c47d`, `046f545`.
- Все критерии приёмки трёх задач перегнаны поимённо и зелены, включая посимвольное сравнение рендера макроса с эталоном, исполнимые проверки поля `callers`, предусловия D-08 и формы несущего правила через `inspect.getsource`.
- Проверка плана: `tests/test_templates/ tests/test_pages/ -q` — **1502 passed, exit 0**; `uv run python -m compileall -q app main.py tests` — без ошибок.
- Число контролей выросло ровно как предписано: 17 → 18 (задача 2) → 19 (задача 3).

---
*Phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy*
*Completed: 2026-08-29*
