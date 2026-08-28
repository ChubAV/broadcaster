---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 03
subsystem: payments
tags: [alembic, sqlite, postgresql, partial-unique-index, batch-alter-table, yookassa, jinja2]

requires:
  - phase: 05-oplata-i-podpiska
    provides: "ревизии 0017/0018/0019 — прецеденты batch-режима, зачистки перед индексом и одностороннего отката; _open_subscription_intents и TERMINAL_STATUSES"
  - phase: 07-admin
    provides: "PAY_LABELS обоих экранов и общий словарь состояний платежа (D-14)"
provides:
  - "Ревизия 0021: потолок незакрытых подписочных намерений стал свойством СХЕМЫ — частичный уникальный индекс uq_payments_open_subscription_intent на payments(user_id) WHERE kind = 'subscription' AND status = 'pending'"
  - "Зачистка существующих строк в той же ревизии до индекса: выживает новейшее намерение, остальные → expired"
  - "yookassa_payment_id допускает NULL при сохранённой уникальности — колонка под порядок «резерв → сеть → дозапись» плана 08-05"
  - "Статус expired назван русским словом на экране пользователя и администратора"
  - "Строка предиката OPEN_INTENT_PREDICATE — единственный источник формулировки, который план 08-05 переносит в __table_args__ модели"
affects: [08-05, 08-10]

actuals:
  tokens: 14300
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Зачистка данных и создание ограничения — в ОДНОЙ ревизии, зачистка первой (0018 → 0021)"
    - "Предикат частичного индекса — ОДНА именованная константа, повторно использованная в sqlite_where и postgresql_where"
    - "Отказ уникального ограничения разбирается ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ, а не текстом ошибки: имени индекса в тексте SQLite нет"

key-files:
  created:
    - alembic/versions/0021_payments_open_intent_index.py
    - tests/test_migrations/test_0021_payments_open_intent_index.py
  modified:
    - app/models/payment.py
    - app/templates/billing/balance.html
    - app/templates/admin/payments.html
    - tests/test_pages/test_billing_section.py
    - tests/test_pages/test_admin_payments.py

key-decisions:
  - "Владелец ответил `proceed` на чекпойнт односторонней двери: ревизия пишется как спроектировано под D-01/D-03/D-05, вариант `split` отвергнут явно"
  - "Предикат частичного индекса выписан ОДНОЙ константой OPEN_INTENT_PREDICATE, а не двумя дословными литералами: две копии одной строки могут разойтись молча, чего сквозной принцип фазы «один источник вместо второй копии» не допускает"
  - "Разбор IntegrityError по имени ограничения признан неработоспособным на SQLite и заменён перечитыванием состояния (прецедент _extend_subscription) — это меняет проектирование плана 08-05"
  - "downgrade НЕ возвращает NOT NULL на yookassa_payment_id: к моменту отката в таблице могут лежать резервные строки с NULL, и возврат ограничения оборвал бы откат"

patterns-established:
  - "Один источник формулировки предиката: строка живёт константой в ревизии и оттуда копируется в __table_args__ модели"
  - "Порядок шагов миграции, не проверяемый поведением на чистой базе, утверждается номерами строк исходника"
  - "Запрет импорта из app.* в ревизии проверяется РАЗБОРОМ ДЕРЕВА (ast), а не подстрокой: подстрока ловит комментарии"

requirements-completed: []

coverage:
  - id: D1
    description: "Второе незакрытое подписочное намерение того же пользователя отвергается СУБД, а не прикладной проверкой"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_upgrade_rejects_a_second_open_subscription_intent"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_upgrade_creates_the_partial_unique_index"
        status: pass
    human_judgment: false
  - id: D2
    description: "Предикат частичный: проведённый, просроченный и пакетный платёж рядом с намерением проходят"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_the_index_is_partial_and_lets_the_neighbours_through"
        status: pass
    human_judgment: false
  - id: D3
    description: "Зачистка идёт до индекса и оставляет НОВЕЙШЕЕ намерение; ничья разрывается наибольшим id; строки переводятся, а не удаляются"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_backfill_keeps_the_newest_open_intent"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_backfill_breaks_an_exact_tie_by_highest_id"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_backfill_expires_rather_than_deletes"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_the_backfill_runs_before_the_index_is_created"
        status: pass
    human_judgment: false
  - id: D4
    description: "Чужие строки, проведённые платежи и пакеты зачисткой не тронуты; на чистых данных накат не меняет ни одной строки"
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_backfill_leaves_other_users_and_other_kinds_alone"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_upgrade_on_clean_data_changes_no_row"
        status: pass
    human_judgment: false
  - id: D5
    description: "yookassa_payment_id принимает NULL, резервы сосуществуют, а уникальность непустых значений переживает batch-пересоздание таблицы"
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_upgrade_makes_the_payment_id_nullable_and_null_rows_coexist"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_the_unique_index_on_the_payment_id_survives_the_batch_recreate"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_model_matches_head.py#test_every_mapped_payment_column_exists_at_head"
        status: pass
    human_judgment: false
  - id: D6
    description: "downgrade снимает индекс, но не восстанавливает переведённые строки и не возвращает NOT NULL"
    verification:
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_downgrade_drops_the_index_and_accepts_a_second_intent_again"
        status: pass
      - kind: integration
        ref: "tests/test_migrations/test_0021_payments_open_intent_index.py#test_downgrade_does_not_restore_the_expired_rows"
        status: pass
    human_judgment: false
  - id: D7
    description: "Статус expired печатается человеку и администратору словом «просрочен», а не сырым латинским идентификатором"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_section.py#test_an_expired_intent_is_printed_in_words"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_payments.py#test_an_expired_intent_is_printed_in_words"
        status: pass
    human_judgment: false
  - id: D8
    description: "Число тронутых строк уходит в журнал наката, а предупреждение о неполноте отката — в журнал отката"
    verification:
      - kind: other
        ref: "logger.info/logger.warning в alembic/versions/0021_payments_open_intent_index.py; сообщение наблюдалось в stderr прогона (`0021: expired 2 stale open subscription intent row(s)`)"
        status: pass
    human_judgment: true
    rationale: "Утверждение о СОДЕРЖАНИИ журнальной записи — про читаемость её человеком в момент боевого наката. Тест на текст сообщения проверял бы совпадение строки с самой собой; полезен здесь только человеческий взгляд на формулировку."
  - id: D9
    description: "Строка, переведённая зачисткой в expired, остаётся оплачиваемой и зачисляемой — оплата по старой ссылке будет принята"
    requirement: PAY-01
    verification: []
    human_judgment: true
    rationale: "Свойство держится тем, что expired не входит в TERMINAL_STATUSES и что _claim_payment написан через это множество. Обработчик уведомления правит план 08-05; до его выполнения утверждение доказывается ЧТЕНИЕМ кода, а не прогоном, и обязано быть перепроверено человеком после 08-05."

duration: 22 min
completed: 2026-08-28
status: complete
---

# Phase 08 Plan 03: Денежный потолок свойством схемы Summary

**Ревизия `0021`: частичный уникальный индекс `uq_payments_open_subscription_intent` на `payments(user_id)`, зачистка существующих незакрытых намерений в той же ревизии (выживает новейшее, остальные → `expired`) и снятие `NOT NULL` с `yookassa_payment_id` batch-режимом под будущий порядок «резерв → сеть → дозапись»**

## Performance

- **Duration:** 22 min
- **Started:** 2026-08-28T12:03:00Z (приблизительно; первый коммит — 12:16:09Z)
- **Completed:** 2026-08-28T12:25:33Z
- **Tasks:** 3 (плюс чекпойнт решения, снятый ответом владельца)
- **Files modified:** 7 (2 создано, 5 изменено)

## Accomplishments

- **Потолок стал свойством СХЕМЫ, а не проверкой в коде.** Вторая незакрытая подписочная строка того же пользователя отвергается СУБД. Прикладная проверка, которую две одновременные отправки формы проходили обе, перестаёт быть последней линией — снимает её план 08-05.
- **Зачистка существующих строк живёт в ТОЙ ЖЕ ревизии и идёт ДО индекса.** Правило выжившей — новейшее намерение (`MAX(created_at)`, тай-брейк `MAX(id)`) — выписано в докстринге прямо, а не оставлено выводимым из SQL, и проверено тремя тестами. Проигравший зачистку **ничего не теряет**: `expired` не входит в терминальные статусы.
- **`yookassa_payment_id` допускает `NULL` при сохранённой уникальности**, и уникальность переживает batch-пересоздание таблицы — это утверждает тест, а не надежда (T-08-15).
- **Новый статус назван человеку и администратору одним русским словом** — «просрочен», тоном `neutral`, а не `danger`.
- **Найдена и записана ошибка проектирования плана 08-05:** разбор `IntegrityError` «по имени ограничения» на SQLite не работает никогда (см. «Issues Encountered»).

## Task Commits

1. **Task 1 (RED): failing round-trip test for revision 0021** — `547409a` (test)
2. **Task 1 (GREEN): revision 0021 — cleanup, nullable payment id, partial unique index** — `444a044` (feat)
3. **Task 2: yookassa_payment_id допускает NULL при сохранённой уникальности** — `da4a577` (feat)
4. **Task 3: статус expired назван русским словом на обоих экранах** — `7bccb6e` (feat)

Фазы REFACTOR не было: чистить в ревизии оказалось нечего.

## Files Created/Modified

- `alembic/versions/0021_payments_open_intent_index.py` — зачистка → batch-снятие `NOT NULL` → частичный уникальный индекс; односторонний `downgrade` с предупреждением
- `tests/test_migrations/test_0021_payments_open_intent_index.py` — 17 утверждений round-trip: индекс, частичность, правило выжившей, ничья, перевод вместо удаления, nullable, переживание batch-пересоздания, односторонность отката, линейность истории, порядок шагов, запрет импорта из `app.*`
- `app/models/payment.py` — `yookassa_payment_id: Mapped[str | None]`, `nullable=True`; абзац о том, что единственное состояние без значения — резерв
- `app/templates/billing/balance.html` — `'expired': ('просрочен', 'neutral')` в `PAY_LABELS`
- `app/templates/admin/payments.html` — та же запись, тем же словом
- `tests/test_pages/test_billing_section.py` — `test_an_expired_intent_is_printed_in_words`
- `tests/test_pages/test_admin_payments.py` — `test_an_expired_intent_is_printed_in_words`

## Decisions Made

**Чекпойнт задачи 1 (односторонняя дверь) — ответ владельца: `proceed`, 2026-08-28.** Ревизия написана как спроектировано под D-01 / D-03 / D-05: зачистка, снятие `NOT NULL` и построение индекса — всё в ревизии `0021`. Вариант `split` (две ревизии) отвергнут владельцем явно. Чекпойнт не переспрашивался.

**Предикат — одна константа, а не два дословных литерала.** План требовал повторить `kind = 'subscription' AND status = 'pending'` дословно в `sqlite_where` и `postgresql_where`. Формулировка выписана ОДИН раз константой `OPEN_INTENT_PREDICATE` и оттуда подставлена в оба параметра. Требование плана было про ОДНУ формулировку («это та самая строка, которую 08-05 переносит символ в символ»), и константа даёт его строже: две копии одной строки в одном файле могут разойтись при правке молча — ровно то, что сквозной принцип фазы «один источник вместо второй копии» запрещает. Для 08-05 ничего не меняется: строка по-прежнему выписана в ревизии ровно один раз и копируется оттуда.

**`downgrade` не возвращает `NOT NULL`.** Односторонность стала двойной, и это названо в докстринге: к моменту отката в таблице уже могут лежать резервные строки с `NULL` в колонке, и возврат ограничения оборвал бы откат на них. Выбор между «откат падает» и «колонка остаётся нулевой» сделан в пользу второго — проходимость отката важнее полноты возврата схемы.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Утверждение об имени ограничения в тексте `IntegrityError` невыполнимо на SQLite**

- **Found during:** Task 1 (GREEN-фаза)
- **Issue:** Приёмочный критерий плана требовал: «вторая строка … поднимает `IntegrityError` **с именем ограничения в тексте**». Тест, написанный по этому критерию, упал: SQLite сообщает `UNIQUE constraint failed: payments.user_id` — то есть КОЛОНКУ, а не индекс. Имя индекса приводит только PostgreSQL. Критерий не был бы выполним никакой правкой ревизии.
- **Fix:** Утверждение переписано на факт диалекта (`payments.user_id` в тексте отказа), а расхождение двух диалектов названо и в докстринге теста, и в докстринге ревизии — вместе с указанием на дословный прецедент проекта: `_extend_subscription` тексту отказа НЕ доверяет вовсе, а ловит `IntegrityError`, перечитывает состояние и, не найдя чужой строки, поднимает тот же объект заново.
- **Files modified:** `tests/test_migrations/test_0021_payments_open_intent_index.py`, `alembic/versions/0021_payments_open_intent_index.py`
- **Verification:** `uv run pytest tests/test_migrations/ -q` → 102 passed
- **Committed in:** `444a044`

**2. [Rule 3 - Blocking] План называл неверный адрес происхождения таблицы `payments`**

- **Found during:** Task 1 (сбор DDL для round-trip-теста)
- **Issue:** План велел собрать состав колонок «по `0001_initial_schema.py` + `0017` + `0019`». В `0001_initial_schema.py` таблицы `payments` НЕТ ВОВСЕ — её заводит `0009_add_message_balance_and_payment_tables.py`.
- **Fix:** Снимок собран по фактическим адресам; правильные адреса названы в докстринге тестового файла, чтобы следующий читатель не повторил поиск.
- **Files modified:** `tests/test_migrations/test_0021_payments_open_intent_index.py`
- **Verification:** `command.upgrade` от штампа `0020` проходит; 17 тестов файла зелёные
- **Committed in:** `547409a` / `444a044`

**3. [Rule 2 - Missing Critical] Имя индекса не было названо в докстринге ревизии**

- **Found during:** Task 1 (сверка приёмочных критериев)
- **Issue:** Абзац «ГРАНИЦА ОГРАНИЧЕНИЯ» описывал индекс, ни разу его не назвав: читатель, ищущий ограничение по имени из журнала отказа, в докстринге его не нашёл бы.
- **Fix:** Имя вписано в абзац.
- **Files modified:** `alembic/versions/0021_payments_open_intent_index.py`
- **Verification:** `grep -c 'uq_payments_open_subscription_intent' …` → 2 (критерий требовал ≥ 2)
- **Committed in:** `444a044`

---

**Total deviations:** 3 auto-fixed (1 bug, 1 blocking, 1 missing critical)
**Impact on plan:** Ни одна правка не изменила предмет плана. Первая — существенна и переносится в 08-05 (см. ниже); вторая и третья — поправки к адресам и полноте объяснения.

## Documentation drift (проверено оркестратором, дизайн НЕ меняется)

Место ревизии `0021` в невыкаченной очереди названо неверно В ОБОИХ исходных документах фазы:

| Источник | Утверждает | Проверенный факт |
|---|---|---|
| `08-CONTEXT.md` (D-03) | `0021` встанет **десятой** | неверно |
| `08-PATTERNS.md` | **девятой** (со ссылкой на D-26 Фазы 5, «бой на `0012`») | неверно |
| Проверено оркестратором: `ls alembic/versions/` → голова репозитория `0020`; докстринг `tests/test_migrations/test_model_matches_head.py` → «на 2026-08-21 бой проверен `alembic current` и стоит на `0019`» | — | **`0021` встанет ВТОРОЙ** |

**Существо довода D-03 расхождением НЕ ЗАТРОНУТО:** «зачистка обязана идти в той же ревизии» — довод про АТОМАРНОСТЬ, а не про номер в очереди. Докстринг ревизии написан по ФАКТУ («ВТОРОЙ НЕВЫКАЧЕННОЙ»), а не по D-03. Сами документы фазы этим планом не правились: они принадлежат оркестратору.

## Issues Encountered

**⚠️ ЧИТАТЬ ПЕРЕД ВЫПОЛНЕНИЕМ ПЛАНА 08-05 — НАЙДЕНО ЗДЕСЬ, ЛЕЧИТЬ ТАМ.**

D-06 предписывает поднимать `PendingIntentCapError` «из разбора `IntegrityError` **по имени ограничения**». Эта формулировка неработоспособна на диалекте, по которому идёт ВСЯ суита проекта: SQLite имени индекса в тексте отказа не приводит вовсе (`UNIQUE constraint failed: payments.user_id`), имя приводит только PostgreSQL. Разбор по имени зеленел бы на бою и молчал бы на каждом тесте — то есть дефект ловился бы пользователем.

Прецедент, на который D-06 САМО ССЫЛАЕТСЯ, тексту отказа не доверяет и правильный приём уже показывает: `_extend_subscription` (`app/services/payment_service.py:809-822`) ловит `IntegrityError`, ПЕРЕЧИТЫВАЕТ состояние и, если чужой строки не нашлось, поднимает тот же объект заново. Приём диалекта не касается и переносится в 08-05 без правок. Факт записан в двух местах кода, чтобы не потеряться: докстринг ревизии `0021` (абзац «РАЗБИРАТЬ ОТКАЗ ПО ИМЕНИ ОГРАНИЧЕНИЯ НЕЛЬЗЯ») и докстринг теста `test_upgrade_rejects_a_second_open_subscription_intent`.

Прочих проблем не было.

## Known Stubs

Заглушек нет. Незавершённого по замыслу — ДВА пункта, и оба перенесены планом сознательно, а не забыты:

1. **Индекс объявлен только ревизией, но не моделью.** Схема, поднятая из моделей (`Base.metadata.create_all` в `tests/conftest.py`), об Alembic не знает: для всей обычной суиты индекса физически нет. Объявление в `__table_args__` переносит план 08-05 ВМЕСТЕ с ленивой уборкой — включить потолок раньше уборки значило бы запереть каждого владельца просроченного намерения (`test_a_stale_intent_does_not_block_a_new_one` покраснел бы). Это порядок работ, названный в плане прямо, а не половинчатость.
2. **Константа `STATUS_EXPIRED` в сервисе не заведена.** Статус сегодня существует строкой в ревизии и подписью в двух шаблонах; константу и всё поведение вокруг неё заводит план 08-05.

## Threat Flags

Новых поверхностей сверх `<threat_model>` плана не появилось.

## User Setup Required

None — внешних сервисов план не касается. **Операционное замечание:** ревизия меняет ДАННЫЕ денежной таблицы и необратима в этой половине; число тронутых строк на бою станет известно только из журнала наката (`0021: expired N stale open subscription intent row(s)`).

## Next Phase Readiness

- **Готово для 08-05:** колонка `yookassa_payment_id` допускает `NULL`; индекс существует в схеме Alembic; строка предиката выписана один раз и копируется оттуда символ в символ.
- **Блокирует 08-05 до прочтения:** ошибка проектирования «разбор по имени ограничения» (см. «Issues Encountered»). Переносить в 08-05 нужно приём `_extend_subscription`, а не букву D-06.
- **Не сделано намеренно:** объявление индекса в `__table_args__` модели и константа `STATUS_EXPIRED` — оба в 08-05, одной задачей вместе с ленивой уборкой и переводом отказа в свой тип.

## Self-Check: PASSED

- Файлы на диске: `alembic/versions/0021_payments_open_intent_index.py`, `tests/test_migrations/test_0021_payments_open_intent_index.py`, `app/models/payment.py`, `app/templates/billing/balance.html`, `app/templates/admin/payments.html` — все найдены.
- Коммиты в истории: `547409a`, `444a044`, `da4a577`, `7bccb6e` — все найдены.
- Плановая верификация:
  - `uv run pytest tests/test_migrations/ -q` → **102 passed**
  - `uv run pytest tests/test_pages/test_billing_section.py tests/test_pages/test_admin_payments.py -q` → **77 passed**
  - `uv run pytest tests/test_services/ -q` → **200 passed**
  - `uv run python -m compileall -q app main.py tests` → **код 0**

---
*Phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy*
*Completed: 2026-08-28*
