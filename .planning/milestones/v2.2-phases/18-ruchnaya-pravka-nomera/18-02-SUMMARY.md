---
phase: 18-ruchnaya-pravka-nomera
plan: 02
subsystem: ui
tags: [phone, manual-edit, form, htmx, fastapi, route, notices, gates, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "единственный писатель set_manual_phone (очистка = (NULL, false)), PhoneError и тексты отказа, EXAMPLE_PHONE, MANUAL_INPUT_MAX_CHARS; fill_reported_phone (KEPT / WRITTEN)"
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "помощник подписи label_of / row_of / load_account_rows, макрос components/account_label.html"
  - phase: 18-ruchnaya-pravka-nomera
    provides: "план 18-01: phone_is_manual в AccountRow / AccountLabel, пометка «указан вручную», seed_account(..., manual_phone=...), MANUAL_MARK"
provides:
  - "POST /accounts/{account_id}/phone — обработчик account_phone_save (app/pages/account_groups.py): владение на маршруте, единственный писатель, оба транспорта"
  - "Форма ручной правки номера в шапке экрана групп: контейнер #acct-phone [data-acct-phone], поле #phone (якорь для ссылки с карточки, план 18-03)"
  - "Ответ успеха с JS: <title> верхним узлом, форма, два внеполосных блока (#acct-head-name, #page-title) и приклеенное уведомление"
  - "Коды реестра уведомлений phone_saved («Номер сохранён.») и phone_cleared («Номер удалён.»)"
  - "Помощники экрана _screen_context / _screen_title, константа PHONE_FIELD_MAXLENGTH = 64, модульный logger"
  - "Числа сквозных гейтов сдвинуты поимённо одним коммитом с маршрутом (ведомость ниже)"
affects: [18-03]

actuals:
  tokens: 22500
  tasks: 3
  commits: 6
plan_head_before: 6d16402f96fc36ae623ca1617ce7dcdd0f97d867
plan_head_after: ef1f4cc03399aa2aa319c71fb1f612c2b25648aa

tech-stack:
  added: []
  patterns:
    - "Форма — единственный включаемый шаблон (phone_form.html), которым рисуются страница, ответ успеха и фрагмент 422; ключи формы ставит контекст экрана, включение умолчаний не ставит (Pitfall 2)"
    - "Контекст страницы — один сборщик _screen_context в том же модуле; заголовок вкладки — один помощник _screen_title для страницы, ответа и страницы 422"
    - "Отсутствие поля формы отличается от пустого поля сверкой присланных полей запроса: обязательное поле формы не годится — фреймворк считает пустую строку отсутствующей"
    - "Номер едет только телом POST: в адресе перехода — код исхода, в уведомлении номера нет, в журнале — account_id и phone_set"

key-files:
  created:
    - app/templates/account_groups/includes/phone_form.html
    - app/templates/account_groups/partials/phone_response.html
    - tests/test_pages/test_account_phone_form.py
  modified:
    - app/pages/account_groups.py
    - app/pages/notices.py
    - app/pages/htmx.py
    - app/templates/account_groups/list.html
    - app/templates/base.html
    - app/static/css/app.css
    - tests/test_pages/test_impersonation.py
    - tests/test_pages/test_impersonation_gate.py
    - tests/test_pages/test_notices_registry.py
    - tests/test_templates/test_form_inventory.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_origin_guard_on_destructive_routes.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_htmx_validation_sink.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_pages/test_responsive_markup.py
    - .planning/STATE.md

key-decisions:
  - "Поле phone — Form(None) + сверка присланных полей через request.form(), а НЕ Form(...): FastAPI 0.129 считает присланную пустую строку отсутствующей для обязательного поля формы (422 раньше обработчика), и очистка пустым полем (D-09) стала бы невозможной"
  - "Отсутствие поля поднимает тот же RequestValidationError, какой поднял бы фреймворк: без JS — стандартный 422, с JS — пустой 400 смягчения; проверка стоит после сверки источника и ДО выборки аккаунта, чтобы отказ не зависел от владения"
  - "Тип пути — PostIdPath и id_in_column первым использованием (не IdPath): так проект принял для изменяющих маршрутов (Фаза 11, D-07)"
  - "Откат сессии на ветках PhoneError / LookupError не звать; user_id = user.id берётся до писателя (Pitfall 1)"
  - "Кнопка «Сохранить» — variant=ghost: перечень мест акцентного цвета экрана групп исчерпывающий"
  - "maxlength = 2 * MANUAL_INPUT_MAX_CHARS = 64; autocomplete=off, inputmode=tel; required у поля нет"
  - "Журнал: одна запись account_phone_saved с account_id и phone_set на все сохранения, поля актора нет (D-16)"
  - "Сохранить без правки автономера делает его ручным — решение владельца 2026-11-21, закреплено тестом, сравнения с сохранённым значением в обработчике нет"

patterns-established:
  - "Тесты постят только на литеральные адреса f\"/accounts/{account_id}/phone\"; утверждение статуса перехода стоит ровно в двух функциях модуля (сохранение и очистка) — остальные сравнивают ответы между собой"
  - "Отрицательный контроль закрепляющего теста — временная мутация app/pages/account_groups.py, отказ записан дословно, git checkout -- файл, в коммит не входит"

requirements-completed: [PHONE-09, PHONE-10, PHONE-11]

coverage:
  - id: D1
    description: "Форма ручной правки номера в шапке экрана групп: ровно одна, method=post, action и hx-post равны /accounts/{id}/phone, поле type=tel id=phone с предзаполнением формой показа, подсказка с примером, без required"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_the_screen_carries_the_phone_form_in_the_account_head"
        status: pass
    human_judgment: false
  - id: D2
    description: "Годный ввод сохраняется единственным писателем: без JS — переход на экран с кодом исхода и якорем поля (номер в адресе не стоит), с JS — фрагмент с <title>, формой, двумя заголовками с пометкой и уведомлением; подпись в ответе свежая"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_a_valid_number_is_saved_and_the_redirect_carries_only_the_outcome_code"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_the_htmx_answer_replaces_the_form_the_headings_and_the_notice"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_the_answer_shows_the_saved_number_not_the_stale_object"
        status: pass
    human_judgment: false
  - id: D3
    description: "Неверный ввод — 422 с эхом (экранированным) и текстом константы PhoneError на обоих транспортах, без уведомления, кода исхода и внеполосных блоков; номер в базе прежний"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_an_invalid_number_answers_422_with_the_echo_on_both_transports"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пустое и пробельное поле (в том числе длиннее 32 символов) — очистка (None, false); текст PHONE_ERROR_BLANK форма не показывает; POST без поля номер не стирает; после очистки автоисточник снова пишет (KEPT → WRITTEN), пометки нет"
    requirement: "PHONE-10"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_an_empty_field_clears_the_number_and_never_shows_the_blank_error"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_a_post_without_the_field_leaves_the_number_untouched"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_after_the_clearing_an_automatic_source_may_fill_the_number_again"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_saving_an_automatic_number_unchanged_makes_it_manual"
        status: pass
    human_judgment: false
  - id: D5
    description: "Чужой, несуществующий, вне колонки аккаунт и LookupError писателя отвечают одинаково; чужой источник — 403 с пустым телом до выборки; номер чужого цел; дубликат номера принимается молча, аккаунты становятся двойниками"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_a_foreign_a_missing_and_an_out_of_column_account_answer_alike"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_a_writer_lookup_error_answers_like_a_missing_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_a_cross_origin_post_is_refused_before_any_lookup"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_the_same_number_on_two_accounts_makes_them_twins_without_a_refusal"
        status: pass
    human_judgment: false
  - id: D6
    description: "Номер не попадает в адрес, уведомление и журнал: событие account_phone_saved несёт только account_id и phone_set; запись только через set_manual_phone (гейты номера Фазы 16 зелены)"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_form.py#test_the_number_reaches_neither_the_address_nor_the_notice_nor_the_log"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py (1161 passed)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Правка под имперсонацией разрешена и пишет в базу; аккаунт третьего пользователя под имперсонацией отвечает как несуществующий; маршрут внесён в ALLOWED_ROUTES с причиной"
    requirement: "PHONE-11"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_phone_edit_is_allowed_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_third_users_account_stays_out_of_reach_under_another_identity"
        status: pass
    human_judgment: false
  - id: D8
    description: "Сквозные гейты D-08 сдвинуты поимённо одним коммитом с маршрутом, ровно на то, что называет план; реестр уведомлений — 21 код"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_notices_registry.py (626 passed) и полный tests/test_pages (2255 passed)"
        status: pass
    human_judgment: false
  - id: D9
    description: "Форма — собственная строка шапки; поле и кнопка переносятся без медиазапроса, фиксированных ширин нет (текст CSS закреплён тестом)"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_phone_form_takes_its_own_row_in_the_account_head"
        status: pass
    human_judgment: false
  - id: D10
    description: "Ручная половина: htmx подменяет форму, <h2> и <h1> шелла и заголовок вкладки без перезагрузки, плашка исхода появляется; 422 не поднимает плашку аварии; autocomplete не подставляет номер пользователя; раскладка шапки с формой на 320 и 375 px не ломается"
    requirement: "PHONE-09"
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет JS и не рендерит страницу, ширину и автозаполнение браузера видит только человек (/gsd-verify-work 18, «Manual-Only» в 18-VALIDATION.md); серверная половина — код 422 без уведомления и кода исхода — закреплена тестом 4"

duration: 71min
completed: 2026-11-21
status: complete
---

# Phase 18 Plan 02: Ручная правка номера — форма и маршрут Summary

**Форма в шапке экрана групп и маршрут `POST /accounts/{id}/phone` (`account_phone_save`): владение проверяется на маршруте, номер пишет только `set_manual_phone`, без JS — переход с кодом исхода, с JS — фрагмент с заголовком вкладки, формой и двумя заголовками; пустое поле очищает номер, неверный ввод — 422 с эхом, а все сдвинутые числа сквозных гейтов пришли тем же коммитом.**

## Performance

- **Duration:** 71 min
- **Started:** 2026-11-21T10:59:37Z
- **Completed:** 2026-11-21T12:10:21Z (до коммита этого файла)
- **Tasks:** 3 (задача 1 — трассер, один цикл RED → GREEN; задача 2 — закрепляющие тесты и CSS; задача 3 — записи и проза)
- **Files modified:** 23 (ровно перечень `files_modified` плана, из них 3 новых файла; других файлов нет)

## Accomplishments

- **Трассер (задача 1):** человек сохраняет, исправляет и стирает номер своего аккаунта формой в шапке `/accounts/{id}/groups`. Без JS — перенаправление `/accounts/{id}/groups?notice=phone_saved#phone` (номера в адресе нет), с JS — 200, тело начинается узлом `<title>`, затем форма `#acct-phone` и два внеполосных блока на `#acct-head-name` и `#page-title`, в конце приклеено «Номер сохранён.».
- **Неотличимость и источник:** чужой, несуществующий, вне колонки (`ID_MAX + 1`) аккаунты и `LookupError` писателя отвечают побайтно одинаково (302 / 204 + `HX-Location` на `/accounts`); чужой источник — 403 с пустым телом ДО выборки; закрыта угроза T-16-19.
- **D-09:** пустое и пробельное поле (в том числе 40 пробелов) — очистка `(NULL, false)`, `PHONE_ERROR_BLANK` форма не показывает; POST без поля `phone` номер не стирает.
- **Критерий 3:** ручной номер → `fill_reported_phone` = `KEPT` → очистка через маршрут → `WRITTEN`, подпись «Telegram +7 999 555-66-77» без пометки.
- **Имперсонация (D-06):** правка пишет в базу под чужой личностью; маршрут в `ALLOWED_ROUTES` с причиной; аккаунт третьего пользователя отвечает как несуществующий.
- **Бюджет гейтов (D-08):** все числа сквозных гейтов сдвинуты поимённо и поставлены прогоном покрасневших правил — первым же прогоном совпали с ведомостью плана; долг IN-01 закрыт диспозицией владельца в STATE.md.

## Публичный контракт для плана 18-03

**Форма и якорь.** Контейнер `<div id="acct-phone" data-acct-phone>` стоит последним ребёнком `[data-acct-head]` на `/accounts/{id}/groups`; внутри форма `method="post"`, `action` = `hx-post` = `/accounts/{id}/phone`, цель `#acct-phone`, способ `outerHTML`. Поле: `<input type="tel" name="phone" id="phone" autocomplete="off" inputmode="tel" maxlength="64">`, `value` — форма показа номера (`+7 999 123-45-67`) или пусто. **Ссылка с карточки аккаунта ведёт на `/accounts/{id}/groups#phone`** — якорь `id="phone"` стоит на поле, `<label for="phone">` её оборачивает. Кнопка «Сохранить» — `variant=ghost`.

**Маршрут.** `POST /accounts/{account_id}/phone`, обработчик `account_phone_save`, `Form` поле `phone` (необязательное для фреймворка, отсутствие отличается сверкой присланных полей). Без зависимости запрета имперсонации.

**Контракт ответа.**

| Запрос | Ответ |
|---|---|
| без htmx, годный ввод | `302`, `Location: /accounts/{id}/groups?notice=phone_saved#phone` |
| без htmx, пустое/пробельное поле | `302`, `Location: …?notice=phone_cleared#phone` |
| с htmx, успех | `200`; тело: `<title>`, `#acct-phone`, два внеполосных блока, приклеенное уведомление (`phone_saved` / `phone_cleared`) |
| без htmx, неверный ввод | `422`, страница экрана целиком (`<!DOCTYPE`, `data-acct-head`), эхо в поле, текст `PhoneError` под полем |
| с htmx, неверный ввод | `422`, фрагмент `#acct-phone` с эхом и текстом; ни уведомления, ни `hx-swap-oob`, ни заголовков `hx-*` |
| чужой / нет / вне колонки / `LookupError` | `302 /accounts`; с htmx — `204` и `HX-Location: /accounts` |
| чужой источник | `403`, тело пустое |
| нет сессии | переход на `/login` |
| POST без поля `phone` | без htmx — стандартный `422` фреймворка, с htmx — пустой `400`; номер прежний |

**Коды реестра уведомлений:** `phone_saved` — «Номер сохранён.», `phone_cleared` — «Номер удалён.» (`success`, оба без номера). **Ключи контекста шаблонов:** `screen_title`, `phone_value`, `phone_error`, `example_phone`, `phone_maxlength`, `acct_label`, `account_id`.

**Числа гейтов после 18-02** (для плана 18-03, который их не двигает): `WRITE_FORM_PLACES` 50, `MUTATING_ROUTE_COUNT` 50, `MUTATING_MODULE_COUNT` 14, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 26, `PUSH_URL_DECISIONS_DECLARED` 38, `PAIRED_302_ASSERTIONS_DECLARED` 193, `POST_PAIR_CASES_DECLARED` 79, реестр уведомлений 21. Ссылка карточки — GET, не форма: этих чисел она не двигает.

## Ведомость чисел гейтов: до → после

Каждое число поставлено прогоном покрасневшего правила; все совпали с ведомостью плана с первого прогона.

| Файл | Константа / реестр | До | После |
|---|---|---|---|
| `test_impersonation_gate.py` | `MUTATING_ROUTE_COUNT`; `ALLOWED_ROUTES` | 49 | 50; +ключ `account_phone_save` |
| там же | `MUTATING_MODULE_COUNT` | 14 | 14 |
| `test_form_inventory.py` | `WRITE_FORM_PLACES` / `WRITE_FORM_FILES` / `FORM_WRAPPER_CALLS` / `ALL_FORM_PLACES` / `ALL_FORM_FILES` | 49 / 27 / 29 / 51 / 29 | 50 / 28 / 30 / 52 / 30 |
| `test_htmx_markup_gates.py` | `OOB_BLOCKS` | 22 | 24 |
| там же | `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` | 29 | 30 |
| там же | `MACRO_DEFINITION_SITES_CALLERS_DECLARED` (+`phone_form.html` перед `list.html`) | 32 | 33 |
| там же | `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` (+`phone_form.html` между `group_row.html` и `max_connect_step.html`) | 16 | 17 |
| `test_htmx_gates.py` | `POST_HANDLERS` | 37 | 38 |
| там же | `FRAGMENT_RESPONSE_HANDLERS_DECLARED`; множество +ключ | 25 | 26 |
| там же | `TRANSITION_BRANCH_HANDLERS_DECLARED` | 31 | 32 |
| там же | `DUAL_BRANCH_HANDLERS_DECLARED`; множество +ключ | 19 | 20 |
| там же | `DUAL_BRANCH_PLACES_DECLARED` | 20 | 21 |
| там же | `PUSH_URL_DECISIONS_DECLARED`; +строка | 37 | 38 |
| там же | `OWN_RESPONSE_EXITS_DECLARED`; +запись | 14 | 15 |
| `test_origin_guard_on_destructive_routes.py` | `PAGE_POST_HANDLERS_MEASURED` / `ORIGIN_GUARD_CALL_SITES_MEASURED` | 37 / 14 | 38 / 15 (`GATE_UNIVERSE_HANDLERS_MEASURED` 10 без сдвига) |
| `test_identifier_bounds.py` | `CATALOGUE_UNIVERSE_DECLARED` | 36 | 37 |
| `test_htmx_post_pairs.py` | `POST_PAIR_CASES_DECLARED`; +2 `_PairCase` | 77 | 79 |
| там же | `PAIRED_302_ASSERTIONS_DECLARED` | 191 | 193 |
| `test_account_groups.py` | `SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED` | 61 | 62 |
| `test_notices_registry.py` + `notices.py` | `DECLARED_CODES`; два литерала | 19 | 21 |
| `test_htmx_validation_sink.py` | `VALIDATION_SINK_ROUTES_DECLARED` | 27 | 28 |
| `test_hx_location_destinations.py` | `HX_LOCATION_DESTINATION_CALLS_DECLARED` | 81 | 84 |
| `test_write_path_invariants.py` | своего числа нет | — | зелён (читает `ORIGIN_GUARD_CALL_SITES_MEASURED`) |

Ни одна строка летописи не стёрта: к каждому сдвинутому числу дописана строка «Фаза 18, план 18-02».

## Task Commits

1. **Задача 1 (трассер): форма, маршрут и все числа гейтов**
   - RED: `baa85949` (test) — 19 красных узлов
   - GREEN: `fccee5ed` (feat) — маршрут, форма, ответ, коды реестра и все числа одним коммитом (`git show --stat` называет `app/pages/account_groups.py` и девять модулей гейтов)
2. **Задача 2: закрепляющие тесты и раскладка формы**
   - закрепляющие (сразу зелёные, с отрицательными контролями): `fd3dba26` (test)
   - RED раскладки: `b4e0a323` (test) — 1 красный узел
   - GREEN раскладки: `25375c88` (feat)
3. **Задача 3: диспозиция IN-01 и поколение прозы слоя ответа**: `ef1f4cc0` (docs)

**Метаданные плана:** коммит `docs(18-02): …` с этим файлом.

## RED / GREEN / REFACTOR (улики)

Улики лежат под `.pytest_cache/gsd-red/` (вне git): `task1.{xml,record.json,out}`, `task2.{xml,record.json,out}`. Обе записи прошли `gsd_run check tdd-red-evidence` вердиктом `RED_EVIDENCE_OK` (`target_test_failed`).

- **Задача 1.** Цель: `tests/test_pages/test_account_phone_form.py::test_a_valid_number_is_saved_and_the_redirect_carries_only_the_outcome_code[display_form]` (классификатору нужно уникальное имя узла — берётся один параметр). Три совпадения: `FAILED tests/test_pages/test_account_phone_form.py::test_a_valid_number_is_saved_and_the_redirect_carries_only_the_outcome_code[eight_prefix]` (и два соседа), итог `19 failed, 56 passed`, причинный литерал `AssertionError: маршрут сохранения номера не ответил переходом` / `assert 404 == 302` (маршрута нет). Остальные красные узлы: 13 в новом модуле (все `404 == …` либо отсутствие формы на экране, `AttributeError` у `monkeypatch` на `set_manual_phone`), 2 имперсонации (`(None, False) == ('+79991234567', True)`, `None == '/accounts'`), 3 реестра уведомлений (`записей в реестре 19, ожидалось 21` и два соседних). Семантическая оценка: целевой узел упал на утверждении планируемого поведения (маршрут не отвечает переходом), а не на ошибке сбора или фикстуры. GREEN: те же три файла — `75 passed`.
- **Задача 2.** Цель: `tests/test_pages/test_responsive_markup.py::test_the_phone_form_takes_its_own_row_in_the_account_head`. Итог `1 failed`, причинный литерал `ValueError: substring not found`. GREEN: `731 passed` (`test_responsive_markup`, `test_account_groups`, `tests/test_templates`, `test_account_phone_form`).
- **REFACTOR:** не было (чистого рефакторинга нет, коммитов `refactor(18-02)` нет). Вынос `_screen_context` из `account_groups_page` сделан внутри GREEN задачи 1 — он нужен самому маршруту.

### Отрицательные контроли закрепляющих тестов (дословные отказы)

Каждая мутация — временная правка `app/pages/account_groups.py`, прогон одного теста, `git checkout -- app/pages/account_groups.py`; `git status --short app/pages/account_groups.py` после каждого пуст, в коммит не входила.

1. **D-14**, `test_the_answer_shows_the_saved_number_not_the_stale_object` — из сборщика `_saved` убран `await db.refresh(account)`: `AssertionError: ['Telegram +7 999 000-00-00', 'Telegram +7 999 000-00-00']`.
2. **D-15**, `test_the_same_number_on_two_accounts_makes_them_twins_without_a_refusal` — временный отказ при совпадении номера с другим аккаунтом пользователя: `AssertionError: assert '/accounts' == '/accounts/2/...e_saved#phone'`.
3. **Решение владельца**, `test_saving_an_automatic_number_unchanged_makes_it_manual` — временное сравнение с сохранённым значением (ввод, равный автономеру, ничего не пишет): `AssertionError: assert ('+79991234567', False) == ('+79991234567', True)`.
4. **Критерий 3**, `test_after_the_clearing_an_automatic_source_may_fill_the_number_again` — пустой ввод не доходит до писателя (флаг не снимается): `AssertionError: assert <PhoneWrite.KEPT: 'kept'> is <PhoneWrite.WRITTEN: 'written'>`.

## TDD Gate Compliance

Для обеих задач с кодом есть `test(18-02): …`, затем `feat(18-02): …` (потомок RED): порядок `baa85949 → fccee5ed`, `b4e0a323 → 25375c88`. Коммит `fd3dba26` — `test(18-02)` без парного `feat`: это закрепляющие тесты поведения, доставленного `fccee5ed`, они зелёные сразу, и их защита от вакуума — четыре мутации выше. Нарушений порядка нет.

## Числа рядом с базой

| Набор | База (после 18-01, по заметке оркестратора) | Итог (`ef1f4cc0`) | Разница |
|---|---|---|---|
| compileall `app main.py tests` | rc=0 | rc=0 | — |
| `prohibitions_census.py --check` | 965 строк, согласие | 965 строк, согласие, rc=0 | 0 (плана нет строк реестра) |
| гейты номера Фазы 16 (privacy + parity + single-writer) | 1161 passed | 1161 passed | 0 |
| сквозные гейты (команда заметки 8: `tests/test_templates` + `test_htmx_gates` + `test_htmx_post_pairs` + `test_declared_invariants` + `test_impersonation_gate` + `test_notices_registry`) | 624 passed | 626 passed | +2 (два новых параметра пар `POST_PAIR_CASES`) |
| `tests/test_pages/test_responsive_markup.py` | 146 passed | зелёный в составных прогонах `1543` и `731` и в полном `tests/test_pages`; отдельным прогоном число не снималось | +1 узел (`test_the_phone_form_takes_its_own_row_in_the_account_head`) |
| новый `tests/test_pages/test_account_phone_form.py` | — | 18 passed | +18 |
| команда 1 `<verify>` задачи 1 (форма + имперсонация + реестр уведомлений) | — | 75 passed | — |
| `tests/test_templates` + гейты номера + `test_services/test_phone.py` + `test_declared_invariants` (команда 2 задачи 3) | — | 1892 passed | — |
| полный `tests/test_pages` | — | 2255 passed (27 мин) | — |
| `tests/test_planning` | 218 passed, 2 skipped | 218 passed, 2 skipped (перед коммитом задачи 3); после коммита сводки — в сообщении возврата | 0 |

## Decisions Made

См. `key-decisions` во frontmatter. Главное: поле `phone` необязательное для фреймворка (`Form(None)`) с явной сверкой присланных полей; тип пути `PostIdPath`; без отката сессии; кнопка `ghost`; журнал только `account_id` и `phone_set`.

## Deviations from Plan

### Auto-fixed / замеренные отличия

**1. [Rule 1 - Bug в посылке плана] `Form(...)` делает очистку невозможной**
- **Найдено в:** задача 1, GREEN (первый же прогон `test_an_empty_field_clears_the_number…[empty]` дал `404 → 422`).
- **Суть:** план и RESEARCH Pitfall 3 прописывают `phone: str = Form(...)`: «пустая строка очищает, отсутствие поля — отказ разбора». Замер на FastAPI 0.129 (`fastapi/dependencies/utils.py::_get_multidict_value`): для поля формы присланная пустая строка считается отсутствующей и, если поле обязательное, даёт `422` раньше обработчика. То есть с `Form(...)` очистка пустым полем — основной путь D-09 — невозможна, а с умолчанием (`Form("")`, как у `profile_post`) отсутствие поля неотличимо от пустого и молча стирает номер (T-18-08).
- **Fix:** `phone: str | None = Form(None)`; в теле, после сверки источника и ДО выборки аккаунта, — `submitted = await request.form()` (разобранная форма кэшируется, второго чтения тела нет) и `if "phone" not in submitted: raise RequestValidationError(...)` — тот же отказ, какой поднял бы фреймворк: без JS стандартный 422, с JS пустой 400 смягчения (`malformed_request_response`). `phone_text = phone or ""` передаётся писателю. Докстринг обработчика называет замер и снятое утверждение плана.
- **Файлы:** `app/pages/account_groups.py`. **Проверено:** `test_a_post_without_the_field_leaves_the_number_untouched` (422 / пустой 400, номер прежний), `test_an_empty_field_clears…` (три параметра), все гейты. **Коммит:** `fccee5ed`.

**2. [Plan vs measured] Число вызовов `respond` с фрагментом — `25 2`, а не `16 2`**
- **Найдено в:** задача 3, воспроизводимая команда из докстринга `respond`.
- **Суть:** план ожидал `16 2` (пятнадцать на дереве конца Фазы 11 плюс один). Замер на дереве плана: `25 2` — 25 вызовов в 18 обработчиках; между Фазой 11 и этим деревом фрагменты добавили Фазы 12 и 13: `accounts_connect_tg_user_start_qr` (3), `_refresh_qr` (1), `_verify_2fa` (1), `_qr_status` (2) и `ads_images_upload` (2) — девять вызовов. Вызовов с фрагментом И кодом исхода — два (`profile_post`, `account_phone_save`), как ожидал план.
- **Fix:** абзацы шестого поколения в докстрингах `respond` и `_glue_notice` написаны по замеру и называют причину расхождения; формулировки пятого поколения не стёрты, названы верными для дерева Фазы 11. **Коммит:** `ef1f4cc0`.

**3. [Plan vs measured] Отрицательный контроль 4 — мутация обработчика, а не писателя**
- План называет контролем «временный писатель без снятия флага». Писатель `app/application/accounts/phone.py` не входит в `files_modified` плана, а снятие флага без обнуления номера краснит `CHECK ck_messenger_accounts_manual_requires_phone` (500, а не `KEPT`). Мутация сделана в обработчике: пустой ввод не доходит до писателя — флаг остаётся, второй вызов даёт `KEPT`. Закрепляющий тест, который охраняет сценарий критерия 3 на пути маршрута, краснеет тем же отказом.

**4. [Plan vs measured] Узел цели RED — один параметр**
- Верб RED-улики не принимает имя параметризованного теста без параметра (`no_target_test_failure`); запись собрана на `…[display_form]`, как у 18-01.

**5. [Замечание] Правило полноты 302 на RED-коммите не прогонялось**
- План называет его ожидаемо красным в RED-коммите задачи 1 (`test_htmx_post_pairs`: новые утверждения о маршруте, которого нет). Командой RED были три файла плана; `test_htmx_post_pairs` на RED-дереве не гонялся, чтобы не тратить ~4 минуты на заранее названное красное. На GREEN-коммите оно зелёное с числом 193.

### Подмены механики (не отклонения от плана)

- Журнал плана (`plan-head-before-18-02`) лежит в `.pytest_cache/checks/`, не в `.git/…`: составные `git`-команды песочница отклоняет (как у 18-01); база — SHA `6d16402f96fc36ae623ca1617ce7dcdd0f97d867`, взятый при старте (он же `plan_head_before`). Сентинел `gsd-spawn-toplevel` не писался; смещение cwd контролировалось тем, что все команды шли из корня worktree.
- Правки реестров гейтов, замены в шаблонах и мутации контролей делались скриптами `python3 -` с точной заменой и `assert count == 1` (инструмент Edit не годится для десятков однотипных вставок); каждая замена проверена утверждением числа вхождений.
- Прогоны pytest — через `.pytest_cache/checks/pt.sh` под общим замком `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`; ожидание длинных прогонов — `flock -w … true`.
- `graphify update .` не запускался (графа в worktree нет; граф пересобирает оркестратор после слияния). Полная суита (`just test`) не гонялась — её гоняет посмертный гейт оркестратора; вместо неё — полный `tests/test_pages`, `tests/test_templates`, гейты номера, `test_planning`.
- `commits: 6` измерено `git rev-list --count 6d16402f..HEAD` до коммита этой сводки.

**Итого отклонений:** 5 (1 ошибочная посылка плана про `Form(...)`, 2 расхождения с замером, 1 замечание о RED-прогоне). **Влияние:** поведение — как в плане (в том числе для отсутствующего поля: 422 / пустой 400, номер цел), числа гейтов — как в ведомости; scope не расширен.

## Authentication Gates

Нет.

## Issues Encountered

Нет неразрешённых. `deferred-items.md` не создавался; отложенного нет. Предмет вне плана, увиденный при работе и не тронутый: поведение `Form(None)` FastAPI для пустых строк у `profile_post` (там умолчание `""` и очистка/отсутствие неразличимы) — к фазе не относится, для профиля пустой пояс не годится в любом случае.

## Known Stubs

Нет: заглушек, пустых значений, текстов «скоро» в изменённых файлах нет. `phone_error=None` и `phone_value=""` в `_screen_context` — осознанные умолчания страницы (перекрываются обработчиком на ветке ошибки), не заглушки.

## Threat Flags

Нет: новый сетевой адрес (`POST /accounts/{id}/phone`) и его границы доверия целиком названы в `<threat_model>` плана (T-18-04…T-18-14). Мера T-18-08 (стирание POST-ом без поля) реализована иначе, чем предполагал план (см. отклонение 1), но закрыта тестом.

## Next Phase Readiness

- План 18-03 строит ссылку «Указать номер» / «Изменить» на `/accounts/{id}/groups#phone`; контракт якоря и ответов — выше. Числа гейтов он не двигает.
- Ручная половина критериев 1 и 2 остаётся человеку: `/gsd-verify-work 18` (подмена формы/заголовков/вкладки с JS, плашка исхода, отсутствие плашки аварии на 422, автозаполнение браузера, ширины 320 и 375 px).

## Self-Check: PASSED

- Созданные файлы существуют: `app/templates/account_groups/includes/phone_form.html`, `app/templates/account_groups/partials/phone_response.html`, `tests/test_pages/test_account_phone_form.py`.
- Коммиты `baa85949`, `fccee5ed`, `fd3dba26`, `b4e0a323`, `25375c88`, `ef1f4cc0` — предки HEAD.
- Приёмочные счётчики: `@router.post("/accounts/{account_id}/phone")` — 1; `set_manual_phone` в `account_groups.py` — 3 (≥2); `D-09 Фазы 18` — 1; `_screen_context` — 4 (≥3); `PHONE_SAVED = "phone_saved"` и `PHONE_CLEARED = "phone_cleared"` — по 1; `id="acct-head-name"` в `list.html` — 1; `id="page-title"` в `base.html` — 1; включение `phone_form.html` в `list.html` — 1; `hx-swap-oob` в `phone_response.html` — 2, `acct-phone` там — 0; `PHONE_ERROR_BLANK` в `app/services/phone.py` — 3; утверждений о переходе в `test_account_phone_form.py` — 2, в `test_impersonation.py` — 14; `notice-alert` / `hx-swap-oob` в `test_account_phone_form.py` — 1 / 3; `data-acct-phone` в `app.css` — 3 (≥2); `пустое поле = очистка (D-09 Фазы 18)` в `STATE.md` — 1; `Phase 16 → Phase 18` в `STATE.md` — 1; `ШЕСТОЕ ПОКОЛЕНИЕ` в `htmx.py` — 2, `account_phone_save` там — 3.
- Диспозиция IN-01 — до правки третьей колонки строка `| Phase 16 → Phase 18 | IN-01 …` была: «Отложено на Фазу 18 (решение владельца О-4, 2026-10-09, прогон `/gsd-plan-phase 16 --gaps`): её форма выбирает между явным действием «очистить» и показом `PHONE_ERROR_BLANK`; поведение сегодня предписано D-07 / PHONE-10 — планировщику Фазы 18 решить до плана формы» — теперь целиком перенесена в кавычки после новой диспозиции; первая, вторая и четвёртая колонки не тронуты, иных строк STATE.md план не правил, шагов трекинга исполнитель не вызывал.

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-21*
