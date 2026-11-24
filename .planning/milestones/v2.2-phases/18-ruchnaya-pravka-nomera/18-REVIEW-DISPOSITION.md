---
phase: 18
review: 18-REVIEW.md
titles: json
findings:
  - id: WR-04
    severity: warning
    disposition: open
    title: "переворот утверждений в гейте предков плашки привязывает охранное правило к стилевому решению и не получил контроля"
  - id: WR-05
    severity: warning
    disposition: open
    title: "литералы отступа прокрутки (170 / 236 px) не привязаны к высоте шапки, а границы теста живут в самом тесте"
  - id: IN-04
    severity: info
    disposition: open
    title: "устаревшие имена и перечни ключей после рефакторинга"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "кнопка «Сохранить» выровнена по низу подсказки, а не по полю"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "якорь `#phone` не учитывает липкую шапку шелла"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "умолчание `phone_is_manual = False` в `SyncStatusView` обходит собственную защиту фазы от тихой потери пометки"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "фокус теряется только при нажатии на кнопку, а не при отправке Enter (уточнение к `18-UI-REVIEW.md`)"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "`_screen_context` — семь позиционных параметров и словарь, достраиваемый после литерала"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "тест закрепляет литерал `maxlength == \"64\"` вместо выведения из константы"
open: 3
total: 9
recorded: 2026-11-22T11:23:35.784Z
---

# Phase 18: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-04 | info | open | - |
| WR-01 | warning | fixed | закрыто планом 18-07 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |
| WR-02 | warning | fixed | закрыто планом 18-04 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |
| WR-03 | warning | fixed | закрыто планом 18-06 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |
| IN-01 | info | fixed | закрыто планом 18-05 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |
| IN-02 | info | fixed | закрыто планом 18-07 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |
| IN-03 | info | fixed | закрыто планом 18-07 — `18-REVIEW.md` «Prior findings — disposition» (повторное ревью 2026-11-22, `4b10454f`) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
