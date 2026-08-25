# Phase 1: Интерфейсный фундамент - Pattern Map

**Mapped:** 2026-08-09
**Files analyzed:** 21 групп новых/изменяемых артефактов
**Analogs found:** 18 / 21 (3 без аналога)

Фаза не пишет новую логику — она **переукладывает существующий слой представления**. Поэтому ценность этой карты не в «как написать», а в «что уже написано и не должно потеряться». Для каждого нового файла ниже назван конкретный существующий файл, чьи соглашения он обязан повторить, с дословной выдержкой.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/templates/components/*.html` (10 макросов) | template-macro-library | render-only | `app/templates/includes/icons.html` | exact |
| `app/templates/base.html` (переписывается) | template-shell | request-response | `app/templates/base.html` (текущий) | exact (self) |
| `app/templates/auth_base.html` (новый) | template-shell | request-response | `app/templates/base.html` + `app/templates/auth/login.html` | role-match |
| `app/pages/common.py` → `get_shell_context()` | context-provider / service | CRUD (read-only aggregate) | `app/pages/common.py::get_user_from_cookie` + `app/pages/ads.py::_enrich_ads_with_stats` | role-match |
| `app/pages/common.py` → глобал `asset_version` | config / template-global | render-only | `app/pages/common.py:27-29,60` | exact |
| `app/main.py` → `app.mount("/static", ...)` | config | file-I/O | `app/main.py:61-74` (`include_router` блок) | role-match |
| `app/static/css/app.css` | static asset | file-I/O | `app/templates/base.html:25-29` (inline `<style>`) | partial |
| `app/static/js/htmx.min.js`, `alpine.min.js` | vendored asset | file-I/O | `app/templates/base.html:23-24` (CDN-ссылки) | partial |
| `app/static/fonts/*.woff2` (18) | static asset | file-I/O | — | **none** |
| `app/templates/ads/list.html` + `ads/includes/ad_card.html` + `ads/partial_cards.html` | template-page + partial | request-response + infinite-scroll | сама эта тройка (эталон миграции для 4 остальных разделов) | exact (self) |
| `app/templates/{groups,schedules,history,accounts}/list.html` + partials | template-page | request-response + infinite-scroll | `ads/` тройка | exact |
| `app/templates/accounts/partials/sync_status_card.html` | template-partial | polling (self-terminating) | сам файл | exact (self) |
| `app/templates/auth/*.html` (7) | template-page | request-response (form POST) | `app/templates/auth/login.html` | exact |
| `app/templates/admin/*.html` (8) | template-page | request-response | `app/templates/admin/user_history.html` (единственный с HTMX) | role-match |
| `app/templates/billing/balance.html` | template-page | request-response | — (единственный `<table>` в проекте) | **none** |
| Удаление 6 `*_rows.html` + 6 веток `layout` | cleanup | — | `app/pages/ads.py:60` | exact |
| `tests/test_pages/test_shell.py` | test | request-response | `tests/test_pages/test_profile.py` | exact |
| `tests/test_pages/test_htmx_preserved.py` | test | infinite-scroll / polling | `tests/test_pages/test_profile.py` | exact |
| `tests/test_pages/test_responsive_markup.py` | test | request-response | `tests/test_pages/test_profile.py` | exact |
| `tests/test_templates/test_components.py` | test | render-only (без HTTP) | — (в проекте нет тестов, рендерящих шаблон напрямую) | **none** |
| `tests/conftest.py` → `authed_client`, `admin_client` | test-fixture | request-response | `tests/conftest.py:45-67` (`client`, `auth_headers`) | exact |

---

## Pattern Assignments

### `app/templates/components/*.html` (template-macro-library, render-only)

**Analog:** `app/templates/includes/icons.html` — прямо назван прецедентом в D-13.

**Шапка файла + сигнатура макроса** (`includes/icons.html:1-6`, дословно):
```jinja
{# Унифицированные иконки (Heroicons outline, viewBox 0 0 24 24) #}
{# size: h-4 w-4, h-5 w-5 и т.д. По умолчанию h-5 w-5 #}

{% macro icon_back(size='h-4 w-4') %}
<svg class="{{ size }}" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
{% endmacro %}
```

Соглашения, читаемые из прецедента и обязательные для новой библиотеки:
1. Файл открывается комментарием `{# ... #}` с назначением и описанием параметров.
2. Все параметры **явные, со значениями по умолчанию**; ноль обращений к переменным контекста.
3. Тело макроса — одна строка разметки, без внутренних `{% include %}`.
4. `aria-hidden="true"` на декоративной графике.

**Многопараметрический вариант** — `app/templates/includes/messenger_icon.html:1`:
```jinja
{% macro messenger_icon(messenger_type, size='h-5 w-5', title=None, show_label=true) %}
```
Порядок: обязательный позиционный первым, дальше опциональные. Новые макросы (`badge(variant, label)`, `button(label, href=None, variant='primary')`, `field(name, label, type='text', value='', required=false)`) строятся по этой же форме.

**Стиль вызова** (`app/templates/schedules/list.html:5`, дословно) — `from ... import`, а **не** `import ... as`:
```jinja
{% from "includes/icons.html" import icon_pause, icon_play, icon_edit, icon_delete %}
```
Так написаны все 25 существующих импортов. Новая библиотека должна импортироваться идентично: `{% from "components/badge.html" import badge %}`.

**Вызов с передачей параметра** (`ads/includes/ad_card.html:33`):
```jinja
{{ icon_edit('h-4 w-4 lg:h-5 lg:w-5') }}
```

**Чего в аналоге нет и что нужно спроектировать:** модалка (`components/modal.html`) — прецедента нет ни в макете, ни в приложении (D-18). Для неё аналогов не существует; см. §No Analog Found.

---

### `app/templates/base.html` (template-shell, request-response)

**Analog:** текущий `app/templates/base.html` — переписывается целиком, но **имена блоков и контракт переменных менять нельзя**.

**Контракт блоков** (`base.html:9,32,215,221`):
```jinja
<title>{% block title %}Broadcaster{% endblock %}</title>
...
{% block body %}
{% if user %}
   ... шелл ...
        {% block content %}{% endblock %}
{% endif %}
{% endblock %}
```

Критично: **29 шаблонов делают `{% extends "base.html" %}`**, из них 22 переопределяют `content`, а 7 auth-страниц переопределяют `body` (обходя `{% if user %}`). Переименование `title` / `body` / `content` ломает всё разом. Новый шелл обязан сохранить эти три имени; auth-шелл (D-08) даёт auth-страницам возможность перестать переопределять `body`.

**Контракт переменных шелла** — читаются только три: `user`, `is_admin`, `active_page`:
```jinja
{% if active_page == 'dashboard' %}bg-gray-100 text-gray-900 font-medium{% else %}...{% endif %}
{% if is_admin %} ... /admin ... {% endif %}
{{ user.name[0]|upper if user.name else '?' }}
```
`[app/templates/base.html:45,73-78,84]`

`active_page` проставляется 26 раз в 9 роутерах вручную — механизм переиспользуется как есть (UI-03), см. `app/pages/profile.py:30`.

**Навигация — `<a href>`, а не кнопка.** Дословно `base.html:45`:
```jinja
<a href="/dashboard" class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors {% if active_page == 'dashboard' %}...{% endif %}">
```
В макете переходы сделаны `<button sc-camel-on-click>` (SPA-прототип) — переносить это **нельзя**. Существующее поведение `<a href>` — правильное, оно и есть аналог.

**Дублирование, которое новый шелл устраняет:** сейчас список навигации выписан **трижды** (desktop sidebar 44-79, slide-over 139-174, bottom tabs 189-210) — 26 копий одной ссылки. Новый шелл с `data-nav` + `data-tabs` должен вынести состав меню в один список (Jinja-цикл по списку из шелл-контекста), иначе после D-11 переименования придётся править в трёх местах.

**Что обязано переехать в `app.css` дословно** (`base.html:25-29`):
```html
<style>
    [x-cloak] { display: none !important; }
    @keyframes fade-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fade-in { animation: fade-in 0.2s ease-out; }
</style>
```
Без `[x-cloak]` в `app.css` свёрнутые Alpine-блоки фильтров мигнут при загрузке.

**Комментарий, который нужно сохранить** (`base.html:223`) — зафиксированный отрицательный опыт:
```html
<!-- View Transitions отключены: при infinite scroll (hx-trigger="revealed") вызывали мерцание и рывки скролла -->
```

**Подключение ассетов** — заменяются строки 10-24 (Tailwind CDN + `tailwind.config` + Google Fonts preconnect + unpkg htmx/alpine) на `url_for('static', ...)`. `url_for` уже в globals окружения.

---

### `app/templates/auth_base.html` (template-shell, request-response)

**Analog:** `app/templates/auth/login.html` — образец текущей компоновки auth-экрана; из него выносится обёртка.

**Текущая обёртка** (`auth/login.html:1-10`, дословно):
```jinja
{% extends "base.html" %}
{% block title %}Вход — Broadcaster{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
  <div class="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-sm">
    <!-- Logo -->
    <div class="text-center mb-8">
      <h1 class="text-xl font-semibold text-gray-900">Broadcaster</h1>
      <p class="text-sm text-gray-500 mt-1">Войдите в аккаунт</p>
    </div>
```

Все 7 auth-страниц повторяют эту структуру «центрированная карточка + логотип + подзаголовок». `auth_base.html` — это ровно она, вынесенная в шелл с блоками `title`, `auth_subtitle`, `content`; страницы после миграции переходят с `{% block body %}` на `{% extends "auth_base.html" %}` + `{% block content %}`.

**Паттерн сообщений** (`auth/login.html:13-19`) — переносится в auth-шелл или в компонент `alert`:
```jinja
{% if error %}
<div class="bg-red-50 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{{ error }}</div>
{% endif %}
{% if request.query_params.get('reset') == 'success' %}
<div class="bg-green-50 ...">Пароль успешно изменён. Войдите с новым паролем.</div>
{% endif %}
```
Обратите внимание: используется `request` из контекста — при переносе в макрос этот доступ пропадёт (Pitfall 4), значение нужно передавать параметром.

**Поле формы — исходник для макроса `field`** (`auth/login.html:23-28`):
```jinja
<div>
  <label for="email" class="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
  <input type="email" name="email" id="email" required autocomplete="email"
    class="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm ..."
    placeholder="you@example.com">
</div>
```
Сигнатура макроса обязана покрыть: `type`, `name`, `id`, `required`, `autocomplete`, `placeholder`, `label`, `value`. Иначе 7 auth-экранов не соберутся.

---

### `app/pages/common.py` → `get_shell_context()` (context-provider, read-only aggregate)

**Analog 1 — форма функции модуля:** `app/pages/common.py:63-76`, дословно:
```python
async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Read JWT from httpOnly cookie and return the User, or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    ...
```
Конвенции: async, явные `db: AsyncSession` / `settings: Settings` параметрами (не Depends — функция вызывается из обработчика), однострочный докстринг на английском, ранний `return None`.

**Analog 2 — агрегирующие подсчёты одним запросом:** `app/pages/ads.py:17-37`, дословно:
```python
async def _enrich_ads_with_stats(db: AsyncSession, ads: list[Ad]) -> None:
    """Добавляет sends_count и schedules_count к каждому объявлению."""
    if not ads:
        return
    ad_ids = [a.id for a in ads]
    sends_result = await db.execute(
        select(SendLog.ad_id, func.count().label("cnt"))
        .where(SendLog.ad_id.in_(ad_ids), SendLog.status == "ok")
        .group_by(SendLog.ad_id)
    )
    sends_map = {r.ad_id: r.cnt for r in sends_result.all()}
```
Это образец для счётчиков меню: `select(func.count()).where(Model.user_id == user.id)` через `db.execute`, без репозиториев — так написан весь слой `app/pages/`.

**Analog 3 — фильтрация по пользователю:** `app/pages/accounts.py:118-124`, дословно:
```python
result = await db.execute(
    select(MessengerAccount)
    .where(MessengerAccount.user_id == user.id)
    .order_by(MessengerAccount.id)
    .offset(offset)
    .limit(limit + 1)
)
```
Индикатор «воркеров онлайн» (D-19) — это тот же запрос, суженный до `func.count()` с дополнительным `MessengerAccount.status == "active"`. `status: Mapped[str] = mapped_column(String(20), default="disconnected")` — `app/models/messenger_account.py:19`.

**Analog 4 — регистрация глобала** (`app/pages/common.py:27-29,60`, дословно):
```python
templates.env.globals["get_image_url"] = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["resolve_image_url"] = _resolve_image_url
templates.env.globals["s3_public_url"] = lambda: get_settings().s3_public_url
...
templates.env.globals["format_datetime_for_user"] = format_datetime_for_user
```
`asset_version` регистрируется здесь же и этим же способом — значение не зависит от запроса.

**Ограничение, определяющее реализацию:** Starlette 0.52.1 вызывает контекст-процессоры **синхронно** (`context.update(context_processor(request))`, без `await`). Async-провайдер зарегистрировать как `context_processors` **нельзя** — `get_shell_context` вызывается из обработчика (или как FastAPI-зависимость) и подмешивается в словарь.

**Точка подмешивания — образец словаря контекста** (`app/pages/profile.py:24-32`, дословно):
```python
return templates.TemplateResponse(
    "profile.html",
    {
        "request": request,
        "user": user,
        "is_admin": check_is_admin(user, settings),
        "active_page": "profile",
        "timezone_choices": TIMEZONE_CHOICES,
    },
)
```
Таких мест ~26. Планировать надо либо `**await get_shell_context(db, user)` в каждое, либо async-зависимость FastAPI. `check_is_admin` показывает, как в этот словарь уже добавляется вычисляемое поле.

**Запрещённый источник:** `wa_container_manager.list_worker_containers()` — синхронный Docker SDK (`app/services/wa_container_manager.py:103-106`), вызывается сегодня только из Celery (`app/worker/tasks.py:458`). На рендере страницы блокирует event loop; в тестах `/var/run/docker.sock` недоступен. D-19 фиксирует источник = БД.

---

### `app/main.py` → монтирование `/static` (config, file-I/O)

**Analog:** блок регистрации в `create_app()`, `app/main.py:61-74`, дословно:
```python
    app = FastAPI(title="Broadcaster", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    Instrumentator(
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")
    app.include_router(auth_router)
```
Монтирование ставится сразу после `add_middleware` (строка 62). Импорты — верхним блоком файла (`app/main.py:6-25`), внутрь функции не заносятся.

**Аналог построения пути** — `app/pages/common.py:14`, дословно:
```python
_templates_dir = Path(__file__).resolve().parent.parent / "templates"
```
Тот же приём для `_static_dir`, имя `name="static"` обязательно — оно включает `url_for('static', path=...)`.

**Риск, который аналог подсвечивает:** фикстура `client` вызывает `create_app(settings=test_settings)` в каждом тесте (`tests/conftest.py:46`). `StaticFiles(directory=...)` бросает исключение, если каталога нет — значит `app/static/` должен существовать в git (с `.gitkeep`, если пустой), иначе упадут **все** 393 теста, а не только новые.

---

### `app/templates/ads/list.html` + `ads/includes/ad_card.html` + `ads/partial_cards.html` (эталон миграции раздела)

Это самая маленькая полная тройка «страница + карточка + партиал» — её стоит мигрировать первой и использовать как образец для `groups`, `schedules`, `history`, `accounts`.

**Скелет страницы раздела** (`ads/list.html:1-12`, дословно):
```jinja
{% extends "base.html" %}
{% block title %}Объявления — Broadcaster{% endblock %}
{% block content %}

<!-- Header -->
<div class="flex items-center justify-between mb-6">
  <h1 class="text-lg lg:text-xl font-semibold text-gray-900">Объявления</h1>
  <a href="/ads/new" class="inline-flex items-center gap-1.5 bg-indigo-600 text-white rounded-lg px-3.5 py-2 ...">
    <svg class="h-4 w-4" ...></svg>
    Создать
  </a>
</div>
```
После миграции заголовок раздела и CTA переезжают в `data-head` шелла (макет, строка 373) — то есть у страниц раздела этот блок **исчезает**, а его содержимое передаётся в шелл через переменные контекста (`page_title`, `page_subtitle`, CTA). Это структурное изменение, а не покраска: планировать его надо один раз в Плане 1, иначе каждый раздел изобретёт своё.

**Список + сентинел** (`ads/list.html:15-23`, дословно):
```jinja
{% if ads %}
<div class="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
  {% for ad in ads %}
  {% include "ads/includes/ad_card.html" %}
  {% endfor %}
  {% if has_next %}
  <div hx-get="/ads/partial?offset={{ next_offset }}&limit=30&layout=cards" hx-trigger="revealed" hx-swap="outerHTML" class="py-4 text-center text-sm text-gray-400">Загрузка...</div>
  {% endif %}
</div>
{% else %}
<div class="text-center py-12">
  <p class="text-sm text-gray-500">Нет объявлений</p>
  ...
{% endif %}
```

**Партиал — тот же фрагмент без обёртки** (`ads/partial_cards.html`, файл целиком, 6 строк):
```jinja
{% for ad in ads %}
{% include "ads/includes/ad_card.html" %}
{% endfor %}
{% if has_next %}
<div hx-get="/ads/partial?offset={{ next_offset }}&limit=30&layout=cards" hx-trigger="revealed" hx-swap="outerHTML" class="py-4 text-center text-sm text-gray-400">Загрузка...</div>
{% endif %}
```

**Инварианты, которые обязаны пережить перевёрстку:**
- сентинел — **последний элемент внутри того же контейнера**, что и карточки; он заменяет сам себя (`hx-swap="outerHTML"`) и приносит следующий сентинел. Вынести его из контейнера или обернуть = обрыв цепочки после первой подгрузки, невидимый на первом экране;
- `list.html` и `partial_cards.html` содержат **идентичный** сентинел — при правке одного правится второй;
- `hx-target` нет и добавлять его не нужно — цель неявная (сам элемент);
- в `groups` / `history` сентинел дополнительно протаскивает фильтры циклом `{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}` — переносится дословно.

**Карточка — кандидат в макрос** (`ads/includes/ad_card.html:1,5,14`):
```jinja
{% from "includes/icons.html" import icon_edit, icon_delete %}
...
{% if ad.images and ad.images|length > 0 %}
<img src="{{ get_image_url(ad.images[0]) }}" ...>
...
<p class="text-sm lg:text-base font-medium text-gray-900 truncate">{{ ad.title }}</p>
```
Файл **не объявляет параметров** и берёт `ad` из переменной цикла вызывающего шаблона. При переводе в макрос `ad` обязан стать параметром, иначе Jinja отрендерит пустые строки без ошибки — страница вернёт 200 с пустыми карточками.

**Статус-бейдж — исходник для `badge`** (`ad_card.html:25-29`):
```jinja
{% if ad.is_active %}
<span class="inline-flex items-center rounded-full bg-emerald-50 ... text-emerald-700 shrink-0">Активно</span>
{% else %}
<span class="inline-flex items-center rounded-full bg-gray-100 ... text-gray-600 shrink-0">Пауза</span>
{% endif %}
```
Маппинг «домен → вариант» остаётся в вызывающем шаблоне (как здесь), макрос принимает `variant` явным параметром — единого enum статусов в проекте нет.

**Подтверждение удаления — точка применения модалки (D-18)** (`ad_card.html:34-36`):
```jinja
<form method="post" action="/ads/{{ ad.id }}/delete" onsubmit="return confirm('Удалить объявление?')">
  <button type="submit" ...>{{ icon_delete(...) }}<span class="hidden lg:inline text-sm">Удалить</span></button>
</form>
```
Модалка заменяет `onsubmit="return confirm(...)"`, **не** сам `<form method="post">` — маршрут и метод остаются.

---

### Удаление `*_rows.html` + веток `layout` (cleanup)

**Analog / точка правки:** `app/pages/ads.py:60`, дословно:
```python
    template = "ads/partial_cards.html" if layout == "cards" else "ads/partial_rows.html"
```
и сигнатура выше, `app/pages/ads.py:46`:
```python
    layout: str = Query("table"),
```
Пять аналогичных мест: `accounts.py:131`, `accounts.py:704`, `groups.py:152`, `schedules.py:68`, `history.py:107`.

Порядок операции: сначала схлопнуть тернарник в единственный шаблон, затем удалить параметр `layout` из сигнатуры (или оставить как игнорируемый ради совместимости уже открытых вкладок), затем удалить 6 файлов. Обратный порядок ломает роутер.

---

### `tests/test_pages/test_shell.py`, `test_htmx_preserved.py`, `test_responsive_markup.py` (test)

**Analog:** `tests/test_pages/test_profile.py` — единственный образец тестирования **page-роута** с cookie-авторизацией.

**Cookie-логин — копировать дословно** (`test_profile.py:17-42`):
```python
@pytest.mark.asyncio
async def test_profile_get_renders_form_for_authenticated_user(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict,
):
    # Фикстура auth_headers создаёт пользователя через API-роуты
    result = await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    user = result.scalar_one()
    ...
    # Логинимся через page-роут, чтобы установить cookie access_token
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.get("/profile")
    assert response.status_code == 200
    html = response.text
    assert "Профиль" in html
```

**Почему это критично:** `auth_headers` (`tests/conftest.py:55-67`) регистрирует пользователя и возвращает **Bearer-заголовок для `/api/*`**:
```python
@pytest_asyncio.fixture
async def auth_headers(client):
    """Register a user and return auth headers."""
    await client.post("/api/auth/register", json={...})
    resp = await client.post("/api/auth/login", json={...})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```
Page-роуты читают JWT **из httpOnly-cookie `access_token`** (`app/pages/common.py:67`), а не из заголовка. Поэтому `auth_headers` сам по себе страницу не авторизует — обязателен последующий `POST /login`. Фикстура `authed_client` из Wave 0 инкапсулирует именно эту связку `auth_headers` → `POST /login`.

**Паттерн проверки редиректа неавторизованного** (`test_profile.py:9-14`):
```python
async def test_profile_requires_auth(client: AsyncClient):
    response = await client.get("/profile", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/login" in response.headers.get("location", "")
```

**Для `test_htmx_preserved.py`** проверка второй страницы выдачи делается тем же `client`, прямым запросом партиала: `GET /ads/partial?offset=30&limit=30&layout=cards` → в `response.text` снова присутствует `hx-get` со следующим `offset`. Тест самоостановки поллинга: ответ `sync-status` при не-`syncing` статусе не содержит `hx-trigger`.

**Осторожно — существующие ассерты на точную разметку** (`tests/`, дословно):
```python
assert '<option value="Europe/Moscow" selected' in html
assert 'selected' in html.split('Europe/Moscow')[1]
assert "selected" not in html.split('name="account_id"')[1].split("</select>")[0]
```
Первый сломается, если `<select>` начнёт рендериться макросом с другим порядком атрибутов. Ни один существующий ассерт **не** ссылается на Tailwind-классы — удаление Tailwind само по себе тесты не ломает; ломают переименования D-11 (`"Профиль"`, `"Пауза"`, `"Справочник групп"`).

**Фикстуры-аналоги для `authed_client` / `admin_client`** (`tests/conftest.py:45-51`):
```python
async def client(db_session, test_settings):
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```
`admin_client` строится подменой `test_settings.admin_email` — `check_is_admin` сравнивает ровно `user.email == settings.admin_email` (`app/pages/common.py:79-83`).

---

## Shared Patterns

### Аутентификация page-роута
**Source:** `app/pages/profile.py:14-22` (повторено в 26 обработчиках)
**Apply to:** любое изменение сигнатуры/контекста страниц (в т.ч. подмешивание шелл-контекста)
```python
@router.get("/profile", response_class=HTMLResponse)
async def profile_get(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
```
Шелл-контекст добавляется **после** этой проверки — `get_shell_context` не должен вызываться для `user is None`.

### Словарь контекста шаблона
**Source:** `app/pages/profile.py:24-32`, `app/pages/ads.py:61-70`
**Apply to:** все 26 мест рендера страниц
Обязательный минимум ключей: `request`, `user`, `is_admin`, `active_page`. Новый шелл добавляет к ним данные D-09 — и это должно быть **одно** место сборки, а не 26 разных наборов ключей.

### Импорт макросов
**Source:** `app/templates/schedules/list.html:5`, `app/templates/ads/includes/ad_card.html:1`
**Apply to:** все шаблоны, использующие компоненты
```jinja
{% from "includes/icons.html" import icon_edit, icon_delete %}
```
`{% from ... import ... with context %}` запрещён D-13 (он ещё и отключает кэширование импорта).

### Экранирование
**Source:** весь `app/templates/` — ноль вхождений `|safe`, `Markup(`, `{% autoescape %}`
**Apply to:** все новые макросы. Компонент, принимающий HTML-строку, нарушит инвариант, который сегодня целостен; параметры должны быть текстом/числами/булевыми.

### Глобалы окружения вместо самодельных хелперов
**Source:** `app/pages/common.py:27-29,60`
**Apply to:** все мигрируемые шаблоны
Доступны: `get_image_url`, `resolve_image_url`, `s3_public_url`, `format_datetime_for_user`, `url_for`. Форматирование дат в новых шаблонах — только через `format_datetime_for_user`; заметьте, что `ad_card.html:20` сейчас использует `ad.created_at.strftime('%d.%m.%Y')` в обход глобала — при миграции это стоит привести к общему хелперу.

---

## No Analog Found

Файлы без близкого аналога в кодовой базе — планировщику опираться на RESEARCH.md и макет.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/templates/components/modal.html` | component | client-side | Модалок нет ни в приложении, ни в макете (0 `dialog`/overlay; единственный `position:fixed` — `data-tabs`). Проектируется с нуля: overlay, focus-trap, закрытие по Esc. Единственный потребитель — замена `onsubmit="return confirm(...)"` в `ad_card.html:34` |
| `app/static/fonts/*.woff2` | static asset | file-I/O | Каталога `app/static` не существует; вендоринга шрифтов в проекте не было никогда. Источник — манифест макета (18 woff2), процедура извлечения в RESEARCH.md §Code Examples, пример 1 |
| `tests/test_templates/test_components.py` | test | render-only | В проекте нет ни одного теста, рендерящего шаблон напрямую через `templates.env.get_template(...).render(...)` — все тесты идут через HTTP-клиент. Паттерн придётся ввести (можно опереться на `templates` из `app/pages/common.py:15` как на готовое окружение) |
| `app/templates/billing/balance.html` | template-page | request-response | Единственный `<table>` в проекте (120 строк), а в макете `<table>/<tr>/<td>` встречаются 0 раз. Прямого образца «как таблица выглядит в новой системе» нет — либо `data-row`/`data-rowhead`, либо проектное решение |

**Отдельно про `[data-hrow] > [style*="grid-area:meta"]`** (медиазапрос 1080px макета): селектор совпадает только при наличии инлайн-`style` у ребёнка. При переезде на классы (D-01) он молча перестанет работать — единственное место, где «дословный перенос CSS» делать нельзя; заменяется на `[data-hrow] > [data-area="meta"]`.

---

## Metadata

**Analog search scope:** `app/templates/` (48 файлов), `app/pages/` (9 роутеров + `common.py`), `app/main.py`, `tests/conftest.py`, `tests/test_pages/`
**Files read this session:** `app/templates/base.html`, `app/templates/includes/icons.html`, `app/templates/auth/login.html`, `app/templates/ads/list.html`, `app/templates/ads/includes/ad_card.html`, `app/templates/ads/partial_cards.html`, `app/pages/common.py`, `app/pages/ads.py` (1-80), `app/pages/accounts.py` (100-140), `app/pages/profile.py` (1-60), `app/main.py` (1-120), `tests/test_pages/test_profile.py`, `tests/conftest.py` (45-67)
**Pattern extraction date:** 2026-08-09
