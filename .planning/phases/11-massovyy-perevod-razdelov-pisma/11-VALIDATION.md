---
phase: "11"
slug: "massovyy-perevod-razdelov-pisma"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-14"
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `11-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0; httpx `AsyncClient`; in-memory SQLite (`sqlite+aiosqlite:///:memory:`) |
| **Config file** | `[tool.pytest]` в `pyproject.toml` отсутствует; фикстуры — `tests/conftest.py` (`client`, `authed_client`, `admin_client`, `htmx_client` `:70`) |
| **Quick run command** | `uv run pytest tests/test_pages/test_htmx_gates.py -q` (сегодня `43 passed`, ~19 с) |
| **Разметочные гейты** | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q` (сегодня `77 passed`, ~4 с) |
| **Компоненты** | `uv run pytest tests/test_templates/test_components.py -q` (сегодня `90 passed`, ~14 с) |
| **Full suite command** | `uv run pytest tests/ -q` — без исключения `tests/test_planning/` (Фаза 10: `3182 passed`, ~38 мин) |
| **Estimated runtime** | ~20 с быстрый круг + модуль раздела задачи |

⚠️ `pytest-randomly` в окружении не установлен — флаг `-p no:randomly` безвреден, но и ничего не значит.

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_pages/test_htmx_gates.py -q` + модуль раздела задачи (таблица ниже).
- **After every plan wave:** три команды гейтов выше + модуль пар GATE-02 + `uv run pytest tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_shell.py -q`.
- **Before `/gsd-verify-work`:** `uv run pytest tests/ -q` целиком, зелёная.
- **Max feedback latency:** ~20 секунд на задачу.

⚠️ В полном прогоне известен красный `full-suite-ads-editor-order-pollution` (`.planning/todos/pending/`) — предмет порядка исполнения суиты, не htmx; фаза его не втягивает (`11-CONTEXT.md` §Reviewed Todos), но обязана отличать его от собственной регрессии.

---

## Per-Task Verification Map

> Заполняется планировщиком при нарезке фазы на планы: `Task ID` появляется только вместе с PLAN.md.
> Строки ниже — требование → поведение → команда, снятые с §Phase Requirements → Test Map разведки;
> планировщик обязан привязать каждую к задаче, а не переписывать заново.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-T1, 11-03-T1/T2, 11-04-T1/T2, 11-05-T2, 11-06-T1/T2, 11-10-T1 | 01, 03, 04, 05, 06, 10 | 1, 3, 4, 5, 6, 10 | FORM-03 | T-11-01, T-11-07 | 9 фрагментных обработчиков: htmx → 200 фрагмент по `id`, без `<!DOCTYPE`, OOB-счётчик/notice; без htmx → 302 | integration | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_schedules_list.py tests/test_pages/test_admin_panel.py tests/test_pages/test_ads_editor.py tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py -q` | ✅ файлы, пары — 11-01-T1 | ⬜ pending |
| 11-01-T1 … 11-10-T1 (каждый перевод) | 01–10 | 1–10 | FORM-03 | — | `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 3 → 12, `NOT_YET_CONVERTED_COUNT` 26 → 14 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q` | ✅ (числа двигаются) | ⬜ pending |
| 11-01-T2 (далее прогоном в каждом плане с разметкой) | 01 | 1 | FORM-03 | T-11-02 | цели свопа существуют, `x-data`-узел не цель, OOB по `id`; разметочные константы пересчитаны | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q` | ✅ (пересчёт констант) | ⬜ pending |
| 11-09-T1, 11-09-T2 (исходы — 11-01…11-08) | 09 | 9 | FORM-04 | T-11-28 | `retry_sync`, `sync_groups`, исходы расписаний/оплаты/админки → 204 + `HX-Location`, тела нет; `_SYNC_IN_FLIGHT` освобождается | integration | `uv run pytest tests/test_routes/test_sync_groups.py tests/test_routes/test_wa_sync_status.py tests/test_pages/test_hx_location_destinations.py -q` | ✅, случаи — модуль пар | ⬜ pending |
| 11-08-T1, 11-08-T2 | 08 | 8 | FORM-05 | T-11-23 (открытый редирект, Spoofing) | без htmx → 302 на `confirmation_url`; htmx → 204 + `HX-Redirect`; чужой хост/схема → заголовка нет, `HX-Location` на `/billing?notice=…`; `HX_HEADER_WRITES` = 3, `SAFE_BY_NAME` = 2 записи | integration + gate | `uv run pytest tests/test_pages/test_billing_subscription.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_htmx_gates.py -q -k "subscribe or redirect or header_write or triple_pair"` | ✅ файлы, тесты — 11-08 | ⬜ pending |
| 11-04-T1 | 04 | 4 | FORM-07 | T-11-10 | создание: фрагмент раскрытой карточки для `beforeend` в контейнер `#sched-list` + OOB счётчика; «было ноль» → 204 `HX-Location` `/ads/{id}/edit?sched=N#sched-N` | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -k "appends_the_card or first_schedule_over_htmx"` | тесты — 11-04-T1 | ⬜ pending |
| 11-05-T2, 11-10-T1 | 05, 10 | 5, 10 | FORM-08 | T-11-13, T-11-31 (XSS эхо ввода) | профиль: неверный пояс → 422, форма с выбранным значением, без `<!DOCTYPE`; MAX: пустой телефон → 422 с эхо; правило 422 и `SERVER_SIDE_VALIDATION_RESPONSES` сдвинуты явно | integration + gate | `uv run pytest tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_shell.py tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py -q` | утверждение `swap is False` переписывается — 11-05-T2 | ⬜ pending |
| 11-05-T1 | 05 | 5 | FORM-08 | T-07-13 | на htmx-пути нет тела отказа валидации FastAPI (нечисловой id на маршрутах с целым параметром пути, пропущенное поле) | integration | `uv run pytest tests/test_pages/test_htmx_validation_sink.py -q` | модуль — 11-05-T1 | ⬜ pending |
| 11-05-T3 | 05 | 5 | FORM-10 | T-11-16 | вхождений `HX-Retarget`/`HX-Reswap` в `app/` == записей перечня | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k retarget` | гейт — 11-05-T3 | ⬜ pending |
| 11-01-T1 (модуль, замыкание), 11-11-T1 (обход, число) | 01, 11 | 1, 11 | GATE-02 | T-11-36 | число утверждений 302 == константе, снятой обходом; у каждого переведённого обработчика ≥ 1 пара; существующие 302 не удалены | gate + parametrized | `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q` | модуль — 11-01-T1 | ⬜ pending |
| 11-02-T1/T2, 11-04-T3, 11-06-T3, 11-09-T3, 11-10-T2 | 02, 04, 06, 09, 10 | 2, 4, 6, 9, 10 | D-07 (окно 51) | T-11-04, T-11-34 (DoS переполнение столбца) | `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` 23 → 0; id вне диапазона ≡ «нет/чужое»; проверка первым использованием | gate + integration | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_identifier_bounds.py -q -k "validation_refusal or framework_bound or checked_before_its_first_use"` | ✅ (реестр пустеет) | ⬜ pending |
| 11-06-T1/T2, 11-08-T2 | 06, 08 | 6, 8 | D-08 (окно 63) | T-11-17, T-11-27 (CSRF, Tampering) | `OWN_RESPONSE_EXITS_DECLARED` 9 → 12, голый 403 на провале `is_same_origin`, состояние решения D-08 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k own_response` | ✅ | ⬜ pending |
| 11-07-T1, 11-07-T2 | 07 | 7 | D-10 | T-11-21 | 0 вхождений `?result=` в `app/`; коды в `notices.py` с дословными текстами | gate | `uv run pytest tests/test_pages/test_notices_channel.py tests/test_pages/test_confirm_delete_transport.py -q` | гейт — `RETIRED_QUERY_KEYS` (11-07-T2) | ⬜ pending |
| 11-03-T2 | 03 | 3 | D-11 | T-11-09 | keyset `/schedules/partial`: тумблер под фильтром не теряет строку | integration | `uv run pytest tests/test_pages/test_schedules_list.py -q -k "does_not_skip_a_row"` | тест — 11-03-T2 | ⬜ pending |
| 11-04-T2 | 04 | 4 | D-13 | T-11-11 | `HX-Push-Url: /ads/{id}/edit` на создании переживает переезд на `respond()` | integration | `uv run pytest tests/test_pages/test_ads_editor.py -q -k "push_url_header_after_the_move"` | тест — 11-04-T2 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] модуль пар GATE-02 (реестр случаев, AST-обход, константа, замыкание с `NOT_YET_CONVERTED`)
- [ ] тесты третьего выхода в `tests/test_pages/test_htmx_response_layer.py` (хост, схема, суффикс, userinfo, порт)
- [ ] гейт перечня `HX-Retarget`/`HX-Reswap` (FORM-10)
- [ ] гейт `?result=` == 0 (D-10)
- [ ] переписать `test_validation_rule_carries_both_swap_and_error` и литерал `tests/test_pages/test_shell.py:1300` вместе с правилом 422
- [ ] тест отсутствия 422 умолчания на htmx-пути страничных POST (T-07-13)
- [ ] фикстура `CONFIRMATION_URL` на документированном хосте для htmx-пар оплаты

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Переход в ЮKassa на тестовом ключе; фактический хост `confirmation_url` | FORM-05 | внешний сервис, реальный ключ | на `/billing` оформить подписку с htmx; записать хост страницы подтверждения и сверить с закрытым множеством D-09 |
| Позиция прокрутки при создании расписания | FORM-07 | браузер | в редакторе с длинным списком прокрутить вниз, создать расписание; прокрутка не сбрасывается, карточка в конце списка |
| Alpine после свапа: раскрытая карточка, `accounts/*`, утечка слушателей, размножение панелей | критерий 5 (UAT п. 5) | браузер, накопление за десятки действий | десятки действий без перезагрузки в `schedules`, `admin`, `accounts`; панели не множатся, раскрытие держится |
| Back и F5 не предлагают повторить POST; `hx-push-url` меняет адрес | критерий 5 (UAT п. 7) | история браузера | после переходов `HX-Location` и создания объявления нажать Back и F5 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
