# Phase 12: Загрузка изображений без `fetch()` — Pattern Map

**Mapped:** 2026-09-18
**Files analyzed:** 16 (2 создаются, 11 правятся, 1 снимается целиком, 2 тестовых файла заводятся)
**Analogs found:** 15 / 16

Все пути ниже проверены `git ls-files` — это отслеживаемый исходник, не зеркало установки.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/pages/ads.py` (+ обработчик загрузки) | route (page/htmx) | file-I/O + request-response | `app/pages/ads.py::ads_create` (:652-736) + `_save_from_editor` (:486-560) | exact |
| `app/services/image_upload.py` (НОВЫЙ) | service | file-I/O / transform | `app/routes/uploads.py::upload_image` (:191-319) — источник переноса; соседство `app/services/images.py`, `app/services/image_keys.py` | exact (дословный перенос) |
| `app/templates/ads/includes/media_strip.html` (НОВЫЙ) | template (include-фрагмент) | render | `app/templates/ads/includes/sched_count_rule.html` | exact |
| `app/templates/ads/form.html` | template (страница) | render | сам себе (:102-164 заменяется одной строкой include, как :220-223) | exact |
| `app/templates/ads/includes/autosave_response.html` | template (OOB-ответ) | event-driven | сам себе (:19-21 — форма OOB-блока) | exact |
| `app/templates/components/form_wrapper.html` | component macro | render | сам себе (:162-172 — сигнатура макроса) | exact |
| `app/routes/uploads.py` | route (JSON API) | — | СНИМАЕТСЯ | n/a |
| `tests/test_pages/test_ads_image_upload.py` (НОВЫЙ) | test (integration) | request-response | `tests/test_pages/test_account_groups.py:516-550` (htmx-фрагмент) + `tests/test_routes/test_uploads.py:264-320` (multipart) | role-match ×2 |
| `tests/test_services/test_image_upload.py` (НОВЫЙ) | test (unit) | transform | `tests/test_routes/test_uploads.py` (переезжающие утверждения о сервисе) | exact |
| `tests/test_pages/test_access_gate.py` | test (гейт-перечень) | — | сам себе (:84-90, :139-145) | exact |
| `tests/test_pages/test_impersonation_gate.py` | test (гейт-перечень) | — | сам себе (:218) | exact |
| `tests/test_templates/test_htmx_markup_gates.py` | test (инвентарь чисел) | — | сам себе (:140, :2219, :186-190, :895) | exact |
| `tests/test_templates/test_ads_form_security.py` | test (гейт безопасности) | — | сам себе (:49-66) — утверждение ИНВЕРТИРУЕТСЯ | exact |
| `tests/test_pages/test_hx_location_destinations.py` | test | — | сам себе (:52-56 `EDITOR_SCRIPT_MARKER`) | exact |
| `tests/test_pages/test_ads_editor.py` | test | — | сам себе (:33, :198, :406-424) | exact |
| `nginx/nginx.conf.template`, `nginx/nginx-http.conf.template` | config | — | `nginx/nginx.conf.template:59` | partial (HTTP-шаблон директивы не имеет) |

## Pattern Assignments

### `app/pages/ads.py` — новый обработчик загрузки (route, file-I/O)

**Analog:** `app/pages/ads.py::ads_create` (:652-736) и `_save_from_editor` (:486-560) — тот же роутер, тот же слой ответа, тот же разбор формы.

**Скелет маршрута и гарда** (:652-692) — копируется посимвольно, включая порядок «пользователь → отказ → работа → `respond`»:
```python
@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")
    ...
    degraded, fragment = await _save_from_editor(...)
    return await respond(request, redirect=degraded, fragment=fragment)
```
Гейта доступа в теле НЕТ и заводить его не нужно — `Depends(require_access)` висит на `ads_router` (`app/pages/__init__.py:143`), это и есть закрытие критерия 3 (D-01).

**Разбор составного запроса + владение ключами** (:519-551) — образец для `hx-include`-половины. Правка при переносе одна: `await request.form()` получает явные `max_files=` / `max_fields=` (G-3):
```python
    form_data = await request.form()
    raw_images = form_data.getlist("images")
    string_images = [value for value in raw_images if isinstance(value, str)]
    try:
        if len(string_images) != len(raw_images):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=INACCESSIBLE_IMAGE_MESSAGE,
            )
        image_list = own_image_keys(
            [v for v in string_images if v.strip()],
            user.id,
            settings.max_images_per_ad,
        )
    except HTTPException as exc:
        return _attachment_refusal(request, db, settings, user, ad, exc)
```
⚠️ У загрузки ветка `except HTTPException` ведёт НЕ в `_attachment_refusal` (тот отвечает 400 без htmx), а в тот же фрагмент полосы с 200 (D-04). Форму «перехватить `HTTPException` из `own_image_keys` и не дать ей доехать до htmx» копировать обязательно; адресат другой.

**Именованный помощник для изъятия транспорта** (:436-483) — образец того, КАК в этом файле оформляется отступление от общего слоя ответа: отдельная функция с докстрингом, называющим изъятие, а не строка посреди пути. D-09 (недостижимость пути без JS) оформляется так же.

**Сборка фрагмента** (:409-433) — нульарный async-сборщик + `templates.TemplateResponse(request, "<шаблон>", {...})`:
```python
async def _autosave_response(request, db, settings, user, ad, error=None) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "ads/includes/autosave_response.html",
        {"user": user, "ad": ad,
         "editor": await _editor_context(db, ad, settings, user),
         "autosave_error": error},
    )
```
Новый обработчик строит такую же пару `(degraded_url, fragment)` и отдаёт её `respond(request, redirect=..., fragment=...)`. `redirect=` — адрес редактора (`f"/ads/{ad.id}/edit"` либо `"/ads/new"`), как в :483.

---

### `app/services/image_upload.py` (НОВЫЙ) (service, file-I/O)

**Analog:** `app/routes/uploads.py:191-319` — это не «похожий файл», а сам предмет переноса. Переезжает ДОСЛОВНО, вместе с комментариями-обоснованиями.

**Порционное чтение + предел размера ВЫШЕ типа** (:197-234) — порядок сохранить, следствие наблюдаемо:
```python
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    chunks: list[bytes] = []
    received = 0
    while True:
        chunk = await file.read(UPLOAD_CHUNK_SIZE)
        if not chunk:
            break
        received += len(chunk)
        if received > max_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"File size exceeds {settings.max_image_size_mb}MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)
    if sniff_image(content) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=UNSUPPORTED_IMAGE_MESSAGE)
```
⚠️ В сервисе форма отказа перестаёт быть `HTTPException` и становится `Rejected(display_name, reason)` (§Pattern 2 RESEARCH) — но ПОРЯДОК проверок и ТЕКСТЫ констант не меняются ни на символ.

**Счётная работа в поток** (:243-261) — переносится целиком с комментарием про один uvicorn-воркер и `/health`:
```python
    try:
        prepared = await asyncio.to_thread(prepare_upload, content)
    except ImageTooLarge:
        raise HTTPException(status_code=..., detail=OVERSIZED_IMAGE_MESSAGE)
    except ImageUnreadable:
        raise HTTPException(status_code=..., detail=UNSUPPORTED_IMAGE_MESSAGE)
```

**Ключ и запись объекта** (:263-314) — форма ключа неизменна; миниатюра ВТОРАЯ и своим провалом запрос не валит:
```python
    filename = retarget_extension(safe_filename(file.filename), prepared.extension)
    key = f"{user_id}/{uuid4().hex}_{filename}"
    await upload_file_to_s3(content=prepared.delivery, key=key,
                            content_type=prepared.content_type, ...)
    try:
        await upload_file_to_s3(content=prepared.thumbnail, key=thumb_key(key), ...)
    except Exception:
        logger.warning("thumbnail_upload_failed", key=key, exc_info=True)
```

**Нормализация имени** (`retarget_extension`, :157-188) — та же функция обслуживает D-05: имя ОТВЕРГНУТОГО файла проводится через `safe_filename` перед показом.

---

### `app/templates/ads/includes/media_strip.html` (НОВЫЙ) (template, render)

**Analog:** `app/templates/ads/includes/sched_count_rule.html` — действующая идиома «один источник разметки, три отрисовщика», со своим гейтом единственности.

**Шапка файла — обязательная форма** (sched_count_rule.html:1-34), три абзаца воспроизводятся по смыслу:
```jinja
{# ЕДИНСТВЕННЫЙ ИСТОЧНИК РАЗМЕТКИ ЛИНЕЙКИ СЧЁТЧИКА РАСПИСАНИЙ РЕДАКТОРА ...
   Включают его ДВА места отрисовки: страница редактора (`ads/form.html`) и
   внеполосный узел ответа удаления расписания (...). Вторая копия разметки
   разошлась бы с первой МОЛЧА ...

   ⚠️ ПРИЗНАКА ВНЕПОЛОСНОЙ ПОДМЕНЫ ЗДЕСЬ НЕТ И БЫТЬ НЕ ДОЛЖНО. Этот файл —
   СОДЕРЖИМОЕ, а не узел; внеполосным узел делает ВКЛЮЧАЮЩИЙ его файл ...
   обход считает ФАЙЛЫ, несущие признак ...

   Ожидаемые переменные: `schedules_count`. #}
```
⚠️ Прямое следствие для `OOB_BLOCKS`: `hx-swap-oob` ставится в `autosave_response.html`, а НЕ в `media_strip.html`.

**Содержимое полосы** — переносится из `ads/form.html:107-128` дословно, включая комментарии:
```jinja
<div data-media id="media-strip">
  {%- for key in (ad.images if ad and ad.images else []) %}
  <span class="media-tile">
    {{ thumb(key) }}
    <button class="media-tile__remove" type="submit" name="remove_image"
            value="{{ key }}" aria-label="Убрать вложение"
            title="{{ key.split('_', 1)[-1] }}">×</button>
  </span>
  {%- endfor %}
  <label class="media-tile media-tile--add"{% if ... %} hidden{% endif %} for="file-input">+ ФАЙЛ</label>
</div>
```
Кнопка «×» уже сегодня — именованная кнопка ОТПРАВКИ; D-10 снимает только JS-слушатель, разметку не трогает. Скрытые поля `#image-inputs` (`form.html:124-128`) переезжают внутрь фрагмента и получают `form="ad-form"`.

**Откат миниатюры** — берётся макросом, свой `img.onerror` не пишется (`app/templates/components/thumb.html:30-34`):
```jinja
{% macro thumb(value, class='', lazy=false, alt='') -%}
<img src="{{ thumb_image_url(value) }}" data-full="{{ resolve_image_url(value) }}"
     {%- if class %} class="{{ class }}"{% endif %}
     {%- if lazy %} loading="lazy"{% endif %} alt="{{ alt }}"
     onerror="this.onerror=null;this.src=this.dataset.full">
{%- endmacro %}
```

---

### `app/templates/ads/form.html` (template, render)

**Analog:** сам файл, :220-223 — образец «постоянная обёртка + include»:
```jinja
<div id="sched-count">
  {%- set schedules_count = editor.schedules_count %}
  {% include "ads/includes/sched_count_rule.html" %}
</div>
```
Блок вложений (:102-164) заменяется той же формой. ⚠️ Слово `innerHTML` в этом файле появиться не должно (`test_ads_form_builds_dom_not_markup`) — `hx-swap="innerHTML"` печатает `form_wrapper`, а вызов формы загрузки живёт в `media_strip.html`.

**Связь элемента вне формы с формой** (:319) — механизм, на котором держится буква критерия 1, уже обкатан:
```html
<button class="btn btn--primary" type="submit" form="ad-form" name="save" value="1">...</button>
```

**Соседство, а не вложенность** (:169-178) — комментарий объясняет, почему форма загрузки обязана стоять СОСЕДОМ `#ad-form`; тот же довод переносится к новой форме.

---

### `app/templates/ads/includes/autosave_response.html` (template, event-driven)

**Analog:** сам файл, :19-21 — форма внеполосного блока:
```jinja
<div id="ad-preview" hx-swap-oob="true">{% include "ads/includes/preview.html" %}</div>
<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>
{% set oob = true %}{% include "ads/includes/autosave.html" %}
```
Новый блок полосы пишется ровно так же — и по Pattern 5 несёт **второй** идентификатор (не `#media-strip`), иначе падает G-11. Шапка файла перечисляет идентификаторы списком (:9-12) — новый добавляется туда же. `OOB_BLOCKS = 19` (`test_htmx_markup_gates.py:2219`) → 20.

---

### `app/templates/components/form_wrapper.html` (component macro, render)

**Analog:** сам файл, :162-172. Правка врезается в существующую сигнатуру; четыре ограничения шапки (:24-83) не нарушаются: `method="post"` литералом, `action`/`hx-post` — одно выражение, ни одного `>` внутри тега, `hx-indicator` сразу после адреса.

**Образец вызова с `disabled_elt=''` и `trigger='change'`** — уже есть в дереве (`app/templates/ads/includes/sched_card.html:167-168`):
```jinja
{% call form_wrapper(action='/schedules/' ~ s.id ~ '/toggle', target='#sched-' ~ s.id, swap='outerHTML',
                     trigger='change', disabled_elt='', sync='this:drop') %}
  <input type="hidden" name="return_to" value="editor">
```
Вызывающий, передавший своё `disabled_elt`, обязан быть объявлен в `DISABLED_ELT_EXCEPTIONS` (сегодня `= 2`).

---

### `tests/test_pages/test_ads_image_upload.py` (НОВЫЙ) (test, integration)

**Analog A — htmx-фрагмент:** `tests/test_pages/test_account_groups.py:516-550`. Копируется целиком форма: пара фикстур, утверждение об отсутствии документа, адресное сообщение в каждом `assert`:
```python
@pytest.mark.asyncio
async def test_toggle_returns_the_row_fragment(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """С признаком htmx тумблер отвечает ФРАГМЕНТОМ строки и внеполосным счётчиком."""
    ...
    response = await htmx_client.post(f"/accounts/{account.id}/groups/{group.id}/toggle")
    assert response.status_code == 200, (
        f"запрос htmx получил {response.status_code} вместо фрагмента"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ: обработчик ответил перенаправлением, а "
        "клиент незаметно по нему прошёл — ровно то, чего не видит человек"
    )
    assert f'id="group-row-{group.id}"' in response.text, (...)
```
Пара `authed_client` / `htmx_client` закрывает строку «без htmx маршрут отвечает 302» из карты тестов.

**Analog B — multipart:** `tests/test_routes/test_uploads.py:264-320` — форма отправки файла и генераторы тел (`make_real_png_bytes` :142, `make_png_bytes` :71, `make_declared_huge_png_bytes` :154):
```python
    png_bytes = make_real_png_bytes()
    response = await upload_client.post(
        "/api/uploads/image",
        files={"file": ("test_image.png", png_bytes, "image/png")},
        headers=upload_auth_headers,
    )
```
Для партии — список кортежей под ОДНИМ именем поля (не `images`, см. WR-03): `files=[("files", ("a.png", png, "image/png")), ("files", ("cat.webp", webp, "image/webp"))]`.

⚠️ 26 патчей `@patch("app.routes.uploads.upload_file_to_s3")` привязаны к имени модуля — при переезде они превращаются в `AttributeError`, а не в осмысленный отказ (G-8). Новая цель патча — `app.services.image_upload.upload_file_to_s3`.

---

### Гейт-перечни — точная форма записи

**`tests/test_pages/test_access_gate.py:84-90` и `:139-145`** — оба множества правятся (`uploads_router` уходит, 5 → 4):
```python
GATED_API_ROUTERS = {
    "ads_router",
    "accounts_router",
    "schedules_router",
    "history_router",
    "uploads_router",     # ← снимается
}
...
BLOCK_CHECKED_API_ROUTERS = {
    "ads_router", "accounts_router", "schedules_router", "history_router",
    "uploads_router",     # ← снимается
}
```
⚠️ В файле объявлено, что это ТРИ независимых множества и выведение одного из другого запрещено — правки делаются по отдельности, не «заодно».

**`tests/test_pages/test_impersonation_gate.py:218`** — ТРЕТИЙ перечень, критерием 3 не названный (G-7). Форма записи — `"<путь>::<имя функции>": "<причина>"`:
```python
    "app/pages/ads.py::ads_create": "правка объявления; ничего не отправляет и денег не трогает",
    "app/routes/uploads.py::upload_image": "загрузка картинки объявления",   # ← адрес меняется
```
Новая запись: `"app/pages/ads.py::<имя нового обработчика>": "загрузка картинки объявления"`.

**`tests/test_templates/test_htmx_markup_gates.py`** — инвентарные числа: `HX_POST_PLACES = 3` (:140), `OOB_BLOCKS = 19` (:2219), `FRAGMENT_ROUTES_DECLARED = 11` (:895), летопись изменений :160-190. Каждое изменение дописывается пронумерованной строкой в летопись, а значение ставится ПРОГОНОМ покрасневшего правила.

**`tests/test_templates/test_ads_form_security.py:49-66`** — утверждение инвертируется (`>= 3` → `== 0`), а не ослабляется:
```python
MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")
def test_ads_form_uses_property_assignment():
    assert body.count("createElement") >= 3, body.count("createElement")
    assert body.count("replaceChildren") >= 2, body.count("replaceChildren")
```

---

### `nginx/*.conf.template` (config)

**Analog:** `nginx/nginx.conf.template:59` — единственное вхождение, в блоке `listen 443 ssl`:
```nginx
    client_max_body_size 20M;
```
Соседние директивы файла (:55-57) несут прозу-обоснование прямо над значением — ту же форму берёт и новая запись (связь `max_images_per_ad × max_image_size_mb`). В `nginx/nginx-http.conf.template` директивы НЕТ вовсе — там она заводится впервые, аналога внутри файла нет (см. §No Analog Found).

## Shared Patterns

### Слой ответа — `respond()`
**Source:** `app/pages/htmx.py:712`; применение — `app/pages/ads.py:685,692,728,736`
**Apply to:** новый обработчик загрузки
```python
return await respond(request, redirect=degraded, fragment=fragment)
```
`redirect=` обязателен (FOUND-04) и проверяется даже на ветке фрагмента. Маршрут, зовущий `respond()`, в `FRAGMENT_ROUTES` НЕ попадает — `FRAGMENT_ROUTES_DECLARED = 11` не двигается.

### Гейт доступа — уже висит
**Source:** `app/pages/__init__.py:143` (`Depends(require_access)` на `ads_router`)
**Apply to:** новый маршрут — ни строки гейта не пишется (D-01).

### Владение ключом и потолок — один инструмент
**Source:** `app/services/image_keys.py:83-119`
**Apply to:** обработчик загрузки и обработчик сохранения — обоим один и тот же `own_image_keys`; `free = max_images - len(проверенные)` считается однострочно из его результата, вторым инструментом не заводится.

### Комментарий-обоснование как обязательный артефакт
**Source:** `app/routes/uploads.py:197-234,294-302`; `app/templates/components/thumb.html:1-28`; `app/templates/ads/includes/sched_count_rule.html:1-34`
**Apply to:** все переносимые куски. Переписанный своими словами комментарий — потеря (D-03).

### Адресное сообщение в каждом `assert`
**Source:** `tests/test_pages/test_account_groups.py:531-548`
**Apply to:** оба новых тестовых файла. Сообщение объясняет, ЧТО увидит человек при отказе, а не повторяет выражение.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `nginx/nginx-http.conf.template` (новая `client_max_body_size`) | config | — | в файле директивы нет вовсе; единственный образец — HTTPS-шаблон, у которого другой блок и другое окружение. Умолчание nginx при отсутствии директивы в дереве не измерено (A1) — значение задаётся явно |
| `HX-Trigger` на ответе загрузки (если Q-1 решится первым вариантом) | route header | event-driven | в `app/pages/` сегодня ноль вхождений `HX-Trigger`; ближайший родственник — `HX-Location` в `app/pages/htmx.py` (правило GATE-07 про литеральный правый операнд). Планировщику: образца формы `hx-trigger="<событие> from:body"` в шаблонах дерева тоже нет — это ПЕРВОЕ такое место |

## Metadata

**Analog search scope:** `app/pages/`, `app/routes/`, `app/services/`, `app/templates/ads/includes/`, `app/templates/components/`, `tests/test_pages/`, `tests/test_routes/`, `tests/test_templates/`, `nginx/`
**Files scanned:** 14 прочитано прицельно, ~40 перечислено
**Pattern extraction date:** 2026-09-18
