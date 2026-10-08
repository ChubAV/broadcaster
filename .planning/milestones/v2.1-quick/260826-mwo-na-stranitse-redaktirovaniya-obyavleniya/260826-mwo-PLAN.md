---
phase: quick-260826-mwo-sched-toggle-collapses-card
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/form.html
  - app/pages/schedules.py
  - tests/test_pages/test_editor_schedules.py
autonomous: true
requirements:
  - QUICK-MWO-SCHED-TOGGLE-KEEPS-EXPANSION
estimate:
  tokens: 48000
  raw_tokens: 48000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "Нажатие тумблера на СВЁРНУТОЙ карточке расписания в редакторе объявления (`/ads/{id}/edit`) оставляет её СВЁРНУТОЙ: адрес ответа-редиректа не несёт `sched=` этой карточки, и после перехода по нему формы `\/schedules/{id}/edit` этой карточки в разметке нет."
    - "Нажатие тумблера на РАЗВЁРНУТОЙ карточке оставляет её РАЗВЁРНУТОЙ: адрес ответа несёт `sched=` именно её идентификатора."
    - "Карточка, развёрнутая ДО нажатия, остаётся развёрнутой после нажатия тумблера на ЛЮБОЙ ДРУГОЙ карточке. Это ВТОРАЯ половина дефекта, и она закрывается вместе с первой: сегодня карточка-сосед теряет `sched=` и схлопывается — ровно то «сворачивает», о котором говорит сообщивший."
    - "Тумблер продолжает делать своё дело: `Schedule.is_active` инвертируется, `next_run_at` пересчитывается при включении и обнуляется при выключении — ни одна ветка `schedules_toggle` (app/pages/schedules.py:699-742) кроме ПОСЛЕДНЕГО оператора возврата не тронута."
    - "Отказ D-08 сохранён: неполное расписание POST-ом на маршрут переключения не включается, `resume_blocked` остаётся точкой принуждения, и разметка тумблера неполного расписания остаётся недоступной."
    - "Пути СОХРАНЕНИЯ (`/schedules/{id}/edit`) и СОЗДАНИЯ расписания продолжают возвращать пользователя с `sched=` правленого расписания — их поведение верное и НЕ меняется: правку ведут в развёрнутой карточке, и она обязана остаться развёрнутой. Регрессии `test_update_from_editor_returns_to_the_editor` (строка 220) и проверка адреса на строке 193 остаются зелёными без правки."
    - "Сводный список расписаний (`/schedules`) не задет: там форма тумблера признака `return_to` не несёт, и редирект остаётся `\/schedules`. `schedules/includes/schedule_row.html` не изменён ни байтом."
    - "Прогрессивное улучшение сохранено (объявлено в докстринге `sched_card.html:20-25`): новое состояние едет СКРЫТЫМ ПОЛЕМ формы, а не JavaScript-ом; при выключенном Alpine форма уходит обычным POST-ом и возвращает ту же страницу с тем же разворотом."
    - "Значение скрытого поля приводится к целому на входе обработчика; непреобразуемое — отбрасывается, и POST с мусором в этом поле отвечает редиректом, а не 500. Это единственная величина, приходящая ИЗ ФОРМЫ в строку адреса, и целочисленность — то, что делает её структурно неспособной адрес изменить; принадлежность идентификатора этому объявлению перепроверяет сам редактор (app/pages/ads.py:361-363)."
    - "Докстринг `_editor_redirect` (app/pages/schedules.py:189-201) приведён в соответствие с кодом: устаревшее утверждение о том, что значение поля в адрес не попадает никогда, снято, а на его месте названо то, что держится СЕГОДНЯ — адрес по-прежнему строится из `ad_id` подтверждённой владением записи, а из формы приходит только целое. Ссылка на T-02-23 не удалена: сказано, ЧТО от неё осталось."
    - "Макрос `sched_card` не получает ДВУХ параметров об одном и том же: признак «эта карточка развёрнута» ВЫВОДИТСЯ из идентификатора развёрнутой карточки внутри макроса, а не приходит вторым параметром рядом с ним. Два параметра, способных разойтись, — тот самый класс дефекта, о котором предупреждает докстринг макроса (sched_card.html:1-7)."
    - "`uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedules_list.py tests/test_pages/test_ads_status.py -q` — зелёный."
    - "`graphify update .` прогнан после правок (правило CLAUDE.md)."
  artifacts:
    - "app/templates/ads/includes/sched_card.html — параметр `expanded_id` в сигнатуре макроса вместо `expanded`, вывод локального `expanded` из него, и скрытое поле `keep_sched` внутри формы тумблера (сегодня строки 62, 114-121)"
    - "app/templates/ads/form.html — вызов макроса на строке 202-204 передаёт `expanded_id=editor.expanded_schedule_id`"
    - "app/pages/schedules.py — функция `_expanded_from_form(form_data) -> int | None` по образцу `_clean_ints` (строка 167), её вызов в операторе возврата `schedules_toggle` (строка 740-742), правленый докстринг `_editor_redirect`"
    - "tests/test_pages/test_editor_schedules.py — четыре именованные регрессии в окрестности `test_toggle_from_editor_returns_to_the_editor` (строка 250) и `test_selected_schedule_is_the_expanded_one` (строка 800)"
  key_links:
    - "`schedules_toggle` → `_editor_redirect(form_data, ad_id, schedule_id)` (app/pages/schedules.py:740-742) → `url += f\"?sched={schedule_id}#sched-{schedule_id}\"` (строка 200) → `app/pages/ads.py:361` `expanded_id = selected_schedule_id` → `ads/form.html:203` `expanded=(s.id == editor.expanded_schedule_id)`. ЭТО И ЕСТЬ ДЕФЕКТ ЦЕЛИКОМ: разворот — не JavaScript и не CSS, а СЕРВЕРНОЕ состояние, определяемое единственным параметром `?sched=`, и обработчик тумблера ПЕРЕЗАПИСЫВАЕТ его идентификатором нажатой карточки. Гипотеза о всплытии события и о перекрывающем `label for=` — ЛОЖНАЯ: разворот сделан ССЫЛКОЙ `<a class=\"sched-card__expand\">` (sched_card.html:124-126), обработчика клика на шапке нет вовсе, а `x-on:change` на форме тумблера только отправляет её."
    - "Отсутствие `?sched=` означает «развёрнутых карточек НЕТ» (app/pages/ads.py:361-363 — умолчание `selected_schedule_id` есть `None`). Поэтому «не передавать ничего» — НЕ решение: оно чинит нажатую карточку и схлопывает соседнюю. Сохранить состояние можно только пронеся через POST идентификатор той карточки, что была развёрнута, — и он известен разметке (`editor.expanded_schedule_id`), которая эту форму и рисует."
    - "Форма тумблера (sched_card.html:114-121) уже несёт скрытое поле `return_to` — ПРЕЦЕДЕНТ проноса состояния через POST существует в этой же форме, и новое поле встаёт рядом с ним, а не заводит второй механизм."
    - "Имя `keep_sched` в `app/` и `tests/` сегодня не встречается ни разу (проверено), поэтому столкновения с существующим полем формы (`return_to`, `is_active`, `ad_id`, `group_ids`, `days_of_week`, `times_of_day`) не будет."
    - "Jinja НЕ принимает неизвестный именованный аргумент макроса: пропущенный при переименовании вызов упадёт TypeError-ом при рендере, а не отрисует пустую карточку. Это и есть причина ЗАМЕНЫ параметра `expanded` на `expanded_id` вместо добавления второго — отказ становится громким. Вызов у макроса ровно один (app/templates/ads/form.html:202), проверено по всему дереву `app/`."
    - "`test_toggle_from_editor_returns_to_the_editor` (строка 250) утверждает про адрес только `startswith(f\"/ads/{ad.id}/edit\")` и `sched=` НЕ требует — правка её не краснит. А вот `test_update_from_editor_returns_to_the_editor` (строка 220) `sched=` требует, и это ровно тот путь, который трогать нельзя."
---

<objective>
Нажатие тумблера включения/выключения расписания в редакторе объявления перестаёт менять разворот карточек: тумблер меняет `is_active` и возвращает пользователя ровно к тому разворороту, что был перед нажатием.

Purpose: сегодня обработчик переключения возвращает адрес `/ads/{ad}/edit?sched={нажатая карточка}` всегда — и свёрнутая карточка от нажатия тумблера РАЗВОРАЧИВАЕТСЯ, а развёрнутая соседка СВОРАЧИВАЕТСЯ. Пользователь читает это как «тумблер нажал кнопку СВЕРНУТЬ/РАЗВЕРНУТЬ».
Output: скрытое поле формы с идентификатором развёрнутой карточки, целочисленное чтение его на сервере, правленый докстринг и четыре именованные регрессии.
</objective>

<execution_context>
@/source/broadcaster/.claude/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@app/templates/ads/includes/sched_card.html
@app/pages/schedules.py
@app/pages/ads.py
@tests/test_pages/test_editor_schedules.py
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Task 1: пронести разворот через POST тумблера — сквозной путь разметка → форма → обработчик → редирект → рендер</name>
  <files>app/templates/ads/includes/sched_card.html, app/templates/ads/form.html, app/pages/schedules.py, tests/test_pages/test_editor_schedules.py</files>
  <read_first>
    - app/templates/ads/includes/sched_card.html строки 1-30 (докстринг: формы, прогрессивное улучшение, разворот ссылкой) и 62, 105-127 (сигнатура макроса, шапка, форма тумблера, ссылка разворота)
    - app/templates/ads/form.html строки 194-206 (единственный вызов макроса)
    - app/pages/schedules.py строки 33 (`RETURN_TO_EDITOR`), 167-185 (`_clean_ints` — образец отбрасывающей коэрции), 189-203 (`_editor_redirect`), 699-742 (`schedules_toggle`)
    - app/pages/ads.py строки 356-380 (`expanded_id` и ключ контекста `expanded_schedule_id`)
    - tests/test_pages/test_editor_schedules.py строки 40-80 (`_seed_ad`, `_seed_account`), 244-272 (`_form`, `FORM_HEADERS`, существующая регрессия тумблера), 799-825 (`test_selected_schedule_is_the_expanded_one` — образец утверждений о развороте)
  </read_first>
  <behavior>
    Красный тест пишется ПЕРВЫМ и падает до правки. Он сквозной: он не проверяет «поле есть в разметке» и не проверяет «редирект такой-то» по отдельности, он проходит путь пользователя целиком.

    - `test_the_toggle_does_not_fold_or_unfold_the_schedule_card` — объявление, аккаунт, группа, ДВА расписания. GET `/ads/{ad}/edit?sched={second.id}`; из полученной разметки берётся форма тумблера ПЕРВОГО (свёрнутого) расписания; её скрытые поля отправляются POST-ом на `/schedules/{first.id}/toggle` без `follow_redirects`; адрес редиректа запрашивается GET-ом. Утверждается ТРИ вещи: (1) `first` остался свёрнутым — `action="/schedules/{first.id}/edit"` в ответе отсутствует; (2) `second` остался развёрнутым — `action="/schedules/{second.id}/edit"` присутствует; (3) `is_active` первого расписания ИНВЕРТИРОВАЛСЯ — иначе тест зелен и при тумблере, который перестал работать вовсе.
    - Утверждение (2) — та половина дефекта, которую пользователь называет словом «сворачивает». Без неё правка прошла бы «не разворачивая нажатую» и продолжала бы схлопывать соседнюю.
    - Скрытые поля берутся ИЗ ОТРЕНДЕРЕННОЙ разметки, а не собираются в тесте вручную: собранные вручную поля прошли бы и при разметке, которая их не рисует, и связка «шаблон ↔ обработчик» осталась бы непроверенной.
  </behavior>
  <action>
    Провести идентификатор развёрнутой карточки через POST тумблера — от разметки до редиректа.

    Разметка. В `sched_card.html` заменить булев параметр разворота в сигнатуре макроса (строка 62, шестой по счёту, с умолчанием `false`) на `expanded_id` с умолчанием `none` и сразу за строкой-сеттером `account` вывести локальное значение: `expanded` истинно, когда `expanded_id` не `none` и равен `s.id`. Второго параметра об одном факте не заводить — тело макроса продолжает читать локальное `expanded` без единой правки. В форме тумблера (строки 114-121), СРАЗУ ЗА существующим скрытым полем `return_to`, добавить скрытое поле `keep_sched` со значением `expanded_id`, отрисовываемое только когда `expanded_id` не `none`. Рядом поставить русский комментарий Jinja, называющий ПРИЧИНУ: разворот — серверное состояние, определяемое единственным параметром адреса `sched`, и без проноса его через POST обработчик переключения перезаписал бы разворот идентификатором нажатой карточки. В `ads/form.html` (строка 202-204) снять из вызова макроса булев именованный аргумент разворота, сравнивающий `s.id` с `editor.expanded_schedule_id`, и передать вместо него `expanded_id=editor.expanded_schedule_id`. Прежнее имя аргумента не оставлять в вызове ни в каком виде — ни живым, ни закомментированным. Докстринг макроса (строки 1-35) дополнить одной фразой о том, что форма тумблера несёт разворот, — перечень форм там уже есть.

    Обработчик. В `app/pages/schedules.py` рядом с `_clean_ints` завести `_expanded_from_form(form_data) -> int | None`: читает поле `keep_sched`, приводит `int()`, на `(TypeError, ValueError)` возвращает `None`. Отбрасывание, а не отказ, — по той же причине, что названа в докстринге `_clean_ints`. В докстринге новой функции назвать, ЗАЧЕМ здесь коэрция: это единственная величина, приходящая из формы в строку адреса, и целочисленность делает её структурно неспособной адрес изменить; принадлежность идентификатора этому объявлению перепроверяет редактор (`app/pages/ads.py:361-363`), поэтому чужой или несуществующий номер даёт страницу без развёрнутых карточек, а не доступ к чужой записи. В `schedules_toggle` заменить в операторе возврата (строки 740-742) третий аргумент `schedule_id` на `_expanded_from_form(form_data)`. Больше в `schedules_toggle` не менять НИЧЕГО: ветка `resume_blocked`, инверсия `is_active` и пересчёт `next_run_at` остаются как есть. Ни `_editor_redirect`, ни обработчики сохранения, создания и удаления расписания в этой задаче не трогать — их возврат с `sched=` правленого расписания верен.
  </action>
  <verify>
    <automated>uv run pytest tests/test_pages/test_editor_schedules.py -q</automated>
    <automated>grep -c "keep_sched" app/templates/ads/includes/sched_card.html</automated>
    <automated>grep -v '^\s*#' app/pages/schedules.py | grep -c "keep_sched"</automated>
    <automated>grep -c "expanded=" app/templates/ads/form.html || true</automated>
  </verify>
  <done>
    `test_the_toggle_does_not_fold_or_unfold_the_schedule_card` падал до правки и зелен после. `grep -c "keep_sched"` по `sched_card.html` не меньше 1; тот же счёт по `app/pages/schedules.py` с отфильтрованными строками комментариев не меньше 1 — имя живёт в КОДЕ, а не только в пояснении. `grep -c "expanded=" app/templates/ads/form.html` печатает 0: старый именованный аргумент из вызова ушёл. Вся сюита `tests/test_pages/test_editor_schedules.py` зелёная, включая `test_update_from_editor_returns_to_the_editor` и `test_incomplete_schedule_cannot_be_switched_on`.
  </done>
  <reversibility rating="reversible">Скрытое поле формы и один аргумент вызова — снимаются обратной правкой тех же четырёх строк, состояния в БД не заводят.</reversibility>
</task>

<task type="auto" tdd="true">
  <name>Task 2: закрепить границы значения и привести докстринг `_editor_redirect` в соответствие с кодом</name>
  <files>app/pages/schedules.py, tests/test_pages/test_editor_schedules.py</files>
  <read_first>
    - app/pages/schedules.py строки 189-203 (докстринг `_editor_redirect` целиком) и новая `_expanded_from_form` из задачи 1
    - tests/test_pages/test_editor_schedules.py строки 244-272 (образец POST-а формой) и 530-548 (`test_incomplete_schedule_cannot_be_switched_on` — образец прямого POST-а мимо браузера)
  </read_first>
  <behavior>
    - `test_a_toggle_without_the_expansion_field_leaves_every_card_collapsed` — POST на маршрут переключения с одним лишь `return_to=editor` (форма браузера в этом состоянии именно такова: развёрнутых карточек нет, поле не отрисовано). Адрес редиректа обязан быть РОВНО `/ads/{ad.id}/edit` — без `sched=` и без якоря. Это регрессия на первую половину дефекта в чистом виде.
    - `test_a_malformed_expansion_field_is_dropped_instead_of_crashing` — POST мимо браузера с `keep_sched` = строка, не являющаяся числом. Ответ — 302 (не 500), адрес — `/ads/{ad.id}/edit` без параметра, `is_active` инвертирован. Разметка — не точка принуждения, ровно как сказано в комментарии обработчика на строках 718-720.
    - `test_the_collapsed_cards_toggle_carries_the_expanded_card_id` — GET `/ads/{ad}/edit?sched={second.id}` при двух расписаниях; в куске разметки, начинающемся с `action="/schedules/{first.id}/toggle"`, обязано присутствовать скрытое поле `keep_sched` со значением `second.id` — то есть свёрнутая карточка несёт чужой, а не свой идентификатор. Это утверждение о СВЯЗКЕ: без него обработчик и шаблон могли бы пройти проверки по отдельности при неработающей странице.
  </behavior>
  <action>
    Дописать три названные регрессии в `tests/test_pages/test_editor_schedules.py`, поставив первые две в окрестности `test_toggle_from_editor_returns_to_the_editor` (строка 250), а третью — рядом с `test_selected_schedule_is_the_expanded_one` (строка 800), переиспользуя `_seed_ad`, `_seed_account`, `_seed_group`, `_seed_schedule`, `_reload`, `_form` и `FORM_HEADERS`. Каждой регрессии дать русский докстринг, называющий ЗАЩИЩАЕМОЕ ПОВЕДЕНИЕ, а не механику.

    Привести докстринг `_editor_redirect` (app/pages/schedules.py:189-201) в соответствие с тем, что код теперь делает. Утверждение третьего абзаца о том, что значение поля не попадает в адрес никогда, стало неверным — снять его и назвать на его месте то, что держится сегодня: адрес по-прежнему строится ЗДЕСЬ и `ad_id` берётся из записи, владение которой подтверждено запросом, а из формы приходит ровно одна величина — целое, полученное `_expanded_from_form` у вызывающего, и никакая строка формы в адрес не подставляется. Ссылку на T-02-23 сохранить, назвав, что именно от неё осталось в силе. Сигнатуру `_editor_redirect` не менять: обработчики сохранения, создания и удаления продолжают передавать идентификатор из пути.

    После правок прогнать `graphify update .` — правило CLAUDE.md.
  </action>
  <verify>
    <automated>uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedules_list.py tests/test_pages/test_ads_status.py -q</automated>
    <automated>sed -n '/^def _editor_redirect/,/^def _apply_named_actions/p' app/pages/schedules.py | grep -c "ни при каких условиях" || true</automated>
    <automated>sed -n '/^def _editor_redirect/,/^def _apply_named_actions/p' app/pages/schedules.py | grep -c "T-02-23"</automated>
  </verify>
  <done>
    Три регрессии зелёные, вся перечисленная сюита зелёная. Область докстринга `_editor_redirect`, вырезанная `sed`-ом от его `def` до `def _apply_named_actions`, печатает 0 для устаревшего утверждения и не меньше 1 для `T-02-23`: неверная фраза снята, а прослеживаемость к решению не потеряна. `graphify update .` завершился успешно.
  </done>
  <reversibility rating="reversible">Тексты тестов и докстринга.</reversibility>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| браузер → `POST /schedules/{id}/toggle` | недоверенное поле формы `keep_sched` впервые становится источником величины, попадающей в строку заголовка `Location` |
| `Location` → `GET /ads/{id}/edit?sched=` | значение проходит через параметр запроса обратно на сервер и решает, какая карточка развёрнута |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-mwo-01 | Tampering | `_expanded_from_form` → `_editor_redirect` (app/pages/schedules.py) | medium | mitigate | Приведение к `int()` с отбрасыванием непреобразуемого: строка с `&`, `#`, CRLF или абсолютным адресом до конкатенации не доходит. Закреплено `test_a_malformed_expansion_field_is_dropped_instead_of_crashing`. |
| T-mwo-02 | Information Disclosure | `app/pages/ads.py:361-363` | low | accept | Подделанный номер чужого расписания в `keep_sched` даёт лишь параметр адреса: редактор отбрасывает идентификатор, отсутствующий среди расписаний ЭТОГО объявления, и страница рисуется без развёрнутых карточек. Собственный подставленный номер к раскрытию чужих данных не ведёт. |
| T-mwo-03 | Elevation of Privilege | `schedules_toggle` (app/pages/schedules.py:699-742) | high | mitigate | Правка не касается ни выборки с `join(Ad, Ad.user_id == user.id)`, ни ветки `resume_blocked`: владение и отказ D-08 решаются до и независимо от нового поля. Закреплено сохранностью `test_incomplete_schedule_cannot_be_switched_on` и утверждением об инверсии `is_active` в сквозной регрессии. |
| T-mwo-04 | Denial of Service | `_expanded_from_form` | low | mitigate | `int()` на произвольной строке ограничен по длине самим лимитом тела формы; исключения перехвачены, 500 на пути тумблера не возникает. |
</threat_model>

<verification>
1. `uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_ads_editor.py tests/test_pages/test_responsive_markup.py tests/test_pages/test_schedules_list.py tests/test_pages/test_ads_status.py -q` — зелёный.
2. Сквозная регрессия `test_the_toggle_does_not_fold_or_unfold_the_schedule_card` ПАДАЛА до правки — записать это в SUMMARY фактом прогона, а не утверждением.
3. `git diff --stat` не содержит `app/templates/schedules/includes/schedule_row.html` и `app/routes/schedules.py`: сводный список и JSON-API не задеты.
4. `graphify update .` прогнан.
</verification>

<success_criteria>
- Тумблер расписания в редакторе объявления меняет только состояние расписания; разворот карточек после нажатия — тот же, что был до него, для ВСЕХ карточек списка.
- Ни один существующий тест не покраснел; путь сохранения расписания продолжает возвращать пользователя в развёрнутую карточку.
- Докстринг `_editor_redirect` не утверждает про код неправды.
</success_criteria>

<output>
Create `.planning/quick/260826-mwo-na-stranitse-redaktirovaniya-obyavleniya/260826-mwo-SUMMARY.md` when done
</output>
