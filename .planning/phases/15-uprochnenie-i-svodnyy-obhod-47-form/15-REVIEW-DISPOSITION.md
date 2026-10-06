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
    title: "A keyboard upload that reaches the ceiling hides the field that holds focus, and focus falls to `<body>` — open, owner-accepted 2026-10-06"
  - id: WR-12
    severity: warning
    disposition: open
    title: "The replacement rule never proves that its second upload reached the ceiling, so it can go green without exercising the case it exists for (new, `9afcd205`)"
  - id: IN-07
    severity: info
    disposition: open
    title: "Five sentinels still carry `limit={{ page_size }}`, and two renderers echo the request's `limit` into markup (pre-existing, confirmed) — open"
  - id: IN-08
    severity: info
    disposition: open
    title: "`app/dependencies.py:323` still hand-spells the notice URL (pre-existing) — open"
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
    title: "`.media-tile--add:focus-visible` is dead, and sharing a selector list with `:has()` makes the whole ring rule all-or-nothing — open"
  - id: IN-13
    severity: info
    disposition: open
    title: "The visually-hidden declaration block is duplicated — open"
  - id: IN-17
    severity: info
    disposition: open
    title: "The page half of the new rule renders an empty `/ads/new` with no status check, so it cannot see the strip's per-tile markup and would pass on a redirect (new, `9afcd205`)"
  - id: CR-01
    severity: critical
    disposition: open
    title: "The ceiling autofocus takes focus from wherever the person is when the upload response arrives, and the next Space or Enter removes an attachment (new, `568b8f75`)"
  - id: IN-14
    severity: info
    disposition: open
    title: "Nothing pins the claim that the page render never prints `autofocus`, and the template header does not list the new variable (new, `568b8f75`)"
  - id: IN-15
    severity: info
    disposition: open
    title: "The ceiling predicate is now spelled twice in one render, and the two copies must agree for the focus landing to be correct (new, `568b8f75`)"
  - id: IN-16
    severity: info
    disposition: open
    title: "The two synthetic controls are marked `characterisation`, which the marker's own definition says they are not (new, `568b8f75`)"
  - id: WR-10
    severity: warning
    disposition: open
    title: "`test_the_file_field_is_reachable_from_the_keyboard` checks text, not reachability, and stays green when the field becomes unreachable again (new, `d0a31bd9`)"
  - id: WR-11
    severity: warning
    disposition: open
    title: "`560ce871` tells the fixer to rewrite the digest in the same commit, while the module header still forbids exactly that; two unmarked controls pin the same digest (new)"
open: 19
total: 19
recorded: 2026-10-06T12:08:54.453Z
---

# Phase 15: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-05 | warning | open | - |
| WR-06 | warning | open | - |
| WR-07 | warning | open | - |
| WR-09 | warning | open | - |
| WR-12 | warning | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |
| IN-10 | info | open | - |
| IN-11 | info | open | - |
| IN-12 | info | open | - |
| IN-13 | info | open | - |
| IN-17 | info | open | - |
| CR-01 | critical | open | - (not in the current review) |
| IN-14 | info | open | - (not in the current review) |
| IN-15 | info | open | - (not in the current review) |
| IN-16 | info | open | - (not in the current review) |
| WR-10 | warning | open | - (not in the current review) |
| WR-11 | warning | open | - (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
