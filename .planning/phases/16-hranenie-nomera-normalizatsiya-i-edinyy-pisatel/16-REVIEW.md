---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-14T12:18:41Z
depth: standard
review_kind: incremental
diff_base: 22338a9a9c2130b6bacec52ae486e6cfb7be3769
head: bb48dcd1
files_reviewed: 6
files_reviewed_list:
  - app/services/phone.py
  - tests/phone_gate_grammar.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_phone_gates_parity.py
  - tests/test_phone_privacy_gate.py
  - tests/test_services/test_phone.py
findings:
  critical: 0
  warning: 6
  info: 1
  total: 7
carried_forward: 0
closed_prior: 6
status: issues_found
---

# Phase 16: Code Review Report (incremental re-review after gap batch 16-26…16-30)

**Reviewed:** 2026-10-14T12:18:41Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This is an incremental re-review. The diff base is `22338a9a` and `HEAD` is `bb48dcd1`. It covers the six files changed by gap batch round 5:
- the item-5 bracket rule and the item-7 pointer (16-26);
- the shared binding grammar `tests/phone_gate_grammar.py` and the writer gate's binding axis (16-27);
- composed column namings and kind 5 judged in code (16-28);
- the privacy gate's reference carriers, `methodcaller`, and the parity rule `tests/test_phone_gates_parity.py` (16-29).

This report replaces the prior `16-REVIEW.md`. Each prior finding appears once, in the disposition table below.

What I checked:
- **Tests.** The four test files pass: `931 passed` (writer gate, privacy gate, parity, `test_phone`), run with `-p no:randomly`. Parity alone: `11 passed`. Privacy `-s -k live_trees` prints `224 / 68 / 93`, 0 findings, as its header states.
- **Commits.** Every claimed fixing commit is an ancestor of `HEAD` (`git merge-base --is-ancestor`), and each subject matches its claim. The commits are `25f2bb5e`, `8aaded0d`, `d9323cd0`, `b8c84eb3`, `18e13784`, `e5df9047`, `0ea91ee8`, `9df72956`, `29249009`, `17ef8eb8`, `5bf3e3f5`, `a412c3c5`, `5e826558`, `6c6bbea2`, `334b0b9a`, `aff284c9`, `90803f88`, `e2807607`, `d51dc5b2`, `ce5d2378` and `a12ad73c`.
- **Prior forms.** I re-ran every form from the prior WR-14…WR-17 code blocks through `phone_write_offences` / `python_log_offences`. Each one now gives exactly one finding.
- **Parity mutations in memory.** I made four in-memory mutations. Dropping `:=` from the privacy side turns `walrus` red. Dropping the privacy carrier rule turns all nine forms red. Dropping attribute targets on the writer side turns the three `self.`/`cls.` forms red. Inside its cells, the behavioural half of the parity rule does go red. The structural half does not catch a private grammar copy under another name (IN-15).
- **Cross-axis sweep.** I swept every `BINDING_FORMS` row × 7 identification values (including `bulk_update_mappings` and `partial` over it) × direct call and every carrier × each of the 36 `COLUMN_NAMINGS`. That is 12,960 cells, with 0 misses. Composition across the alias, naming and carrier axes holds inside the shared vocabulary.
- **SQLAlchemy / SQLite.** I confirmed every write claimed below on SQLAlchemy 2.0.46 with in-memory SQLite. In each case the column read `+71`…`+86` afterwards.
- **Normalizer.** `app/services/phone.py` changed only in the item-7 docstring (+3 lines). The code is unchanged.

What the batch got right:
- All six prior findings are closed (table below).
- The shared grammar really is the only binding walk in both gates. Neither gate module contains an `ast.Assign` / `ast.AnnAssign` binding walk any more. The only `ast.NamedExpr` hits left in the writer gate (`:1925`, `:2098`) are the container grammar (`rows := …`), not bindings.
- The item-5 rule now compares each bracket with the table in both directions. Its mutation controls (TW moved, RS added) are real red tests.

New problems:
- **When a name is bound twice in a module, only the first binding counts.** This holds in the writer gate's alias maps and in the privacy gate's `methodcaller` resolution. The header promises the opposite (WR-18).
- **The privacy gate's carrier rule is narrower than the writer's.** Four shapes the writer catches pass the privacy gate. The parity matrix has no cell that could show it (WR-19).
- **A reference handed by a keyword other than `fn=` passes.** An example is `threading.Thread(target=…, args=…)`, an idiom the project uses. On `Timer(…, args=…)` the two gates also disagree (WR-20).
- **Kind 5 misses SQLite's single-quoted identifiers.** The 16-28 reason "a literal does not write the column" is false in identifier position (WR-21).
- **Kind 5 (в)/(г) are not comment-aware.** `INSERT /* x */ INTO messenger_accounts` passes (WR-22).
- **`Column("phone")` / `ColumnClause("phone")` as a `values` key pass.** The column is still named literally (WR-23).
- The parity rule's structural half matches names, not copies (IN-15).

## Prior findings — disposition

Titles are copied verbatim from the prior `16-REVIEW.md`. Older ledger rows (CR-01, WR-01…WR-13, IN-01…IN-12) are not repeated: my re-derivation does not contradict their ledger state. That includes the owner-`deferred` IN-01…IN-05; for example, the `phonenumberslite==9.0.41` pin behind IN-02 is unchanged at `pyproject.toml:21`.

| ID | Prior title | State | Evidence (current tree `bb48dcd1`) |
|----|-------------|-------|------------------------------------|
| WR-14 | The single-writer gate's alias claim covers "присваивание", but `_module_aliases` sees only `Name = Name\|Attribute`: tuple, `:=`, `self.x =` and `getattr`-string aliases of writer APIs pass | closed (GREEN `25f2bb5e`, `8aaded0d`, `d9323cd0`, `b8c84eb3`, `18e13784`, `e5df9047`, `0ea91ee8`, `9df72956`, `29249009`; all ancestors of HEAD) | `_module_aliases` (`tests/test_application/test_phone_single_writer_gate.py:2175-2210`) and the `bound` pre-filter of `_api_aliases` (`:2259-2267`) now read `module_bindings` (`tests/phone_gate_grammar.py:100-136`). That covers tuple pairs with a starred target, `:=`, attribute targets, the class body, and `getattr`-literal values read as `Attribute` (`getattr_as_attribute`, `:74-97`). Probe: each of the four forms in the prior WR-14 block gives one finding. Matrix `test_every_binding_form_of_a_writer_api_alias_is_judged` (`:3592`) is green. My 12,960-cell sweep is clean. A remaining hole on rebinding is new **WR-18**. |
| WR-15 | Column namings do not compose: a naming inside an index, lookup or constructor, and a `getattr` derivative, pass although the column is named literally in the writing call | closed (GREEN `17ef8eb8`, `5bf3e3f5`; ancestors) | `_phone_column` (`:1981-2059`) recurses through the name position of a constructor or lookup (`:2027-2029`), an index (`:2035`) and `getattr` (`:2038-2046`). It also handles the `getattr` derivative (`:2054-2058`). The four new `COLUMN_NAMINGS` rows (`:3185-3192`) and `NAME_POSITIONS` × namings (`:3504`, `:3531`) are green. Probe: all five prior WR-15 forms give one finding each. A constructor still outside `COLUMN_CONSTRUCTORS` is new **WR-23**. |
| WR-16 | Raw-SQL kind 5(а) takes the first `WHERE` anywhere as the statement's `WHERE`; a subquery placed before `phone` in `SET` hides the write | closed (GREEN `a412c3c5`, `5e826558`, `6c6bbea2`, `5bf3e3f5`; ancestors) | `_raw_sql_set_writes` (`:1715-1753`) cuts `SET` at a depth-0 `WHERE` (`_sql_set_clause_end`, `:1797-1811`) over `_sql_visible` text. Probe: the prior statement `UPDATE messenger_accounts SET user_id = (SELECT id FROM users WHERE id = 1), phone = :p` gives one finding. The 16-28 narrowing that blanks `'…'` hides a real SQLite write; that is new **WR-21**. The (в)/(г) regex was not made comment-aware; that is new **WR-22**. |
| WR-17 | The privacy gate misses a log method handed by reference to another call (`asyncio.to_thread(logger.info, …, a.phone)`); its boundary does not name the form | closed (GREEN `9df72956`, `29249009`, `334b0b9a`, `aff284c9`, `90803f88`, `e2807607`; ancestors) | `_carried_log_calls` (`tests/test_phone_privacy_gate.py:941-974`) judges the arguments after any positional log callable. `python_log_calls` (`:1061-1082`) adds it. Probe: all four prior forms (`to_thread`, `run_in_executor`, `map`, `Context.run`) give one finding each. Live trees: 224/68/93, 0 findings. The rule is still narrower than the writer's carrier rule on `*`, wrapped carriers and wrapped iterables; that is new **WR-19**. Keyword-delivered references are new **WR-20**. |
| IN-13 | The item-5 recount rule pins that each table region is *named*, not that the prose files it under the right cause; the "region named in prose must be in the table" obligation is not enforced | closed (GREEN `d51dc5b2`; ancestor) | `_item_five_boundary_problems` (`tests/test_services/test_phone.py:982-1039`) parses the three brackets (`ITEM_FIVE_GROUP_PATTERNS`, `:960-964`). It compares each bracket with the table's regions of that cause in both directions (`:999-1011`). It checks every region code in the remainder sentence against the table (`:1012-1022`). The controls `test_the_item_five_rule_reddens_a_region_filed_under_another_cause` (`:1080`) and `…_named_without_a_table_row` (`:1107`) mutate the item in memory, and both go red. I checked the patterns against the live item (`app/services/phone.py:266-271`); each matches its bracket. |
| IN-14 | Item 7, the rule that closes the non-`+7` class, gives no pointer to its remainder, which lives in item 5 (the code-7 item) | closed (GREEN `ce5d2378`; ancestor) | Item 7 now reads "Остаток класса … назван с живым замером в пункте 5" (`app/services/phone.py:299-302`). `test_item_seven_points_to_its_remainder_in_item_five` (`tests/test_services/test_phone.py:1126`) pins the pointer, and pins that item 7 repeats neither the numbers nor the table regions. The diff of `phone.py` is docstring-only. |

## Narrative Findings (AI reviewer)

## Warnings

### WR-18: A name bound twice in one module resolves only to its FIRST binding: a writer API, descriptor, `partial` or `methodcaller` bound second under a reused name passes both gates

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:194-200`: the claim. «имя, однажды связанное с `set_committed_value`, судится как он … `other.bum(…)` любого объекта того же файла судится так же».
- `:2268-2272`: `_api_aliases`, `aliases.setdefault(alias, name)`. One original per alias, picked by `sorted(...)` order.
- `:2289-2292`: `_api_alias_targets`, `bindings.setdefault(target, …)`. The first binding in walk order wins.
- `:1394-1396`: `_partial_aliases`, `name in found → continue`.
- `:1424-1431`: `_methodcaller_aliases`, the same pattern.
- `tests/test_phone_privacy_gate.py:1038-1049`: `_applied_log_methodcaller` returns on the FIRST log-receiver candidate.

**Issue:** The scope is flat, so a short name reused in two functions or two classes of one file (`w`, `fn`, `self.write`) maps to only one target. Every form below gives `[]`. I ran each writer form on SQLAlchemy 2.0.46 / SQLite in memory, and each one wrote the column:
```python
def b(session, p):                       # w → bulk_update_mappings (sorted first)
    w = session.bulk_update_mappings
    w(MessengerAccount, [{"id": 1, "flag": p}])
def a(account, x):
    w = setattr
    w(account, "phone", x)               # judged as bulk_update_mappings(...) — passes; +71

class A:
    def __init__(self, s): self.write = s.bulk_update_mappings
class B:
    def __init__(self): self.write = setattr
    def go(self, account, x): self.write(account, "phone", x)   # passes

set_phone = helper.thing
set_phone = MessengerAccount.phone.__set__
set_phone(account, x)                    # receiver lost: passes; +72

f = methodcaller("noop")
f = methodcaller("__set__", account, x)
f(MessengerAccount.phone)                # passes; +73

w = partial(session.bulk_update_mappings, MessengerAccount)
w = partial(setattr, account)
w("phone", x)                            # passes; +74
```
Privacy side, `[]`:
```python
emit = methodcaller("noop")
emit = methodcaller("info", account.phone)
emit(logger)                             # first candidate `logger.noop()` is returned
```
The header says a name bound once "is judged as it" anywhere in the file. A second binding is just as much a binding under the shared grammar, and no boundary item names "a name rebound to another target". The privacy gate's own name sets (`receiver_names`, `log_functions`) accumulate every binding and catch the `logger.info` rebinding. Only its `methodcaller` path returns early. The parity matrix never binds one name twice, so it cannot see this.

**Fix:**
- Make each alias map multi-valued: `dict[str, set[str]]` in `_api_aliases`, and `dict[str, list[ast.expr]]` in `_api_alias_targets`, `_partial_aliases` and `_methodcaller_aliases`.
- In `_canonical_call` / `_referenced_calls`, judge the call once per target and dedupe findings by `(line, col, kind)`.
- In `_applied_log_methodcaller`, collect a synthetic call for every candidate whose receiver is a logger, rather than `return`ing the first. `python_log_calls` already `extend`s lists.
- Add a `BindingForm("rebound", "f = noop\nf = {value}\n{use}\n", "f")` row to `BINDING_FORMS`, plus a reversed-order row, so the parity matrix holds the axis.

### WR-19: The privacy gate's carrier rule is narrower than the writer's: `*[…]`-delivered references, `partial`-wrapped carriers and wrapped iterables pass, and the parity matrix has no cell that could see it

**File:**
- `tests/test_phone_privacy_gate.py:67-79`: the claim, «Носитель — любой вызов». It says "позиционным аргументом без `*`", but the boundary `:227-276` does not name `*` or any of the forms below.
- `:961-965`: `_carried_log_calls` skips `Starred`.
- `:659-667`: `_is_log_partial` looks at `node.args[0]` only.
- `:1012-1014`: `_applied_log_methodcaller` skips `Starred`.
- `:977-987`: `_iterable_elements` has no `list(…)` wrapper.
- Writer equivalents: `_referenced_calls` (`tests/test_application/test_phone_single_writer_gate.py:1623-1659`) expands `*[…]` via `_positional_arguments` and treats ANY applied call `X(…)(…)` as carrying its reference. Its `_iterable_elements` (`:1507-1530`) unwraps `list(…)`.

**Issue:** Each pair below shows the writer catching the shape and the privacy gate returning `[]`:
```python
await asyncio.to_thread(*[logger.info, "x %s", account.phone])        # writer: to_thread(*[setattr, account, "phone", x]) caught
partial(*[logger.info, "x %s", account.phone])()                       # writer: partial(*[setattr, …])() caught
await partial(asyncio.to_thread, logger.info)("x %s", account.phone)   # writer: partial(asyncio.to_thread, setattr)(account, "phone", x) caught
list(map(methodcaller("info", account.phone), list([logger])))         # writer: map(mc, list([MessengerAccount.phone])) caught
```
Each line makes the logger emit the number. This is the asymmetry О-12 (а) forbids: "one carrier list" holds only as a vocabulary. The carrier *semantics* (where a reference sits, `*` expansion, applied wrappers, elementwise iteration) are still two independent copies. `REFERENCE_CARRIERS` templates (`tests/phone_gate_grammar.py:274-284`) contain no `*`, no wrapped carrier and no wrapper iterable, so `test_both_gates_agree_on_every_binding_form_identification_and_carrier` cannot go red on any of these. "Позиционным аргументом без `*`" narrows the claim in passing, but the boundary never names the `*` form with a reason, as О-12 (а) requires.

**Fix:**
- Move the carrier semantics into the shared module: one `reference_arguments(call, is_reference) -> list[(reference, args_after, keywords)]`, built on literal `*` expansion like the writer's `_forwarded_arguments`. Treat an applied `X(…)(…)` as a carrier of `X`'s references, and use one `iterable_elements` that includes the `LITERAL_CONTAINER_WRAPPERS` unwrap.
- Have both gates call it.
- Add carrier rows to `REFERENCE_CARRIERS`, so both matrices and the parity rule hold them: `starred` (`asyncio.to_thread(*[{ref}, {args}])`), `partial-wrapped` (`functools.partial(asyncio.to_thread, {ref})({args})`) and `map-wrapped-iterable`.

### WR-20: A reference handed by a keyword other than `fn=` passes (`threading.Thread(target=…, args=…)`), neither boundary names it, and the gates disagree on `Timer(…, args=…)`

**File:**
- `tests/phone_gate_grammar.py:244-251`: `REFERENCE_KEYWORDS = frozenset({"fn"})`, the only keyword either gate reads as a reference.
- Writer claim: `tests/test_application/test_phone_single_writer_gate.py:237-246` («ссылка — поданная любому вызову»). Boundary (1)…(5): `:248-287`.
- Privacy claim: `tests/test_phone_privacy_gate.py:67-79` («Носитель — любой вызов»). Boundary: `:227-276`.

**Issue:** Each line below gives `[]`. The writer forms wrote the column on SQLite (`+75`, `+76`):
```python
threading.Thread(target=setattr, args=(account, "phone", x)).start()                    # writer: []
threading.Timer(1.0, setattr, args=(account, "phone", x)).start()                      # writer: []
threading.Thread(target=logger.info, args=("x %s", account.phone)).start()             # privacy: []
```
`threading.Thread(target=…)` is an idiom the project already uses (`app/worker/celery_app.py:196`). The same holds for `multiprocessing.Process(target=, args=)` and `concurrent.futures`' `initializer=`/`initargs=`. Both headers claim "any call" as a carrier, and no boundary item names a keyword-delivered reference or arguments delivered in an `args=` tuple.

The two gates also diverge here. The privacy gate CATCHES `threading.Timer(1.0, logger.info, args=("x %s", account.phone))`, but only by accident: it judges every keyword of the synthetic call, `args=` included. The writer gate misses the same Timer shape, because its synthetic `setattr(args=(…))` has no name parameter. The parity matrix has no keyword-delivered cell.

**Fix:**
- Add a shared table of keyword carriers to `tests/phone_gate_grammar.py`: `KEYWORD_REFERENCE_CARRIERS = {"target": ("args", "kwargs"), "function": ("args", "kwargs"), "initializer": ("initargs", None)}`.
- Teach both gates to synthesise `ref(*<literal args tuple>, **<literal kwargs dict>)` from them.
- Add `Thread(target=…, args=…)` and `Timer(…, args=…)` rows to `REFERENCE_CARRIERS`, so the parity rule covers them.
- If the owner keeps this form out, name it in both boundaries with its true reason. "Поток данных" is not that reason: the tuple is a literal.

### WR-21: Kind 5 misses SQLite's single-quoted identifiers; 16-28's "text inside a literal is not a write" hides `SET 'phone' = …` and `INSERT INTO 'messenger_accounts'`

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:1773-1775`: `_sql_visible` blanks every `'…'` span.
- `:519`: `_SQL_QUOTE = r'["`\[\]]?'`, without `'`.
- `:149`: the header claims «Кавычки идентификатора — `"…"`, `` `…` `` и `[…]`: SQLite принимает все три».
- `:134-142`: the kind 5 claim, "по механизму записи".
- The disposition row for WR-16 states «текст «phone = …» внутри литерала … больше не находка (колонку он не пишет)».

**Issue:** SQLite reads a single-quoted token as an identifier wherever a string literal is not allowed. This is documented legacy behaviour. Each statement below wrote the column on SQLAlchemy 2.0.46 / SQLite in memory, and `phone_write_offences` returns `[]` for each:
```python
s.execute(text("UPDATE messenger_accounts SET 'phone' = :p WHERE id = 1"), {"p": p})          # (а)  +78
s.execute(text("UPDATE messenger_accounts SET ('phone', flag) = (:p, 'f')"), {"p": p})        # (б)  +84
s.execute(text("INSERT INTO 'messenger_accounts' (id, phone) VALUES (5, :p)"), {"p": p})       # (в)  +86
```
The quoted-identifier list on `:149` says SQLite accepts three forms. It accepts a fourth. The 16-28 reason for narrowing ("колонку он не пишет") is false for a one-word single-quoted token in identifier position. The suite runs on SQLite, so this is no hypothetical dialect. The pre-16-28 regex missed `'phone' =` too, but 16-28 is where the claim was written down.

**Fix:**
- In `_sql_visible`, keep a one-word `'…'` span visible, exactly as one-word `"…"`/`` `…` ``/`[…]` already are (`:1784`). Add `'` to `_SQL_QUOTE`, and to the quote class in `_SQL_PHONE_ASSIGNMENT`.
- The cost of this strictness is `WHERE status = 'phone'` before `SET`. That is acceptable, and the header should name it in the cost paragraph.
- Plant the three statements as `LITERAL_FORM_CASES`. Fix the `:149` sentence to list four quote forms.

### WR-22: Kind 5 (в) and (г) still run a `\s+` regex over raw text, so a SQL comment inside the statement head hides an `INSERT` / `REPLACE` / `COPY` into the accounts table

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:1699-1701`: `_raw_sql_write` calls `RAW_SQL_PHONE_WRITE.search(text)` on the raw text, not on `_sql_visible(text)`.
- `:545-554`: the regex joins `insert`, `or …`, `into` and the table with `\s+`.
- `:139-141`: the header says comments do not break (а)/(б). It makes no such statement for (в)/(г), and the boundary does not name comments in the head.

**Issue:** Each statement below wrote rows `(2,'+79')`, `(3,'+80')` and `(4,'+81')` on SQLite, and the gate returns `[]` for each:
```python
s.execute(text("INSERT /* x */ INTO messenger_accounts (id, phone) VALUES (:i, :p)"), …)
s.execute(text("INSERT INTO /* x */ messenger_accounts (id, phone) VALUES (:i, :p)"), …)
s.execute(text("REPLACE -- c\n INTO messenger_accounts (id, phone) VALUES (4, '+81')"))
```
16-28 made the `SET` half comment-aware, because a comment before the column hid the write. The same lexical class still hides the head half. Kind 5's claim is "по механизму записи". A comment does not change the mechanism, and no boundary item names it.

**Fix:**
- Run the (в)/(г) regex over `_sql_visible(text)`. Comments become spaces, so `\s+` spans them. One-word quoted identifiers stay visible, so `"messenger_accounts"` still matches.
- After WR-21, `'messenger_accounts'` will match too.
- Plant the three statements as `LITERAL_FORM_CASES`.

### WR-23: `Column("phone")` / `ColumnClause("phone")` as a `values` key pass, though the column is named literally in the writing call

**File:** `tests/test_application/test_phone_single_writer_gate.py`:
- `:486`: `COLUMN_CONSTRUCTORS = frozenset({"column", "literal_column"})`.
- `:98-99`: kind 3 lists `column("phone")` / `literal_column(…)`.
- `:226-236`: the claim, «Ловится всякая запись, в которой колонка номера … названа литералом в самом пишущем вызове».

**Issue:** `phone_write_offences` returns `[]` for each line below. Both wrote the column on SQLAlchemy 2.0.46 / SQLite (`+77`, `+83`):
```python
update(MessengerAccount).where(MessengerAccount.id == 1).values({sa.Column("phone"): x})
update(MessengerAccount).where(MessengerAccount.id == 1).values({ColumnClause("phone"): x})
```
`ColumnClause` is the class behind `column()`. `Column` is the core column type. Both name the column by a literal string in the writing call, which is the header's own criterion. No boundary item names them. (As an executemany row key, `Column("phone")` does not write on SQLite. That matches what the header already says about `column()` there, so it is not a separate gap.)

**Fix:** Extend `COLUMN_CONSTRUCTORS` to `{"column", "literal_column", "Column", "ColumnClause"}`, and add `ColumnNaming("Column", 'sa.Column("phone")')` and `ColumnNaming("ColumnClause", 'ColumnClause("phone")')` rows. The 714-context matrix and `NAME_POSITIONS` will then hold them. For `Column`, the name keyword is `name=`, not `text=`, so add `name` to `COLUMN_NAME_KEYWORDS`. Alternatively, name the class in the boundary with a true reason.

## Info

### IN-15: The parity rule's structural half matches four function names and four table names, not "no own copy"; a private grammar or carrier copy under any other name passes it

**File:**
- `tests/test_phone_gates_parity.py:53-60`: `GRAMMAR_FUNCTIONS`, `GRAMMAR_TABLES`.
- `:66-86`: `own_grammar_problems`.
- `:116-123`: the docstring «своих копий грамматики и носителей нет».

**Issue:**
- **The check matches names only.** It flags a top-level `def` or assignment only when its name is one of `binding_pairs`, `_binding_pairs`, `module_bindings`, `getattr_as_attribute`, `REFERENCE_KEYWORDS`, `ELEMENTWISE_CARRIERS`, `REFERENCE_CARRIERS` or `BINDING_FORMS`. In my in-memory probe, a module that imports the shared names but defines `def _my_pairs(...)` and `MY_CARRIERS = (...)` gives `[]`.
- **Copies already exist.** The carrier semantics already have two diverging copies, `_iterable_elements` (writer `:1507`, privacy `:977`) and `_getattr_literal` (writer `:1299` accepts ≥2 args and any keywords; privacy `:567` accepts 2–3 args and no keywords). These are where WR-19's divergences live.
- **What really holds parity.** Only the behavioural half does, and only on the cells of the shared vocabulary.

**Fix:** Either reword the docstring to say what is checked ("the named grammar entry points are not redefined"), or move `iterable_elements`, the `getattr`-literal reader and the reference-argument extraction into `tests/phone_gate_grammar.py` (WR-19). Add their names to `GRAMMAR_FUNCTIONS`.

---

_Reviewed: 2026-10-14T12:18:41Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `22338a9a`, head `bb48dcd1`)_
