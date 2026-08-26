---
phase: quick-260826-6jq-dashboard-drops-worker-block
plan: 01
subsystem: dashboard
status: complete
tags: [dashboard, shell-context, cleanup, removal, tests]
requires:
  - app/pages/common.py::get_shell_context
provides:
  - "контракт шелла без поаккаунтного перечня (только sessions_online / sessions_total)"
  - "четыре положительных запрета на возврат карточки «Воркеры аккаунтов»"
affects:
  - app/pages/dashboard.py
  - app/templates/dashboard.html
  - app/static/css/app.css
tech-stack:
  added: []
  patterns:
    - "положительный запрет как замена снятому инвентаризационному тесту (приём плана 04-05)"
    - "разбор ОТРЕНДЕРЕННОГО ответа и текста CSS без комментариев, чтобы объяснение снятия не краснило собственный запрет"
key-files:
  created:
    - .planning/quick/260826-6jq-ubrat-so-stranitsy-dashboard-blok-otvech/deferred-items.md
  modified:
    - app/templates/dashboard.html
    - app/static/css/app.css
    - app/pages/common.py
    - app/pages/dashboard.py
    - tests/test_pages/test_shell.py
    - tests/test_pages/test_responsive_markup.py
  deleted:
    - app/templates/dashboard/includes/worker_row.html
decisions:
  - "WORKER_ONLINE_STATUS оставлена: после снятия перечня у неё остался один потребитель — счётный подзапрос пилюли, и она по-прежнему ЕДИНСТВЕННОЕ объявление предиката «онлайн»"
  - "sessions_online / sessions_total оставлены: их читает шапка шелла на всех 26 маршрутах, а не дашборд"
  - "утверждения снятых тестов о владении и о предикате переехали на числа агрегатов, а не потерялись вместе с предметом"
  - "красное в tests/test_planning/ признано пред-существующим и НЕ чинилось: коммиты задачи не тронули .planning ни одним байтом"
metrics:
  duration: ~55m
  completed: 2026-08-26
actuals:
  tokens: 21000
  tasks: 3
  commits: 2
---

# Quick 260826-6jq: дашборд без карточки воркеров — Summary

Карточка «Воркеры аккаунтов» снята со страницы дашборда вместе с плумбингом,
существовавшим только ради неё: шаблоном строки, стилями перечня и отдельным
запросом за строками messenger-аккаунтов, который контракт шелла делал на каждом
из 26 страничных маршрутов, а читал один.

## Что сделано

### Задача 1 — снятие блока и его плумбинга (`a97a583`)

| Слой | Изменение |
|------|-----------|
| `app/templates/dashboard.html` | снят импорт макроса строки и карточка целиком (строки 58–102); на месте блока оставлен комментарий Jinja, называющий причину снятия и два теста, которые держат запрет |
| `app/templates/dashboard/includes/worker_row.html` | файл удалён (46 строк) |
| `app/static/css/app.css` | сняты семь правил перечня (`.worker-list`, `.worker-row*`); имя `.worker-row__dot.is-online` вычеркнуто из `@media (prefers-reduced-motion: reduce)`, комментарий над правилом приведён с «четыре» к «три» и назвал причину второго вычёркивания |
| `app/pages/common.py` | сняты `WORKER_LIST_CAP`, отдельный запрос `worker_rows`, сборка списка словарей и ключи `sessions` / `sessions_truncated`; докстринг и комментарии приведены к новому положению дел |
| `app/pages/dashboard.py` | сняты три ключа контекста (`sessions`, `sessions_truncated`, `sessions_total`) |

Что осталось нетронутым и почему — проверено явно:

- `sessions_online` / `sessions_total` в контракте шелла — их читает пилюля
  состояния сессий в шапке `base.html` на всех 26 маршрутах;
- `WORKER_ONLINE_STATUS` — её читает скалярный подзапрос счёта онлайн-аккаунтов;
- `@keyframes pulse` — три живых потребителя (`grep` подтверждает: строки 673,
  1410, 2490 в `app.css`);
- `app/templates/admin/includes/worker_row.html` — ДРУГОЙ файл с тем же
  basename, живой, потребляется `admin/includes/workers_partial.html`.

### Задача 2 — тесты (`ba169b7`)

Сняты девять тестов и два помощника разбора (`_worker_rows`, `_worker_states`),
предмет которых перестал существовать.

Три теста переписаны, чтобы их утверждения не ушли вместе с предметом:

| Было | Стало | Что сохранено |
|------|-------|---------------|
| `test_dashboard_worker_list_excludes_another_users_account` | `test_dashboard_account_count_excludes_another_users_account` | владение чужой строкой — теперь на числах пилюли (`total="1"`, online `1`) |
| `test_shell_reads_worker_state_in_a_single_query` | `test_shell_makes_no_own_read_of_messenger_accounts` | утверждение ИНВЕРТИРОВАНО: собственных чтений строк ноль; блок про агрегаты в общем round-trip и проверка на N+1 оставлены дословно |
| `test_shell_aggregate_is_derived_from_the_worker_list` | `test_shell_counts_accounts_and_online_accounts_by_one_predicate` | из четырёх аккаунтов онлайном считаются ровно два — единственность предиката |

Добавлены четыре положительных запрета:

- `test_the_dashboard_carries_no_per_account_worker_block` — признаков перечня
  нет в ОТРЕНДЕРЕННОЙ разметке, и при этом пилюля шапки на месте (без второй
  половины запрет прошёл бы и на снесённом заодно индикаторе);
- `test_the_shell_contract_carries_no_per_account_list` — ключей `sessions` и
  `sessions_truncated` в словаре нет, агрегаты равны единице; этим же закрыта
  граница секретов, которую держал снятый `test_shell_worker_list_carries_no_secrets`;
- `test_the_dashboard_worker_row_template_is_gone` — шаблона нет на диске,
  разметки нет ни в одном шаблоне под `app/templates/dashboard/`, а строка
  таблицы админки на месте;
- `test_the_dashboard_worker_list_left_no_css_behind` — селекторов нет в CSS
  (разбор через `_css_without_comments()`), а блок `.session-pill` / `.session-dot` жив.

Признаки перечня вынесены в один кортеж `WORKER_LIST_MARKERS`: три теста
проверяют разные поверхности, но предмет у них один, и разъехавшиеся списки дали
бы запрет, дырявый там, где список короче.

### Задача 3 — полный прогон и граф

`uv run pytest tests/ -q`: **2282 passed, 1 failed** за 23 минуты. Единственное
красное — `tests/test_planning/test_state_progress_matches_roadmap.py`, разбор
ниже. `graphify update .` отработал (12367 узлов, 23773 ребра);
`graphify-out/` игнорируется git, незакоммиченных правок вне перечисленных файлов
`git status` не показывает.

## Проверка границы задачи

```
git diff HEAD~2 HEAD -- app/templates/admin/ app/services/ app/worker/ wa_worker/ | wc -l
0
```

Ноль строк — подсистема воркеров и раздел админки не изменены ни одним байтом.
`tests/test_pages/test_admin_panel.py` остался зелёным без единой правки, что и
было заявлено в плане доказательством T-6jq-03.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Новый тест контракта падал на отсутствующем пользователе**

- **Found during:** Задача 2
- **Issue:** `test_the_shell_contract_carries_no_per_account_list` был написан по
  плану только с фикстурой `db_session`, но `_dashboard_user` ищет
  `testuser@test.com`, которого сеет фикстура `authed_client` — `NoResultFound`.
- **Fix:** добавлена фикстура `authed_client`, как у остальных тестов секции,
  зовущих `get_shell_context` напрямую.
- **Commit:** `ba169b7`

**2. [Rule 1 — Bug] Перепись шапок блоков дашборда разъехалась со снятой карточкой**

- **Found during:** Задача 2
- **Issue:** `test_dashboard_blocks_share_one_head_without_a_divider`
  (`tests/test_pages/test_responsive_markup.py:4605`) требовал ровно трёх
  вхождений `data-blockhead` в `dashboard.html`. Третья шапка принадлежала
  снятой карточке воркеров, и тест покраснел с `2 == 3`. В `files_modified`
  плана этот тест назван, но в разборе задачи 2 он не упомянут.
- **Fix:** число приведено к двум, комментарий переписи и докстринг названы
  причиной. Утверждение по смыслу не ослаблено: собственная шапка у нового блока
  это число не увеличила бы.
- **Commit:** `ba169b7`

### Отступления от буквы плана

**Комментарии на месте снятого.** План допускал их косвенно (оба новых теста
написаны так, чтобы объяснение снятия их не краснило). Комментарии оставлены в
`dashboard.html` и `app.css` — они называют причину снятия и тесты, держащие
запрет.

## Deferred Issues

**`test_the_machine_readable_progress_is_derived_from_the_roadmap` — красный,
НЕ починен, пред-существующий.**

Тест сверяет счёт планов, выводимый из `.planning/ROADMAP.md`, с полями
`progress.*` во frontmatter `.planning/STATE.md`: выводится `0`, записано `110`.

Доказательство пред-существования:

- `git diff --stat HEAD~2 HEAD -- .planning` пуст — коммиты задачи не тронули эти
  файлы ни одним байтом;
- `.planning/ROADMAP.md` последний раз менялся коммитом `3d1e672`
  («chore: archive v2.0 milestone files»), которым строки фаз уехали в архив
  вехи, и выводить счёт стало не из чего;
- `.planning/STATE.md` последний раз менялся коммитом `6a1d88f` — предыдущей
  быстрой задачей.

Не починено по SCOPE BOUNDARY: правка `.planning/STATE.md` ради зелёного
означала бы занизить счёт закрытой вехи до нуля, потеряв запись «110/110»,
которую сама STATE.md объясняет как выправленную при закрытии вехи. Решать это
должен тот, кто закрывает веху. Разбор — в
`.planning/quick/260826-6jq-.../deferred-items.md`, запись заведена и в
`.planning/WINDOWS.md`.

## Known Stubs

Нет. Задача снимает код, а не добавляет; заглушек, пустых значений и
плейсхолдеров не заведено.

## Threat Flags

Нет. Новой сетевой, авторизационной или файловой поверхности не появилось —
поверхность раскрытия данных (`sessions` в словаре шелла, печатавшемся в HTML на
каждой из 26 страниц) СНЯТА целиком, что и было диспозицией `mitigate` для
T-6jq-01.

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | `a97a583` | `refactor(quick-260826-6jq): снять карточку воркеров с дашборда и её плумбинг` |
| 2 | `ba169b7` | `test(quick-260826-6jq): запретить возврат перечня воркеров на дашборд` |

Задача 3 своего коммита не имеет: прогон набора и `graphify update .` файлов под
контролем версий не меняют (`graphify-out/` в `.gitignore`).

## Self-Check: PASSED

| Проверка | Результат |
|----------|-----------|
| `260826-6jq-SUMMARY.md` на диске | FOUND |
| `deferred-items.md` на диске | FOUND |
| `.planning/WINDOWS.md` (запись 9) | FOUND |
| `app/templates/admin/includes/worker_row.html` (не тронут) | FOUND |
| `app/templates/dashboard/includes/worker_row.html` | CONFIRMED GONE |
| коммит `a97a583` | FOUND |
| коммит `ba169b7` | FOUND |
