# Phase 11: Массовый перевод разделов письма — Pattern Map

**Mapped:** 2026-09-14
**Files analyzed:** 27 (1 слой ответа, 1 помощник границы id, 7 модулей обработчиков/реестров, 10 шаблонов, 7 файлов гейтов/тестов, 1 новый модуль пар)
**Analogs found:** 26 / 27 (без аналога — только тест «нет 422 умолчания на htmx-пути»; ближайший частичный назван)

Все выдержки ниже сняты с рабочего дерева 2026-09-14. Каждый путь проверен `git ls-files`
(tracked). Номера строк — текущие. Там, где дерево разошлось с CONTEXT/докстрингами, это
отмечено ⚠️ ДРЕЙФ.

---

## File Classification

| Файл (правится / заводится) | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `app/pages/htmx.py` — третий выход `HX-Redirect` (D-09) | utility (слой ответа) | request-response, внешний переход | `app/pages/htmx.py::location_response` (`:154-170`) + `_local_path` (`:110-151`) | exact |
| `app/pages/identifiers.py` — неограниченные POST-алиасы + помощник границы (D-07, T-07-13) | utility | validation | `app/pages/identifiers.py:97-103` (`IdPath`/`IdForm`/`OptionalIdForm`) | self |
| `app/pages/schedules.py::schedules_create` (`:901`) | route handler | fragment `beforeend` + OOB; «было ноль» → `HX-Location` | `app/pages/account_groups.py::account_groups_toggle` (`:561-599`) | role-match |
| `app/pages/schedules.py::schedules_update` (`:995`) | route handler | fragment `outerHTML` | `app/pages/schedules.py::schedules_delete` фрагмент (`:1411-1437`) | exact |
| `app/pages/schedules.py::schedules_toggle` (`:1078`) | route handler | fragment по источнику (скрытое поле) | `account_groups_toggle` (`:431-599`) + `returns_to_editor` (`schedules.py:1242`) | exact |
| `app/pages/schedules.py::schedules_partial` (`:762-806`) | route handler (GET) | keyset-курсор | `app/pages/account_groups.py::account_groups_partial` (`:285-380`) | exact |
| `app/pages/ads.py::ads_create`/`ads_update` (через `_save_from_editor`, `:543-549`) | route handler | fragment (OOB-only) + `HX-Push-Url` | сам себе + `respond(fragment=…)` | self |
| `app/pages/admin.py::admin_toggle_free_access` (`:1597`), `admin_toggle_block` (`:1812`) | route handler | fragment `[data-actions]` + OOB | `account_groups_toggle` | role-match |
| `app/pages/admin.py::admin_drop_task` `?result=` (`:1145,1160,1173`) | route handler | request-response → `?notice=` | `respond(redirect=…, notice=…)` в `app/pages/htmx.py:394` | exact |
| `app/pages/notices.py` — коды из `QUEUE_DROP_RESULTS` (D-10) | config (реестр) | — | `app/pages/notices.py:95-113` + `NOTICES` (`:134-150`) | self |
| `app/pages/accounts.py::accounts_retry_sync` (`:714`), `accounts_sync_groups` (`:786`) | route handler | request-response → `HX-Location` | `respond(request, redirect=…)` (`account_groups.py:337,341,510`) | exact |
| `app/pages/accounts.py::accounts_connect_max_start` (`:542`) | route handler | fragment шага + 422 эхо | `account_groups_toggle` + `profile.py:79-90` (форма ошибки) | role-match |
| `app/pages/profile.py::profile_post` (`:38`) | route handler | fragment + notice OOB; 422 эхо | `respond(fragment=…, notice=…)` → `_glue_notice` (`htmx.py:285-354`) | role-match (первое поведение ветки) |
| `app/pages/billing.py::subscribe_to_plan` (`:269-352`) | route handler | внешний переход | `billing.py:337-352` (сегодняшние ветки) → третий выход | role-match |
| `app/templates/includes/htmx_config.html:129` | config | — | сам себе; зеркало `tests/test_pages/test_shell.py:1300` | self |
| `app/templates/ads/form.html` (`:219` `#sched-count`, `:223` `data-sched-list`) | template (контейнер + счётчик) | fragment target / OOB | `#sched-count` там же (Фаза 10) | exact |
| `app/templates/ads/includes/sched_card.html` (`:112`, тумблер `:122`, `:132`) | template (карточка) | fragment target | `account_groups/includes/group_row.html` (тумблер Фазы 9, `:95-214`) | exact |
| `app/templates/schedules/includes/schedule_row.html` (`:64`, `:81`) | template (строка) | fragment target | то же | exact |
| `app/templates/schedules/list.html:61` + `partial_cards.html:7` (сентинел) | template | keyset | `account_groups/list.html` + `account_groups/partial_cards.html` (сентинел `after_id`) | exact |
| `app/templates/<раздел>/partials/*_response.html` (новые: создание расписания, действия админа) | template (ответ с OOB) | fragment / OOB | `account_groups/partials/delete_response.html` (`:99-101`), `ads/includes/autosave_response.html` | exact |
| `app/templates/admin/user_detail.html:133` (`data-actions` → `id`) | template | fragment target | `#sched-count` / `group-row-N` | role-match |
| `app/templates/admin/queue.html:34-35` (снять `drop_result`) | template | — | шелл-область уведомлений (D-12 Фазы 8) | self |
| `app/templates/accounts/connect_max.html`, `profile.html:33` | template (форма) | fragment + 422 | `sched_card.html` форма правки | role-match |
| `tests/test_pages/test_htmx_gates.py` (числа, `SAFE_BY_NAME`, `OWN_RESPONSE_EXITS`, `VALIDATION_REFUSAL_DIVERGENCES`, новые гейты `HX-Retarget`/`?result=`) | test (gate) | — | сам себе (`:163,344,1399,1585,2429,2981,3804,3986`) | self |
| `tests/test_templates/test_htmx_markup_gates.py` (пересчёт констант, перечень D-16) | test (gate) | — | `DISABLED_ELT_EXCEPTIONS` (`:2760-2870`, счёт `:3198-3207`) | exact |
| `tests/test_pages/test_htmx_response_contract.py` (`:72`, `:194-250`) + `tests/test_pages/test_shell.py:1300` | test (gate) | — | сам себе | self |
| `tests/test_pages/test_<пары>.py` — новый модуль GATE-02 | test (parametrized) | обход пар | `tests/test_pages/test_confirm_delete_transport.py` (`:1223-1320`) | exact |
| тест «на htmx-пути страничных POST нет 422 умолчания» (T-07-13) | test | — | частично: `_status_code_literals` в `test_htmx_response_contract.py:~80`; обход — форма `test_confirm_delete_transport.py` | **partial** (см. No Analog) |

---

## Pattern Assignments

### 1. `app/pages/htmx.py` — третий выход (D-09, FORM-05)

**Аналог:** `location_response` + `_local_path`, тот же модуль.

**Сборка ответа перехода** (`:154-170`) — копировать форму 1:1, заменив заголовок и проверку:
```python
def location_response(location: str) -> Response:
    """ЕДИНСТВЕННАЯ сборка ответа, приказывающего браузеру уйти по адресу.
    ⚠️ СТАТУС 204, А НЕ 200 ... правило `{"code":"204","swap":false}` ...
    Статус разбору заголовка не мешает: слой письма читает заголовок перехода
    ДО применения правил обработки ответа (проверено по вендоренному 2.0.10).
    """
    return Response(
        status_code=204, headers={HX_LOCATION_HEADER: _local_path(location)}
    )
```

**Рантайм-проверка значения заголовка** (`:130-151`) — классы отказа переиспользовать (управляющие, не-ASCII); текст ошибки НЕ подставляет значение (докстринг `:126-128`):
```python
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ValueError("адрес перехода содержит управляющий символ — ...")
    if not value.isascii():
        raise ValueError("адрес перехода содержит символ вне ASCII — ...")
    return value
```

**Ветвление транспорта** (`respond`, `:468-475`) — третий выход повторяет порядок: сначала `is_htmx`, путь без JS — прежний 302:
```python
    if not is_htmx(request):
        return RedirectResponse(url=_with_notice(redirect, notice), status_code=302)
    if fragment is None:
        return location_response(_with_notice(redirect, notice))
```

**Отложенные импорты** (`:221`, `:259-260`) — если нужен логгер/`notices`, импортировать ВНУТРИ функции (Assumption A6).

**Докстринг-ловушка, которую фаза закрывает** (`:418-425`): «ветку эту вводит Фаза 11» — переписать абзац по идиоме «прежняя редакция опровергнута, а не стёрта» (`:440-447`).

Иллюстрация сигнатуры и множества хостов: RESEARCH §Code Examples «Третий выход» (`frozenset({"yoomoney.ru"})`, `urlsplit(...).hostname`, провал → `respond(redirect="/billing", notice=PAYMENT_FAILED)`).

---

### 2. `app/pages/identifiers.py` (D-07, закрытие стока T-07-13)

**Сегодняшние алиасы** (`:97-103`) — **не менять** (`IdPath` 33 потребителя, включая GET; Open Question 4). Рядом завести POST-алиасы без `ge/le` и один помощник:
```python
IdPath = Annotated[int, Path(ge=1, le=ID_MAX)]
IdForm = Annotated[int, Form(ge=1, le=ID_MAX)]
OptionalIdForm = Annotated[int | None, Form(ge=1, le=ID_MAX)]
```
Комментарий над ними (`:90-96`) объясняет ПОЧЕМУ граница на входе — новый помощник обязан сохранить свойство «до первого обращения к базе, включая `is_same_origin`/`_ownership_verdict`» (Landmine CONTEXT). Значение вне диапазона (и нечисловое, если выбран вариант 1 RESEARCH) → та же ветка «нет/чужое» обработчика.

---

### 3. `app/pages/schedules.py::schedules_update` / `schedules_toggle` / `schedules_create` (FORM-03, FORM-07)

**Аналог фрагмента:** `schedules_delete`, тот же модуль (`:1411-1437`). ⚠️ ДРЕЙФ: докстринги `htmx.py:319-320,432-433` называют `schedules.py:1240`; фактический вызов — `:1437`. Замер «ТРИ сборщика» в `_glue_notice`/`respond` фаза обязана обновить (станет 12).
```python
        schedules_count = await _ad_schedule_count(db, user.id, ad_id)
        return HTMLResponse(
            templates.env.get_template(
                "ads/partials/sched_delete_response.html"
            ).render(
                schedule_id=schedule_id,
                schedules_count=schedules_count,
                ad=await _ad_row(db, user.id, ad_id),
                user=user,
                editor={...},
            )
        )

    # `notice` НЕ передаётся (D-03): ...
    return await respond(request, redirect=screen_url, fragment=_fragment)
```

**Источник формы через скрытое поле, читается ОДИН раз** (`:1242`) — образец для «какой экран прислал тумблер»:
```python
    returns_to_editor = form_data.get("return_to") == RETURN_TO_EDITOR
```

**Нульарный async-сборщик** (`account_groups.py:561-599`) — докстринг объясняет, почему не `lambda` и почему отложенность несущая:
```python
    async def _fragment() -> HTMLResponse:
        """⚠️ ФУНКЦИЯ НУЛЬАРНАЯ И АСИНХРОННАЯ: слой ответа делает `await
        fragment()` ... на пути без htmx разметка не собирается вовсе"""
        schedules_count = (await _schedule_counts(db, user.id, [group.id])).get(group.id, 0)
        active_groups, total_groups = await _group_counts(db, user.id, account_id)
        html = templates.env.get_template(
            "account_groups/partials/toggle_response.html"
        ).render(group=group, account_id=account_id, ..., filter_search=term or "")
        return HTMLResponse(html)

    return await respond(request, redirect=screen_url, fragment=_fragment)
```

**Ветки «нет/чужое/исход» → `HX-Location`** (`account_groups.py:510`): `return await respond(request, redirect=screen_url)`; с кодом — `respond(redirect=<редактор>, notice=notices.SCHEDULE_ACCOUNT_GONE)` (коды `notices.py:106-113`).

**Отказ по источнику** (`schedules.py:1190-1191`) — стоит ВЫШЕ выборки, не трогать:
```python
    if not is_same_origin(request):
        return Response(status_code=403)
```

**`schedules_create` «было ноль»:** контейнера `data-sched-list` нет (`ads/form.html:223` против `empty_state`) → `respond(request, redirect=f"/ads/{ad_id}/edit?sched={N}#sched-{N}")`; `_with_notice` уже корректно режет якорь (`htmx.py:386-391`).

---

### 4. `app/pages/schedules.py::schedules_partial` — keyset (D-11)

**Аналог:** `app/pages/account_groups.py:297` и `:345-373`.
```python
    after_id: int | None = Query(None, ge=1, le=ID_MAX),
    ...
    # КЛЮЧЕВОЙ КУРСОР ВМЕСТО СМЕЩЕНИЯ (план 09-13, решение владельца `keyset`).
    # ⚠️ ПОДДЕЛАННЫЙ КЛЮЧ СУЖАЕТ ВЫБОРКУ, НО НЕ ОТМЕНЯЕТ ТРОЙНОГО `WHERE` (T-09-13-01)
    query = _build_groups_query(user.id, account_id, term)
    if after_id is not None:
        query = query.where(Group.id > after_id)
    result = await db.execute(query.limit(limit + 1))
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    groups = rows[:limit]
    ... "next_after_id": groups[-1].id if groups else None,
```
**Заменяет сегодняшнее** (`schedules.py:765,788,803`): `offset: int = Query(0, ge=0)`, `.order_by(Schedule.id).offset(offset).limit(limit + 1)`, `"next_offset": offset + limit`. Внимание: `rows` здесь — кортежи (`r.Schedule`), ключ — `page[-1].Schedule.id`. `Query(ge=, le=)` на GET — вне D-07 (только POST), но проверить против `VALIDATION_REFUSAL_DIVERGENCES`.

**Сентинел** (`schedules/partial_cards.html:7`, байт-в-байт с `list.html:61`):
```jinja
<div hx-get="/schedules/partial?offset={{ next_offset }}&limit=30{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
```
`offset=` → `after_id=`, синхронно в двух файлах (гейт идентичности, Pitfall 10).

---

### 5. `app/pages/ads.py::_save_from_editor` (D-13)

**Сегодня** (`:543-549`) — ветка htmx собирается вручную, мимо `respond`:
```python
    if htmx:
        response = await _autosave_response(request, db, settings, user, ad)
        if created:
            response.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"
        return response
```
Переезд: `_fragment` возвращает этот же `response` (заголовок ставится ВНУТРИ сборщика; при `notice=None` `respond` отдаёт ответ как есть, `htmx.py:482-484`). Запись `HX-Push-Url` остаётся одним из `HX_HEADER_WRITES`. Запись заголовка — `ads.py:548`, совпадает с CONTEXT. Путь без JS (`:555-556`) не трогается. `htmx` здесь — локальный признак; второе чтение заголовка роняет `HX_HEADER_READS = 1` (RESEARCH Don't Hand-Roll).

---

### 6. `app/pages/admin.py` — тумблеры (`:1597`, `:1812`) и `?result=` (`:1145,1160,1173`)

**Тумблеры:** аналог — `account_groups_toggle` (§3). Отказ по источнику — `admin.py:1116-1117` (форма комментария «Чужому источнику причина отказа не сообщается»), в `OWN_RESPONSE_EXITS` (§11).

**`?result=` сегодня:**
```python
        return await respond(request, redirect=f"{location}?result=unknown_account")
    ...
        return await respond(request, redirect=f"{location}?result={outcome}")
    ...
    return await respond(request, redirect=f"{location}?result={DROP_REMOVED}")
```
Цель: `respond(request, redirect=location, notice=notices.QUEUE_DROP_…)` — сборка адреса с кодом только через `_with_notice` (Don't Hand-Roll). Источник текстов — `QUEUE_DROP_RESULTS` (`admin.py:308-320`), переносить ДОСЛОВНО вместе с вариантом (`success`/`warning`/`error`). Снять чтение `:1065` и `admin/queue.html:34-35`. Тесты, читающие `result=`: `test_hx_location_destinations.py`, `test_account_groups.py`, `test_confirm_delete_transport.py`.

### 7. `app/pages/notices.py` (D-10)

**Форма константы + комментарий-основание** (`:95-113`):
```python
# Отказ перезапустить воркер в админке. Кнопку жмут в аварии, ...
WORKER_NO_CONTAINER = "worker_no_container"
WORKER_RESTART_FAILED = "worker_restart_failed"
```
**Форма записи реестра** (`:134-147`):
```python
NOTICES: tuple[Notice, ...] = (
    # -- повтор отправки --
    Notice(
        RETRY_QUEUED,
        "Повтор поставлен в очередь. ...",
        "success",
    ),
```

---

### 8. `app/pages/accounts.py::accounts_retry_sync` / `accounts_sync_groups` (FORM-04)

**Аналог:** `respond(request, redirect=...)` без фрагмента (`account_groups.py:337,341,510`):
```python
        return await respond(request, redirect="/accounts")
```
⚠️ `accounts_sync_groups`: `return await respond(...)` ставится ВНУТРИ `try`, освобождение `_SYNC_IN_FLIGHT` в `finally` сохраняется (Pitfall 8).

### 9. `app/pages/accounts.py::accounts_connect_max_start` и `app/pages/profile.py::profile_post` (FORM-08)

**Сегодняшняя ветка ошибки поля** (`profile.py:79-90`) — источник эхо и текста (переносится дословно), статус `400 → 422`, тело — фрагмент формы, а не полная страница:
```python
    return templates.TemplateResponse(
        "profile.html",
        {..., "timezone_choices": TIMEZONE_CHOICES, "error": "Неверный часовой пояс"},
        status_code=400,
    )
```
**Успех профиля** (`:77`) → `respond(request, redirect="/profile", notice=notices.PROFILE_SAVED, fragment=_fragment)`; приклейка — `_glue_notice` (`htmx.py:328-354`: статус с телом, `text/html`, свежий `HTMLResponse` без `BackgroundTask`). Это ПЕРВЫЙ фрагмент с `notice` — обновить докстринг `respond` (`:426-438`, «не пользуется НИ ОДИН обработчик») по идиоме поколений.

⚠️ `timezone: str = Form(...)` (`profile.py:40`) — источник 422 умолчания FastAPI; по варианту 1 RESEARCH → `Form("")` с проверкой внутри.

---

### 10. `app/pages/billing.py::subscribe_to_plan` (FORM-05)

**Сегодня** (`:337-352`):
```python
    except PendingIntentCapError:
        return RedirectResponse(url=f"/billing?notice={notices.PAYMENT_PENDING}", status_code=302)
    except PaymentCreationError:
        return RedirectResponse(url=f"/billing?notice={notices.PAYMENT_FAILED}", status_code=302)
    return RedirectResponse(url=result["confirmation_url"], status_code=302)
```
Цель: ветки отказа → `respond(request, redirect="/billing", notice=…)`; последняя строка → третий выход (§1). Комментарии веток (почему отдельная ветка PENDING) сохраняются. Попутно — комментарий `:93-95` (D-10).

---

### 11. `tests/test_pages/test_htmx_gates.py` — реестры и числа

**`SAFE_BY_NAME`** (`:1585-1592`) — вторая запись по той же форме (основание = рантайм-проверка + её тесты + асимметрия пути 302, Open Question 2):
```python
SAFE_BY_NAME: dict[str, str] = {
    "app/pages/htmx.py::location_response": (
        "значение приходит ПАРАМЕТРОМ, и безопасность его доказывается не "
        "разбором дерева, а рантайм-проверкой локального пути того же модуля "
        "(`_local_path`): ... у неё есть собственные тесты (план 08-01). ..."
    ),
}
```

**`OWN_RESPONSE_EXITS`** (`:3804`, запись `:3805-3824`) — три новые записи (D-08) с общим префиксом `_OWN_RESPONSE_PRICE + ". " + _OWN_RESPONSE_ORIGIN_GUARD` и своим хвостом; `decision_state` — НЕ `DECISION_WAITS_FOR_THE_OWNER`, а решённое со ссылкой «решение владельца 2026-09-14, `11-CONTEXT.md` D-08» (CONTEXT §specifics; сверить имя константы решённого состояния в модуле):
```python
    _OwnResponseExit(
        entry="app/pages/account_groups.py::account_groups_delete",
        kind="Response(status_code=403)",
        reason=(_OWN_RESPONSE_PRICE + ". " + _OWN_RESPONSE_ORIGIN_GUARD + ". ⚠️ СВОЁ У ЭТОГО ВХОДА: ..."),
        lifting_condition=LIFTING_CONDITION_OWN_RESPONSE,
        decision_state=DECISION_WAITS_FOR_THE_OWNER,
    ),
```
Полнота сверяется замером (`_own_response_completeness_complaints`, `:3989-4010`) — число `OWN_RESPONSE_EXITS_DECLARED = 9` (`:3986`) → 12.

**`VALIDATION_REFUSAL_DIVERGENCES`** (`:2429`, запись `_ValidationRefusalDivergence(entry=…, alias=…, reason=…, lifting_condition=LIFTING_CONDITION_VALIDATION_REFUSAL, …)`) — 23 → 0; тест числа `:3288`, тест обоснования `:3336` (на пустом кортеже — проверить, что не зеленеет вакуумом; память проекта «RED-гейт зеленеет вакуумом»). `LIFTING_CONDITION_VALIDATION_REFUSAL` (`:2409-2415`) называет Фазу 11 — летопись снятия.

**Числа:** `HX_HEADER_WRITES = 2` (`:163`) → 3; `NOT_YET_CONVERTED` (`:201-230`) минус 12 ключей, `NOT_YET_CONVERTED_COUNT = 26` (`:344`) → 14 (летопись словами, не ключами); `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 3` (`:1399`) → 12.

### 12. `tests/test_templates/test_htmx_markup_gates.py` — перечень `HX-Retarget`/`HX-Reswap` (D-16, FORM-10)

**Аналог формы перечня** — `DISABLED_ELT_EXCEPTIONS` (`:2760`), dataclass с `callers`/`reason` (`:2790-2794`), число `DISABLED_ELT_EXCEPTIONS_DECLARED = 2` (`:2870`), правило числа (`:3198-3207`):
```python
    assert len(DISABLED_ELT_EXCEPTIONS) == DISABLED_ELT_EXCEPTIONS_DECLARED, (
        f"исключений цели блокировки в перечне {len(DISABLED_ELT_EXCEPTIONS)}, "
        f"объявлено {DISABLED_ELT_EXCEPTIONS_DECLARED}: "
        f"{sorted(DISABLED_ELT_EXCEPTIONS)} — из-под общего правила выведено ..."
    )
```
Новый гейт: вхождений `HX-Retarget`/`HX-Reswap` в `app/` == записям (ожидаемо 0; сегодня grep пуст). Пересчёт: `HX_POST_PLACES = 3` (`:140`), `FRAGMENT_ROUTES_DECLARED = 11` (`:895`), `HX_TARGETS = 1` (`:1831`), `OOB_BLOCKS = 13` (`:1932`), `CLIENT_STATE_NODES = 24` (`:1952`).

### 13. Правило 422 (Находка B) — `htmx_config.html:129`, `test_htmx_response_contract.py`, `test_shell.py:1300`

Одним планом/коммитом (указание самого литерала `test_htmx_response_contract.py:62-72`):
- `app/templates/includes/htmx_config.html:129`: `{"code":"422", "swap": false, "error": true},` → `"swap": true`.
- `tests/test_pages/test_shell.py:1300`: `{"code": "422", "swap": False, "error": True},` → `True` (порядок `RESPONSE_HANDLING_CODES` не трогать).
- `tests/test_pages/test_htmx_response_contract.py:72` `SERVER_SIDE_VALIDATION_RESPONSES = 0` → число мест, снятое гейтом `:169`.
- `:245` `assert validation.get("swap") is False` переворачивается; докстринг `:194-230` уже предписывает «вернуть ПРАВОМЕРНО только одновременно с первым маршрутом, отдающим 422 с авторским фрагментом» — дописать поколение, не стирать.
- `07-SECURITY.md:114` T-07-13 переоткрывается в `11-SECURITY`.

### 14. Новый модуль пар GATE-02 — `tests/test_pages/test_<…>_pairs.py`

**Аналог:** `tests/test_pages/test_confirm_delete_transport.py`.
- Реестр маршрутов + число: `test_the_number_of_confirmed_delete_routes_is_the_declared_one` (`:1223`) — `len(CONFIRMED_DELETE_ROUTES) == CONFIRMED_DELETE_ROUTES_DECLARED` + уникальность ключей.
- Вторая ось (случаи) с антивакуумной половиной: `:1246` — пустой список исходов краснеет; `len(_outcome_cases()) == …_DECLARED`; «Поставьте число ПРОГОНОМ этого отказа, а не сложением в уме».
- Обход: `@pytest.mark.parametrize("case", _outcome_cases(), ids=_case_id)` + `@pytest.mark.asyncio` (`:1287-1289`), состояние готовится заново для каждой половины:
```python
    route, outcome = case
    await _identify(client, route.identity, test_settings)
    degraded = await outcome.arrange(client, db_session, test_settings, route.identity)
    expected = outcome.expected_landing(degraded)
    with degraded.context():
        without = await client.post(degraded.url, data=degraded.data, follow_redirects=False)
    assert without.status_code == 302, (...)
    assert without.headers["location"] == expected, (...)
```
Вторая половина — по классу: фрагмент → 200 и `"<!DOCTYPE" not in r.text`; навигация → 204 + `HX-Location`, `r.content == b""`; оплата → 204 + `r.headers["HX-Redirect"] == CONFIRMATION_URL` и `"HX-Location" not in r.headers` (Pitfall 2). Клиент с признаком — фикстура `htmx_client` (`tests/conftest.py:70`). Добавить AST-обход утверждений `302` против `POST_HANDLERS − NOT_YET_CONVERTED` и замыкание «≥1 случай на переведённый обработчик». Фикстура хоста — документированный `https://yoomoney.ru/...`, не `yookassa.ru` (`test_billing_subscription.py:38`).

---

### 15. Шаблоны фрагментов с OOB

**Плоское тело, узлы — прямые дети файла** (`account_groups/partials/delete_response.html:62-65,99-101`; `allowNestedOobSwaps: false`):
```jinja
<div id="group-row-{{ group_id }}" hx-swap-oob="delete"></div>
<div id="group-del-{{ group_id }}" hx-swap-oob="delete"></div>
{% include "account_groups/partials/count_rule_oob.html" %}
```
Узел линейки ВКЛЮЧАЕТСЯ, а не копируется (`:67-70`) — для создания расписания включать ту же линейку `#sched-count`, что и `ads/partials/sched_delete_response.html`.

**OOB-only ответ с `hx-swap="none"`** (`ads/includes/autosave_response.html:19-21,34`) — для `ads_*` без изменений:
```jinja
<div id="ad-preview" hx-swap-oob="true">{% include "ads/includes/preview.html" %}</div>
<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>
{% set oob = true %}{% include "ads/includes/autosave.html" %}
```

**Тумблер под htmx** (`account_groups/includes/group_row.html:95-214`): `x-on:change="$el.submit()"` снят, отправку берёт `hx-trigger="change"`, `hx-sync="this:drop"`; голый `x-data` переехал на `<span x-data x-init="if (window.htmx) $el.remove()">` с кнопкой «Применить» (`:214`). Панель удаления — снаружи цели (`:234-235`, `x-on:submit.prevent="$dispatch('modal-open-…')"`). Применить к `sched_card.html:122` и `schedule_row.html:81`.

---

## Shared Patterns

### Единственный выход обработчика
**Source:** `app/pages/htmx.py:394-485` (`respond`)
**Apply to:** все 12 обработчиков. `redirect=` ключевой и обязательный; `fragment=` — нульарный `async def _fragment() -> HTMLResponse`; `notice=` — только код из `notices.py`. Никаких `request.headers.get("HX-Request")` в обработчике.

### Отказ по источнику
**Source:** `app/pages/schedules.py:1190-1191`, `app/pages/admin.py:1116-1117`
**Apply to:** `admin_toggle_*`, `subscribe_to_plan` (как есть) + запись в `OWN_RESPONSE_EXITS`.

### Реестр с обоснованием и числом
**Source:** `DISABLED_ELT_EXCEPTIONS` (`test_htmx_markup_gates.py:2760-2870,3198`), `OWN_RESPONSE_EXITS` (`test_htmx_gates.py:3804-3986`)
**Apply to:** перечень D-16, расширение D-08, пары GATE-02, гейт `?result=` == 0.

### Комментарии-обоснования
Стиль всего слоя: `⚠️` + ПРОПИСНОЙ тезис + почему; опровергнутые редакции называются, а не стираются (`htmx.py:440-447`, `delete_response.html:83-96`). Замеры в докстрингах (`htmx.py:319-320,432-433` — «ТРИ сборщика») фаза обязана перемерить.

### Постоянная обёртка + `innerHTML`
**Source:** `ads/form.html:219` `<div id="sched-count">`
**Apply to:** `data-sched-list` (новый `id`), `admin/user_detail.html:133` `data-actions`, контейнер шага MAX, обёртка формы профиля.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| тест «на htmx-пути страничных POST нет 422 умолчания FastAPI» (T-07-13, после `swap:true`) | test (parametrized) | request-response | Такого теста в дереве нет: до фазы 422 на htmx-пути гасился правилом. Ближайшее: AST-счёт мест `_status_code_literals` (`test_htmx_response_contract.py:~80`, считает и `exception_handler(RequestValidationError)`) + форма обхода `test_confirm_delete_transport.py:1287`. Случаи — нечисловой id пути, пропущенное обязательное поле, id вне диапазона на POST-маршрутах фазы; утверждение: `status_code != 422` или тело — авторский фрагмент. Обработчика `RequestValidationError` в `app/main.py:219-248` нет. |

## Metadata

**Analog search scope:** `app/pages/`, `app/templates/{account_groups,ads,schedules,admin,includes}/`, `tests/test_pages/`, `tests/test_templates/`, `tests/conftest.py`, `.planning/phases/10-*/10-PATTERNS.md` (форма документа)
**Files scanned:** ~20
**Дрейф, найденный этой сессией:** фрагментный вызов `schedules_delete` — `schedules.py:1437` (докстринги `htmx.py` говорят `:1240`). Прочие номера строк CONTEXT/RESEARCH совпали с деревом.
**Pattern extraction date:** 2026-09-14
