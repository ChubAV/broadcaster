---
phase: 18-ruchnaya-pravka-nomera
plan: 04
subsystem: ui
tags: [css, flexbox, scroll-padding, wcag-contrast, sticky-header, gap-closure]

requires:
  - phase: 18-ruchnaya-pravka-nomera
    provides: "пометка «указан вручную» в подписи аккаунта (18-01), форма номера в шапке экрана групп (18-02), ссылки к полю #phone (18-03)"
provides:
  - "приоритет усечения пометки в .chip__label и .acct-head__name (flex: 1 1 0; max-width: max-content), номер сжимается только после ухода пометки"
  - "сжимаемый ряд действий шапки экрана групп: .acct-head__actions { flex: 0 1 auto; min-width: 0 }"
  - "пометка кеглем номера (--fs-xs) и цветом --text-secondary с контрастом не ниже 4,5:1 на четырёх фонах подписи"
  - "html { scroll-padding-top } для десктопа (170px) и ≤860 px (236px): поле #phone не под липкой шапкой"
affects: [18-05, 18-07, verify-work-18]

actuals:
  tokens: 8300
  tasks: 3
  commits: 6

plan_head_before: 889019ccfc2d072f8731fb63506b5aea8927c28f
plan_head_after: 8e9b62b82f848ff3c3d1e401a138730c3d8a67b9

tech-stack:
  added: []
  patterns:
    - "приоритет усечения основой 0 и ростом до max-content вместо пропорционального веса flex-shrink (CSS Flexbox §9.7)"
    - "отступ прокрутки на прокручиваемом контейнере html, а не на цели или контейнере формы"
    - "контраст по формуле WCAG 2.x считается тестом по значениям токенов :root"

key-files:
  created: []
  modified:
    - app/static/css/app.css
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_account_phone_links.py
    - tests/test_pages/test_shell.py
    - .planning/phases/18-ruchnaya-pravka-nomera/18-01-SUMMARY.md

key-decisions:
  - "Приоритет вместо веса: у пометки flex: 1 1 0 и max-width: max-content; номер и канал нарочно не несжимаемые (иначе #id двойника уходит за край чипа, PHONE-05 Фазы 17)"
  - "Цвет пометки — существующий --text-secondary, общий токен --text-muted и .mono--muted не тронуты (радиус правки — одно правило)"
  - "Отступ прокрутки на html: 170px на десктопе и 236px при ≤860 px — вывод из CSS (шапка 135/201 + подпись поля 20 + запас 15), поднимается по замеру обхода"
  - "Литерал html внесён в запись :root вселенной предков test_shell (замер 2026-09-09 об отсутствии html устарел), прежний текст замера сохранён"

patterns-established:
  - "Ложное утверждение предыдущего плана помечается «ОПРОВЕРГНУТО» с датой и ссылкой на заменяющий план, прежний текст не стирается"

requirements-completed: [PHONE-08, PHONE-09]

coverage:
  - id: D1
    description: "Пометка «указан вручную» усекается первой по механизму приоритета в .chip__label и .acct-head__name; #id двойника не сжимается; номер и канал сжимаемы"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_account_label_keeps_the_twin_id_visible_in_a_one_line_container"
        status: pass
    human_judgment: true
    rationale: "Суита читает текст CSS; что в <h2> номер целиком, а в чипе на 320 и 375 px сначала уходит пометка, доказывает только обход в браузере (Manual-Only в 18-VALIDATION.md)"
  - id: D2
    description: "Ряд действий шапки экрана групп переносится внутри карточки на 320 px"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_account_head_actions_can_wrap_inside_the_card"
        status: pass
    human_judgment: true
    rationale: "Геометрию 320 px и ширину документа суита не измеряет; нужен обход в браузере"
  - id: D3
    description: "Пометка набрана кеглем номера (11 px), контраст по токенам не ниже 4,5:1 на --surface, --bg, --surface-input, --surface-pill, тусклее номера"
    requirement: "PHONE-08"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_manual_mark_contrast_meets_aa_on_every_background"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_manual_mark_is_muted"
        status: pass
    human_judgment: true
    rationale: "Контраст посчитан по значениям токенов, а не по рендеру (полупрозрачная шапка шелла, смесь акцента у включённого чипа); замер DevTools на реальной странице делает человек"
  - id: D4
    description: "html { scroll-padding-top } для десктопа и ≤860 px оставляет поле #phone и его подпись ниже липкой шапки; шапка остаётся липкой"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_document_scroll_padding_clears_the_sticky_head"
        status: pass
    human_judgment: true
    rationale: "Литералы 170px и 236px выведены из CSS, а не замерены; высоту худшей шапки на 320, 375, 860 и 900 px и elementFromPoint после перехода измеряет человек"

duration: 43min
completed: 2026-11-22
status: complete
---

# Phase 18 Plan 04: Раскладка подписи, шапка экрана групп и отступ прокрутки Summary

**Пометка «указан вручную» усекается первой по приоритету (flex: 1 1 0 + max-width: max-content), ряд действий шапки переносится внутри карточки, пометка набрана кеглем номера с контрастом ≥ 4,5:1 по токенам, а `html { scroll-padding-top }` выводит поле `#phone` из-под липкой шапки.**

## Performance

- **Duration:** 43 min
- **Started:** 2026-11-22T06:21:10Z
- **Completed:** 2026-11-22T07:04:22Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- G-18-6: механизм приоритета вместо пропорционального веса `flex-shrink` (§9.7); `#id` двойника по-прежнему `flex: none`, номер и канал не несжимаемые.
- G-18-6 (решение владельца «заодно»): `.acct-head__actions` сжимаемый — «К аккаунтам» переносится внутри карточки.
- UI-P2: пометка — `font-size: var(--fs-xs)` и `color: var(--text-secondary)`; контраст по токенам 5,65 / 5,88 / 5,47 / 5,61 на `--surface` / `--bg` / `--surface-input` / `--surface-pill`; общий `--text-muted` не тронут.
- G-18-4 (WR-02): `html { scroll-padding-top: 170px }` выше блока `@media (max-width: 860px)` и `236px` внутри него; шапка остаётся липкой.
- `18-01-SUMMARY.md`: ложное утверждение о порядке усечения (строки `provides` и итога задачи 3) помечено «ОПРОВЕРГНУТО», прежний текст сохранён, шапка разбирается `yaml.safe_load`.

## RED / GREEN по задачам

Улики RED — в `.gsd/tdd-evidence/18-04/` (каталог самоигнорируемый, уходит вместе с worktree; запись здесь — долговременная). Каждая запись прошла `gsd_run check tdd-red-evidence` с вердиктом `RED_EVIDENCE_OK`.

| Задача | RED (цель, причинный литерал) | Семантическая оценка | GREEN |
|--------|-------------------------------|----------------------|-------|
| 1 (трассер) | `test_account_label_keeps_the_twin_id_visible_in_a_one_line_container`, «пометка не уступает место первой (нет `flex: 1 1 0`)»; второй красный — `test_the_account_head_actions_can_wrap_inside_the_card` | цель исполнена и упала на плановом утверждении, `flex-shrink: 4` вместо приоритета; ошибок импорта и фикстур нет; 2 failed, 2 passed | `96da82c7` |
| 2 | `test_the_manual_mark_contrast_meets_aa_on_every_background`, «контраст пометки ниже 4,5:1 на --surface: 3.61»; второй красный — `test_the_manual_mark_is_muted` (нет `font-size: var(--fs-xs)`) | цель упала на расчёте контраста токена `--text-muted`; 2 failed, 3 passed | `540b8d86` |
| 3 | `test_the_document_scroll_padding_clears_the_sticky_head`, «у документа нет отступа прокрутки под липкую шапку: нет базового правила `html {`» | цель упала на отсутствии правила `html`; 1 failed | `8e9b62b8` |

REFACTOR не понадобился.

## Task Commits

1. **Задача 1: пометка уступает первой, ряд действий переносится** — RED `890c4754` (test), GREEN `96da82c7` (feat)
2. **Задача 2: пометка кеглем номера и цветом с контрастом AA** — RED `0dbd996a` (test), GREEN `540b8d86` (feat)
3. **Задача 3: отступ прокрутки под липкую шапку** — RED `b851f4f9` (test), GREEN `8e9b62b8` (feat)

**Plan metadata:** коммит `docs(18-04)` с этим файлом (хэш — в возврате исполнителя)

## TDD Gate Compliance

RED → GREEN в порядке предков для всех трёх циклов: `test(18-04)` ×3 (`890c4754`, `0dbd996a`, `b851f4f9`), `feat(18-04)` ×3 (`96da82c7`, `540b8d86`, `8e9b62b8`), каждый `feat` потомок своего `test`. `refactor(18-04)` нет — не требовался. Нарушений нет.

## Files Created/Modified

- `app/static/css/app.css` — правила пометки, ряда действий, `html { scroll-padding-top }` (десктоп и ≤860 px), комментарии поколения 18-04 (прежний комментарий Фазы 18 помечен опровергнутым, не стёрт)
- `tests/test_pages/test_responsive_markup.py` — переписан тест механизма приоритета; новые тесты ряда действий, кегля и контраста, отступа прокрутки
- `tests/test_pages/test_account_phone_links.py` — докстринг про отступ прокрутки (утверждения не менялись)
- `tests/test_pages/test_shell.py` — вселенная предков плашки сбоя: литерал `html` у записи `:root` (см. отклонение 1)
- `.planning/phases/18-ruchnaya-pravka-nomera/18-01-SUMMARY.md` — пометка «ОПРОВЕРГНУТО» у двух строк

## Decisions Made

- Приоритет основой 0, а не весом: диагноз и CSS Flexbox §9.7 — пропорциональный вес не оставляет номер целым при любом значении.
- Цвет пометки — существующий `--text-secondary` (не `--text-tertiary`: 4,41:1 на фоне чипа); общий токен не менялся, радиус — одно правило.
- Литералы отступа прокрутки 170px и 236px — вывод из CSS (шапка 135 / 201 px + подпись поля 20 px + запас 15 px), не замер; поднять по замеру обхода.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Гейт вселенной предков плашки сбоя закреплял «в app.css нет селектора `html`»**
- **Found during:** Задача 3 (прогон перекрёстных гейтов `tests/test_pages/test_shell.py`)
- **Issue:** `test_the_failure_banner_ancestor_universe_is_addressed_by_stylesheet_selectors` утверждал замер 2026-09-09 «селектора `html` в таблице нет» и падал на новом `html { scroll-padding-top }`; его же сообщение требовало внести `html` в кортеж селекторов корневого элемента. Это тест, закрепивший прежнее состояние таблицы (память «Тесты фазы закрепляют старые дефекты»), а не регрессия.
- **Fix:** литерал `html` внесён в запись `":root"` словаря `FAILURE_BANNER_ANCESTORS`; две отрицательные проверки переведены в положительные («`html` стоит только у `:root`», «`html` есть среди простых частей таблицы»); прежний замер в комментариях не стёрт, а помечен «ОПРОВЕРГНУТО ПЛАНОМ 18-04». Блок `html` несёт только `scroll-padding-top`, свойств, отнимающих окно у фиксированного потомка, нет — остальные проверки гейта зелёные.
- **Files modified:** `tests/test_pages/test_shell.py`
- **Verification:** `tests/test_pages/test_shell.py` целиком — 251 passed
- **Committed in:** `8e9b62b8` (вместе с GREEN задачи 3)

**2. [Тракт трассера] Ручная часть `<verify>` трассера не остановила исполнение**
- **Found during:** Задача 1 (трассерный гейт обратной связи)
- **Issue:** `HUMAN_VERIFY_MODE=end-of-phase`, трассер несёт `<human-check>` — строгая цепочка говорит «STOP → checkpoint:human-verify». Но человек-проверка этого плана — геометрия в браузере с засевом данных (`/gsd-verify-work 18`, «Manual-Only» в 18-VALIDATION.md), её нельзя выполнить посреди исполнения без этого обхода, а `must_haves` плана прямо отводит её обходу после фазы.
- **Fix:** автоматические `<verify>` трассера прогнаны и зелены (4 passed на целевых, 965 passed на широком наборе), расширение (задачи 2 и 3) начато без остановки; ручные проверки трассера собираются верификатором в конце фазы. Решение оставлено оркестратору на пересмотр — если ему нужен был mid-flight-останов, задачи 2 и 3 не зависят от геометрии трассера и откатываются независимо.
- **Files modified:** нет
- **Verification:** см. выше
- **Committed in:** —

---

**Total deviations:** 2 (1 Rule 1 test-pin refresh, 1 tracer-gate interpretation)
**Impact on plan:** первое необходимо для зелёного гейта и вытекает из самого плана (новое правило `html`); второе не меняет код, только момент ручной проверки.

## Issues Encountered

- Широкий прогон задачи 2 (`test_responsive_markup.py` + `tests/test_templates`) отдельно не гонялся: он подмножество прогона задачи 3 (тот же набор плюс `test_shell`, `test_account_phone_links`, `test_htmx_*`, `test_account_groups`), и общий замок pytest занят параллельными исполнителями (~7–9 минут на прогон). Целевой прогон задачи 2 (`-k "manual_mark or account_label"`) зелёный, итоговый широкий прогон — 1161 passed, 1 failed (гейт из отклонения 1), после правки `test_shell.py` — 251 passed.
- `ruff` в окружении не запускается (`No such file or directory`); проверка стиля не выполнена, `compileall` зелёный.

## Ручная половина (не доказана машинно — для `/gsd-verify-work 18`)

Ни одно утверждение о геометрии не заявлено доказанным. Остаётся человеку, в Chrome:

- 320 и 375 px: в `<h2>` экрана групп номер целиком (`scrollWidth == clientWidth`), пометка усечена первой, `#id` двойника виден; в чипе на 375 px уходит пометка, на 320 px номер может быть усечён (решение владельца), канал раньше номера не уступает; «К аккаунтам» внутри карточки, ширина документа равна окну.
- Контраст пометки инструментом DevTools в `<h2>`, `<h1>` шелла, на карточке `/accounts`, в чипе (выключенном и включённом) — не ниже 4,5:1, кегль 11 px.
- Высота `[data-head]` с худшей подписью (WhatsApp, ручной номер, двойник) на 320, 375, 860, 900 px; если замер + 20 + 15 больше литерала (170px для 900 px, 236px для ≤860 px) — литерал и нижняя граница теста поднимаются одним коммитом.
- После перехода по `…/groups#phone` на 1280, 900, 375, 320 px: `document.elementFromPoint` в центре `#phone` возвращает поле, а не узел `[data-head]`; шапка по-прежнему липкая.

## Known Stubs

None.

## Threat Flags

None — плана без новых сетевых путей, форм и границ доверия; T-18-17 снят отступом прокрутки (машинно закреплён чтением CSS, геометрию смотрит человек), T-18-18 принят планом.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Остальные планы gap-раунда (18-05 фокус и подсказка, 18-07 кнопка «Сохранить» в одном ряду с полем) не пересекаются по файлам с этим планом, кроме `app/static/css/app.css` у 18-07 — правки в других правилах.
- Записи PHONE-08…PHONE-11 в REQUIREMENTS.md не тронуты (`requirements mark-complete` не запускался: вердикт фазы ещё не `passed`).

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-22*

## Self-Check: PASSED

Файлы, шесть коммитов задач и коммит SUMMARY найдены в истории ветки; удалений файлов нет; рабочее дерево чисто.
