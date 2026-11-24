---
phase: "19"
slug: "zahvat-nomera-pri-podklyuchenii"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-23"
---

# Phase 19 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Реестр собран из блоков `<threat_model>` планов 19-01…19-08 (составлен на этапе плана) и разделов `## Threat Flags` восьми сводок; новых поверхностей сводки не заявили (новое — одно поле `phone` в ответе существующих `/status` воркеров WA и MAX и разбор поля формы MAX; всё названо в реестрах планов). Уровень ASVS 1, порог блокировки `high`: сверка мер — по коду и тестам на уровне grep, аудитор не порождался (короткий путь `/gsd-secure-phase`: `threats_open: 0`, реестр плановый, ASVS 1). `T-19-SC` повторяется во всех восьми планах как одна и та же угроза и записан один раз. Номера `T-19-19…T-19-23` и `T-19-27` распределены между планами 19-06 и 19-07 не по порядку (ревизия 1 перенесла сторону опросчика из T-19-22 в T-19-27); пропусков нет — 27 номерных угроз плюс `T-19-SC`.

Область кода — коммиты фазы `d7c4eba1…8f48e56a` (21 файл вне `.planning/`), включая коммиты оркестратора после планов: `85174888` / `8f48e56a` (воркер MAX передаёт `url="wss://api.oneme.ru/websocket"` — константа `MAX_WEBSOCKET_URL`, `max_worker/main.py:72,465`; адрес TLS, новых данных через границу не несёт) и `e9364641` (разрешение конфликтов слияния, тестовая правка журнала). Проверки плана 19-01 через `inspect.getsource` (`_save_tg_account`: один коммит после писателя; `complete_auth`: нет `await` между `_owned(` и `_qr_sessions.pop(`) выполнены и проходят. Набор тестов-улик (14 файлов, перечислены в столбце Mitigation) прогнан на `cb33e9f1`: 1378 passed.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Telegram → приложение | `User` из ответа входа Telethon (`qr_login.wait()`, `sign_in`) — внешние данные; поле `phone` недоверенное | номер собственного пользователя |
| состояние мастера TG → запись аккаунта | номер едет только с состоянием владельца (`_owned`, D-04 Фазы 13) тем же `pop`, что строка сессии | строка сессии, номер |
| сервер WhatsApp → `creds.me` / `sock.user` | `jid` от сервера — PN, LID, суффиксы устройства | JID аккаунта |
| сервер MAX → `client.me` | профиль из ответа `LOGIN` | `contact.phone` |
| воркер WA/MAX → приложение (`/status`) | тело ответа — недоверенный JSON (старый образ, мусор); приложение нормализует заново | поле `phone` |
| браузер → `POST /accounts/connect/max/start` | поле `phone` — свободный текст недоверенного клиента | номер формы |
| старт подключения MAX → строка `connecting` | номер формы хранится как запас в `credentials` (E.164), колонку номера старт не пишет | номер формы |
| опросчик → единственный писатель Фазы 16 | запись только условным оператором `phone IS NULL AND phone_is_manual IS false` | `account_id`, номер |
| приложение / воркеры → журнал, `repr` | номер — персональные данные (PHONE-21); маска приложения на контейнеры воркеров не распространяется | только `account_id`, `outcome`, `error_type` |
| репозиторий → образы воркеров на бою | код воркера доезжает до боя только пересборкой образа; рецепты исполняет владелец | образ WA |
| исполнитель → боевой стенд / запись обхода | исполнитель только читает; отметки обхода — слова владельца | улики обхода |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-19-01 | Information Disclosure (номер в журнале) | `_save_tg_account`, `telegram_user.py` | high | mitigate | журнал `tg_phone_captured` — только `account_id`, `outcome` (`app/pages/accounts.py:335`); `tests/test_routes/test_tg_user_auth.py::test_the_capture_log_carries_no_number`; гейт `tests/test_phone_privacy_gate.py` | closed |
| T-19-02 | Information Disclosure (номер в `repr` датакласса) | `QRAuthState`, `QrAuthResult` | medium | mitigate | `field(repr=False)` у `QRAuthState.own_phone` и `QrAuthResult.phone` (`app/messengers/telegram_user.py:45,59`); `tests/test_messengers/test_telegram_user.py::test_the_number_stays_out_of_the_state_and_result_repr` | closed |
| T-19-03 | Spoofing / Tampering (номер чужой сессии; двойная запись при гонке) | `complete_auth` | high | mitigate | `_owned` → `_qr_sessions.pop` без `await`; `QrAuthResult(session_string, own_phone)` собирается до первого `await` (`telegram_user.py`, `complete_auth`); проверка `inspect.getsource` плана проходит; правила гонки на настоящем `complete_auth` (фикстура `race_client`, `tests/test_routes/test_tg_user_auth.py`) зелены | closed |
| T-19-04 | Tampering (запись колонки номера мимо писателя; CR-09, WR-40, IN-29 Фазы 16) | `_save_tg_account` | high | mitigate | только `record_reported_phone` (`app/pages/accounts.py:333`), колонку не пишет никто иной; гейты `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_application/test_phone_writer_runtime_guard.py` зелены | closed |
| T-19-05 | Denial of Service (мусорный `User.phone` ломает подключение) | `reported_phone_of`, писатель | medium | mitigate | `reported_phone_of` тотальна (`try/except` вокруг `getattr`, только непустая строка; `telegram_user.py:62`); писатель отвечает `UNPARSEABLE` без базы; `test_an_unparseable_phone_still_connects_the_account` | closed |
| T-19-06 | Tampering (цифры LID записаны как номер) | `ownPhoneFromMe` | high | mitigate | только `isPnUser(id)` + `jidDecode(id).user`, результат `^[0-9]+$`, иначе `null`; разбиения строки JID нет (`wa_worker/own_phone.js`); `tests/test_worker/test_wa_worker_own_phone.py` (входы D-03, LID → `null`) | closed |
| T-19-07 | Information Disclosure (номер в журнале воркера WA) | `wa_worker/index.js`, `own_phone.js` | high | mitigate | значение уходит только в тело ответа `/status` (`index.js:764`), модуль ничего не импортирует и не пишет в консоль; JS-половина `tests/test_phone_privacy_gate.py` судит `sock.user` / `creds.me`; тест «ноль вызовов консоли» в `test_wa_worker_own_phone.py`; `BAILEYS_LOG_LEVEL` по умолчанию `warn` (`index.js:49`) не поднят | closed |
| T-19-08 | Denial of Service (исключение разбора роняет `/status`) | обработчик `/status` WA | medium | mitigate | `ownPhoneFromMe` в `try/catch` → `null`, никогда не бросает; тест мусорных входов в `test_wa_worker_own_phone.py` | closed |
| T-19-09 | Spoofing (номер формы выдан за номер, сообщённый MAX) | `get_session_status` | high | mitigate | `/status` отдаёт только `session.own_phone` из `client.me` (`max_worker/main.py:1043`); `self.phone` (номер формы) не отдаётся; `tests/test_worker/test_max_worker.py::test_the_form_number_never_leaks_into_the_status_answer` | closed |
| T-19-10 | Information Disclosure (номер в журнале воркера MAX) | `on_start`, `own_phone_of` | high | mitigate | журнал отказа `own_phone_capture_failed` — `account_id` и тип исключения (`max_worker/main.py:493`); гейт `tests/test_phone_privacy_gate.py` судит `max_worker/`; `test_the_capture_writes_no_number_to_the_log` | closed |
| T-19-11 | Denial of Service (исключение захвата оставляет воркер «инициализирующимся») | `on_start` | medium | mitigate | захват первым в `try/except` до `is_connected = True` (`max_worker/main.py:487-498`); `own_phone_of` сам тотален; `test_a_failing_capture_does_not_break_the_connection` | closed |
| T-19-12 | Tampering / Integrity (на бою старый образ WA) | `prod-deploy`, `prod-hard-deploy`, `prod-build` | medium | mitigate | `just wa-worker-build` во всех трёх рецептах до первой остановки контейнеров (`justfile:108,121,134`); тег `broadcaster-wa-worker:latest` = `WA_WORKER_IMAGE` (`app/services/wa_container_manager.py:13`); `tests/test_wa_worker_deployment.py`. Живая проверка 1 обхода 19-08 в `19-UAT.md` ещё `pending` — на статус меры не влияет | closed |
| T-19-13 | Denial of Service (сборка после остановки; неверный аргумент роняет деплой) | порядок шагов рецептов | low | mitigate | правило порядка в `tests/test_wa_worker_deployment.py`; `wa-worker-build *args`; `just --dry-run prod-deploy` разворачивается: сборка WA раньше `docker stop` | closed |
| T-19-14 | Tampering (подменённое тело `/status` пишет мусор) | `reported_phone_from_status`, писатель | medium | mitigate | принимается только `dict` → непустая строка или `int > 0` (`bool` отвергнут) (`app/messengers/base.py:16`); писатель нормализует `normalize_reported`, мусор → `UNPARSEABLE`; параметризованные тесты в `tests/test_messengers/test_whatsapp.py`, `test_max.py` | closed |
| T-19-15 | Denial of Service (сбой захвата оставляет `connecting`) | `accounts_connect_wa_status` | high | mitigate | `capture_connect_phone` — сейвпоинт `begin_nested` + `except Exception` → `None` (`app/application/accounts/connect_phone.py`); `account_id` снят до захвата (`accounts.py:773`); `tests/test_pages/test_connect_phone_capture.py::test_a_failing_capture_still_connects_the_account` | closed |
| T-19-16 | Tampering (пустое или чужое значение поверх известного номера) | `fill_reported_phone`, помощник | high | mitigate | UPDATE писателя с `phone IS NULL AND phone_is_manual IS false` (`app/application/accounts/phone.py:128-134`); запасной пробуется только при `UNPARSEABLE` (`connect_phone.py`); тесты `KEPT` в `tests/test_application/test_connect_phone.py`; `test_connect_phone_capture.py::test_an_empty_or_other_report_never_overwrites_a_known_number` | closed |
| T-19-17 | Information Disclosure (номер в журнале приложения) | `connect_phone.py`, `whatsapp.py`, `accounts.py` | high | mitigate | `connect_phone_captured` / `connect_phone_capture_failed` — `account_id`, `outcome` / `error_type`; адаптеры — `get_own_phone_failed` только `error_type` (`whatsapp.py:162`, `max.py:153`); гейт `tests/test_phone_privacy_gate.py`; тест журнала в `test_connect_phone.py` | closed |
| T-19-18 | Elevation of Privilege / IDOR (номер записан чужому аккаунту) | выборка строки `connecting` | medium | mitigate | выборка обработчиков статуса не менялась: `MessengerAccount.user_id == user.id` (`accounts.py:752` WA, `:1018` MAX); `account_id` берётся из этой строки | closed |
| T-19-19 | Tampering / Information Disclosure (XSS через эхо 422 формы MAX) | `max_connect_step.html`, `field` | high | mitigate | эхо только автоэкранированием макроса `field`; в шаблоне `|safe` — 0 вхождений; текст ошибки — `str(PhoneError)` из констант (`accounts.py:930-932`); `tests/test_pages/test_max_connect_transport.py::test_a_hostile_phone_never_reaches_the_response_raw` (HTTP-путь) | closed |
| T-19-20 | Spoofing (номер формы A выдан за номер аккаунта, хотя MAX сообщил B; помечен ручным) | `capture_connect_phone`, `accounts_connect_max_status` | high | mitigate | сообщённый номер первым, запасной `entered_phone` только при `UNPARSEABLE`; запись `fill_reported_phone` без признака ручного (`connect_phone.py`, `accounts.py:1043-1045`); `test_entered_a_scanned_b_shows_b`. Живой замер W-1 в `19-UAT.md` `blocked` (внешний переезд сервера MAX) — на статус меры не влияет | closed |
| T-19-21 | Denial of Service (сбой захвата или старый образ оставляют `connecting`) | `accounts_connect_max_status` | high | mitigate | та же обёртка с сейвпоинтом 19-05; `test_an_old_max_worker_status_connects_with_the_form_number`, `test_a_failing_max_capture_still_connects_the_account` | closed |
| T-19-22 | Information Disclosure (номер формы в журнале или в тексте ошибки) | `accounts_connect_max_start` | high | mitigate | ввод в текст ошибки не подставляется (текст — `PhoneError`), `credentials` в журнал не идут; отрицательный контроль в `test_max_connect_transport.py`; гейт `tests/test_phone_privacy_gate.py`; сторона опросчика — T-19-27 | closed |
| T-19-23 | Denial of Service (длинный ввод в нормализатор) | `normalize_manual` | low | accept | см. AR-19-01; предел `MANUAL_INPUT_MAX_CHARS = 32` проверяется до разбора (`app/services/phone.py:153,325`) — на месте | closed |
| T-19-24 | Repudiation (машинная улика выдана за приёмку; голый «pass») | `19-UAT.md` | medium | mitigate | раздел `## Машинная улика обхода` отделён; `status: testing`; `result: pass` только у проверки 4 со словами владельца о наблюдённом; `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` зелён | closed |
| T-19-25 | Tampering (исполнитель меняет боевые данные или выкатывает без владельца) | стенд | high | mitigate | выкат — `checkpoint:human-action` владельца («пересобрал оба образа»); исполнитель записи в базу и выката не выполнял (`19-08-SUMMARY.md` § Threat Flags); запреты `must_haves.prohibitions` плана 19-08 | closed |
| T-19-26 | Information Disclosure (номера владельца в записи обхода) | `19-UAT.md` | low | accept | см. AR-19-02 | closed |
| T-19-27 | Information Disclosure (номер в журнале опросчика или адаптера MAX) | `accounts_connect_max_status`, `MaxMessenger.get_own_phone` | high | mitigate | адаптер журналирует только `error_type`, без `str(exc)` (`app/messengers/max.py:153`); помощник — `account_id`, `outcome`, `error_type`; `credentials` в журнал не идут; гейт `tests/test_phone_privacy_gate.py`; `test_a_failing_max_capture_still_connects_the_account` (в журнале нет `9991234567`) | closed |
| T-19-SC | Tampering | npm/pip/cargo installs | high | mitigate | установок нет: `git diff d7c4eba1~1..HEAD` по `pyproject.toml`, `uv.lock`, `wa_worker/package*.json`, `max_worker/requirements*.txt` пуст; пины Baileys 7.0.0-rc14 и `maxapi-python==2.3.1` не менялись (обновление PyMax 2.5.0 — отдельный todo `max-worker-pymax-2-5-0-upgrade`, вне фазы) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-19-01 | T-19-23 | предел `MANUAL_INPUT_MAX_CHARS = 32` отсекает длинный ввод до разбора; ответ 422 — автоэкранированное эхо без повторной обработки | план 19-06 (решение фазы, диспозиция `accept` реестра плана) | 2026-11-23 |
| AR-19-02 | T-19-26 | номера — собственные номера владельца в его репозитории; маскирование на экранах самого пользователя вне области (REQUIREMENTS Out of Scope). Наблюдение аудита: оговорка плана «в улику пишутся признаки, а не цифры» соблюдена не полностью — `19-UAT.md` содержит два номера владельца (номер A формы MAX и номер WA в цитате владельца, строки 30, 41, 86, 187). Риск остаётся в границах принятого (номера владельца, запись владельца); вычистить цифры — решение владельца | план 19-08 (решение фазы, диспозиция `accept` реестра плана) | 2026-11-23 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-23 | 28 | 28 | 0 | `/gsd-secure-phase 19` (подагент оркестратора `/gsd-execute-phase 19`, шаг verify:post; L1 grep + 14 файлов тестов-улик, 1378 passed на `cb33e9f1`; аудитор не порождался — короткий путь ASVS 1) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-23

## Security Audit 2026-11-24

| Metric | Count |
|---|---|
| Threats found | 28 |
| Closed | 28 |
| Open | 0 |

Перепроверка перед раундом 3 верификации (`/gsd-execute-phase 19`, вердикт `stale`: после раунда 2 фаза 20 дописала в `justfile` рецепты `backfill-phones` и `prod-backfill-phones`). Проводил оркестратор, без аудитора: сработало правило короткого пути `secure-phase` — `threats_open: 0`, реестр составлен при планировании (8 из 8 планов несут `<threat_model>`; все 27 номерных угроз и `T-19-SC` есть в реестре), `asvs_level: 1`. Реестр не менялся, ни одна строка не сменила статус. Это замер дерева `f7cefff4`. Вне `.planning/` оно совпадает с `eeb44eed`, где полная суита дала 6298 passed, 2 skipped, 0 failed (`.pytest_cache/gsd-orch/suite-p18r.log`).

- **T-19-09…T-19-11 (`max_worker/main.py`).** После аудита файл правила быстрая задача 261123-bgc (`7153c9fb`, переход на PyMax 2.5.0). Она сняла три прослойки совместимости (`contact`/`sticker`-вложения, загрузка фото) и обновила комментарии. Код мер фазы не тронут, номера строк сдвинулись на 11: `/status` отдаёт `session.own_phone` (`max_worker/main.py:1032`); журнал отказа — `own_phone_capture_failed account_id=%s error_type=%s` (`:482`); захват стоит первым в `try/except` до `state.is_connected = True` (`:476–486`). Тесты-улики `test_the_form_number_never_leaks_into_the_status_answer`, `test_the_capture_writes_no_number_to_the_log` (3 случая) и `test_a_failing_capture_does_not_break_the_connection` (2 случая) — PASSED в суите на `eeb44eed`. Ссылки на строки в реестре — снимок аудита 2026-11-23, а не обещание.
- **T-19-12, T-19-13 (`justfile`).** Фаза 20 (`b5ba2c6b`) дописала два рецепта ниже деплойных. Строки `just wa-worker-build` в `prod-hard-deploy`, `prod-deploy` и `prod-build` прежние (`justfile:108,121,134`). `tests/test_wa_worker_deployment.py` и `tests/test_max_worker_deployment.py` — 9 из 9 на дереве с новыми рецептами.
- **T-19-SC (строка «npm/pip/cargo installs»).** Улика `git diff d7c4eba1~1..HEAD` по манифестам — снимок на момент аудита 2026-11-23. Сегодня тот же диапазон показывает ещё `7153c9fb` (быстрая задача 261123-bgc): `maxapi-python` 2.3.1 → 2.5.0 в `max_worker/requirements.txt`, в dev-группе `pyproject.toml` и в строках `maxapi-python` файла `uv.lock` (specifier, version, sdist, wheel). Это и есть отдельный todo `max-worker-pymax-2-5-0-upgrade`, названный в строке. Он выполнен вне фазы, быстрой задачей. Угроза фазы — подмена пакета, поставленного её планами, — закрыта прежней мерой: планы фазы ничего не ставили. Легитимность пакета 2.5.0 относится к быстрой задаче, а не к этому реестру.
- **T-19-24 (`19-UAT.md`).** Мера держится: раздел `## Машинная улика обхода` отделён от отметок, `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` зелёный (`tests/test_planning` на `f7cefff4`: 218 passed, 2 skipped). Слова строки «`status: testing`; `result: pass` только у проверки 4» — снимок аудита. Сейчас запись завершена `/gsd-verify-work 19` (`9f226ee8`): `status: complete`, 5 из 5 `result: pass`, отметки словами владельца.
- **T-19-26 / AR-19-02 (наблюдение, не новая угроза).** После завершения обхода (`9f226ee8`) в `19-UAT.md` по-прежнему два номера владельца, но уже в 16 строках вместо четырёх, названных в AR-19-02. Риск в границах принятого: номера владельца, запись владельца. Вычистить цифры — решение владельца. Сами номера в этот реестр не выписаны.
