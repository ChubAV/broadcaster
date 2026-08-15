---
phase: 03-gruppy-akkaunta
fixed_at: 2026-08-12T20:55:00Z
review_path: .planning/phases/03-gruppy-akkaunta/03-REVIEW.md
iteration: 1
findings_in_scope: 15
fixed: 15
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-08-12
**Source review:** `.planning/phases/03-gruppy-akkaunta/03-REVIEW.md`
**Iteration:** 1
**Scope:** all (Critical + Warning + Info)

**Summary:**
- Findings in scope: 15 (1 critical, 5 warning, 9 info)
- Fixed: 15
- Skipped: 0

**Verification:** правки применялись и коммитились в изолированном git-worktree
(`.claude/worktrees/rf-03-…`, ветка `gsd-reviewfix/03-…`), затем ветка
fast-forward-ом переносилась на `master`. Тесты гонялись ТАМ ЖЕ, интерпретатором
основного checkout-а (`/source/broadcaster/.venv/bin/python -m pytest`) — в
worktree нет собственного `.venv`. Полная суита после последней правки: **1083
passed** (11 мин 51 с). Числа воспроизводимы из основного checkout-а после
fast-forward: worktree отличался от него только исходниками, среда была общая.

## Fixed Issues

### CR-01: Ревизия 0015 удаляет строки `groups`, но не переписывает ссылки на них в `schedules.group_ids`

**Files modified:** `alembic/versions/0015_groups_unique_account_external.py`, `tests/test_migrations/test_0015_groups_unique_account_external.py`
**Commit:** `96affc3`
**Applied fix:** перед `_DROP_DUPLICATES` добавлен шаг `_remap_schedule_group_ids`:
строит соответствие «удаляемый дубль → выживший» (`_DUPLICATE_MAP`), построчно
переводит `schedules.group_ids` и схлопывает дубликаты, возникшие после перевода
(расписание, выбравшее ОБЕ строки одной группы, не должно слать в чат дважды).
Параметр UPDATE объявлен `sa.JSON()` bindparam-ом — сериализацию берёт диалект,
поэтому шаг работает и на SQLite (TEXT), и на PostgreSQL (`json`, куда текстовый
литерал без приведения не принимается); чтение принимает и строку, и уже
десериализованный список. Не-целые элементы проходят насквозь — ревизия не имеет
права упасть на мусоре в чужой базе. Докстринг ревизии переписан: оправдание
«переписать эти ссылки ревизия не может» заменено на описание инварианта.
Тестовая схема 0014 дополнена таблицей `schedules`, добавлены
`test_schedule_reference_to_a_dropped_duplicate_is_remapped` (висячая ссылка
переезжает; выбор обеих строк схлопывается; расписание без дублей не трогается) и
`test_schedule_group_ids_survive_when_there_are_no_duplicates` (без дублей шаг не
переписывает ничего).

### WR-01: Задача отправки создаётся для группы, строки которой больше нет

**Files modified:** `app/application/scheduling/use_cases.py`, `tests/test_application/test_collect_due_inactive_group.py`
**Commit:** `afdfbbc`
**Applied fix:** `if group is None: continue` вынесено ОТДЕЛЬНОЙ веткой перед
проверкой включённости, с `logger.warning("group_skipped_missing", …)` —
«группы нет» и «группа выключена» различимы в логе, и уровень разный (висячая
ссылка — расхождение данных, а не решение пользователя). Избыточное `if group:`
внутри ветки `wa`/`max` снято: второе определение «группа есть» разъехалось бы с
первым. Добавлены три теста (все три канала: задача не создаётся; соседняя живая
группа шлёт дальше; в `SendLog` ничего не пишется).

### WR-02: Текст произвольного исключения уезжает в пользовательскую плашку

**Files modified:** `app/application/accounts/group_resync.py`, `app/pages/accounts.py`, `app/worker/tasks.py`, `tests/test_routes/test_sync_groups.py`
**Commit:** `f9a1b3d`
**Applied fix:** заведена константа `UNEXPECTED_FAILURE_MESSAGE` рядом с
`EMPTY_RESPONSE_MESSAGE`/`MALFORMED_RESPONSE_MESSAGE`; все три широких обработчика
(`accounts.py` и оба фоновых пути в `tasks.py`) пишут на аккаунт её вместо
`str(e) or e.__class__.__name__`. Исходный текст остаётся в логе с
`exc_info=True`. Узкие ветки (`MessengerFetchError`, состояние моста, таймаут)
сохранили свои тексты — они формируются нами.
`test_sync_failure_is_recorded_not_swallowed` переписан: теперь утверждает и
«отказ не потерян», и «детали исключения на экран не уехали». Ветку узкого
исключения по-прежнему держит
`test_bridge_failure_reaches_the_account_through_the_real_adapter` (`"502" in
result["error"]`).

### WR-03: Карточка редактора запрещает ПОСТАВИТЬ НА ПАУЗУ активное неполное расписание

**Files modified:** `app/templates/ads/includes/sched_card.html`, `tests/test_pages/test_editor_schedules.py`
**Commit:** `2e90f28`
**Applied fix:** введено `resume_blocked = not s.is_active and not complete` —
буквально то же выражение, что в `schedules/includes/schedule_row.html` и в
обработчике `app/pages/schedules.py`; `disabled` и подпись тумблера переведены на
него, текст исправлен на «Возобновить нельзя: …». Существующий тест пустого
аккаунта пересеян выключенным расписанием (недоступность относится именно к
возобновлению), добавлен
`test_active_incomplete_schedule_can_still_be_paused_from_the_editor`.

### WR-04: `IntegrityError` на новом ограничении не обработан — вместо плашки JSON-пятисотка

**Files modified:** `app/pages/accounts.py`, `tests/test_routes/test_sync_groups.py`
**Commit:** `7717564`
**Applied fix:** `await db.commit()` обёрнут в `try/except IntegrityError`:
откат, событие `sync_groups_conflict`, повторное получение аккаунта и
`record_sync_failure(…, "Синхронизация уже выполнялась — откройте экран заново")`.
В событие лога идут только собственные значения обработчика — после отката
атрибуты `account` просрочены, и обращение к `account.type` тянуло бы ленивую
догрузку вне greenlet-контекста, то есть новое исключение внутри обработчика
исключения (это и произошло на первом прогоне теста). Добавлен
`test_constraint_conflict_becomes_a_summary_not_a_json_five_hundred`: редирект
вместо 500, след на аккаунте, отсутствие SQL в тексте, откат второй строки.

**Требует внимания человека:** ветка воспроизводится в тесте подменой
`apply_group_resync`, а не настоящей гонкой двух POST-ов — реальный параллельный
сценарий на PostgreSQL тестом не покрыт.

### WR-05: Внешний идентификатор группы молча обрезается до 255 символов

**Files modified:** `app/application/accounts/group_resync.py`, `tests/test_application/test_group_resync.py`
**Commit:** `00df236`
**Applied fix:** обрезка `group_external_id` заменена на пропуск ЭЛЕМЕНТА —
той же реакцией, что уже применяется к любому другому негодному элементу ответа.
Обрезка `name` оставлена как есть (цена ошибки косметическая); комментарий у
`_EXTERNAL_ID_MAX` теперь объясняет, почему реакции разные. Старый тест разделён:
`test_overlong_name_is_trimmed_to_the_column`,
`test_overlong_external_id_skips_the_group_instead_of_trimming_it` (соседняя
годная группа уцелела), `test_two_overlong_ids_sharing_a_prefix_do_not_collapse_into_one`
(побочный путь к `IntegrityError`), `test_nameless_group_falls_back_to_the_id`
(идентификатор ровно на границе колонки).

### IN-01: Мёртвые импорты в `app/worker/tasks.py`

**Files modified:** `app/worker/tasks.py`
**Commit:** `ca00e33`
**Applied fix:** удалены `select`, `joinedload`, `Schedule`, `get_image_url`,
`compute_next_run_at`. Проверено, что ни один тест не патчит эти имена через
`app.worker.tasks.*`.

### IN-02: `record_sync_failure` объявлена `async`, но ничего не ожидает

**Files modified:** `app/application/accounts/group_resync.py`
**Commit:** `4b1e48a`
**Applied fix:** выбран вариант «оставить `async`, но сказать это явно».
В докстринг добавлен раздел, называющий причину (симметрия с
`apply_group_resync`, шесть точек вызова в трёх модулях, первая же будущая
правка с запросом вернула бы `async` обратно) и объявляющий сигнатуру
стабильной.

### IN-03: Заглушка `/groups` объявляет параметр, которым не пользуется

**Files modified:** `app/pages/groups.py`
**Commit:** `994723f`
**Applied fix:** параметр сохранён, причина названа комментарием прямо в
сигнатуре (нужен, чтобы FastAPI принял `{deep_link:path}`; снятие ломает
маршрут), добавлен `# noqa: ARG001`.

### IN-04: «Все группы удалены» показывается аккаунту, у которого групп никогда не было

**Files modified:** `app/templates/account_groups/list.html`, `tests/test_pages/test_account_groups.py`
**Commit:** `8e7eded`
**Applied fix:** ветка пустого состояния различается не только по
`last_synced_at`, но и по сводке: удавшийся синк с `found == 0 and new == 0 and
missing == 0` означает «групп нет». Сводка с `error` в счёт не идёт — при отказе
счётчики нулевые по построению, и принимать их за «групп никогда не было»
значило бы вернуть ту же ложь с другой стороны. Добавлены парные тесты: аккаунт
без чатов читает «Групп пока нет»; сводка с `missing > 0` по-прежнему даёт «Все
группы удалены».

### IN-05: `SyncStatusView.group_count` считается запросом и никогда не используется

**Files modified:** `app/application/accounts/dto.py`, `app/application/accounts/use_cases.py`, `app/pages/accounts.py`, `app/templates/accounts/partials/sync_status_card.html`
**Commit:** `83f7af9`
**Applied fix:** поле убрано из `SyncStatusView`, вместе с ним снят `SELECT
Group.id …` в `get_sync_status_view` (выполнялся на каждый ответ опроса, то есть
раз в 5 секунд на вкладку) и неиспользуемый импорт `Group`; из обработчика убран
`group_count=…`, шаблон читает `stats.get('groups_count', 0)`. Поведение
идентично: `_get_account_stats` кладёт `groups_count` для КАЖДОГО запрошенного
аккаунта, а в ветках `syncing`/`sync_failed` число не печатается вовсе.

### IN-06: `_sync_wa_groups_async` и `_sync_max_groups_async` — посимвольные копии

**Files modified:** `app/worker/tasks.py`
**Commit:** `31ed3dd`
**Applied fix:** введён `_sync_groups_async(account_id, *, messenger_type,
messenger_factory)` с общим телом (опрос, три ветки исхода, таймаут, обработчик
исключения) и две трёхстрочные обёртки `_sync_wa_groups_async` /
`_sync_max_groups_async`, сохранившие прежние имена — параметризованные тесты
`SYNC_PATHS` продолжают импортировать именно их. Имена событий лога выводятся из
`messenger_type` (`sync_wa_groups_error` / `sync_max_groups_error`), а не
передаются третьим рассогласуемым параметром. Фабрики адаптеров вынесены в
`_wa_messenger` / `_max_messenger` с локальными импортами — тесты патчат
`app.messengers.*` и продолжают работать. `POLL_INTERVAL`/`MAX_POLLS` подняты на
уровень модуля.

### IN-07: У слота `caller` в `components/modal.html` нет ни одного продуктового потребителя

**Files modified:** `app/templates/components/modal.html`
**Commit:** `20262c4`
**Applied fix:** докстринг исправлен — утверждение «ПОТРЕБИТЕЛЯ у слота сегодня
нет ни одного» заменено на названного потребителя (`ads/includes/sched_card.html`
кладёт в слот скрытое `return_to`) и на вывод «слот не удаляется: снятие сломало
бы живой путь, а не убрало бы мёртвый код».

### IN-08: `ADD CONSTRAINT` ревизии 0015 берёт исключительную блокировку

**Files modified:** `alembic/versions/0015_groups_unique_account_external.py`
**Commit:** `695a189`
**Applied fix:** выбран вариант «назвать размен в докстринге». Добавлен раздел:
дисциплина 0014 нарушена осознанно, `ACCESS EXCLUSIVE` назван прямо, размен
принят по размеру таблицы, и объяснено, почему `CREATE UNIQUE INDEX
CONCURRENTLY` не может стоять в ЭТОЙ ревизии (индекс строился бы по несхлопнутым
данным, и ревизия должна быть без транзакции) — разделение на две ревизии
объявлено готовым следующим шагом.

### IN-09: Проверка владения в `apply_group_resync` шире ограничения схемы

**Files modified:** `app/application/accounts/group_resync.py`, `tests/test_application/test_group_resync.py`
**Commit:** `fb14859`
**Applied fix:** снято условие `Group.user_id == account.user_id` — скоуп поиска
существующих строк теперь совпадает со скоупом `uq_groups_account_external`
(только `account_id`). Изоляция T-03-06 сохранена: чужая группа висит на чужом
аккаунте, что закреплено существующим
`test_foreign_group_with_same_external_id_untouched`. Добавлен
`test_row_with_a_diverged_user_id_is_updated_not_inserted_again` — тот самый
случай, который прежде превращал безобидное расхождение в отказ синка всего
аккаунта.

## Skipped Issues

Нет — все 15 находок применены.

## Notes

- Каждая правка закоммичена отдельно; порядок коммитов совпадает с порядком
  разделов выше.
- После правок CR-01 и IN-06 менялась структура файлов (новая функция ревизии,
  слияние двух фоновых путей) — их стоит перечитать глазами при верификации, а
  не полагаться только на зелёную суиту.
- WR-04 помечен как требующий человеческой проверки: тест воспроизводит конфликт
  подменой хелпера, а не настоящей параллельной записью.

---

_Fixed: 2026-08-12_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
