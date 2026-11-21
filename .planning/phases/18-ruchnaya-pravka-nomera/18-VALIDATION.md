---
phase: "18"
slug: "ruchnaya-pravka-nomera"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-21"
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `18-RESEARCH.md` §Validation Architecture (замеры 2026-11-21). Карту задач ниже
> заполняет планировщик по своим планам (строка на задачу).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0, httpx `AsyncClient`, SQLite in-memory |
| **Config file** | отдельного нет; фикстуры `tests/conftest.py` (`client`, `db_session`, `authed_client`, `admin_client`) |
| **Quick run command** | `uv run pytest tests/test_pages/test_account_phone_form.py tests/test_services/test_account_label.py -q -p no:randomly` (файл формы создаётся планом; до него — модули задачи) |
| **Full suite command** | `uv run pytest tests/ -q -p no:randomly` (≈46 мин; только гейт фазы, таймаут 5400 с) |
| **Estimated runtime** | быстрый прогон задачи — секунды…~150 с; прогон гейтов волны — ~8–10 мин |

---

## Sampling Rate

- **After every task commit:** `uv run pytest <файл(ы) задачи> -q -p no:randomly`
- **After every plan wave (гейты поимённо):** `uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_account_groups.py tests/test_pages/test_notices_registry.py tests/test_pages/test_write_path_invariants.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_hx_location_destinations.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_phone_writer_runtime_guard.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_shell.py -q -p no:randomly`
- **Records:** `uv run pytest tests/test_planning -q -p no:randomly` (≈22 с) после засева реестра запретов и правки `progress.total_plans`
- **Before `/gsd-verify-work`:** полная суита зелёная (`just test`, таймаут 5400 с)
- **Max feedback latency:** 150 секунд на задачу

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-NN-NN | — | — | — | — | заполняет планировщик | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_pages/test_account_phone_form.py` — новый: маршрут, оба транспорта, 422, владение, граница, приватность, критерий 3 (PHONE-09, PHONE-10)
- [ ] `tests/account_label_support.py::seed_account` — параметр посева ручного номера через `set_manual_phone` (PHONE-08)
- [ ] тест разрешения под имперсонацией в `tests/test_pages/test_impersonation.py` рядом с `:1254` (PHONE-11)
- [ ] расширение цикла частей и селекторов CSS в `tests/test_pages/test_responsive_markup.py:5182` (PHONE-08)

*Новых зависимостей и каркаса нет — `pytest`, `httpx`, фикстуры существуют.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| htmx-обмен: подмена формы, внеполосные `<h2>`/`<h1>`, смена `<title>`, уведомление «Номер сохранён» без перезагрузки | PHONE-09 | суита не исполняет JS | `/gsd-verify-work 18`: сохранить номер с JS, убедиться, что шапка и заголовок сменились без перезагрузки |
| якорь `#phone` с карточки прокручивает к полю | PHONE-09 | прокрутка — поведение браузера | перейти по «Указать номер» / «Изменить» с `/accounts` |
| `autocomplete` не подставляет номер пользователя | PHONE-09 | поведение браузеров неоднородно | открыть экран групп в браузере с сохранённым автозаполнением |
| раскладка шапки с формой и пометкой «указан вручную» на 320 и 375 px; `#id` двойника виден рядом с пометкой | PHONE-08 | рендер в суите не проверяется | обход на 320 и 375 px |
| 422 без плашки аварии | PHONE-09 | консоль/плашка — поведение клиента | ввести неверный номер с JS |

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
