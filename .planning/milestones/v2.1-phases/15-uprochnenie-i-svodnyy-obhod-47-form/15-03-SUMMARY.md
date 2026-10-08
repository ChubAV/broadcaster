---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 03
subsystem: testing
tags: [pytest, ast, htmx, alpine, degradation, gate, GATE-10]

requires:
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: "идиома пар SP-3 и прохибиция плана 09-03 #0 (GATE-06 не переименовывается)"
  - phase: 10-rychag-components-modal-html
    provides: "панель подтверждения `modal()` с формой `hx-post` = `action`"
provides:
  - "гейт `tests/test_templates/test_degradation_pairs.py`: предикат пары объявлен до первого числа, счёт пар по записанному ключу предмета"
  - "пять новых `*_degrades_without_htmx` — по одному к каждому `*_degrades_without_alpine`, в том же файле сразу после пары"
  - "три границы разборщика названы в докстринге и закрыты правилами-запретами с контролями от вакуума"
affects: [15-09, 15-14, GATE-10, "критерий 4 ROADMAP Фазы 15"]

actuals:
  tokens: 13900
  tasks: 3
  commits: 4
plan_head_before: 02827604ada8b041eba2f26c9f2c1d31c399001f

tech-stack:
  added: []
  patterns:
    - "ключ предмета теста записан полем (`DegradationSubject`), а не выведен из имени"
    - "гейт суиты о себе разбирает `tests/**/*.py` через `ast` по поданному отображению «путь → исходник»"
    - "правило-запрет на каждую границу разборщика + синтетический исходник в памяти как контроль от вакуума"

key-files:
  created:
    - tests/test_templates/test_degradation_pairs.py
  modified:
    - tests/test_pages/test_billing_section.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_ads_editor.py

key-decisions:
  - "Предикат пары — совпадение записанного ключа предмета (экран, действие) при разных механизмах; паритет счёта (2) и совпадение основы (5) отвергнуты с замером"
  - "Ключ предмета = (страница, изменяющий маршрут); замер уточнил контрпример: у editor_delete_form и editor_delete экран ОДИН, различается ДЕЙСТВИЕ"
  - "Новые htmx-тесты смотрят на форму ПАНЕЛИ ПОДТВЕРЖДЕНИЯ (единственную с hx-post), поэтому основа их имён не совпадает с alpine-парой, а пару держит ключ"
  - "Маркер planning на гейт не ставится: предмет — суита о себе, не запись проекта"

patterns-established:
  - "Гейт пар: число пар объявлено константой с летописью и поставлено прогоном покрасневшего правила"
  - "Невидимая разборщику форма запрещается отдельным правилом (приём второго уровня)"

requirements-completed: [GATE-10]

coverage:
  - id: D1
    description: "Предикат пары объявлен в докстринге выше первого числа и первого теста; перечни литералами с отдельно утверждаемыми числами; изъятия и непарные с причиной"
    requirement: GATE-10
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_degradation_pairs.py -q -p no:randomly (15 passed)"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_degradation_pairs.py -q -p no:randomly -k 'control or false_pair' (4 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять новых *_degrades_without_htmx по совпадающему ключу предмета; в трёх правимых файлах только добавления"
    requirement: GATE-10
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_billing_section.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_ads_editor.py -q -p no:randomly -k degrades_without_htmx (5 passed)"
        status: pass
      - kind: integration
        ref: "те же три файла целиком: 253 passed (до задачи 248)"
        status: pass
      - kind: other
        ref: "git show --format= --unified=0 0203202f -- <три файла> | grep -cE '^-[^-]' → 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Три границы разборщика названы в докстринге и закрыты правилами-запретами; полнота изъятий утверждена машинно"
    requirement: GATE-10
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_degradation_pairs.py -q -p no:randomly -k 'boundary or cannot_see or exemptions_are_complete' (3 passed)"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_templates/ -q -p no:randomly (275 passed, порог 236)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Верность объявленных ключей предмета (что каждый тест действительно проверяет названный экран и действие)"
    verification: []
    human_judgment: true
    rationale: "Гейт утверждает ПОЛНОТУ и НЕПРОТИВОРЕЧИВОСТЬ ключей, но не их верность — это человеческое суждение по тексту каждого теста; так и записано в абзаце «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ»"

duration: 22min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 03: Предикат пары и пять недостающих `*_degrades_without_htmx` Summary

**Гейт `test_degradation_pairs.py` считает ПАРЫ по записанному ключу предмета `(экран, действие)`, объявленному до первого числа; к каждому из пяти alpine-тестов добавлен htmx-тест того же предмета (0 → 5 пар), ни одно существующее имя не тронуто, три границы разборщика закрыты правилами-запретами.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-24T07:06:30Z
- **Completed:** 2026-09-24T07:28:35Z
- **Tasks:** 3
- **Files modified:** 4 (1 создан, 3 дополнены)

## Объявленный предикат пары (дословно, из докстринга гейта)

> **Пара** — два теста, объявившие ОДИН И ТОТ ЖЕ ключ предмета `(экран, действие)` и
> деградирующие РАЗНЫЕ клиентские механизмы: один `*_degrades_without_alpine`, другой
> `*_degrades_without_htmx`.

Отвергнутые чтения, с числами:
- **паритет счёта** (`count(htmx) >= count(alpine)`) — «не хватает 2»; парность не измеряет:
  две функции любого предмета сделали бы его зелёным при нуле точных пар;
- **совпадение основы имени** — «не хватает 5»; ошибается на измеренном примере
  `test_editor_delete_form_degrades_without_alpine` (`test_ads_editor.py`) /
  `test_editor_delete_degrades_without_htmx` (`test_editor_schedules.py`).

Замер до плана: alpine — 5, htmx — 3, пересечение объявленных ключей пусто → точных пар 0.

## Пять новых тестов и их ключи предмета

| Новый htmx-тест | Файл | Пара (alpine) | Ключ `(screen, action)` |
|---|---|---|---|
| `test_the_payment_form_keeps_its_route_and_degrades_without_htmx` | `test_billing_section.py` | `test_the_only_payment_left_is_a_real_form_and_degrades_without_alpine` | `("/billing", "POST /billing/subscribe")` |
| `test_accounts_delete_confirm_degrades_without_htmx` | `test_responsive_markup.py` | `test_accounts_delete_form_degrades_without_alpine` | `("/accounts", "POST /accounts/{account_id}/delete")` |
| `test_ads_delete_confirm_degrades_without_htmx` | `test_responsive_markup.py` | `test_ads_delete_form_degrades_without_alpine` | `("/ads", "POST /ads/{ad_id}/delete")` |
| `test_admin_user_delete_confirm_degrades_without_htmx` | `test_responsive_markup.py` | `test_admin_user_delete_form_degrades_without_alpine` | `("/admin/users/{user_id}", "POST /admin/users/{user_id}/delete")` |
| `test_editor_ad_delete_confirm_degrades_without_htmx` | `test_ads_editor.py` | `test_editor_delete_form_degrades_without_alpine` | `("/ads/{ad_id}/edit", "POST /ads/{ad_id}/delete")` |

Каждый утверждает по отрендеренной разметке: форма с `hx-post` несёт `method="post"`,
непустой `action`, и `hx-post` посимвольно равен `action`; затем POST без признака htmx
отвечает перенаправлением на полный документ (для удалений — 302/303, после перехода
`200` с `<!DOCTYPE`; для оплаты — 302 на страницу ЮKassa под подменой сети
`_yookassa_network` из `test_htmx_post_pairs.py`, без `HX-Location`/`HX-Redirect`).
Каждый докстринг одной строкой говорит, чего тест НЕ утверждает (рантайма JS).

## Летопись чисел (записана в модуле гейта)

- `не хватает 2 → не хватает 5, Фаза 15, план 15-03` — 2 есть ВЫЧИТАНИЕ (5 − 3), верное как
  паритет счёта и неверное как число пар; «ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ»; текст D-14
  не вычёркивается.
- `DEGRADATION_PAIRS_DECLARED`: `0` (задача 1, измерено: ключи не пересекаются) → `5`
  (задача 2). Число поставлено прогоном покрасневшего правила: RED дословно
  `пар по объявленному предикату 0, объявлено 5:` + пять строк `… : БЕЗ ПАРЫ` + `assert 0 == 5`;
  GREEN — тот же прогон нашёл пять пар.
- `HTMX_DEGRADATION_TESTS_DECLARED`: `3 → 8` (задача 2).

## Ни один существующий тест не переименован

`git show --format= --unified=0 0203202f -- <файл>` (коммит задачи 2), заголовки ханков:

```
tests/test_pages/test_billing_section.py
@@ -665,0 +666,49 @@ async def test_the_only_payment_left_is_a_real_form_and_degrades_without_alpine(
tests/test_pages/test_responsive_markup.py
@@ -1261,0 +1262,44 @@ async def test_accounts_delete_form_degrades_without_alpine(
@@ -3446,0 +3491,42 @@ async def test_ads_delete_form_degrades_without_alpine(
@@ -3472,0 +3559,43 @@ async def test_admin_user_delete_form_degrades_without_alpine(
tests/test_pages/test_ads_editor.py
@@ -1923,0 +1924,49 @@ async def test_editor_delete_form_degrades_without_alpine(
```

Каждый ханк `-N,0` — ноль удалённых строк; `grep -cE '^-[^-]'` по каждому файлу — `0`.
`grep -c 'degrades_without_alpine'` по трём файлам — 1 + 3 + 1 = 5, как до правки.
`test_no_client_state_node_is_a_swap_target` (GATE-06) утверждается существующим правилом гейта.

## Accomplishments
- Гейт пар с объявленным предикатом, 15 правил: перечни литералами (SP-1), полнота и
  непротиворечивость ключей, счёт пар, ложная пара, изъятия, непарные, три контроля от вакуума,
  GATE-06, три границы разборщика.
- Пять пар добавлены, `DEGRADATION_PAIRS_DECLARED` 0 → 5 с RED-уликой `RED_EVIDENCE_OK`.
- Три границы (`parametrize`/фабрика/присвоение/`setattr`/`globals()`; имя в прозе; суффикс не
  механизма) закрыты правилами-запретами, каждое со своим синтетическим контролем в памяти.

## Task Commits

1. **Задача 1: предикат пары, перечни, ноль точных пар** — `b548347a` (test)
2. **Задача 2 RED: пять ключей записаны до функций, 0 → 5, 3 → 8** — `319f6612` (test)
3. **Задача 2 GREEN: пять `*_degrades_without_htmx`** — `0203202f` (feat)
4. **Задача 3: три границы разборщика и правила-запреты** — `4538d1ba` (feat)

## Files Created/Modified
- `tests/test_templates/test_degradation_pairs.py` — гейт суиты о себе: предикат, `DEGRADATION_SUBJECTS`, счёт пар, изъятия, границы.
- `tests/test_pages/test_billing_section.py` — пара к тесту формы оплаты.
- `tests/test_pages/test_responsive_markup.py` — три пары к удалениям аккаунта, объявления, пользователя.
- `tests/test_pages/test_ads_editor.py` — пара к удалению объявления из редактора.

## Decisions Made
- Ключ предмета — `(страница, изменяющий маршрут)`, записанный полем; сравнение точное, без нормализации (контроль: ключ, отличающийся одним регистром глагола, пары не даёт).
- htmx-тесты смотрят на форму панели подтверждения (единственную с `hx-post`), alpine-тесты — на форму-триггер строки; предмет у них один, основы имён разные.
- Для оплаты путь без htmx проверен на успешной ветке с подменой только сети ЮKassa (сервис создания платежа не подменяется) — существующий приём `test_htmx_post_pairs.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Точность записи] Контрпример ложной пары: экран один, различается действие**
- **Found during:** Задача 1 (чтение `test_editor_delete_degrades_without_htmx`)
- **Issue:** План пишет, что `editor_delete_form` и `editor_delete` — «разные экраны в разных файлах». Замер: htmx-тест шлёт `POST /schedules/{id}/delete` с возвратом в `/ads/{ad_id}/edit`, то есть экран у обоих — редактор объявления; различается ДЕЙСТВИЕ (удаление объявления против удаления расписания).
- **Fix:** Ключи записаны по замеру; докстринг гейта называет уточнение; правило ложной пары утверждает `a.screen == h.screen` и `a.action != h.action`. Вывод плана (это НЕ пара) не меняется и становится сильнее: совпадение экрана без действия парой не является.
- **Files modified:** `tests/test_templates/test_degradation_pairs.py`
- **Committed in:** `b548347a`

**2. [Rule 3 - Критерий приёмки] Подстрока `in source` в `sources.items()`**
- **Found during:** Задача 3
- **Issue:** Критерий задачи 1 `grep -c "in source"` == 0 ловил выражение `for path, text in sources.items()`.
- **Fix:** Переписано на `in sorted(sources.items())` (поведение то же, порядок детерминирован).
- **Committed in:** `4538d1ba`

**3. [Оркестратор] Команда `uv run pytest tests/ -q -p no:randomly -m "not planning"` не прогонялась**
- **Found during:** Задача 3, verify
- **Issue:** Отбор `-m "not planning"` — это практически вся продуктовая суита (~36 мин); оркестратор прямо указал не запускать полный прогон — он выполняет его сам после волны.
- **Fix:** Прогнано то, что эти правки могут задеть: гейт (15), три правимых файла целиком (253, было 248), `tests/test_templates/` (275), восемь гейтов, читающих `tests/` (`test_no_metering_remains`, `test_declared_invariants`, `test_payment_status_vocabulary`, `test_ops_state`, `test_hx_location_destinations`, `test_htmx_response_contract`, `test_notices_channel`, `test_prose_names_live_symbols` — 138), `compileall` — чисто. Непрогнанная команда записана в `.planning/WINDOWS.md` (`unrun-verify`, фаза 15) и закрывается полным прогоном оркестратора.

---

**Total deviations:** 3 (1 уточнение записи, 1 критерий приёмки, 1 прогон передан оркестратору)
**Impact on plan:** Предмет плана не изменён; расхождения названы, а не сглажены.

## TDD Gate Compliance

- RED: `319f6612 test(15-03)` — целевое правило `test_the_pair_count_is_the_declared_one` упало на утверждении предмета (`0 == 5`, пятеро названы БЕЗ ПАРЫ); запись улики сведена из junit-xml того же прогона в TAP, `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`). Скрипт перевода не закоммичен.
- GREEN: `0203202f feat(15-03)` — пять тестов, гейт 12/12 зелёный, три файла 253 passed.
- `b548347a test(15-03)` (задача 1) предшествует RED как честный ноль и зелёный; `4538d1ba feat(15-03)` — границы задачи 3 (не TDD-задача). REFACTOR не понадобился.

## Issues Encountered
- Пробный скрипт разметки (`tests/test_pages/test_zz_scratch_probe.py`) создавался для замера форм `hx-post` на пяти экранах и удалён до первого коммита; в дерево не попал.
- `requirements.ready-ids` для GATE-10: `ready: []`, `blocked: ["GATE-10"]` — требование объявлено ещё и планом 15-09; отметка не ставится (её ставит закрытие фазы).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Гейт пар готов; план 15-09 (тоже GATE-10) может опираться на `DEGRADATION_SUBJECTS`.
- Верность ключей предмета — человеческое суждение (D4 в `coverage`).

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- FOUND: `tests/test_templates/test_degradation_pairs.py`, `tests/test_pages/test_billing_section.py`, `tests/test_pages/test_responsive_markup.py`, `tests/test_pages/test_ads_editor.py`
- FOUND commits: `b548347a`, `319f6612`, `0203202f`, `4538d1ba`
- `git rev-list --count 02827604..HEAD` = 4 (до коммитов записи)
