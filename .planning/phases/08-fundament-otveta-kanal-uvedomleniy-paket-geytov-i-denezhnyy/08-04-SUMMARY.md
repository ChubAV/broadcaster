---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 04
subsystem: ui
tags: [notices, aria-live, htmx, oob-swap, shell, gates, qual-03, found-06]
status: complete

requires:
  - phase: 08-01
    provides: "app/pages/htmx.py — respond() с обязательным redirect=, is_htmx, единственное на проект чтение признака htmx"
  - phase: 08-02
    provides: "app/pages/notices.py — закрытый реестр из 14 записей, notice_for(code) -> Notice | None"
  - phase: 07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii
    provides: "includes/htmx_config.html — правило \"422\" с признаком ошибки и предписание каналу видимости отказов"
provides:
  - "app/templates/includes/notice_area.html — две aria-live-области уведомления, единственный владелец их разметки"
  - "app/templates/includes/notice_oob.html — внеполосная форма подмены СОДЕРЖИМОГО областей"
  - "app/templates/includes/htmx_error_banner.html — две скрытые заготовки плашек отказа + два обработчика событий"
  - "Jinja-глобаль notice_for — единственный вход шаблона в закрытый реестр"
  - "app/pages/htmx.py::_notice_oob и _glue_notice — приклейка внеполосного блока к фрагменту в respond()"
  - "G-23 в tests/test_pages/test_shell.py — гейт шелла с группой -k control из четырёх тестов"
  - "tests/test_pages/test_notices_surface.py — утверждения о СБОРКЕ ответа с уведомлением"
affects: [08-06, 08-08, 08-09, 09, 10, 11, 12, 13, 14, 15]

tech-stack:
  added: []
  patterns:
    - "Область уведомления живёт в ШЕЛЛЕ: узел стабилен всегда, плашка — только по известному коду"
    - "Деление вежливое/настойчивое идёт по ВАРИАНТУ записи — существующей оси, а не новой"
    - "Внеполосный блок подменяет СОДЕРЖИМОЕ общей области; подмена узла остаётся законной для собственных узлов фрагмента"
    - "Плашка отказа приходит с сервера заранее отрисованной скрытой заготовкой; сценарий только снимает атрибут"
    - "Гейт по исходнику включения читает файл ПО ПУТИ, а не по константе — иначе группа контроля невыразима"

key-files:
  created:
    - app/templates/includes/notice_area.html
    - app/templates/includes/notice_oob.html
    - app/templates/includes/htmx_error_banner.html
    - tests/test_pages/test_notices_surface.py
  modified:
    - app/templates/base.html
    - app/templates/auth_base.html
    - app/pages/common.py
    - app/pages/htmx.py
    - tests/test_pages/test_shell.py

key-decisions:
  - "Заготовки плашек ОБЁРНУТЫ, а не выписаны классами: идентификатор и атрибут скрытия живут на обёртке, классы и role приходят от общего макроса — макрос этих параметров не принимает, а вторая копия его классов запрещена доктриной"
  - "Внеполосный блок объявлен ДВУМЯ ветками Jinja при одном рендерящемся блоке: цели две, запись попадает ровно в одну, а обе цели разом нарисовали бы плашку дважды и объявили её двумя тонами"
  - "Приклейка пересчитывает заголовок длины тела: заголовок, собранный вызывающим по исходному фрагменту, обрезал бы дописанный блок по прежней границе — и увидеть это можно было бы только по проводу"
  - "Приклейка к телу не-HTML поднимает ValueError и на потоковом ответе тоже: тела для дописывания у него нет вовсе"
  - "Гейт стоков разметки читает исходник С комментариями (как его близнец у htmx_config.html), а гейты событий и кода ответа — БЕЗ них: иначе снятая ветка оставалась бы 'найденной' в объяснении"
  - "Утверждение о недостижимости присланного значения записано сравнением с ответом БЕЗ параметра, а не отсутствием подстроки тега сценария: тег сценария есть в каждом ответе обоих шеллов"

requirements-completed: [FOUND-06, QUAL-03, GATE-08]

coverage:
  - id: D1
    description: "На каждой странице обоих шеллов существуют ровно две области уведомления — вежливая и настойчивая — каждая со своими признаками роли и живости"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_main_shell_carries_both_notice_regions"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_shell_carries_both_notice_regions"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_notice_area_has_single_source"
        status: pass
    human_judgment: false
  - id: D2
    description: "При отсутствии кода уведомления разметки плашки нет вовсе — область присутствует пустой"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_without_a_code_neither_region_draws_a_banner"
        status: pass
    human_judgment: false
  - id: D3
    description: "Неизвестный код не рисует ничего, и присланное значение не попадает в документ ни одним путём"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_an_unknown_code_draws_nothing_and_never_reaches_the_document"
        status: pass
      - kind: other
        ref: "число тегов сценария в ответе с параметром равно числу в ответе без него"
        status: pass
    human_judgment: false
  - id: D4
    description: "Плашка появляется РОВНО В ОДНОЙ из двух областей — в той, что соответствует варианту записи; оба шелла получают канал"
    requirement: FOUND-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_a_known_code_draws_in_the_polite_region_by_its_variant"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_a_known_error_code_draws_in_the_assertive_region"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_the_auth_shell_draws_a_known_code_too"
        status: pass
    human_judgment: false
  - id: D5
    description: "Внеполосный блок подменяет СОДЕРЖИМОЕ области, а не её узел, и проверен работой на настоящем ответе respond()"
    requirement: FOUND-06
    verification:
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_the_out_of_band_block_replaces_content_and_not_the_node"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_a_fragment_answer_carries_the_notice_out_of_band"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_the_block_targets_the_assertive_region_for_an_error_record"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_the_block_targets_the_polite_region_for_a_calm_record"
        status: pass
    human_judgment: false
  - id: D6
    description: "Приклейка не портит чужое тело молча: фрагмент не-HTML поднимает ValueError, фрагмент без кода остаётся посимвольно неизменным"
    requirement: FOUND-06
    verification:
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_a_non_html_fragment_refuses_the_glue_instead_of_corrupting_it"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_without_a_code_the_fragment_body_is_left_alone"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_ads_editor.py -q → 45 passed"
        status: pass
    human_judgment: false
  - id: D7
    description: "Плашки отказа сервера и обрыва связи приходят с сервера ЗАРАНЕЕ ОТРИСОВАННЫМИ и скрытыми в обоих шеллах"
    requirement: QUAL-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_main_shell_carries_both_failure_banners"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_shell_carries_both_failure_banners"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_failure_banner_has_single_source"
        status: pass
    human_judgment: false
  - id: D8
    description: "Обработчиков ДВА, и сценарий разметки не собирает и тела ответа не читает"
    requirement: QUAL-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_carries_both_handlers"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_touches_no_markup_sink"
        status: pass
    human_judgment: false
  - id: D9
    description: "Ответ 422 плашку аварии не поднимает: различение по коду ответа присутствует в сценарии"
    requirement: QUAL-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_failure_banner_tells_a_validation_answer_from_a_crash"
        status: pass
    human_judgment: false
  - id: D10
    description: "Зубы шелл-гейта G-23 доказаны, а не заявлены: гейт краснеет на трёх изменённых копиях включения и зеленеет на настоящем"
    requirement: GATE-08
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_negative_a_removed_send_error_handler_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_negative_a_removed_validation_check_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_negative_an_added_markup_sink_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_control_positive_the_untouched_banner_keeps_the_gates_green"
        status: pass
      - kind: command
        ref: "uv run pytest tests/test_pages/test_shell.py -k control -v → 4 selected, 4 passed"
        status: pass
    human_judgment: false
  - id: D11
    description: "Сценарий ДЕЙСТВИТЕЛЬНО поднимает плашку обрыва связи при выключенной сети, плашку отказа при 500 и не поднимает ничего при 422"
    requirement: QUAL-03
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет ни строчки JS: httpx отдаёт текст ответа, а не браузер с событиями. Гейты утверждают ДОСТАВКУ строк в документ и наличие обеих веток в исходнике; что сценарий делает в браузере — пункт 8 перечня ручного UAT (остановленный контейнер, ответ 500, форма с 422). Браузерный стенд отклонён на уровне вехи и отложен как E2E-01."
  - id: D12
    description: "Пять сегодняшних мест отрисовки плашки уехали в общую область (D-12), и человек видит исход там, где ждёт"
    requirement: FOUND-06
    verification: []
    human_judgment: true
    rationale: "Область заведена этим планом, но ПОТРЕБИТЕЛИ кодов переводятся планом 08-06: до него обработчики продолжают писать пять старых написаний, и переезд плашек с их прежних мест — предмет UI-суждения, а не теста. Проверять после слияния 08-06."

metrics:
  duration: "82 min"
  completed: "2026-08-28"
  tasks: 3
  commits: 4
  files-created: 4
  files-modified: 5

actuals:
  tokens: 22984
  tasks: 3
  commits: 4
---

# Phase 8 Plan 04: Видимая поверхность канала уведомлений Summary

**Канал обратной связи получил видимую поверхность: две `aria-live`-области в обоих шеллах с делением по варианту записи, внеполосный блок, подменяющий их СОДЕРЖИМОЕ на ответе `respond()`, и две заранее отрисованные скрытые заготовки плашек отказа с двумя обработчиками, различающими ошибку заполнения формы от аварии сервера ПО КОДУ ответа.**

## Performance

- **Duration:** 82 min
- **Started:** 2026-08-28T14:17:00Z
- **Completed:** 2026-08-28T15:39:00Z
- **Tasks:** 3 из 3
- **Files:** 9 (4 создано, 5 изменено)

## Accomplishments

- **Две области уведомления заведены одним владельцем и подключены в оба шелла.** Вежливая (`id="notice"`, роль `status`, живость `polite`) и настойчивая (`id="notice-alert"`, роль `alert`, живость `assertive`). Деление идёт по ВАРИАНТУ записи — существующей оси, которую макрос `components/alert.html` уже использует для вывода роли; вторая ось не заводится и разойтись с первой не может.
- **«Нет кода — нет плашки» стало машинным.** Значение параметра адреса только ВЫБИРАЕТ запись и в разметку не уходит ни одним путём. Неизвестный код не рисует ничего; недостижимость доказана сравнением числа тегов сценария в ответе с параметром и без него, а не отсутствием подстроки.
- **Узел области существует всегда, и это записано абзацем прямо в шаблоне.** Правило «нет кода — нет разметки» относится к ПЛАШКЕ; стабильный узел нужен внеполосной подмене по идентификатору, и следующий читатель, увидев пустой `div`, не снимет его как мусор.
- **Граница, оставленная планом 08-01 в докстринге `respond()`, закрыта.** `_notice_oob` собирает блок окружением Jinja по приёму `accounts.py::_connect_status`, `_glue_notice` дописывает его к телу фрагмента, пересчитывая заголовок длины. Приклейка к телу не-HTML поднимает `ValueError`, а не портит чужое тело молча.
- **Граница требования подмены содержимого названа прямо в шаблоне**, чтобы гейт плана 08-08 не расширили на весь проект: четыре внеполосных блока редактора объявлений объявляют подмену УЗЛА, работают и фазой не правятся.
- **Плашки отказа приходят с сервера скрытыми, сценарий только снимает атрибут.** Ноль стоков разметки, ноль чтений тела ответа, ранний выход по коду 422 первым действием обработчика.
- **Зубы G-23 доказаны контролем.** Чтение исходника вынесено в функцию, принимающую ПУТЬ; три изменённые копии включения краснеют, настоящий файл зелёный.

## Task Commits

| Task | Gate | Name | Commit | Files |
|------|------|------|--------|-------|
| 1 | — | Две aria-live-области в обоих шеллах и вход шаблона в реестр | `6b73be2` | `includes/notice_area.html`, `base.html`, `auth_base.html`, `common.py`, `test_shell.py` |
| 2 | RED | Красные утверждения о внеполосной форме уведомления | `fee7fb1` | `tests/test_pages/test_notices_surface.py` |
| 2 | GREEN | Внеполосная форма и её приклейка в `respond()` | `0297075` | `includes/notice_oob.html`, `app/pages/htmx.py` |
| 3 | — | Плашки отказа, два обработчика, шелл-гейт G-23 | `6d2eaf2` | `includes/htmx_error_banner.html`, `base.html`, `auth_base.html`, `test_shell.py` |

## TDD Gate Compliance

| Gate | Commit | Статус |
|------|--------|--------|
| RED | `fee7fb1` `test(08-04)` | Пройден — 5 из 7 утверждений красные по построению (формы и приклейки не существовало); два оставшихся зелёными названы таковыми в своих докстрингах как ОХРАННЫЕ (без признака htmx фрагмент не собирается, код едет адресом) |
| GREEN | `0297075` `feat(08-04)` | Пройден — 7/7 зелёных |
| REFACTOR | — | Не потребовался: `_notice_oob` и `_glue_notice` написаны в окончательной форме, дублирования не возникло. Коммит без изменений не заводился. |

Последовательность `test(...)` → `feat(...)` соблюдена; нарушений нет.

## Verification Results

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_shell.py -q` | **137 passed**, exit 0 |
| `uv run pytest tests/test_pages/test_notices_surface.py -v` | **7 passed**, exit 0 |
| `uv run pytest tests/test_pages/test_shell.py -k control -v` | **4 selected, 4 passed**, exit 0 (требовалось ≥4) |
| `uv run pytest tests/test_pages/ tests/test_templates/ -q` | **1326 passed**, exit 0 |
| `uv run pytest tests/test_pages/test_ads_editor.py -q` | 45 passed — форма внеполосного ответа редактора не тронута |
| `uv run pytest tests/test_pages/test_htmx_response_layer.py -q` | 20 passed — слой ответа 08-01 не сломан |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `grep -rn 'HX-Request' app/ --include=*.py` | **1 вхождение** — `app/pages/htmx.py:33`; второго чтения не заведено |
| Ручной обход пункта 8 UAT | **не выполнен** — предмет ручной проверки после слияния волны (см. `coverage` D11) |

### Критерии приёмки по исходникам

| Критерий | Факт |
|---|---|
| `grep -c 'includes/notice_area.html'` в `base.html` / `auth_base.html` | 1 / 1 |
| `grep -c 'aria-live="polite"'` / `'aria-live="assertive"'` в `notice_area.html` | 1 / 1 |
| `grep -c 'notice_for' app/pages/common.py` | 2 (≥1) |
| `grep -c '<!--'` в `notice_area.html` / `htmx_error_banner.html` | 0 / 0 |
| `grep -c 'hx-swap-oob="innerHTML:#notice"'` / `'…#notice-alert"'` в `notice_oob.html` | 1 / 1 |
| `grep -c 'notice_oob.html' app/pages/htmx.py` | 1 (≥1) |
| `grep -c 'includes/htmx_error_banner.html'` в `base.html` / `auth_base.html` | 1 / 1 |
| `grep -c 'htmx:responseError'` / `'htmx:sendError'` в `htmx_error_banner.html` | 1 / 1 |
| `grep -c 'innerHTML' / 'outerHTML' / 'insertAdjacentHTML' / 'document.write'` в `htmx_error_banner.html` | 0 / 0 / 0 / 0 |
| `grep -c '422'` в `htmx_error_banner.html` | 4 (≥1) |

## Success Criteria

- [x] Две области уведомления существуют в обоих шеллах, различаются признаками роли и живости и пусты без кода
- [x] Внеполосная форма подменяет содержимое областей и проверена работой на настоящем ответе `respond()`
- [x] Заготовки плашек приходят с сервера скрытыми, сценарий только снимает атрибут
- [x] Ответ 422 плашку аварии не поднимает — различение машинно утверждено
- [x] Зубы G-23 доказаны группой контроля: гейт краснеет на трёх изменённых копиях включения и зеленеет на настоящем

## Decisions Made

1. **Заготовки плашек ОБЁРНУТЫ, а не выписаны классами.** Макрос `alert()` параметров идентификатора и скрытия не принимает, а вторая копия его классов в шелле запрещена доктриной единственного источника. Идентификатор и атрибут скрытия живут на обёртке; классы и роль приходят от макроса. Названо абзацем в шаблоне.
2. **Внеполосный блок объявлен двумя ветками Jinja, рендерится один.** Целевых областей две, запись попадает ровно в одну, и выбирает её вариант. Оба блока разом нарисовали бы плашку дважды и объявили её двумя разными тонами.
3. **Заголовок длины тела пересчитывается при приклейке.** Заголовок, собранный вызывающим по ИСХОДНОМУ фрагменту, обрезал бы дописанный блок ровно по прежней границе — ответ ушёл бы усечённым, и увидеть это можно было бы только по проводу, а не в объекте ответа. Утверждение добавлено в тест приклейки.
4. **Приклейка отказывает и на потоковом ответе**, а не только на не-HTML: у такого ответа собранного тела нет вовсе, и «дописать» к нему нечего.
5. **Гейты читают исходник по-разному, и это решение.** Стоки разметки ищутся в исходнике С комментариями (форма близнеца у `htmx_config.html`: сток, «объяснённый» в комментарии, приехал бы в код одним движением правки). События и код ответа ищутся БЕЗ комментариев: иначе объяснение, называющее снятую ветку, оставляло бы гейт зелёным — ровно то, что доказывают два отрицательных контроля.
6. **Признаки живости и имена событий набраны в комментариях СЛОВАМИ, а не литералами.** Критерии приёмки считают вхождения в файле целиком; объяснение, набранное проверяемой строкой, роняет собственный гейт. Урок взят у `htmx_config.html` и у реестра уведомлений, которые не называют снятые написания их литералами.

## Deviations from Plan

### 1. [Rule 3 — Блокирующее] Критерий «подстроки `<script>` из параметра в теле нет» невыразим и заменён тремя утверждениями

- **Найдено при:** Task 1 (написание утверждения о неизвестном коде)
- **Проблема:** критерий приёмки требует, чтобы при `GET /profile?notice=%3Cscript%3E` подстроки `<script>` в теле не было. Оба шелла несут инлайн-сценарий миграционной очистки (`includes/htmx_config.html`), то есть открывающий тег сценария БЕЗ атрибутов присутствует в каждом ответе независимо от адреса. Утверждение было бы красным всегда — то есть не утверждением, а поломкой.
- **Исправление:** проверяемое свойство записано тремя утверждениями, вместе строгими: (а) плашки нет ни в одной из областей; (б) ЭКРАНИРОВАННОЙ формы присланного значения (`&lt;script&gt;`) в документе нет — её появление означало бы, что значение уехало в разметку и спаслось лишь автоэкранированием; (в) число тегов сценария в ответе С параметром РАВНО числу в ответе БЕЗ него, то есть присланное значение не добавило в документ ни одного узла. Последнее и есть недостижимость, которой требует T-08-08.
- **Файлы:** `tests/test_pages/test_shell.py`
- **Проверка:** `test_an_unknown_code_draws_nothing_and_never_reaches_the_document` зелёный; довод выписан абзацем в докстринге теста, чтобы следующий читатель не счёл замену послаблением.
- **Коммит:** `6b73be2`

### 2. [Rule 3 — Блокирующее] Литералы проверяемых строк убраны из комментариев новых включений

- **Найдено при:** Task 1 (первая сверка критериев приёмки по исходникам)
- **Проблема:** первая редакция комментариев называла признаки живости и путь включения их собственными литералами. `grep -c 'aria-live="polite"'` дал 2 вместо 1, `aria-live="assertive"` — 3 вместо 1, а `grep -c 'includes/notice_area.html' auth_base.html` — 2 вместо 1. Гейты плана считают вхождения в файле ЦЕЛИКОМ, поэтому объяснение роняло собственный гейт.
- **Исправление:** признаки и имена событий набраны в комментариях словами («живость polite», «событие отказа отправки»), путь включения из комментария шелла убран. Причина записана отдельным абзацем в `notice_area.html` и в `htmx_error_banner.html` — иначе следующий редактор вернул бы литерал ради читаемости.
- **Файлы:** `app/templates/includes/notice_area.html`, `app/templates/auth_base.html`, `app/templates/includes/htmx_error_banner.html`
- **Проверка:** все десять греп-критериев трёх задач сверены и совпадают (таблица выше).
- **Коммит:** `6b73be2`, `6d2eaf2`

### 3. [Rule 2 — Missing critical] Пересчёт заголовка длины тела при приклейке

- **Найдено при:** Task 2 (GREEN)
- **Проблема:** план описывает приклейку как «тело ответа фрагмента дополняется отрендеренным блоком» и о заголовке длины не говорит. Ответ Starlette собирает заголовок длины в момент построения — по ИСХОДНОМУ телу. Дописанный блок при неизменном заголовке был бы обрезан ровно по прежней границе: клиент получил бы усечённую разметку, а в объекте ответа всё выглядело бы правильно.
- **Исправление:** `_glue_notice` пересчитывает заголовок длины; утверждение о равенстве заголовка и фактической длины добавлено в `test_a_fragment_answer_carries_the_notice_out_of_band`.
- **Файлы:** `app/pages/htmx.py`, `tests/test_pages/test_notices_surface.py`
- **Коммит:** `0297075`

### 4. [Rule 2 — Missing critical] Гейт на чтение ТЕЛА пришедшего ответа

- **Найдено при:** Task 3
- **Проблема:** строка T-08-20 реестра угроз объявляет мерой «сценарий читает из ответа ТОЛЬКО код состояния», но перечень утверждений задачи закрывал лишь стоки разметки и наличие сравнения с 422. Чтение тела чужого ответа не было запрещено ничем — а именно оно выносит наружу внутреннее устройство.
- **Исправление:** в `test_the_failure_banner_touches_no_markup_sink` добавлено утверждение об отсутствии чтения тела ответа в сценарии, с выписанным основанием.
- **Файлы:** `tests/test_pages/test_shell.py`
- **Коммит:** `6d2eaf2`

### 5. [Rule 2 — Missing critical] Отказ приклейки на потоковом ответе

- **Найдено при:** Task 2 (GREEN)
- **Проблема:** план требует `ValueError` для ответа с типом содержимого не-HTML. Ответ HTML, но ПОТОКОВЫЙ, собранного тела не имеет вовсе — попытка дописать к нему подняла бы `TypeError` в неочевидном месте либо, при небрежной реализации, прошла бы молча.
- **Исправление:** отсутствие собранного тела поднимает `ValueError` с текстом, называющим причину.
- **Файлы:** `app/pages/htmx.py`
- **Коммит:** `0297075`

---

**Total deviations:** 5 (2 × Rule 3 «блокирующее», 3 × Rule 2 «недостающее критическое»).
**Impact on plan:** расширения объёма нет. Ни один файл вне `files_modified` плана не тронут; `app/models/payment.py` и `app/services/payment_service.py` (предмет параллельного плана 08-05) не открывались. Оба блокирующих исправления вызваны столкновением буквы критерия с фактическим устройством документа и с формой гейтов; оба разрешены так, чтобы проверяемое СВОЙСТВО осталось утверждённым, а не ослабленным.

## Issues Encountered

**`tests/test_planning/test_state_progress_matches_roadmap.py` красный, и это НЕ дефект этого плана.** Полный прогон проекта (`uv run pytest tests/ -q`) даёт 2398 passed, 1 failed; единственный отказ — расхождение `Progress:` в `.planning/STATE.md` с выведенным из `.planning/ROADMAP.md` счётом.

Отказ **предшествует** работе этого плана и лежит **вне его прав на запись**:

- `git diff --name-only <база> HEAD -- .planning/` — **пусто**: план не тронул ни одного планировочного файла;
- последний коммит, писавший `STATE.md`, — `fcc41f5 docs(phase-08): update tracking after wave 1`, то есть **сам базовый коммит этого рабочего дерева**; в нём `STATE.md` несёт `Progress: [░░░░░░░░░░] 0%` при исполненной волне 1;
- диспетчер прямо запретил исполнителю трогать `STATE.md` и `ROADMAP.md` — они обновляются централизованно после слияния волны.

Расхождение закрывается тем же обновлением, которым диспетчер закрывает волну 2. Чинить его здесь значило бы писать в файл, единственным писателем которого исполнитель не является, и получить конфликт слияния с соседним деревом.

**Прочего не было.** Ни одного аутентификационного гейта, ни одной установки пакета: рамка вехи «ни одной новой Python-зависимости» соблюдена, `pyproject.toml` не тронут.

## Known Stubs

Продуктовых заглушек нет. Три границы отложены ЯВНЫМИ решениями и записаны словами там, где их встретит следующий читатель:

| Граница | Файл | Владелец |
|---|---|---|
| Коды уведомления никто ещё не ЗАПИСЫВАЕТ: восемь обработчиков продолжают писать пять старых написаний, поэтому область на сегодняшних маршрутах пуста | план 08-06 | план 08-06 |
| Гейт «внеполосный блок обязан подменять содержимое» — форма объявлена, машинное правило пишется отдельно | `includes/notice_oob.html` (комментарий о границе) | план 08-08 |
| Автоматическое сокрытие снятой плашки отказа: третий обработчик не заводится, рамка вехи ограничивает число новых сценариев | `includes/htmx_error_banner.html` (абзац «ЧЕГО СЦЕНАРИЙ НЕ ДЕЛАЕТ») | допущение плана, к обсуждению при заметном накоплении |

Ни одна из трёх не мешает цели плана: поверхность канала существует и проверена работой на настоящем ответе `respond()`.

## Threat Flags

Новой поверхности сверх реестра угроз плана не заведено. Две строки реестра уточнены реализацией:

| Строка | Уточнение |
|---|---|
| T-08-08 | недостижимость утверждается СРАВНЕНИЕМ ответов с параметром и без него, а не отсутствием подстроки: в документе обоих шеллов тег сценария присутствует всегда, и утверждение о его отсутствии было бы красным по построению |
| T-08-20 | к мере добавлено машинное утверждение об отсутствии чтения ТЕЛА пришедшего ответа: перечень задачи закрывал только стоки разметки, а вынести внутреннее устройство наружу способно именно тело |

## Authentication Gates

None.

## User Setup Required

None — внешней настройки не требуется. Новых переменных окружения, ключей и сервисов план не вводит.

## Next Phase Readiness

**Готово для следующих планов фазы:**

- **08-06** может переписывать восемь обработчиков на `?notice=` и снимать пять частных написаний: область отрисовки существует в обоих шеллах, а `respond(notice=…)` доводит код и до адреса, и до внеполосного блока.
- **08-08** может писать гейт «внеполосный блок подменяет содержимое»: форма объявлена, а граница её применимости выписана в шаблоне словами — гейт, распространённый на редактор объявлений, покраснел бы на работающем коде.
- **08-09** может писать гейт запрета `|safe` в шаблонах: ни одно из трёх новых включений его не использует.

**Что закрылось у соседа по волне 1:** пункт `D7` покрытия плана 08-01 («отвергнутое действие уводит на экран, где отказ НАЗВАН СЛОВОМ») стал проверяем целиком — область `#notice` существует, а код `impersonation_forbidden` в реестре 08-02 есть. Проверять глазами после слияния волны.

**Что остаётся человеку:** пункт 8 перечня ручного UAT — остановленный контейнер `web` (плашка обрыва связи), ответ 500 (плашка отказа сервера, а не обрыва) и форма, отдающая 422 (плашки аварии быть НЕ должно). Суита не исполняет ни строчки JS и доказать это не может.

## Self-Check: PASSED

- `app/templates/includes/notice_area.html` — FOUND
- `app/templates/includes/notice_oob.html` — FOUND
- `app/templates/includes/htmx_error_banner.html` — FOUND
- `tests/test_pages/test_notices_surface.py` — FOUND
- Коммиты `6b73be2`, `fee7fb1`, `0297075`, `6d2eaf2` — все четыре FOUND в `git log`
- Все `<acceptance_criteria>` всех трёх задач перепроверены после завершения работ (таблицы выше); весь блок `<verification>` плана перезапущен и зелёный
- Единственный красный тест полного прогона (`tests/test_planning/`) предшествует плану и лежит вне его прав на запись — разобран в «Issues Encountered»

---
*Phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy*
*Completed: 2026-08-28*
