---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-16T13:53:17Z
depth: standard
review_kind: incremental
diff_base: 2f8c1656b4dadc1506c7b6b8f5ab445bc58ed631
head: a3f3ee0d
files_reviewed: 4
files_reviewed_list:
  - tests/phone_gate_grammar.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_phone_gates_parity.py
  - tests/test_phone_privacy_gate.py
findings:
  critical: 2
  warning: 3
  info: 2
  total: 7
carried_forward: 0
closed_prior: 7
status: issues_found
---

# Phase 16: Code Review Report (инкрементальное повторное ревью партии раунда 6, 16-31…16-35)

**Reviewed:** 2026-10-16T13:53:17Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Инкрементальное ревью: база диффа `2f8c1656`, `HEAD` `a3f3ee0d`. С базы изменились только четыре файла тестовых гейтов: общий модуль `tests/phone_gate_grammar.py`, гейт писателя, гейт приватности и правило-паритет. `app/`, `scripts/` и `main.py` не менялись (`git diff --stat 2f8c1656 HEAD`). Этот отчёт заменяет прежний `16-REVIEW.md`. Каждая из семи прежних находок стоит один раз — в таблице диспозиций ниже.

Что проверено:
- **Тесты.** Модули гейтов и паритета зелёные: `792 passed` (`uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`).
- **Коммиты.** Все 19 исправляющих хешей из клеток диспозиций и коммит теста «9dc72673» — предки `HEAD` (`git merge-base --is-ancestor`); темы совпадают с заявленным.
- **Формы прежних находок.** Каждая форма из блоков кода WR-18…WR-23 прогнана через `phone_write_offences` / `python_log_offences`: 22 формы, у каждой ровно одна находка. Сверх них прогнаны варианты осей: тройное и разнородное повторное связывание (10 форм), 15 лексических вариантов SQL, `Process(target=)` и `initializer=`/`initargs=` — всё поймано.
- **Дифференциал база ↔ `HEAD`.** Для каждого гейта собран корпус «ссылка × носитель × форма аргументов» и прогнан на дереве `2f8c1656` (`git archive`) и на `HEAD`:
  - гейт приватности — 765 ячеек; ловилось на базе и пропускается на `HEAD` — 55, все на носителе `map` (CR-02);
  - гейт писателя — 432 ячейки, ни одной регрессии. Отдельным зондом найдена регрессия формы «обёртка носителя под именем, переданная, а не вызванная» (CR-03).
- **Исполнение.** Каждая новая форма-пропуск исполнена. Номер печатается в журнал `logging` (CR-02, WR-24, WR-25). Колонка пишется на SQLAlchemy 2.0.46 / SQLite в памяти (CR-03: `+71`, `+72`). Атрибут пишется через сам носитель (WR-26: `+71`…`+74`).

Что партия сделала верно:
- Все семь прежних находок закрыты (таблица ниже). Карты псевдонимов многозначны. Одинарная кавычка — четвёртый вид кавычек. Голова видов 5 (в)/(г) судится по видимому SQL. `Column` / `ColumnClause` — в `COLUMN_CONSTRUCTORS`. Ссылка поданная любым именованным аргументом судится общим правилом. Докстринг паритета называет ровно то, что проверяет.
- Лексер SQL `_sql_scan` выдержал все мои зонды: комментарий вплотную к ключевому слову, `''` внутри литерала, схема в одинарных кавычках, `UPDATE OR REPLACE`, `ON CONFLICT … SET 'phone'`.

Новые проблемы:
- **Две регрессии, внесённые самой партией.** Обе формы ловились на базе `2f8c1656`:
  - гейт приватности, после перевода на общую семантику носителя (`c6953017`), пропускает `map(logger.info, account.phones)` и все `.map(…)` с не-литеральной итерируемой (CR-02);
  - гейт писателя, после правила «поглощения» обёртки носителя (`147f5e46`), пропускает дословное тело `asyncio.to_thread` — `func_call = functools.partial(ctx.run, setattr, account, "phone", x); await loop.run_in_executor(None, func_call)` (CR-03).
- **Остаток 16-34 (а) — не только копия под О-15, но и расхождение гейтов.** Гейт приватности держит свою `_carrier_wrappers` и вручную повторяет `applied_wrapper`. Вызов `getattr(self, "w")(…)` гейт писателя ловит, а гейт приватности нет. Структурная половина паритета эту копию не видит: это ровно класс, который называла IN-15 (WR-24).
- **Остаток 16-34 (в) подтверждён и содержит живое расхождение.** Ячеек `starmap`, `apply_async` и именованной обёртки у поведенческой половины паритета нет. А `starmap(methodcaller("info", …, account.phone), [(logger,)])` гейт писателя в своей форме ловит, гейт приватности — нет. Докстринг общего модуля утверждает обратное (WR-25).
- **Обёртку носителя, поданную другому носителю, не ловит ни один гейт.** Ни одна граница эту композицию не называет (WR-26).
- **Остаток 16-34 (б) подтверждён:** комментарий о выведенной `REFERENCE_KEYWORDS` (IN-16). Отдельно — устаревшее будущее время «впишет план 16-34» в шапке гейта приватности (IN-17).

## Prior findings — disposition

| ID | Title | State | Evidence |
|----|-------|-------|----------|
| WR-18 | A name bound twice in one module resolves only to its FIRST binding: a writer API, descriptor, `partial` or `methodcaller` bound second under a reused name passes both gates | closed | GREEN `d3304aab`, `0b7a503b`, `2a506aea`, `ebe466ac` (предки `HEAD`). Карты многозначны: `_api_aliases` даёт «псевдоним → frozenset» (`tests/test_application/test_phone_single_writer_gate.py:2540-2545`); `_api_alias_targets` прослеживает каждое связывание (`:2569-2593`); `_partial_aliases` (`:1594-1613`) и `_methodcaller_aliases` (`:1628-1645`) хранят списки через `_add_bound_values` (`:1556-1566`). Толкования одного вызова сводятся в одну находку (`:1111-1156`, `:1186-1189`). `_applied_log_methodcaller` судит каждого кандидата (`tests/test_phone_privacy_gate.py:1136-1176`). Строки `rebound`, `rebound-reversed`, `rebound-across-classes` — `tests/phone_gate_grammar.py:236-262`. Зонд: пять форм писателя и форма приватности из блока WR-18 — по одной находке; тройное и разнородное повторное связывание (`partial`→API, API→`methodcaller`, обёртка→API, цель `for`) — по одной находке в обоих гейтах. |
| WR-19 | The privacy gate's carrier rule is narrower than the writer's: `*[…]`-delivered references, `partial`-wrapped carriers and wrapped iterables pass, and the parity matrix has no cell that could see it | closed | GREEN `c6953017`, `50d6e5cf`, `8a28d2e7`, `6231a0b3`, `5e57325d`, `a28d6efc`. Гейт приватности ищет ссылку общей `reference_arguments` (`tests/test_phone_privacy_gate.py:1097-1105`; `tests/phone_gate_grammar.py:765-813`). `iterable_elements` раскрывает `list([…])` (`tests/phone_gate_grammar.py:452-460`). Ячейки `starred`, `partial-wrapped`, `map-wrapped-iterable` есть в `REFERENCE_CARRIERS` (`:348-356`), обе матрицы и паритет их держат. Зонд: все четыре формы блока WR-19 — по одной находке. Тот же перевод на общую семантику (`c6953017`) сузил `map` у гейта приватности — это новая **CR-02**, а не продолжение WR-19: WR-19 говорила, что приватность уже писателя, а CR-02 — что приватность уже собственной базы и собственной шапки. |
| WR-20 | A reference handed by a keyword other than `fn=` passes (`threading.Thread(target=…, args=…)`), neither boundary names it, and the gates disagree on `Timer(…, args=…)` | closed | GREEN `c6953017`, `94b6c25d`, `a28d6efc`, `e5987a35`, `147f5e46`, `21d463f0`. Общее правило `literal_keyword_arguments` — `tests/phone_gate_grammar.py:555-604`. Именованная ссылка с любым ключом — `_carried_by`, `:682-687`. `REFERENCE_KEYWORDS` выведена (летопись `:293-302`; ввоза нет ни в одном гейте). Строки `thread-target`, `timer-args`, `invented-keyword` — `:357-371`. Зонд: `Thread(target=…, args=…)` и `Timer(1.0, …, args=…)` — по одной находке у обоих гейтов, расхождения нет; `multiprocessing.Process(target=, args=)`, `initializer=`/`initargs=`, `kwargs={…}` — по одной находке в обоих; идиома `celery_app.py:196` — ноль. Коммит `147f5e46` того же ряда внёс регрессию — новая **CR-03**. |
| WR-21 | Kind 5 misses SQLite's single-quoted identifiers; 16-28's "text inside a literal is not a write" hides `SET 'phone' = …` and `INSERT INTO 'messenger_accounts'` | closed | GREEN `e478c8c2`, `6fbc414c`, `e72a8e53`, `c5e82453`. `_SQL_QUOTE` содержит `'` (`tests/test_application/test_phone_single_writer_gate.py:658`). Ветка одинарной кавычки `_sql_scan` оставляет видимым однословный отрезок и понимает `''` (`:2027-2038`). Шапка называет четыре вида кавычек (`:191-197`). Зонд: три оператора блока WR-21 — по одной находке; ещё `INSERT INTO main.'messenger_accounts'`, `SET 'phone'=:p` после `AS m`, `SET note = 'a''b', phone = :p`, `ON CONFLICT … DO UPDATE SET 'phone' = …` — по одной находке. |
| WR-22 | Kind 5 (в) and (г) still run a `\s+` regex over raw text, so a SQL comment inside the statement head hides an `INSERT` / `REPLACE` / `COPY` into the accounts table | closed | GREEN `e478c8c2`, `e72a8e53`. `_raw_sql_write` ищет `RAW_SQL_PHONE_WRITE` в `_sql_visible(text)` (`tests/test_application/test_phone_single_writer_gate.py:1914-1917`); `_SQL_HEAD_GAP` — `:692`. Зонд: три оператора блока WR-22 — по одной находке; комментарий вплотную без пробелов (`INSERT/**/INTO`, `INTO/**/messenger_accounts`, `OR/**/REPLACE`) — по одной находке. |
| WR-23 | `Column("phone")` / `ColumnClause("phone")` as a `values` key pass, though the column is named literally in the writing call | closed | GREEN `8aba9962`, `6fbc414c`. `COLUMN_CONSTRUCTORS = {"column", "literal_column", "Column", "ColumnClause"}` (`tests/test_application/test_phone_single_writer_gate.py:617`); `name` в `COLUMN_NAME_KEYWORDS` (`:631`). Зонд: обе формы блока WR-23 — по одной находке вида «ключ словаря values». |
| IN-15 | The parity rule's structural half matches four function names and four table names, not "no own copy"; a private grammar or carrier copy under any other name passes it | closed | GREEN `50d6e5cf`, `a28d6efc`. Ревью предлагало «или переформулировать докстринг, или перенести копии»; сделано и то и другое. Докстринги паритета называют проверяемое — «названные точки не переопределены», копию под другим именем видит только поведенческая половина (`tests/test_phone_gates_parity.py:28-30`, `:170-172`, `:203-205`). `_iterable_elements` и `_getattr_literal` нет ни в одном модуле гейта (grep по `def _iterable_elements\|def _getattr_literal` пуст). `GRAMMAR_FUNCTIONS` — 24 имени (`:89-93`), контроль `test_the_structural_half_reddens_a_redefined_grammar_point` (`:197-225`). Но класс, названный IN-15, получил в этой же партии новый живой экземпляр: `_carrier_wrappers` гейта приватности родилась в `5e57325d`, структурная половина её не видит и копия расходится с гейтом писателя. Это новая **WR-24**: экземпляр родился после находки и нарушает О-15, а не продолжает невыполненное исправление IN-15. |

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-02: Гейт приватности после перевода на общую семантику носителя пропускает `map` с не-литеральной итерируемой: `list(map(logger.info, account.phones))` ловился на базе, на `HEAD` — нет

**File:**
- `tests/phone_gate_grammar.py:476-495` — `elementwise_arguments`: итерируемая не-литерал заменяется именем `UNJUDGED_ELEMENT` (`:487-490`), `Starred` обрывает перечень (`:478-479`).
- `tests/phone_gate_grammar.py:450-451` — `iterable_elements`: у comprehension остаётся только `node.elt`, источник итерации теряется.
- `tests/phone_gate_grammar.py:709`, `:729-736` — `_carried_by`: у `ELEMENTWISE_CARRIERS` аргументы ссылки — только элементы.
- `tests/test_phone_privacy_gate.py:1097-1105` — `_carried_log_calls` зовёт `reference_arguments` и судит только эти элементы.
- Заявление: `tests/test_phone_privacy_gate.py:328-332` — «аргументы ссылки на журнал, пришедшие нелитералом (… распаковка `*rows` …) — … судится само выражение (имя с `phone` краснит, `row` — нет)». А также `:78-79` — «Судятся аргументы после ссылки».

**Issue:** На базе `2f8c1656` гейт приватности судил итерируемые `map` целиком: `_carried_log_calls` подавал синтетическому вызову все аргументы за ссылкой. Коммит `c6953017` (16-32, задача 1) перевёл гейт на `reference_arguments`, написанную «по семантике гейта писателя — она полнее» (`tests/phone_gate_grammar.py:384`). Писателю безразлично имя итерируемой, поэтому общая функция гасит его в `UNJUDGED_ELEMENT`. А приватность судит именно имена (правило (б)). Мой дифференциал на 765 ячейках (носитель × ссылка × форма аргументов) нашёл 55 ячеек, которые ловились на `c6953017^` и не ловятся на `c6953017` и на `HEAD`. Все 55 — носитель `map`. Исполнены с `logging` (номер напечатан):
```python
list(map(logger.info, account.phones))                          # []   LOG +79990000001, LOG +79990000002
with ThreadPoolExecutor() as ex:
    list(ex.map(logger.info, account.phones))                    # []   (последнее имя `map` — поэлементный носитель)
list(map(logger.info, [f"n {p}" for p in account.phones]))       # []   LOG n +79990000001 …
list(map(logger.info, "x %s", *phone_lists))                     # []
list(pool.imap(logger.info, account.phones))                     # находка: `imap` не в ELEMENTWISE_CARRIERS
```
Последняя строка показывает, что правило противоречиво внутри одного гейта: `imap` ловится, `map` — нет. Это регрессия, а не старый пробел. Строки `NEGATIVE_CONTROLS` с `map` (`tests/test_phone_privacy_gate.py:2381`, `:2421`, `:2519`) все литеральные, поэтому ни одно правило не краснеет. Ячейки паритета собираются из литеральных одноэлементных списков (`binding_form_source`, `tests/phone_gate_grammar.py:913-914`) и не видят этого тоже. Гейт приватности — единственная защита D-11 от номера в Loki. BLOCKER: форма проходила гейт до партии и уходит мимо после неё, против явного пункта собственной границы.

**Fix:** Вернуть гейту приватности суд итерируемых целиком, не трогая семантику писателя. Например, отдельное прочтение у поэлементного носителя, где за ссылкой стоят исходные итерируемые:
```python
# tests/test_phone_privacy_gate.py, _carried_log_calls
carried = reference_arguments(call, is_reference, _not_carriers(names))
found = [... как сейчас ...]
if _callee_name(call.func) in ELEMENTWISE_CARRIERS:
    for item in carried:
        # приватность судит имя итерируемой и источник comprehension (правило (б), граница :328-332)
        found.append(ast.copy_location(
            ast.Call(func=item.reference, args=forwarded_arguments(list(call.args))[1:], keywords=[]), call))
```
Либо параметр общей функции: например, `reference_arguments(…, keep_iterables=True)` подставляет на место `UNJUDGED_ELEMENT` саму итерируемую и оставляет comprehension целиком. Вписать в `NEGATIVE_CONTROLS` пять строк выше (плюс `pool.map`, `map(…, iter(phones))`) и трасер с подложенным `map(logger.info, account.phones)`.

### CR-03: Гейт писателя после правила «поглощения» обёртки носителя (`147f5e46`) пропускает обёртку под именем, которую передают, а не вызывают — дословное тело `asyncio.to_thread`

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:1066-1070` — `used`: любое имя в контексте `Load`, в том числе переданное ссылкой.
- `:1077-1084` — обёртка носителя `carrier_wrappers[alias]` поглощается, если имя `alias` есть в `used`.
- `:1875-1884` — обёртка под именем судится только у ВЫЗОВА `w(…)` (`_call_name(call) in carrier_wrappers`).
- Заявление: `:75-78` — «обёртка носителя, связанная с именем любой формой общей грамматики … судится как применённая на месте вызова `w(…)`».

**Issue:** Коммит `147f5e46` (16-34, самопроверка, заход 1) ввёл поглощение, чтобы `w = partial(asyncio.to_thread, setattr, account, "phone"); w(x)` давал одну находку, а не две. Но `used` включает и передачу имени ссылкой. Поглощённая обёртка, которую ни разу не вызвали, не судится ни у связывания, ни у использования. На `147f5e46^` и на базе `2f8c1656` каждая форма ниже давала одну находку (обёртку судили на месте связывания как носитель), на `147f5e46` и `HEAD` — `[]`:
```python
func_call = functools.partial(ctx.run, setattr, account, "phone", x)   # тело asyncio.to_thread (CPython,
await loop.run_in_executor(None, func_call)                            # asyncio/threads.py) — []  SQLite: +71
job = functools.partial(contextvars.copy_context().run, setattr, account, "phone", x)
threading.Thread(target=job).start()                                   # []  SQLite: +72
loop.call_soon(job)                                                    # []
job = functools.partial(asyncio.to_thread, setattr, account, "phone", x); tasks.append(job)   # []
```
Абсурдный контроль: та же обёртка без единого использования (`job = …` и больше ничего) ловится. Добавление использования снимает находку. Для сравнения, псевдоним `partial(<API>, …)`, переданный тем же способом (`job = partial(setattr, account, "phone", x); Thread(target=job)`), ловится: он разрешается как ссылка через `_bound_reference`. Обёртка носителя ссылкой не разрешается. Гейт приватности на той же форме находку даёт (у него поглощения нет), так что гейты здесь расходятся. Паритет не видит: ячейки «именованная обёртка» в нём нет (WR-25). Строки `LITERAL_FORM_CASES` закрепляют только вызванную обёртку (`:6189`). BLOCKER: регрессия партии, форма — естественный путь скрипта, который хочет `to_thread` с копией контекста.

**Fix:** Поглощать обёртку только у имени, каждое чтение которого — вызываемое вызова; иначе судить её на месте связывания, как до `147f5e46`:
```python
called_only = {
    alias for alias in carrier_wrappers
    if all(_is_callee(load) for load in loads_of(tree, alias))  # Load, который не стоит в Call.func
}
consumed |= {id(w) for alias, ws in carrier_wrappers.items() if alias in called_only for w in ws}
```
Либо, полнее, разрешать имя обёртки, поданное носителю, как применённую обёртку с аргументами внешнего носителя (это закроет и WR-26). Вписать четыре формы выше в `LITERAL_FORM_CASES` и трасер.

## Warnings

### WR-24: Гейт приватности держит свою копию семантики обёртки носителя под именем (`_carrier_wrappers`, ручной `applied_wrapper`) — копия расходится с гейтом писателя, а структурная половина паритета её не видит (остаток 16-34 (а), класс IN-15)

**File:**
- `tests/test_phone_privacy_gate.py:882-928` — `_carrier_wrappers`: та же неподвижная точка «имя → обёртки», что у `carrier_wrapper_bindings` (`tests/phone_gate_grammar.py:816-850`); родилась в `5e57325d` (16-32, цикл 2).
- `tests/test_phone_privacy_gate.py:1212-1226` — имя обёртки ищется только как `node.func.id` / `node.func.attr`; применение собирается вручную (`:1222-1224`) — тело `applied_wrapper` (`tests/phone_gate_grammar.py:853-857`).
- Ложные заявления: `tests/test_phone_privacy_gate.py:98-100` («решение владельца О-15: своих копий у гейта нет») и `:359-360` («своих копий … гейт не держит»).
- `tests/test_phone_gates_parity.py:79-85` — сам паритет записывает копию комментарием; `REQUIRED_SHARED_NAMES` (`:104-107`) не требует ни `carrier_wrapper_bindings`, ни `applied_wrapper`; имя `_carrier_wrappers` не входит в `GRAMMAR_FUNCTIONS` (`:89-93`).

**Issue:** О-15 требует, чтобы семантика носителя жила один раз, в общем модуле. Здесь она живёт дважды, и копии уже расходятся. Гейт писателя ищет обёртку по `_call_name` и потому читает `getattr`-строку. Гейт приватности — только по `Name`/`Attribute`:
```python
class K:
    def __init__(self):
        self.w = functools.partial(asyncio.to_thread, logger.info)
    async def go(self):
        await getattr(self, "w")("x %s", account.phone)    # приватность: []   LOG x +79991234567
# писатель на той же форме (setattr, account, "phone", x) — одна находка; то же с methodcaller-обёрткой
```
Второе расхождение — счёт: `w = partial(asyncio.to_thread, logger.info, "x %s", account.phone); w()` даёт у гейта приватности две одинаковые находки на одном месте. У писателя на той же форме одна: у него есть поглощение, у копии нет. Структурная половина паритета эту копию пропускает по построению. Поведенческая тоже: ячейки «именованная обёртка» нет (WR-25). Это ровно класс, который описала IN-15, и новый экземпляр родился в той же партии, что закрывала IN-15. Шапка гейта при этом утверждает, что копий нет.

**Fix:** Заменить копию вызовом общего модуля и сделать имена обязательными:
```python
# tests/test_phone_privacy_gate.py
def _is_carrier_wrapper(value: ast.Call) -> bool:
    return (_last_name(value.func) in names.partial_names and not _is_log_partial(value, names)
            and bool(reference_arguments(value, is_reference, not_carriers)))
wrappers = carrier_wrapper_bindings(bindings, _is_carrier_wrapper)
...
for wrapper in wrappers.get(_last_name(node.func) or "", []):   # _last_name читает getattr-строку
    application = applied_wrapper(node, wrapper)
```
```python
# tests/test_phone_gates_parity.py
REQUIRED_SHARED_NAMES |= {"carrier_wrapper_bindings", "applied_wrapper"}
```
Снять ложные фразы `:98-100` и `:359-360` (или оставить их, но после перевода). Дедуплицировать находки `python_log_offences` по строке и предмету, как гейт писателя.

### WR-25: Поведенческая половина паритета не держит формы самопроверки 16-34 (`starmap`, `apply_async`, именованная обёртка), и в этих ячейках гейты уже расходятся: `starmap(methodcaller(…), [(logger,)])` гейт приватности пропускает (остаток 16-34 (в))

**File:**
- `tests/phone_gate_grammar.py:333-372` — `REFERENCE_CARRIERS`: 11 строк, ни `starmap`, ни `apply_async`, ни обёртки под именем.
- `tests/test_phone_gates_parity.py:239-245` — ячейки паритета собираются только из `REFERENCE_CARRIERS`.
- `tests/phone_gate_grammar.py:792-803` — докстринг `reference_arguments`: «Гейт приватности … зовёт функцию без флага: лишние прочтения ему ничего не добавляют».
- `tests/test_phone_privacy_gate.py:1147` — `_applied_log_methodcaller` зовёт `reference_arguments` без `every_reading`, поэтому прочтения `starmap` (`tests/phone_gate_grammar.py:740-756`) у него нет.
- Строки только у писателя: `tests/test_application/test_phone_single_writer_gate.py:6189`, `:6209`, `:6243`, `:6250`.

**Issue:** Формы, которые нашла самопроверка 16-34, закреплены строками гейта писателя, но не строками общего словаря. Правило-паритет их не собирает. Гейт приватности ловит `starmap` и `apply_async` со ссылкой-журналом только потому, что судит поддерево целиком. Как только ссылка — `methodcaller`, получатель надо достать из кортежа `starmap`, а это прочтение есть лишь при `every_reading=True`:
```python
list(itertools.starmap(operator.methodcaller("info", "x %s", account.phone), [(logger,)]))   # приватность: []
pool.starmap(operator.methodcaller("info", "x %s", account.phone), [(logger,)])              # приватность: []
# писатель: starmap(methodcaller("__set__", account, x), [(MessengerAccount.phone,)]) — одна находка
```
Исполнено: `LOG x +79991234567`. Значит, докстринг общего модуля ложен: лишнее прочтение даёт приватности получателя `methodcaller`. Второе расхождение в той же непокрытой оси — `getattr(self, "w")(…)` (WR-24). О-12 (а) требует, чтобы расхождение гейтов краснило паритет. На этих ячейках он не может покраснеть.

**Fix:**
- Вписать в `REFERENCE_CARRIERS` строки `starmap` (`"list(itertools.starmap({ref}, [({positional},)]))"`) и `apply-async` (`"pool.apply_async({ref}, ({positional},), {keywords})"`).
- Обёртку под именем вписать в паритет отдельной осью, например `CARRIER_BINDING_FORMS` с шаблонами `w = functools.partial(asyncio.to_thread, {ref})\nw({args})\n` и `getattr(self, "w")`-вариантом.
- В `_applied_log_methodcaller` звать `reference_arguments(…, every_reading=True)` — или исправить докстринг `:802-803`, — тогда строка `starmap` позеленеет у обоих гейтов.

### WR-26: Обёртка носителя, поданная другому носителю (а не применённая), или обёрнутая ещё одним `partial` — не ловит ни один гейт, и ни одна граница её не называет

**File:**
- `tests/phone_gate_grammar.py:807-813` — правило 1 `reference_arguments` смотрит на один уровень `X(…)(…)`. Обёртку носителя среди аргументов носитель ссылкой не считает: у писателя `_bound_reference` видит только `partial(<API>, …)` (`tests/test_application/test_phone_single_writer_gate.py:1536-1545`), у приватности `_is_log_partial` — только `partial(<вызываемое журнала>, …)` (`tests/test_phone_privacy_gate.py:726-734`).
- Заявления: писатель `:56-57`, `:75-78`, `:86-91`; приватность `:74-78`.
- Границы: писатель (1) `:323-341` и приватность `:301-332` называют только «результат не-`partial` вызова».

**Issue:** Каждая строка даёт `[]` у обоих гейтов. Так было и на базе, то есть это пробел композиции, а не регрессия. Исполнено: носитель вызывает `setattr(account, "phone", x)`, атрибут записан (`+71`…`+74`); журнал на журнальном варианте тоже печатает номер.
```python
await loop.run_in_executor(None, functools.partial(ctx.run, setattr), account, "phone", x)
list(map(functools.partial(ctx.run, setattr), [account], ["phone"], [x]))
w = functools.partial(ctx.run, setattr); await asyncio.to_thread(w, account, "phone", x)
functools.partial(functools.partial(ctx.run, setattr))(account, "phone", x)
```
Обе части заявлены по отдельности: «ссылка … в применённой обёртке носителя» и «ссылка может стоять и внутри `functools.partial(ref, …)` … поданного другому вызову». Их композиция не ловится. Это та же ось «как подана ссылка», которую О-14 (а) велит закрывать целиком. `partial(ctx.run, func)` — не экзотика: так устроен сам `asyncio.to_thread`.

**Fix:** Научить `_carried_by` раскрывать аргумент-обёртку носителя: позиционный или именованный аргумент, который предикат гейта признаёт обёрткой (тот же `is_wrapper`, что у `carrier_wrapper_bindings`), — или имя, связанное с ней, — судится как `applied_wrapper(<синтетический вызов с аргументами за ним>, wrapper)`, рекурсивно, с защитой от цикла. Тот же механизм закроет CR-03 без отдельного правила поглощения. Вписать в `REFERENCE_CARRIERS` строку `wrapper-handed`: `"loop.run_in_executor(None, functools.partial(contextvars.copy_context().run, {ref}), {args})"`.

## Info

### IN-16: Комментарий ввоза гейта приватности называет выведенную `REFERENCE_KEYWORDS` и путает, кто кого зовёт (остаток 16-34 (б))

**File:** `tests/test_phone_privacy_gate.py:359-363`
**Issue:** «ввоз держит имя для правила-паритета, как и `ELEMENTWISE_CARRIERS` и `REFERENCE_KEYWORDS`». В ввозе (`:364-377`) `REFERENCE_KEYWORDS` нет: таблицу вывел `a28d6efc`, строку ввоза снял 16-34. Фраза «`iterable_elements` здесь зовёт `reference_arguments`» неверна: гейт зовёт `iterable_elements` сам (`:1154`), а `reference_arguments` её не зовёт.
**Fix:** Убрать `REFERENCE_KEYWORDS` из комментария. Написать, что `iterable_elements` гейт зовёт в пути `methodcaller` (`_applied_log_methodcaller`).

### IN-17: Шапка гейта приватности и комментарий её правила говорят о строках `REFERENCE_CARRIERS` в будущем времени — «впишет план 16-34»

**File:** `tests/test_phone_privacy_gate.py:87-91`, `:2793-2795`
**Issue:** «`REFERENCE_CARRIERS` общего модуля — … и шесть строк, которые впишет план 16-34». Строки вписаны (`tests/phone_gate_grammar.py:348-371`), их держат обе матрицы. Шапка описывает дерево до 16-34. Правило шапки сверяет только имена носителей (`:2810-2823`), а не время глагола, поэтому молчит.
**Fix:** «… и шесть строк плана 16-34: …». То же в комментарии правила.

---

_Reviewed: 2026-10-16T13:53:17Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `2f8c1656`, head `a3f3ee0d`)_
