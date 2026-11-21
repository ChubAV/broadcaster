---
phase: 18-ruchnaya-pravka-nomera
verified: 2026-11-21T15:00:00Z
status: human_needed
score: 5/5 must-haves verified
covered_files:
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-01-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-01-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-02-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-02-SUMMARY.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-03-PLAN.md"
  - ".planning/phases/18-ruchnaya-pravka-nomera/18-03-SUMMARY.md"
  - "app/application/accounts/dto.py"
  - "app/application/accounts/labels.py"
  - "app/application/accounts/use_cases.py"
  - "app/pages/account_groups.py"
  - "app/pages/accounts.py"
  - "app/pages/htmx.py"
  - "app/pages/notices.py"
  - "app/services/account_label.py"
  - "app/static/css/app.css"
  - "app/templates/account_groups/includes/phone_form.html"
  - "app/templates/account_groups/list.html"
  - "app/templates/account_groups/partials/phone_response.html"
  - "app/templates/accounts/list.html"
  - "app/templates/accounts/partial_cards.html"
  - "app/templates/accounts/partials/sync_status_card.html"
  - "app/templates/base.html"
  - "app/templates/components/account_label.html"
  - "tests/account_label_support.py"
  - "tests/test_application/test_account_label_rows.py"
  - "tests/test_pages/test_account_groups.py"
  - "tests/test_pages/test_account_label_accounts.py"
  - "tests/test_pages/test_account_label_groups.py"
  - "tests/test_pages/test_account_label_sweep.py"
  - "tests/test_pages/test_account_phone_form.py"
  - "tests/test_pages/test_account_phone_links.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_htmx_validation_sink.py"
  - "tests/test_pages/test_hx_location_destinations.py"
  - "tests/test_pages/test_identifier_bounds.py"
  - "tests/test_pages/test_impersonation.py"
  - "tests/test_pages/test_impersonation_gate.py"
  - "tests/test_pages/test_notices_registry.py"
  - "tests/test_pages/test_origin_guard_on_destructive_routes.py"
  - "tests/test_pages/test_responsive_markup.py"
  - "tests/test_services/test_account_label.py"
  - "tests/test_templates/test_form_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
covered_digest: "v4:sha256:07f4591bca3343b4aeb47d0296ae2d442437a164cbf60ede380eb70a4e8393ee"
behavior_unverified: 0
overrides_applied: 0
prohibitions_flagged: 12
human_verification:
  - test: "htmx-обмен без перезагрузки: на экране групп аккаунта (`/accounts/{id}/groups`) в браузере с JS ввести `8 999 123 45 67` в поле «Номер телефона» и нажать «Сохранить»"
    expected: "страница не перезагружается; форма `#acct-phone` показывает `+7 999 123-45-67`; `<h2>` шапки аккаунта и `<h1>` шелла сменили подпись на «+7 999 123-45-67 указан вручную»; заголовок вкладки браузера сменился на подпись с новым номером; появилась плашка «Номер сохранён.»"
    why_human: "суита не исполняет JS: она проверяет разметку ответа (`<title>` первым узлом, два внеполосных блока, уведомление), но не то, что рантайм htmx действительно подменил цели"
  - test: "Очистка с JS: стереть поле и нажать «Сохранить»"
    expected: "без перезагрузки подпись везде «Номер неизвестен», пометки «указан вручную» нет, плашка «Номер удалён.»; текста про пустой ввод нигде нет"
    why_human: "то же: серверная часть закреплена тестами, подмена цели в браузере — нет"
  - test: "422 без плашки аварии: ввести неверный номер (например `abc`) с JS и нажать «Сохранить»"
    expected: "под полем текст «Не похоже на номер телефона. Пример: +7 999 123-45-67» по-русски; в поле остался набранный текст `abc`; плашка аварии на экране НЕ появилась"
    why_human: "поведение плашки — клиентский код; серверная половина (код ровно 422, без `HX-*` и внеполосных блоков) закреплена тестами 18-02-01 и `test_shell.py`"
  - test: "Якорь `#phone`: с `/accounts` нажать «Указать номер» / «Изменить» на аккаунте, у которого длинный список групп (экран прокручивается)"
    expected: "открывается экран групп этого аккаунта, поле «Номер телефона» оказалось в видимой области и НЕ скрыто липкой шапкой `[data-head]` (см. WR-02: `scroll-margin-top` в `app.css` нет — поле может оказаться под шапкой)"
    why_human: "прокрутка и перекрытие липкой шапкой — поведение браузера; вывод WR-02 сделан по чтению CSS, замера нет"
  - test: "Автозаполнение: открыть экран групп в браузере с сохранённым автозаполнением (в том числе своим номером)"
    expected: "поле «Номер телефона» не предлагает номер самого пользователя (`autocomplete=\"off\"`)"
    why_human: "поведение браузеров неоднородно, суита проверяет только атрибут"
  - test: "Раскладка на 320 и 375 px: шапка экрана групп с формой номера и пометкой «указан вручную»; чип расписания с ручным номером; карточка аккаунта на `/accounts`"
    expected: "шапка с формой не ломает раскладку, форма на своей строке; пометка усекается раньше номера, `#id` двойника виден рядом; кнопка «Сохранить» стоит у поля, а не отрывается от него (WR-01: выровнена по низу подсказки); ряд действий карточки в `sync_failed` (четыре элемента) не ломается"
    why_human: "рендер в суите не проверяется: тесты читают только текст CSS"
---

# Фаза 18: ручная правка номера — отчёт верификации

**Цель фазы:** пользователь сам указывает, исправляет или стирает номер своего аккаунта в любой момент и видит, что номер указан им, — а автоматика его не перебивает
**Проверено:** 2026-11-21
**Статус:** human_needed
**Повторная верификация:** нет — первичная

Исходная гипотеза проверки — «задачи выполнены, цель не достигнута». Опровергнуть её по коду и тестам не удалось: маршрут, форма, пометка, ссылки и гейты существуют, связаны и исполняются. Остались только проверки в браузере, которые суита не способна выполнить, — они вынесены в `human_verification`. Блокеров и разрывов нет.

## Достижение цели

### Наблюдаемые истины (контракт — пять критериев ROADMAP)

| # | Истина | Статус | Улика |
|---|--------|--------|-------|
| 1 | Ссылка «Указать номер» / «Изменить» ведёт с карточки на экран групп; свободная форма ввода; с JS — фрагмент, без JS — `method="post"` с тем же `action`; после сохранения номер с пометкой «указан вручную» виден везде, где подпись рисуется разметкой | ✓ VERIFIED (серверная часть; браузерная — в human_verification) | Девять ссылок `…/groups#phone` в трёх исходниках карточки (`accounts/list.html:119,145,185`, `partial_cards.html:67,93,128`, `sync_status_card.html:102,119,143`), текст выбирается по `acct_label.phone_text`. `form_wrapper(action='/accounts/' ~ account_id ~ '/phone', target='#acct-phone', swap='outerHTML')` в `phone_form.html`. Обработчик `account_phone_save` (`account_groups.py:356`) пишет через `set_manual_phone` (`8 999…` → `(+79991234567, True)`). Ответ с JS — `phone_response.html`: `<title>`, форма, два внеполосных блока на `#acct-head-name` и `#page-title`; ответ без JS — `respond(..., redirect=…#phone, notice=…)`. Пометка — макрос `account_label.html` по `label.phone_is_manual`, 17 мест использования макроса; плоские формы (`<title>`, модалка `acct_label.plain`, `<option>`, CSV) без пометки. Целевой прогон: `test_account_phone_form.py`, `test_account_phone_links.py`, `test_account_label.py`, `test_account_label_rows.py` — 98 passed |
| 2 | Неверный ввод — 422 с русским текстом и примером; поле сохраняет введённое; плашка аварии не поднимается | ✓ VERIFIED (серверная часть; плашка на экране — в human_verification) | `except PhoneError` → `respond_field_error(request, page=_page, fragment=_error_fragment)`; `_page` и `_error_fragment` ставят `phone_value=phone_text` (эхо) и `phone_error=refusal_text`; значение в текст ошибки не подставляется. `test_an_invalid_number_answers_422_with_the_echo_on_both_transports` и `test_shell.py::test_the_failure_banner_tells_a_validation_answer_from_a_crash` зелёные |
| 3 | Очистка поля: везде «Номер неизвестен», пометка исчезает, автоисточник снова вправе писать (условная запись проходит) | ✓ VERIFIED | `set_manual_phone`: пустая/пробельная строка → `UPDATE … SET phone=NULL, phone_is_manual=false` (`phone.py:216-243`); обработчик пустоту ошибкой не считает. `test_after_the_clearing_an_automatic_source_may_fill_the_number_again`: `KEPT` при ручном номере → очистка → `WRITTEN`, подпись «Telegram +7 999 555-66-77» без пометки. `test_an_empty_field_clears_the_number_and_never_shows_the_blank_error` и `test_a_post_without_the_field_leaves_the_number_untouched` (отсутствие поля не стирает) зелёные |
| 4 | Имперсонация: администратор правит номер, разрешение закреплено тестом с причиной; чужой аккаунт отвечает как несуществующий; `is_same_origin` и граница `ID_MAX` | ✓ VERIFIED | `ALLOWED_ROUTES["app/pages/account_groups.py::account_phone_save"] = "номер — подпись, а не учётные данные; на доставку не влияет"` (`test_impersonation_gate.py:260`); у маршрута нет зависимости запрета имперсонации. `test_impersonation.py::test_the_phone_edit_is_allowed_under_another_identity` читает базу (`(+79991234567, True)`; третий пользователь — номер не тронут). Порядок проверок в обработчике: сессия → `is_same_origin` (403 без тела) → `"phone" not in submitted` → `id_in_column(account_id)` → `_load_owned_account` → писатель; `PostIdPath`. Тесты `test_a_foreign_a_missing_and_an_out_of_column_account_answer_alike`, `test_a_writer_lookup_error_…`, `test_a_cross_origin_post_is_refused_before_any_lookup` зелёные |
| 5 | Сквозные гейты нового маршрута и формы пересчитаны и зелёны в полном прогоне | ✓ VERIFIED | Числа в коде: `WRITE_FORM_PLACES = 50` (`test_form_inventory.py:176`), `MUTATING_ROUTE_COUNT = 50` (`test_impersonation_gate.py:125`), `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 26` (`test_htmx_gates.py:2353`), `PUSH_URL_DECISIONS_DECLARED = 38` (`:6969`), `PAIRED_302_ASSERTIONS_DECLARED = 193` (`test_htmx_post_pairs.py:3490`); реестр уведомлений: `PHONE_SAVED`/`PHONE_CLEARED` + записи `Notice(...)` в `notices.py:146-147,316-317`. Мой прогон гейтовой выборки (имперсонация, реестр уведомлений, границы ID, сверка источника, валидационный сток, адреса `HX-Location`, паритет и приватность номера, единый писатель, тест имперсонации номера) — 1248 passed. Полный прогон на `d197f956`: 6035 passed, 2 skipped (лог оркестратора `.pytest_cache/gsd-orch/suite-p18-w3.log`, `TEST_EXIT=0`); после него менялись только `.planning/` (`git diff --name-only d197f956..HEAD -- app tests` пуст) |

**Счёт:** 5/5 истин критериев верифицировано (браузерные половины критериев 1 и 2 — отдельными пунктами `human_verification`); 0 истин «присутствует, поведение не проверено».

### Истины планов (сверх ROADMAP, не сужают контракт)

| Источник | Истина | Статус | Улика |
|----------|--------|--------|-------|
| 18-01 | Пометка только при известном номере: `AccountLabel.phone_is_manual` истинен лишь при `shown is not None` | ✓ VERIFIED | `account_label.py:148,162` — `manual and shown is not None` |
| 18-01 | Флаг не входит в ключ двойника | ✓ VERIFIED | `account_label.py:155` — `_twin_key(type_, shown)`; флаг в ключ не передаётся |
| 18-01 | Порядок частей: канал → номер → «указан вручную» → `#id` | ✓ VERIFIED | `account_label.html` макрос `account_label`: строки в этом порядке |
| 18-01 | Фрагмент опроса несёт пометку во всех статусах | ✓ VERIFIED | `dto.py` `SyncStatusView.phone_is_manual`; `accounts.py` собирает `AccountRow(account_id, view.messenger_type, view.phone, view.phone_is_manual)`; тесты `test_account_label_accounts.py`, `test_account_label_sweep.py` зелёные в полной суите |
| 18-02 | Запись только через `set_manual_phone`, журнал — только `account_id` и `phone_set`, номер не в адресе и не в уведомлении | ✓ VERIFIED | `logger.info("account_phone_saved", account_id=…, phone_set=…)`; редирект — код исхода; гейты единого писателя и приватности номера зелёные; `test_the_number_reaches_neither_the_address_nor_the_notice_nor_the_log` |
| 18-02 | Свежая подпись после записи (D-14) | ✓ VERIFIED | `_saved()` делает `db.refresh(account)` и `load_account_rows` до рендера; `test_the_answer_shows_the_saved_number_not_the_stale_object` |
| 18-02 | Дубликат принимается; «Сохранить» без правки — ручной номер | ✓ VERIFIED | `test_the_same_number_on_two_accounts_…`, `test_saving_an_automatic_number_unchanged_makes_it_manual` |
| 18-03 | Номера в `href` нет; ссылка не новый маршрут и не форма; чужой аккаунт во фрагменте ссылки не получает | ✓ VERIFIED | `href` — только `/accounts/{id}/groups#phone`; `test_the_phone_link_carries_no_number`, `test_a_foreign_account_poll_draws_no_phone_link` |
| 18-01/02/03 | Ручные половины (`verification: backstop`: раскладка 320/375 px, htmx-подмена, автозаполнение, прокрутка якоря) | абстиненция | Присутствие + проводка не квалифицируют; вынесено в `human_verification` |

### Обязательные артефакты (все из frontmatter трёх планов)

| Артефакт | Ожидание | Статус | Детали |
|----------|----------|--------|--------|
| `app/services/account_label.py` | `AccountRow/AccountLabel.phone_is_manual` | ✓ VERIFIED | поля без умолчания (`:55`, `:66`), используются `row_of`, `label_of`, `build_labels` |
| `app/application/accounts/labels.py` | четвёртая колонка в `load_account_rows` | ✓ VERIFIED | проходит через тесты строк подписи |
| `app/templates/components/account_label.html` | `acct-label__manual` | ✓ VERIFIED | печатается по `label.phone_is_manual` |
| `app/application/accounts/dto.py` | `SyncStatusView.phone_is_manual: bool = False` | ✓ VERIFIED (см. WR-03) | умолчание задано планом дословно |
| `app/static/css/app.css` | правила `.acct-label__manual` | ✓ VERIFIED | `:2556-2560`, усечение в чипе и `.acct-head__name`; `#id` — `flex: none` |
| `app/pages/account_groups.py` | `account_phone_save`, `_screen_context`, `_screen_title` | ✓ VERIFIED | не заглушка, 150+ строк логики |
| `account_groups/includes/phone_form.html`, `partials/phone_response.html` | форма и ответ успеха | ✓ VERIFIED | включены в `list.html` и ответ обработчика |
| `app/pages/notices.py` | `PHONE_SAVED`, `PHONE_CLEARED` | ✓ VERIFIED | константы и записи реестра |
| `accounts/list.html`, `partial_cards.html`, `partials/sync_status_card.html` | по три ссылки | ✓ VERIFIED | девять совпадений `/groups#phone` |
| `tests/test_pages/test_account_phone_form.py`, `test_account_phone_links.py`, `tests/account_label_support.py` | тесты и посев | ✓ VERIFIED | 19 + 7 функций тестов, зелёные |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус |
|--------|------|-------|--------|
| `phone_form.html` | `account_phone_save` | `form_wrapper(action='/accounts/'~id~'/phone')` ↔ `@router.post("/accounts/{account_id}/phone")` | ✓ WIRED |
| `account_phone_save` | `set_manual_phone` | `await set_manual_phone(db, account_id, phone_text)` после `_load_owned_account` | ✓ WIRED |
| `account_phone_save` | слой ответа | `respond(...)`, `respond_field_error(request, page=…, fragment=…)` | ✓ WIRED |
| `phone_response.html` | `base.html` (`#page-title`) и `list.html` (`#acct-head-name`) | внеполосные блоки `innerHTML:#…` | ✓ WIRED |
| `account_label.html` | `AccountLabel` | `label.phone_is_manual` | ✓ WIRED |
| `accounts.py` (опрос) | `SyncStatusView` | `view.phone_is_manual` | ✓ WIRED |
| ссылка карточки | поле формы | `…/groups#phone` ↔ `<input id="phone">` в `[data-acct-phone]` (тест сквозного перехода) | ✓ WIRED (прокрутка — human) |

### Трассировка потока данных (уровень 4)

| Артефакт | Данные | Источник | Реальные данные | Статус |
|----------|--------|----------|-----------------|--------|
| форма номера | `phone_value` | `acct_label.phone_text` из `load_account_rows` (запрос к `messenger_accounts`) / эхо присланного | да | ✓ FLOWING |
| пометка | `label.phone_is_manual` | колонка `MessengerAccount.phone_is_manual` под CHECK базы | да | ✓ FLOWING |
| ответ успеха | `acct_label` | `db.refresh` + `load_account_rows` после коммита | да | ✓ FLOWING |
| ссылка карточки | `acct_label.phone_text` | уже в контексте трёх шаблонов | да | ✓ FLOWING |

### Поведенческие проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Маршрут, оба транспорта, 422, очистка, владение, источник, приватность, критерий 3, ссылки, подпись | `flock … uv run pytest tests/test_pages/test_account_phone_form.py tests/test_pages/test_account_phone_links.py tests/test_services/test_account_label.py tests/test_application/test_account_label_rows.py -q -p no:randomly` | 98 passed | ✓ PASS |
| Гейты нового маршрута и номера, имперсонация | `flock … uv run pytest tests/test_pages/test_impersonation_gate.py tests/test_pages/test_notices_registry.py tests/test_pages/test_identifier_bounds.py tests/test_pages/test_origin_guard_on_destructive_routes.py tests/test_pages/test_htmx_validation_sink.py tests/test_pages/test_hx_location_destinations.py tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py "tests/test_pages/test_impersonation.py::test_the_phone_edit_is_allowed_under_another_identity" -q -p no:randomly` | 1248 passed | ✓ PASS |
| Полная суита | не запускалась (≈44 мин); берётся лог оркестратора на `d197f956` | 6035 passed, 2 skipped, `TEST_EXIT=0`; кодовых изменений после него нет | ✓ PASS (по логу) |

Критерий 3 — переход состояния (ручной → очистка → автоисточник вправе писать): behavior-dependent, и исполняющий его тест есть и прошёл (`KEPT` → `WRITTEN`), поэтому здесь VERIFIED, а не «присутствует без проверки».

### Выполнение проб

Фаза не объявляет проб (`probe-*.sh`) — шаг пропущен.

### Покрытие требований

| Требование | План | Описание | Статус | Улика |
|------------|------|----------|--------|-------|
| PHONE-08 | 18-01 | пометка «указан вручную» у ручного номера | ✓ SATISFIED | макрос подписи, `phone_is_manual` в `AccountRow/AccountLabel/SyncStatusView`, CSS-контракт; тесты подписи и прохода по экранам. Раскладка 320/375 px — human |
| PHONE-09 | 18-02, 18-03 | указать/изменить/очистить в любой момент, с JS и без, свободный ввод, 422 по-русски с эхо | ✓ SATISFIED (браузерные половины — human) | маршрут `account_phone_save`, форма, 9 ссылок входа |
| PHONE-10 | 18-02 | после очистки «Номер неизвестен» и автоисточники снова вправе писать | ✓ SATISFIED | `set_manual_phone` очищает обе колонки; тест `KEPT` → `WRITTEN` |
| PHONE-11 | 18-02 | администратор под имперсонацией правит номер; чужой аккаунт как несуществующий | ✓ SATISFIED | `ALLOWED_ROUTES` с причиной, тест имперсонации читает базу, тест неотличимости чужого |

Все четыре ID (PHONE-08, 09, 10, 11) заявлены в `requirements:` планов (18-01: PHONE-08; 18-02: PHONE-09, 10, 11; 18-03: PHONE-09) и присутствуют в `REQUIREMENTS.md` (строки 28, 32–34; трассировка: Phase 18). Осиротевших требований нет: другие ID фазе 18 в `REQUIREMENTS.md` не назначены. Чекбоксы и колонка «Pending» в `REQUIREMENTS.md` — запись оркестратора при закрытии фазы, верификатор их не правит.

### Запреты планов (`must_haves.prohibitions`)

Все 12 запретов трёх планов объявлены `status: flagged-unverified` (уровень judgment). Ниже — НЕАВТОРИТЕТНЫЙ вердикт по чтению кода; `unverified-prohibition — human review recommended`, как предписано режимом верификации.

| Запрет | Вердикт по коду | Флаг |
|--------|-----------------|------|
| 18-01: флаг в `_twin_key` | не нарушен (`_twin_key(type_, shown)`) | human review recommended |
| 18-01: пометка в плоских формах | не нарушена (`<title>`/модалка используют `plain`; макрос — единственный источник пометки) | human review recommended |
| 18-01: умолчание у `AccountRow.phone_is_manual` | не нарушен (`:55` без умолчания); умолчание есть у `SyncStatusView` — это отдельное поле, прямо заданное планом (см. WR-03) | human review recommended |
| 18-01: запись в колонки из продуктового кода плана | не нарушен; гейт единого писателя зелёный | human review recommended |
| 18-02: запись мимо `set_manual_phone` | не нарушен; гейты писателя и паритета зелёные | human review recommended |
| 18-02: номер в журнал/адрес/уведомление | не нарушен (`account_id`, `phone_set`) | human review recommended |
| 18-02: зависимость запрета имперсонации; различение чужого и несуществующего | не нарушен | human review recommended |
| 18-02: `PHONE_ERROR_BLANK` из формы, `required` у поля | не нарушен (поле без `required`, пустота — очистка до нормализатора) | human review recommended |
| 18-02: откат сессии на ветках отказа; собственный редирект | не нарушен (в обработчике нет `rollback` и собственного редиректа) | human review recommended |
| 18-02: удаление/вставка аккаунта, сравнение с сохранённым, UNIQUE/отказ по дубликату | не нарушен | human review recommended |
| 18-03: новый маршрут показа или ключ контекста ради ссылки | не нарушен (нового GET нет, используется `acct_label.phone_text`) | human review recommended |
| 18-03: прятать ссылку в `syncing`/`sync_failed`, оформлять её формой | не нарушен (по ссылке в каждой из трёх веток, `link_button`) | human review recommended |

### Антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Влияние |
|------|--------|--------|-------------|---------|
| (все изменённые файлы `app/` и `tests/` фазы) | — | `TBD` / `FIXME` / `XXX` в добавленных строках | — | совпадений нет (проверено по `git diff 103fa6d0..d197f956`) |

Заглушек нет: поля формы и ссылки питаются реальными данными (уровень 4). Находки code review (все `open`, консультативные, критических 0):

- WR-01 — кнопка «Сохранить» выровнена по низу подсказки (`align-items: flex-end` у `.form-wrapper`): косметика, цель не ломает; проверка раскладки включена в human-пункт про 320/375 px.
- WR-02 — у якоря `#phone` нет `scroll-margin-top` под липкой шапкой `[data-head]`: может перекрывать поле при прокрутке. Это не разрыв критерия (переход на экран и фокус по якорю работают, тест сквозного перехода зелёный), но реальное поведение прокрутки по этому критерию подтвердит только человек — вынесено в `human_verification`.
- WR-03 — умолчание `SyncStatusView.phone_is_manual = False`: сам план требует именно такое поле; риск — будущий пятый конструктор молча потеряет пометку. Тест на четыре конструктора есть. Не блокирует.
- IN-01…IN-03 — потеря фокуса после нажатия кнопки, форма `_screen_context`, литерал `64` в тесте: не затрагивают критерии.

### Человеческая проверка

Шесть пунктов перечислены в frontmatter (`human_verification`) — подмена htmx без перезагрузки, очистка с JS, 422 без плашки, якорь `#phone` (с учётом WR-02), автозаполнение, раскладка 320/375 px. Результаты за владельца не записаны: отметки и `result` остаются владельцу (`/gsd-verify-work 18`).

### Резюме

Цель фазы достигнута в части, проверяемой кодом и тестами: человек указывает, исправляет и стирает номер на обоих транспортах; ручной номер помечен «указан вручную» везде, где подпись рисуется разметкой; автоматический источник не перебивает ручной (`KEPT`) и снова вправе писать после очистки; имперсонация разрешена с записанной причиной, чужой аккаунт неотличим от несуществующего; числа сквозных гейтов пересчитаны и зелёные в полном прогоне. Разрывов и блокеров нет. Статус `human_needed` — из-за браузерных половин критериев (htmx-подмена, плашка аварии, прокрутка якоря, автозаполнение, раскладка на узких экранах), которые суита исполнить не может.

---

_Проверено: 2026-11-21_
_Верификатор: Claude (gsd-verifier)_
