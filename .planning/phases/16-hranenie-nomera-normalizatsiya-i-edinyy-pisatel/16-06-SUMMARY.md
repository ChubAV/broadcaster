---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 06
subsystem: testing
tags: [ast-gate, single-writer, phone, sqlalchemy, tdd, source-walk]

requires:
  - phase: 16-05
    provides: "app/application/accounts/phone.py — единственный писатель номера (условные UPDATE, set_manual_phone, зеркало set_committed_value)"
  - phase: 16-03
    provides: "колонки messenger_accounts.phone / phone_is_manual, константа MANUAL_REQUIRES_PHONE"
provides:
  - "tests/test_application/test_phone_single_writer_gate.py — PHONE_WRITER_MODULE, PHONE_WRITER_EXCEPTIONS, WRITER_TREES, writer_sources(root), phone_write_offences(source, path), judged_offences(source, path), tree_offences(root); 31 правило (с параметрами)"
affects: [phase 18 manual form, phase 19 capture on connect, phase 20 backfill]

actuals:
  tokens: 6119      # chars/4 над единственным файлом плана (24478 символов), та же шкала, что estimate
  tasks: 2
  commits: 4        # git rev-list --count plan_head_before..plan_head_after
plan_head_before: 000be2ac3dd4e41aec0481c3d85508cf7da8a0b0
plan_head_after: 873847673fafa2f34f5674837c24b4cbcf8ec526

tech-stack:
  added: []
  patterns:
    - "Гейт записи по AST пяти видов; вселенная выводится обходом app/ и scripts/, а не перечнем"
    - "Чистый предикат без исключений (phone_write_offences) отдельно от судимого пути (judged_offences): им же доказывается, что запись в самом писателе видна"
    - "Исключение реестра снимает виды 2–5 и никогда не снимает присваивание"

key-files:
  created:
    - tests/test_application/test_phone_single_writer_gate.py
  modified: []

key-decisions:
  - "Задача 1 до появления реестра пропускала модуль-писатель обходом целиком; задача 2 заменила пропуск реестром PHONE_WRITER_EXCEPTIONS, и обход теперь судит писатель тоже (присваивание в нём краснит)"
  - "Вид 5 сужен до присваивания колонки номера в SET до WHERE: «UPDATE groups SET title = :t WHERE phone = :p» — фильтр, а не запись; закреплено положительным контролем"
  - "Вид 3 берёт словари во всех позиционных аргументах values(...), включая словари внутри списка или кортежа (многострочная вставка) — строже буквы плана"
  - "Граница предиката названа в шапке: values(**fields), setattr с вычисленным именем и SQL из склейки переменных по исходнику не определимы"

patterns-established:
  - "Гейт записи колонки: реестр исключений поимённо с причиной, правило на его состав, контроль с подложенным запрещённым видом в исключённом модуле"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Запись номера вне модуля-писателя любым из пяти видов краснит суиту; подложенная запись в синтетическом app/ находится тем же обходом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_phone_write_outside_the_writer_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_raw_sql_phone_write_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_an_assignment_to_a_phone_attribute_is_a_write (4 параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_phone_keyword_in_a_write_call_is_a_write (4 параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_phone_key_in_a_values_dict_is_a_write (3 параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_phone_attribute_written_by_name_is_a_write (2 параметра)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_raw_sql_phone_write_in_a_string_constant_is_a_write (2 параметра)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Живое дерево — ноль нарушений при доказанно непустом обходе (104 файла, модуль-писатель среди них, 5 записей второго вида в нём без исключения)"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
    human_judgment: false
  - id: D3
    description: "Законные упоминания номера не краснят: render/start_session/_max_step_markup с phone=, объявление колонки, константа CHECK, докстринги, чтение и фильтр; max_worker/, alembic/, tests/ вне обхода"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write (10 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_walk_leaves_max_worker_alembic_and_tests_outside"
        status: pass
    human_judgment: false
  - id: D4
    description: "Исключение — ровно модуль-писатель с причиной; его виды 2–5 не судятся, а присваивание в нём краснит"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_exception_registry_names_only_the_writer_module"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_control_an_assignment_inside_the_writer_module_still_reddens"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-08
status: complete
---

# Phase 16 Plan 06: Гейт единственного писателя номера Summary

**Новый AST-гейт `tests/test_application/test_phone_single_writer_gate.py` краснит суиту на любой записи `phone` / `phone_is_manual` вне `app/application/accounts/phone.py` в `app/` и `scripts/`. Он ловит пять видов записи: присваивание, именованный аргумент в `values`/`update`/`insert`/`MessengerAccount`, ключ словаря в `values`, `setattr`/`set_committed_value` и сырой UPDATE/INSERT в строке. Исключение в реестре одно — модуль-писатель, и присваивание запрещено даже в нём.**

## Performance

- **Duration:** около 10 мин (по замеру от записи времени старта; чтение контекста шло раньше)
- **Started:** 2026-10-08T18:40:06Z
- **Completed:** 2026-10-08T18:50:25Z
- **Tasks:** 2
- **Files modified:** 1 (создан)

## Accomplishments
- Пять видов записи номера ловятся по AST. Законные `phone=` в `app/pages/accounts.py` (`render`, `_max_step_markup`, `start_session`) не краснят.
- Обход `writer_sources(root)` выводит множество файлов из `app/` и `scripts/`. Подложенная запись в `tmp_path/app/…` находится тем же обходом. `max_worker/`, `alembic/` и `tests/` остаются вне обхода, и это закреплено отдельным правилом.
- Антивакуум внутри живого правила: обойдено больше 50 файлов, модуль-писатель среди них, и предикат без исключения находит в нём настоящую условную запись.
- Реестр `PHONE_WRITER_EXCEPTIONS` содержит ровно одну запись с причиной, и его состав закреплён правилом. Исключение снимает виды 2–5 и никогда не снимает присваивание. Это проверено контролем: в исходник писателя подложено присваивание.

## Замер обхода (живое дерево и главная рабочая копия)

| Корень | Файлов в обходе | Модуль-писатель виден | Сырых находок без исключения | Судимых нарушений |
|---|---|---|---|---|
| корень worktree (`/source/broadcaster/.claude/worktrees/agent-a8fef15e05e17d38b`) | 104 | да | 6 (все в писателе) | 0 |
| главная рабочая копия (`/source/broadcaster`, только чтение) | 104 | да | 6 (все в писателе) | 0 |

Множество файлов на обоих корнях совпало полностью. Замер сделан одноразовым скриптом из scratchpad. Скрипт импортировал модуль гейта из worktree и в главную копию ничего не писал. Gitignored `__pycache__/` под `app/` и `scripts/` не содержит `*.py`, поэтому `rglob("*.py")` его не берёт. `.claude/worktrees/` лежит вне `app/` и `scripts/`. Урок 16-04 про `node_modules` здесь не применим, потому что обход не выходит за эти два каталога.

Шесть сырых находок в писателе:
- `:83` — `values(phone=…)`;
- `:117` — `set_committed_value(…, 'phone', …)`;
- `:132` — `values(phone=…)` и `values(phone_is_manual=…)`;
- `:135` — `values(phone=…)` и `values(phone_is_manual=…)`.

Пять из них — второго вида, одна — четвёртого.

## Task Commits

1. **Задача 1 (трасер): обход, присваивание, аргумент пишущего вызова.**
   - `a47252c4` (test, RED)
   - `b5ed32dc` (feat, GREEN)
2. **Задача 2: словарь, запись по имени, сырой SQL, реестр.**
   - `496aee66` (test, RED)
   - `87384767` (feat, GREEN)

**Plan metadata:** коммит этой сводки (docs).

## TDD: RED / GREEN

**RED задачи 1.**
- Команда: `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly -k test_a_planted_phone_write_outside_the_writer_reddens_the_gate --junit-xml=.pytest_cache/gsd-red/red1.xml`, под замком хоста.
- Exit 1. Все три совпадения на месте:
  - `FAILED tests/test_application/test_phone_single_writer_gate.py::test_a_planted_phone_write_outside_the_writer_reddens_the_gate`;
  - `1 failed, 9 deselected`;
  - `AssertionError: подложенная запись номера не найдена: присваивание account.phone в app/pages/planted.py гейт пропустил`.
- `check tdd-red-evidence` на неизменённом JUnit XML: `RED_EVIDENCE_OK` / `target_test_failed`, `format: junit`, `report_errors: []`.
- **semanticAssessment:**
  - Цель исполнилась. Первое утверждение (обход нашёл подложенный `app/pages/planted.py`) прошло.
  - Цель упала на запланированном утверждении «находки есть», потому что заготовка `phone_write_offences` возвращала `[]`. Ошибок сбора, импорта и фикстур не было.
  - Прогон всего файла в RED дал `10 failed`, без строк ERROR. Каждое падение — поведенческое утверждение.
  - Живое правило в RED прошло проверки «обойдено 104 файла» и «писатель виден». Упало оно на антивакууме: «предикат без исключения нашёл в модуле-писателе 0 записей второго вида при 104 обойдённых файлах».

**GREEN задачи 1.** Виды 1–2. Модуль-писатель обход пока пропускал целиком. Результат: `10 passed`, отбор `-k "planted or live_tree"` — `2 passed`.

**RED задачи 2.**
- Команда: `… -k test_a_raw_sql_phone_write_reddens_the_gate --junit-xml=.pytest_cache/gsd-red/red2.xml`.
- Exit 1. Три совпадения:
  - `FAILED tests/test_application/test_phone_single_writer_gate.py::test_a_raw_sql_phone_write_reddens_the_gate`;
  - `1 failed, 30 deselected`;
  - `AssertionError: сырой SQL с номером не найден: []`.
- `check tdd-red-evidence`: `RED_EVIDENCE_OK`, `format: junit`, `report_errors: []`.
- **semanticAssessment:**
  - Цель исполнилась: обход нашёл подложенный `app/x.py`. Упала она на запланированном утверждении, потому что у предиката ещё не было пятого вида.
  - Прогон всего файла дал `10 failed, 21 passed`, без ERROR. Падали виды 3–5, правило реестра («реестр исключений — не ровно модуль-писатель: []» на заготовке `{}`) и контроль присваивания в писателе (заготовка `judged_offences → []`).
  - Зелёными остались задача 1 и положительные контроли. Это ожидаемо: они проверяют отсутствие находок.

**GREEN задачи 2.** Виды 3–5, реестр, `judged_offences`. `tree_offences` теперь судит и писатель. Результат: `31 passed`.

**Как записана улика.** JUnit XML и записи `red1.json` / `red2.json` лежат в gitignored `.pytest_cache/gsd-red/` worktree и не коммитились. Сборщик записей `mkred1606.py` остался в scratchpad. Верб принял JUnit напрямую, перегон в node:test TAP не понадобился.

## TDD Gate Compliance

| Задача | RED | GREEN | REFACTOR |
|---|---|---|---|
| 1 | `a47252c4` test(16-06) | `b5ed32dc` feat(16-06) | — (не нужен) |
| 2 | `496aee66` test(16-06) | `87384767` feat(16-06) | — (не нужен) |

Каждый `test(16-06)` предшествует своему `feat(16-06)`. Нарушений нет.

## Files Created/Modified
- `tests/test_application/test_phone_single_writer_gate.py` — гейт единственного писателя: шапка по-русски (зачем, вселенная и её граница, почему AST, цена строгости второго вида, граница предиката, реестр), константы, обход, предикат пяти видов, судимый путь, 31 правило.

## Decisions Made
- **Пропуск писателя в задаче 1 заменён реестром в задаче 2.** Живое правило задачи 1 («вне писателя ноль») требовало как-то исключить писатель, а реестр план отнёс к задаче 2. После задачи 2 обход судит писатель тоже, и присваивание в нём краснит гейт.
- **Пятый вид: только присваивание в `SET` до `WHERE`.** Фильтр по номеру в `WHERE` — не запись. Положительный контроль `update-filtering-by-phone-in-where` это закрепляет.
- **Третий вид берёт словари во всех позиционных аргументах `values(...)`**, в том числе внутри списка или кортежа (многострочная вставка `insert(...).values([{...}])`).
- **Положительных контролей больше, чем в плане:** чтение `account.phone`, фильтр `.where(MessengerAccount.phone.is_(None))`, `phone_set=` в журнале, докстринг модуля с `INSERT INTO`, фильтр в `WHERE`. Всего 10 параметров с `id`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Журнал головы плана — в scratchpad, а не в git-dir**
- **Found during:** старт плана.
- **Issue:** изоляция worktree отказала в записи `gsd-plan-head-before-16-06` и сентинела `gsd-spawn-toplevel` в `/source/broadcaster/.git/worktrees/agent-a8fef15e05e17d38b/`.
- **Fix:** голова плана `000be2ac…` записана в scratchpad (`1606-plan-head-before.txt`). Это та же база, что проверил `worktree_branch_check`. Счёт `commits` измерен от неё: `git rev-list --count 000be2ac..HEAD` = 4. Дрейф cwd проверялся перед каждым коммитом через `git rev-parse --show-toplevel`.
- **Files modified:** нет.
- **Committed in:** — (процедура).

**2. [Rule 1 - Bug] Время старта в записях RED-улики было вписано вручную**
- **Found during:** сбор сводки.
- **Issue:** при первой сборке записей `runStartedAt` был вписан на глаз. У второй записи (18:52) он оказался позже текущих часов. Верб принял обе, но поле было неверным.
- **Fix:** обе записи пересобраны с `runStartedAt` из атрибута `timestamp` JUnit, который записал сам pytest (18:41:00.34 и 18:43:25.68), и снова поданы классификатору: `RED_EVIDENCE_OK` для обеих. JUnit-файлы не менялись со времени RED-прогонов.
- **Files modified:** только записи в gitignored `.pytest_cache/gsd-red/`.
- **Committed in:** — (вне коммитов).

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug). Оба касаются процедуры, а не кода.
**Impact on plan:** на гейт не влияют.

## Issues Encountered
None.

## Verification (прогон на итоговом дереве, под замком хоста)
- `tests/test_application/test_phone_single_writer_gate.py`: 31 passed. Отбор `-k "planted or live_tree"`: 2 passed.
- Гейт вместе с писателем, гонкой и приватностью: 113 passed.
- Сквозные гейты `test_htmx_post_pairs.py test_htmx_gates.py tests/test_templates test_declared_invariants.py -p no:randomly`: **576 passed** (2:32).
- `tests/test_phone_privacy_gate.py`: 64 passed.
- Весь `tests/test_application/`: 306 passed.
- Набор фазы (`test_phone.py`, писатель, гонка, гейт, приватность, CHECK модели, `tests/test_migrations`): 365 passed.
- Широкие гейты по исходникам `app/` (`test_no_metering_remains`, `test_payment_status_vocabulary`, `test_schedule_invariants`, `test_ops_state`, `test_notices_channel`; `test_declared_invariants` уже в прогоне выше): 120 passed.
- `uv run python -m compileall -q app main.py tests`: OK.
- `tests/test_planning`: результат ниже, в Self-Check.

**Заменено, названо поимённо:**
- Полная суита (`just test`, ≈40 мин) не гонялась. Это пост-мердж гейт оркестратора (замечание 4 диспетчера).
- `graphify update .` не запускался в worktree: `graphify-out/` gitignored, и после мерджа его запускает оркестратор (замечание 3).

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Фазы 18–20 встретят гейт зелёным. Любая новая запись номера должна идти через `fill_reported_phone` / `record_reported_phone` / `set_manual_phone`, иначе суита покраснеет.
- Расширять `PHONE_WRITER_EXCEPTIONS` можно только решением владельца с причиной: правило состава реестра покраснеет на второй записи.
- Фаза 16 завершена планами 16-01…16-06 и готова к фазовой верификации после пост-мердж гейта.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-08*

## Self-Check: PASSED

- FOUND: `tests/test_application/test_phone_single_writer_gate.py`
- FOUND: `a47252c4`, `b5ed32dc`, `496aee66`, `87384767` (все — предки HEAD, `git merge-base --is-ancestor`)
- Критерии приёмки, перепроверены на итоговом дереве:
  - `^def (writer_sources|phone_write_offences)\(` → 2;
  - `^PHONE_WRITER_MODULE = "app/application/accounts/phone.py"` → 1;
  - `^PHONE_WRITER_EXCEPTIONS` → 1;
  - `def test_control_an_assignment_inside_the_writer_module_still_reddens` → 1;
  - `set_committed_value|setattr` → 12;
  - `INSERT INTO messenger_accounts` → 3.
- `tests/test_planning` (с этой сводкой на диске): 217 passed, 3 skipped, 0 failed — форма совпадает с той, что назвал диспетчер
