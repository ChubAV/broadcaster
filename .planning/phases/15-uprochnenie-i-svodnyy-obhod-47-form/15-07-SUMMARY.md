---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 07
subsystem: ui
tags: [htmx, jinja, css, accessibility, wcag-4.1.2, pytest, gate-09, banner-dismiss]

requires:
  - phase: 10
    provides: "орган снятия плашки отказа (план 10-57): `<input type=\"checkbox\" class=\"banner-dismiss\">`, блок `.failure-stack:has(> .banner-dismiss:checked)`, стопка `.failure-stack` (план 10-56)"
  - phase: 15
    provides: "утверждение обвода фокуса органа снятия в CSS и передача числа правил `.failure-stack` этому плану (план 15-05)"
provides:
  - "два различимых доступных имени органа снятия, каждое по предмету своей заготовки"
  - "объявленная компенсация перекрытия `.failure-stack > .alert { padding-right: 38px }`, выведенная из коробки органа"
  - "единственный носитель числа правил `.failure-stack` (5) с летописью 6 → 4 → 5"
  - "запрет невидимых гейту форм доступного имени и сторож открытого следствия `--failure-banner-top`"
  - "перечень пяти наблюдений для раздела улики плана 15-14"
affects: [15-14, "15-UAT.md", "tests/test_pages/test_shell.py"]

actuals:
  tokens: 15055
  tasks: 3
  commits: 5
plan_head_before: f0ed76c6c655cf7005128eb69a32b5fb1b1b1641

tech-stack:
  added: []
  patterns:
    - "разборщик принимает ИСХОДНИК ТЕКСТОМ; обход, вырезание комментариев и разбор CSS — импортом из `test_htmx_markup_gates.py`, своего не заводится"
    - "величина CSS утверждается РАВЕНСТВОМ сумме слагаемых, прочитанных из другого блока той же таблицы (не подобранное число)"
    - "имя органа утверждается и различимостью, и СООТВЕТСТВИЕМ предмету узла"

key-files:
  created:
    - tests/test_templates/test_banner_dismiss.py
  modified:
    - app/templates/includes/htmx_error_banner.html
    - app/static/css/app.css
    - tests/test_pages/test_shell.py

key-decisions:
  - "Доступные имена по ПРЕДМЕТУ заготовки: «Скрыть сообщение об отказе сервера» / «Скрыть сообщение об обрыве связи»; нумерация отвергнута — на слух она не различает ничего"
  - "Компенсация 38px = ширина органа 24px + right 6px + зазор 8px; рамка `.alert` 1px в сумму не входит (лишь прибавляет пиксель к видимому зазору)"
  - "Блок CSS вставлен ПОСЛЕ `app.css:1330`, а не выше: цитата `app.css:1255-1258` в модуле плана 15-05 и координаты 1259/1263/1266/1330 не сдвинуты"
  - "Гейт органа в `test_shell.py` держал одно имя на обе заготовки; он переведён на ожидание ПО УЗЛУ из единственного носителя `BANNER_DISMISS_ACCESSIBLE_NAMES` (импорт внутри функции, чтобы не сдвигать цитируемые номера строк модуля)"
  - "Коммит задачи 3 (тесты, зелёные с рождения) — `feat(15-07)` по прецеденту 15-05, чтобы ревизия TDD не приняла его за RED после GREEN"

patterns-established:
  - "Сторож открытого следствия: число блоков + наличие ЗАПИСИ следствия в CSS; молчаливое удаление записи краснит так же, как тихая починка"

requirements-completed: [GATE-09]

coverage:
  - id: D1
    description: "Два доступных имени органа снятия различимы и каждое соответствует предмету своего узла; органов ровно 2 (`> 0`); форма — флажок без текстового узла; регистраций обработчика 3 = до правки"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_banner_dismiss.py -q -p no:randomly (20 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_the_two_dismiss_controls_have_distinct_accessible_names"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_each_accessible_name_names_its_own_failure"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_shell.py -q -p no:randomly (245 passed)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Компенсация перекрытия объявлена блоком `.failure-stack > .alert { padding-right: 38px }`, величина равна width + right органа + зазор, прочитанным из `.banner-dismiss`; правил стопки 5; блоков `--failure-banner-top` 3; способа отображения нет"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_banner_dismiss.py#test_the_clearance_is_derived_from_the_dismiss_box"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/ -q -p no:randomly -k \"banner or failure_stack or selector_lifts or display_mode or stack_block\" (61 passed; до правки 41)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Четыре границы гейта названы; запрет `aria-labelledby`/`title`/текстового узла; сторож открытого следствия с цитатой основания из CSS"
    requirement: "GATE-09"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_templates/test_banner_dismiss.py -q -p no:randomly -k \"boundary or cannot_see or no_control_gets_its_name\" (3 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пять наблюдений глазами: обвод фокуса виден; пробел снимает плашку; нарисованного столкновения текста с крестиком нет; два имени различимы на слух; вторая заготовка после снятия первой органом остаётся смещённой (известное открытое следствие)"
    requirement: "GATE-09"
    verification: []
    human_judgment: true
    rationale: "Движка раскладки, дерева доступности и браузерного привода в суите нет; `app/static/css/app.css:1255-1258` запрещает объявлять отрисовку пройденной по зелени правил. `result` и отметку заполняет человек (D-17); раздел улики пишет план 15-14"

duration: 44min
completed: 2026-09-24
status: complete
---

# Phase 15 Plan 07: Различимые имена органа снятия и объявленная компенсация перекрытия Summary

**Органы снятия двух плашек отказа получили различимые доступные имена по предмету своей аварии («Скрыть сообщение об отказе сервера» / «Скрыть сообщение об обрыве связи», WCAG 4.1.2), а перекрытие текста коробкой органа закрыто объявленным `padding-right: 38px`, выведенным из самой коробки (24 + 6 + 8). Новый гейт `test_banner_dismiss.py` из 20 правил держит обе правки, число правил `.failure-stack` (5, летопись 6 → 4 → 5) и сторож открытого следствия; отрисовка названа и оставлена человеку.**

## Performance

- **Duration:** ~44 min
- **Started:** 2026-09-24T08:12:45Z
- **Completed:** 2026-09-24T08:57:38Z
- **Tasks:** 3
- **Files modified:** 4 (1 создан, 3 изменены)

## Accomplishments

- Два значения `aria-label` дословно:
  - узел `htmx-failure-server`, орган `htmx-failure-server-close`: `aria-label="Скрыть сообщение об отказе сервера"`
  - узел `htmx-failure-network`, орган `htmx-failure-network-close`: `aria-label="Скрыть сообщение об обрыве связи"`
- Правка разметки — ровно две строки (`git show --numstat` → `2 2`), сценарий и комментарий-докстринг шаблона не тронуты.
- Блок компенсации `.failure-stack > .alert { padding-right: 38px; }` с комментарием (повод, ⚠️-оговорка о нарисованной половине, форма правки, граница с дословной цитатой `объявлять их пройденными по зелени правил НЕЛЬЗЯ`); правка CSS — `32 0`, только добавление.
- Гейт `tests/test_templates/test_banner_dismiss.py`: 20 правил (8 задачи 1 + контроль кодовых точек, 8 задачи 2, 3 задачи 3).

## Замеры ДО и ПОСЛЕ

| Величина | ДО правки | ПОСЛЕ |
|---|---|---|
| `grep -c 'aria-label="Скрыть сообщение"' htmx_error_banner.html` | 2 | 0 |
| `grep -c 'aria-label="Скрыть сообщение об' …` | 0 | 2 |
| регистрации обработчика (`addEventListener`) в файле заготовок | 3 | 3 |
| `grep -c 'failure-banner-top' app/static/css/app.css` | 5 | 5 |
| блоков, ОБЪЯВЛЯЮЩИХ `--failure-banner-top` | 3 | 3 |
| правил с селектором `.failure-stack` | 4 | 5 |
| `-k "banner or failure_stack or selector_lifts or display_mode or stack_block"` по `tests/` | 41 passed | 61 passed (+20 — весь новый модуль попадает в отбор по слову `banner`) |
| `tests/test_templates/` | 307 passed | 327 passed |
| `tests/test_pages/test_shell.py` | — | 245 passed |

## Вывод величины компенсации из замера

Коробка органа, блок `.banner-dismiss` (`app.css:1318-1326`): `position: absolute; top: 6px; right: 6px; width: 24px; height: 24px`.
Замер D-18.3 (2026-09-14): коробка 885→909 при содержимом `.alert`, кончающемся на 900, — перекрытие 15 px.

`BANNER_DISMISS_CLEARANCE_PX = width 24 + right 6 + зазор 8 = 38`. Правило `test_the_clearance_is_derived_from_the_dismiss_box` читает `width` и `right` из блока `.banner-dismiss` той же таблицы и утверждает равенство и объявленной константы, и значения в CSS этой сумме. Рамка `.alert` (1px) в сумму не входит нарочно: видимый зазор 9px. Контроль занижения на 1px (`37px`) краснит правило и называет расхождение.

## Летопись `6 → 4 → 5` (полный текст — докстринг модуля)

- «6» — запись долга D-18.3 и `15-CONTEXT.md`: «компенсации `padding-right` нет ни в одном из шести правил `failure-stack`».
- «4» — перезамер планирования Фазы 15 (Ф-19 `15-RESEARCH.md`), снят ЧТЕНИЕМ ФАЙЛА, а не вычитанием: селекторы `app.css:1259, 1263, 1266, 1330`.
- «5» — правка плана `15-07`, задача 2: добавлен ПЯТЫЙ селектор — блок компенсации перекрытия `.failure-stack > .alert`.

ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и правится не он, а числа, которые он пережил. Записи разведки (`.planning/research/*`) НЕ ПРАВЯТСЯ. ⚠️ Утверждение записи долга «компенсации нет ни в одном из шести» верно ПО СУЩЕСТВУ — её не было ни в одном из ЧЕТЫРЁХ; расходится число, не вывод. Носитель числа один — `FAILURE_STACK_RULES` в `test_banner_dismiss.py`; план 15-05 своего литерала не заводил.

## Пересборка `asset_version` — ожидаемое следствие (FOUND-03)

Правка `app/static/css/app.css` сдвигает `?v=` на теге стилей: версия выводится из байтов охвата `.css`/`.js` (`app/pages/common.py`, `_compute_asset_version`). Это ожидаемое следствие, а не регрессия; `tests/test_pages/test_asset_version.py` зелен (входит в прогон 160 passed вместе с `test_responsive_markup.py`).

## Пять наблюдений, передаваемых плану 15-14 разделом улики

Окно 1280 px, обе заготовки видимы (двойная авария: отказ 500 и обрыв сети).

1. Виден ли обвод фокуса на органе снятия при переходе табуляцией (`outline: 2px solid var(--focus-ring)`, `app.css:1329`, существование утверждено планом 15-05)?
2. Срабатывает ли ПРОБЕЛ на `<input type="checkbox">` (заготовка скрывается)?
3. Есть ли нарисованное столкновение текста с крестиком — уже с компенсацией (замер 2026-09-14: столкновения НЕТ и до неё; подтвердить или опровергнуть заново)?
4. Различимы ли два доступных имени НА СЛУХ скринридера?
5. Остаётся ли вторая заготовка на смещённом месте после снятия первой ОРГАНОМ (известное открытое следствие — подтвердить, что оно именно такое, а не хуже)?

⚠️ `result` и отметку заполняет человек (D-17); машинный замер идёт разделом улики, а не приёмкой.

## Открытое следствие, переданное дальше

Смещение второй заготовки после снятия первой органом этой фазой НЕ чинится. Основание (дословно из `app.css`): «Починка требует четвёртого блока, объявляющего `--failure-banner-top`, а разбор `_stack_blocks` относит его к роли смещения — и правила стопки плана 10-56 покраснели бы за ФОРМУ правки». Адресат — решение ВЕХИ (как `DEF-09-04`). Сторож `test_boundary_the_open_banner_top_consequence_is_guarded_not_fixed` держит число блоков (3) и наличие записи следствия в CSS.

## Task Commits

1. **Задача 1: различимые доступные имена** — RED `3bbb0a95` (test), GREEN `1742e129` (feat)
2. **Задача 2: объявленная компенсация и число правил стопки** — RED `53e286f2` (test), GREEN `cb1d1857` (feat)
3. **Задача 3: границы, запрет и сторож** — `3df07f15` (feat)

## TDD Gate Compliance

- Задача 1 RED: `uv run pytest tests/test_templates/test_banner_dismiss.py -q -p no:randomly --junit-xml=…` → `4 failed, 5 passed`, exit 1; целевое `test_the_two_dismiss_controls_have_distinct_accessible_names` упало на утверждении, назвав повтор «Скрыть сообщение» у обоих узлов. Прибор `check tdd-red-evidence` (запись переведена из junit того же прогона в TAP) → `RED_EVIDENCE_OK`. GREEN → `9 passed`.
- Задача 2 RED: тот же модуль → `7 failed, 10 passed`, exit 1; целевое `test_the_overlap_clearance_is_declared` упало на утверждении «объявления `.failure-stack > .alert { padding-right: … }` нет». `RED_EVIDENCE_OK`. GREEN → `17 passed`.
- `test(15-07)` предшествует `feat(15-07)` в обеих задачах; REFACTOR-коммитов нет (изменений не потребовалось).

## Verification

- `uv run pytest tests/test_templates/test_banner_dismiss.py -q -p no:randomly` → 20 passed; `-k control` → 12 passed (≥ 3).
- `uv run pytest tests/ -q -p no:randomly -k "banner or failure_stack or selector_lifts or display_mode or stack_block"` → 61 passed (до правки 41).
- `uv run pytest tests/test_pages/test_shell.py tests/test_templates/ -q -p no:randomly` на итоговом дереве кода → 572 passed (245 + 327; порог каталога шаблонов 236 перекрыт).
- `grep -c 'aria-label="Скрыть сообщение"' app/templates/includes/htmx_error_banner.html` → 0; `grep -c 'failure-banner-top' app/static/css/app.css` → 5 (= до правки).
- `uv run python -m compileall -q app main.py tests` → молчание, exit 0.
- `graphify update .` выполнен.
- Прочие модули, читающие `app.css` или шаблон заготовок: `test_htmx_gates.py` + `test_hx_location_destinations.py` + `tests/test_templates/` → 391 passed (после задачи 1); `test_responsive_markup.py` + `test_asset_version.py` → 160 passed; CSS-правила `test_billing_section`/`test_account_groups`/`test_history` → 18 + 1 passed.
- ⚠️ ПОДМЕНА, НАЗВАННАЯ ЯВНО: полная суита (`just test`) и прогон всего `tests/` здесь НЕ запускались — по указанию оркестратора их запускает он после волны (окно 101). Вместо них прогнаны целевой модуль, `tests/test_templates/`, `test_shell.py` и перечисленные модули, ссылающиеся на `htmx_error_banner`/`banner-dismiss`/`app.css`.
- `requirements.ready-ids 15-07-PLAN.md GATE-09` → `0/1 requirement(s) ready` (GATE-09 объявляют и другие планы без сводок); `requirements.mark-complete` НЕ вызывался.

## Decisions Made

См. `key-decisions` во frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Гейт органа снятия в `test_shell.py` держал прежнее единое имя**
- **Found during:** Задача 1 (подготовка GREEN)
- **Issue:** `_dismiss_control_findings` требовал `aria-label="{FAILURE_BANNER_DISMISS_LABEL}"` с `FAILURE_BANNER_DISMISS_LABEL = "Скрыть сообщение"` — правка плана покрасила бы `test_every_failure_banner_carries_a_dismiss_control`, а план требует `test_shell.py` зелёным; файла в `files_modified` плана нет.
- **Fix:** ожидание переведено ПО УЗЛУ из единственного носителя `BANNER_DISMISS_ACCESSIBLE_NAMES` (импорт внутри функции). Прежняя константа названа летописью в комментарии (D-30/D-32), а не вычеркнута молча. Проверка не ослаблена: имя по-прежнему сличается точно, теперь — своё у каждого узла. Номера строк выше 2457, цитируемые `15-13-PLAN.md` и `15-PATTERNS.md` (`test_shell.py:2321`) и `test_components.py` (`:2295-2311`), не сдвинуты.
- **Files modified:** `tests/test_pages/test_shell.py`
- **Verification:** `test_shell.py` 245 passed
- **Committed in:** `1742e129`

**2. [Rule 1 - Bug] Летопись 6 → 4 → 5 сначала легла комментарием, а не докстрингом**
- **Found during:** Задача 2 (проверка критериев приёмки)
- **Issue:** критерий требует летопись в ДОКСТРИНГЕ модуля.
- **Fix:** перенесена в докстринг, в комментарии группы — ссылка.
- **Committed in:** `cb1d1857`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 acceptance-criterion fix)
**Impact on plan:** правка `test_shell.py` необходима для зелени заявленного плана прогона; предмет и сила гейта шелла сохранены.

### 15-05 handoff

Цитата `app.css:1255-1258` в `test_htmx_markup_gates.py` не сдвинута: блок вставлен после строки 1330, строки 1255-1258 байт в байт прежние. Число правил `.failure-stack`, оставленное планом 15-05 этому плану, объявлено здесь (`FAILURE_STACK_RULES = 5`). Модуль 15-05 зелен (в составе 327 passed каталога шаблонов).

## Issues Encountered

- `-k control` отбирает 12, а не 3: подстрока `control` есть и в именах правил об органе (`dismiss_control`). Порог плана (≥ 3) выполнен; три объявленных контроля задачи 1 (`test_control_repeated_accessible_names_redden`, `test_control_a_control_without_an_accessible_name_reddens`, `test_control_the_untouched_tree_is_a_nonempty_universe`) входят в отбор.

## Known Stubs

None — пустых значений, заглушек и плейсхолдеров в созданных и изменённых файлах нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Готово для плана 15-14: пять наблюдений перечислены выше и в докстринге модуля.
- Открыто и передано вехе: смещение второй заготовки после снятия первой органом.
- GATE-09 остаётся `Pending` до верификации фазы.

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-24*

## Self-Check: PASSED

- Файлы на месте: `tests/test_templates/test_banner_dismiss.py`, `app/templates/includes/htmx_error_banner.html`, `app/static/css/app.css`, `tests/test_pages/test_shell.py`.
- Коммиты найдены: `3bbb0a95`, `1742e129`, `53e286f2`, `cb1d1857`, `3df07f15`; `git rev-list --count f0ed76c6..HEAD` → 5.
