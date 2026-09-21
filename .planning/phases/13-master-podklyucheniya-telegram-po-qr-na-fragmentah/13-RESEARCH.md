# Phase 13: Мастер подключения Telegram по QR на фрагментах — Research

**Researched:** 2026-09-21
**Domain:** htmx 2.0.10: периодический POST-опрос, останов опроса ответом; машина состояний QR-входа Telethon 1.42.0 в памяти процесса; привязка сессии к пользователю; перенос инвентарных гейтов
**Confidence:** HIGH. Всё ниже измерено чтением исходников этого дерева, неминифицированного исходника вендоренного htmx (sha256 совпал с `app/static/js/htmx.min.js`) и установленного Telethon, а также двумя прогонами-зондами. Вопросов, которые может решить только владелец, не осталось (§Open Questions).

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Сохранение аккаунта после сканирования — РЕШЕНИЕ ВЛАДЕЛЬЦА (2026-09-21)**

- **D-01:** **Аккаунт создаёт сам запрос опроса, который первым увидел «отсканировано».**
  Отдельного `POST /complete` больше нет: обработчик опроса при статусе `success` зовёт
  `complete_auth()`, создаёт `MessengerAccount` и отдаёт фрагмент «Подключено». Опрос пишет
  в базу, поэтому становится **POST** (htmx умеет периодический POST с `hx-trigger="every 3s"`).
  Это вариант (а) из `.planning/research/ARCHITECTURE.md` §4.2.
  - **Остаточное окно записано честно.** Вариант (а) окно не закрывает, а СУЖАЕТ: сегодня
    между сканированием и сохранением стоят два запроса, после фазы — один интервал опроса.
    Если вкладку закрыли между сканированием и следующим опросом (до ~3 с), авторизованная
    сессия Telethon не сохранится и уйдёт по сроку жизни, а в «Устройствах» Telegram останется
    неиспользуемый вход. Владелец это окно ПРИНЯЛ. Вариант «сохранять фоновой задачей даже при
    закрытой вкладке» рассмотрен и отклонён: запись в базу уходит из фоновой задачи слоя
    мессенджера, вне запроса, а это больше кода и новый вид отказа.
  - **Ровно один аккаунт на одно сканирование.** `complete_auth()` снимает сессию из
    `_qr_sessions` через `pop`, поэтому второй опрос, пришедший следом, сессии уже не найдёт.
    Исследователь проверяет, может ли htmx выпустить опросы внахлёст (`hx-sync` и поведение
    `every` при запросе в полёте). Планировщик заводит машинный тест: два опроса после
    `success` дают один `MessengerAccount`.
  - **`complete_auth()` звать только при `success`.** Он снимает сессию ДО проверки
    `session_string` (`telegram_user.py:155-171`): вызов в другом статусе молча уничтожает
    живую сессию.
  - **Критерий 1 ROADMAP получает летопись, а не переписывается.** «Пять маршрутов отдают
    HTML-фрагменты» становится «четыре маршрута отдают фрагменты, пятый (`complete`) снят
    по D-01, опрос сменил метод GET → POST». Летопись ставится рядом с критерием по идиоме
    D-30/D-32 проекта. Записи разведки (`.planning/research/*`) НЕ правятся.

**Истечение QR-кода — РЕШЕНИЕ ВЛАДЕЛЬЦА (2026-09-21)**

- **D-02:** **Истёкший код → «QR-код истёк» и кнопка «Обновить QR-код».** Кнопка шлёт
  `refresh-qr`, ответ несёт новый QR и возобновляет опрос. Автоматического обновления нет:
  забытая вкладка не должна продолжать обращаться к Telegram. Вариант «обновлять самому до
  5 минут» рассмотрен и отклонён.
- **D-03:** **Сегодня эта ветка фактически мертва, и фаза её ОЖИВЛЯЕТ. Это единственное место,
  где фаза меняет поведение, а не только транспорт.** Замер по коду:
  - `QRLogin.wait()` (Telethon 1.42.0) по умолчанию ждёт до `expires` токена, то есть
    примерно 30 с, выдаваемых Telegram, и затем поднимает `asyncio.TimeoutError`;
  - `_wait_for_qr` (`telegram_user.py:77-97`) ловит его общей веткой как `status = "error"`
    с `error = ""` и пишет в лог `qr_auth_error` с трассировкой;
  - `get_qr_status` отдаёт `expired` только после `QR_SESSION_TTL = 300` с, а ошибка к этому
    времени давно на экране.

  Итог сегодня: через ~30 с человек видит «Ошибка авторизации», и выхода из этого состояния
  нет. Кнопка «Обновить» не появляется. Поэтому **истечение токена QR (таймаут `wait()`) —
  это статус «код истёк», а не ошибка**, и оно отличается от истечения всей сессии
  (300 с). Когда истекла сессия целиком, `refresh-qr` отвечает «Сессия истекла — начните
  заново» с кнопкой старта. Без этой правки критерий 4 (живое «обновление истёкшего кода»)
  не проходится. Нормальное истечение не логируется как ошибка с трассировкой.

**Владение сессией — принято по умолчанию при делегировании**

- **D-04:** **Проверка владения ДОБАВЛЯЕТСЯ: сегодня её нет.** Критерий 3 ROADMAP говорит
  «серверная проверка владения сессией СОХРАНЕНА», а `.planning/research/FEATURES.md:241` —
  «по-прежнему проверяется». Обе посылки ложны. `QRAuthState` (`telegram_user.py:31-39`) не
  хранит пользователя, `start_qr_auth` его не принимает, а обработчики проверяют только сам
  факт входа. Любой вошедший пользователь, зная чужой `session_id`, получает чужой статус и
  может сохранить чужой Telegram-аккаунт себе. Решение:
  - сессия привязывается к пользователю в момент `start-qr`, и опрос, `refresh-qr` и
    `verify-2fa` сверяют её с текущим пользователем;
  - чужой `session_id` получает ТОТ ЖЕ ответ, что неизвестный или истёкший («Сессия не
    найдена — начните заново»): существование сессии не раскрывается;
  - чужой запрос НИЧЕГО не делает с сессией жертвы: не снимает, не отменяет задачу ожидания,
    не обновляет QR;
  - машинный тест на каждый из трёх обработчиков: подставленный чужой `session_id`
    отвергается, а сессия владельца цела и доходит до успеха;
  - летопись у критерия 3 и у FETCH-02 в `.planning/REQUIREMENTS.md` («проверка не
    сохранена, а заведена, потому что её не было»), без переписывания текста критерия.
  - ⚠️ Подключение разрешено под имперсонацией (`tests/test_pages/test_impersonation_gate.py:222-225`,
    «воспроизведение жалобы „не подключается"»). Привязка идёт к тому же пользователю, на
    которого создаётся `MessengerAccount`. Исследователь сверяет, что именно возвращает
    `get_user_from_cookie` под имперсонацией.

**Форма шагов и ответов — принято по умолчанию при делегировании**

- **D-05:** **Один постоянный якорь мастера и своп `innerHTML`** (D-12 Фазы 9), по фрагменту на
  состояние: старт, ожидание сканирования, код истёк, пароль 2FA, подключено, ошибка.
  Идентификатор якоря и запрос опроса стоят на ОДНОМ элементе (Landmine из
  `connect_wa.html:29-33`). `hx-trigger="every 3s"` несёт только фрагмент ожидания, с тем же
  интервалом 3 с, что сегодня. Все остальные фрагменты приходят без триггера, и опрос
  останавливается ответом. Гейт критерия 2 обобщает `test_sync_polling_stops`: у каждого
  фрагмента с `hx-trigger="every "` есть парный без него.
- **D-06:** **`session_id` живёт в скрытом поле внутри фрагментов и уходит полем формы** (опрос
  теперь POST). Ни в переменные JS, ни в URL, ни в хранилища браузера он не попадает.
  QR-картинка и пароль 2FA по-прежнему не переносятся ни в хранилища, ни в атрибуты
  (T-06-02 переносится как есть).
- **D-07:** **Успех — фрагмент «Подключено» со ссылкой «К аккаунтам», как сегодня.** Ни
  автоперехода, ни `HX-Location`, ни нового скрипта. Переход с `setTimeout` из мастеров WA/MAX
  (`accounts/partials/connect_status.html`) сюда не копируется.
- **D-08:** **Неверный пароль 2FA — 422 и шаг 2FA с ошибкой у формы** (D-06 Фазы 11: ошибка
  поля существует и сегодня; D-12 Фазы 8: ошибка поля — у формы). Пароль в ответ НЕ
  возвращается, поле приходит пустым. Пустой пароль сегодня ловит клиентская проверка
  «Введите пароль». После фазы его ловят `required` на поле и серверная проверка тем же
  текстом.
- **D-09:** **Отказы старта и ошибки Telethon — фрагмент с алертом и кнопкой «Начать заново»,
  опрос остановлен.** Существующие тексты переезжают дословно («Telegram API не настроен.
  Обратитесь к администратору.», «Неверный пароль 2FA.», «Сессия авторизации истекла. Начните
  заново.»). Новые тексты ограничены D-02, D-03 и D-04.
- **D-10:** **Нет сессии входа — тот же путь слоя ответа, что у переведённых обработчиков
  раздела** (`respond(redirect="/login")` / `HtmxRefusal`, образец — `accounts_connect_max_start`,
  план 11-18). Никакого JSON `{"error": "Не авторизован"}`.
- **D-11:** **Путь деградации без JS — страница мастера `/accounts/connect/tg_user`, и только.**
  Параметр `redirect` у `respond()` обязателен (FOUND-04), но фаза НЕ строит мастер, работающий
  без JS: без опроса он невозможен, и фаза не заводит возможностей, которых не было (та же линия,
  что в Фазе 12). Критерий 5 записывается в артефактах фазы прямо: мастер на 100 % JS-only
  и сегодня, веха на этом участке регрессировать не может, аудит не вправе записать здесь
  провал.
- **D-12:** **Старое снимается целиком и сразу** (D-09 Фазы 8): 152 строки скрипта, три `onclick`
  (так закрывается долг R-08-02 — часть MAX закрыта Фазой 11), четыре `hidden`-секции, `#error-box`,
  `showSection`/`showError`, пять JSON-контрактов. `fetch(` в `connect_tg_user.html` = 0.
  Инвентарные числа двигаются ЯВНО и измеряются прогоном, а не предсказываются (D-13 Фазы 8).
  Перечни, держащие мастер поимённо:
  `NOT_YET_CONVERTED` / `NOT_YET_CONVERTED_COUNT = 14` (`tests/test_pages/test_htmx_gates.py:258-263, 568`,
  запись `complete` уходит снятием, а не переводом); `connect_tg_user.html#0..#4`
  (`tests/test_templates/test_htmx_inventory.py:1091-1095, 1317`); три исключения `onclick`
  (`tests/test_templates/test_htmx_markup_security.py:65-70`);
  `tests/test_pages/test_hx_location_destinations.py:501-509`; четыре записи
  `tests/test_pages/test_impersonation_gate.py:222-225`; запись приложения с ключом
  `GET /accounts/connect/tg_user/qr-status → session_id` (`tests/test_pages/test_identifier_bounds.py:1500`),
  которая переезжает вместе со сменой метода.
- **D-13:** **Слой мессенджера меняется ровно на D-01, D-03 и D-04.** Семантика Telethon-сессии,
  `QR_SESSION_TTL`, `_cleanup_expired_sessions` и `TelegramUserMessenger` не трогаются.
  `_qr_sessions` остаётся в памяти процесса: прод запускает один процесс uvicorn без
  `--workers` (`docker-compose.prod.yml:103`), поэтому опрос всегда попадает в тот же процесс.

### Claude's Discretion

Владелец решил лично D-01 и D-02. Остальное (D-03…D-13) принято по умолчанию при делегировании:
эти решения стоят на рекомендациях разведки и на действующих решениях прошлых фаз.

Свободно и не решено ни здесь, ни ROADMAP-ом: адрес POST-маршрута опроса (новый путь или
прежний `qr-status` под POST); один шаблон с ветками или файл на фрагмент, и где он лежит —
`accounts/includes/` (как `max_connect_step.html`) или `accounts/partials/`; нужен ли
`form_wrapper`; куда ставится `hx-indicator`; точные формулировки трёх новых текстов из D-02,
D-03 и D-04; разбиение на планы и волны.

### Deferred Ideas (OUT OF SCOPE)

- **Сохранение аккаунта фоновой задачей при закрытой вкладке** — рассмотрено и отклонено
  владельцем (D-01). Вернуться, если потери после сканирования станут наблюдаемыми.
- **Автообновление истёкшего QR** — рассмотрено и отклонено владельцем (D-02).
- **Закрытие Telethon-клиента при уходе со страницы / «Отмене»** — сегодня клиент живёт до
  чистки по сроку. Отдельная работа.
- **Общее хранилище QR-сессий для нескольких процессов** — понадобится только при `--workers > 1`.

**Reviewed Todos (not folded):** `blocked-user-can-still-log-in.md`, `session-cookie-without-secure-flag.md`
(авторизация и транспорт, Фаза 14 и позже); `full-suite-ads-editor-order-pollution.md`,
`plan-price-credibility-bound.md` (редактор объявлений и биллинг).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FETCH-02 | мастер подключения Telegram по QR работает на HTML-фрагментах — опрос через `hx-trigger`, останов опроса ответом без `hx-trigger`, состояние мастера на сервере, `session_id` в скрытом поле при сохранённой серверной проверке владения | Опрос и его останов: §Pattern 1 (форма-опросчик ВНУТРИ фрагмента ожидания, а не на якоре; замер по исходнику 2.0.10). Отсутствие опросов внахлёст: §Pattern 2 (очередь `last` и проверка `bodyContains`). Один аккаунт на сканирование: §Pattern 3. D-03: §Pattern 4 (зонд воспроизвёл `status='error'`, `error=''`). D-04: §Pattern 5 (`get_user_from_cookie` возвращает субъекта имперсонации). Перенос гейтов: §Инвентарь гейтов (D-12 плюс ДЕВЯТЬ перечней, которых D-12 не называет). |
</phase_requirements>

## Summary

Фаза сводится к трём вещам: новой разметке (один включаемый шаблон шага за постоянным якорем `#tg-connect-step`), четырём обработчикам на `respond()` и трём точечным правкам слоя QR-сессий (D-01, D-03, D-04). Всё это делается на уже имеющихся в дереве средствах: `form_wrapper` умеет `trigger=`, `respond()`/`respond_field_error()` дают оба транспорта, образец мастера MAX (план 11-18) показывает раскладку «страница + включаемый шаг». Новых пакетов не нужно.

**Две посылки CONTEXT.md в буквальном прочтении не держатся, и их надо читать иначе.** (1) **D-05** требует ставить идентификатор якоря и запрос опроса на ОДИН элемент и одновременно менять его `innerHTML`. Если элемент с `hx-trigger` переживает подмену, опрос НЕ ОСТАНАВЛИВАЕТСЯ никогда. Именно так устроены WA и MAX, и гейт `PERMANENT_POLLS` поэтому числит их бессрочными (`test_htmx_inventory.py:863-902`). Критерию 2 такая форма противоречит. Рабочая форма: опрашивающая форма лежит ВНУТРИ фрагмента ожидания и явно целится в якорь (`hx-target="#tg-connect-step"`). Подмена удаляет её вместе с таймером. Смысл Landmine («не терять цель подмены») сохраняется явным `hx-target`, а не совпадением элементов. (2) **D-12** перечисляет шесть мест с перечнями гейтов, а живых перечней, которые фаза сдвинет, больше: `test_htmx_post_pairs.py` (замыкание «у каждого переведённого есть пара»), `FRAGMENT_RESPONSE_HANDLERS`, `HX_LOCATION_DESTINATION_CALLS_DECLARED`, два счётчика вызывающих `form_wrapper`, перечень `DISABLED_ELT_EXCEPTIONS`, `MANUAL_FETCH_CEILING_AT_PHASE_08`, контрольный тест `:1317`, построенный на самом мастере, правило непустоты `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` и `tests/test_messengers/test_telegram_user.py` (сигнатура `start_qr_auth`). Полная карта — §Инвентарь гейтов.

**Ответы на четыре делегированных вопроса.** (Q1) Внахлёст опросов вендоренный htmx 2.0.10 НЕ выпускает. Запрос, сработавший при запросе в полёте, ставится в очередь `last` на один слот (`htmx.js:4363-4397`). После ответа он исполняется только если элемент ещё в документе (`:4285`). Подмена якоря удаляет форму-опросчик, и отложенный опрос отбрасывается. `hx-sync` не нужен. Серверную единственность аккаунта держит синхронный `_qr_sessions.pop` до первого `await` в `complete_auth`. (Q2) Под имперсонацией `get_user_from_cookie` возвращает СУБЪЕКТА (`payload["sub"]`), а не администратора (`common.py:599-609`). Сессию привязывать к `user.id`, тому же, на кого создаётся `MessengerAccount`. (Q3) `QRLogin.wait()` без аргумента ждёт `expires − now` и поднимает `TimeoutError` (`qrlogin.py:90-103`). Зонд воспроизвёл сегодняшнее `status='error'`, `error=''`. На Python 3.12 `asyncio.TimeoutError is TimeoutError` → `True`. (Q4) Гейты перечислены в §Инвентарь гейтов вместе с ожидаемым направлением каждого числа. Сами числа ставятся прогоном.

**Primary recommendation:** один шаблон `accounts/includes/tg_connect_step.html` за якорем `<div class="connect-shell" id="tg-connect-step">`. Опрос: `POST /accounts/connect/tg_user/qr-status` формой `form_wrapper(trigger='every 3s', target='#tg-connect-step', swap='innerHTML', disabled_elt='')` со скрытым `session_id`. На `waiting` ответ `204` без тела (правило `"204": swap false` в конфиге). На любое другое состояние — фрагмент без `hx-trigger`. Владение проверяется в слое сессий ДО любого `pop`/`cancel`/`recreate`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Машина состояний QR-входа (`waiting`/`qr_expired`/`needs_2fa`/`success`/`error`) | API / Backend (`app/messengers/telegram_user.py`, память процесса) | — | Состояние живёт рядом с Telethon-клиентом; D-13 запрещает выносить его из процесса |
| Привязка сессии к пользователю и проверка владения (D-04) | API / Backend (слой сессий) | Frontend Server (обработчик передаёт `user.id`) | Проверка до `pop`/`cancel`/`recreate` возможна только там, где эти операции живут |
| Выбор фрагмента по состоянию, оба транспорта | Frontend Server (SSR: `app/pages/accounts.py` + `respond()`) | — | Единственное место решения о форме ответа (G-1/G-2) |
| Периодический опрос, его останов | Browser (htmx `hx-trigger="every 3s"`) | Frontend Server (ответ без триггера / 204) | Таймер — у рантайма; останов — у сервера, через содержимое ответа |
| Создание `MessengerAccount` | API / Backend (обработчик опроса и `verify-2fa`, общий помощник) | Database | D-01: пишет запрос опроса |
| Рендер QR | Frontend Server (`_generate_qr_base64`, `accounts.py:128`) | Browser (`<img src="data:">`) | Без изменений |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| htmx (вендорен) | 2.0.10 | опрос `every 3s`, подмена `innerHTML`, отправка форм | `[VERIFIED: app/static/js/htmx.min.js — version:"2.0.10"; sha256 71ea6718…c0de совпадает с unpkg htmx.org@2.0.10/dist/htmx.min.js]` |
| Telethon | 1.42.0 | `qr_login()`, `QRLogin.wait/recreate/expires`, `sign_in(password=)` | `[VERIFIED: uv run python -c "import telethon; print(telethon.__version__)" → 1.42.0]` |
| FastAPI + Jinja2 | уже в проекте | обработчики, включаемый шаблон шага | существующий стек |
| qrcode | уже в проекте | `_generate_qr_base64` | без изменений |

### Supporting (в дереве, переиспользуются)
| Средство | Где | Когда |
|---------|-----|-------|
| `respond(request, *, redirect, notice=None, fragment=None)` | `app/pages/htmx.py:712` | все исходы, кроме ошибки поля |
| `respond_field_error(request, *, page, fragment)` → 422 | `app/pages/htmx.py:847` | неверный/пустой пароль 2FA (D-08) |
| `form_wrapper(action, target=None, swap=None, trigger=None, disabled_elt='find button[type=submit]', sync=None, encoding=false, include=None)` | `app/templates/components/form_wrapper.html` | ВСЕ формы мастера, включая опросчика (гейт `test_every_htmx_post_is_born_of_a_component_macro`) |
| Раскладка «страница + включаемый шаг + `_max_step_markup`» | `app/pages/accounts.py:540-567`, `accounts/includes/max_connect_step.html`, `accounts/connect_max.html` | прямой образец для TG |

### Alternatives Considered
| Вместо | Можно | Почему не выбрано |
|--------|-------|-------------------|
| 204 на `waiting` | Перерисовывать фрагмент ожидания каждые 3 с | Каждые 3 с заменяется всё содержимое якоря: QR перерисовывается, фокус клавиатуры со ссылки «Отмена» теряется (у `link_button` нет `id`, QUAL-06 не спасёт). 204 не трогает DOM. Цена 204 — случай пары для `qr-status` в `test_htmx_post_pairs` надо сеять не в состоянии `waiting` (§Pitfall 7). |
| Опрос на самом якоре с `outerHTML` (идиома `sync_status_card`) | — | `hx-post` разрешён только на `<form>` и только из макроса. Форма-якорь обняла бы форму 2FA, а вложенные формы в HTML недопустимы. |
| Ручной `<form hx-post … hx-trigger>` | — | Краснит `test_every_htmx_post_is_born_of_a_component_macro` и `test_only_a_form_tag_carries_the_post_attribute` |
| `hx-sync` на опросчике | — | Не нужен: опросчик единственный на экране, а сериализация по элементу уже встроена (§Pattern 2) |

**Installation:** не требуется, новых зависимостей нет.

## Package Legitimacy Audit

Фаза не ставит внешних пакетов. Telethon 1.42.0 и вендоренный htmx 2.0.10 уже в дереве.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | новых пакетов нет |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Браузер (страница /accounts/connect/tg_user)
  #tg-connect-step (постоянный якорь, id печатается страницей безусловно)
     │
     │ [старт] form_wrapper → POST /start-qr ─────────────────────────────┐
     │                                                                     ▼
     │                                              get_user_from_cookie → user (субъект)
     │                                              start_qr_auth(api_id, api_hash, user_id=user.id)
     │                                                 └─ Telethon connect + qr_login + task _wait_for_qr
     │◄── 200 фрагмент «ожидание»: <img QR> + форма-опросчик(hx-trigger every 3s, hidden session_id)
     │
     │ [каждые 3 с] форма-опросчик → POST /qr-status (session_id) ─────────┐
     │                                                                     ▼
     │                                  состояние сессии (с проверкой владельца; чужая = «нет»)
     │                    ┌──────────────┬───────────────┬──────────────┬──────────────┬──────────────┐
     │                 waiting       qr_expired       needs_2fa       success       error / нет / TTL
     │                    │              │               │         complete_auth(pop)      │
     │                    │              │               │         + MessengerAccount      │
     │◄── 204 (без свопа, опросчик жив, опрос идёт)       │               │                 │
     │◄──────────── 200 фрагмент БЕЗ hx-trigger: опросчик удалён подменой → опрос остановлен ◄┘
     │
     │ [код истёк] form_wrapper → POST /refresh-qr ── recreate() + новый _wait_for_qr → 200 «ожидание» (опрос снова)
     │ [2FA]       form_wrapper → POST /verify-2fa ── submit_2fa + complete_auth(pop) + MessengerAccount
     │                                                 └─ неверный/пустой пароль → 422 шаг 2FA (respond_field_error)
     │
Без JS: каждый POST → 302 на /accounts/connect/tg_user (D-11; мастер без JS не работал и не работает)
Нет входа: respond(redirect="/login") → htmx: 204 + HX-Location; без htmx: 302
```

### Recommended Project Structure
```
app/templates/accounts/
├── connect_tg_user.html              # страница: <div class="connect-shell" id="tg-connect-step">{% include %}</div>, скрипт снят
└── includes/tg_connect_step.html     # ЕДИНСТВЕННЫЙ источник разметки шага: start | waiting | qr_expired | password | connected | gone | error
app/pages/accounts.py                 # 4 обработчика на respond(), помощники _tg_step_markup и _save_tg_account; complete снят
app/messengers/telegram_user.py       # QRAuthState.user_id; классификация TimeoutError; проверка владельца в 5 функциях
```

Один файл с ветками, а не файл на фрагмент. Основание — прецедент `max_connect_step.html`: страница и фрагменты рисуются из одного места, разойтись им негде. Отдельный файл на каждый фрагмент к тому же добавил бы вызывающих `form_wrapper` в два счётчика (§Инвентарь, строки 10–11).

### Pattern 1: Опрос останавливается ответом — форма-опросчик ВНУТРИ фрагмента ожидания

**Что:** якорь `#tg-connect-step` постоянный и триггера не несёт. Во фрагменте ожидания лежит маленькая форма `form_wrapper(action='/accounts/connect/tg_user/qr-status', target='#tg-connect-step', swap='innerHTML', trigger='every 3s', disabled_elt='')` со скрытым `session_id`. Любой ответ 200 заменяет содержимое якоря. Форма-опросчик уходит из документа, и её таймер гаснет на следующем тике.

**Почему это работает — по исходнику 2.0.10** `[VERIFIED: htmx.org@2.0.10/dist/htmx.js, sha256 минифицированного совпал с вендоренным]`:
```js
// htmx.js:2360-2373 — таймер опроса перезапускается только пока элемент в документе
function processPolling(elt, handler, spec) {
  const nodeData = getInternalData(elt)
  nodeData.timeout = getWindow().setTimeout(function() {
    if (bodyContains(elt) && nodeData.cancelled !== true) {
      ...
        handler(elt)
      ...
      processPolling(elt, handler, spec)
    }
  }, spec.pollInterval)
}
```
**Почему НЕ «якорь = опросчик + innerHTML» (посылка D-05):** элемент с `hx-trigger` переживает подмену своего содержимого, `bodyContains(elt)` остаётся истинным, и опрос вечен. Так и работают WA/MAX: `id="wa-status" hx-get=… hx-trigger="every 3s" hx-swap="innerHTML"` (`connect_wa.html:34`) и гейт числит их в `PERMANENT_POLLS` с обоснованием «Завершения у ветки нет — человек уходит со страницы» (`test_htmx_inventory.py:863-879`). Для TG это нарушило бы критерий 2.

**Отправляемые значения:** когда инициатор — сама форма, htmx включает её поля: `processInputValue(processed, formData, errors, elt, validate)` (`htmx.js:3627`). Скрытый `session_id` уходит без `hx-include`/`hx-vals`.

**Индикатор:** у `.form-busy` порог появления 300 мс (`app/static/css/app.css:2200-2204`: `transition: opacity .12s linear .3s, visibility 0s linear .3s`). Быстрый опрос не мигает точкой.

**`disabled_elt=''`, а не умолчание:** кнопки у опросчика нет. Умолчание `find button[type=submit]` ничего бы не нашло, а это известный дефект «строка в консоли на каждый запрос» (обоснование записи `components/form_wrapper.html` в `DISABLED_ELT_EXCEPTIONS`, `test_htmx_markup_gates.py:3640-3657`). Пустое значение требует добавить новый шаблон в `callers` той же записи (§Инвентарь, строка 12).

### Pattern 2: Опросов внахлёст не бывает — ответ на вопрос 1 D-01

`[VERIFIED: htmx.js:4331-4397, 4401-4411, 4285-4289, 4573-4604]`
1. Без `hx-sync` ветка `if (syncStrategy)` пропускается. Дальше `if (eltData.xhr)`: запрос в полёте и не прерываемый → `queueStrategy` берётся из события (у опроса события нет: `handler(elt)` зовётся без него) → умолчание `'last'` → `eltData.queuedRequests = []` и в очередь один отложенный вызов, `return`. **Второго XHR не создаётся.**
2. Лок снимается в `finally` у `xhr.onload` — ПОСЛЕ `responseHandler`. Своп при `swapDelay` 0 синхронный (`htmx.js:2049-2053`: `if (swapSpec?.swapDelay && swapSpec.swapDelay > 0) … else { doSwap() }`), так что к моменту `endRequestLock()` старая форма-опросчик уже вне документа.
3. Отложенный вызов идёт в `issueAjaxRequest`, который первым делом проверяет `if (!bodyContains(elt)) { … return promise }` (`:4285`) — запрос отброшен.
4. `hx-sync` поменял бы только стратегию очереди на ТОМ ЖЕ элементе (`drop`/`abort`/`replace`/`queue`). Других элементов, шлющих `qr-status`, на экране нет. **Ставить `hx-sync` не нужно.**
5. Сетевая ошибка (`xhr.onerror`, `:4606-4612`) тоже снимает лок. Элемент на месте, и опрос продолжается — это повторяет сегодняшнее «Network error — keep trying».

Итог: из одной вкладки после `success` уходит РОВНО ОДИН запрос, который видит `success`. Второй приходит только из второй вкладки, где открыт тот же `session_id` (невозможно: `session_id` в каждой вкладке свой), или подделанным запросом. Для этих случаев нужна серверная гарантия (Pattern 3).

### Pattern 3: Ровно один `MessengerAccount` на сканирование — серверная гарантия

`complete_auth` снимает сессию синхронно, до первого `await` (`telegram_user.py:157`: `state = _qr_sessions.pop(session_id, None)`). `await complete_auth(...)` исполняет тело корутины синхронно до первой точки ожидания (`await state.client.disconnect()`). Поэтому из двух конкурентных вызовов в одном цикле событий состояние получает ровно один, второй получает `None`. `[VERIFIED: app/messengers/telegram_user.py:155-171]`

Что обязан сделать обработчик:
- звать `complete_auth` ТОЛЬКО при `status == "success"` (D-01);
- создавать `MessengerAccount` ТОЛЬКО если `complete_auth` вернул непустую строку. Сегодняшний `verify-2fa` этого НЕ проверяет (`accounts.py:303-326`: результат `await complete_auth(session_id)` отбрасывается, аккаунт создаётся из `session_string` от `submit_2fa`), то есть два конкурентных `verify-2fa` дали бы два аккаунта. Общий помощник `_save_tg_account` берёт строку сессии из `complete_auth`, а не из `submit_2fa`, и закрывает оба места;
- проигравшему отвечать фрагментом «Сессия не найдена — начните заново». Из одной вкладки проигравшего не бывает (Pattern 2), поэтому стереть экран «Подключено» ему нечем.

Машинный тест, который не зеленеет вакуумом: НАСТОЯЩЕЕ `QRAuthState(status="success", session_string=…, user_id=…)` в `_qr_sessions`, `client.disconnect` — `AsyncMock` с `await asyncio.sleep(0)` (точка переключения), два POST на опрос через `asyncio.gather`, затем `select count(MessengerAccount)` = 1. `complete_auth` НЕ подменять, иначе атомарность `pop` не измеряется.

### Pattern 4: D-03 — истечение токена как «код истёк»

Факты `[VERIFIED: .venv telethon/tl/custom/qrlogin.py:22-27, 60-66, 90-105]`:
```python
async def recreate(self):
    self._resp = await self._client(self._request)          # новый ExportLoginToken
...
async def wait(self, timeout: float = None):
    if timeout is None:
        timeout = (self._resp.expires - datetime.datetime.now(tz=datetime.timezone.utc)).total_seconds()
    ...
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
    finally:
        self._client.remove_event_handler(handler)
```
Зонд по сегодняшнему коду (настоящий `QRLogin`, `expires = now + 0.2 с`, клиент — заглушка), вывод дословно:
```
TimeoutError
status= 'error' error= ''
get_qr_status= {'status': 'error'}
```
(ключа `error` в ответе нет, потому что `""` ложно → старый JS показывал «Ошибка авторизации»). `asyncio.TimeoutError is TimeoutError` → `True` на 3.12.13. `wait_for` с отрицательным таймаутом поднимает `TimeoutError` сразу (зонд: `neg timeout -> TimeoutError`).

Что менять (в пределах D-03/D-13):
```python
# _wait_for_qr: ветка ДО общего except, после CancelledError
except asyncio.TimeoutError:          # токен QR истёк (~30 с), сессия жива
    state.status = "qr_expired"       # без logger.error и без exc_info (D-03)
```
- `SessionPasswordNeededError` приходит из `self._client(self._request)` ПОСЛЕ события, а не из таймаута, и остаётся в своей ветке.
- `refresh_qr` сегодня корректно перезапускает ожидание: `recreate()` → `status="waiting"` → `created_at=time.time()` → `cancel()` старой задачи (после таймаута она уже завершена, вызов ничего не делает) → новая `_wait_for_qr`. Обработчик события у завершённого `wait` снят в его `finally`. Менять механику не нужно. Нужны две проверки в начале: владелец (D-04) и срок: `refresh_qr` сегодня срок НЕ проверяет (`telegram_user.py:115-134`), а `_cleanup_expired_sessions` зовётся только из `start_qr_auth`, так что устаревшая сессия может «ожить». Требование D-03 «когда истекла сессия целиком, refresh-qr отвечает „Сессия истекла“» без проверки срока не выполняется.
- Рекомендуется пускать `refresh_qr` только из `status == "qr_expired"`. Из `success`/`needs_2fa` подделанный запрос иначе вернул бы сессию в `waiting` и стёр бы готовый вход.
- `refresh_qr` сбрасывает `created_at`, поэтому 300 с отсчитываются от ПОСЛЕДНЕГО выпуска кода, а не от старта. «Сессия истекла целиком» на практике означает: человек простоял на экране «код истёк» дольше ~270 с. Это условие для UAT (§Validation).

### Pattern 5: D-04 — владение сессией и имперсонация

`get_user_from_cookie` (`app/pages/common.py:593-609`) `[VERIFIED: read this session]`:
```python
user = await db.get(User, payload["sub"])
...
actor_id = token_actor_id(payload)
actor = await db.get(User, actor_id) if actor_id is not None else None
setattr(user, IMPERSONATOR_ATTR, actor)
...
return user
```
Возвращается СУБЪЕКТ (тот, под кем вошли), а администратор висит атрибутом `IMPERSONATOR_ATTR = "impersonated_by"` (`common.py:551`). `MessengerAccount(user_id=user.id, …)` создаётся на того же субъекта (`accounts.py:309-316`, `:343-350`). **Привязка — к `user.id`.** Администратор под A и под B получает разные `user.id`, так что сессия, начатая под A, после переключения на B честно отвергается.

Форма правки:
- `QRAuthState` получает поле `user_id: int`; `start_qr_auth(api_id, api_hash, user_id)` его пишет;
- один помощник `_owned(session_id, user_id) -> QRAuthState | None` (чужая = нет) используют `get_qr_status`, `refresh_qr`, `submit_2fa` и `complete_auth`;
- **`complete_auth` сверяет владельца ДО `pop`:** `state = _qr_sessions.get(sid)`; при чужом состоянии `return None`, и только потом `_qr_sessions.pop(sid)`. Между `get` и `pop` нет `await`, так что атомарность Pattern 3 сохраняется. Иначе чужой запрос снял бы сессию жертвы: D-04 это прямо запрещает;
- чужой, неизвестный и истёкший `session_id` дают один и тот же фрагмент;
- `session_id = uuid.uuid4().hex[:16]` — 64 бита, перебором не угадать. Но `session_id` пишется в журнал (`logger.error("qr_auth_error", session_id=…)`, `telegram_user.py:97`; `qr_refresh_error`, `:133`). Проверка владения — не страховка «на всякий случай», а единственная защита от утечки через журналы.

### Pattern 6: Обработчик на слое ответа (образец `accounts_connect_max_start`)

```python
# Source: app/pages/accounts.py:545-567, 571-681 (образец MAX, план 11-18) — форма, а не готовый код
TG_CONNECT_STEP_TEMPLATE = "accounts/includes/tg_connect_step.html"
TG_WIZARD = "/accounts/connect/tg_user"          # путь деградации (D-11)

def _tg_step_markup(**context) -> str:
    return templates.env.get_template(TG_CONNECT_STEP_TEMPLATE).render(**context)

@router.post("/accounts/connect/tg_user/qr-status", response_class=HTMLResponse)
async def accounts_connect_tg_user_qr_status(request: Request, db=Depends(get_db), settings=Depends(get_settings)):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")            # D-10
    form = await request.form()                                      # не Form(...) в сигнатуре — см. Pitfall 8
    session_id = str(form.get("session_id") or "")
    ...
    if status == "waiting":
        async def _unchanged() -> Response:
            return Response(status_code=204)                         # опросчик жив, опрос идёт
        return await respond(request, redirect=TG_WIZARD, fragment=_unchanged)
    ...
    async def _step() -> HTMLResponse:
        return HTMLResponse(_tg_step_markup(step=step, session_id=..., qr_code=..., error=...))
    return await respond(request, redirect=TG_WIZARD, fragment=_step)
```
Сборщики подаются слою ИМЕНЕМ (`fragment=_step`). Анализатор `_fragment_builder_names` исключает их тела из «собственных выходов», и `Response(status_code=204)` внутри `_unchanged` не требует записи в `OWN_RESPONSE_EXITS` `[VERIFIED: tests/test_pages/test_htmx_gates.py:4088-4141, 4161-4171]`. Тот же `Response(...)`, собранный в теле обработчика мимо сборщика, требовал бы записи с решением владельца.

### Anti-Patterns to Avoid
- **Опрос на якоре с `innerHTML`** — вечный опрос (Pattern 1).
- **`complete_auth` вне ветки `success`** — молча уничтожает живую сессию (D-01).
- **Аккаунт из `session_string` от `submit_2fa`, а не из результата `complete_auth`** — два аккаунта при двух `verify-2fa` (Pattern 3).
- **Проверка владельца после `pop`/`cancel`** — чужой запрос ломает сессию жертвы (Pattern 5).
- **Тест D-03, подменяющий `status="qr_expired"` напрямую** — зеленеет вакуумом. Подменять надо `wait()` так, чтобы она поднимала `asyncio.TimeoutError` (или строить настоящий `QRLogin` с коротким `expires`, как в зонде).
- **Эхо пароля в 422** — поле приходит пустым (D-08). `field(... value=...)` для пароля не передавать.
- **`Form(...)` в сигнатуре** — отказ валидации фреймворка вместо авторского фрагмента (Pitfall 8).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Периодический опрос | `setInterval`/`setTimeout` в шаблоне | `form_wrapper(trigger='every 3s')` | критерий 2; таймер htmx гаснет сам при удалении элемента |
| Дедупликация опросов | `hx-sync`, флаги в JS | встроенная очередь `last` + `bodyContains` (Pattern 2) | уже в рантайме |
| Выбор транспорта ответа | ветвление по заголовку в обработчике | `respond()` / `respond_field_error()` | G-1/G-2: признак htmx читается в проекте ровно один раз |
| Ошибка поля 2FA | ручной 422 | `respond_field_error(page=, fragment=)` | правило `"422": swap true` конфига, баннер ошибок пропускает 422 |
| Одиночность сохранения | блокировки, флаги «сохраняется» | `dict.pop` до первого `await` | атомарно в одном цикле событий |
| Форма с hx-post | ручные атрибуты | `form_wrapper` | гейт «рождён компонентным макросом» |

## Runtime State Inventory

Фаза — перевод транспорта, а не переименование. Сверено по категориям:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Нет. `MessengerAccount` пишется прежней формой (`type="tg_user"`, `credentials=session_string`, `status="active"`); миграции нет | нет |
| Live service config | Нет. Внешних конфигураций с путями `…/complete` или `GET …/qr-status` нет (nginx проксирует всё приложение целиком) | нет |
| OS-registered state | Нет | нет |
| Secrets/env vars | `telegram_api_id` / `telegram_api_hash` читаются как прежде | нет |
| Build artifacts | Нет. Кеш статики версионируется `?v={{ asset_version }}`; шаблоны рендерятся сервером | нет |
| In-process state | `_qr_sessions` в памяти: при деплое (перезапуск uvicorn) все незавершённые мастера теряются. Так было и до фазы. Вкладка со старым JS после деплоя шлёт `GET qr-status` (станет 405) и `POST complete` (исчезнет): старый JS ловит ошибку разбора и показывает «Ошибка сети» | нет; записать в SUMMARY как ожидаемое |

## Инвентарь гейтов — что двигается (ответ на вопрос 4)

Направления выведены чтением. **Числа ставятся ПРОГОНОМ покрасневшего правила** (D-13 Фазы 8). Ниже приведены значения на сегодня `[VERIFIED: чтение файлов этой сессии]` и ожидаемое направление `[ASSUMED до прогона]`.

| # | Перечень / число | Файл:строка (сегодня) | Сегодня | Ожидаемо после | В D-12? |
|---|------------------|------------------------|---------|----------------|---------|
| 1 | `NOT_YET_CONVERTED` — 4 ключа TG (`start_qr`, `refresh_qr`, `verify_2fa`, `complete`) | `test_htmx_gates.py:260-263` | `NOT_YET_CONVERTED_COUNT = 14` (`:568`) | 10; `complete` уходит снятием, три — переводом; `qr_status` (станет POST) в перечень не входит — он рождается переведённым | да |
| 2 | `POST_HANDLERS` | `test_htmx_gates.py:161` | `37` | 37 (−`complete`, +`qr_status` под POST) — при сохранении имени функции | нет |
| 3 | `FRAGMENT_RESPONSE_HANDLERS` / `…_DECLARED` | `:1584`, `:1805` | `13` | 17 (+4 ключа; все четыре подают `fragment=`) | нет |
| 4 | `ALLOWED_ROUTES` (имперсонация) | `test_impersonation_gate.py:222-225` | 4 записи TG; `MUTATING_ROUTE_COUNT = 49` (`:110`) | ключ `…_complete` заменяется на `…_qr_status` с причиной «подключение аккаунта»; 49 → 49; `MUTATING_MODULE_COUNT = 14` без движения | да |
| 5 | `MANUAL_FETCH_SITES` `#0..#4`, `MANUAL_FETCH_PLACES` | `test_htmx_inventory.py:1085, 1090-1096` | `5` | 0, перечень пуст (именованный ноль с летописью) | да |
| 6 | `MANUAL_FETCH_CEILING_AT_PHASE_08` | `test_htmx_inventory.py:1082` | `5` | 0 (правило: «опускается ТЕМ ЖЕ коммитом, который снимает место») | нет |
| 7 | контрольный тест `test_control_negative_a_fallen_manual_fetch_count_reddens_the_equality_gate` | `test_htmx_inventory.py:1308-1330` | строит подмену на `sources["accounts/connect_tg_user.html"].replace("fetch(", …)` и утверждает, что подмена что-то изменила | **ПОКРАСНЕЕТ** («вызова ручной сборки в мастере не найдено»); переписать на синтетический шаблон с `fetch(`, добавленный в копию словаря | строка названа, суть — нет |
| 8 | `TOP_LEVEL_BINDING_EXEMPT_TEMPLATES` | `test_hx_location_destinations.py:500-513` | 1 запись (мастер) | запись снимается вместе со скриптом, **но** `test_every_exempt_template_carries_a_non_empty_rationale` утверждает `assert TOP_LEVEL_BINDING_EXEMPT_TEMPLATES, ("перечень изъятий пуст — правило непустоты стало бы вакуумным")` (`:1189-1191`) и **ПОКРАСНЕЕТ**; `test_the_connect_screen_is_not_a_transition_destination_today` (`:1202`) на пустом перечне вакуумен. Оба правила переписать в форму «именованный ноль» | строки да, поломка нет |
| 9 | `HX_LOCATION_DESTINATION_CALLS_DECLARED` | `test_hx_location_destinations.py:452` | `73` | 77 (+4: по одному `respond(redirect="/login")` без `fragment` на обработчик); карта назначений не двигается, `/login` уже в ней | нет |
| 10 | `MACRO_DEFINITION_SITES_CALLERS_DECLARED` + кортеж вызывающих | `test_htmx_markup_gates.py:1629`; кортеж `:1429` | `23` | 24 (+`accounts/includes/tg_connect_step.html`; считаются ФАЙЛЫ, а не вызовы) | нет |
| 11 | `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` + кортеж | `:1740`; кортеж `:2653` | `8` | 9; снимаемые правила G-9/G-11/G-12 проверить замером, как у MAX (`:1706-1712`) | нет |
| 12 | `DISABLED_ELT_EXCEPTIONS["components/form_wrapper.html"].callers` | `test_htmx_markup_gates.py:3632-3638` | 4 вызывающих | +1 (опросчик передаёт `disabled_elt=''`); `DISABLED_ELT_EXCEPTIONS_DECLARED = 2` не двигается | нет |
| 13 | `POST_PAIR_CASES` / `POST_PAIR_CASES_DECLARED` | `test_htmx_post_pairs.py:970`, `:1560` | `50` | +N (по ≥1 случаю на каждый из 4 переведённых; образец — пара MAX `:1432-1447`: `FRAGMENT` с `fragment_mark` и `LOCATION` «нет сессии») | нет |
| 14 | `PAIRED_302_ASSERTIONS_DECLARED` | `test_htmx_post_pairs.py:2340` | `159` | двинется на число новых утверждений `status_code == 302` о переведённых TG-обработчиках (обход в конце модуля) | нет |
| 15 | `CATALOGUE_APPENDIX` запись `GET …/qr-status → session_id` | `test_identifier_bounds.py:1499-1508` | `CATALOGUE_APPENDIX_DECLARED = 10` | ключ переписать на `POST …/qr-status → session_id` (поле формы); число 10 не двигается. ⚠️ Правило `test_every_appendix_entry_is_still_outside_the_universe` (`:2364`) проверяет только, что ключ НЕ во вселенной, а не что он существует: устаревший ключ прошёл бы МОЛЧА. Перенос держится дисциплиной плана | да |
| 16 | Проза об `onclick` | `test_htmx_markup_security.py:63-70` | докстринг: «ЧЕТЫРЕ… три обработчика `connect_tg_user.html` остаются» | летопись: три сняты Фазой 13, R-08-02 закрыт. Числового перечня `onclick` в этом файле НЕТ, двигается только текст | да |
| 17 | `tests/test_messengers/test_telegram_user.py::test_start_qr_auth` и соседи | `:331-391` | `start_qr_auth(api_id=12345, api_hash="test_hash")` | покраснеет на новой сигнатуре (`user_id`); `QRAuthState(...)` в тестах получает `user_id` | нет |
| 18 | `tests/test_routes/test_tg_user_auth.py` | 297 строк, 13 тестов JSON-контрактов | JSON | переписываются на фрагменты (CONTEXT: «не удаляются молча»); тесты `complete` → тесты опроса `success` | да (по названию) |
| 19 | `POLLING_FRAGMENTS = 10`, `PERMANENT_POLLS`/`TERMINATING_POLLS`, неравенство `POLL_PLACES <= POLLING_FRAGMENTS <= POLL_PLACES + CONDITIONAL_PLACES` | `test_htmx_inventory.py:696, 856, 863-925, 918-957` | 10 | **СКОРЕЕ ВСЕГО НЕ ДВИНЕТСЯ — и это слепое пятно, а не соблюдение.** Гейт ищет `hx-trigger="…every…"` в ТЕГАХ исходника (`POLL_TRIGGER_ATTR`, `:696`). У формы из макроса в теге стоит `hx-trigger="{{ trigger }}"`, а `'every 3s'` живёт в аргументе `{% call %}` вне `<…>`. Опросчик TG гейту невидим. Критерий 2 поэтому доказывается ОТРЕНДЕРЕННЫМИ ответами (§Validation), а в летописи гейта записывается слепота к опросам, рождённым макросом. Проверить прогоном: правило остаётся зелёным при добавленном опросчике | нет |
| 20 | `FRAGMENT_ROUTES_DECLARED` | `test_htmx_markup_gates.py:918` | `11` | 11 (все обработчики несут путь деградации через `respond`) | нет |
| 21 | `HX_POST_PLACES` | `:149` | `3` | 3 (считаются файлы, ПЕЧАТАЮЩИЕ атрибут; новые формы рождены макросом) | нет |

Сверх таблицы: запускать весь набор (`just test`). По памяти проекта только полный прогон ловит перечни, которых обход не называл («Orchestrator gate catches records defects»).

## Common Pitfalls

### Pitfall 1 (BLOCKER): посылка D-05 «якорь = опросчик» даёт вечный опрос
**What goes wrong:** опрос не останавливается ни на «Подключено», ни на 2FA. Экран 2FA продолжает раз в 3 с перерисовываться ответом опроса и стирает набранный пароль.
**Why:** `processPolling` проверяет только `bodyContains(elt)` (Pattern 1).
**How to avoid:** опросчик — дочерняя форма фрагмента ожидания с явным `hx-target="#tg-connect-step"`.
**Warning signs:** в журнале nginx/uvicorn поток `POST …/qr-status` после успеха.

### Pitfall 2 (HIGH): D-03 оживляет ветку, но `refresh_qr` не знает срока
**What goes wrong:** «Обновить QR-код» через 10 минут простоя выдаёт новый код на устаревшей сессии (её не чистил никто, кроме чужого `start_qr_auth`) вместо «Сессия истекла — начните заново».
**How to avoid:** проверка `time.time() - state.created_at > QR_SESSION_TTL` в `refresh_qr` (или в обработчике через общий помощник). Сама `QR_SESSION_TTL` не меняется (D-13).

### Pitfall 3 (HIGH): гонка двух `verify-2fa` сегодня создаёт два аккаунта
Pattern 3: аккаунт создавать из результата `complete_auth`. Защиту от двойного нажатия на клиенте даёт `hx-disabled-elt` обёртки, на сервере — `pop`.

### Pitfall 4 (HIGH): контрольные тесты, построенные НА самом мастере, краснеют
Инвентарь, строки 7 и 8. Оба красных — следствие работы, а не регрессии. Чинятся переписыванием контроля на синтетику и формой «именованный ноль», а не удалением правил.

### Pitfall 5 (MEDIUM): 500 в опросе → баннер каждые 3 с
**What goes wrong:** необработанное исключение в обработчике опроса даёт 500. Правило `"[45]..": swap false, error true` не меняет DOM, опросчик жив и шлёт снова, общий баннер отказа (`includes/htmx_error_banner.html`) поднимается раз за разом.
**How to avoid:** обработчик опроса и `submit_2fa` оборачивают ошибки Telethon (FloodWait, сеть) во фрагмент ошибки D-09 с кнопкой «Начать заново». Сегодня `submit_2fa` ловит только `PasswordHashInvalidError` (`telegram_user.py:145-148`).

### Pitfall 6 (MEDIUM): часы сервера против `expires` Telegram
`wait()` считает таймаут по ЛОКАЛЬНЫМ часам против серверного `expires` (`qrlogin.py:91`). Если часы сервера спешат больше чем на ~30 с, таймаут отрицательный, `TimeoutError` поднимается сразу, и после правки D-03 каждый QR будет мгновенно «истёкшим». До D-03 то же давало мгновенную «Ошибку авторизации». Предусловие UAT: часы прод-хоста синхронизированы (NTP). `[VERIFIED: зонд — wait_for(timeout=-5) → TimeoutError]`

### Pitfall 7 (MEDIUM): пара для `qr-status` в `test_htmx_post_pairs`
Ветка `FRAGMENT` реестра ожидает «200 и фрагмент» (`test_htmx_post_pairs.py:107`: `FRAGMENT = "ожидается 200 и фрагмент"`). Состояние `waiting` отвечает 204, поэтому случай пары сеется в состоянии, дающем фрагмент (например `qr_expired`, с меткой вроде `name="session_id"` на форме обновления), плюс случай «нет сессии» → `LOCATION`. Без htmx любой исход даёт 302 на `/accounts/connect/tg_user`.

### Pitfall 8 (MEDIUM): `Form(...)` в сигнатуре
Параметр формы, объявленный через `Form(...)`, при отсутствии поля уходит в отказ валидации фреймворка (пустой 400 на пути htmx — `malformed_request_response`, `htmx.py:426-458`), а не в авторский фрагмент «Сессия не найдена». Образец MAX читает поле внутри обработчика (`form = await request.form()`, `accounts.py:612-614`). Заодно это обходит реестр `VALIDATION_REFUSAL_DIVERGENCES` (`test_htmx_gates.py:2945`, `…_DECLARED = 0`).

### Pitfall 9 (LOW): старт без JS порождает сироту Telethon
Без JS форма старта уходит обычным POST, сервер заводит сессию Telethon и отвечает 302 на страницу мастера (D-11). Клиент живёт до чужого `start_qr_auth` после 300 с. Так же было и раньше, только кнопка без JS вообще ничего не делала. Решать это ветвлением по признаку htmx в обработчике НЕЛЬЗЯ (G-1/G-2). Записать как принятое. Относится к отложенной «чистке клиентов».

### Pitfall 10 (LOW): `success` после TTL выглядит как «истекло»
`get_qr_status` проверяет срок РАНЬШЕ статуса (`telegram_user.py:106-107`). Сканирование на 299-й секунде и опрос на 301-й дают «истекло» при авторизованной сессии. Окно ~3 с раз в 300 с; см. Open Questions, п. 2.

## Code Examples

### Шаблон шага (форма; тексты — места для D-02/D-03/D-04)
```jinja
{# accounts/includes/tg_connect_step.html — единственный источник разметки шага.
   Source (форма): accounts/includes/max_connect_step.html #}
{% from "components/card.html" import card_open, card_close %}
{% from "components/button.html" import button, link_button %}
{% from "components/badge.html" import badge %}
{% from "components/alert.html" import alert %}
{% from "components/field.html" import field %}
{% from "components/form_wrapper.html" import form_wrapper %}
  {% if error %}{{ alert(error) }}{% endif %}
  {{ card_open() }}
  {% if step == "waiting" %}
  <div class="connect-step connect-step--center">
    <div class="connect-qr"><img src="{{ qr_code }}" alt="QR-код"></div>
    <p class="connect-step__text">Ожидание сканирования...</p>
    {% call form_wrapper(action='/accounts/connect/tg_user/qr-status', target='#tg-connect-step',
                         swap='innerHTML', trigger='every 3s', disabled_elt='') %}
      <input type="hidden" name="session_id" value="{{ session_id }}">
    {% endcall %}
    <div class="connect-step__actions">{{ link_button('Отмена', '/accounts', variant='ghost') }}</div>
  </div>
  {% elif step == "qr_expired" %}  {# форма refresh-qr + hidden session_id + button('Обновить QR-код') #}
  {% elif step == "password" %}    {# форма verify-2fa + hidden session_id + field(password, required=true) — без value #}
  {% elif step == "connected" %}   {# badge('Подключено','success') + link_button('К аккаунтам','/accounts') — D-07 #}
  {% else %}                       {# start / gone / error: форма start-qr, button('Начать подключение' | 'Начать заново') #}
  {% endif %}
  {{ card_close() }}
```
Страница: `<div class="connect-shell" id="tg-connect-step">{% include "accounts/includes/tg_connect_step.html" %}</div>`. Идентификатор печатается безусловно (правило G-9 параметрических целей).

### Классификация в `_wait_for_qr`
```python
# Source: app/messengers/telegram_user.py:77-97 (правка D-03)
try:
    await state.qr_login.wait()
    state.session_string = state.client.session.save()
    state.status = "success"
except asyncio.CancelledError:
    pass
except asyncio.TimeoutError:            # == TimeoutError на 3.12; токен ~30 с истёк
    state.status = "qr_expired"         # сессия жива, лог без трассировки
except Exception as e:
    ...                                 # прежние ветки needs_2fa / error без изменений
```

### Тест D-03 без вакуума
```python
# Настоящий QRLogin с коротким expires — воспроизводит именно asyncio.TimeoutError
q = QRLogin(client, [])
q._resp = SimpleNamespace(expires=datetime.now(tz=timezone.utc) + timedelta(seconds=0.05), token=b"x")
state = QRAuthState(client=client, qr_login=q, user_id=1)
_qr_sessions["sid"] = state
await _wait_for_qr("sid")
assert state.status == "qr_expired" and not state.error
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setInterval` + `fetch` + JSON + `hidden` | `hx-trigger="every 3s"` на форме из макроса, фрагменты, останов удалением опросчика | эта фаза | 152 строки JS → 0; `fetch(` в шаблонах 5 → 0 |
| `GET qr-status` + отдельный `POST complete` | `POST qr-status` сам сохраняет аккаунт | D-01 | окно «отсканировано, не сохранено» сужается с двух запросов до одного интервала |
| таймаут токена = «Ошибка авторизации» без выхода | `qr_expired` + «Обновить QR-код» | D-03 | единственное поведенческое изменение фазы |
| сессия без владельца | `QRAuthState.user_id` + проверка до любых действий | D-04 | закрыт перехват чужого подключения по `session_id` |

**Deprecated/outdated:** `POST /accounts/connect/tg_user/complete` — снимается. `GET /accounts/connect/tg_user/qr-status` — заменяется на POST.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Ожидаемые значения чисел в §Инвентарь (14→10, 13→17, 73→77, 23→24, 8→9, 49→49, 37→37) | Инвентарь | Низкий: числа ставятся прогоном; неверный прогноз только меняет число в правке |
| A2 | Гейт опросов слеп к опросчику из `form_wrapper` (строка 19) | Инвентарь | Средний: если гейт его увидит, POLLING_FRAGMENTS станет 11, и неравенство `≤ POLL_PLACES + CONDITIONAL_PLACES` покраснеет — тогда неравенство переписывается под POST-опросы. Проверяется первым же прогоном |
| A3 | Время жизни токена QR у Telegram около 30 с | Pattern 4 | Низкий: код опирается на `expires`, а не на число; это влияет только на ожидание в UAT |
| A4 | Ответ 204 без заголовков не краснит ни одного гейта ответа (проверенные гейты 204 требуют `HX-Location` только у ветки перехода) | Pattern 6 | Средний: если какой-то гейт требует `HX-Location` на любом 204, откат — перерисовка фрагмента ожидания (вариант из Alternatives) |

## Open Questions (RESOLVED — владельцу вопросов нет)

1. **Адрес опроса.** Решение: прежний путь `/accounts/connect/tg_user/qr-status` под POST и прежнее имя функции `accounts_connect_tg_user_qr_status`. Так переезжает запись приложения идентификаторов (D-12) и остаётся стабильным ключ имперсонации.
2. **Успех после TTL (Pitfall 10).** Рекомендация: в обработчике опроса проверять `status == "success"` раньше срока (срок сессии при этом не меняется, D-13 соблюдён). Решение за планировщиком: окно мало, а исправление — одна перестановка в пределах D-01.
3. **Тексты D-02/D-03/D-04.** Рекомендация: «QR-код истёк. Обновите его, чтобы продолжить.»; «Сессия подключения истекла. Начните заново.»; «Сессия подключения не найдена. Начните заново.» Для истёкшей сессии разумно взять существующий текст «Сессия авторизации истекла. Начните заново.» (D-09 предписывает переносить тексты дословно). Решение за планировщиком/UI-SPEC.
4. **Нужен ли `form_wrapper`.** Да, это обязательно: без него не пройти `test_every_htmx_post_is_born_of_a_component_macro` и `test_only_a_form_tag_carries_the_post_attribute`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (uv) | всё | ✓ | 3.12.13 | — |
| Telethon | слой сессий | ✓ | 1.42.0 | — |
| Node | `run_node_script` в гейтах (`test_hx_location_destinations.py`) | ✓ | v22.22.1 | — |
| Настоящий Telegram-аккаунт с 2FA и без, телефон | критерий 4 (UAT) | ✗ (человек) | — | нет: ручной UAT |
| `telegram_api_id/hash` на стенде UAT | критерий 4 | не проверено | — | нет |
| Синхронизированные часы стенда | D-03 в UAT (Pitfall 6) | не проверено | — | нет |

**Missing dependencies with no fallback:** живой аккаунт Telegram и человек со сканером на этапе UAT (закладывается как `checkpoint:human-verify`, `human_verify_mode: end-of-phase`).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio, httpx `AsyncClient` (ASGI), SQLite в памяти |
| Config file | `pyproject.toml` / `tests/conftest.py` (фикстуры `authed_client`, `htmx_client`, `db_session`) |
| Quick run command | `uv run pytest tests/test_routes/test_tg_user_auth.py tests/test_messengers/test_telegram_user.py -q` |
| Gate run command | `uv run pytest tests/test_pages/test_htmx_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_markup_security.py tests/test_pages/test_hx_location_destinations.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_htmx_post_pairs.py -q` (замер на сегодня: 331 passed за 157 с) |
| Full suite command | `just test` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-02 / кр.1 | `fetch(` = 0, `setInterval`, `hidden`, `onclick`, `<script>` в `connect_tg_user.html` = 0; 4 маршрута отдают `text/html`, `complete` → 404/405 | unit (разметка + маршруты) | `uv run pytest tests/test_routes/test_tg_user_auth.py -q` | ✅ переписывается |
| FETCH-02 / кр.2 | обобщённая пара: для КАЖДОГО исхода каждого из 4 маршрутов только `waiting`-фрагмент (start/refresh) несёт `hx-trigger="every 3s"`; все прочие 200-ответы — без `hx-trigger`; опрос в `waiting` → 204 и пустое тело | unit, параметризованный по (маршрут × состояние) | `uv run pytest tests/test_routes/test_tg_user_auth.py -k polling -q` | ❌ Wave 0 |
| FETCH-02 / кр.3 | чужой `session_id` на опросе, `refresh-qr`, `verify-2fa`: ответ = ответу «неизвестная сессия»; сессия владельца цела (`_qr_sessions` содержит её, задача ожидания не отменена, `recreate` не вызван) и доходит до успеха | unit | `uv run pytest tests/test_routes/test_tg_user_auth.py -k foreign -q` | ❌ Wave 0 |
| D-01 | два конкурентных опроса после `success` → ровно 1 `MessengerAccount`; `complete_auth` не подменяется | unit (asyncio.gather) | `uv run pytest tests/test_routes/test_tg_user_auth.py -k one_account -q` | ❌ Wave 0 |
| D-03 | настоящий `QRLogin` с коротким `expires` → `status == "qr_expired"`, `error` пуст, `logger.error` не звался; `refresh_qr` после TTL → None | unit | `uv run pytest tests/test_messengers/test_telegram_user.py -k expired -q` | ❌ Wave 0 |
| D-04 | `get_user_from_cookie` под имперсонацией → привязка к субъекту; аккаунт создаётся на субъекта | unit | `uv run pytest tests/test_routes/test_tg_user_auth.py -k impersonat -q` | ❌ Wave 0 |
| D-08 | неверный/пустой пароль → 422, шаг 2FA, поле пустое, пароля нет в теле | unit | `… -k 2fa -q` | ✅ переписывается |
| кр.4 | сканирование, «код истёк» → «Обновить», 2FA — на живой сессии | manual-only (живой Telegram, телефон) | — | UAT |
| кр.5 | документная запись «деградации без JS нет и сегодня» | doc check | grep в SUMMARY/VERIFICATION | — |

### Sampling Rate
- **Per task commit:** quick run + `uv run pytest <файл гейта, который задача двигает> -q`
- **Per wave merge:** gate run command
- **Phase gate:** `just test` зелёный до `/gsd-verify-work` (только полный прогон ловит перечни, которых обход не называл)

### Wave 0 Gaps
- [ ] `tests/test_routes/test_tg_user_auth.py` — переписать фикстуру под `htmx_client`-форму (заголовок `HX-Request` на запрос), завести тесты: пары опроса, чужой `session_id` ×3, один аккаунт, имперсонация
- [ ] `tests/test_messengers/test_telegram_user.py` — `user_id` в `start_qr_auth`/`QRAuthState`; тест D-03 на настоящем `QRLogin`; `refresh_qr` после TTL; `complete_auth` с чужим владельцем не снимает сессию
- [ ] Строки 1–19 §Инвентаря — по задаче на перечень или группу перечней, числа — прогоном
- UAT: сценарии без 2FA, с 2FA (верный и неверный пароль), «код истёк» (ждать ≥ ~30 с после выдачи кода) → «Обновить», «сессия истекла» (≥ 300 с на экране «код истёк» → «Обновить»). Сканирует человек, браузер CDP стоит на другой машине. Машинная улика обхода — не приёмка.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (опосредованно) | вход в продукт — `get_user_from_cookie`; 2FA Telegram проверяет сервер Telegram (`sign_in(password=)`) |
| V3 Session Management | yes | QR-сессия: 64-битный `session_id`, срок 300 с (без изменений), привязка к `user.id` (D-04) |
| V4 Access Control | **yes — основной предмет** | проверка владельца в слое сессий ДО `pop`/`cancel`/`recreate`/`sign_in`; одинаковый ответ на чужое, неизвестное и истёкшее |
| V5 Input Validation | yes | `session_id` — строка-ключ словаря (сравнение по колонке не идёт); пароль не эхо; поля читаются из формы в обработчике |
| V6 Cryptography | no | — |
| V7 Error/Logging | yes | пароль не логируется; нормальное истечение кода без `exc_info`; `session_id` в журнале остаётся, и поэтому D-04 обязателен |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Подстановка чужого `session_id` → чужой Telegram себе | Elevation / Spoofing | D-04: `state.user_id == user.id`, иначе «не найдено» |
| Чужой запрос рушит сессию жертвы (pop/cancel/recreate) | Denial of Service | проверка владельца ДО мутаций (Pattern 5) |
| Раскрытие существования сессии | Information Disclosure | одинаковый фрагмент для чужой/неизвестной/истёкшей |
| Двойное сохранение (гонка) | Tampering | `pop` до первого `await`; аккаунт только из результата `complete_auth` |
| Эхо пароля 2FA в 422 | Information Disclosure | поле пустое; `respond_field_error` рендерит шаблоном с автоэкранированием |
| XSS через QR / тексты ошибок | Tampering | QR — data URI из `_generate_qr_base64`; тексты рендерятся Jinja2 с автоэкранированием; `|safe` не вводить |
| CSRF на POST опроса | Tampering | атакующему нужен чужой `session_id`, а D-04 его отвергает; куки и origin-проверки проекта без изменений |
| Опрос под имперсонацией | Repudiation | разрешено по `ALLOWED_ROUTES` с причиной; ключ `complete` → `qr_status` |

## Sources

### Primary (HIGH confidence)
- `app/messengers/telegram_user.py:24-186` — машина состояний, `pop`, отсутствие владельца, отсутствие проверки срока в `refresh_qr`
- `app/pages/accounts.py:128-134, 211-356, 540-720` — пять маршрутов, образец MAX
- `app/pages/common.py:551, 561-609` — `get_user_from_cookie` под имперсонацией
- `app/pages/htmx.py:188, 426-458, 712-844, 847-960` — слой ответа
- `app/templates/components/form_wrapper.html` — сигнатура макроса и параметр `trigger`
- `app/templates/includes/htmx_config.html` — `responseHandling` (`"204": swap false`, `"422": swap true`, `"[45]..": swap false`)
- `htmx.org@2.0.10/dist/htmx.js` (sha256 минифицированного = вендоренный) — `:2360-2373`, `:4269-4411`, `:4573-4612`, `:2049-2053`, `:1559-1616`, `:3602-3627`
- `.venv/.../telethon/tl/custom/qrlogin.py:22-119`, `client/auth.py:491-529` — Telethon 1.42.0
- Зонды этой сессии: `_wait_for_qr` на настоящем `QRLogin` → `status='error' error=''`; `asyncio.TimeoutError is TimeoutError` → True; `wait_for(timeout=-5)` → `TimeoutError`
- Файлы гейтов, перечисленные в §Инвентарь (читались этой сессией)
- `docker-compose.prod.yml:103` — один процесс uvicorn; `tests/test_infra/test_web_service_is_single_process.py` стережёт это

### Secondary (MEDIUM confidence)
- нет

### Tertiary (LOW confidence)
- Время жизни токена QR около 30 с — со слов CONTEXT/разведки, в этой сессии не замерено (A3)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — всё в дереве, версии проверены
- Architecture: HIGH — механика опроса прочитана по исходнику рантайма, образец MAX в дереве
- Pitfalls: HIGH для 1–4, 7, 8 (прочитано и воспроизведено); MEDIUM для A2/A4 (подтверждаются первым прогоном)

**Research date:** 2026-09-21
**Valid until:** 2026-10-21 (стек стабилен; числа инвентаря устареют с первой же фазой, которая их двинет)
