---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 01
subsystem: ui
tags: [htmx, jinja2, fastapi, css, gates, tdd]

# Dependency graph
requires:
  - phase: 08-sloy-otveta-i-geyty-razmetki
    provides: "слой ответа respond()/location_response(), фикстура htmx_client, девять машинных правил разметки и счётчик отставания NOT_YET_CONVERTED"
  - phase: 03-ekran-grupp-akkaunta
    provides: "экран /accounts/{id}/groups, макрос group_row, обработчик account_groups_toggle с тройным WHERE"
provides:
  - "components/form_wrapper.html — макрос-обёртка htmx-формы: ОДНО место, раздающее свойства качества сорока семи формам вехи"
  - "класс .form-busy и порог видимости 300 мс в app.css — единственный индикатор «запрос идёт» на веху"
  - "account_groups/partials/toggle_response.html и count_rule_oob.html — шипнутая форма ответа «фрагмент + внеполосный узел»"
  - "параметр with_modal у group_row — способ вернуть строку без второй панели подтверждения"
  - "помощник _group_counts() — один источник чисел линейки для страницы и обоих обработчиков"
  - "account_groups_toggle идёт через слой ответа во ВСЕХ ветках — первый переведённый обработчик вехи"
  - "MACRO_DEFINITION_SITES — идиома вывода мест определения макросов из-под правил адреса"
  - "_macro_callers — ЕДИНСТВЕННЫЙ на фазу сканер вызывающих; потребители — планы 09-02 и 09-03"
  - "_app_css / _css_with — группа контроля для правил, читающих файл стилей"
  - "DISABLED_ELT_EXCEPTIONS + DisabledEltException — перечень исключений цели блокировки по SP-1"
  - "два правила формы ответа: верхнеуровневый OOB-узел и подмена содержимого долгоживущей области"
affects: [09-02, 09-03, 09-04, "Фаза 10 (FORM-06)", "Фаза 11", "Фаза 12 (FETCH-01)", "Фаза 15 (QUAL-04)"]

# Actuals (#2632) — та же шкала estimateTokens (chars/4) по реализованному диффу.
actuals:
  tokens: 24860
  tasks: 3
  commits: 7

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "макрос-обёртка печатает тег формы САМ (готовая разметка параметром запрещена GATE-07)"
    - "адрес действия и адрес запроса — ОДНО выражение, выписанное дважды (G-4 сравнивает сырые строки)"
    - "плоское тело ответа: внеполосные узлы — прямые дети файла (allowNestedOobSwaps: false)"
    - "долгоживущая область = постоянный узел с id + подмена innerHTML:#id"
    - "перечень исключений с обоснованием на запись + отдельно утверждаемое ЧИСЛО (SP-1)"
    - "контроль зубов правила: изменённая копия дерева ИЛИ файла стилей (SP-2)"
    - "парный тест htmx_client: половина без htmx зовёт follow_redirects=False явно (SP-3)"

key-files:
  created:
    - app/templates/components/form_wrapper.html
    - app/templates/account_groups/partials/toggle_response.html
    - app/templates/account_groups/partials/count_rule_oob.html
  modified:
    - app/pages/account_groups.py
    - app/static/css/app.css
    - app/templates/account_groups/includes/group_row.html
    - app/templates/account_groups/list.html
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_templates/test_components.py
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Ключ любого параметрического перечня фазы — ФАЙЛ, который возвращает разборщик (Site.template); ключ вида file::name не заводится, потому что разборщик такой строки не производит"
  - "До вызывающего правило доходит ТОЛЬКО через объявленное поле callers, утверждаемое сканером _macro_callers; γ1 (умолчание параметра) оставлено там, где переопределения вызывающим не бывает"
  - "Половина «атрибут объявлен» снимается ТОЛЬКО записью с пустыми callers — иначе оба места отправки вывелись бы и правило зеленело бы на пустом множестве"
  - "Имя класса индикатора form-busy, а не имя рантайма: собственный стиль рантайма приезжает последним и съел бы порог, а седьмой ключ конфигурации запрещён числом Фазы 7"
  - "Задержка появления висит на состоянии «запрос идёт», а не на покое: в покое она задержала бы и обратный ход"
  - "Литерал len(paths) ПЕРЕСЧИТАН исполнением и остался равен 2, а не поднялся до 3, как проектировала разведка"
  - "Прозаические ссылки на проверяемые грепом литералы записаны СЛОВАМИ: комментарий, набравший литерал дословно, удовлетворил бы греп сам"

patterns-established:
  - "Инвентарное число правится ВМЕСТЕ с записью летописи, объясняющей, из чего оно складывается"
  - "Неподвижность числа тоже утверждается записью, а не молчанием (CLIENT_STATE_NODES = 24)"
  - "Помощник чтения источника принимает путь параметром — иначе группа контроля невыразима"

requirements-completed: []

coverage:
  - id: D1
    description: "Тумблер группы идёт через htmx: 200, тело без <!DOCTYPE, во фрагменте id=\"group-row-N\" и внеполосный узел innerHTML:#account-groups-count"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_returns_the_row_fragment"
        status: pass
    human_judgment: false
  - id: D2
    description: "Тумблер деградирует без htmx: прежний 302 на экран групп; форма остаётся <form> с литеральным method=\"post\" и action, посимвольно равным hx-post"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_degrades_without_htmx"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_is_a_real_post_form"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_such_form_keeps_its_method_and_action"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_post_attribute_matches_the_action_character_for_character"
        status: pass
    human_judgment: false
  - id: D3
    description: "Чужая и несуществующая группа отвечают неотличимо: одинаковые 204 + HX-Location, тело пустое; тройной WHERE не ослаблен фрагментным транспортом"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_foreign_toggle_goes_to_location"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_does_not_trust_the_account_id_from_the_url_over_htmx"
        status: pass
    human_judgment: false
  - id: D4
    description: "Свойства качества раздаёт ОДИН макрос: hx-disabled-elt и hx-indicator печатает он, селектор индикатора не передаёт ни один вызывающий, единственное отступление объявлено записью перечня с обоснованием, числом и сверкой вызывающих"
    requirement: FORM-09
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_htmx_post_declares_a_disabled_elt"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_disabled_elt_exception_is_actually_an_exception"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_number_of_disabled_elt_exceptions_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_post_without_a_disabled_elt_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D5
    description: "Индикатор «запрос идёт» существует одним классом .form-busy с порогом 300 мс через transition-delay, и имя класса НЕ имя рантайма"
    requirement: QUAL-02
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_indicator_class_is_not_the_runtime_one"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_indicator_class_carries_a_visibility_threshold"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_the_runtime_indicator_class_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_threshold_on_the_resting_rule_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D6
    description: "Чекбокс тумблера несёт стабильный id=\"group-toggle-N\" и в первичной отрисовке, и в разметке фрагмента ответа — механизм восстановления фокуса обеспечен разметкой"
    requirement: QUAL-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_fragment_keeps_the_toggle_id"
        status: pass
    human_judgment: false
  - id: D7
    description: "Двойное нажатие не создаёт второй записи: обработчик ИНВЕРТИРУЕТ is_active; единица записи — один commit одной строки под тройным WHERE; hx-disabled-elt серверной защитой не объявляется"
    requirement: QUAL-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_touches_exactly_one_group"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_does_not_edit_the_schedules"
        status: pass
    human_judgment: false
  - id: D8
    description: "Форма ответа: внеполосный узел — узел верхнего уровня своего файла; долгоживущая область подменяется содержимым, а не узлом. Зубы обоих правил доказаны контролями"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_oob_node_is_a_top_level_node_of_its_response"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_long_lived_region_is_replaced_by_content"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_nested_oob_node_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_long_lived_region_replaced_by_node_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D9
    description: "Инвентарные числа сдвинуты и утверждены собственными обходами: HX_POST_PLACES 1→2, HX_TARGETS 0→1, OOB_BLOCKS 6→7, NOT_YET_CONVERTED_COUNT 36→35; четыре числа подтверждены неподвижными; литерал len(paths) пересчитан исполнением"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_positive_the_untouched_tree_keeps_every_gate_green"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_backlog_matches_the_declared_count"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_both_branches_of_the_editor_action_are_extracted"
        status: pass
    human_judgment: false
  - id: D10
    description: "Своп действительно произошёл и ИМЕННО в #group-row-N; OOB-счётчик приземлился в #account-groups-count; позиция прокрутки списка не потеряна"
    requirement: FORM-02
    verification: []
    human_judgment: true
    rationale: "httpx не свопает и не собирает внеполосные узлы: тест видит ТЕКСТ ответа, а факт подмены и сохранение прокрутки — свойства браузера. Пункт 3 ручного UAT (план 09-04)"
  - id: D11
    description: "После переключения тумблера КЛАВИАТУРОЙ (Space) фокус остался на том же тумблере"
    requirement: QUAL-06
    verification: []
    human_judgment: true
    rationale: "⚠️ ОЖИДАЕМЫЙ ОТВЕТ СЕГОДНЯ — «НЕТ», и это записано заранее, а не будет обнаружено на UAT: hx-disabled-elt (D-06) снимает блокировку ПОСЛЕ свапа, отключённый чекбокс теряет фокус ДО него, и активным элементом на момент свапа успевает стать <body> (09-RESEARCH §4.3). Проверить, а не предположить — пункт 3 ручного UAT. Три способа снять конфликт записаны в обосновании DISABLED_ELT_EXCEPTIONS"
  - id: D12
    description: "Индикатор виден на медленной сети и не мигает на быстрой; hx-disabled-elt реально мешает второму нажатию"
    requirement: QUAL-02
    verification: []
    human_judgment: true
    rationale: "Порог 300 мс на глаз и поведение при быстром двойном нажатии — свойства реального браузера и реальной сети; машинно проверено лишь ОБЪЯВЛЕНИЕ порога в стилях. Пункт 6 ручного UAT"

# Metrics
duration: 2h 3m
completed: 2026-08-29
status: complete
---

# Phase 9 Plan 01: Пилот на `account_groups` — сквозной контракт формы Summary

**Тумблер группы переведён на htmx целиком — от нового макроса-обёртки `form_wrapper` через строку и слой ответа до фрагмента `#group-row-N` с внеполосным счётчиком, — и четыре инвентарных числа гейтов Фазы 8 сдвинуты ровно на этот путь.**

## Performance

- **Duration:** 2h 3m
- **Started:** 2026-08-29T15:25:00Z (приблизительно — с прогона предусловия)
- **Completed:** 2026-08-29T17:28:34Z
- **Tasks:** 3 из 3
- **Files modified:** 12 (3 создано, 9 изменено)

## Accomplishments

- **Трассирующий срез доказан целиком.** Один и тот же маршрут `/accounts/{a}/groups/{g}/toggle` отвечает фрагментом строки запросу htmx и прежним 302 запросу без него; обе половины закреплены парами тестов, а несущая половина второй — `assert "<!DOCTYPE" not in response.text`.
- **Свойства качества стали свойством ОДНОГО файла.** `components/form_wrapper.html` печатает тег формы сам и раздаёт `hx-disabled-elt` и `hx-indicator`; ни один из сорока семи будущих вызывающих селектора индикатора не передаёт.
- **Три правила гейта заведены вместе со своими зубами.** Верхнеуровневый внеполосный узел, подмена содержимого долгоживущей области и объявленная цель блокировки — каждое с контролем, который на подставленном дереве (или на подставленной копии стилей) краснеет.
- **Счётчик прогресса вехи впервые убыл:** `NOT_YET_CONVERTED_COUNT` 36 → 35, и у правила G-2 впервые появился предмет — до этой фазы множество переведённых обработчиков было пусто.

## Task Commits

1. **Задача 1 (tracer, tdd) — RED: числа и пары двигаются первыми** — `9d181af` (test)
2. **Задача 1 — GREEN: макрос, разметка, обработчик, исключение гейта** — `13320ba` (feat)
3. **Задача 2 (tdd) — RED: контроли формы ответа** — `0b52b36` (test)
4. **Задача 2 — GREEN: два правила формы ответа** — `802a757` (feat)
5. **Задача 3 (tdd) — RED: контроли свойств качества** — `2c4cab3` (test)
6. **Задача 3 — GREEN: индикатор и перечень исключений** — `cc0e484` (feat)
7. **Отклонение — инвентарь библиотеки компонентов 15 → 16** — `969fee5` (fix)

_Порядок RED → GREEN соблюдён в каждой из трёх задач: гейтовая последовательность `test(09-01) → feat(09-01)` присутствует трижды._

## Files Created/Modified

- `app/templates/components/form_wrapper.html` — **NEW.** Макрос `form_wrapper(action, target, swap, trigger, disabled_elt)`, печатающий тег формы; `method="post"` литералом, `action` и `hx-post` — одно выражение, оба селектора с префиксом `find `, узел индикатора внутри формы.
- `app/templates/account_groups/partials/toggle_response.html` — **NEW.** Плоское тело ответа: строка через `group_row(..., with_modal=false)` плюс включение узла счётчика.
- `app/templates/account_groups/partials/count_rule_oob.html` — **NEW.** Один узел верхнего уровня с `hx-swap-oob="innerHTML:#account-groups-count"`; один источник на оба ответа экрана.
- `app/static/css/app.css` — раздел «Индикатор htmx-формы»: `.form-busy` и `.form-busy.htmx-request`, порог 300 мс задержкой перехода на состоянии запроса.
- `app/templates/account_groups/includes/group_row.html` — форма тумблера стала блочным вызовом обёртки; параметр `with_modal`; `x-data` переехал на `<span>` с `x-init`; условие снятия кнопки «Применить» — живой htmx.
- `app/templates/account_groups/list.html` — постоянная обёртка `#account-groups-count` вокруг линейки, `{% if total_groups %}` внутри неё.
- `app/pages/account_groups.py` — помощник `_group_counts()`; `account_groups_toggle` переписан на `respond()` во всех ветках, с нульарным асинхронным `_fragment()`.
- `tests/test_pages/test_account_groups.py` — шесть новых пар SP-3; предмет первой половины `test_toggle_is_a_real_post_form` сменил механизм.
- `tests/test_templates/test_htmx_markup_gates.py` — четыре инвентарных числа, `MACRO_DEFINITION_SITES`, `LONG_LIVED_REGION_IDS`, `INDICATOR_CLASS`, `DISABLED_ELT_EXCEPTIONS`, `_macro_callers`, `_app_css`/`_css_with`, девять новых правил и пять новых контролей.
- `tests/test_pages/test_htmx_gates.py` — счётчик отставания 36 → 35 с записью летописи.
- `tests/test_templates/test_components.py` — новый макрос зарегистрирован в `COMPONENT_CALLS`.
- `tests/test_pages/test_responsive_markup.py` — инвентарь библиотеки компонентов 15 → 16 (см. Отклонения).

## Decisions Made

- **Форма ключа параметрической записи** (решение фазы, принятое этим планом и читаемое отсюда планами 09-02 и 09-03): ключ перечня — файл, который возвращает разборщик; до вызывающего правило доходит только через поле `callers`, утверждаемое `_macro_callers`. Гибрид взят вместо чистого γ1 потому, что γ1 зеленел бы и на будущем вызывающем, накрывшем кнопку Отмены, которую QUAL-01 запрещает блокировать.
- **Восьмое движущееся число измерено, а не подставлено.** Литерал `len(paths)` в `test_both_branches_of_the_editor_action_are_extracted` **остался равен 2**, хотя разведка проектировала 3. Причина названа в докстринге: множество складывается из двух ветвей условного адреса ОДНОЙ формы — редактора объявлений (`/ads/new` и `/ads/{}/edit`); второе место отправки — определение макроса-обёртки, и в `_action_sites` оно не входит, потому что адрес там приходит параметром. Разведка допускала, что `hx-post` тумблера останется в шаблоне строки; под макросом-обёрткой место переехало в каталог компонентов, и допущение не сбылось.
- **`NOT_YET_CONVERTED_COUNT` 36 → 35 — это ДВИЖЕНИЕ СЧЁТЧИКА ПРОГРЕССА ВЕХИ, а не правка теста под реализацию.** Текст отказа `test_the_backlog_matches_the_declared_count` написан заранее и прямо требует опустить число и снять переведённый обработчик из перечня, когда Фаза 9 переведёт первый. Число разделено на два утверждения именно затем, чтобы прогресс не читался как регрессия.
- **Прозаические ссылки на литералы, проверяемые грепом, записаны словами.** Четыре критерия приёмки плана — блёклые грепы (`x-on:change`, ключ перечня отставания, класс ответа-перенаправления, имена запрещённых конструкций экранирования). Комментарий, набравший такой литерал дословно, удовлетворил бы греп сам, и проверка зеленела бы на документации о соблюдении вместо самого соблюдения. Во всех четырёх местах имя названо словами, и причина этого записана рядом.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Шапка макроса-обёртки набирала путь компонента панели и ломала инвентарь потребителей**

- **Found during:** Задача 1 (GREEN)
- **Issue:** Докстринг `form_wrapper.html` ссылался на компонент модального окна его ПУТЁМ (`components/modal.html:81-83`, `:113-114`). Инвентарь мест панели (`test_components.py`) считает потребителей по вхождению пути компонента в исходник шаблона, и три утверждения — `test_modal_site_inventory`, `test_modal_guard_is_inherited_by_every_consumer`, `test_every_modal_site_has_cancel_and_escape` — покраснели на 12 импортёрах вместо 11.
- **Fix:** Ссылки переписаны словами («компонент модального окна»), и причина этого записана в самой шапке абзацем. Правка `components/modal.html` при этом не потребовалась — запрет плана «не править ни на символ» соблюдён.
- **Files modified:** `app/templates/components/form_wrapper.html`
- **Verification:** `uv run pytest tests/test_templates/test_components.py -q` — 33 зелёных.
- **Committed in:** `13320ba` (коммит задачи 1)

**2. [Rule 1 - Bug] Тест `test_toggle_fragment_keeps_the_toggle_id` был зелен по построению в фазе RED**

- **Found during:** Задача 1 (RED)
- **Issue:** Написанный по плану, тест утверждал наличие `id="group-toggle-N"` в теле ответа — и проходил ДО реализации: фикстура `htmx_client` следует редиректу незаметно, и целая страница экрана групп несёт тот же идентификатор. Тест доказывал бы наличие разметки на странице, о которой и без него всё известно, а про ответ тумблера не утверждал бы ничего. По правилу fail-fast TDD зелёный тест в фазе RED расследуется, а не принимается.
- **Fix:** Добавлена несущая половина `assert "<!DOCTYPE" not in response.text` (форма SP-3), после чего тест стал красным до реализации и красным по правильной причине.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Verification:** прогон `-k toggle_fragment_keeps_the_toggle_id` до реализации — красный; после — зелёный.
- **Committed in:** `9d181af` (коммит RED задачи 1)

**3. [Rule 3 - Blocking] Девятое движущееся число фазы: инвентарь библиотеки компонентов**

- **Found during:** проверка слияния волны, после задачи 3
- **Issue:** `tests/test_pages/test_responsive_markup.py` пинует размер каталога `app/templates/components/` ДВАЖДЫ (`test_billing_component_library_did_not_grow` и `test_template_inventory`), числом 15. `form_wrapper.html` сделал его 16, и оба утверждения покраснели. Числа нет ни в таблице контекста, ни в перечне движущихся чисел плана, а файл не входит ни в один из проверочных наборов трёх задач — отказ проявлялся только в прогоне `tests/test_pages/` целиком.
- **Fix:** Оба числа подняты до 16 с записью летописи у каждого, ровно тем приёмом, который предписан комментариями самих этих мест: константы поднимаются коммитом, добавляющим файл, а не задним числом.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** `uv run pytest tests/test_pages/test_responsive_markup.py -q` — 139 зелёных; полный прогон волны — 1489 зелёных.
- **Committed in:** `969fee5`

---

**Total deviations:** 3 auto-fixed (2 блокирующих, 1 ошибка теста).
**Impact on plan:** Ни одно отклонение не расширило предмет плана. Два блокирующих — следствия того, что новый файл попадает в чужие инвентари, и оба закрыты движением числа/переписыванием прозы, а не ослаблением проверок. Третье усилило тест, который иначе вошёл бы в проект зелёным по построению. Запреты плана соблюдены: `components/modal.html` не изменён, `hx-push-url` не появился, плашка `?notice=` на успешный тумблер не выдаётся, новых зависимостей и файлов JS не заведено, седьмой ключ конфигурации не добавлен, правило G-11 не снято.

## Issues Encountered

- **Полный прогон `tests/test_templates/ tests/test_pages/` занимает ~20 минут** и дважды упирался в потолок времени одного вызова инструмента. Обойдено запуском в фоне с записью в файл; на результат не влияет.
- **Известный красный `full-suite-ads-editor-order-pollution`** (`.planning/todos/pending/`) в прогонах этого плана НЕ проявился: он про `test_image_base_url_comes_from_app_settings` и виден только в прогоне всей суиты `tests/`. Отклонение №3 с ним не связано — сверено по имени теста, как того требует раздел `<verification>` плана.

## Known Stubs

Заглушек нет. Ни один новый файл не отдаёт пустых или подставных данных: узел счётчика печатает реальные числа из `_group_counts()`, фрагмент строки собирается тем же макросом, что и первичная отрисовка.

## Threat Flags

Новой поверхности вне `<threat_model>` плана не появилось. Единственный новый путь — фрагментный ответ уже существовавшего маршрута `POST /accounts/{account_id}/groups/{group_id}/toggle`; вердикт доступа (тройной `WHERE`) вычисляется ДО развилки транспорта и сохранён дословно, новых мест записи заголовков `HX-*` не заведено (`HX_HEADER_WRITES` остаётся 2 и утверждается тестом).

## Requirements

`requirements-completed` оставлен **пустым намеренно**, и `REQUIREMENTS.md` этим планом не правился. Все пять объявленных идентификаторов заявлены также соседними планами фазы, у которых сводки ещё нет:

| ID | Кто ещё заявляет | Готов к отметке |
|----|------------------|-----------------|
| FORM-02 | 09-02, 09-03 | нет |
| FORM-09 | 09-03 | нет |
| QUAL-01 | 09-02, 09-03 | нет |
| QUAL-02 | 09-02, 09-04 | нет |
| QUAL-06 | 09-04 | нет |

Отметить их сейчас означало бы объявить требование выполненным, пока соседние планы, его заявившие, ещё не исполнены, — то самое, ради чего заведён гейт общих идентификаторов. Отметку делает последний завершивший план фазы.

## Notes for the Orchestrator

- `STATE.md` и `ROADMAP.md` этим агентом не изменялись (режим worktree).
- **Гейт трассирующего среза.** План несёт `type="tracer"` в задаче 1. Auto-режим в `config.json` выключен (`auto_advance: false`, `_auto_chain_active: false`), но `mode: yolo`, `human_verify_mode: end-of-phase`, `autonomous: true` во фронтматере плана и прямое указание оркестратора «выполнить все задачи» читаются как автономный прогон. Поэтому гейт исполнен в автономной форме: `<verify>` трассирующей задачи перегнан целиком (202 зелёных) ПЕРЕД началом задач расширения, и расширение началось только после этого. Человеку срез не показывался — по `human_verify_mode: end-of-phase` он попадёт в общий разбор конца фазы.

## Next Phase Readiness

Готово к плану 09-02:

- `components/form_wrapper.html` шипнут — `modal(..., hx_post=false)` план 09-02 добавляет поверх него.
- `_macro_callers` заведён и утверждён на живом вызывающем; `PARAMETRIC_SWAP_TARGETS.callers` плана 09-02 и правило D-08 плана 09-03 опираются на него, а не заводят второй резолвер.
- `count_rule_oob.html` — один источник узла счётчика; ответ удаления включает ТОТ ЖЕ файл, поэтому `OOB_BLOCKS` за фазу поднимется суммарно на 3, а не на 4.
- `MACRO_DEFINITION_SITES_DECLARED` = 1; план 09-02 поднимает до 2, Фаза 10 обязана опустить до 0 или обосновать заново.
- `DISABLED_ELT_EXCEPTIONS_DECLARED` = 2; запись `ads/form.html` назначена Фазе 12 (FETCH-01).

Незакрытое, названное явно:

- **QUAL-06 на пути тумблера сегодня НЕ выполняется** — `hx-disabled-elt` (D-06) отменяет возврат фокуса. Ожидание записано в перечне исключений и в UAT; решение о трёх способах снятия конфликта не принято и ждёт ручной проверки.
- Лишний блочный уровень вокруг `.count-rule` (flex с `margin: 0 0 12px`) проверяется UI-ревью фазы.

## Self-Check: PASSED

- Три созданных файла существуют на диске: `components/form_wrapper.html`, `account_groups/partials/toggle_response.html`, `account_groups/partials/count_rule_oob.html`.
- Семь коммитов присутствуют в `git log`: `9d181af`, `13320ba`, `0b52b36`, `802a757`, `2c4cab3`, `cc0e484`, `969fee5`.
- Все критерии приёмки трёх задач перегнаны поимённо и зелены, включая временную проверку зубов правила верхнего уровня на живом дереве (обёртка вставлена → красный → откачена).
- Проверка плана: `tests/test_templates/ tests/test_pages/ -q` — **1489 passed, exit 0**; `uv run python -m compileall -q app main.py tests` — без ошибок.
- Числа контролей выросли ровно как предписано: 12 → 14 (задача 2) → 17 (задача 3).

---
*Phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy*
*Completed: 2026-08-29*
