---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
plan: 13
subsystem: ui
tags: [htmx, jinja2, fastapi, keyset-pagination, infinite-scroll, oob-swap]

requires:
  - phase: 09-05
    provides: четвёртый внеполосный узел починки курсора и оба охраняющих теста, чей зеркальный отказ этот план и закрывает
  - phase: 09-11
    provides: условное объявление включаемых данных и перечень INCLUDE_TARGET_EXCEPTIONS, потерявший здесь предмет
provides:
  - Контракт курсора прокрутки экрана групп на КЛЮЧЕ последней отрисованной строки (`after_id`) вместо свободно плавающего абсолютного смещения
  - Регрессионный тест чередования, прошедший путь RED → GREEN двумя разными коммитами
  - Положительный контроль обратного порядка применения ответов
  - Правило IN-01: шапка ответа удаления держит число своих внеполосных узлов ПРАВИЛОМ, а не читателем
  - Обе половины антивакуумной замены правила включаемых данных на подставленном дереве
  - Блокировка прокрутки тела за открытой панелью подтверждения (добавка `scroll-lock`)
affects: [09-14, 09-15, 09-16, "Фаза 10", "Фаза 11", "Фаза 15"]

actuals:
  tokens: 48000
  tasks: 4
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Keyset-курсор бесконечной прокрутки: сентинел несёт ключ последней отрисованной строки, маршрут порции добирает строки строго больше него"
    - "Антивакуум правила, потерявшего предмет, переезжает на ПОДСТАВЛЕННОЕ дерево и получает отрицательный контроль — обе половины, ни одна не факультативна"
    - "Инвентарное число, потерявшее предмет, сдвигается ПРОГОНОМ покрасневшего правила, а не вычитанием"

key-files:
  created: []
  modified:
    - app/pages/account_groups.py
    - app/templates/account_groups/includes/sentinel.html
    - app/templates/account_groups/includes/group_row.html
    - app/templates/account_groups/list.html
    - app/templates/account_groups/partial_cards.html
    - app/templates/account_groups/partials/delete_response.html
    - app/templates/components/modal.html
    - app/static/css/app.css
    - tests/test_pages/test_account_groups.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_templates/test_htmx_inventory.py
    - tests/test_pages/test_htmx_preserved.py
    - tests/test_pages/test_history_retry.py
    - .planning/phases/09-pilot-na-account-groups-skvoznoy-kontrakt-formy/09-13-PLAN.md

key-decisions:
  - "Форма контракта курсора — `keyset` (решение владельца, задача 2): сентинел несёт ключ последней отрисованной строки, четвёртый внеполосный узел уходит из дерева целиком"
  - "`scroll-lock` принят ДОБАВКОЙ, а не самостоятельным закрытием: тест чередования зеленеет по причине `keyset`, а не по причине блокировки прокрутки"
  - "Ветвь `serialize` отвергнута ПРОЧТЕНИЕМ ИСХОДНИКА до выбора: применимо `test_no_opaque_address_declares_a_request_queue`, а не правило периметра"
  - "Отказ владельца от `always-present-cursor` (09-11) пересмотрен сознательно: арифметика доказана источником зеркального отказа исполнением, а не рассуждением"
  - "Запись `INCLUDE_TARGET_EXCEPTIONS['group-list-sentinel']` закрыта записью летописи, а не удалена молча; прежний текст сохранён целиком"

patterns-established:
  - "Закрытие класса отказа через НЕВЫРАЗИМОСТЬ: величина, которую можно было применить не к тому узлу, убрана из контракта, а не обложена проверками"
  - "Правило, потерявшее предмет, ОБРАЩАЕТСЯ, а не снимается: «узел обязан быть внеполосной целью» → «узла в внеполосных целях нет», плюс антивакуум о его существовании"
  - "Инвентарное число ставится прогоном: ожидание `30` для подставленного дерева прогон опроверг числом `60`"

requirements-completed: [FORM-02, FORM-09, QUAL-01]

coverage:
  - id: D1
    description: "Курсор бесконечной прокрутки не может уехать НАЗАД от ответа удаления: чередование «порция приехала между снятием величины и применением ответа» не задваивает строк"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_an_interleaved_portion_and_delete_never_double_a_row"
        status: pass
    human_judgment: false
  - id: D2
    description: "Порядок, в котором отказ НЕ живёт, исполняется отдельным положительным контролем: правило ловит ТОЛЬКО нарушение"
    requirement: QUAL-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_control_positive_the_reverse_order_keeps_the_document_whole"
        status: pass
    human_judgment: false
  - id: D3
    description: "Переход цвета доказан историей: RED на 5de9c56, GREEN на 0326694, тест между ними не тронут"
    verification:
      - kind: other
        ref: "git log --oneline: 5de9c56 test(09-13) → 0326694 feat(09-13)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Повторное удаление безвредно и неотличимо для чужой, несуществующей и уже удалённой группы; ветви по факту удаления в шаблоне ответа нет"
    requirement: QUAL-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_a_no_op_delete_does_not_double_a_row"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_the_delete_response_is_indistinguishable_for_a_foreign_and_a_missing_group"
        status: pass
    human_judgment: false
  - id: D5
    description: "Обе формы экрана деградируют без htmx: 302 на адрес экрана с сохранённым фильтром"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_toggle_degrades_without_htmx"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_delete_degrades_without_htmx"
        status: pass
    human_judgment: false
  - id: D6
    description: "Размер страницы объявлен ОДИН раз и доезжает до разметки параметром из контекста маршрута (WR-05)"
    verification:
      - kind: other
        ref: "grep -c 'limit=30' app/templates/account_groups/includes/sentinel.html → 0"
        status: pass
    human_judgment: false
  - id: D7
    description: "Шапка шаблона ответа удаления держит число своих внеполосных узлов правилом, а не читателем (IN-01)"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_the_delete_response_header_counts_its_own_nodes"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_control_negative_a_header_that_miscounts_its_nodes_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D8
    description: "Правило включаемых данных не стало вакуумным при обнулившемся предмете: обе половины замены на месте"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_control_negative_an_include_declaration_without_a_target_reddens_the_gate"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_no_declared_include_selector_names_an_id_the_document_lacks"
        status: pass
    human_judgment: false
  - id: D9
    description: "Гейты Фазы 8 не ослаблены и не сужены; ветвь, которая красила бы зелёный гейт, отвергнута"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_pages/test_money_perimeter_gate.py → 15 passed, git diff --stat пуст"
        status: pass
    human_judgment: false
  - id: D10
    description: "Добавка `scroll-lock`: список за открытой панелью подтверждения перестаёт прокручиваться"
    verification: []
    human_judgment: true
    rationale: "Блокировка прокрутки тела наблюдаема только в живом браузере: правило CSS и признак Alpine проверяются по исходнику, но ОЩУЩЕНИЕ «список за окном стоит» тестом не снимается. Обход обязан открыть панель на списке длиннее экрана и попробовать прокрутить."

duration: 1h 50m
completed: 2026-08-31
status: complete
---

# Phase 09 Plan 13: Форма контракта курсора прокрутки Summary

**Курсор бесконечной прокрутки экрана групп переведён со свободно плавающего абсолютного смещения на КЛЮЧ последней отрисованной строки (`after_id`), чем класс отказа CR-01 сделан невыразимым: четвёртый внеполосный узел починки, скрытое поле `rendered_rows` и объявление включаемых данных панели ушли из дерева целиком.**

## Performance

- **Duration:** 1h 50m
- **Started:** 2026-08-31T12:18:00Z
- **Completed:** 2026-08-31T14:08:52Z
- **Tasks:** 4
- **Files modified:** 14

## Accomplishments

- **Чередование стало ИСПОЛНЯЕМЫМ, и закрытие доказано ПЕРЕХОДОМ ЦВЕТА.** `test_an_interleaved_portion_and_delete_never_double_a_row` краснел на коммите `5de9c56` и зеленеет на `0326694`. Тест между этими коммитами не тронут ни на символ — доказательством служит смена цвета, а не смена утверждения. RED называл виновника поимённо: строки 31–60 приезжали вторично, курсор уезжал с `offset=60` на `offset=29`.
- **Порядок, в котором отказ НЕ живёт, исполняется отдельно.** `test_control_positive_the_reverse_order_keeps_the_document_whole` зелен и ДО правки, и ПОСЛЕ: «ловит нарушение» и «ловит ТОЛЬКО нарушение» — разные высказывания, и второе теперь тоже проверено.
- **Форма контракта выбрана владельцем, а не исполнителем.** Останов задачи 2 вернул `keyset` + `scroll-lock` добавкой; ответ записан в план дословно вместе с прочтением гейта Фазы 8, сделанным ДО выбора.
- **Класс отказа закрыт невыразимостью.** Величины, которую можно снять в один момент и применить в другой, в контракте не осталось: `rendered_rows`, `repaired_offset`, `rows_this_response_takes_off_screen`, четвёртый внеполосный узел и `hx_include` панели сняты вместе с задачей, которую решали.
- **Попутно закрыты WR-05 и IN-01.** Размер страницы доезжает параметром из контекста маршрута (литерала в разметке не осталось); шапка ответа удаления перестала недосчитывать собственные узлы и держит это число ПРАВИЛОМ с отрицательным контролем.
- **Правило включаемых данных не стало вакуумным.** Ветвь обнулила его предмет (`INCLUDE_DECLARATIONS_MEASURED` 30 → 0), и обе половины замены заведены: антивакуум переехал на подставленное дерево, у правила появились зубы.

## Task Commits

1. **Задача 1: чередование становится исполняемым (RED)** — `5de9c56` (test)
2. **Задача 2: решение владельца о форме контракта** — `e884e7c` (docs)
3. **Задача 3: названная ветвь применена (GREEN)** — `0326694` (feat)
4. **Задача 4: инвентарь и шапка ответа** — `8692d79` (test)

_Переход цвета RED → GREEN разнесён по коммитам 1 и 3, как того требует план._

## Files Created/Modified

- `app/pages/account_groups.py` — маршрут порции читает `after_id` вместо `offset`; обработчик удаления не принимает числа от клиента и курсора не чинит
- `app/templates/account_groups/includes/sentinel.html` — сигнатура `sentinel(account_id, after_id, filter_params, page_size)`; скрытое поле и внеполосная ветка сняты
- `app/templates/account_groups/partials/delete_response.html` — три внеполосных узла вместо четырёх, шапка себе не противоречит
- `app/templates/account_groups/includes/group_row.html` — `has_sentinel` и `hx_include` сняты, летопись дописана
- `app/templates/account_groups/list.html`, `partial_cards.html` — вызовы приведены к новой сигнатуре
- `app/templates/components/modal.html` — признак открытой панели поднимает существующий Alpine; СИГНАТУРА МАКРОСА НЕ ТРОНУТА
- `app/static/css/app.css` — правило `.is-modal-open` запрещает прокрутку тела
- `tests/test_pages/test_account_groups.py` — два новых правила, летопись контролей, обе половины антивакуумной замены
- `tests/test_templates/test_htmx_markup_gates.py` — правило IN-01, его контроль, `OOB_BLOCKS` 10 → 9
- `tests/test_templates/test_htmx_inventory.py` — три числа `revealed`/`hx-get` сдвинуты летописью
- `tests/test_pages/test_htmx_preserved.py` — цепочка прокрутки перестала знать форму курсора за раздел
- `tests/test_pages/test_history_retry.py` — окно панели вырезается по корню следующей панели

## Decisions Made

**Ответ владельца (задача 2), процитированный, а не выведенный:** основная ветвь `keyset`, добавкой `scroll-lock`. `declared-cursor` и `serialize` не выбраны.

**Прочтение гейта Фазы 8 ПО ИСХОДНИКУ, сделанное и записанное ДО выбора:**
- `test_no_perimeter_route_carries_a_queued_request_sync` (`test_money_perimeter_gate.py:745`) — **неприменимо**: правило ограничено маршрутами периметра, и его докстринг говорит прямо, что вне периметра очередь законна. Маршрутов тумблера и удаления в периметре нет.
- `test_no_opaque_address_declares_a_request_queue` (`:768`) — **применимо именно оно**: запрещает очередь на адресе, собранном целиком из переменных, и само называет форму `action="{{ action }}"` общего макроса окна. Перемерено чтением `components/modal.html`: `action` на `:202`, `hx-post` на `:204`, оба печатают одно выражение.
- **Следствие:** `serialize` выразима только очередью и потому красит зелёный гейт. Отвергнута прочтением исходника, а не предположением.

**Пересмотр отказа от `always-present-cursor` (09-11)** признан сознательным. Изменившееся обстоятельство названо: арифметика, ради сохранения которой ветвь была отклонена, ИСПОЛНЕНИЕМ доказана источником зеркального отказа (задача 1). «Не трогать её» перестало быть безрисковым выбором.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Модель документа дочитывает список ДО КОНЦА, а не одним запросом**

- **Found during:** Задача 1
- **Issue:** План предписывал одно дочитывание (`GET document_read_on_url → read_on`). При посеве `PAGE_SIZE * 2 + 5` одного запроса хватает несущему тесту, но НЕ положительному контролю: в обратном порядке документ показывает 29 строк и дочитывает 30, то есть до конца списка не доходит — и требование плана «контроль обязан быть ЗЕЛЁНЫМ уже сейчас» становилось неисполнимым.
- **Fix:** заведён помощник `_read_to_the_end`, идущий по цепочке адресов до ответа без сентинела. Утверждение «объединение равно оставшемуся списку» стало исполнимым в обоих порядках; помощник снабжён пределом шагов и защитой от зацикливания.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Verification:** несущий тест краснеет на живом дереве, контроль зелен до правки
- **Committed in:** `5de9c56`

**2. [Rule 1 - Bug] Внеполосная ветка макроса сентинела осталась без вызывающего**

- **Found during:** Задача 4
- **Issue:** после снятия четвёртого узла ветку `oob=true` не звал никто, но она продолжала давать обходу внеполосный блок и место `revealed`. Инвентарные числа при этом НЕ ДВИНУЛИСЬ — то есть считали разметку вместо поведения, а план прямо ожидал их движения.
- **Fix:** ветка снята вместе с параметром `oob`; `OOB_BLOCKS` 10 → 9, `REVEALED_PLACES` 12 → 11, `REVEALED_LITERAL_OCCURRENCES` 12 → 11, `HX_GET_PLACES` 22 → 21 — каждое перемерено прогоном.
- **Files modified:** `app/templates/account_groups/includes/sentinel.html`, оба файла инвентаря
- **Verification:** 92 passed в обоих гейтовых файлах
- **Committed in:** `8692d79`

**3. [Rule 1 - Bug] Цепочка прокрутки знала форму курсора за раздел**

- **Found during:** Задача 4, прогон полной суиты
- **Issue:** `test_infinite_scroll_chain[account_groups]` собирал адрес второй страницы сам (`?offset=30`). Для экрана групп это стало НЕИЗВЕСТНЫМ параметром: маршрут молча возвращал первую страницу, и тест сообщал «в URL сентинела нет смещения» — обвинял форму вместо разорванной цепочки.
- **Fix:** тест идёт по адресу, который дала первая страница, и утверждает общее обеим формам: следующий курсор строго больше нынешнего, и форма его по дороге не меняется.
- **Files modified:** `tests/test_pages/test_htmx_preserved.py`
- **Verification:** 25 passed
- **Committed in:** `8692d79`

**4. [Rule 1 - Bug] Окно панели повтора вырезалось на фиксированную длину**

- **Found during:** Задача 4, прогон полной суиты
- **Issue:** `test_retry_confirmation_panel_carries_a_real_form` резал `html[start : start + 2000]`. Добавка `scroll-lock` удлинила выражение Alpine примерно на сотню символов, и кнопка отправки уехала за окно — тест краснел на разметке, которая исправна.
- **Fix:** окно вырезается до КОРНЯ следующей панели (`id="history-retry-\d+"`, а не по префиксу — заголовок той же панели несёт тот же префикс и обрезал бы окно на себе).
- **Files modified:** `tests/test_pages/test_history_retry.py`
- **Verification:** 61 passed
- **Committed in:** `8692d79`

### Отступления от буквы критериев приёмки, названные прямо

**5. Критерий задачи 3 «`git diff --stat app/templates/components/modal.html` показывает изменения ТОЛЬКО в строках шапки-комментария» НЕ ВЫПОЛНЕН БУКВАЛЬНО, и вот почему.** Критерий писался под ЧИСТУЮ ветвь `keyset`. Владелец принял `scroll-lock` добавкой, а сам план предписывает её механизм: «признак открытой панели поднимается на элемент документа… механизм поднятия — существующий Alpine панели (`components/modal.html`)». То есть буква критерия и текст задачи требуют несовместимого, как только добавка выбрана. СУЩЕСТВО критерия — «рычаг Фазы 10 не тронут» — проверено и выполнено: сигнатура макроса не изменена (`grep -c "hx_include=None"` → `1`), шестнадцать мест подтверждения получают ту же разметку с точностью до выражения Alpine, ни один вызов не правился.

**6. Критерий задачи 3 «полный прогон файла экрана → `0 failed`» на коммите задачи 3 НЕ ВЫПОЛНЯЛСЯ: два правила включаемых данных краснели ЗАВЕДОМО.** Ветвь `keyset` обнуляет их предмет, а замену план поручает ЗАДАЧЕ 4 («`INCLUDE_DECLARATIONS_MEASURED` перемеряются», обе половины). Закрыть их внутри задачи 3 значило бы перенести работу задачи 4 и разъехаться с летописью её чисел. Краснота названа в коммите задачи 3 прямым текстом и закрыта задачей 4; итоговый прогон зелен целиком.

---

**Total deviations:** 4 auto-fixed (1 blocking, 3 bugs) + 2 названных отступления от буквы критериев.
**Impact on plan:** ни одно отступление не ослабляет ни одного правила. Три из четырёх автоправок — починка тестов, краснеющих на ИСПРАВНОЙ разметке; четвёртая сняла фантомную разметку, из-за которой инвентарь молчал бы о движении.

## Issues Encountered

- **Ожидание числа объявлений на подставленном дереве оказалось неверным, и это поймало измерение.** Ожидалось `30` (по числу строк страницы), прогон вернул `60`: подстановка идёт на каждое место, отправляющее POST, а таких у строки ДВА — форма тумблера и форма панели подтверждения. Ровно та причина, по которой числа в этом дереве ставятся прогоном, а не арифметикой. Записано в комментарии константы.
- Прочих проблем нет.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Форма контракта опубликована и наследуема.** Фазы 10-11 получают образец: курсор — ключ, а не порядковый номер; величина, снимаемая с живого документа и применяемая к узлу другого момента, признана формой отказа.
- **Готово к плану 09-14.** Летопись контролей `tests/test_pages/test_account_groups.py` заведена и стоит на `2`; план 09-14 двигает её на `3` своим `test_control_negative_a_claim_site_without_the_runtime_event_reddens_the_gate`.
- **Фазе 15 передан ЗАКРЫТЫЙ, а не отложенный долг.** Запись `INCLUDE_TARGET_EXCEPTIONS['group-list-sentinel']` закрыта; правило стоит заряженным — вернувшееся объявление немедленно поднимет число, и решение придётся принять, а не обнаружить.
- **Остаётся на обход:** добавка `scroll-lock` (D10) — единственное непокрытое тестом утверждение плана; проверяется открытием панели на списке длиннее экрана.

---
*Phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy*
*Completed: 2026-08-31*
