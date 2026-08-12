---
phase: 03-gruppy-akkaunta
reviewed: 2026-08-12T00:00:00Z
depth: standard
files_reviewed: 58
files_reviewed_list:
  - alembic/versions/0014_sync_result_and_group_missing.py
  - alembic/versions/0015_groups_unique_account_external.py
  - app/application/accounts/dto.py
  - app/application/accounts/group_resync.py
  - app/application/scheduling/use_cases.py
  - app/main.py
  - app/messengers/base.py
  - app/messengers/max.py
  - app/messengers/telegram_user.py
  - app/messengers/whatsapp.py
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
  - tests/test_messengers/test_max.py
  - tests/test_messengers/test_telegram_user.py
  - tests/test_messengers/test_whatsapp.py
  - tests/test_migrations/test_0013_ad_status.py
  - tests/test_migrations/test_0014_sync_result_columns.py
  - tests/test_migrations/test_0015_groups_unique_account_external.py
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
  critical: 1
  warning: 5
  info: 9
  total: 15
status: issues_found
---

# Phase 03: Code Review Report (re-review after 03-REVIEW-FIX)

**Reviewed:** 2026-08-12
**Depth:** standard
**Files Reviewed:** 58
**Status:** issues_found

## Summary

Повторный проход по тем же файлам ПОСЛЕ применённых исправлений CR-01, CR-02,
WR-01…WR-05 и добавления ревизии 0015. Все шесть прежних находок проверены по
текущему содержимому файлов и подтверждены как закрытые — они здесь НЕ
повторяются:

- `MessengerFetchError` действительно поднимается всеми тремя адаптерами
  (`app/messengers/{telegram_user,whatsapp,max}.py`) и ловится
  `app/pages/accounts.py:821`;
- предохранитель вырожденного ответа стоит (`group_resync.py:218`);
- тумблер группы несёт резервную кнопку отправки (`group_row.html:76`);
- `record_sync_failure` не трогает `last_synced_at` (`group_resync.py:275`);
- уникальность `(account_id, group_external_id)` есть и в модели, и в ревизии;
- плашка массовой пропажи красится `warning` (`list.html:135-140`).

Новые находки сосредоточены вокруг ПОСЛЕДСТВИЙ этих исправлений, а не вокруг
них самих. Главная — ревизия 0015 стала единственным местом проекта, которое
удаляет строки `groups`, и она удаляет их, не переписывая ссылки на них в
`schedules.group_ids`; собственный маршрут удаления группы этой же фазы такие
ссылки чистит обязательно, и его докстринг прямо называет цену пропуска
(«тихо неполная отправка»). Ниже — она и ещё пять предупреждений: недосмотренный
путь IntegrityError, произвольный текст исключения в пользовательской плашке,
второе (расходящееся) определение полноты расписания в карточке редактора,
обрезка ключа маршрутизации и создание задачи отправки для несуществующей
группы.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Ревизия 0015 удаляет строки `groups`, но не переписывает ссылки на них в `schedules.group_ids`

**File:** `alembic/versions/0015_groups_unique_account_external.py:99-115` (обоснование — строки 18-21)
**Severity:** BLOCKER

**Issue:**
`_DROP_DUPLICATES` снимает все строки, кроме `MIN(id)` в каждой паре
`(account_id, group_external_id)`. Докстринг оправдывает выбор выжившей строки
так: «именно на неё ссылаются расписания, созданные ДО появления дубля
(`schedules.group_ids` хранится JSON-ом, и переписать эти ссылки ревизия не
может)». Оправдание закрывает только половину случаев. Расписание, созданное
или отредактированное ПОСЛЕ появления дубля, ссылается ровно на тот
идентификатор, который пользователь увидел и выбрал в списке, — а в списке видны
ОБЕ строки (это и есть описанный в том же докстринге дефект: «обе видны на
экране, обе выбираемы в расписаниях»). Значит, выбранной вполне могла оказаться
строка с бОльшим id, и ревизия её удаляет, оставляя в JSON висячий
идентификатор.

Дальше висячая ссылка ведёт себя молча и по-разному:

- `app/application/scheduling/use_cases.py:124` — `session.get(Group, group_id)`
  возвращает `None`, ветка пропуска на строке 150 не срабатывает (`if group and
  not group.is_active`), и задача ВСЁ РАВНО создаётся (строка 158);
- для `wa`/`max` блок наполнения полей закрыт условием `if group:` (строка 167),
  поэтому в Redis уезжает payload с `"group_external_id": null` и
  `"group_name": null` (`app/worker/tasks.py:97-110`, `136-149`);
- для `tg_user` `send_message_once` пишет в журнал `status="fail"`,
  `error_message="Missing ad, group, or account"`
  (`use_cases.py:212-229`) — то есть пользователь видит отказ отправки без
  единого намёка на его причину.

Итог: после однократного выката рассылка в выбранный пользователем чат
прекращается навсегда, а объяснение отсутствует. Ровно этот класс дефекта
маршрут удаления группы ЭТОЙ ЖЕ фазы считает недопустимым и потому чистит
расписания обязательно:
`app/pages/account_groups.py:343-347` — «оставленный в `Schedule.group_ids`
идентификатор удалённой строки не роняет отправку, он делает её тихо неполной»,
`:370` — `await ScheduleRepository(db).remove_group_ids(user.id, {group.id})`.
Ревизия обязана держать тот же инвариант; «ревизия не может» неверно —
переписать JSON можно и на SQLite, и на PostgreSQL, и без импорта из
`app.models`.

**Fix:**
Добавить шаг ПЕРЕД `_DROP_DUPLICATES`, который заменяет удаляемые идентификаторы
на выживший. Портируемый вариант — на стороне Python, через тот же
`op.get_bind()`:

```python
import json

_DUP_MAP = sa.text(
    """
    SELECT d.id AS dead, s.keep AS keep
    FROM groups AS d
    JOIN (
        SELECT account_id, group_external_id, MIN(id) AS keep
        FROM groups
        GROUP BY account_id, group_external_id
        HAVING COUNT(*) > 1
    ) AS s
      ON s.account_id = d.account_id
     AND s.group_external_id = d.group_external_id
    WHERE d.id <> s.keep
    """
)


def _remap_schedule_group_ids(connection) -> None:
    """Ссылки на удаляемые дубли переводятся на выжившую строку.

    `schedules.group_ids` — JSON-строка, агрегата по ней нет ни в одном из двух
    диалектов, поэтому перевод идёт построчно. Порядок сохраняется, дубликаты
    после перевода схлопываются: расписание не должно получить одну группу
    дважды и отправить в неё два сообщения.
    """
    mapping = {row.dead: row.keep for row in connection.execute(_DUP_MAP)}
    if not mapping:
        return
    rows = connection.execute(
        sa.text("SELECT id, group_ids FROM schedules WHERE group_ids IS NOT NULL")
    ).fetchall()
    for row in rows:
        raw = row.group_ids
        try:
            ids = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            continue
        if not isinstance(ids, list):
            continue
        moved, seen = [], set()
        for gid in ids:
            new = mapping.get(gid, gid)
            if new not in seen:
                seen.add(new)
                moved.append(new)
        if moved != ids:
            connection.execute(
                sa.text("UPDATE schedules SET group_ids = :v WHERE id = :i"),
                {"v": json.dumps(moved), "i": row.id},
            )


def upgrade():
    connection = op.get_bind()
    connection.execute(_MERGE_IS_ACTIVE)
    connection.execute(_MERGE_MISSING_SINCE)
    _remap_schedule_group_ids(connection)   # <-- до удаления строк
    connection.execute(_DROP_DUPLICATES)
    ...
```

Парный тест обязан быть в `tests/test_migrations/test_0015_*.py`: расписание,
ссылающееся на дубль с бОльшим id, после апгрейда ссылается на выжившего и не
содержит его дважды.

## Warnings

### WR-01: Задача отправки создаётся для группы, строки которой больше нет

**File:** `app/application/scheduling/use_cases.py:123-180`
**Severity:** WARNING

**Issue:**
```python
group = await session.get(Group, group_id)
if group and not group.is_active:
    ...
    continue
task = DispatchTask(type=account.type, ..., group_id=group_id, ...)
if account.type in ("wa", "max"):
    if group:
        ...  # заполнение group_external_id / group_name
tasks_to_dispatch.append(task)
```
`group is None` не отсеивается нигде. Для `wa`/`max` в очередь Redis попадает
задача с `group_external_id=None`; воркер получает адресата `null`. Для
`tg_user` задача доезжает до `send_message_once` и превращается в запись журнала
«Missing ad, group, or account» — то есть в отказ без причины. Ветка `if group:`
на строке 167 показывает, что автор знал о возможности `None`, но выбрал
наполнять поля условно вместо того, чтобы задачу не создавать.

Это ОТДЕЛЬНЫЙ дефект от CR-01: он делает любую висячую ссылку тихой, откуда бы
она ни взялась.

**Fix:**
```python
group = await session.get(Group, group_id)
# Строки нет — задачи нет. Отправлять в None нельзя, а «попытка», которой не
# было, не должна занимать очередь и журнал.
if group is None:
    logger.warning("group_skipped_missing", group_id=group_id, schedule_id=schedule.id)
    continue
if not group.is_active:
    logger.info("group_skipped_inactive", group_id=group_id, schedule_id=schedule.id)
    continue
```
После этого `if group:` внутри ветки `wa`/`max` становится избыточным и должен
быть снят — иначе останется два определения «группа есть».

### WR-02: Текст произвольного исключения уезжает в пользовательскую плашку

**File:** `app/pages/accounts.py:850`, `app/worker/tasks.py:358`, `app/worker/tasks.py:461`; отображается в `app/templates/account_groups/list.html:116`
**Severity:** WARNING

**Issue:**
Широкие обработчики пишут на аккаунт `str(e) or e.__class__.__name__`, и это
значение шаблон печатает пользователю дословно:
`alert('Синхронизация не удалась: ' ~ sync_result.get('error') ~ …)`.
Комментарий на `accounts.py:830` заявляет, что «пишется сообщение исключения, а
не строка подключения (T-03-17)», но это верно только для узкой ветки
`MessengerFetchError`. Широкая ветка ловит ВСЁ, включая исключения слоя данных:
после добавления `uq_groups_account_external` реальный кандидат — `IntegrityError`,
чей `str()` содержит полный SQL и значения параметров
(`… UNIQUE constraint failed: groups.account_id, groups.group_external_id
[SQL: INSERT INTO groups (user_id, account_id, …)] [parameters: (…)]`).
В `tasks.py` то же значение пишется в фоновых путях, где источником может
оказаться и `RuntimeError` менеджера контейнеров с внутренним адресом.

Раскрытие ограничено владельцем аккаунта, но это всё равно утечка деталей схемы
и внутренних адресов в UI, и она прямо противоречит объявленному правилу
T-03-17.

**Fix:** сообщение для пользователя должно быть СВОИМ, а исходный текст — только
в лог (он там уже есть, `exc_info=True`):

```python
# app/pages/accounts.py и оба фоновых пути
UNEXPECTED_SYNC_FAILURE = (
    "Синхронизация не удалась из-за внутренней ошибки — повторите попытку"
)
...
await record_sync_failure(db, account, UNEXPECTED_SYNC_FAILURE)
```
Текст `MessengerFetchError` (он формируется адаптером и подконтролен нам) можно
оставить как есть — узкая ветка выше по коду.

### WR-03: Карточка редактора запрещает ПОСТАВИТЬ НА ПАУЗУ активное неполное расписание

**File:** `app/templates/ads/includes/sched_card.html:105-108`
**Severity:** WARNING

**Issue:**
```jinja
{{ toggle(name='is_active', checked=s.is_active, id='sched-toggle-' ~ s.id,
          disabled=(not complete),
          title=('Включить нельзя: выберите аккаунт, хотя бы одну группу, день и время.'
                 if not complete else …)) }}
```
Условие недоступности — `not complete`. Два других носителя того же правила
считают иначе:

- `app/templates/schedules/includes/schedule_row.html:48`:
  `resume_blocked = not s.is_active and not complete`;
- обработчик `app/pages/schedules.py:723-729` с явным комментарием «Пауза
  активного не блокируется: право поставить на паузу не зависит от
  заполненности».

То есть карточка редактора отключает орган управления в состоянии, которое и
сервер, и второй шаблон считают полностью законным, — и подпись при этом врёт
(«Включить нельзя», когда пользователь хочет ВЫКЛЮЧИТЬ). Флажок `disabled`
браузером не отправляется и событие `change` не порождает, поэтому пути
поставить расписание на паузу из редактора нет вовсе.

Состояние «активное И неполное» — не теоретическое, и создаёт его именно эта
фаза: `POST /accounts/{id}/groups/{gid}/delete` вычищает идентификатор из
`Schedule.group_ids` (`app/pages/account_groups.py:370`), не трогая `is_active`.
Удалили единственную группу активного расписания — и оно осталось включённым,
молчащим и не выключаемым из того экрана, куда его же карточка и ведёт.

D-08 требует ОДНОГО определения полноты; здесь их два, и разошлись они ровно так,
как предупреждает докстринг `app/services/schedule_rules.py`.

**Fix:**
```jinja
{%- set resume_blocked = not s.is_active and not complete -%}
...
{{ toggle(name='is_active', checked=s.is_active, id='sched-toggle-' ~ s.id,
          disabled=resume_blocked,
          title=('Включить нельзя: выберите аккаунт, хотя бы одну группу, день и время.'
                 if resume_blocked else ('Приостановить' if s.is_active else 'Возобновить'))) }}
```
Тест-спецификация: активное расписание с пустым `group_ids` рендерит тумблер БЕЗ
`disabled` (парный к существующим в `tests/test_pages/test_editor_schedules.py`).

### WR-04: `IntegrityError` на новом ограничении не обработан — вместо плашки JSON-пятисотка

**File:** `app/pages/accounts.py:835-858`
**Severity:** WARNING

**Issue:**
Комментарий на строках 772-788 объявляет размен осознанным: «гонка заканчивается
IntegrityError на коммите одного из двух запросов». Но `await db.commit()` на
строке 858 стоит ВНЕ какого-либо `except`, поэтому исключение уходит в
`generic_error_handler` (`app/main.py:108-119`) и пользователь, отправивший
обычную HTML-форму, получает `{"detail": "Internal server error"}` — сырой JSON
вместо страницы. Хуже другое: на аккаунт при этом НИЧЕГО не записывается, то
есть у отказа не остаётся ни следа в UI. Это прямо противоречит правилу,
объявленному тем же обработчиком двадцатью строками выше (835-841): «отказ
обязан лечь сводкой на аккаунт, а не пятисоткой… сузить блок означало бы вернуть
на экран стек-трейс там, где раньше была красная плашка».

Второй, более частый триггер того же исключения — не гонка, а обрезка ключа
(см. WR-05).

**Fix:**
```python
from sqlalchemy.exc import IntegrityError

...
await apply_group_resync(db, account, fetched_groups, messenger_type=messenger_type)
try:
    await db.commit()
except IntegrityError:
    # Ограничение уровня схемы сработало — состав групп уже кто-то записал
    # (второе нажатие «Синхронизировать всё»). Откат обязателен: сессия после
    # IntegrityError непригодна ни для чего, кроме rollback.
    await db.rollback()
    structlog.get_logger().warning("sync_groups_conflict", account_id=account_id)
    account = await db.get(MessengerAccount, account_id)
    if account:
        await record_sync_failure(
            db, account, "Синхронизация уже выполнялась — откройте экран заново"
        )
        await db.commit()
return RedirectResponse(url=account_groups_url, status_code=302)
```

### WR-05: Внешний идентификатор группы молча обрезается до 255 символов

**File:** `app/application/accounts/group_resync.py:166` (обоснование — 79-90)
**Severity:** WARNING

**Issue:**
```python
external_id = str(external_id)[:_EXTERNAL_ID_MAX]
```
Для `name` (строка 174) обрезка — верное решение: «обрезанное имя чата читается
хуже полного», и цена ошибки — косметическая. Для `group_external_id` цена
другая: это КЛЮЧ МАРШРУТИЗАЦИИ, он же уходит в мессенджер при отправке
(`app/application/scheduling/use_cases.py:307`:
`group_id=group.group_external_id`). Обрезанный ключ — не «хуже читается», он
не адресует ничего: строка создаётся, показывается пользователю, выбирается им в
расписании, и каждая отправка по ней тихо проваливается.

Побочно: два разных длинных идентификатора с одинаковым 255-символьным префиксом
после обрезки становятся одним и теперь нарушают
`uq_groups_account_external` — то есть роняют весь синк аккаунта именно тем
`IntegrityError`, который не обработан (WR-04).

Модуль уже умеет правильную реакцию на негодный элемент — пропуск (строки
161-165, 167-170): «мусорный ЭЛЕМЕНТ не роняет весь синк… стоит пропуска одной
группы». Идентификатор длиннее колонки — ровно такой элемент.

**Fix:**
```python
raw_external_id = str(external_id)
if len(raw_external_id) > _EXTERNAL_ID_MAX:
    # Ключ маршрутизации обрезать нельзя: обрезанный адресует не тот чат или не
    # адресует ничего. Пропуск ОДНОЙ группы честнее строки-призрака, по которой
    # отправка будет молча проваливаться. Границу не проходит ни один реальный
    # идентификатор трёх поддержанных мессенджеров.
    continue
external_id = raw_external_id
```
(обрезку `name` оставить как есть — там аргумент докстринга верен).

## Info

### IN-01: Мёртвые импорты в `app/worker/tasks.py`

**File:** `app/worker/tasks.py:7, 9, 16, 21, 22`
**Severity:** Info
**Issue:** после переноса логики в `app/application/scheduling/use_cases.py` не
используются `select`, `joinedload`, `Schedule`, `get_image_url`,
`compute_next_run_at`. Находка переносится из прошлого прохода (IN-01) — в
`03-REVIEW-FIX.md` она попала в «Skipped», в коде осталась.
**Fix:** удалить пять строк импорта.

### IN-02: `record_sync_failure` объявлена `async`, но ничего не ожидает

**File:** `app/application/accounts/group_resync.py:253-277`
**Severity:** Info
**Issue:** тело — одно присваивание; `async` вынуждает всех вызывающих ставить
`await` и создаёт впечатление обращения к БД, которого нет. Переносится из
прошлого прохода (IN-03).
**Fix:** оставить `async` ради симметрии с `apply_group_resync` можно, но тогда
это должно быть сказано в докстринге явно; иначе — сделать обычной функцией и
снять `await` в трёх точках вызова.

### IN-03: Заглушка `/groups` объявляет параметр, которым не пользуется

**File:** `app/pages/groups.py:35`
**Severity:** Info
**Issue:** `async def groups_retired(deep_link: str = "")` — значение не читается
(и не должно: докстринг требует безусловного перенаправления). Параметр нужен
только чтобы FastAPI принял `{deep_link:path}`. Переносится из прошлого прохода
(IN-04).
**Fix:** оставить, но назвать причину в сигнатуре комментарием — иначе первый же
линтер «неиспользуемый аргумент» предложит его снять и сломает маршрут.

### IN-04: «Все группы удалены» показывается аккаунту, у которого групп никогда не было

**File:** `app/templates/account_groups/list.html:208-210`
**Severity:** Info
**Issue:** ветки пустого состояния различаются по `account.last_synced_at`.
Успешный синк, законно вернувший ноль групп (аккаунт без единого чата), ставит
`last_synced_at` (`group_resync.py:248`) — и пользователь читает утверждение
«Все группы удалены», которого не было. Докстринг `record_sync_failure`
(строки 268-271) называет именно этот класс вранья причиной не трогать колонку
при отказе — но случай «синк удался, групп ноль» тем исправлением не покрыт.
**Fix:** различать по сводке, а не только по времени: `sync_result.found == 0 and
sync_result.new == 0` при `missing == 0` означает «групп нет», а не «все
удалены».

### IN-05: `SyncStatusView.group_count` считается запросом и никогда не используется

**File:** `app/application/accounts/use_cases.py:54-62`, потребитель — `app/templates/accounts/partials/sync_status_card.html:52`
**Severity:** Info
**Issue:** шаблон читает `stats.get('groups_count', group_count or 0)`, а
`_get_account_stats` (`app/pages/accounts.py:104-111`) кладёт ключ
`groups_count` для КАЖДОГО запрошенного аккаунта — значит второй аргумент
`get` недостижим. При этом `get_sync_status_view` ради него выполняет
`SELECT Group.id …` и считает длину в Python на каждом ответе опроса (раз в
5 секунд на вкладку).
**Fix:** убрать `group_count` из `SyncStatusView` и второй аргумент из
`stats.get(...)`, либо — если поле нужно — перестать дублировать подсчёт в
`_get_account_stats`.

### IN-06: `_sync_wa_groups_async` и `_sync_max_groups_async` — посимвольные копии

**File:** `app/worker/tasks.py:272-366` и `379-469`
**Severity:** Info
**Issue:** различаются классом адаптера, литералом `messenger_type` и текстами
логов; остальные ~90 строк (опрос, три ветки состояния, таймаут, обработчик
исключения) дублированы. Это ровно тот дефект, ради устранения которого заведён
`group_resync` («однажды поправят две из трёх», докстринг модуля) — просто на
уровень выше.
**Fix:** один `_sync_groups_async(account_id, messenger_type, messenger_factory)`
и две трёхстрочные обёртки-таски.

### IN-07: У слота `caller` в `components/modal.html` нет ни одного продуктового потребителя

**File:** `app/templates/components/modal.html:74`
**Severity:** Info
**Issue:** единственный блочный вызов в продукте —
`ads/includes/sched_card.html:238-247` (скрытое `return_to`), заведён же слот был
под массовое удаление групп, снятое планом 03-08. Докстринг это признаёт.
Переносится из прошлого прохода (IN-05) с уточнением: потребитель ОДИН, а не
ноль, поэтому удалять слот нельзя.
**Fix:** поправить докстринг (строки 33-36) — утверждение «ПОТРЕБИТЕЛЯ у слота
сегодня нет ни одного» неверно и уведёт следующего читателя.

### IN-08: `ADD CONSTRAINT` ревизии 0015 берёт исключительную блокировку — вразрез с дисциплиной 0014

**File:** `alembic/versions/0015_groups_unique_account_external.py:117-120`
**Severity:** Info
**Issue:** ревизия 0014 отдельно объясняет, почему в ней нет ни одного
переписывания строк («не держит долгую блокировку»). 0015 в той же истории
делает `UPDATE`, `DELETE` и `ALTER TABLE … ADD CONSTRAINT UNIQUE`: последний на
PostgreSQL строит уникальный индекс под `ACCESS EXCLUSIVE`. На сегодняшнем
размере таблицы это неощутимо, но заявленная дисциплина нарушена молча.
**Fix:** либо назвать размен в докстринге, либо (для больших таблиц)
`CREATE UNIQUE INDEX CONCURRENTLY` + `ADD CONSTRAINT … USING INDEX` в отдельной
ревизии без транзакции.

### IN-09: Проверка владения в `apply_group_resync` шире ограничения схемы

**File:** `app/application/accounts/group_resync.py:142-150`
**Severity:** Info
**Issue:** словарь существующих групп строится по `account_id AND user_id`, а
`uq_groups_account_external` скоупится только по `account_id`. Строка, чей
`user_id` разошёлся с владельцем аккаунта (миграция данных, ручная правка), в
словарь не попадёт, будет вставлена заново и упрётся в ограничение — то есть
защитное условие превращает безобидное расхождение в отказ всего синка. Тест
`test_same_external_id_in_another_account_survives` этот случай не покрывает: там
разные `account_id`.
**Fix:** либо снять условие по `user_id` (владение уже проверено вызывающими и
скоупом `account_id`), либо расширить ограничение до
`(user_id, account_id, group_external_id)` — но тогда оно перестанет закрывать
исходную гонку.

---

_Reviewed: 2026-08-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
