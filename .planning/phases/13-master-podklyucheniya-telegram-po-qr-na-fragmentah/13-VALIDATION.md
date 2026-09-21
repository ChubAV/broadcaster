---
phase: "13"
slug: "master-podklyucheniya-telegram-po-qr-na-fragmentah"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-09-21"
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

Источник — `13-RESEARCH.md` §Validation Architecture (строки 608-641), §Environment Availability и
§Security Domain; карта задач — планы `13-01`…`13-06`. Время прогона гейтов (157 с, 331 passed)
измерено разведкой на дереве 2026-09-21; время полного прогона (~36–37 мин) — по памяти проекта
(прогоны Фаз 11 и 12), не перемерялось.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio, httpx `AsyncClient` поверх ASGI, SQLite `:memory:` (гонки 13-02 — SQLite на временном файле) |
| **Config file** | `pyproject.toml`; фикстуры — `tests/conftest.py` (`client`, `htmx_client`, `authed_client`, `admin_client`, `db_session`) |
| **Quick run command** | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q -p no:randomly` |
| **Gate run command** | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_markup_security.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_htmx_post_pairs.py tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q -p no:randomly` |
| **Records command** | `uv run pytest tests/test_planning -q` (только план 13-06 правит записи) |
| **Full suite command** | `uv run pytest tests/ -q` (рецепт `just test`) |
| **Estimated runtime** | быстрый прогон — секунды; прогон гейтов — ~160 с; полный — ~36 мин |

---

## Sampling Rate

**Обратная связь и гейт завершения — разные инструменты.**

- **After every task commit (обратная связь):** первая команда `<automated>` задачи — модуль мастера
  и/или файл гейта, который задача двигает (секунды — десятки секунд).
- **After every plan (последняя задача плана):** прогон гейтов (Gate run command) — все перечни,
  которые фаза двигает, плюс модули мастера и слоя сессий.
- **After plan 13-01:** полный прогон ОДИН раз (13-01 двигает больше всего перечней; только полный
  прогон ловит перечни, не названные обходом разведки).
- **After every plan wave:** полный прогон — пост-слияночный гейт оркестратора (`just test`).
- **Before `/gsd-verify-work`:** полный прогон зелёный.
- **Max feedback latency:** ~160 с (прогон гейтов в конце плана); на задачу — меньше минуты.

⚠️ Полный прогон единицей обратной связи НЕ является: ~36 мин против секунд у быстрого прогона.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | FETCH-02 | T-13-04, T-13-06, T-13-07, T-13-09 | опрос останавливается ответом; аккаунт сохраняет только опрос, увидевший `success`; `session_id` не в адресе; тексты — автоэкранированием | tracer (e2e маршрутов на настоящем слое сессий) | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly` | ✅ переписывается | ✅ green |
| 13-01-02 | 01 | 1 | FETCH-02 | T-13-10 | подключение под имперсонацией разрешено поимённо с причиной | gate (перечни слоя ответа) | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` | ✅ | ✅ green |
| 13-01-03 | 01 | 1 | FETCH-02 | T-13-07 | слепота гейта опросов к опросчику из макроса измерена и записана | gate (перечни разметки) | `uv run pytest tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_inventory.py -q -p no:randomly` | ✅ | ✅ green |
| 13-02-01 | 02 | 2 | FETCH-02 | T-13-04, T-13-05, T-13-08 | пароль 2FA не эхается; два конкурентных сохранения дают один аккаунт; ошибка Telethon — фрагмент, не 500 | unit + concurrency (`asyncio.gather`, сессия базы на запрос) | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly` | ✅ | ✅ green |
| 13-02-02 | 02 | 2 | FETCH-02 | — | N/A | gate | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` | ✅ | ✅ green |
| 13-03-01 | 03 | 3 | FETCH-02 | T-13-15 | нормальное истечение кода не пишет `logger.error` с `session_id` и трассировкой | unit на настоящем `QRLogin` | `uv run pytest tests/test_messengers/test_telegram_user.py -q -p no:randomly -k "expired"` | ✅ | ✅ green |
| 13-03-02 | 03 | 3 | FETCH-02 | T-13-12, T-13-07 | устаревшая сессия не оживает; пересоздание только из `qr_expired`; обновление только кнопкой | unit + e2e маршрутов | `uv run pytest tests/test_messengers/test_telegram_user.py tests/test_routes/test_tg_user_auth.py -q -p no:randomly` | ✅ | ✅ green |
| 13-03-03 | 03 | 3 | FETCH-02 | — | N/A | gate | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` | ✅ | ✅ green |
| 13-04-01 | 04 | 4 | FETCH-02 | T-13-01, T-13-02, T-13-03, T-13-10 | чужой опрос отвечает как неизвестный побайтно и не трогает сессию владельца; привязка к субъекту имперсонации | unit + маршруты | `uv run pytest tests/test_messengers/test_telegram_user.py tests/test_routes/test_tg_user_auth.py -q -p no:randomly` | ✅ | ✅ green |
| 13-04-02 | 04 | 4 | FETCH-02 | T-13-01, T-13-02, T-13-03 | чужие `refresh-qr` и `verify-2fa` отвергнуты без `recreate`/`sign_in` | unit + маршруты | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k "foreign"` | ✅ | ✅ green |
| 13-05-01 | 05 | 5 | FETCH-02 | T-13-07 | каждая ветка шага достигнута; у каждого опроса есть терминальная пара; контроли краснят | gate + отрицательные контроли | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k "polling or control"` | ✅ | ✅ green |
| 13-05-02 | 05 | 5 | FETCH-02 | T-13-16 | возврат сценария на экран подключения краснит правило о предмете | gate | `uv run pytest tests/test_pages/test_hx_location_destinations.py tests/test_templates/test_htmx_markup_security.py tests/test_templates/test_components.py -q -p no:randomly` | ✅ | ✅ green |
| 13-06-01 | 06 | 5 | FETCH-02 | T-13-17 | критерии не переписаны, летописи стоят | records | `uv run pytest tests/test_planning -q` | ✅ | ✅ green |
| 13-06-02 | 06 | 5 | FETCH-02 | T-13-18 | FETCH-02 не отмечен выполненным до верификации | records | `uv run pytest tests/test_planning -q -k "requirement or flag_and_the_status"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Требование → тест (RESEARCH §Phase Requirements → Test Map)

| Критерий / решение | Поведение | Где доказывается |
|--------------------|-----------|------------------|
| кр. 1 | снят сценарий мастера, `complete` и GET-опрос; четыре маршрута отдают `text/html` | 13-01-01 (`test_the_wizard_page_carries_no_client_script`, `test_the_complete_route_and_the_get_poll_are_gone`), 13-01-03 (`MANUAL_FETCH_*` = 0) |
| кр. 2 | только шаг ожидания несёт `hx-trigger="every 3s"`; всё прочее 200 — без; опрос в ожидании — 204 | 13-01-01 (`test_polling_stops_by_a_response_without_trigger`), 13-02-01, 13-03-02, 13-05-01 (замыкание и контроли) |
| кр. 3 | чужой `session_id` на трёх обработчиках — ответ неизвестной сессии, сессия владельца цела | 13-04-01, 13-04-02 |
| кр. 4 | живой сценарий на Telethon | ручной UAT (ниже) |
| кр. 5 | документная запись «деградации без JS нет и сегодня» | 13-06 (летопись критерия 5 + раздел SUMMARY) |
| D-01 | два конкурентных сохранения → один аккаунт | 13-02-01 (`-k concurrent`), 13-04-01 (`test_concurrent_completes_yield_one_session_string`) |
| D-03 | таймаут `wait()` → `qr_expired`, не ошибка | 13-03-01 (настоящий `QRLogin`) |
| D-08 | 422 у поля, пароль не эхается | 13-02-01 |

---

## Wave 0 Requirements

Отдельной волны 0 нет: фреймворк, фикстуры и модули тестов существуют, а каждая задача фазы
начинается с RED своего поведения (TDD-режим). Заготовки, которых сегодня нет и которые заводит
план, их создающий:

- [x] `tests/test_routes/test_tg_user_auth.py` — переписывается на фикстуры `tests/conftest.py`; реестр `POLLING_CASES` и правило останова опроса (13-01); фикстура отдельной сессии базы на запрос для гонок (13-02); замыкание и контроли (13-05)
- [x] `tests/test_messengers/test_telegram_user.py` — тест D-03 на настоящем `QRLogin` (13-03); правила владения и гонка `complete_auth` (13-04)

*Existing infrastructure covers the framework; the rows above are created by their plans' RED steps.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Сканирование QR телефоном без 2FA → «Подключено», поток опросов в журнале прекращается | FETCH-02, кр. 4 | нужен настоящий аккаунт Telegram и телефон; сервер Telegram не подменяем | Открыть `/accounts/connect/tg_user`, «Начать подключение», отсканировать в Telegram (Настройки → Устройства → Подключить устройство); ждать «Подключено»; в журнале uvicorn после этого нет `POST …/qr-status` |
| Аккаунт с 2FA: неверный пароль → ошибка у поля, поле пустое; верный → «Подключено» | FETCH-02, кр. 4, D-08 | живая сессия Telethon с паролем 2FA | Отсканировать аккаунт с 2FA; ввести неверный пароль, затем верный |
| «Код истёк» → «Обновить QR-код» → новый код, опрос возобновлён | FETCH-02, кр. 4, D-02, D-03 | время жизни токена задаёт Telegram (~30 с, A3) | Получить QR и НЕ сканировать ≥ ~30 с; нажать «Обновить QR-код»; отсканировать новый код |
| «Сессия авторизации истекла» после простоя | FETCH-02, D-03 | нужен простой ≥ ~270 с на экране «код истёк» | Дождаться «код истёк», ждать ещё ≥ 270 с, нажать «Обновить QR-код» — ждать шаг с формой «Начать заново» |

**Предусловия стенда UAT:** `telegram_api_id` / `telegram_api_hash` заданы; часы хоста синхронизированы
NTP (RESEARCH §Pitfall 6 — иначе каждый код мгновенно «истёк»). Браузер CDP стоит на другой машине,
сканирует человек; машинная улика обхода — не приёмка (память проекта). `human_verify_mode:
end-of-phase` — чекпоинтов внутри планов нет, обход — на приёмке фазы.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 180s
- [x] `nyquist_compliant: true` set in frontmatter — выставлен `/gsd-validate-phase 13` по замеру 2026-09-21 (раздел аудита ниже)

**Approval:** validated 2026-09-21 (`/gsd-validate-phase 13`, прогон из `/gsd-execute-phase 13`)

---

## Validation Audit 2026-09-21

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**Замер, а не перенос статусов из сводок.** Все 14 строк карты сверены прогоном их команд на дереве
`e5c1288c` (после всех шести планов), с `-p no:randomly`; у каждого отбора `-k` число отобранных
ненулевое — зелень не вакуумная:

| Строки карты | Команда (сокращённо) | Итог |
|--------------|----------------------|------|
| 13-01-01, 13-02-01 | `tests/test_routes/test_tg_user_auth.py` | 56 passed |
| 13-01-02 (надмножество 13-02-02, 13-03-03) | пять файлов гейтов слоя ответа | 166 passed |
| 13-01-03 | `test_htmx_markup_gates.py` + `test_htmx_inventory.py` | 102 passed |
| 13-03-01 | `test_telegram_user.py -k expired` | 3 passed, 31 deselected |
| 13-03-02, 13-04-01 | `test_telegram_user.py` + `test_tg_user_auth.py` | 90 passed |
| 13-04-02 | `test_tg_user_auth.py -k foreign` | 6 passed, 50 deselected |
| 13-05-01 | `test_tg_user_auth.py -k "polling or control"` | 34 passed, 22 deselected |
| 13-05-02 | `test_hx_location_destinations.py` + `test_htmx_markup_security.py` + `test_components.py` | 119 passed |
| 13-06-01 | `tests/test_planning` | 44 passed |
| 13-06-02 | `tests/test_planning -k "requirement or flag_and_the_status"` | 16 passed, 28 deselected |

Правила, названные таблицей «Требование → тест», существуют в дереве поимённо (проверено грепом
определений): `test_the_wizard_page_carries_no_client_script`,
`test_the_complete_route_and_the_get_poll_are_gone`, `test_polling_stops_by_a_response_without_trigger`
(`tests/test_routes/test_tg_user_auth.py`), `test_concurrent_completes_yield_one_session_string`
(`tests/test_messengers/test_telegram_user.py`); отбор `-k concurrent` модуля мастера — 2 правила.

**Полный прогон после каждой волны** (пост-слияночный гейт оркестратора, `just test`, без отбора
маркером): 3459 → 3473 → 3486 → 3501 → **3511 passed, 0 failed** (волна 5, 39:02, HEAD `e5c1288c`).
⚠️ Оценка «~36 мин» в §Test Infrastructure не была ошибкой — она устарела: перемер этой фазы даёт
39:02–39:43 на пяти прогонах; строка выше не правится по идиоме D-30/D-32.

**TDD-гейт конца фазы в этой фазе НЕ вакуумен:** планы 13-01…13-04 объявлены `type: tdd`, и
`tdd.review-checkpoint` отчитался `tddPlans: 4, violations: 0` (RED и GREEN найдены в истории у
каждого). План 13-05 — `type: execute` с задачей `tdd="true"`: гейт его не видит, улика — в
`13-05-SUMMARY.md` (правила зелены на живом дереве с первого прогона, раскрыто; непустота доказана
мутантами продукта).

**Manual-Only не сдвинут:** четыре проверки критерия 4 над живой сессией Telethon остаются за
человеком — автоматизировать их нельзя (сервер Telegram не подменяем), и аудит их в «покрытые» не
переводит.
