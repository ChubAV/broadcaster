---
phase: 18-ruchnaya-pravka-nomera
plan: 03
subsystem: ui
tags: [phone, manual-edit, account-card, link, jinja, tdd, tracer]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "ключ acct_label во всех трёх шаблонах карточки аккаунта, поле phone_text («Номер неизвестен» = None)"
  - phase: 18-ruchnaya-pravka-nomera
    provides: "план 18-02: форма номера на /accounts/{id}/groups, контейнер #acct-phone [data-acct-phone], поле id=phone (якорь D-12), маршрут POST /accounts/{id}/phone"
provides:
  - "Ссылка «Указать номер» / «Изменить» на /accounts/{id}/groups#phone в девяти местах трёх синхронных копий карточки аккаунта (страница, порция, фрагмент опроса; по три ветки статуса)"
  - "tests/test_pages/test_account_phone_links.py: разбор phone_link_texts(html, account_id), адресные тесты трёх путей и трёх статусов, сквозной переход к полю, счёт ссылок по трём исходникам"
affects: [verify-work-18]

actuals:
  tokens: 6200
  tasks: 2
  commits: 4
plan_head_before: f194506a95b43aa44bf91f02b89a2aa8375b9024
plan_head_after: df8a679e0e7e1a0b9ecec7ca0497902460fd688c

tech-stack:
  added: []
  patterns:
    - "Вход к правке номера — ссылка GET (link_button, ghost) рядом с входом в группы, а не форма: числа сквозных гейтов формы и маршрута не двигаются"
    - "Слово ссылки выбирает уже имеющаяся подпись: 'Изменить' if acct_label.phone_text else 'Указать номер'; ключей контекста и правок обработчиков нет"
    - "Синхронность трёх копий карточки держит счёт по исходникам: по три вхождения /groups#phone и по три слова в каждом из трёх файлов; в комментариях шаблонов адрес ссылки и её слова дословно не повторяются"

key-files:
  created:
    - tests/test_pages/test_account_phone_links.py
  modified:
    - app/templates/accounts/list.html
    - app/templates/accounts/partial_cards.html
    - app/templates/accounts/partials/sync_status_card.html

key-decisions:
  - "Ссылка стоит сразу после «Настроить группы» в .acct-card__actions каждой ветки (решение из Claude's Discretion, scope_note плана): оба входа ведут на один экран и лежат рядом"
  - "Ветки syncing и sync_failed ссылку НЕ прячут: у синхронизирующегося аккаунта номер без входа остался бы недоступным"
  - "Во фрагменте опроса адрес собирается из account_id (объекта account у фрагмента нет), слово — из acct_label.phone_text, который обработчик опроса передаёт всегда"
  - "Счёт по исходникам проверяет и слово «Изменить» (по три на файл) сверх требуемого планом — в трёх файлах оно больше нигде не встречается"

requirements-completed: [PHONE-09]

coverage:
  - id: D1
    description: "Карточка страницы /accounts во всех трёх ветках статуса (syncing, sync_failed, прочие) несёт ссылку к полю номера: «Указать номер» без номера, «Изменить» с номером"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_every_page_card_links_to_the_phone_field_with_the_right_word"
        status: pass
    human_judgment: false
  - id: D2
    description: "Порция подгрузки /accounts/partial несёт ту же ссылку во всех трёх ветках статуса"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_every_partial_card_links_to_the_phone_field_with_the_right_word"
        status: pass
    human_judgment: false
  - id: D3
    description: "Фрагмент опроса /accounts/{id}/sync-status (статусы active, syncing, sync_failed) несёт ту же ссылку, адрес из account_id; чужой аккаунт — «Аккаунт не найден» без ссылки"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_every_poll_fragment_links_to_the_phone_field_with_the_right_word"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_a_foreign_account_poll_draws_no_phone_link"
        status: pass
    human_judgment: false
  - id: D4
    description: "Переход по ссылке (адрес без якоря) открывает экран групп того же аккаунта: ровно одно поле id=phone внутри [data-acct-phone], форма пишет в /accounts/{id}/phone этого аккаунта; в адресе ссылки номера нет"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_the_phone_link_lands_on_the_phone_field_of_the_same_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_phone_links.py#test_the_phone_link_carries_no_number"
        status: pass
    human_judgment: false
  - id: D5
    description: "Три копии карточки синхронны по ссылке: по три вхождения /groups#phone, «Указать номер» и «Изменить» в каждом из трёх исходников"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_links.py#test_three_card_sources_carry_the_phone_link_three_times_each"
        status: pass
    human_judgment: false
  - id: D6
    description: "Числа сквозных гейтов D-08 не сдвинуты (ссылка — не форма): все восемь названных чисел и реестр уведомлений равны значениям после 18-02; git diff --stat по файлам гейтов пуст"
    requirement: "PHONE-09"
    verification:
      - kind: integration
        ref: "wave gate command плана (2472 passed), tests/test_templates + gates cross-cutting (626 passed), phone gates (1161 passed), prohibitions_census.py --check (965 rows, rc=0), compileall rc=0"
        status: pass
    human_judgment: false
  - id: D7
    description: "Ручная половина: ссылка прокручивает экран групп к полю номера; ряд действий карточки с тремя-четырьмя элементами («Настроить группы», ссылка к номеру, «Повторить», «Удалить») не ломается на 320 и 375 px; ссылка есть и в карточке, пришедшей опросом"
    requirement: "PHONE-09"
    verification: []
    human_judgment: true
    rationale: "Прокрутку к якорю и перенос ряда кнопок суита не исполняет — она не рендерит страницу в браузере (/gsd-verify-work 18, «Manual-Only» в 18-VALIDATION.md); серверная половина — адрес, слово, владение — закреплена тестами D1–D5"

duration: 33min
completed: 2026-11-21
status: complete
---

# Phase 18 Plan 03: Ссылка к полю номера на карточке аккаунта Summary

**Ссылка «Указать номер» / «Изменить» на `/accounts/{id}/groups#phone` стоит в девяти местах трёх синхронных копий карточки аккаунта (страница, порция, фрагмент опроса — по три ветки статуса), слово выбирает `acct_label.phone_text`, номера в адресе нет, а ни одно число сквозных гейтов не сдвинулось.**

## Performance

- **Duration:** 33 min
- **Started:** 2026-11-21T13:00:00Z (первый прогон RED — 13:02)
- **Completed:** 2026-11-21T13:33:00Z (до коммита этого файла)
- **Tasks:** 2 (задача 1 — трассер, один цикл RED → GREEN; задача 2 — RED → GREEN для порции, фрагмента опроса и счёта по исходникам)
- **Files modified:** 4 (ровно `files_modified` плана: три шаблона и один новый тестовый модуль)

## Accomplishments

- **Трассер (задача 1):** на `/accounts` у карточки любого статуса стоит ссылка к полю номера, слово — по наличию номера; переход по ссылке (адрес без якоря) отвечает 200 экраном групп того же аккаунта с одним полем `id="phone"` внутри `[data-acct-phone]` и формой на `/accounts/{id}/phone`; в `href` номера нет.
- **Порция и фрагмент опроса (задача 2):** та же ссылка посимвольно в `accounts/partial_cards.html` и `accounts/partials/sync_status_card.html` (во фрагменте адрес из `account_id`, объекта `account` у него нет). Обработчики не менялись.
- **Чужой аккаунт:** опрос чужого аккаунта отвечает «Аккаунт не найден» без единой ссылки правки номера (T-18-16).
- **Синхронность:** новый счёт по исходникам краснеет, если в любой из трёх копий ссылок не три.
- **Бюджет гейтов (D-08):** ни одного сдвига; числа и пустой `git diff --stat` — ниже.

## Где стоит ссылка (для верификатора фазы)

| Путь отрисовки | Файл | Ветки статуса, несущие ссылку |
|---|---|---|
| `/accounts` (первая отрисовка) | `app/templates/accounts/list.html` | `syncing`, `sync_failed`, прочие (`active`, `disconnected`, неизвестный статус) |
| `/accounts/partial` (порция подгрузки) | `app/templates/accounts/partial_cards.html` | те же три |
| `/accounts/{id}/sync-status` (фрагмент опроса) | `app/templates/accounts/partials/sync_status_card.html` | `active`, `sync_failed`, `syncing` — все статусы, для которых обработчик вообще рисует карточку (прочие статусы, например `connecting`, обработчик отдаёт пустым ответом, карточки и, значит, ссылки нет) |

Слово ссылки — `'Изменить' if acct_label.phone_text else 'Указать номер'`; во всех ветках ссылка стоит сразу после «Настроить группы» в `.acct-card__actions`, тем же `link_button(..., variant='ghost')`. У ветки `sync_failed` в ряду теперь четыре элемента («Настроить группы», ссылка, «Повторить», «Удалить»), у остальных три.

## Ведомость чисел гейтов D-08: до → после

Каждое число прочитано из файла на дереве `df8a679e` (`grep` по объявлению); база — значения после 18-02 из заметки оркестратора и из `18-02-SUMMARY.md`.

| Гейт | Константа / реестр | До (после 18-02) | После |
|---|---|---|---|
| `tests/test_templates/test_form_inventory.py` | `WRITE_FORM_PLACES` | 50 | 50 |
| `tests/test_pages/test_impersonation_gate.py` | `MUTATING_ROUTE_COUNT` | 50 | 50 |
| там же | `MUTATING_MODULE_COUNT` | 14 | 14 |
| `tests/test_pages/test_htmx_gates.py` | `FRAGMENT_RESPONSE_HANDLERS_DECLARED` | 26 | 26 |
| там же | `PUSH_URL_DECISIONS_DECLARED` | 38 | 38 |
| `tests/test_pages/test_htmx_post_pairs.py` | `PAIRED_302_ASSERTIONS_DECLARED` | 193 | 193 |
| там же | `POST_PAIR_CASES_DECLARED` | 79 | 79 |
| `app/pages/notices.py` + `test_notices_registry.py` | записей `Notice(` в реестре / `DECLARED_CODES` | 21 | 21 |

`git diff --stat f194506a95b43aa44bf91f02b89a2aa8375b9024..HEAD -- tests/test_templates/test_form_inventory.py tests/test_pages/test_impersonation_gate.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_notices_registry.py app/pages/notices.py` — **пуст** (0 строк). Полный `git diff --stat БАЗА..HEAD` называет ровно четыре файла плана: три шаблона и `tests/test_pages/test_account_phone_links.py`. Порядковые ключи `ModalTrigger("acc-del-", …)` не сдвинулись (`tests/test_templates` зелёные).

## Числа рядом с базой

| Набор | База (по заметке оркестратора / 18-02) | Итог (`df8a679e`) | Разница |
|---|---|---|---|
| сквозные гейты (команда заметки 8: `test_templates` + `test_htmx_gates` + `test_htmx_post_pairs` + `test_declared_invariants` + `test_impersonation_gate` + `test_notices_registry`) | 626 passed | 626 passed | 0 |
| гейты номера Фазы 16 (privacy + parity + single-writer) | 1161 passed | 1161 passed | 0 |
| `tests/test_pages/test_responsive_markup.py` | 147 (146 + 1 от 18-02; отдельным прогоном на базе не снималось) | 147 passed | 0 (файл в diff не входит) |
| `prohibitions_census.py --check` | 965 строк, rc=0 | 965 строк, биекция с переписью — согласие, rc=0 | 0 (плана нет строк реестра) |
| `compileall -q app main.py tests` | rc=0 | rc=0 | — |
| новый `tests/test_pages/test_account_phone_links.py` | — | 24 passed | +24 |
| команда 1 `<verify>` задач 1 и 2 (`test_account_phone_links.py`) | — | 8 passed после задачи 1; 24 passed после задачи 2 | — |
| команда 2 `<verify>` задачи 1 (`test_templates` + `test_responsive_markup` + `test_account_label_accounts`) | — | 585 passed | — |
| команда 2 `<verify>` задачи 2 (+ `test_account_label_sweep` + `test_routes/test_wa_sync_status`) | — | 647 passed | — |
| команда 3 `<verify>` задачи 2 (шесть гейтов + три гейта номера) | — | 1362 passed | — |
| гейтовая команда волны плана (`<verification>`, 17 путей) | — | 2472 passed (10 мин 45 с) | — |
| `tests/test_planning` | 218 passed, 2 skipped | после коммита этой сводки — в сообщении возврата | — |

## Task Commits

1. **Задача 1 (трассер): ссылка на странице `/accounts`**
   - RED: `13fea817` (test) — 8 красных узлов
   - GREEN: `f64d05a2` (feat) — `accounts/list.html`
2. **Задача 2: порция и фрагмент опроса, счёт по исходникам**
   - RED: `55539548` (test) — 14 красных узлов
   - GREEN: `df8a679e` (feat) — `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`

**Метаданные плана:** коммит `docs(18-03): …` с этим файлом.

## RED / GREEN / REFACTOR (улики)

Улики лежат под `.pytest_cache/gsd-red/` (вне git): `task1.{xml,record.json,out}`, `task2.{xml,record.json,out}`. Обе записи прошли `gsd_run check tdd-red-evidence` вердиктом `RED_EVIDENCE_OK` (`target_test_failed`).

- **Задача 1.** Цель: `test_every_page_card_links_to_the_phone_field_with_the_right_word[with_number-active]`. Три совпадения: `FAILED tests/test_pages/test_account_phone_links.py::test_every_page_card_links_to_the_phone_field_with_the_right_word[with_number-active]` (и пять соседей), итог `8 failed`, причинный литерал `assert [] == ['Изменить']` (и `assert [] == ['Указать номер']` у параметров без номера). Остальные два красных узла — переход (`на странице нет ссылки на /accounts/2/groups#phone`) и «ровно одна ссылка» (`[] == ['/accounts/1/groups#phone']`) — упали по той же причине: ссылки нет. Семантическая оценка: цель упала на утверждении планируемого поведения (ссылка отсутствует на карточке при отрисованной странице, ответ 200), а не на ошибке сбора, импорта или фикстуры. GREEN: `8 passed`.
- **Задача 2.** Цель: `test_every_partial_card_links_to_the_phone_field_with_the_right_word[with_number-active]`. Три совпадения: `FAILED tests/test_pages/test_account_phone_links.py::test_every_partial_card_links_to_the_phone_field_with_the_right_word[with_number-active]` (и 13 соседей: 5 порции, 6 фрагмента опроса, 2 счёта по исходникам), итог `14 failed, 10 passed`, причинный литерал `assert [] == ['Изменить']`. Десять зелёных — тесты задачи 1 и защитный `test_a_foreign_account_poll_draws_no_phone_link` (он утверждает отсутствие ссылки и зелёный до правки по построению; его мутационная сила — следующий абзац). Семантическая оценка: цель упала на планируемом утверждении, ответ порции 200. GREEN: `24 passed`.
- **REFACTOR:** не было (чистого рефакторинга нет, коммитов `refactor(18-03)` нет).

**Про защитный тест чужого аккаунта.** Он зелёный до GREEN и ожидаемо остаётся зелёным после: его утверждение — отсутствие ссылки в ответе «Аккаунт не найден». Защиту от вакуума несёт утверждение `"Аккаунт не найден" in html` (ответ именно отказа, а не карточки) и связка с `test_every_poll_fragment_links_…`, который доказывает, что парсер ссылки находит ссылку во фрагменте опроса (иначе пустой список чужого ответа ничего бы не значил).

## TDD Gate Compliance

Для обеих задач `test(18-03): …`, затем `feat(18-03): …` — потомок RED: порядок `13fea817 → f64d05a2`, `55539548 → df8a679e`. Нарушений порядка нет; `git log --grep` по темам `test(18-03)` / `feat(18-03)` находит ровно по два коммита каждого вида.

## Decisions Made

См. `key-decisions` во frontmatter. Главное: ссылка — GET рядом с «Настроить группы» во всех ветках статуса, без формы и без новых ключей контекста; слово — по `acct_label.phone_text`; во фрагменте опроса адрес из `account_id`.

## Deviations from Plan

### Auto-fixed / замеренные отличия

**1. [Plan vs measured] Узел цели RED — один параметр, имя без пути файла**
- Верб RED-улики не принимает имя параметризованного теста без параметра, а полный путь `файл::тест[параметр]` отклоняет как `no_target_test_failure` (при том что узел есть в `failing_tests`): классификатор ищет имя в форме `тест[параметр]`. Запись собрана на `test_every_…[with_number-active]`, как у 18-01 и 18-02 (там — по параметру).

**2. [Дополнение к плану] Счёт по исходникам проверяет и слово «Изменить»**
- План требует по три вхождения `/groups#phone` и `Указать номер`. Тест дополнен счётом «Изменить» (по три): замер показал, что в трёх файлах это слово больше нигде не стоит, поэтому счёт не даёт ложных срабатываний, а потеря слова в одной ветке видна сразу.

**3. [Дополнение к плану] Разбор тестового модуля ищет поле внутри контейнера**
- Сквозной тест перехода сверяет не только наличие `data-acct-phone` и `id="phone"` (как в плане), но и вложенность поля в контейнер и `action` охватывающей формы — так «якорь попал в поле формы того же аккаунта» утверждается, а не предполагается.

**Итого отклонений:** 3 (1 механика верба улики, 2 усиления проверки без изменения объёма). **Влияние:** поведение и числа гейтов — как в плане; `files_modified` не расширен.

### Подмены механики (не отклонения от плана)

- Журнал плана (`plan-head-before-18-03`) лежит в `.pytest_cache/checks/`, не в `.git/…`: составные `git`-команды песочница отклоняет (как у 18-01 и 18-02); база — SHA `f194506a95b43aa44bf91f02b89a2aa8375b9024`, взятый при старте (он же `plan_head_before`). Сентинел `gsd-spawn-toplevel` не писался; смещение cwd контролировалось тем, что все команды шли из корня worktree.
- Прогоны pytest — через `.pytest_cache/checks/pt.sh` под общим замком `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`; ожидание длинных прогонов — `flock -w … true`. Запись RED-улики собирает `.pytest_cache/checks/mkrec.py` (поля camelCase, вывод — JUnit XML).
- `graphify update .` не запускался (графа в worktree нет; граф пересобирает оркестратор после слияния). Полная суита (`just test`) не гонялась — её гоняет посмертный гейт оркестратора; вместо неё — гейтовая команда волны плана (2472 passed), набор заметки 8, гейты номера, `test_planning`.
- `commits: 4` измерено `git rev-list --count f194506a..HEAD` до коммита этой сводки.

## Authentication Gates

Нет.

## Issues Encountered

Нет. `deferred-items.md` не создавался; отложенного нет. Плановых записей (STATE.md, ROADMAP.md, REQUIREMENTS.md, реестр запретов) не правилось: orchestrator владеет ими.

## Known Stubs

Нет: заглушек, пустых значений, текстов «скоро» в изменённых файлах нет.

## Threat Flags

Нет: новых сетевых адресов, путей аутентификации и файловых доступов нет — ссылка GET на уже существующий экран; границы доверия целиком названы в `<threat_model>` плана (T-18-15 закрыт тестом `test_the_phone_link_carries_no_number`, T-18-16 — `test_a_foreign_account_poll_draws_no_phone_link`).

## Для `/gsd-verify-work 18` (ручная половина, `human_judgment`)

Суита не исполняет браузер, поэтому человеку остаётся (ранее объявлено в `18-VALIDATION.md`, «Manual-Only»):

1. На `/accounts` нажать «Указать номер» у аккаунта без номера и «Изменить» у аккаунта с номером: открывается экран групп этого аккаунта и страница **прокручена к полю номера** (якорь `#phone`).
2. Карточка в статусе синхронизации после подмены опросом (`syncing` → смена статуса) несёт ссылку и после подмены.
3. Ряд действий карточки (особенно `sync_failed`: «Настроить группы», ссылка к номеру, «Повторить», «Удалить») **переносится без обрезки** на ширинах 320 и 375 px.

Машинную улику обхода записывать разделом улики, отметки и `result` оставлять человеку.

## Next Phase Readiness

- План 18-03 — последний план Фазы 18; дальше фазовый верификатор по PHONE-08…11 и критериям ROADMAP, затем `/gsd-verify-work 18` для ручной половины (критерии 1 и 2: прокрутка к полю, подмена шапки/заголовков/вкладки с JS, ширины 320 и 375 px, автозаполнение браузера).
- Число сквозных гейтов фаза оставляет на значениях после 18-02.

## Self-Check: PASSED

- Созданный файл существует: `tests/test_pages/test_account_phone_links.py`.
- Коммиты `13fea817`, `f64d05a2`, `55539548`, `df8a679e` — предки HEAD.
- Приёмочные счётчики: `/groups#phone` в `accounts/list.html`, `partial_cards.html`, `partials/sync_status_card.html` — по 3; `Указать номер` в `list.html` — 3; `acct_label.phone_text` в `sync_status_card.html` — 4 (≥3); `git diff --stat БАЗА..HEAD` по файлам гейтов и `app/pages/notices.py` — пуст.

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-21*
