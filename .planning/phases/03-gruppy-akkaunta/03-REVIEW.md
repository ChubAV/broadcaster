---
phase: 03-gruppy-akkaunta
reviewed: 2026-08-12T00:00:00Z
depth: standard
files_reviewed: 48
files_reviewed_list:
  - alembic/versions/0014_sync_result_and_group_missing.py
  - app/application/accounts/dto.py
  - app/application/accounts/group_resync.py
  - app/application/scheduling/use_cases.py
  - app/main.py
  - app/models/group.py
  - app/models/messenger_account.py
  - app/pages/__init__.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/group_row.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partial_cards.html
  - app/templates/account_groups/partials/sync_result.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/components/modal.html
  - app/worker/tasks.py
  - tests/conftest.py
  - tests/test_application/test_account_deletion_schedules.py
  - tests/test_application/test_collect_due_inactive_group.py
  - tests/test_application/test_group_resync.py
  - tests/test_e2e.py
  - tests/test_migrations/test_0013_ad_status.py
  - tests/test_migrations/test_0014_sync_result_columns.py
  - tests/test_models/test_sync_result_columns.py
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedules_detached_account.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_history.py
  - tests/test_routes/test_limits.py
  - tests/test_routes/test_schedules.py
  - tests/test_routes/test_schedules_api_null.py
  - tests/test_routes/test_schedules_api_ownership.py
  - tests/test_routes/test_schedules_toggle_detached.py
  - tests/test_routes/test_sync_groups.py
  - tests/test_templates/test_components.py
  - tests/test_worker/test_tasks.py
findings:
  critical: 2
  warning: 5
  info: 8
  total: 15
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-08-12
**Depth:** standard
**Files Reviewed:** 48
**Status:** issues_found

## Summary

Проверены пять областей повышенного риска, названных в задании. Четыре из пяти
держатся, и это стоит зафиксировать явно, потому что дальше речь пойдёт только о
дефектах:

- **Владение проверяется на каждом входе.** Все пять входов
  (`account_groups_page`, `account_groups_partial`, `account_groups_sync_status`,
  `account_groups_toggle`, `account_groups_delete`) самостоятельно вызывают
  `get_user_from_cookie` и затем либо `_load_owned_account`, либо тройной WHERE
  по `(id, user_id, account_id)`. Наследования проверки от страницы нет ни в
  одном обработчике; поллинговый вход отвечает пустым телом, а не редиректом.
  `_schedule_counts` дополнительно ограничивает выборку расписаний владельцем
  через связь с `Ad`. Заявка модуля соответствует коду.
- **Утечки `credentials` нет.** Ни `account_groups/list.html`, ни
  `accounts/list.html`, ни `accounts/partial_cards.html`, ни
  `accounts/partials/sync_status_card.html`, ни `sync_result.html` не выводят
  `account.credentials` ни в текст, ни в атрибут.
- **Заглушка `/groups` безусловна.** `groups_retired` возвращает
  `RedirectResponse("/accounts")` независимо от входа; параметр пути в цель
  редиректа не подставляется, open redirect невозможен. Маршрут
  `/groups/{deep_link:path}` регистрируется внутри `pages_router` и не
  перекрывает ни один существующий маршрут (`/admin/groups-info` живёт под
  другим префиксом).
- **Миграция 0014 корректна.** Три additive nullable-колонки без
  `server_default`; downgrade снимает ровно те же три в обратном порядке;
  `down_revision = "0013"`. Round-trip закреплён тестом.

Пятая область — `apply_group_resync` и три её вызывающих — держится частично.
Прохибиция D-11 соблюдена буквально: модуль не удаляет строк и не содержит имени
`is_active` вовсе. Но **контур обработки отказа мессенджера, ради которого фаза
завела `record_sync_failure` и плашку ошибки, в продакшене недостижим**: все три
реализации `get_groups()` глушат исключения и возвращают `[]`, а пустой ответ
хелпер трактует как авторитетное «всех групп больше нет». Это первые два
блокера. К ним примыкают пять предупреждений, из которых три — расхождения между
утверждениями комментариев и фактическим поведением кода.

## Structural Findings (fallow)

Блок `<structural_findings>` в задании не передавался — структурного пред-прохода
не было. Кросс-модульные наблюдения ниже получены собственным чтением и помечены
как обычные находки (IN-01, IN-02, IN-05).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Ветка записи отказа синхронизации недостижима — сбой мессенджера выглядит как успешный синк

**File:** `app/pages/accounts.py:778-816`
**Related:** `app/messengers/whatsapp.py:116-126`, `app/messengers/max.py:107-117`,
`app/messengers/telegram_user.py:247-262`, `tests/test_routes/test_sync_groups.py:498-518`

**Issue:**
Обработчик обёрнут в `try/except Exception`, и в `except` вызывается
`record_sync_failure`. Комментарий над блоком утверждает: «Новое здесь только
одно — отказ внешней системы записывается на аккаунт, а не теряется 500-й».
Но **ни одна из трёх реализаций `get_groups()` не поднимает исключений**:

```python
# app/messengers/whatsapp.py:116  (max.py:107 — посимвольно то же самое)
async def get_groups(self) -> list[dict]:
    try:
        response = await client.get(self._url("groups"), timeout=600.0)
        if response.status_code == 200:
            return response.json()
        self.log.error("get_groups_error", http_status=response.status_code)
        return []
    except Exception as e:
        self.log.error("get_groups_error", error=str(e), exc_info=True)
        return []            # <-- сюда уходит ВСЁ, включая RuntimeError
                             #     "Cannot start wa-worker" из bridge_url
```

`telegram_user.get_groups()` устроен так же: `except Exception` + `return groups`,
где `groups` к этому моменту пуст.

Следствие цепочки: контейнер wa-worker не поднялся / мост вернул 500 / сессия
Telethon протухла → `fetched_groups == []` → `except` **не срабатывает** →
`apply_group_resync(db, account, [], ...)` помечает `missing_since` **у всех**
групп аккаунта и записывает на аккаунт сводку **успеха**
`{"found":0,"new":0,"renamed":0,"missing":42,"error":null}`. Экран групп рисует
`alert(..., 'success')` — зелёную плашку «Синхронизация завершена: найдено 0,
новых 0, обновлено имён 0, не найдено 42» — и ни одного признака того, что
мессенджер вообще не отвечал.

До этой фазы то же самое `[]` было безвредно: блок был «только добавить», и
пустой ответ означал ноль вставок. Именно переход на полную переинвентаризацию
(D-10) сделал неотличимость «мессенджер молчит» и «групп ноль» разрушительной.

Тест `test_sync_failure_is_recorded_not_swallowed` зелёный, но он подменяет
`TelegramUserMessenger` моком с `side_effect=RuntimeError(...)`, то есть проверяет
контракт, которого у настоящего класса нет. Соседний
`test_sync_marks_missing_group_but_keeps_it` подаёт `AsyncMock(return_value=[])`
и закрепляет именно то поведение, которое настоящий класс выдаёт при отказе.

**Fix:**
Различить «мессенджер не ответил» и «мессенджер вернул ноль групп» на границе
адаптера — исключение глушить нельзя, потому что вызывающий не может отличить
`[]` от `[]`:

```python
# app/messengers/whatsapp.py (аналогично max.py и telegram_user.py)
class MessengerFetchError(RuntimeError):
    """Мессенджер не отдал состав групп — это НЕ пустой список."""

async def get_groups(self) -> list[dict]:
    client = get_http_client()
    try:
        response = await client.get(self._url("groups"), timeout=600.0)
    except Exception as e:
        self.log.error("get_groups_error", error=str(e), exc_info=True)
        raise MessengerFetchError(f"{type(e).__name__}: {e}") from e
    if response.status_code != 200:
        self.log.error("get_groups_error", http_status=response.status_code)
        raise MessengerFetchError(f"мост вернул HTTP {response.status_code}")
    return response.json()
```

и ловить `MessengerFetchError` (а не голый `Exception`) в
`app/pages/accounts.py`. Проверить остальных потребителей `get_groups()` перед
сменой контракта. Тест обязан вызывать реальный класс с подменённым HTTP-слоем
(`respx`/подменённый `get_http_client`), а не мок самого метода — иначе он
снова зазеленеет на несуществующем контракте.

---

### CR-02: Пустой ответ мессенджера принимается за авторитетную опись без единого предохранителя

**File:** `app/application/accounts/group_resync.py:137-158`
**Related:** `app/worker/tasks.py:292-316` (WA), `app/worker/tasks.py:392-415` (MAX),
`app/pages/accounts.py:815`

**Issue:**
Хелпер помечает пропавшими все группы, которых нет в `fetched`, без какой-либо
проверки правдоподобия ответа:

```python
missing = 0
marked_at = _utcnow()
for external_id, group in existing.items():
    if external_id in seen:
        continue
    missing += 1
```

Триггеров у вырожденного `fetched` три, и все три достижимы независимо от CR-01:

1. **Страничный путь** — см. CR-01.
2. **WA/MAX Celery** — `groups = sync_data.get("groups") or []` (`tasks.py:293`,
   `tasks.py:393`). Мост объявляет `state == "ready"`, но кладёт в `groups`
   `null`, `[]` или вовсе не кладёт поле → все группы аккаунта помечаются, а на
   аккаунт пишется сводка успеха. Форма ответа моста (`{"state": ..., "groups":
   [...] | None}`) допускает это по своей же документации в
   `whatsapp.py:150-151`.
3. **Ре-синк отключённой сессии** — WhatsApp/MAX после разлогина отдают 200 и
   пустой список.

Прохибиция D-11 («не удалять, потому что мессенджер может не отдать группу
из-за собственного сбоя») распознала опасность верно, но выбрала защиту не того
уровня: строки уцелели, а вот `missing_since` — это состояние, которое сама же
фаза выводит в интерфейс как утверждение о факте («не найдена при синке»,
`group_row.html:49-53`). Массовая ложная пометка обесценивает признак: после
одного сбоя моста весь список аккаунта помечен, и настоящая пропажа одной группы
в нём неразличима.

Единственный сдерживающий фактор — `if not account or account.status != "syncing"`
в фоновых путях — от вырожденного `ready`-ответа не защищает вовсе: статус в этот
момент как раз `syncing`.

**Fix:**
Ввести в `apply_group_resync` явный предохранитель и обязать вызывающего решать,
что делать с подозрительным ответом, вместо молчаливого применения:

```python
async def apply_group_resync(
    session, account, fetched, *, messenger_type: str,
    allow_full_wipe: bool = False,
) -> GroupResyncResult:
    ...
    # Ответ, не содержащий НИ ОДНОЙ ранее известной группы при непустом
    # существующем составе, — с большей вероятностью сбой мессенджера, чем
    # одномоментный выход пользователя из всех чатов. Пометка не ставится,
    # результат называет причину.
    if existing and not seen and not allow_full_wipe:
        return GroupResyncResult(
            found=0, created=0, renamed=0, missing=0,
            error="мессенджер вернул пустой состав групп — пометки не ставились",
        )
```

и записывать этот результат через ту же форму `last_sync_result` (ветка `error`
уже умеет рисовать красную плашку). `allow_full_wipe=True` оставить только для
пути, где пустой состав действительно достоверен, если такой найдётся.
Закрепить тестом: непустой существующий состав + пустой `fetched` не ставит ни
одного `missing_since`.

## Warnings

### WR-01: Тумблер группы не работает без JavaScript, хотя комментарий утверждает обратное

**File:** `app/templates/account_groups/includes/group_row.html:54-63`
**Related:** `app/templates/components/toggle.html:6-15`

**Issue:**
Комментарий заявляет: «Перехват на форме — это и есть базовый путь без JS: не
навесится Alpine — форма уйдёт настоящим POST-ом на тот же маршрут (D-09,
правило Фазы 2)». Код это не обеспечивает:

```html
<form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/toggle"
      x-data x-on:change="$el.submit()">
  {{- toggle(name='is_active', checked=group.is_active, ...) -}}
</form>
```

Внутри формы — единственный элемент, `<input type="checkbox">` (см.
`toggle.html:9`). Кнопки отправки нет. Неявная отправка по Enter спецификацией
HTML для формы без submit-кнопки и без единственного текстового поля не
предусмотрена. То есть без Alpine форма **не отправляется никак**, и группу
невозможно ни включить, ни выключить.

Соседняя форма удаления сделана правильно и подтверждает разницу: в ней стоит
`button(...)`, а макрос `button` по умолчанию рендерит `type="submit"`
(`components/button.html:16`) — без Alpine она честно уходит POST-ом.

Цена ошибки выросла именно в этой фазе: с D-05 тумблер — единственный способ
исключить группу из рассылки, не удаляя её.

**Fix:**
Добавить в форму настоящую submit-кнопку и скрыть её только при живом Alpine —
тогда путь без JS существует, а с JS поведение не меняется:

```html
<form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/toggle"
      x-data x-on:change="$el.submit()">
  {{- toggle(name='is_active', checked=group.is_active, id='group-toggle-' ~ group.id,
             title='Отключить' if group.is_active else 'Включить') -}}
  <noscript>{{ button('Применить', variant='ghost') }}</noscript>
</form>
```

либо, если `<noscript>` в проекте не используется, — обычная кнопка с
`x-init="$el.remove()"`. Закрепить тестом разметки: форма тумблера обязана
содержать элемент, отправляющий её без JS.

---

### WR-02: Неудавшийся синк переставляет `last_synced_at` — шапка и пустое состояние начинают врать

**File:** `app/application/accounts/group_resync.py:161-173`
**Related:** `app/templates/account_groups/list.html:39-45`,
`app/templates/account_groups/list.html:194-200`

**Issue:**
`record_sync_failure` пишет `account.last_synced_at = _utcnow()` на **провале**.
Модель определяет эту колонку иначе (`messenger_account.py:20-29`: «результат
последней синхронизации», шапка «последняя синхронизация N назад»), и оба
потребителя читают её как «синк состоялся»:

1. `list.html:41-42` — при `last_synced_at` рисует «последняя синхронизация
   только что». Одновременно ниже, на `list.html:115-117`, стоит красная плашка
   «Синхронизация не удалась: …». Экран сообщает два противоречащих факта.
2. `list.html:194` — ветка пустого состояния:
   ```jinja
   {% elif account.last_synced_at %}
   {{ empty_state('Все группы удалены', hint='Запустите синхронизацию, ...') }}
   ```
   Аккаунт, у которого синхронизация не удавалась **ни разу**, а групп нет
   никогда не было, получает утверждение «Все группы удалены». Комментарий над
   веткой (`list.html:181-188`) прямо перечисляет три состояния и обосновывает,
   почему их нельзя называть одним словом, — но условие различает их по колонке,
   которую провал уже испортил.

**Fix:**
Не трогать `last_synced_at` при провале — время попытки, если оно нужно, писать
отдельно либо брать из самого `last_sync_result`:

```python
async def record_sync_failure(session, account, message: str) -> None:
    # last_synced_at НЕ трогается: колонка означает «синхронизация состоялась»,
    # и шапка «последняя синхронизация N назад» обязана называть последний
    # УДАВШИЙСЯ синк. Время неудачной попытки несёт сама сводка.
    account.last_sync_result = _encode_result(
        GroupResyncResult(found=0, created=0, renamed=0, missing=0, error=message)
    )
```

Тест: после `record_sync_failure` на свежем аккаунте `last_synced_at is None`, а
экран показывает «Групп пока нет», а не «Все группы удалены».

---

### WR-03: Guard `status == "syncing"` не закрывает заявленную гонку двойного нажатия и может породить дубли групп

**File:** `app/pages/accounts.py:771-773`
**Related:** `app/models/group.py:9-41`, `app/application/accounts/group_resync.py:89-128`

**Issue:**
Комментарий утверждает: «Guard повторного запуска: он же закрывает гонку двойного
нажатия». Но обработчик **нигде не выставляет** `account.status = "syncing"` —
он выполняет синхронизацию синхронно и сразу коммитит результат. Значение
`syncing` ставят только фоновые пути (`accounts_retry_sync`,
`accounts_connect_*_status`). Следовательно, два одновременных POST-а
`/accounts/{id}/sync-groups` для tg_user оба читают `status == "active"`, оба
проходят guard и оба выполняют `apply_group_resync`.

Дальше — отсутствие страховки на уровне схемы. У `groups` нет уникального
ограничения на `(account_id, group_external_id)`: в модели объявлены только
первичный ключ и `index=True` на `user_id`. Две параллельные транзакции читают
одинаковый пустой `existing`, обе делают `session.add(Group(...))` для одного и
того же внешнего идентификатора — и в таблице появляются две строки на одну
группу мессенджера. Обе видны на экране, обе выбираемы в расписаниях; выбор
обеих означает две отправки в один чат.

Побочно: `existing` строится словарём по `group_external_id`
(`group_resync.py:95-97`), поэтому при уже существующих дублях одна из строк
навсегда выпадает из обработки — её имя не обновляется и `missing_since` на неё
не ставится.

**Fix:**
Две правки, и обе нужны:

1. Ограничение на уровне схемы (отдельной ревизией, с дедупликацией
   существующих строк в ней же):
   ```python
   class Group(Base):
       __table_args__ = (
           UniqueConstraint("account_id", "group_external_id",
                            name="uq_groups_account_external"),
       )
   ```
2. Либо честно занимать статус на время работы, либо убрать ложное утверждение
   из комментария:
   ```python
   account.status = "syncing"
   await db.commit()          # занимаем состояние ДО похода в мессенджер
   try:
       ...
   finally:
       account.status = "active"
       await db.commit()
   ```

---

### WR-04: Ответ мессенджера объявлен недоверенным, но не проверяется ни по форме, ни по длине

**File:** `app/application/accounts/group_resync.py:68-135`
**Related:** `app/messengers/whatsapp.py:121`, `app/messengers/max.py:112`,
`app/models/group.py:20-21`

**Issue:**
Докстринг обещает: «`fetched` — последовательность словарей … Содержимое
НЕДОВЕРЕННОЕ: и идентификатор, и имя приходят из внешней системы». Проверок при
этом ноль:

- `for item in fetched: external_id = item.get("id")` — если мост вернул
  JSON-объект вместо массива (`{"error": "..."}`), цикл идёт по строковым
  ключам, и `str.get` даёт `AttributeError` → 500 через
  `generic_error_handler`. Источник — `response.json()` без валидации
  (`whatsapp.py:121`, `max.py:112`). То же при массиве скаляров `[1, 2, 3]`.
- `name = item.get("name") or external_id` — длина не ограничена, а колонки
  объявлены `String(255)`. На SQLite (вся тестовая суита) длина не проверяется
  вовсе; на PostgreSQL (прод) строка длиннее 255 даёт `DataError` при commit.
  То есть класс дефекта, который ни один зелёный тест поймать не может.
- `external_id = str(external_id)` — тот же `String(255)`, та же проблема.

**Fix:**
Отфильтровать и обрезать на входе хелпера — там, где недоверенность объявлена:

```python
_NAME_MAX = 255
_EXTERNAL_ID_MAX = 255

for item in fetched:
    if not isinstance(item, Mapping):
        continue                      # мусорный элемент не роняет весь синк
    external_id = item.get("id")
    if external_id is None:
        continue
    external_id = str(external_id)[:_EXTERNAL_ID_MAX]
    ...
    raw_name = item.get("name")
    name = (str(raw_name) if raw_name else external_id)[:_NAME_MAX]
```

и защитить сам вход:

```python
if not isinstance(fetched, (list, tuple)):
    raise ValueError("состав групп пришёл не списком")
```

Тест обязан подавать `{"error": "..."}`, `[1, 2, 3]` и имя длиной 5000 символов.

---

### WR-05: Массовая пропажа групп отображается зелёной плашкой успеха

**File:** `app/templates/account_groups/list.html:113-129`

**Issue:**
Ветвление плашки бинарно: есть `error` — красный `alert`, нет — зелёный
`'success'`. Но сводка без `error` может нести произвольно плохую новость:

```jinja
{{- alert('Синхронизация завершена: найдено ' ~ sync_result.get('found')|int ~
          ', новых ' ~ sync_result.get('new')|int ~
          ', обновлено имён ' ~ sync_result.get('renamed')|int ~
          (', не найдено ' ~ missing if missing > 0 else ''), 'success') -}}
```

«Синхронизация завершена: найдено 0, новых 0, обновлено имён 0, не найдено 42» —
это зелёное сообщение об исчезновении всех групп аккаунта. Комментарий на
`list.html:119-121` объясняет, почему сегмент не печатается при нуле («читается
как отчёт о проблеме, которой нет»), — но обратный случай, когда проблема есть,
цветом не отмечен. Это тот же экран, на котором CR-01/CR-02 массово ставят
ложные пометки, поэтому цена ровно здесь и максимальна.

**Fix:**
Выбирать вариант плашки по содержимому сводки, а не только по наличию `error`:

```jinja
{%- set missing = sync_result.get('missing')|int -%}
{%- set tone = 'warning' if missing > 0 else 'success' -%}
{{- alert('Синхронизация завершена: найдено ' ~ ... , tone) -}}
```

## Info

### IN-01: Мёртвые импорты в `app/worker/tasks.py`

**File:** `app/worker/tasks.py:7,9,17,22`
**Issue:** `select` использовался снятыми в этой фазе inline-блоками синка и
после рефакторинга не используется нигде в модуле. Заодно (уже до фазы) мертвы
`joinedload`, `Schedule`, `compute_next_run_at`, `get_image_url`.
**Fix:** удалить `from sqlalchemy import select`, `from sqlalchemy.orm import
joinedload`, `from app.models.schedule import Schedule`,
`from app.services.schedule_service import compute_next_run_at`,
`from app.services.s3 import get_image_url`. Прогнать линтер по модулю (`ruff`
в окружении не установлен — стоит добавить его в dev-зависимости).

### IN-02: Комментарии ссылаются на код, снесённый этой же фазой

**File:** `app/pages/ads.py:207`, `app/pages/schedules.py:110`,
`app/templates/components/filters.html:8`
**Issue:** Первые два места называют `app/pages/groups.py` «образцом обхода»
JSON-списка `group_ids` и подсчёта расписаний. После плана 03-08 в этом файле
осталась только заглушка-редирект — образца там нет. `filters.html:8` даёт
пример вызова `{% call filters('groups-filters', action='/groups') %}`, где
`/groups` теперь редирект.
**Fix:** переадресовать ссылки на живой образец
(`app/pages/account_groups.py:_schedule_counts`) и заменить пример в
`filters.html` на существующий адрес (`/history` или
`/accounts/{id}/groups`).

### IN-03: `record_sync_failure` объявлена `async`, но ничего не ожидает

**File:** `app/application/accounts/group_resync.py:161-173`
**Issue:** Тело функции — два присваивания атрибутов ORM-объекта; ни одного
`await`. Соседний `apply_group_resync` асинхронен по делу.
**Fix:** либо сделать функцию синхронной и убрать `await` на трёх вызовах, либо
оставить как есть с однострочным комментарием «сигнатура симметрична
`apply_group_resync` намеренно».

### IN-04: Заглушка `/groups` объявляет фантомный query-параметр

**File:** `app/pages/groups.py:33-37`
**Issue:** Два декоратора на одной функции: для `@router.get("/groups")`
параметр `deep_link: str = ""` не является параметром пути, поэтому FastAPI
трактует его как query-параметр и публикует в OpenAPI. В теле функции параметр
не используется вовсе.
**Fix:** развести на два обработчика или принять путь через `Request`:
```python
@router.get("/groups")
@router.get("/groups/{deep_link:path}")
async def groups_retired() -> RedirectResponse:
    return RedirectResponse(url="/accounts", status_code=302)
```
(FastAPI не требует объявлять неиспользуемый параметр пути.)

### IN-05: У слота `caller` в `components/modal.html` нет ни одного потребителя

**File:** `app/templates/components/modal.html:22-40,74`
**Issue:** Единственным потребителем было массовое удаление групп, снесённое
планом 03-08. Сейчас возможность держится синтетическим вызовом в
`tests/test_templates/test_components.py`.
**Fix:** Решение задокументировано и обосновано в самом файле — как дефект не
классифицируется. Отмечено, чтобы попало в реестр мёртвого кода: при следующей
ревизии библиотеки компонентов слот либо получает потребителя, либо снимается.

### IN-06: Поле `is_active` формы тумблера не читается обработчиком

**File:** `app/templates/account_groups/includes/group_row.html:61`,
`app/pages/account_groups.py:322-327`
**Issue:** Чекбокс отправляется под именем `is_active`, но обработчик тела
запроса не разбирает вовсе — он инвертирует текущее значение. Значение поля не
влияет ни на что, и при двух быстрых нажатиях два POST-а дают инверсию дважды.
**Fix:** либо читать желаемое состояние из формы (`is_active` присутствует →
включить), что делает операцию идемпотентной, либо переименовать поле, чтобы
имя не обещало смысла, которого у него нет.

### IN-07: Дубли `group_external_id` внутри одного аккаунта молча выпадают из синка

**File:** `app/application/accounts/group_resync.py:95-97`
**Issue:** `existing` — словарь по `group_external_id`; при двух строках с
одинаковым внешним идентификатором в словарь попадает только последняя. Первая
никогда не переименовывается и никогда не помечается `missing_since` — она
навсегда «застывает». Источник дублей — WR-03.
**Fix:** снимается уникальным ограничением из WR-03. До него — собирать
`dict[str, list[Group]]` и обрабатывать все строки группы.

### IN-08: Подсчёт расписаний завышается при повторе идентификатора и не различает расписания

**File:** `app/pages/account_groups.py:96-106`
**Issue:** `for group_id in row.group_ids or []: counts[group_id] += 1` — если
одно расписание содержит один и тот же `group_id` дважды (список хранится
JSON-ом и уникальность не гарантирована), подпись «в 2 расписаниях» появится
при одном расписании.
**Fix:** считать по множеству идентификаторов строки:
```python
for row in rows:
    for group_id in set(row.group_ids or []):
        if group_id in counts:
            counts[group_id] += 1
```

---

_Reviewed: 2026-08-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
