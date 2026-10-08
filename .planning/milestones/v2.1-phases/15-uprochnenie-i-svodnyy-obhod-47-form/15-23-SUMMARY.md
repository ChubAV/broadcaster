---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 23
subsystem: schedules-editor
tags: [schedules, timezone, cr-01, ui-review, sched_card, jinja-global, tdd, ast]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-08: откат нераспознанной зоны в `schedules_update` на проверенное значение (CR-01) и группа правил `malformed_stored`; план 15-16: вторая линия отказа правки и создания; план 15-21: снятие `page_size` из контекстов редактора"
provides:
  - "`app/services/schedule_rules.py::profile_timezone_or_utc` — одно место решения «зона профиля, если она в перечне, иначе UTC»; его зовут `schedules_create`, `schedules_update` и `_editor_context`"
  - "глобал шаблонизатора `VALID_TIMEZONES` (замороженная копия константы) в `app/pages/common.py`"
  - "ключ контекста редактора `fallback_timezone`; параметр `fallback_timezone` у макросов `sched_card` / `sched_card_article` без умолчания, передан во всех трёх вызовах"
  - "строка подсказки «Часовой пояс «…» не распознан — при сохранении расписание перейдёт на …» под нетронутой подписью «Время по …», класс `sched-card__hint`"
  - "`PAIRED_302_ASSERTIONS_DECLARED` 190 → 191 с летописью"
affects: [15-24, 15-33, phase-15-verification, 15-UAT, schedules-editor]

actuals:
  tokens: 7767
  tasks: 2
  commits: 4
plan_head_before: 70e36da60a91e084cd92a6d62919c59fcc822f00

tech-stack:
  added: []
  patterns:
    - "решение, которое печатается человеку ДО действия и исполняется обработчиком ПРИ действии, живёт в одном чистом помощнике сервиса; шаблон получает его результат через контекст, а не считает сам"
    - "параметр макроса без умолчания принуждается правилом по исходникам ВСЕХ шаблонов: Jinja подставляет пустое значение на пропущенном параметре молча"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-23-SUMMARY.md
  modified:
    - app/services/schedule_rules.py
    - app/pages/schedules.py
    - app/pages/ads.py
    - app/pages/common.py
    - app/templates/ads/includes/sched_card.html
    - app/templates/ads/form.html
    - app/templates/ads/partials/sched_card_response.html
    - app/templates/ads/partials/sched_create_response.html
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_post_pairs.py

key-decisions:
  - "15-23: зона подсказки карточки едет ключом `fallback_timezone` контекста редактора (`_editor_context` зовёт `profile_timezone_or_utc`), а не отдельным вычислением в каждом обработчике: оба пути отрисовки карточки (страница `ads/form.html` и фрагменты `app/pages/schedules.py`) уже строят карточку из этого контекста"
  - "15-23: подсказка стоит в развёрнутом теле карточки под подписью «Время по …» — там же, где кнопка сохранения; класс `sched-card__hint` (действующая предупреждающая подпись карточки, `color: var(--warn)`), новых CSS-правил нет"
  - "15-23: третий вызов макроса (`ads/partials/sched_create_response.html`) тоже передаёт `fallback_timezone` — параметр без умолчания, и правило по исходникам требует его в каждом вызове"
  - "15-23: `PAIRED_302_ASSERTIONS_DECLARED` 190 → 191 поставлено прогоном покрасневшего правила — одно новое утверждение 302 о давно переведённой правке расписания (исход сохранения не сдвинулся)"

patterns-established:
  - "Правило «каждый вызов макроса передаёт параметр» пишется по исходникам всех шаблонов с антивакуумом (вызовы найдены на обоих путях, названных планом)"

requirements-completed: ["долг-D-18"]

coverage:
  - id: D1
    description: "Один помощник `profile_timezone_or_utc`: зона профиля при верной зоне, UTC при нераспознанной и при отсутствии; `schedules_create` и `schedules_update` зовут его и своих выражений `… in VALID_TIMEZONES else \"UTC\"` не держат"
    requirement: "долг-D-18"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_profile_timezone_or_utc_answers_the_profile_zone_or_utc"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_profile_timezone_is_decided_by_one_helper_in_create_and_update"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_control_profile_timezone_literal_expression_is_found_in_a_synthetic_source"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k malformed_stored"
        status: pass
    human_judgment: false
  - id: D2
    description: "Карточка с нераспознанной сохранённой зоной показывает подсказку до сохранения на обоих путях отрисовки (страница редактора и фрагмент карточки), называет зону профиля или UTC; зона экранирована"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_unrecognised_zone_hint_on_the_editor_page_names_the_fallback_zone"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_unrecognised_zone_hint_on_the_card_fragment"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_unrecognised_zone_hint_escapes_the_stored_zone"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_every_card_call_passes_the_hint_fallback_zone"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_hint_fallback_zone_comes_from_the_same_helper_as_the_save"
        status: pass
    human_judgment: false
  - id: D3
    description: "Карточка с верной зоной подсказки не несёт; подпись «Время по …» на месте на обоих путях; после сохранения подсказки нет, уведомления нет, в строке зона профиля"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_recognised_zone_card_carries_no_hint_on_either_path"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_unrecognised_zone_hint_is_gone_after_the_save_and_no_notice_is_shown"
        status: pass
    human_judgment: false
  - id: D4
    description: "Человек читает подсказку как предупреждение о смене пояса и понимает, что сделает сохранение (формулировка и заметность на живой карточке)"
    verification: []
    human_judgment: true
    rationale: "Правила утверждают наличие и текст строки, но не то, что человек её замечает и понимает до нажатия «СОХРАНИТЬ РАСПИСАНИЕ» — это вопрос обхода `15-UAT.md`; машинная улика не есть приёмка"

duration: 49min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 23: подсказка о нераспознанной зоне на карточке расписания до сохранения Summary

**Карточка расписания с нераспознанной сохранённой зоной теперь до сохранения говорит «Часовой пояс «Mars/Phobos» не распознан — при сохранении расписание перейдёт на Europe/Moscow», и эту зону вычисляет тот же помощник `profile_timezone_or_utc`, которым сохранение её откатывает; плашки успеха и нового кода уведомления нет.**

## Performance

- **Duration:** 49 min
- **Started:** 2026-09-25T11:31:11Z
- **Completed:** 2026-09-25T12:20:17Z
- **Tasks:** 2 (оба `tdd="true"`, RED → GREEN)
- **Files modified:** 10

## Accomplishments

- **Один помощник зоны (задача 1).** `profile_timezone_or_utc(user_timezone)` в `app/services/schedule_rules.py`: чистая функция, без чтения СУБД и без перехвата. Два выражения `user.timezone if user.timezone in VALID_TIMEZONES else "UTC"` в `app/pages/schedules.py` заменены вызовом. В `schedules_create` это место с комментарием «Умолчание — ТАЙМЗОНА ПРОФИЛЯ» (было `:1093`, теперь `:1099`), в `schedules_update` — откат CR-01 (было `:1333`, теперь `:1344`). Комментарии над обоими местами сохранены и дописаны записью плана 15-23. Откат `stored_tz = … else profile_tz` правки не тронут, и исход сохранения не изменился.
- **Подсказка на карточке (задача 2).** В `sched_card.html` под подписью «Время по {{ s.timezone }}» (была `:299`) добавлена условная строка `<p class="sched-card__hint">`. Она появляется при `s.timezone not in VALID_TIMEZONES`. Подпись не переформулирована: `grep -c 'Время по {{ s.timezone }}'` → 1.
- **Пути отрисовки карточки.** Макрос `sched_card_article` / `sched_card` получил параметр `fallback_timezone`, ключевой и без умолчания. Его передают все три вызова, и значение берётся из ключа `fallback_timezone` контекста `_editor_context` (`app/pages/ads.py`):
  1. `ads/form.html` — страница редактора (`GET /ads/{id}/edit`);
  2. `ads/partials/sched_card_response.html` — фрагмент карточки из ответов правки (`schedules_update`) и тумблера (`schedules_toggle`) из `app/pages/schedules.py`;
  3. `ads/partials/sched_create_response.html` — фрагмент создания. План этот путь не называл; на нём зона всегда верная, но без параметра вызов нарушил бы договор макроса.
- **Класс подписи.** Строка использует класс `sched-card__hint` — действующую предупреждающую подпись карточки (`app.css:2480`, `color: var(--warn)`; ту же, что «Заполните группы, дни и время»). Новых CSS-правил нет: `git diff --stat 70e36da6..HEAD -- app/pages/notices.py app/static/css/app.css` пуст.
- **Глобал `VALID_TIMEZONES`.** В `app/pages/common.py` рядом с `AD_STATUS_*` зарегистрирован `frozenset(VALID_TIMEZONES)`, то есть копия константы из `app/constants.py`, которую шаблон изменить не может.

## Task Commits

1. **Задача 1: один помощник зоны профиля** — `3fe4a25a` (test, RED), `5187b807` (feat, GREEN)
2. **Задача 2: подсказка на карточке на обоих путях** — `7202350b` (test, RED), `a74f2651` (feat, GREEN)

**Plan metadata:** коммит `docs(15-23)` со сводкой и трекингом.

## TDD

План имеет `type: execute` при `workflow.tdd_mode: true`, а на таком плане гейт TDD инертен. Поэтому здесь явно названо, какая задача добавляет поведение и где её RED. **Поведение добавляют обе задачи.** Каждая прошла RED → GREEN отдельными коммитами: `test(15-23)` → `feat(15-23)`.

- **Задача 1, RED `3fe4a25a`.** Цель — `test_profile_timezone_is_decided_by_one_helper_in_create_and_update`: `FAILED …::test_profile_timezone_is_decided_by_one_helper_in_create_and_update`, последняя строка `1 failed`. Причинный литерал: `AssertionError: schedules_create решает зону профиля своим выражением на строках [1093] — решение обязано жить в profile_timezone_or_utc`. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`); запись получена через `--junit-xml`, перегнанный в node:test TAP одноразовым скриптом в scratchpad (скрипт не закоммичен). Соседние правила помощника упали на `assert helper is not None` — это утверждение, а не обрыв сборки.
- **Задача 2, RED `7202350b`.** Цель — `test_unrecognised_zone_hint_on_the_editor_page_names_the_fallback_zone[valid-profile-zone]`: `FAILED …`, `1 failed`. Причинный литерал: `AssertionError: профиль 'Europe/Moscow': на карточке нет подсказки о переходе на Europe/Moscow`. Верб вернул `RED_EVIDENCE_OK`. Остальные четыре новых правила тоже упали на своих утверждениях. Два охранных правила (карточка с верной зоной и карточка после сохранения) были зелены до GREEN, как и положено: они закрепляют то, что уже верно.
- Коммитов REFACTOR нет.

## Files Created/Modified

- `app/services/schedule_rules.py` — ввоз `VALID_TIMEZONES`, функция `profile_timezone_or_utc` с докстрингом (единственное место решения и три его потребителя).
- `app/pages/schedules.py` — ввоз помощника; два вызова вместо выражений; комментарии дополнены.
- `app/pages/ads.py` — ввоз помощника; ключ `fallback_timezone` в `_editor_context`.
- `app/pages/common.py` — глобал `VALID_TIMEZONES`.
- `app/templates/ads/includes/sched_card.html` — параметр `fallback_timezone` у обоих макросов и строка подсказки с комментарием.
- `app/templates/ads/form.html`, `ads/partials/sched_card_response.html`, `ads/partials/sched_create_response.html` — передают `fallback_timezone=editor.fallback_timezone`.
- `tests/test_pages/test_editor_schedules.py` — 3 правила задачи 1 (5 случаев) и 7 правил задачи 2 (8 случаев) рядом с группой `malformed_stored`.
- `tests/test_pages/test_htmx_post_pairs.py` — `PAIRED_302_ASSERTIONS_DECLARED` 190 → 191 с летописью.

## Decisions Made

- Зона подсказки передаётся через контекст редактора, и отдельных вычислений в обработчиках нет. Все пять мест, которые рисуют карточку (обработчик страницы, три фрагмента `app/pages/schedules.py` и фрагмент создания), строят её из `_editor_context`. Одно вычисление в нём держит подсказку и сохранение на одном помощнике (T-15-88), а правило `test_hint_fallback_zone_comes_from_the_same_helper_as_the_save` это проверяет по дереву.
- Подсказка стоит только в развёрнутом теле. Кнопка «СОХРАНИТЬ РАСПИСАНИЕ» есть только там, поэтому строка видна ровно тогда, когда сохранение возможно. В свёрнутой карточке строки нет.
- Четыре выражения `tz_name = … else "UTC"` в `app/pages/schedules.py` (списки и строка списка после тумблера) не вынесены. Они выбирают зону ПОКАЗА времени, а не зону сохраняемой строки, и план выносит ровно два выражения сохранения. Граница записана в комментарии над правилами задачи 1.

## Сверка с инвариантами продукта Фазы 10 (по диффу `70e36da6..HEAD`)

Выполнено `uv run python scripts/prohibitions_census.py --list --phase 10 --class product-invariant`. Добавленные строки `app/` проверены грепом `compute_next_run_at|except Exception|notice=|notices\.|\|safe|NOTICE`: совпадений нет.

- `10-01#3`, `10-24#2`, `10-31#1` (новых кодов уведомления нет): `app/pages/notices.py` не тронут; ответ сохранения по-прежнему идёт без `notice` — это утверждает правило `…_is_gone_after_the_save_and_no_notice_is_shown`.
- `10-01#6` (тексты и подписи карточки переносятся дословно): подпись «Время по {{ s.timezone }}» на месте. Строка добавлена, ничего не заменено. Удалённые строки диффа — только два выражения и три сигнатуры и вызова макросов.
- `10-55#0` (`compute_next_run_at` не правится): вычислитель не тронут и не вызывается.
- `10-55#4` (перечень не расширяется до `except Exception`): помощник чистый. Гейт `tests/test_services/test_schedule_rules_gate.py` зелен (9 passed).
- `10-09#3` касается параметров макроса ПАНЕЛИ подтверждения (`modal`), а новый параметр добавлен макросу карточки. Панель не тронута.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Третий вызов макроса карточки — `ads/partials/sched_create_response.html`**
- **Found during:** задача 2
- **Issue:** план назвал два пути вызова (`form.html`, `sched_card_response.html`). Нашёлся третий — фрагмент создания. Параметр без умолчания, пропущенный там, Jinja молча заменила бы пустым значением.
- **Fix:** вызов передаёт `fallback_timezone=editor.fallback_timezone`. Правило `test_every_card_call_passes_the_hint_fallback_zone` проверяет все вызовы по исходникам всех шаблонов.
- **Files modified:** `app/templates/ads/partials/sched_create_response.html`
- **Committed in:** `a74f2651`

**2. [Rule 3 - Blocking] Счётный гейт `PAIRED_302_ASSERTIONS_DECLARED` 190 → 191**
- **Found during:** проверка задачи 2 (`test_htmx_post_pairs.py`)
- **Issue:** правило «после сохранения» утверждает `302` о `schedules_update`, и гейт отказал дословно: `утверждений 302 о переведённых обработчиках 191, объявлено 190. Поставьте число ПРОГОНОМ этого отказа`. Правило пар на этом утверждении жалобы не дало.
- **Fix:** число поставлено из замера, над константой добавлена летопись.
- **Files modified:** `tests/test_pages/test_htmx_post_pairs.py`
- **Committed in:** `a74f2651`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Оба исправления нужны для корректности и зелёных гейтов. Поведение сохранения не изменилось, лишней работы нет.

## Issues Encountered

None.

## Verification

- Задача 1: `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_services/ -q -p no:randomly -k "malformed_stored or profile_timezone or schedule_rules"` → `47 passed`. Приёмка: `grep -c 'def profile_timezone_or_utc'` → 1; `grep -c 'profile_timezone_or_utc(' app/pages/schedules.py` → 2. Гейт огульного перехвата → `9 passed`. Модули, ввозящие `schedule_rules` (`tests/test_services/`, `test_schedules_api_create_completeness.py`, `test_schedules_api_value_domain.py`, `test_schedules_out_of_domain_resume.py`), → `457 passed`.
- Задача 2: `-k "hint or unrecognised or malformed_stored"` → `42 passed`. Вторая строка проверки (`test_editor_schedules.py`, `test_ads_editor.py`, `tests/test_templates/`, `test_htmx_gates.py`, `test_htmx_post_pairs.py`, `test_notices_channel.py`) → после установки числа гейта зелена. Первый прогон дал `1 failed, 772 passed`: упал только счётный гейт, см. отклонение 2. Приёмка: `grep -c 'не распознан'` → 1; `grep -c 'Время по {{ s.timezone }}'` → 1; дифф `notices.py` / `app.css` пуст.
- Гейты оркестратора и все модули, ввозящие `app.pages.common` (`test_htmx_post_pairs`, `test_hx_location_destinations`, `test_htmx_preserved`, `test_responsive_markup`, `test_admin`, `test_admin_panel`, `test_ads_image_upload`, `test_asset_version`, `test_billing_section`, `test_confirm_delete_transport`, `test_filter_chips`, `test_history_retry`, `test_impersonation`, `test_origin_guard_on_destructive_routes`, `test_shell`, `test_account_groups`, пять модулей `test_schedule*`), → `1168 passed`. `HX_LOCATION_DESTINATION_CALLS_DECLARED` (81) и `DEGRADATION_PAIRS_DECLARED` (5) не сдвинулись.
- Проверка плана `tests/test_pages/ tests/test_templates/ tests/test_services/`: каталог `tests/test_pages/` прогнан целиком в три последовательных захода (оставшиеся 32 модуля → `546 passed`), `tests/test_templates/` — во второй строке задачи 2, `tests/test_services/` — в задаче 1 (после неё сервис не менялся). Ноль `failed`.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed`.
- `graphify update .` выполнен после правок кода.
- Новый `import yaml` не заведён.
- **Подмена полного прогона названа:** полную суиту (`just test`, ~40 мин) по указанию оркестратора запускает сам оркестратор после волны 7. Здесь её заменяют прогоны выше. Окно в WINDOWS.md для этого не открыто.
- `15-UAT.md` не правился: машинная улика — не приёмка, отметки и результат ставит человек.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Волна 7 исполнена (15-22, 15-23). Дальше — полный прогон суиты оркестратором и план 15-24.
- Пункт 4 UI-ревью исполнен без плашки успеха и без нового кода уведомления. Понятна ли формулировка человеку на живой карточке, решит обход (`D4`, `human_judgment: true`).
- Требование `долг-D-18` в REQUIREMENTS.md не отмечалось.

## Self-Check: PASSED
