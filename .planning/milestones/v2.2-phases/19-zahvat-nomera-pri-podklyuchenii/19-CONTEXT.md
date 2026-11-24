# Phase 19: Захват номера при подключении - Context

**Gathered:** 2026-11-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Новый аккаунт любого из трёх мессенджеров (Telegram, WhatsApp, MAX) получает номер в момент
подключения, и пользователь видит его в списке аккаунтов, ничего не вводя (PHONE-12…PHONE-16).
Источники: результат входа Telethon (TG), поле `phone` в `/status` воркеров WA и MAX; у MAX
запасной источник — номер из формы подключения. Плюс деплой-рецепты, пересобирающие оба образа
воркеров.

Вне фазы: дозаполнение номеров уже существующих аккаунтов (Фаза 20), обновление уже известного
автономера, починка давнего дефекта `check_connection()`, смена пинов Telethon / Baileys / pymax.

</domain>

<decisions>
## Implementation Decisions

### Уже заперто роадмапом, требованиями и решениями прошлых фаз (не пересматривать)
- **D-01:** Пишет номер **только** писатель Фазы 16 (`app/application/accounts/phone.py`).
  Мастер TG — через `record_reported_phone` (строка создаётся в том же обработчике). Опрос
  статуса WA/MAX — через `fill_reported_phone` (строка уже существует). Оба пишут только
  неизвестный номер, признак «указан вручную» не ставят никогда. Своя запись в колонку мимо
  писателя краснит гейт единственного писателя и защиту `phone_guard` (D-13 Фазы 16).
  Транзакцией владеет обработчик. Номер пишется в том же коммите, что `status="active"` (TG) или
  `status="syncing"` (WA/MAX).
- **D-02:** **TG.** Номер берётся из ответа самого входа: `User` из `qr_login.wait()` на пути QR
  и `User` из `sign_in(password=)` на пути 2FA. Второго подключения к Telegram нет (критерий 1,
  тест). Результат входа передаётся в `_save_tg_account` из **того же `pop`** состояния
  `_qr_sessions`, что и строка сессии. Инвариант «нет `await` между проверкой и `pop`»
  сохраняется (пометка роадмапа). Часть TG от живого стенда не зависит и может идти отдельной
  волной.
- **D-03:** **WA.** Номер в `wa_worker/index.js` берётся из `creds.me.id` **только** через
  `isPnUser` + `jidDecode(...).user`. Никогда не через `split(':')`. LID (`@lid`) и пусто → `null`,
  номер остаётся «неизвестен». Юнит-тест на четырёх входах: PN с устройством, PN без устройства,
  LID, пусто (критерий 2).
- **D-04:** **MAX.** Номер в `max_worker/main.py` — `client.me.contact.phone` (`int | None`),
  читается в `on_start`. `session.db → sessions.phone` у `WebClient` всегда пуст и источником не
  служит (SUMMARY разведки). Заполненность при QR-входе не проверена. Это первый вопрос
  разведки и ручного обхода.
- **D-05:** **Старый образ воркера** (`/status` без поля `phone`) подключает аккаунт как раньше:
  номер остаётся «неизвестен», подключение не падает. Сбой захвата (исключение, мусор) обёрнут
  так, чтобы вход не ломался. Пустое значение никогда не пишется поверх известного (это
  гарантирует `fill_reported_phone`). Тест на `/status` старой формы (критерий 4, PHONE-15).
- **D-06:** **Деплой.** `prod-deploy` и `prod-hard-deploy` в `justfile` вызывают
  `just wa-worker-build` рядом с уже стоящим `just max-worker-build`, у hard-варианта — с
  `--no-cache` (критерий 5, PHONE-16, машинная проверка).
- **D-07:** Номера не попадают в журналы (PHONE-21). В журнал — только `account_id` и исход
  писателя (`PhoneWrite`), без значения. Гейты номера Фазы 16 называются поимённо в
  `<automated>` каждого плана: `tests/test_phone_privacy_gate.py`,
  `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py`.
  Плюс сквозные гейты затронутых обработчиков, включая `tests/test_pages/test_htmx_post_pairs.py`.
- **D-08:** Давний дефект `check_connection()` (отозванную TG-сессию считает подключённой) тесты
  фазы **не закрепляют** как норму (пометка роадмапа; см. память о тестах, закрепляющих старые
  дефекты).

### Номер из формы подключения MAX (решение владельца, 2026-11-22)
- **D-09:** **Неверный номер в форме MAX отклоняется с подсказкой.** Поле разбирается тем же
  нормализатором ручного ввода (`normalize_manual` из `app/services/phone.py`). Если номер не
  разобрался, форма отвечает тем же русским текстом ошибки с примером написания (константа
  `PhoneError`), что и ручная правка Фазы 18. QR не открывается, пока номер не исправлен. Ввод
  вида `8 999 123 45 67` или `+7 999 123-45-67` (плейсхолдер самого поля) проходит.
  - Путь ошибки — уже существующий путь пустого поля (`respond_field_error`, 422, поле сохраняет
    введённое). Новой формы и нового маршрута нет. Введённое значение в текст ошибки не
    подставляется (D-18 Фазы 16).
  - Пустое поле отвечает как сегодня (`MAX_EMPTY_PHONE_ERROR`). Заменять ли этот текст на
    `PHONE_ERROR_BLANK`, решает планировщик. Удалять `MAX_EMPTY_PHONE_ERROR`, не проверив, кто
    его закрепляет, нельзя.
  - *Почему не строгий разбор:* `normalize_reported` принимает только цифры ASCII, и плейсхолдер
    формы им отвергается. Поэтому ручной нормализатор.
- **D-10:** Номер из формы — **запасной автоматический источник, а не ручной** (PHONE-14,
  решение 2 разведки). При подключении сначала пишется номер, который отдал MAX. Если MAX номер
  не отдал, пишется нормализованный номер из формы. Оба через `fill_reported_phone`, признак
  «указан вручную» не ставится, пометки «указан вручную» нет. Тест «ввёл A, отсканировал B →
  показан B» (критерий 3).
  - Где хранится введённый номер до подключения, выбирает планировщик. Сегодня он лежит в
    `account.credentials` до перехода в `syncing` (там его затирает `session_id`) и в
    `phone.txt` воркера. Номер из формы не логируется (D-07).

### Приёмка WA/MAX (решение владельца, 2026-11-22)
- **D-11:** **Ручной обход WA и MAX проводится на бою после деплоя**, как в прошлых фазах. Код
  ветки и пересобранные образы воркеров на боевом стенде, владелец подключает свои живые WA и
  MAX. Обход заодно проверяет, что деплой пересобирает оба образа. Машинная улика обхода не
  заменяет отметку владельца (память `uat-machine-evidence-is-not-acceptance`). Проверить код
  ветки в web-контейнере до обхода (память `prod-walkthrough-stand-and-seeding`).

### Принято по умолчанию при делегировании (владелец, 2026-11-22: два вопроса, остальное — по умолчаниям)
- **D-12:** Шаг «подключено» в мастерах номер **не показывает**. Номер виден в списке аккаунтов
  и всех подписях через помощник Фазы 17. *Обоснование:* критерий говорит «показывает в
  списке». Лишний показ — ещё одно место для гейта приватности и маски.
- **D-13:** Волны: TG — отдельная волна без стенда. WA/MAX (воркеры, адаптеры, обработчики
  статуса, форма MAX, деплой) — вторая волна. Ручной обход — чекпойнт в конце. *Обоснование:*
  пометка роадмапа. Отказ стенда не держит TG.
- **D-14:** Форма ответа `/status`: поле `phone` — строка цифр E.164 без `+` или `null`.
  Отсутствие поля (старый образ) равносильно `null`. Окончательная нормализация — в
  `normalize_reported` на стороне приложения, воркер номер не форматирует. *Обоснование:* один
  нормализатор, старый и новый образ читаются одним кодом.
- **D-15:** Если номер известен воркеру, но приложение опросило статус раньше, чем он появился
  (MAX: `on_start` ещё не прошёл), повторного опроса ради номера нет. Номер дозаполнит Фаза 20
  или ручная правка. *Обоснование:* подключение не должно ждать номер (PHONE-15).

### Claude's Discretion
- Имена и сигнатуры: `get_own_phone()` в адаптерах или чтение поля из ответа статуса; способ
  передать `User` из `complete_auth` / `submit_2fa` (кортеж, датакласс `QrAuthResult` и т. п.).
- Как именно воркер MAX хранит номер из `client.me` между `on_start` и запросом `/status`.
- Тексты подсказки под полем номера в форме MAX (например, «нужен, если MAX не сообщит номер
  сам»). Без значения номера.
- Где в `wa_worker` держать разбор `creds.me.id` (отдельная функция ради юнит-теста на четырёх
  входах обязательна по смыслу D-03).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Требования и границы фазы
- `.planning/ROADMAP.md` §«Phase 19: Захват номера при подключении» — цель, 5 критериев успеха,
  пометки Research (Baileys rc14, pymax), инвариант `pop`, дефект `check_connection()`
- `.planning/REQUIREMENTS.md` — PHONE-12…PHONE-16, PHONE-21
- `.planning/research/SUMMARY.md` — решения разведки 2 (номер формы MAX — запасной, не ручной) и
  источники номера; «Phase 4: Захват» = эта фаза
- `.planning/research/STACK.md`, `.planning/research/PITFALLS.md`,
  `.planning/research/ARCHITECTURE.md` — `isPnUser`/`jidDecode`, `client.me.contact.phone`,
  read-check-write, пересборка образов

### Решения прошлых фаз, на которых стоит эта
- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-CONTEXT.md` — единый
  писатель (D-12, D-13), нормализация (D-05, D-15), приватность (D-18)
- `.planning/phases/17-pokaz-nomera-na-vseh-ekranah/17-CONTEXT.md` — показ через помощник подписи
- `.planning/phases/18-ruchnaya-pravka-nomera/18-CONTEXT.md` — `PhoneError` и путь 422 формы
  (образец для D-09), сквозные гейты (D-08 Фазы 18)

### Код
- `app/application/accounts/phone.py` — `record_reported_phone`, `fill_reported_phone`, `PhoneWrite`
- `app/services/phone.py` — `normalize_manual`, `normalize_reported`, `PhoneError`
- `app/messengers/telegram_user.py` — `QRAuthState`, `_qr_sessions`, `complete_auth`, `submit_2fa`
- `app/pages/accounts.py` — `_save_tg_account`, `accounts_connect_wa_status`,
  форма MAX (`MAX_EMPTY_PHONE_ERROR`), `accounts_connect_max_status`
- `app/messengers/whatsapp.py`, `app/messengers/max.py` — адаптеры (`check_connection`)
- `wa_worker/index.js` — `GET /api/sessions/:id/status`, `creds.json`
- `max_worker/main.py` — `create_client`, `on_start`, `get_session_status`, `phone.txt`
- `justfile` — `prod-deploy`, `prod-hard-deploy`, `wa-worker-build`, `max-worker-build`
- `app/templates/accounts/includes/max_connect_step.html` — поле номера формы MAX

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `record_reported_phone(session, account, raw)` — для только что созданной строки мастера TG:
  сам сбрасывает ожидающую вставку и кладёт значение на объект без лишнего UPDATE. Объект
  обязан быть в сессии писателя, иначе громкий `ValueError(ACCOUNT_NOT_IN_SESSION)`.
- `fill_reported_phone(session, account_id, raw)` — для существующей строки WA/MAX. На мусоре
  отвечает `UNPARSEABLE` без обращения к базе.
- `normalize_manual` / `PhoneError` — разбор свободного ввода формы MAX с готовыми русскими
  текстами.
- `respond_field_error` — путь 422 формы MAX уже существует (пустое поле).

### Established Patterns
- Мастер TG: оба пути (опрос QR и подтверждение 2FA) сводятся в `_save_tg_account`.
  `complete_auth` снимает состояние `pop` до первого ожидания: одно сканирование — один аккаунт.
- Опрос статуса WA/MAX: найти строку `connecting` → `check_connection()` → `credentials =
  session_id`, `status = "syncing"`, коммит → Celery-задача синка групп.
- `max-worker-build` уже вызывается деплой-рецептами, `wa-worker-build` — нет.

### Integration Points
- Номер в мастер TG приходит из `telegram_user.py` и уходит в `_save_tg_account`.
- Поле `phone` в `/status` воркеров приходит через адаптеры в два обработчика опроса статуса.
- Номер формы MAX: `accounts_connect_max_post` (сейчас кладёт в `credentials` и в
  `start_session(phone=)`) → обработчик опроса статуса при подключении.

</code_context>

<specifics>
## Specific Ideas

- Сценарий приёмки MAX: «ввёл A, отсканировал B → показан B». Если MAX номер не отдал — показан
  A, без пометки «указан вручную».
- Сценарий приёмки WA: сессия отдала только LID → «Номер неизвестен», а не цифры LID.

</specifics>

<deferred>
## Deferred Ideas

- Обновление уже известного автономера при повторном подключении (сейчас автоисточник пишет
  только в пустое) — v2+, вместе с возможным `phone_source` (SUMMARY разведки).
- Починка `check_connection()` для отозванной TG-сессии — вне вехи. Здесь только не закреплять
  дефект тестами.

</deferred>

---

*Phase: 19-zahvat-nomera-pri-podklyuchenii*
