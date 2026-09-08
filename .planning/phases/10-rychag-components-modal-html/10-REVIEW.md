---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-08T21:40:00Z
depth: standard
files_reviewed: 42
files_reviewed_list:
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/identifiers.py
  - app/pages/schedules.py
  - app/templates/account_groups/includes/group_row.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/sched_count_rule.html
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/history/includes/history_card.html
  - app/templates/includes/notice_area.html
  - tests/conftest.py
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_origin_guard_on_destructive_routes.py
  - tests/test_planning/__init__.py
  - tests/test_planning/test_planning_gates_are_independent_of_the_live_verdict.py
  - tests/test_planning/test_requirement_completion_follows_verification.py
  - tests/test_planning/test_state_progress_matches_roadmap.py
  - tests/test_planning/test_the_walkthrough_cannot_self_certify.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_walkthrough_anchors.py
findings:
  critical: 1
  warning: 6
  info: 4
  total: 11
status: issues_found
---

# Фаза 10: отчёт ревизии кода (ШЕСТОЙ круг)

**Дата:** 2026-09-08
**Глубина:** standard
**Файлов просмотрено:** 42 (9 модулей страничного слоя, 12 шаблонов, 21 модуль суиты)
**Статус:** issues_found

## Summary

Заявленные предметы партии закрыты и перепроверены ЗАМЕРОМ, а не прочтением:

* `app/pages/identifiers.py` — величина границы объявлена во всём `app/` ровно
  один раз (`ast`-обход дерева подтверждает: единственное присваивание
  `2147483647` стои́т в этом файле);
* 36 POST-обработчиков страничного слоя, гард происхождения зовут ровно 13 —
  число, записанное в докстринге `is_same_origin`, сошлось с деревом; все шесть
  изменяющих маршрутов админки гард несут;
* «два отсутствия сложились в совпадение» в `is_same_origin` закрыто явной
  проверкой `origin_host is not None` — второго экземпляра этого класса в
  изменённом коде не нашлось (проверены `check_is_admin`, `email_is_admin`,
  `actor_of`, `_ownership_verdict`, тройной `WHERE` экрана групп,
  `retry_availability`, `_thumb_image_url`);
* приклейка внеполосного блока к ответу без тела закрыта третьим инвариантом
  (`_STATUSES_WITHOUT_BODY`), и правило проверяет ОБЕ стороны;
* все 18 мест подтверждения приземляются на маршруты, ПЕРЕВЕДЁННЫЕ на слой
  ответа, — ни одна панель с безусловным `hx-post` не бьёт в необращённый
  обработчик, отвечающий `302` (проверено перечислением всех вызовов `modal(`);
  `admin_toggle_block` и `admin_toggle_free_access` панелей не имеют, и их
  обычные формы остаются формами;
* скрипты слоя письма и клиентского состояния стоят в `<head>`, поэтому своп
  тела по `HX-Location` их не переисполняет; единственный инлайн-скрипт с
  объявлениями верхнего уровня на экране-цели обёрнут (`ads/form.html`), а
  единственный необёрнутый (`accounts/connect_tg_user.html`) целью перехода не
  является и изъят ИМЕНОВАННО;
* прогон трёх партий правил (`tests/test_planning`, `tests/test_templates`,
  `test_htmx_gates`, `test_identifier_bounds`, `test_hx_location_destinations`,
  `test_origin_guard_on_destructive_routes`, `test_confirm_delete_transport`,
  `test_editor_schedules`, `test_impersonation`, `test_notices_channel`,
  `test_history_retry`, `test_htmx_response_layer`) — **603 зелёных**;
* ссылок на несуществующие имена правил в изменённых файлах НЕТ (сверено
  автоматически: каждое `test_*`-имя из `app/**` разрешается в живую функцию
  суиты либо в существующий модуль).

Поэтому ревизия шла по двум осям, где партия могла ослабнуть: (1) чего фаза
НЕ ограничила за пределами объявленной вселенной гейта и (2) где ЗАПИСЬ этой же
партии расходится с деревом. Обе оси дали находки.

Головная находка — `CR-01` — не о фазе: это авторизационный провал мастера
подключения Telegram, живущий в `app/pages/accounts.py` и попавший в обзор
вместе с файлом. Он не создан этой фазой и её критериями не покрыт, но правило
ревизии «не подтверждать, что работа сделана» требует его назвать: сеанс QR-входа
не привязан к пользователю НИ В ОДНОМ месте, а его идентификатор ездит строкой
запроса.

Записанные закрытия НЕ переоткрываются: мёртвый первый дизъюнкт условия закрытия
панели (замер плана 10-27), `500` на шести маршрутах через `parse_account_id` и
`int(ad_id)` (`CATALOGUE_APPENDIX`, вердикт `open`), флаг `sched`, цена
внеполосных узлов на холостом пути, названная граница гарда «без обоих
заголовков» — всё это прочитано, сверено и оставлено как есть.

---

## Critical Issues

### CR-01: сеанс QR-входа Telegram не привязан к пользователю, а его идентификатор ездит строкой запроса

**Файлы:**
- `app/pages/accounts.py:253-264` (`accounts_connect_tg_user_qr_status`, `session_id: str = Query(...)`)
- `app/pages/accounts.py:267-286` (`accounts_connect_tg_user_refresh_qr`)
- `app/pages/accounts.py:289-326` (`accounts_connect_tg_user_verify_2fa`)
- `app/pages/accounts.py:329-358` (`accounts_connect_tg_user_complete`)
- `app/messengers/telegram_user.py:54-74, 100-112, 137-153, 155-167` (реестр
  `_qr_sessions`, ключ — только токен)

**Issue:**

Четыре маршрута мастера подключения Telegram спрашивают ТОЛЬКО «пришёл ли
вообще кто-то» (`if not user: return {"error": ...}`) и НЕ спрашивают, тот ли
это пользователь, который сеанс завёл. Сам реестр сеансов
(`_qr_sessions` в `app/messengers/telegram_user.py`) хранится в памяти процесса
и ключуется одним лишь токеном: поля владельца у `QRAuthState` нет вовсе.

Следствие полное, а не частичное. `complete_auth(session_id)` возвращает
`session_string` — сохранённую сессию Telethon, то есть ПОЛНЫЙ доступ к
аккаунту Telegram, — и обработчик `:349-356` кладёт её в `MessengerAccount`
**вызывающего**:

```python
session_string = await complete_auth(session_id)
...
account = MessengerAccount(
    user_id=user.id,          # ← ВЫЗЫВАЮЩЕГО, а не того, кто сканировал QR
    type="tg_user",
    credentials=session_string,
    status="active",
)
```

Тот же путь короче через `verify-2fa`: `submit_2fa(session_id, password)`
подписывает сеанс паролем и `:317-324` привязывает результат к вызывающему.

**Предусловие названо честно:** токен — `uuid.uuid4().hex[:16]`, то есть 64 бита
случайности от `os.urandom`, и перебором он не берётся. Дефект — не
перебираемость, а ОТСУТСТВИЕ ПРИВЯЗКИ, из-за которой утечка токена
превращается в захват аккаунта. Утечка при этом не гипотетическая: `session_id`
едет **строкой запроса** GET-маршрута (`/accounts/connect/tg_user/qr-status?session_id=…`),
который страница опрашивает циклически, — то есть штатно оседает в журнале
доступа nginx, в журналах обратного прокси и в заголовке `Referer` при любом
исходящем переходе с этой страницы. Значение, дающее полный доступ к чужому
Telegram, обязано ездить телом либо серверным состоянием, а не адресом.

Это ровно та ось, по которой ревизия Фазы 6 (`CR-02`) уже закрывала
асимметрию административных маршрутов: соседние маршруты этого же файла
проверяют владение запросом (`accounts_sync_status` зовёт
`get_sync_status_view(db, user.id, account_id)`; `accounts_retry_sync` и
`accounts_sync_groups` несут `MessengerAccount.user_id == user.id`), а мастер
подключения не проверяет ничего.

**Fix:**

Привязать сеанс к субъекту в момент создания и сверять привязку на каждом из
четырёх входов; идентификатор убрать из адреса.

```python
# app/messengers/telegram_user.py
@dataclass
class QRAuthState:
    ...
    owner_user_id: int          # ← НОВОЕ ПОЛЕ

async def start_qr_auth(api_id: int, api_hash: str, owner_user_id: int) -> tuple[str, str]:
    ...
    state = QRAuthState(client=client, qr_login=qr_login, owner_user_id=owner_user_id)

def _owned(session_id: str, user_id: int) -> QRAuthState | None:
    """Сеанс СВОЙ или None. «Нет сеанса» и «чужой сеанс» дают ОДИН исход —
    иначе ответ становится картой занятых токенов."""
    state = _qr_sessions.get(session_id)
    if state is None or state.owner_user_id != user_id:
        return None
    return state
```

```python
# app/pages/accounts.py — каждый из четырёх маршрутов
state = _owned(session_id, user.id)
if state is None:
    return {"status": "expired"}     # тот же ответ, что и у истёкшего
```

и перевести опрос статуса на `POST` с телом либо на путь
`/accounts/connect/tg_user/qr-status` БЕЗ параметра — сеанс у пользователя
единственный, и сервер находит его по `user.id` сам:

```python
@router.get("/accounts/connect/tg_user/qr-status")
async def accounts_connect_tg_user_qr_status(request, db, settings):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"status": "error", "error": "Не авторизован"}
    return get_qr_status_for_owner(user.id)   # токена в адресе больше нет
```

---

## Warnings

### WR-01: запись `app/pages/schedules.py:28` опровергается строкой 352 того же файла

**Файл:** `app/pages/schedules.py:26-34`, опровергается `app/pages/schedules.py:352`

**Issue:**

Комментарий над ввозом утверждает дословно:

> `⚠️ ID_MAX ВВОЗИТСЯ И НЕ ЗОВЁТСЯ В ЭТОМ ФАЙЛЕ НИ РАЗУ, И ЭТО НАМЕРЕННО.`
> `Имя обязано остаться доступным ПО ПРЕЖНЕМУ ПУТИ: два модуля суиты ввозят его отсюда`

Замер по файлу (`grep -n ID_MAX app/pages/schedules.py`) даёт вхождение в
ИСПОЛНЯЕМОМ коде:

```python
# app/pages/schedules.py:348-354
    try:
        value = int(form_data.get("ad_id"))
    except (TypeError, ValueError):
        return None
    if value < 1 or value > ID_MAX:      # ← ВЫЗОВ, которого «нет ни разу»
        return None
    return value
```

Цена не косметическая. Запись объявляет ввоз ЧИСТО ТРАНЗИТНЫМ, то есть
удаляемым без последствий, как только суита перестанет ввозить имя отсюда.
Следующий читатель, доверившись ей и сняв ввоз при уборке транзитных имён,
уронит `_ad_id_from_form` на `NameError` — на маршруте подтверждённого удаления
расписания, то есть в проде, а не на прогоне. Это ровно класс «запись шире
дерева», за который фаза получила круги 3, 4 и 5, — только здесь запись УЖЕ
неверна на момент отгрузки.

**Fix:**

Привести запись к дереву и назвать оба основания ввоза:

```python
# ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА ВВОЗИТСЯ, А НЕ ОБЪЯВЛЯЕТСЯ ЗДЕСЬ (план 10-24).
#
# ⚠️ У ВВОЗА `ID_MAX` ДВА ОСНОВАНИЯ, И ПЕРВОЕ — ИСПОЛНЯЕМОЕ. Величина ЗОВЁТСЯ
# в `_ad_id_from_form` (:352): необязательное поле контекста ограничивается
# ВЕЛИЧИНОЙ вручную, потому что псевдоним формы к нему неприменим —
# отбрасывание, а не отказ (разбор — докстринг помощника). Второе основание —
# сохранённый вход: два модуля суиты ввозят имя по прежнему пути
# (`tests/test_pages/test_editor_schedules.py:35`,
# `tests/test_pages/test_confirm_delete_transport.py:117`).
from app.pages.identifiers import ID_MAX, IdForm, IdPath, OptionalIdForm
```

и завести правило, которое красит расхождение автоматически, — по образцу
`test_the_identifier_bound_is_declared_exactly_once_in_the_whole_app`: обход
`ast` по модулю, утверждающий, что имя, объявленное комментарием НЕЗВАННЫМ,
действительно не встречается ни в одном `ast.Name` вне блока ввоза.

---

### WR-02: два файла одной партии по-разному отвечают на вопрос «всегда ли существует `#sched-count`»

**Файлы:**
- `app/templates/ads/partials/sched_delete_response.html:56-62` (новый файл партии)
- `app/templates/ads/form.html:202-219` (правленный той же партией)

**Issue:**

Новый файл ответа удаления утверждает без оговорок:

> `Поэтому обёртка в ads/form.html существует всегда, а сюда приезжает только её содержимое.`

Правленный той же партией `ads/form.html` утверждает обратное — и утверждает
ЯВНО, отдельным абзацем:

> `⚠️ ОБЁРТКА СТОИТ ВНУТРИ УСЛОВИЯ «РАСПИСАНИЯ ЕСТЬ», И ЭТО ВЫПОЛНЕНИЕ D-12 ПРИ НАЗВАННОЙ ГРАНИЦЕ, А НЕ ОТСТУПЛЕНИЕ ОТ НЕГО.`

Дерево подтверждает второе: `<div id="sched-count">` стои́т внутри `{%- if ad %}`
и внутри `{%- if editor.schedules %}` (`ads/form.html:202`, сам узел — `:219`).

Поведенческого отказа сегодня нет, и это перепроверено, а не предположено:
ветка фрагмента `schedules_delete` требует `returns_to_editor` И
`_ad_has_a_schedule(...)`, а форма удаления существует только внутри
отрисованного `sched_card`, то есть на экране, где обёртка уже стои́т. Дефект
здесь ЗАПИСНОЙ: два места одного факта говорят разное, одно из них ложно, и
именно ложное — то, на которое сошлётся автор СЛЕДУЮЩЕГО внеполосного узла,
целящегося в `#sched-count`. Проект сам объявил такое расхождение классом
отказа (`WR-01` того же круга: «две копии одного основания расходятся молча»),
и здесь копии разошлись в пределах одной партии.

**Fix:**

Свести к одному утверждению — сузить запись нового файла до измеренного, а не
дублировать основание:

```jinja
{#- ⚠️ УЗЕЛ ЛИНЕЙКИ ВКЛЮЧАЕТСЯ, А НЕ КОПИРУЕТСЯ, И ПОДМЕНЯЕТСЯ У НЕЁ
    СОДЕРЖИМОЕ, А НЕ УЗЕЛ (D-12 Фазы 9). Подмена узла унесла бы область
    `#sched-count` из документа…
    ОБЛАСТЬ ЖИВЁТ РОВНО ТАМ, ГДЕ ЖИВЁТ ЭТОТ ОТВЕТ, И ГРАНИЦА ЗАПИСАНА ОДИН РАЗ —
    в `ads/form.html` (абзац «⚠️ ОБЁРТКА СТОИТ ВНУТРИ УСЛОВИЯ „РАСПИСАНИЯ ЕСТЬ“»).
    Здесь она НЕ ПОВТОРЯЕТСЯ: вторая копия границы разошлась бы с первой молча. -#}
```

---

### WR-03: измеренные ссылки на строки протухли в трёх местах — читатель приземляется в прозу

**Файлы:**
- `app/pages/htmx.py:321-322` (докстринг `_glue_notice`)
- `app/pages/htmx.py:432-434` (докстринг `respond`)
- `app/templates/components/modal.html:720-723`

**Issue:**

Файлы этой партии ссылаются на строки ЧИСЛОМ и называют ссылки ЗАМЕРОМ. Три
ссылки числу не соответствуют:

| Где | Сказано | На самом деле | Что стои́т по указанному номеру |
|---|---|---|---|
| `htmx.py:321`, `htmx.py:433` | `app/pages/account_groups.py:836` | `:839` | конец докстринга `_fragment`, не вызов |
| `modal.html:721` | «обращение к `HX_LOCATION_HEADER` на **:148**» | `:169` | текст `ValueError` про latin-1 внутри `_local_path` |
| `modal.html:723` | «`respond()` там же (**:375**)» | `:475` | проза докстринга `_with_notice` |

Замер, которым это снято:

```
$ grep -n "fragment=_fragment" app/pages/*.py
app/pages/account_groups.py:599 …
app/pages/account_groups.py:839 …
app/pages/schedules.py:1240 …
$ grep -n "HX_LOCATION_HEADER\|location_response" app/pages/htmx.py app/main.py
app/main.py:226:        return location_response(exc.location)     # ← верно
app/pages/htmx.py:169:        status_code=204, headers={HX_LOCATION_HEADER: …}
app/pages/htmx.py:475:        return location_response(_with_notice(redirect, notice))
```

Цена в том, что `modal.html:764-769` объявляет эту пометку СТЕРЕЖЁННОЙ:

> `⚠️ ЭТА ПОМЕТКА НЕ ИМЕЕТ ПРАВА ПЕРЕЖИТЬ СВОЮ ИСТИННОСТЬ… Её стережёт правило test_the_transition_response_is_assembled_in_one_declared_place`

Правило сличает ЧИСЛО мест сборки и СТАТУС, а номера строк не читает вовсе —
то есть половина пометки объявлена стерегомой, будучи нестерегомой, и уже
протухла. Это тот же класс, что `WR-02` пятого круга («перечень, который надо
не забыть исправить, ЗАБЫВАЮТ»), только предмет — не перечень, а координата.

**Fix:**

Номера строк из прозы убрать, оставив имена конструкций (они переживают сдвиг
файла), либо расширить стерегущее правило до координат:

```python
# tests/test_templates/test_components.py — расширение существующего правила
CITED_ANCHORS = (
    ("app/pages/htmx.py", "HX_LOCATION_HEADER: "),
    ("app/pages/htmx.py", "return location_response("),
    ("app/main.py", "return location_response(exc.location)"),
    ("app/pages/account_groups.py", "fragment=_fragment"),
)

def test_every_line_number_cited_by_the_lever_points_at_what_it_names():
    """Координата, названная ЗАМЕРОМ, обязана указывать на названную конструкцию."""
    for path, needle in CITED_ANCHORS:
        for lineno in cited_line_numbers(MODAL_HEADER + HTMX_DOCSTRINGS, path):
            assert needle in read_line(path, lineno), (
                f"{path}:{lineno} не несёт {needle!r} — ссылка протухла"
            )
```

---

### WR-04: те же неограниченные идентификаторы живут в `app/routes/`, и вселенная гейта этого не объявляет

**Файлы:**
- `app/routes/ads.py:77` (`get_ad`), `:90` (`update_ad`), `:116` (`delete_ad`)
- `app/routes/accounts.py:56` (`delete_account`), `:73` (`get_account_status`)
- `app/routes/schedules.py:157` (`update_schedule`), `:218` (`delete_schedule`), `:234` (`toggle_schedule`)
- Вселенная гейта: `tests/test_pages/test_identifier_bounds.py:1116`
  (`CATALOGUE_DIRECTORY = APP_DIRECTORY / "pages"`, обход `glob("*.py")`)

**Issue:**

Восемь идентификаторов пути JSON-API объявлены голым `int` и уезжают операндом
сравнения по колонке тем же путём, каким уезжали закрытые входы страничного
слоя:

```python
# app/routes/ads.py:75-83
@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(ad_id: int, user_id: int = Depends(get_current_user_id), db=...):
    ad = await repo.get_by_id_and_user(ad_id, user_id)   # WHERE Ad.id == ad_id
```

Механизм отказа подтверждён на драйвере суиты:

```
$ python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('select 1 where 1 = ?', (10**26,))"
OverflowError: Python int too large to convert to SQLite INTEGER
```

на PostgreSQL порог ниже (`DataError` вне диапазона int32), то есть в проде
разрыв шире.

Дефект не в самом факте — это давний код, и фаза его не заводила. Дефект в
том, что ВСЕЛЕННАЯ обоих принуждений нигде не объявлена ЧИСЛОМ и не оговорена
изъятием. `test_every_identifier_parameter_of_the_catalogue_carries_the_bound`
обходит только `app/pages/*.py`; `CATALOGUE_APPENDIX` (10 записей с вердиктом
`open`) тоже целиком про страничный слой. При этом
`app/pages/identifiers.py:1` объявляет предмет словами
«ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА — ОДНА НА ВЕСЬ ПРОЕКТ», а
`app/pages/admin.py:99` называет единственность держащим правилом
«во всём `app/`». Читатель, пришедший от этих двух записей, заключит, что
проект закрыт целиком, — и заключит неверно на восьми входах.

Это ровно та форма, которую сам проект уже потребовал от гарда происхождения
(`common.py:781-816`: «ГРАНИЦА ВСЕЛЕННЫХ ОБОИХ ГЕЙТОВ НАЗВАНА ЧИСЛОМ, А НЕ
СЛОВОМ „ПОЛНОТА“»), — здесь той же формы нет.

**Fix:**

Либо закрыть входы тем же псевдонимом (правка механическая, восемь сигнатур):

```python
from app.pages.identifiers import IdPath

@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(ad_id: IdPath, ...):
```

либо — если владелец решает отложить — назвать границу вселенной ЧИСЛОМ рядом
с гейтом, по образцу, который проект уже принял:

```python
# tests/test_pages/test_identifier_bounds.py
# ⚠️ ВСЕЛЕННАЯ ГЕЙТА — `app/pages/*.py`, И ЭТО ГРАНИЦА, А НЕ ПОЛНОТА.
# ЗАМЕР 2026-09-08: идентификаторов пути в `app/routes/` — ВОСЕМЬ, границы не
# несёт НИ ОДИН. Вход JSON-API закрыт токеном, а не cookie, и перевод его —
# предмет отдельной фазы; число стережёт правило ниже и падает на пустом
# множестве.
API_UNBOUNDED_IDENTIFIERS_DECLARED = 8

def test_the_boundary_of_the_catalogue_universe_is_declared_by_number():
    found = identifier_parameters(_read_directory(APP_DIRECTORY / "routes"))
    assert found, "обход маршрутов API выродился — правило зеленело бы ВАКУУМОМ"
    unbounded = [p for p in found if not p.carries_the_bound]
    assert len(unbounded) == API_UNBOUNDED_IDENTIFIERS_DECLARED, ...
```

---

### WR-05: текст исключения внешней системы доезжает до пользователя — там же, где соседний обработчик этого файла запрещает это прямо

**Файл:** `app/pages/accounts.py:244-245`, `:421-422`, `:605-606`
(запрет, который они нарушают, — `app/pages/accounts.py:925-937`)

**Issue:**

Три места собирают сообщение пользователю из `str(e)` необъявленного
исключения:

```python
# :244-245  — уезжает JSON-ответом в браузер
except Exception as e:
    return {"error": f"Ошибка запуска QR авторизации: {e}"}

# :421-422  — уезжает в контекст шаблона connect_wa.html и печатается
except Exception as e:
    error = f"Ошибка подключения к WA Bridge: {e}"

# :605-606  — то же для MAX
except Exception as e:
    error = f"Ошибка подключения к MAX: {e}"
```

Соседний широкий `except` ЭТОГО ЖЕ ФАЙЛА (`:925-937`) объявляет ровно обратное
правило и объясняет почему:

> `На аккаунт пишется СВОЙ текст, а не str(e): сюда долетает что угодно, включая IntegrityError с полным SQL и значениями параметров, а шаблон печатает error пользователю дословно (T-03-17).`

Сюда «что угодно» долетает такое же: конструктор адаптера и свойство
`bridge_url` бросают `RuntimeError` с адресом моста, `httpx` — с полным URL
(включая всё, что в нём стоит), Telethon — с внутренними путями. XSS здесь нет
(автоэкранирование Jinja цело, `|safe` в дереве шаблонов НОЛЬ — проверено), но
раскрытие внутренней топологии есть, и правило, которому оно противоречит,
записано в тридцати строках ниже по тому же файлу.

**Fix:**

Взять форму у соседа: свой текст на экран, исходный — в журнал с `exc_info`.

```python
# app/pages/accounts.py, все три места
except Exception as e:
    import structlog
    structlog.get_logger().error(
        "tg_qr_start_failed", user_id=user.id, error=str(e), exc_info=True
    )
    return {"error": UNEXPECTED_FAILURE_MESSAGE}   # уже ввезён в этот файл
```

(`UNEXPECTED_FAILURE_MESSAGE` ввозится файлом на `:18` и используется на `:946`
— второй константы заводить не нужно.)

---

### WR-06: перечень каналов в `accounts_sync_groups` существует в двух экземплярах, и второй молча даёт `UnboundLocalError`

**Файл:** `app/pages/accounts.py:811-812` и `:891-909`, отказ приземляется на `:953`

**Issue:**

Допустимые каналы перечислены дважды и в разных формах:

```python
# :811 — ГАРД, перечень кортежем
if account.type not in ("tg_user", "wa", "max"):
    return RedirectResponse(url=account_groups_url, status_code=302)
...
# :892-909 — ВЕТВЛЕНИЕ, тот же перечень цепочкой if/elif/elif БЕЗ else
    if account.type == "tg_user":
        fetched_groups = await messenger.get_groups(); messenger_type = "tg_user"
    elif account.type == "wa":
        ...
    elif account.type == "max":
        ...
```

Сегодня копии согласованы, поэтому отказа нет. Но канал, добавленный в гард и
забытый в цепочке (правка в двух местах, разнесённых на 80 строк), оставит
`fetched_groups` и `messenger_type` НЕПРИВЯЗАННЫМИ, и `UnboundLocalError`
поднимется на `:953`:

```python
await apply_group_resync(db, account, fetched_groups, messenger_type=messenger_type)
```

— то есть УЖЕ ЗА ПРЕДЕЛАМИ внутреннего `try/except`, который кончается на
`:948`. Результат — `500` вместо красной плашки на аккаунте, ровно то, что
широкий `except` этого обработчика заведён не допускать (`:926-931`:
«Сузить блок … означало бы вернуть на экран стек-трейс там, где раньше была
красная плашка»). Заявка при этом освободится (`finally` на `:991`), но
пользователь получит стек вместо сводки — на маршруте, чей докстринг обещает
обратное.

**Fix:**

Свести перечень к одному объявлению и сделать невыразимой ветку без адаптера:

```python
# перечень ОДИН, и он же строит адаптер
SYNC_ADAPTERS = {
    "tg_user": lambda account, settings: TelegramUserMessenger(
        session_string=account.credentials,
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
    ),
    "wa": lambda account, settings: WhatsAppMessenger(session_id=str(account.id)),
    "max": lambda account, settings: MaxMessenger(session_id=str(account.id)),
}

build = SYNC_ADAPTERS.get(account.type)
if build is None:                       # гард и ветвление — одно множество
    return RedirectResponse(url=account_groups_url, status_code=302)
...
messenger = build(account, settings)
fetched_groups = await messenger.get_groups()
messenger_type = account.type
```

---

## Info

### IN-01: второй экземпляр порога предупреждения счётчика — литерал `0.9` в разметке

**Файл:** `app/templates/ads/form.html:356` (`const TEXT_WARN_AT = {{ (editor.text_limit * 0.9) | round | int | tojson }};`),
первый экземпляр — `app/pages/ads.py:55` (`TEXT_WARN_RATIO = 0.9`)

**Issue:** сервер уже кладёт готовое значение в контекст
(`editor.text_warn_at`, `app/pages/ads.py:403`), и серверная отрисовка счётчика
им пользуется (`ads/form.html:98`), а JS его игнорирует и пересчитывает по
собственному литералу (`:356`, читается на `:386`). Правка `TEXT_WARN_RATIO` в Python оставит клиент на 0.9
молча — и разойдутся ровно две поверхности одного счётчика. Дефект
унаследованный, этой партией не заведён.

**Fix:** отдать в JS то же значение, что уже посчитано сервером:
`const TEXT_WARN_AT = {{ editor.text_warn_at | tojson }};` — и снять из JS ветку
`imagePaths.length ? CAPTION_LIMIT : TEXT_WARN_AT`, заменив её пересчётом на
стороне сервера при следующем ответе автосохранения (либо оставив обе величины,
но взяв обе из контекста, а не из литерала).

---

### IN-02: выражение-оператор с отброшенным значением читается как мёртвый код

**Файл:** `app/pages/htmx.py:477-480`

**Issue:** проверка адреса на ветке фрагмента выполнена голым вызовом, значение
которого отбрасывается:

```python
    # Адрес деградации проверяется ДАЖЕ НА ВЕТКЕ ФРАГМЕНТА, где он никуда не уезжает…
    _with_notice(redirect, notice)
```

Намерение объяснено комментарием, но форма — та, которую любой линтер и любой
«уборщик мёртвого кода» снимет первой, и снятие пройдёт зелёным, если правила
суиты меряют только исходы `respond()` на годных адресах.

**Fix:** сделать намерение выразимым в самой строке и закрепить его правилом,
красящим снятие:

```python
    # Возвращаемое значение здесь НЕ НУЖНО — нужен ОТКАЗ на негодном адресе.
    _assert_local(redirect, notice)   # тонкая обёртка над `_with_notice`, имя называет предмет
```

плюс правило `test_a_fragment_branch_still_refuses_a_hostile_degradation_address`
(вызов `respond` с `fragment=…` и внешним `redirect=` обязан поднять
`ValueError`).

---

### IN-03: числа изъятий обхода считаются по всему `.planning/` и краснеют от штатного продвижения проекта

**Файл:** `tests/test_planning/test_the_walkthrough_cannot_self_certify.py:55, 67, 300-326`

**Issue:** `MARKED_FORM_EXEMPT_DECLARED = 11` и
`DECLARED_COUNT_EXEMPT_DECLARED = 12` — разности между числом ВСЕХ файлов
`.planning/**/*UAT*.md` и числом попавших во вселенную. Любая следующая фаза,
заведшая свой `NN-UAT.md` без таблиц отметок (нормальное состояние
свежесозданного артефакта), поднимет обе разности и покрасит правило,
не сказав ничего о продукте. Правило само это признаёт («ВЫРОСШЕЕ изъятие — это
либо новый артефакт другой эпохи…»), то есть цена принята; но принята она
молча в том смысле, что артефакт-нарушитель ещё не существует, а красный прогон
уже назначен.

**Fix:** считать изъятие ПОИМЁННО, а не разностью, — тогда новый артефакт
краснит только если он ОБЪЯВИЛ себя закрытым:

```python
MARKED_FORM_EXEMPT: frozenset[str] = frozenset({
    ".planning/phases/01-…/01-UAT.md",   # эпоха до таблиц отметок
    ...
})
def test_the_declared_vocabularies_and_exemptions_agree():
    exempt = {name for name, _ in sources} - {name for name, _ in marked_walkthroughs(sources)}
    assert exempt == MARKED_FORM_EXEMPT, (
        f"изъятие разошлось с деревом; лишние: {sorted(exempt - MARKED_FORM_EXEMPT)}, "
        f"пропавшие: {sorted(MARKED_FORM_EXEMPT - exempt)}"
    )
```

---

### IN-04: реестр якорей обхода проверяет только половину связи

**Файл:** `tests/test_templates/test_walkthrough_anchors.py:57-129, 169-182`

**Issue:** правило утверждает, что каждый якорь ЕСТЬ в шаблоне-источнике, и
делает это честно (отрицательный контроль показан на обеих ветвях). Но поле
`step` — «шаг 1.8», «шаг 3.4» — не сверяется НИ С ЧЕМ: файл обхода
(`.planning/phases/10-…/10-UAT.md`) правилом не читается вовсе. Перенумерация
шагов обхода оставит реестр зелёным, а ссылки — указывающими в никуда; это тот
же класс, что `WR-03` выше, только координата не строчная, а шаговая.

**Fix:** замкнуть вторую половину связи тем же обходом, которым
`test_the_walkthrough_cannot_self_certify.py` уже разбирает шапки и разделы:

```python
def test_every_anchor_names_a_step_that_the_walkthrough_declares():
    declared = walkthrough_step_ids(WALKTHROUGH_PATH.read_text(encoding="utf-8"))
    assert declared, "шагов в обходе не найдено — правило зеленело бы ВАКУУМОМ"
    orphans = sorted({a.step for a in WALKTHROUGH_ANCHORS} - declared)
    assert not orphans, f"якоря ссылаются на шаги, которых в обходе нет: {orphans}"
```

---

## Verified and not reported

Просмотрено, сверено с деревом, отказа не найдено — перечислено, чтобы
следующий круг не проходил по этим местам заново:

* **Гард происхождения.** `is_same_origin` (`common.py:826-833`) — три ветви,
  явная проверка `origin_host is not None`; 13 площадок вызова, 36 POST-ов
  страничного слоя, шесть изменяющих маршрутов админки покрыты все.
* **`_local_path`.** Схема, протокол-относительный адрес, обратная косая,
  управляющие символы, не-ASCII — отвергаются; значение в текст ошибки не
  подставляется.
* **Приклейка.** Порядок трёх забот (статус → тип → длина) верен; пересчёт
  `content-length` через `MutableHeaders` действует; правило проверяет обе
  стороны.
* **Панель подтверждения.** Все 18 мест приземляются на переведённые
  обработчики; `hx-swap="none"` + `HX-Location` даёт своп тела, а не тихую
  потерю ответа; выражение `x-on:htmx:after-request` синтаксически корректно и
  под правилом Alpine `rightSideSafeExpression` исполняется как два оператора;
  три пути ухода панели гейтованы признаком отправки.
* **Ключ панели.** Все `modal(id=…)` собираются из серверных величин
  (первичные ключи, `loop.index0`); значения из тела очереди в имя атрибута не
  попадают.
* **Экранирование.** `|safe` в `app/templates/**` — ноль; `data-diag`
  диагностического блока читается через `dataset`, а не через `eval`;
  `tojson` применён ко всем подстановкам в JS-контекст.
* **Своп тела по `HX-Location`.** `htmx` и `alpine` подключены в `<head>` и
  переисполнению не подлежат; `htmx_error_banner.html` защищён признаком на
  `document.body`, переживающим своп `innerHTML`; единственный необёрнутый
  инлайн-скрипт с `let` верхнего уровня целью перехода не является и изъят
  ИМЕНОВАННО с воспроизводимым основанием.
* **Имперсонация.** Cookie ставится на объект, ВОЗВРАЩЁННЫЙ слоем ответа;
  `require_admin` читает права по действующему лицу; три необратимых/денежных
  маршрута закрыты `forbid_when_impersonating`.
* **Суита.** 603 правила изменённых модулей зелёные; тестов без утверждений
  нет (три кандидата делегируют в помощники с утверждениями); `skip` — ноль;
  вселенные всех обходов защищены проверкой непустоты; отрицательные контроли
  есть у каждого несущего правила, которое зелено первым прогоном.

Записанные открытыми и НЕ переоткрытые: `CATALOGUE_APPENDIX` (10 записей,
вердикт `open`), мёртвый первый дизъюнкт условия закрытия панели,
`OOB_TARGET_EXCEPTIONS`, `OWN_RESPONSE_EXITS` (9 записей, «ЖДЁТ ВЛАДЕЛЬЦА»),
цена третьего внеполосного узла (`WR-05`/`WR-02` прежних кругов), названная
граница гарда «без обоих заголовков».

---

_Reviewed: 2026-09-08T21:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
