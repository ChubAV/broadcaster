# Phase 6: Админ-панель — Pattern Map

**Mapped:** 2026-08-21
**Files analyzed:** 34 (создаются / правятся)
**Analogs found:** 30 / 34

Все пути — от корня репозитория `/source/broadcaster`. Номера строк сняты чтением исходников в этой сессии.

---

## File Classification

| Новый / правимый файл | Роль | Data flow | Ближайший аналог | Качество |
|---|---|---|---|---|
| `app/pages/admin.py` (переписывается: шесть маршрутов) | page router | request-response | `app/pages/history.py` (:1026 `history_list`) + сам `app/pages/admin.py` (:172) | exact |
| `app/pages/admin.py` — паршал опроса воркеров | page router (partial) | polling / request-response | `app/pages/dashboard_feed.py` (весь файл) | exact |
| `app/pages/admin.py` — POST «Перезапустить», POST «Снять задачу» | page router (action) | command | `app/pages/admin.py:499` `admin_toggle_free_access` | exact |
| `app/services/ops_state.py` (НОВЫЙ) | service | cache read (Redis) | `app/services/billing_cache.py:11-25` `_get_redis` | role-match |
| `app/services/loki_client.py` (НОВЫЙ) | service | external HTTP request-response | `app/services/max_container_manager.py:200+` `wait_for_container_ready` (httpx + timeout) + `billing_cache` (деградация) | role-match |
| предикат свежести heartbeat (общее место) | utility | transform | `app/services/max_container_manager.py:156-164` `_has_fresh_heartbeat` | exact (переиспользовать) |
| `app/application/admin/users_query.py` (НОВЫЙ) | application query | CRUD read + pagination | `app/application/analytics/send_analytics.py:764` `apply_history_filters` + `:797` `history_count` | exact |
| `app/application/admin/payments_query.py` (НОВЫЙ) | application query | CRUD read | там же | exact |
| `app/application/admin/incidents.py` (НОВЫЙ) | application (pure + query) | transform | `app/application/analytics/send_analytics.py:138` `send_metrics` (агрегаты одним round-trip) | role-match |
| `app/application/analytics/send_analytics.py` (ПРАВКА: `user_id: int \| None`) | application | CRUD read | сам файл, :138-208 | exact |
| `app/application/scheduling/use_cases.py` (ПРАВКА: блокировка) | application use case | batch | сам файл, :193-199 (`checked_users` / `check_limit`) | exact |
| `app/dependencies.py` — `get_current_user_id_active` (CR-01) | middleware / dependency | guard | `app/dependencies.py:95-134` `get_current_user_id_with_access` | exact |
| `app/dependencies.py` — `forbid_when_impersonating` (D-23) | middleware / dependency | guard | там же | exact |
| `app/dependencies.py` — `require_admin` (ПРАВКА под `act`) | middleware / dependency | guard | `app/dependencies.py:74-82` | exact |
| `app/services/auth_service.py` (ПРАВКА: claim `act`) | service | transform | сам файл, :17-29 | exact |
| `app/pages/common.py` — `check_is_admin` (ПРАВКА под `act`) | utility | transform | `app/pages/common.py:315-331` | exact |
| `app/pages/auth.py` — CR-01 в `login_submit`, CR-03 `secure` | page router | command | `app/pages/auth.py:40-57`, `:341` | exact |
| `app/pages/auth.py` — CR-02 (`secrets` вместо `random`) | utility | transform | нет аналога в `app/` | **нет** |
| `app/config.py` — `cookie_secure` | config | — | `app/config.py:77` `subscription_price` | exact |
| `app/pages/__init__.py` / `app/main.py` — навеска новых зависимостей | config / wiring | — | `app/pages/__init__.py:123-133`, `app/main.py:92-132` | exact |
| `app/templates/admin/{overview,users,workers,queue,logs,payments}.html` | template (page) | — | `app/templates/history/list.html:1-60` | exact |
| `app/templates/admin/includes/_tabs.html` | template (component) | — | `app/templates/base.html:37-56` (цикл `NAV_ITEMS` + `is-active`) | role-match |
| `app/templates/admin/includes/{worker_row,queue_row,log_row,incident_row}.html` | template (component) | — | `app/templates/accounts/partial_cards.html:32` (`data-row`, `--cols`) | exact |
| `app/templates/components/filter_chips.html` (ПЕРЕЕЗД) | template (component) | — | `app/templates/history/includes/filter_chips.html` | exact (тот же файл) |
| `app/templates/base.html` — полоса имперсонации | template (shell) | — | `app/templates/base.html:1-5` (импорт `badge`) | role-match |
| `app/templates/admin/includes/*_partial.html` (опрос воркеров) | template (partial) | polling | `app/templates/dashboard.html:163` + `dashboard/partial_feed.html` | exact |
| `nginx/nginx.conf.template` — HSTS | config | — | нет (в `nginx/` ноль вхождений `Strict-Transport-Security`) | **нет** |
| `tests/test_pages/test_admin_*.py` | test | — | `tests/test_pages/test_history.py`, фикстура `admin_client` (`tests/conftest.py:245-262`) | exact |
| `tests/test_pages/test_impersonation_gate.py` (AST) | test | — | `tests/test_pages/test_access_gate.py:97-120`, `:291-318` | exact |
| `tests/test_services/test_ops_state.py`, `test_loki_client.py` | test | — | `tests/test_billing_cache.py:26-45`, `tests/test_wa_container_manager.py:1-35` | exact |
| `.planning/REQUIREMENTS.md` — частичный вердикт по ADMIN-02 | docs | — | форма вердикта GRP-08 (Фаза 3, D-13/D-14) | role-match |
| удаление `/admin/groups-info*` + шаблоны + `tests/test_pages/test_admin_groups_info.py` | removal | — | — | n/a |

---

## Pattern Assignments

### `app/pages/admin.py` — шесть подразделов (page router, request-response)

**Аналог:** `app/pages/history.py` (фильтры, санация, счётчик, чипсы) и уже отгруженные обработчики самого `app/pages/admin.py`.

**Imports pattern** — `app/pages/admin.py:1-33` (копировать состав, дописывать по нужде):
```python
import structlog
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
from app.pages.common import templates

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])
```

**Auth pattern** — `require_admin` параметром обработчика, а не зависимостью роутера (`app/pages/admin.py:171-177`); `admin_router` включается БЕЗ `require_access` (`app/pages/__init__.py:132`) — это закреплено `test_the_api_admin_gate_does_not_ask_about_paid_access`:
```python
@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: str = "",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
```

**Форма ответа и обязательные ключи контекста** — `app/pages/admin.py:194-206`:
```python
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",   # подсветка раздела в сайдбаре
            "users": user_data,
            "search_query": q,
        },
    )
```
К этому добавляются `admin_tab` и `admin_tabs` (D-01). ⚠️ Ключ данных о ЧУЖОМ пользователе называется `target_*`, а не `user`/`access` — обоснование выписано в `app/pages/admin.py:253-260` («шелл кладёт в контекст СВОЙ словарь доступа»).

**Единый `now` на список + один запрос подписок** — `app/pages/admin.py:186-193`:
```python
    now = datetime.now(timezone.utc)
    subscriptions = await _active_subscriptions_by_user(db, [u.id for u in users])
    user_data = [
        {"user": u, "access": _access_view(subscriptions.get(u.id), now)}
        for u in users
    ]
```

---

### `app/application/admin/users_query.py` (application query, CRUD read + pagination)

**Аналог:** `app/application/analytics/send_analytics.py:764` (`apply_history_filters`) + `:797` (`history_count`), потребитель — `app/pages/history.py:1026-1157`.

**Core pattern — фильтры навешиваются на готовый `select`, счётчик считает по ТОМУ ЖЕ выражению** (`send_analytics.py:764-793`):
```python
def apply_history_filters(
    query,
    *,
    status: str | None = None,
    messenger_type: str | None = None,
    account_id: int | None = None,
    period: str | None = None,
    user: User | None = None,
):
    if status:
        query = query.where(SendLog.status == status)
    if messenger_type:
        query = query.where(SendLog.messenger_type == messenger_type)
    if account_id is not None:
        query = query.where(Group.account_id == account_id)
    cutoff = _period_cutoff(period, user)
    if cutoff is not None:
        query = query.where(SendLog.sent_at >= cutoff)
    return query
```

**Санация значений оси — замкнутое множество из объявления чипсов** (`app/pages/history.py:93-127`):
```python
def _values(chips) -> frozenset[str]:
    """Допустимые значения оси без варианта «все»."""
    return frozenset(value for value, _ in chips if value)

STATUS_VALUES = _values(STATUS_CHIPS)

def clean_choice(value: str | None, allowed: frozenset[str]) -> str | None:
    if not value:
        return None
    value = value.strip()
    return value if value in allowed else None
```
`clean_choice` и `parse_account_id` — **публичные имена по контракту** (докстринг `history.py:129-146` объясняет, почему без подчёркивания): админка уже их импортирует (`app/pages/admin.py:16-23`). Для осей D-32 («Доступ», «Состояние») завести свои `*_CHIPS` / `*_VALUES` рядом, той же формой.

**Пагинация + точный `COUNT` отдельным запросом** — `app/pages/history.py:1058-1062` и `:1109-1117`:
```python
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(PAGE_SIZE + 1)
    rows = list((await db.execute(query)).all())
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]
    ...
    history_total = await history_count(db, user_id=user.id, status=status, ...)
```
⚠️ Сегодняшний `app/repositories/user.py:17-30` (`get_all_users`, `search_users`) тянет таблицу без `limit` — D-33 закрывает это; форма поиска `or_(User.email.ilike(...), User.name.ilike(...))` переносится дословно.

---

### `app/services/ops_state.py` (service, cache read — Redis)

**Аналог:** `app/services/billing_cache.py:11-25` — ленивый модульный клиент, именованная точка для `patch`.

**Lazy-клиент + деградация** (`billing_cache.py:11-25`):
```python
_redis_client = None


def _get_redis():
    """Lazy-init Redis client for billing cache."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio
            settings = get_settings()
            _redis_client = redis.asyncio.from_url(settings.redis_url)
        except Exception:
            logger.warning("billing_cache_redis_unavailable")
            return None
    return _redis_client
```

**Каждое обращение обёрнуто, отсутствие Redis не роняет страницу** (`billing_cache.py:70-90`):
```python
    r = _get_redis()
    if r:
        try:
            cached = await r.get(cache_key)
            ...
        except Exception as e:
            logger.debug("access_cache_read_error", cache_key=cache_key, error=str(e))
```

**Свежесть heartbeat — НЕ `EXISTS`, а возраст** (`app/services/max_container_manager.py:20, 156-164`) — переиспользовать, а не писать своё 60:
```python
MAX_HEARTBEAT_STALE_SEC = 90

def _has_fresh_heartbeat(heartbeat: object) -> bool:
    """Accept only recent worker heartbeat timestamps in milliseconds."""
    try:
        heartbeat_ms = int(heartbeat)
    except (TypeError, ValueError):
        return False

    age_ms = int(time.time() * 1000) - heartbeat_ms
    return 0 <= age_ms <= MAX_HEARTBEAT_STALE_SEC * 1000
```
Нижняя граница `0 <= age_ms` несущая: heartbeat из будущего читается как несвежий.

**Пороги и лимиты — константами модуля с объяснением, а не литералами в разметке** (`app/pages/dashboard_feed.py:41-49`):
```python
FEED_LIMIT = 8
FEED_POLL_SECONDS = 20
```

---

### `app/services/loki_client.py` (service, external HTTP)

**Аналог:** `app/services/max_container_manager.py:200+` (`wait_for_container_ready` — `httpx` с явным `timeout`) для формы запроса, `billing_cache` — для формы деградации.

Форма, которую обязан дать сервис: явный `timeout`, `except` вокруг похода, возврат **пары «данные, признак недоступности»**, а не исключения — подраздел «Логи» при мёртвом Loki рисует `alert(..., variant='warning')` (`app/templates/components/alert.html:9`), а не `empty_state`. Именованная функция модуля обязательна: суита подменяет её через `patch` (см. §Shared Patterns → Подмена внешних систем).

Аналога **клиента Loki** в проекте нет — единственная по-настоящему новая точка вместе с `ops_state.py` и claim `act`.

---

### `app/dependencies.py` — `get_current_user_id_active` (CR-01) и `forbid_when_impersonating` (D-23)

**Аналог:** `app/dependencies.py:95-134` `get_current_user_id_with_access` — **соседняя** зависимость, вешаемая пер-роутерно.

**Core pattern** (`app/dependencies.py:129-134`):
```python
    user_id = await get_current_user_id(request, credentials, settings)

    allowed, _reason = await check_access(db, user_id)
    if not allowed:
        raise HTTPException(status_code=402, detail=ACCESS_EXPIRED_DETAIL)
    return user_id
```
Форма несущая: зависимость сначала зовёт существующую проверку, затем **отказывает исключением** — возвращаемое значение `include_router(dependencies=[...])` никуда не отдаёт.

⚠️ **`get_current_user_id` (`:26-41`) не трогать ни строкой.** `test_the_api_authentication_dependency_is_left_untouched` (`tests/test_pages/test_access_gate.py:291-318`) читает файл по AST и запрещает параметр `db`:
```python
    parameters = {argument.arg for argument in authenticator.args.args}
    assert "db" not in parameters, (...)
```

**Навеска — пер-роутерно, там же, где гейт доступа** (`app/pages/__init__.py:123-133`):
```python
router.include_router(ads_router, dependencies=[Depends(require_access)])
...
router.include_router(admin_router)
router.include_router(profile_router)
```

**Guard-форма с чтением пользователя** (`app/dependencies.py:74-82` `require_admin`) — образец «спросить существующее, затем отказать»:
```python
async def require_admin(request, db=Depends(get_db), settings=Depends(get_settings)) -> "User":
    user = await get_current_user(request, db, settings)
    if user.email != settings.admin_email:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

---

### `app/services/auth_service.py` — claim `act` (D-19)

**Аналог:** сам файл, `:17-29` — единственная точка выпуска и чтения токена.

```python
def create_access_token(user_id: int, secret_key: str, expires_minutes: int = 1440) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        payload["sub"] = int(payload["sub"])
        return payload
    except (JWTError, KeyError, ValueError):
        return None
```
⚠️ Приведение типа живёт **внутри** `decode_access_token` (`:26`) — значит и `act` приводится там же, иначе один читатель сравнит `"42"`, другой `42`. Новый параметр — keyword-only (`*, actor_id: int | None = None`), чтобы позиционные вызовы (`app/pages/auth.py:55`, `:340`, `app/routes/auth.py`) не менялись.

---

### `app/pages/auth.py` — CR-01 и CR-03

**Аналог:** сам файл, две установки cookie **одной формы** (`:56` и `:341`):
```python
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response
```
Обе правятся одинаково и читают `secure` из **настройки**, а не литерала (Ф-9 исследования). Форма настройки — `app/config.py:77` (`subscription_price`), там же `admin_email`. `max_age`/`expires` сегодня нет — это session cookie, и молча менять форму нельзя. `logout` (`auth.py:347-350`) удаляет cookie — набор атрибутов удаления обязан совпасть с набором установки (Pitfall 9 исследования).

Отказ во входе заблокированному строится по форме отказа в `login_submit` (`auth.py:50-53`) — тот же `TemplateResponse("auth/login.html", {"error": ...})`, а не редирект.

---

### `app/application/scheduling/use_cases.py` — блокировка в `collect_due_schedules` (D-30)

**Аналог:** сам файл, `:193-199` — мемоизация вердикта на пользователя уже есть, блокировка ложится соседним условием:
```python
        user_id = ad.user_id
        if user_id not in checked_users:
            checked_users[user_id] = await check_limit(session, user_id, "send")

        allowed, _reason = checked_users[user_id]
        if not allowed:
            schedule.next_run_at = compute_next_run_at(...)
            continue
```
⚠️ Пропуск **пересчитывает `next_run_at`** и делает `continue` — не оставляет расписание «висеть», иначе разблокировка выстрелит всеми накопленными слотами (тот же довод выписан ниже по файлу, :204-215).

---

### `app/pages/admin.py` — POST-действия «Перезапустить» (D-11) и «Снять задачу» (D-17)

**Аналог:** `app/pages/admin.py:499-588` `admin_toggle_free_access` — привилегированная операция над чужой сущностью.

**Core pattern** (`:552-588`):
```python
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    location = f"/admin/users/{user_id}"
    ...
    logger.warning(
        "free_access_toggle_without_subscription",
        admin_user_id=admin.id,
        target_user_id=target_user.id,
    )
    return RedirectResponse(url=location, status_code=302)
    ...
    logger.info(
        "free_access_toggled",
        admin_user_id=admin.id,
        target_user_id=target_user.id,
        has_free_access=subscription.has_free_access,
    )
```
Отсюда же берётся **форма следа D-24**: именованный ключ + оба идентификатора + новое значение. `impersonation_start` / `impersonation_stop` пишутся ровно так.

**Отказ не проглатывается молча** — он уходит в журнал именованным ключом и возвращает ту же страницу (`:566-577`). Для «Перезапустить» при недоступном Docker daemon — та же форма, плюс `except APIError` по образцу `app/services/wa_container_manager.py`.

**Панель подтверждения, а не `confirm()`** — `app/templates/components/modal.html:84`, использование `app/templates/admin/user_detail.html:169-173`:
```jinja
{{ modal(id='user-del-' ~ target_user.id,
         title='Удалить пользователя?',
         body='Пользователь ' ~ target_user.name ~ ' и все его данные будут удалены. Действие необратимо.',
         action='/admin/users/' ~ target_user.id ~ '/delete',
         confirm_label='Удалить') }}
```
Сигнатура: `modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post")`.

---

### `app/pages/admin.py` — паршал опроса «Воркеров» (D-12)

**Аналог:** `app/pages/dashboard_feed.py` целиком + `app/templates/dashboard.html:163`.

⚠️ Ключевое решение аналога, применимое буквально: **паршал бессрочного опроса живёт в СВОЁМ роутере**, вне `pages_router`, чтобы не платить четыре запроса `load_shell_context` на каждый тик (докстринг `dashboard_feed.py:1-29`). Гард входа при этом пишется в самом обработчике:
```python
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
```
Для админского паршала гард — `require_admin`, и роутер обязан попасть в перечни `test_access_gate.py` (`OPEN_ROUTERS` / `OPEN_API_ROUTERS`), иначе тест краснеет на «роутер, о котором этот тест не знает».

**Разметка опроса** (`app/templates/dashboard.html:163-167`) — интервал приходит **константой модуля**, первичная отрисовка тем же паршалом:
```jinja
<div id="dash-feed" data-feed hx-get="/dashboard/feed" hx-trigger="every {{ feed_poll_seconds }}s">
  {% include "dashboard/partial_feed.html" %}
</div>
```

**Опрос строки, а не блока** (альтернатива, если строка воркера обновляется отдельно) — `app/templates/accounts/partial_cards.html:32`:
```jinja
<div data-row id="account-row-{{ account.id }}" hx-get="/accounts/{{ account.id }}/sync-status"
     hx-trigger="every 5s" hx-swap="outerHTML" style="--cols: {{ ACCOUNT_COLS }}">
```

---

### Шаблоны подразделов `app/templates/admin/*.html`

**Аналог:** `app/templates/history/list.html:1-60`.

**Шапка шаблона — импорты компонентов и контракт «страница → шелл»** (`history/list.html:1-16`):
```jinja
{% extends "base.html" %}
{% from "components/alert.html" import alert %}
{% from "components/button.html" import button, link_button %}
{% from "components/empty_state.html" import empty_state %}
{% from "components/filters.html" import filters %}
{% from "components/mono.html" import mono %}
{% from "history/includes/filter_chips.html" import filter_chips %}

{% block title %}История — Broadcaster{% endblock %}
{# Заголовок раздела рендерит шапка шелла, собственного заголовка у страницы нет #}
{% block page_title %}История отправок{% endblock %}
{% block content %}
```

**Полоса чипсов** (`history/list.html:50-60`) — три оси одним действием, без «Применить»:
```jinja
<div class="chip-bar">
  {{ filter_chips(status_chips, status_filter, filter_params, 'status') }}
  {{ filter_chips(messenger_chips, filter_messenger, filter_params, 'messenger') }}
  {{ filter_chips(period_chips, filter_period, filter_params, 'period') }}
```

**Макрос чипсов** — `app/templates/history/includes/filter_chips.html:52`:
```jinja
{% macro filter_chips(options, active, base_params, param_name, base_path='/history') -%}
```
⚠️ Докстринг файла (строки 1-11) **сам предписывает переезд**: «второй потребитель (история пользователя в админке, Фаза 6) станет поводом для переезда» в `app/templates/components/`. Переезд ломает `test_template_inventory` (инвентарь фиксирует ровно 13 файлов библиотеки) — константу правит тот же план, что делает переезд, и `base_path` перестаёт быть умолчанием `/history`.

**Плашка недоступного Loki** — `alert(..., variant='warning')` в обёртке с data-атрибутом, по образцу `history/list.html:26-29`:
```jinja
{% if export_blocked %}
<div data-export-cap="{{ export_row_cap }}">
  {{ alert('Выгрузка не сформирована: ...', variant='warning') }}
</div>
{% endif %}
```

---

### `app/templates/admin/includes/_tabs.html` (вкладки шести подразделов)

**Аналог:** `app/templates/base.html:37-56` — цикл по перечню, объявленному в Python, с подсветкой `is-active` + `aria-current`:
```jinja
{% for item in nav_items %}
<a class="nav-item{% if active_page == item.key %} is-active{% endif %}"
   href="{{ item.href }}"{% if active_page == item.key %} aria-current="page"{% endif %}>
    <span class="nav-dot"></span>
    <span class="nav-label">{{ item.label }}</span>
</a>
{% endfor %}
```
Состав меню задан один раз в `app/pages/common.py::NAV_ITEMS` — `ADMIN_TABS` объявляется той же формой в `app/pages/admin.py`. Вкладки — обычные `<a href>`: ни `hx-`, ни `x-on:` (D-01, проверяемо по разметке).

---

### `app/templates/base.html` — полоса имперсонации (D-25)

**Аналог:** `app/templates/base.html:1-5` — единственный импорт шелла, с выписанным обоснованием («копия классов бейджа в шелле разъехалась бы с оригиналом молча»). Полоса встаёт в `{% block body %}` до `<div data-shell>` (`:22-27`), читает признак из контекста шелла тем же приёмом, что `access` / `nav_counts`:
```jinja
{% set shell = request.state.shell or {} %}
{% set access = shell.get('access', {}) %}
```
⚠️ Виджеты шелла рисуются условно и **молчат при отсутствии ключа** (комментарий `base.html:78-80`) — полоса имперсонации обязана вести себя так же: нет `act` — нет разметки.

---

### `app/application/analytics/send_analytics.py` — общесистемный вход (D-39)

**Аналог:** сам файл, `:138-144`:
```python
async def send_metrics(
    session: AsyncSession,
    *,
    user_id: int,
    now: datetime | None = None,
    window: timedelta = DEFAULT_WINDOW,
) -> SendMetrics:
    """Считает восемь чисел плиток ОДНИМ round-trip (D-38)."""
```
Правка — `user_id: int | None = None` с ветвлением при сборке `where` (`:196-208`), чтобы восемь условных агрегатов и `int(... or 0)` не дублировались. ⚠️ Граница владельца у `recent_feed` держится обязательным keyword `user_id` (докстринг `dashboard_feed.py:26-29`) — расширение `send_metrics` **не должно** заодно открыть общесистемную ветку у `recent_feed`.

---

### Тесты

**Фикстура администратора** — `tests/conftest.py:245-262` (готова, править не нужно):
```python
@pytest_asyncio.fixture
async def admin_client(client, test_settings):
    """Client with the httpOnly access_token cookie of the admin user."""
    await client.post("/api/auth/register", json={
        "email": test_settings.admin_email, "password": "testpass123", "name": "Admin User",
    })
    await client.post("/login", data={...}, follow_redirects=False)
    return client
```
Рядом: `client`, `db_session`, `auth_headers`, `authed_client`, `expired_client` (:96), `comped_client` (:141), `seed_group` (:201).

**Подмена Redis** — `tests/test_billing_cache.py:36-45`:
```python
    mock_db = AsyncMock()
    with patch("app.services.billing_cache.check_access", return_value=(True, "")) as mock_check:
        with patch("app.services.billing_cache._get_redis", return_value=None):
```

**Подмена Docker** — `tests/test_wa_container_manager.py:22-27`:
```python
@patch("app.services.wa_container_manager.get_settings")
@patch("app.services.wa_container_manager._get_docker_client")
def test_start_container_new(mock_docker, mock_settings):
    client = MagicMock()
    mock_docker.return_value = client
    client.containers.get.side_effect = NotFound("not found")
```
Отсюда — ответ на дискрецию «как проверять Loki, Docker и Redis в суите»: `unittest.mock.patch` по **именованной функции модуля**, нового пакета не требуется. Именно поэтому чтение Redis и Loki обязано быть сервисом, а не кодом в обработчике.

**AST-гейт запретов имперсонации (D-23)** — `tests/test_pages/test_access_gate.py:97-120`, копируется целиком:
```python
def _routers_with_dependency(source: Path, dependency: str) -> dict[str, bool]:
    """Каждый вызов `.include_router(...)` → «висит ли на нём названная зависимость»."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    found: dict[str, bool] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "include_router":
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue
        router_name = node.args[0].id
        gated = False
        for keyword in node.keywords:
            if keyword.arg != "dependencies":
                continue
            for element in ast.walk(keyword.value):
                if isinstance(element, ast.Name) and element.id == dependency:
                    gated = True
        found[router_name] = gated
    return found
```
Перечни выписываются **явно** (`GATED_ROUTERS` :44-51, `OPEN_ROUTERS` :60-66) с замыкающим утверждением (`:285-288`):
```python
    assert set(included) == GATED_API_ROUTERS | OPEN_API_ROUTERS, (
        "в сборку приложения включён роутер, о котором этот тест не знает — "
        "решение «закрывает ли его истёкший доступ» не принято"
    )
```
⚠️ Для D-22 пер-роутерного гейта **недостаточно** (повтор отправки живёт в `history_router`, смена пароля — в `auth_router`): разбор придётся расширить обходом `@router.post/put/delete` по AST. Это самая сложная по форме утверждения задача фазы — отдельным планом.

**Гейт-запрет на правку аутентификатора** — `test_access_gate.py:291-318` (см. выше, раздел `dependencies.py`).

**Греп-гейт метрической модели** — `tests/test_application/test_no_metering_remains.py:54-79`: `FORBIDDEN_NAMES` не содержит голого `plan`, то есть D-42 обходить или расширять гейт не требуется.

---

## Shared Patterns

### Проверка прав администратора
**Источник:** `app/dependencies.py:74-82` (`require_admin`), `app/pages/common.py:331` (`check_is_admin`).
**Применять к:** всем шести маршрутам подразделов, всем POST-действиям админки, паршалу опроса.
Форма — параметр обработчика `admin: User = Depends(require_admin)`, а не зависимость роутера: `admin_router` включается **без** `require_access` (`app/pages/__init__.py:132`), и это закреплено `test_the_api_admin_gate_does_not_ask_about_paid_access`.

### Ленивый клиент внешней системы + деградация
**Источник:** `app/services/billing_cache.py:11-25` и `:70-90`.
**Применять к:** `ops_state.py`, `loki_client.py`.
Модульный `_get_*()` с `try/except` и `logger.warning` при недоступности; каждое обращение обёрнуто отдельно; недоступность внешней системы **никогда** не превращается в 500 страницы.

### Именованный след действия в structlog
**Источник:** `app/pages/admin.py:576-586`.
**Применять к:** `impersonation_start` / `impersonation_stop` (D-24), перезапуск воркера (D-11), снятие задачи (D-17), отказ во входе заблокированному (D-30).
```python
    logger.info(
        "free_access_toggled",
        admin_user_id=admin.id,
        target_user_id=target_user.id,
        has_free_access=subscription.has_free_access,
    )
```
Имя события + оба идентификатора + новое значение. Без нового значения выдача неотличима от отзыва.

### Отказ, названный словами, а не проглоченный
**Источник:** `app/pages/admin.py:566-577` (журнал + тот же редирект), `app/pages/history.py:1122-1128` (`export_blocked`), `app/templates/history/list.html:26-29` (`alert(variant='warning')`).
**Применять к:** недоступный Loki, недоступный Docker daemon, отсутствие задачи при `LREM`, вход заблокированного.

### Значение из адреса сравнивается ЦЕЛИКОМ по закрытому словарю
**Источник:** `app/pages/history.py:1141-1146` (`retry_notice`), `:1136` (`export_blocked`), `clean_choice` (`:103-127`).
**Применять к:** всем query-параметрам новых подразделов (фильтры «Логов», «Платежей», «Пользователей», окно 15м/1ч/24ч).
Неизвестное значение → фильтр не применён / плашка не рисуется. Иначе чужая ссылка рисует администратору сообщение о событии, которого не было.

### Панель подтверждения вместо `confirm()`
**Источник:** `app/templates/components/modal.html:84`, пример `app/templates/admin/user_detail.html:169-173`.
**Применять к:** «Перезапустить воркер» (D-11), «Снять задачу» (D-17).

### Пороговые числа — константы модуля с объяснением
**Источник:** `app/pages/dashboard_feed.py:41-49`, `app/services/max_container_manager.py:20`, `app/pages/history.py:45` (`PAGE_SIZE = 30`).
**Применять к:** интервалу опроса воркеров, порогу свежести heartbeat (переиспользовать `MAX_HEARTBEAT_STALE_SEC = 90`), размеру страницы пользователей, потолку логов, окну «всплеска отказов», порогам «залипшего платежа» и «вставшего планировщика».

### Контекст шаблона: обязательные ключи и защита от коллизии имён
**Источник:** `app/pages/admin.py:194-206` и комментарий `:253-260`.
**Применять к:** всем шести подразделам.
Обязательны `request`, `user` (= администратор), `is_admin: True`, `active_page: "admin"`; всё, что относится к чужой учётной записи, именуется `target_*`.

---

## No Analog Found

| Файл | Роль | Data flow | Причина |
|---|---|---|---|
| `app/services/loki_client.py` (сам протокол `query_range`/LogQL) | service | external HTTP | Loki в `app/` не читался ни разу; форма `httpx` + timeout берётся у `max_container_manager.wait_for_container_ready`, а контракт API — из RESEARCH §Code Example 1 |
| `app/pages/auth.py` — CR-02 (`secrets` вместо `random.randint`) | utility | transform | `secrets` в `app/` не используется; свидетель обязан утверждать **источник** (разбор дерева), а не значение — RESEARCH |
| `nginx/nginx.conf.template` — HSTS | config | — | `Strict-Transport-Security` в `nginx/` — ноль вхождений; добавляется **только** в HTTPS-шаблон (Ф-9) |
| claim `act` (семантика RFC 8693) | service | transform | форма функций есть (`auth_service.py:17-29`), формы claim — нет; выбор «объект vs скаляр» записать решением |

---

## Metadata

**Analog search scope:** `app/pages/`, `app/services/`, `app/application/`, `app/repositories/`, `app/templates/`, `tests/`, `nginx/`, `monitoring/`
**Files read this session:** 20
**Pattern extraction date:** 2026-08-21
