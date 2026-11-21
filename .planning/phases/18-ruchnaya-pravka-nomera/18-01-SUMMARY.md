---
phase: 18-ruchnaya-pravka-nomera
plan: 01
subsystem: ui
tags: [account-label, phone, manual-mark, jinja-macro, css, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "колонки phone / phone_is_manual (CHECK ck_messenger_accounts_manual_requires_phone), писатель set_manual_phone"
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "помощник подписи (AccountRow, AccountLabel, label_of, build_labels), макрос components/account_label.html, load_account_rows, tests/account_label_support.py"
provides:
  - "AccountRow.phone_is_manual и AccountLabel.phone_is_manual (обязательные, без умолчания); пометка только при известном номере"
  - "load_account_rows — проекция четырёх колонок (id, type, phone, phone_is_manual)"
  - "components/account_label.html: часть <span class=\"acct-label__manual\">указан вручную</span> между номером и #id"
  - "SyncStatusView.phone_is_manual (умолчание False), заполнен во всех четырёх конструкторах get_sync_status_view; пометка переживает подмену карточки опросом"
  - "CSS: .acct-label__manual приглушена (--text-muted, nowrap), в .chip__label и .acct-head__name усекается первой (flex-shrink: 4), #id остаётся flex: none"
  - "tests/account_label_support.py: seed_account(..., manual_phone=...) через set_manual_phone и MANUAL_MARK"
affects: [18-02, 18-03]

actuals:
  tokens: 11200
  tasks: 3
  commits: 6
plan_head_before: bff2d1ea6ad2e77d69d93791743b544c510a4422
plan_head_after: 77d2d81296d6fa2661ada22e3a65a0276431577a

tech-stack:
  added: []
  patterns:
    - "Один признак вдоль всего пути: колонка → загрузчик → правило подписи → DTO опроса → макрос → CSS; список мест не перебирается (D-10)"
    - "Обязательное поле без умолчания у строки подписи: забытый конструктор падает TypeError громко, а не теряет пометку молча"
    - "Пометка живёт только в разметке (макрос); плоские формы text/plain/plain_with_id/<title>/<option>/модалка/CSV её не несут"

key-files:
  created: []
  modified:
    - app/services/account_label.py
    - app/application/accounts/labels.py
    - app/templates/components/account_label.html
    - app/application/accounts/dto.py
    - app/application/accounts/use_cases.py
    - app/pages/accounts.py
    - app/static/css/app.css
    - tests/account_label_support.py
    - tests/test_services/test_account_label.py
    - tests/test_application/test_account_label_rows.py
    - tests/test_pages/test_account_label_groups.py
    - tests/test_pages/test_account_label_accounts.py
    - tests/test_pages/test_account_label_sweep.py
    - tests/test_pages/test_responsive_markup.py

key-decisions:
  - "Признак называется phone_is_manual у AccountRow, AccountLabel и SyncStatusView — как колонка (RESEARCH §5 перевесил phone_manual из PATTERNS)"
  - "AccountRow.phone_is_manual и AccountLabel.phone_is_manual без умолчания; SyncStatusView.phone_is_manual = False (поле после полей с умолчанием)"
  - "Флаг подписи = row.phone_is_manual and shown is not None: у «Номер неизвестен» пометки нет никогда (T-18-01)"
  - "row_of читает account.phone_is_manual атрибутом без getattr-умолчания: объект без признака падает AttributeError громко"
  - "Разметка пометки — собственный класс acct-label__manual без mono (пометка — слово, не данные); приглушение правилом CSS"
  - "В CSS базовое правило .acct-label__manual стоит ДО правила усечения в однострочных контейнерах (порядок читает _css_rule по первому вхождению селектора)"

patterns-established:
  - "MANUAL_MARK = \"указан вручную\" — одна константа для тестов; номер ручным делает только seed_account(..., manual_phone=...)"
  - "Проход по экранам: _seed_world(..., manual=True), _assert_every_label_marked — пометка у КАЖДОГО вхождения data-account-label, порядок «номер → пометка»"

requirements-completed: [PHONE-08]

coverage:
  - id: D1
    description: "Ручной номер несёт пометку «указан вручную» в <h1> и <h2> экрана групп; <title> без неё; порядок номер → пометка → #id у двойника"
    requirement: "PHONE-08"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_a_manual_number_is_marked_in_both_headings_but_not_in_the_title"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_groups.py#test_a_manual_twin_reads_number_mark_then_id"
        status: pass
    human_judgment: false
  - id: D2
    description: "Правило подписи: флаг доезжает до AccountLabel; ключ двойника без флага; плоские формы без пометки; у неизвестного номера пометки нет никогда; загрузчик несёт четвёртую колонку"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_services/test_account_label.py (4 новых теста, 7 узлов)"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_account_label_rows.py#test_rows_carry_the_manual_flag"
        status: pass
    human_judgment: false
  - id: D3
    description: "Фрагмент опроса несёт пометку во всех статусах с подписью номера; пометка у каждого адреса подписи на всех экранах прохода (пользователь и админка); <title>, <option>, модалка, CSV без пометки"
    requirement: "PHONE-08"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_label_accounts.py#test_sync_status_view_carries_the_manual_flag_in_all_four_constructors"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_sweep.py#test_every_user_screen_marks_a_manual_number_at_its_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_sweep.py#test_every_admin_screen_marks_a_manual_number_at_its_label"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_label_sweep.py#test_flat_forms_of_a_manual_number_carry_no_mark"
        status: pass
    human_judgment: false
  - id: D4
    description: "Контракт CSS пометки записан и закреплён чтением таблицы стилей: приглушена, неразрывна, в однострочных контейнерах усекается раньше номера, #id не сжимается, фиксированных ширин нет"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_account_label_keeps_the_twin_id_visible_in_a_one_line_container"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_manual_mark_is_muted"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ширины 320 и 375 px: подпись с пометкой не ломает раскладку шапки экрана групп, чипа расписания и карточки; #id двойника виден рядом с пометкой"
    requirement: "PHONE-08"
    verification: []
    human_judgment: true
    rationale: "Суита читает текст CSS и не рендерит страницу; ширину доказывает только обход человеком (/gsd-verify-work 18, «Manual-Only» в 18-VALIDATION.md)"

duration: 36min
completed: 2026-11-21
status: complete
---

# Phase 18 Plan 01: Пометка «указан вручную» в подписи аккаунта Summary

**Признак `phone_is_manual` идёт от колонки через загрузчик, правило подписи и `SyncStatusView` до макроса и CSS: ручной номер несёт приглушённую пометку «указан вручную» между номером и `#id` везде, где подпись рисуется разметкой, а плоские формы и ключ двойника остались без неё.**

## Performance

- **Duration:** 36 min
- **Started:** 2026-11-21T09:34:00Z (оценка: время создания worktree; штамп старта не снят)
- **Completed:** 2026-11-21T10:12:00Z
- **Tasks:** 3 (каждая — цикл RED → GREEN)
- **Files modified:** 14 (ровно перечень `files_modified` плана; других файлов нет)

## Accomplishments

- **Трассер (задача 1):** ручной номер, поставленный писателем Фазы 16 (`seed_account(..., manual_phone="8 999 123 45 67")`), виден в обоих заголовках экрана групп как «Telegram +7 999 123-45-67 указан вручную», `<title>` без пометки; у двойника — «… указан вручную #<id>».
- **Правило подписи:** `AccountLabel.phone_is_manual` истинен только при известном номере; `_twin_key` не тронут — ручной и автоматический одинаковые номера остаются двойниками; `text`, `plain`, `plain_with_id` без пометки.
- **Фрагмент опроса (задача 2):** `SyncStatusView.phone_is_manual` во всех четырёх конструкторах; единственная правка `app/pages/accounts.py` — одна строка. Проход по 10 экранам пользователя и 6 экранам админки: пометка у КАЖДОГО вхождения подписи, `<title>`, `<option>`, тело модалки и CSV без неё.
- **Контракт CSS (задача 3):** пометка приглушена (`--text-muted`), неразрывна; в `.chip__label` и `.acct-head__name` усекается первой (`flex-shrink: 4`), `#id` остаётся `flex: none`; фиксированных ширин нет.
- **D-08 соблюдён:** ни формы, ни адреса записи, ни уведомления, ни утверждения `302`; числа гейтов не сдвинуты (`git diff` базы по файлам гейтов и `app/pages/notices.py` пуст).

## Публичный контракт для планов 18-02 и 18-03

**`app/services/account_label.py`**
- `AccountRow(NamedTuple)`: `id: int`, `type: str`, `phone: str | None`, `phone_is_manual: bool` — все четыре обязательны; `AccountRow(1, "wa", None)` падает `TypeError`.
- `AccountLabel` (frozen, slots): `account_id`, `channel`, `phone_text`, `twin`, `phone_is_manual` (пятое, обязательное). `phone_is_manual` истинно только при `phone_text is not None`; `text`/`plain`/`plain_with_id` пометки не несут.
- `row_of(account)` читает `account.id/.type/.phone/.phone_is_manual` атрибутами; объект без признака — `AttributeError`. ВАЖНО для 18-02: `set_manual_phone` пишет с `synchronize_session=False`, поэтому до `row_of(account)` нужен `await db.refresh(account)` (D-14), иначе подпись возьмёт устаревший флаг.
- `label_of(subject, rows)`, `build_labels(rows)`, `labels_for(accounts)` — сигнатуры прежние, флаг переносят.
- `app/application/accounts/labels.py::load_account_rows(session, user_id)` — `select(id, type, phone, phone_is_manual)`, одна инструкция, граница `user_id` прежняя.
- `app/application/accounts/dto.py::SyncStatusView.phone_is_manual: bool = False`; `accounts_sync_status` строит `AccountRow(account_id, view.messenger_type, view.phone, view.phone_is_manual)`.

**Вывод макроса `account_label(label, show_channel=False, with_twin_id=True)`** (только `<span>`, адрес `data-account-label="<id>"` на внешнем):

```
<span class="acct-label" data-account-label="ID">
  [<span class="acct-label__chan">Канал</span> ]                      # show_channel
  <span class="acct-label__text mono …">ТЕКСТ</span>
  [ <span class="acct-label__manual">указан вручную</span>]            # label.phone_is_manual
  [ <span class="acct-label__id mono mono--muted" data-account-id="ID">#ID</span>]   # with_twin_id и label.twin
</span>
```

Текст элемента (как его читает `label_texts`): «Telegram +7 999 123-45-67 указан вручную #12». Пометка стоит строго между номером и `#id`; у «Номер неизвестен» её нет.

**Тестовый API (`tests/account_label_support.py`)**
- `seed_account(session, user_id, type_="tg_user", *, phone=None, manual_phone=None, stored_as_is=None, status="active", account_id=None) -> int`. `manual_phone` идёт через `set_manual_phone` (он же ставит `phone_is_manual`), затем `commit`; результат `None` (очистка) — `assert`. При одновременных `phone` и `manual_phone` сначала пишется автономер, затем ручной его перезаписывает.
- `MANUAL_MARK = "указан вручную"`.
- В `tests/test_pages/test_account_label_sweep.py`: `_seed_world(db, owner_id, *, unique_type="tg_user", manual=False)` и `_assert_every_label_marked(html, name)`.

**CSS (`app/static/css/app.css`):** классы `.acct-label__manual` (базовое правило до правила усечения), `.chip__label .acct-label__manual`, `.acct-head__name .acct-label__manual`. План 18-02 вставляет форму в `data-acct-head`: контейнер `.acct-head__name` остаётся однострочным, форма в него не входит.

## Task Commits

1. **Задача 1 (трассер): ручной номер из колонки до пометки в шапке экрана групп**
   - RED: `3a458b82` (test) — 10 красных узлов, трассер упал на утверждении об отсутствии пометки
   - GREEN: `f3c959d3` (feat)
2. **Задача 2: фрагмент опроса и проход по всем экранам**
   - RED: `2f4377b9` (test) — 18 красных узлов
   - GREEN: `b9073138` (feat)
3. **Задача 3: контракт CSS пометки**
   - RED: `c695d0e0` (test) — 3 красных узла, `ValueError: substring not found`
   - GREEN: `77d2d812` (feat)

**Метаданные плана:** коммит `docs(18-01): …` с этим файлом.

## RED / GREEN / REFACTOR (улики)

Улики RED лежат под `.pytest_cache/gsd-red/` (вне git): `task{1,2,3}.xml` (JUnit), `task{1,2,3}.record.json`, `task{1,2,3}.out`. Каждая запись прошла `gsd_run check tdd-red-evidence` с вердиктом `RED_EVIDENCE_OK` (`target_test_failed`).

- **Задача 1.** Цель: `tests/test_pages/test_account_label_groups.py::test_a_manual_number_is_marked_in_both_headings_but_not_in_the_title`. Итог: `10 failed, 54 passed`. Строки `FAILED …` — 7 узлов `test_services/test_account_label.py`, `test_rows_carry_the_manual_flag`, оба теста экрана групп. Литерал: `TypeError: AccountRow.__new__() takes 4 positional arguments but 5 were given` (8 узлов) и `AssertionError: оба заголовка экрана групп обязаны нести пометку после номера` (трассер: `'Telegram +7 999 123-45-67' != '… указан вручную'`). Семантическая оценка: целевой узел упал на планируемом утверждении, не на ошибке сбора. GREEN: те же файлы `64 passed`; широкий прогон `tests/test_templates tests/test_services tests/test_application tests/test_models tests/test_repositories tests/test_scripts` — `2230 passed`.
- **Задача 2.** Цель: `…test_account_label_accounts.py::test_sync_status_view_carries_the_manual_flag_in_all_four_constructors[active]` (классификатору нужно уникальное имя узла — берётся один параметр). Итог: `18 failed, 59 passed`. Литерал: `AttributeError: 'SyncStatusView' object has no attribute 'phone_is_manual'` (4 узла) и `/accounts/7311/sync-status 500` у случаев `sync-status-*` (см. отклонение 1). GREEN: четыре `<automated>` задачи — `77`, `172`, `1161`, `199 passed`.
- **Задача 3.** Цель: `tests/test_pages/test_responsive_markup.py::test_account_label_keeps_the_twin_id_visible_in_a_one_line_container`. Итог: `3 failed, 1 passed`; литерал `ValueError: substring not found`. GREEN: `4 passed` по `-k`, широкий прогон `test_responsive_markup + test_shell + test_templates` — `812 passed`.
- **REFACTOR:** не было (чистого рефакторинга нет, коммитов `refactor(18-01)` нет).

Мутационный контроль охранного теста: временно дописанная пометка в `AccountLabel.plain` краснит `test_flat_forms_of_a_manual_number_carry_no_mark` (`<title>: плоская форма несёт пометку`); правка откатана `git checkout -- app/services/account_label.py`, в коммит не попала. `test_flat_forms_…` на этапе RED уже зелёный (охранный тест нового свойства «плоские формы без пометки», которое до задачи выполнялось само); от вакуума его держат положительные контроли в самом тесте (мир ручной, номер в плоских формах есть).

## TDD Gate Compliance

Для каждой из трёх задач есть `test(18-01): …`, затем `feat(18-01): …` (потомок RED): порядок `3a458b82 → f3c959d3`, `2f4377b9 → b9073138`, `c695d0e0 → 77d2d812`. Нарушений нет.

## Числа рядом с базой (`baseline-p18.log`)

| Набор | База (bff2d1ea) | Итог (77d2d812) | Разница |
|---|---|---|---|
| compileall | rc=0 | rc=0 | — |
| `prohibitions_census.py --check` | 965 строк, согласие, rc=0 | 965 строк, согласие, rc=0 | 0 |
| гейты номера Фазы 16 (3 файла) | 1161 passed | 1161 passed | 0 |
| сквозные гейты (команда note 8: `tests/test_templates` + htmx_gates + htmx_post_pairs + declared_invariants + impersonation_gate + notices_registry) | 594 passed без двух последних файлов (база); 30 passed у impersonation_gate + notices_registry | 624 passed целиком (594 + 30); 30 passed у пары | 0 после учёта состава набора |
| тесты правила и загрузчика (`test_account_label.py`, `test_account_label_rows.py`) | 48 passed | 56 passed | +8 (7 правило, 1 загрузчик) |
| страницы подписи (accounts, groups, history, admin, admin_history, sweep) | 85 passed | 108 passed | +23 (4 + 2 + 17) |
| `tests/test_pages/test_responsive_markup.py` | 145 passed | 146 passed | +1 (`test_the_manual_mark_is_muted`) |
| `tests/test_pages/test_admin_panel.py` + `test_shell.py` + `test_phone_writer_runtime_guard.py` | — | 458 passed | (в базе не мерялось) |
| сбор тестов `--collect-only` | 5954 | 5986 | +32 = 8 + 23 + 1 |

Объявленные числа гейтов D-08 не сдвинуты: `WRITE_FORM_PLACES` 49 (`tests/test_templates` зелены), `MUTATING_ROUTE_COUNT` 49, `MUTATING_MODULE_COUNT` 14, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 25, `PUSH_URL_DECISIONS_DECLARED` 37, `PAIRED_302_ASSERTIONS_DECLARED` 191, `POST_PAIR_CASES_DECLARED` 77, реестр уведомлений 19 кодов; `git diff --stat bff2d1ea..HEAD -- tests/test_pages/test_impersonation_gate.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_notices_registry.py app/pages/notices.py` пуст.

`tests/test_planning` — гонялась один раз после коммита SUMMARY, результат в сообщении возврата оркестратору.

## Decisions Made

См. `key-decisions` во frontmatter: имя `phone_is_manual`, обязательные поля без умолчания, флаг только при известном номере, `row_of` без `getattr`, отдельный класс пометки, порядок правил CSS.

## Deviations from Plan

### Auto-fixed / замеренные отличия

**1. [Plan vs measured] Промежуточное состояние между GREEN задач 1 и 2**
- **Найдено в:** RED задачи 2.
- **Суть:** после `f3c959d3` (GREEN задачи 1) строка `accounts_sync_status` (`app/pages/accounts.py:1051`) ещё строила `AccountRow` из трёх аргументов, и маршрут `/accounts/{id}/sync-status` отвечал 500 (`TypeError`) до `b9073138`. Вне двух файлов scope_note красными стали 11 узлов `tests/test_pages` (5 в `test_account_label_accounts.py`, 6 в `test_account_label_sweep.py`), потому что `<verify>` задачи 1 не включает `tests/test_pages` кроме экрана групп, а scope_note мерил каталоги без `test_pages`. Починить в задаче 1 нельзя: поле `SyncStatusView.phone_is_manual`, которое строка читает, входит в задачу 2.
- **Исход:** на итоговом дереве красных нет; коммит `f3c959d3` сам по себе не доставлять отдельно от `b9073138` (одна ветка, один merge). Правило «иных красных нет — остановиться» scope_note читал про прогон задачи 1; замер показал, что граница шире.
- **Коммиты:** `f3c959d3`, `b9073138`.

**2. [Plan vs measured] Причинный литерал RED задачи 1**
- План называл литерал `TypeError` и для трассера. Замер: трассер падает на утверждении (`AssertionError`: пометки в заголовках нет), `TypeError` у семи узлов правила и загрузчика. Трассер сильнее: упал именно из-за отсутствия поведения, а не конструкторов.

**3. [Plan vs measured] Узел цели RED задачи 2**
- Верб RED-улики не принимает имя параметризованного теста без параметра (`no_target_test_failure`); запись собрана на `…[active]`.

**4. [Rule 1 - порядок CSS] Базовое правило перед правилом усечения; одно правило для флагов усечения**
- **Найдено в:** задача 3, GREEN.
- **Суть:** `_css_rule(css, ".acct-label__manual")` берёт первое вхождение селектора, в том числе внутри `.chip__label .acct-label__manual`; базовое правило с `color` стоит выше правила усечения. Для `flex-shrink: 4` вместо двух отдельных правил (усечение + flex-shrink) сделано одно правило на оба селектора контейнеров с четырьмя объявлениями усечения и `flex-shrink: 4` — иначе чтение первого вхождения не видит `flex-shrink`.
- **Файлы:** `app/static/css/app.css`. **Коммит:** `77d2d812`.

**5. [Rule 2 - усиление] Проекция загрузчика проверяется по четырём колонкам**
- `test_the_statement_reads_only_three_columns` переименован в `…four_columns`, цикл колонок дополнен `phone_is_manual`; утверждения не ослаблены. **Коммит:** `f3c959d3`.

### Подмены механики (не отклонения от плана)

- Журнал плана (`gsd-plan-head-before-18-01`) лежит в `.pytest_cache/`, не в `.git/worktrees/…`: песочница отказала в записи по общему пути гита, а составные `git`-команды отклонялись; база — SHA `bff2d1ea6ad2e77d69d93791743b544c510a4422`, взятый при старте (она же `plan_head_before`). Сентинел `gsd-spawn-toplevel` не писался; смещение cwd контролировалось тем, что все команды шли из корня worktree.
- `commits: 6` измерено `git rev-list --count bff2d1ea..HEAD` до коммита SUMMARY.
- Записи RED собирал `.pytest_cache/checks/mkred.py` (вместо ручного JSON), прогоны — скриптами `.pytest_cache/checks/*.sh` под общим замком `flock …/pytest.lock`.
- `graphify update .` не запускался (графа в worktree нет; граф пересобирает оркестратор после слияния). Полная суита (`just test`) не гонялась — её гоняет посмертный гейт оркестратора.

**Итого отклонений:** 5 (1 промежуточное состояние ветки, 2 замера RED, 1 порядок CSS, 1 усиление теста). **Влияние:** на итоговом дереве поведение и числа гейтов — как в плане; scope не расширен.

## Authentication Gates

Нет.

## Issues Encountered

Нет неразрешённых. Не создавался `deferred-items.md`; отложенного нет.

## Known Stubs

Нет: заглушек, пустых значений, текстов «скоро» в изменённых файлах нет. `SyncStatusView.phone_is_manual = False` — осознанное умолчание поля DTO (его заполняют все четыре конструктора, закреплено тестом), не заглушка.

## Threat Flags

Нет: новых сетевых адресов, путей аутентификации, доступа к файлам и схемы на границе доверия план не добавил. T-18-01 (пометка у «Номер неизвестен») закрыт `test_a_flag_without_a_number_never_marks_the_unknown_label`; T-18-02 — граница `WHERE user_id` загрузчика не менялась, добавлена колонка; T-18-03 — пометка статичный текст шаблона, `test_templates` зелены.

## Next Phase Readiness

- Планы 18-02 и 18-03 опираются на контракт выше. Для 18-02: после записи `set_manual_phone` — `commit`, `db.refresh(account)`, затем `load_account_rows` и `label_of(row_of(account), rows)`; подпись в ответе (`<h2>`, `<h1>`) рисует макрос, пометка появится сама.
- Ручная половина критерия 1 и края boundary (320 и 375 px) остаётся человеку: `/gsd-verify-work 18`.

## Self-Check: PASSED

- Файлы из `key-files.modified` существуют (проверено `ls`); новых файлов у плана нет.
- Коммиты `3a458b82`, `f3c959d3`, `2f4377b9`, `b9073138`, `c695d0e0`, `77d2d812` — предки HEAD.
- Приёмочные счётчики: `phone_is_manual` в `account_label.py` — 10 (≥4); `MessengerAccount.phone_is_manual` в `labels.py` — 1; `acct-label__manual` в макросе — 2 (≥1), в `app.css` — 3 (≥3); `manual_phone` в `tests/account_label_support.py` — 8 (≥2); `phone_is_manual: bool = False` в `dto.py` — 1; `phone_is_manual=account.phone_is_manual` в `use_cases.py` — 4; `view.phone_is_manual` в `accounts.py` — 1, изменена одна строка; `"chan", "text", "manual"` в `test_responsive_markup.py` — 2.

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-21*
