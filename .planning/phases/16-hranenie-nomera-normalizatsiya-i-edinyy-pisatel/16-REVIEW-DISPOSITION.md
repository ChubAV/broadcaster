---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Manual input with the `00` prefix or a leading-0 local number is saved as a made-up `+7 0…` number"
  - id: WR-01
    severity: warning
    disposition: open
    title: "The single-writer gate misses five write forms that are visible in the source"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The privacy gate misses `structlog.contextvars.bind_contextvars(phone=…)`, a pattern the project uses"
  - id: WR-03
    severity: warning
    disposition: open
    title: "`mask_phone` shows the whole number when the national part has 2 digits or fewer"
  - id: WR-04
    severity: warning
    disposition: open
    title: "The auto-path lower bound of 5 digits saves source junk as a \"number\"; a test pins this"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Auto writers return `KEPT` when no row was updated at all"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer"
  - id: IN-02
    severity: info
    disposition: open
    title: "The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on"
  - id: IN-03
    severity: info
    disposition: open
    title: "The race test cannot detect dropping the `phone_is_manual` predicate"
  - id: IN-04
    severity: info
    disposition: open
    title: "`reconcile_lines` now crashes on decimal phase directories (copied from Phase 15)"
  - id: IN-05
    severity: info
    disposition: open
    title: "The migration test's claim that \"children survive the recreate\" is only proven with SQLite foreign keys off"
open: 10
total: 11
recorded: 2026-10-08T20:49:45.192Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-01 | info | deferred | отложено на Фазу 18 (решение владельца О-4, 2026-10-09): её форма выбирает между явным действием «очистить» и показом `PHONE_ERROR_BLANK`; поведение сегодня предписано D-07 / PHONE-10; записано в `.planning/STATE.md` §Deferred Items |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
