---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 07
subsystem: ui
tags: [account-label, phone, admin, history, jinja-macro, tdd, tracer, htmx-fragments]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: labels_for, build_labels, load_account_rows, AccountLabel.plain_with_id, макросы account_label / account_id_mark, tests/account_label_support.py"
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-04: history_account_label, ключ account_label записи, параметр audience макроса history_card"
provides:
  - "app/pages/admin.py: ключ account_label в словарях записей админской истории (страница и порция); acct_labels в контексте страницы; карта порции — один load_account_rows по просматриваемому пользователю"
  - "admin/user_history.html: history_card(..., audience='admin'); подписи <option> фильтра — plain_with_id («Telegram +7 999 123-45-67 #5»)"
  - "admin/history_partial_cards.html: history_card(..., audience='admin')"
  - "tests/test_pages/test_account_label_admin_history.py: шесть адресных тестов (страница, порция, фильтр, T-17-21, D-15)"
affects: [17-08, 17-09]

actuals:
  tokens: 3600
  tasks: 2
  commits: 4
plan_head_before: 8712cc044a036e1a5d9d0c3f3e9425bec7233b49
plan_head_after: f7cbfb4ec7b0855754fece8212f52b170cbf5d0c

tech-stack:
  added: []
  patterns:
    - "Админская история подписывает запись той же history_account_label, что пользовательская; карта — по ПРОСМАТРИВАЕМОМУ пользователю, а не по администратору"
    - "Страница админской истории строит подписи по all_accounts, которые и так читала (чтение перенесено выше сборки logs, нового запроса нет); порция — один load_account_rows(db, user_id)"
    - "Плоская подпись <option> администратора — plain_with_id: #id всегда (D-17), без зависимости от двойников"

key-files:
  created:
    - tests/test_pages/test_account_label_admin_history.py
  modified:
    - app/pages/admin.py
    - app/templates/admin/user_history.html
    - app/templates/admin/history_partial_cards.html

key-decisions:
  - "Тесты строят просматриваемого пользователя отдельно от администратора (и тот и другой с аккаунтами): иначе карта «по администратору» и карта «по просматриваемому» были бы неразличимы"
  - "history_card.html не правился: ветка audience == 'admin' из 17-04 принята как есть; изменения шаблона истории не потребовалось"

patterns-established:
  - "Админская карточка записи: номер по data-account-label и отдельный #id по data-account-id — всегда, у недвойников тоже"

requirements-completed: [PHONE-06]

coverage:
  - id: D1
    description: "Карточка записи на /admin/users/{id}/history показывает номер по data-account-label и отдельный #id по data-account-id; без номера — приглушённое «Номер неизвестен» с #id, без двойного #"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_the_admin_history_card_shows_the_number_and_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_an_unknown_number_in_the_admin_history_is_muted"
        status: pass
    human_judgment: false
  - id: D2
    description: "Подписи <option> фильтра админской истории — «Telegram +7 999 123-45-67 #id», #id всегда; сырой tg_user ушёл"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_the_admin_history_filter_option_always_carries_the_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "Порция /admin/users/{id}/history/partial подписана так же; карта — один запрос по просматриваемому пользователю, аккаунтов администратора в порции нет"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_the_admin_history_batch_shows_the_number_and_the_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_the_admin_batch_reads_only_the_viewed_users_accounts"
        status: pass
    human_judgment: false
  - id: D4
    description: "Запись без группы в админской истории (страница и порция) — без data-account-label и без data-account-id (D-15)"
    requirement: "PHONE-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_admin_history.py#test_a_record_without_a_group_carries_no_admin_label"
        status: pass
    human_judgment: false
  - id: D5
    description: "Раскладка админской карточки с номером и #id на 320–375px"
    requirement: "PHONE-06"
    verification: []
    human_judgment: true
    rationale: "Правила CSS подписи приходят планом 17-09; вид и усечение на узком экране смотрит владелец при обходе — этот план стилей не правит"

duration: 22min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 07: Номер и отдельный #id в истории пользователя в админке

**Страница, порция прокрутки и фильтр админской истории пользователя (`/admin/users/{id}/history*`) показывают номер по `data-account-label` и отдельный `#id` по `data-account-id` — всегда; подписи строит та же `history_account_label`, что у пользовательской истории, карта порции — один `load_account_rows` по просматриваемому пользователю, а `<option>` фильтра — `plain_with_id`.**

## Performance

- **Duration:** 22 мин по часам хоста (19:06–19:28 UTC; чтение контекста и плана — до замера; большая часть — ожидание общего замка pytest: два исполнителя на хосте)
- **Started:** 2026-11-20T19:06:17Z
- **Completed:** 2026-11-20T19:28Z
- **Tasks:** 2 (обе `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 4 (1 новый, 3 изменённых)

## Accomplishments

- **Сквозной срез (трассер):** колонка `phone` просматриваемого пользователя → `labels_for(all_accounts)` → `history_account_label(group, acct_labels)` → ключ `account_label` словаря записи → `history_card(..., audience='admin')` → `<span data-account-label>` и отдельный `<span data-account-id>` на `/admin/users/{id}/history`.
- **Страница без нового запроса:** `all_accounts` просматриваемого пользователя администраторская страница читала и раньше — чтение поднято выше сборки `logs`, подписи записей и `<option>` фильтра берутся из одной карты `acct_labels`.
- **Порция:** `build_labels(await load_account_rows(db, user_id))` — одна инструкция на порцию по пользователю из адреса (за `require_admin`); тест `test_the_admin_batch_reads_only_the_viewed_users_accounts` держит T-17-21: у администратора свой аккаунт с номером, в порции чужого пользователя ни его адреса, ни его номера нет.
- **Фильтр:** `acct_labels[acc.id].plain_with_id` вместо `acc.type ~ ' #' ~ acc.id` — «Telegram +7 999 123-45-67 #5», `#id` у недвойника тоже.
- **Запись без группы** (аккаунта уже нет) — без подписи и без `#id` на странице и в порции (D-15).

## Task Commits

1. **Задача 1 (tracer): страница и фильтр админской истории**
   - RED `5a0a206d` — `test(17-07): add failing tests for the account number on the admin user history`
   - GREEN `a96397be` — `feat(17-07): show the account number and id on the admin user history page`
2. **Задача 2: порция прокрутки**
   - RED `316ea667` — `test(17-07): add failing tests for the admin history batch label`
   - GREEN `f7cbfb4e` — `feat(17-07): label the admin history batch from the viewed user's account map`

REFACTOR-коммитов нет. **Plan metadata:** коммит `docs(17-07)` этой сводки.

## TDD Gate Compliance

RED (`test(17-07):`) предшествует GREEN (`feat(17-07):`) у обеих задач; каждый `feat` — потомок своего `test`. Нарушений нет.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (`.pytest_cache/gsd-red/`, вне git): `17-07-t1.{xml,log,json}`, `17-07-t2.{xml,log,json}`. Каждая запись прошла `check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_account_label_admin_history.py::test_the_admin_history_card_shows_the_number_and_the_id` | `3 failed` | `KeyError: '1'` (`label_texts(html)[str(id)]`) | Цель выполнилась и упала на планируемом утверждении: в карточке админской истории адреса `data-account-label` нет. Не сбор и не фикстура: посев и `GET` вернули 200. Второй красный падает на `assert 'tg_user #1' == 'Telegram +7 999 123-45-67 #1'` (сырой тип в `<option>`), третий — `KeyError: '1'` по той же причине |
| 2 | `FAILED tests/test_pages/test_account_label_admin_history.py::test_the_admin_history_batch_shows_the_number_and_the_id` | `2 failed, 4 passed` | `KeyError: '1'` | Порция до правки без подписи: адреса в ответе `/history/partial` нет. Второй красный (`…reads_only_the_viewed_users_accounts`) — `KeyError: '2'` на подписи аккаунта просматриваемого пользователя. **`test_a_record_without_a_group_carries_no_admin_label` зелёный при RED по построению:** это охранник D-15 («подписи нет, где её быть не должно»); он краснеет, если подпись когда-либо припишут записи без группы |

## Verification (замеры; база — дерево 8712cc04 по заметкам оркестратора)

| Проверка | База | Итог (f7cbfb4e) |
|---|---|---|
| `tests/test_pages/test_account_label_admin_history.py` | — | **6 passed** (3 + 3) |
| Админские модули истории: `test_admin_panel` 130, `test_admin_users` 38, `tests/test_admin.py` 18, `test_impersonation` 44 | 230 | **230 passed** (прогон на дереве задачи 1; повторно в общем прогоне ниже) |
| Общий прогон: четыре админских модуля + `test_account_label_admin_history` 6 + `test_account_label_history` 10 + `test_account_label_admin` 7 + `test_history_retry` 63 + `test_identifier_bounds` 21 + `test_history` 49 | 230 + 10 + 7 + 63 + 21 + 49 = 380 | **386 passed** (380 + 6 новых; сумма собранных совпала) |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) + `test_impersonation_gate` | 576 + 15 | **591 passed** (576 + 15; `MUTATING_ROUTE_COUNT` не сдвинут — маршрутов план не добавляет) |
| `prohibitions_census.py --check` | 953 строки, exit 0 | 953 строки, согласие, exit 0 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `tests/test_planning` (до коммита сводки) | 218 passed, 2 skipped | **218 passed, 2 skipped** (повторный прогон после коммита сводки — в сообщении возврата) |

Приёмочные greps: `acc.type ~ ' #' ~ acc.id` в `admin/user_history.html` = 0; `plain_with_id` в нём = 1; `audience='admin'` в `user_history.html` = 1, в `history_partial_cards.html` = 1; `history_account_label(group` в `admin.py` = 2; `"account_label": history_account_label` = 2; `load_account_rows(db, user_id)` = 1.

Пользовательская карточка не затронута: `tests/test_pages/test_account_label_history.py` — 10 passed, `test_history.py` — 49 passed; `history.py` и `history/includes/history_card.html` не правились.

## Deviations from Plan

### Plan-vs-measured (измерение побеждает)

- **Приёмочный grep `history_account_label(group` в `admin.py`:** после задачи 1 — 1 (план: ≥ 1), на финальном дереве — 2 (страница и порция); число по плану для задачи 2 (`"account_label": history_account_label` = 2) совпало. Расхождения нет — запись нужна лишь потому, что итог задачи 1 и итог дерева различаются.
- **Админ-тест «без группы»** зелёный при RED (охранник D-15) — разобран в таблице RED.

Отклонений от плана в продуктовом коде нет: правка вне перечня файлов не потребовалась; красных существующих правил вне перечня нет.

**Total deviations:** 0 auto-fixed; 2 plan-vs-measured (оба описаны выше)
**Impact on plan:** продуктовый код и поведение — ровно по плану.

## Issues Encountered

- Каждый прогон pytest ждал общего замка; три прогона уходили в фон (`test_admin_panel` и сквозные гейты — 2–5 мин), результат читался из журнала. Дефектов не вскрыто.
- Измерение количества тестов: 386 в общем прогоне = сумма модулей, пропусков нет.

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5852 теста, ~41 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модуль плана, четыре админских модуля истории, пользовательская история (`test_account_label_history`, `test_history`, `test_history_retry`, `test_identifier_bounds`), `test_account_label_admin`, оба набора сквозных гейтов, `test_impersonation_gate`, гейты номера, перепись запретов, `compileall`, `tests/test_planning`. Каждый прогон pytest и перепись шли под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (в рабочем дереве нет графа, `graphify-out/` игнорируется git): перестроит оркестратор после слияния.
- **Рабочий файл улик:** `.pytest_cache/checks/make_red_record.py` собирает запись RED (JSON из JUnit XML) для `check tdd-red-evidence`; лежит в игнорируемом `.pytest_cache/`.
- **Датчик каталога git:** файлы `gsd-plan-head-before-17-07` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами (песочница отказала составным командам с `git rev-parse` внутри).
- **Утверждение ветки/базы** (`worktree_branch_check`) разбито на три простых команды по той же причине (`git symbolic-ref`, `git rev-parse HEAD`, `git rev-parse --show-toplevel`): HEAD на `worktree-agent-ab7e9c161e6761978`, база `8712cc04`.
- **Дописывание тестов задачи 2** — `cat >> … <<'EOF'` в тестовый файл (песочница пропустила); продуктовые правки — `Edit`.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались; `/source/broadcaster` не изменялся, читался только граф/gsd-core.

## Known Stubs

Нет. На экране 320–375px правил CSS у подписи пока нет — их приносит план 17-09 (`D5` в `coverage`, `human_judgment: true`).

## Threat Flags

Нет новой поверхности. T-17-21: карта порции — `load_account_rows(db, user_id)` по пользователю из адреса, `test_the_admin_batch_reads_only_the_viewed_users_accounts`. T-17-22: обработчики остаются за `Depends(require_admin)`, маршрутов не добавлено (`test_impersonation_gate.py` зелёный, `MUTATING_ROUTE_COUNT` не сдвинут). T-17-23: подпись печатается автоэкранированием, `|safe` не добавлен (сквозные гейты `tests/test_templates` зелёные). Вызовов журнала в новом коде нет, гейты номера зелены (1161).

## Next Phase Readiness

- Готово для 17-08 (гейт `#id`-сборки) и 17-09 (сквозной обход и CSS): админская история теперь рисует `#id` только через `account_id_mark` и `plain_with_id`; шаблонный гейт 17-08 не найдёт в `admin/user_history.html` ручной склейки `'#' ~ acc.id`.

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Созданный файл на месте: `tests/test_pages/test_account_label_admin_history.py`.
- Коммиты `5a0a206d`, `a96397be`, `316ea667`, `f7cbfb4e` — предки HEAD; `git rev-list --count 8712cc04..HEAD` = 4 = `commits` во frontmatter.
- Тема-гейты: 2 × `test(17-07):`, 2 × `feat(17-07):`, `refactor(17-07):` — 0.
