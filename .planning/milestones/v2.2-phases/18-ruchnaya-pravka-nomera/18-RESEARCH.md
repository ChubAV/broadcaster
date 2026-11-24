# Phase 18: Ручная правка номера - Research

**Researched:** 2026-11-21
**Domain:** страничный слой FastAPI + Jinja2 + htmx (контракт формы v2.1), единый писатель номера (Фаза 16), сквозные гейты чтения исходников
**Confidence:** HIGH по числам гейтов и поведению маршрута (сняты прогоном прототипа в копии дерева вне репозитория); MEDIUM по раскладке шапки на 320–375 px (суита текст CSS читает, браузера нет)

**Как читать метки.** `[ЗАМЕР: команда]` — прогнано в этой сессии; `[ПРОЧИТАНО: путь:строки]` — открыт файл, значение процитировано дословно; `[ВЫВОД]` — следствие из двух прочитанных мест; `[ОЦЕНКА]` — суждение без прогона; `[ASSUMED]` — знание из обучения, не проверенное в сессии (собрано в «Assumptions Log»). Рабочее дерево репозитория не менялось: `git status --short` на конец исследования — только `?? .dockerignore`, как на старте.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Уже заперто роадмапом, требованиями и решениями владельца 2026-10-08 (не пересматривать)
- **D-01:** Форма живёт на **экране групп аккаунта** (`/accounts/{id}/groups`). С карточки аккаунта туда ведёт ссылка: «Указать номер», если номер неизвестен, и «Изменить», если он есть (критерий 1). Маршрут — `POST /accounts/{id}/phone` в `app/pages/account_groups.py`.
- **D-02:** Ввод свободный (`8 999 123 45 67`, `+7 (999) 123-45-67`, пробелы, скобки, дефисы), поле `type="tel"`. Нормализует и пишет **только** писатель Фазы 16 (`app/application/accounts/phone.py::set_manual_phone`): гейт единственного писателя (D-13 Фазы 16) и защита `phone_guard` краснят любую запись мимо него.
- **D-03:** На неверный ввод — **422**: текст ошибки по-русски с примером написания, то есть константа `PhoneError` из `app/services/phone.py`. Поле сохраняет введённое значение, плашка аварии не поднимается (критерий 2). Введённое значение в текст ошибки не подставляется (D-18 Фазы 16, PHONE-21).
- **D-04:** Без JS — рабочая форма `method="post"`, у которой `hx-post` посимвольно совпадает с `action` (рамка v2.1). С JS — ответ фрагментом без перезагрузки страницы.
- **D-05:** Владение проверяется на маршруте через `_load_owned_account`, потому что писатель владельца не проверяет (T-16-19, принятый риск Фазы 16; STATE.md, Blockers). Чужой аккаунт отвечает **так же, как несуществующий**. `LookupError` писателя (строку удалили между проверкой и записью) отвечает тем же образом. Обработчик сверяет источник запроса (`is_same_origin`) и границу `ID_MAX` (тип пути `IdPath`).
- **D-06:** Правка под имперсонацией **разрешена** (решение 4 разведки, PHONE-11). Маршрут вносится в `ALLOWED_ROUTES` гейта `tests/test_pages/test_impersonation_gate.py` с записанной причиной: «номер — подпись, а не учётные данные; на доставку не влияет». В отличие от `profile_post` (D-22), зависимости `forbid_when_impersonating` у маршрута **нет**. Разрешение закрепляется тестом.
- **D-07:** Очистка ставит `phone = NULL`, `phone_is_manual = false` (D-07 Фазы 16). Тест: после очистки условная запись автоисточника (`fill_reported_phone`) возвращает `WRITTEN` (критерий 3).
- **D-08:** Сквозные гейты новой формы и маршрута пересчитываются и называются **поимённо в `<automated>` каждого плана**: `WRITE_FORM_PLACES`, `MUTATING_ROUTE_COUNT` (сегодня 49), `MUTATING_MODULE_COUNT`, `PAIRED_302_ASSERTIONS_DECLARED`, `FRAGMENT_RESPONSE_HANDLERS_DECLARED`, `PUSH_URL_DECISIONS_DECLARED`, реестр `app/pages/notices.py`, гейт имперсонации, `tests/test_pages/test_htmx_post_pairs.py`, а также гейты номера Фазы 16: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py`. Риск фазы — бюджет гейтов, а не техника (пометка «Research» роадмапа).

#### Как стирается номер (решение владельца, 2026-11-21) — закрывает долг IN-01
- **D-09:** **Пустое поле означает «стереть».** Человек стирает текст и нажимает «Сохранить»: номер становится «неизвестен». Отдельной кнопки «Очистить» нет, подтверждения нет. Так дословно сказано в критерии 3 («очищает поле») и в PHONE-10, а ошибочно стёртое вписывается обратно за секунду: номер — только подпись. Форма отдаёт пустой или пробельный ввод писателю как есть (`set_manual_phone` уже трактует его как очистку).
  - `PHONE_ERROR_BLANK` форма **не показывает никогда**. Константа **остаётся** в `app/services/phone.py`: её поднимает `normalize_manual("")`, этот контракт прямого вызова закреплён тестами Фазы 16 (`tests/test_services/test_phone.py:661–662, 1256`), а удаление покраснило бы их без пользы. В докстринге обработчика нужно записать, что пустой ввод на этом пути означает очистку, а не ошибку, со ссылкой на это решение.
  - Строку «Phase 16 → Phase 18 / IN-01» в таблице отложенного в `.planning/STATE.md` план фазы закрывает диспозицией «решено владельцем 2026-11-21: пустое поле = очистка (D-09 Фазы 18)», а не оставляет открытой.

#### Где видна пометка «указан вручную» (решение владельца, 2026-11-21)
- **D-10:** **Везде, где подпись аккаунта рисуется разметкой**: карточки аккаунтов (страница, порция, фрагмент опроса синхронизации), шапка и `<h2>` экрана групп, чипы расписаний, карточка истории, админка («Воркеры», «Очередь», карточка пользователя, история пользователя). Пометка — приглушённый текст «указан вручную» после номера и до `#id` двойника. Делается **одной правкой общего помощника**: `AccountRow`/`AccountLabel` получают признак ручного номера, макрос `components/account_label.html` печатает пометку. Список мест повторно не перебирается.
  - **В плоских формах пометки нет:** `<title>`, `<option>` фильтра истории, `plain` / `plain_with_id`, CSV-экспорт. Там только простой текст подписи.
  - Признак ручного номера **не входит в ключ двойника** (D-14 Фазы 17 сравнивает готовую подпись номера). Ручной и автоматический одинаковые номера — по-прежнему двойники.
  - Пометку получают все пути, которые несут номер: `load_account_rows` (выбирает `phone_is_manual`), `SyncStatusView` (рядом с `phone`), карта `account_id → phone` истории и порций (одним запросом, как в D-18 Фазы 17).
  - Контракт раскладки длинной подписи на 320–375 px (`tests/test_pages/test_responsive_markup.py`, план 17-09) обязан выдержать подпись с пометкой.

#### Принято по умолчанию при делегировании (владелец: «остальное — по умолчаниям», 2026-11-21)
- **D-11:** Форма стоит **в шапке аккаунта** экрана групп (блок `data-acct-head`) и **видна всегда**, без раскрытия по кнопке, поэтому без JS ничего прятать и раскрывать не нужно. Поле заполнено текущим номером в форме показа (`+7 999 123-45-67`; нормализатор принимает её обратно). Под полем подсказка с примером. Кнопка «Сохранить». Оформление — `form_wrapper` и `field` по образцу формы профиля. *Обоснование:* одна форма, одно место, рабочая деградация без условной разметки.
- **D-12:** Ссылка с карточки ведёт на `/accounts/{id}/groups#phone`; якорь стоит на поле номера. Текст ссылки «Указать номер» / «Изменить» (D-01) выбирается по наличию номера. *Обоснование:* человек сразу попадает к полю, новый маршрут показа не нужен.
- **D-13:** Успех **с JS**: ответ — фрагмент шапки аккаунта (подпись + форма с новым значением), подпись в заголовке шелла обновляется тем же ответом, исход сообщается уведомлением из реестра `app/pages/notices.py` («Номер сохранён» / «Номер удалён», **без самого номера**). Успех **без JS**: 302 обратно на `/accounts/{id}/groups` с кодом исхода (PRG). На 422 — тот же фрагмент формы с ошибкой под полем (`respond_field_error`, образец `profile_post`), а без JS — страница целиком со статусом 422. *Обоснование:* канон контракта формы v2.1 (`respond()`), первый потребитель уведомления с фрагментом — `profile_post`.
- **D-14:** После записи обработчик **перечитывает** аккаунт и строки подписи, прежде чем рисовать ответ. Писатель работает с `synchronize_session=False`, поэтому объект той же сессии показал бы прежний номер (докстринг писателя, «Объект той же сессии устаревает»). Транзакцией владеет маршрут: коммит после писателя.
- **D-15:** Номер, совпавший с номером другого аккаунта того же пользователя, принимается молча: `UNIQUE` нет (D-02 Фазы 16), блокировка из-за дубликата — анти-функция. Такие аккаунты становятся двойниками по D-03 Фазы 17 и получают `#id`.
- **D-16:** Приватность (PHONE-21): номер не попадает ни в URL (только тело POST, без query-параметров в адресе возврата), ни в текст уведомления, ни в журнал. В журнал — только `account_id` и `phone_set=True/False`. Запись в журнал о правке под имперсонацией — на усмотрение планировщика, но только в этой форме.

### Claude's Discretion
- Точная разметка и классы пометки «указан вручную»; имя поля признака в `AccountRow` / `AccountLabel`.
- Обновлять ли `<title>` вкладки ответом с JS (через OOB или `<title>` во фрагменте) или оставить его до перезагрузки. Шапка шелла и `<h2>` обновляются обязательно.
- `maxlength` у поля. Предел ввода держит сервер (`MANUAL_INPUT_MAX_CHARS = 32`); молча обрезать вставленный текст браузер не должен.
- `autocomplete` и `inputmode` у поля (браузер не должен подставлять собственный номер пользователя).
- Где именно на каждой из трёх форм карточки (страница, порция, фрагмент опроса) стоит ссылка «Указать номер» / «Изменить».

### Deferred Ideas (OUT OF SCOPE)
Нет: обсуждение осталось в границах фазы.

Reviewed Todos (not folded): `classify-420-prohibitions-outside-phase-10.md`, `full-suite-ads-editor-order-pollution.md`, `send-code-status-reveals-account.md` совпали с фазой только по общим словам (score 0.2) и к ручной правке номера не относятся. В объём не взяты, как и в Фазе 17.

Вне фазы (из «Phase Boundary»): захват номера при подключении и `phone` в `/status` воркеров (Фаза 19), дозаполнение существующих аккаунтов (Фаза 20), перенос ручного номера при переподключении, предупреждение о расхождении ручного номера с номером сессии, JS-маска ввода и SMS-подтверждение.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PHONE-08 | у номера, указанного вручную, видна пометка «указан вручную» | §5 (все пути до макроса; макрос напечатан и снят на прототипе), §9 (35 ожидаемо красных правил при обязательном поле), §Pitfall 8 (CSS-контракт 17-09) |
| PHONE-09 | пользователь может указать, изменить или очистить номер своего аккаунта в любой момент — с JS и без; свободный ввод; неверный ввод → 422 по-русски с сохранённым введённым значением | §1 (писатель и нормализатор прогнаны), §2 (маршрут, порядок проверок), §3 (форма, страница-фолбэк 422), §4 (ответ с JS) |
| PHONE-10 | после очистки снова «Номер неизвестен», автоматические источники снова вправе заполнить номер | §1 [ЗАМЕР] сценарий критерия 3: `KEPT` → очистка → `WRITTEN`; §12 цель RED |
| PHONE-11 | администратор под имперсонацией может править номер аккаунта пользователя; чужой аккаунт отвечает как несуществующий | §2 (ключ `ALLOWED_ROUTES`, прецедент теста `test_impersonation.py:1254`), §7 строка 1 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Из `/source/broadcaster/CLAUDE.md` и `/source/broadcaster/.claude/CLAUDE.md` [ПРОЧИТАНО]:
- Стек: Python 3.12 + `uv`, FastAPI + SQLAlchemy async + Jinja2; команды проекта через `just` (`just test` = `uv run pytest tests/ -v`, `just upgrade` и т. д.). Тесты — `sqlite+aiosqlite:///:memory:` с полной схемой на тест, фикстуры `client`, `db_session`, `auth_headers`, `authed_client` (`tests/conftest.py`).
- `graphify`: для вопросов о коде сначала `graphify query "<вопрос>"`; **после правки кода — `graphify update .`** (это правило исполнителей; исследователь его не запускал).
- Новых зависимостей фаза не вводит; новых каталогов верхнего уровня тоже.

Директивы памяти проекта, которые применимы к планированию Фазы 18 (`MEMORY.md`, [ПРОЧИТАНО]): «Cross-cutting gates skipped by executors» (в наряде каждого плана называть `test_htmx_post_pairs` и прочие поимённо); «Orchestrator gate catches records defects» (исполнители отключают `tests/test_planning/` — гонять явно); «Шаг 5.5 обнуляет VALIDATION.md» (на replan пропускать); «Гейт уникальности ID угроз» (`T-18-NN` не повторять в фазе); «Гейт до коммита в цепочке» (`pytest …; commit` коммитит и при красном — только `&&`); «Отпечаток ломается закрытием фазы», «Регрессия-гейт дублирует пост-мердж суиту» (полная суита ~46 мин, таймаут 5400 с); «Ответы владельца возвращать в RESEARCH.md» (закрытые Open Questions вернуть сюда).

## Summary

Фаза не тянет ни одного пакета: писатель, нормализатор, форма v2.1, слой ответа `respond()` / `respond_field_error()`, реестр уведомлений и помощник подписи уже в дереве. Риск фазы — **бюджет сквозных гейтов**, и он измерен, а не прогнозирован: прототип (route + форма в новом включаемом шаблоне + ответ-фрагмент с двумя внеполосными блоками + два кода реестра + флаг ручного номера в помощнике подписи + девять ссылок на карточках) собран в копиях дерева вне репозитория и прогнан через 14 модулей гейтов и три каталога тестов. Итог: **добавление одного POST и одной формы двигает 27 объявленных чисел (25 констант и два литерала `19` в тесте реестра уведомлений) в 11 файлах тестов и требует правки девяти реестров поимённо**; два из этих гейтов (`test_htmx_validation_sink`, `test_hx_location_destinations`) в брифе и в CONTEXT не названы и нашлись только полным прогоном каталога `tests/test_pages/`; весь набор зеленеет 343 passed на четырёх модулях (`test_account_groups`, `test_htmx_post_pairs`, `test_identifier_bounds`, `test_htmx_gates`) после правки и 1515 passed на `test_templates/services/application/models/repositories/scripts`, кроме 35 ожидаемо красных узлов правила подписи, которые вызваны обязательным четвёртым полем `AccountRow` (§9).

Главные находки, меняющие план:
1. **Числа гейтов нельзя править «потом»**: каждое сдвигается в тот же момент, как маршрут появился. Маршрут, форма, коды реестра, реестры гейтов и тесты — **один атомарный план**; план флага ручного номера в помощнике (35 ожидаемых красных) — отдельный и независимый от него.
2. **Три ловушки, которые прототип поймал сам**: (а) `db.rollback()` на ветке `PhoneError` истекает `user` и роняет следующий `user.id` ошибкой `MissingGreenlet` (500) — откат не нужен, писатель падает ДО обращения к базе; (б) включение формы в `list.html` с `{% with phone_value = … %}` затирает контекст и теряет эхо введённого значения на странице 422 (измерено: `value="abc"` на странице отсутствует) — значения обязан класть в контекст обработчик; (в) `phone: str = Form("")` стирает номер при POST **без поля** вовсе (измерено: 302 `phone_cleared`) — «пусто» и «поля нет» разные состояния.
3. **`<title>` и шелл обновляются тем же ответом без нового механизма**: у проекта есть два прецедента — `<title>` прямым потомком ответа (`app/templates/auth/includes/step_response.html:13`) и внеполосный блок `innerHTML:#id` (`count_rule_oob.html`, `notice_oob.html`). Цена — два новых `hx-swap-oob` (счётчик `OOB_BLOCKS` 22 → 24) и два новых `id` (`<h2>` экрана и `<h1>` шелла в `base.html`).
4. **Формулировка D-05 уточняется**: для POST граница `ID_MAX` — это `PostIdPath` плюс `id_in_column()` первым использованием, а не `IdPath` (последний — псевдоним GET; `app/pages/identifiers.py:103, 132`). Это не конфликт с решением, а его форма, принятая в проекте (Фаза 11, D-07).
5. Гейты номера Фазы 16 (`privacy` 346, `parity` 143, `single-writer` 672, `runtime guard` 77) **зелены на странице, которая впервые зовёт писателя**, без правки списков допущенных вызывающих: гейты судят формы записи в колонку и вызовы журнала, а вызов `set_manual_phone` формой записи не является (измерено на прототипе, плюс отрицательный контроль: `logger.info(..., phone=saved)` краснит приватность с адресом `app/pages/account_groups.py:960`).

**Primary recommendation:** три плана — (1) `type: tdd`, флаг `phone_is_manual` в `AccountRow`/`AccountLabel`/загрузчике/`SyncStatusView`/макросе + CSS части «указан вручную»; (2) `type: tdd`, атомарный: маршрут, форма, ответ-фрагмент, страница 422, коды реестра, **все** девять реестров гейтов и тесты маршрута; (3) `type: tdd` либо `execute` с тестом, написанным в том же плане до правки, — ссылки на девяти местах карточек. Порядок волн: (1) → (2) → (3); (2) зависит от (1) по посеву ручного номера в тестах (`tests/account_label_support.py`) и по показу пометки в ответе, (3) — по общему файлу `test_responsive_markup.py`. В `<automated>` каждого плана — поимённо модули из §7 (**одиннадцать** с правкой чисел и `test_write_path_invariants` без правки — он читает чужую константу; список D-08 неполон) и `tests/test_planning/`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Нормализация и запись номера | Application (`app/application/accounts/phone.py`) | Database (UPDATE одним оператором) | Единственный писатель D-13 Фазы 16; страница его только зовёт |
| Проверка владельца аккаунта, происхождения запроса, границы `ID_MAX` | Frontend Server (страничный обработчик) | — | Писатель владельца не проверяет (T-16-19); `is_same_origin` и `id_in_column` — гарды страничного слоя |
| Форма ввода и её деградация без JS | Frontend Server (Jinja2: `form_wrapper`, `field`) | Browser (htmx — только улучшение) | `method="post"` и `action` печатает макрос; `hx-post` ему посимвольно равен |
| Ответ: PRG / фрагмент / 422 | Frontend Server (`respond()`, `respond_field_error()`) | Browser (htmx swap) | Форму ответа выбирает слой ответа, обработчик подаёт сборщики |
| Правило пометки «указан вручную» и ключ двойника | Domain/service (`app/services/account_label.py`, чистая функция) | Jinja2 (макрос рисует `<span>`) | Один источник правила; разметка из Python запрещена (`MARKUP_BUILDERS = 0`) |
| Обновление шапки шелла, `<h2>` и `<title>` | Browser (htmx OOB / top-level `<title>`) | Frontend Server (собирает один ответ) | Шелл живёт вне основной цели подмены |
| Уведомление об исходе | Frontend Server (реестр `app/pages/notices.py` + `_glue_notice`) | Browser (область `#notice`) | Код едет константой, текст — из закрытого реестра |
| Ссылка «Указать номер» / «Изменить» | Frontend Server (три шаблона карточек × три ветки статуса) | — | Выбор текста по `acct_label.phone_text` — данные уже в контексте всех трёх |

## Standard Stack

Фаза **не вводит ни одного нового пакета** [ВЫВОД: прототип собран из существующих модулей; `uv.lock` не менялся].

### Core (уже в проекте)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.129.0 | маршрут `POST /accounts/{id}/phone`, `Form`, `Depends` | `[ЗАМЕР: .venv/bin/python importlib.metadata]` |
| Starlette | 0.52.1 | ответы `HTMLResponse`, `Response` | там же |
| SQLAlchemy (async) | 2.0.46 | `AsyncSession`, UPDATE писателя | там же |
| Jinja2 | 3.1.6 | `form_wrapper`, `field`, макрос подписи, автоэкранирование | там же |
| phonenumbers | 9.0.41 | нормализация (внутри `app/services/phone.py`) | `[ЗАМЕР: import phonenumbers; __version__]` |
| htmx (вендорен) | 2.0.10 | подмена фрагмента, OOB, `<title>` верхнего уровня | `[ПРОЧИТАНО: докстринги delete_response/htmx_config — «version 2.0.10»]` |
| pytest / pytest-asyncio / httpx | 9.0.2 / 1.3.0 / 0.28.1 | суита | `[ЗАМЕР]` |

### Supporting
Модули проекта, которые план обязан использовать, а не заводить заново: `app/application/accounts/phone.py::set_manual_phone`, `app/services/phone.py` (`PhoneError`, `EXAMPLE_PHONE`, `MANUAL_INPUT_MAX_CHARS`), `app/pages/htmx.py::respond`, `::respond_field_error`, `app/pages/notices.py`, `app/pages/identifiers.py::PostIdPath`, `::id_in_column`, `app/pages/common.py::is_same_origin`, `app/services/account_label.py`, `app/application/accounts/labels.py::load_account_rows`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Новый включаемый шаблон `phone_form.html` | Форма прямо в `list.html` | Меньше сдвигов гейтов (файлы 27/29 не двигаются, вызывающий `form_wrapper` не добавляется), но **ответу-фрагменту (D-13) нечего включать**: вторая копия формы разошлась бы с первой молча — проект ровно этого не допускает (`profile_settings.html`, шапка «ЕДИНСТВЕННЫЙ ИСТОЧНИК ЭТОЙ ФОРМЫ») |
| Два внеполосных блока (`<h2>` и `<h1>`) | Один: `<h2>` внутри основной цели, `<h1>` внеполосно | на 1 меньше `OOB_BLOCKS`; цена — цель подмены разрастается до узла, где живёт ещё и строка идентичности, а форма внутри `.acct-head__id` меняет раскладку шапки (решает UI-SPEC, не исследование) |

**Installation:** не требуется. **Version verification:** версии сняты командой из таблицы; реестр пакетов не опрашивался — новых имён нет.

## Package Legitimacy Audit

Фаза не устанавливает внешних пакетов — аудит неприменим: `uv.lock`, `pyproject.toml` не затрагиваются. **Packages removed due to [SLOP] verdict:** none. **Packages flagged [SUS]:** none.

## Метод и границы замера

- Старт: HEAD `5a75f567` `[ЗАМЕР: git rev-parse --short HEAD]`. Дерево копировано `git -C /source/broadcaster archive HEAD | tar -x -C <scratch>/tree` (копии `tree_a`…`tree_d` — стадии прототипа), планировочная суита — в `git clone --no-hardlinks` (`<scratch>/clone`).
- Прогон: `cd <копия> && UV_PROJECT_ENVIRONMENT=/source/broadcaster/.venv uv run --frozen --no-sync pytest <модуль> -q -p no:randomly --no-header -p no:cacheprovider -rf`. `app` в копии разрешается из копии (`python -c "import app; print(app.__file__)"` печатает путь копии) `[ЗАМЕР]`.
- Прототип (в копии): handler `account_phone_save` в `account_groups.py`; `account_groups/includes/phone_form.html`; `account_groups/partials/phone_response.html`; id на `<h2>` и `<h1>`; два кода реестра; флаг ручного номера в помощнике; девять ссылок на карточках; числа гейтов выставлены **прогоном покрасневшего правила**, а не вычитанием.
- **Каскад утверждений.** Часть гейтов утверждает числа по цепочке (`assert A; assert B`): первое красное скрывает второе. Поэтому числа ставились итеративно: правка → прогон → следующее красное. Так найдены числа, которые первый прогон не показывал (`MUTATING_MODULE_COUNT` — на самом деле неподвижен; `DUAL_BRANCH_PLACES_DECLARED`, `ORIGIN_GUARD_CALL_SITES_MEASURED`, `CATALOGUE_UNIVERSE_DECLARED`, `PAIRED_302_ASSERTIONS_DECLARED`, `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED`).
- **Чего замер не доказывает.** Браузера нет: суита не исполняет JS, поэтому «OOB-блок реально подменил `<h1>`», «`<title>` сменился», «якорь `#phone` прокрутил к полю» — предмет ручного обхода (раздел «Validation Architecture», Manual-Only). Цифры ниже верны **для раскладки прототипа** (новый включаемый файл формы с одним вызовом `form_wrapper` и `target=`; ответ-фрагмент с двумя `hx-swap-oob`; один `Response(status_code=403)`; два утверждения 302 на литеральном адресе; два случая пары). Для иной раскладки в §7 приведена формула «что двигает».

## 1. Писатель и нормализатор: что дерево уже умеет

**Писатель** `[ПРОЧИТАНО: app/application/accounts/phone.py:216-241]`:
`async def set_manual_phone(session: AsyncSession, account_id: int, text: str | None) -> str | None` — `None`/пустая/пробельная строка очищают (`values(phone=None, phone_is_manual=False)` одним UPDATE), иначе `normalize_manual(text)` и `values(phone=e164, phone_is_manual=True)`; `PhoneError` поднимается **до обращения к базе**; `LookupError(f"аккаунт {account_id} не найден")` при `result.rowcount != 1`; операторы идут `synchronize_session=False, autoflush=False` под `writer_scope()`; **не коммитит**. Дословно из докстринга модуля (строки 61-63): «не проверяет владельца аккаунта: принимает только `account_id`, а проверку «аккаунт принадлежит пользователю» делает вызывающая страница Фазы 18» — T-16-19 подтверждён кодом: у функции нет ни параметра пользователя, ни запроса владельца.

**Нормализатор** `[ЗАМЕР: normalize_manual на 10 вводах]`: `'8 999 123 45 67'` → `+79991234567`; `'+7 (999) 123-45-67'` → `+79991234567`; `'+7 999 123-45-67'` (форма показа) → `+79991234567` — то есть D-11 «нормализатор принимает её обратно» подтверждён; `'  8-999-123-45-67 '` → `+79991234567`. Отказы (тексты — константы, ввод в них не подставляется): `''` → `PHONE_ERROR_BLANK` «Введите номер телефона. Пример: +7 999 123-45-67»; `'abc'` → `PHONE_ERROR_NOT_A_NUMBER` «Не похоже на номер телефона. Пример: +7 999 123-45-67»; с «доб 12» → `PHONE_ERROR_EXTENSION`; 33 символа → `PHONE_ERROR_TOO_LONG` «Слишком длинный ввод: не больше 32 символов и 15 цифр. Пример: +7 999 123-45-67». Константы: `MANUAL_INPUT_MAX_CHARS = 32`, `EXAMPLE_PHONE = "+7 999 123-45-67"` `[ПРОЧИТАНО: app/services/phone.py:153, 156]`.

**Устаревание объекта (D-14)** `[ЗАМЕР: probe, writer → stale]`: до записи `acc.phone == '+79990000000'`; писатель вернул `+79991234567`; **объект той же сессии по-прежнему `+79990000000, False`**, и после `commit()` тоже (в сессии проекта объекты после коммита не истекают — `user.id` читался после коммита без обращения к базе); только `await db.refresh(acc)` даёт `+79991234567, True`. [ВЫВОД] Источник «свежих» данных для ответа — либо `refresh(account)`, либо проекция колонок `load_account_rows` (SELECT колонок идёт в базу и видит UPDATE той же транзакции) — подпись из `label_of(<строка из load_account_rows>, rows)`. Нельзя строить подпись из ORM-объекта, загруженного до записи (`row_of(account)`): страничный путь делает именно так (`account_groups_page`), и это верно для GET, неверно для ответа после записи.

**Критерий 3 как сценарий** `[ЗАМЕР: probe, одна сессия]`: ручной номер стоит → `fill_reported_phone(…, "+79995556677")` вернул `PhoneWrite.KEPT` → `set_manual_phone(…, "   ")` вернул `None` → после `commit` `fill_reported_phone(…)` вернул `PhoneWrite.WRITTEN` → строка `('+79995556677', False)`. Это готовый тест PHONE-10.

**D-15** `[ЗАМЕР]`: второму аккаунту того же пользователя тот же номер записывается молча (`set_manual_phone` вернул `+79995556677`).

**Пробельная строка длиннее 32 символов** `[ВЫВОД из phone.py:225-227 и services/phone.py:325-328]`: `set_manual_phone` проверяет `not text.strip()` ДО `normalize_manual`, поэтому 40 пробелов — очистка, а не `TOO_LONG`. Достижимо только не-браузером (`maxlength` режет ввод у людей).

## 2. Маршрут `POST /accounts/{id}/phone`

### Порядок проверок (повторяет `account_groups_delete`, `app/pages/account_groups.py:714-736`)
1. `user = await get_user_from_cookie(...)`; нет → `return await respond(request, redirect="/login")`.
2. `if not is_same_origin(request): return Response(status_code=403)` — **форма отказа одна на проект**: `test_every_origin_guard_site_answers_the_refusal_of_the_existing_consumers` (`tests/test_pages/test_write_path_invariants.py:503`) требует ветку отказа, равную дословно `return Response(status_code=403)`; с телом (`content=`) — красное. Стоит **ВЫШЕ** выборки аккаунта (отказ по происхождению не должен стать признаком существования строки — `app/pages/account_groups.py:718-725`).
3. Граница `ID_MAX`: параметр пути — **`PostIdPath`**, а не `IdPath`; первым использованием — `id_in_column(account_id)` `[ПРОЧИТАНО: app/pages/identifiers.py:103 «IdPath = Annotated[int, Path(ge=1, le=ID_MAX)]», :132 «PostIdPath = Annotated[int, Path()]»]`. Ложь не заводит своей ветки и идёт веткой «нет аккаунта». Правило: `tests/test_pages/test_identifier_bounds.py::test_every_post_identifier_is_checked_before_its_first_use` (:2344) и каталог `CATALOGUE_UNIVERSE_DECLARED` (+1, §7).
4. `account = await _load_owned_account(db, user, account_id)` (`:122-132`); `None` → `return await respond(request, redirect="/accounts")` — тот же адрес, что у `account_groups_page` для чужого и несуществующего (`:225`). Измерено: несуществующий id → `302 /accounts`; `/accounts/99999999999/phone` (вне колонки) → `302 /accounts` `[ЗАМЕР: probe3]`.
5. `saved = await set_manual_phone(db, account_id, phone)`; `except PhoneError as refusal` → `respond_field_error(request, page=…, fragment=…)`; `except LookupError` → `respond(request, redirect="/accounts")` (D-05: «так же, как несуществующий»).
6. `await db.commit()` (транзакцией владеет маршрут; писатель не коммитит).
7. Журнал — **ровно** `logger.info("account_phone_saved", account_id=account_id, phone_set=saved is not None)` `[ЗАМЕР: privacy 346 passed, parity 143 passed]`.
8. `respond(request, redirect=f"/accounts/{account_id}/groups#phone", notice=notices.PHONE_SAVED if saved else notices.PHONE_CLEARED, fragment=_saved)`.

### Что измерено на ответах `[ЗАМЕР: probe, probe3]`
| Запрос | Ответ |
|---|---|
| без htmx, годный номер | `302`, `Location: /accounts/1/groups?notice=phone_saved#phone` (номера в адресе нет — D-16; код исхода — константа реестра) |
| без htmx, очистка (`phone=` пустое) | `302`, `…?notice=phone_cleared#phone` |
| с htmx, годный | `200`, тело начинается `<title>…</title>`, затем форма `<div id="acct-phone" data-acct-phone>`, два внеполосных блока, в конце приклеенный `notice_oob` («Номер сохранён»); заголовков `HX-*` нет |
| без htmx, мусор | `422`, **страница целиком** (`<!DOCTYPE`, `data-acct-head`), эхо `value="abc"` и текст ошибки — **только после исправления прототипа** (см. Pitfall 2) |
| с htmx, мусор | `422`, фрагмент без `<!DOCTYPE`, эхо и текст ошибки, без плашки аварии |
| чужой/нет аккаунта/вне колонки | `302 /accounts` (с htmx — `respond` отдаёт 204 + `HX-Location`) |
| чужой источник (`Origin: http://evil.example`) | `403`, тело пустое |
| 33 символа | `422` + «Слишком длинный ввод…» |

«Плашка аварии не поднимается» (критерий 2): `app/templates/includes/htmx_config.html:194` `{"code":"422", "swap": true, "error": true}` и `includes/htmx_error_banner.html:314` `if (event.detail && event.detail.xhr && event.detail.xhr.status === 422) { return; }` `[ПРОЧИТАНО]` — 422 свопается и не поднимает плашку. Суита этого не исполняет (нет JS) — это предмет обхода.

### Имперсонация (D-06, PHONE-11)
- У маршрута **нет** `Depends(forbid_when_impersonating)` (как у `profile_post`, `app/pages/profile.py:82`, он есть). Ключ в `ALLOWED_ROUTES`: `"app/pages/account_groups.py::<имя обработчика>": "номер — подпись, а не учётные данные; на доставку не влияет"` — форма ключа `модуль::функция`, причина непустая (`test_every_allowed_route_carries_a_reason`, `test_impersonation_gate.py:773`) `[ПРОЧИТАНО: :217-303]`. Без записи красны `test_every_mutating_route_is_classified` («app/pages/account_groups.py::account_phone_save» назван в отказе) и `test_control_positive_the_untouched_source_tree_keeps_the_gate_green` `[ЗАМЕР]`.
- Имя обработчика выбирается один раз и **повторяется в девяти реестрах** (§7); прототип звал его `account_phone_save`.
- **Прецедент поведенческого теста разрешения** — `tests/test_pages/test_impersonation.py:1254-1284` (`test_the_group_toggle_is_allowed_under_another_identity`): `_seed_target`, `_seed_account_with_group` (`:1022`), `_enter` (`:72`), затем POST, утверждение `IMPERSONATION_REFUSAL_MARK not in _detail_of(response)` (`:1011`, «чужой учётной записью») **и** факт состоявшейся записи — «отказ, пришедший редиректом, кодом от успеха неотличим». Для номера — прочитать `phone`/`phone_is_manual` из базы после запроса. [ВЫВОД] Не утверждать `status_code == 302` в этом тесте — иначе +1 к `PAIRED_302_ASSERTIONS_DECLARED` (§7); утверждение по состоянию базы дешевле и сильнее.

### Собственный выход и реестр `OWN_RESPONSE_EXITS`
Форма отказа гарда — `Response(status_code=403)` (собственный выход мимо слоя ответа). Каждый такой обработчик обязан быть в `OWN_RESPONSE_EXITS` (`tests/test_pages/test_htmx_gates.py:5106`): без записи красен `test_every_own_response_exit_of_a_converted_handler_is_declared` — «НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::account_phone_save (вид Response(status_code=403))» `[ЗАМЕР]`. Запись: `_OwnResponseExit(entry=…, kind="Response(status_code=403)", reason=_OWN_RESPONSE_PRICE + ". " + _OWN_RESPONSE_ORIGIN_GUARD, lifting_condition=LIFTING_CONDITION_OWN_RESPONSE, decision_state=DECISION_OWNER_D08)` — на прототипе принято прогоном (правила полноты и обоснования зелены); готовые константы `_OWN_RESPONSE_PRICE` (:5062) и `_OWN_RESPONSE_ORIGIN_GUARD` (:5092) переиспользуются, как у остальных девяти записей.

### G-2: обработчик, идущий через `respond()`, не строит редирект сам
Правило `_builds_own_redirect` (`test_htmx_gates.py:1192-1222`) — разбор AST: вызов `RedirectResponse(...)` либо `status_code=302` / `HTTP_302_*` в ключевом аргументе. `Response(status_code=403)` не подпадает. Докстринг обработчика под правило не попадает (проза не есть узел `Call`), но проект соблюдает идиому «имена набраны словами» — повторять её.

## 3. Форма v2.1 и страница-фолбэк

**Что поддерживает макрос поля** `[ПРОЧИТАНО: app/templates/components/field.html:7]`: `field(name, label=None, type='text', value='', required=false, placeholder=None, autocomplete=None, id=None, hint=None, error=None, maxlength=None, minlength=None, pattern=None, inputmode=None, align=None, disabled=false, readonly=false, step=None, min=None, max=None)` — `type="tel"`, `autocomplete`, `inputmode`, `maxlength`, `id` (якорь `#phone`), `hint` (`<span class="field__hint">`), `error` (`field--invalid`, `aria-invalid="true"`, `<span class="field__error">`) **есть**; ничего расширять не надо.

**Обёртка** `[ПРОЧИТАНО: components/form_wrapper.html:187-189]`: `<form method="post" action="{{ action }}" hx-post="{{ action }}" class="form-wrapper"` — `action` и `hx-post` печатают одно выражение `{{ action }}` (гейт G-4 сравнивает сырые строки шаблона).

**Прототип формы** (напечатано `[ЗАМЕР: probe]`):
```html
<div id="acct-phone" data-acct-phone>
<form method="post" action="/accounts/1/phone" hx-post="/accounts/1/phone" class="form-wrapper" hx-target="#acct-phone" hx-swap="outerHTML" hx-disabled-elt="find button[type=submit]" hx-indicator="find .form-busy">
  <label class="field" for="phone"><span class="field__label">Номер телефона</span><input class="field__input" type="tel" name="phone" id="phone" value="+7 999 123-45-67" autocomplete="off" maxlength="32" inputmode="tel"><span class="field__hint">Пример: +7 999 123-45-67</span></label>
  <button class="btn btn--primary" type="submit"><span class="btn__label">Сохранить</span></button>
  <span class="form-busy" aria-hidden="true"></span>
</form>
</div>
```
Прецедент поля номера в дереве — форма MAX-мастера `app/templates/accounts/includes/max_connect_step.html:66`: `field(name="phone", label='Номер телефона', type='tel', value=phone or '', placeholder='+7 999 123-45-67', required=true, autocomplete='tel')` `[ПРОЧИТАНО]` — там человек вводит СВОЙ номер, и `autocomplete='tel'` уместен; здесь обратная цель (D-решение «браузер не должен подставлять собственный номер пользователя»), поэтому значение другое. Рекомендация по полям `[ОЦЕНКА]`: `autocomplete="off"`, `inputmode="tel"`, `maxlength=32` (константа `MANUAL_INPUT_MAX_CHARS` едет в контекст, не литералом в шаблоне — второй экземпляр величины разошёлся бы молча, как `PAGE_SIZE`, `account_groups.py:281-285`); пример для подсказки — тоже из контекста (`EXAMPLE_PHONE`).

**Страница-фолбэк 422** (D-13): `respond_field_error(request, page=_page, fragment=_fragment)` — без адреса деградации (редиректить некуда, введённое потерялось бы) `[ПРОЧИТАНО: app/pages/htmx.py:903-957]`; ответ — **свежий** `HTMLResponse(body, status_code=422)`, поэтому сборщик обязан вернуть ответ с `.body` (не потоковый) — иначе `ValueError` (`:1010-1019`). Страница-сборщик — полноценная `account_groups/list.html` с контекстом страницы: **контекст экрана сейчас собран внутри `account_groups_page`** (`account_groups.py:227-291`), его надо вынести в помощник **в том же модуле** (`_screen_context`), потому что гейт пути деградации считает достижимость по цепочке функций внутри модуля — помощник, вынесенный наружу, унёс бы имя шаблона (`account_groups.py:177-181`, докстринг `_group_counts`). На прототипе вынос сделан, страница 422 печатает `<!DOCTYPE`, `data-acct-head`, `value="abc"`, «Не похоже на номер» и проходит `test_account_groups` + `test_htmx_gates` (343 passed). Кроме эха, сборщик ставит в контекст `phone_value=<присланное>`, `phone_error=<константа PhoneError>`.

**Текст ошибки — `str(PhoneError)`** (одна из четырёх констант `PHONE_ERROR_MESSAGES`); `PHONE_ERROR_BLANK` до формы не доходит никогда — пустой ввод очищает (D-09). Докстринг обработчика обязан записать это решение (требование D-09).

## 4. Шапка шелла, `<title>` и `<h2>`: как обновить одним ответом

Сегодня: `<title>` печатает `{% block title %}{{ acct_label.plain }} — группы аккаунта — Broadcaster{% endblock %}` (`account_groups/list.html:17`), шелловый `<h1 class="head-title">` — блок `page_title` (`base.html:231`; сам `<h1>` **без `id`**), `<h2 class="acct-head__name">` — `list.html:55` (**без `id`**) `[ПРОЧИТАНО]`. Тест на странице считает `data-account-label="<id>"` ровно дважды (`test_account_label_groups.py:60-70`): `h1` и `h2`.

**Прецеденты механизмов в дереве** `[ПРОЧИТАНО]`:
| Механизм | Где | Что даёт |
|---|---|---|
| `<title>` **прямым потомком** ответа | `app/templates/auth/includes/step_response.html:13` (докстринг :3-12: «Рантайм берёт заголовок вкладки частичного ответа только с узла верхнего уровня: вложенный в обёртку заголовок вкладку не сменит и сам уедет в разметку элементом») | смена заголовка вкладки без OOB; приклейка `_glue_notice` дописывает блок в конец, `<title>` остаётся первым узлом `[ЗАМЕР: тело ответа на прототипе]` |
| внеполосный блок `innerHTML:#id` | `account_groups/partials/count_rule_oob.html:67` `<div hx-swap-oob="innerHTML:#account-groups-count">…</div>`; `includes/notice_oob.html:58-60` | подмена СОДЕРЖИМОГО цели, цель остаётся на странице |
| цель шелла в области уведомления | `includes/notice_area.html` (`#notice`, `#notice-alert`) | прецедент внеполосной цели в шелле (но не в заголовке) |

**Рекомендация** `[ОЦЕНКА, подтверждено прототипом]`: (а) `<title>` — прямым потомком ответа (решение остаётся за планировщиком по CONTEXT, но прецедент есть и числа гейтов он **не двигает**: `<title>` — не `hx-swap-oob`); (б) `<h2>` и `<h1>` — внеполосные блоки `<span hx-swap-oob="innerHTML:#acct-head-name">` и `<span hx-swap-oob="innerHTML:#page-title">`, внутри `account_label(acct_label, show_channel=true)`; (в) два новых `id` — на `<h2>` (`list.html:55`) и на `<h1>` (`base.html:231`, строка общая для **всех** страниц: `<h1` остаётся одним — `test_shell.py:747 html.count("<h1") == 1`, на прототипе зелено). Имена `id` — на усмотрение планировщика; используемые прототипом `acct-head-name`, `page-title` свободны в дереве.

**Правила, которые это задевает (все прогнаны):** `OOB_BLOCKS` 22 → **24** (+1 за каждое вхождение признака в исходниках шаблонов; `hx-swap-oob` в `phone_response.html` дважды) `[ЗАМЕР: «внеполосных блоков найдено 24, объявлено 22»]`. Целевой идентификатор формы (`acct-phone`) стоит в `phone_form.html`, а блоки OOB — в `phone_response.html` — **разные файлы**, поэтому правило G-11 «нет файла, несущего и внеполосную подмену, и идентификатор цели» не краснит; держать так: id цели формы и `hx-swap-oob` в одном файле не смешивать. `OOB_TARGET_EXCEPTIONS_DECLARED = 4` и `INCLUDE_TARGET_EXCEPTIONS_DECLARED = 0` (`test_account_groups.py:5149, 3707`) **не двигаются**: цели на странице есть `[ЗАМЕР: test_account_groups зелено]`.

Размер ответа 422-фрагмента: форма достаточна; `<title>`/OOB в нём не нужны (подпись не менялась). Допустимо собирать его тем же `phone_response.html` — числа не меняются (счётчики считают файлы шаблонов, не ответы).

## 5. Помощник подписи (D-10): все пути, на которых живёт номер

[ПРОЧИТАНО] `app/services/account_label.py`: `AccountRow(NamedTuple)` — `id: int; type: str; phone: str | None` (:39-44); `AccountLabel` — `@dataclass(frozen=True, slots=True)`: `account_id, channel, phone_text, twin` (:47-54); `row_of(account)` читает `account.id, account.type, account.phone` (:104-106); `label_of(subject, rows)` (:109-122), `build_labels(rows)` (:125-137), `labels_for(accounts)` (:140-142); `_twin_key(row_type, shown)` — `(тип, готовая подпись)` (:93-101). Макрос `components/account_label.html:31-37`; только `<span>` (строку воркера админки тест режет по первому `</div>`, `test_admin_panel.py::_row_markup`).

**Источники строк подписи и что каждому добавить** (`[ЗАМЕР: grep по app/]`):
| Путь | Место | Что менять для флага |
|---|---|---|
| `load_account_rows` | `app/application/accounts/labels.py:31-38`, `select(MessengerAccount.id, .type, .phone)` | 4-я колонка `MessengerAccount.phone_is_manual`; `[AccountRow(*row) for row in result.all()]` подхватит |
| страница `/accounts` и порция | `app/pages/accounts.py:167`, `:213` — `build_labels(await load_account_rows(db, user.id))` | автоматически (через загрузчик) |
| фрагмент опроса синхронизации | `app/pages/accounts.py:1050-1051` — `label_of(AccountRow(account_id, view.messenger_type, view.phone), rows)` | **конструктор вручную**: добавить `view.phone_is_manual`; `SyncStatusView` (`dto.py:34-36`: `status, messenger_type=None, phone=None`) получает `phone_is_manual: bool = False`; четыре конструктора в `app/application/accounts/use_cases.py:58, 61, 64, 66` передают `phone=account.phone` — добавить `phone_is_manual=account.phone_is_manual` во **все четыре** (`tests/test_pages/test_account_label_accounts.py:264` — «D-18: `SyncStatusView.phone` заполняют все четыре конструктора» — прямой образец теста для флага) |
| экран групп | `app/pages/account_groups.py:232` — `label_of(row_of(account), await load_account_rows(db, user.id))` | `row_of(account)` читает ORM-атрибут — добавить `account.phone_is_manual`; предмет — **свежий** объект (GET: верно) |
| история (страница и порция) | `app/pages/history.py:673` `build_labels(await load_account_rows(...))` | автоматически |
| история — карточки списком | `app/pages/history.py:1192` `labels_for(all_accounts)` (ORM) | через `row_of` |
| CSV-карта `id → phone` | `app/pages/history.py:796` `{row.id: row.phone for row in await load_account_rows(db, user.id)}` | не меняется: CSV без пометки (D-10); `row.phone` остаётся |
| админка: история пользователя | `app/pages/admin.py:1454` `labels_for(all_accounts)` (ORM), `:1554` `build_labels(await load_account_rows(db, user_id))` | автоматически |
| админка: воркеры, очередь, карточка пользователя | глобал `phone_label(account)` → `label_of(row_of(account), ())` (`common.py:347-351`); `account` — ORM (`admin.py:833, 1033`) | через `row_of` |
| чипы расписаний | `ads/includes/sched_card.html:77, 223` `phone_labels(accounts)` → `labels_for` | через `row_of` |

[ВЫВОД] Источников, где флаг приходится передавать **руками**, два: конструктор `AccountRow` в `accounts.py:1051` и четыре конструктора `SyncStatusView` в `use_cases.py`. Все остальные пути закрываются двумя строками — колонка в `load_account_rows` и поле в `row_of`.

**Ключ двойника не включает флаг (D-10)** `[ЗАМЕР: макрос на четырёх подписях]`: при `AccountRow(1,'tg_user','+79991234567',True)` и `AccountRow(2,'tg_user','+79991234567',False)` оба `twin=True`; `plain` обоих — `Telegram +7 999 123-45-67 #1` / `#2` (без пометки); макрос печатает `…текст номера</span> <span class="acct-label__manual muted">указан вручную</span> <span class="acct-label__id …">#1</span>` — порядок «номер → пометка → `#id`» как требует D-10. Прототип печатает пометку только при `phone_is_manual and shown is not None` (флаг без номера невозможен в базе — CHECK `ck_messenger_accounts_manual_requires_phone`, `app/models/messenger_account.py:38-39` — но строка «Номер неизвестен» с пометкой была бы ложью).

**Имя поля** — на усмотрение; прототип `phone_is_manual` (то же имя, что у колонки: меньше словаря). **Обязательное ли поле у `AccountRow`?** Рекомендация: **обязательное, без умолчания** — тогда забытый конструктор падает `TypeError` громко (проект: «выдуманная подпись сообщала бы о состоянии, которого нет»), а цена — **ожидаемые красные §9** (35 узлов, все в двух файлах и все на одном `TypeError`). С умолчанием `False` красных нет, но забытый путь молча теряет пометку — «зелёное вакуумом». Для `AccountLabel` (его конструируют только `account_label.py`) — тоже обязательное.

## 6. Карточки аккаунтов: ссылка «Указать номер» / «Изменить»

[ПРОЧИТАНО] Три файла × три ветки статуса = **девять мест** «Настроить группы»: `app/templates/accounts/list.html:110, 135, 174`; `accounts/partial_cards.html:62, 87, 121`; `accounts/partials/sync_status_card.html:96, 112, 135`. В первых двух адрес строится `'/accounts/' ~ account.id ~ '/groups'`, в `sync_status_card.html` — `'/accounts/' ~ account_id ~ '/groups'` (объекта `account` у фрагмента опроса нет). Подпись во всех трёх есть как `acct_label` (`list.html:89, 122, 161`; `partial_cards.html:47, 74, 108`; `sync_status_card.html:64`), поэтому выбор текста — `acct_label.phone_text` (`None` ⇒ «Указать номер», иначе «Изменить»): **ничего нового в контекст обработчиков класть не надо** `[ЗАМЕР: прототип, три файла, девять мест — 9 замен]`.

Прототип: рядом с существующей кнопкой, `{{- link_button('Изменить' if acct_label.phone_text else 'Указать номер', '/accounts/' ~ account.id ~ '/groups#phone', variant='ghost') -}}`; ссылка стоит и в ветке `syncing`, и в `sync_failed` (проектное правило: «условная ветка, скрывающая вход, оставила бы группы синхронизирующегося аккаунта недостижимыми», `list.html:105-109`). Тесты `tests/test_templates/` целиком (включая `ModalTrigger("acc-del-", …)` по порядковым номерам форм) на прототипе зелены: ссылка — не `<form>`, порядковые номера мест формы не сдвигаются `[ЗАМЕР: C3 1515 passed]`. Правило «три файла карточки синхронны» (`test_responsive_markup.py:3006-3140`, `test_accounts_three_files_*`) — см. §9: сверка должна подтвердить, что **все три** файла получили одну и ту же ссылку.

Единственное существующее утверждение о ссылке — `tests/test_pages/test_account_groups.py:745-758` (`"Настроить группы" in html`) — не краснеет. [ВЫВОД] Тесты на новую ссылку пишутся с нуля, **до** правки шаблонов (RED: ссылки нет).

## 7. Сквозные гейты: ведомость чисел

Все «После» — **выставлены прогоном покрасневшего правила на прототипе** и в конце зелёные: `test_htmx_gates` + `test_htmx_post_pairs` + `test_identifier_bounds` + `test_account_groups` → **343 passed**; `test_impersonation_gate` 15, `test_form_inventory` 24, `test_htmx_markup_gates` 125, `test_notices_registry` 15, `test_write_path_invariants` 13, `test_origin_guard_on_destructive_routes` 12, `test_htmx_validation_sink` 8, `test_hx_location_destinations` 15 — все passed `[ЗАМЕР]`. **Список D-08 в CONTEXT неполон**: строки 10 и 11 им не названы, и красными они становятся не в модулях, которые обычно гонят исполнители, а в каталоге `tests/test_pages/` целиком.

| № | Гейт (файл) | Константа / реестр | Сегодня | После | Что двигает | Что ещё править |
|---|---|---|---|---|---|---|
| 1 | `tests/test_pages/test_impersonation_gate.py` | `MUTATING_ROUTE_COUNT` (:119) | 49 | **50** | +1 изменяющий маршрут | `ALLOWED_ROUTES` (:217) +1 ключ `"app/pages/account_groups.py::<handler>": "<причина>"` |
| 1 | там же | `MUTATING_MODULE_COUNT` (:132) | 14 | **14 (не двигается)** | модуль `account_groups.py` уже объявляет `account_groups_toggle`, `account_groups_delete` `[ЗАМЕР: после правки числа маршрутов 15 passed]` | — (второе утверждение теста скрыто первым — проверено после правки первого) |
| 2 | `tests/test_templates/test_form_inventory.py` | `WRITE_FORM_PLACES` (:166) | 49 | **50** | +1 вызов `form_wrapper` | `FORM_WRAPPER_CALLS` (:169) 29→**30**; `ALL_FORM_PLACES` (:173) 51→**52** |
| 2 | там же | `WRITE_FORM_FILES` (:167) | 27 | **28** | **только если форма в новом файле** (прототип: `phone_form.html`) | `ALL_FORM_FILES` (:174) 29→**30**. Форма в `list.html` (без файла) — файлы не двигаются |
| 3 | `tests/test_templates/test_htmx_markup_gates.py` | `OOB_BLOCKS` (:2646) | 22 | **24** | +1 за каждое вхождение `hx-swap-oob` в шаблонах | тест `test_control_negative_an_extra_oob_block_reddens_the_counter` берёт число из константы |
| 3 | там же | `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` (:5194) | 29 | **30** | +1 блок вызова `form_wrapper` | — |
| 3 | там же | `MACRO_DEFINITION_SITES_CALLERS_DECLARED` (:1829) | 32 | **33** | +1 файл-вызывающий макроса-обёртки | кортеж `MACRO_DEFINITION_SITES_CALLERS["components/form_wrapper.html"].callers` (:1454) +`"account_groups/includes/phone_form.html"` — **в отсортированном порядке: ПЕРЕД `account_groups/list.html`** (на прототипе неверный порядок дал красное) |
| 3 | там же | `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` (:2033) | 16 | **17** | форма передаёт `target=` | кортеж `PARAMETRIC_SWAP_TARGETS["components/form_wrapper.html"].callers` (:2947) +тот же файл (между `group_row.html` и `max_connect_step.html`). Без `target=` (`hx-swap="none"`) — не двигается |
| 4 | `tests/test_pages/test_htmx_gates.py` | `POST_HANDLERS` (:224) | 37 | **38** | +1 POST в `app/pages` | — |
| 4 | там же | `FRAGMENT_RESPONSE_HANDLERS_DECLARED` (:2330) | 25 | **26** | обработчик подаёт `fragment=` | множество `FRAGMENT_RESPONSE_HANDLERS` (:1959) +ключ (оно же `CHANGES_DATA_HANDLERS`, :7616) |
| 4 | там же | `TRANSITION_BRANCH_HANDLERS_DECLARED` (:6662) | 31 | **32** | есть ветка перехода (`respond(redirect=…)` без фрагмента — «нет аккаунта») | — |
| 4 | там же | `DUAL_BRANCH_HANDLERS_DECLARED` (:6691) | 19 | **20** | и фрагмент, и переход | множество `DUAL_BRANCH_HANDLERS` (:6666) +ключ; `DUAL_BRANCH_OWNER_DECISIONS` строится из него |
| 4 | там же | `DUAL_BRANCH_PLACES_DECLARED` (:6709) | 20 | **21** | место письма дуального обработчика (скрыто каскадом) | — |
| 4 | там же | `PUSH_URL_DECISIONS_DECLARED` (:6907) | 37 | **38** | +1 POST-обработчик | `PUSH_URL_DECISIONS` (:6759) +строка `(PUSH_URL_CASE_THREE, _DUAL + "<причина по веткам>")` (форма — как у `account_groups_toggle`/`profile_post`); у формы нет `hx-push-url`, ответ не шлёт `HX-Push-Url` → `HX_PUSH_URL_*` не двигаются |
| 4 | там же | `OWN_RESPONSE_EXITS_DECLARED` (:5528) | 14 | **15** | собственный `Response(status_code=403)` | запись в `OWN_RESPONSE_EXITS` (:5106), см. §2 |
| 5 | `tests/test_pages/test_origin_guard_on_destructive_routes.py` | `PAGE_POST_HANDLERS_MEASURED` (:713) | 37 | **38** | +1 POST | — |
| 5 | там же | `ORIGIN_GUARD_CALL_SITES_MEASURED` (:729) | 14 | **15** | +1 вызов `is_same_origin` с формой отказа | `test_write_path_invariants` читает ту же константу — своего числа не правит. `GATE_UNIVERSE_HANDLERS_MEASURED` (:752) = 10 **не двигается** (не маршрут подтверждённого удаления) |
| 6 | `tests/test_pages/test_identifier_bounds.py` | `CATALOGUE_UNIVERSE_DECLARED` (:1414) | 36 | **37** | +1 параметр пути-идентификатора (`account_id`) | — |
| 7 | `tests/test_pages/test_htmx_post_pairs.py` | `POST_PAIR_CASES_DECLARED` (:2416) | 77 | **77 + k** (прототип k=2 → 79) | каждый случай пары | реестр `POST_PAIR_CASES` (:1424) +≥1 `_PairCase`; замыкание `test_every_converted_handler_has_a_pair` красно, пока случая нет |
| 7 | там же | `PAIRED_302_ASSERTIONS_DECLARED` (:3418) | 191 | **191 + m** (прототип m=2 → 193) | каждое `assert … .status_code == 302` на **POST с литеральным адресом** во всех тестах **кроме** самого модуля пар | отказ: «утверждений 302 о переведённых обработчиках 193, объявлено 191. Поставьте число ПРОГОНОМ этого отказа» `[ЗАМЕР]` |
| 8 | `tests/test_pages/test_account_groups.py` | `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED` (:3593) | 61 | **62** | +1 место, отправляющее POST, **на странице экрана групп** (подстановка `re.subn` идёт по живой странице) | `INCLUDE_TARGET_EXCEPTIONS_DECLARED` 0 и `OOB_TARGET_EXCEPTIONS_DECLARED` 4 — не двигаются |
| 9 | `app/pages/notices.py` + `tests/test_pages/test_notices_registry.py` | `NOTICES` (кортеж), `DECLARED_CODES` (:84), `len(codes) == 19` (:277) | 19 записей | **21** | +2 кода: `PHONE_SAVED = "phone_saved"`, `PHONE_CLEARED = "phone_cleared"` | в `notices.py` — константа **и** `Notice(...)`; в тесте — `DECLARED_CODES` +2 строки, **два** литерала `19` в `test_every_code_is_distinct_and_the_index_loses_nothing` (:277 и :278); `MOVED_TEXTS` не нужен (новые тексты, не перенос) |
| 10 | `tests/test_pages/test_htmx_validation_sink.py` | `VALIDATION_SINK_ROUTES_DECLARED` (:106) | 27 | **28** | +1 маршрут страничного слоя с целым параметром пути (`account_id`) — пара «метод + путь» в обходе | отказ: «пар обхода страничного слоя стало 28, в летописи записано 27» `[ЗАМЕР]`; `JSON_API_BOUNDARY_ROUTES_DECLARED` = 8 не двигается. **Гейт не назван ни в CONTEXT D-08, ни в брифе — найден полным прогоном `tests/test_pages/`** |
| 11 | `tests/test_pages/test_hx_location_destinations.py` | `HX_LOCATION_DESTINATION_CALLS_DECLARED` (:506) | 81 | **84** | +1 за **каждый** вызов `respond(...)` БЕЗ `fragment=` в новом обработчике; прототип: три — `/login`, `/accounts` («нет аккаунта»), `/accounts` (`LookupError`) | число = число таких вызовов: **сведение двух выходов «нет аккаунта» и `LookupError` в один вызов даёт 83** (решение планировщика; неотличимость при этом не страдает). Адреса `/login` и `/accounts` в карте назначений уже есть, `test_every_transition_destination_has_a_declared_template` не краснеет. Отказ: «вызовов слоя ответа БЕЗ фрагмента найдено 84, а объявлено 81» `[ЗАМЕР]`. **Не назван ни в CONTEXT, ни в брифе** |

**Формулы на случай иной раскладки** (чтобы планировщик пересчитал сам и проверил прогоном): +1 `OOB_BLOCKS` за каждое вхождение `hx-swap-oob`; +1 `PAIRED_302…` за каждый новый `status_code == 302` на POST-литерале вне модуля пар; +1 `POST_PAIR_CASES_DECLARED` за случай пары; `target=` у `form_wrapper` ⇒ +1 в параметрических вызывающих; новый файл с `form_wrapper` ⇒ +1 `WRITE_FORM_FILES`, `ALL_FORM_FILES`, `MACRO_DEFINITION_SITES_CALLERS_DECLARED`; форма на странице экрана групп ⇒ +1 `SUBSTITUTED_INCLUDE…`.

**Что проверено и НЕ двигается** (зелёное на прототипе): `FRAGMENT_ROUTES_DECLARED` = 11 (обработчик идёт через `respond`, у него есть путь деградации), `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` = 0, `RETARGET_RESWAP_USES_DECLARED` = 1, `HX_HEADER_READS` = 1 / `HX_HEADER_WRITES` = 6, `HX_PUSH_URL_*`, весь `tests/test_templates/test_htmx_inventory.py` (30 passed), `test_markup_literal_inventory.py`, `test_components.py`, `test_account_label_gate.py` (внутри C3: 1515 passed).

**Правило полноты по 302 и литеральный адрес.** В обходе `_post_302_assertions` (`test_htmx_post_pairs.py:2971-3026`) адрес POST читается из присваивания имени ответа: f-строка с подстановками (`f"/accounts/{aid}/phone"`) разбирается плейсхолдерами и сличается с таблицей маршрутов приложения; адрес, собранный выражением (`action.group(1)`), не разбирается и даёт запись «без обработчика» — а её надо вносить в `UNATTRIBUTED_302_ASSERTIONS` с обоснованием (не делать) `[ПРОЧИТАНО: :2933-2946, :3073-3129]`. Независимый счёт `_lexical_302_comparisons` обязан совпасть с числом разобранных — расхождение «форма записи ушла из-под обхода».

## 8. Гейты номера Фазы 16 применительно к странице, которая впервые ПИШЕТ номер

[ЗАМЕР: прототип с вызовом писателя и с журналом из §2 п. 7] `tests/test_phone_privacy_gate.py` **346 passed**; `tests/test_phone_gates_parity.py` **143 passed**; `tests/test_application/test_phone_single_writer_gate.py` **672 passed**; `tests/test_application/test_phone_writer_runtime_guard.py` **77 passed**.

- **Допусков вызывающих списка нет**: гейт писателя (`test_phone_single_writer_gate.py`) судит ФОРМЫ записи в колонку (присваивание атрибуту, `update(...).values(phone=…)`, `bulk_update_mappings`, `setattr`, `set_committed_value`, их псевдонимы и носители) во вселенной `app/**/*.py` и `scripts/**/*.py` — модуль добавляется под гейт сам. Вызов `await set_manual_phone(...)` формой записи не является; расширять нечего `[ПРОЧИТАНО: шапка гейта :1-90]`, `[ЗАМЕР]`.
- **Новый маршрут и шаблон внутри вселенной автоматически** (обход каталогов, не перечень). Обязанность новых файлов — не вводить **ни одной** формы записи в `phone`/`phone_is_manual` вне писателя.
- **Журнал** (PHONE-21, D-11/D-16): положительный контроль — `logger.info("account_phone_saved", account_id=account_id, phone_set=saved is not None)` зелен; отрицательный — `…, phone=saved` даёт `tests/test_phone_privacy_gate.py::test_no_number_reaches_a_python_log_call_in_the_live_trees`: «app/pages/account_groups.py:960 — имя — phone= (владелец account_phone_save)» `[ЗАМЕР]`. Правило судит **имя** аргумента и значения опознания: не передавать в вызов журнала `phone`, `text`, `saved`, `acct_label`, `.plain` — только `account_id` и булево `phone_set`.
- **Номер в URL.** Путь запроса попадает в событие `request` каждого ответа (`app/services/log_masking.py` докстринг «CR-07 … путь запроса попадает в событие `request` (`RequestIdMiddleware`)»); адрес маршрута `/accounts/{id}/phone` номера не содержит, номер едет только телом POST `[ВЫВОД]`. Код исхода в `Location` — константа реестра.
- **Текст исключения.** `str(PhoneError)` — константа без ввода; тем не менее при непредвиденной ошибке трассировка уходит в журнал: на прототипе 500-я трассировка печатала пример `+7 *** ***-**-67` — защита маски (`log_masking`) замаскировала даже пример из константы; это признак того, что маска работает как последний рубеж, а не разрешение логировать.

## 9. Ожидаемо красные правила (идиома D-20 Фазы 17)

Допущение: `AccountRow` получает **обязательное** 4-е поле (рекомендация §5). `[ЗАМЕР: tree_c, tests/test_templates + test_services + test_application (без single-writer) + test_models + test_repositories + test_scripts → 35 failed, 1515 passed]`; все 35 — `TypeError: AccountRow.__new__() missing 1 required positional argument: 'phone_is_manual'`:

| Файл:строка | Конструкция | Красные узлы |
|---|---|---|
| `tests/test_services/test_account_label.py:77-78` | помощник `_rows` → `AccountRow(*item)` на трёхэлементных кортежах | через `_rows` падают: `test_twins_are_found_by_the_ready_label_inside_one_messenger` (:106, 8 параметров), `test_the_plain_form_carries_the_id_only_for_a_twin` (:113, 8), `test_a_twin_plain_label_reads_whatsapp_unknown_with_its_id` (:122, 1), `test_a_unique_plain_label_reads_channel_and_number` (:129, 1), `test_plain_with_id_always_carries_the_id` (:136, 1), `test_an_unfamiliar_type_keeps_its_own_word_as_the_channel` (:143, 1), `test_label_of_agrees_with_build_labels` (:151, 8) |
| `…test_account_label.py:89` | `AccountRow(1, "wa", blank)` | `test_a_blank_stored_number_reads_as_unknown` (2) |
| `…:98` | `AccountRow(1, "tg_user", stored)` | `test_an_unparseable_number_is_shown_as_it_is_not_as_unknown` (3) |
| `…:161, 163, 164` | `AccountRow(9, "wa", None)`, `AccountRow(1, "wa", None)`, `AccountRow(1, "tg_user", None)` | `test_label_of_does_not_need_the_subject_among_the_rows` (1) |
| `tests/test_application/test_account_label_rows.py:74, 76` | `by_id[mine[0]] == AccountRow(mine[0], "tg_user", "+79991234567")`, `AccountRow(mine[3], "max", "abc")` — равенство с трёхполым кортежем | `test_rows_cover_every_account_of_the_user_in_one_statement` (1) |

Итого **35 узлов в 2 файлах (10 функций + 1)**: правки — один помощник `_rows` + шесть прямых конструкций + два равенства; **объявляются планом флага заранее** (D-20). Красных вне этих двух файлов в `tests/test_templates/`, `test_services/`, `test_application/` (кроме single-writer — он зелен), `test_models/`, `test_repositories/`, `test_scripts/` **нет**.

**Каталог `tests/test_pages/` целиком (66 модулей) прогнан на дереве прототипа** `[ЗАМЕР: четыре прогона — 343 passed (4 модуля гейтов), 22 модуля подписи/шелла/адаптивности/истории/админки/расписаний — 1103 passed и 2 failed, остальные 37 модулей — 708 passed, плюс четыре модуля, снятых раньше]`. Красных от флага, ссылок на карточках, страницы 422 и добавленных `id` **нет ни одного** — единственные два красных в этой части каталога — счётчики маршрута (§7, строки 10 и 11), и они вызваны самим маршрутом, а не подписью. В том числе зелены: `test_shell.py` (`html.count("<h1") == 1` при новом `id` у `<h1>`), `test_responsive_markup.py` (в том числе сверка трёх файлов карточки с девятью новыми ссылками), `test_account_label_*` (шесть модулей), `test_admin_panel.py`, `test_history*.py`, `test_editor_schedules.py`, `test_impersonation.py`, `test_notices_*`. Остальные каталоги тестов (`test_routes`, `test_worker`, `test_messengers`, `test_infra`, `test_migrations`, 25 корневых `tests/test_*.py` без двух гейтов номера) на дереве прототипа: **819 passed, 3 failed**; те же три красных воспроизводятся на **нетронутом HEAD `5a75f567`** (`816 passed, 3 failed` тем же списком модулей в том же порядке) — это уже существующее загрязнение порядка суиты, а не следствие Фазы 18: `tests/test_admin.py::test_the_free_access_grant_is_journaled_with_both_identities` («выдача бесплатного доступа не оставила записи `free_access_toggled`») и `tests/test_logging_config.py::test_a_long_split_request_path_is_logged_in_bounded_time[1801-chars]`, `[7999-chars]` («событие `request` не дошло до журнала: []»); по отдельности те же тесты зелены (`21 passed` на `test_admin::…` + `test_logging_config.py`) `[ЗАМЕР]`. Прибавка 816 → 819 — три одноразовых пробных теста в копии прототипа. [ВЫВОД] В полном прогоне гейта оркестратора эти три узла не засчитывать за регрессию Фазы 18; причина здесь не исследовалась (по отдельности тесты проходят — зависимость от порядка прогона), и в объём фазы они не входят.

**Итог по числу красных от Фазы 18 на прототипе:** 35 ожидаемых (обязательное поле `AccountRow`, §9) + 0 неожиданных после правки чисел §7; до правки чисел §7 — 11 файлов гейтов красны немедленно после появления маршрута.

**Зелёное вакуумом — что обязано быть расширено, но не покраснеет (расширить в том же плане):**
- `tests/test_pages/test_responsive_markup.py:5147-5199` — `ONE_LINE_LABEL_CONTAINERS = (".chip__label", ".acct-head__name")` и цикл `for part in ("chan", "text")` (:5182) читают CSS-правила частей подписи; новая часть «указан вручную» в этот цикл **не входит**, и ни одно существующее утверждение не заметит, что пометка не усекается/ломает перенос на 320–375 px. CSS Фазы 17 (`app/static/css/app.css:2537-2547`): `.chip__label > .acct-label, .acct-head__name > .acct-label { display: inline-flex; …; max-width: 100%; min-width: 0 }`, `… .acct-label__chan, … .acct-label__text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }`, `.acct-label__id { flex: none; }`. [ВЫВОД] Часть-пометка должна усекаться **раньше `#id`** (`#id` не сжимается — различитель двойников); добавить селектор в оба списка и часть `"manual"` в цикл теста (RED: правила нет — тест краснеет «по существу»). Ширину 320–375 px текст CSS не доказывает — ручной обход (§Validation, Manual-Only).
- `tests/account_label_support.py::seed_account` (`phone=` — только автономер через `fill_reported_phone`): **ручной номер сеять нечем**. Нужен параметр (например `manual_phone=`), вызывающий `set_manual_phone` (санкционированный путь; конструктор и присваивание отказывают `PhoneWriteOutsideWriter`). Wave 0.
- `tests/test_pages/test_account_label_accounts.py:264` («четыре конструктора `SyncStatusView`») — парный тест на `phone_is_manual`.

## 10. Суита записей `tests/test_planning` и новые планы

**Исходное состояние** `[ЗАМЕР: клон вне репозитория, HEAD 5a75f567, uv run pytest tests/test_planning -q -p no:randomly]`: **`218 passed, 2 skipped`** за 22 с.

| Что внесли в клон | Результат [ЗАМЕР] |
|---|---|
| `18-01-PLAN.md` с `must_haves.prohibitions` из **строк** (`- "текст"`) | **9 failed, 22 errors** — перепись отказывает на форме: элемент обязан быть отображением `statement:` + `status:` (форма как у `17-01-PLAN.md:73-79`: `- statement: "MUST NOT …"` / `  status: flagged-unverified`) |
| тот же план с правильной формой, два запрета | **6 failed**: `test_the_census_and_the_registry_are_a_bijection`, `test_the_registry_declares_its_own_length`, `test_plans_after_the_fixed_set_only_add_rows_outside_the_decision_scope`, `test_control_negative_a_synthetic_prohibition_is_found_and_named`, `test_control_a_plan_after_the_fixed_set_is_named_by_the_bijection`, `test_reconcile_seed_of_the_registry_is_idempotent_by_identity` (все — `test_plan_prohibitions_census.py`) |
| затем `uv run python scripts/prohibitions_census.py --seed-registry` | `реестр записан: 955 строк → .planning/milestones/v2.1-phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` (было 953); повторный прогон — **218 passed, 2 skipped**; в diff реестра — только строки плана и `measured`/`rows_declared` (4 вставки, 2 удаления) |
| в `ROADMAP.md` у Фазы 18 пункт `- [ ] 18-01-PLAN.md — …`, `progress.total_plans` в `STATE.md` не тронут (73) | **1 failed**: `test_state_progress_matches_roadmap.py::test_the_machine_readable_progress_is_derived_from_the_roadmap` — «поле `progress.total_plans` … записано как 73, а из отметок `.planning/ROADMAP.md` выводится 74 — привести надо ПОЛЕ» |

**Что из этого следует плану:**
1. Блок `must_haves.prohibitions` у каждого плана Фазы 18 — **отображения `statement`/`status`**. Любая правка блока (добавили, убрали, переставили) меняет тождества «путь плана + индекс» ⇒ после каждой правки заново `--seed-registry`, затем `uv run pytest tests/test_planning -q -p no:randomly`. Шапка реестра (`REGISTRY_HEADER` в `scripts/prohibitions_census.py`) принадлежит скрипту: ручная правка краснит правило идемпотентности засева (память проекта «Шапка реестра запретов — за скриптом»).
2. Строки `**Plans**:` / `- [ ] 18-NN-PLAN.md` в разделе Фазы 18 `ROADMAP.md` (сегодня `**Plans**: TBD`, `ROADMAP.md:358`) и `progress.total_plans` (`STATE.md:16` — 73) **правятся одним коммитом**: total = 73 + N. Каждая отметка `- [x]` на исполнении требует правки `completed_plans` (`STATE.md:17` — 73) тем же коммитом; шаг `state.planned-phase` по памяти проекта стирает летопись `Phase/Status` и обнуляет `percent` (сейчас `percent: 40`, `STATE.md:18`) — проверять после него.
3. **Отметки требований.** `PHONE-08…PHONE-11` в `REQUIREMENTS.md:91-94` — `Pending`; `[x]`/`Complete` до отчёта верификации со статусом `passed` краснит `test_requirement_completion_follows_verification.py`. Планы отметок не ставят.
4. Если исполнитель заведёт `.planning/phases/18-…/deferred-items.md` с разделами «## План 18-NN» — нужен якорь `<!-- deferred-items:end -->` и один раздел на план (`test_deferred_items_are_idempotent.py`). Строка отложенного **«Phase 16 → Phase 18 / IN-01»** живёт в `STATE.md:774` (таблица `## Deferred Items`), а не в `deferred-items.md`: её диспозицию правит трекинг STATE; память проекта «Реестр диспозиций сбрасывает deferred» — снять копию строки до шага трекинга и сверить после.
5. `test_executed_plans_kept_their_scope.py` судит коммиты планов Фазы 10 и требует полной истории git; Фазы 18 не касается.
6. Нужна **процедурная последовательность** в коммите планирования (оркестратор): засев реестра → `total_plans` в STATE → `tests/test_planning` → коммит; повторять после каждого переплана. Исполнители по умолчанию каталог `tests/test_planning/` пропускают — гнать явно в конце волны.

## 11. Адресаты фазы 18 за пределами CONTEXT.md

| Место | Что это в дереве сегодня | Работа в планировании Фазы 18? |
|---|---|---|
| `STATE.md:774` — «Phase 16 → Phase 18 / IN-01» | `PHONE_ERROR_BLANK` через писателя недостижим, пустой ввод очищает `[ПРОЧИТАНО]`. Тесты, закрепляющие константу: `tests/test_services/test_phone.py:661` `pytest.param("", PHONE_ERROR_BLANK, id="empty")`, `:662` `pytest.param("   ", PHONE_ERROR_BLANK, id="spaces_only")`, `:1256` `PHONE_ERROR_BLANK,` `[ЗАМЕР: grep]`; в `app/` константу поднимает только `normalize_manual` (`services/phone.py:328`) | **ДА, закрыть диспозицией** «решено владельцем 2026-11-21: пустое поле = очистка (D-09 Фазы 18)» (текст из CONTEXT D-09); константу и её тесты **не трогать**; в докстринге обработчика записать, что пустой ввод — очистка |
| `STATE.md:663` — «Писатель номера не проверяет владельца аккаунта (T-16-19)» | подтверждено чтением `phone.py:61-63` и отсутствием параметра владельца у `set_manual_phone` | **ДА** — закрывается D-05: `_load_owned_account` перед писателем; тест на **чужой** аккаунт обязателен (RED: без проверки чужой аккаунт получил бы запись) |
| `STATE.md:661, :775` — границы защиты и маски (CR-09, WR-40, IN-29, WR-41, WR-42, `raw-dbapi-sql-from-a-parameter` T-16-145, `--loglevel` Celery IN-28) | не работа фазы; «называть в каждом плане, который пишет номер или печатает его в журнал» | **Называть в `<automated>`/`threat_model` плана маршрута** и держать новый код внутри защищаемых форм: (1) **ни одной** записи колонок `phone`/`phone_is_manual` вне `set_manual_phone` — ни `account.phone = …`, ни `update(MessengerAccount).values(phone=…)`, ни ORM-flush; (2) **никакого** сырого SQL (`text(...)`, `exec_driver_sql`) с этими колонками — он обходит все проверки (T-16-145); (3) никакого DML внутри CTE и `INSERT OR REPLACE` (CR-09, IN-29); (4) имена таблиц/колонок в нижнем регистре, как в модели (WR-40); (5) в журнал — только `account_id`, `phone_set`; в вызовы `print`/`logger` не подаются `phone`, `text`, `saved`, подпись; (6) на маску (WR-41/WR-42) не полагаться — она последний рубеж |
| `STATE.md:662` — удаление и повторная вставка аккаунта стирает ручной номер (advisory 4 раунда 12) | в `app/` три вставки `MessengerAccount(` — `app/pages/accounts.py:312, 681, 933` (подключение), все **без явного `id`** `[ЗАМЕР: grep MessengerAccount( app/]`; фаза 18 не добавляет ни удаления, ни вставки | **Нет** (адресат — ревью Фаз 17–20); план называет: «новых путей delete+reinsert фаза не заводит» |
| `STATE.md:76` — «Порядок исполнения: 16 → 17 → 18 → 19 → 20, строго последовательно — фазы 17, 18 и 19 сходятся в `app/pages/accounts.py`» `[ПРОЧИТАНО]` | Фаза 18 правит `accounts.py` в **одном** месте: конструктор `AccountRow` для фрагмента опроса (`:1051`, добавить `view.phone_is_manual`) | **ДА** (планирование): минимальная правка, без перестройки обработчика, чтобы Фазе 19 не разбирать чужие изменения; порядок 18 → 19 строгий |
| `ROADMAP.md` критерий 1 «номер виден **на всех экранах Фазы 17** с пометкой «указан вручную»» против D-10 «в плоских формах пометки нет» (`<title>`, `<option>`, `plain`, CSV, тело модалки удаления) | текст критерия шире решения владельца; D-10 принят владельцем явно | **Записать в `truths` плана** слово в слово: «пометка — везде, где подпись рисуется разметкой; плоские формы без пометки (D-10)» — чтобы верификатор не прочёл критерий буквально |
| CONTEXT D-05: «границу `ID_MAX` (тип пути `IdPath`)» | для POST — `PostIdPath` + `id_in_column` (§2) | **ДА, уточнить в плане** — иначе исполнитель поставит `IdPath` на POST, и правило `test_every_post_identifier_is_checked_before_its_first_use` / `POST-псевдоним на GET` покраснеет |
| `app/pages/htmx.py` докстринги `respond` / `_glue_notice` | утверждают «единственный вызов с фрагментом И кодом — `profile_post`» (`:707-711` в `_glue_notice`; «ПЯТОЕ ПОКОЛЕНИЕ» в `respond`) | **Опционально:** дописать «шестое поколение» (прежнее не стирать — идиома D-30/D-32); тесты прозу не принуждают (`test_prose_names_live_symbols` не затрагивается, если проза не вносится в его реестр) `[ОЦЕНКА]` |

## 12. TDD: цели RED (`workflow.tdd_mode: true`)

`[ПРОЧИТАНО: .planning/config.json — "tdd_mode": true]`. Память проекта: гейт TDD на `type: execute` инертен (`tddPlans: 0` — вакуум), на `type: tdd` меряет по-настоящему; RED-гейт, объявляющий отказ по `test $? -ne 0`, зеленеет там, где правило не исполнялось вовсе — RED-шаг обязан утверждать **конкретный** отказ (имя узла и класс ошибки), а не «ненулевой код»; запись RED-улики принимает pytest JUnit XML напрямую (`--junitxml=…`).

| Поведение | Цель RED (файл → идея имени теста) | Почему красно ДО правки | Тип плана |
|---|---|---|---|
| ручной флаг в правиле подписи | `tests/test_services/test_account_label.py` → `test_a_manual_number_carries_the_flag_and_the_text_stays_the_same` | у `AccountRow` нет поля (`TypeError`/`AttributeError`) | **tdd** |
| ключ двойника без флага (D-10) | там же → `test_a_manual_and_an_automatic_number_with_the_same_text_are_still_twins` | то же | tdd |
| плоские формы без пометки | там же → `test_plain_forms_never_carry_the_manual_mark` | то же | tdd |
| загрузчик строк отдаёт флаг | `tests/test_application/test_account_label_rows.py` → `test_rows_carry_the_manual_flag` | у строки три поля | tdd |
| четыре конструктора `SyncStatusView` | `tests/test_pages/test_account_label_accounts.py` (рядом с `:264`) → `test_sync_status_view_carries_the_manual_flag_in_all_four_constructors` | поля нет | tdd |
| макрос: «номер → пометка → `#id`», пометки нет у «Номер неизвестен» | `tests/test_pages/test_account_label_*.py` → разбор по `data-account-label` (`tests/account_label_support.py::label_texts`) | пометки в разметке нет | tdd |
| CSS-контракт 17-09 с пометкой | `tests/test_pages/test_responsive_markup.py` → расширить `for part in ("chan", "text")` частью пометки | правила в `app.css` нет | tdd |
| маршрут: годный ввод, PRG | `tests/test_pages/test_account_phone_form.py` → `test_a_valid_number_is_saved_and_the_redirect_carries_only_the_outcome_code` | маршрута нет (405) | **tdd** (атомарный план) |
| ответ htmx: фрагмент + `<title>` + два OOB + уведомление | там же → `test_the_htmx_answer_replaces_the_form_the_headings_and_the_notice` | то же | tdd |
| 422 без JS — страница с эхом; 422 с htmx — фрагмент | там же → `test_an_invalid_number_answers_422_with_the_echo_on_both_transports` | то же | tdd |
| пустое поле — очистка; `PHONE_ERROR_BLANK` не показывается | там же → `test_an_empty_field_clears_the_number_and_never_shows_the_blank_error` | то же | tdd |
| POST без поля не стирает номер | там же → `test_a_post_without_the_field_leaves_the_number_untouched` | (красно только при `Form("")`) | tdd |
| чужой = несуществующий = вне колонки; `LookupError` | там же → `test_a_foreign_a_missing_and_an_out_of_column_account_answer_alike` (статус, `Location`, тело побайтно) | то же | tdd |
| чужой источник → 403 до выборки | там же → `test_a_cross_origin_post_is_refused_before_any_lookup` | то же | tdd |
| приватность: номера нет в `Location`, уведомлении, журнале | там же → `test_the_number_reaches_neither_the_address_nor_the_notice_nor_the_log` | то же | tdd |
| свежая подпись после записи (D-14) | там же → `test_the_answer_shows_the_saved_number_not_the_stale_object` | при ленивой реализации — прежний номер | tdd |
| дубликат принимается (D-15) | там же → `test_the_same_number_on_two_accounts_makes_them_twins_without_a_refusal` | то же | tdd |
| сценарий критерия 3 | там же → `test_after_the_clearing_an_automatic_source_may_fill_the_number_again` (`KEPT` → очистка → `WRITTEN`) | маршрута нет | tdd |
| разрешение под имперсонацией (PHONE-11) | `tests/test_pages/test_impersonation.py` (рядом с `:1254`) → `test_the_phone_edit_is_allowed_under_another_identity` (запись видна в базе) | маршрута нет | tdd |
| коды реестра | `tests/test_pages/test_notices_registry.py` → `DECLARED_CODES` +2, `19 → 21` **первыми** | в реестре нет кодов (красно «пропавшие: [phone_cleared, phone_saved]») | tdd (пара «тест раньше кода») |
| ссылки на девяти местах карточек | новый `tests/test_pages/test_account_phone_links.py` → `test_every_account_card_links_to_the_phone_field_with_the_right_word` (страница, порция `/accounts/partial`, фрагмент опроса; три ветки статуса) | ссылок нет | tdd либо `execute` с тестом **в том же плане до правки** |
| числа и реестры гейтов §7 | сами гейты | красны **сразу** после появления маршрута/формы | **не отдельный RED**: правятся в том же плане и коммите, что и маршрут |

## 13. Форма работы

### Какие файлы касается каждое требование
| Требование | Python | Шаблоны / CSS | Тесты |
|---|---|---|---|
| PHONE-08 | `app/services/account_label.py`, `app/application/accounts/{labels,dto,use_cases}.py`, `app/pages/accounts.py` (одна строка `:1051`) | `components/account_label.html`, `app/static/css/app.css` (`:2537-2547`) | `test_account_label.py`, `test_account_label_rows.py`, `test_account_label_*.py`, `test_responsive_markup.py`, `tests/account_label_support.py` |
| PHONE-09 | `app/pages/account_groups.py`, `app/pages/notices.py` | `account_groups/includes/phone_form.html` (новый), `account_groups/partials/phone_response.html` (новый), `account_groups/list.html`, `base.html`; ссылки — три шаблона карточек | **новый** `test_account_phone_form.py`, 9 файлов гейтов (§7), `test_account_phone_links.py` |
| PHONE-10 | — (писатель готов) | — | `test_account_phone_form.py` (сценарий критерия 3) |
| PHONE-11 | — | — | `test_impersonation.py`, `test_impersonation_gate.py` |

### Общие файлы — порядок волн
- `app/pages/accounts.py` — Фаза 17 → **18** → 19 строго по очереди (`STATE.md:76`); Фаза 18 правит ровно одну строку (`:1051`).
- `app/static/css/app.css` — пометка (PHONE-08) и раскладка формы в шапке (UI-SPEC) — **один план** владеет файлом, иначе слияние параллельных worktree-веток.
- `tests/test_pages/test_responsive_markup.py` — расширение цикла частей (план флага) и сверка трёх файлов карточки (план ссылок): последовательно, не параллельно.
- Девять файлов гейтов правятся **одним** планом маршрута (§7) — разнос по планам оставляет промежуточное дерево красным.

### Рекомендуемая раскладка (вариант; решает планировщик)
1. **18-01, `tdd`, волна 1** — флаг ручного номера: правило подписи, загрузчик, `SyncStatusView` + четыре конструктора + `accounts.py:1051`, макрос, CSS-часть и её тест, посев ручного номера в `tests/account_label_support.py`; 35 ожидаемо красных переписаны в этом же плане (D-20).
2. **18-02, `tdd`, волна 2** (зависит от 18-01 по посеву и по показу пометки в ответе) — маршрут, страница 422, форма, ответ-фрагмент, два кода реестра, `_screen_context`, два `id`, **все** реестры и числа §7, тест разрешения под имперсонацией, критерий 3, приватность. Атомарен.
3. **18-03, `tdd` или `execute` с тестом-до-правки, волна 3** — девять ссылок на карточках, адресные тесты, сверка трёх синхронных копий.
4. Закрытие долгов (диспозиция IN-01 в `STATE.md`, названные границы в `threat_model`, записи `truths`) — внутри 18-02 и 18-03, отдельный план не нужен.

**Самый тонкий сквозной срез (tracer):** флаг в правиле → один шаблон → один адресный тест. Прототип этой цепочки прошёл за ~35 строк правки помощника + одну строку макроса и дал ожидаемые 35 красных в двух файлах.

## Architecture Patterns

### System Architecture Diagram

```
Браузер (форма в шапке аккаунта на /accounts/{id}/groups, якорь #phone)
   │  POST /accounts/{id}/phone   тело: phone=<свободный ввод>   (номер — только в теле, D-16)
   │  с JS: заголовок HX-Request, цель #acct-phone;  без JS: обычная форма, тот же action
   ▼
account_phone_save (app/pages/account_groups.py)
   ├─ нет сессии ──────────────────────────► respond(redirect="/login")
   ├─ is_same_origin? нет ──────────────────► Response(403)           ← собственный выход (реестр OWN_RESPONSE_EXITS)
   ├─ id_in_column(account_id)? нет ┐
   ├─ _load_owned_account → None ───┴──────► respond(redirect="/accounts")   (как «несуществующий», D-05)
   ▼
set_manual_phone(db, account_id, phone)    ← единственный писатель; без коммита
   ├─ PhoneError (до БД) ──► respond_field_error ──┬─ htmx: 422 + фрагмент формы с ошибкой и эхом
   │                                               └─ без JS: 422 + страница list.html целиком (контекст из _screen_context)
   ├─ LookupError (строку удалили) ───────► respond(redirect="/accounts")
   ▼
db.commit()  → logger.info("account_phone_saved", account_id=…, phone_set=…)
   ▼
respond(redirect=/accounts/{id}/groups#phone, notice=PHONE_SAVED|PHONE_CLEARED, fragment=_saved)
   ├─ без JS: 302 Location …?notice=<код>#phone  → GET страницы: плашка из реестра
   └─ htmx: 200  <title> + #acct-phone (форма с новым значением) + OOB(#acct-head-name) + OOB(#page-title) + OOB(#notice)
              ▲ подпись из load_account_rows (свежий SELECT), НЕ из ORM-объекта до записи (D-14)
```

### Recommended Project Structure
```
app/pages/account_groups.py                         # + _screen_context(), + account_phone_save()
app/pages/notices.py                                # + PHONE_SAVED, PHONE_CLEARED
app/templates/account_groups/includes/phone_form.html     # НОВЫЙ: единственный источник формы (страница + фрагмент)
app/templates/account_groups/partials/phone_response.html # НОВЫЙ: <title> + форма + 2 OOB
app/templates/account_groups/list.html              # + id у <h2>, include формы в [data-acct-head]
app/templates/base.html                             # + id у <h1 class="head-title">
app/templates/components/account_label.html         # + пометка «указан вручную»
app/services/account_label.py                       # + phone_is_manual в AccountRow / AccountLabel / row_of / label_of / build_labels
app/application/accounts/{labels,dto,use_cases}.py  # + колонка / поле
app/templates/accounts/{list,partial_cards}.html, accounts/partials/sync_status_card.html  # + 9 ссылок
app/static/css/app.css                              # + часть .acct-label__manual в двух списках селекторов
tests/                                              # 9 реестров гейтов + новые модули (§13)
```

### Pattern 1: «обработчик подаёт сборщики, слой выбирает форму» (образец `profile_post`)
**What:** успех — `respond(request, redirect=…, notice=…, fragment=_saved)`; ошибка поля — `respond_field_error(request, page=_page, fragment=_fragment)`. **When to use:** любой обработчик формы v2.1. `[ПРОЧИТАНО: app/pages/profile.py:141-193]`

### Pattern 2: «включаемый шаблон — единственный источник формы» (образец `includes/profile_settings.html`)
Страница и оба ответа (успех, ошибка) включают один файл; контекст — `phone_value`, `phone_error`, `account_id`, `example_phone`, `phone_maxlength` — кладёт **вызывающий**, шаблон умолчаний не ставит (`profile_settings.html:23-27`).

### Pattern 3: вспомогательные функции экрана — в том же модуле
Гейт пути деградации считает достижимость по цепочке функций внутри модуля (`account_groups.py:177-181`): `_screen_context`, сборщики формы — рядом с обработчиком.

### Anti-Patterns to Avoid
- **`db.rollback()` на ветке `PhoneError`/`LookupError`**: писатель падает до записи (нечего откатывать), а откат истекает `user`/`account` — следующий `user.id` в `_form_context` падает `MissingGreenlet` (500) `[ЗАМЕР: INVALID htmx → 500]`. Брать `user_id = user.id` заранее, откат не звать.
- **`{% with phone_value = …, phone_error = none %}{% include … %}` в `list.html`**: затирает контекст обработчика; страница 422 теряет эхо и текст ошибки `[ЗАМЕР: до правки `value="abc"` на странице: False]`. Значения по умолчанию кладёт `_screen_context`.
- **Вторая копия разметки формы в фрагменте** — ровно то, что включаемый шаблон исключает.
- **Подпись из ORM-объекта после записи** (`row_of(account)` без `refresh`) — прежний номер (§1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Разбор и приведение номера | свой regex / `re.sub` цифр | `set_manual_phone` → `normalize_manual` | разбор `phonenumbers`, пределы, расширения, «88…» — всё покрыто 700+ тестами Фазы 16 |
| Форма ответа на оба транспорта | свой `RedirectResponse` / ветвление по `HX-Request` | `respond()`, `respond_field_error()` | G-2 краснит собственный редирект у переведённого обработчика |
| Тело ошибки поля | `HTMLResponse(f"…{phone}…")` | включаемый шаблон + `field(error=…)` | автоэкранирование; ни фильтра отключения экранирования, ни `Markup(` (`test_no_unsafe_escaping`) |
| Уведомление | текст в обработчике или в URL | константа `notices.PHONE_*` + запись реестра | код едет в адресе, текст — из закрытого реестра |
| Метка «указан вручную» | собственная сборка разметки в Python / в каждом шаблоне | макрос `account_label` + поле флага | `MARKUP_BUILDERS = 0`; правило подписи — один источник |
| Проверка владельца | запрос с `user_id` внутри писателя | `_load_owned_account` | писатель владельца не проверяет по решению Фазы 16 |
| Источник запроса | свои заголовки | `is_same_origin(request)` + форма отказа `Response(status_code=403)` | форма отказа одна на проект |

**Key insight:** вся техника фазы уже написана; **каждое отступление** от готового кирпича — это новая строка в реестре гейта, а не экономия.

## Runtime State Inventory

Фаза — не переименование и не миграция (новых колонок и ревизий нет: колонки `phone`, `phone_is_manual` и CHECK заведены ревизией `0023`, Фаза 16). Раздел опущен по правилу шаблона. Единственное, что «живёт вне git» и касается фазы: ручные номера пользователей в боевой базе появятся только после выката v2.2 (деплой-гейт владельца D-26, Out of Scope вехи).

## Common Pitfalls

### Pitfall 1: откат сессии на ветке отказа валидации
**What goes wrong:** 500 вместо 422 на пути htmx (`MissingGreenlet`). **Why:** `rollback()` истекает объекты; `user.id` в сборщике — ленивая загрузка в async. **How to avoid:** не откатывать (писатель не писал), `user_id = user.id` до первых `await`. **Warning signs:** в журнале `unhandled_exception_in_middleware` с `MissingGreenlet`; тест 422 на htmx получает `{"detail":"Internal server error"}`. `[ЗАМЕР]`

### Pitfall 2: контекст формы затёрт в `list.html`
**What goes wrong:** страница 422 без эха и без текста ошибки (критерий 2 нарушен только на пути без JS). **How to avoid:** `phone_value`/`phone_error` — ключи контекста, `_screen_context` ставит умолчания (`acct_label.phone_text or ""`, `None`), `_page` перекрывает; в шаблоне — голый `include`. Тест: POST `phone=abc` без htmx ⇒ 422, `value="abc"`, «Не похоже на номер». `[ЗАМЕР]`

### Pitfall 3: «поля нет» стирает номер
**What goes wrong:** `phone: str = Form("")` (как у `profile_post`) отвечает `302 …?notice=phone_cleared` на POST без поля `phone` `[ЗАМЕР: probe3 «no field»]`. Браузерная форма всегда шлёт поле (пустое поле — `phone=`), так что достижимо только не-браузером — но это молчаливое удаление данных. **How to avoid:** обязательное `phone: str = Form(...)` — пустая строка очищает (D-09), отсутствие поля — отказ разбора фреймворка (на пути письма его закрывает `malformed_request_response`, `htmx.py:482`, пустым 400 `[ПРОЧИТАНО: includes/htmx_config.html — «отказ валидации отвечает пустым 400»]`; форма этого отказа для данного маршрута **не прогонялась** — проверит тест из §12). RED-тест: POST без поля оставляет номер как был. [ОЦЕНКА: решение планировщика; `profile_post` выбрал умолчание, чтобы браузерный путь не получал пустой 400, а у браузера поле присутствует всегда.]

### Pitfall 4: числа гейтов правятся «потом»
**What goes wrong:** маршрут добавлен — 9 модулей красные немедленно (§7). **How to avoid:** маршрут + шаблоны + реестры + числа — один план и один коммит; в `<automated>` плана — поимённо все модули §7 и команда `uv run pytest <9 модулей> -q -p no:randomly`.

### Pitfall 5: каскад утверждений прячет второе красное
**What goes wrong:** тест с `assert A; assert B` показывает только A. **How to avoid:** ставить числа итеративно, прогоняя после каждой правки; `MUTATING_MODULE_COUNT` в этом смысле проверен (стоит после `MUTATING_ROUTE_COUNT`).

### Pitfall 6: утверждение `status_code == 302` на не-литеральном адресе
Число `PAIRED_302_ASSERTIONS_DECLARED` растёт на каждое утверждение; адрес из выражения не разбирается и даёт запись «без обработчика». Для PRG-проверки использовать f-строку с идентификатором (`f"/accounts/{account_id}/phone"`) и вносить число прогоном; пары `POST_PAIR_CASES` — отдельный реестр (случай пары: успех `FRAGMENT` с `landing="/accounts/{account_id}/groups?notice=phone_saved#phone"` и `fragment_mark='id="acct-phone"'`; «аккаунта нет» `LOCATION` `landing="/accounts"`).

### Pitfall 7: порядок кортежа вызывающих
`MACRO_DEFINITION_SITES_CALLERS` сверяется кортежем в отсортированном порядке: `account_groups/includes/phone_form.html` **перед** `account_groups/list.html` `[ЗАМЕР: неверный порядок — красное]`.

### Pitfall 8: пометка вне CSS-контракта 17-09
Часть `.acct-label__manual` без правил усечения в двух списках селекторов (`app/static/css/app.css:2537-2547`) вытолкнет `#id` двойника на узком экране; существующие тесты этого не заметят (§9). Пометка стоит **до** `#id`, усекается она, `#id` — нет.

### Pitfall 9: «Сохранить» без правки превращает автономер в ручной
Поле предзаполнено текущим номером (D-11); нажатие «Сохранить» без правки пишет `phone_is_manual = true` поверх автономера, и пометка «указан вручную» появляется там, где человек ничего не вводил. Поведение — следствие D-11; **закрепить тестом осознанно** (не оставлять случайным). См. Open Question 1.

### Pitfall 10: `<title>` не прямым потомком
Вложенный в обёртку `<title>` вкладку не сменит и уедет в разметку элементом (`step_response.html:3-8`). Только верхний узел ответа; приклейка уведомления дописывает блок в КОНЕЦ и первый узел не трогает `[ЗАМЕР]`.

## Code Examples

### Скелет обработчика (проверен прототипом; имена — на усмотрение)
```python
# Source: прототип в копии дерева; образцы — account_groups_delete (порядок проверок), profile_post (respond/respond_field_error)
@router.post("/accounts/{account_id}/phone")
async def account_phone_save(
    request: Request,
    account_id: PostIdPath,
    phone: str = Form(...),               # пустая строка = очистка (D-09); «поля нет» — отказ разбора
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")
    if not is_same_origin(request):
        return Response(status_code=403)
    account = await _load_owned_account(db, user, account_id) if id_in_column(account_id) else None
    if account is None:
        return await respond(request, redirect="/accounts")
    user_id = user.id                      # ДО любых await, которые могут истечь объект
    try:
        saved = await set_manual_phone(db, account_id, phone)
    except PhoneError as refusal:          # без rollback: писатель не писал
        ...                                # respond_field_error(page=_page, fragment=_error_fragment)
    except LookupError:
        return await respond(request, redirect="/accounts")
    await db.commit()
    logger.info("account_phone_saved", account_id=account_id, phone_set=saved is not None)
    ...                                    # respond(redirect=f"/accounts/{account_id}/groups#phone", notice=…, fragment=_saved)
```

### Ответ-фрагмент (напечатан прототипом)
```html
<title>Telegram +7 999 123-45-67 — группы аккаунта — Broadcaster</title>
<div id="acct-phone" data-acct-phone> …форма… </div>
<span hx-swap-oob="innerHTML:#acct-head-name"><span class="acct-label" data-account-label="1">…</span></span>
<span hx-swap-oob="innerHTML:#page-title"><span class="acct-label" data-account-label="1">…</span></span>
<div hx-swap-oob="innerHTML:#notice"><div class="alert alert--success" role="status">Номер сохранён</div></div>   <!-- приклеивает _glue_notice -->
```

### Макрос подписи с пометкой (напечатан прототипом)
```jinja
{%- if label.phone_is_manual %} <span class="acct-label__manual muted">указан вручную</span>{% endif -%}
{%- if with_twin_id and label.twin %} {{ account_id_mark(label.account_id) }}{% endif -%}
```
Результат: `…+7 999 123-45-67</span> <span class="acct-label__manual muted">указан вручную</span> <span class="acct-label__id mono mono--muted" data-account-id="1">#1</span>`; `plain` — без пометки.

### Сценарий критерия 3 (готов к переносу в тест)
```python
await set_manual_phone(db_session, aid, "8 999 123 45 67"); await db_session.commit()
assert await fill_reported_phone(db_session, aid, "+79995556677") is PhoneWrite.KEPT
assert await set_manual_phone(db_session, aid, "   ") is None; await db_session.commit()
assert await fill_reported_phone(db_session, aid, "+79995556677") is PhoneWrite.WRITTEN
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `profile_post`: `Form("")`, успех без номера | тот же слой + поле с эхом и фрагментом с кодом исхода | Фаза 11 (11-09) | образец для маршрута; единственный прежний потребитель «фрагмент + код исхода» |
| подпись `#id` в ~17 местах | один помощник + макрос (`account_label`) | Фаза 17 | флаг ручного номера — правка одного помощника (D-10) |
| номер не хранился | `phone` + `phone_is_manual`, единственный писатель, `phone_guard` | Фаза 16 | страница — первый вызывающий `set_manual_phone` |

**Deprecated/outdated:** ничего не снимается.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `autocomplete="off"` удержит браузер от подстановки собственного номера пользователя (поведение браузеров неоднородно) | §3 | вместо номера аккаунта в поле окажется номер пользователя; проверяется ручным обходом |
| A2 | htmx 2.0.10 применяет `<title>` верхнего уровня частичного ответа и `hx-swap-oob="innerHTML:#id"` на `<span>`-обёртке | §4 | заголовок вкладки/шапка не сменятся без перезагрузки; проект утверждает это для `<title>` (`step_response.html`), для `<span>`-обёртки OOB — прецедент `<div>`/`<span>` в `user_actions_response.html:48` (`<span hx-swap-oob="innerHTML:#user-block-badge">`); исполнение JS суитой не проверяется |
| A3 | Идентификатор поля `phone` не пересекается на странице экрана групп с другим `id="phone"` (поле MAX-мастера живёт на другой странице; на экране групп `id` поля поиска — `filter-search`) | §3 | два `id` на странице ломают цель якоря `#phone`; три имени `acct-phone`, `acct-head-name`, `page-title` свободны `[ЗАМЕР: grep -rn по app/templates, app/static/css, app/static/js — вхождений нет]` |
| A4 | Исполнители выберут обязательное, а не умолчаемое поле `phone_is_manual` у `AccountRow` | §5, §9 | при умолчании красных 35 не будет, но путь без флага перестанет быть громким |
| A5 | Полный `tests/test_pages/` прогнан не целиком (только перечисленные модули — полная суита ~46 мин по памяти проекта); не прогнанные модули не читают изменяемых прототипом мест | §9 | тест вне перечня может краснеть на изменённой разметке карточек/подписи; закрывается полным прогоном в гейте оркестратора |

## Open Questions (RESOLVED)

> Закрыты владельцем 2026-11-21, прогон `/gsd-plan-phase 18` (п. 1 и п. 3); п. 2 и п. 4 закрыты
> рекомендацией как решения планировщика.

1. **«Сохранить» без правки делает автоматический номер «указан вручную».** — **RESOLVED (владелец,
   2026-11-21, прогон `/gsd-plan-phase 18`): принять как есть.** Нажатие «Сохранить» — осознанное
   подтверждение; номер, сохранённый без правки, становится ручным `(phone, True)`; закрепляется тестом.
   Вариант «без изменения значения ничего не писать (сравнение в обработчике)» — ОТВЕРГНУТО ВЛАДЕЛЬЦЕМ.
   - Что известно: поле предзаполнено (D-11), писатель всегда ставит `phone_is_manual = true`; повторное сохранение того же значения — запись ручного.
   - Что неясно: хочет ли владелец, чтобы нажатие «Сохранить» без изменения значения считалось подтверждением (ручной) — или не писало бы ничего.
   - Рекомендация: **принять как есть** (нажатие — осознанное подтверждение, номер остаётся подписью), закрепить тестом «автономер, сохранён без правки ⇒ `(phone, True)`»; если владелец не согласен — отдельное решение (сравнение с сохранённым значением в обработчике, а не в писателе).
2. **Поле `phone`: `Form(...)` или `Form("")`?** — **RESOLVED (решение планировщика, делегировано):** рекомендация — `Form(...)` (§Pitfall 3); решения владельца не требует.
3. **UI-SPEC.** — **RESOLVED (владелец, 2026-11-21, прогон `/gsd-plan-phase 18`): планировать без
   UI-SPEC**, как Фаза 17; раскладку формы в шапке, перенос на 320–375 px и вид пометки планировщик
   берёт из ограничений ниже и D-11, проверка — ручным обходом на приёмке. Вариант «сначала
   `/gsd-ui-phase 18`» — ОТВЕРГНУТО ВЛАДЕЛЬЦЕМ. `.planning/config.json` — `workflow.ui_phase: true`, роадмап — `UI hint: yes`. Исследование не определяет раскладку формы внутри `[data-acct-head]` (flex-wrap, `app/static/css/app.css:2775-2814`), перенос на 320–375 px и вид приглушённой пометки — это предмет UI-SPEC (`/gsd-ui-phase 18`), если оркестратор его запускает до планирования. Исследование даёт только ограничения: форма стоит в шапке, видна всегда (D-11); пометка стоит до `#id`, усекается до него.
4. **Журнал правки под имперсонацией (D-16).** — **RESOLVED (рекомендацией).** «Запись в журнал — на усмотрение планировщика, но только в этой форме»: рекомендация — одна строка `account_phone_saved` с `account_id`, `phone_set` на **все** сохранения; поле «кто правил» (id администратора) в форму D-16 не входит — добавлять его значило бы расширить решение владельца. Закрыто рекомендацией.

Открытых вопросов: **0** (до 2026-11-21: «Вопросов, требующих владельца до планирования, **один** (п. 1); п. 2–4 — решения планировщика/оркестратора с рекомендациями»).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | запуск суиты | да | 0.12.1 | — |
| Python (venv проекта) | суита | да | 3.12.13 | — |
| `just` | рецепты | да | 1.45.0 | `uv run pytest …` напрямую |
| SQLite in-memory | суита (aiosqlite) | да (встроена) | — | — |
| PostgreSQL / Redis / Docker / Node | **не нужны** | — | — | фаза не трогает воркеры, миграции, образы |

Блокирующих отсутствующих зависимостей нет.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (`@pytest.mark.asyncio`), httpx `AsyncClient` |
| Config file | `tests/conftest.py` (фикстуры `client`, `db_session`, `authed_client`, `admin_client`); отдельного `pytest.ini` нет |
| Quick run command | `uv run pytest tests/test_pages/test_account_phone_form.py tests/test_services/test_account_label.py -q -p no:randomly` (файл формы создаётся планом; до него — `-k phone`) |
| Full suite command | `uv run pytest tests/ -q -p no:randomly` (~46 мин; для гейта — таймаут 5400 с, память проекта) |
| Planning records | `uv run pytest tests/test_planning -q -p no:randomly` (22 с; `218 passed, 2 skipped` на HEAD) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PHONE-08 | подпись с флагом: порядок «номер → пометка → `#id`»; плоские формы без пометки; ключ двойника без флага | unit | `uv run pytest tests/test_services/test_account_label.py -q -p no:randomly` | ✅ (дополнить; 35 красных узлов объявить заранее) |
| PHONE-08 | загрузчик отдаёт `phone_is_manual`; все четыре конструктора `SyncStatusView` | unit/интеграция | `uv run pytest tests/test_application/test_account_label_rows.py tests/test_pages/test_account_label_accounts.py -q -p no:randomly` | ✅ дополнить |
| PHONE-08 | пометка на карточках, шапке, чипах, истории, админке — по адресу `data-account-label` | integration | `uv run pytest tests/test_pages/test_account_label_accounts.py tests/test_pages/test_account_label_groups.py tests/test_pages/test_account_label_history.py tests/test_pages/test_account_label_admin.py tests/test_pages/test_account_label_admin_history.py tests/test_pages/test_account_label_sweep.py -q -p no:randomly` | ✅ дополнить (посев ручного номера — Wave 0) |
| PHONE-08 | CSS-контракт: пометка усекается до `#id` | unit (текст CSS) | `uv run pytest tests/test_pages/test_responsive_markup.py -q -p no:randomly -k label` | ✅ расширить цикл частей |
| PHONE-09 | годный ввод: 302 PRG (адрес и код без номера), htmx 200 + `<title>` + форма + 2 OOB + уведомление; `8 …`, `+7 (…)`, форма показа | integration | `uv run pytest tests/test_pages/test_account_phone_form.py -q -p no:randomly` | ❌ Wave 0 (новый) |
| PHONE-09 | 422: страница целиком без JS, фрагмент с htmx, эхо, текст из `PHONE_ERROR_MESSAGES`, `PHONE_ERROR_BLANK` не показывается, плашка аварии не поднимается (CSS-/конфиг-утверждения) | integration | там же | ❌ Wave 0 |
| PHONE-09 | владение: чужой = несуществующий = вне колонки (статус, `Location`, тело побайтно); `LookupError`; чужой источник → 403; POST без поля не стирает | integration | там же | ❌ Wave 0 |
| PHONE-09 | приватность: номера нет в `Location`, теле уведомления, журнале (`caplog`/структлог) | integration + гейты | `uv run pytest tests/test_pages/test_account_phone_form.py tests/test_phone_privacy_gate.py -q -p no:randomly` | ❌/✅ |
| PHONE-10 | очистка → «Номер неизвестен», пометки нет; `fill_reported_phone` → `WRITTEN` | integration | `uv run pytest tests/test_pages/test_account_phone_form.py -q -p no:randomly -k clear` | ❌ Wave 0 |
| PHONE-11 | под имперсонацией правка проходит и **пишет** (чтение `phone`, `phone_is_manual`); чужой аккаунт — как несуществующий | integration | `uv run pytest tests/test_pages/test_impersonation.py -q -p no:randomly -k phone` | ✅ файл / ❌ тест |
| PHONE-11 | гейт имперсонации: ключ в `ALLOWED_ROUTES` с причиной; число 50/14 | gate | `uv run pytest tests/test_pages/test_impersonation_gate.py -q -p no:randomly` | ✅ править числа |
| все | сквозные гейты | gate | см. «Sampling Rate» (полная команда ниже) | ✅ править числа и реестры §7 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_pages/test_account_phone_form.py tests/test_services/test_account_label.py -q -p no:randomly` (≈ секунды).
- **Per wave merge (гейты, поимённо в `<automated>` каждого плана):** `uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_account_groups.py tests/test_pages/test_notices_registry.py tests/test_pages/test_write_path_invariants.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_hx_location_destinations.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py tests/test_application/test_phone_writer_runtime_guard.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_shell.py -q -p no:randomly` — замеры времени: `test_htmx_post_pairs` ≈ 70 с, `test_account_groups` ≈ 150 с, `test_htmx_gates` ≈ 32 с, `test_identifier_bounds` ≈ 30 с, `test_phone_single_writer_gate` ≈ 46 с, `tests/test_templates` целиком ≈ 25 с.
- **Records:** `uv run pytest tests/test_planning -q -p no:randomly` после засева реестра и правки `total_plans`.
- **Phase gate:** полная суита зелёная (`uv run pytest tests/ -q -p no:randomly`, таймаут 5400 с) до `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `tests/test_pages/test_account_phone_form.py` — новый: маршрут, оба транспорта, 422, владение, граница, приватность, критерий 3 (PHONE-09, PHONE-10).
- [ ] `tests/account_label_support.py::seed_account` — параметр посева ручного номера через `set_manual_phone` (PHONE-08).
- [ ] тест разрешения под имперсонацией в `tests/test_pages/test_impersonation.py` рядом с `:1254` (PHONE-11).
- [ ] расширение цикла частей и селекторов CSS в `tests/test_pages/test_responsive_markup.py:5182` (PHONE-08).
- [ ] Новых зависимостей и каркаса нет — `pytest`, `httpx`, фикстуры существуют.

**Manual-Only (в суите не проверяется — ручной обход, `/gsd-verify-work 18`):** сам htmx-обмен (подмена `#acct-phone`, внеполосные `<h2>`/`<h1>`, смена `<title>`, плашка «Номер сохранён» без перезагрузки), якорь `#phone` прокручивает к полю с карточки, `autocomplete="off"` не подставляет номер пользователя, раскладка шапки и пометки на 320 и 375 px, `#id` двойника остаётся видимым рядом с пометкой, 422 без плашки аварии в консоли. Суита не исполняет JS и не рендерит в браузере. Записи обхода — по правилам самозаверения (`test_the_walkthrough_cannot_self_certify.py`): машинную улику писать разделом улики, отметки и `result` оставлять человеку.

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: high` `[ПРОЧИТАНО: .planning/config.json]`.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | вход не меняется |
| V3 Session Management | косвенно | `get_user_from_cookie`; имперсонация — токен с действующим лицом, маршрут её **разрешает** (D-06) |
| V4 Access Control | **yes** | `_load_owned_account` на каждом входе; чужой = несуществующий (неотличимость); `is_same_origin` (V4.2.2); `PostIdPath` + `id_in_column` |
| V5 Input Validation | **yes** | `normalize_manual` (пределы 32 символа/15 цифр, расширения); ввод в текст ошибки не подставляется; автоэкранирование Jinja при эхо в `value=` |
| V6 Cryptography | no | номер не шифруется и не хэшируется (подпись, D-решения Фазы 16) |
| V7 Logging / PHONE-21 | **yes** | в журнал — только `account_id`, `phone_set`; гейт приватности |

### Known Threat Patterns for FastAPI + Jinja2 + htmx
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR: правка номера чужого аккаунта (T-16-19) | Tampering / Information Disclosure | `_load_owned_account` до писателя; тест на чужой аккаунт; ответ неотличим от несуществующего |
| CSRF по cookie-сессии | Tampering | `is_same_origin`, форма отказа `Response(status_code=403)` |
| XSS через эхо введённого значения в `value="…"` | Tampering | автоэкранирование `field`; ни `\|safe`, ни `Markup(`; тест с враждебным значением (`'"><script>alert(1)</script>'` — образец `test_account_label_groups.py::HOSTILE`) |
| Утечка номера в URL / уведомление / журнал / трассировку | Information Disclosure | номер только в теле POST; код реестра; `logger` с `account_id`/`phone_set`; маска `log_masking` — последний рубеж |
| Стирание данных по пропущенному полю | Tampering | `Form(...)` (§Pitfall 3) |
| Переполнение идентификатора пути (500 на PostgreSQL) | DoS | `PostIdPath` + `id_in_column` первым использованием |
| Запись под чужой личностью | Repudiation | разрешено решением D-06 (номер — подпись); журнал `account_phone_saved` без поля актора — граница D-16 |

Принятые границы Фазы 16 (CR-09, WR-40, IN-29, WR-41, WR-42, T-16-145, IN-28) — **не работа Фазы 18**; план называет их и держит код в защищаемых формах (§11).

## Sources

### Primary (HIGH confidence) — исходники дерева, открытые в сессии
- `app/application/accounts/phone.py` (писатель), `app/services/phone.py` (нормализатор, константы), `app/services/account_label.py`, `app/application/accounts/{labels,dto,use_cases}.py`
- `app/pages/account_groups.py`, `app/pages/profile.py`, `app/pages/htmx.py` (`respond`, `respond_field_error`, `_glue_notice`, `_with_notice`), `app/pages/notices.py`, `app/pages/identifiers.py`, `app/pages/common.py` (`is_same_origin`)
- `app/templates/account_groups/list.html`, `account_groups/partials/*`, `includes/profile_settings.html`, `includes/notice_oob.html`, `includes/htmx_config.html`, `includes/htmx_error_banner.html`, `components/{form_wrapper,field,account_label}.html`, `auth/includes/step_response.html`, `base.html`, `accounts/{list,partial_cards}.html`, `accounts/partials/sync_status_card.html`
- Гейты: `tests/test_pages/{test_impersonation_gate,test_htmx_gates,test_htmx_post_pairs,test_identifier_bounds,test_account_groups,test_notices_registry,test_origin_guard_on_destructive_routes,test_write_path_invariants,test_responsive_markup,test_impersonation,test_account_label_groups}.py`, `tests/test_templates/{test_form_inventory,test_htmx_markup_gates}.py`, `tests/test_phone_*`, `tests/test_application/test_phone_*`, `tests/test_planning/*`, `scripts/prohibitions_census.py`
- `.planning/{REQUIREMENTS,ROADMAP,STATE,config}.md/json`, `.planning/phases/17-…/17-RESEARCH.md` (форма документа)

### Secondary (MEDIUM)
- Прогоны прототипа в копиях вне репозитория (описаны в «Метод и границы замера»).

### Tertiary (LOW)
- Поведение браузеров (`autocomplete`, прокрутка к якорю) — `[ASSUMED]`, A1.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — новых пакетов нет, версии сняты.
- Числа гейтов: HIGH для раскладки прототипа (выставлены прогоном покрасневшего правила, 343 + 15 + 24 + 125 + 15 + 13 + 12 passed); MEDIUM для иной раскладки (формулы).
- Architecture: HIGH для сервера (ответы сняты), MEDIUM для htmx-подмены (JS не исполняется).
- Pitfalls: HIGH — три из десяти воспроизведены прототипом.

**Research date:** 2026-11-21
**Valid until:** до первого коммита, меняющего `tests/test_pages/test_htmx_*`, `test_impersonation_gate.py`, `test_form_inventory.py`, `test_htmx_markup_gates.py` или `app/pages/account_groups.py` (числа гейтов привязаны к HEAD `5a75f567`); иначе 30 дней.
