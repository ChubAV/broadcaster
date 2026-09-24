---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 08
subsystem: schedules
tags: [cr-01, schedules_update, next_run_or_none, timezone, ast-gate, pytest, tdd]

requires:
  - phase: 10-rychag-components-modal-html
    provides: "долг D-18 (находки 1 и 2): CR-01 на четвёртом входе и докстринг-фантом, обещавший несуществующий греп-гейт"
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "плана-предшественника нет (depends_on: []); перечень MALFORMED_STORED_FORMS — tests/test_schedules_out_of_domain_resume.py"
provides:
  - "schedules_update: откат невалидной зоны на ПРОВЕРЕННОЕ значение (сохранённая зона, только если валидна, иначе profile_tz) — путь восстановления возвращён"
  - "schedules_update спрашивает next_run_or_none(schedule) вместо прямого вызова вычислителя; неисполнимое полное включённое расписание сохраняется выключенным"
  - "tests/test_services/test_schedule_rules_gate.py — гейт огульного перехвата по ast ТЕЛА schedule_rules.py с тремя отрицательными и одним положительным контролем"
  - "докстринг next_run_or_none называет запрещённую конструкцию прямо и принуждающее правило; вынужденная оговорка снята летописью D-30/D-32"
  - "32 правила CR-01 в tests/test_pages/test_editor_schedules.py над импортированным перечнем форм"
affects: [15-09, 15-verification, schedules, WR-03]

actuals:
  tokens: 12337
  tasks: 3
  commits: 8
plan_head_before: 83c34ab5fedc3eb0ed6f1d089996c305c566b879

tech-stack:
  added: []
  patterns:
    - "Вторая линия защиты измеряется, ОТКРЫВ первую: санитайзеры страницы подменяются пропуском сохранённых значений (monkeypatch), и только тогда видно, держит ли помощник исход"
    - "Гейт по ТЕЛУ модуля через ast.Try/ast.ExceptHandler, функции запрета принимают исходник ТЕКСТОМ — контроли от вакуума на синтетических исходниках"
    - "Правило разности обходов: текст находит упоминания в докстринге, дерево — нет; оба числа и разность утверждаются"

key-files:
  created:
    - tests/test_services/test_schedule_rules_gate.py
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/deferred-items.md
  modified:
    - app/pages/schedules.py
    - app/services/schedule_rules.py
    - tests/test_pages/test_editor_schedules.py
    - tests/test_pages/test_htmx_post_pairs.py

key-decisions:
  - "Откат зоны в schedules_update: невалидное значение формы откатывается на сохранённую зону ТОЛЬКО если она сама валидна, иначе на profile_tz (user.timezone ∈ VALID_TIMEZONES, UTC последним рубежом); валидная сохранённая зона остаётся умолчанием — исправная строка не переводится на зону профиля"
  - "Посылка задачи 2 плана опровергнута замером: путём карточки редактора все 6 форм перечня зелены уже после задачи 1 (правка переписывает дни/времена значениями формы, санитайзеры отбрасывают негодное). Помощник на этом входе — ВТОРАЯ линия; он внесён по решению владельца и измерен правилами с открытой первой линией"
  - "Неисполнимое ПОЛНОЕ включённое расписание на правке сохраняется ВЫКЛЮЧЕННЫМ (is_active=False, next_run_at=None) по основанию D-08, а не отказом: иначе фиксация падала бы на ck_schedules_active_requires_next_run"
  - "Критерий grep -c 'compute_next_run_at' == 1 буквально невыполним (импорт + три комментария); прямой вызов считается по ast правилом test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save: 2 → 1"
  - "Миграции данных нет (решение владельца chubav 2026-09-23 «только код»); WR-03 правила не получил"

patterns-established:
  - "Правило о починенном поведении без маркера слепка непочиненного, с названной причиной; имя маркера в файле не набирается, когда приёмка считает его вхождения"

requirements-completed: ["долг-D-18"]

coverage:
  - id: D1
    description: "Правка из редактора на строке с зоной Mars/Phobos не даёт пятисотки и записывает ВАЛИДНУЮ зону, прочитанную из СУБД; откат на проверенную зону профиля/UTC; валидная зона формы уважается, невалидная не попадает; предикат доступа не сдвинут; next_run_at согласован с полнотой"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k malformed_stored_zone"
        status: pass
    human_judgment: false
  - id: D2
    description: "schedules_update спрашивает next_run_or_none; ни одна из 6 форм MALFORMED_STORED_FORMS не даёт пятисотки ни путём карточки, ни на второй линии; исход один (next_run_at None, строка выключена); обратное направление на исправной форме; days-str-1 отдельно; перечень объявлен числом 6"
    requirement: "долг-D-18"
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly -k malformed_stored"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save"
        status: pass
    human_judgment: false
  - id: D3
    description: "Запрет огульного перехвата в schedule_rules.py принуждён ast-разбором ТЕЛА; перечень UNRUNNABLE_STORED_VALUE_ERRORS заперт числом 5; докстринг называет конструкцию и правило, оговорка снята летописью"
    requirement: "долг-D-18"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_services/test_schedule_rules_gate.py -q -p no:randomly"
        status: pass
    human_judgment: false

duration: 76min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 08: CR-01 обоими корнями на четвёртом входе и ast-гейт огульного перехвата Summary

**Правка расписания из редактора откатывает невалидную зону на проверенную (зона профиля или UTC), а не на сохранённую, и спрашивает `next_run_or_none`; запрет огульного перехвата в `schedule_rules.py` принуждён разбором ТЕЛА по `ast`, и докстринг помощника наконец называет свой предмет**

## Performance

- **Duration:** 76 min
- **Started:** 2026-09-24T09:01:33Z
- **Completed:** 2026-09-24T10:17:40Z
- **Tasks:** 3 (все)
- **Files modified:** 5 кода/тестов + `deferred-items.md`
- **Commits:** 8 (замер `git rev-list --count 83c34ab5..HEAD` при записи сводки)

## Перезамеренные координаты (D-18.1 записи долга НЕВЕРНЫ)

`15-CONTEXT.md` D-18.1 называет `app/pages/schedules.py:1049-1070` (трасса `:1067`). Это внутренности УЖЕ ПОЧИНЕННОГО `schedules_create` (973-1177). По `ast` на дереве `83c34ab5`: `schedules_update` = **1181-1356**; дефект отката — `:1278-1280`, запись зоны — `:1287`, прямой вызов вычислителя — `:1296` (план называл `:1290`; сдвиг на 6 строк, предмет тот же).

**Целевые строки после плана** (`ast`, дерево `5e9b4d49`): `schedules_update` = **1181-1399**; первая половина починки (откат на проверенное) — `:1278-1304`, `profile_tz` на `:1298`, `stored_tz` на `:1299-1301`; вторая половина (вопрос к помощнику) — `:1318-1350`, вызов `next_run_or_none(schedule)` на `:1334`.

## Accomplishments

- **Корень 1 (задача 1).** Откат идёт на проверенное значение по образцу `schedules_create:1079-1082`. Правка строки с `timezone='Mars/Phobos'` больше не даёт 500 и ЗАПИСЫВАЕТ ВАЛИДНУЮ зону — проверено чтением строки из СУБД. Путь восстановления, который предписывают три починенных обработчика, возвращён.
- **Корень 2 (задача 2).** `schedules_update` спрашивает `next_run_or_none(schedule)` (образец `schedules_toggle`). Прямой вызов вычислителя в модуле остался ровно один, в `schedules_create` (по `ast`).
- **Находка 2 (задача 3).** Добавлен `tests/test_services/test_schedule_rules_gate.py`: 9 правил, из них 4 контроля (голый перехват, `Exception` в кортеже, литеральный кортеж в помощнике, положительный «обработчиков > 0»). Докстринг `next_run_or_none` называет `except:` / `except Exception:` / `except BaseException:` прямо и указывает принуждающее правило по имени файла.

## Прогон по ВСЕМУ перечню форм (метка → исход) против зонда 13-го круга

Зонд 13-го круга: **5 passed / 1 failed** (`tz-mars-phobos`).

| Метка | Путь карточки редактора (санитайзеры на месте), после плана | Вторая линия (сохранённые значения дошли до расчёта): ДО задачи 2 | Вторая линия: ПОСЛЕ задачи 2 |
|---|---|---|---|
| `times-abc` | 302 ✓ (время отброшено → неполное) | 500 (`ValueError`) | 302, `next_run_at=None`, выключено |
| `times-25-00` | 302 ✓ | 500 (`ValueError`) | 302, `None`, выключено |
| `times-9` | 302 ✓ | 500 (`IndexError`) | 302, `None`, выключено |
| `times-int-9` | 302 ✓ | 500 (`AttributeError`) | 302, `None`, выключено |
| `tz-mars-phobos` | 302 ✓ (**до задачи 1 — 500**, `ZoneInfoNotFoundError`) | 302 (зону уже чинит корень 1) | 302, момент есть, включено |
| `days-str-1` | 302 ✓ (день `"1"` → `[1]`) | 500 (`IntegrityError` на `ck_schedules_active_requires_next_run` — `None` без исключения) | 302, `None`, выключено |

Итог: путём карточки **6 passed / 0 failed** (было 5/1); на второй линии **6/6** (до задачи 2 было 1/6).

**Исключения вне перечня пяти имён: НЕ встречено ни одного.** Замеренные на второй линии: `ValueError` ×2, `IndexError`, `AttributeError`, `ZoneInfoNotFoundError` (до задачи 1). `days-str-1` исключения не бросает: вычислитель отвечает `None`. Перечень `UNRUNNABLE_STORED_VALUE_ERRORS` не тронут: `grep -c` = 3 до и после, пять имён.

## Снятая оговорка докстринга: прежний и новый текст

- **Прежний** (`schedule_rules.py:178-179`): «Запрет проверяется грепом по телу модуля, поэтому имя запрещённой конструкции здесь и не набирается.»
- **Новый**: «Запрет ПРИНУЖДЁН правилами `tests/test_services/test_schedule_rules_gate.py`, и принуждён РАЗБОРОМ ТЕЛА модуля по `ast`, а не грепом: гейт читает узлы обработчиков исключений, и упоминание конструкции в этом докстринге ему не видно по построению.» Рядом летопись: прежняя формулировка процитирована с многоточием, чтобы не совпасть с грепом приёмки, и стоит формула «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ». Обещанного греп-гейта в дереве не существовало.

## Task Commits

1. **Задача 1: откат зоны на проверенное значение**
   - `849e1479` test(15-08): RED — 5 failed / 5 passed; целевое правило: `assert 500 == 302`
   - `de5b0549` fix(15-08): GREEN
   - `131850df` refactor(15-08): маркер слепка назван без своего имени (приёмка ждёт 0 вхождений)
2. **Задача 2: четвёртый вход спрашивает помощника**
   - `46e85ffe` test(15-08): RED — 12 failed / 20 passed
   - `854750e2` feat(15-08): GREEN
3. **Задача 3: гейт по `ast` ТЕЛА и докстринг**
   - `8905f6af` test(15-08): RED — 2 failed / 7 passed (докстринг молчит)
   - `5bc1f538` feat(15-08): GREEN
- **Rule 3:** `5e9b4d49` fix(15-08): число 302 правила пар 188 → 189

## TDD Gate Compliance

RED → GREEN соблюдены для всех трёх задач: у каждой `test(15-08)` стоит до `fix(15-08)` / `feat(15-08)`. RED-улика каждой задачи снята прогоном `--junit-xml`, переложена в TAP одноразовым скриптом в scratchpad (не закоммичен) и проверена `gsd-tools check tdd-red-evidence`. Вердикт — **RED_EVIDENCE_OK** на всех трёх:
- задача 1: `test_malformed_stored_zone_edit_from_the_editor_does_not_answer_500`, exit 1, `assert 500 == 302` (ZoneInfoNotFoundError);
- задача 2: `test_malformed_stored_form_on_the_second_line_never_answers_500[times-abc]`, exit 1, `assert 500 == 302` (ValueError);
- задача 3: `test_the_text_walk_sees_the_docstring_and_the_tree_walk_does_not`, exit 1: текстовых вхождений 0.

Случай задачи 2 назван под «Deviations»: прямой RED по посылке плана дал бы неожиданную ЗЕЛЕНЬ.

## Files Created/Modified

- `app/pages/schedules.py` — `schedules_update`: откат зоны на проверенное значение и вопрос к `next_run_or_none`
- `app/services/schedule_rules.py` — только докстринг `next_run_or_none`
- `tests/test_pages/test_editor_schedules.py` — 32 правила CR-01 (`-k malformed_stored`) над ввезённым `MALFORMED_STORED_FORMS`
- `tests/test_services/test_schedule_rules_gate.py` — новый гейт, 9 правил
- `tests/test_pages/test_htmx_post_pairs.py` — `PAIRED_302_ASSERTIONS_DECLARED` 188 → 189 с записью летописи
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/deferred-items.md` — предсуществующая жалоба правила пар (план 15-03)

## Сдвиг строк, на которые ссылаются другие записи (для плана 15-09 и далее)

- `app/pages/schedules.py`: строки **≤1277 не сдвинуты** (цитаты 15-09 `schedules.py:84`, `:867-871` действуют). Начиная с `:1278` всё сдвинуто на **+43**: `schedules_toggle` 1360-1574 → **1403-1617** (его `next_run_or_none` 1469 → **1512**), `schedules_delete` 1578-1854 → **1621-1897**. Файл: 1854 → 1897 строк.
- `tests/test_pages/test_editor_schedules.py`: импорты +6 строк, поэтому всё начиная со строки 45 сдвинуто на **+6**. Цитата 15-09 `test_editor_schedules.py:2182` → **2188**, `:2170-2195` → **2176-2201**. Новый раздел — хвост файла, **3878-4518**.
- `tests/test_pages/test_htmx_post_pairs.py`: `PAIRED_302_ASSERTIONS_DECLARED` 3380 → **3393** (+13).

## Decisions Made

См. `key-decisions`. Главное: неисполнимое полное включённое расписание на правке сохраняется **выключенным**, а не отказом. Основание — то же, что у неполного (D-08): правка человека сохраняется, а возобновление тумблером откажет с объяснением `SCHEDULE_VALUES_OUT_OF_DOMAIN`. Сегодня эта ветвь достижима только второй линией, путь карточки её не открывает.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Посылка плана] Путём редактора пять форм задачи 2 уже зелены, RED по посылке невозможен**
- **Found during:** Задача 2
- **Issue:** План считал, что пять форм перечня бросают на правке исключение мимо обработчика. Замер: `schedules_update` переписывает дни и времена значениями ФОРМЫ, а `_clean_ints` / `_clean_times` отбрасывают негодное ДО расчёта. Правило над всем перечнем путём карточки зелено уже после задачи 1, то есть неожиданная зелень, fail-fast правило 1. Пять форм зонда проходили ровно поэтому.
- **Fix:** Правило пути карточки оставлено как ЗАМЕР посылки. RED и GREEN задачи 2 измерены на второй линии: санитайзеры подменяются пропуском сохранённых значений. Добавлено правило по `ast`: `schedules_update` зовёт помощника, а не вычислитель. Решение владельца «четвёртый вход спрашивает `next_run_or_none`» исполнено.
- **Files modified:** `tests/test_pages/test_editor_schedules.py`, `app/pages/schedules.py`
- **Committed in:** `46e85ffe`, `854750e2`

**2. [Rule 1 - Bug, найден RED'ом второй линии] `None` на полной включённой строке ронял фиксацию**
- **Found during:** Задача 2 (форма `days-str-1`)
- **Issue:** Если скопировать ветвь тумблера дословно, получается `next_run_at=None` при `is_active=True`, а это `IntegrityError` на `ck_schedules_active_requires_next_run`, то есть пятисотка.
- **Fix:** При `next_run is None` строка сохраняется выключенной (D-08).
- **Committed in:** `854750e2`

**3. [Rule 3 - Критерий невыполним буквально] `grep -c 'compute_next_run_at' app/pages/schedules.py` → 1**
- **Issue:** `grep` считает и импорт (`:23`), и комментарии (`:145`, `:275`, `:1449→1492`). Было 6, стало **5**. Прямых ВЫЗОВОВ по `ast`: было 2, стало **1**. Удалять нужный импорт или переписывать чужие комментарии ради счёта строк значило бы испортить код ради числа.
- **Fix:** Счёт вызовов принуждён правилом по дереву (`test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save`).
- **Committed in:** `46e85ffe`

**4. [Rule 3 - Blocking] Слово маркера слепка в комментарии нарушало приёмку «0 вхождений»**
- **Fix:** Маркер назван по месту регистрации, без своего имени (`131850df`, refactor, только комментарий).

**5. [Rule 3 - Blocking] Правило числа пар 302 покраснело: 189 против 188**
- **Found during:** финальный прогон `tests/test_pages/`
- **Issue:** Правило 6 задачи 1 (`test_malformed_stored_zone_access_predicate_is_unchanged`, строка 4203) добавило одно утверждение 302 о переведённом `schedules_update`. На снимке `83c34ab5` правило числа зелено: движение внёс этот план.
- **Fix:** 188 → 189, число поставлено прогоном, запись летописи добавлена. Жалобы на пару у утверждения нет.
- **Committed in:** `5e9b4d49`

**6. [Уточнение] Тест 6 задачи 1 берёт утверждения из `tests/test_pages/test_schedule_ownership.py`**
- План говорил «из существующих правил файла», но правил отказа по доступу на правке в `test_editor_schedules.py` нет: они живут в `test_schedule_ownership.py` (`test_update_of_a_foreign_schedule_with_a_foreign_ad_stays_silent`, `test_page_update_rejects_swapping_in_foreign_account`). Утверждения взяты оттуда. Сверх них утверждается, что испорченная зона осталась в строке: откат стоит ПОСЛЕ проверок владения.

---

**Total deviations:** 6: 2 по Rule 1, 3 по Rule 3, 1 уточнение.
**Impact on plan:** Оба корня закрыты разными задачами, как требовал план. Посылка задачи 2 опровергнута замером, и это записано, а не замолчано. Договор `compute_next_run_at` и перечень исключений не тронуты. В область ничего не добавлено.

## Issues Encountered

- **Предсуществующее, вне области:** `test_every_302_assertion_on_a_converted_handler_is_paired` красен на `tests/test_pages/test_billing_section.py:706` («обработчик не назван — адрес POST собран выражением»). Красен и на снимке `83c34ab5`, до первого коммита плана. Файл правил последним коммитом `0203202f` (план 15-03). Записано в `deferred-items.md`.

## Проверки (подстановка вместо полной суиты названа прямо)

Полную суиту (`just test`) по договорённости гонит оркестратор. Вместо неё прогнаны модули плана и все модули, которые исполняют `app/pages/schedules.py` / `app/services/schedule_rules.py`:
- `tests/test_pages/ tests/test_services/`: ДО плана **2215 passed / 2 failed**. Прогон шёл 35 мин, и обе жалобы правил пар — одна предсуществующая (billing), вторая — число, увидевшее уже добавленный тест 6. ПОСЛЕ плана, дерево кода `5e9b4d49`: **2257 passed / 1 failed**. Остался только предсуществующий billing. Прирост +41 = 32 + 9 новых правил.
- Тройка задачи 1 (`test_editor_schedules.py`, `test_schedules_out_of_domain_resume.py`, `test_schedules_poisoned_row.py`): ДО **118 passed**, ПОСЛЕ задачи 1 **128 passed**.
- `tests/test_services/`: ДО **284 passed**, ПОСЛЕ **293 passed**. `test_schedule_service.py`: **8 passed** (договор `compute_next_run_at` не тронут).
- `-k malformed_stored`: **32 passed** (≥ 12). Гейт: **9 passed**, `-k control`: **4 passed**.
- Вне `test_pages` / `test_services`: `tests/test_routes/test_schedules*.py` (8 модулей), `tests/test_schedules_out_of_domain_resume.py`, `tests/test_templates/test_degradation_pairs.py`, `tests/test_templates/test_form_inventory.py` — **254 passed**.
- `uv run python -m compileall -q app main.py tests` молчит. `tests/test_planning/`: **78 passed**.
- Греп-критерии: `tz = schedule.timezone` → **0**; `next_run_or_none` в `schedules.py` → **5** (≥ 2); `UNRUNNABLE_STORED_VALUE_ERRORS` → **3** до и после; оговорка → **0**; `ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ` → **1**; `check_schedules` в гейте → **0**; `ast.ExceptHandler` в гейте → **4**; `characterisation` в `test_editor_schedules.py` → **0**.
- `graphify update .` прогнан после каждой правки кода: задачи 1, 2 и 3.
- `requirements.ready-ids` (только чтение) для `долг-D-18` ответил «1/1 ready». `requirements.mark-complete` НЕ вызывался: это не ID `REQUIREMENTS.md`, а требования фазы 15 закрываются после верификации.

## Прямые записи, требуемые планом

- **Миграции данных НЕ было.** Ни `alembic/`, ни `scripts/`, ни разового запроса (`git diff --name-only 83c34ab5..HEAD` не содержит таких путей). Решение владельца `chubav` 2026-09-23: «только код». Уже испорченную строку человек перезаписывает через редактор, и правило 2 задачи 1 доказывает, что это теперь работает.
- **WR-03 правила НЕ получил.** Гейт называет его вне области, а слово `check_schedules` в гейте не набрано. Правила, закрепляющего обрыв партии как норму, нет, слепка под маркером непочиненного тоже нет.
- `tests/conftest.py`, `compute_next_run_at` и `UNRUNNABLE_STORED_VALUE_ERRORS` не тронуты.

## Known Stubs

Нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- План 15-09 (волна 2) может брать `app/pages/schedules.py` и `tests/test_pages/test_editor_schedules.py`: сдвиги строк перечислены выше.
- Жалоба правила пар на billing (15-03) остаётся открытой в `deferred-items.md`. Полный прогон оркестратора её увидит.

## Self-Check: PASSED

- FOUND: все 5 файлов кода и тестов и `deferred-items.md`
- FOUND: коммиты `849e1479`, `de5b0549`, `131850df`, `46e85ffe`, `854750e2`, `8905f6af`, `5bc1f538`, `5e9b4d49`

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*
