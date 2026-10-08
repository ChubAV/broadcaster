---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 11
subsystem: testing
tags: [htmx, hx-push-url, response-form, ast, pytest, qual-04, d-11, d-12, d-13, def-09-04]

requires:
  - phase: 15
    provides: "план 15-02 — инвентарь мест письма `test_form_inventory.py` (49/27, ключ `путь#порядковый_номер`)"
  - phase: 15
    provides: "план 15-10 — связка «форма-триггер → модалка»: 18 триггеров дают обработчиков формы `components/modal.html#0`"
  - phase: 14
    provides: "`FRAGMENT_RESPONSE_HANDLERS` (25 из 37) с обоснованием на каждую запись и правилом согласованности; `_hands_a_fragment` (план 14-02)"
provides:
  - "реестр решений `hx-push-url` по трём случаям (`PUSH_URL_DECISIONS`, 37 строк), выведенный из формы ответа и сверяемый с выводом; биекция с 49 местами письма"
  - "дуальность читается по вызову: `DUAL_BRANCH_HANDLERS` = 19 (20 спорных мест), все — случай третий"
  - "ноль атрибута в разметке утверждён В ПАРЕ с полнотой реестра (D-12); один отправитель `HX-Push-Url`, летопись 2 → 1"
  - "запрет D-13 на местах обработчиков «изменяет данные» с двумя контролями, различающими предмет; граница `DEF-09-04` названа, сторож стоит, вселенная G-2 на GET НЕ расширена"
  - "решение владельца по 19 спорным формам — `case-three-server-header` — записано полями в `15-FORM-DECISIONS.md` и в `DUAL_BRANCH_OWNER_DECISIONS` со сверкой ветви и случая"
affects: [15-14, phase-15-verification, QUAL-04, v2.1-milestone-audit]

actuals:
  tokens: 30309
  tasks: 3
  commits: 7
plan_head_before: c64089ed7cac6acb1b39c3306728ee6d76964105

tech-stack:
  added: []
  patterns:
    - "случай конвенции выводится функцией от исходников (`_push_url_case_for`) и сверяется с записанным; реестр — запись, вывод — проверка"
    - "переходная ветка — это ВЫЗОВ выхода слоя ответа (`respond` без `fragment=`, `redirect_internal`, `redirect_external`), снятый `ast`, а не имя в тексте"
    - "ответ владельца на чекпойнте ложится летописью рядом с привязкой «ожидает», а не поверх неё; ветвь владельца переводится в случай реестра и сверяется с ним"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-FORM-DECISIONS.md
  modified:
    - tests/test_pages/test_htmx_gates.py

key-decisions:
  - "Признак переходной ветки — вызов `respond` без аргумента фрагмента, `redirect_internal`, `redirect_external`; буква плана (`respond_screen`/`location_response`) дала бы 8 дуальных, все из авторизации, и ни одного из четырёх названных"
  - "Дуальных обработчиков 19 (20 спорных мест); 12 обработчиков уходят только переходом и по порядку правил — случай третий; случай первый — 0 обработчиков, 0 мест"
  - "Владелец (`chubav`, 2026-09-24, AskUserQuestion в /gsd-execute-phase 15) выбрал ОДНУ ветвь на все 19 дуальных: `case-three-server-header`; своих слов обоснования не дал"
  - "Шесть экранов кода авторизации (случай второй: у шага нет своего адреса) владельцу не выносились и ответом не решены"
  - "`status: subject` артефакта сохранён: поля владельца встают после шапки замера, как `permit_*` в `10-PROHIBITIONS-SUBJECT.md`, и вердиктом не являются"

patterns-established:
  - "Спорные случаи выносятся владельцу узким машинным перечнем; неспорные решает Claude по D-11 и подписи не просит"

requirements-completed: [QUAL-04]

coverage:
  - id: D1
    description: "Правило классификации трёх случаев объявлено шапкой группы выше первого числа; дуальность побеждает наличие фрагмента; реестр полон по 37 POST-обработчикам и совпадает с выводом из формы ответа"
    requirement: "QUAL-04"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly -k push_url (24 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_decisions_agree_with_the_response_form"
        status: pass
    human_judgment: false
  - id: D2
    description: "19 дуальных обработчиков (включая четыре названных обоснованиями фрагментных) отнесены к третьему случаю; отнесение к первому/второму называется"
    requirement: "QUAL-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_dual_branch_handlers_are_case_three"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_push_url_a_dual_handler_filed_as_case_two_is_named"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ноль `hx-push-url` в разметке утверждён в паре с полнотой реестра по 49 местам письма; отправитель `HX-Push-Url` один, упоминаний в прозе два"
    requirement: "QUAL-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_zero_in_markup_is_a_decision_not_a_gap"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_header_has_exactly_one_sender_and_two_prose_mentions"
        status: pass
    human_judgment: false
  - id: D4
    description: "Запрет D-13 на местах обработчиков «изменяет данные» читает `FRAGMENT_RESPONSE_HANDLERS`, доказан двумя контролями; сторож границы `DEF-09-04` держит вселенную G-2 на изменяющих методах"
    requirement: "QUAL-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_forbidden_on_places_of_changes_data_handlers"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_push_url_forbidden_stays_silent_outside_the_changes_data_list"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_g2_universe_holds_only_changing_methods"
        status: pass
    human_judgment: false
  - id: D5
    description: "Решение владельца по 19 спорным формам записано полями в артефакте и в реестре; ветвь сверяется со случаем реестра, контроль называет противоречие"
    requirement: "QUAL-04"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_push_url_owner_branch_agrees_with_the_registry_case"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_push_url_owner_branch_contradicting_the_registry_is_named"
        status: pass
      - kind: other
        ref: "grep -c '^status: subject' 15-FORM-DECISIONS.md (1)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Верность конвенции и поведение адреса, Back и F5 в браузере на переведённых экранах"
    requirement: "QUAL-04"
    verification: []
    human_judgment: true
    rationale: "Группа утверждает, что решение ЗАПИСАНО и выведено, а не что оно ВЕРНО; поведение в браузере — пункт 7 ручного обхода, закрытый Фазой 11 и принимаемый её записью по D-15"

duration: 2h 52m
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 11: решения `hx-push-url` по каждому месту письма — Summary

**Реестр трёх случаев `hx-push-url` на 37 POST-обработчиков и 49 мест письма, выведенный `ast`-разбором формы ответа, где дуальность (19 обработчиков, 20 мест) побеждает наличие фрагмента; запрет D-13 с двумя контролями, сторож границы `DEF-09-04` без расширения G-2, и ветвь владельца `case-three-server-header` на все спорные формы, записанная полями.**

## Performance

- **Duration:** 2h 52m (включает ожидание владельца на чекпойнте задачи 3)
- **Started:** 2026-09-24T13:21:11Z
- **Completed:** 2026-09-24T16:13:52Z
- **Tasks:** 3 (задачи 1–2 и предчекпойнтная часть задачи 3 — первым исполнителем; запись ответа и закрытие — исполнителем-продолжением)
- **Files modified:** 2

## Accomplishments

- Реестр `PUSH_URL_DECISIONS` (37 строк, ключ `путь/файл.py::имя_функции`) сверяется со случаем, который правило шапки выводит из формы ответа; биекция с 49 местами письма плана 15-02.
- Дуальность читается по вызову: 19 дуальных обработчиков, все случай третий, включая четыре, названные обоснованиями `FRAGMENT_RESPONSE_HANDLERS` (`ads_update`, `schedules_create`, `schedules_delete`, `schedules_update`).
- Ноль `hx-push-url` в `app/templates/` утверждён одним правилом с полнотой реестра (D-12).
- Один реальный отправитель `HX-Push-Url` (`app/pages/ads.py:783`), два упоминания в прозе; летопись 2 → 1.
- Запрет D-13 стоит на чужом поддерживаемом перечне; `DEF-09-04` выписан четырьмя пунктами, сторож на месте, вселенная G-2 на GET НЕ расширена, адресат передан вехе.
- Ответ владельца по 19 спорным формам записан в `15-FORM-DECISIONS.md` (поля `owner_*`, колонка «Ветвь владельца») и в `DUAL_BRANCH_OWNER_DECISIONS` со сверкой ветви и случая.

## Правило классификации (дословно из шапки группы)

> • обработчик, имеющий ПЕРЕХОДНУЮ ВЕТКУ, → СЛУЧАЙ ТРЕТИЙ: решение об адресе принадлежит ветке,
> то есть СЕРВЕРУ, и адрес приходит заголовком ответа;
> • обработчик в `FRAGMENT_RESPONSE_HANDLERS` БЕЗ переходной ветки → СЛУЧАЙ ВТОРОЙ: меняются
> только данные, атрибута нет, и это ЗАПИСАННОЕ решение, а не пробел;
> • обработчик, меняющий ЧТО показано и не дуальный (ни фрагмента, ни перехода — адрес самого
> запроса и есть адрес нового экрана), → СЛУЧАЙ ПЕРВЫЙ: `hx-push-url="true"`.
>
> ⚠️ ДУАЛЬНОСТЬ ПОБЕЖДАЕТ НАЛИЧИЕ ФРАГМЕНТА. `hx-push-url` — СТАТИЧЕСКИЙ атрибут разметки и по
> ветке ответа не меняется. ДУАЛЬНЫЙ обработчик стои́т в `FRAGMENT_RESPONSE_HANDLERS` И имеет
> переходную ветку. Его форма с `hx-push-url="true"` сменила бы адрес и во фрагментной ветке,
> где показанное не менялось.

## Дуальные обработчики (19)

`account_groups.py::account_groups_delete`, `account_groups.py::account_groups_toggle`,
`accounts.py::accounts_connect_max_start`, `accounts.py::accounts_connect_tg_user_qr_status`,
`accounts.py::accounts_connect_tg_user_refresh_qr`, `accounts.py::accounts_connect_tg_user_start_qr`,
`accounts.py::accounts_connect_tg_user_verify_2fa`, `admin.py::admin_toggle_block`,
`admin.py::admin_toggle_free_access`, `ads.py::ads_create`, `ads.py::ads_images_upload`,
`ads.py::ads_update`, `auth.py::forgot_password_reset`, `auth.py::register_complete`,
`profile.py::profile_post`, `schedules.py::schedules_create`, `schedules.py::schedules_delete`,
`schedules.py::schedules_toggle`, `schedules.py::schedules_update` (все в `app/pages/`).

## Летопись `2 → 1` (дословно из гейта)

> ЛЕТОПИСЬ ЧИСЛА ОТПРАВИТЕЛЕЙ `HX-Push-Url`: 2 → 1 (Фаза 15, план 15-11). `15-CONTEXT.md` D-12
> говорит: «`HX-Push-Url` в `app/` — 2». ⚠️ ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей
> записи он был верным, и правится не он, а числа, которые он пережил. Сеть «вхождения имени
> заголовка» посчитала вместе с отправителем прозу. Новое число снято РАЗБОРОМ `ast` ПО
> ПРИСВАИВАНИЯМ, а не грепом по имени заголовка: это обход `_header_writes` гейта G-13 с отбором
> по имени. Реальный отправитель ОДИН — `app/pages/ads.py:783`, присваивание
> `response.headers["HX-Push-Url"] = f"/ads/{saved.id}/edit"` в сборщике `_fragment`. Упоминаний
> в ПРОЗЕ два: докстринг `app/pages/htmx.py:694` и комментарий шаблона
> `app/templates/ads/includes/autosave_response.html:146`. Запись контекста НЕ ПРАВИТСЯ.

## Вопрос владельцу и его ответ

**Вопрос (дословно, как записан в `15-FORM-DECISIONS.md` §2):**

> У 19 форм из таблицы выше поведение двойное. Обычно форма меняет кусок страницы на месте, и
> адрес в строке браузера при этом меняться не должен. В других исходах та же форма уводит на
> другой экран: сессия истекла, расписание было последним, объявление удалено, регистрация
> завершена. Как записать эти формы?
>
> **`case-three-server-header`** — «адрес решает сервер» (так выведено машинно). Что увидит
> человек: пока кусок меняется на месте, в строке прежний адрес, и «Назад» ведёт туда, откуда он
> пришёл. Когда форма уводит на другой экран, в строке адрес нового экрана, и F5 показывает тот
> экран, который он видит. Нового кода не нужно: замер показал, что так уже работает сегодня.
> При уходе сервер присылает адрес, и браузер сам записывает его в историю.
>
> **`case-two-no-attribute`** — «атрибута нет». Что увидит человек сегодня: то же самое, что в
> первом варианте. Атрибута на форме нет в обоих вариантах, а адрес при уходе всё равно приходит
> от сервера. Чтобы этот вариант значил буквально «адрес не меняется ни в одной ветке», пришлось
> бы запретить серверу записывать адрес при уходе. Тогда после ухода на другой экран в строке
> останется прежний адрес, и F5 вернёт человека на прежний экран, а не на тот, который он видит.
>
> Можно ответить одной строкой на все 19, по группам А/Б/В или по каждой форме.

Вопрос задал оркестратор через AskUserQuestion; исполнителю передан выбранный вариант в той
формулировке, в какой он был предъявлен. Полный текст вопроса оркестратора исполнителю не
передан, поэтому его совпадение с записанным выше не проверялось.

**Ответ (полями):**

| Поле | Значение |
|---|---|
| Кто решил | владелец (`chubav`) |
| Когда | 2026-09-24 |
| Канал | AskUserQuestion в `/gsd-execute-phase 15` |
| Ветвь | `case-three-server-header` — одна на все 19 дуальных обработчиков (все 20 спорных мест) |
| Основание | выбран вариант, предъявленный как «Сервер решает — адрес меняется только когда сервер уводит человека на другой экран. Так это работает сегодня, и нового кода не нужно»; своих слов обоснования владелец не дал |
| Не выносилось | шесть экранов кода авторизации (случай второй: `register_step#0`, `register_verify_step#0/#1`, `forgot_password_step#0`, `forgot_password_verify_step#0/#1`) |

Нового кода в `app/` ответ не требует: адрес перехода уже приходит заголовком `HX-Location`
или `HX-Redirect` (замер htmx 2.0.10).

## `DEF-09-04` и вселенная G-2

Вселенная гейта G-2 на GET-маршруты **НЕ расширена**. Граница `DEF-09-04` выписана в докстринг
четырьмя пунктами (невидимость GET-маршрута в обе стороны; граница названа и не расширена;
расширение — решение ВЕХИ, а не плана, и план, расширивший её, нарушил бы запись самого долга;
адресат передан вехе v2.1 по имени). Сторож `test_push_url_g2_universe_holds_only_changing_methods`
краснеет на пришедшем GET-маршруте и называет его. Ни один коммит плана не удалил ни одной строки
`test_htmx_gates.py` (замер против базы `c64089ed`: 0).

## Task Commits

1. **Задача 1: реестр решений трёх случаев** — `d992926d` (test, RED), `aa54bd00` (feat, GREEN)
2. **Задача 2: запрет D-13 и граница `DEF-09-04` со сторожем** — `39d2e945` (test, RED), `5900c2cc` (feat, GREEN)
3. **Задача 3: спорные формы — решение владельца** — `45a86b78` (docs, предмет до чекпойнта), `3620e947` (feat, ветвь владельца в реестре), `5ac7201e` (docs, ответ владельца полями в артефакте)

**Plan metadata:** коммит этой сводки (docs) и коммит учёта STATE/ROADMAP.

## Files Created/Modified

- `tests/test_pages/test_htmx_gates.py` — группа `hx-push-url`: реестр, дуальность, отправители, ноль разметки, запрет D-13, сторож `DEF-09-04`, ветвь владельца со сверкой; только добавления.
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-FORM-DECISIONS.md` — сводка по 49 местам письма, таблица 19 спорных форм, вопрос владельцу дословно, ответ полями; `status: subject`.

## Decisions Made

- Решение владельца: `case-three-server-header` на все 19 дуальных обработчиков. Основание записано так, как дано: выбор варианта, своих слов нет.
- Ответ записан летописью рядом с привязкой «ожидает решения владельца», а не поверх неё: в гейте прежняя привязка осталась, новая встала ниже (только добавления); в артефакте прежнее название раздела оставлено примечанием.
- Добавлено правило сверки ветви владельца со случаем реестра и контроль к нему: без них ответ владельца был бы данными, которые ничто не читает.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Признак переходной ветки по букве плана был неверен**
- **Found during:** Задача 1
- **Issue:** план назвал признаком вызовы `respond_screen` и `location_response`. `location_response` не зовёт напрямую ни один POST-обработчик (его зовёт сам `respond` без фрагмента), а `respond_screen` этот же файл засчитывает передачей фрагмента (`_hands_a_fragment`, план 14-02). По букве плана вышло бы 8 дуальных, все из авторизации, и ни одного из четырёх, названных планом.
- **Fix:** признак — вызов `respond` без `fragment=`, `redirect_internal`, `redirect_external` (`TRANSITION_BRANCH_CALLS`); 19 дуальных, все четыре названных среди них. Поправка названа в докстринге (идиома D-30/D-32).
- **Files modified:** tests/test_pages/test_htmx_gates.py
- **Committed in:** d992926d / aa54bd00

**2. [Rule 1 - Bug] Обработчики только с переходом и пустой первый случай**
- **Found during:** Задача 1
- **Issue:** правило плана не называло обработчиков, которые уходят ТОЛЬКО переходом (12).
- **Fix:** по порядку правил они — случай третий; случай первый — 0 обработчиков, 0 мест, что согласуется с нулём атрибута в разметке.
- **Committed in:** aa54bd00

**3. [Rule 1 - Bug] Цены вариантов чекпойнта поправлены по замеру htmx 2.0.10**
- **Found during:** Задача 3
- **Issue:** план записал цену третьего случая как «новый код отправителя в каждом обработчике», а второго — как «прежний адрес после перехода». На `HX-Location` htmx ставит `push ?? "true"` раньше, чем прочтёт собственную настройку формы; `HX-Redirect` — полная загрузка. Ни одна из цен сегодня не наступает.
- **Fix:** цены в вопросе и в артефакте записаны по замеру; поправка названа в артефакте.
- **Committed in:** 45a86b78

**4. [Форма артефакта] Таблица спорных форм — строка на обработчика**
- **Found during:** Задача 3
- **Issue:** критерий приёмки требует, чтобы число строк спорных форм равнялось `DUAL_BRANCH_HANDLERS_DECLARED` (19), а спорных мест 20 (панель подтверждения входит в два перечня).
- **Fix:** 19 строк по обработчикам, в колонке мест — все 20.
- **Committed in:** 45a86b78

**5. [Добавлено сверх плана] Контроли и дословная фраза**
- **Found during:** Задачи 1–3
- **Issue/Fix:** семь дополнительных контролей от вакуума в задачах 1–2; одна лишняя строка несёт дословную фразу `ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ`, которая иначе переносилась бы. В задаче 3 добавлены правило сверки ветви владельца со случаем реестра и контроль к нему (+2 теста).
- **Committed in:** aa54bd00, 5900c2cc, 3620e947

**Устаревшие координаты плана (летопись, не правка плана):** отправитель `HX-Push-Url` — `app/pages/ads.py:783` в `_fragment` (план: `:775`); `DEF-09-04` — `REQUIREMENTS.md:433` (план: `:430`); строки `test_htmx_gates.py` сдвинуты на +20 новыми импортами; число отправителей 2 → 1 — летописью, запись контекста не правилась.

---

**Total deviations:** 3 auto-fixed (Rule 1) + 2 form/extension deviations.
**Impact on plan:** поправка №1 несущая: без неё правило по букве плана не нашло бы ни одного из четырёх дуальных, ради которых план написан. Остальные — точность записи. Кода в `app/` план не менял.

## TDD Gate Compliance

- Задача 1: RED `d992926d` → GREEN `aa54bd00`; улика RED — `RED_EVIDENCE_OK` / `target_test_failed` (прогон `--junit-xml`, сведённый в TAP; файлы улики были в черновике первого исполнителя и могли не сохраниться — здесь цитируется вердикт, а не файл).
- Задача 2: RED `39d2e945` → GREEN `5900c2cc`; улика RED — `RED_EVIDENCE_OK` / `target_test_failed`, так же.
- Задача 3 — `checkpoint:decision`, не TDD. Правило сверки ветви владельца (`3620e947`) зелёно с первого прогона: оно сверяет записанные данные, а не требует поведения от кода; от вакуума его отделяет контроль `test_control_push_url_owner_branch_contradicting_the_registry_is_named`. Отдельного RED-коммита у него нет.
- REFACTOR-коммитов нет.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly -k push_url` | 24 passed (до плана — 0; после задач 1–2 — 22) |
| `uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly` | 84 passed (до плана — 60; до ответа владельца — 82) |
| `tests/test_templates/` + `test_htmx_post_pairs.py` + `test_htmx_gates.py` | 526 passed (до плана — 502; до ответа — 524) |
| `uv run pytest tests/test_planning/ -q -p no:randomly` | 78 passed |
| `grep -c 'DEF-09-04' tests/test_pages/test_htmx_gates.py` | ≥ 1 |
| `grep -c '^status: subject' 15-FORM-DECISIONS.md` | 1 |
| строка `status` содержит `passed`/`complete` | 0 |
| удалённые строки `test_htmx_gates.py` против базы `c64089ed` | 0 |

Прогон `tests/test_pages/ tests/test_templates/` целиком из плана заменён набором сквозных гейтов выше (указание оркестратора: полную суиту он гонит после волны; план 15-14 обещает её отдельно).

`requirements.ready-ids` (только чтение): `1/1 requirement(s) ready to mark complete` для QUAL-04. **QUAL-04 НЕ отмечен выполненным** в `REQUIREMENTS.md` — по указанию оркестратора он остаётся Pending до проверки фазы.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- QUAL-04 записан по всем 49 местам письма; решение по спорным формам принято владельцем. Верность конвенции в браузере (адрес, Back, F5) — пункт 7 ручного обхода, принимаемый записью Фазы 11 по D-15.
- Шесть экранов кода авторизации (случай второй) владельцу не выносились; если их сочтут спорными, их можно вынести отдельно.
- Расширение вселенной G-2 на GET-маршруты (`DEF-09-04`) — за аудитом вехи v2.1, не за планом.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED
