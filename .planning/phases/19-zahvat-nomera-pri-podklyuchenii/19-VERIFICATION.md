---
phase: 19-zahvat-nomera-pri-podklyuchenii
verified: 2026-11-23T11:00:00Z
status: passed
score: 5/5 must-haves verified
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
  - .planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-UAT.md
  - app/application/accounts/connect_phone.py
  - app/messengers/base.py
  - app/messengers/max.py
  - app/messengers/telegram_user.py
  - app/messengers/whatsapp.py
  - app/pages/accounts.py
  - app/templates/accounts/includes/max_connect_step.html
  - justfile
  - max_worker/main.py
  - max_worker/pymax_compat.py
  - max_worker/requirements.txt
  - wa_worker/index.js
  - wa_worker/own_phone.js
covered_digest: "v4:sha256:1e35cefaca3ce1f353a0c689623e3d6f6445a3c6b585d9922e8ffcaa030497e5"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 4/5
  previous_verified: 2026-11-23T09:00:00Z
  reason: "отчёт устарел: после него изменён покрываемый файл max_worker/main.py (quick 261123-bgc, переход MAX-воркера на PyMax 2.5.0: d2588e0a, 7153c9fb, e0ce7d32); затем владелец прошёл обход на бою (19-UAT.md, commit 9f226ee8, 5/5)"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  human_items_closed:
    - item: "W-1 (MAX): в форму номер A, сканирует аккаунт B (human_verification №1 и behavior_unverified_items — критерий 3)"
      disposition: "закрыто наблюдением владельца: 19-UAT №2, result: pass — «сканировал +79284335314, у MAX #88 этот номер, пометок нет»; в форме A = +79181976661, в списке показан B = +7 928 433-53-14. Исход B: MAX отдаёт contact.phone при QR-входе у PyMax 2.5.0 (ответ на вопрос разведки A3)"
      evidence: ".planning/phases/19-zahvat-nomera-pri-podklyuchenii/19-UAT.md (раздел «Проверка 2», «Машинная улика обхода» — возобновление 09:55Z)"
    - item: "W-2 (MAX): в форму номер сканирующего аккаунта (human_verification №2)"
      disposition: "закрыто наблюдением владельца: 19-UAT №3, result: pass — «у MAX этот номер +79284335314, пометок нет» (аккаунт #89)"
      evidence: "19-UAT.md, раздел «Проверка 3»"
    - item: "W-4: нигде нет «указан вручную», шаг «Подключено» без номера (human_verification №3)"
      disposition: "закрыто словами владельца: 19-UAT №5, result: pass — «была надпись MAX подключён номера не было пометок тоже»; WA — «пометок нет» (проверка 4). Шаг «Подключено» WA владелец отдельно не описывал: его отсутствие номера снято машиной (19-UAT, перепроверка 06:29–06:31Z, «WhatsApp подключён!» без номера) и закреплено тестами шаблона — отмечено как информационное, не как пробел"
      evidence: "19-UAT.md, раздел «Проверка 5»"
    - item: "Проверка 1 (19-UAT №1): образы воркеров пересобраны, контейнеры на :latest (human_verification №4)"
      disposition: "закрыто словами владельца: 19-UAT №1, result: pass — «я пересобрал и поднял web-broadcaster и пересобрал broadcaster-wa-worker и broadcaster-max-worker»; машинный замер агента: max-worker-88/89 на e734363b… = broadcaster-max-worker:latest, ревизия d373515e, PyMax 2.5.0"
      evidence: "19-UAT.md, раздел «Проверка 1»"
  behavior_unverified_items_closed:
    - truth: "Критерий 3 (MAX: номер из мессенджера, иначе номер формы без пометки)"
      disposition: "поведение теперь наблюдено на живом аккаунте владельцем (W-1 и W-2 выше) и подтверждено тестами; в списке behavior_unverified_items больше нет"
  carried_warning:
    - id: "WR-01"
      status: "open (без изменений)"
      note: "19-REVIEW-DISPOSITION.md: WR-01 warning, open; в этом раунде не менялось, цель не блокирует"
gaps: []
---

# Phase 19: Захват номера при подключении — отчёт верификации

**Цель фазы:** новый аккаунт любого из трёх мессенджеров получает номер в момент подключения, и пользователь видит его в списке, ничего не вводя
**Проверено:** 2026-11-23T11:00:00Z
**Статус:** passed
**Повторная верификация:** да — после устаревания отчёта (правка `max_worker/main.py` переходом на PyMax 2.5.0) и после завершённого обхода владельца

## Достижение цели

Цель достигнута. Две причины повторной проверки сняты.

1. **Переход воркера MAX на PyMax 2.5.0 не сломал путь захвата номера.** Дифф `53653a05..HEAD` по `max_worker/main.py` затрагивает только импорты и вызовы совместимостей (`apply_*_compatibility`, кроме кадров websocket), комментарий к `url` и строку docstring в `own_phone_of` («pymax 2.3.1» -> «pymax 2.5.0»). Тело `own_phone_of`, захват в `on_start` (в `try/except` до `is_connected`, `state.own_phone = own_phone_of(connected_client)`), поле `phone` в `/status` (строка 1032) и `MAX_WEBSOCKET_URL` не менялись. Приложение (`app/`), `wa_worker/` и `justfile` с `53653a05` не менялись вовсе. Мои 10 файлов тестов фазы — 278 passed. Полный набор (замер оркестратора на HEAD `9f226ee8`): 6143 passed, 2 skipped, 0 failed.
2. **Владелец своими словами закрыл все живые проверки** (19-UAT.md, `status: complete`, 5/5, все таблицы «Отметка» заполнены его словами, не шаблоном). Главное: вопрос разведки A3 получил ответ — **MAX отдаёт номер при QR-входе у PyMax 2.5.0** (в форме A = +79181976661, отсканирован аккаунт B, в списке показан B = +7 928 433-53-14, пометки «указан вручную» нет). Это прямое наблюдение работы цепочки `client.me.contact.phone` -> `/status.phone` -> `capture_connect_phone` -> колонка `phone` -> подпись списка на PyMax 2.5.0.

### Наблюдаемые истины (критерии успеха ROADMAP)

| # | Истина | Статус | Доказательство |
|---|--------|--------|----------------|
| 1 | Telegram по QR и по 2FA: аккаунт сразу показывает номер из ответа входа, второго подключения к Telegram нет | ✓ VERIFIED | Без изменений с прошлого раунда: `app/messengers/telegram_user.py` (`_wait_for_qr`, `submit_2fa`, `complete_auth` -> `QrAuthResult`), `_save_tg_account` -> `record_reported_phone`. Файл с `53653a05` не менялся; `test_a_qr_scan_gives_the_new_account_its_number_without_a_second_connection`, `test_a_right_password_gives_the_new_account_its_number` в зелёных 278. Отдельной живой отметки по TG в UAT нет (TG и не входил в W-проверки плана 19-08) — истина держится на тестах и неизменном коде, как и в прошлом раунде |
| 2 | WhatsApp: номер показан; LID не превращается в цифры; юнит на четырёх входах; на живом аккаунте — обход | ✓ VERIFIED | `wa_worker/own_phone.js` + `index.js` без изменений; `test_the_own_number_is_taken_only_from_a_pn_jid` (настоящий node, 4 входа D-03), `test_a_lid_only_session_leaves_the_number_unknown`. Живой обход: 19-UAT №4, result: pass — «мой номер +79284335314, он был присвоем аккаунту все правильно сработало, пометок нет, группы синхронизировались» |
| 3 | MAX: номер из мессенджера; иначе номер формы без «указан вручную»; «ввёл A, отсканировал B -> B»; на живом аккаунте — обход | ✓ VERIFIED (было: UNCERTAIN) | Код: `own_phone_of`/`on_start`/`/status.phone` в `max_worker/main.py` (путь не затронут переходом на 2.5.0, см. выше), `MaxMessenger.get_own_phone`, `capture_connect_phone`, `normalize_manual` в форме. Тесты `test_entered_a_scanned_b_shows_b` и ещё два зелёные. Живое: 19-UAT №2 (A введён, показан B, без пометки) и №3 (номер сканирующего в форме, показан он же, без пометки), `result: pass`, слова владельца дословно. Запасной путь D-10 («MAX номер не отдал -> номер формы») на живом аккаунте не сработал, потому что MAX номер отдал; он покрыт тестами `test_max_without_a_reported_number_shows_the_form_number_without_the_manual_mark`, `test_a_known_max_number_survives_both_sources` |
| 4 | Воркер старого образа (нет `phone` в `/status`) подключает аккаунт как раньше; пустое не пишется поверх известного | ✓ VERIFIED | Без изменений: `reported_phone_from_status` тотальна, `get_own_phone` глотает отказ; тесты `test_an_old_worker_status_connects_the_wa_account_with_an_unknown_number`, `test_an_old_max_worker_status_connects_with_the_form_number`, `test_a_failing_capture_still_connects_the_account`, `test_an_empty_or_other_report_never_overwrites_a_known_number` зелёные |
| 5 | `just prod-deploy` и `just prod-hard-deploy` пересобирают оба образа (WA и MAX) | ✓ VERIFIED | Перезапуск `just --dry-run`: `prod-deploy` печатает `... && just max-worker-build && just wa-worker-build && ...` до остановки контейнеров; `prod-hard-deploy` — то же с `--no-cache`. `tests/test_wa_worker_deployment.py` зелёный. Выкат владельцем в этот обход пересобрал образы (19-UAT №1) |

**Счёт:** 5/5 истин подтверждено; `behavior_unverified: 0`.

### Артефакты

| Артефакт | Ожидание | Статус | Детали |
|----------|----------|--------|--------|
| `app/application/accounts/connect_phone.py` | помощник захвата WA/MAX, «сообщённый -> запасной» | ✓ VERIFIED | не менялся с прошлого раунда; подключён в двух опросчиках |
| `app/messengers/telegram_user.py`, `base.py`, `whatsapp.py`, `max.py` | `QrAuthResult`, `reported_phone_*`, `get_own_phone` | ✓ VERIFIED | не менялись |
| `app/pages/accounts.py`, `max_connect_step.html` | `_save_tg_account`, опросчики, форма MAX с подсказкой | ✓ VERIFIED | не менялись; живой обход прошёл через форму и опросчик MAX |
| `max_worker/main.py` | `own_phone_of`, `on_start`, `/status.phone`, `MAX_WEBSOCKET_URL` | ✓ VERIFIED | изменён переходом на 2.5.0 (импорты, комментарии), путь захвата цел; на бою `max-worker-88/89`: «client started», `connected` |
| `max_worker/requirements.txt`, `pymax_compat.py` | `maxapi-python==2.5.0`, оставлена только совместимость кадра websocket | ✓ VERIFIED | образ на бою: `maxapi-python 2.5.0` (19-UAT, машинная улика) |
| `wa_worker/own_phone.js`, `index.js`, `justfile` | разбор `creds.me.id`, `phone` в `/status`, пересборка обоих образов | ✓ VERIFIED | не менялись |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус |
|--------|------|-------|--------|
| `qr_login.wait()` / `sign_in()` | колонка `phone` | `own_phone` -> `QrAuthResult` -> `record_reported_phone` | WIRED |
| `/status` WA/MAX | колонка `phone` | `get_own_phone` -> `capture_connect_phone` -> `fill_reported_phone` | WIRED (MAX — подтверждено наблюдением на живом аккаунте №88/№89 на PyMax 2.5.0) |
| форма MAX | запас D-10 | `normalize_manual` -> `credentials` -> `entered_phone` | WIRED |
| `client.me.contact.phone` (PyMax 2.5.0) | `state.own_phone` -> `/status.phone` | `own_phone_of` в `on_start` | WIRED; живой исход B |
| колонка `phone` | список аккаунтов | помощник подписи Фазы 17 | WIRED; владелец видел номер в списке |

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Тесты фазы (10 файлов) | `uv run pytest tests/test_worker/test_max_worker.py tests/test_application/test_connect_phone.py tests/test_pages/test_connect_phone_capture.py tests/test_pages/test_max_connect_transport.py tests/test_messengers/{test_telegram_user,test_max,test_whatsapp}.py tests/test_routes/test_tg_user_auth.py tests/test_wa_worker_deployment.py tests/test_worker/test_wa_worker_own_phone.py -q -p no:randomly` | 278 passed | ✓ PASS |
| Полный набор (замер оркестратора, не мой) | `uv run pytest tests/ -v` на HEAD `9f226ee8` | 6143 passed, 2 skipped, 0 failed (45:20) | принято как улика оркестратора |
| Деплой-рецепты | `just --dry-run prod-deploy` / `prod-hard-deploy` | оба образа, hard — `--no-cache` | ✓ PASS |
| Дифф покрытых кодовых файлов с прошлого отчёта | `git diff 53653a05 HEAD -- app wa_worker justfile max_worker` | меняется только `max_worker/{main.py,pymax_compat.py,requirements.txt}`; в `main.py` путь захвата не тронут | ✓ PASS |

### Выполнение проб

Проб `probe-*.sh` фаза не объявляет — шаг пропущен.

### Покрытие требований

| Требование | План | Описание | Статус | Доказательство |
|------------|------|----------|--------|----------------|
| PHONE-12 | 19-01 | TG: номер при подключении, QR и 2FA, без второго подключения | ✓ SATISFIED | истина 1 |
| PHONE-13 | 19-02, 19-05, 19-08 | WA: номер при подключении; LID не принимается | ✓ SATISFIED | истина 2; UAT №4 |
| PHONE-14 | 19-03, 19-06, 19-07, 19-08 | MAX: номер при подключении, запас — номер формы как автоматический | ✓ SATISFIED | истина 3; UAT №2, №3 (было: NEEDS HUMAN) |
| PHONE-15 | 19-02, 19-03, 19-05, 19-07 | воркер старого образа не ломает подключение | ✓ SATISFIED | истина 4 |
| PHONE-16 | 19-04, 19-08 | `prod-deploy`/`prod-hard-deploy` пересобирают оба образа | ✓ SATISFIED | истина 5; UAT №1 |

Все пять ID из REQUIREMENTS.md заявлены в frontmatter планов (`requirements:` 19-01…19-08 перечислены и сверены); осиротевших требований нет. Пометки Complete в REQUIREMENTS.md остаются за оркестратором.

### Антипаттерны

| Файл | Строка | Образец | Серьёзность | Влияние |
|------|--------|---------|-------------|---------|
| `max_worker/main.py` | — | `TBD/FIXME/XXX` | — | не найдено |

### Предупреждения (WARNING)

**WR-01 (из 19-REVIEW.md, диспозиция `open`) — остаётся WARNING, не BLOCKER.** `_save_tg_account` вызывает `record_reported_phone` без сейвпоинта, тогда как WA/MAX идут через `capture_connect_phone` с сейвпоинтом. Расхождение с D-05 узкое (только инфраструктурный сбой UPDATE на пути TG), плановое решение задокументировано; тотальность `reported_phone_of` (мусор/исключение -> номер неизвестен, аккаунт создаётся) выполнена и покрыта тестами. Без изменений с прошлого раунда (`app/pages/accounts.py` не менялся); решение — за владельцем. IN-01…IN-03 информационные.

### Информационные замечания

- **Шаг «Подключено» WA.** Владелец в UAT №5 описал шаг MAX («MAX подключён, номера не было»); про шаг WA его слов нет. Отсутствие номера на шаге WA снято машиной в том же обходе (19-UAT, 06:29–06:31Z: «WhatsApp подключён!» без номера) и закреплено тестами шаблона. Критерий успеха ROADMAP от этого не зависит; на статус не влияет.
- **Вне объёма фазы (запись 19-UAT):** после удаления аккаунта #88 контейнер `max-worker-88` продолжил работу и заново начал QR-вход — удаление аккаунта, судя по всему, не гасит воркер сразу (ожидание `idle_shutdown_sec=300`). К захвату номера отношения не имеет.
- **Живой аккаунт `max-worker-19`** (отказы с 2026-11-22) вне фазы; переход на PyMax 2.5.0 устранил причину для новых подключений.

### Проверка людьми

Нет. Все четыре пункта прошлого раунда закрыты наблюдениями владельца (см. `re_verification.human_items_closed`).

### Итог

Расхождений нет: ни одна истина не FAILED, живая часть критерия 3 подтверждена владельцем, переход на PyMax 2.5.0 путь захвата не затронул. Статус — `passed`; открытым остаётся только WARNING WR-01 (решение владельца, цель не блокирует).

---

_Проверено: 2026-11-23T11:00:00Z_
_Верификатор: Claude (gsd-verifier)_
