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
| 17-01-01 | 01 | 1 | PHONE-03, PHONE-04, PHONE-05 | T-17-01 | Подпись чипа — данные из глобала, разметка из макроса; без `Markup`/`|safe` | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_editor_schedules.py -q -p no:randomly` | ✅ переписать `:1336`; ❌ W0 `tests/account_label_support.py` | ⬜ pending |
| 17-01-02 | 01 | 1 | PHONE-04, PHONE-05 | T-17-01 | Неразбираемое значение — как есть, текстом; модуль чистый (без `markupsafe`/`jinja2`/`sqlalchemy`); знак при id в Python — только `id_mark` (одна константа, разбор `ast`) | unit, таблица | `uv run pytest tests/test_services/test_account_label.py -q -p no:randomly` | ❌ W0 | ⬜ pending |
| 17-01-03 | 01 | 1 | PHONE-05 | T-17-02, T-17-03, T-17-04 | Карта только своего пользователя, три колонки, один запрос; номер не в журнал | integration (БД) + гейты номера и шаблонов | `uv run pytest tests/test_application/test_account_label_rows.py tests/test_services/test_account_label.py -q -p no:randomly` · `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly` | ❌ W0 / ✅ | ⬜ pending |
| 17-02-01 | 02 | 2 | PHONE-03, PHONE-05 | T-17-06, T-17-07 | В `x-on`/`$dispatch` только числовой id; модалка двойника несёт `#id` | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_account_label_accounts.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_responsive_markup.py -q -p no:randomly -k "accounts"` | ❌ W0; ✅ переписать `:1100` | ⬜ pending |
| 17-02-02 | 02 | 2 | PHONE-03, PHONE-04, PHONE-05 | T-17-07 | Признак двойника по всем аккаунтам пользователя, не по порции | integration, по адресу | `uv run pytest tests/test_pages/test_account_label_accounts.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_responsive_markup.py -q -p no:randomly -k "three_files or partial"` | ❌ W0 / ✅ | ⬜ pending |
| 17-02-03 | 02 | 2 | PHONE-03, PHONE-04 | T-17-05, T-17-08 | Подпись опроса только после проверки владения | integration, по адресу + гейты | `uv run pytest tests/test_pages/test_account_label_accounts.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_routes/test_wa_sync_status.py -q -p no:randomly` · гейты номера · гейты шаблонов | ❌ W0 / ✅ | ⬜ pending |
| 17-03-01 | 03 | 2 | PHONE-03, PHONE-04 | T-17-10, T-17-11 | Номер из колонки `phone`, не из `credentials` | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_account_label_groups.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_account_groups.py tests/test_pages/test_shell.py -q -p no:randomly` | ❌ W0 / ✅ | ⬜ pending |
| 17-03-02 | 03 | 2 | PHONE-05 | T-17-09 | Враждебное значение экранировано в `<title>`, `<h1>`, `<h2>` | integration + гейты | `uv run pytest tests/test_pages/test_account_label_groups.py -q -p no:randomly` · гейты номера · гейты шаблонов | ❌ W0 / ✅ | ⬜ pending |
| 17-04-01 | 04 | 2 | PHONE-03, PHONE-04, PHONE-05 | T-17-12 | Подпись записи — только из карты пользователя | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_account_label_history.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_history.py -q -p no:randomly` | ❌ W0 / ✅ | ⬜ pending |
| 17-04-02 | 04 | 2 | PHONE-04, PHONE-05 | T-17-12, T-17-14 | Одна карта на порцию; запись без аккаунта — без подписи (D-15) | integration, по адресу + счёт запросов | `uv run pytest tests/test_pages/test_account_label_history.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_history_retry.py -q -p no:randomly -k "bounded_number_of_queries"` | ❌ W0 / ✅ | ⬜ pending |
| 17-04-03 | 04 | 2 | PHONE-03, PHONE-05 | T-17-13 | `<option>` экранирован | integration + гейты | `uv run pytest tests/test_pages/test_account_label_history.py tests/test_pages/test_history.py -q -p no:randomly` · гейты номера · гейты шаблонов | ❌ W0 / ✅ | ⬜ pending |
| 17-05-01 | 05 | 2 | PHONE-06 | T-17-15, T-17-17 | Строка воркера — только `<span>`/`<a>`; `#id` — ссылка на логи | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_account_label_admin.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_admin_panel.py -q -p no:randomly` | ❌ W0; ✅ переписать `:102,287,387,554,588` | ⬜ pending |
| 17-05-02 | 05 | 2 | PHONE-06 | T-17-16 | Ключ панели очереди без подписи | integration + гейты | `uv run pytest tests/test_pages/test_account_label_admin.py tests/test_pages/test_admin_panel.py tests/test_pages/test_admin_users.py -q -p no:randomly` · гейты номера · гейты шаблонов | ❌ W0 / ✅ | ⬜ pending |
| 17-06-01 | 06 | 3 | PHONE-07 | T-17-19, T-17-20 | Карта номеров своего пользователя, до потока | integration (tracer) | `uv run pytest tests/test_pages/test_history_export.py -q -p no:randomly` · `… -k "number or nine or cap_is_checked or as_a_stream"` | ✅ расширить | ⬜ pending |
| 17-06-02 | 06 | 3 | PHONE-07 | T-17-18 | Ячейка «Номер» всегда через `export_cell` | unit, таблица + гейты | `uv run pytest tests/test_pages/test_history_export.py -q -p no:randomly` · гейты номера · `uv run pytest tests/test_pages/test_history.py tests/test_pages/test_history_retry.py tests/test_pages/test_account_label_history.py -q -p no:randomly` | ✅ расширить | ⬜ pending |
| 17-07-01 | 07 | 3 | PHONE-06 | T-17-22, T-17-23 | Маршруты за `require_admin`; `<option>` экранирован | integration, по адресу (tracer) | `uv run pytest tests/test_pages/test_account_label_admin_history.py -q -p no:randomly` · `uv run pytest tests/test_pages/test_admin_panel.py tests/test_pages/test_admin_users.py -q -p no:randomly` | ❌ W0 / ✅ | ⬜ pending |
| 17-07-02 | 07 | 3 | PHONE-06 | T-17-21 | Карта порции — по просматриваемому пользователю | integration + гейты | `uv run pytest tests/test_pages/test_account_label_admin_history.py -q -p no:randomly` · гейты номера · гейты шаблонов и `tests/test_pages/test_impersonation_gate.py` | ❌ W0 / ✅ | ⬜ pending |
| 17-08-01 | 08 | 4 | PHONE-03 | T-17-24 | Подложенная склейка названа; вне реестра — ноль | gate (tracer) | `uv run pytest tests/test_templates/test_account_label_gate.py -q -p no:randomly` | ❌ W0 | ⬜ pending |
| 17-08-02 | 08 | 4 | PHONE-03, PHONE-06 | T-17-24, T-17-25 | Исключения по вхождению с предметом; числа объявлены (шаблоны 3, Python 2 — `partition` и `id_mark`); вторая сборка знака в помощнике краснит | gate + сквозные | `uv run pytest tests/test_templates/test_account_label_gate.py -q -p no:randomly` · `uv run pytest tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_phone_privacy_gate.py -q -p no:randomly` | ❌ W0 | ⬜ pending |
| 17-09-01 | 09 | 4 | PHONE-03 | T-17-26 | Контроль синтетической разметкой доказывает непустоту прохода | integration, проход (tracer) | `uv run pytest tests/test_pages/test_account_label_sweep.py -q -p no:randomly` | ❌ W0 | ⬜ pending |
| 17-09-02 | 09 | 4 | PHONE-03, PHONE-04, PHONE-05, PHONE-06 | T-17-26 | Идентификатор в тексте только по объявленным адресам | integration, проход | `uv run pytest tests/test_pages/test_account_label_sweep.py -q -p no:randomly` · `… -k "every_user_screen or every_admin_screen or twins or worst_case"` | ❌ W0 | ⬜ pending |
| 17-09-03 | 09 | 4 | PHONE-03 | T-17-27, T-17-28 | Скрипта посева и `17-UAT.md` нет; бриф обхода в сводке | unit по тексту CSS + гейты — ТОЛЬКО машинная половина критерия 5 (контракт CSS); ширина 320–375 px — manual-only (backstop-истина 17-09, раздел Manual-Only ниже) | `uv run pytest tests/test_pages/test_responsive_markup.py -q -p no:randomly -k "account_label"` · гейты номера · гейты шаблонов с `test_responsive_markup.py` | ✅ дополнить | ⬜ pending |

*«Гейты номера» = `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`; «гейты шаблонов» = `uv run pytest tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py -q -p no:randomly`. Дословные команды — в `<verify>` задач планов.*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Каждый файл создаётся RED-шагом своей задачи (TDD: тест до правки продукта), а не отдельной волной;
маркеров `MISSING — Wave 0` в планах нет.

- [ ] `tests/account_label_support.py` — общий модуль: `seed_account` (номер только писателем Фазы 16: создать без номера → `fill_reported_phone` → `commit`; «как есть» — внутри `writer_scope()`), разбор адресов `label_texts`, `id_mark_texts`, `muted_label_ids`, `element_text`, `option_texts`, `title_text` — план 17-01, задача 1
- [ ] `tests/test_services/test_account_label.py` — правило подписи и двойника (PHONE-04, PHONE-05) — 17-01, задача 2
- [ ] `tests/test_application/test_account_label_rows.py` — загрузчик строк: граница пользователя, три колонки, один запрос (PHONE-05, D-14) — 17-01, задача 3
- [ ] `tests/test_pages/test_account_label_accounts.py` — страница, порция, опрос, модалка удаления (PHONE-03…05) — 17-02
- [ ] `tests/test_pages/test_account_label_groups.py` — `<h1>`, `<h2>`, `<title>` экрана групп (PHONE-03…05) — 17-03
- [ ] `tests/test_pages/test_account_label_history.py` — карточка, порция, фильтр, D-15 (PHONE-03…05) — 17-04
- [ ] `tests/test_pages/test_account_label_admin.py` — воркеры, паршал, очередь, карточка пользователя (PHONE-06) — 17-05
- [ ] `tests/test_pages/test_account_label_admin_history.py` — история пользователя в админке (PHONE-06) — 17-07
- [ ] расширение `tests/test_pages/test_history_export.py` — позиции колонок, ячейка «Номер», обезвреживание формул (PHONE-07) — 17-06
- [ ] `tests/test_templates/test_account_label_gate.py` — греп-гейт с реестром исключений по вхождению и подложенными строками (D-06, D-19) — 17-08
- [ ] `tests/test_pages/test_account_label_sweep.py` — проход «идентификатор в тексте только по объявленным адресам» по экранам и фрагментам (PHONE-03…06, критерий 5) — 17-09
- [ ] правила чтения CSS подписи в `tests/test_pages/test_responsive_markup.py` (`-k account_label`) — 17-09

*Предложенный разведкой единый `test_account_label_screens.py` разнесён по планам второй–четвёртой волн: один файл на четыре параллельных плана дал бы пересечение `files_modified` внутри волны.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Раскладка с длинной подписью не ломается на 320–375px (ширинная половина критерия 5; в 17-09 — истина с `verification: backstop`) | PHONE-03 (критерий 5) | Браузера в репозитории нет; машинно проверяется только текст CSS-контракта (задача 17-09-03) — он НЕ доказывает ширину | Обход человеком на 320 и 375px: список аккаунтов, экран групп (`<h1>`, `<h2>`), чипы и сводка расписаний, карточка и фильтр истории, модалка удаления; виден ли `#id` двойника на чипе и в `<h2>` |
| Вид пяти образцов D-21 на живых экранах | PHONE-03…PHONE-06 | Засев идёт на стенде владельца (решение О-1, О-2 в `17-RESEARCH.md`) | Обход `/gsd-verify-work 17`; чистка засеянного после обхода обязательна |

---

## Validation Sign-Off

Счёт планирования (2026-11-20, прогон `/gsd-plan-phase 17`): 9 планов, 22 задачи, 4 волны; строк
карты — 22; задач с `<automated>` — 22 из 22; маркеров `MISSING — Wave 0` — 0; новых файлов тестов —
10 (из них 1 модуль поддержки `tests/account_label_support.py`); правимых существующих — 4
(`test_editor_schedules.py`, `test_responsive_markup.py`, `test_admin_panel.py`,
`test_history_export.py`).

- [x] All tasks have `<automated>` verify or Wave 0 dependencies — 22/22 (планирование)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify — у каждой задачи свой `<automated>`
- [x] Wave 0 covers all MISSING references — маркеров `MISSING` нет
- [x] No watch-mode flags
- [ ] Feedback latency < 120s — быстрый прогон задачи укладывается; задачи-замыкатели планов гонят гейты шаблонов (`tests/test_templates` + два гейта htmx, ≈100–150 с) — проверить на исполнении
- [ ] `nyquist_compliant: true` set in frontmatter — ставит `/gsd-validate-phase` после исполнения

**Approval:** pending
