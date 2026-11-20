---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 03
subsystem: ui
tags: [account-label, phone, jinja-macro, tdd, tracer, account-groups]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: label_of/row_of, load_account_rows, макрос components/account_label.html, адрес data-account-label, tests/account_label_support.py"
provides:
  - "account_groups_page кладёт в контекст acct_label — подпись аккаунта экрана с признаком двойника по всем аккаунтам пользователя"
  - "account_groups/list.html: номер в <title> (acct_label.plain), в шелловом <h1> (page_title) и в <h2 class=acct-head__name> (макрос account_label, show_channel=true)"
  - "tests/test_pages/test_account_label_groups.py: шесть адресных тестов шапки, <title>, двойника, враждебного значения и прозы"
affects: [17-09, 18]

actuals:
  tokens: 3600
  tasks: 2
  commits: 4
plan_head_before: 7baa1f8d725cd0d5019277866a1018544bf3eda5
plan_head_after: 834ad02fb6e6b7cc429294d3c16b1d68b7028a0b

tech-stack:
  added: []
  patterns:
    - "Ключ контекста acct_label (одна подпись), а не account_label: имя макроса компонента в шаблоне занято ввозом"
    - "Признак двойника экрана — label_of(row_of(account), await load_account_rows(db, user.id)): по аккаунтам пользователя, а не по порции"
    - "Прозу-отрицание в исходнике шаблона стережёт тест по тексту без пробелов, фраза собрана из двух половин"

key-files:
  created:
    - tests/test_pages/test_account_label_groups.py
  modified:
    - app/pages/account_groups.py
    - app/templates/account_groups/list.html

key-decisions:
  - "Порция groups/partial и опрос groups/sync-status не тронуты: шапку они не рисуют, подпись им не нужна"
  - "Локальный {% set MESSENGER_LABELS %} оставлен: это условие иконки канала в шапке, подписи он больше не касается"
  - "Тест прозы проверяет ДВЕ фразы-отрицания (из комментария и из приёмочного grep плана), обе собраны из половин"

requirements-completed: [PHONE-03, PHONE-04, PHONE-05]

coverage:
  - id: D1
    description: "Экран групп аккаунта подписывает аккаунт номером «{Мессенджер} {номер}» в шелловом <h1> и в <h2> карточки — ровно два адреса data-account-label"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_the_groups_header_shows_the_number_at_both_addresses"
        status: pass
    human_judgment: false
  - id: D2
    description: "<title> экрана — та же подпись простой строкой с прежним хвостом «— группы аккаунта — Broadcaster»"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_the_page_title_carries_the_plain_label"
        status: pass
    human_judgment: false
  - id: D3
    description: "Аккаунт без номера — приглушённое «Номер неизвестен» в обоих заголовках"
    requirement: "PHONE-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_an_unknown_number_is_muted_in_the_header"
        status: pass
    human_judgment: false
  - id: D4
    description: "Двойник: #id в обоих заголовках и в <title> простым текстом; признак по всем аккаунтам пользователя"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_a_twin_header_and_title_carry_the_id"
        status: pass
    human_judgment: false
  - id: D5
    description: "Враждебное неразбираемое значение колонки печатается текстом в <title>, <h1>, <h2>; живого <script> нет"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_a_hostile_stored_value_is_escaped_in_every_header_sink"
        status: pass
    human_judgment: false
  - id: D6
    description: "Проза шапки не отрицает колонку номера; credentials по-прежнему в разметку не выводится"
    requirement: "PHONE-03"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_label_groups.py#test_the_header_prose_no_longer_denies_the_phone_column"
        status: pass
    human_judgment: false
  - id: D7
    description: "Вид подписи в двух заголовках на 320–375px (усечение, приглушение)"
    requirement: "PHONE-03"
    verification: []
    human_judgment: true
    rationale: "Правила CSS приходят планом 17-09, вид на узких экранах — предмет обхода владельца; этот план стилей не правит"

duration: 25min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 03: Номер в шапке и `<title>` экрана групп аккаунта

**Экран `/accounts/{id}/groups` подписывает аккаунт «{Мессенджер} {номер}» в шелловом `<h1>`, в `<h2>` карточки (макрос `account_label`, адрес `data-account-label`, ровно два на странице) и в `<title>` (плоская `acct_label.plain`); у двойника — `#id`, у аккаунта без номера — приглушённое «Номер неизвестен», враждебное значение колонки — текстом.**

## Performance

- **Duration:** 25 min по часам хоста (основное время — ожидание общего замка pytest и прогоны соседних модулей)
- **Tasks:** 2 (обе `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 3 (1 новый, 2 изменённых)

## Accomplishments

- **Сквозной срез (трассер):** `account_groups_page` после `_load_owned_account` собирает `acct_label = label_of(row_of(account), await load_account_rows(db, user.id))` и отдаёт его ключом `acct_label`. Признак двойника считается по всем аккаунтам пользователя, поэтому шапка помечает аккаунт так же, как карточка «Аккаунтов» (D-14).
- **Шаблон:** `{% set account_label = … ' #' ~ account.id %}` удалён; ввезён `components/account_label.html`; блок `title` — `acct_label.plain`; блок `page_title` и `<h2 class="acct-head__name">` — `account_label(acct_label, show_channel=true)`. Нового `<h1>` нет (контракт «страница → шелл»).
- **Проза комментария шапки** (`list.html`) переписана по факту Фазы 16: номер стоит в заголовках и берётся из `phone` через помощника; запрет вывода `credentials` сохранён с прежней причиной (T-17-11). Прежняя фраза-отрицание в летопись не перенесена.
- **Экранирование (T-17-09):** `|safe` и `Markup(` в шаблоне — 0; значение `"><script>alert(1)</script>` проходит автоэкранированием во всех трёх приёмниках.

## Task Commits

1. **Задача 1 (tracer): номер в `<h1>`, `<h2>`, `<title>`**
   - RED `96ac45b8` — `test(17-03): add failing tests for the account number in the groups header and title`
   - GREEN `b610f785` — `feat(17-03): show the account number in the groups header and title`
2. **Задача 2: двойник, враждебное значение, проза**
   - RED `0bffc2f1` — `test(17-03): add failing test for header prose and pins for twin and hostile value`
   - GREEN `834ad02f` — `feat(17-03): correct the groups header prose about the phone column`

REFACTOR-коммитов нет. **Plan metadata:** коммит `docs(17-03)` этой сводки.

## TDD Gate Compliance

RED (`test(17-03):`) предшествует GREEN (`feat(17-03):`) у обеих задач; каждый `feat` — потомок своего `test`. Нарушений нет. Тема-гейты: 2 × `test(17-03):`, 2 × `feat(17-03):`, `refactor(17-03):` — 0.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (вне git, `.pytest_cache/gsd-red/`): `17-03-t1.{xml,log,json}`, `17-03-t2.*`. Каждая запись прошла `gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_account_label_groups.py::test_the_groups_header_shows_the_number_at_both_addresses` | `3 failed` | `KeyError: '1'` (`label_texts(html)["1"]`) | Цель выполнилась и упала на утверждении плана: в неизменённом шаблоне адреса `data-account-label` на странице нет — шапка печатает «Telegram #1». Это не ошибка сбора: модуль импортируется, остальные два красных падают на той же причине (`<title>` — `'Telegram #1 — группы аккаунта — Broadcaster'`, и тот же `KeyError: '1'`) |
| 2 | `FAILED tests/test_pages/test_account_label_groups.py::test_the_header_prose_no_longer_denies_the_phone_column` | `1 failed, 5 passed` | `AssertionError: проза шапки всё ещё отрицает колонку телефона у аккаунта` | Цель выполнилась, прочла `list.html` и нашла склеенную фразу-отрицание в комментарии `:36-40` — упала на планируемом утверждении |

**Замеренное расхождение с описанием плана (задача 2):** `test_a_twin_header_and_title_carry_the_id` и `test_a_hostile_stored_value_is_escaped_in_every_header_sink` в момент RED задачи 2 УЖЕ зелёные (5 passed): всё нужное им даёт разметка задачи 1 (двойник — через `label_of`, экранирование — автоэкранирование Jinja). Это закрепляющие тесты, а не RED-цели; целью RED задачи 2 по плану является только тест прозы. Ни одно утверждение не ослаблено.

## Verification (замеры; база — заметки оркестратора на 037eeaee)

| Проверка | База | Итог (834ad02f) |
|---|---|---|
| `tests/test_pages/test_account_label_groups.py` | — | **6 passed** |
| `tests/test_pages/test_account_groups.py` + `tests/test_pages/test_shell.py` (после задачи 1) | зелёные | **402 passed** |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| `prohibitions_census.py --check` | 953 строки, согласие | rc 0, 953 строки, согласие |
| `compileall -q app main.py tests` | rc 0 | rc 0 |
| Соседние модули, рисующие экран групп аккаунта (`test_responsive_markup` — 142 на базе, `test_hx_location_destinations`, `test_confirm_delete_transport`, `test_htmx_validation_sink`, `test_identifier_bounds`, `test_impersonation`, `test_htmx_preserved`, `test_routes/test_wa_sync_status`, `test_routes/test_sync_groups`) | зелёные | **356 passed** вместе |
| `tests/test_planning` | 218 passed, 2 skipped | см. сообщение возврата (прогон после коммита сводки) |

Приёмочные greps: `' #' ~ account.id` в `list.html` = 0 (было 1); `set account_label` = 0 (было 1); `account_label(acct_label, show_channel=true)` = 2; `"acct_label"` в `account_groups.py` = 1 (было 0); `Телефона в строке нет и быть не может` = 0 (было 1); `\|\s*safe|Markup\(` = 0. Объявленные числа гейтов не сдвинуты.

## Decisions Made

- Порция `groups/partial` и опрос `groups/sync-status` не тронуты — шапку они не рисуют (по плану).
- `{% set MESSENGER_LABELS %}` оставлен в `list.html`: он остаётся условием иконки канала (`account.type in MESSENGER_LABELS`), подписи больше не касается.

## Deviations from Plan

None — план выполнен как написан (замеренное уточнение про уже зелёные закрепляющие тесты — выше, в «Улики RED»; оно не меняет файлы и состав работы).

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5810 тестов, ~42 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модуль плана, оба набора сквозных гейтов, гейты номера, census, compileall и девять соседних модулей страниц/маршрутов (выше). Каждый прогон pytest шёл под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния. Ориентация шла `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- **Датчики каталога git:** файлы `gsd-plan-head-before-17-03` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами (составная команда с `git rev-parse` в подстановке отвергается песочницей).
- **Сборка записи RED:** `.pytest_cache/checks/make_red_record.py` превращает JUnit XML pytest в запись `{command, exitCode, targetTest, output}` для `gsd_run check tdd-red-evidence`; лежит в игнорируемом `.pytest_cache/`. Вместо `.gsd/tdd-evidence/` улики лежат в `.pytest_cache/gsd-red/` по указанию оркестратора.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались.

## Issues Encountered

None. Прогоны под замком уходили в фон (замок общий с тремя соседями); результаты читались из журналов.

## Known Stubs

Нет. На 320–375px правил CSS у подписи в этих двух заголовках пока нет — их приносит план 17-09 (`D7` в `coverage`, `human_judgment: true`).

## Threat Flags

Нет новой поверхности. T-17-09 (хранимый XSS) — закрыт автоэкранированием, закреплён `test_a_hostile_stored_value_is_escaped_in_every_header_sink`; T-17-10 (номер в `<title>`) — принято планом (D-12); T-17-11 (строка сессии под видом «телефона») — шаблон читает номер только через `acct_label`, `credentials` не читает, прозa-запрет сохранена; T-17-SC — установок пакетов нет.

## Next Phase Readiness

- Экран групп аккаунта готов к Фазе 18 (ручная правка номера): подпись в шапке уже берётся из `phone`, правка колонки отразится сама.
- Для 17-09: два адреса `data-account-label` на этом экране (`<h1>` шелла и `<h2 class="acct-head__name">`) — оба должны получить правила усечения без потери `#id` двойника.

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Созданный файл на месте: `tests/test_pages/test_account_label_groups.py`; изменённые — `app/pages/account_groups.py`, `app/templates/account_groups/list.html`.
- Коммиты `96ac45b8`, `b610f785`, `0bffc2f1`, `834ad02f` — предки HEAD; `git rev-list --count 7baa1f8d..HEAD` = 4 = `commits` во frontmatter.
- Тема-гейты: 2 × `test(17-03):`, 2 × `feat(17-03):`, `refactor(17-03):` — 0.
