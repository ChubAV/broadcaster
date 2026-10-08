---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 16
subsystem: schedules-pages
tags: [schedules, second-line, next_run_or_none, notices, refusal, wr-01, wr-02, in-04, tdd, ast]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-08: `schedules_update` спрашивает `next_run_or_none`, откат зоны на проверенное значение, правила второй линии и перечень `MALFORMED_STORED_FORMS`; план 15-14 — предшественник по `depends_on`"
provides:
  - "одна политика второй линии на трёх страничных входах и в JSON-API: правка и создание ОТКАЗЫВАЮТ, как тумблер, — ничего не записано, переход в редактор объявления с существующим кодом `SCHEDULE_VALUES_OUT_OF_DOMAIN`"
  - "`schedules_update`: `await db.rollback()` + `respond(redirect=/ads/{ad_id}/edit, notice=SCHEDULE_VALUES_OUT_OF_DOMAIN)` вместо молчаливого `is_active = False`"
  - "`schedules_create`: временная модель `Schedule(...)` до решения о моменте, `next_run_or_none`, отказ без `db.add`; прямой вызов вычислителя и его ввоз из модуля сняты"
  - "правило по дереву: ноль вызовов `compute_next_run_at` в `app/pages/schedules.py` (по имени и по атрибуту), `next_run_or_none` у правки и у создания"
  - "`HX_LOCATION_DESTINATION_CALLS_DECLARED` 79 → 81 с летописью"
affects: [15-17, 15-18, 15-19, phase-15-verification, schedules-editor]

actuals:
  tokens: 10717
  tasks: 2
  commits: 4
plan_head_before: 94b59fe05ea64447d6bb3a8b9ba3daecc5c7f576

tech-stack:
  added: []
  patterns:
    - "отказ второй линии правила расписания — один исход на всех входах: ничего не записано, `respond(redirect=/ads/{ad_id}/edit, notice=SCHEDULE_VALUES_OUT_OF_DOMAIN)`"
    - "помощник, читающий модель, спрашивается у ВРЕМЕННОЙ модели, ещё не добавленной в сессию, — второго входа помощника по значениям не заводится"
    - "правило «строка нетронута» сверяет СНИМОК-КОПИЮ посева со строкой после запроса: сессия теста та же, что у обработчика, и объект карты идентичности сравнивался бы сам с собой"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-16-SUMMARY.md
  modified:
    - app/pages/schedules.py
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_hx_location_destinations.py

key-decisions:
  - "15-16: правка из редактора на второй линии ОТКАЗЫВАЕТ, как тумблер и JSON-API: `await db.rollback()`, переход в редактор с `SCHEDULE_VALUES_OUT_OF_DOMAIN`, строка остаётся включённой и целой (WR-01, решение владельца `chubav` Г-2 2026-09-25; вариант «сохранить паузой с уведомлением» отвергнут)"
  - "15-16: создание получает ту же вторую линию — временная модель до решения о моменте, `next_run_or_none`, отказ без `db.add`; ввоз `compute_next_run_at` в `app/pages/schedules.py` снят (WR-02)"
  - "15-16: `HX_LOCATION_DESTINATION_CALLS_DECLARED` 79 → 81 поставлено прогоном покрасневшего правила — два новых выхода без фрагмента (отказ правки и отказ создания); карта назначений не двинулась"

patterns-established:
  - "Правило, закрепившее предсуществующую политику, переписывается с цитатой прежних утверждений рядом (летопись D-30/D-32), а не молча"
  - "Любой новый вызов `respond` без `fragment=` в `app/pages/` двигает `HX_LOCATION_DESTINATION_CALLS_DECLARED` — гейт живёт в `tests/test_pages/test_hx_location_destinations.py`, вне списка проверок плана"

requirements-completed: ["долг-D-18"]

coverage:
  - id: D1
    description: "Правка из редактора на второй линии (все пять неисполнимых форм перечня) отвечает 302 на `/ads/{ad_id}/edit?notice=schedule_values_out_of_domain`, строка в СУБД равна снимку посева (включена, дни, времена, зона, момент); исправная форма `tz-mars-phobos` и законная форма получают момент без кода отказа"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_days_str_form_goes_the_same_way"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_form_on_the_second_line_lands_one_outcome"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_legal_form_on_the_second_line_gets_a_moment"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_form_on_the_second_line_never_answers_500"
        status: pass
    human_judgment: false
  - id: D2
    description: "На транспорте htmx тот же отказ правки — 204 с `HX-Location` на тот же адрес с кодом, тело пусто, строка нетронута"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_days_str_refusal_over_htmx_is_a_location_with_the_notice"
        status: pass
    human_judgment: false
  - id: D3
    description: "Создание на второй линии: 302 на каждой из шести форм; пять неисполнимых — отказ с кодом и ноль новых строк; `tz-mars-phobos` создаётся включённой с моментом"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_create_on_the_second_line_refuses_the_days_str_form_with_the_notice"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_create_on_the_second_line_never_answers_500"
        status: pass
    human_judgment: false
  - id: D4
    description: "Ни один обработчик `app/pages/schedules.py` не зовёт `compute_next_run_at`; правка и создание зовут `next_run_or_none`; проверка владения стоит до отказа"
    requirement: "долг-D-18"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_zone_access_predicate_is_unchanged"
        status: pass
    human_judgment: false
  - id: D5
    description: "Плашка отказа на редакторе после перехода читается человеком как путь восстановления (текст реестра не менялся; уместность формулировки для входа СОЗДАНИЯ — вопрос суждения)"
    verification: []
    human_judgment: true
    rationale: "Текст `SCHEDULE_VALUES_OUT_OF_DOMAIN` писался для тумблера («после этого включение сработает»); что он понятен человеку, чьё СОЗДАНИЕ отвергнуто, ни одно правило не утверждает"

duration: 49min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 16: одна политика отказа второй линии расписания Summary

**Правка из редактора и создание расписания на неисполнимых значениях теперь отказывают, как тумблер и JSON-API: ничего не записано, переход в редактор с существующим кодом `schedule_values_out_of_domain`; ни один страничный обработчик больше не зовёт вычислитель напрямую.**

## Performance

- **Duration:** 49 min
- **Started:** 2026-09-25T05:59:09Z
- **Completed:** 2026-09-25T06:48:52Z
- **Tasks:** 2 (оба `tdd="true"`, RED → GREEN)
- **Files modified:** 3

## Accomplishments

- `schedules_update`: полное включённое расписание без момента (`next_run_or_none` → `None`) → `await db.rollback()` и `respond(request, redirect=f"/ads/{ad_id}/edit", notice=notices.SCHEDULE_VALUES_OUT_OF_DOMAIN)`. Молчаливое `schedule.is_active = False` снято; прежний комментарий оставлен цитатой (летопись ниже). Ветки «неполное» и «на паузе» не тронуты, проверки владения не сдвинуты.
- `schedules_create`: `Schedule(...)` собирается до решения о моменте (`is_active=False`, `next_run_at=None`) и в сессию не добавляется; при полноте — `next_run_or_none(schedule)`; `None` → тот же отказ без `db.add`; иначе `is_active=True`, момент присвоен. Прямой вызов `compute_next_run_at` и строка `from app.services.schedule_service import compute_next_run_at` сняты.
- Правила фазы, закреплявшие молчаливую паузу, переписаны: код в `Location`, равенство адреса отказа, строка равна снимку посева. Новые правила: отказ на htmx (204 + `HX-Location`), создание на второй линии (целевое + параметризованное по шести формам).
- Правило по дереву ослаблено до «ни один обработчик не зовёт вычислитель напрямую»; вызов ловится и по имени, и по атрибуту.
- IN-04 (половина этого модуля): устаревшее основание «строка в шапке сдвинула бы номера строк» названо устаревшим с плана 15-08, настоящее основание дописано рядом.

## Task Commits

1. **Задача 1: Редактор отказывает на второй линии, как тумблер (WR-01)**
   - `0aa43f8a` test(15-16): RED
   - `5fa0552f` feat(15-16): GREEN
2. **Задача 2: Создание спрашивает ту же вторую линию; правило по дереву ослаблено (WR-02, половина IN-04)**
   - `6c6edb3e` test(15-16): RED
   - `0e86878a` feat(15-16): GREEN (вместе с числом гейта `HX_LOCATION_DESTINATION_CALLS_DECLARED`)

**Plan metadata:** коммит `docs(15-16)` со сводкой, STATE.md, ROADMAP.md, state.json.

## RED-улики (обе — `RED_EVIDENCE_OK`)

Прогон целевого правила с `--junit-xml` в scratchpad, тот же прогон переложен в TAP одноразовым скриптом в scratchpad (не закоммичен), запись `{command, exitCode, targetTest, output}` проверена `gsd-tools check tdd-red-evidence` → `RED_EVIDENCE_OK`, `reason: target_test_failed`.

**Задача 1** — на коммите `0aa43f8a`, дерево продукта до правки:
- `FAILED tests/test_pages/test_editor_schedules.py::test_malformed_stored_days_str_form_goes_the_same_way`
- последняя строка: `1 failed, 1 warning in 1.90s`
- причинный литерал: `assert 'notice=schedule_values_out_of_domain' in '/ads/1/edit?sched=1#sched-1'` — прежний ответ вёл в редактор на карточку, без кода.
- Замер всей выборки `-k "malformed_stored or second_line"` на RED-дереве: `7 failed, 26 passed` (пять неисполнимых форм `…_lands_one_outcome`, целевое правило, правило htmx); после GREEN — `33 passed`.

**Задача 2** — на коммите `6c6edb3e`:
- `FAILED tests/test_pages/test_editor_schedules.py::test_create_on_the_second_line_refuses_the_days_str_form_with_the_notice`
- последняя строка: `1 failed, 1 warning in 1.93s`
- причинный литерал: `AssertionError: форма days-str-1: создание ответило 500: PendingRollbackError: … Original exception was: (sqlite3.IntegrityError) CHECK constraint failed: ck_schedules_active_requires_next_run`, `assert 500 == 302`.
- Замер выборки `-k "second_line or asked_through_the_helper or create"` на RED-дереве: `7 failed, 18 passed` (целевое, пять неисполнимых форм создания, правило по дереву; `tz-mars-phobos` на создании зелен и до правки — зону откатывает профиль); после GREEN — `25 passed`.

## TDD Gate Compliance

`git log --grep="^test(15-16):"` → `6c6edb3e`, `0aa43f8a`; `git log --grep="^feat(15-16):"` → `0e86878a`, `5fa0552f`. У каждой задачи `test` стоит до `feat`. REFACTOR не понадобился. Нарушений нет.

## Летописи переписанных правил и комментариев (дословно)

**`app/pages/schedules.py`, `schedules_update`, ветка `next_run is None`:**
> ⚠️ ЛЕТОПИСЬ АБЗАЦА (идиома D-30/D-32; прежняя редакция названа, а не стёрта). До плана 15-16 здесь стояло: «Полное включённое расписание без момента сохраняется ВЫКЛЮЧЕННЫМ: пару „включено + нет момента“ схема не примет (`ck_schedules_active_requires_next_run`), и фиксация ответила бы пятисоткой. Правка человека при этом сохраняется — тем же основанием, что неполное расписание выше (D-08), — а возобновление тумблером откажет с объяснением, как отказывает на такой строке сегодня», — и ветка ставила `schedule.is_active = False` и фиксировала. Это описывало поведение до плана 15-16 верно, но работающее расписание гасло МОЛЧА, на обычном ответе успеха, тогда как тумблер и JSON-API тот же исход отвергали по имени. Вариант «сохранить паузой с уведомлением» владелец отверг.

**`test_malformed_stored_form_on_the_second_line_lands_one_outcome`:**
> ⚠️ ЛЕТОПИСЬ ПРАВИЛА (идиома D-30/D-32; прежние утверждения названы, а не стёрты молча). До плана 15-16 докстринг гласил «неисполнимая форма — `next_run_at` пуст и строка выключена», а ветка неисполнимых форм утверждала `assert stored.next_run_at is None` и `assert stored.is_active is False` и в адрес ответа не смотрела вовсе. Правило закрепляло ПРЕДСУЩЕСТВУЮЩУЮ политику второй линии — молчаливое выключение работающего расписания, — которая противоречила тумблеру и JSON-API (ревью WR-01; память проекта «тесты фазы закрепляют старые дефекты»). Владелец `chubav` выбрал ОТКАЗ 2026-09-25 (Г-2).

**`test_malformed_stored_days_str_form_goes_the_same_way`:**
> ⚠️ ЛЕТОПИСЬ ПРАВИЛА (идиома D-30/D-32; прежние утверждения названы, а не стёрты молча). До плана 15-16 правило после кода ответа утверждало `assert stored.next_run_at is None` и `assert stored.is_active is False` — молчаливое выключение. Оно закрепляло ПРЕДСУЩЕСТВУЮЩУЮ политику второй линии, противоречившую тумблеру и JSON-API (ревью WR-01); владелец выбрал отказ 2026-09-25 (Г-2).

**Шапка группы второй линии (план 15-08, задача 2):**
> ⚠️ ЛЕТОПИСЬ АБЗАЦА (идиома D-30/D-32; прежняя редакция названа, а не стёрта). До плана 15-16 абзац кончался словами «полное включённое расписание без момента сохраняется ВЫКЛЮЧЕННЫМ — пару „включено + нет момента“ схема не примет (`ck_schedules_active_requires_next_run`)». Это описывало дерево плана 15-08 верно, но закрепляло ПРЕДСУЩЕСТВУЮЩУЮ политику второй линии, которая противоречила тумблеру и JSON-API: работающее расписание гасло молча, без единого слова человеку (ревью WR-01). Владелец `chubav` 2026-09-25 (Г-2) выбрал ОТКАЗ, а не «сохранить паузой с уведомлением».

**`test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save`:**
> ⚠️ ЛЕТОПИСЬ ПРАВИЛА (идиома D-30/D-32; прежняя формулировка процитирована, а не стёрта). До плана 15-16 докстринг гласил: «`schedules_update` спрашивает `next_run_or_none` и не зовёт вычислитель сам. … Прямой вызов вычислителя в модуле обязан остаться РОВНО ОДИН — в `schedules_create`, где входы отсекаются на создании», — а последнее утверждение требовало `len(module_direct) == 1 and create_direct == ["compute_next_run_at"]`. Правило тем самым ЗАКРЕПЛЯЛО предсуществующую асимметрию: прямой вызов в создании старше фазы, а основание второй линии, данное правке планом 15-08, применимо к созданию дословно (ревью WR-02; память проекта «тесты фазы закрепляют старые дефекты»). Правило ослаблено до «ни один обработчик не зовёт вычислитель напрямую» по решению владельца `chubav` 2026-09-25 (Г-2).

**IN-04, комментарий над группой плана 15-09:**
> ⚠️ ОСНОВАНИЕ ПРЕДЫДУЩЕЙ ФРАЗЫ УСТАРЕЛО (отметка плана 15-16, 2026-09-25, ревью IN-04; идиома D-30/D-32 — фраза названа, а не стёрта). Оно перестало быть верным с планом 15-08: тот уже поставил в шапку модуля шестистрочный ввоз перечня форм (`from tests.test_schedules_out_of_domain_resume import …`), и номера строк ниже шапки сдвинулись тогда же. Настоящее основание — ввоз обслуживает ОДНО правило и потому живёт рядом с ним, а не в шапке всего модуля.

## Сверка с инвариантами продукта Фазы 10 (по диффу)

Перечень снят `uv run python scripts/prohibitions_census.py --list --phase 10 --class product-invariant` — **70 строк**, прочитан против диффа `94b59fe0..0e86878a` (три файла: `app/pages/schedules.py`, два модуля тестов).

- `10-01#3`, `10-24#2`, `10-31#1` (новых кодов реестра не заводить): соблюдено — отказ едет существующим `notices.SCHEDULE_VALUES_OUT_OF_DOMAIN`; `git diff --stat 94b59fe0..HEAD -- app/pages/notices.py` пуст.
- `10-55#0` (`compute_next_run_at` не правится): соблюдено — `app/services/schedule_service.py` в диффе отсутствует.
- `10-55#2` (`_clean_times`, `_reject_malformed_times`, `validate_timezone` не ослабляются): соблюдено — не тронуты; правила второй линии подменяют санитайзеры только в тестах через `monkeypatch`.
- `10-55#4` (без `except Exception`): соблюдено — в продукте перехвата не добавлено; помощник `next_run_or_none` не тронут. Два `except Exception` появились только в тестовом помощнике `_create_on_the_second_line` (перевод обрыва запроса в код ответа, тот же приём с `noqa: BLE001`, что у давнего `_save_from_editor`), не в `app/`.
- `10-18#3` (адрес приземления с кодом собирается ОДНИМ местом): соблюдено — оба отказа передают `notice=` слою ответа, склейку делает `respond`.
- `10-08#2` / `10-22#0` (граница величины не вводится отказом обработчика и не переносится внутрь): не затронуто — отказ второй линии 302/204 с кодом, не 4xx, и стоит ПОСЛЕ `id_in_column` / `_ownership_verdict`.
- `10-50#3` (скоуп владельца у новых чтений): новых чтений нет.
- `10-01#6`, `10-49#2`, `10-56#6`, `10-57#7` (тексты карточки и плашек не правятся): шаблоны, CSS, сценарий плашки и тексты реестра не тронуты.
- Остальные строки (панель подтверждения, гард происхождения, блок подъёма плашки, постраничный вывод, `hx-on`, третий обработчик) касаются файлов, которых дифф не касается.

Нарушений нет.

## Files Created/Modified

- `app/pages/schedules.py` — отказ второй линии в `schedules_update` и `schedules_create`, снят ввоз `compute_next_run_at`.
- `tests/test_pages/test_editor_schedules.py` — ввоз `notices`; `_save_from_editor_response`; `_RowSnapshot`/`_snapshot`, `_SecondLineSave`, `_refusal_landing`; переписанные правила второй линии; правило htmx; `_SecondLineCreate`, `_ad_schedules`, `_create_on_the_second_line` и два правила создания; переписанное правило по дереву; отметка IN-04.
- `tests/test_pages/test_hx_location_destinations.py` — `HX_LOCATION_DESTINATION_CALLS_DECLARED` 79 → 81 с записью летописи.

## Decisions Made

- Снимок строки берётся КОПИЕЙ значений до запроса: сессия теста та же, что у обработчика (`dependency_overrides`), и сравнение объекта карты идентичности с ним же самим было бы вакуумом.
- Правило по дереву ловит вызов и по атрибуту (`schedule_service.compute_next_run_at(...)`): иначе ввоз модуля вместо имени обходил бы ослабленное правило.
- Отказ создания ведёт в редактор объявления независимо от признака `return_to`: объявление подтверждено вердиктом владения выше, и адрес совпадает с адресом отказа правки и тумблера.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Гейт `test_the_number_of_transition_answering_calls_is_declared` покраснел: 81 вызов слоя ответа без фрагмента, объявлено 79**
- **Found during:** Задача 2, прогон соседних модулей (`tests/test_pages/test_hx_location_destinations.py` не назван ни в `<verify>` плана, ни в перечне оркестратора).
- **Issue:** Каждый из двух новых отказов — выход `respond` без `fragment=`; число гейта объявлено литералом.
- **Fix:** 79 → 81, поставлено прогоном покрасневшего правила (дословно: `вызовов слоя ответа БЕЗ фрагмента найдено 81, а объявлено 79`), запись летописи в действующей форме; адрес `/ads/{}/edit` уже в карте назначений, `test_every_transition_destination_has_a_declared_template` зелен.
- **Files modified:** `tests/test_pages/test_hx_location_destinations.py`
- **Committed in:** `0e86878a`
- ⚠️ **Окно красноты:** первый из двух вызовов (правка) лёг коммитом `5fa0552f`; на дереве `5fa0552f`…`6c6edb3e` правило было красным (80 против 79). Прогон задачи 1 этот модуль не включал. Окно закрыто коммитом `0e86878a`.

**2. [Rule 1 - Bug, тестовая обвязка] Помощник создания читал атрибут модели на упавшей сессии**
- **Found during:** Задача 2, первый RED-прогон.
- **Issue:** Общий обработчик `app/main.py` превращал `IntegrityError` в ответ 500 без проброса исключения, и чтение `ad.id` после запроса уходило в ленивую загрузку на сессии в состоянии `PendingRollbackError` — тест падал в обвязке, а не на утверждении.
- **Fix:** идентификаторы снимаются до запроса; на ответе 500 помощник снимает исходную причину первым запросом на упавшей сессии и откатывает её. RED стал падать на утверждении `assert 500 == 302` с литералом ограничения.
- **Files modified:** `tests/test_pages/test_editor_schedules.py`
- **Committed in:** `6c6edb3e`

**3. [Рамка плана] В RED-коммиты вошли больше одного правила**
- Правило htmx (задача 1) и правило по дереву (задача 2) утверждают новое поведение и краснели на своих RED-деревьях вместе с целевыми. Улика снята только с целевого правила, как требует план.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug in test harness) + 1 note on RED scope.
**Impact on plan:** Правки продукта строго по плану. Число гейта сдвинуто замером, не прогнозом.

## Номера строк плана (перезамер)

Сверены по содержанию, не по номерам: `schedules_create` :982, прямой вызов :1094-1100, `schedules_update` :1190, ветка второй линии :1330-1355, `schedules_toggle` :1412, отказ тумблера :1521-1535, JSON-API :400-417, `notices.py:134`, `schedule.py:47`, `test_editor_schedules.py` :3927, :4285-4470, :4472-4535, ввоз в шапке :44-50 (план: :45-50, сдвиг на одну строку — ввоз начинается строкой `from tests.test_schedules_out_of_domain_resume import (` на :45, его строки перечня :46-50) — на дереве `94b59fe0` совпали. После этого плана номера сдвинуты: в `app/pages/schedules.py` ветка правки выросла на ~20 строк, создание — на ~20; в модуле тестов ввоз `notices` в шапке (+1) и новые помощники и правила выше группы плана 15-09 (+~300).

## Issues Encountered

- Полный прогон суиты (`just test`, ~40 мин) по решению оркестратора выполняется ПОСЛЕ волны (после 15-19); здесь не запускался и записи `.planning/WINDOWS.md` не открывает. Замена — прогоны ниже.
- Прогоны на итоговом дереве (последовательно, `-p no:randomly`):
  - 22 модуля `tests/test_pages/`, работающих с обработчиками расписаний или читающих `app/pages/`, плюс `tests/test_routes/`, `tests/test_services/`, `tests/test_templates/`, `tests/test_schedule_relationships.py`, `tests/test_schedules_out_of_domain_resume.py`: `1 failed, 2032 passed` — единственный отказ — число гейта из отклонения 1; после правки числа тот модуль и 14 оставшихся модулей, читающих исходники `app/pages/` (`test_account_groups`, `test_access_gate`, `test_billing_*`, `test_history_*`, `test_htmx_response_contract`, `test_money_perimeter_gate`, `test_notices_channel`, `test_origin_guard_on_destructive_routes`, `test_reset_code_source`, `test_schedules_list`, `tests/test_application/test_declared_invariants.py`, `test_no_metering_remains.py`): `532 passed`.
  - Задача 1: `test_editor_schedules.py`, `test_schedules_out_of_domain_resume.py`, `test_schedules_api_value_domain.py`, `test_htmx_post_pairs.py`, `test_htmx_gates.py`: `419 passed`. `PAIRED_302_ASSERTIONS_DECLARED` не двинулся (190): новые утверждения 302 идут через помощники по коду ответа.
  - `tests/test_planning/`: `114 passed`.
  - `uv run python -m compileall -q app main.py tests` — без вывода; `graphify update .` выполнен.
- Ни одного `import yaml` не добавлено — `YAML_DIRECT_IMPORTERS` не трогался.

## Known Stubs

Нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Готов 15-17. Три страничных входа второй линии и JSON-API отвечают одной политикой.
- Для верификатора: строка D5 `coverage` — суждение о тексте плашки на входе создания (текст писался для тумблера).
- Строка пробы FORM-01 (`unclassified — review manually`) названа планом и не закрывается им.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED
