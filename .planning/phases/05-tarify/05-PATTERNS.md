# Phase 5: Тарифы — Pattern Map

**Mapped:** 2026-08-15
**Files analyzed:** 18 (12 code/template, 5 test, 1 doc)
**Analogs found:** 17 / 18

Источник списка файлов: `05-CONTEXT.md` §Integration Points + `05-RESEARCH.md` §Recommended Project Structure, §Wave 0 Gaps.

## File Classification

| New/Modified File | New/Mod | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|---------|------|-----------|----------------|---------------|
| `app/application/billing/plan_usage.py` | NEW | application/analytics module | batch aggregate (read-only) | `app/application/analytics/send_analytics.py` | exact |
| `app/application/analytics/send_analytics.py` | MOD | application module | batch aggregate | сам себе (`_period_cutoff`, `history_count`) | exact |
| `app/config.py` | MOD | config | — | `message_packages` / `parsed_message_packages` в том же файле | exact |
| `app/models/payment.py` | MOD | model | — | соседние колонки того же файла + `app/models/subscription.py` | exact |
| `alembic/versions/0017_payment_kind_and_plan.py` | NEW | migration | schema DDL | `alembic/versions/0014_sync_result_and_group_missing.py` (add_column) + `0016` (шапка/докстринг) | exact |
| `app/services/payment_service.py` | MOD | service | request-response + external HTTP + webhook | сам себе (`create_payment` / `handle_webhook`) | exact |
| `app/pages/billing.py` | REWRITE | page router (GET) | request-response | `app/pages/dashboard.py` | exact |
| `app/pages/billing.py` (обработчик формы оплаты) | NEW | page router (POST) | request-response / PRG | `app/pages/history.py:891` `history_retry` | exact |
| `app/routes/billing.py` | MOD | API router (webhook guard) | event-driven | `app/pages/history.py:345` `_is_same_origin` (форма гарда источника) | role-match |
| `app/templates/billing/balance.html` | REWRITE | template | server render | сам себе + `app/templates/dashboard.html` | exact |
| `app/templates/billing/includes/plan_card.html` | NEW | template partial (macro) | server render | `app/templates/dashboard/includes/metric_tile.html` | exact |
| `app/templates/billing/includes/usage_meters.html` | NEW | template partial (macro) | server render | `metric_tile.html` + `components/progress.html` | exact |
| `app/templates/billing/includes/payment_row.html` | NEW | template partial (macro) | server render | `balance.html:91-119` (история операций) | exact |
| `app/templates/billing/plans.html` | DELETE | template | — | Фаза 1 (снос 6 шаблонов), Фаза 3 (03-11) | precedent |
| `app/static/css/app.css` (`[data-plans]`) | MOD | style | — | `[data-metrics]` (`app.css:1131-1133`) | exact |
| `tests/test_application/test_plan_usage.py` | NEW | test (unit) | — | `tests/test_application/test_send_analytics.py` | exact |
| `tests/test_pages/test_billing_section.py` | NEW | test (integration) | — | `tests/test_pages/test_history_retry.py` | exact |
| `tests/test_migrations/test_0017_payment_kind_and_plan.py` | NEW | test (migration) | — | `tests/test_migrations/test_0016_send_logs_user_sent_at.py` | exact |
| `tests/test_services/test_payment_service.py` | MOD | test (unit) | — | сам себе | exact |
| `tests/test_pages/test_responsive_markup.py` | MOD | test (integration) | — | сам себе (`:1244`, `:1985-1987`) | exact |
| `.planning/REQUIREMENTS.md` | MOD | doc | — | — | n/a (правка документа, D-13) |

## Pattern Assignments

---

### `app/application/billing/plan_usage.py` (NEW — application module, read-only aggregate)

**Analog:** `app/application/analytics/send_analytics.py`

**Docstring pattern — модуль обязан выписать свои границы** (`send_analytics.py:1-37`, сокращённо):

```python
"""Аналитика журнала отправок — один модуль на дашборд, историю и Фазу 6.

ЧЕГО МОДУЛЬ НЕ ДЕЛАЕТ:

- не читает `Request`, не знает про cookie и про то, кто вошёл: владелец
  приезжает обязательным именованным `user_id`, а ветки «по всем пользователям»
  здесь нет вовсе — её отсутствие и есть проверяемая форма T-04-01;
- ничего не пишет в БД и не коммитит: все функции только читают;
- не знает про Jinja, шаблоны и разметку: наружу выходят числа и запросы, а не
  строки для показа;
...
ПЕРЕНОСИМОСТЬ АГРЕГАЦИИ. Тесты проекта идут на SQLite, бой работает на
PostgreSQL. ... Поэтому окна режутся сравнением `sent_at` с посчитанными в
Python границами ...
"""
```

**Imports pattern** (`send_analytics.py:39-54`):

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.send_log import SendLog
from app.models.user import User
```

**Отложенный импорт таймзоны — обязателен (цикл pages → application)** (`send_analytics.py:743-751`):

```python
        # Импорт отложен в тело функции НАМЕРЕННО. `app/pages/__init__.py`
        # собирает роутеры разделов, поэтому импорт `app.pages.common` на
        # верхнем уровне этого модуля замыкает цикл: pages → dashboard →
        # send_analytics → pages. Цикл рвётся только отложенным импортом или
        # копией хелпера таймзоны — копия завела бы второй источник одного
        # правила.
        from app.pages.common import _get_timezone_for_user

        tz = _get_timezone_for_user(user)
        local_midnight = datetime.now(tz).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return local_midnight.astimezone(timezone.utc)
```

→ Копировать буквально для `current_month_bounds_utc` (D-11): граница считается в зоне пользователя и переводится в UTC.

**Aware/naive хелпер — звать, не переписывать** (`send_analytics.py:81-100`):

```python
def normalize_utc(value: datetime | None) -> datetime | None:
    """Доводит значение `sent_at` до aware-UTC. ..."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
```

→ Обязателен на `Subscription.expires_at` и `Payment.confirmed_at` (RESEARCH §Pitfall 3).

**Core aggregate pattern — счёт одним запросом, владелец именованным аргументом** (`send_analytics.py:817-822`):

```python
    query = (
        select(func.count())
        .select_from(SendLog)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
```

**Именованные константы модуля с обоснованием** (`send_analytics.py:64-78`) — образец для `PLAN_AXES` / `UNLIMITED`:

```python
STATUS_OK = "ok"
STATUS_FAIL = "fail"
STATUS_ACCOUNT_DISCONNECTED = "account_disconnected"

FAILED_STATUSES = (STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED)

# Ширина окна плиток по умолчанию: скользящие сутки от момента запроса (D-02).
DEFAULT_WINDOW = timedelta(hours=24)
```

---

### `app/config.py` (MOD — config)

**Analog:** тот же файл, `message_packages`.

**Настройка + `parsed_`-свойство** (`app/config.py:59-61` и `74-76`):

```python
    # Billing — message balance
    free_monthly_messages: int = 10
    message_packages: str = '[{"name":"100 сообщений","count":100,"price":"149.00"},...]'

    @property
    def parsed_message_packages(self) -> list[dict]:
        return json.loads(self.message_packages)
```

→ Новая `plan_limits: str = '[...]'` + `parsed_plan_limits`. Цена — машинная строка `"1490.00"` (RESEARCH A3), безлимит — JSON `null` (A2), Free входит третьей записью (A5). Свойство зовётся **один раз в обработчике**, не из Jinja (§Pitfall 10) — образец в `app/pages/billing.py:24`:

```python
    packages = settings.parsed_message_packages if settings.yookassa_enabled else []
```

---

### `app/models/payment.py` (MOD — model)

**Analog:** соседние колонки того же файла.

**Стиль колонок** (`app/models/payment.py:19-23`):

```python
    status: Mapped[str] = mapped_column(String(50), default="pending")
    amount_value: Mapped[str] = mapped_column(String(50))
    amount_currency: Mapped[str] = mapped_column(String(10), default="RUB")
    messages_count: Mapped[int] = mapped_column(Integer)
    package_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

→ `kind: Mapped[str] = mapped_column(String(50), default="package")`, `plan: Mapped[str | None] = mapped_column(String(50), nullable=True)`, `messages_count: Mapped[int | None] = mapped_column(Integer, nullable=True)`. Строка, не `sa.Enum` (RESEARCH §Alternatives, `app/constants.py:24-27`).

---

### `alembic/versions/0017_payment_kind_and_plan.py` (NEW — migration)

**Analog:** `alembic/versions/0014_sync_result_and_group_missing.py` (add_column), шапка/номерация — `0016`.

**Шапка ревизии** (`0016_send_logs_user_sent_at.py:38-44`):

```python
Revision ID: 0016
Revises: 0015
"""
from alembic import op

revision = "0016"
down_revision = "0015"
```

→ `revision = "0017"`, `down_revision = "0016"` (НЕ `"0013"` — `05-CONTEXT.md` здесь устарел).

**Правило литералов — обязательно** (`0014:33-36`):

```python
# Литералы типов выписаны здесь, а не импортированы из app.models: ревизия
# обязана описывать схему на СВОЙ момент времени (правило ревизии 0013).
# Импорт связал бы уже применённую миграцию с текущим кодом, и правка модели
# задним числом изменила бы смысл давно выполненного шага.
```

**upgrade/downgrade — симметричные, additive** (`0014:39-57`):

```python
def upgrade():
    op.add_column(
        "messenger_accounts",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    ...

def downgrade():
    op.drop_column("groups", "missing_since")
    ...
```

→ Отличие фазы: `kind` добавляется с `server_default="package"` (backfill умолчанием, Runtime State Inventory), а снятие `NOT NULL` с `messages_count` идёт через `op.batch_alter_table("payments")` — SQLite не умеет `ALTER COLUMN`.

---

### `app/services/payment_service.py` (MOD — service, external HTTP + webhook)

**Analog:** сам себе. Ветвление, а не второй контур (D-01, Pattern 1).

**Существующая сигнатура и метаданные** (`payment_service.py:23-50`):

```python
async def create_payment(
    db: AsyncSession,
    user_id: int,
    package_name: str,
    messages_count: int,
    price: str,
) -> dict:
    _configure_yookassa()
    settings = get_settings()

    idempotency_key = str(uuid.uuid4())
    payment = YooPayment.create(
        {
            "amount": {"value": price, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
            },
            "capture": True,
            "description": f"Пополнение баланса: {package_name}",
            "metadata": {
                "user_id": str(user_id),
                "messages_count": str(messages_count),
                "package_name": package_name,
            },
        },
        idempotency_key,
    )
```

→ Добавляются `kind: str` и `plan: str | None = None`; `messages_count: int | None`; `metadata` получает `"kind"`. **`metadata` не источник истины для обработчика** — решает колонка `kind` из БД.

**Порядок проверок вебхука — сохранить** (`payment_service.py:78-103`):

```python
async def handle_webhook(
    db: AsyncSession, event: str, payment_data: dict
) -> bool:
    if event != "payment.succeeded":      # ← D-16 расширяет до двух событий
        return False

    obj = payment_data.get("object", {})
    yookassa_id = obj.get("id")
    if not yookassa_id:
        logger.warning("webhook_missing_payment_id")
        return False

    result = await db.execute(
        select(Payment).where(Payment.yookassa_payment_id == yookassa_id)
    )
    db_payment = result.scalar_one_or_none()
    if db_payment is None:
        logger.warning("webhook_payment_not_found", yookassa_id=yookassa_id)
        return False

    if db_payment.status == "succeeded":   # ← ИДЕМПОТЕНТНОСТЬ, до ветвления по kind
        logger.info("webhook_payment_already_processed", yookassa_id=yookassa_id)
        return True

    db_payment.status = "succeeded"
    db_payment.confirmed_at = datetime.now(timezone.utc)
```

**Логирование — только `event` / `id` / `user_id` / `amount`, никогда тело уведомления** (`payment_service.py:64-70, 116-122`):

```python
    logger.info(
        "payment_created",
        user_id=user_id,
        yookassa_id=payment.id,
        amount=price,
        messages=messages_count,
    )
```

**Upsert `Subscription` — тем же запросом, что шелл** (`app/pages/common.py:397-404`, цит. RESEARCH §Pitfall 5):

```python
    subscription = (
        await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
```

---

### `app/pages/billing.py` (REWRITE — page router, GET + POST)

**Analog (GET):** `app/pages/dashboard.py`.

**Обработчик — гард входа, вызовы модулей, один `TemplateResponse`** (`dashboard.py:64-79, 108-116, 142`):

```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Плитки. Страница агрегатов НЕ СЧИТАЕТ: восемь чисел приходят одним
    # запросом из модуля аналитики, который зовут и история, и Фаза 6 (D-35).
    metrics = await send_metrics(db, user_id=user.id)
    ...
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "metrics": metrics,
            ...
            "active_page": "dashboard",
        },
    )
```

**Чтение уже посчитанного шелла вместо второго запроса** (`dashboard.py:119-121, 127`) — прямой образец для осей «Объявления» и «Аккаунты» (Pattern 3):

```python
            "next_step": dashboard_next_step(
                getattr(request.state, "shell", {}).get("nav_counts")
            ),
            "sessions": getattr(request.state, "shell", {}).get("sessions") or [],
```

**Analog (POST-форма оплаты):** `app/pages/history.py:891-961` `history_retry`.

**Порядок проверок + PRG** (`history.py:946-961`):

```python
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if not _is_same_origin(request):
        return Response(status_code=403)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)
    ...
    return RedirectResponse(url=f"/history?retry={RETRY_BUSY}", status_code=302)
```

→ Для оплаты: гард входа → сверка источника → валидация `plan` по списку конфига (никогда цена из формы) → `create_payment` → `RedirectResponse(url=result["confirmation_url"], status_code=302)`.

**Потолок списка — проверять и называть, а не обрезать молча** (`history.py:749-770`):

```python
    # ПОТОЛОК ПРОВЕРЯЕТСЯ ДО КОНСТРУИРОВАНИЯ ПОТОКА (D-27, T-04-33). ...
    total = await history_count(...)
    if total > EXPORT_ROW_CAP:
        params = history_filter_params(status, messenger, account_id_int, period)
        params["export"] = EXPORT_TOO_MANY
        return RedirectResponse(url=f"/history?{urlencode(params)}", status_code=302)
```

→ Образец для технического потолка списка платежей (D-17).

---

### `app/routes/billing.py` (MOD — API router, webhook)

**Analog:** текущий обработчик + форма гарда из `history.py:345` `_is_same_origin` (гард с выписанной границей защиты).

**Точка врезки IP-проверки** (`app/routes/billing.py:69-84`):

```python
@router.post("/webhook")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not settings.yookassa_enabled:
        raise HTTPException(status_code=403, detail="Payments are disabled")
    try:
        body = await request.json()
        event = body.get("event", "")
        payment_data = body

        logger.info("yookassa_webhook_received", event=event)

        processed = await handle_webhook(db, event, payment_data)
```

→ `SecurityHelper().is_ip_trusted(client_ip)` встаёт **сразу после** проверки `yookassa_enabled`, до `await request.json()`.

**Валидация идентификатора по списку конфига** (`app/routes/billing.py:52-58`) — образец для валидации `plan` из формы:

```python
    if not settings.yookassa_enabled:
        raise HTTPException(status_code=403, detail="Payments are disabled")
    packages = settings.parsed_message_packages
    if data.package_index < 0 or data.package_index >= len(packages):
        raise HTTPException(status_code=400, detail="Invalid package index")

    pkg = packages[data.package_index]
```

**Форма докстринга гарда с названной границей** (`history.py:346-372`) — копировать структуру для IP-проверки: ЗАЧЕМ → ПРАВИЛО → ⚠️ НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ (здесь: `X-Forwarded-For` за nginx, A1).

---

### `app/templates/billing/balance.html` (REWRITE — template)

**Analog:** сам себе.

**Шапка шаблона: extends + импорты компонентов** (`balance.html:1-13`):

```jinja
{% extends "base.html" %}
{% from "components/card.html" import card_open, card_close %}
{% from "components/table.html" import rowhead, row_open, row_close, cell %}
{% from "components/badge.html" import badge %}
{% from "components/empty_state.html" import empty_state %}
{% from "components/mono.html" import mono %}
{% from "components/progress.html" import progress %}

{% block title %}Тарифы — Broadcaster{% endblock %}

{# Контракт «страница → шелл» (План 01): заголовок раздела рендерит шапка. #}
{% block page_title %}Тарифы{% endblock %}
{% block page_subtitle %}Баланс сообщений и история операций{% endblock %}
```

**Чтение шелла внутри `content`** (`balance.html:24`):

```jinja
{% set quota = request.state.shell.get('quota', {}) if request.state.shell else {} %}
```

**Табличные примитивы + `data-cell-label`** (`balance.html:32-41, 93-113`) — прямой образец истории платежей (RESEARCH §Code Example 3):

```jinja
{% set TX_COLS = 'minmax(132px,1fr) 128px 92px 100px minmax(160px,2fr)' %}
{% set TX_COLUMNS = ['Дата', 'Тип', 'Кол-во', 'Баланс', 'Описание'] %}
{% set TX_LABELS = {
  'purchase': ('Покупка', 'success'),
  ...
} %}

    {{ rowhead(columns=TX_COLUMNS, cols=TX_COLS) }}
    {% for tx in transactions %}
    {%- set tx_label = TX_LABELS.get(tx.type) -%}
    {{ row_open(cols=TX_COLS) }}
      {{- cell(text=tx.created_at[:16] if tx.created_at else '', mono=true, muted=true) }}
      {%- call cell() %}
        {%- if tx_label %}{{ badge(tx_label[0], tx_label[1]) }}{% else %}{{ mono(tx.type) }}{% endif -%}
      {%- endcall %}
      {%- call cell() %}
        <span data-cell-label>Кол-во</span>
        {{- mono(('+' if tx.amount > 0 else '') ~ tx.amount, 'ok' if tx.amount > 0 else 'danger') -}}
      {%- endcall %}
    {{ row_close() }}
    {% endfor %}
```

**Ветка выключенных платежей** (`balance.html:87-89`) — образец D-21:

```jinja
  {% elif not payments_enabled and not balance_info.is_unlimited %}
  {{ empty_state('Пополнение баланса доступно через администратора') }}
  {% endif %}
```

**Что сносится** (`balance.html:80-85` и `123-146`): `onclick="purchasePackage(...)"` и весь `<script>` с `fetch` + `alert()` (D-20).

---

### `app/templates/billing/includes/*.html` (NEW — партиалы раздела)

**Analog:** `app/templates/dashboard/includes/metric_tile.html`.

**Партиал — МАКРОС с явными параметрами и докстрингом-комментарием** (весь файл, `metric_tile.html:1-31`):

```jinja
{# Плитка метрики дашборда с дельтой к предыдущему окну (DASH-01, макет 387-392).

   Это МАКРОС, а не include: импортированные шаблоны Jinja контекста
   вызывающего не получают, поэтому `label`, `value`, `delta` и `tone` — явные
   параметры. Ошибка в имени параметра проявится не исключением, а ПУСТОЙ
   плиткой при статусе 200, поэтому отрисовка реальных чисел закреплена тестом
   test_dashboard_tile_counts_last_day_sends.

   Импорт: {% from "dashboard/includes/metric_tile.html" import metric_tile %} #}

{% from "components/card.html" import card_open, card_close %}
{% from "components/mono.html" import mono %}

{% macro metric_tile(label, value, delta, tone='neutral') -%}
{{ card_open() }}
  {{ mono(label, 'muted', upper=true) }}
  <div data-metric-line>
    <span data-metric-value>{{ value }}</span>
    <span data-metric-delta data-tone="{{ tone }}">{{ '+' if delta > 0 else '' }}{{ delta }}</span>
  </div>
{{ card_close() }}
{%- endmacro %}
```

→ `plan_card`, `usage_meter`, `payment_row` пишутся ровно этой формой. **Остаются в `billing/includes/`, не в `components/`** — иначе `assert len(components) == 13` (§Pitfall 8в) требует правки той же задачей.

**Метр — через готовый макрос, кламп внутри** (`components/progress.html:7-15`):

```jinja
{% macro progress(percent, label=None, variant='accent') -%}
{%- set raw = percent|int -%}
{%- set pct = 0 if raw < 0 else (100 if raw > 100 else raw) -%}
<div class="progress progress--{{ variant }}">
  {%- if label %}<span class="progress__label">{{ label }}</span>{% endif %}
  <div class="progress__track" role="progressbar" aria-valuenow="{{ pct }}" aria-valuemin="0" aria-valuemax="100">
    <div class="progress__bar" style="width: {{ pct }}%"></div>
  </div>
</div>
{%- endmacro %}
```

→ Кламп и превышение лимита макрос закрывает сам; делить на лимит только под условием (безлимит = `null`).

---

### `tests/test_application/test_plan_usage.py` (NEW — unit test)

**Analog:** `tests/test_application/test_send_analytics.py`.

**Докстринг файла + правило явного времени** (`test_send_analytics.py:1-10`):

```python
"""Юнит-покрытие модуля аналитики отправок (app/application/analytics).

Модуль — единственный источник агрегатов журнала для дашборда, истории и
Фазы 6 (D-35). Этот файл держит его контракт: окно скользящих суток, три
статуса, охват групп, изоляция по владельцу и перенос фильтров истории.

Все посевы ставят `sent_at` ЯВНО. У колонки есть `server_default=func.now()`,
и запись без явного времени попала бы в окно «сейчас» — то есть в текущее окно
всегда, независимо от того, что проверяет тест.
"""
```

**Фиксированное «сейчас» + хелперы посева с таймзоной пользователя** (`test_send_analytics.py:47-59`):

```python
NOW = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)


async def _user(
    db: AsyncSession,
    email: str = "metrics@test.com",
    tz_name: str = "UTC",
) -> User:
    user = User(email=email, password_hash="x", name="U", timezone=tz_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

→ Тест границы месяца (D-11) строится этим же приёмом: `_user(tz_name="Europe/Moscow")` + `sent_at` первого числа в 00:30 местного времени.
→ Счётчик запросов (`query_count`): образец `from sqlalchemy import event` уже импортирован в этом файле (`:16`).

---

### `tests/test_pages/test_billing_section.py` (NEW — integration test)

**Analog:** `tests/test_pages/test_history_retry.py`.

**Докстринг «что здесь есть и чего здесь НЕТ»** (`test_history_retry.py:1-19`, сокращённо):

```python
"""Повтор отправки из записи истории — пользовательская половина HIST-04.

Это ЕДИНСТВЕННОЕ отступление фазы от правила «интерфейс, а не функция»: здесь
заводится настоящее действие, и ведёт оно прямо в боевую очередь отправки.
...
Файл собственный, а не дописка к `test_history.py`: тот держит фильтры и
счётчик, и смешивать с ними единственное необратимое действие раздела значило
бы прятать его среди чтения.

ЧЕГО ЗДЕСЬ НЕТ. ... два теста одного свойства расходятся при первой правке.
"""
```

**Imports** (`test_history_retry.py:22-47`):

```python
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.pages import history as history_module

HISTORY_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "history.py"
```

→ `BILLING_PY = ... / "app" / "pages" / "billing.py"` и `BALANCE_HTML = ... / "app" / "templates" / "billing" / "balance.html"` для проверок по исходнику (`degrades_without_alpine`, отсутствие `alert(`/`fetch(`).

---

### `tests/test_migrations/test_0017_payment_kind_and_plan.py` (NEW — migration test)

**Analog:** `tests/test_migrations/test_0016_send_logs_user_sent_at.py`.

**Докстринг с четырьмя обязательными оговорками** (`test_0016:1-31`, сокращённо):

```python
"""Round-trip ревизии 0016: составной индекс (user_id, sent_at) на send_logs.

Файл существует по той же причине, что `test_0013_ad_status.py` ...: суита
строит схему через `Base.metadata.create_all` (tests/conftest.py) и о
существовании Alembic не знает, поэтому текст ревизии не исполняется НИ В
ОДНОМ обычном тесте.

**Файловая база, а не `:memory:`.** Alembic открывает собственное соединение ...

**Тест синхронный.** `alembic/env.py` в online-режиме вызывает `asyncio.run` ...

**Стартовая точка — `0015`, целевая — `0016`, обе названы явно.** ... Имя `head`
целью не берётся: оно перестанет означать эту ревизию при следующем пополнении
истории.
"""
```

**Каркас** (`test_0016:33-88`):

```python
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"

SEND_LOGS_AT_0015 = """
CREATE TABLE send_logs (...);
"""

INSERT_SEND_LOG = ("INSERT INTO send_logs ... VALUES (...)")


def _index_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        return {row[0] for row in rows}
    finally:
        conn.close()
```

→ Для `0017`: `PAYMENTS_AT_0016` (состав по `app/models/payment.py`, `messages_count INTEGER NOT NULL`), посев одной строки старого платежа, `_columns()` через `PRAGMA table_info(payments)`, штамп `0016` → `upgrade("0017")` → проверки: `kind`/`plan` существуют, `messages_count` nullable, старая строка получила `kind='package'`; `downgrade` возвращает схему и строк не теряет.

---

### `tests/test_services/test_payment_service.py` (MOD)

**Analog:** сам себе.

**Мок ЮKassa — установленный образец** (`test_payment_service.py:18-37`):

```python
    mock_yoo_payment = MagicMock()
    mock_yoo_payment.id = "yoo_123"
    mock_yoo_payment.confirmation = MagicMock()
    mock_yoo_payment.confirmation.confirmation_url = "https://yookassa.ru/pay/123"

    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "https://app.com/billing"
    mock_settings.app_name = "Broadcaster"

    with patch("app.services.payment_service.get_settings", return_value=mock_settings), \
         patch("app.services.payment_service.YooPayment.create", return_value=mock_yoo_payment):
        result = await create_payment(...)
```

**Мок инвалидации кэша в вебхуке** (`:61`):

```python
    with patch("app.services.payment_service.invalidate_balance_cache", new_callable=AsyncMock):
```

**Тест, который ломается намеренно** (`:72-79`) — переписать на действительно неизвестное событие (`refund.succeeded`), плюс новый тест настоящей отмены:

```python
@pytest.mark.asyncio
async def test_handle_webhook_wrong_event(db_session):
    processed = await handle_webhook(
        db_session,
        event="payment.canceled",   # ← после D-16 событие ЗНАКОМОЕ, имя теста лжёт
        payment_data={"object": {"id": "yoo_789"}},
    )
    assert processed is False
```

---

## Shared Patterns

### Гард входа на странице
**Source:** `app/pages/dashboard.py:70-72` (идентично в `billing.py:19-21`, `history.py:740-742`)
**Apply to:** каждый маршрут `app/pages/billing.py`
```python
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
```

### Владение — предикатом запроса, не фильтром в шаблоне
**Source:** `app/application/analytics/send_analytics.py:821`, `app/pages/history.py:954`
**Apply to:** список платежей, форма оплаты, оси лимитов
```python
    .where(SendLog.user_id == user_id)
    ...
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)
```

### Сверка источника на изменяющем запросе
**Source:** `app/pages/history.py:345` `_is_same_origin`, вызов на `:950-951`
**Apply to:** POST-форма оплаты (единственный новый изменяющий вход фазы)
```python
    if not _is_same_origin(request):
        return Response(status_code=403)
```
⚠️ Функция сегодня приватная в `app/pages/history.py`. Переиспользование требует переноса в `app/pages/common.py` — копия завела бы второй источник одного правила.

### Контекст шаблона страничного маршрута
**Source:** `app/pages/dashboard.py:108-116, 142`, `app/pages/billing.py:25-37`
**Apply to:** обработчик `/billing`
```python
    return templates.TemplateResponse(
        "billing/balance.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            ...
            "active_page": "billing",
        },
    )
```

### Числа из шелла, а не вторым запросом
**Source:** `app/pages/dashboard.py:119-121, 127`; контракт `app/pages/common.py:431-444`
**Apply to:** оси «Объявления» и «Аккаунты» (Pattern 3)
```python
    getattr(request.state, "shell", {}).get("nav_counts")
```

### Календарные границы — в Python, никогда средствами диалекта
**Source:** `app/application/analytics/send_analytics.py:30-36 (докстринг), :736-755, :81-100`
**Apply to:** ось «Отправок в месяц», `add_one_month`, определение «истекла»
Запрещённые имена: `func.strftime`, `func.date_trunc`, `func.extract`, `func.to_char`, `func.julianday` — есть тест-сторож `test_module_has_no_dialect_specific_calendar_functions`.

### Структурированный лог без секретов
**Source:** `app/services/payment_service.py:64-70`, `app/routes/billing.py:82`
**Apply to:** новые ветки вебхука и обработчик формы
```python
    logger.info("payment_created", user_id=user_id, yookassa_id=payment.id, amount=price)
```
Тело уведомления целиком не логируется (в нём `payment_method.card.first6/last4`).

### Табличные данные без `<table>`
**Source:** `app/templates/billing/balance.html:26-33, 93-113`
**Apply to:** история платежей, строки лимитов
Тест-сторож `test_template_inventory` валится на `("<table", "<td", "<th ", "<thead", "<tbody")` по всем шаблонам.

### Потолок с явным сообщением вместо тихой обрезки
**Source:** `app/pages/history.py:749-770`
**Apply to:** список платежей (D-17)

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/static/css/app.css` — правило `[data-plans]` | style | — | Ближайшее правило `[data-metrics]` (`app.css:1131-1133`, `minmax(210px,1fr)`) — **образец формы, но не аналог значения**: макет требует `minmax(260px,1fr)`, а переопределять `[data-metrics]` нельзя (его держат плитки дашборда Фазы 4). Копировать форму правила, завести новый атрибут. |

## Metadata

**Analog search scope:** `app/application/`, `app/pages/`, `app/routes/`, `app/services/`, `app/models/`, `app/templates/`, `alembic/versions/`, `tests/`
**Orientation:** `graphify query "billing page route service payment subscription"` (572 узла), затем точечные чтения
**Files read for excerpts:** 17
**Pattern extraction date:** 2026-08-15
