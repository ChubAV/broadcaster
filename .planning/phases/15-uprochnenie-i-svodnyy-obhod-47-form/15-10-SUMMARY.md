---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 10
subsystem: testing
tags: [htmx, jinja, alpine, markup-gates, pytest, form-01, modal, linkage, d-07]

requires:
  - phase: 15
    provides: "план 15-05 — `_ordinal_keys`, форма именованного нуля и контролей от вакуума в `test_htmx_markup_gates.py`"
  - phase: 15
    provides: "план 15-02 — инвентарь мест письма `test_form_inventory.py` (49/27; классы «сырой POST без hx-post» / «с hx-post»)"
  - phase: 10
    provides: "`components/modal.html` — форма панели с безусловным `hx-post=\"{{ action }}\"`; четвёртый счёт `test_modal_site_inventory` (план 10-01, D-14)"
provides:
  - "гейт связки «форма-триггер → модалка с `hx-post`» (D-07): контракт выше первого числа, четыре независимых счёта, расхождение называет ПАРУ счётов и ключ"
  - "`MODAL_TRIGGER_FORMS = 18` с перечнем `MODAL_TRIGGER_SITES` (основа события + скелет адреса на каждый ключ)"
  - "три границы связки: два запрета с именованным нулём (готовый `action`, событие вне `x-on:submit.prevent`) и контроль второй формы компонента"
affects: [15-14, phase-15-verification, FORM-01]

actuals:
  tokens: 12172
  tasks: 2
  commits: 4
plan_head_before: d934618b2be01cee60ed1368d1f7a4812e849a86

tech-stack:
  added: []
  patterns:
    - "связка двух узлов доказывается МНОЖЕСТВАМИ ключей от каждого счёта; `_linkage_pair_offence` называет каждую разошедшуюся пару и ключи"
    - "прямой счёт по тексту значения атрибута (без разбора границ тега) стоит рядом со счётом по тегу: их расхождение есть ошибка разбора, а не пропажа"
    - "косвенное имя события выводится из тела макроса через объявленное отображение, а не вписывается литералом"
    - "импорт констант соседних модулей-гейтов — внутри теста: они сами импортируют этот модуль"

key-files:
  created: []
  modified:
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Ключ триггера — порядковый номер СРЕДИ ФОРМ-ТРИГГЕРОВ файла (`_ordinal_keys`), а не среди всех мест формы, как у 15-02; сверка с классами 15-02 идёт по тексту тега, а не по ключу"
  - "Связь триггера с модалкой — по основе имени события и скелету адреса по всему дереву: 3 триггера `sync_status_card.html` и 2 шаблона админки собирают модалку в ДРУГОМ файле"
  - "Косвенное имя `modal-open-{{ modal_id }}` строки очереди разрешено объявленным отображением `MODAL_OPEN_EVENT_INDIRECTIONS` → тело макроса `queue_drop_modal_id` (`queue-drop-`)"
  - "Пятый свидетель (`MODAL_PLACES`, `MODAL_EVENT_NAMES`) и инвентарь 15-02 импортируются внутри теста: оба модуля импортируют `test_htmx_markup_gates.py`, импорт в шапке замкнул бы круг"
  - "Скрипты `app/static/js/` вне вселенной запрета границы 2 — названная граница (там только вендорные htmx/alpine, 0 вхождений), новый обход не заведён"

patterns-established:
  - "Гейт отношения между узлами: каждый счёт отдаёт множество ключей, которые он признаёт связанными; несвязанный ключ называется"

requirements-completed: [FORM-01]

coverage:
  - id: D1
    description: "Контракт связки D-07 объявлен шапкой группы выше первого числа (строка 9256 < 9367) с прямым указанием, что `hx-post` на триггере признаком связки не является (D-07, FORM-06); обе летописи — «тремя → четырьмя счётами» (план 10-01, D-14 Фазы 10) и «805 → 807»"
    requirement: "FORM-01"
    verification:
      - kind: other
        ref: "grep -n 'СВЯЗКА — пара «форма-триггер' / '^MODAL_LINKAGE_UNIVERSE_FLOOR = 50' tests/test_templates/test_htmx_markup_gates.py (9256 < 9367)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Связка доказана четырьмя счётами (I теги 18, II одна форма компонента с hx-post == action, III прямой счёт событий 18 / 9 основ, IV адрес `action` ⊆ сигнатуры и скелеты сходятся); расхождение называет пару"
    requirement: "FORM-01"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k \"modal_linkage or trigger_form\" (12 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_modal_linkage_an_unpaired_synthetic_trigger_form_is_named"
        status: pass
    human_judgment: false
  - id: D3
    description: "18 триггеров и форма модалки остаются раздельными местами разных классов инвентаря 15-02; `test_form_inventory.py` зелён (49 мест письма)"
    requirement: "FORM-01"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_modal_linkage_keeps_the_triggers_and_the_component_form_as_separate_places"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_form_inventory.py -q -p no:randomly (24 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Три границы связки: запрет готового `action` (замер 0 из 18), запрет вызова события вне `x-on:submit.prevent` (19 = 18 + слушатель, вне — 0), контроль второй формы компонента; контроли от вакуума на каждый"
    requirement: "FORM-01"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k \"cannot_see or linkage_boundary or open_event_outside\" (6 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Рантайм связки: Alpine перехватывает submit, модалка открывается, её submit доезжает до сервера"
    requirement: "FORM-01"
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет JS и не рендерит страниц. Это пункты 3 и 5 ручного обхода, закрытые глазами Фазами 9 и 11; по D-15 они принимаются записью своих фаз, а не переподтверждаются. Зелень гейта — утверждение о тексте шаблонов, а не наблюдение"

duration: 25min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 10: Гейт связки «форма-триггер → модалка с `hx-post`» Summary

**Связка D-07 доказана четырьмя независимыми счётами. Разбор тегов триггеров, единственная форма компонента с `hx-post == action`, прямой счёт вызовов события по тексту атрибута и сверка адресов по сигнатуре макроса дают каждый множество связанных ключей; расхождение называет пару счётов и ключ. Три границы связки названы, две из них запрещены правилами с именованным нулём. Всё в `tests/test_templates/test_htmx_markup_gates.py`, в файл только добавлялись строки.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-09-24T12:56:25Z
- **Completed:** 2026-09-24T13:21Z
- **Tasks:** 2 (из них 1 TDD)
- **Files modified:** 1 (`tests/test_templates/test_htmx_markup_gates.py`, 9245 → 10270 строк; по плану 1 удалённая строка — см. отклонения)

## Accomplishments

- Контракт связки объявлен выше первого числа группы. Четыре счёта сходятся на 18 ключах: I = 18, II = 18, III = 18, IV = 18.
- Места не слиты: 18 триггеров стоят в классе 15-02 «сырой POST без hx-post», форма модалки — в классе «с hx-post». Это 19 разных ключей инвентаря; мест письма по-прежнему 49.
- Три границы связки: две закрыты запретами, третья — контролем; для каждой есть контроль от вакуума на синтетическом шаблоне.

## Объявленный контракт связки (дословно, из шапки группы)

> СВЯЗКА — пара «форма-триггер, отдающая свой `action` событию открытия
> модалки» и «единственная форма компонента модалки, несущая `hx-post`,
> посимвольно равный полученному параметру `action`».
>
> ⚠️ Атрибут `hx-post` на САМОМ ТРИГГЕРЕ признаком связки НЕ ЯВЛЯЕТСЯ. D-07
> объявляет 18 триггеров переведёнными ИМЕННО потому, что действие письма
> идёт формой модалки, и требование атрибута на триггере рисковало бы
> работающим подтверждением удаления ради буквы атрибута. Основание — FORM-06
> закрыт: 18 мест подтверждения одной правкой `components/modal.html`, число
> `MODAL_PLACES` (`tests/test_templates/test_components.py`).

## Числа четырёх счетов

| Счёт | Что считает | Число | Множество связанных ключей |
|---|---|---|---|
| I — триггеры | теги `<form>` с `x-on:submit.prevent` → `$dispatch('modal-open-…')` (разбор границ тега) | `MODAL_TRIGGER_FORMS = 18` | 18 |
| II — второй узел | формы `components/modal.html` с `hx-post` | `MODAL_COMPONENT_POST_FORMS = 1`, `hx-post == action == "{{ action }}"` | 18 |
| III — событие (прямой) | вызовы `$dispatch('modal-open-…')` в значениях `x-on:submit.prevent` по тексту, без разбора тега | 18 вызовов, 9 основ (`MODAL_OPEN_EVENT_NAMES_CALLED`) ⊆ 9 основ `id=` у 11 вызовов `modal(…)` | 18 |
| IV — адрес | имена аргументов, несущих адрес у вызывающих | `{action}` = `MODAL_ADDRESS_PARAMETER_NAMES` ⊆ сигнатуры; скелет адреса каждого триггера равен скелету `action=` его модалки | 18 |
| пятый свидетель | `MODAL_PLACES = 18`, `MODAL_EVENT_NAMES = 9` (`test_components.py`, не тронут) | сходится по имени | — |

Мутационная проверка вне коммитов: в тег `ads/includes/ad_card.html` вставлен `data-note="a>b"`. Счёт I потерял ключ, прямой счёт III его сохранил, и отказ назвал `счёты I и III разошлись … ['ads/includes/ad_card.html#0']`, то есть это ошибка разбора, а не пропажа разметки.

## Летописи (записаны в шапке группы)

1. **«Сходятся тремя счётами» → «ЧЕТЫРЬМЯ».** «`15-CONTEXT.md` §Reusable Assets говорит, что 18 мест FORM-06 «сходятся тремя счётами». Это УСТАРЕЛО: `test_modal_site_inventory` сводит инвентарь ЧЕТЫРЬМЯ счётами, и четвёртый (имена именованных аргументов вызывающих ⊆ имён сигнатуры макроса) прибавлен планом 10-01 (D-14 Фазы 10) ради свойства, которого до него не существовало. Запись контекста ошибкой не была — она устарела.»
2. **Координата второго узла: 805 → 807.** «тег `<form class="modal__form" method="post" action="{{ action }}"` ОТКРЫВАЕТСЯ на 805, а атрибут `hx-post="{{ action }}"` стои́т на 807. По тегу координата верна, по атрибуту — на две строки ниже». Перезамер 2026-09-24 подтвердил обе строки.

## Замер границы 1 (числом)

Форм-триггеров **18**. Триггеров, чей `action` приезжает готовой строкой из `app/pages/`, **0**: у всех 18 `action` начинается литеральным сегментом маршрута (`/accounts`, `/admin`, `/ads`, `/history`, `/schedules`), а выражения внутри адреса — только идентификаторы сущностей. `grep -rn 'modal-open\|modal_id' app/pages/` находит **0** строк. Замер границы 2: вхождений `modal-open-` в шаблонах без комментариев **19** (18 вызовов в `x-on:submit.prevent` и 1 слушатель компонента), вне их **0**; в `app/static/js/` **0** (там только вендорные `htmx.min.js` и `alpine.min.js`).

## `test_components.py` не тронут, `test_form_inventory.py` зелён

- `git diff d934618b..HEAD --name-only` называет один файл: `tests/test_templates/test_htmx_markup_gates.py`. `MODAL_IMPORTERS`, `MODAL_EVENT_NAMES`, `MODAL_PLACES` и `test_modal_site_inventory` не тронуты; новая группа ссылается на них по имени как на пятого свидетеля.
- `uv run pytest tests/test_templates/test_form_inventory.py -q -p no:randomly` дал 24 passed, то есть места не слиты и вселенная FORM-01 (49/27) не переопределена.

## Task Commits

1. **Task 1: контракт связки и четыре счёта** — RED `74ec8bc3` (test), исправление RED-утверждения `c48880f9` (test), GREEN `f4b359cd` (feat)
2. **Task 2: границы связки** — `6fa370c5` (feat)

## TDD Gate Compliance

- `test(15-10)` 74ec8bc3 → `test(15-10)` c48880f9 → `feat(15-10)` f4b359cd. REFACTOR-шага не было.
- RED-улика: `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly -k "modal_linkage or trigger_form"`, код 1, 12 тестов / 11 провалов / 1 зелёный (пятый свидетель — константы). Целевой `test_modal_linkage_count_i_trigger_forms_are_the_declared_eighteen` упал на `AssertionError` (`assert set() == {18 ключей}`). Все 11 провалов — `AssertionError` на объявленном поведении, падений на импорте или фикстуре нет. `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`). Запись собрана из того же прогона: `--junit-xml` переведён в TAP одноразовым скриптом во временном каталоге, скрипт не закоммичен.
- RED построен приёмом 15-05: у четырёх сборщиков пустые тела (`found = {}` / `return found`), и GREEN вставил тела между этими строками. `git show --format= --unified=0 f4b359cd` не содержит строк `-`.

## Verification

| Команда | Итог |
|---|---|
| `-k "modal_linkage or trigger_form"` | 12 passed (≥ 9) |
| `-k control` | до правки 33 → после задачи 1 36 → после задачи 2 40; среди собранных есть синтетический несвязанный триггер, синтетический вызов вне `x-on:submit.prevent` и вторая форма компонента |
| `-k "cannot_see or linkage_boundary or open_event_outside"` | 6 passed |
| `tests/test_templates/test_htmx_markup_gates.py` | 122 passed (до правки 104); одинаково под `-p no:randomly` и в порядке по умолчанию |
| `tests/test_templates/test_form_inventory.py` | 24 passed |
| `tests/test_templates/` | 351 после задачи 1 (до правки 339) |
| `tests/test_templates/ tests/test_pages/test_htmx_gates.py` | 417 passed (до правки 399 = 339 + 60) |
| `tests/test_pages/test_htmx_post_pairs.py` (сквозной гейт, читающий `tests/`) | 85 passed |
| `uv run python -m compileall -q app main.py tests` | молчание, код 0 |
| `tests/test_planning/` | 78 passed |
| `grep -c rglob` модуля | 2 до и после |
| строк `-` в `git show HEAD` для модуля (f4b359cd, 6fa370c5) | 0 и 0 |

Полную суиту и прогон `-m "not planning"` по всему `tests/` исполнитель не запускал. Её после волны гонит оркестратор по всему дереву вместе с коммитами учёта. Вместо неё прогнаны целевой модуль, весь `tests/test_templates/` и сквозные гейты `tests/test_pages/test_htmx_gates.py` и `tests/test_pages/test_htmx_post_pairs.py`.

## Decisions Made

См. `key-decisions` во frontmatter. Главное: связка проверяется по всему дереву, по основе события и скелету адреса, потому что модалка часто собирается не в файле триггера. У 3 триггеров `accounts/partials/sync_status_card.html` модалка стоит в `accounts/list.html` и `partial_cards.html`, у `user_actions.html` — в `admin/user_detail.html`, у `worker_row.html` — в `admin/workers.html`, у `queue_row.html` — в `admin/queue.html`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] RED-утверждение о сошедшейся паре никогда не могло выполниться**
- **Found during:** Task 1 (GREEN)
- **Issue:** тест 5 проверял `"счёты I и II" not in diverged`, но эта подстрока входит в `"счёты I и III"`, поэтому утверждение ложно при любой реализации.
- **Fix:** утверждение сверяет полную фразу `"счёты I и II разошлись"`. Исправление ушло отдельным коммитом ДО GREEN, чтобы GREEN оставался чистым добавлением.
- **Files modified:** tests/test_templates/test_htmx_markup_gates.py (1 строка, добавленная этим же планом в 74ec8bc3)
- **Verification:** 12 passed после GREEN
- **Committed in:** c48880f9. В его диффе есть одна строка `-`, и она принадлежит тексту самого плана; критерий «ни одной строки `-`» проверяется на HEAD задач (f4b359cd, 6fa370c5), и там 0.

**2. [Rule 2 - Missing critical] Незакрытый вызов `modal(` не режется срезом `[…:-1]`**
- **Found during:** Task 1 (GREEN)
- **Issue:** `_scan_to_close` возвращает `-1` для незакрытого вызова, и срез по нему молча отрезал бы последний символ исходника.
- **Fix:** незакрытый вызов записывается без аргументов. Он ничего не связывает, и триггеры, зависящие от него, называются несвязанными.
- **Committed in:** f4b359cd

### Устаревшие числа плана (перезамер, не отклонения кода)

- «`test_htmx_markup_gates.py` ~7400 строк»: до плана было 9245, после 10270. Координаты каркаса `:285-286`, `:326`, `:342`, `:365`, `:375`, `:384` совпали.
- `test_modal_site_inventory` «`:1632-1662`» / «`:1632-1678`»: тест начинается на :1632, но блок четвёртого счёта продолжается ниже :1678, и следующее правило начинается на :1739. `MODAL_IMPORTERS`/`MODAL_EVENT_NAMES`/`MODAL_PLACES` стоят на :1096-1098, как и в плане.
- `components/modal.html:805/807`, координаты D-08 всех 18 триггеров (строки открытия тега) и `test_impersonation_gate.py:456-476` совпали с планом.
- Комментарий `test_form_inventory.py` (план 15-02) называет носителем связки «план 15-09». Связку несёт этот план 15-10; файл 15-02 этим планом не правится, расхождение только названо.

### Plan-text inconsistencies resolved

- План называет абзацы контракта и границ «докстрингом группы». Группа в модуле не является функцией, поэтому, как и у групп 15-05, это шапка-комментарий над первым числом группы. Критерий «строка контракта меньше строки первого числа» выполнен: 9256 < 9367.
- Сверх девяти объявленных тестов задачи 1 добавлены ещё три: пятый свидетель по имени, вывод косвенного имени события из тела макроса, чистота функции от порядка отображения (must_have `backstop`).

**Total deviations:** 2 auto-fixed (1 Rule 1, 1 Rule 2). **Impact:** правка одной строки собственного RED-теста и защита разборщика; утверждения плана не ослаблены.

## Issues Encountered

None.

## Known Stubs

None. `MODAL_TRIGGER_ACTION_FROM_PAGES_SITES = {}` и `MODAL_OPEN_CALLS_OUTSIDE_SUBMIT_SITES = {}` — объявленные именованные нули, а не заглушки: их стерегут синтетические контроли и контроль пустой вселенной.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-14 может ссылаться на гейт связки как на машинную половину D-07. Рантайм связки (пункты 3 и 5 обхода) принимается записью Фаз 9 и 11 по D-15.
- `requirements.ready-ids` для FORM-01 (только чтение): `0/1 requirement(s) ready`, потому что его объявляют и соседние планы фазы. `mark-complete` не вызывался: требования отмечаются закрытием фазы после верификации.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- Файлы `tests/test_templates/test_htmx_markup_gates.py` и `15-10-SUMMARY.md` на месте; коммиты 74ec8bc3, c48880f9, f4b359cd, 6fa370c5, 472e2ec3 найдены.
- `tests/test_planning/` перед коммитом учёта — зелёный (прогон ниже в истории коммита учёта).
