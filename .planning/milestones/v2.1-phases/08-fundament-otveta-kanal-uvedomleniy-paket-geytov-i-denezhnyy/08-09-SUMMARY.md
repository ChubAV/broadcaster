---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 09
subsystem: testing
tags: [pytest, jinja2, htmx, xss, autoescape, markupsafe, ast, inventory-gate]

requires:
  - phase: 08-04
    provides: "Области уведомления в обоих шеллах и внеполосная подмена — та поверхность, ради которой три инвентаря объявлены нулями"
  - phase: 08-06
    provides: "Форма гейта, живущего вне области собственного поиска, и правило «свойство названо в докстринге»"
  - phase: 08-10
    provides: "Форма группы контроля: каждая подмена несёт утверждение «подмена что-то изменила»; запрет очереди на непрозрачном адресе"
provides:
  - "G-14: ESCAPE_ESCAPES = 0 и MARKUP_BUILDERS = 0 — два инвентаря, закрывающие два разных пути внесения готовой разметки"
  - "G-15: REQUEST_PARAM_ATTRS = 0 плюс исполнимое правило сериализации в JSON на вырост"
  - "Утверждение о включённом автоматическом экранировании окружения шаблонов"
  - "G-21: PERMANENT_POLLS (8) и TERMINATING_POLLS (2), объединение равно найденному обходом; останов опроса доказан положением признака внутри условия"
  - "G-22: MANUAL_FETCH_PLACES = 6 как убывающий счётчик прогресса вехи с потолком MANUAL_FETCH_CEILING_AT_PHASE_08"
  - "13 тестов группы контроля на два файла — доказательство того, что оба гейта краснеют"
affects: [09, 10, 11, 12, 13, 14, 15]

actuals:
  tokens: 27000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Гейт живёт в tests/ и ищет в app/ — структурная невозможность удовлетворить собственный шаблон поиска"
    - "Разборщик принимает исходники словарём, а не читает дерево сам — только так группа контроля подаёт изменённую копию"
    - "Убывающий счётчик с отдельным потолком, чьё имя называет фазу: поднять его молча нельзя"

key-files:
  created:
    - tests/test_templates/test_htmx_markup_security.py
  modified:
    - tests/test_templates/test_htmx_inventory.py

key-decisions:
  - "Инвентарь обработчиков событий закрывает семейство hx-on, а не HTML-атрибуты onclick: последних сегодня четыре, и объявленный по ним ноль был бы красным по неустранимой причине"
  - "MARKUP_BUILDERS собирается по дереву разбора и учитывает ввоз под псевдонимом — вызов псевдонима прошёл бы мимо гейта, знающего только имя"
  - "Объединение множеств опроса приравнено множеству, найденному обходом (10 фрагментов), а не POLL_PLACES (8): критерий плана назвал число одного механизма инвентаря hx-get"
  - "Границы опрашивающего множества относительно инвентаря hx-get утверждаются неравенствами, а не тождеством — тождество покраснело бы на условном месте без расписания"
  - "Потолок MANUAL_FETCH_CEILING_AT_PHASE_08 заведён отдельной величиной: без него убывающий счётчик чинится поднятием константы и перестаёт убывать"

patterns-established:
  - "Именованный ноль с летописью и собственным обходом — третье применение формы SERVER_SIDE_VALIDATION_RESPONSES"
  - "Ключ записи инвентаря — путь файла плюс порядковый номер вхождения; тест доказывает, что совпадающие тексты в дереве ЕСТЬ, иначе он зелен по построению"
  - "Пара тестов на убывающий счётчик: «не выросло» читается как находка, «равно объявленному» — как задача записать прогресс"

requirements-completed: [GATE-07, GATE-08]

coverage:
  - id: D1
    description: "Ноль конструкций снятия экранирования в шаблонах — именованный ноль, собранный собственным обходом с вырезанием комментариев обоих видов"
    requirement: GATE-07
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_no_template_removes_automatic_escaping"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_control_negative_an_unescaped_value_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_control_positive_a_construct_inside_a_comment_keeps_the_gate_green"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ноль сборок безопасной разметки в коде приложения — по дереву разбора, с учётом ввоза под псевдонимом"
    requirement: GATE-07
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_no_application_module_builds_safe_markup"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_control_negative_a_markup_builder_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ноль атрибутов параметров запроса и обработчиков событий htmx плюс исполнимое правило сериализации в JSON"
    requirement: GATE-07
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_no_markup_declares_request_parameters_or_event_handlers"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_request_param_attributes_go_through_json_serialisation"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_control_negative_an_unserialised_request_param_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_control_negative_an_inline_event_handler_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D4
    description: "Автоматическое экранирование окружения шаблонов утверждается чтением свойства, а не подразумевается умолчанием библиотеки"
    requirement: GATE-07
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_security.py#test_the_template_environment_escapes_by_default"
        status: pass
    human_judgment: false
  - id: D5
    description: "Каждый опрашивающий фрагмент отнесён к бессрочному опросу либо к опросу до завершения; объединение равно найденному обходом"
    requirement: GATE-08
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_every_polling_fragment_is_classified"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_the_two_poll_sets_do_not_overlap"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_no_two_polling_fragments_collapse_into_one_key"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_negative_an_unclassified_polling_fragment_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D6
    description: "Опрос до завершения имеет доказанный останов: признак опроса стоит внутри условия шаблонизатора в том же теге"
    requirement: GATE-08
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_every_terminating_poll_declares_its_stop"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_negative_a_terminating_poll_without_its_condition_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_positive_a_tree_without_polling_fragments_keeps_the_stop_gate_green"
        status: pass
    human_judgment: false
  - id: D7
    description: "Число мест ручной сборки запроса объявлено убывающим счётчиком: гейт краснеет на росте факта, на падении факта и на росте объявления"
    requirement: GATE-08
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_manual_request_assembly_never_grows"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_manual_request_assembly_matches_the_declared_count"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_the_declared_manual_fetch_ceiling_never_rises"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_inventory.py#test_control_negative_raising_the_declared_ceiling_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D8
    description: "Граница пакета: обычные HTML-атрибуты обработчиков событий (четыре места) сознательно оставлены вне инвентаря до Фаз 12/13"
    requirement: GATE-07
    verification: []
    human_judgment: true
    rationale: "Решение о границе правила, а не проверяемое свойство. Человек обязан подтвердить, что четыре onclick/onsubmit в connect_tg_user.html и connect_max.html допустимо оставить незакрытыми до перевода этих экранов на фрагменты, а не закрывать их убывающим счётчиком уже сейчас."

duration: 46 min
completed: 2026-08-28
status: complete
---

# Phase 8 Plan 09: Гейты безопасности разметки и инвентарь опроса — Summary

**Три именованных нуля безопасности разметки (снятие экранирования, сборка безопасной разметки, атрибуты параметров запроса) плюс классификация десяти опрашивающих фрагментов с доказанным остановом и убывающий счётчик ручной сборки запроса с потолком, который нельзя поднять молча.**

## Performance

- **Duration:** 46 min
- **Started:** 2026-08-28T20:25:00Z
- **Completed:** 2026-08-28T21:11:24Z
- **Tasks:** 2
- **Files modified:** 2 (1 создан, 1 дописан)

## Accomplishments

- **Три инвентаря безопасности объявлены именованными нулями и доказали зубы.** `ESCAPE_ESCAPES = 0` и `MARKUP_BUILDERS = 0` закрывают ДВА РАЗНЫХ пути внесения готовой разметки: конструкции шаблонизатора в разметке и сборку безопасной строки в Python. Второй путь первому невидим — значение, объявленное безопасным на стороне кода, доезжает до шаблона обычной подстановкой. `REQUEST_PARAM_ATTRS = 0` закрывает второй слой экранирования: содержимое атрибута параметров запроса и атрибута обработчика события разбирается рантаймом htmx как выражение, и автоматическое экранирование шаблонизатора его не касается.
- **Автоматическое экранирование окружения утверждается, а не подразумевается.** Без этого утверждения все три нуля остались бы честными нулями при полностью открытой поверхности — снимать было бы просто нечего. Свойство читается у объекта окружения; умолчание библиотеки есть свойство версии зависимости, а не проекта.
- **Гейт структурно не может удовлетворить собственный шаблон поиска.** Файл живёт в `tests/`, область поиска — ровно `app/templates` и `app/**/*.py`. Свойство названо в шапке файла отдельным абзацем с предупреждением, потому что «прибраться» и перенести файл под `app/` значит отменить не расположение, а само правило.
- **Десять опрашивающих фрагментов классифицированы, и объединение объявленных множеств РАВНО найденному обходом.** Опрос, добавленный будущей фазой, не попадёт ни в одно множество и уронит тест вместо того, чтобы оказаться бессрочным по умолчанию. У обоих опросов до завершения останов ДОКАЗАН положением признака опроса внутри условия шаблонизатора в том же теге — ответ со статусом «готово» признака не несёт, и подменённый узел перестаёт опрашивать сам. Доказательство читается из исходника и не требует исполнения ни строчки JS.
- **Убывающий счётчик ручной сборки запроса имеет ТРИ зуба, а не один.** Рост факта краснит `test_manual_request_assembly_never_grows`; падение факта краснит `test_manual_request_assembly_matches_the_declared_count` сообщением-задачей («число упало до N — опустите константу»); рост ОБЪЯВЛЕНИЯ краснит `test_the_declared_manual_fetch_ceiling_never_rises`. Третий зуб — прямой ответ на стандарт волны: без него седьмое место чинится поднятием константы до семи, и счётчик прогресса тихо становится описанием того, что есть.
- **Тринадцать тестов группы контроля на два файла.** Каждый гейт получает подставное дерево с настоящим нарушением и обязан покраснеть; два положительных контроля доказывают, что он не краснеет зря (проза в комментарии остаётся зелёной; пустое множество кандидатов остаётся зелёным). Дополнительно оба положительных контроля утверждают, что обход НЕ ПУСТ — ноль, полученный из пустого обхода, неотличим от нуля по существу.

## Task Commits

1. **Task 1: Гейты безопасности шаблонов — три именованных нуля и их зубы** — `acfe7dc` (test)
2. **Task 2: Гейт останова опроса и убывающий счётчик ручной сборки запроса** — `5b50637` (test)

## Files Created/Modified

- `tests/test_templates/test_htmx_markup_security.py` (создан, 764 строки) — G-14 и G-15: три именованных нуля, утверждение об автоматическом экранировании, исполнимое правило сериализации в JSON, шесть контролей.
- `tests/test_templates/test_htmx_inventory.py` (дописан, +743 строки) — G-21 и G-22: `POLLING_FRAGMENTS = 10`, `PERMANENT_POLLS`, `TERMINATING_POLLS`, `MANUAL_FETCH_PLACES = 6`, `MANUAL_FETCH_CEILING_AT_PHASE_08 = 6`, `MANUAL_FETCH_SITES` и семь контролей. Дописано в действующий файл, а не заведено соседним: обе группы считают то же дерево теми же разборщиками, и вторая копия `_strip_comments` разошлась бы с первой молча.

## Decisions Made

- **Инвентарь обработчиков событий закрывает семейство `hx-on`, а не HTML-атрибуты `onclick`.** Последних сегодня четыре (`accounts/connect_tg_user.html` — три, `accounts/connect_max.html` — один), и объявленный по ним ноль был бы КРАСНЫМ в момент написания по причинам, которых исполнитель этого плана устранить не может: оба экрана переезжают на фрагменты Фазами 12 и 13. Прохибиция GATE-08 того же плана запрещает такую клаузу прямо. Граница выписана в разделе «⚠️ ЧЕГО ГЕЙТ НЕ ВИДИТ» шапки файла, а не растворена. Приемочные критерии плана называют именно `hx-on:`, то есть решение совпадает с ними, а не расходится.
- **`MARKUP_BUILDERS` собирается по ДЕРЕВУ РАЗБОРА и учитывает ввоз под псевдонимом.** Текстовый поиск краснел бы на правку документации и молчал бы на переезд вызова в переменную. Ввоз `from markupsafe import Markup as X` с последующим вызовом `X(...)` прошёл бы мимо гейта, знающего только имя, — та же слепая зона, которую план 08-10 закрыл запретом псевдонима импорта создания платежа; имя, связанное ввозом, добавляется к искомым.
- **Границы опрашивающего множества относительно инвентаря `hx-get` утверждаются НЕРАВЕНСТВАМИ.** `POLL_PLACES <= POLLING_FRAGMENTS <= POLL_PLACES + CONDITIONAL_PLACES`. Тождество `POLLING_FRAGMENTS == POLL_PLACES + CONDITIONAL_PLACES` истинно сегодня (оба условных места несут расписание), но покраснело бы на первом же условном месте БЕЗ расписания — то есть на правке, ничего не ломающей.
- **Потолок ручной сборки заведён ОТДЕЛЬНОЙ величиной с именем фазы.** Прецедент формы — долговая летопись `test_declared_invariants.py`, чей потолок опускался 21 → 20 тем же коммитом, который снял запись долга. Поднять `MANUAL_FETCH_CEILING_AT_PHASE_08` молча нельзя: величина утверждает собственным именем, чему она была равна в Фазе 8.
- **`_strip_comments` взят ИМПОРТОМ, а не второй копией.** Доктрина единственного источника; тот же ход, что у `test_htmx_response_contract.py`, ввозящего `_htmx_config_of` из `test_shell.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Критерий «объединение равно `POLL_PLACES`» неудовлетворим как написан**

- **Найдено при:** Task 2
- **Критерий:** `<acceptance_criteria>` задачи 2, строка «Behavior: объединение двух множеств опросов равно множеству, найденному обходом (`POLL_PLACES`)».
- **Проблема:** `POLL_PLACES = 8` — число мест ОДНОГО механизма инвентаря `hx-get` (безусловное расписание). Образец опроса до завершения, названный тем же планом в `<read_first>` (`app/templates/account_groups/partials/sync_result.html:50`), в этот механизм не входит: его атрибуты собраны Jinja-условием, то есть он относится к механизму 3 (`CONDITIONAL_PLACES = 2`). Требовать объединения, равного восьми, значило бы требовать выбросить из классификации ровно те два фрагмента, чей останов план и просит доказать.
- **Исправление:** реализовано НАМЕРЕНИЕ критерия — объединение объявленных множеств равно множеству, найденному обходом. Опрашивающим считается тег, чьё срабатывание содержит расписание; таких в дереве **десять** (8 безусловных + 2 условных). Число выписано литералом `POLLING_FRAGMENTS = 10`, а поправка записана комментарием-летописью над константой, чтобы следующая фаза не перенесла старое число как факт.
- **Истинное число:** **10**, не 8.
- **Файлы:** `tests/test_templates/test_htmx_inventory.py`
- **Проверка:** `uv run pytest tests/test_templates/test_htmx_inventory.py -v` — 19 passed.
- **Коммит:** `5b50637`

**2. [Rule 2 - Missing critical] Убывающий счётчик без потолка чинится поднятием константы**

- **Найдено при:** Task 2
- **Проблема:** план требует двух тестов счётчика («не выросло» и «равно объявленному»). Оба удовлетворяются поднятием `MANUAL_FETCH_PLACES` до семи в момент, когда появится седьмое место: красный цвет гаснет, счётчик перестаёт убывать и становится описанием того, что есть. Стандарт волны требует от убывающего счётчика доказательства, что потолок не может подняться молча, — а план такого механизма не называет.
- **Исправление:** добавлены `MANUAL_FETCH_CEILING_AT_PHASE_08 = 6`, чистая функция `_ceiling_offence(declared, ceiling)`, тест `test_the_declared_manual_fetch_ceiling_never_rises` и контроль `test_control_negative_raising_the_declared_ceiling_reddens_the_gate`, подающий функции семь при потолке шесть и отдельно проверяющий, что путь ВНИЗ зелёный (правило, запрещающее снижение, сняли бы первым же коммитом).
- **Файлы:** `tests/test_templates/test_htmx_inventory.py`
- **Проверка:** `uv run pytest tests/test_templates/test_htmx_inventory.py -k ceiling -v` — зелёный; контроль доказывает красный на поднятом объявлении.
- **Коммит:** `5b50637`

**3. [Rule 2 - Missing critical] Перечень мест ручной сборки был бы непроверяем одним числом**

- **Найдено при:** Task 2
- **Проблема:** план объявляет `MANUAL_FETCH_PLACES = 6` с абзацем-обоснованием, но не перечнем. Число «шесть» ничего не говорит о том, ЧТО именно снимать, и первая же фаза перевода уменьшила бы его наугад — сняв не то место и оставив счётчик формально верным.
- **Исправление:** добавлен `MANUAL_FETCH_SITES` — шесть записей с обоснованием и указанием фазы, которая снимает каждую (пять мест мастера подключения Telegram → Фаза 13, одно место отправки изображения редактором объявлений → Фаза 12). Равенство перечня найденному множеству утверждается отдельно от равенства чисел.
- **Файлы:** `tests/test_templates/test_htmx_inventory.py`
- **Коммит:** `5b50637`

**4. [Rule 3 - Blocking] Требование «гейт не поднимает приложение» несовместимо с чтением свойства окружения**

- **Найдено при:** Task 1
- **Проблема:** план требует и `test_the_gate_reads_sources_not_the_rendered_document`, и `test_the_template_environment_escapes_by_default`. Форма образца (`test_money_perimeter_gate.py`) запрещает ВСЯКИЙ ввоз из приложения; второе требование без такого ввоза невыполнимо — признак автоматического экранирования есть свойство объекта окружения.
- **Исправление:** запрет сформулирован точнее вместо того, чтобы быть обойдённым молча: утверждается, что ввоз из приложения РОВНО ОДИН и это `app.pages.common`, и отдельно — что в дереве разбора файла нет ни построения клиента, ни сборки приложения, ни рендера. Отличие от образца названо прямо в докстринге теста вместе с доводом, почему допущение безопасно (ожидания трёх инвентарей выписаны литералами, обходы читают файлы как текст и как дерево).
- **Файлы:** `tests/test_templates/test_htmx_markup_security.py`
- **Коммит:** `acfe7dc`

---

**Total deviations:** 4 auto-fixed (2 × Rule 3 — блокирующие противоречия в критериях, 2 × Rule 2 — недостающая критическая функциональность).
**Impact on plan:** ни одна правка не расширяет охват плана. Две — исправление арифметики/формулировки критериев с записью истинного числа; две — добавление зубов, без которых убывающий счётчик не убывает, а перечень непроверяем. Ни одного теста не оставлено красным.

## Threat Flags

Новой поверхности безопасности не внесено: план правит только `tests/`, ни одного файла `app/` не тронуто. Строки `T-08-12`, `T-08-37`, `T-08-38`, `T-08-30`, `T-08-39` реестра закрыты соответствующими тестами (см. блок `coverage`). `T-08-SC` (установка пакетов) — ни одной установочной задачи в плане нет, ни один пакет не устанавливался.

## Known Stubs

Ни одного. Все объявленные константы утверждаются собственным обходом, все тесты зелёные, ни один `<verify>` не остался неисполненным.

Одна ГРАНИЦА объявлена сознательно и не является заглушкой: обычные HTML-атрибуты обработчиков событий (`onclick`, `onsubmit`) — четыре места в двух шаблонах — оставлены вне инвентаря до Фаз 12/13. Граница выписана в шапке файла с указанием причины и фаз, которые её снимают; закрыть её убывающим счётчиком по образцу G-22 — решение для человека (см. `coverage` D8).

## Issues Encountered

**Полный прогон суиты занял 27 минут вместо обычных нескольких.** Причина установлена и не связана с правкой: три агента волны 4 (планы 08-07, 08-08, 08-09) исполняли `uv run pytest tests/` одновременно в трёх рабочих деревьях, деля процессор. Прогон завершился кодом 0: **2520 passed** (2493 до плана + 12 новых тестов файла безопасности + 15 новых тестов инвентаря).

**Проверка зубов выполнена не только контролями.** Помимо тринадцати тестов группы `-k control`, гейт безопасности проверен НАСТОЯЩЕЙ правкой боевого дерева: в `app/templates/dashboard.html` временно внесена конструкция снятия экранирования, гейт покраснел на трёх тестах (`test_no_template_removes_automatic_escaping` плюс оба положительных контроля — они утверждают чистоту всего дерева и потому краснеют законно), после чего файл восстановлен `git checkout -- app/templates/dashboard.html`. Рабочее дерево оставлено чистым.

## Self-Check: PASSED

- `tests/test_templates/test_htmx_markup_security.py` — FOUND на диске
- `tests/test_templates/test_htmx_inventory.py` — FOUND на диске
- Коммиты `acfe7dc`, `5b50637` — FOUND в `git log --oneline --all`
- Все объявленные константы найдены `grep`: `ESCAPE_ESCAPES = 0`, `MARKUP_BUILDERS = 0`, `REQUEST_PARAM_ATTRS = 0`, `POLLING_FRAGMENTS = 10`, `PERMANENT_POLLS`, `TERMINATING_POLLS`, `MANUAL_FETCH_PLACES = 6`, `MANUAL_FETCH_CEILING_AT_PHASE_08 = 6`
- `uv run pytest tests/test_templates/test_htmx_markup_security.py -v` — 12 passed
- `uv run pytest tests/test_templates/test_htmx_markup_security.py -k control -v` — 6 passed (критерий: не менее шести), код 0
- `uv run pytest tests/test_templates/test_htmx_inventory.py -v` — 19 passed
- `uv run pytest tests/test_templates/ -k control -v` — 13 passed, код 0
- `uv run pytest tests/ -q` — **2520 passed**, код 0
- Приемочные grep-критерии: `grep -rc '|safe' app/templates/ | grep -v ':0' | wc -l` → 0; `grep -rc 'Markup(' app/ | grep -v ':0' | wc -l` → 0; `grep -rc 'hx-vals' app/templates/ | grep -v ':0' | wc -l` → 0; `grep -rc 'hx-on:' app/templates/ | grep -v ':0' | wc -l` → 0; `grep -rno 'fetch(' app/templates/ | wc -l` → 6

## User Setup Required

Ни одной — внешних служб план не касается, пакетов не устанавливает.

## Next Phase Readiness

Готово. Пакет гейтов этого плана закрывает G-14, G-15, G-21, G-22 и требования GATE-07, GATE-08.

Что наследуют следующие фазы:

- **Фазам 9–11 (перевод форм):** правило сериализации в JSON уже исполнимо — первый заведённый атрибут параметров запроса начнёт проверяться сам, без правки гейта. Первый добавленный опрашивающий фрагмент уронит `test_every_polling_fragment_is_classified` и потребует решения, а не пройдёт бессрочным по умолчанию.
- **Фазе 12 (загрузка изображений):** сняв `fetch(` из `app/templates/ads/form.html`, надлежит ОДНИМ коммитом опустить `MANUAL_FETCH_PLACES` и `MANUAL_FETCH_CEILING_AT_PHASE_08` до 5 и убрать запись `ads/form.html#0` из `MANUAL_FETCH_SITES`. Сообщение об отказе теста равенства говорит это дословно.
- **Фазе 13 (QR-мастер):** то же для пяти мест `accounts/connect_tg_user.html`; после её завершения счётчик достигает нуля, и там же уместно закрыть границу обычных HTML-обработчиков событий.
- **Фазе 15 (сводное закрытие):** финальное утверждение `fetch( == 0` (FETCH-03) пишется поверх этого счётчика, а не вместо него — потолок с именем Фазы 8 остаётся свидетельством того, откуда путь начался.

---
*Phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy*
*Completed: 2026-08-28*
