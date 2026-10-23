---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 55
subsystem: testing
tags: [ast, static-gate, single-writer, ban-channel, runtime-guard, O-23, WR-33, WR-34, V10-1, V10-2, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-51 — app/models/phone_guard.py (writer_scope, _WRITER_ACTIVE, PhoneWriteOutsideWriter, регистрация в app/models/__init__.py); 16-53 — канал запрета dynamic_construct_findings, DYNAMIC_CONSTRUCT_KINDS, DYNAMIC_CONSTRUCT_EXCEPTIONS и dynamic_construct_scan гейта писателя"
provides:
  - "ROUND_TEN_BANNED_FORMS (10 строк: 7 WR-33, 2 V10-1, 1 V10-2) и правило test_a_round_ten_form_is_red_as_a_banned_construct; трасер test_a_planted_backfill_pick_is_red_as_a_banned_construct"
  - "RUNTIME_GUARD_MODULE, RUNTIME_GUARD_REGISTRATION, runtime_guard_bypasses, правило test_the_runtime_guard_is_entered_only_by_the_writer и контроль test_a_planted_guard_bypass_reddens_the_rule (8 строк)"
  - "NAMED_COST_MECHANISM_CASES (15 измеренных форм: 12 «двоек», 3 «единицы») и правило test_a_named_cost_mechanism_form_gives_its_measured_count"
  - "шапка гейта писателя: раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ», оговорки трёх обещаний, пункты границы (1), (2), (5) по замеру, абзац цены по механизму, летописи WR-33 / V10-1 / V10-2, согласование прежних запретов, живое дерево 106; правило шапки test_the_writer_gate_header_names_the_ban_and_the_runtime_guard"
affects: [16-56, "Фазы 18–20 (вход в writer_scope или event.remove вне писателя краснит гейт)"]

actuals:
  tokens: 14017   # chars/4: дифф d9b38e21..6b5ab496 — 56 066 знаков (wc -m)
  tasks: 3
  commits: 6      # git rev-list --count d9b38e21..HEAD до коммита сводки
plan_head_before: d9b38e21f7147f8b86ce9ac7e5a53f1096e23fae
plan_head_after: 6b5ab4969deca89e36ff13c9fbea3486a05a3581

tech-stack:
  added: []
  patterns:
    - "Строки форм раунда 10 — через сканер канала (dynamic_construct_scan) с измеренным списком (строка, вид), а не через предикат распознавания"
    - "Правило входа в разрешение защиты — по имени модуля и разрешения в любой позиции (ast.Name / ast.Attribute / ввоз), а не по пути ввоза; снятие слушателя — по последнему имени получателя remove"
    - "Цена называется по механизму с таблицей измеренных чисел, предикат не правится"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Трасер задачи 1 связан со строкой таблицы V10-1: канал стоит с плана 16-53, поэтому RED — отсутствие строки формы в ROUND_TEN_BANNED_FORMS, а не отсутствие поимки"
  - "RED задачи 2 — заглушка runtime_guard_bypasses, возвращающая [] (как RED-заглушка канала в 16-53), а не ввоз внутри тела: падение утверждением с литералом, а не ImportError"
  - "Контроль обхода защиты расширен двумя формами сверх плана: псевдоним модуля событий (sa_event.remove) и ввоз remove из sqlalchemy.event"
  - "Механизм цены записан по замеру: functools.partial(<API>, other) под именем НОСИТЕЛЯ даёт одну находку; пару partial даёт только под именем самого применения (цена kw)"
  - "Пункт (1) границы: setattr(self, \"f\", api) с литеральным именем — НЕ конструкция канала (замер); названо открытой находкой владельцу, а не принятой границей"

patterns-established:
  - "Шапка не повторяет заголовки разделов («ГРАНИЦА ПРЕДИКАТА», «ЗАПРЕТ ДИНАМИКИ …», «Летопись …») вне их места: правила шапки ищут первое вхождение"

requirements-completed: [PHONE-02]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Формы раунда 10 стороны писателя (WR-33 ×7, V10-1 ×2, V10-2 ×1) красны каналом запрета ровно измеренным списком (строка, вид); подложенный scripts/phone_backfill_pick.py — двумя находками «отражение как значение» на строках 2 и 8"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_round_ten_form_is_red_as_a_banned_construct (10), #test_a_planted_backfill_pick_is_red_as_a_banned_construct"
        status: pass
    human_judgment: false
  - id: D2
    description: "Вход в writer_scope / ссылка на модуль защиты вне трёх законных мест и event.remove где угодно краснят гейт; живое дерево — 106 файлов, 0 обходов; контроль — 7 подложенных обходов по находке, писатель — 0"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_runtime_guard_is_entered_only_by_the_writer, #test_a_planted_guard_bypass_reddens_the_rule (8)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Цена WR-34 по механизму закреплена 15 измеренными формами (12 «двоек», 3 «единицы»), один узел колонки, одно место, каждая красна каналом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_named_cost_mechanism_form_gives_its_measured_count (15)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_accept.py — OK (12, 3)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка правдива: раздел запрета и защиты, оговорки, пункты границы по замеру, абзац цены без прежней фразы, летописи, согласование запретов, живое дерево 106"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_ban_and_the_runtime_guard и два прежних правила шапки"
        status: pass
    human_judgment: false
  - id: D5
    description: "Открытая находка: держатель setattr(self, \"f\", s.bulk_update_mappings) с применением self.f(MessengerAccount, rows) не судит ни предикат, ни канал, ни защита — решение владельца"
    verification: []
    human_judgment: true
    rationale: "Закрытие требует правки общего канала или предиката — вне файлов плана (заметка 0 оркестратора) и, вероятно, решения владельца о расширении перечня видов"

duration: 36min
completed: 2026-10-23
status: complete
---

# Phase 16 Plan 55: Гейт писателя после О-23 (а) — формы раунда 10 каналом, вход в защиту, цена WR-34 по механизму, правдивая шапка

**Десять форм раунда 10 стороны писателя (WR-33, V10-1, V10-2) теперь строки канала запрета с измеренными находками; новое правило краснит вход в `writer_scope` и ссылку на модуль защиты вне трёх законных мест и любое `event.remove`; цена WR-34 названа по механизму и закреплена 15 измеренными формами; шапка гейта писателя называет запрет, исключения, защиту и её границу. Замер нашёл одну открытую дыру вне файлов плана — держатель `setattr(self, "f", <bulk API>)`; она вынесена владельцу.**

## Performance

- **Duration:** 36 мин
- **Started:** 2026-10-23T10:31:13Z
- **Completed:** 2026-10-23T11:07Z
- **Tasks:** 3 (трасер + 2), все RED → GREEN
- **Files modified:** 1 (`tests/test_application/test_phone_single_writer_gate.py`, +781 / −12)

## Accomplishments

- **Задача 1.** `RoundTenBannedForm(id, source, constructs)` и `ROUND_TEN_BANNED_FORMS` — 10 строк по таблице `<scope_note>`. Каждая форма подкладывается в синтетическое `scripts/x.py`, судится `dynamic_construct_scan`, и список находок (строка, вид) должен точно совпасть с измеренным. Трасер с `scripts/phone_backfill_pick.py`: ровно две находки «отражение как значение», на строках 2 и 8.
- **Задача 2.** Добавлены `RUNTIME_GUARD_MODULE` и `RUNTIME_GUARD_REGISTRATION`, а также помощник `runtime_guard_bypasses(source, path)`, построенный без `getattr` со строкой. Он ищет два случая:
  - (а) вне `RUNTIME_GUARD_PLACES`: ввоз модуля защиты или его имён, а также любые `Name` / `Attribute` с именами `phone_guard`, `writer_scope`, `_WRITER_ACTIVE`;
  - (б) везде: `remove` у получателя `event` или у псевдонима модуля событий, а также ввоз `remove` из `sqlalchemy.event`.

  Живое правило несёт антивакуум. Контроль — 8 строк. Рядом с `NAMED_COST_CASES` стоят `NAMED_COST_MECHANISM_CASES` (15 форм) и правило числа находок, одного места, одного узла колонки и красноты каналом.
- **Задача 3.** Шапка:
  - новый раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ» перед «ГРАНИЦЕЙ ПРЕДИКАТА»: обещание, девять видов с примерами, пять исключений деревьев гейта с причиной, защита и её граница по шапке модуля защиты, первый и второй рубеж, открытая находка, что остаётся от прежнего, согласование запретов С1/С2, живое дерево;
  - оговорки к «Каждое связывание имени судится», «Судится каждое толкование вызова» и к подаче ссылки;
  - пункты границы (1), (2), (5) — по замеру;
  - абзац цены — по механизму; прежняя фраза пересказана, дословного текста нет;
  - три летописи;
  - комментарий `NAMED_COST_CASES`.

## Task Commits

1. **Задача 1 (трасер): формы раунда 10 — строки канала**
   - RED `0188f348` — `test(16-55): add failing tracer for a planted backfill pick red as a banned construct`
   - GREEN `fa3cfdfc` — `feat(16-55): round-ten writer forms are rows of the ban channel (WR-33, V10-1, V10-2)`
2. **Задача 2: вход в защиту только у писателя; цена WR-34 по механизму**
   - RED `d1f35e6f` — `test(16-55): add failing rule that only the writer enters the runtime guard, with planted bypass controls`
   - GREEN `d9ea00c2` — `feat(16-55): runtime guard entered only by the writer and WR-34 cost by mechanism`
3. **Задача 3: правдивая шапка**
   - RED `87780baa` — `test(16-55): add failing rule that the writer gate header names the ban and the runtime guard`
   - GREEN `6b5ab496` — `feat(16-55): truthful writer gate header for the ban, the runtime guard and the WR-34 cost`

REFACTOR-коммитов нет. Для 16-56: GREEN WR-33 (сторона писателя) — «fa3cfdfc»; GREEN WR-34 (задачи 2–3) — «d9ea00c2», «6b5ab496».

## TDD: RED-улики (три совпадения + верб)

Улики лежат в `.pytest_cache/gsd-red/task{1,2,2b,3}.{out,xml,json}` (gitignored). Каждая запись `{command, exitCode, targetTest, output=JUnit XML, expected, actual, semanticAssessment}` прошла `check tdd-red-evidence` с итогом `RED_EVIDENCE_OK` / `target_test_failed`. Первая запись задачи 2 с общим именем правила дала `INVALID_RED no_target_test_failure`: у параметризованного правила имя цели должно быть точным. Её переписали с точным именем строки — `task2` — и добавили отдельную запись живого правила — `task2b`. Обе прошли.

| Задача | Команда (`-k`) | Строка `FAILED` | Последняя строка | Причинный литерал |
|--------|----------------|-----------------|------------------|-------------------|
| 1 | `test_a_planted_backfill_pick_is_red_as_a_banned_construct` | `FAILED …::test_a_planted_backfill_pick_is_red_as_a_banned_construct` | `1 failed, 626 deselected, 1 warning in 0.71s` | «подложенный скрипт с `f = getattr` в `pick` и `self.f = setattr` в классе не красен как запрещённая конструкция строкой таблицы `ROUND_TEN_BANNED_FORMS` …» |
| 2 | `"guard_bypass or entered_only_by_the_writer"` | `FAILED …::test_a_planted_guard_bypass_reddens_the_rule[from-the-guard-module-import-writer-scope]` (+6 строк контроля, + живое правило) | `8 failed, 1 passed, 637 deselected, 1 warning in 1.62s` (N = 8 ≥ 6) | «подложенный обход защиты на исполнении не краснит правило входа в разрешение писателя …» (7 раз) и «защита писателя на исполнении обходится кодом приложения незаметно …» |
| 3 | `test_the_writer_gate_header_names_the_ban_and_the_runtime_guard` | `FAILED …::test_the_writer_gate_header_names_the_ban_and_the_runtime_guard` | `1 failed, 660 deselected, 1 warning in 0.79s` | «шапка гейта писателя не называет запрет динамики и защиту на исполнении» |

**Семантическая оценка RED.**
- **Задача 1.** Цель исполнилась и упала на втором утверждении: `pinned is None`, таблица до GREEN пуста. Первое утверждение — две находки канала на строках 2 и 8 — зелено уже на RED, потому что канал стоит с плана 16-53. Правило таблицы с пустой параметризацией на RED — skipped, вне выборки.
- **Задача 2.** Заглушка `runtime_guard_bypasses` возвращает `[]`. Поэтому семь подложенных обходов дают 0 находок вместо 1–2, а антивакуум живого правила не видит `writer_scope` в писателе. Строка законного места (писатель, 0) зелена и на RED — это закрепка. Ошибок сбора, ввоза и имени нет.
- **Задача 3.** Правило назвало 10 недостающих пунктов: раздел, 5 игл абзаца цены, прежняя фраза и 3 летописи.

**GREEN.**
- Задача 1: модуль писателя — 636 passed (план: ≥ 636).
- Задача 2: выборка `-k "guard_bypass or entered_only_by_the_writer or named_cost"` — 27 passed (план: ≥ 25). Три модуля — 1109.
- Задача 3: три правила шапки зелёные, три модуля — 1110.

## Справочно: прежний `phone_write_offences` на формах `ROUND_TEN_BANNED_FORMS` (не утверждается)

| Строка | Находки канала (строка, вид) | Прежний предикат |
|--------|------------------------------|------------------|
| `wr33-getattr-under-to-thread` | (8, отражение) | 0 |
| `wr33-getattr-under-run-in-executor` | (8, отражение), (10, отражение) | 0 |
| `wr33-getattr-under-context-run` | (8, отражение), (9, отражение) | 0 |
| `wr33-getattr-under-thread` | (8, отражение), (9, отражение) | 0 |
| `wr33-getattr-under-a-partial-wrapper` | (8, отражение), (9, отражение) | 1 — `:9 запись атрибута по имени setattr(…, 'phone', …)` |
| `wr33-methodcaller-under-to-thread` | (8, отложенный вызов), (9, отражение) | 0 |
| `wr33-methodcaller-under-to-thread-descriptor` | (8, отложенный вызов), (9, отложенный вызов) | 0 |
| `v10-1-function-binds-getattr-class-binds-setattr` | (8, отражение), (14, отражение) | 0 |
| `v10-1-function-binds-a-methodcaller-class-binds-setattr` | (8, отложенный вызов), (14, отражение) | 1 — `:17 запись атрибута по имени setattr(…, 'phone', …)` |
| `v10-2-getattr-string-of-a-setattr-attribute` | (8, отражение), (14, отражение) | 0 |
| трасер `scripts/phone_backfill_pick.py` | (2, отражение), (8, отражение) | 0 |

Вид каждой конструкции связывания совпал с колонкой «вид канала» таблицы плана. Расхождений вида нет. `getattr(self, "f")` сама находкой не является, как предупреждала сводка 16-53.

## Замеры на конечном дереве (`6b5ab496`, всё под общим замком)

| Проверка | База (оркестратор / план) | Здесь |
|----------|---------------------------|-------|
| модуль писателя, задача 1 | 625 → план ≥ 636 | 636 passed |
| `<automated>` 2 задачи 1 (`t1_rows.py`) | — | `OK 10` |
| выборка задачи 2 | план ≥ 25 | 27 passed |
| приёмка задачи 2 (`t2_accept.py`) | `(12, 3)` | `OK` |
| три модуля гейтов (писатель + паритет + приватность) | 1074 | 1110 passed (+36: 11 + 24 + 1) |
| предикаты против `c9da79b2` (`predicates.py`) | — | `OK 6` (после каждого GREEN) |
| строки против `c9da79b2` (`base_rows.py`) | 268 / 107 | `OK {'LITERAL_FORM_CASES': 268, 'LEGITIMATE_CASES': 107}` (после каждого GREEN) |
| `NAMED_COST_CASES`, `NAMED_COST_FINDINGS`, `LITERAL_FORM_PLACES`, `PHONE_WRITER_EXCEPTIONS` против `c9da79b2` (`base_extra.py`, сверх плана) | — | `OK` (AST-дамп тождествен) |
| набор фазы (11 путей) | 1604 | 1640 passed (+36) |
| живые деревья `-s -k "live_tree or dynamic_construct or entered_only_by_the_writer"` | — | 5 passed; «Канал запрета гейта писателя: файлов 106; находок 0» |
| живое дерево писателя (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| `test_phone_writer_runtime_guard.py` | 36 | 36 passed |
| `tests/test_application` | 946 | 982 passed (+36) |
| сквозные гейты (`htmx_post_pairs`, `htmx_gates`, `test_templates`, `declared_invariants`, `test_logging_config`) | 593 | 593 passed |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `prohibitions_census.py --check` | exit 0, 913 | exit 0, «реестр: 913 строк, биекция с переписью — согласие» |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `tests/test_planning` | 218 passed, 2 skipped | гонится после коммита сводки (заметка 5) — итог в финальном сообщении |

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py`. Изменения:
  - ввоз `DYNAMIC_CONSTRUCT_EXCEPTIONS`, `DYNAMIC_CONSTRUCT_KINDS`, `DYNAMIC_KIND_DEFERRED_CALL`, `DYNAMIC_KIND_REFLECTION_VALUE`;
  - константы защиты;
  - `_channel_places`, `RoundTenBannedForm`, `ROUND_TEN_BANNED_FORMS`, трасер и правило таблицы;
  - `NAMED_COST_MECHANISM_CASES` и правило;
  - `REFUTED_CARRIER_COST_CLAIM` и правило шапки;
  - помощник обхода защиты, живое правило и контроль;
  - шапка.

  Предикаты распознавания, прежние таблицы, матрица и реестр не тронуты.

## Decisions Made

- **Трасер связан с таблицей.** Канал стоит с 16-53, поэтому трасер, утверждающий только находки канала, был бы зелёным уже на RED. Второе утверждение проверяет закрепку формы V10-1 строкой таблицы того же вида. Это то, что поставляет GREEN задачи 1.
- **RED задачи 2 — заглушка.** План предлагал ввоз помощника внутри тела правила. Заглушка, возвращающая `[]`, даёт падение утверждением с литералом, а не `ImportError`. Это тот же приём, что у RED-заглушки канала в 16-53.
- **Пустые таблицы на RED.** Пустые `ROUND_TEN_BANNED_FORMS` и `NAMED_COST_MECHANISM_CASES` на RED дают skipped. Строки цены зелёные с первого прогона, это закрепки: предикат не правится, и падения утверждением, о котором говорит `<tdd_notes>`, у строк цены быть не может без искусственного правила.
- **Список С1 — из таблицы 16-56.** Его берёт и сосед 16-54. Абзац согласования цитирует группы С1 (21 запрет) и С2 (13) из `16-56-PLAN.md` `<scope_note>`, а не 15 номеров текста плана 16-55.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Две формы снятия слушателя сверх плана**
- **Found during:** Задача 2 (прототип помощника).
- **Issue:** Буквальное правило «получатель с последним именем `event`» пропускает `from sqlalchemy import event as sa_event; sa_event.remove(…)` и `from sqlalchemy.event import remove`. Это то же выключение защиты.
- **Fix:** `_event_receivers` собирает псевдонимы ввоза модуля событий; ввоз `remove` из `sqlalchemy.event` считается находкой. Добавлены две строки контроля: `an-aliased-event-module-remove`, `an-imported-event-remove`.
- **Verification:** обе красны на RED `d1f35e6f`, зелены на GREEN `d9ea00c2`; живое дерево — 0.
- **Committed in:** `d1f35e6f`, `d9ea00c2`.

**2. [Rule 1 - Truthfulness] Механизм цены уже фразы плана**
- **Found during:** Задача 3 (замер до текста).
- **Issue:** Истина 4 плана относит к «двойкам» и `functools.partial(<API>, …)`, связанный с последним именем вызова-носителя. Замер: `to_thread = functools.partial(setattr, other)` и `… (set_committed_value, other)` дают ОДНУ находку. Пару `partial` даёт только под именем самого применения `f(MessengerAccount.phone)` (цена kw). `Thread(target=f, …)` и `Timer(1.0, f, …)` тоже дают одну.
- **Fix:** абзац цены и комментарий `NAMED_COST_CASES` называют механизм по замеру. Формы вне таблицы помечены «строками не закреплён»: строки не добавлены, потому что приёмка задачи 2 требует ровно `(12, 3)`.
- **Committed in:** `6b5ab496`.

**3. [Rule 1 - Truthfulness] Пункт (1) границы: `setattr(self, "f", api)` — не конструкция канала**
- **Found during:** Задача 3 (замер `proto_boundary.py`).
- **Issue:** План велел написать, что все три формы пункта (1) — `setattr(self, "f", api)`, `globals()["f"] = api`, `vars(obj)["f"] = api` — «с плана 16-53 конструкции канала». Замер показал иное. Канал находит только `globals()` / `vars()`, вид «пространство имён». `setattr` с литеральным именем в позиции вызова канал не судит.
- **Fix:** пункт (1) и раздел запрета говорят это прямо. Дальнейшее — в «Открытой находке» ниже.
- **Committed in:** `6b5ab496`.

### Расхождения замера с планом (замер выигрывает; строк и утверждений не убавлено)

- **Контроль обхода — 8 строк, а не 6.** Причина — п. 1 выше. Выборка задачи 2 — 27 passed, а не «≥ 25». RED задачи 2 — `8 failed`.
- **Вид у строк формы.** Строки несут полный измеренный список находок, а не одну. Например, у `wr33-getattr-under-run-in-executor` вторая находка — поданный `setattr` на строке 10. Вид связывания всюду совпал с планом.
- **Прежний предикат.** Он ловит 2 из 10 форм: `wr33-getattr-under-a-partial-wrapper` и `v10-1-function-binds-a-methodcaller-class-binds-setattr`, по одной находке. Ревью и верификатор писали «ноль», но для других написаний; справочно, без утверждения.
- **Пункт (5).** `instance_dict(account)[…] = …` канал не судит, и защита его не видит. Шапка говорит «нет и по-прежнему не запись». `del` / `delattr` / `del_attribute` отказывают событием `remove`: замер на объекте модели.
- **Живое дерево — 106, как в замере оркестратора.** Правило обхода на нём — 0.

### Подстановки исполнения

- Каждая проверка `python -c` из `<automated>` / `<acceptance_criteria>` записана дословно в `.pytest_cache/checks/` и исполнена с `PYTHONPATH=.`:
  - `t1_rows.py`, `t2_accept.py`, `base_rows.py`, `predicates.py`;
  - сверх плана — `base_extra.py`.

  Эталон `c9da79b2` извлечён простой командой `git show … > .pytest_cache/r10_base_writer.py`. Цепочка `git show … && python -c` плана разбита на два шага.
- `writer_live.py` скопирован из scratchpad оркестратора в `.pytest_cache/checks/`.
- Журнал базы плана — `.pytest_cache/gsd-plan-head-before-16-55`: запись в `.git/worktrees/…` песочница запрещает. `commits` измерен `git rev-list --count d9b38e21..HEAD` и равен 6.
- `uv run` при первом запуске создал `.venv` в worktree; каталог gitignored.
- `graphify update .` в worktree не запускался: `graphify-out/` нет, граф пересобирает оркестратор после слияния. Ориентация шла через `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Полный `just test` не запускался (заметка 4): его гонит пост-мердж гейт оркестратора.
- Запись в `.planning/WINDOWS.md` не делалась: единственная запись в `.planning/` — эта сводка (заметка 5). Открытая находка передаётся сводкой и финальным сообщением.

**Total deviations:** 3 auto-fixed — 1 Rule 2, 2 Rule 1 (правдивость шапки по замеру) — плюс названные расхождения счёта и подстановки.
**Impact on plan:** правки расширяют закрытое и делают тексты правдивыми. Ни одно правило плана не сужено. Общий модуль, гейт приватности, паритет и продуктовый код не тронуты.

## Открытая находка (вынесена владельцу и оркестратору; закрытие — вне файлов плана)

Держатель, связанный вызовом с литеральным именем, — запись, которую сегодня не судит ни один рубеж:

```python
class B:
    def __init__(self, s):
        setattr(self, "f", s.bulk_update_mappings)
    def run(self, x):
        self.f(MessengerAccount, [{"id": 1, "phone": x}])
```

- **Канал.** Находок нет. `setattr` в позиции вызова с литеральным именем — не вид перечня; `s.bulk_update_mappings` — значение, а не `getattr`-строка.
- **Прежний предикат.** Находок нет: пункт (1) границы, поток данных через контейнер объекта (с плана 16-27).
- **Защита на исполнении.** Не видит: `bulk_*_mappings` лежит за её границей. То же с `set_committed_value`, но он не пишет базу.
- **Исполнение через соединение.** `setattr(self, "f", conn.execute)` с литеральным SQL ловит прежний вид 5, сырой SQL.

Это исключение из обещания свойства 1 О-23 (а): «в коде нет конструкции, которую гейт не умеет судить». Шапка называет его открытой находкой, а не принятой границей. Закрыть можно так: канал краснит `setattr` / `getattr` с литеральным именем при значении — пишущем API гейта (`BANNED_GETATTR_NAMES`), или вообще любой `setattr(<self/cls>, "<имя>", <значение>)`. Это правка `tests/phone_gate_grammar.py`, общего для обоих гейтов, и вероятно — решение владельца о перечне видов. Живое дерево таких конструкций не содержит: канал и правило писателя дают 0.

## Issues Encountered

- Первая запись RED задачи 2 дала `INVALID_RED no_target_test_failure`, потому что у параметризованного правила не было точного имени цели. Её переписали с точными именами — `task2`, `task2b`; повторного прогона не понадобилось, улика та же.

## Known Stubs

Нет. RED-заглушка `runtime_guard_bypasses` снята GREEN `d9ea00c2`.

## Threat Flags

Нет новых поверхностей: изменён только тестовый гейт. Угрозы T-16-126 (формы раунда 10), T-16-127 (вход в разрешение и снятие слушателя) и T-16-128 (цена) закрыты строками и правилами выше. Для T-16-126 есть остаток — открытая находка выше.

## Для следующих волн

- **16-56.** Хэши GREEN:
  - WR-33, сторона писателя — «fa3cfdfc»;
  - WR-34, задачи 2–3 — «d9ea00c2», «6b5ab496»;
  - темы `feat(16-55): …` — дословно выше.

  Открытую находку стоит назвать в диспозиции WR-33 / в карте истины 18 или вынести владельцу.
- **16-54.** Абзац согласования этого гейта цитирует ту же таблицу 16-56 (С1 — 21 запрет, С2 — 13).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Свойства 1, 3, 4 О-23 (а) на стороне писателя исполнены строками, правилом входа в защиту и шапкой. Есть одно исключение из свойства 1 — открытая находка. Фаза по-прежнему `gaps_found` до верификации партии раунда 10.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-23*

## Self-Check: PASSED

- FOUND: `tests/test_application/test_phone_single_writer_gate.py`, эта сводка.
- FOUND (ancestors of HEAD): `0188f348`, `fa3cfdfc`, `d1f35e6f`, `d9ea00c2`, `87780baa`, `6b5ab496`.
- Шлюз TDD: на каждую задачу `test(16-55)` идёт перед `feat(16-55)`; RED-улики — `RED_EVIDENCE_OK`.
