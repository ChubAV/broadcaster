# Phase 13: Мастер подключения Telegram по QR на фрагментах — Pattern Map

**Mapped:** 2026-09-21
**Files analyzed:** 13 (3 исходных, 1 новый шаблон, 1 переписываемый шаблон, 8 тестовых/гейтовых)
**Analogs found:** 12 / 13

> ⚠️ Опрос НЕ копируется с мастеров WA/MAX. У них якорь и `hx-trigger` стоят на одном элементе
> (`max_connect_step.html:69`, `connect_wa.html:34`), и гейт числит их вечными (`PERMANENT_POLLS`).
> RESEARCH §Pitfall 1 отменяет посылку D-05: форма-опросчик лежит ВНУТРИ фрагмента ожидания и целится
> в постоянный якорь `#tg-connect-step` через `hx-target`. Механизм останова — как у
> `accounts/partials/sync_status_card.html` (ответ без триггера), форма-обёртка — из `form_wrapper`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/pages/accounts.py` (4 обработчика TG, снять `complete`, помощники `_tg_step_markup`, `_save_tg_account`) | controller | request-response (+ опрос) | `accounts_connect_max_start` + `_max_step_markup` (`app/pages/accounts.py:541-681`) | exact |
| `app/templates/accounts/includes/tg_connect_step.html` (НОВЫЙ) | component (включаемый шаг) | request-response / polling | `app/templates/accounts/includes/max_connect_step.html` | exact по раскладке, опрос — по `sync_status_card.html` |
| `app/templates/accounts/connect_tg_user.html` (переписать: якорь + include, скрипт снят) | page template | — | `app/templates/accounts/connect_max.html:10-20` | exact |
| `app/messengers/telegram_user.py` (`QRAuthState.user_id`, `qr_expired`, `_owned`) | service (in-memory state) | event-driven (фоновая задача) | сам файл (`:31-172`) | self |
| `tests/test_routes/test_tg_user_auth.py` (переписать на фрагменты) | test | request-response | сам файл (фикстура `auth_setup` `:15-65`) + `test_htmx_preserved.py:290-318` | exact |
| `tests/test_messengers/test_telegram_user.py` (сигнатура `start_qr_auth`, `user_id`) | test | unit | сам файл `:331-360` | self |
| `tests/test_pages/test_htmx_post_pairs.py` (случаи TG) | test (гейт) | registry | пара MAX `:1432-1447` | exact |
| `tests/test_pages/test_htmx_gates.py` (`NOT_YET_CONVERTED`, `FRAGMENT_RESPONSE_HANDLERS`, `POST_HANDLERS`) | test (гейт) | registry | записи MAX в тех же перечнях | exact |
| `tests/test_templates/test_htmx_inventory.py` (`MANUAL_FETCH_*`, контроль `:1308-1330`) | test (гейт) | registry | — (именованный ноль) | role-match |
| `tests/test_pages/test_hx_location_destinations.py` (`TOP_LEVEL_BINDING_EXEMPT_TEMPLATES`, `…CALLS_DECLARED`) | test (гейт) | registry | — (именованный ноль) | role-match |
| `tests/test_templates/test_htmx_markup_gates.py` (callers `form_wrapper`, `DISABLED_ELT_EXCEPTIONS`) | test (гейт) | registry | запись `ads/includes/sched_card.html` в тех же кортежах | exact |
| `tests/test_pages/test_impersonation_gate.py:222-225`, `test_identifier_bounds.py:1499-1508`, `test_htmx_markup_security.py:63-70` | test (гейт) | registry | соседние записи тех же перечней | exact |
| Тест «два опроса после success → один аккаунт» | test (concurrency) | — | нет | none |

## Pattern Assignments

### `app/pages/accounts.py` — обработчики TG (controller, request-response)

**Analog:** `accounts_connect_max_start` и `_max_step_markup`, `app/pages/accounts.py:541-681`.

**Помощник разметки шага** (строки 541-567) — копировать форму, заменив имя шаблона и контекст:
```python
MAX_CONNECT_STEP_TEMPLATE = "accounts/includes/max_connect_step.html"

def _max_step_markup(*, step: str, qr_code: str | None = None, error: str | None = None, phone: str = "") -> str:
    return templates.env.get_template(MAX_CONNECT_STEP_TEMPLATE).render(
        connected=False, step=step, qr_code=qr_code, error=error, phone=phone
    )
```
Для TG: `TG_CONNECT_STEP_TEMPLATE = "accounts/includes/tg_connect_step.html"`, `TG_WIZARD = "/accounts/connect/tg_user"`, `_tg_step_markup(*, step, session_id=None, qr_code=None, error=None)`.

**Нет сессии входа (D-10)** (строки 608-610):
```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    return await respond(request, redirect="/login")
```
Заменяет сегодняшние `return {"error": "Не авторизован"}` (`:234`, `:264`, `:276`, `:299`, `:338`).

**Чтение поля формы внутри обработчика, а не `Form(...)`** (строки 612-614, Pitfall 8):
```python
form = await request.form()
submitted = form.get("phone") or ""
```
Для TG: `session_id = str(form.get("session_id") or "")`, `password = str(form.get("password") or "")`. Сегодняшний `request.json()` (`:280`, `:302`) и `session_id: str = Query(...)` (`:260`) снимаются.

**Ошибка поля 422 на оба транспорта (D-08)** (строки 616-638) — образец для неверного/пустого пароля 2FA:
```python
if not phone:
    async def _page() -> HTMLResponse:
        return templates.TemplateResponse("accounts/connect_max.html", {
            "request": request, "user": user, "is_admin": check_is_admin(user, settings),
            "active_page": "accounts", "step": "phone", "error": MAX_EMPTY_PHONE_ERROR, "phone": submitted,
        })

    async def _fragment() -> HTMLResponse:
        return HTMLResponse(_max_step_markup(step="phone", error=MAX_EMPTY_PHONE_ERROR, phone=submitted))

    return await respond_field_error(request, page=_page, fragment=_fragment)
```
Отличие для TG: пароль НЕ эхается (`phone=submitted` не копировать), `session_id` в контекст передаётся, чтобы форма 2FA сохранила скрытое поле.

**Исход фрагментом через сборщик ИМЕНЕМ** (строки 677-681):
```python
async def _step() -> HTMLResponse:
    return HTMLResponse(_max_step_markup(step="qr", qr_code=qr_code, error=error))

return await respond(request, redirect="/accounts", fragment=_step)
```
Для TG `redirect=TG_WIZARD` (D-11). Ответ 204 на `waiting` — тоже сборщиком (`async def _unchanged(): return Response(status_code=204)`), иначе нужна запись в `OWN_RESPONSE_EXITS` (RESEARCH §Pattern 6).

**Что снимается / сводится** (сегодняшний код `:226-354`):
- `@router.post("/accounts/connect/tg_user/complete")` (`:329-354`) — снимается целиком (D-01).
- `@router.get(".../qr-status")` (`:255-266`) → `@router.post(..., response_class=HTMLResponse)`.
- Два одинаковых блока создания аккаунта (`:308-316`, `:342-350`) сводятся в `_save_tg_account(db, user, session_string)`; строку сессии брать из результата `complete_auth`, а не из `submit_2fa` (RESEARCH §Pattern 3):
```python
account = MessengerAccount(user_id=user.id, type="tg_user", credentials=session_string, status="active")
db.add(account)
await db.commit()
```
- Тексты дословно: «Telegram API не настроен. Обратитесь к администратору.» (`:237`), «Ошибка запуска QR авторизации: {e}» (`:245`).
- `_generate_qr_base64` (`:128-133`) — без изменений.

---

### `app/templates/accounts/includes/tg_connect_step.html` (component, polling) — НОВЫЙ

**Analog раскладки:** `app/templates/accounts/includes/max_connect_step.html` (100 строк).

**Импорты макросов** (строки 19-24):
```jinja
{% from "components/card.html" import card_open, card_close %}
{% from "components/button.html" import button, link_button %}
{% from "components/badge.html" import badge %}
{% from "components/alert.html" import alert %}
{% from "components/field.html" import field %}
{% from "components/form_wrapper.html" import form_wrapper %}
```

**Алерт вне карточки, ветки по `step`** (строки 26-36):
```jinja
  {% if error %}{{ alert(error) }}{% endif %}

  {{ card_open() }}
  {% if connected %}
  <div class="connect-step connect-step--center">
    {{ badge('Подключено', 'success') }}
    <p class="connect-step__text">Ваш аккаунт MAX готов к использованию.</p>
    {{ link_button('К аккаунтам', '/accounts') }}
  </div>
  {% elif step == "phone" %}
```
Ветки TG: `start | waiting | qr_expired | password | connected | gone | error`. «Подключено» — ровно эта форма (D-07), без `setTimeout`/`HX-Location`.

**Форма шага через обёртку** (строка 64):
```jinja
{% call form_wrapper(action='/accounts/connect/max/start', target='#max-connect-step', swap='innerHTML') %}
```
Для кнопок «Начать» / «Обновить QR-код» / «Начать заново» / формы 2FA — та же форма с `target='#tg-connect-step', swap='innerHTML'`. Поле пароля — `field(...)` с `required`, без `value`.

**Опросчик — НЕ копировать** строку 69 MAX (`<div id="max-status" hx-get=… hx-trigger="every 3s">` — вечный опрос). Вместо неё — форма обёртки с `trigger=` и `disabled_elt=''`, по образцу `app/templates/ads/includes/sched_card.html:167-168`:
```jinja
{% call form_wrapper(action='/schedules/' ~ s.id ~ '/toggle', target='#sched-' ~ s.id, swap='outerHTML',
                     trigger='change', disabled_elt='', sync='this:drop') %}
  <input type="hidden" name="return_to" value="editor">
```
Для TG (в ветке `waiting`, внутри фрагмента, без `sync` — RESEARCH §Pattern 2):
```jinja
{% call form_wrapper(action='/accounts/connect/tg_user/qr-status', target='#tg-connect-step',
                     swap='innerHTML', trigger='every 3s', disabled_elt='') %}
  <input type="hidden" name="session_id" value="{{ session_id }}">
{% endcall %}
```
Что печатает макрос (`app/templates/components/form_wrapper.html:187-195`):
```jinja
{% macro form_wrapper(action, target=None, swap=None, trigger=None, disabled_elt='find button[type=submit]', sync=None, encoding=false, include=None) -%}
<form method="post" action="{{ action }}" hx-post="{{ action }}" class="form-wrapper"
      {%- if target %} hx-target="{{ target }}" hx-swap="{{ swap or 'outerHTML' }}"
      {%- else %} hx-swap="none"{% endif %}
      {%- if trigger %} hx-trigger="{{ trigger }}"{% endif %}
      ...
      {%- if disabled_elt %} hx-disabled-elt="{{ disabled_elt }}"{% endif %} hx-indicator="find .form-busy">
```

**Механизм останова** — `app/templates/accounts/partials/sync_status_card.html:3-12` (докстринг скопировать по смыслу в шапку нового шаблона): «команды „стоп“ у опроса нет: он прекращается тем, что очередной ответ приходит БЕЗ атрибутов запроса и триггера». У TG это обеспечивается тем, что только ветка `waiting` содержит опросчик.

**QR-картинка** — как `max_connect_step.html:71`: `<div class="connect-qr"><img src="{{ qr_code }}" alt="Telegram QR-код"></div>`.

---

### `app/templates/accounts/connect_tg_user.html` (page template)

**Analog:** `app/templates/accounts/connect_max.html:10-20`:
```jinja
<div class="connect-shell" id="max-connect-step">
  {% include "accounts/includes/max_connect_step.html" %}
</div>
```
Для TG: `<div class="connect-shell" id="tg-connect-step">{% include "accounts/includes/tg_connect_step.html" %}</div>`, контекст страницы `step="start"`. Снимаются: скрипт `:71-223`, три `onclick`, четыре `hidden`-секции, `#error-box`. Итог `fetch(` = 0.

---

### `app/messengers/telegram_user.py` (service, event-driven) — точечно D-01/D-03/D-04

**Analog:** сам файл.

- `QRAuthState` (`:31-39`) — добавить `user_id: int` (и `"qr_expired"` в комментарий статусов `:35`).
- `start_qr_auth(api_id, api_hash)` (`:54-74`) → `start_qr_auth(api_id, api_hash, user_id)`; `QRAuthState(client=client, qr_login=qr_login, user_id=user_id)` (`:68`).
- `_wait_for_qr` (`:83-97`) — ветка ДО общего `except Exception`, после `CancelledError`:
```python
    except asyncio.CancelledError:
        pass
    except asyncio.TimeoutError:      # D-03: токен истёк, сессия жива; без logger.error
        state.status = "qr_expired"
    except Exception as e:
```
- `_owned(session_id, user_id) -> QRAuthState | None` — один помощник для `get_qr_status` (`:100`), `refresh_qr` (`:115`), `submit_2fa` (`:137`), `complete_auth` (`:155`). В `complete_auth` проверка владельца через `.get` ДО `pop` (`:157`), без `await` между ними.
- `refresh_qr` — добавить проверку `time.time() - state.created_at > QR_SESSION_TTL` и `status == "qr_expired"` в начале (RESEARCH Pitfall 2). `QR_SESSION_TTL`, `_cleanup_expired_sessions` не трогать (D-13).

---

### `tests/test_routes/test_tg_user_auth.py` (test)

**Analog:** фикстура `auth_setup` (`:15-65`) остаётся; патчинг — `patch("app.pages.accounts.start_qr_auth", new_callable=AsyncMock)` (`:81`). Утверждения переводятся с `resp.json()` на HTML + заголовок `HX-Request: true`. Тесты `complete` (`:180-219`) переписываются в тесты опроса `success`.

**Парные тесты останова** — `tests/test_pages/test_htmx_preserved.py:290-318`:
```python
response = await authed_client.get(f"/accounts/{account.id}/sync-status?layout=cards")
assert response.status_code == 200
assert "hx-trigger" not in response.text
...
# парный:
assert "hx-trigger" in response.text
```
Для TG: фрагмент ожидания (ответ `start-qr`, `refresh-qr`) содержит `hx-trigger="every 3s"`; каждый ответ опроса / 2FA / ошибки — без `hx-trigger`. Тест D-03 обязан подменять `wait()` на `side_effect=asyncio.TimeoutError`, а не ставить `status="qr_expired"` напрямую.

### `tests/test_messengers/test_telegram_user.py` (test)
`:331-360`: `start_qr_auth(api_id=12345, api_hash="test_hash")` → с `user_id=`; `QRAuthState(client=AsyncMock(), status="waiting", created_at=time.time())` → с `user_id=`.

### `tests/test_pages/test_htmx_post_pairs.py` (гейт)
**Analog:** пара MAX `:1437-1450`:
```python
_PairCase(key=ACCOUNTS_CONNECT_MAX_START, name="старт подключения MAX — успех", identity="user",
          arrange=_arrange_max_start, landing="/accounts", transport=FRAGMENT, fragment_mark='id="max-status"'),
_PairCase(key=ACCOUNTS_CONNECT_MAX_START, name="старт подключения MAX — нет сессии", identity="user",
          arrange=_arrange_max_start_without_session, landing="/login", transport=LOCATION),
```
Для TG `landing="/accounts/connect/tg_user"`; случай `qr-status` сеять в состоянии, дающем фрагмент (не `waiting` → 204), Pitfall 7.

### Остальные гейты
Карта всех движимых чисел — RESEARCH §Инвентарь гейтов (строки 1-21 таблицы). Паттерн для гейтов: числа ставятся прогоном; контрольный тест `test_htmx_inventory.py:1308-1330` и правило непустоты `test_hx_location_destinations.py:1189-1191` переписываются в форму «именованный ноль» / синтетика, а не удаляются. Новый шаблон добавляется в кортежи вызывающих `form_wrapper` (`test_htmx_markup_gates.py:1429`, `:2653`) и в `DISABLED_ELT_EXCEPTIONS["components/form_wrapper.html"].callers` (`:3632-3638`) рядом с `ads/includes/sched_card.html`.

## Shared Patterns

### Слой ответа
**Source:** `app/pages/htmx.py` — `respond` (`:712`, `redirect` ключевой обязательный), `respond_field_error` (`:847`, `page`+`fragment`), `HtmxRefusal` (`:188`).
**Apply to:** все четыре обработчика TG. Признак htmx в обработчике не читать (G-1/G-2).

### Аутентификация
**Source:** `app/pages/accounts.py:608-610` (`get_user_from_cookie` → `respond(redirect="/login")`). Под имперсонацией возвращается субъект (`app/pages/common.py:593-609`) — привязка сессии к `user.id`.

### Формы
**Source:** `app/templates/components/form_wrapper.html:187-195`. Все формы мастера, включая опросчик, — только через макрос (гейт `test_every_htmx_post_is_born_of_a_component_macro`).

### Тексты отказа
Переносятся дословно (`accounts.py:237, 245`; `telegram_user.py:141, 148`).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Тест «два конкурентных опроса после `success` → один `MessengerAccount`» | test | concurrency | Конкурентных тестов через `asyncio.gather` в наборе нет; схема — RESEARCH §Pattern 3 (настоящий `QRAuthState`, `client.disconnect` с `await asyncio.sleep(0)`, `complete_auth` не подменять) |
| Опрос, останавливаемый ответом, на POST-форме | component | polling | Оба существующих самоостанавливающихся опроса — GET на самом элементе с `outerHTML`; комбинация «форма-опросчик внутри фрагмента + `hx-target` на якорь» новая, собирается из `form_wrapper(trigger=)` + механизма `sync_status_card.html` |

## Metadata

**Analog search scope:** `app/pages/`, `app/templates/accounts/`, `app/templates/components/`, `app/templates/ads/includes/`, `app/messengers/`, `tests/test_pages/`, `tests/test_routes/`, `tests/test_messengers/`
**Files scanned:** ~14
**Pattern extraction date:** 2026-09-21
