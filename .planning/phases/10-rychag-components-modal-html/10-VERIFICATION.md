---
phase: 10-rychag-components-modal-html
verified: 2026-09-03T05:10:00Z
status: gaps_found
score: 2/4 must-haves verified
behavior_unverified: 1
overrides_applied: 0
gaps:
  - truth: "Критерий 3: панель закрывается существующим Alpine (`x-on:htmx:after-request`)"
    status: failed
    reason: >-
      Ветвь закрытия `if ($event.detail.successful) hide()` МЕРТВА на транспорте, которым
      пользуются 16 из 18 мест. Независимо проверено по вендоренному рантайму:
      в `app/static/js/htmx.min.js` (htmx 2.0.10) присваивание `e.successful` встречается
      РОВНО ОДИН РАЗ (смещение 48147, `e.target=r;e.failed=a;e.successful=!a`), и стоит оно
      ПОСЛЕ раннего возврата ветки `HX-Location` в `Vn` (`if(T(n,/HX-Location:/i)){…Nn("get",e,s);return}`).
      `Vn` — и есть обработчик ответа (`const M=i.handler||Vn`), а `htmx:afterRequest`
      диспетчеризуется из `g.onload` с ТЕМ ЖЕ объектом `T` (`ae(r,"htmx:afterRequest",T)`).
      Следовательно на каждом ответе `location_response()` (204 + `HX-Location`, `app/pages/htmx.py:147-148`)
      `$event.detail.successful` есть `undefined` → ложь → `hide()` не зовётся НИКОГДА.
      `respond()` отдаёт такой ответ на ВСЕХ нефрагментных ветках, то есть на всех местах
      подтверждения фазы, кроме единственной фрагментной ветки `schedules_delete`
      (и фрагмента `account_groups_delete` Фазы 9): `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3`,
      из них за панелью подтверждения стоят два.
      Панель на этих 16 местах уходит НЕ механизмом критерия 3, а свопом `<body>` по
      follow-up GET, а уборку делает Alpine `destroy()`. Механизм, названный критерием
      ПОИМЁННО, на доминирующем транспорте не работает.
    artifacts:
      - path: "app/templates/components/modal.html:467"
        issue: >-
          `x-on:htmx:after-request="sending = false; if ($event.detail.successful) hide()"` —
          условие никогда не истинно на транспорте `HX-Location`.
      - path: "tests/test_templates/test_components.py:1757-1762"
        issue: >-
          Гарнир поведенческой половины подаёт `{ detail: { successful: successful } }` —
          форму события, которой htmx на пути `HX-Location` НЕ ПРОИЗВОДИТ. Правило
          `test_the_panel_closes_only_on_a_successful_exchange` зелено на форме, не
          встречающейся у 16 из 18 мест: отличить исправную панель от сегодняшней оно не может.
      - path: "app/templates/components/modal.html:57-63"
        issue: >-
          Запись шапки приписывает ветви наоборот («на фрагментном пути `hide()` не
          вызывается ВОВСЕ»). Отсоединение узла слушателей не снимает: OOB-`delete`
          происходит синхронно внутри свопа, `htmx:afterRequest` летит в той же задаче,
          а Alpine сносит компонент из колбэка MutationObserver, то есть МИКРОЗАДАЧЕЙ ПОЗЖЕ.
          Значит `hide()` живёт как раз на фрагментном пути, а `destroy()` приземляется
          только на пути перехода — зеркально записанному.
    missing:
      - >-
        Читать величину, которую htmx выставляет на ОБОИХ путях (например
        `$event.detail.xhr.status` в диапазоне 2xx-3xx), либо оставить
        `$event.detail.successful` и добавить явную ветку `HX-Location` с названным
        в комментарии ранним возвратом.
      - >-
        Перенацелить JS-гарнир на РЕАЛЬНЫЕ формы события: `{ detail: { xhr: { status: 204,
        getResponseHeader: () => '/ads' } } }` без ключа `successful` — для транспорта
        перехода, и `{ detail: { successful: true, xhr: { status: 200 } } }` — для
        фрагментного.
      - >-
        Исправить запись шапки `modal.html:57-63` об атрибуции двух ветвей и утверждать
        в правиле ИМЕННО ветвь (какая из двух отработала), а не итоговую позицию фокуса.
  - truth: "DEF-09-02 — «Отмена» панели закрывает панель, но летящий запрос не отменяет; назначенная фаза — 10"
    status: partial
    reason: >-
      Пункт назначен Фазе 10 ПОИМЁННО (`.planning/REQUIREMENTS.md:428`, открытое окно 15
      в `.planning/WINDOWS.md`) с основанием «фаза, которой макрос принадлежит». Ни один
      артефакт фазы 10 (планы, сводки, CONTEXT, REVIEW) слова `DEF-09-02` не содержит: он
      не закрыт, не отложен записью и не перемаршрутизирован. При этом фаза РАСШИРИЛА его
      предмет с одного места до 18 — `x-on:keydown.escape.window="hide()"` и
      `x-on:click="hide()"` на оверлее не спрашивают `sending`, а признак отправки теперь
      стои́т на всех 18 панелях.
    artifacts:
      - path: "app/templates/components/modal.html:459,462"
        issue: "Esc и оверлей закрывают панель во время летящего необратимого запроса."
    missing:
      - "Либо закрыть DEF-09-02 (гейт отмены на `sending`, либо реальный `abort`), либо записать перемаршрутизацию с основанием и обновить окно 15 в WINDOWS.md."
behavior_unverified_items:
  - truth: "Критерий 2: ответ снимает осиротевшую панель подтверждения вторым OOB-узлом `hx-swap-oob=\"delete\"` по её `id`"
    test: >-
      В браузере: открыть редактор объявления с ≥3 расписаниями, удалить расписание через
      панель подтверждения; повторить N раз. Затем в консоли:
      `document.querySelectorAll('[role=\"dialog\"]').length` и
      `document.querySelectorAll('[id^=\"sched-del-\"]').length`.
    expected: >-
      После N удалений в документе НЕ остаётся N осиротевших `role="dialog"`: число
      панелей равно числу оставшихся карточек расписаний, а `#sched-N` и `#sched-del-N`
      удалённых расписаний отсутствуют оба.
    why_human: >-
      Роадмап называет это ЕДИНСТВЕННЫМ выводом фазы, взятым из документации и не
      проверенным ни на чём (ручной UAT, пункт 4). httpx не свопает и внеполосных узлов
      не применяет: суита доказывает только ПРИСУТСТВИЕ узла в теле ответа, а не то, что
      рантайм его применил.
human_verification:
  - test: >-
      Открыть редактор объявления с ≥3 расписаниями, удалить расписание через панель N раз;
      считать `document.querySelectorAll('[role="dialog"]').length` и `[id^="sched-del-"]`.
    expected: "После N удалений осиротевших диалогов с живыми ловушками фокуса в документе нет."
    why_human: "OOB-снятие применяется рантаймом htmx; httpx свопов не делает. Ручной UAT, пункт 4 перечня роадмапа."
  - test: >-
      Замедлить сеть (Slow 3G), подтвердить удаление на ЛЮБОМ из 16 мест, отвечающих 204 +
      `HX-Location`, и оборвать follow-up GET (Offline сразу после нажатия).
    expected: >-
      Панель не остаётся висеть поверх устаревшего экрана с `is-modal-open` на `<html>`.
    why_human: >-
      Это наблюдаемое следствие мёртвой ветви критерия 3: уборка на этом транспорте зависит
      ЦЕЛИКОМ от `destroy()`, срабатывающего при свопе `<body>`. Не сработал своп — не
      сработала и уборка. Суита этого пути не поднимает.
  - test: "Вызвать 500 на маршруте за панелью подтверждения и наблюдать панель."
    expected: "Панель ОСТАЁТСЯ открытой, поверх встаёт плашка аварии, повтор возможен без переоткрытия."
    why_human: "Половина D-12, работающая на всех транспортах (на 5xx `successful` присваивается), но наблюдаемая только глазом."
  - test: "Подтвердить удаление и проверить `document.activeElement` после ухода панели на фрагментном и на переходном пути."
    expected: "Фокус приземлился в `#notice`, а не на `<body>`."
    why_human: "Приземление фокуса поднимает Alpine и реальный своп; суита исполняет объект `x-data` в интерпретаторе со стаб-документом."
---

# Phase 10: Рычаг `components/modal.html` — Verification Report

**Phase Goal:** подтверждение удаления идёт через htmx во всех 18 местах одной правкой одного файла, и после N удалений в документе не остаётся N мёртвых диалогов
**Verified:** 2026-09-03T05:10:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Все 18 мест подтверждения удаления работают через htmx одной правкой `components/modal.html`; инвентарь утверждён ЧИСЛОМ; `test_modal_guard_is_inherited_by_every_consumer` и `test_modal_site_inventory` РАСШИРЕНЫ | ✓ VERIFIED | Макрос `modal()` (`app/templates/components/modal.html:444,466-467,470`) печатает `hx-post` / `hx-swap="none"` / `hx-disabled-elt` / `hx-indicator` и узел `.form-busy` БЕЗУСЛОВНО; параметры `hx_post` и `hx_include` из сигнатуры сняты (диff `7c1041d..HEAD`). Инвентарь: `MODAL_IMPORTERS=11`, `MODAL_EVENT_NAMES=9`, `MODAL_PLACES=18`, `MODAL_CONSUMERS` — 10 имён. Оба названных правила расширены НАСТОЯЩИМИ утверждениями, а не только прогнаны: гард получил проверку `"{%" not in form_tag` и присутствие `PANEL_QUALITY_SOURCE_PROPERTIES` в открывающем теге (`test_components.py:1417-1434`), инвентарь — ЧЕТВЁРТЫЙ счёт «имена именованных аргументов вызывающих ⊆ сигнатура макроса» (`:1490-1500`) с антивакуумом. Поведенчески: `test_every_confirmed_delete_route_answers_both_transports` шлёт настоящий POST с `HX-Request` по 8 маршрутам × исходы и утверждает 204 + `HX-Location` (или 200 + фрагмент). Прогон: `87 passed`. Все 9 маршрутов за вызовами `modal()` стоя́т на `respond()`. |
| 2 | Ответ снимает осиротевшую панель вторым OOB-узлом `hx-swap-oob="delete"` по её `id` | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Узел присутствует и адресован верно: `ads/partials/sched_delete_response.html:71-72` — `<div id="sched-{{ schedule_id }}" hx-swap-oob="delete">` и `<div id="sched-del-{{ schedule_id }}" hx-swap-oob="delete">`; тот же парный узел у Фазы 9 (`account_groups/partials/delete_response.html:99-100`). Структурная предпосылка держится: панель стои́т СНАРУЖИ удаляемой карточки — `sched_card.html:112` открывает `<article id="sched-{{ s.id }}">`, а `{% call modal(id='sched-del-' ~ s.id …) %}` (`:274`) стои́т ПОСЛЕ `</article>`. ФАКТИЧЕСКОЕ снятие рантаймом не проверено ничем: роадмап сам называет это ручным UAT, пункт 4, планы объявляют `verification: backstop`. httpx свопов не делает. → человеку. |
| 3 | Панель закрывается существующим Alpine (`x-on:htmx:after-request`) — новых строк JS фаза не добавляет | ✗ FAILED | Вторая половина держится: `git diff 7c1041d..HEAD -- app/static/js/` ПУСТ; `test_criterion_three_holds_by_the_numbers` (четыре числа: вендоренные файлы, `KNOWN_SUBMIT_HANDLER_FILES`, ноль `hx-on`, `CLIENT_STATE_NODES=24`) зелен; прочтение «новые СУЩНОСТИ, а не правка существующих» — решение владельца D-13, записанное ДО исполнения (`10-CONTEXT.md:197-210`) и продублированное в шапке компонента. ПЕРВАЯ ПОЛОВИНА НЕ ДЕРЖИТСЯ: механизм мёртв на транспорте 16 из 18 мест — разбор в `gaps` и в разделе «Adjudication: CR-01» ниже. |
| 4 | Все 10 потребителей `modal.html` продолжают удалять без JS: панель остаётся настоящей формой POST с непустым `action` | ✓ VERIFIED | В макросе `method="{{ method }}"` при умолчании `method="post"` литералом и `action="{{ action }}"`; `hx-post="{{ action }}"` выписан ТЕМ ЖЕ выражением. Гейты деградации Фазы 8 наследование держат: `test_every_such_form_keeps_its_method_and_action` (G-3) и `test_the_post_attribute_matches_the_action_character_for_character` (G-4, сравнение по СЫРОЙ строке шаблона). Поведенчески: половина деградации того же обхода шлёт POST БЕЗ `HX-Request` и утверждает `302` и `location`, ПОСИМВОЛЬНО равный ожидаемому, по 8 маршрутам × исходы. `87 passed`. |

**Score:** 2/4 truths verified (1 present, behavior-unverified; 1 failed)

### Adjudication: CR-01 (независимая, не унаследованная)

Заявление ревизии проверено ПО ИСХОДНИКУ РАНТАЙМА, а не принято и не отброшено.

1. `app/static/js/htmx.min.js` (2.0.10): строка `successful` встречается в бандле **ровно один раз** — присваивание `e.target=r;e.failed=a;e.successful=!a` на смещении 48147.
2. Оно стои́т ПОСЛЕ раннего возврата ветки перехода в `Vn`: `if(T(n,/HX-Location:/i)){let e=n.getResponseHeader("HX-Location");…Nn("get",e,s);return}`.
3. `Vn` и есть обработчик ответа: `const M=i.handler||Vn`, а проект собственного `handler` не подставляет (`app/static/js/` фазой не тронут, `hx-on` в дереве ноль).
4. `htmx:afterRequest` летит из `g.onload` с ТЕМ ЖЕ объектом: `M(r,T); … ae(r,"htmx:afterRequest",T)`.
5. `location_response()` (`app/pages/htmx.py:147-148`) отдаёт `Response(status_code=204, headers={HX_LOCATION_HEADER: …})`, и `respond()` выбирает его на КАЖДОЙ нефрагментной ветке.

**Вердикт: CR-01 подтверждён фактически.** `$event.detail.successful` на транспорте перехода есть `undefined`, и `hide()` из выражения критерия 3 там не вызывается никогда. Обработчиков, отдающих фрагмент, объявлено три (`FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3`), за панелью подтверждения из них стоят два, — то есть механизм критерия 3 работает на 2 из 18 мест.

**Что при этом НЕ сломано, и это названо честно:** видимый исход счастливого пути верен — панель уезжает вместе со свопом `<body>`, а `destroy()` снимает `is-modal-open` и приземляет фокус. Защитная половина D-12 («панель остаётся на отказе») работает ВЕЗДЕ: у 5xx заголовка `HX-Location` нет, ранний возврат не срабатывает, `successful=false` присваивается штатно; у `onerror`/`onabort`/`ontimeout` признак остаётся `undefined` — то есть ложью, и панель тоже остаётся открытой.

**Почему это всё равно FAILED, а не WARNING:** (а) критерий 3 называет механизм ПОИМЁННО, и на 16 из 18 мест он не работает; (б) единственное правило, которое его стережёт, зелено на форме события, которой htmx на этом пути не производит, — оно не отличает исправную панель от сегодняшней; (в) запись в шапке компонента утверждает противоположное реальному рантайму (атрибуция `hide()`/`destroy()` перевёрнута), а в этом проекте запись есть несущий контракт; (г) остаётся наблюдаемое следствие: не доехавший follow-up GET оставляет панель поверх устаревшего экрана с блокировкой прокрутки.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `app/templates/components/modal.html` | Сигнатура без `hx_post`/`hx_include`, безусловные атрибуты | ✓ VERIFIED | 478 строк; `{% macro modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post") %}`; в открывающем теге формы `{%` нет |
| `app/templates/ads/partials/sched_delete_response.html` | Три внеполосных узла верхнего уровня | ✓ VERIFIED | `:71-73` — снятие `#sched-N`, снятие `#sched-del-N`, `innerHTML:#sched-count` |
| `app/templates/ads/includes/sched_count_rule.html` | Единственный источник линейки счётчика | ✓ VERIFIED | Включается и страницей (`ads/form.html:219` обёртка `<div id="sched-count">`), и узлом ответа |
| `app/pages/schedules.py` | `_editor_url`, `_ad_has_a_schedule`, `_ad_schedule_count`, переведённый `schedules_delete` | ✓ VERIFIED | Собственного `RedirectResponse` у `schedules_delete` нет ни в одной ветке, включая «нет сессии» (`:909`) |
| `tests/test_templates/test_components.py` | Расширенные два правила + `test_the_panel_hands_the_sending_state_to_every_call_site` + гейт критерия 3 | ⚠️ ORPHANED (частично) | Правила существуют и зелены; но `test_the_panel_closes_only_on_a_successful_exchange` стережёт мёртвую ветвь синтетическим событием |
| `tests/test_pages/test_confirm_delete_transport.py` | Обход обоих транспортов | ✓ VERIFIED | 8 маршрутов, 302 + посимвольный `location` на деградации, 204 + `HX-Location` на слое письма |
| `tests/test_pages/test_htmx_gates.py` | `FRAGMENT_RESPONSE_HANDLERS` и три правила согласованности | ✓ VERIFIED | `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3`, правило непересечения с `NOT_YET_CONVERTED` |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `modal()` без признака отправки | 14 вызовов в 11 файлах | Безусловные атрибуты макроса | ✓ WIRED | Четвёртый счёт инвентаря утверждает, что снятый параметр не вернулся ни одним вызывающим |
| `sched_delete_response.html` | `#sched-N`, `#sched-del-N` | `hx-swap-oob="delete"` | ✓ WIRED (разметочно) | Оба узла верхнего уровня; фактическое применение — UAT |
| `sched_count_rule.html` | `ads/form.html` и узел ответа | `{% include %}` | ✓ WIRED | Один источник, обёртка `#sched-count` переживает ответы |
| `_editor_url` | `respond(redirect=)` и `_editor_redirect` | Один помощник адреса | ✓ WIRED | Оба транспорта приземляются на один адрес |
| `x-on:htmx:after-request` → `hide()` | Панель на транспорте `HX-Location` | `$event.detail.successful` | ✗ NOT_WIRED | Признак на этом пути `undefined`: связь разорвана рантаймом, а не разметкой |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `sched_delete_response.html` | `schedule_id` | Из ПУТИ запроса, а не из найденной строки | ✓ | ✓ FLOWING — повтор неотличим от первого удаления |
| `sched_count_rule.html` | `schedules_count` | `_ad_schedule_count(db, user.id, ad_id)` с `join(Ad)` по владельцу | ✓ | ✓ FLOWING |
| `modal()` | `action` | Аргумент вызывающего, тот же в `action` и `hx-post` | ✓ | ✓ FLOWING |
| Панель после успеха на `HX-Location` | `$event.detail.successful` | Рантайм htmx (не присваивается на этом пути) | ✗ | ✗ DISCONNECTED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Оба транспорта всех подтверждённых маршрутов | `uv run pytest -q -p no:randomly tests/test_pages/test_confirm_delete_transport.py tests/test_pages/test_editor_schedules.py` | `87 passed` | ✓ PASS |
| Расширенные правила критерия 1 + гейт критерия 3 | `uv run pytest -q` по 5 именованным узлам `test_components.py` | `5 passed` | ✓ PASS |
| Вендоренные сценарии фазой не тронуты | `git diff 7c1041d..HEAD -- app/static/js/` | пусто | ✓ PASS |
| Присваивание `successful` в рантайме htmx | поиск по `app/static/js/htmx.min.js` | 1 вхождение, ПОСЛЕ раннего возврата `HX-Location` | ✗ FAIL (критерий 3) |
| Долговые маркеры в файлах фазы | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` по 22 изменённым файлам | ноль вхождений | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| --- | --- | --- | --- |
| — | — | — | SKIPPED — фаза probe-скриптов не объявляет, `scripts/*/tests/probe-*.sh` в дереве нет |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| FORM-06 | 10-01, 10-02, 10-03, 10-04 | Подтверждение удаления через htmx во всех 18 местах одной правкой `components/modal.html`; ответ снимает осиротевшую панель вторым OOB-узлом | ✓ SATISFIED (машинная половина) / ? NEEDS HUMAN (снятие панели) | Первая половина доказана инвентарём и обходом обоих транспортов; вторая — присутствием узла, применение — UAT, пункт 4 |
| DEF-09-02 | — | «Отмена» панели закрывает панель, но летящий запрос не отменяет; назначенная Фаза 10 | ✗ ORPHANED | `.planning/REQUIREMENTS.md:428`, открытое окно 15 в `.planning/WINDOWS.md`. Ни один артефакт фазы 10 его не называет — ни закрыт, ни отложен, ни перемаршрутизирован |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `tests/test_templates/test_components.py` | 1757-1762 | Гарнир синтезирует форму события, которой рантайм на доминирующем транспорте не производит | 🛑 Blocker | Гейт зелен независимо от исправности механизма критерия 3 |
| `app/templates/components/modal.html` | 57-63 | Запись противоречит рантайму: атрибуция `hide()`/`destroy()` перевёрнута | ⚠️ Warning | В проекте, где запись есть контракт, следующий читатель «починит» верную ветвь |
| `app/templates/components/modal.html` | 459, 462 | Esc и оверлей зовут `hide()` не спрашивая `sending` | ⚠️ Warning | Предмет DEF-09-02, размноженный фазой с 1 места до 18 |
| `app/templates/components/modal.html` | 444, 466-467 | Параметр `method=` жив, а `hx-post` захардкожен POST-ом | ⚠️ Warning | Латентный разъезд базового и улучшенного пути; не-POST вызывающих сегодня нет (WR-03) |
| `app/pages/schedules.py` | 911-928 | `await request.form()` стои́т ПОСЛЕ `commit()` | ⚠️ Warning | Падение разбора тела оставляет строку удалённой, а человеку отдаёт 500 (WR-08) |
| `app/pages/schedules.py` | 942-962 | Докстринг обещает guard по `return_to`, которого в условии нет | ⚠️ Warning | Запрос с `HX-Request`, но без `return_to` уходит в ветку фрагмента с узлами, у которых на сводном экране нет целей (WR-01) |
| `app/templates/ads/partials/sched_delete_response.html` | 73 | Узел счётчика перечнем изъятий докстринга не покрыт | ⚠️ Warning | Кросс-объявленческое удаление пишет счёт чужого объявления в `#sched-count` открытого редактора (WR-10) |
| `tests/test_pages/test_confirm_delete_transport.py` | 587, 838 | `CONFIRMED_DELETE_ROUTES` — литеральный кортеж с литеральным числом 8; `account_groups_delete` в нём нет | ⚠️ Warning | Новый маршрут за панелью краснит инвентарь, но обход остаётся зелёным и маршрут — недоказанным на обоих транспортах (WR-04) |
| `.planning/ROADMAP.md` | 72, 448 | Живые записи вехи по-прежнему говорят «16 мест подтверждения» | ⚠️ Warning | План 10-04 объявил расхождение закрытым; критерий 1 и FORM-06 исправлены на 18, строка перечня фаз и §448 — нет |
| `tests/test_templates/test_htmx_inventory.py` | 203 | `CONDITIONAL_PLACES = 2` не сдвинут | ℹ️ Info | Исполнитель обосновал: константа инвентаризирует УСЛОВНЫЕ ВХОДЫ ЧТЕНИЯ (`hx-get`). Свойство роадмапа («условие ушло из тега формы панели») закрыто другим правилом — `"{%" not in form_tag` |

### Human Verification Required

#### 1. Снятие осиротевшей панели (критерий 2, UAT пункт 4)

**Test:** Открыть редактор объявления с ≥3 расписаниями, удалить расписание через панель N раз, затем в консоли — `document.querySelectorAll('[role="dialog"]').length` и `document.querySelectorAll('[id^="sched-del-"]').length`.
**Expected:** Осиротевших диалогов с живыми ловушками фокуса не остаётся; `#sched-N` и `#sched-del-N` удалённых расписаний отсутствуют оба.
**Why human:** Единственный вывод фазы, взятый из документации и не проверенный ни на чём. httpx не свопает и внеполосных узлов не применяет.

#### 2. Уборка панели при не доехавшем follow-up GET

**Test:** Slow 3G → подтвердить удаление на любом из 16 мест, отвечающих 204 + `HX-Location` → Offline сразу после нажатия.
**Expected:** Панель не остаётся висеть поверх устаревшего экрана с `is-modal-open` на `<html>`.
**Why human:** Прямое следствие мёртвой ветви критерия 3: уборка на этом транспорте зависит целиком от `destroy()` при свопе `<body>`.

#### 3. Панель остаётся открытой на отказе

**Test:** Вызвать 500 на маршруте за панелью подтверждения.
**Expected:** Панель остаётся открытой, поверх встаёт плашка аварии, повтор возможен без переоткрытия.
**Why human:** Половина D-12, работающая на всех транспортах, но наблюдаемая только глазом.

#### 4. Приземление фокуса в `#notice`

**Test:** Подтвердить удаление и посмотреть `document.activeElement` после ухода панели — на фрагментном и на переходном пути.
**Expected:** Фокус в `#notice`, а не на `<body>`.
**Why human:** Требует настоящих Alpine и htmx; суита исполняет `x-data` в интерпретаторе со стаб-документом.

### Gaps Summary

Цель фазы достигнута НАПОЛОВИНУ, и разрез проходит ровно по критерию 3.

Первая половина цели — «подтверждение идёт через htmx во всех 18 местах одной правкой одного
файла» — держится и держится хорошо. Рычаг дёрнут по-настоящему: два параметра сняты с
сигнатуры, атрибуты печатаются безусловно, и это утверждается не заявлением, а расширенными
правилами (`"{%" not in form_tag`, четвёртый счёт по именованным аргументам вызывающих) плюс
сквозным обходом, который шлёт настоящий POST по восьми маршрутам на обоих транспортах.
Деградация — критерий 4 — не тронута: 302 и посимвольно тот же адрес.

Вторая половина — «после N удалений не остаётся N мёртвых диалогов» — доказана разметочно и
честно объявлена ручной: узлы `hx-swap-oob="delete"` стоя́т парой и адресованы верно, панель
действительно живёт СНАРУЖИ удаляемой карточки, но применяет узлы рантайм, которого суита не
поднимает.

Провален критерий 3, и провален он не на словах. Ветвь `if ($event.detail.successful) hide()`,
заведённая ради D-12, мертва на транспорте, которым пользуются 16 из 18 мест: htmx 2.0.10
возвращается из обработчика ответа ДО присваивания `successful`, увидев заголовок
`HX-Location`, а `respond()` отдаёт именно такой ответ на каждой нефрагментной ветке. Хуже
самой мёртвой ветви — то, что стерегущее её правило зелено на форме события, которой htmx на
этом пути не производит: гейт не отличает исправную панель от сегодняшней, и следующая фаза
унаследует зелёный цвет как доказательство. Рядом стои́т третья цена: запись в шапке
компонента приписывает две ветви ухода узла ровно наоборот тому, что делает рантайм.

Отдельной позицией — `DEF-09-02`. Он назначен ЭТОЙ фазе поимённо и остаётся открытым окном;
ни один артефакт фазы его не называет, а сама фаза его предмет размножила с одного места до
восемнадцати.

Что фазу НЕ порочит: единственный красный тест суиты
(`test_the_overview_error_number_matches_the_users_own_dashboard`) предсуществующий,
воспроизведён на дофазовом `7c1041d` и записан окном 27; расхождение `CONDITIONAL_PLACES`
обосновано исполнителем по существу и свойство роадмапа закрыто другим правилом; долговых
маркеров в 22 изменённых файлах ноль.

---

_Verified: 2026-09-03T05:10:00Z_
_Verifier: Claude (gsd-verifier)_
