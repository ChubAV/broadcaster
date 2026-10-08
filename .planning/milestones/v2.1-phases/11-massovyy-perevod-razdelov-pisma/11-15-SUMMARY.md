---
phase: 11-massovyy-perevod-razdelov-pisma
plan: 15
subsystem: payments
tags: [htmx, billing, yookassa, hx-redirect, open-redirect, gates, form_wrapper]

requires:
  - phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
    provides: "слой ответа respond()/location_response/_local_path, потолок незакрытых намерений PAY-01, запрет синхронизации очередью PAY-02, закрытый реестр уведомлений"
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "11-12/11-13: форма записи OWN_RESPONSE_EXITS в состоянии DECISION_OWNER_D08; 11-14: дерево HEAD e63e7e7"
provides:
  - "третий выход слоя ответа redirect_external: 204 + HX-Redirect только на адрес закрытого множества YOOKASSA_CONFIRMATION_HOSTS = {yoomoney.ru}; без htmx прежний 302"
  - "_confirmation_url: https, точный хост, без порта, без @ в узле, без обратной косой, ASCII, без управляющих символов"
  - "журнал payment_confirmation_url_rejected с хостом и без полного адреса; провал проверки — respond(/billing, payment_failed)"
  - "subscribe_to_plan на respond() и redirect_external(); голый 403 объявлен записью OWN_RESPONSE_EXITS (D-08)"
  - "форма оплаты на form_wrapper без цели и без hx-sync; data-plan-cta на обёртке-предке"
  - "первый случай ветки EXTERNAL реестра пар и тройная пара оплаты на документированном хосте"
affects: [11-16, 11-17, 11-18, 11-19, 11-20, 11-UAT, 11-SECURITY]

actuals:
  tokens: 10300
  tasks: 2
  commits: 5
plan_head_before: e63e7e7bb9b54e623bf6e9fd4f418e2b5871bad3

tech-stack:
  added: []
  patterns:
    - "Внешний переход — отдельная функция слоя ответа с закрытым множеством хостов константой рядом с проверкой, а не параметр respond() и не настройка окружения"
    - "Пары денежного маршрута идут через настоящий create_payment с подменой только сети ЮKassa: потолок PAY-01 проверяется тем же прогоном (незакрытое намерение заводится настоящим первым нажатием)"
    - "Журнал выхода, берущего логгер внутри вызова, снимается structlog.testing.capture_logs; caplog пуст без сборки приложения"

key-files:
  created: []
  modified:
    - app/pages/htmx.py
    - app/pages/billing.py
    - app/templates/billing/balance.html
    - tests/test_pages/test_htmx_response_layer.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_billing_subscription.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_billing_payment_errors.py
    - tests/test_pages/test_notices_channel.py
    - .planning/WINDOWS.md

key-decisions:
  - "Проверка хоста отвергает любой @ в узле (включая пустые данные пользователя https://@yoomoney.ru) и обратную косую черту: urlsplit и браузер читают https://evil.example\\@yoomoney.ru по-разному"
  - "Асимметрия принята и записана в SAFE_BY_NAME: путь без htmx отвечает прежним 302 без проверки хоста (источник — ответ SDK по TLS; правило границы фазы)"
  - "Прежние фикстуры yookassa.ru в тестах без htmx не тронуты; тройная пара и пары реестра стоят на yoomoney.ru"
  - "Пары оплаты используют настоящий create_payment с подменой сети ЮKassa; тройная пара подменяет create_payment в обработчике — её предмет развилка транспорта после создания"

patterns-established:
  - "Ветка EXTERNAL обхода пар утверждает 204, HX-Redirect посимвольно, отсутствие HX-Location и пустое тело"

requirements-completed: [FORM-05, FORM-04]

coverage:
  - id: D1
    description: "Третий выход redirect_external: на htmx 204 + HX-Redirect посимвольно без HX-Location и тела; без htmx 302 на любой адрес"
    requirement: FORM-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_an_external_address_leaves_by_the_redirect_header_only"
        status: pass
    human_judgment: false
  - id: D2
    description: "Адрес вне закрытого множества хостов (18 написаний подделки) не доходит до HX-Redirect; переход на /billing?notice=payment_failed; журнал несёт хост без полного адреса"
    requirement: FORM-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_confirmation_address_off_the_closed_host_set_never_reaches_the_header"
        status: pass
    human_judgment: false
  - id: D3
    description: "Оформление доступа — тройная пара: 302 / 204 + HX-Redirect / чужой хост → HX-Location с payment_failed"
    requirement: FORM-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_subscription.py#test_subscription_over_htmx_answers_the_triple_pair"
        status: pass
    human_judgment: false
  - id: D4
    description: "Отказы оплаты (выключены, незакрытое намерение через потолок PAY-01, сбой создания, нет сессии) на htmx — 204 + HX-Location с прежним кодом; без htmx прежний 302"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[subscribe_to_plan-*]"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_money_perimeter_gate.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Гейты: HX_HEADER_WRITES 3, SAFE_BY_NAME 2 записи, OWN_RESPONSE_EXITS_DECLARED 12 (D-08), NOT_YET_CONVERTED_COUNT 17, пары 33, вызовы перехода 60, места записи кода 1, вызывающие обёртки 17, блоки 9"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py; tests/test_pages/test_hx_location_destinations.py; tests/test_templates/test_htmx_markup_gates.py; tests/test_pages/test_notices_channel.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "Оформление доступа на тестовом ключе ЮKassa в браузере с htmx уводит на страницу подтверждения; фактический хост confirmation_url совпадает с закрытым множеством"
    requirement: FORM-05
    verification: []
    human_judgment: true
    rationale: "Ручной UAT критерия 2 ДО слияния: нужен настоящий платёж на тестовом ключе и наблюдение хоста; допущение A1 (закрытость множества {yoomoney.ru}) автоматически не проверяется. Исполнителем НЕ проведён"
  - id: D7
    description: "Кнопка оплаты сохраняет нажимаемую высоту 44px после переезда data-plan-cta на обёртку формы"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_touch_attribute_reaches_the_rendered_form"
        status: pass
    human_judgment: true
    rationale: "Правило CSS [data-plan-cta] .btn адресуется предком и проверяется по объявлению и разметке; отрисованная высота в браузере автоматически не измеряется"

duration: 67min
completed: 2026-09-16
status: complete
---

# Phase 11 Plan 15: Оплата — третий выход HX-Redirect с закрытым множеством хостов ЮKassa Summary

**Оформление доступа на htmx уводит на страницу ЮKassa заголовком `HX-Redirect` только после проверки хоста по закрытому множеству `{"yoomoney.ru"}`. Отказы оплаты и провал проверки уходят переходом на `/billing` с кодом реестра. Путь без JavaScript отвечает прежним 302, а голый 403 сверки источника объявлен изъятием D-08.**

## Performance

- **Duration:** 67 min
- **Started:** 2026-09-16T22:08:21Z
- **Completed:** 2026-09-16T23:15:33Z
- **Tasks:** 2
- **Files modified:** 11 (плюс запись `.planning/WINDOWS.md`)

## Accomplishments

- `app/pages/htmx.py`: `HX_REDIRECT_HEADER`, `YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})` константой с основанием (допущение A1, OQ3), `_confirmation_url`, `_host_for_the_journal`, `async def redirect_external(request, *, url, fallback, fallback_notice)`. Ответ несёт ровно один заголовок перехода.
- `subscribe_to_plan` переведён на слой ответа. «Нет сессии» уходит на `/login`. «Платежи выключены», «незакрытое намерение» и «сбой создания» уходят на `/billing` с `PAYMENT_DISABLED`, `PAYMENT_PENDING` и `PAYMENT_FAILED`. Успех идёт через `redirect_external(fallback="/billing", fallback_notice=PAYMENT_FAILED)`. `RedirectResponse` в обработчике не осталось. Порядок проверок, голый 403 и `create_payment` не тронуты.
- Форма оплаты собирается `form_wrapper(action='/billing/subscribe')`: без цели (`hx-swap="none"`), с `hx-disabled-elt` макроса и без `hx-sync`. `data-plan-cta` переехал на единственную обёртку-предок, и вхождение в шаблоне осталось одно.
- Тесты: 18 написаний подделки хоста, каждое отдельным случаем (суффикс, префикс, `user@`, `host@evil`, пустые данные пользователя, обратная косая, порт 8443 и 443, `http`, протокол-относительный и относительный адрес, CRLF, кириллица в пути и в хосте, `yookassa.ru`, пустая строка). Добавлены тройная пара и пять случаев реестра пар. Первый случай ветки `EXTERNAL` утверждает и отсутствие `HX-Location`.
- Числа поставлены прогонами покрасневших правил:
  - `HX_HEADER_WRITES` 2 → 3, `SAFE_BY_NAME` 1 → 2;
  - `OWN_RESPONSE_EXITS_DECLARED` 11 → 12, `NOT_YET_CONVERTED_COUNT` 18 → 17;
  - `POST_PAIR_CASES_DECLARED` 28 → 33, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 56 → 60, в карту назначений добавлен `/billing` → `billing/balance.html`;
  - `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 16 → 17, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 8 → 9;
  - `NOTICE_WRITE_PLACES` 4 → 1.

## Task Commits

1. **Задача 1: Третий выход слоя ответа.** RED `04fdaa9` (test), GREEN `efc7ae5` (feat).
2. **Задача 2: Оформление доступа — тройная пара, форма на обёртке, изъятие D-08.** RED `d5a3d87` (test), GREEN `b9db0db` (feat).
3. **Счётчик, найденный полным прогоном.** `a0f791a` (fix).

**Plan metadata:** коммит сводки и коммит метаданных следуют за этим файлом.

## TDD Gate Compliance

- **Задача 1, RED.** Прогон `-k "redirect_header_only or off_the_closed_host_set"` дал `19 failed, 26 deselected`. Все падения на утверждении «третьего выхода слоя ответа нет»; причинный литерал: `grep -c redirect_external app/pages/htmx.py` = 0. Запись собрана из JUnit XML в TAP, `check tdd-red-evidence` вернул `RED_EVIDENCE_OK`. RED гейтов замерен после появления выхода, до движения числа: `мест записи заголовка HX-* в app/ стало 3, а объявлено 2` и `правый операнд записи заголовка не принадлежит разрешённому множеству форм: app/pages/htmx.py:365 (redirect_external, HX-Redirect)`.
- **Задача 2, RED.** Прогон дал `7 failed`: тройная пара (`оформление на htmx ответило 302`, `assert 302 == 204`), пять случаев пар на половине htmx при зелёных половинах 302 и число реестра `33 != 28`. Причинный литерал: `grep -c redirect_external app/pages/billing.py` = 0. `RED_EVIDENCE_OK`.
- **GREEN.** Оба `feat(11-15)` следуют за своими `test(11-15)`. REFACTOR не понадобился.

## Files Created/Modified

- `app/pages/htmx.py` — третий выход, проверка хоста, поколения докстрингов модуля и `respond()` (третий выход введён; собственных выходов двенадцать).
- `app/pages/billing.py` — `subscribe_to_plan` на `respond()` и `redirect_external()`.
- `app/templates/billing/balance.html` — форма на `form_wrapper` внутри `<div data-plan-cta>`.
- `tests/test_pages/test_htmx_response_layer.py` — два правила третьего выхода.
- `tests/test_pages/test_htmx_gates.py` — `HX_HEADER_WRITES` с летописью, запись `SAFE_BY_NAME` с асимметрией, снят ключ оплаты из `NOT_YET_CONVERTED`, запись `OWN_RESPONSE_EXITS` в `DECISION_OWNER_D08`, поколение докстринга отрицательного контроля «третьей записи».
- `tests/test_pages/test_billing_subscription.py` — тройная пара на `yoomoney.ru`.
- `tests/test_pages/test_htmx_post_pairs.py` — пять случаев оформления и утверждения ветки `EXTERNAL`.
- `tests/test_pages/test_hx_location_destinations.py` — число вызовов и `/billing`.
- `tests/test_templates/test_htmx_markup_gates.py` — вызывающий `billing/balance.html`, два числа.
- `tests/test_pages/test_billing_payment_errors.py` — поколение обхода кодов причин.
- `tests/test_pages/test_notices_channel.py` — `NOTICE_WRITE_PLACES` 4 → 1.

## Decisions Made

- Множество хостов — константа в `htmx.py`, не настройка (OQ3). Хоста `yookassa.ru` в нём нет.
- Асимметрия проверки записана в `SAFE_BY_NAME`: путь 302 хост не проверяет.
- `payment_confirmation_url_rejected` пишется уровнем `error`, только с хостом. Если разборщик отказывает (`https://[::1/`), хост пишется `None`, а не 500.
- Пары оформления идут через настоящий `create_payment` с подменой сети. Тройная пара подменяет `create_payment` в обработчике, как предписал план.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing Critical] Проверка хоста закрыта шире перечня плана**
- **Found during:** задача 1.
- **Issue:** `urlsplit("https://evil.example\\@yoomoney.ru/").hostname` равен `yoomoney.ru`, а браузер (WHATWG) уходит на `evil.example`. Пустые данные пользователя (`https://@yoomoney.ru`) дают ложное `username` и прошли бы проверку «есть ли данные пользователя».
- **Fix:** отказ на любой `\` в значении и на любой `@` в узле. Оба случая добавлены в параметризацию. Разбор хоста для журнала завёрнут в `try`.
- **Files modified:** `app/pages/htmx.py`, `tests/test_pages/test_htmx_response_layer.py`.
- **Committed in:** `04fdaa9`, `efc7ae5`.

**2. [Rule 3 — Blocking] Снятие записи журнала через `capture_logs`, а не `caplog`**
- **Found during:** задача 1 (GREEN).
- **Issue:** при прямом вызове выхода без сборки приложения structlog не выводит в stdlib, и `caplog` пуст (18 failed при напечатанной записи).
- **Fix:** логгер берётся внутри вызова, поэтому прокси связывается под подменой, и `structlog.testing.capture_logs` его видит. Основание записано в докстринге правила: это обратный случай довода `tests/test_admin.py`.
- **Committed in:** `efc7ae5`.

**3. [Rule 3 — Blocking] Обход кодов причин оплаты читал литерал `/billing?notice={notices.X}`**
- **Found during:** задача 2 (прогон проверочного набора).
- **Issue:** `test_the_reason_codes_of_the_handlers_are_exactly_the_known_set` находил пустое множество, потому что адрес и код теперь отдельные аргументы слоя ответа.
- **Fix:** выражения читают `redirect="/billing", notice=notices.X` и пару `fallback="/billing", fallback_notice=notices.X`. Ожидаемое множество не тронуто.
- **Files modified:** `tests/test_pages/test_billing_payment_errors.py`.
- **Committed in:** `b9db0db`.

**4. [Rule 1 — Bug] Комментарий шаблона удваивал счёт атрибута**
- **Found during:** задача 2.
- **Issue:** новое поколение комментария называло `data-plan-cta` по имени, и `test_billing_payment_forms_carry_the_touch_attribute` насчитал 3 вместо 1.
- **Fix:** комментарий переписан без литерала имени, с объяснением почему.
- **Committed in:** `b9db0db`.

**5. [Rule 1 — Bug] Счётчик, не названный планом, устарел от собственной правки**
- **Found during:** полный прогон исполнителя (`1 failed, 3320 passed` за 35:19).
- **Issue:** `NOTICE_WRITE_PLACES` оставался 4, а стало 1: три адреса `/billing` с кодом собирает слой ответа.
- **Fix:** число поставлено прогоном, с летописью. Правило осиротевших кодов зелёное. Модуль `test_notices_channel.py` — 57 passed.
- **Committed in:** `a0f791a`.

---

**Total deviations:** 5 auto-fixed (1 Rule 2, 2 Rule 3, 2 Rule 1).
**Impact on plan:** все правки нужны для корректности либо безопасности. Поведение пути без JavaScript не менялось.

## Issues Encountered

- Сопутствующие числа, двинутые переводом и не названные планом, найдены прогонами: вызовы перехода, вызывающие и блоки обёртки, места записи кода. Каждое поставлено по отказу покрасневшего правила.
- Полный прогон шёл 22:38–23:13 UTC, вне окна известного красного правила обзора админки. Его не было среди падений.

## Verification

- `uv run pytest tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_htmx_gates.py -q` — 91 passed (задача 1).
- Проверочный набор задачи 2 плюс `test_billing_section.py`, `test_notices_surface.py`, `test_access_gate.py`, `test_htmx_response_layer.py` — 494 passed.
- `uv run pytest tests/test_templates/` — 218 passed.
- Полная суита без `tests/test_planning/`: `1 failed, 3320 passed` (rc=1, 35:19). Единственное падение — `NOTICE_WRITE_PLACES`, исправлено `a0f791a`, модуль перепрогнан: 57 passed. Полная суита после исправления повторно НЕ прогонялась.
- `uv run python -m compileall -q app main.py tests` — без ошибок. `graphify update .` выполнен.
- Все критерии приёмки обеих задач пройдены: греп-строки, `-k "redirect_header_only or off_the_closed_host_set"` 19 passed, `-k header_write` 4 passed, `-k triple_pair` 1 passed, `-k subscribe` 5 passed, `hx-sync` в `balance.html` = 0.

## User Setup Required

None — внешних настроек не требуется.

## Manual UAT — ОТКРЫТО (не проведено исполнителем)

**Критерий 2 фазы, ДО слияния ветки.** На стенде с тестовым ключом ЮKassa открыть `/billing` и нажать кнопку оплаты при живом htmx. Браузер должен уйти на страницу подтверждения ЮKassa. Во вкладке Network у `POST /billing/subscribe` ожидаются статус 204 и заголовок `HX-Redirect`. Фактический хост `confirmation_url` записать в `11-UAT.md` и сверить с `YOOKASSA_CONFIRMATION_HOSTS`. Если хост вне множества, остановить слияние и вернуть вопрос о множестве; в Loki это видно по `payment_confirmation_url_rejected`. Допущение A1 остаётся `[ASSUMED]`. Пункт записан в `.planning/WINDOWS.md` окном 87 (`unrun-verify`).

## Next Phase Readiness

- Готово к 11-16 (аккаунты). Денежный маршрут переведён, PAY-01 и PAY-02 не ослаблены.
- Блокер слияния фазы: ручной UAT критерия 2 (выше).

---
*Phase: 11-massovyy-perevod-razdelov-pisma*
*Completed: 2026-09-16*

## Self-Check: PASSED
