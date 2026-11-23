---
phase: "20"
slug: "dozapolnenie-nomerov-suschestvuyuschih-akkauntov"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-23"
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `20-RESEARCH.md` §Validation Architecture (замеры 2026-11-23). Карту задач ниже
> заполняет планировщик по своим планам (строка на задачу).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio ≥ 1.3.0; `db_session` из `tests/conftest.py` (SQLite in-memory); для гонки критерия 2 — файловая база с двумя независимыми сессиями (образец `tests/test_application/test_account_phone_race.py:97-100`); Docker, HTTP воркеров и Telethon — только двойники внедряемых источников ядра `run(...)`: тесты не касаются ни Docker, ни Telegram, ни сети |
| **Config file** | отдельного нет (pytest в dev-зависимостях `pyproject.toml`); фикстуры `tests/conftest.py`; образец теста скрипта — `tests/test_scripts/test_recompress_attachments.py` (`tests/test_scripts/__init__.py` уже есть) |
| **Quick run command** | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` |
| **Full suite command** | `just test` (≈46 мин, 6143 passed на закрытии Фазы 19; только гейт фазы, таймаут 5400 с, исполнители её не гоняют) |
| **Estimated runtime** | быстрый прогон задачи — секунды; гейты номера — ≈65 с (1161 passed, замер 2026-11-23); записи — ≈22 с (218 passed, 2 skipped) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` + гейты номера (ниже) для любой задачи, трогающей файл скрипта
- **After every plan wave (гейты поимённо, в `<automated>` каждого плана — D-07):**
  - гейты номера: `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`
  - писатель и маска: `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_services/test_log_masking.py -k "phone or without_setup_logging" -q -p no:randomly`
  - скрипты: `uv run pytest tests/test_scripts/ -q -p no:randomly`
  - сквозной гейт 302-пар (фаза число не двигает, но исполнители его пропускают): `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly`
- **Records:** `uv run pytest tests/test_planning -q -p no:randomly` (≈22 с) — явно, после каждой правки ROADMAP/STATE (исполнители записи отключают)
- **Before `/gsd-verify-work`:** полная суита зелёная (`just test`, таймаут 5400 с); `grep -rn "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with" app/ scripts/ --include=*.py` без шапок гейтов — пусто (долг (i) части C RESEARCH: границы О-26 скрипт не задевает)
- **Max feedback latency:** 120 секунд на задачу

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-NN-NN | — | — | — | — | заполняет планировщик | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scripts/test_backfill_account_phones.py` — новый: все строки карты «Phase Requirements → Test Map» из `20-RESEARCH.md` (PHONE-17 выборка / идемпотентность / ручной номер во время прогона / итог; PHONE-18 `--dry-run` и отказ `--wake` под ним; PHONE-19 только работающие, подъём по флагу, классификация `/status`, адаптеры не будят; PHONE-20 последовательность TG, «занят», карта ошибок, рецепты; PHONE-21 маска вывода с антивакуумом)
- [ ] фикстура файловой базы с двумя независимыми сессиями (образец `tests/test_application/test_account_phone_race.py:97-100`) — для теста критерия 2
- [ ] двойник Telethon-клиента со счётчиком одновременных подключений, `start` с `assert_not_called()`, `disconnect` с проверкой ожидания в `finally`
- [ ] двойники источников WA/MAX: список работающих контейнеров, ответ `/status`, подъём / ожидание / остановка со счётчиком вызовов `start_container`

*Новых зависимостей и каркаса нет — `pytest`, `pytest-asyncio`, `httpx`, `just` существуют.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

Вне критериев фазы и не ручная проверка фазы (CONTEXT §Phase Boundary; ответ владельца O-4 (а), 2026-11-23): боевой прогон — шаг владельца после выката (деплой-гейт). Порядок: образ приложения → образы воркеров → перезапуск работающих воркеров → `just prod-backfill-phones --dry-run --account-id <один>` по одному аккаунту каждого типа → прогон с записью. Там же видны допущения RESEARCH, которые тестами не измерить: A4 (отдаёт ли MAX `contact.phone` при восстановлении сессии), A3 (код 405 у Baileys при `--wake`), A1 (короткое подключение TG без `AuthKeyDuplicated`).

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
