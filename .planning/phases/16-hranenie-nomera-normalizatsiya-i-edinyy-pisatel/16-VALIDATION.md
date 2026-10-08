---
phase: "16"
slug: "hranenie-nomera-normalizatsiya-i-edinyy-pisatel"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-08"
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `16-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.0.2 + pytest-asyncio ≥1.3.0 |
| **Config file** | none — маркеры объявляются хуком в `tests/conftest.py` |
| **Quick run command** | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_migrations -q` |
| **Records command** | `uv run pytest tests/test_planning -q` |
| **Full suite command** | `just test` |
| **Estimated runtime** | quick ~10–20 s; records ~16 s; full ~40 min |

---

## Sampling Rate

- **After every task commit:** целевой модуль задачи и `tests/test_migrations`; у плана записей — `uv run pytest tests/test_planning -q`
- **After every plan wave:** quick run command + `tests/test_planning` + широкие гейты из RESEARCH §Sampling Rate
- **Before `/gsd-verify-work`:** `just test` must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| (заполняет планировщик — одна строка на задачу) | | | | | | | | | |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_services/test_phone.py` — SC3 (таблица нормализации, показ, маска)
- [ ] `tests/test_migrations/test_0023_messenger_account_phone.py` — SC1, SC2
- [ ] `tests/test_migrations/test_model_matches_head.py` — расширение снимка `messenger_accounts` (SC1, D-04)
- [ ] `tests/test_application/test_account_phone_writer.py` — SC2, SC4 (последовательно)
- [ ] `tests/test_application/test_account_phone_race.py` — SC4 (гонка, контроль-отрицание)
- [ ] `tests/test_application/test_phone_single_writer_gate.py` — D-13
- [ ] `tests/test_phone_privacy_gate.py` — SC5 (PHONE-21)
- [ ] `phonenumberslite==9.0.41` — `just add` за `checkpoint:human-verify` (пакет помечен SUS: версия от 2026-10-08)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Легитимность пакета `phonenumberslite==9.0.41` | PHONE-01 | Сторож пакетов дал SUS (too-new) | Владелец сверяет страницу PyPI / автора перед `just add` |
| Ветвь PostgreSQL ревизии `0023` | PHONE-01 | Тестовой PostgreSQL в окружении нет | Покрывается деплой-гейтом владельца (D-26, R-08-06) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
