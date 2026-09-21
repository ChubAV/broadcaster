---
phase: "13"
slug: "master-podklyucheniya-telegram-po-qr-na-fragmentah"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
block_on: high
created: "2026-09-21"
register_authored_at_plan_time: true
# ⚠️ АУДИТОР НЕ ЗАПУСКАЛСЯ, И ЭТО НЕ ПРОПУСК, А ПРАВИЛО СПИНЫ. `secure-phase.md` шаг 3:
# `threats_open: 0 AND register_authored_at_plan_time: true AND asvs_level == 1` → прямо к шагу 6,
# глубины L1 (grep) достаточно. Реестр собран оркестратором из шести блоков `<threat_model>` и
# шести разделов `## Threat Flags`; каждое смягчение сверено по коду и по названному правилу суиты,
# а шесть файлов суиты, несущих эти правила, прогнаны (154 passed). Ретроспективный STRIDE НЕ
# запускался — новые угрозы не искались.
---

# Phase 13 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Фаза: «Мастер подключения Telegram по QR на фрагментах». Проверка проведена 2026-09-21
оркестратором `/gsd-secure-phase` по ASVS L1, порог блокировки — `high`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → страничный слой | тело POST опроса, обновления кода и пароля; признак htmx; cookie сессии входа | `session_id` (целиком управляем клиентом), пароль 2FA, cookie |
| страничный слой → слой QR-сессий | идентичность пользователя и ключ сессии | `user.id` субъекта (под имперсонацией — субъект), `session_id` как ключ словаря в памяти процесса |
| слой сессий → Telegram | `sign_in(password=…)`, `recreate()` — новый `ExportLoginToken` | пароль 2FA, токен входа |
| слой сессий → база | запись `MessengerAccount` | строка сессии Telethon — полный доступ к аккаунту Telegram |
| страничный слой → браузер | фрагменты шага мастера | QR (data URI), тексты отказа, в том числе текст исключения старта |
| шаблон шага → браузер | наличие формы-опросчика в ответе решает, остановится ли опрос | разметка шага |
| часы сервера ↔ `expires` Telegram | таймаут `wait()` считается по локальным часам | время |
| журнал → внешний читатель | `session_id` пишется на ошибках (`qr_auth_error`, `qr_refresh_error`) | `session_id` |
| записи планирования → верификатор и аудит вехи | критерии и требования читаются как контракт приёмки | текст ROADMAP / REQUIREMENTS |

---

## Threat Register

19 уникальных идентификаторов после устранения повторов, собраны из 22 строк шести планов.
Повторы: T-13-04 (13-01, 13-02), T-13-07 (13-01, 13-03, 13-05), T-13-10 (13-01 — `accept`,
13-04 — `mitigate`). Для T-13-10 действует диспозиция 13-04: более поздний план заменил
принятие смягчением, и в реестре она итоговая.

| Threat ID | Category | Component | Severity | Disposition | Mitigation (evidence) | Status |
|-----------|----------|-----------|----------|-------------|------------------------|--------|
| T-13-01 | Elevation / Spoofing | опрос, `verify-2fa`, `refresh-qr` — чужой `session_id` сохраняет чужой Telegram себе | high | mitigate | `telegram_user.py:36` `user_id: int` без умолчания; `_owned` `:119-124` (`state.user_id != user_id` → None); вызовы `_owned` — первая строка `get_qr_status` `:134`, `refresh_qr` `:156`, `submit_2fa` `:189`, `complete_auth` `:216`; все три обработчика передают `user.id` (`accounts.py:395,478,554`). Правила `test_a_foreign_poll_…` `test_tg_user_auth.py:1098`, `test_a_foreign_refresh_…` `:1185`, `test_a_foreign_password_…` `:1222` | closed |
| T-13-02 | DoS | чужой запрос снимает, отменяет, пересоздаёт или авторизует сессию жертвы | medium | mitigate | `_owned` стоит ДО `pop` (`:216` → `:219`), ДО `recreate` (`:156` → `:171`), ДО `sign_in` (`:189` → `:196`). `cleanup_qr_session` (`:236`) проверки не несёт, но вызовов в `app/` у неё ноль. Правила слоя `test_a_foreign_complete_leaves_the_session_alone` `test_telegram_user.py:647`, `test_a_foreign_refresh_changes_nothing` `:751`, `test_a_foreign_password_is_never_submitted` `:786` | closed |
| T-13-03 | Info Disclosure | ответ раскрывает существование чужой сессии | medium | mitigate | чужая = неизвестная: один статус `gone` (`telegram_user.py:134-136`); владелец проверяется раньше срока (`:134` раньше `:143`). Помощник `_same_answer` `test_tg_user_auth.py:328-343` сравнивает код и тело ПОБАЙТНО (`foreign.content == unknown.content`); `test_a_foreign_user_sees_no_session` `test_telegram_user.py:627` | closed |
| T-13-04 | Tampering | двойное сохранение при двух опросах после `success` или двух подтверждениях пароля (Pitfall 3) | medium | mitigate | `complete_auth` `telegram_user.py:216-219`: между проверкой и `pop` нет `await`; строка для записи берётся только из результата `complete_auth` (`accounts.py:411,574`), место записи одно — `_save_tg_account` `:276`. Правила `test_two_concurrent_password_submits_save_one_account` `test_tg_user_auth.py:1271`, `test_two_concurrent_polls_after_success_save_one_account` `:1325`, модульное `test_concurrent_completes_yield_one_session_string` `test_telegram_user.py:696`. ⚠️ См. Unregistered Flags п. 2 (WR-04): мутант перестановки ловит только модульное правило | closed |
| T-13-05 | Info Disclosure | ответ 422 шага пароля и журнал | high | mitigate | пароль в контекст шаблона не передаётся: страница `accounts.py:588-598` и фрагмент `:601-606` несут только `password_error`; поле без `value` (`tg_connect_step.html:104-106`); запись журнала на ветке Telethon — только `error_type` (`accounts.py:570-572`). Правило `test_a_wrong_password_answers_422_at_the_field_without_echo` `test_tg_user_auth.py:888` | closed |
| T-13-06 | Tampering (XSS) | шаг `error` — текст исключения старта и текст ошибки состояния в разметке | medium | mitigate | `_tg_step_markup` рендерит окружением (`accounts.py:267`), автоэкранирование — умолчание Starlette `env_options.setdefault("autoescape", True)` при `Jinja2Templates(...)` `common.py:36`; ни `|safe`, ни `Markup(` в `tg_connect_step.html`, `connect_tg_user.html` и `accounts.py` (grep — ноль); макрос `alert` выводит `{{ message }}` без снятия экранирования (`components/alert.html`) | closed |
| T-13-07 | DoS | вечный опрос: триггер на якоре, опросчик в общей ветке, автообновление забытой вкладкой | medium | mitigate | опросчик `trigger='every 3s'` — ТОЛЬКО в ветке `waiting` (`tg_connect_step.html:47-62`); якорь `connect_tg_user.html:24` триггера не несёт; шаг `qr_expired` без опросчика (`:68-83`), обновление — кнопкой. Правила `test_polling_stops_by_a_response_without_trigger` (`test_tg_user_auth.py`, `test_htmx_inventory.py`), замыкание `POLLING_CASES`, контроль якоря `test_control_the_anchor_inside_a_fragment_reddens_the_guard` `test_tg_user_auth.py:1826` | closed |
| T-13-08 | DoS | необработанное исключение Telethon → 500 → баннер отказа (Pitfall 5) | low | mitigate | ветка `except Exception` `accounts.py:568-572` оставляет `step="error"` и отвечает фрагментом с «Начать заново». Правило `test_a_telethon_failure_on_the_password_step_is_a_fragment` `test_tg_user_auth.py:987` | closed |
| T-13-09 | Info Disclosure | `session_id` в адресе запроса (журналы, Referer) | low | mitigate | `session_id` — только скрытое поле тела POST (`tg_connect_step.html:61,79,103`); GET-опрос снят (`test_the_complete_route_and_the_get_poll_are_gone` `test_tg_user_auth.py:639`); утверждения `"?session_id" not in` `:487,490` | closed |
| T-13-10 | Repudiation | подключение под имперсонацией | low | mitigate | сессия привязана к субъекту `get_user_from_cookie` (`accounts.py:337`), аккаунт — на него же (`:287`); разрешение `ALLOWED_ROUTES` с причиной `test_impersonation_gate.py:236-238` (ключ `qr_status`). Правило `test_the_wizard_binds_the_session_to_the_impersonated_subject` `test_tg_user_auth.py:1152` | closed |
| T-13-11 | Tampering (CSRF) | POST опроса, обновления, пароля с чужого сайта | low | accept | см. AR-13-01 | closed |
| T-13-12 | Tampering / DoS | `refresh_qr` — оживление устаревшей сессии и сброс готового входа подделанным запросом (Pitfall 2) | medium | mitigate | `telegram_user.py:162` — только из `qr_expired`; `:167` — только в сроке `QR_SESSION_TTL`; иначе None до `recreate` (`:171`) и без смены статуса. Правила `test_refresh_qr_recreates_only_an_expired_code` `test_telegram_user.py:506`, `test_refresh_qr_does_not_revive_an_outdated_session` `:558`, `test_refreshing_a_non_expired_code_is_refused` `test_tg_user_auth.py:789`. ⚠️ См. Unregistered Flags п. 1 (WR-01): инвариант держится последовательно, под конкурентным обновлением ВЛАДЕЛЬЦА — нет | closed |
| T-13-13 | DoS | расхождение часов стенда с `expires` → каждый код мгновенно «истёк» (Pitfall 6) | low | accept | см. AR-13-02 | closed |
| T-13-14 | DoS | старт без JS заводит клиента Telethon, живущего до чистки по сроку (Pitfall 9) | low | accept | см. AR-13-03 | closed |
| T-13-15 | Info Disclosure | `qr_auth_error` с `session_id` и трассировкой на каждом нормальном истечении | low | mitigate | ветка `except asyncio.TimeoutError` `telegram_user.py:93-101` ставит `qr_expired` без записи в журнал; `logger.error` остался только в общей ветке `:109`. Правило `test_an_expired_qr_token_is_a_status_not_an_error` `test_telegram_user.py:442` утверждает `not module_logger.error.called` на настоящем `QRLogin` | closed |
| T-13-16 | Tampering | возврат инлайн-сценария на экран подключения без решения | low | mitigate | `TOP_LEVEL_BINDING_EXEMPTIONS_DECLARED = 0` `test_hx_location_destinations.py:544`; правило `test_the_connect_screen_declares_no_top_level_binding` `:1257`; `test_the_wizard_page_carries_no_client_script` `test_tg_user_auth.py:494` | closed |
| T-13-17 | Repudiation | критерий 3 и FETCH-02 утверждают «сохранённую» проверку, которой не было | low | mitigate | летописи «проверка ЗАВЕДЕНА»: `.planning/ROADMAP.md:660` (критерий 3), `.planning/REQUIREMENTS.md:52` (FETCH-02); текст требования `:51` не переписан | closed |
| T-13-18 | Tampering | преждевременная отметка FETCH-02 выполненным | low | mitigate | `REQUIREMENTS.md:51` — `[ ]`, `:151` — `Pending`; правило `test_requirement_completion_follows_verification.py` зелёное | closed |
| T-13-SC | Tampering (supply chain) | установки пакетов npm/pip/cargo | low | accept | см. AR-13-04 | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-13-01 | T-13-11 | Межсайтовому отправителю нужен `session_id` жертвы, а проверка владельца (T-13-01) его отвергает: чужой запрос получает ответ неизвестной сессии и сессию не трогает. Cookie и проверки источника проекта фазой не менялись | планировщик фазы (реестр 13-04) | 2026-09-21 |
| AR-13-02 | T-13-13 | Предусловие UAT — NTP на стенде. До фазы то же расхождение часов давало мгновенную «Ошибку авторизации», так что фаза отказ не ухудшает | планировщик фазы (реестр 13-03) | 2026-09-21 |
| AR-13-03 | T-13-14 | Так было и до фазы; ветвление по признаку htmx запрещено G-1/G-2; закрытие клиентов — отложенная работа (CONTEXT §Deferred, D-13). Находка ревизии IN-03 расширяет риск тем же классом: `_cleanup_expired_sessions` отменяет задачу, но клиента не отключает, и брошенная после позднего сканирования сессия оставляет живую авторизацию Telegram. Это остаётся под тем же отложенным решением | планировщик фазы (реестр 13-01), владелец (D-13) | 2026-09-21 |
| AR-13-04 | T-13-SC | Фаза не устанавливает ни одного пакета (RESEARCH §Package Legitimacy Audit); `git diff --stat` по `pyproject.toml`, `uv.lock`, `package.json`, `wa_worker/package.json` и файлам замков от базы раньше фазы до `HEAD` пуст | планировщик фазы (реестр 13-01), проверено 2026-09-21 | 2026-09-21 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Находки `13-REVIEW.md`, которые касаются компонентов реестра, но разрывом объявленного
смягчения не являются. Все они уровня WARNING или INFO, ни одна не блокирует. Записаны здесь,
чтобы не жили только в отчёте ревизии, который каждый круг перезаписывает целиком.

1. **WR-01: гонка при обновлении кода** (`13-REVIEW.md` WR-01, `telegram_user.py:162-178`). Проверка статуса стоит
   перед `await recreate()`, поэтому два конкурентных обновления ОДНОГО ВЛАДЕЛЬЦА оба пересоздают
   код. Соседствует с T-13-12, но смягчение T-13-12 направлено против подделанного запроса, а
   чужой запрос отсекается `_owned` раньше гонки. Постороннему она недоступна; для владельца это
   надёжность (две вкладки, повторная отправка без JS). Исправление описано в ревизии.
2. **WR-04: маршрутное правило гонки опроса зеленеет вакуумом** (`13-REVIEW.md` WR-04). Правило
   `test_two_concurrent_polls_after_success_save_one_account` не сводит два запроса в одну точку,
   и мутант перестановки `disconnect` перед `pop` оба маршрутных правила проходят. Свойство
   T-13-04 держит модульное правило `test_concurrent_completes_yield_one_session_string`, а его
   ревизия сама проверила против того же мутанта. Смягчение на месте; доказательство у названного
   в реестре правила слабее заявленного.
3. **WR-03: результат сканирования теряется при отказе записи** (`13-REVIEW.md` WR-03). `complete_auth` снимает
   единственную копию строки сессии до `commit`. При отказе базы ответом будет 500, а в списке
   устройств Telegram останется осиротевшая авторизация. Ни одна строка реестра этот отказ не
   описывает, поверхность заведена этой фазой (`_save_tg_account`). Это надёжность и
   гигиена авторизаций, а не разглашение.
4. **IN-01: сырой текст Telethon у поля пароля** (`13-REVIEW.md` IN-01). Ветки `ValueError` и `RuntimeError` в
   `verify-2fa` ловят и посторонние исключения Telethon и выводят их текст. Сверено с T-13-06:
   текст экранируется, так что XSS нет. Сверено с T-13-08: ответ 422 или фрагмент, а не 500.
   Это внутренний англоязычный текст на экране, но не секрет.
5. **IN-02: `submit_2fa` не проверяет `needs_2fa` в своём слое** (`13-REVIEW.md` IN-02). Сейчас статус проверяет
   обработчик (`accounts.py:554-561`), а проверка владельца T-13-02 стоит до `sign_in`. Будущий
   вызывающий, минуя обработчик, смог бы перевести сессию в `success`. Риск на будущее, а не
   текущий разрыв.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-21 | 19 | 19 | 0 | оркестратор `/gsd-secure-phase` (ASVS L1, block_on: high; аудитор не запускался — правило короткого замыкания шага 3) |

## Security Audit 2026-09-21
| Metric | Count |
|--------|-------|
| Threats found | 19 |
| Closed | 19 |
| Open | 0 |

Разбивка закрытий: **15 mitigate**, **4 accept** (T-13-11, T-13-13, T-13-14, T-13-SC), **0 transfer**.

Прогон правил, несущих доказательства:
`uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_hx_location_destinations.py tests/test_templates/test_htmx_inventory.py tests/test_planning/test_requirement_completion_follows_verification.py`
— **154 passed** (61.5 s).

Ни один файл реализации не изменён: проход был только на чтение.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-21
