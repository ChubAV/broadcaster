---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-10T06:59:01Z
depth: standard
review_kind: incremental
diff_base: 7ad786703ac8b43128ff186b7f00f50c83d2e4cb
head: 720cbd5e
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
  warning: 2
  info: 3
  total: 5
carried_forward: 5
closed_prior: 5
status: issues_found
---

# Phase 16: Code Review Report (incremental re-review after gap batch 16-11…16-14)

**Reviewed:** 2026-10-10T06:59:01Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This is an incremental re-review. The diff base is `7ad78670`, the commit of the prior review, and `HEAD` is `720cbd5e`. It covers the six files changed by gap batch 16-11…16-14:
- the `+7` and auto-path refusals (16-11);
- the single-writer gate widening (16-12);
- the privacy gate's aliases and module loggers (16-13);
- the writer's session-membership check (16-14).

This report replaces the prior `16-REVIEW.md`. Each prior finding appears once below, in a table with its original title. Its state is either `closed`, with evidence, or `still open`.

What I checked:
- **Tests.** The six files pass: `408 passed` (22 + 119 + 94 + 173), run under the shared flock with `-p no:randomly`.
- **Commits.** Every GREEN commit cited in `16-REVIEW-DISPOSITION.md` for WR-06/07/08 and IN-06/07 is an ancestor of `HEAD`: `02d73c93`, `2565d515`, `f10abdd7`, `2ccdb4d2`, `6c862686`, `e168d3dd`, `3bd2e6a0`, `58550bb3`, `164a0276`, plus the guard `1fad15e3`. I checked each with `git merge-base --is-ancestor`.
- **Probes.** I called the live functions and both gate predicates directly from `uv run python` scratch scripts. I checked SQLAlchemy 2.0.46 behaviour on a throwaway in-memory SQLite engine. Every new finding below was reproduced, not inferred.
- **Deferred findings.** The batch did not touch the code behind IN-01…IN-05. `git diff 7ad78670..HEAD` is empty for `pyproject.toml`, `test_account_phone_race.py`, `scripts/prohibitions_census.py`, `tests/test_migrations/test_0023_*` and `alembic/`, and `set_manual_phone` and the `phone_is_manual` predicate are unchanged.

What the batch got right:
- The shared predicate `_is_impossible_zone_seven` (`app/services/phone.py:159-176`) closes the `+7` extra-digit class on both paths. The 4×5 enumeration pins it and includes an anti-vacuum step on each base.
- The auto path refuses `TOO_LONG` / `INVALID_LENGTH`. I re-ran the enumeration: 1935 inputs, 583 accepted as `TOO_SHORT` and 558 as `IS_POSSIBLE`, none with a refused verdict. This matches the header's "583 of 1935".
- The membership check in `record_reported_phone` issues no statement and does not flush. A foreign-session object is refused. I verified that by probe; it is not covered by a test (see IN-10).

New problems:
- **WR-06's harm survives outside code 7.** A Belarusian, Ukrainian, Kyrgyz, Turkish, Israeli, Chinese or German number typed with extra digits is still saved as an invented, locked "manual" number. Nothing in the code names this boundary (WR-09).
- **The single-writer gate over-claims a third time.** The header now claims coverage "through the mechanism", but `Query.update(values={…})`, the keyword form of `set_attribute`, and `run_sync(Session.bulk_update_mappings, …)` all write the column and pass. None of the three is among the five named unreachable forms (WR-10).
- Three smaller honesty gaps (IN-08, IN-09, IN-10).

## Prior findings — disposition

Titles are copied verbatim from the prior report, with the appended « — still open (deferred per 16-REVIEW-DISPOSITION.md)» suffix stripped. Status is in the State column only. CR-01 and WR-01…WR-05 were already closed in the prior pass and are not repeated.

| ID | Original title | State | Evidence (current tree `720cbd5e`) |
|----|----------------|-------|------------------------------------|
| WR-06 | Manual input of a valid `+7` number plus four extra digits is saved as an invented 15-digit "manual" number | closed (fix `02d73c93`, ancestor of HEAD) | `app/services/phone.py:237-238` calls `_is_impossible_zone_seven` (`:159-176`; `RU_KZ_NATIONAL_DIGITS = 10` at `:110`). Probed: `+7 999 123-45-67 1234`, `8 999 123 45 67 8901` and `89991234567 8901` → `PHONE_ERROR_NOT_A_NUMBER`. The rows are `wr06_*` (`tests/test_services/test_phone.py` `MANUAL_REJECTED`) plus the 4×5 class rule at `:512-551`. The closure is honest for code 7 only. The same harm in other zones is new **WR-09**. |
| WR-07 | The P-1 boundary in the module header understates the auto path; `TOO_LONG`, `INVALID_LENGTH`, longer `TOO_SHORT` and `+7 0…` are all stored | closed (fix `2565d515`, ancestor of HEAD) | `REPORTED_REFUSED_VERDICTS` is at `app/services/phone.py:86-92`, the refusal at `:285-288`. Every row in the prior WR-07 table now gives `None` except `123456789` (`TOO_SHORT`, code 1). That value is named in the new boundary paragraph at `:37-45`. The owner chose (a) (O-5). The remaining TOO_SHORT boundary is honestly named. The paragraph's framing "Кроме настоящих номеров" ("besides real numbers") hides a second accepted class; see new **IN-08**. |
| WR-08 | The single-writer gate's header claims "Всё, что видно литералом в исходнике, ловится" ("everything visible as a literal in the source is caught"), but literal write forms still pass | closed (fixes `f10abdd7`, `2ccdb4d2`, `6c862686`, `e168d3dd`, ancestors of HEAD) | All eight forms from the prior WR-08 code block now produce exactly one offence. Each is planted in `LITERAL_FORM_CASES`, and I re-checked `parameters=`, the comprehension, `values([… for …])`, quoted column, quoted table, schema prefix, `ordered_values` and `object.__setattr__` with `phone_write_offences`. The "everything" claim is gone (`test_phone_single_writer_gate.py:120-129` keeps it only as history). The five named unreachable forms (`:100-115`) are stated with reasons. The new mechanism claim is itself narrower than the predicate in three places; see new **WR-10**. |
| IN-06 | The privacy gate's binder match misses an aliased import and the threadlocal binders | closed (fixes `3bd2e6a0`, `58550bb3`, ancestors of HEAD) | `CONTEXT_BINDERS` is at `tests/test_phone_privacy_gate.py:192-194` and covers `bind_threadlocal`, `bound_threadlocal` and `tmp_bind`. `module_log_names` (`:295-338`) resolves `bind_ctx` aliases. Probed: both forms named in the prior IN-06 produce an offence. The aliased factory import and the plain re-assignment `a = lg` are named in "ГРАНИЦА СРЕДСТВА" (the gate's stated boundary, `:119`, `:122-123`), as the SUMMARY says. Two forms identifiable "по ввозу" ("by import") or by module binding are neither caught nor named; see new **IN-09**. |
| IN-07 | `record_reported_phone` still answers a forgotten `session.add` silently whenever the source sends no number | closed (fix `164a0276`, guard `1fad15e3`, ancestors of HEAD) | `app/application/accounts/phone.py:164-165` checks membership before `normalize_reported`. The test `test_recording_an_account_never_added_to_the_session_raises[none\|empty\|garbage\|parseable]` pins zero statements and `id is None`. A pending member with garbage input gets `UNPARSEABLE` with no flush (`test_recording_garbage_for_a_pending_member_issues_nothing`). The other-session case is untested. The test docstring's stated reason for that is false; see new **IN-10**. |
| IN-01 | Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer | still open: deferred, not re-verified (outside this batch) | Owner decision O-4. Addressee: Phase 18 form. `set_manual_phone` (`app/application/accounts/phone.py:179-199`) is unchanged in substance by this batch; only its line numbers moved. |
| IN-02 | The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on | still open: deferred, not re-verified (outside this batch) | Owner decision O-4. Addressee: owner / backlog. `pyproject.toml` is untouched since `7ad78670`. The batch adds more measurements tied to 9.0.41 (`app/services/phone.py:72`, `:81-85`, `:104-109`, `:41-42`), which raises the cost of a silent bump. |
| IN-03 | The race test cannot detect dropping the `phone_is_manual` predicate | still open: deferred, not re-verified (outside this batch) | Owner decision O-4. The predicate is now at `app/application/accounts/phone.py:110`. `test_account_phone_race.py` is untouched since `7ad78670`. |
| IN-04 | `reconcile_lines` crashes on decimal phase directories (copied from Phase 15) | still open: deferred, not re-verified (outside this batch) | Owner decision O-4. Addressee: backlog, census owner. `scripts/prohibitions_census.py` is untouched since `7ad78670`. |
| IN-05 | The migration test's claim that "children survive the recreate" is only proven with SQLite foreign keys off | still open: deferred, not re-verified (outside this batch) | Owner decision O-4. Addressee: backlog. The migration test and `alembic/` are untouched since `7ad78670`. |

## Narrative Findings (AI reviewer)

## Warnings

### WR-09: Manual input of a non-`+7` number plus extra digits is still saved as an invented "manual" number (BY, UA, KG, TR, IL, CN, DE)

**File:** `app/services/phone.py:159-176` (`_is_impossible_zone_seven` returns `False` for every code other than 7), `:193-213` (docstring item 5), `:237-240`; `tests/test_services/test_phone.py:512-517` (`EXTRA_DIGIT_BASES` contains only `+7` bases)
**Issue:** WR-06 was raised because a real number with extra digits typed without `доб`/`ext` is saved under `phone_is_manual=true`. No auto source can then correct it (D-07). 16-11 closed that harm for code 7 only. For every other code, the only guard is the metadata's general possible lengths. Those lengths are the union over all number types, so they admit extra digits wherever any number type (toll-free, premium, shared cost) is longer than mobile. Measured with `normalize_manual` on `phonenumberslite==9.0.41` (extra digits = how many trailing digits were added; OK = saved):

| Base (real mobile) | +1 | +2 | +3 | +4 | Saved for +1 |
|---|---|---|---|---|---|
| `+375 29 123 45 67` (Belarus) | OK | OK | refused | refused | `+3752912345671` |
| `+380 50 123 4567` (Ukraine) | OK | refused | refused | refused | `+3805012345671` |
| `+996 700 123 456` (Kyrgyzstan) | OK | refused | refused | refused | — |
| `+90 532 123 45 67` (Turkey) | refused | OK | OK | refused | — |
| `+972 50 123 4567` (Israel) | OK | OK | OK | refused | — |
| `+86 138 0013 8000` (China) | OK | refused | refused | refused | `+86138001380001` |
| `+49 151 23456789` (Germany) | OK | OK | refused | refused | — |

Belarus and Ukraine are the likeliest non-RU inputs for this product. Turkey is non-monotonic: +1 is refused while +2 and +3 are saved. That is the same shape the verifier used to reopen WR-06.

The code does not name this boundary. Docstring item 5 says "Условие ограничено кодом 7: у Италии `+39 06 …` ведущий ноль законен" ("The condition is limited to code 7: in Italy a leading zero `+39 06 …` is legitimate"), which explains the limit only for the leading-zero half. The 16-REVIEW-DISPOSITION row says "класс «номер плюс лишние цифры» закреплён перебором" ("the class 'number plus extra digits' is pinned by enumeration"). That reads wider than the code-7-only enumeration.

**Fix:** This stays within D-05: it checks lengths only and never calls the validity check. On the manual path, require the number to be possible for an account-shaped type:
```python
_ACCOUNT_NUMBER_TYPES = (
    PhoneNumberType.MOBILE, PhoneNumberType.FIXED_LINE,
    PhoneNumberType.FIXED_LINE_OR_MOBILE, PhoneNumberType.VOIP,
)
...
if not any(
    phonenumbers.is_possible_number_for_type_with_reason(number, kind) == ValidationResult.IS_POSSIBLE
    for kind in _ACCOUNT_NUMBER_TYPES
):
    raise PhoneError(PHONE_ERROR_NOT_A_NUMBER)
```
Measured:
- This refuses every +1/+2 row in the table above.
- No `MANUAL_ACCEPTED` row is refused.
- Every regional example number of those four types in the 9.0.41 metadata is still accepted.
- Including `TOLL_FREE` re-admits every row in the table, so leave it out. That uses the same argument the module already makes for RU `8108…`: a toll-free number is never a messenger account.

Add `EXTRA_DIGIT_BASES` rows for BY, UA and TR. If the owner keeps the current behaviour, name the boundary in item 5 and narrow the disposition wording to "code 7".

### WR-10: The single-writer gate's new "through the mechanism" claim is again wider than the predicate: `Query.update(values=…)`, keyword `set_attribute`, and `run_sync(Session.bulk_*_mappings, …)` pass

**File:** `tests/test_application/test_phone_single_writer_gate.py`:
- `:36-46`: header kinds 3 and 4.
- `:96-118`: the boundary. "Ловится всякая запись, в которой колонка номера … названа литералом в самом пишущем вызове, в его аргументе-контейнере" ("Every write is caught in which the phone column … is named by a literal in the writing call itself, or in its container argument").
- `:360-363`: only positional args of `update(...)` are judged.
- `:413-431`: named-attribute writers are judged by position only.
- `:372-386`: row mappings only when the call name itself is `execute`/`bulk_*`.

**Issue:** Each form below names the phone column as a literal in the writing call's own argument. Each falls under the header's mechanism claim and none of the five named unreachable forms. `phone_write_offences` returns `[]` for each. On SQLAlchemy 2.0.46 the first two emit a real write: on a scratch engine I saw `UPDATE a SET phone=?`, and the value persisted.
```python
session.query(MessengerAccount).filter_by(id=i).update(values={"phone": x})   # Query.update(self, values, …)
set_attribute(account, key="phone", value=x)                                  # signature (instance, key, value, initiator=None)
set_committed_value(account, key="phone", value=x)                            # same keyword form, kind 4
await session.run_sync(Session.bulk_update_mappings, MessengerAccount, [{"id": 1, "phone": p}])
stmt = update(MessengerAccount).values(**{"phone": n for n in [x]})           # boundary (1) excludes only "{k: v for …} с вычисленными ключами" (with computed keys)
```
- `run_sync(fn, *args)` is the AsyncSession way to reach a sync-only bulk API, and this project is async throughout, so for Phase 20 this form is plausible.
- `Query.update` is legacy, but the header names it explicitly as kind 3 and judges only its positional form.
- The header's own rule (`:116-118`) is: "Форма, которая под механизм подпадает, но предикатом не ловится, — слепота предиката" ("A form that falls under the mechanism but is not caught by the predicate is a blindness of the predicate"). This is the WR-01 → WR-08 pattern a third time, and less severe each time.

**Fix:**
- In the `update`/`values` branch, also judge `keyword.arg == "values"` through `_literal_mappings`.
- For `NAMED_ATTRIBUTE_WRITERS`, also judge a `key=` keyword (and `name=` for `setattr`-like calls) whose value is a `PHONE_COLUMNS` constant.
- For a call whose positional argument is a `Name`/`Attribute` with last name in `ROW_MAPPING_CALL_NAMES` (the `run_sync(Session.bulk_update_mappings, …)` shape), judge the remaining positional arguments as rows.
- In `_literal_mappings`, return an `ast.DictComp` whose `key` is a `PHONE_COLUMNS` constant, and handle it in `_mapping_phone_keys`.
- Plant each form as a `LITERAL_FORM_CASES` row.

Alternatively, add a sixth named unreachable form: "API reached through a function reference or a keyword the predicate does not judge".

## Info

### IN-08: The auto-path boundary paragraph says "besides real numbers" the only extra acceptance is `TOO_SHORT`; 400 of the 558 `IS_POSSIBLE` values accepted in the same enumeration are not valid numbers

**File:** `app/services/phone.py:37-45`
**Issue:** The paragraph reads: "Кроме настоящих номеров автопуть принимает ЛЮБОЕ разбираемое значение из 7…15 цифр с вердиктом `TOO_SHORT`" ("Besides real numbers, the auto path accepts ANY parseable 7…15-digit value with verdict `TOO_SHORT`"). That implies every accepted `IS_POSSIBLE` value is a real number. It is not. Re-running the header's own enumeration (code × length 7…15, filler `2345678901234567`):
- 558 values are accepted as `IS_POSSIBLE`;
- 400 of those fail `is_valid_number`;
- examples: `+72345678901`, `+2023456789`, `+2723456`;
- probes outside the enumeration give the same: `10000000000` → `+10000000000` and `440000000000` → `+44000000000`.

A NANP number cannot start with 0 or 1 after `+1`, which is structurally the same as a `+7` national part starting with 0. Yet `+7 0…` is refused and `+1 0…` is stored. D-05 justifies skipping validity ("ложный отказ хуже пропуска" — "a false refusal is worse than a miss"). The boundary paragraph should still say this class exists rather than frame the remainder as "real numbers".
**Fix:** Reword as: "besides numbers the metadata considers possible (including ones it considers invalid, D-05) …". Optionally cite the 400/558 measurement next to 583/1935.

### IN-09: The privacy gate neither catches nor names two logger forms that are identifiable by import or module binding

**File:** `tests/test_phone_privacy_gate.py:17-23` (what counts as a log call), `:110-128` (ГРАНИЦА СРЕДСТВА, the gate's stated boundary), `:307-322`, `:331-337`
**Issue:** The boundary justifies every out-of-scope form with one argument: the logger "нельзя опознать ни по фабрике, ни по имени журнала, ни по ввозу" ("cannot be identified by factory, by logger name, or by import"). Two forms can be identified that way, yet produce no offence and are not listed:
- `from logging import info` / `from logging import warning as warn_`, then `info("n=%s", account.phone)`. This is a direct import of a `logging` module function. `module_log_names` only treats an `ImportFrom` alias as a receiver when the imported name looks like a logger (`:313`).
- A class-body binding used through the instance or the class: `class S: lg = structlog.get_logger()` and then `self.lg.info(..., phone=…)` / `cls.lg.warning(...)`. The class-body `Assign` target is an `ast.Name`, so `lg` goes into `receiver_names` (`:332-334`). The call site is an `ast.Attribute`, which is matched only against `receiver_attributes`. The header lists `self.lg = structlog.get_logger()` as covered; this sibling form is not.

`if (lg := logging.getLogger()): lg.info(account.phone)` is also missed (`NamedExpr` is not collected at `:319-322`), but it is contrived. None of these forms occurs in the live tree today.
**Fix:**
- Treat `ImportFrom` names from module `logging` that are in `LOG_METHODS` as bare log calls.
- When a class-body `Assign`/`AnnAssign` binds a receiver, also add the name to `receiver_attributes`.
- Or list both forms in ГРАНИЦА СРЕДСТВА with a reason.

### IN-10: The other-session case of `record_reported_phone` is left untested on a false premise, and the refusal text gives wrong advice for it

**File:** `tests/test_application/test_account_phone_writer.py:369-394`; `app/application/accounts/phone.py:70`, `:150-152`, `:169-172`
**Issue:**
- **False premise.** The test docstring says the foreign-session case is pinned only through a detached object because "вторая сессия к базе `:memory:` в фикстуре не гарантирована" ("a second session to the `:memory:` database is not guaranteed in the fixture"). A second session needs no database. The membership check reads `inspect(account).session` and never executes anything. I probed `other = AsyncSession(); other.add(account); await record_reported_phone(db_session, account, "79991234567")` with no bind: it raises `ValueError(ACCOUNT_NOT_IN_SESSION)`. So the case is trivially testable.
- **Single-value parametrize.** `@pytest.mark.parametrize("detach", ["detached"])` has one value. It makes the rule look like a matrix that does not exist.
- **Wrong advice.** `ACCOUNT_NOT_IN_SESSION` reads "добавьте его через session.add" ("add it via session.add"). For a foreign-session object that advice fails: `session.add` raises `InvalidRequestError` ("already attached to session"). The same text is raised by the post-flush check at `:171-172`, where the object is by construction already in the session.

**Fix:**
- Add a `"foreign"` row: create a fresh unbound `AsyncSession()` in the test, `add` a new `MessengerAccount`, assert the `ValueError`, assert zero statements on `db_session`, then close it.
- Reword the constant neutrally, e.g. "аккаунт не принадлежит сессии писателя" ("the account does not belong to the writer's session").
- Give the post-flush line its own closed constant, e.g. "после flush у аккаунта нет id" ("the account has no id after flush").

---

_Reviewed: 2026-10-10T06:59:01Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `7ad78670`, head `720cbd5e`)_
