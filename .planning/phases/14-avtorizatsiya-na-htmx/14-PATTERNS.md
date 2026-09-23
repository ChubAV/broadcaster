# Phase 14: Авторизация на htmx — Pattern Map

**Mapped:** 2026-09-22
**Files analyzed:** 22 (новых 3 группы, изменяемых 19)
**Analogs found:** 21 / 22

Номера строк сняты с дерева ветки `gsd/phase-14-avtorizatsiya-na-htmx` (HEAD `1934b826`). Все пути аналогов — tracked (`git ls-files`). Новые файлы помечены **НОВЫЙ**.

## File Classification

| Новый/изменяемый файл | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `app/pages/htmx.py` (+ выход шага `respond_screen`, + выход полной перезагрузки `redirect_internal`) | utility (слой ответа) | request-response | `respond_field_error` (`htmx.py:847-904`), `redirect_external` (`htmx.py:345-393`) | exact |
| `app/pages/auth.py` (десять обработчиков) | controller | request-response | `accounts.py::accounts_connect_max_start` (`accounts.py:828-892`) + `admin.py` (`:1883-1884`) | exact |
| `app/templates/auth/includes/*_step.html` (семь экранов) — **НОВЫЙ** | component (включаемый шаблон) | transform (SSR) | `app/templates/accounts/includes/max_connect_step.html` | exact |
| `app/templates/auth/includes/step_response.html` — **НОВЫЙ** (имя — рекомендация RESEARCH) | component (обёртка фрагмента с `<title>`) | transform | нет прямого (см. No Analog) | — |
| `app/templates/auth/*.html` (семь страниц) | component (страница) | transform | `accounts/connect_max.html` через include шага | role-match |
| `app/templates/auth_base.html` (якорь `#auth-step`) | component (шелл) | — | сам файл; якорь `#max-connect-step` | role-match |
| `app/templates/base.html:74` (форма возврата) | component | request-response | `form_wrapper` без `target` (`account_groups/list.html`, `hx-swap="none"`) | exact |
| `app/static/css/app.css` (`#auth-step`, `.auth-form` на внутреннем узле, `.impersonation-back`) | config (стили) | — | приём «коробку даёт внутренний узел» (`max_connect_step.html:59-68`) | role-match |
| `tests/test_pages/test_auth_transport.py` — **НОВЫЙ** | test | request-response | `tests/test_pages/test_max_connect_transport.py:125-175` | exact |
| `tests/test_pages/test_impersonation.py` (htmx-половины возврата) | test | request-response | тот же файл, `:208-…` (тройная пара) | exact |
| `tests/test_pages/test_registration.py`, `test_password_reset.py`, `test_blocked_user.py`, `test_cookie_flags.py`, `test_trial.py`, `test_reset_code_source.py` | test | request-response | правка статусов 200→422 (Pitfall 6) | exact |
| `tests/test_pages/test_htmx_gates.py` | test (гейт) | batch (AST-обход) | сам файл: `_calls_response_layer` `:925-941`, `_fragment_builder_names` `:4217-4268`, `NOT_YET_CONVERTED` `:265-281`, `OWN_RESPONSE_EXITS` `:4476` | exact |
| `tests/test_pages/test_htmx_post_pairs.py` | test (гейт пар) | request-response | ветка `EXTERNAL` `:1890-1912`, `_PairCase` `:113` | exact |
| `tests/test_pages/test_hx_location_destinations.py` | test (гейт) | batch | `HX_LOCATION_DESTINATION_TEMPLATES` `:502-517` | exact |
| `tests/test_pages/test_htmx_response_contract.py` | test (гейт) | batch | `SERVER_SIDE_VALIDATION_RESPONSES = 2` `:115` | exact |
| `tests/test_pages/test_impersonation_gate.py`, `test_identifier_bounds.py` | test (гейт) | batch | числа ставит прогон | exact |
| `tests/test_templates/test_htmx_markup_gates.py` | test (гейт разметки) | batch | `MACRO_DEFINITION_SITES_CALLERS` `:1414`, `PARAMETRIC_SWAP_TARGETS` `:2682`, `LONG_LIVED_REGION_IDS` `:2511` | exact |
| `.planning/WINDOWS.md:80`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (летописи) | config (записи) | — | идиома D-30/D-32 | role-match |

## Pattern Assignments

### `app/pages/htmx.py` — выход шага (utility, request-response)

**Аналог:** `respond_field_error`, `app/pages/htmx.py:847-904`. Сигнатура и тело:
```python
async def respond_field_error(
    request: Request,
    *,
    page: Callable[[], Awaitable[Response]],
    fragment: Callable[[], Awaitable[Response]],
) -> Response:
    ...
    built = await (fragment if is_htmx(request) else page)()

    body = getattr(built, "body", None)
    if body is None:
        raise ValueError(
            "сборщик ответа об ошибке заполнения вернул ответ без собранного "
            "тела (потоковый ответ): пересобрать его с кодом ошибки нечем, а "
            "молча отданная пустота стёрла бы форму вместе с введённым"
        )

    return HTMLResponse(body, status_code=422)
```
Что копировать: `respond_screen(request, *, page, fragment)` — тот же контракт, код **200**; общее тело — в закрытый помощник `_respond_by_transport(..., status_code=)` (RESEARCH Pattern 1). Сигнатура `respond_field_error` не меняется. Докстринг в стиле модуля: блоки `⚠️ …` с основанием (почему не `respond()` — путь без JS потерял бы `token`, Находка 1). Если литерал `422` переезжает в вызов — `SERVER_SIDE_VALIDATION_RESPONSES` (`test_htmx_response_contract.py:115`) ставит прогон.

### `app/pages/htmx.py` — выход полной перезагрузки (utility, request-response)

**Аналог:** `redirect_external`, `app/pages/htmx.py:345-393`; проверки адреса — `_local_path` (`:207-248`), код исхода — как в `respond` (`:712-…`).
```python
async def redirect_external(
    request: Request, *, url: str, fallback: str, fallback_notice: str
) -> Response:
    ...
    if not is_htmx(request):
        return RedirectResponse(url=url, status_code=302)
    ...
    return Response(status_code=204, headers={HX_REDIRECT_HEADER: checked})
```
Проверка кода исхода и адреса — из `respond` (`htmx.py` в теле `respond`):
```python
    if notice is not None:
        _require_registered_notice(notice)

    if not is_htmx(request):
        return RedirectResponse(url=_with_notice(redirect, notice), status_code=302)
```
Что копировать: отдельная функция `redirect_internal(request, *, redirect: str, notice: str | None = None)` — `_require_registered_notice` → `location = _with_notice(redirect, notice)` (внутри `_local_path`: только `/…`, ASCII) → 302 без htmx / `Response(204, headers={HX_REDIRECT_HEADER: location})`. **`redirect_external` не трогать** (D-11). Ровно один заголовок перехода. Гейты: `HX_HEADER_WRITES = 5` → 6 (`test_htmx_gates.py:227`) + запись `SAFE_BY_NAME`.

---

### `app/pages/auth.py` — десять обработчиков (controller, request-response)

**Аналог ошибки поля + сборщики:** `app/pages/accounts.py:802-825` и `:869-892`.
```python
def _max_step_markup(*, step: str, qr_code: str | None = None, error: str | None = None, phone: str = "") -> str:
    return templates.env.get_template(MAX_CONNECT_STEP_TEMPLATE).render(
        connected=False, step=step, qr_code=qr_code, error=error, phone=phone
    )
...
        async def _page() -> HTMLResponse:
            """Страница мастера с ошибкой поля — путь деградации ошибки заполнения."""
            return templates.TemplateResponse(
                "accounts/connect_max.html",
                {"request": request, ..., "step": "phone", "error": MAX_EMPTY_PHONE_ERROR, "phone": submitted},
            )

        async def _fragment() -> HTMLResponse:
            """Тот же включаемый шаг с тем же контекстом — без шелла."""
            return HTMLResponse(
                _max_step_markup(step="phone", error=MAX_EMPTY_PHONE_ERROR, phone=submitted)
            )

        return await respond_field_error(request, page=_page, fragment=_fragment)
```
Для auth: `_screen_markup(screen, **ctx)` рендерит `auth/includes/step_response.html` (`<title>` верхним узлом + include экрана) через `templates.env.get_template(...).render(...)`; ни `|safe`, ни `Markup(`. Сборщики подаются ИМЕНЕМ (`page=_page`, `fragment=_fragment`) — иначе `_fragment_builder_names` их не узнает. Эхо: `email`, `code`, `name`; пароль в контекст не передаётся никогда.

**Аналог cookie на возвращаемом ответе:** `app/pages/admin.py:1870-1884`.
```python
    # ⚠️ ПОРЯДОК ЗДЕСЬ НЕСУЩИЙ: СНАЧАЛА БЕРЁТСЯ РЕЗУЛЬТАТ СЛОЯ ОТВЕТА, И ТОЛЬКО
    # ПОТОМ НА ЭТОТ ЖЕ ОБЪЕКТ НАВЕШИВАЕТСЯ COOKIE. ...
    response = await respond(request, redirect="/dashboard")
    set_session_cookie(response, token, settings)
```
Применение: `login_submit`, `register_complete` → `redirect_internal(request, redirect="/dashboard")` + `set_session_cookie`; `forgot_password_reset` → `redirect_internal(request, redirect="/login", notice=notices.PASSWORD_RESET_DONE)`; `stop_impersonation` успех → `respond(request, redirect="/admin")` + `set_session_cookie`; нет действующего лица → `respond(request, redirect="/dashboard")`; админа нет/заблокирован → `redirect_internal(request, redirect="/login")` + `clear_session_cookie`.

**Что сегодня снимается** (`auth.py:115-138`, образец одного из десяти):
```python
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html", {"request": request, "error": "Неверный email или пароль"}
        )
    if user.is_blocked:
        logger.warning("blocked_login_refused", user_id=user.id)
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": BLOCKED_LOGIN_ERROR},
        )
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(response, token, settings)
    return response
```
Порядок «пароль → блокировка → cookie» сохраняется (D-05). В `register_complete` (`auth.py:410-427`) `start_trial` + commit остаются ДО выдачи cookie. `stop_impersonation` (`auth.py:442-…`): голый `Response(status_code=403)` на `:479` остаётся (D-01). Полная карта исходов — RESEARCH §«Карта выходов десяти обработчиков».

---

### `app/templates/auth/includes/*_step.html` (component, SSR) — НОВЫЕ

**Аналог:** `app/templates/accounts/includes/max_connect_step.html` (шапка-комментарий `:1-17`, импорты `:18-23`, форма `:28-68`).
```jinja
{% from "components/field.html" import field %}
{% from "components/form_wrapper.html" import form_wrapper %}
  {% if error %}{{ alert(error) }}{% endif %}
    {% call form_wrapper(action='/accounts/connect/max/start', target='#max-connect-step', swap='innerHTML') %}
    <div class="connect-step__form">
      {{ field(name="phone", label='Номер телефона', type='tel', value=phone or '', placeholder='+7 999 123-45-67', required=true, autocomplete='tel') }}
      {{ button('Продолжить', variant='primary', extra_class='btn--block') }}
    </div>
    {% endcall %}
```
Для auth: `target='#auth-step', swap='innerHTML'`; класс колонки `auth-form` — на внутреннем `<div>`, а не на теге формы (макрос печатает `class="form-wrapper"`, `form_wrapper.html:188`). Подзаголовок `<p class="auth-subtitle">` печатает экран (блок `auth_subtitle` шелла снимается). Эхо — параметр `value=` макроса `field` (`components/field.html:7`), ошибка — `error=`. Экран кода: две формы с общим `token`, рекомендация `sync='closest #auth-step:drop'`. Исходная разметка для переноса — `auth/login.html:18-27`, `auth/register_verify.html:8-25` и т. д.

Сигнатура макроса (`components/form_wrapper.html:187`):
```jinja
{% macro form_wrapper(action, target=None, swap=None, trigger=None, disabled_elt='find button[type=submit]', sync=None, encoding=false, include=None) -%}
```

### `app/templates/auth/*.html` (страницы)
Схема: `{% extends "auth_base.html" %}{% block title %}…{% endblock %}{% block content %}{% include "auth/includes/<screen>_step.html" %}{% endblock %}`. Текст `<title>` страницы и фрагмента — один источник (словарь в `auth.py` или правило суиты).

### `app/templates/auth_base.html` (шелл)
Сейчас (`:33-50`): `.auth-brand` → `<p class="auth-subtitle">{% block auth_subtitle %}` → `notice_area.html` → `htmx_error_banner.html` → `{% block content %}`. Якорь `<div id="auth-step">` ставится ПОСЛЕ двух include и оборачивает `{% block content %}`; области `#notice`/`#notice-alert` в якорь не попадают. CSS якоря — flex-колонка с `gap: 14px` или `display: contents` (RESEARCH Pattern 2).

### `app/templates/base.html:74` (форма возврата)
Сейчас:
```jinja
        <form method="post" action="/impersonation/stop" class="impersonation-back">
            <button type="submit" class="btn btn--ghost">{{ mono('ВЕРНУТЬСЯ В АДМИНА', 'muted', upper=true) }}</button>
        </form>
```
Станет `{% call form_wrapper(action='/impersonation/stop') %}…{% endcall %}` без `target` (→ `hx-swap="none"`, аналог — `account_groups/list.html`); отступ `margin-left: auto` (`app.css:531`) перенести на обёртку/внутренний узел. `base.html` — только в `MACRO_DEFINITION_SITES_CALLERS`, не в `PARAMETRIC_SWAP_TARGETS`.

---

### `tests/test_pages/test_auth_transport.py` (test) — НОВЫЙ

**Аналог:** `tests/test_pages/test_max_connect_transport.py:125-175`.
```python
    over_htmx = await authed_client.post(START_URL, data={"phone": blank}, headers=HTMX_HEADERS, follow_redirects=True)
    assert over_htmx.status_code == 422, (...)
    assert EMPTY_PHONE_ERROR in over_htmx.text, "во фрагменте нет текста ошибки"
    assert DOCUMENT_MARK not in over_htmx.text, (...)
    assert f'value="{blank}"' in over_htmx.text, (...)
    assert STEP_TARGET in over_htmx.text, (...)

    without = await authed_client.post(START_URL, data={"phone": blank}, follow_redirects=False)
    assert without.status_code == 422, (...)
    assert DOCUMENT_MARK in without.text, (...)
```
Добавить на каждом пути ошибки: пароль не в теле, враждебное значение экранировано (RESEARCH §«Тройное утверждение ошибки», форма `&#34;` сверяется прогоном), `access_token` не в `set-cookie`; для шага — 200 + `<!DOCTYPE` без htmx, 200 без `<!DOCTYPE` и первым узлом `<title>` с htmx. Сообщения `assert` — по-русски с объяснением, как в аналоге.

### `tests/test_pages/test_impersonation.py`
**Аналог:** `test_impersonation_over_htmx_keeps_both_the_location_and_the_cookie` (`:208-…`) — тройная пара: заголовок, cookie, фактическая смена лица следующим запросом. Дописать для `stop_impersonation`: успех (204 `HX-Location: /admin` + cookie), нет лица (204 `HX-Location: /dashboard`), админа нет (204 `HX-Redirect: /login` + снятие cookie), чужой источник — 403.

### `tests/test_pages/test_htmx_gates.py`
- Узнавание (`:925-941`) — сейчас одно имя:
```python
        if isinstance(func, ast.Name) and func.id == RESPONSE_CALL:
            return True
        if isinstance(func, ast.Attribute) and func.attr == RESPONSE_CALL:
            return True
```
  Расширить до закрытого `RESPONSE_LAYER_EXITS = frozenset({"respond", "respond_field_error", "respond_screen", "redirect_internal"})`; `RESPONSE_CALL` (`:122`) остаётся. Контроли зубов — через `_sources_with` (`:2456`).
- `_fragment_builder_names` (`:4217-4268`) — добавить ветку для выхода шага, по образцу:
```python
        if called == RESPONSE_CALL:
            builder_arguments: tuple[str, ...] = (FRAGMENT_ARGUMENT,)
        elif called == FIELD_ERROR_CALL:
            builder_arguments = FIELD_ERROR_BUILDER_ARGUMENTS
```
  Докстринг дополнять летописью, прежнюю редакцию не стирать (идиома D-30/D-32, как у плана 11-09).
- `NOT_YET_CONVERTED` (`:265-281`) → пустой `frozenset()` с летописью; `NOT_YET_CONVERTED_COUNT = 10` (`:638`) → 0.
- `OWN_RESPONSE_EXITS` (`:4476`) — запись по форме `_OwnResponseExit(entry="app/pages/auth.py::stop_impersonation", kind="Response(status_code=403)", reason=_OWN_RESPONSE_PRICE + ". " + _OWN_RESPONSE_ORIGIN_GUARD + …, lifting_condition=LIFTING_CONDITION_OWN_RESPONSE, decision_state=…)`; `OWN_RESPONSE_EXITS_DECLARED = 13` (`:4847`) — прогоном. Состояние решения: D-08 называет свои записи поимённо (`:2987-2997`) — для D-01 Фазы 14 может понадобиться своё состояние, как `DECISION_OWNER_D15`.
- Новый гейт критерия 3: вызывающие `redirect_internal` == {`login_submit`, `register_complete`, `forgot_password_reset`, `stop_impersonation`}; `respond` без `fragment=` / `location_response` в `auth.py` — только `stop_impersonation`.
- Летописи чисел — по форме «ЧИСЛО ПОСТАВЛЕНО ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА» с дословным выводом (`:4841-4846`).

### `tests/test_pages/test_htmx_post_pairs.py`
Ветки-метки `:107-109` (`FRAGMENT`, `LOCATION`, `EXTERNAL`); добавить `SCREEN` и ветку драйвера по образцу `:1890-1912`:
```python
    assert case.transport is EXTERNAL, f"{case.name}: неизвестная ветка {case.transport!r}"
    assert with_layer.status_code == 204, (...)
    assert with_layer.headers.get("HX-Redirect") == expected, (...)
    assert "HX-Location" not in with_layer.headers, (...)
    assert with_layer.content == b"", f"{case.name}: у ответа 204 появилось тело"
```
Для внутреннего выхода ветку `EXTERNAL` можно переиспользовать (или завести `FULL_LOAD`) + утверждение cookie; нужна личность «аноним» в `_PairCase.identity`. Случай — по форме `:1434-1444`. `POST_PAIR_CASES_DECLARED = 58` (`:1803`) и `PAIRED_302_ASSERTIONS_DECLARED` — прогоном; замыкание `:1935` использует `handler.calls_respond` — перевести на расширенное узнавание.

### `tests/test_pages/test_hx_location_destinations.py`
В `HX_LOCATION_DESTINATION_TEMPLATES` (`:502-517`) добавить `"/admin": "admin/overview.html"`; `HX_LOCATION_DESTINATION_CALLS_DECLARED = 77` (`:476`) → прогоном (ожидание 79). Если выход полной перезагрузки — отдельная функция, обход его не считает.

### `tests/test_templates/test_htmx_markup_gates.py`
- `MACRO_DEFINITION_SITES_CALLERS["components/form_wrapper.html"].callers` (`:1414-…`) — добавить включения экранов и `base.html` с комментарием «Фаза 14, план 14-NN: …» по образцу записи `max_connect_step.html` (`:1424-1429`); `…_CALLERS_DECLARED = 24` (`:1649`) прогоном.
- `PARAMETRIC_SWAP_TARGETS` (`:2682-…`) — экраны с `target='#auth-step'`; `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED = 9` (`:1774`) прогоном.
- `LONG_LIVED_REGION_IDS` (`:2511`) — `+ "auth-step"`.

## Shared Patterns

### Единственное чтение признака htmx
**Источник:** `app/pages/htmx.py:166` `is_htmx`. **Применять:** везде; `request.headers.get("HX-Request")` в обработчиках запрещено (`HX_HEADER_READS = 1`).

### Cookie сессии
**Источник:** `set_session_cookie` / `clear_session_cookie` (`auth.py:68-107`), порядок — `admin.py:1870-1884`. **Применять:** `login_submit`, `register_complete`, `stop_impersonation`. Сначала ответ слоя, потом cookie на тот же объект; `delete_cookie`/`set_cookie` напрямую — нельзя.

### Адрес и код исхода в заголовке
**Источник:** `_local_path` (`htmx.py:207-248`), `_with_notice`, `_require_registered_notice`; код — `notices.PASSWORD_RESET_DONE` (`app/pages/notices.py:137`). Кириллицы в `HX-*` нет.

### Форма через макрос
**Источник:** `components/form_wrapper.html:187-199`. `hx-post` только из макроса (D-03 Фазы 9); `method`/`action` печатает макрос — путь без JS сохраняется.

### Одна разметка на страницу и фрагмент
**Источник:** `accounts/includes/max_connect_step.html` + `accounts.py:802-825`. Рендер фрагмента — `templates.env.get_template(...).render(...)`, автоэкранирование, без `|safe`/`Markup(`.

### Инвентарь числом
Все объявленные числа гейтов ставит прогон покрасневшего правила; летопись с дословным выводом, прежние редакции не стираются (D-13 Фазы 8, D-30/D-32).

## No Analog Found

| Файл | Роль | Поток | Причина |
|---|---|---|---|
| `app/templates/auth/includes/step_response.html` | component | transform | Ни один фрагмент проекта не несёт `<title>` верхним узлом; опираться на RESEARCH Находка 4 / Pattern 4 (`<title>` — прямой потомок ответа, иначе вкладка не сменится) |

Частично новое: выход `respond_screen` (200 на обоих транспортах) — в слое такого кода нет, форма берётся у `respond_field_error`; ветка пар `SCREEN` — нет прецедента «200 + `<!DOCTYPE`» без htmx в драйвере.

## Metadata

**Analog search scope:** `app/pages/`, `app/templates/{auth,accounts/includes,components}/`, `app/templates/{auth_base,base}.html`, `tests/test_pages/`, `tests/test_templates/`
**Files scanned:** ~20
**Pattern extraction date:** 2026-09-22
