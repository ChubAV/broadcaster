---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-09T00:00:00Z
depth: standard
review_kind: incremental
diff_base: c3b0b232ce64ff22c5fbfc06f467b6cc522f27e0
files_reviewed: 6
files_reviewed_list:
  - app/application/accounts/phone.py
  - app/services/phone.py
  - tests/test_application/test_account_phone_writer.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_phone_privacy_gate.py
  - tests/test_services/test_phone.py
findings:
  critical: 0
  warning: 3
  info: 7
  total: 10
carried_forward: 5
closed_prior: 6
status: issues_found
---

# Phase 16: Code Review Report (incremental re-review after gap batch 16-07…16-09)

**Reviewed:** 2026-10-09
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This is an incremental re-review. The diff base is `c3b0b232`, the commit of the prior review. It covers the six files that the gap-closure batch 16-07…16-09 changed. This report replaces the prior 11-finding `16-REVIEW.md`. Every prior finding is accounted for below, either as `closed` with evidence re-derived on the current tree or as `still open`.

I re-derived each claim against the current tree:
- The six files plus `test_account_phone_race.py` pass: 274 passed.
- All eight GREEN commits named in `16-REVIEW-DISPOSITION.md` are ancestors of `HEAD`.
- I probed the live functions and both gate predicates directly with `uv run python` scripts. Every new finding below was reproduced, not inferred.

What the batch got right:
- The CR-01 refusal is limited to country code 7, as promised. Italy (`+39 06 1234 5678` → `+390612345678`), UK with a typed trunk zero (`+44 020 7946 0958` → `+442079460958`) and the RU IDD form `8 10 44 7911 123456` → `+447911123456` are unaffected.
- The WR-05 existence probe can never run before the write, or instead of it. `_fill_if_unknown` always issues the conditional UPDATE first (`app/application/accounts/phone.py:105-114`). The probe is reached only when `rowcount != 1` (`:115-120`), and the order rule pins `[Update]` / `[Update, Select]`.
- `ACCOUNT_NOT_IN_SESSION` is a closed constant (`:70`) and carries no number.

New problems:
- **16-07 closed only half of the CR-01 class.** The RU metadata's 14-digit national length still lets a valid `+7` number with four extra digits be saved as an invented 15-digit "manual" number (WR-06).
- **The P-1 boundary in the module header understates what the auto path accepts.** It names only a 7-digit `TOO_SHORT` fragment. In fact every `TOO_LONG` and `INVALID_LENGTH` input is accepted, `TOO_SHORT` inputs longer than 7 digits are accepted, and so are `+7 0…` numbers (WR-07).
- **The single-writer gate's header again claims full literal coverage ("Всё, что видно литералом в исходнике, ловится" — "everything visible as a literal in the source is caught"), and that claim is again false.** Among the forms that still pass are `Connection.execute(..., parameters=[…])` and a list comprehension of literal dicts. Both are natural shapes for the Phase 20 backfill (WR-08).

## Prior findings — disposition

| ID | State | Evidence (current tree) |
|----|-------|-------------------------|
| CR-01 | **closed** (fix `97e62918`) | `app/services/phone.py:172-173` refuses `country_code == 7 and italian_leading_zero` with `PHONE_ERROR_NOT_A_NUMBER`. Probed: `00 44 7911 123456`, `0079991234567`, `7 0123456789`, `+70123456789`, `0 999 123 45 67` are all refused. The table rows `cr01_*` are at `tests/test_services/test_phone.py:275-283`, and the positive control `italian_leading_zero_is_not_plus_seven` is at `:228`. The scope is exactly the leading-zero subset. The sibling 14-digit invention is reported separately as new **WR-06**. |
| WR-01 | **closed** (fixes `a97179ab`, `78495634`) | All five forms named in WR-01 now produce an offence. Executemany by PK: `test_phone_single_writer_gate.py:229-241`, row `orm-bulk-update-by-pk` at `:659-666`. `dict(...)`: `:286-296` + `:316-321`, row `values-dict-call`. Literal `**{…}`: `:220-225`, row `values-double-star-dict`. `set_` of `on_conflict_do_update`: `:242-249`, row `upsert-set-dict`. `bulk_update_mappings`: row `bulk-update-mappings`. Other literal forms still pass; see new **WR-08**. |
| WR-02 | **closed** (fix `6ed63a95`) | `tests/test_phone_privacy_gate.py:149` `CONTEXT_BINDERS`, `:237-239` `_is_context_binding`, `:253` wired into `python_log_calls`. Probed: `structlog.contextvars.bind_contextvars(phone=…)` and `bind_contextvars(**{'phone': x})` both produce an offence. Remaining name-based gaps are in new **IN-06**. |
| WR-03 | **closed** (fix `fdb12dd5`) | `app/services/phone.py:266-268`: `tail_digits <= 2` → `head + " ***"`. `mask_phone("+88812") == "+888 ***"`, `mask_phone("+712") == "+7 ***"`. The leak rule (`test_phone.py:395-417`) now derives the national digit count and covers the short rows. |
| WR-04 | **closed** (fix `ae44c1d0`) | `app/services/phone.py:63` `REPORTED_MIN_DIGITS = 7`. `:213-215` refuses `IS_POSSIBLE_LOCAL_ONLY`. The pinned row moved to `REPORTED_REFUSED` as `five_digits_fragment_was_the_lower_bound` (`test_phone.py:115`). Probed: `12345`, `123456`, `88812`, `4412345`, `71234567` → `None`. The header's statement of what remains accepted is inaccurate; see new **WR-07**. |
| WR-05 | **closed** (fixes `67a25113`, `bee23ee2`) | `app/application/accounts/phone.py:89` `PhoneWrite.MISSING`. `:115-120`: probe only after a zero-row UPDATE. `:153-156`: `ValueError(ACCOUNT_NOT_IN_SESSION)` after flush. Tests are at `test_account_phone_writer.py:290-357`. The refusal is skipped on the unparseable path; see new **IN-07**. |
| IN-01 | **still open** (deferred per 16-REVIEW-DISPOSITION.md) | Unchanged: `app/application/accounts/phone.py:172-174` treats `None`/blank as "clear". `PHONE_ERROR_BLANK` is still reachable only through `normalize_manual` directly (`app/services/phone.py:165-166`). Addressee: Phase 18 form. |
| IN-02 | **still open** (deferred per 16-REVIEW-DISPOSITION.md) | Unchanged: `pyproject.toml:21` `"phonenumberslite==9.0.41"`. The new 16-07 bounds (`REPORTED_MIN_DIGITS` comment, `app/services/phone.py:54-59`) now cite measurements against this exact metadata version, which raises the cost of a silent bump. Addressee: owner / backlog. |
| IN-03 | **still open** (deferred per 16-REVIEW-DISPOSITION.md) | The predicate `MessengerAccount.phone_is_manual.is_(False)` is now at `app/application/accounts/phone.py:110`. `tests/test_application/test_account_phone_race.py` is byte-identical since `225fd3c7` (per 16-08 SUMMARY; no diff since `c3b0b232`). Dropping the predicate still keeps every test green. |
| IN-04 | **still open** (deferred per 16-REVIEW-DISPOSITION.md) | Unchanged since `c3b0b232`: `scripts/prohibitions_census.py:398-402` `_phase_number_of` raises `CensusError` for a non-integer phase. It is called at `:418` (`through_fixed_set`) and `:1337` (`reconcile_lines`). Addressee: backlog, census owner. |
| IN-05 | **still open** (deferred per 16-REVIEW-DISPOSITION.md) | Unchanged since `c3b0b232`: `tests/test_migrations/test_0023_messenger_account_phone.py:377-399` asserts child rows survive. There is no `PRAGMA foreign_keys` in `alembic/env.py` or `alembic/versions/0023_messenger_account_phone.py`. Addressee: backlog. |

## Narrative Findings (AI reviewer)

## Warnings

### WR-06: Manual input of a valid `+7` number plus four extra digits is saved as an invented 15-digit "manual" number

**File:** `app/services/phone.py:172-179` (also the docstring at `:137-148`)
**Issue:** This is the sibling of CR-01 that 16-07 left open.

16-07's own docstring (`:140-141`) names the cause: "RU-метаданные допускают национальную часть из 10 и 14 цифр" ("RU metadata allows a national part of 10 and 14 digits"). But the fix closes only the leading-zero subset. In `phonenumberslite==9.0.41`, the 14-digit RU length exists only for the toll-free pattern `8\d{13}` (`toll_free` `8(?:0[04]|108\d{3})\d{7}`). Every other `+7` national part of 14 digits is a typed number with extra digits.

Measured:

| Typed by the user | Saved (manual, locked by D-07) | Shown by `format_phone` |
|---|---|---|
| `+7 999 123-45-67 1234` (extension typed without `доб`/`ext`) | `+799912345671234` | `+7 99912345671234` |
| `8 999 123 45 67 8901` | `+799912345678901` | `+7 99912345678901` |
| `89991234567 8901` | `+799912345678901` | — |

Each is saved with `phone_is_manual=true`, so the auto source can never correct it (D-07). This is the same harm CR-01 was raised for. The extension path refuses `+7 999 123 45 67 доб 5` with `PHONE_ERROR_EXTENSION`, but the same input without the marker is saved. The table pins `one_digit_long` (`+7 999 123-45-678`, refused) but has no row at +4 digits, so the suite cannot see this.

**Fix:** The fix uses a parse attribute and does not call validity (D-05), like the CR-01 fix. A `+7` national part of 14 digits is legitimate only in the `8…` toll-free form, which can never be a messenger account. Owner choice:
```python
RU_KZ_NATIONAL_DIGITS = 10
...
if number.country_code == RU_KZ_COUNTRY_CODE and (
    number.italian_leading_zero
    or len(str(number.national_number)) != RU_KZ_NATIONAL_DIGITS
):
    raise PhoneError(PHONE_ERROR_NOT_A_NUMBER)
```
Add `MANUAL_REJECTED` rows `+7 999 123-45-67 1234` and `8 999 123 45 67 8901`. Update the docstring item 5 so it no longer reads as if the 14-digit admission were closed.

### WR-07: The P-1 boundary in the module header understates the auto path; `TOO_LONG`, `INVALID_LENGTH`, longer `TOO_SHORT` and `+7 0…` are all stored

**File:** `app/services/phone.py:33-37` (P-1 paragraph), `:190-196` (docstring), `:208-216`
**Issue:** The header names the remaining auto-path boundary as one case: "Семизначный обрывок с вердиктом `TOO_SHORT` (`1234567` → `+1234567`)" ("a 7-digit fragment with verdict `TOO_SHORT`"). The 16-07 SUMMARY repeats this ("a 7-digit `TOO_SHORT` fragment … is still stored").

The code refuses only `IS_POSSIBLE_LOCAL_ONLY` (`:213-215`). Every other verdict is stored. Measured with `normalize_reported`:

| Raw from source | Stored | Verdict |
|---|---|---|
| `799912345678` (Russian mobile + 1 digit) | `+799912345678` | `INVALID_LENGTH` |
| `79991234567890` | `+79991234567890` | `INVALID_LENGTH` |
| `1234567890123` | `+1234567890123` | `TOO_LONG` |
| `441234567890123` | `+441234567890123` | `TOO_LONG` |
| `123456789` (9 digits) | `+123456789` | `TOO_SHORT` |
| `70123456789` | `+70123456789` | `IS_POSSIBLE` |

Two of these contradict the module itself:
- The manual table refuses `+799912345678` as `twelve_digits` (`test_phone.py:270`), while the auto path stores the same digits.
- `RU_KZ_COUNTRY_CODE`'s comment (`:70-73`) says a `+7` national part "НИКОГДА не начинается с нуля" ("never starts with zero"), yet the auto path stores `+70123456789`.

The cost argument for P-1 (Fragment) does not cover these. Fragment `+888` has possible length `(11,)` in 9.0.41, so real Fragment numbers with 8–9 national digits give `TOO_SHORT`, not `TOO_LONG` or `INVALID_LENGTH`.

Stating the boundary honestly is what the owner's O-1 decision relies on. As written, a later fix that refuses `TOO_LONG` would look like a new restriction rather than closing a known gap.

**Fix:** Pick one:
- (a) Also refuse `TOO_LONG` and `INVALID_LENGTH`, and the code-7 leading zero, on the auto path. None of these is a Fragment shape. Add the measured rows above to `REPORTED_REFUSED`.
- (b) If the owner keeps them, rewrite the P-1 paragraph to state the real accepted set: "any parseable 7…15-digit value except `IS_POSSIBLE_LOCAL_ONLY`". Add a named table of rows accepted by that boundary, so the boundary is stated rather than presented as coverage.

### WR-08: The single-writer gate's header claims "Всё, что видно литералом в исходнике, ловится" ("everything visible as a literal in the source is caught"), but literal write forms still pass

**File:** `tests/test_application/test_phone_single_writer_gate.py:63-68` (claim), `:122` (`ROW_MAPPING_KEYWORDS`), `:299-313` (`_literal_mappings`), `:129-133` (`RAW_SQL_PHONE_WRITE`), `:108-111`
**Issue:** I fed each form below to `phone_write_offences`. Each returned `[]`:
```python
await conn.execute(update(MessengerAccount), parameters=[{"id": 1, "phone": p}])         # Connection/AsyncConnection kwarg
await s.execute(update(MessengerAccount), [{"id": a.id, "phone": n} for a, n in rows])    # comprehension of literal dicts
stmt = insert(MessengerAccount).values([{"user_id": u, "phone": n} for u, n in rows])
SQL = 'UPDATE messenger_accounts SET "phone" = :p WHERE id = :id'                        # quoted identifier
SQL = 'INSERT INTO "messenger_accounts" (user_id, phone) VALUES (1, :p)'                  # quoted table
SQL = "INSERT INTO public.messenger_accounts (user_id, phone) VALUES (1, :p)"            # schema-qualified
stmt = update(MessengerAccount).ordered_values((MessengerAccount.phone, x))
object.__setattr__(account, "phone", x)
```
- **`parameters=`:** 16-09 added `params=` deliberately (SUMMARY deviation 1) to close a keyword gap. But in SQLAlchemy 2.0.46, `Connection.execute` and `AsyncConnection.execute` name the argument `parameters` (verified by `inspect.signature`). Only `Session.execute` uses `params`.
- **Comprehensions:** a list comprehension whose element is a dict literal with a `"phone"` key is the natural shape for a Phase 20 backfill. The key is a literal in the source, and the gate can see it directly in the call's argument. It is not "a value assembled at runtime" in the sense the header's boundary uses for a variable.
- **Raw SQL:** the regex requires `\bphone\b\s*=` and a bare `messenger_accounts`, so quoting the identifier or qualifying the schema defeats it.

This is the WR-01 pattern again: the header names a boundary, and the predicate's real boundary is narrower.

**Fix:**
- Add `"parameters"` to `ROW_MAPPING_KEYWORDS`.
- In `_literal_mappings`, also return `node.elt` for `ast.ListComp`/`ast.GeneratorExp`/`ast.SetComp` when the element is a dict literal or a `dict(...)` call.
- Widen `RAW_SQL_PHONE_WRITE` to allow an optional quote around `phone(_is_manual)?` and an optional `"?\w+"?\.` schema prefix plus optional quotes on `messenger_accounts`.
- Add `ordered_values` to `WRITE_CALL_NAMES` (judge positional tuples whose first element is a `phone*` key) and `__setattr__` to `NAMED_ATTRIBUTE_WRITERS`.
- Plant each form as a row in `LITERAL_FORM_CASES`.

Alternatively, narrow the claim at `:68` to the forms actually judged.

## Info

### IN-06: The privacy gate's binder match misses an aliased import and the threadlocal binders

**File:** `tests/test_phone_privacy_gate.py:19-21, 149, 237-239`
**Issue:** `_is_context_binding` matches the callee's last name only. The header says the bare name after import is covered. These forms produce no offence:
- `from structlog.contextvars import bind_contextvars as bind_ctx; bind_ctx(phone=account.phone)`
- `structlog.threadlocal.bind_threadlocal(phone=account.phone)`

The second is deprecated but still shipped, along with `tmp_bind`. Neither form is in the live tree today.
**Fix:** Add `bind_threadlocal` and `tmp_bind` to `CONTEXT_BINDERS`. Resolve `ImportFrom` aliases of `structlog.contextvars`/`structlog.threadlocal` names in `python_log_calls`, or name the alias case in "ГРАНИЦА СРЕДСТВА" (the gate's stated boundary).

### IN-07: `record_reported_phone` still answers a forgotten `session.add` silently whenever the source sends no number

**File:** `app/application/accounts/phone.py:144-156`
**Issue:** The docstring says a Phase 19 wizard that forgot `session.add` "узнаёт об ошибке сразу" ("learns about the error at once"). But `normalize_reported` runs first (`:150-152`) and returns `UNPARSEABLE` before the id check. With an old worker that reports no number (PHONE-15), the commonest auto-source case, the caller error still produces a normal-looking outcome.
**Fix:** Check membership before normalizing, without issuing a statement: `if sqlalchemy.inspect(account).session is not session.sync_session: raise ValueError(ACCOUNT_NOT_IN_SESSION)`. Alternatively, narrow the docstring to "when the source reports a parseable number".

### IN-01: Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer — still open (deferred per 16-REVIEW-DISPOSITION.md)

**File:** `app/application/accounts/phone.py:172-174`; `app/services/phone.py:88, 165-166`
**Issue:** `set_manual_phone("")` clears the number, so an accidental empty submit in the Phase 18 form wipes a manual number. "Введите номер телефона" ("Enter a phone number") is reachable only through `normalize_manual` directly. D-07/PHONE-10 mandate this behaviour. Deferred to Phase 18 (owner decision O-4), which chooses between an explicit "clear" action and showing `PHONE_ERROR_BLANK`.

### IN-02: The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on — still open (deferred per 16-REVIEW-DISPOSITION.md)

**File:** `pyproject.toml:21`
**Issue:** Every other dependency uses `>=`. The `IS_POSSIBLE` check and all display formatting come from library metadata. With an exact pin, newly issued ranges or lengths are refused or misformatted until someone bumps the pin by hand. The new bounds in `app/services/phone.py:54-59` are measured against this exact version. Addressee: owner / backlog (O-4). Either write down the bump procedure, or use `>=9.0.41,<10`.

### IN-03: The race test cannot detect dropping the `phone_is_manual` predicate — still open (deferred per 16-REVIEW-DISPOSITION.md)

**File:** `tests/test_application/test_account_phone_race.py:252-264`; `app/application/accounts/phone.py:110`
**Issue:** The CHECK `ck_messenger_accounts_manual_requires_phone` makes `phone IS NULL` sufficient on its own. `phone_is_manual IS false` is redundant, and removing it keeps every test green. Do not read it as tested. PostgreSQL's READ COMMITTED re-check is also untested; the revision header states that limit.

### IN-04: `reconcile_lines` crashes on decimal phase directories (copied from Phase 15) — still open (deferred per 16-REVIEW-DISPOSITION.md)

**File:** `scripts/prohibitions_census.py:398-402, 1334-1338`
**Issue:** `_phase_number_of` raises `CensusError` for a directory such as `16.1-…`, which GSD's inserted phases use. The defect predates this phase: it was introduced in `49ca9ddf` (15-15), and this phase copied it into `reconcile_lines`. Addressee: backlog, owner of `scripts/prohibitions_census.py`. Parse the major number with `int(phase.split(".")[0])`, or decide explicitly that decimal phases are out of scope.

### IN-05: The migration test's claim that "children survive the recreate" is only proven with SQLite foreign keys off — still open (deferred per 16-REVIEW-DISPOSITION.md)

**File:** `tests/test_migrations/test_0023_messenger_account_phone.py:377-399`; `alembic/versions/0023_messenger_account_phone.py:167-172`
**Issue:** In batch mode, `DROP TABLE messenger_accounts` would cascade-delete `groups` and null out `schedules.account_id` under `PRAGMA foreign_keys=ON`. `alembic/env.py` does not enable it, so the test passes. Production PostgreSQL is not affected. Addressee: backlog. Name the precondition in the header, or execute `PRAGMA foreign_keys=OFF` on the SQLite branch.

---

_Reviewed: 2026-10-09_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `c3b0b232`)_
