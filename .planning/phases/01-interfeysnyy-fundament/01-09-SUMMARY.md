---
phase: 01-interfeysnyy-fundament
plan: 09
subsystem: ui
tags: [jinja2, templates, macros, tailwind-removal, responsive, pytest]

# Dependency graph
requires:
  - phase: 01-02
    provides: "Библиотека компонентов components/*.html и запрет на неэкранированный вывод"
  - phase: 01-07
    provides: "Правило [data-cell-label] в app.css (строки 1133 и 1144) и медиазапрос 860px"
  - phase: 01-08
    provides: "Сплошной обход шаблонов и список признаков utility-классов (40 токенов)"
provides:
  - "Параметр label у макроса cell — примитив подписи колонки через библиотеку"
  - "Слот дополнительных полей формы у макроса modal через блочный вызов caller()"
  - "Расширенный детектор utility-классов: пять семейств с числовым суффиксом"
  - "Удалённый мёртвый app/templates/includes/icons.html — седьмой недостижимый шаблон"
affects: [01-10, 01-11, 01-12, 01-13, "Фазы 2-6 (вызывают cell и modal)"]

actuals:
  tokens: 21455
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Блочный вызов макроса (caller is defined) как единственный способ передать разметку в компонент — параметром строкой готовый HTML не принимается"
    - "Детектор признаков удалённого фреймворка вынесен в общую функцию utility_markers_in(), которой пользуются оба сплошных обхода"
    - "Семейства классов с числовым суффиксом заданы выражениями (TAILWIND_PATTERNS), а не подстроками"

key-files:
  created: []
  modified:
    - app/templates/components/table.html
    - app/templates/components/modal.html
    - tests/test_templates/test_components.py
    - tests/test_pages/test_responsive_markup.py
  deleted:
    - app/templates/includes/icons.html

key-decisions:
  - "Параметр label поставлен ПОСЛЕДНИМ в сигнатуре cell — позиционные вызовы десяти существующих шаблонов не сдвинулись"
  - "При пустом label элемент подписи не эмитится вовсе: вывод байт-в-байт прежний, что закреплено проверкой на точное равенство строки"
  - "Слот модалки принимает разметку блочным вызовом, а не параметром строкой — тот же приём, что у cell; готовый HTML в макрос по-прежнему не попадает"
  - "Ни один новый токен не был сужен: сканирование всех живых шаблонов и обработчиков дало ноль ложных срабатываний до удаления файла"
  - "Оба сплошных обхода переведены на общий детектор — иначе расширенные семейства до реального файла бы не дошли"

patterns-established:
  - "Подпись колонки дублирует название из rowhead и берётся из того же списка колонок — контракт записан в шапке table.html"
  - "Синтетический тест списка признаков держит свойство после того, как реальный нарушитель удалён"
  - "Обратная гарантия OWN_DESIGN_SYSTEM_CLASSES: свои классы дизайн-системы не имеют права опознаваться как чужие"

requirements-completed: [UI-04, UI-06]

coverage:
  - id: D1
    description: "Макрос cell принимает подпись колонки и выводит её отдельным элементом перед значением; без подписи вывод не изменился"
    requirement: "UI-06"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_cell_label_emitted"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_cell_without_label_emits_no_span"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_cell_label_is_escaped"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_cell_label_composes_with_all_flags"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_cell_label_in_block_call"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py (60 passed без правок файла)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Модальное подтверждение принимает дополнительные поля формы блочным вызовом, не меняя маршрута, метода и приоритета отмены — на уровне РАЗМЕТКИ"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_accepts_block_fields"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_block_fields_do_not_replace_actions"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_body_and_block_coexist"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_block_call_keeps_method_and_action"
        status: pass
    human_judgment: false
  - id: D3
    description: "Поведение модалки в рантайме при появлении полей: начальный фокус на отмене, ловушка фокуса подхватывает новые поля, скрытые поля не попадают в обход по Tab"
    requirement: "UI-04"
    verification: []
    human_judgment: true
    rationale: "Ни один тест проекта не исполняет JS (01-VERIFICATION.md держит поведение модалки в behavior_unverified). Разметочные признаки проверены, но фактический порядок фокуса в браузере — нет. Браузерный тест-раннер в этой фазе намеренно не вводится."
  - id: D4
    description: "В проекте не осталось ни одного шаблона с utility-классами удалённого фреймворка, включая недостижимые из роутов файлы"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_no_utility_classes_anywhere"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_no_utility_classes_in_python_handlers"
        status: pass
      - kind: e2e
        ref: "tests/test_pages/test_shell.py (79 passed — ни один адрес не потерял 200)"
        status: pass
      - kind: other
        ref: "test ! -f app/templates/includes/icons.html"
        status: pass
    human_judgment: false
  - id: D5
    description: "Список признаков utility-классов ловит семейства, которые реально встречались в этой кодовой базе, а не абстрактный набор"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_utility_markers_catch_the_families_that_were_missed"
        status: pass
      - kind: other
        ref: "Наблюдённый красный на реальном файле после расширения списка и до удаления (см. RED #2 ниже)"
        status: pass
    human_judgment: false

# Metrics
duration: 33 min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 09: Примитивы библиотеки для закрытия SC-3 и SC-5 Summary

**Параметр `label` у макроса `cell` эмитит `<span data-cell-label>` под уже существующее правило `app.css:1133`, макрос `modal` получил слот полей формы через `caller()` под массовое удаление, а седьмой недостижимый шаблон `includes/icons.html` удалён после того, как расширенный на пять семейств детектор utility-классов доказанно на нём покраснел.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-08-09T17:05:00Z
- **Completed:** 2026-08-09T17:38:00Z
- **Tasks:** 3 (все TDD)
- **Files modified:** 4 изменено, 1 удалён

## Accomplishments

- **Подпись колонки стала доступна через библиотеку.** Правило `[data-cell-label]` лежало в `app.css` с Плана 07 и было подтверждено верификацией как рабочее, но эмитить атрибут было нечем — у `cell` не было параметра. Теперь есть, и Планы 11-12 могут проставлять подписи, не дописывая библиотеку каждый по-своему.
- **Обратная совместимость доказана точным равенством, а не «не упало».** `test_cell_without_label_emits_no_span` сравнивает вывод `cell('42')` со строкой `<span class="cell">42</span>` целиком. Плюс 60 тестов `test_responsive_markup.py` прошли без единой правки файла — все существующие вызовы `cell(...)` дают прежнюю разметку.
- **Модалка научилась нести НАБОР, а не одну сущность.** Массовое удаление групп — единственное подтверждение в проекте, где идентификаторы приходят полями формы (`form.getlist("group_ids")`), а не в маршруте. Без слота Gap 1 закрылся бы одиннадцатью местами из двенадцати.
- **Промах Плана 08 закрыт доказательно, а не декларативно.** Два наблюдённых красных: синтетический исходник до расширения списка (все пять семейств возвращали `set()`) и реальный файл после расширения и до удаления. Синтетический тест остаётся зелёным после удаления — свойство держится и без реального нарушителя.
- **Ни один токен не пришлось сужать.** Сканирование всех `class="…"` во всех живых шаблонах и во всех обработчиках `app/pages/*.py` дало ровно 8 совпадений, все — в удаляемом файле, и ноль ложных срабатываний на своих классах.

## Task Commits

1. **Задача 1: Параметр `label` у макроса `cell` (UI-06)** — `ec8944e` (test, RED) → `2d8abc6` (feat, GREEN)
2. **Задача 2: Слот полей формы в модалке (UI-04)** — `31d636d` (test, RED) → `09329d7` (feat, GREEN)
3. **Задача 3: Расширение детектора + удаление мёртвого шаблона (UI-04)** — `52541b0` (test, RED #1) → `7ff274d` (feat, GREEN)

Рефакторинга не потребовалось ни в одной задаче: изменения аддитивные.

## Files Created/Modified

- `app/templates/components/table.html` — параметр `label=None` последним в сигнатуре `cell`; при заданном значении первым внутри ячейки выводится `<span data-cell-label>`. В шапку записан контракт: подпись дублирует название колонки из `rowhead` и берётся из того же списка колонок.
- `app/templates/components/modal.html` — `{%- if caller is defined %}{{ caller() }}{% endif %}` внутри формы после текста и перед блоком кнопок. В шапку записано, чего слот НЕ меняет: начальный фокус, ловушку фокуса, метод и маршрут.
- `tests/test_templates/test_components.py` — 9 новых тестов (5 на подпись, 4 на слот), +141 строка. Было 25 тестов, стало 34.
- `tests/test_pages/test_responsive_markup.py` — `TAILWIND_PATTERNS` (пять выражений), общий детектор `utility_markers_in()`, `MISSED_FAMILIES`, `OWN_DESIGN_SYSTEM_CLASSES`, тест `test_utility_markers_catch_the_families_that_were_missed`. Оба сплошных обхода переведены на общий детектор.
- `app/templates/includes/icons.html` — **удалён** (98 строк, 24 макроса, ноль потребителей).

## Итоговые сигнатуры библиотеки

Планы 11-12 и Фазы 2-6 вызывают именно это:

```jinja
{% macro cell(text=None, grow=false, mono=false, muted=false, area=None, title=None, label=None) %}
```

Вывод без подписи (байт-в-байт как до Плана 09):
```html
<span class="cell">42</span>
```
Вывод с подписью:
```html
<span class="cell"><span data-cell-label>Групп</span>42</span>
```
Со всеми признаками:
```html
<span class="cell cell--mono cell--muted" data-area="meta"><span data-cell-label>Групп</span>42</span>
```

Модалка — сигнатура не изменилась, добавился блочный вызов:
```jinja
{% call modal(id='del-bulk', title='Удалить выбранные группы?',
              action='/groups/bulk', confirm_label='Удалить') %}
  <input type="hidden" name="action" value="delete">
{% endcall %}
```
Содержимое блока попадает между `<form …>` и `<div class="modal__actions">`.

## Доказательство деадности удалённого файла

Искали и по шаблонам, и строкой в Python, по `app/`, `tests/`, `scripts/`, расширения `.py` и `.html`:

| Проверка | Результат |
|---|---|
| `grep -rn '{% from "includes/…' app/templates/` | 13 строк, **все** — `messenger_icon.html`; ни одной на удаляемый файл |
| `grep -rn 'icons.html' app/ tests/ scripts/ main.py alembic/` | вне самого файла — ноль потребителей |
| Имена всех 24 макросов (`icon_back`, `icon_spinner`, `icon_delete`, …) | встречаются только как определения внутри самого файла |
| `tests/test_pages/test_shell.py` после удаления | 79 passed — ни один адрес не потерял 200 |

Сосед по каталогу `app/templates/includes/messenger_icon.html` — ЖИВОЙ: импортируется 12 шаблонами (`accounts/list`, `accounts/partial_cards`, `accounts/partials/sync_status_card`, `admin/group_info_detail`, `admin/groups_info`, `admin/user_detail`, `admin/user_history_detail`, `dashboard/includes/recent_send_card`, `groups/includes/group_row`, `history/detail`, `history/includes/history_card`, `schedules/includes/schedule_row`). Не тронут.

`test_template_inventory` не затронут: он считает файлы только по `components/*.html` (утверждение `len(components) == 13`), а удалённый файл лежал в `includes/`. Проверено чтением теста ДО удаления и прогоном ПОСЛЕ — правка ожидаемого числа не потребовалась.

## Окончательный список признаков utility-классов

40 подстрочных токенов Плана 08 не тронуты. Добавлено пять выражений:

| Семейство | Выражение | Ловит |
|---|---|---|
| бесконечное вращение | `\banimate-spin\b` | `animate-spin` |
| прозрачность с числовым суффиксом | `\bopacity-\d+\b` | `opacity-25`, `opacity-75` |
| отрицательный отступ с префиксом направления | `(?:^\|\s)-[mp][trblxy]?-\d` | `-ml-0.5`, `-mt-2` |
| дробный отступ | `\b[mp][trblxy]?-\d+\.\d+\b` | `mr-1.5`, `px-2.5` |
| размерные классы высоты и ширины | `\b[hw]-\d+(?:\.\d+)?\b` | `h-4 w-4`, `h-8 w-8` |

**Ни один токен не был сужен.** Сканирование до удаления файла: 8 совпадений, все в `includes/icons.html`; ноль совпадений во всех остальных шаблонах и ноль в `app/pages/*.py`. Обратная гарантия закреплена тестом — `OWN_DESIGN_SYSTEM_CLASSES` (`cell cell--mono cell--muted`, `btn btn--ghost`, `msg__glyph msg__glyph--tg {{ size }}`, `modal__panel`, `badge badge--success`, `avatar`, `mono` и др.) не имеет права быть опознан ни одним признаком.

### Наблюдённые красные

**RED #1 — синтетический исходник ДО расширения списка.** Все пять семейств возвращали пустое множество под старым списком из 40 токенов:

```
MISSED  бесконечное вращение                          'animate-spin h-8 w-8'  -> set()
MISSED  прозрачность с числовым суффиксом             'opacity-25'            -> set()
MISSED  отрицательный отступ с префиксом направления  '-ml-0.5'               -> set()
MISSED  дробный отступ                                'mr-1.5'                -> set()
MISSED  размерные классы высоты и ширины              'h-3 w-3'               -> set()
```
Текст падения pytest: `AssertionError: семейство не опознано: бесконечное вращение ('animate-spin h-8 w-8')`

**RED #2 — реальный файл ПОСЛЕ расширения списка и ДО удаления.** Сплошной обход покраснел и назвал файл дословно:

```
FAILED tests/test_pages/test_responsive_markup.py::test_no_utility_classes_anywhere
AssertionError: utility-классы остались в шаблонах:
{'includes/icons.html': {'opacity-25', '-ml-0', 'animate-spin', 'opacity-75', 'ml-0.5'}}
```

Это и есть подтверждение, что дописанные семейства ловят ровно те классы, из-за которых промах Плана 08 случился.

### Честное ограничение: семейство размерных классов проверено только синтетически

Сплошной обход смотрит **только** на значения `class="…"`. В удалённом файле литералы `h-4 w-4`, `h-8 w-8`, `h-3 w-3` стояли в значениях параметров по умолчанию макросов (`{% macro icon_back(size='h-4 w-4') %}`), а в самом атрибуте было `class="{{ size }}"` — Jinja-выражение. Поэтому в RED #2 семейство размерных классов **не сработало**: четыре семейства из пяти назвали файл, размерное — нет.

Практического значения для этой фазы это не имеет (файл удалён целиком), но для будущих фаз важно: семейство размерных классов держится ТОЛЬКО синтетическим тестом. Если появится шаблон с размерным классом прямо в `class="…"`, обход его поймает; если размер придёт через параметр макроса по умолчанию — не поймает. Расширение обхода на значения параметров по умолчанию в план не входило и не делалось.

## Decisions Made

- **Параметр `label` — последним в сигнатуре.** Позиционные вызовы `cell(...)` в существующих шаблонах не сдвигаются. Проверено прогоном `test_responsive_markup.py` без единой правки файла.
- **При пустом `label` элемент не эмитится вовсе, а не эмитится пустым.** Строчная конструкция `{%- if label %}…{% endif %}` со стрип-маркером даёт вывод, идентичный прежнему до символа — это закреплено сравнением на точное равенство, а не подстрокой.
- **Слот модалки — блочный вызов, а не параметр строкой.** Готовый HTML параметром макрос по-прежнему не принимает: запрет Плана 02 распространён и на новую точку входа. Тот же приём, что у `cell`.
- **Оба сплошных обхода переведены на общий детектор `utility_markers_in()`.** Без этого расширенные семейства жили бы только в синтетическом тесте и до реального файла бы не дошли — красный на `includes/icons.html` не наступил бы, и доказательства промаха не было бы.
- **Добавлена обратная гарантия `OWN_DESIGN_SYSTEM_CLASSES`.** План предупреждал, что широкие токены могут сработать на живом шаблоне. Вместо того чтобы ловить это прогоном и потом сужать вручную, свойство закреплено тестом: список признаков теперь сам себя сторожит.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Оба сплошных обхода переведены на общий детектор**
- **Найдено при:** Задаче 3, шаг 2
- **Проблема:** План описывает «расширить список признаков», но обходы содержали инлайновые генераторы по `TAILWIND_TOKENS`. Расширение только константы не дошло бы до обходов — реальный красный (RED #2), который план требует НАБЛЮДАТЬ, не наступил бы.
- **Исправление:** Логика обнаружения вынесена в `utility_markers_in()`; `test_no_utility_classes_anywhere` и `test_no_utility_classes_in_python_handlers` переведены на неё.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** RED #2 наступил и назвал файл; после удаления оба обхода зелёные.
- **Коммит:** `7ff274d`

**2. [Rule 2 - Missing Critical] Обратная гарантия: свои классы не опознаются как чужие**
- **Найдено при:** Задаче 3, шаг 1
- **Проблема:** План допускал, что широкий токен сработает на живом шаблоне, и предписывал в этом случае сузить его вручную. Но ничто не удерживало бы свойство дальше: следующее расширение списка могло снова задеть свои классы, и обнаружилось бы это только падением обхода.
- **Исправление:** В синтетический тест добавлен блок `OWN_DESIGN_SYSTEM_CLASSES` — двенадцать реальных значений `class="…"` дизайн-системы, ни одно из которых не имеет права быть опознано.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** Тест зелёный; сканирование живых шаблонов дало ноль ложных срабатываний независимо.
- **Коммит:** `52541b0`

**3. [Rule 1 - Bug] Собственные комментарии ломали критерий приёмки**
- **Найдено при:** Задаче 3, шаг 3
- **Проблема:** Три новых комментария в тесте содержали литерал `includes/icons.html`, из-за чего критерий `grep -rn 'includes/icons.html' app/ tests/ scripts/ | wc -l == 0` не выполнялся бы — при том, что потребителей у файла нет.
- **Исправление:** Комментарии переформулированы («мёртвый набор иконок в каталоге includes») без потери смысла.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** `grep -rn 'includes/icons.html' app/ tests/ scripts/ | wc -l` → `0`
- **Коммит:** `7ff274d`

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** Все три обслуживают требования самого плана — наблюдаемый красный, устойчивость расширенного списка и буквальное выполнение критерия приёмки. Расширения области нет: ни одного файла вне `<files>` плана не тронуто.

## Issues Encountered

**Базовая линия суиты — 572, а не 545.** Must-have плана называет «545 passed на базовой линии верификации». Фактический прогон на базе `643d1ad` до единой правки: **572 passed**. Число в плане устарело — оно взято из `01-VERIFICATION.md`, а волны 01-06…01-08 после той верификации добавили тесты. Инвариант, который число охраняет («полная суита остаётся зелёной»), выполнен: 572 → 577 (+5, Задача 1) → 581 (+4, Задача 2) → 582 (+1, Задача 3). Ни один существующий тест не потребовал правки.

**Расхождение зафиксировано, а не подогнано:** ожидаемое число в плане не редактировалось, потому что план — исторический документ; правильное место для актуальной базовой линии — этот SUMMARY.

## Требования: почему REQUIREMENTS.md не тронут

`UI-04` и `UI-06` объявлены двенадцатью планами фазы, включая ещё не выполненные 01-10, 01-11, 01-12, 01-13. Правило общего идентификатора (#2388) запрещает помечать такой ID выполненным, пока не завершился ПОСЛЕДНИЙ объявивший его план — иначе первый финишировавший план закрыл бы требование, пока соседи ещё в работе. Готовое подмножество пустое, поэтому `REQUIREMENTS.md` не изменялся. Требования будут помечены после плана 01-13.

## Known Stubs

Отсутствуют. Заглушек, пустых значений, ведущих в разметку, и маркеров долга (`TODO`, `FIXME`, `TBD`) в изменённых файлах не появилось — проверено: удаление файла не оставило ни маркера, ни закомментированного тела.

## Threat Flags

Новой security-релевантной поверхности не добавлено. Диспозиции `mitigate` из `<threat_model>` выполнены:

| Threat ID | Как закрыт |
|---|---|
| T-09-01 | Подпись проходит обычным экранированным выводом Jinja; закреплено `test_cell_label_is_escaped`; `test_no_unsafe_escaping` по-прежнему зелёный |
| T-09-02 | Слот принимает разметку блочным вызовом, а не строкой параметром; готовый HTML параметром макрос не принимает |
| T-09-03 | `method="post"` и `action` не изменены; закреплено `test_modal_block_call_keeps_method_and_action` и грепом (`method="post"` встречается 2 раза, включая дословную запись в шапке) |
| T-09-04 | Деадность доказана до удаления по шаблонам и по строкам в Python; `test_shell.py` — 79 passed |
| T-09-05 | `x-ref="cancel"` ровно один; порядок индексов проверен: отмена раньше `type="submit"` |
| T-09-SC | Пакеты не устанавливались, новых зависимостей нет |

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- **Готово для Плана 11 (подписи колонок):** `cell(..., label='НАЗВАНИЕ')` эмитит `<span data-cell-label>`; правило `app.css:1133` и медиазапрос 860px уже на месте. Контракт «брать подпись из того же списка колонок, которым вызывается `rowhead`» записан в шапке `table.html`.
- **Готово для Плана 12 (массовое удаление групп):** `{% call modal(...) %}<input type="hidden" …>{% endcall %}` кладёт поля внутрь формы. Форма данных обработчика подтверждена чтением `app/pages/groups.py`: поле `action` со значением `delete` и повторяющиеся поля `group_ids`. Текущая реализация в `groups/list.html` строит форму из JS и вызывает браузерный `confirm()` — её замена принадлежит Плану 12, файл не тронут.
- **Открытое допущение (не блокер):** поведение модалки в рантайме (Esc, ловушка фокуса, возврат фокуса, порядок обхода при появившихся полях) программно не проверяется — ни один тест проекта не исполняет JS. Проверены разметочные признаки. Введение браузерного тест-раннера — отдельное решение об инструментарии, в этой фазе намеренно не принималось.
- **Замечание для будущих фаз:** семейство размерных классов (`h-4 w-4`) в детекторе держится только синтетическим тестом — сплошной обход смотрит на `class="…"` и не видит значения параметров макросов по умолчанию. Подробности в разделе про ограничение выше.
- **graphify:** `graphify-out/` в этом worktree отсутствует (не отслеживается git), поэтому `graphify update .` не выполнялся. Обновление графа уместно после слияния ветки в основную рабочую копию.

## Self-Check: PASSED

**Файлы на диске:**
- `app/templates/components/table.html` — FOUND (содержит `label=None`, `data-cell-label`)
- `app/templates/components/modal.html` — FOUND (содержит `caller()`, `caller is defined`)
- `tests/test_templates/test_components.py` — FOUND (34 теста)
- `tests/test_pages/test_responsive_markup.py` — FOUND (содержит `animate-spin`, `opacity-`, `test_utility_markers_catch_the_families_that_were_missed`)
- `app/templates/includes/icons.html` — ОТСУТСТВУЕТ, как и требуется (`test ! -f` → 0)

**Коммиты в истории:** `ec8944e`, `2d8abc6`, `31d636d`, `09329d7`, `52541b0`, `7ff274d` — все шесть присутствуют.

**Проверка плана (`<verification>`) перепрогнана целиком:**

| # | Команда | Результат |
|---|---|---|
| 1 | `uv run pytest tests/test_templates/test_components.py -x -q` | 34 passed |
| 2 | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` | 61 passed |
| 3 | `uv run pytest tests/test_pages/test_shell.py -q` | 79 passed |
| 4 | `test ! -f app/templates/includes/icons.html` | exit 0 |
| 5 | `just test` | **582 passed** |

**Критерии приёмки всех трёх задач перепрогнаны — все PASS**, включая поведенческие (порядок подписи и значения, экранирование, сочетание с признаками, положение полей внутри формы, приоритет отмены, отсутствие подписи без `label`).

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
