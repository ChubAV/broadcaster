---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 01
subsystem: ui
tags: [account-label, phone, jinja-macro, tdd, tracer, htmx-fragments]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "колонка messenger_accounts.phone, format_phone (D-06), писатель fill_reported_phone и writer_scope"
provides:
  - "app/services/account_label.py: PHONE_UNKNOWN_TEXT, AccountRow, AccountLabel (text, plain, plain_with_id), id_mark, shown_phone, row_of, label_of, build_labels, labels_for"
  - "app/application/accounts/labels.py: load_account_rows(session, user_id) — три колонки, одна инструкция, граница владельца"
  - "components/account_label.html: макросы account_label и account_id_mark, адреса data-account-label и data-account-id"
  - "Jinja-глобалы phone_labels и phone_label в app/pages/common.py"
  - "tests/account_label_support.py: seed_account, label_texts, id_mark_texts, muted_label_ids, element_text, option_texts, title_text"
  - "чип аккаунта в карточке расписания редактора показывает «{Мессенджер} {номер}» (первый экран PHONE-03/04/05)"
affects: [17-02, 17-03, 17-04, 17-05, 17-06, 17-07, 17-08, 17-09]

actuals:
  tokens: 11000
  tasks: 3
  commits: 6
plan_head_before: f542dcd36b944f990e3472ffdc106ebc8a89d2a3
plan_head_after: 8111c099b27379905390ada93535cda3ba89785d

tech-stack:
  added: []
  patterns:
    - "Данные из глобала, разметка из макроса: правило в чистом сервисе, <span data-account-label> рисует макрос, MARKUP_BUILDERS остаётся 0"
    - "Двойник — по готовой подписи (тип, shown_phone) через одну закрытую _twin_key для build_labels и label_of"
    - "Карта «аккаунты пользователя» — по пользователю одной проекцией трёх колонок, а не по порции"
    - "Тесты находят подпись по адресу элемента (html.parser со счётчиком вложенности), а не подстрокой"

key-files:
  created:
    - app/services/account_label.py
    - app/application/accounts/labels.py
    - app/templates/components/account_label.html
    - tests/account_label_support.py
    - tests/test_services/test_account_label.py
    - tests/test_application/test_account_label_rows.py
  modified:
    - app/pages/common.py
    - app/templates/ads/includes/sched_card.html
    - tests/test_pages/test_editor_schedules.py

key-decisions:
  - "Тела-заготовки RED несут окончательные сигнатуры, поэтому каждое падение — утверждение, а не ошибка сбора; пустое/пробельное значение и label_of/plain_with_id доведены задачей 2, как велел план"
  - "phone_label — именованная функция _phone_label, а не lambda в присваивании глобала: читается и не попадает под правила динамических конструкций"
  - "Знак # перед id в Python — одна f-строка f\"#{account_id}\" в id_mark; в шаблонах — одно печатающее место account_id_mark"

patterns-established:
  - "Адресная проверка подписи: label_texts(html)[str(id)] — список текстов всех элементов с таким адресом"
  - "Плоская форма подписи (plain / plain_with_id) идёт в title=, <title>, <option>, звено join; разметка — только макрос"

requirements-completed: [PHONE-03, PHONE-04, PHONE-05]

coverage:
  - id: D1
    description: "Чип аккаунта в карточке расписания редактора: «Telegram +7 999 123-45-67», «WhatsApp Номер неизвестен» (приглушён), у двойника — «… #id», у уникальной подписи #id нет"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_account_chip_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_an_account_without_a_number_reads_as_unknown_on_the_chip"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_twin_chips_carry_a_muted_id"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило подписи: пустое/пробельное — «Номер неизвестен», неразбираемое — как есть, двойник — по готовой подписи внутри мессенджера, плоские формы plain и plain_with_id"
    requirement: "PHONE-04"
    verification:
      - kind: unit
        ref: "tests/test_services/test_account_label.py (44 проверки: SHOWN, TWINS, плоские формы, label_of, чистота модуля)"
        status: pass
    human_judgment: false
  - id: D3
    description: "title= чипа и звено сводки карточки несут плоскую подпись (у двойника — с #id); переписано правило test_editor_card_renders_data на адрес"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_the_chip_title_and_the_panel_text_carry_the_plain_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_card_renders_data"
        status: pass
    human_judgment: false
  - id: D4
    description: "Загрузчик строк аккаунтов пользователя: одна инструкция SELECT, три колонки, граница владельца, любой статус"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_application/test_account_label_rows.py (4 теста)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Раскладка чипа с номером на 320–375px — правила CSS приходят планом 17-09, здесь разметка без них"
    requirement: "PHONE-03"
    verification: []
    human_judgment: true
    rationale: "Вид и усечение подписи на узких экранах — предмет CSS плана 17-09 и обхода владельца; этот план стилей не правит"

duration: 21min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 01: Один помощник подписи аккаунта и сквозной срез через чипы расписания

**Номер из колонки `phone` проходит чистое правило подписи, глобал `phone_labels` и макрос `components/account_label.html` и оказывается на чипе карточки расписания по адресу `data-account-label` («Telegram +7 999 123-45-67», «WhatsApp Номер неизвестен», у двойника — приглушённый `#id`); рядом — загрузчик строк пользователя одной инструкцией и общий тестовый модуль посева и разбора адресов.**

## Performance

- **Duration:** 21 min (по часам хоста; прогоны pytest под общим замком — около 10 мин из них)
- **Started:** 2026-11-20T16:00:20Z
- **Completed:** 2026-11-20T16:21:06Z
- **Tasks:** 3 (все `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 9 (6 новых, 3 изменённых)

## Accomplishments

- **Сквозной срез (трассер):** колонка `phone` → писатель Фазы 16 → `shown_phone` / `format_phone` → `phone_labels` → макрос → `<span data-account-label="<id>">` на чипе `/ads/{id}/edit?sched={id}`. Локальный макрос `account_label(account)` и инлайн-словарь `{'tg_user': 'Telegram', …}` в `sched_card.html` удалены, имя канала берётся из `MESSENGER_LABELS`.
- **Правило подписи целиком:** `None`, пустая и пробельная строка — «Номер неизвестен» (`mono--muted`); сохранённое неразбираемое (`abc`, `=1+1`, `<b>x</b>`) — как есть; двойник — совпала ГОТОВАЯ подпись `(тип, shown_phone)`: два «неизвестных» одного мессенджера и `+79991234567` / `+7 999 123-45-67` двойники, Telegram и WhatsApp с одним номером — нет.
- **Загрузчик** `load_account_rows(session, user_id)`: один `SELECT id, type, phone WHERE user_id = …`, аккаунты любого статуса, без `credentials` и `session_data`.
- **Общий тестовый модуль** `tests/account_label_support.py` вместо пятой копии `_seed_account` и вместо разбора подстрокой.

## Public contract for plans 17-02 … 17-09

### `app/services/account_label.py` (чистый, без БД и Jinja)

| Имя | Сигнатура / состав |
|---|---|
| `PHONE_UNKNOWN_TEXT` | `"Номер неизвестен"` |
| `AccountRow` | `NamedTuple(id: int, type: str, phone: str \| None)` |
| `AccountLabel` | `@dataclass(frozen=True, slots=True)`: `account_id: int`, `channel: str`, `phone_text: str \| None`, `twin: bool`; свойства `text` (номер или «Номер неизвестен»), `plain` (`«{channel} {text}»`, у двойника + ` #id`), `plain_with_id` (`#id` ВСЕГДА, для админки D-17) |
| `id_mark(account_id: int) -> str` | единственная сборка `#id` в Python: `f"#{account_id}"` |
| `shown_phone(stored: str \| None) -> str \| None` | `None`/`""`/пробелы → `None`; иначе `format_phone(stored)`; неразбираемое возвращается как есть |
| `row_of(account) -> AccountRow` | из ORM-объекта или DTO с полями `id`, `type`, `phone` |
| `label_of(subject: AccountRow, rows: Iterable[AccountRow]) -> AccountLabel` | двойник — строка с иным `id` и тем же `_twin_key`; `rows` может не содержать `subject`; `rows=()` — `twin is False` |
| `build_labels(rows) -> dict[int, AccountLabel]` | подписи ВСЕХ аккаунтов одного пользователя; `label_of(row, rows) == build_labels(rows)[row.id]` закреплено тестом |
| `labels_for(accounts) -> dict[int, AccountLabel]` | `build_labels(row_of(a) for a in accounts)`; глобал `phone_labels` |
| `_twin_key(type, shown)` | закрытая; ключ `(type, готовая подпись)` |

### Глобалы Jinja (`app/pages/common.py`, без сессии БД)

- `phone_labels(accounts)` = `labels_for` — словарь `id → AccountLabel` по списку ВСЕХ аккаунтов пользователя (двойник считается по списку, а не по чипу). Вызывается внутри импортированных макросов (контекст вызывающего им не передаётся, глобалы окружения видны).
- `phone_label(account)` — подпись ОДНОГО объекта без признака двойника (`label_of(row_of(account), ())`); только админка (D-17), где `#id` печатается всегда отдельным элементом.

### Макрос `components/account_label.html`

`{% from "components/account_label.html" import account_label, account_id_mark %}`

- `account_label(label, show_channel=false, with_twin_id=true)` рисует ТОЛЬКО `<span>`:
  `<span class="acct-label" data-account-label="ID">` + (при `show_channel`) `<span class="acct-label__chan">Канал</span> ` + `<span class="acct-label__text mono mono--muted|mono--bright">ТЕКСТ</span>` + (при `with_twin_id and label.twin`) ` ` + `account_id_mark(ID)`.
  `mono--muted` — когда `label.phone_text is none`, иначе `mono--bright`.
- `account_id_mark(account_id)`: `<span class="acct-label__id mono mono--muted" data-account-id="ID">#ID</span>` — единственное место печати `#` перед id аккаунта в шаблонах.
- **Админка (D-17):** `account_label(label, with_twin_id=false)` + отдельный `account_id_mark(id)` — `#id` всегда, без дублирования у двойника.
- **Адресный контракт:** `data-account-label="<id>"` — подпись (полный текст элемента: канал, номер, `#id` двойника); `data-account-id="<id>"` — отдельный знак `#id`. Классы `acct-label`, `acct-label__chan`, `acct-label__text`, `acct-label__id` — для CSS плана 17-09. Подпись печатается только автоэкранированием; в `x-*` / `hx-*` не класть.

### `app/application/accounts/labels.py`

`async def load_account_rows(session: AsyncSession, user_id: int) -> list[AccountRow]` — ОДНА инструкция `SELECT messenger_accounts.id, .type, .phone WHERE user_id = :uid`, без `ORDER BY` (порядок строк не определён — потребители собирают `build_labels`), аккаунты любого статуса, `credentials` / `session_data` не читаются, журнала нет.

### `tests/account_label_support.py`

- `async seed_account(session, user_id, type_="tg_user", *, phone=None, stored_as_is=None, status="active", account_id=None) -> int` — возвращает id; `phone` ставит ТОЛЬКО `fill_reported_phone` (с проверкой `PhoneWrite.WRITTEN`), `stored_as_is` — внутри `writer_scope()`.
- `label_texts(html) -> dict[str, list[str]]` — **значения — СПИСКИ** текстов всех элементов с таким адресом (порядок документа, пробелы схлопнуты); проверять `x in label_texts(html)[str(id)]` или `== [...]`; отсутствие адреса — `KeyError`.
- `id_mark_texts(html)` — то же для `data-account-id`; `muted_label_ids(html) -> set[str]`; `element_text(html, element_id) -> str | None`; `option_texts(html, select_name) -> dict[value, text]`; `title_text(html) -> str`.
- Локальные в `test_editor_schedules.py` и НЕ публичные: `_editor_html`, `_ChipTitles`, `_SummaryTitles`.

### Для плана 17-08 (гейт)

Печатающие знак `#` перед id аккаунта: шаблоны — `components/account_label.html` (макрос `account_id_mark`, одно вхождение вне комментариев); Python — `app/services/account_label.py` (f-строка в `id_mark`, одна строковая константа модуля, оканчивающаяся на `#`).

## Task Commits

1. **Задача 1 (tracer): номер на чипе расписания по `data-account-label`**
   - RED `a72ceb74` — `test(17-01): add failing tests for the account chip number at data-account-label`
   - GREEN `3097018e` — `feat(17-01): show the account number on the schedule chip by data-account-label`
2. **Задача 2: правило подписи целиком**
   - RED `d2e12c6c` — `test(17-01): add failing table for the account label rule`
   - GREEN `5492dd6f` — `feat(17-01): implement the full account label rule and the phone_label global`
3. **Задача 3: строки аккаунтов одним запросом**
   - RED `6a1d01ae` — `test(17-01): add failing test for the one-statement account rows loader`
   - GREEN `8111c099` — `feat(17-01): load the account rows of a user in one three-column statement`

REFACTOR-коммитов нет (чистой переделки не было). **Plan metadata:** коммит `docs(17-01)` этой сводки.

## TDD Gate Compliance

RED (`test(17-01):`) предшествует GREEN (`feat(17-01):`) у всех трёх задач: каждый `feat` — потомок своего `test`. Нарушений нет.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (в `.pytest_cache/gsd-red/`, вне git): `17-01-t1.{xml,log,json}`, `17-01-t2.*`, `17-01-t3.*`. Каждая запись прошла `gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_editor_schedules.py::test_the_account_chip_shows_the_number_at_its_address` | `5 failed, 1 passed` | `KeyError: '1'` (`label_texts(html)["1"]`) | Цель выполнилась и упала на утверждении плана: в неизменённом шаблоне адреса `data-account-label` нет. Не ошибка сбора — заготовка сервиса с окончательными сигнатурами импортируется. Пятый красный (`…carry_the_plain_label`) падает на `assert None == 'WhatsApp Номер неизвестен #1'` по той же причине — нет подписи с адресом |
| 2 | `FAILED tests/test_services/test_account_label.py::test_a_blank_stored_number_reads_as_unknown[empty]` (и `[blank]`) | `15 failed, 29 passed` | `assert '' is None` (`AccountLabel(…, phone_text='')`) | Падает на планируемом утверждении: пустое значение даёт пустую подпись, а не «Номер неизвестен». `test_the_module_is_pure` зелёный при RED по построению — это охранник чистоты, не проверка поведения |
| 3 | `FAILED tests/test_application/test_account_label_rows.py::test_rows_cover_every_account_of_the_user_in_one_statement` | `4 failed` | `assert 0 == 5` (`len([])`) | Заготовка возвращает `[]`, пять аккаунтов пользователя не приходят; остальные три красных падают на тех же отсутствующих строках и нуле инструкций, а не на пустоте теста |

## Verification (замеры; база — `baseline-w1.log` оркестратора)

| Проверка | База (f542dcd3) | Итог (8111c099) |
|---|---|---|
| `tests/test_pages/test_editor_schedules.py` | 129 passed | **133 passed** (+4 новых; `test_editor_card_renders_data` переписан на месте) |
| `tests/test_services/test_account_label.py` | — | 44 passed |
| `tests/test_application/test_account_label_rows.py` + сервис | — | 48 passed вместе (4 + 44) |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| `prohibitions_census.py --check` | 953 строки, согласие | 953 строки, согласие |
| `compileall -q app main.py tests` | rc 0 | rc 0 |
| Соседние страницы (`test_responsive_markup`, `test_schedules_poisoned_row`, `test_identifier_bounds`, `test_ads_editor`, `test_schedules_detached_account`, `test_schedules_list`, `test_schedule_ownership`, `test_schedule_invariants`) | `test_responsive_markup` 142 passed | **298 passed, 1 failed** — `test_responsive_markup.py::test_template_inventory` (см. отклонение 1) |
| `tests/test_planning` | 218 passed, 2 skipped | см. конец сводки |

Объявленные числа гейтов не сдвинуты (`POST_PAIR_CASES_DECLARED` и прочие — прогон зелёный). Приёмочные greps задач 1–3 сняты: `class AccountLabel` = 1; четыре `def` задачи 1 = 4; `globals["phone_labels"]` = 1; `globals["phone_label"]` = 1; `{#` первой строкой компонента; макрос рисует только `span` (`'div' not in h`); `'tg_user': 'Telegram'` вне комментариев = 0; `macro account_label` в `sched_card.html` = 0; `Telegram #{account.id}` в тесте = 0; `markupsafe|jinja2|sqlalchemy` в сервисе = 0; AST-проверка единственной константы на `#` — выход 0; `MessengerAccount.(credentials|session_data)` и `logger|structlog|print(` в загрузчике = 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Правка вне перечня плана — НЕ ВНЕСЕНА, ТРЕБУЕТ РЕШЕНИЯ ОРКЕСТРАТОРА] Счётчик файлов каталога компонентов краснеет от нового компонента**
- **Found during:** проверка соседних страниц после задачи 3
- **Issue:** `tests/test_pages/test_responsive_markup.py::test_template_inventory` (строка `assert len(components) == 16, …`, около `:3192`) считает файлы `app/templates/components/*.html`; новый `account_label.html` делает их 17, тест красный. Это прямое следствие файла, который план обязывает создать; ни в `files_modified` 17-01, ни в планах 17-02…17-09 это правило не названо (`grep` по записям фазы пуст).
- **Fix:** НЕ внесён: заметки оркестратора запрещают правку файлов вне `files_modified` без записи, а счётчик — объявленное число гейта. Нужная правка — одна: `16 → 17` в этом утверждении и строка в комментарии над ним («Плюс семнадцатый — account_label.html, подпись аккаунта Фазы 17: одно место, собирающее «{Мессенджер} {номер}» вместо копий в шаблонах»).
- **Files modified:** нет
- **Verification:** прогон `tests/test_pages/test_responsive_markup.py` на базе — 142 passed; на 8111c099 — `assert 17 == 16` с перечнем `['account_label.html', 'alert.html', …]`
- **Impact:** до внесения правки красна ровно одна проверка; после слияния её закроет оркестратор отдельным коммитом либо план 17-02, который и так правит `test_responsive_markup.py` (`test_accounts_card_renders_data`).

**2. [Rule 3 — расширение теста, не отступление] Дополнительные проверки сверх перечня плана**
- В `test_account_label.py` добавлены `test_an_unparseable_number_is_shown_as_it_is_not_as_unknown`, `test_label_of_does_not_need_the_subject_among_the_rows`, `test_an_unfamiliar_type_keeps_its_own_word_as_the_channel`, `test_shown_phone_table`; план требовал не меньше 20 строк таблиц — получено 44 проверки.
- В `test_editor_schedules.py` к четырём тестам плана добавлены локальные разборщики `_ChipTitles` / `_SummaryTitles` и помощник `_editor_html` (для `title=` чипа и сводки нужен разбор атрибутов, которого публичные функции `account_label_support` не дают; сделаны локальными, чтобы не раздувать общий модуль сверх названного в плане состава).

### Plan-vs-measured (измерение побеждает)

- **Цель RED у задачи 2 с параметрами:** план называет `FAILED …::test_a_blank_stored_number_reads_as_unknown`; измерено `…::test_a_blank_stored_number_reads_as_unknown[empty]` и `[blank]` (параметризация по `ids=["empty","blank"]`). Глагол `check tdd-red-evidence` принимает цель только с идентификатором параметра (`test_a_blank_stored_number_reads_as_unknown[empty]`); голое имя дало `no_target_test_failure` — это формат отчёта JUnit, не промах теста.
- **Литерал RED у задачи 1:** план — `KeyError: '`; измерено `KeyError: '1'` — совпадает.
- **Вторые `<automated>` у задач 1–2:** вместо `-k "chip or renders_data"` и `-k "blank or twin or plain or agrees or pure"` прогнаны полные файлы (133 и 44 passed) и для задачи 1 дополнительно `-k "chip or renders_data or twin or panel_text or unknown"` (6 passed): полный прогон — надмножество выборки.

---

**Total deviations:** 1 вне перечня файлов (не внесена, нужно решение оркестратора) + 1 расширение тестов
**Impact on plan:** продуктовый код и поведение — ровно по плану; единственное, что остаётся, — одна строка счётчика компонентов в чужом тестовом модуле.

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5760 тестов, ~46 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модули плана, оба набора сквозных гейтов, гейты номера, `tests/test_planning` и восемь соседних модулей страниц (выше). Каждый прогон pytest шёл под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния. Ориентация шла `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- **Рабочий файл улик:** `.pytest_cache/checks/make_red_record.py` собирает запись RED (JSON из JUnit XML) для `gsd_run check tdd-red-evidence`; лежит в игнорируемом `.pytest_cache/`.
- **Датчик каталога git:** файлы `gsd-plan-head-before-17-01` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами (песочница отказала составной команде с `git rev-parse` внутри подстановки).
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались.

## Issues Encountered

- Одна красная проверка вне плана (отклонение 1).
- Прогон `tests/test_pages/test_editor_schedules.py` целиком занимает ~2 мин под нагрузкой хоста: оба раза он уходил в фон, результат читался из журнала.

## Known Stubs

Нет: заготовки RED заменены реализациями в соответствующих GREEN-коммитах. На экране 320–375px правил CSS у подписи пока нет — их приносит план 17-09 (`D5` в `coverage`, `human_judgment: true`).

## Threat Flags

Нет новой поверхности. Угрозы плана: T-17-01 (хранимое значение «как есть») — только автоэкранирование, глобал отдаёт данные, макрос рисует `<span>`; значение `<b>x</b>` закреплено таблицей сервиса, на экранах враждебное значение проверяют планы 17-03 и 17-04; T-17-02 — условие `user_id` в единственном запросе, `test_rows_never_carry_another_users_account`; T-17-03 — проекция трёх колонок, тест на текст инструкции; T-17-04 — вызовов журнала в новом коде нет, гейты номера зелены.

## Next Phase Readiness

- Готово для 17-02…17-07: правило, глобалы, макрос, загрузчик, тестовый модуль и адресный контракт выше. Замечание для экранов, где аккаунт приезжает идентификатором (порции, опрос, история): строить карту `load_account_rows` + `build_labels` по пользователю, а не по порции (D-14).
- Для оркестратора: внести правку счётчика компонентов (отклонение 1) до или вместе с вехой слияния; без неё `test_responsive_markup.py::test_template_inventory` красен.

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Созданные файлы на месте: `app/services/account_label.py`, `app/application/accounts/labels.py`, `app/templates/components/account_label.html`, `tests/account_label_support.py`, `tests/test_services/test_account_label.py`, `tests/test_application/test_account_label_rows.py`.
- Коммиты `a72ceb74`, `3097018e`, `d2e12c6c`, `5492dd6f`, `6a1d01ae`, `8111c099` — предки HEAD; `git rev-list --count f542dcd3..HEAD` = 6 = `commits` во frontmatter.
- Тема-гейты: 3 × `test(17-01):`, 3 × `feat(17-01):`, `refactor(17-01):` — 0.
