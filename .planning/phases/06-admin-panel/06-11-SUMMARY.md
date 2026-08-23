---
phase: 06-admin-panel
plan: 11
subsystem: ui
tags: [admin, payments, ledger, filters, jinja2, sqlalchemy, tdd]

requires:
  - phase: 06-admin-panel
    plan: 10
    provides: "overview_stats.paying_total / monthly_revenue — счёт платящих по трём условиям и выручка; paying_subscription_clauses в слое доступа к данным"
  - phase: 06-admin-panel
    plan: 04
    provides: "incidents.unclosed_payments_stmt — правило «платёж не закрыт» через множество терминальных статусов"
  - phase: 06-admin-panel
    plan: 09
    provides: "app/pages/admin.py в редакции подраздела «Пользователи» — форма обработчика, санация значений адреса, полоса чипсов двумя осями"
  - phase: 06-admin-panel
    plan: 03
    provides: "components/filter_chips.html в библиотеке компонентов с ОБЯЗАТЕЛЬНЫМ базовым адресом"
  - phase: 05.1-ploskaya-podpiska
    provides: "PAYMENT_LIST_CAP с комментарием, называющим этот подраздел потребителем; format_amount с проверкой конечности внутри; слова статусов платежа"
provides:
  - "app/application/admin/payments_query.py — величина «истекло и не продлено за окно», журнал платежей с двумя осями, потолком и признаком его срабатывания"
  - "expired_not_renewed_clauses в app/repositories/user.py — три условия истёкшей нельготной подписки одним объявлением"
  - "unclosed_payment_clause — правило «платёж не закрыт» ОТДЕЛЕНО от своей выборки: читателей у него стало два"
  - "app/templates/admin/includes/payment_row.html — четвёртая строка админки той же формы, что воркер, очередь и пользователь"
  - "Машинный свидетель: тарифный план платежа недостижим из разметки ПО ПОСТРОЕНИЮ — строка уезжает значениями, а не строкой модели"
  - "tests/test_{application,pages}/__init__.py — одноимённые файлы суиты в двух каталогах перестали ронять прогон на сборке"
affects: [06-14-mobile-acceptance, phase-06-verification]

actuals:
  # 113 592 символа реализованного диффа / 4. Шкала та же, что у `estimate`
  # плана (60 000), и это НЕ счётчик токенов раннера. Значение не подтянуто к
  # оценке: план ПЕРЕоценил объём вдвое, ровно как и план 06-10, и по той же
  # причине. Обе задачи легли на уже существующие формы — выручка оказалась
  # посчитанной соседним планом, правило незакрытого статуса объявленным,
  # потолок объявленным, форма строки отгруженной трижды. Изобретать пришлось
  # только величину ушедших и две оси фильтра.
  tokens: 28398
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Прикладной модуль подраздела отдаёт строку ЗНАЧЕНИЯМИ, а не строкой модели: запрет на показ колонки становится свойством формы данных, а не дисциплиной автора шаблона"
    - "Условие, у которого появился второй читатель, отделяется от своей выборки в отдельную функцию — копия разошлась бы с оригиналом молча"
    - "Ось фильтра объявлена одним словарём «значение → (подпись, условие)»; чипсы и множество допустимых значений ВЫВЕДЕНЫ из него"

key-files:
  created:
    - app/application/admin/payments_query.py
    - app/templates/admin/includes/payment_row.html
    - tests/test_application/test_admin_payments.py
    - tests/test_pages/test_admin_payments.py
    - tests/test_application/__init__.py
    - tests/test_pages/__init__.py
  modified:
    - app/pages/admin.py
    - app/templates/admin/payments.html
    - app/repositories/user.py
    - app/application/admin/incidents.py
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Выручка НЕ переопределена в новом модуле: подраздел зовёт paying_total + monthly_revenue плана 06-10. Второе определение той же величины дало бы два разных числа на двух экранах одной админки"
  - "Три условия истёкшей подписки положены в слой доступа к данным (expired_not_renewed_clauses), а не в прикладной модуль: признак бесплатного доступа читает ровно один файл app/application/, и гейт этого правила не ослаблен"
  - "Правило «платёж не закрыт» выделено в unclosed_payment_clause и переиспользовано, а не скопировано: свидетелем служит тождество, а не совпадение поведения"
  - "Строка журнала уезжает из модуля значениями пяти колонок — тарифный план и ключ платежа во внешней системе недостижимы из разметки по построению (D-42, T-06-PAY1)"
  - "Ось периода названа длительностями (24 часа / 7 дней / 30 дней), а не словом «Сегодня»: «сегодня» уже означает локальную полночь ПОЛЬЗОВАТЕЛЯ, а административный журнал смотрит на платежи всех сразу"
  - "Даты в журнале администратора подписаны, хотя у журнала пользователя «Дата» освобождена: рядом с датой здесь стоит имя плательщика, и дата без подписи читалась бы как дата его регистрации"

patterns-established:
  - "Отрицательное утверждение про колонку закрепляется посевом с ЗАПОЛНЕННЫМ значением: пустая колонка не отличает «не показываем» от «нечего показать»"
  - "Утверждение про единственность правила пишется тождеством функции (clause is clause), а не совпадением выдачи: копия совпадает с оригиналом ровно до дня, когда оригинал изменится"
  - "Константу подменяют и требуют, чтобы за ней поехала ПОДПИСЬ — так проверяется, что число приехало подстановкой, а не выписано в копирайте литералом"

requirements-completed: [ADMIN-10]

coverage:
  - id: D1
    description: "Регулярная выручка считается без льготных пользователей — по трём условиям, а не по двум (D-38)"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_mrr_counts_only_the_paying_subscription_of_the_whole_population"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_mrr_excludes_the_comped_user_whose_term_is_still_alive"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_mrr_of_an_empty_base_is_zero_and_not_an_exception"
        status: pass
    human_judgment: false
  - id: D2
    description: "Вместо доли ушедших показана величина, называющая ровно то, что считает: «истекло и не продлено за 30 дней» (D-41)"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_expired_not_renewed_counts_the_dead_term_without_a_later_payment"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_expired_not_renewed_skips_the_user_who_paid_after_the_term_died"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_lapsed_caption_takes_its_window_from_the_single_constant"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_lapsed_figure_prints_zero_instead_of_disappearing"
        status: pass
    human_judgment: false
  - id: D3
    description: "Средний чек и доля ушедших не показываются: имён обеих величин нет ни в модуле, ни в разметке (D-41)"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_module_never_names_the_metrics_that_the_decision_threw_out"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_exactly_two_figures_are_printed_and_the_thrown_out_ones_are_absent"
        status: pass
    human_judgment: false
  - id: D4
    description: "Тарифный план платежа не появляется в разметке журнала ни в одной строке (D-42)"
    requirement: "ADMIN-10"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_no_plan_value_from_the_dead_tariff_column_reaches_the_markup"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_payments.py#test_no_plan_lookup_exists_in_either_payments_template"
        status: pass
    human_judgment: false
  - id: D5
    description: "Журнал фильтруется по статусу и периоду; значения обеих осей санируются замкнутым множеством и в выражение сырыми не попадают"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_ledger_count_equals_its_own_content_under_the_same_filters"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_a_value_outside_the_declared_axis_means_all_and_never_reaches_the_query"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_both_axes_are_drawn_by_the_library_component_with_this_base_path"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_a_junk_axis_value_highlights_nothing_and_filters_nothing"
        status: pass
    human_judgment: false
  - id: D6
    description: "Незакрытые платежи видны в журнале и отбираются по ОТСУТСТВИЮ терминального статуса, а не по равенству одному"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_ledger_selects_unclosed_payments_by_the_absence_of_a_terminal_status"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_unclosed_chip_reuses_the_single_declared_rule_instead_of_a_copy"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_unclosed_payment_is_visible_and_wears_its_own_status"
        status: pass
    human_judgment: false
  - id: D7
    description: "Потолок журнала — уже объявленное проектом значение, и его срабатывание названо подписью, а не проявляется коротким списком"
    requirement: "ADMIN-10"
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_ledger_cap_truncates_and_reports_its_own_firing"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_payments.py#test_the_ledger_cap_is_the_value_the_project_already_declared"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_firing_cap_names_itself_above_the_ledger"
        status: pass
    human_judgment: false
  - id: D8
    description: "Суммы печатаются общим денежным глобалом, у которого проверка конечности значения уже внутри"
    requirement: "ADMIN-10"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_amounts_go_through_the_money_global_and_junk_does_not_break_the_page"
        status: pass
    human_judgment: false
  - id: D9
    description: "Подраздел отвечает 200 администратору и 403 постороннему; ключ платежа во внешней платёжной системе не печатается нигде"
    requirement: "ADMIN-10"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_subsection_answers_the_admin_and_refuses_the_stranger"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_subsection_refuses_the_regular_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_the_screen_never_prints_the_external_payment_key"
        status: pass
    human_judgment: false
  - id: D10
    description: "Раскладка подраздела на узком экране: подписи колонок едут вместе со значениями, крупный кегль не занят"
    requirement: "ADMIN-10"
    verification:
      - kind: automated_ui
        ref: "tests/test_pages/test_responsive_markup.py#test_rowhead_titles_are_covered_by_labels[admin/payments.html]"
        status: pass
    human_judgment: true
    rationale: "Сетка доказывает, что подпись у каждой колонки ЕСТЬ, но не что раскладка пяти колонок на 375px читается: ширины колонок заданы значением --cols, и годность их — вопрос глаза. Приёмка на живом экране входит в план 06-14"

duration: 78 min
completed: 2026-08-23
status: complete
---

# Phase 6 Plan 11: Подраздел «Платежи» Summary

**Подраздел показывает две величины — регулярную выручку без льготных и число людей, у которых доступ истёк и не был продлён за месяц, — и журнал платежей всего сервиса с двумя осями фильтра и честным потолком; тарифный план снятой системы тарифов недостижим из разметки по построению, а не по договорённости.**

## Performance

- **Duration:** 78 min
- **Tasks:** 2 из 2
- **Files created:** 6
- **Files modified:** 5
- **Tests added:** 31 (14 прикладных + 17 страничных)

## Accomplishments

- **Величина ухода называет ровно то, что считает.** «Истекло и не продлено за 30 дней» — дата окончания в прошлом внутри окна и ни одного успешного платежа после неё. Доля не считается: подписка одна на пользователя, дата сдвигается при продлении, истории продлений строка не хранит, и любая доля из имеющегося была бы числом, чьё определение никто не назовёт через месяц.
- **Выручка не задвоена.** Новый модуль её не считает вовсе — подраздел зовёт `paying_total` и `monthly_revenue`, отгруженные планом 06-10. Второе определение той же величины дало бы «MRR на обзоре не сходится с MRR в платежах».
- **Тарифный план недостижим из разметки ПО ПОСТРОЕНИЮ.** Строка журнала уезжает из прикладного модуля пятью значениями, а не строкой модели: дотянуться из шаблона до колонки, которой в строке нет, нельзя. Тем же движением недостижим `yookassa_payment_id` — ключ подделки уведомления об оплате.
- **Незакрытые платежи отбираются по отсутствию терминального статуса.** Правило вынесено из `unclosed_payments_stmt` в `unclosed_payment_clause` и переиспользовано; свидетелем служит ТОЖДЕСТВО функции, а не совпадение поведения, и написан тест на ТРЕТЬЕМ, никогда не встречавшемся статусе.
- **Числа не скопированы в копирайт.** И окно величины ушедших, и потолок журнала приезжают в текст экрана подстановкой; тесты подменяют константы и требуют, чтобы за ними поехала подпись.

## Task Commits

1. **Задача 1: Платёжные величины и журнал** — `04fdbd7` (test, RED) → `3ef8fb1` (feat, GREEN)
2. **Задача 2: Подраздел «Платежи»** — `1bbb96b` (test, RED) → `f2ec932` (feat, GREEN)

Фазы REFACTOR ни у одной задачи не было: чистить оказалось нечего — обе реализации написаны в форме, уже отгруженной соседними подразделами, и второй проход менял бы её ради самого прохода.

## Files Created/Modified

- `app/application/admin/payments_query.py` (создан) — величина ушедших, журнал с двумя осями, потолком и признаком срабатывания; предмет платежа замкнутым множеством из трёх строк
- `app/templates/admin/includes/payment_row.html` (создан) — строка журнала пятью колонками, подписи из того же списка, что и шапка
- `app/templates/admin/payments.html` — подраздел целиком вместо честной пустоты
- `app/pages/admin.py` — обработчик подраздела: санация обеих осей, момент один на весь запрос, агрегатов не строит
- `app/repositories/user.py` — `expired_not_renewed_clauses`: три условия истёкшей нельготной подписки
- `app/application/admin/incidents.py` — `unclosed_payment_clause` отделён от `unclosed_payments_stmt`
- `tests/test_application/test_admin_payments.py` (создан) — 14 тестов
- `tests/test_pages/test_admin_payments.py` (создан) — 17 тестов
- `tests/test_pages/test_responsive_markup.py` — два новых шаблона внесены в перечни сверки и в три счётчика
- `tests/test_application/__init__.py`, `tests/test_pages/__init__.py` (созданы) — уникальность имён модулей суиты

## Decisions Made

1. **Ось периода названа длительностями, а не «Сегодня».** Слово «сегодня» в проекте уже занято разделом истории и означает там ЛОКАЛЬНУЮ полночь пользователя. У административного журнала такой величины нет: он смотрит на платежи всех людей сразу, и чья именно полночь была бы «сегодня» — ответить нечем. Второе значение одного слова на соседних экранах врёт обоим читателям; скользящее окно с честным именем не врёт никому. Форма взята у окон журнала логов того же раздела.
2. **Колонка «Дата» подписана, хотя у журнала платежей пользователя она освобождена.** Там журнал одного человека, где каждая строка про него самого; здесь рядом с датой стоит имя ПЛАТЕЛЬЩИКА, и на 860px, где шапка скрыта, дата без подписи прочиталась бы как дата регистрации того, чьё имя напечатано следом.
3. **Присоединение имени пользователя ВНЕШНЕЕ.** Внешний ключ платежа объявлен с каскадным удалением, поэтому платежа без человека в норме не бывает — но внутреннее присоединение уронило бы такую строку из денежного журнала МОЛЧА, а молча пропавший платёж хуже платежа без имени. Пустое имя печатает прочерк, называющий причину.
4. **Пустых состояния два, и различие несущее.** «Не нашлось по фильтрам» называет выход и даёт кнопку сброса; «платежей ещё не было» не предлагает ничего — предлагать там нечего. Слитые в одно, они отправили бы администратора искать поломку приёма платежей вместо того, чтобы снять свой же фильтр.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Правило проекта важнее буквы критерия] Признак бесплатного доступа НЕ читается в новом прикладном модуле, и `monthly_revenue` в нём не объявлена**

- **Найдено:** Задача 1
- **Что требовал план:** критерий приёмки `grep -Ec 'has_free_access' app/application/admin/payments_query.py` не меньше 1 и артефакт `contains: "def monthly_revenue"` в том же файле.
- **Почему это невыполнимо:** гейт `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision` утверждает, что признак встречается в `app/application/` РОВНО в одном файле — предикате доступа. Гейт читает ТЕКСТ (его собственный докстринг называет это прямо), поэтому даже упоминание имени в комментарии нового модуля уронило бы прогон. Второе: `monthly_revenue` уже отгружена планом 06-10 в `overview_stats.py`, и второе объявление той же денежной величины — ровно тот дубль, который фаза запрещает.
- **Что сделано вместо:** три условия истёкшей подписки положены в слой доступа к данным как `expired_not_renewed_clauses` — зеркально уже отгруженному `paying_subscription_clauses`, с тем же объяснением цены; обработчик подраздела зовёт `paying_total` + `monthly_revenue` планом 06-10. Гейт не ослаблен и не расширен. Это тот же ход, которым закрылись планы 06-09 и 06-10, когда гейт срабатывал на них.
- **Файлы:** `app/repositories/user.py`, `app/application/admin/payments_query.py`, `app/pages/admin.py`
- **Проверено:** `uv run pytest tests/test_application/test_no_metering_remains.py -q` — 5 passed; выручка покрыта тремя тестами D1
- **Коммит:** `3ef8fb1`

**2. [Rule 2 — то же основание] `TERMINAL_STATUSES` не названо в новом модуле; отбор идёт общей функцией**

- **Найдено:** Задача 1
- **Что требовал план:** `grep -n 'TERMINAL_STATUSES' app/application/admin/payments_query.py` находит отбор по множеству.
- **Почему изменено:** `incidents.unclosed_payments_stmt` объявлен «единственным местом правила статуса». Написать множество вторым местом ради грепа значило бы завести копию, которую этот греп и должен предотвращать.
- **Что сделано вместо:** условие выделено в `unclosed_payment_clause()`, `unclosed_payments_stmt` теперь зовёт его, журнал зовёт его же. Греп-свидетель заменён на более сильный: тест `test_the_unclosed_chip_reuses_the_single_declared_rule_instead_of_a_copy` утверждает ТОЖДЕСТВО функции — копия его роняет, а поведенческую проверку копия прошла бы.
- **Файлы:** `app/application/admin/incidents.py`, `app/application/admin/payments_query.py`
- **Проверено:** `tests/test_application/test_incidents.py` зелёный; тест на третьем статусе зелёный
- **Коммит:** `3ef8fb1`

**3. [Rule 3 — Блокирующее] Прогон суиты падал на СБОРКЕ из-за двух одноимённых тестовых файлов**

- **Найдено:** Задача 2, при первом полном прогоне
- **Проблема:** план называет оба файла `test_admin_payments.py` — в `tests/test_application/` и в `tests/test_pages/`. Ни один из этих двух каталогов не нёс `__init__.py`, поэтому pytest импортировал модуль по БАЗОВОМУ имени и падал с `import file mismatch`, не выполнив ни одного утверждения. По отдельности каждый файл проходил — красным становился только полный прогон.
- **Исправление:** добавлены `tests/test_application/__init__.py` и `tests/test_pages/__init__.py`. Это не новшество, а восстановление собственной раскладки проекта: восемь из десяти каталогов суиты такой файл уже несли, и эти два были единственным исключением. Переименование одного из файлов было отвергнуто: оно спрятало бы предмет (прикладной модуль и его страничный потребитель называются одинаково) за особенностью инструмента.
- **Файлы:** `tests/test_application/__init__.py`, `tests/test_pages/__init__.py`
- **Проверено:** полный прогон собирается и выполняется — 2039 passed
- **Коммит:** `f2ec932`

**4. [Rule 2 — Обязательная регистрация в гейтах вёрстки] Два новых шаблона внесены в перечни сверки**

- **Найдено:** Задача 2
- **Проблема:** `test_rowhead_pages_all_have_a_parametrization_entry` и `test_row_templates_without_header_are_accounted_for` красные — новый шаблон с шапкой и новый макрос строки обязаны быть НАЗВАНЫ, а не проходить по умолчанию. Гейты сработали ровно так, как задуманы.
- **Исправление:** `admin/payments.html` внесён в `ROWHEAD_PAGES` с посевом `admin_payments` и пустой разностью неподписанных колонок; `admin/includes/payment_row.html` — в `ROW_TEMPLATES_WITHOUT_HEADER` с названным классом причины; три счётчика подняты с объяснением шага (7→8 шаблонов с шапкой, 8→9 строк без шапки).
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверено:** `uv run pytest tests/test_pages/test_responsive_markup.py -q` — 131 passed
- **Коммит:** `f2ec932`

**5. [Не отклонение по существу] `app/static/css/app.css` в плане назван изменяемым, но НЕ изменён**

- Подраздел не завёл ни одного нового класса: utility-классы по проекту запрещены и проверяются сплошным обходом всех шаблонов, а все нужные примитивы (`chip-bar`, `card`, `mono`, `[data-row]`, `[data-rowhead]`, `[data-stack]`) уже отгружены. Раскладка пяти колонок задана значением `--cols` в самом шаблоне — тем же приёмом, что у трёх соседних подразделов.

---

**Total deviations:** 4 auto-fixed (2 × Rule 2 «правило проекта важнее буквы критерия», 1 × Rule 3 «блокирующее», 1 × Rule 2 «регистрация в гейтах») + 1 запись без правки кода.
**Impact on plan:** Предмет плана исполнен целиком. Два отклонения — это отказ ОСЛАБИТЬ машинные гейты ради буквы грепа: в обоих случаях греп-свидетель заменён на более сильный (тождество функции, тест на третьем статусе). Расширения области нет: тронуты ровно те файлы, которые названы планом, плюс два объявления в слое доступа к данным и в модуле признаков инцидента — оба вынужденные единственностью правил, оба на одну функцию.

## Issues Encountered

**Пре-существующий отказ `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings`.** Красный в полном прогоне, зелёный в одиночку. Воспроизводится на базовом коммите фазы, уже записан в `.planning/phases/06-admin-panel/deferred-items.md` с двумя минимальными репродьюсерами. НЕ диагностировался и НЕ чинился — вне области плана. Он единственная причина, по которой `just test` возвращает ненулевой код: кроме него в полном прогоне зелено всё (2039 passed, 1 failed).

## Known Stubs

Нет. Заглушек, подставных значений и невыведенных данных подраздел не содержит: обе величины и все пять колонок журнала приходят из запросов к своей базе.

## TDD Gate Compliance

Обе задачи прошли последовательность RED → GREEN полностью:

| Задача | RED | GREEN | REFACTOR |
|--------|-----|-------|----------|
| 1 | `04fdbd7` (`ModuleNotFoundError` — модуля нет) | `3ef8fb1` (14 passed) | не потребовался |
| 2 | `1bbb96b` (15 failed из 17) | `f2ec932` (17 passed) | не потребовался |

⚠️ **Одна оговорка про RED задачи 1, названная прямо.** Три теста выручки (`test_mrr_*`) на момент RED падали ВМЕСТЕ со всем файлом — из-за отсутствия импортируемого модуля, а не потому, что выручка не считалась. Она уже считалась: план 06-10 отгрузил её накануне. Это ровно тот случай, о котором предупреждает правило «неожиданный GREEN в фазе RED — расследуй»: расследование показало, что величина существует, и результатом расследования стало решение её ПЕРЕИСПОЛЬЗОВАТЬ, а не написать вторую. Тесты при этом оставлены: до этого плана у `paying_total` и `monthly_revenue` не было ни одного прямого теста, и три условия выручки держались только страничной проверкой.

## Verification Results

| Проверка | Результат |
|----------|-----------|
| `uv run pytest tests/test_application/test_admin_payments.py -q` | 14 passed (требовалось ≥10) |
| `uv run pytest tests/test_application/test_admin_payments.py -q -k mrr` | 3 passed, код 0 |
| `uv run pytest tests/test_pages/test_admin_payments.py -q` | 17 passed (требовалось ≥9) |
| `uv run pytest tests/test_pages/test_admin_payments.py -q -k no_plan` | 2 passed, код 0 |
| `uv run pytest tests/test_application/test_no_metering_remains.py -q` | 5 passed — гейт не тронут и не расширен |
| `uv run pytest tests/test_application -q` | 259 passed |
| `uv run pytest tests/test_pages/test_responsive_markup.py -q` | 131 passed |
| `just test` | 2039 passed, 1 failed — только пре-существующий отказ (см. «Issues Encountered») |
| `grep -Ec 'payment\.plan\|\.plan\b' <оба шаблона>` | 0 и 0 |
| `grep -Ec 'ARPU\|Средний чек\|Отток' admin/payments.html` | 0 |
| `grep -c 'components/filter_chips.html' admin/payments.html` | 1 |
| `grep -Ec 'base_path=' admin/payments.html` | 2 |
| `grep -c 'format_amount' admin/includes/payment_row.html` | 1 |
| `grep -Ec 'arpu\|ARPU\|churn' payments_query.py` | 0 |
| `grep -c 'normalize_utc' payments_query.py` | 4 (требовалось ≥2) |
| `grep -Ec 'has_free_access' payments_query.py` | 0 — см. отклонение 1 |
| `grep -n 'TERMINAL_STATUSES' payments_query.py` | пусто — см. отклонение 2 |

## Next Phase Readiness

Подраздел «Платежи» закрывает критерий 5 фазы. Открытым остаётся приёмка раскладки пяти колонок на узком экране — она входит в план 06-14 вместе с остальными подразделами фазы (покрытие D10).

## Self-Check: PASSED

- Все шесть созданных файлов существуют на диске.
- Все четыре коммита задач присутствуют в истории ветки: `04fdbd7`, `3ef8fb1`, `1bbb96b`, `f2ec932`.
- Все критерии приёмки обеих задач перепрогнаны; два невыполнимых буквально задокументированы отклонениями 1 и 2 с заменой свидетеля на более сильный.
- Плановая `<verification>` перепрогнана целиком; единственный красный тест полного прогона — пре-существующий и вне области.
