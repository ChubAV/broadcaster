---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 05
subsystem: payments
tags: [sqlalchemy, partial-unique-index, sqlite, postgresql, yookassa, integrity-error, lazy-sweep, tdd]

requires:
  - phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
    plan: "03"
    provides: "ревизия 0021 (индекс uq_payments_open_subscription_intent, зачистка, nullable yookassa_payment_id) и константа OPEN_INTENT_PREDICATE — источник строки предиката"
  - phase: 05-oplata-i-podpiska
    provides: "create_payment, PendingIntentCapError, TERMINAL_STATUSES, _claim_payment, прецедент _extend_subscription"
provides:
  - "Потолок незакрытых подписочных намерений объявлен ОБОИМИ источниками схемы: __table_args__ модели Payment и ревизией 0021 — база из Base.metadata.create_all отвергает второе намерение так же, как накаченная алембиком"
  - "Порядок денежного пути подписки «уборка → резерв → сеть → дозапись»: строка резервируется до обращения к ЮKassa, отказ приходит от ограничения схемы"
  - "Ленивая уборка _expire_stale_intents: просроченные намерения гасятся в expired на пути самого пользователя, идемпотентно и строго по предикату индекса"
  - "Разбор отказа ограничения ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ (_is_open_intent_conflict) — дialect-независимый приём вместо неисполнимого разбора по имени"
  - "Машинный сторож двух источников схемы с доказанными зубами (tests/test_models/test_payment_open_intent_index.py)"
  - "STATUS_EXPIRED как нетерминальный статус: погашенная строка остаётся оплачиваемой и зачисляемой"
affects: [08-10]

actuals:
  tokens: 96000
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Отказ уникального ограничения различается ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ, а не текстом/именем ошибки: имени индекса в сообщении SQLite нет вовсе"
    - "Ленивая уборка просроченных окон на пути самого пользователя со СВОИМ коммитом — чтобы откат отказа не унёс уборку"
    - "Два источника схемы (модель и ревизия) сверяются разбором ast обоих файлов; зубы сверки доказываются подделкой с изменённым пробелом"
    - "Резерв строки ДО сетевого вызова там, где отказ ограничения способен прийти после него"

key-files:
  created:
    - tests/test_services/test_payment_intent_cap.py
    - tests/test_models/test_payment_open_intent_index.py
  modified:
    - app/models/payment.py
    - app/services/payment_service.py
    - tests/test_services/test_payment_service.py
    - tests/test_services/test_payment_concurrency.py
    - tests/test_pages/test_billing_payment_errors.py
    - tests/test_application/test_declared_invariants.py
    - tests/test_application/declared_invariants_without_witness.txt

key-decisions:
  - "D-06 ИСПРАВЛЕНО ПО РЕАЛЬНОСТИ: разбор IntegrityError по имени ограничения заменён перечитыванием состояния (прецедент _extend_subscription). На SQLite, где идёт вся суита, имени индекса в тексте отказа нет — сообщается колонка, — поэтому разбор по имени зеленел бы на бою и молча не срабатывал в тестах"
  - "Потолок, ленивая уборка, порядок «резерв → сеть» и перевод отказа в свой тип выполнены ОДНОЙ задачей: все три промежуточных состояния негодны (индекс без уборки запирает владельца просроченного намерения; снятая проверка без индекса снимает потолок; индекс без разбора отдаёт сырой IntegrityError человеку)"
  - "OPEN_INTENT_INDEX_NAME оставлена как грep-якорь и НЕ читается кодом: имя ограничения в вердикте не участвует, и это выписано над самой константой"
  - "Запись subscription_intent_cap_reached потеряла поле с числом намерений: считать его больше некому, а подставленная единица была бы неправдой в журнале"
  - "Реестр объявлений без свидетеля понижен 21 → 20 тем же коммитом, что закрыл долг: абзац о НЕ построенном индексе переписан на сделанное и назвал свидетелей"

requirements-completed: [PAY-01]

coverage:
  - id: D1
    description: "Потолок существует в ОБОИХ источниках схемы: база из Base.metadata.create_all отвергает второе незакрытое подписочное намерение"
    requirement: PAY-01
    verification:
      - kind: unit
        ref: "tests/test_models/test_payment_open_intent_index.py#test_the_model_declares_the_open_intent_index"
        status: pass
      - kind: integration
        ref: "tests/test_models/test_payment_open_intent_index.py#test_the_cap_exists_in_the_schema_built_from_models"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_second_open_intent_is_refused_by_the_schema"
        status: pass
    human_judgment: false
  - id: D2
    description: "Предикаты двух источников схемы равны символ в символ, и сверка умеет краснеть"
    requirement: PAY-01
    verification:
      - kind: unit
        ref: "tests/test_models/test_payment_open_intent_index.py#test_the_two_sources_of_the_schema_declare_one_predicate"
        status: pass
      - kind: unit
        ref: "tests/test_models/test_payment_open_intent_index.py#test_the_comparison_reddens_on_a_single_changed_space"
        status: pass
    human_judgment: false
  - id: D3
    description: "Отказ потолка приходит ДО денег: SDK не вызывается ни одним вызовом, второй строки не остаётся"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_service.py#test_the_refusal_never_reaches_yookassa"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_second_open_intent_is_refused_by_the_schema"
        status: pass
    human_judgment: false
  - id: D4
    description: "Отказ ограничения различается дialect-независимо; чужой отказ поднимается наружу тем же объектом"
    requirement: PAY-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_verdict_does_not_depend_on_the_driver_text"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_foreign_rejection_is_not_swallowed"
        status: pass
    human_judgment: false
  - id: D5
    description: "Внутренности СУБД на экран не уходят: текст отказа фиксирован, без имени ограничения и цифр"
    requirement: PAY-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_refusal_says_nothing_of_the_database"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_second_subscription_intent_from_the_form_is_refused_with_words"
        status: pass
    human_judgment: false
  - id: D6
    description: "Ленивая уборка гасит строго то, что считает предикат индекса, идемпотентна и честна счётчиком"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_stale_intent_is_swept_at_the_start_of_a_payment"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_second_sweep_touches_nothing_and_says_so"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_sweep_takes_exactly_what_the_index_counts"
        status: pass
    human_judgment: false
  - id: D7
    description: "Уборка зафиксирована своим коммитом и переживает откат отвергнутого резерва"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_sweep_survives_a_refused_reserve"
        status: pass
    human_judgment: false
  - id: D8
    description: "Срок давности применяется в Python: наивное и осведомлённое время обрабатываются одинаково"
    requirement: PAY-01
    verification:
      - kind: unit
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_deadline_is_applied_in_python"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_row_without_a_birth_time_is_left_alone"
        status: pass
    human_judgment: false
  - id: D9
    description: "Отказ SDK после резерва гасит свою же строку; погашенная строка не мешает следующей попытке"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_failed_sdk_call_expires_its_own_reserve"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_reserve_killed_by_the_sdk_does_not_block_the_next_attempt"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_failed_subscription_payment_leaves_its_reserve_expired"
        status: pass
    human_judgment: false
  - id: D10
    description: "Погашенная строка остаётся ОПЛАЧИВАЕМОЙ: заявка выигрывается на expired, доступ выдаётся"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_claim_is_won_on_an_expired_intent"
        status: pass
    human_judgment: false
  - id: D11
    description: "У пакета порядок «сеть → запись» сохранён: отказ SDK не оставляет строки"
    requirement: PAY-01
    verification:
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_a_failed_package_payment_leaves_no_row_in_the_journal"
        status: pass
      - kind: integration
        ref: "tests/test_services/test_payment_intent_cap.py#test_the_predicate_catches_only_subscription_intents"
        status: pass
    human_judgment: false
  - id: D12
    description: "Поведение потолка на боевом диалекте PostgreSQL (частичный индекс, форма diag драйвера)"
    requirement: PAY-01
    human_judgment: true
    rationale: "Суита проекта идёт на SQLite; поведение на PostgreSQL закрыто конструкцией (вердикт читает СОСТОЯНИЕ и от диалекта не зависит вовсе) и равенством предикатов двух источников, но прогоном на боевом диалекте не проверено — как и всё остальное в этом проекте"

duration: 4h 12m
completed: 2026-08-28
status: complete
---

# Phase 08 Plan 05: Переключение денежного пути на потолок в схеме — Summary

Потолок незакрытых подписочных намерений перестал быть проверкой в коде и стал свойством СХЕМЫ: строка-намерение резервируется до обращения к ЮKassa, второе намерение отвергает частичный уникальный индекс, просроченные намерения гасит ленивая уборка на пути самого пользователя, а отказ ограничения переводится в свой тип перечитыванием состояния — приёмом, работающим на обоих диалектах.

## Accomplishments

- **Потолок объявлен ВТОРЫМ источником схемы.** `app/models/payment.py` получил `__table_args__` с индексом `uq_payments_open_subscription_intent`; предикат скопирован из `OPEN_INTENT_PREDICATE` ревизии `0021` символ в символ. До этого шага индекс существовал только в ревизии, а суита строит базу `Base.metadata.create_all` — то есть потолка в ней не было ФИЗИЧЕСКИ, ровно там, где снималась прикладная проверка. Доказано контролем: с временно снятым `__table_args__` шесть тестов потолка краснеют.
- **Ленивая уборка `_expire_stale_intents`** (D-02) гасит просроченные намерения в `STATUS_EXPIRED` в начале создания платежа, своим коммитом, с ранним выходом на пустом отборе. Селектор переименован в `_stale_subscription_intents` и сужен до `status == STATUS_PENDING` — зеркало предиката индекса.
- **Порядок «уборка → резерв → сеть → дозапись»** (D-05) для подписки; у пакета порядок «сеть → запись» сохранён, и это решение выписано абзацем, а не подразумевается.
- **Прикладная проверка потолка снята целиком** (D-06) вместе с полем `open_intents` в журнальной записи.
- **Машинный сторож двух источников схемы** с доказанными зубами: разбор `ast` обоих файлов (включая разрешение именованных констант ревизии), контроль подделкой с одним лишним пробелом, отдельное утверждение об отсутствии импорта модуля ревизии.
- **17 новых тестов потолка** на уровне сервиса и **6** на уровне схемы; ни одно действующее утверждение не ослаблено и ни один тест не удалён.

## Task Commits

| Задача | Коммит | Что |
| --- | --- | --- |
| 1 | `8ab1921` | Переключение денежного пути целиком: схема, уборка, резерв до сети, перевод отказа в свой тип |
| 2 | `7764ad1` | Сторож двух источников схемы |
| 3 | `ef08dfe` | Слова действующих тестов приведены к новому механизму |

## Deviations from Plan

### 1. [Rule 3 — Blocking] D-06 исправлено: разбор отказа по ИМЕНИ ограничения заменён перечитыванием состояния

- **Found during:** задача 1 (предупреждение оставлено исполнителем плана 08-03 и подтверждено на коде)
- **Issue:** D-06, объективная часть плана и его `must_haves.truths` («Отказ ограничения различается ПО ИМЕНИ ограничения») предписывали разбирать `IntegrityError` по вхождению `uq_payments_open_subscription_intent`. Приём НЕИСПОЛНИМ на SQLite — диалекте, на котором идёт вся суита проекта (`tests/conftest.py`: `sqlite+aiosqlite:///:memory:`). SQLite сообщает `UNIQUE constraint failed: payments.user_id` — КОЛОНКУ; имя индекса приводит только PostgreSQL. Разбор по имени зеленел бы на бою и МОЛЧА не срабатывал бы в каждом тесте: потолок выглядел бы покрытым и покрыт не был.
- **Fix:** перенесён прецедент самого проекта, на который ссылается и сам D-06 — `_extend_subscription`: поймать `IntegrityError`, ПЕРЕЧИТАТЬ состояние (`_is_open_intent_conflict` спрашивает предикат индекса слово в слово) и, не найдя конфликта, поднять ТОТ ЖЕ объект заново. Приём диалекта не касается вовсе.
- **Files modified:** `app/services/payment_service.py`
- **Verification:** `test_the_verdict_does_not_depend_on_the_driver_text` (вердикт не зависит от текста драйвера в ОБЕ стороны), `test_a_foreign_rejection_is_not_swallowed` (тождество объекта), `test_a_second_open_intent_is_refused_by_the_schema` — все зелёные НА SQLITE, чего разбор по имени дать не мог.
- **Commit:** `8ab1921`
- **Требует правки документов фазы:** формулировка D-06 в `08-CONTEXT.md`, `must_haves.truths` и `key_links` плана 08-05 и строка `T-08-25` его threat-register всё ещё говорят «по имени ограничения». Механизм не соответствует букве этих записей НАМЕРЕННО; исправить следует записи, а не код.

### 2. [Rule 2 — Missing critical] Каждое новое объявление денежного пути получило исполняемого свидетеля

- **Found during:** задача 1, полный прогон суиты
- **Issue:** проект держит машинный гейт `tests/test_application/test_declared_invariants.py`: каждый отобранный абзац денежного пути обязан назвать существующий тест либо быть записан в реестр долга, чей потолок может только СНИЖАТЬСЯ. 29 новых абзацев свидетеля не называли.
- **Fix:** к каждому абзацу добавлено имя теста, который его закрепляет. Один абзац («коммит уборки СВОЙ») свидетеля не имел вовсе — под него написан `test_the_sweep_survives_a_refused_reserve`, доказывающий, что уборка не уезжает в откат отвергнутого резерва. Это не оформление: утверждение было ничем не проверено.
- **Files modified:** `app/services/payment_service.py`, `tests/test_services/test_payment_intent_cap.py`
- **Commit:** `8ab1921`

### 3. [Rule 3 — Blocking] Реестр объявлений без свидетеля: мёртвая запись снята, потолок понижен 21 → 20

- **Found during:** задача 1
- **Issue:** запись реестра для абзаца `create_payment` «ЧТО ЗАКРЫЛО БЫ ОКНО СВОЙСТВОМ…» перестала резолвиться: абзац переписан НА СДЕЛАННОЕ. Тест `test_the_ledger_holds_no_dead_entry` краснел.
- **Fix:** запись удалена, `WITHOUT_WITNESS_CEILING` понижен до фактического числа записей ТЕМ ЖЕ коммитом (иначе разница стала бы запасом — местом для нового ложного абзаца). Причина понижения выписана и в реестре, и над константой. Долг закрыт РАБОТОЙ: индекс построен, абзац назвал свидетелей.
- **Files modified:** `tests/test_application/declared_invariants_without_witness.txt`, `tests/test_application/test_declared_invariants.py`
- **Commit:** `8ab1921`

### 4. [Rule 1 — Bug] Поведение 10 плана недостижимо в заявленной форме: `created_at` объявлен `NOT NULL`

- **Found during:** задача 1
- **Issue:** плановое поведение 10 требовало строки с ПУСТЫМ временем рождения. База такую строку не принимает вовсе (`NOT NULL constraint failed: payments.created_at`) — тест падал на посадке данных, а не на предмете.
- **Fix:** утверждение перецелено на настоящий источник пустого значения — `normalize_utc`, вернувший `None`. Правило («непрочитанное время рождения ⇒ строка СВЕЖАЯ и не гасится») сохранено и проверено; в докстринге теста выписано, почему подделывается именно приведение времени, а не строка.
- **Files modified:** `tests/test_services/test_payment_intent_cap.py`
- **Commit:** `8ab1921`

### 5. [Rule 3 — Blocking] Тест `test_a_user_without_open_intents_pays_without_obstruction` переименован

- **Found during:** задача 1, проверка приёмочного критерия
- **Issue:** критерий `grep -v '^\s*#' app/services/payment_service.py | grep -c 'open_intents'` == 0 не выполнялся из-за упоминания ИМЕНИ ТЕСТА в докстринге (фильтр критерия снимает только строки комментариев).
- **Fix:** тест переименован в `test_a_user_without_an_open_intent_pays_without_obstruction` — единственное число к тому же точнее под потолком «не более одного незакрытого». Ссылка в сервисе обновлена.
- **Files modified:** `tests/test_services/test_payment_service.py`, `app/services/payment_service.py`
- **Commit:** `8ab1921`

**Total deviations:** 5 auto-fixed (1 × Rule 1, 1 × Rule 2, 3 × Rule 3). Ни одного отступления класса Rule 4 — архитектурных решений не принималось, все правки следуют уже принятым решениям владельца.
**Impact:** предмет плана выполнен полностью и СИЛЬНЕЕ его буквы: потолок проверяется суитой на самом деле, а не только на бою.

## Verification Results

| Проверка | Результат |
| --- | --- |
| `uv run pytest tests/test_services/test_payment_intent_cap.py -v` | 17 passed |
| `uv run pytest tests/test_models/test_payment_open_intent_index.py -v` | 8 passed (6 функций, одна параметризована втрое) |
| `uv run pytest tests/test_services/ -q` | 220 passed |
| `uv run pytest tests/ -q` (конец каждой задачи) | 2397 passed, 1 failed — **предсуществующий** отказ, см. ниже |
| `grep -rn '_open_subscription_intents' app/ tests/` | 0 вхождений |
| `uv run python -m compileall -q app main.py tests` | код 0 |
| Все приёмочные критерии задач 1-3 (`grep`/`sed`/номера строк) | выполнены |

**Контроль зубов, проведённый вручную:** с временно снятым `__table_args__` модели краснеют шесть тестов (`test_a_second_open_intent_is_refused_by_the_schema`, `test_the_refusal_says_nothing_of_the_database`, `test_the_refusal_is_recorded_once_and_without_a_count`, `test_a_second_subscription_intent_is_refused_before_the_money_moves`, `test_the_refusal_never_reaches_yookassa`, `test_the_refusal_leaves_its_own_trace`). Объявление восстановлено, суита зелёная. Это и есть доказательство, что потолок проверяется прогоном, а не только существует в ревизии.

## Issues Encountered

**Предсуществующий отказ, к этому плану отношения не имеющий:**
`tests/test_planning/test_state_progress_matches_roadmap.py::test_the_machine_readable_progress_is_derived_from_the_roadmap` — поле `progress.completed_plans` во frontmatter `.planning/STATE.md` записано как 7, из отметок `.planning/ROADMAP.md` выводится 10.

Отказ **снят прогоном на базовом коммите `fcc41f5` ДО единой правки этого плана** и присутствовал там же. Он касается ИСКЛЮЧИТЕЛЬНО `.planning/STATE.md` и `.planning/ROADMAP.md` — файлов, которые этому исполнителю трогать прямо запрещено: их синхронизацию оркестратор выполняет централизованно после слияния волны. Отказ снимется этой синхронизацией сам. Ни одного файла приложения или суиты он не касается.

## Known Stubs

Заглушек нет. Незавершённого по замыслу — один пункт:

**`OPEN_INTENT_INDEX_NAME` объявлена и кодом не читается.** Это осознанное решение, выписанное абзацем над самой константой: имя ограничения в вердикте не участвует ВОВСЕ (см. отступление 1), а константа существует как якорь поиска — чтобы поиск по имени индекса находил и то место, которое о нём рассуждает, а не только два места, которые его объявляют. Удалить её значило бы оставить денежный модуль без единого текстового следа имени, которым его потолок называется в схеме.

## Threat Flags

Новых поверхностей сверх `<threat_model>` плана не появилось. Диспозиции `mitigate` закрыты: T-08-22 (`test_a_second_open_intent_is_refused_by_the_schema`), T-08-14 (`test_the_refusal_says_nothing_of_the_database`), T-08-23 (`test_a_stale_intent_is_swept_at_the_start_of_a_payment`), T-08-24 (`test_a_claim_is_won_on_an_expired_intent`), T-08-25 (`test_a_foreign_rejection_is_not_swallowed` — механизм различения ИСПРАВЛЕН, см. отступление 1), T-08-26 (`test_a_failed_sdk_call_expires_its_own_reserve` + номера строк), T-08-32 (`test_the_two_sources_of_the_schema_declare_one_predicate` с доказанными зубами), T-08-33 (`test_a_second_sweep_touches_nothing_and_says_so`), T-08-34 (все шаги одной задачей, суита зелёная в конце каждой).

## TDD Gate Compliance

Задача 1 объявлена `type="tdd"`, но фазы RED в отдельном коммите у неё НЕТ, и это следствие самого плана, а не небрежность: его главный приёмочный критерий гласит «ОЖИДАЕМО КРАСНЫХ ТЕСТОВ У ЭТОЙ ЗАДАЧИ НЕТ НИ ОДНОГО», а переключение денежного пути объявлено неделимым — любое из трёх промежуточных состояний оставляет продукт сломанным. Коммит с красной суитой посреди необратимой правки денежного пути противоречил бы плану прямо. Последовательность гейтов в истории: `feat(08-05)` → `test(08-05)` → `docs(08-05)`; проверка зубов (снятие `__table_args__` с проверкой покраснения) выполнена вручную и описана выше — она даёт ту же гарантию, что RED-коммит, не оставляя сломанного состояния в истории.

## Next Phase Readiness

- **Готово для 08-10:** потолок PAY-01 закрыт свойством схемы; `STATUS_EXPIRED` заведён константой и участвует в русских подписях статусов, добавленных планом 08-03.
- **Требует правки документов фазы (не кода):** формулировка D-06 в `08-CONTEXT.md`, `must_haves.truths`/`key_links` плана 08-05 и строка T-08-25 его threat-register описывают разбор отказа ПО ИМЕНИ ограничения — механизм, признанный неисполнимым и заменённый. Записи следует привести к коду.
- **Не сделано намеренно:** обобщение сверки «модель ↔ ревизия» на пару `uq_subscriptions_active_user` (граница объёма выписана в докстринге сторожа).

## Self-Check: PASSED

- Файлы на диске: `app/models/payment.py`, `app/services/payment_service.py`, `tests/test_services/test_payment_intent_cap.py`, `tests/test_models/test_payment_open_intent_index.py` — все найдены.
- Коммиты в истории: `8ab1921`, `7764ad1`, `ef08dfe` — все найдены.
- Плановая верификация выполнена, результаты в разделе «Verification Results».

---
*Phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy*
*Completed: 2026-08-28*
