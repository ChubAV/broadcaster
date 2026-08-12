---
phase: 03-gruppy-akkaunta
plan: 04
subsystem: backend
tags: [sync, celery, pages, resync, tdd]

# Dependency graph
requires:
  - phase: 03-02
    provides: "apply_group_resync, record_sync_failure и колонки результата синка"
  - phase: 03-01
    provides: "Экран /accounts/{id}/groups — адрес, на который теперь ведут редиректы синка"
provides:
  - "Единственная логика состава групп на все три пути синхронизации: собственной в accounts.py и tasks.py не осталось"
  - "Результат и время последнего синка записываются во всех трёх путях"
  - "Провал синка (отказ мессенджера, отказ моста, исчерпание попыток, исключение) записывается текстом ошибки"
  - "Редиректы синхронизации ведут на экран групп аккаунта вместо сносимого раздела /groups"
affects:
  - "03-06: экран групп читает last_synced_at и last_sync_result, заполняемые этими тремя путями"
  - "03-05: экран групп аккаунта — цель редиректов синка и повторного запуска"

actuals:
  tokens: 51000
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Отказ внешней системы оборачивается вокруг ВЕТОК получения групп, а не вокруг одного вызова: состав и порядок обращений к мессенджеру остаётся посимвольно прежним, а исключение перестаёт быть 500-й"
    - "Симметрия двух копий проверяется одним параметризованным набором тестов: расхождение WA- и MAX-путей падает тестом, а не обнаруживается в проде"
    - "Тест прохибиции усиливается утверждением о счётчике: без «группа была увидена» он зеленел бы и на пути, который до неё не дошёл"
    - "Текст провала для пользователя собирается двумя общими функциями (_bridge_failure_message, _sync_timeout_message) — две копии не могут разойтись формулировкой"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - app/worker/tasks.py
    - tests/test_routes/test_sync_groups.py
    - tests/test_worker/test_tasks.py

key-decisions:
  - "Неразрешимый account_id уводит на /accounts, всё остальное — на /accounts/{id}/groups: адрес несуществующего экрана предлагать нечему"
  - "Финальный редирект повторного запуска (retry-sync) тоже переведён на экран групп аккаунта — кнопку нажимают оттуда"
  - "Ветка «аккаунт не найден» и ветка «неподходящий тип» разделены: у второй аккаунт существует, и ей есть куда вернуть пользователя"
  - "try оборачивает все три ветки получения групп целиком, а не вынесенный общий вызов get_groups() — так конструкторы мессенджеров и порядок вызовов остаются нетронутыми"
  - "test_sync_groups_skips_existing переведён на D-11: он утверждал заморозку имени существующей группы — поведение, которое фаза сознательно меняет"

requirements-completed: [GRP-07]

# Metrics
duration: 40min
completed: 2026-08-12
status: complete
---

# Phase 03 Plan 04: Три пути синхронизации через один хелпер — Summary

**Три копии логики состава групп сведены к трём вызовам `apply_group_resync`; результат и время синка впервые записываются во всех трёх путях, провал синка перестал быть безмолвным, а редиректы обработчиков ведут на экран групп того аккаунта, с которым работал пользователь.**

---

## Что построено

| Артефакт | Содержание |
|---|---|
| `app/pages/accounts.py` — `accounts_sync_groups` | Встроенный блок only-add заменён вызовом хелпера; отказ `get_groups()` пишется `record_sync_failure`; четыре редиректа ведут на `/accounts/{id}/groups` |
| `app/pages/accounts.py` — `accounts_retry_sync` | Финальный редирект повторного запуска ведёт туда же |
| `app/worker/tasks.py` — `_sync_wa_groups_async` | Состав групп через хелпер; три ветки отказа пишут результат |
| `app/worker/tasks.py` — `_sync_max_groups_async` | То же самое, тем же хелпером — обе функции обработаны идентично |
| `_bridge_failure_message` / `_sync_timeout_message` | Тексты провала, общие на оба фоновых пути |

---

## Task 1 — TG-путь и редиректы (TDD)

**RED** (`500ac43`): девять падающих тестов в `tests/test_routes/test_sync_groups.py`.

Один тест на первом прогоне **прошёл ошибочно** — `test_sync_keeps_disabled_group_disabled`. Причина: старый путь был «добавить только новые», существующую строку он вообще не трогал, поэтому выключенность сохранялась сама собой, и тест зеленел бы на пути, который до группы не дошёл. Усилен утверждением о сводке (`found == 1`, `new == 0`): теперь он требует, чтобы группа была именно УВИДЕНА синком и при этом не переключена. После правки — 9 падений из 9.

**GREEN** (`ee546c9`):

```python
try:
    if account.type == "tg_user":
        messenger = TelegramUserMessenger(...)
        fetched_groups = await messenger.get_groups()
        messenger_type = "tg_user"
    elif ...            # ветки wa и max без изменений
except Exception as e:
    await record_sync_failure(db, account, str(e) or e.__class__.__name__)
    await db.commit()
    return RedirectResponse(url=account_groups_url, status_code=302)

await apply_group_resync(db, account, fetched_groups, messenger_type=messenger_type)
await db.commit()
```

`try` обёрнут вокруг **веток целиком**, а не вокруг вынесенного общего `get_groups()`. Вынос выглядел короче, но менял состав и порядок обращений к мессенджеру — жёсткая рамка milestone. В нынешнем виде `MockMessenger.assert_called_once_with(session_string=…, api_id=…, api_hash=…)` двух существующих тестов проходит без правки, что и есть доказательство неизменности протокола.

### Редиректы

| Ветка | Было | Стало |
|---|---|---|
| Аккаунт не разрешён в собственный | `/groups` | `/accounts` |
| Тип аккаунта неподходящий | `/groups` | `/accounts/{id}/groups` |
| Guard `syncing` | `/groups` | `/accounts/{id}/groups` |
| Успех синка | `/groups` | `/accounts/{id}/groups` |
| Повторный запуск (`retry-sync`) | `/accounts` | `/accounts/{id}/groups` |

Ветка `if not account or account.type not in (...)` разделена надвое: у «неподходящего типа» аккаунт существует, и ему есть куда вернуть пользователя, а у неразрешимого `account_id` — нет.

| Критерий | Результат |
|---|---|
| `grep -c 'apply_group_resync' app/pages/accounts.py` | **2** |
| `grep -v '^ *#' … \| grep -c 'RedirectResponse(url="/groups"'` | **0** |
| `grep -c 'accounts/{account_id}/groups' app/pages/accounts.py` | **2** (≥1) |
| `grep -v '^ *#' … \| grep -c 'existing_ids = '` | **0** |
| `uv run pytest tests/test_routes/test_sync_groups.py -q` | **12 passed** |
| `uv run pytest tests/test_routes/ tests/test_pages/ -q --ignore=tests/test_pages/test_account_groups.py` | **561 passed** |

Флаг исключения `test_account_groups.py` не снимался: файл дописывает план 03-05 той же волны.

---

## Task 2 — фоновые синки WA и MAX (TDD)

**RED** (`ecae458`): один параметризованный набор на оба пути — 12 падений (`[wa]` и `[max]` каждого сценария), 2 прохода на регрессии существующего guard-а.

Симметрия закреплена конструкцией теста, а не дисциплиной: `SYNC_PATHS` подставляет в один и тот же сценарий `_sync_wa_groups_async` + `app.messengers.whatsapp.WhatsAppMessenger` и `_sync_max_groups_async` + `app.messengers.max.MaxMessenger`. Расхождение копий даёт падение половины параметризации.

**GREEN** (`131622e`): обе функции получили идентичную правку.

```python
result = await apply_group_resync(session, account, groups, messenger_type="wa")  # "max"
account.status = "active"
await session.commit()
log.info("sync_complete", total_groups=len(groups), new_groups=result.created,
         renamed_groups=result.renamed, missing_groups=result.missing)
```

Три ветки отказа — состояние моста (`failed`/`not_found`/`unknown`), исчерпание попыток опроса и перехват исключения — дополнены `record_sync_failure` перед переводом в `sync_failed`. До правки экран не смог бы показать причину провала: колонка оставалась пустой при явно неуспешном синке.

Протоколы опроса не тронуты: `POLL_INTERVAL = 15`, `MAX_POLLS = 40`, набор распознаваемых состояний и имена Celery-задач прежние. Правка касается ровно того участка, где ответ моста превращается в строки таблицы.

| Критерий | Результат |
|---|---|
| `grep -c 'apply_group_resync' app/worker/tasks.py` | **3** (≥2: импорт + два вызова) |
| `grep -c 'record_sync_failure' app/worker/tasks.py` | **7** (≥2: импорт + шесть веток отказа) |
| `grep -v '^ *#' … \| grep -c 'existing_ids = '` | **0** |
| WA и MAX на одинаковом сценарии | ✅ одинаковые счётчики и состояние строк — параметризация зелена целиком |
| Отказ моста → `sync_failed` + непустой текст | ✅ `test_background_sync_failed_state_records_error[wa/max]` |
| Выключенная группа остаётся выключенной | ✅ `test_background_sync_keeps_disabled_group_disabled[wa/max]` |
| `uv run pytest tests/test_worker/test_tasks.py -q` | **22 passed** |
| `uv run pytest tests/test_worker/ tests/test_worker_tasks.py tests/test_application/ -q` | **105 passed** |

---

## Отклонения от плана

### 1. [Rule 1 — Bug] `test_sync_keeps_disabled_group_disabled` проходил в фазе RED

- **Найдено:** на первом прогоне RED (до реализации), 8 падений из 9 ожидаемых
- **Проблема:** прохибиция D-11 «синк не трогает включённость» выполнялась и старым кодом, но по другой причине — путь only-add до существующей строки просто не доходил. Тест был зелёным при любом поведении хелпера.
- **Исправление:** добавлено утверждение о сводке (`found == 1`, `new == 0`) — группа обязана быть увидена синком. Тест стал настоящим RED и остаётся регрессией на прохибицию.
- **Файл:** `tests/test_routes/test_sync_groups.py` (правка внутри того же RED-коммита `500ac43`)

### 2. [Rule 1 — Bug] Существующий тест утверждал поведение, отменённое D-11

- **Найдено:** на первом прогоне RED
- **Проблема:** `test_sync_groups_skips_existing` содержал `assert groups[0].name == "Existing Group A"` — заморозку имени существующей группы при том, что ответ мессенджера нёс новое имя. Это ровно то поведение, которое фаза меняет (D-11: синк обновляет имена).
- **Исправление:** утверждение переведено на новое поведение — имя обновляется, второй строки не появляется. Проверка отсутствия дубликата (собственно «skips existing») сохранена, имя теста не менялось.
- **Файл:** `tests/test_routes/test_sync_groups.py`, коммит `500ac43`

**Итого отклонений:** 2, оба Rule 1, оба внутри тестов. Ни одно не расширяет объём плана и не меняет решений D-10/D-11/D-12.

---

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_routes/test_sync_groups.py -q` | ✅ 12 passed |
| `uv run pytest tests/test_worker/test_tasks.py -q` | ✅ 22 passed |
| `uv run pytest tests/test_routes/ tests/test_pages/ -q --ignore=…test_account_groups.py` | ✅ 561 passed |
| `uv run pytest tests/test_worker/ tests/test_worker_tasks.py tests/test_application/ -q` | ✅ 105 passed |
| `uv run pytest tests/ -q` — суита не деградировала | ✅ **978 passed, 0 failed** |
| Собственной логики состава групп в `accounts.py` и `tasks.py` не осталось | ✅ `existing_ids = ` — 0 вхождений в обоих файлах |
| Протоколы мессенджеров не изменены | ✅ существующие `assert_called_once_with` конструкторов проходят без правки; интервал/предел/состояния/имена задач прежние |

**О прогоне полной суиты.** Первый прогон шёл с флагом `-p no:logging` и дал `978 passed, 4 errors`. Все четыре ошибки — в `tests/test_messengers/`, у тестов, запрашивающих фикстуру `caplog`, которую этот флаг и отключает. Артефакт способа запуска, а не регрессия: `uv run pytest tests/test_messengers/ -q` без флага — **56 passed**. Настоящий счёт зелёных — 982.

---

## Success criteria

| Критерий | Результат |
|---|---|
| GRP-07 (серверная половина): переинвентаризация и сохранение результата для всех трёх типов аккаунта | ✅ три вызова одного хелпера, результат пишется в каждом |
| D-09, D-10, D-11, D-12 реализованы во всех трёх путях | ✅ по одному набору тестов на страничный путь и по параметризованному — на оба фоновых |
| Протоколы отправки и синхронизации не изменены | ✅ см. Verification |

---

## Known Stubs

Отсутствуют. Оба обработчика и обе фоновые задачи переведены на хелпер полностью; TODO, пустых веток и заглушенных значений план не оставил.

Не является заглушкой, но подлежит учёту: **записанный результат синка пока никто не показывает.** Плашку сводки и подпись «не найдена при синке» рисует план 03-06 — так и задумано последовательностью: значение начинают писать до того, как его начнут читать.

---

## Threat Flags

Новых поверхностей вне `<threat_model>` плана не появилось. Диспозиции `mitigate`:

| Угроза | Реализация |
|---|---|
| T-03-14 (владение при синке) | Проверка `MessengerAccount.id == account_id AND user_id == user.id` сохранена без изменений; хелпер дополнительно скоупит выборку по `account.user_id`. Закреплено `test_sync_foreign_account_changes_nothing`: чужой `account_id` не конструирует мессенджера, не создаёт групп и не пишет результата |
| T-03-15 (повторный запуск) | Guard `account.status == "syncing"` сохранён; `test_sync_while_syncing_does_not_touch_messenger` утверждает `MockMessenger.assert_not_called()` и незаполненные колонки результата |
| T-03-16 (ответ моста как источник состава) | Строк не удаляется и `is_active` не переписывается ни в одном из трёх путей — свойство хелпера, закреплённое тестами «пропавшая остаётся» и «выключенная остаётся выключенной» в обоих фоновых путях и в страничном |
| T-03-17 (текст ошибки в результате) | Записывается сообщение исключения либо собранная фраза о состоянии моста; строка подключения и учётные данные в `last_sync_result` не попадают |
| T-03-18 (расхождение WA и MAX) | Один параметризованный набор на оба пути: расхождение даёт падение половины параметризации |

---

## Next Phase Readiness

- План 03-06 получает заполняемые колонки: `last_synced_at` и `last_sync_result` теперь пишутся всеми тремя путями, включая провальные, — плашке есть что показать и при неуспехе.
- План 03-05 получает адрес назначения: после синхронизации и повторного запуска пользователь приходит на `/accounts/{id}/groups`, а не в сносимый раздел.
- Раздел `/groups` этим планом не сносится — редиректов на него из `app/pages/accounts.py` больше нет, но сам снос остаётся за планом фазы, которому он поручен.

---

## Self-Check: PASSED

Проверено на диске и в git, а не по памяти:

**Файлы изменены** — все четыре присутствуют в `git diff --stat cdb09db..HEAD`: `app/pages/accounts.py`, `app/worker/tasks.py`, `tests/test_routes/test_sync_groups.py`, `tests/test_worker/test_tasks.py`.

**Коммиты существуют** — `500ac43`, `ee546c9`, `ecae458`, `131622e` присутствуют в `git log`.

**Удалений файлов нет** — ни один коммит плана не содержит удалённых файлов.

**Общие артефакты не тронуты** — `STATE.md` и `ROADMAP.md` этим планом не изменялись (worktree-режим, запись за оркестратором).

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-12*
