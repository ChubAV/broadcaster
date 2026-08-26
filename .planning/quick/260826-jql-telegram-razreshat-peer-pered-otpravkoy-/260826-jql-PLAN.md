---
phase: quick-260826-jql-telegram-resolve-peer
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - app/messengers/telegram_user.py
  - tests/test_messengers/test_telegram_user.py
autonomous: true
requirements:
  - QUICK-TG-RESOLVE-PEER
estimate:
  tokens: 55000
  raw_tokens: 55000
  tasks: 3
  confidence: low
must_haves:
  truths:
    - "Во ВСЕ ТРИ точки отправки `send_message` уходит РАЗРЕШЁННАЯ сущность, полученная `get_input_entity`, а не голое число `int(group_id)`: `send_file` в ветке картинок (сегодня строка 219), `send_message` в откате после `ForbiddenError` (строка 228) и `send_message` текстовой ветки (строка 230)."
    - "Peer разрешается РОВНО ОДИН РАЗ за вызов `send_message` — до ветвления на картинки/текст, а не по разу на каждую точку отправки."
    - "Холодный кэш сущностей прогревается вызовом `get_dialogs()` РОВНО ОДИН РАЗ за вызов `send_message`, после чего разрешение повторяется ровно один раз. Второго прогрева и третьей попытки нет ни на одной ветке: лишний тяжёлый запрос к Telegram на каждую отправку в недоступную группу приближает FloodWait на аккаунте."
    - "Одна картинка уходит ОДИНОЧНЫМ файлом, а не списком из одного элемента: это уводит telethon с альбомной ветки `_send_album` на `messages.sendMedia`, и `messages.uploadMedia` — запрос, который сегодня получает 400 PEER_ID_INVALID, — не вызывается вовсе. Две и более картинок продолжают уходить списком."
    - "`PeerIdInvalidError` ловится ОТДЕЛЬНОЙ веткой выше catch-all и даёт `{\"ok\": False, \"no_retry\": True, \"error\": PEER_UNREACHABLE_MESSAGE}` — русский текст, а не строку telethon."
    - "Окончательный провал разрешения peer (`ValueError` из `get_input_entity` ПОСЛЕ прогрева) даёт ТОТ ЖЕ ответ, что и `PeerIdInvalidError`: это то же самое «группа недоступна», а не неизвестный сбой, и в catch-all он больше не утекает."
    - "Ни одна ветка отказа не отдаёт наружу английский текст telethon: `result[\"error\"]` в обоих исходах равен константе `PEER_UNREACHABLE_MESSAGE` целиком, а не содержит её."
    - "`get_groups`, `get_group_details`, `check_connection` и весь блок QR-авторизации не тронуты; `app/application/scheduling/use_cases.py` и `app/services/schedule_rules.py` не изменены ни байтом."
    - "Автоматическая пересинхронизация групп и автоматическая деактивация группы по этой ошибке НЕ введены: задача меняет текст ошибки и флаг `no_retry`, и ничего сверх."
    - "`uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q` — зелёный (базовая линия до правки: 88 passed)."
  artifacts:
    - "app/messengers/telegram_user.py — `PEER_UNREACHABLE_MESSAGE`, `PeerUnreachableError`, метод `TelegramUserMessenger._resolve_peer`"
    - "tests/test_messengers/test_telegram_user.py — восемь затронутых тестов: шесть новых от задачи 1 (три на подстановку разрешённой сущности в три точки отправки, одна на прогрев кэша ровно один раз, две на единый русский текст отказа), одна новая на границу «одна картинка / две картинки» и одна существующая, переписанная под одиночный файл с сохранением имени"
  key_links:
    - "`_resolve_peer(group_id)` → `peer` → ТРИ точки отправки. Разрыв этой связи в любой ОДНОЙ из трёх точек возвращает исходный дефект ровно на той ветке, и заметен он будет только в бою: с `AsyncMock`-клиентом голое число проходит молча."
    - "`get_input_entity` → `ValueError` → ОДИН `get_dialogs()` → повторная попытка. Прогрев внутри `_resolve_peer`, вызываемого один раз за отправку, — единственное место, где количество запросов к Telegram ограничено; перенос прогрева в точки отправки даёт до трёх `get_dialogs` на одну отправку."
    - "`PeerUnreachableError` и `PeerIdInvalidError` → ОДНА ветка `except` → `PEER_UNREACHABLE_MESSAGE`. Два разных исхода одной причины обязаны давать один ответ: разведённые по разным веткам, один из них уедет в catch-all и покажется пользователю сырым английским текстом."
    - "`result[\"error\"]` → `group.last_error` (`app/application/scheduling/use_cases.py:483`) и в `SendLog` → экран истории отправок. Это и есть причина, по которой возвращается КОНСТАНТА, а не `str(e)`: строка telethon здесь не диагностика в логе, а текст на экране пользователя."
    - "`len(files) == 1` → одиночный файл → `messages.sendMedia`. Граница живёт между 1 и 2, поэтому регрессия на ДВЕ картинки обязательна: тест на три её не держит."
---

<objective>
Разрешать peer группы явно перед отправкой в Telegram, чтобы отправка объявления с
картинками перестала падать на `PeerIdInvalidError`, а недоступная группа сообщала
о себе по-русски и без повторов.

Purpose: сегодня объявление с картинками в Telegram-группу не уходит ВОВСЕ —
`messages.uploadMedia` получает 400 PEER_ID_INVALID, — а пользователь видит в
истории отправок сырой английский текст telethon. Причина проверена по исходникам
telethon 1.42.0: клиент создаётся на каждую отправку заново, `StringSession.save()`
(`telethon/sessions/string.py:52`) хранит только dc_id/ip/port/auth_key, соответствия
`id → access_hash` в строке сессии нет. Голое число telethon вынужден УГАДЫВАТЬ по
знаку (`telethon/client/users.py:465-473`): `-100…` становится `PeerChannel` с
до-разрешением через `channels.getChannels(access_hash=0)`, прочее отрицательное —
`InputPeerChat(id)` вообще без проверки. Догадку сервер и отвергает. Падает именно
`uploadMedia`, потому что картинки всегда передаются СПИСКОМ, а на список telethon
уходит в альбомную ветку `_send_album` (`telethon/client/uploads.py:540`), где каждый
файл сперва конвертируется в `InputPhoto` через `messages.uploadMedia` — это ПЕРВЫЙ
запрос альбома, несущий peer. Текст идёт через `messages.sendMessage` и такой проверки
не проходит, поэтому та же группа принимает текст и отваливается на картинке.

Output: `TelegramUserMessenger` разрешает peer один раз за отправку с одним прогревом
кэша диалогов, шлёт одиночную картинку не списком, и отвечает на недоступную группу
русским текстом с `no_retry: True`.
</objective>

<execution_context>
@/source/broadcaster/.claude/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.claude/CLAUDE.md
@app/messengers/telegram_user.py
@app/messengers/base.py
@tests/test_messengers/test_telegram_user.py
</context>

<house_rules>
Правила этого репозитория, действующие на КАЖДУЮ задачу плана:

1. **Комментарии и докстринги — по-русски, плотно, про ПРИЧИНУ.** Проект объясняет
   не «что делает строка», а ПОЧЕМУ выбран этот вариант и ЧТО ЛОМАЕТСЯ иначе.
   Образец тона и плотности лежит в этом же файле — докстринг `get_groups`
   (`app/messengers/telegram_user.py:248-255`) и докстринг `MessengerFetchError`
   (`app/messengers/base.py:4-14`). Тонкий комментарий вида «разрешаем peer»
   этот проект не принимает.
2. **Имена тестов — английские предложения, называющие закрепляемую истину.**
   Образец в этом же файле: `test_get_groups_logs_error_on_failure`. Докстринг
   теста — по-русски, с объяснением, какой именно дефект тест ловит.
3. **Фикстура `messenger` подменяет клиент на `AsyncMock`.** Это значит, что
   ЛЮБОЙ неподменённый метод клиента возвращает новый `AsyncMock` и не падает —
   поэтому утверждение «в `send_file` уехала разрешённая сущность» обязано
   проверяться ИДЕНТИЧНОСТЬЮ (`is`) с объектом, который вернул подменённый
   `get_input_entity`. Проверка «не число» сама по себе бесполезна: `AsyncMock`
   числом не является никогда, и тест был бы зелёным и на сломанном коде.
4. **Запуск тестов — `uv run pytest`, как в `justfile`.** Полная сюита в этом
   проекте идёт дольше девяти минут и гейтом этой задачи НЕ является: правка
   затрагивает один адаптер, и его окружение закрывается прицельным набором из
   `<verify>`.
5. **Границы задачи.** `get_groups`, `get_group_details`, `check_connection` и
   блок QR-авторизации не трогаются. `app/application/scheduling/use_cases.py`
   не трогается: связка «группа — аккаунт» уже защищена `owned_group_ids`
   (`app/services/schedule_rules.py:35`). Автопересинхронизация и автодеактивация
   группы по этой ошибке НЕ вводятся.
6. **`graphify update .` после правок** — правило `CLAUDE.md`, исполняется в
   задаче 3.
</house_rules>

<tasks>

<task type="tracer" tdd="true">
  <name>Задача 1: сквозная нить — разрешённый peer доходит до всех трёх точек отправки, а недоступная группа говорит по-русски</name>

  <files>app/messengers/telegram_user.py, tests/test_messengers/test_telegram_user.py</files>

  <read_first>
    - `app/messengers/telegram_user.py:1-21` — блок импортов telethon и объявление `logger`.
    - `app/messengers/telegram_user.py:189-246` — секция «Messenger adapter» целиком: `__init__`, `send_message` со всеми тремя точками отправки и лестницей `except`.
    - `app/messengers/telegram_user.py:247-271` — `get_groups`: ОБРАЗЕЦ плотности докстринга и обращения с `finally`.
    - `app/messengers/base.py:1-14` — `MessengerFetchError`: образец того, как в этом проекте объявляется собственное исключение адаптера и как пишется его докстринг.
    - `tests/test_messengers/test_telegram_user.py:17-31` — фикстура `messenger`.
    - `tests/test_messengers/test_telegram_user.py:34-63` — три существующих теста отправки: форма обращения к `call_args`.
    - `tests/test_messengers/test_telegram_user.py:196-214` — `test_get_groups_logs_error_on_failure`: образец русского докстринга теста.
    - `app/application/scheduling/use_cases.py:480-492` — потребитель ответа: куда попадает `result["error"]` при `no_retry`.
  </read_first>

  <behavior>
    Тесты пишутся ДО правки кода и краснеют на текущем дереве.

    - Тест 1 — `test_send_file_receives_a_resolved_peer_not_a_bare_id`:
      `get_input_entity` подменён и возвращает часовой объект; после
      `send_message("-100123", "Hi", images=[одна ссылка])` первый позиционный
      аргумент `send_file` — ЭТОТ САМЫЙ объект (сравнение через `is`).
      На текущем дереве туда уезжает `-100123`.
    - Тест 2 — `test_the_text_path_sends_to_a_resolved_peer`: без картинок первый
      позиционный аргумент `client.send_message` — тот же часовой объект.
    - Тест 3 — `test_the_forbidden_media_fallback_also_uses_the_resolved_peer`:
      `send_file` кидает `ForbiddenError`, и текстовый откат уходит ТОЙ ЖЕ
      разрешённой сущности. Точка отправки третья и самая незаметная — без
      своего теста она остаётся с голым числом и в бою падает только у тех
      групп, где запрещены медиа.
    - Тест 4 — `test_a_cold_entity_cache_is_warmed_exactly_once`:
      `get_input_entity.side_effect = [ValueError("cold"), часовой объект]`;
      после успешной текстовой отправки `get_dialogs.await_count == 1`,
      `get_input_entity.await_count == 2`, `result["ok"] is True`, и в
      `client.send_message` уехал часовой объект.
    - Тест 5 — `test_a_peer_that_stays_unresolved_reads_as_a_lost_group`:
      `get_input_entity.side_effect = ValueError("cold")` на ВСЕХ вызовах;
      `result["ok"] is False`, `result["no_retry"] is True`,
      `result["error"] == PEER_UNREACHABLE_MESSAGE`, и `get_dialogs.await_count == 1` —
      прогрев не зацикливается.
    - Тест 6 — `test_peer_id_invalid_is_not_reported_to_the_user_in_english`:
      `send_message` клиента кидает `PeerIdInvalidError(request=None)`;
      `result["ok"] is False`, `result["no_retry"] is True`,
      `result["error"] == PEER_UNREACHABLE_MESSAGE`. Дополнительно
      утверждается, что `result["error"]` НЕ содержит подстроки `"Peer"` —
      это и есть проверка того, что наружу ушла константа, а не `str(e)`.
    - Существующие шестнадцать тестов файла остаются зелёными без правки:
      фикстура отдаёт `AsyncMock`, поэтому `get_input_entity` у них разрешается
      сам собой, а форма обращения `call_args[0][1]` к списку файлов не меняется —
      peer встаёт нулевым аргументом, файлы остаются первым.
  </behavior>

  <action>
Правка идёт одним куском: подстановка peer в три точки отправки и обработка
неразрешимого peer — одно утверждение о поведении, и разъединённые они дают
дерево, где две ветки из трёх чинены, а третья молча падает в бою.

1. **Импорт.** Добавить `PeerIdInvalidError` в существующий блок
   `from telethon.errors import (...)`. Блок отсортирован по алфавиту — имя
   встаёт между `ForbiddenError` и `SlowModeWaitError`.

2. **Константа текста отказа.** Рядом с секцией «Messenger adapter» объявить
   модульную константу `PEER_UNREACHABLE_MESSAGE` со значением
   `"Аккаунт больше не имеет доступа к этой группе — пересинхронизируйте группы аккаунта."`
   Комментарий над ней называет ПРИЧИНУ существования именно константы, а не
   литерала в месте возврата: значение уезжает в `group.last_error`
   (`app/application/scheduling/use_cases.py:483`) и в `SendLog`, то есть прямо
   на экран истории отправок; два исхода одной причины возвращают ЕГО ЖЕ, и
   разъехавшись, они показали бы пользователю два разных объяснения одной беды.

3. **Собственное исключение.** Объявить `class PeerUnreachableError(RuntimeError)`
   по образцу `MessengerFetchError` (`app/messengers/base.py:4-14`) — с
   докстрингом, объясняющим ПОЧЕМУ оно заведено: `get_input_entity` на
   окончательно недоступной группе поднимает `ValueError`, и это ровно то же
   «аккаунт потерял доступ к группе», что и ответ сервера PEER_ID_INVALID, но
   типом от него неотличимое от любого другого `ValueError` в теле отправки.
   Собственный тип позволяет поймать оба исхода ОДНОЙ веткой и не расширять её
   до `except ValueError`, который проглотил бы, например, негодный
   идентификатор группы и выдал бы его за потерю доступа.

4. **Метод `_resolve_peer(self, group_id: str)`** на `TelegramUserMessenger`,
   до `send_message`:
   - `peer_id = int(group_id)` вычисляется ВНЕ `try`. Негодный идентификатор не
     должен выглядеть как холодный кэш и тянуть лишний запрос к Telegram.
   - первая попытка `await self.client.get_input_entity(peer_id)`;
   - на `ValueError` — РОВНО ОДИН `await self.client.get_dialogs()` и РОВНО ОДНА
     повторная попытка;
   - второй `ValueError` → `raise PeerUnreachableError(PEER_UNREACHABLE_MESSAGE) from e`.
   Докстринг метода несёт разбор причины из `<objective>` своими словами: строка
   сессии не хранит `access_hash`, клиент на каждую отправку свежий, кэш
   сущностей пуст, telethon угадывает peer по знаку числа, и догадку сервер
   отвергает. Отдельным абзацем — почему прогрев ОДИН: `get_dialogs()` для
   свежего клиента запрос не бесплатный, а группа, потерянная навсегда, отправку
   получает по расписанию раз за разом; второй прогрев на попытку превратил бы
   потерянную группу в источник FloodWait на аккаунте.

5. **Подстановка в `send_message`.** Сразу после `await self.client.connect()` и
   ДО ветвления на картинки/текст — `peer = await self._resolve_peer(group_id)`.
   Один вызов на отправку: разрешение внутри веток дало бы до трёх прогревов на
   одну отправку. Заменить `int(group_id)` на `peer` во всех трёх точках:
   `send_file` (сегодня строка 219), `send_message` в откате после
   `ForbiddenError` (строка 228), `send_message` текстовой ветки (строка 230).

6. **Ветка обработки.** Между веткой запретов
   (`ChatWriteForbiddenError, UserBannedInChannelError, ForbiddenError`) и
   catch-all добавить `except (PeerIdInvalidError, PeerUnreachableError) as e:`
   с `self.log.warning("send_peer_invalid", group_id=group_id, error=str(e))` и
   возвратом `{"ok": False, "error": PEER_UNREACHABLE_MESSAGE, "no_retry": True}`.
   Порядок относительно ветки запретов безразличен и это стоит сказать
   комментарием: `PeerIdInvalidError` наследует `BadRequestError` (400), а не
   `ForbiddenError` (403), пересечения между ветками нет. Что сказать
   комментарием ОБЯЗАТЕЛЬНО — две вещи: почему `no_retry` (peer не станет
   валидным сам собой, повтор шлёт тот же отвергаемый запрос и приближает
   FloodWait) и почему наружу уходит константа, а не `str(e)` (`str(e)` — это
   текст экрана пользователя, а не строка лога; диагностика остаётся в
   `log.warning`, где ей и место).
  </action>

  <verify>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py -q</automated>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py --collect-only -q -k "resolved_peer or warmed_exactly_once or stays_unresolved or in_english" 2>/dev/null | grep -c "::test_" | grep -qx 6</automated>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py -q -k "resolved_peer or warmed_exactly_once or stays_unresolved or in_english"</automated>
    <automated>uv run python -c "from app.messengers.telegram_user import PEER_UNREACHABLE_MESSAGE, PeerUnreachableError, TelegramUserMessenger; assert hasattr(TelegramUserMessenger, '_resolve_peer'); assert 'пересинхронизируйте' in PEER_UNREACHABLE_MESSAGE"</automated>
  </verify>

  <done>Шесть новых регрессий зелёные, шестнадцать существующих зелёные без правки. Во все три точки отправки уходит объект, возвращённый `get_input_entity` (проверено `is`). Холодный кэш прогревается ровно одним `get_dialogs`, попыток разрешения ровно две. `PeerIdInvalidError` и окончательный `ValueError` дают один и тот же ответ `{"ok": False, "no_retry": True, "error": PEER_UNREACHABLE_MESSAGE}`, английского текста telethon в нём нет.</done>
</task>

<task type="auto" tdd="true">
  <name>Задача 2: одна картинка уходит одиночным файлом и не будит альбомную ветку</name>

  <files>app/messengers/telegram_user.py, tests/test_messengers/test_telegram_user.py</files>

  <read_first>
    - `app/messengers/telegram_user.py:204-231` — ветка картинок после правки задачи 1.
    - `tests/test_messengers/test_telegram_user.py:43-90` — `test_send_message_with_image` и `test_send_message_with_multiple_images`: обе достают файлы из `call_args[0][1]`; первую предстоит переписать под одиночный файл.
    - `.venv/lib/python3.12/site-packages/telethon/client/uploads.py` — ветвление `send_file` на список и тело `_send_album` (строка около 540): убедиться своими глазами, что `messages.uploadMedia` вызывается ИМЕННО там и ИМЕННО первым.
  </read_first>

  <behavior>
    - Тест 1 (переписывается существующий, имя сохраняется) —
      `test_send_message_with_image`: при ОДНОЙ картинке первый файловый
      аргумент `send_file` — сам объект `BytesIO` с именем `img.jpg` и
      содержимым `b"fake-image-bytes"`, а НЕ список. Утверждение об этом
      прямое: `assert not isinstance(sent, list)`. На дереве после задачи 1
      тест красный — туда уезжает список из одного элемента.
    - Тест 2 (новый) — `test_two_images_still_go_as_an_album`: при ДВУХ
      картинках уезжает список длиной 2 с именами `img1.jpg` и `img2.jpg`.
      Граница `len(files) == 1` живёт между единицей и двойкой, и
      существующий тест на ТРИ картинки её не держит: перепутанное сравнение
      «не больше единицы» вместо «ровно один» он не поймает.
    - Существующий `test_send_message_with_multiple_images` (три картинки)
      остаётся зелёным без правки.
  </behavior>

  <action>
1. В ветке картинок `send_message` вычислить полезную нагрузку перед вызовом:
   при `len(files) == 1` в `send_file` уходит `files[0]`, иначе — сам список
   `files`. Вызов `send_file` остаётся один, `caption=text` и
   `force_document=False` не меняются.

2. Комментарий над этим вычислением называет ПРИЧИНУ, а не действие: список
   уводит telethon в альбомную ветку `_send_album`
   (`telethon/client/uploads.py`, около строки 540), где каждый файл сперва
   конвертируется в `InputPhoto` через `messages.uploadMedia` — это ПЕРВЫЙ
   запрос альбома, несущий peer, и именно он получал от сервера отказ. Одиночный
   файл идёт через `messages.sendMedia`, и `uploadMedia` не вызывается вовсе.
   Отдельной фразой — что это ВТОРАЯ независимая мера, а не замена разрешению
   peer из задачи 1: разрешённый peer чинит и альбом тоже, а одиночный файл
   убирает с пути самый хрупкий запрос у самого частого случая — одной картинки
   в объявлении.

3. Переписать `test_send_message_with_image` под одиночный файл, сохранив имя
   теста: имя называет истину «одна картинка уходит», и заводить рядом второе
   имя для того же утверждения значило бы держать две записи одного факта.
   Русский докстринг теста говорит, какой дефект он ловит.

4. Добавить `test_two_images_still_go_as_an_album` с русским докстрингом,
   называющим границу.
  </action>

  <verify>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py -q</automated>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py --collect-only -q -k "with_image or two_images or multiple_images" 2>/dev/null | grep -c "::test_" | grep -qx 3</automated>
    <automated>uv run pytest tests/test_messengers/test_telegram_user.py -q -k "with_image or two_images or multiple_images"</automated>
  </verify>

  <done>При одной картинке в `send_file` уезжает сам `BytesIO`, при двух и при трёх — список соответствующей длины. Весь файл тестов зелёный. Комментарий у вычисления объясняет альбомную ветку и `uploadMedia`, а не пересказывает условие.</done>
</task>

<task type="auto">
  <name>Задача 3: закрывающий прогон — границы соблюдены, объявления не расходятся с кодом, граф обновлён</name>

  <files>app/messengers/telegram_user.py, tests/test_messengers/test_telegram_user.py</files>

  <read_first>
    - Диффы задач 1 и 2 целиком, от коммита самого плана: `git diff $(git log -1 --format=%H -- .planning/quick/260826-jql-telegram-razreshat-peer-pered-otpravkoy-/260826-jql-PLAN.md) -- app/messengers/telegram_user.py tests/test_messengers/test_telegram_user.py`. База берётся так, а не `HEAD~N`, потому что число коммитов, оставленных задачами 1 и 2 в TDD-режиме, заранее неизвестно.
  </read_first>

  <action>
Закрывающая сверка, новой функциональности не вносит.

1. Перечитать дифф и убедиться, что ни один комментарий и ни один докстринг в
   правленом файле не утверждает того, чего код рядом с ним не исполняет. Особое
   внимание — трём утверждениям, которые легко пережили бы правку и стали
   неверными: «прогрев ровно один раз» (сверить со счётчиком вызовов в теле
   `_resolve_peer`), «во все три точки уходит peer» (сверить перечислением точек
   отправки в файле) и «uploadMedia не вызывается при одной картинке» (сверить с
   условием на `len(files)`). Найденное расхождение чинится в этой же задаче.

2. Прогнать прицельный набор: тесты мессенджеров и два соседних файла, которые
   импортируют этот адаптер (`tests/test_services/test_messenger_factory.py`,
   `tests/test_routes/test_sync_groups.py`). Базовая линия до правки — 88 passed.

3. Убедиться, что правка не вышла за пределы двух файлов плана. Границы задачи
   проверяются командой, а не глазами: `app/application/`, `app/services/`,
   `app/worker/`, `app/routes/`, `app/models/`, `alembic/` не изменены ни байтом.
   Миграций задача не заводит, зависимостей не добавляет.

4. Убедиться, что в `app/messengers/telegram_user.py` не появилось ни вызова
   синхронизации групп, ни изменения состояния группы: задача меняет текст
   ошибки и флаг `no_retry`, автопересинхронизация и автодеактивация в неё не
   входят.

5. `graphify update .` — граф проекта содержит правленый модуль (правило `CLAUDE.md`).
  </action>

  <verify>
    <automated>uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q</automated>
    <automated>BASE=$(git log -1 --format=%H -- .planning/quick/260826-jql-telegram-razreshat-peer-pered-otpravkoy-/260826-jql-PLAN.md); test -n "$BASE" || { echo "PLAN.md не закоммичен — гейт диффа не имеет якоря" >&amp;2; exit 1; }; git diff --name-only "$BASE" -- app tests alembic pyproject.toml uv.lock | sort | tr '\n' '|' | grep -qx "app/messengers/telegram_user.py|tests/test_messengers/test_telegram_user.py|"</automated>
    <automated>uv run python -m compileall -q app main.py tests</automated>
    <automated>graphify update .</automated>
    <human-check>Отправить в боевом окружении объявление с ОДНОЙ картинкой в реальную Telegram-группу и убедиться, что сообщение ушло. Затем отправить объявление в группу, из которой аккаунт удалён, и убедиться, что в истории отправок стоит русский текст про потерю доступа, а не английская строка telethon.</human-check>
  </verify>

  <done>Прицельный набор зелёный (88+ passed), правка не вышла за два файла плана, ни одно объявление в правленом файле не расходится с кодом рядом, `graphify update .` отработал.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `groups.external_id` из БД → `int(group_id)` → telethon | значение, записанное синхронизацией групп, попадает в аргумент запроса к Telegram |
| ответ Telegram (текст исключения telethon) → `group.last_error` / `SendLog` → экран истории отправок | текст, сочинённый чужой стороной и библиотекой, доходит до пользователя без посредников |
| планировщик → `send_message` → Telegram API | частота обращений к Telegram от лица аккаунта пользователя; превышение наказывается FloodWait и потерей аккаунта |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-jql-01 | Information Disclosure | лестница `except` в `send_message` | medium | mitigate | Сырой текст telethon (`str(e)`) сегодня уезжает в `group.last_error` и `SendLog` и показывается пользователю: он несёт имя класса запроса и подсказку про ботов, то есть внутренности библиотеки на экране продукта. Обе ветки потери доступа возвращают КОНСТАНТУ `PEER_UNREACHABLE_MESSAGE`; диагностика остаётся в `log.warning("send_peer_invalid", ...)`. Закреплено тестом `test_peer_id_invalid_is_not_reported_to_the_user_in_english`, который утверждает РАВЕНСТВО константе и отсутствие подстроки `"Peer"`. |
| T-jql-02 | Denial of Service | `_resolve_peer` → `get_dialogs()` | medium | mitigate | `get_dialogs()` у свежего клиента — не бесплатный запрос, а группа, потерянная навсегда, получает отправку по расписанию раз за разом. Прогрев без потолка превратил бы её в источник FloodWait на аккаунте пользователя. Прогрев ровно один за вызов `send_message`, попыток разрешения ровно две; закреплено `test_a_cold_entity_cache_is_warmed_exactly_once` и утверждением `get_dialogs.await_count == 1` в `test_a_peer_that_stays_unresolved_reads_as_a_lost_group`. |
| T-jql-03 | Denial of Service | флаг `no_retry` на ветке потери доступа | medium | mitigate | Без `no_retry` вызывающий поднимает исключение (`app/application/scheduling/use_cases.py:486`) и отправка уходит в повтор, а повтор шлёт Telegram ТОТ ЖЕ отвергаемый запрос. `no_retry: True` на обеих ветках потери доступа обрывает цикл; закреплено обоими тестами отказа. |
| T-jql-04 | Spoofing | `group_id` как аргумент отправки | low | accept | `group_id` приходит из строки группы, уже отфильтрованной по владельцу: связка «группа — аккаунт» проверяется `owned_group_ids` (`app/services/schedule_rules.py:35`) ДО этой точки. Задача границу владения не пересекает и `app/application/scheduling/use_cases.py` не трогает — это записано отдельным правилом в `<house_rules>`. |
| T-jql-05 | Tampering | подмена peer чужой сущностью через прогретый кэш | low | accept | `get_input_entity` разрешает идентификатор через кэш сущностей ЭТОГО аккаунта, наполненный его же `get_dialogs()`: чужая группа в кэш попасть не может, потому что попадает туда только то, в чём аккаунт состоит. Разрешение сужает область возможных адресатов по сравнению с сегодняшней догадкой по знаку числа, а не расширяет её. |

Установок пакетов задача не делает: `pyproject.toml`, `uv.lock` и `package.json` в `files_modified` не входят и закреплены отдельным гейтом `<verify>` задачи 3 — поэтому строки цепочки поставки в реестре нет по построению.
</threat_model>

<verification>
1. `uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q` — зелёный; базовая линия до правки 88 passed.
2. Во все три точки отправки уходит объект, возвращённый `get_input_entity`, — проверено сравнением `is` в трёх отдельных тестах, по одному на точку.
3. Холодный кэш прогревается ровно одним `get_dialogs()`, попыток разрешения ровно две — на успешной ветке и на ветке окончательного отказа.
4. Одна картинка уезжает одиночным `BytesIO`, две — списком длиной 2, три — списком длиной 3.
5. `PeerIdInvalidError` и `ValueError` после прогрева дают ОДИН ответ: `ok=False`, `no_retry=True`, `error` РАВЕН `PEER_UNREACHABLE_MESSAGE`.
6. Дифф от коммита самого плана (`git log -1 --format=%H --` по пути к PLAN.md) по путям `app tests alembic pyproject.toml uv.lock` показывает ровно два файла плана и ни одного сверх них. База берётся от коммита плана, а не `HEAD~N`: число коммитов задачи в TDD-режиме заранее неизвестно, и `HEAD~3` сверял бы не тот интервал.
7. `uv run python -m compileall -q app main.py tests` — без ошибок.
8. `graphify update .` отработал.
</verification>

<success_criteria>
- Объявление с одной картинкой уходит в Telegram-группу, а не падает на `messages.uploadMedia`.
- Группа, из которой аккаунт удалён, сообщает о себе в истории отправок по-русски и один раз, а не английской строкой telethon и не бесконечными повторами.
- Разрешение peer стоит ОДНО на отправку и стоит ДО ветвления: ни одна из трёх точек отправки не осталась с голым числом.
- Границы задачи соблюдены: `get_groups`, `get_group_details`, QR-авторизация, планировщик и правила расписаний не тронуты; автопересинхронизация и автодеактивация группы не введены.
- Ни один комментарий и ни один докстринг в правленом файле не утверждает того, чего код рядом с ним не исполняет.
</success_criteria>

<output>
Create `.planning/quick/260826-jql-telegram-razreshat-peer-pered-otpravkoy-/260826-jql-SUMMARY.md` when done
</output>
