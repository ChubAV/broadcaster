---
phase: 17
review: 17-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: open
    title: "`_ChipTitles` в `test_editor_schedules.py` не знает пустых элементов и приписывает всем чипам `title=` первого"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Недостижимая ветка `group.account_id is None` в `history_account_label`, а докстринг называет её случаем D-15"
  - id: IN-01
    severity: info
    disposition: open
    title: "`export_row(..., phone=None)` молча отдаёт пустую «Номер» при забытом аргументе"
  - id: IN-02
    severity: info
    disposition: open
    title: "Шесть локальных словарей «тип → имя канала» остались рядом с единым `MESSENGER_LABELS`"
  - id: IN-03
    severity: info
    disposition: open
    title: "Тест прохода импортирует приватные помощники из чужих тестовых модулей"
open: 5
total: 5
recorded: 2026-11-20T21:40:17.563Z
---

# Phase 17: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
