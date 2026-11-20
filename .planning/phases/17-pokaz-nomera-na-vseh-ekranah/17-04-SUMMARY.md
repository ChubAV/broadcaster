---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 04
subsystem: ui
tags: [account-label, phone, history, jinja-macro, tdd, tracer, htmx-fragments]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: AccountLabel, build_labels, labels_for, load_account_rows, макрос account_label / account_id_mark, tests/account_label_support.py"
provides:
  - "app/pages/history.py: history_account_label(group, labels) -> AccountLabel | None; ключ account_label в словаре записи (список и порция); ключ acct_labels в контексте history_list"
  - "history_card(log, user=None, detail_base_path='/history', audience='user'): подпись по адресу data-account-label, ветки audience user | admin"
  - "history/list.html: подписи <option> фильтра — плоская строка acct_labels[acc.id].plain"
  - "tests/test_pages/test_account_label_history.py: 10 адресных тестов (карточка, порция, фильтр, D-14, D-15, D-18, T-17-13)"
affects: [17-06, 17-07, 17-08, 17-09]

actuals:
  tokens: 6200
  tasks: 3
  commits: 6
plan_head_before: 7baa1f8d725cd0d5019277866a1018544bf3eda5
plan_head_after: c4e4d16cbf698a97233fe39464a3f93336529121

tech-stack:
  added: []
  patterns:
    - "Подпись аккаунта записи журнала выводится ОДНОЙ функцией history_account_label из карты по пользователю; запись без группы или без account_id — None (D-15)"
    - "Страница строит подписи по уже загруженным all_accounts (без нового запроса), порция — одним load_account_rows по пользователю, отдельно от retry_availability"
    - "Аудитория карточки — явный параметр макроса, а не вывод из detail_base_path"

key-files:
  created:
    - tests/test_pages/test_account_label_history.py
  modified:
    - app/pages/history.py
    - app/templates/history/includes/history_card.html
    - app/templates/history/list.html

key-decisions:
  - "Тест D-14 сверяет признак двойника с build_labels(load_account_rows(...)) — тем же правилом, по которому строит подписи экран «Аккаунты»; самого /accounts в этом дереве ещё не конвертирован (план 17-02 той же волны), поэтому сверка через правило, а не через разметку соседнего экрана"
  - "Утверждения о фильтре — по одному на опцию (options[id] == ...), а не равенство словарей: так причинный литерал RED остаётся читаемым «assert 'tg_user #…» и падение называет конкретный аккаунт"

patterns-established:
  - "Карточка истории: {% if log.account_label %}account_label(log.account_label, with_twin_id=(audience != 'admin')){% if audience == 'admin' %}account_id_mark(...){% endif %}{% endif %}"

requirements-completed: [PHONE-03, PHONE-04, PHONE-05]

coverage:
  - id: D1
    description: "Карточка истории страницы /history показывает номер по адресу data-account-label; без номера — приглушённое «Номер неизвестен»; у двойника рядом #id"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_the_history_card_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_a_history_card_without_a_number_reads_as_unknown"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_a_twin_history_card_carries_the_id"
        status: pass
    human_judgment: false
  - id: D2
    description: "Порция прокрутки /history/partial подписана так же; признак двойника считается по всем аккаунтам пользователя; карта аккаунтов — один запрос на порцию без записи"
    requirement: "PHONE-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_the_history_batch_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_the_batch_twin_flag_matches_the_accounts_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_the_batch_reads_accounts_once"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_retry.py#test_retry_availability_takes_a_bounded_number_of_queries"
        status: pass
    human_judgment: false
  - id: D3
    description: "Запись без группы (аккаунта уже нет) остаётся без подписи аккаунта; «Номер неизвестен» ей не приписывается (D-15)"
    requirement: "PHONE-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_a_record_without_a_group_carries_no_account_label"
        status: pass
    human_judgment: false
  - id: D4
    description: "Подписи <option> фильтра истории — плоская строка из MESSENGER_LABELS («Telegram +7 999 123-45-67»), у двойника #id в конце; враждебное сохранённое значение экранируется"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_the_history_filter_option_carries_the_plain_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_twin_filter_options_carry_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_history.py#test_a_hostile_stored_value_is_escaped_in_the_option"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ветка audience='admin' макроса history_card (номер и отдельный #id всегда) — реализована, подключается и закрепляется планом 17-07"
    requirement: "PHONE-06"
    verification: []
    human_judgment: true
    rationale: "Админские шаблоны передают audience='admin' и админские сборщики дают ключ account_label только в плане 17-07; здесь ветка без потребителя и без теста — её проверит адресный модуль того плана"
  - id: D6
    description: "Раскладка карточки с номером на 320–375px — правила CSS приходят планом 17-09, здесь разметка без них"
    requirement: "PHONE-03"
    verification: []
    human_judgment: true
    rationale: "Вид и усечение подписи на узких экранах — предмет CSS плана 17-09 и обхода владельца; этот план стилей не правит"

duration: 61min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 04: Номер в карточке, порции и фильтре истории пользователя

**Карточка истории пользователя (страница `/history` и порция `/history/partial`) на месте прежнего «Акк #id» показывает номер по адресу `data-account-label` — «Номер неизвестен» приглушённо, `#id` только у двойника, у записи без аккаунта подписи нет; подписи `<option>` фильтра — плоская строка «Telegram +7 999 123-45-67»; подпись выводит одна функция `history_account_label`, а макрос `history_card` получил явный параметр аудитории.**

## Performance

- **Duration:** 61 мин по часам хоста; бо́льшая часть — ожидание общего замка pytest (четыре исполнителя на хосте)
- **Started:** 2026-11-20T17:14:18Z
- **Completed:** 2026-11-20T18:15Z
- **Tasks:** 3 (все `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 4 (1 новый, 3 изменённых)

## Что добавлено в `app/pages/history.py` и макрос — для планов 17-06 и 17-07

### `app/pages/history.py`

| Имя | Где | Состав |
|---|---|---|
| `history_account_label(group, labels)` | модуль, сразу после `parse_account_id` (до блока выгрузки) | `Group \| None` и `dict[int, AccountLabel]` → `AccountLabel \| None`; `None`, если группы нет или `group.account_id is None` (D-15), иначе `labels.get(group.account_id)` (аккаунт вне карты — тоже `None`). Публичное имя: админский модуль ввозит его тем же способом, что `parse_account_id` |
| ключ `"account_label"` | словарь записи `logs`: в `history_list` и в `history_partial` | `history_account_label(group, acct_labels)`; ключ `"account_id"` СОХРАНЁН |
| `acct_labels` в `history_list` | `labels_for(all_accounts)`; чтение `all_accounts` перенесено выше сборки `logs` | **нового запроса нет**; ключ `"acct_labels"` добавлен в контекст `history/list.html` (им строится фильтр) |
| `acct_labels` в `history_partial` | `build_labels(await load_account_rows(db, user.id))` — одна инструкция по ПОЛЬЗОВАТЕЛЮ, а не по порции; идёт после `retry_availability`, но отдельно | ключ в контекст порции НЕ кладётся — подпись уже внутри словарей записей |
| импорты | `from app.application.accounts.labels import load_account_rows`; `from app.services.account_label import AccountLabel, build_labels, labels_for` | |

**Для 17-06 (CSV):** `load_account_rows(db, user.id)` в `history.py` сейчас встречается РОВНО ОДИН раз (`history_partial`); CSV добавит второй вызов — до `db.stream(query)` и до `StreamingResponse(` (`test_export_cap_is_checked_before_the_streaming_response`). `retry_availability` не расширен. Импорт `load_account_rows`, `build_labels`, `AccountLabel` уже есть в шапке модуля.

**Для 17-07 (админская история):** четыре сборщика словаря записи — два здесь (готовы) и два в `app/pages/admin.py` (`:1457`, `:1551` по замеру плана): им нужно добавить `"account_label": history_account_label(group, acct_labels)`, ввезя функцию из `app.pages.history`; карта — `labels_for` по уже загруженным аккаунтам просматриваемого пользователя (`admin.py:1350`, `:1466` читают их сами) либо `build_labels(await load_account_rows(db, <просматриваемый user.id>))`.

### Макрос `history_card` (`app/templates/history/includes/history_card.html`)

- Сигнатура: `history_card(log, user=None, detail_base_path='/history', audience='user')`. Четвёртый параметр с умолчанием, поэтому все четыре существующих вызова (`history/list.html`, `history/partial_cards.html`, `admin/user_history.html`, `admin/history_partial_cards.html`) не менялись.
- Ввоз добавлен: `{% from "components/account_label.html" import account_label, account_id_mark %}`.
- Шапка `data-area="head"`: строка `mono('Акк #' ~ log.account_id, 'muted')` заменена блоком: при истинном `log.account_label` — `account_label(log.account_label, with_twin_id=(audience != 'admin'))`, при `audience == 'admin'` следом `account_id_mark(log.account_label.account_id)`. Без `log.account_label` (нет ключа, `None`) — ничего. Строка `#` у `group_external_id` не тронута.
- Значок канала в подпись НЕ входит (`show_channel` не задан: он уже стоит в шапке отдельным `messenger_icon`) — D-10.
- Шапка файла дополнена абзацем об `audience`; админские шаблоны включают этот же макрос и **пока без `audience='admin'` и без ключа `account_label` в своих сборщиках** — подписи аккаунта там сегодня нет (как и ожидает план: до 17-07 «Акк #…» ни одно правило админки не утверждало).

### `history/list.html`

Построение `account_options`: пары `(acc.id, acct_labels[acc.id].plain)` вместо `acc.type ~ ' #' ~ acc.id`. Прочие пары фильтра и чипсы не тронуты.

## Accomplishments

- **Сквозной срез:** колонка `phone` → `labels_for(all_accounts)` → `history_account_label` → ключ `account_label` словаря записи → `history_card` → `<span data-account-label="<id>">` на `/history`.
- **Порция прокрутки** подписана тем же правилом: карта читается один раз на порцию по пользователю (`≤ 2` запросов предпроверки повтора не тронуты); признак двойника совпадает с признаком на странице и на «Аккаунты», даже когда второй двойник в порцию не попал (D-14).
- **Запись без аккаунта** остаётся без подписи (D-15); `«Номер неизвестен»` ей не приписывается.
- **Фильтр истории** называет аккаунты плоской строкой из `MESSENGER_LABELS`; двойники различимы `#id` в конце; сырой `tg_user #5` ушёл.

## Task Commits

1. **Задача 1 (tracer): номер в карточке страницы `/history`**
   - RED `4c711b37` — `test(17-04): add failing tests for the account number on the history card`
   - GREEN `b7e88827` — `feat(17-04): show the account number on the history card by data-account-label`
2. **Задача 2: порция `/history/partial`**
   - RED `c119e286` — `test(17-04): add failing tests for the account number in the history batch`
   - GREEN `8fd99464` — `feat(17-04): label the history batch from one per-user account map`
3. **Задача 3: подписи `<option>` фильтра**
   - RED `a4edceb7` — `test(17-04): add failing tests for the history filter option labels`
   - GREEN `c4e4d16c` — `feat(17-04): name history filter options by the plain account label`

REFACTOR-коммитов нет. **Plan metadata:** коммит `docs(17-04)` этой сводки.

## TDD Gate Compliance

RED (`test(17-04):`) предшествует GREEN (`feat(17-04):`) у всех трёх задач: каждый `feat` — потомок своего `test`. Нарушений нет.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (`.pytest_cache/gsd-red/`, вне git): `17-04-t{1,2,3}.{xml,log,json}`. Каждая запись прошла `gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_account_label_history.py::test_the_history_card_shows_the_number_at_its_address` | `3 failed` | `KeyError: '1'` (`label_texts(html)["1"]`) | Цель выполнилась и упала на планируемом утверждении: в неизменённой карточке адреса `data-account-label` нет, `label_texts` не находит ключ. Не ошибка сбора и не фикстура: посев и `GET /history` отработали, 200. Соседние два красных падают тем же `KeyError` по той же причине |
| 2 | `FAILED tests/test_pages/test_account_label_history.py::test_the_history_batch_shows_the_number_at_its_address` | `3 failed, 4 passed` | `KeyError: '1'` | Порция до правки без подписи: адреса в ответе `/history/partial` нет. Красных три из четырёх тестов задачи: второй (`…twin_flag…`) падает `KeyError: '1'`, четвёртый (`…reads_accounts_once`) — `AssertionError: пять записей — пять подписей`; **`test_a_record_without_a_group_carries_no_account_label` зелёный при RED по построению** — это охранник D-15 («подписи нет, где её быть не должно»), до правки подписи нет нигде; он станет красным, если подпись когда-либо припишут записи без группы |
| 3 | `FAILED tests/test_pages/test_account_label_history.py::test_the_history_filter_option_carries_the_plain_label` | `3 failed, 7 passed` | `assert 'tg_user #1' == 'Telegram +7 999 123-45-67'` (в `AssertionError`) | Цель упала на утверждении плана: `<option>` несёт сырой `tg_user #1`. Остальные два красных (`…twin_filter_options…`, `…hostile…`) падают на том же `tg_user #1` |

## Verification (замеры; база — дерево 037eeaee по заметкам оркестратора)

| Проверка | База | Итог (c4e4d16c) |
|---|---|---|
| `tests/test_pages/test_account_label_history.py` | — | **10 passed** (3 + 4 + 3) |
| `tests/test_pages/test_account_label_history.py` + `tests/test_pages/test_history.py` | `test_history.py` 49 | **59 passed** (10 + 49) |
| `test_history_retry.py -k bounded_number_of_queries` | — | 1 passed (`≤ 2` запросов, `retry_availability` не расширен) |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| `test_history_export.py` (CSV не тронут) | 48 | 48 (в общем прогоне) |
| `test_responsive_markup.py` | 142 | 142 (в общем прогоне) |
| Один прогон страниц истории и админки: `test_history_export` (48), `test_history_retry` (63), `test_responsive_markup` (142), `tests/test_admin.py` (18), `test_admin_users.py` (38), `test_impersonation.py` (44), `test_identifier_bounds.py` (21) | — | **374 passed** (сумма собранных = 374) |
| `prohibitions_census.py --check` | 953 строки, exit 0 | 953 строки, согласие, exit 0 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `tests/test_planning` | 218 passed, 2 skipped | см. конец сводки |

Приёмочные greps: `'Акк #' ~ log.account_id` в `history_card.html` = 0; `'#' ~ log.group_external_id` = 1; `^def history_account_label` = 1; `"account_label": history_account_label` = 2; `load_account_rows(db, user.id)` = 1; `acc.type ~ ' #' ~ acc.id` в `history/list.html` = 0; `acct_labels[acc.id].plain` = 1. Объявленные числа гейтов не сдвинуты (`POST_PAIR_CASES_DECLARED` и прочие — прогон зелёный). Админские страницы истории рисуют прежний вывод: красных нет ни в `test_admin.py`, ни в `test_admin_users.py`, ни в `test_impersonation.py`; на них подписи аккаунта пока нет (как и до плана).

## Deviations from Plan

### Plan-vs-measured (измерение побеждает)

- **Литерал RED задачи 3:** план — `assert 'tg_user #`; измерено `assert 'tg_user #1' == 'Telegram +7 999 123-45-67'` — совпадает (утверждение по одной опции, а не равенство словарей: так литерал читается в сообщении).
- **Тест D-14 против «экрана Аккаунты»:** план называет тест `test_the_batch_twin_flag_matches_the_accounts_screen` и требует «тот же признак, что на `/accounts`». В дереве этого плана `/accounts` ещё не конвертирован (его делает 17-02 той же волны), поэтому адресно сверять с разметкой того экрана нельзя. Тест сверяет признак с `build_labels(await load_account_rows(...))` — тем же правилом, по которому подписи строит и «Аккаунты», — и сверх этого проверяет адресную подпись `Номер неизвестен #<id>` в порции при том, что записи второго двойника в порции нет. Имя теста оставлено по плану.
- **`test_a_record_without_a_group_carries_no_account_label` зелёный при RED:** нормально для охранника «подписи нет» (разобрано в таблице RED выше), не пропуск.

Других отклонений нет: правка вне перечня файлов не потребовалась, `retry_availability` не тронут, файлы 17-01 не правились.

**Total deviations:** 0 auto-fixed; 2 plan-vs-measured (оба описаны выше)
**Impact on plan:** продуктовый код и поведение — ровно по плану.

## Issues Encountered

- Прогоны pytest под общим замком ждали соседей по волне: обычный прогон модуля — 8–60 с, каждый внешний гейт — до нескольких минут; три раза выход уходил в фон, результат читался из журналов. Дефектов не вскрыто.

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5810 тестов, ~42 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модуль плана, `test_history.py`, оба набора сквозных гейтов, гейты номера, `test_history_export.py` (CSV не тронут), `test_responsive_markup.py` и пять страниц, рисующих историю пользователя или админа, перепись запретов и `compileall`. Каждый прогон pytest шёл под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния. Ориентация шла `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- **Рабочий файл улик:** `.pytest_cache/checks/make_red_record.py` собирает запись RED (JSON из JUnit XML) для `check tdd-red-evidence`; лежит в игнорируемом `.pytest_cache/`.
- **Датчик каталога git:** файлы `gsd-plan-head-before-17-04` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами (песочница отказала составным командам с `git rev-parse` внутри).
- **Правки через `Edit`/`Write`, не `cat <<EOF`:** песочница отказала составной команде с heredoc при дописывании тестов.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались.

## Known Stubs

Нет. На экране 320–375px правил CSS у подписи пока нет — их приносит план 17-09 (`D6` в `coverage`, `human_judgment: true`); ветка `audience='admin'` без потребителя до плана 17-07 (`D5`).

## Threat Flags

Нет новой поверхности. T-17-12: карта строится только по аккаунтам пользователя (`all_accounts` по `user_id`, `load_account_rows(db, user.id)`); `history_account_label` берёт подпись только из неё. T-17-13: подпись печатается автоэкранированием, `test_a_hostile_stored_value_is_escaped_in_the_option`. T-17-14: `None` без группы и без аккаунта, `test_a_record_without_a_group_carries_no_account_label`. Вызовов журнала в новом коде нет, гейты номера зелены (1161).

## Next Phase Readiness

- Готово для 17-06 (CSV «Номер» после «Аккаунт»; один дополнительный вызов `load_account_rows` до потока) и 17-07 (админские сборщики: `history_account_label` + `audience='admin'` в двух шаблонах). Подробности — в разделе «Что добавлено» выше.

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Созданный файл на месте: `tests/test_pages/test_account_label_history.py`.
- Коммиты `4c711b37`, `b7e88827`, `c119e286`, `8fd99464`, `a4edceb7`, `c4e4d16c` — предки HEAD; `git rev-list --count 7baa1f8d..HEAD` = 6 = `commits` во frontmatter.
- Тема-гейты: 3 × `test(17-04):`, 3 × `feat(17-04):`, `refactor(17-04):` — 0.
