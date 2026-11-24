---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 27
subsystem: testing
tags: [ast, phone, single-writer-gate, binding-grammar, tdd, wr-14]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт единственного писателя планов 16-09…16-22 (`_module_aliases`, `_api_aliases`, `_api_alias_targets`, `_referenced_calls`, `_bound_reference`, `LITERAL_FORM_CASES`, `LEGITIMATE_CASES`)"
provides:
  - "tests/phone_gate_grammar.py — общая грамматика связывания и перечень носителей ссылки обоих гейтов номера (Binding, binding_pairs, getattr_as_attribute, module_bindings, binding_name, BindingForm, BINDING_FORMS, OutOfGrammarForm, OUT_OF_GRAMMAR_BINDING_FORMS, REFERENCE_KEYWORDS, ELEMENTWISE_CARRIERS, ReferenceCarrier, REFERENCE_CARRIERS, IdentificationValue, binding_form_source)"
  - "гейт писателя на общей грамматике: распаковка (и со звёздной целью), `:=`, `self.<x>` / `cls.<x>` в любом методе, тело класса, `getattr`-строка как атрибут; связанный `partial`; поэлементный `map`; получатель `methodcaller` у любого применения; псевдоним носителя через атрибут"
  - "правило-матрица оси B `test_every_binding_form_of_a_writer_api_alias_is_judged` (9 форм × 5 значений × 6 способов = 270 ячеек) и правило шапки `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier`"
affects: [16-28, 16-29, 16-30, phase-18, phase-19, phase-20]

actuals:
  tokens: 18757
  tasks: 3
  commits: 15
plan_head_before: e6ab315252d0612b4dc59aa160e54411a34a3ad2
plan_head_after: 0ea91ee825506b8c43c35f0990c4311d98987976

tech-stack:
  added: []
  patterns:
    - "Общий нетестовый модуль `tests/phone_gate_grammar.py`: оба гейта ввозят грамматику связывания и перечень носителей, паритет — по построению"
    - "Ячейка матрицы собирается одной функцией `binding_form_source(form, value, carrier)` для обоих гейтов и самопроверок"
    - "Самопроверка — композиция осей, для форм вне грамматики — сравнение с базой «то же, но имя не связано»"

key-files:
  created:
    - tests/phone_gate_grammar.py
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Локальная таблица гейта `BINDING_FORMS` (формы связывания ПАРАМЕТРА: positional/keyword/double-star/starred) переименована в `PARAMETER_BINDING_FORMS`: имя `BINDING_FORMS` занято общей таблицей, а правило-паритет 16-29 запрещает гейту присваивать `BINDING_FORMS` (id параметров не изменились)"
  - "Связанный `partial`, который модуль зовёт или подаёт, судится у использования, а не на месте связывания: иначе `w = partial(setattr, account, \"phone\"); w(x)` дал бы две находки; несвязанный и неиспользованный — как прежде, у себя"
  - "`methodcaller` судится по каждому получателю применения (прямое, вызов связанного имени, носитель со следующим аргументом, `map` — элементы первой итерируемой); без известного применения — как прежде, без получателя"
  - "Связывание вызовом или через пространство имён (`setattr(self, \"f\", api)`, `globals()[\"f\"] = api`, `vars(obj)[\"f\"] = api`) названо в пункте (1) границы с причиной «поток данных через контейнер», а не в `OUT_OF_GRAMMAR_BINDING_FORMS` (план фиксирует там ровно 2 строки)"

patterns-established:
  - "Псевдоним носителя опознания (`methodcaller`, `getattr`) переводится и через атрибут `<obj>.<псевдоним>` — по последнему звену, как псевдонимы пишущих API"
  - "Форма вне грамматики проверяется против базы с несвязанным именем: находка сверх базы значила бы, что связывание разрешено"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Класс-исполнитель скрипта дозаполнения с `self.bum = session.bulk_update_mappings` в `__init__` в синтетическом `scripts/` краснит гейт с файлом, строкой и видом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_method_bound_writer_alias_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Формы WR-14 (getattr-строка, распаковка с setattr / flag_modified / set_committed_value, `:=`, `self.bum =` в методе, getattr-строка в теле класса) — строки LITERAL_FORM_CASES, по одной находке ожидаемого вида"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ось B — правило-матрица 9 форм × 5 значений опознания × (прямой вызов и 5 носителей) = 270 ячеек, ноль промахов"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_binding_form_of_a_writer_api_alias_is_judged"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка гейта писателя называет общую грамматику, каждый носитель, формы вне грамматики с причиной; пункт (1) без пойманного связанного partial; заявление прежнее"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
    human_judgment: false
  - id: D5
    description: "Живое дерево app/ + scripts/ — 104 файла, 0 судимых находок; в писателе 6 сырых; реестр — ровно писатель; 152 / 68 прежних строк на месте"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: other
        ref: "plan 16-27 task 3 verify #2 (OK 6 104) and verify #2 of task 1 (OK 152 68 175 78)"
        status: pass
    human_judgment: false

duration: 46min
completed: 2026-10-14
status: complete
---

# Phase 16 Plan 27: Общая грамматика связывания и ось B гейта писателя — Summary

**Гейт единственного писателя теперь берёт связывания из общего модуля `tests/phone_gate_grammar.py`: он ловит пишущий API, связанный распаковкой (со звёздной целью тоже), `:=`, `self.<x>` / `cls.<x>` в любом методе, телом класса, `getattr`-строкой и `functools.partial`, а также ссылку, поданную `map` (поэлементно) и любому носителю. Ось B стала правилом-матрицей из 270 ячеек. Самопроверка композицией прошла 63 688 форм и нашла три класса промахов; все три закрыты циклами RED/GREEN.**

## Performance

- **Duration:** ≈46 мин
- **Started:** 2026-10-14T08:30:13Z
- **Completed:** 2026-10-14T09:16Z
- **Tasks:** 3 (плюс 4 цикла самопроверки)
- **Files modified:** 2 (1 новый)

## Accomplishments

- Новый модуль `tests/phone_gate_grammar.py` (pytest его не собирает, из `app/` ничего не ввозит). В нём грамматика (`module_bindings`, `binding_pairs`, `getattr_as_attribute`, `binding_name`), таблицы матриц (`BINDING_FORMS` 9, `OUT_OF_GRAMMAR_BINDING_FORMS` 2), перечень носителей (`REFERENCE_CARRIERS` 5, `ELEMENTWISE_CARRIERS`, перенесённый `REFERENCE_KEYWORDS`) и сборщик ячейки `binding_form_source`.
- Гейт писателя: `_module_aliases`, пред-фильтр `_api_aliases`, `_api_alias_targets` и, через них, псевдонимы модели и носителей работают на `module_bindings`. Новые `_partial_aliases` (связанный `partial`), поэлементный `map` (`_elementwise_arguments`), `_methodcaller_receivers` (получатель при любом применении). `_rename_aliases` переводит и `<obj>.<псевдоним>`.
- Трасер WR-14, правило-матрица оси B, правило шапки; строки: `LITERAL_FORM_CASES` 152 → 175, `LEGITIMATE_CASES` 68 → 78.
- Шапка: общий абзац называет грамматику и носителей, пункт (1) — цель `for`, `with … as` и связывание вызовом с причиной. Связанный `partial` перенесён в летопись, летопись WR-14 дописана. Заявление прежнее.

## Task Commits

1. **Задача 1 (трасер): общий модуль, связывания из него**: `c30b676c` (test, RED), `25f2bb5e` (feat, GREEN)
2. **Подготовка задачи 2**: `a12ad73c` (refactor: `BINDING_FORMS` гейта → `PARAMETER_BINDING_FORMS`)
3. **Задача 2: ось B, носители, `map`, связанный `partial`**: `5abe7a71` (test, RED), `8aaded0d` (feat, GREEN)
4. **Задача 3: шапка**: `45898dbd` (test, RED), `d9323cd0` (feat, GREEN)
5. **Самопроверка, цикл 1 — `methodcaller` с поздним получателем**: `4bb5ab4f` (test), `b8c84eb3` (feat)
6. **Самопроверка, цикл 2 — псевдоним носителя через атрибут**: `4c692d95` (test), `18e13784` (feat)
7. **Самопроверка, цикл 3 — распаковка со звёздной целью**: `175c9ab4` (test), `e5df9047` (feat)
8. **Самопроверка, цикл 4 — шапка: звёздная цель и связывание вызовом**: `aa756a96` (test), `0ea91ee8` (feat)

**Plan metadata:** коммит `docs(16-27)` с этой сводкой.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном `-k <цель>` с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored). По каждому циклу есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех семи записях.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_method_bound_writer_alias_reddens_the_gate` | `1 failed, 423 deselected` | «псевдоним пишущего API, связанный атрибутом в методе, не опознан» | цель исполнилась, гейт вернул `[]` |
| Задача 2 | `test_every_binding_form_of_a_writer_api_alias_is_judged` (все 9 форм) | `9 failed, 430 deselected` | «форма связывания пишущего API не опознана» | 76 промахов из 270 (4 у `direct`, по 9 у восьми форм): ячейки `map` и связанного `partial`, ровно как в замере планирования |
| Задача 3 | `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 439 deselected` | «шапка гейта писателя не называет общую грамматику связывания» | 11 недостающих мест шапки |
| Цикл 1 | 5 строк `methodcaller-*` | `5 failed, 10 passed` | «дала 0 находок вместо одной» | `__set__` / `__init__` без получателя |
| Цикл 2 | 4 строки `*-carrier-alias` | `4 failed, 4 passed` | «дала 0 находок вместо одной» | `self.mc(…)`, `K.attr(…)` не переводились |
| Цикл 3 | 2 строки `starred-tuple-*` | `2 failed, 39 passed` | «дала 0 находок вместо одной» | `binding_pairs` отказывал на `Starred` |
| Цикл 4 | правило шапки | `1 failed, 455 deselected` | «шапка гейта писателя не называет общую грамматику связывания» | 3 недостающих места |

## Самопроверка исполнителя (задача 3; урок 16-12, 16-17, 16-22; О-12 (а))

Скрипт `selfcheck.py` лежит в scratchpad и в репозиторий не коммитится. Он однопроцессный и потоковый (собрал ячейку → осудил → посчитал) и работает под общим `flock`. Скрипт подаёт `phone_write_offences(…, "scripts/x.py")` **композицию**, а не перечень. Под заявлением он требует ровно одну находку ожидаемого вида, предмет которой называет API и `phone`. Исключение — вызов псевдонима модели: предмет называет псевдоним, как в прежней строке `model-attribute-alias`. Для формы вне грамматики скрипт сравнивает находки с базой: та же ячейка, где имя не связано (`never_bound_fn`).

- **Формы связывания (19):** 9 `BINDING_FORMS`; 8 сверх таблицы — цепочка `g = f`, вложенная распаковка `(f, g), h = …`, список-цель `[f, g] = […]`, аннотированное `self.f: object =`, `:=` внутри comprehension, аннотированное в теле класса с `cls.f`, звёздная цель до и после звезды (с захода 5); 2 `OUT_OF_GRAMMAR_BINDING_FORMS`.
- **Значения опознания (до 24 на API):** имя; атрибут; `getattr`-строка (и с умолчанием); `partial`, связанный по имени и по атрибуту, и несвязанный; `methodcaller`; псевдоним ввоза `as`. Отдельно псевдоним самого носителя (`mc = operator.methodcaller`, `attr = getattr`, `bind = functools.partial`), связанный пятью формами: `=`, кортеж, `:=`, `self.<x>`, тело класса.
- **Судимые API (20):** `setattr`, `set_committed_value`, `set_attribute`, `flag_modified`, `object.__setattr__`; строки `execute`, `scalars`, `bulk_update_mappings`, `bulk_insert_mappings`, `op.bulk_insert`; `values` (именем и словарём), `Query.update`, `insert`, `from_select`, `on_conflict_do_update`; конструктор модели, псевдоним модели, `MessengerAccount.__init__`; дескриптор `__set__`.
- **Способы (8):** прямой вызов; каждый из `REFERENCE_CARRIERS` (`run_sync`, `to_thread`, `run_in_executor`, `map`, `Context.run`); `run_sync(fn=partial(ref, …))`; `partial` внутри `run_in_executor`.

| Заход | HEAD, время (UTC) | Форм подано | `[]` / не та находка под заявлением | Кратных | Вне грамматики: разрешено сверх базы | Закрыто коммитами |
|-------|-------------------|-------------|--------------------------------------|---------|--------------------------------------|-------------------|
| 1 | `d9323cd0`, 2026-10-14 08:52 | 11 440 | 142 — один класс: `methodcaller` API, судимого по получателю (`__set__` дескриптора колонки, `MessengerAccount.__init__`), получает получателя позже — вызовом связанного имени (`f = methodcaller("__set__", a, x); f(M.phone)`) или носителем со следующим аргументом (`to_thread(mc, M.phone)`, `map(mc, [M])`, `partial(mc, M.phone)`) | 0 | 0 | `4bb5ab4f` / `b8c84eb3` |
| 2 | `b8c84eb3`, 08:55 | 17 680 (+ 6 форм сверх таблицы) | **0** | 0 | 0 | — |
| 3 | `b8c84eb3`, 08:58 | 56 984 (+ псевдонимы носителей × 5 форм, `getattr` с умолчанием) | 9 120 — один класс: псевдоним `methodcaller` / `getattr`, связанный целью-атрибутом или в теле класса, вызывается через атрибут (`self.mc(…)`, `K.attr(…)`), а `_rename_aliases` переводил только `Name` | 0 | 0 | `4c692d95` / `18e13784` |
| 4 | `18e13784`, 09:02 | 56 984 | **0** | 0 | 0 | — |
| зонд | `18e13784`, ≈09:03 | 10 форм связывания вне операторов | распаковка со звёздной целью (`w, *rest = setattr, …`, `*rest, scv = …`) — `[]`; `setattr(self, "f", api)` и `globals()["f"] = api` — `[]` и в границе не названы | — | — | `175c9ab4` / `e5df9047` (звёздная цель — в грамматику); `aa756a96` / `0ea91ee8` (связывание вызовом — в пункт (1) с причиной) |
| 5 (итог) | `0ea91ee8`, 09:07 | **63 688** | **0** | **0** | **0** | — |

По осям на заходе 5:
- по 3 352 формы на каждую из 19 форм связывания;
- по 7 961 форме на каждый из 8 способов;
- по API: от 304 (псевдоним модели) до 3 648 форм.

На формах вне грамматики (`for`, `with … as`) из 6 704 ячеек 4 470 дают `[]`. Остальные 2 234 дают находку, равную базе с несвязанным именем, то есть связывание в них не разрешено. Находку даёт само значение или цена строгости носителя:
- 1 632 — `methodcaller` со всеми аргументами записи;
- 462 — `partial`, у которого привязанный аргумент уже несёт номер (`values({...})`, `Query.update({...})`, перечень `from_select`), или срабатывает строгость носителя;
- 140 — `insert(MessengerAccount, phone=x)`: `MessengerAccount` стоит среди позиционных аргументов.

**Зонд вне операторов связывания:**
- `staticmethod(...)` в теле класса, `attrgetter(...)(obj)` и `writers["scv"](…)` уже названы в пункте (1): результат не-`partial` вызова или контейнер.
- lambda-обёртка ловится прямо.
- `partial` с `key="phone"` и `partial` с привязанным номером дают по одной находке: используется он или нет, consumption не даёт двойного счёта.

Замер записи на SQLite не проводился. Каждая новая строка — форма классов, запись которых уже измерена: верификатор раунда 5 (`+71`…`+75`) и исполнитель 16-22 (`methodcaller("__set__", a, v)(M.phone)` пишет колонку). Носитель и связывание поведение вызова не меняют.

## Files Created/Modified

- `tests/phone_gate_grammar.py` (новый, 329 строк): общая грамматика связывания, таблицы матриц, перечень носителей, `binding_form_source`.
- `tests/test_application/test_phone_single_writer_gate.py` (+978 / −96 по сумме диффа плана): ввоз общего модуля; `_module_aliases` / `_api_aliases` / `_api_alias_targets` на `module_bindings`; `_partial_aliases`, `_iterable_elements`, `_elementwise_arguments`, `_methodcaller_aliases`, `_methodcaller_receivers`; `_rename_aliases` на `NodeTransformer`; `API_IDENTIFICATION_VALUES`; три правила; 23 строки форм и 10 законных; шапка.

## Decisions Made

См. `key-decisions` во frontmatter. Главные:
- **Переименование `PARAMETER_BINDING_FORMS`.** Иначе общий `BINDING_FORMS` нельзя ввезти под своим именем, а 16-29 проверяет, что гейт его не присваивает.
- **Связанный `partial` судится у использования.**
- **`methodcaller` судится по каждому получателю применения.**
- **Связывание вызовом названо в пункте (1).** Оно описано там прозой, без новой строки `OUT_OF_GRAMMAR_BINDING_FORMS`: задача 2 закрепляет ровно две строки.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Конфликт имени `BINDING_FORMS` в модуле гейта**
- **Found during:** задача 2 (ввоз общей таблицы)
- **Issue:** гейт уже определял `BINDING_FORMS = ("positional", "keyword", "double-star", "starred")` для сторожа сигнатур. Ввоз общей таблицы под тем же именем затёр бы её. Правило-паритет 16-29 запрещает гейту присваивать `BINDING_FORMS`.
- **Fix:** чистое переименование в `PARAMETER_BINDING_FORMS`; id параметров `BINDING_CASES` не изменились.
- **Verification:** 424 passed до и после.
- **Committed in:** `a12ad73c` (refactor)

**2. [Rule 2 — критично для заявления] Три класса промахов самопроверки и одна непоименованная форма**
- **Found during:** самопроверка задачи 3, заходы 1 и 3 и зонд
- **Issue:** формы под заявлением давали `[]` (таблица выше).
- **Fix:** четыре цикла RED/GREEN со строками `LITERAL_FORM_CASES` и `LEGITIMATE_CASES`; правка общей грамматики (`binding_pairs`) и шапки.
- **Committed in:** `4bb5ab4f`…`0ea91ee8`

**3. `ELEMENTWISE_CARRIERS` определён в RED задачи 2, а не в GREEN**
- **Причина:** его использует `binding_form_source`, а сборщик ячейки по плану входит в RED. Это данные, не предикат: до GREEN гейт его не ввозил.

**4. План против замера (замер побеждает, ни одна прежняя строка не ослаблена)**

| Величина | В плане | Замер |
|----------|---------|-------|
| Строки после задачи 1 | `OK 160 71` | `OK 160 71` ✓ |
| Строки после задачи 2 | `OK 164 73` | `OK 164 73` ✓ |
| Строки итог | — | 175 / 78: +11 форм и +5 законных строк самопроверки |
| Гейт писателя, итог | ≥ 440 passed | 456 passed (440 + 16 строк самопроверки) |
| Quick run фазы | 982 на базе | 1026 passed |
| `tests/test_application` | 697 на базе | 741 passed |
| Промахи матрицы | 166 → 76 → 0 | 76 после задачи 1 (совпало) → 0 |
| Самопроверка | ≥ 3 000 форм | 63 688 |

**Total deviations:** 1 блокирующая (переименование), 4 цикла самопроверки по плану, 1 перенос данных между RED и GREEN.
**Impact:** заявление шапки не сужено, реестр прежний, прежние 152 / 68 строк на месте.

### Подстановки окружения (песочница worktree, указания оркестратора)

- **Вторая команда `<verify>` задачи 1.** `git show 33a31ee3:<путь>` из Python-однострочника песочница не пускает. Поэтому файл сохранён простой командой в gitignored `.pytest_cache/gate_33a31ee3.py`, а та же логика сравнения исполнена над ним (`rows_cmp.py` в scratchpad). Итог: `OK 152 68 175 78`.
- **Составные команды и heredoc песочница отклоняет.** Команды разбиты, а скрипты записаны инструментом Write. Селектор `-k` подбирался по одному слову (`methodcaller`, `carrier`, `starred`).
- **`graphify update .` не запускался:** его выполняет оркестратор после слияния.
- **Полная суита (`just test`, ≈45 мин) не гналась:** её прогоняет оркестратор после слияния на объединённом дереве.

## Issues Encountered

- **Две ошибки моего проверяющего на заходе 1** (не промахи гейта).
  - Шаблон `run_sync(a, b, fn=f)` невозможен при исполнении: первый позиционный аргумент связывается с `fn`, и вызов падает `TypeError`. Правильная форма — `run_sync(fn=partial(ref, …))`.
  - Предмет находки у псевдонима модели называет псевдоним (`f(phone=…)`), как в прежней строке `model-attribute-alias`. Проверяющий исправлен; 142 промаха захода 1 посчитаны уже после исправления.
- **Цепочка `pytest … | tail -1 && git commit`** в коммите `a12ad73c` маскировала бы код выхода pytest. Зелень (424 passed) я видел до коммита. Остальные коммиты сделаны только после отдельно наблюдённого зелёного прогона.

## Gates on the final tree (`0ea91ee8`, под общим `flock`)

| Гейт | Итог |
|------|------|
| `tests/test_application/test_phone_single_writer_gate.py` | 456 passed |
| quick run фазы (7 путей, `16-VALIDATION.md`) | 1026 passed |
| оба гейта поимённо (приватность + писатель) | 626 passed |
| `tests/test_application` | 741 passed |
| сквозные (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (как на базе; новый модуль в их обходе `tests/` проходит) |
| `compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 (реестр 819 строк, биекция) |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed |
| живое дерево (verify задачи 3 №2) | `OK 6 104` |
| `tests/test_planning` | после коммита сводки — в итоговом сообщении |

## Notes for wave 2 (16-28, 16-29)

- `binding_pairs` общего модуля шире `_binding_pairs` гейта приватности: он попарно разбирает распаковку со звёздной целью. Когда 16-29 переведёт приватность на `module_bindings`, она получит эту форму автоматически, и паритет сохранится.
- `binding_form_source` принимает и `OutOfGrammarForm`. На формах вне грамматики гейт писателя даёт находку только там, где значение само несёт запись: `methodcaller` со всеми аргументами, `partial` с привязанным номером, строгость носителя. Сравнивая вердикты гейтов, правило 16-29 `test_both_gates_leave_the_same_forms_out_of_the_grammar` должно это учитывать.
- `ELEMENTWISE_CARRIERS` и `REFERENCE_KEYWORDS` гейт писателя ввозит из общего модуля (`g.REFERENCE_KEYWORDS is m.REFERENCE_KEYWORDS`).

## Known Stubs

Нет.

## User Setup Required

Нет.

## Next Phase Readiness

16-28 (ось «как названа колонка», сырой SQL) и 16-29 (приватность на общем модуле, правило-паритет) могут строиться на этом модуле: публичные имена совпадают с перечнем плана. Отложенных пунктов нет.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-14*

## Self-Check: PASSED

- FOUND: `tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`
- FOUND (ancestor of HEAD): c30b676c, 25f2bb5e, a12ad73c, 5abe7a71, 8aaded0d, 45898dbd, d9323cd0, 4bb5ab4f, b8c84eb3, 4c692d95, 18e13784, 175c9ab4, e5df9047, aa756a96, 0ea91ee8
- TDD gate: `test(16-27)` и `feat(16-27)` присутствуют в истории
