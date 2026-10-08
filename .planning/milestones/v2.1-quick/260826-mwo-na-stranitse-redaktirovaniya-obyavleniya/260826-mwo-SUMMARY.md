---
phase: quick-260826-mwo-sched-toggle-collapses-card
plan: 01
subsystem: pages/schedules + templates/ads
status: complete
tags: [ui, schedules, ads-editor, regression, bugfix]
requires:
  - app/pages/ads.py (expanded_schedule_id — источник разворота)
provides:
  - Разворот карточек расписания переживает нажатие тумблера
affects:
  - app/pages/schedules.py
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/form.html
tech-stack:
  added: []
  patterns:
    - Пронос серверного состояния через скрытое поле POST-формы (рядом с существующим `return_to`)
    - Отбрасывающая целочисленная коэрция значения формы перед попаданием в строку адреса
key-files:
  created: []
  modified:
    - app/pages/schedules.py
    - app/templates/ads/includes/sched_card.html
    - app/templates/ads/form.html
    - tests/test_pages/test_editor_schedules.py
decisions:
  - Разворот выводится ВНУТРИ макроса из `expanded_id`, а не приходит вторым булевым параметром: два параметра об одном факте способны разойтись
  - Параметр `expanded` ЗАМЕНЁН, а не дополнен: Jinja падает TypeError-ом на неизвестном именованном аргументе, поэтому пропущенный вызов отказал бы громко
  - Испорченное значение поля отбрасывается, а не отвергается: переключение расписания не должно теряться из-за поля разворота
metrics:
  duration: ~25 мин
  completed: 2026-08-26
actuals:
  tokens: 40000
  tasks: 2
  commits: 3
---

# Quick 260826-mwo: тумблер расписания сворачивал и разворачивал карточки — Summary

Нажатие тумблера в редакторе объявления больше не меняет разворот карточек: идентификатор развёрнутой карточки едет скрытым полем `keep_sched` через POST тумблера, и обработчик возвращает пользователя к БЫВШЕМУ развороту вместо идентификатора нажатой карточки.

## Что было сделано

**Задача 1 (tracer, TDD) — пронос разворота через POST.**

RED: `test_the_toggle_does_not_fold_or_unfold_the_schedule_card` — сквозной тест, берущий скрытые поля формы тумблера ИЗ ОТРЕНДЕРЕННОЙ разметки, отправляющий их POST-ом и запрашивающий адрес ответа. Падал до правки (`b91f2aa`) с сообщением «свёрнутая карточка РАЗВЕРНУЛАСЬ от нажатия собственного тумблера»; лог прогона показал дефект дословно: `GET /ads/1/edit?sched=2` → `POST /schedules/1/toggle` → `GET /ads/1/edit?sched=1`.

GREEN (`d602502`):
- `sched_card.html` — параметр `expanded=false` заменён на `expanded_id=none`, локальное `expanded` выводится сразу за сеттером `account`; тело макроса не правлено ни строкой.
- В форме тумблера, сразу за `return_to`, добавлено скрытое поле `keep_sched`, отрисовываемое только когда развёрнутая карточка есть.
- `ads/form.html` — единственный вызов макроса (строка 202) передаёт `expanded_id=editor.expanded_schedule_id`; прежнего имени аргумента в вызове не осталось.
- `app/pages/schedules.py` — `_expanded_from_form(form_data) -> int | None` по образцу `_clean_ints`; в `schedules_toggle` заменён ТОЛЬКО третий аргумент оператора возврата.

**Задача 2 (TDD) — границы значения и правда в докстринге** (`d03cb48`): три именованные регрессии + приведение докстринга `_editor_redirect` в соответствие с кодом.

## Отклонения от плана

Нет — план исполнен как написан.

## Проверка (фактические прогоны)

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_editor_schedules.py -k test_the_toggle_does_not_fold_or_unfold_the_schedule_card -q` ДО правки | **1 failed** — RED-гейт подтверждён фактом прогона |
| `uv run pytest tests/test_pages/test_editor_schedules.py -q` после задачи 1 | **41 passed** |
| `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedules_list.py tests/test_pages/test_ads_status.py -q` | **283 passed**, 0 failed (5:03) |
| `grep -c "keep_sched" app/templates/ads/includes/sched_card.html` | `1` |
| `grep -v '^\s*#' app/pages/schedules.py \| grep -c "keep_sched"` | `1` — имя живёт в КОДЕ, а не только в пояснении |
| `grep -c "expanded=" app/templates/ads/form.html` | `0` — старый аргумент из вызова ушёл |
| `sed -n '/^def _editor_redirect/,/^def _apply_named_actions/p' … \| grep -c "ни при каких условиях"` | `0` — неверная фраза снята |
| то же с `grep -c "T-02-23"` | `1` — прослеживаемость сохранена |
| `git diff --stat dc1ec42` | `schedule_row.html` и `app/routes/schedules.py` НЕ задеты |
| `graphify update .` | успешно: 12512 узлов, 23943 ребра |

## Критерии успеха

- [x] Тумблер меняет только состояние расписания; разворот после нажатия тот же, что был до него, для ВСЕХ карточек.
- [x] Ни один существующий тест не покраснел; `test_update_from_editor_returns_to_the_editor` и `test_incomplete_schedule_cannot_be_switched_on` зелёные без правки.
- [x] Докстринг `_editor_redirect` не утверждает про код неправды.

## Модель угроз

- **T-mwo-01 (Tampering, mitigate)** — закрыто: `int()` с перехватом `(TypeError, ValueError)`; закреплено `test_a_malformed_expansion_field_is_dropped_instead_of_crashing`, где в поле уходит `1&sched=99#hack` и ответ — 302 с чистым адресом.
- **T-mwo-03 (EoP, mitigate)** — закрыто сохранностью: выборка с `join(Ad, Ad.user_id == user.id)` и ветка `resume_blocked` не тронуты; `test_incomplete_schedule_cannot_be_switched_on` зелёный.
- **T-mwo-04 (DoS, mitigate)** — исключения перехвачены, 500 на пути тумблера не возникает.
- **T-mwo-02 (Info Disclosure, accept)** — принято планом без изменений: подделанный чужой номер даёт лишь параметр адреса, редактор его отбрасывает.

Новой security-relevant поверхности сверх зарегистрированной в плане не появилось.

## Known Stubs

Нет. Заглушек, пропущенных тестов и непрогнанных проверок не осталось.

## Коммиты

| Хеш | Сообщение |
|---|---|
| `b91f2aa` | test(quick-260826-mwo): тумблер расписания не должен менять разворот карточек |
| `d602502` | fix(quick-260826-mwo): тумблер расписания сохраняет разворот карточек |
| `d03cb48` | test(quick-260826-mwo): границы поля разворота и докстринг `_editor_redirect` |

## Self-Check: PASSED

Все три коммита найдены в `git log --oneline --all`. Все четыре изменённых файла на месте, SUMMARY.md записан. `git diff --diff-filter=D dc1ec42 HEAD` пуст — ни один файл не удалён.
