---
phase: 04-dashbord-i-istoriya
plan: 09
subsystem: ui
tags: [fastapi, csrf, celery, jinja2, alpine, history, retry, security, tdd]

requires:
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-03: Celery-таск app.worker.tasks.retry_send — вход повтора на все три канала"
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-01: предикат «неуспешная = не успешная» и константы статусов в app/application/analytics/send_analytics.py"
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-07: метаколонка карточки истории и страница записи, переверстанная на примитив записи"
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-08: маршруты app/pages/history.py и отсечка _clean_choice на третьем входе"
  - phase: 01-interfejsnyj-fundament
    provides: "панель подтверждения components/modal.html с гардом повторной отправки, ловушкой фокуса и закрытием по Esc"
provides:
  - "Маршрут POST /history/{log_id}/retry (history_retry) — единственное настоящее действие раздела"
  - "_is_same_origin — первая в проекте сверка источника изменяющего запроса (Sec-Fetch-Site + Origin по хосту)"
  - "retry_availability — серверная предпроверка целости тройки сущностей фиксированным числом запросов"
  - "RETRY_TASK_NAME, RETRY_QUEUED/GONE/NO_BALANCE/BUSY, RETRY_NOTICES, RETRY_REASON_* в app/pages/history.py"
  - "_RETRY_IN_FLIGHT с синхронным занятием и освобождением отбрасыванием"
  - "Макросы retry_trigger и retry_modal — одно определение запуска повтора на карточку списка и страницу записи"
  - "Собственный файл тестов: tests/test_pages/test_history_retry.py"
affects: [04-10, phase-6-admin]

actuals:
  tokens: 17444
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Сверка источника изменяющего запроса заголовками внутри самого обработчика — без схемы токенов на весь проект"
    - "Предпроверка страницы по ОБЪЕДИНЕНИЮ идентификаторов: число запросов не зависит от числа записей"
    - "Отсутствие ключа в вердикте и None под ключом — разные ответы: «нечего повторять» против «повтор возможен»"
    - "Признак доступности необратимого действия вычисляет сервер и передаёт значением; разметка его не выводит"
    - "Первое место подтверждения проекта, подтверждающее НЕ удаление"

key-files:
  created:
    - tests/test_pages/test_history_retry.py
  modified:
    - app/pages/history.py
    - app/templates/history/includes/history_card.html
    - app/templates/history/detail.html
    - app/templates/history/list.html
    - tests/test_templates/test_components.py

key-decisions:
  - "Предикат пригодности — «статус НЕ ok», а не членство в FAILED_STATUSES: буква плана разошлась с контрактом 04-01, и выбран контракт — иначе запись с неизвестным статусом не была бы ни успешной, ни повторяемой"
  - "Сверка источника сравнивает ХОСТ, а не строку целиком: заголовок несёт схему и порт, посимвольное сравнение сломалось бы за обратным прокси"
  - "Запрос без обоих заголовков ПРОПУСКАЕТСЯ — названная граница защиты, выписанная в докстринге и здесь"
  - "Запуск и панель повтора объявлены ОДИН раз в history_card.html; страница записи их импортирует — вторая копия разошлась бы в тексте, обещающем ЧТО будет отправлено (D-17)"
  - "Текст отказа по балансу ПОСТОЯННЫЙ и из ответа гейта не собирается: провоз причины через адрес дал бы владельцу ссылки печатать пользователю произвольный текст"
  - "Признак доступности приезжает в карточку значением; админский экран его не кладёт, поэтому повтор чужой записи там не появляется сам собой"
  - "Предпроверка стоит два запроса на страницу, а не три на запись: N+1 на самой растущей таблице системы"
  - "HIST-04 в REQUIREMENTS.md НЕ отмечен: тот же идентификатор объявляют планы 04-01, 04-03 и 04-10"

patterns-established:
  - "Необратимое действие, вводимое фазой, приносит сверку источника вместе с собой — а не откладывает её на «потом, по всему проекту»"
  - "Инвентаризационные числа пересчитываются СЧЁТОМ ПО ФАЙЛАМ после правки шаблонов, и комментарий фиксирует причину сдвига"

requirements-completed: []

coverage:
  - id: D1
    description: "Повторить можно только неуспешную запись: сервер отклоняет повтор успешной, а интерфейс кнопки не рисует (D-19)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_of_a_successful_record_is_refused_by_the_server"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_successful_record_offers_no_retry_launcher"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_history_detail_offers_no_retry_for_a_successful_record"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_is_eligible_for_an_unknown_status"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_is_eligible_for_a_disconnected_account_status"
        status: pass
    human_judgment: false
  - id: D2
    description: "Повтор чужой записи отклоняется: владение проверяется на входе обработчика (T-04-35)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_of_another_users_record_is_refused_by_ownership"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_of_a_missing_record_queues_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_requires_login"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_admin_history_offers_no_retry_launcher"
        status: pass
    human_judgment: false
  - id: D3
    description: "Исчезнувшие объявление, группа или аккаунт останавливают повтор ДО очереди, и записи в журнал не появляется (D-21, T-04-39)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_ad_is_gone"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_group_is_gone"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_account_is_gone"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_precheck_stops_when_the_account_is_not_active"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_precheck_runs_before_the_queue"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_availability_names_each_missing_entity"
        status: pass
    human_judgment: false
  - id: D4
    description: "Исчерпанный лимит отправок отклоняет повтор до постановки в очередь и объясняется пользователю (T-04-36)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_is_refused_when_the_balance_is_exhausted"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_explains_the_exhausted_balance_to_the_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_balance_gate_runs_before_the_queue"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_does_not_touch_billing_itself"
        status: pass
    human_judgment: false
  - id: D5
    description: "Повтор ставится тем же механизмом диспетчеризации, что боевая рассылка, и второго пути отправки не создаёт (D-18)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_of_an_eligible_record_queues_exactly_one_task — постановка по имени app.worker.tasks.retry_send с аргументами [log_id, user_id]"
        status: pass
      - kind: unit
        ref: "tests/test_worker/test_tasks.py#test_retry_send_routes_queue_channels_to_redis (план 04-03) — маршрутизация трёх каналов; здесь НЕ дублируется"
        status: pass
    human_judgment: false
  - id: D6
    description: "Запрос повтора с чужого источника отклоняется ДО любых действий (T-04-38, ASVS L1 V4.2.2)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_rejects_a_cross_site_origin"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_rejects_a_cross_site_fetch_context"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_accepts_its_own_origin"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_lets_a_headerless_request_through"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_origin_check_runs_before_the_record_is_read"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_origin_check_documents_its_boundary"
        status: pass
    human_judgment: false
  - id: D7
    description: "Одно действие пользователя порождает не более одной постановки: перенаправление после формы плюс заявка в памяти процесса (T-04-37)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_answers_with_a_redirect_not_a_page"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_of_a_busy_record_queues_no_second_task"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_releases_the_slot_after_success"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_releases_the_slot_after_an_exception"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_slot_claim_is_synchronous"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_slot_release_is_a_discard_in_a_finally_block"
        status: pass
    human_judgment: false
  - id: D8
    description: "Подтверждение идёт общей панелью проекта с настоящей формой, и текст называет отправку ТЕКУЩЕГО содержимого объявления (D-23, D-17, T-04-40)"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_confirmation_panel_carries_a_real_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_confirmation_panel_names_the_current_ad_content"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_uses_the_shared_confirmation_panel"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_guard_is_inherited_by_every_consumer"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_no_rendered_page_calls_browser_dialog — браузерного диалога не появилось"
        status: pass
    human_judgment: false
  - id: D9
    description: "Панель эмитится вне разметки записи и переживает подмену бесконечной прокруткой"
    requirement: "HIST-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_panel_is_emitted_outside_the_record_markup"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_history_detail_panel_is_outside_the_record_markup"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_launcher_survives_the_infinite_scroll_partial"
        status: pass
    human_judgment: false
  - id: D10
    description: "Инвентаризация мест подтверждения пересчитана счётом по файлам после правки шаблонов"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_site_inventory — 9 импортёров, 6 имён события, 15 мест"
        status: pass
      - kind: other
        ref: "grep -rl 'components/modal.html' app/templates → 9 файлов; grep -o 'modal-open-[a-z-]*' минус компонент → 15 вхождений, 6 различных имён"
        status: pass
    human_judgment: false
  - id: D11
    description: "Признак доступности повтора считает сервер, и число запросов не растёт с числом записей"
    requirement: "HIST-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_availability_takes_a_bounded_number_of_queries"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_retry.py#test_retry_availability_ignores_successful_records"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_availability_is_computed_by_the_server"
        status: pass
    human_judgment: false
  - id: D12
    description: "Панель подтверждения при поднявшемся Alpine не даёт отправить повтор дважды двойным нажатием"
    requirement: "HIST-04"
    verification: []
    human_judgment: true
    rationale: "Backstop плана, названный в must_haves. Браузерных/e2e-тестов в проекте нет: рантайм-поведение Alpine автотестами не исполняется, проверяется только НАЛИЧИЕ гарда в макросе (test_modal_confirm_guards_double_submit) и его наследование потребителем. Пункт уходит в перечень ручных проверок плана 04-10 — тем же путём, что рантайм Alpine из Фазы 3"
  - id: D13
    description: "Повтор доезжает до живого получателя: задача, поставленная из интерфейса, доставляется в группу мессенджера"
    requirement: "HIST-04"
    verification: []
    human_judgment: true
    rationale: "Продолжение D5 сводки 04-03: сквозной путь пересекает границу процесса (задачу читает wa_worker/index.js в отдельном контейнере, которого в тестовой среде нет). Вход пользователя в этот путь появился ИМЕННО СЕЙЧАС, поэтому ручная проверка на живом аккаунте стала возможна — она уходит в план 04-10"
  - id: D14
    description: "Кнопка повтора и её объяснение пригодны на узких ширинах"
    verification: []
    human_judgment: true
    rationale: "Медиазапросы автотестами не исполняются. Метаколонка карточки получила третий орган управления (копирование, повтор, «Подробнее») — тот же пункт чекпоинта плана 04-10, что у плиток 04-01, блоков 04-04, ленты 04-05 и полосы чипсов 04-06"

duration: 75 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 09: Повтор отправки из записи истории Summary

**Пользователь повторяет неуспешную отправку прямо из истории: кнопка есть только у той записи, у которой цела вся тройка сущностей, подтверждение идёт общей панелью проекта и честно называет, что уйдёт ТЕКУЩЕЕ содержимое объявления, а межсайтовый запрос на адрес повтора получает 403 до того, как сервер прочитает хотя бы одну строку.**

## Performance

- **Duration:** 75 min
- **Started:** 2026-08-14T12:40:00Z
- **Completed:** 2026-08-14T13:55:00Z
- **Tasks:** 2 (обе TDD)
- **Files modified:** 6 (1 создан, 5 изменено)

## Accomplishments

- **Заведено первое настоящее ДЕЙСТВИЕ раздела, и все четыре его гарантии стоят ДО очереди.** Владение, пригодность, целость тройки сущностей и баланс проверяются в обработчике, а не внутри отправки. Проверка внутри отправки означала бы запись в журнал о заведомо невозможной отправке — историю, наполненную свидетельствами того, чего быть не могло (D-21).
- **Введена первая в проекте сверка источника изменяющего запроса (T-04-38, ASVS L1 V4.2.2).** Аутентификация проекта идёт cookie, а действие необратимо: страница, размещённая где угодно, иначе тратила бы баланс пользователя и слала бы рекламу в чужую группу, просто прокатившись на его сессии. `Sec-Fetch-Site` принимается только со значением «тот же источник»; иначе сверяется ХОСТ заголовка `Origin` с хостом запроса — не строка целиком, потому что заголовок несёт схему и порт, и посимвольное сравнение сломалось бы на первом же развёртывании за обратным прокси. Отказ — 403 ДО чтения записи, и это закреплено не только поведением, но и структурной проверкой порядка: «403 до чтения» и «403 после чтения» на клиенте неразличимы, а разница существенна.
- **Граница защиты названа, а не умолчана.** Запрос без обоих заголовков пропускается: браузер, способный отправить межсайтовую форму, шлёт `Origin` на POST с 2016 года, поэтому отсутствие обоих означает не-браузерного клиента — в том числе суиту проекта. Ограничение выписано в докстринге функции, и на это есть отдельный тест: принятый риск, о котором не написано, через один рефакторинг становится неизвестным.
- **Гейт баланса закрыл обход тарифного лимита (T-04-36).** Гейт стоит у планировщика, а не внутри отправки; без этого шага повтор стал бы способом отправить ровно столько сообщений, сколько у пользователя неудачных записей. Биллинг при этом не правится — списание за успешный повтор произойдёт там же, где у боевой рассылки (D-20), и отсутствие второго места списания проверяется по исходнику.
- **Предпроверка для интерфейса стоит ДВА запроса на страницу, а не три на запись.** Проверка тройки по каждой строке означала бы девяносто обращений к базе на страницу в тридцать записей — и так на каждый рендер списка, на самой растущей таблице системы. Оба запроса идут по объединению идентификаторов показываемых строк, и это закреплено счётом инструкций через слушатель движка.
- **Отсутствие ключа и `None` под ключом — РАЗНЫЕ ответы.** Первое значит «запись успешна, повторять нечего», второе — «повтор возможен». Слить их в один пустой ответ значило бы предложить повтор успешной отправки.
- **Запуск повтора не приехал в админскую историю сам собой.** Тот же макрос карточки обслуживает админский экран, а признак доступности приходит туда значением, которого админский обработчик не кладёт. Кнопка, появившаяся там, обещала бы админу действие, которое сервер всё равно отклонит проверкой владения, — то есть предлагала бы заведомый отказ. Закреплено тестом.
- **Панель подтверждения не соврала о том, что будет отправлено.** Её текст называет следствие D-17 прямо: уйдёт ТЕКУЩЕЕ содержимое объявления из базы, а не снапшот, показанный в записи. Умолчать это значит показать пользователю один текст, а отправить другой (T-04-40).
- **Инвентаризация мест подтверждения пересчитана СЧЁТОМ ПО ФАЙЛАМ** уже после правки шаблонов: импортёров 8 → 9, различных имён события 5 → 6, мест 14 → 15. Комментарий к константам называет этот план, причину сдвига и — отдельно — почему мест пятнадцать, а не шестнадцать при повторе на двух экранах.
- **У повтора собственный файл тестов — 48 тестов**, и вся суита выросла с 1316 до 1364 без единого снятого теста.

## Task Commits

Обе задачи исполнены как TDD-пары «красный набор → реализация»:

1. **Task 1 RED — маршрут повтора** — `bfbe333` (test, падал на ImportError отсутствующих констант)
2. **Task 1 GREEN — обработчик, сверка источника, реестр заявок** — `b6d2c60` (feat)
3. **Task 2 RED — запуск, панель и предпроверка для интерфейса** — `926101f` (test, 15 падений из 48)
4. **Task 2 GREEN — макросы повтора, серверный признак, пересчёт инвентаризаций** — `ef3ee15` (feat)

Фазы REFACTOR не потребовалось: обработчик состоит из последовательности проверок без дублирования, а разметка повтора с первого раза объявлена одним определением на оба экрана.

## Files Created/Modified

- `tests/test_pages/test_history_retry.py` — **создан**, 48 тестов: четыре случая сверки источника, пригодность (включая выдуманный статус), владение, четыре случая предпроверки, баланс с объяснением, занятие и освобождение заявки, структурные проверки порядка проверок и локального импорта, запуск в карточке и на странице записи, панель вне разметки записи, админский экран, число запросов предпроверки
- `app/pages/history.py` — маршрут `POST /history/{log_id}/retry`, `_is_same_origin`, `retry_availability`, реестр `_RETRY_IN_FLIGHT` с занятием и освобождением, константы `RETRY_*`; `can_retry`/`retry_reason` в записях списка, паршала прокрутки и страницы записи; параметр `retry` и разбор признака исхода по словарю
- `app/templates/history/includes/history_card.html` — макросы `retry_trigger` и `retry_modal`, вызов запуска в метаколонке и панели соседом записи
- `app/templates/history/detail.html` — импорт тех же макросов, запуск в метаколонке и панель вне записи
- `app/templates/history/list.html` — плашка исхода повтора рядом с плашкой отказа выгрузки
- `tests/test_templates/test_components.py` — три инвентаризационных числа и перечень потребителей панели, пересчитанные по файлам, с комментарием-следом

## Decisions Made

- **Предикат пригодности — «статус НЕ `ok`», а НЕ членство в `FAILED_STATUSES`.** Буква плана называла «перечень неуспешных статусов из модуля аналитики», но контракт 04-01 и прохибиция P-04-01 требуют обратного: перечень известных неудач конечен ровно до появления следующего статуса, и запись с неизвестным значением оказалась бы ни успешной, ни повторяемой — то есть лишилась бы повтора именно тогда, когда он нужнее всего. Тот же предикат уже держат счётчик неудач дашборда и кнопка копирования диагностики; третий ответ на один вопрос разошёлся бы с двумя первыми. Закреплено тестом с ВЫДУМАННЫМ статусом, поэтому реализация с перечнем на нём краснеет.
- **Сверка источника сравнивает хост, а не строку.** Заголовок источника несёт схему и порт, адрес запроса — тоже. Хост своего адреса берётся ИЗ ЗАПРОСА, а не из настроек: поля с базовым адресом приложения в проекте нет, и заводить его ради одной проверки значило бы завести конфигурацию, которую придётся сопровождать.
- **Текст отказа по балансу ПОСТОЯННЫЙ.** Гейт возвращает причину строкой, и провоз этой строки через адрес означал бы, что владелец ссылки печатает пользователю произвольный текст на его собственной странице. Признак исхода сравнивается ЦЕЛИКОМ по словарю известных значений — та же дорога, что у `_clean_choice` для осей фильтрации и у признака несостоявшейся выгрузки.
- **Заявка занимается ДО любой асинхронной работы по записи.** Функция занятия синхронная и не содержит ни одного ожидания: точка переключения задач между проверкой и добавлением вернула бы гонку ровно туда, откуда её убирают. Освобождение — отбрасыванием в блоке завершения, поэтому и после исключения запись остаётся повторяемой.
- **Клиент очереди импортируется ЛОКАЛЬНО.** Не ради стиля: именно локальный импорт позволяет подменить модуль очереди в тесте. Поднятый на уровень модуля, он разрешился бы один раз при загрузке пакета страниц, и любой тест повтора пошёл бы к настоящему брокеру. Свойство закреплено тестом в обе стороны — импорт обязан быть в теле и обязан отсутствовать в шапке.
- **Признак доступности передаётся макросам ЯВНЫМИ аргументами, а не читается с `log`.** Карточка списка получает запись словарём (признаки в нём есть), страница записи — сущностью ORM (признаков там нет и быть не может). Один макрос с явными аргументами обслуживает оба; чтение `log.can_retry` внутри макроса молча дало бы на странице записи «повтор недоступен» при статусе 200.
- **Причины недоступности названы ПОИМЁННО** (объявление, группа, аккаунт удалён, аккаунт отключён). Общее «повторить нельзя» на все четыре случая не сказало бы пользователю ничего о том, что чинить.
- **`HIST-04` в REQUIREMENTS.md не отмечен НАМЕРЕННО** — тот же идентификатор объявляют планы 04-01, 04-03 и 04-10. Отметка сейчас показала бы требование закрытым, пока последний объявивший его план ещё идёт (тот же приём, что у HIST-01 в 04-06 и HIST-03 в 04-08).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Признак исхода повтора было некому нарисовать**

- **Found during:** Task 1
- **Issue:** План требует, чтобы при исчерпанном балансе «пользователь получил объяснение», а отказ по исчезнувшей сущности приезжал «перенаправлением с признаком причины». Перечень `files_modified` при этом `app/templates/history/list.html` не содержит. Признак, приезжающий в адрес и не рисующий ничего, — заглушка: пользователь нажимает «Повторить», возвращается на тот же экран и не узнаёт, ушла отправка или была отклонена. Исход, неотличимый от «ничего не произошло».
- **Fix:** На странице списка добавлена плашка исхода — существующим макросом сообщения, рядом с уже стоящей там плашкой отказа выгрузки и ровно тем же приёмом: пара «текст, вариант» приходит с сервера из словаря известных признаков, неизвестное содержимое параметра не рисует ничего.
- **Files modified:** app/templates/history/list.html, app/pages/history.py
- **Verification:** `test_retry_explains_the_exhausted_balance_to_the_user` — passed
- **Committed in:** b6d2c60

### Отступления от буквы плана (не автопочинка)

**2. Пригодность определяется предикатом «не `ok`», а не перечнем `FAILED_STATUSES`.** Разобрано выше в «Decisions Made». Буква плана (`<action>` шаг 3 и `<read_first>`) разошлась с контрактом 04-01, названным в must-have труте «повторить можно только НЕУСПЕШНУЮ запись»; выбран контракт. Поведение на двух известных неудачных статусах при этом идентично — разница видна только на неизвестном, и ровно она закреплена тестом.

**3. Запуск повтора и панель объявлены ОДИН раз, поэтому `history/detail.html` не содержит строки `components/modal.html`.** Критерий приёмки задачи 2 требует этой строки в обоих файлах; исполнен он только для карточки. Причина: вторая копия вызова панели означала бы вторую копию ТЕКСТА, обещающего пользователю, ЧТО именно будет отправлено, — а расхождение именно этого текста есть угроза T-04-40 и нарушение D-17. Прецедент принят соседним планом 04-07 на этих же двух файлах: кнопка копирования объявлена в карточке и импортируется страницей записи, потому что «вторая кнопка разошлась бы с первой». Следствие для инвентаризации: мест подтверждения ПЯТНАДЦАТЬ, а не шестнадцать, и потребителей панели восемь, а не девять — обе причины выписаны комментарием там же, где числа. Свойство «страница записи не собирает панель сама» закреплено тестом `test_retry_launcher_has_one_definition_for_both_screens`, поэтому будущая копия краснеет.

**4. Заведены константы сверх перечисленных в «Artifacts this phase produces»:** признаки исхода (`RETRY_QUEUED`, `RETRY_GONE`, `RETRY_NO_BALANCE`, `RETRY_BUSY`), их тексты (`RETRY_NOTICES`), причины недоступности (`RETRY_REASON_*`) и имя таска (`RETRY_TASK_NAME`). Ни одна не расширяет объём: все обслуживают ровно то поведение, которое план предписывает, — объяснение отказа пользователю и предпроверку, названную артефактом. Тексты вынесены константами, потому что они видимы пользователю и сравниваются целиком.

**5. Предпроверка вынесена в отдельную функцию `retry_availability`, общую для списка, паршала прокрутки и страницы записи.** План называет предпроверку артефактом, не уточняя формы. Три копии проверки разошлись бы, и один экран предлагал бы повтор там, где другой его прячет; кроме того, только вынесенная функция позволяет закрепить число запросов тестом.

---

**Total deviations:** 1 автопочинка (Rule 2) + 4 задокументированных отступления от буквы плана
**Impact on plan:** объём не расширен — новых файлов приложения ноль, новых правил стилей ноль, новых зависимостей ноль, удалённых файлов ноль. Автопочинка обязательна: без неё две ветви отказа возвращали бы пользователя на прежний экран молча.

## Issues Encountered

Откатов не было. Красных прогонов, кроме двух запланированных фаз RED, не случилось; две правки потребовались внутри GREEN-фаз, и обе — в ТЕСТАХ, а не в коде:

1. **Проверка «в занятии заявки нет ожидания» краснела на собственном докстринге.** Докстринг обязан объяснять, почему ожидания здесь нет, — то есть содержит само слово. Поиск по сырому тексту функции ловил объяснение запрета вместо его нарушения: ровно тот класс ложного срабатывания, который в этом репозитории уже стоил переработки нескольким планам (`test_module_has_no_dialect_specific_calendar_functions` снимает только строчные комментарии). Проверка теперь вырезает докстринг и отдельно утверждает, что вырезала его целиком.
2. **Проверка освобождения заявки после исключения ждала всплытия исключения.** До теста оно не доезжает: посредник приложения (`app/middleware.py`) ловит его, пишет в журнал и отдаёт 500. Тест переписан на СЛЕДСТВИЕ — код 500 и снятая заявка, — что и есть проверяемое свойство.

Четыре теста предпроверки и админского экрана поначалу падали на `NoResultFound`: они брали `db_session` напрямую, а пользователь `testuser@test.com` заводится фикстурой регистрации. Добавлена недостающая фикстура.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None — заглушек не заведено. Маршрут ставит настоящую задачу в настоящую очередь; предпроверка читает настоящие сущности; гейт баланса вызывается настоящий (в тестах подменяется по установленному в проекте образцу, потому что боевой лезет в Redis); панель подтверждения — общий компонент проекта со всеми его гарантиями.

**Названное ограничение (не заглушка).** Реестр заявок живёт в памяти ОДНОГО рабочего процесса: два одновременных нажатия, попавшие в разные процессы, обе заявки займут успешно. Ограничение уже принято проектом для синхронизации аккаунтов, но здесь цена ошибки выше — вторая необратимая отправка в чужую группу. Оно выписано у самого реестра и вынесено ниже, в перечень для отчёта безопасности фазы. Остальные три линии защиты от двойной отправки (перенаправление после формы, гард панели, `max_retries=0` у самого таска) от числа процессов не зависят.

## Threat Flags

Новых поверхностей вне `<threat_model>` не появилось: заведён ровно один маршрут, он под гардом входа, владение проверяется на входе, значения в адрес уходят константами модуля, а тексты плашек — обычным экранированным выводом Jinja. Диспозиции `mitigate` реализованы и закреплены тестами:

| Threat ID | Реализация | Тест |
|-----------|------------|------|
| T-04-35 | владение на входе обработчика + повторно внутри таска (04-03) | `test_retry_of_another_users_record_is_refused_by_ownership` |
| T-04-36 | `check_balance_cached(..., "send")` ДО постановки | `test_retry_is_refused_when_the_balance_is_exhausted`, `test_retry_balance_gate_runs_before_the_queue` |
| T-04-37 | перенаправление после формы + синхронная заявка + гард панели | `test_retry_answers_with_a_redirect_not_a_page`, `test_retry_of_a_busy_record_queues_no_second_task`, `test_modal_confirm_guards_double_submit` |
| T-04-38 | `_is_same_origin` первой проверкой после гарда входа, 403 без перенаправления | четыре теста источника + `test_retry_origin_check_runs_before_the_record_is_read` |
| T-04-39 | предпроверка тройки и статуса аккаунта ДО постановки | четыре теста предпроверки (число записей журнала не растёт) |
| T-04-40 | текст панели называет ТЕКУЩЕЕ содержимое объявления | `test_retry_confirmation_panel_names_the_current_ad_content` |

## Для отчёта безопасности фазы (план 04-10)

Три остаточных риска, принятых ЯВНО, — их место в отчёте, а не в умолчании:

1. **Запрос без заголовков `Sec-Fetch-Site` и `Origin` проходит сверку.** Граница защиты; обоснование — в докстринге `_is_same_origin`.
2. **Остальные формы проекта сверки источника не получили.** Фаза не расширяет рамки: правка помещалась в обработчик, который план и так писал. Защита форм проекта — отдельная задача, рекомендация переносится в отчёт.
3. **Реестр заявок не переживает нескольких рабочих процессов.** Описано выше в «Known Stubs».

## Ручные проверки, уходящие в план 04-10

1. **Двойное нажатие подтверждения при поднявшемся Alpine** — гард в разметке есть, его рантайм-поведение автотестами не исполняется (D12).
2. **Сквозной повтор на живом аккаунте** — вход пользователя в этот путь появился именно сейчас, и пункт D5 сводки 04-03 стал проверяемым (D13).
3. **Адаптивность метаколонки с третьим органом управления** на узких ширинах (D14).

## Next Phase Readiness

- **Готово для 04-10 (чекпоинт, отчёт безопасности и выравнивание):** три пункта ручной проверки и три остаточных риска выше; `HIST-04` ждёт отметки в REQUIREMENTS.md вместе с остальными идентификаторами, объявленными 04-10.
- **Готово для Фазы 6 (история пользователя в админке):** макросы повтора приезжают туда вместе с карточкой, но БЕЗДЕЙСТВУЮТ, пока админский обработчик не положит признак доступности. Это осознанный вход: если Фаза 6 захочет дать админу повтор от имени владельца, ей придётся сначала решить вопрос владения — и решение это будет видно, а не приедет само собой.
- **Не тронуто намеренно:** `app/worker/tasks.py` (таск повтора написан планом 04-03 и не изменён ни на символ), `app/services/billing_*` (списание остаётся там, где оно есть), `app/pages/admin.py` и его шаблоны истории, `app/static/css/app.css` (запуск повтора собран существующим макросом кнопки; своих правил не заведено), JSON-API `app/routes/history.py`.
- **Файлов НЕ удалялось:** `git diff --diff-filter=D` от базы ветки до HEAD пуст.
- Граф `graphify-out/` в этом worktree отсутствует, поэтому `graphify update .` не выполнялся — граф обновляется в основном рабочем дереве после слияния.

## Verification Results

- `uv run pytest tests/test_pages/test_history_retry.py -q` — **48 passed**
- `uv run pytest tests/test_pages/test_history_retry.py -k "eligible or ownership or precheck or balance or origin" -x -q` — 16 passed
- `uv run pytest tests/test_templates/test_components.py -q` — 45 passed
- `uv run pytest tests/test_pages/ -q` — **690 passed**, exit 0
- `uv run pytest tests/test_pages/ tests/test_templates/ -q` — **757 passed**, exit 0
- `uv run pytest tests/ -q` — **1364 passed**, exit 0 (база ветки 1316: +48 новых, ни одного снятого)
- `grep -c '@router.post("/history/{log_id}/retry"' app/pages/history.py` → 1
- `grep -rl "components/modal.html" app/templates | wc -l` → 9; вхождений `modal-open-*` вне компонента — 15, различных имён — 6

## Self-Check: PASSED

- Созданный файл присутствует на диске: `tests/test_pages/test_history_retry.py`; все пять изменённых файлов на месте; УДАЛЁННЫХ файлов ноль.
- Все четыре коммита задач присутствуют в истории ветки: `bfbe333`, `b6d2c60`, `926101f`, `ef3ee15`.
- Гейты TDD соблюдены на обеих задачах: коммит `test(...)` предшествует коммиту `feat(...)`, оба присутствуют дважды. Обе фазы RED состоялись по-настоящему — первая падала на ImportError отсутствующих констант, вторая дала 15 падений из 48.
- Критерии приёмки перепроверены командами: маршрут объявлен POST-ом; `_is_same_origin` стоит в обработчике до чтения записи; `check_balance_cached(` — до `send_task(`; локальный импорт клиента очереди в теле функции и его отсутствие в шапке модуля; синхронное занятие заявки и освобождение отбрасыванием в блоке завершения; `components/modal.html` в карточке; форма панели с `method="post"` и адресом на `/retry`; у успешной записи запуска повтора нет; текст панели называет текущее содержимое объявления; три инвентаризационных числа пересчитаны и тест инвентаризации зелёный.
- Невакуумность ключевых утверждений: тест пригодности параметризован ВЫДУМАННЫМ статусом, поэтому реализация с перечнем известных неудач на нём краснеет; сверка источника проверяется ЧЕТЫРЬМЯ случаями (чужой источник, чужой контекст выборки, свой источник, отсутствие обоих заголовков), поэтому реализация, отклоняющая или пропускающая всё подряд, краснеет на одном из них; порядок проверок закреплён структурно, потому что поведенчески два порядка на клиенте неразличимы; освобождение заявки проверяется ПАРОЙ (после успеха и после исключения); панель проверяется парой «есть вне записи / нет внутри записи»; число запросов предпроверки считается на ДВАДЦАТИ записях, поэтому реализация с проверкой по записи на нём краснеет; отсутствие повтора на админском экране закреплено отдельно, поэтому признак, приехавший туда, краснеет.
- Новых поверхностей вне `<threat_model>` не появилось; заглушек в изменённом исходном коде нет (`TODO`/`FIXME`/`placeholder` отсутствуют).

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*
