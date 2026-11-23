---
phase: 19-zahvat-nomera-pri-podklyuchenii
verified: 2026-11-23T09:00:00Z
status: human_needed
score: 4/5 must-haves verified
covered_files:
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-01-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-01-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-02-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-02-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-03-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-03-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-04-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-04-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-05-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-05-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-06-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-06-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-07-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-07-SUMMARY.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-08-PLAN.md
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-08-SUMMARY.md
  - app/application/accounts/connect_phone.py
  - app/messengers/base.py
  - app/messengers/max.py
  - app/messengers/telegram_user.py
  - app/messengers/whatsapp.py
  - app/pages/accounts.py
  - app/templates/accounts/includes/max_connect_step.html
  - justfile
  - max_worker/main.py
  - wa_worker/index.js
  - wa_worker/own_phone.js
covered_digest: "v4:sha256:36c00282be60261208582350cf6f8181a4a95966e7508d7139a3d4e662acb11b"
behavior_unverified: 1
overrides_applied: 0
behavior_unverified_items:
  - truth: "Критерий 3: новый аккаунт MAX показывает номер из мессенджера, а если мессенджер номер не отдал — номер из формы без пометки «указан вручную» (на живом аккаунте)"
    test: "Владелец проходит мастер MAX на бою после восстановления связи и перехода воркера на PyMax >= 2.5.0: W-1 (в форме номер A, сканирует аккаунт B) и W-2 (в форме номер сканирующего аккаунта)"
    expected: "В списке аккаунтов у нового аккаунта показан B (MAX отдал contact.phone) либо A (запас D-10); пометки «указан вручную» нет; шаг «Подключено» номера не показывает"
    why_human: "Код и тесты (тестовые двойники воркера) доказывают порядок «сообщённый, затем запасной», но вопрос разведки A3 — отдаёт ли MAX contact.phone при QR-входе у PyMax 2.5.0 — не измерен: QR MAX не открывается со стенда (внешняя смена сервера MAX), поэтому на живом аккаунте поведение не наблюдалось"
human_verification:
  - test: "W-1 (MAX): в форму ввести номер A, отсканировать QR аккаунтом с номером B"
    expected: "В списке аккаунтов показан B либо A (оба исхода верны по D-10); пометки «указан вручную» нет; исход записать как ответ на вопрос A3"
    why_human: "БЛОКИРОВАНО ВНЕШНЕЙ ПРИЧИНОЙ. MAX перенёс websocket-сервер (ws-api.oneme.ru -> api.oneme.ru) с изменением протокола; PyMax 2.3.1 не подключается даже с новым URL (закрытие 1000 после рукопожатия), PyMax 2.5.0 получает QR. Затрагивает все аккаунты MAX с 2026-11-22T02:11Z. Разблокировка: todo .planning/todos/pending/max-worker-pymax-2-5-0-upgrade.md. Коммиты 85174888/8f48e56a (ExtraConfig url=api.oneme.ru) нужны, но недостаточны. Проверка 19-UAT №2 имеет result: blocked, blocked_by: server"
  - test: "W-2 (MAX): в форму ввести номер того же аккаунта, которым сканируют"
    expected: "В списке показан этот номер без «указан вручную»"
    why_human: "Та же внешняя блокировка (19-UAT №3, blocked_by: server)"
  - test: "W-4: ни в одном мастере и ни у одного нового аккаунта нет «указан вручную»; шаг «Подключено» без номера"
    expected: "Для WA — подтверждено словами владельца («пометок нет»), шага «Подключено» WA владелец не описывал; для MAX — не пройдено"
    why_human: "19-UAT №5 без отметки: половина MAX ждёт восстановления связи; слов владельца о шаге «Подключено» нет"
  - test: "Check 1 (19-UAT №1): образы воркеров на бою пересобраны, контейнеры подняты на :latest"
    expected: "Наблюдение владельца об образах (WA c3b44c91…, MAX 592b2e00… пересобраны 2026-11-23T06:19Z, ревизия MAX = HEAD того момента)"
    why_human: "Машинная улика есть (19-UAT, раздел «Машинная улика»), но отметка владельца пуста (result: [pending]); машинная улика приёмкой не считается"
gaps: []
---

# Phase 19: Захват номера при подключении — отчёт верификации

**Цель фазы:** новый аккаунт любого из трёх мессенджеров получает номер в момент подключения, и пользователь видит его в списке, ничего не вводя
**Проверено:** 2026-11-23T09:00:00Z
**Статус:** human_needed
**Повторная верификация:** нет — первичная

## Достижение цели

Код на ветке реализует захват номера для всех трёх мессенджеров, и всё, что можно проверить без живого MAX, проверено по коду и тестам. Цель не достигнута только в одном месте, где проверка невозможна: на живом MAX она заблокирована внешним отказом (смена сервера MAX), а не дефектом фазы. Поэтому статус — `human_needed`, а не `passed`; блокирующих расхождений (`gaps`) нет.

### Наблюдаемые истины (критерии успеха ROADMAP)

| # | Истина | Статус | Доказательство |
|---|--------|--------|----------------|
| 1 | Telegram по QR и по 2FA: аккаунт сразу показывает номер из ответа входа, второго подключения к Telegram нет | ✓ VERIFIED | `app/messengers/telegram_user.py`: `_wait_for_qr` берёт `user = await qr_login.wait()` и ставит `state.own_phone = reported_phone_of(user)` раньше `status="success"`; `submit_2fa` берёт `user = await sign_in(password=)`; `complete_auth` отдаёт `QrAuthResult(session_string, phone)` из того же `pop`. `_save_tg_account` пишет `record_reported_phone` и `status="active"` одним коммитом. Тесты `test_a_qr_scan_gives_the_new_account_its_number_without_a_second_connection` (`get_me.assert_not_called()`, строка 548) и `test_a_right_password_gives_the_new_account_its_number` (строка 603); гонки `complete_auth` зелёны; `repr=False` у номера |
| 2 | WhatsApp: номер показан; LID не превращается в цифры; юнит на четырёх входах; на живом аккаунте — обход | ✓ VERIFIED | `wa_worker/own_phone.js` (`ownPhoneFromMe`: `isPnUser` + `jidDecode().user`, LID/пусто -> `null`, без `split(':')`, без журнала); `index.js` вводит `isPnUser`/`jidDecode` и отдаёт `phone` в `/status`. `test_the_own_number_is_taken_only_from_a_pn_jid` гоняет настоящий node на четырёх входах D-03 (PN с устройством, PN без, LID, пусто); `test_a_lid_only_session_leaves_the_number_unknown`. Живой обход W-3: владелец словами — «мой номер +79284335314, он был присвоен аккаунту, все правильно сработало, пометок нет, группы синхронизировались» (19-UAT №4, result: pass) |
| 3 | MAX: номер из мессенджера; иначе номер формы без «указан вручную»; «ввёл A, отсканировал B -> B» (тест); на живом аккаунте — обход | ? UNCERTAIN (код и тесты зелёные; живая часть заблокирована внешней причиной) | Код: `max_worker/main.py` (`own_phone_of`, захват в `on_start` в `try/except` до `is_connected`, `phone` в `/status`); `MaxMessenger.get_own_phone`; `accounts_connect_max_status` читает `entered_phone = account.credentials` до перезаписи и зовёт `capture_connect_phone(db, id, reported, entered)`; форма — `normalize_manual` + 422 `PhoneError`. Тесты `test_entered_a_scanned_b_shows_b`, `test_max_without_a_reported_number_shows_the_form_number_without_the_manual_mark`, `test_a_known_max_number_survives_both_sources` зелёны. Живое поведение не измерено: вопрос A3 без ответа (см. Проверку людьми) |
| 4 | Воркер старого образа (нет `phone` в `/status`) подключает аккаунт как раньше; пустое не пишется поверх известного | ✓ VERIFIED | `reported_phone_from_status` тотальна (не dict, нет поля, bool, мусор -> `None`); `get_own_phone` глотает любой отказ, в журнал только `error_type`. Тесты `test_an_old_worker_status_connects_the_wa_account_with_an_unknown_number`, `test_an_old_max_worker_status_connects_with_the_form_number`, `test_a_failing_capture_still_connects_the_account` (WA и MAX), `test_an_empty_or_other_report_never_overwrites_a_known_number`; писатель пишет только в `phone IS NULL AND NOT phone_is_manual` |
| 5 | `just prod-deploy` и `just prod-hard-deploy` пересобирают оба образа (WA и MAX) | ✓ VERIFIED | `just --dry-run prod-deploy` печатает `just max-worker-build && just wa-worker-build`, до остановки контейнеров; `prod-hard-deploy` — `just max-worker-build --no-cache && just wa-worker-build --no-cache`; `wa-worker-build *args`; `prod-build` тоже. Тесты `tests/test_wa_worker_deployment.py` (4) зелёные |

**Счёт:** 4/5 истин подтверждено; 1 (критерий 3) — код и тесты подтверждены, живая часть ждёт человека и внешнего восстановления связи.

### Артефакты

| Артефакт | Ожидание | Статус | Детали |
|----------|----------|--------|--------|
| `app/application/accounts/connect_phone.py` | помощник захвата WA/MAX с сейвпоинтом, источник «сообщённый -> запасной» | ✓ VERIFIED | 56 строк, подключён в двух опросчиках, пишет только `fill_reported_phone`, журнал без значения |
| `app/messengers/telegram_user.py` | `QrAuthResult`, `reported_phone_of`, `own_phone` | ✓ VERIFIED | подключён в `_wait_for_qr`, `submit_2fa`, `complete_auth`; инвариант «нет `await` между проверкой и `pop`» сохранён |
| `app/messengers/base.py`, `whatsapp.py`, `max.py` | `reported_phone_from_status`, `get_own_phone` | ✓ VERIFIED | вызываются обработчиками статуса; тотальны |
| `app/pages/accounts.py` | `_save_tg_account`, опросчики WA/MAX, форма MAX | ✓ VERIFIED | данные текут от воркера до колонки через писателя (Level 4: FLOWING) |
| `app/templates/accounts/includes/max_connect_step.html` | подсказка под полем номера | ✓ VERIFIED | `hint=` без значения номера |
| `wa_worker/own_phone.js`, `wa_worker/index.js` | разбор `creds.me.id`, поле `phone` | ✓ VERIFIED | модуль без импортов, подключён |
| `max_worker/main.py` | `own_phone_of`, `on_start`, `/status.phone`, `MAX_WEBSOCKET_URL` | ✓ VERIFIED | `own_phone` ставится до `is_connected`; номер формы воркер не отдаёт |
| `justfile` | пересборка образа WA в деплое | ✓ VERIFIED | см. истину 5 |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус |
|--------|------|-------|--------|
| `qr_login.wait()` / `sign_in()` | колонка `phone` | `own_phone` -> `QrAuthResult` -> `record_reported_phone` | WIRED |
| `/status` воркера WA/MAX | колонка `phone` | `get_own_phone` -> `capture_connect_phone` -> `fill_reported_phone` | WIRED |
| форма MAX | запас D-10 | `normalize_manual` -> `credentials` (E.164) -> `entered_phone` | WIRED |
| `wa_worker/index.js` | образ на бою | `wa-worker-build` в `prod-deploy`/`prod-hard-deploy` | WIRED |
| колонка `phone` | список аккаунтов | помощник подписи Фазы 17 (тест листинга) | WIRED |

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Тесты фазы (10 файлов) | `uv run pytest tests/test_application/test_connect_phone.py tests/test_pages/test_connect_phone_capture.py tests/test_pages/test_max_connect_transport.py tests/test_messengers/{test_telegram_user,test_max,test_whatsapp}.py tests/test_routes/test_tg_user_auth.py tests/test_wa_worker_deployment.py tests/test_worker/{test_max_worker,test_wa_worker_own_phone}.py -q -p no:randomly` | 278 passed, 0 skipped | ✓ PASS |
| Полный набор (замер оркестратора, не мой) | `uv run pytest tests/ -q -p no:randomly` на 53653a05 | 6143 passed, 2 skipped, TEST_EXIT=0 | принято как улика оркестратора |
| Деплой-рецепты | `just --dry-run prod-deploy` / `prod-hard-deploy` | оба образа, hard — `--no-cache` | ✓ PASS |

### Выполнение проб

Проб `probe-*.sh` фаза не объявляет — шаг пропущен.

### Покрытие требований

| Требование | План | Описание | Статус | Доказательство |
|------------|------|----------|--------|----------------|
| PHONE-12 | 19-01 | TG: номер при подключении, QR и 2FA, без второго подключения | ✓ SATISFIED | истина 1 |
| PHONE-13 | 19-02, 19-05, 19-08 | WA: номер при подключении; LID не принимается | ✓ SATISFIED | истина 2; живой обход пройден словами владельца |
| PHONE-14 | 19-03, 19-06, 19-07, 19-08 | MAX: номер при подключении, запас — номер формы как автоматический | ? NEEDS HUMAN | код и тесты есть; живой MAX заблокирован внешним отказом, вопрос A3 открыт |
| PHONE-15 | 19-02, 19-03, 19-05, 19-07 | воркер старого образа не ломает подключение | ✓ SATISFIED | истина 4 |
| PHONE-16 | 19-04, 19-08 | `prod-deploy`/`prod-hard-deploy` пересобирают оба образа | ✓ SATISFIED | истина 5 |

Все пять ID из REQUIREMENTS.md заявлены хотя бы одним планом; осиротевших требований нет. Требования Complete не отмечаются (по указанию оркестратора).

### Антипаттерны

| Файл | Строка | Образец | Серьёзность | Влияние |
|------|--------|---------|-------------|---------|
| — | — | `TBD/FIXME/XXX/TODO/HACK` в добавленных строках кода | — | не найдено |

### Предупреждения (WARNING)

**WR-01 (из 19-REVIEW.md, диспозиция `open`) — оценка против D-05: WARNING, не BLOCKER.**
`_save_tg_account` вызывает `record_reported_phone` без сейвпоинта, тогда как WA/MAX идут через `capture_connect_phone`. D-05 говорит «сбой захвата (исключение, мусор) обёрнут так, чтобы вход не ломался»; на пути TG исключение базы из писателя не проглатывается. Расхождение реально, но узкое. Объявленная в плане 19-01 истина D-05 — тотальность `reported_phone_of` (мусор, `None`, не-строка, исключение источника -> номер неизвестен, аккаунт создаётся) — выполнена и покрыта тестами; плановое решение «без сейвпоинта» задокументировано и обосновано (громкий `ValueError(ACCOUNT_NOT_IN_SESSION)` обязан остаться громким). Достижимых сбоев UPDATE, кроме инфраструктурных (потеря соединения, взаимоблокировка), нет: `phone`-CHECK касается только `phone_is_manual AND phone IS NULL`, E.164 вмещается в `String(16)`, `phone_guard` открыт `writer_scope()`; инфраструктурный сбой всё равно уронил бы и коммит. Практическая цена — при таком сбое теряется уже израсходованная сессия Telegram (повторное сканирование). Рекомендация: закрыть ревизией — сейвпоинт с `except ValueError: raise` (эскиз в 19-REVIEW.md) или `capture_connect_phone` после `flush()`; решение владельца. IN-01…IN-03 — информационные, цель не затрагивают (IN-01: `QrAuthResult.session_string` попадает в `repr`; IN-02: дубль `get_own_phone`; IN-03: введённый номер MAX не самоисправляется — решение владельца OQ1).

**Внешний риск живого MAX.** Воркер MAX закреплён на PyMax 2.3.1, а коммиты оркестратора `85174888`/`8f48e56a` (url `api.oneme.ru`) недостаточны: 2.3.1 закрывается с кодом 1000 после рукопожатия. Пока нет перехода на PyMax 2.5.0 (todo `max-worker-pymax-2-5-0-upgrade.md`), подключение MAX не работает вовсе, и ни захват номера, ни запас формы на живом аккаунте проверить нельзя. Чтение `client.me.contact.phone` написано под 2.3.1; совместимость с 2.5.0 не проверена.

### Проверка людьми

1. **W-1 (MAX, ввёл A, отсканировал B)** — ожидается B либо A, без «указан вручную»; исход записать как ответ на вопрос A3. Блокировано: смена сервера MAX, нужен PyMax 2.5.0.
2. **W-2 (MAX, форма с номером сканирующего аккаунта)** — ожидается этот номер без пометки. Блокировано той же причиной.
3. **W-4 (нигде нет «указан вручную», шаг «Подключено» без номера)** — для WA владелец сказал «пометок нет», слов о шаге «Подключено» нет; для MAX не пройдено.
4. **Проверка 1 (образы воркеров на бою)** — машинная улика есть, слов владельца нет.

### Итог

Расхождений, требующих плана закрытия, нет: ни одна истина не FAILED. Фаза остаётся без статуса `passed`, пока владелец не отметит проверки 1, 2, 3, 5 в 19-UAT.md; MAX-часть критерия 3 (PHONE-14) разблокируется переходом воркера на PyMax 2.5.0.

---

_Проверено: 2026-11-23T09:00:00Z_
_Верификатор: Claude (gsd-verifier)_
