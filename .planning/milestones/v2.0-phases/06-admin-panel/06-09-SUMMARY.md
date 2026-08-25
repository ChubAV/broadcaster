---
phase: 06-admin-panel
plan: 09
subsystem: ui
tags: [fastapi, sqlalchemy, jinja2, pagination, filtering, sqlite, postgres]

requires:
  - phase: 06-admin-panel
    provides: "план 06-03 — компонент чипсов components/filter_chips.html с ОБЯЗАТЕЛЬНЫМ base_path"
  - phase: 06-admin-panel
    provides: "план 06-08 — тот же страничный модуль админки и тот же файл стилей"
  - phase: 05.1
    provides: "access_is_open / days_left — единственное объявление правила доступа; _access_view и _active_subscriptions_by_user в админке"
provides:
  - "app/application/admin/users_query.py — поиск, две оси, страница и счёт ОДНИМ выражением"
  - "app/repositories/user.py::access_axis_clause — перевод вердикта доступа в язык запроса, пиннутый к оригиналу тестом"
  - "app/templates/admin/includes/user_row.html — макрос строки пользователя по форме строк воркера и очереди"
  - "первый потребитель отгруженного примитива [data-pager] (app.css:1561)"
  - "юникодные lower()/upper() для SQLite — регистронезависимый поиск ведёт себя одинаково на обеих СУБД"
affects: [06-admin-panel, будущие подразделы со страницами, любой регистронезависимый поиск по кириллице]

actuals:
  tokens: 28700
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Фильтры, поиск, страница и счёт одним выражением: count зовёт ту же функцию условий, что и выдача"
    - "Значение оси из адреса — КЛЮЧ замкнутого словаря условий: санация встроена в поиск условия, а не приставлена сбоку"
    - "SQL-двойник Python-вердикта живёт в слое доступа к данным и пиннется к оригиналу тестом по общей популяции"
    - "Юникодное складывание регистра в SQLite: тестовая СУБД подтягивается к боевой, а не наоборот"

key-files:
  created:
    - app/application/admin/users_query.py
    - app/templates/admin/includes/user_row.html
    - tests/test_pages/test_admin_users.py
  modified:
    - app/pages/admin.py
    - app/repositories/user.py
    - app/database.py
    - app/templates/admin/users.html
    - tests/test_pages/test_responsive_markup.py
    - tests/test_repositories/test_user_repo.py

key-decisions:
  - "Ось доступа отбирает В ЗАПРОСЕ (иначе счёт и страница не могут быть одним выражением), а перевод вердикта положен в app/repositories/, а не в app/application/ — гейт «признак бесплатного доступа читает ровно один файл прикладной логики» не ослаблен"
  - "Явного func.lower() с обеих сторон НЕДОСТАТОЧНО: lower() в SQLite сам складывает только латиницу. Юникодная замена зарегистрирована на соединении в app/database.py"
  - "Репозиторные get_all_users и search_users сняты вместе со своими тестами, а не оставлены без потребителей"
  - "Счётчик «N из M» собирается ОДНИМ выражением шаблона и печатается дважды; положение в списке пишется дробью, чтобы две разные пары чисел не читались как одна разошедшаяся"
  - "Число дней до конца доступа печатается ТОЛЬКО при доступе, открытом сроком, и только подсказкой; льготному печатается признак бессрочности"

patterns-established:
  - "Пустое состояние ФИЛЬТРОВ отличимо от пустого состояния продукта и называет выход; второе не предлагает ничего"
  - "Номер страницы из адреса зажимается, а не проверяется на допустимость: отказ был бы отказом в обслуживании по подконтрольному отправителю значению"
  - "Инвентари подписей ячеек и шаблонов строки поднимаются ТЕМ ЖЕ коммитом, что и колонка"

requirements-completed: [ADMIN-04]

coverage:
  - id: D1
    description: "Поиск, обе оси, страница и счётчик считаются одним выражением: «N из M» равно тому, что лежит в выдаче при тех же условиях"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_search_count_equals_the_search_contents"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_both_axes_and_the_search_apply_together"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_the_counter_over_the_list_equals_the_list"
        status: pass
    human_judgment: false
  - id: D2
    description: "Список выбирается страницами по 50 с точным общим счётом; выборок без предела на пути подраздела не осталось"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_second_page_shares_nothing_with_the_first"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_unlimited_select_left_the_repository"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_the_edge_pages_disable_the_button_instead_of_hiding_it"
        status: pass
    human_judgment: false
  - id: D3
    description: "Поиск по кириллице ведёт себя одинаково на обеих СУБД проекта"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_search_folds_cyrillic_case_both_ways"
        status: pass
    human_judgment: false
  - id: D4
    description: "Две группы чипсов строятся компонентом библиотеки с базовым адресом подраздела; значения санируются замкнутым множеством"
    requirement: ADMIN-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_two_chip_groups_come_from_the_library_with_the_subsection_path"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_switching_one_axis_keeps_the_other_and_drops_the_page"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_an_unknown_axis_value_means_all_and_never_reaches_the_expression"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ось доступа считается существующим вердиктом; SQL-перевод и Python-оригинал отвечают одно и то же на каждой строке"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_sql_axis_agrees_with_the_single_python_verdict"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_users.py#test_the_access_axis_partitions_everyone"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_no_metering_remains.py#test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision"
        status: pass
    human_judgment: false
  - id: D6
    description: "Число дней печатается только при доступе, открытом сроком; величин потребления и квоты и ручного продления доступа нет"
    requirement: ADMIN-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_a_comped_user_gets_no_number_of_days"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_an_expired_user_gets_a_date_and_not_a_negative_number"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_no_consumption_or_quota_survived_the_reverse_layout"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_no_manual_extension_of_access_exists"
        status: pass
    human_judgment: false
  - id: D7
    description: "Карточка пользователя остаётся отдельной страницей, её вход в историю отправок жив"
    requirement: ADMIN-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_the_row_leads_to_the_card_and_does_not_unfold_in_place"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_users.py#test_the_card_still_reaches_the_user_history"
        status: pass
    human_judgment: false
  - id: D8
    description: "Визуальная посадка подраздела: полоса чипсов, счётчик, строки и панель страниц на ширинах 375/860/1280"
    verification: []
    human_judgment: true
    rationale: "Раскладка сетки колонок, перенос полосы чипсов и читаемость длинных адресов на узкой ширине — свойства, которые тест по разметке подтверждает только косвенно: он видит атрибуты, но не видит, что колонка схлопнулась или что адрес вылез за карточку"

duration: 95min
completed: 2026-08-22
status: complete
---

# Phase 06 Plan 09: Подраздел «Пользователи» Summary

**Администратор находит конкретного человека поиском и двумя группами фильтров, видит честное «N из M», листает страницами по 50 — и ни одно из этих чисел не может разойтись с содержимым, потому что все они считаются одним выражением.**

## Performance

- **Duration:** ~95 min
- **Tasks:** 2/2
- **Files modified:** 9 (3 созданы, 6 изменены)
- **Tests:** 34 в `tests/test_pages/test_admin_users.py` (план требовал не менее 22); полный прогон — 1979 passed

## Accomplishments

- **Выборка пользователей стала одним выражением.** `apply_user_filters` — единственное место, где строятся условия подраздела; `count_users` зовёт её же. Счётчик над списком и содержимое страницы не могут ответить на один вопрос двумя разными числами. Это ровно тот дефект, который проект уже закрывал в разделе истории общей функцией фильтров (D-34).
- **Выборка без предела ушла с пути подраздела.** `get_all_users()` и `search_users()` тянули всю таблицу пользователей на одну страницу; обе сняты вместе со своими тестами — потребителей у них не осталось. На их месте страницы по 50 с точным `COUNT` по тому же выражению (D-33, T-06-USR2).
- **Поиск по кириллице перестал зависеть от СУБД.** Явного `func.lower()` с обеих сторон оказалось НЕДОСТАТОЧНО — см. «Отклонения» ниже. Встроенные `lower()`/`upper()` SQLite заменены юникодными на уровне соединения, и тестовая СУБД подтянута к боевой.
- **Две группы чипсов, страницы и счётчик собраны из уже отгруженного.** Компонент `components/filter_chips.html` (план 06-03) с явным `base_path`; примитив `[data-pager]` получил своего первого потребителя за всё время своего существования. Новых классов подраздел не завёл ни одного.
- **Колонки называют то, что существует.** Макетные величины потребления и предела не перенесены — после смены модели тарификации такой величины в продукте нет. Число дней до конца доступа печатается только там, где доступ открыт сроком: у льготного с мёртвой датой оно отрицательно (D-35).

## Task Commits

1. **Задача 1: Выборка — фильтры, поиск, страница и счёт одним выражением** (TDD)
   - `11a669a` — test: падающие тесты выборки
   - `280bae1` — feat: `users_query.py` + юникодный `lower()` для SQLite
2. **Задача 2: Подраздел — две группы чипсов, страницы, колонки** (TDD)
   - `9558038` — test: падающие тесты разметки подраздела
   - `1e91409` — feat: обработчик, разметка, строка, снятие выборок без предела

_Репозиторная чистка (`get_all_users`/`search_users`) исполнена в коммите задачи 2, а не задачи 1 — см. «Отклонения»._

## Files Created/Modified

- `app/application/admin/users_query.py` — **создан.** `ACCESS_CHIPS`/`STATE_CHIPS`, `USERS_PAGE_SIZE = 50`, `apply_user_filters`, `count_users`, `users_page`.
- `app/repositories/user.py` — `access_axis_clause` (перевод вердикта доступа в язык запроса) добавлен; `get_all_users` и `search_users` сняты.
- `app/pages/admin.py` — обработчик `/admin/users` переписан под модуль выборки; `_account_counts_by_user`, `_parse_page`, `_users_href` добавлены.
- `app/database.py` — юникодные `lower()`/`upper()` для соединений SQLite.
- `app/templates/admin/users.html` — переписан: полоса чипсов, форма поиска, счётчик, строки макросом, панель страниц, два пустых состояния.
- `app/templates/admin/includes/user_row.html` — **создан.** Строка по форме `worker_row.html` / `queue_row.html`.
- `tests/test_pages/test_admin_users.py` — **создан.** 34 теста.
- `tests/test_pages/test_responsive_markup.py` — два инвентаря подняты тем же коммитом, что и колонки.
- `tests/test_repositories/test_user_repo.py` — два теста сняты вместе со своим предметом.

## Decisions Made

1. **Ось доступа отбирает в запросе, а её перевод живёт в слое доступа к данным.** Счётчик и страница обязаны считаться одним выражением (D-34), значит отбор по доступу обязан случиться ДО `OFFSET`, то есть в SQL. Правило доступа объявлено на Python и в модуле, который по своей объявленной границе ничего не знает про SQLAlchemy, — поэтому перевод неизбежен. Положен он в `app/repositories/user.py`: это работа слоя доступа к данным, и она не подпадает под гейт «признак бесплатного доступа читает ровно один файл `app/application/`». Цена перевода оплачена тестом `test_the_sql_axis_agrees_with_the_single_python_verdict`, который прогоняет оба выражения по одной популяции.
2. **Счётчик собирается один раз и печатается дважды.** `{% set users_counter = ... %}` в шаблоне; над списком и в панели страниц печатается одна и та же переменная. Положение в списке («страница 1 / 3») пишется дробью намеренно: две разные пары чисел одной формой на одном экране читались бы как одна величина, напечатанная дважды и разошедшаяся.
3. **Пустых состояния два.** «Не нашлось по фильтрам» называет выход и даёт чем его исполнить; «зарегистрированных ещё нет» не предлагает ничего — предлагать нечего. Слитые в одно, они отвечали бы «пользователей нет» на экран, где пользователи есть.
4. **Номер страницы разбирается мягко.** Объявить параметр как `int` значило бы отдать 422 на `?page=абв`, то есть отказать в обслуживании по значению из чужой ссылки (T-06-USR3). Разбор — в обработчике, зажим диапазона — в модуле, который один знает, сколько страниц получилось.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Механизм, предписанный планом для кириллического поиска, не достигал своей цели**

- **Найдено при:** Задача 1
- **Проблема:** План предписывал «привести обе стороны сравнения к одному регистру ЯВНО» и утверждал, что этого достаточно, чтобы поиск вёл себя одинаково в суите и в бою. Утверждение неверно: встроенный `lower()` SQLite сам складывает регистр **только для латиницы** (проверено: `select lower('Иван')` → `'Иван'`). `func.lower()` с обеих сторон даёт на SQLite сравнение `'Иван' LIKE '%иван%'` → ложь. Тест 3 плана («поиск по кириллическому имени в верхнем регистре находит пользователя, записанного в нижнем; тест обязан быть зелёным на СУБД суиты») при буквальном исполнении предписания был бы красным.
- **Исправление:** В `app/database.py` на событие `connect` любого движка зарегистрирована замена `lower()`/`upper()` юникодными для соединений, у которых есть `create_function` (SQLite и его адаптеры; у адаптеров PostgreSQL такого метода нет — проверено на `AsyncAdapt_asyncpg_connection`). Направление правки: **тестовая СУБД подтягивается к боевой**, поведение продукта не меняется. Функции переопределены парой — мир, где `lower()` знает про кириллицу, а `upper()` нет, хуже мира, где не знает ни одна.
- **Файлы:** `app/database.py`
- **Проверка:** `test_the_search_folds_cyrillic_case_both_ways`; полный прогон 1979 passed — переопределение не сдвинуло ни одного существующего утверждения.
- **Коммит:** `280bae1`

**2. [Rule 3 — Blocking] Перевод вердикта доступа в SQL ронял машинный гейт единственного читателя признака**

- **Найдено при:** Задача 2 (полный прогон суиты)
- **Проблема:** Первая редакция положила SQL-перевод оси доступа в `app/application/admin/users_query.py`. Это уронило `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`: признак бесплатного доступа обязан читаться в `app/application/` ровно одним файлом — предикатом доступа.
- **Исправление:** Перевод (`access_axis_clause` и её условия) перенесён в `app/repositories/user.py`; `users_query.py` зовёт её и признака не называет. Гейт **не ослаблен и не переписан** — ослабить его значило бы разрешить следующему читателю третье чтение уже без вопросов. SQL-выражения по нашим таблицам — работа слоя доступа к данным, а не прикладного модуля; причина размещения выписана в самом файле.
- **Файлы:** `app/repositories/user.py`, `app/application/admin/users_query.py`
- **Проверка:** `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision` — зелёный; `test_the_sql_axis_agrees_with_the_single_python_verdict` — зелёный.
- **Коммит:** `1e91409`

**3. [Rule 2 — Missing critical] Добавлен тест равенства SQL-перевода и Python-вердикта**

- **Найдено при:** Задача 1
- **Проблема:** План требовал не заводить своей копии правила доступа, но одновременно требовал, чтобы счёт и страница считались одним выражением, — а это возможно только с отбором по доступу в SQL. Перевод неизбежен, и без пиннинга разойтись ему было бы на чём: достаточно забыть про активность строки или ослабить строгость сравнения дат, и администратор увидел бы «открыт» у человека, которому продукт уже отказывает.
- **Исправление:** `test_the_sql_axis_agrees_with_the_single_python_verdict` прогоняет `access_is_open` и SQL-отбор по одной и той же популяции из шести состояний (платный, льготный, льготный с мёртвой датой, истёкший, без строки подписки, деактивированный) и требует совпадения множеств.
- **Файлы:** `tests/test_pages/test_admin_users.py`
- **Коммит:** `11a669a`

**4. [Rule 3 — Blocking] Два инвентаря разметки подняты тем же коммитом, что и колонки**

- **Найдено при:** Задача 2 (полный прогон суиты)
- **Проблема:** Набор колонок строки переписан целиком (D-35), а строка вынесена в отдельный файл. Это уронило `test_admin_users_cell_labels_present` (кортеж-свидетель подписей всё ещё называл «Статус» и не знал про «Состояние» и «Аккаунтов») и `test_row_templates_without_header_are_accounted_for` (новый файл строки без шапки не был назван поимённо).
- **Исправление:** `ADMIN_USER_CELL_LABELS` поднят до нового набора; `admin/includes/user_row.html` внесён в перечень с причиной, число поднято 7 → 8. Оба — **по прямому предписанию комментариев в самих тестах**: «изменение объявленного числа — признание СОЗНАТЕЛЬНОГО шага», и поднимать их полагается тем же планом, иначе новая колонка приехала бы без подписи и на 860px стала бы значением без названия.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Коммит:** `1e91409`

**5. [Rule 3 — Blocking] Репозиторная чистка перенесена из коммита задачи 1 в коммит задачи 2**

- **Найдено при:** Задача 1
- **Проблема:** План отнёс снятие `get_all_users`/`search_users` к задаче 1, но обработчик подраздела переписывает задача 2. Снятие методов в коммите задачи 1 оставило бы `admin_users` зовущим несуществующие методы — то есть коммит с падающим приложением в середине плана.
- **Исправление:** Граница задач сдвинута на один файл: методы сняты в том же коммите, где обработчик перестал их звать. Ни один коммит плана не оставляет суиту красной.
- **Файлы:** `app/repositories/user.py`, `tests/test_repositories/test_user_repo.py`
- **Коммит:** `1e91409`

**6. [Rule 1 — Bug] Дефект в собственном тесте: заглушка хеша пароля**

- **Найдено при:** Задача 2
- **Проблема:** Хелпер посева заводил пользователей с `password_hash="x"`. Утверждение «хеша пароля нет в разметке» при этом проверяло отсутствие буквы «x» в HTML — то есть было красным всегда и не проверяло ничего осмысленного.
- **Исправление:** Хеш сделан заметным и разным у каждого пользователя.
- **Файлы:** `tests/test_pages/test_admin_users.py`
- **Коммит:** `1e91409`

---

**Total deviations:** 6 auto-fixed (Rule 1 ×2, Rule 2 ×1, Rule 3 ×3)
**Impact on plan:** Расширения предмета нет. Пять из шести отклонений — следствия того, что план не мог знать заранее: неверная посылка про складывание регистра в SQLite, машинный гейт единственного читателя признака, два инвентаря разметки и порядок коммитов. Шестое — дефект в собственном тесте. Единственная правка вне списка `files_modified` плана — `app/database.py`, и она названа выше вместе с причиной.

## Issues Encountered

**Ось доступа не выражается в SQL «бесплатно» — конфликт двух требований плана.** План требовал (а) не заводить своей копии правила доступа и (б) считать поиск, фильтры, страницу и счётчик одним выражением. Второе требует отбора по доступу до `OFFSET`, то есть в SQL; первое запрещает второе объявление правила. Разрешено переводом, положенным в слой доступа к данным и **пиннутым к оригиналу тестом по общей популяции**: одно правило по-прежнему объявлено один раз, а его перевод не может разойтись с ним молча. Оба свойства — и «ровно один читатель признака в прикладной логике», и «перевод отвечает то же, что оригинал» — держатся тестами, а не соглашением.

**Известный чужой отказ.** `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` красен в полном прогоне и зелен поодиночке. Воспроизводится на базовом коммите фазы, записан в `deferred-items.md`, к этому плану отношения не имеет и не диагностировался.

## User Setup Required

None — внешних служб план не трогает.

## Next Phase Readiness

- Подраздел «Пользователи» отгружен целиком: ADMIN-04 закрыт.
- `[data-pager]` получил первого потребителя и форму вызова — следующий подраздел со страницами повторяет её, а не изобретает.
- `access_axis_clause` доступна любому будущему отбору по доступу; порог входа в неё — прочитать, почему она лежит в репозитории, а не в прикладном модуле.
- Юникодное складывание регистра теперь общесистемно: любой следующий регистронезависимый поиск по кириллице ведёт себя в суите так же, как в бою, и отдельного внимания не требует.
- Открытых заглушек план не оставил.

## Self-Check: PASSED

- Все заявленные файлы существуют (`users_query.py`, `user_row.html`, `test_admin_users.py`, `database.py`, `user.py`, этот SUMMARY).
- Все четыре коммита плана присутствуют в истории: `11a669a`, `280bae1`, `9558038`, `1e91409`.
- Заявленное число тестов подтверждено сбором: `34 tests collected`.
- Полный прогон суиты: `1979 passed, 1 failed` — единственный отказ известен, предшествует фазе и записан в `deferred-items.md`.

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*
