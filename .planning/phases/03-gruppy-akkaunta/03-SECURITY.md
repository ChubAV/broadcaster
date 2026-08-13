---
phase: 03
slug: gruppy-akkaunta
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-13
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

Register authored at plan time — all eight PLAN files carry a `<threat_model>` block, so this
audit verified declared mitigations rather than building a register retroactively.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| браузер → `/accounts/{id}/groups` и его паршалы | `account_id`, `offset`, `limit`, `search` приходят из адреса, то есть от недоверенного клиента | идентификаторы аккаунта и группы, строка поиска |
| браузер → POST toggle / delete / sync-groups | разрушительные и дорогие операции инициируются из адреса любым клиентом с валидной cookie | идентификаторы аккаунта и группы |
| мессенджер / мост → хелпер переинвентаризации → БД | `fetched` целиком приходит из внешней системы: и `id`, и `name` недоверенные | внешние идентификаторы и имена групп |
| БД → шаблон | `Group.name` и текст ошибки внешней системы рендерятся в HTML | имена групп, текст ошибки синка |
| одноразовая база ↔ целевая база | команды миграции не должны перепутать адреса | схема и данные групп |
| браузер → старый адрес `/groups` | закладки приходят на адрес, за которым больше нет страницы | — |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-01 | Elevation of Privilege | `GET /accounts/{id}/groups` | high | mitigate | `_load_owned_account` (`app/pages/account_groups.py:65-75`) вызывается на входе `:121`; выборка групп трижды скоуплена `:51` | closed |
| T-03-02 | Elevation of Privilege | `POST .../toggle` | high | mitigate | Тройной WHERE `app/pages/account_groups.py:314-320`; тесты `tests/test_pages/test_account_groups.py:346,367` | closed |
| T-03-03 | Tampering | `account_groups/includes/group_row.html` | medium | mitigate | Autoescape Jinja2; ни одного `\|safe` в шаблонах `account_groups/` | closed |
| T-03-04 | Repudiation | `collect_due_schedules` | low | accept | `app/application/scheduling/use_cases.py:171-177` — `logger.info` + `continue`, записи в SendLog нет (D-06) | closed |
| T-03-05 | Tampering | POST-формы экрана | low | accept | CSRF-токенов нет ни на одной форме проекта; новой поверхности класса не добавлено | closed |
| T-03-06 | Tampering | `apply_group_resync` — выборка существующих групп | high | mitigate | **Реализовано иначе, чем объявлено.** `group_resync.py:185-190` скоупит только по `account_id`. Безопасно: `Group(...)` конструируется единственным местом `:223-231` и всегда ставит `user_id=account.user_id`, поэтому `account_id ⇒ user_id` — инвариант; владение доказано вызывающим (`app/pages/accounts.py:755-766`, `app/worker/tasks.py:300`). Тесты `tests/test_application/test_group_resync.py:568-587,591-619` | closed |
| T-03-07 | Denial of Service | размер ответа мессенджера | medium | accept | Протоколы синхронизации запрещены к правке рамками milestone; действует таймаут опроса воркера | closed |
| T-03-08 | Tampering | `last_sync_result` как JSON-строка | medium | mitigate | `parse_sync_result` (`group_resync.py:336-354`) не бросает: мусор даёт `None` | closed |
| T-03-09 | Destruction of data | ревизия `0014` | high | mitigate | `alembic/versions/0014_...py:40-50` — три `add_column` nullable, без `server_default`, без data-migration | closed |
| T-03-10 | Information Disclosure | имя группы во внешней системе | low | accept | Имена групп хранятся в БД с первой версии; фаза не расширяет их видимость | closed |
| T-03-11 | Elevation of Privilege | выборка групп редактора (`app/pages/ads.py`) | high | mitigate | `app/pages/ads.py:250` сохраняет `Group.user_id == user.id` рядом с расширенным `group_scope` | closed |
| T-03-12 | Information Disclosure | пометка «отключена» | low | accept | Раскрывается состояние собственной группы пользователя | closed |
| T-03-13 | Tampering | рендер имени в списке выбора | medium | mitigate | Autoescape; покрыто обходом всех шаблонов | closed |
| T-03-14 | Elevation of Privilege | `accounts_sync_groups` | high | mitigate | `app/pages/accounts.py:755-760` — проверка владения цела; чужой id уводит на `/accounts` до конструирования мессенджера `:765-766`; тест `tests/test_routes/test_sync_groups.py:505-531` | closed |
| T-03-15 | Denial of Service | повторный запуск синхронизации | medium | mitigate | Внутрипроцессная заявка `_claim_sync_slot` / `_release_sync_slot` (`app/pages/accounts.py`) закрывает повторный запуск **в пределах синхронного HTTP-пути** обработчика `accounts_sync_groups` — всех трёх его веток мессенджера; заявка занимается после проверки владения и до конструирования адаптера, освобождается в `finally` на четырёх выходах (успех, `MessengerFetchError`, широкий отказ, `IntegrityError`). Существующий guard по `account.status` сохранён для фоновых путей WA/MAX. Тесты: `test_second_sync_during_a_running_sync_does_not_reach_the_messenger`, `test_sync_slot_is_per_account`, семейство `test_slot_is_released_*`, `test_sync_does_not_persist_syncing_for_the_page_path`. Остаточные направления — строкой T-03-36, а не умолчанием | closed |
| T-03-16 | Tampering | ответ моста как источник состава групп | medium | mitigate | Прохибиция проверяется отсутствием: ноль вхождений `is_active`, `session.delete`, `.delete(` в `group_resync.py`; пропавшие группы получают только `missing_since` `:274-284`; предохранитель вырожденного ответа `:263-272` | closed |
| T-03-17 | Information Disclosure | текст ошибки в `last_sync_result` | medium | mitigate | В узкую ветку `accounts.py:832` долетает только `MessengerFetchError`, все конструкции — свой текст (`telegram_user.py:265`, `whatsapp.py:130,133`, `max.py:120,123`). `IntegrityError` попасть не может: коммит в своём `try` `:864-866`, обработчик пишет фиксированную строку `:889-891`; широкая ветка пишет `UNEXPECTED_FAILURE_MESSAGE` `:856` | closed |
| T-03-18 | Repudiation | расхождение WA- и MAX-путей | low | mitigate | Параметризация `SYNC_PATHS`, 7 тестов `tests/test_worker/test_tasks.py:390-541`; оба пути сведены в `_sync_groups_async` (`app/worker/tasks.py:300`) | closed |
| T-03-19 | Elevation of Privilege | `GET .../groups/partial` | high | mitigate | `_load_owned_account` на входе `app/pages/account_groups.py:222` | closed |
| T-03-20 | Elevation of Privilege | `POST .../delete` | high | mitigate | Тройной WHERE `:356-362`; чистка расписаний владельцем `ScheduleRepository.remove_group_ids(user.id, ...)` `:370`; тесты `:991,1011,917,941` | closed |
| T-03-21 | Tampering | строка поиска | high | mitigate | Bind-параметр `account_groups.py:56` (f-строка собирает ЗНАЧЕНИЕ шаблона, не SQL); urlencode на слое шаблона — `list.html:190`, `partial_cards.html:17`; эхо под autoescape `components/field.html:10` | closed |
| T-03-22 | Denial of Service | параметры постраничной загрузки | medium | mitigate | `account_groups.py:201-202` — `ge=0`, `ge=1, le=100`; отказ 422 до тела обработчика, то есть до БД | closed |
| T-03-23 | Tampering | имя группы в панели подтверждения | medium | mitigate | Текст, не разметка; ноль `\|safe` | closed |
| T-03-24 | Denial of Service | подсчёт вхождений в `group_ids` в Python | low | accept | `account_groups.py:93-106`, ограничено 30 отрисованными идентификаторами | closed |
| T-03-25 | Elevation of Privilege | `GET .../sync-status` | high | mitigate | `_load_owned_account` `:284`; неаутентифицированному и чужому — пустой `HTMLResponse` `:282,286,291` | closed |
| T-03-26 | Denial of Service | автоматический опрос статуса | high | mitigate | `hx-get`/`hx-trigger`/`hx-swap` объявлены ТОЛЬКО внутри `{% if status == 'syncing' %}` (`partials/sync_result.html:50`); парные тесты `test_account_groups.py:1860-1865,1899,1907-1917,1933-1938` + `source.count("hx-trigger") == 1` `:2080-2082` | closed |
| T-03-27 | Tampering | испорченный сохранённый результат | medium | mitigate | `parse_sync_result` не бросает; шаблон закрыт `{% if sync_result %}` (`list.html:113`), счётчики через `\|int` `:135-138` | closed |
| T-03-28 | Denial of Service | повторный запуск синка с экрана | medium | mitigate | Подпись состояния есть (`list.html:84-85`); недопуск второго запуска — тот же контроль и **та же граница синхронного HTTP-пути**, что у T-03-15 (`_claim_sync_slot` / `_release_sync_slot`, освобождение в `finally`): угроза та же, увиденная со стороны экрана. Закрепляющие тесты перечислены в строке T-03-15; остаточные направления — T-03-36 | closed |
| T-03-29 | Elevation of Privilege | вход создания группы в `app/routes/groups.py` | high | mitigate | Файл удалён целиком (D-14); ноль ссылок в `app/` | closed |
| T-03-30 | Elevation of Privilege | входы списка/удаления/переключения там же | high | mitigate | Удалены вместе с создающим; поведение воспроизведено страничными маршрутами с проверкой владения на каждом входе | closed |
| T-03-31 | Denial of Service | отсутствие тарифного лимита на группы | low | accept | Точки применения лимита не существует (`app/services/billing_cache.py`); решение вне рамок фазы | closed |
| T-03-32 | Repudiation | снятие требования GRP-08 | low | mitigate | Причина, дата и автор в `.planning/REQUIREMENTS.md:156,220,252,257` | closed |
| T-03-33 | Denial of Service | старый адрес раздела | medium | mitigate | `app/pages/groups.py` — безусловный 302 на экран аккаунтов | closed |
| T-03-34 | Elevation of Privilege | потеря проверок владения вместе со снесёнными тестами | high | mitigate | Обе семьи утверждений живут на новом экране: toggle `test_account_groups.py:346,367`, delete `:991,1011`, чистка расписаний `:917,941` | closed |
| T-03-35 | Tampering | заглушка перенаправления | low | accept | `app/pages/groups.py` не читает ни параметров, ни состояния, ни сессии | closed |
| T-03-36 | Denial of Service | повторный синк вне синхронного HTTP-пути обработчика | medium | accept | Два РАЗЛИЧЁННЫХ направления остаточного риска. **(а) Многопроцессная раскладка `web` — сегодня ГИПОТЕТИЧНА:** флаг числа воркеров uvicorn не задан ни в `Dockerfile:30`, ни в `docker-compose.yml:25`, ни в `docker-compose.prod.yml:78`, ни в `justfile:11`, а сервис `web` вдобавок несёт `container_name` (`docker-compose.yml:26`, `docker-compose.prod.yml:79`), то есть репликами не масштабируется без правки файла раскладки; увеличение числа процессов вырождает заявку в защиту на процесс. **(б) Асимметрия «страничный синк ↔ фоновый синк» — РЕАЛЬНА УЖЕ СЕГОДНЯ:** тот же `apply_group_resync` вызывается фоновым `_sync_groups_async` (`app/worker/tasks.py:300`, вызов хелпера `:331`), а `celery-worker-telegram` раскладывается двумя репликами (`docker-compose.yml:61-62`, `deploy: replicas: 2`); сверх того страничный путь по построению не пишет `account.status`, поэтому фоновый повтор, запущенный из `accounts_retry_sync` (`app/pages/accounts.py:732`) во время идущего страничного синка, внутрипроцессной заявкой не виден и не блокируется. Кросс-процессный запас для ОБОИХ направлений — `uq_groups_account_external` (ревизия 0015) и ветка `IntegrityError` (`app/pages/accounts.py`): дублирующие СТРОКИ исключены, дублирующий внешний запрос — нет. Оба направления названы комментарием в точке заявки | open — below high threshold (non-blocking) |
| T-03-37 | Destruction of data | ревизия `0015_groups_unique_account_external.py` | high | mitigate | **Что делает ревизия и чем отличается от 0014.** T-03-09 её НЕ покрывает: та строка сознательно ограничивает себя ревизией `0014` («только additive nullable, без data-migration»), и читать её как характеристику всей фазы неверно. Ревизия 0015 разрушительна: сливает дубли через `UPDATE` (`_MERGE_IS_ACTIVE`, `_MERGE_MISSING_SINCE`), перезаписывает `schedules.group_ids` (`_remap_schedule_group_ids`, вызов `:223`), выполняет `DELETE FROM groups` — оператор объявлен константой `_DROP_DUPLICATES` `:208-216`, сама строка `DELETE FROM groups` — `:210`, исполнение — `:224` — и строит уникальное ограничение `uq_groups_account_external` (`:226-229`), берущее на PostgreSQL `ACCESS EXCLUSIVE` на таблицу `groups`: на время построения таблица недоступна и на чтение. **Доказательная база.** Восемь тестов `tests/test_migrations/test_0015_groups_unique_account_external.py`, включая перенос ссылок расписаний ДО удаления строк (`test_schedule_reference_to_a_dropped_duplicate_is_remapped`) и обратную миграцию (`test_downgrade_removes_the_constraint`). Безопасным удаление делает именно ПОРЯДОК операций в `upgrade` (`:219-229`): слияние → перезапись ссылок расписаний → удаление → ограничение. **Дисциплина применения, перенесённая с 0014.** Применение доказывается на одноразовой базе; программный guard по `hostname`/`port`/`dbname` обязателен и проверяется на отказ; целевая база не адресуется ни одной командой. На момент записи целевая база остаётся на ревизии `0012` (`.planning/STATE.md`, раздел Blockers/Concerns), то есть ни 0013, ни 0014, ни 0015 в прод не выкачены — записанная дисциплина есть ОБЯЗАТЕЛЬСТВО перед выкатом, а не отчёт о состоявшемся применении. **Названный размен и порог его пересмотра.** Окно блокировки принято по размеру таблицы; ревизия сама называет готовый следующий шаг — разделение на две ревизии с `CREATE UNIQUE INDEX CONCURRENTLY` и `ADD CONSTRAINT ... USING INDEX` — если таблица вырастет настолько, что окно станет заметным (`:44-55`). Порог назван заранее, а не обнаруживается инцидентом | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Open Threats (non-blocking)

One remains, medium, below the configured `block_on: high` threshold, so it does not count
toward `threats_open`. T-03-15 and T-03-28 are now **closed** — plan 03-09 implemented the
in-process sync slot (`_claim_sync_slot` / `_release_sync_slot` in `app/pages/accounts.py`,
released in `finally` on all four handler exits), so two concurrent POSTs no longer both reach
the messenger. What that control does *not* cover is registered below under its own identifier
rather than left as a footnote.

**T-03-36 — the claim is in-process, so it does not cover repeat syncs outside the synchronous
HTTP path.** Two *distinct* directions, and they differ in whether they are real today:

**(a) A multi-process `web` deployment — hypothetical today.** The uvicorn worker-count flag is
set nowhere: `Dockerfile:30`, `docker-compose.yml:25`, `docker-compose.prod.yml:78`,
`justfile:11`. The `web` service additionally carries `container_name`
(`docker-compose.yml:26`, `docker-compose.prod.yml:79`), so it cannot be scaled by replicas
without editing the deployment file. Should the process count ever grow, the claim degrades to
a per-process guard.

**(b) The page-sync ↔ background-sync asymmetry — real *as deployed today*.** The same
`apply_group_resync` is called by the background `_sync_groups_async`
(`app/worker/tasks.py:300`, helper call `:331`), and `celery-worker-telegram` is deployed with
two replicas (`docker-compose.yml:61-62`, `deploy: replicas: 2`). On top of that the page path
deliberately never writes `account.status`, so a background re-sync dispatched from
`accounts_retry_sync` (`app/pages/accounts.py:732`) *while a page sync is running* is invisible
to the in-process claim and is not blocked by it. This is a statement of the current state, not
a condition on the future — the phrasing "the control is complete as deployed today" would be
false for this direction.

Compensating control for both directions: the schema-level `uq_groups_account_external`
(revision 0015) plus the `IntegrityError` branch in `accounts_sync_groups` prevent duplicate
*rows*. They do not prevent the duplicate outbound fetch. Both directions are also named in the
code comment at the claim site.

---

## Unregistered Findings (carry into next phase)

1. **Revision `0015_groups_unique_account_external.py` has no threat ID.** It performs `UPDATE`
   merges, rewrites `schedules.group_ids`, executes `DELETE FROM groups` (`:210-224`), and takes
   `ACCESS EXCLUSIVE` on `groups` while building the unique index (self-documented at `:44-55`).
   The register's only destruction-of-data entry, T-03-09 (high), scopes itself explicitly to
   revision **0014** as "additive nullable only, no data-migration". Revision 0015 arrived later
   via code-review fix WR-03 (commit `cd4714b`) and CR-01 (commit `96affc3`), and appears in no
   `<threat_model>` and no SUMMARY `## Threat Flags`. It is well covered by
   `tests/test_migrations/test_0015_groups_unique_account_external.py` (8 tests, including
   remap-before-delete and downgrade), but the throwaway-database + hostname/port/dbname guard
   discipline that T-03-09 demanded for 0014 has no recorded application to 0015.

2. **T-03-06's register text is stale.** The recorded mitigation ("double scope `account_id AND
   user_id`") no longer describes the code — IN-09 (commit `fb14859`) deliberately narrowed the
   lookup to match `uq_groups_account_external`. The threat is closed on the merits, but the
   register wording should be updated to the implemented control, or a future audit will read a
   false mitigation as evidence.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-03-01 | T-03-04 | Пропуск выключенной группы фиксируется только structlog-событием; запись в SendLog прямо запрещена D-06 — история обязана отражать реальные попытки отправки | chubav | 2026-08-12 |
| R-03-02 | T-03-05 | CSRF-токенов нет ни на одной форме проекта; новые формы не хуже существующих. Общесистемное решение — вне рамок фазы | chubav | 2026-08-12 |
| R-03-03 | T-03-07 | Ограничения на длину ответа мессенджера фаза не вводит: протоколы синхронизации запрещены к правке рамками milestone | chubav | 2026-08-12 |
| R-03-04 | T-03-10 | Имена групп хранятся в БД с первой версии продукта; фаза не расширяет их видимость | chubav | 2026-08-12 |
| R-03-05 | T-03-12 | Пометка раскрывает состояние собственной группы пользователя — новой информации о чужих данных не появляется | chubav | 2026-08-12 |
| R-03-06 | T-03-24 | Обход выполняется для 30 отрисованных строк; агрегация по всей таблице расписаний не выполняется | chubav | 2026-08-12 |
| R-03-07 | T-03-31 | Лимита на количество групп не существует и точки его применения нет; удаление входа состояние не меняет | chubav | 2026-08-12 |
| R-03-08 | T-03-35 | Заглушка не принимает параметров и не читает состояния: перенаправление безусловно | chubav | 2026-08-12 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-13 | 35 | 33 | 2 (both below `block_on: high`) | gsd-security-auditor |
| 2026-08-13 | 36 | 35 | 1 (below `block_on: high`) | gsd-executor (план 03-09) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-13
