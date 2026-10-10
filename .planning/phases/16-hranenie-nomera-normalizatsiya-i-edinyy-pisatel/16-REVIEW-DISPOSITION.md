---
phase: 16
review: 16-REVIEW.md
titles: json
findings:
  - id: WR-09
    severity: warning
    disposition: open
    title: "Manual input of a non-`+7` number plus extra digits is still saved as an invented \"manual\" number (BY, UA, KG, TR, IL, CN, DE)"
  - id: WR-10
    severity: warning
    disposition: open
    title: "The single-writer gate's new \"through the mechanism\" claim is again wider than the predicate: `Query.update(values=…)`, keyword `set_attribute`, and `run_sync(Session.bulk_*_mappings, …)` pass"
  - id: IN-08
    severity: info
    disposition: open
    title: "The auto-path boundary paragraph says \"besides real numbers\" the only extra acceptance is `TOO_SHORT`; 400 of the 558 `IS_POSSIBLE` values accepted in the same enumeration are not valid numbers"
  - id: IN-09
    severity: info
    disposition: open
    title: "The privacy gate neither catches nor names two logger forms that are identifiable by import or module binding"
  - id: IN-10
    severity: info
    disposition: open
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
open: 5
total: 21
recorded: 2026-10-10T07:01:03.448Z
---

# Phase 16: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-09 | warning | open | - |
| WR-10 | warning | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |
| IN-10 | info | open | - |
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
