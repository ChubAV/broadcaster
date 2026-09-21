---
phase: quick-260921-qvt-tg-wizard-visual-regressions
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/templates/accounts/includes/tg_connect_step.html
  - app/static/css/app.css
  - tests/test_templates/test_tg_connect_step_layout.py
autonomous: true
requirements:
  - QUICK-13-UI-1
  - QUICK-13-UI-2
  - QUICK-13-UI-3
estimate:
  tokens: 50000
  raw_tokens: 50000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "UI-1. На шаге пароля 2FA поле «Пароль 2FA» и кнопка «Подтвердить» снова разделены промежутком 14px — тем же, что у колонки шага `.connect-step`. Так на обоих ответах: на первом показе шага и на 422 с ошибкой у поля (D-08). Поле и ряд действий лежат во внутренней колонке `div.connect-step__form` внутри формы, по образцу `max_connect_step.html:64-69`. Правило `.connect-step__form` (app.css:1934) уже объявляет `display: flex; flex-direction: column; gap: 14px`, и его величина не меняется."
    - "UI-2. На шаге «QR-код истёк» ряд «Обновить QR-код» / «Отмена» стоит по центру под центрированным текстом. Причина — правило `.connect-step--center .connect-step__actions { justify-content: center; }`, поставленное рядом с `.connect-step__actions` (app.css:1933). На остальных центрированных шагах ничего не сдвигается: у `waiting` ряд — прямой ребёнок колонки шириной по содержимому, у `connected` и у шагов WA/MAX ряда действий нет вовсе."
    - "UI-3. После нажатия «Начать подключение», «Начать заново» или «Обновить QR-код» в ряду действий, после «Отмена», появляется текст «Загрузка...». Он виден ровно столько, сколько идёт запрос, и гаснет, когда пришёл ответ либо запрос упал на сети. Ни скрипта, ни обработчика, ни атрибута `hidden` для этого не добавлено (D-11, D-12). Показ держит состояние, которое htmx ставит сам: атрибут `disabled` на кнопке отправки формы — цели блокировки макроса-обёртки по умолчанию."
    - "Селектор из ревью (`.form-wrapper.htmx-request …`) НЕ использован, и причина записана. У каждой обёрнутой формы стоит `hx-indicator=\"find .form-busy\"`. Поэтому htmx 2.0.10 вешает класс запроса на узел индикатора, а не на форму: функция `tn()` вендоренного рантайма берёт саму форму, только когда индикатора нет. Правило по классу формы не сработало бы НИКОГДА — это ловушка, записанная в app.css:2094-2099."
    - "Шаги `password`, `waiting` и `connected` подписи загрузки не несут. Опросчик шага ожидания, реестр `POLLING_CASES`, метки `STEP_MARKS` и число блоков вызова обёртки (`UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED = 19`) не сдвинуты. Новых вызовов `form_wrapper` нет, и аргументы существующих не изменены."
    - "Регрессия НЕВАКУУМНА. Каждое утверждение о правиле стилей идёт в паре с утверждением о том, что адресуемая структура действительно есть в отрисованном шаге. До правки каждая новая проверка падала на своём утверждении, и тексты падений названы в SUMMARY."
    - "Зелёные: новая регрессия, маршрутные тесты мастера, гейты разметки и индикатора (включая неподвижность индикатора панели подтверждения и порог 300 мс), инвентарь, компоненты, гейты htmx-страниц, `test_shell.py`, `tests/test_planning/`. `graphify update .` прогнан, код возврата записан в SUMMARY."
    - "Зрительный результат в живом браузере записан в `coverage` SUMMARY отдельным пунктом: `human_judgment: true`, пустой список `verification`. Машинная сверка разметки и стилей не выдаётся за приёмку вёрстки."
  artifacts:
    - path: "app/templates/accounts/includes/tg_connect_step.html"
      provides: "Внутренняя колонка `connect-step__form` на шаге пароля. Подпись `<span class=\"connect-step__busy\">Загрузка...</span>` последним ребёнком ряда действий в ветке старта/ошибки и в ветке `qr_expired`."
    - path: "app/static/css/app.css"
      provides: "Правило центрирования ряда действий центрированного шага. Базовое правило подписи загрузки (скрыта) и правило показа по отключённой кнопке отправки — с комментарием-обоснованием."
    - path: "tests/test_templates/test_tg_connect_step_layout.py"
      provides: "Регрессия UI-1…UI-3 над отрисованными ветками шага (`_tg_step_markup`) и над правилами стилей. Правила читаются разборщиком гейта `test_htmx_markup_gates.py`, второго разборщика нет."
  key_links:
    - from: "app/static/css/app.css — правило показа подписи загрузки"
      to: "components/form_wrapper.html — умолчание `disabled_elt='find button[type=submit]'`"
      via: "htmx ставит `disabled` на кнопку отправки на всё время запроса и снимает его по ответу или по сбою сети. Подпись стоит ПОСЛЕ кнопки в том же ряду, и комбинатор последующего соседа находит её от кнопки."
      pattern: "button\\[type=\"submit\"\\]\\[disabled\\] ~ \\.connect-step__busy"
    - from: "tg_connect_step.html, ветка `password`"
      to: "app/static/css/app.css:1934 `.connect-step__form`"
      via: "Промежуток колонки шага не доходит до детей формы: у тега формы макроса одно правило — `position: relative` (app.css:2207). Внутренняя колонка возвращает 14px."
      pattern: "class=\"connect-step__form\""
    - from: "tg_connect_step.html, ветка `qr_expired`"
      to: "app/static/css/app.css — `.connect-step--center .connect-step__actions`"
      via: "`.connect-step > form { align-self: stretch }` (app.css:1931) растягивает форму на всю ширину, и центрирование колонки до ряда внутри формы не доходит."
      pattern: "\\.connect-step--center \\.connect-step__actions"
---

<objective>
Убрать три визуальные регрессии мастера подключения Telegram по QR. Фаза 13
оставила их как неблокирующие замечания (`13-VERIFICATION.md`, записи
`advisory` UI-1, UI-2, UI-3). Владелец 2026-09-21 решил починить именно эти
три до отгрузки фазы 13.

Все три — следствие одного переезда: каждый шаг с действием теперь лежит внутри
`form_wrapper`. Макрос печатает `<form class="…">`, у которого одно правило —
`position: relative` (app.css:2207). Поэтому flex-выкладка колонки `.connect-step`
(промежуток 14px, центрирование) до детей формы больше не доходит.

Purpose: форма шага, где человек вводит секрет, не должна выглядеть сломанной.
Действие шага «код истёк» не должно висеть у левого края под центрированным
текстом. Нажатие, за которым следуют секунды подключения к Telegram, должно
снова давать видимый ответ «Загрузка...», как до фазы.

Output: правка шаблона шага, три правила стилей (плюс одно центрирующее) с
обоснованием и новый файл регрессии. Разметка страницы мастера
`connect_tg_user.html`, обработчики `app/pages/accounts.py`, макрос
`form_wrapper` и мастера WA/MAX не меняются.
</objective>

<design_decisions>
Решения, принятые планировщиком по праву усмотрения, которое дал владелец
(`13-CONTEXT.md` § Claude's Discretion: «куда ставится `hx-indicator`»).
Все проверены по коду, а не взяты из ревью на веру.

**DD-1. Сигнал показа подписи загрузки — атрибут `disabled` на кнопке отправки.**
Ревью предлагало `.form-wrapper.htmx-request .connect-step__busy` либо
`hx-indicator` на видимый узел. Отвергнуты оба варианта из ревью и ещё один:

- Класс запроса на форме. `form_wrapper` безусловно печатает
  `hx-indicator="find .form-busy"`. В вендоренном htmx 2.0.10 функция `tn()`
  добавляет `htmx-request` целям индикатора и берёт сам элемент, только когда
  индикатора нет. Форма класс не получает никогда. Это ловушка из app.css:2094-2099,
  и её же держит пункт 1 `test_the_indicator_class_carries_a_visibility_threshold`.
- Свой `hx-indicator` у вызывающего. Индикатор печатает сам макрос, ни один
  вызывающий селектор не передаёт (D-14 Фазы 9, FORM-09), и атрибут обязан
  остаться последним в теге (докстринг `form_wrapper.html`). К тому же `find`
  находит только первое совпадение.
- `:has(> .form-busy.htmx-request)`. `_offenders_panel_indicator_reach`
  (`test_htmx_markup_gates.py:3559-3580`) краснит любую часть селектора с
  классом индикатора вне объявленного множества. Правило охраняет решение
  владельца от 2026-09-17 (принятая высота 18 мест подтверждения, 10-UAT 3.5).
  Расширять это множество ради правила, которое индикатор даже не стилизует,
  значит ослабить гейт решения владельца.

Выбран документированный контракт `hx-disabled-elt`. Для этих двух форм цель
блокировки — умолчание макроса `find button[type=submit]`. htmx ставит `disabled`
на кнопку при выдаче запроса и снимает его по ответу, по сбою сети, по таймауту.
Вне запроса эти кнопки не отключены никогда: макрос `button` печатает `disabled`,
только если его передали, а здесь его не передают. Прецедент соседского
селектора по отключённому органу уже есть: `.toggle__input[disabled] + .toggle__track`
(app.css:815).

**DD-2. Скрытие через `display`, без порога 300 мс.** Пока запроса нет, подпись
не имеет коробки. Иначе невидимый, но занимающий место узел сдвинул бы с центра
пару кнопок на `qr_expired` (свёл бы UI-2 на нет) и на узкой ширине дал бы
пустую перенесённую строку в ряду. Следствие: порога нет, потому что `display`
не задерживается (app.css:2101-2105). Это принято сознательно. Запрос старта
и обновления длится секунды (подключение Telethon плюс выдача токена), мигания
на мгновенном ответе здесь нет. Подпись до фазы тоже появлялась сразу по
нажатию. Порог D-15 остаётся у точки `.form-busy` и не трогается.

**DD-3. Место подписи — последний ребёнок `.connect-step__actions`, после «Отмена».**
Комбинатор последующего соседа находит только более поздних соседей, поэтому
подпись обязана стоять после кнопки. После «Отмена» — чтобы в левом ряду
старта/ошибки при появлении подписи не сдвинулся ни один орган. На узкой ширине
подпись уносит на новую строку `flex-wrap: wrap`. В центрированном ряду
`qr_expired` пара на время запроса смещается на половину ширины подписи. Это
принято: кнопка в этот момент отключена, а шаг сразу заменяет ответ.

**DD-4. Текст — «Загрузка...» (три точки), а не «Получаем QR-код…».** Это
дословная подпись, которую ставил снятый скрипт (`git show
f21a6316:app/templates/accounts/connect_tg_user.html`, строка 101,
`setBtnLabel(btn, 'Загрузка...')`). Регрессия чинится возвратом прежнего, по
линии фазы «перенести, а не переизобрести» (`13-CONTEXT.md:275`). D-09
ограничивает новые тексты мастера текстами D-02, D-03 и D-04. Прежняя подпись
новым текстом не является, а новая формулировка расширила бы этот набор.
Три точки совпадают с «Ожидание сканирования...» этого же шаблона. Метки
`STEP_MARKS` (`test_tg_user_auth.py:1411-1418`) текст не задевает.

**DD-5. Регрессионный тест включён.** Все три дефекта молчаливы: страница отдаёт
200 одинаково с правкой и без неё, и ни один существующий гейт выкладку не
читает. UI-3 к тому же ровно того рода, что гейты проекта ловят машинно: правило,
которое выглядит верным и не срабатывает никогда. Форма теста — прецедент
задачи 260826-ojg: утверждение о правиле стилей в паре с утверждением о
структуре, которую оно адресует.
</design_decisions>

<execution_context>
@/source/broadcaster/.claude/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-UI-REVIEW.md
@.planning/phases/13-master-podklyucheniya-telegram-po-qr-na-fragmentah/13-CONTEXT.md
@app/templates/accounts/includes/tg_connect_step.html
@app/templates/accounts/includes/max_connect_step.html
@app/templates/components/form_wrapper.html

<interfaces>
Факты, снятые при планировании, 2026-09-21. Номера строк — на коммите ab72d228.

Шаблон `app/templates/accounts/includes/tg_connect_step.html`:
- ветка `qr_expired` — строки 68-85, ряд действий внутри формы — 80-83;
- ветка `password` — строки 87-111, вызов `form_wrapper` — 102-110: скрытое поле
  `session_id`, затем `field(...)` (104-106), затем `div.connect-step__actions`
  с `button('Подтвердить')` (107-109);
- ветка старта/ошибки (`{% else %}`) — строки 121-135, ряд действий внутри
  формы — 130-133.

Отрисованная форма старта сегодня (через `_tg_step_markup(step="start")`):
`form.form-wrapper[hx-disabled-elt="find button[type=submit]"][hx-indicator="find .form-busy"]`
→ `div.connect-step__actions` → `button.btn.btn--primary[type=submit]`,
`a.btn.btn--ghost`; затем `span.form-busy[aria-hidden=true]` — последний ребёнок
формы, его печатает макрос. У `qr_expired` и `password` форма устроена так же,
плюс `input[type=hidden][name=session_id]` первым ребёнком.

Стили `app/static/css/app.css`:
- 1928 `.connect-step { display: flex; flex-direction: column; gap: 14px; align-items: flex-start; }`
- 1930 `.connect-step--center { align-items: center; text-align: center; }`
- 1931 `.connect-step > .field, .connect-step > form { align-self: stretch; }`
- 1932 `.connect-step__text { margin: 0; font-size: var(--fs-md); color: var(--text-secondary); }`
- 1933 `.connect-step__actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }`
- 1934 `.connect-step__form { display: flex; flex-direction: column; gap: 14px; align-items: stretch; }`
- 2088-2210 — раздел «Индикатор htmx-формы» (`.form-busy`, `.form-wrapper`).

Разборщик стилей гейта (переиспользовать, а не писать второй):
`from tests.test_templates.test_htmx_markup_gates import _app_css, _css_rules, _declaration`.
`_app_css()` — файл стилей без комментариев. `_css_rules(css)` — список пар
(селектор, тело). `_declaration(body, prop)` — значение свойства или `None`.
Импорт модуля занимает около 0.3 с.

Отрисовщик шага: `from app.pages.accounts import _tg_step_markup` — принимает только
именованные `step`, `session_id`, `qr_code`, `error`, `password_error`.
Прецедент импорта — `tests/test_routes/test_tg_user_auth.py:64`.
</interfaces>
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Задача 1: регрессия UI-1 и UI-2 красной, затем внутренняя колонка шага пароля и центрирование ряда центрированного шага</name>
  <files>tests/test_templates/test_tg_connect_step_layout.py, app/templates/accounts/includes/tg_connect_step.html, app/static/css/app.css</files>
  <read_first>
    - app/templates/accounts/includes/tg_connect_step.html (целиком; ветки `password` 87-111 и `qr_expired` 68-85)
    - app/templates/accounts/includes/max_connect_step.html:39-70 (образец внутренней колонки и абзац «КОРОБКУ ВЫКЛАДКИ ДАЁТ ВНУТРЕННИЙ УЗЕЛ, А НЕ ТЕГ ФОРМЫ»)
    - app/static/css/app.css:1920-1946 (раздел шагов мастера)
    - tests/test_templates/test_htmx_markup_gates.py:3203-3302 (`_app_css`, `_css_rules`, `_declaration`)
    - tests/test_routes/test_tg_user_auth.py:60-75 и 1775-1810 (импорты и прецедент вызова `_tg_step_markup`)
  </read_first>
  <behavior>
    Новый файл `tests/test_templates/test_tg_connect_step_layout.py`. Докстринг
    модуля по-русски: регрессия UI-1…UI-3 из `13-UI-REVIEW.md`, причина всех трёх
    одна (см. `<objective>`). Разбор отрисованного шага — маленький построитель
    дерева на `html.parser.HTMLParser` стандартной библиотеки, как
    `tests/test_pages/test_confirm_delete_transport.py:241`. Узел: тег,
    атрибуты-словарь, дети, собственный текст. Пустые элементы (`input`, `img`,
    `br`, `hr`, `meta`, `link`) детей не получают. Помощник правила стилей
    возвращает тело ПОСЛЕДНЕГО правила, чей селектор после `strip()` равен
    переданному ТОЧНО; источник — `_css_rules(_app_css())`.

    - `test_the_password_step_keeps_its_field_and_button_in_one_column` (UI-1).
      Для `password_error` из `(None, "Неверный пароль 2FA.")` (первый показ и
      422 по D-08) отрисовать `step="password"`, `session_id="s"`. Найти форму с
      `action`, оканчивающимся на `/verify-2fa`. Утверждать по порядку:
      (а) у формы РОВНО ОДИН прямой ребёнок `div` с классом `connect-step__form`;
      (б) его прямые дети — `label` с классом `field`, содержащий
      `input[name=password]`, и затем `div.connect-step__actions`, содержащий
      `button[type=submit]`;
      (в) среди прямых детей формы нет ни `label.field`, ни `.connect-step__actions`;
      (г) `input[type=hidden][name=session_id]` — потомок формы, идентификатор
      уходит телом POST (D-06).
      Затем половина стилей: правило `.connect-step__form` объявляет
      `display: flex`, `flex-direction: column`, и его `gap` РАВЕН `gap`
      правила `.connect-step`. Величина взята у колонки шага, а не подобрана.
    - `test_a_centered_step_centers_the_actions_nested_in_its_form` (UI-2).
      Отрисовать `step="qr_expired"`, `session_id="s"`. Утверждать структуру,
      ради которой правило существует: у `div` шага оба класса,
      `connect-step` и `connect-step--center`; `.connect-step__actions` НЕ прямой
      ребёнок этого `div`, а потомок его формы. Затем стили: правило с селектором
      ровно `.connect-step--center .connect-step__actions` существует и объявляет
      `justify-content: center`.

    RED первым: файл пишется и запускается ДО правки шаблона и стилей.
    UI-1 обязан упасть на утверждении (а): колонки внутри формы ещё нет.
    UI-2 обязан упасть на утверждении о правиле: структурные утверждения к этому
    моменту уже зелёные, иначе краснота пришла бы не от отсутствующей правки.
    RED-прогон — с `--junit-xml` во временный файл вне репозитория: верб улики
    RED читает pytest только в этом формате. Тексты обоих упавших утверждений
    записать в SUMMARY.
  </behavior>
  <action>
    Сначала написать регрессию из `<behavior>` и получить RED ровно на названных
    утверждениях. Затем две правки, по одной на дефект.

    UI-1, шаблон, ветка `password` (строки 102-110). Внутри вызова `form_wrapper`
    скрытое поле `session_id` остаётся первым. Сразу после него — новый
    `<div class="connect-step__form">`, и в него переносятся вызов `field(...)`
    (все аргументы дословно: `id='password'`, `required=true`,
    `autocomplete='off'`, `error=password_error`) и неизменённый
    `div.connect-step__actions` с `button('Подтвердить')`. Кнопке `btn--block` не
    добавлять: ряд действий шага Telegram остаётся рядом, как до фазы. Меняется
    только коробка выкладки. В существующий комментарий `{#- … -#}` над вызовом
    (строки 92-101) дописать абзац по-русски. Он объясняет, почему нужен
    внутренний узел. Тег формы печатает макрос, у тега одно правило — контекст
    позиционирования, и промежуток колонки шага до детей формы не доходит.
    Внутренний узел — тот же приём, что у шага MAX. Класс формы макроса
    называть в комментарии словами, как это делает MAX, а не литералом.
    В разметке шаблона литерал этого класса не набирать вовсе: вне
    макроса-обёртки его ловит `_offenders_panel_indicator_reach`. Значение поля
    по-прежнему не выводить (D-08, T-06-02).

    UI-2, стили. В `app/static/css/app.css` НЕПОСРЕДСТВЕННО после правила
    `.connect-step__actions` (строка 1933) и перед `.connect-step__form`
    поставить правило `.connect-step--center .connect-step__actions` с одним
    свойством `justify-content: center`. Над ним — короткий комментарий
    по-русски. Он говорит: центрированный шаг центрирует свои flex-предметы, но
    форма шага растянута правилом `.connect-step > form` (строка 1931), поэтому
    ряд действий внутри формы начинается у левого края; правило центрирует ряд
    внутри растянутой формы и так же защищает любой будущий центрированный шаг.

    Не трогать: комментарий app.css:1925-1927 и правило `.connect-step[hidden]`
    (устаревшие, но это UI-4…UI-17 — вне объёма); ветку `waiting` и её
    форму-опросчик (D-05; реестр `POLLING_CASES`); порядок и аргументы
    вызовов `form_wrapper`; ни одного `hidden`, `<script>`, `onclick`
    (D-11, D-12).
  </action>
  <verify>
    <automated>uv run pytest tests/test_templates/test_tg_connect_step_layout.py tests/test_routes/test_tg_user_auth.py -q</automated>
  </verify>
  <done>
    Регрессия была красной до правки на названных утверждениях (тексты в
    SUMMARY) и теперь зелёная. Отрисованный шаг пароля несёт
    `form > div.connect-step__form > [label.field, div.connect-step__actions]` на
    обоих ответах. В app.css между `.connect-step__actions` и
    `.connect-step__form` стоит `.connect-step--center .connect-step__actions { justify-content: center; }`
    с комментарием. `tests/test_routes/test_tg_user_auth.py` зелёный целиком.
    Правила 1928-1934 не изменены.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Задача 2: подпись «Загрузка...» на формах старта/ошибки и обновления QR, показ по отключённой кнопке отправки, прогон гейтов и graphify</name>
  <files>tests/test_templates/test_tg_connect_step_layout.py, app/templates/accounts/includes/tg_connect_step.html, app/static/css/app.css</files>
  <read_first>
    - app/static/css/app.css:2088-2210 (раздел «Индикатор htmx-формы» — почему класс запроса не садится на форму и почему `display` не задерживается)
    - app/templates/components/form_wrapper.html (умолчание `disabled_elt` и последний атрибут `hx-indicator`)
    - tests/test_templates/test_htmx_markup_gates.py:3519-3616 (`_offenders_panel_indicator_reach`) и 6555-6592 (опоры подстановки `CSS_*`)
    - tests/test_routes/test_tg_user_auth.py:494-507 (`test_the_wizard_page_carries_no_client_script`) и 1407-1418 (`STEP_MARKS`)
  </read_first>
  <behavior>
    Дописать в тот же файл регрессии три проверки:

    - `test_start_and_refresh_show_a_busy_label_while_the_button_is_disabled`.
      Для пар `("start", None)`, `("error", "Ошибка")`, `("qr_expired", None)`
      отрисовать шаг с `session_id="s"`. У формы шага атрибут `hx-disabled-elt`
      равен `find button[type=submit]`: именно эту кнопку htmx отключает на
      время запроса. У `.connect-step__actions` внутри формы среди прямых детей
      есть `button[type=submit]` и РОВНО ОДИН `span.connect-step__busy`; текст
      span после `strip()` равен «Загрузка...». Индекс span среди детей ряда
      БОЛЬШЕ индекса кнопки: комбинатор последующего соседа находит только
      более поздних соседей. Во всей отрисовке шага подпись одна.
    - `test_no_other_step_carries_the_busy_label`. Для `step="password"`,
      `step="waiting"` (с `qr_code="data:image/png;base64,AA"`) и
      `step="connected"` в отрисовке нет класса `connect-step__busy`.
    - `test_the_busy_label_is_keyed_on_the_disabled_button_not_on_the_form`.
      Утверждения:
      (а) у правила `.connect-step__busy` `display: none`, `font-size: var(--fs-md)`,
      `color: var(--text-secondary)` — только токены раздела, новых цветов и кеглей нет;
      (б) правило с селектором ровно
      `.connect-step__actions > button[type="submit"][disabled] ~ .connect-step__busy`
      объявляет `display: inline`;
      (в) ни у одного правила, чей селектор содержит `.connect-step__busy`, в
      селекторе нет класса запроса рантайма. Стили читаются через `_app_css()`
      с вырезанными комментариями, поэтому комментарий, называющий ловушку
      словами, утверждение не опровергает.

    RED первым: до правки шаблона и стилей первая проверка обязана упасть на
    отсутствии `span.connect-step__busy`, третья — на отсутствии правила (а).
    Вторая до правки зелёная и остаётся зелёной: она охраняет объём. RED — с
    `--junit-xml`, как в задаче 1. Тексты падений записать в SUMMARY.
  </behavior>
  <action>
    Сначала дописать проверки из `<behavior>` и получить RED на названных
    утверждениях. Затем правки по DD-1…DD-4.

    Шаблон. В ветке старта/ошибки (ряд 130-133) и в ветке `qr_expired` (ряд
    80-83) последним ребёнком `div.connect-step__actions`, сразу после
    `link_button('Отмена', …)`, поставить
    `<span class="connect-step__busy">Загрузка...</span>`. Текст — литерал с тремя
    точками (DD-4, D-09). Ни `role`, ни `aria-live`, ни `aria-hidden` не ставить:
    объявление смен шага для вспомогательных технологий — отдельное
    замечание вне объёма, а видимый текст должен оставаться в дереве
    доступности. Над одним из двух рядов (у ветки старта/ошибки) — комментарий
    `{#- … -#}` по-русски с тремя фактами:
    (1) подпись показывают стили, пока htmx держит кнопку отправки отключённой, —
    это цель блокировки обёртки по умолчанию; значит, форма обязана сохранить
    умолчание `disabled_elt`, а подпись — стоять ПОСЛЕ кнопки;
    (2) скрипта нет, и он не нужен (D-11, D-12);
    (3) текст — прежняя подпись снятого скрипта, возвращённая дословно (D-09).
    Вызовы `form_wrapper` и их аргументы не менять. Литерал класса формы
    обёртки не набирать.

    Стили. В `app/static/css/app.css` сразу после правила `.connect-step__form`
    (строка 1934, после вставки задачи 1 — на строку ниже) поставить два
    правила по порядку:
    - `.connect-step__busy` с `display: none`, `font-size: var(--fs-md)`,
      `color: var(--text-secondary)`;
    - `.connect-step__actions > button[type="submit"][disabled] ~ .connect-step__busy`
      с `display: inline`.
    Над ними — комментарий по-русски. Он называет все пункты DD-1…DD-3:
    сигнал — `disabled` от цели блокировки; почему не класс запроса на форме
    (индикатор обёртки уводит его на узел точки; сослаться на раздел
    «Индикатор htmx-формы» ниже); почему не `:has()` на узле точки (гейт
    неподвижности индикатора панели, решение владельца от 2026-09-17); почему
    `display`, а не прозрачность и видимость, и почему поэтому нет порога
    300 мс; почему подпись — последующий сосед кнопки.
    ⚠️ В комментарии НЕ воспроизводить дословно ни одну опору подстановки
    `CSS_*` из `test_htmx_markup_gates.py:6561-6589` — строки открытия правил
    индикатора, их записи перехода и вывода из потока. `_css_with` требует
    ровно одного вхождения опоры в СЫРОМ файле, комментарии включительно, и
    второе вхождение покрасило бы три контроля гейтов индикатора. Правила
    индикатора называть словами и номерами строк, а не цитатой.
    Ни одна часть нового селектора не должна содержать класс индикатора
    обёртки или имя класса индикатора рантайма.

    После правок прогнать сводный набор из `<verify>`. Затем `graphify update .`
    (правило CLAUDE.md, только AST, без обращений к API) и записать код возврата
    в SUMMARY. Если какой-то гейт покраснеет, чинить причину в правке. Реестры,
    числа и множества гейтов не расширять; если починка без этого невозможна,
    остановиться и вынести вопрос владельцу.
  </action>
  <verify>
    <automated>uv run pytest tests/test_templates/test_tg_connect_step_layout.py tests/test_routes/test_tg_user_auth.py tests/test_templates/test_htmx_markup_gates.py tests/test_templates/test_htmx_inventory.py tests/test_templates/test_components.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q</automated>
    <automated>uv run pytest tests/test_pages/test_responsive_markup.py -k connect -q</automated>
    <automated>uv run pytest tests/test_pages/test_shell.py -q</automated>
    <automated>uv run pytest tests/test_planning/ -q</automated>
    <automated>graphify update .</automated>
    <human-check>
      На живом стенде открыть `/accounts/connect/tg_user`.
      (1) Нажать «Начать подключение». Пока кнопка отключена, справа от
      «Отмена» видно «Загрузка...»; с приходом QR подпись исчезает вместе со
      шагом. Для детерминированного взгляда без Telegram: в инструментах
      разработчика поставить кнопке атрибут `disabled` — подпись появляется,
      снять — исчезает.
      (2) Дождаться «QR-код истёк» (токен живёт около 30 с): пара «Обновить
      QR-код» / «Отмена» стоит по центру под текстом; при нажатии «Обновить
      QR-код» появляется «Загрузка...».
      (3) На аккаунте с 2FA: между полем «Пароль 2FA» и «Подтвердить» —
      промежуток, такой же и после неверного пароля (422).
      Отметки ставит владелец. Исполнитель записывает пункт в `coverage`
      SUMMARY с `human_judgment: true` и пустым `verification`.
    </human-check>
  </verify>
  <done>
    Регрессия была красной до правки на названных утверждениях (тексты в
    SUMMARY), теперь все пять проверок файла зелёные. Ветки старта, ошибки и
    `qr_expired` несут одну `span.connect-step__busy` «Загрузка...» последним
    ребёнком ряда действий, после кнопки отправки; остальные ветки её не несут.
    В app.css после `.connect-step__form` стоят два правила подписи с
    комментарием по DD-1…DD-3. Все команды `<automated>` зелёные, код возврата
    `graphify update .` записан. `git diff --name-only` называет ровно три
    файла из `files_modified` (плюс артефакты graphify, если граф
    версионируется); `connect_tg_user.html`, `app/pages/accounts.py`,
    `components/form_wrapper.html` и файлы `.planning/phases/13-*/` не
    изменены.
  </done>
</task>

</tasks>

<threat_model>
Уровень ASVS 1, блокирующий порог `high`. Угроз уровня `high` и выше задача не
вводит.

## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| сервер → браузер (фрагмент шага) | Новая разметка — статический литерал шаблона: ни одного значения из запроса, сессии или Telegram в неё не попадает. Автоэкранирование окружения не тронуто. Маршруты, обработчики и состав полей форм не меняются. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-QUICK-QVT-01 | Information Disclosure | Шаг `password`: перенос поля во внутреннюю колонку | low | mitigate | Поле пароля обязано остаться внутри формы и без значения на любом ответе (D-08, T-06-02), а `session_id` — скрытым полем формы (D-06). Первая проверка задачи 1 утверждает, что поле и скрытое поле — потомки формы, на обоих ответах, включая 422. `test_a_wrong_password_answers_422_at_the_field_without_echo` входит в `<verify>` обеих задач. |
| T-QUICK-QVT-02 | Denial of Service | Формы старта и обновления QR: цель блокировки | low | mitigate | Подпись держится на `disabled`, который ставит `hx-disabled-elt`. Правка не должна подталкивать к снятию цели блокировки: это вернуло бы двойное нажатие и два запроса нового токена у Telegram. Первая проверка задачи 2 закрепляет `hx-disabled-elt="find button[type=submit]"` у обеих форм; гейты цели блокировки (`UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED = 19`, перечень исключений) входят в `<verify>`. |
| T-QUICK-QVT-03 | Tampering | Правила стилей подписи | low | accept | Правила не задевают узел индикатора обёртки и панели подтверждения: селекторы не содержат класса индикатора, и это держит `_offenders_panel_indicator_reach` в `<verify>`. Внедрения данных нет: подпись — литерал. |
| T-QUICK-QVT-SC | Tampering | Установка пакетов | low | accept | Пакеты (npm/pip/cargo) не устанавливаются: правятся два существующих файла и добавляется один тестовый. Гейт легитимности пакетов беспредметен. |
</threat_model>

<source_audit>
| Source | Item | Covered by |
|--------|------|------------|
| GOAL | Три визуальные регрессии мастера TG убраны до отгрузки фазы 13 | Задачи 1-2 |
| REQ | QUICK-13-UI-1 (0px между полем 2FA и «Подтвердить») | Задача 1 |
| REQ | QUICK-13-UI-2 (ряд `qr_expired` у левого края) | Задача 1 |
| REQ | QUICK-13-UI-3 (нет подписи загрузки на старте и обновлении) | Задача 2 |
| CONTEXT | D-02 (нет автообновления кода) | Задача 1 — `qr_expired` не получает опросчика |
| CONTEXT | D-05 (опросчик только в `waiting`) | Задачи 1-2 — ветка `waiting` не трогается |
| CONTEXT | D-06, D-08 (идентификатор в скрытом поле; пароль не возвращается; 422 у поля) | Задача 1, T-QUICK-QVT-01 |
| CONTEXT | D-09 (тексты дословно; новые — только D-02/D-03/D-04) | Задача 2, DD-4 |
| CONTEXT | D-11, D-12 (мастер только на JS; ни скрипта, ни `onclick`, ни `hidden`) | Задача 2, DD-1; `test_the_wizard_page_carries_no_client_script` в `<verify>` |
| CONTEXT | Claude's Discretion: «куда ставится `hx-indicator`» | DD-1 (индикатор макроса не трогается, сигнал — `disabled`) |
| EXCLUDED | UI-4…UI-17, WR-01…WR-04, IN-01…IN-03 | Вне объёма по решению владельца |
</source_audit>

<verification>
- Новая регрессия зелёная и была красной до правок (тексты RED в SUMMARY по обеим задачам).
- Сводный набор гейтов из `<verify>` задачи 2 зелёный. Замер при планировании
  на ab72d228 — все эти файлы зелёные до правки: восемь файлов первой
  команды — около 160 с, `test_responsive_markup.py` целиком — 129 с (здесь
  только `-k connect`), `tests/test_planning/` — 44 теста за 0.4 с.
  `test_shell.py` — самый дорогой: больше 6 минут, при планировании до конца
  не домерен. Его запускать фоном параллельно с остальными командами. Он
  остаётся в наборе, потому что гейты шелла разбирают КАЖДЫЙ селектор файла
  стилей, а правило показа подписи — первый в app.css селектор с комбинатором
  `~` (разборщик `_CSS_COMBINATORS = ">+~"` его поддерживает, но впервые
  исполнит на живом файле).
- Отрисовка через `uv run python -c` для `start`, `error`, `qr_expired` и
  `password` (`from app.pages.accounts import _tg_step_markup`) показывает
  новую форму DOM. Фрагмент вывода — в SUMMARY.
- `graphify update .` прогнан.
</verification>

<success_criteria>
- UI-1: поле 2FA и «Подтвердить» разделены промежутком колонки шага на обоих ответах.
- UI-2: ряд действий `qr_expired` центрирован под текстом.
- UI-3: «Загрузка...» видна во время запроса старта, повтора и обновления
  QR. Она держится на `disabled`, который ставит htmx, и не требует ни строчки JS.
- Объём не вышел за три файла. Реестры и числа гейтов не сдвинуты. Замечания
  вне объёма не тронуты.
</success_criteria>

<output>
Create `.planning/quick/260921-qvt-popravit-vizualnye-regressii-mastera-tel/260921-qvt-SUMMARY.md` when done
</output>
