---
phase: "16"
slug: "hranenie-nomera-normalizatsiya-i-edinyy-pisatel"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| **Quick run command** | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q` |
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
| 16-01-01 | 01 | 1 | записи-старт-вехи (решение владельца 2026-10-08) | T-16-01 | правила отложенного пропускаются только при отсутствии живых кандидатов и с причиной; кандидат без раздела плана краснит; архивные файлы проверяются всегда | tracer (records) | `uv run pytest tests/test_planning/test_deferred_items_are_idempotent.py -q -p no:randomly -rs` | ✅ | ✅ green |
| 16-01-02 | 01 | 1 | записи-старт-вехи | T-16-01, T-16-02 | счёт строк — картой по вехе с летописью 44; вывод вехи пропускается только без отчётов и без `Complete`; субъекты контролей выведены из записи; проза — антивакуум по отметкам; мета-гейт вердиктов зелен | records | `uv run pytest tests/test_planning/test_requirement_completion_follows_verification.py tests/test_planning/test_state_progress_matches_roadmap.py tests/test_planning/test_planning_gates_are_independent_of_the_live_verdict.py -q -p no:randomly -rs` | ✅ | ✅ green |
| 16-01-03 | 01 | 1 | записи-старт-вехи | T-16-02, T-16-03 | отбор «до Фазы 15» по номеру фазы (планы v2.2 не сдвигают чисел 142/650/745, контроль с планом фазы 17); реестр засеян штатным `--seed-registry`, решения владельца v2.1 перенесены как есть, шапка несёт летопись О-2 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-02-01 | 02 | 1 | PHONE-01 | T-16-SC | пакет со статусом SUS ставится только после ответа владельца своими словами | checkpoint:human-verify (`blocking-human`) | — (чекпойнт владельца; ответ — в `16-02-SUMMARY.md`) | N/A | ✅ green (ответ владельца «пакет проверен, ставить 9.0.41», 2026-10-08) |
| 16-02-02 | 02 | 1 | PHONE-01 | T-16-06 | автопуть: только цифры 5…15 и успешный разбор, мусор → `None`; показ неразбираемого — как есть | tracer (unit, табличный) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-02-03 | 02 | 1 | PHONE-01, PHONE-21 | T-16-04, T-16-05, T-16-06 | ручной ввод: предел 32 символа / 15 цифр, `IS_POSSIBLE`, отказ по добавочному; тексты отказа — закрытый набор без ввода; маска `+7 *** ***-**-67` | unit (табличный + `ast`) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-03-01 | 03 | 1 | PHONE-01 | T-16-09, T-16-10, T-16-11 | колонка модели без ревизии краснит суиту (D-04); `upgrade head` доходит до `0023`; тест ставит `DATABASE_URL` на `tmp_path` | tracer (migration) | `uv run pytest tests/test_migrations/test_model_matches_head.py -q -p no:randomly` | ✅ | ✅ green |
| 16-03-02 | 03 | 1 | PHONE-01 | T-16-07, T-16-08, T-16-10 | CHECK «ручной без номера» с обеих сторон; три законные пары; нет индекса по номеру; `ON DELETE` целы; downgrade возвращает прежнюю таблицу | migration + unit (модель на `db_session`) | `uv run pytest tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q -p no:randomly` | ✅ | ✅ green |
| 16-04-01 | 04 | 1 | PHONE-21 | T-16-12, T-16-14 | номер по имени, литералом, ключом или маской в журнале Python краснит; `phone_set` булевой формы и маска в выводе `scripts/` — нет; подложенная строка находится обходом | tracer (gate, AST) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-04-02 | 04 | 1 | PHONE-21 | T-16-13, T-16-14, T-16-15 | JS: `${…}` шаблонов, носители `sock.user` / `creds.me`, литералы краснят; комментарии и `node_modules` — нет; реестр исключений под потолком 0 | gate (JS-токенизатор) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-05-01 | 05 | 2 | PHONE-02, PHONE-01 | T-16-16, T-16-17, T-16-18, T-16-19 | автоисточник — только условный `UPDATE`; ручной цел; очистка одним оператором; мусор и неверный ввод — до базы; писатель не коммитит и не ставит признак ручного | tracer (unit, `db_session`) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ✅ green |
| 16-05-02 | 05 | 2 | PHONE-02 | T-16-16 | гонка: ручной номер цел во всех измеренных позициях, флаг «ручная запись состоялась» в каждой; отрицание чтение-проверка-запись краснит позицию 2 | integration (файловая SQLite, две сессии) | `uv run pytest tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-06-01 | 06 | 3 | PHONE-02 | T-16-20, T-16-21 | присваивание и `values(phone=…)` вне модуля-писателя краснят; подложенная запись находится; модуль-писатель виден обходом | tracer (gate, AST) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-06-02 | 06 | 3 | PHONE-02 | T-16-20, T-16-21 | словарь, `setattr` / `set_committed_value`, сырой SQL краснят; законные `phone=` — нет; исключение ровно одного модуля, присваивание запрещено и в нём | gate (AST) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |

**Сквозные гейты (в `<verification>` каждого плана):** `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates tests/test_application/test_declared_invariants.py -q -p no:randomly` (≈2,5 мин; замер планирования 2026-10-08 — 576 passed) — на волну, а не на задачу: дольше 60 с.

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_services/test_phone.py` — SC3 (таблица нормализации, показ, маска)
- [x] `tests/test_migrations/test_0023_messenger_account_phone.py` — SC1, SC2
- [x] `tests/test_models/test_messenger_account_phone_check.py` — SC2 (модельная половина CHECK, форма колонок; план 16-03)
- [x] `tests/test_migrations/test_model_matches_head.py` — расширение снимка `messenger_accounts` (SC1, D-04)
- [x] `tests/test_application/test_account_phone_writer.py` — SC2, SC4 (последовательно)
- [x] `tests/test_application/test_account_phone_race.py` — SC4 (гонка, контроль-отрицание)
- [x] `tests/test_application/test_phone_single_writer_gate.py` — D-13
- [x] `tests/test_phone_privacy_gate.py` — SC5 (PHONE-21)
- [x] `phonenumberslite==9.0.41` — `just add` за `checkpoint:human-verify` (пакет помечен SUS: версия от 2026-10-08)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Легитимность пакета `phonenumberslite==9.0.41` | PHONE-01 | Сторож пакетов дал SUS (too-new) | Владелец сверяет страницу PyPI / автора перед `just add` |
| Ветвь PostgreSQL ревизии `0023` | PHONE-01 | Тестовой PostgreSQL в окружении нет | Покрывается деплой-гейтом владельца (D-26, R-08-06) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-08 (`/gsd-validate-phase 16` из `/gsd-execute-phase 16`): все 14 строк карты зелёные на дереве `85d65afd` — команды карты `582 passed, 3 skipped`, `prohibitions_census.py --check` rc 0, полная суита `4349 passed, 3 skipped, 0 failed`. Пробелов 0; ручными остаются две строки таблицы Manual-Only.

## Validation Audit 2026-10-08

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
