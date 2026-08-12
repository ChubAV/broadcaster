---
phase: 03-gruppy-akkaunta
plan: 03
subsystem: ui
tags: [jinja2, fastapi, sqlalchemy, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-obyavleniya-i-raspisaniya
    provides: "Карточка расписания в редакторе объявления (sched_card.html), контекст редактора _editor_context, гейт tests/test_pages/test_editor_schedules.py"
provides:
  - "Выборка групп редактора: активные ПЛЮС выключенные, уже выбранные в расписаниях этого объявления (D-07)"
  - "Ключ контекста inactive_group_ids и одноимённый параметр макроса карточки расписания"
  - "Пометка «отключена» с пояснением на строке списка выбора групп"
  - "Счётчик «выбрано N из M», согласованный с отрисованным набором строк"
affects: [03-05, 03-06, 03-07, 03-08, verify-work]

# Actuals (#2632)
actuals:
  tokens: 7071
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Расширение скоупа выборки условием ИЛИ при сохранённом условии владельца"
    - "Обход JSON-списка group_ids в Python вместо непереносимого условия по JSON-массиву"
    - "Протаскивание вспомогательного множества параметром импортированного макроса"

key-files:
  created: []
  modified:
    - app/pages/ads.py
    - app/templates/ads/includes/sched_card.html
    - app/templates/ads/form.html
    - tests/test_pages/test_editor_schedules.py

key-decisions:
  - "Множество выбранных идентификаторов строится ТОЛЬКО из расписаний этого объявления — уже проверенного на владение, поэтому подстановка чужого group_id выборку не расширяет"
  - "Обход group_ids идёт в Python, а не условием запроса: переносимого между SQLite и PostgreSQL условия «идентификатор входит в JSON-массив» нет"
  - "Числитель подписи «выбрано N из M» считает отрисованные выбранные строки, а не длину хранимого списка — иначе группы другого аккаунта врали бы в числах"
  - "Признака недоступности на флажке нет ни у одной строки: невыбранные выключенные не рендерятся вовсе, а с выбранных выбор обязан сниматься"

patterns-established:
  - "Скоуп по владельцу — отдельное неснимаемое условие: расширение выборки добавляется ИЛИ-веткой ВНУТРИ него, а не рядом с ним"
  - "Пустое множество выбранных вырождает условие в прежнее поведение — обычный случай даёт нулевой диф"

requirements-completed: [GRP-05]

coverage:
  - id: D1
    description: "Выключенная группа, уже выбранная в расписании объявления, остаётся видна в карточке расписания"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_disabled_group_chosen_in_the_schedule_stays_visible"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_active_group_is_present_regardless_of_schedules"
        status: pass
    human_judgment: false
  - id: D2
    description: "Невыбранная выключенная группа в список выбора не попадает — список не захламляется"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_disabled_group_not_chosen_is_absent_from_the_picker"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_disabled_group_chosen_in_another_ad_is_absent_here"
        status: pass
    human_judgment: false
  - id: D3
    description: "Выборка редактора остаётся скоупнутой по владельцу: чужая группа не попадает в карточку ни в одной ветке (T-03-11)"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_group_of_another_user_never_reaches_the_editor"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пометка «отключена» с пояснением стоит ровно на строке выключенной выбранной группы"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_disabled_chosen_row_is_marked_as_off"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_without_disabled_selections_renders_the_same_group_set"
        status: pass
    human_judgment: false
  - id: D5
    description: "Флажок выключенной выбранной группы работоспособен: выбор снимается и снятие доезжает до хранилища"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_disabled_chosen_checkbox_stays_operable"
        status: pass
    human_judgment: false
  - id: D6
    description: "Подпись «выбрано N из M» согласована с видимым списком в присутствии выключенных строк"
    requirement: GRP-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_group_counter_agrees_with_the_rendered_rows"
        status: pass
    human_judgment: false
  - id: D7
    description: "Вид пометки в карточке расписания на реальной ширине экрана: цвет --warn, отсутствие переполнения строки и обрезки длинного имени"
    verification: []
    human_judgment: true
    rationale: "Цвет, положение пометки внутри flex-строки и поведение при длинном имени группы проверяются глазом на 320px/400px — автоматической проверки внешнего вида в проекте нет"

# Metrics
duration: 31min
completed: 2026-08-12
status: complete
---

# Phase 03 План 03: Выключенные группы в редакторе объявления — Summary

**Редактор перестал молча терять группы: выключенная группа, уже выбранная в расписании, видна в карточке с пометкой «отключена» и снимаемым флажком, а невыбранные выключенные в список выбора не попадают**

## Performance

- **Duration:** 31 min
- **Started:** 2026-08-12T09:55:40Z
- **Completed:** 2026-08-12T10:26:40Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Выборка групп редактора расширена с «только активные» до «активные ИЛИ уже выбранные в расписаниях ЭТОГО объявления» — при пустом множестве выбранных условие вырождается в прежнее, и обычный случай даёт нулевой диф.
- Скоуп по владельцу подтверждён тестом с подстановкой чужого `group_id` в СВОЁ расписание: клиентское значение проходит весь путь до множества выбранных и всё равно не расширяет выдачу (T-03-11).
- В строке списка выбора появилась mono-пометка «отключена» в цвете `--warn` с пояснением «Группа отключена и пропускается при рассылке»; флажок такой строки остаётся работоспособным, и снятие выбора доезжает до хранилища.
- Числитель подписи «выбрано N из M» переведён с длины хранимого списка на количество ОТРИСОВАННЫХ выбранных строк — числа больше не могут противоречить списку перед глазами (RESEARCH Pitfall 6).
- Суита не деградировала: 904 теста зелёные (обход с исключением `tests/test_pages/test_account_groups.py` — файла плана 03-01 из той же волны).

## Task Commits

Каждая задача закоммичена атомарно:

1. **Task 1: Выборка групп редактора включает выключенные, но выбранные** (TDD)
   - `c13227d` (test) — RED: шесть утверждений D-07, параметр `is_active` у посева группы, помощник `_stranger`
   - `eb87bda` (feat) — GREEN: множество выбранных из расписаний этого объявления, условие «активные ИЛИ выбранные», `inactive_group_ids` в контексте
2. **Task 2: Пометка «отключена» и согласованный счётчик** — `044ade1` (feat)

_Шага REFACTOR не потребовалось: обе правки легли в существующие блоки без дублирования._

## Files Created/Modified

- `app/pages/ads.py` — в `_editor_context` собирается множество выбранных идентификаторов из расписаний объявления, выборка групп берёт активные плюс выбранные выключенные, в шаблон уходит `inactive_group_ids`
- `app/templates/ads/includes/sched_card.html` — новый параметр макроса `inactive_group_ids`, mono-пометка «отключена» в строке выбора, числитель счётчика по отрисованному набору
- `app/templates/ads/form.html` — единственная точка вызова макроса передаёт `editor.inactive_group_ids`
- `tests/test_pages/test_editor_schedules.py` — девять новых тестов D-07, помощники `_group_rows` / `_row_of` / `_stranger`, параметр `is_active` у посева группы

## Decisions Made

- **Обход `group_ids` в Python, а не условием запроса.** `Schedule.group_ids` — JSON-список; переносимого между SQLite (тесты) и PostgreSQL (прод) условия «идентификатор входит в JSON-массив» нет. Расписания объявления уже загружены выше по обработчику, поэтому второго чтения не добавилось. Образец обхода — подсчёт расписаний в `app/pages/groups.py`.
- **Расширение выборки — ИЛИ-ветка ВНУТРИ условия владельца, а не рядом с ним.** `Group.user_id == user.id AND (Group.is_active OR Group.id IN chosen)`: расширение не может снять скоуп даже при испорченном множестве.
- **`inactive_group_ids` — отдельное множество в контексте, а не флаг на объекте группы.** Карточка — импортированный макрос и контекста вызывающего не видит; второй запрос за флагом из разметки невозможен.
- **Числитель счётчика считает отрисованные строки.** Хранимый `group_ids` может нести идентификаторы групп другого аккаунта (остатки до сохранения), и `chosen | length` показывал бы число, которого в видимом списке нет.
- **Признак недоступности флажка не ставится вообще.** UI-SPEC требует «disabled только на выключенных-невыбранных», но такие строки в набор не приходят — их отсекла выборка Задачи 1. Противоречие спецификации разрешается тем, что ветка недостижима, а не тем, что атрибут ставится и ломает снятие выбора.

## Deviations from Plan

None — plan executed exactly as written.

Обе половины правки (выборка и разметка) выполнены в заданном порядке, ни одно правило отклонений не сработало. Порог в 3 попытки авто-починки не задействован.

## Issues Encountered

- **Утверждение на пометку считало два вхождения вместо одного.** Слово «отключена» входит и в видимую подпись, и в пояснение `title` («Группа отключена и пропускается при рассылке»), поэтому счёт по голой подстроке давал 2. Это дефект утверждения, а не разметки: константа `OFF_MARK_CAPTION = ">отключена<"` переведена на видимую подпись, проверка пояснения осталась отдельным утверждением. Проявилось и починено внутри Задачи 2 до её коммита.

## User Setup Required

None — внешней конфигурации фаза не требует, установок пакетов нет.

## Next Phase Readiness

- D-07 закрыт в обеих половинах; критерий фазы «переключение группы немедленно отражается на доступности групп при настройке расписаний и не прячет уже выбранные» выполнен на стороне редактора.
- Ключ контекста `inactive_group_ids` и параметр макроса доступны планам, которые будут дальше трогать карточку расписания.
- Открытым остаётся D7 из `coverage` — визуальная проверка пометки на 320px/400px; уходит в UAT фазы.
- Обход суиты выполнялся с исключением `tests/test_pages/test_account_groups.py`: файл создаёт план 03-01 той же волны. Полный обход каталога без исключений — за планом 03-05 во второй волне.

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-12*
