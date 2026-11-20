---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 05
subsystem: ui
tags: [account-label, phone, admin, jinja-macro, tdd, tracer]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: глобал phone_label, макросы account_label / account_id_mark, адреса data-account-label / data-account-id, tests/account_label_support.py"
provides:
  - "Строка воркера админки («Воркеры», страница и паршал): канал, номер и отдельный #id-ссылка на логи"
  - "Строка очереди и заголовок «Аккаунт #id · {канал} {номер}» на /admin/queue"
  - "Карточка пользователя в админке: канал из MESSENGER_LABELS вместо сырого tg_user, номер, отдельный #id"
  - "tests/test_pages/test_account_label_admin.py: семь адресных тестов админских экранов"
  - "_row_markup и четыре правила test_admin_panel.py находят строку по data-account-id (D-20)"
affects: [17-07, 17-08, 17-09]

actuals:
  tokens: 5600
  tasks: 2
  commits: 4
plan_head_before: 7baa1f8d725cd0d5019277866a1018544bf3eda5
plan_head_after: e1c027b8e9ee70ba4a6764c718640c853d2ddd32

tech-stack:
  added: []
  patterns:
    - "Админская форма (D-17): три <span> подряд — канал (label.channel), account_label(phone_label(account), with_twin_id=false), отдельный account_id_mark; #id печатается всегда"
    - "Ссылка на логи оборачивает account_id_mark: текст ссылки по-прежнему ровно #<id>, номер внутрь ссылки не попадает"
    - "Строку воркера и очереди тест режет по адресу знака, а не по тексту «>#id<»"

key-files:
  created:
    - tests/test_pages/test_account_label_admin.py
  modified:
    - app/templates/admin/includes/worker_row.html
    - app/templates/admin/includes/queue_row.html
    - app/templates/admin/queue.html
    - app/templates/admin/user_detail.html
    - tests/test_pages/test_admin_panel.py

key-decisions:
  - "Разделитель « · » стоит только в заголовке очереди (queue.html), в строках и карточке три элемента идут рядом без него — как велит D-17"
  - "Заголовок очереди берёт подпись с show_channel=true: значка канала рядом с h3 нет, поэтому «WhatsApp +7 999 123-45-67» читается целиком"
  - "Текст канала берётся из label.channel (MESSENGER_LABELS, D-11); локальные словари строк остаются только условием значка"

patterns-established:
  - "_row_markup ищет строку по data-account-id=\"<id>\" с кавычками: 1 не совпадает с 10"

requirements-completed: [PHONE-06]

coverage:
  - id: D1
    description: "Строка воркера на /admin/workers и /admin/workers/partial: канал, номер (или приглушённое «Номер неизвестен») и отдельный #id; #id остаётся ссылкой на логи воркера"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_worker_row_shows_the_number_and_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_worker_id_stays_a_link_to_its_logs"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_an_unknown_worker_number_is_muted_and_keeps_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_worker_partial_matches_the_page_label"
        status: pass
    human_judgment: false
  - id: D2
    description: "Строка очереди и заголовок «Аккаунт #id · {канал} {номер}» на /admin/queue"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_queue_row_shows_the_number_and_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_queue_heading_keeps_the_id_and_gains_the_number"
        status: pass
    human_judgment: false
  - id: D3
    description: "Карточка пользователя в админке: «Telegram» вместо tg_user, номер и отдельный #id"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin.py#test_the_user_card_names_the_channel_and_the_number"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пять утверждений test_admin_panel.py переписаны на адрес элемента без ослабления смысла"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py (130 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Раскладка админской строки с тремя элементами на 320–375px"
    requirement: "PHONE-06"
    verification: []
    human_judgment: true
    rationale: "Правила CSS подписи приходят планом 17-09, вид и усечение на узком экране смотрит владелец при обходе; этот план стилей не правит"

duration: 70min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 05: Номер и отдельный #id на экранах админки

**Строки «Воркеров» (страница и паршал), строки и заголовки «Очереди» и карточка пользователя в админке показывают канал, номер (или приглушённое «Номер неизвестен») и отдельный `#id` — всегда; `#id` воркера остался ссылкой на логи, а пять утверждений `test_admin_panel.py` переписаны на адрес `data-account-id`.**

## Performance

- **Duration:** ~70 мин по часам хоста (17:10–18:20 UTC; значительная часть — ожидание общего замка pytest: четыре исполнителя на одной машине)
- **Tasks:** 2 (обе `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 6 (1 новый, 5 изменённых)

## Accomplishments

- **Сквозной срез (трассер):** `phone_label(account)` → `account_label(lbl, with_twin_id=false)` + `account_id_mark(account.id)` в ячейке аккаунта `worker_row.html`: `<span data-grow>` канала, номер по `data-account-label`, `#id` по `data-account-id` внутри `<a href="/admin/logs?source=<id>">`. Только `<span>`/`<a>`: `_row_markup` по-прежнему режет строку по первому `</div>`, страница и паршал дают одну разметку.
- **Очередь:** `queue_row.html` — канал, номер, отдельный `#id`; заголовок `queue.html` — «Аккаунт», `#id`, « · », подпись с каналом (`Аккаунт #5 · WhatsApp +7 999 123-45-67`). Ключи панелей подтверждения (Alpine) подпись не получают.
- **Карточка пользователя:** вместо `tg_user #5` — «Telegram +7 999 123-45-67» и отдельный `#5`.
- **D-20:** `_row_markup` ищет строку по `data-account-id="<id>"`; `:287`, `:387`, `:588` — `id_mark_texts(...)[str(id)] == [f"#{id}"]`; `:554` — `html.index(f'data-account-id="{id}"')`. Смысл правил (строка ровно одна, порядок каналов, равенство страницы и паршала) сохранён.
- Обработчики `app/pages/admin.py` не менялись: ORM-объекты аккаунтов уже загружены, номер читается с объекта.

## Замер D-20 до переписывания (на замене, GREEN трассера, ДО правки test_admin_panel.py)

Полный прогон модуля на дереве с изменённым `worker_row.html` и неизменённым `test_admin_panel.py`: **130 passed, 0 failed** (`.pytest_cache/gsd-red/17-05-d20-measure.log`). Поимённо:

| Правило (строка до правки) | До переписывания |
|---|---|
| `_row_markup` (`:102`) и зависимые: `test_telegram_row_worker_label_changes_with_the_source_state`, `test_telegram_queue_cell_names_the_cause_of_the_missing_depth`, `test_queue_cell_names_the_broken_observer_when_redis_is_down`, `test_workers_partial_answers_the_admin_with_the_same_rows` | PASSED |
| `test_workers_subsection_shows_idle_account_row` (`:287`) | PASSED |
| `test_telegram_row_worker_label_changes_with_the_source_state` (`:387`) | PASSED |
| `test_lower_block_groups_accounts_by_channel` (`:554`) | PASSED |
| `test_workers_partial_answers_the_admin_with_the_same_rows` (`:588`) | PASSED |

Итог: ожидание плана подтвердилось — **ни одно из пяти не покраснело** (знак `#id` остаётся отдельным элементом с текстом `#<id>`, его по-прежнему находит `>#<id><`; предпосылка A3 RESEARCH верна). Переписывание на адрес сделано всё равно, как требовал D-20. После переписывания: `test_admin_panel.py` — **130 passed** (число не изменилось, тестов не добавлено и не убрано); добавленные пять греп-условий приёмки плана: `marker = f">#{account_id}<"` = 0, `f">#{account.id}<"` = 0, `f"#{account.id}" in html` = 0.

## Task Commits

1. **Задача 1 (tracer): строка воркера**
   - RED `13ce3db3` — `test(17-05): add failing tests for the admin worker row number and id`
   - GREEN `cac75410` — `feat(17-05): show the channel, the number and the id link on the worker row`
2. **Задача 2: очередь и карточка пользователя**
   - RED `b45a2059` — `test(17-05): add failing tests for the admin queue row, heading and user card number`
   - GREEN `e1c027b8` — `feat(17-05): show the number beside the id on the admin queue and user card`

REFACTOR-коммитов нет. **Plan metadata:** коммит `docs(17-05)` этой сводки.

## TDD Gate Compliance

У обеих задач `test(17-05):` предшествует `feat(17-05):`, каждый `feat` — потомок своего `test`. Нарушений нет.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы: `.pytest_cache/gsd-red/17-05-t1.{xml,log,json}`, `17-05-t2.*` (вне git). Обе записи прошли `gsd_run check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_account_label_admin.py::test_the_worker_row_shows_the_number_and_the_id` | `4 failed` | `KeyError: '1'` (`label_texts(html)["1"]`) | Цель выполнилась и упала на утверждении плана: в неизменённом шаблоне адреса `data-account-label` нет. Не ошибка сбора и не фикстуры — страница ответила 200. Три теста падают тем же `KeyError`, четвёртый (`…stays_a_link_to_its_logs`) — на `assert 'data-account-id="1"' in links[0]`: ссылка есть, знака внутри нет |
| 2 | `FAILED tests/test_pages/test_account_label_admin.py::test_the_queue_row_shows_the_number_and_the_id` | `3 failed, 4 passed` | `KeyError: '1'` | Страница очереди и карточка ответили 200, строка очереди нашлась ровно одна; падение — отсутствие адреса в разметке. Четыре теста задачи 1 в этом прогоне зелёные (GREEN задачи 1 уже в дереве) |

Plan-vs-measured: литерал `KeyError: '` совпал с планом (`KeyError: '1'`); отличий нет.

## Verification (замеры; база — дерево 037eeaee/7baa1f8d по заметкам оркестратора)

| Проверка | База | Итог (e1c027b8) |
|---|---|---|
| `tests/test_pages/test_account_label_admin.py` | — | **7 passed** |
| `tests/test_pages/test_admin_panel.py` | 130 | **130 passed** |
| Три модуля задачи 2 вместе (`test_account_label_admin`, `test_admin_panel`, `test_admin_users`) | — | 175 passed (7 + 130 + 38) |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| `prohibitions_census.py --check` | exit 0, 953 строки | exit 0, 953 строки |
| `compileall -q app main.py tests` | rc 0 | rc 0 |
| Модули, рисующие воркеры / очередь / карточку пользователя (`test_admin`, `test_queue_rows`, `test_blocked_user`, `test_confirm_delete_transport`, `test_history_retry`, `test_hx_location_destinations`, `test_identifier_bounds`, `test_impersonation`, `test_notices_channel`, `test_shell`, `test_responsive_markup`) | — | **704 passed** |
| `tests/test_planning` | 218 passed, 2 skipped | см. конец сводки |

Приёмочные greps: `mono('#' ~ account.id)` в `worker_row.html` = 0 (было 2), в `queue_row.html` = 0 (было 1); `account_id_mark(account.id)` в `worker_row.html` = 2; `Аккаунт #{{` в `queue.html` = 0; `acc.type }} #{{` в `user_detail.html` = 0; `account_id_mark` в `queue.html` = 2, в `user_detail.html` = 2. Объявленные числа гейтов не сдвинуты (прогоны зелёные).

## Deviations from Plan

None - plan executed exactly as written.

Уточнения без отступления: в задачу 1 вошёл четвёртый тест плана `test_the_worker_partial_matches_the_page_label` и три остальных в точности по списку behavior; к трём тестам задачи 2 добавлена проверка простого текста заголовка (`Аккаунт #<id> · WhatsApp +7 999 123-45-67`) — она фиксирует разделитель « · ». Файлы вне `files_modified` не правились; `app/pages/admin.py` не понадобился.

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5810 тестов, ~42 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модули плана, оба набора сквозных гейтов, гейты номера, census, `compileall`, одиннадцать соседних модулей страниц (выше) и `tests/test_planning`. Каждый прогон под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock` (два раза `flock -w 590` вышел по тайм-ауту ожидания замка, rc 1 с пустым журналом, — прогон тогда не стартовал и был повторён; это не красный результат).
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния.
- **Датчик спавна:** запись `gsd-spawn-toplevel` в каталог git рабочего дерева классификатор песочницы отказал; корень дерева сверялся вручную перед каждым коммитом (`git rev-parse --show-toplevel` = корень рабочего дерева). Журнал начала плана `gsd-plan-head-before-17-05` записан (`7baa1f8d`).
- **Рабочий файл улик:** `.pytest_cache/checks/make_red_record.py` собирает запись RED из JUnit XML; лежит в игнорируемом `.pytest_cache/`. Правки шаблонов и тестов сделаны небольшим скриптом Python и инструментом Edit (без `sed`-конвейеров); добавление тестов в конец файла — через Edit, так как heredoc с `cat >>` песочница отказала.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались (Redis во всех тестах подменён двойниками).

## Issues Encountered

Ожидание общего замка pytest (четыре исполнителя): основная часть времени. Красных проверок вне плана нет.

## Known Stubs

Нет.

## Threat Flags

Нет новой поверхности. T-17-15 (номера пользователей на админских экранах) принято планом: маршруты за `require_admin`, обработчики не менялись, запрет `403` для пользователя стерегут существующие тесты. T-17-16: подпись в ключи панелей очереди и выражения Alpine не попала (в `queue_row.html` ключи не тронуты, подпись — только текст `<span>`). T-17-17: подпись печатается только автоэкранированием макроса компонента, `MARKUP_BUILDERS` в сквозных гейтах — зелёные 576.

## Next Phase Readiness

- Готово: админские экраны «Воркеры», «Очередь» и карточка пользователя. Историю пользователя в админке (`admin/user_history.html`, `admin/history_partial_cards.html`, `app/pages/admin.py`) делает план 17-07.
- Для плана 17-09 (CSS): в админских строках три `<span>` подряд (`.acct-label` внутри `[data-grow]`-соседства), заголовок очереди `h3.card__title` теперь несёт два знака и подпись — проверить усечение на 320–375px (D5, `human_judgment: true`).

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Созданный файл на месте: `tests/test_pages/test_account_label_admin.py`.
- Коммиты `13ce3db3`, `cac75410`, `b45a2059`, `e1c027b8` — предки HEAD; `git rev-list --count 7baa1f8d..HEAD` = 4 = `commits` во frontmatter (до коммита этой сводки).
- Темы-гейты: 2 × `test(17-05):`, 2 × `feat(17-05):`, `refactor(17-05):` — 0.
