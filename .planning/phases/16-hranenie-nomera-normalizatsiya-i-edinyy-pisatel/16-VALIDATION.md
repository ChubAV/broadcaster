---
phase: "16"
slug: "hranenie-nomera-normalizatsiya-i-edinyy-pisatel"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-08"
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Источник: `16-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest ≥9.0.2 + pytest-asyncio ≥1.3.0 |
| **Config file** | none — маркеры объявляются хуком в `tests/conftest.py` |
| **Quick run command** | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q` |
| **Records command** | `uv run pytest tests/test_planning -q` |
| **Full suite command** | `just test` |
| **Estimated runtime** | quick ~10–20 s; records ~16 s; full ~40 min |

---

## Sampling Rate

- **After every task commit:** целевой модуль задачи и `tests/test_migrations`; у плана записей — `uv run pytest tests/test_planning -q`
- **After every plan wave:** quick run command + `tests/test_planning` + широкие гейты из RESEARCH §Sampling Rate
- **Before `/gsd-verify-work`:** `just test` must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | записи-старт-вехи (решение владельца 2026-10-08) | T-16-01 | правила отложенного пропускаются только при отсутствии живых кандидатов и с причиной; кандидат без раздела плана краснит; архивные файлы проверяются всегда | tracer (records) | `uv run pytest tests/test_planning/test_deferred_items_are_idempotent.py -q -p no:randomly -rs` | ✅ | ✅ green |
| 16-01-02 | 01 | 1 | записи-старт-вехи | T-16-01, T-16-02 | счёт строк — картой по вехе с летописью 44; вывод вехи пропускается только без отчётов и без `Complete`; субъекты контролей выведены из записи; проза — антивакуум по отметкам; мета-гейт вердиктов зелен | records | `uv run pytest tests/test_planning/test_requirement_completion_follows_verification.py tests/test_planning/test_state_progress_matches_roadmap.py tests/test_planning/test_planning_gates_are_independent_of_the_live_verdict.py -q -p no:randomly -rs` | ✅ | ✅ green |
| 16-01-03 | 01 | 1 | записи-старт-вехи | T-16-02, T-16-03 | отбор «до Фазы 15» по номеру фазы (планы v2.2 не сдвигают чисел 142/650/745, контроль с планом фазы 17); реестр засеян штатным `--seed-registry`, решения владельца v2.1 перенесены как есть, шапка несёт летопись О-2 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-02-01 | 02 | 1 | PHONE-01 | T-16-SC | пакет со статусом SUS ставится только после ответа владельца своими словами | checkpoint:human-verify (`blocking-human`) | — (чекпойнт владельца; ответ — в `16-02-SUMMARY.md`) | N/A | ✅ green (ответ владельца «пакет проверен, ставить 9.0.41», 2026-10-08) |
| 16-02-02 | 02 | 1 | PHONE-01 | T-16-06 | автопуть: только цифры 5…15 и успешный разбор, мусор → `None`; показ неразбираемого — как есть | tracer (unit, табличный) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-02-03 | 02 | 1 | PHONE-01, PHONE-21 | T-16-04, T-16-05, T-16-06 | ручной ввод: предел 32 символа / 15 цифр, `IS_POSSIBLE`, отказ по добавочному; тексты отказа — закрытый набор без ввода; маска `+7 *** ***-**-67` | unit (табличный + `ast`) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-03-01 | 03 | 1 | PHONE-01 | T-16-09, T-16-10, T-16-11 | колонка модели без ревизии краснит суиту (D-04); `upgrade head` доходит до `0023`; тест ставит `DATABASE_URL` на `tmp_path` | tracer (migration) | `uv run pytest tests/test_migrations/test_model_matches_head.py -q -p no:randomly` | ✅ | ✅ green |
| 16-03-02 | 03 | 1 | PHONE-01 | T-16-07, T-16-08, T-16-10 | CHECK «ручной без номера» с обеих сторон; три законные пары; нет индекса по номеру; `ON DELETE` целы; downgrade возвращает прежнюю таблицу | migration + unit (модель на `db_session`) | `uv run pytest tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q -p no:randomly` | ✅ | ✅ green |
| 16-04-01 | 04 | 1 | PHONE-21 | T-16-12, T-16-14 | номер по имени, литералом, ключом или маской в журнале Python краснит; `phone_set` булевой формы и маска в выводе `scripts/` — нет; подложенная строка находится обходом | tracer (gate, AST) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-04-02 | 04 | 1 | PHONE-21 | T-16-13, T-16-14, T-16-15 | JS: `${…}` шаблонов, носители `sock.user` / `creds.me`, литералы краснят; комментарии и `node_modules` — нет; реестр исключений под потолком 0 | gate (JS-токенизатор) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-05-01 | 05 | 2 | PHONE-02, PHONE-01 | T-16-16, T-16-17, T-16-18, T-16-19 | автоисточник — только условный `UPDATE`; ручной цел; очистка одним оператором; мусор и неверный ввод — до базы; писатель не коммитит и не ставит признак ручного | tracer (unit, `db_session`) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ✅ green |
| 16-05-02 | 05 | 2 | PHONE-02 | T-16-16 | гонка: ручной номер цел во всех измеренных позициях, флаг «ручная запись состоялась» в каждой; отрицание чтение-проверка-запись краснит позицию 2 | integration (файловая SQLite, две сессии) | `uv run pytest tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-06-01 | 06 | 3 | PHONE-02 | T-16-20, T-16-21 | присваивание и `values(phone=…)` вне модуля-писателя краснят; подложенная запись находится; модуль-писатель виден обходом | tracer (gate, AST) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-06-02 | 06 | 3 | PHONE-02 | T-16-20, T-16-21 | словарь, `setattr` / `set_committed_value`, сырой SQL краснят; законные `phone=` — нет; исключение ровно одного модуля, присваивание запрещено и в нём | gate (AST) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |

**Сквозные гейты (в `<verification>` каждого плана):** `uv run pytest tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_htmx_gates.py tests/test_templates tests/test_application/test_declared_invariants.py -q -p no:randomly` (≈2,5 мин; замер планирования 2026-10-08 — 576 passed) — на волну, а не на задачу: дольше 60 с.

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Партия закрытия гэпа 16-07…16-10 (после верификации, `gap_closure: true`)

⚠️ **Волны ниже нумеруются ЗАНОВО от единицы** — это вторая партия фазы (первая 16-01…16-06), и числа
взяты из `wave` планов дословно (прецедент `12-VALIDATION.md` вехи v2.1). Партия исполняется ПОСЛЕ
приёмки первой, поэтому одноимённые волны разных партий одновременно не идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (2026-10-08, `gaps_found`, 9/10: CR-01 с WR-04 и
попутным WR-03) и решения владельца О-3 (а) «отказ» и О-4 «гэп и три предупреждения» (2026-10-09,
прогон `/gsd-plan-phase 16 --gaps`, записаны в `16-RESEARCH.md`). Опора — зелёный полный прогон на
дереве `85d65afd` (`4349 passed, 3 skipped`, код которого совпадает с `225fd3c7`); строки карты ниже
добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-07-01 | 07 | 1 | PHONE-01 | T-16-22 | ручной `00…` и местный номер с ведущим нулём — `PhoneError(PHONE_ERROR_NOT_A_NUMBER)`, а не `+7 0…`; отказ ограничен кодом 7 (`+39 06 …` принят); вариант (б) «`00` как `+`» не реализован (О-3) | tracer (unit, табличный, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-07-02 | 07 | 1 | PHONE-01 | T-16-23 | автопуть: 7…15 цифр и отказ `IS_POSSIBLE_LOCAL_ONLY`; `12345`, `88812`, `4412345` → `None`; Fragment и `+683 1234` приняты; прежняя граница 5 названа летописью | unit (табличный, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-07-03 | 07 | 1 | PHONE-21 | T-16-24 | маска короткой национальной части прячет все её цифры (`+88812` → `+888 ***`); формы D-10 прежние | unit (табличный, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-08-01 | 08 | 1 | PHONE-02 | T-16-25, T-16-26 | отсутствующая строка — `PhoneWrite.MISSING`, а не `KEPT`; проба `select(exists())` только после условного UPDATE с 0 строк (D-07) | tracer (unit, `db_session`, TDD) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ✅ green |
| 16-08-02 | 08 | 1 | PHONE-02 | T-16-25, T-16-26 | объект вне сессии — `ValueError` без операторов; тест гонки не правится, отрицание краснит позицию 2 (D-08) | unit + integration (TDD) | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-09-01 | 09 | 1 | PHONE-02 | T-16-27 | ORM bulk UPDATE по первичному ключу в синтетическом `scripts/` краснит гейт писателя; живое дерево — ноль (D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-09-02 | 09 | 1 | PHONE-02 | T-16-27, T-16-29 | `dict(...)`, `**{…}`, `set_` при конфликте, `bulk_*_mappings` краснят; законные словари с ключом `phone` — нет; реестр — ровно модуль-писатель | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-09-03 | 09 | 1 | PHONE-21 | T-16-28, T-16-29 | `bind_contextvars` / `bound_contextvars` с номером краснят при любом получателе; живые привязки без номера — нет; реестр пуст, потолок 0 (D-17) | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-10-01 | 10 | 2 | диспозиция-ревью-16 (О-4) | T-16-30 | IN-01 — `deferred` с адресатом Фаза 18 в диспозиции и строкой STATE.md §Deferred Items | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-10-02 | 10 | 2 | диспозиция-ревью-16 (О-4) | T-16-30, T-16-31 | 11/11 находок с диспозицией; `fixed` только с существующим коммитом; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии:** ни одной задачи без `<automated>`; у каждой из десяти задач первая
команда — модуль задачи (≈3–20 с), всего команд `<automated>` в партии 22, и у каждой есть парный
`<fails_when>` (замер планирования: 6/6, 5/5, 6/6, 5/5). Сквозные гейты — на волну, как у первой партии.

**Столбец `File Exists` у партии везде ✅, и это замер, а не умолчание:** все десять задач целятся в
модули, существующие на дереве `225fd3c7`; ни одного НОВОГО тестового модуля партия не заводит.

### Партия закрытия гэпа, раунд 2: 16-11…16-15 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это третья партия фазы (первая 16-01…16-06, вторая
16-07…16-10), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки второй, поэтому
одноимённые волны разных партий одновременно не идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 2, 2026-10-09T17:03:15Z, `gaps_found`, 16/20:
гэпы WR-06, WR-07, WR-08, IN-07 и advisory IN-06) и решения владельца О-5 (а) «автопуть — отказ» и
О-6 «закрыть IN-06 в этом проходе» (2026-10-09, второй прогон `/gsd-plan-phase 16 --gaps`, записаны в
`16-RESEARCH.md`). Опора — дерево `ed800e77` (код совпадает с `49347f53`, на котором полный прогон дал
`4406 passed, 2 skipped, 0 failed`); quick run на нём — `421 passed`. Строки карты ниже добавлены
планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-11-01 | 11 | 1 | PHONE-01 | T-16-32 | ручной номер зоны +7 с лишними цифрами (`+7 999 123-45-67 1234` и класс «настоящий номер плюс 1…5 цифр») — `PhoneError(PHONE_ERROR_NOT_A_NUMBER)`; у кода 7 ровно 10 национальных цифр без ведущего нуля; прежние написания приняты (WR-06, D-05) | tracer (unit, табличный + перебор, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-11-02 | 11 | 1 | PHONE-01 | T-16-33 | автопуть: `70123456789`, `799912345678`, `1234567890123` → `None`, Fragment `88801234567` принят (О-5 (а)); перебор 1935 входов — ни одного хранимого `TOO_LONG` / `INVALID_LENGTH` / `IS_POSSIBLE_LOCAL_ONLY` и невозможного кода 7; 1023 номера-образца метаданных приняты; шапка называет оставшееся множество `TOO_SHORT` (WR-07) | unit (табличный + перебор, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-12-01 | 12 | 1 | PHONE-02 | T-16-34 | скрипт с `parameters=[… for …]` в синтетическом `scripts/` краснит гейт писателя; литеральный контейнер разбирается грамматикой; живое дерево — ноль (WR-08, D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-12-02 | 12 | 1 | PHONE-02 | T-16-34, T-16-35 | сырой SQL с кавычками и схемой, `INSERT OR … INTO`, `REPLACE` / `MERGE INTO`, `COPY … FROM`, строчный `SET (…) =`, склейка литералов, asyncpg COPY краснят; чтение, выгрузка и другие таблицы — нет | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-12-03 | 12 | 1 | PHONE-02 | T-16-34, T-16-35 | `ordered_values`, `from_select`, `__setattr__`, `set_attribute`, `Query.update({...})`, MySQL upsert, псевдоним модели краснят; реестр — ровно модуль-писатель; шапка заявляет охват через механизм (WR-08, запрет 16-09 №2) | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-13-01 | 13 | 1 | PHONE-21 | T-16-36, T-16-37 | псевдоним ввоза привязки, `bind_threadlocal` / `bound_threadlocal` / `tmp_bind` краснят гейт приватности; живые деревья — прежние числа вызовов, ноль находок (IN-06, О-6, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-13-02 | 13 | 1 | PHONE-21 | T-16-36, T-16-37 | получатель журнала, связанный в модуле с фабрикой или ввезённый под псевдонимом, краснит; настройка журнала — нет; «ГРАНИЦА СРЕДСТВА» называет остальное; реестр пуст, потолок 0 | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-14-01 | 14 | 1 | PHONE-02 | T-16-38 | объект вне сессии писателя — `ValueError(ACCOUNT_NOT_IN_SESSION)` при `None` / `''` / `'garbage'` / разбираемом номере и у отсоединённого объекта, без операторов и без сброса (IN-07) | tracer (unit, `db_session`, TDD) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ✅ green |
| 16-14-02 | 14 | 1 | PHONE-02 | T-16-39 | член сессии с мусором — `UNPARSEABLE`, ноль операторов, без сброса; тест гонки не правится, отрицание краснит позицию 2 (D-08) | unit + integration (сторож) | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-15-01 | 15 | 2 | диспозиция-ревью-16 | T-16-40 | WR-06 — `fixed` с существующим коммитом GREEN плана 16-11; frontmatter согласован | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-15-02 | 15 | 2 | диспозиция-ревью-16 | T-16-40, T-16-41 | пять находок повторного ревью — `fixed` с коммитами `feat(16-1N)`; 11 прежних строк байт в байт; `open: 0`, `total: 16`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 2:** ни одной задачи без `<automated>`; у каждой из
одиннадцати задач первая команда — модуль задачи (≈1–20 с), у каждой задачи кода последняя —
quick run фазы; всего команд `<automated>` в партии 36, и у каждой есть парный `<fails_when>`
(замер планирования: 7/7, 9/9, 7/7, 8/8, 5/5). Сквозные гейты — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 2 везде ✅, и это замер, а не умолчание:** все одиннадцать
задач целятся в модули, существующие на дереве `ed800e77`; ни одного НОВОГО тестового модуля партия
не заводит.

### Партия закрытия гэпа, раунд 3: 16-16…16-20 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это четвёртая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки
третьей, поэтому одноимённые волны разных партий одновременно не идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 3, 2026-10-10T07:08:40Z, `gaps_found`, 27/30:
гэпы WR-09, WR-10, IN-09 и advisory IN-08, IN-10) и решения владельца О-7 (а) «ручной номер чужой зоны —
отказ по типам аккаунта» и О-8 «IN-08 и IN-10 закрыть в этом проходе» (2026-10-12, третий прогон
`/gsd-plan-phase 16 --gaps`, записаны в `16-RESEARCH.md`); WR-10 и IN-09 — умолчание прохода. Опора —
дерево `7a4ee433` (код совпадает с `719555b7`, на котором полный прогон дал `4544 passed, 2 skipped,
0 failed`); quick run на нём — `559 passed`, `tests/test_planning` — `218 passed, 2 skipped`. Строки карты
ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-16-01 | 16 | 1 | PHONE-01 | T-16-42 | ручной номер чужой зоны с лишними цифрами — `PhoneError(PHONE_ERROR_NOT_A_NUMBER)`: исход владельца О-7 (а) (`+375 29 123 45 67 1`, `+380 50 123 4567 1` — отказ; `+375 29 123 45 67`, `8-800-555-35-35` — приняты); перебор 5 баз × 1…5; граница DE / IL названа в докстринге, нормой не утверждена (WR-09, D-05, D-06) | tracer (unit, табличный + перебор, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-16-02 | 16 | 1 | PHONE-01 | T-16-43 | 830 номеров-образцов четырёх типов аккаунта приняты ручным путём; негеографические `+800`/`+808`/`+888`/`+979` — отказ, `+870`/`+878`/`+881`/`+882`/`+883` — приняты; голая проверка «возможности» по типу запрещена правилом чистоты (D-05) | unit (сторож) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-16-03 | 16 | 1 | PHONE-01 | T-16-44 | шапка называет оба принимаемых автопутём класса — возможные, в том числе недействительные (400 из 558), и `TOO_SHORT` у кода не 7 (583 из 1935); правило сверяет шапку с перебором вживую; автопуть не менялся (IN-08, О-8) | unit (сверка прозы с замером, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-17-01 | 17 | 1 | PHONE-02 | T-16-45 | скрипт с `run_sync(Session.bulk_update_mappings, …)` в синтетическом `scripts/` краснит гейт писателя; пишущий API опознаётся по ссылке, `getattr`-строке и `methodcaller`; живое дерево — ноль (WR-10, D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-17-02 | 17 | 1 | PHONE-02 | T-16-45, T-16-46 | таблица `JUDGED_PARAMETERS` (33 строки перебора `inspect.signature`) сверена с установленными сигнатурами; правило-матрица 31 × 4 формы связывания; `Query.update(values=…)`, `key=`, `DictComp`, `scalar(s)` / `stream*` / `exec_driver_sql` — находки | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-17-03 | 17 | 1 | PHONE-02 | T-16-45, T-16-46 | вид 1 по контексту `Store` (цель `for` / `with` / comprehension), `__set__`, `MessengerAccount.__init__`, `column("phone")`; шапка — граница с правдивой причиной; самопроверка исполнителя ≥ 200 форм; реестр — ровно модуль-писатель (запреты 16-09 №2, 16-12 №2) | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-18-01 | 18 | 1 | PHONE-21 | T-16-47 | функция `logging`, ввезённая (и под псевдонимом), — вызов журнала; подложенный файл в синтетическом `app/` краснит гейт; одноимённая функция без ввоза — нет; живые деревья 215 / 68 / 89, ноль находок (IN-09, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-18-02 | 18 | 1 | PHONE-21 | T-16-47, T-16-48 | журнал из тела класса через `self.` / `cls.`, `:=`, второе связывание, фабрика под псевдонимом, `getattr`-строка, `LoggerAdapter` / `wrap_logger`, начальные значения фабрики, `partial` и ссылки на методы краснят; «ГРАНИЦА СРЕДСТВА» — только с правдивой причиной; реестр пуст, потолок 0 | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-19-01 | 19 | 1 | PHONE-02 | T-16-49, T-16-50 | `ACCOUNT_NOT_IN_SESSION` — «аккаунт не принадлежит сессии писателя»; вторая линия после `flush` — `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`; проверка членства первая, без операторов и `flush` (IN-10, О-8) | tracer (unit, `db_session`, TDD) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-19-02 | 19 | 1 | PHONE-02 | T-16-49, T-16-50 | объект чужой непривязанной `AsyncSession()` — `ValueError(ACCOUNT_NOT_IN_SESSION)`, ноль операторов, строка цела; тест гонки не правится, отрицание краснит позицию 2 (D-08) | unit + integration (сторож) | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-20-01 | 20 | 2 | диспозиция-ревью-16 | T-16-51 | WR-09 — `fixed` с существующим коммитом GREEN плана 16-16; frontmatter согласован | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ⬜ pending |
| 16-20-02 | 20 | 2 | диспозиция-ревью-16 | T-16-51, T-16-52 | пять находок повторного ревью раунда 2 — `fixed` с коммитами `feat(16-1N)`, предками `HEAD`; 16 прежних строк байт в байт; `open: 0`, `total: 21`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 3:** ни одной задачи без `<automated>`; у каждой из двенадцати
задач первая команда — модуль задачи (≈1–20 с), у каждой задачи кода последняя — quick run фазы либо
целевой сторож; всего команд `<automated>` в партии 38, и у каждой есть парный `<fails_when>` (замер
планирования: 8/8, 10/10, 7/7, 8/8, 5/5). Сквозные гейты — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 3 везде ✅, и это замер, а не умолчание:** все двенадцать задач
целятся в модули, существующие на дереве `7a4ee433`; ни одного НОВОГО тестового модуля партия не
заводит.

---

## Wave 0 Requirements

- [x] `tests/test_services/test_phone.py` — SC3 (таблица нормализации, показ, маска)
- [x] `tests/test_migrations/test_0023_messenger_account_phone.py` — SC1, SC2
- [x] `tests/test_models/test_messenger_account_phone_check.py` — SC2 (модельная половина CHECK, форма колонок; план 16-03)
- [x] `tests/test_migrations/test_model_matches_head.py` — расширение снимка `messenger_accounts` (SC1, D-04)
- [x] `tests/test_application/test_account_phone_writer.py` — SC2, SC4 (последовательно)
- [x] `tests/test_application/test_account_phone_race.py` — SC4 (гонка, контроль-отрицание)
- [x] `tests/test_application/test_phone_single_writer_gate.py` — D-13
- [x] `tests/test_phone_privacy_gate.py` — SC5 (PHONE-21)
- [x] `phonenumberslite==9.0.41` — `just add` за `checkpoint:human-verify` (пакет помечен SUS: версия от 2026-10-08)

### Волна 0 партии закрытия гэпа (16-07…16-10): пуста, и это замер

Партия **не заводит ни одного нового тестового модуля** — все десять задач целятся в файлы,
существующие на дереве `225fd3c7`. Требований волны 0 у неё нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано):
строка `REPORTED_ACCEPTED[five_digits_lower_bound]` переносится в `REPORTED_REFUSED` с летописью
(16-07-02 — это тест фазы, закреплявший дефект, урок «тесты фазы закрепляют старые дефекты»); правило
утечки маски `test_a_mask_shows_only_the_country_code_and_two_last_digits` начинает судить и короткие
номера (16-07-03); число распознанных вызовов журнала дерева `app` в живом правиле гейта приватности
растёт на 2 — живые привязки `bind_contextvars` (16-09-03); перепись запретов получает строки планов
16-07…16-10 штатным засевом (оркестратор при коммите планов, повтор — 16-10-02).

### Волна 0 партии раунда 2 (16-11…16-15): пуста, и это замер

Партия **не заводит ни одного нового тестового модуля** — все одиннадцать задач целятся в файлы,
существующие на дереве `ed800e77`. Требований волны 0 у неё нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано):
число правил `tests/test_services/test_phone.py` растёт со 133 до 173 (16-11), гейта писателя — с 48
до 99 (16-12), гейта приватности — с 72 до 94 (16-13), теста писателя — с 17 до 22 (16-14; правило
`test_recording_an_account_never_added_to_the_session_raises` становится четырьмя строками); quick run
— с 421 до 539. Текст `ACCOUNT_NOT_IN_SESSION` меняется (16-14-01), правила сравнивают с константой.
Числа распознанных вызовов журнала в живом правиле гейта приватности НЕ меняются (215 / 68 / 89 —
замер прототипа планирования; изменение было бы признаком ложного распознавания). Строк, которые
партия переносит из таблицы в таблицу, нет: прототипы правил прогнаны планированием по всем прежним
строкам таблиц и законных случаев — ни одна не меняет исход (урок «тесты фазы закрепляют старые
дефекты»). Перепись запретов получает строки планов 16-11…16-15 штатным засевом (оркестратор при
коммите планов, повтор — 16-15-02).

### Волна 0 партии раунда 3 (16-16…16-20): пуста, и это замер

Партия **не заводит ни одного нового тестового модуля** — все двенадцать задач целятся в файлы,
существующие на дереве `7a4ee433` (`tests/test_services/test_phone.py`,
`tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_privacy_gate.py`,
`tests/test_application/test_account_phone_writer.py`, записи `.planning/`). Требований волны 0 у неё нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано):
число правил `tests/test_services/test_phone.py` растёт со 173 до 224 (16-16: трасер, 25 строк перебора
чужих баз, 8 строк `wr09_*` в двух правилах, 6 контролей `*_mobile`, два сторожа, правило шапки); гейта
писателя — со 119 до 296 (16-17: правило-матрица 124, сторож сигнатур, 34 строки `LITERAL_FORM_CASES`,
15 законных строк, три правила; плюс строки самопроверки исполнителя, если она найдёт формы); гейта
приватности — с 94 до 126 (16-18: два правила, 21 отрицательная и 9 положительных строк); теста писателя
— с 22 до 24 (16-19). Текст `ACCOUNT_NOT_IN_SESSION` меняется
(16-19-01), правила сравнивают с константой. `FORBIDDEN_CALLS` правила чистоты модуля номера растёт на
голую проверку «возможности» по типу, и контроль-отрицание этого правила дополняется тем же вызовом
(16-16-02). Числа распознанных вызовов журнала в живом правиле гейта приватности НЕ меняются (215 / 68 /
89 — замер прототипа планирования; изменение было бы признаком ложного распознавания); в модуле-писателе
гейт писателя по-прежнему видит 6 сырых записей. Строк, которые партия переносит из таблицы в таблицу,
нет: прототипы правил прогнаны планированием по всем прежним строкам таблиц и законных случаев — ни одна
не меняет исход (урок «тесты фазы закрепляют старые дефекты»); граница DE / IL правила по типам названа
в докстринге и строкой таблицы не утверждается. Перепись запретов получает строки планов 16-16…16-20
штатным засевом (оркестратор при коммите планов, повтор — 16-20-02).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Легитимность пакета `phonenumberslite==9.0.41` | PHONE-01 | Сторож пакетов дал SUS (too-new) | Владелец сверяет страницу PyPI / автора перед `just add` |
| Ветвь PostgreSQL ревизии `0023` | PHONE-01 | Тестовой PostgreSQL в окружении нет | Покрывается деплой-гейтом владельца (D-26, R-08-06) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-08 (`/gsd-validate-phase 16` из `/gsd-execute-phase 16`): все 14 строк карты зелёные на дереве `85d65afd` — команды карты `582 passed, 3 skipped`, `prohibitions_census.py --check` rc 0, полная суита `4349 passed, 3 skipped, 0 failed`. Пробелов 0; ручными остаются две строки таблицы Manual-Only.

**Партия закрытия гэпа 16-07…16-10: validated 2026-10-09** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 10 строк партии зелёные на дереве `b72c32cd` — `test_phone.py` 133 passed; `test_account_phone_writer.py` 17 passed, с тестом гонки 21 passed; `test_phone_single_writer_gate.py` 48 passed; `test_phone_privacy_gate.py` 72 passed; `tests/test_planning` 218 passed, 2 skipped; `prohibitions_census.py --check` rc 0. Полная суита на слитом коде волны 1 партии (`49347f53`; после него менялись только файлы `.planning/`) — `4406 passed, 2 skipped, 0 failed`. Пробелов 0; frontmatter (`status: validated`, `nyquist_compliant: true`) остаётся верным для всех 24 строк. До этой подписи абзац гласил: «**Партия закрытия гэпа 16-07…16-10: pending**» (строки добавлены планированием 2026-10-09, прогон
`/gsd-plan-phase 16 --gaps`). Подпись и отметки выше относятся к ПЕРВОЙ партии — 14 задачам. Партия
добавляет десять задач: у каждой есть `<automated>` с парным `<fails_when>` (22 из 22), трёх подряд
задач без машинной проверки нет, новых тестовых модулей нет. Что планирование изменило в этом файле и
почему: дописаны подраздел карты партии, подраздел волны 0 партии и этот абзац; frontmatter
(`status: validated`, `nyquist_compliant: true`) и прежние строки НЕ тронуты — переоценку фазы с
десятью новыми строками делает `/gsd-validate-phase 16` после исполнения партии, а не планировщик.

**Партия закрытия гэпа, раунд 2 (16-11…16-15): validated 2026-10-10** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 11 строк партии зелёные на дереве `2111732b` — `test_phone.py` 173 passed; `test_phone_single_writer_gate.py` 119 passed; `test_phone_privacy_gate.py` 94 passed; `test_account_phone_writer.py` 22 passed, с тестом гонки 26 passed; `tests/test_planning` 218 passed, 2 skipped; `prohibitions_census.py --check` rc 0; quick run 559 passed. Полная суита на слитом коде волны 1 партии (`719555b7`; после него менялись только файлы `.planning/`) — `4544 passed, 2 skipped, 0 failed`. Пробелов 0; frontmatter (`status: validated`, `nyquist_compliant: true`) остаётся верным для всех 35 строк. Расхождение с прогнозом волны 0: гейт писателя вырос до 119 правил, а не до 99 — исполнитель 16-12 закрыл 16 форм сверх плана (отступление, `16-12-SUMMARY.md`). До этой подписи абзац гласил: «**Партия закрытия гэпа, раунд 2 (16-11…16-15): pending**» (строки добавлены планированием 2026-10-09,
второй прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач) и к
партии 16-07…16-10 (10 задач). Партия раунда 2 добавляет одиннадцать задач: у каждой есть
`<automated>` с парным `<fails_when>` (36 из 36), трёх подряд задач без машинной проверки нет, новых
тестовых модулей нет. Что планирование изменило в этом файле и почему: дописаны подраздел карты
партии раунда 2, подраздел её волны 0 и этот абзац; frontmatter (`status: validated`,
`nyquist_compliant: true`), прежние строки и прежние подписи НЕ тронуты — переоценку фазы с
одиннадцатью новыми строками (всего строк станет 35) делает `/gsd-validate-phase 16` после
исполнения партии, а не планировщик.

**Партия закрытия гэпа, раунд 3 (16-16…16-20): pending** (строки добавлены планированием 2026-10-12,
третий прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии
16-07…16-10 (10 задач) и к партии раунда 2 (11 задач). Партия раунда 3 добавляет двенадцать задач: у
каждой есть `<automated>` с парным `<fails_when>` (38 из 38), трёх подряд задач без машинной проверки
нет, новых тестовых модулей нет. Что планирование изменило в этом файле и почему: дописаны подраздел карты
партии раунда 3, подраздел её волны 0 и этот абзац; frontmatter (`status: validated`,
`nyquist_compliant: true`), прежние строки и прежние подписи НЕ тронуты — шаг 5.5 `/gsd-plan-phase`
оркестратор пропустил намеренно (он записал бы пустой шаблон поверх заполненной карты), а переоценку фазы
с двенадцатью новыми строками (всего строк станет 47) делает `/gsd-validate-phase 16` после исполнения
партии, а не планировщик.

## Validation Audit 2026-10-08

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Validation Audit 2026-10-09 (партия закрытия гэпа 16-07…16-10)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой: `verification.append-audit` пропустил запись (`appended: false`), потому что
последний блок аудита тоже 0/0/0. Предмет аудита другой — десять строк партии 16-07…16-10, измеренные
на `b72c32cd` (числа — в подписи выше); без этого раздела аудит партии читался бы как часть аудита
первой партии от 2026-10-08.

## Validation Audit 2026-10-10 (партия закрытия гэпа, раунд 2: 16-11…16-15)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой: `verification.append-audit` пропустил запись (`appended: false`), потому что
последний блок аудита тоже 0/0/0. Предмет аудита другой — одиннадцать строк партии раунда 2,
измеренные на `2111732b` (числа — в подписи выше).
