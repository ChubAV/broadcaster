---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 19
subsystem: ui
tags: [css, jinja, a11y, wcag, banner-dismiss, focus-ring, aria-label, in-04, GATE-09]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-07: два различимых имени органа снятия и компенсация перекрытия; запись следствия смещения второй заготовки и её сторож; план 15-05: правило обвода фокуса органа снятия; план 15-14 — предшественник по `depends_on`"
provides:
  - "две записи «⚠️ ПРИНЯТОЕ СЛЕДСТВИЕ ВЕТВИ A» в `app/static/css/app.css` (потеря фокуса при снятии клавишей; роль «флажок») с основанием Г-3"
  - "сторож `test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed` и контроль `test_control_a_silently_fixed_or_dropped_consequence_reddens`"
  - "имена органов «Отказ сервера: скрыть сообщение» / «Обрыв связи: скрыть сообщение»; `BANNER_DISMISS_ACCESSIBLE_NAMES`, `BANNER_DISMISS_SUBJECT_MARKS`, `BANNER_DISMISS_LEADING_WORDS`; правило `test_each_accessible_name_leads_with_its_own_failure`"
  - "непрозрачный токен `--focus-ring: rgb(196, 132, 252)`; правило `test_the_focus_ring_token_is_opaque_enough_for_non_text_contrast` (альфа не ниже 0.7)"
  - "датированная поправка арифметики шага стопки (поле набора 346 → 322px); ссылка по цитате вместо «строки 1255-1258» (IN-04, половина `app.css`)"
affects: [15-UAT У-8, phase-15-verification, GATE-09]

actuals:
  tokens: 6240
  tasks: 3
  commits: 6
plan_head_before: 039325d29d7af8cee568491e5c8537d783ce4fcd

tech-stack:
  added: []
  patterns:
    - "принятое следствие записывается в исходнике с основанием владельца и стережётся правилом, которое краснеет и на молчаливой починке, и на снятии записи"
    - "указатель на абзац — по его открывающим словам и цитате, а не по номерам строк; прежний указатель остаётся летописью"

key-files:
  created:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-19-SUMMARY.md
  modified:
    - app/static/css/app.css
    - app/templates/includes/htmx_error_banner.html
    - tests/test_templates/test_banner_dismiss.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "15-19: Г-3 исполнено записью, а не починкой. Механизм ветви `A` (CSS-флажок, `:has(> .banner-dismiss:checked) { display: none; }`, ноль новых обработчиков) не тронут; оба следствия записаны принятыми рядом со следствием смещения второй заготовки, и их стережёт правило с контролями"
  - "15-19: признак аварии стоит первым словом имени органа — «Отказ сервера: скрыть сообщение» / «Обрыв связи: скрыть сообщение»; признаки предмета переведены в именительный падеж («Отказ сервера», «Обрыв связи») тем же коммитом, что и имена"
  - "15-19: токен `--focus-ring` непрозрачен; правило утверждает НЕПРОЗРАЧНОСТЬ (альфа не ниже 0.7), а не контраст — контраст зависит от фона, смешанного `color-mix`, и остаётся шагу У-8"
  - "15-19: общий префикс прежних имён замерен как 21 знак — имена расходятся на 22-м (UI-ревью пишет «22»); в летопись записано замеренное"

patterns-established:
  - "Принятое следствие = запись в исходнике с основанием владельца + сторож, краснеющий на починке и на снятии записи"

requirements-completed: [GATE-09]

coverage:
  - id: D1
    description: "Потеря фокуса при снятии клавишей и роль «флажок» записаны в `app.css` принятыми следствиями ветви `A` с основанием Г-3; сторож краснеет на `<button>`, на вырезанной записи и на ушедшем правиле скрытия"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_control_a_silently_fixed_or_dropped_consequence_reddens"
        status: pass
      - kind: unit
        ref: "RED до записи: FAILED …::test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed, 1 failed (check tdd-red-evidence → RED_EVIDENCE_OK)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Имена органов начинаются с различающего слова; тексты плашек, идентификаторы и однострочность узла обрыва связи не тронуты"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_each_accessible_name_leads_with_its_own_failure"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py (весь модуль, в прогоне 1407 passed): правило строки узла обрыва связи и правило органа снятия по `BANNER_DISMISS_ACCESSIBLE_NAMES`"
        status: pass
      - kind: other
        ref: "сличение диффа шаблона: две строки узлов после вырезания `aria-label=\"…\"` равны посимвольно, аргументы `alert(...)` тождественны"
        status: pass
    human_judgment: false
  - id: D3
    description: "Токен обвода фокуса непрозрачен; правило утверждает альфу не ниже 0.7"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_the_focus_ring_token_is_opaque_enough_for_non_text_contrast"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_control_a_half_transparent_focus_ring_reddens"
        status: pass
    human_judgment: false
  - id: D4
    description: "Видимость обвода на настоящем экране, место, куда падает фокус после снятия клавишей, и то, различает ли скринридер имена на слух"
    verification: []
    human_judgment: true
    rationale: "В суите нет движка раскладки, дерева доступности и браузерного привода; это шаг У-8 обхода `15-UAT.md`, и отметки там ставит человек"
  - id: D5
    description: "Датированная поправка арифметики шага стопки (322px) и ссылка по цитате вместо номеров строк (IN-04)"
    verification:
      - kind: other
        ref: "grep -c 'ПОПРАВКА 2026-09-25' app/static/css/app.css → 1; grep -c '346px' → 2; grep 'строки 1255-1258' → одна строка, и в ней «Летопись указателя: прежде»"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_the_stack_step_clears_the_tallest_first_banner (в прогоне 1407 passed)"
        status: pass
    human_judgment: false

duration: 46min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 19: Орган снятия плашки — принятые следствия ветви A, имена с первого слова, непрозрачный обвод Summary

**Потеря фокуса и роль «флажок» записаны в `app.css` принятыми следствиями ветви `A` (Г-3) со сторожем, который краснеет и на починке, и на снятии записи. Органы названы «Отказ сервера: скрыть сообщение» / «Обрыв связи: скрыть сообщение». Токен `--focus-ring` стал непрозрачным `rgb(196, 132, 252)`, и правило держит его альфу не ниже 0.7. Механизм снятия не тронут.**

## Performance

- **Duration:** 46 min (из них около 36 мин — два прогона гейтов, читающих `app.css`: 14 и 22 мин)
- **Started:** 2026-09-25T07:40:10Z
- **Completed:** 2026-09-25T08:26:52Z
- **Tasks:** 3
- **Files modified:** 4 (`app.css`, шаблон плашки, `test_banner_dismiss.py`, `test_htmx_markup_gates.py`: последний — отклонение, см. ниже)

## Accomplishments

- **Г-3, приоритет 1 UI-ревью.** Сразу после записи о смещении второй заготовки в `app.css` стоят две записи «⚠️ ПРИНЯТОЕ СЛЕДСТВИЕ ВЕТВИ A». Первая — «СНЯТИЕ КЛАВИШЕЙ ТЕРЯЕТ ФОКУС»: пробел скрывает всю стопку через `display: none`, фокус падает на `<body>` (WCAG 2.4.3), а Enter флажок не переключает. Вторая — «ОРГАН ОБЪЯВЛЯЕТСЯ ФЛАЖКОМ»: ролевая половина D-18.3 не починена. Каждая запись дословно называет основание: «решение владельца `chubav` 2026-09-25 (Г-3, «записать следствием»)». Там же сказано, что починка — это НОВОЕ решение владельца.
- **Сторож.** Он проверяет, что обе записи на месте и называют основание, что каждый орган остаётся `<input type="checkbox">`, что скрытие — ровно `display: none` по `.failure-stack:has(> .banner-dismiss:checked)` и что регистраций обработчика по-прежнему 3. Контроль на синтетических копиях проверяет три случая: орган `<button>` краснеет и называется в отказе; каждая из двух записей, вырезанная из текста, краснеет; снятое правило скрытия краснеет. Сторож смещения `test_boundary_the_open_banner_top_consequence_is_guarded_not_fixed` зелен без правки.
- **IN-04 (половина `app.css`).** Комментарий компенсации ссылается на абзац стопки по его открывающим словам («⚠️ ГРАНИЦА ДОКАЗАННОГО НАЗВАНА ЗДЕСЬ, А НЕ ОСТАВЛЕНА ЧИТАТЕЛЮ: правила утверждают ОБЪЯВЛЕНИЯ этой таблицы») и по цитате. Прежний указатель «(строки 1255-1258)» оставлен летописью.
- **Пункт 7.** Органы теперь называются «Отказ сервера: скрыть сообщение» и «Обрыв связи: скрыть сообщение». `BANNER_DISMISS_ACCESSIBLE_NAMES` и признаки предмета обновлены в том же коммите. Новое правило требует, чтобы первое слово имени было признаком своей аварии и чтобы первые слова двух органов различались. Летопись прежних имён записана в тесте и в комментарии шаблона.
- **Пункт 6.** Рядом со словами «поле набора 346px» стоит датированная поправка: 376 − 2 − 14 − 38 = 322px. Текст плашки (55 знаков) укладывается в две строки, третья строка остаётся запасом, 96px достаточно. Старое число не стёрто.
- **Пункт 5.** Токен теперь `--focus-ring: rgb(196, 132, 252)`. Прежнее значение `rgba(196, 132, 252, .5)` названо летописью у токена. Правило допускает `#rgb`/`#rrggbb`, `rgb(r, g, b)`, `rgba(…, a)` и `rgb(r g b / a)` с альфой не ниже 0.7. Контроль: альфа .5 краснеет и называет объявление, а .7, `#c484fc` и `rgb(… / 100%)` проходят.

## Пересчёт поля набора (UI-ревью, пункт 6)

Слагаемые прочитаны из таблицы: `.alert { padding: 11px 14px; border: 1px solid … }`, `.failure-stack > .alert { padding-right: 38px; }`, ширина заготовки `min(560px, calc(100% - 24px))`. Самое узкое объявленное окно — медиазапрос 400px, где ширина плашки 376px. Поле набора: 376 − 2 (рамка) − 14 (отступ слева) − 38 (компенсация справа) = **322px**, как и в ревью. Текст «Действие не выполнено. Попробуйте ещё раз через минуту.» — 55 знаков, при кегле 13px это ≈370–400px набора (оценка, не замер отрисовки). На две строки есть 644px, так что текст занимает две строки. Третья строка остаётся запасом: 82.5 + 8 = 90.5 ≤ 96px.

## Потребители токена `--focus-ring` (16)

`outline: 2px solid var(--focus-ring)` — `.nav-item:focus-visible`, `.btn:focus-visible`, `.toggle__input:focus-visible + .toggle__track`, `.banner-dismiss:focus-visible`, `[data-clamp] > summary:focus-visible`, `[data-uprow]:focus-visible`, `[data-feedrow]:focus-visible`, `.media-tile__remove:focus-visible`, `.media-tile--add:focus-visible`, `.sched-card__expand:focus-visible`, `.chip:has(.chip__input:focus-visible)`, `a.chip:focus-visible`, `.time-pill__input:focus-visible`, `.time-pill__remove:focus-visible`, `.group-pick__box:focus-visible`. Рамка — `.field__input:focus { border-color: var(--focus-ring); }`. Шаблоны токен не читают (`grep -rn 'var(--focus-ring)' app/templates` → 0). Форма ни одного правила не менялась, изменилось только значение токена, то есть вид каждого обвода на всех экранах. Обходы фаз 7–14 видели прежний, полупрозрачный обвод.

## Сверка с инвариантами продукта Фазы 10 (по диффу)

Замер сделан на дереве `039325d2..dc851613`. `_css_rules` над обеими версиями `app.css` без комментариев даёт 564 правила против 564, и отличается ОДНО правило — `:root` (`--focus-ring: rgba(196, 132, 252, .5)` → `rgb(196, 132, 252)`). Блок `<script>` шаблона тождественен побайтно.

| Запрет | Исход |
|---|---|
| `10-49#2`, `10-56#6`, `10-57#7` — тексты плашек не правятся, строка узла обрыва связи одна | соблюдён: аргументы `alert(...)` тождественны; строк с `id="htmx-failure-network"` одна; `_network_banner_line` зелен (прогон `test_shell.py`) |
| `10-49#1`, `10-56#5`, `10-57#3`, `10-57#4` — сценарий и третий обработчик не трогаются | соблюдён: блок `<script>` тождественен побайтно; регистраций 3 |
| `10-56#1…#4`, `10-57#8` — блок подъёма и его селектор | соблюдён: правил, кроме `:root`, дифф не касается |
| `10-57#9` — правило скрытия объявляет только «нет» | соблюдён: `.failure-stack:has(> .banner-dismiss:checked) { display: none; }` не тронуто, его держит новый сторож |
| `10-57#1`, `10-57#2` — ни `hx-on`, ни `x-data` | соблюдён: в шаблоне плашки 0 и 0 |

## TDD

План `type: execute`, `tdd_mode: true`. Поведение добавляют задачи 2 и 3: имя органа слышит пользователь, цвет обвода видит пользователь. Задача 1 поведения продукта не меняет: она добавляет записи в CSS и правило, но правило-сторож было написано и закоммичено красным до записей. Для каждой задачи RED закоммичен отдельным `test(15-19)`, запуск — из одного целевого теста, `-p no:randomly`. Запись переведена из `--junit-xml` в TAP одноразовым скриптом в scratchpad (не закоммичен). `check tdd-red-evidence` каждый раз вернул `RED_EVIDENCE_OK` (`target_test_failed`):

| Задача | RED-коммит | Упавший тест (`1 failed`) | Причинный литерал отказа | GREEN |
|---|---|---|---|---|
| 1 | `83e13522` | `…::test_boundary_the_keyboard_focus_and_the_checkbox_role_consequences_are_guarded_not_fixed` | «записи «ПРИНЯТОЕ СЛЕДСТВИЕ ВЕТВИ A: СНЯТИЕ КЛАВИШЕЙ ТЕРЯЕТ ФОКУС» в `app.css` НЕТ» | `3d8557eb` (docs) |
| 2 | `19a751e4` | `…::test_each_accessible_name_leads_with_its_own_failure` | «доступное имя «Скрыть сообщение об отказе сервера» начинается словом «Скрыть», а не признаком своей аварии «Отказ»» | `ace989f9` (feat) |
| 3 | `16576749` | `…::test_the_focus_ring_token_is_opaque_enough_for_non_text_contrast` | «`--focus-ring: rgba(196, 132, 252, .5)` — альфа 0.5 ниже 0.7» | `dc851613` (fix) |

## Task Commits

1. **Задача 1 RED** — `83e13522` (test)
2. **Задача 1: записи следствий и ссылка по цитате** — `3d8557eb` (docs)
3. **Задача 2 RED** — `19a751e4` (test)
4. **Задача 2: имена, поправка арифметики** — `ace989f9` (feat)
5. **Задача 3 RED** — `16576749` (test)
6. **Задача 3: непрозрачный токен** — `dc851613` (fix)

**Plan metadata:** docs(15-19) — коммит сводки и трекинга.

## Files Created/Modified

- `app/static/css/app.css` — две записи принятых следствий; ссылка по цитате вместо номеров строк; поправка шага стопки; непрозрачный токен с летописью
- `app/templates/includes/htmx_error_banner.html` — два значения `aria-label`; летопись имён в комментарии
- `tests/test_templates/test_banner_dismiss.py` — сторож и контроль следствий, правило порядка слов и его контроль, правило непрозрачности и его контроль; новые имена и признаки с летописью; пятая граница в докстринге
- `tests/test_templates/test_htmx_markup_gates.py` — два указателя `app.css:1255-1258` заменены цитатой (отклонение)

## Decisions Made

См. `key-decisions`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Указатели `app.css:1255-1258` в гейте разметки устарели бы от правки этого плана**
- **Found during:** Задача 2 (поправка в пункте (д) стоит выше абзаца стопки и сдвигает его на 7 строк)
- **Issue:** Комментарий раздела плана 15-05 и докстринг `test_focus_ring_rule_is_declared_for_the_banner_dismiss` цитировали абзац по номерам строк. После поправки номера указывали бы на другой текст. Это та же форма дефекта, что IN-04, только её половина в модуле, которого `files_modified` плана не называет.
- **Fix:** обе ссылки переведены на открывающие слова абзаца стопки, прежний указатель назван летописью. Тем же коммитом в докстринге `test_banner_dismiss.py` заменены указатели `app.css:1255-1258` и `app.css:1329` (этот файл план правит).
- **Files modified:** `tests/test_templates/test_htmx_markup_gates.py`, `tests/test_templates/test_banner_dismiss.py`
- **Verification:** `grep -rn '1255-1258' tests/ app/` находит только строки летописи; `tests/test_templates/` → 368 passed
- **Committed in:** `ace989f9`

**2. [Rule 1 - Bug] План называл адресатом ссылки «(г) ГРАНИЦА ДОКАЗАННОГО», а цитата живёт в абзаце стопки**
- **Found during:** Задача 1
- **Issue:** Цитата «объявлять их пройденными по зелени правил НЕЛЬЗЯ — окно 77 журнала…» стоит в абзаце, который замыкает пункт (д) шага стопки («⚠️ ГРАНИЦА ДОКАЗАННОГО НАЗВАНА ЗДЕСЬ, А НЕ ОСТАВЛЕНА ЧИТАТЕЛЮ: правила утверждают ОБЪЯВЛЕНИЯ этой таблицы»). В пункте (г) блока органа снятия её нет: там похожая фраза, но без «окна 77». Ревью IN-04 тоже пишет «quotes the stack paragraph».
- **Fix:** ссылка указывает на настоящий абзац по его открывающим словам и цитате
- **Files modified:** `app/static/css/app.css`
- **Committed in:** `3d8557eb`

**3. [Rule 1 - Bug] Признаки предмета имени пришлось перевести в именительный падеж**
- **Found during:** Задача 2
- **Issue:** `BANNER_DISMISS_SUBJECT_MARKS` («отказе сервера», «обрыве связи») не входят в новые имена. Без правки правило соответствия предмету (`test_each_accessible_name_names_its_own_failure`) краснело бы на исполненном требовании.
- **Fix:** признаки заменены на «Отказ сервера» / «Обрыв связи» тем же коммитом, что и имена; прежние названы летописью
- **Committed in:** `ace989f9`

---

**Total deviations:** 3 auto-fixed (Rule 1). **Impact:** ожидания правил других модулей не менялись. Правка вне `files_modified` — только комментарии и докстринг в `test_htmx_markup_gates.py`.

## Issues Encountered

- UI-ревью пишет, что общий префикс прежних имён — «22 знака». Замер `os.path.commonprefix` дал 21 знак («Скрыть сообщение об о»), имена расходятся на 22-м. В летопись записано замеренное число и названо, откуда взялось «22».
- В `tests/test_pages/test_shell.py` у `FAILURE_BANNER_STACK_LINES` осталась летопись замера 2026-09-13 с «поле набора … = 346px». Она датирована и верна на свой день, модуль вне `files_modified`, поэтому она не правилась. Поправка записана рядом с числом в `app.css`, где ревью и нашло устаревшую арифметику.
- Литеральные счёты не сдвинулись: `PAIRED_302_ASSERTIONS_DECLARED` 190, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5 — их модули зелены в прогоне, объявления не правились. Новых `import yaml` нет.

## Прогоны

- `tests/test_templates/test_banner_dismiss.py` → 28 passed (финальное дерево).
- Проверка задачи 2: `-k "banner or dismiss or accessible or stack"` по `test_banner_dismiss.py` и `test_shell.py` → 62 passed.
- Проверка задачи 3: `-k focus` по `test_banner_dismiss.py` и `test_htmx_markup_gates.py` → 6 passed; `tests/test_templates/` → 368 passed.
- Проверка плана на финальном дереве кода (`dc851613`): `tests/test_templates/ tests/test_pages/test_shell.py test_responsive_markup.py test_htmx_gates.py test_htmx_post_pairs.py test_hx_location_destinations.py test_asset_version.py test_https_asset_scheme.py test_prose_names_live_symbols.py test_account_groups.py test_admin_panel.py test_admin_users.py test_billing_section.py test_history.py tests/test_routes/test_billing_webhook_proxy_headers.py` → **1407 passed, 0 failed** (22 мин). Это все модули, которые читают `app.css` или шаблон плашки.
- `tests/test_planning/` — перед коммитом метаданных и после него (числа — в коммите и в отчёте исполнителя).
- ⚠️ **Подмена полного прогона названа:** полную суиту (`just test`, ~40 мин) по договору волны запускает оркестратор сразу после этого плана. Исполнитель её не запускал и окна `WINDOWS.md` под неё не открывал.

## Known Stubs

Нет.

## User Setup Required

Нет.

## Next Phase Readiness

Волна 5 исполнена (15-15…15-19). Шаг У-8 `15-UAT.md` должен увидеть: новый непрозрачный обвод на органе снятия и на остальных 15 потребителях; куда падает фокус после снятия пробелом (Chrome и Firefox); как скринридер произносит новые имена. Отметки и `result` ставит человек, план их не трогал. Приоритет 2 UI-ревью (смещение второй заготовки) остаётся записанным следствием, переданным вехе.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*

## Self-Check: PASSED

- FOUND: app/static/css/app.css, app/templates/includes/htmx_error_banner.html, tests/test_templates/test_banner_dismiss.py, tests/test_templates/test_htmx_markup_gates.py
- FOUND commits: 83e13522, 3d8557eb, 19a751e4, ace989f9, 16576749, dc851613
