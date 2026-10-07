---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 17
subsystem: testing
tags: [pytest, ast, htmx, degradation, gate, GATE-10, wr-03, location, delete]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-03: гейт `test_degradation_pairs.py` и четыре пары удаления `*_delete_confirm_degrades_without_htmx`; план 15-14 — предшественник по `depends_on`"
provides:
  - "четыре пары удаления GATE-10 утверждают ТОЧНЫЙ `Location` ветки успеха своего обработчика и исчезновение строки (`expire_all()` → `get(...) is None`)"
  - "`_redirect_pairs_without_exact_location` — чистая функция над «путь → исходник» (ast): перенаправляющая `*_degrades_without_htmx` без сличения адреса называется `файл:строка имя`"
  - "правило `test_every_redirecting_degradation_pair_asserts_the_exact_location` с антивакуумом (пять пар GATE-10 видны перенаправляющими) и контроль `test_control_a_pair_asserting_only_the_status_is_named`"
affects: [15-18, phase-15-verification, GATE-10, "критерий 4 ROADMAP Фазы 15"]

actuals:
  tokens: 7090
  tasks: 2
  commits: 2
plan_head_before: 583563d8330dd43d624644756b5fac1c8d32892d

tech-stack:
  added: []
  patterns:
    - "пара деградации различает удаление, холостую ветку и отказ: точный адрес успеха литералом, снятым чтением обработчика, + исчезновение строки как несущее утверждение там, где адрес холостой ветки совпадает с адресом успеха"
    - "самосравнение адреса (`location == response.headers[\"location\"]`) распознаётся замыканием имён, связанных с чтением `location` ответа, до неподвижной точки"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-17-SUMMARY.md
  modified:
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_ads_editor.py
    - tests/test_templates/test_degradation_pairs.py

key-decisions:
  - "15-17: адреса успеха сняты чтением обработчиков и совпали с ожиданием ревью — `/ads` (ads_delete, и со списка, и из редактора), `/accounts` (accounts_delete), `/admin/users` (admin_delete_user); расхождений с ревью нет"
  - "15-17: форма утверждения статуса `in (302, 303)` сохранена — `PAIRED_302_ASSERTIONS_DECLARED` не двигался (190), `DEGRADATION_PAIRS_DECLARED` = 5, ни одна пара не переименована"
  - "15-17: правило пакета пар смотрит только `*_degrades_without_htmx` с узнаваемым утверждением кода 302/303; адрес считается точным, если вторая сторона равенства не вычитана из того же ответа (имя, связанное с чтением `location`, тоже вычитано)"

patterns-established:
  - "Пара, считающаяся уликой пути без htmx, обязана сличать адрес перенаправления с адресом не из ответа — иначе краснит гейт пакета пар"

requirements-completed: [GATE-10]

coverage:
  - id: D1
    description: "Четыре пары удаления утверждают точный `Location` ветки успеха и исчезновение сущности; холостая ветка и отказ пару не зеленят"
    requirement: GATE-10
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_responsive_markup.py tests/test_pages/test_ads_editor.py -q -p no:randomly -k delete_confirm_degrades_without_htmx (4 passed)"
        status: pass
      - kind: integration
        ref: "контроль направления: ads_delete без удаления → 2 failed (`объявление осталось в базе`), accounts_delete без удаления → failed (`аккаунт остался в базе`), admin_delete_user веткой отказа → failed (`'/admin/users/1' == '/admin/users'`); `git diff --exit-code -- app/` пуст"
        status: pass
    human_judgment: false
  - id: D2
    description: "Гейт пакета пар краснеет на слабой паре: перенаправление без точного адреса"
    requirement: GATE-10
    verification:
      - kind: unit
        ref: "tests/test_templates/test_degradation_pairs.py#test_every_redirecting_degradation_pair_asserts_the_exact_location"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_degradation_pairs.py#test_control_a_pair_asserting_only_the_status_is_named"
        status: pass
      - kind: other
        ref: "помощник над исходниками `git show 583563d8` (до задачи 1): названо ровно 4 — все WR-03; над `95fb1d06`: 0"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 17: Пары удаления различают удаление и отказ (WR-03) Summary

**Четыре пары удаления GATE-10 теперь утверждают точный `Location` ветки успеха (`/accounts`, `/ads`, `/admin/users`, `/ads`) и то, что строки в базе больше нет; гейт `test_degradation_pairs.py` получил правило по `ast`, которое краснит любую перенаправляющую `*_degrades_without_htmx` без сличения адреса — на дереве до плана оно называет ровно эти четыре.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-09-25T06:53:12Z
- **Completed:** 2026-09-25T07:10:35Z
- **Tasks:** 2
- **Files modified:** 3 (все — тесты; `app/` не тронут)

## Accomplishments

- `test_accounts_delete_confirm_degrades_without_htmx`, `test_ads_delete_confirm_degrades_without_htmx`,
  `test_admin_user_delete_confirm_degrades_without_htmx` (`test_responsive_markup.py`) и
  `test_editor_ad_delete_confirm_degrades_without_htmx` (`test_ads_editor.py`) утверждают
  `response.headers["location"] == <литерал успеха>` и, после `db_session.expire_all()`,
  `await db_session.get(<Модель>, <id>) is None`. Прежние утверждения (302/303, нет
  `HX-Location`, 200 и `<!DOCTYPE` по адресу) оставлены. Имена не тронуты.
- Правило пакета пар `test_every_redirecting_degradation_pair_asserts_the_exact_location` и
  контроль `test_control_a_pair_asserting_only_the_status_is_named`; три границы правила
  названы в докстринге помощника; в докстринге модуля «ровно две вещи» дополнены третьей
  по идиоме D-30/D-32 (прежний текст не вычеркнут).

## Адреса успеха, снятые чтением обработчиков

| Пара | Обработчик | Ветка успеха | Холостая ветка | Отказ |
|---|---|---|---|---|
| accounts | `accounts_delete` (`app/pages/accounts.py:1365`) | `redirect="/accounts"` (`:1413`) | тот же `/accounts` (вне колонки / чужой / нет строки) | `/login`, 403 чужого источника |
| ads (список) | `ads_delete` (`app/pages/ads.py:1549`) | `redirect="/ads"` (`:1614`) | тот же `/ads` (`:1605` вне колонки; нет строки — `:1614`) | `/login`, 403 |
| admin user | `admin_delete_user` (`app/pages/admin.py:1969`) | `redirect="/admin/users"` (`:2015`) | тот же `/admin/users` (`:2006`) | удаление себя → `/admin/users/{user_id}` (`:2009-2010`), 403 |
| editor ad | `ads_delete` — тот же маршрут | `/ads` (экрана редактора после удаления нет) | тот же `/ads` | `/login`, 403 |

**Расхождений с ревью нет:** ожидание ревью (`/ads`, `/accounts`, `/admin/users`; для
редактора — адрес успеха `ads_delete`) совпало с чтением. Во всех четырёх случаях адрес
холостой ветки СОВПАДАЕТ с адресом успеха, поэтому несущее утверждение каждой пары —
исчезновение строки; адрес отсекает отказы (`/login`, `/admin/users/{id}`).

Номера строк плана (перезамер): `ads.py:1549`, `accounts.py:1365`, `admin.py:1969` и отказ
`:2010` — на месте; `test_htmx_post_pairs.py` `_302_subjects` `:2949`,
`_post_302_assertions` `:2971`, `PAIRED_302_ASSERTIONS_DECLARED` `:3406` — в пределах
цитированных диапазонов; `test_impersonation_gate.py` абзац границ `:459` (план `:456-476`).

## `PAIRED_302_ASSERTIONS_DECLARED` — не двигался

Форма `status_code in (302, 303)` сохранена во всех четырёх парах; правило пар 302
считает только `status_code == 302`, так что число утверждений 302 о переведённых
обработчиках не изменилось: **190, не двигалось**. `DEGRADATION_PAIRS_DECLARED = 5`
(`grep` — одна строка). `HX_LOCATION_DESTINATION_CALLS_DECLARED` (81) считает вызовы в
`app/pages/`, которые план не трогал, — не двигался.

## Контроль направления (на копии рабочего дерева, файлы восстановлены)

1. `ads_delete`: `if ad:` → `if ad and False:` (холостая ветка вместо удаления) —
   `2 failed, 2 passed`: `test_ads_delete_confirm_degrades_without_htmx` и
   `test_editor_ad_delete_confirm_degrades_without_htmx`, обе по
   `AssertionError: объявление осталось в базе: путь без htmx прошёл холостой веткой, а не удалением`.
2. `accounts_delete`: `if id_in_column(account_id):` → `… and False:` —
   `test_accounts_delete_confirm_degrades_without_htmx` FAILED:
   `аккаунт остался в базе …`.
3. `admin_delete_user`: ветка успеха заменена ответом ветки отказа
   (`redirect=f"/admin/users/{user_id}"`) — `test_admin_user_delete_confirm_degrades_without_htmx`
   FAILED: `assert '/admin/users/1' == '/admin/users'`.

После каждого: `git checkout -- <файл>`; `git diff --exit-code -- app/` пуст (`RESTORED`).

## Замер правила пакета пар на дереве до и после задачи 1

Помощник, поданный исходниками `tests/**/*.py` из `git show` (скрипт в scratchpad, не
закоммичен):

- `583563d8` (до задачи 1): перенаправляющих htmx-функций 8, названо **ровно 4** —
  `test_ads_editor.py:1925 test_editor_ad_delete_confirm_…`,
  `test_responsive_markup.py:1263 test_accounts_delete_confirm_…`,
  `:3492 test_ads_delete_confirm_…`, `:3560 test_admin_user_delete_confirm_…`.
- `95fb1d06` (после задачи 1): перенаправляющих 8, названо **0**.

Замер записан комментарием над правилом в самом модуле гейта.

## Task Commits

1. **Задача 1: четыре пары удаления утверждают точный адрес и исчезновение сущности** — `95fb1d06` (test)
2. **Задача 2: пакет пар запрещает слабую пару** — `5650c978` (test)

**Plan metadata:** коммит `docs(15-17)` со сводкой и учётом.

## TDD

План `type: execute`, `tdd_mode: true`. Поведения продукта ни одна задача не добавляет и
не меняет: обе задачи правят только тесты, `app/` не тронут. Задача 1 УСИЛИВАЕТ пары;
её RED-эквивалент — контроль направления выше (подмена обработчика краснит пару по
несущему утверждению, дословные отказы приведены), а не коммит `test(...)` перед
`feat(...)`: реализации, которую пришлось бы писать, нет. Задача 2 добавляет правило
гейта; его RED — замер на дереве `583563d8`, где правило называет ровно четыре функции
WR-03 (приведено выше), GREEN — ноль на дереве после задачи 1. Коммита `feat(15-17)` нет
и быть не должно; `## TDD Gate Compliance` для `type: execute` не требуется.

## Files Created/Modified

- `tests/test_pages/test_responsive_markup.py` — три пары удаления: точный адрес + исчезновение строки, абзац WR-03 в докстрингах
- `tests/test_pages/test_ads_editor.py` — пара удаления из редактора: то же
- `tests/test_templates/test_degradation_pairs.py` — `_redirect_pairs_without_exact_location` и помощники, правило, контроль, замер, дополнение докстринга модуля

## Decisions Made

- Статус оставлен формой `in (302, 303)`: переход на `== 302` сдвинул бы
  `PAIRED_302_ASSERTIONS_DECLARED` без выигрыша в различении — различение даёт адрес и
  исчезновение строки.
- Правило распознаёт самосравнение не только буквальным `headers["location"]` с обеих
  сторон, но и через имя, связанное с чтением `location` ответа (замыкание до
  неподвижной точки): иначе контроль плана `location == response.headers["location"]`
  прошёл бы как «точный адрес». Имя из импорта (`YOOMONEY_CONFIRMATION_URL` в паре
  оплаты) адресом считается — оно не вычитано из ответа.
- Антивакуум правила — не новое число, а включение: все пять `PAIRED_HTMX_TESTS` обязаны
  быть видны правилу перенаправляющими.

## Deviations from Plan

None - plan executed exactly as written. (Контроль направления сделан на трёх
обработчиках вместо одного — это усиление улики, а не отступление.)

## Issues Encountered

- `ruff` в окружении не установлен (`uv run ruff` — `Failed to spawn`); одна длинная
  строка правлена руками, длины строк сверены `awk`.

## Проверки (без полной суиты)

- `tests/test_pages/test_responsive_markup.py tests/test_pages/test_ads_editor.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_hx_location_destinations.py tests/test_templates/` — `736 passed`.
- `tests/test_templates/` — `359 passed`; `tests/test_templates/test_degradation_pairs.py` — `17 passed`.
- `tests/test_pages/test_responsive_markup.py tests/test_pages/test_ads_editor.py` целиком — `193 passed`.
- `tests/test_planning/` — `114 passed`.
- Полная суита (`just test`, ~40 мин) — **подменена** перечнем выше по указанию оркестратора: её гоняет оркестратор после волны; запись в `WINDOWS.md` не открывалась.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 15-18. Требование GATE-10 в `REQUIREMENTS.md` не отмечалось (указание
оркестратора).

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED
