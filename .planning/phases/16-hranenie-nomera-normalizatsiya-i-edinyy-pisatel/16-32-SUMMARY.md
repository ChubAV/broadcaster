---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 32
subsystem: testing
tags: [ast, phone, privacy-gate, carrier-semantics, shared-grammar, tdd, wr-19, wr-20, in-15]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль `tests/phone_gate_grammar.py` (16-27, 16-29, 16-31), гейт приватности 16-08…16-31, правило-паритет 16-29, многозначные `methodcaller` 16-31"
provides:
  - "общий модуль: `LITERAL_CONTAINER_WRAPPERS`, `UNJUDGED_ELEMENT`, `expanded_arguments`, `forwarded_arguments`, `iterable_elements`, `elementwise_arguments`, `ReferenceArguments`, `literal_keyword_arguments`, `reference_arguments`, `getattr_literal` (`getattr_as_attribute` на нём), поле `ReferenceCarrier.element`, места `{positional}` и `{keywords}` в `binding_form_source`"
  - "гейт приватности: `_carried_log_calls` и `_applied_log_methodcaller` на `reference_arguments`; свои `_iterable_elements` и `_getattr_literal` сняты; `ModuleLogNames.carrier_wrappers`; трасер `test_a_planted_log_reference_handed_to_a_thread_target_reddens_the_gate`; 14 строк `NEGATIVE_CONTROLS`, 4 строки `POSITIVE_CONTROLS`; шапка с общим правилом носителя, ценой, границей и летописью WR-19 / WR-20"
affects: [16-33, 16-34, 16-35, phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 20690
  tasks: 3
  commits: 10
plan_head_before: 3ffd946e6f9939cf9cc3249df5b063196fc1b484
plan_head_after: 5e57325d243a6d8578a132e709d41b2296ce6047

tech-stack:
  added: []
  patterns:
    - "Семантика носителя ссылки — функции общего модуля, которые не знают ни журнала, ни API: предикат ссылки (`is_reference`) и не-носители (`not_carriers`) подаёт гейт"
    - "Общее правило именованного аргумента О-14 (а): литеральный кортеж / список — позиционные аргументы ссылки, литеральный словарь / `dict(…)` / пары `**{…}` — именованные, прочие — как есть; ключи API не перечисляются"
    - "Применённый `X(…)` в `X(…)(…)` носителем не судится — его судит применение (одна находка на место)"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "`reference_arguments` пишется по семантике гейта писателя (`*`-распаковка, применённый `X(…)(…)`, поэлементный `map` с позициями, обёртка итерируемой) и дополнена: если в применённой обёртке ссылки нет, носитель — само применение со своими аргументами (`make_runner()(logger.info, …)`)"
  - "Общее правило литеральных аргументов применяется и к именованным аргументам применения обёртки; `skip` у `literal_keyword_arguments` — узел самой ссылки (именованный аргумент или пара `**{…}`)"
  - "Получатель `methodcaller` у носителя — первый аргумент, который носитель подаст ссылке, и (цикл 1) первый элемент литерального кортежа / списка, поданного первым (`pool.apply_async(mc, [logger])`)"
  - "Обёртка носителя, связанная с именем (`w = partial(asyncio.to_thread, logger.info); w(…)`), судится как применённая обёртка (цикл 2); у гейта писателя та же форма даёт `[]` — передано плану 16-34"

patterns-established:
  - "Самопроверка оси «как подана ссылка»: способ подачи × значение опознания × получатель × метод × форма аргумента × форма связывания; граница (аргументы нелитералом) — ноль находок; не-журнальная ссылка — ноль вызовов"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Подложенный `threading.Thread(target=logger.info, args=(…, account.phone)).start()` в синтетическом `app/` краснит гейт приватности с файлом, строкой и предметом"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_log_reference_handed_to_a_thread_target_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять форм WR-19 / WR-20 этого гейта, закрепки общего правила, `methodcaller` у любого носителя и две формы самопроверки — строки NEGATIVE_CONTROLS с находкой `phone`; идиома Celery, ссылка без аргументов, обёртка под именем с не-журнальной ссылкой — не вызов журнала; член `send_log` по ключу — вызов без находок"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half"
        status: pass
    human_judgment: false
  - id: D3
    description: "Семантика носителя — функции общего модуля; копий `_iterable_elements` / `_getattr_literal` в гейте приватности нет; шесть будущих строк `REFERENCE_CARRIERS` — 360 ячеек без промахов; гейт писателя и паритет зелёные на общем модуле"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "task-2 <automated> #2 (OK 360) и #3 (OK) плана 16-32"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка: носитель без сужающей оговорки, общее правило, шесть будущих носителей поимённо, цена `app/worker/tasks.py:453`, граница «аргументы нелитералом — поток данных», летопись WR-19 / WR-20; живые деревья 225 / 68 / 93, находок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
    human_judgment: false

duration: 42min
completed: 2026-10-16
status: complete
---

# Phase 16 Plan 32: Семантика носителя ссылки в общем модуле, общее правило именованного аргумента — Summary

**Где стоит ссылка и какие аргументы носитель ей подаст, теперь решают функции общего модуля `tests/phone_gate_grammar.py` (`reference_arguments`, `literal_keyword_arguments`, `iterable_elements`, `getattr_literal`). Гейт приватности переведён на них и снял свои копии. Ссылка на журнал, поданная любым именованным аргументом, литеральной `*`-распаковкой или внутри применённой обёртки носителя, краснит гейт. Литеральные аргументы того же вызова судятся общим правилом О-14 (а), ключи API не перечисляются. `methodcaller` работает у любого носителя. Самопроверка прошла 99 600 форм композицией, нашла два класса, оба закрыты циклами RED/GREEN.**

## Performance

- **Duration:** ≈42 мин
- **Started:** 2026-10-16T09:40:44Z
- **Completed:** 2026-10-16T10:22:05Z
- **Tasks:** 3 (плюс 2 цикла самопроверки)
- **Files modified:** 2

## Accomplishments

- Общий модуль, новые функции (у каждой докстринг: что делает, откуда семантика, какое ревью):
  - `LITERAL_CONTAINER_WRAPPERS`, `UNJUDGED_ELEMENT`;
  - `expanded_arguments`, `forwarded_arguments`, `iterable_elements` (раскрывает обёртку `list([…])`), `elementwise_arguments` — по смыслу копий гейта писателя;
  - `ReferenceArguments` (NamedTuple `reference`, `args`, `keywords`);
  - `literal_keyword_arguments(keywords, skip)` — общее правило О-14 (а);
  - `reference_arguments(call, is_reference, not_carriers)` — ссылка позицией, `*[…]` / `*(…)`, любым именованным аргументом или парой `**{…}`, в применённой обёртке `X(…)(…)`; у `map` — по позициям;
  - `getattr_literal` — один читатель getattr-литерала (строгая форма); на нём `getattr_as_attribute`.
- Общий модуль, словарь матриц: поле `ReferenceCarrier.element` (умолчание `"[{}]"`), места `{positional}` и `{keywords}` в `binding_form_source`. Строки `REFERENCE_CARRIERS` не добавлялись: их впишет план 16-34.
- Гейт приватности:
  - `_carried_log_calls` и `_applied_log_methodcaller` построены на `reference_arguments`;
  - применённый `X(…)` в `X(…)(…)` носителем не судится (`_applied_carriers`), одна находка на место;
  - свои `_iterable_elements` и `_getattr_literal` сняты, `_member` берёт `getattr_literal`;
  - `ModuleLogNames.carrier_wrappers`: обёртка носителя, связанная с именем (цикл 2);
  - получатель `methodcaller` — и первый элемент литеральной последовательности (цикл 1).
- Строки: трасер, `NEGATIVE_CONTROLS` +14 (7 задачи 1, 4 задачи 2, 1 цикла 1, 2 цикла 2), `POSITIVE_CONTROLS` +4 (3 задачи 1, 1 цикла 2). Прежние 102 / 44 строки на `4cd68671` — на месте.
- Шапка:
  - «ПО НОСИТЕЛЮ ССЫЛКИ» — без оговорки «позиционным аргументом без `*`»;
  - общее правило литеральных аргументов;
  - шесть будущих носителей поимённо и обёртка `list([…])`;
  - функции общего модуля, обёртка носителя под именем;
  - цена `app/worker/tasks.py:453`, живые числа 225 / 68 / 93;
  - пункт границы «аргументы нелитералом — поток данных»;
  - летопись WR-19 / WR-20.

## Task Commits

1. **Задача 1 (трасер): `reference_arguments` с общим правилом, гейт приватности на нём** — `1bebbbf7` (test, RED), `c6953017` (feat, GREEN).
2. **Задача 2: `methodcaller` у любого носителя, `getattr_literal`, копии сняты, `{positional}` / `{keywords}`** — `fd319752` (test, RED), `50d6e5cf` (feat, GREEN).
3. **Задача 3: шапка** — `534e1ca8` (test, RED), `8a28d2e7` (feat, GREEN).
4. **Самопроверка, цикл 1: `methodcaller` с литеральным списком аргументов** — `3477554f` (test, RED), `6231a0b3` (feat, GREEN).
5. **Самопроверка, цикл 2: обёртка носителя под именем** — `111ecad1` (test, RED), `5e57325d` (feat, GREEN).

**Plan metadata:** коммит `docs(16-32)` с этой сводкой. Первый коммит плана — `1bebbbf7`. `git log --format=%h 1bebbbf7^..HEAD -- tests/test_application/test_phone_single_writer_gate.py` печатает пустую строку: модуль гейта писателя план не правил.

Гейт трасера после задачи 1: режим `end-of-phase`, проверка только `<automated>`. Все три команды `<verify>` прогнаны повторно и зелёные (`214 passed`, строка живых деревьев 225 / 68 / 93, `520 passed`), после чего план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). У каждого есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех пяти записях.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_log_reference_handed_to_a_thread_target_reddens_the_gate` | `1 failed, 213 deselected` | «ссылка на метод журнала, поданная именованным аргументом, не опознана» | цель исполнилась: обход нашёл файл, `calls 0`, находок `[]`. В соседнем прогоне строк 8 failed: трасер, 6 из 7 новых `NEGATIVE_CONTROLS` и строка `send-log-member-…`. `timer-args-log-reference` зелёная до GREEN — план называл её «ловилась случайно» |
| Задача 2 | `test_a_number_handed_to_a_python_log_call_is_found[methodcaller-handed-to-map-in-a-wrapped-iterable]` (`-k "methodcaller and (wrapped or thread or starred)"`) | `4 failed, 214 deselected` | «номер в вызове журнала не найден» | все четыре новые строки `methodcaller-*` дали `[]` |
| Задача 3 | `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 217 deselected` | «шапка гейта приватности не называет носителя ссылки» | 13 недостающих мест, включая сужающую оговорку |
| Цикл 1 | `…[methodcaller-handed-with-a-literal-argument-list]` | `1 failed, 218 deselected` | «номер в вызове журнала не найден» | `pool.apply_async(mc, [logger])` дал `[]` |
| Цикл 2 | `…[carrier-wrapper-bound-to-a-name-log-reference]` (`-k "carrier-wrapper-bound or header_names"`) | `3 failed, 1 passed, 218 deselected` | «номер в вызове журнала не найден» (и «шапка гейта приватности не называет носителя ссылки») | обе строки обёртки под именем дали `[]`; шапка её не называла; строка `POSITIVE_CONTROLS` зелёная |

## Самопроверка исполнителя (задача 3; урок 16-18, 16-23, 16-29; О-14 (а))

Скрипт `.pytest_cache/1632_selfcheck.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный и работает под общим `flock`. Каждая форма подаётся в `python_log_offences(…, "app/x.py")`. Под заявлением находка обязана быть непустой и называть предмет формы аргумента.

**Оси:**
- **Способы подачи (50 на заходе 1, 52 на заходе 2):**
  - позицией (`runner.call(R, …)`), после исполнителя (`run_in_executor(None, R, …)`);
  - `*[…]` и `*(…)` одной ссылкой, после других аргументов и целиком (`run_in_executor(*[None, R, …])`);
  - применённая обёртка `functools.partial(asyncio.to_thread, R)(…)`, она же под псевдонимом присваиванием и ввозом;
  - `Timer(1.0, R, args=(…), kwargs={…})`, позиционный литеральный список `pool.apply_async(R, […], {…})`;
  - `map` с элементами `[…]`, `list([…])`, `tuple([…])`, `iter([…])`;
  - именованная ссылка `fn=`, `target=`, `function=`, `initializer=`, выдуманные `job=`, `payload=` × 7 форм аргументов: позиционные носителя, литеральный кортеж, список, `dict(…)`, пары `**{…}`, смесь, выдуманные ключи аргументов (`data=`, `options=`);
  - заход 2 — обёртка носителя под именем (`w = partial(asyncio.to_thread, R); w(…)`) и под атрибутом (`self.w = partial(loop.run_in_executor, None, R); self.w(…)`).
- **Значения опознания (64):** атрибут, `getattr`-строка, `partial` с привязкой, `methodcaller` — каждое × 5 получателей (`logger`, `self.log`, `logging`, `structlog.get_logger()`, `logger.bind(a=1)`) × 3 метода (`info`, `ainfo`, `_log`); плюс `print`, функция `logging` из ввоза `as`, `bind_contextvars` атрибутом и ввозом `as`.
- **Формы аргумента (5):** `phone=`, `account.phone`, f-строка, ключ словаря, литерал `+79991234567`. У форм связывания, кроме `direct`, — две: позиционная и именованная.
- **Формы связывания:** 12 `BINDING_FORMS`, включая `rebound*` с подменой того же вида.
- **Граница:** аргументы нелитералом (`args=row, kwargs=opts`, `*rows, **opts`, `*rows` перед именованной ссылкой) — находок 0.
- **Контроль:** не-журнальная ссылка (`noop`, `helper.noop`, `getattr(helper, "noop")`, `partial(helper.noop, …)`, `methodcaller` с получателем `other`) — вызовов журнала 0.

| Заход | HEAD, время (UTC) | Под заявлением: подано / `[]` | Граница: подано / с находкой | Не-журнальная: подано / с вызовом | Зонд вне буквы | Закрыто коммитами |
|-------|-------------------|-------------------------------|------------------------------|-----------------------------------|----------------|-------------------|
| 1 | `8a28d2e7`, 2026-10-16 ≈09:58 | 96 144 / **405** — один класс: `methodcaller` у `pool.apply_async(mc, [logger], {})`; получатель — элемент литерального списка, поданного первым | 896 / 0 | 1 181 / 0 | обёртка носителя под именем: 320 / **320** без находки | `3477554f` / `6231a0b3` (класс 405); `111ecad1` / `5e57325d` (зонд: форма — `partial(…)(…)`, разделённое связыванием, а каждое связывание судится, значит она под заявлением) |
| 2 (итог) | `5e57325d`, 2026-10-16 10:14 | **99 600 / 0** | **896 / 0** | **1 223 / 0** | — (обёртка под именем вошла в способы подачи) | — |

**По осям на заходе 2:**
- формы связывания: `direct` — 18 684, каждая из прочих 11 — 7 356;
- способы подачи: каждый позиционный — 1 728; каждая обёртка `map` — 1 140; именованные (6 ключей × 7) — 72 576 вместе;
- значения: атрибут, `getattr`, `partial` — по 23 175; `methodcaller` — 23 895; каждое без получателя — 1 545;
- формы аргумента: позиционная 45 312, именованная 42 960, f-строка, ключ словаря, литерал — по 3 776.

Итого подано 99 600 форм под заявлением, порог плана — 5 000. На итоговом дереве промахов ноль.

У гейта писателя та же обёртка под именем тоже даёт `[]` (`w = functools.partial(asyncio.to_thread, setattr); w(account, "phone", x)`; на месте — находка). Правка модуля гейта писателя этим планом запрещена, поэтому форма передаётся плану 16-34 (см. отступление 5).

## Живые деревья и сверка множеств вызовов

Команда `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -s -k live_trees` печатает:

`Python-половина гейта приватности: app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0`

Скрипт `.pytest_cache/1632_callset_diff.py` сверяет множества распознанных вызовов `(строка, столбец)` по каждому из 106 файлов. База — гейт на `4cd68671` (копия `.pytest_cache/base_privacy_gate_4cd68671.py`) с общим модулем той же ревизии. Сверка гонялась на исходном дереве (0 / 0), после задачи 1, задачи 2, циклов 1 и 2:
- **added 1:** `app/worker/tasks.py` (453, 23) — `build_dispatch_task(ad=ad, group=group, account=account, schedule_id=send_log.schedule_id)`. Это член записи `SendLog` под именем `send_log` (шаблон имени журнала D-17), поданный именованным аргументом рядом с другими. Цена строгости, находок нет. Ровно то место, которое называл план;
- **removed 0:** прочие 105 файлов совпадают;
- итого вызовов: база 385, сейчас 386.

`PHONE_LOG_EXCEPTIONS == {}`, `PHONE_LOG_EXCEPTIONS_CEILING == 0`. JS-половина не правилась.

## Files Created/Modified

- `tests/phone_gate_grammar.py`:
  - раздел «Семантика носителя ссылки»: функции и таблицы выше, частные `_callee_name`, `_literal_named_pairs`, `_literal_sequence`, `_keyword_references`, `_carried_by`;
  - `getattr_literal`, `getattr_as_attribute` на нём;
  - `ReferenceCarrier.element`, `{positional}` / `{keywords}` в `binding_form_source`.
- `tests/test_phone_privacy_gate.py`:
  - носитель и `methodcaller` на общих функциях, `_not_carriers`, `_applied_carriers`, `_carrier_wrappers` / `ModuleLogNames.carrier_wrappers`;
  - копии сняты, ввоз из общего модуля дополнен (`getattr_literal`, `iterable_elements`, `reference_arguments`);
  - трасер, строки контролей, правило шапки, шапка.

## Decisions Made

- **Фолбэк применённой обёртки.** Если в `X(…)` у `X(…)(…)` ссылки нет, носитель — само применение со своими аргументами (`make_runner()(logger.info, …)`). План описывал только первую ветку. Заявление «носитель — любой вызов» без фолбэка оставляло бы форму `[]`.
- **Общее правило — и к именованным аргументам применения.** `partial(Thread, target=…)(args=(…))` подаёт ссылке литеральный кортеж применения так же, как носителя.
- **`skip` у `literal_keyword_arguments` — узел самой ссылки,** а не `ast.keyword`. Так одним параметром пропускается и именованная ссылка, и пара `**{"fn": ref}`.
- **Ввоз `ELEMENTWISE_CARRIERS` и `REFERENCE_KEYWORDS` оставлен** (`# noqa: F401`). Правилом носителя ключ больше не читается, но `REQUIRED_SHARED_NAMES` правила-паритета требует `REFERENCE_KEYWORDS`. Константы выводит план 16-34.
- **Шапка называет шесть будущих носителей уже сейчас.** Когда 16-34 впишет строки `REFERENCE_CARRIERS`, правило шапки, обходящее имена, уже будет зелёным.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Фолбэк носителя у применённой обёртки без ссылки**
- **Found during:** задача 1, при проектировании `reference_arguments`.
- **Issue:** по букве шага (1) плана источник ссылки у `X(…)(…)` — только `X(…)`. Тогда `make_runner()(logger.info, "x", account.phone)` не судился бы ни как носитель, ни как применение.
- **Fix:** если в `X(…)` ссылки нет, носителем судится само применение. Докстринг называет правило.
- **Files modified:** `tests/phone_gate_grammar.py`.
- **Verification:** живые деревья — новое место ровно одно (tasks.py), удалённых нет; гейт писателя и паритет зелёные.
- **Committed in:** `c6953017`.

**2. [Rule 1 - Bug] Путь носителя `methodcaller` у применённого `X(…)`**
- **Found during:** задача 2.
- **Issue:** правило «`X(…)` в `X(…)(…)` носителем не судится» касалось только `_carried_log_calls`. У `partial(to_thread, mc, logger)()` внутренний вызов и применение дали бы два синтетических вызова на одном месте.
- **Fix:** параметр `as_carrier` у `_applied_log_methodcaller`. Прямое применение `methodcaller(…)(R)` судится всегда, путь носителя у применённого `X(…)` — нет.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Committed in:** `50d6e5cf`.

**3. [Rule 2 - Missing critical] Самопроверка, цикл 1: `methodcaller` с литеральным списком аргументов**
- **Found during:** задача 3, самопроверка, заход 1 (405 форм).
- **Issue:** `pool.apply_async(operator.methodcaller("info", …, account.phone), [logger])` зовёт `logger.info(…)`. Первым аргументом ссылке подан список, и получатель не опознавался.
- **Fix:** первый элемент литерального кортежа / списка, поданного ссылке первым, — тоже кандидат в получатели. Его читает общий `iterable_elements`. Цена — в сторону лишней находки.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Verification:** строка `methodcaller-handed-with-a-literal-argument-list` зелёная; заход 2 — 0 промахов; живые деревья прежние.
- **Committed in:** `3477554f` (RED), `6231a0b3` (GREEN).

**4. [Rule 2 - Missing critical] Самопроверка, цикл 2: обёртка носителя, связанная с именем**
- **Found during:** задача 3, зонд захода 1 (320 форм `[]`).
- **Issue:** `w = functools.partial(asyncio.to_thread, logger.info); w("x %s", account.phone)` — это применение `partial(…)(…)`, разделённое связыванием. Шапка называет и применённую обёртку, и правило «каждое связывание судится», а форма давала `[]`.
- **Fix:** `ModuleLogNames.carrier_wrappers` — имена, связанные общей грамматикой с `partial(<носитель>, <ссылка на журнал или methodcaller>, …)`, с цепочками, до неподвижной точки. Вызов `w(…)` судится как применение этой обёртки через `reference_arguments`. Шапка называет форму, правило шапки её требует.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Verification:** две строки `NEGATIVE_CONTROLS` и одна `POSITIVE_CONTROLS`; заход 2 — 0 промахов (3 456 форм обёртки под именем и атрибутом); живые деревья прежние.
- **Committed in:** `111ecad1` (RED), `5e57325d` (GREEN).

### Передано плану 16-34 (отложено, `deferred-items.md` в этой волне не создавался — orchestrator_notes 5)

**5. Гейт писателя: обёртка носителя под именем.** `w = functools.partial(asyncio.to_thread, setattr); w(account, "phone", x)` у гейта писателя даёт `[]`, на месте — находка «запись атрибута по имени» (зонд 2026-10-16, дерево `5e57325d`). Правка модуля гейта писателя этим планом запрещена. Плану 16-34 при переводе гейта писателя на `reference_arguments`: применить общую семантику и к имени, связанному с `partial(<носитель>, <ссылка>, …)` (у гейта приватности — `_carrier_wrappers`). Иначе это асимметрия, которую запрещает О-12 (а).

### Отклонения чисел план → замер (замер побеждает, строки не снимались)

| Что | План | Замер | Почему |
|-----|------|-------|--------|
| гейт приватности после задачи 1 | ≥ 214 | 214 | — |
| три модуля после задачи 2 | ≥ 736 | 738 (218 + 14 + 506) | гейт писателя 506, а не 504 (+2 строки самопроверки 16-31) |
| гейт приватности на итоговом дереве | ≥ 218 | 222 | +4 строки циклов 1 и 2 |
| `NEGATIVE_CONTROLS` / `POSITIVE_CONTROLS` | 102 / 44 прежних | 117 / 49 (прежние 102 / 44 на месте, `OK 102 44`) | 16-31 +1 / +1; план +11 / +3; циклы +3 / +1 |
| оба гейта и паритет | 723 на базе | 742 | +19 правил гейта приватности |
| quick run фазы | 1127 на базе | 1146 | то же |

---

**Total deviations:** 4 исправлены автоматически (1 — Rule 1, 3 — Rule 2), 1 передан плану 16-34; плюс расхождения чисел, описанные выше.
**Impact on plan:** все правки — в файлах плана. Реестр исключений, потолок, прежние строки, JS-половина и модуль гейта писателя не тронуты.

## Замены команд (песочница worktree, хост)

- Критерий задачи 1 «прежние строки» (`git show` внутри `python -c`): эталон сохранён простой командой `git show 4cd68671:tests/test_phone_privacy_gate.py > .pytest_cache/base_privacy_gate_4cd68671.py`. Та же логика сравнения исполнена скриптом `.pytest_cache/1632_rows_check.py` над этой копией: `OK 102 44`.
- RED задачи 2 (`-k` со скобками под `flock`): песочница отказала. Та же команда записана в `.pytest_cache/1632_red2.sh` и запущена `flock … bash .pytest_cache/1632_red2.sh`.
- Проверка 360 ячеек (`python -c` под `flock`): песочница отказала. Проверка гонялась без `flock` — она лёгкая (360 форм, ниже порога 5 000 для блокировки). Самопроверка (99 600 форм) гонялась под `flock`.
- Сверка множеств вызовов: база загружается из копий `.pytest_cache/base_privacy_gate_4cd68671.py` и `.pytest_cache/base_grammar_4cd68671.py`.
- Полная суита (~5112 тестов, ~46 мин) не гонялась: её гонит пост-мердж гейт оркестратора на слитом дереве (вместе с правками 16-33).
- `graphify update .` не запускался: граф обновит оркестратор после слияния. Ориентация шла по `graphify query … --graph /source/broadcaster/graphify-out/graph.json` (только чтение).
- `.planning/WINDOWS.md`, `deferred-items.md`, STATE.md, ROADMAP.md, REQUIREMENTS.md не писались (orchestrator_notes 5). Отложенное — пункт 5 выше.

## Гейты на итоговом дереве (`5e57325d`, 2026-10-16, под `flock`)

- Task-1 `<automated>`: гейт приватности `222 passed`; строка живых деревьев — 225 / 68 / 93, находок 0; гейт писателя + паритет `520 passed`.
- Task-1 критерии: `grep -c` пяти функций и трасера — по `1`; общее правило — `OK 5`; прежние строки — `OK 102 44` (сейчас 117 / 49).
- Task-2 `<automated>`: три модуля `742 passed`; `OK 360`; копий нет, ввоз есть — `OK`. `grep -c "^def getattr_literal"` = 1, `grep -c "element"` = 21.
- Task-3 `<automated>`: гейт приватности `222 passed`; фразы шапки — `OK`; quick run фазы `1146 passed`. Реестр и потолок — `OK`.
- Оба гейта и паритет поимённо: `742 passed`.
- `tests/test_application`: `791 passed`.
- Сквозные гейты `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`: `576 passed` (2 мин 40 с). `tests/test_logging_config.py`: `3 passed`.
- `uv run python -m compileall -q app main.py tests`: код выхода 0.
- `scripts/prohibitions_census.py --check`: код выхода 0, «реестр: 837 строк, биекция с переписью — согласие». `tests/test_planning/test_plan_prohibitions_census.py`: `110 passed`.
- `tests/test_planning` гонится после коммита этой сводки, число — в финальном сообщении исполнителя.

## TDD Gate Compliance

- **RED:** `test(16-32)` — `1bebbbf7`, `fd319752`, `534e1ca8`, `3477554f`, `111ecad1`.
- **GREEN:** `feat(16-32)` — `c6953017`, `50d6e5cf`, `8a28d2e7`, `6231a0b3`, `5e57325d`.
- **REFACTOR:** не понадобился.
- Каждый RED предшествует своему GREEN; нарушений нет.

## Issues Encountered

Нет нерешённых. Оба класса самопроверки закрыты в плане; сторона гейта писателя для обёртки под именем передана плану 16-34 (пункт 5).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

План 16-34 может переводить гейт писателя на общую семантику:
- функции `reference_arguments`, `iterable_elements`, `elementwise_arguments`, `forwarded_arguments`, `getattr_literal`, `LITERAL_CONTAINER_WRAPPERS` готовы;
- шесть шаблонов строк `REFERENCE_CARRIERS` гейт приватности проходит во всех 360 ячейках: поле `element`, места `{positional}` и `{keywords}` готовы;
- шапка гейта приватности уже называет шесть имён;
- остаётся форма из пункта 5: обёртка носителя под именем у гейта писателя;
- 16-34 должен сохранить многозначные карты 16-31 и сведение толкований по месту.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-16*

## Self-Check: PASSED

- FOUND: tests/phone_gate_grammar.py, tests/test_phone_privacy_gate.py
- FOUND (ancestors of HEAD): 1bebbbf7, c6953017, fd319752, 50d6e5cf, 534e1ca8, 8a28d2e7, 3477554f, 6231a0b3, 111ecad1, 5e57325d
