---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 05
subsystem: ui
tags: [htmx, jinja2, fastapi, infinite-scroll, out-of-band-swap, oob, pagination]

requires:
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: "план 09-02 — фрагментный ответ удаления с тремя внеполосными узлами и макрос modal(hx_post)"
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: "план 09-01 — слой ответа respond() и узел линейки счётчика"
provides:
  - "Единственный источник разметки сентинела бесконечной прокрутки — макрос sentinel(account_id, next_offset, filter_params, oob=false)"
  - "Стабильный идентификатор сентинела group-list-sentinel во всех трёх местах отрисовки"
  - "Четвёртый внеполосный узел ответа удаления — починка курсора прокрутки"
  - "Опциональный параметр modal(hx_include=...) — дополнительные данные запроса панели подтверждения"
  - "Поля запроса удаления rendered_rows и search (второй потребитель search — план 09-06)"
  - "Помощник тестов _scroll_read_on_url — модель живого документа для всех тестов курсора"
affects: [09-06, 09-07, 09-08, 09-09, "Фаза 10 FORM-06 (перевод шестнадцати мест подтверждения)", "Фазы 11-15 (пары «список + порция»)"]

actuals:
  tokens: 15634
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Единый источник разметки вместо двух согласованных копий: разъезд копий утверждается счётом файлов, а не сравнением строк"
    - "Внеполосная ветка макроса печатается ВТОРЫМ ПОЛНЫМ тегом, а не условием внутри открывающего тега"
    - "Курсор прокрутки чинится величиной, верной в ОБОИХ случаях: rendered_rows минус число снятых с экрана строк"

key-files:
  created:
    - app/templates/account_groups/includes/sentinel.html
  modified:
    - app/pages/account_groups.py
    - app/templates/account_groups/list.html
    - app/templates/account_groups/partial_cards.html
    - app/templates/account_groups/includes/group_row.html
    - app/templates/account_groups/partials/delete_response.html
    - app/templates/components/modal.html
    - tests/test_pages/test_account_groups.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_templates/test_htmx_inventory.py

key-decisions:
  - "Смещение починенного сентинела выводится из rendered_rows МИНУС число строк, которые этот же ответ снимает с экрана (1 при найденной строке, 0 при ненайденной), а не вычитанием константы: вычитание единицы всегда задваивало бы строку на холостом пути"
  - "Четвёртый внеполосный узел собирается по НАЛИЧИЮ rendered_rows, а не по факту удаления: условная сборка сделала бы само присутствие узла признаком состоявшегося удаления"
  - "Разметка сентинела переведена в единый источник, а прежний тест попарного сравнения двух копий заменён утверждением о ЕДИНСТВЕННОСТИ источника"
  - "hx_include навешен на форму панели подтверждения, а не на предка списка: наследование признака молча прицепило бы поле ко всем htmx-запросам внутри списка"
  - "keyset-пагинация (after_id) не заводится — решение владельца исполнено, а не пересмотрено"

patterns-established:
  - "Помощник-модель живого документа в тестах: адрес дочитывания берётся из четвёртого внеполосного узла, если ответ его несёт, и со страницы, если не несёт — иначе предписанный красный недостижим"
  - "Невакуумность утверждения о равенстве тел доказывается ПОДСТАНОВКОЙ в дерево и наблюдением красного, а не рассуждением"
  - "Неподвижность инвентарного числа при СМЕНИВШЕМСЯ составе записывается летописью явно (12 → 12), чтобы не читаться как неподвижность состава"

requirements-completed: [FORM-02, QUAL-01]

coverage:
  - id: D1
    description: "Удаление строки с первой страницы через htmx больше не теряет ни одной группы: объединение отрисованного и дочитанного покрывает весь оставшийся список"
    requirement: "FORM-02"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_scroll_cursor_survives_a_fragment_delete"
        status: pass
    human_judgment: false
  - id: D2
    description: "Холостое удаление (чужая, уже удалённая группа) не двигает курсор ни на единицу и не задваивает ни одной строки; ответ несёт четыре внеполосных узла, а не три"
    requirement: "QUAL-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_a_no_op_delete_does_not_double_a_row"
        status: pass
    human_judgment: false
  - id: D3
    description: "Сентинел существует в дереве ОДНИМ источником и несёт стабильный идентификатор в странице, порции прокрутки и ответе удаления"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_sentinel_carries_a_stable_id_in_both_templates"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_sentinel_markup_has_exactly_one_source"
        status: pass
    human_judgment: false
  - id: D4
    description: "Путь деградации не тронут: без признака htmx удаление отвечает прежним перенаправлением, четвёртый узел не собирается, поля rendered_rows в запросе нет вовсе"
    requirement: "FORM-02"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_delete_degrades_without_the_rendered_rows_field"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_delete_response_repairs_the_sentinel_only_over_htmx"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ответ удаления неотличим ВНУТРИ класса «строка не найдена»: чужая и несуществующая группа дают один статус, один заголовок перехода и одинаковое тело после подстановки идентификатора пути"
    requirement: "QUAL-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_delete_response_is_indistinguishable_for_a_foreign_and_a_missing_group"
        status: pass
    human_judgment: false
  - id: D6
    description: "Вырожденное число отрисованных строк (ноль и отрицательное) не строит курсор вовсе и не даёт отрицательного смещения в адресе подгрузки"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_a_non_positive_rendered_rows_does_not_build_a_sentinel"
        status: pass
    human_judgment: false
  - id: D7
    description: "Починенный сентинел дочитывает ОТФИЛЬТРОВАННУЮ выдачу: строка поиска доезжает до адреса четвёртого узла"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_repaired_sentinel_keeps_the_search_filter"
        status: pass
    human_judgment: false
  - id: D8
    description: "Каждое сдвинутое инвентарное число несёт запись летописи и работающий контроль; числа, двигаться не имевшие права, утверждены записями"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py + tests/test_templates/test_htmx_inventory.py (104 passed вместе с test_htmx_gates.py)"
        status: pass
    human_judgment: false
  - id: D9
    description: "Умолчание макроса modal() не сдвинулось: пятнадцать остальных мест подтверждения рендерятся байт-в-байт как до правки"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py (48 passed)"
        status: pass
    human_judgment: false
  - id: D10
    description: "Живая проверка в браузере: после удаления строки с прокрученного экрана следующая порция подтягивается без потери и без задвоения строк, индикатор и панель ведут себя как прежде"
    verification: []
    human_judgment: true
    rationale: "Поведение htmx-подмены в живом документе (hx-include с сентинела, внеполосная подмена узла, момент срабатывания revealed) машинно здесь не исполняется: тесты моделируют документ помощником _scroll_read_on_url. Ручной обход — предмет плана 09-09."

duration: 41 min
completed: 2026-08-30
status: complete
---

# Phase 09 Plan 05: Починка курсора прокрутки после фрагментного удаления — Summary

**Сентинел бесконечной прокрутки стал адресуемым узлом из единственного источника, живой документ шлёт своё число отрисованных строк вместе с запросом удаления, и ответ чинит курсор четвёртым внеполосным узлом со смещением `rendered_rows` минус число снятых с экрана строк — потеря группы (CR-01) и её зеркальное задвоение закрыты одной арифметикой.**

## Performance

- **Duration:** 41 min
- **Started:** 2026-08-30T07:26:00Z
- **Completed:** 2026-08-30T08:07:00Z
- **Tasks:** 3
- **Files modified:** 10 (1 создан, 9 изменены)

## Accomplishments

- **GAP-1 (CR-01) закрыт.** Удаление строки с первой страницы больше не делает одну группу неотрисовываемой ни одной из двух порций. Регрессия закреплена тестом, который на дереве ДО правки красный и называет потерянную группу поимённо.
- **Зеркальный отказ закрыт той же арифметикой, а не второй заплаткой.** Холостое удаление (чужой, несуществующий, уже удалённый идентификатор) не двигает курсор ни на единицу: вычитается число строк, которые ЭТОТ ЖЕ ответ снимает с экрана, а оно — функция единственного вопроса «вернул ли тройной `WHERE` строку».
- **Разметка сентинела стала одним источником.** Две копии (`list.html`, `partial_cards.html`) переехали в `account_groups/includes/sentinel.html`; прежний тест попарного сравнения заменён утверждением о ЕДИНСТВЕННОСТИ источника — сильнее прежнего, потому что попарное сравнение при трёх копиях осталось бы зелёным.
- **Неотличимость D-04 (в редакции D-04-A) закреплена машинно и НЕВАКУУМНО.** Тест сравнения тел первым исполняемым утверждением закрепляет достижение фрагментной ветки; невакуумность доказана красным на подставленном дереве (WARN-4 снят).
- **Ни одно инвентарное число не сдвинулось молча.** `OOB_BLOCKS` 9 → 10 с летописью; состав `REVEALED_SITES` пересобран; `REVEALED_PLACES` / `REVEALED_LITERAL_OCCURRENCES` / `HX_GET_PLACES` пересчитаны ОБХОДОМ (12 / 12 / 22 — состав сменился, число нет, и это записано); `CONDITIONAL_PLACES`, `HX_POST_PLACES`, `HX_TARGETS`, `LONG_LIVED_REGION_IDS`, `MACRO_DEFINITION_SITES_DECLARED` не сдвинулись, и это утверждено записями.

## Task Commits

1. **Задача 1 (RED): падающий тест курсора прокрутки** — `84f21e9` (test)
2. **Задача 1 (GREEN): починка курсора четвёртым внеполосным узлом** — `fc03990` (feat)
3. **Задача 2: инвентарные числа сдвинуты явно** — `969ec94` (test)
4. **Задача 3: деградация и неотличимость закреплены тестами** — `73d1014` (test)

_Задача 1 — трассирующий срез, исполнена по циклу RED → GREEN; фазы REFACTOR не потребовалось (правка минимальна и чиста)._

## Files Created/Modified

- `app/templates/account_groups/includes/sentinel.html` — **создан**: единственный источник разметки сентинела; макрос `sentinel(account_id, next_offset, filter_params, oob=false)`, две взаимоисключающие полные ветки, скрытое поле `rendered_rows` со значением `next_offset`, адрес собирается в переменную один раз выше обеих ветвей.
- `app/pages/account_groups.py` — `Form` в импорте; `account_groups_delete` принимает `rendered_rows: int | None = Form(None)` и `search: str | None = Form(None)`; величина `rows_this_response_takes_off_screen` рядом с проверкой `if group:`; смещение `repaired_offset`; `_fragment()` передаёт в шаблон `account_id`, `sentinel_offset`, `filter_params`; два новых абзаца докстринга (почему число приходит от клиента; почему вычитается число снятых строк и почему неотличимость цела).
- `app/templates/account_groups/list.html` — импорт макроса, вызов вместо собственной разметки, третий инвариант прокрутки переписан на «ОДИН МАКРОС», `filter_search` пробрасывается в строку.
- `app/templates/account_groups/partial_cards.html` — то же; `filter_search` берётся из `filter_params`.
- `app/templates/account_groups/includes/group_row.html` — параметр `filter_search=''`; вызов панели стал БЛОЧНЫМ со скрытым полем `search`; `hx_include='#group-list-sentinel'`. Форма-триггер удаления не тронута вовсе (D-03).
- `app/templates/components/modal.html` — `hx_include=None` последним в сигнатуре, печать признака внутри той же ветки `{%- if hx_post %}`; абзац докстринга о единственном потребителе и о запрете наследования признака с предка.
- `app/templates/account_groups/partials/delete_response.html` — четвёртый узел вызовом макроса с `oob=true`, условие «число пришло» СНАРУЖИ тега; три абзаца докстринга.
- `tests/test_pages/test_account_groups.py` — 8 новых тестов, 1 заменён более сильным, 2 помощника (`_scroll_read_on_url`, `_sentinel_ids`), `_search_param`.
- `tests/test_templates/test_htmx_markup_gates.py` — `OOB_BLOCKS` 9 → 10 с летописью; абзац у `LONG_LIVED_REGION_IDS`; запись в докстринге G-11; поимённое чтение новой цели в положительном контроле.
- `tests/test_templates/test_htmx_inventory.py` — состав `REVEALED_SITES`, летописи у `REVEALED_PLACES`, `REVEALED_LITERAL_OCCURRENCES`, `HX_GET_PLACES`, `CONDITIONAL_PLACES`.

## Decisions Made

Все решения плана исполнены без пересмотра. Детали — в `key-decisions` фронтматтера.

## Выписки, требуемые критериями приёмки

### 1. Красный до правки — регрессия курсора (задача 1, критерий 1)

Прогон `test_the_scroll_cursor_survives_a_fragment_delete` на дереве ДО правки:

```
E   AssertionError: после удаления строки список потерял группы: [31] — их не отрисовала
    ни первая страница, ни порция, которую дочитает сентинел; человек не увидит их до
    перезагрузки, а линейка счётчика продолжит их считать
E   assert not [31]
```

Отказ называет ПОТЕРЯННЫЙ идентификатор поимённо, а не сообщает «в ответе нет сентинела»: помощник адреса дочитывания на дереве до правки вернул адрес СО СТРАНИЦЫ, как и предписано.

### 2. Красный на подстановке «уменьшать всегда» (задача 1, критерий 2)

Временная замена `rendered_rows - rows_this_response_takes_off_screen` на `rendered_rows - 1`, прогон `test_a_no_op_delete_does_not_double_a_row`:

```
E   AssertionError: строка показана дважды после удаления, которое ничего не удалило: [30]
    — курсор уехал назад там, где с экрана не снялось ни одной строки
E   assert not [30]
```

Дерево возвращено; `git status --short` после возврата показывал только ожидаемые файлы плана.

### 3. Строка сборки смещения (задача 1, критерий 3)

`app/pages/account_groups.py:541-545` — вычитаемое есть ИМЯ ВЕЛИЧИНЫ, а не число:

```python
    repaired_offset = (
        rendered_rows - rows_this_response_takes_off_screen
        if rendered_rows is not None and rendered_rows > 0
        else None
    )
```

Сама величина вычислена один раз рядом с проверкой `if group:`:

```python
    rows_this_response_takes_off_screen = 1 if group else 0
```

### 4. Где встречается `group-list-sentinel` (задача 1, критерий 7)

`grep -rn "group-list-sentinel" app/templates/` → 4 строки в **трёх** файлах, каждый назван:

- `app/templates/account_groups/includes/sentinel.html` — 2 строки (обе ветки макроса, разметка);
- `app/templates/account_groups/includes/group_row.html` — 1 строка (`hx_include='#group-list-sentinel'`);
- `app/templates/account_groups/partials/delete_response.html` — 1 строка (перечисление узлов в докстринге, не разметка).

`grep -c "hx-trigger=\"revealed\"" app/templates/account_groups/list.html app/templates/account_groups/partial_cards.html` → **0** в обоих.

### 5. Первое исполняемое утверждение теста неотличимости (задача 3, критерий 3)

```python
    # ПЕРВОЕ ИСПОЛНЯЕМОЕ УТВЕРЖДЕНИЕ — О ДОСТИГНУТОЙ ФРАГМЕНТНОЙ ВЕТКЕ.
    assert foreign.status_code == 200, (
        f"фрагментная ветка не достигнута: ответ {foreign.status_code} вместо "
        f"200 — без неё равенство тел ниже вакуумно, потому что сравнивало бы "
        f"два пустых тела ветки перехода"
    )
    assert f'id="group-row-{foreign_group.id}"' in foreign.text, (
```

### 6. Красный на подстановке «ветка перехода безусловно» (задача 3, критерий 4)

Временная замена `if total_groups == 0:` на `if True:`:

```
E   AssertionError: фрагментная ветка не достигнута: ответ 204 вместо 200 — без неё
    равенство тел ниже вакуумно, потому что сравнивало бы два пустых тела ветки перехода
E   assert 204 == 200
```

Отказ называет НЕДОСТИГНУТУЮ фрагментную ветку, а не неравенство тел. Дерево возвращено; `git status --short` после возврата показывал только `tests/test_pages/test_account_groups.py`.

### 7. Посев теста неотличимости и значение `rendered_rows` (задача 3, критерий 5)

```python
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )
    rendered_rows = PAGE_SIZE
```

У действующего человека 35 СВОИХ групп; чужая группа заведена ДРУГОМУ пользователю в ЕГО аккаунте. Ни один из двух запросов ничего не удаляет, поэтому `total_groups = 35 > 0` до и после обоих — фрагментная ветка достижима на обоих.

### 8. Утверждение о непустоте в тесте фильтра (задача 3, критерий 8)

Стоит ДО утверждения о совпадении фильтра:

```python
    page_sentinels = _sentinels(page)
    assert page_sentinels, (
        "сентинела нет на отфильтрованной странице — поиск отсёк выдачу до "
        "размера страницы, и утверждение о фильтре сравнивать не с чем"
    )
```

### 9. Обе величины вырожденного числа (задача 3, критерий 2)

```python
    for value, victim in ((0, seeded[0]), (-5, seeded[1])):
        ...
        assert response.text.count("hx-swap-oob") == 3, (
            f"при rendered_rows={value} ответ несёт "
            f"{response.text.count('hx-swap-oob')} внеполосных узла вместо "
            f"трёх — курсор построен по вырожденному числу"
        )
        assert not _sentinels(response.text), (
            f"при rendered_rows={value} ответ подменил сентинел"
        )
```

## Verification Results

| # | Проверка | Результат |
|---|---|---|
| 1 | `uv run pytest tests/test_pages/test_account_groups.py -q -p no:randomly` | **110 passed** (было 102 до плана; +8 новых, 1 заменён) |
| 2 | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_inventory.py tests/test_pages/test_htmx_gates.py -q` | **104 passed** |
| 3 | `uv run pytest tests/test_templates/test_components.py -q` | **48 passed** |
| 4 | `uv run python -m compileall -q app main.py tests` | без ошибок |
| 5 | `grep -rnE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER" app/templates/account_groups app/templates/components/modal.html app/pages/account_groups.py` | пусто |
| 6 | Текст отказа регрессии до правки | выписан выше, называет потерянные идентификаторы |
| 7 | Текст отказа на «уменьшать всегда» | выписан выше, дерево возвращено |
| 8 | Текст отказа на «ветка перехода безусловно» | выписан выше, называет недостигнутую ветку |
| — | `uv run pytest tests/test_templates -q` (сверх плана) | **148 passed** |
| — | `uv run pytest tests/test_pages/test_responsive_markup.py -q` (сверх плана, риск от нового файла шаблона) | **139 passed** |

Контрольные числа задачи 2: `grep -c "^def test_control" tests/test_templates/test_htmx_markup_gates.py` → **21** (не упало);
`grep -c "план 09-05"` → **4** в каждом из двух файлов инвентаря;
`grep -n "^CONDITIONAL_PLACES = 2"` → одна строка;
`-k "long_lived or notice_regions or swap_target_and_an_oob_target"` → 4 passed;
`tests/test_pages/test_htmx_gates.py -k "redirect or backlog"` → 4 passed, `NOT_YET_CONVERTED_COUNT = 34` не двинулся.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Признак htmx снимается пустым заголовком, а не выбором фикстуры

- **Найдено при:** Задача 1, тест `test_the_delete_response_repairs_the_sentinel_only_over_htmx`.
- **Проблема:** тест запрашивает ОБЕ фикстуры (`authed_client` и `htmx_client`), а `htmx_client` по объявлению возвращает ТОТ ЖЕ объект клиента и выставляет `HX-Request` глобально. Половина «без признака htmx» получала 200 вместо 302 — запроса без признака в таком тесте не бывает вовсе.
- **Починка:** половина деградации шлёт `headers={"HX-Request": ""}`. Пустое значение считается отсутствием признака ЯВНО и по объявлению (`app/pages/htmx.py::is_htmx`), а не по совпадению; ловушка складываемости фикстур названа в докстринге теста одной фразой. Утверждение при этом стало СИЛЬНЕЕ предписанного: доказывается, что присланное поле не переключает путь деградации на фрагментный ответ. Половина «поля нет вовсе» закреплена отдельным тестом задачи 3, который запрашивает одну фикстуру.
- **Файлы:** `tests/test_pages/test_account_groups.py`.
- **Коммит:** `fc03990`.

### 2. [Rule 3 — Blocking] Проверка строгой положительности приехала на задачу раньше

- **Найдено при:** Задача 1, пункт 6 действия («Смещение собирается только когда `rendered_rows` пришло и строго положительно (задача 3)»).
- **Проблема:** план поручает проверку задаче 3, но собрать смещение в задаче 1 без неё нельзя: `rendered_rows=0` при найденной строке дало бы смещение `-1` уже на первом же прогоне задачи 1.
- **Починка:** условие `rendered_rows is not None and rendered_rows > 0` и абзац о причине («величина приходит от недоверенного клиента, отрицательное смещение — либо отказ маршрута, либо молча съехавшая выдача») внесены в коммите задачи 1. Задача 3 внесла ТЕСТ, закрепляющий это свойство (`test_a_non_positive_rendered_rows_does_not_build_a_sentinel`), — то есть предмет у неё остался.
- **Файлы:** `app/pages/account_groups.py`.
- **Коммит:** `fc03990` (код), `73d1014` (тест).

### 3. [Rule 2 — Missing critical] Поимённое чтение новой внеполосной цели в положительном контроле

- **Найдено при:** Задача 2, пункт 6 («проверить, что действующий контроль продолжает видеть все объявленные множества»).
- **Проблема:** новая цель `group-list-sentinel` попадала во все правила через ОБЩИЕ множества, но множество, потерявшее ровно одну цель, остаётся непустым и молчит: выпавшая из обхода цель снимает с себя И правило существования идентификатора, И правило двух ролей — разом и без признака.
- **Починка:** одна строка утверждения дописана в СУЩЕСТВУЮЩИЙ положительный контроль (двадцать второй контроль не заведён, число `test_control_*` осталось 21).
- **Файлы:** `tests/test_templates/test_htmx_markup_gates.py`.
- **Коммит:** `969ec94`.

---

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing critical)
**Impact on plan:** ни одна правка не расширила предмет плана. Две первые — вынужденные механикой (общий объект фикстур; невозможность собрать смещение без проверки вырожденного числа), третья усиливает контроль, прямо предписанный пунктом 6 задачи 2. Прохибиции плана соблюдены целиком: keyset-пагинация не заведена, умолчание `modal()` не сдвинуто, условных внеполосных блоков по-прежнему ровно один, `LONG_LIVED_REGION_IDS` не расширен, G-11 не ослаблен, Playwright и новые зависимости не появились, форма-триггер удаления не тронута, `hx-include` на предка списка не навешен.

## Issues Encountered

Прогон ВСЕЙ суиты (`uv run pytest tests/ -q`) вышел за 600-секундный лимит инструмента и доводился фоном; его итог в эту сводку не попал. Вместо него исполнены все суиты, названные разделом `<verification>` плана, ПЛЮС две суиты, на которые правка могла подействовать за пределами плана (`tests/test_templates` целиком — 148 passed; `tests/test_pages/test_responsive_markup.py` — 139 passed, инвентарь шаблонов и библиотека компонентов от нового файла не сдвинулись). Прогон полной суиты остаётся предметом верификации фазы.

## Known Stubs

Нет. Поле `search` заведено этим планом и уже используется обработчиком для сборки адреса сентинела (закреплено `test_the_repaired_sentinel_keeps_the_search_filter`); его ВТОРОЙ потребитель — план 09-06 (WARN-6). Это объявленная последовательность планов, а не заглушка.

## Принятый долг, названный честно

Абсолютное смещение остаётся структурно хрупким: оно верно ровно до следующей мутации набора, о которой курсор не узнал. Сегодня такая мутация одна — удаление одной строки с экрана, — и она чинится. Промоушен к keyset-пагинации (`after_id`) станет ОБЯЗАТЕЛЬНЫМ при появлении любого из четырёх спусковых крючков, перечисленных в `<assumption_delta_decision>` плана: вторая мутация набора без перезагрузки; изменение порядка выдачи; второй одновременный клиент на том же списке; снятие строки, о котором документ не отчитывается. Ни одного из четырёх сегодня нет.

Инвариантный тест, который покраснеет при возврате сингулярного допущения «набор между отрисовкой и дочитыванием не меняется», — `test_the_scroll_cursor_survives_a_fragment_delete`.

## User Setup Required

None — внешней конфигурации план не требует.

## Next Phase Readiness

- **Готово для 09-06.** Поле `search` заведено и доезжает до обработчика; форма утверждения повторного удаления перенесена на охраняемое свойство (равенство ВНУТРИ класса «строка не найдена») и обязана быть исполнена там: прежняя проксирующая пара «первый / второй ответ при одном теле» теперь разойдётся по смещению (`R−1` против `R`), и это ВЕРНО — в живом документе второе нажатие уходит уже с `rendered_rows = R−1`.
- **Готово для 09-08.** `OOB_BLOCKS = 10`, состав `REVEALED_SITES` пересобран, границы, двигаться не имевшие права, утверждены записями.
- **Готово для 09-09.** Ручной обход обязан включить пункт: удаление строки на ПРОКРУЧЕННОМ экране (вторая порция), проверка отсутствия потери и задвоения глазом — единственное, что здесь не исполняется машинно (D10 в `coverage`).
- **Блокеров нет.** Требования `FORM-02` и `QUAL-01` объявлены также планами 09-06, 09-08, 09-09, у которых сводок ещё нет, поэтому `REQUIREMENTS.md` этим планом НЕ трогается — отметка отложена до последнего объявившего плана.

## Self-Check

Проверено исполнением:

- `app/templates/account_groups/includes/sentinel.html` — FOUND;
- `.planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-05-SUMMARY.md` — FOUND;
- коммиты `84f21e9`, `fc03990`, `969ec94`, `73d1014` — все четыре присутствуют в `git log`;
- все `<acceptance_criteria>` трёх задач перепрогнаны на итоговом дереве (таблица «Verification Results»), ни одно не пропущено.

## Self-Check: PASSED

---
*Phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy*
*Completed: 2026-08-30*
