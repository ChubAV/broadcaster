---
phase: quick-260826-jql-telegram-resolve-peer
verified: 2026-08-26T14:57:01Z
status: human_needed
score: 10/10 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Отправить в боевом окружении объявление с ОДНОЙ картинкой в реальную Telegram-группу"
    expected: "Сообщение уходит; `messages.uploadMedia` не вызывается и 400 PEER_ID_INVALID не возникает"
    why_human: "400 PEER_ID_INVALID приходит от живого сервера Telegram, которого в тестах нет. Фикстура подменяет клиент на AsyncMock — голое число там проходит молча, поэтому юнит-тесты закрепляют ФОРМУ запроса, но не факт доставки."
  - test: "Отправить объявление в группу, из которой аккаунт удалён, и открыть историю отправок"
    expected: "В истории стоит русский текст «Аккаунт больше не имеет доступа к этой группе — пересинхронизируйте группы аккаунта.», а не английская строка telethon; повторов отправки нет"
    why_human: "Требует живого сервера Telegram и реальной группы с потерянным доступом. Записано в `.planning/WINDOWS.md` как запись 10 (`kind: unrun-verify`, `status: open`) и в SUMMARY как покрытие D5 с `human_judgment: true`."
---

# Quick 260826-jql: разрешение peer перед отправкой в Telegram — Verification Report

**Задача:** Telegram: разрешать peer перед отправкой картинок (PeerIdInvalidError на UploadMediaRequest)
**Verified:** 2026-08-26T14:57:01Z
**Status:** human_needed
**Re-verification:** No — initial verification
**Diff base:** `e953f2c` → `HEAD` (`bf2a6b5`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Во ВСЕ ТРИ точки отправки уходит разрешённая сущность, а не `int(group_id)` | ✓ VERIFIED | `app/messengers/telegram_user.py:296` `send_file(peer, payload, …)`, `:305` откат после `ForbiddenError` `send_message(peer, text)`, `:307` текстовая ветка `send_message(peer, text)`. `git diff e953f2c..HEAD` удаляет ровно три строки с `int(group_id)` и ни одной сверх. `grep -n "int(group_id)"` по файлу — единственное попадание на `:248` внутри `_resolve_peer`. Три теста сравнивают адресата через `is` с объектом подменённого `get_input_entity` (`:181`, `:200`, `:227` в тестах) — все зелёные. |
| 2 | Peer разрешается РОВНО ОДИН РАЗ за вызов `send_message`, до ветвления | ✓ VERIFIED | Единственный вызов `self._resolve_peer(group_id)` в файле — `telegram_user.py:262`, сразу после `await self.client.connect()` и ДО `if images:` (`:263`). Внутри веток вызовов разрешения нет. |
| 3 | Холодный кэш прогревается `get_dialogs()` ровно один раз, повторная попытка ровно одна; второго прогрева и третьей попытки нет ни на одной ветке | ✓ VERIFIED (behavioral) | `_resolve_peer` (`:227-256`): один `except ValueError` → один `await self.client.get_dialogs()` → один повторный `get_input_entity` → `raise PeerUnreachableError`. Поведенчески закреплено на ОБЕИХ ветках: `test_a_cold_entity_cache_is_warmed_exactly_once` (успех: `get_dialogs.await_count == 1`, `get_input_entity.await_count == 2`) и `test_a_peer_that_stays_unresolved_reads_as_a_lost_group` (отказ: `get_dialogs.await_count == 1`) — оба зелёные в прогоне верификатора. |
| 4 | Одна картинка уходит одиночным файлом, две и более — списком | ✓ VERIFIED | `telegram_user.py:294` `payload = files[0] if len(files) == 1 else files`. Граница закреплена на самой границе: `test_send_message_with_image` (`assert not isinstance(sent, list)`), `test_two_images_still_go_as_an_album` (`len(sent) == 2`), `test_send_message_with_multiple_images` (3) — все три собираются и зелёные. |
| 5 | `PeerIdInvalidError` ловится ОТДЕЛЬНОЙ веткой выше catch-all → `ok=False`, `no_retry=True`, константа | ✓ VERIFIED | `telegram_user.py:310` `except (PeerIdInvalidError, PeerUnreachableError) as e:` — между веткой запретов (`:306`) и `except Exception` (`:325`). Возврат `{"ok": False, "error": PEER_UNREACHABLE_MESSAGE, "no_retry": True}`. Достижимость ветки проверена независимо: `PeerIdInvalidError.__mro__ = [PeerIdInvalidError, BadRequestError, RPCError, Exception, …]`, `issubclass(PeerIdInvalidError, ForbiddenError) is False` — вышестоящая ветка запретов её не перехватывает. |
| 6 | Окончательный провал разрешения (`ValueError` после прогрева) даёт ТОТ ЖЕ ответ | ✓ VERIFIED (behavioral) | `_resolve_peer:256` `raise PeerUnreachableError(PEER_UNREACHABLE_MESSAGE) from e`; тип перечислен в той же ветке `except`, что и `PeerIdInvalidError`. `test_a_peer_that_stays_unresolved_reads_as_a_lost_group` утверждает `ok is False`, `no_retry is True`, `error == PEER_UNREACHABLE_MESSAGE` и `send_message.assert_not_awaited()` — зелёный. |
| 7 | Ни одна ветка потери доступа не отдаёт наружу английский текст telethon: `error` РАВЕН константе целиком | ✓ VERIFIED | Обе ветки возвращают модульную константу, а не `str(e)`; `str(e)` уходит только в `self.log.warning("send_peer_invalid", …)`. `test_peer_id_invalid_is_not_reported_to_the_user_in_english` утверждает равенство константе И отсутствие подстроки `"Peer"` — зелёный. |
| 8 | `get_groups`, `get_group_details`, `check_connection`, блок QR-авторизации не тронуты; `use_cases.py` и `schedule_rules.py` не изменены ни байтом | ✓ VERIFIED | `git diff --name-only e953f2c..HEAD` (весь диапазон, без ограничения путей) даёт РОВНО два файла: `app/messengers/telegram_user.py`, `tests/test_messengers/test_telegram_user.py`. Хунки адаптера: `@@ -9,6` (импорт), `@@ -190,6` (константа + исключение), `@@ -198,9`, `@@ -215,9`, `@@ -225,9`, `@@ -235,6` — все внутри `__init__`/`send_message`; `get_groups` (исходная строка 248), `check_connection`, `get_group_details` и весь QR-блок (`:54-190`) вне хунков. |
| 9 | Автопересинхронизация и автодеактивация группы НЕ введены | ✓ VERIFIED | `grep -n "sync\|deactivate\|is_active\|resync"` по `telegram_user.py` — ни одного попадания в теле адаптера. Изменения состояния группы в файле нет; `group.last_error` упоминается только текстом комментария. |
| 10 | Прицельный набор зелёный (базовая линия 88) | ✓ VERIFIED | Прогнан верификатором: `uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q` → **95 passed, 35 warnings in 24.52s**. Заявленное SUMMARY число подтверждено независимым прогоном; прирост 88 → 95 = 7 новых тестов. |

**Score:** 10/10 truths verified (0 present, behavior-unverified)

### Дополнительная проверка по запросу оркестратора

| Проверка | Статус | Доказательство |
|---|---|---|
| Негодный `group_id` НЕ выдаётся за потерю доступа | ✓ VERIFIED (behavioral) | `peer_id = int(group_id)` стоит ВНЕ `try` (`:248`), поэтому `ValueError` из `int()` не перехватывается `except ValueError` метода. Исполнено верификатором с `group_id="not-a-number"`: результат `{'ok': False, 'error': "invalid literal for int() with base 10: 'not-a-number'", 'no_retry': True}` — текст НЕ равен `PEER_UNREACHABLE_MESSAGE`, `get_dialogs` не вызван ни разу (тяжёлый запрос не потрачен), отправка не предпринята. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `app/messengers/telegram_user.py` | `PEER_UNREACHABLE_MESSAGE`, `PeerUnreachableError`, `TelegramUserMessenger._resolve_peer` | ✓ VERIFIED | Все три символа импортируются и используются. Константа — `:201-204` (текст содержит «пересинхронизируйте»), исключение — `:207-218` с содержательным русским докстрингом о ПРИЧИНЕ, метод — `:227-256`. Не стаб: докстринги плотные, разбор причины из `<objective>` воспроизведён своими словами, комментарии называют причину, а не действие. |
| `tests/test_messengers/test_telegram_user.py` | восемь затронутых тестов (6 новых по задаче 1, 1 новый по границе картинок, 1 переписанный) | ✓ VERIFIED | Сбор по `-k "resolved_peer or warmed_exactly_once or stays_unresolved or in_english"` → ровно **6**; по `-k "with_image or two_images or multiple_images"` → ровно **3**. Файл целиком 23 теста (16 существующих + 7 новых). Утверждения содержательные: адресат сверяется через `is`, а не «не число». |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `_resolve_peer(group_id)` | три точки отправки | `peer` | ✓ WIRED | `:262` → `:296`, `:305`, `:307`. Ни одна точка не осталась с голым числом; `int(group_id)` в теле `send_message` отсутствует. |
| `get_input_entity` → `ValueError` | повторная попытка | один `get_dialogs()` | ✓ WIRED | Прогрев живёт ВНУТРИ `_resolve_peer`, вызываемого один раз за отправку; переноса в точки отправки нет. |
| `PeerUnreachableError` + `PeerIdInvalidError` | `PEER_UNREACHABLE_MESSAGE` | одна ветка `except` | ✓ WIRED | `:310` — оба типа в одном кортеже, один возврат. Разъехаться исходы не могут по построению. |
| `result["error"]` | `group.last_error` / `SendLog` → экран истории | `use_cases.py` | ✓ WIRED | `app/application/scheduling/use_cases.py:481-484`: `if not result.get("ok")` → `error = result.get("error")` → `if result.get("no_retry"): group.last_error = error`. Ссылка в комментарии адаптера (`:196`) указывает на `:484` — она верна (правка `731080c` исправила ошибочную `:483` из текста плана). |
| `len(files) == 1` | одиночный файл → `messages.sendMedia` | `payload` | ✓ WIRED | `:294`; регрессия на ДВЕ картинки заведена отдельно от теста на три. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Прицельный набор тестов | `uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q` | `95 passed in 24.52s` | ✓ PASS |
| Сбор шести регрессий задачи 1 | `pytest --collect-only -q -k "resolved_peer or warmed_exactly_once or stays_unresolved or in_english"` | `6` | ✓ PASS |
| Сбор трёх тестов границы картинок | `pytest --collect-only -q -k "with_image or two_images or multiple_images"` | `3` | ✓ PASS |
| Ветка `PeerIdInvalidError` достижима (не перехвачена веткой запретов) | `python -c "issubclass(PeerIdInvalidError, ForbiddenError)"` | `False`, MRO через `BadRequestError` | ✓ PASS |
| Негодный `group_id` не выдаётся за потерю доступа | скрипт с `AsyncMock`, `send_message("not-a-number", "hi")` | `error != PEER_UNREACHABLE_MESSAGE`, `get_dialogs.await_count == 0` | ✓ PASS |
| Коммиты задачи существуют в истории | `git log -1 --format=%s <hash>` × 5 | `d45ffb5` test → `f031c40` feat → `f57088e` test → `7202ecd` feat → `731080c` docs | ✓ PASS |
| Границы диффа | `git diff --name-only e953f2c..HEAD` | ровно 2 файла плана | ✓ PASS |
| Боевая отправка (одна картинка / потеря доступа) | требует живого Telegram | — | ? SKIP → человек |

### Probe Execution

Проектных probe-скриптов (`scripts/*/tests/probe-*.sh`) в репозитории нет; ни PLAN, ни SUMMARY их не объявляют. Шаг не применим.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| QUICK-TG-RESOLVE-PEER | `260826-jql-PLAN.md` | Разрешать peer перед отправкой картинок в Telegram; недоступная группа сообщает о себе по-русски и без повторов | ✓ SATISFIED (частично требует боевой приёмки) | Истины 1-10 закрыты; покрытие D1-D4 подтверждено независимым прогоном тестов. D5 (боевая доставка) остаётся за человеком. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TODO` / `FIXME` / `XXX` / `HACK` / `PLACEHOLDER` | — | Ни одного попадания в обоих правленых файлах. Долговых маркеров задача не оставила. |
| `graphify-out/graph.json` | — | Граф проекта не перестроен в рабочем дереве | ⚠️ Warning | SUMMARY утверждает «`graphify update .` отработал (12439 узлов, 23828 рёбер)», но `graphify-out/graph.json` в основном дереве датирован `Aug 26 06:21`, тогда как `app/messengers/telegram_user.py` закоммичен в `14:47`. Исполнитель работал в снятом с тех пор worktree (`bf2a6b5 chore: merge executor worktree …`), и обновлённый граф уехал вместе с ним; `graphify-out/` в `.gitignore` и с мержем не пришёл. На цель задачи не влияет — граф это навигационный артефакт, — но правило `CLAUDE.md` о свежести графа в рабочем дереве сейчас не выполнено. Лечится одним прогоном `graphify update .`. |

### Notes (info, не гэпы)

- **Негодный `group_id` показывает пользователю английский `str(e)`.** Это не регрессия и не выход за границы: ветка catch-all существовала до задачи, а плановое решение сознательно НЕ расширяет ветку потери доступа до `except ValueError` — иначе негодный идентификатор советовал бы «пересинхронизировать группы», что не помогло бы. Поведение проверено (см. выше) и соответствует замыслу.
- **Тесты проверены на способность краснеть косвенно.** SUMMARY описывает мутационную проверку каждой из трёх точек отправки; независимо подтверждено, что утверждения написаны через `is` с объектом подменённого `get_input_entity`, то есть на голом числе они действительно краснеют (сравнение «не число» было бы зелёным и на сломанном коде — этой ошибки в тестах нет).
- **Внешние утверждения о telethon подтверждены на месте:** `PeerIdInvalidError` наследует `BadRequestError`, а не `ForbiddenError` — порядок веток `except` действительно безразличен, как и сказано комментарием в коде.

### Human Verification Required

Оба пункта требуют живого сервера Telegram и в этом окружении неисполнимы по существу, а не по недосмотру. Зафиксированы в `.planning/WINDOWS.md` записью **10** (`kind: unrun-verify`, `phase: quick-260826-jql`, `status: open`, `recorded_at: 2026-08-26T14:50:52.666Z`) — проверено верификатором в файле.

#### 1. Боевая отправка объявления с ОДНОЙ картинкой

**Test:** Отправить в боевом окружении объявление с одной картинкой в реальную Telegram-группу, куда аккаунт входит.
**Expected:** Сообщение доставлено; в логах нет `send_peer_invalid` и нет 400 PEER_ID_INVALID на `messages.uploadMedia`.
**Why human:** 400 PEER_ID_INVALID приходит от живого сервера, которого в тестах нет. Фикстура подменяет клиент на `AsyncMock` — туда и голое число проходит молча, поэтому юнит-тесты закрепляют форму запроса, но не факт доставки.

#### 2. Русский текст потери доступа в истории отправок

**Test:** Отправить объявление в группу, из которой аккаунт удалён, и открыть экран истории отправок.
**Expected:** В истории стоит «Аккаунт больше не имеет доступа к этой группе — пересинхронизируйте группы аккаунта.», английской строки telethon нет, повторной отправки не происходит.
**Why human:** Требует реальной группы с потерянным доступом и прохода значения через `group.last_error` / `SendLog` до экрана — цепочка целиком за пределами адаптера.

### Gaps Summary

Гэпов нет. Все десять истин `must_haves` подтверждены на реальном коде, а не по тексту SUMMARY: три точки отправки перечислены в файле поимённо, единственный оставшийся `int(...)` живёт внутри `_resolve_peer`, потолок прогрева закреплён поведенчески на обеих ветках, ветка `PeerIdInvalidError` доказанно достижима (проверен MRO), границы диффа подтверждены командой на всём диапазоне `e953f2c..HEAD` без ограничения путей, а прицельный набор прогнан верификатором и дал заявленные 95 passed при базовой линии 88.

Статус `human_needed`, а не `passed`, ровно по одной причине: плановый `<human-check>` боевой отправки в этом окружении неисполним. Это ожидаемое и зафиксированное ограничение (`WINDOWS.md` запись 10, покрытие D5 с `human_judgment: true`), а не пропущенная работа.

Единственное предупреждение — устаревший `graphify-out/graph.json` в рабочем дереве: обновление графа осталось в снятом worktree исполнителя. Цели задачи не касается, закрывается одним прогоном `graphify update .`.

---

_Verified: 2026-08-26T14:57:01Z_
_Verifier: Claude (gsd-verifier)_
