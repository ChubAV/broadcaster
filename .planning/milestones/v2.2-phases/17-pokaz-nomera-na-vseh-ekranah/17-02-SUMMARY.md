---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 02
subsystem: ui
tags: [account-label, phone, accounts-screen, htmx-fragments, sync-status, tdd, tracer]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: build_labels / label_of / AccountRow, load_account_rows, components/account_label.html (data-account-label), tests/account_label_support.py"
provides:
  - "Страница /accounts: номер (или «Номер неизвестен») по адресу data-account-label в трёх ветках карточки; ключ контекста acct_labels"
  - "Порция /accounts/partial: тот же ключ acct_labels и та же карта, признак двойника через границу страницы из 30"
  - "Фрагмент опроса /accounts/{id}/sync-status: подпись объектом acct_label в статусах active, syncing, sync_failed"
  - "SyncStatusView.phone: str | None = None, заполняется во всех четырёх конструкторах get_sync_status_view"
  - "Тело модалки удаления аккаунта acc-del-<id>-text = acct_label.plain (у двойника с #id) на странице и в порции"
  - "tests/test_pages/test_account_label_accounts.py: адресные тесты страницы, порции, опроса, модалки и SyncStatusView.phone"
affects: [17-03, 17-04, 17-05, 17-06, 17-07, 17-08, 17-09]

actuals:
  tokens: 8500
  tasks: 3
  commits: 6
plan_head_before: 7baa1f8d725cd0d5019277866a1018544bf3eda5
plan_head_after: 6a36b4d56ab8f32ad389ec7c60de0ba27ad2bfeb

tech-stack:
  added: []
  patterns:
    - "Один ключ контекста acct_labels на два файла карточки (list.html, partial_cards.html); карта строится по ВСЕМ аккаунтам пользователя"
    - "Фрагмент без объекта аккаунта получает подпись ОБЪЕКТОМ (acct_label): забытый ключ падает UndefinedError, а не печатает пустоту"
    - "Номер для фрагмента опроса приносит DTO (SyncStatusView.phone) у уже загруженного объекта; признак двойника — строки пользователя одним SELECT"

key-files:
  created:
    - tests/test_pages/test_account_label_accounts.py
  modified:
    - app/pages/accounts.py
    - app/application/accounts/dto.py
    - app/application/accounts/use_cases.py
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/accounts/partials/sync_status_card.html
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Карта acct_labels строится в accounts_list и accounts_partial ОДНИМ вызовом build_labels(await load_account_rows(db, user.id)): по пользователю, не по странице и не по порции (D-14)"
  - "Обработчик опроса считает подпись только после view is not None и только для статусов active / sync_failed / syncing; ветки «Не авторизован», «Аккаунт не найден», «other» подписи не рисуют (T-17-05)"
  - "Потеря ключа не маскируется запасным значением: acct_labels[account.id] у отсутствующей строки даёт Undefined и громкое падение макроса (Pitfall 1)"

patterns-established:
  - "Тест порции проверяет не только «подпись есть», но и «ровно одна подпись» (list(labels) == [id]) — вакуумный пустой словарь не пройдёт"
  - "Граница страницы проверяется настоящим посевом 31 аккаунта (первый и последний wa без номера), а не маленькой выборкой с limit"

requirements-completed: [PHONE-03, PHONE-04, PHONE-05]

coverage:
  - id: D1
    description: "Карточка аккаунта на /accounts в трёх ветках статуса показывает номер «+7 999 123-45-67» по data-account-label; без номера — приглушённое «Номер неизвестен»; у двойников — приглушённый #id; у уникальной подписи #id нет"
    requirement: "PHONE-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_account_card_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_a_card_without_a_number_reads_as_unknown_in_every_status_branch"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_twin_cards_carry_a_muted_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_accounts_card_renders_data"
        status: pass
    human_judgment: false
  - id: D2
    description: "Тело модалки удаления аккаунта называет аккаунт плоской подписью: «Telegram +7 999 123-45-67», у двойника «WhatsApp Номер неизвестен #id» — на странице и в порции подгрузки"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_delete_modal_names_the_account_by_its_plain_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_batch_delete_modal_carries_the_plain_label"
        status: pass
    human_judgment: false
  - id: D3
    description: "Порция /accounts/partial подписана тем же текстом и тем же признаком двойника, что и страница; двойник, разнесённый границей страницы из 30 и порцией, помечен в обоих местах"
    requirement: "PHONE-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_partial_batch_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_a_twin_split_across_the_page_and_the_batch_is_marked_in_both"
        status: pass
    human_judgment: false
  - id: D4
    description: "Фрагмент опроса /accounts/{id}/sync-status подписан номером / «Номер неизвестен» / двойником с #id в статусах active, syncing, sync_failed; номер приносит SyncStatusView.phone; чужой аккаунт подписи не рисует"
    requirement: "PHONE-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_poll_fragment_shows_the_number_at_its_address"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_poll_fragment_reads_as_unknown_in_every_status"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_poll_fragment_marks_a_twin"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_a_foreign_account_poll_draws_no_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_the_sync_status_view_carries_the_phone_in_every_branch"
        status: pass
    human_judgment: false

duration: 60min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 02: Номер на экране «Аккаунты» — страница, порция, опрос синхронизации и модалка удаления

**Карточка аккаунта на `/accounts`, в порции `/accounts/partial` и во фрагменте опроса `/accounts/{id}/sync-status` показывает номер («+7 999 123-45-67») или приглушённое «Номер неизвестен» по адресу `data-account-label`; признак двойника считается по ВСЕМ аккаунтам пользователя и одинаков на странице, в порции и в опросе; номер во фрагмент опроса приносит `SyncStatusView.phone`, а модалка удаления называет аккаунт плоской подписью с `#id` у двойника.**

## Performance

- **Duration:** ≈ 60 мин по часам хоста (время старта не снято: первый коммит 17:14:34Z, последний 17:46:37Z, итоговые прогоны закончились около 18:03Z; заметная часть — ожидание общего замка pytest и сквозные прогоны по 2–10 мин)
- **Completed:** 2026-11-20T18:03Z
- **Tasks:** 3 (все `tdd="true"`; задача 1 — `type="tracer"`)
- **Files modified:** 8 (1 новый, 7 изменённых) — ровно `files_modified` плана

## Accomplishments

- **Сквозной срез (трассер, задача 1):** колонка `phone` → писатель Фазы 16 → `build_labels(load_account_rows)` → макрос `account_label` → `<span data-account-label="<id>">` на карточке `/accounts`. В трёх ветках `list.html` (`syncing`, `sync_failed`, прочие) `mono('#' ~ account.id)` заменён на `account_label(acct_label)` (D-10: имя канала остаётся отдельным `acct-card__chan`); `body=` модалки — `acct_label.plain`. Локальный словарь каналов и `{% set label %}` остались (иконка канала и `title=` предупреждения синхронизации).
- **Порция (задача 2):** `accounts_partial` передаёт тот же ключ `acct_labels` и ту же карту по пользователю, `partial_cards.html` правится посимвольно как `list.html`. Двойник, один из которых лежит на странице из 30, а другой на 31-м месте в порции, помечен `#id` в обоих местах (D-14).
- **Опрос (задача 3):** `SyncStatusView.phone` заполняют все четыре конструктора; `accounts_sync_status` строит `label_of(AccountRow(account_id, view.messenger_type, view.phone), rows)` по строкам пользователя и отдаёт подпись фрагменту ОБЪЕКТОМ `acct_label`; `sync_status_card.html` ввозит только `account_label` (компонент модалки в файл не ввозится).
- **Переписано по D-20:** `test_responsive_markup.py::test_accounts_card_renders_data` — с подстроки `f"#{account.id}" in html` на адрес `label_texts(html)[str(account.id)] == ["Номер неизвестен"]`. Правила трёх файлов карточки (`test_accounts_three_files_*`) и ключи модалок `ModalTrigger("acc-del-", …)` не сдвинуты.

## Task Commits

1. **Задача 1 (tracer): номер в карточке `/accounts` и в теле модалки удаления**
   - RED `c4fc5e00` — `test(17-02): add failing tests for the number on the account card at data-account-label`
   - GREEN `7bee4d50` — `feat(17-02): show the account number on the /accounts card and in the delete modal`
2. **Задача 2: порция `/accounts/partial`**
   - RED `36df0360` — `test(17-02): add failing tests for the number in the /accounts/partial batch`
   - GREEN `b3dcdce8` — `feat(17-02): label the /accounts/partial batch with the same number and twin mark as the page`
3. **Задача 3: фрагмент опроса и `SyncStatusView.phone`**
   - RED `65676c1d` — `test(17-02): add failing tests for the number in the sync-status poll fragment`
   - GREEN `6a36b4d5` — `feat(17-02): label the sync-status poll fragment with the number through SyncStatusView.phone`

REFACTOR-коммитов нет (чистой переделки не было). **Plan metadata:** коммит `docs(17-02)` этой сводки.

## TDD Gate Compliance

RED (`test(17-02):`) предшествует GREEN (`feat(17-02):`) у всех трёх задач: каждый `feat` — потомок своего `test` (`git log --grep` — 3 × `test(17-02)`, 3 × `feat(17-02)`, `refactor(17-02)` — 0). Нарушений нет.

**Трассер:** после GREEN задачи 1 обе `<verify>` (`test_account_label_accounts.py` 6 passed; `test_responsive_markup.py -k accounts` 21 passed) перезапущены до начала задачи 2 — срез проверен сквозно, расширение шло по зелёному основанию.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (в `.pytest_cache/gsd-red/`, вне git): `17-02-t1.{xml,log,json}`, `17-02-t2.*`, `17-02-t3.*`. Каждая запись прошла `check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed` (формат `junit`).

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_account_label_accounts.py::test_the_account_card_shows_the_number_at_its_address` | `7 failed, 8 warnings` | `KeyError: '1'` (`label_texts(html)[str(account_id)]`) | Цель выполнилась и упала на планируемом утверждении: в неизменённом `list.html` адреса `data-account-label` нет. Не ошибка сбора: модуль импортируется. Модальный тест падает на `assert 'Telegram #1' == 'Telegram +7 999 123-45-67'` по той же причине, переписанный `test_accounts_card_renders_data` — на `KeyError: '1'` |
| 2 | `FAILED tests/test_pages/test_account_label_accounts.py::test_the_partial_batch_shows_the_number_at_its_address` | `3 failed, 6 passed` | `KeyError: '2'` (`labels[str(middle)]`) | Падает порция, а не страница: 6 тестов задачи 1 зелёные, значит красное — именно отсутствие адреса в `partial_cards.html`. Двойник через границу страницы падает на `KeyError: '31'` (страничная половина проходит), модалка порции — на `'Telegram #2' == 'Telegram +7 …'` |
| 3 | `FAILED tests/test_pages/test_account_label_accounts.py::test_the_poll_fragment_shows_the_number_at_its_address` | `9 failed, 10 passed` | `KeyError: '1'` (`label_texts(html)[str(account_id)]`) | Фрагмент опроса не несёт адреса. Тесты `SyncStatusView.phone` падают на `AttributeError: 'SyncStatusView' object has no attribute 'phone'`; охранник чужого опроса (`test_a_foreign_account_poll_draws_no_label`) зелёный при RED по построению — это охранник границы, не проверка нового поведения |

## Verification (замеры; база — заметки оркестратора, дерево 037eeaee / 7baa1f8d)

| Проверка | База | Итог (6a36b4d5) |
|---|---|---|
| `tests/test_pages/test_account_label_accounts.py` | — (новый) | **19 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| `prohibitions_census.py --check` | 953 строки, согласие | 953 строки, согласие (фаза 17: 19 строк), exit 0 |
| `compileall -q app main.py tests` | rc 0 | rc 0 |
| Соседние модули, рисующие `/accounts` и опрос (`test_responsive_markup` 142, `test_account_label_accounts` 19, `test_wa_sync_status`, `test_account_groups`, `test_confirmation_panel_settle`, `test_htmx_preserved`, `test_hx_location_destinations`, `test_identifier_bounds`, `test_max_connect_transport`, `test_shell`, `test_editor_schedules` 133) | — | **773 passed**, 0 failed |
| Комбинированный `<verify>` задачи 3 (`test_responsive_markup`, `test_wa_sync_status`, три гейта номера, `tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`) | — | **1877 passed** |
| `tests/test_planning` | 218 passed, 2 skipped | см. конец сводки |

Объявленные числа гейтов не сдвинуты (прогоны зелёные, в выводе ни одного сообщения о счётчике). Приёмочные greps: `mono('#' ~ account.id)` в `list.html` = 0 и в `partial_cards.html` = 0; `' #' ~ account.id` в обоих = 0; `mono('#' ~ account_id)` в `sync_status_card.html` = 0; `load_account_rows(db, user.id)` в `accounts.py` = 3 (страница, порция, опрос; ≥ 1); `"acct_labels"` в `accounts.py` = 2; `acct_labels` в `partial_cards.html` = 2; `acct_label=` в `accounts.py` = 1; `phone: str | None = None` в `dto.py` = 1; `phone=account.phone` в `use_cases.py` = 4; `components/modal.html` в `sync_status_card.html` = 0; `f"#{account.id}" in html` в `test_responsive_markup.py` = 0. Новых POST с `302` план не пишет (ни одного POST в новом модуле).

## Deviations from Plan

### Auto-fixed Issues

Нет: продуктовый код — ровно по плану, ни одного отступления по Rules 1–3 не потребовалось.

### Plan-vs-measured (измерение побеждает)

- **Проверка границы страницы (задача 2, тест 2).** План: «`wa` без номера первым и `wa` без номера последним; `GET /accounts/partial?offset=1&limit=5` несёт `#<id>` у последнего». При 2–3 аккаунтах «последний» лежит на странице из 30, и граница страницы не проверяется вовсе. Сделано строже: посеяно 31 аккаунт (первый `wa`, 29 `max`, последний `wa`), порция читается с `offset=30&limit=5`, а в тест добавлено `assert str(last) not in page` — доказательство, что последний аккаунт действительно за границей страницы. Измеренный ход: страничная половина теста зеленела уже после GREEN задачи 1, порционная — после GREEN задачи 2.
- **Форма причинного литерала RED.** Первый вариант тестов порции сравнивал весь словарь (`label_texts(html) == {...}`) и падал на `assert {} == {...}`, а не на плановом `KeyError: '`. Тесты переписаны на обращение по адресу (`labels[str(middle)]`, `batch[str(last)]`) до RED-коммита: литерал совпал с планом (`KeyError: '2'`, `KeyError: '31'`), сравнение «ровно одна подпись» осталось отдельным утверждением.
- **Расширение набора тестов сверх перечня плана:** `test_the_sync_status_view_carries_the_phone_in_every_branch` (4 статуса, включая `connecting` → ветка «other» DTO) закрепляет, что ВСЕ четыре конструктора `get_sync_status_view` заполняют `phone`; план проверял это только grep-ом `phone=account.phone` = 4. Параметризация по статусу в трёх тестах (`syncing` / `sync_failed` / `active`) — вместо трёх отдельных функций, как велит behavior плана «по аккаунту каждого статуса».

---

**Total deviations:** 0 auto-fixed, 3 plan-vs-measured / расширения теста (без изменения продуктового поведения)
**Impact on plan:** продукт — ровно по плану; изменились лишь формы проверок (строже граница страницы, адресный литерал RED, +1 тест DTO).

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5810 тестов, ~42 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модуль плана, оба набора сквозных гейтов, гейты номера, census, compileall, комбинированный прогон `<verify>` задачи 3 (1877) и 11 соседних модулей страниц (773). Каждый прогон pytest и тяжёлый скрипт шёл под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния.
- **Рабочие файлы:** `.pytest_cache/checks/make_red_record.py` собирает запись RED (camelCase JSON из JUnit XML) для `check tdd-red-evidence`; `.pytest_cache/gsd-red/17-02-t{1,2,3}.{xml,log,json}` — улики. Всё в игнорируемом `.pytest_cache/`.
- **Датчики каталога git:** `gsd-plan-head-before-17-02` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами (составной команде с подстановкой `git rev-parse` песочница отказала).
- **Многострочные правки** `app/pages/accounts.py` и шаблонов сделаны блоками `python3 - <<'EOF'` с `assert old in s` перед каждой заменой (точное совпадение подтверждалось утверждением); одну составную `cat >> … <<EOF` + `pytest` песочница отказала — вместо неё `Edit`.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения и живой Redis не использовались; все тесты — на `sqlite+aiosqlite:///:memory:`.

## Issues Encountered

- Три фоновых прогона pytest шли по 5–10 мин из-за общего замка и четырёх исполнителей на 4 ядрах — ожидание, не дефект.
- **Не дефект, но граничный случай для памяти:** карта `acct_labels` и страница читаются двумя отдельными запросами. Аккаунт, удалённый (или созданный) между ними, даст `acct_labels[account.id]` = `Undefined` и громкое падение макроса (500), а не пустую подпись — так задумано планом (Pitfall 1: громко, а не пусто). Окно — доли миллисекунды и только для той же вкладки пользователя; запасного значения не заводилось, чтобы не вернуть «молчаливую пустоту».
- `/accounts` теперь делает на один `SELECT` больше (три колонки по пользователю), опрос — один `SELECT` на ответ активной/синхронизирующейся/упавшей карточки (T-17-08, принято планом: опрос идёт раз в 5 с и только у `syncing`).

## Known Stubs

Нет: заглушек и пустых значений, текущих в UI, план не вводит. Раскладка подписи на 320–375px (правила CSS `.acct-label` внутри `.acct-card__ident`) — предмет плана 17-09; этот план стилей не правит.

## Threat Flags

Нет новой поверхности. Угрозы плана: T-17-05 (номер чужого аккаунта во фрагменте опроса) — подпись строится только после `view is not None`, строки соседей читает `load_account_rows(db, user.id)`, закреплено `test_a_foreign_account_poll_draws_no_label` (нет ни `data-account-label`, ни номера в ответе); T-17-06 — в `x-on:` / `$dispatch` по-прежнему только числовой `account.id`, подпись — текст элемента и `body=` модалки (`<p>`), формы-триггеры не тронуты, правила `ModalTrigger` зелёные; T-17-07 — `body=` модалки несёт `plain` с `#id` у двойника, закреплено тестами страницы и порции; T-17-08 принят; T-17-SC — установок пакетов нет.

## Next Phase Readiness

- Для 17-03…17-07: обращение к подписи — через объект `AccountLabel` и ключ контекста; шаблон читает поле объекта (громкое падение), а не россыпь переменных; карта — `build_labels(await load_account_rows(db, user.id))`. Этот план проверил, что подход работает и на отдельном `.render(...)` фрагмента (`label_of` по строкам пользователя).
- Для 17-08 (гейт): `accounts/list.html`, `partial_cards.html`, `partials/sync_status_card.html` больше не печатают `#` перед id аккаунта — их строки реестра «ещё не переведено» (если план 17-08 заводит такой реестр) убывают на три файла; в `sync_status_card.html` ключ `acct_label` описан в шапке файла.
- Файл `app/pages/accounts.py` в фазе правил только этот план; Фазы 18–19 сходятся в него после 17 — правки сведены к ввозам и ключам контекста, обработчики не перестраивались.
- Красных вне перечня файлов нет.

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Файл создан и на месте: `tests/test_pages/test_account_label_accounts.py`; изменённые файлы — те же 7, что в `git diff --stat 7baa1f8d..HEAD` (8 файлов = `files_modified`).
- Коммиты `c4fc5e00`, `7bee4d50`, `36df0360`, `b3dcdce8`, `65676c1d`, `6a36b4d5` — предки HEAD; `git rev-list --count 7baa1f8d..HEAD` = 6 = `commits` во frontmatter.
- Тема-гейты: 3 × `test(17-02):`, 3 × `feat(17-02):`, `refactor(17-02):` — 0; каждый `feat` — потомок своего `test`.
