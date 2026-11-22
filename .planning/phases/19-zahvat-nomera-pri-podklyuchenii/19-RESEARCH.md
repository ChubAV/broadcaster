# Phase 19: Захват номера при подключении - Research

**Researched:** 2026-11-22
**Domain:** подключение аккаунтов TG / WA / MAX; контракт `/status` воркеров; единый писатель номера Фазы 16; деплой образов воркеров
**Confidence:** HIGH по Telethon, Baileys rc14 (исходник пина прочитан, tarball сверен с lockfile), писателю, интеграционным точкам и гейтам; **LOW по одному вопросу, который исходник решить не может**: отдаёт ли сервер MAX `contact.phone` при QR-входе `WebClient` (раздел A1 — решает только ручной обход владельца)

**Как читать метки.** `[ЗАМЕР: команда]` — прогнано в этой сессии; `[ПРОЧИТАНО: путь:строки]` — файл открыт, значение процитировано дословно; `[ВЫВОД]` — следствие из двух прочитанных мест; `[ОЦЕНКА]` — суждение без прогона; `[ASSUMED]` — знание из обучения, не проверенное в сессии (собрано в «Assumptions Log»). Рабочее дерево репозитория не менялось: `git status --short` на конец исследования — только `?? .dockerignore`, как на старте. Исходники пина Baileys читались из tarball, скачанного в `/home/orca/.claude/jobs/46358bbc/tmp/baileys-rc14/` (только чтение; `npm install` и исполнение скачанного кода не выполнялись); хеш tarball совпал с `package-lock.json` (см. A2).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Уже заперто роадмапом, требованиями и решениями прошлых фаз (не пересматривать)
- **D-01:** Пишет номер **только** писатель Фазы 16 (`app/application/accounts/phone.py`). Мастер TG — через `record_reported_phone` (строка создаётся в том же обработчике). Опрос статуса WA/MAX — через `fill_reported_phone` (строка уже существует). Оба пишут только неизвестный номер, признак «указан вручную» не ставят никогда. Своя запись в колонку мимо писателя краснит гейт единственного писателя и защиту `phone_guard` (D-13 Фазы 16). Транзакцией владеет обработчик. Номер пишется в том же коммите, что `status="active"` (TG) или `status="syncing"` (WA/MAX).
- **D-02:** **TG.** Номер берётся из ответа самого входа: `User` из `qr_login.wait()` на пути QR и `User` из `sign_in(password=)` на пути 2FA. Второго подключения к Telegram нет (критерий 1, тест). Результат входа передаётся в `_save_tg_account` из **того же `pop`** состояния `_qr_sessions`, что и строка сессии. Инвариант «нет `await` между проверкой и `pop`» сохраняется (пометка роадмапа). Часть TG от живого стенда не зависит и может идти отдельной волной.
- **D-03:** **WA.** Номер в `wa_worker/index.js` берётся из `creds.me.id` **только** через `isPnUser` + `jidDecode(...).user`. Никогда не через `split(':')`. LID (`@lid`) и пусто → `null`, номер остаётся «неизвестен». Юнит-тест на четырёх входах: PN с устройством, PN без устройства, LID, пусто (критерий 2).
- **D-04:** **MAX.** Номер в `max_worker/main.py` — `client.me.contact.phone` (`int | None`), читается в `on_start`. `session.db → sessions.phone` у `WebClient` всегда пуст и источником не служит (SUMMARY разведки). Заполненность при QR-входе не проверена. Это первый вопрос разведки и ручного обхода.
- **D-05:** **Старый образ воркера** (`/status` без поля `phone`) подключает аккаунт как раньше: номер остаётся «неизвестен», подключение не падает. Сбой захвата (исключение, мусор) обёрнут так, чтобы вход не ломался. Пустое значение никогда не пишется поверх известного (это гарантирует `fill_reported_phone`). Тест на `/status` старой формы (критерий 4, PHONE-15).
- **D-06:** **Деплой.** `prod-deploy` и `prod-hard-deploy` в `justfile` вызывают `just wa-worker-build` рядом с уже стоящим `just max-worker-build`, у hard-варианта — с `--no-cache` (критерий 5, PHONE-16, машинная проверка).
- **D-07:** Номера не попадают в журналы (PHONE-21). В журнал — только `account_id` и исход писателя (`PhoneWrite`), без значения. Гейты номера Фазы 16 называются поимённо в `<automated>` каждого плана: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py`. Плюс сквозные гейты затронутых обработчиков, включая `tests/test_pages/test_htmx_post_pairs.py`.
- **D-08:** Давний дефект `check_connection()` (отозванную TG-сессию считает подключённой) тесты фазы **не закрепляют** как норму (пометка роадмапа; см. память о тестах, закрепляющих старые дефекты).

#### Номер из формы подключения MAX (решение владельца, 2026-11-22)
- **D-09:** **Неверный номер в форме MAX отклоняется с подсказкой.** Поле разбирается тем же нормализатором ручного ввода (`normalize_manual` из `app/services/phone.py`). Если номер не разобрался, форма отвечает тем же русским текстом ошибки с примером написания (константа `PhoneError`), что и ручная правка Фазы 18. QR не открывается, пока номер не исправлен. Ввод вида `8 999 123 45 67` или `+7 999 123-45-67` (плейсхолдер самого поля) проходит.
  - Путь ошибки — уже существующий путь пустого поля (`respond_field_error`, 422, поле сохраняет введённое). Новой формы и нового маршрута нет. Введённое значение в текст ошибки не подставляется (D-18 Фазы 16).
  - Пустое поле отвечает как сегодня (`MAX_EMPTY_PHONE_ERROR`). Заменять ли этот текст на `PHONE_ERROR_BLANK`, решает планировщик. Удалять `MAX_EMPTY_PHONE_ERROR`, не проверив, кто его закрепляет, нельзя.
  - *Почему не строгий разбор:* `normalize_reported` принимает только цифры ASCII, и плейсхолдер формы им отвергается. Поэтому ручной нормализатор.
- **D-10:** Номер из формы — **запасной автоматический источник, а не ручной** (PHONE-14, решение 2 разведки). При подключении сначала пишется номер, который отдал MAX. Если MAX номер не отдал, пишется нормализованный номер из формы. Оба через `fill_reported_phone`, признак «указан вручную» не ставится, пометки «указан вручную» нет. Тест «ввёл A, отсканировал B → показан B» (критерий 3).
  - Где хранится введённый номер до подключения, выбирает планировщик. Сегодня он лежит в `account.credentials` до перехода в `syncing` (там его затирает `session_id`) и в `phone.txt` воркера. Номер из формы не логируется (D-07).

#### Приёмка WA/MAX (решение владельца, 2026-11-22)
- **D-11:** **Ручной обход WA и MAX проводится на бою после деплоя**, как в прошлых фазах. Код ветки и пересобранные образы воркеров на боевом стенде, владелец подключает свои живые WA и MAX. Обход заодно проверяет, что деплой пересобирает оба образа. Машинная улика обхода не заменяет отметку владельца (память `uat-machine-evidence-is-not-acceptance`). Проверить код ветки в web-контейнере до обхода (память `prod-walkthrough-stand-and-seeding`).

#### Принято по умолчанию при делегировании (владелец, 2026-11-22: два вопроса, остальное — по умолчаниям)
- **D-12:** Шаг «подключено» в мастерах номер **не показывает**. Номер виден в списке аккаунтов и всех подписях через помощник Фазы 17. *Обоснование:* критерий говорит «показывает в списке». Лишний показ — ещё одно место для гейта приватности и маски.
- **D-13:** Волны: TG — отдельная волна без стенда. WA/MAX (воркеры, адаптеры, обработчики статуса, форма MAX, деплой) — вторая волна. Ручной обход — чекпойнт в конце. *Обоснование:* пометка роадмапа. Отказ стенда не держит TG.
- **D-14:** Форма ответа `/status`: поле `phone` — строка цифр E.164 без `+` или `null`. Отсутствие поля (старый образ) равносильно `null`. Окончательная нормализация — в `normalize_reported` на стороне приложения, воркер номер не форматирует. *Обоснование:* один нормализатор, старый и новый образ читаются одним кодом.
- **D-15:** Если номер известен воркеру, но приложение опросило статус раньше, чем он появился (MAX: `on_start` ещё не прошёл), повторного опроса ради номера нет. Номер дозаполнит Фаза 20 или ручная правка. *Обоснование:* подключение не должно ждать номер (PHONE-15).

### Claude's Discretion
- Имена и сигнатуры: `get_own_phone()` в адаптерах или чтение поля из ответа статуса; способ передать `User` из `complete_auth` / `submit_2fa` (кортеж, датакласс `QrAuthResult` и т. п.).
- Как именно воркер MAX хранит номер из `client.me` между `on_start` и запросом `/status`.
- Тексты подсказки под полем номера в форме MAX (например, «нужен, если MAX не сообщит номер сам»). Без значения номера.
- Где в `wa_worker` держать разбор `creds.me.id` (отдельная функция ради юнит-теста на четырёх входах обязательна по смыслу D-03).

### Deferred Ideas (OUT OF SCOPE)
- Обновление уже известного автономера при повторном подключении (сейчас автоисточник пишет только в пустое) — v2+, вместе с возможным `phone_source` (SUMMARY разведки).
- Починка `check_connection()` для отозванной TG-сессии — вне вехи. Здесь только не закреплять дефект тестами.

Вне фазы (из «Phase Boundary»): дозаполнение номеров уже существующих аккаунтов (Фаза 20), обновление уже известного автономера, починка давнего дефекта `check_connection()`, смена пинов Telethon / Baileys / pymax.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PHONE-12 | новый аккаунт Telegram получает номер при подключении — и по QR, и после пароля 2FA — без повторного подключения к Telegram | A3 (оба `User` прочитаны в Telethon 1.42.0), B3 (карта мастера TG, место `pop`), §Pattern 1; тест «`get_me` не вызван, клиент создан один раз» |
| PHONE-13 | новый аккаунт WhatsApp получает номер при подключении; LID за номер не принимается | A2 (`isPnUser`/`jidDecode` rc14, `creds.me`), §Pattern 3 (чистая функция + DI), §Pattern 2 (опрос статуса), измерение «16 % LID-подобных строк проходят `normalize_reported`» |
| PHONE-14 | новый аккаунт MAX получает номер при подключении; если мессенджер номер не отдал — номер из формы, как автоматический, не ручной | A1 (pymax 2.3.1), B6 (форма, `credentials`), §Pattern 4 (порядок «MAX, затем форма»), измерение «ввёл A, отсканировал B → B» |
| PHONE-15 | воркер старого образа не ломает подключение: аккаунт подключается, номер остаётся неизвестным | B4–B5 (старая форма `/status`), C (IN-07 закрыт: писатель ловит ошибку вызывающего и на мусоре), §Pitfall 5, Open Question 1 |
| PHONE-16 | рецепты `prod-deploy` и `prod-hard-deploy` пересобирают оба образа воркеров | B8 (`justfile`, `just --dry-run`, тест уже есть для MAX), Open Question 2 (`prod-build`) |
| PHONE-21 (сквозное) | номера не попадают в журналы | B9 (что гейты судят и чего не видят), §Pitfall 8–9, Security Domain |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Из `/source/broadcaster/CLAUDE.md` и `/source/broadcaster/.claude/CLAUDE.md` [ПРОЧИТАНО]:
- Стек: Python 3.12 + `uv`, FastAPI + SQLAlchemy async + Jinja2; команды через `just` (`just test` = `uv run pytest tests/ -v`). Тесты — `sqlite+aiosqlite:///:memory:` с полной схемой на тест; фикстуры `client`, `db_session`, `auth_headers`, `authed_client`.
- `graphify`: для вопросов о коде сначала `graphify query "<вопрос>"`; **после правки кода — `graphify update .`** (правило исполнителей; исследователь его не запускал, код не менялся).
- Новых зависимостей фаза не вводит; новых каталогов верхнего уровня тоже.

Директивы памяти проекта, применимые к планированию (`MEMORY.md`, [ПРОЧИТАНО]): `cross-cutting-gates-skipped-by-executors` (в наряде каждого плана называть `test_htmx_post_pairs` и прочие поимённо); `orchestrator-gate-catches-records-defects` (исполнители отключают `tests/test_planning/` — гонять явно); `phase-tests-can-pin-preexisting-defects` (тесты не закрепляют `check_connection()`); `uat-machine-evidence-is-not-acceptance` и `uat-template-trips-self-certify-rule` (улику обхода писать разделом, отметки оставлять владельцу, форма UAT — как в фазах 9–10); `prod-walkthrough-stand-and-seeding` (проверить код ветки в web-контейнере до обхода); `threat-id-uniqueness-gate` (`T-19-NN` не повторять в фазе); `check-gate-before-commit-in-chains` (`pytest …; commit` коммитит и при красном — только `&&`); `regression-gate-duplicates-post-merge-suite` (полная суита ~46 мин, таймаут 5400 с); `plan-phase-5-5-blanks-validation` (на replan не затирать VALIDATION.md); `owner-answers-must-return-to-research` (закрытые Open Questions вернуть сюда); `ask-owner-in-russian`.

## Summary

Фаза не тянет ни одного пакета. Писатель, нормализаторы, слой ответа, форма v2.1, адаптеры и сквозные гейты уже в дереве; Phase 18 закрыта и больше не держит `app/pages/accounts.py` (она правила в нём одну строку, `:1051`). Три места, где мастер создаёт аккаунт, и два опросчика статуса — все в одном файле, поэтому его правят **строго последовательно** (план TG раньше плана WA/MAX).

**Внешняя неопределённость сведена к одной точке.** По Telethon и Baileys вопрос закрыт чтением исходников пина: оба `User` у Telethon 1.42.0 берутся из ответов входа без `get_me()`; в Baileys 7.0.0-rc14 `isPnUser` и `jidDecode` экспортированы корневым пакетом, `creds.me.id` — сырой `jid` из узла `pair-success` (сам Baileys трактует его как PN: `const myPN = authState.creds.me.id`), а живой объект `creds` отдаётся геттером `sock.user`. По pymax 2.3.1 прочитано всё, что можно прочитать: `client.me` заполняется **до** `on_start`, из ответа `LOGIN` (путь `web_login` у `WebClient`), `contact.phone` — `int | None`. **Приходит ли `phone` в этом ответе у QR-входа — исходник не говорит и сказать не может** (в `pymax` нет ни одной проверки или фикстуры с `phone` у профиля; внешний поиск ничего не дал). Значит, единственное измерение — ручной обход владельца (D-11), а реалистичный путь MAX в плане — номер из формы (D-10), с `phone` от воркера как приятным бонусом.

**Все долги, названные Фазе 19 вне CONTEXT, замерены в дереве: IN-07 и WR-43 закрыты** (код + прогон), гейты единственного писателя и приватности зелёны (1161 passed за 63 с), T-16-25 и T-16-49 держатся. Открытых долгов, на которые опирается Фаза 19, нет. Две находки самого исследования меняют план: (1) **критерий 3 и критерий 4 расходятся на MAX со старым образом воркера** (форма требует номер, запасной источник — форма, а критерий 4 говорит «остаётся неизвестен») — вопрос владельцу; (2) **`MAX_EMPTY_PHONE_ERROR` закрепляет один тест подстрокой**, замена на `PHONE_ERROR_BLANK` безопасна, но тест `test_a_hostile_phone_never_reaches_the_response_raw` после D-09 перестаёт быть «веткой старта» и станет настоящим каналом эха 422.

**Primary recommendation:** шесть планов в трёх волнах — (1) TG: `QRAuthState.own_phone` + `QrAuthResult` + `record_reported_phone` в `_save_tg_account`; (2) параллельно воркеры WA (чистая функция в отдельном модуле с внедрением `isPnUser`/`jidDecode`, тест через уже существующий `run_node_script`), MAX (вспомогательная функция и `SessionState.own_phone`, захват в `on_start` в защитной обёртке), деплой (`wa-worker-build *args`) и приложение WA/MAX (адаптер `get_own_phone()`, захват в обёртке с сейвпоинтом, форма MAX через `normalize_manual`, запасной номер из `credentials`); (3) чекпойнт ручного обхода. Сквозные счётчики гейтов (`WRITE_FORM_PLACES`, `MUTATING_ROUTE_COUNT` и т. п.) **не двигаются**: нет ни нового маршрута, ни формы, ни кода уведомления [ОЦЕНКА: структурные гейты считают маршруты, формы, коды реестра и OOB; ни одного из них фаза не добавляет; проверяется прогоном поимённых модулей в каждом плане].

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Достать собственный номер из ответа мессенджера (TG `User.phone`, WA `creds.me.id`, MAX `client.me.contact.phone`) | Воркер / адаптер мессенджера (там, где живёт сессия) | — | Только там есть сам объект ответа; второго подключения быть не должно (D-02) |
| Разбор JID (PN vs LID) | wa_worker (JS, через функции Baileys) | — | LID-цифры выглядят как номер (измерено) — отсекать надо до передачи (D-03) |
| Нормализация к E.164 | Приложение (`normalize_reported`) | — | Один нормализатор для старых и новых образов (D-14) |
| Нормализация номера из формы MAX | Приложение (`normalize_manual`, страничный слой) | — | Плейсхолдер формы не проходит строгий разбор (D-09) |
| Запись номера в колонку | Application (`app/application/accounts/phone.py`) | Database (условный UPDATE) | Единственный писатель D-13 Фазы 16; транзакция — за обработчиком (D-01) |
| Опрос статуса и переход в `syncing` / `active` | Frontend Server (обработчики `accounts.py`) | Воркер (`/status`) | Обработчик владеет коммитом; поле `phone` приходит из воркера через адаптер |
| Запас «номер из формы» MAX | Frontend Server (`credentials` строки `connecting`) | — | Хранение уже существует; воркеру номер не нужен (Open Question 1 — если владелец выберет иначе) |
| Пересборка образов воркеров при деплое | Build/Deploy (`justfile`) | — | Образы строятся вне compose (`docker build`), в деплой-рецепт их вносит только человек |

## Standard Stack

Фаза **не вводит ни одного нового пакета и не меняет пины** [ВЫВОД: правки лежат в наших исходниках, `uv.lock`, `package-lock.json`, `max_worker/requirements.txt` не трогаются].

### Core (уже в проекте, пины прочитаны)
| Library | Pin | Где закреплён | Что даёт фазе |
|---------|-----|---------------|---------------|
| Telethon | 1.42.0 | `uv.lock:2040-2041` (`name = "telethon"` / `version = "1.42.0"`); `pyproject.toml:30` — только нижняя граница `"telethon>=1.37.0"`; образ приложения ставит `uv sync --frozen --no-dev` (`Dockerfile:17`) | `QRLogin.wait()` и `sign_in(password=)` возвращают `User` |
| Baileys | `7.0.0-rc14` | `wa_worker/package.json` (`"@whiskeysockets/baileys": "7.0.0-rc14"`), `package-lock.json:677-678` | `isPnUser`, `jidDecode`, `sock.user` |
| maxapi-python (pymax) | `2.3.1` | `max_worker/requirements.txt:1` (`maxapi-python==2.3.1`); в `.venv` стоит та же `2.3.1` `[ЗАМЕР: uv pip list]` | `client.me.contact.phone` |
| phonenumbers | 9.0.41 | внутри `app/services/phone.py` | `normalize_reported` / `normalize_manual` |
| Node | образ `node:20-slim` (`wa_worker/Dockerfile:1`); у Baileys `"engines": {"node": ">=20.0.0"}`; на этой машине `v22.22.1` | — | JS-тест фазы идёт через `node -e` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `run_node_script` из `tests/conftest.py` для JS-теста | `node --test` + скрипт в `package.json` | Нужен ещё и pytest-обёртка, иначе `just test` его не увидит; `run_node_script` уже есть, пропуск при отсутствии Node он запрещает (`pytest.fail`) |
| Фоллбек «номер из формы» в приложении (`credentials`) | Фоллбек в воркере (`phone.txt` → `/status.phone`) | см. Open Question 1; приложение-вариант работает со старым образом и не требует правки воркера, воркер-вариант буквально выполняет критерий 4 для MAX |
| Один вызов `get_status()` в адаптере (тело `/status` целиком) | `get_own_phone()` вторым GET после `check_connection()` | Один вызов — без второго обращения, но трогает `check_connection()`, которому адаптерные тесты закрепляют `check_connection_failed`; второй GET (локальный, один раз на подключение) не трогает ничего существующего. Рекомендация: `get_own_phone()` |

**Installation:** не требуется.

**Version verification:** `[ЗАМЕР: uv pip list]` → `maxapi-python 2.3.1`, `telethon 1.42.0`; `[ЗАМЕР: sha512 tarball]` `sha512-WK+X8ju8TPGxvWIsP8hrY6JB6FltYuFe+vsqKfjOYX25JObij9qLf2c3ZGdl1Q+vhFwbnT+AZmWAB5pTvzmSiQ==` совпал с `package-lock.json:680` для `baileys-rc14.tgz`.

## Package Legitimacy Audit

Новых внешних пакетов фаза не устанавливает, поэтому проверка `package-legitimacy check` не требовалась. Три затронутые зависимости — уже закреплённые пины проекта.

| Package | Registry | Закреплён | Источник проверки | Verdict | Disposition |
|---------|----------|-----------|-------------------|---------|-------------|
| `@whiskeysockets/baileys` 7.0.0-rc14 | npm | `package-lock.json` с `integrity` | хеш скачанного tarball = хеш lockfile `[ЗАМЕР]` | OK (существующий пин) | Не меняется |
| `telethon` 1.42.0 | PyPI | `uv.lock` | установленная в `.venv` версия = lock `[ЗАМЕР]` | OK (существующий пин) | Не меняется |
| `maxapi-python` 2.3.1 | PyPI | `max_worker/requirements.txt` `==2.3.1` | установленная в `.venv` версия = пин `[ЗАМЕР]` | OK (существующий пин) | Не меняется |

**Packages removed due to [SLOP] verdict:** none. **Packages flagged [SUS]:** none.

## Ответы на вопросы разведки (часть A: внешняя неопределённость)

### A1. pymax / MAX (D-04, первый вопрос)

**Версия, на которой работает воркер.** `max_worker/requirements.txt` пинует `maxapi-python==2.3.1` `[ПРОЧИТАНО: max_worker/requirements.txt:1]`; `max_worker/Dockerfile` ставит файл как есть (`RUN pip install --no-cache-dir -r requirements.txt`); тест `test_requirements_pin_maxapi_2_3_1` закрепляет пин (`tests/test_worker/test_max_worker.py:1028`). Исходник читался из `.venv/lib/python3.12/site-packages/pymax` той же версии 2.3.1 `[ЗАМЕР: uv pip list]`.

**Что заполняет `client.me` и когда.**
- `WebClient` строит конфиг с `phone=None` `[ПРОЧИТАНО: pymax/client_web.py:55]` — `phone=None,`; при сохранении новой сессии пишется `phone=self.config.phone or "",` `[ПРОЧИТАНО: pymax/app.py:100, :115]` — то есть `sessions.phone` у `WebClient` всегда `""` (подтверждает D-04).
- `App.start()` после аутентификации (QR → токен → `store.save_session`) вызывает `self.api.auth.login(...)`; для `DeviceType.WEB` это `web_login()` (`pymax/api/auth/service.py:108` — `if user_agent.device_type == DeviceType.WEB:`, `:137` — `async def web_login`), ответ разбирается в `LoginResponse` (`profile: Profile`), и затем `self.me = response.profile` `[ПРОЧИТАНО: pymax/app.py:155]`, `self.started = True` `[ПРОЧИТАНО: pymax/app.py:161]`.
- Только после этого `BaseClient.start()` зовёт `emit_start`: `await self._app.start()` (`pymax/base.py:131`), `if not self._app.started:` (`:132`), `await self._app.dispatcher.emit_start(self)` (`:136`). Каждый `on_start`-обработчик запускается **отдельной задачей** `asyncio.create_task(self._run_start_handler(...))` `[ПРОЧИТАНО: pymax/dispatch/dispatcher.py:192]`.
- Вывод `[ВЫВОД]`: **к моменту `on_start` `client.me` — `Profile`, не `None`** (профиль присвоен строкой 155, обработчик стартует после строки 161). До завершения `start()` свойство `client.me` возвращает `None` (`pymax/base.py:52-54`: `def me(self) -> Profile | None:` … `return self._app.me`), и цепочка `client.me.contact.phone` падала бы `AttributeError` — читать надо через `getattr`-защиту.
- Исключение в `on_start` не роняет клиент, но **останавливает остаток самого обработчика**: в нашем `on_start` (`max_worker/main.py:459-480`) сразу после `state.is_connected = True` идёт `state.ready_event.set()` и запуск синка групп — исключение в захвате номера **перед** ними оборвало бы подключение. Поэтому захват — в `try/except` и, лучше, **до** `is_connected = True` (все строки обработчика синхронны: ни одного `await` до `asyncio.create_task`, окна гонки нет).

**Тип и форма `phone`.** `phone: int | None = None` `[ПРОЧИТАНО: pymax/types/domain/user.py:71]`; `Profile.contact: User`. Модель — `CamelModel` с `extra="allow"`. `[ЗАМЕР: User.model_validate на примерах]`: `{"phone": 79991234567}` → `79991234567`; `"79991234567"` и `"+79991234567"` → `79991234567` (строка приводится к `int`); `""` → `ValidationError` (разбор всего `LOGIN` упал бы раньше нашего кода — давний режим pymax, не фазы); поле отсутствует или `None` → `None`. Профиль без `phone`: `Profile.model_validate({"contact":{"id":42}}).contact.phone is None` `[ЗАМЕР]`. Как это стать формой D-14: `str(phone)` для `int > 0`, иначе `None`; `bool` отсекать явно (подкласс `int`), как в `normalize_reported`.

**Заполняет ли сервер `phone` при QR-входе — исходник решить не может.** В pymax нет ни проверки, ни фикстуры, ни комментария о том, что `contact.phone` приходит (единственные упоминания — тип поля и описание «Телефон пользователя, если возвращен API»); фикстура нашего теста даёт профиль без `phone` (`incomplete_contact_login_payload`: `"profile": {"contact": {"id": 42}}`, `tests/test_worker/test_max_worker.py`), так что она тоже ничего не доказывает. Внешний поиск документации pymax (docs / DeepWiki / PyPI) описания полей `client.me` и ответа `WebClient` не нашёл `[ЗАМЕР: поиск, источников нет]`. **Вывод для плана:** это **проверка на ручном обходе** (D-11), не вопрос владельцу. План обязан быть корректным в обоих исходах: MAX отдал номер → пишется он («ввёл A, отсканировал B → B»); не отдал → пишется номер из формы без пометки «указан вручную» (D-10). Это и есть «реалистичный путь» MAX.

### A2. Baileys 7.0.0-rc14 / WA (D-03)

**Версия.** `wa_worker/package.json`: `"@whiskeysockets/baileys": "7.0.0-rc14"` (точный пин, без `^`); `package-lock.json:677-678` — `"node_modules/@whiskeysockets/baileys": {` / `"version": "7.0.0-rc14",`. `wa_worker/node_modules` на этой машине пуст (только `.package-lock.json`), поэтому исходник читался из tarball того же пина `[ЗАМЕР: sha512 tarball = lockfile]`.

**Экспорты.** `lib/index.js:6` — `export * from './WABinary/index.js';`; `WABinary/index.js` реэкспортирует `jid-utils.js`. В `jid-utils.js`: `export const jidDecode = (jid) => {` (`:30`), `export const isPnUser = (jid) => jid?.endsWith('@s.whatsapp.net');` (`:65`), `export const isLidUser = (jid) => jid?.endsWith('@lid');` (`:67`). Типы: `isPnUser: (jid: string | undefined) => boolean | undefined`, `jidDecode: (jid: string | undefined) => FullJid | undefined` `[ПРОЧИТАНО: lib/WABinary/jid-utils.d.ts:24, :30]`. То есть **оба имени экспортируются именованно из корня пакета** — `import makeWASocket, {…, isPnUser, jidDecode} from '@whiskeysockets/baileys'` работает; имена в rc14 именно такие (не `isJidUser`).

**Что возвращает `jidDecode(...).user`.** Тело (`jid-utils.js:30-58`): индекс `@`, `userCombined = jid.slice(0, sepIdx)`, `const [userAgent, device] = userCombined.split(':');` (`:38`), `const [user, agent] = userAgent.split('_');` (`:39`). Вывод `[ВЫВОД]`: для `79991234567:12@s.whatsapp.net` → `user = "79991234567"`, `device = 12`; для `79991234567@s.whatsapp.net` → `user = "79991234567"`, `device = undefined`; для `…_1:12@…` агент отбрасывается. `isPnUser` — просто `endsWith('@s.whatsapp.net')`, на `undefined` возвращает `undefined` (на не-строке упадёт `TypeError` — тип надо проверять самим).

**Форма `creds.me.id` и `creds.me.lid`.**
- При первом сопряжении: `const jid = deviceNode.attrs.jid;` / `const lid = deviceNode.attrs.lid;` (`lib/Utils/validate-connection.js:139-140`), `me: { id: jid, name: bizName, lid },` (`:192`) — **`id` кладётся как пришёл от сервера, без нормализации**, поэтому суффикс устройства возможен (отсюда «PN с устройством»); `lid` — отдельное поле.
- При открытии соединения: `ev.emit('creds.update', { me: { ...authState.creds.me, lid: node.attrs.lid } });` (`lib/Socket/socket.js:764`) — меняется только `lid`.
- Сам Baileys трактует `me.id` как PN: `const myPN = authState.creds.me.id;` (`socket.js:771`) и сохраняет пару `{ lid: myLID, pn: myPN }`. Нигде в `lib/` `me.id` не переписывается в `@lid` (поиск по `me: {` / `me = ` дал только `validate-connection.js:192`, `socket.js:764`, `chats.js:927`, `chat-utils.js:734` — все сохраняют `id`) `[ВЫВОД]`. Тип `Contact.id` в `Types/Contact.d.ts` описан как «ID either in lid or jid format (preferred)», поэтому **LID в `me.id` исключать нельзя** — это и есть смысл теста D-03 на входе `…@lid`.
- Живая форма значения от реального сервера (`<digits>:<device>@s.whatsapp.net`) прочитанным кодом не доказывается `[ASSUMED]` (A2 в журнале допущений); проверяется ручным обходом.

**Где `creds` в момент ответа `/status`.** `useMultiFileAuthState(sessionDir)` читает `creds.json` в память (`use-multi-file-auth-state.js:87`: `const creds = (await readData('creds.json')) || initAuthCreds();`), `saveCreds` пишет его же (`:116-117`). Сокет мутирует тот же объект: `Object.assign(creds, update);` (`socket.js:855`). Публичный доступ — геттер `get user() { return authState.creds.me; }` (`socket.js:931-932`). В `wa_worker/index.js` `authState` в состояние сессии не сохраняется (в объекте `sessionState`, `index.js:229-243`, только `sock`, `saveCreds` и флаги), зато есть `session.sock` → **читать `session.sock.user` в обработчике `GET /api/sessions/:id/status`** (`index.js:746-762`; сегодня отвечает `{ connected: session.isConnected, exists: true, syncState: session.syncState }`). Пока `isConnected` истинно, `creds.me` уже заполнен (сопряжение случилось до рестарта соединения, `creds.json` сохранён) `[ВЫВОД]`.

**Побочное наблюдение о приватности (не часть фазы).** Baileys сам пишет `me` на уровне `info`: `logger.info({ me: updatedCreds.me, platform: updatedCreds.platform }, 'pairing configured successfully, …')` (`socket.js:734`) и `{ myPN, myLID }` (`socket.js:~778`). В воркере этот журнал — `baileysLogger = pino({ level: process.env.BAILEYS_LOG_LEVEL || 'warn' })` (`wa_worker/index.js:48`), и `BAILEYS_LOG_LEVEL` нигде в проекте не задаётся `[ЗАМЕР: grep по *.py/*.yml/justfile]`; при `warn` этих строк нет. Гейт приватности называет «журналы сторонних библиотек — Baileys/pino на уровне `warn`» границей средства (`tests/test_phone_privacy_gate.py:~694`). Фаза этого не меняет и **не должна поднимать `BAILEYS_LOG_LEVEL`**.

### A3. Telethon 1.42.0 / TG (D-02)

- `QRLogin.wait()`: после `UpdateLoginToken` запрашивает `ExportLoginToken`, при `LoginTokenMigrateTo` переключает DC и импортирует токен; на `LoginTokenSuccess`: `user = resp.authorization.user` / `await self._client._on_login(user)` / `return user` `[ПРОЧИТАНО: telethon/tl/custom/qrlogin.py:108-116]`. Docstring: «On success, an instance of :tl:`User`». При включённой 2FA `wait()` не возвращает — поднимает `SessionPasswordNeededError` (поэтому в `_wait_for_qr` есть ветка `needs_2fa` и вход идёт вторым путём).
- `sign_in(password=…)`: сначала `me = await self.get_me(); if me: return me` (`client/auth.py:327-329`), затем `CheckPasswordRequest` и `return await self._on_login(result.user)` (`:369`); `_on_login` — `return user` `[ПРОЧИТАНО: client/auth.py:385-407]` (внутри использует `user.id`, `user.bot`, `user.access_hash`, то есть это настоящий `types.User`). Возврат — `User`, как и обещает аннотация `-> 'typing.Union[types.User, types.auth.SentCode]'`.
- **`get_me()` — запрос к серверу при каждом вызове** (`client/users.py:144-174`: `GetUsersRequest([InputUserSelf()])`); кэширован только `input_peer=True`. Значит, получение номера «потом через `get_me()`» — это второй запрос после того, как `complete_auth` уже сделал `disconnect()`, то есть именно «второе подключение» критерия 1. Брать надо `User` из самого ответа входа.
- Форма `User.phone`: `phone: Optional[str]` в `User.__init__` `[ПРОЧИТАНО: telethon/tl/types/__init__.py, класс User]`. Что у **своего** пользователя это цифры без `+` и непустая строка — знание о поведении Telegram, прочитанным кодом не доказывается `[ASSUMED]` (A1 в журнале). Это безопасно по построению: `normalize_reported` принимает и с `+`, и без, а `None`/пусто → `PhoneWrite.UNPARSEABLE`, аккаунт всё равно создаётся.
- Карта сегодняшнего потока `app/messengers/telegram_user.py` (все строки [ПРОЧИТАНО]):

| Место | Что делает | Где теряется `User` |
|---|---|---|
| `:87` `await state.qr_login.wait()` | ждёт сканирования; **возврат отбрасывается** | здесь (QR-путь) |
| `:89-90` | `state.session_string = state.client.session.save()`, `state.status = "success"` | |
| `:196` `await state.client.sign_in(password=password)` | **возврат отбрасывается** | здесь (2FA-путь) |
| `:200-202` | `state.session_string = …save()`, `status = "success"`, `return state.session_string` | |
| `:205-231` `complete_auth` | `_owned` + проверка статуса (`:217`), **`_qr_sessions.pop(session_id, None)` (`:219`)**, затем `await state.client.disconnect()` (`:227`), возвращает `state.session_string` | — |
| `app/pages/accounts.py:437-439` (опрос QR) и `:600-602` (после 2FA) | `session_string = await complete_auth(…)`; `await _save_tg_account(db, user, session_string)` | — |
| `app/pages/accounts.py:302-319` `_save_tg_account` | `db.add(MessengerAccount(user_id=…, type="tg_user", credentials=session_string, status="active"))`, `await db.commit()` | номера нет |

Из-за того, что `QRAuthState` — датакласс с автоматическим `__repr__`, поле с номером **обязано** идти с `repr=False` (иначе любая отладочная печать состояния выводит номер).

## Интеграционные точки в репозитории (часть B)

### B3. Мастер TG: куда несётся `User` без нового `await`

Инвариант: `complete_auth` проверяет `_owned` и статус, `pop` идёт **сразу следом** (`telegram_user.py:216-219`), и между ними нет `await`. Номер снимается с `state` тем же синхронным блоком: после `pop`, до `await state.client.disconnect()` (`:227`). Формируется неизменяемый результат `QrAuthResult(session_string, phone)`; из двух конкурентных вызовов состояние снимает ровно один, номер получает он же (второй вернёт `None`, как сегодня). Существующие тесты гонки (`tests/test_routes/test_tg_user_auth.py:1272-1326`, «Два конкурентных верных пароля — ОДИН аккаунт; строка берётся из `complete_auth`») остаются верными и обязаны остаться зелёными.

Единственный потребитель возврата `complete_auth` в приложении — два обработчика выше; в тестах `complete_auth` **не подменяется** (`patch("app.pages.accounts.complete_auth")` в дереве нет `[ЗАМЕР: grep]`), его настоящий возврат проверяет один тест: `tests/test_messengers/test_telegram_user.py:391-399` (`assert result == "saved_session_123"`) — его придётся изменить сознательно вместе с контрактом (рекомендация: возврат `QrAuthResult | None`, а не второй функции-двойник `pop`).

### B4. Опрос статуса WA/MAX сегодня

`accounts_connect_wa_status` (`app/pages/accounts.py:724-773`) и `accounts_connect_max_status` (`:968-1019`) устроены одинаково: пользователь → строка `connecting` своего типа (`scalar_one_or_none`) → `messenger = …Messenger(session_id=str(account.id))` → `is_connected = await messenger.check_connection()` (`:749`, `:994`) → при `True`: `account.credentials = session_id` (`:751`, `:996`), `account.status = "syncing"` (`:752`, `:997`), `await db.commit()`, затем `celery.send_task("app.worker.tasks.sync_wa_groups" | "…sync_max_groups", args=[account.id])` (`:757`, `:1002`) и ответ «Подключено». Любое исключение внутри `try` ловится общим `except Exception` и превращается в уведомление «Ошибка соединения…» — **значит, исключение захвата номера внутри этого `try` не должно пролететь**, иначе строка останется `connecting` и опрос повторится вечно (нарушение D-05). Тестов на эти два обработчика в дереве нет (только ссылки на их адреса в `test_htmx_inventory.py:496`, `test_max_connect_transport.py:102`) — тесты фазы пишутся с нуля; подмена по образцу `test_max_connect_transport.py`: `patch("app.pages.accounts.MaxMessenger")` / `WhatsAppMessenger` и подмена `celery.send_task` (импорт внутри функции: `from app.worker.celery_app import celery`).

Адаптеры (`app/messengers/whatsapp.py:136-143`, `max.py:126-133`): `check_connection` делает `GET {bridge}/api/sessions/{id}/status` и возвращает `response.status_code == 200 and response.json().get("connected", False)`; при исключении — `warning("check_connection_failed", error=str(e))` и `False`. Узкий путь добавить `phone`: **метод `get_own_phone()`** в обоих адаптерах (общий для обоих разбор тела — маленькая чистая функция, например в `app/messengers/base.py`): второй `GET …/status`, `None` на любое отклонение (не 200, не JSON-объект, поля нет, тип не строка/число, исключение), значение в журнал не пишется (только `phone_set`). Обработчик зовёт его **только после** `is_connected` и **до** `status = "syncing"`, и фиксирует всё одним коммитом (D-01). Отказ второго `GET` = «номер неизвестен», подключение идёт.

Что трогала Фаза 18: в `accounts.py` — только `:1051`, конструктор `AccountRow(account_id, view.messenger_type, view.phone, view.phone_is_manual)` во фрагменте опроса синхронизации (коммит `b9073138`) `[ПРОЧИТАНО: git log]`; больше фаза в файле ничего не меняла — Фаза 19 правит его без конфликта с ней.

### B5. `/status` воркеров сегодня

- **WA** (`wa_worker/index.js:746-762`): без сессии — `res.json({ connected: false, exists, syncState: null })` (`exists = sessionExistsOnDisk()`); с сессией — `res.json({ connected: session.isConnected, exists: true, syncState: session.syncState })`. Обработчик синхронный (`(req, res) =>`).
- **MAX** (`max_worker/main.py:989-1005`): без сессии — `{"connected": False, "exists": exists, "syncState": None}`; с сессией — `{"connected": session.is_connected, "exists": True, "syncState": session.sync_state}`. `SessionState.phone` (`main.py:211`) — это номер **из формы**, он `/status` отдавать не должен: иначе приложение примет «ввёл A» за «MAX сообщил A», и сценарий «ввёл A, отсканировал B» потеряет смысл.
- Единственное место, где `is_connected` становится `True`, — `on_start` (`main.py:461`) `[ЗАМЕР: grep is_connected]`; поэтому **гонки D-15 для MAX нет**: к моменту, когда `/status` ответит `connected: true`, `client.me` уже присвоен (см. A1), и номер, захваченный в `on_start` до `is_connected = True`, уже лежит в `SessionState`. Для WA аналогично — `creds.me` готов раньше `isConnected`.
- Добавление поля `phone`: `{"connected", "exists", "syncState", "phone"}` — строка цифр или `null`; старый образ ключа не имеет, и `body.get("phone")` читает его как `None` без ветвления (D-14, D-05). Ответ «нет сессии» поля `phone` не несёт — приложению он не нужен.

### B6. Форма MAX (D-09 / D-10)

`accounts_connect_max_start` (`app/pages/accounts.py:854-964`): `submitted = form.get("phone") or ""` (`:892`), `phone = submitted.strip()` (`:893`), `if not phone:` → `respond_field_error(request, page=_page, fragment=_fragment)` с `MAX_EMPTY_PHONE_ERROR = "Введите номер телефона"` (`:825`, использование `:907`, `:915`); далее существующий «connecting» MAX-аккаунт переиспользуется (`account.credentials = phone`, `:930`) либо создаётся (`credentials=phone`, `:936`), `messenger.start_session(phone=phone)` (`:950`), пять секунд ожидания, QR. Шаблон `app/templates/accounts/includes/max_connect_step.html` — поле `{{ field(name="phone", label='Номер телефона', type='tel', value=phone or '', placeholder='+7 999 123-45-67', required=true, autocomplete='tel') }}`; ошибка рисуется `alert(error)` над карточкой, а не под полем; макрос `field` умеет `hint=` (`components/field.html`, подпись `hint=None`).

**Кто закрепляет `MAX_EMPTY_PHONE_ERROR` [ЗАМЕР: grep по `*.py`, `*.html`, `*.md`, `*.json`, без каталогов фаз 10–18 в `.planning`]:**
- код: только `app/pages/accounts.py:825, 907, 915`;
- тесты: **один** — `tests/test_pages/test_max_connect_transport.py:35` объявляет **свой литерал** `EMPTY_PHONE_ERROR = "Введите номер телефона"` (не импорт константы) и проверяет его вхождением подстроки (`:147`, `:170`) и подаёт в `_max_step_markup` напрямую (`:195`). `PHONE_ERROR_BLANK` («Введите номер телефона. Пример: +7 999 123-45-67») этот литерал **содержит как префикс**, поэтому замена текста на `PHONE_ERROR_BLANK` оба вхождения-подстроки не красит;
- реестров уведомлений (`app/pages/notices.py`) и гейтов, перечисляющих тексты ошибок поля, у константы нет; планы фаз 11/13/14 в архиве `.planning/milestones` — документы, не тесты.
Рекомендация (решает планировщик): единая ветка `try: e164 = normalize_manual(submitted) / except PhoneError as exc: error = str(exc)` — пустой ввод сам даёт `PHONE_ERROR_BLANK` (контракт `normalize_manual("")`, `tests/test_services/test_phone.py:661-662, 1256`), константу `MAX_EMPTY_PHONE_ERROR` удалить, а литерал `tests/test_pages/test_max_connect_transport.py:35` заменить импортом `PHONE_ERROR_BLANK`. Структура гейтов ответа требует, чтобы сборщики оставались **вложенными функциями, поданными `respond_field_error` по имени** (`page=_page`, `fragment=_fragment`; не лямбды) и вызов был один — тогда ни одно объявленное число гейта `test_htmx_gates.py` не двигается `[ПРОЧИТАНО: _fragment_builder_names, test_htmx_gates.py:~4833]`.

**Побочный эффект D-09 на существующие тесты:** `test_a_hostile_phone_never_reaches_the_response_raw` (`test_max_connect_transport.py:209`) постит `HOSTILE_PHONE` на старт, ждёт «ветку старта». После D-09 это значение даст **422** с эхом в поле; проверка «сырых» меток остаётся истинной (автоэкранирование макроса `field`), но докстринг и сам смысл теста меняются — тест надо перечитать и подправить, а не оставить зелёным вакуумом. Остальные тесты, постящие `+79990001122` / `+79991234567` (`test_max_connect_transport.py:88, 113, 239`, `test_htmx_preserved.py:431`, `test_htmx_post_pairs.py:972, 983`), проходят `normalize_manual` `[ЗАМЕР: normalize_manual("+79990001122") → +79990001122]`.

**Где живёт введённый номер между POST и опросом (D-10), варианты:**
1. **`account.credentials` (рекомендуется).** Уже существует (сегодня там сырая строка). Предлагается класть туда **нормализованный** E.164 (`normalize_manual` → `+79990001122`), потому что опросчик читает его строгим `normalize_reported`, а строка «`+7 999 123-45-67`» им отвергается. `credentials` для MAX больше нигде не читается (читает его только `messenger_factory` для `tg_user`; `[ЗАМЕР: grep \.credentials app/]`), затирается `session_id` в том же коммите, что `syncing`. Плюс: ноль правок воркера, работает и со старым образом. Минус: колонка перегружена; legacy-строка `connecting` с сырым значением просто не даст запаса (нормализатор вернёт `None`), без ошибки.
2. **Воркер: `phone.txt` → `/status.phone`.** Номер уже лежит в `phone.txt` и в `SessionState.phone`; воркер вернул бы его как запас. Минус: воркер сам решает «чей номер», размывает D-14 («воркер номер не форматирует»), приложению нельзя отличить «MAX сообщил» от «взято из формы», а старый образ запаса вообще не даст — см. Open Question 1.
3. **Отдельное поле/таблица.** Миграция ради одной строки на время подключения — несоразмерно.

Журналы: ни `credentials`, ни `phone.txt` не пишутся в журнал (гейт приватности отдельно называет `PHONE` в окружении контейнера и `phone.txt` границей средства: `tests/test_phone_privacy_gate.py:~696-699`, «отложено (CONTEXT §Deferred, кандидат в бэклог)»); фаза эту границу не расширяет.

### B7. Контракт писателя Фазы 16 — как сегодня

Файл `app/application/accounts/phone.py` (241 строка) прочитан целиком. Что требует каждый вызов и что возвращает `[ПРОЧИТАНО]` + прогон `[ЗАМЕР: /home/orca/.claude/jobs/46358bbc/tmp/probe/tg_probe.py на in-memory SQLite]`:

| Вызов | Требует от вызывающего | Возвращает |
|---|---|---|
| `record_reported_phone(session, account, raw)` | объект **уже в сессии** (`session.add` сделан): первой строкой `if inspect(account).session is not session.sync_session: raise ValueError(ACCOUNT_NOT_IN_SESSION)` (до нормализации); строка может быть ещё `pending` — писатель сам делает `flush()` (`if inspect(account).pending: await session.flush()`), вставка и условный `UPDATE` идут внутри; **коммитит вызывающий** | `WRITTEN` на `79991234567` / `"79991234567"` / `"+79991234567"` (колонка `+79991234567`, `phone_is_manual=False`, значение зеркалится на объект `set_committed_value`); `UNPARSEABLE` на `None`, `""`, `"garbage"` (к базе не обращался); `KEPT`, если номер уже есть/ручной; `ValueError(ACCOUNT_NOT_IN_SESSION)` на любом входе, если объект не в сессии |
| `fill_reported_phone(session, account_id, raw)` | только `account_id` существующей строки; сессия может нести другие несброшенные изменения (`flush()` внутри, вне разрешения); **коммитит вызывающий**; владельца не проверяет | `UNPARSEABLE` на мусоре (без обращения к базе), `WRITTEN`, `KEPT` (номер уже есть или ручной), `MISSING` (строки нет) |

Сквозной прогон на тех же входах: запись `+79991234567` без признака «ручной»; второй вызов поверх известного → `KEPT`; `None` поверх известного — номер не тронут (`UNPARSEABLE`). Фраза «пустое значение никогда не пишется поверх известного» гарантирована **двумя** слоями: нормализатор не пропускает пустоту, а условие UPDATE (`phone IS NULL AND phone_is_manual IS false`) не тронуло бы строку и так.

**Ограничение для тестов и сидов.** Защита `phone_guard` отказывает на исполнении любому присваиванию колонок номера вне `writer_scope()` (в том числе аргументу конструктора `MessengerAccount(phone=…)`): в тестах номер сеют `tests/account_label_support.py::seed_account(session, user_id, type_, *, phone=…, manual_phone=…, stored_as_is=…, status=…, account_id=…)`.

### B8. `justfile`

`[ПРОЧИТАНО: justfile:104-130, 136-138, 149-151]` и `[ЗАМЕР: just --dry-run]`:
- `prod-hard-deploy:` — `git pull && docker compose -f docker-compose.prod.yml build --no-cache && just max-worker-build --no-cache && docker ps -q --filter "label=broadcaster.role=wa-worker" | xargs -r docker stop && …` (затем остановка/удаление контейнеров `wa-worker`, затем `max-worker`, `docker compose … down && … up -d`);
- `prod-deploy:` — то же без `--no-cache`, с `just max-worker-build &&`;
- `prod-build:` — `docker compose -f docker-compose.prod.yml build && just max-worker-build`;
- `wa-worker-build:` — **без аргументов**: `docker build -t broadcaster-wa-worker:latest ./wa_worker` (вывод `just --dry-run wa-worker-build`: ровно эта строка);
- `max-worker-build *args:` — `docker build {{ args }} --build-arg MAX_WORKER_BUILD_REVISION="$(git rev-parse HEAD)" -t broadcaster-max-worker:latest ./max_worker`.
Образы воркеров строит **только** `docker build` отдельными рецептами, compose их не строит; имена образов — `WA_WORKER_IMAGE = "broadcaster-wa-worker:latest"` (`app/services/wa_container_manager.py:13`), `MAX_WORKER_IMAGE = "broadcaster-max-worker:latest"` (`max_container_manager.py:13`). Поэтому `--no-cache` у hard-варианта для WA возможен только после изменения рецепта на **`wa-worker-build *args:`** с `docker build {{ args }} -t broadcaster-wa-worker:latest ./wa_worker` (по образцу MAX).

**Тест «машинно» уже существует для MAX** — `tests/test_max_worker_deployment.py` (5 тестов, `[ЗАМЕР: 5 passed]`) разбирает `just --dry-run <рецепт>` и проверяет порядок: `dry_run(recipe)` (`:12-19`), `assert_max_build_precedes_worker_teardown` (`:22-25`: `output.index("just max-worker-build")` меньше `output.index('label=broadcaster.role=max-worker')`), `test_prod_deploy_builds_max_image_before_any_dynamic_worker_teardown`, `test_prod_hard_deploy_rebuilds_max_image_without_cache_before_teardown` (требует `"just max-worker-build --no-cache" in output`). Для WA — зеркальные три теста: `prod-deploy` содержит `just wa-worker-build` раньше первой подстроки `label=broadcaster.role=wa-worker`; `prod-hard-deploy` содержит `just wa-worker-build --no-cache` раньше неё же; `dry_run("wa-worker-build --no-cache")` (или рецепт с аргументом) даёт `docker build --no-cache -t broadcaster-wa-worker:latest ./wa_worker`. `just` стоит на машине (`just 1.45.0`). Ловушка: остановка WA-контейнеров идёт **раньше** остановки MAX-контейнеров, поэтому для WA «до остановки» значит раньше строки `label=broadcaster.role=wa-worker`.

### B9. Гейты приватности и единственного писателя: что они судят

`[ПРОЧИТАНО: шапки гейтов]` + `[ЗАМЕР: 1161 passed in 63.42s]` на базе (три модуля вместе):
- **`tests/test_application/test_phone_single_writer_gate.py`** — вселенная **`app/**/*.py` и `scripts/**/*.py`**, обходом каталогов; **`max_worker/`, `alembic/` и `tests/` вне вселенной** (шапка: «`max_worker/` — пишет `phone` … в память процесса, а не в базу»; правило `test_the_walk_leaves_max_worker_alembic_and_tests_outside`, `:9097`). `wa_worker/` не упомянут (JS). Судит **формы записи в колонку**; вызов `record_reported_phone` / `fill_reported_phone` / `set_manual_phone` формой записи не является (см. Фазу 18). Списка допущенных вызывающих писателя в гейтах нет `[ЗАМЕР: grep record_reported_phone в tests/ — пусто]`; для воркеров писатель в базу не обращается вообще.
- **`tests/test_phone_privacy_gate.py`** — `GATE_TREES = ("app", "scripts", "wa_worker", "max_worker")`, `PYTHON_TREES = ("app", "scripts", "max_worker")`, `JS_TREES = ("wa_worker",)` (`:826-830`). То есть **оба воркера под гейтом**, Python-половина судит `max_worker/main.py`, JS-половина — все `.js` под `wa_worker/` без `node_modules`. Но он **именной**: в Python краснит имя с `phone` (кроме `phone_set` булевой формы) и аргументы вызова журнала; в JS — идентификатор кода аргументов вызова `log|console|logger|baileysLogger.*(` с `phone`, литерал, похожий на номер, и носители `sock.user` / `creds.me` (в том числе `state.creds.me`) внутри аргументов. **Чего он не видит** (дословно названо в шапке): значение, пришедшее в журнал без имени `phone` («`logger.info("x", value=v)`, где `v` — номер»), журналы сторонних библиотек, `PHONE` в окружении контейнера и `phone.txt`; маска приложения `log_masking.py` на контейнер `max_worker` (свой журнал) и `wa_worker` не распространяется.
- **Вывод для планировщика `[ВЫВОД]`:** `log.info("…", own=me.contact.phone)` в воркере будет найдено (имя `phone` в выражении), а `log.info("…", n=digits)` — **нет**. Поэтому: (а) называть переменные номера с `phone` в имени и не передавать их в журнал вообще; (б) в плане воркера MAX и воркера WA добавить тест «захват не пишет число в журнал» (захват номера на известном значении; `caplog` / перехват `log.*` — значения нет ни в одной записи); (в) ревью-пункт: ни `err.message`, ни `str(e)` захвата не должны нести значение. Расширять сам гейт не требуется.

### B10. Тестовая инфраструктура воркеров

- **MAX:** `tests/test_worker/test_max_worker.py` импортирует настоящий `max_worker.main` через фикстуру `worker` (`importlib.import_module("max_worker.main")` с `ACCOUNT_ID=42`, `SESSIONS_DIR` во временном каталоге, сброс `module.session = None` и т. д.); `install_fake_client(monkeypatch, worker)` подменяет `WebClient` на `FakeWebClient` — у него **нет атрибута `me`** (`FakeWebClient.__init__` задаёт `chats`, `start_handler`, `start`, `close`, `fetch_chats`, `send_message`). `create_client` проверяется как `state = await worker.create_client(...)`, затем `await client.start_handler(client)` (`test_create_client_uses_webclient_contract`, `:345-358`). Следствие: **вспомогательная функция разбора обязана выдерживать клиента без `.me`** (`getattr(client, "me", None)`), иначе поломаются существующие тесты. Для нового теста достаточно `client.me = SimpleNamespace(contact=SimpleNamespace(phone=79991234567))`, затем `await worker.get_session_status("42")` (сопрограмма, `main.py:990`).
- **WA:** тестов `wa_worker` в дереве **нет** (`package.json` — только `"start": "node index.js"`, раннера нет; в `tests/` на `wa_worker` ссылаются лишь `conftest.py`, гейты и два чужих модуля). Зато есть `tests/conftest.py::run_node_script(source) -> dict` (`NODE_BIN = "node"`; исполняет `node -e <source>`, вердикт — последняя строка stdout как JSON; отсутствие Node — `pytest.fail`, **пропуск запрещён**), её уже используют `tests/test_templates/test_components.py`, `tests/test_pages/test_shell.py`, `tests/test_pages/test_hx_location_destinations.py`. Рекомендуемый минимум: **чистая функция в отдельном модуле** `wa_worker/own_phone.js` (в `index.js` нельзя: `main()` вызывается при импорте, `index.js:998` — `main().catch(…)`), без импорта Baileys на верхнем уровне (локально `node_modules` пуст, пока не сделан `npm ci`) и с внедрением `{ isPnUser, jidDecode }`; `index.js` передаёт настоящие функции Baileys. Тест — `tests/test_worker/test_wa_worker_own_phone.py` через `run_node_script`: `import("file:///…/wa_worker/own_phone.js")` (динамический `import()` работает из `node -e`, пакет `wa_worker` помечен `"type": "module"`) `[ЗАМЕР: эскиз на пробе /home/orca/.claude/jobs/46358bbc/tmp/probe/esm: четыре входа PN-с-устройством / PN-без-устройства / LID / пусто → "79991234567", "79991234567", null, null; проба шла на ПОДСТАВНЫХ `isPnUser`/`jidDecode`, повторяющих прочитанное тело rc14, а не на настоящем Baileys]`. Чтобы подмены не разошлись с настоящими функциями, добавить два закрепляющих правила: (1) `package.json` пинует ровно `7.0.0-rc14` (смена пина краснит тест и заставляет перечитать контракт); (2) ссылка на проверенный исходник `jid-utils.js:30-58, :65` в докстринге теста. Ловушка: `run_node_script` печатает вердикт последней строкой — гарнир JS не должен печатать номер.
- Прогон: RED-улика — `--junit-xml` pytest принимается верифицирующим глаголом напрямую (память `red-evidence-verb-wants-node-tap`).

### B11. Сквозные гейты (текущие объявленные числа и почему они не сдвинутся)

`[ЗАМЕР: grep констант]`: `OOB_BLOCKS = 25` (`tests/test_templates/test_htmx_markup_gates.py:2677`), `WRITE_FORM_PLACES = 50` (`tests/test_templates/test_form_inventory.py:176`), `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 26` (`tests/test_pages/test_htmx_gates.py:2353`), `PUSH_URL_DECISIONS_DECLARED = 38` (`:6969`), `TRANSITION_BRANCH_HANDLERS_DECLARED = 32` (`:6713`), `MUTATING_ROUTE_COUNT = 50` и `MUTATING_MODULE_COUNT = 14` (`tests/test_pages/test_impersonation_gate.py:125, 138`), `PAIRED_302_ASSERTIONS_DECLARED = 193` (`tests/test_pages/test_htmx_post_pairs.py:3490`). **Фаза 19 не добавляет ни POST-маршрута, ни `<form>`, ни кода реестра уведомлений, ни OOB-блока** (D-09: «Новой формы и нового маршрута нет»; D-12: шаг «подключено» без номера), поэтому ни одно из этих чисел не двигается `[ОЦЕНКА: прототип правок не собирался, в отличие от Фазы 18 — числа выведены из того, что каждая константа считает]`. Что именно проверять в каждом плане и что может сдвинуть число, если исполнитель отступит от рекомендации:
- `test_htmx_post_pairs.py` — записи для `accounts_connect_max_start` (строки `972`, `983`) шлют `{"phone": "+79990001122"}` (проходит `normalize_manual`); сдвинется, только если в этом файле добавят 302-утверждения.
- `test_htmx_gates.py` — обработчик `accounts_connect_max_start` объявлен «дуальным» (`DUAL_BRANCH_HANDLERS`, `PUSH_URL_CASE_THREE`); сохраняйте фрагмент и переход как были; новый `Response`/`RedirectResponse` в теле обработчика мимо слоя потребует записи в перечне расхождений.
- `test_impersonation_gate.py` — `accounts_connect_max_start` уже в `ALLOWED_ROUTES` (`:245`, «подключение аккаунта»); GET-опросчики статуса в перечне изменяющих маршрутов не числятся, **но** `test_money_perimeter_gate.py:170-179` держит их в `HOLD_NOT_BUILT_YET` (опрос ставит Celery-задачу без удержания) — запись остаётся верной, не менять.
- `test_notices_registry.py` — затрагивается, только если форма MAX получит **код уведомления**; подсказка под полем (`hint=`) реестра не касается.
- `tests/test_templates/` — подсказка `hint=` в `max_connect_step.html` не меняет число `<form>`; `test_responsive_markup.py:1180-1182` закрепляет `action="/accounts/connect/max/start"` и `method="POST"` — не менять.
- `tests/test_planning/` — гонять явно (память `orchestrator-gate-catches-records-defects`): число планов в реестре запретов `test_plan_prohibitions_census.py` реагирует на новые планы фазы с `prohibitions` — планировщик прогоняет модуль после записи планов и правит числа так, как это делали Фазы 16–18 `[ЗАМЕР: база — 218 passed, 2 skipped за 20 с]`.

### B12. D-08: тесты вокруг `check_connection()` TG

Существующие: `test_check_connection_success` (`tests/test_messengers/test_telegram_user.py:331-334`: `messenger.client.get_me = AsyncMock()` → `True`), `test_check_connection_failure` (`:337-339`: `get_me` бросает → `False`), `test_check_connection_logs_warning_on_failure` (`:831-840`). Дефект: `get_me()` на **неавторизованном** клиенте возвращает `None` без исключения (`client/users.py:144-149`, «If the user has not logged in yet, this method returns `None`»), а `check_connection` на `None` отвечает `True`; ни один существующий тест этого случая не фиксирует. **Как не закрепить дефект:** тесты Фазы 19 не вызывают `TelegramUserMessenger.check_connection()` вообще (мастеру TG она не нужна), не добавляют кейс `get_me → None ⇒ True` и не называют «подключён» то, что на деле отозванная сессия. Критерий «второго подключения нет» формулируется на **мастере**, а не через `check_connection`: фабрика клиента Telethon в `tests/test_routes/test_tg_user_auth.py` вызвана один раз, `client.connect` ждался один раз (из `start_qr_auth`), `client.get_me.assert_not_called()` (клиент там `MagicMock`, `get_me` — авто-мок). Рядом положить комментарий-тропу: «чинить `check_connection()` вне вехи (CONTEXT, Deferred)».

## Architecture Patterns

### System Architecture Diagram

```
 ПОЛЬЗОВАТЕЛЬ                                          ВОРКЕРЫ / МЕССЕНДЖЕРЫ
 ───────────                                           ─────────────────────
 TG: QR / пароль 2FA ──► accounts_connect_tg_user_qr_status / _verify_2fa (accounts.py:388, :529)
                          │  state = _owned(...)                          ┌───────────────┐
                          │                                               │ Telegram API  │
 start_qr_auth ──────────────────────────────────────────────────────────►│ qr_login.wait()│──► User
 (telegram_user.py:57)    │  _wait_for_qr: user = await qr_login.wait()   │ sign_in(pw=)  │──► User
                          │     └─ state.own_phone = reported_phone_of(user)  └───────────────┘
                          │  complete_auth: check ─► pop (БЕЗ await) ─► QrAuthResult(session_string, phone)
                          ▼
                    _save_tg_account(db, user, result)
                          │  db.add(MessengerAccount(...status="active"))
                          │  record_reported_phone(db, account, result.phone)  ◄── писатель Фазы 16
                          └─ db.commit()   (номер и status="active" — один коммит)

 WA / MAX: опрос #wa-status / #max-status каждые 3 с
        ▼
 accounts_connect_{wa,max}_status  ──► check_connection() ──► GET /api/sessions/{id}/status ─► {connected, exists, syncState, phone?}
        │ connected                                                      ▲                     (wa_worker/index.js:746, max_worker/main.py:990)
        ├─► get_own_phone()  ──► GET /status ─► body.get("phone") ─► str | None   wa: own_phone.js ◄ sock.user (isPnUser+jidDecode)
        │                                                              max: SessionState.own_phone ◄ on_start ◄ client.me.contact.phone
        ├─► MAX: entered = normalize_reported(account.credentials)   (форма, нормализована при POST)
        ├─► try/savepoint: fill_reported_phone(db, id, reported)  ─UNPARSEABLE─► fill_reported_phone(db, id, entered)
        └─► account.credentials = session_id; account.status = "syncing"; commit ─► celery sync_*_groups
                                      (сбой захвата ─► журнал: account_id, без значения; подключение идёт)
 MAX форма: POST /accounts/connect/max/start ─► normalize_manual(phone) ─ok─► credentials = E.164 ─► start_session(phone=E.164) ─► QR
                                                              └─PhoneError─► respond_field_error (422, поле сохраняет ввод)
```

### Recommended Project Structure
```
app/messengers/telegram_user.py     # QRAuthState.own_phone (repr=False), reported_phone_of(user), QrAuthResult, complete_auth -> QrAuthResult | None
app/messengers/base.py              # reported_phone_from_status(body) — общий чистый разбор тела /status (по желанию)
app/messengers/{whatsapp,max}.py    # get_own_phone()
app/pages/accounts.py               # _save_tg_account(result); обёртка захвата WA/MAX; форма MAX через normalize_manual
app/application/accounts/           # (по желанию) capture-помощник: «reported, затем entered» поверх fill_reported_phone
wa_worker/own_phone.js              # NEW: ownPhoneFromMe(me, { isPnUser, jidDecode }) — чистая функция
wa_worker/index.js                  # import isPnUser, jidDecode; /status добавляет phone
max_worker/main.py                  # own_phone_of(client), SessionState.own_phone, захват в on_start, /status добавляет phone
justfile                            # wa-worker-build *args; prod-deploy / prod-hard-deploy вызывают его
tests/test_worker/test_wa_worker_own_phone.py   # NEW (run_node_script)
tests/test_pages/test_connect_phone_capture.py  # NEW: WA/MAX опросчики + форма MAX
```

### Pattern 1: TG — номер из того же `pop`, без нового `await`
**What:** захват в двух местах входа, считывание — в `complete_auth` синхронно после `pop`, запись — в `_save_tg_account` через `record_reported_phone`.
**Example:**
```python
# Источник: прочитанные Telethon 1.42.0 (qrlogin.py:108-116, auth.py:327-369) и app/messengers/telegram_user.py:205-231
@dataclass(frozen=True)
class QrAuthResult:
    session_string: str
    phone: str | None = field(default=None, repr=False)   # номер не должен печататься отладкой

def reported_phone_of(user: object) -> str | None:
    """Чистая и тотальная: на моках тестов (`.phone` — не строка) и на None отвечает None."""
    phone = getattr(user, "phone", None)
    return phone if isinstance(phone, str) and phone else None

# QRAuthState: own_phone: str | None = field(default=None, repr=False)
# _wait_for_qr:   user = await state.qr_login.wait(); state.own_phone = reported_phone_of(user); ...
# submit_2fa:     user = await state.client.sign_in(password=password); state.own_phone = reported_phone_of(user)
# complete_auth:  state = _owned(...); if not state or state.status != "success": return None
#                 _qr_sessions.pop(session_id, None)            # <-- между проверкой и pop нет await
#                 result = QrAuthResult(state.session_string, state.own_phone)   # синхронно, до disconnect()
#                 ... await state.client.disconnect() ...; return result  (None, если нет session_string, как сегодня)

# app/pages/accounts.py
async def _save_tg_account(db, user, result: QrAuthResult) -> None:
    account = MessengerAccount(user_id=user.id, type="tg_user", credentials=result.session_string, status="active")
    db.add(account)                                   # писатель требует объект в сессии
    outcome = await record_reported_phone(db, account, result.phone)   # flush + условный UPDATE
    structlog.get_logger().info("tg_phone_captured", account_id=account.id, outcome=outcome.value)  # id есть после flush
    await db.commit()                                 # номер и status="active" — один коммит (D-01)
```
Если `outcome` — `UNPARSEABLE`, `record_reported_phone` строку не сбрасывал и `account.id` может быть `None`; перед журналом сделать `await db.flush()` или журналировать после коммита (в проекте `expire_on_commit=False`, `app/database.py:85`, поэтому `account.id` читается и после коммита).

### Pattern 2: WA/MAX — захват в обёртке, которая не роняет подключение
**What:** опросчик читает номер только после `connected`; всё, что связано с номером, — в защитной обёртке: сбой → запись в журнал без значения, а `syncing` и Celery идут как обычно.
**Example (эскиз, измерен на in-memory SQLite: `/home/orca/.claude/jobs/46358bbc/tmp/probe/sp_probe.py`):**
```python
async def capture_connect_phone(db, account_id: int, reported: object, entered: object = None):
    try:
        async with db.begin_nested():                       # сейвпоинт: сбой не отравляет внешнюю транзакцию
            outcome = await fill_reported_phone(db, account_id, reported)
            if outcome is PhoneWrite.UNPARSEABLE and entered is not None:
                outcome = await fill_reported_phone(db, account_id, entered)   # запас: номер из формы
        return outcome
    except Exception:
        structlog.get_logger().warning("phone_capture_failed", account_id=account_id)   # без str(e) и значения
        return None
# обработчик:  ... if is_connected:
#                    reported = await messenger.get_own_phone()
#                    entered  = account.credentials if account.type == "max" else None   # ДО перезаписи credentials
#                    await capture_connect_phone(db, account.id, reported, entered)
#                    account.credentials = session_id; account.status = "syncing"; await db.commit()
```
`[ЗАМЕР: sp_probe.py]`: `reported=79995554433, entered="+79990001122"` → `WRITTEN`, в колонке `+79995554433` (B побеждает A); `reported=None` → запас → `+79990001122`; писатель, подменённый на падающий, → `('failed','RuntimeError')`, и строка всё равно становится `syncing` (`(3, None, 'syncing')`). `entered` читается строгим `normalize_reported`: при `POST` туда кладётся уже нормализованный E.164 (`+79990001122`), старое сырое значение даёт `UNPARSEABLE` без ошибки.

### Pattern 3: WA — чистая функция с внедрением функций Baileys (TDD-единица)
**What:** `ownPhoneFromMe(me, { isPnUser, jidDecode })`; `index.js` вызывает её с настоящими функциями; сбой любого рода → `null`.
**Example:**
```js
// wa_worker/own_phone.js — без верхнеуровневого импорта Baileys; проверенный контракт: jid-utils.js:30-58 (jidDecode), :65 (isPnUser)
export function ownPhoneFromMe(me, { isPnUser, jidDecode }) {
  try {
    const id = me && me.id;
    if (typeof id !== 'string' || !isPnUser(id)) return null;   // LID, @hosted, пусто -> неизвестен
    const user = jidDecode(id)?.user;                           // НЕ split(':') (D-03)
    return typeof user === 'string' && /^[0-9]+$/.test(user) ? user : null;
  } catch (_) {
    return null;                                                // никогда не бросает в /status
  }
}
// index.js: import makeWASocket, { …, isPnUser, jidDecode } from '@whiskeysockets/baileys';
//           res.json({ connected, exists: true, syncState, phone: ownPhoneFromMe(session.sock?.user, { isPnUser, jidDecode }) });
```
Четыре входа D-03: `79991234567:12@s.whatsapp.net` → `"79991234567"`; `79991234567@s.whatsapp.net` → `"79991234567"`; `123456789012345@lid` → `null`; `""`/`undefined` → `null`. Плюс `{}` / `undefined` как `me`.

### Pattern 4: MAX воркер — чистая функция, защитный захват, поле в `/status`
**Example:**
```python
def own_phone_of(client) -> str | None:
    """int | None из client.me.contact.phone -> '79991234567' | None. Выдерживает клиента без .me (FakeWebClient)."""
    try:
        phone = getattr(getattr(getattr(client, "me", None), "contact", None), "phone", None)
    except Exception:
        return None
    if isinstance(phone, bool) or not isinstance(phone, int) or phone <= 0:
        return None
    return str(phone)
# on_start: state.own_phone = own_phone_of(connected_client)  # В try/except и ДО state.is_connected = True; исключение не должно сорвать ready_event и синк групп
# get_session_status: return {"connected": ..., "exists": True, "syncState": ..., "phone": session.own_phone}
```
`SessionState` получает `self.own_phone: str | None = None`; поле `phone` (форма) воркер наружу не отдаёт.

### Anti-Patterns to Avoid
- **`complete_auth` не трогает, а второй функцией-двойником `pop`.** Два места `pop` — два места держать инвариант; меняется возврат одной функции.
- **`get_me()` для номера TG.** Лишний запрос после `disconnect()` — буквально «второе подключение».
- **`split(':')` по `creds.me.id` и «цифры до `@`».** Берёт цифры LID как номер (измерено ниже).
- **Читать `credentials` формы строгим нормализатором без нормализации при POST.** «`+7 999 123-45-67`» им отвергается (D-09, обоснование).
- **Отдавать `SessionState.phone` (форму) как `/status.phone`.** Сотрёт различие «MAX сообщил / человек ввёл».
- **Захват номера внутри общего `try` опросчика без собственного `except`.** Исключение даёт «Ошибка соединения» и вечный опрос.
- **Тест, подставляющий `phone` в атрибут объекта MessengerAccount или в `__init__`.** `phone_guard` откажет; сеять через `seed_account` / писателя.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Приведение номера к E.164 | свой `re`/`strip('+')` | `normalize_reported` (воркерные источники), `normalize_manual` (форма MAX) | Правила зоны 7, длин и вердиктов `phonenumbers` уже закреплены тестами Фазы 16 |
| Запись в колонку | `account.phone = …`, свой `UPDATE` | `record_reported_phone` / `fill_reported_phone` | Единственный писатель, `phone_guard` и два гейта краснят любую иную запись |
| Разбор JID | `split(':')`, `split('@')` | `isPnUser` + `jidDecode` из Baileys | LID-цифры выглядят как номер: `[ЗАМЕР]` 323 из 2000 случайных 14–15-значных строк проходят `normalize_reported` (форма синтетическая, не реальные LID) |
| Тест JS | свой раннер, `npm install` в тесте | `tests/conftest.py::run_node_script` | Уже есть; `pytest.skip` при отсутствии Node запрещён проектом |
| 422 формы MAX | новый ответ | `respond_field_error(request, page=_page, fragment=_fragment)` | Путь уже существует и учтён гейтами |
| Перенос номера между POST и опросом | новая колонка/таблица | `account.credentials` | Уже есть, затирается тем же коммитом `syncing` |
| Проверка «второго подключения» | счётчик сокетов | `client.get_me.assert_not_called()` + число вызовов фабрики и `connect` | Прямой факт, а не косвенный |

**Key insight:** вся ценность фазы — в **двух швах** (извлечение из ответа мессенджера и вызов писателя); всё между ними уже построено Фазой 16, а любая «своя» запись или «свой» разбор нарушает ровно то, что гейты Фазы 16 охраняют.

## Common Pitfalls

### Pitfall 1: Номер Telegram в `repr` состояния
**What goes wrong:** `QRAuthState` — `@dataclass`; любое поле печатается в `repr`, а `logger.error("…", state=state)` или отладочная печать выводят номер. Гейт приватности этого не увидит (имя без `phone` в журнальном вызове).
**How to avoid:** `own_phone: str | None = field(default=None, repr=False)` и то же у `QrAuthResult.phone`; тест `repr(state)` не содержит цифр номера.

### Pitfall 2: В тестах `.phone` пользователя Telethon — не строка
**What goes wrong:** `_ScannableQRLogin.wait()` возвращает `None`; `client.sign_in = AsyncMock()` возвращает `MagicMock`; `mock_qr_login.wait = AsyncMock()` (`test_telegram_user.py:353`) — тоже. `getattr(mock, "phone")` — тоже `MagicMock`; запись такого «номера» дала бы `UNPARSEABLE`, но без защиты типов `str(mock)` попал бы в нормализатор.
**How to avoid:** `reported_phone_of` принимает только непустую `str`; новые тесты задают пользователя явным `SimpleNamespace(phone="79990001122")` (в `_ScannableQRLogin.wait` — возвращают его).

### Pitfall 3: Сброс `complete_auth` ломает один существующий тест
`tests/test_messengers/test_telegram_user.py:391-399` ждёт `result == "saved_session_123"`. Менять его надо осознанно вместе с контрактом (`QrAuthResult`), а гонки (`test_tg_user_auth.py:1272-1326`) — не трогать: они держат инвариант `pop`.

### Pitfall 4: Исключение в `on_start` MAX срывает подключение
Захват номера стоит в обработчике, который отвечает за `ready_event.set()` и запуск синка групп; исключение до них (например, `AttributeError` на `client.me is None` или на `FakeWebClient` без `.me`) оставляет воркер «инициализирующимся». **How to avoid:** функция `own_phone_of` не бросает; вызов в `try/except`; захват — **до** `state.is_connected = True`.

### Pitfall 5: Старый образ воркера и вечный опрос
Если захват номера выбросит исключение внутри `try` опросчика, пользователь получит «Ошибка соединения…», а строка останется `connecting`. **How to avoid:** собственная обёртка (Pattern 2); тест «`fill_reported_phone` бросает ⇒ всё равно `syncing`, Celery отправлен, номер неизвестен».

### Pitfall 6: Критерии 3 и 4 расходятся на MAX
Форма MAX требует номер (`required=true`), запасной источник — форма, а критерий 4 требует «номер остаётся неизвестен» для старого образа. См. Open Question 1; до ответа планировщик не должен молча выбирать трактовку в тесте.

### Pitfall 7: Эхо враждебного значения теперь достижимо
После D-09 `HOSTILE_PHONE` даёт 422 с эхом в поле (раньше ветка ошибки была достижима только пробелами). Защита — автоэкранирование макроса `field` (`value="{{ value }}"`), текст ошибки — константа (ввод в него не подставляется). Тест `test_a_hostile_phone_never_reaches_the_response_raw` обновить так, чтобы он доказывал именно это и не оставался «зелёным по старой причине».

### Pitfall 8: Число в журнал через переменную без `phone` в имени
Гейт приватности именной (B9). **How to avoid:** тест на журнал (захват с известным номером; в записях `caplog` / вызовах `log.*` нет цифр номера), имена с `phone`, а в исключениях/журналах — только константы и `account_id`. Для JS — не писать `err.message` разбора, не логировать `me` и `sock.user` (гейт краснит оба носителя).

### Pitfall 9: Пин Baileys и расхождение подменённых функций
Тест на подставных `isPnUser`/`jidDecode` честен, пока пин `7.0.0-rc14`. **How to avoid:** правило «`package.json` пинует ровно `7.0.0-rc14`» в том же тест-файле; смена пина краснит его и возвращает к чтению `jid-utils.js`.

### Pitfall 10: Деплой-рецепт: ловушка `--no-cache` и порядка
`wa-worker-build` сегодня не принимает аргументы; добавление `just wa-worker-build --no-cache` без `*args` падает (`just` ругается на лишний аргумент). И сборка обязана стоять **до** остановки контейнеров воркеров (иначе остановка идёт раньше сборки), как у MAX.

### Pitfall 11: Образ WA копирует каталог целиком
`wa_worker/Dockerfile`: `COPY . .` после `npm ci --omit=dev`; `.dockerignore` исключает `node_modules`, `npm-debug.log*`, `.npm`, `sessions`. Новый `own_phone.js` попадает в образ автоматически (нужен там); тестовые файлы — нет, потому что тест лежит в `tests/` вне `wa_worker/`. **Не** класть тесты в `wa_worker/test/` без правки `.dockerignore`.

## Runtime State Inventory

Фаза — не rename/refactor; раздел опущен по правилу шаблона. Единственное «состояние», которое меняется: поле `phone` в ответах `/status` и форма значения в `account.credentials` строк `connecting` MAX (нормализованный E.164 вместо сырого ввода) — строки живут секунды–минуты, строка `connecting` с сырым значением «не даёт запаса», без ошибки.

## Долги, адресованные Фазе 19 вне CONTEXT.md (часть C)

Свёрка `grep -rn "Фаз[ыуеа] 19|Фазой 19|Фазу 19|Phase 19"` по `phases/16-*`, `17-*`, `18-*`, `STATE.md`, `REQUIREMENTS.md`, `ROADMAP.md` дала: десятки упоминаний «мастер Фазы 19» в планах/сводках 16-xx (контракт писателя), 16-CONTEXT:77 и :153, 16-REVIEW (WR-43), 16-VERIFICATION (IN-07), 17-/18-CONTEXT («вне фазы»), `18-CONTEXT.md:199` («`app/pages/accounts.py`: общий с Фазой 19 файл»), `18-01-PLAN.md:406`. В `STATE.md` таблица отложенного называет адресатом «писатели и ревью фаз 17–20 (мастер Фазы 19, скрипт Фазы 20)» только для **принятых границ финального раунда 12** (строка `Phase 16 | Принятые границы…`).

| Долг | Окончательная диспозиция | Доказательство | Для Фазы 19 |
|---|---|---|---|
| **IN-07** (`record_reported_phone` на аккаунте вне сессии отвечал `UNPARSEABLE` на None / `''` / мусоре) | **closed** | `16-VERIFICATION.md` итог `status: passed`, `score: 223/223`; строка «Гэп 4 раунда 2 (IN-07)» (`:~2514`) — «проверка членства до normalize_reported; GREEN `164a0276`». Код: первой строкой `record_reported_phone` стоит `if inspect(account).session is not session.sync_session: raise ValueError(ACCOUNT_NOT_IN_SESSION)` (`phone.py:201`, до `normalize_reported`). `[ЗАМЕР: tg_probe.py]` не-в-сессии + `None` и + `'garbage'` → `ValueError('аккаунт не принадлежит сессии писателя')`; `[ЗАМЕР: pytest tests/test_application/test_account_phone_writer.py → 27 passed]`; тест параметризован `[None, "", "garbage", "79991234567"]` (`:341-342`) | Опора: `_save_tg_account` обязан делать `db.add` до `record_reported_phone`; забытый `add` падает громко на любом входе, в том числе у старого воркера (тест Фазы 19 это не повторяет, он зелёный по контракту) |
| **WR-43** (`autoflush=False` у операторов писателя терял номер на строке, ждущей вставки с известным `id`) | **closed** | Коммиты `73461de8 feat(16): WR-43 — writer flushes the session before its scope`, `c31e077a`, `39c04a34`; код: `_fill_if_unknown` и `set_manual_phone` начинаются с `await session.flush()` перед `writer_scope()`; `record_reported_phone` делает `if inspect(account).pending: await session.flush()` (`phone.py:206`), а не только при `id is None`; тест-трасер `test_a_row_pending_insert_with_a_known_id_is_written` (`test_account_phone_writer.py:537`) на трёх вызовах | Не влияет: мастер TG добавляет объект без явного `id`; опросчики WA/MAX зовут по существующему `id` после коммита |
| `16-CONTEXT.md:77` — гейт единственного писателя обязан не дать Фазам 19/20 обойти модуль | **closed, действует** | `[ЗАМЕР: 1161 passed in 63.42s]` на трёх модулях гейтов; формы записи ловит ещё и `phone_guard` на исполнении (4 линии, `phone_guard.py` шапка) | Фаза 19 только зовёт писателя; гейты зелёные должны остаться, их нельзя «чинить» в плане |
| `16-CONTEXT.md:153` — MAX-подключение кладёт введённый номер в `credentials` и в `start_session(phone=…)` | **измерено, действует (это и есть захват фазы)** | `app/pages/accounts.py:930, 936, 950` | Вариант 1 из B6: класть в `credentials` **нормализованное** значение; `start_session(phone=…)` — тоже нормализованное |
| `16-SECURITY.md` T-16-25 (отсутствие строки выдаётся за «оставлено»; ошибка мастера проходит молча) | **closed** | строка `16-08 \| T-16-25 \| … closed`, мера изменена поздним планом 16-14 | Опирается: `PhoneWrite.MISSING` на удалённой строке и `ValueError` на забытом `add` — разные исходы; тесты Фазы 19 не сворачивают их |
| `16-SECURITY.md` T-16-49 (два отказа писателя называют неверную причину) | **closed** | `16-19 \| T-16-49 \| … closed`; `ACCOUNT_NOT_IN_SESSION` / `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` — две константы (`phone.py:87-89`) | Опирается при отладке мастера TG |
| `STATE.md`: «Принятые границы финального раунда 12» (CR-09, WR-40, IN-29, WR-41, WR-42, форма `raw-dbapi-sql-from-a-parameter`, IN-28) | **open, not load-bearing** | Названы в шапках `phone_guard.py` и `log_masking.py`; решение владельца О-26, суд не расширен | Не мешают: Фаза 19 не пишет сырой SQL, не использует CTE-DML; маска наполовину относится к `app/` логам, а Фаза 19 номер в журнал не кладёт вообще |
| `STATE.md` строка «Phase 16 → Phase 18, IN-01» (пустой ручной ввод) | **closed** (планом 18-02) | `STATE.md:781` «✓ Закрыто планом 18-02» | Не относится к Фазе 19 |
| `16-REVIEW.md` / ревью других фаз: упоминание Фазы 19 как адресата вне перечисленного | не найдено | grep (выше) | — |

**Нет ни одного открытого долга, на который Фаза 19 опирается и который требует решения владельца** (вопросы 1–2 ниже — не долги, а находки этого исследования).

## Волны и планы (рекомендация, D-13)

Файлы-конфликты: **только `app/pages/accounts.py`** (TG-обработчики и WA/MAX-обработчики) — планы 19-01 и 19-05 идут строго друг за другом; `tests/test_pages/test_max_connect_transport.py` правит только 19-05; `tests/test_worker/test_max_worker.py` — только 19-03; остальные файлы планов не пересекаются.

| План | Волна | Тип | Файлы (production) | Файлы (тесты) | Зависит от |
|---|---|---|---|---|---|
| **19-01 TG** (PHONE-12) | 1 | `tdd` | `app/messengers/telegram_user.py`, `app/pages/accounts.py` (`_save_tg_account`, `accounts_connect_tg_user_qr_status`, `accounts_connect_tg_user_verify_2fa`) | `tests/test_messengers/test_telegram_user.py`, `tests/test_routes/test_tg_user_auth.py` | — |
| **19-04 деплой** (PHONE-16) | 2 (D-13; файлы не пересекаются ни с чем, идёт параллельно с 19-02/19-03) | `tdd` (RED: тест `just --dry-run`) | `justfile` | `tests/test_max_worker_deployment.py` (или новый `tests/test_worker_images_deployment.py`) | — |
| **19-02 воркер WA** (PHONE-13, часть PHONE-15) | 2 | `tdd` | `wa_worker/own_phone.js` (new), `wa_worker/index.js` | `tests/test_worker/test_wa_worker_own_phone.py` (new) | — |
| **19-03 воркер MAX** (PHONE-14, часть PHONE-15) | 2 | `tdd` | `max_worker/main.py` | `tests/test_worker/test_max_worker.py` | — |
| **19-05 приложение WA/MAX** (PHONE-13/14/15) | 2 (после 19-01 по `accounts.py`) | `tdd` | `app/messengers/{base,whatsapp,max}.py`, `app/pages/accounts.py` (`accounts_connect_wa_status`, `accounts_connect_max_start`, `accounts_connect_max_status`), `app/templates/accounts/includes/max_connect_step.html`, (по желанию) `app/application/accounts/…` | `tests/test_messengers/test_whatsapp.py`, `test_max.py`, `tests/test_pages/test_max_connect_transport.py`, `tests/test_pages/test_connect_phone_capture.py` (new) | 19-01 |
| **19-06 ручной обход** | 3 (чекпойнт) | `checkpoint:human-verify` | — | UAT в форме фаз 9–10 | 19-01…19-05, деплой |

**TDD-пригодные единицы (чистые, RED → GREEN):** `reported_phone_of(user)` (19-01); `QrAuthResult`/`complete_auth` — возврат и пустое `phone` (19-01); `ownPhoneFromMe` на четырёх входах (19-02); `own_phone_of(client)` и поле `phone` в `/status` (19-03); разбор тела `/status` и `get_own_phone` на форме «новая / старая / мусор» (19-05); функция «reported, затем entered» (19-05); `just --dry-run` для WA (19-04). **Только интеграционные (RED на уровне поведения):** подключение TG по QR и по 2FA от обработчика до `phone` строки; опросчики WA/MAX; форма MAX 422; «сбой захвата не ломает подключение»; ручной обход. `type: tdd` у `app/pages/accounts.py`-планов: память `tdd-review-gate-inert-on-type-execute` — на `type: execute` TDD-гейт инертен, поэтому планы 19-01…19-05 объявлять `type: tdd`.

**Состав ручного обхода (19-06; D-11).** Перед обходом — проверка, что код ветки в web-контейнере (`prod-walkthrough-stand-and-seeding`). Затем `just prod-deploy` (проверяет и критерий 5: оба образа пересобраны и новые контейнеры воркеров стартуют на них). Проверки: **W-1 (MAX, главный вопрос исследования):** подключить живой MAX с номером A в форме и сканировать другим аккаунтом B — какой номер показан (B ⇒ MAX отдаёт `contact.phone` при QR; A ⇒ не отдаёт, работает запас D-10); **W-2:** то же, форма с A и скан тем же аккаунтом; **W-3 (WA):** новый аккаунт показывает номер; если сессия отдала только LID — «Номер неизвестен», не цифры LID; **W-4:** ни один из шагов не показывает «указан вручную». Чего обход измерить не может (и не должен выдавать за измерение): форму `creds.me.id` от реального сервера иначе, чем по результату на экране. Машинная улика обхода — разделом улики, отметки — владельцу.

## Validation Architecture

> `workflow.nyquist_validation` = `true` (`.planning/config.json`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9 + pytest-asyncio (auto-mode), httpx `AsyncClient`, in-memory SQLite `[ЗАМЕР: версии в 18-RESEARCH: pytest 9.0.2, pytest-asyncio 1.3.0, httpx 0.28.1]` |
| Config file | нет раздела настроек прогона (нет `pytest.ini` / `[tool.pytest.ini_options]`), фикстуры в `tests/conftest.py` |
| Quick run command | `uv run pytest <файлы плана> -q -p no:randomly` |
| Full suite command | `just test` — ~5700+ тестов, ~46 мин; только с таймаутом 5400 с и `--durations=15`; исполнители её не гоняют; `tests/test_pages/test_shell.py` кейсы `/accounts/connect/wa` — 90–120 с каждый |

### Phase Requirements → Test Map
| Req / критерий | Поведение | Тип | Автоматическая команда | Файл |
|---|---|---|---|---|
| PHONE-12 / кр.1 | QR-путь: аккаунт `active` и `phone == "+7…"`, `phone_is_manual is False`, один коммит | integration | `uv run pytest tests/test_routes/test_tg_user_auth.py -q -p no:randomly -k "phone"` | ❌ Wave 0 (новые кейсы в существующем файле) |
| PHONE-12 / кр.1 | 2FA-путь: то же; номер от `sign_in(password=)` | integration | тот же | ❌ |
| PHONE-12 / кр.1 | второго подключения нет: фабрика клиента вызвана 1 раз, `client.connect` 1 раз, `client.get_me.assert_not_called()` | integration | тот же | ❌ |
| PHONE-12 / D-02 | `complete_auth`: возврат `QrAuthResult`, номер из того же `pop`; гонки не краснеют | unit + integration | `uv run pytest tests/test_messengers/test_telegram_user.py tests/test_routes/test_tg_user_auth.py -q -p no:randomly` | ✅ править `test_complete_auth` (`:391`) |
| PHONE-12 / D-05 | `reported_phone_of`: `str` → `str`; `None`, `""`, `MagicMock`, число → `None`; вход при мусоре не падает | unit | `uv run pytest tests/test_messengers/test_telegram_user.py -q -p no:randomly -k "reported_phone"` | ❌ |
| PHONE-13 / кр.2 | `ownPhoneFromMe` на 4 входах (PN+dev, PN, LID, пусто) + `me` не объект | unit (JS) | `uv run pytest tests/test_worker/test_wa_worker_own_phone.py -q -p no:randomly` | ❌ Wave 0 (новый файл) |
| PHONE-13 | пин `package.json` = `7.0.0-rc14`; `own_phone.js` не импортирует Baileys на верхнем уровне | unit | тот же | ❌ |
| PHONE-13 / кр.2 | опросчик WA: `get_own_phone` вернул цифры → `phone` строки, `status="syncing"`, один коммит | integration | `uv run pytest tests/test_pages/test_connect_phone_capture.py -q -p no:randomly -k "wa"` | ❌ (новый файл) |
| PHONE-14 / кр.3 | MAX воркер: `client.me.contact.phone=int` → `/status.phone` строкой; `None`/без `.me`/`me=None`/`bool`/`0` → `None` | unit | `uv run pytest tests/test_worker/test_max_worker.py -q -p no:randomly -k "own_phone or status"` | ✅ файл есть, кейсов нет |
| PHONE-14 / кр.3 | «ввёл A, отсканировал B → показан B» и «MAX не отдал → показан A, без пометки» | integration | `uv run pytest tests/test_pages/test_connect_phone_capture.py -q -p no:randomly -k "max"` | ❌ |
| PHONE-14 / D-09 | форма MAX: `8 999 123 45 67` и `+7 999 123-45-67` проходят и пишут `credentials` нормализованным; `abc`, пустое → 422, ввод сохранён, QR не открыт, `start_session` не вызван | integration | `uv run pytest tests/test_pages/test_max_connect_transport.py -q -p no:randomly` | ✅ править (литерал `:35`, `HOSTILE_PHONE`) |
| PHONE-15 / кр.4 | `/status` старой формы (без `phone`): подключение идёт, `status="syncing"`, Celery отправлен, `phone IS NULL`; пустое не пишется поверх известного (сид через `seed_account(phone=…)`) | integration | `uv run pytest tests/test_pages/test_connect_phone_capture.py tests/test_messengers/test_whatsapp.py tests/test_messengers/test_max.py -q -p no:randomly` | ❌ |
| PHONE-15 / D-05 | сбой захвата (`fill_reported_phone` бросает) не ломает подключение: `syncing`, Celery, журнал без значения | integration | тот же файл | ❌ |
| PHONE-16 / кр.5 | `prod-deploy` / `prod-hard-deploy` содержат `just wa-worker-build` (hard — с `--no-cache`) до остановки контейнеров; `wa-worker-build --no-cache` разворачивается в `docker build --no-cache …` | unit (`just --dry-run`) | `uv run pytest tests/test_max_worker_deployment.py -q -p no:randomly` | ✅ расширить |
| PHONE-21 | воркеры не пишут номер в журнал (`caplog` MAX; JS — тест в гарнире) | unit | `uv run pytest tests/test_worker -q -p no:randomly` + гейты ниже | ❌ |
| кр.2/3 «на живом аккаунте» | ручной обход | manual | — | UAT 19-06 |

### Sampling Rate
- **Per task commit:** `uv run pytest <файлы задачи> -q -p no:randomly`.
- **Per plan wave merge — называть поимённо в `<automated>` каждого плана:** гейты номера `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` `[ЗАМЕР: 1161 passed, 63 с]`; сквозные `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_money_perimeter_gate.py tests/test_templates/test_form_inventory.py tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly` (база части — `test_htmx_post_pairs`, `test_impersonation_gate`, `test_max_connect_transport`, `test_tg_user_auth`, `tests/test_messengers`, `tests/test_worker`, `test_max_worker_deployment`: **340 passed, 137 с** `[ЗАМЕР]`; `test_htmx_gates`, `test_form_inventory`, `test_htmx_markup_gates`, `test_money_perimeter_gate` в этом прогоне не гонялись — их базу снять исполнителю); записи планирования `uv run pytest tests/test_planning -q -p no:randomly` `[ЗАМЕР: 218 passed, 2 skipped, 20 с]`; шаблоны `uv run pytest tests/test_templates -q -p no:randomly` (если тронут `max_connect_step.html`).
- **Phase gate:** полная суита зелёная перед `/gsd-verify-work` (таймаут 5400 с); пост-мердж суиту гонит оркестратор.

### Wave 0 Gaps
- [ ] `tests/test_worker/test_wa_worker_own_phone.py` — PHONE-13 (JS-юнит через `run_node_script`); раннера ставить не нужно, `node` есть (v22 локально, образ `node:20-slim`).
- [ ] `tests/test_pages/test_connect_phone_capture.py` — PHONE-13/14/15 (опросчики и форма MAX; подмена `MaxMessenger` / `WhatsAppMessenger` и `celery.send_task` по образцу `test_max_connect_transport.py::max_bridge`).
- [ ] Кейсы фазы в `tests/test_routes/test_tg_user_auth.py` — `_ScannableQRLogin.wait` возвращает пользователя с `phone`; `_seed_2fa_state(..., sign_in=…)` — `AsyncMock(return_value=SimpleNamespace(phone="…"))`.
- [ ] Framework install: не требуется.

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: high` (`.planning/config.json`).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | подключение мессенджера — не вход пользователя |
| V3 Session Management | частично | QR-состояние TG владельцем (`_owned`, D-04 Фазы 13) — не менять; поле `own_phone` лежит в нём, `repr=False` |
| V4 Access Control | yes | опросчики берут только строку `connecting` **своего** пользователя; `/status` воркера отвечает 403 на чужой `session_id` (`ACCOUNT_ID`); чужой номер не читается |
| V5 Input Validation | yes | форма MAX — `normalize_manual` (длина ≤32, отказ на расширении); `/status.phone` — `normalize_reported` (недоверенная строка воркера); `Telethon User.phone` — тип-проверка + `normalize_reported` |
| V6 Cryptography | no | |
| V7 Error Handling and Logging | yes (PHONE-21) | в журнал только `account_id` и `PhoneWrite.value`; без `str(e)` захвата; гейты приватности |
| V8 Data Protection | yes | номер — персональные данные; не в URL, не в журнале, не в `repr`, не в тексте ошибки |

### Known Threat Patterns for {FastAPI + Baileys + pymax + Telethon}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LID-цифры записаны как номер | Tampering (целостность данных) | `isPnUser` + `jidDecode` в воркере; на стороне приложения — строгий `normalize_reported` (но он **не** отличит LID: 16 % синтетических строк проходят — поэтому защита именно в воркере, D-03) |
| Номер «чужого» аккаунта (QR отсканирован другим телефоном) | Spoofing | D-10: номер, отданный мессенджером, побеждает номер формы; форма — только запас; признак «указан вручную» не ставится |
| Враждебный ввод в поле MAX (XSS через эхо 422) | Tampering/Info | автоэкранирование `field`; текст ошибки — константа `PhoneError` (D-18 Фазы 16) |
| Утечка номера в журналы (воркер, приложение) | Information disclosure | только `account_id` + исход; гейт приватности (именной) + тест «нет цифр в записях журнала»; не поднимать `BAILEYS_LOG_LEVEL` |
| Номер в `repr` датакласса TG | Information disclosure | `field(repr=False)` |
| Номер в `phone.txt`/`PHONE` окружения MAX | Information disclosure | существующая названная граница (отложено); фаза не расширяет |
| Захват номера ломает вход (DoS подключения) | Denial of service | собственный `try/except` + сейвпоинт; единственный коммит всё равно проходит (D-05) |
| Подмена `/status` воркера (недоверенный JSON) | Tampering | `get_own_phone()` принимает только `str`/`int`, остальное `None`; писатель нормализует |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 / `uv` | тесты | ✓ | `.venv` | — |
| Node | JS-тест (`run_node_script`) | ✓ | v22.22.1 (образ `node:20-slim`, Baileys `>=20`) | нет (пропуск запрещён) |
| `just` | тест рецептов | ✓ | 1.45.0 | — |
| Docker / боевой стенд | ручной обход, `just prod-deploy` | ✗ не использовался (запрещено исследованием) | — | обход — отдельный чекпойнт; TG-часть от стенда не зависит |
| `wa_worker/node_modules` | запуск настоящего Baileys | ✗ (пуст) | — | чистая функция с внедрением зависимостей; пин сторожится правилом `package.json` |
| Живые WA / MAX / TG | критерии 2, 3 на живом | ✗ | — | ручной обход владельца (D-11) |

**Missing dependencies with no fallback:** нет. **With fallback:** `node_modules` (внедрение), живые мессенджеры (обход).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Номер WA «из `sock.user.id.split(':')[0]`» | PN-JID через `isPnUser` + `jidDecode`; LID отдельно в `me.lid` | Baileys 7.0.0-rc (LID-миграция) | `split` берёт LID-цифры за номер |
| Номер MAX из `session.db → sessions.phone` | `client.me.contact.phone` (если сервер отдаёт) | pymax 2.x `WebClient` | `sessions.phone` у `WebClient` всегда `""` |
| Номер TG через `get_me()` после входа | `User` из ответа входа | — | без второго запроса |

**Deprecated/outdated:** `wa_bridge/` (legacy, «used for reference», CLAUDE.md) — не трогать.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `User.phone` у собственного пользователя Telegram — непустая строка цифр без `+` | A3 | Нет `UNPARSEABLE`-катастрофы: `normalize_reported` принимает и с `+`; при `None` номер просто «неизвестен» — но тогда критерий 1 на живом TG не выполнится, заметно на первом подключении |
| A2 | Реальный сервер WA отдаёт `me.id` как `<digits>:<device>@s.whatsapp.net` | A2 | Если вместо PN приходит LID, номер WA останется «неизвестен» (по D-03 верно, но критерий 2 «показывает номер» на живом не пройдёт) — ручной обход W-3 |
| A3 | Сервер MAX заполняет `profile.contact.phone` в `LOGIN` при QR-входе `WebClient` | A1 | Не заполняет ⇒ номер MAX всегда из формы (D-10) — план рассчитан на этот исход, критерий 3 «B» не выполнится, а «A без пометки» выполнится |
| A4 | Старые образы воркеров исчезают после `prod-deploy` (стоп и удаление всех контейнеров `wa-worker` и `max-worker`, `justfile:108-111, 120-123`) | Open Question 1 | Если контейнеры остаются, окно «старый образ + новое приложение» шире |
| A5 | Savepoint `begin_nested()` ведёт себя в тестах на SQLite/aiosqlite так же, как в боевом PostgreSQL | Pattern 2 | Измерено на SQLite (`sp_probe.py`) и применяется в `payment_service`/`subscription_service` с тестами; на PostgreSQL — стандартное поведение, но не прогонялось |

## Open Questions

1. **Как читать критерий 4 для MAX, если воркер старого образа, а в форме номер есть?**
   - Что известно: критерий 3 и PHONE-14: «если мессенджер номер не отдал — номер из формы, как автоматический». Критерий 4 и PHONE-15: «воркер старого образа не ломает подключение; номер остаётся неизвестным». Для WA противоречия нет (формы нет). Для MAX форма **обязательна** (`required=true`), и запасной источник — приложение, поэтому со старым образом MAX номер **не** остаётся неизвестным.
   - Что неясно: хочет ли владелец, чтобы MAX со старым образом показывал номер из формы (читает критерий 4 только про «воркер сам ничего не отдал») или «Номер неизвестен» (запас должен жить в новом воркере и со старым образом молчать).
   - Практический вес малый: `prod-deploy` удаляет все контейнеры воркеров, и старый образ возможен лишь если образы не пересобрали (ровно то, что чинит критерий 5).
   - Вопрос по-русски: «Если воркер MAX остался на старом образе и не сообщил номер, показывать номер, который человек ввёл в форме подключения, или оставить «Номер неизвестен»?» Варианты: (а) **показать номер из формы** — запас в приложении, работает и без нового образа; (б) оставить «неизвестен» — запас переезжает в воркер (`phone.txt` → `/status.phone`), приложение номер формы не пишет.
   - Рекомендация: **(а)**. Это буквальный PHONE-14, не требует правок воркера под запас, а тест критерия 4 для MAX читается как «подключение не падает, воркер ничего не дописал, итоговый номер — из формы либо неизвестен, если формы нет»; чистое «остаётся неизвестен» докажет тест на WA.

2. **Пересобирать ли образ WA и в `prod-build`?**
   - Что известно: PHONE-16 и D-06 называют только `prod-deploy` и `prod-hard-deploy`; `prod-build` сегодня строит compose и MAX-образ (`justfile:128-130`), для MAX это закреплено тестом (`tests/test_max_worker_deployment.py:27`). Если `prod-build` не получит WA, он останется единственным рецептом, строящим MAX без WA.
   - Вопрос по-русски: «Добавить сборку образа WhatsApp-воркера ещё и в `just prod-build` — так же, как там уже есть сборка образа MAX?» Варианты: (а) да, одна строка и тест рядом; (б) нет, только два рецепта деплоя, как сказано в требовании.
   - Рекомендация: **(а)** — одна строка, обратима; без неё `prod-build` и `prod-deploy` расходятся в том, что собирают.

(Технические неопределённости, которые решает только живой обход — не вопросы владельцу: W-1 «отдаёт ли MAX `contact.phone` при QR», W-3 «форма `creds.me.id` у реального WA». Запасные пути плана описаны выше.)

## Sources

### Primary (HIGH confidence)
- Исходник Baileys `7.0.0-rc14` (tarball из `registry.npmjs.org`, хеш сверен с `wa_worker/package-lock.json:680`): `lib/index.js:6`, `lib/WABinary/jid-utils.js:30-67`, `jid-utils.d.ts:24, 30`, `lib/Utils/validate-connection.js:139-140, 192`, `lib/Socket/socket.js:734, 764, 771, 855, 931-932`, `lib/Utils/use-multi-file-auth-state.js:87, 116-117`, `lib/Types/Contact.d.ts`, `package.json` (`engines`).
- Исходник pymax `2.3.1` (`.venv/lib/python3.12/site-packages/pymax`): `app.py:100, 115, 155, 161`, `base.py:52-54, 131-136`, `client_web.py:55`, `api/auth/service.py:108, 137`, `dispatch/dispatcher.py:192`, `types/domain/user.py:71`, `types/domain/profile.py`, `types/domain/base.py`.
- Исходник Telethon `1.42.0` (`.venv/…/telethon`): `tl/custom/qrlogin.py:68-116`, `client/auth.py:270-369, 385-407`, `client/users.py:144-174`, `tl/types/__init__.py` (`User.__init__`).
- Репозиторий (прочитано целиком или участками): `app/application/accounts/phone.py`, `app/services/phone.py`, `app/messengers/{telegram_user,max,whatsapp}.py`, `app/pages/accounts.py`, `wa_worker/index.js`, `max_worker/main.py`, `justfile`, `tests/test_max_worker_deployment.py`, `tests/conftest.py` (`run_node_script`), `tests/test_worker/test_max_worker.py`, `tests/test_routes/test_tg_user_auth.py`, `tests/test_messengers/test_telegram_user.py`, `tests/test_pages/test_max_connect_transport.py`, шапки трёх гейтов номера, `tests/account_label_support.py`.
- Прогоны этой сессии: гейты номера 1161 passed (63 с); связка модулей 340 passed (137 с); `tests/test_planning` 218 passed, 2 skipped (20 с); `test_account_phone_writer.py` 27 passed; `test_max_worker_deployment.py` 5 passed; пробы в `/home/orca/.claude/jobs/46358bbc/tmp/probe/` (`tg_probe.py`, `sp_probe.py`, `esm/`).

### Secondary (MEDIUM confidence)
- Внешний поиск по pymax (docs.pymax.org / DeepWiki / PyPI): полей `client.me` и ответа `WebClient` не описывает — как источник утверждений не использован.

### Tertiary (LOW confidence)
- Нет (все `[ASSUMED]` собраны в «Assumptions Log»).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — пины и версии прочитаны/замерены; новых пакетов нет.
- Architecture (TG, WA, опросчики, писатель, деплой): HIGH — прочитано в исходниках пинов и в дереве, ключевые потоки прогнаны на in-memory SQLite.
- MAX `contact.phone` при QR: LOW — исходник не отвечает; измерение — ручной обход; план корректен в обоих исходах.
- Сквозные гейты (счётчики не двигаются): MEDIUM — вывод из того, что считает каждая константа; прототип правок не собирался.
- Pitfalls: HIGH — каждый привязан к прочитанной строке или замеру.

**Research date:** 2026-11-22
**Valid until:** 2026-12-22 для TG/WA/деплоя (пины заморожены); смена пина Baileys/pymax/Telethon или правка `accounts.py` вне фазы обнуляет номера строк.
