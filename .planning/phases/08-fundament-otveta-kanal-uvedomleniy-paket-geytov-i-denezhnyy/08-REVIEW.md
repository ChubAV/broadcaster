---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
reviewed: 2026-08-29T10:05:00Z
depth: standard
files_reviewed: 59
files_reviewed_list:
  - alembic/versions/0021_payments_open_intent_index.py
  - app/application/admin/incidents.py
  - app/application/admin/payments_query.py
  - app/dependencies.py
  - app/main.py
  - app/models/payment.py
  - app/pages/__init__.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/auth.py
  - app/pages/billing.py
  - app/pages/common.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/notices.py
  - app/pages/profile.py
  - app/pages/schedules.py
  - app/services/payment_service.py
  - app/templates/admin/payments.html
  - app/templates/admin/workers.html
  - app/templates/ads/form.html
  - app/templates/auth/login.html
  - app/templates/auth_base.html
  - app/templates/base.html
  - app/templates/billing/balance.html
  - app/templates/history/list.html
  - app/templates/includes/htmx_error_banner.html
  - app/templates/includes/notice_area.html
  - app/templates/includes/notice_oob.html
  - tests/conftest.py
  - tests/test_application/declared_invariants_without_witness.txt
  - tests/test_application/test_admin_payments.py
  - tests/test_application/test_declared_invariants.py
  - tests/test_application/test_incidents.py
  - tests/test_infra/__init__.py
  - tests/test_infra/test_web_service_is_single_process.py
  - tests/test_migrations/test_0021_payments_open_intent_index.py
  - tests/test_models/test_payment_open_intent_index.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_admin_payments.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_money_perimeter_gate.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_notices_surface.py
  - tests/test_pages/test_password_reset.py
  - tests/test_pages/test_schedule_ownership.py
  - tests/test_pages/test_shell.py
  - tests/test_services/test_payment_concurrency.py
  - tests/test_services/test_payment_intent_cap.py
  - tests/test_services/test_payment_service.py
  - tests/test_services/test_payment_status_vocabulary.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py
findings:
  critical: 1
  warning: 9
  info: 7
  total: 17
status: issues_found
---

# Фаза 08: отчёт код-ревью

**Reviewed:** 2026-08-29T10:05:00Z
**Depth:** standard
**Files Reviewed:** 59
**Status:** issues_found

## Summary

Просмотрены денежный путь (`payment_service.py`, `incidents.py`, `payments_query.py`,
ревизия `0021`, модель платежа), слой ответа (`htmx.py`, `main.py`, `dependencies.py`,
`pages/__init__.py`), реестр уведомлений и его разметка, восемь правленных
обработчиков и семь шаблонов, а также пакет новых гейтов.

Подмножества суиты, прогнанные под ревью, зелёные:
`tests/test_services` + `tests/test_models` + `tests/test_migrations` +
`tests/test_application` — 511 passed; `tests/test_templates` + `tests/test_infra` —
126 passed. `ruff --select F401,F811,F841,E711,E712,B006` по всем правленным
модулям приложения — чисто. Полный прогон `tests/test_pages` не уложился в лимит
времени ревью и в отчёте не засчитан.

Ключевые замечания:

1. **Денежный путь.** Перевод потолка в схему сделан аккуратно (порядок
   «уборка → резерв → сеть → дозапись», savepoint, перечитывание состояния вместо
   разбора текста драйвера), но **окно отказа охватывает только вызов SDK**.
   Любой сбой ПОСЛЕ успешного ответа ЮKassa оставляет резерв в `pending`, а новый
   частичный уникальный индекс превращает это в 24-часовую блокировку оплаты для
   конкретного человека без единого пути восстановления (CR-01).
2. **Слой ответа полу-подключён.** `respond()` — центральная функция фазы —
   не имеет НИ ОДНОГО вызова в `app/`; вместе с ней мертвы `_glue_notice`,
   `_notice_oob` и шаблон `includes/notice_oob.html`. Все двенадцать
   обработчиков продолжают собирать `RedirectResponse(302)` руками (WR-01).
3. **Утверждения комментариев расходятся с деревом.** Заявление «частных
   реестров не осталось ни одного» неверно: `QUEUE_DROP_RESULTS`
   (`app/pages/admin.py:288`) жив и работает по прежней схеме (WR-06). Гейт
   словаря статусов, на который прямо ссылается новая положительная выборка
   `AWAITING_STATUSES`, уже, чем обещает его читатель: `alembic/` и голый SQL вне
   области (WR-07).
4. **Фикстура теста ревизии `0021` не воспроизводит боевую схему** — во внешнем
   ключе `payments.user_id → users.id ON DELETE CASCADE` нет вовсе, поэтому
   утверждение «пересоздание таблицы ничего не потеряло» не покрывает главный
   риск batch-режима (WR-08).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: отказ ПОСЛЕ успешного вызова ЮKassa запирает человека от оплаты на 24 часа

**File:** `app/services/payment_service.py:721-808`
**Issue:**
`try/except Exception` охватывает РОВНО `YooPayment.create(...)` (строки 721-769).
Всё, что стоит после него, не защищено:

```python
771  if reserved is not None:
772      reserved.yookassa_payment_id = payment.id
778      await db.commit()          # ← вне try
...
805  return {
806      "confirmation_url": payment.confirmation.confirmation_url,   # ← вне try
807      "payment_id": payment.id,
808  }
```

Сценарий: SDK ответил успехом, платёж у ЮKassa создан, а `db.commit()` на строке
778 упал (обрыв соединения с БД, statement timeout, дедлок) либо
`payment.confirmation` оказался `None`. Тогда:

* исключение уходит наверх мимо `PaymentCreationError`, поэтому
  `subscribe_to_plan` (`app/pages/billing.py:311-351`) его НЕ ловит — человек
  получает 500 и адрес оплаты не получает вовсе;
* ветка гашения резерва (`reserved.status = STATUS_EXPIRED`, строки 743-745)
  живёт ВНУТРИ `except` вокруг SDK и на этом пути не исполняется;
* строка остаётся `kind='subscription' AND status='pending'`, то есть ПОД
  предикатом `uq_payments_open_subscription_intent`;
* следующая попытка того же человека начинается с `_expire_stale_intents`
  (строка 635), но строке пять минут от роду — под срок давности
  `PENDING_INTENT_TTL_HOURS = 24` она не подпадает, уборка её не трогает, и
  вставка нового резерва отвергается индексом → `PendingIntentCapError` →
  плашка «Предыдущая оплата ещё не завершена».

Итог: транзиентный сбой БД превращается в **24 часа невозможности заплатить**
для этого пользователя. Ни самообслуживания, ни админского инструмента снятия
намерения в продукте нет (ветка `expired` проставляется только приложением на
своём же пути и ревизией `0021`). Это ровно то состояние, которое докстринг
`_reserve_subscription_intent` объявляет невозможным («локальная строка без
удалённого платежа восстановима — она гасится в `expired`»): для отказа SDK это
правда, для отказа ПОСЛЕ SDK — нет.

**Fix:** расширить окно гашения резерва на весь участок «после сети», а не
только на вызов SDK:

```python
    try:
        payment = YooPayment.create({...}, idempotency_key)
    except Exception as exc:
        await _expire_reserve(db, reserved)
        logger.error("payment_create_failed", ...)
        raise PaymentCreationError("ЮKassa не создала платёж") from exc

    try:
        if reserved is not None:
            reserved.yookassa_payment_id = payment.id
            await db.commit()
        else:
            ...
        confirmation_url = payment.confirmation.confirmation_url
    except Exception as exc:
        # Резерв обязан быть погашен и здесь: платёж у ЮKassa создан, но человеку
        # не отдан, а `pending` запер бы его на PENDING_INTENT_TTL_HOURS.
        await _expire_reserve(db, reserved)
        logger.error("payment_link_failed", user_id=user_id,
                     yookassa_id=getattr(payment, "id", None),
                     error_type=type(exc).__name__)
        raise PaymentCreationError("ЮKassa не создала платёж") from exc
```

где `_expire_reserve` — уже существующие три строки 743-745, вынесенные в
хелпер (он должен пережить и падение самого гашения: обернуть в свой
`try/except` с записью в журнал, чтобы исходная причина не потерялась).

---

## Warnings

### WR-01: `respond()` и вся htmx-половина канала уведомлений не имеют ни одного вызова в `app/`

**File:** `app/pages/htmx.py:209-367`, `app/templates/includes/notice_oob.html`
**Issue:**
Проверка по дереву:

```
$ grep -rn "from app.pages.htmx import" app/
app/dependencies.py:385:    from app.pages.htmx import refuse
app/main.py:25:from app.pages.htmx import HtmxRefusal, location_response
app/pages/__init__.py:12:from app.pages.htmx import refuse
app/pages/ads.py:15:from app.pages.htmx import is_htmx
$ grep -rn "\brespond\b" app/ | grep -v htmx.py
(пусто)
```

Таким образом мертвы в продакшене: `respond()` (305-367), `_glue_notice`
(251-283), `_notice_oob` (217-248), `_require_registered_notice` (180-206),
`NOTICE_OOB_TEMPLATE` (209), `NOTICE_QUERY_KEY` (45) и весь шаблон
`includes/notice_oob.html`. Ни один из тринадцати обработчиков, пишущих код
исхода, через слой не проходит — все тринадцать собирают адрес и
`RedirectResponse(..., status_code=302)` руками (см. WR-02).

Следствия, а не только эстетика:

* сверка кода с реестром (`_require_registered_notice`) на боевом пути НЕ
  выполняется ни разу — она живёт только внутри `respond()`;
* приклейка внеполосного блока (единственный способ показать исход
  человеку, оставшемуся на странице благодаря htmx) недостижима, поэтому
  форма редактора объявлений (`ads/form.html:64`, `hx-post`) исход действия
  показать по-прежнему не может;
* 400 строк логики и один шаблон проверяются исключительно тестами — то есть
  «покрыты» без единого потребителя.

**Fix:** либо перевести обработчики на `respond()` (тогда `respond` перестанет
быть мёртвым и приклейка заработает), либо, если перевод отложен решением фазы,
пометить это явным `HOLD_NOT_BUILT_YET`-подобным реестром в гейте htmx и
удалить `_glue_notice`/`_notice_oob`/`notice_oob.html` до момента, когда у них
появится вызывающий. Сегодня существует и то, и другое: строки есть, потребителя
нет, а тесты создают впечатление работающего канала.

### WR-02: ключ строки запроса `notice` объявлен константой, но выписан литералом в 15 местах

**File:** `app/pages/htmx.py:45`, `app/dependencies.py:323`,
`app/pages/billing.py:309,346,351`, `app/pages/auth.py:813`,
`app/pages/profile.py:77`, `app/pages/history.py:911,958,962,998`,
`app/pages/admin.py:926,945`, `app/pages/schedules.py:335`,
`app/templates/includes/notice_area.html:61`
**Issue:** `NOTICE_QUERY_KEY = "notice"` (htmx.py:45) используется ровно один
раз — в мёртвом `_with_notice`. Все тринадцать реальных мест записи набирают
`?notice=` / `&notice=` литералом, а чтение в шаблоне — `request.query_params.get('notice')`.
Модуль, чей докстринг требует единственного объявления признака заголовка,
собственный ключ канала размножил в пятнадцати точках. Переименование ключа
сегодня — правка пятнадцати файлов, из которых один шаблон и один
`app/dependencies.py` не связаны с пакетом `app.pages` вовсе.
**Fix:** провести запись через `respond()` (см. WR-01), а чтение — через
шаблонный глобал, принимающий `Request`, например
`templates.env.globals["notice_from"] = lambda request: notice_for(request.query_params.get(NOTICE_QUERY_KEY))`,
и заменить строку 61 на `{% set notice = notice_from(request) %}`.

### WR-03: код исхода в `IMPERSONATION_REFUSED_LOCATION` — сырой литерал, не проверяемый в рантайме

**File:** `app/dependencies.py:323`
**Issue:**
```python
IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"
```
Все остальные двенадцать мест записи подают `notices.<CONSTANT>`; здесь код
набран руками. Реестр закрыт, поэтому опечатка в этом литерале даёт МОЛЧАЛИВОЕ
«плашки нет вовсе» — ровно тот дефект, ради которого модуль `notices.py`
требует констант (его собственный докстринг: «опечатка в литерале даёт
молчаливое „плашки нет“»). Ни `refuse()`, ни `location_response()` код не
сверяют — сверка есть только в мёртвом `respond()` (WR-01). Комментарий над
строкой ссылается на «соседний план 08-02», который уже отгружен, то есть
объяснение устарело в том же коммите.

Смягчающее обстоятельство: гейт `tests/test_pages/test_notices_channel.py::test_every_written_notice_code_is_registered`
ловит эту форму через `WRITTEN_LITERAL`, так что сегодня опечатка покраснела бы
в суите. Защита при этом остаётся тестовой, а не структурной.

**Fix:** отложенный импорт уже применён в этой же функции (строка 385) —
использовать его и для реестра:

```python
def _impersonation_refused_location() -> str:
    from app.pages.notices import IMPERSONATION_FORBIDDEN
    return f"/dashboard?{NOTICE_QUERY_KEY}={IMPERSONATION_FORBIDDEN}"
```

### WR-04: отказ авторизации отвечает кодом 204 при наличии заголовка `HX-Request` — в том числе на JSON-роутере

**File:** `app/dependencies.py:395-402`, `app/main.py:174-176`, `app/pages/htmx.py:133-149`
**Issue:** `forbid_when_impersonating` — зависимость запрета действий под чужой
личностью. После правки её отказ выглядит так:

* без `HX-Request` → `403` + `detail` (как было);
* с `HX-Request` → `HtmxRefusal` → обработчик в `app/main.py:218-225` →
  `location_response(...)` → **`204 No Content`**.

Заголовок пишет клиент, а не приложение: любой запрос, добавивший
`HX-Request: true`, получает на отвергнутое денежное действие статус
УСПЕХА-без-тела. Сама операция при этом заблокирована (отказ поднимается до
обработчика), то есть обхода авторизации нет; проблема в семантике ответа для
потребителей, читающих статус: `if (response.ok) { ... }` прочитает отказ как
успех.

Радиус шире страничного слоя: `app/main.py:174-176` вешает ту же зависимость на
`billing_router` — JSON-роутер `/api/billing`. Сегодня на нём одна ручка
(`POST /webhook`), и она отказ не получает (у уведомления ЮKassa нет
действующего лица, `_actor_id(...) is None` → ранний `return`). Но любая
следующая JSON-ручка, добавленная в этот роутер, унаследует HTML-транспорт
отказа вместе с заголовком `HX-Location` в JSON-ответе.

**Fix:** ограничить развилку транспорта страничным слоем — например, вынести
htmx-ветку в отдельную зависимость `forbid_when_impersonating_page`, оставив на
`app/main.py` прежнюю чисто-403 версию; либо отвечать `403` с заголовком
`HX-Location` вместо `204` (htmx обрабатывает `HX-Location` до разбора
`responseHandling`, проверено в `app/static/js/htmx.min.js`, функция `Vn`), тогда
статус остаётся честным отказом на обоих транспортах.

### WR-05: `is_htmx` считает признаком любое непустое значение, включая `"false"`

**File:** `app/pages/htmx.py:48-67`
**Issue:**
```python
return bool(request.headers.get(HX_REQUEST_HEADER))
```
`HX-Request: false`, `HX-Request: 0`, `HX-Request: no` — все дают `True`.
Единственное объявление признака на проект, от которого зависят обе развилки
транспорта (`refuse`) и весь путь редактора объявлений (`app/pages/ads.py:435,614`),
принимает решение по факту присутствия заголовка, а не по его значению. Прокси,
нормализующий заголовки, или клиент, явно объявивший `HX-Request: false`,
получит htmx-ветку.
**Fix:**
```python
return request.headers.get(HX_REQUEST_HEADER, "").strip().lower() == "true"
```
(htmx всегда шлёт строку `true`; см. `htmx.min.js`).

### WR-06: четвёртый частный реестр уведомлений жив, вопреки утверждениям комментариев

**File:** `app/pages/admin.py:278-300`, `app/templates/admin/queue.html:28-37`,
`app/pages/billing.py:84-95`, `app/pages/notices.py:4-8`
**Issue:** Комментарий `app/pages/billing.py:93-95` утверждает:

> «Три частных реестра — этот, реестр исхода повтора и реестр отказа перезапуска
> воркера — держали одно правило тремя копиями… **Копий не осталось ни одной**.»

Копия осталась. `QUEUE_DROP_RESULTS` (`app/pages/admin.py:288-300`) — словарь
`код → (текст, вариант)`, читаемый обработчиком `admin_queue` из
`?result=` (`app/pages/admin.py:962,1041,1055`) и рисуемый собственным
`{% if drop_result %}{{ alert(...) }}` в `admin/queue.html:34-36`. Это ровно та
форма, которую фаза объявила снятой: свой ключ адреса, свой словарь слов, своя
плашка вне общей области шелла. То же касается зачина докстринга
`app/pages/notices.py:4-8` («таких владельцев было пять») — их было шесть.

Практический вред: страница `/admin/queue` теперь несёт ДВА независимых канала
исхода (общую область шелла и свой `drop_result`), и следующий читатель, ищущий
«где рисуются исходы админки», найдёт один из двух.

**Fix:** либо перенести четыре записи `QUEUE_DROP_RESULTS` в `app/pages/notices.py`
и снять `?result=`-ветку так же, как снята `?error=`-ветка воркеров, либо
исправить три комментария, назвав оставшийся реестр поимённо и записав причину,
по которой он остался (сегодня они утверждают неправду, и гейт
`test_no_retired_query_key_remains` её не ловит — `result` в
`RETIRED_QUERY_KEYS` не входит).

### WR-07: гейт словаря статусов уже, чем несущее его утверждение — `alembic/` и голый SQL вне области

**File:** `tests/test_services/test_payment_status_vocabulary.py:137-184,391-474`,
`app/application/admin/incidents.py:437-441`,
`alembic/versions/0021_payments_open_intent_index.py:148-162`
**Issue:** Докстринг `unclosed_payment_clause` объявляет положительную выборку
безопасной, ссылаясь на гейт:

> «словарь колонки `payments.status` ЗАКРЫТ и принадлежит нам, писатели статуса
> живут только в `app/services/payment_service.py`, и это УТВЕРЖДАЕТСЯ гейтом
> `tests/test_services/test_payment_status_vocabulary.py`».

Гейт этого не утверждает. `_app_sources()` обходит только `APP_DIR.rglob("*.py")`
(строки 137-138, 174-184) — каталог `alembic/` вне области. Форм записи
распознаётся пять, и все они ORM-ные: конструктор `Payment(...)`,
`update/insert(Payment).values(status=...)`, присваивание `.status = "..."`,
`set_committed_value(..., "status", ...)`, умолчание колонки модели. Голый SQL
(`sa.text("UPDATE payments SET status = ...")`, `session.execute(text(...))`)
не распознаётся ни одной формой.

Это не гипотетическая дыра: ревизия `0021` (строки 148-162) ПРЯМО СЕЙЧАС пишет
`status = 'expired'` голым SQL, вне области гейта. Сегодня слово совпадает с
`STATUS_EXPIRED`, но именно этот путь записи гейт не охраняет, а вся
безопасность новой положительной выборки `AWAITING_STATUSES` на нём и держится:
статус, попавший в колонку мимо перечисления, МОЛЧА исчезнет и из чипса
«В обработке», и из признака залипшего платежа.

**Fix:** расширить `_app_sources()` (или добавить второй обход) на
`alembic/versions/*.py` и добавить шестую форму — текстовый поиск
`SET\s+status\s*=\s*'([a-z_]+)'` и `status\s*=\s*'([a-z_]+)'` внутри
`sa.text(...)`/`text(...)` — с утверждением, что каждое найденное слово входит в
`_declared_statuses(...)`. Контроль-подделку добавить рядом с остальными пятью.

### WR-08: фикстура теста ревизии `0021` не воспроизводит боевую схему — внешнего ключа в ней нет

**File:** `tests/test_migrations/test_0021_payments_open_intent_index.py:66-87,410-425`
**Issue:** `PAYMENTS_AT_0020` — рукописный DDL, объявленный как «таблица платежей
в том виде, в каком её застаёт ревизия `0021`». В нём:

```sql
user_id INTEGER NOT NULL,        -- ← ни REFERENCES users(id), ни ON DELETE CASCADE
```

тогда как модель (`app/models/payment.py:61-63`) объявляет
`ForeignKey("users.id", ondelete="CASCADE")`. Таблицы `users` в фикстуре нет
вовсе, `PRAGMA foreign_keys` не включается.

`op.batch_alter_table` в SQLite ПЕРЕСОЗДАЁТ таблицу по отражённой схеме — это
единственная операция ревизии, способная потерять ограничение. Тест
`test_the_unique_index_on_the_payment_id_survives_the_batch_recreate` (410-425)
проверяет выживание индекса и заявлен докстрингом ревизии (строки 179-183) как
доказательство безопасности пересоздания. Про внешний ключ с каскадом — то есть
про ограничение, от которого напрямую зависит удаление пользователя и
рассуждение `payment_ledger` («внешний ключ платежа объявлен с каскадным
удалением») — не проверяется ничего, потому что в фикстуре его нет.

Боевой диалект PostgreSQL batch-режим в пересоздание не превращает, поэтому
непосредственный риск низкий; но утверждение теста шире, чем его предмет, и
следующая batch-правка `payments` унаследует ложную уверенность.

**Fix:** довести фикстуру до боевой формы — добавить `CREATE TABLE users(...)`,
объявить `user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE`,
включить `PRAGMA foreign_keys=ON` и добавить утверждение
`PRAGMA foreign_key_list(payments)` после `upgrade()`, проверяющее, что запись
FK и её `on_delete` пережили пересоздание.

### WR-09: любой код реестра рисуется на ЛЮБОЙ странице по одной ссылке

**File:** `app/templates/includes/notice_area.html:61-63`,
`app/templates/base.html:233-234`, `app/templates/auth_base.html:41-49`
**Issue:** До фазы каждый признак исхода читался ровно одним обработчиком:
`?retry=` только `/history`, `?error=` только `/billing`, `?restart_error=`
только `/admin/workers`. Теперь `notice_area.html` включён в оба шелла и
разрешает КАЖДЫЙ из тринадцати кодов на КАЖДОЙ из 33 страниц:

* `https://<host>/login?notice=password_reset_done` — «Пароль успешно изменён.
  Войдите с новым паролем.» показывается любому, кто перешёл по присланной
  ссылке, включая того, у кого пароль никто не менял;
* `https://<host>/dashboard?notice=payment_pending` — «Предыдущая оплата ещё не
  завершена…» на экране человека, ничего не оплачивавшего.

Тексты закрыты реестром и не содержат ни ссылок, ни разметки, поэтому XSS и
подстановки произвольного текста тут нет — модуль это разбирает верно. Но
поверхность социальной инженерии выросла: сообщение ОТ ИМЕНИ ПРИЛОЖЕНИЯ на
подлинном домене теперь выбирается владельцем ссылки, а не действием человека.
Особенно чувствителен `password_reset_done` на экране входа — классическая
приманка «ваш пароль сменили, войдите заново».

**Fix:** сделать код исхода одноразовым и серверным, а не адресным: писать его в
`Set-Cookie` (`HttpOnly`, `Max-Age=30`, `SameSite=Lax`) и удалять при отрисовке —
тогда плашка появляется только после РЕАЛЬНОГО редиректа, а ссылка её не
рисует. Более дешёвая мера: объявить в реестре допустимый путь приземления для
каждой записи (`Notice(..., landing="/login")`) и рисовать плашку, только если
`request.url.path` совпал.

## Info

### IN-01: результат `_with_notice` на строке 362 выбрасывается — проверка выглядит мёртвым кодом

**File:** `app/pages/htmx.py:358-362`
**Issue:** `_with_notice(redirect, notice)` вызывается как самостоятельное
выражение ради побочного эффекта — `ValueError` из `_local_path`. Комментарий
это объясняет, но статические анализаторы и читатель видят строку без эффекта;
первый же «уборщик мёртвого кода» её снимет.
**Fix:** выделить намерение в имя: `_reject_unusable_path(_with_notice(redirect, notice))`
или `_local_path(_with_notice(redirect, notice))  # noqa: B018` с явной функцией
`assert_local(...)`.

### IN-02: `htmx_client` мутирует общий объект `client` и глобально включает следование редиректам

**File:** `tests/conftest.py:65-101`
**Issue:** Фикстура ставит `client.headers["HX-Request"]` и
`client.follow_redirects = True` на ТОТ ЖЕ объект, который отдают `client`,
`authed_client`, `admin_client`, `expired_client`. Тест, запросивший
`htmx_client` и `client` одновременно, получает один и тот же
htmx-настроенный клиент, а умолчание проекта (`follow_redirects=False`)
переключается для всего теста целиком. Свойство названо в докстринге, но
ловушка остаётся: тест, который «просто хотел проверить 302», позеленеет на 200
чужой страницы.
**Fix:** либо вернуть КОПИЮ клиента с наложенными настройками, либо
переименовать фикстуру в `client_as_htmx` и добавить утверждение в
`test_shell.py`, что ни один тест не берёт обе фикстуры сразу.

### IN-03: `notice_areas()` считает вложенность по подстроке `<div`

**File:** `tests/conftest.py:334-350`
**Issue:** `html.find("<div", scan)` совпадёт и с `<divider>`, и с текстом
`&lt;div` после экранирования, и с подстрокой внутри значения атрибута. Сегодня
разметка областей проста и совпадений нет, но хелпер объявлен общим для всех
будущих проверок исхода.
**Fix:** считать по `re.finditer(r"<div\b|</div>", html)` либо разобрать область
`html.parser`-ом (стандартная библиотека, новой зависимости не требует).

### IN-04: частичный индекс `0021` вырождается в полный на любом третьем диалекте

**File:** `alembic/versions/0021_payments_open_intent_index.py:194-201`
**Issue:** `op.create_index(..., unique=True, sqlite_where=..., postgresql_where=...)`
— предикат объявлен только для двух диалектов. На любом другом (MySQL, MSSQL)
Alembic создаст УНИКАЛЬНЫЙ индекс по всей колонке `user_id`, то есть ровно то
состояние, которое докстринг ревизии (строки 54-59) называет «заперло бы
человека навсегда: ни одного второго платежа». Проект сегодня ходит только на
PostgreSQL и SQLite, поэтому это заметка на будущее, а не действующий дефект.
**Fix:** добавить в `upgrade()` явный отказ:
`if op.get_bind().dialect.name not in ("postgresql", "sqlite"): raise NotImplementedError(...)`.

### IN-05: в `QUEUE_DROP_RESULTS` один ключ набран литералом, три — константами

**File:** `app/pages/admin.py:288-300`, `app/pages/admin.py:1111`
**Issue:** `"unknown_account"` выписан строкой и в словаре, и в адресе редиректа
(строка 1111), тогда как `DROP_REMOVED`, `DROP_MISSING`, `DROP_UNAVAILABLE` —
константы. Опечатка в одном из двух вхождений даёт молчаливое «плашки нет».
**Fix:** завести `DROP_UNKNOWN_ACCOUNT = "unknown_account"` рядом с тремя
соседями (или снять реестр целиком по WR-06).

### IN-06: запись `htmx_refusal` не называет, какое правило отвергло запрос

**File:** `app/main.py:218-225`
**Issue:** Обработчик пишет `logger.info("htmx_refusal", path=...)` — без
указания зависимости (`require_access` или `forbid_when_impersonating`) и без
`location`. Комментарий рассчитывает на то, что «сам факт отказа пишется
вызывающей зависимостью своим ключом», но связать две записи в потоке логов
можно только по `request_id`, а `path` дублирует уже связанные поля
`RequestIdMiddleware`. Запись в текущем виде не добавляет ничего, кроме шума.
**Fix:** добавить `location=exc.location` (адрес отличает два правила
однозначно) либо снять запись как избыточную.

### IN-07: сценарий плашек отказа перерегистрирует слушателей при каждой навигации по `HX-Location`

**File:** `app/templates/includes/htmx_error_banner.html:76-86`
**Issue:** `HX-Location` заставляет htmx подменить содержимое `<body>` целиком
(`Nn("get", …)` в `htmx.min.js`), а при `allowScriptTags:true` пришедший
`<script>` исполняется заново и добавляет вторую пару слушателей на тот же
`document.body`, который подменой не уносится. Обработчики идемпотентны (снимают
атрибут `hidden`), поэтому видимого дефекта нет, но число слушателей растёт с
каждым отказом гейта доступа.
**Fix:** обернуть регистрацию признаком:
`if (!document.body.dataset.htmxFailureBound) { document.body.dataset.htmxFailureBound = '1'; ... }`.

---

_Reviewed: 2026-08-29T10:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
