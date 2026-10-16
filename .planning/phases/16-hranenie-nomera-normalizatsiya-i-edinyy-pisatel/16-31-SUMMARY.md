---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 31
subsystem: testing
tags: [ast, phone, single-writer-gate, privacy-gate, binding-grammar, tdd, wr-18]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль `tests/phone_gate_grammar.py` (16-27, 16-29), гейт писателя 16-09…16-28, гейт приватности 16-08…16-29, правило-паритет 16-29"
provides:
  - "гейт писателя: многозначные `_api_aliases` (`dict[str, frozenset[str]]`), `_api_alias_targets`, `_partial_aliases`, `_methodcaller_aliases` (`dict[str, list[ast.expr]]`); `_bound_reference` → список; `_canonical_call` → список; одна находка на место у толкований одного вызова"
  - "гейт приватности: `_applied_log_methodcaller` → `list[ast.Call]`, каждый кандидат с опознанным получателем"
  - "общий модуль: `IdentificationValue.decoy`, место `{decoy}` в `binding_form_source`, строки `BINDING_FORMS` `rebound`, `rebound-reversed`, `rebound-across-classes` (12 форм, 360 ячеек на гейт)"
  - "трасер `test_a_planted_backfill_with_a_rebound_writer_alias_reddens_the_gate`; 7 строк `LITERAL_FORM_CASES`, 2 строки `LEGITIMATE_CASES`, строки `NEGATIVE_CONTROLS` и `POSITIVE_CONTROLS`"
affects: [16-32, 16-33, 16-34, 16-35, phase-18, phase-19, phase-20]

actuals:
  tokens: 19135
  tasks: 3
  commits: 8
plan_head_before: 17a5b504fd3e006732b28b4e9998ddb0cc9ec264
plan_head_after: ebe466ac4f2788bc552310977ea79a194d4b66b9

tech-stack:
  added: []
  patterns:
    - "Карта псевдонимов многозначна: «имя → множество / список значений» по всем связываниям `module_bindings`, неподвижная точка — по росту списков"
    - "Толкования одного вызова (прямое и через ссылку, по каждой цели) — альтернативы: одна находка на место (строка, столбец), первая в порядке обхода целей"
    - "Подменное значение (`decoy`) — поле значения опознания, а не строка формы: подмена того же вида, что значение"

key-files:
  created: []
  modified:
    - tests/phone_gate_grammar.py
    - tests/test_application/test_phone_single_writer_gate.py
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Толкования ОДНОГО вызова по разным целям сводятся в одну находку на место (строка, столбец), а не только на (строка, столбец, вид): самопроверка нашла две находки разных видов на одном ключе (`f = update; f = bulk_update_mappings; f({\"phone\": x})`); исходные API обходятся по алфавиту, первая находка остаётся"
  - "Имя, которое одновременно псевдоним пишущего API и псевдоним `partial` / `methodcaller`, переводится по каждому связыванию: `_partial_aliases` не переводит только само судимое имя (`untranslated=judged_names`), `_methodcaller_receivers` получает `judged_names`, а не `referable`; ветка `partial_aliases` в `_referenced_calls` стоит до проверки судимого имени"
  - "`_bound_reference` возвращает и само имя-ссылку рядом со ссылками его `partial`-связываний: вызывающий отбирает судимые имена"
  - "Гейт приватности не дублирует одно и то же применение `methodcaller`, пришедшее двумя путями (равный `ast.dump`)"

patterns-established:
  - "Самопроверка оси кратности: ответ ячейки с повторным связыванием обязан совпасть с ответом той же ячейки с одним связыванием; ячейка, где все связывания безобидны, — с ответом одного безобидного связывания"

requirements-completed: [PHONE-02, PHONE-21]

coverage:
  - id: D1
    description: "Скрипт дозаполнения с именем `w`, связанным с `session.bulk_update_mappings` в одной функции и с `setattr` в другой, в синтетическом `scripts/` краснит гейт писателя с файлом, строкой и видом; у вызова ровно одна находка"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_rebound_writer_alias_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять форм WR-18 гейта писателя и две формы самопроверки — строки LITERAL_FORM_CASES, по одной находке ожидаемого вида; два законных повторных связывания — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "`methodcaller`, связанный дважды и применённый к журналу, краснит гейт приватности; без опознанного получателя — не вызов журнала"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half"
        status: pass
    human_judgment: false
  - id: D4
    description: "Общий словарь держит ось кратности: 12 форм × 5 значений × 6 способов = 360 ячеек на гейт в обеих матрицах и в правиле-паритете, ноль промахов"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_binding_form_of_a_writer_api_alias_is_judged"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_every_binding_form_of_a_log_reference_is_judged"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_agree_on_every_binding_form_identification_and_carrier"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шапки обоих гейтов называют правило «каждое связывание имени судится», цену и летопись WR-18; заявления прежние; живые деревья — 0 находок, 224 / 68 / 93 вызова, в писателе 6 сырых, реестры прежние"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
    human_judgment: false

duration: 43min
completed: 2026-10-16
status: complete
---

# Phase 16 Plan 31: Ось «сколько раз связано имя» в обоих гейтах — Summary

**Гейт писателя судит КАЖДОЕ связывание имени: его карты псевдонимов многозначны, а толкования одного вызова сводятся в одну находку на место. Гейт приватности судит каждого кандидата `methodcaller`. Общий словарь получил подменное значение `decoy` и три формы повторного связывания (360 ячеек на гейт). Самопроверка прошла 134 460 форм композицией и нашла один класс кратных находок; он закрыт циклом RED/GREEN.**

## Performance

- **Duration:** ≈43 мин
- **Started:** 2026-10-16T08:02:23Z
- **Completed:** 2026-10-16T08:45:20Z
- **Tasks:** 3 (плюс 1 цикл самопроверки)
- **Files modified:** 3

## Accomplishments

- Гейт писателя:
  - `_api_aliases` теперь даёт «псевдоним → множество исходных API», а не одно, первое по алфавиту.
  - `_api_alias_targets`, `_partial_aliases` и `_methodcaller_aliases` дают «имя → список значений» по всем связываниям в порядке обхода. Цепочка `Y = X` прослеживается для каждого связывания отдельно.
  - `_bound_reference` и `_canonical_call` возвращают списки. `_referenced_calls` строит синтетический вызов на каждую ссылку.
  - Находки дедуплицируются по (строка, столбец, вид). Толкования одного вызова сводятся в одну находку на место (строка, столбец).
- Гейт приватности: `_applied_log_methodcaller` возвращает синтетический вызов на каждую пару «`methodcaller` × опознанный получатель». `python_log_calls` добавляет их все.
- Общий модуль:
  - у `IdentificationValue` новое поле `decoy` (умолчание — пустая строка);
  - в `binding_form_source` новое место `{decoy}`, и функция отвергает форму с `{decoy}`, если у значения подмены нет (вакуум);
  - в `BINDING_FORMS` три новые строки: `rebound`, `rebound-reversed`, `rebound-across-classes`.
- Подменные значения есть у каждой строки `API_IDENTIFICATION_VALUES` и `LOG_IDENTIFICATION_VALUES`.
- Шапки:
  - у гейта писателя общий абзац и абзац «ЦЕНА СТРОГОСТИ ВТОРОГО И ТРЕТЬЕГО ВИДОВ» называют правило «каждое связывание имени судится», одну находку на (строка, столбец, вид) и на место у толкований одного вызова, а также цену в сторону лишней находки; дописана летопись шестого круга;
  - у гейта приватности то же правило названо в «ПО СВЯЗЫВАНИЮ», в абзаце о единой области видимости и в пункте границы «область видимости одна» (с `methodcaller`); добавлена отдельная летопись WR-18.
  - Заявления обоих гейтов прежние.

## Task Commits

1. **Задача 1 (трасер): многозначные карты гейта писателя** — `a9e1f6a1` (test, RED), `d3304aab` (feat, GREEN).
2. **Задача 2: ось кратности в общем словаре, каждый кандидат `methodcaller`** — `8e411e06` (test, RED), `0b7a503b` (feat, GREEN).
3. **Задача 3: шапки** — `97434b5b` (test, RED), `2a506aea` (feat, GREEN).
4. **Самопроверка, цикл 1: два вида на одном месте** — `c7c297ed` (test, RED), `ebe466ac` (feat, GREEN).

**Plan metadata:** коммит `docs(16-31)` с этой сводкой.

Гейт трасера после задачи 1: режим `end-of-phase`, проверка только `<automated>`. Все три команды `<verify>` прогнаны повторно и зелёные (`501 passed`, `OK 190 84 195 86`, `OK 6 104`), после чего план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). По каждому есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех четырёх записях.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_rebound_writer_alias_reddens_the_gate` | `1 failed, 500 deselected` | «псевдоним пишущего API, связанный повторно, не опознан» | цель исполнилась, гейт вернул `[]`; соседний прогон `-k rebound`: 6 failed (трасер + 5 строк WR-18), 2 passed (законные строки) |
| Задача 2 | `test_both_gates_agree_on_every_binding_form_identification_and_carrier[rebound]` | `5 failed, 3 passed, 209 deselected` | «расхождение гейтов» и «форма связывания ссылки на журнал не опознана» | ровно замер планирования: у гейта приватности промахи 6 / 0 / 6 (`rebound` / `rebound-reversed` / `rebound-across-classes`), только ячейки `methodcaller`; строка `NEGATIVE_CONTROLS` красная; гейт писателя на новых строках зелёный (`504 passed`) |
| Задача 3 | `test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` | `2 failed, 705 deselected` | «шапка гейта писателя не называет общую грамматику связывания» (и «шапка гейта приватности не называет носителя ссылки») | по 3 недостающих места в каждой шапке |
| Цикл 1 | `test_a_literal_write_form_is_a_write[rebound-alias-two-kinds-at-one-place]` | `2 failed, 504 deselected` | «дала 2 находок вместо одной» | `update({'phone': …})` и `bulk_update_mappings({'phone': …})` на одном ключе |

## Самопроверка исполнителя (задача 3; урок 16-12, 16-17, 16-22, 16-27, 16-28, 16-29; О-14 (а))

Скрипт `.pytest_cache/selfcheck_1631.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный и потоковый и работает под общим `flock`. Ячейка собирается функцией `binding_form_source` общего модуля, подмены подставляются в шаблон формы.

Критерий — инвариантность по кратности. Ответ ячейки с повторным связыванием обязан совпасть с ответом той же ячейки с ОДНИМ связыванием (`f = V; use`). Ответ одного связывания сам должен лежать под заявлением:
- у гейта писателя — ровно одна находка, называющая `phone`;
- у гейта приватности — находки непусты, и каждая называет `phone`.

На обоих заходах ни одна ячейка с одним связыванием из перебора не выпала.

**Формы кратности (18):**
- одна область, имя связано 2 раза: значение первым и последним;
- одна область, 3 раза: значение первым, в середине, последним;
- разные функции: значение в первой, во второй, в средней из трёх; вызов в функции, где имя связано с подменой;
- разные классы (`self.f`): подмена в первом, значение в первом, значение в среднем из трёх;
- перевязка в том же методе;
- тело класса против метода, в обе стороны;
- модуль против функции, в обе стороны; функция с подменой и модуль со значением.

Перебор гейта писателя (`phone_write_offences(…, "scripts/x.py")`):
- **судимые API (16):** `setattr`, `set_committed_value`, `set_attribute`, `flag_modified`, `object.__setattr__`, дескриптор `MessengerAccount.phone.__set__`, `MessengerAccount.__init__`, строки `execute`, `bulk_update_mappings`, `bulk_insert_mappings`, `values`, `Query.update`, `insert`, `from_select`, `on_conflict_do_update`, конструктор модели (и псевдоним модели — значением «ввоз `as`»);
- **значения опознания (7):** имя, атрибут, `getattr`-строка, `partial` без привязки и с привязкой, `methodcaller`, псевдоним ввоза `as`;
- **подмены (9):** пишущий API, первый по алфавиту, — `bulk_update_mappings` именем, `session.bulk_insert_mappings` атрибутом, `getattr(session, "execute")`; безобидные имя и атрибут; `partial` над чужим API и над безобидным; `methodcaller("noop")` и `methodcaller` над чужим API;
- **способы (6):** прямой вызов и 5 `REFERENCE_CARRIERS`.

У формы с тремя связываниями вторая подмена — следующая по списку. Подмена, которая сама пишущий API и на тех же аргументах даёт находку, — второе правдивое толкование того же вызова. Её вид засчитывается: одна находка на место, первая в порядке обхода целей.

Перебор гейта приватности (`python_log_offences(…, "app/x.py")`):
- **получатели × методы:** `logger`, `self.log`, `logging`, `structlog.get_logger()` × `info`, `ainfo`, `_log`, `bind`;
- **значения при получателе:** атрибут, `getattr`-строка, `partial`, `methodcaller`;
- **значения без получателя:** `print`, функция `logging` из ввоза `as`, `bind_contextvars` атрибутом и ввозом `as`;
- **подмены (6):** `noop`, `helper.noop`, `getattr(helper, "noop")`, `partial(helper.noop, …)`, `methodcaller("noop")`, `methodcaller("info", "ok")`;
- **способы:** прямой вызов и 5 носителей.

Отдельно проверено:
- `methodcaller` каждой формы, применённый к `other` (без опознанного получателя), не даёт вызова журнала;
- ячейка, где все связывания безобидны, даёт ноль находок.

| Заход | HEAD, время (UTC) | Форм подано (писатель / приватность) | `[]` под заявлением | Кратных / не того вида | Безобидные: расхождение с одним связыванием | Закрыто коммитами |
|-------|-------------------|--------------------------------------|---------------------|------------------------|---------------------------------------------|-------------------|
| 1 | `2a506aea`, 2026-10-16 ≈08:20 | 90 396 / 44 064 | 0 / 0 | **1 968** кратных у гейта писателя — один класс: `Query.update` (имя, атрибут, `getattr`-строка, `partial` без привязки) с подменой — пишущим API строк; `f({"phone": x})` давал две находки разных видов на одном ключе (`ключ словаря values` и `ключ словаря строк`) во всех 18 формах; у приватности 0 | (критерий захода 1 — «ноль»: 1 800 безобидных ячеек с аргументами `insert` дали находку — см. ниже) | `c7c297ed` / `ebe466ac` |
| 2 (итог) | `ebe466ac`, 2026-10-16 08:37 (писатель), 08:39 (приватность) | **90 396 / 44 064** | **0 / 0** | **0 / 0** | **0** | — |

Безобидные ячейки на заходе 2:
- гейт писателя — 40 176 форм, все совпали с ответом одного безобидного связывания;
- гейт приватности — 44 064 формы, находок 0;
- «без получателя» — 10 368 форм `methodcaller`, вызова журнала нет ни в одной.

На заходе 1 1 800 безобидных ячеек с аргументами `insert` — `f(MessengerAccount, phone=x)`, где `f` безобиден, — дали находку `MessengerAccount(phone=…)`. Это прежняя цена строгости носителя: модель, поданная позиционно, судится как ссылка на конструктор; её назвала сводка 16-27 («140 — `insert(MessengerAccount, phone=x)`»). Ту же находку даёт и одно связывание, и вызов без связывания, то есть к оси кратности она не относится. Критерий безобидных ячеек поэтому переписан на «совпадает с ответом одного связывания». На заходе 2 все 1 800 таких ячеек дали ровно ответ одного связывания.

По осям на заходе 2:
- гейт писателя: по 5 022 формы на каждую из 18 форм кратности; по 10 044 на подмену; по 15 066 на способ; по API — от 4 860 до 6 804; по значению — от 5 832 до 15 552;
- в 1 526 ячейках находка одна, но называет вид подменного API — второго правдивого толкования того же вызова;
- гейт приватности: по 2 448 форм на форму кратности; по 7 344 на подмену и на способ; по цели — от 648 до 2 592.

Итого подано 134 460 форм под заявлением (90 396 + 44 064). Это больше порогов плана: 5 000 у гейта писателя и 2 000 у гейта приватности.

Запись на SQLite не замерялась. Повторное связывание поведения вызова не меняет, а классы записи всех форм измерены раньше: верификатор раунда 6 (`+71`, `+74`) и исполнитель 16-22.

## Files Created/Modified

- `tests/phone_gate_grammar.py` — поле `IdentificationValue.decoy`, место `{decoy}` и отказ при пустой подмене в `binding_form_source`, три строки `BINDING_FORMS` с летописью.
- `tests/test_application/test_phone_single_writer_gate.py`:
  - многозначные карты, `_bound_reference` и `_canonical_call` — списками, `_add_bound_values`;
  - толкования одного вызова сводятся по месту, дедупликация (строка, столбец, вид);
  - подменные значения `API_IDENTIFICATION_VALUES`;
  - трасер, 7 строк `LITERAL_FORM_CASES`, 2 строки `LEGITIMATE_CASES`;
  - правило шапки и шапка.
- `tests/test_phone_privacy_gate.py`:
  - `_applied_log_methodcaller` → список;
  - подменные значения `LOG_IDENTIFICATION_VALUES`;
  - строки `NEGATIVE_CONTROLS` / `POSITIVE_CONTROLS`;
  - правило шапки и шапка с летописью WR-18.

## Decisions Made

- **Одна находка на место у толкований одного вызова.** План требовал дедупликации по (строка, столбец, вид). Самопроверка показала, что этого мало для обещания «одна находка на вызов, сколько бы целей ни было»: два пишущих API одного имени дают на одном ключе находки РАЗНЫХ видов. Поэтому все толкования одного узла вызова — прямое, через ссылку, по каждому исходному API и каждой цели — считаются альтернативами и сводятся по (строка, столбец). Исходные API обходятся по алфавиту, и остаётся первая находка. Глобальная дедупликация (строка, столбец, вид) осталась. Шапка называет оба правила.
- **Имя — сразу псевдоним API и псевдоним `partial` / `methodcaller`.** Раньше такое имя не переводилось как `partial` / `methodcaller`: проверка «имя само судимо» шла по `referable`, а туда входят псевдонимы API. Теперь не переводится только само судимое имя. Без этого подмена-API рядом со значением-`partial` теряла бы значение.
- **`_bound_reference` возвращает и голое имя-ссылку.** Имя, которое одновременно псевдоним пишущего API и `partial`, судится носителем в обоих качествах.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Две находки разных видов на одном месте у имени, связанного с двумя API**
- **Found during:** задача 3, самопроверка, заход 1.
- **Issue:** `f = update; f = bulk_update_mappings; f({"phone": x})` давал две находки на одном ключе: `ключ словаря values` и `ключ словаря строк`. Дедупликация по (строка, столбец, вид) их не сводила. Так было в 1 968 формах.
- **Fix:** толкования одного вызова сводятся в одну находку на место (строка, столбец), первая в порядке обхода целей. Шапка называет правило. Добавлены строки `LITERAL_FORM_CASES` `rebound-alias-two-kinds-at-one-place` и `rebound-partial-and-alias-two-kinds-at-one-place`.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.
- **Verification:** обе строки зелёные; заход 2 самопроверки — 0 кратных; 190 / 84 прежних строк на месте; живое дерево — 0, в писателе 6 сырых.
- **Committed in:** `c7c297ed` (RED), `ebe466ac` (GREEN).

**2. [Rule 2 - Missing critical] Имя — сразу псевдоним API и `partial` / `methodcaller`**
- **Found during:** задача 1, при проектировании многозначных карт. Комбинация подмен разного вида, которую перебирает самопроверка.
- **Issue:** `_partial_aliases` и `_methodcaller_aliases` исключали любое имя из `referable`, то есть и псевдонимы API. В `_referenced_calls` ветка `partial_aliases` стояла после выхода по судимому имени. Имя, связанное и с API, и с `partial`, судилось только как API.
- **Fix:**
  - у `_partial_aliases` новый параметр `untranslated` (из `_phone_writes` в него подаётся `judged_names`);
  - `_methodcaller_receivers` получает `judged_names`;
  - ветка `partial_aliases` перенесена до проверки судимого имени;
  - `_bound_reference` возвращает и голое имя.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.
- **Verification:** самопроверка — 0 промахов на подменах `partial-other-api` и `methodcaller-other-api` при каждом значении.
- **Committed in:** `d3304aab`.

**3. [Rule 2 - Missing critical] Повторное применение того же `methodcaller` не дублируется**
- **Found during:** задача 2.
- **Issue:** план требовал «находки одного места не дублируются». Список кандидатов мог дать два одинаковых синтетических вызова, если имя связано дважды с равным `methodcaller(…)`.
- **Fix:** синтетический вызов с равным `ast.dump` в списке не повторяется.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Committed in:** `0b7a503b`.

### Отклонения чисел план → замер (замер побеждает, строки не снимались)

| Что | План | Замер | Почему |
|-----|------|-------|--------|
| строки после задачи 1 | `OK 195 86` | `OK 195 86` (после задачи 1), `OK 197 86` на итоговом дереве | +2 строки цикла 1 самопроверки |
| task-1 `<automated>` #2 на итоговом дереве | строка начинается с `OK 190 84` | `OK 190 84 197 86` | то же |
| гейт писателя | ≥ 504 | 506 | +2 строки цикла 1 |
| оба гейта и паритет | ≥ 721 | 723 | то же |
| quick run фазы | ≥ 1125 | 1127 | то же |
| `tests/test_application` | 778 на базе | 791 | +13 у гейта писателя |

---

**Total deviations:** 3 исправлены автоматически (1 — Rule 1, 2 — Rule 2), плюс расхождения чисел, описанные выше.
**Impact on plan:** все правки — в файлах плана. Реестры, заявления шапок и прежние строки не тронуты.

## Замены команд (песочница worktree, хост)

- Task-1 `<automated>` #2 (`git show` внутри `python -c`): эталон сохранён простой командой `git show 4cd68671:tests/test_application/test_phone_single_writer_gate.py > .pytest_cache/base_writer_gate.py`. Та же логика сравнения исполнена скриптом `.pytest_cache/rows_check.py` над этой копией: `OK 190 84 195 86` после задачи 1, `OK 190 84 197 86` на итоговом дереве.
- Песочница отказала одной составной команде с heredoc (без `git`). Её заменила правка отчёта самопроверки инструментом Write.
- Законные строки выбирались через `-k rebound` / по `id`, без слова с подстрокой `git`.
- Полная суита (~5090 тестов, ~46 мин) не гонялась: её гонит пост-мердж гейт оркестратора на слитом дереве.
- `graphify update .` не запускался: граф обновит оркестратор после слияния. Ориентация шла по `graphify query … --graph /source/broadcaster/graphify-out/graph.json` (только чтение).
- `.planning/WINDOWS.md` и `deferred-items.md` не писались (orchestrator_notes 5). Отложенного нет.

## Гейты на итоговом дереве (`ebe466ac`, 2026-10-16, под `flock`)

- Task-1 `<automated>`:
  - #1 — гейт писателя `506 passed`;
  - #2 — `OK 190 84 197 86`;
  - #3 — `OK 6 104`: в писателе 5 × `KIND_KEYWORD` + 1 × `KIND_SETATTR`, реестр — ровно писатель, 104 файла, находок 0.
- Task-2 `<automated>`:
  - приватность + паритет — `217 passed`;
  - писатель — `506 passed`;
  - #3 — `OK 360`.
- Task-3 `<automated>`:
  - три модуля — `723 passed`;
  - фразы шапок — `OK`.
- Критерии приёмки:
  - `grep -c "decoy" tests/phone_gate_grammar.py` = 13;
  - `grep -c '"rebound' tests/phone_gate_grammar.py` = 3;
  - многозначная карта — `OK`;
  - кандидаты `methodcaller` — `OK`;
  - реестры (`PHONE_LOG_EXCEPTIONS == {}`, потолок 0, `PHONE_WRITER_EXCEPTIONS` — ровно `app/application/accounts/phone.py`) — `OK`.
- Quick run фазы (8 путей с модулем паритета): `1127 passed`.
- Оба гейта и паритет поимённо: `723 passed`.
- Живые деревья приватности (`-s -k live_trees`): «Python-половина гейта приватности: app: файлов 100, вызовов 224, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0».
- `tests/test_application`: `791 passed`.
- Сквозные гейты `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`: `576 passed` (2 мин 36 с). `tests/test_logging_config.py`: `3 passed`.
- `uv run python -m compileall -q app main.py tests`: код выхода 0.
- `scripts/prohibitions_census.py --check`: код выхода 0, «реестр: 837 строк, биекция с переписью — согласие». `tests/test_planning/test_plan_prohibitions_census.py`: `110 passed`.
- `tests/test_planning` гонится после коммита этой сводки, число — в финальном сообщении исполнителя.

## TDD Gate Compliance

- **RED:** `test(16-31)` — `a9e1f6a1`, `8e411e06`, `97434b5b`, `c7c297ed`.
- **GREEN:** `feat(16-31)` — `d3304aab`, `0b7a503b`, `2a506aea`, `ebe466ac`.
- **REFACTOR:** не понадобился.
- Каждый RED предшествует своему GREEN; нарушений нет.

## Issues Encountered

Нет: каждый промах закрыт в плане.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

План 16-32 готов к исполнению:
- семантика носителя переезжает в `tests/phone_gate_grammar.py`, гейт приватности переходит на неё;
- строки `rebound*` и поле `decoy` уже в общем словаре, их обходят обе матрицы и паритет;
- `_applied_log_methodcaller` теперь возвращает список: план 16-32 при переносе семантики носителя должен сохранить «каждого кандидата».

План 16-34 переведёт гейт писателя на общую семантику носителя. Ему нужно сохранить:
- многозначные `_partial_aliases` / `_methodcaller_aliases`;
- списки у `_bound_reference` / `_canonical_call`;
- сведение толкований одного вызова по месту.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-16*

## Self-Check: PASSED

- FOUND: tests/phone_gate_grammar.py, tests/test_application/test_phone_single_writer_gate.py, tests/test_phone_privacy_gate.py
- FOUND (ancestors of HEAD): a9e1f6a1, d3304aab, 8e411e06, 0b7a503b, 97434b5b, 2a506aea, c7c297ed, ebe466ac
