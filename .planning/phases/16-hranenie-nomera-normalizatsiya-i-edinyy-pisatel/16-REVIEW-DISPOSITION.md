---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "Гейт приватности после перевода на общую семантику носителя пропускает `map` с не-литеральной итерируемой: `list(map(logger.info, account.phones))` ловился на базе, на `HEAD` — нет"
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "Гейт писателя после правила «поглощения» обёртки носителя (`147f5e46`) пропускает обёртку под именем, которую передают, а не вызывают — дословное тело `asyncio.to_thread`"
  - id: WR-24
    severity: warning
    disposition: fixed
    title: "Гейт приватности держит свою копию семантики обёртки носителя под именем (`_carrier_wrappers`, ручной `applied_wrapper`) — копия расходится с гейтом писателя, а структурная половина паритета её не видит (остаток 16-34 (а), класс IN-15)"
  - id: WR-25
    severity: warning
    disposition: fixed
    title: "Поведенческая половина паритета не держит формы самопроверки 16-34 (`starmap`, `apply_async`, именованная обёртка), и в этих ячейках гейты уже расходятся: `starmap(methodcaller(…), [(logger,)])` гейт приватности пропускает (остаток 16-34 (в))"
  - id: WR-26
    severity: warning
    disposition: fixed
    title: "Обёртка носителя, поданная другому носителю (а не применённая), или обёрнутая ещё одним `partial` — не ловит ни один гейт, и ни одна граница её не называет"
  - id: IN-16
    severity: info
    disposition: fixed
    title: "Комментарий ввоза гейта приватности называет выведенную `REFERENCE_KEYWORDS` и путает, кто кого зовёт (остаток 16-34 (б))"
  - id: IN-17
    severity: info
    disposition: fixed
    title: "Шапка гейта приватности и комментарий её правила говорят о строках `REFERENCE_CARRIERS` в будущем времени — «впишет план 16-34»"
  - id: WR-18
    severity: warning
    disposition: fixed
    title: "A name bound twice in one module resolves only to its FIRST binding: a writer API, descriptor, `partial` or `methodcaller` bound second under a reused name passes both gates"
  - id: WR-19
    severity: warning
    disposition: fixed
    title: "The privacy gate's carrier rule is narrower than the writer's: `*[…]`-delivered references, `partial`-wrapped carriers and wrapped iterables pass, and the parity matrix has no cell that could see it"
  - id: WR-20
    severity: warning
    disposition: fixed
    title: "A reference handed by a keyword other than `fn=` passes (`threading.Thread(target=…, args=…)`), neither boundary names it, and the gates disagree on `Timer(…, args=…)`"
  - id: WR-21
    severity: warning
    disposition: fixed
    title: "Kind 5 misses SQLite's single-quoted identifiers; 16-28's \"text inside a literal is not a write\" hides `SET 'phone' = …` and `INSERT INTO 'messenger_accounts'`"
  - id: WR-22
    severity: warning
    disposition: fixed
    title: "Kind 5 (в) and (г) still run a `\\s+` regex over raw text, so a SQL comment inside the statement head hides an `INSERT` / `REPLACE` / `COPY` into the accounts table"
  - id: WR-23
    severity: warning
    disposition: fixed
    title: "`Column(\"phone\")` / `ColumnClause(\"phone\")` as a `values` key pass, though the column is named literally in the writing call"
  - id: IN-15
    severity: info
    disposition: fixed
    title: "The parity rule's structural half matches four function names and four table names, not \"no own copy\"; a private grammar or carrier copy under any other name passes it"
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
total: 46
recorded: 2026-10-16T13:56:58.217Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-02 | critical | fixed | `16-38` задачи 1 и 3, GREEN `3a7fe75b`, `d7013797`, и цикл самопроверки исполнителя (заход 1), GREEN `85ac9a2e` — решение владельца О-16 (а): регрессия партии раунда 6 («c6953017», 16-32 задача 1: перевод гейта приватности на общую `reference_arguments` гасил не-литеральную итерируемую поэлементного носителя в `UNJUDGED_ELEMENT`, и «list(map(logger.info, account.phones))», ловившийся на базе, проходил); гейт приватности снова судит итерируемую поэлементного носителя целиком — `reference_arguments(…, keep_iterables=True)`: не-литерал выражением, comprehension вместе с источником итерации, «*name» узлом `Starred`; семантика гейта писателя прежняя (он зовёт ту же функцию без параметра, ответ прежних строк и ячеек не изменился); обёртка журнала, поданная поэлементному носителю, получает и элементы, и итерируемые целиком (`wrapper_applications(…, keep_iterables=True)`, заход 1 самопроверки — «432» промаха, ноль после цикла); трасер `test_a_planted_log_reference_mapped_over_an_account_attribute_reddens_the_gate`; семь форм ревью — строки `NEGATIVE_CONTROLS` («145» строк на итоговом дереве 16-38), «map(logger.info, account.names)» — вызов журнала без находки; граница шапки «судится само выражение» снова правда; строка словаря `map-named-iterable` с местом `ReferenceCarrier.last` — план 16-39, задача 2 (строка вписана коммитом теста «bb6ce1be», поле `last` и его место — GREEN «7a3a7b46»); итог сверки «база ↔ HEAD» плана — «BASE 9a92efd9 -> HEAD 9ce79852: cells=32970 regressions=0», «OPEN_REGRESSIONS=0»; итог сверки партии раунда 7 — «AGAINST 1c243203 -> HEAD defeaae4: cells=107825 regressions=0»; самопроверка — «9 180» форм, ноль промахов на итоговом дереве; коммиты RED — «1da1b993», «0b50a4de», «9f804a44» |
| CR-03 | critical | fixed | `16-36` задачи 1 и 3, GREEN `b67495dc`, `b8d557f0`, и цикл сверки «база ↔ HEAD», GREEN `4ffef0c1` — решение владельца О-16 (а): регрессия партии раунда 6 («147f5e46», самопроверка 16-34, заход 1: обёртка носителя поглощалась по любому чтению её имени, и переданная, а не вызванная обёртка не судилась нигде); обёртка носителя под именем судится везде, где её имя прочитано — вызванная, поданная исполнителю, потоку или очереди («await loop.run_in_executor(None, func_call)» — дословное тело `asyncio.to_thread`), — а поглощение суда на месте связывания — только когда каждое чтение судится как применение (`_absorbed_carrier_wrappers`); применения обёрток — общая `wrapper_applications` модуля `tests/phone_gate_grammar.py` (с `named_wrappers` и `WrapperApplication`), гейт писателя судит каждое применение как носитель на месте внешнего вызова; трасер `test_a_planted_backfill_with_a_context_run_wrapper_handed_to_an_executor_reddens_the_gate`; четыре формы ревью и контроль «без использования» — строки `LITERAL_FORM_CASES` («244» строки на итоговом дереве 16-36, `LEGITIMATE_CASES` — «98»); цикл сверки закрыл собственную регрессию плана на «44452e68» (вложенный литерал обёртки с аргументами записи давал две находки вместо одной, «798» ячеек; RED «a5b43616»); итог сверки «база ↔ HEAD» плана — «BASE 1c243203 -> HEAD 4ffef0c1: cells=54001 regressions=0», «OPEN_REGRESSIONS=0», «SELFTEST» «43» и «52»; самопроверка — «34 243» формы, ноль промахов; коммиты RED — «388ed1a9», «ec639a54»; заявление шапки гейта писателя прежнее; форма ревью «w = partial(Context.run, …); run_in_executor(None, w)» — строка общего словаря `named-wrapper-bound-handed` (план 16-39, задача 1: строка вписана коммитом теста «f684dc45», шапки обоих гейтов называют её с GREEN «59654f01»; «60» ячеек на гейт без промахов); итог сверки партии раунда 7 — «AGAINST 1c243203 -> HEAD defeaae4: cells=107825 regressions=0» |
| WR-24 | warning | fixed | `16-37` задачи 1 и 3, GREEN `51d0d766`, `0a4e4411`; применения обёрток — задача 2, GREEN `2d59adff` — решение владельца О-16 (а), свойство 5, и О-15: копия семантики обёртки носителя гейта приватности снята — `_carrier_wrappers` стала тонкой обёрткой над общей `carrier_wrapper_bindings(…, nested=True)` с общим предикатом `is_carrier_wrapper` (гейт даёт только имена `partial` и свой предикат ссылки `_log_wrapper_reference`), обёртки узла — общая `named_wrappers` (литерал, имя, атрибут, getattr-строка), применения — общая `wrapper_applications`, ручная сборка применения ушла; оба гейта зовут общие `carrier_wrapper_bindings` / `is_carrier_wrapper` / `named_wrappers` / `applied_wrapper` / `wrapper_applications`; «getattr(self, "w")(…)» ловится обоими гейтами; одно место — одна находка: `python_log_offences` не повторяет тройку «строка, вид, предмет» (двойной счёт «5e57325d» снят); `REQUIRED_SHARED_NAMES` правила-паритета — «11» имён, среди них пять имён семантики обёртки, `CARRIER_SEMANTICS` их требует; трасер `test_a_planted_log_wrapper_called_through_a_getattr_string_reddens_the_gate`; две формы ревью — строки `NEGATIVE_CONTROLS`; фраза шапки «своих копий нет» теперь правда; план 16-37 правил модуль гейта приватности по свойству 8; строка словаря `named-wrapper-getattr` — план 16-39, задача 2 (вписана коммитом теста «bb6ce1be», зеленеет с GREEN «7a3a7b46»); итог сверки «база ↔ HEAD» плана — «BASE df9cea19 -> HEAD 0a4e4411: cells=38402 regressions=0», «OPEN_REGRESSIONS=0»; самопроверка — «16 634» формы, ноль промахов, ноль повторов места; коммиты RED — «a6c87597», «fa786d20» |
| WR-25 | warning | fixed | `16-38` задача 2, GREEN `b953ce0d` (одно правило носителей для обоих гейтов: `ELEMENTWISE_CARRIERS` — `map`, `imap`, `imap_unordered`, `map_async`, `ROW_CARRIERS` — `starmap`, `starmap_async`, построчное прочтение у обоих гейтов без флага; `methodcaller` у `starmap` получает получателя из строки; правдивый докстринг `reference_arguments`; сторож `test_the_elementwise_and_row_carriers_name_the_installed_apis` сверяет таблицы с установленным stdlib), её регрессия «219» ячеек (обёртка журнала у `pool.imap` / `pool.imap_unordered` / `pool.map_async`) закрыта GREEN `85ac9a2e`, и цикл сверки «база ↔ HEAD», GREEN `9ce79852` (путь `methodcaller` гейта приватности — `every_reading=True`, как у гейта писателя: «partial(threading.Thread, target=mc)(args=(logger,))» — находка); `16-39` задача 2, GREEN `7a3a7b46` (строки словаря `starmap`, `apply-async` в `REFERENCE_CARRIERS` вписаны коммитом теста «bb6ce1be» и зеленеют с этим GREEN; ось «именованная обёртка» — строки `named-wrapper-called`, `named-wrapper-handed`, `named-wrapper-getattr`; обе матрицы — «1 260» ячеек на гейт без промахов, поведенческая половина паритета без расхождений) — решение владельца О-16 (а), свойства 4 и 6: две формы ревью («starmap(methodcaller(…), [(logger,)])» у `itertools` и `pool`) — строки `NEGATIVE_CONTROLS`; итог сверки «база ↔ HEAD» 16-38 — «BASE 9a92efd9 -> HEAD 9ce79852: cells=32970 regressions=0», «OPEN_REGRESSIONS=0»; 16-39 — «BASE ff1d3b7a -> HEAD defeaae4: cells=107825 regressions=0»; коммиты RED — «3b503f81», «269b9218», «bb6ce1be» |
| WR-26 | warning | fixed | `16-36` задачи 1–2, GREEN `b67495dc`, `44452e68`, и цикл сверки «база ↔ HEAD», GREEN `4ffef0c1` (сторона писателя: общая `wrapper_applications` раскрывает обёртку, поданную носителю позицией, «*[…]», любым именованным аргументом или внутри «X(…)(…)», рекурсивно, с защитой от цикла; общий рекурсивный предикат `is_carrier_wrapper` и `carrier_wrapper_bindings(…, nested=True)` видят обёртку поверх обёртки литералом любой глубины и именем; вложенный литерал судится один раз; четыре формы ревью — строки `LITERAL_FORM_CASES`), `16-37` задача 2, GREEN `2d59adff` (сторона приватности: гейт приватности судит каждое применение `wrapper_applications`; семь форм — поданная литералом и именем, в `partial`, имя поверх имени, глубина три литералом и именем, `methodcaller` в поданной обёртке — строки `NEGATIVE_CONTROLS`), `16-39` задача 2, GREEN `7a3a7b46` (строки словаря `wrapper-handed`, `wrapper-of-wrapper`, `named-wrapper-handed` в `REFERENCE_CARRIERS` вписаны коммитом теста «bb6ce1be» и зеленеют с этим GREEN; обе матрицы — «1 260» ячеек на гейт без промахов, правило-паритет без расхождений) — решение владельца О-16 (а), свойство 3: пробел композиции (на базе ревью тоже ноль находок), а не регрессия; шапки обоих гейтов называют поданную и вложенную обёртку пойманной; итог сверки партии раунда 7 — «AGAINST 1c243203 -> HEAD defeaae4: cells=107825 regressions=0», итоговая самопроверка партии — «82 035» форм, ноль промахов; коммиты RED — «388ed1a9», «8e1f2ebf», «a5b43616», «a53126a7», «bb6ce1be» |
| IN-16 | info | fixed | `16-37` задача 3, GREEN `0a4e4411` — решение владельца О-17: комментарий ввоза гейта приватности не называет выведенную таблицу ключа ссылки (`REFERENCE_KEYWORDS` из него снята) и называет путь `methodcaller`, в котором гейт сам зовёт `iterable_elements` (`_applied_log_methodcaller`); формула плана «`reference_arguments` её не зовёт» была бы ложной — общая `reference_arguments` доходит до `iterable_elements` через `elementwise_arguments` у поэлементного носителя, и комментарий говорит это (отступление 1 сводки 16-37); правило шапки `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` держит оба места; коммит RED — «fa786d20» |
| IN-17 | info | fixed | `16-37` задача 3, GREEN `0a4e4411` — решение владельца О-17: шапка гейта приватности и комментарий правила шапки говорят о строках `REFERENCE_CARRIERS` плана 16-34 в прошедшем времени («шесть строк, вписанные планом 16-34»), а не «впишет план 16-34»; правило шапки `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` краснеет, если «впишет» стоит рядом с «16-34»; коммит RED — «fa786d20» |
| WR-18 | warning | fixed | `16-31` задачи 1–3, GREEN `d3304aab`, `0b7a503b`, `2a506aea`, и цикл самопроверки исполнителя, GREEN `ebe466ac` — решение владельца О-14 (а): заявления обоих гейтов прежние, каждое связывание имени судится; карты псевдонимов гейта писателя многозначны (`_api_aliases` — «псевдоним → множество исходных API», `_api_alias_targets`, `_partial_aliases`, `_methodcaller_aliases` — «имя → список значений»), `_bound_reference` и `_canonical_call` возвращают списки, находки дедуплицируются по (строка, столбец, вид), а толкования одного вызова сводятся в одну находку на место; гейт приватности судит каждого кандидата `methodcaller` с опознанным получателем (`_applied_log_methodcaller` возвращает список); в общем словаре `BINDING_FORMS` три строки повторного связывания `rebound`, `rebound-reversed`, `rebound-across-classes` с подменой того же вида (поле `IdentificationValue.decoy`, место `{decoy}`), «12» форм, «360» ячеек на гейт в обеих матрицах и правиле-паритете; трасер `test_a_planted_backfill_with_a_rebound_writer_alias_reddens_the_gate`; самопроверка оси кратности — «134 460» форм («90 396» у гейта писателя, «44 064» у гейта приватности), ноль промахов после одного цикла (две находки разных видов на одном месте у имени, связанного с двумя API, — «1 968» форм); живые деревья — 0 находок, «224/68/93» вызовов; коммиты RED — «a9e1f6a1», «8e411e06», «97434b5b», «c7c297ed» (not in the current review) |
| WR-19 | warning | fixed | `16-32` задачи 1–3, GREEN `c6953017`, `50d6e5cf`, `8a28d2e7`, и два цикла самопроверки исполнителя, GREEN `6231a0b3`, `5e57325d`; строки носителей в словаре и паритет — `16-34` задача 2, GREEN `a28d6efc` (шесть строк `REFERENCE_CARRIERS` вписаны коммитом теста «9dc72673», зеленеют с этим GREEN) — решение владельца О-14 (а): семантика носителя — функции общего модуля `tests/phone_gate_grammar.py` (`reference_arguments`, `iterable_elements` с обёрткой `list([…])`, `getattr_literal`, `expanded_arguments`, `forwarded_arguments`, `elementwise_arguments`), гейт приватности зовёт их; ссылка на журнал, поданная литеральной `*`-распаковкой, внутри применённой обёртки носителя `X(…)(…)` (в том числе обёртки, связанной с именем, — цикл 2) или в обёрнутой итерируемой, судится; `methodcaller` — у любого носителя, получатель — и первый элемент литерального списка, поданного первым (цикл 1); сужающая оговорка «позиционным аргументом без `*`» снята из шапки гейта приватности; трасер `test_a_planted_log_reference_handed_to_a_thread_target_reddens_the_gate`; самопроверка — «99 600» форм под заявлением, ноль промахов после двух циклов; живые деревья — «225/68/93» вызовов и 0 находок (было «224/68/93»: новое распознанное место app/worker/tasks.py, строка «453», — цена строгости, находок нет); строки `starred`, `partial-wrapped`, `map-wrapped-iterable`, `thread-target`, `timer-args`, `invented-keyword` — «11» носителей, обе матрицы и правило-паритет держат по «720» ячеек на гейт (not in the current review) |
| WR-20 | warning | fixed | `16-32` задача 1, GREEN `c6953017` (сторона приватности: общая `reference_arguments` с общим правилом `literal_keyword_arguments`, трасер `test_a_planted_log_reference_handed_to_a_thread_target_reddens_the_gate`); `16-34` задачи 1–3, GREEN `94b6c25d`, `a28d6efc`, `e5987a35`, и два цикла самопроверки исполнителя, GREEN `147f5e46`, `21d463f0` (сторона писателя: гейт писателя ищет ссылку той же функцией `reference_arguments`, трасер `test_a_planted_backfill_with_a_threaded_writer_reference_reddens_the_gate`; строки `thread-target`, `timer-args`, `invented-keyword` в `REFERENCE_CARRIERS`) — решение владельца О-14 (а): ссылка, поданная любым именованным аргументом, судится общим правилом по литеральным аргументам того же вызова (литеральный кортеж / список — позиционные аргументы ссылки, литеральный словарь — именованные), а не таблицей ключей отдельных API; закрытая таблица ключа ссылки `REFERENCE_KEYWORDS` выведена из общего модуля, из ввоза обоих гейтов и из `REQUIRED_SHARED_NAMES`; расхождение гейтов на `Timer(…, args=…)` снято тем же правилом; цена — в сторону лишней находки («handler(fn=update, data={"phone": x})»), названа в шапке гейта писателя; аргументы нелитералом («args=row», «kwargs=opts», «*rows») — пункт (1) границы гейта писателя (поток данных); самопроверка гейта писателя — «98 952» формы под заявлением, ноль промахов после двух циклов (обёртка носителя под именем, переданная планом 16-32; позиционные литералы за ссылкой; каждая ссылка носителя; именованная ссылка применённой обёртки; `starmap`) (not in the current review) |
| WR-21 | warning | fixed | `16-33` задачи 1 и 3, GREEN `e478c8c2`, `6fbc414c`, и два цикла самопроверки исполнителя, GREEN `e72a8e53`, `c5e82453` — решение владельца О-14 (а): одинарная кавычка — четвёртый вид кавычки идентификатора SQLite (`_SQL_QUOTE`; `_sql_visible` над разбором `_sql_scan` оставляет видимым однословный `'…'`, «''» внутри — кавычка литерала), шапка называет четыре вида кавычек («все четыре»); признак «ключевое слово в кавычках» у `UPDATE` / `SET` / `WHERE` — по разбору отрезков, а не по соседним символам (циклы самопроверки: ключевое слово вплотную к кавычке — «1 008» форм, между двумя отрезками в кавычках — «24»); трасер `test_a_planted_backfill_with_a_single_quoted_identifier_reddens_the_gate`, правило шапки `test_the_writer_gate_header_names_four_quote_kinds_and_every_column_constructor`; цена однословной строки-значения по замеру — находка только при «=» за «'phone'» на нулевой глубине `SET` («CASE WHEN 'phone' = kind», «SET note = 'phone' = kind»), у «SET note = 'phone'», «WHERE status = 'phone'», CTE и скобок — ноль; самопроверка оси лексики SQL — «100 908» форм под заявлением, ноль промахов после двух циклов; ПОПРАВКА клетки WR-16: довод «текст «phone = …» внутри литерала … больше не находка (колонку он не пишет)» ложен для одного слова в одинарных кавычках на месте идентификатора — SQLite читает его как идентификатор, и `SET 'phone' = …` пишет колонку (замер верификатора раунда 6, «+78»; замер исполнителя 16-33 на SQLite «3.53.1»); строка WR-16 перенесена без изменений (not in the current review) |
| WR-22 | warning | fixed | `16-33` задача 1, GREEN `e478c8c2`, и цикл самопроверки исполнителя, GREEN `e72a8e53` — решение владельца О-14 (а): виды 5 (в) и (г) судятся по видимому SQL (`_raw_sql_write` и `_raw_sql_subject` ищут `RAW_SQL_PHONE_WRITE` в `_sql_visible`), комментарий SQL («/* x */», «-- x⏎») в голове оператора запись больше не прячет; голова допускает кавычку вплотную к таблице (`_SQL_HEAD_GAP`, цикл 1: «INTO'messenger_accounts'», «COPY"…"»); отрезок предмета находки берётся из исходного текста по позициям совпадения; три формы ревью — строки `LITERAL_FORM_CASES`, комментарий в голове вставки в чужую таблицу — ноль; самопроверка — комментарий перед и после каждого слова головы и во всех зазорах сразу, ноль промахов на итоговом дереве (not in the current review) |
| WR-23 | warning | fixed | `16-33` задача 2, GREEN `8aba9962`; шапка вида 3 — задача 3, GREEN `6fbc414c` — решение владельца О-14 (а): `Column` и `ColumnClause` в `COLUMN_CONSTRUCTORS` (рядом с `column`, `literal_column`), `name` в `COLUMN_NAME_KEYWORDS`; три наименования в матрице контекстов (`column-class`, `column-clause-class`, `column-class-name-keyword`; «39» наименований против «714» контекстов) и две позиции имени (`column-class`, `column-clause-class` в `NAME_POSITIONS`, «12» позиций); обе формы ревью («values({sa.Column("phone"): x})», «values({ColumnClause("phone"): x})») — строки `LITERAL_FORM_CASES`, «sa.Column("title")» — ноль; самопроверка оси класса конструктора — «116 424» формы под заявлением, ноль промахов; шапка вида 3 называет `Column(…)` (имя позицией или `name=`) и `ColumnClause(…)` (not in the current review) |
| IN-15 | info | fixed | `16-32` задача 2, GREEN `50d6e5cf` (копии `_iterable_elements` и `_getattr_literal` гейта приватности сняты, он берёт `iterable_elements` и `getattr_literal` общего модуля), и `16-34` задача 2, GREEN `a28d6efc` (копии семантики носителя гейта писателя — `_iterable_elements`, `_getattr_literal`, `_expanded_arguments`, `_forwarded_arguments`, `_elementwise_arguments`, `_UNJUDGED_ELEMENT`, своя `LITERAL_CONTAINER_WRAPPERS` — сняты; докстринги правила-паритета называют проверяемое: названные точки не переопределены, копию под другим именем видит только поведенческая половина на ячейках общего словаря; имена семантики носителя в `GRAMMAR_FUNCTIONS` / `GRAMMAR_TABLES` и правило-контроль `test_the_structural_half_reddens_a_redefined_grammar_point` вписаны коммитом теста «9dc72673» и зеленеют с этим GREEN; «24» имени `GRAMMAR_FUNCTIONS` и «7» таблиц — на итоговом дереве 16-34) — решение владельца О-15; остаток, записанный в 16-34-SUMMARY («Остаётся открытым»), сверх находки ревью: гейт приватности держит свою `_carrier_wrappers` (семантика обёртки носителя под именем, которую гейт писателя берёт из общих `carrier_wrapper_bindings` / `applied_wrapper`; запрет №4 плана 16-34), комментарий `tests/test_phone_privacy_gate.py` в строке «362» называет выведенную `REFERENCE_KEYWORDS`, а формы самопроверки 16-34 (обёртка носителя под именем, позиционные кортежи `apply_async`, `starmap`) закреплены строками гейта писателя, но не строками `REFERENCE_CARRIERS`, и поведенческая половина паритета их не держит (not in the current review) |
| WR-14 | warning | fixed | `16-27` задачи 1–3, GREEN `25f2bb5e`, `8aaded0d`, `d9323cd0`, и четыре цикла самопроверки исполнителя, GREEN `b8c84eb3`, `18e13784`, `e5df9047`, `0ea91ee8`; гейт приватности на той же грамматике — `16-29` задача 1, GREEN `9df72956`; правило-паритет `tests/test_phone_gates_parity.py` — `16-29` задача 2, GREEN `29249009` — решение владельца О-12 (а): заявление шапки прежнее; общая грамматика связывания `tests/phone_gate_grammar.py` (распаковка кортежа, в том числе со звёздной целью, `:=`, цель-атрибут `self.<x>` / `cls.<x>` в любом методе, тело класса, `getattr`-строка как атрибут, связанный `partial`) и один перечень носителей с гейтом приватности (`run_sync`, `to_thread`, `run_in_executor`, `map` поэлементно, `Context.run`); получатель `methodcaller` судится у любого применения; правило-матрица оси B `test_every_binding_form_of_a_writer_api_alias_is_judged` («270» ячеек: «9» форм × «5» значений опознания × прямой вызов и «5» носителей); самопроверка исполнителя — «63 688» форм, ноль промахов; связывание вызовом или через пространство имён («setattr(self, "f", api)», «globals()["f"] = api») не ловится — названо в пункте (1) шапки с причиной «поток данных через контейнер»; подготовительное переименование таблицы гейта `BINDING_FORMS` в `PARAMETER_BINDING_FORMS` — коммит «a12ad73c» (refactor) (not in the current review) |
| WR-15 | warning | fixed | `16-28` задача 1, GREEN `17ef8eb8`, и шапка — задача 3, GREEN `5bf3e3f5` — решение владельца О-12 (а): `_phone_column` композиционен — наименование колонки номера в позиции имени индекса, поиска, конструктора и `getattr` любой глубины тоже запись («MessengerAccount.__table__.c[MessengerAccount.phone.key]», «t.c.get(M.phone.key)», «column(M.phone.key)»), а `getattr(X, "<const>")` судится как производная `X`; четыре новые строки `COLUMN_NAMINGS` («36» наименований против «714» контекстов); таблица `NAME_POSITIONS` («10» позиций) и правило `test_every_column_naming_nested_in_every_name_position_is_a_write`; самопроверка исполнителя оси A — глубина 1 в каждом контексте, глубина 2, позиции сверх таблицы и контроль чужой колонки, «350 012» форм, ноль промахов, циклов по оси A не понадобилось; предмет находки называет колонку и тогда, когда текст наименования её не показывает (`_naming_text`) (not in the current review) |
| WR-16 | warning | fixed | `16-28` задача 2, GREEN `a412c3c5`, и два цикла самопроверки исполнителя оси SQL, GREEN `5e826558`, `6c6bbea2`; шапка — задача 3, GREEN `5bf3e3f5` — решение владельца О-12 (а): виды 5 (а) и (б) судит код `_raw_sql_set_writes` над предложением `SET` на нулевой глубине скобок — подзапрос со своим `WHERE`, литерал, комментарий SQL или идентификатор в кавычках перед колонкой запись больше не прячут, строчный конструктор судится в любой позиции `SET`; `RAW_SQL_PHONE_WRITE` несёт только (в) и (г); фильтр по номеру в `WHERE` и в подзапросе — не запись; самопроверка оси SQL — «10 142» формы, ноль промахов после двух циклов («where» в кавычках или в комментарии SQL перед колонкой; склейка `+` из одних констант судится один раз — у склейки); сужение только в сторону не-записи: текст «phone = …» внутри литерала, комментария или строки в двойных кавычках больше не находка (колонку он не пишет); `_raw_sql_set_writes` возвращает список найденных записей, а не `bool` (not in the current review) |
| WR-17 | warning | fixed | `16-29` задачи 1–3, GREEN `9df72956`, `29249009`, `334b0b9a`, и три цикла самопроверки исполнителя, GREEN `aff284c9`, `90803f88`, `e2807607` — умолчание прохода и решение владельца О-12 (а): носитель ссылки на журнал — любой вызов с аргументами после ссылки (`to_thread`, `run_in_executor`, `map`, `Context.run`, `run_sync`, `fn=`), синтетический вызов журнала судится аргументами после ссылки (`_carried_log_calls`); `methodcaller` над опознанным получателем, в том числе под `fn=` (`_applied_log_methodcaller`); псевдонимы `partial` и `methodcaller` (`_wrapper_aliases`); связывания — из общей грамматики `tests/phone_gate_grammar.py`; правило-матрица `test_every_binding_form_of_a_log_reference_is_judged` («270» ячеек) и правило-паритет обоих гейтов `tests/test_phone_gates_parity.py`; самопроверка — «160 080» форм, ноль промахов; ссылка, связанная `setattr` / `globals()` / `vars()`, взятая из контейнера, возвращённая не-`partial` вызовом или обёрнутая в `lambda`, не ловится — названа в «ГРАНИЦЕ СРЕДСТВА» с причиной «поток данных»; живые деревья — «224/68/93» вызовов и 0 находок (было «221/68/93»: три новых распознанных вызова в app/pages/history.py, строки «288», «289», «293», — цена строгости, названная шапкой, находок на них нет) (not in the current review) |
| IN-13 | info | fixed | `16-26` задача 1, GREEN `d51dc5b2` — решение владельца О-13: правило-сверка пункта 5 докстринга `normalize_manual` разбирает три скобки причин (`_item_five_groups`: сам `MOBILE`, только `VOIP`, классы `FIXED_LINE`) и сверяет каждую с `MANUAL_BOUNDARY_EXAMPLES` в обе стороны; обратное вложение — по отрезку остатка: код региона в предложении остатка обязан быть ключом таблицы; контроли над текстом, мутированным в памяти (TW в скобке MOBILE, RS в скобке VOIP или в предложении остатка), краснят правило; коммит RED — «a501f826»; код `normalize_manual` прежний (not in the current review) |
| IN-14 | info | fixed | `16-26` задача 2, GREEN `ce5d2378` — решение владельца О-13: пункт 7 докстринга `normalize_manual` одной фразой ссылается на остаток, измеренный в пункте 5, без чисел и без регионов таблицы; правило `test_item_seven_points_to_its_remainder_in_item_five`; коммит RED — «ab206ce9»; поведение `normalize_manual` AST-равно «33a31ee3» (not in the current review) |
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
