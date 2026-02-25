# Profile Timezone Settings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Реализовать страницу настроек профиля с выбором часового пояса по умолчанию и использовать этот часовой пояс как дефолт в формах создания расписаний.

**Architecture:** Новый pages-модуль `profile.py` обеспечивает GET/POST для `/profile`, используя существующие зависимости (`get_db`, `get_settings`, `get_user_from_cookie`, `TIMEZONE_CHOICES`, `VALID_TIMEZONES`). Шаблон `profile.html` отображает форму с select таймзоны. В `schedules` pages-обработчик прокидывает в шаблон дефолтный timezone из `user.timezone` при создании нового расписания.

**Tech Stack:** FastAPI (pages-роуты), SQLAlchemy async (модель `User`), Jinja2 шаблоны, pytest для тестов.

---

### Task 1: Добавить tests для страницы профиля

**Files:**
- Create: `tests/test_pages/test_profile.py`
- Modify: *(нет)*
- Test command: `uv run pytest tests/test_pages/test_profile.py -v`

**Step 1: Write the failing tests**

В `tests/test_pages/test_profile.py`:

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_profile_requires_auth(client: AsyncClient):
    response = await client.get("/profile", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/login" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_profile_get_renders_form_for_authenticated_user(client: AsyncClient, db_session: AsyncSession):
    user = User(email="test@example.com", password_hash="x", name="Test", timezone="Europe/Moscow")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Логинимся через существующий helper (через форму /login или прямую установку cookie),
    # предполагая наличие тестового helper `auth_headers` или подобного.


@pytest.mark.asyncio
async def test_profile_post_updates_timezone(client: AsyncClient, db_session: AsyncSession):
    ...
```

(Детали будут дописаны по факту изучения существующих фикстур `client`, `db_session`, `auth_headers` в `tests/conftest.py`.)

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_pages/test_profile.py -v
```

Ожидаем: файл/маршрут не найден, тесты падают.

**Step 3: (будет после реализации)**

---

### Task 2: Реализовать pages-модуль профиля

**Files:**
- Create: `app/pages/profile.py`
- Modify: `app/pages/__init__.py` (если требуется для включения роутера), `main.py` (если подключение роутера идёт там)
- Test: `tests/test_pages/test_profile.py`

**Step 1: Реализовать GET /profile**

В `app/pages/profile.py`:

```python
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import TIMEZONE_CHOICES, VALID_TIMEZONES
from app.dependencies import get_db, get_settings
from app.models.user import User
from app.pages.common import templates, get_user_from_cookie, check_is_admin


router = APIRouter(tags=["pages"])


@router.get("/profile", response_class=HTMLResponse)
async def profile_get(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

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

**Step 2: Реализовать POST /profile**

В том же модуле:

```python
@router.post("/profile")
async def profile_post(
    request: Request,
    timezone: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if timezone in VALID_TIMEZONES:
        user.timezone = timezone
        db.add(user)
        await db.commit()
        # Можно добавить флаг успеха через query param
        return RedirectResponse(url="/profile?saved=1", status_code=302)

    # Невалидное значение — просто вернуть форму без сохранения
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "profile",
            "timezone_choices": TIMEZONE_CHOICES,
            "error": "Неверный часовой пояс",
        },
        status_code=400,
    )
```

**Step 3: Подключить роутер профиля**

- Найти, где в `main.py` или в `app/routes/__init__.py` регистрируются pages-роуты (например, `app.include_router(app.pages.accounts.router)` и т.п.).
- Добавить подключение:

```python
from app.pages import profile as profile_pages
app.include_router(profile_pages.router)
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_pages/test_profile.py -v
```

---

### Task 3: Добавить шаблон profile.html

**Files:**
- Create: `app/templates/profile.html`
- Modify: `app/templates/base.html` (навигация)
- Test: `tests/test_pages/test_profile.py` (проверка наличия select и выбранного значения)

**Step 1: Создать шаблон profile.html**

В `app/templates/profile.html`:

```html
{% extends "base.html" %}

{% block content %}
<div class="max-w-2xl mx-auto py-8">
  <h1 class="text-2xl font-bold text-slate-900 mb-6">Настройки профиля</h1>

  <form method="post" class="space-y-6">
    <div>
      <label for="timezone" class="block text-sm font-medium text-slate-900 mb-2">Часовой пояс</label>
      <select id="timezone" name="timezone" class="block w-full rounded-lg border-0 py-2 px-3 text-slate-900 shadow-sm ring-1 ring-slate-300 focus:ring-2 focus:ring-primary-500 transition-shadow sm:text-sm">
        {% for tz_value, tz_label in timezone_choices %}
        <option value="{{ tz_value }}" {% if user.timezone == tz_value %}selected{% endif %}>{{ tz_label }}</option>
        {% endfor %}
      </select>
    </div>

    {% if error %}
    <p class="text-sm text-red-600">{{ error }}</p>
    {% endif %}

    <div class="flex justify-end">
      <button type="submit" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
        Сохранить
      </button>
    </div>
  </form>
</div>
{% endblock %}
```

**Step 2: Добавить пункт "Профиль" в навигацию**

- В `app/templates/base.html` найти блок навигации (меню по страницам).
- Добавить ссылку:

```html
<a href="/profile" class="{% if active_page == 'profile' %}text-primary-600{% else %}text-slate-600 hover:text-slate-900{% endif %} ...">
  Профиль
``` 

**Step 3: Run tests**

```bash
uv run pytest tests/test_pages/test_profile.py -v
```

---

### Task 4: Использовать user.timezone как дефолт в новой форме расписания

**Files:**
- Modify: `app/pages/schedules.py`
- Modify: `app/templates/schedules/form.html`
- Test: `tests/test_pages/test_schedules.py` (или новый, если нет)

**Step 1: Прокинуть default_timezone из pages-хэндлера**

- В `app/pages/schedules.py` в обработчике GET формы создания нового расписания:
  - После получения `user` вычислить:

```python
from app.constants import TIMEZONE_CHOICES, VALID_TIMEZONES

default_timezone = None
if user and user.timezone in VALID_TIMEZONES:
    default_timezone = user.timezone
```

  - Передать `default_timezone` в контекст шаблона.

**Step 2: Учесть default_timezone в шаблоне**

- В `app/templates/schedules/form.html` найти блок select для `timezone`.
- Обновить условие `selected`:

```html
<option value="{{ tz_value }}"
  {% if schedule and schedule.timezone == tz_value %}
    selected
  {% elif not schedule and default_timezone and tz_value == default_timezone %}
    selected
  {% elif not schedule and not default_timezone and tz_value == 'Europe/Moscow' %}
    selected
  {% endif %}
>
  {{ tz_label }}
</option>
```

**Step 3: Добавить/обновить тесты расписаний**

- В `tests/test_pages/test_schedules.py` (или новом файле) добавить тест:

```python
@pytest.mark.asyncio
async def test_new_schedule_form_uses_user_timezone_by_default(client, db_session):
    ...
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_pages/test_schedules.py -v
```

---

### Task 5: Прогон всех тестов

**Files:** *(нет новых)*  
**Command:**

```bash
uv run pytest tests/ -v
```

Убедиться, что все тесты проходят, и фича профиля с таймзоной интегрирована без регрессий.

