---
phase: 02-obyavleniya-i-raspisaniya
plan: 09
subsystem: api
tags: [fastapi, sqlalchemy, authorization, idor, jinja2, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-02
    provides: "проверка владения `ad_id` и `account_id` на обоих входах постановки расписания"
  - phase: 02-05
    provides: "секция расписаний внутри редактора объявления, `_editor_context`"
  - phase: 02-08
    provides: "контракт автосохранения редактора, INACCESSIBLE_AD_MESSAGE, форма отказа по данным"
provides:
  - "app/services/schedule_rules.py — нейтральный модуль правил расписания, от которого зависят ОБА слоя"
  - "is_schedule_complete — единственное определение полноты расписания в проекте"
  - "owned_group_ids — сведение идентификаторов групп к принадлежащим владельцу И выбранному аккаунту"
  - "Отказ 404 на чужой group_id на create и update JSON-API расписаний"
  - "sched_error — признак отказа в строке запроса редактора и серверный текст под него"
  - "_ownership_verdict — трёхзначный исход проверки владения вместо булева"
affects: [02-10, 02-11, 02-12, 02-VERIFICATION, 02-REVIEW, schedules, ads-editor]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 19297
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Правило, нужное двум слоям, живёт в НЕЙТРАЛЬНОМ модуле: оба зависят от него, он — ни от одного из них"
    - "Проверка владения на частичном обновлении применяется ровно тогда, когда ключ ПРИСУТСТВУЕТ в `model_dump(exclude_unset=True)`"
    - "Отказ по данным различает «запись подтверждена своей» и «доверять нечему»: первый объясняется на месте, второй остаётся неразличимым с «нет такой записи»"
    - "Признак в строке запроса ВЫБИРАЕТ серверный текст, а не является им"

key-files:
  created:
    - app/services/schedule_rules.py
    - tests/test_routes/test_schedules_api_ownership.py
  modified:
    - app/routes/schedules.py
    - app/pages/schedules.py
    - app/pages/ads.py
    - app/templates/ads/form.html
    - tests/test_routes/test_schedules.py
    - tests/test_routes/test_schedules_toggle_detached.py
    - tests/test_pages/test_schedule_ownership.py
    - tests/test_pages/test_schedules_detached_account.py
    - tests/test_application/test_account_deletion_schedules.py

key-decisions:
  - "Отказ на чужой `group_id` оформлен кодом 404 с текстом `Group not found` — тем же, что у несуществующей группы: разные тексты подтверждали бы существование чужой строки перебором идентификаторов (T-02G-07)"
  - "Проверка на update выполняется только при ПРИСУТСТВИИ ключа `group_ids` в патче: отказ на отсутствующем ключе превратил бы частичное обновление в обязательную передачу всего состава групп"
  - "Правило issue #35 ПОГЛОЩЕНО определением полноты, а не оставлено рядом: `is_schedule_complete` требует непустой `account_id`, и два сообщения об одном отказе разъехались бы так же, как разъехались два определения полноты"
  - "`_owns_ad_and_account` заменена на `_ownership_verdict` с тремя исходами вместо булева: различие нужно не проверке, а ОТВЕТУ — она в обоих случаях запрещает запись"
  - "Признак `sched_error` в строке запроса выбирает СЕРВЕРНЫЙ текст, а не является им: приняв значение текстом, страница печатала бы произвольное сообщение от имени приложения по одной лишь ссылке с чужого сайта"
  - "Отказ по ОТСУТСТВИЮ записи расписания тоже возвращает в редактор, когда объявление подтверждено своим: тот же ответ приходит и на несуществующий идентификатор, и на чужой, поэтому о чужих записях это не сообщает ничего"
  - "Тесты переведены на РЕАЛЬНЫЕ группы правкой ДАННЫХ, не ожиданий: ни один assert не ослаблен и не удалён"

patterns-established:
  - "Красная фаза проверяется прогоном, СУЖЁННЫМ по именам (`-k`): код возврата конвейера `pytest | grep` принадлежит grep и «проходит» на любом падении"
  - "Тесты-стражи, зелёные уже на текущем коде, в сужение красной фазы не входят и перечисляются отдельно"
  - "Данные теста, от которых зависит смысл проверки, закрепляются собственным утверждением: группа перепривязки несёт `account_id` того аккаунта, чей идентификатор ушёл в то же тело"

requirements-completed: [ADS-07, ADS-08, SCH-05]

coverage:
  - id: D1
    description: "Чужой идентификатор группы отклоняется на СОЗДАНИИ расписания через JSON-API: строка `schedules` не появляется (CR-02, T-02G-06)"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_create_rejects_a_group_id_of_another_user"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_create_rejects_a_group_id_of_another_account_of_the_same_user"
        status: pass
    human_judgment: false
  - id: D2
    description: "Чужой идентификатор группы отклоняется на ОБНОВЛЕНИИ: `group_ids` в базе не меняются (T-02G-06)"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_update_rejects_swapping_in_a_foreign_group_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "Отсутствующий в патче ключ `group_ids` означает «не трогать»: частичное обновление не требует передавать весь состав групп"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_update_without_group_ids_leaves_them_untouched"
        status: pass
    human_judgment: false
  - id: D4
    description: "Определение полноты одно на оба входа: неполное расписание не включается ни страничным тумблером, ни JSON-API (WR-05, D-08, T-02G-08)"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_api_toggle_refuses_to_enable_an_incomplete_schedule"
        status: pass
      - kind: static
        ref: "grep -v '^#' app/pages/schedules.py | grep -c 'def _is_complete' == 0"
        status: pass
    human_judgment: false
  - id: D5
    description: "Право поставить на паузу не зависит от заполненности; два переключения возвращают расписание в исходное состояние, потому что `is_active` вычисляется от значения в базе"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_api_toggle_pausing_an_active_schedule_is_never_blocked"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_double_toggle_returns_to_the_initial_state"
        status: pass
    human_judgment: false
  - id: D6
    description: "Приостановленное расписание после PUT не несёт времени ближайшего запуска: сводка редактора не рекламирует отправку, которой не будет (WR-06, T-02G-09)"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_paused_schedule_does_not_carry_a_future_next_run"
        status: pass
    human_judgment: false
  - id: D7
    description: "Повторный одинаковый PUT оставляет то же число строк, то же `is_active`, то же `next_run_at` и тот же состав групп"
    requirement: "SCH-05"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_api_ownership.py#test_repeated_update_is_idempotent"
        status: pass
    human_judgment: false
  - id: D8
    description: "Отказ по данным при ПОДТВЕРЖДЁННО своём объявлении возвращает в редактор с объяснением, а не уводит на сводный список молча (WR-07, T-02G-11)"
    requirement: "ADS-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_create_rejects_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_update_rejects_swapping_in_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_path_rejects_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_update_of_a_missing_schedule_returns_to_the_own_editor"
        status: pass
    human_judgment: false
  - id: D9
    description: "Отказ по ЧУЖОМУ объявлению остаётся неразличимым с «нет такой записи»: прежний редирект на /schedules без признака ошибки"
    requirement: "ADS-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_create_rejects_foreign_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_update_of_a_foreign_schedule_with_a_foreign_ad_stays_silent"
        status: pass
    human_judgment: false
  - id: D10
    description: "Формулировка контракта UI-SPEC (E4 `error`) видна в секции расписаний — ПОСЛЕ закрытия элемента `<form id=\"ad-form\">`, без вложенной формы и без нового элемента формы"
    requirement: "ADS-08"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_shows_the_refusal_message_in_the_schedules_section"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_schedule_section_is_a_sibling_of_the_ad_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_markup_has_no_nested_forms"
        status: pass
    human_judgment: false
  - id: D11
    description: "Значение признака отказа в разметку не попадает: неизвестный признак не рисует сообщения и страницу не роняет"
    requirement: "ADS-08"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_never_prints_the_query_value_itself"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_without_the_flag_shows_no_refusal_message"
        status: pass
    human_judgment: false
  - id: D12
    description: "Кнопка подтверждения удаления расписания отражает состояние выполняющегося запроса и не отправляется дважды"
    verification: []
    human_judgment: true
    rationale: "Must-have плана помечен `verification: backstop`. Суита рендерит разметку, но не исполняет htmx и не воспроизводит двойной клик; проверяемо только в браузере."

# Metrics
duration: 36min
completed: 2026-08-11
status: complete
---

# Phase 02 Plan 09: Владение группами на JSON-входе и одно определение полноты Summary

**Межарендная дыра `group_ids` закрыта на обоих входах JSON-API, а три разошедшихся правила — полнота расписания, пересчёт ближайшего запуска и форма отказа по данным — сведены к одному определению каждое**

## Performance

- **Duration:** ~36 min
- **Started:** 2026-08-11T05:47:00Z
- **Completed:** 2026-08-11T06:23:00Z
- **Tasks:** 3
- **Files created:** 2
- **Files modified:** 9

## Accomplishments

- **T-02G-06 (critical, нарушение авторизации на уровне объекта) закрыт.** `create_schedule` писал `group_ids` дословно, `update_schedule` присваивал их слепо. Ниже по потоку владельца не перепроверял никто: `collect_due_schedules` итерирует `schedule.group_ids` как есть, `send_message_once` резолвит группу по первичному ключу. Теперь `owned_group_ids` сводит присланные идентификаторы к `Group.user_id == user_id AND Group.account_id == account_id` ДО расчёта следующего запуска и ДО записи; несведённый остаток даёт 404.
- **Правило владения группами перестало существовать в двух экземплярах.** Страничный слой применял его через `_groups_of_account` + фильтрацию, JSON-API — не применял вовсе. Обе половины теперь берут его из `app/services/schedule_rules.py`.
- **Определение полноты стало ЕДИНСТВЕННЫМ (WR-05, D-08).** `_is_complete` не скопирована, а ПЕРЕНЕСЕНА: `grep -c 'def _is_complete'` по `app/pages/schedules.py` даёт 0, страничный слой связывает прежнее локальное имя с импортом. API-тумблер, смотревший только на `account_id`, теперь отказывает на том же множестве расписаний, что и страничный.
- **Приостановленное расписание больше не рекламирует отправку (WR-06).** `update_schedule` пересчитывал `next_run_at` безусловно — включая расписания, которые пользователь поставил на паузу руками. Пересчёт теперь зеркалит страничное правило.
- **Отказ по данным перестал быть навигацией (WR-07).** При ПОДТВЕРЖДЁННО своём объявлении пользователь возвращается в его редактор с сообщением контракта UI-SPEC; при чужом — прежним неразличимым редиректом.
- **Пять тестовых модулей переведены с выдуманных `group_ids` на реальные строки `groups`.** Тест, создававший расписание с `group_ids: [1, 2, 3]` при полном отсутствии строк `groups` и утверждавший, что значения возвращаются, ЗАКРЕПЛЯЛ дыру (02-REVIEW.md, CR-02). Ни одно утверждение не ослаблено — менялись только данные.

## Task Commits

1. **Task 1 (RED): регрессия межарендной границы и общего определения полноты** — `975748b` (test)
2. **Task 2 (GREEN): нейтральный модуль правил и его применение на обоих входах** — `cbddd4a` (feat)
3. **Task 3: отказ по данным перестаёт быть навигацией, полный прогон суиты** — `7a366bb` (fix)

REFACTOR-коммита нет: перенос `_is_complete` в нейтральный модуль — сама суть GREEN-задачи, чистить после неё было нечего.

## TDD Gate Compliance

| Gate | Commit | Статус |
|---|---|---|
| RED | `975748b` (`test(02-09): …`) | ✓ Пять тестов владения и полноты упали на текущем коде |
| GREEN | `cbddd4a` (`feat(02-09): …`) | ✓ 205 тестов прогона верификации задачи 2 зелёные |
| REFACTOR | — | Не потребовался |

Красная фаза проверена прогоном, СУЖЁННЫМ по именам (`-k`), а не кодом возврата конвейера `pytest | grep`: код возврата конвейера принадлежит `grep` и «проходил» бы на любом падении. Исходы падений — по существу дефекта, ни одного постороннего имени:

| Тест | Исход на текущем коде |
|---|---|
| `test_create_rejects_a_group_id_of_another_user` | `assert 201 == 404` |
| `test_create_rejects_a_group_id_of_another_account_of_the_same_user` | `assert 201 == 404` |
| `test_update_rejects_swapping_in_a_foreign_group_id` | `assert 200 == 404` |
| `test_api_toggle_refuses_to_enable_an_incomplete_schedule` | `assert 200 == 400` |
| `test_paused_schedule_does_not_carry_a_future_next_run` | `assert '2026-08-11T10:00:00' is None` |

Пять тестов-стражей того же модуля (`accepts_own_group_ids`, `without_group_ids_leaves_them_untouched`, `pausing_an_active_schedule`, `double_toggle`, `repeated_update_is_idempotent`) на текущем коде зелены — они не красная фаза и в сужение не входили: **5 passed, 5 deselected**.

Подготовительная правка данных проверена отдельно: `tests/test_routes/test_schedules_toggle_detached.py` — **5 passed** на ТЕКУЩЕМ коде, то есть правка не задела ни одного ожидания; `tests/test_routes/test_schedules.py` — **11 passed** там же.

## Files Created/Modified

- **`app/services/schedule_rules.py` (новый)** — `is_schedule_complete` (перенесена дословно вместе с комментарием про D-08) и `async def owned_group_ids`. Модуль не импортирует ни `app.pages`, ни `app.routes`: направление зависимости закрывает инверсию, которую называет WR-04.
- **`app/routes/schedules.py`** — проверка владения группами в `create_schedule` и в `update_schedule` (на update — только при присутствии ключа в `model_dump(exclude_unset=True)`); трёхветочный пересчёт `next_run_at` вместо безусловного; `toggle_schedule` перешёл на общее определение полноты. Комментарий у проверки фиксирует поглощение правила issue #35.
- **`app/pages/schedules.py`** — `_is_complete` удалена, локальное имя связано с импортом; `_owns_ad_and_account` заменена на `_owns_ad` + `_ownership_verdict` (три исхода); добавлены `_editor_error_redirect`, константы исходов и признаков; `_clean_times` проверяет тип значения до строковых операций (WR-03).
- **`app/pages/ads.py`** — константы `SCHEDULE_ERROR_MESSAGE` (формулировка UI-SPEC E4 `error`) и `SCHEDULE_ERROR_REASONS`; `ads_edit` принимает `sched_error` и кладёт в контекст ТЕКСТ, выбранный признаком.
- **`app/templates/ads/form.html`** — импорт макроса `alert` рядом с `empty_state`; вызов внутри секции расписаний, между `card_open('Расписания')` и `card_close()`. Новой разметки сообщения не написано, нового элемента формы не введено.
- **`tests/test_routes/test_schedules_api_ownership.py` (новый, 10 тестов)** — регрессия межарендной границы и общего определения полноты.
- **Пять существующих тестовых модулей** переведены на реальные группы: `test_schedules.py`, `test_schedules_toggle_detached.py`, `test_schedules_detached_account.py`, `test_account_deletion_schedules.py`, плюс `test_schedule_ownership.py` (разделение ожиданий по двум ситуациям отказа + шесть новых тестов).

## Decisions Made

- **404 и `"Group not found"` — та же форма отказа, что у соседних проверок объявления и аккаунта.** Чужой идентификатор неотличим от несуществующего; иной текст или иной код подтверждали бы существование чужой строки перебором (T-02G-07).
- **Проверка на update — только при присутствии ключа.** `UpdateScheduleRequest` не содержит `account_id`, поэтому группы сверяются с аккаунтом уже сохранённой записи. Отказ на отсутствующем ключе сломал бы частичное обновление, которое `test_update_schedule_timezone` использует с самого начала.
- **Поглощение правила issue #35, а не соседство с ним.** `is_schedule_complete` требует непустой `account_id`, значит отвязанное расписание — частный случай неполного. Оставить рядом второе сообщение означало бы завести второе определение того же отказа — ровно ту ошибку, которую план и устраняет. Регрессия issue #35 проверяет коды ответа, а не тексты, и осталась зелёной без единой правки в задаче 3, как план и предсказывал.
- **Трёхзначный исход проверки владения.** Различие «отказ по аккаунту» / «отказ по объявлению» нужно не проверке, а ответу. Наружу его выпускать безопасно ровно потому, что во втором случае адрес строится из ПОДТВЕРЖДЁННОЙ своей записи, и о чужих записях ответ не сообщает ничего.
- **Признак `sched_error` выбирает текст, а не является им.** Значение приходит строкой запроса и подконтрольно отправителю. Приняв его текстом, страница печатала бы произвольное сообщение от имени приложения по ссылке с чужого сайта — та же причина, по которой `return_to` в этом файле признак, а не адрес (T-02-23).
- **Отказ по ОТСУТСТВИЮ записи тоже возвращает в редактор.** Must-have плана требует, чтобы правки не терялись без объяснения и при отсутствии записи. Утечки нет: несуществующий и чужой идентификаторы дают один и тот же ответ.

## Deviations from Plan

### 1. [Rule 1 — Bug] Ещё два тестовых модуля создавали расписания с выдуманными `group_ids`

- **Найдено при:** Task 3, полный прогон суиты
- **Проблема:** план перечислил `test_schedules.py` и `test_schedules_toggle_detached.py`, но того же класса данные несут `tests/test_pages/test_schedules_detached_account.py` (`_seed_detached_schedule`, `group_ids: [1]`) и `tests/test_application/test_account_deletion_schedules.py` (создание расписания через API с тем же `[1]`). После задачи 2 создание отвечало кодом 404, `.json()["id"]` бросал `KeyError`, и шесть тестов падали.
- **Исправление:** та же правка ДАННЫХ, что в задаче 1 — реальная группа на аккаунте через `POST /api/groups`, её идентификатор в тело. Ни одно ожидание не тронуто: оба модуля проверяют судьбу расписания при удалении аккаунта и видимость отвязанного расписания, и от состава групп это не зависит.
- **Файлы:** `tests/test_pages/test_schedules_detached_account.py`, `tests/test_application/test_account_deletion_schedules.py`
- **Проверка:** оба модуля — 68 passed вместе с `tests/test_messengers/`.
- **Committed in:** `7a366bb`

### 2. [Rule 2 — Missing critical] Возврат в редактор добавлен и для ОТСУТСТВУЮЩЕЙ записи расписания

- **Найдено при:** Task 3
- **Проблема:** текст задачи описывает две ситуации (аккаунт недоступен / объявление чужое), но must-have плана требует шире: «Отказ по владению ИЛИ ПО ОТСУТСТВИЮ ЗАПИСИ не выбрасывает пользователя из редактора молча». Ветка `if not schedule` в `schedules_update` оставалась молчаливым редиректом.
- **Исправление:** при подтверждённо своём `ad_id` из тела — возврат в редактор с `sched_error=missing`; иначе прежний редирект. Различимости чужой записи не появляется: несуществующий и чужой идентификаторы дают один ответ.
- **Файлы:** `app/pages/schedules.py`, `tests/test_pages/test_schedule_ownership.py`
- **Проверка:** `test_update_of_a_missing_schedule_returns_to_the_own_editor`, `test_update_of_a_foreign_schedule_with_a_foreign_ad_stays_silent`.
- **Committed in:** `7a366bb`

### 3. [Rule 2 — Missing critical] Признак отказа проверяется по перечню, а не рендерится как есть

- **Найдено при:** Task 3
- **Проблема:** план говорит «признак прочитать и передать в контекст шаблона». Прочитанный и переданный ДОСЛОВНО, он стал бы текстом сообщения: значение строки запроса подконтрольно отправителю, и ссылка с чужого сайта печатала бы в редакторе произвольное сообщение от имени приложения (фишинг доверенным интерфейсом).
- **Исправление:** признак сверяется с перечнем и ВЫБИРАЕТ серверную константу; неизвестное значение не выбирает ничего и страницу не роняет — образец `_clean_choice` из того же слоя.
- **Файлы:** `app/pages/ads.py`, `tests/test_pages/test_schedule_ownership.py`
- **Проверка:** `test_editor_never_prints_the_query_value_itself`.
- **Committed in:** `7a366bb`

---

**Total deviations:** 3 auto-fixed (1 bug, 2 missing critical)
**Impact on plan:** объём не изменился, ни одна задача не пропущена. Отклонения 2 и 3 закрывают must-have и prohibition плана, которые текст задачи 3 описал уже́, чем сформулировал их frontmatter.

## Issues Encountered

- Четыре «ошибки» в `tests/test_messengers/` при первом полном прогоне оказались артефактом моего собственного флага `-p no:logging`, отключающего фикстуру `caplog`, — не дефектом кода. Повторный прогон без флага: **858 passed, 0 failed**.
- Прогон полной суиты занимает ~9 минут.

## Deferred Issues

`POST /api/groups` (`create_group`) не проверяет владение `account_id`: своя строка `groups` может ссылаться на чужой `messenger_accounts.id`. Сегодня это не дыра — `owned_group_ids` требует совпадения И владельца, И аккаунта, поэтому такая группа не проходит ни на одном входе. Маршрут не входит в `files_modified` плана, поэтому находка вынесена в `.planning/phases/02-obyavleniya-i-raspisaniya/deferred-items.md` (D-02-09-01), а не исправлена здесь.

## Known Stubs

None. Сканирование изменённых файлов на `TODO`/`FIXME`/`placeholder`/`xfail`/`.skip(` дало три совпадения, и все три — не заглушки: слово «заглушка» в прозе давнего комментария `app/pages/schedules.py` и два атрибута `placeholder` у полей ввода в `ads/form.html`. Пропущенных и невыполненных проверок план не оставил.

## Threat Flags

Новой поверхности сверх зарегистрированной в `<threat_model>` плана не появилось. Единственное расширение — параметр строки запроса `sched_error` у `GET /ads/{id}/edit`: он подконтролен отправителю, поэтому в разметку не попадает вовсе и лишь выбирает серверную константу из закрытого перечня (см. отклонение 3). Все шесть зарегистрированных угроз (T-02G-06 … T-02G-11) закрыты и покрыты регрессией; T-02G-SC не применим — пакетов план не устанавливал, `pyproject.toml` и `uv.lock` не изменены.

## User Setup Required

None — внешних сервисов, переменных окружения и миграций схемы этот план не затрагивает.

## Next Phase Readiness

- **Планы 02-10 … 02-12 разблокированы:** правило владения группами и определение полноты лежат в одном месте, и любой новый вход обязан взять их оттуда, а не завести третье.
- **Изменение контракта публичного JSON-API:** запросы `POST /api/schedules` и `PUT /api/schedules/{id}`, ранее принимавшиеся с произвольными `group_ids`, теперь отклоняются кодом 404. Это и есть закрытие дефекта; откат вернул бы межарендную дыру.
- **Открыто для конца фазы:** пункт покрытия `D12` — двойной клик по кнопке подтверждения удаления расписания (must-have с `verification: backstop`), проверяемый только в браузере.
- **Блокеров нет.**

## Self-Check: PASSED

- Файлы на диске: `app/services/schedule_rules.py`, `app/routes/schedules.py`, `app/pages/schedules.py`, `app/pages/ads.py`, `app/templates/ads/form.html`, `tests/test_routes/test_schedules_api_ownership.py`, `.planning/phases/02-obyavleniya-i-raspisaniya/deferred-items.md` — все найдены.
- Коммиты в истории ветки: `975748b`, `cbddd4a`, `7a366bb` — все найдены.
- Удалений отслеживаемых файлов ни в одном коммите плана нет; неотслеживаемых файлов после каждого коммита не оставалось.

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-11*
