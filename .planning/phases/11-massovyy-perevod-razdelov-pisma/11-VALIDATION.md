---
phase: "11"
slug: "massovyy-perevod-razdelov-pisma"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-14"
validated: "2026-09-17"
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
> Ревизия 2 планирования (2026-09-14): 13 планов → 20; идентификаторы задач приведены к новой нумерации.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-T1, 11-03-T1/T2, 11-04-T2, 11-05-T1/T2, 11-06-T1, 11-09-T1, 11-12-T1/T2, 11-13-T1/T2, 11-18-T2 | 01, 03, 04, 05, 06, 09, 12, 13, 18 | 1, 3, 4, 5, 6, 9, 12, 13, 18 | FORM-03 | T-11-01, T-11-07 | 9 фрагментных обработчиков: htmx → 200 фрагмент по `id`, без `<!DOCTYPE`, OOB-счётчик/notice; без htmx → 302 | integration | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_schedules_list.py tests/test_pages/test_admin_panel.py tests/test_pages/test_ads_editor.py tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py -q` | ✅ файлы, пары — 11-01-T1 | ✅ green |
| 11-01-T1 … 11-18-T2 (каждый перевод) | 01–18 | 1–18 | FORM-03 | — | `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 3 → 12, `NOT_YET_CONVERTED_COUNT` 26 → 14 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q` | ✅ (числа двигаются) | ✅ green |
| 11-01-T2, 11-08-T2, 11-11-T1, 11-18-T1 (далее прогоном в каждой задаче разметки) | 01, 08, 11, 18 | 1, 8, 11, 18 | FORM-03 | T-11-02 | цели свопа существуют, `x-data`-узел не цель, OOB по `id`; разметочные константы пересчитаны; выносы во включаемые шаблоны (настройки профиля, состояние карточки пользователя, шаг мастера MAX) не меняют разметку страницы | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_pages/test_responsive_markup.py -q` | ✅ (пересчёт констант) | ✅ green |
| 11-16-T1, 11-17-T1 (исходы — 11-01…11-15) | 16, 17 | 16, 17 | FORM-04 | T-11-28 | `retry_sync`, `sync_groups`, исходы расписаний/оплаты/админки → 204 + `HX-Location`, тела нет; `_SYNC_IN_FLIGHT` освобождается | integration | `uv run pytest tests/test_routes/test_sync_groups.py tests/test_routes/test_wa_sync_status.py tests/test_pages/test_hx_location_destinations.py -q` | ✅, случаи — модуль пар | ✅ green |
| 11-15-T1, 11-15-T2 | 15 | 15 | FORM-05 | T-11-23 (открытый редирект, Spoofing) | без htmx → 302 на `confirmation_url`; htmx → 204 + `HX-Redirect`; чужой хост/схема → заголовка нет, `HX-Location` на `/billing?notice=…`; `HX_HEADER_WRITES` = 3, `SAFE_BY_NAME` = 2 записи | integration + gate | `uv run pytest tests/test_pages/test_billing_subscription.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_htmx_gates.py -q -k "subscribe or redirect or header_write or triple_pair"` | ✅ файлы, тесты — 11-15 | ✅ green |
| 11-05-T1 (разметка вставки — 11-05-T2) | 05 | 5 | FORM-07 | T-11-10 | создание: фрагмент раскрытой карточки для `beforeend` в контейнер `#sched-list` + OOB счётчика; «было ноль» → 204 `HX-Location` `/ads/{id}/edit?sched=N#sched-N` | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -k "appends_the_card or first_schedule_over_htmx"` | тесты — 11-05-T1 | ✅ green |
| 11-08-T1, 11-09-T1, 11-10-T1, 11-18-T2 | 08, 09, 10, 18 | 8, 9, 10, 18 | FORM-08 | T-11-13, T-11-31 (XSS эхо ввода) | выход `respond_field_error` — единственный литерал 422 в `app/*.py`; профиль: неверный пояс → 422, форма с выбранным значением, без `<!DOCTYPE`; MAX: пустой телефон → 422 с эхо; правило 422 и `SERVER_SIDE_VALIDATION_RESPONSES` сдвинуты явно | integration + gate | `uv run pytest tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_shell.py tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py -q` | утверждение `swap is False` переписывается — 11-09-T1 | ✅ green |
| 11-07-T1 | 07 | 7 | FORM-08, D-07 | T-07-13, T-11-37, T-11-38 | на htmx-пути к обработчику страничного слоя нет тела отказа валидации FastAPI (путь — обход маршрутов с целым параметром пути; тело формы и строка запроса — поимённые случаи); ответы JSON-API `app/routes/` с заголовком htmx и без него байт-в-байт одинаковы (422 JSON); ни один адрес запроса htmx в шаблонах не указывает на `/api/` | integration + gate | `uv run pytest tests/test_pages/test_htmx_validation_sink.py tests/test_routes/test_schedules_api_identifier_bounds.py -q` | модуль — 11-07-T1 | ✅ green |
| 11-10-T2 | 10 | 10 | FORM-10 | T-11-16 | вхождений `HX-Retarget`/`HX-Reswap` в `app/` == записей перечня | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k retarget` | гейт — 11-10-T2 | ✅ green |
| 11-01-T1 (модуль, замыкание), 11-20-T1 (обход, число) | 01, 20 | 1, 20 | GATE-02 | T-11-36 | число утверждений 302 == константе, снятой обходом; у каждого переведённого обработчика ≥ 1 пара; существующие 302 не удалены | gate + parametrized | `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q` | модуль — 11-01-T1 | ✅ green |
| 11-02-T1/T2, 11-06-T2, 11-11-T2, 11-17-T3, 11-19-T1/T2 | 02, 06, 11, 17, 19 | 2, 6, 11, 17, 19 | D-07 (окно 51) | T-11-04, T-11-34 (DoS переполнение столбца) | `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` 23 → 0; id вне диапазона ≡ «нет/чужое»; проверка первым использованием; контроли реестра на синтетических входах до его опустения | gate + integration | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_identifier_bounds.py -q -k "validation_refusal or framework_bound or checked_before_its_first_use"` | ✅ (реестр пустеет) | ✅ green |
| 11-12-T1, 11-13-T1, 11-15-T2 | 12, 13, 15 | 12, 13, 15 | D-08 (окно 63, часть «решение о форме») | T-11-17, T-11-27 (CSRF, Tampering) | `OWN_RESPONSE_EXITS_DECLARED` 9 → 12, голый 403 на провале `is_same_origin`, состояние решения D-08 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k own_response` | ✅ | ✅ green |
| 11-14-T1, 11-14-T2 | 14 | 14 | D-10 | T-11-21 | 0 вхождений `?result=` в `app/`; коды в `notices.py` с дословными текстами | gate | `uv run pytest tests/test_pages/test_notices_channel.py tests/test_pages/test_confirm_delete_transport.py -q` | гейт — `RETIRED_QUERY_KEYS` (11-14-T2) | ✅ green |
| 11-20-T3 | 20 | 20 | D-07 (окно 51), D-08 (окно 63) | T-11-35 | окно 51 `fixed` командой реестра; окно 63 остаётся `open`, частичное решение D-08 записано летописью в `ROADMAP.md`; флажки и клетки состояний не тронуты | gate | `uv run pytest tests/test_planning/ -q` | ✅ | ✅ green |
| 11-04-T1 | 04 | 4 | D-11 | T-11-09 | keyset `/schedules/partial`: тумблер под фильтром не теряет строку | integration | `uv run pytest tests/test_pages/test_schedules_list.py -q -k "does_not_skip_a_row"` | тест — 11-04-T1 | ✅ green |
| 11-06-T1 | 06 | 6 | D-13 | T-11-11 | `HX-Push-Url: /ads/{id}/edit` на создании переживает переезд на `respond()` | integration | `uv run pytest tests/test_pages/test_ads_editor.py -q -k "push_url_header_after_the_move"` | тест — 11-06-T1 | ✅ green |
| 11-21-T1, 11-21-T2 | 21 | 1 (партия закрытия гэпов) | FORM-03, FORM-04, FORM-08 (`G-11-6`) | T-11-42 (перехват нажатия), T-11-43, T-11-44, T-11-45 | индикатор формы обёртки не занимает места в потоке: область задаёт класс, печатаемый ТОЛЬКО макросом `form_wrapper`; `pointer-events: none` — нажатие по углу органа доходит до него; панель подтверждения печатает тот же узел и под область НЕ попадает (её ~22 px приняты решением владельца 1, 10-UAT 3.5) | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_components.py -q` | 4 гейта — 11-21-T1/T2 | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Каждый пункт заводится RED-шагом названной задачи до её GREEN-шага; ни одна команда `<automated>` планов
не ссылается на модуль, который заводит не её собственная задача либо задача более раннего плана.

- [x] модуль пар GATE-02 (реестр случаев, AST-обход, константа, замыкание с `NOT_YET_CONVERTED`) — 11-01-T1 (реестр и замыкание), 11-20-T1 (обход и число)
- [x] тесты третьего выхода в `tests/test_pages/test_htmx_response_layer.py` (хост, схема, суффикс, userinfo, порт) — 11-15-T1
- [x] гейт перечня `HX-Retarget`/`HX-Reswap` (FORM-10) — 11-10-T2
- [x] гейт `?result=` == 0 (D-10) — 11-14-T2
- [x] переписать `test_validation_rule_carries_both_swap_and_error` и литерал `tests/test_pages/test_shell.py:1300` вместе с правилом 422 — 11-09-T1
- [x] тест отсутствия 422 умолчания на htmx-пути страничных POST (T-07-13) — 11-07-T1
- [x] фикстура `CONFIRMATION_URL` на документированном хосте для htmx-пар оплаты — 11-15-T2

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

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [ ] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Основание отметок (ревизия 2 планирования, 2026-09-14, замер по 20 планам).** Каждая из задач всех
двадцати планов несёт `<automated>` в `<verify>` — непрерывность выборки выполняется тем же фактом; ни
один `<verify>` не несёт маркера `MISSING` — новые модули (`test_htmx_post_pairs.py`,
`test_htmx_validation_sink.py`, `test_max_connect_transport.py`) заводятся RED-шагом той же задачи, чья
команда их прогоняет, и каждый пункт Wave 0 привязан к задаче выше; флагов режима наблюдения нет.
**Задержка обратной связи не отмечена:** её основание — время прогона, а не текст плана; быстрый круг
один уже занимает ~19 с, а задачи прогоняют его вместе с модулем раздела, так что пункт измеряется при
исполнении, а не утверждается при планировании. `status: draft` и `wave_0_complete: false` верны до
исполнения Wave 0 и `/gsd-validate-phase`.

**Задержка обратной связи измерена при аудите (2026-09-17) и пункт остаётся неотмеченным:**
`uv run pytest tests/test_pages/test_htmx_gates.py -q` — `49 passed in 21.01s`, стена 24,2 с с запуском
`uv`; модуль вырос с 43 до 49 тестов за фазу. Это превышение порога выборки, а не пробел покрытия:
`nyquist_compliant` определяется наличием автоматической проверки у каждого требования.

**Approval:** approved 2026-09-17 (аудит `/gsd-validate-phase 11`, пробелов 0)

---

## Validation Audit 2026-09-17

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Основание.** Дерево `05963ea` (последний коммит 11-20), без правок в `app/` и `tests/` после гейта.

- **Зелень.** Полная суита на этом дереве (гейт волны 20): `3406 passed, 1000 warnings in 2267.02s`, exit 0,
  строк `FAILED`/`ERROR` — 0; ночной красный окна 85 в прогон 08:03–08:41 UTC не попал.
- **Невакуумность команд карты** (`--collect-only`, 16 строк): 307, 49, 216, 54, 13, 2, 303, 27, 3, 56, 6,
  7, 118, 44, 1, 1 тестов. Ни одна `-k`-выборка не пуста, выбранные имена соответствуют поведению строки
  (`test_schedule_create_over_htmx_appends_the_card_to_the_list`,
  `test_the_first_schedule_over_htmx_lands_by_a_location_header`,
  `test_every_retarget_or_reswap_use_is_declared`,
  `test_the_next_portion_does_not_skip_a_row_after_a_toggle_under_the_state_filter`,
  `test_created_draft_keeps_the_push_url_header_after_the_move_to_the_response_layer` и др.).
- **Числа реестров сверены с картой:** `NOT_YET_CONVERTED_COUNT = 14`,
  `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 12`, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0`,
  `OWN_RESPONSE_EXITS_DECLARED = 12`, `HX_HEADER_WRITES = 3`, `SAFE_BY_NAME` — 2 записи,
  `RETARGET_RESWAP_USES = {}` при `RETARGET_RESWAP_USES_DECLARED = 0`,
  `PAIRED_302_ASSERTIONS_DECLARED = 158`, `HX_LOCATION_DESTINATION_CALLS_DECLARED = 72`.
- **Литералы:** `?result=` в `app/` — 0 вхождений. Исполняемый литерал `422` в `app/*.py` — один
  (`app/pages/htmx.py:904`, выход `respond_field_error`), остальные 22 вхождения — комментарии и докстринги.
- **Третий выход:** `test_a_confirmation_address_off_the_closed_host_set_never_reaches_the_header` —
  18 параметризованных враждебных адресов.
- **Реестр окон:** 51 — `fixed`; 63, 84, 85, 86, 87 — `open`, как заявляет строка 11-20-T3.

**Ручные проверки не изменились:** четыре строки раздела Manual-Only остаются ручными по природе
(внешний сервис, браузер, история). Окно 87 фиксирует, что UAT перехода в ЮKassa ещё не проведён.

---

## Validation Audit 2026-09-17 (партия закрытия гэпов, план 11-21)

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Основание.** Дерево `fa2b766` (пост-слияночный гейт оркестратора `/gsd-execute-phase 11 --gaps-only`).
Предыдущий аудит снят на `05963ea` — ДО существования плана 11-21, и его «0 гэпов» ошибкой не было:
оно верно для состава фазы до первой партии закрытия гэпов.

- **Гэпов не заведено, потому что поведение приехало с гейтами, а не без них.** Задачи 11-21-T1 и
  11-21-T2 — обе `tdd="true"`, и обе предъявили КРАСНОЕ до зелёного: T1 замером
  (`2 failed` → `2 passed`, `check tdd-red-evidence` → `RED_EVIDENCE_OK`), T2 — двумя мутантами
  (селектор без области; класс области на теге панели), каждый из которых красит ровно свой гейт.
  Классификация строки карты — COVERED, а не MISSING: чинить нечего, недоставало ЗАПИСИ.
- **Невакуумность команды строки** (`--collect-only -k "indicator_scope or layout_footprint or
  outside_the_indicator_scope or accepted_place"`): `4/171 tests collected` — выборка не пуста, и
  четыре имени соответствуют поведению строки
  (`test_the_reported_profile_form_carries_the_indicator_scope`,
  `test_a_wrapped_form_gives_its_indicator_no_layout_footprint`,
  `test_the_panel_form_stays_outside_the_indicator_scope`,
  `test_the_confirmation_panel_indicator_keeps_its_accepted_place`).
  Полный прогон обоих файлов: `171 passed in 12.04s`.
- **Числа реестров, сверенные планом:** `pointer-events: none;` 1 → 2; базовое правило `.form-busy`
  по-прежнему ровно 1; контроль числа файлов 24; `PANEL_QUALITY_DIFFERENCES_ALLOWED` = 2;
  `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED` = 1 (точка строки группы — объявленное исключение).
- **Полная суита оркестратора ПОСЛЕ коммитов трекинга:** `2 failed, 3408 passed in 2233.49s`; оба
  отказа — в `tests/test_planning/` и внесены самим шагом трекинга (преждевременные отметки
  FORM-03/04/08 и проза `**Plans**` 20 при 21 отметке), исправлены в `fa2b766`, после чего
  `tests/test_planning/` — `44 passed`. В `app/` и `tests/` отказов нет ни одного.

**Ручное остаётся ручным:** пункт 5a проверки 6 `11-UAT.md` (точка над углом органа — перенос ряда и
тумблер шапки 40 px в положении «вкл») НАБЛЮДЕНИЕМ НЕ СНЯТ и записан открытой записью
`unrun-verify` в `.planning/WINDOWS.md`. Гейт доказывает ОТСУТСТВИЕ СЛЕДА В ПОТОКЕ и проходимость
нажатия, но не то, что 8 px не накрывают подпись — это предмет глаза, а не утверждения.
