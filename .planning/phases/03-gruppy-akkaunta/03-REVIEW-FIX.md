---
phase: 03-gruppy-akkaunta
fixed_at: 2026-08-12T00:00:00Z
review_path: .planning/phases/03-gruppy-akkaunta/03-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-08-12
**Source review:** `.planning/phases/03-gruppy-akkaunta/03-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (CR-01, CR-02, WR-01 … WR-05)
- Fixed: 7
- Skipped: 0
- Out of scope (untouched): IN-01 … IN-08

## Verification

**Где прогонялись гейты:** правки делались и коммитились в изолированном
git-worktree (`.claude/worktrees/rf-03-…`), а pytest запускался интерпретатором
основного чекаута (`/source/broadcaster/.venv/bin/python -m pytest`) с рабочим
каталогом внутри worktree. У worktree нет собственного `.venv`, поэтому
окружение зависимостей — то же самое, что в основном чекауте; воспроизвести
цифры после сноса worktree можно из `master` тем же интерпретатором.

| Прогон | Результат |
|---|---|
| Базовая линия (после CR-01, до остальных правок) | 1052 passed |
| Полная суита на итоговом дереве | **1069 passed, 0 failed** (12:06) |

Каждая правка дополнительно проверялась целевым подмножеством перед своим
коммитом. Прирост +17 тестов — новые проверки, перечисленные ниже.

**Гейты, которые НЕ прогонялись:** линтера в окружении нет (`ruff` не
установлен — это отдельно отмечено в IN-01), миграция 0015 прогонялась только
round-trip'ом на SQLite; на PostgreSQL она не выкатывалась.

## Fixed Issues

### CR-01: Ветка записи отказа синхронизации недостижима

**Files modified:** `app/messengers/base.py`, `app/messengers/whatsapp.py`,
`app/messengers/max.py`, `app/messengers/telegram_user.py`,
`app/pages/accounts.py`, `tests/test_messengers/test_whatsapp.py`,
`tests/test_messengers/test_max.py`, `tests/test_messengers/test_telegram_user.py`,
`tests/test_routes/test_sync_groups.py`
**Commit:** `c6a1634`

**Applied fix:** Заведён `MessengerFetchError` в `app/messengers/base.py` —
общий дом для всех трёх адаптеров (в REVIEW.md класс предлагался внутри
`whatsapp.py`; общий модуль выбран, чтобы `max.py` и `telegram_user.py` не
импортировали друг у друга). Все три `get_groups()` перестали глушить отказ:
не-200 и обрыв соединения поднимают исключение, пустой список означает ровно
«групп нет». У Telethon `raise` поставлен внутри `except` перед `finally`,
поэтому сессия по-прежнему закрывается на пути отказа (закреплено
`assert_awaited` на `disconnect`).

**Отклонение от текста REVIEW.md:** широкий `except Exception` в
`accounts_sync_groups` СОХРАНЁН и стоит ПОСЛЕ узкого `except
MessengerFetchError`, а не заменён им. Причина: `RuntimeError("Cannot start
wa-worker")` поднимается свойством `bridge_url` ДО запроса за составом групп и
`MessengerFetchError`'ом не является; сузив блок, мы вернули бы на экран
стек-трейс там, где раньше была красная плашка. Узкая ветка нужна для
отдельного лог-события и точного сообщения, широкая — как страховка.

**Проверено перед сменой контракта:** единственные потребители `get_groups()` в
приложении — три ветки `app/pages/accounts.py`; `app/messengers/base.py` —
абстракция, `max_worker/main.py:1022` — HTTP-эндпоинт самого воркера, не
вызывающий. Celery-таски состав групп берут из `get_sync_status()`, а не из
`get_groups()`.

**Тесты:** все три адаптерных теста переведены на `pytest.raises` и вызывают
НАСТОЯЩИЙ класс с подменённым HTTP-слоем (`patch("…get_http_client")`), как
требовал review. Добавлены парные тесты «пустой ответ 200 — не ошибка» (иначе
исключение могло бы поехать и на валидной пустоте). Добавлен страничный
`test_bridge_failure_reaches_the_account_through_the_real_adapter`: живой
`WhatsAppMessenger` + подменённые `ensure_wa_container` и HTTP-клиент,
проверяет, что 502 от моста ложится на аккаунт ошибкой И не помечает ни одной
группы.

---

### CR-02: Пустой ответ мессенджера принимается за авторитетную опись

**Files modified:** `app/application/accounts/group_resync.py`,
`app/worker/tasks.py`, `tests/test_application/test_group_resync.py`,
`tests/test_routes/test_sync_groups.py`
**Commit:** `8de235f`

**Applied fix:** В `apply_group_resync` добавлен предохранитель `if existing and
not seen and not allow_full_wipe` — ровно как предложено в REVIEW.md. Результат
с `error=EMPTY_RESPONSE_MESSAGE` записывается на аккаунт той же формой
`last_sync_result`, поэтому существующая ветка красной плашки его уже рисует.
`last_synced_at` не переставляется (согласовано с WR-02). Флаг
`allow_full_wipe=False` по умолчанию; ни один вызывающий его не снимает.

Предохранитель безопасно стоит ПОСЛЕ основного цикла: `created`/`renamed`
растут только после `seen.add`, поэтому пустой `seen` гарантирует, что сессия
ещё не тронута и откатывать нечего (это выписано комментарием в коде).

**Сверх текста REVIEW.md:** обе Celery-таски теперь логируют отклонённый ответ
отдельным событием `sync_response_rejected` вместо `sync_complete` — иначе в
логе вырожденный ответ выглядел бы успешным синком.

**Тесты:** `test_empty_response_marks_all_and_deletes_none` закреплял ровно
дефектное поведение и переписан в
`test_empty_response_marks_nothing_and_deletes_none`. Добавлены
`test_empty_response_on_empty_account_is_a_normal_zero_sync` (предохранитель не
бьёт по новому аккаунту без групп) и
`test_allow_full_wipe_puts_the_decision_on_the_caller`. Страничный
`test_sync_marks_missing_group_but_keeps_it` перестроен так, чтобы проверять
пометку через НЕпустой ответ, и рядом добавлен
`test_sync_refuses_to_mark_everything_on_an_empty_response`.

---

### WR-01: Тумблер группы не работает без JavaScript

**Files modified:** `app/templates/account_groups/includes/group_row.html`,
`app/static/css/app.css`, `tests/test_pages/test_account_groups.py`
**Commit:** `ea0f412`

**Applied fix:** В форму тумблера добавлена настоящая submit-кнопка, обёрнутая
в `<span x-init="$el.remove()">`. Выбран второй вариант из REVIEW.md, а не
`<noscript>`: `<noscript>` в проекте не используется вовсе И, что важнее, он
закрывает только выключенный JS — а реальный сценарий из формулировки находки
(«не навесится Alpine») означает JS включён, Alpine не загрузился. `x-init`
закрывает оба.

Добавлено одно CSS-правило (`display: inline-flex` на форме тумблера): без него
резервная кнопка вставала бы ПОД тумблер и ломала высоту строки-карточки — при
живом Alpine правило не проявляется, потому что кнопки уже нет.

**Тесты:** `test_toggle_is_a_real_post_form` проверял только открывающий тег
формы и потому дефект не ловил; теперь он разбирает тело формы и требует
наличия элемента с `type="submit"`.

---

### WR-02: Неудавшийся синк переставляет `last_synced_at`

**Files modified:** `app/application/accounts/group_resync.py`,
`tests/test_application/test_group_resync.py`,
`tests/test_routes/test_sync_groups.py`, `tests/test_worker/test_tasks.py`
**Commit:** `a3a454e`

**Applied fix:** Строка `account.last_synced_at = _utcnow()` убрана из
`record_sync_failure`, докстринг объясняет почему через обоих потребителей
колонки. Шаблон `list.html` править не потребовалось: ветка `{% elif
account.last_synced_at %}` становится корректной сама, как только колонку
перестаёт портить провал.

**Тесты:** добавлен
`test_record_sync_failure_does_not_move_last_synced_at`, который проверяет обе
стороны — провал не ставит колонку на свежем аккаунте И не сдвигает её после
удавшегося синка (без второй половины тест зеленел бы и на реализации, которая
не пишет колонку вовсе). Добавлен страничный
`test_failed_first_sync_leaves_the_screen_saying_groups_not_fetched_yet` на
текст экрана («Групп пока нет», а не «Все группы удалены»), как и просил
review. Четыре ассерта `last_synced_at is not None` в `test_tasks.py`
инвертированы — они закрепляли исправляемое поведение.

---

### WR-03: Guard `status == "syncing"` не закрывает гонку двойного нажатия

**Files modified:** `app/models/group.py`, `app/pages/accounts.py`,
`alembic/versions/0015_groups_unique_account_external.py`,
`tests/test_migrations/test_0015_groups_unique_account_external.py`,
`tests/test_migrations/test_0014_sync_result_columns.py`,
`tests/test_pages/test_account_groups.py`
**Commit:** `cd4714b`

**Applied fix, часть 1 (сделано как предложено):** `UniqueConstraint("account_id",
"group_external_id", name="uq_groups_account_external")` на модели + ревизия
0015 с дедупликацией существующих строк в ней же. Ограничение создаётся через
`batch_alter_table` — на SQLite (вся тестовая суита) именованное UNIQUE иначе
не добавляется. Правила слияния дублей выбраны так, чтобы не потерять ни одного
пользовательского решения: выживает строка с наименьшим id (на неё ссылаются
расписания, созданные до появления дубля — `schedules.group_ids` хранится
JSON-ом и переписан ревизией быть не может), выживает выключенность (ошибка
выбирается в сторону НЕотправки — «не отправили» чинится одним нажатием,
«отправили в выключенный чат» необратимо) и самая ранняя `missing_since`.
Попутно снимается IN-07.

**Applied fix, часть 2 — выбран второй из двух разрешённых вариантов.** REVIEW.md
допускал «либо честно занимать статус, либо убрать ложное утверждение из
комментария». Занимать статус здесь НЕЛЬЗЯ: запрос, умерший между «занял» и
«освободил», оставил бы аккаунт в `syncing` навсегда — фоновой задачи, которая
его вычистит, на страничном пути нет, а guard тогда заблокировал бы синк
окончательно. Это хуже исходного дефекта. Комментарий переписан на правду и
называет настоящую защиту (ограничение схемы) и настоящее следствие гонки
(IntegrityError на коммите одного из двух запросов вместо двух строк).

**Тесты:** новый файл round-trip ревизии 0015 (6 тестов), ключевой из них —
`test_duplicate_rows_are_merged_not_just_deleted`: ревизия единственный раз во
всём проекте удаляет строки `groups`, поэтому проверяется КАЖДОЕ правило
слияния по отдельности, плюс `test_same_external_id_in_another_account_survives`
(T-03-06) и `test_group_without_duplicates_keeps_its_disabled_state` (промах в
`HAVING COUNT(*) > 1` выключил бы группы, которых дефект не касался).

**Побочные правки, потребовавшиеся из-за ограничения:**
- фикстура `_seed_group` в `test_account_groups.py` выводила
  `group_external_id` из ИМЕНИ, поэтому тест про две одноимённые группы создавал
  две строки с одинаковым внешним идентификатором — состояние, которого он не
  имел в виду. Идентификатор теперь берётся из счётчика;
- `test_revision_0014_continues_0013` утверждал «0014 — голова истории»; с
  появлением 0015 это перестало быть верно. Утверждение заменено на «история не
  разветвилась» — то, что файл и имел в виду (его собственный докстринг это
  предсказывал).

---

### WR-04: Ответ мессенджера объявлен недоверенным, но не проверяется

**Files modified:** `app/application/accounts/group_resync.py`,
`tests/test_application/test_group_resync.py`
**Commit:** `d2f71a3`

**Applied fix:** Три проверки на входе хелпера, как предложено: форма всего
ответа, пропуск не-`Mapping` элементов, обрезка `external_id` и `name` по 255.
Аннотация `fetched` сменена с `Iterable` на `Sequence`.

**Отклонение от текста REVIEW.md:** на не-список хелпер НЕ поднимает
`ValueError`, а возвращает `GroupResyncResult(error=MALFORMED_RESPONSE_MESSAGE)`.
`ValueError` дал бы ту же пятисотку через `generic_error_handler`, от которой
находка и защищает, — сменился бы только тип исключения. Возврат результата
кладёт причину на аккаунт той же формой, что и любой отказ синка, и пользователь
видит красную плашку. Мусорные ЭЛЕМЕНТЫ при этом пропускаются, а не роняют весь
синк: там ошибся отдельный чат, а не мост.

**Тесты:** ровно три случая, названные в review, плюс четвёртый —
`test_object_instead_of_list_is_refused_not_crashed` (`{"error": "..."}`),
`test_scalar_items_are_skipped_without_losing_the_rest` (`[1, 2, 3]` вперемешку
с валидной группой), `test_overlong_name_and_id_are_trimmed_to_the_column` (имя
и id по 5000 символов) и `test_nameless_group_falls_back_to_the_trimmed_id`
(ветка `name or external_id` тоже обязана обрезать).

---

### WR-05: Массовая пропажа групп отображается зелёной плашкой успеха

**Files modified:** `app/templates/account_groups/list.html`,
`tests/test_pages/test_account_groups.py`
**Commit:** `9b852b2`

**Applied fix:** Вариант плашки выбирается по содержимому сводки:
`'warning' if missing > 0 else 'success'`. Класс `alert--warning` в
`app/static/css/app.css:797` уже существовал — новых стилей не понадобилось.
Красный сознательно не используется: синк состоялся, повторять его незачем.

**Тесты:** `test_plashka_with_missing_groups_is_not_painted_as_success` и парный
`test_plashka_stays_success_while_nothing_went_missing` — без второй стороны
предупреждающий тон мог бы стоять всегда, и цвет перестал бы что-либо различать.

## Skipped Issues

Пропущенных находок нет.

## Требует человеческой проверки

Автоматическая верификация (перечитывание файла + зелёная суита) подтверждает
синтаксис и отсутствие регрессий, но не семантику. Две правки меняют
ПОВЕДЕНИЕ, а не только форму, и их стоит подтвердить глазами:

1. **CR-02 — порог предохранителя.** Условие `existing and not seen` отклоняет
   любой ответ, не содержащий ни одной ранее известной группы. Побочное
   следствие: пользователь, который действительно вышел из всех чатов сразу,
   получит красную плашку вместо пометок и должен будет удалить группы вручную.
   Это осознанный размен, но он затрагивает живой сценарий.
2. **WR-03 — ревизия 0015 удаляет строки.** Единственное место во всём проекте,
   где миграция удаляет данные из `groups`. Правила слияния (наименьший id,
   выключенность, самая ранняя пометка) проверены тестом на SQLite, но на
   продовой PostgreSQL ревизия не прогонялась, а целевая база по STATE.md стоит
   на 0012 — выкат будет прыжком 0012 → 0015. **Перед выкатом стоит снять
   слепок таблицы `groups` и посчитать
   `SELECT account_id, group_external_id, COUNT(*) FROM groups GROUP BY 1,2
   HAVING COUNT(*) > 1`** — если дублей нет, ревизия сведётся к добавлению
   ограничения.

Отдельно: с WR-03 гонка двойного нажатия заканчивается `IntegrityError` на
коммите, то есть пятисоткой. Это лучше молчаливого дубля, но обработчиком не
перехватывается — если такой отказ окажется заметным на практике, его стоит
довести до плашки отдельной находкой.

---

_Fixed: 2026-08-12_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
