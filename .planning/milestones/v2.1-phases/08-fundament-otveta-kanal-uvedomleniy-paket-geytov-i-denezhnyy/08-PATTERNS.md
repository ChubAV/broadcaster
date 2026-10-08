# Phase 8: Фундамент ответа, канал уведомлений, пакет гейтов и денежный потолок — Pattern Map

**Mapped:** 2026-08-28
**Files analyzed:** 24 (новых 8, правимых 16)
**Analogs found:** 22 / 24 (2 без аналога)
**Источник списка файлов:** `08-CONTEXT.md` §`<code_context>` → Integration Points, §`<canonical_refs>`;
RESEARCH.md фазы нет намеренно (ROADMAP: «Research: не требуется»).

---

## File Classification

### Денежный узел (PAY-01, PAY-02) — независимый поток

| Новый / правимый файл | Роль | Поток данных | Ближайший аналог | Качество совпадения |
|---|---|---|---|---|
| `alembic/versions/0021_payments_open_intent_index.py` (новый) | migration | batch + schema | `alembic/versions/0018_subscriptions_unique_user.py` | **exact** — тот же класс: частичный уникальный индекс + зачистка данных в одной ревизии |
| `app/models/payment.py` (правка: `yookassa_payment_id` → nullable, статус `expired`) | model | CRUD | сам файл + `app/constants.py` (правило «String, а не sa.Enum») | **exact** (правка на месте) |
| `app/services/payment_service.py` (правка: резерв→сеть→дозапись, ленивая уборка, `IntegrityError` по имени ограничения, `_claim_payment` расширяется) | service | CRUD + request-response | `_extend_subscription` (разбор отказа ограничения) + `app/pages/history.py::_claim_retry_slot` (ленивая уборка) | **exact** — оба прецедента внутри проекта |
| `app/pages/billing.py::subscribe` (правка: `?error=` → `?notice=`) | controller | request-response | сам обработчик (ветки `PendingIntentCapError` / `PaymentCreationError`) | **exact** |
| `tests/test_pages/test_money_perimeter_gate.py` (новый, G-18) | test (гейт множества по AST) | — | `tests/test_pages/test_impersonation_gate.py` | **exact** — «гейт, замкнутый на себя» (равенство найденного и объявленного) |
| `tests/test_infra/test_web_service_is_single_process.py` (новый, гейт D-07) | test (гейт артефакта) | file-I/O | `tests/test_templates/test_htmx_inventory.py` (чтение файла-исходника + утверждение состава) | role-match |

### Слой ответа и отказ зависимости (FOUND-04, FOUND-07)

| Новый / правимый файл | Роль | Поток данных | Ближайший аналог | Качество совпадения |
|---|---|---|---|---|
| `app/pages/htmx.py` (новый) | utility / response-layer | request-response | `app/pages/ads.py::_save_from_editor` + `_autosave_response`; `app/pages/accounts.py::_connect_status` | **exact** по механике, **новый** по форме (обобщение) |
| `app/pages/__init__.py::require_access` (правка) | middleware / dependency | request-response | сам себя (`HTTPException(302, headers={"location": …})`) | **exact** |
| `app/dependencies.py::forbid_when_impersonating` (правка) | middleware / dependency | request-response | `require_access` (та же форма «зависимость ОТКАЗЫВАЕТ исключением») | **exact** |
| `tests/conftest.py::htmx_client` (новая фикстура) | test fixture | request-response | `tests/conftest.py::client` / `authed_client` / `expired_client` | **exact** |

### Канал уведомлений (FOUND-05, FOUND-06, QUAL-03, D-12)

| Новый / правимый файл | Роль | Поток данных | Ближайший аналог | Качество совпадения |
|---|---|---|---|---|
| `app/pages/notices.py` (новый) | config / registry | transform (код → текст+вариант) | `app/pages/history.py::RETRY_NOTICES`, `app/pages/billing.py::PAYMENT_ERROR_MESSAGES`, `app/pages/ads.py::SCHEDULE_ERROR_REASONS` | **exact** — три частных реестра одной формы |
| `app/templates/base.html` (правка: две `aria-live`-области + скрытая заготовка плашки) | template / shell | — | блок `{% if impersonation %}` `base.html:71-78` (условная область в шелле) | role-match |
| `app/templates/auth_base.html` (правка) | template / shell | — | `base.html` (шеллы совпадают построчно) | **exact** |
| `app/templates/includes/notice_area.html` + `includes/htmx_error_banner.html` (новые) | template include | — | `app/templates/includes/htmx_config.html` (единственный владелец, включаемый в оба шелла; D-01/D-02 Фазы 7) | **exact** |
| Инлайн-`<script>` обработчиков `htmx:responseError` / `htmx:sendError` | template / script | event-driven | второй блок `<script>` в `includes/htmx_config.html` (D-11 Фазы 7 — первый инлайн-скрипт проекта) | **exact** |
| Восемь обработчиков старых параметров: `app/pages/billing.py` ×3, `admin.py` ×2, `profile.py`, `auth.py`, `schedules.py`, `history.py` ×4 (итого 12 мест `RedirectResponse`) | controller | request-response | друг друга; канон — `history.py` (коды через константы) | **exact** |
| Пять мест отрисовки плашки: `billing/balance.html:60,62`, `ads/form.html:183`, `history/list.html:41`, `profile.html:18`, `auth/login.html:11-12` | template | — | `app/templates/components/alert.html` (макрос остаётся, переезжает точка вызова) | **exact** |

### Пакет гейтов (GATE-01, 03…08)

| Новый файл | Роль | Поток данных | Ближайший аналог | Качество совпадения |
|---|---|---|---|---|
| `tests/test_pages/test_htmx_gates.py` (G-1/G-2, G-13, инвентари `HX_POST_PLACES`/`HX_HEADER_WRITES`) | test (гейт множества по AST) | file-I/O | `tests/test_pages/test_impersonation_gate.py`, `tests/test_pages/test_htmx_response_contract.py` | **exact** |
| `tests/test_templates/test_htmx_markup_gates.py` (деградация, своп, OOB, граница Alpine, `hx-vals`) | test (гейт разметки регуляркой) | file-I/O | `tests/test_templates/test_htmx_inventory.py` | **exact** |
| `tests/test_pages/test_notices_registry.py` (уникальность кодов, 0 вхождений снятых имён, `expired` вне реестра) | test (греп-гейт + гейт уникальности) | file-I/O | `test_htmx_inventory.py` + греп-гейт снятых имён тарификации (v2.0) | role-match |
| `tests/test_pages/test_shell.py` (правка, G-23) | test | request-response | сам файл | **exact** |

---

## Pattern Assignments

### `alembic/versions/0021_payments_open_intent_index.py` (migration, batch+schema)

**Аналог:** `alembic/versions/0018_subscriptions_unique_user.py` — берётся **целиком, дословно по форме**,
включая тон журнальных сообщений (§`<specifics>` CONTEXT).

**Докстринг: продуктовое решение называется прямо** (`0018`, строки 1-30) — воспроизвести структуру:
```
"""<однострочное имя ревизии>

ЗАЧЕМ. <...>

⚠️ РЕВИЗИЯ СТРОГО ОДНОСТОРОННЯЯ — ТОТ ЖЕ КЛАСС, ЧТО `0013`. Она МЕНЯЕТ ДАННЫЕ, а
не только схему: перед созданием индекса она деактивирует лишние строки.
`downgrade` снимает индекс, но НЕ ВОССТАНАВЛИВАЕТ снятые пометки <...>

⚠️ ПРОДУКТОВОЕ РЕШЕНИЕ, ПРИНЯТОЕ МИГРАЦИЕЙ, А НЕ ЧЕЛОВЕКОМ — НАЗЫВАЕТСЯ ЗДЕСЬ
ПРЯМО, ЧТОБЫ ЧИТАТЕЛЬ РЕВИЗИИ НАШЁЛ ЕГО, А НЕ ВЫВОДИЛ ИЗ SQL:

    ИЗ НЕСКОЛЬКИХ АКТИВНЫХ ПОДПИСОК ПОЛЬЗОВАТЕЛЯ ВЫЖИВАЕТ ТА, У КОТОРОЙ СРОК
    ДАЛЬШЕ (`MAX(expires_at)`). При ТОЧНОМ равенстве сроков выживает строка с
    НАИБОЛЬШИМ `id`.

BACKFILL ИДЁТ ДО СОЗДАНИЯ ИНДЕКСА И В ТОЙ ЖЕ РЕВИЗИИ. <...>
СЛЕД В ЖУРНАЛЕ ОБЯЗАТЕЛЕН. <...>
ИНДЕКС ЧАСТИЧНЫЙ (`WHERE is_active`), А НЕ УНИКАЛЬНОСТЬ НА ВСЮ КОЛОНКУ. <...>
⚠️ ГРАНИЦА ОГРАНИЧЕНИЯ. <...>
Литералы имён таблицы, колонок и индекса выписаны ЗДЕСЬ строками и НЕ
импортированы из `app.models` — правило ревизий `0013`/`0014`/`0017` <...>
"""
```
Для Фазы 8 подставляется решение D-03: выживает **новейшее** (`MAX(created_at)`,
тай-брейк `MAX(id)`), остальные → `expired`; отличие от `0018` («проигравший ничего
не теряет: `expired` оплачиваем и зачисляем») выписывается явно.

**Заголовок ревизии и константа имени** (`0018`, строки 71-80):
```python
import logging

from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"

INDEX_NAME = "uq_subscriptions_active_user"

logger = logging.getLogger("alembic.runtime.migration")
```
→ `revision = "0021"`, `down_revision = "0020"` (последняя в каталоге — `0020_flat_subscription.py`;
боевая база стоит на `0012`, ревизия встаёт **девятой** в невыкаченной очереди),
`INDEX_NAME = "uq_payments_open_subscription_intent"`.

**Зачистка голым SQL с коррелированным подзапросом** (`0018`, строки 82-110):
```python
_DEACTIVATE_DUPLICATES = sa.text(
    """
    UPDATE subscriptions SET is_active = false
    WHERE is_active
      AND id <> (
          SELECT keeper.id FROM subscriptions AS keeper
          WHERE keeper.user_id = subscriptions.user_id
            AND keeper.is_active
          ORDER BY keeper.expires_at DESC, keeper.id DESC
          LIMIT 1
      )
    """
)
```
Для Фазы 8: `UPDATE payments SET status = 'expired' WHERE kind = 'subscription'
AND status = 'pending' AND id <> (SELECT keeper.id … ORDER BY keeper.created_at DESC,
keeper.id DESC LIMIT 1)`. ⚠️ Урок ревизии `0015`, выписанный в комментарии `0018`:
булев литерал — **ключевым словом, никогда нулём**; здесь предмет строковый, но
комментарий-предупреждение о расхождении диалектов сохраняется по форме.

**`upgrade()` — backfill, журнал, потом индекс** (`0018`, строки 113-131):
```python
def upgrade():
    connection = op.get_bind()

    result = connection.execute(_DEACTIVATE_DUPLICATES)
    deactivated = result.rowcount if result.rowcount is not None else -1
    logger.info(
        "0018: deactivated %s duplicate active subscription row(s); "
        "kept the row with the furthest expires_at (ties broken by highest id). "
        "THIS IS NOT REVERSIBLE.",
        deactivated,
    )

    op.create_index(
        INDEX_NAME,
        "subscriptions",
        ["user_id"],
        unique=True,
        sqlite_where=sa.text("is_active"),
        postgresql_where=sa.text("is_active"),
    )
```
→ предикат: `sa.text("kind = 'subscription' AND status = 'pending'")` в обоих
`sqlite_where` и `postgresql_where`. Плюс отдельным шагом — `op.alter_column`
на `payments.yookassa_payment_id` → `nullable=True` (D-05).

**`downgrade()` — односторонний, с предупреждением в журнал** (`0018`, строки 134-149):
```python
def downgrade():
    """Снимает индекс. Деактивированные строки НЕ восстанавливает — их не вернуть.

    Откат намеренно НЕ ПРИТВОРЯЕТСЯ симметричным. <...>
    """
    op.drop_index(INDEX_NAME, table_name="subscriptions")
    logger.warning(
        "0018 downgrade: index %s dropped, but rows deactivated by the upgrade "
        "backfill are NOT restored — that information was never recorded. "
        "The data half of this revision is one-way (same class as 0013).",
        INDEX_NAME,
    )
```

---

### `app/services/payment_service.py` (service, CRUD)

**Аналог по разбору отказа ограничения:** `_extend_subscription`, строки 798-825
— **прямой прецедент D-06** (отличить свой отказ от чужого):
```python
    try:
        async with db.begin_nested():
            db.add(
                Subscription(
                    user_id=db_payment.user_id,
                    expires_at=next_expiry(None, now),
                    is_active=True,
                )
            )
            await db.flush()
        return
    except IntegrityError as rejection:
        logger.info(
            "subscription_insert_lost",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
        )
        rejected_by = rejection

    subscription = await _active_subscription(db, db_payment.user_id)
    if subscription is None:
        # Ограничение отвергло вставку, но активной строки нет — значит отказ
        # пришёл НЕ от `uq_subscriptions_active_user`, и глотать его нельзя:
        # исключение поднимается тем же объектом, а не новым.
        raise rejected_by
```
Копируется: `db.begin_nested()` вокруг вставки, `except IntegrityError as rejection`,
логирование факта проигранной гонки, **обязательный `raise rejected_by`** для чужого
отказа. Для Фазы 8 различение идёт **по имени ограничения** (`uq_payments_open_subscription_intent`)
— способ разбора (текст vs `orig.diag`) оставлен на усмотрение планировщика (Claude's Discretion).

**Аналог по ленивой уборке на своём же пути (основание D-02):**
`app/pages/history.py::_claim_retry_slot`, строки 538-565:
```python
def _claim_retry_slot(log_id: int) -> bool:
    """Открывает окно удержания повтора записи. `False` — окно ещё не истекло.

    ЗДЕСЬ ЖЕ СНИМАЮТСЯ ПРОСРОЧЕННЫЕ УДЕРЖАНИЯ ЧУЖИХ ЗАПИСЕЙ. Успешная постановка
    удержание СОХРАНЯЕТ (в этом вся защита от второго нажатия), и снимать его
    больше некому: обхода реестра нет нигде, периодической задачи под него не
    заведено. <...>
    """
    now = monotonic()
    for stale in [key for key, until in _RETRY_IN_FLIGHT.items() if until <= now]:
        del _RETRY_IN_FLIGHT[stale]
    deadline = _RETRY_IN_FLIGHT.get(log_id)
    if deadline is not None and now < deadline:
        return False
```
Идиома для `create_payment`: `UPDATE payments SET status='expired' WHERE user_id=…
AND kind='subscription' AND status='pending' AND created_at < cutoff` **прямо перед
вставкой резерва**, без второго писателя и без Celery beat.

**Форма CAS, расширяемая до `IN ('pending','expired')`** — `_claim_payment`, строки 478-509:
```python
    result = await db.execute(
        update(Payment)
        .where(
            Payment.yookassa_payment_id == yookassa_id,
            Payment.status.not_in(TERMINAL_STATUSES),
        )
        .values(status=new_status, confirmed_at=now)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1
```
⚠️ Ключевое: условие написано **через `TERMINAL_STATUSES`, а не через равенство
`pending`** (докстринг: «третий нетерминальный статус, добавленный когда-нибудь,
обязан попасть сюда сам»). Значит D-01 (`expired` **не входит** в `TERMINAL_STATUSES`)
даёт расширение `_claim_payment` **бесплатно**, ни одной строки условия не трогая —
это и есть проверка того, что решение легло в существующую конструкцию.

**Константы и их обоснование** — строки 30-52. `PENDING_INTENT_TTL_HOURS = 24`
не меняется (D-04), но комментарий над ней **переписывается**: сегодняшний абзац
(«срок давности — единственный сегодня выход из незакрытого намерения») с D-01
перестал быть правдой. Форма комментария («ЗДЕСЬ ВАЖНО НЕ ЧИСЛО, А ТО, ЗАЧЕМ
КОНСТАНТА ВООБЩЕ СУЩЕСТВУЕТ») сохраняется.

**Докстринг `create_payment`, строки 175-315** — раздел «⚠️ СУЖАЕТ, А НЕ ДЕЛАЕТ
НЕДОСТИЖИМЫМ, И ОСТАТОЧНЫХ ОКОН ДВА, А НЕ ОДНО» и абзац «ЧТО ЗАКРЫЛО БЫ ОКНО
СВОЙСТВОМ, А НЕ ФОРМУЛИРОВКОЙ, НАЗВАНО ПОИМЁННО И НАЗВАНО НЕСДЕЛАННЫМ»
**переписываются на сделанное**. Абзац буквально перечисляет объём этой фазы:
«своя ревизия Alembic в невыкаченной очереди (D-26), своё решение о том, что делать
с уже существующими строками, свой round-trip-тест и своя обработка отказа
ограничения ЗДЕСЬ». План обязан снять это описание долга, а не оставить рядом
с закрывшим его кодом.

**Порядок, который меняется (D-05)** — сегодня, строки 305-315:
```python
    # ⚠️ ПРОВЕРКА СТОИТ ДО `_configure_yookassa()`, ДО СБОРКИ `metadata` И ДО
    # `YooPayment.create`. Отказ, принятый ПОСЛЕ вызова SDK, оставил бы у ЮKassa
    # платёж, которого нет в нашей базе <...> зеркало ровно той ловушки, ради
    # которой запись в свою базу стоит ПОСЛЕ вызова SDK (T-05-49).
    if kind == KIND_SUBSCRIPTION:
        open_intents = await _open_subscription_intents(...)
        if open_intents:
            logger.warning("subscription_intent_cap_reached", user_id=user_id, ...)
            raise PendingIntentCapError(
                "Предыдущее подписочное намерение ещё не завершено"
            )
```
Прикладной блок снимается целиком (D-06), `_open_subscription_intents` остаётся
**селектором уборки**; рассуждение T-05-49 в комментарии **зеркалится** (CONTEXT D-05:
«локальная строка без удалённого платежа восстановима, удалённый платёж без локальной
строки — нет»), а не удаляется молча. Логирование `logger.warning("subscription_intent_cap_reached", …)`
переезжает в ветку разбора `IntegrityError` — уровень `warning` и обоснование
(«это исход, по которому к нам придёт человек») сохраняются.

**Тип исключения не меняется** — `PendingIntentCapError` (строки 89-114): докстринг уже
объясняет, почему у него свой тип и почему его текст на экран не уходит. Под D-06
он лишь поднимается из другого места.

---

### `app/pages/htmx.py` (utility / response-layer, request-response) — НОВЫЙ

**Аналог механики:** `app/pages/ads.py::_save_from_editor`, строки 413-525 — единственный
сегодняшний обработчик с двойным ответом.

**Чтение заголовка — сегодня в двух местах, после фазы в одном** (`ads.py:435`, `ads.py:611`):
```python
    is_htmx = request.headers.get("HX-Request") is not None
```
Именно эта строка становится единственной на проект (FOUND-04, критерий 1). Гейт
G-1/G-2 утверждает `HX_HEADER_READS == 1` **своим обходом** (D-13).

**Обоснование ветвления, которое `respond()` обобщает** (`ads.py:424-432`):
```python
    """Один путь для автосохранения, «Сохранить» и работы без JavaScript.

    Ветвление — по наличию заголовка запроса htmx, а не по отдельным маршрутам:
    базовый путь D-09 обязан быть ТЕМ ЖЕ кодом, иначе он тихо разойдётся с
    улучшенным.
    """
```
Это же рассуждение — основание обязательного `redirect=` в сигнатуре `respond()`.

**Ветка htmx + запись заголовка** (`ads.py:517-523`) — единственное сегодняшнее
`response.headers["HX-*"]`, предмет инвентаря `HX_HEADER_WRITES = 1`:
```python
    if is_htmx:
        response = await _autosave_response(request, db, settings, user, ad)
        if created:
            # D-03: браузер подменяет адрес без перезагрузки — дальнейшие
            # автосохранения уходят уже на маршрут редактирования.
            response.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"
        return response
```

**Ветка деградации** (`ads.py:525-531`):
```python
    # Путь без JavaScript. «Сохранить» завершает работу над объявлением и
    # возвращает в список; всё остальное <...> оставляет пользователя в редакторе
    if explicit_save:
        return RedirectResponse(url="/ads", status_code=302)
```

**Аналог «маршрут возвращает фрагмент»:** `app/pages/accounts.py:47-50`:
```python
def _connect_status(macro: str, *args) -> HTMLResponse:
    """Рендерит макрос ответа опроса подключения через окружение Jinja2."""
    module = templates.env.get_template(_CONNECT_STATUS).module
    return HTMLResponse(str(getattr(module, macro)(*args)))
```
и `app/pages/ads.py::_autosave_response` (386-410) — `templates.TemplateResponse(request, …)`
без ключей оболочки: «фрагмент не перерисовывает оболочку страницы».

**Второй выход — помощник отказа зависимости.** Аналога в проекте нет: сегодня отказ
зависимости выражается только `HTTPException`, а `HTTPException(status_code=200)`
отдал бы тело `{"detail": …}`, что FOUND-07 запрещает (Landmine из CONTEXT). Форма —
за планировщиком; ближайшая опора — форма отказа `require_access` ниже.

---

### `app/pages/__init__.py::require_access` (dependency, request-response)

**Аналог:** сам себя, строки 50-110. Правится **тело отказа**, докстринг дополняется.

**Текущий отказ** (строки 105-108) — точка правки FOUND-07:
```python
    if not access_is_open(subscription, datetime.now(timezone.utc)):
        raise HTTPException(
            status_code=302, headers={"location": ACCESS_EXPIRED_LOCATION}
        )
```
где `ACCESS_EXPIRED_LOCATION = "/billing?expired=1"` (строка 47).

**Обоснование, которое ОСТАЁТСЯ в силе и обязано быть сохранено** (строки 72-84):
```
    ⚠️ ОТКАЗ — `HTTPException` СО СТАТУСОМ 302 И ЗАГОЛОВКОМ `location`, А НЕ
    ВОЗВРАТ `RedirectResponse`, И ВЫБОР ЗДЕСЬ ВЫНУЖДЕННЫЙ. Зависимость,
    объявленная через `APIRouter(dependencies=[...])`, своего возвращаемого
    значения никуда не отдаёт — FastAPI его ОТБРАСЫВАЕТ <...> Прервать
    цепочку зависимость может единственным способом — исключением.
```
Это ограничение и есть причина, по которой у `htmx.py` заводится **второй, узкий выход**
(D-15): новая ветка обязана остаться `raise`, а не `return`.

**Решение D-11, переезжающее на новый канал вместе с адресом** (строки 86-89):
```
    ⚠️ ПАРАМЕТР `?expired=1` — АРТЕФАКТ РЕДИРЕКТА, А НЕ ВХОД ОБРАБОТЧИКА.
    Читать его в `/billing` запрещено (UI-контракт, E2): состояние доступа
    известно серверу из строки подписки, и решать по параметру адресной строки,
    что показать, значило бы отдать этот вопрос владельцу ссылки.
```

**Вторая точка правки FOUND-07** — `app/dependencies.py::forbid_when_impersonating`,
строки 344-356 (не `common.py::impersonation_view`, который только собирает контекст
шелла и ничего не бросает):
```python
    if _actor_id(request, credentials, settings) is None:
        return

    logger.warning(
        "impersonated_action_refused",
        path=request.url.path,
        method=request.method,
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=IMPERSONATION_FORBIDDEN_DETAIL,
    )
```
⚠️ Формы отказа **две разные**: 302+`location` у доступа и 403+`detail` у имперсонации.
FOUND-07 требует, чтобы на `HX-Request` обе отвечали `HX-Location`, «не 302 и не JSON» —
то есть общий помощник обязан покрыть оба, а не быть скроен под один.

---

### `app/pages/notices.py` (config / registry, transform) — НОВЫЙ

**Аналог №1 — форма «код → (текст, вариант)»:** `app/pages/history.py::RETRY_NOTICES`,
строки 317-350:
```python
RETRY_NOTICES = {
    RETRY_QUEUED: (
        "Повтор поставлен в очередь. Уйдёт ТЕКУЩЕЕ содержимое объявления, "
        "а не то, что показано в записи.",
        "success",
    ),
    RETRY_GONE: (
        "Повторить не удалось: объявления, группы или аккаунта этой отправки "
        "больше нет либо аккаунт отключён.",
        "warning",
    ),
    RETRY_ACCESS_CLOSED: (
        "Повторить не удалось: доступ к системе закрыт. Оплатите подписку — "
        "и повтор станет доступен.",
        "warning",
    ),
    ...
}
```
и потребление через `.get()` (закрытое множество), `history.py:1170`:
```python
            "retry_notice": RETRY_NOTICES.get(retry),
```

**Аналог №2 — реестр с объяснением снятых записей:** `app/pages/billing.py:102-145`:
```python
PAYMENT_ERROR_MESSAGES = {
    "payment": "Не удалось начать оплату — попробуйте ещё раз через минуту",
    "disabled": "Оплата сейчас недоступна — обратитесь к администратору",
    # ⚠️ ТРИ ЗАПИСИ СНЯТЫ ВМЕСТЕ СО СВОИМ ПРЕДМЕТОМ, И ИМЕНА ИХ ЗДЕСЬ НЕ
    # НАЗВАНЫ НАМЕРЕННО: регрессия читает этот файл ТЕКСТОМ, и объяснение,
    # набранное снятым литералом, уронило бы собственный запрет.
    ...
}

    return PAYMENT_ERROR_MESSAGES.get(code or "", "")
```
⚠️ **Прямо применимо к D-09:** гейт нулевых вхождений снятых имён читает файл ТЕКСТОМ,
поэтому объяснение в `notices.py`, набранное снятым литералом (`?error=`, `?saved=`…),
уронит собственный гейт. Прецедент уже отработан — повторить приём умолчания имён.

**Аналог №3 — закрытое множество кортежем:** `app/pages/ads.py:65`:
```python
SCHEDULE_ERROR_REASONS = ("account", "missing")
```
`ads.py:670`: `... if sched_error in SCHEDULE_ERROR_REASONS`.

**Что переносится дословно (§`<specifics>`):** тексты всех трёх реестров переезжают
без переписывания. Инвентарь кодов на переезд: `billing` — `payment`, `disabled`,
`pending`; `admin` — `no_container`, `restart_failed`; `?saved=1` (булев → код
`profile_saved`); `?reset=success`; `?retry=` — 4 кода; `?sched_error=` — 2 кода.

**Форма сборки (D-10):** реестр собирается **из пар с гейтом на уникальность**, а не
литералом словаря — дубль ключа в словаре Python есть молчаливая перезапись. Аналога
этой формы в проекте нет; ближайшее — `NamedTuple`-таблицы в
`tests/test_templates/test_htmx_inventory.py:44` (`class ... (NamedTuple)` + кортеж записей).

---

### `app/templates/base.html` / `auth_base.html` (shell) + новые includes

**Аналог владения общим блоком:** `app/templates/includes/htmx_config.html` — прецедент
D-01/D-02 Фазы 7, задающий правило для новых включений:
```
   ПОЧЕМУ ОДИН ФАЙЛ, А НЕ ДВА ЛИТЕРАЛЬНЫХ БЛОКА В ДВУХ ШЕЛЛАХ (D-01).
   Шеллов у проекта два — base.html и auth_base.html, — и их <head> совпадают
   построчно. Две копии конфигурации держались бы в единстве только
   бдительностью теста <...> Источник один, второй копии не заводится — и это
   утверждается тестом единственности, а не соблюдается по договорённости.
```
Подключение (`base.html:25`, `auth_base.html:24`): `{% include "includes/htmx_config.html" %}`.

**Аналог условной области в шелле:** `base.html:71-78` — блок имперсонации:
```jinja
    {% if impersonation %}
    <div data-impersonation class="alert alert--warning" role="status">
        <span class="impersonation-text">Вы работаете от имени пользователя {{ impersonation.get('subject_label') }}</span>
        <form method="post" action="/impersonation/stop" class="impersonation-back">
            <button type="submit" class="btn btn--ghost">{{ mono('ВЕРНУТЬСЯ В АДМИНА', 'muted', upper=true) }}</button>
        </form>
    </div>
    {% endif %}
```
⚠️ Ровно та же форма «нет ключа — нет разметки», которой требует критерий 2
(«при отсутствии кода разметки нет вовсе»). Обоснование в докстринге
`common.py::impersonation_view` («НЕТ ДЕЙСТВУЮЩЕГО ЛИЦА — НЕТ КЛЮЧА, а не ключ с
пустым значением») переиспользуется для `#notice`.

**Аналог примитива плашки:** `app/templates/components/alert.html` — `role` **уже** выводится
из варианта, переучивать не нужно (находка CONTEXT):
```jinja
{% macro alert(message, variant='error') -%}
<div class="alert alert--{{ variant }}" role="{{ 'alert' if variant == 'error' else 'status' }}">{{ message }}</div>
{%- endmacro %}
```
Деление на вежливую (`role="status"`) и настойчивую (`role="alert"`) области — это
**два `aria-live`-узла**, а не новая ось.

**Аналог инлайн-скрипта (D-11 Фазы 7):** хвост `includes/htmx_config.html`:
```html
<script>
  try { localStorage.removeItem('htmx-history-cache'); } catch (error) { /* приватный режим: хранилище недоступно, чистить нечего */ }
</script>
```
с Jinja-комментарием над ним (⚠️ **не HTML-комментарием** — он приехал бы в документ и
удвоил счёт вхождений, уронив гейты) и абзацем «ЧЕГО СКРИПТ НЕ ДЕЛАЕТ»:
```
   ЧЕГО СКРИПТ НЕ ДЕЛАЕТ. Он зовёт ровно один метод удаления ключа, не читает ни
   одного значения из пришедшего запроса и не собирает разметку строкой —
   правило вехи v2.0 «сборка узлами DOM, не строкой» держится и здесь. Это
   утверждается ГЕЙТОМ по исходнику этого файла
   (test_history_cache_purge_touches_no_markup_sink) <...>
```
→ обработчики `htmx:responseError`/`htmx:sendError` пишутся ровно в этой форме:
скрипт **только переключает атрибут** на заранее отрисованной скрытой заготовке,
и парный гейт утверждает отсутствие `innerHTML` / `outerHTML` / `insertAdjacentHTML`
/ `document.write` (§`<specifics>`).

⚠️ **Предписание, оставленное Фазой 7 именно этой фазе** — в том же файле:
```
   ⚠️ ОГРАНИЧЕНИЕ ДЛЯ ТОГО, КТО БУДЕТ ПИСАТЬ ОБЩИЙ КАНАЛ ВИДИМОСТИ ОТКАЗОВ
   (QUAL-03). Помеченный неуспешным ответ валидации НЕ ЕСТЬ отказ сервера.
   Когда FORM-08 будет приземлено, ответ 422 станет ОДНОВРЕМЕННО успешной
   перерисовкой формы и источником htmx:responseError. Канал ОБЯЗАН различать
   их по коду, иначе на каждой ошибке заполнения пользователь получит плашку
   аварии поверх корректно перерисованной формы.
```

**Аналог формы OOB-ответа:** `app/templates/ads/includes/autosave_response.html` —
три блока с `id`, форма `hx-swap-oob="true"`:
```jinja
<div id="ad-preview" hx-swap-oob="true">{% include "ads/includes/preview.html" %}</div>
<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>
{% set oob = true %}{% include "ads/includes/autosave.html" %}
<input type="hidden" id="ad-id-field" name="ad_id" value="{{ ad.id if ad else '' }}" hx-swap-oob="true">
```
⚠️ Строка `{% set oob = true %}` — тот самый **четвёртый OOB, собранный условием Jinja**
внутри `autosave.html:28`; обход гейта разметки обязан его увидеть, иначе `OOB_BLOCKS`
насчитает 3 вместо 4. И ⚠️ форма `hx-swap-oob="true"` (подмена узла) **сосуществует**
с требуемой FOUND-06 формой `innerHTML:` — гейт «OOB обязан быть `innerHTML:`»
относится ТОЛЬКО к области уведомлений, иначе он покраснеет на работающем редакторе.

---

### Пять мест отрисовки плашки → общая область (D-12)

**Точный инвентарь по коду (снят обходом `alert(` в шаблонах):**

| Файл:строка | Сегодняшний вызов |
|---|---|
| `app/templates/billing/balance.html:60` | `<div data-payment-error>{{ alert(error_message, 'error') }}</div>` |
| `app/templates/billing/balance.html:62` | `<div data-access-notice>{{ alert(access_notice, 'warning') }}</div>` |
| `app/templates/ads/form.html:183` | `{{ alert(sched_error) }}` |
| `app/templates/history/list.html:41` | `{{ alert(retry_notice[0], variant=retry_notice[1]) }}` |
| `app/templates/profile.html:18` | `{% if error %}{{ alert(error) }}{% endif %}` |
| `app/templates/auth/login.html:11-12` | `{% if error %}{{ alert(error) }}{% endif %}` / `{% if password_reset_done %}{{ alert('Пароль успешно изменён. Войдите с новым паролем.', 'success') }}{% endif %}` |

⚠️ Прочие ~14 вызовов `alert()` (`account_groups/list.html`, `admin/*`, `accounts/connect_*`,
`auth/register*`, `auth/forgot_password.html`, `history/list.html:28` про потолок выгрузки,
`accounts/partials/connect_status.html`) — **не исходы действия по коду уведомления**, а
контекстные сообщения экрана. В D-12 они не входят; при нарезке планов это надо назвать
явно, иначе «пять мест» разъедется с двадцатью.

---

### Восемь обработчиков старых параметров → `?notice=` (D-09)

**Точный инвентарь `RedirectResponse` со снятыми параметрами (12 мест в 6 файлах):**

| Файл | Сегодня |
|---|---|
| `app/pages/auth.py` | `"/login?reset=success"` |
| `app/pages/profile.py` | `"/profile?saved=1"` |
| `app/pages/billing.py` ×3 | `"/billing?error=disabled"`, `"/billing?error=pending"`, `"/billing?error=payment"` |
| `app/pages/schedules.py` | `f"/ads/{ad_id}/edit?sched_error={reason}"` |
| `app/pages/admin.py` ×2 | `f"{location}?error=no_container"`, `f"{location}?error=restart_failed"` |
| `app/pages/history.py` ×4 | `f"/history?retry={RETRY_BUSY|RETRY_GONE|RETRY_ACCESS_CLOSED|RETRY_QUEUED}"` |

**Канон формы** — `history.py`: код едет **константой**, а не литералом. `billing.py`
сегодня пишет литералы (`?error=pending`) — при переезде приводится к канону
`history.py` (константа кода из `notices.py`).

**Образец ветки-редиректа с обоснованием** — `app/pages/billing.py::subscribe`, строки 390-399:
```python
    except PendingIntentCapError:
        # ОТДЕЛЬНАЯ ВЕТКА, А НЕ ОБЩАЯ С СОСЕДНЕЙ, И ЭТО НЕ ОФОРМЛЕНИЕ. Соседняя
        # говорит человеку «попробуйте ещё раз через минуту» — то есть ровно то
        # действие, которое этот отказ и вызвало. Различаются они ТИПОМ
        # исключения, потому что тип — единственное, что не разъедется.
        return RedirectResponse(url="/billing?error=pending", status_code=302)
    except PaymentCreationError:
        return RedirectResponse(url="/billing?error=payment", status_code=302)
    return RedirectResponse(url=result["confirmation_url"], status_code=302)
```
⚠️ Последняя строка — **внешний адрес ЮKassa**. Ловушка D-15, записанная заранее для
Фазы 11: он НИКОГДА не едет в `redirect=` и уходит `HX-Redirect`, а не `HX-Location`
(`selfRequestsOnly: true`). В Фазе 8 обработчик не переводится — только `?error=` → `?notice=`.

---

### `tests/conftest.py::htmx_client` (fixture, request-response)

**Аналог:** `tests/conftest.py:56-62` (`client`) и `:65-93` (`authed_client`):
```python
@pytest_asyncio.fixture
async def client(db_session, test_settings):
    app = create_app(settings=test_settings)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def authed_client(client, auth_headers):
    """Client with the httpOnly access_token cookie of a regular user.

    Page routes read the cookie, not the Bearer header — auth_headers alone
    does not authorize a page request.
    """
    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )
    return client
```
Стиль: короткий докстринг, называющий **почему фикстура нужна**, а не что делает
(см. `expired_client`, строки 97-110: «без этой фикстуры непроверяем: каждый файл
заводил бы просроченного пользователя своим хелпером»). `htmx_client` надстраивается
над `client` через `headers={"HX-Request": "true"}` + `follow_redirects=True`
(сегодняшнее умолчание проекта — `follow_redirects=False`, строки 91 и 260).

**Форма парного теста (D-16, §`<specifics>`):**
```python
# без заголовка → 302
assert response.status_code == 302
# с заголовком → HX-Location и НЕ документ
assert "HX-Location" in response.headers
assert "<!DOCTYPE" not in response.text
```
Вторая половина закрывает Pitfall 1 целиком одной строкой.

---

### Пакет гейтов — три разные формы, не одна

⚠️ Проект уже провёл эту границу явно, и планировщик обязан её удержать.
`tests/test_templates/test_htmx_inventory.py:36-40`:
```
Файл живёт в ``tests/test_templates/``, а не в ``tests/test_pages/``: это гейт
РАЗМЕТКИ, читающий исходники шаблонов, и его канонический образец —
``test_components.py`` (``ROW_DELETE_PLACES``, ``MODAL_PLACES``). Гейты в
``tests/test_pages/test_access_gate.py`` и ``test_impersonation_gate.py`` —
гейты множеств по синтаксическому дереву Python; форма у них другая.
```

**Форма A — гейт разметки (регулярка по шаблонам).** Аналог: `test_htmx_inventory.py`.
Инвентарные константы и обход:
```python
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"

REVEALED_PLACES = 12
POLL_PLACES = 8
CONDITIONAL_PLACES = 2
HX_GET_PLACES = 22

HX_GET_ATTR = re.compile(r"(?<![-\w])hx-get\s*=")
HX_GET_TAG = re.compile(r"<[^<>]*?(?<![-\w])hx-get\s*=[^<>]*>")
JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.DOTALL)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
```
Копируется: (1) отрицательный lookbehind `(?<![-\w])`, иначе `hx-get` совпадёт внутри
`data-hx-get`; (2) **вырезание комментариев обоих видов до счёта** — правка 07-07,
и её же требует `test_inventory_gate_ignores_prose`; (3) парный контроль
`test_hx_get_tag_count_matches_attribute_count` (счёт атрибутов == счёт тегов) —
ловит атрибут вне тега. Для Фазы 8: `HX_POST_PLACES = 1`, `OOB_BLOCKS = 4`,
`HX_TARGETS = 0`.

**Форма B — гейт множества по AST Python.** Аналог: `tests/test_pages/test_impersonation_gate.py`.
Несущее свойство — **равенство найденного и объявленного** (основание D-08 для G-18):
```
⚠️ ЧЕМ ЭТО ОТЛИЧАЕТСЯ ОТ ЧЁРНОГО СПИСКА — ОДНИМ УТВЕРЖДЕНИЕМ, И ОНО ЗДЕСЬ
ГЛАВНОЕ. `test_every_mutating_route_is_classified` требует, чтобы ОБЪЕДИНЕНИЕ
трёх объявленных множеств равнялось множеству НАЙДЕННЫХ изменяющих маршрутов.
Маршрут, добавленный будущей фазой, не попадёт ни в одно из них и уронит тест —
вместо того чтобы оказаться разрешённым по умолчанию.
```
Оттуда же — четыре обязательных свойства нового гейта:
1. «ЧИТАЕТ ИСХОДНИК, А НЕ СОБРАННОЕ ПРИЛОЖЕНИЕ»;
2. **`test_the_gate_imports_no_application_module`** — гейт не импортирует ни одного модуля `app/`;
3. **ЗУБЫ ДОКАЗАНЫ** — группа `-k control` подаёт разборщику изменённые копии исходника
   и утверждает, что гейт краснеет на нарушении и зеленеет на настоящем дереве
   («Тест, обходящий сорок девять маршрутов и зелёный ПО ПОСТРОЕНИЮ, создавал бы
   уверенность вместо проверки»);
4. **ГРАНИЦЫ ВЫПИСАНЫ В ДОКСТРИНГЕ** — «⚠️ ЧЕГО ГЕЙТ НЕ ВИДИТ — ВЫПИСАНО ЗДЕСЬ, А НЕ
   ОСТАВЛЕНО НА ДОГАДКУ (WR-08)». Для Фазы 8 обязательная запись границы:
   атрибуты, собранные условием Jinja (`{% if oob %}hx-swap-oob="true"{% endif %}`),
   и рекурсивный обход `**/*.py` вместо плоского.

**Форма перечня с обоснованием на запись** — `tests/test_pages/test_access_gate.py:41-58`:
```python
# РОУТЕРЫ, КОТОРЫЕ ЗАКРЫВАЕТ ИСТЁКШИЙ ДОСТУП. Перечень выписан ЗДЕСЬ, а не
# выведен из исходника: тест, выводящий ожидание из проверяемого, согласился бы
# с любой правкой. Изменение этого множества обязано быть решением, записанным
# в двух местах сразу.
GATED_ROUTERS = {
    "ads_router",
    ...
}

# РОУТЕРЫ, КОТОРЫЕ НЕ ЗАКРЫВАЮТСЯ НИКОГДА (T-05.1-03). Вход, регистрация и
# выход — иначе человек не может даже войти, чтобы заплатить; <...>
```
→ прямая форма для **двух списков G-1** (D-14): `NEVER_RESPONDS` (исключения с
обоснованием на каждую запись) и `NOT_YET_CONVERTED = 35` (убывающее число).
⚠️ §`<specifics>`: сообщение об отказе второго списка формулируется как
«фаза N вернула обработчик назад», а не «список устарел».

**Форма C — гейт по дереву разбора над `app/`.** Аналог: `tests/test_pages/test_htmx_response_contract.py`
— прямой образец для G-13 (AST на правый операнд `response.headers["HX-*"]`):
```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"
VALIDATION_STATUS_CODE = 422
SERVER_SIDE_VALIDATION_RESPONSES = 0
...
            tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "status_code":
                ...
                # в ast.Attribute, а не в ast.Constant, поэтому ветка выше его не …
```
Копируется: разбор обеих форм записи (`ast.Constant` **и** `ast.Attribute` — константа
`status.HTTP_*`), обход `ast.walk` по всем файлам `app/`, инвентарь-ноль как
именованная константа (`SERVER_SIDE_VALIDATION_RESPONSES = 0` — прецедент для `HX_TARGETS = 0`).

---

### `tests/test_pages/test_shell.py` (G-23)

**Аналог:** сам файл. Стиль утверждений — по СОДЕРЖИМОМУ ответа, не по имени файла
(строки 30-45), с абзацем-комментарием на каждую величину. Фаза дописывает: обе
`aria-live`-области, оба обработчика ошибок, скрытая заготовка плашки, `samesite == "lax"`
(записанное решение, а не наблюдение — ROADMAP §«Перенесено незакрытым из v2.0»).

---

## Shared Patterns

### 1. Инвентарный гейт числом, собранным СОБСТВЕННЫМ обходом (D-13)
**Источник:** `tests/test_templates/test_htmx_inventory.py:107-139`, `tests/test_pages/test_htmx_response_contract.py:72`
**Применять к:** каждому гейту пакета (G-3…G-7, G-9…G-15, G-23)
```python
REVEALED_PLACES = 12
POLL_PLACES = 8
CONDITIONAL_PLACES = 2
HX_GET_PLACES = 22
```
Обоснование, которого нет у сводного счётчика (D-13): собственное число ловит **не только
пустоту, но и сломанный обход** — опечатка в регулярке даёт тот же зелёный ноль.

### 2. Гейт читает исходник, а не собранное приложение
**Источник:** `tests/test_pages/test_access_gate.py:19-27`
**Применять к:** G-1/G-2, G-13, G-18
```
ПОЧЕМУ ГЕЙТ ПЕРЕЧНЯ ЧИТАЕТ ИСХОДНИК, А НЕ СОБРАННОЕ ПРИЛОЖЕНИЕ. Цель —
поймать роутер, добавленный БУДУЩИМ планом БЕЗ зависимости. В объекте
приложения такой роутер выглядит совершенно обычно: у его маршрутов просто нет
одной зависимости, и отличить «забыли» от «не должно быть» там нечем. В
исходнике же решение записано явным вызовом, и множество вызовов замкнуто.
```

### 3. Закрытое множество вместо непустой строки
**Источник:** `app/pages/billing.py:145` (`PAYMENT_ERROR_MESSAGES.get(code or "", "")`),
`app/pages/history.py:1170` (`RETRY_NOTICES.get(retry)`), `app/pages/ads.py:670` (`in SCHEDULE_ERROR_REASONS`)
**Применять к:** `app/pages/notices.py` целиком
Плашка по любому непустому значению параметра позволила бы владельцу ссылки нарисовать
пользователю сообщение о событии, которого не было.

### 4. Один источник вместо второй копии (единственный владелец включения)
**Источник:** `app/templates/includes/htmx_config.html` (шапка, D-01)
**Применять к:** областям уведомлений, заготовке плашки, обработчикам ошибок — по одному
файлу-включению, приезжающему в **оба** шелла; тест единственности, а не договорённость.

### 5. Разбор отказа ограничения по имени, чужой отказ — наружу
**Источник:** `app/services/payment_service.py:798-825`
**Применять к:** `create_payment` (D-06)
```python
    except IntegrityError as rejection:
        logger.info("subscription_insert_lost", ...)
        rejected_by = rejection
    ...
    if subscription is None:
        raise rejected_by
```

### 6. Ленивая уборка просроченных окон на своём же пути
**Источник:** `app/pages/history.py:538-565` (`_claim_retry_slot`)
**Применять к:** `create_payment` (D-02) — уборка просроченных намерений перед вставкой резерва.
Обоснование, дословно переносимое: «обхода реестра нет нигде, периодической задачи под него
не заведено», плюс довод D-02 о втором писателе на денежный путь.

### 7. Комментарий объясняет ПОЧЕМУ, а снятое решение переписывается, а не остаётся рядом
**Источник:** сквозной; образцы — `payment_service.py:40-52`, `billing.py:105-116`,
`includes/htmx_config.html` («⚠️ ПРЕЖНЕЕ ОБЪЯСНЕНИЕ СНЯТО КАК НЕВЕРНОЕ ДЛЯ ОТГРУЖЕННОГО АРТЕФАКТА»)
**Применять к:** всем правкам фазы. Конкретно обязаны быть переписаны, а не дополнены:
комментарий над `PENDING_INTENT_TTL_HOURS` (D-04), абзац «ЧТО ЗАКРЫЛО БЫ ОКНО СВОЙСТВОМ…»
в докстринге `create_payment`, комментарий T-05-49 о порядке «сеть → запись» (D-05).

### 8. Ни одной новой Python-зависимости, никакого build-шага
**Источник:** `.planning/research/SUMMARY.md` §R-1; D-02 фазы 01 вехи v2.0
**Применять к:** `htmx.py`, `notices.py`, обработчикам ошибок (чистый инлайн-JS без сборки).

---

## No Analog Found

| Файл / предмет | Роль | Поток данных | Причина |
|---|---|---|---|
| Узкий выход `app/pages/htmx.py` для **отказа зависимости** (D-15, FOUND-07) | utility | request-response | Ни один сегодняшний код не возвращает 2xx с `HX-Location` из зависимости. `HTTPException(status_code=200)` отдаёт тело `{"detail": …}` — то есть JSON, что FOUND-07 прямо запрещает; `RedirectResponse` из зависимости FastAPI отбрасывает (`require_access`, строки 72-84). Форма решения — за планировщиком (Claude's Discretion). Опоры: форма отказа `require_access` (302+`location`) и `forbid_when_impersonating` (403+`detail`) — покрыть надо **обе**. |
| Гейт `docker-compose.prod.yml` на `--workers` / `deploy.replicas` (D-07) | test | file-I/O | Ни один тест проекта не читает compose-артефакт. Ближайшее по форме — `test_htmx_inventory.py` (чтение файла-исходника + утверждение состава). Предмет гейта: `docker-compose.prod.yml:91-107`, сервис `web` — один контейнер, `command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 --forwarded-allow-ips=*`, без `--workers` и без `deploy.replicas`. |
| Сборка реестра **из пар с гейтом на уникальность** вместо литерала словаря (D-10) | config | transform | Все три сегодняшних реестра — литеральные словари, то есть ровно та форма, которую D-10 отвергает (дубль ключа = молчаливая перезапись). Ближайшее — `NamedTuple`-таблицы `test_htmx_inventory.py:44`. |

---

## Metadata

**Analog search scope:** `app/pages/`, `app/services/`, `app/models/`, `app/templates/`,
`app/dependencies.py`, `alembic/versions/`, `tests/test_pages/`, `tests/test_templates/`,
`tests/conftest.py`, `docker-compose.prod.yml`
**Files scanned:** 24 прочитано целиком или прицельными срезами; ~10 инвентаризовано грепом
**Pattern extraction date:** 2026-08-28
