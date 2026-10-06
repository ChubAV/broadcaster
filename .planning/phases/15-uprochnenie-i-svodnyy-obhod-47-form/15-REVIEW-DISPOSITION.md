---
phase: 15
review: 15-REVIEW.md
titles: json
findings:
  - id: WR-05
    severity: warning
    disposition: open
    title: "The new create/update refusal reuses the toggle's notice, whose text tells an editor user to repeat the action that was just refused — open, owner-accepted 2026-10-06"
  - id: WR-06
    severity: warning
    disposition: open
    title: "The census gate raises `CensusError` on any decimal-numbered phase, and this project has used one — open"
  - id: WR-07
    severity: warning
    disposition: open
    title: "A product-suite test reads a Phase 10 planning artifact through a `test_planning` import, and will fail on milestone archive — open"
  - id: WR-09
    severity: warning
    disposition: open
    title: "A keyboard upload that reaches the ceiling hides the field that has focus, and the visible focus point disappears (new, `d0a31bd9`)"
  - id: WR-10
    severity: warning
    disposition: open
    title: "`test_the_file_field_is_reachable_from_the_keyboard` checks text, not reachability, and stays green when the field becomes unreachable again (new, `d0a31bd9`)"
  - id: WR-11
    severity: warning
    disposition: open
    title: "`560ce871` tells the fixer to rewrite the digest in the same commit, while the module header still forbids exactly that; two unmarked controls pin the same digest (new)"
  - id: IN-07
    severity: info
    disposition: open
    title: "Five sentinels still carry `limit={{ page_size }}`, and two renderers echo the request's `limit` into markup (pre-existing, confirmed) — open"
  - id: IN-08
    severity: info
    disposition: open
    title: "`app/dependencies.py:323` still hand-spells the notice URL (pre-existing, not a phase regression) — open"
  - id: IN-09
    severity: info
    disposition: open
    title: "The shell layer-literal rule reddens on any `60` or `70` anywhere in an 8,946-line module — open"
  - id: IN-10
    severity: info
    disposition: open
    title: "The same seven-line history comment is pasted into six handlers — open"
  - id: IN-11
    severity: info
    disposition: open
    title: "A new rule asserts two accepted accessibility defects as the required state — open, owner-accepted"
  - id: IN-12
    severity: info
    disposition: open
    title: "`.media-tile--add:focus-visible` is dead, and sharing a selector list with `:has()` makes the whole ring rule all-or-nothing (new, `d0a31bd9`)"
  - id: IN-13
    severity: info
    disposition: open
    title: "The visually-hidden declaration block is now duplicated (new, `d0a31bd9`)"
open: 13
total: 13
recorded: 2026-10-06T09:52:38.503Z
---

# Phase 15: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| WR-09 | warning | open | - |
| WR-10 | warning | open | - |
| WR-11 | warning | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |
| IN-10 | info | open | - |
| IN-11 | info | open | - |
| IN-12 | info | open | - |
| IN-13 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
