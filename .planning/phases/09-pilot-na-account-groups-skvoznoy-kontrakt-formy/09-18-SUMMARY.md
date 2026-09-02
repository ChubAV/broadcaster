---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 18
subsystem: pages
tags: [htmx, jinja2, fastapi, forms, search-filter, tdd]

# Dependency graph
requires:
  - phase: 09 (план 09-06)
    provides: "третье место отрисовки строки группы — `toggle_response.html`, вызывающий макрос с `with_modal=false`"
  - phase: 09 (план 09-15)
    provides: "починка WR-03 — скрытое поле строки поиска в ОБЕИХ формах пути удаления и правило равенства их наборов полей"
  - phase: 09 (план 09-15)
    provides: "присвоение присланного состояния вместо инверсии хранимого — форма, которую проза строки продолжала описывать снятой"
  - phase: 09 (план 09-13)
    provides: "`_screen_url` и `_filter_params` — единый источник адреса приземления с сохранённым фильтром"
provides:
  - "обработчик тумблера ПРИНИМАЕТ строку поиска телом формы и проводит её через тот же `_clean_search`, что и обработчик удаления"
  - "ОБА выхода тумблера собраны `_screen_url(account_id, term)`; вхождений f-строки адреса в модуле осталось одно — тело самого помощника"
  - "строка поиска доезжает до ВСЕХ ТРЁХ мест отрисовки формы удаления, а не до двух"
  - "форма тумблера несёт скрытое поле строки поиска — третье такое поле в строке группы"
  - "`DELETE_FORM_RENDER_SITES` / `DELETE_FORM_RENDER_SITES_DECLARED = 3` — объявленное число мест отрисовки с зубами: четвёртое, заведённое молча, краснеет"
  - "`_delete_trigger_form` — разборщик ОДНОЙ формы удаления для фрагмента, где панели подтверждения нет по построению"
  - "правило третьего места отрисовки, утверждающее НЕ ТОЛЬКО набор имён полей, но и ЗНАЧЕНИЕ"
  - "поведенческое правило: тело формы удаления ИЗ ОТВЕТА ТУМБЛЕРА приземляется на отфильтрованную выдачу"
  - "`TOGGLE_CLAIM_SITES_MEASURED = 2` и правило прозы о механизме идемпотентности тумблера с отрицательным контролем"
  - "закрытие CR-02, WR-01 и WR-02 ревизии четвёртого круга (`09-REVIEW.md`, `09-VERIFICATION.md` гейп 2)"
affects: [09-19, 09-20, "Phase 10 (FORM-06)"]

actuals:
  tokens: 17855
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "ПАРА правил вместо переименования: имя существующего правила выбирается подстрокой командой свидетельств, поэтому предмет расширяется вторым правилом плюс объявленным числом мест, а не переименованием первого"
    - "правило разметочной симметрии утверждает НАБОР ИМЁН И ЗНАЧЕНИЕ: имена совпадали и на сломанном дереве — поле было, величины не было"
    - "признак htmx ставится ОДНОМУ запросу заголовком, а не фикстурой: `htmx_client` возвращает тот же объект клиента и выставил бы его всему тесту"
    - "правило прозы на АБЗАЦАХ (комментарий Jinja / пробег строк-# модуля), а не на файле: летописная рамка одного абзаца не засчитывается другому"
    - "переход цвета ИСПОЛНЯЕТСЯ в отдельном отсоединённом рабочем дереве на SHA коммита правила; порог кода прогона — РОВНО `1`"

key-files:
  created: []
  modified:
    - app/pages/account_groups.py
    - app/templates/account_groups/partials/toggle_response.html
    - app/templates/account_groups/includes/group_row.html
    - tests/test_pages/test_account_groups.py

key-decisions:
  - "Имя `test_both_delete_forms_post_the_same_field_names` НЕ изменено: команда свидетельств `.planning/REQUIREMENTS.md` выбирает его подстрокой, и переименование закрыло бы дефект удалением записи о нём. Предмет накрыт ПАРОЙ плюс объявленным числом мест"
  - "Правило третьего места утверждает ЗНАЧЕНИЕ, а не только равенство множеств имён: измерено — имя поля в ответе тумблера ЕСТЬ, а значение пустое, и правило на одних множествах было бы зелено ровно на сломанном дереве"
  - "`term` и `screen_url` собираются ДО развилки и одни на обе ветки: собранные порознь, они выдали бы ветку ненайденной группы различием заголовка перехода (D-13)"
  - "Область сканирования правила прозы — ТОЛЬКО `app/templates/account_groups/` и `app/pages/account_groups.py`: константы правила живут в `tests/` и попали бы в собственную выборку при более широкой области"
  - "Перечень мест прозы НЕ выписывается руками (в отличие от `OOB_SILENCE_CLAIM_SITES`): `<behavior>` плана предписывает сканеру НАХОДИТЬ места обходом области приложения, а роль антивакуума играет измеренное число `TOGGLE_CLAIM_SITES_MEASURED`"
  - "Летописная рамка засчитывается по слову «план» перед номером, а не по любому виду `NN-NN`: даты измерений (`08-30`) в этом дереве есть, и рамкой они не являются"

patterns-established:
  - "Объявленное число мест ОТРИСОВКИ (а не только мест-отступлений) как сторож ОКНА соседних правил: пара правил равна предмету ровно до тех пор, пока мест столько же"
  - "Разборщик ОДНОЙ формы рядом с разборщиком ДВУХ: существующий не ослабляется, потому что ослабленный перестал бы ловить пропажу панели на странице"
  - "Летопись вместо переписывания в РАЗМЕТКЕ, а не только в питоновском докстринге: прежняя формулировка приведена дословно и названа описывающей снятую форму"

requirements-completed: []

coverage:
  - id: D1
    description: "Число мест отрисовки формы удаления объявлено и утверждается: обход дерева шаблонов даёт РОВНО объявленный перечень из трёх"
    requirement: "QUAL-06"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_number_of_delete_form_render_sites_is_the_declared_one"
        status: pass
    human_judgment: false
  - id: D2
    description: "CR-02: третье место отрисовки печатает строку поиска — набор имён полей равен эталону СТРАНИЦЫ И значение то же"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_toggle_response_renders_the_delete_form_with_the_same_field_names"
        status: pass
      - kind: command
        ref: "прогон правила на ДО-правочном дереве 78c6622 в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "ПОВЕДЕНЧЕСКАЯ половина: тело формы удаления ИЗ ОТВЕТА ТУМБЛЕРА, посланное базовым путём, приземляется на отфильтрованную выдачу, а удаление единственной найденной строки приводит на выдачу без строк"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_toggle_response_trigger_form_body_lands_on_the_filtered_listing"
        status: pass
    human_judgment: false
  - id: D4
    description: "WR-01: адрес приземления тумблера несёт фильтр и приходит из того же источника, что и адрес после перезагрузки; неотличимость чужой и несуществующей группы не ослаблена"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_toggle_landing_address_carries_the_search_filter"
        status: pass
      - kind: command
        ref: "grep -c 'redirect=f\"/accounts/{account_id}/groups\"' app/pages/account_groups.py → 0; grep -c 'f\"/accounts/{account_id}/groups\"' → 1"
        status: pass
    human_judgment: false
  - id: D5
    description: "WR-02: проза строки описывает действующий механизм (присвоение) и несёт летопись снятого; класс сторожит правило с антивакуумом"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_every_claim_about_the_toggle_names_the_mechanism_the_handler_has"
        status: pass
      - kind: command
        ref: "прогон правила на ДО-правочном дереве bb91db6 в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D6
    description: "Зубы правила прозы: место, называющее снятую форму без летописной рамки, обязано краснеть"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_control_negative_a_claim_site_naming_the_removed_form_reddens"
        status: pass
    human_judgment: false
  - id: D7
    description: "QUAL-01 / idempotency: присвоение присланного состояния остаётся идемпотентным — параметр `search` состояния не касается"
    requirement: "QUAL-01"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_groups.py#test_the_toggle_is_idempotent_on_a_repeated_post"
        status: pass
    human_judgment: false
  - id: D8
    description: "Путь деградации не двинулся: обе пары деградации зелены, собственного RedirectResponse у переведённых обработчиков нет, NOT_YET_CONVERTED_COUNT не тронут"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py (21 passed) + -k 'degrades_without_htmx or no_converted_handler_builds_its_own_redirect or not_yet_converted' (3 passed)"
        status: pass
    human_judgment: false
  - id: D9
    description: "QUAL-06, поведенческая половина: фокус после подмены строки возвращается на элемент с тем же id"
    verification: []
    human_judgment: true
    rationale: "НЕ ЗАКРЫТО ЭТИМ ПЛАНОМ И НЕ ДОЛЖНО. Разметочная половина закреплена `test_toggle_fragment_keeps_the_toggle_id` (зелено); поведенческая сервером не доказуема — предмет плана 09-20"

# Metrics
duration: ~55 min
completed: 2026-09-02
status: complete
---

# Phase 9 Plan 18: Сквозной контракт формы на третьем месте отрисовки — Summary

**Строка поиска доехала до всех ТРЁХ мест отрисовки формы удаления, оба выхода тумблера
пришли из единого источника адреса, а ложность прозы о снятом механизме закрыта ПРАВИЛОМ с
антивакуумом и отрицательным контролем — переход цвета каждого из четырёх новых правил
ИСПОЛНЕН в отдельном отсоединённом рабочем дереве кодом РОВНО `1`, а не заявлен парой
коммитов.**

## Performance

- **Duration:** ~55 min
- **Completed:** 2026-09-02
- **Tasks:** 3 из 3 (человеческих останов в плане нет — `autonomous: true`)
- **Files modified:** 4
- **Commits:** 4

## Accomplishments

- **CR-02 закрыт по всей цепи, а не в одном звене.** Обработчик тумблера принимает
  `search: str | None = Form(None)` и проводит его через тот же `_clean_search`, что и
  обработчик удаления; величина доезжает до `toggle_response.html` выражением `term or ""` —
  тем же, каким это делает страница; форма тумблера получила скрытое поле, без которого
  величине неоткуда приехать на пути «Alpine мёртв, htmx жив».
- **WR-01 закрыт единым источником, а не второй f-строкой.** `term` и `screen_url` собираются
  ДО развилки и одни на обе ветки. Вхождений `f"/accounts/{account_id}/groups"` в модуле
  осталось **одно** — тело самого `_screen_url`, ради которого правка и делалась.
- **Окно правила равенства наборов полей стало равно предмету.** Существующее правило
  осталось правилом СТРАНИЦЫ и не переименовано; третье место получило собственное правило, а
  число мест отрисовки объявлено `DELETE_FORM_RENDER_SITES_DECLARED = 3` и утверждается
  обходом дерева.
- **Правило третьего места утверждает ЗНАЧЕНИЕ, а не только имена — и это несущее решение.**
  Измерение подтвердилось посимвольно: имена полей на странице и в ответе тумблера СОВПАДАЛИ
  (`{'search'}` в обоих), а значение в ответе было пустым. Правило, сверяющее одни множества,
  было бы зелено ровно на сломанном дереве.
- **WR-02 закрыт правилом, а не правкой.** Абзац приведён к форме летописи, а класс «проза
  описывает снятый механизм» сторожит правило с измеренным числом мест и отрицательным
  контролем: правка чинит одно место, правило — класс, который наследуют Фазы 10-15.
- **Довод прозы УСИЛЕН, а не только исправлен.** Присвоение даёт идемпотентность в ПОЛНОМ
  смысле; инверсия давала безвредность только В ПАРЕ нажатий. Прежняя формулировка занижала
  реальную гарантию и одновременно называла её не тем механизмом — абзац теперь говорит обе
  половины.

## ПЕРЕХОД ЦВЕТА — ИСПОЛНЕН, А НЕ ЗАЯВЛЕН

Все четыре прогона шли в ОТДЕЛЬНОМ отсоединённом рабочем дереве (`git worktree add --detach`)
на SHA коммита правила. Живое дерево на запись не открывалось ни разу — тот класс отказа, при
котором проверка, ПИШУЩАЯ в проверяемый файл, зеленеет ровно там, где производственная правка
уничтожена, здесь невыразим, а не подавлен.

### 1. `test_the_toggle_response_renders_the_delete_form_with_the_same_field_names` на `78c6622`

```
E       AssertionError: форма удаления в ОТВЕТЕ ТУМБЛЕРА несёт строку поиска '' вместо 'Альфа': тело ответа {'search': ''}. Имя поля на месте, ЗНАЧЕНИЯ нет — третье место отрисовки печатает умолчание макроса, потому что до него величине неоткуда приехать. Равенство имён выше от этого зелено, и именно так дефект и дожил до ревизии (CR-02).
E       assert '' == 'Альфа'
E
E         - Альфа

tests/test_pages/test_account_groups.py:5774: AssertionError
=========================== short test summary info ============================
FAILED tests/test_pages/test_account_groups.py::test_the_toggle_response_renders_the_delete_form_with_the_same_field_names
1 failed, 140 deselected, 2 warnings in 2.21s
код правила на ДО-правочном дереве 78c6622: 1
```

### 2. `test_the_toggle_response_trigger_form_body_lands_on_the_filtered_listing` на `78c6622`

```
E   AssertionError: тело формы удаления ИЗ ОТВЕТА ТУМБЛЕРА ({'search': ''}) не донесло строки поиска: адрес приземления /accounts/1/groups — человек, переключивший строку без Alpine, приземляется на НЕотфильтрованный список
/…/wt-red/tests/test_pages/test_account_groups.py:5840: AssertionError: тело формы удаления ИЗ ОТВЕТА ТУМБЛЕРА ({'search': ''}) не донесло строки поиска: адрес приземления /accounts/1/groups — человек, переключивший строку без Alpine, приземляется на НЕотфильтрованный список
1 failed, 140 deselected, 2 warnings in 1.51s
код правила на ДО-правочном дереве 78c6622: 1
```

### 3. `test_the_toggle_landing_address_carries_the_search_filter` на `78c6622`

```
E   AssertionError: тело формы тумблера ({'is_active': '1'}) не донесло строки поиска до адреса приземления: /accounts/1/groups. Адрес после действия и адрес после перезагрузки РАЗОШЛИСЬ — ровно то, что докстринг `_screen_url` запрещает прямым текстом; человек без Alpine приземляется на НЕотфильтрованный список, а ветка «выдача опустела» решается по всему аккаунту вместо той выдачи, что он видел
/…/wt-red/tests/test_pages/test_account_groups.py:5923: AssertionError: тело формы тумблера ({'is_active': '1'}) не донесло строки поиска до адреса приземления: /accounts/1/groups. …
1 failed, 140 deselected, 2 warnings in 1.58s
код правила на ДО-правочном дереве 78c6622: 1
```

### 4. `test_every_claim_about_the_toggle_names_the_mechanism_the_handler_has` на `bb91db6`

```
E   AssertionError: проза рассуждает о том, чем обработчик тумблера обеспечивает безвредность второго нажатия, НЕ НАЗЫВАЯ действующего механизма — присвоения присланного значения:
        app/templates/account_groups/includes/group_row.html

      СЛЕДСТВИЕ, НАЗВАННОЕ ПРЯМЫМ ТЕКСТОМ: обработчик ПРИСВАИВАЕТ `is_active` присланное значение с плана 09-15 и инверсии не делает. …
    assert not {'app/templates/account_groups/includes/group_row.html'}
/…/wt-red3/tests/test_pages/test_account_groups.py:6148: AssertionError
=========================== short test summary info ============================
FAILED tests/test_pages/test_account_groups.py::test_every_claim_about_the_toggle_names_the_mechanism_the_handler_has
1 failed, 142 deselected, 1 warning in 0.56s
код правила на ДО-правочном дереве bb91db6: 1
```

### Почему у пятого нового правила перехода цвета НЕТ, и это не пропуск

`test_the_number_of_delete_form_render_sites_is_the_declared_one` ЗЕЛЕНО с момента заведения —
ровно как объявляет `<behavior>` плана: «Сегодня — ЗЕЛЁНОЕ: мест ровно три, и правило сторожит
их ЧИСЛО, а не чинит дефект». То же и с
`test_control_negative_a_claim_site_naming_the_removed_form_reddens`: отрицательный контроль
зелен по обе стороны перехода намеренно — он доказывает СВОЙСТВО ПРАВИЛА, а не состояние
дерева, и краснел бы ровно тогда, когда правило потеряло бы зубы.

## Verify — по задачам, КОДАМИ ВОЗВРАТА

### Задача 1 (RED)

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `-k "number_of_delete_form_render_sites"` | `0` | **`0`** — `1 passed, 140 deselected` |
| 2 | `-k` три новых правила + `[ "$RC" -eq 1 ]` | `1` | **`1`** — `3 failed, 138 deselected` |
| 3 | `-k` ОСТАЛЬНЫЕ правила файла | `0` | **`0`** — `138 passed, 3 deselected` |
| 4 | `git diff --stat app/ \| wc -l` | `0` | **`0`** |

### Задача 2 (GREEN)

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `-k` три новых правила | `0` | **`0`** — `3 passed, 138 deselected` |
| 2 | переход цвета на `RED_SHA` в отдельном дереве | `1` | **`1`** — вывод процитирован выше |
| 3 | `pytest tests/test_pages/test_account_groups.py` | `0` | **`0`** — `141 passed in 152.21s` |
| 4 | `pytest tests/test_pages/test_htmx_gates.py` | `0` | **`0`** — `21 passed` |
| 5 | счёт f-строк адреса | `F=0`, `T=1` | **`выходов, собранных f-строкой: 0; всего вхождений: 1`** |
| 6 | счёт скрытых полей строки поиска | `3` | **`скрытых полей строки поиска в строке группы: 3`** |

### Задача 3 (RULE → GREEN)

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `-k "claim_about_the_toggle_names_the_mechanism or claim_site_naming_the_removed_form"` | `0` | **`0`** — `2 passed, 141 deselected` |
| 2 | `pytest tests/test_pages/test_account_groups.py` | `0` | **`0`** — `143 passed in 147.94s` |
| 3 | `grep -c "ПРИСВАИВАЕТ" group_row.html` | `≥1` | **`мест, называющих действующую форму: 1`** |
| 4 | `grep -c "WR-02" group_row.html` | `≥1` | **`летописных ссылок на находку: 1`** |
| 5 | `grep -c "PAY-02" group_row.html` | `≥1` | **`мест, называющих статус защиты: 1`** |
| 6 | `git diff --stat app/pages/ \| wc -l` | `0` | **`изменённых файлов app/pages/: 0`** |
| 7 | `pytest tests/ -q -p no:randomly` | `0` | **`0`** — `2688 passed in 1436.88s (0:23:56)` |

## Прочие критерии приёмки

- Параметр обработчика: `sed -n '/^async def account_groups_toggle/,/^):/p' … | grep -c "search: str | None = Form(None)"` → **`1`**.
- Передача величины макросу: `grep -c "filter_search=filter_search" toggle_response.html` → **`1`**.
- Три объявления задачи 1: `grep -c "^DELETE_FORM_RENDER_SITES\b\|^DELETE_FORM_RENDER_SITES_DECLARED\|^def _delete_trigger_form"` → **`3`**.
- Имя соседа не изменено: `grep -c "async def test_both_delete_forms_post_the_same_field_names"` → **`1`**.
- Перекрёстная ссылка в его докстринге: `grep -c "test_the_toggle_response_renders_the_delete_form_with_the_same_field_names"` → **`2`** (объявление + ссылка).
- `grep -c "^TOGGLE_CLAIM_SITES_MEASURED"` → **`1`** (значение `2`, строго больше нуля — утверждается самим правилом).
- Деградация: `-k "degrades_without_htmx or no_converted_handler_builds_its_own_redirect or not_yet_converted"` → **`0`** (`3 passed`).
- Свойства тумблера: `-k "toggle_fragment_keeps_the_toggle_id or toggle_fragment_carries_no_second_modal or toggle_is_idempotent_on_a_repeated_post or toggle_honours_the_posted_state or two_toggles_and_a_submit"` → **`0`** (`8 passed`).
- Неотличимость: `-k "indistinguishable_for_a_foreign or repeated_delete_is_harmless"` → **`0`** (`3 passed`).
- Контракт курсора `keyset`: `-k "interleaved_portion_and_delete or control_positive_the_reverse_order or scroll_cursor"` → **`0`** (`5 passed`).
- Долговых маркеров в `group_row.html`, `toggle_response.html`, `account_groups.py` — **ноль** (`grep` пуст, код `1`).
- **Тело правил между RED- и GREEN-коммитом НЕ ИЗМЕНЕНО:** `git diff 78c6622 74e1de7 -- tests/` → **пусто**; `git diff bb91db6 7504105 -- tests/` → **пусто**.

## Где теперь стои́т правленый абзац (критерий задачи 3)

`app/templates/account_groups/includes/group_row.html:151-171` — три абзаца внутри того же
Jinja-комментария, что и прежде:

- `:151-154` — действующее: обработчик **ПРИСВАИВАЕТ** `is_active` присланное значение одной
  строкой под тройным ограничением; «серверной защитой это не является (PAY-02)» оставлено
  дословно.
- `:156-161` — усиление довода: присвоение даёт идемпотентность в ПОЛНОМ смысле, инверсия
  давала безвредность только в паре нажатий.
- `:163-171` — летопись: прежняя формулировка приведена ДОСЛОВНО и названа описывающей снятую
  форму; названо и то, почему абзац дожил (план 09-15 переписал питоновский докстринг и до
  разметки не дошёл) — WR-02, план 09-18.

## Task Commits

1. **Задача 1: три правила третьего места отрисовки (RED)** — `78c6622` (`test`)
2. **Задача 2: строка поиска доезжает до третьего места; оба выхода на `_screen_url` (GREEN)** — `74e1de7` (`fix`)
3. **Задача 3, половина RULE: правило прозы о механизме идемпотентности (RED)** — `bb91db6` (`test`)
4. **Задача 3, половина GREEN: проза называет действующий механизм** — `7504105` (`docs`)
5. **Сводка завершения** — коммит `docs(09-18)` этой сводки

## Files Created/Modified

- `tests/test_pages/test_account_groups.py` (+780 строк; коммиты `78c6622`, `bb91db6`) —
  `DELETE_FORM_RENDER_SITES`, `DELETE_FORM_RENDER_SITES_DECLARED`, `GROUP_ROW_CALL_RE`,
  `_delete_form_render_sites`, `_delete_trigger_form`, `_toggle_form`,
  `TOGGLE_CLAIM_SITES_MEASURED`, сканер прозы и пять новых правил.
- `app/pages/account_groups.py` (+41/−6; коммит `74e1de7`) — параметр `search`, `term`,
  `screen_url`, оба выхода на помощника, `filter_search=term or ""` в отрисовку фрагмента.
- `app/templates/account_groups/partials/toggle_response.html` (+16/−2; коммит `74e1de7`) —
  `filter_search` в перечне ожидаемых величин и в вызове макроса.
- `app/templates/account_groups/includes/group_row.html` (+36/−3 суммарно; коммиты `74e1de7`,
  `7504105`) — скрытое поле строки поиска в форме тумблера и правдивый абзац обоснования.

## Decisions Made

- **Пара вместо переименования.** Отчёт верификации просит «расширить
  `test_both_delete_forms_post_the_same_field_names` на третье место». Расширение исполнено
  парой: имя не тронуто (команда свидетельств выбирает его подстрокой), третье место получило
  своё правило, число мест объявлено и утверждается.
- **Правило третьего места утверждает и ЗНАЧЕНИЕ.** Прогон подтвердил: множества имён
  совпадали и до правки. Правило на одних множествах было бы третьим экземпляром того же
  отказа «зелено по построению».
- **Тело формы берётся ИЗ РАЗМЕТКИ, а не набирается литералом.** Правило, подставляющее
  строку поиска руками, зеленело бы на форме, которая её не несёт, — то есть ровно там, где
  сломано. Ради этого заведён `_toggle_form`.
- **Признак htmx ставится одному запросу заголовком.** `htmx_client` возвращает ТОТ ЖЕ объект
  клиента и выставил бы признак всему тесту; двум из трёх правил нужны обе половины в одной
  функции.
- **Существующий `_delete_forms` не ослаблен.** Он требует ровно ДВУХ форм и на фрагменте
  обязан краснеть — панели там нет по построению. Ослабленный, он перестал бы ловить пропажу
  панели на СТРАНИЦЕ.
- **Правило прозы работает на АБЗАЦАХ, а не на файлах.** Файловая гранулярность засчитала бы
  летописную рамку одного абзаца совсем другому — и была бы зелена на дереве до правки.
- **Летописная рамка требует слова «план» перед номером.** Даты измерений (`08-30`,
  Chrome/macOS) в этом дереве есть, и рамкой они не являются.
- **Перечень мест прозы не выписан руками.** В отличие от `OOB_SILENCE_CLAIM_SITES`,
  `<behavior>` этого плана предписывает сканеру НАХОДИТЬ места обходом области приложения;
  антивакуумом служит измеренное число, а не рукописный список. Цена выбора — правило
  согласилось бы с переформулировкой, снявшей слово «идемпотентность»; граница названа в
  докстринге `_toggle_claim_blocks`, а не оставлена на догадку.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocker] В рабочем дереве исполнителя нет `.venv`, а команды плана зовут `uv run` и `$ROOT/.venv/bin/python`**

- **Found during:** Задача 1, первый прогон `<verify>`
- **Issue:** План набирает прогоны как `uv run pytest …`, а команду перехода цвета — как
  `ROOT=$(git rev-parse --show-toplevel); "$ROOT/.venv/bin/python" -m pytest …`. В рабочем
  дереве исполнителя `git rev-parse --show-toplevel` возвращает путь ЭТОГО дерева, а `.venv`
  в нём нет: команда упала бы предохранителем «нет $ROOT/.venv — проверка НЕ ИСПОЛНЕНА», а
  `uv run` завёл бы здесь второй `.venv` — ровно то, что план запрещает прямым текстом для
  временного дерева.
- **Fix:** Интерпретатор живого окружения зовётся по абсолютному пути
  `/source/broadcaster/.venv/bin/python -m pytest` во ВСЕХ прогонах — и в рабочем дереве, и в
  обоих временных отсоединённых. Это тот же интерпретатор, который выбрал бы `uv run` в
  `/source/broadcaster`. Ни одного `.venv` ни в одном дереве не создано.
- **Files modified:** нет (правка способа прогона, не артефакта)
- **Verification:** `/source/broadcaster/.venv/bin/python -m pytest --version` → `pytest 9.0.2`;
  все семнадцать прогонов исполнены, коды объявлены выше
- **Committed in:** отражено этой сводкой

**2. [Rule 2 — Missing critical] Разборщик формы ТУМБЛЕРА (`_toggle_form`) в перечне артефактов плана не назван**

- **Found during:** Задача 1, набор правил
- **Issue:** `<artifacts_this_phase_produces>` называет `_delete_trigger_form`, но не
  разборщик формы тумблера. Двум из трёх правил тело формы тумблера нужно, и взять его
  «как шлёт разметка» без разборщика нечем.
- **Fix:** Заведён `_toggle_form(html, account_id, group_id)` — прямой сосед
  `_delete_trigger_form` с той же границей (вложенных форм не поддерживает) и тем же
  утверждением «ровно одна». Альтернатива — набрать строку поиска в теле запроса ЛИТЕРАЛОМ —
  отвергнута: правило зеленело бы на форме, которая поля не несёт.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Verification:** три правила краснеют кодом `1` на `78c6622` и зелены на `74e1de7`
- **Committed in:** `78c6622`

**3. [Rule 2 — Missing critical] Опорные имена сканеров в перечне артефактов не перечислены**

- **Found during:** Задачи 1 и 3
- **Issue:** Перечень артефактов называет константы и правила, но не вспомогательные имена,
  без которых объявленное поведение неисполнимо.
- **Fix:** Заведены `GROUP_ROW_CALL_RE` + `_delete_form_render_sites` (обход мест отрисовки),
  `JINJA_COMMENT_BLOCK_RE`, `TOGGLE_SUBJECT_RE`, `TOGGLE_IDEMPOTENCY_RE`,
  `TOGGLE_ACTING_FORM_RE`, `TOGGLE_REMOVED_FORM_RE`, `CHRONICLE_FRAME_RE`,
  `TOGGLE_CLAIM_SCOPE_TEMPLATES`, `TOGGLE_CLAIM_SCOPE_MODULE`, `TOGGLE_CLAIM_CONTROL_BLOCK`,
  `_prose_blocks`, `_toggle_claim_blocks`, `_claims_not_naming_the_acting_form`,
  `_claims_naming_the_removed_form_unframed`. Ни одно не меняет объявленного поведения — все
  они его исполняют.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Verification:** `TOGGLE_CLAIM_SITES_MEASURED = 2` поставлено ИЗМЕРЕНИЕМ по дереву
  (обход вернул ровно два места: абзац `group_row.html` и комментарий присвоения
  `account_groups.py`), а не арифметикой плана
- **Committed in:** `78c6622`, `bb91db6`

---

**Total deviations:** 3 (одна — способ прогона, две — недостающие опорные имена).
**Impact on plan:** нулевой для предмета. Ни одно объявленное поведение не изменено, ни одно
`<acceptance_criteria>` не ослаблено, ни один порог не смягчён.

⚠️ **Чего НЕ трогалось, и это проверено, а не заявлено.** `.planning/STATE.md` и
`.planning/ROADMAP.md` — вне диффа плана целиком. `NOT_YET_CONVERTED_COUNT = 34` не тронут
(файл `test_htmx_gates.py` в диффе отсутствует). Плашка `?notice=` не выдаётся ни на успешный
тумблер, ни на успешное удаление (D-10): единственное вхождение слова в обработчике тумблера —
комментарий о том, что величина НЕ передаётся. `hx-sync='this:drop'`, пустая цель блокировки,
`trigger='change'`, `target`, `swap` и `id='group-toggle-' ~ group.id` в форме тумблера
посимвольно прежние. Планы 09-19 и 09-20 и их файлы не тронуты.

## Issues Encountered

Ни один прогон не потребовал второй попытки; ни одного авто-исправления кода приложения сверх
предписанных правкой не понадобилось. Три правила задачи 1 покраснели ровно на тех
утверждениях, ради которых написаны (несущих, а не антивакуумных), и сообщения об отказе
воспроизвели измерение верификатора посимвольно: `{'search': ''}` и `/accounts/1/groups`.

## TDD Gate Compliance

| Гейт | Требуется | Состояние |
|---|---|---|
| RED (задачи 1-2) | да | ✅ `78c6622` — три правила краснеют кодом РОВНО `1`; `git diff --stat app/` пуст |
| GREEN (задача 2) | да | ✅ `74e1de7` — переход цвета ИСПОЛНЕН в отдельном отсоединённом дереве на `78c6622`, код `1`; тело правил не тронуто ни на байт |
| RED (задача 3) | да | ✅ `bb91db6` — правило прозы краснеет кодом `1`; `git diff --stat app/` пуст |
| GREEN (задача 3) | да | ✅ `7504105` — переход цвета ИСПОЛНЕН на `bb91db6`, код `1`; `git diff --stat app/pages/` пуст |
| REFACTOR | нет | — |

## User Setup Required

Нет. План не устанавливает пакетов, не трогает ни одной ORM-модели и ни одной ревизии
Alembic, не конфигурирует внешних сервисов.

## Допущения, оставшиеся ОТКРЫТЫМИ (не закрыты молча)

- **FORM-02 / `unclassified`** — обход не отнёс требование ни к одной категории. Допущение
  «деградация не задета» ПРОВЕРЕНО прогоном (`test_toggle_degrades_without_htmx`,
  `test_delete_degrades_without_htmx`, `tests/test_pages/test_htmx_gates.py` целиком), а не
  рассуждением; само требование остаётся `unresolved`.
- **QUAL-06 / `unclassified`** — план возврат фокуса не трогает: `id='group-toggle-' ~ group.id`
  посимвольно прежний, `test_toggle_fragment_keeps_the_toggle_id` зелен. Поведенческая
  половина сервером не доказуема — предмет плана 09-20.
- **QUAL-01 / `concurrency`** (`verification: backstop`) — тройной `WHERE` и единица записи в
  один `commit` не тронуты; параллельного исполнения суита не поднимает, и утверждать шире
  измеренного нельзя.

## Next Phase Readiness

✅ **ПЛАН ЗАВЕРШЁН.** Все три задачи исполнены, все семнадцать прогонов `<verify>` дали
объявленные коды, суита зелена целиком (`2688 passed`).

- **CR-02, WR-01 и WR-02 четвёртого круга закрыты** — первые два механизмом, третий
  механизмом И правилом.
- **Фаза 10 (FORM-06) получает записанное обоснование, описывающее действующий механизм.**
  Читатель, решающий вопрос клиентской блокировки для сорока шести оставшихся форм, унаследует
  свойство, которое у кода ЕСТЬ, и правило, которое покраснеет, если оно снова разъедется.
- **Окно правил симметрии равно предмету и сторожится.** Четвёртое место отрисовки, заведённое
  молча, краснит `test_the_number_of_delete_form_render_sites_is_the_declared_one`.
- **Требования FORM-02, QUAL-01, QUAL-06 этим планом НЕ переводятся** — прохибиция плана,
  предмет плана 09-20.
- **Планы 09-19 (WR-04, WR-05) и 09-20 (наблюдение глазами) этим планом не затронуты.**
- Ветка `worktree-agent-ab9f287b9d0f5c5c9` не мержится этим планом: слияние волны — по
  манифесту оркестратора.

## Self-Check: PASSED

- Коммиты `78c6622`, `74e1de7`, `bb91db6`, `7504105` — FOUND в `git log`.
- Все четыре изменённых файла существуют на диске и входят в `git diff --stat 2b39c1b..HEAD`.
- Переход цвета исполнен для КАЖДОГО из четырёх правил, у которых он предусмотрен; вывод
  процитирован дословно, код каждый раз РОВНО `1`.
- `git diff 78c6622 74e1de7 -- tests/` и `git diff bb91db6 7504105 -- tests/` — оба пусты:
  тело правил между гейтами не тронуто.
- `.planning/STATE.md` и `.planning/ROADMAP.md` в диффе плана отсутствуют.

## Known Stubs

Нет. Ни одного правила не пропущено, ни одного `<verify>` не оставлено неисполненным, ни
одного долгового маркера не отгружено. Записей в `.planning/WINDOWS.md` этот план не порождает.

---
*Phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy*
*Completed: 2026-09-02*
