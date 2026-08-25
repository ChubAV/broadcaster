---
phase: 06-admin-panel
plan: 06
subsystem: auth
tags: [fastapi, dependencies, jwt, blocking, scheduler, celery, pytest, tdd]

requires:
  - phase: 06-admin-panel (план 06-02)
    provides: единая точка установки cookie сессии (`set_session_cookie`) и объявленный набор её атрибутов — отказ во входе встал в тот же обработчик ПОСЛЕ неё
  - phase: 05.1
    provides: приём «соседняя зависимость + пер-роутерная навеска + машинный гейт перечня» (`get_current_user_id_with_access`), повторённый здесь третьим множеством
provides:
  - Блокировка ДЕЙСТВУЕТ на всех трёх путях: страничный вход не выдаёт cookie, JSON-поверхность не пускает по уже выданной cookie, сбор расписаний не рассылает за заблокированного
  - `get_current_user_id_active` — соседняя зависимость блокировки с веткой признака действующего лица (`act`, D-26)
  - `BLOCK_CHECKED_API_ROUTERS` — третье объявленное множество машинного гейта; роутер, не попавший ни в одно из трёх, роняет тест
  - Решение D-53: денежный роутер блокировкой не закрывается; вебхук ЮKassa принимается всегда
  - `tests/test_pages/test_blocked_user.py` — единственный файл, где предмет блокировки собран целиком (20 тестов)
affects: [06-12 (имперсонация — выпуск токенов с `act`), 06-13 (запреты под чужой личностью), любая будущая правка авторизации]

actuals:
  tokens: 20000
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Соседняя зависимость + пер-роутерная навеска + объявленное множество в машинном гейте — второй экземпляр приёма 05.1, не второе его изобретение"
    - "Один вердикт на пользователя под уже существующей мемоизацией цикла (блокировка + доступ в одной функции)"

key-files:
  created:
    - tests/test_pages/test_blocked_user.py
  modified:
    - app/dependencies.py
    - app/main.py
    - app/pages/auth.py
    - app/application/scheduling/use_cases.py
    - tests/test_pages/test_access_gate.py
    - tests/test_admin.py
    - .planning/phases/06-admin-panel/06-CONTEXT.md

key-decisions:
  - "D-53: денежный роутер блокировкой НЕ закрывается (вариант A владельца); вебхук ЮKassa принимается всегда; цена — ручной возврат средств силами поддержки"
  - "Комментарий app/main.py:108-110 о составе денежного роутера был устаревшим — исправлен по факту и записан в решении, чтобы следующая фаза не повторила ложную посылку"
  - "Блокировка стоит ПЕРВОЙ из двух зависимостей: заблокированному с истёкшим сроком осмысленно сказать «заблокировано», а не «продлите доступ»"
  - "Предмет блокировки вывезен из tests/test_admin.py целиком, включая тумблер админки: половина, оставленная там, снова разложила бы блокировку по файлам"

patterns-established:
  - "Третье множество машинного гейта объявлено ОТДЕЛЬНО, хотя совпадает по составу со вторым: гейт доступа и гейт блокировки отвечают на разные вопросы, и выведение одного из другого запретило бы будущее расхождение молча"
  - "Ветка `act` пишется ДО плана, выпускающего такие токены, и закрепляется тестом на вручную собранном токене — иначе следующая правка авторизации закрыла бы вход администратора молча"

requirements-completed: [ADMIN-05, CR-01]

coverage:
  - id: D1
    description: "Заблокированному не выдаётся cookie при страничном входе; причина названа словами и записана именованной строкой журнала"
    requirement: "CR-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_a_blocked_user_gets_no_cookie_from_the_page_login"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_the_login_refusal_is_journaled_with_the_user_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_an_ordinary_user_still_logs_in_unchanged"
        status: pass
    human_judgment: false
  - id: D2
    description: "Заблокированный не проходит по УЖЕ ВЫДАННОЙ cookie на закрытых JSON-маршрутах; незаблокированный проходит по всем"
    requirement: "CR-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_a_blocked_user_is_refused_on_a_closed_json_route"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_the_json_refusal_is_journaled_with_the_user_id"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_an_ordinary_user_still_passes_every_closed_json_route"
        status: pass
    human_judgment: false
  - id: D3
    description: "Сбор расписаний пропускает заблокированного тихо, вердикт спрашивается один раз на пользователя, рассылки остальных не задеты"
    requirement: "ADMIN-05"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_a_blocked_user_dispatches_nothing_and_keeps_the_schedule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_blocking_one_user_does_not_touch_the_others"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_the_blocking_verdict_is_asked_once_per_user"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_unblocking_returns_the_schedule_to_the_selection"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_a_skipped_blocked_user_writes_no_send_log"
        status: pass
    human_judgment: false
  - id: D4
    description: "Перечень закрываемых блокировкой роутеров объявлен и полон; денежный роутер вне него (D-53); общий аутентификатор не тронут"
    requirement: "CR-01"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_access_gate.py#test_the_blocking_gate_covers_exactly_the_declared_routers"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_access_gate.py#test_the_api_authentication_dependency_is_left_untouched"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_blocked_user.py#test_the_blocking_check_did_not_move_into_the_shared_authenticator"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_the_money_router_stays_open_to_a_blocked_user"
        status: pass
    human_judgment: false
  - id: D5
    description: "Вход администратора под заблокированным пользователем остаётся возможным на JSON-поверхности (D-26)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_blocked_user.py#test_an_impersonation_token_is_not_refused_by_the_subject_block"
        status: pass
    human_judgment: true
    rationale: "Тест закрывает только JSON-поверхность на ВРУЧНУЮ собранном токене. Страничный путь имперсонации (`get_user_from_cookie`) ветки `act` не имеет и заблокированного отвергает — см. «Передача плану 06-12». Полнота D-26 наблюдаема только после 06-12, и человек обязан это увидеть."

duration: 90min
completed: 2026-08-22
status: complete
---

# Phase 06 Plan 06: Блокировка начинает действовать Summary

**Блокировка учётной записи закрыта на трёх путях сразу — отказ во входе словами, соседняя зависимость `get_current_user_id_active` на пяти JSON-роутерах и пропуск в боевом сборе расписаний, — при нетронутом общем аутентификаторе и открытом денежном роутере (D-53).**

## Performance

- **Duration:** ~90 мин (агент-продолжение; чекпойнт задачи 1 решён владельцем до старта; из них ~30 мин — прогоны полной суиты)
- **Started:** 2026-08-22T15:52Z
- **Completed:** 2026-08-22T17:23Z
- **Tasks:** 3
- **Files modified:** 7 (+1 создан)

## Verification

| Команда | Результат |
|---------|-----------|
| `uv run pytest tests/test_pages/test_blocked_user.py -q` | **20 passed** (план требовал ≥15) |
| `uv run pytest tests/test_pages/test_access_gate.py -q` | **12 passed**, включая гейт-запрет на правку аутентификатора |
| `uv run pytest tests/test_application tests/test_admin.py -q` | **241 passed** |
| `uv run pytest tests/test_routes -q` | **170 passed** |
| `uv run pytest tests/test_worker tests/test_services -q` | **163 passed** |
| `uv run pytest tests/ -q` (= `just test`) | **1 failed, 1844 passed** — единственное падение есть чужой доказанно дофазовый долг (см. «Issues», п. 2) |

Греп-критерии плана: `def get_current_user_id_active` найден; `get_current_user_id_active` в `app/main.py` — 7 вхождений; `BLOCK_CHECKED_API_ROUTERS` объявлен; `grep -Ec 'billing_cache|invalidate_access_cache' app/dependencies.py` = **0** (кэша вердикта не заведено); `grep -Ec 'select\(Schedule\)' app/application/scheduling/use_cases.py` = **1** (второго запроса не появилось); `grep -c 'blocked' tests/test_admin.py` = **0**.

## Accomplishments

- **Три пути закрыты, и ни один не «везде».** Отказ во входе (`login_submit`), соседняя зависимость на JSON-поверхности и вердикт в сборе расписаний. Страничный путь не тронут — он проверяет состояние учётной записи с фазы 05.1.
- **Общий аутентификатор не тронут ни одной строкой.** Машинный гейт `test_the_api_authentication_dependency_is_left_untouched` зелёный; в новый файл добавлен его близнец, сторожащий именно `is_blocked`.
- **Перечень закрываемых роутеров стал третьим объявленным множеством.** Роутер, добавленный будущей фазой и не попавший ни в одно из трёх, роняет тест — «наверное, забыли» больше не проходит молча.
- **Обе границы сверху проверены, а не подразумеваются.** Незаблокированный входит с тем же набором атрибутов cookie, проходит все пять закрытых маршрутов и рассылает по расписанию; смешанная выборка (заблокированный вперемешку с двумя обычными) — отдельный тест.
- **Слабый свидетель заменён, а не переименован.** `test_blocked_user_cannot_login` обещал эффект блокировки, а проверял один JSON-маршрут входа; весь предмет переехал в `tests/test_pages/test_blocked_user.py` (20 тестов).

## Task Commits

1. **Задача 1: решение владельца о денежном роутере** — `99aa0d8` (docs)
2. **Задача 2 RED: тесты входа и JSON-поверхности** — `2602f82` (test)
3. **Задача 2 GREEN: зависимость, навеска, отказ во входе** — `7c91157` (feat)
4. **Задача 3 RED: тесты сбора расписаний** — `e53201b` (test)
5. **Задача 3 GREEN: пропуск заблокированного в сборе** — `2104e6c` (feat)

REFACTOR-коммитов нет: обе реализации минимальны и переписывать в них было нечего.

## Files Created/Modified

- `app/dependencies.py` — `BLOCKED_DETAIL`, `_actor_claim` (чтение `act`), `get_current_user_id_active`; общий аутентификатор не изменён
- `app/main.py` — вторая зависимость на пяти роутерах создания ценности; исправлен устаревший комментарий о составе денежного роутера
- `app/pages/auth.py` — `BLOCKED_LOGIN_ERROR` и отказ заблокированному ДО выдачи cookie, с записью `blocked_login_refused`
- `app/application/scheduling/use_cases.py` — `_user_send_verdict`: блокировка и доступ одним вердиктом под существующей мемоизацией
- `tests/test_pages/test_blocked_user.py` — новый файл, 20 тестов на все три пути + тумблер админки
- `tests/test_pages/test_access_gate.py` — `BLOCK_CHECKED_API_ROUTERS` и `test_the_blocking_gate_covers_exactly_the_declared_routers`
- `tests/test_admin.py` — вывезен весь предмет блокировки (`grep -c blocked` = 0)
- `.planning/phases/06-admin-panel/06-CONTEXT.md` — решение D-53
- `.planning/phases/06-admin-panel/deferred-items.md` — уточнение к чужому долгу (см. «Issues»)

## Decisions Made

- **D-53 (владелец, вариант A):** денежный роутер блокировкой не закрывается; вебхук ЮKassa принимается всегда; цена — ручной возврат средств. Отвергнутые B и C записаны с причиной, оба перепроверенных факта — тоже.
- **Номер решения — D-53, а не D-52.** Файл на момент чтения содержал максимум D-51; D-52 concurrently берёт план 06-05 по указанию оркестратора. Пропуск номера дешевле коллизии при слиянии.
- **Порядок двух зависимостей:** блокировка первой. Заблокированному с истёкшим сроком «продлите доступ» — неверный совет: продление ему ничего не откроет.
- **`act` читается вторым разбором токена.** Общий аутентификатор отдаёт только `sub` и трогаться не может; цена — одна лишняя проверка подписи на ЗАКРЫТЫХ маршрутах, и она названа в докстринге.
- **Кэша вердикта блокировки нет (D-31).** `grep -Ec 'billing_cache|invalidate_access_cache' app/dependencies.py` = 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Устаревший комментарий в `app/main.py` исправлен**
- **Found during:** Задача 2 (навеска зависимости)
- **Issue:** Комментарий на строках 108-110 утверждал, что в денежном роутере живут «и чтения раздела оплаты, и вебхук». Чтений там нет с плана 05-04; страничные маршруты оплаты живут в `app/pages/billing.py`. Именно по этому комментарию формулировалась развилка задачи 1 — то есть ложная посылка воспроизводилась бы каждой следующей фазой.
- **Fix:** Комментарий переписан по факту и связан с D-53; сам факт записан в решении, а не только в коде.
- **Files modified:** `app/main.py`, `.planning/phases/06-admin-panel/06-CONTEXT.md`
- **Verification:** `tests/test_pages/test_access_gate.py` зелёный; факт перепроверен чтением `app/routes/billing.py` (один маршрут, строка 95).
- **Committed in:** `7c91157` / `99aa0d8`

**2. [Rule 3 - Blocking] Тумблер блокировки вывезен из `tests/test_admin.py` вместе с предметом**
- **Found during:** Задача 3
- **Issue:** Критерий приёмки требует `grep -c 'blocked' tests/test_admin.py` = 0, а в файле было ТРИ теста со словом: слабый свидетель (`test_blocked_user_cannot_login`) и два теста тумблера (`test_admin_block_user`, `test_admin_cannot_block_self`). Удаление одного лишь слабого свидетеля критерий не закрывает, а правка ассертов ради грепа была бы игрой с проверкой.
- **Fix:** Слабый свидетель удалён; оба теста тумблера ПЕРЕЕХАЛИ в `tests/test_blocked_user.py` (переписаны на помощники файла). Покрытие не потеряно, предмет собран в одном месте.
- **Files modified:** `tests/test_admin.py`, `tests/test_pages/test_blocked_user.py`
- **Verification:** `uv run pytest tests/test_admin.py -q` зелёный; `grep -c 'blocked' tests/test_admin.py` = 0.
- **Committed in:** `e53201b`

**3. [Rule 3 - Blocking] Тест 5 задачи 2 утверждает достижимость обработчика, а не «200 на любом открытом маршруте»**
- **Found during:** Задача 2 (написание RED)
- **Issue:** План просит «200 на маршруте, оставленном открытым перечнем». Открытых JSON-маршрутов, отдающих 200 заблокированному, в продукте ровно один — вебхук ЮKassa, и он под собственным гардом источника (403 «Untrusted source» в суите).
- **Fix:** Тест собирает приложение с `yookassa_webhook_verify_ip=False` (настройкой, а не подделкой адреса) и посылает НЕЗНАКОМОЕ событие: обработчик отвечает 200 `{"ok": false}`. Утверждение получилось сильнее просимого — оно доказывает, что запрос заблокированного ДОШЁЛ до денежного обработчика, то есть прямо свидетельствует D-53.
- **Files modified:** `tests/test_pages/test_blocked_user.py`
- **Verification:** `test_the_money_router_stays_open_to_a_blocked_user` зелёный.
- **Committed in:** `2602f82`

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking). Расширения предмета нет: правки лежат ровно в трёх названных планом местах плюс исправленный комментарий рядом с навеской.

## Issues Encountered

**1. Процессное нарушение исполнителя: случайно выполнен `git stash` (запрещённая в worktree операция).**
Команда `git stash push -k -u -m nope` попала в строку по ошибке исполнителя и сняла незакоммиченные правки задач 2–3. Стек стэша содержал РОВНО ОДНУ запись — свою, на этой ветке, — и она была немедленно возвращена `git stash pop stash@{0}`; `git stash list` после этого пуст, `git diff --stat` подтвердил все 545 строк на месте. Работа не потеряна, чужие записи не тронуты. Раскрывается здесь потому, что операция запрещена не из вкуса: стек `refs/stash` общий для всех worktree, и при наличии соседней записи `pop` втянул бы чужой WIP.

**2. `test_image_base_url_comes_from_app_settings` краснеет в общем прогоне — ЧУЖОЙ, ДОКАЗАННО ДОФАЗОВЫЙ долг.**
Долг уже описан планом 06-04 в `deferred-items.md`. Этот план сузил его до минимального воспроизведения (`test_access_gate.py` + `test_ads_editor.py`) и ПРОВЕРИЛ на базовом коммите фазы: та же пара файлов на базе даёт то же падение. То есть связь с планом 06-06 отсутствует, а не «не найдена». Уточнение и гипотеза (снимок глобалов Jinja при первой загрузке шаблона макроса) дописаны в `deferred-items.md`. Не чинится здесь по границе предмета: правка кэша шаблонов задевает рендер всех страниц продукта.

## Известные допущения (не заглушки)

- **Ветка `act` в `get_current_user_id_active` мертва до плана 06-12** — токенов с этим признаком продукт пока не выпускает. Это не заглушка, а исполнение D-26: ветка написана СЕЙЧАС и закреплена тестом на вручную собранном токене именно затем, чтобы починка блокировки не выкинула заодно администратора.
- **Блокировка не выселяет открытые сеансы принудительно** — она закрывает следующее обращение. Мгновенное выселение потребовало бы списка отозванных токенов, то есть хранилища, которого фаза не заводит. Допущение флагировано планом и здесь подтверждено тестом.

## Передача плану 06-12 (НЕ чинилось здесь)

⚠️ **`get_user_from_cookie` (`app/pages/common.py:326`) отвергает заблокированного БЕЗУСЛОВНО — ветки `act` там нет.**
D-26 требует, чтобы администратор мог войти под заблокированным пользователем, а имперсонация ходит именно СТРАНИЧНЫМ путём. Сегодня противоречия не видно: токенов с `act` никто не выпускает. В момент, когда план 06-12 научится их выпускать, вход под заблокированным упрётся ровно в эту строку — и упрётся молча, редиректом на `/login`, а не отказом с причиной.

Этот план страничный путь не трогает намеренно (граница предмета объявлена планом и D-30: там уже есть проверка состояния учётной записи, и правка ограничена тремя названными местами). Шов передан плану 06-12 как ПРЕДУСЛОВИЕ, а не как пожелание: без ветки `act` в `get_user_from_cookie` критерий 3 фазы («не теряя админ-доступ») не закрывается.

## Next Phase Readiness

- Критерий 2 фазы («заблокировать и разблокировать») закрыт содержательно: кнопка есть И эффект есть, оба направления проверены.
- Приём «соседняя зависимость + пер-роутерная навеска + объявленное множество» повторён третьим множеством и готов к четвёртому — план 06-13 (запреты под чужой личностью) ложится на ту же форму.
- Открытый шов один и назван выше (06-12).

## Self-Check: PASSED

- Все семь названных файлов существуют на диске (`ls` подтвердил каждый).
- Все пять коммитов задач присутствуют в `git log` этой ветки: `99aa0d8`, `2602f82`, `7c91157`, `e53201b`, `2104e6c`.
- Заявленные числа тестов сняты с прогонов, а не оценены: 20 в новом файле, 1844 зелёных в полной суите.
- `.planning/WINDOWS.md` НЕ правился намеренно: единственный подходящий дефект (порядковая зависимость суиты) уже стоит там записью 1 от плана 06-04, а дубль в общем файле из параллельного worktree создал бы конфликт слияния без новой информации. Новых заглушек, пропущенных тестов и невыполненных проверок этот план не оставил.

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*
