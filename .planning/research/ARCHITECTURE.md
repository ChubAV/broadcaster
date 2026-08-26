# Architecture Research

**Domain:** brownfield server-rendered SaaS (FastAPI + Jinja2), перевод слоя ПИСЬМА на htmx
**Milestone:** v2.1 «HTMX-first»
**Researched:** 2026-08-26
**Confidence:** HIGH — все интеграционные точки сняты чтением исходников `app/pages/`, `app/templates/`, `tests/test_templates/`; внешние утверждения об htmx 2.x проверены по официальному migration guide и исходнику `bigskysoftware/htmx` v2.0.4

---

## Executive Finding

**Слой ответа для htmx в проекте уже написан — один раз, в одном месте, руками.**
`app/pages/ads.py::_save_from_editor` (строки 413-531) — это ровно та развилка,
которую веха обязана размножить на остальные 34 обработчика: один путь бизнес-логики,
`is_htmx = request.headers.get("HX-Request") is not None` в начале, ветвление
на ВЫХОДАХ. Рядом лежат ещё два готовых куска той же машины:

| Что уже есть | Где | Что оно есть на самом деле |
|---|---|---|
| Определение htmx-пути + ветвление на выходах | `app/pages/ads.py:435, 519-531, 611-618` | прототип `respond()` |
| Централизованное «куда вернуть» | `app/pages/schedules.py::_editor_redirect` (214), `_editor_error_redirect` (321) | аргумент `redirect=` будущего `respond()` |
| Рендер МАКРОСА из Python в `HTMLResponse` | `app/pages/accounts.py::_connect_status` (47-50) | рендерер фрагмента |
| Ответ «фрагмент + три OOB» | `app/templates/ads/includes/autosave_response.html` | конвенция `*_response.html` |
| Стабильный `id` на каждой карточке/строке | 5 макросов (см. §Template Inventory) | готовые `hx-target` |

Веха не вводит новую архитектуру. Она **обобщает четыре локальных решения в один
именованный слой** и применяет его к 36 обработчикам. Это меняет оценку риска:
главная опасность не «сработает ли подход», а **тихое расхождение 36 копий**
— ровно тот класс, против которого в проекте уже стоят машинные гейты,
читающие исходник (`tests/test_templates/test_components.py`).

---

## Standard Architecture

### Сегодняшний путь письма (снят по коду)

```
┌──────────────────────────────────────────────────────────────────┐
│  БРАУЗЕР                                                          │
│  <form method="post" action="/x">  ×47 форм, hx-post — 2          │
└─────────────────────────┬────────────────────────────────────────┘
                          │ POST (полная навигация)
┌─────────────────────────▼────────────────────────────────────────┐
│  APIRouter(dependencies=[load_shell_context])   app/pages/__init__│
│    └─ require_access / forbid_when_impersonating (пер-роутерно)   │
├──────────────────────────────────────────────────────────────────┤
│  ОБРАБОТЧИК app/pages/*.py       36 POST-декораторов              │
│    get_user_from_cookie → is_same_origin → владение → мутация     │
│    └──► RedirectResponse(302)          127 вхождений              │
│         ?error=pending | ?saved=1 | ?reset=success | ?retry=…     │
└─────────────────────────┬────────────────────────────────────────┘
                          │ 302 → GET той же страницы целиком
┌─────────────────────────▼────────────────────────────────────────┐
│  GET-обработчик → templates.TemplateResponse(полная страница)    │
│  шаблон читает код из query → {{ alert(text, variant) }}         │
└──────────────────────────────────────────────────────────────────┘
      Потеря: позиция скролла, раскрытые карточки, набранный ввод
```

### Целевой путь письма

```
┌──────────────────────────────────────────────────────────────────┐
│  БРАУЗЕР                                                          │
│  <form method="post" action="/x"          ← ОСТАЁТСЯ (D-09)      │
│        hx-post="/x" hx-target="#row-42"                          │
│        hx-disabled-elt="find button" hx-indicator="…">           │
│  + один глобальный слушатель htmx:responseError в base.html      │
└─────────────────────────┬────────────────────────────────────────┘
                          │ POST + HX-Request: true
┌─────────────────────────▼────────────────────────────────────────┐
│  ТОТ ЖЕ РОУТЕР, ТЕ ЖЕ ЗАВИСИМОСТИ, ТОТ ЖЕ ОБРАБОТЧИК              │
│  ── бизнес-логика НЕ ветвится ────────────────────────────────    │
│  return respond(request,                       ← НОВЫЙ СЛОЙ      │
│      redirect="/accounts/7/groups",   ← базовый путь, обязателен │
│      fragment=("account_groups/includes/group_row.html",         │
│                "group_row", (group, 7, n, user)),                │
│      oob=[…], notice=("group_enabled", "success"))               │
└────────┬────────────────────────────────────┬────────────────────┘
         │ HX-Request отсутствует             │ HX-Request: true
         ▼                                    ▼
  302 → /accounts/7/groups             200 text/html
     ?notice=group_enabled             ┌───────────────────────────┐
         │                             │ <div id="group-row-42">…  │  ← hx-target
         ▼                             │ <span id="groups-count"   │
  GET резолвит код в текст             │       hx-swap-oob="true"> │  ← побочная область
  через app/pages/notices.py           │ <div id="notice"          │
         │                             │       hx-swap-oob="true"> │  ← канал уведомлений
         ▼                             └───────────────────────────┘
  base.html #notice рисует alert()      base.html #notice рисует alert()
         └──────────── ОДИН И ТОТ ЖЕ ТЕКСТ, ОДИН И ТОТ ЖЕ МАКРОС ──┘
```

### Component Responsibilities (новый слой)

| Компонент | Ответственность | Где живёт |
|---|---|---|
| `hx_request(request) -> bool` | единственное объявление «это htmx» на проект | `app/pages/htmx.py` (NEW) |
| `respond(...)` | выбор ФОРМЫ ответа: 302 / фрагмент+OOB / `HX-Location` / `HX-Redirect` | `app/pages/htmx.py` (NEW) |
| `render_macro(template, macro, *args)` | рендер макроса в строку | `app/pages/htmx.py` (NEW, переезд `accounts._connect_status`) |
| `NOTICES: dict[str, Notice]` | закрытый реестр «код → (текст, variant)» | `app/pages/notices.py` (NEW) |
| `resolve_notice(code)` | резолв кода из query в текст для базового пути | `app/pages/notices.py` (NEW) |
| `#notice` OOB-область | ЕДИНСТВЕННАЯ поверхность показа обратной связи оболочки | `app/templates/base.html` (MOD) |
| `*_response.html` | «фрагмент + OOB» для конкретного действия | `<section>/includes/` (NEW ×N) |

---

## 1. Проблема двойного ответа

### Постановка по фактам репозитория

- 36 POST-декораторов в `app/pages/` (35 `@router.post` + 1 `@money_router.post` в `billing.py:316`)
- 127 `RedirectResponse` в `app/pages/`
- 160 утверждений `status_code == 302` в `tests/`
- Деградация без JS — **рамка вехи**, не пожелание: каждая форма остаётся `method="post"` с настоящим `action`

Значит: **каждый обработчик обязан отдавать две формы ответа из одного кода.**

### Что обработчики делают СЕГОДНЯ (прочитано, не угадано)

Обработчики `app/pages/` написаны в узнаваемом едином стиле — цепочка ранних
возвратов, каждый из которых уже сегодня есть `RedirectResponse`:

```python
# app/pages/account_groups.py:299-332 — типовой представитель
user = await get_user_from_cookie(request, db, settings)
if not user:
    return RedirectResponse(url="/login", status_code=302)      # выход 1
result = await db.execute(select(Group).where(...тройной WHERE...))
group = result.scalar_one_or_none()
if group:
    group.is_active = not group.is_active
    await db.commit()
return RedirectResponse(url=f"/accounts/{account_id}/groups", 302)  # выход 2
```

Ключевые свойства этого стиля, которые определяют выбор:

1. **Выходов много и они разнородны.** У `history_retry` их семь, включая
   `Response(status_code=403)` для отказа `is_same_origin` и два разных
   `?retry=` кода. У `_save_from_editor` — четыре.
2. **Возвращаемые типы уже разные:** `RedirectResponse`, `TemplateResponse`,
   `HTMLResponse`, голый `Response(403)`, а `require_access` вообще
   `raise HTTPException(302, headers={"location": ...})`.
3. **Шаблоны построены на МАКРОСАХ в отдельных файлах, а не на блоках.**
   `test_macros_take_no_context` и `test_components_are_documented_macros`
   (`tests/test_templates/test_components.py:599, 617`) это принуждают.
4. **Правило «куда вернуть» уже вынесено в функцию** там, где оно нетривиально
   (`schedules._editor_redirect`).

### Сравнение подходов

| Подход | Как ложится на `app/pages/` как он написан | Вердикт |
|---|---|---|
| **A. FastAPI-зависимость `is_htmx: bool = Depends(hx_request)`** | Объявляет признак в сигнатуре — читаемо, тестируемо, `dependency_overrides` работает. Но признак ≠ ответ: ветвление на 7 выходах `history_retry` всё равно пишется руками 7 раз. Решает 10% задачи. | Взять ЧАСТЬЮ (как источник признака), не как решение |
| **B. Декоратор над обработчиком** | Обязан интерпретировать возвращённое значение. Разнородность типов (п. 2) означает, что декоратор вынужден различать `RedirectResponse` от `Response(403)` от `TemplateResponse` по типу и вытаскивать `location` из заголовка — то есть **угадывать намерение по побочному признаку**. `Response(403)` гарда CSRF он превратил бы во фрагмент. Молчаливое неверное решение — ровно тот класс, который проект в комментариях называет худшим. | **Отклонить** |
| **C. `jinja2-fragments` / `render_block`** | Требует, чтобы фрагменты были `{% block %}` внутри страницы. В проекте фрагменты — МАКРОСЫ в `includes/`, и это принуждается двумя машинными гейтами (п. 3). Переход на блоки означает переписать 5 готовых макросов строк/карточек, переучить `test_macros_take_no_context` и завести новую зависимость при действующей дисциплине минимума зависимостей и нулевого build-шага (D-02). Цена — переучивание конвенции; выгода — ноль, потому что макросы уже дают ровно ту же независимую отрисовку. | **Отклонить** |
| **D. Тонкий слой рендера: явный `respond()`, вызываемый на выходах** | Это ОБОБЩЕНИЕ трёх уже существующих локальных решений (`_save_from_editor`, `_editor_redirect`, `_connect_status`), а не новая идея. Каждый выход остаётся явным `return` — читается так же, как читается сейчас. `Response(403)` остаётся `Response(403)` и через слой не проходит вовсе. Аргумент `redirect=` делает базовый путь СТРУКТУРНО обязательным: забыть его нельзя — не соберётся вызов. | **✅ РЕКОМЕНДАЦИЯ** |

### Рекомендуемая форма

`app/pages/htmx.py` — НОВЫЙ модуль. Не `common.py`: тот уже 745 строк и мешает
Jinja-глобалы, чтение cookie и CSRF-гард; машинному гейту вехи нужен ОДИН файл,
который он читает как источник правила (тот же приём, что у
`tests/test_pages/test_access_gate.py`, читающего `app/pages/__init__.py`).

```python
# app/pages/htmx.py
Fragment = tuple[str, str, tuple]          # (шаблон, макрос, аргументы)

def hx_request(request: Request) -> bool:
    """ЕДИНСТВЕННОЕ объявление признака htmx на проект."""
    return request.headers.get("HX-Request") is not None

def respond(
    request: Request,
    *,
    redirect: str,                      # базовый путь — ОБЯЗАТЕЛЕН
    fragment: Fragment | None = None,   # None ⇒ действие навигационное
    oob: Sequence[Fragment] = (),
    notice: str | None = None,          # КОД из app/pages/notices.py
    external: bool = False,             # адрес вне приложения (ЮKassa)
    status_code: int = 200,
) -> Response
```

Три ветки, и все три уже встречаются в проекте по одиночке:

| Условие | Ответ | Прецедент в коде |
|---|---|---|
| не htmx | `RedirectResponse(redirect + "?notice=<code>", 302)` | все 127 сегодняшних редиректов |
| htmx + `fragment` | `HTMLResponse(макрос + OOB-куски + OOB-уведомление)`, 200 | `ads/includes/autosave_response.html` |
| htmx + `fragment is None` | `Response(204, headers={"HX-Location": redirect})`, либо `HX-Redirect` при `external=True` | новое, но заголовки — из того же семейства, что уже применяемый `HX-Push-Url` (`ads.py:522`) |

**Почему `redirect=` обязателен и позиционно первым.** Он ЕСТЬ контракт
деградации. Обработчик, у которого его нет, не компилируется как вызов —
деградация становится свойством ТИПА, а не дисциплины. Это тот же приём, что
`RowDeleteSite(..., forms=3)` в гейте: ожидаемое число объявлено, а не выведено.

**Почему `notice` — КОД, а не текст.** Правило уже написано в проекте дважды:
`billing._payment_error_message` (137) резолвит `?error=` через закрытый словарь,
`ads.py:642` резолвит `sched_error` через `SCHEDULE_ERROR_REASONS` с явной
припиской «значение строки запроса лишь ВЫБИРАЕТ текст и в разметку не
попадает». Веха эту норму не изобретает — она её обобщает. Произвольный текст в
адресной строке был бы регрессом по отношению к уже принятому решению.

### Классификация 36 обработчиков по ФОРМЕ ответа

Это главный вход для роадмаппера: «фрагмент» — не универсальный ответ.

| Класс | Ответ на htmx-пути | Кол-во | Обработчики |
|---|---|---|---|
| **A. Правка на месте** | фрагмент + OOB | **15** | `account_groups`: toggle, delete · `schedules`: new, edit, toggle · `ads`: new✅, edit✅ · `accounts`: retry-sync, sync-groups, connect/max/start · `admin`: unlimited, block, workers/restart, queue/drop · `profile` |
| **B. Навигационные** | `HX-Location` (204) | **5** | `ads/{id}/delete`*, `accounts/{id}/delete`*, `schedules/{id}/delete`*, `admin/users/{id}/delete`, `admin/users/{id}/impersonate` |
| **C. Смена личности** | ошибка → фрагмент формы; успех → `HX-Location` | **10** | 9 форм авторизации + `/impersonation/stop` |
| **D. Внешний адрес** | `HX-Redirect` (НЕ `HX-Location`) | **1** | `/billing/subscribe` → `confirmation_url` ЮKassa |
| **E. Многошаговый мастер** | фрагмент шага | **5** | QR-поток Telegram (см. §4) |

\* Три из класса B имеют ДВЕ точки вызова с разным исходом. `ads/{id}/delete`
вызывается и из карточки списка (`ads/includes/ad_card.html:116` — там правильно
удалить `#ad-row-{id}` фрагментом), и из редактора (`ads/form.html:267` — там
надо уйти на `/ads`). `schedules/*` уже решают ровно это через `return_to` в теле
формы (`_editor_redirect`). **Вывод для планировщика: расширить существующий
механизм `return_to` вместо изобретения второго.**

**⚠️ `/billing/subscribe` — единственный обработчик, где `HX-Location` СЛОМАЕТ
работающий платёж.** `HX-Location` делает AJAX-GET по адресу, а htmx 2.x по
умолчанию несёт `selfRequestsOnly: true` — межсайтовый запрос будет заблокирован
самим htmx. Успешный путь обязан уйти `HX-Redirect` (полная навигация браузера).
Проверено по `app/pages/billing.py:400` (`return RedirectResponse(url=result["confirmation_url"])`).

---

## 2. Реструктуризация шаблонов

### Что УЖЕ готово (проверено по исходникам)

Контракт «фрагмент по `hx-target`» требует, чтобы каждая записываемая
карточка/строка (а) собиралась одним макросом и (б) несла стабильный `id`.
**Пять из пяти продуктовых списков это уже выполняют:**

| Файл | Стабильный `id` | Готов как `hx-target` |
|---|---|---|
| `account_groups/includes/group_row.html:31` | `group-row-{{ group.id }}` | ✅ |
| `schedules/includes/schedule_row.html:64` | `schedule-row-{{ s.id }}` | ✅ |
| `ads/includes/ad_card.html:41` | `ad-row-{{ ad.id }}` | ✅ |
| `ads/includes/sched_card.html:112` | `sched-{{ s.id }}` | ✅ (уже якорь `#sched-N` в `_editor_redirect`) |
| `history/includes/history_card.html:183` | `history-row-{{ log.id }}` | ✅ |
| `accounts/partials/sync_status_card.html` | `account-row-{{ account_id }}` | ✅ **и уже является целью `hx-swap="outerHTML"`** |

Это самый недооценённый факт вехи: **этап «сделать карточки независимо
рендерящимися» для продуктовой части проекта УЖЕ ВЫПОЛНЕН Фазами 2-4 v2.0.**
Планировщику не нужна фаза «извлечь фрагменты» — нужна фаза «подключить существующие».

### Что менять обязательно

| Что | Почему | Объём |
|---|---|---|
| `admin/includes/*.html` — 9 файлов, **0 макросов, 0 `id`** | admin-строки собраны `{% include %}`-ами, а не макросами; целиться нечем. Записывают трое: `worker_row`, `queue_row`, `user_detail` | 3 файла обязательно (`worker_row`, `queue_row`, + блок действий в `user_detail.html`), 6 — опционально |
| `accounts/*` — тройная копия разметки | `list.html`, `partial_cards.html`, `partials/sync_status_card.html` несут ТРИ ветки статуса каждый; `ROW_DELETE_PLACES = 12` в гейте. Каждый `hx-post` на карточке аккаунта правится в 3 местах × до 3 веток | **9 правок на одно действие** — наибольший радиус в проекте |
| `components/modal.html:111` | форма панели подтверждения — ОДНА, а обслуживает 16 мест / 10 потребителей. Добавление `hx-post` в макрос переводит все 16 подтверждений разом | 1 файл ⇒ 16 мест. **Наивысший рычаг вехи** |
| `components/filters.html:31` | форма фильтров — `method=get`, ЧТЕНИЕ. В объём вехи (письмо) не входит | 0 |

### Куда ставит OOB-область уведомлений

**Место: `app/templates/base.html`, внутри `<div data-main>`, между
`<header data-head>` (213) и `<div data-body>` (232).**

```jinja
            </header>

            {#- КАНАЛ ОБРАТНОЙ СВЯЗИ. Единственная поверхность показа результата
                действия в оболочке. Стоит СНАРУЖИ {% block content %}: внутри
                него дочерний шаблон мог бы область переопределить, и потеря
                была бы молчаливой — ровно тот класс, за который вынесен
                #wa-status в connect_wa.html.

                aria-live стоит НА САМОМ озвучиваемом элементе, а не на обёртке
                — то же правило, что записано у #autosave-indicator
                (ads/includes/autosave_response.html:14-15).

                НЕТ КОДА — НЕТ РАЗМЕТКИ ВОВСЕ, умолчание запрещено: пустая
                плашка на 26 страницах хуже её отсутствия (правило виджета
                доступа, base.html:131-136). -#}
            <div id="notice" data-notice aria-live="polite" role="status">
              {%- if notice %}{{ alert(notice.text, notice.variant) }}{% endif -%}
            </div>

            <div data-body>
```

**Почему не над `data-shell`, рядом с полосой имперсонации (71-78).** Та полоса
документная и постоянная — она обязана быть видна на КАЖДОЙ странице всё время.
Уведомление принадлежит разделу, в котором пользователь только что действовал,
а на 375px документная плашка выталкивает вниз всю оболочку.

**Почему НЕ дублировать в `auth_base.html`.** Экраны авторизации наследуют ВТОРОЙ
шелл (`app/templates/auth_base.html`, 7 шаблонов), и они уже сегодня рисуют отказ
своим `{% if error %}{{ alert(error) }}{% endif %}` внутри формы. Второй канал дал
бы авторизации два способа сказать одно и то же. Область уведомлений — свойство
оболочки приложения, а не всех страниц проекта.

### Как обработчик отдаёт фрагмент ВМЕСТЕ с уведомлением

Конвенция берётся готовой у единственного существующего образца —
`ads/includes/autosave_response.html`. Обобщённое имя: **`*_response.html`**.

```
app/templates/<section>/includes/<action>_response.html
```

Правило файла (дословно по образцу):
1. первым идёт ОСНОВНОЙ фрагмент — цель `hx-target`, без `hx-swap-oob`;
2. далее побочные области — каждая своим `id` + `hx-swap-oob="true"`;
3. уведомление НЕ выписывается в файле — его дописывает `respond()` из
   `notices.py`, чтобы 36 обработчиков не носили 36 копий одной разметки.

Сигнатура макроса побочной области — единая, чтобы гейт умел её проверять:

```jinja
{# app/templates/includes/oob.html — NEW #}
{% macro oob(id) -%}
<div id="{{ id }}" hx-swap-oob="true">{{ caller() }}</div>
{%- endmacro %}
```

Блочный вызов (`{% call %}`) — тот же приём, что уже применяют `components/table.html::cell`
и `components/modal.html` (слот скрытых полей), и он уже покрыт тестами
(`test_cell_label_in_block_call`, `test_modal_accepts_block_fields`). Готовую
разметку строкой макрос не принимает — норма проекта сохраняется.

---

## 3. Инвентарь: НОВОЕ против ИЗМЕНЁННОГО

### Genuinely NEW

| # | Артефакт | Файл | Размер | Зависимость |
|---|---|---|---|---|
| N1 | `hx_request()`, `respond()`, `render_macro()` | `app/pages/htmx.py` | ~120 строк | — |
| N2 | Реестр уведомлений «код → (текст, variant)» | `app/pages/notices.py` | ~80 строк; ≥8 кодов существуют уже (`pending`, `disabled`, `payment`, `saved`, `reset`, `retry:*`, `sched_error:*`) | — |
| N3 | OOB-область `#notice` | `app/templates/base.html` (+12 строк) | 1 правка | N2 |
| N4 | Макрос-обёртка `oob(id)` | `app/templates/includes/oob.html` | ~6 строк | — |
| N5 | Глобальный обработчик `htmx:responseError` | `base.html` + `auth_base.html`, inline `<script>` ~15 строк | 2 правки | N3 |
| N6 | Конфиг `responseHandling` (`<meta name="htmx-config">`) | `base.html` + `auth_base.html` `<head>` | 2 правки | htmx 2.x |
| N7 | Ответы `*_response.html` | `<section>/includes/` | **~13 новых файлов** (по одному на действие класса A, кроме двух готовых в `ads/`) | N4 |
| N8 | Фрагменты шагов QR-мастера Telegram | `accounts/partials/tg_qr_*.html` | **5 файлов** (см. §4) | N1 |
| N9 | Фрагмент результата загрузки изображения | `ads/includes/upload_response.html` | 1 файл | N1 |
| N10 | Обновление вендоренного htmx 1.9.10 → 2.x | `app/static/js/htmx.min.js` | 1 файл + бамп `asset_version` | — |
| N11 | Новые машинные гейты | `tests/test_templates/test_htmx_contract.py` | ~250 строк (см. §6) | N1-N4 |

**Итого нового: 4 модуля Python/JS-конфига + ~20 файлов шаблонов + 1 файл тестов.**

### MODIFIED

| Область | Файлов | Точек правки | Основание счёта |
|---|---|---|---|
| Роутеры страниц | **9** из 14 (`account_groups`, `accounts`, `admin`, `ads`, `auth`, `billing`, `history`, `profile`, `schedules`) | **36 обработчиков**; из них 15 класса A требуют ещё и `*_response.html` | `grep -c '_router\.post'` |
| Формы в шаблонах | **27** файлов | **47 форм** (25 продуктовых + 9 auth + 6 admin + 1 имперсонация + 6 в `accounts/*` дублях) | `grep -rn '<form' app/templates` |
| Разметка `accounts/*` | 3 | 9 (3 файла × 3 ветки статуса) | `ROW_DELETE_SITES` в гейте |
| `components/modal.html` | 1 | 1 правка ⇒ **16 мест подтверждения** | `MODAL_PLACES = 16` |
| `admin/includes/*` — добавить `id` и/или макросы | 3 обязательно, 6 опционально | 3 | 0 `id`, 0 `{% macro %}` во всех девяти |
| `app/routes/uploads.py` — вторая форма ответа | 1 | 1 (`return {"path": key}` → фрагмент или JSON по `HX-Request`) | `uploads.py:319` |
| Ручные `fetch()` | 2 шаблона | **6 вызовов** (`ads/form.html` ×1, `accounts/connect_tg_user.html` ×5) | `grep -rn 'fetch(' app/templates` |
| Тесты, утверждающие 302 | ~30 файлов | **160 утверждений** `status_code == 302` | `grep -rn 'status_code == 302' tests/` |
| Существующие `hx-*` под 2.x | 22 шаблона | 79 атрибутов (25 `hx-swap`, 24 `hx-trigger`, 22 `hx-get`, 5 `hx-swap-oob`, 2 `hx-post`, 1 `hx-sync`) | `grep -rho 'hx-[a-z-]*'` |

**Три пиковые точки радиуса, названные величиной:**
1. **160 утверждений `status_code == 302`.** Это не «правка тестов» — это
   пересмотр контракта. Каждое утверждение обязано стать ПАРОЙ: базовый путь
   по-прежнему 302, htmx-путь — 200 с фрагментом или 204 с `HX-Location`.
   Правильная форма — параметризованный обход, а не 320 отдельных функций.
2. **`accounts/*` — 9 правок на одно действие.** Тройная копия разметки уже
   стоит проекту гейта `ROW_DELETE_PLACES = 12`; веха её нагружает.
3. **`components/modal.html` — 1 правка ⇒ 16 мест.** Рычаг в обратную сторону:
   единственное место, где одна строка закрывает шестнадцать.

---

## 4. Два JSON-потока

### 4.1 `/api/uploads/image` — multipart → JSON `{path: ...}`

**Что есть сегодня** (`app/routes/uploads.py:191-319`, `ads/form.html:426-455`):

```
file-input (change)  ──► handleFiles()  ──► uploadFile() ──► fetch POST /api/uploads/image
                                                                    │
                              imagePaths.push(data.path) ◄──── {"path": key} 200
                                                                    │ 400
                                                        refusalTextOf(resp) → detail
                              renderImages()   ← ПЕРЕСОБИРАЕТ полосу вложений узлами DOM
                              requestSave()    ← dispatchEvent('change') на #ad-form
```

**Границы фрагментов при переводе.** Загрузка НЕ самостоятельна — её результат
существует ради двух вещей: скрытых `<input name="images">` в `#image-inputs` и
плиток в `#media-strip`. Обе уже имеют `id`, обе уже перерисовываются целиком.
Значит фрагмент естественный:

```html
<!-- ads/includes/upload_response.html — NEW -->
{# ОСНОВНОЙ: полоса плиток #}
<div data-media id="media-strip">…{{ каждая плитка }}…{{ плитка «+ ФАЙЛ» }}</div>
{# OOB: скрытые поля #}
{% call oob('image-inputs') %}{% for k in keys %}<input type="hidden" name="images" value="{{ k }}">{% endfor %}{% endcall %}
{# OOB: счётчик длины — его порог ЗАВИСИТ от наличия вложений (CAPTION_LIMIT vs TEXT_LIMIT) #}
{% call oob('text-counter') %}…{% endcall %}
{# OOB: отказ — в СВОЙ ящик, не в общий #notice #}
{% call oob('upload-error') %}{% if error %}{{ alert(error) }}{% endif %}{% endcall %}
```

Разметка формы:

```html
<form hx-post="/api/uploads/image" hx-encoding="multipart/form-data"
      hx-target="#media-strip" hx-swap="outerHTML"
      hx-trigger="change from:#file-input"
      hx-include="#image-inputs"          ← сервер узнаёт УЖЕ прикреплённые ключи
      hx-disabled-elt="find label" hx-indicator="#upload-indicator">
```

**Четыре решения, которые перевод обязан принять (все — по прочитанному коду):**

1. **`/api/uploads/image` перестаёт быть чисто-JSON, но JSON НЕ теряет.**
   Он живёт в `app/routes/` (JSON-API), гейтится
   `get_current_user_id_with_access`, а не `require_access`. Правильная форма —
   тот же `hx_request()`-развилка на выходе: `HX-Request` ⇒ фрагмент,
   иначе ⇒ прежний `{"path": key}`. Это сохраняет и контракт API, и 14 тестов
   `tests/test_routes/`.
2. **Отказ обязан приезжать со статусом, который htmx СВОПАЕТ.** Сегодня
   отказ — `HTTPException(400, detail=…)`. htmx (и 1.x, и 2.x) по умолчанию
   **4xx не свопает вовсе** — плашка отказа не появилась бы, и загрузка
   «молча ничего не делала бы». Два законных выхода: (а) вернуть 422 и добавить
   `{"code":"422","swap":true}` в `responseHandling`; (б) вернуть 200 с телом,
   несущим только OOB-отказ. **Рекомендация — (а)**: код отказа остаётся
   осмысленным для JSON-потребителя и для логов.
3. **Копию текста отказа в JS (`UPLOAD_TYPE_ERROR`, `UPLOAD_LIMIT_ERROR`,
   `UPLOAD_TRANSPORT_ERROR`) можно СНЯТЬ**, и это чистый выигрыш вехи: сегодня
   `ads/form.html:300-302` держит вторую копию серверных текстов, а
   render-тест в `tests/test_pages/test_ads_editor.py` держит их совпадение.
   Сервер, отдающий разметку, делает копию ненужной, а тест — снимаемым.
4. **`renderImages()` (≈45 строк построения DOM узлами) уходит целиком.**
   Вместе с ним уходит и повод для правила «строить узлами, а не конкатенацией»
   в этом файле — правило остаётся в силе для остальных, гейт не ослабляется.
   `requestSave()` заменяется на `hx-trigger="… , htmx:afterSwap from:#media-strip"`
   на `#ad-form` — очередь `hx-sync="this:queue last"` при этом сохраняется как есть.

**Итог:** `/api/uploads/image` — самый дешёвый из двух потоков. Одна развилка в
обработчике, один новый шаблон, минус ~70 строк JS, минус одна пара копий текста.

### 4.2 QR-поток Telegram — машина состояний над живой сессией Telethon

**Что есть сегодня** (`app/pages/accounts.py:215-347`, `accounts/connect_tg_user.html:71-223`):

```
                    ┌─ start-btn onclick=startQR() ─┐
                    ▼                                │
POST /start-qr ──► {session_id, qr_image}            │ ошибка → showError()
   │  currentSessionId = data.session_id   ← СОСТОЯНИЕ ЖИВЁТ В ПЕРЕМЕННОЙ JS
   ▼
setInterval(checkStatus, 3000)
   │
GET /qr-status?session_id=… ──► {"status": waiting|success|needs_2fa|expired|error}
   ├─ waiting   → продолжать
   ├─ success   → stopPolling(); POST /complete {session_id} → создать MessengerAccount → showSection('success')
   ├─ needs_2fa → stopPolling(); showSection('2fa') → submit2FA() → POST /verify-2fa {session_id, password}
   ├─ expired   → stopPolling(); показать refresh-btn → POST /refresh-qr {session_id} → новый qr_image
   └─ error     → stopPolling(); showError()
```

Четыре шага — `hidden`-блоки, переключаемые `showSection()`; ошибка — `#error-box`;
состояние `currentSessionId` и `pollInterval` — переменные модуля.

**У проекта УЖЕ ЕСТЬ работающий образец ровно этого мастера — на HTML-фрагментах.**
Поток WhatsApp (`/accounts/connect/wa/status`, `app/pages/accounts.py:429-475` +
`accounts/connect_wa.html` + `accounts/partials/connect_status.html`) делает то же
самое БЕЗ единого `fetch()`:
- один якорь `<div id="wa-status" hx-get="…/status" hx-trigger="every 3s" hx-swap="innerHTML">`;
- три макроса ответа: `notice(message, variant)`, `qr(src, label)`, `connected(label)`;
- **опрос останавливается тем, что очередной ответ приходит БЕЗ `hx-get`/`hx-trigger`**
  — механизм задокументирован в шапке `accounts/partials/sync_status_card.html:3-12`
  и закреплён парой тестов `test_sync_polling_stops` / `test_sync_polling_continues_while_syncing`
  (`tests/test_pages/test_htmx_preserved.py:254, 270`).

**Проект QR-потока Telegram = применение этого образца к пяти состояниям.**

**Границы фрагментов.** Один якорь на весь мастер, а не четыре `hidden`-блока:

```html
<!-- accounts/connect_tg_user.html — после перевода -->
<div class="connect-shell">
  {{ card_open() }}
  {#- ЕДИНСТВЕННЫЙ ЯКОРЬ МАСТЕРА. Идентификатор и запрос стоят на ОДНОМ элементе:
      ответ заменяет его СОДЕРЖИМОЕ. Перенос идентификатора на соседний элемент
      рвёт мастер молча — то же предупреждение, что в connect_wa.html:29-33. -#}
  <div id="tg-connect">
    <form method="post" action="/accounts/connect/tg_user/start-qr"
          hx-post="/accounts/connect/tg_user/start-qr"
          hx-target="#tg-connect" hx-swap="innerHTML"
          hx-disabled-elt="find button" hx-indicator="#tg-indicator">
      {{ button('Начать подключение', variant='primary') }}
    </form>
  </div>
  {{ card_close() }}
</div>
```

**Пять фрагментов — по одному на состояние, все в `accounts/partials/`:**

| Файл (NEW) | Отдаёт | Несёт опрос? | Несёт `session_id`? |
|---|---|---|---|
| `tg_qr_waiting.html` | `<img src=qr>` + «Ожидание сканирования…» | **да** — `hx-get="/…/qr-status" hx-trigger="every 3s" hx-vals` | да, `<input type="hidden" name="session_id">` |
| `tg_qr_expired.html` | «QR-код истёк» + форма `hx-post="/…/refresh-qr"` | **нет** ⇒ опрос останавливается | да |
| `tg_qr_2fa.html` | поле пароля + форма `hx-post="/…/verify-2fa"` | **нет** | да |
| `tg_qr_connected.html` | бейдж «Подключено» + ссылка на `/accounts` | **нет** | нет |
| `tg_qr_error.html` | `{{ alert(message) }}` + форма «Начать заново» | **нет** | нет |

**Как поллинг становится `hx-trigger`.** Прямой перенос:
`setInterval(checkStatus, 3000)` → `hx-trigger="every 3s"` на самом фрагменте
`tg_qr_waiting.html`. `stopPolling()` → **отсутствие** атрибутов в четырёх
остальных фрагментах. Это не приём — это ровно то, чем уже пользуются два
работающих опроса проекта, и у механизма есть парные тесты, которые
надо просто размножить на новый мастер.

**Как машина состояний ложится на свопы.** Один обработчик `GET /qr-status`
диспетчеризует ВСЕ переходы, возвращая соответствующий фрагмент вместо
`{"status": …}`:

| `get_qr_status()` | Сегодня в JS | Становится |
|---|---|---|
| `waiting` | продолжать интервал | `tg_qr_waiting.html` (с опросом) — вечный цикл самозамены |
| `success` | `stopPolling()` + **второй fetch** `/complete` | **обработчик сам зовёт `complete_auth()` и создаёт `MessengerAccount`**, возвращает `tg_qr_connected.html` |
| `needs_2fa` | `stopPolling()` + `showSection('2fa')` | `tg_qr_2fa.html` (без опроса) |
| `expired` | `stopPolling()` + показать кнопку | `tg_qr_expired.html` (без опроса) |
| `error` | `stopPolling()` + `showError()` | `tg_qr_error.html` (без опроса) |

**⚠️ Это сворачивает `POST /complete` внутрь `GET /qr-status`, и решение
нетривиальное — назвать его планировщику явно.** Сегодня клиент делает ДВА
запроса подряд (статус, потом complete), и между ними живёт окно, в котором
вкладка может закрыться с уже авторизованной, но не сохранённой сессией.
Свёртка окно закрывает. Цена: `GET` перестаёт быть безопасным методом — он
создаёт `MessengerAccount`. Два законных выхода:
- **(а) свернуть** и переименовать маршрут в `POST /qr-poll` с `hx-trigger="every 3s"`
  на форме (htmx умеет периодический POST) — метод честен, окно закрыто;
- **(б) не сворачивать**: `tg_qr_waiting.html` при `success` возвращает
  фрагмент, который САМ несёт `hx-post="/…/complete" hx-trigger="load"` —
  цепочка из двух запросов сохраняется декларативно, окно остаётся.

**Рекомендация — (а).** Причина из кода: `complete_auth(session_id)` уже
идемпотентен по факту («Сессия не найдена или авторизация не завершена» — 
`accounts.py:335`), а окно потери авторизованной сессии Telethon — реальная
цена, тогда как «GET не должен писать» здесь чинится переименованием метода,
а не архитектурой.

**Что уходит:** 152 строки скрипта (`connect_tg_user.html:71-223`), четыре
`hidden`-блока, `showSection()`, `showError()`/`hideError()`, `#error-box`,
переменные `currentSessionId`/`pollInterval`. `session_id` переезжает из
переменной JS в `<input type="hidden">` внутри фрагмента — то есть в то же
место, где уже живёт `ad_id` редактора объявлений (`#ad-id-field`,
подменяемое OOB). Прецедент есть, приём известен, тест на него есть.

**Что остаётся ограничением:** `POST /refresh-qr`, `/verify-2fa`, `/complete`
сегодня читают `await request.json()`. Они обязаны перейти на `Form(...)` —
htmx шлёт `application/x-www-form-urlencoded`. Три обработчика, механическая правка.

**Что деградация без JS даёт и чего не даёт.** Форма «Начать подключение»
уходит обычным POST и рисует шаг QR — это работает. Дальше **опрос без JS
невозможен по природе**: пользователю остаётся кнопка «Проверить»
(`method="post"` на тот же `/qr-poll`), обновляющая шаг вручную. Это честная
деградация, а не эквивалент; её надо записать в критерий приёмки фазы явно,
иначе UAT сочтёт её дефектом.

---

## 5. Изменение потока данных: канал уведомлений

### Что несут `?error=` / `?saved=1` сегодня

Восемь редиректов с кодом обратной связи, пять разных написаний:

| Код в адресе | Где ставится | Где резолвится в текст |
|---|---|---|
| `?error=disabled\|pending\|payment` | `billing.py:357, 394, 399` | `billing._payment_error_message` (137) → контекст `error_message` (308) |
| `?saved=1` | `profile.py:70` | шаблон `profile.html` |
| `?reset=success` | `auth.py:806` | `auth/login.html:10` — `request.query_params.get('reset')` |
| `?retry=RETRY_QUEUED\|RETRY_BUSY` | `history.py:952, 1043` | `history.py:1055` — `retry: str = Query(None)` |
| `?sched_error=<reason>` | `schedules._editor_error_redirect` (328) | `ads.py:642` через `SCHEDULE_ERROR_REASONS` |
| `?expired=1` | `pages/__init__.py:47` | **НИГДЕ — читать запрещено прямо** (`__init__.py:80-83`) |

Из этой таблицы следуют два вывода, оба важны планировщику:
1. **Правило «код, а не текст» в проекте уже действует** — в трёх местах из
   пяти, с выписанным обоснованием. Веха его не вводит, а достраивает до
   единообразия.
2. **Разнобой имён (`error`/`saved`/`reset`/`retry`/`sched_error`) — не стиль,
   а пять независимых микро-контрактов**, каждый со своим резолвером в своём
   модуле. Единый канал их СВОДИТ, и это самостоятельная ценность вехи,
   независимая от htmx.

### Целевой поток

```
                     ОДИН ИСТОЧНИК ТЕКСТА
        app/pages/notices.py :: NOTICES = {"group_enabled": Notice("Группа включена", "success"), …}
                              ▲                                       ▲
        ┌─────────────────────┘                                       └──────────────┐
        │ htmx-путь                                                 базовый путь     │
┌───────┴──────────────────────────┐                    ┌──────────────────────────┴─┐
│ respond(notice="group_enabled")  │                    │ 302 → /…?notice=group_enabled│
│  дописывает к телу ответа:       │                    │        ▼                     │
│  <div id="notice"                │                    │ GET-обработчик:              │
│       hx-swap-oob="true">        │                    │  notice=resolve_notice(code) │
│    {{ alert(text, variant) }}    │                    │  → в контекст шаблона        │
│  </div>                          │                    │        ▼                     │
└───────┬──────────────────────────┘                    │ base.html #notice            │
        │                                               │  {{ alert(n.text,n.variant) }}│
        └──────────► ОДИН И ТОТ ЖЕ id, ОДИН И ТОТ ЖЕ ───┴──────────────────────────────┘
                     макрос components/alert.html
```

### Пять свойств, которые контракт обязан удержать

1. **Текст рождается на СЕРВЕРЕ и только там.** В адрес уходит код из закрытого
   множества. Неизвестный код не выбирает ничего — область не рисуется, страница
   отдаётся 200. Правило дословно скопировано с `ads.py:642` («значение приходит
   строкой запроса, то есть из ссылки или закладки»).
2. **Базовый путь ОБЯЗАН продолжать работать.** `?notice=<code>` — не
   совместимость ради совместимости: это единственный носитель обратной связи
   при выключенном JS, и рамка вехи его сохраняет. Отсюда обязательность
   `redirect=` в `respond()`.
3. **`load_shell_context` наливает `request.state.shell` ДО обработчика.**
   Зависимость висит на роутере (`app/pages/__init__.py:123`), то есть на POST
   она отрабатывает **до `db.commit()`**. **Счётчики навигации в
   `request.state.shell` на htmx-пути ПРОТУХШИЕ.** Обработчик удаления группы,
   отдавший `nav_counts` из `request.state.shell` OOB-куском, показал бы
   старое число. Два выхода: (а) `respond()` при наличии OOB-счётчика зовёт
   `get_shell_context(db, user)` ПОВТОРНО после коммита; (б) счётчики оболочки
   в OOB не отдаются вовсе. **Рекомендация — (а), но только для тех действий,
   которые счётчик реально двигают** (создание/удаление объявления, аккаунта,
   расписания; toggle — нет). Цена (а) — 4 подзапроса счёта на действие;
   цена (б) — цифра в сайдбаре расходится с экраном до следующей навигации.
4. **`aria-live` — на самом `#notice`, не на обёртке.** Правило уже выписано у
   `#autosave-indicator` (`ads/includes/autosave.html:20-28`).
5. **Нет кода — нет разметки.** Пустая плашка-заглушка запрещена по тому же
   основанию, что и у виджета доступа (`base.html:131-136`).

### ⚠️ Ловушка: OOB не приезжает, если htmx не свопает

`hx-swap-oob` обрабатывается **внутри** свопа. При ответе, который htmx свопать
не собирается, OOB-куски не применяются вовсе — включая область уведомлений.
Затрагивает три реальных места в этом коде:

| Ответ | Где | Что произойдёт без правки |
|---|---|---|
| `Response(status_code=403)` гарда `is_same_origin` | `history.py:947`, `admin.py` ×3, `billing.py:354` | **молчание**: кнопка нажата, ничего не произошло, объяснения нет |
| `TemplateResponse(..., status_code=400)` | `profile.py:82` | форма не перерисуется, отказ «Неверный часовой пояс» пропадёт |
| `HTTPException(302, headers={"location": …})` гейта `require_access` | `pages/__init__.py:105` | htmx пойдёт по редиректу XHR-ом и свопнет **всю страницу `/billing`** внутрь `#row-42` |

Это и есть причина, по которой в объёме вехи стоят ДВА новых артефакта, а не
один: `responseHandling`-конфиг (N6) и глобальный `htmx:responseError` (N5).
Третий случай (`require_access` на htmx-запросе) — отдельная правка гейта:
на `HX-Request` он обязан отвечать `HX-Redirect`, а не 302.

---

## 6. Порядок работ

### Граф зависимостей

```
                 ┌──────────────────────────────────────────┐
   P0  ──────────► 0. htmx 1.9.10 → 2.x + responseHandling  │  ЖЁСТКИЙ ГЕЙТ
                 │    ревизия 79 существующих hx-атрибутов   │  (решение вехи)
                 └───────────────┬──────────────────────────┘
                                 │
       ┌─────────────────────────┼──────────────────────────────┐
       ▼                         ▼                              ▼
┌──────────────┐   ┌───────────────────────────┐   ┌──────────────────────────┐
│ 1. Слой      │   │ 2. Канал уведомлений      │   │ 3. Загрузка изображения  │
│  app/pages/  │   │  notices.py + #notice     │   │  /api/uploads/image      │
│  htmx.py     │◄──┤  + htmx:responseError     │   │  ← НЕЗАВИСИМА, может     │
│  N1          │   │  N2 N3 N4 N5              │   │    идти параллельно 1-2  │
└──────┬───────┘   └──────────┬────────────────┘   └──────────────────────────┘
       │                      │
       └──────────┬───────────┘
                  ▼
     ┌────────────────────────────────────────┐
     │ 4. ПИЛОТ: account_groups (2 обработчика)│  самый простой класс A:
     │    доказывает контракт целиком          │  готовый id, готовый макрос,
     │    + первые машинные гейты (N11)        │  2 действия, 1 шаблон
     └────────────┬───────────────────────────┘
                  ▼
   ┌──────────────┴──────────────┬─────────────────┬────────────────┐
   ▼                             ▼                 ▼                ▼
┌──────────────┐  ┌────────────────────┐  ┌──────────────┐  ┌──────────────┐
│ 5a. schedules│  │ 5b. modal.html     │  │ 5c. admin    │  │ 5d. accounts │
│  + ads (4)   │  │  1 правка ⇒16 мест │  │  6 + id для  │  │  3 файла ×3  │
│              │  │  РЫЧАГ             │  │  3 includes  │  │  ветки = 9   │
└──────────────┘  └────────────────────┘  └──────────────┘  └──────────────┘
   ▼
┌───────────────────────────────────────────────────────────┐
│ 6. QR-поток Telegram (5 обработчиков, машина состояний)    │  ПОСЛЕ 1-4:
│    Telethon-сессия живая, отката дешёвого нет             │  нужен готовый слой
└─────────────────────────┬─────────────────────────────────┘
                          ▼
┌───────────────────────────────────────────────────────────┐
│ 7. Авторизация (9 форм + /impersonation/stop)             │  ПОСЛЕДНЯЯ
│    второй шелл auth_base.html, смена cookie личности      │  осознанно
└───────────────────────────────────────────────────────────┘
```

### Обоснование порядка — по реальным зависимостям

| Шаг | Почему здесь, а не раньше/позже |
|---|---|
| **0 (htmx 2.x) — блокирует ВСЁ** | Решение вехи: 47 форм под 1.x пришлось бы править дважды. Сверх того: `responseHandling` в декларативной форме появился ТОЛЬКО в 2.0, а без него отказ 4xx не свопается, то есть контракт «ошибка перерисовывает форму» не собирается вовсе. Ревизия 79 существующих атрибутов дешевле сейчас, чем на нескольких сотнях новых. **Риск при этом низкий: в 22 шаблонах нет ни `hx-on`, ни `hx-vars`, ни `hx-sse`/`hx-ws`, ни расширений — то есть НИ ОДНОГО из ломающих изменений 2.0.** Проверено `grep -rho 'hx-[a-z-]*'`. |
| **1 и 2 — параллельны друг другу, но оба до 4** | `respond()` дописывает OOB-уведомление ⇒ зависит от `notices.py` и `#notice`. Но сами по себе они пишутся независимо: канал уведомлений можно завести и на СЕГОДНЯШНИХ редиректах (свести пять написаний кода в один `?notice=`) ещё до появления первого `hx-post`. **Это даёт независимо проверяемую ценность на шаге 2 и снижает риск шага 4.** |
| **3 (загрузка) — параллельна 1-2** | Единственный поток, не касающийся ни `app/pages/`, ни оболочки: живёт в `app/routes/uploads.py` + `ads/form.html`, целится в `#media-strip` (существует), даёт минус ~70 строк JS. Может идти отдельным исполнителем с первого дня. |
| **4 (пилот `account_groups`) — до всех остальных классов A** | Два обработчика, один шаблон-макрос, готовый `id="group-row-N"`, готовый `partial_cards`. Наименьшая поверхность, на которой контракт «фрагмент + OOB + notice + деградация + `hx-disabled-elt` + `hx-indicator` + `hx-push-url`» проверяется ЦЕЛИКОМ. Гейты (N11) пишутся здесь же — дальше они держат остальные 30. |
| **5a-5d — параллельны между собой** | Разные файлы, разные тесты, ноль общих правок после шага 4. `5b` (modal) стоит делать первым из четырёх: 1 правка ⇒ 16 мест, и она разгружает 5a/5c/5d. |
| **6 (QR) — после 1-4, но до 7** | Пять обработчиков над ЖИВОЙ сессией Telethon; окно между `qr-status` и `complete` требует продуктового решения (см. §4.2), а не механической правки. Требует готового `respond()` и отлаженных гейтов опроса. Не первым — цена ошибки высока; не последним — не блокирует авторизацию. |
| **7 (авторизация) — последняя** | (а) второй шелл `auth_base.html` — `#notice` туда не приходит, конвенция другая; (б) успех меняет cookie личности, `HX-Location` через AJAX-GET кросс-шелловый (`auth_base` → `base`); (в) сломанный вход блокирует ВЕСЬ ручной UAT остальных фаз. Ставить его после того, как всё остальное подтверждено вручную. |

### ⚠️ Названный риск шага 7: `HX-Location` через границу шеллов

`HX-Location` выполняет AJAX-GET и свопает результат в `body` документа. Пять
успешных путей авторизации ведут из документа на `auth_base.html` в документ на
`base.html`. Оба шелла подключают ОДИН и тот же `app.css` и те же два скрипта
(`auth_base.html:23-25` ≡ `base.html:24-26`), поэтому оформление переживает;
не переживает `<title>` и `<meta>`-конфиг htmx, который останется от исходного
документа. Дешёвая и честная альтернатива для этих пяти путей — `HX-Redirect`
(полная навигация): выигрыш вехи заявлен **в ОШИБКЕ** («неверный код перестаёт
терять заполненную форму»), а не в успехе, и на успехе полная перезагрузка
ничего не отнимает. **Рекомендация: `HX-Redirect` для 5 путей, пересекающих
границу шеллов; `HX-Location` — для `/impersonation/stop`, который остаётся
внутри `base.html`.**

### Машинные гейты, которые стоит завести и расширить

`tests/test_templates/test_components.py` — готовая форма для этого: он читает
ИСХОДНИК всех 79 шаблонов через `_all_templates()` (856) и утверждает
инвентари ЯВНЫМИ числами (`ROW_DELETE_PLACES = 12`, `MODAL_PLACES = 16`,
`MODAL_EVENT_NAMES`), так что молчаливое исчезновение или появление места краснеет.
Веха обязана дать своим инвариантам ту же форму.

**Расширить существующие:**

| Гейт | Как расширяется |
|---|---|
| `test_every_row_delete_site_keeps_a_real_form` (994) | `_delete_forms_in()` уже вытаскивает форму целиком и проверяет `method="post"` + `action`. **Добавить третье утверждение: у формы есть и `hx-post`, и он СОВПАДАЕТ с `action`.** Это ровно та проверка, которая делает «htmx только перехватывает» свойством исходника, а не намерения |
| `test_modal_guard_is_inherited_by_every_consumer` (1128) | Гард повторной отправки приходит из макроса. **Добавить: `hx-disabled-elt` приходит оттуда же** — иначе 16 потребителей понесут 16 копий |
| `test_modal_site_inventory` (1179) | Форма счёта тремя способами переносится дословно на новый инвентарь `hx-post` |

**Завести новые (`tests/test_templates/test_htmx_contract.py`):**

| Гейт | Что утверждает | Почему это НЕ ловится обычным тестом |
|---|---|---|
| `test_every_form_keeps_method_and_action` | обход всех 79 шаблонов: у каждого `<form>` с `hx-post` есть `method="post"` и непустой `action` | деградация ломается МОЛЧА — страница остаётся 200, кнопка просто перестаёт работать без JS |
| `test_hx_post_matches_action` | `hx-post` == `action` посимвольно | расхождение шлёт запись по ДРУГОМУ адресу только на htmx-пути |
| `test_hx_target_points_at_an_existing_id` | каждый `hx-target="#…"` находит источник этого `id` хотя бы в одном шаблоне | опечатка в `hx-target` даёт свопы «в никуда» без единой ошибки |
| `test_every_oob_block_carries_an_id` | у каждого `hx-swap-oob` есть `id` | OOB без `id` htmx тихо игнорирует |
| `test_notice_region_is_declared_once` | `id="notice"` встречается ровно в `base.html` и нигде больше | две области с одним `id` — свопается первая, вторая мертва |
| `test_notice_codes_are_closed` | каждый `?notice=<code>` в `app/pages/*.py` есть ключ `NOTICES` | код без текста = молчаливое отсутствие обратной связи на базовом пути |
| `test_write_handlers_go_through_respond` | обход исходников `app/pages/*.py`: каждый обработчик под `@router.post` содержит `respond(` (либо стоит в явном перечне исключений с обоснованием) | **самый важный.** Именно он не даёт 36 копиям разъехаться, и он — точная копия приёма `tests/test_pages/test_access_gate.py`, который читает `app/pages/__init__.py` |
| `test_polling_fragments_declare_their_stop` | каждый фрагмент с `hx-trigger="every "` имеет парный фрагмент БЕЗ него | прямое обобщение `test_sync_polling_stops` / `test_account_groups_polling_stops` на новый QR-мастер |
| `test_no_manual_fetch_remains` | `fetch(` в `app/templates/` — 0 вхождений | закрывает цель вехи «снятие всех 6 ручных `fetch()`» так же, как гейт грепом закрыл возврат имён счётной модели |

Последний — прямой аналог уже применённого в проекте приёма: возврат имён
снятой счётной модели закрыт греп-гейтом, выводящим множество файлов обходом
каталога. Форма проверена, её надо переиспользовать, а не изобретать.

---

## Anti-Patterns

### AP-1. Перерисовывать контейнер списка вместо строки

**Что делают:** отдают `partial_cards.html` целиком и свопают в `#list`.
**Почему неверно здесь:** теряется позиция скролла бесконечной прокрутки
(`hx-trigger="revealed"`, 4 раздела) и гасятся раскрытые карточки расписаний
(состояние `sched` — СЕРВЕРНОЕ, живёт параметром адреса). Это ровно то, что
решение вехи запрещает прямым текстом.
**Вместо:** `hx-target` на `#<section>-row-{id}`, побочные области — OOB.

### AP-2. Отдавать htmx-ответ ДРУГИМ обработчиком, чем базовый путь

**Что делают:** заводят `/x/fragment` рядом с `/x`.
**Почему неверно здесь:** в проекте уже записано прямым текстом
(`_save_from_editor`, докстринг): «ветвление — по наличию заголовка htmx, а не
по отдельным маршрутам: базовый путь D-09 обязан быть ТЕМ ЖЕ кодом, иначе он
тихо разойдётся с улучшенным». Два маршрута = две копии проверок владения,
CSRF-гарда и запретов имперсонации.
**Вместо:** один маршрут, ветвление на выходах через `respond()`.

### AP-3. Класть текст сообщения в адрес редиректа

**Что делают:** `?msg=Группа+включена`.
**Почему неверно здесь:** правило уже действует в трёх местах проекта с
выписанным обоснованием; текст в адресе — вход для подстановки чужого
сообщения на своей странице.
**Вместо:** код из закрытого `NOTICES`.

### AP-4. Отдавать `TemplateResponse` полной страницы в ответ на `hx-post`

**Что делают:** оставляют `templates.TemplateResponse("profile.html", …)` как есть.
**Почему неверно здесь:** htmx свопнет ВЕСЬ документ (включая сайдбар, шапку и
второй `#notice`) внутрь `hx-target`. Особенно опасно на пути
`require_access` → 302 → `/billing`: внутри `#row-42` окажется целая страница
подписки. Симптом — визуальная поломка, а не ошибка.
**Вместо:** фрагмент; для гейтов — `HX-Redirect` при `HX-Request`.

### AP-5. Полагаться на `hidden`-блоки и `showSection()` в мастерах

**Что делают:** переносят QR-мастер «как есть», добавив `hx-post`.
**Почему неверно здесь:** четыре блока с `hidden` держат состояние в DOM и в
переменной JS одновременно; фрагментный ответ обязан знать, какие ещё блоки
погасить. У проекта уже есть образец без этого — WhatsApp-мастер с одним якорем.
**Вместо:** один якорь `#tg-connect`, пять взаимоисключающих фрагментов.

### AP-6. Считать, что `4xx` доедет до пользователя

**Что делают:** возвращают `HTTPException(400)` и ждут, что плашка появится.
**Почему неверно здесь:** htmx по умолчанию 4xx не свопает; OOB-уведомление
внутри такого ответа не применяется вовсе. Затрагивает 5 действующих гардов
`is_same_origin` (`Response(403)`) и `profile.py:82`.
**Вместо:** `responseHandling` для 422 + глобальный `htmx:responseError`,
который рисует в `#notice` то, чего сервер отдать не смог.

---

## Integration Points

### Внутренние границы (изменяемые вехой)

| Граница | Сегодня | После | Риск |
|---|---|---|---|
| `app/pages/*` ↔ браузер | 302 + query-код | 302 ИЛИ фрагмент/`HX-Location` | 160 тестовых утверждений |
| `app/pages/*` ↔ `app/templates/*` | `TemplateResponse` полной страницы | + `render_macro()` фрагмента | новый способ рендера, свой гейт |
| `app/routes/uploads.py` ↔ `ads/form.html` | JSON + ручной DOM | фрагмент + OOB (JSON сохраняется) | 14 тестов `tests/test_routes/` |
| `accounts.py` ↔ `connect_tg_user.html` | 5 JSON-эндпоинтов + 152 строки JS | 5 фрагментов + 0 JS | живая Telethon-сессия |
| `load_shell_context` ↔ OOB-счётчики | шелл читается ДО обработчика | требуется перечитывание после коммита | протухшие счётчики |
| `require_access` / `is_same_origin` ↔ htmx | 302 / 403 | `HX-Redirect` / свопаемый отказ | молчаливые отказы |

### Границы, которые веха НЕ трогает (подтверждено)

| Граница | Почему устойчива |
|---|---|
| `is_same_origin` (CSRF) | читает `Sec-Fetch-Site` / `Origin`; XHR htmx шлёт оба на POST — правило продолжает действовать без правок |
| `require_access` пер-роутерно + `test_access_gate.py` | гейт читает `app/pages/__init__.py`; новый модуль `htmx.py` роутеров не добавляет |
| Alpine (14 шаблонов с `x-data`) | вне объёма; `modal.html` продолжает открываться событием, htmx лишь перехватывает отправку его формы |
| Протоколы отправки TG/WA/MAX | вне объёма с v2.0 |
| Инвентарные гейты `MODAL_*`, `ROW_DELETE_*`, `THUMB_*` | расширяются, не заменяются |
| Вендоринг без build-шага (D-02) | htmx 2.x — один файл замены + бамп `asset_version`; сборка не вводится |

---

## Sources

**Первичные — исходный код репозитория (HIGH):**
- `app/pages/ads.py` (`_save_from_editor` 413-531, `_autosave_response` 386-411, `ads_create` 557-624)
- `app/pages/schedules.py` (`_editor_redirect` 214, `_editor_error_redirect` 321, `schedules_partial` 420, toggle/delete 731-807)
- `app/pages/accounts.py` (`_connect_status` 47-50, QR-поток 215-347, WA-мастер 350-475, `accounts_sync_status` 668-700)
- `app/pages/account_groups.py` (299-377), `app/pages/profile.py` (полностью), `app/pages/billing.py` (137, 278-400), `app/pages/history.py` (867-960), `app/pages/admin.py` (1789-1877), `app/pages/auth.py` (109-160, 227-300, 806)
- `app/pages/__init__.py` (`load_shell_context` 27-45, `require_access` 50-108, сборка роутеров 123-150), `app/pages/common.py` (`get_shell_context` 640-745, `is_same_origin` 542+)
- `app/routes/uploads.py` (191-319)
- `app/templates/base.html`, `auth_base.html`, `components/alert.html`, `components/modal.html`, `components/filters.html`, `ads/form.html`, `ads/includes/autosave_response.html`, `accounts/partials/connect_status.html`, `accounts/partials/sync_status_card.html`, `accounts/connect_wa.html`, `accounts/connect_tg_user.html`, `account_groups/partial_cards.html`, `schedules/partial_cards.html`, все `*/includes/*_row.html` и `*_card.html`
- `tests/test_templates/test_components.py` (`_all_templates` 856, `ROW_DELETE_SITES` 739-755, `MODAL_CONSUMERS` 1085-1120, `test_modal_site_inventory` 1179)
- `tests/test_pages/test_htmx_preserved.py` (`test_sync_polling_stops` 254, `test_account_groups_polling_stops` 303)
- `tests/test_pages/test_access_gate.py`, `pyproject.toml`, `uv.lock`

**Счёты, снятые командами (HIGH, воспроизводимо):**
`36` POST-декораторов · `127` `RedirectResponse` · `47` `<form>` в `27` файлах ·
`79` `hx-*` в `22` шаблонах (`25 hx-swap / 24 hx-trigger / 22 hx-get / 5 hx-swap-oob / 2 hx-post / 1 hx-sync`) ·
`4` `HX-*` в Python (все в `ads.py`) · `6` `fetch(` в `2` шаблонах ·
`160` `status_code == 302` в тестах · `14` шаблонов с `x-data` · `79` шаблонов · `134` тестовых файла

**Внешние (HIGH — официальные):**
- htmx 1.x → 2.x Migration Guide — https://htmx.org/migration-guide-htmx-1/
- `bigskysoftware/htmx` v2.0.4, `www/content/docs.md` — `responseHandling`, `hx-swap-oob`, `htmx:beforeSwap`, `HX-Location` / `HX-Reswap`
- `bigskysoftware/htmx` `src/htmx.js` — жизненный цикл событий (`htmx:responseError` 4969, `htmx:afterSwap` 1982)

---
*Architecture research for: v2.1 «HTMX-first» — интеграция слоя письма на htmx в действующую FastAPI + Jinja2 систему*
*Researched: 2026-08-26*
