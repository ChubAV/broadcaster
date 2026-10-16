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
| 16-16-01 | 16 | 1 | PHONE-01 | T-16-42 | ручной номер чужой зоны с лишними цифрами — `PhoneError(PHONE_ERROR_NOT_A_NUMBER)`: исход владельца О-7 (а) (`+375 29 123 45 67 1`, `+380 50 123 4567 1` — отказ; `+375 29 123 45 67`, `8-800-555-35-35` — приняты); перебор 5 баз × 1…5; граница DE / IL названа в докстринге, нормой не утверждена (WR-09, D-05, D-06) | tracer (unit, табличный + перебор, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-16-02 | 16 | 1 | PHONE-01 | T-16-43 | 830 номеров-образцов четырёх типов аккаунта приняты ручным путём; негеографические `+800`/`+808`/`+888`/`+979` — отказ, `+870`/`+878`/`+881`/`+882`/`+883` — приняты; голая проверка «возможности» по типу запрещена правилом чистоты (D-05) | unit (сторож) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-16-03 | 16 | 1 | PHONE-01 | T-16-44 | шапка называет оба принимаемых автопутём класса — возможные, в том числе недействительные (400 из 558), и `TOO_SHORT` у кода не 7 (583 из 1935); правило сверяет шапку с перебором вживую; автопуть не менялся (IN-08, О-8) | unit (сверка прозы с замером, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-17-01 | 17 | 1 | PHONE-02 | T-16-45 | скрипт с `run_sync(Session.bulk_update_mappings, …)` в синтетическом `scripts/` краснит гейт писателя; пишущий API опознаётся по ссылке, `getattr`-строке и `methodcaller`; живое дерево — ноль (WR-10, D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-17-02 | 17 | 1 | PHONE-02 | T-16-45, T-16-46 | таблица `JUDGED_PARAMETERS` (33 строки перебора `inspect.signature`) сверена с установленными сигнатурами; правило-матрица 31 × 4 формы связывания; `Query.update(values=…)`, `key=`, `DictComp`, `scalar(s)` / `stream*` / `exec_driver_sql` — находки | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-17-03 | 17 | 1 | PHONE-02 | T-16-45, T-16-46 | вид 1 по контексту `Store` (цель `for` / `with` / comprehension), `__set__`, `MessengerAccount.__init__`, `column("phone")`; шапка — граница с правдивой причиной; самопроверка исполнителя ≥ 200 форм; реестр — ровно модуль-писатель (запреты 16-09 №2, 16-12 №2) | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-18-01 | 18 | 1 | PHONE-21 | T-16-47 | функция `logging`, ввезённая (и под псевдонимом), — вызов журнала; подложенный файл в синтетическом `app/` краснит гейт; одноимённая функция без ввоза — нет; живые деревья 215 / 68 / 89, ноль находок (IN-09, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-18-02 | 18 | 1 | PHONE-21 | T-16-47, T-16-48 | журнал из тела класса через `self.` / `cls.`, `:=`, второе связывание, фабрика под псевдонимом, `getattr`-строка, `LoggerAdapter` / `wrap_logger`, начальные значения фабрики, `partial` и ссылки на методы краснят; «ГРАНИЦА СРЕДСТВА» — только с правдивой причиной; реестр пуст, потолок 0 | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-19-01 | 19 | 1 | PHONE-02 | T-16-49, T-16-50 | `ACCOUNT_NOT_IN_SESSION` — «аккаунт не принадлежит сессии писателя»; вторая линия после `flush` — `ACCOUNT_WITHOUT_ID_AFTER_FLUSH`; проверка членства первая, без операторов и `flush` (IN-10, О-8) | tracer (unit, `db_session`, TDD) | `uv run pytest tests/test_application/test_account_phone_writer.py -q -p no:randomly` | ✅ | ✅ green |
| 16-19-02 | 19 | 1 | PHONE-02 | T-16-49, T-16-50 | объект чужой непривязанной `AsyncSession()` — `ValueError(ACCOUNT_NOT_IN_SESSION)`, ноль операторов, строка цела; тест гонки не правится, отрицание краснит позицию 2 (D-08) | unit + integration (сторож) | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-20-01 | 20 | 2 | диспозиция-ревью-16 | T-16-51 | WR-09 — `fixed` с существующим коммитом GREEN плана 16-16; frontmatter согласован | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-20-02 | 20 | 2 | диспозиция-ревью-16 | T-16-51, T-16-52 | пять находок повторного ревью раунда 2 — `fixed` с коммитами `feat(16-1N)`, предками `HEAD`; 16 прежних строк байт в байт; `open: 0`, `total: 21`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 3:** ни одной задачи без `<automated>`; у каждой из двенадцати
задач первая команда — модуль задачи (≈1–20 с), у каждой задачи кода последняя — quick run фазы либо
целевой сторож; всего команд `<automated>` в партии 38, и у каждой есть парный `<fails_when>` (замер
планирования: 8/8, 10/10, 7/7, 8/8, 5/5). Сквозные гейты — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 3 везде ✅, и это замер, а не умолчание:** все двенадцать задач
целятся в модули, существующие на дереве `7a4ee433`; ни одного НОВОГО тестового модуля партия не
заводит.

### Партия закрытия гэпа, раунд 4: 16-21…16-25 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это пятая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15, четвёртая 16-16…16-20), числа взяты из `wave` планов дословно. Партия
исполняется ПОСЛЕ приёмки четвёртой, поэтому одноимённые волны разных партий одновременно не идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 4, 2026-10-12T20:26:19Z, `gaps_found`, 43/46:
гэпы WR-11, WR-12, WR-13 и advisory IN-11, IN-12) и решения владельца О-9 (а) «правило О-7 (а) остаётся,
граница называется по настоящему остатку с живым замером», О-10 (а) «чинить предикат, заявление шапки
прежнее» и О-11 «IN-11 и IN-12 закрыть попутно» (2026-10-13, четвёртый прогон `/gsd-plan-phase 16 --gaps`,
записаны в `16-RESEARCH.md`); WR-13 — умолчание прохода. Опора — дерево `cce988cb` (код совпадает с
`15b12ad1`, на котором полный прогон дал `4841 passed, 2 skipped, 0 failed`); quick run на нём — `856
passed` (замер верификатора раунда 4), `tests/test_planning` — `218 passed, 2 skipped` (замер планирования
до записей партии). Строки карты ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-21-01 | 21 | 1 | PHONE-01 | T-16-53 | пункт 5 докстринга `normalize_manual` называет настоящий остаток правила О-7 (а) — «56 из 976» вводов в 36 регионах, причины по типам аккаунта, «15 из 56» действительных; правило-сверка пересчитывает числа и регионы-примеры перебором вживую; исход О-9 (а): `+31 6 12345678 12` → `+3161234567812`, `+375 29 123 45 67 1` — отказ (WR-11, D-05, D-06, D-07) | tracer (unit, сверка прозы с замером, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-21-02 | 21 | 1 | PHONE-01 | T-16-53, T-16-54 | тексты теста называют границу ссылкой на пункт 5 и правило-сверку, без чисел без правила; IN-11 — пробел своим коммитом `refactor(16-21)`; код `normalize_manual` по дереву разбора и `normalize_reported` байт в байт — как на `cce988cb` (О-11) | unit (сверка кода с `cce988cb`) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-22-01 | 22 | 1 | PHONE-02 | T-16-55 | скрипт дозаполнения со строковым ключом `MessengerAccount.phone.key` в строках `bulk_update_mappings` в синтетическом `scripts/` краснит гейт писателя; производная `.key` / `.name`; имя у писателей атрибута — через `_phone_column`; живое дерево — ноль (WR-12, D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-22-02 | 22 | 1 | PHONE-02 | T-16-55, T-16-56 | перечень `from_select` в любом литеральном контейнере; пишущий API под псевдонимом того же модуля (ввоз и присваивание) судится как сам API; пункт (1) границы переписан | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-22-03 | 22 | 1 | PHONE-02 | T-16-55, T-16-56 | `COLUMN_NAMINGS` (≥ 16) × `COLUMN_CONTEXTS` (≥ 500 на наименование) — правило-матрица, ровно одна находка на форму; производная колонки — цепочкой; заявление шапки прежнее (О-10 (а)); самопроверка исполнителя ≥ 20 000 форм по обеим осям; реестр — ровно модуль-писатель, в писателе 6 сырых (запреты 16-09 №2, 16-12 №2, 16-17 №2) | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-23-01 | 23 | 1 | PHONE-21 | T-16-57 | `await logger.ainfo(…, phone=…)` в синтетическом `app/` краснит гейт приватности; `ASYNC_LOG_METHODS` в `LOG_METHODS`, сторож против `dir(structlog.stdlib.BoundLogger)`; живые деревья 215 / 68 / 89, ноль находок (WR-13, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-23-02 | 23 | 1 | PHONE-21 | T-16-57, T-16-58 | охват по получателю: любой метод опознанного журнала (`_log`, `makeRecord`, `handle`, `callHandlers`, `_proxy_to_logger`, настройка) судится; `getChild` / `unbind` / `try_unbind` — привязки; граница не приписывает D-17 список методов; живые деревья — 221 / 68 / 93 вызова (настройка журнала) и ноль находок; реестр пуст, потолок 0 (запрет 16-18 №2) | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-24-01 | 24 | 1 | PHONE-02 | T-16-59 | `ACCOUNT_WITHOUT_ID_AFTER_FLUSH` ввезена по имени, второй путь ввоза снят; 24 правила теста писателя зелены; тест гонки байт в байт как на `225fd3c7` (IN-12, О-11, D-08) | tracer (unit, гигиена ввоза) | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py -q -p no:randomly` | ✅ | ✅ green |
| 16-25-01 | 25 | 2 | диспозиция-ревью-16 | T-16-60 | WR-11 — `fixed` с существующим коммитом GREEN плана 16-21; исправление узкой формулировки WR-09 — в клетке WR-11; строка WR-09 прежняя | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-25-02 | 25 | 2 | диспозиция-ревью-16 | T-16-60, T-16-61 | пять находок повторного ревью раунда 3 — `fixed` с коммитами-предками `HEAD` (`feat(16-2N)` у WR-11…WR-13, `refactor(16-21)` / `refactor(16-24)` у IN-11 / IN-12); 21 прежняя строка байт в байт; `open: 0`, `total: 26`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 4:** ни одной задачи без `<automated>`; у каждой из десяти задач
первая команда — модуль задачи (≈1–20 с), у каждой задачи кода последняя — quick run фазы либо целевой
сторож; всего команд `<automated>` в партии 30, и у каждой есть парный `<fails_when>` (замер планирования:
5/5, 10/10, 7/7, 3/3, 5/5). Сквозные гейты — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 4 везде ✅, и это замер, а не умолчание:** все десять задач целятся
в модули, существующие на дереве `cce988cb`; ни одного НОВОГО тестового модуля партия не заводит.

### Партия закрытия гэпа, раунд 5: 16-26…16-30 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это шестая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25), числа взяты из `wave` планов
дословно. Партия исполняется ПОСЛЕ приёмки пятой, поэтому одноимённые волны разных партий одновременно не
идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 5, 2026-10-13T12:19:35Z, `gaps_found`, 56/58:
гэп 1 — WR-14, WR-15, WR-16, гэп 2 — WR-17, advisory IN-13, IN-14) и решения владельца О-12 (а) «чинить
проверку, заявления обоих гейтов прежние; одна грамматика связывания и один перечень носителей ссылки;
правило-паритет; самопроверка композицией» и О-13 «IN-13 и IN-14 закрыть попутно, отдельным маленьким
планом» (2026-10-13, пятый прогон `/gsd-plan-phase 16 --gaps`, записаны в `16-RESEARCH.md`); WR-17 —
умолчание прохода. Гэп 1 разрезан на два последовательных плана одного файла (16-27 — ось «как назван API»
и общий модуль, 16-28 — ось «как названа колонка» и сырой SQL). Опора — дерево `33a31ee3` (код совпадает с
`fb17f03b`, на котором полный прогон дал `4967 passed, 2 skipped, 0 failed`); quick run на нём — `982
passed`, `tests/test_planning` — `218 passed, 2 skipped` (замер планирования до записей партии). Строки
карты ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-26-01 | 26 | 1 | PHONE-01 | T-16-62 | правило-сверка пункта 5 разбирает три скобки и сверяет их с `MANUAL_BOUNDARY_EXAMPLES` в обе стороны, обратное вложение — по отрезку остатка; TW в чужой скобке и RS без строки таблицы краснят помощник (IN-13, О-13, D-05, D-06) | tracer (unit, сверка прозы с таблицей, TDD) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-26-02 | 26 | 1 | PHONE-01 | T-16-62, T-16-63 | пункт 7 докстринга `normalize_manual` ссылается на остаток в пункте 5 без чисел и регионов; тело `normalize_manual` AST-равно `33a31ee3`, прочий код модуля байт в байт (IN-14, О-13) | unit (TDD, сверка кода с `33a31ee3`) | `uv run pytest tests/test_services/test_phone.py -q -p no:randomly` | ✅ | ✅ green |
| 16-27-01 | 27 | 1 | PHONE-02 | T-16-64 | класс-исполнитель скрипта дозаполнения с `self.bum = session.bulk_update_mappings` в синтетическом `scripts/` краснит гейт писателя; грамматика связывания (кортеж, `:=`, `self.<x>` / `cls.<x>`, `getattr`-значение) — в общем модуле `tests/phone_gate_grammar.py`; формы WR-14 — строки; живое дерево 0 (WR-14, О-12 (а), D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ (модуль `tests/phone_gate_grammar.py` создан RED-коммитом задачи, `c30b676c`) | ✅ green |
| 16-27-02 | 27 | 1 | PHONE-02 | T-16-64, T-16-65 | правило-матрица оси B `BINDING_FORMS` × `API_IDENTIFICATION_VALUES` × (прямой вызов и `REFERENCE_CARRIERS`) — 270 ячеек; `map` поэлементно, связанный `partial`; один перечень носителей и `REFERENCE_KEYWORDS` — в общем модуле | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-27-03 | 27 | 1 | PHONE-02 | T-16-65 | шапка называет общую грамматику, носителей и правдивую границу (`for`, `with … as`); пункт (1) без пойманного `partial`; заявление прежнее; самопроверка оси B ≥ 3 000 форм (запреты 16-09 №2, 16-12 №2, 16-17 №2, 16-22 №2) | gate (AST, TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-28-01 | 28 | 2 | PHONE-02 | T-16-66 | скрипт с ключом `MessengerAccount.__table__.c[MessengerAccount.phone.key]` в синтетическом `scripts/` краснит гейт; `_phone_column` композиционен; правило `NAME_POSITIONS` (10 позиций); четыре новых `COLUMN_NAMINGS` в матрице 714 контекстов (WR-15, О-12 (а)) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-28-02 | 28 | 2 | PHONE-02 | T-16-66, T-16-67 | виды 5 (а) и (б) — кодом на нулевой глубине скобок (`_raw_sql_set_writes`): запись после подзапроса, после литерала со словом `where`, строчный конструктор не первым — находки; фильтр по номеру в `WHERE` и в подзапросе — ноль (WR-16) | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-28-03 | 28 | 2 | PHONE-02 | T-16-67 | шапка — композиция наименований, вид 5 кодом, летопись пятого круга; самопроверка осей A (глубина 2) и SQL; общий модуль не тронут; реестр — ровно писатель, в писателе 6 сырых | gate (AST, шапка, самопроверка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-29-01 | 29 | 2 | PHONE-21 | T-16-68, T-16-70 | `await asyncio.to_thread(logger.info, …, account.phone)` в синтетическом `app/` краснит гейт приватности; носитель `_carried_log_calls` (аргументы после ссылки); связывания из общего модуля; живые деревья 224 / 68 / 93, ноль находок (WR-17, D-11, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-29-02 | 29 | 2 | PHONE-21 | T-16-68, T-16-69 | `methodcaller` над опознанным получателем; правило-матрица гейта приватности (270 ячеек); правило-паритет обоих гейтов — построение, 270 ячеек, формы вне грамматики | gate (AST, TDD, паритет) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ (модуль `tests/test_phone_gates_parity.py` создан RED-коммитом задачи, `22e1b6bb`) | ✅ green |
| 16-29-03 | 29 | 2 | PHONE-21 | T-16-69, T-16-70 | шапка называет носителя, `methodcaller`, общую грамматику и цену строгости (`app/pages/history.py:288`, `:289`, `:293`); граница правдива; самопроверка ≥ 5 000 форм; реестр `{}`, потолок 0 (запреты 16-18 №2, 16-23 №2) | gate (AST, TDD, шапка) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-30-01 | 30 | 3 | диспозиция-ревью-16 | T-16-71 | WR-14 — `fixed` с существующими коммитами GREEN плана 16-27; прочие строки — как на `33a31ee3` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-30-02 | 30 | 3 | диспозиция-ревью-16 | T-16-71, T-16-72 | шесть находок повторного ревью раунда 4 — `fixed` с коммитами-предками `HEAD` (`feat(16-26)` … `feat(16-29)`); 26 прежних строк байт в байт; `open: 0`, `total: 32`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 5:** ни одной задачи без `<automated>`; у каждой из тринадцати задач
первая команда — модуль задачи (≈1–25 с), у каждой задачи кода последняя — quick run фазы, сторож живого
дерева гейта писателя либо замер живых деревьев гейта приватности; всего команд `<automated>` в партии 38, и
у каждой есть парный `<fails_when>` (замер планирования: 6/6, 9/9, 9/9, 9/9, 5/5). Сквозные гейты — на
волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 5 — ✅ у одиннадцати задач и «создаёт сама задача» у двух, и это
замер, а не умолчание:** на дереве `33a31ee3` нет ни `tests/phone_gate_grammar.py` (его заводит 16-27-01), ни
`tests/test_phone_gates_parity.py` (его заводит 16-29-02); прочие модули, в которые целятся задачи,
существуют.

### Партия закрытия гэпа, раунд 6: 16-31…16-35 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это седьмая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25, шестая 16-26…16-30), числа взяты
из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки шестой, поэтому одноимённые волны разных партий
одновременно не идут никогда.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 6, 2026-10-14T12:32:03Z, `gaps_found`, 70/72:
гэп 1 — WR-18, WR-20, WR-21, WR-22, WR-23 (пятнадцать форм гейта писателя), гэп 2 — WR-18 (путь
`methodcaller`), WR-19, WR-20 (шесть форм гейта приватности), advisory IN-15) и решения владельца О-14 (а)
«ловить все двадцать одну форму, заявления обоих гейтов прежние; ссылка, поданная любым именованным
аргументом, судится общим правилом по литеральным аргументам того же вызова, а не перечнем ключей; карты
псевдонимов многозначные; семантика носителя — функции общего модуля; словарь самопроверки прирастает осями
этого круга» и О-15 «IN-15 закрыть попутно» (2026-10-16, шестой прогон `/gsd-plan-phase 16 --gaps`, записаны
в `16-RESEARCH.md`); диспозиции и пересев реестра — умолчание прохода. Ось кратности связывания — один план на
оба гейта (16-31); семантика носителя переезжает в общий модуль планом гейта приватности (16-32), гейт
писателя переходит на неё, а словарь носителей прирастает в 16-34; лексика SQL и класс конструктора колонки —
16-33, параллельно с 16-32 (разные файлы). Опора — дерево `4cd68671` (код совпадает с `d725e473`, на котором
полный прогон дал `5091 passed, 2 skipped, 0 failed`); quick run на нём — `1106 passed`, `tests/test_planning`
— `218 passed, 2 skipped` (замер планирования до записей партии). Строки карты ниже добавлены планированием и
стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-31-01 | 31 | 1 | PHONE-02 | T-16-73 | скрипт дозаполнения с именем `w`, связанным с `session.bulk_update_mappings` в одной функции и с `setattr` в другой, в синтетическом `scripts/` краснит гейт писателя; карты псевдонимов многозначны, находки дедуплицируются по (строка, столбец, вид); пять форм WR-18 — строки; живое дерево 0 (WR-18, О-14 (а), D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-31-02 | 31 | 1 | PHONE-02, PHONE-21 | T-16-73, T-16-74 | поле `decoy` значения опознания и три строки повторного связывания в общем `BINDING_FORMS`; `_applied_log_methodcaller` — каждый кандидат; обе матрицы и правило-паритет — 360 ячеек на гейт без промахов (WR-18, D-17) | gate (AST, TDD, матрица, паритет) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-31-03 | 31 | 1 | PHONE-02, PHONE-21 | T-16-75 | шапки обоих гейтов называют правило «каждое связывание имени судится» и его цену, летопись WR-18; самопроверка оси кратности ≥ 5 000 / 2 000 форм; заявления прежние (запреты №2 планов 16-09…16-29) | gate (AST, TDD, шапки) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-32-01 | 32 | 2 | PHONE-21 | T-16-76, T-16-78 | `threading.Thread(target=logger.info, args=(…, account.phone))` в синтетическом `app/` краснит гейт приватности; `reference_arguments` общего модуля — общее правило именованного аргумента, `*`-распаковка, обёртка носителя; формы WR-19 / WR-20 — строки; идиома Celery — не вызов журнала; живые деревья 225 / 68 / 93 (новое место `app/worker/tasks.py:453`), ноль находок (D-11, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-32-02 | 32 | 2 | PHONE-21 | T-16-76, T-16-77 | `methodcaller` у любого носителя; `iterable_elements` с обёрткой итерируемой и `getattr_literal` — в общем модуле, копии гейта приватности сняты (IN-15, О-15); шесть будущих строк носителей — 360 ячеек без промахов | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-32-03 | 32 | 2 | PHONE-21 | T-16-77, T-16-78 | шапка — носитель без сужающей оговорки, общее правило, шесть носителей поимённо, цена `app/worker/tasks.py:453`, граница по аргументам нелитералом, летопись WR-19 / WR-20; самопроверка ≥ 5 000 форм; реестр `{}`, потолок 0 (запреты 16-18 №2, 16-23 №2, 16-29 №2) | gate (AST, TDD, шапка) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-33-01 | 33 | 2 | PHONE-02 | T-16-79 | скрипт с `UPDATE messenger_accounts SET 'phone' = :p` в синтетическом `scripts/` краснит гейт писателя; одинарные кавычки — четвёртый вид кавычек идентификатора; виды 5 (в) / (г) — по видимому SQL; шесть форм WR-21 / WR-22 — строки; живое дерево 0 (D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-33-02 | 33 | 2 | PHONE-02 | T-16-80 | `Column` / `ColumnClause` в `COLUMN_CONSTRUCTORS`, `name` в `COLUMN_NAME_KEYWORDS`; 39 наименований × 714 контекстов и 12 позиций имени без промахов; две формы WR-23 — строки | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-33-03 | 33 | 2 | PHONE-02 | T-16-81 | правило шапки — четыре вида кавычек SQLite и каждый конструктор колонки; цена однословной строки по замеру; летопись WR-21…WR-23; самопроверка лексики SQL и класса конструктора ≥ 20 000 форм; общий модуль не тронут | gate (AST, TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-34-01 | 34 | 3 | PHONE-02 | T-16-82 | поток скрипта дозаполнения `threading.Thread(target=setattr, args=(…))` в синтетическом `scripts/` краснит гейт писателя; `_referenced_calls` и `_methodcaller_receivers` — на `reference_arguments`; формы WR-20 и общего правила — строки; живое дерево 0 (D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-34-02 | 34 | 3 | PHONE-02, PHONE-21 | T-16-82, T-16-83 | копии семантики носителя в гейте писателя сняты, закрытая таблица ключа ссылки выведена; шесть строк `REFERENCE_CARRIERS` — 720 ячеек на гейт без промахов и расхождений; правило-паритет называет проверяемое и краснеет на каждом названном имени (IN-15, О-15) | gate (AST, TDD, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-34-03 | 34 | 3 | PHONE-02 | T-16-82 | шапка гейта писателя — общее правило именованного аргумента, цена, граница (1) по аргументам нелитералом, летопись WR-20 / IN-15; самопроверка ≥ 10 000 форм; живые деревья обоих гейтов прежние (запреты №2 планов 16-09…16-28) | gate (AST, TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ⬜ pending |
| 16-35-01 | 35 | 4 | диспозиция-ревью-16 | T-16-84 | WR-18 — `fixed` с существующими коммитами GREEN плана 16-31; прочие строки — как на `749ddfc5` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ⬜ pending |
| 16-35-02 | 35 | 4 | диспозиция-ревью-16 | T-16-84, T-16-85 | семь находок повторного ревью раунда 5 — `fixed` с коммитами-предками `HEAD` (`feat(16-31)` … `feat(16-34)`); поправка довода клетки WR-16 — в клетке WR-21; 32 прежние строки байт в байт; `open: 0`, `total: 39`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 6:** ни одной задачи без `<automated>`; у каждой из четырнадцати задач
первая команда — модуль задачи (≈1–30 с), у каждой задачи кода последняя — quick run фазы, сторож живого
дерева гейта писателя, замер живых деревьев гейта приватности либо прогон обоих гейтов с паритетом; всего
команд `<automated>` в партии 41, и у каждой есть парный `<fails_when>` (замер планирования: 9/9, 9/9, 9/9,
9/9, 5/5). Сквозные гейты — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 6 везде ✅, и это замер, а не умолчание:** все четырнадцать задач
целятся в модули, существующие на дереве `4cd68671` (`tests/phone_gate_grammar.py`, гейт писателя, гейт
приватности, `tests/test_phone_gates_parity.py`, записи `.planning/`); ни одного нового модуля партия не
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

### Волна 0 партии раунда 4 (16-21…16-25): пуста, и это замер

Партия **не заводит ни одного нового тестового модуля** — все десять задач целятся в файлы,
существующие на дереве `cce988cb` (`tests/test_services/test_phone.py`,
`tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_privacy_gate.py`,
`tests/test_application/test_account_phone_writer.py`, `app/services/phone.py`, записи `.planning/`).
Требований волны 0 у неё нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано):
число правил `tests/test_services/test_phone.py` растёт с 224 до 225 (16-21: правило-сверка пункта 5);
гейта писателя — с 316 до не менее чем 363 (16-22: два новых правила, правило-матрица по 16
наименованиям колонки, 21 строка `LITERAL_FORM_CASES` и 8 строк `LEGITIMATE_CASES`; плюс строки
самопроверки исполнителя, если она найдёт формы); гейта приватности — со 141 до не менее чем 168 (16-23:
три новых правила, 20 отрицательных и 4 положительных строки); теста писателя — прежние 24 (16-24). Строки,
которые партия СОЗНАТЕЛЬНО меняет (урок «тесты фазы закрепляют старые дефекты»): четыре строки
`POSITIVE_CONTROLS` гейта приватности утверждали «настройка опознанного журнала — не вызов журнала» и тем
закрепляли закрытый список методов, которого D-17 не задаёт (ревью WR-13), — 16-23-02 переименовывает их
(`…-is-judged-without-a-finding`) с летописью, флаг «вызов журнала» становится `True`, находок по-прежнему
ноль; пункт (1) границы гейта писателя перестаёт называть ссылку на пишущий API в переменной того же
модуля (16-22-02 её ловит). Числа распознанных вызовов журнала в живом правиле гейта приватности МЕНЯЮТСЯ
на измеренную настройку журнала: `app` 215 → 221, `max_worker` 89 → 93, `scripts` — прежние 68 (замер
прототипа планирования: новые вызовы — ровно `app/logging_config.py:46, :51, :52, :55, :56, :57` и
`max_worker/main.py:98, :101, :119, :120`; любое иное изменение — признак ложного распознавания). В
модуле-писателе гейт писателя по-прежнему видит 6 сырых записей. Перепись запретов получает строки планов
16-21…16-25 штатным засевом (оркестратор при коммите планов, повтор — 16-25-02).

### Волна 0 партии раунда 5 (16-26…16-30): два новых модуля, оба заводят сами задачи партии — это замер

Партия заводит ДВА новых модуля, и ни один не служит предпосылкой чужой задачи: `tests/phone_gate_grammar.py`
— вспомогательный, не тестовый (pytest собирает только `test_*.py`) — создаёт RED-коммит 16-27-01 (данные
`BINDING_FORMS`, `OUT_OF_GRAMMAR_BINDING_FORMS`) и его GREEN (функции грамматики); тестовый
`tests/test_phone_gates_parity.py` создаёт RED-коммит 16-29-02. Первая команда `<automated>` каждой задачи
целится либо в существующий модуль (`tests/test_services/test_phone.py`, гейт писателя, гейт приватности,
`tests/test_planning`), либо в модуль, который заводит RED-коммит той же задачи; отметка `MISSING — Wave 0`
не нужна ни одной задаче. Начиная с 16-29 quick run фазы несёт и `tests/test_phone_gates_parity.py` (так он
записан в `<verification>` планов 16-29 и 16-30).

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): число
правил `tests/test_services/test_phone.py` растёт с 225 до не менее чем 229 (16-26: два контроля-мутации —
три строки — и правило пункта 7); гейта писателя — с 412 до не менее чем 440 (16-27: трасер, 8 + 3 строки
форм и законных, 9 параметров матрицы оси B, 4 + 2 строки, правило шапки) и далее до не менее чем 469
(16-28: трасер, 10 позиций имени, 4 наименования колонки в матрице, 5 + 2 строки, правило сырого SQL,
4 + 2 строки); плюс строки самопроверок исполнителей, если они найдут формы; гейта приватности — со 170 до
не менее чем 195 (16-29: трасер, 6 + 3 строки, 9 параметров матрицы, 3 + 2 строки, правило шапки); модуль
паритета — 11 правил. Строки, которые партия СОЗНАТЕЛЬНО меняет (урок «тесты фазы закрепляют старые
дефекты»): пункт (1) границы гейта писателя перестаёт называть `w = partial(…); w(rows)` — связанный
`partial` теперь ловится, а гейт приватности ту же форму ловил давно (16-27-03, пример уходит в летопись);
`REFERENCE_KEYWORDS` гейта писателя и `_binding_pairs` гейта приватности переезжают в общий модуль
(16-27-02, 16-29-01); `RAW_SQL_PHONE_WRITE` теряет альтернативы (а) и (б) — их судит код (16-28-02). Строк,
которые партия переносит из таблицы в таблицу, нет: прототипы планирования прогнаны по всем прежним строкам
— 152 / 68 гейта писателя и 90 / 39 гейта приватности дают прежний ответ. Числа распознанных вызовов журнала
в живом правиле гейта приватности МЕНЯЮТСЯ ровно на носителя: `app` 221 → 224 (`app/pages/history.py:288`,
`:289`, `:293` — член записи `SendLog` под именем `log`, поданный вызову с аргументами за ним; цена
строгости 16-23), `scripts` — прежние 68, `max_worker` — прежние 93 (замер прототипа планирования; любое
иное изменение — признак ложного распознавания, разбирается по файлам). Живое дерево гейта писателя — ноль
судимых находок в 104 файлах, в модуле-писателе — 6 сырых. Перепись запретов получает строки планов
16-26…16-30 штатным засевом (оркестратор при коммите планов, повтор — 16-30-02).

### Волна 0 партии раунда 6 (16-31…16-35): пуста, и это замер

Партия **не заводит ни одного нового модуля** — все четырнадцать задач целятся в файлы, существующие на
дереве `4cd68671` (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`,
`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, записи `.planning/`). Требований
волны 0 у неё нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): гейт
писателя — с 493 до не менее чем 504 (16-31: трасер, 5 + 2 строки, 3 параметра матрицы оси B), далее до не
менее чем 522 (16-33: трасер, 6 + 2 строки, 3 наименования колонки и 2 позиции имени в матрицах, 2 + 1
строки, правило шапки) и до не менее чем 530 (16-34: трасер, 5 + 2 строки); гейт приватности — со 198 до не
менее чем 203 (16-31: 1 + 1 строки, 3 параметра матрицы) и до не менее чем 218 (16-32: трасер, 7 + 3 строки,
4 строки); правило-паритет — с 11 до 14 (16-31: три формы) и 15 (16-34: правило-контроль структурной
половины); quick run фазы — с 1106 до не менее чем 1167; плюс строки самопроверок исполнителей, если они
найдут формы. Словарь общего модуля: `BINDING_FORMS` 9 → 12, `REFERENCE_CARRIERS` 5 → 11 — матрицы обоих
гейтов и правило-паритет растут с 270 до 720 ячеек на гейт. Строки, которые партия СОЗНАТЕЛЬНО меняет (урок
«тесты фазы закрепляют старые дефекты»): фраза шапки гейта писателя о трёх видах кавычек идентификатора
становится фразой о четырёх (16-33-03); сужающая оговорка правила носителя гейта приватности о звёздной
распаковке снимается (16-32-03); закрытая таблица ключа ссылки выводится из общего модуля и обоих гейтов,
`BINDING_CASES` отбирает строки ссылки `run_sync` по `KIND_BY_REFERENCE` — параметры правила прежние
(16-34-02); докстринги правила-паритета перестают обещать отсутствие любых копий и называют проверяемое
(16-34-02); копии `_iterable_elements` / `_getattr_literal` обоих гейтов уходят в общий модуль (16-32-02,
16-34-02); строка `NEGATIVE_CONTROLS` `timer-args-log-reference` закрепляет форму, которую гейт приватности до
плана 16-32 ловил случайно. Строк, которые партия переносит из таблицы в таблицу, нет: прототипы планирования
прогнаны по всем прежним строкам — 190 / 84 гейта писателя и 102 / 44 гейта приватности дают прежний ответ.
Числа распознанных вызовов журнала в живом правиле гейта приватности МЕНЯЮТСЯ ровно на общее правило
именованного аргумента: `app` 224 → 225 (`app/worker/tasks.py:453` — член записи `SendLog` под именем
`send_log`, поданный именованным аргументом рядом с другими аргументами; цена строгости), `scripts` — прежние
68, `max_worker` — прежние 93 (замер прототипа планирования; любое иное изменение — признак ложного
распознавания, разбирается по файлам). Живое дерево гейта писателя — ноль судимых находок в 104 файлах, в
модуле-писателе — 6 сырых. Перепись запретов получает строки планов 16-31…16-35 штатным засевом (оркестратор
при коммите планов, повтор — 16-35-02).

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

**Партия закрытия гэпа, раунд 3 (16-16…16-20): validated 2026-10-12** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 12 строк партии зелёные на дереве `5abdd098` — `test_phone.py` 224 passed; `test_phone_single_writer_gate.py` 316 passed; `test_phone_privacy_gate.py` 141 passed; `test_account_phone_writer.py` с тестом гонки 28 passed; `tests/test_planning` 218 passed, 2 skipped; `prohibitions_census.py --check` rc 0 (реестр 788 строк, без пересева); quick run на слитом коде волны 1 — 856 passed. Полная суита на слитом коде волны 1 партии (`15b12ad1`; после него менялись только файлы `.planning/`) — `4841 passed, 2 skipped, 0 failed`. Пробелов 0; frontmatter (`status: validated`, `nyquist_compliant: true`) остаётся верным для всех 47 строк. Расхождения с прогнозом волны 0 и с прозой строк 16-17-02 и 16-18-02 (строки карты не переписаны, правда — здесь): гейт писателя вырос до 316 правил, а не до 296; таблица `JUDGED_PARAMETERS` — 34 строки, а не 33, и матрица — 32 × 4, а не 31 × 4 (исполнитель 16-17 нашёл, что `flag_modified` — запись, и закрыл ещё два класса форм самопроверкой; отступления — `16-17-SUMMARY.md`); гейт приватности вырос до 141 правила, а не до 126 (16-18 поймал формы той же оси сверх плана, `16-18-SUMMARY.md`); числа вызовов живого правила приватности не сдвинулись (215 / 68 / 89). До этой подписи абзац гласил: «**Партия закрытия гэпа, раунд 3 (16-16…16-20): pending**» (строки добавлены планированием 2026-10-12,
третий прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии
16-07…16-10 (10 задач) и к партии раунда 2 (11 задач). Партия раунда 3 добавляет двенадцать задач: у
каждой есть `<automated>` с парным `<fails_when>` (38 из 38), трёх подряд задач без машинной проверки
нет, новых тестовых модулей нет. Что планирование изменило в этом файле и почему: дописаны подраздел карты
партии раунда 3, подраздел её волны 0 и этот абзац; frontmatter (`status: validated`,
`nyquist_compliant: true`), прежние строки и прежние подписи НЕ тронуты — шаг 5.5 `/gsd-plan-phase`
оркестратор пропустил намеренно (он записал бы пустой шаблон поверх заполненной карты), а переоценку фазы
с двенадцатью новыми строками (всего строк станет 47) делает `/gsd-validate-phase 16` после исполнения
партии, а не планировщик.

**Партия закрытия гэпа, раунд 4 (16-21…16-25): validated 2026-10-13** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 10 строк партии зелёные на дереве `6895b196` — `test_phone.py` 225 passed; `test_phone_single_writer_gate.py` 412 passed; `test_phone_privacy_gate.py` 170 passed; `test_account_phone_writer.py` + `test_account_phone_race.py` 28 passed; quick run фазы 982 passed (на `fb17f03b`, код с тех пор не менялся); полная суита `4967 passed, 2 skipped, 0 failed` (на `fb17f03b`); `tests/test_planning` 218 passed, 2 skipped; `prohibitions_census.py --check` rc 0 (802 строки). Пробелов выборки 0 — у всех десяти задач есть `<automated>` по существующему модулю. Летопись: до 2026-10-13 — «pending» (строки добавлены планированием 2026-10-13,
четвёртый прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии
16-07…16-10 (10 задач), к партии раунда 2 (11 задач) и к партии раунда 3 (12 задач). Партия раунда 4
добавляет десять задач: у каждой есть `<automated>` с парным `<fails_when>` (30 из 30), трёх подряд задач
без машинной проверки нет, новых тестовых модулей нет. Что планирование изменило в этом файле и почему:
дописаны подраздел карты партии раунда 4, подраздел её волны 0 и этот абзац; frontmatter
(`status: validated`, `nyquist_compliant: true`), прежние строки и прежние подписи НЕ тронуты — шаг 5.5
`/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с десятью новыми
строками (всего строк станет 57) делает `/gsd-validate-phase 16` после исполнения партии, а не
планировщик.

**Партия закрытия гэпа, раунд 5 (16-26…16-30): validated 2026-10-14** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 13 строк партии зелёные на дереве `f3ac7f1d` — `tests/test_services/test_phone.py` 229 passed, `tests/test_application/test_phone_single_writer_gate.py` 493, `tests/test_phone_privacy_gate.py` 198, вместе с `tests/test_phone_gates_parity.py` 209, `tests/test_planning` 218 passed / 2 skipped, `scripts/prohibitions_census.py --check` rc 0 (819 строк); полная суита на `d725e473` (код с тех пор не менялся) — 5091 passed, 2 skipped, 0 failed. Столбец `File Exists` у 16-27-01 и 16-29-02 переписан: модули созданы RED-коммитами задач. До 2026-10-14 — pending (строки добавлены планированием 2026-10-13, пятый
прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии
16-07…16-10 (10 задач), к партиям раундов 2 (11 задач), 3 (12 задач) и 4 (10 задач). Партия раунда 5
добавляет тринадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (38 из 38), трёх подряд задач
без машинной проверки нет; новых модулей два — вспомогательный `tests/phone_gate_grammar.py` и тестовый
`tests/test_phone_gates_parity.py`, оба заводят сами задачи партии (подраздел волны 0 выше). Что
планирование изменило в этом файле и почему: дописаны подраздел карты партии раунда 5, подраздел её волны 0
и этот абзац; frontmatter (`status: validated`, `nyquist_compliant: true`), прежние строки, прежние подписи
и разделы аудита НЕ тронуты — шаг 5.5 `/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а
переоценку фазы с тринадцатью новыми строками (всего строк станет 70) делает `/gsd-validate-phase 16` после
исполнения партии, а не планировщик.

**Партия закрытия гэпа, раунд 6 (16-31…16-35): pending** (строки добавлены планированием 2026-10-16, шестой
прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10
(10 задач), к партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач) и 5 (13 задач). Партия раунда 6
добавляет четырнадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (41 из 41), трёх подряд
задач без машинной проверки нет, новых модулей нет (подраздел волны 0 выше). Что планирование изменило в этом
файле и почему: дописаны подраздел карты партии раунда 6, подраздел её волны 0 и этот абзац; frontmatter
(`status: validated`, `nyquist_compliant: true`), прежние строки, прежние подписи и разделы аудита НЕ тронуты —
шаг 5.5 `/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с
четырнадцатью новыми строками (всего строк станет 84) делает `/gsd-validate-phase 16` после исполнения
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

## Validation Audit 2026-10-12 (партия закрытия гэпа, раунд 3: 16-16…16-20)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой: `verification.append-audit` пропустил запись (`appended: false`), потому что
последний блок аудита тоже 0/0/0. Предмет аудита другой — двенадцать строк партии раунда 3,
измеренные на `5abdd098` (числа — в подписи выше).

## Validation Audit 2026-10-13 (партия закрытия гэпа, раунд 4: 16-21…16-25)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раунда 3: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает. Предмет аудита другой — десять строк партии раунда 4, измеренные на `6895b196` (числа — в подписи выше).

## Validation Audit 2026-10-14 (партия закрытия гэпа, раунд 5: 16-26…16-30)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3 и 4: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает. Предмет аудита — 13 строк партии раунда 5; все зелёные на `f3ac7f1d`, гэпов нет, аудитор не вызывался.
