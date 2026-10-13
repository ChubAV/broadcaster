---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-13T12:06:15Z
depth: standard
review_kind: incremental
diff_base: 6fc1ee91e3b2fabd7309468bab03699019340ddf
head: 4fc4d870
files_reviewed: 5
files_reviewed_list:
  - app/services/phone.py
  - tests/test_application/test_account_phone_writer.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_phone_privacy_gate.py
  - tests/test_services/test_phone.py
findings:
  critical: 0
  warning: 4
  info: 2
  total: 6
carried_forward: 0
closed_prior: 5
status: issues_found
---

# Phase 16: Code Review Report (incremental re-review after gap batch 16-21…16-25)

**Reviewed:** 2026-10-13T12:06:15Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

This is an incremental re-review. The diff base is `6fc1ee91` and `HEAD` is `4fc4d870`. It covers the five files changed by gap batch round 4:
- the measured remainder in item 5 of `normalize_manual` and its live-recount rule (16-21);
- single-writer gate: column derivatives, `from_select` containers, same-module aliases of writer APIs, the `COLUMN_NAMINGS` × `COLUMN_CONTEXTS` matrix (16-22);
- privacy gate: structlog async levels, any method of an identified logger, `getChild` / `unbind` / `parent` (16-23);
- the writer-test import (16-24).

This report replaces the prior `16-REVIEW.md`. Each prior finding appears once, in the disposition table below.

What I checked:
- **Tests.** The four test files pass: `831 passed` (225 + 24 + 412 + 170), run with `-p no:randomly`.
- **Commits.** Every claimed fixing commit is an ancestor of `HEAD` (`git merge-base --is-ancestor`), and each has the expected subject: `dd164d6e`, `71957ec1`, `93632304`, `9711cb39`, `ecd1be76`, `4d6f286e`, `9f50ed19`, `878b4679`, `dbe22dcc`, `a973ea55`, `ddbb33f7`, `a4c49b66`, `80153e32`, `1852b951`, `e54fd6e3`, `978a9408`, `d9cfd6c4`.
- **Live numbers.** I re-ran the item-5 enumeration from a scratch script and got `976 / 56 / 36 / 15`. All ten example regions fall in the cause class item 5 gives them. The privacy gate's `-s -k live_trees` prints `221 / 68 / 93`, 0 findings. The matrix is `32 × 714` (`len(COLUMN_NAMINGS)`, `len(COLUMN_CONTEXTS)`).
- **Probes.** I called `phone_write_offences` and `python_log_offences` directly on planted sources. Every single-writer form reported below was also run on SQLAlchemy 2.0.46 against an in-memory SQLite engine, and each one wrote the column (`+71` … `+76` persisted). Every new finding was reproduced, not inferred.

What the batch got right:
- All five prior findings are closed (table below).
- The item-5 text is now true. The rule recounts every number item 5 states, so a metadata bump (IN-02) will turn the suite red.
- The privacy gate's guard against the installed structlog is not vacuous. It derives the expected set from `dir(BoundLogger)` minus the async set itself, so an added `amsg` or `awarn` would fail it.

New problems:
- **The single-writer gate's alias claim is wider than `_module_aliases`.** Tuple unpacking, `:=`, `self.x = …` in a method, and an alias bound to a `getattr`-string all pass. All four write the column (WR-14).
- **Column namings do not compose.** A naming inside a lookup (`t.c[M.phone.key]`, `t.c.get(M.phone.key)`, `column(M.phone.key)`) passes, and so does a `getattr` derivative (`getattr(M.phone, "key")`) (WR-15).
- **Raw-SQL kind 5(а) treats the first `WHERE` anywhere as the statement's `WHERE`.** A subquery placed before `phone` in `SET` hides the write (WR-16).
- **The privacy gate misses a log method handed by reference to another call** (`asyncio.to_thread(logger.info, …, a.phone)`). Its sibling gate catches exactly this shape, and the boundary does not name it (WR-17).
- Two small items in the 16-21 texts and rule (IN-13, IN-14).

## Prior findings — disposition

Titles are copied verbatim from the prior `16-REVIEW.md`. Older ledger rows (CR-01, WR-01…WR-10, IN-01…IN-10) are not repeated: my re-derivation does not contradict their ledger state. That includes the owner-`deferred` IN-01…IN-05; for example, the `phonenumberslite==9.0.41` pin behind IN-02 is unchanged at `pyproject.toml:21`.

| ID | Prior title | State | Evidence (current tree `4fc4d870`) |
|----|-------------|-------|------------------------------------|
| WR-11 | `normalize_manual` item 5 names Germany and Israel as the only non-`+7` extra-digit boundary; 36 regions still save an invented "manual" number | closed (GREEN `dd164d6e`, ancestor of HEAD; RED `71957ec1`, texts `93632304`) | Item 5 (`app/services/phone.py:266-291`) now names the class by mechanism: "где длину … допускает какой-либо тип", with «56 из 976», «36 регионах» and «15 из 56». My recount from a scratch script matches exactly. The ten example regions fall in the cause class item 5 gives them: MOBILE, 22 regions including NL/FI/ID/MY/AT; VOIP only, exactly TW and ZW; fixed-line only, 12 regions including DE/IL/IT. DE with 3 and 4 extra digits is refused with `PHONE_ERROR_TOO_LONG` (item 8), as stated. `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement` (`tests/test_services/test_phone.py:946`) recomputes the numbers live. The code is unchanged apart from IN-11. The rule has a gap in the other direction; that is new **IN-13**. |
| WR-12 | The single-writer gate's mechanism claim is again wider than the predicate: `MessengerAccount.phone.key`, container forms of `from_select` names, and same-module import aliases of writer APIs pass | closed (GREEN `ecd1be76`, `4d6f286e`, `9f50ed19`, `878b4679`, `dbe22dcc`, `a973ea55`, `ddbb33f7`, `a4c49b66`, `80153e32`, ancestors of HEAD) | Probe: each of the ten forms in the prior WR-12 code block now gives exactly one offence. These are `values({M.phone.key: x})`, `bulk_update_mappings`/`execute` rows keyed by `M.phone.key`, `setattr`/`set_committed_value` with `M.phone.key`, `from_select` over `+` / conditional / `list(…)`, and `set_committed_value as scv`, `flag_modified as touch`. The fixes are in `_phone_column` (`tests/test_application/test_phone_single_writer_gate.py:1467-1527`), `_positional_phone_columns` (`:1588-1628`), and `_api_aliases`/`_canonical_call` (`:1686-1768`). The matrix `test_every_column_naming_in_every_judged_context_is_a_write` (`:2770`) runs 32 × 714. On the same two axes, the claim is still wider than the predicate; those are new **WR-14** and **WR-15**. |
| WR-13 | The privacy gate misses structlog's async level methods (`ainfo`, `awarning`, …) that the project's configured logger provides | closed (GREEN `1852b951`, `e54fd6e3`, `978a9408`, ancestors of HEAD) | `ASYNC_LOG_METHODS` (`tests/test_phone_privacy_gate.py:253-255`) is part of `LOG_METHODS` (`:273`). The guard `test_the_async_level_methods_match_the_installed_structlog` (`:1380`) compares it with `dir(structlog.stdlib.BoundLogger)`. Probe: `await logger.ainfo(…, phone=account.phone)`, `await self.logger.awarning(…)`, `getattr(logger, "ainfo")(…)`, `partial(logger.ainfo, …)`, `logger.bind(…).ainfo(…)` and the prior `getChild` sibling each produce offences. The D-17 attribution is gone from the boundary (`:178-211`). Live trees: 221/68/93, 0 findings. A remaining receiver gap on the "by reference" axis is new **WR-17**. |
| IN-11 | Missing space after `=` in `normalize_manual` | closed (`9711cb39`, ancestor of HEAD) | `app/services/phone.py:337` reads `e164 = phonenumbers.format_number(number, PhoneNumberFormat.E164)`. |
| IN-12 | The writer test reaches the new constant through the module object while its sibling is imported by name | closed (`d9cfd6c4`, ancestor of HEAD) | `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` is imported by name (`tests/test_application/test_account_phone_writer.py:31`). `writer_module` no longer occurs in the file (grep: 0 hits). The assertion at `:485` compares with the by-name constant. |

## Narrative Findings (AI reviewer)

## Warnings

### WR-14: The single-writer gate's alias claim covers "присваивание", but `_module_aliases` sees only `Name = Name|Attribute`: tuple, `:=`, `self.x =` and `getattr`-string aliases of writer APIs pass

**File:** `tests/test_application/test_phone_single_writer_gate.py`:
- `:29-35`, `:195-198`: the claim. "по псевдониму такого имени, связанному в том же модуле ввозом `as` или присваиванием имени либо атрибута".
- `:1636-1668` (`_module_aliases`) and `:1699-1707` (`_api_aliases`, the `bound` pre-filter): the predicate.
- `:201-207`, `:217-224`: boundaries (1) and (4).

**Issue:** `_module_aliases` accepts only an `Assign`/`AnnAssign` whose target is a bare `Name` and whose value is a `Name`, or an `Attribute` with the right `.attr`. `phone_write_offences(…, "scripts/x.py")` returns `[]` for each form below. I ran the starred ones on SQLAlchemy 2.0.46 / SQLite in memory, and each wrote the column:
```python
bum = getattr(session, "bulk_update_mappings")                 # * writes (+71)
bum(MessengerAccount, [{"id": 1, "phone": p}])

scv, touch = set_committed_value, flag_modified                 # * writes (+74, via setattr)
scv(account, "phone", x)

if (scv := set_committed_value):
    scv(account, "phone", x)

class W:
    def __init__(self, s):
        self.bum = s.bulk_update_mappings                       # * writes (+75)
    def go(self):
        self.bum(MessengerAccount, [{"id": 1, "phone": p}])
```
Why each form is under the claim and not in a boundary:
- **`getattr`-string.** The header lists a "`getattr`-строка" as a literal identification of the API (`:36`, `:196`), and `getattr(session, "bulk_update_mappings")(…)` is caught when called inline. Binding the same expression to a name makes it pass. Boundary (1) says "результатом другого вызова". If `getattr` counts as "another call" here, it contradicts the header treating `getattr`-strings as literal everywhere else.
- **Tuple unpacking and `:=`.** Both are assignments of a name. The sibling privacy gate resolves both forms for loggers (`_binding_pairs`, `NamedExpr`, `tests/test_phone_privacy_gate.py:588-601`, `:675`).
- **`self.bum =` inside a method.** The same binding in the class body is caught, because the flat-scope `Assign` has a `Name` target. Inside `__init__` it passes. The privacy gate treats `self.lg = …` from `__init__` as an attribute binding.

None of these is named in (1) or (4). By the header's own rule (`:232-234`), this is "слепота предиката, а не граница средства" ("a blindness of the predicate, not a boundary of the tool"). This is the fifth round on this axis: WR-01 → WR-08 → WR-10 → WR-12 → here.

**Fix:**
- Reuse the privacy gate's binding grammar in `_module_aliases`:
  - pair tuple targets with tuple values (`_binding_pairs`);
  - collect `ast.NamedExpr`;
  - record `Attribute` targets as attribute aliases, called through `self.<attr>` / `cls.<attr>`.
- Treat a `getattr(<obj>, "<api>")` value as `Attribute(<obj>, "<api>")`: in `_module_aliases` and the `bound` pre-filter use `_getattr_literal(value)`, and in `_api_alias_targets` keep the receiver `<obj>`.
- Plant all four forms as `LITERAL_FORM_CASES` rows, and add the alias-binding forms to the 16-22 self-check's axis B.
- If any form is meant to stay outside, name it in (1) with its real reason ("`getattr` bound to a name"), not under "результатом другого вызова".

### WR-15: Column namings do not compose: a naming inside an index, lookup or constructor, and a `getattr` derivative, pass although the column is named literally in the writing call

**File:** `tests/test_application/test_phone_single_writer_gate.py`:
- `:76-86`, `:191-194`: the claim. Kind 3 lists the index, lookup and constructor forms, and «"названа литералом" включает производную колонки любой цепочкой атрибутов и индексов».
- `:1497-1499`: constructor/lookup names go through `_constant_text` only.
- `:1505-1510`: an index needs a constant slice.
- `:1511-1519`: `getattr` needs the constant to be the column itself.
- `:1520-1526`: a derivative must be an `ast.Attribute`/`ast.Subscript`.

**Issue:** `_phone_column` recognises each naming in `COLUMN_NAMINGS`, but it never runs `_phone_column` on the *name argument* of another naming. It also does not treat `getattr(<column>, "<const>")` as attribute access. The gate does treat it that way for the column itself (`getattr(M, "phone")`) and for API identification. Probe, `[]` for each; the starred ones wrote the column on SQLAlchemy 2.0.46:
```python
update(MessengerAccount).values({MessengerAccount.__table__.c[MessengerAccount.phone.key]: x})   # * +72
session.bulk_update_mappings(MessengerAccount, [{"id": 1, getattr(MessengerAccount.phone, "key"): p}])  # * +73
update(MessengerAccount).values({MessengerAccount.__table__.c.get(MessengerAccount.phone.key): x})
update(MessengerAccount).values({column(MessengerAccount.phone.key): x})
setattr(account, getattr(getattr(MessengerAccount, "phone"), "key"), x)
```
`Model.__table__.c[Model.attr.key]` is the ordinary idiom for going from an ORM attribute to its `Table` column. `getattr(M, "phone").key` is caught (row `getattr-key`), while the mirror form `getattr(M.phone, "key")` is not. This is a hole on the naming axis that the 32 × 714 matrix cannot see: the matrix varies the *context* of each naming, not a naming nested inside another naming. Boundary (2) ("вычисленные во время исполнения … результат вызова над строкой") does not cover these: no part is computed from a non-literal.

**Fix:**
- In the constructor/lookup branch (`:1497`) and the index branch (`:1505`), accept the name if `_phone_column(name)` is not `None`, not only `_constant_text(name) in PHONE_COLUMNS`.
- Treat `getattr(X, "<const>")` like `ast.Attribute(X, "<const>")` in the derivative branch (`:1520`): recurse into `node.args[0]` when it is a `getattr`-literal.
- Add rows `table-c-index-by-key`, `table-c-get-by-key`, `column-by-key` and `getattr-derivative` to `COLUMN_NAMINGS`. The matrix will then hold them in every context.

### WR-16: Raw-SQL kind 5(а) takes the first `WHERE` anywhere as the statement's `WHERE`; a subquery placed before `phone` in `SET` hides the write

**File:** `tests/test_application/test_phone_single_writer_gate.py:110-112` (kind 5 (а): "присваивание колонки номера в `SET` до `WHERE`"), `:438-440`, `:451-454` (`RAW_SQL_PHONE_WRITE`, first alternative `(?:(?!\bwhere\b)[\s\S])*?`)

**Issue:** The negative look-ahead stops the scan at the first `where` token after `SET`, including one inside a parenthesised subquery that belongs to an earlier assignment. `phone_write_offences` returns `[]` for:
```python
await s.execute(text(
    "UPDATE messenger_accounts SET user_id = (SELECT id FROM users WHERE id = 1), phone = :p"
), {"p": p})
```
On SQLite this statement writes the column: the row reads `+79991234567` after it, and `+76` in the SQLAlchemy probe. `(б)` and `(в)` do not apply, because the statement is a plain `UPDATE` with no row constructor. The header promises "по механизму записи" for SQL in a string constant, and this is an assignment to the column in `SET`.

**Fix:** Stop the (а) scan only at a top-level `WHERE`. A regex cannot balance parentheses, so do it in code. Either:
- strip parenthesised groups from the `SET … WHERE` slice before matching `\bphone(?:_is_manual)?\b["`\]]?\s*=`; or
- split at the first `where` whose parenthesis depth is 0.

Plant the statement above as a `LITERAL_FORM_CASES` row. Keep `SELECT … WHERE phone = :p` in `LEGITIMATE_CASES` as the negative control.

### WR-17: The privacy gate misses a log method handed by reference to another call (`asyncio.to_thread(logger.info, …, a.phone)`); its boundary does not name the form

**File:** `tests/test_phone_privacy_gate.py`:
- `:54-59`: "ПО ССЫЛКЕ НА МЕТОД ОПОЗНАННОГО ЖУРНАЛА". This covers only a name or attribute *bound* to a log method, plus `functools.partial(<log callable>, …)`.
- `:564-571` (`_is_log_partial`) and `:782-799` (`python_log_calls`): the only reference carrier is `partial`.
- `:178-211`: the boundary list, which names no such form.

**Issue:** `python_log_offences(…, "app/x.py")` returns `[]` for each of:
```python
await asyncio.to_thread(logger.info, "connected %s", account.phone)
await loop.run_in_executor(None, logger.info, "connected %s", account.phone)
list(map(logger.info, [a.phone for a in accounts]))
contextvars.copy_context().run(logger.info, account.phone)
```
Each call makes the logger emit the number. `asyncio.to_thread` is already in `app/` (`app/services/image_upload.py:444`). The project is async, so offloading a blocking call is an idiom its authors use. The `phone` name is right there in the call, so the boundary bullet "значение … без имени `phone`" does not apply. The sibling single-writer gate treats exactly this shape as identification by reference: `run_sync`, `to_thread` and `run_in_executor` (`tests/test_application/test_phone_single_writer_gate.py:36-46`, `_referenced_calls`). The privacy gate accepts `partial(logger.info, …)` but not the same reference handed to `to_thread`. That asymmetry is a blindness of the predicate, not an owner frame.

**Fix:** Treat any call that has a log callable (`_is_log_callable`) among its positional arguments as a log call, and judge the arguments after that reference. This is the same rule as `partial`, applied to every carrier:
```python
def _is_log_reference_carrier(call: ast.Call, names: ModuleLogNames) -> bool:
    return any(
        not isinstance(arg, ast.Starred) and _is_log_callable(arg, names)
        for arg in call.args
    )
```
Add it to `python_log_calls`. Plant the four forms as `NEGATIVE_CONTROLS`. Add `asyncio.to_thread(prepare_upload, content)` as a `POSITIVE_CONTROLS` row, so a non-log reference stays clean. Re-run `-s -k live_trees` to confirm the call counts move only where expected.

## Info

### IN-13: The item-5 recount rule pins that each table region is *named*, not that the prose files it under the right cause; the "region named in prose must be in the table" obligation is not enforced

**File:** `tests/test_services/test_phone.py:888-895` (comment: "Регион, названный прозой пункта 5, обязан стоять здесь (запрет №3 плана 16-21)"), `:930-944`, `:981-990`
**Issue:**
- **Where a region sits is not checked.** The rule checks `re.search(region, item)` over the whole item, and it checks each region's cause from `MANUAL_BOUNDARY_EXAMPLES`. It never checks which parenthesis the prose puts a region in. Moving `TW` into "сам `MOBILE` (NL, FI, ID, MY, AT, TW)" would stay green, though the prose would then be false.
- **The converse is not checked.** A region added to the prose but not to the table, such as `RS` under "только `VOIP`", is never measured. The comment states an obligation the rule does not enforce.

**Fix:** Parse the three parenthesised groups from item 5 (after "сам `MOBILE` (", "только `VOIP` (", "у … —"). Assert that each group equals the table's regions with that cause, so the set comparison runs in both directions.

### IN-14: Item 7, the rule that closes the non-`+7` class, gives no pointer to its remainder, which lives in item 5 (the code-7 item)

**File:** `app/services/phone.py:246-291` (item 5, "код страны 7 …", which carries the non-7 remainder at `:266-291`), `:295-310` (item 7)
**Issue:** Item 7 reads as a full closure: "так выглядит настоящий номер чужой зоны с лишними цифрами …", and its chronicle says the class "был закрыт только у кода 7" before 16-16. A Phase 18 reader who looks up the account-type rule learns of the «56 из 976» remainder only by reading the code-7 item. The placement predates this batch, but 16-21 doubled the remainder text in place. `_manual_item_five` (`tests/test_services/test_phone.py:909-927`) now pins the text to item 5, so moving it means changing the rule too.
**Fix:** Move the non-7 remainder paragraph to item 7, and point `_manual_item_five` at item 7 (rename it accordingly). If that churn is unwanted, add one sentence to item 7: "остаток класса — пункт 5, замер «56 из 976»".

---

_Reviewed: 2026-10-13T12:06:15Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `6fc1ee91`, head `4fc4d870`)_
