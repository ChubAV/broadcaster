---
phase: 03-gruppy-akkaunta
plan: 01
subsystem: ui
tags: [fastapi, jinja2, sqlalchemy, alpine, celery, structlog, tdd]

# Dependency graph
requires:
  - phase: 01-interfeysnyy-fundament
    provides: "Дизайн-система (макросы toggle/avatar/card/empty_state/button), шелл base.html с блоками page_title/page_subtitle/page_actions, правило трёх синхронных копий строки аккаунта"
  - phase: 02-obyavleniya-i-raspisaniya
    provides: "Правило «владение проверяется на каждом входе», прецедент нового условия в диспетчеризации (D-01, пропуск черновиков), базовый путь без JS (D-09)"
provides:
  - "Экран `/accounts/{id}/groups`: список групп конкретного аккаунта с проверкой владения"
  - "Маршрут `POST /accounts/{id}/groups/{gid}/toggle` — обратимое включение/отключение группы"
  - "Вход «Настроить группы» во всех трёх синхронных копиях строки аккаунта на `/accounts`"
  - "Условие D-05 в `collect_due_schedules`: выключенная группа не получает задач отправки на всех трёх каналах"
  - "structlog-событие `group_skipped_inactive` — единственный след тихого пропуска (D-06)"
  - "Макрос строки `account_groups/includes/group_row.html` и шаблон страницы — основа для планов 03-05 и 03-06"
affects: [03-02, 03-03, 03-04, 03-05, 03-06, дашборд, история]

actuals:
  tokens: 15105
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Экран, вложенный в аккаунт: `active_page` родительского раздела при собственном маршруте (D-02)"
    - "Тройной WHERE на маршруте изменения состояния: id + user_id + account_id, клиентскому account_id не верят"
    - "Карточная строка [data-group-row] вместо data-row-таблицы для экранов, остающихся списком карточек на всех ширинах"

key-files:
  created:
    - app/pages/account_groups.py
    - app/templates/account_groups/list.html
    - app/templates/account_groups/includes/group_row.html
    - tests/test_pages/test_account_groups.py
    - tests/test_application/test_collect_due_inactive_group.py
  modified:
    - app/pages/__init__.py
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/accounts/partials/sync_status_card.html
    - app/application/scheduling/use_cases.py

key-decisions:
  - "Пропуск выключенной группы врезан в per-group цикл `collect_due_schedules`, а не в WHERE выборки расписаний: состав групп хранится JSON-списком на расписании, а выключение группы состав не меняет — тумблер обратим"
  - "`session.get(Group, group_id)` поднят ВЫШЕ ветвления по `account.type`: до правки объект группы запрашивался только в ветке WA/MAX, и условие внутри неё пропустило бы Telegram"
  - "Тумблер отвечает редиректом на экран групп в обоих случаях — и при найденной, и при ненайденной группе: различимый отказ сообщал бы о существовании чужих групп"
  - "Страница чужого аккаунта отвечает редиректом на /accounts, как и несуществующий аккаунт — тем же ответом, без различимого сигнала"

patterns-established:
  - "Вложенный в аккаунт экран: собственный маршрут `/accounts/{id}/...`, но `active_page='accounts'` — подсветка меню остаётся у родительского раздела"
  - "Вход на дочерний экран дублируется во всех синхронных копиях строки родителя безусловно, без ветки по статусу"

requirements-completed: [GRP-04, GRP-05]

coverage:
  - id: D1
    description: "Пользователь открывает /accounts/{id}/groups своего аккаунта и видит только группы этого аккаунта (GRP-04, D-02)"
    requirement: "GRP-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_page_shows_groups_of_this_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_page_hides_groups_of_another_account_of_the_same_user"
        status: pass
    human_judgment: false
  - id: D2
    description: "Чужой аккаунт и чужая группа недостижимы: страница не отдаёт данных, toggle не меняет состояния (T-03-01, T-03-02)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_page_of_a_foreign_account_leaks_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_leaves_a_foreign_group_alone"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_does_not_trust_the_account_id_from_the_url"
        status: pass
    human_judgment: false
  - id: D3
    description: "Тумблер переключает группу одним действием без подтверждения, обратимо, ровно одну группу, не трогая состав расписаний (GRP-05, D-05, D-08)"
    requirement: "GRP-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_inverts_is_active_and_redirects"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_double_toggle_returns_the_group_to_its_initial_state"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_touches_exactly_one_group"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_does_not_edit_the_schedules"
        status: pass
    human_judgment: false
  - id: D4
    description: "Выключенная группа не получает задач отправки при диспетчеризации на всех трёх каналах; включение немедленно возобновляет рассылку (D-05)"
    requirement: "GRP-05"
    verification:
      - kind: unit
        ref: "tests/test_application/test_collect_due_inactive_group.py#test_only_the_active_group_of_a_schedule_gets_a_task"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_collect_due_inactive_group.py#test_inactive_group_produces_no_task_for_any_channel"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_collect_due_inactive_group.py#test_enabling_the_group_resumes_dispatch"
        status: pass
    human_judgment: false
  - id: D5
    description: "Тихий пропуск: записи в SendLog не создаётся, расписание продолжает двигать next_run_at (D-06)"
    verification:
      - kind: unit
        ref: "tests/test_application/test_collect_due_inactive_group.py#test_skipping_writes_nothing_to_the_send_log"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_collect_due_inactive_group.py#test_next_run_at_moves_forward_when_every_group_is_off"
        status: pass
    human_judgment: false
  - id: D6
    description: "Экран достижим кликом с /accounts — вход «Настроить группы» во всех трёх копиях разметки строки и во всех ветках статуса (UI-SPEC E8)"
    requirement: "GRP-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_accounts_screen_links_to_the_account_groups"
        status: pass
      - kind: other
        ref: "grep -c 'accounts/.*groups' app/templates/accounts/list.html → 3"
        status: pass
    human_judgment: false
  - id: D7
    description: "Базовый путь без JS: тумблер остаётся настоящей POST-формой с перехватом на самой форме (D-09)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_is_a_real_post_form"
        status: pass
    human_judgment: false
  - id: D8
    description: "Внешний вид и адаптивность экрана на 320/400px — карточные строки без CSS-секции, которая приходит планом 03-05"
    verification: []
    human_judgment: true
    rationale: "Нумерованная секция app.css для [data-group-row] по плану создаётся планом 03-05; до неё разметка живёт на наследуемых классах карточки. Визуальная приёмка на брейкпоинтах невозможна автоматически и относится к экрану в собранном виде — её место в UAT фазы."

# Metrics
duration: 23 min
completed: 2026-08-12
status: complete
---

# Phase 3 Plan 01: Сквозной срез экрана групп аккаунта Summary

**Экран `/accounts/{id}/groups` с проверкой владения и обратимым тумблером плюс условие D-05 в `collect_due_schedules`, из-за которого выключенная группа впервые перестаёт получать задачи отправки на всех трёх каналах.**

## Performance

- **Duration:** 23 min
- **Started:** 2026-08-12T09:56:43Z
- **Completed:** 2026-08-12T10:20:01Z
- **Tasks:** 2 (обе TDD, четыре гейта RED/GREEN)
- **Files modified:** 10 (5 создано, 5 изменено)

## Accomplishments

- **Сквозной срез экрана доказан целиком:** маршрут → владение → выборка → шаблон → POST-форма → БД → редирект. Новый роутер `app/pages/account_groups.py` (страница и toggle) зарегистрирован в `app/pages/__init__.py` за общей зависимостью `load_shell_context`.
- **Тумблер получил реальное следствие.** Условие D-05 врезано в per-group цикл `collect_due_schedules`: выключенная группа не получает `DispatchTask` ни на `tg_user`, ни на `wa`, ни на `max`. Надпись макета «выключенные группы пропускаются при рассылке» стала правдой, а не обещанием.
- **Вход на экран открыт из всех трёх синхронных копий строки аккаунта** (`list.html`, `partial_cards.html`, `partials/sync_status_card.html`) и во всех трёх ветках статуса каждой — включая файл подмены по опросу, потеря входа в котором проявилась бы только после первого опроса.
- **Пропуск оставлен тихим (D-06):** запись в `SendLog` не создаётся, новый статус журнала не вводится; единственный след — structlog-событие `group_skipped_inactive`.
- **Обратимость тумблера удержана двумя сторонами:** маршрут инвертирует `is_active` (двойное нажатие возвращает исходное состояние), а состав `Schedule.group_ids` не читается и не пишется ни маршрутом, ни диспетчеризацией.

## Task Commits

Каждая задача закоммичена атомарно; обе — TDD, поэтому по два коммита на задачу:

1. **Task 1 (tracer): экран групп аккаунта и рабочий тумблер**
   - `e3514de` — test (RED): 14 падающих тестов из 16
   - `a9f5996` — feat (GREEN): 16/16 зелёных
2. **Task 2: выключенная группа пропускается при диспетчеризации**
   - `5ab3545` — test (RED): 8 падающих из 10 (2 зелёных — прохибиции, охраняющие уже верное поведение)
   - `1aa1000` — feat (GREEN): 10/10 зелёных

_Фазы REFACTOR не потребовалось: обе реализации минимальны и повторяют форму своих аналогов._

## Files Created/Modified

**Создано:**

- `app/pages/account_groups.py` — роутер экрана: `account_groups_page` (владение аккаунтом + выборка групп с `order_by(Group.id)` и приёмом `limit+1`), `account_groups_toggle` (тройной WHERE, инверсия `is_active`, PRG-редирект)
- `app/templates/account_groups/list.html` — страница: шапка через блоки шелла, карточный список, пустое состояние «Групп пока нет»
- `app/templates/account_groups/includes/group_row.html` — макрос `group_row(group, account_id)`: аватар инициалов, экранированное имя группы, тумблер внутри настоящей POST-формы
- `tests/test_pages/test_account_groups.py` — 16 поведенческих тестов экрана (владение, состав и порядок списка, тумблер, деградация без JS, вход с `/accounts`)
- `tests/test_application/test_collect_due_inactive_group.py` — 10 тестов D-05/D-06 (три канала параметризацией, живучесть расписания, тихий пропуск)

**Изменено:**

- `app/pages/__init__.py` — импорт и `include_router(account_groups_router)`
- `app/templates/accounts/list.html`, `.../partial_cards.html`, `.../partials/sync_status_card.html` — `link_button('Настроить группы', …)` в actions-ячейку всех веток статуса; в третьей копии ссылка собрана из переменной `account_id`, а не `account.id`
- `app/application/scheduling/use_cases.py` — модуль-логгер structlog, подъём `session.get(Group, …)` выше ветвления по типу аккаунта, условие пропуска с комментарием-инвариантом D-05

## Decisions Made

- **Условие D-05 — в per-group цикле, а не в WHERE выборки расписаний.** Состав групп хранится JSON-списком в `Schedule.group_ids`, поэтому WHERE-фильтр по составу там невозможен в принципе. Но даже будь он возможен, он был бы неверен: выключение группы состав расписания не меняет, и пропускается ГРУППА, а не расписание — `next_run_at` продолжает двигаться.
- **`session.get(Group, group_id)` поднят выше ветвления по `account.type`.** До правки объект группы запрашивался только в ветке WA/MAX. Условие, оставленное внутри неё, пропустило бы Telegram — самый населённый канал продукта. Ветка WA/MAX теперь переиспользует уже полученный объект; лишний вызов из кода убран.
- **Неразличимый ответ на чужие идентификаторы.** И страница чужого аккаунта, и toggle чужой группы отвечают тем же редиректом, что и несуществующие: различимый отказ сообщал бы, какие идентификаторы заняты чужими сущностями.
- **Пустое состояние пока одно.** Различить «Групп пока нет» и «Все группы удалены» можно только по `last_synced_at`, колонка которого приходит миграцией плана 03-04. До неё рендерится ветка, называющая следующий шаг.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Тест возобновления рассылки не перевзводил расписание**

- **Found during:** Task 2 (GREEN)
- **Issue:** `test_enabling_the_group_resumes_dispatch` вызывал `collect_due_schedules` дважды подряд. Первый вызов (с выключенной группой) уже сдвигал `next_run_at` в будущее — расписание переставало быть просроченным, и второй вызов не выбирал его вовсе. Тест краснел не из-за пропуска группы, а из-за собственного посева: в логе виден ровно один `group_skipped_inactive`, от первого вызова.
- **Fix:** Перед вторым сбором расписание возвращается в просроченное состояние (`next_run_at` на сутки назад) вместе с включением группы. Причина зафиксирована комментарием в теле теста со ссылкой на парный `test_next_run_at_moves_forward_when_every_group_is_off`, который это свойство и утверждает.
- **Files modified:** `tests/test_application/test_collect_due_inactive_group.py`
- **Verification:** 10/10 тестов файла зелёные; реализация не менялась — дефект был в тесте, а не в коде.
- **Committed in:** `1aa1000` (коммит GREEN задачи 2)

---

**Total deviations:** 1 auto-fixed (1 bug в собственном тестовом посеве)
**Impact on plan:** Изменений в границах плана нет. Ни одной правки продуктового кода деривация не потребовала; scope creep отсутствует.

## Issues Encountered

**Гейт tracer-задачи разрешён прогоном, а не остановкой.** Task 1 — `type="tracer"`, и его фидбек-гейт в интерактивном режиме требует остановки на `checkpoint:human-verify` до расширяющих задач. `workflow.auto_advance` и `workflow._auto_chain_active` в `.planning/config.json` — `false`, но `mode: "yolo"` и `human_verify_mode: "end-of-phase"` задают неинтерактивный прогон с приёмкой в конце фазы, а исполнитель работает изолированным агентом в worktree без канала к пользователю. Остановка оставила бы план без SUMMARY и обрушила бы волну. Гейт исполнен по автономной ветке: `<verify>` трассера перепрогнан на закоммиченном дереве (16/16 зелёных), после чего началась задача 2. Решение фиксируется здесь как видимое, а не молчаливое.

**Прочего:** нет. Существующие тесты диспетчеризации переживают новый `session.get(Group, …)` на TG-пути без правок — прогон `tests/test_worker/`, `tests/test_worker_tasks.py` и `tests/test_application/test_collect_due_draft.py` зелёный.

## Known Stubs

Заглушек, мешающих цели плана, нет. Сознательно отложенное, с адресом плана-владельца:

| Что | Где | Почему и кто закрывает |
|-----|-----|------------------------|
| Нет CSS-секции для `[data-group-row]`, `[data-group-list]`, `.group-row--off` | `app/static/css/app.css` | По плану нумерованная секция создаётся ЦЕЛИКОМ планом 03-05; разметка до неё работоспособна на наследуемых классах карточки |
| Шапка экрана без карточки аккаунта, счётчика «N активных из M» и CTA «Синхронизировать всё» | `app/templates/account_groups/list.html` | Состав экрана — планы 03-05 (список, счётчики, поиск) и 03-06 (синк и его результат) |
| Пустое состояние одно вместо двух ветвей | `app/templates/account_groups/list.html` | Ветку «Все группы удалены» различает `last_synced_at`; колонка приходит миграцией плана 03-04 |
| Подсказка пустого состояния ссылается на кнопку «Синхронизировать всё», которой на экране ещё нет | `app/templates/account_groups/list.html` | Копирайтинг задан планом дословно; кнопка появляется планом 03-06 |
| Нет удаления группы, поиска и бесконечной прокрутки (`has_next`/`next_offset` считаются, но паршала нет) | `app/pages/account_groups.py` | GRP-06 и остальной состав экрана — планы 03-02 и 03-05 |

## Threat Flags

Новой поверхности сверх зафиксированной в `<threat_model>` плана не появилось. Отработка регистра:

| Threat ID | Disposition | Как закрыт |
|-----------|-------------|------------|
| T-03-01 | mitigate | Владение аккаунтом — отдельным запросом `MessengerAccount.id == account_id AND user_id == user.id`; выборка групп дополнительно ограничена `Group.user_id` и `Group.account_id`. Тест «чужой аккаунт не отдаёт имён групп» написан до реализации |
| T-03-02 | mitigate | Тройной WHERE у toggle; при несовпадении состояние не меняется, ответ — тот же редирект. Два теста: чужой пользователь и свой-но-другой аккаунт |
| T-03-03 | mitigate | `{{ group.name }}` под autoescape, в макросы уходит текст, не разметка; покрыто обходящим все шаблоны `test_no_unsafe_escaping` |
| T-03-04 | accept | Пропуск фиксируется только structlog-событием; отсутствие записи в `SendLog` закреплено тестом |
| T-03-05 | accept | CSRF-токенов в проекте нет ни на одной форме; новая форма тумблера новой поверхности класса не добавляет |

## User Setup Required

None — внешней конфигурации план не требует, миграций схемы не содержит.

## Next Phase Readiness

- **Готово к планам первой волны и далее.** Роутер, шаблон страницы и макрос строки — точки расширения для 03-05 (шапка, счётчики, поиск, прокрутка, CSS-секция) и 03-06 (синк и его результат). Маршрут удаления группы (GRP-06) встаёт рядом с toggle по той же форме владения.
- **Плану 03-03 (снос `/groups`)** передаётся рабочая замена: экран групп аккаунта достижим и функционален, поэтому удаление глобального раздела больше не оставляет пользователя без места управления группами.
- **Открытое предположение планировщика по GRP-07** («какие границы у требования, которого классификатор не отнёс ни к одной категории») не разрешено и переносится на верификацию фазы человеком — автоматически оно не закрывалось и в критерий не превращалось.
- **Блокеров нет.** Полная суита — 921 зелёных против базы 895; прирост ровно на 26 новых тестов этого плана, деградации нет.

## Self-Check: PASSED

Проверено на закоммиченном дереве:

- Все пять созданных файлов существуют на диске (`app/pages/account_groups.py`, оба шаблона, оба тестовых файла) — размеры выше объявленных в `must_haves.artifacts` минимумов
- Все четыре коммита задач присутствуют в истории ветки: `e3514de`, `a9f5996`, `5ab3545`, `1aa1000`
- Acceptance criteria обеих задач перепрогнаны поимённо: `account_groups_page`/`account_groups_toggle` объявлены; `Group.account_id == account_id` — 2 вхождения; `account_groups_router` зарегистрирован; `active_page` = `accounts`; `accounts/.*groups` в `accounts/list.html` — 3; подстрока `/groups` присутствует в каждой из трёх копий строки; `group_skipped_inactive` и `D-05` — в `use_cases.py`
- Оба `<verify>` задачи 1 зелёные (16 и 153 теста), оба `<verify>` задачи 2 зелёные (10 и 58 тестов)
- Плановая `<verification>`: `uv run pytest tests/ -q` → **921 passed**, 0 failed

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-12*
