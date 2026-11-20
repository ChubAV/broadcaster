---
phase: "17"
slug: "pokaz-nomera-na-vseh-ekranah"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-20"
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `17-RESEARCH.md` §Validation Architecture (замеры 2026-11-20).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio, SQLite in-memory |
| **Config file** | отдельного нет; маркеры `planning`, `characterisation` объявляет хук `tests/conftest.py` |
| **Quick run command** | `uv run pytest <файл(ы) задачи> -q -p no:randomly` |
| **Full suite command** | `uv run pytest tests/ -q -p no:randomly` (≈46 мин; только гейт фазы, таймаут 5400 с) |
| **Estimated runtime** | быстрый прогон задачи — до ~120 с; прогон волны — ~12–14 мин |

---

## Sampling Rate

- **After every task commit:** `uv run pytest <файл(ы) задачи> -q -p no:randomly`
- **After every plan wave:** `uv run pytest tests/test_templates tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_planning -q -p no:randomly` (≈2 мин) плюс модули экранов волны: `tests/test_pages/test_responsive_markup.py tests/test_pages/test_editor_schedules.py tests/test_pages/test_history.py tests/test_pages/test_history_export.py tests/test_pages/test_account_groups.py tests/test_pages/test_admin_panel.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py` (≈10–12 мин)
- **Before `/gsd-verify-work`:** полная суита зелёная (`just test`, таймаут 5400 с)
- **Max feedback latency:** 120 секунд на задачу

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|

*Строки заполняет планировщик — по одной на каждую задачу каждого плана 17-NN.*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_services/test_account_label.py` — правило подписи и двойника (PHONE-04, PHONE-05)
- [ ] `tests/test_pages/test_account_label_screens.py` — адресные тесты (`data-account-label`) и проход «нет `#<id>` вне объявленных адресов» по экранам и фрагментам (PHONE-03…PHONE-06)
- [ ] `tests/test_templates/test_account_label_gate.py` — греп-гейт с реестром исключений и подложенными строками (D-06, D-19)
- [ ] общий хелпер посева аккаунта с номером через писателя Фазы 16 (создать без номера → `fill_reported_phone` → `commit`)
- [ ] расширение `tests/test_pages/test_history_export.py` — позиции колонок, ячейка «Номер», обезвреживание формул (PHONE-07)

*Имена файлов — предложение разведки; окончательные называет план.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Раскладка с длинной подписью не ломается на 320–375px | PHONE-03 (критерий 5) | Браузера в репозитории нет; машинно проверяется только текст CSS-контракта | Обход человеком на 320 и 375px: список аккаунтов, чипы расписаний, карточка истории, модалка удаления |
| Вид пяти образцов D-21 на живых экранах | PHONE-03…PHONE-06 | Засев идёт на стенде владельца (решение О-1, О-2 в `17-RESEARCH.md`) | Обход `/gsd-verify-work 17`; чистка засеянного после обхода обязательна |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
