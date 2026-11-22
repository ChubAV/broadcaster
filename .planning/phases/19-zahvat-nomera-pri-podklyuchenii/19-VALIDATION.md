---
phase: "19"
slug: "zahvat-nomera-pri-podklyuchenii"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-22"
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `19-RESEARCH.md` §Validation Architecture (замеры 2026-11-22). Карту задач ниже
> заполняет планировщик по своим планам (строка на задачу).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 (auto-mode), httpx `AsyncClient`, SQLite in-memory; JS-юниты воркера WA — через `run_node_script` из `tests/conftest.py` (Node v22 локально, образ `node:20-slim`; пропуск при отсутствии Node запрещён) |
| **Config file** | отдельного нет (нет `pytest.ini` / `[tool.pytest.ini_options]`); фикстуры `tests/conftest.py` (`client`, `db_session`, `authed_client`), посев номера — `tests/account_label_support.py::seed_account` |
| **Quick run command** | `uv run pytest <файлы плана> -q -p no:randomly` |
| **Full suite command** | `just test` (≈5700+ тестов, ≈46 мин; только гейт фазы, таймаут 5400 с, исполнители её не гоняют) |
| **Estimated runtime** | быстрый прогон задачи — секунды…~140 с; гейты волны поимённо — ~4–5 мин (гейты номера 63 с, связка модулей 137 с, записи 20 с) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest <файл(ы) задачи> -q -p no:randomly`
- **After every plan wave (гейты поимённо, в `<automated>` каждого плана):**
  - гейты номера: `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`
  - сквозные: `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_money_perimeter_gate.py tests/test_templates/test_form_inventory.py tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly`
  - шаблоны (если тронут `app/templates/accounts/includes/max_connect_step.html`): `uv run pytest tests/test_templates -q -p no:randomly`
- **Records:** `uv run pytest tests/test_planning -q -p no:randomly` (≈20 с) после засева реестра запретов и правки `progress.total_plans`
- **Before `/gsd-verify-work`:** полная суита зелёная (`just test`, таймаут 5400 с)
- **Max feedback latency:** 150 секунд на задачу

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-NN-NN | — | — | — | — | заполняет планировщик | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_worker/test_wa_worker_own_phone.py` — новый: разбор `creds.me.id` на четырёх входах (PN с устройством, PN без устройства, LID, пусто) и `me` не объект, через `run_node_script` (PHONE-13)
- [ ] `tests/test_pages/test_connect_phone_capture.py` — новый: опросчики WA/MAX, «ввёл A, отсканировал B → показан B», «MAX не отдал → показан A, без пометки», `/status` старой формы, сбой захвата не ломает подключение (PHONE-13, PHONE-14, PHONE-15)
- [ ] кейсы фазы в `tests/test_routes/test_tg_user_auth.py` — QR и 2FA до `phone` строки, второго подключения нет (PHONE-12)
- [ ] кейсы `own_phone` / поле `phone` в `/status` в `tests/test_worker/test_max_worker.py` (PHONE-14)
- [ ] тесты рецептов WA (и `prod-build` — решение владельца 2026-11-22) рядом с `tests/test_max_worker_deployment.py` (PHONE-16)

*Новых зависимостей и каркаса нет — `pytest`, `httpx`, `run_node_script`, `just` существуют.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MAX отдаёт ли `client.me.contact.phone` при QR-входе (W-1: «ввёл A, отсканировал B» на живом аккаунте) | PHONE-14 | исходник pymax 2.3.1 ответа не даёт; нужен живой сервер MAX | ручной обход на бою после деплоя (D-11): подключить MAX с номером A в форме, сканировать аккаунтом B |
| MAX: форма с A и скан тем же аккаунтом (W-2) | PHONE-14 | живой MAX | тот же обход |
| WA: новый аккаунт показывает номер; при LID-only — «Номер неизвестен», не цифры LID (W-3) | PHONE-13 | форма `creds.me.id` у реального сервера WA | подключить живой WA на бою |
| ни один шаг подключения не показывает «указан вручную» (W-4) | PHONE-14 | сквозной итог на живых аккаунтах | тот же обход |
| `just prod-deploy` пересобирает оба образа, новые контейнеры воркеров стартуют на них | PHONE-16 | боевой стенд | обход проверяет заодно (D-11); код ветки в web-контейнере — до обхода |

*Записи обхода — по правилам самозаверения: машинную улику писать разделом улики, отметки и `result` оставлять человеку.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 150s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
