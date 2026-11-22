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
- **Документированное исключение (ревизия 1 планов):** задача 19-07-02 один раз на фазу гонит полный каталог `uv run pytest tests/test_pages -q -p no:randomly` (≈15–27 мин) — фоном (`run_in_background`), после последней правки `app/pages/accounts.py` цепочки 19-01 → 19-05 → 19-06 → 19-07; причина — гейты, читающие исходники ЧУЖИХ модулей (`test_htmx_post_pairs`, `test_htmx_gates` и др.), исполнители иначе пропускают (память `cross-cutting-gates-skipped-by-executors`); это прогон гейта, а не обратная связь задачи — быстрые команды задачи остаются в пределе 150 с. Прецедент — 18-02-03 (`18-VALIDATION.md`: «фоном, ~15–20 мин»; замер исполнения 2255 passed за 27 мин).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 19-01 | 1 | PHONE-12 | T-19-03, T-19-04 | номер из того же `pop`, что строка сессии; пишет только `record_reported_phone` в коммите `status="active"`; второго подключения нет | integration (tracer) | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q -p no:randomly` | ✅ файлы есть, случаи новые | ⬜ pending |
| 19-01-02 | 19-01 | 1 | PHONE-12 | T-19-01, T-19-02, T-19-05 | путь 2FA; мусорный `User.phone` → «неизвестен» без отказа; номер не в журнале и не в `repr` | unit + integration | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ файлы есть, случаи новые | ⬜ pending |
| 19-02-01 | 19-02 | 2 | PHONE-13 | T-19-06 | четыре входа D-03: PN с устройством / без → цифры; LID и пусто → `null`; только `isPnUser` + `jidDecode` | unit (JS через `run_node_script`, tracer) | `uv run pytest tests/test_worker/test_wa_worker_own_phone.py -q -p no:randomly` | ❌ W0 (новый файл) | ⬜ pending |
| 19-02-02 | 19-02 | 2 | PHONE-13, PHONE-15 | T-19-07, T-19-08 | разбор тотален и молчалив; пин Baileys `7.0.0-rc14` сторожится | unit (JS) | `uv run pytest tests/test_worker/test_wa_worker_own_phone.py tests/test_phone_privacy_gate.py -q -p no:randomly` | ❌ W0 (новый файл) | ⬜ pending |
| 19-03-01 | 19-03 | 2 | PHONE-14 | T-19-09 | `client.me.contact.phone` → `/status.phone`; номер формы в `/status` не уходит (OQ1) | unit (tracer) | `uv run pytest tests/test_worker/test_max_worker.py -q -p no:randomly` | ✅ файл есть, случаи новые | ⬜ pending |
| 19-03-02 | 19-03 | 2 | PHONE-14, PHONE-15 | T-19-10, T-19-11 | границы и точность `own_phone_of`; сбой захвата не срывает `on_start`; номер не в журнале | unit | `uv run pytest tests/test_worker/test_max_worker.py tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ файл есть, случаи новые | ⬜ pending |
| 19-04-01 | 19-04 | 2 | PHONE-16 | T-19-12 | `prod-deploy` собирает образ WA до остановки WA-воркеров; тег = `WA_WORKER_IMAGE` | unit (`just --dry-run`, tracer) | `uv run pytest tests/test_wa_worker_deployment.py tests/test_max_worker_deployment.py -q -p no:randomly` | ❌ W0 (новый файл) | ⬜ pending |
| 19-04-02 | 19-04 | 2 | PHONE-16 | T-19-12, T-19-13 | `prod-hard-deploy` — `--no-cache` до остановки; `prod-build` собирает WA (OQ2) | unit (`just --dry-run`) | `uv run pytest tests/test_wa_worker_deployment.py tests/test_max_worker_deployment.py -q -p no:randomly` | ❌ W0 (новый файл) | ⬜ pending |
| 19-05-01 | 19-05 | 2 | PHONE-13 | T-19-15, T-19-17 | номер из `/status` WA в коммите `syncing` через `capture_connect_phone` (сейвпоинт); виден в списке | integration (tracer, настоящий адаптер) | `uv run pytest tests/test_pages/test_connect_phone_capture.py -q -p no:randomly` | ❌ W0 (новый файл) | ⬜ pending |
| 19-05-02 | 19-05 | 2 | PHONE-13, PHONE-15 | T-19-14, T-19-16, T-19-18 | старая форма `/status` и LID → подключён, «неизвестен»; сбой захвата → `syncing`; известное не затирается; порядок «сообщённый, затем запасной» | integration + unit | `uv run pytest tests/test_pages/test_connect_phone_capture.py tests/test_application/test_connect_phone.py tests/test_messengers/test_whatsapp.py -q -p no:randomly` | ❌ W0 (новые файлы) | ⬜ pending |
| 19-06-01 | 19-06 | 3 | PHONE-14 | T-19-22 | свободный ввод (`8 999 123 45 67`, плейсхолдер) → `credentials` и `start_session(phone=…)` в E.164; колонку `phone` старт не пишет (D-10) | integration (tracer) | `uv run pytest tests/test_pages/test_max_connect_transport.py -q -p no:randomly` | ✅ файл есть, случаи новые | ⬜ pending |
| 19-06-02 | 19-06 | 3 | PHONE-14 | T-19-19, T-19-22, T-19-23 | 422 через `PhoneError` с экранированным эхом до QR; подсказка без номера | integration | `uv run pytest tests/test_pages/test_max_connect_transport.py tests/test_templates -q -p no:randomly` | ✅ файл есть, правки | ⬜ pending |
| 19-07-01 | 19-07 | 4 | PHONE-14 | T-19-20, T-19-27 | «ввёл A, отсканировал B → показан B»; номер пишет `capture_connect_phone` в коммите `syncing`; номер формы читается из `credentials` до перезаписи | integration (tracer) | `uv run pytest tests/test_pages/test_connect_phone_capture.py tests/test_pages/test_max_connect_transport.py -q -p no:randomly` | ✅ после 19-05 | ⬜ pending |
| 19-07-02 | 19-07 | 4 | PHONE-14, PHONE-15 | T-19-21, T-19-27 | MAX не отдал / старый образ → номер формы без «указан вручную» (OQ1); сбой захвата → `syncing`; известное не затирается | integration | `uv run pytest tests/test_pages/test_connect_phone_capture.py tests/test_messengers/test_max.py tests/test_application/test_connect_phone.py -q -p no:randomly` · полный `uv run pytest tests/test_pages -q -p no:randomly` — фоном, документированное исключение §Sampling Rate | ✅ после 19-05 | ⬜ pending |
| 19-08-01 | 19-08 | 5 | PHONE-16 | T-19-25 | выкат — действие владельца (деплой-гейт D-26) | manual (`checkpoint:human-action`) | — (ответ владельца в сводке) | n/a | ⬜ pending |
| 19-08-02 | 19-08 | 5 | PHONE-16 | T-19-24, T-19-25 | код ветки в web-контейнере и оба образа подтверждены до обхода; `19-UAT.md` в размеченной форме | records + machine evidence | `uv run pytest tests/test_planning -q -p no:randomly` · гейты номера D-07: `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ❌ (`19-UAT.md` заводит задача) | ⬜ pending |
| 19-08-03 | 19-08 | 5 | PHONE-13, PHONE-14 | T-19-24, T-19-26 | W-1…W-4 на живых WA и MAX; отметки словами владельца, `status: testing` | manual (`checkpoint:human-verify`) + records | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ после 19-08-02 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_worker/test_wa_worker_own_phone.py` — новый: разбор `creds.me.id` на четырёх входах (PN с устройством, PN без устройства, LID, пусто) и `me` не объект, через `run_node_script` (PHONE-13)
- [ ] `tests/test_pages/test_connect_phone_capture.py` — новый: опросчики WA/MAX, «ввёл A, отсканировал B → показан B», «MAX не отдал → показан A, без пометки», `/status` старой формы, сбой захвата не ломает подключение (PHONE-13, PHONE-14, PHONE-15)
- [ ] кейсы фазы в `tests/test_routes/test_tg_user_auth.py` — QR и 2FA до `phone` строки, второго подключения нет (PHONE-12)
- [ ] кейсы `own_phone` / поле `phone` в `/status` в `tests/test_worker/test_max_worker.py` (PHONE-14)
- [ ] `tests/test_wa_worker_deployment.py` — новый: тесты рецептов WA (и `prod-build` — решение владельца 2026-11-22) рядом с `tests/test_max_worker_deployment.py`, который не меняется (PHONE-16; план 19-04)
- [ ] `tests/test_application/test_connect_phone.py` — новый: помощник `capture_connect_phone` — порядок «сообщённый, затем запасной», `KEPT`/`MISSING` без запасного, сбой → `None` при живой внешней транзакции (PHONE-14, PHONE-15; план 19-05)

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
