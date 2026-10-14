---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: WR-14
    severity: warning
    disposition: fixed
    title: "The single-writer gate's alias claim covers \"присваивание\", but `_module_aliases` sees only `Name = Name|Attribute`: tuple, `:=`, `self.x =` and `getattr`-string aliases of writer APIs pass"
  - id: WR-15
    severity: warning
    disposition: fixed
    title: "Column namings do not compose: a naming inside an index, lookup or constructor, and a `getattr` derivative, pass although the column is named literally in the writing call"
  - id: WR-16
    severity: warning
    disposition: fixed
    title: "Raw-SQL kind 5(а) takes the first `WHERE` anywhere as the statement's `WHERE`; a subquery placed before `phone` in `SET` hides the write"
  - id: WR-17
    severity: warning
    disposition: fixed
    title: "The privacy gate misses a log method handed by reference to another call (`asyncio.to_thread(logger.info, …, a.phone)`); its boundary does not name the form"
  - id: IN-13
    severity: info
    disposition: fixed
    title: "The item-5 recount rule pins that each table region is *named*, not that the prose files it under the right cause; the \"region named in prose must be in the table\" obligation is not enforced"
  - id: IN-14
    severity: info
    disposition: fixed
    title: "Item 7, the rule that closes the non-`+7` class, gives no pointer to its remainder, which lives in item 5 (the code-7 item)"
  - id: WR-11
    severity: warning
    disposition: fixed
    title: "`normalize_manual` item 5 names Germany and Israel as the only non-`+7` extra-digit boundary; 36 regions still save an invented \"manual\" number"
  - id: WR-12
    severity: warning
    disposition: fixed
    title: "The single-writer gate's mechanism claim is again wider than the predicate: `MessengerAccount.phone.key`, container forms of `from_select` names, and same-module import aliases of writer APIs pass"
  - id: WR-13
    severity: warning
    disposition: fixed
    title: "The privacy gate misses structlog's async level methods (`ainfo`, `awarning`, …) that the project's configured logger provides"
  - id: IN-11
    severity: info
    disposition: fixed
    title: "Missing space after `=` in `normalize_manual`"
  - id: IN-12
    severity: info
    disposition: fixed
    title: "The writer test reaches the new constant through the module object while its sibling is imported by name"
  - id: WR-09
    severity: warning
    disposition: fixed
    title: "Manual input of a non-`+7` number plus extra digits is still saved as an invented \"manual\" number (BY, UA, KG, TR, IL, CN, DE)"
  - id: WR-10
    severity: warning
    disposition: fixed
    title: "The single-writer gate's new \"through the mechanism\" claim is again wider than the predicate: `Query.update(values=…)`, keyword `set_attribute`, and `run_sync(Session.bulk_*_mappings, …)` pass"
  - id: IN-08
    severity: info
    disposition: fixed
    title: "The auto-path boundary paragraph says \"besides real numbers\" the only extra acceptance is `TOO_SHORT`; 400 of the 558 `IS_POSSIBLE` values accepted in the same enumeration are not valid numbers"
  - id: IN-09
    severity: info
    disposition: fixed
    title: "The privacy gate neither catches nor names two logger forms that are identifiable by import or module binding"
  - id: IN-10
    severity: info
    disposition: fixed
    title: "The other-session case of `record_reported_phone` is left untested on a false premise, and the refusal text gives wrong advice for it"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "Manual input of a valid `+7` number plus four extra digits is saved as an invented 15-digit \"manual\" number"
  - id: WR-07
    severity: warning
    disposition: fixed
    title: "The P-1 boundary in the module header understates the auto path; `TOO_LONG`, `INVALID_LENGTH`, longer `TOO_SHORT` and `+7 0…` are all stored"
  - id: WR-08
    severity: warning
    disposition: fixed
    title: "The single-writer gate's header claims \"Всё, что видно литералом в исходнике, ловится\" (\"everything visible as a literal in the source is caught\"), but literal write forms still pass"
  - id: IN-06
    severity: info
    disposition: fixed
    title: "The privacy gate's binder match misses an aliased import and the threadlocal binders"
  - id: IN-07
    severity: info
    disposition: fixed
    title: "`record_reported_phone` still answers a forgotten `session.add` silently whenever the source sends no number"
  - id: IN-01
    severity: info
    disposition: deferred
    title: "Blank manual input clears a manual number with no confirmation; `PHONE_ERROR_BLANK` cannot be reached through the writer — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-02
    severity: info
    disposition: deferred
    title: "The exact pin `phonenumberslite==9.0.41` freezes the metadata the manual path depends on — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-03
    severity: info
    disposition: deferred
    title: "The race test cannot detect dropping the `phone_is_manual` predicate — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-04
    severity: info
    disposition: deferred
    title: "`reconcile_lines` crashes on decimal phase directories (copied from Phase 15) — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: IN-05
    severity: info
    disposition: deferred
    title: "The migration test's claim that \"children survive the recreate\" is only proven with SQLite foreign keys off — still open (deferred per 16-REVIEW-DISPOSITION.md)"
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Manual input with the `00` prefix or a leading-0 local number is saved as a made-up `+7 0…` number"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "The single-writer gate misses five write forms that are visible in the source"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The privacy gate misses `structlog.contextvars.bind_contextvars(phone=…)`, a pattern the project uses"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "`mask_phone` shows the whole number when the national part has 2 digits or fewer"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "The auto-path lower bound of 5 digits saves source junk as a \"number\"; a test pins this"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Auto writers return `KEPT` when no row was updated at all"
open: 0
total: 32
recorded: 2026-10-13T12:08:30.551Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-14 | warning | fixed | `16-27` задачи 1–3, GREEN `25f2bb5e`, `8aaded0d`, `d9323cd0`, и четыре цикла самопроверки исполнителя, GREEN `b8c84eb3`, `18e13784`, `e5df9047`, `0ea91ee8`; гейт приватности на той же грамматике — `16-29` задача 1, GREEN `9df72956`; правило-паритет `tests/test_phone_gates_parity.py` — `16-29` задача 2, GREEN `29249009` — решение владельца О-12 (а): заявление шапки прежнее; общая грамматика связывания `tests/phone_gate_grammar.py` (распаковка кортежа, в том числе со звёздной целью, `:=`, цель-атрибут `self.<x>` / `cls.<x>` в любом методе, тело класса, `getattr`-строка как атрибут, связанный `partial`) и один перечень носителей с гейтом приватности (`run_sync`, `to_thread`, `run_in_executor`, `map` поэлементно, `Context.run`); получатель `methodcaller` судится у любого применения; правило-матрица оси B `test_every_binding_form_of_a_writer_api_alias_is_judged` («270» ячеек: «9» форм × «5» значений опознания × прямой вызов и «5» носителей); самопроверка исполнителя — «63 688» форм, ноль промахов; связывание вызовом или через пространство имён («setattr(self, "f", api)», «globals()["f"] = api») не ловится — названо в пункте (1) шапки с причиной «поток данных через контейнер»; подготовительное переименование таблицы гейта `BINDING_FORMS` в `PARAMETER_BINDING_FORMS` — коммит «a12ad73c» (refactor) |
| WR-15 | warning | fixed | `16-28` задача 1, GREEN `17ef8eb8`, и шапка — задача 3, GREEN `5bf3e3f5` — решение владельца О-12 (а): `_phone_column` композиционен — наименование колонки номера в позиции имени индекса, поиска, конструктора и `getattr` любой глубины тоже запись («MessengerAccount.__table__.c[MessengerAccount.phone.key]», «t.c.get(M.phone.key)», «column(M.phone.key)»), а `getattr(X, "<const>")` судится как производная `X`; четыре новые строки `COLUMN_NAMINGS` («36» наименований против «714» контекстов); таблица `NAME_POSITIONS` («10» позиций) и правило `test_every_column_naming_nested_in_every_name_position_is_a_write`; самопроверка исполнителя оси A — глубина 1 в каждом контексте, глубина 2, позиции сверх таблицы и контроль чужой колонки, «350 012» форм, ноль промахов, циклов по оси A не понадобилось; предмет находки называет колонку и тогда, когда текст наименования её не показывает (`_naming_text`) |
| WR-16 | warning | fixed | `16-28` задача 2, GREEN `a412c3c5`, и два цикла самопроверки исполнителя оси SQL, GREEN `5e826558`, `6c6bbea2`; шапка — задача 3, GREEN `5bf3e3f5` — решение владельца О-12 (а): виды 5 (а) и (б) судит код `_raw_sql_set_writes` над предложением `SET` на нулевой глубине скобок — подзапрос со своим `WHERE`, литерал, комментарий SQL или идентификатор в кавычках перед колонкой запись больше не прячут, строчный конструктор судится в любой позиции `SET`; `RAW_SQL_PHONE_WRITE` несёт только (в) и (г); фильтр по номеру в `WHERE` и в подзапросе — не запись; самопроверка оси SQL — «10 142» формы, ноль промахов после двух циклов («where» в кавычках или в комментарии SQL перед колонкой; склейка `+` из одних констант судится один раз — у склейки); сужение только в сторону не-записи: текст «phone = …» внутри литерала, комментария или строки в двойных кавычках больше не находка (колонку он не пишет); `_raw_sql_set_writes` возвращает список найденных записей, а не `bool` |
| WR-17 | warning | fixed | `16-29` задачи 1–3, GREEN `9df72956`, `29249009`, `334b0b9a`, и три цикла самопроверки исполнителя, GREEN `aff284c9`, `90803f88`, `e2807607` — умолчание прохода и решение владельца О-12 (а): носитель ссылки на журнал — любой вызов с аргументами после ссылки (`to_thread`, `run_in_executor`, `map`, `Context.run`, `run_sync`, `fn=`), синтетический вызов журнала судится аргументами после ссылки (`_carried_log_calls`); `methodcaller` над опознанным получателем, в том числе под `fn=` (`_applied_log_methodcaller`); псевдонимы `partial` и `methodcaller` (`_wrapper_aliases`); связывания — из общей грамматики `tests/phone_gate_grammar.py`; правило-матрица `test_every_binding_form_of_a_log_reference_is_judged` («270» ячеек) и правило-паритет обоих гейтов `tests/test_phone_gates_parity.py`; самопроверка — «160 080» форм, ноль промахов; ссылка, связанная `setattr` / `globals()` / `vars()`, взятая из контейнера, возвращённая не-`partial` вызовом или обёрнутая в `lambda`, не ловится — названа в «ГРАНИЦЕ СРЕДСТВА» с причиной «поток данных»; живые деревья — «224/68/93» вызовов и 0 находок (было «221/68/93»: три новых распознанных вызова в app/pages/history.py, строки «288», «289», «293», — цена строгости, названная шапкой, находок на них нет) |
| IN-13 | info | fixed | `16-26` задача 1, GREEN `d51dc5b2` — решение владельца О-13: правило-сверка пункта 5 докстринга `normalize_manual` разбирает три скобки причин (`_item_five_groups`: сам `MOBILE`, только `VOIP`, классы `FIXED_LINE`) и сверяет каждую с `MANUAL_BOUNDARY_EXAMPLES` в обе стороны; обратное вложение — по отрезку остатка: код региона в предложении остатка обязан быть ключом таблицы; контроли над текстом, мутированным в памяти (TW в скобке MOBILE, RS в скобке VOIP или в предложении остатка), краснят правило; коммит RED — «a501f826»; код `normalize_manual` прежний |
| IN-14 | info | fixed | `16-26` задача 2, GREEN `ce5d2378` — решение владельца О-13: пункт 7 докстринга `normalize_manual` одной фразой ссылается на остаток, измеренный в пункте 5, без чисел и без регионов таблицы; правило `test_item_seven_points_to_its_remainder_in_item_five`; коммит RED — «ab206ce9»; поведение `normalize_manual` AST-равно «33a31ee3» |
| WR-11 | warning | fixed | `16-21` задача 1, GREEN `dd164d6e` — решение владельца О-9 (а): правило О-7 (а) остаётся, пункт 5 докстринга `normalize_manual` называет настоящий остаток — «56 из 976» вводов «образец MOBILE + 1…4 цифры» в 36 регионах, причины по типам аккаунта (сам `MOBILE` — NL, FI, ID, MY, AT; только `VOIP` — TW, ZW; классы `FIXED_LINE` — DE, IL, IT), «15 из 56» действительных по метаданным; правило `test_the_manual_path_names_its_extra_digit_boundary_with_its_measurement` пересчитывает числа и регионы-примеры `MANUAL_BOUNDARY_EXAMPLES` вживую из метаданных; коммит RED — «71957ec1», тексты теста — коммит «93632304»; исправлена узкая формулировка строки WR-09 («граница названа в пункте 5 — Германия … и Израиль …»): это была граница, названная двумя регионами из тридцати шести, а не весь остаток правила О-7 (а); сама строка WR-09 перенесена без изменений (not in the current review) |
| WR-12 | warning | fixed | `16-22` задачи 1–3, GREEN `ecd1be76`, `4d6f286e`, `9f50ed19`, и шесть циклов самопроверки исполнителя, GREEN `878b4679`, `dbe22dcc`, `a973ea55`, `ddbb33f7`, `a4c49b66`, `80153e32` — решение владельца О-10 (а): заявление шапки «через механизм» прежнее; колонка номера опознаётся в производной (`MessengerAccount.phone.key`, `.name`, `.expression`, `.property.key`, `.property.columns[0]` и любая цепочка), в поиске по имени, в конструкторе при любом литеральном связывании и в константной склейке; перечень `from_select` — в любом литеральном контейнере и любом позиционном аргументе; псевдоним пишущего API в том же модуле (ввоз и присваивание, в том числе псевдонимы `methodcaller` и `getattr`) судится как сам API; ось «как названа колонка» — таблица `COLUMN_NAMINGS` («32» наименования) с правилом-матрицей против `COLUMN_CONTEXTS` («714» контекстов); самопроверка исполнителя по обеим осям — «205 680» форм, ноль промахов; имя колонки, вычисленное вызовом («"PHONE".lower()», «"{}".format("phone")», «8 456» форм), не ловится — граница (2) шапки с причиной «предикат вызовов не исполняет»; сообщение RED-коммита «37ec629e» называет «140» форм самопроверки, замер — «120» (сводка 16-22) (not in the current review) |
| WR-13 | warning | fixed | `16-23` задачи 1–2, GREEN `1852b951`, `e54fd6e3`, и цикл самопроверки исполнителя, GREEN `978a9408` — умолчание прохода: `ASYNC_LOG_METHODS` (восемь асинхронных уровней structlog) входит в `LOG_METHODS`, сторож `test_the_async_level_methods_match_the_installed_structlog` сверяет набор с установленным structlog «25.5.0»; охват по получателю (D-17 `logger.*`) — любой метод опознанного журнала судится как вызов журнала, `getChild` / `unbind` / `try_unbind` — привязки (`LOGGER_RETURNING_METHODS`), `root` и `parent` — журналы-члены (`parent` найден самопроверкой); член опознанного журнала остаётся и получателем по шаблону имени, так что «logger._logger.info(…)» по-прежнему ловится (строже буквы плана, сводка 16-23); граница больше не приписывает D-17 список методов; самопроверка — «18 490» форм, ноль промахов; живые деревья — «221/68/93» вызовов и 0 находок (было «215/68/89»: прибавились вызовы настройки журнала в app/logging_config.py и max_worker/main.py); число строк выше буквы критерия («OK 90 39», «170» тестов файла) — из-за строк самопроверки (not in the current review) |
| IN-11 | info | fixed | `16-21` задача 2, коммит `9711cb39` (тема `refactor(16-21): add the missing space after = in normalize_manual (IN-11)`) — решение владельца О-11: пробел после `=` в `normalize_manual` («e164 = phonenumbers.format_number(…)»); код функции по дереву разбора прежний (AST совпадает с «cce988cb») (not in the current review) |
| IN-12 | info | fixed | `16-24` задача 1, коммит `d9cfd6c4` (тема `refactor(16-24): import ACCOUNT_WITHOUT_ID_AFTER_FLUSH by name in the writer test`) — решение владельца О-11: `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` ввезена по имени рядом с `ACCOUNT_NOT_IN_SESSION`, второй путь ввоза (объект модуля под псевдонимом `writer_module`) снят вместе с единственным использованием; утверждения прежние, модуль писателя и тест гонки не тронуты (not in the current review) |
| WR-09 | warning | fixed | `16-16` задача 1, GREEN `333bf8e0` — решение владельца О-7 (а): ручной номер принимается, только если его длина возможна хотя бы для одного типа аккаунта (`ACCOUNT_NUMBER_TYPES`: `MOBILE`, `FIXED_LINE`, `FIXED_LINE_OR_MOBILE`, `VOIP`; пункт 7 докстринга `normalize_manual`): «+375 29 123 45 67 1» и «+380 50 123 4567 1» — отказ `PHONE_ERROR_NOT_A_NUMBER`; класс «чужой номер плюс лишние цифры» закреплён перебором 5 баз × 1–5 лишних цифр (до плана сохранялись 7 из 25 строк, замер исполнения), а не отдельными вводами; граница названа в пункте 5 докстринга — Германия «+49 151 23456789» с одной и двумя лишними цифрами (с тремя и четырьмя её отвергает предел E.164) и Израиль «+972 50 123 4567» с двумя и тремя остаются принятыми (not in the current review) |
| WR-10 | warning | fixed | `16-17` задачи 1–3, GREEN `9b074697`, `417229e7`, `282c16d7`, и три цикла самопроверки исполнителя, GREEN `b7a1e127`, `e3f46b63`, `e53d9320` — пишущий API опознаётся по ссылке, `getattr`-строке, `methodcaller` и `partial` (в том числе `run_sync(Session.bulk_update_mappings, …)` и `partial` внутри другого вызова); таблица `JUDGED_PARAMETERS` из перебора сигнатур (34 строки: 33 запланированные и `flag_modified`; сверена с `inspect.signature` правилом-сторожем) судит каждый параметр позицией, именем, `**{…}` и `*[…]` — `Query.update(values=…)`, `set_attribute(…, key=…)`, `set_committed_value(…, key=…)`, comprehension с ключом номера; вид 1 судится по грамматике `Store`, `__set__` дескриптора, `__init__` модели и ключам `column()`; самопроверка нашла и закрыла три класса сверх плана — `flag_modified` (замер: запись, план числил его не-записью), `partial` внутри другого вызова, псевдонимы `partial` и модели в модуле; шапка гейта — граница только с правдивой причиной (not in the current review) |
| IN-08 | info | fixed | `16-16` задача 3, GREEN `5c3ffb94` — решение владельца О-8: абзац «ГРАНИЦА ПРАВИЛА АВТОПУТИ» шапки `app/services/phone.py` называет оба принимаемых класса — значения, которые метаданные считают возможными, в том числе недействительные («400 из 558», примеры «+72345678901», «+10000000000»), и вердикт `TOO_SHORT` у кода не 7 («583 из 1935»); асимметрия «+7 0…» против «+1 0…» названа следствием О-5 (а); правило `test_the_module_header_names_the_auto_path_boundary_with_its_measurement` сверяет оба числа с перебором вживую (not in the current review) |
| IN-09 | info | fixed | `16-18` задачи 1–2, GREEN `38727536`, `5a7cc660` — функции `logging`, ввезённые в модуль («from logging import info», «warning as warn_»), судятся как вызовы журнала; журнал из тела класса находится через `self.` и `cls.`; распознаны также `:=`, второе связывание, фабрика под псевдонимом, `getattr`-строка, обёртки (`LoggerAdapter`, `wrap_logger`), `functools.partial` и ссылки на методы, а сверх буквы плана — формы той же оси (`logging.root`, классы журнала вроде `logging.Logger`, связывание кортежем, `builtins.print`); «ГРАНИЦА СРЕДСТВА» названа заново — в ней остались только формы с правдивой причиной (рамка D-17); живые деревья — прежние «215/68/89» вызовов и 0 находок (not in the current review) |
| IN-10 | info | fixed | `16-19` задача 1, GREEN `b2758f43` — решение владельца О-8: нейтральный текст `ACCOUNT_NOT_IN_SESSION` («аккаунт не принадлежит сессии писателя», без совета `session.add`) и своя константа `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` для второй линии после flush; правило `test_each_refusal_of_the_recorder_names_its_own_cause`; строка «foreign» (объект в несвязанной `AsyncSession()`) — сторож задачи 2, коммит теста «27cfc105»; ложная посылка докстринга теста о второй сессии снята (not in the current review) |
| WR-06 | warning | fixed | `16-11` задача 1, GREEN `02d73c93` — отказ `PHONE_ERROR_NOT_A_NUMBER` у кода 7 с национальной частью не из 10 цифр или с ведущим нулём (`_is_impossible_zone_seven`): «+7 999 123-45-67 1234» и родственные вводы больше не сохраняются выдуманным «ручным» номером; класс «номер плюс лишние цифры» закреплён перебором (4 основы × 1–5 лишних цифр), а не четырьмя вводами (not in the current review) |
| WR-07 | warning | fixed | `16-11` задача 2, GREEN `2565d515` — решение владельца О-5 (а): автопуть отвергает невозможные значения кода 7 (тот же `_is_impossible_zone_seven`) и вердикты `TOO_LONG` / `INVALID_LENGTH` (`REPORTED_REFUSED_VERDICTS`): «70123456789», «799912345678», «1234567890123» дают отказ, «88801234567» по-прежнему принимается; шапка модуля называет оставшуюся границу — любое разбираемое значение из 7–15 цифр с вердиктом `TOO_SHORT` у кода не 7 (пример «123456789»; 583 из 1935 перебранных вводов), особого случая для кода 888 нет (О-1) (not in the current review) |
| WR-08 | warning | fixed | `16-12` задачи 1–3 и дополнительный цикл самопроверки исполнителя, GREEN `f10abdd7`, `2ccdb4d2`, `6c862686`, `e168d3dd` — девять литеральных форм верификатора и формы тех же семейств (`parameters=`, comprehension, сырой SQL с кавычками и схемой, `ordered_values`, `__setattr__`, upsert MySQL, псевдонимы модели; 51 новая строка `LITERAL_FORM_CASES`, живое дерево — 0 судимых находок); шапка гейта заявляет охват через механизм, а не «всё», и называет пять недостижимых форм с причиной: значение потоком данных, имя колонки или SQL во время исполнения, позиционный кортеж без имён колонок, пишущий API без имени или под псевдонимом из другого модуля, `__dict__` / `vars()` (not in the current review) |
| IN-06 | info | fixed | `16-13` задачи 1–2, GREEN `3bd2e6a0`, `58550bb3` — решение владельца О-6: псевдоним ввоза привязки (`bind_ctx`), `bind_threadlocal` / `bound_threadlocal` / `tmp_bind`, получатель журнала из фабрики или под псевдонимом ввоза (`module_log_names`); живые деревья — прежние 215/68/89 вызовов и 0 находок; остальное названо в «ГРАНИЦЕ СРЕДСТВА», среди прочего фабрика под псевдонимом ввоза и связывание без вызова «a = lg» (not in the current review) |
| IN-07 | info | fixed | `16-14` задача 1, GREEN `164a0276` — проверка членства в сессии писателя до нормализации (`inspect(account).session is not session.sync_session`), без операторов и без flush: отказ `ACCOUNT_NOT_IN_SESSION` при любом входе источника («None», пустая строка, мусор, разбираемый номер) и для отсоединённого объекта; страж задачи 2 — коммит теста «1fad15e3»; случай объекта из чужой сессии тестом не смоделирован, назван в докстринге (not in the current review) |
| IN-01 | info | deferred | отложено на Фазу 18 (решение владельца О-4, 2026-10-09): её форма выбирает между явным действием «очистить» и показом `PHONE_ERROR_BLANK`; поведение сегодня предписано D-07 / PHONE-10; записано в `.planning/STATE.md` §Deferred Items (not in the current review) |
| IN-02 | info | deferred | адресат — владелец / бэклог (О-4): точный пин `phonenumberslite==9.0.41` заперт роадмапом («Рамки вехи»); процедура подъёма пина против `>=9.0.41,<10` — решение владельца (not in the current review) |
| IN-03 | info | deferred | заметка без работы (О-4): предикат `phone_is_manual IS false` избыточен при CHECK `ck_messenger_accounts_manual_requires_phone`; тестом не закреплён — читать его как проверенный нельзя (not in the current review) |
| IN-04 | info | deferred | адресат — бэклог, владелец `scripts/prohibitions_census.py` (О-4): давний дефект с `49ca9ddf` (15-15) — `_phase_number_of` падает на дробных каталогах фаз; фаза 16 его скопировала, а не завела (not in the current review) |
| IN-05 | info | deferred | адресат — бэклог (О-4): шапка теста ревизии `0023` должна назвать предусловие «внешние ключи SQLite выключены на время batch»; боевой PostgreSQL не затронут, деплой-гейт D-26 (not in the current review) |
| CR-01 | critical | fixed | `16-07` задача 1, GREEN `97e62918` — отказ `PHONE_ERROR_NOT_A_NUMBER` при коде 7 и ведущем нуле национальной части (О-3 (а)): `00 …`, украинский местный и белорусский `8 0…` больше не сохраняются как `+7 0…` (not in the current review) |
| WR-01 | warning | fixed | `16-09` задачи 1–2, GREEN `a97179ab`, `78495634` — пять литеральных форм записи: `execute` и `bulk_*_mappings` с ключом `phone*` в строках, `set_` у `on_conflict_do_update`, литеральный `**{…}` и `dict(...)` (not in the current review) |
| WR-02 | warning | fixed | `16-09` задача 3, GREEN `6ed63a95` — `bind_contextvars` / `bound_contextvars` судятся гейтом приватности как вызовы журнала при любом приёмнике (not in the current review) |
| WR-03 | warning | fixed | `16-07` задача 3, GREEN `fdb12dd5` — порог маски короткой национальной части: при двух цифрах и меньше маскируется вся она (`+88812` → `+888 ***`) (not in the current review) |
| WR-04 | warning | fixed | `16-07` задача 2, GREEN `ae44c1d0` — граница 7, отказ `IS_POSSIBLE_LOCAL_ONLY`, строка `five_digits_lower_bound` переписана с летописью; остаётся названная граница П-1 (шапка модуля): 7-значный обрывок `TOO_SHORT` вроде «1234567» автопуть принимает, особого случая для кода 888 владелец не принял (О-1) (not in the current review) |
| WR-05 | warning | fixed | `16-08` задачи 1–2, GREEN `67a25113`, `bee23ee2` — `PhoneWrite.MISSING` для отсутствующей строки; `ValueError` на объекте вне сессии (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
