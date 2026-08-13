---
phase: 03-gruppy-akkaunta
verified: 2026-08-13T08:05:00Z
status: gaps_found
score: 131/132 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Кнопка подтверждения отражает выполняющийся запрос и не допускает повторной отправки (E6 loading)"
    status: failed
    reason: "Панель подтверждения удаления использует общий компонент `components/modal.html`, у которого кнопка подтверждения — обычный `<button type=\"submit\">` без единого признака выполняющегося запроса и без защиты от повторной отправки. Ни `disabled`, ни `aria-busy`, ни смены подписи, ни перехвата отправки в разметке нет; собственного JS у проекта нет (в `app/static/js/` только вендорные alpine.min.js и htmx.min.js), а UI-SPEC при этом объявляет строку E6/loading как `✅ covered`. Фактическая защита реализована ИНАЧЕ — идемпотентностью маршрута: повторный POST удаления безвреден (`app/pages/account_groups.py:363-377`, тест `test_repeated_delete_is_harmless`). То есть повторная отправка ДОПУСКАЕТСЯ, но не приводит к вреду — это не то, что утверждает must-have."
    artifacts:
      - path: "app/templates/components/modal.html"
        issue: "Строка 82: `<button class=\"btn btn--{{ confirm_variant }}\" type=\"submit\">` — нет ни состояния выполнения, ни блокировки повторной отправки. Файл не входил в files_modified плана 03-05, объявившего эту истину."
      - path: ".planning/phases/03-gruppy-akkaunta/03-UI-SPEC.md"
        issue: "Строка 379 помечает E6/loading как `✅ covered` с формулировкой «The confirm button reflects the in-flight POST and is not double-submittable» — утверждение не подтверждается разметкой."
      - path: ".planning/phases/03-gruppy-akkaunta/03-05-SUMMARY.md"
        issue: "Сводка плана не упоминает E6/loading вовсе — истина объявлена планом и не закрыта ни кодом, ни тестом, ни явным отказом."
    missing:
      - "Либо признак выполняющегося запроса и защита от повторной отправки на кнопке подтверждения `components/modal.html` (например, `x-on:submit` на форме модалки, снимающий кнопку — тем же приёмом, что уже применён к тумблеру и к форме удаления в `account_groups/includes/group_row.html`), плюс тест уровня разметки"
      - "Либо явный override с обоснованием «защита перенесена на уровень маршрута (идемпотентное удаление), UI-гарда сознательно нет» и синхронная правка строки E6/loading в 03-UI-SPEC.md, чтобы спецификация не утверждала непроверяемое"
---

# Phase 3: Группы аккаунта — Verification Report

**Phase Goal:** Пользователь управляет составом групп на уровне конкретного messenger-аккаунта, а не только выбирает их при настройке рассылки.
**Verified:** 2026-08-13T08:05:00Z
**Status:** gaps_found (1 gap, WARNING-уровня — цель фазы достигнута, промах в краевой UI-истине)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Roadmap Success Criteria (контракт фазы)

| # | Критерий | Статус | Доказательство в коде |
|---|----------|--------|------------------------|
| 1 | Пользователь может открыть экран групп конкретного messenger-аккаунта и видит на нём только группы этого аккаунта | ✓ VERIFIED | `app/pages/account_groups.py:109-194` — маршрут `GET /accounts/{account_id}/groups`; `_load_owned_account:65-75` на входе `:121`; выборка `_build_groups_query:51` скоуплена `Group.user_id == user_id AND Group.account_id == account_id`. Роутер зарегистрирован: `app/pages/__init__.py:45`. Вход с `/accounts` — 9 вхождений «Настроить группы» в трёх копиях разметки строки аккаунта. Тесты прошли: `test_page_shows_groups_of_this_account`, `test_page_hides_groups_of_another_account_of_the_same_user`, `test_page_of_a_foreign_account_leaks_nothing` |
| 2 | Пользователь может включить или отключить отдельную группу, и это сразу отражается на том, какие группы доступны при настройке расписаний объявления | ✓ VERIFIED | Тумблер: `account_groups.py:299-332`, тройной WHERE `:314-320`, ИНВЕРСИЯ `:326`. Отражение в диспетчеризации: `app/application/scheduling/use_cases.py:171-177` — `if not group.is_active: logger.info(...); continue`. Отражение в редакторе: `app/pages/ads.py:243-259` — `group_scope = is_active OR id IN chosen`, `inactive_group_ids` → пометка «отключена» в `ads/includes/sched_card.html:186`. Тесты прошли: `test_toggle_inverts_is_active_and_redirects`, `test_double_toggle_returns_the_group_to_its_initial_state`, `test_only_the_active_group_of_a_schedule_gets_a_task`, `test_enabling_the_group_resumes_dispatch`, `test_disabled_group_chosen_in_the_schedule_stays_visible`, `test_disabled_group_not_chosen_is_absent_from_the_picker` |
| 3 | Пользователь может удалить группу из списка аккаунта | ✓ VERIFIED | `account_groups.py:335-377` — тот же тройной WHERE, `ScheduleRepository(db).remove_group_ids(user.id, {group.id})` перед `db.delete(group)`. Панель подтверждения — `group_row.html:104-109`. Тесты прошли: `test_delete_removes_the_group_and_redirects`, `test_delete_cleans_the_group_out_of_schedules`, `test_delete_keeps_the_neighbour_ids_in_the_same_schedule`, `test_repeated_delete_is_harmless`, `test_remaining_rows_keep_the_id_order_after_delete` |
| 4 | Пользователь может повторно синхронизировать группы аккаунта и увидеть результат синхронизации не покидая экран | ✓ VERIFIED | Кнопка «Синхронизировать всё» → `POST /accounts/{id}/sync-groups` (`list.html:84-90`); обработчик `app/pages/accounts.py:741,771,834,858,893` возвращает 302 на `/accounts/{id}/groups` во ВСЕХ ветках. Результат хранится на аккаунте (`last_synced_at`, `last_sync_result`) и читается при каждом заходе через `parse_sync_result` (`account_groups.py:186`). Плашка сводки — `list.html:113-143` (найдено / новых / обновлено имён / не найдено при >0, ошибка отдельной веткой). Фоновые WA/MAX добираются самоостанавливающимся опросом `sync-status` (`account_groups.py:251-296` + `partials/sync_result.html:50`). Тесты прошли: `test_success_plashka_prints_all_three_counters`, `test_error_plashka_names_the_error_and_the_next_step`, `test_stored_result_survives_a_revisit`, `test_account_groups_polling_stops`, `test_account_groups_polling_continues_while_syncing`. UAT №5 (живая синхронизация всех трёх путей) — pass |
| 5 | Экран групп аккаунта пригоден к использованию на мобильных ширинах | ✓ VERIFIED | `app/static/css/app.css:1593-1735` — выделенная секция экрана: `[data-acct-head]` (flex-wrap, действия переносятся на свою строку), `.count-rule` (flex-wrap + схлопывающаяся линия), `[data-group-row]` (карточка, flex-wrap, `min-width:0`), `@media (max-width: 400px)` с перекомпоновкой строки; фильтры сворачиваются на 860px существующим макросом. Автопроверки прошли: `test_account_groups_list_is_card_based`, `test_account_groups_filters_block_collapsible`, `test_account_groups_row_names_each_value`, параметризованный `CLEAN_SECTIONS` включает `account_groups`. UAT №2 (320/860/1280) и №3 (шапка+плашка на трёх ширинах) — pass |

**Roadmap SC: 5/5 VERIFIED.**

### Plan Must-Have Truths (по планам)

| План | Труths | Verified | Failed | Заметки |
|------|--------|----------|--------|---------|
| 03-01 | 17 (1 backstop) | 17 | 0 | Backstop «окно между сбором и постановкой задач» подтверждён явным кодом: `collect_due_schedules` проверяет `is_active` на сборе, `dispatch_send_tasks` (`app/worker/tasks.py:50-130`) повторной проверки не делает — гарантия действительно ограничена моментом сбора, как и объявлено |
| 03-02 | 11 | 11 | 0 | `apply_group_resync` не содержит слова `is_active` ни разу (grep -c = 0) — прохибиция D-11 в проверяемой форме. Ревизия `0014` — три `add_column` nullable, `down_revision = "0013"`, симметричный `downgrade` |
| 03-03 | 13 | 13 | 0 | Все 13 закрыты тестами `test_editor_schedules.py` (6 профильных прогнаны отдельно — passed) |
| 03-04 | 9 | 9 | 0 | Три пути синка сведены к одному хелперу: `app/pages/accounts.py:863` и `app/worker/tasks.py:331` вызывают `apply_group_resync`; WA и MAX объединены в один `_sync_groups_async` (коммит `31ed3dd`) |
| 03-05 | 42 (3 backstop) | 41 | **1** | Провал: E6 loading — см. Gaps. Три backstop-истины (320px) закрыты человеческим UAT №2/№3 |
| 03-06 | 23 (2 backstop) | 23 | 0 | Опрос объявлен ТОЛЬКО в ветке `syncing` (`sync_result.html:50`), закреплён парой тестов «продолжает» / «останавливается» — обе прошли |
| 03-07 | 8 | 8 | 0 | GRP-08 снято согласованно в ROADMAP.md (стр. 26, 214, 291) и REQUIREMENTS.md (стр. 156, 220, 247, 252); `app/routes/groups.py` удалён, `app/main.py` его не упоминает; посев групп — `tests/conftest.py:110 seed_group` |
| 03-08 | 9 | 9 | 0 | `app/templates/groups/` отсутствует целиком; `app/pages/groups.py` — 44-строчная заглушка с `RedirectResponse` на `/accounts` для `/groups` и `/groups/{deep_link:path}`; пункта меню нет (`test_nav_has_no_groups_item`); старых классов в CSS нет |

**Итого по планам: 131/132 truths verified, 1 FAILED.**

### Prohibitions (must-NOT)

Четыре прохибиции, объявленные планами; все judgment-tier по умолчанию, но у каждой найдено **wired enforcement evidence** — проходящий негативный тест, а не только декларация. Поэтому ни одна не помечается `unverified-prohibition`.

| # | Прохибиция | План | Enforcement evidence | Статус |
|---|-----------|------|----------------------|--------|
| 1 | Выключение группы не удаляет её id из `Schedule.group_ids` | 03-01 | `test_toggle_does_not_edit_the_schedules`, `test_schedule_group_ids_are_not_edited_by_the_skip` — passed. Маршрут тумблера состав расписаний не читает и не пишет (`account_groups.py:329-332`) | ✓ ENFORCED |
| 2 | Пропуск выключенной группы не создаёт записи в SendLog | 03-01 | `test_skipping_writes_nothing_to_the_send_log`, `test_missing_group_writes_nothing_to_the_send_log` — passed. `use_cases.py:171-177` — только `logger.info` + `continue` | ✓ ENFORCED |
| 3 | Синхронизация не удаляет данные пользователя (пропавшая группа помечается) | 03-02 | `test_missing_group_is_marked_not_deleted`, `test_empty_response_marks_nothing_and_deletes_none` — passed. В `group_resync.py` нет ни одного `session.delete` | ✓ ENFORCED |
| 4 | То же для всех трёх путей синхронизации | 03-04 | Та же реализация вызывается всеми тремя путями (`accounts.py:863`, `tasks.py:331`) — прохибиция удерживается по построению | ✓ ENFORCED |

### Required Artifacts

| Artifact | Expected | Exists | Substantive | Wired | Data flows | Status |
|----------|----------|--------|-------------|-------|------------|--------|
| `app/pages/account_groups.py` | Роутер экрана (мин. 150 стр.) | ✓ 377 стр. | ✓ 5 маршрутов | ✓ `pages/__init__.py:45` | ✓ 4 живых запроса к БД + 2 запроса подсчёта | ✓ VERIFIED |
| `app/templates/account_groups/list.html` | Страница (мин. 25) | ✓ 234 стр. | ✓ | ✓ `TemplateResponse:165` | ✓ рендерит `groups`, `schedule_counts`, `sync_result`, счётчики | ✓ VERIFIED |
| `app/templates/account_groups/includes/group_row.html` | Макрос строки (мин. 20) | ✓ 110 стр. | ✓ | ✓ импорт в list.html:10 и partial_cards.html:10 | ✓ | ✓ VERIFIED |
| `app/templates/account_groups/partial_cards.html` | Порция прокрутки (мин. 10) | ✓ 18 стр. | ✓ | ✓ `TemplateResponse:235` | ✓ | ✓ VERIFIED |
| `app/templates/account_groups/partials/sync_result.html` | Блок опроса (мин. 20) | ✓ 59 стр. | ✓ | ✓ `include` в list.html:68 + `env.get_template:293` | ✓ | ✓ VERIFIED |
| `app/application/accounts/group_resync.py` | Хелпер переинвентаризации (мин. 60) | ✓ 354 стр. | ✓ | ✓ 3 вызывающих | ✓ | ✓ VERIFIED |
| `alembic/versions/0014_sync_result_and_group_missing.py` | Ревизия D-11/D-12 (мин. 25) | ✓ 57 стр. | ✓ `down_revision="0013"` | ✓ цепь 0013→0014→0015 | ✓ колонки совпадают с ORM | ✓ VERIFIED |
| `app/static/css/app.css` | Секция экрана, `data-group-row` | ✓ стр. 1593-1735 | ✓ | ✓ | — | ✓ VERIFIED |
| `app/pages/groups.py` | Заглушка-редирект (мин. 8) | ✓ 44 стр. | ✓ `RedirectResponse` | ✓ `pages/__init__.py:46` | — | ✓ VERIFIED |
| `tests/test_pages/test_account_groups.py` | Поведенческие тесты (мин. 60) | ✓ 2084 стр., 82 теста | ✓ | ✓ | ✓ | ✓ VERIFIED |
| `tests/test_application/test_group_resync.py` | Тесты D-10/D-11/D-12 (мин. 80) | ✓ 745 стр., 24 теста | ✓ | ✓ | ✓ | ✓ VERIFIED |
| `tests/test_application/test_collect_due_inactive_group.py` | Тесты D-05/D-06 (мин. 50) | ✓ 372 стр., 9 тестов | ✓ | ✓ | ✓ | ✓ VERIFIED |
| `tests/conftest.py` (`seed_group`) | Фикстура посева через ORM | ✓ `:110`, `Group(` на `:141` | ✓ | ✓ | ✓ | ✓ VERIFIED |
| `.planning/REQUIREMENTS.md` (GRP-08 out of scope) | Причина + прослеживаемость | ✓ стр. 156, 220 | ✓ | ✓ согласовано с ROADMAP | — | ✓ VERIFIED |
| `app/routes/groups.py` | ДОЛЖЕН отсутствовать (D-14) | ✓ отсутствует | — | ✓ `app/main.py` его не импортирует | — | ✓ VERIFIED (removal) |
| `app/templates/groups/` | ДОЛЖЕН отсутствовать (D-01) | ✓ каталога нет | — | — | — | ✓ VERIFIED (removal) |

### Key Link Verification

| From | To | Via | Статус | Детали |
|------|----|-----|--------|--------|
| `app/pages/__init__.py` | `app/pages/account_groups.py` | `include_router` | ✓ WIRED | `from app.pages.account_groups import router as account_groups_router` + `router.include_router(account_groups_router)` |
| `account_groups/includes/group_row.html` | `app/pages/account_groups.py` | action формы тумблера | ✓ WIRED | `action="/accounts/{{ account_id }}/groups/{{ group.id }}/toggle"` ↔ `@router.post("/accounts/{account_id}/groups/{group_id}/toggle")` |
| `app/application/scheduling/use_cases.py` | `app/models/group.py` | `is_active` — условие пропуска | ✓ WIRED | `:171 if not group.is_active: continue`, поднято ВЫШЕ ветвления по `account.type` (покрывает Telegram) |
| `alembic/versions/0014_...` | `app/models/messenger_account.py` | совпадение колонок | ✓ WIRED | `last_synced_at:27`, `last_sync_result:38`, `missing_since` в `models/group.py:69` |
| `app/application/accounts/group_resync.py` | `app/models/group.py` | `missing_since` | ✓ WIRED | `:240 group.missing_since = None`, `:284 group.missing_since = marked_at` |
| `app/pages/accounts.py` | `group_resync.py` | `apply_group_resync` | ✓ WIRED | `:863` — встроенного блока only-add больше нет |
| `app/worker/tasks.py` | `group_resync.py` | `apply_group_resync` | ✓ WIRED | `:331` в единой `_sync_groups_async` для WA и MAX |
| `app/pages/ads.py` | `ads/includes/sched_card.html` | `selectattr('account_id'...)` | ✓ WIRED | `sched_card.html:64` + `inactive` множество из `ads.py:259` |
| `account_groups/list.html` | `app/pages/account_groups.py` | сентинел `groups/partial?offset=` | ✓ WIRED | `list.html:190` ↔ `@router.get(".../groups/partial")`; разметка идентична `partial_cards.html` (закреплено `test_sentinel_markup_is_identical_in_both_templates`) |
| `app/pages/account_groups.py` | `app/repositories/schedule.py` | `remove_group_ids` | ✓ WIRED | `:370` |
| `partials/sync_result.html` | `app/pages/account_groups.py` | `groups/sync-status` | ✓ WIRED | `:50 hx-get="/accounts/{{ account_id }}/groups/sync-status"` ↔ `@router.get(".../groups/sync-status")` |
| `app/pages/account_groups.py` | `group_resync.py` | `parse_sync_result` | ✓ WIRED | импорт `:20`, вызов `:186` |
| `app/pages/groups.py` | `app/pages/accounts.py` | `RedirectResponse` на `/accounts` | ✓ WIRED | `:44` |
| `tests/conftest.py` | `app/models/group.py` | `Group(` прямой посев | ✓ WIRED | `:141` |

**Key links: 14/14 WIRED.**

### Data-Flow Trace (Level 4)

| Артефакт | Значение | Источник | Реальные данные | Статус |
|----------|----------|----------|------------------|--------|
| `list.html` | `groups` | `_build_groups_query` → `db.execute` (`:131`) | ✓ | ✓ FLOWING |
| `list.html` | `total_groups` / `active_groups` | два выделенных `select(func.count())` (`:143-162`) | ✓ | ✓ FLOWING |
| `list.html` | `sync_result` | `account.last_sync_result` → `parse_sync_result` (`:186`) | ✓ | ✓ FLOWING |
| `group_row.html` | `schedule_counts` | `_schedule_counts` → `select(Schedule.group_ids).join(Ad)` (`:96-106`) | ✓ | ✓ FLOWING |
| `group_row.html` | `group.missing_since` | пишется `apply_group_resync:284`, снимается `:240` | ✓ | ✓ FLOWING |
| `sync_result.html` | `status` | `account.status` из БД (`:290-295`) | ✓ | ✓ FLOWING |
| `partial_cards.html` | `groups` (2-я порция) | тот же запрос с `offset` (`:227-229`) | ✓ | ✓ FLOWING |
| `sched_card.html` | `inactive` | `ads.py:259` из выборки БД | ✓ | ✓ FLOWING |

Ни одна цепочка не заканчивается статическим возвратом, литералом или моком.

### Behavioral Spot-Checks

Выполнены реальными прогонами тестов в этом процессе верификации (не пересказ SUMMARY).

| Behavior | Command | Result | Статус |
|----------|---------|--------|--------|
| Экран, тумблер, удаление, поиск, прокрутка, плашка, опрос | `pytest tests/test_pages/test_account_groups.py tests/test_application/test_group_resync.py tests/test_application/test_collect_due_inactive_group.py -q` | `136 passed in 101.80s` | ✓ PASS |
| Синк всех трёх путей, htmx-инварианты, адаптивная разметка, шелл, миграции | `pytest tests/test_routes/test_sync_groups.py tests/test_pages/test_htmx_preserved.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_shell.py tests/test_migrations -q` | `247 passed in 789.26s` | ✓ PASS |
| Выключенные группы в редакторе расписаний | `pytest tests/test_pages/test_editor_schedules.py -q -k "disabled_group or disabled_chosen or without_disabled_selections"` | `6 passed` | ✓ PASS |
| Прохибиция «повторная отправка удаления безвредна» | `test_repeated_delete_is_harmless` (в первом прогоне) | passed | ✓ PASS |
| Двойная отправка тумблера возвращает исходное состояние | `test_double_toggle_returns_the_group_to_its_initial_state` | passed | ✓ PASS |
| Защита от повторной отправки на кнопке подтверждения | grep по `app/templates/components/modal.html`, `app/static/js/`, всем шаблонам | ни `disabled`, ни `aria-busy`, ни `x-on:submit` на модалке; собственного JS нет | ✗ FAIL |

**Итого прогнано в этой верификации: 389 тестов, 389 passed, 0 failed.**

### Probe Execution

| Probe | Command | Result | Статус |
|-------|---------|--------|--------|
| — | — | — | ? SKIP |

Проектных probe-скриптов нет (`find scripts -path '*/tests/probe-*.sh'` → пусто); ни один PLAN/SUMMARY фазы probe не объявляет. Роль probe здесь выполняет pytest-суита — прогнана выше.

### Requirements Coverage

| Requirement | Source Plan(s) | Описание | Статус | Evidence |
|-------------|----------------|----------|--------|----------|
| GRP-04 | 03-01, 03-05, 03-08 | Пользователь может открыть экран групп конкретного messenger-аккаунта | ✓ SATISFIED | SC1 + маршрут `account_groups.py:109`, вход с `/accounts` в 9 местах, старый раздел снесён |
| GRP-05 | 03-01, 03-03 | Пользователь может включать и отключать отдельные группы аккаунта | ✓ SATISFIED | SC2 + `account_groups.py:299-332`, отражение в `use_cases.py:171` и `ads.py:243` |
| GRP-06 | 03-05, 03-08 | Пользователь может удалить группу из списка аккаунта | ✓ SATISFIED | SC3 + `account_groups.py:335-377` с чисткой `Schedule.group_ids` |
| GRP-07 | 03-02, 03-04, 03-06 | Повторная синхронизация с показом результата | ✓ SATISFIED | SC4 + ревизия 0014, `apply_group_resync`, плашка и самоостанавливающийся опрос |
| GRP-08 | 03-07 | Ручное добавление группы | ✓ WITHDRAWN (не unmet) | Снятие зафиксировано согласованно: `REQUIREMENTS.md:156` (Out of Scope с причиной и датой), `:220` (строка прослеживаемости переведена в `Out of scope v2.0 (D-13, 2026-08-11)`, а не удалена), `:247/:252` (счётчики пересчитаны 39→38); `ROADMAP.md:26,214,291` согласованы, строка Requirements фазы 3 несёт только GRP-04..07. Код: `app/routes/groups.py` удалён, `app/main.py` его не импортирует, пустое состояние экрана призыва «добавить вручную» не содержит |

**Orphaned requirements:** нет. `grep "Phase 3" .planning/REQUIREMENTS.md` даёт ровно GRP-01..03 (baseline, closed ранее) и GRP-04..08; GRP-04..07 заявлены планами, GRP-08 закрыт как снятый.

**Бухгалтерская заметка (info, не gap):** GRP-04..GRP-07 в `REQUIREMENTS.md` всё ещё стоят как `- [ ]` и `Pending` в таблице прослеживаемости (строки 90-93, 216-219), а строка фазы 3 в Coverage-таблице ROADMAP.md — `In Progress`. Это состояние «фаза ещё не закрыта», и его штатно правит шаг закрытия фазы после верификации, а не исполнение планов.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TBD` / `FIXME` / `XXX` | — | **Ноль вхождений** во всех файлах, изменённых фазой (34 файла `app/` + `alembic/`). Долговой гейт пройден |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | — | Ноль вхождений в файлах фазы |
| `app/repositories/group.py` | весь класс | Мёртвый код | ℹ️ Info | `GroupRepository` остался без единого потребителя после сноса `/groups` и JSON-входа. Зафиксировано осознанно в `deferred-items.md` с проверкой после 03-08: снос потребителей не добавил и не убавил. Решение о слое отложено намеренно, к цели фазы отношения не имеет |
| `app/pages/accounts.py` | 790 | Guard `syncing` не покрывает синхронный TG-путь | ⚠️ Warning | Открытые угрозы T-03-15/T-03-28 (medium, ниже порога блокировки, `threats_open: 0`). Два одновременных POST для `tg_user` оба проходят guard; дубли строк закрыты ограничением схемы `uq_groups_account_external` (ревизия 0015). Задокументировано в 03-SECURITY.md с обоснованием, почему занимать статус здесь нельзя |
| `app/templates/components/modal.html` | 82 | Кнопка подтверждения без состояния выполнения | 🛑 Gap | См. раздел Gaps — единственная провалившаяся must-have истина |

### Human Verification Required

**Нет открытых пунктов.** Человеческое UAT по фазе уже выполнено и зафиксировано: `03-UAT.md`, `status: complete`, 48/48 пройдено, 0 issues — 7 человеческих чекпоинтов (холодный старт с миграциями 0014/0015, адаптивность 320/860/1280, шапка+плашка на трёх ширинах, пометка «отключена» на 320/400, живая синхронизация всех трёх путей на реальном аккаунте, отсутствие внутренностей в тексте ошибки, пять критериев успеха на живом приложении) и 41 автопокрытый пункт с поимённой трассировкой `verified_by`.

Все backstop-истины (`verification: backstop`) фазы закрыты явными доказательствами:
- 03-01 «окно между сбором и постановкой задач» — подтверждена чтением кода: `dispatch_send_tasks` повторной проверки `is_active` не делает, то есть гарантия действительно ограничена моментом сбора, как и объявлено;
- 03-05 (2 шт.) и 03-06 (2 шт.) — визуальные на 320px — закрыты человеческими UAT №2 и №3 (`coverage_id: 03-05/D11`, `03-06/D9`).

Поэтому статус — не `human_needed`.

### Gaps Summary

Цель фазы достигнута: все пять критериев успеха ROADMAP подтверждены кодом и прогнанными тестами, все четыре требования GRP-04..07 удовлетворены, GRP-08 снято согласованно и прослеживаемо, все 14 ключевых связок соединены, все восемь артефактных наборов существенны и подключены, все четыре прохибиции имеют проходящие негативные тесты, долговых маркеров в файлах фазы ноль.

Провалилась **одна** must-have истина плана 03-05 — краевой UI-контракт `E6 loading`:

> «Кнопка подтверждения отражает выполняющийся запрос и не допускает повторной отправки»

Разметка панели подтверждения (`components/modal.html:82`) отдаёт обычную submit-кнопку без единого признака выполняющегося запроса и без защиты от повторной отправки; собственного JS, который мог бы это добавить, в проекте нет. При этом `03-UI-SPEC.md:379` помечает эту строку матрицы как `✅ covered`, а `03-05-SUMMARY.md` про неё не говорит вовсе — то есть истина не была ни закрыта, ни явно снята. Пользовательского вреда нет: маршрут удаления идемпотентен и повторный POST безвреден (проверено `test_repeated_delete_is_harmless`), поэтому это WARNING-уровня расхождение «спецификация утверждает больше, чем делает код», а не поломка сценария удаления.

**Это расхождение выглядит намеренным** — защита реализована на уровне маршрута вместо уровня UI. Чтобы принять его как осознанное отклонение, добавьте в frontmatter этого файла:

```yaml
overrides:
  - must_have: "Кнопка подтверждения отражает выполняющийся запрос и не допускает повторной отправки (E6 loading)"
    reason: "Защита от повторной отправки перенесена на уровень маршрута: удаление идемпотентно (test_repeated_delete_is_harmless), UI-гарда сознательно нет — отключение кнопки не является защитой, а форму можно отправить и без страницы"
    accepted_by: "{ваше имя}"
    accepted_at: "{ISO timestamp}"
```

и синхронно поправьте строку `E6 / loading` в `03-UI-SPEC.md`, чтобы спецификация перестала утверждать непроверяемое. Альтернатива — реализовать гард тем же приёмом, который уже применён в `account_groups/includes/group_row.html` (`x-on:submit` на самой форме), и закрепить его тестом уровня разметки.

---

_Verified: 2026-08-13T08:05:00Z_
_Verifier: Claude (gsd-verifier)_
