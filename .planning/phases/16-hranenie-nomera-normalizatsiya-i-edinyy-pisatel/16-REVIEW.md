---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-08T00:00:00Z
depth: standard
files_reviewed: 18
files_reviewed_list:
  - alembic/versions/0023_messenger_account_phone.py
  - app/application/accounts/phone.py
  - app/models/messenger_account.py
  - app/services/phone.py
  - pyproject.toml
  - scripts/prohibitions_census.py
  - tests/test_application/test_account_phone_race.py
  - tests/test_application/test_account_phone_writer.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_migrations/test_0023_messenger_account_phone.py
  - tests/test_migrations/test_model_matches_head.py
  - tests/test_models/test_messenger_account_phone_check.py
  - tests/test_phone_privacy_gate.py
  - tests/test_planning/test_deferred_items_are_idempotent.py
  - tests/test_planning/test_plan_prohibitions_census.py
  - tests/test_planning/test_requirement_completion_follows_verification.py
  - tests/test_planning/test_state_progress_matches_roadmap.py
  - tests/test_services/test_phone.py
findings:
  critical: 1
  warning: 5
  info: 5
  total: 11
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-10-08
**Depth:** standard
**Files Reviewed:** 18
**Status:** issues_found

## Summary

I reviewed the diff from `41e2396f` to HEAD for the 18 listed files. The phase's own tests (246 of them) pass. I also ran probes against the live functions and the two gate predicates. Every finding below was reproduced, not inferred.

Parts that hold up:
- The schema half (revision 0023, the model CHECK, `copy_from` keeping `ON DELETE`) is sound.
- The single-statement conditional UPDATE in the writer is correct on PostgreSQL. Under READ COMMITTED, a blocked UPDATE re-checks its WHERE against the committed row version, so a manual write that commits first wins. On asyncpg, `rowcount` for UPDATE is reliable.

Main problems:
- **The manual normalizer invents Russian numbers.** It turns several common real-world ways of writing a foreign or local number into a made-up `+7 0…` number. Examples: the `00` international prefix, and a Ukrainian or Belarusian local number with a leading 0.
- **Both cross-cutting gates have blind spots.** Each misses forms that can be seen directly in the source code, and the privacy gate misses one form that this project already uses (`structlog.contextvars.bind_contextvars`).

Pre-existing defects: I found no defect in the touched production files that predates the phase. One pre-existing fragility in `scripts/prohibitions_census.py` was copied into a second place (IN-04).

The new tests pin one questionable behaviour as correct: `five_digits_lower_bound` (`"12345"` → `"+12345"`), see WR-04.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Manual input with the `00` prefix or a leading-0 local number is saved as a made-up `+7 0…` number

**File:** `app/services/phone.py:130-140`
**Issue:** `normalize_manual` parses with region `RU`. The RU international dialling prefix is `810`, not `00`. The RU metadata also allows a 14-digit national number (`possible_length == (10, 14)`). So any input whose national significant number begins with `0` and has 10 or 14 digits passes the `IS_POSSIBLE` check and is saved as a Russian number that cannot exist (no Russian number starts with 0). Measured results:

| Typed by the user | Saved |
|---|---|
| `00 44 7911 123456` (UK mobile) | `+700447911123456` |
| `00 380 50 123 4567` (Ukraine) | `+700380501234567` |
| `00 90 532 123 4567` (Turkey) | `+700905321234567` |
| `00 1 202 555 01234` | `+700120255501234` |
| `050 123 4567` (Ukrainian local) | `+70501234567` |
| `8 029 123 45 67` (Belarus long-distance) | `+70291234567` |

No error is raised. Phase 18's form would show "saved". Because `phone_is_manual=true`, the auto source then **can never correct it** (D-07). This contradicts D-06: "garbage … is rejected, not turned into a 'number'". `MANUAL_ACCEPTED` and `MANUAL_REJECTED` have no rows for `00…` or for a leading-0 national number, so the suite does not see this.

D-05 says only "`parse(text, "RU")` → `is_possible_number` → E.164". The defect follows from applying that wording literally. The fix below does **not** need `is_valid_number`, which D-05 forbids, so it stays inside the owner's decision.

**Fix:**
```python
number = _parse_or_none(text, MANUAL_REGION)
if number is None:
    raise PhoneError(PHONE_ERROR_NOT_A_NUMBER) from None
if number.extension:
    raise PhoneError(PHONE_ERROR_EXTENSION)
# A +7 national number never starts with 0: a leading zero means "00"/IDD or a
# foreign local number misread under RU, never a real Russian/Kazakh number.
if number.country_code == 7 and number.italian_leading_zero:
    raise PhoneError(PHONE_ERROR_NOT_A_NUMBER)
```
Optionally, first rewrite a leading `00` (after stripping) to `+`, so that `00 44 …` is accepted as `+44 …`. Add rows for `00 44 7911 123456`, `050 123 4567` and `8 029 123 45 67` to `MANUAL_REJECTED` (or to `MANUAL_ACCEPTED` if you add the `00`→`+` rewrite).

## Warnings

### WR-01: The single-writer gate misses five write forms that are visible in the source

**File:** `tests/test_application/test_phone_single_writer_gate.py:86-89, 175-190`
**Issue:** `phone_write_offences` returns `[]` for each of the following. I fed them to the predicate to confirm:
```python
await session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])   # ORM bulk UPDATE by PK
stmt = update(MessengerAccount).values(dict(phone=x))                      # dict(...) call
stmt = update(MessengerAccount).values(**{"phone": x})                     # literal ** dict
insert(MessengerAccount).values(...).on_conflict_do_update(set_={"phone": x})
session.bulk_update_mappings(MessengerAccount, [{"id": 1, "phone_is_manual": True}])
```
The header lists "a value assembled at runtime" as the gate's boundary. These five forms are not runtime values: each is a literal you can read in the source. The first form, an executemany of a list of dicts by primary key, is the natural shape for the Phase 20 backfill script. That script is exactly the "second writer" D-13 exists to catch.
**Fix:** Do all of the following:
- In `_values_dict_keys`, also inspect `**`-keywords whose value is an `ast.Dict`, and `dict(...)` calls with `phone*` keywords.
- Treat `set_` of `on_conflict_do_update` as a write call.
- For `execute` and `bulk_update_mappings`/`bulk_insert_mappings`, scan list/dict arguments for `phone*` string keys.
- Add each form as a planted case in the test file.

### WR-02: The privacy gate misses `structlog.contextvars.bind_contextvars(phone=…)`, a pattern the project uses

**File:** `tests/test_phone_privacy_gate.py:114-132, 213-215`
**Issue:** The gate's header gives a reason for including `bind`: "a bound value goes into every following line". `bind_contextvars` binds into the global structlog context in exactly the same way. The project already calls it in `app/middleware.py:19` and `app/worker/tasks.py:260`. Its callee name is not in `LOG_METHODS`, and its receiver `structlog.contextvars` does not match `_LOGGER_NAME`. Confirmed: `structlog.contextvars.bind_contextvars(phone=account.phone)` produces no offence.
**Fix:** In `_is_log_method_call`/`python_log_calls`, treat any call whose callee name is `bind_contextvars` as a log call, whatever the receiver. Add a planted row to the Python half.

### WR-03: `mask_phone` shows the whole number when the national part has 2 digits or fewer

**File:** `app/services/phone.py:211-223`
**Issue:** The branch for parseable values masks all but the last two digits of the national part, with no minimum. `normalize_reported("88812")` stores `+88812`, and `mask_phone("+88812")` returns `"+888 12"`: nothing is masked. The branch for unparseable values has a guard (`< 4 digits → "+***"`); the parseable branch does not. The leak check `test_a_mask_shows_only_the_country_code_and_two_last_digits` only uses numbers with 8 or more national digits, so it never reaches this case.
**Fix:** Apply the same floor in the parseable branch. If `tail_digits <= 2`, return `head + " ***"`, or mask everything except the country code. Add `"+88812"` to `MASKED`.

### WR-04: The auto-path lower bound of 5 digits saves source junk as a "number"; a test pins this

**File:** `app/services/phone.py:44, 165`; `tests/test_services/test_phone.py:81`
**Issue:** `REPORTED_MIN_DIGITS = 5` was a discretion choice, not a locked decision. With it, `"12345"` → `"+12345"` (a "US" number with a 4-digit national part), `"4412345"` → `"+4412345"`, and `"88812"` → `"+88812"`. D-06 requires that garbage be rejected. Real Telegram, WhatsApp, MAX and Fragment numbers all have at least 7 digits (Fragment `+888` numbers have 11). The new row `five_digits_lower_bound` asserts the junk-acceptance as correct. Raising the bound later will turn that test red and look like a regression.
**Fix:** Raise `REPORTED_MIN_DIGITS` to 7, or 8. Move `"12345"` to `REPORTED_REFUSED` and keep a 7- or 8-digit row as the boundary.

### WR-05: Auto writers return `KEPT` when no row was updated at all

**File:** `app/application/accounts/phone.py:86, 113-115`
**Issue:**
- `_fill_if_unknown` maps any `rowcount != 1` to `KEPT`, whose docstring says it means "the row already has a number, or the user was first". Confirmed: `fill_reported_phone(session, 9999, "79991234567")` on a missing account returns `KEPT`.
- `record_reported_phone` with an account that was never `session.add`-ed: `flush()` does not insert it, `account.id` stays `None`, and the UPDATE runs `WHERE id IS NULL`. Result: `KEPT` with `account.id is None` (confirmed).

The Phase 20 backfill would count deleted accounts as "user was first", and a Phase 19 wizard bug that forgets `session.add` would fail silently. This is also inconsistent with `set_manual_phone`, which raises `LookupError` on the same condition.
**Fix:** In `record_reported_phone`, after the flush, `if account.id is None: raise ValueError("account is not in the session")`. In `_fill_if_unknown`, either add `PhoneWrite.MISSING`, chosen with a `select(exists())` when `rowcount == 0`, or document that `KEPT` includes "row absent" and rename it.

## Info

### IN-01: Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer

**File:** `app/application/accounts/phone.py:130-132`; `app/services/phone.py:63, 128-129`
**Issue:** `set_manual_phone("")` clears the number. An accidental empty submit in the Phase 18 form wipes a manual number. The "Введите номер телефона" ("Enter a phone number") text is only reachable if a caller uses `normalize_manual` directly. This is mandated by D-07/PHONE-10. I flag it so that Phase 18 decides between an explicit "clear" action and showing `PHONE_ERROR_BLANK`.

### IN-02: The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on

**File:** `pyproject.toml:21`
**Issue:** Every other dependency uses `>=`. The manual path's `IS_POSSIBLE` check and all display formatting come from library metadata. With an exact pin, a newly issued number range or length is refused or misformatted until someone bumps the pin by hand. If the pin is intentional, write down the bump procedure; otherwise use `>=9.0.41,<10`.

### IN-03: The race test cannot detect dropping the `phone_is_manual` predicate

**File:** `tests/test_application/test_account_phone_race.py:252-264`; `app/application/accounts/phone.py:81`
**Issue:** The CHECK constraint guarantees that `phone_is_manual` implies `phone IS NOT NULL`, so `WHERE phone IS NULL` alone is enough. The predicate `phone_is_manual IS false` is redundant, and removing it keeps every test green. This is not a bug. Note it so nobody reads that predicate as tested. PostgreSQL's READ COMMITTED re-check is also not tested; that limit is stated honestly in the revision header.

### IN-04: `reconcile_lines` now crashes on decimal phase directories (copied from Phase 15)

**File:** `scripts/prohibitions_census.py:1334-1338`; `tests/test_planning/test_plan_prohibitions_census.py:939-944`
**Issue:** `_phase_number_of` raises `CensusError` for a directory such as `16.1-…`, which GSD's inserted phases use. The old filter `phase_of(path) != "15"` did not raise. This is pre-existing in `through_fixed_set`, introduced in `49ca9ddf` (15-15, 2026-09-25); the phase copies it into a second function. Parse the major number with `int(phase.split(".")[0])`, or decide explicitly that decimal phases are out of scope.

### IN-05: The migration test's claim that "children survive the recreate" is only proven with SQLite foreign keys off

**File:** `tests/test_migrations/test_0023_messenger_account_phone.py:377-399`; `alembic/versions/0023_messenger_account_phone.py:167-172`
**Issue:** In batch mode, `DROP TABLE messenger_accounts` deletes rows implicitly. With `PRAGMA foreign_keys=ON` it would cascade-delete `groups` and null out `schedules.account_id`. `alembic/env.py` does not turn the pragma on, so the test passes, but the header presents preserved child rows as a property of the revision. Production is PostgreSQL and is not affected. Either name the precondition (FK enforcement off during batch) in the header, or have the revision execute `PRAGMA foreign_keys=OFF` on the SQLite branch.

---

_Reviewed: 2026-10-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
