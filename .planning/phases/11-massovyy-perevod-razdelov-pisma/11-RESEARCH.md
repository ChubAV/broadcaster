# Phase 11: Массовый перевод разделов письма - Research

**Researched:** 2026-09-14
**Domain:** перевод 12 POST-обработчиков `app/pages/` на слой ответа `respond()` (htmx 2.0.10, FastAPI, Jinja2), третий выход `HX-Redirect`, 422 с перерисовкой формы, параметризованный обход пар 302
**Confidence:** HIGH по коду и рантайму htmx (всё снято с дерева и вендоренного файла этой сессией); MEDIUM по множеству хостов ЮKassa (документация прямо называет «страницу ЮKassa или её партнёра»)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Скопировано дословно из `11-CONTEXT.md` §`<decisions>`.

### Счёт критерия 1 и форма ответа по обработчику

- **D-01 (по умолчанию):** Числа критерия 1 «15 класса A / 5 класса B» — **прогноз разведки от
  2026-08-26 на ВСЮ веху**, а не счёт этой фазы; прочтение записывается по форме D-17 Фазы 10.
  Фазы 9 и 10 уже потребили **все 5 класса B** и **4 класса A**: переключение и удаление группы
  (фрагменты, Фаза 9), перезапуск воркера и снятие задачи из очереди (`HX-Location` решениями
  D-06/D-09 Фазы 10 — **заново не открываются**). Предмет Фазы 11 — **ровно 12 обработчиков**,
  оставшихся в `NOT_YET_CONVERTED` и принадлежащих её разделам; `NOT_YET_CONVERTED_COUNT`
  движется **26 → 14** (остаются 4 обработчика QR-мастера — Фаза 13 — и 10 авторизационных —
  Фаза 14). Летопись «прогноз пережит Фазами 9–10» пишется в `ROADMAP.md` у критерия 1 и в
  `REQUIREMENTS.md` у FORM-03/FORM-04 коммитом фазы — той же формулировкой, что «16 → 18»:
  прогноз не был ошибкой, он устарел.
  Переоткрытие перезапуска и снятия задачи ради буквального «15 фрагментов» отвергнуто: оба
  решения записаны Фазой 10 с измеренным основанием (ключ панели очереди — ПОЗИЦИЯ строки, и
  перевод его на `task_id` запрещён WR-04).
  — **Reversibility:** reversible.

- **D-02 (по умолчанию):** Форма ответа выбирается **по классу действия, измеренному на
  СЕГОДНЯШНЕМ поведении** (D-01 Фазы 10): действие оставляет экран → фрагмент + OOB; уводит с
  экрана или заменяет содержимое целиком → `respond()` без `fragment` (204 + `HX-Location`).

  | Обработчик | Сегодня | htmx-путь Фазы 11 |
  |---|---|---|
  | `schedules.py::schedules_create` (`:901`) | 302 в редактор `#sched-N` раскрытой | фрагмент: новая карточка + счётчик OOB; «было ноль» → `HX-Location` (D-05) |
  | `schedules.py::schedules_update` (`:995`) | 302 в редактор, раскрытие по форме | фрагмент `#sched-N` (`outerHTML`), раскрытие из `keep_sched` / `_expanded_from_form` |
  | `schedules.py::schedules_toggle` (`:1078`) | 302 на экран-источник | фрагмент строки ТОГО экрана, откуда пришла форма: `#schedule-row-N` (сводный список) или `#sched-N` (редактор); экран узнаётся скрытым полем (идиома D-02 Фазы 10) |
  | `ads.py::ads_create` (`:584`), `ads_update` (`:720`) | уже фрагмент через `_save_from_editor` | переезд на `respond()` БЕЗ изменения поведения; `HX-Push-Url` при создании сохраняется (D-13) |
  | `admin.py::admin_toggle_free_access` (`:1597`), `admin_toggle_block` (`:1812`) | 302 на `/admin/users/{id}` | фрагмент карточки «Действия» (`[data-actions]` получает постоянный `id`) + OOB для прочих мест страницы, печатающих то же состояние; «пользователя нет» / «подписки нет» → `HX-Location` |
  | `accounts.py::accounts_retry_sync` (`:714`) | 302 на `/accounts/{id}/groups` — УВОДИТ | `HX-Location` туда же. ⚠️ Разведка относила к классу A; сегодняшнее поведение — навигация |
  | `accounts.py::accounts_sync_groups` (`:786`) | 302 на тот же экран групп после замены списка целиком | `HX-Location` на тот же адрес (идиома D-09 Фазы 9: смена всего списка — не правка на месте) |
  | `accounts.py::accounts_connect_max_start` (`:542`) | полная страница шага `phone`/`qr` | фрагмент контейнера шага мастера (постоянный `id`); пустой телефон → 422 + эхо (D-06) |
  | `profile.py::profile_post` (`:38`) | успех 302 `?notice=profile_saved`; неверный пояс 400 полной страницей | успех — фрагмент формы + код `profile_saved` внеполосным блоком (ПЕРВОЕ поведение ветки «код на фрагменте», механизм покрыт суитой заранее); неверный пояс → 422 + эхо |
  | `billing.py::subscribe_to_plan` (`:269`) | 302 на `confirmation_url` | D-09 |

  Итог: **9 фрагментных, 2 навигационных, 1 внешний**. Второй счёт «отдаёт фрагмент» (D-18
  Фазы 10) растёт на 9.
  — **Reversibility:** costly — форма ответа задаёт разметку целей свопа в шаблонах шести разделов.

- **D-03 (по умолчанию):** Постоянный `id` получает **только блок действий
  `admin/user_detail.html`**. `admin/includes/worker_row.html` и `queue_row.html` в этой фазе
  `id` и макросов НЕ получают. Запись роадмапа «три файла `admin/includes/*` обязаны получить
  `id` и макросы» опиралась на прогноз разведки, где перезапуск и снятие задачи были фрагментами
  класса A; D-06/D-09 Фазы 10 этот прогноз заменили, и `id` без потребителя-свопа ничего не
  добавляет. Прочтение записывается рядом с D-01.
  — **Reversibility:** reversible.

- **D-04 (по умолчанию):** **Изъятие D-08 Фазы 10 остаётся в силе.** Удаление аккаунта и
  объявления из списков идёт `HX-Location`, смещённые курсоры `/accounts/partial` и
  `/ads/partial` не трогаются. Критерий 1 Фазы 11 фрагментного удаления там не требует, а
  изъятие снимается ТОЛЬКО вместе с курсором — порознь эти работы смысла не имеют.
  — **Reversibility:** reversible.

### Создание расписания (FORM-07)

- **D-05 (по умолчанию):** **Прочтение `afterbegin` критерия 3 — ПО СВОЙСТВУ, а не по
  ключевому слову.** Свойство: сущность вставляется в список, контейнер НЕ перерисовывается,
  прокрутка не теряется. Место вставки — **то, которое даёт порядок сервера**: редактор сортирует
  расписания по `Schedule.id` по возрастанию (`app/pages/ads.py:315`), поэтому новая карточка
  встаёт В КОНЕЦ (`beforeend` в контейнер `data-sched-list`, получающий постоянный `id`).
  Буквальный `afterbegin` отвергнут: после F5 карточка переехала бы в конец — экран молча
  расходился бы с сервером, ровно тот класс отказа, который веха закрывает. Смена порядка
  редактора на «новые сверху» отвергнута: видимое изменение экрана, прошедшего UI-ревью, вне
  объёма фазы. ⚠️ Верификатору читать критерий 3 вместе с этим решением.
  Карточка приезжает **раскрытой** (как сегодня после редиректа); соседние карточки не
  трогаются — ранее раскрытая остаётся раскрытой до F5, после которого раскрыта только новая.
  Линейка `sched_count_label` (`ads/form.html`) — постоянная обёртка с `id` + `innerHTML` (D-12
  Фазы 9).
  **Первое расписание:** при пустом списке контейнера нет вовсе (ветка `empty_state`), поэтому
  «было ноль» → `HX-Location` на `/ads/{id}/edit?sched=N#sched-N` — идиома D-09 Фазы 9 в обратную
  сторону, второго механизма отрисовки пустого/непустого состояния не заводится (подпись кнопки
  «+ ДОБАВИТЬ ПЕРВОЕ» → «+ РАСПИСАНИЕ» приезжает тем же переходом).
  — **Reversibility:** reversible.

### Ошибка заполнения и окно 51 (FORM-08)

- **D-06 (по умолчанию):** **422 + эхо введённого применяется ровно там, где ошибка ПОЛЯ
  существует сегодня:** часовой пояс профиля (сегодня 400 полной страницей → 422, выбранное
  значение возвращается) и пустой телефон подключения MAX (сегодня 200 с перерисовкой → 422).
  **Редактор расписаний новых ошибок поля НЕ получает:** `schedules_update` сегодня ничего не
  отвергает — неверные значения тихо отбрасываются (`_clean_ints`, `_clean_times`, пояс
  откатывается к сохранённому), неполное расписание сохраняется выключенным. Завести проверки
  ввода значило бы добавить возможность. `SCHEDULE_ACCOUNT_GONE`, `SCHEDULE_AD_MISSING`,
  `SCHEDULE_VALUES_OUT_OF_DOMAIN` — ИСХОДЫ, а не ошибки поля (граница D-12 Фазы 8): они едут
  `respond(redirect=<редактор>, notice=…)` без фрагмента → `HX-Location`.
  Правило `responseHandling` для 422 (`swap: false`) уже стоит (Фаза 7), и общий обработчик
  отказа 422 пропускает (`htmx_error_banner.html:306`) — форма получает свою перерисовку
  точечным `HX-Retarget`/`HX-Reswap` либо собственным правилом, выбор за планировщиком в рамках
  D-16.
  — **Reversibility:** reversible.

- **D-07 (по умолчанию):** **Окно 51 снимается РАБОТОЙ, изъятие не чеканится.** Границы
  `ge=`/`le=` в аннотациях `Path()`/`Form()` страничных POST-обработчиков переносятся ВНУТРЬ
  обработчиков; значение вне диапазона идёт ТОЙ ЖЕ веткой, что «записи нет / запись чужая»
  данного обработчика (идиома неотличимости D-04 Фазы 9). Объём — **весь реестр
  `VALIDATION_REFUSAL_DIVERGENCES`** (`tests/test_pages/test_htmx_gates.py:2429`; сегодня 23
  записи: `schedules` ×7, `admin` ×6, `account_groups` ×4, `accounts` ×3, `ads` ×2, `history`
  ×1) → **0**, и гейт утверждает пустоту. С исчезновением расхождения вопрос владельцу о его
  законности теряет предмет.
  Именованное изъятие отвергнуто: владельцу пришлось бы чеканить изъятие из запертого D-01 на
  двадцать три входа. Частичный объём (только разделы фазы) отвергнут: пять записей
  `account_groups`/`history` остались бы без адресата.
  JSON-API `app/routes/` (`tests/test_routes/test_schedules_api_identifier_bounds.py`, 422 по
  контракту) **не трогается** — это другой транспорт.
  — **Reversibility:** reversible.

### Отказ по источнику запроса (окно 63) — РЕШЕНИЕ ВЛАДЕЛЬЦА

- **D-08 (владелец, 2026-09-14):** **Голый `Response(status_code=403)` на провале
  `is_same_origin` ОСТАЁТСЯ и объявляется именованным изъятием.** К девяти записям
  `OWN_RESPONSE_EXITS` добавляются три обработчика этой фазы — `admin_toggle_free_access`,
  `admin_toggle_block`, `subscribe_to_plan`; `OWN_RESPONSE_EXITS_DECLARED` **9 → 12**.
  `stop_impersonation` принадлежит Фазе 14 и решает свой случай там.
  **Основание — недостижимость из интерфейса на htmx-пути:** браузер на страницах приложения
  сам ставит `Sec-Fetch-Site: same-origin`; `selfRequestsOnly: true` не даёт htmx уйти на чужой
  адрес; поддельная форма со стороннего сайта приходит полной навигацией и получает тот же 403,
  что и сегодня. Атакующему объяснять незачем.
  **Цена названа:** на htmx-пути общий обработчик `htmx:responseError` поднимает плашку
  «Действие не выполнено. Попробуйте ещё раз через минуту.» (`htmx_error_banner.html:300,305` —
  исключение сделано только для 422), то есть при редком сбое заголовков у прокси человек
  получит неверный совет; панель подтверждения остаётся открытой (свойство плана 10-07
  сохраняется).
  Отвергнуто: отказ через слой ответа с новым кодом уведомления и переходом — новый код реестра,
  отмена свойства 10-07, смена пути без JS с 403 на редирект.
  Запись **закрывает часть «решение о форме» окна 63**; машинный гейт продолжает считать выходы.
  — **Reversibility:** reversible.

### Оплата (FORM-05)

- **D-09 (по умолчанию):** **Третий выход `app/pages/htmx.py` — отдельная функция для
  внешнего адреса**, а не параметр `redirect=` (ловушка D-15 Фазы 8). Без htmx —
  `RedirectResponse(url, 302)` как сегодня; с htmx — 204 + `HX-Redirect`. Перед записью
  заголовка адрес проходит **рантайм-проверку**: схема `https` и хост из ЗАКРЫТОГО множества
  хостов страницы подтверждения ЮKassa. Провал проверки → заголовок не пишется, событие
  логируется, ответ — `respond(redirect="/billing", notice=PAYMENT_FAILED)`.
  Проверка и есть доказательство безопасности, поэтому гейт
  `test_every_header_write_has_a_safe_right_operand` получает **запись** в `SAFE_BY_NAME` по
  форме `location_response` (дыра шириной в одну строку, а не разрешение классом);
  `HX_HEADER_WRITES` **2 → 3**.
  Множество хостов **не угадывается в коде**: планировщик снимает его с документации ЮKassa, а
  ручной UAT критерия 2 записывает хост фактического `confirmation_url` тестового ключа.
  Ветки отказа (`PAYMENT_DISABLED`, `PAYMENT_PENDING`, `PAYMENT_FAILED`) → `respond(redirect=
  "/billing", notice=…)` → `HX-Location`. Запрет `hx-sync` с `queue` на маршруте (PAY-02)
  остаётся в силе.
  — **Reversibility:** reversible.

### Админка: `?result=` (D-07 Фазы 10)

- **D-10 (по умолчанию):** **`?result=` сводится в `?notice=`.** Значения `QUEUE_DROP_RESULTS`
  становятся кодами закрытого реестра `app/pages/notices.py`, тексты переносятся ДОСЛОВНО;
  старое написание снимается сразу, гейт утверждает **0** вхождений `?result=` в `app/` (идиома
  D-09 Фазы 8); собственное место отрисовки `admin/queue.html:34-35` снимается — исход рисует
  общая область шелла (D-12 Фазы 8). Вызовы — `app/pages/admin.py:1145,1160,1173`.
  Попутно приводится к истине комментарий `app/pages/billing.py:93-95` («Три частных реестра…
  Копий не осталось ни одной») и закрывается пункт §Active `PROJECT.md` о четвёртом частном
  реестре.
  D-03 Фазы 10 («новых кодов фаза не заводит») здесь не связывает: то решение Фазы 10, а коды
  этой записи ЗАМЕЩАЮТ существующий частный реестр, а не добавляют сообщения.
  — **Reversibility:** reversible.

### Сводный список расписаний, Alpine и адрес

- **D-11 (по умолчанию):** **Курсор `/schedules/partial` переводится на ключ последней строки**
  (ветвь `keyset`, выбранная владельцем в Фазе 9 для того же класса отказа). Основание снято с
  кода: список листается смещением (`app/pages/schedules.py:765-769,788`) и фильтруется по
  `state`; фрагментный тумблер под фильтром состояния выводит строку из выдачи, и следующая
  порция пропускает ровно одну строку — дословно CR-01 Фазы 9. Порядок уже `Schedule.id`, так что
  ключ естественный.
  `HX-Location` при активном фильтре отвергнут: строка исчезала бы из-под руки, а фрагментный
  контракт работал бы через раз.
  Тумблер наследует решения Фазы 9 целиком: `x-on:change="$el.submit()"` снимается, отправку
  берёт `hx-trigger="change"`; защита от двойного нажатия — по прецеденту DIV-09-02
  (`hx-sync="this:drop"`); «не найдено / чужое» → `HX-Location` (D-13 Фазы 9); ловушка
  оптимистичного чекбокса закрыта D-13/D-16 Фазы 9.
  — **Reversibility:** costly — разметка сентинела прокрутки держится идентичной в двух шаблонах и
  закреплена гейтом.

- **D-12 (по умолчанию):** **Критерий 5 (Alpine после свапа) — прочтение по разделам.**
  (а) Раскрытие карточки расписания — СЕРВЕРНОЕ состояние (`expanded_id`, `keep_sched`,
  `sched_card.html:71,131-132`), а не Alpine; «раскрытая карточка не схлопывается» обеспечивает
  фрагмент, отрисованный с раскрытием из формы. (б) Внутри целей свопа — только голый `x-data`
  (D-08 Фазы 9); панели подтверждения остаются снаружи карточек. (в) **В шаблоны `accounts/*`
  фаза НОВЫХ свопов не приносит** (D-02: оба действия синхронизации — `HX-Location`), поэтому
  тройная копия разметки карточки аккаунта в этой фазе **не сводится** в один макрос; «три
  шаблона `accounts/*` не теряют состояние» наблюдается ручным UAT на существующем опросе
  `account-row-N` (`outerHTML`) и на панелях удаления после десятков действий без перезагрузки.
  Утечка слушателей и размножение панелей — тот же UAT-пункт 5. ⚠️ Верификатору читать критерий 5
  вместе с этим решением.
  — **Reversibility:** reversible.

- **D-13 (по умолчанию):** **Атрибут `hx-push-url` фаза не ставит ни на одну форму.** Все
  фрагментные действия фазы меняют только данные; навигационные и внешний переход меняют адрес
  сами. Решение «по каждой форме» по конвенции трёх случаев — QUAL-04, Фаза 15.
  **Отдельный пункт, названный роадмапом:** совместное поведение `hx-push-url` с заголовком
  `HX-Push-Url` — сегодня `app/pages/ads.py:548` (роадмап называл `:522`, строка сдвинулась).
  Фаза проверяет, что `HX-Push-Url` при создании объявления переживает переезд на `respond()`, и
  записывает наблюдение; UAT-пункт 7 (Back и F5 не предлагают повторить POST) снимается на
  переходах `HX-Location` и на создании объявления.
  — **Reversibility:** reversible.

### Пары утверждений (GATE-02)

- **D-14 (по умолчанию):** **Прочтение критерия 4 — вторая половина пары утверждает «htmx-путь
  не получает полного документа и редиректа»:** фрагментная ветка → 200 и `"<!DOCTYPE" not in
  response.text`; навигационная → 204 + `HX-Location` (у оплаты — `HX-Redirect`), тела нет.
  Буквальное «с заголовком → 200» для всех отвергнуто: оно противоречит отгруженной ветке Фазы 8
  (204). **Вселенная обхода:** утверждения `status_code == 302` на POST-запросах к
  `@router.post`-обработчикам `app/pages/`, идущим через `respond()`; редиректы GET-страниц
  (вход, гейт доступа) вне её; обработчики, ещё стоящие в `NOT_YET_CONVERTED`, вне её и входят
  автоматически, покидая перечень. **Число «160» — прогноз:** сегодня вхождений 191 всего, из них
  около 136 на POST (эвристический замер 2026-09-14); объявляется число, которое СНИМАЕТ ОБХОД,
  константой по идиоме D-13 Фазы 8, с летописью по форме D-17 Фазы 10. Существующие утверждения
  `302` не заменяются и не размножаются в 320 функций: один параметризованный модуль; у каждого
  переведённого обработчика не меньше одной пары (замыкание с дополнением `NOT_YET_CONVERTED`).
  — **Reversibility:** reversible.

### Порядок и заголовки

- **D-15 (подтверждено):** Порядок роадмапа не переставляется: `schedules` + `ads` → `admin` →
  `accounts` последним; `billing` — не первым, после отработки контракта на `schedules`/`ads`,
  поверх потолка Фазы 8 (построен). Перенос границ окна 51 (D-07) естественно идёт с первой
  волной `schedules`, где сидят семь исходных входов.

- **D-16 (по умолчанию):** **`HX-Retarget` и `HX-Reswap` — только поимённым перечнем** с
  обоснованием на запись и счётом ЧИСЛОМ (форма `DISABLED_ELT_EXCEPTIONS`), по FORM-10. Кандидаты,
  видимые сегодня: перерисовка формы на 422 (D-06) и ветка «было ноль» создания, если планировщик
  предпочтёт её переходу. Каждое применение делает поведение невидимым в шаблоне — поэтому перечень,
  а не практика.
  — **Reversibility:** reversible.

### Инвентарные числа, которые фаза обязана подвинуть ЯВНО

Идиома D-13 Фазы 8. Значения «сейчас» сняты с кода 2026-09-14; где стоит «пересчитать» — число
снимается планировщиком своим обходом, а не выводится.

| Константа | Файл | Сейчас | Станет |
|---|---|---|---|
| `NOT_YET_CONVERTED_COUNT` | `tests/test_pages/test_htmx_gates.py` | 26 | **14** (D-01) |
| `OWN_RESPONSE_EXITS_DECLARED` | там же, `:3986` | 9 | **12** (D-08) |
| `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` | там же, `:2981` | 23 | **0** (D-07) |
| `HX_HEADER_WRITES` | там же, `:163` | 2 | **3** (D-09) |
| `SAFE_BY_NAME` | там же, `~:1585` | 1 запись | 2 записи (D-09) |
| второй счёт «отдаёт фрагмент» (D-18 Фазы 10) | см. Фазу 10 | — | +9 (D-02) |
| `HX_POST_PLACES`, `OOB_BLOCKS`, `HX_TARGETS`, `FRAGMENT_ROUTES_DECLARED` | `tests/test_templates/test_htmx_markup_gates.py` | пересчитать | пересчитать |
| `CLIENT_STATE_NODES` | там же | пересчитать | не должен меняться; если снятие `x-on:change` уносит голый `x-data`, число двигается явно с записью |
| перечень `HX-Retarget`/`HX-Reswap` | новый | — | заводится (D-16) |
| `?result=` в `app/` | новый гейт | 3 вызова | **0** (D-10) |

### Claude's Discretion

- Имя и сигнатура третьего выхода `htmx.py`; форма и место закрытого множества хостов ЮKassa.
- Механизм перерисовки формы на 422: точечный `HX-Retarget`/`HX-Reswap` (в перечень D-16) или
  иное, не расширяющее шесть ключей конфигурации (D-03 Фазы 7).
- Способ сборки вселенной пар (разбор дерева тестов против реестра случаев) — при условии, что
  число снимает обход (D-14).
- Имена скрытых полей контекста для тумблера расписания (D-02) и постоянных `id` (`data-actions`,
  `data-sched-list`, линейка счётчика, контейнер шага MAX).
- Помощник проверки границы идентификатора внутри обработчиков (D-07) — один на проект.
- Состав побочных OOB-областей карточки пользователя (D-02) — какие ещё места страницы печатают
  признак безлимита и блокировки.
- Нарезка на планы и волны в пределах порядка D-15.

### Deferred Ideas (OUT OF SCOPE)

- **Фрагментное удаление аккаунта и объявления вместе с keyset-курсорами `/accounts/partial` и
  `/ads/partial`** — снимает изъятие D-08 Фазы 10 (D-04). Фаза-владелец не назначена; назначает
  владелец.
- **Сведение тройной копии разметки карточки аккаунта в один макрос** — кандидат, когда карточки
  `accounts/*` получат фрагментные ответы (D-12).
- **`id` и макросы `admin/includes/worker_row.html` и `queue_row.html`; фрагментные перезапуск и
  снятие задачи** — только вместе с непозиционным ключом панели очереди, не нарушающим WR-04 (D-03).
- **Проверки ввода в редакторе расписаний** (ошибки поля на пустые дни/время) — новая возможность,
  не перевод (D-06).
- **Порядок расписаний «новые сверху» в редакторе** — видимое изменение экрана (D-05).
- **Понятный текст отказа по источнику запроса** — отвергнут владельцем (D-08); кандидат к возврату,
  если такие отказы появятся в журналах у живых пользователей.
- **`hx-push-url` по каждой форме** — QUAL-04, Фаза 15 (D-13).
- **Отказ по источнику у `stop_impersonation`** — Фаза 14.
- Reviewed Todos (not folded): `full-suite-ads-editor-order-pollution`, `plan-price-credibility-bound`.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FORM-03 | правка на месте возвращает фрагмент по `id` строки/карточки + OOB; контейнер не перерисовывается | §«Паттерн 1: фрагмент через `respond(fragment=…)`», §Сверка дрейфа (9 фрагментных обработчиков, `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3` → 12), §Pitfalls 4, 5, 7 |
| FORM-04 | навигационные действия возвращают `HX-Location` | §«Паттерн 2: навигация `respond()` без `fragment`» (готовая ветка `htmx.py:474-475`), Pitfall 8 (`_SYNC_IN_FLIGHT`) |
| FORM-05 | `/billing/subscribe` → `HX-Redirect`, а не `HX-Location` | §«Находка A: `HX-Redirect` в 2.0.10» (проверено по вендоренному файлу), §«Находка C: хосты ЮKassa», §Code Examples «Третий выход» |
| FORM-07 | создание вставляет сущность в список, не перерисовывая контейнер | D-05 (`beforeend` в `data-sched-list`, `ads.py:315` порядок подтверждён), Pitfall 6 (ветка `empty_state`) |
| FORM-08 | 422 + перерисовка формы + эхо введённого | ⚠️ §«Находка B: `HX-Reswap` НЕ включает своп на 422» — главный риск фазы; Pitfall 1 |
| FORM-10 | `HX-Retarget`/`HX-Reswap` только поимённо | §Находка B (перечень, вероятно, пуст при правильной разметке цели), §Validation Map |
| GATE-02 | 302-утверждения становятся парами параметризованным обходом | §«Паттерн 4: обход пар», замер вселенной (157 утверждений в POST-тестах против «~136» CONTEXT), образец `tests/test_pages/test_confirm_delete_transport.py` |
</phase_requirements>

## Summary

Всё, на что опирается фаза, уже есть в дереве: `respond()` с ветками «302 / 204 + `HX-Location` / фрагмент» и приклейкой кода уведомления к фрагменту (`app/pages/htmx.py:394-485`), фикстура `htmx_client` (`tests/conftest.py:70`), реестры-гейты с числом. Новых зависимостей фаза не требует. Все номера строк, на которые ссылается CONTEXT, сверены с текущим деревом. Дрейф один, и он в замере вселенной пар: 157 против «около 136» (см. §Сверка).

Сессия нашла **три факта, которые меняют план**. Все три сняты с первоисточников.

1. **(Находка B — блокирующая для D-06/FORM-08.)** В вендоренном htmx 2.0.10 решение «свопать ли» берётся ТОЛЬКО из правила `responseHandling` (`shouldSwap: f`, где `f = c.swap`). Заголовок `HX-Reswap` меняет лишь *стиль* свопа (`swapOverride`), `HX-Retarget` — лишь цель. При правиле `{"code":"422","swap":false,"error":true}` ни один заголовок перерисовку формы не включит. Путь без нового JS один: вернуть правилу `422` значение `"swap": true`. Это правка ЗНАЧЕНИЯ, а не седьмой ключ, поэтому D-03 Фазы 7 не нарушается. Но она явно открывает три запертых места: гейт `test_validation_rule_carries_both_swap_and_error` (`swap is False`), литерал `SERVER_SIDE_VALIDATION_RESPONSES = 0` и запись безопасности `07-05/T-07-13` (своп на 422 — сток исполнения скрипта, пока 422 может прийти умолчанием фреймворка с эхо ввода). Возврат свопа эти записи прямо разрешают «только одновременно с первым маршрутом, отдающим 422 с авторским фрагментом», то есть ровно в этой фазе. Но тогда нужно закрыть остаточные источники 422 умолчания на страничных маршрутах.
2. **(Находка A.)** В 2.0.10 `HX-Redirect` исполняется как `location.href = …`, то есть полной навигацией браузера, а не XHR. Проверка `selfRequestsOnly` (функция `Ln`) стоит только на XHR-пути, и межсайтовый переход ею не блокируется. `HX-Location` же уходит через `Nn("get", …)` → XHR → `Ln` и на чужом хосте отказывает. Посылка D-09 подтверждена. Порядок в обработчике: `HX-Location` читается раньше `HX-Redirect`, и оба — раньше `responseHandling`, так что 204 не мешает.
3. **(Находка C — множество хостов ЮKassa.)** Официальная документация говорит, что пользователю «необходимо что-то сделать на странице ЮKassa или ее партнера». Закрытость множества хостов документация НЕ гарантирует. Все найденные официальные примеры `confirmation_url` — на хосте `yoomoney.ru`. Проект создаёт платёж без `payment_method_data` (`app/services/payment_service.py:723-732`), то есть пользователь выбирает способ оплаты на странице ЮKassa. Рекомендация: закрытое множество `{"yoomoney.ru"}`, точное сравнение хоста. При этом ручной UAT критерия 2 обязателен ДО мержа, а ветка отказа проверки — громкий журнал. Тестовые фикстуры проекта используют `https://yookassa.ru/checkout/payments/…`, которого в документации как хоста подтверждения нет, поэтому пары оплаты должны взять документированный хост.

**Primary recommendation:** начать волну `schedules`+`ads` с решения по Находке B. В одном плане вернуть правилу `422` своп, снять утверждение `swap is False`, двинуть `SERVER_SIDE_VALIDATION_RESPONSES` и закрыть сток T-07-13: на htmx-пути ни один 422 умолчания FastAPI не должен доезжать до свопа. Перечень D-16 при этом, скорее всего, остаётся ПУСТЫМ: цель 422 совпадает с целью успеха.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Выбор формы ответа (302 / 204+`HX-Location` / фрагмент / `HX-Redirect`) | API / Backend (`app/pages/htmx.py`) | — | единственное место решения (FOUND-04); обработчик только подаёт `redirect=`, `fragment=`, `notice=` |
| Проверка внешнего адреса ЮKassa | API / Backend (третий выход `htmx.py`) | — | рантайм-проверка перед записью заголовка, по форме `_local_path` |
| Граница идентификатора (D-07) | API / Backend (обработчик, до первого `select`) | — | снимается с аннотации FastAPI, иначе 422 умолчания |
| Разметка целей свопа (`id`, `hx-target`, `hx-swap`) | Frontend Server (Jinja2 макросы) | Browser (htmx) | цель объявляется в шаблоне; `HX-Retarget` скрывает её, поэтому только по перечню |
| Свап / OOB / история / навигация по заголовкам | Browser (htmx 2.0.10) | — | рантайм вендоренного файла; поведение снято с его кода |
| Раскрытие карточки расписания | Frontend Server (`expanded_id`, `keep_sched`) | — | серверное состояние, не Alpine (D-12а) |
| Клиентское состояние панелей | Browser (Alpine) | — | вне целей свопа (GATE-06), только голый `x-data` внутри |
| Keyset-курсор `/schedules/partial` | API / Backend + Database | Frontend Server (сентинел) | порядок `Schedule.id`, ключ последней строки |
| Пары 302/htmx | Test tier (pytest, `htmx_client`) | — | параметризованный модуль |

## Сверка дрейфа (CONTEXT против дерева 2026-09-14)

| Утверждение CONTEXT | Замер сессии | Статус |
|---|---|---|
| Обработчики на `schedules.py:901,995,1078`; `ads.py:584,720`; `admin.py:1597,1812`; `accounts.py:542,714,786`; `profile.py:38`; `billing.py:269` | те же строки (`grep -nE "^async def …"`) [VERIFIED: grep] | совпадает |
| `HX-Push-Url` на `ads.py:548` | `app/pages/ads.py:548: response.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"` [VERIFIED: app/pages/ads.py:544-551] | совпадает |
| Порядок расписаний `ads.py:315` | `315: .order_by(Schedule.id)` [VERIFIED: grep] | совпадает |
| `?result=` на `admin.py:1145,1160,1173` | `1145 …?result=unknown_account`, `1160 …?result={outcome}`, `1173 …?result={DROP_REMOVED}` [VERIFIED: app/pages/admin.py:1145-1173] | совпадает; `QUEUE_DROP_RESULTS` объявлен на `admin.py:308`, читается на `:1065` |
| Тесты, читающие `result=` | `tests/test_pages/test_hx_location_destinations.py`, `test_account_groups.py`, `test_confirm_delete_transport.py` [VERIFIED: grep -rln] | новое для плана D-10: эти файлы правятся вместе с кодом |
| `NOT_YET_CONVERTED_COUNT = 26` | `tests/test_pages/test_htmx_gates.py:344: NOT_YET_CONVERTED_COUNT = 26`; 26 ключей в перечне `:201-230` [VERIFIED: Read] | совпадает; 12 ключей фазы присутствуют, `MONEY_HANDLER_KEY = "app/pages/billing.py::subscribe_to_plan"` (`:155`) |
| `HX_HEADER_WRITES = 2` (`:163`) | `163:HX_HEADER_WRITES = 2`; две записи: `app/pages/htmx.py:169` и `app/pages/ads.py:548` [VERIFIED] | совпадает |
| `SAFE_BY_NAME` одна запись (`~:1585`) | `1585: SAFE_BY_NAME: dict[str, str] = {"app/pages/htmx.py::location_response": (…)}` [VERIFIED: Read :1585-1597] | совпадает |
| `VALIDATION_REFUSAL_DIVERGENCES` (`:2429`) 23 записи | `2981:VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 23`; поля `entry=`: schedules 7, ads 2, account_groups 4, accounts 3, history 1, admin 6 [VERIFIED: sed + grep] | совпадает |
| `OWN_RESPONSE_EXITS` (`:3804`), 9 | `3986:OWN_RESPONSE_EXITS_DECLARED = 9`; 9 `entry=` (account_groups_delete, accounts_delete, admin_restart_worker, admin_drop_task, admin_impersonate, admin_delete_user, ads_delete, history_retry, schedules_delete) [VERIFIED] | совпадает |
| «второй счёт отдаёт фрагмент» | `1399:FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3` [VERIFIED: grep] | имя константы теперь названо: **3 → 12** |
| Разметочные константы «пересчитать» | `HX_POST_PLACES = 3` (`:140`), `FRAGMENT_ROUTES_DECLARED = 11` (`:895`), `HX_TARGETS = 1` (`:1831`), `OOB_BLOCKS = 13` (`:1932`), `CLIENT_STATE_NODES = 24` (`:1952`) в `tests/test_templates/test_htmx_markup_gates.py` [VERIFIED: grep -nE "^NAME ="] | стартовые значения для планировщика |
| Правила `responseHandling` `htmx_config.html:126-131` | строки 127-131; правило 422 на `:129`: `{"code":"422", "swap": false, "error": true},` [VERIFIED: grep -n] | сдвиг на 1 (126 — открывающая строка массива) |
| Исключение 422 в баннере `:306` | `306: if (event.detail && event.detail.xhr && event.detail.xhr.status === 422) { return; }` [VERIFIED] | совпадает |
| «191 утверждение 302, ~136 на POST» | 191 в 36 файлах; **157** внутри тест-функций, содержащих `.post(` [VERIFIED: AST-скрипт, см. ниже] | **дрейф эвристики**: 136 vs 157 — разные эвристики; обход сам снимает окончательное число (D-14) |
| `sched_card.html:112` `id="sched-N"`, тумблер `:122`, `keep_sched` `:131-132` | `112: <article data-sched-card id="sched-{{ s.id }}">`; `122: <form method="post" action="/schedules/{{ s.id }}/toggle" x-data x-on:change="$el.submit()">`; `132: <input type="hidden" name="keep_sched" value="{{ expanded_id }}">` [VERIFIED: grep] | совпадает |
| `schedule_row.html:64,81` | `64: <article class="sched-item" id="schedule-row-{{ s.id }}">`; `81: <form … x-data x-on:change="$el.submit()">` [VERIFIED] | совпадает |
| `ads/form.html` `data-sched-list` без `id`, форма создания `:241` | `223: <div data-sched-list>`; `241: <form method="post" action="/schedules/new">`; `250: … '+ РАСПИСАНИЕ' if editor.schedules else '+ ДОБАВИТЬ ПЕРВОЕ'` [VERIFIED] | совпадает |
| `user_detail.html` `data-actions`, формы `:145,:149` | `133: <div data-actions>`; `145: …/unlimited">`; `149: …/block">` [VERIFIED] | совпадает |
| `queue.html:34-35` | `34: {% if drop_result %}` / `35: {{ alert(drop_result[0], variant=drop_result[1]) }}` [VERIFIED: sed 28-40] | совпадает |
| `profile_post` сегодня: успех 302, неверный пояс 400 полной страницей | `return RedirectResponse(url=f"/profile?notice={notices.PROFILE_SAVED}", status_code=302)`; `"error": "Неверный часовой пояс"`, `status_code=400` [VERIFIED: app/pages/profile.py] | совпадает |
| `accounts_connect_max_start` пустой телефон — 200 перерисовкой | `TemplateResponse("accounts/connect_max.html", {…"step": "phone", "error": "Введите номер телефона"})` без `status_code` [VERIFIED] | совпадает |
| `/schedules/partial` смещением `:765-769,788` | `765: offset: int = Query(0, ge=0)`; `query.order_by(Schedule.id).offset(offset).limit(limit + 1)`; сентинел `hx-get="/schedules/partial?offset={{ next_offset }}…"` в `schedules/list.html:61` и `schedules/partial_cards.html:7` [VERIFIED] | совпадает |

Команда замера вселенной пар (повторяема):
`uv run python /tmp/claude-1000/-source-broadcaster/29e6a8b0-914f-45d2-b00f-b03ee76f0872/scratchpad/count302.py` → `assert302_in_test_funcs 191 in_funcs_with_post 157`. Эвристика завышена: сюда входят POST на ещё не переведённые маршруты (auth, QR) и 302 на GET внутри тех же функций. Верхние файлы: `test_account_groups.py` 23, `test_routes/test_sync_groups.py` 19, `test_history_retry.py` 17, `test_editor_schedules.py` 16, `test_schedule_ownership.py` 12.

## Standard Stack

### Core (всё уже установлено — новых зависимостей 0, запрет вехи)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| htmx (вендоренный) | 2.0.10 | свап, OOB, `HX-*` заголовки | `app/static/js/htmx.min.js` содержит `version:"2.0.10"` [VERIFIED: grep] |
| FastAPI / Starlette | как в `uv.lock` | обработчики `app/pages/` | действующий стек проекта [VERIFIED: CLAUDE.md] |
| Jinja2 | как в `uv.lock` | макросы фрагментов | гейты требуют МАКРОСЫ, не `{% block %}` [CITED: REQUIREMENTS.md Out of Scope] |
| pytest | 9.0.2 | суита | `uv run pytest --version` → `pytest 9.0.2` [VERIFIED] |
| pytest-asyncio | 1.3.0 | async-тесты | `uv pip list` [VERIFIED] |
| httpx | 0.28.1 | `AsyncClient` / `htmx_client` | `uv pip list` [VERIFIED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| своп на 422 правилом `responseHandling` | `htmx:beforeSwap`-слушатель, ставящий `detail.shouldSwap = true` | новый JS — запрещён рамкой вехи |
| своп на 422 | расширение `response-targets` (`hx-target-422`) | новый вендоренный файл — Out of Scope |
| 422 на htmx-пути | 200 с перерисованной формой | нарушает букву FORM-08 («возвращает 422») |

**Installation:** не требуется.

## Package Legitimacy Audit

Фаза не устанавливает внешних пакетов (рамка вехи «0 новых зависимостей», REQUIREMENTS.md Out of Scope). Проверка `package-legitimacy` не применима.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Браузер (форма с hx-post == action)
   │  POST + HX-Request: true             POST без заголовка (без JS)
   ▼                                           ▼
FastAPI обработчик app/pages/<раздел>.py ──────┘
   │ 1. кто пришёл (cookie)  2. is_same_origin → голый 403 (D-08, OWN_RESPONSE_EXITS)
   │ 3. граница id ВНУТРИ (D-07) → ветка «нет/чужое»   4. действие (без изменений)
   ▼
решение формы ответа ── app/pages/htmx.py ───────────────────────────────┐
   ├─ respond(redirect=…, notice=…)            → 302 | 204 + HX-Location (класс B, исходы)
   ├─ respond(redirect=…, fragment=…, notice?) → 302 | 200 фрагмент (+OOB notice) (класс A)
   ├─ 422 + форма с эхо (профиль, MAX)         → 422 фрагмент (нужен swap:true у правила 422)
   └─ третий выход (внешний адрес ЮKassa)      → 302 | 204 + HX-Redirect (хост проверен)
                                                  └ провал проверки → respond("/billing", PAYMENT_FAILED)
   ▼
htmx 2.0.10 в браузере (Vn): HX-Trigger → HX-Location(XHR, selfRequestsOnly) → HX-Redirect(location.href)
   → responseHandling(код → swap/error) → HX-Retarget/HX-Reswap → swap цели + OOB → история (HX-Push-Url > hx-push-url)
   ▼
DOM: цель по id (#sched-N, #schedule-row-N, [data-actions]→id, контейнер шага MAX, форма профиля)
     OOB: счётчик расписаний (innerHTML), #notice (innerHTML)
```

### Recommended Project Structure (что трогается)
```
app/pages/htmx.py                  # третий выход (внешний адрес) + множество хостов
app/pages/identifiers.py           # помощник границы id (D-07), неограниченный алиас для POST
app/pages/{schedules,ads,admin,accounts,profile,billing}.py
app/pages/notices.py               # коды из QUEUE_DROP_RESULTS (D-10)
app/templates/ads/{form.html,includes/sched_card.html}
app/templates/schedules/{list.html,partial_cards.html,includes/schedule_row.html}
app/templates/admin/{user_detail.html,queue.html}
app/templates/accounts/connect_max.html, profile.html
app/templates/includes/htmx_config.html   # ⚠️ Находка B: значение swap у правила 422
tests/test_pages/test_htmx_gates.py, test_htmx_response_contract.py, test_shell.py
tests/test_templates/test_htmx_markup_gates.py
tests/test_pages/<новый модуль пар GATE-02>.py
```

### Находка A: `HX-Redirect` против `selfRequestsOnly` в 2.0.10 (FORM-05)

Снято с вендоренного `app/static/js/htmx.min.js` [VERIFIED: grep по файлу, 2.0.10]:

```js
// обработчик ответа Vn — порядок:
if(T(n,/HX-Trigger:/i)){ze(n,"HX-Trigger",t)}
if(T(n,/HX-Location:/i)){let e=n.getResponseHeader("HX-Location"); … s.push=s.push??"true";Nn("get",e,s);return}
const l=T(n,/HX-Refresh:/i)&&n.getResponseHeader("HX-Refresh")==="true";
if(T(n,/HX-Redirect:/i)){e.keepIndicators=true;Q.location.href=n.getResponseHeader("HX-Redirect");l&&Q.location.reload();return}
…
const u=Mn(t,e);const c=Bn(n);const f=c.swap;   // responseHandling — ПОСЛЕ заголовков перехода

// проверка пути XHR:
function Ln(e,t,n){… const i=o===r.origin;if(Q.config.selfRequestsOnly){if(!i){return false}} …}
// вызывается в issueAjaxRequest: if(!Ln(r,H,C)){fe(r,"htmx:invalidPath",C); …}
```

Следствия:
- `HX-Redirect` — это присвоение `location.href`, полная навигация без XHR. `Ln`/`selfRequestsOnly` к ней не применяются, и переход на `yoomoney.ru` пройдёт.
- `HX-Location` уходит через `Nn("get", …)`, то есть через XHR с проверкой `Ln`. На чужом origin будет `htmx:invalidPath`, и переход молча не состоится. Это подтверждает ловушку, записанную в `htmx.py:39-43`.
- `HX-Location` проверяется ПЕРВЫМ. Ответ, несущий оба заголовка, уйдёт по `HX-Location`, поэтому третий выход обязан ставить ровно один.
- `keepIndicators=true`: индикатор кнопки оплаты остаётся видимым до ухода страницы, это ожидаемо.
- Оба заголовка читаются ДО `responseHandling`, поэтому ответ 204 с `HX-Redirect` отработает (та же посылка, что у `location_response`, `htmx.py:165-166`).

### Находка B: `HX-Reswap`/`HX-Retarget` НЕ включают своп на 422 (FORM-08, D-06, D-16)

[VERIFIED: app/static/js/htmx.min.js, 2.0.10]:

```js
function Bn(e){for(var t=0;t<Q.config.responseHandling.length;t++){var n=Q.config.responseHandling[t];if(Fn(n,e.status)){return n}}return{swap:false}}
// в Vn:
const c=Bn(n);const f=c.swap;let a=!!c.error; …
if(T(n,/HX-Retarget:/i)){e.target=Un(t,n.getResponseHeader("HX-Retarget"))}
if(T(n,/HX-Reswap:/i)){p=n.getResponseHeader("HX-Reswap")}
var m=le({shouldSwap:f,serverResponse:g,isError:a,…,swapOverride:p},e);
if(!ae(r,"htmx:beforeSwap",m))return;
```

`shouldSwap` берётся только из правила. Текущее правило [VERIFIED: app/templates/includes/htmx_config.html:129]: `{"code":"422", "swap": false, "error": true},`. Значит D-06 в формулировке «перерисовка точечным `HX-Retarget`/`HX-Reswap`» **не работает**: ответ 422 придёт, баннер промолчит (`:306`), а форма не перерисуется. Это та самая «мёртвая кнопка», о которой предупреждает шапка `htmx_config.html`.

Единственный путь в рамках «ни нового JS, ни седьмого ключа»: **значение `"swap": true` у правила 422** (порядок пяти правил не трогается). Правка запускает три записанных механизма, и план обязан пройти их явно:

| Что краснеет / что правится | Где | Цитата |
|---|---|---|
| утверждение `swap is False` | `tests/test_pages/test_htmx_response_contract.py:194` `test_validation_rule_carries_both_swap_and_error` | «вернуть его ПРАВОМЕРНО только одновременно с появлением первого маршрута, отдающего 422 с авторским фрагментом» [VERIFIED: Read] |
| литерал числа мест 422 в `app/` | там же, `:72: SERVER_SIDE_VALIDATION_RESPONSES = 0` | гейт `:169` краснеет на первом `status_code=422` [VERIFIED] |
| литерал правила в тесте шелла | `tests/test_pages/test_shell.py:1300: {"code": "422", "swap": False, "error": True},` [VERIFIED: grep] | GATE-08 утверждает каждую строку конфигурации |
| запись безопасности | `.planning/phases/07-…/07-SECURITY.md:114` «`07-05/T-07-13` \| InfoDisclosure \| … `swap` снят у правила `422`» [VERIFIED: grep] | своп на 422 = сток исполнения скрипта, пока 422 может быть умолчанием фреймворка с эхо ввода |

**Остаточные источники 422 умолчания FastAPI на страничных POST** (их тело с `swap:true` вклеилось бы в DOM):
- `IdPath = Annotated[int, Path(ge=1, le=ID_MAX)]`, `IdForm = Annotated[int, Form(ge=1, le=ID_MAX)]`, `OptionalIdForm = …Form(ge=1, le=ID_MAX)` [VERIFIED: app/pages/identifiers.py:97-103]. D-07 снимает границы, но **нечисловое** значение пути (`/schedules/abc/edit`) по-прежнему даёт 422 разбора типа. `IdPath` используется в `app/pages/*.py` 33 раза, в том числе GET-маршрутами вне D-07 [VERIFIED: grep -c].
- Обязательные поля формы `Form(...)`: `app/pages/profile.py:40 timezone: str = Form(...)`, `app/pages/admin.py:1088 task_id: str = Form(...)`, 14 в `auth.py` (Фаза 14) [VERIFIED: grep].
- Обработчика `RequestValidationError` в `app/main.py` нет: зарегистрированы `HtmxRefusal`, `NotFoundError`, `ForbiddenError`, `BillingLimitError`, `MessengerConnectionError`, `Exception` (`:219-248`) [VERIFIED: grep].

Достижимость из интерфейса низкая: `hx-post` рендерится сервером с целыми, поле пояса — `select`. Остаётся self-XSS через подделанный запрос. Но T-07-13 записан как `mitigate`, и снятие смягчения без замены — регрессия безопасности. Варианты для планировщика (все `[ASSUMED]`, выбор — план, запись — `11-SECURITY`):
1. Неограниченные алиасы `str`-путь/форма на страничных POST и разбор целого внутри помощника D-07 (нечисловое значение идёт веткой «нет/чужое»). `Form(...)` у двух обработчиков фазы превращается в `Form("")` с проверкой внутри. Остаток — только `auth.py`, куда htmx-формы придут в Фазе 14. Минимально инвазивно и естественно продолжает D-07.
2. Обработчик `RequestValidationError`, отвечающий на htmx-пути через `refuse`-подобный транспорт (204 + `HX-Location`), а на остальных — прежним JSON. Гейт `_status_code_literals` считает `exception_handler(RequestValidationError)` местом (`test_htmx_response_contract.py`), и JSON-API `app/routes/` задевать нельзя (D-07).

**Следствие для D-16/FORM-10.** Если цель 422 совпадает с целью успеха (форма профиля перерисовывается в ту же обёртку; шаг MAX — в тот же контейнер шага), `HX-Retarget`/`HX-Reswap` не нужны вовсе. Перечень заводится с числом **0** и гейтом «вхождений `HX-Retarget`/`HX-Reswap` в `app/` == записей перечня». Сегодня вхождений 0 [VERIFIED: grep -rn по `app/`, пусто]. Ветка «было ноль» D-05 уже решена переходом.

### Находка C: множество хостов страницы подтверждения ЮKassa (D-09)

- Документация: при сценарии `redirect` «пользователю необходимо что-то сделать на странице ЮKassa или ее партнера»; «Вам нужно перенаправить пользователя на `confirmation_url`» [CITED: yookassa.ru/developers/payment-acceptance/getting-started/payment-process]. **Слово «партнёра» прямо означает, что множество хостов документацией НЕ закрыто.** Это утверждение документации, а не вывод из отсутствия.
- Официальные примеры `confirmation_url` (все на `yoomoney.ru`):
  - `https://yoomoney.ru/api-pages/v2/payment-confirm/epl?orderId=…` [CITED: …/getting-started/payment-process; …/testing-and-going-live/testing]
  - `https://yoomoney.ru/checkout/payments/v2/contract/tinkoff-pay?orderId=…`, `…/v2/contract/electronic-certificate?…`, `https://yoomoney.ru/checkout/payments/sbp?orderId=…`, `https://yoomoney.ru/api-pages/v2/payment-confirm/cash?…`, `https://yoomoney.ru/payments/internal/confirmation?…` [CITED: страницы сценариев yookassa.ru/developers/…, через WebSearch — MEDIUM]
- Проект создаёт платёж так [VERIFIED: app/services/payment_service.py:723-732]: `"confirmation": {"type": "redirect", "return_url": …}`, `"capture": True`, без `payment_method_data`. Пользователь попадает на страницу выбора способа оплаты ЮKassa. Партнёрские страницы (3-D Secure банка и т. п.) при таком создании открываются уже ИЗ страницы ЮKassa, а не как `confirmation_url`. Это `[ASSUMED]` и снимается UAT.
- Хоста `yookassa.ru` в документированных `confirmation_url` не найдено (отсутствие, а не запрет, поэтому `[ASSUMED]`). Фикстуры проекта: `CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"` (`tests/test_pages/test_billing_subscription.py:38`, `test_access_lifecycle.py:48`, `test_billing_payment_errors.py:71`), `tests/test_pages/test_access_gate.py:511` [VERIFIED: grep].

**Рекомендация (MEDIUM):** `frozenset({"yoomoney.ru"})`, сравнение `urlsplit(url).hostname == host` строго (без суффиксов: `evil-yoomoney.ru`, `yoomoney.ru.evil`), схема `https`, порт отсутствует, без userinfo, ASCII, без управляющих символов (переиспользовать проверки `_local_path` по классам). Провал: `logger.error("payment_confirmation_url_rejected", host=…)` без полного адреса, затем `respond(redirect="/billing", notice=notices.PAYMENT_FAILED)`. Пары оплаты — на документированном хосте. Фикстуры `yookassa.ru` без htmx-заголовка продолжают работать, потому что путь 302 не проверяется. Открытый вопрос 2 — об асимметрии.

### Паттерн 1: фрагмент через `respond(fragment=…)` (класс A)
**What:** обработчик собирает `TemplateResponse` макроса строки/карточки и подаёт его замыканием; без htmx уходит тот же 302.
**Example (форма уже в дереве):**
```python
# Source: app/pages/htmx.py:394-400 (сигнатура, VERIFIED)
return await respond(
    request,
    redirect=_editor_url(...),            # путь деградации — обязателен
    fragment=lambda: _render_sched_card(...),   # async-callable → Response
)
```
Приклейка `notice=` к фрагменту допустима только к `text/html` со статусом, разрешающим тело (`_glue_notice`, `htmx.py:328-343`). Для `profile_saved` это первое использование ветки. Сборщик фрагмента обязан возвращать СВЕЖИЙ `Response` без `BackgroundTask` (граница `htmx.py:314-326`).

### Паттерн 2: навигация — `respond()` без `fragment` (класс B и исходы)
`respond(request, redirect=f"/accounts/{account_id}/groups")` даёт 302 или `204 + HX-Location` (`htmx.py:471-475`) [VERIFIED].

### Паттерн 3: `HX-Push-Url` при создании объявления (D-13, пункт ⚠ роадмапа)
[VERIFIED: htmx.min.js функция `Mn`]:
```js
if(T(n,/HX-Push:/i)){…}else if(T(n,/HX-Push-Url:/i)){r=n.getResponseHeader("HX-Push-Url");o="push"}else if(T(n,/HX-Replace-Url:/i)){…}
if(r){if(r==="false"){return{}}else{return{type:o,path:r}}}
… let l=t.etc.push||ne(e,"hx-push-url"); …
```
Заголовок ответа **имеет приоритет** над атрибутом: атрибут читается только при отсутствии заголовка, а `HX-Push-Url: false` подавляет запись истории даже при `hx-push-url="true"`. Раз по D-13 атрибут не ставится ни на одну форму, совместного поведения в этой фазе нет: адрес меняет только заголовок `ads.py:548`. При переезде на `respond(fragment=…)` заголовок, выставленный внутри сборщика, переживает `respond` (ответ возвращается как есть при `notice=None`, `htmx.py:482-484`; `_glue_notice` заголовки не трогает). Утверждать это тестом по `response.headers["HX-Push-Url"]`, а не по коду.
Back/F5: при `historyCacheSize: 0` и `historyRestoreAsHxRequest: false` Back восстанавливает страницу полным GET по адресу из истории, POST не повторяется. `[ASSUMED]` по семантике конфигурации, снимается UAT-пунктом 7.

### Паттерн 4: обход пар GATE-02
Образец в дереве: `tests/test_pages/test_confirm_delete_transport.py` — реестр случаев `_outcome_cases()`, `@pytest.mark.parametrize("case", _outcome_cases(), ids=_case_id)` (`:1287`), число маршрутов константой (`:1223`), замыкание обхода (`:1246`) [VERIFIED: grep]. Для GATE-02:
- (а) AST-обход `tests/` находит утверждения `status_code == 302` в функциях с POST на ключи, переведённые (`POST_HANDLERS − NOT_YET_CONVERTED`);
- (б) реестр случаев «маршрут × ветка» с ожидаемой htmx-половиной (`fragment` → 200 и без `<!DOCTYPE`; `location` → 204 + `HX-Location`, тела нет; `external` → 204 + `HX-Redirect`);
- (в) константа `…_PAIRS_DECLARED` = число, снятое обходом, с летописью «160 → N»;
- (г) замыкание: каждый переведённый обработчик несёт ≥1 случай.
Существующие 302-тесты не трогаются.

### Anti-Patterns to Avoid
- **Внешний адрес в `redirect=`:** `_local_path` выбросит `ValueError` на обоих транспортах (`htmx.py:130-134`).
- **`HX-Retarget` как умолчание для 422:** делает цель невидимой в шаблоне (FORM-10), а своп всё равно не включит (Находка B).
- **Тумблер с `x-on:change="$el.submit()"` под htmx:** `form.submit()` не порождает событие `submit`, и запрос уходит полной навигацией мимо htmx. Снимается по D-11 (`hx-trigger="change"`) [ASSUMED: семантика DOM `HTMLFormElement.submit()`; прецедент Фазы 9].
- **Проверка границы id ниже `select`:** 500 на PostgreSQL при переполнении (Landmine CONTEXT).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ветвление htmx / без JS | `if request.headers.get(...)` в обработчике | `respond()` / `is_htmx()` | `HX_HEADER_READS = 1` — второе чтение роняет гейт |
| адрес с кодом уведомления | f-строка `?notice=` | `respond(notice=…)` → `_with_notice` | якорь и второй `?` (`htmx.py:357-391`) |
| OOB уведомления | ручная разметка в шаблоне ответа | `respond(fragment=…, notice=…)` → `_glue_notice` | длина тела, статус без тела, тип |
| разбор URL ЮKassa | regex по строке | `urllib.parse.urlsplit` + `.hostname` | userinfo, порт, регистр, IDN |
| своп на 422 | JS-слушатель `htmx:beforeSwap` | значение `swap` у правила 422 | запрет нового JS; Находка B |
| keyset-курсор | новый механизм | ветвь `keyset` групп Фазы 9 (`account_groups.py:297 after_id: int | None = Query(None, ge=1, le=ID_MAX)`) | та же форма гейта сентинела |
| пары тестов | 320 функций | параметризованный реестр случаев | GATE-02, образец `test_confirm_delete_transport.py` |

**Key insight:** всё трудное (ветвление, адреса, OOB, безопасность заголовков) уже вынесено в `htmx.py` и гейты. Фаза проигрывает там, где обходит слой, а не там, где его не хватает.

## Common Pitfalls

### Pitfall 1: 422 приходит, форма не перерисовывается
**What goes wrong:** правило `422` с `swap:false` — «мёртвая кнопка» без плашки (баннер пропускает 422).
**Why:** `shouldSwap` берётся только из `responseHandling` (Находка B).
**How to avoid:** в одном плане: `"swap": true` + снятие `swap is False` + `SERVER_SIDE_VALIDATION_RESPONSES` + `test_shell.py:1300` + закрытие стока T-07-13.
**Warning signs:** тест утверждает только код 422 и тело, а не правило конфигурации; UAT: нажатие без видимого следствия.

### Pitfall 2: `HX-Redirect` потерян, тест зелёный
**What goes wrong:** тест проверяет `status_code == 204`, заголовок записан на выброшенный объект.
**How to avoid:** утверждать `response.headers["HX-Redirect"] == CONFIRMATION_URL` и отсутствие `HX-Location` (урок cookie D-05 Фазы 10).

### Pitfall 3: хост ЮKassa, отвергнутый проверкой, ломает оплату молча
**What goes wrong:** реальный `confirmation_url` приходит не с `yoomoney.ru`, htmx-пользователь получает `PAYMENT_FAILED`, платёж-резерв уже создан.
**How to avoid:** журнал `error` с хостом; UAT на тестовом ключе ДО мержа; помнить, что резерв уже в `payments` (потолок PAY-01 — повтор получит `PAYMENT_PENDING`).
**Warning signs:** `payment_confirmation_url_rejected` в Loki.

### Pitfall 4: G-11 — `sched-N` и цель, и OOB-цель
Правка/тумблер целятся в `#sched-N`, удаление Фазы 10 шлёт OOB в тот же `id`. Применить форму Фазы 9, правило не снимать (гейт GATE-05).

### Pitfall 5: панель подтверждения уезжает со свапом карточки
`sched_card.html:256` содержит форму с `x-on:submit.prevent="$dispatch('modal-open-sched-del-…')"` внутри `<article id="sched-N">`, а сама панель `modal(...)` должна остаться снаружи. Подмена `outerHTML` не должна задвоить или унести панель.

### Pitfall 6: «было ноль» — нет контейнера
`data-sched-list` рендерится только при непустом списке (`ads/form.html:223` против `empty_state` на `:233`). Фрагмент `beforeend` в отсутствующую цель даст `htmx:targetError`. Ветка «было ноль» → `HX-Location` (D-05).

### Pitfall 7: оптимистичный чекбокс тумблера
Браузер переключает `checked` до ответа; отказ оставит экран неверным. Решение Фаз 9 (D-13/D-16) — фрагмент всегда отражает сервер, `hx-sync="this:drop"`.

### Pitfall 8: `_SYNC_IN_FLIGHT` и ранний `return`
`accounts_sync_groups` освобождает заявку в `finally`. `return await respond(...)` внутри `try` корректен, а сборка ответа до входа в `try` — нет.

### Pitfall 9: `asyncio.sleep(5)` в `accounts_connect_max_start`
Запрос длится ≥5 с, поэтому `hx-disabled-elt`/индикатор обязательны. Поле телефона при `reportValidityOfForms: true` и `required` не даст отправить пустое, и 422 достижим пробелами (`.strip()`) или без `required`. Тест 422 шлёт `phone="   "`.

### Pitfall 10: смещённый курсор после фрагментного тумблера под фильтром
См. D-11. Сентинел в `schedules/list.html:61` и `partial_cards.html:7` обязан меняться синхронно (гейт идентичности).

### Pitfall 11: `-p no:randomly` ничего не отключает
`pytest-randomly` в окружении не установлен (`uv pip list` — нет) [VERIFIED]. Флаг безвреден, команды Фазы 10 можно переиспользовать дословно, но порядок тестов и так детерминирован.

## Code Examples

### Третий выход (иллюстрация; имена — на усмотрение, D-09)
```python
# Source: форма снята с app/pages/htmx.py:110-170 (VERIFIED); хост — CITED yookassa.ru docs
from urllib.parse import urlsplit

HX_REDIRECT_HEADER = "HX-Redirect"
YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})  # [CITED] примеры docs; UAT фиксирует факт

def _yookassa_confirmation_url(value: str) -> str:
    parts = urlsplit(value)
    if (parts.scheme != "https" or parts.hostname not in YOOKASSA_CONFIRMATION_HOSTS
            or parts.port is not None or parts.username or parts.password
            or not value.isascii() or any(ord(c) < 0x20 or ord(c) == 0x7F for c in value)):
        raise ValueError("адрес подтверждения оплаты вне закрытого множества хостов")
    return value

async def respond_external(request, *, url: str, fallback: str, fallback_notice: str) -> Response:
    if not is_htmx(request):
        return RedirectResponse(url=url, status_code=302)         # путь без JS — как сегодня
    try:
        checked = _yookassa_confirmation_url(url)
    except ValueError:
        logger.error("payment_confirmation_url_rejected", host=urlsplit(url).hostname)
        return await respond(request, redirect=fallback, notice=fallback_notice)
    return Response(status_code=204, headers={HX_REDIRECT_HEADER: checked})
```
Вызов в `subscribe_to_plan` (`billing.py:352` сегодня: `return RedirectResponse(url=result["confirmation_url"], status_code=302)`): `respond_external(request, url=result["confirmation_url"], fallback="/billing", fallback_notice=notices.PAYMENT_FAILED)`. Константа `PAYMENT_FAILED = "payment_failed"` [VERIFIED: app/pages/notices.py:95]. В `htmx.py` нет логгера; импорт `structlog`-логгера проекта — `[ASSUMED]`, сверить с `app/pages/billing.py`.

### Тройная пара оплаты (форма из CONTEXT §specifics)
```python
# без заголовка → 302 на confirmation_url; с HX-Request → 204 + HX-Redirect;
# чужой хост → нет HX-Redirect, 204 + HX-Location на /billing?notice=payment_failed
assert r.status_code == 204 and r.headers["HX-Redirect"] == CONFIRMATION_URL
assert "HX-Location" not in r.headers and r.content == b""
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| htmx 1.x: `HX-Retarget`/своп ошибок через `htmx:beforeSwap` | htmx 2.x: `responseHandling` решает своп по коду | htmx 2.0 | своп 422 — только правилом (Находка B) |
| `selfRequestsOnly` по умолчанию `false` (1.9.x) | `true` по умолчанию в 2.x | htmx 2.0 [CITED: htmx.org/reference — «defaults to `true`»] | внешний переход только `HX-Redirect` |
| `?result=` частный реестр | `?notice=` закрытый реестр | Фаза 8 → Фаза 11 (D-10) | четвёртая копия снимается |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | При создании платежа без `payment_method_data` `confirmation_url` всегда на `yoomoney.ru`; партнёрские страницы открываются уже с неё | Находка C | htmx-оплата падает в `PAYMENT_FAILED` у части пользователей; снимается UAT критерия 2 |
| A2 | `yookassa.ru` не бывает хостом `confirmation_url` | Находка C | фикстуры/множество расходятся с фактом |
| A3 | Back после `HX-Location`/`HX-Push-Url` при `historyCacheSize:0` делает полный GET, POST не повторяется | Паттерн 3 | UAT-пункт 7 красный |
| A4 | `form.submit()` из Alpine обходит htmx | Anti-Patterns | тумблер уйдёт полной навигацией |
| A5 | Варианты закрытия стока T-07-13 (неограниченные строковые алиасы / обработчик `RequestValidationError`) | Находка B | повторное открытие InfoDisclosure/XSS-стока |
| A6 | Логгер проекта импортируем в `htmx.py` без цикла импортов | Code Examples | порядок импортов (ср. отложенные импорты `htmx.py:211-221`) |

## Open Questions (RESOLVED)

> Разрешения дописаны при ревизии 1 планирования (2026-09-14). Находки и рекомендации выше не
> переписаны; каждое разрешение называет план и задачу, которые его исполняют (нумерация планов —
> ревизии 1: 13 планов).

1. **Своп на 422: чья подпись?**
   - What we know: без `"swap": true` FORM-08 невыполним без нового JS; запись T-07-13 разрешает возврат ровно с первым авторским 422.
   - What's unclear: D-06 предполагал заголовки; CONTEXT называет механизм «на усмотрение, не расширяя шесть ключей» — значение не ключ.
   - Recommendation: планировщик берёт `swap:true` в пределах усмотрения; `11-SECURITY` переоткрывает T-07-13 с новым смягчением; при сомнении — вопрос владельцу одной строкой до волны 1.
   - **RESOLVED — решение оркестратора планирования 2026-09-14, владельцу НЕ эскалировалось.** Основание: D-06 принят «по умолчанию» (делегирован владельцем), а §Claude's Discretion `11-CONTEXT.md` прямо отдаёт планировщику «механизм перерисовки формы на 422: … или иное, не расширяющее шесть ключей конфигурации (D-03 Фазы 7)»; `"swap": true` — значение существующего правила, а не седьмой ключ. Проверка владельцем «до волны 1», предложенная рекомендацией, не проводилась ПО ЭТОМУ РЕШЕНИЮ, а не по пропуску. Исполнение: план `11-05`, задача 1 — смягчение T-07-13 ОТДЕЛЬНЫМ планом до свопа (обработчик `RequestValidationError`, ветвь htmx только у обработчиков пакета `app.pages`, JSON-API `app/routes/` байт-в-байт прежний — D-07); план `11-06`, задача 2 — своп правилу 422 одним коммитом с первым авторским 422 (сохранение профиля) и датированное добавление к записи `07-05/T-07-13` в `07-SECURITY.md`. Перечень D-16 — план `11-05`, задача 2, с нулём записей.
2. **Асимметрия проверки хоста.** D-09 проверяет адрес только на htmx-пути; путь 302 уводит на любой адрес из ответа SDK, как сегодня. Правило границы («не меняем, ЧТО делает действие») говорит в пользу асимметрии. Recommendation: записать асимметрию в `SAFE_BY_NAME`-обосновании; источник адреса — ответ SDK по TLS, не ввод пользователя.
   - **RESOLVED — план `11-09`, задача 1:** асимметрия принята по рекомендации; основание записывается в запись `SAFE_BY_NAME` для `redirect_external` (источник — ответ SDK по TLS; правило границы фазы), а истина плана утверждает, что путь без htmx хост не проверяет.
3. **Где множество хостов.** `app/pages/htmx.py` (рядом с проверкой) против `app/config.py` (настраиваемо). Recommendation: константа в `htmx.py`; настройка открыла бы подмену через окружение, а ценность проверки — в закрытости.
   - **RESOLVED — план `11-09`, задача 1:** `YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})` константой в `app/pages/htmx.py`; запрет плана — множество в настройки окружения не выносится. Фактический хост подтверждает ручной UAT критерия 2 до слияния (допущение A1).
4. **`ScheduleIdPath = IdPath` (`schedules.py:93`) и GET-потребители `IdPath`.** Снятие границ с общего алиаса затронуло бы GET-маршруты вне D-07. Recommendation: новый алиас для POST, `IdPath` не менять.
   - **RESOLVED — план `11-02`, задача 1:** POST-псевдонимы `PostIdPath`, `PostIdForm`, `OptionalPostIdForm` заводятся рядом с неизменными `IdPath`/`IdForm`/`OptionalIdForm`; правило каталога допускает неограниченный псевдоним только на POST (синтетический GET на нём краснеет).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | все команды | ✓ | 0.12.1 | — |
| Python | суита | ✓ | 3.12.13 | — |
| pytest / pytest-asyncio / httpx | суита | ✓ | 9.0.2 / 1.3.0 / 0.28.1 | — |
| pytest-randomly | `-p no:randomly` | ✗ | — | флаг безвреден (Pitfall 11) |
| тестовый ключ ЮKassa + браузер | UAT критерия 2 | не проверялось | — | ручной UAT владельца |
| браузер (Chrome) | UAT пункты 5, 7, прокрутка | вне стенда | — | ручной UAT |

**Missing dependencies with no fallback:** нет для машинной части. Ручная часть требует человека.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0, httpx `AsyncClient`, in-memory SQLite |
| Config file | `[tool.pytest]` в `pyproject.toml` отсутствует; фикстуры `tests/conftest.py` (`client`, `authed_client`, `admin_client`, `htmx_client` `:70`) |
| Quick run command | `uv run pytest tests/test_pages/test_htmx_gates.py -q` (сегодня `43 passed` за 18.9 с) |
| Разметочные гейты | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q` (сегодня `77 passed`, 3.5 с) |
| Компоненты | `uv run pytest tests/test_templates/test_components.py -q -p no:randomly` (сегодня `90 passed`, 13.5 с) |
| Full suite command | `uv run pytest tests/ -q` (без исключения `tests/test_planning/`; последняя известная длительность ~38 мин, `3182 passed` в Фазе 10) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FORM-03 | 9 обработчиков: htmx → 200 фрагмент по `id`, без `<!DOCTYPE`, OOB-счётчик/notice; без htmx → 302 | integration | `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_schedules_list.py tests/test_pages/test_admin_panel.py tests/test_pages/test_ads_editor.py -q` | ✅ файлы есть, пары ❌ Wave 0 |
| FORM-03 | счёт `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 3→12, `NOT_YET_CONVERTED_COUNT` 26→14 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q` | ✅ (числа двигаются) |
| FORM-03 | цели свопа существуют, `x-data`-узел не цель, `id` OOB | gate | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q` | ✅ (пересчёт констант) |
| FORM-04 | `retry_sync`, `sync_groups`, исходы расписаний/оплаты/админки → 204 + `HX-Location`, тела нет | integration | `uv run pytest tests/test_routes/test_sync_groups.py tests/test_pages/test_hx_location_destinations.py -q` | ✅, случаи ❌ Wave 0 |
| FORM-05 | 302 / 204+`HX-Redirect` / чужой хост → `HX-Location` `/billing?notice=payment_failed`; `HX_HEADER_WRITES`=3; `SAFE_BY_NAME` 2 | integration + gate | `uv run pytest tests/test_pages/test_billing_subscription.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_htmx_gates.py -q -k "subscribe or redirect or header_write"` | ✅ файлы, тесты ❌ Wave 0 |
| FORM-05 | переход в ЮKassa на тестовом ключе, фактический хост | **manual-only** | — (внешний сервис, реальный ключ) | UAT |
| FORM-07 | создание: фрагмент карточки (раскрытой) для `beforeend` в `#<id data-sched-list>` + OOB счётчика; «было ноль» → 204 `HX-Location` `/ads/{id}/edit?sched=N#sched-N` | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -q -k create` | ❌ Wave 0 |
| FORM-07 | позиция прокрутки не теряется | **manual-only** | — (браузер) | UAT |
| FORM-08 | профиль: неверный пояс → 422, форма с выбранным значением, без `<!DOCTYPE`; MAX: `phone="   "` → 422 с эхо; правило 422 `swap:true`; `SERVER_SIDE_VALIDATION_RESPONSES` = новое число | integration + gate | `uv run pytest tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_shell.py -q` + профильный/MAX-модуль | ❌ Wave 0 (утверждение `swap is False` переписывается) |
| FORM-08 | сток T-07-13: на htmx-пути страничных POST нет 422 умолчания FastAPI (нечисловой id, пропущенное поле) | integration | параметризованный тест по POST-маршрутам фазы | ❌ Wave 0 |
| FORM-10 | вхождений `HX-Retarget`/`HX-Reswap` в `app/` == записей перечня (ожидаемо 0) | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k retarget` | ❌ Wave 0 |
| GATE-02 | обход: число пар == константе, у каждого переведённого обработчика ≥1 пара, существующие 302 не удалены | gate + parametrized | `uv run pytest tests/test_pages/<модуль пар>.py -q` | ❌ Wave 0 |
| D-07 (окно 51) | `VALIDATION_REFUSAL_DIVERGENCES_DECLARED` 23→0; id вне диапазона ≡ «нет/чужое» | gate + integration | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k validation_refusal` | ✅ (реестр пустеет) |
| D-08 (окно 63) | `OWN_RESPONSE_EXITS_DECLARED` 9→12 | gate | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k own_response` | ✅ |
| D-10 | 0 вхождений `?result=` в `app/`; коды в `notices.py` с дословными текстами | gate | `uv run pytest tests/test_pages/test_notices_surface.py tests/test_pages/test_htmx_gates.py -q -k "result or notice"` | ❌ Wave 0 (гейт) |
| D-11 | keyset `/schedules/partial`: тумблер под фильтром не теряет строку | integration | `uv run pytest tests/test_pages/test_schedules_list.py -q -k cursor` | ❌ Wave 0 |
| D-13 | `HX-Push-Url: /ads/{id}/edit` на создании после переезда на `respond()` | integration | `uv run pytest tests/test_pages/test_ads_editor.py -q -k push` | ❌/✅ сверить |
| Критерий 5 | Alpine после свапа, утечка слушателей, панели | **manual-only** | — (UAT пункт 5) | UAT |
| UAT п.7 | Back/F5 не повторяют POST | **manual-only** | — | UAT |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_pages/test_htmx_gates.py -q` + модуль раздела задачи
- **Per wave merge:** три команды Фазы 10 + модуль пар + `tests/test_pages/test_htmx_response_contract.py tests/test_pages/test_shell.py`
- **Phase gate:** `uv run pytest tests/ -q` зелёная до `/gsd-verify-work`

### Wave 0 Gaps
- [ ] модуль пар GATE-02 (реестр случаев, AST-обход, константа, замыкание)
- [ ] тесты третьего выхода в `tests/test_pages/test_htmx_response_layer.py` (хост, схема, суффикс, userinfo, порт)
- [ ] гейт перечня `HX-Retarget`/`HX-Reswap` (FORM-10)
- [ ] гейт `?result=` == 0 (D-10)
- [ ] переписать `test_validation_rule_carries_both_swap_and_error` и литерал `test_shell.py:1300` вместе с правилом
- [ ] тест отсутствия 422 умолчания на htmx-пути страничных POST (T-07-13)
- [ ] фикстура `CONFIRMATION_URL` на документированном хосте для htmx-пар оплаты

## Security Domain

`security_enforcement: true`, ASVS L1, `security_block_on: high`; изъятие Фазы 10 владелец отклонил (`10-SECURITY.md`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | нет (не меняется) | `get_user_from_cookie` |
| V3 Session Management | нет | cookie `samesite=lax` (GATE-08) |
| V4 Access Control | да | владение записью до действия; id вне диапазона ≡ «нет/чужое» (D-07); `is_same_origin` (V4.2.2) до БД |
| V5 Input Validation | да | граница id до `select`; закрытые множества (`VALID_TIMEZONES`, хосты ЮKassa); эхо ввода только через автоэкранирование Jinja |
| V6 Cryptography | нет | — |
| V14 / Output | да | `|safe` и `Markup(` = 0 (GATE-07); AST-гейт правого операнда `HX-*` |

### Known Threat Patterns for stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| открытый редирект через `HX-Redirect` | Spoofing | закрытое множество хостов, точное сравнение `hostname`, `https`; запись `SAFE_BY_NAME` |
| инъекция заголовка / latin-1 500 | Tampering / DoS | отказ на управляющих и не-ASCII (как `_local_path`) |
| своп тела 422 умолчания фреймворка с эхо ввода (T-07-13) | InfoDisclosure / XSS | авторский фрагмент + устранение 422 умолчания на htmx-пути (Находка B) |
| переполнение целого столбца (500) | DoS | граница id внутри обработчика до БД |
| CSRF на изменяющих POST | Tampering | `is_same_origin`, голый 403 (D-08) |
| двойная оплата | Tampering | потолок PAY-01 + запрет `hx-sync` `queue` (PAY-02) |
| эхо введённого пояса/телефона в 422 | XSS | только автоэкранирование, без `|safe` |

## Sources

### Primary (HIGH confidence)
- `app/static/js/htmx.min.js` (2.0.10, вендоренный) — функции `Vn` (порядок `HX-Location`→`HX-Redirect`→`responseHandling`→`HX-Retarget`/`HX-Reswap`), `Mn` (приоритет `HX-Push-Url`), `Bn`, `Ln` (`selfRequestsOnly`)
- Код проекта, прочитанный этой сессией: `app/pages/htmx.py`, `billing.py:255-352`, `profile.py`, `accounts.py:535-830`, `schedules.py:758-810`, `admin.py:1138-1176`, `identifiers.py:97-103`, `services/payment_service.py:690-810`, `main.py:219-248`, шаблоны (строки выше), `tests/test_pages/test_htmx_gates.py`, `test_htmx_response_contract.py`, `tests/conftest.py`
- Прогоны: три гейтовых модуля (43/77/90 passed), AST-замер 302

### Secondary (MEDIUM confidence)
- [yookassa.ru — Процесс проведения платежа](https://yookassa.ru/developers/payment-acceptance/getting-started/payment-process) — «на странице ЮKassa или ее партнера», пример `yoomoney.ru/api-pages/v2/payment-confirm/epl`
- [yookassa.ru — Тестирование](https://yookassa.ru/developers/payment-acceptance/testing-and-going-live/testing) — пример `confirmation_url` в тестовом режиме
- [htmx.org/reference](https://htmx.org/reference/) — описания `HX-Redirect`, `HX-Location`, `HX-Push-Url`, `HX-Retarget`, `HX-Reswap`, `selfRequestsOnly`

### Tertiary (LOW/MEDIUM, через WebSearch)
- Страницы сценариев ЮKassa: [T-Pay](https://yookassa.ru/developers/payment-acceptance/integration-scenarios/manual-integration/other/tinkoff-bank), [СБП](https://yookassa.ru/developers/payment-acceptance/integration-scenarios/manual-integration/other/sbp), [Наличные](https://yookassa.ru/developers/payment-acceptance/integration-scenarios/manual-integration/other/cash), [ЮMoney](https://yookassa.ru/developers/payment-acceptance/integration-scenarios/manual-integration/yoo-money), [Электронный сертификат](https://yookassa.ru/developers/payment-acceptance/integration-scenarios/manual-integration/other/electronic-certificate/ready-made-payment-form) — все примеры на `yoomoney.ru`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — ничего нового, версии сняты с окружения
- Architecture / рантайм htmx: HIGH — снято с вендоренного файла, а не с памяти
- Хосты ЮKassa: MEDIUM — документация явно не закрывает множество; UAT обязателен
- Pitfalls: HIGH — из кода и записанных решений прошлых фаз

**Research date:** 2026-09-14
**Valid until:** 2026-10-14 (код стабилен; хосты ЮKassa перепроверить UAT)
