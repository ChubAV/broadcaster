---
phase: 06-admin-panel
plan: 03
subsystem: ui
tags: [jinja2, templates, component-library, filters, chips]

requires:
  - phase: 04-history
    provides: "Макрос чипсов-фильтров, его CSS-примитив (.chip / .chip-set / .chip--on) и три живых вызова в разделе истории"
  - phase: 06-admin-panel
    plan: "01"
    provides: "Файловая развязка: 06-01 закончил свои правки tests/test_pages/test_responsive_markup.py, и константа инвентаря правится без наложения"
provides:
  - "app/templates/components/filter_chips.html — макрос чипсов-фильтров как компонент общей библиотеки"
  - "Обязательный базовый адрес макроса: умолчания /history больше нет, каждый вызов называет свой раздел"
  - "Громкий отказ на забытом базовом адресе (UndefinedError) вместо тихой ссылки href=\"\" на текущий экран"
  - "tests/test_pages/test_filter_chips.py — переносимость компонента, обязательность параметра и постоянный обход дерева шаблонов против возврата старого пути"
  - "Библиотека компонентов: 14 файлов, оба утверждения инвентаризации подняты тем же коммитом"
affects: [06-08-logs, 06-09-users]

actuals:
  # 27 409 символов реализованного диффа / 4. Шкала та же, что у `estimate`
  # плана (32 000), и это НЕ счётчик токенов раннера. Промах четырёхкратный и
  # записан как есть: план оценён с `confidence: low`, а по факту оказался
  # перемещением файла, правкой трёх вызовов и двух констант. Округление в
  # сторону оценки испортило бы каждую следующую.
  tokens: 6900
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Общий макрос НЕ имеет умолчания для адреса раздела: у компонента с несколькими потребителями умолчание одного из них — тихая утечка в чужой раздел, а не удобство"
    - "Обязательность параметра Jinja обеспечивается обращением к его атрибуту первой строкой макроса: забытый аргумент — Undefined, и он печатается пустой строкой, а не падает"
    - "Компонент общей библиотеки проверяется ПРЯМЫМ рендером с чужим базовым адресом, а не через разметку одного из потребителей"
    - "Снятое утверждение заменяется надгробной запиской с адресами, куда переехали обе его половины"

key-files:
  created:
    - tests/test_pages/test_filter_chips.py
  modified:
    - app/templates/components/filter_chips.html
    - app/templates/history/list.html
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_history.py
    - .planning/phases/06-admin-panel/deferred-items.md

key-decisions:
  - "Обязательность базового адреса реализована обращением к атрибуту (`base_path.startswith('/')`) первой строкой макроса, а не переводом окружения на StrictUndefined: StrictUndefined — правка уровня всего проекта ради одного макроса, и она уронила бы шаблоны, живущие на мягком Undefined"
  - "Третье, не названное планом место с числом 13 (`test_filter_chips_template_lives_outside_the_component_library` в tests/test_pages/test_history.py) снято, а не поправлено: его предмет — «файл лежит ВНЕ библиотеки» — отменён этим планом целиком, и поднятая до 14 константа оставила бы тест, утверждающий обратное текущему устройству"
  - "Явный базовый адрес в трёх вызовах истории написан ключевым словом (`base_path='/history'`), а не позиционно: позиционный пятый аргумент в вызове из пяти читается как «что-то про историю», ключевой — как «раздел назван вслух»"

patterns-established:
  - "Переезд шаблона в общую библиотеку = один коммит: файл, все вызовы и ОБЕ константы инвентаризации. Раздельные коммиты на время отключают проверку пополнения библиотеки"
  - "Докстринг, объясняющий «почему файл лежит НЕ там», переписывается вместе с переездом: после него он становится ложью в файле"

requirements-completed: [ADMIN-04, ADMIN-09]

coverage:
  - id: D1
    description: "Макрос чипсов-фильтров лежит в библиотеке компонентов и импортируется оттуда; в каталоге включений раздела истории его больше нет"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_filter_chips.py#test_no_template_imports_the_old_path"
        status: pass
      - kind: other
        ref: "ls app/templates/components/filter_chips.html && ! ls app/templates/history/includes/filter_chips.html"
        status: pass
    human_judgment: false
  - id: D2
    description: "Базовый адрес — обязательный параметр макроса: умолчания, уводящего чипсы в раздел истории, не осталось (Ф-15)"
    requirement: ADMIN-09
    verification:
      - kind: unit
        ref: "tests/test_pages/test_filter_chips.py#test_missing_base_path_raises"
        status: pass
      - kind: other
        ref: "grep -Ec \"base_path='/history'\" app/templates/components/filter_chips.html == 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Три вызова в разделе истории передают базовый адрес явно и рисуют ту же разметку, что до переезда"
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages -q -k history (192 passed)"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_responsive_markup.py -q (129 passed)"
        status: pass
      - kind: other
        ref: "grep -Ec 'base_path=' app/templates/history/list.html == 3"
        status: pass
    human_judgment: false
  - id: D4
    description: "Инвентаризация библиотеки признаёт четырнадцатый файл ОБОИМИ своими утверждениями, и обе константы подняты тем же коммитом, что и переезд"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_template_inventory"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_billing_component_library_did_not_grow"
        status: pass
      - kind: other
        ref: "git show --stat cd6c742 — оба утверждения и переезд в одном коммите"
        status: pass
    human_judgment: false
  - id: D5
    description: "Макрос, вызванный с чужим базовым адресом, строит ссылки на этот адрес — свойство закреплено тестом, а не выведено из чтения кода"
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_filter_chips.py#test_macro_serves_a_foreign_section"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_filter_chips.py#test_other_filters_survive_switching_one_axis"
        status: pass
    human_judgment: false

duration: 1h 4m
completed: 2026-08-22
status: complete
---

# Phase 06 Plan 03: Переезд чипсов-фильтров в библиотеку компонентов Summary

**Макрос чипсов-фильтров переехал из `history/includes/` в общую библиотеку компонентов, базовый адрес раздела стал обязательным параметром с громким отказом на забытом аргументе, и переносимость закреплена шестью тестами прямого рендера.**

## Performance

- **Duration:** 1h 4m
- **Started:** 2026-08-22T15:48:00Z
- **Completed:** 2026-08-22T16:52:00Z
- **Tasks:** 2
- **Files modified:** 6 (1 создан, 1 перемещён, 4 изменены)

## Accomplishments

- **Переезд состоялся по сроку, назначенному самим файлом.** Головной докстринг макроса прямо
  писал: «второй потребитель станет поводом для переезда». В фазе 6 потребителей стало трое —
  раздел истории, «Пользователи» (D-32) и «Логи» (D-29) админки, — и файл переехал в
  `app/templates/components/filter_chips.html`. Тело макроса не тронуто ни одним символом:
  переезд, смешанный с правкой вёрстки, оставил бы разъехавшийся пиксель необъяснимым.
- **Умолчание базового адреса снято, и это закрыло ловушку по построению, а не предупреждением.**
  До переезда `base_path='/history'` был умолчанием единственного тогдашнего потребителя. Импорт
  такого макроса в админку дал бы не ошибку разметки, а 200, верную вёрстку и чипсы, уводящие
  администратора из своего подраздела при КАЖДОМ клике по фильтру. Теперь параметр обязателен.
- **Забытый параметр падает на рендере.** Забытый аргумент в Jinja — не ошибка, а `Undefined`, и в
  атрибут `href` он печатается ПУСТОЙ строкой: доказано отдельной пробой — шаблон без защиты даёт
  `<a href="?x=1">`, то есть чипс, ведущий на текущий адрес и молча ничего не фильтрующий. Макрос
  первой строкой ТРОГАЕТ параметр обращением к атрибуту, и `UndefinedError` («parameter 'base_path'
  was not provided») приходит на рендере, а не тихой ссылкой в никуда.
- **Инвентаризация сведена ОБОИМИ утверждениями в одном коммите с переездом.** Число файлов
  библиотеки пинуется в `test_responsive_markup.py` дважды, и одно из двух (`test_billing_component_
  library_did_not_grow`) в выборку `-k inventory` не попадает: поднятое в одиночку, оно зеленит
  выборку и краснит полный прогон из теста, названного по чужому разделу. Обе константы 13 → 14,
  к каждой дописано, что за четырнадцатый файл и почему он появился.
- **Компонент впервые проверяется как компонент, а не как разметка одного экрана.** До этого плана
  макрос жил под косвенным покрытием тестов истории — и ровно поэтому привязка к одному разделу
  дожила незамеченной до третьего потребителя: тест, который рендерит историю, на «историю» в адресе
  чипса и рассчитывает. Новый файл рендерит макрос напрямую с ЧУЖИМ базовым адресом.

## Task Commits

1. **Задача 1: Переезд макроса в библиотеку компонентов и обязательный базовый адрес** — `cd6c742` (refactor)
2. **Задача 2: Тест переносимости — макрос обслуживает произвольный раздел** — `a8ac676` (test)

## Files Created/Modified

- `app/templates/components/filter_chips.html` — переехавший макрос (из `history/includes/`).
  Тело без изменений; переписан головной докстринг (абзац «почему файл НЕ в библиотеке» стал бы
  ложью в файле), снято умолчание `base_path`, добавлена строка-страж обязательности параметра.
- `app/templates/history/list.html` — новый путь импорта (строка перенесена в алфавитный порядок
  блока `components/*`), три вызова передают `base_path='/history'` ключевым словом, комментарий
  полосы чипсов объясняет, почему адрес назван вслух.
- `tests/test_pages/test_filter_chips.py` — **новый.** Шесть тестов прямого рендера.
- `tests/test_pages/test_responsive_markup.py` — обе константы инвентаризации 13 → 14 с пояснением
  у каждой, включая указание, что выборка `-k inventory` берёт лишь одну из двух.
- `tests/test_pages/test_history.py` — снят устаревший `test_filter_chips_template_lives_outside_
  the_component_library`, на его месте надгробная записка с адресами обеих переехавших половин.
- `.planning/phases/06-admin-panel/deferred-items.md` — к записи плана 06-04 дописано вторичное
  подтверждение и найденный минимальный набор-воспроизводитель (см. «Issues Encountered»).

## Decisions Made

1. **Обязательность параметра — обращением к атрибуту, а не переводом окружения на `StrictUndefined`.**
   `StrictUndefined` — правка уровня всего проекта ради одного макроса, и она уронила бы шаблоны,
   которые сегодня штатно живут на мягком `Undefined`. Строка `{% set _ = base_path.startswith('/') %}`
   стоит ровно там, где нужна, и даёт готовое сообщение Jinja с ИМЕНЕМ параметра.
2. **Явный адрес написан ключевым словом, а не позиционно.** Позиционный пятый аргумент в вызове из
   пяти читается как «что-то про историю»; `base_path='/history'` читается как «раздел назван вслух»,
   то есть как выполнение того самого требования, ради которого умолчание и снималось.
3. **Третье место с числом 13 снято, а не поправлено** — см. «Deviations», пункт 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocker] Число файлов библиотеки пинилось ТРЕТЬИМ, не названным планом местом, и это место утверждало обратное предмету плана**

- **Found during:** Задача 1
- **Issue:** План (и `must_haves`, и список чтения, и критерии приёмки) исходит из того, что число
  файлов библиотеки закреплено в суите ДВАЖДЫ — обоими утверждениями в
  `tests/test_pages/test_responsive_markup.py`. Мест оказалось ТРИ. Третье —
  `test_filter_chips_template_lives_outside_the_component_library` в
  `tests/test_pages/test_history.py:571` — не просто пинило то же число, а утверждало ровно то,
  что план отменяет: `assert (templates_dir / "history/includes/filter_chips.html").exists()` и
  `assert len(...components...) == 13`. С ним переезд не мог сойтись ни в одном виде: суита
  краснела бы обеими половинами.
- **Fix:** Тест снят целиком, а не «поправлен под новое число». Его предмет — «файл лежит ВНЕ
  библиотеки» — отменён этим планом, и тест с константой 14 остался бы утверждением, противоречащим
  устройству проекта. На его месте оставлена надгробная записка (приём, уже принятый в этой суите —
  ср. блок про шесть снятых тестов прямого рендера в `test_responsive_markup.py`), которая называет
  адреса ОБЕИХ переживших половин: число файлов — двумя константами в `test_responsive_markup.py`,
  место шаблона — тестом `test_no_template_imports_the_old_path`, который обходит всё дерево
  шаблонов постоянно, а не разово.
- **Files modified:** `tests/test_pages/test_history.py`
- **Verification:** `uv run pytest tests/test_pages -q -k history` → 192 passed;
  `uv run pytest tests/test_pages/test_responsive_markup.py -q` → 129 passed.
- **Committed in:** `cd6c742` (в составе коммита задачи 1 — по тому же доводу, по которому
  константы правятся вместе с переездом: раздельно они на время оставляют суиту красной)

---

**Total deviations:** 1 auto-fixed (1 × Rule 3 — blocker).
**Impact on plan:** Правка обязательна для сходимости суиты и строго в границах предмета плана —
снятое утверждение говорило именно о переезжающем файле. Расширения области не произошло:
ни одного файла вне списка `files_modified` плана, кроме `test_history.py`, где жило само
препятствие, и `deferred-items.md`, куда по правилу границы записан чужой отказ.

## TDD Gate Compliance

⚠️ **Задача 2 помечена `tdd="true"`, но фазы RED в строгом смысле у неё не было, и это следствие
устройства плана, а не пропущенная дисциплина.**

- **GREEN-коммит:** `a8ac676` (`test(06-03): ...`) — шесть тестов, зелёные с первого прогона.
- **RED-коммита нет.** Порядок задач плана не оставляет для него места: `<read_first>` задачи 2
  прямо называет входом «app/templates/components/filter_chips.html (результат задачи 1 — сигнатура
  и тело макроса)». Тесты писать было НЕ на что, пока задача 1 не переехала файл и не сняла
  умолчание. Написанные раньше, они падали бы на отсутствии файла по новому пути — то есть
  «красное» говорило бы о ненаписанной задаче 1, а не о непроверенном свойстве.
- **Чем компенсировано.** Зубы главного утверждения проверены отдельной пробой, а не приняты на
  веру: шаблон без строки-стража рендерит `<a href="?x=1"></a>` вместо отказа
  (`uv run python -c "import jinja2; ..."`, вывод приложен в журнале исполнения). То есть
  `test_missing_base_path_raises` доказанно краснеет без защиты, которую он охраняет, — ровно то,
  что должна была установить фаза RED.
- **Природа файла.** Остальные пять тестов — характеризующие: они закрепляют поведение, которое
  до плана существовало, но проверялось лишь косвенно. Для таких тестов RED недостижим по
  определению, и плановое описание задачи это признаёт прямо: «Он существует не ради покрытия».

## Issues Encountered

**Один пре-существующий красный тест в полном прогоне — НЕ следствие этого плана.**

`tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` краснеет в
полном прогоне (`uv run pytest tests/ -q` → **1 failed, 1831 passed**) и зеленеет в одиночку
(`tests/test_pages/test_ads_editor.py -q` → 36 passed).

Отказ уже был записан в `deferred-items.md` планом 06-04 ДО того, как этот план тронул хоть строку.
Здесь он подтверждён вторично и **найден минимальный набор-воспроизводитель**: пять файлов, идущих
в алфавитном порядке ДО всех файлов этого плана
(`test_access_gate.py test_access_lifecycle.py test_account_groups.py test_admin_panel.py test_ads_editor.py`
→ 1 failed, 163 passed). Файлы плана — `test_filter_chips.py`, `test_history.py`,
`test_responsive_markup.py` — сортируются ПОСЛЕ `test_ads_editor.py` и в этот прогон не попадают
вовсе: связь с планом отсутствует, а не «не найдена».

Кандидат на причину назван самим проектом, а не выведен: `app/pages/common.py` объявляет прямым
текстом, что `templates` — модульный синглтон, общий на процесс, «последний `create_app`
выигрывает», и разведение окружений Jinja по приложениям — архитектурная правка. Поэтому починка
относится к Правилу 4 (архитектурное решение, требующее вердикта), а не к Правилам 1–3, и по
границе области в этот план не берётся. Запись дополнена в `deferred-items.md`.

**Побочно:** при первой записи в `deferred-items.md` файл был перезаписан целиком вместо дополнения
(файл уже существовал и содержал запись плана 06-04). Обнаружено сразу по `git status`
(` M` вместо `??`), исходное содержимое восстановлено `git checkout -- <файл>` до какого-либо
коммита, запись 06-04 сохранена дословно, своё добавлено дописыванием. Ни одна чужая строка не
потеряна — проверено диффом.

## Known Stubs

None — заглушек, отложенных тестов и непрогнанных `<verify>` план не оставил.

## Threat Flags

None — новой поверхности за пределами `<threat_model>` плана не появилось. `T-06-CHIP` (Tampering,
базовый адрес макроса) закрыт по назначенному плану смягчения: параметр обязателен, переносимость и
обязательность закреплены тестами `test_macro_serves_a_foreign_section` и
`test_missing_base_path_raises`.

## Verification Results

| Проверка | Результат |
|----------|-----------|
| `uv run pytest tests/test_pages/test_filter_chips.py -q` | ✅ 6 passed |
| `uv run pytest tests/test_pages/test_responsive_markup.py -q -k inventory` | ✅ 1 passed |
| `uv run pytest tests/test_pages/test_responsive_markup.py -q` | ✅ 129 passed |
| `uv run pytest tests/test_pages -q -k history` | ✅ 192 passed |
| `uv run pytest tests/test_pages -q` | ⚠️ 914 passed, 1 failed — пре-существующий отказ, см. «Issues Encountered» |
| `uv run pytest tests/ -q` (эквивалент `just test`) | ⚠️ 1831 passed, 1 failed — тот же пре-существующий отказ |

**Критерии приёмки задачи 1 (машинные), все проверены:**

| Критерий | Факт |
|----------|------|
| `ls app/templates/components/filter_chips.html` | ✅ код 0 |
| `ls app/templates/history/includes/filter_chips.html` | ✅ код 2 (переехал, а не скопирован) |
| старого пути импорта в `app/templates/` нет | ✅ 0 |
| `grep -c "components/filter_chips.html" .../history/list.html` | ✅ 1 |
| `grep -Ec "base_path='/history'" .../components/filter_chips.html` | ✅ 0 |
| `grep -Ec "base_path=" .../history/list.html` | ✅ 3 |
| `ls app/templates/components/*.html \| wc -l` | ✅ 14 |
| `len(components) == 14` вне комментариев | ✅ 2 |
| `len(components) == 13` вне комментариев | ✅ 0 |

## User Setup Required

None — внешней настройки план не требует.

## Next Phase Readiness

**Готово к использованию планами 06-08 («Логи», ADMIN-09) и 06-09 («Пользователи», ADMIN-04).**
Оба импортируют макрос строкой `{% from "components/filter_chips.html" import filter_chips %}` и
ОБЯЗАНЫ передать свой базовый адрес — забытый параметр теперь падает на рендере, а не строит
ссылку в чужой раздел. Форма данных не изменилась: `(options, active, base_params, param_name,
base_path)`, где `options` — `[(значение, подпись)]` с пустым значением как вариантом «все».

**Требования ADMIN-04 и ADMIN-09 в `REQUIREMENTS.md` этим планом НЕ отмечены** — намеренно. Оба
объявлены и планами 06-08/06-09, которые ещё не завершены; отметка «Complete» сейчас закрыла бы
требование до того, как появится сама поверхность, ради которой оно заведено. Этот план —
предпосылка, а не исполнение требования (что зафиксировано и комментарием в его frontmatter).

**Разделяемые артефакты (`STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`) не тронуты** — их пишет
оркестратор после схождения волны.

## Self-Check: PASSED

- `app/templates/components/filter_chips.html` — FOUND
- `tests/test_pages/test_filter_chips.py` — FOUND
- `app/templates/history/includes/filter_chips.html` — отсутствует (ожидаемо: переехал)
- commit `cd6c742` — FOUND
- commit `a8ac676` — FOUND

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*
