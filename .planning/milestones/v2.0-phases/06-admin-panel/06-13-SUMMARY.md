---
phase: 06-admin-panel
plan: 13
subsystem: auth
tags: [impersonation, fastapi, ast, dependencies, authorization, tdd, security-gate]

requires:
  - phase: 06-admin-panel (план 06-12)
    provides: "`actor_id(payload)` и claim `act` объектной формы RFC 8693 — единственный читатель признака действующего лица; `_actor_id` в `app/dependencies.py`, читающий тот же признак из запроса без сессии БД"
  - phase: 06-admin-panel (план 06-06)
    provides: "D-53 — денежный роутер НЕ закрывается гейтом блокировки; форма пер-роутерной навески и довод «отказ обязан быть исключением»"
  - phase: 05.1-edinaya-podpiska
    provides: "`tests/test_pages/test_access_gate.py` — образец машинного гейта, читающего ИСХОДНИК по синтаксическому дереву (T-05.1-01, T-05.1-14)"
provides:
  - "`forbid_when_impersonating` — зависимость запрета необратимых и денежных действий под чужой личностью; отказ ИСКЛЮЧЕНИЕМ, отсутствие токена НЕ отказ, сессии БД не берёт"
  - "`IMPERSONATION_FORBIDDEN_DETAIL` — текст отказа, ОТЛИЧИМЫЙ от отказа по правам"
  - "`app/pages/billing.py::money_router` — отдельный роутер денежных ИЗМЕНЯЮЩИХ входов страничного слоя; чтение раздела осталось в общем роутере"
  - "`tests/test_pages/test_impersonation_gate.py` — машинный гейт: 49 изменяющих маршрутов в 15 модулях, три объявленных множества, замыкающее утверждение полноты, три доказанных контроля"
  - "Запрет вложенной имперсонации"
affects: [любая будущая фаза, добавляющая изменяющий маршрут; любая правка авторизации; любая правка денежного пути]

actuals:
  tokens: 27000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Запрет как ЗАВИСИМОСТЬ маршрута + машинный гейт полноты по AST (D-23)"
    - "Гибрид «роутер целиком плюс отдельные маршруты» там, где чисто пер-роутерная форма невозможна"
    - "Выделение отдельного роутера ради свойства «новый маршрут закрыт по умолчанию»"

key-files:
  created:
    - tests/test_pages/test_impersonation_gate.py
  modified:
    - app/dependencies.py
    - app/main.py
    - app/pages/__init__.py
    - app/pages/auth.py
    - app/pages/billing.py
    - app/pages/history.py
    - app/pages/profile.py
    - app/pages/admin.py
    - tests/test_pages/test_impersonation.py
    - tests/test_pages/test_access_gate.py

key-decisions:
  - "Страничный денежный роутер РАЗДЕЛЁН на роутер чтения и `money_router`: навеска на общий роутер закрыла бы `GET /billing`, то есть ответ на типовое обращение «я заплатил, а доступ не открылся»"
  - "Форма профиля закрыта ЦЕЛИКОМ на вырост: отдельного маршрута смены адреса нет, и поле, добавленное в уже разрешённый маршрут, гейт не заметил бы"
  - "`admin_toggle_free_access` запрещён как ДЕНЬГИ; `admin_restart_worker`, `admin_drop_task`, `admin_toggle_block` разрешены как обратимые операции действующего лица"
  - "Расписания разрешены как НАМЕРЕНИЕ отправить, обратимое до срабатывания; необратимый немедленный запуск в продукте один (`history_retry`) и запрещён"
  - "Зависимость в `app/pages/history.py` импортируется МОДУЛЕМ, а не именем: закрыт ровно один маршрут из двух, и это свойство проверяется поиском по файлу"

patterns-established:
  - "Замыкающее утверждение полноты: объединение трёх объявленных множеств равно множеству найденных изменяющих маршрутов — маршрут будущей фазы роняет тест вместо того, чтобы оказаться разрешённым по умолчанию"
  - "Доказанные зубы: два отрицательных контроля и один положительный на временных копиях исходника — гейт, зелёный по построению, не принимается"
  - "Проверка навески по ОБЪЯВЛЕНИЮ (умолчания параметров и `dependencies=` декоратора), а не обходом тела: упоминание в докстринге не считается"

requirements-completed: [ADMIN-06]

coverage:
  - id: D1
    description: "Под чужой личностью запрещены оплата и весь денежный путь, смена пароля, правка профиля, удаление учётной записи, повтор рассылки (D-22)"
    requirement: ADMIN-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_purchase_form_is_refused_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_password_change_is_refused_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_profile_change_is_refused_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_account_deletion_is_refused_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_send_retry_is_refused_but_the_history_reads"
        status: pass
    human_judgment: false
  - id: D2
    description: "Под чужой личностью разрешены чтение, синхронизация групп и включение/выключение — перечень объявлен, а не выведен из отсутствия запрета"
    requirement: ADMIN-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_group_sync_is_allowed_under_another_identity"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_group_toggle_is_allowed_under_another_identity"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_no_allowed_route_carries_the_dependency"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_every_allowed_route_carries_a_reason"
        status: pass
    human_judgment: false
  - id: D3
    description: "Машинный гейт обходит каждый изменяющий маршрут по AST; маршрут, добавленный будущей фазой и не попавший ни в одно из трёх множеств, роняет тест (D-23)"
    requirement: ADMIN-06
    verification:
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_every_mutating_route_is_classified"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_the_number_of_mutating_routes_is_the_declared_one"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_the_gate_imports_no_application_module"
        status: pass
    human_judgment: false
  - id: D4
    description: "Зубы гейта ДОКАЗАНЫ: снятие зависимости и добавление необъявленного маршрута оба роняют гейт; на неизменённом дереве он зелен"
    requirement: ADMIN-06
    verification:
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_control_negative_a_forbidden_route_without_the_dependency_reddens_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_control_negative_an_undeclared_new_route_reddens_the_completeness"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_impersonation_gate.py#test_control_positive_the_untouched_source_tree_keeps_the_gate_green"
        status: pass
      - kind: manual_procedural
        ref: "живая мутация боевого дерева: sed-удаление зависимости из app/pages/profile.py и добавление необъявленного маршрута — оба уронили гейт, обе мутации откачены через git checkout"
        status: pass
    human_judgment: false
  - id: D5
    description: "Вебхук платёжной системы, приходящий БЕЗ токена, зависимостью запрета не задет — приём денег по совершённым платежам не остановлен (D-53)"
    requirement: ADMIN-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_payment_webhook_without_a_token_is_not_refused"
        status: pass
    human_judgment: false
  - id: D6
    description: "Отказ под чужой личностью отличим от отказа по правам, и вложенная имперсонация запрещена"
    requirement: ADMIN-06
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_refusal_names_the_other_identity_and_not_missing_rights"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_nested_impersonation_is_refused"
        status: pass
    human_judgment: false
  - id: D7
    description: "Формулировка отказа понятна администратору в живом продукте и приводит его к нужному действию (выйти из чужой учётной записи)"
    verification: []
    human_judgment: true
    rationale: "Тест утверждает, что тексты РАЗЛИЧАЮТСЯ и что отказ называет чужую личность; понятен ли текст человеку под нагрузкой разбора инцидента — суждение, которого автоматика не выносит"

duration: 71min
completed: 2026-08-23
status: complete
---

# Phase 6 Plan 13: Запреты действий под чужой личностью Summary

**Запрет необратимого и денежного под чужой личностью закреплён ЗАВИСИМОСТЬЮ на маршруте, а полнота перечня — машинным гейтом, который обходит все 49 изменяющих маршрутов проекта по синтаксическому дереву и роняет сборку на маршруте, о котором решения не принимали.**

## Performance

- **Duration:** 71 min
- **Started:** 2026-08-23T10:20:00Z
- **Completed:** 2026-08-23T11:31:00Z
- **Tasks:** 3 of 3
- **Files modified:** 11 (10 изменено, 1 создан)

## Accomplishments

- **Запрет объявлен зависимостью, а не проверкой внутри обработчика.** `forbid_when_impersonating` отказывает ИСКЛЮЧЕНИЕМ (зависимость роутера своего значения никуда не отдаёт — «вернуть отказ» дало бы запрет, не срабатывающий ни на одном маршруте), пропускает запрос БЕЗ токена (вебхук ЮKassa токена не несёт, D-53) и не берёт сессию БД.
- **Форма закрепления — гибрид, и он вынужденный.** Денежные ИЗМЕНЯЮЩИЕ входы закрыты роутером целиком с обеих сторон; смена пароля (четыре шага), правка профиля, повтор отправки, выдача бесплатного доступа, удаление пользователя и вложенный вход — поимённо. Чисто пер-роутерной формы недостаточно: повтор отправки живёт в роутере истории, чтение которого разрешено и составляет смысл входа, а смена пароля — в роутере авторизации, который обязан оставаться открытым.
- **Полнота держится машиной, а не вниманием.** Гейт читает ИСХОДНИК 15 модулей обоих слоёв, находит 49 изменяющих объявлений и требует, чтобы каждое попало ровно в одно из трёх ОБЪЯВЛЕННЫХ множеств. Маршрут будущей фазы не попадёт никуда и уронит тест — вместо того чтобы оказаться разрешённым по умолчанию.
- **Зубы гейта доказаны, а не заявлены.** Три контроля (`-k control`) на временных копиях исходника плюс ЖИВАЯ мутация боевого дерева: снятие зависимости и добавление необъявленного маршрута оба уронили гейт, обе мутации откачены.

## Task Commits

1. **Задача 1: Зависимость запрета и её навеска** — `991d787` (test, RED) → `ee09e5a` (feat, GREEN)
2. **Задача 2: Машинный гейт** — `0eb65bc` (test)
3. **Задача 3: Доказанные зубы гейта** — `49ccbb3` (test)

## Files Created/Modified

- `app/dependencies.py` — `forbid_when_impersonating` + `IMPERSONATION_FORBIDDEN_DETAIL`
- `app/main.py` — JSON-денежный роутер закрыт целиком
- `app/pages/__init__.py` — `billing_money_router` закрыт целиком, чтение раздела оставлено открытым
- `app/pages/billing.py` — денежные изменяющие входы вынесены в `money_router`
- `app/pages/auth.py` — четыре шага восстановления пароля закрыты поимённо
- `app/pages/history.py` — закрыт ровно повтор отправки
- `app/pages/profile.py` — форма профиля закрыта целиком на вырост
- `app/pages/admin.py` — выдача бесплатного доступа, удаление пользователя, вложенный вход
- `tests/test_pages/test_impersonation_gate.py` — машинный гейт (749 строк, 11 тестов)
- `tests/test_pages/test_impersonation.py` — 11 сквозных утверждений (файл: 33 теста)
- `tests/test_pages/test_access_gate.py` — `billing_money_router` объявлен в `OPEN_ROUTERS`

## Decisions Made

**Страничный денежный роутер разделён надвое.** План предписывал закрыть его ЦЕЛИКОМ, но в нём живёт и `GET /billing`. Разделение сохраняет свойство, ради которого пер-роутерная форма и выбиралась («новый денежный маршрут закрыт по умолчанию»), не отнимая чтение.

**Форма профиля закрыта целиком, хотя правит сегодня только часовой пояс.** Отдельного маршрута смены адреса (D-22) в продукте нет; когда его заведут, естественное место ему здесь, а поле, добавленное в уже РАЗРЕШЁННЫЙ маршрут, гейт не заметил бы — маршрут-то объявлен. Часовой пояс к тому же определяет, в какое время уходят рассылки.

**Граница в админке проведена по обратимости и деньгам.** Права администратора читаются по действующему лицу (D-20), поэтому админка из-под имперсонации работает и решение нужно по каждой кнопке. Запрещены удаление пользователя (необратимо), выдача бесплатного доступа (деньги) и вложенный вход. Разрешены перезапуск воркера, снятие задачи и блокировка — обратимы и пишутся в журнал под идентификатором актора.

**Расписания разрешены.** Расписание — намерение отправить, обратимое выключением и удалением до срабатывания планировщика, а «включение/выключение» D-22 называет разрешённым прямо. Необратимый немедленный запуск в продукте один и запрещён. Маршрут «отправить сейчас», появись он, не попадёт ни в одно множество и уронит гейт.

**Зависимость в `history.py` импортируется модулем.** В файле она закрывает ровно один маршрут из двух, и это проверяемое свойство: импорт по имени добавил бы вторую строку с ним и сделал бы утверждение нечитаемым поиском. В коде это выписано, чтобы следующий читатель не «привёл к общему виду».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Навеска на страничный денежный роутер закрыла чтение раздела оплаты**

- **Found during:** Задача 1 (GREEN)
- **Issue:** План предписывал закрыть страничный денежный роутер ЦЕЛИКОМ. В `app/pages/billing.py` живут ДВА маршрута: `GET /billing` (чтение) и `POST /billing/subscribe` (покупка). Навеска на роутер закрыла и чтение: `/billing` начал отвечать 403 под чужой личностью, уронив `test_the_return_bar_is_present_in_every_section` и `test_the_bar_does_not_break_the_shell_layout` из плана 06-12. Содержательная цена больше тестовой: D-22 разрешает чтение прямо, а «я заплатил, а доступ не открылся» — типовое обращение, ответ на которое виден именно на этом экране.
- **Fix:** Денежные ИЗМЕНЯЮЩИЕ входы вынесены в отдельный `money_router` в том же модуле; чтение осталось в общем роутере. Запрет навешен на `money_router` целиком — свойство «маршрут, добавленный будущей фазой, закрыт по умолчанию» сохранено, а не потеряно: оно и было причиной пер-роутерной формы. Адреса маршрутов не изменились (оба роутера включаются без префикса).
- **Files modified:** `app/pages/billing.py`, `app/pages/__init__.py`, `tests/test_pages/test_access_gate.py`
- **Verification:** `uv run pytest tests/test_pages/test_impersonation.py tests/test_pages/test_access_gate.py -q` → 53 passed
- **Committed in:** `ee09e5a`

**2. [Rule 2 — Missing critical] Новый роутер потребовал решения в гейте доступа**

- **Found during:** Задача 1 (GREEN)
- **Issue:** `test_pages_gate_covers_exactly_the_declared_routers` покраснел на `billing_money_router` — ровно то поведение, ради которого гейт доступа и написан: новый роутер обязан получить решение «закрывает ли его истёкший доступ», а не умолчание.
- **Fix:** `billing_money_router` объявлен в `OPEN_ROUTERS` с выписанной причиной: обе половины раздела оплаты обязаны оставаться открытыми, иначе человек с истёкшим сроком не сможет заплатить (T-05.1-16).
- **Files modified:** `tests/test_pages/test_access_gate.py`
- **Verification:** `uv run pytest tests/test_pages/test_access_gate.py -q` → зелёный
- **Committed in:** `ee09e5a`

---

**Total deviations:** 2 auto-fixed (1 × Rule 1, 1 × Rule 2)
**Impact on plan:** Обе правки сохраняют намерение плана и уточняют его букву. Расширения области нет: закрыто ровно то, что называет D-22.

## Issues Encountered

**Пробел в перечне D-22: маршрута смены АДРЕСА в продукте не существует.** D-22 называет смену адреса запрещённой, но отдельного маршрута у неё нет — есть только путь восстановления пароля по почте. Закрыт весь этот путь и, на вырост, форма профиля. Записано и в коде, и в гейте: когда поле адреса заведут, оно почти наверняка приедет в форму профиля, которая уже закрыта.

**Известное падение, к плану отношения не имеющее.** `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` падает в полном прогоне и проходит в одиночку (проверено: `1 passed`). Пред-существующее, записано в `deferred-items.md` четырьмя предыдущими планами. Не диагностировалось и не чинилось.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_impersonation_gate.py -q` | 11 passed (включая 3 контроля) |
| `uv run pytest tests/test_pages/test_impersonation_gate.py -q -k control` | 3 passed, 8 deselected |
| `uv run pytest tests/test_pages/test_impersonation.py -q` | 33 passed (требовалось ≥ 28) |
| `uv run pytest tests/test_pages/test_access_gate.py -q` | зелёный — гейт доступа не сломан |
| `uv run pytest tests/test_pages tests/test_routes -q` | 1263 passed, 1 failed (известное) |
| `just test` (`uv run pytest tests/ -q`) | **2096 passed, 1 failed** — только известное пред-существующее |

Критерии приёмки по grep: `def forbid_when_impersonating` найдено; `app/main.py` = 2 и `app/pages/__init__.py` = 2; `app/pages/auth.py` = 5 (≥ 2); `app/pages/history.py` = **ровно 1**; три множества в гейте — 18 упоминаний (≥ 3); `ast.parse` — 3 (≥ 1); файл гейта 749 строк (≥ 180).

## Порядок выката

**Механика входа под пользователем НЕ ВЫКАТЫВАЕТСЯ НА БОЙ РАНЬШЕ ЭТОГО ПЛАНА.** План 06-12 отгрузил вход, возврат и живую кнопку «Войти под пользователем» на карточке пользователя; до приземления настоящего плана администратор под чужой личностью мог необратимо отправить рассылку в чужие группы и пройти денежным путём от чужого имени. Отменить отправленное не может ни администратор, ни владелец учётной записи, и откатом кода оно не возвращается. Поэтому ветка фазы 6 не сливается и не деплоится частично: 06-12 и 06-13 едут вместе либо не едут вовсе.

`.planning/WINDOWS.md`, запись 4 (`unmet-truth`, статус `open`) фиксирует ровно этот запрет и названа закрывающейся приземлением 06-13. **Условие закрытия выполнено кодом этого плана**, но сама запись оставлена открытой намеренно: она про состояние СЛИЯНИЯ ветки, которым исполнитель плана не управляет. Закрыть её следует оркестратору при слиянии фазы.

## User Setup Required

None — внешних сервисов план не трогает, установок пакетов нет (разбор дерева — стандартная библиотека).

## Next Phase Readiness

ADMIN-06 закрыт целиком: механику дал план 06-12, запреты и их машинное закрепление — этот.

**Что наследует следующая фаза.** Любой новый изменяющий маршрут обязан получить решение в `tests/test_pages/test_impersonation_gate.py` — иначе суита краснеет с сообщением, объясняющим, что делать. Это относится и к маршрутам, не имеющим отношения к имперсонации: цена дисциплины — одна строка с причиной, цена её отсутствия — денежный или разрушительный маршрут, разрешённый по умолчанию.

**Известная граница, которую стоит держать в виду.** Гейт видит маршрут, а не ПОЛЕ. Поле смены адреса, добавленное в уже разрешённый маршрут, он бы не заметил — поэтому форма профиля закрыта целиком заранее. Тот же приём понадобится, если разрешённый маршрут начнёт делать что-то из перечня D-22.

## Self-Check: PASSED

- `tests/test_pages/test_impersonation_gate.py` — существует на диске (749 строк)
- `.planning/phases/06-admin-panel/06-13-SUMMARY.md` — этот файл
- Коммиты `991d787`, `ee09e5a`, `0eb65bc`, `49ccbb3` — присутствуют в `git log`
- Все `<verify>` каждой задачи прогнаны; результаты в таблице выше
- Все `<acceptance_criteria>` трёх задач проверены поимённо
- Заглушек нет; пропущенных тестов нет; непрогнанных `<verify>` нет

---
*Phase: 06-admin-panel*
*Completed: 2026-08-23*
