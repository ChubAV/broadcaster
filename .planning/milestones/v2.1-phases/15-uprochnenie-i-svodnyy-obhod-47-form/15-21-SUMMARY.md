---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 21
subsystem: infinite-scroll
tags: [def-09-03, page-size, sentinel, infinite-scroll, htmx, jinja, role-status, in-05, ui-review, pytest, tdd]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-09 — `limit={{ page_size }}` в шести сентинелах, ключ контекста `page_size`, гейт `test_markup_literal_inventory.py`; планы 15-16 и 15-17 — предшественники по `depends_on` (правки `app/pages/schedules.py` и пар деградации)"
provides:
  - "шесть сентинелов `app/templates/{ads,accounts,schedules}/{list,partial_cards}.html` не несут `limit`: единственный носитель размера — умолчание `Query(PAGE_SIZE)` обработчика порции"
  - "на тех же шести строках подпись `Загрузка…` и `role=\"status\"`; обе половины каждой пары сменились одним коммитом"
  - "шесть мест рендера больше не кладут `page_size` в контекст; комментарии DEF-09-03 / 15-09 дополнены записью плана 15-21 с датой"
  - "правило 6 `test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant` (исходник, сигнатура, рендер, мёртвый ключ, счёт карточек порции без `limit`); на месте прежнего правила оставлена датированная запись о замене"
  - "`PAGE_SIZE_LITERAL_FORMS`: сеть литерала 1 → 5 форм, места называются формой; контроль `test_control_every_page_size_literal_form_is_found_and_named` с проверкой точности"
  - "названный остаток: четыре сентинела истории и макрос сентинела экрана групп аккаунта несут `limit={{ page_size }}`, адресат — следующая веха"
affects: [15-verification, 15-UI-REVIEW, GATE-09, GATE-10, history, account_groups]

actuals:
  tokens: 11600
  tasks: 2
  commits: 3
plan_head_before: bb89dfeee9dfbd165d2ebc4916fe74218fcde88f

tech-stack:
  added: []
  patterns:
    - "Размер порции знает только сервер: адрес сентинела несёт курсор и отбор, а не `limit`; умолчание параметра проверяется по `inspect.signature` (`parameter.default.default` у `Query`) против константы, прочитанной из модуля"
    - "Сеть литерала — перечень именованных образцов; место называется `путь#индекс [форма]`, у каждой формы свой синтетический образец, и отдельно проверяется, что размер, записанный ИМЕНЕМ, сеть не ловит"
    - "Правило по трём разделам собирает все нарушения и называет каждое одним отказом, а не падает на первом"

key-files:
  created: []
  modified:
    - app/templates/ads/list.html
    - app/templates/ads/partial_cards.html
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/schedules/list.html
    - app/templates/schedules/partial_cards.html
    - app/pages/ads.py
    - app/pages/accounts.py
    - app/pages/schedules.py
    - tests/test_templates/test_markup_literal_inventory.py

key-decisions:
  - "Ключ `page_size` снят из контекстов всех шести мест рендера. По `grep -rn page_size app/templates/{ads,accounts,schedules}` ни один шаблон цепочки его больше не читает (0 вхождений), а правило 6 теперь утверждает, что ключа в контексте НЕТ: оставшийся ключ подталкивал бы вернуть `limit={{ page_size }}`"
  - "Новое правило 6 не параметризовано: оно проходит по трём разделам в одном тесте и перечисляет ВСЕ нарушения. Так RED-цель одна (`1 failed`), а отказ называет каждое место"
  - "Остаток назван с адресатом «следующая веха», и мест в нём ПЯТЬ, а не четыре, как в плане. Пятое место замерено при исполнении: макрос `sentinel` экрана групп аккаунта (`account_groups/includes/sentinel.html`). Ни одно из пяти не тронуто"
  - "Правило 7 сохранило имя `test_the_rendered_portion_url_is_unchanged`, ожидание сменилось на адрес без `limit`, в докстринге объяснено, что теперь значит «unchanged». Правило упоминается в сводке 15-09, поэтому имя не менялось"

patterns-established:
  - "Путь «пропавший ключ → пустой параметр → 422 → молчаливое зависание» закрыт тем, что параметра нет вовсе, а не строгим `Undefined`"

requirements-completed: [GATE-09, GATE-10]

coverage:
  - id: D1
    description: "Шесть сентинелов без `limit`; умолчание сервера = `PAGE_SIZE` модуля; контексты без `page_size`; порция без `limit` отдаёт `PAGE_SIZE` карточек"
    requirement: GATE-09
    verification:
      - kind: integration
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant"
        status: pass
      - kind: integration
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_the_rendered_portion_url_is_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain"
        status: pass
    human_judgment: false
  - id: D2
    description: "Подпись `Загрузка…` и `role=\"status\"` на шести строках; тождество пар «страница / порция» сохранено"
    requirement: GATE-09
    verification:
      - kind: unit
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_both_halves_of_every_pair_build_the_portion_url_with_the_same_line"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_control_negative_a_diverged_pair_is_named"
        status: pass
      - kind: other
        ref: "grep -c 'role=\"status\"' / 'Загрузка…' / 'Загрузка\\.\\.\\.' по шести шаблонам → 1 / 1 / 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Сеть литерала размера страницы ловит пять форм и каждую называет; размер, записанный ИМЕНЕМ, не ловит"
    requirement: GATE-10
    verification:
      - kind: unit
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_control_every_page_size_literal_form_is_found_and_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_markup_literal_inventory.py#test_no_page_size_literal_is_left_in_the_template_sources"
        status: pass
    human_judgment: false
  - id: D4
    description: "Бесконечная прокрутка трёх разделов в живом браузере (`revealed` → следующая порция, озвучивание `role=\"status\"`)"
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет JS и не наблюдает `revealed`. Шаг прокрутки в браузере видит только рантайм, и он остаётся пунктам обхода (assumptions_flagged плана)"

duration: 66min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 21: Сентинелы без размера страницы и пятиформная сеть литерала Summary

**Шесть сентинелов бесконечной прокрутки больше не несут `limit`. Размер задаёт только `Query(PAGE_SIZE)` обработчика порции, так что пропавший ключ контекста уже не может дать `limit=`, 422 и вечную «Загрузку». На тех же строках стоят `Загрузка…` и `role="status"`. Сеть литерала размера расширена с одной формы до пяти, у каждой свой контроль.**

## Performance

- **Duration:** 66 min (большая часть — два прогона гейтов, 21 и 36 мин)
- **Started:** 2026-09-25T09:21:18Z
- **Completed:** 2026-09-25T10:27:55Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- **UI-ревью, приоритет 3 (решение Г-2).** Из шести сентинелов снят `&limit={{ page_size }}`. Адрес аккаунтов теперь `/accounts/partial?offset={{ next_offset }}`, у объявлений и расписаний остались курсор и цикл отбора. Размер порции знает только сервер, и цель DEF-09-03 (один носитель числа) достигнута полнее, чем выражением плана 15-09.
- **Сняты ли ключи `page_size` из контекстов — да, из всех шести мест.** Замер: `grep -rn page_size app/templates/ads app/templates/accounts app/templates/schedules` → 0 вхождений, то есть ни один шаблон цепочки ключ не читает. Шесть строк `"page_size": PAGE_SIZE` удалены в `ads_partial`, `ads_list`, `accounts_partial`, `accounts_list`, `schedules_partial` и `schedules_list`. Комментарии `DEF-09-03, план 15-09` не стёрты: каждый стал записью «ЛЕТОПИСЬ (DEF-09-03)» из двух шагов с датой и основанием плана 15-21. У порции расписаний сохранена строка про ключевой курсор.
- **UI-ревью, пункт 8.** На шести строках `Загрузка...` заменено на `Загрузка…` и добавлен `role="status"`. Обе половины каждой пары сменились одним коммитом `5a95c970`, правило тождества пар зелёное.
- **Правило 6 заменено.** Новое правило `test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant` проверяет пять вещей: (а) в исходнике `hx-get` сентинела нет `limit`; (б) умолчание `limit` обработчика порции по `inspect.signature` равно `PAGE_SIZE` своего модуля; (в) отрендеренный адрес страницы и порции без `limit`; ключа `page_size` в контексте нет; порция без `limit` отдаёт ровно `PAGE_SIZE` карточек (счёт `id="ad-row-N"`, `account-row-N`, `schedule-row-N` при посеве 61). На месте прежнего правила стоит комментарий: имя прежнего правила, что оно утверждало, чем и когда заменено.
- **IN-05.** `PAGE_SIZE_LITERAL_FORMS` — это пять именованных образцов: `limit=<цифра>` (прежний, без изменений), `limit={{ <цифра> }}`, `limit={{ '<цифра>' }}`, `"limit": <цифра>` в `hx-vals` и скрытое поле `<input name="limit" value="<цифра>">`. Места называются `путь#индекс [форма]`. Рядом с перечнем записано, как менялось число форм (1 → 5). Проверка на снимке в scratchpad: прежнее одиночное выражение находит 1 из 5 синтетических образцов, новая сеть — 5 из 5. На живом дереве правило 1 зелёное.
- **Остаток назван.** Выражение `limit={{ page_size }}` по-прежнему несут `history/list.html`, `history/partial_cards.html`, `admin/user_history.html` и `admin/history_partial_cards.html` (`grep -c` → по 1). Пятое место той же формы нашлось при исполнении — макрос `account_groups/includes/sentinel.html`. Все пять записаны в докстринге модуля с адресатом «следующая веха».

## Какие правила сличали адрес с `limit` и как приведены

| Правило | Файл | Что сличало | Как приведено |
|---|---|---|---|
| `test_the_page_size_in_the_context_is_the_module_constant` (прежнее правило 6) | `tests/test_templates/test_markup_literal_inventory.py` | ключ `page_size` = `PAGE_SIZE` в контексте обоих обработчиков | заменено новым правилом 6; на его месте оставлен комментарий о замене |
| `test_the_rendered_portion_url_is_unchanged` (правило 7) | тот же | адрес страницы и порции `…&limit={size}` | ожидание — адрес без `limit`; имя сохранено, в докстринге объяснено, что теперь значит «unchanged» |
| `test_control_negative_a_diverged_pair_is_named` (контроль к правилу 5) | тот же | подмена первого `&` на `&amp;` в строке аккаунтов | в строке аккаунтов `&` больше нет. Подмена теперь возвращает `&limit={{ page_size }}` в ОДНУ половину пары, то есть моделирует ровно ту правку, от которой держит правило 5 |
| `test_infinite_scroll_chain`, `test_infinite_scroll_keeps_filters`, `test_partial_without_layout_param_ok` | `tests/test_pages/test_htmx_preserved.py` | адрес сентинела с `limit` НЕ сличают: курсор ищут через `CURSOR_RE`, отбор — через `in` | **не правились.** Они шлют `limit={PAGE}` в запросе порции, а сервер его по-прежнему принимает. Все зелёные |
| `test_the_next_portion_does_not_skip_a_row_after_a_toggle_under_the_state_filter` | `tests/test_pages/test_schedules_list.py` | идёт по адресу, который выдала страница | не правилось, зелёное: адрес без `limit` даёт порцию `PAGE_SIZE` |

## Task Commits

1. **Задача 1 RED:** правило отсутствия размера — `ed8ae09f` (test)
2. **Задача 1 GREEN:** шесть сентинелов, обработчики, правило 7, контроль пары, докстринг — `5a95c970` (feat)
3. **Задача 2:** сеть литерала из пяти форм с контролем — `3bf34862` (test)

**Plan metadata:** коммит `docs(15-21)` со сводкой, затем коммит учёта `docs(15-21)` (STATE.md, ROADMAP.md, state.json).

## TDD Gate Compliance

План `type: execute`, `workflow.tdd_mode: true`.

- **Поведение добавляет задача 1.** RED — коммит `ed8ae09f` `test(15-21)`, GREEN — `5a95c970` `feat(15-21)`, RED предшествует GREEN. Запуск RED: один целевой тест с `-p no:randomly`. В выводе `FAILED tests/test_templates/test_markup_literal_inventory.py::test_the_six_sentinels_carry_no_page_size_and_the_server_default_is_the_module_constant`, последняя строка `1 failed, 7 warnings`. Отказ содержательный: 18 нарушений, и каждое называет `limit` или ключ `page_size` — шесть «исходник адреса сентинела несёт `limit`», шесть «отрендеренный адрес `…&limit=30` несёт `limit`», шесть «в контексте мёртвый ключ `page_size`». Нарушений по сигнатуре и счёту карточек нет: эти две половины были зелёными и до правки, и так задумано (умолчание `Query(PAGE_SIZE)` уже было). Запись переведена из `--junit-xml` в TAP одноразовым скриптом в scratchpad (не закоммичен), `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`).
- **Задача 2 продукт не меняет.** Она правит только тестовый прибор (сеть литерала и её контроль), поэтому это один коммит `test(15-21)` без `feat`. Что контроль не пустой, проверено отдельно: на снимке в scratchpad прежнее одиночное выражение находит 1 из 5 образцов, и новый контроль на нём покраснел бы.
- REFACTOR-коммитов нет.

## Сверка правки с инвариантами продукта Фазы 10

`uv run python scripts/prohibitions_census.py --list --phase 10 --class product-invariant` прочитан. Сверка по диффу `bb89dfee..HEAD -- app/pages`: `git diff … | grep -E '^[+-].*(Query|limit|offset)'` без строк комментариев не нашёл ничего. Значит, границы `limit`/`offset` (`Query(PAGE_SIZE, ge=1, le=100)`, `Query(0, ge=0)`, `after_id … le=ID_MAX`) не тронуты, и запреты `10-28#1` / `10-29#1` соблюдены. Новых кодов уведомления нет, модалка, плашка и CSS не менялись. Сентинелы вне шести названных не тронуты: остаток из пяти мест проверен `grep -c` (по 1).

## Files Created/Modified

- `app/templates/{ads,accounts,schedules}/{list,partial_cards}.html`: сентинел без `limit`, подпись `Загрузка…`, `role="status"`. В `accounts/list.html` комментарий «и «Загрузка...» прочтётся» переписан как «и подпись загрузки прочтётся», иначе счёт критерия `Загрузка\.\.\.` → 0 не сходился бы.
- `app/pages/ads.py`, `app/pages/accounts.py`, `app/pages/schedules.py`: из шести контекстов убран `page_size`, комментарии DEF-09-03 дополнены записью плана 15-21.
- `tests/test_templates/test_markup_literal_inventory.py`: новое правило 6 (с комментарием о прежнем на его месте), ожидания правила 7, подмена в контроле пары, `PAGE_SIZE_LITERAL_FORMS` + `PAGE_SIZE_FORMS_DECLARED` + образцы и контроль пяти форм, в докстринге модуля история носителя (литерал → выражение → отсутствие) и названный остаток.

## Decisions Made

См. `key-decisions` во frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Контроль разошедшейся пары перестал бы приземлять подмену**
- **Found during:** Задача 1 (GREEN)
- **Issue:** `test_control_negative_a_diverged_pair_is_named` подменял первый `&` в строке сентинела аккаунтов на `&amp;`. После снятия `&limit=…` в этой строке `&` не осталось, и проверка «ПОДМЕНА НЕ ПРИЗЕМЛИЛАСЬ» покраснела.
- **Fix:** подмена теперь возвращает `&limit={{ page_size }}` в одну половину пары. Докстринг контроля объясняет, почему сменилась подмена.
- **Files modified:** `tests/test_templates/test_markup_literal_inventory.py`
- **Verification:** контроль зелёный, `_diverged_pairs` называет `["accounts"]`.
- **Committed in:** `5a95c970`

**2. [Rule 3 - Blocking] Критерий `grep -c '^PAGE_SIZE_LITERAL_FORMS'` → 1**
- **Found during:** Задача 2
- **Issue:** константа числа форм с именем `PAGE_SIZE_LITERAL_FORMS_DECLARED` тоже начиналась с проверяемого префикса, и счёт давал 2.
- **Fix:** константа названа `PAGE_SIZE_FORMS_DECLARED` (суффикс `_DECLARED` проекта сохранён).
- **Committed in:** `3bf34862`

**3. [Rule 2 - Missing Critical] Правило 6 утверждает и отсутствие мёртвого ключа контекста**
- **Found during:** Задача 1 (RED)
- **Issue:** план требует снять `page_size` из контекстов (truth 2), но в перечне проверок (а)-(в) нет правила, которое помешало бы ключу вернуться.
- **Fix:** в половину (в) правила 6 добавлена проверка `PAGE_SIZE_CONTEXT_KEY not in context` для обоих обработчиков каждого раздела.
- **Committed in:** `ed8ae09f`

### Отступления без правки кода

- **`tests/test_pages/test_htmx_preserved.py` не правился**, хотя он есть в `files_modified`. Замер: ни одно его правило не сличает адрес сентинела с `limit` (см. таблицу выше). Тестам нужен только их `_seed_section` и `_sentinel_urls`, которые новое правило берёт оттуда без изменений.
- **Остаток — пять мест, а не четыре.** Макрос сентинела экрана групп аккаунта несёт ту же форму, план его не называл. Он записан рядом с четырьмя, но не тронут: запрет «не трогать сентинелы вне шести названных».
- **Правило 6 не параметризовано** (обход трёх разделов внутри теста): так RED-цель одна, а отказ перечисляет все нарушения.

---

**Total deviations:** 3 исправлены автоматически (1 Rule 1, 1 Rule 2, 1 Rule 3) и 3 отступления без правки кода.
**Impact on plan:** все правки нужны для корректности правил. Продукт вне шести сентинелов и шести контекстов не тронут.

## Issues Encountered

None.

## Проверка

- Задача 1, первый `<verify>`: `test_markup_literal_inventory.py` + `test_htmx_preserved.py` → `35 passed`.
- Задача 1, расширенный набор: все `tests/test_templates/`, `tests/test_pages/` (`test_htmx_gates`, `test_htmx_post_pairs`, `test_hx_location_destinations`, `test_htmx_preserved`, `test_responsive_markup`, `test_shell`, `test_account_groups`, `test_history`, `test_schedules_list`, `test_schedules_detached_account`, `test_identifier_bounds`, `test_admin_users`) → `1271 passed`, 0 failed (21 мин).
- Задача 2: `tests/test_templates/` целиком → `367 passed`.
- `<verification>` плана: `uv run pytest tests/test_templates/ tests/test_pages/ -q -p no:randomly -m "not planning"` → `2371 passed`, 0 failed (35 мин 32 с) на дереве `3bf34862`. `uv run python -m compileall -q app main.py tests` → ОК. `graphify update .` выполнен.
- `uv run pytest tests/test_planning/ -q` → `130 passed`.
- Критерии приёмки задачи 1: `limit=` → 0 в каждом из шести файлов; `role="status"` → 1, `Загрузка…` → 1, `Загрузка\.\.\.` → 0 в каждом; остаток истории `limit={{ page_size }}` → по 1; имя правила → 1. Задача 2: `^PAGE_SIZE_LITERAL_FORMS` → 1, контроль называет пять форм, правило 1 зелёное.
- Считающие гейты не сдвинулись: новых 302-утверждений, вызовов назначений `HX-Location` и пар деградации план не заводил.
- **Замена полного прогона:** полный `just test` (около 40 мин) после волны 6 запускает оркестратор, по указанию диспетчера. Здесь он не запускался, запись в `WINDOWS.md` не открывалась. Вместо него прогнаны каталоги `tests/test_templates/` и `tests/test_pages/` целиком и `tests/test_planning/`.

## Known Stubs

None. `PAGE_SIZE_LITERAL_SITES = {}` — это объявленный ноль (перечень законных мест), а не заглушка.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Следующий по порядку план — 15-22 (волна 7).
- Пункты UI-ревью «приоритет 3» и «пункт 8» и находка IN-05 исполнены. Бесконечную прокрутку в живом браузере должен подтвердить обход (D4, `human_judgment: true`).
- Пять сентинелов с `limit={{ page_size }}` (история ×2, история пользователя в админке ×2, макрос экрана групп аккаунта) переданы следующей вехе. Путь «пропавший ключ → `limit=` → 422» у них открыт так же, как был открыт у шести до этого плана.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED
