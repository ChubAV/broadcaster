---
phase: "18"
slug: "ruchnaya-pravka-nomera"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| 18-01-01 | 01 | 1 | PHONE-08 | T-18-01, T-18-02, T-18-03 | Пометка только при известном номере; флаг вне ключа двойника; плоские формы без пометки; номер — только автоэкранированием; загрузчик читает строки своего пользователя | unit (таблица) + integration по адресу `data-account-label` (tracer) | `uv run pytest tests/test_services/test_account_label.py tests/test_application/test_account_label_rows.py tests/test_pages/test_account_label_groups.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_services tests/test_application tests/test_models tests/test_repositories tests/test_scripts -q -p no:randomly` | ✅ (параметр `manual_phone` в `tests/account_label_support.py` заведён планом 18-01) | ✅ green |
| 18-01-02 | 01 | 1 | PHONE-08 | T-18-02 | `SyncStatusView.phone_is_manual` во всех четырёх конструкторах; пометка у каждого адреса подписи на всех экранах прохода; `<title>`, `<option>`, модалка, CSV — без пометки; номер не в журнал; сквозные гейты D-08 поимённо на прежних числах (`MUTATING_ROUTE_COUNT` 49, `MUTATING_MODULE_COUNT` 14, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 25, `PUSH_URL_DECISIONS_DECLARED` 37, `PAIRED_302_ASSERTIONS_DECLARED` 191, `POST_PAIR_CASES_DECLARED` 77, реестр уведомлений 19) | integration (проход по экранам) + гейты номера + сквозные гейты D-08 | `uv run pytest tests/test_pages/test_account_label_accounts.py tests/test_pages/test_account_label_sweep.py -q -p no:randomly` · `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_notices_registry.py -q -p no:randomly` | ✅ дополнить | ✅ green |
| 18-01-03 | 01 | 1 | PHONE-08 | — | Пометка приглушена и усекается раньше номера; `#id` двойника `flex: none` | unit (текст CSS) | `uv run pytest tests/test_pages/test_responsive_markup.py -q -p no:randomly -k "account_label or manual_mark"` | ✅ расширить цикл частей `:5182` | ✅ green |
| 18-02-01 | 02 | 2 | PHONE-09, PHONE-10, PHONE-11 | T-18-04, T-18-05, T-18-06, T-18-07, T-18-08, T-18-09, T-18-11, T-18-12, T-18-14 | Владение до писателя, чужой = несуществующий = вне колонки = `LookupError`; чужой источник — 403 до выборки; эхо экранировано; 422 без уведомления и кода исхода на обоих транспортах (критерий 2, машинная половина); номер не в адрес, уведомление, журнал; POST без поля не стирает; под имперсонацией правка пишет; запись только через `set_manual_phone`; `PAIRED_302_ASSERTIONS_DECLARED` 191 → 193 (два литеральных `== 302`: тесты 1 и 5) | integration (оба транспорта, tracer) + 11 модулей гейтов одним коммитом | `uv run pytest tests/test_pages/test_account_phone_form.py tests/test_pages/test_impersonation.py tests/test_pages/test_notices_registry.py -q -p no:randomly` · гейты: `uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_pages/test_write_path_invariants.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_identifier_bounds.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_account_groups.py tests/test_pages/test_account_label_groups.py tests/test_pages/test_shell.py -q -p no:randomly` · `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_phone_writer_runtime_guard.py -q -p no:randomly` | ✅ (`tests/test_pages/test_account_phone_form.py` создан планом 18-02; числа и реестры гейтов сдвинуты по ведомости) | ✅ green |
| 18-02-02 | 02 | 2 | PHONE-09, PHONE-10 | T-18-04 | Свежая подпись после записи (D-14); дубликат принимается (D-15); «Сохранить» без правки — ручной; критерий 3 `KEPT` → очистка → `WRITTEN`; у каждого закрепляющего теста — отрицательный контроль мутацией; форма — собственная строка шапки | integration (закрепляющие) + unit (текст CSS) | `uv run pytest tests/test_pages/test_account_phone_form.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_account_groups.py tests/test_templates -q -p no:randomly` · `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly` | ✅ (создан задачей 18-02-01) | ✅ green |
| 18-02-03 | 02 | 2 | PHONE-09 | T-18-11 | Диспозиция IN-01 (D-09) в `STATE.md`; проза слоя ответа правдива; полный каталог страничных тестов и гейты номера зелены | gate (полный `tests/test_pages`) + records | `uv run pytest tests/test_pages -q -p no:randomly` (фоном, ~15–20 мин) · `uv run pytest tests/test_templates tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_phone_writer_runtime_guard.py tests/test_services/test_phone.py -q -p no:randomly` · `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 18-03-01 | 03 | 3 | PHONE-09 | T-18-15 | Ссылка к полю номера на карточке страницы во всех ветках статуса; номера в `href` нет; переход ведёт к полю `id="phone"` своего аккаунта | integration по `href` (tracer) | `uv run pytest tests/test_pages/test_account_phone_links.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_pages/test_responsive_markup.py tests/test_pages/test_account_label_accounts.py -q -p no:randomly` | ✅ (`tests/test_pages/test_account_phone_links.py` создан планом 18-03) | ✅ green |
| 18-03-02 | 03 | 3 | PHONE-09 | T-18-15, T-18-16 | Та же ссылка в порции и во фрагменте опроса; чужой аккаунт во фрагменте ссылки не получает; три исходника по три ссылки; числа гейтов не сдвинуты (значения после 18-02: `WRITE_FORM_PLACES` 50, `MUTATING_ROUTE_COUNT` 50, `MUTATING_MODULE_COUNT` 14, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 26, `PUSH_URL_DECISIONS_DECLARED` 38, `PAIRED_302_ASSERTIONS_DECLARED` 193, `POST_PAIR_CASES_DECLARED` 79, реестр уведомлений 21) | integration + счёт по исходникам + гейты | `uv run pytest tests/test_pages/test_account_phone_links.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_pages/test_responsive_markup.py tests/test_pages/test_account_label_accounts.py tests/test_pages/test_account_label_sweep.py tests/test_routes/test_wa_sync_status.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_notices_registry.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ (создан задачей 18-03-01) | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_pages/test_account_phone_form.py` — новый: маршрут, оба транспорта, 422, владение, граница, приватность, критерий 3 (PHONE-09, PHONE-10)
- [x] `tests/account_label_support.py::seed_account` — параметр посева ручного номера через `set_manual_phone` (PHONE-08)
- [x] тест разрешения под имперсонацией в `tests/test_pages/test_impersonation.py` рядом с `:1254` (PHONE-11)
- [x] расширение цикла частей и селекторов CSS в `tests/test_pages/test_responsive_markup.py:5182` (PHONE-08)

*Новых зависимостей и каркаса нет — `pytest`, `httpx`, фикстуры существуют.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| htmx-обмен: подмена формы, внеполосные `<h2>`/`<h1>`, смена `<title>`, уведомление «Номер сохранён» без перезагрузки | PHONE-09 | суита не исполняет JS | `/gsd-verify-work 18`: сохранить номер с JS, убедиться, что шапка и заголовок сменились без перезагрузки |
| якорь `#phone` с карточки прокручивает к полю | PHONE-09 | прокрутка — поведение браузера | перейти по «Указать номер» / «Изменить» с `/accounts` |
| `autocomplete` не подставляет номер пользователя | PHONE-09 | поведение браузеров неоднородно | открыть экран групп в браузере с сохранённым автозаполнением |
| раскладка шапки с формой и пометкой «указан вручную» на 320 и 375 px; `#id` двойника виден рядом с пометкой | PHONE-08 | рендер в суите не проверяется | обход на 320 и 375 px |
| 422 без плашки аварии | PHONE-09 | консоль/плашка — поведение клиента; машинная половина автоматизирована: тест 4 задачи 18-02-01 (код ровно 422, ни `hx-swap-oob`, ни заголовков `HX-*`, пустые `#notice` / `#notice-alert`, нет кодов и текстов исхода) + `tests/test_pages/test_shell.py::test_the_failure_banner_tells_a_validation_answer_from_a_crash` (ранний выход сценария плашки по коду 422) | ввести неверный номер с JS и убедиться, что плашки аварии на экране нет |

*Записи обхода — по правилам самозаверения: машинную улику писать разделом улики, отметки и `result` оставлять человеку.*

---

## Validation Sign-Off

Счёт планирования (2026-11-21, прогон `/gsd-plan-phase 18`): 3 плана, 8 задач, 3 волны (18-01 →
18-02 → 18-03); строк карты — 8; задач с `<automated>` — 8 из 8; маркеров `MISSING — Wave 0` — 0;
новых файлов тестов — 2 (`tests/test_pages/test_account_phone_form.py`,
`tests/test_pages/test_account_phone_links.py`); правимых существующих тестовых модулей — 19 (из них
11 модулей гейтов, ведомость scope_note 18-02).

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — 8/8 (планирование)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify — у каждой задачи свой `<automated>`
- [x] Wave 0 covers all MISSING references — маркеров `MISSING` нет; новые модули создаются задачами-трассерами 18-02-01 и 18-03-01, посев ручного номера — задачей 18-01-01
- [x] No watch-mode flags
- [x] Feedback latency < 150s (быстрые команды задач) — быстрые команды задач укладываются (секунды…~60 с); гейтовые команды идут ОДИН раз на план там, где сдвигаются или проверяются числа: задача 18-01-02 — команда сквозных гейтов D-08 без сдвига чисел (ревизия 1; длительность проверить на исполнении), задача 18-02-01 — пять команд по ≈30–160 с (суммарно ≈6–8 мин), команда волны ≈8–10 мин, полный `tests/test_pages` в задаче 18-02-03 ≈15–20 мин фоном — проверить на исполнении. Замер исполнения (2026-11-21): быстрые команды задач — в пределах порога; гейтовые команды шли по одному разу на план — команда волны плана 18-03 2472 passed за 10 мин 45 с, полный `tests/test_pages` плана 18-02 2255 passed за 27 мин (фоном); это прогоны гейтов, не обратная связь задачи
- [x] `nyquist_compliant: true` set in frontmatter — `/gsd-validate-phase 18` (2026-11-21, из `/gsd-execute-phase 18`, шаг verify:post)

**Approval:** validated 2026-11-21 — пробелов 0 из 8 строк карты; все строки зелены в полной суите на `d197f956` (6035 passed, 2 skipped, 44:13), после неё менялись только `.planning/`; ручные половины остаются в «Manual-Only Verifications» для `/gsd-verify-work 18`

## Validation Audit 2026-11-21

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
