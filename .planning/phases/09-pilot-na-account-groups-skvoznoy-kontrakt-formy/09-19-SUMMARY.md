---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 19
subsystem: testing
tags: [htmx, jinja2, jsdom-free-js-execution, tdd, single-source, deferred-items]

# Dependency graph
requires:
  - phase: 09 (план 09-17)
    provides: "запуск исходника JS в интерпретаторе (`NODE_BIN`, `MODAL_LIFECYCLE_HARNESS`, `_run_modal_lifecycle`) — то, что этот план переносит в единственное место"
  - phase: 09 (план 09-13)
    provides: "вынужденная правка окна теста панели повтора (граница по следующей панели вместо 2000 символов) — предмет WR-04"
  - phase: 08 (QUAL-03)
    provides: "инлайн-сценарий плашек отказа с двумя обработчиками и тремя гейтами по исходнику"
provides:
  - "`tests/conftest.py::run_node_script(source)` — ЕДИНСТВЕННЫЙ на проект запуск исходника JS в интерпретаторе с разбором последней строки вывода как JSON"
  - "`NODE_BIN` переехал в `tests/conftest.py`; собственного вызова подпроцесса в `test_components.py` не осталось"
  - "`_retry_panel_form(html, log_id)` — окно, режущееся по СОБСТВЕННОЙ форме панели подтверждения повтора, с раздельными отказами «нет корня» и «нет собственной формы»"
  - "`test_control_negative_a_panel_without_its_own_form_reddens` — отрицательный контроль смещения окна на подставленном документе"
  - "признак однократной регистрации `data-htmx-failure-wired` (`document.body.dataset.htmxFailureWired`) на ТОМ ЖЕ узле, к которому вешаются слушатели"
  - "`FAILURE_BANNER_HANDLERS_MEASURED = 2`, `_failure_banner_script`, `_failure_banner_registration_count(path, runs)` — ПОВЕДЕНЧЕСКИЙ замер регистраций"
  - "`test_the_failure_banner_registers_its_handlers_once_per_body` с антивакуумом, `test_the_failure_banner_guard_lives_on_the_node_it_wires`, `test_control_negative_an_unguarded_banner_accumulates_listeners`"
  - "`DEF-09-03` и `DEF-09-04` — два непоглощённых пункта круга с назначенной фазой у каждого"
  - "закрытие WR-04 и WR-05 ревизии четвёртого круга (`09-REVIEW.md:385-460`)"
affects: [09-20, "Phase 10 (FORM-06)", "Phase 15 (GATE-09/GATE-10)"]

actuals:
  tokens: 13272
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "единственный на проект запуск подпроцесса как ФУНКЦИЯ МОДУЛЯ conftest, а не фикстура: у запуска нет жизненного цикла теста, и фикстура потребовала бы параметра у каждого правила"
    - "павлоад подаётся ПОДСТАНОВКОЙ образца в исходник, а не стандартным вводом: общий запуск принимает ровно строку и вторым каналом не обзаводится"
    - "окно правила ограничивается СЛЕДУЮЩИМ корнем не ради утверждений, а ради того, чтобы отсутствие предмета стало ОТКАЗОМ, а не молчаливым захватом чужой разметки"
    - "ПОВЕДЕНЧЕСКОЕ правило числа регистраций: исходник сценария исполняется дважды против одного стаб-узла со счётчиком; антивакуумное утверждение о ОДНОМ исполнении стои́т первым"
    - "переход цвета ИСПОЛНЯЕТСЯ в отдельном отсоединённом рабочем дереве на SHA коммита правила; порог кода прогона — РОВНО `1`"

key-files:
  created: []
  modified:
    - tests/conftest.py
    - tests/test_templates/test_components.py
    - tests/test_pages/test_history_retry.py
    - tests/test_pages/test_shell.py
    - app/templates/includes/htmx_error_banner.html
    - .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/deferred-items.md
    - graphify-out/ (gitignored — в историю не попадает)

key-decisions:
  - "`_retry_panel_form` заведён В RED-КОММИТЕ С СЕГОДНЯШНЕЙ СЕМАНТИКОЙ (граница по следующей панели), и только GREEN-коммит меняет его тело. Иначе контроль в RED падал бы `NameError`, а не «окно молча вернуло чужую разметку» — то есть краснел бы не по своей причине"
  - "Поиск собственной формы ОГРАНИЧЕН следующим корнем окна (`<div class=\"modal\"`). Без границы панель, потерявшая форму, захватила бы форму СЛЕДУЮЩЕГО окна и вернула бы её молча — ровно то, что `<behavior>` плана («отсутствие формы ВНУТРИ — отдельное сообщение об отказе») и запрещает"
  - "Контроль задачи 1 сеет ДВА журнала на одну тройку сущностей, а проверяемой берёт панель, за которой в документе ещё есть соседняя: контроль обязан воспроизводить ту разметку, на которой правило зеленело не по своей причине"
  - "`run_node_script(source)` принимает РОВНО исходник; павлоад гарнира панели подставляется образцом `__PAYLOAD__`, а не подаётся стандартным вводом. Стандартный ввод был бы вторым каналом, о котором знал бы один вызывающий из двух"
  - "`_failure_banner_registration_count(path, runs=2)` — путь ПАРАМЕТРОМ и число исполнений ПАРАМЕТРОМ: без первого невозможен отрицательный контроль, без второго — антивакуумное утверждение о ОДНОМ исполнении"
  - "Правило совпадения узлов разбирает ПРИЁМНИК вызова (`([A-Za-z_$][\\w.$]*)\\.addEventListener`), а не факт вхождения слова `dataset`: предмет — совпадение двух узлов, а не наличие двух строк"
  - "Отступ тел обоих обработчиков НЕ правлен: прохибиция требует посимвольного сохранения, и переиндентация переписала бы каждую строку сценария, включая раннее сравнение с кодом ответа валидации. Выбор назван абзацем в шапке шаблона, а не оставлен на догадку"

patterns-established:
  - "RED-коммит вводит ХЕЛПЕР со снятой семантикой, чтобы контроль краснел по СВОЕЙ причине, а не по отсутствию имени"
  - "Общий запуск подпроцесса живёт в conftest функцией модуля; частные гарниры и их константы остаются у своих предметов"
  - "Отрицательный контроль поведенческого правила подставляет копию, в которой УСЛОВИЕ обращено в заведомо истинное, а не вырезано вместе с телом: снятым обязан быть ПРИЗНАК, а не регистрация"

requirements-completed: []

coverage:
  - id: D1
    description: "WR-04: все три утверждения теста панели повтора говорят об ОДНОЙ И ТОЙ ЖЕ форме — собственной форме проверяемой панели"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_confirmation_panel_carries_a_real_form"
        status: pass
      - kind: command
        ref: "grep -c 'id=\"history-retry-\\d+\"' tests/test_pages/test_history_retry.py → 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Смещение окна доказано ОТРИЦАТЕЛЬНЫМ КОНТРОЛЕМ: панель, потерявшая собственную форму при целой разметке соседней строки, роняет правило"
    requirement: "FORM-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_control_negative_a_panel_without_its_own_form_reddens"
        status: pass
      - kind: command
        ref: "прогон контроля на ДО-правочном дереве 7d3073e в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D3
    description: "WR-05: два исполнения инлайн-сценария дают то же число регистраций, что и одно (2, а не 4)"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_registers_its_handlers_once_per_body"
        status: pass
      - kind: command
        ref: "прогон правила на ДО-правочном дереве 70ef917 в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D4
    description: "T-09-19-02: признак однократности стои́т на ТОМ ЖЕ узле, к которому вешаются слушатели — подмена узла снимает и признак"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_guard_lives_on_the_node_it_wires"
        status: pass
      - kind: command
        ref: "прогон правила на ДО-правочном дереве 70ef917 в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D5
    description: "Зубы замера: копия БЕЗ признака обязана дать удвоенное число регистраций"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_negative_an_unguarded_banner_accumulates_listeners"
        status: pass
      - kind: command
        ref: "прогон контроля на ДО-правочном дереве 70ef917 в отдельном отсоединённом рабочем дереве → код 1"
        status: pass
    human_judgment: false
  - id: D6
    description: "Запуск интерпретатора JS живёт в проекте в ОДНОМ экземпляре, и правила плана 09-17 зелены на нём; судьба всех четырёх имён утверждена ЧИСЛАМИ"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py (54 passed)"
        status: pass
      - kind: command
        ref: "grep -c 'def run_node_script' tests/conftest.py → 1; grep -c subprocess test_components.py → 0; ^NODE_BIN в conftest → 1, в test_components → 0; три оставшихся имени → 3"
        status: pass
    human_judgment: false
  - id: D7
    description: "T-09-19-03: ни одного стока разметки и ни одного нового чтения из ответа; текст обеих заготовок не тронут"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py -k 'failure_banner or network_banner' (10 passed)"
        status: pass
    human_judgment: false
  - id: D8
    description: "T-09-19-05: два пункта, которые круг называет и не поглощает, маршрутизированы записями с назначенной фазой и механизмом со ссылкой на исходник"
    verification:
      - kind: command
        ref: "grep -c '^## DEF-09-0[34]' deferred-items.md → 2; grep -c 'Назначенная фаза' → 3"
        status: pass
    human_judgment: false
  - id: D9
    description: "QUAL-02, ребро `unclassified`: предмет требования (класс индикатора и его порог видимости) правкой плашки НЕ задет"
    requirement: "QUAL-02"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py -k indicator (4 passed)"
        status: pass
    human_judgment: false
  - id: D10
    description: "Число слушателей на живом узле тела документа В БРАУЗЕРЕ после нескольких переходов HX-Location равно двум"
    verification: []
    human_judgment: true
    rationale: "НЕ ЗАКРЫТО ЭТИМ ПЛАНОМ И НЕ МОЖЕТ БЫТЬ. Суита исполняет сценарий в интерпретаторе со СТАБ-узлом и подмены самого узла не воспроизводит; ревизия назвала эту неопределённость прямо. Замер счётчиком регистраций в живом браузере — проверка 4.2 плана 09-20 (backstop истины `must_haves`)"

# Metrics
duration: ~75 min
completed: 2026-09-02
status: complete
---

# Phase 9 Plan 19: Окно правила равно его предмету, а общий канал отказа регистрируется однажды — Summary

**Окно теста панели повтора возвращено к предмету и это доказано отрицательным контролем, а
общий канал обратной связи вехи перестал вешать слушателей заново на каждом переходе
`HX-Location` — число регистраций утверждается ИСПОЛНЕНИЕМ сценария (было `4` при двух
обработчиках, стало `2`), запуск интерпретатора JS сведён в проекте к одному экземпляру, и
переход цвета КАЖДОГО из четырёх новых правил исполнен в отдельном отсоединённом рабочем
дереве кодом РОВНО `1`.**

## Performance

- **Duration:** ~75 min
- **Completed:** 2026-09-02
- **Tasks:** 3 из 3 (человеческих останов в плане нет — `autonomous: true`)
- **Files modified:** 6 (плюс gitignored `graphify-out/`)
- **Commits:** 6 + сводка

## Accomplishments

- **WR-04 закрыт возвратом окна к предмету, а не расширением предмета.** `_retry_panel_form`
  режет окно по СОБСТВЕННОЙ форме панели (`<form class="modal__form"` … `</form>`), и все три
  утверждения — `method="post"`, `action` с идентификатором записи, `type="submit"` — говорят
  теперь об одной и той же форме. Утверждений о FORM-06 не добавлено: требование принадлежит
  Фазе 10.
- **Смещение окна доказано ИСПОЛНЕНИЕМ.** Контроль собирает подставленный документ из
  настоящего — вырезает собственную форму проверяемой панели, оставляя форму-триггер соседней
  строки нетронутой, — и требует, чтобы разбор УПАЛ. На ДО-правочном дереве он не падает:
  прогон на `7d3073e` дал код `1` с сообщением «ОКНО МОЛЧА ВЕРНУЛО ЧУЖУЮ РАЗМЕТКУ».
- **Измерение планировщика подтвердилось посимвольно.** Первый же прогон поведенческого
  правила на неправленом шаблоне дал `assert 4 == 2` — ровно то число, которое план объявил
  измеренным. Накопление слушателей было настоящим, а не выведенным.
- **WR-05 закрыт признаком на ТОМ ЖЕ узле, а не на документе.** Признак —
  `document.body.dataset.htmxFailureWired` (в разметке: `data-htmx-failure-wired`). Подмена
  узла тела снимает вместе с ним и признак, поэтому регистрация происходит ровно один раз на
  ЖИВОЙ узел. Признак на документе или на окне пережил бы подмену и оставил бы новый узел без
  обработчиков ВОВСЕ — отказ громче исходного (T-09-19-02), и он гейтируется отдельным
  правилом.
- **Запуск интерпретатора JS сведён к одному экземпляру.** `run_node_script(source)` живёт в
  `tests/conftest.py` функцией модуля; `NODE_BIN` переехал вместе с ним; собственного вызова
  подпроцесса в `test_components.py` не осталось. Правила плана 09-17 перенацелены и зелены
  целиком (54 passed).
- **Два непоглощённых пункта круга переданы по адресу.** `DEF-09-03` (шесть литералов размера
  порции на соседних экранах) и `DEF-09-04` (вселенная гейта G-2 — только POST) — обе записи с
  назначенной **Фазой 15**, механизмом со ссылкой на файл и строку и развилками решения.

## ПЕРЕХОД ЦВЕТА — ИСПОЛНЕН, А НЕ ЗАЯВЛЕН

Все четыре прогона шли в ОТДЕЛЬНОМ отсоединённом рабочем дереве (`git worktree add --detach`)
на SHA коммита правила; интерпретатор звался по абсолютному пути
`/source/broadcaster/.venv/bin/python` — `uv run` внутри временного дерева не звался ни разу и
второго `.venv` не заведено. Живое дерево на запись не открывалось.

### 1. `test_control_negative_a_panel_without_its_own_form_reddens` на `7d3073e` (WR-04)

```
F                                                                        [100%]
=================================== FAILURES ===================================
E   Failed: ОКНО МОЛЧА ВЕРНУЛО ЧУЖУЮ РАЗМЕТКУ: панель без собственной формы не уронила правило, а значит правило доказывает наличие формы у СОСЕДНЕЙ строки, а не у проверяемой панели (WR-04)
…/scratchpad/wr04-before/tests/test_pages/test_history_retry.py:1534: Failed: ОКНО МОЛЧА ВЕРНУЛО ЧУЖУЮ РАЗМЕТКУ: панель без собственной формы не уронила правило, а значит правило доказывает наличие формы у СОСЕДНЕЙ строки, а не у проверяемой панели (WR-04)
=========================== short test summary info ============================
FAILED …/wr04-before/tests/test_pages/test_history_retry.py::test_control_negative_a_panel_without_its_own_form_reddens
1 failed, 61 deselected, 2 warnings in 1.65s
```

**Код возврата: `1`.**

### 2. `test_the_failure_banner_registers_its_handlers_once_per_body` на `70ef917` (WR-05)

```
F                                                                        [100%]
=================================== FAILURES ===================================
E   AssertionError: includes/htmx_error_banner.html: два исполнения сценария дали 4 регистраций вместо 2 — на каждом переходе HX-Location общий канал видимости отказа вешает слушателей ЗАНОВО, и число их растёт всю сессию
    assert 4 == 2
…/scratchpad/wr05-before/tests/test_pages/test_shell.py:2348: AssertionError: includes/htmx_error_banner.html: два исполнения сценария дали 4 регистраций вместо 2 …
=========================== short test summary info ============================
FAILED …/wr05-before/tests/test_pages/test_shell.py::test_the_failure_banner_registers_its_handlers_once_per_body
1 failed, 140 deselected, 1 warning in 0.70s
```

**Код возврата: `1`.** ⚠️ Это и есть подтверждение измерения планировщика: `4` при двух
обработчиках.

### 3. `test_the_failure_banner_guard_lives_on_the_node_it_wires` на `70ef917`

```
F                                                                        [100%]
=================================== FAILURES ===================================
E   AssertionError: includes/htmx_error_banner.html: признака однократности в сценарии НЕТ — обработчики вешаются заново на каждом переходе HX-Location (WR-05)
    assert []
…/scratchpad/wr05-before/tests/test_pages/test_shell.py:2379: AssertionError: includes/htmx_error_banner.html: признака однократности в сценарии НЕТ — обработчики вешаются заново на каждом переходе HX-Location (WR-05)
=========================== short test summary info ============================
FAILED …/wr05-before/tests/test_pages/test_shell.py::test_the_failure_banner_guard_lives_on_the_node_it_wires
1 failed, 140 deselected, 1 warning in 0.11s
```

**Код возврата: `1`.**

### 4. `test_control_negative_an_unguarded_banner_accumulates_listeners` на `70ef917`

```
F                                                                        [100%]
=================================== FAILURES ===================================
E   AssertionError: в настоящем файле нет проверки признака однократности — подставлять нечего, и контроль ничего не доказал бы
    assert None
…/scratchpad/wr05-before/tests/test_pages/test_shell.py:2411: AssertionError: в настоящем файле нет проверки признака однократности — подставлять нечего, и контроль ничего не доказал бы
=========================== short test summary info ============================
FAILED …/wr05-before/tests/test_pages/test_shell.py::test_control_negative_an_unguarded_banner_accumulates_listeners
1 failed, 140 deselected, 1 warning in 0.08s
```

**Код возврата: `1`.** Контроль краснеет ДО правки по названной причине — подставлять нечего;
после правки он краснел бы иначе (не удвоилось), и обе половины его свойства покрыты.

### Тело правил между RED- и GREEN-коммитом НЕ ИЗМЕНЕНО

- Задача 2: `git diff 70ef917 efe9cb6 -- tests/` → **пусто** (0 строк). Правила не подгонялись
  под правку.
- Задача 1: GREEN-коммит правит `_retry_panel_form` и комментарий, но тело самого контроля не
  тронуто — `git diff 7d3073e 9cd6f32 -- tests/test_pages/test_history_retry.py | grep -c '^[+-].*control_negative'` → **`0`**.

## Verify — по задачам, КОДАМИ ВОЗВРАТА

Прогоны шли `/source/broadcaster/.venv/bin/python -m pytest` (см. «Deviations», отклонение 1).

### Задача 1 (WR-04)

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `pytest tests/test_pages/test_history_retry.py -q -p no:randomly` | `0` | **`0`** — `62 passed in 54.92s` |
| 2 | `-k "control_negative_a_panel_without_its_own_form"` | `0` | **`0`** — `1 passed, 61 deselected` |
| 3 | `grep -c "def _retry_panel_form"` | `1` | **`разборщиков собственной формы панели: 1`** |
| 4 | `grep -c 'id="history-retry-\d+"'` | `0` | **`вырезаний окна по СЛЕДУЮЩЕЙ панели: 0`** |
| — | `git diff --stat app/ \| wc -l` | `0` | **`0`** |
| — | `grep -c "WR-04"` | `≥1` | **`3`** |

### Задача 2 (WR-05)

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `pytest tests/test_pages/test_shell.py -q -p no:randomly` | `0` | **`0`** — `141 passed in 121.08s` |
| 2 | `pytest tests/test_templates/test_components.py -q -p no:randomly` | `0` | **`0`** — `54 passed in 1.15s` |
| 3 | `grep -c "def run_node_script" tests/conftest.py` | `1` | **`определений запуска интерпретатора в conftest: 1`** |
| 4 | `grep -c "subprocess" tests/test_templates/test_components.py` | `0` | **`собственных вызовов подпроцесса в test_components.py: 0`** |
| 5 | `grep -c "dataset" htmx_error_banner.html` | `≥2` | **`мест признака однократности: 2`** |
| 6 | `-k "failure_banner"` | `0` | **`0`** — `8 passed, 133 deselected` |
| — | `-k "failure_banner or network_banner"` | `0` | **`0`** — `10 passed` (с учётом контроля без признака) |
| — | `-k "registers_its_handlers_once_per_body"` | `0` | **`0`** |
| — | `-k "control_negative_an_unguarded_banner_accumulates_listeners"` | `0` | **`0`** |
| — | `-k "network_banner_names_the_screen_server_divergence"` | `0` | **`0`** |

**Судьба ЧЕТЫРЁХ имён плана 09-17 — числами, а не прогоном:**

| Имя | Где сейчас | Проверка | Получено |
|---|---|---|---|
| `NODE_BIN` | **ПЕРЕЕХАЛ** в `tests/conftest.py` | `grep -c "^NODE_BIN" tests/conftest.py` | **`1`** |
| `NODE_BIN` | в `test_components.py` не остался | `grep -c "^NODE_BIN" tests/test_templates/test_components.py` | **`0`** |
| `MODAL_LIFECYCLE_HARNESS`, `SCROLL_LOCK_CLASS`, `MODAL_XDATA_RE` | **ОСТАЛИСЬ** | `grep -c "^SCROLL_LOCK_CLASS\|^MODAL_XDATA_RE\|^MODAL_LIFECYCLE_HARNESS"` | **`3`** |

### Задача 3

| # | Команда | Ожидалось | Получено |
|---|---|---|---|
| 1 | `grep -c "^## DEF-09-0[34]"` | `2` | **`новых записей: 2`** |
| 2 | `grep -c "Назначенная фаза"` | `≥3` | **`записей с назначенной фазой: 3`** |
| 3 | `pytest tests/test_templates/test_htmx_markup_gates.py -k "indicator"` | `0` | **`0`** — `4 passed, 69 deselected` |
| 4 | `pytest tests/ -q -p no:randomly` | `0` | **`0`** — `2692 passed, 963 warnings in 1441.76s (0:24:01)` |
| 5 | `git status --porcelain .planning/REQUIREMENTS.md \| wc -l` | `0` | **`изменений в файле требований: 0`** |
| 6 | `graphify update .` | `0` | **`код graphify update: 0`** (вывод ниже) |
| 7 | `find app tests \( -name '*.py' -o -name '*.html' \) -newer graphify-out/graph.json \| wc -l` | `0` | **`файлов app/ и tests/, изменённых ПОЗЖЕ графа: 0`** |

Плюс критерий приёмки: `git status --porcelain .planning/REQUIREMENTS.md .planning/WINDOWS.md 09-UAT.md 09-VERIFICATION.md` → **пусто**.

### Вывод `graphify update .` — ДОСЛОВНО

```
Re-extracting code files in . (no LLM needed)...
  AST extraction: 794/794 uncached files (100%) [4 workers]
  warning: 5 source file(s) produced zero nodes and are absent from the graph: config.json, .02-EDGE-COVERAGE.json, .worktree-wave-manifest.json, new_broadcaster_design.manifest-index.json, broadcaster.json. A re-run will retry them (empties are no longer cached); if it persists, please report the file(s) (#1666).
Graph has 15586 nodes (above 5000 limit). Building aggregated community view...
graph.html written (aggregated: 877 community nodes, 718 cross-community edges)
[graphify watch] Rebuilt: 15586 nodes, 28522 edges, 877 communities
[graphify watch] graph.json, graph.html and GRAPH_REPORT.md updated in graphify-out
Code graph updated. For doc/paper/image changes run /graphify --update in your AI assistant.
```

Пять файлов с нулём узлов — JSON-манифесты планирования и дизайна, не исходники `app/` или
`tests/`; предупреждение инструмента, а не находка круга.

## Имя признака однократности — ДОСЛОВНО (критерий приёмки)

- **В разметке:** `data-htmx-failure-wired`
- **В сценарии (через `dataset`):** `document.body.dataset.htmxFailureWired`
- **Место:** `app/templates/includes/htmx_error_banner.html:103-104` — проверка и присвоение,
  оба на `document.body`, то есть на ТОМ ЖЕ узле, к которому вешаются слушатели.

## Что этот круг НЕ трогал и почему это не забытая работа

Названо прямым текстом, чтобы следующий читатель не счёл пропущенным:

- **Устаревшие записи `.planning/WINDOWS.md` (12 и 13)** — предмет их снят планом 09-13,
  статус остался `open`. Это **предмет плана 09-20** (бухгалтерия `.planning/`), и прохибиция
  этого плана запрещает их трогать.
- **Устаревший `outstanding` во frontmatter `09-UAT.md`** — там же, план 09-20.
- **Перевод состояний требований и флажков `.planning/REQUIREMENTS.md`** — план 09-20; этим
  планом не тронуты вовсе (проверено `git status --porcelain`).
- **CR-01** — план 09-17; **CR-02, WR-01, WR-02** — план 09-18. Двойного планирования нет.
- **DEF-09-01 и DEF-09-02** уже маршрутизированы и повторно не заводятся.

## Task Commits

1. **Задача 1, RED: отрицательный контроль окна панели повтора** — `7d3073e` (`test`)
2. **Задача 1, GREEN: окно режется по собственной форме панели (WR-04)** — `9cd6f32` (`fix`)
3. **Задача 2, шаг 1: перенос запуска интерпретатора в единственный источник** — `0dfdd0a` (`refactor`)
4. **Задача 2, RED: замер регистраций обработчиков (WR-05)** — `70ef917` (`test`)
5. **Задача 2, GREEN: однократная регистрация на живом узле тела** — `efe9cb6` (`fix`)
6. **Задача 3: две записи с назначенной фазой** — `fa16f87` (`docs`)
7. **Сводка завершения** — коммит `docs(09-19)` этой сводки

## Files Created/Modified

- `tests/test_pages/test_history_retry.py` (+130/−7; коммиты `7d3073e`, `9cd6f32`) —
  `_retry_panel_form`, отрицательный контроль, летопись WR-04 над утверждениями.
- `tests/conftest.py` (+82; коммит `0dfdd0a`) — `NODE_BIN`, `NODE_SCRIPT_TIMEOUT`,
  `run_node_script`, три импорта (`json`, `shutil`, `subprocess`, `pytest`).
- `tests/test_templates/test_components.py` (+18/−42; коммит `0dfdd0a`) — импорт общего
  запуска, подстановка `__PAYLOAD__`, снятие собственного подпроцесса и `NODE_BIN`.
- `tests/test_pages/test_shell.py` (+204/−5; коммит `70ef917`) —
  `FAILURE_BANNER_HANDLERS_MEASURED`, `FAILURE_BANNER_REGISTRATION_HARNESS`,
  `_BANNER_SCRIPT_RE`, `_LISTENER_HOST_RE`, `_GUARD_HOST_RE`, `_failure_banner_script`,
  `_failure_banner_registration_count` и три новых правила.
- `app/templates/includes/htmx_error_banner.html` (+27; коммит `efe9cb6`) — два абзаца шапки и
  обёртка признака однократности.
- `.planning/…/deferred-items.md` (+83; коммит `fa16f87`) — `DEF-09-03`, `DEF-09-04`.
- `graphify-out/` — перестроен (`15586` узлов, `28522` ребра); директория gitignored и в
  историю не попадает.

## Decisions Made

- **Хелпер с СЕГОДНЯШНЕЙ семантикой в RED-коммите.** `_retry_panel_form` заведён в
  `7d3073e` с прежней границей окна (по следующей панели), и только `9cd6f32` меняет его тело.
  Иначе контроль в RED падал бы `NameError` — то есть краснел бы не по своей причине, и порог
  «код РОВНО `1`» был бы удовлетворён вакуумом.
- **Поиск собственной формы ограничен следующим корнем окна.** Иначе панель, потерявшая форму,
  захватила бы форму СЛЕДУЮЩЕГО окна и вернула бы её молча. Граница не участвует в
  утверждениях — возвращается тело формы ЭТОЙ панели; она нужна ровно затем, чтобы отсутствие
  формы стало ОТКАЗОМ. Прямо названо в докстринге разборщика.
- **Контроль сеет ДВА журнала.** Один журнал дал бы документ без соседней панели, и контроль
  перестал бы воспроизводить условие, ради которого собран. Проверяемой берётся панель, за
  которой в документе ещё есть соседняя; целость её разметки утверждается отдельно.
- **`run_node_script` принимает РОВНО исходник.** Павлоад гарнира панели подставляется
  образцом `__PAYLOAD__` (единственность образца утверждается перед подстановкой), а не
  подаётся стандартным вводом: поток был бы вторым каналом, о котором знал бы один вызывающий
  из двух.
- **Функция модуля, а не фикстура.** У запуска подпроцесса нет ни подготовки, ни уборки, ни
  разделяемого состояния; фикстура потребовала бы параметра у каждого правила. Форма импорта —
  `from tests.conftest import run_node_script`, тот же образец, которым файл уже импортирует
  `seed_group`.
- **Отступ тел обработчиков не правлен.** Прохибиция требует посимвольного сохранения;
  переиндентация переписала бы каждую строку, включая раннее сравнение с кодом ответа
  валидации. Выбор назван абзацем в шапке шаблона.
- **Правило совпадения узлов разбирает ПРИЁМНИК вызова.** Проверка «в файле есть слово
  `dataset`» была бы зелена при признаке на `document` или на `window` — то есть ровно в том
  случае, который T-09-19-02 и называет более громким отказом.
- **Отрицательный контроль обращает УСЛОВИЕ в истинное, а не вырезает блок.** Снятым обязан
  быть признак, а не регистрация; целость двух вызовов регистрации в подставленной копии
  утверждается отдельно, иначе контроль доказывал бы пустоту.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocker] В рабочем дереве исполнителя нет `.venv`, а команды плана зовут `uv run`**

- **Found during:** Задача 1, первый прогон `<verify>`
- **Issue:** Все `<verify>` плана набраны как `uv run pytest …`. В рабочем дереве агента
  `.venv` отсутствует, а `uv run` завёл бы здесь второй — ровно то, что прохибиция круга
  запрещает для временных деревьев, и что рассинхронизировало бы окружение с живым.
- **Fix:** Интерпретатор живого окружения зовётся по абсолютному пути
  `/source/broadcaster/.venv/bin/python -m pytest` во ВСЕХ прогонах — и в рабочем дереве, и в
  обоих временных отсоединённых. Это тот же интерпретатор, который выбрал бы `uv run` в
  `/source/broadcaster`. Ни одного `.venv` ни в одном дереве не создано.
- **Files modified:** нет (правка способа прогона, не артефакта)
- **Verification:** все прогоны исполнены, коды объявлены выше; `2692 passed`
- **Committed in:** отражено этой сводкой

**2. [Rule 1 — Bug] Собственное утверждение записи `DEF-09-03` о числе вхождений `limit=30` в `tests/` было ЛОЖНЫМ**

- **Found during:** Задача 3, проверка написанного грепом
- **Issue:** Первая редакция записи утверждала «греп по `tests/` даёт единственное вхождение
  `limit=30`». Прогон дал **28** вхождений. Утверждение было бы ровно тем классом отказа, ради
  снятия которого круг и собран, — заявлением вместо измерения, записанным в летопись, где
  следующий читатель принял бы его за проверенный факт.
- **Fix:** Формулировка исправлена ДО коммита и приведена к измеренному: 28 вхождений, из них
  ЕДИНСТВЕННОЕ, стоящее в утверждении о ОТРИСОВАННОЙ разметке, — строка 824; остальные 27
  названы поимённо по классам (адреса, которые тесты собирают сами, один параметризованный
  набор строк запроса, один комментарий).
- **Files modified:** `.planning/…/deferred-items.md`
- **Verification:** `grep -rn "limit=30" tests/ | wc -l` → `28`; единственный `assert` с этим
  литералом — `tests/test_pages/test_account_groups.py:824`
- **Committed in:** `fa16f87` (исправлено до коммита, ложная редакция в историю не попала)

### Отступления от буквы плана, названные прямо

- **`<action>` задачи 1 описывает поиск собственной формы БЕЗ границы** («от найденной позиции
  — открывающий тег `<form class="modal__form"` и ближайший `</form>`»), а `<behavior>` того
  же плана требует, чтобы «отсутствие формы ВНУТРИ» было отдельным сообщением об отказе, и
  прямо запрещает «молча вернуть чужое окно». Две формулировки несовместимы на документе с
  несколькими панелями: без границы разбор захватил бы форму следующего окна. Исполнено по
  `<behavior>` — поиск ограничен следующим корнем `<div class="modal"`. Это НЕ расширение
  предмета: возвращается по-прежнему тело формы проверяемой панели.
- **`_failure_banner_registration_count` получил параметр `runs`** (умолчание `2`, как и
  объявлено планом). Без него антивакуумное утверждение «после ОДНОГО исполнения регистраций
  ровно `FAILURE_BANNER_HANDLERS_MEASURED`», которое `<behavior>` требует поставить ПЕРВЫМ,
  было бы невыразимо.
- **`test_control_negative_an_unguarded_banner_accumulates_listeners` в RED-состоянии краснеет
  по причине «подставлять нечего», а не «не удвоилось».** Иначе быть не может: признака в
  файле до правки нет, и подстановка его снятия невозможна. Обе половины свойства контроля
  покрыты — до правки он краснеет отсутствием якоря, после правки зеленеет удвоением.

### Что осталось КРАСНЫМ или незакрытым

Ничего красного. Незакрытым по построению остаётся ровно один пункт, и он вынесен наружу
осознанно:

- **Замер числа слушателей в ЖИВОМ БРАУЗЕРЕ** после нескольких переходов `HX-Location`. Суита
  исполняет сценарий в интерпретаторе со СТАБ-узлом тела и подмены самого узла не
  воспроизводит; ревизия назвала эту неопределённость прямо, и правило шире неё не сделано.
  Адрес — **проверка 4.2 плана 09-20** (в `must_haves` плана истина помечена
  `verification: backstop`).

## Known Stubs

Заглушек нет. Стаб-узел тела документа в
`FAILURE_BANNER_REGISTRATION_HARNESS` — это ИНСТРУМЕНТ ИЗМЕРЕНИЯ в тестовом гарнире, а не
заглушка в производственном пути: счётчик регистраций в нём настоящий (предмет), а поиск узла
по идентификатору и снятие атрибута застаблены намеренно, потому что предметом не являются.
Граница того, что этот стаб доказывает, названа абзацем в докстринге правила и вынесена в
`coverage.D10` как `human_judgment: true`.

## Threat Flags

Новой поверхности не появилось: план не заводит ни одного сетевого входа, ни одного пути
доступа к файлам в производственном коде и ни одной правки схемы. Единственная правка `app/` —
обёртка признака в инлайн-сценарии; подпроцесс интерпретатора исполняется ТОЛЬКО в тестовом
окружении и в производственный путь не входит (T-09-19-04, диспозиция `mitigate`, исходник
подаётся исключительно из собственных шаблонов проекта).

## Self-Check: PASSED

- Все шесть изменённых файлов и `graphify-out/graph.json` присутствуют на диске (`ls -la`).
- Все шесть SHA задач присутствуют в истории ветки (`git log --oneline -7`): `7d3073e`,
  `9cd6f32`, `0dfdd0a`, `70ef917`, `efe9cb6`, `fa16f87` поверх базы `c70b17f`.
- `git status --porcelain` пуст; `graphify-out/` gitignored и в коммиты не попадает.
- `.planning/STATE.md` и `.planning/ROADMAP.md` этим планом НЕ ТРОГАЛИСЬ (прохибиция круга:
  их синхронизирует оркестратор). `.planning/REQUIREMENTS.md`, `.planning/WINDOWS.md`,
  `09-UAT.md`, `09-VERIFICATION.md` — тоже не тронуты, проверено `git status --porcelain`.
