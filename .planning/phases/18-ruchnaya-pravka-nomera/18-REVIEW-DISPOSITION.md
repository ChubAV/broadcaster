---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "кнопка «Сохранить» выровнена по низу подсказки, а не по полю"
  - id: WR-02
    severity: warning
    disposition: open
    title: "якорь `#phone` не учитывает липкую шапку шелла"
  - id: WR-03
    severity: warning
    disposition: open
    title: "умолчание `phone_is_manual = False` в `SyncStatusView` обходит собственную защиту фазы от тихой потери пометки"
  - id: IN-01
    severity: info
    disposition: open
    title: "фокус теряется только при нажатии на кнопку, а не при отправке Enter (уточнение к `18-UI-REVIEW.md`)"
  - id: IN-02
    severity: info
    disposition: open
    title: "`_screen_context` — семь позиционных параметров и словарь, достраиваемый после литерала"
  - id: IN-03
    severity: info
    disposition: open
    title: "тест закрепляет литерал `maxlength == \"64\"` вместо выведения из константы"
open: 6
total: 6
recorded: 2026-11-21T14:34:25.174Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
