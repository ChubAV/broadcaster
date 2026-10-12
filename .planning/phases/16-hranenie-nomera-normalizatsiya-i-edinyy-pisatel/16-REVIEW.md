---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-12T20:15:50Z
depth: standard
review_kind: incremental
diff_base: 388add7184e27f4b42f2243c116888c6ec31af62
head: 4bd0276f
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
  info: 2
  total: 5
carried_forward: 0
closed_prior: 5
status: issues_found
---

# Phase 16: Code Review Report (incremental re-review after gap batch 16-16…16-20)

**Reviewed:** 2026-10-12T20:15:50Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This is an incremental re-review. The diff base is `388add71`, the commit of the prior review, and `HEAD` is `4bd0276f`. It covers the six files changed by gap batch round 3:
- account-type refusal on the manual path and the auto-path header (16-16);
- single-writer gate: `JUDGED_PARAMETERS`, writer API by reference, kind 1 by `Store` grammar (16-17);
- privacy gate: imported `logging` functions, class-body loggers, `:=`, aliases, wrappers, `partial` (16-18);
- the writer's two refusal constants and the foreign-session row (16-19).

This report replaces the prior `16-REVIEW.md`. Each prior finding appears once, in the disposition table below.

What I checked:
- **Tests.** The four test files pass: `705 passed`. I ran them under the shared flock with `-p no:randomly`.
- **Commits.** Every GREEN commit that `16-REVIEW-DISPOSITION.md` cites for round 3 is an ancestor of `HEAD` (checked with `git merge-base --is-ancestor`): `333bf8e0`, `5c3ffb94`, `9b074697`, `417229e7`, `282c16d7`, `b7a1e127`, `e3f46b63`, `e53d9320`, `38727536`, `5a7cc660`, `b2758f43`, and the test commit `27cfc105`.
- **Probes.** I called `normalize_manual`, `phone_write_offences` and `python_log_offences` directly from scratch scripts. I confirmed SQLAlchemy 2.0.46 write behaviour on a throwaway in-memory SQLite engine. Every new finding below was reproduced, not inferred.
- **Library path.** I read `phonenumbers` 9.0.41 `_test_number_length`. A type with no metadata description returns `INVALID_LENGTH`; it does not fall back to the general lengths. So `ACCOUNT_NUMBER_TYPES` is not vacuous for the 149 regions without a `VOIP` description.

What the batch got right:
- All five prior findings are closed (table below).
- The 16-19 writer change is minimal and correct.
- The header measurement rule (`test_the_module_header_names_the_auto_path_boundary_with_its_measurement`) recomputes both numbers live. A metadata bump will now turn the suite red instead of leaving the header stale.

New problems:
- **The manual-path boundary is named too narrowly.** Docstring item 5 says only Germany and Israel still accept a non-`+7` number with extra digits. Measured: 36 regions do, including Italy, Netherlands, Finland, Ireland, Austria, Serbia and Indonesia (WR-11).
- **The single-writer gate's mechanism claim is wider than the predicate for a fourth time.** `MessengerAccount.phone.key` and container forms of `from_select` names both write the column and pass. So does a same-module import alias of a writer API (WR-12).
- **The privacy gate misses structlog's async level methods.** `await logger.ainfo(…, phone=…)` passes, and the project's configured wrapper provides that method (WR-13).
- Two small hygiene items (IN-11, IN-12).

## Prior findings — disposition

Titles are copied verbatim from the prior `16-REVIEW.md`. Older ledger rows (WR-01…WR-08, CR-01, IN-01…IN-07) are not repeated: my re-derivation does not contradict their ledger state.

| ID | Prior title | State | Evidence (current tree `4bd0276f`) |
|----|-------------|-------|------------------------------------|
| WR-09 | Manual input of a non-`+7` number plus extra digits is still saved as an invented "manual" number (BY, UA, KG, TR, IL, CN, DE) | closed (GREEN `333bf8e0`, ancestor of HEAD) | `ACCOUNT_NUMBER_TYPES` is at `app/services/phone.py:142-147` and `_is_possible_for_an_account_type` at `:216-229`; the refusal is at `:318-319`. Probe results: every BY, UA, KG, TR and CN input in the prior table is refused, as is IL +1 (`PHONE_ERROR_NOT_A_NUMBER`). IL +2/+3 and DE +1/+2 are still accepted, and item 5 names them. Pinned by the `wr09_*` rows (`tests/test_services/test_phone.py:615-646`), the `FOREIGN_EXTRA_DIGIT_BASES` 5×5 enumeration (`:750-800`) and the 830-example guard (`:805`). The fix the prior review proposed was implemented as written. The boundary text it introduced is too narrow; that is new **WR-11**, a defect in the new item-5 text, not a reopening. |
| WR-10 | The single-writer gate's new "through the mechanism" claim is again wider than the predicate: `Query.update(values=…)`, keyword `set_attribute`, and `run_sync(Session.bulk_*_mappings, …)` pass | closed (GREEN `9b074697`, `417229e7`, `282c16d7`, `b7a1e127`, `e3f46b63`, `e53d9320`, ancestors of HEAD) | Each of the five forms in the prior WR-10 code block now produces exactly one offence (probe): `Query.update(values=…)`, `set_attribute(…, key=…)`, `set_committed_value(…, key=…)`, `run_sync(Session.bulk_update_mappings, …)` and `values(**{"phone": n for …})`. `JUDGED_PARAMETERS` is at `tests/test_application/test_phone_single_writer_gate.py:454-587`; the signature guard at `:1952` and the binding matrix at `:2054` pass. The new mechanism claim is again wider than the predicate in other places; that is new **WR-12**. |
| IN-08 | The auto-path boundary paragraph says "besides real numbers" the only extra acceptance is `TOO_SHORT`; 400 of the 558 `IS_POSSIBLE` values accepted in the same enumeration are not valid numbers | closed (GREEN `5c3ffb94`, ancestor of HEAD) | `app/services/phone.py:37-56` names both classes: possible values including invalid ones ("400 из 558") and `TOO_SHORT` outside code 7 ("583 из 1935"). The rule `test_the_module_header_names_the_auto_path_boundary_with_its_measurement` (`tests/test_services/test_phone.py:334`) recomputes both numbers live and passes. |
| IN-09 | The privacy gate neither catches nor names two logger forms that are identifiable by import or module binding | closed (GREEN `38727536`, `5a7cc660`, ancestors of HEAD) | `module_log_names` (`tests/test_phone_privacy_gate.py:560-638`) handles both forms. A `from logging import <LOG_METHOD>` becomes a `log_functions` entry; a class-body binding also goes into the attributes (`_bind`, `:541-557`). `NamedExpr` is collected. Probe: `from logging import info`, `warning as warn_`, class-body `lg` through `self.`/`cls.`, and `if (lg := logging.getLogger()):` each produce an offence. |
| IN-10 | The other-session case of `record_reported_phone` is left untested on a false premise, and the refusal text gives wrong advice for it | closed (GREEN `b2758f43`, test `27cfc105`, ancestors of HEAD) | `ACCOUNT_NOT_IN_SESSION` is neutral (`app/application/accounts/phone.py:73`). The post-flush line has its own `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` (`:75`, `:189`). The `"foreign"` row adds the object to an unbound `AsyncSession()` and has an anti-vacuum assert (`tests/test_application/test_account_phone_writer.py:371-413`). The false premise is gone from the docstring. `test_each_refusal_of_the_recorder_names_its_own_cause` is at `:444`. |

## Narrative Findings (AI reviewer)

## Warnings

### WR-11: `normalize_manual` item 5 names Germany and Israel as the only non-`+7` extra-digit boundary; 36 regions still save an invented "manual" number

**File:** `app/services/phone.py:266-274` (item 5, "У кодов, отличных от 7, класс … закрывает пункт 7, КРОМЕ названной границы: Германия … и Израиль …") and `:278-282` (item 7); `tests/test_services/test_phone.py:45-53` (module docstring) and the `FOREIGN_EXTRA_DIGIT_BASES` docstring (`:745-749`, `:780-784`)

**Issue:** Item 5 says the "number plus extra digits" class outside code 7 is closed by item 7 *except* for Germany and Israel, "because their `FIXED_LINE` / `FIXED_LINE_OR_MOBILE` length is variable". The test module repeats the claim. I enumerated it: for every region, the metadata `MOBILE` example in E.164 with `1`, `12`, `123` and `1234` appended (976 inputs over 244 regions). **56 inputs in 36 regions are accepted** and stored with `phone_is_manual=true`, so no auto source can correct them (D-07). Examples (`normalize_manual` output):

| Typed | Stored | Type that admits the length |
|---|---|---|
| `+39 312 345 6789 1` (Italy) | `+3931234567891` | FIXED_LINE |
| `+31 6 12345678 12` (Netherlands) | `+3161234567812` | **MOBILE** |
| `+358 41 2345678 1` (Finland) | `+3584123456781` | **MOBILE** |
| `+353 85 012 3456 1` (Ireland) | `+3538501234561` | FIXED_LINE |
| `+381 60 1234567 123` (Serbia) | `+381601234567123` | FIXED_LINE |
| `+62 812 345 678 123` (Indonesia) | `+62812345678123` | **MOBILE** |
| `+886 912 345 678 1` (Taiwan) | `+8869123456781` | **VOIP** |
| `+60 12 345 6789 1` (Malaysia) | `+601234567891` | MOBILE / VOIP |

The other regions: AD, AT (all four counts), AX, BA, BG, BQ, CD, CU, GA, GM, IS, KH, LU, MM, MN, NZ, PM, SM, SO, TK, TV, VA, VN, WS, XK, ZW, plus the named DE and IL.

Two problems:
- **The named boundary is about 1/18 of the real one.** It names 2 of the 36 regions.
- **The stated reason is wrong for part of the set.** For NL, FI, ID and MY the *mobile* length itself is variable, and for TW it is `VOIP`. No length-only rule can close those, so the boundary is permanent there, not an artefact of `FIXED_LINE`.

This is the same "named boundary narrower than the measured one" shape the phase has been closing (IN-08, WR-07). The disposition ledger repeats the narrow wording ("граница названа в пункте 5 … Германия … и Израиль").

**Fix:** Name the class with a live measurement instead of two countries, and pin it the way the auto-path header is pinned:
```python
# tests/test_services/test_phone.py
def _manual_extra_digit_enumeration() -> tuple[int, int, set[str]]:
    total = accepted = 0
    regions: set[str] = set()
    for region in sorted(phonenumbers.SUPPORTED_REGIONS):
        example = phonenumbers.example_number_for_type(region, phonenumbers.PhoneNumberType.MOBILE)
        if example is None:
            continue
        base = phonenumbers.format_number(example, phonenumbers.PhoneNumberFormat.E164)
        for tail in ("1", "12", "123", "1234"):
            total += 1
            try:
                normalize_manual(base + tail)
            except PhoneError:
                continue
            accepted += 1
            regions.add(region)
    return total, accepted, regions
```
Then:
- Assert that item 5 contains `f"{accepted} из {total}"` and the region count.
- Reword item 5: "outside code 7 the class is closed only where no account type's length admits the extra digits; where MOBILE/VOIP length is itself variable (NL, FI, ID, MY, TW, AT, …) no length rule can close it" (D-05 forbids the validity check).
- If the owner wants a tighter rule, that is a new decision (O-x). It is not something to word around.

### WR-12: The single-writer gate's mechanism claim is again wider than the predicate: `MessengerAccount.phone.key`, container forms of `from_select` names, and same-module import aliases of writer APIs pass

**File:** `tests/test_application/test_phone_single_writer_gate.py`:
- `:152-160`: the boundary. "Ловится всякая запись, в которой колонка номера … названа литералом в самом пишущем вызове, в его аргументе-контейнере (грамматика `_literal_mappings` …)".
- `:1312-1348`: `_phone_column` accepts `X.phone` but not `X.phone.key`.
- `:1418-1428`: `from_select` names only as a bare `List`/`Tuple`.
- `:659`, `:675`: aliases are resolved only for the model and `partial`.
- `:173-177`: boundary (4) names only "псевдоним модели, заведённый в чужом файле".

**Issue:** `phone_write_offences` returns `[]` for each form below. I ran the starred ones on SQLAlchemy 2.0.46 against an in-memory SQLite engine; each wrote the column (`+71`, `+72`, `+74` persisted):
```python
stmt = update(MessengerAccount).values({MessengerAccount.phone.key: x})                      # * writes
session.bulk_update_mappings(MessengerAccount, [{"id": 1, MessengerAccount.phone.key: p}])  # * writes
await session.execute(update(MessengerAccount), [{"id": 1, MessengerAccount.phone.key: p}])
setattr(account, MessengerAccount.phone.key, x)
set_committed_value(account, MessengerAccount.phone.key, x)
stmt = insert(MessengerAccount).from_select(["user_id"] + ["phone"], sel)                    # * writes
stmt = insert(MessengerAccount).from_select(["user_id", "phone"] if full else ["user_id"], sel)
stmt = insert(MessengerAccount).from_select(list(("user_id", "phone")), sel)
from sqlalchemy.orm.attributes import set_committed_value as scv; scv(account, "phone", x)
from sqlalchemy.orm.attributes import flag_modified as touch; touch(account, "phone")
```
- **`Model.attr.key`.** It is the standard way to build the *string* keys that `bulk_update_mappings` requires without a bare literal. That is exactly the Phase 20 backfill shape. The column is named literally (`MessengerAccount.phone`) inside the writing call's argument, and `_phone_column` already treats `X.phone` as literal naming. No boundary item covers it: (1) is "name or result of another call" and (2) is "computed at run time", and `.key` is neither in any sense that `X.phone` is not.
- **`from_select` names.** The header promises the `_literal_mappings` container grammar (`+`, conditional, `list(…)`), but this kind is judged only on a bare list or tuple.
- **Import aliases.** The gate already resolves same-module import aliases for the model and for `partial` (`_module_aliases`). Writer APIs get no such resolution, and boundary (4) names only the model alias from another file. If the intent is to file this under (1) ("reference in a variable"), (1) has to say so: today it names only `fn = s.bulk_update_mappings`.

This is the WR-01 → WR-08 → WR-10 pattern a fourth time. The header's own rule (`:185-187`) says such a form is "слепота предиката, а не граница средства" ("a blindness of the predicate, not a boundary of the tool").

**Fix:**
- In `_phone_column`, accept `ast.Attribute(attr in {"key", "name"})` whose `.value` is itself a phone-column node (`MessengerAccount.phone.key`, `table.c.phone.name`). For the `NAMED_ATTRIBUTE_WRITERS` branch (`:850-853`), test `_phone_column(attribute)` instead of `isinstance(attribute, ast.Constant)`.
- In `_positional_phone_columns`, run the bound `names` value through `_pair_candidates` (which already implements the list/tuple/`+`/`IfExp`/`:=`/wrapper grammar) instead of requiring `List`/`Tuple`.
- Build `write_names` / `judged_names` with `_module_aliases(tree, n)` for every name in `_judged_call_names(...)`, the same way it is done for `MessengerAccount` and `partial`.
- Plant each form above as a `LITERAL_FORM_CASES` row, and keep `Group.title.key` in `LEGITIMATE_CASES` as the negative control.

### WR-13: The privacy gate misses structlog's async level methods (`ainfo`, `awarning`, …) that the project's configured logger provides

**File:** `tests/test_phone_privacy_gate.py:218-235` (`LOG_METHODS`), `:12-14` (header: "метод — уровень журнала или `bind`/`new`"), `:177-181` (boundary bullet attributing the method list to D-17); `app/logging_config.py:35` (`wrapper_class=structlog.stdlib.BoundLogger`)

**Issue:** The project configures structlog with `structlog.stdlib.BoundLogger`. In structlog 25.5.0 that class exposes `adebug`, `ainfo`, `awarning`, `aerror`, `aexception`, `acritical`, `afatal` and `alog` (checked with `dir()`). These are the level methods for `async` code, and this is an async FastAPI + Celery codebase. None of them is in `LOG_METHODS`. Probe:
```python
logger = structlog.get_logger()
async def g(account):
    await logger.ainfo("connected", phone=account.phone)      # python_log_offences -> []
class S:
    async def g(self, a):
        await self.logger.awarning("x", phone=a.phone)         # -> []
```
The number goes to stdout, then Loki, exactly like `logger.info`.

The boundary bullet says "методы журнала вне `LOG_METHODS` … D-17 задаёт гейт списком получателей и методов". But D-17 (`16-CONTEXT.md:90-94`) reads "Python — `logger.*`/`log.*`/`logging.*`/`print(`": a wildcard over methods, not a method list. The header also says the gate judges "вызовы уровней" ("level calls"), and `ainfo` is a level call. So this is a blindness of the predicate, not an owner frame. `ainfo` is not mentioned anywhere in `.planning/` or `tests/`.

A smaller sibling: `lg = logging.getLogger(__name__).getChild("x"); lg.info(a.phone)` also passes. `getChild` returns a logger, as `bind` does, but it is neither a factory nor in `LOG_METHODS`.

**Fix:**
```python
ASYNC_LOG_METHODS = frozenset({"adebug", "ainfo", "awarning", "aerror", "aexception",
                               "acritical", "afatal", "alog"})
LOG_METHODS = frozenset({...existing..., *ASYNC_LOG_METHODS})
```
- Add a guard rule that compares `ASYNC_LOG_METHODS` with `{m for m in dir(structlog.stdlib.BoundLogger) if m.startswith("a") and m[1:] in LOG_METHODS}`, so a structlog bump turns the suite red.
- Plant `await logger.ainfo(…, phone=…)` as a positive case.
- Optionally treat `getChild` like `bind` when classifying a binding's value (`module_log_names`).
- If the owner does want a closed method list, fix the boundary bullet's attribution to D-17 instead.

## Info

### IN-11: Missing space after `=` in `normalize_manual`

**File:** `app/services/phone.py:320`
**Issue:** `e164 =phonenumbers.format_number(number, PhoneNumberFormat.E164)` was introduced by `333bf8e0`. The project has no formatter in the toolchain (`uv run ruff` is not installed), so nothing catches it.
**Fix:** `e164 = phonenumbers.format_number(number, PhoneNumberFormat.E164)`.

### IN-12: The writer test reaches the new constant through the module object while its sibling is imported by name

**File:** `tests/test_application/test_account_phone_writer.py:29`, `:31`, `:485`
**Issue:** `ACCOUNT_NOT_IN_SESSION` is imported from `app.application.accounts.phone`. `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` is read as `writer_module.ACCOUNT_WITHOUT_ID_AFTER_FLUSH` through an extra `import … as writer_module`. This is a leftover of the RED commit, where the constant did not yet exist and a by-name import would have broken collection. Now it is only an inconsistent second import path.
**Fix:** Add `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` to the `from app.application.accounts.phone import (...)` list and drop `writer_module`.

---

_Reviewed: 2026-10-12T20:15:50Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `388add71`, head `4bd0276f`)_
