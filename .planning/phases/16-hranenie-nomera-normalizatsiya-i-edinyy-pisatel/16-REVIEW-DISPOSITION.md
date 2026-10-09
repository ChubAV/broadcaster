---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: WR-06
    severity: warning
    disposition: open
    title: "Manual input of a valid `+7` number plus four extra digits is saved as an invented 15-digit \"manual\" number"
  - id: WR-07
    severity: warning
    disposition: open
    title: "The P-1 boundary in the module header understates the auto path; `TOO_LONG`, `INVALID_LENGTH`, longer `TOO_SHORT` and `+7 0…` are all stored"
  - id: WR-08
    severity: warning
    disposition: open
    title: "The single-writer gate's header claims \"Всё, что видно литералом в исходнике, ловится\" (\"everything visible as a literal in the source is caught\"), but literal write forms still pass"
  - id: IN-06
    severity: info
    disposition: open
    title: "The privacy gate's binder match misses an aliased import and the threadlocal binders"
  - id: IN-07
    severity: info
    disposition: open
    title: "`record_reported_phone` still answers a forgotten `session.add` silently whenever the source sends no number"
  - id: IN-01
    severity: info
    disposition: open
    title: "Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-02
    severity: info
    disposition: open
    title: "The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-03
    severity: info
    disposition: open
    title: "The race test cannot detect dropping the `phone_is_manual` predicate — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-04
    severity: info
    disposition: open
    title: "`reconcile_lines` crashes on decimal phase directories (copied from Phase 15) — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-05
    severity: info
    disposition: open
    title: "The migration test's claim that \"children survive the recreate\" is only proven with SQLite foreign keys off — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Manual input with the `00` prefix or a leading-0 local number is saved as a made-up `+7 0…` number"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "The single-writer gate misses five write forms that are visible in the source"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The privacy gate misses `structlog.contextvars.bind_contextvars(phone=…)`, a pattern the project uses"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`mask_phone` shows the whole number when the national part has 2 digits or fewer"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "The auto-path lower bound of 5 digits saves source junk as a \"number\"; a test pins this"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Auto writers return `KEPT` when no row was updated at all"
open: 10
total: 16
recorded: 2026-10-09T16:55:55.664Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| WR-08 | warning | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| CR-01 | critical | fixed | `16-07` задача 1, GREEN `97e62918` — отказ `PHONE_ERROR_NOT_A_NUMBER` при коде 7 и ведущем нуле национальной части (О-3 (а)): `00 …`, украинский местный и белорусский `8 0…` больше не сохраняются как `+7 0…` (not in the current review) |
| WR-01 | warning | fixed | `16-09` задачи 1–2, GREEN `a97179ab`, `78495634` — пять литеральных форм записи: `execute` и `bulk_*_mappings` с ключом `phone*` в строках, `set_` у `on_conflict_do_update`, литеральный `**{…}` и `dict(...)` (not in the current review) |
| WR-02 | warning | fixed | `16-09` задача 3, GREEN `6ed63a95` — `bind_contextvars` / `bound_contextvars` судятся гейтом приватности как вызовы журнала при любом приёмнике (not in the current review) |
| WR-03 | warning | fixed | `16-07` задача 3, GREEN `fdb12dd5` — порог маски короткой национальной части: при двух цифрах и меньше маскируется вся она (`+88812` → `+888 ***`) (not in the current review) |
| WR-04 | warning | fixed | `16-07` задача 2, GREEN `ae44c1d0` — граница 7, отказ `IS_POSSIBLE_LOCAL_ONLY`, строка `five_digits_lower_bound` переписана с летописью; остаётся названная граница П-1 (шапка модуля): 7-значный обрывок `TOO_SHORT` вроде «1234567» автопуть принимает, особого случая для кода 888 владелец не принял (О-1) (not in the current review) |
| WR-05 | warning | fixed | `16-08` задачи 1–2, GREEN `67a25113`, `bee23ee2` — `PhoneWrite.MISSING` для отсутствующей строки; `ValueError` на объекте вне сессии (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
