---
phase: 20
review: 20-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "A failed container stop is silent. The script ignores `stop_container`'s return value."
  - id: WR-02
    severity: warning
    disposition: open
    title: "\"Queue is empty\" is used as proof of \"worker is idle\". A task already popped by the worker is killed mid-send."
  - id: WR-03
    severity: warning
    disposition: open
    title: "The script can stop a container it did not start (D-16 violated in a small window)."
  - id: WR-04
    severity: warning
    disposition: open
    title: "The staged-rollout instruction (`--limit`) cannot make progress past unfillable accounts."
  - id: IN-01
    severity: info
    disposition: open
    title: "The FloodWait wait time is not honoured; the next account is polled after a fixed 1 s."
  - id: IN-02
    severity: info
    disposition: open
    title: "`--wake` has no guard against being run outside the production container."
  - id: IN-03
    severity: info
    disposition: open
    title: "The Telegram busy probe covers Celery sends only. There is also a probe-to-connect gap."
  - id: IN-04
    severity: info
    disposition: open
    title: "Minor hygiene in selection and source construction."
open: 8
total: 8
recorded: 2026-11-23T20:47:53.838Z
---

# Phase 20: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
