# Phase 12: Загрузка изображений без `fetch()` — Research

**Researched:** 2026-09-18
**Domain:** htmx 2.0.10 multipart-фрагмент, перенос маршрута между двумя поверхностями FastAPI, снятие клиентского состояния под живыми машинными гейтами
**Confidence:** HIGH (почти всё измерено чтением исходников этого дерева; четыре вопроса §Open Questions РЕШЕНЫ — три владельцем 2026-09-18, четвёртый планированием)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (владелец):** **Обработчик загрузки переезжает из `app/routes/` в `app/pages/`.**
  Основание не в аккуратности раскладки, а в том, что критерий 3 закрывается СУЩЕСТВУЮЩИМ
  кодом: `app/pages/__init__.py:143` уже вешает `Depends(require_access)` на `ads_router`,
  а провал этой зависимости едет типом `HtmxRefusal` → `app/main.py:219` → 204 + `HX-Location`
  (Фаза 8, FOUND-07). Маршрут, заведённый внутри `ads_router`, получает «отказ доступа виден
  пользователю, а не молчит» **не написав ни строки гейта**. Оставшись в `app/routes/`, он не
  дотянулся бы: `respond()` и `HtmxRefusal` живут в `app/pages/htmx.py`, а 13 разметочных гейтов
  Фазы 8 обходят `app/pages/` и этого маршрута не увидели бы вовсе.
  **Цена названа:** `uploads_router` уходит из `GATED_API_ROUTERS` и `BLOCK_CHECKED_API_ROUTERS`
  (`test_access_gate.py:89,144`) — оба перечня правятся, и именно это имеет в виду критерий 3
  словами «отражено в ОБОИХ гейтах перечня»; адрес маршрута меняется; форма отказа перестаёт
  быть JSON.
  Отвергнуто: остаться в `app/routes/` и отдавать оттуда HTML — D-07 Фазы 11 прямо назвал
  `app/routes/` «другим транспортом», и заведение там HTML-выхода сделало бы эту границу
  бессмысленной ровно в тот момент, когда на неё ещё опираются Фазы 13-15.
  — **Reversibility:** costly.

- **D-02 (владелец):** **Маршрут привязан к ПОЛЬЗОВАТЕЛЮ, не к черновику** — адрес вида
  `/ads/images`, без `ad_id`. Ключ объекта остаётся прежней формы `{user_id}/{uuid4hex}_{имя}`.
  Владение ключом по-прежнему проверяется при СОХРАНЕНИИ объявления (`own_image_keys`,
  Фаза 2 / CR-01), и этот рубеж фаза не двигает.

- **D-03 (владелец):** **`app/routes/uploads.py` снимается ЦЕЛИКОМ; его логика переезжает в
  `app/services/`.** `sniff_image`, `safe_filename`, `retarget_extension`, порционное чтение,
  тексты `UNSUPPORTED_IMAGE_MESSAGE` / `OVERSIZED_IMAGE_MESSAGE` и — обязательно — их
  комментарии-обоснования переносятся **дословно**. Страничный обработчик держит **только
  транспорт**: разбор составного запроса, вызов сервиса, сборка фрагмента.
  Отвергнуто: переименовать файл в `app/pages/uploads.py` как есть.
  — **Reversibility:** costly.

- **D-04 (владелец):** **Загрузка ВСЕГДА отвечает 200 с фрагментом** — и когда принято всё, и
  когда принято частью, и когда не принято ничего. Основание: `htmx_error_banner.html` поднимает
  ОБЩУЮ плашку на любой код, кроме 422, и свопа при этом нет; 422 несёт правило `swap: false`
  с Фазы 7. **Цена названа прямо:** когда отвергнуты ВСЕ файлы, 200 говорит неправду.
  Отвергнуто: 422 когда не принято ничего и 200 когда принят хоть один.

- **D-05 (владелец):** **Отвергнутый файл получает СВОЮ строку со своей причиной.**
  **Обязательное свойство:** имя отвергнутого файла `safe_filename()` НЕ проходило — это сырой
  ввод отправителя, и перед показом его надлежит провести через ту же нормализацию. Одного
  автоэкранирования Jinja2 мало.

- **D-06 (владелец):** **Потолок: сервер берёт первые свободные, остальным отказывает.**
  Это ДОСЛОВНО сегодняшнее поведение `uploadFile()` (`form.html:523`).
  Отвергнуто: отказать партии целиком.

- **D-07 (по умолчанию):** **Форма загрузки включает текущие ключи (`hx-include`), сервер считает
  потолок сам и рисует полосу ЦЕЛИКОМ** — цель `#media-strip`, своп `innerHTML` (идиома D-12
  Фазы 9). Фрагмент несёт и плитки, и скрытые поля `name="images"` с атрибутом `form="ad-form"`,
  и плитку «+ФАЙЛ». Отдельный `#image-inputs` исчезает.
  **Обязательное свойство:** каждый присланный клиентом ключ сверяется на принадлежность
  пользователю ДО того, как попадёт во фрагмент — `own_image_keys(values, user_id, max_images)`.
  Второго инструмента не заводить.
  Отвергнуто: рисовать только новые плитки свопом `beforeend`.

- **D-08 (по умолчанию):** **Текст отказа живёт ВНУТРИ фрагмента `#media-strip`; область
  `#upload-error` снимается.** Одна цель свопа вместо цели плюс OOB-цели — ловушка G-11 Фазы 9
  не заводится.

- **D-09 (владелец):** **Прикрепление файла без JavaScript остаётся НЕВОЗМОЖНЫМ и объявляется
  ИМЕНОВАННЫМ изъятием.** ⚠️ htmx отправляет поля формы ПО ИМЕНИ, поэтому файловое поле `name`
  ПОЛУЧИТ. Изъятие держится тем, что у формы загрузки **не заводится кнопка отправки**.
  Отвергнуто: заставить работать; через форму объявления.

- **D-10 (владелец):** **Перехват кнопки «×» снимается; удаление вложения становится
  htmx-отправкой `#ad-form`.** Снимается ровно слушатель `remove.addEventListener('click', …)`.
  **Цена названа:** удаление перестаёт быть мгновенным.
  Отвергнуто: свой `hx-post` вложения.

- **D-11 (по умолчанию):** **Порог счётчика текста читается из РАЗМЕТКИ, а не из переменной** —
  источником становится число плиток в `#media-strip`.

- **D-12 (по умолчанию):** **Мёртвое снимается СРАЗУ и вместе с тем, что его держало.**
  Уходят из `form.html`: `imagePaths`, `renderImages()`, `uploadFile()`, `handleFiles()`,
  `refusalTextOf()`, `removeImage()`, `fileNameOf()`, слушатель `change` на `#file-input`,
  константы `UPLOAD_TYPE_ERROR`, `UPLOAD_LIMIT_ERROR`, `UPLOAD_TRANSPORT_ERROR`.
  Три следствия: тест step с `UPLOAD_TYPE_ERROR` снимается ВМЕСТЕ с копией;
  `UPLOAD_TRANSPORT_ERROR` растворяется в плашке `htmx:sendError`;
  `IMAGE_BASE_URL` и `THUMB_KEY_PREFIX` — **планировщик обязан ПРОВЕРИТЬ читателей**.

- **D-13 (по умолчанию):** **Фаза двигает инвентарные числа ЯВНО**, одним коммитом с работой:
  `fetch(` в `app/templates/` 6 → 1; `GATED_API_ROUTERS` 5 → 4; `BLOCK_CHECKED_API_ROUTERS` 5 → 4;
  модулей в `app/routes/` минус один файл. Число «~70 строк JS минус» снимается ПО ФАКТУ.

- **D-14 (по умолчанию):** **Долг R-08-02 к этой фазе не относится — он целиком адресован Фазе 13.**

### Claude's Discretion

Владелец оставил на усмотрение планировщика, отметив области как решённые по умолчанию:
D-07 (механика включения ключей и сверка принадлежности), D-08 (место текста отказа),
D-11 (источник порога счётчика), D-12 (состав снимаемого и судьба трёх держателей),
D-13 (форма учёта инвентарных чисел), D-14 (адресация чужого долга).

Свободно и не решено ни здесь, ни ROADMAP-ом: точное написание адреса маршрута внутри
`app/ads/`-пространства; имя файлового поля; имя и расположение шаблона фрагмента; на какой
именно элемент вешается `hx-indicator` и как он выглядит; разбиение работы на планы и волны.

### Deferred Ideas (OUT OF SCOPE)

- **Проценты загрузки** — `UPLD-01`, отложен в v2.2 (требует `htmx:xhr:progress`).
- **Пять `fetch(` QR-мастера Telegram** — Фаза 13 (FETCH-02).
- **Утверждение «`fetch(` в `app/templates/` равно 0»** — Фаза 15 (FETCH-03).
- **Четыре `onclick`/`onsubmit` в экранах подключения** (R-08-02) — Фаза 13, см. D-14.
- **Reviewed Todos (not folded):** `full-suite-ads-editor-order-pollution.md` (нестабильный
  `test_image_base_url_comes_from_app_settings`); `blocked-user-can-still-log-in.md` (Фаза 14).

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FETCH-01 | загрузка изображения объявления идёт htmx-фрагментом вместо `fetch()` + JSON; успешно загруженные файлы остаются прикреплёнными, даже если часть отвалилась | §Architecture Patterns (P-1 форма запроса, P-2 форма ответа при частичном успехе), §Don't Hand-Roll (`own_image_keys`, `form_wrapper`, `thumb()`), §Common Pitfalls (G-1 потолок nginx, G-4 G-11, G-5 автосохранение), §Code Examples |

</phase_requirements>

## Summary

Фаза не изобретает механизма — весь он уже лежит в дереве и **измерен чтением исходников**:
вендоренный htmx 2.0.10 шлёт все файлы одного `<input type="file" multiple>` **одним** составным
запросом при наличии `hx-encoding="multipart/form-data"` (или `enctype` на теге формы), связывает
кнопку и поле с формой через DOM-свойство `element.form` — то есть **атрибут `form="ad-form"`
работает и для скрытых полей, и для кнопки отправки**, — а конфигурация `responseHandling`
проекта на любой 4xx/5xx свопа не делает вовсе. Значит D-04 («всегда 200») не обходной манёвр,
а единственная форма ответа, при которой человек читает причину.

Настоящий риск фазы лежит **не в htmx, а в трёх местах, которых `12-CONTEXT.md` не называет**.
Первое: `client_max_body_size 20M` в боевом nginx при потолке `10 файлов × 5 МБ = 50 МБ` — партия
крупных снимков получает 413 ДО приложения, то есть теряются и те файлы, которые прошли бы,
и критерий 2 нарушается снаружи кода. Второе: снятие `renderImages()` уносит из `ads/form.html`
весь `createElement`/`replaceChildren`, на которых стои́т **зелёный сегодня** гейт безопасности
`test_ads_form_uses_property_assignment` (CR-01), а `IMAGE_BASE_URL` служит опознавательным
маркером экрана в `test_hx_location_destinations.py:56` — оба покраснеют молча. Третье: после
снятия `handleFiles()` исчезает вызов `requestSave()`, и удачная загрузка перестаёт создавать
черновик — сегодняшнее поведение, о котором решения молчат.

Четвёртое, более тонкое: D-10 переводит удаление на отправку `#ad-form`, но эта форма несёт
`hx-swap="none"`, и плитка сама с экрана не уйдёт — ответ автосохранения обязан получить
внеполосный блок полосы. А как только `#media-strip` становится и целью свопа (D-07), и
внеполосной целью, срабатывает **ровно та ловушка G-11**, которую D-08 объявил закрытой.
Нужны два идентификатора, а не один.

**Primary recommendation:** завести **новую форму загрузки соседом `#ad-form`** через
расширенный `components/form_wrapper.html` (новые параметры `encoding`, `include`, `enctype`),
целью `hx-target="#media-strip"` со свопом `innerHTML`, **вынеся разметку полосы в отдельный
включаемый файл** `ads/includes/media_strip.html` — этим и снимается сток CR-01 из `form.html`,
и появляется единый источник разметки для трёх отрисовщиков (страница, ответ загрузки, ответ
автосохранения). Обработчик — в `app/pages/ads.py` (внутри `ads_router`), через `respond()`,
с `await request.form(max_files=…, max_fields=…)`; вся не-транспортная логика — в новом
`app/services/image_upload.py` рядом с `images.py` и `image_keys.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Выбор файлов и составление запроса | Browser / htmx runtime | — | `hx-encoding` + `FormData`; своего JS не пишется (рамка вехи) |
| Признак «запрос идёт» | Browser / CSS | — | класс `htmx-request`, правило `.form-busy.htmx-request` уже в `app.css` |
| Распознавание типа по содержимому | Frontend Server (`app/services/`) | — | CR-02: заголовок клиента авторитетом не является НИКОГДА |
| Предел размера тела | CDN / Reverse proxy (nginx) | Frontend Server | `client_max_body_size` режет ДО приложения; приложение — второй рубеж |
| Предел числа частей запроса | Frontend Server (Starlette) | — | `request.form(max_files=…)`; иначе потолок только у файлов, не у частей |
| Сжатие и миниатюра | Frontend Server (`asyncio.to_thread`) | — | счётная работа, один uvicorn-воркер (issue #40) |
| Сверка владения ключом | Frontend Server (`app/services/image_keys.py`) | — | `own_image_keys`, один источник на оба слоя (WR-04) |
| Потолок числа вложений | Frontend Server | — | D-06/D-07: клиент потолка больше не знает |
| Хранение объектов | Storage (S3) | — | форма ключа не меняется, миграции нет |
| Состояние «какие ключи прикреплены» | Browser DOM (скрытые поля) | Database при сохранении | ровно та мена, ради которой фаза существует (D-11) |
| Гейт доступа | Frontend Server (`ads_router`) | — | D-01: `require_access` уже висит на роутере |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| htmx (вендоренный) | 2.0.10 | составной запрос, своп фрагмента, индикатор | уже в дереве, `app/static/js/htmx.min.js`; веха получает **0 новых зависимостей** (REQUIREMENTS §Out of Scope) [VERIFIED: app/templates/includes/htmx_config.html:167] |
| FastAPI | 0.129.0 | маршрут страничного слоя | измерено в venv проекта [VERIFIED: `uv run python -c "import fastapi"`] |
| Starlette | 0.52.1 | разбор составного запроса (`request.form`) | измерено в venv проекта [VERIFIED] |
| Pillow (через `app/services/images.py`) | — | `prepare_upload` | уже используется, фаза его не трогает |
| pytest / pytest-asyncio | 9.0.2 / ≥1.3.0 | суита | [VERIFIED: pyproject.toml:39-41] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| — | — | — | **Новых пакетов фаза не добавляет ни одного.** Это рамка вехи, а не наблюдение |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| один батч-запрос | расширение `htmx-ext-multi-swap`/`response-targets` | запрещено рамкой вехи: «в htmx 2.x расширения — отдельные пакеты», новый вендоренный файл [CITED: .planning/REQUIREMENTS.md:111] |
| `hx-indicator` | `htmx:xhr:progress` с процентами | `UPLD-01` отложен в v2.2 решением вехи [CITED: .planning/REQUIREMENTS.md:91] |
| фрагмент из Jinja | `jinja2-fragments` | запрещено рамкой вехи [CITED: .planning/REQUIREMENTS.md:105] |

**Installation:** не требуется — новых зависимостей нет.

## Package Legitimacy Audit

**Фаза не устанавливает ни одного внешнего пакета** — секция применима вакуумно.
Проверка `gsd-tools query package-legitimacy check` не запускалась, потому что проверять нечего;
это не пропуск шага, а отсутствие предмета. Все используемые библиотеки уже стоят в
`pyproject.toml` и в вендоренных артефактах дерева.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
[человек выбирает N файлов в #file-input]
            │  change (bubbles)  ← htmx-триггер формы загрузки
            ▼
┌─────────────────────────────────────────────────────────────┐
│ <form> ЗАГРУЗКИ — СОСЕД #ad-form, не вложен                 │
│   hx-post = action  (GATE-04, посимвольно)                  │
│   hx-encoding="multipart/form-data" + enctype=то же         │
│   hx-include="#media-strip input[name='images']"  ← D-07    │
│   hx-target="#media-strip"  hx-swap="innerHTML"             │
│   hx-indicator="find .form-busy"   ← критерий 4             │
│   БЕЗ кнопки отправки            ← D-09 (изъятие)           │
└─────────────────────────────────────────────────────────────┘
            │  ОДИН multipart-запрос: N файлов + K текущих ключей
            ▼
   [nginx]  client_max_body_size  ◄── ⚠️ G-1: 20M против 50M потолка
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│ app/pages/ads.py  (внутри ads_router)                       │
│   Depends(require_access) — УЖЕ ВИСИТ (D-01, критерий 3)    │
│   ├─ await request.form(max_files=…, max_fields=…)          │
│   ├─ own_image_keys(присланные ключи, user.id, max_images)  │  ← D-07, владение
│   ├─ free = max_images - len(ключи)                          │  ← D-06, потолок
│   └─ для каждого файла ПО ПОРЯДКУ:                           │
│        free>0 ?  service.accept(file)  :  отказ «не больше K»│
└─────────────────────────────────────────────────────────────┘
            │            │
            │            ▼
            │   ┌──────────────────────────────────────────┐
            │   │ app/services/image_upload.py  (D-03)     │
            │   │  порционное чтение → предел размера      │  ← порядок
            │   │  sniff_image → предел типа               │     СОХРАНЁН
            │   │  prepare_upload (asyncio.to_thread)      │     (uploads.py:212 vs :230)
            │   │  safe_filename → retarget_extension      │
            │   │  upload_file_to_s3 (объект, затем thumb) │
            │   └──────────────────────────────────────────┘
            │            │ принят ключ  /  отвергнут (причина + СЫРОЕ имя)
            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│ respond(request, redirect=<адрес редактора>, fragment=…)    │
│   без htmx → 302 (путь деградации, FOUND-04)                │
│   с htmx   → 200 + ads/includes/media_strip.html            │  ← D-04: ВСЕГДА 200
│               плитки + hidden name=images form="ad-form"     │
│               + плитка «+ФАЙЛ» + строки отказа (D-05/D-08)   │
└─────────────────────────────────────────────────────────────┘
            │ innerHTML в постоянную обёртку #media-strip
            ▼
[DOM — и есть состояние: скрытые поля едут со следующим сохранением #ad-form]
```

### Recommended Project Structure

```
app/
├── pages/
│   └── ads.py                       # + обработчик загрузки (ТОЛЬКО транспорт)
├── services/
│   ├── images.py                    # существует: prepare_upload, MAX_DECODED_PIXELS
│   ├── image_keys.py                # существует: thumb_key, own_image_keys
│   └── image_upload.py              # НОВЫЙ: всё, что переезжает из routes/uploads.py (D-03)
├── routes/
│   └── uploads.py                   # СНИМАЕТСЯ ЦЕЛИКОМ (D-03)
└── templates/
    ├── components/
    │   └── form_wrapper.html        # + параметры encoding / include (см. P-3)
    └── ads/
        ├── form.html                # блок вложений заменяется одной строкой include
        └── includes/
            ├── media_strip.html     # НОВЫЙ: единственный источник разметки полосы
            └── autosave_response.html # + внеполосный блок полосы (D-10, см. P-5)
tests/
├── test_routes/test_uploads.py      # 1099 строк — ПЕРЕЕЗЖАЮТ, а не удаляются (см. G-8)
└── test_templates/test_ads_form_security.py # 5 гейтов — теряют предмет (см. G-2)
```

### Pattern 1: Один запрос вместо N — механика, а не надежда

**What:** `<input type="file" multiple>` внутри формы с `hx-encoding="multipart/form-data"`
даёт **один** POST со **всеми** выбранными файлами под **одним** именем поля.

**When to use:** всегда для этого маршрута — это и есть предмет решения «один запрос вместо N».

**Почему это так — измерено в вендоренном артефакте, а не выведено из документации:**

```js
// Source: app/static/js/htmx.min.js (вендоренный htmx 2.0.10) — условие составного запроса
function vn(e){return ne(e,"hx-encoding")==="multipart/form-data"
                 ||h(e,"form")&&ee(e,"enctype")==="multipart/form-data"}
```
[VERIFIED: app/static/js/htmx.min.js]

```js
// Source: app/static/js/htmx.min.js — сбор значений формы
if(e instanceof HTMLFormElement){
  ie(e.elements,function(e){ ... });
  new FormData(e).forEach(function(e,t){
      if(e instanceof File&&e.name===""){return}   // ПУСТОЕ файловое поле не даёт части
      ln(t,e,n)                                     // ln = ДОБАВИТЬ (массив значений)
  })
}
```
[VERIFIED: app/static/js/htmx.min.js]

Три следствия, и каждое важно планировщику:
1. `new FormData(form)` берёт **все** выбранные файлы одного поля → один запрос, N частей
   под одним именем. На сервере это `form_data.getlist("<имя поля>")`.
2. Пустое файловое поле части **не даёт** — фантомной пустой части на сервере не появится.
3. `e.elements` — это `HTMLFormElement.elements`, а он по спецификации HTML **включает
   элементы, связанные атрибутом `form="…"` и лежащие вне тега формы**. Отсюда: скрытые поля
   ключей с `form="ad-form"` уедут со следующей отправкой `#ad-form` — буква критерия 1
   работает механически. [VERIFIED: app/static/js/htmx.min.js + существующая кнопка
   `form.html:319`, которая уже так устроена и работает в бою]

**Подтверждение из официальной документации:**
`hx-encoding` меняет кодирование запроса с `application/x-www-form-urlencoded` на
`multipart/form-data`, «primarily for supporting file uploads in AJAX requests», значение
наследуется от родителей. [CITED: github.com/bigskysoftware/htmx/blob/v2.0.4/www/content/attributes/hx-encoding.md]

### Pattern 2: Форма ответа при частичном успехе — «состояние + перечень отказов»

**What:** ответ **всегда** 200 и **всегда** один и тот же шаблон: полоса, отрисованная из
ИТОГОВОГО множества ключей, плюс ноль или больше строк отказа.

**When to use:** все три исхода — принято всё, принято частью, не принято ничего.

**Почему 200, а не 207/422 — тиски измерены:**

```html
<!-- Source: app/templates/includes/htmx_config.html:159-165 -->
"responseHandling": [
    {"code":"204", "swap": false},
    {"code":"[23]..", "swap": true},
    {"code":"422", "swap": true, "error": true},
    {"code":"[45]..", "swap": false, "error": true},
    {"code":"...", "swap": false}
]
```
[VERIFIED: app/templates/includes/htmx_config.html:159-165]

```js
// Source: app/templates/includes/htmx_error_banner.html — исключение ровно одно
document.body.addEventListener('htmx:responseError', function (event) {
    if (event.detail && event.detail.xhr && event.detail.xhr.status === 422) { return; }
    ... server.removeAttribute('hidden');   // «Действие не выполнено. Попробуйте ещё раз…»
});
```
[VERIFIED: app/templates/includes/htmx_error_banner.html]

То есть: **любой** код 4xx/5xx кроме 422 = общая плашка + **ноль свопа**; 422 = своп есть, но
правило `{"code":"[45].."}`-соседа с `swap: false` не применяется, а сам 422 у htmx помечен
`error: true` — плашка гасится только специальным исключением выше. D-04 выбран верно.

**Форма структуры результата, которую отдаёт сервис (рекомендуется):**

```python
@dataclass(frozen=True)
class Accepted:
    key: str                     # {user_id}/{uuid4hex}_{имя}

@dataclass(frozen=True)
class Rejected:
    display_name: str            # safe_filename(сырое имя) — ОБЯЗАТЕЛЬНО (D-05)
    reason: str                  # из закрытого набора констант, не строка по месту
```
Обработчик собирает `list[Accepted | Rejected]` в порядке присланных частей; шаблон рисует
плитки из `итоговые_ключи` и `<p>` на каждый `Rejected`.

### Pattern 3: Расширение `form_wrapper`, а не вторая форма отправки

**What:** добавить макросу `components/form_wrapper.html` параметры `encoding` и `include`.

**Почему обязательно через макрос:** гейт `test_every_htmx_post_is_born_of_a_component_macro`
требует, чтобы каждый `hx-post` рождался компонентным макросом; исключений объявлено ровно
одно (`MACRO_BORN_EXCEPTIONS_DECLARED = 1`, и это сам `ads/form.html`).
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:3654,4586]
Вторая выгода — `HX_POST_PLACES` **не двигается**: разборщик считает ФАЙЛЫ, печатающие атрибут,
а не места вызова. [VERIFIED: tests/test_templates/test_htmx_markup_gates.py:107-140,
«Место здесь ОДНО независимо от числа вызывающих»]
Третья — `hx-disabled-elt` и `hx-indicator="find .form-busy"` приезжают даром, то есть критерий 4
закрывается **существующим** механизмом, ровно по линии §Specifics контекста.

**Текущее определение макроса, в которое врезается правка:**

```jinja
{# Source: app/templates/components/form_wrapper.html:162-172 #}
{% macro form_wrapper(action, target=None, swap=None, trigger=None,
                      disabled_elt='find button[type=submit]', sync=None) -%}
<form method="post" action="{{ action }}" hx-post="{{ action }}" class="form-wrapper"
      {%- if target %} hx-target="{{ target }}" hx-swap="{{ swap or 'outerHTML' }}"
      {%- else %} hx-swap="none"{% endif %}
      {%- if trigger %} hx-trigger="{{ trigger }}"{% endif %}
      {%- if sync %} hx-sync="{{ sync }}"{% endif %}
      {%- if disabled_elt %} hx-disabled-elt="{{ disabled_elt }}"{% endif %} hx-indicator="find .form-busy">
  {%- if caller is defined %}{{ caller() }}{% endif %}
  <span class="form-busy" aria-hidden="true"></span>
</form>
{%- endmacro %}
```
[VERIFIED: app/templates/components/form_wrapper.html:162-172]

⚠️ **Три жёстких ограничения самого макроса, названные в его шапке и обязательные к соблюдению
при правке** [VERIFIED: app/templates/components/form_wrapper.html:24-83]:
* `method="post"` — **литерал в двойных кавычках**, не параметр (гейт читает ТЕКСТ шаблона);
* `action` и `hx-post` печатают **одно и то же выражение** `{{ action }}` посимвольно;
* **внутри тега нет ни одного символа `>`** — разборщик границ тега обрывается на первом;
* `hx-indicator` **стои́т сразу после адреса запроса** — «место это не свободное».

**Вызов для формы загрузки (иллюстрация формы, не финальная разметка):**

```jinja
{% call form_wrapper(action='/ads/images',
                     target='#media-strip',
                     swap='innerHTML',
                     trigger='change',
                     encoding=true,
                     include="#media-strip input[name='images']",
                     disabled_elt='') %}
  <input class="field__input" type="file" id="file-input" name="files"
         accept="image/jpeg,image/png" multiple hidden>
{% endcall %}
```
`disabled_elt=''` — потому что кнопки отправки у формы нет (D-09), а объявленная и недостижимая
цель блокировки пишет строку в консоль **на каждый запрос** и ломает опорный признак обхода
«ответ 200 и чистая консоль». Ветвь пустого значения для этого и заведена планом 09-10, но
вызывающий, передавший своё значение, **обязан быть объявлен поимённо** в
`DISABLED_ELT_EXCEPTIONS` (сегодня `= 2`).
[VERIFIED: app/templates/components/form_wrapper.html:98-121; tests/test_templates/test_htmx_markup_gates.py:3568]

### Pattern 4: Полоса — один шаблон, три отрисовщика

**What:** разметка `#media-strip` живёт в `ads/includes/media_strip.html` и включается
(а) страницей редактора, (б) ответом загрузки, (в) внеполосным блоком ответа автосохранения.

**When to use:** обязательно. Это действующая идиома проекта — ровно так сделана линейка
счётчика расписаний (`sched_count_rule.html` включается и страницей, и внеполосным узлом),
и у неё есть собственный гейт единственности источника
(`test_the_schedule_counter_markup_has_exactly_one_source`).
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:5474; app/templates/ads/form.html:220-223]

**Вторая, не менее важная причина — безопасность:** вынос разметки из `ads/form.html`
одновременно уводит из этого файла строку `innerHTML`, которую иначе пришлось бы там напечатать
(см. G-2 ниже).

### Pattern 5: Два идентификатора, потому что цель свопа и внеполосная цель — разные роли

**What:** постоянная обёртка `#media-strip` (цель `hx-target` формы загрузки, своп `innerHTML`)
и **внутренний** узел с собственным `id` для внеполосной подмены из ответа автосохранения.

**Почему:** см. §Common Pitfalls G-4. Правило G-11 сличает **строки идентификаторов**, а
`_swap_target_ids` собирает **только литеральные `#…`**.
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:5274-5298 и комментарий :2055-2064]

### Anti-Patterns to Avoid

- **Класть файлы в поле `images`.** Обработчик сохранения ОТВЕРГАЕТ файловые части в `images`
  отказом, а не отбрасыванием — и это осознанно (WR-03). Имя файлового поля обязано быть другим.
  [VERIFIED: app/pages/ads.py:524-540]
- **Считать потолок вторым инструментом.** `own_image_keys` уже считает и владение, и потолок;
  два места, считающие потолок, разойдутся (Hyrum).
- **Доверять `Content-Type` присланной части при разборе партии.** CR-02 не смягчается переездом:
  тип определяется по первым байтам, и точка. [VERIFIED: app/routes/uploads.py:32-51]
- **Переставлять отказ по размеру ниже распознавания типа.** Сегодня размер стои́т ВЫШЕ типа
  (`uploads.py:212` против `:230`), и следствие наблюдаемо: тело, которое и превышает предел, и
  не является изображением, получает отказ по размеру. Порядок сохранить при разборе каждой части.
  [VERIFIED: app/routes/uploads.py:204-234]
- **Писать `innerHTML` внутри `ads/form.html`** в любом виде, включая `hx-swap`. См. G-2.
- **Выводить «без JS не работает» из отсутствия `name`.** Его там больше не будет (D-09).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Владение ключом + потолок | свою проверку префикса/лимита | `own_image_keys(values, user_id, max_images)` (`app/services/image_keys.py:83`) | образец без якорей + `fullmatch`, строковое сравнение префикса (`007/…` ≠ `7/…`), запрет ключа миниатюры — всё уже выстрадано (WR-01, T-10-04, T-Q40-04) [VERIFIED: app/services/image_keys.py:25-33,108-119] |
| Откат миниатюры на полноразмерный адрес | `img.onerror` в JS | макрос `thumb()` (`components/thumb.html:30-35`) | уже несёт `data-full` и снятие обработчика с самого себя — защиту от бесконечного цикла [VERIFIED: app/templates/components/thumb.html:23-34] |
| Признак «запрос идёт» | свой класс/таймер | `hx-indicator="find .form-busy"` + `.form-busy.htmx-request` в `app.css:2193-2208` | QUAL-02: один класс и один макрос на все формы вехи; порог видимости через `transition-delay` уже настроен [VERIFIED: app/static/css/app.css:2193-2214] |
| Отказ доступа видимым | свой гейт на маршруте | `Depends(require_access)` на `ads_router` → `HtmxRefusal` → 204 + `HX-Location` | D-01: **ни строки нового гейта** [VERIFIED: app/pages/__init__.py:117-124,143; app/main.py:224-231] |
| Сообщение об обрыве сети | `UPLOAD_TRANSPORT_ERROR` | плашка `htmx:sendError` | она уже стои́т на `document.body` и гасится на успехе [VERIFIED: app/templates/includes/htmx_error_banner.html] |
| Сжатие, миниатюра, предел точек | свой конвейер | `prepare_upload` (`app/services/images.py:223`) | одна распаковка / два кодирования, предел ДО распаковки, снятие EXIF — контракт записан в докстринге [VERIFIED: app/services/images.py:223-245] |
| Двойная отправка формы | своё «уже идёт» | `hx-disabled-elt` / `hx-sync` из `form_wrapper` | QUAL-01/PAY-02 |
| Свойства качества формы | писать атрибуты руками | `form_wrapper` | FORM-09: ревью 47 форм заменено ревью одного файла |

**Key insight:** линия, проходящая через ВСЕ решения фазы, — «предпочесть существующий механизм
новому». Всё, что фаза обязана написать своими руками, — это (1) транспортный обработчик,
(2) шаблон полосы, (3) перенос логики в сервис **дословно**. Любая четвёртая новая сущность
есть сигнал, что решение читается неверно.

## Runtime State Inventory

Фаза — перенос/рефакторинг, поэтому инвентарь обязателен.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | **Ничего не мигрирует.** Форма ключа объекта S3 (`{user_id}/{32 hex}_{имя}`) и форма `Ad.images` не меняются ни на символ (D-02, D-03). Уже сохранённые объекты не переписываются. | нет |
| **Live service config** | **`nginx/nginx.conf.template:59` — `client_max_body_size 20M`**, глобально в блоке `listen 443 ssl`. Файл В ГИТЕ, но применяется перезапуском/переразвёртыванием nginx, а не выкладкой кода. **`nginx/nginx-http.conf.template` — `client_max_body_size` ОТСУТСТВУЕТ вовсе** (значит действует умолчание nginx). [VERIFIED: nginx/nginx.conf.template:59; отсутствие — nginx/nginx-http.conf.template, ноль совпадений в файле] | **правка конфига + переразвёртывание nginx** — см. G-1 |
| **OS-registered state** | Ни Task Scheduler, ни pm2, ни systemd этого маршрута не знают. Celery-задачи (`app/worker/`) вложений не загружают. | нет |
| **Secrets / env vars** | `MAX_IMAGE_SIZE_MB` и `MAX_IMAGES_PER_AD` — поля `Settings` с умолчаниями `5` и `10` (`app/config.py:43-44`). Имена НЕ меняются; маршрут читает те же значения. [VERIFIED: app/config.py:43-44] | нет (но значения участвуют в расчёте G-1) |
| **Build artifacts** | Вендоренный `htmx.min.js` не заменяется, значит `asset_version` не двигается. Питон-пакет проекта не переустанавливается. | нет |
| **Документация вне кода** | `README.md:325` — строка таблицы API `POST /api/uploads/image`. После D-01/D-02 адрес перестаёт существовать. [VERIFIED: README.md:325] | правка README одним коммитом с работой |

**Канонический вопрос — ответ:** после правки каждого файла репозитория **единственная**
рантайм-система, всё ещё настроенная на прежнее поведение, — это **nginx с 20-мегабайтным
потолком тела**, рассчитанным на запросы «один файл за раз». Ничего другого нет.

## Common Pitfalls

### G-1 (BLOCKER): nginx режет партию ДО приложения — 20 МБ против потолка в 50 МБ

**What goes wrong:** пользователь выбирает 10 снимков с телефона по 4–5 МБ. Сегодня это
10 независимых запросов по ≤5 МБ — каждый проходит. После фазы это **один** запрос ~45 МБ;
nginx отвечает **413 Request Entity Too Large**, запрос до FastAPI не доезжает вовсе.

**Why it happens:** `client_max_body_size 20M;` стои́т глобально в HTTPS-блоке, а потолок
приложения — `max_images_per_ad (10) × max_image_size_mb (5) = 50 МБ`.
[VERIFIED: nginx/nginx.conf.template:59; app/config.py:43-44]

**Почему это ломает именно критерий 2:** 413 — это 4xx, а `responseHandling` даёт на 4xx
`swap: false` — своп не происходит, плашка поднимается общая («Действие не выполнено»), и
**все** файлы теряются, включая те, что прошли бы поодиночке. То есть «успешно загруженные
остаются прикреплёнными» нарушается **снаружи кода**, и ни один серверный тест этого не увидит.

**How to avoid:** поднять `client_max_body_size` до значения, выводимого из настроек
(`max_images_per_ad × max_image_size_mb` + запас на границы и текстовые части), **в обоих**
шаблонах nginx, и записать связь прозой рядом со значением. Второй рубеж — `request.form(...)`
с явными пределами (см. G-3).

**Warning signs:** 413 в `prod-logs nginx`; общая плашка при крупной партии и пустой лог приложения.

⚠️ **Проверить отдельно:** `nginx-http.conf.template` не объявляет предел **вовсе**. Утверждать,
какое значение при этом действует, я не стану — это вывод из ОТСУТСТВИЯ директивы, и он тут
`[ASSUMED]`. Планировщику надлежит задать предел явно в обоих файлах, а не выяснять умолчание.

### G-2 (BLOCKER): снятие `renderImages()` роняет **зелёный сегодня** гейт безопасности CR-01

**What goes wrong:** D-12 снимает `renderImages()`, `showUploadError()`, `clearUploadError()`.
Вместе с ними из `ads/form.html` исчезает **весь** `createElement` и **весь** `replaceChildren`.

```python
# Source: tests/test_templates/test_ads_form_security.py:60-66
def test_ads_form_uses_property_assignment():
    """Предпросмотр собирается узлами и заполняется присваиванием свойств."""
    body = form_source()

    assert body.count("createElement") >= 3, body.count("createElement")
    assert "textContent" in body
    assert body.count("replaceChildren") >= 2, body.count("replaceChildren")
```
[VERIFIED: tests/test_templates/test_ads_form_security.py:60-66]

**Измерено на сегодняшнем дереве:** `createElement` — 4 вхождения в `renderImages()` (:438, :441,
:450, :465) и 1 в `showUploadError()` (:491); `replaceChildren` — 2 в `renderImages()` (:432, :433)
и 2 в `showUploadError`/`clearUploadError` (:495, :499). **Все семь уходят.** Остаётся только
`textContent` на счётчике (:424). Баланс: `createElement` 5 → 0, `replaceChildren` 4 → 0.
[VERIFIED: app/templates/ads/form.html:432-499]

**Предпосылка теста фактически неверна:** докстринг говорит «предпросмотр собирается узлами», но
предпросмотр — это Jinja-включение `ads/includes/preview.html` (`form.html:306`), а скриптовый
блок в файле **один** (`form.html:344-578`). Тест меряет **клиентскую сборку плиток**, то есть
ровно то, что фаза удаляет.

**How to avoid:** тест **снимается вместе со своим предметом**, ровно по идиоме D-12 («мёртвое
снимается вместе с тем, что его держало»), и замещается **более сильным** утверждением:
`createElement == 0` и `replaceChildren == 0` в `ads/form.html` — клиентской сборки разметки в
редакторе больше нет вовсе. Ослаблением это не является: `test_ads_form_builds_dom_not_markup`
(ноль стоков разметки) **остаётся на месте и усиливается**.

⚠️ **Второе следствие того же файла:** `test_ads_form_builds_dom_not_markup` падает, если строка
`innerHTML` появится **в тексте** `ads/form.html` — а `hx-swap="innerHTML"` (D-07) её туда и
принесёт.
```python
# Source: tests/test_templates/test_ads_form_security.py:49,52-57
MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")
def test_ads_form_builds_dom_not_markup():
    body = form_source()
    offenders = [sink for sink in MARKUP_SINKS if sink in body]
    assert not offenders, offenders
```
[VERIFIED: tests/test_templates/test_ads_form_security.py:49-57]
**Решение:** разметка формы загрузки и полосы уходит в `ads/includes/media_strip.html` (Pattern 4),
и `ads/form.html` слова `innerHTML` не содержит — гейт остаётся строгим и зелёным.

⚠️ **Третье следствие:** `test_ads_form_hidden_input_contract_kept` требует подстрок `"images"`
и `"hidden"` **в `ads/form.html`**. После выноса полосы `name="images"` уедет в include.
Подстрока `hidden` останется (`<input type="hidden" id="ad-id-field">`, `form.html:140`), а
`images` — **под вопросом**: планировщик обязан проверить на готовой правке и либо перенацелить
тест на новый файл, либо снять его вместе с предметом. [VERIFIED: tests/test_templates/test_ads_form_security.py:83-88]

**Baseline:** `uv run pytest tests/test_templates/test_ads_form_security.py -q -p no:randomly`
→ `5 passed` на сегодняшнем дереве. Покраснение после правки — своё, а не унаследованное.

### G-3 (HIGH): партия снимает потолок с числа частей запроса

**What goes wrong:** сегодня форма запроса — «ровно одна файловая часть». После фазы форма —
«сколько пришлёт клиент». Злоумышленник (или сломанный клиент) шлёт 1000 частей.

**Why it happens:** Starlette ограничивает **непустые текстовые** части, а файловые — нет:

```python
# Source: starlette/formparsers.py (starlette 0.52.1, venv проекта)
class MultiPartParser:
    spool_max_size = 1024 * 1024  # 1MB
    max_part_size = 1024 * 1024   # 1MB
    def __init__(self, ..., max_files=1000, max_fields=1000, max_part_size=1024*1024): ...
    def on_part_data(self, data, start, end):
        message_bytes = data[start:end]
        if self._current_part.file is None:          # ← ТОЛЬКО НЕ-ФАЙЛОВАЯ ЧАСТЬ
            if len(self._current_part.data) + len(message_bytes) > self.max_part_size:
                raise MultiPartException(f"Part exceeded maximum size of ...KB.")
            self._current_part.data.extend(message_bytes)
        else:
            self._file_parts_to_write.append((self._current_part, message_bytes))  # ← БЕЗ ПРЕДЕЛА
```
[VERIFIED: inspect.getsource(starlette.formparsers) в venv проекта, starlette 0.52.1]

Сигнатура `Request.form` — `(*, max_files: int|float = 1000, max_fields: int|float = 1000,
max_part_size: int = 1048576)`. [VERIFIED: `inspect.signature(Request.form)`, starlette 0.52.1]

**How to avoid:** страничный обработчик уже разбирает форму сам (`await request.form()` в
`_save_from_editor`, `app/pages/ads.py:521`), значит пределы передаются **явно**:
`await request.form(max_files=<потолок вложений + небольшой запас>, max_fields=<небольшое число>)`.
Это не педантизм: `max_part_size` умолчанием **1 МБ** к файлам НЕ применяется, и второго рубежа
у приложения нет.

⚠️ **Заодно проверить обратное:** `max_part_size = 1 МБ` применяется к **текстовым** частям, и
`hx-include` присылает до 10 ключей по ~140 символов — с большим запасом проходит. Понижать
`max_part_size` не следует.

### G-4 (HIGH): D-10 и D-07 сталкиваются на ловушке G-11, и столкновение неочевидно

**What goes wrong:** D-10 переводит удаление вложения на отправку `#ad-form`. Но `#ad-form`
несёт `hx-swap="none"` — «форма НИКОГДА не перерисовывается» (`form.html:76`), и всё обновление
приезжает внеполосно из `ads/includes/autosave_response.html`. Этот ответ подменяет
`#ad-preview`, `#ad-summary`, `#autosave-indicator` и `#ad-id-field` — **полосы вложений среди
них нет**. Значит после нажатия «×» плитка **останется на экране**, хотя из БД ключ ушёл.
[VERIFIED: app/templates/ads/form.html:70-76; app/templates/ads/includes/autosave_response.html]

**Следующий шаг ловушки:** чтобы плитка исчезла, `autosave_response.html` обязан получить
внеполосный блок полосы. Но полоса — это `#media-strip`, а он по D-07 становится **целью
`hx-target`** формы загрузки. Один и тот же идентификатор в двух ролях роняет G-11:

```python
# Source: tests/test_templates/test_htmx_markup_gates.py:5274-5297
def test_no_id_is_both_a_swap_target_and_an_oob_target() -> None:
    """G-11: идентификатор не бывает целью подмены и внеполосной целью разом."""
    conflicts = _offenders_id_in_two_roles(_all_templates())
    assert not conflicts, (...)
```
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:5274-5297]

**How to avoid:** Pattern 5 — **два идентификатора**. Постоянная обёртка `#media-strip` служит
целью `hx-target` формы загрузки (своп `innerHTML`), а внутренний узел с собственным `id`
служит внеполосной целью ответа автосохранения; оба включают **один и тот же** шаблон
`ads/includes/media_strip.html` (Pattern 4). D-08 остаётся выполненным: текст отказа лежит
внутри цели свопа, второй OOB-цели под него не заводится.

**Инвентарные числа, которые это движет** (D-13 требует явности):
`OOB_BLOCKS = 19` → 20 (один новый внеполосный блок).
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:2219]

### G-5 (HIGH): удачная загрузка перестаёт создавать черновик

**What goes wrong:** сегодня `handleFiles()` после удачной загрузки зовёт `requestSave()`, а тот
поднимает `change` на `#ad-form` — то есть на `/ads/new` первая же загруженная картинка **создаёт
черновик** и подменяет `#ad-id-field`. После снятия JS этого вызова не останется.

```js
// Source: app/templates/ads/form.html:478-482, 539-548
function requestSave() {
    adForm.dispatchEvent(new Event('change', { bubbles: true }));
}
async function handleFiles(files) { ... if (added) { requestSave(); } }
```
[VERIFIED: app/templates/ads/form.html:478-482,539-548]

**Why it happens:** форма загрузки — **сосед** `#ad-form`, а не его потомок (вложенные формы
браузер молча отбрасывает — `form.html:169-178`). Всплытие событий идёт по ДЕРЕВУ ДОКУМЕНТА, а
не по связи `form="…"`, поэтому `change` формы загрузки до `#ad-form` **не долетит**.
Скрытые поля с `form="ad-form"` при этом сериализуются правильно — но только когда `#ad-form`
отправится по **своей** причине (набор текста, «Сохранить», удаление вложения).

**Наблюдаемое следствие:** человек на `/ads/new` прикрепил картинку, не ввёл ни символа и обновил
страницу — картинка потеряна. Сегодня она сохранена. Это **смена поведения**, а рамка вехи
требует, чтобы существующее осталось работающим.

**How to avoid:** вариант, не заводящий нового JS, — ответ загрузки несёт заголовок
`HX-Trigger` с ASCII-именем события, а `#ad-form` дописывает его в свой `hx-trigger` формой
`<событие> from:body`. ⚠️ Два ограничения проекта здесь действуют и оба проверяемы:
GATE-07 требует, чтобы правый операнд `response.headers["HX-*"]` был литералом либо f-строкой с
целыми — ASCII-литерал это условие выполняет; а запрет `HX-Trigger` в §Out of Scope адресован
**тостам** (кириллица в latin-1), а не событиям.
[CITED: .planning/REQUIREMENTS.md:69,107]
**Это решение владельца, а не планировщика** — см. §Open Questions Q-1.

### G-6 (MEDIUM): `IMAGE_BASE_URL` — не только константа, но и опознавательный маркер экрана

**What goes wrong:** D-12 велит проверить читателей `IMAGE_BASE_URL`. Читателей в продакшене
действительно два, и оба в `renderImages()` (`form.html:435,436`) — то есть константа снимается.
Но у неё есть **третий** потребитель, в суите:

```python
# Source: tests/test_pages/test_hx_location_destinations.py:52-56
# ⚠️ ПРИЗНАК ПРИНАДЛЕЖНОСТИ ЭКРАНУ, А НЕ «ПЕРВЫЙ ПОПАВШИЙСЯ СКРИПТ». ...
# Имя выбрано потому, что оно объявлено ИМЕННО этим экраном и ни одним другим.
EDITOR_SCRIPT_MARKER = "IMAGE_BASE_URL"
```
Маркер используется в трёх местах (:174, :263, :281), и на :174 из него выводится множество, о
котором :177 утверждает «обязано быть ровно одно». Снятие константы делает множество **пустым** —
правило падает. [VERIFIED: tests/test_pages/test_hx_location_destinations.py:52-56,174-177,263,281]

**How to avoid:** выбрать новый маркер, объявленный **ровно этим экраном и ни одним другим**
(например, оставшуюся константу счётчика), и заменить значение `EDITOR_SCRIPT_MARKER` одним
коммитом со снятием `IMAGE_BASE_URL`. Правило при этом не ослабляется — меняется признак, а не
утверждение.

⚠️ **Спутник:** `THUMB_KEY_PREFIX` держится собственным тестом
`test_editor_javascript_carries_the_thumbnail_prefix` (`tests/test_pages/test_ads_editor.py:406-424`,
`assert THUMB_KEY_PREFIX in script`). Он теряет предмет вместе с копией и снимается по той же
логике, что и тест `UPLOAD_TYPE_ERROR` (D-12). [VERIFIED: tests/test_pages/test_ads_editor.py:406-424]

### G-7 (MEDIUM): гейт имперсонации — ТРЕТИЙ перечень, которого критерий 3 не называет

**What goes wrong:** D-01/D-13 называют два перечня (`GATED_API_ROUTERS` :89,
`BLOCK_CHECKED_API_ROUTERS` :144). Перечней **три**:

```python
# Source: tests/test_pages/test_impersonation_gate.py:218
    "app/routes/uploads.py::upload_image": "загрузка картинки объявления",
```
[VERIFIED: tests/test_pages/test_impersonation_gate.py:218]

Обход читает `ROUTE_DIRECTORIES = ("app/pages", "app/routes")` и требует, чтобы **каждое**
изменяющее объявление маршрута стояло либо в перечне запрещённого, либо в `ALLOWED_ROUTES` с
причиной. Маршрут, не попавший ни в одно множество, **роняет гейт** — это заявленное свойство
формы («Появись маршрут „отправить сейчас“ — он не попадёт ни в одно множество и уронит гейт,
что и требуется»). [VERIFIED: tests/test_pages/test_impersonation_gate.py:78-83,223-232]

**How to avoid:** ключ `"app/routes/uploads.py::upload_image"` заменяется на
`"app/pages/ads.py::<имя нового обработчика>"` с сохранением причины. Правка — часть D-13.

**Baseline:** `uv run pytest tests/test_pages/test_access_gate.py tests/test_pages/test_impersonation_gate.py -q -p no:randomly`
→ `35 passed` на сегодняшнем дереве.

### G-8 (MEDIUM): 1099 строк `tests/test_routes/test_uploads.py` переезжают, а не удаляются

**What goes wrong:** D-03 снимает `app/routes/uploads.py` целиком. У модуля есть тестовый файл
на **1099 строк**, который импортирует из него имена (:18-23) и подменяет `app.routes.uploads.upload_file_to_s3`
в **26 местах**, а адрес `/api/uploads/image` называет в ~25 запросах.
[VERIFIED: wc -l tests/test_routes/test_uploads.py = 1099; grep по файлу]
Второй импортёр — `tests/test_pages/test_ads_editor.py:33` (`from app.routes.uploads import
UNSUPPORTED_IMAGE_MESSAGE`), и он же на :198 утверждает `UNSUPPORTED_IMAGE_MESSAGE in html` —
то есть требует, чтобы серверная константа встречалась в отрендеренном редакторе. После D-12
второй копии в шаблоне нет, и это утверждение теряет предмет **вместе с копией**.
[VERIFIED: tests/test_pages/test_ads_editor.py:33,180-198]

**How to avoid:** запланировать перенос суиты **отдельной задачей**, а не «попутно»: пути патчей
`@patch("app.routes.uploads.upload_file_to_s3")` привязаны к имени модуля и молча превратятся в
`AttributeError`/`ModuleNotFoundError`, а не в осмысленный отказ. Утверждения о **сервисе**
(сигнатуры, тексты, порядок отказов) переезжают в `tests/test_services/`; утверждения о
**маршруте** (коды, фрагмент, владение) — в `tests/test_pages/`.

### G-9 (MEDIUM): счётная работа стала последовательной внутри одного запроса

**What goes wrong:** `prepare_upload` — одна распаковка и два кодирования на файл, вынесенные в
поток (`asyncio.to_thread`). Сегодня N файлов = N запросов, и событийный цикл чередует их.
После фазы N файлов = один запрос, и `to_thread` вызывается N раз **последовательно**: время
ответа складывается, а не накладывается.

**How to avoid:** (а) не держать тела всех N файлов в памяти одновременно — обрабатывать часть,
отдавать её байты сборщику мусора, переходить к следующей; (б) именно поэтому `hx-indicator`
(критерий 4) здесь не украшение, а необходимость; (в) параллелить `to_thread` **не следует** —
боевой артефакт держит ОДИН uvicorn-воркер, и параллельное декодирование десяти снимков отняло
бы цикл у `/health`, по которому принимается решение о живости контейнера.
[VERIFIED: app/routes/uploads.py:236-244 — обоснование выноса в поток]

### G-10 (LOW): нестабильный `test_image_base_url_comes_from_app_settings`

Известная нестабильность, заведённая в `.planning/todos/pending/full-suite-ads-editor-order-pollution.md`:
красный **только в полном прогоне**. Фаза трогает ровно ту константу, вокруг которой он крутится,
и может снять его предмет попутно — но целью это не ставится. **Проверять в одиночном прогоне
тоже**, иначе своё покраснение неотличимо от чужого.

### G-11-bis (LOW, но названо Фазой 9 адресно): два изъятия, назначенные ЭТОЙ фазе

Фаза 9 записала в сводной летописи своих чисел:

```python
# Source: tests/test_templates/test_htmx_markup_gates.py:186-190
#  6. DISABLED_ELT_EXCEPTIONS_DECLARED 0 → 2 (этот файл, план 09-01)
#     components/form_wrapper.html — вызывающий передаёт свой селектор (D-06);
#     ads/form.html — атрибута нет вовсе, место назначено Фазе 12 (FETCH-01).
#  7. MACRO_BORN_EXCEPTIONS_DECLARED 0 → 1 (этот файл, план 09-03)
#     ads/form.html — та же назначенная фаза, что и в записи 6, намеренно.
```
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:186-190]

То есть **дерево адресует этой фазе два изъятия, которых `12-CONTEXT.md` не называет**:
`#ad-form` сегодня не объявляет цели блокировки и не рождён компонентным макросом. Снятие обоих
означало бы перевод самой формы объявления на `form_wrapper` — работу, которой §Phase Boundary
контекста не предусматривает. **Решение принадлежит владельцу** — см. §Open Questions Q-3.
Минимум, который фаза обязана сделать, — **записать диспозицию**, а не промолчать: молчание
прочитается при сверке как «Фаза 12 забыла», ровно тот класс, против которого написан D-14.

## Code Examples

### Условие составного запроса и сбор файлов (вендоренный рантайм)

```js
// Source: app/static/js/htmx.min.js (htmx 2.0.10, вендоренный артефакт проекта)
function vn(e){return ne(e,"hx-encoding")==="multipart/form-data"
                 ||h(e,"form")&&ee(e,"enctype")==="multipart/form-data"}

function Nt(e){return e.form||g(e,"form")}   // ← связь по АТРИБУТУ form, затем по дереву
```
Второе — причина, по которой `<button type="submit" form="ad-form" name="remove_image">`,
лежащая ВНЕ формы, доезжает до сервера как нажатый отправитель: htmx сначала спрашивает
DOM-свойство `element.form`, которое атрибут `form="…"` и заполняет. Ровно на этом уже держится
кнопка «Сохранить» (`form.html:319`) — механизм обкатан в бою, а не предположен.

### Существующий скелет транспорта — `respond()` на обеих половинах

```python
# Source: app/pages/htmx.py:712-... (сигнатура и поведение)
async def respond(
    request: Request,
    *,
    redirect: str,                                     # ОБЯЗАТЕЛЕН (FOUND-04)
    notice: str | None = None,
    fragment: Callable[[], Awaitable[Response]] | None = None,
) -> Response:
    ...
    if not is_htmx(request):
        return RedirectResponse(url=_with_notice(redirect, notice), status_code=302)
    if fragment is None:
        return location_response(_with_notice(redirect, notice))
    _with_notice(redirect, notice)      # адрес проверяется ДАЖЕ на ветке фрагмента
    response = await fragment()
    ...
```
[VERIFIED: app/pages/htmx.py:712-... — тело функции прочитано целиком]

⚠️ Из этого следует важное для §Landmines: маршрут, зовущий `respond()`, **не попадает** в
`FRAGMENT_ROUTES` — это множество собирает маршруты, «у которых пути деградации НЕТ ВОВСЕ»
(комментарий :860-865). Значит `FRAGMENT_ROUTES_DECLARED = 11` **не двигается**, а гейт
`test_no_action_path_leads_to_a_fragment_route` для новой формы **выполнен по построению**.
[VERIFIED: tests/test_templates/test_htmx_markup_gates.py:860-895]

### Средство сверки владения и потолка — и его точная форма отказа

```python
# Source: app/services/image_keys.py:83-119
def own_image_keys(values: list[str], user_id: int, max_images: int) -> list[str]:
    if len(values) > max_images:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=(...))
    for value in values:
        match = _IMAGE_KEY_PATTERN.fullmatch(value)
        if match is None or match.group(1) != str(user_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=INACCESSIBLE_IMAGE_MESSAGE)
    return list(values)
```
[VERIFIED: app/services/image_keys.py:83-119]

⚠️ **Разница, которую D-07 стои́т прочесть внимательно, и это НЕ возражение решению.**
`own_image_keys` потолок **не отсекает, а отвергает** — поднимает `HTTPException(400)`, если
ключей больше `max_images`. Правило D-06 «сервер берёт первые свободные, остальным отказывает»
относится к **новым файлам**, а не к уже присланным ключам, и разделение ролей выходит чистым:
* `own_image_keys(присланные_ключи, user.id, max_images)` — **владение** уже прикреплённых.
  Их всегда ≤ потолка, потому что их же нарисовал сервер прошлым ответом; превышение означает
  подделанный запрос и честно отвергается.
* `free = max_images - len(проверенные_ключи)` — сколько **новых** файлов принимается. Этот
  расчёт `own_image_keys` не делает и делать не должен; он однострочный, второго инструмента
  не заводит и разойтись с первым не может, потому что читает его же результат.

⚠️ И второе: `HTTPException(400)` из `own_image_keys` в страничном слое **не должен доехать до
htmx** — на 4xx свопа нет (§Pattern 2), а D-04 велит отвечать 200. Ветку надлежит перехватить
в обработчике, как это уже сделано у сохранения (`_attachment_refusal`, `app/pages/ads.py:436-481`).
[VERIFIED: app/pages/ads.py:436-481,541-551]

### Постоянная обёртка + `innerHTML` — образец уже в дереве

```jinja
{# Source: app/templates/ads/form.html:220-223 — линейка счётчика расписаний #}
<div id="sched-count">
  {%- set schedules_count = editor.schedules_count %}
  {% include "ads/includes/sched_count_rule.html" %}
</div>
```
Тот же включаемый файл используется внеполосным узлом ответа удаления — «вторая копия
разошлась бы с первой молча, и человек видел бы РАЗНОЕ число». Полоса вложений устроена так же.
[VERIFIED: app/templates/ads/form.html:204-223]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `fetch()` + JSON `{path: key}` + клиентская сборка плиток | htmx-фрагмент, DOM как состояние | Фаза 12 (эта) | −~70 строк JS; состояние перестаёт жить в `imagePaths` |
| N запросов по одному файлу | один составной запрос на партию | Фаза 12 | потолок тела переезжает на nginx (G-1); отказ получает СВОЮ строку на файл (D-05) |
| `hx-*` расширение `response-targets` | `responseHandling` + точечный `HX-Retarget` | v2.1, FOUND-02 | в htmx 2.x расширения — отдельные пакеты, а веха получает 0 новых файлов [CITED: .planning/REQUIREMENTS.md:111] |
| `imghdr` из stdlib | своя проверка сигнатуры | до вехи | `imghdr` удалён из stdlib в Python 3.13; `python-magic` тянет `libmagic` в образ [VERIFIED: app/routes/uploads.py:38-39] |
| htmx 1.9.10 | htmx 2.0.10 (вендоренный) | Фаза 7, FOUND-01 | `responseHandling` появился в 2.x; в 1.x поведение задавалось `htmx:beforeSwap` |

**Deprecated/outdated:**
- `POST /api/uploads/image` — адрес исчезает (D-01/D-02). Внешних потребителей нет: единственный
  вызов — `app/templates/ads/form.html:527`. Документируется в `README.md:325` — правится.
- `#image-inputs` (`form.html:124`) — существовал ровно затем, чтобы `renderImages()` мог звать
  `imageInputs.replaceChildren()` отдельно от плиток. Со снятием функции теряет причину.
- `#upload-error` (`form.html:163`) — заменяется строками внутри фрагмента (D-08).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `nginx-http.conf.template` без директивы `client_max_body_size` действует по умолчанию nginx, а не наследует значение от HTTPS-шаблона | G-1 / Runtime State | Низкий для плана (рекомендация — задать предел ЯВНО в обоих файлах в любом случае), но **утверждать конкретное умолчание нельзя**: это вывод из отсутствия директивы |
| A2 | Событие `change` формы загрузки не долетит до `#ad-form`, потому что всплытие идёт по дереву документа, а форма загрузки — сосед, а не потомок | G-5 | Если неверно — G-5 не существует и вопрос Q-1 снимается. Проверяется одним прогоном в браузере на ветке |
| A3 | `HX-Trigger` с ASCII-именем события не нарушает запрет §Out of Scope (запрет адресован кириллическим ТОСТАМ) и проходит AST-правило GATE-07 | G-5 / Q-1 | Средний: если владелец читает запрет шире, вариант решения Q-1 отпадает и нужен другой |
| A4 | Подстрока `"images"` исчезнет из `ads/form.html` после выноса полосы в include | G-2 | Низкий: проверяется грепом на готовой правке; следствие — какой тест править |
| A5 | Множество читателей `IMAGE_BASE_URL` в продакшене исчерпывается двумя строками `renderImages()` | G-6 / D-12 | Низкий: измерено грепом по `app/` и `tests/`, но греп подтверждает вхождения, а не отсутствие непрямого чтения |
| A6 | Форма загрузки, переданная через `form_wrapper` с новыми параметрами, не сдвинет `HX_POST_PLACES` (=3) | Pattern 3 | Средний: логика комментария к константе однозначна, но число ставится **прогоном покрасневшего правила**, а не рассуждением — так требует летопись файла |

## Open Questions (RESOLVED)

⚠️ **Живых открытых вопросов в этом документе НЕТ.** Вопросы 1–3 разрешил **владелец проекта** в
ходе прогона `/gsd-plan-phase 12` **2026-09-18**; это РЕШЕНИЯ ВЛАДЕЛЬЦА, а не находки разведки, и
переоткрывать их планированию или исполнению нельзя. Вопрос 4 владельцу не задавался — он закрыт
выбором планирования из множества, которое разведка уже сузила до одного свойства. Отвергнутые
варианты оставлены в тексте НЕ как живая развилка, а как запись о том, ЧТО именно отвергнуто и КЕМ:
читателю, который возьмётся «упростить» решение, положено увидеть, что этот путь уже пройден и
закрыт.

1. **Как удачная загрузка снова начнёт создавать черновик (G-5)?** — **РЕШЕНО (владелец, 2026-09-18).**
   - Что известно: сегодня `handleFiles()` зовёт `requestSave()`, и это создаёт запись на
     `/ads/new`. После снятия JS вызова не остаётся; форма загрузки — сосед, не потомок.
   - **Ответ владельца: семейство `HX-Trigger` плюс слушатель `hx-trigger="<событие> from:body"`
     на `#ad-form`.** Сегодняшнее наблюдаемое поведение — «черновик создаёт ПЕРВАЯ загруженная
     картинка» — СОХРАНЯЕТСЯ. Нового JavaScript — ноль строк.
   - **ОТВЕРГНУТО ВЛАДЕЛЬЦЕМ:** «сознательное принятие смены поведения: черновик создаётся первым
     набранным символом, а не первой картинкой». Вариант не живой; цена его не платится.
   - **Уточнение планирования ВНУТРИ выбранного механизма (не смена решения):** заголовок сужен до
     `HX-Trigger-After-Swap`, и основание — порядок свопа, а не вкус. Обычный `HX-Trigger` поднимает
     событие ДО подмены, то есть форма объявления сериализовалась бы в момент, когда новых скрытых
     полей в документе ещё нет, и первое же автосохранение сохранило бы объявление БЕЗ только что
     загруженной картинки — ровно та потеря работы, ради предотвращения которой механизм и
     заводится. Заголовок ставится, только когда принят хотя бы ОДИН файл.
   - Оба ограничения, названные в G-5, соблюдены: значение — ASCII-литерал (GATE-07), а запрет
     §Out of Scope адресован кириллическим ТОСТАМ, а не именам событий (A3).
   - Записано планом: `12-04`, задача 2 (`HX_HEADER_WRITES` 3 → 4).

2. **Каким становится `client_max_body_size` и где записывается его связь с настройками (G-1)?** —
   **РЕШЕНО (владелец, 2026-09-18).**
   - Что известно: `20M` в HTTPS-шаблоне при потолке `10 × 5 = 50 МБ`; в HTTP-шаблоне директивы
     нет вовсе.
   - **Ответ владельца: поднять `client_max_body_size` до `64M` в ОБОИХ шаблонах** — в
     `nginx/nginx.conf.template` значение `20M` заменяется, в `nginx/nginx-http.conf.template`
     директива заводится ВПЕРВЫЕ, — **И записать формулу `max_images_per_ad` × `max_image_size_mb`
     прозой рядом со значением**, чтобы читатель, поднявший потолок вложений, видел, что делать с
     прокси.
   - **ОТВЕРГНУТО ВЛАДЕЛЬЦЕМ:** «сузить потолок партии — принимать не более K файлов за раз при
     неизменном `max_images_per_ad`». Потолок приложения этой фазой НЕ сужается: это была бы
     вторая смена поведения сверх тех, что фаза уже несёт.
   - Записано планом: `12-02`, обе задачи (машинная сверка формулы с `Settings()` —
     `tests/test_nginx_body_limit.py`).

3. **Что делать с двумя изъятиями, которые Фаза 9 адресовала Фазе 12 (G-11-bis)?** —
   **РЕШЕНО (владелец, 2026-09-18).**
   - Что известно: `DISABLED_ELT_EXCEPTIONS` и `MACRO_BORN_EXCEPTIONS` содержат `ads/form.html`
     с пометкой «место назначено Фазе 12 (FETCH-01)».
   - **Ответ владельца: ПЕРЕАДРЕСОВАТЬ ЗАПИСЬЮ**, ровно так, как D-14 переадресовал R-08-02.
     Назначенной фазой становится более поздняя фаза сводного обхода форм — план `12-05`
     записывает **Фазу 15**.
   - **ОТВЕРГНУТО ВЛАДЕЛЬЦЕМ:** «снимать их», то есть переводить сам `#ad-form` на `form_wrapper`
     внутри этой фазы. Основание отказа — граница фазы: перевод задевает `hx-trigger`, `hx-sync` и
     `hx-swap="none"`, то есть свойства, ради которых форма и написана руками.
   - ⚠️ Переадресация — ЗАПИСЬ, а не снятие: молчание при сверке прочиталось бы как «Фаза 12
     забыла», ровно тот класс, против которого написан D-14.
   - Записано планом: `12-05`, задача 2.

4. **Имя файлового поля.** — **ЗАКРЫТО планированием** (владельцу не задавалось: разведка уже
   свела вопрос к одному свойству — «лишь бы не `images`»).
   - Что известно: `images` **запрещено** — обработчик сохранения отвергает файловые части под
     этим именем осознанно (WR-03).
   - **Выбрано: `files`.** Единственное объявление имени — `UPLOAD_FILE_FIELD` в
     `app/services/image_upload.py`; разметка печатает его значением из контекста шаблона, а не
     литералом, поэтому второй копии имени в дереве не появляется.
   - Записано планом: `12-01`, обе задачи.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | всё | ✓ | 3.12.13 | — |
| pytest | суита | ✓ | 9.0.2 | — |
| FastAPI | маршрут | ✓ | 0.129.0 | — |
| Starlette | `request.form(max_files=…)` | ✓ | 0.52.1 | — |
| htmx (вендоренный) | фрагмент, `hx-encoding` | ✓ | 2.0.10 | — |
| `uv` | запуск | ✓ | используется всеми рецептами `justfile` | — |
| nginx | предел тела запроса | ✗ (не в среде разработки) | — | конфиг правится в шаблонах `nginx/*.template`; проверка предела — **только на боевом стенде**, машинного теста у неё нет |
| Браузер для UAT | критерий 4 (`hx-indicator`) | ✗ | — | ручной обход, как в Фазах 9–11 |

**Missing dependencies with no fallback:**
- Нет. Всё, что нужно для машинной половины, стоит в venv проекта.

**Missing dependencies with fallback:**
- nginx и браузер — предмет ручного UAT, а не сборки. Критерий 4 роадмапом объявлен ручным;
  предел тела (G-1) объявляется **проверкой боевого стенда** и обязан попасть в UAT-обход
  отдельным пунктом, иначе он останется незакрытым дефектом с зелёной суитой.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio ≥1.3.0 [VERIFIED: pyproject.toml:39-41] |
| Config file | `pyproject.toml` (секция зависимостей); фикстуры — `tests/conftest.py` |
| Quick run command | `uv run pytest <файл> -q -p no:randomly` |
| Full suite command | `uv run pytest tests/ -q` (рецепт `just test`) |

⚠️ `-p no:randomly` применяется целенаправленно: известна нестабильность порядка исполнения
(`.planning/todos/pending/full-suite-ads-editor-order-pollution.md`), и фаза трогает ровно ту
область. Проверять **и** в одиночном, **и** в полном прогоне (см. G-10).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-01 | `fetch(` в `app/templates/` равно 1 (D-13) | unit (инвентарь) | `uv run pytest tests/test_pages/test_shell.py -q -k "no_manual_fetch"` | ✅ (GATE-08 `test_no_manual_fetch_remains`) |
| FETCH-01 | партия из N файлов даёт ОДИН запрос и N результатов | integration | `uv run pytest tests/test_pages/test_ads_image_upload.py -q` | ❌ Wave 0 |
| FETCH-01 | **частичный успех**: 1 годный + 1 негодный → годный прикреплён, негодный назван | integration | `uv run pytest tests/test_pages/test_ads_image_upload.py -q -k partial` | ❌ Wave 0 |
| FETCH-01 | потолок: K свободных мест, N>K файлов → первые K приняты, остальные с причиной (D-06) | integration | `… -k ceiling` | ❌ Wave 0 |
| FETCH-01 | ВСЕ исходы отвечают **200** (D-04), включая «отвергнуто всё» | integration | `… -k always_200` | ❌ Wave 0 |
| FETCH-01 | чужой ключ в `hx-include` не переиздаётся во фрагмент (D-07) | integration | `… -k foreign_key` | ❌ Wave 0 |
| FETCH-01 | имя отвергнутого файла нормализовано `safe_filename` (D-05) | unit | `uv run pytest tests/test_services/test_image_upload.py -q -k rejected_name` | ❌ Wave 0 |
| FETCH-01 | порядок отказов: размер ВЫШЕ типа (перенос дословный) | unit | `… -k oversized_beats_unsupported` | ❌ Wave 0 |
| FETCH-01 | скрытые поля фрагмента несут `form="ad-form"` | unit (разметка) | `uv run pytest tests/test_pages/test_ads_editor.py -q -k form_attribute` | ❌ Wave 0 |
| FETCH-01 | без htmx маршрут отвечает 302 (FOUND-04/GATE-01) | integration | пара `htmx_client` / `authed_client` | ❌ Wave 0 |
| FETCH-01 (кр. 3) | `uploads_router` вышел из ОБОИХ перечней; новый маршрут в `ALLOWED_ROUTES` | unit (гейт) | `uv run pytest tests/test_pages/test_access_gate.py tests/test_pages/test_impersonation_gate.py -q -p no:randomly` | ✅ существует (35 passed) |
| FETCH-01 (кр. 1) | клиентская сборка плиток в редакторе равна нулю | unit (гейт) | `uv run pytest tests/test_templates/test_ads_form_security.py -q` | ✅ существует (5 passed), **утверждение инвертируется** — см. G-2 |
| FETCH-01 | разметочные гейты вехи зелены на новой форме | unit (гейт) | `uv run pytest tests/test_templates/test_htmx_markup_gates.py -q -p no:randomly` | ✅ существует |

### Sampling Rate

- **Per task commit:** `uv run pytest <затронутый файл> -q -p no:randomly`
- **Per wave merge:** `uv run pytest tests/test_pages/ tests/test_templates/ tests/test_services/ -q`
- **Phase gate:** `uv run pytest tests/ -q` зелёная **до** `/gsd-verify-work`; и отдельно —
  повторный прогон затронутых файлов **в одиночку** (G-10).

### Wave 0 Gaps

- [ ] `tests/test_pages/test_ads_image_upload.py` — новый файл: маршрут, партия, частичный успех,
      потолок, «всегда 200», чужой ключ, пара без-htmx/с-htmx (покрывает FETCH-01)
- [ ] `tests/test_services/test_image_upload.py` — новый файл: перенос утверждений о `sniff_image`,
      `safe_filename`, `retarget_extension`, порядке отказов из `tests/test_routes/test_uploads.py`
- [ ] Судьба `tests/test_routes/test_uploads.py` (1099 строк) — **решить явно**: переезд по двум
      адресам выше, а не удаление (G-8)
- [ ] Инверсия `test_ads_form_uses_property_assignment` (G-2) и снятие
      `test_editor_upload_handler_reads_the_refusal_from_the_response_body` (D-12)
- [ ] Замена `EDITOR_SCRIPT_MARKER` в `tests/test_pages/test_hx_location_destinations.py:56` (G-6)
- [ ] Снятие `test_editor_javascript_carries_the_thumbnail_prefix` (G-6)
- [ ] Правка `tests/test_pages/test_ads_editor.py:33,198` — импорт из снятого модуля (G-8)
- [ ] Инвентарные числа D-13 + `OOB_BLOCKS` (G-4) — ставятся **прогоном покрасневшего правила**,
      а не вычитанием в уме (дисциплина летописи `test_htmx_markup_gates.py`)

*(Фреймворк ставить не нужно — суита существует, ~1700 тестов.)*

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1`. [VERIFIED: .planning/config.json]

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | да | `get_user_from_cookie` на страничном слое; маршрут — внутри `ads_router` |
| V3 Session Management | нет | фаза сессий не трогает |
| V4 Access Control | **да** | `Depends(require_access)` на `ads_router` (D-01) + `own_image_keys` как рубеж владения ключом (D-07); гейт имперсонации (G-7) |
| V5 Input Validation | **да** | тип по содержимому (`sniff_image`, CR-02), нормализация имени (`safe_filename`), приведение расширения (`retarget_extension`), предел точек (`MAX_DECODED_PIXELS`) |
| V6 Cryptography | нет | ничего не шифруется и не подписывается |
| V12 File Upload | **да (ядро фазы)** | предел размера тела (nginx + порционное чтение), предел ЧИСЛА частей (`request.form(max_files=…)`), закрытый список форматов, `Content-Type` сохранённого объекта из ПРОИЗВЕДЁННЫХ байтов |
| V14 Configuration | **да** | `client_max_body_size` — часть периметра, а не «настройка удобства» (G-1) |

### Known Threat Patterns for этого стека

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Stored XSS через SVG под видом PNG (CR-02) | Tampering / Elevation | распознавание по первым байтам; `content_type` записывается из **произведённых** приложением байтов, а не из присланных [VERIFIED: app/routes/uploads.py:270-281] |
| Выход за префикс пользователя через сегменты пути в имени файла | Tampering | `safe_filename` отбрасывает сегменты пути целиком [VERIFIED: app/routes/uploads.py:137-154] |
| Прикрепление ЧУЖОГО ключа через скрытое поле / `hx-include` | Elevation of Privilege | `own_image_keys` — строковое сравнение префикса, `fullmatch` без якорей [VERIFIED: app/services/image_keys.py:108-119] |
| Прикрепление ключа МИНИАТЮРЫ (T-Q40-04) | Elevation of Privilege | приставка `thumbs/` не проходит образец ключа — запрет механический, не дисциплинарный [VERIFIED: app/services/image_keys.py:39-56] |
| Decompression bomb | DoS | `MAX_DECODED_PIXELS` проверяется **до** распаковки пикселей [VERIFIED: app/services/images.py:223-245] |
| Удержание тела произвольного размера в памяти (WR-02) | DoS | порционное чтение с прерыванием на первом превышении [VERIFIED: app/routes/uploads.py:197-219] |
| **НОВОЕ В ЭТОЙ ФАЗЕ:** партия из тысячи частей | DoS | `await request.form(max_files=…, max_fields=…)` — **сегодня не задано**, Starlette для файловых частей предела не имеет (G-3) |
| **НОВОЕ В ЭТОЙ ФАЗЕ:** сырое имя отвергнутого файла на экране | XSS / визуальный слом | `safe_filename` перед показом; автоэкранирования Jinja2 мало — оно закрывает разметку, но не имя в четыре тысячи символов (D-05) |
| Инъекция заголовка / открытый редирект через `HX-Location` | Tampering | `_local_path` в `app/pages/htmx.py` + AST-правило GATE-07 |

## Sources

### Primary (HIGH confidence)

- `app/static/js/htmx.min.js` — вендоренный htmx 2.0.10: условие составного запроса (`vn`),
  сбор значений формы (`fn`), связь элемента с формой (`Nt`)
- `app/templates/includes/htmx_config.html:153-167` — `responseHandling`, пять правил
- `app/templates/includes/htmx_error_banner.html` — исключение для 422, обе плашки
- `app/routes/uploads.py` (319 строк, прочитан целиком) — предмет переноса
- `app/services/image_keys.py` (119 строк, прочитан целиком) — `own_image_keys`, `thumb_key`
- `app/services/images.py:85-245` — `prepare_upload`, контракт порядка шагов
- `app/pages/__init__.py` (167 строк, прочитан целиком) — `require_access`, пер-роутерный гейт
- `app/pages/htmx.py:180-240,700-860` — `HtmxRefusal`, `_local_path`, `respond`
- `app/pages/ads.py:436-481,505-560` — `_attachment_refusal`, разбор `images`, WR-03
- `app/templates/ads/form.html` (579 строк, прочитан целиком) — блок вложений и скрипт
- `app/templates/components/form_wrapper.html` (173 строки, прочитан целиком)
- `app/templates/components/thumb.html` (35 строк, прочитан целиком)
- `app/templates/ads/includes/autosave_response.html` (прочитан целиком)
- `tests/test_templates/test_ads_form_security.py` (99 строк, прочитан целиком)
- `tests/test_templates/test_htmx_markup_gates.py:97-200,860-900,2044-2240,3560-3660,5274-5300`
- `tests/test_pages/test_access_gate.py:60-200`
- `tests/test_pages/test_impersonation_gate.py:78-260`
- `tests/test_pages/test_hx_location_destinations.py:40-80`
- `tests/test_pages/test_ads_editor.py:170-200,395-445`
- `nginx/nginx.conf.template`, `nginx/nginx-http.conf.template`
- `app/config.py:43-44`, `pyproject.toml:39-41`
- `starlette.formparsers` и `inspect.signature(Request.form)` — исполнены в venv проекта
- Прогоны на сегодняшнем дереве: `test_ads_form_security.py` → 5 passed;
  `test_access_gate.py` + `test_impersonation_gate.py` → 35 passed

### Secondary (MEDIUM confidence)

- Context7 `/bigskysoftware/htmx/v2.0.4` — `hx-encoding`, `hx-indicator`, `hx-include`,
  `responseHandling`. ⚠️ Документация версии **2.0.4**, а дерево несёт **2.0.10**; поэтому
  каждое поведенческое утверждение перепроверено по вендоренному артефакту, и в тексте
  приоритет отдан ему.

### Tertiary (LOW confidence)

- Умолчание `client_max_body_size` в nginx при отсутствии директивы — **не проверено**, помечено
  A1 и обойдено рекомендацией задавать предел явно.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — новых пакетов нет вовсе; версии сняты исполнением в venv проекта
- Architecture: **HIGH** — механика htmx прочитана в вендоренном артефакте, а не в документации
  другой версии; все интеграционные точки открыты `Read` и процитированы дословно
- Pitfalls: **HIGH** для G-1…G-4, G-6…G-8 (измерены чтением исходников и прогонами);
  **MEDIUM** для G-5 (механизм всплытия — рассуждение A2, проверяется одним прогоном в браузере)
- Validation architecture: **HIGH** — фреймворк и команды исполнены
- Security: **HIGH** — угрозы и меры выписаны из комментариев-обоснований самого дерева

**Research date:** 2026-09-18
**Valid until:** 2026-10-18 (стабильный стек, вендоренные артефакты; переоценить, если до
планирования сменится вендоренный htmx или значения `max_images_per_ad` / `max_image_size_mb`)

---

*Phase: 12-zagruzka-izobrazheniy-bez-fetch*
