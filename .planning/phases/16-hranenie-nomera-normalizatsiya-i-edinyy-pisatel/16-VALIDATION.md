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
| 16-31-01 | 31 | 1 | PHONE-02 | T-16-73 | скрипт дозаполнения с именем `w`, связанным с `session.bulk_update_mappings` в одной функции и с `setattr` в другой, в синтетическом `scripts/` краснит гейт писателя; карты псевдонимов многозначны, находки дедуплицируются по (строка, столбец, вид); пять форм WR-18 — строки; живое дерево 0 (WR-18, О-14 (а), D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-31-02 | 31 | 1 | PHONE-02, PHONE-21 | T-16-73, T-16-74 | поле `decoy` значения опознания и три строки повторного связывания в общем `BINDING_FORMS`; `_applied_log_methodcaller` — каждый кандидат; обе матрицы и правило-паритет — 360 ячеек на гейт без промахов (WR-18, D-17) | gate (AST, TDD, матрица, паритет) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-31-03 | 31 | 1 | PHONE-02, PHONE-21 | T-16-75 | шапки обоих гейтов называют правило «каждое связывание имени судится» и его цену, летопись WR-18; самопроверка оси кратности ≥ 5 000 / 2 000 форм; заявления прежние (запреты №2 планов 16-09…16-29) | gate (AST, TDD, шапки) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-32-01 | 32 | 2 | PHONE-21 | T-16-76, T-16-78 | `threading.Thread(target=logger.info, args=(…, account.phone))` в синтетическом `app/` краснит гейт приватности; `reference_arguments` общего модуля — общее правило именованного аргумента, `*`-распаковка, обёртка носителя; формы WR-19 / WR-20 — строки; идиома Celery — не вызов журнала; живые деревья 225 / 68 / 93 (новое место `app/worker/tasks.py:453`), ноль находок (D-11, D-17) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-32-02 | 32 | 2 | PHONE-21 | T-16-76, T-16-77 | `methodcaller` у любого носителя; `iterable_elements` с обёрткой итерируемой и `getattr_literal` — в общем модуле, копии гейта приватности сняты (IN-15, О-15); шесть будущих строк носителей — 360 ячеек без промахов | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-32-03 | 32 | 2 | PHONE-21 | T-16-77, T-16-78 | шапка — носитель без сужающей оговорки, общее правило, шесть носителей поимённо, цена `app/worker/tasks.py:453`, граница по аргументам нелитералом, летопись WR-19 / WR-20; самопроверка ≥ 5 000 форм; реестр `{}`, потолок 0 (запреты 16-18 №2, 16-23 №2, 16-29 №2) | gate (AST, TDD, шапка) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-33-01 | 33 | 2 | PHONE-02 | T-16-79 | скрипт с `UPDATE messenger_accounts SET 'phone' = :p` в синтетическом `scripts/` краснит гейт писателя; одинарные кавычки — четвёртый вид кавычек идентификатора; виды 5 (в) / (г) — по видимому SQL; шесть форм WR-21 / WR-22 — строки; живое дерево 0 (D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-33-02 | 33 | 2 | PHONE-02 | T-16-80 | `Column` / `ColumnClause` в `COLUMN_CONSTRUCTORS`, `name` в `COLUMN_NAME_KEYWORDS`; 39 наименований × 714 контекстов и 12 позиций имени без промахов; две формы WR-23 — строки | gate (AST, TDD, матрица) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-33-03 | 33 | 2 | PHONE-02 | T-16-81 | правило шапки — четыре вида кавычек SQLite и каждый конструктор колонки; цена однословной строки по замеру; летопись WR-21…WR-23; самопроверка лексики SQL и класса конструктора ≥ 20 000 форм; общий модуль не тронут | gate (AST, TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-34-01 | 34 | 3 | PHONE-02 | T-16-82 | поток скрипта дозаполнения `threading.Thread(target=setattr, args=(…))` в синтетическом `scripts/` краснит гейт писателя; `_referenced_calls` и `_methodcaller_receivers` — на `reference_arguments`; формы WR-20 и общего правила — строки; живое дерево 0 (D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-34-02 | 34 | 3 | PHONE-02, PHONE-21 | T-16-82, T-16-83 | копии семантики носителя в гейте писателя сняты, закрытая таблица ключа ссылки выведена; шесть строк `REFERENCE_CARRIERS` — 720 ячеек на гейт без промахов и расхождений; правило-паритет называет проверяемое и краснеет на каждом названном имени (IN-15, О-15) | gate (AST, TDD, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-34-03 | 34 | 3 | PHONE-02 | T-16-82 | шапка гейта писателя — общее правило именованного аргумента, цена, граница (1) по аргументам нелитералом, летопись WR-20 / IN-15; самопроверка ≥ 10 000 форм; живые деревья обоих гейтов прежние (запреты №2 планов 16-09…16-28) | gate (AST, TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-35-01 | 35 | 4 | диспозиция-ревью-16 | T-16-84 | WR-18 — `fixed` с существующими коммитами GREEN плана 16-31; прочие строки — как на `749ddfc5` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-35-02 | 35 | 4 | диспозиция-ревью-16 | T-16-84, T-16-85 | семь находок повторного ревью раунда 5 — `fixed` с коммитами-предками `HEAD` (`feat(16-31)` … `feat(16-34)`); поправка довода клетки WR-16 — в клетке WR-21; 32 прежние строки байт в байт; `open: 0`, `total: 39`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

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

### Партия закрытия гэпа, раунд 7: 16-36…16-40 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это восьмая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25, шестая 16-26…16-30, седьмая
16-31…16-35), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки седьмой, поэтому
одноимённые волны разных партий одновременно не идут никогда. Внутри партии параллельных волн нет: планы
16-36…16-39 правят общий модуль `tests/phone_gate_grammar.py` и модули гейтов, и каждая волна несёт один план.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 7, 2026-10-16T14:10:15Z, `gaps_found`, 82/85: гэп 1 —
CR-03, WR-26 (гейт писателя, истина 18), гэп 2 — CR-02, WR-25, WR-26 (гейт приватности, истина 28), гэп 3 — WR-24
(копия семантики обёртки носителя, истина 78), advisory IN-16, IN-17; впервые — регрессии против базы: CR-02 внёс
`c6953017`, CR-03 — `147f5e46`), находки повторного ревью раунда 6 (`16-REVIEW.md`, `2f8c1656..a3f3ee0d`) и решения
владельца О-16 (а) «чинить предикаты, заявления прежние, и обязательная сверка с базой» — девять связывающих
свойств, в том числе новая мера «база ↔ HEAD» каждого GREEN против родителя и право плана О-15 править модуль гейта
приватности — и О-17 «IN-16, IN-17 — в плане гэпа 3» (2026-10-18, седьмой прогон `/gsd-plan-phase 16 --gaps`,
записаны в `16-RESEARCH.md`); диспозиции, пересев реестра и эта карта — умолчание прохода. Опора — дерево
`65e5c692` (код гейтов совпадает с `21d463f0`; полный прогон на `e5a4492c` — `5181 passed, 2 skipped`); quick run
на нём — `1196 passed`, три модуля гейтов — `792 passed`, `tests/test_planning` — `218 passed, 2 skipped` (замер
планирования до записей партии). Строки карты ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-36-01 | 36 | 1 | PHONE-02 | T-16-86, T-16-87 | скрипт дозаполнения с `functools.partial(ctx.run, setattr, account, "phone", number)`, поданным `run_in_executor`, в синтетическом `scripts/` краснит гейт писателя; общая `wrapper_applications` судит обёртку на каждом чтении, поглощение — только по судимым чтениям; четыре формы CR-03, четыре WR-26 и контроль «без использования» — строки; инструмент сверки «база ↔ HEAD» с самопроверкой на известных регрессиях (`SELFTEST` пар `c6953017`, `147f5e46` — больше нуля), `OPEN_REGRESSIONS=0` (CR-03, WR-26, О-16 (а), D-13) | tracer (gate, AST, TDD, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-36` | ✅ (инструмент сверки в gitignored `.pytest_cache/r7diff/` заводит сама задача) | ✅ green |
| 16-36-02 | 36 | 1 | PHONE-02 | T-16-86 | общий рекурсивный `is_carrier_wrapper`: обёртка поверх обёртки литералом и именем, глубина до трёх, циклы без зависания; `methodcaller` в поданной обёртке получает получателя; четыре строки и две законные (WR-26) | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-36-03 | 36 | 1 | PHONE-02 | T-16-86, T-16-87 | шапка гейта писателя — суд обёртки на каждом чтении, раскрытие поданной и вложенной обёртки, цена, летопись седьмого круга с регрессией `147f5e46`; самопроверка ≥ 10 000 форм; сверка каждого GREEN с родителем и `BASE` — ноль регрессий; заявление прежнее (запреты №2 планов 16-09…16-34) | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-36` | ✅ | ✅ green |
| 16-37-01 | 37 | 2 | PHONE-21 | T-16-88, T-16-89 | служба с обёрткой журнала в атрибуте, вызванной getattr-строкой, в синтетическом `app/` краснит гейт приватности; копия `_carrier_wrappers` и ручное применение сняты — общие `carrier_wrapper_bindings` / `is_carrier_wrapper` / `named_wrappers` / `applied_wrapper`; одно место — одна находка; `REQUIRED_SHARED_NAMES` с этими именами (WR-24, О-15, D-11) | tracer (gate, AST, TDD, паритет) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-37` | ✅ | ✅ green |
| 16-37-02 | 37 | 2 | PHONE-21 | T-16-88 | обёртка журнала, поданная носителю любым способом, обёрнутая `partial` и вложенная до трёх уровней, — общей `wrapper_applications`; `methodcaller` в поданной обёртке; не-журнальная ссылка — не вызов журнала; семь строк и строка `POSITIVE_CONTROLS` (WR-26, D-17) | gate (AST, TDD, паритет) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-37-03 | 37 | 2 | PHONE-21 | T-16-88, T-16-89 | шапка гейта приватности правдива — своих копий нет, суд обёртки на каждом чтении, раскрытие поданной и вложенной; IN-16 (комментарий ввоза), IN-17 (прошедшее время строк 16-34); летописи WR-24 / WR-26; самопроверка ≥ 5 000 форм; JS-половина — 27 символов без изменений; сверка с базой (О-17) | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-37` | ✅ | ✅ green |
| 16-38-01 | 38 | 3 | PHONE-21 | T-16-90 | отчёт с `list(map(logger.info, account.phones))` в синтетическом `app/` краснит гейт приватности; `reference_arguments(…, keep_iterables=True)` — итерируемая поэлементного носителя целиком, гейт писателя читает `map` прежним образом; семь форм CR-02 — строки, `account.names` — вызов без находки (CR-02, регрессия `c6953017`, D-11) | tracer (gate, AST, TDD, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-38` | ✅ | ✅ green |
| 16-38-02 | 38 | 3 | PHONE-21, PHONE-02 | T-16-90, T-16-91 | одно правило носителей: `ELEMENTWISE_CARRIERS` (`map`, `imap`, `imap_unordered`, `map_async`), `ROW_CARRIERS` (`starmap`, `starmap_async`) — сторож против stdlib; `methodcaller` у `starmap` — первый элемент строки; две формы WR-25 и закрепки; докстринг `reference_arguments` правдив (WR-25) | gate (AST, TDD, паритет, сторож) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-38-03 | 38 | 3 | PHONE-21, PHONE-02 | T-16-90, T-16-91 | шапки: суд итерируемой поэлементного и построчного носителя целиком, граница «судится само выражение» снова правда, одно правило носителей в обеих шапках, летопись CR-02 / WR-25; самопроверка ≥ 3 000 / 2 000 форм; сверка с базой | gate (AST, TDD, шапки, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-38` | ✅ | ✅ green |
| 16-39-01 | 39 | 4 | PHONE-02, PHONE-21 | T-16-92 | строка словаря `named-wrapper-bound-handed` (форма CR-03) — обе матрицы по 60 ячеек и правило-паритет, обе шапки её называют (свойство 6) | tracer (gate, AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-39` | ✅ | ✅ green |
| 16-39-02 | 39 | 4 | PHONE-02, PHONE-21 | T-16-92 | восемь строк словаря и поле `ReferenceCarrier.last` — 20 носителей, 1 260 ячеек на гейт без промахов и расхождений; правило `test_the_shared_dictionary_holds_the_round_seven_axes` (CR-02, WR-24, WR-25, WR-26) | gate (AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-39-03 | 39 | 4 | PHONE-02, PHONE-21 | T-16-92, T-16-93 | летопись словаря и меры в обеих шапках; итоговая самопроверка ≥ 20 000 форм на гейт; сверка «база ↔ HEAD» партии — каждый GREEN, против базы партии и против `2f8c1656` — ноль регрессий (свойство 7) | gate (AST, TDD, шапки, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r7diff/run.sh 16-39 && bash .pytest_cache/r7diff/run.sh --against-batch 16-36 && bash .pytest_cache/r7diff/run.sh --against 2f8c1656` | ✅ | ✅ green |
| 16-40-01 | 40 | 5 | диспозиция-ревью-16 | T-16-94 | CR-03 — `fixed` с существующими коммитами GREEN плана 16-36 и итогом сверки; прочие строки — как на `b1b41431` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-40-02 | 40 | 5 | диспозиция-ревью-16 | T-16-94, T-16-95 | семь находок повторного ревью раунда 6 — `fixed` с коммитами-предками `HEAD` (`feat(16-36)` … `feat(16-39)`); 39 прежних строк байт в байт с `b1b41431`; `open: 0`, `total: 46`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 7:** ни одной задачи без `<automated>`; у каждой из четырнадцати задач
первая команда — модуль задачи или три модуля гейтов (≈1–50 с); у каждой задачи кода последняя — сверка
«база ↔ HEAD» (`bash .pytest_cache/r7diff/run.sh 16-3N`; у 16-39-03 — и против базы партии, и против `2f8c1656`),
у задач записей — `tests/test_planning`; каждый запуск сверки начинается самопроверкой инструмента на
известных регрессиях `c6953017` и `147f5e46` (строки `SELFTEST`), а корпус по источникам с размерами и правилом
выборки записывается в сводку плана; всего команд `<automated>` в партии 51, и у каждой есть парный
`<fails_when>` (замер планирования: 12/12, 12/12, 12/12, 10/10, 5/5). Сквозные гейты
(`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`,
`test_logging_config.py`) названы в последней задаче каждого плана кода и в `<verification>` — на волну, как у
прежних партий.

**Столбец `File Exists` у партии раунда 7 везде ✅, и это замер, а не умолчание:** все четырнадцать задач
целятся в модули, существующие на дереве `65e5c692` (`tests/phone_gate_grammar.py`, гейт писателя, гейт
приватности, `tests/test_phone_gates_parity.py`, записи `.planning/`); ни одного нового модуля в репозитории партия
не заводит. Инструмент сверки «база ↔ HEAD» (`.pytest_cache/r7diff/corpus.py`, `judge.py`, `run.sh`) — gitignored и
в репозиторий не коммитится: его собирает по договору `16-36-PLAN.md` первая задача каждого плана кода в своём
worktree, поэтому в столбце он не учитывается.

### Партия закрытия гэпа, раунд 8: 16-41…16-45 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это девятая партия фазы (первая 16-01…16-06, вторая
16-07…16-10, третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25, шестая 16-26…16-30, седьмая
16-31…16-35, восьмая 16-36…16-40), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки
восьмой, поэтому одноимённые волны разных партий одновременно не идут никогда. Внутри партии параллельных волн нет:
планы 16-41…16-44 правят модули гейтов и общий модуль `tests/phone_gate_grammar.py` и делят инструмент сверки с осью
счёта, каждая волна несёт один план.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 8, 2026-10-19T15:32:57Z, `gaps_found`, 98/101: гэп 1 — WR-28
(гейт писателя, истина 18), гэп 2 — WR-28 (гейт приватности, истина 28): имя, связанное с `methodcaller` и прочитанное
getattr-строкой, не ловит ни один гейт; гэп 3 — WR-27 (истина 101): регрессия счёта `51d0d766` против `1c243203` —
две разные подачи на одной строке дают одну находку, а правило «одно место — одна находка» вакуумно; advisory IN-18,
IN-19, IN-20; на оси «есть находка» регрессий нет), находки повторного ревью раунда 7 (`16-REVIEW.md`,
`38675285..52fcbadc`) и решения владельца О-18 (а) «чинить, заявления прежние» — семь связывающих свойств, в том числе
один читатель имени у обоих гейтов, место «строка, столбец, вид, предмет», правило счёта, считающее места, и ось счёта в
сверке «база ↔ HEAD» на обоих гейтах — и О-19 «IN-18, IN-19, IN-20 — попутно» (2026-10-19, восьмой прогон
`/gsd-plan-phase 16 --gaps`, записаны в `16-RESEARCH.md`); диспозиции, пересев реестра и эта карта — умолчание прохода.
Опора — дерево `8aabdb38` (код гейтов совпадает с `defeaae4`; полный прогон на `fdadd46c` — `5236 passed, 2 skipped`);
три модуля гейтов на нём — `847 passed`, quick run — `1251 passed`, `tests/test_planning` — `218 passed, 2 skipped`
(замер планирования до записей партии). Строки карты ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-41-01 | 41 | 1 | PHONE-21 | T-16-96, T-16-97 | отчёт с двумя номерами в одном вызове журнала в синтетическом `app/` краснит гейт приватности двумя находками на одной строке; место находки — узел (строка и столбец); четыре формы WR-27 — по две находки, форма WR-24 — одна, матрица — ровно одна на ячейку; правило строк считает места по `NEGATIVE_CONTROL_PLACES`, контроль ловит дедупликацию по тексту; инструмент сверки с осью счёта (`SELFTEST-COUNT 51d0d766^ -> 51d0d766` — больше нуля), `OPEN_REGRESSIONS=0` (WR-27, О-18 (а), D-11) | tracer (gate, AST, TDD, сверка с базой по обеим осям) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-41` | ✅ (инструмент сверки в gitignored `.pytest_cache/r8diff/` заводит сама задача) | ✅ green |
| 16-41-02 | 41 | 1 | PHONE-21 | T-16-96, T-16-97 | шапка и докстринг `python_log_offences` называют место «строка, столбец, вид, предмет», летопись WR-27; самопроверка оси счёта ≥ 5 000 форм с числом мест генератора; сверка каждого GREEN и `BASE` — ноль регрессий обеих осей; JS-половина — 27 символов без изменений | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-41` | ✅ | ✅ green |
| 16-42-01 | 42 | 2 | PHONE-02 | T-16-98, T-16-99 | скрипт дозаполнения с `methodcaller("__set__", account, number)` в атрибуте, прочитанным getattr-строкой, в синтетическом `scripts/` краснит гейт писателя; один общий читатель имени `reading_name` в `methodcallers_of`, `is_reference`, `named_wrappers`; две формы WR-28 — строки, девять вариантов чтения — по одной находке, законные — ноль (WR-28, О-18 (а), D-13) | tracer (gate, AST, TDD, сверка с базой по обеим осям) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-42` | ✅ | ✅ green |
| 16-42-02 | 42 | 2 | PHONE-02 | T-16-98, T-16-99 | шапка гейта писателя правдива на оси «где прочитано имя»: `methodcaller` под именем — на каждом чтении через `reading_name`, летопись восьмого круга; самопроверка ≥ 5 000 форм; сверка с базой по обеим осям; заявление прежнее (запреты №2 планов 16-09…16-39) | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-42` | ✅ | ✅ green |
| 16-43-01 | 43 | 3 | PHONE-21 | T-16-100 | служба с `methodcaller` в атрибуте, прочитанным getattr-строкой и применённым к журналу, в синтетическом `app/` краснит гейт приватности; `_methodcaller_calls` на общем `reading_name`; две формы WR-28 — строки, тот же `methodcaller` без номера — вызов журнала без находки; `reading_name` в `REQUIRED_SHARED_NAMES` и `CARRIER_SEMANTICS` (WR-28, О-18 (а), D-11) | tracer (gate, AST, TDD, паритет, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-43` | ✅ | ✅ green |
| 16-43-02 | 43 | 3 | PHONE-21 | T-16-101 | IN-20: довод `ReferenceCarrier.last` правдив; форма `partial` с не-литеральной итерируемой у `map` — строка `NEGATIVE_CONTROLS`, которую дерево `1c243203` не ловит; правило `test_the_partial_value_place_is_pinned_by_a_privacy_row` (О-19) | gate (AST, TDD, паритет, замер базы) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-43-03 | 43 | 3 | PHONE-21 | T-16-100, T-16-101 | шапка гейта приватности: `methodcaller` под именем — через `reading_name`, getattr-строкой тоже; граница правдива; летопись WR-28 (седьмой круг оси «как опознан журнал»); самопроверка ≥ 5 000 форм; сверка с базой по обеим осям; JS-половина — 27 символов без изменений | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-43` | ✅ | ✅ green |
| 16-44-01 | 44 | 4 | PHONE-02, PHONE-21 | T-16-102 | форма `getattr-read` — строка `BINDING_FORMS`: обе матрицы держат её для каждого значения и носителя без промахов, правило-паритет — без расхождений, обе шапки её называют (свойство 3) | tracer (gate, AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-44` | ✅ | ✅ green |
| 16-44-02 | 44 | 4 | PHONE-02, PHONE-21 | T-16-102 | значение `methodcaller-receiver` у обоих гейтов на одной позиции; `API_IDENTIFICATION_CALLS` полна; 13 форм × 6 значений × 21 способ = 1 638 ячеек на гейт без промахов; правило словаря восьмого круга (свойство 3) | gate (AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-44-03 | 44 | 4 | PHONE-02, PHONE-21 | T-16-102, T-16-103 | IN-18 и IN-19 — правила летописей словаря и докстринга паритета; летопись словаря восьмого круга в обеих шапках; итоговая самопроверка ≥ 15 000 форм на гейт; сверка «база ↔ HEAD» партии по обеим осям — каждый GREEN, база партии, `1c243203`, `2f8c1656` — ноль регрессий, `HEAD_WRONG=0`; замер `--rows` (О-19; свойства 6, 7) | gate (AST, TDD, шапки, паритет, сверка с базой) | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q -p no:randomly` и `bash .pytest_cache/r8diff/run.sh 16-44 && bash .pytest_cache/r8diff/run.sh --against-batch 16-41 && bash .pytest_cache/r8diff/run.sh --against 1c243203 && bash .pytest_cache/r8diff/run.sh --against 2f8c1656` | ✅ | ✅ green |
| 16-45-01 | 45 | 5 | диспозиция-ревью-16 | T-16-104 | WR-27 — `fixed` с существующими коммитами GREEN плана 16-41 и итогом сверки по оси счёта; прочие строки — как на `90052e5c` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-45-02 | 45 | 5 | диспозиция-ревью-16 | T-16-104, T-16-105 | пять находок повторного ревью раунда 7 — `fixed` с коммитами-предками `HEAD` (`feat(16-41)` … `feat(16-44)`); 46 прежних строк байт в байт с `90052e5c`; `open: 0`, `total: 51`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 8:** ни одной задачи без `<automated>`; у каждой из двенадцати задач
первая команда — модуль задачи или три модуля гейтов (≈1–55 с); у каждой задачи кода последняя — сверка «база ↔
HEAD» с осью счёта (`bash .pytest_cache/r8diff/run.sh 16-4N`; у 16-44-03 — цепочка против базы партии, `1c243203`,
`2f8c1656` и за ней режим `--rows`), у
задач записей — `tests/test_planning`; каждый запуск сверки начинается самопроверкой инструмента на известных
регрессиях по обеим осям (строки `SELFTEST` пар `c6953017`, `147f5e46` и `SELFTEST-COUNT` пары `51d0d766`), а корпус по
источникам с размерами и правилом выборки записывается в сводку плана; всего команд `<automated>` в партии 50, и у
каждой есть парный `<fails_when>` (замер планирования `verify-failure-directions`: 10/10, 11/11, 13/13, 11/11, 5/5; 0
блокеров, 0 предупреждений). Сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`,
`test_declared_invariants.py`, `test_logging_config.py`) названы в последней задаче каждого плана кода и в
`<verification>` — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 8 везде ✅, и это замер, а не умолчание:** все двенадцать задач целятся в
модули, существующие на дереве `8aabdb38` (`tests/phone_gate_grammar.py`, гейт писателя, гейт приватности,
`tests/test_phone_gates_parity.py`, записи `.planning/`); ни одного нового модуля в репозитории партия не заводит.
Инструмент сверки «база ↔ HEAD» с осью счёта (`.pytest_cache/r8diff/corpus.py`, `judge.py`, `run.sh`) — gitignored и в
репозиторий не коммитится: его собирает по договору `16-41-PLAN.md` первая задача плана 16-41 (планы 16-42…16-44 берут
копию от оркестратора или собирают его заново по тому же договору), поэтому в столбце он не учитывается.

### Партия закрытия гэпа, раунд 9: 16-46…16-50 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это десятая партия фазы (первая 16-01…16-06, вторая 16-07…16-10,
третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25, шестая 16-26…16-30, седьмая 16-31…16-35, восьмая
16-36…16-40, девятая 16-41…16-45), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ приёмки девятой,
поэтому одноимённые волны разных партий одновременно не идут никогда. Внутри партии параллельных волн нет: планы
16-46…16-49 правят модули гейтов и общий модуль `tests/phone_gate_grammar.py` и делят инструмент сверки
`.pytest_cache/r9diff/`, каждая волна несёт один план.

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 9, 2026-10-20T06:31:40Z, `gaps_found`, 112/115: гэп 1 — истина 114,
CR-04 — регрессия наличия `a77263ad` (цикл самопроверки 1 плана 16-43) против `e1d6587e`, `fb8fef72` и `1c243203`, WR-29 —
ложные находки того же коммита, IN-21; гэп 2 — истина 28, WR-30 и давний класс коллизии C5–C7; гэп 3 — истина 115, WR-31 —
слияние двух подач колонки через получатель `methodcaller`, закреплённое мерой 16-44), находки повторного ревью раунда 8
(`16-REVIEW.md`, `42c78bfd..e9449db5`) и решения владельца О-20 (а) «чинить, заявления прежние» (восемь связывающих
свойств), О-21 (а) «чужие корпуса — обязательный вход меры» (семь свойств) и О-22 (а) «цена атрибута названа, ничего не
теряется» (2026-10-20 и 2026-10-21, девятый прогон `/gsd-plan-phase 16 --gaps`, записаны в `16-RESEARCH.md`, строки
742-767); диспозиции, пересев реестра и эта карта — умолчание прохода. Опора — дерево `1163ae39` (код гейтов совпадает с
`dbc73537`; полная суита на `e9449db5` — `5280 passed, 2 skipped`); три модуля гейтов на нём — `891 passed`, quick run —
`1295 passed`, `tests/test_planning` — `218 passed, 2 skipped` (замер до записей партии). Строки карты ниже добавлены
планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-46-01 | 46 | 1 | PHONE-21 | T-16-106, T-16-107 | служба с одним именем, связанным и с `print`, и с `methodcaller` над номером, в синтетическом `app/` краснит гейт приватности одной находкой; каждое толкование узла судится (опознанный вызов не закрывает путь `methodcaller` и обёрток); девять форм CR-04 / C5–C7 — по одной находке, двойники — вызов журнала без находки, матрица — по одной; инструмент r9diff: чужие корпуса (29 941 ячейка) целиком после сверки манифеста, `SELFTEST-CR04 e1d6587e -> a77263ad` и `REPRODUCE` против вакуума, `OPEN_REGRESSIONS=0` (CR-04, О-20 (а), О-21 (а), D-11) | tracer (gate, AST, TDD, сверка с базой по обеим осям на чужих корпусах) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-46` | ✅ (инструмент сверки и копия чужих входов — в gitignored `.pytest_cache/`, их заводит сама задача) | ✅ green |
| 16-46-02 | 46 | 1 | PHONE-21 | T-16-106, T-16-107 | шапка гейта приватности: суд каждого толкования узла, летопись CR-04; самопроверка оси коллизии ≥ 10 000 форм с числом мест генератора; сверка каждого GREEN и `BASE` — ноль регрессий обеих осей; JS-половина — 27 символов без изменений | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-46` | ✅ | ✅ green |
| 16-47-01 | 47 | 2 | PHONE-21 | T-16-108, T-16-109 | журнал модуля, прочитанный через `sys.modules[__name__]`, краснит гейт приватности, а запись номера в файл методом с именем вызываемого журнала — нет; помощник `_is_module_object`; семь форм WR-30 — по одной находке, четыре формы WR-29 — не вызов журнала; форма у параметра (О-22 (а)) — одна находка; строки цикла 1 плана 16-43 — прежние (WR-29, WR-30, О-20 (а), D-11, D-17) | tracer (gate, AST, TDD, сверка с базой на чужих корпусах) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-47` | ✅ | ✅ green |
| 16-47-02 | 47 | 2 | PHONE-21 | T-16-108, T-16-109 | шапка: объект модуля в «ПО СВЯЗЫВАНИЮ», цена атрибута по О-22 (а) рядом с `log.mark_failed(…)` с замером живого дерева, летописи WR-29 и WR-30; улика исполнения `cost_evidence.py` (`EVIDENCE attr: file=… log=''`); строка `COST … attr=122`; самопроверка ≥ 10 000 форм; сверка с базой по обеим осям | gate (AST, TDD, шапка, улика, сверка с базой) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`, `uv run python .pytest_cache/r9diff/cost_evidence.py` и `bash .pytest_cache/r9diff/run.sh 16-47` | ✅ | ✅ green |
| 16-48-01 | 48 | 3 | PHONE-02 | T-16-110 | скрипт с двумя применениями одного `methodcaller` к колонке в синтетическом `scripts/` краснит гейт писателя двумя находками; место записи через получатель — узел получателя; три формы WR-31 — по две находки, контроль литерала — одна; правило таблицы считает места по `LITERAL_FORM_PLACES`, контроль ловит слияние; трасер 16-42 — место 8 → 11 (запланированная смена) (WR-31, О-20 (а), D-13) | tracer (gate, AST, TDD, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-48` | ✅ | ✅ green |
| 16-48-02 | 48 | 3 | PHONE-02 | T-16-111 | вызов, чьё последнее имя связано с пишущим API или `partial` над ним, судится и как носитель: четыре формы коллизии имени носителя — по одной находке, законный двойник — ноль (свойство 2 О-20 на оси носителя; D-07, D-13) | gate (AST, TDD, сверка с базой) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-48` | ✅ | ✅ green |
| 16-48-03 | 48 | 3 | PHONE-02 | T-16-110, T-16-111 | шапка писателя: место через получатель, суд каждого толкования, цена оси носителя; летопись WR-31; самопроверка двух осей ≥ 10 000 форм; сверка с базой и `--against 2f8c1656` — ноль регрессий, `EXTERNAL … defects=0`, переклассификация `REPAIRED` D2 | gate (AST, TDD, шапка, сверка с базой) | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-48 && bash .pytest_cache/r9diff/run.sh --against 2f8c1656` | ✅ | ✅ green |
| 16-49-01 | 49 | 4 | PHONE-02, PHONE-21 | T-16-112 | восемь форм девятого круга (`collision-*`, `module-object-*`) — строки `BINDING_FORMS` с соперником значения (`IdentificationValue.rival`): обе матрицы без промахов, правило-паритет без расхождений, обе шапки их называют (свойство 6) | tracer (gate, AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-49` | ✅ | ✅ green |
| 16-49-02 | 49 | 4 | PHONE-02, PHONE-21 | T-16-112 | значение `receiver` у обоих гейтов (`IdentificationValue.method`), носители с соперником под своим именем, `API_IDENTIFICATION_CALLS` полна; 21 форма × 7 значений × 23 способа = 3 381 ячейка на гейт без промахов (свойство 6) | gate (AST, TDD, матрицы, паритет) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-49` | ✅ | ✅ green |
| 16-49-03 | 49 | 4 | PHONE-02, PHONE-21 | T-16-112, T-16-113 | IN-21 — летописи восьмого круга называют корпус меры, летопись девятого — так же, правило летописей меры; итоговая самопроверка ≥ 15 000 форм на гейт; улика обеих названных цен; сверка «база ↔ HEAD» партии против базы партии, `fb8fef72`, `1c243203`, `2f8c1656` — ноль регрессий, `HEAD_WRONG=0`, `EXTERNAL … defects=0`, `COST kw=281 attr=122`; режим `--dictionary` (свойства 7, 8 О-20; свойства 3, 7 О-21) | gate (AST, TDD, шапки, паритет, улика, сверка с базой) | `uv run pytest tests/test_services/test_phone.py tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_application/test_phone_single_writer_gate.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_models/test_messenger_account_phone_check.py tests/test_migrations -q -p no:randomly` и `bash .pytest_cache/r9diff/run.sh 16-49 && bash .pytest_cache/r9diff/run.sh --against-batch 16-46 && bash .pytest_cache/r9diff/run.sh --against fb8fef72 && bash .pytest_cache/r9diff/run.sh --against 1c243203 && bash .pytest_cache/r9diff/run.sh --against 2f8c1656` | ✅ | ✅ green |
| 16-50-01 | 50 | 5 | диспозиция-ревью-16 | T-16-114 | CR-04 — `fixed` с существующими коммитами GREEN планов 16-46 и 16-49 и итогом меры на чужих корпусах; прочие строки — как на `1163ae39` | tracer (records) | `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-50-02 | 50 | 5 | диспозиция-ревью-16 | T-16-114, T-16-115 | пять находок повторного ревью раунда 8 — `fixed` с коммитами-предками `HEAD` (`feat(16-46)` … `feat(16-49)`); 51 прежняя строка байт в байт с `1163ae39`; `open: 0`, `total: 56`; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 9:** ни одной задачи без `<automated>`; у каждой из двенадцати задач первая
команда — модуль задачи, три модуля гейтов или quick run (≈1–70 с); у каждой задачи кода последняя — сверка «база ↔
HEAD» на своём и чужих корпусах (`bash .pytest_cache/r9diff/run.sh 16-4N`; у 16-48-03 — и `--against 2f8c1656`, у
16-49-03 — цепочка против базы партии, `fb8fef72`, `1c243203`, `2f8c1656` и за ней режим `--dictionary`), у задач записей —
`tests/test_planning`; каждый запуск сверки начинается проверкой манифеста чужих входов (`INPUTS_OK files=62`) и
самопроверкой инструмента на четырёх известных регрессиях (строки `SELFTEST` пар `c6953017`, `147f5e46`, `SELFTEST-COUNT`
пары `51d0d766` и `SELFTEST-CR04 e1d6587e -> a77263ad`) и строками `REPRODUCE` (суд инструмента совпадает с вердиктами
ревьюера); корпус по источникам с размерами, sha256 и правилом выборки записывается в сводку плана; всего команд
`<automated>` в партии 51, и у каждой есть парный `<fails_when>` (по планам: 10, 11, 13, 12, 5). Сквозные гейты
(`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`,
`test_logging_config.py`) названы в последней задаче каждого плана кода и в `<verification>` — на волну, как у прежних
партий.

**Столбец `File Exists` у партии раунда 9 везде ✅, и это замер, а не умолчание:** все двенадцать задач целятся в
модули, существующие на дереве `1163ae39` (`tests/phone_gate_grammar.py`, гейт писателя, гейт приватности,
`tests/test_phone_gates_parity.py`, записи `.planning/`); ни одного нового модуля в репозитории партия не заводит.
Инструмент сверки `.pytest_cache/r9diff/` (`corpus.py`, `judge.py`, `run.sh`, `external.py`, `cost_evidence.py`) и копия
чужих входов `.pytest_cache/r9-inputs/` (манифест — 62 файла) — gitignored и в репозиторий не коммитятся: их заводит по
договору `16-46-PLAN.md` первая задача плана 16-46 (планы 16-47…16-49 берут копию от оркестратора или собирают заново по
тому же договору), поэтому в столбце они не учитываются.

### Партия закрытия гэпа, раунд 10: 16-51…16-56 (после повторной верификации, `gap_closure: true`)

⚠️ **Волны ниже снова нумеруются от единицы** — это одиннадцатая партия фазы (первая 16-01…16-06, вторая 16-07…16-10,
третья 16-11…16-15, четвёртая 16-16…16-20, пятая 16-21…16-25, шестая 16-26…16-30, седьмая 16-31…16-35, восьмая
16-36…16-40, девятая 16-41…16-45, десятая 16-46…16-50), числа взяты из `wave` планов дословно. Партия исполняется ПОСЛЕ
приёмки десятой. Внутри партии параллельны две пары: волна 1 — 16-51 (защита писателя на исполнении: модели, писатель,
две суиты) и 16-52 (маска журнала на исполнении: конвейер журнала, нормализатор только читается) — файлы не пересекаются;
волна 3 — 16-54 (только модуль гейта приватности) и 16-55 (только модуль гейта писателя). Волна 2 — 16-53 (общий модуль,
оба гейта, паритет), волна 4 — 16-56 (записи).

⚠️ **Основание партии** — `16-VERIFICATION.md` (раунд 10, 2026-10-21T23:36:28Z, `gaps_found`, 127/132: гэп 1 — истина 131,
CR-05 — регрессия наличия `16573223` против `d31d86db`, и WR-35; гэп 2 — истина 28, CR-05, WR-32, WR-33; гэп 3 — истина 18,
WR-33, V10-1; гэп 4 — истина 114, V10-2 — регрессия `cc7fbce7` против `e61ab80d`; гэп 5 — истина 132, WR-34; advisory IN-22),
находки повторного ревью раунда 9 (`16-REVIEW.md`, `99c9f99c..c69774cf`) и решения владельца О-23 (а) «сузить обещание до
запрета динамики, добавить защиту на исполнении, раунд финальный» (шесть свойств) и О-24 (а) «маскировать только то, что
нормализатор фазы признаёт номером» (2026-10-22, записаны в `16-RESEARCH.md`, строки 769-785); диспозиции, согласование
прежних запретов, пересев реестра и эта карта — умолчание прохода. Опора — дерево `c9da79b2` (код как на `0f341ea2`): три
модуля гейтов — `960 passed` (622 / 306 / 32), quick run — `1364 passed`, `tests/test_planning` — `218 passed, 2 skipped`
(замер до записей партии). Строки карты ниже добавлены планированием и стоят `⬜ pending` до исполнения.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 16-51-01 | 51 | 1 | PHONE-02 | T-16-116, T-16-117 | подложенный сценарий дозаполнения, присваивающий номер атрибуту, отказывает `PhoneWriteOutsideWriter` до первого оператора, строка прежняя; писатель пишет под `writer_scope()`; аргумент конструктора колонки номера отказывает; разрешение закрыто после исключения; защита регистрируется пакетом моделей; правила CHECK — под разрешением, ограничение базы по-прежнему отвергает (О-23 (а), свойство 3; D-07, D-13) | tracer (runtime guard, ORM events, TDD) | `uv run pytest tests/test_application/test_phone_writer_runtime_guard.py tests/test_application/test_account_phone_writer.py tests/test_models/test_messenger_account_phone_check.py -q -p no:randomly` | ❌ → `tests/test_application/test_phone_writer_runtime_guard.py` и `app/models/phone_guard.py` создаёт сама задача; ✅ прочие | ✅ green |
| 16-51-02 | 51 | 1 | PHONE-02 | T-16-116, T-16-118 | `before_flush` и `do_orm_execute`: 15 путей записи колонок номера вне писателя отказывают (атрибут, сброс, ORM- и Core-оператор, групповой UPDATE, INSERT), 7 законных путей проходят; формы раунда 10 стороны писателя и пути репозитория исполнением отказывают (форма `set_committed_value` колонку не пишет); отрицание гонки под разрешением теряет ручной номер в позиции 2, без разрешения — отказ защиты (D-08) | runtime guard (ORM events, TDD, exec of forms) | `uv run pytest tests/test_application/test_phone_writer_runtime_guard.py tests/test_application/test_account_phone_race.py tests/test_application/test_account_phone_writer.py tests/test_models/test_messenger_account_phone_check.py -q -p no:randomly` | ✅ | ✅ green |
| 16-51-03 | 51 | 1 | PHONE-02 | T-16-116, T-16-117, T-16-118 | шапка модуля защиты (что отказывает, разрешение, граница), абзац «ЗАЩИТА НА ИСПОЛНЕНИИ» писателя, фраза модели; широкий прогон суит с `MessengerAccount` — ноль отказов защиты; живые деревья: писатель 105 файлов, 0, реестр — ровно писатель; приватность — 0, числа вызовов прежние | runtime guard (TDD, шапка), широкий прогон | решающая — `uv run pytest tests/test_application/test_phone_writer_runtime_guard.py -q -p no:randomly` (не меньше 35 passed, в их числе правило шапки `test_the_guard_module_names_what_it_refuses_and_its_boundary`); затем quick run фазы с модулем защиты (не меньше 1399 passed) и широкий прогон `uv run pytest $(grep -rl --include='test_*.py' "MessengerAccount" tests) -q -p no:randomly` | ✅ | ✅ green |
| 16-52-01 | 52 | 1 | PHONE-21 | T-16-119 | после `setup_logging(log_format="json")` номер в поле события structlog (целое и строка) — маска `+7 *** ***-**-67`, `group_id` `-1001234567890` виден, цифр номера в строке нет; модуль маски и конвейер — ноль находок обоих гейтов (О-23 (а), свойство 2; О-24 (а); D-10, D-11) | tracer (runtime mask, logging pipeline, TDD) | `uv run pytest tests/test_logging_config.py -q -p no:randomly` | ❌ → `app/services/log_masking.py` создаёт сама задача; ✅ прочие | ✅ green |
| 16-52-02 | 52 | 1 | PHONE-21 | T-16-119, T-16-120, T-16-121 | таблицы О-24 (а): 34 формы «маска», 28 «видно» (ID групп, JID групп, метки времени, UUID), цена; идемпотентность и «никогда не падает»; процессор по всем видам значений; фильтр на корне и на обработчиках uvicorn, типы аргументов сохраняются, отчёт `--- Logging error ---` без номера; исключения в обоих путях, `console`, JSON разбирается; уровень без `getattr` | runtime mask (unit + pipeline, TDD) | `uv run pytest tests/test_services/test_log_masking.py tests/test_logging_config.py -q -p no:randomly` | ❌ → `tests/test_services/test_log_masking.py` создаёт сама задача; ✅ прочие | ✅ green |
| 16-52-03 | 52 | 1 | PHONE-21 | T-16-119 | формы раунда 10 стороны приватности (CR-05 — четыре написания, WR-32, WR-33), исполненные через настоящий конвейер, печатают маску; шапка маски и абзац D-11 `mask_phone` правдивы; суиты, читающие журнал, зелёные; живые числа гейта приватности до и после — в сводку для 16-54 | runtime mask (TDD, exec of forms, шапка) | `uv run pytest tests/test_services/test_log_masking.py tests/test_logging_config.py -q -p no:randomly` и `uv run pytest tests/test_admin.py tests/test_messengers tests/test_pages/test_admin_panel.py tests/test_pages/test_blocked_user.py tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_impersonation.py tests/test_main.py -q -p no:randomly` | ✅ | ✅ green |
| 16-53-01 | 53 | 2 | PHONE-02, PHONE-21 | T-16-122 | подложенный скрипт с `getattr(sys.modules[__name__], "lg").info(…)` краснит правило живых деревьев канала ОБОИХ гейтов одной функцией общего модуля; живые деревья — ноль находок канала; `dynamic_construct_findings` — в `REQUIRED_SHARED_NAMES`; прежние строки таблиц (173 / 61 / 268 / 107) — на месте (О-23 (а), свойство 1) | tracer (gate, AST, TDD, shared ban channel) | `uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-53-02 | 53 | 2 | PHONE-02, PHONE-21 | T-16-122, T-16-123 | девять видов канала у обоих гейтов, ≥ 50 строк `DYNAMIC_CONSTRUCT_CASES` (13 написаний CR-05, WR-32, WR-33, V10-1, V10-2), ≥ 20 двойников молчат; реестр — шесть измеренных исключений с причиной, потолок 6, правило реестра с контролем седьмой записью | gate (AST, TDD, parity, registry) | `uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-53-03 | 53 | 2 | PHONE-02, PHONE-21 | T-16-122 | комментарий-шапка канала в общем модуле (обещание, перечень, исключения, граница); докстринг паритета без утверждения шире словаря (IN-22); сквозные гейты и записи | gate (TDD, docstring) | `uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-54-01 | 54 | 3 | PHONE-21 | T-16-124 | подложенная служба, читающая журнал через атрибут-объект модуля, красна каналом одной находкой; 18 форм раунда 10 (CR-05 ×14, WR-32 ×2, WR-33 ×2) — строки канала; ответ прежнего предиката — в сводку (О-23 (а), свойства 1, 4) | tracer (gate, AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py -q -p no:randomly` | ✅ | ✅ green |
| 16-54-02 | 54 | 3 | PHONE-21 | T-16-125 | перенастройка журнала (`structlog.configure`, `basicConfig`, `dictConfig`, `addHandler` / `removeFilter` / `setFormatter`, присваивание `handlers` / `propagate`) вне `app/logging_config.py` краснит гейт; контроль семи форм | gate (AST, TDD) | `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k "logging_reconfiguration"` | ✅ | ✅ green |
| 16-54-03 | 54 | 3 | PHONE-21 | T-16-124, T-16-125 | шапка гейта приватности: раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ», оговорки прежних обещаний, летописи CR-05 / WR-32 / WR-33, D-11, живые числа, согласование прежних запретов; предикаты распознавания и JS-половина — тела совпадают с `c9da79b2` | gate (TDD, шапка) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-55-01 | 55 | 3 | PHONE-02 | T-16-126 | подложенный скрипт с `f = getattr` в функции и `self.f = setattr` в классе красен каналом двумя находками; 10 форм раунда 10 (WR-33 ×7, V10-1 ×2, V10-2) — строки канала (О-23 (а), свойства 1, 4; D-13) | tracer (gate, AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-55-02 | 55 | 3 | PHONE-02 | T-16-127, T-16-128 | вход в разрешение писателя и ссылка на модуль защиты вне трёх законных мест и `event.remove` где угодно краснят гейт (контроль шести форм); цена WR-34 — 15 измеренных форм по механизму (`NAMED_COST_MECHANISM_CASES`: 12 «двоек», 3 «единицы») | gate (AST, TDD) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly -k "guard_bypass or entered_only_by_the_writer or named_cost"` | ✅ | ✅ green |
| 16-55-03 | 55 | 3 | PHONE-02 | T-16-126, T-16-127, T-16-128 | шапка гейта писателя: раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ», оговорки прежних обещаний и пунктов границы (1), (2), (5), абзац цены по механизму, летописи WR-33 / V10-1 / V10-2, согласование прежних запретов, живое дерево 106 файлов; предикаты распознавания — тела совпадают с `c9da79b2`, строки 268 / 107 на месте | gate (TDD, шапка) | `uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py -q -p no:randomly` | ✅ | ✅ green |
| 16-56-01 | 56 | 4 | диспозиция-ревью-16 | T-16-129 | CR-05 — `fixed` с существующими коммитами GREEN планов 16-52, 16-53, 16-54, регрессия «16573223» названа; прочие строки — как на `0f341ea2` | tracer (records) | решающая — первая команда `<automated>` задачи 1 `16-56-PLAN.md` (`uv run python -c "…"` над `16-REVIEW-DISPOSITION.md` и `git show 0f341ea2:…`: строка CR-05 — `fixed`, называет `16-53` и хеш в обратных кавычках; прочие строки равны `0f341ea2`; frontmatter `open: 5`; печатает `OK`); затем `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |
| 16-56-02 | 56 | 4 | диспозиция-ревью-16 | T-16-129, T-16-130, T-16-131 | пять находок — `fixed` с коммитами-предками `HEAD` (`feat(16-51)` … `feat(16-55)`), WR-35 — `skipped` с цитатой О-23 (а), свойство 4; 56 прежних строк байт в байт с `0f341ea2`; `open: 0`, `total: 62`; карта истин 18 / 28 / 114 / 131 / 132 и согласование 48 прежних запретов — в сводке, сверены с реестром; реестр пересеян, `--check` с кодом 0 | records | `uv run python scripts/prohibitions_census.py --check` и `uv run pytest tests/test_planning -q -p no:randomly` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Непрерывность выборки партии раунда 10:** ни одной задачи без `<automated>`; у каждой из семнадцати задач первая
команда — модуль задачи, три модуля гейтов или широкий прогон (≈1–90 с; широкий прогон суит с `MessengerAccount` у 16-51-03
— дольше 60 с, это прогон волны, а не задачи); у задач записей — `tests/test_planning`; всего команд `<automated>` в
партии 55, и у каждой есть парный `<fails_when>` (по планам: 11, 10, 9, 10, 10, 5). Сверка «база ↔ HEAD» инструментом
`r9diff` в этой партии не обязательна (решение владельца О-23 (а), свойство 4): правка сужает обещание гейтов, а не
расширяет распознавание; прежние строки таблиц и тела предикатов распознавания сверяются с `c9da79b2` командами задач
16-53-01, 16-54-03 и 16-55-03. Сквозные гейты (`test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`,
`test_declared_invariants.py`, `test_logging_config.py`) и суиты, читающие журнал или создающие `MessengerAccount`, названы
в последней задаче каждого плана кода и в `<verification>` — на волну, как у прежних партий.

**Столбец `File Exists` у партии раунда 10 — замер:** четыре новых модуля в репозитории создают сами задачи партии —
`app/models/phone_guard.py` и `tests/test_application/test_phone_writer_runtime_guard.py` (16-51-01),
`app/services/log_masking.py` (16-52-01) и `tests/test_services/test_log_masking.py` (16-52-02); прочие задачи целятся в модули,
существующие на дереве `c9da79b2` (`app/models/__init__.py`, `app/models/messenger_account.py`,
`app/application/accounts/phone.py`, `app/logging_config.py`, `app/services/phone.py`, `tests/test_logging_config.py`,
`tests/test_models/test_messenger_account_phone_check.py`, `tests/test_application/test_account_phone_race.py`,
`tests/phone_gate_grammar.py`, оба модуля гейтов, `tests/test_phone_gates_parity.py`, записи `.planning/`).

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

### Волна 0 партии раунда 7 (16-36…16-40): пуста, и это замер

Партия **не заводит ни одного нового модуля в репозитории** — все четырнадцать задач целятся в файлы,
существующие на дереве `65e5c692` (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`,
`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, записи `.planning/`). Инструмент сверки
«база ↔ HEAD» живёт в gitignored `.pytest_cache/r7diff/` и предпосылкой чужой задачи не служит: его собирает сама
первая задача каждого плана кода. Требований волны 0 у партии нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): гейт писателя —
с 555 до не менее чем 565 (16-36-01: трасер, 9 строк), 571 (16-36-02: 4 + 2 строки) и 573 (16-38-02: 2 строки-закрепки);
гейт приватности — с 222 до не менее чем 225 (16-37-01: трасер, 2 строки), 233 (16-37-02: 7 + 1 строк), 242
(16-38-01: трасер, 7 + 1 строк) и 248 (16-38-02: 6 строк); правило-паритет — с 15 до 16 (16-38-02: сторож таблиц
носителей против stdlib) и 17 (16-39-02: правило словаря седьмого круга); три модуля гейтов — с 792 до не менее чем
838; quick run фазы — с 1196 до не менее чем 1242; плюс строки самопроверок и циклов сверки исполнителей, если они
найдут формы или регрессии. Словарь общего модуля: `REFERENCE_CARRIERS` 11 → 20 (16-39), поле
`ReferenceCarrier.last` — новое; матрицы обоих гейтов и правило-паритет растут с 720 до 1 260 ячеек на гейт;
`ELEMENTWISE_CARRIERS` 1 → 4, `ROW_CARRIERS` — новая таблица из 2 (16-38); `REQUIRED_SHARED_NAMES` 6 → 11 и
`GRAMMAR_FUNCTIONS` 24 → 30 (16-37: `named_wrappers`, `is_carrier_wrapper`, `wrapper_applications` — каждое имя с
подчёркиванием и без), `GRAMMAR_TABLES` 7 → 9 (16-38). Строки, которые партия СОЗНАТЕЛЬНО меняет (урок «тесты фазы закрепляют старые
дефекты»): правило строк `NEGATIVE_CONTROLS` гейта приватности получает второе утверждение — находки одного места не
повторяются (16-37-01; до плана форма `w = partial(to_thread, logger.info, "x %s", account.phone); await w()` давала
две — регрессия счёта `5e57325d`, найденная замером планирования); фраза шапки гейта писателя «судится как
применённая на месте вызова `w(…)`» становится фразой «судится везде, где её имя прочитано» (16-36-03); фразы шапки
гейта приватности «своих копий нет» становятся правдой после перевода (16-37-03), комментарий ввоза перестаёт
называть выведенную таблицу ключа ссылки (IN-16), строки `REFERENCE_CARRIERS` плана 16-34 названы в прошедшем
времени (IN-17); фраза шапки гейта приватности «У `map` ссылке подаются элементы литеральной итерируемой…»
переписывается под суд итерируемой целиком (16-38-03); ложная фраза докстринга `reference_arguments` о «лишних
прочтениях» гейта приватности заменяется правдой (16-38-02); докстринг `carrier_wrapper_bindings` и комментарий
`CARRIER_SEMANTICS` правила-паритета перестают говорить о копии гейта приватности (16-37-01). Строк, которые партия
переносит из таблицы в таблицу, нет: прототипы планирования прогнаны по всем прежним строкам — 228 / 96 гейта
писателя и 117 / 49 гейта приватности дают прежний ответ (три модуля — `792 passed` на прототипе всей партии). Числа
распознанных вызовов журнала в живом правиле гейта приватности НЕ меняются — `app` 225, `scripts` 68,
`max_worker` 93, находок 0 (замер прототипа; изменение было бы признаком ложного распознавания, разбирается по
файлам); живое дерево гейта писателя — ноль судимых находок в 104 файлах, в модуле-писателе — 6 сырых. Перепись
запретов получает строки планов 16-36…16-40 штатным засевом (оркестратор при коммите планов, повтор — 16-40-02).

### Волна 0 партии раунда 8 (16-41…16-45): пуста, и это замер

Партия **не заводит ни одного нового модуля в репозитории** — все двенадцать задач целятся в файлы, существующие на
дереве `8aabdb38` (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`,
`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, записи `.planning/`). Инструмент сверки
«база ↔ HEAD» с осью счёта живёт в gitignored `.pytest_cache/r8diff/` и предпосылкой чужой задачи не служит: его
собирает сама первая задача плана 16-41, а планы 16-42…16-44 — по тому же договору. Требований волны 0 у партии нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): гейт приватности — с
254 до не менее чем 260 (16-41-01: трасер, 4 строки WR-27, правило-контроль счёта), 264 (16-43-01: трасер, 2 + 1 строки),
265 (16-43-02: строка IN-20) и 266 (16-44-01: параметр матрицы формы `getattr-read`); гейт писателя — с 576 до не менее
чем 581 (16-42-01: трасер, 2 + 2 строки) и 582 (16-44-01: параметр матрицы); правило-паритет — с 17 до 18 (16-43-02:
правило-закрепка IN-20), 20 (16-44-01: параметр формы и правило словаря восьмого круга) и 22 (16-44-03: правила докстринга
паритета и летописей словаря); три модуля гейтов — с 847 до не менее чем 870; quick run фазы — с 1251 до не менее чем
1274; плюс строки самопроверок и циклов сверки исполнителей, если они найдут формы или регрессии. Словарь общего
модуля: `BINDING_FORMS` 12 → 13 (16-44), значений опознания 5 → 6 у каждого гейта (16-44) — матрицы обоих гейтов и
правило-паритет растут с 1 260 до 1 638 ячеек на гейт; `REQUIRED_SHARED_NAMES` 11 → 12 и `GRAMMAR_FUNCTIONS` 30 → 32
(16-43: `reading_name` с подчёркиванием и без). Строки, которые партия СОЗНАТЕЛЬНО меняет (урок «тесты фазы
закрепляют старые дефекты»): правило строк `NEGATIVE_CONTROLS` гейта приватности перестаёт сверять уникальность
выхода той же дедупликации — оно закрепляло регрессию счёта WR-27 (`51d0d766`) — и считает места по
`NEGATIVE_CONTROL_PLACES` (16-41-01); правило-матрица гейта приватности требует ровно одну находку на ячейку, а не
«непусто» (16-41-01; замер — все 1 260 ячеек дают одну); `_judge_arguments` возвращает место со столбцом (16-41-01);
правило-матрица писателя и `_writer_finds` паритета требуют в предмете API значения из `API_IDENTIFICATION_CALLS`, а не
одного `set_committed_value` (16-44-02); `_reference_name` гейта писателя становится делегатом общего `reading_name`
(16-42-01); довод докстринга `ReferenceCarrier.last` о `partial` исправляется (16-43-02); фразы «краснят обе матрицы» о
строках словаря седьмого круга разводятся по матрицам (16-44-03). Строк, которые партия переносит из таблицы в
таблицу, нет: прототипы планирования прогнаны по всем прежним строкам — 246 / 98 гейта писателя и 145 / 51 гейта
приватности дают прежний ответ (у 145 строк — 136 по одной находке и 9 по две, и на HEAD, и на прототипе); три модуля
на прототипе всей партии — `844 passed` и шесть правил живого дерева копии без `app/`. Числа распознанных вызовов
журнала в живом правиле гейта приватности НЕ меняются — `app` 225, `scripts` 68, `max_worker` 93, находок 0 (замер
прототипа; изменение было бы признаком ложного распознавания, разбирается по файлам); живое дерево гейта писателя —
ноль судимых находок в 104 файлах, в модуле-писателе — 6 сырых. Перепись запретов получает строки планов 16-41…16-45
штатным засевом (оркестратор при коммите планов, повтор — 16-45-02).

### Волна 0 партии раунда 9 (16-46…16-50): пуста, и это замер

Партия **не заводит ни одного нового модуля в репозитории** — все двенадцать задач целятся в файлы, существующие на
дереве `1163ae39` (`tests/phone_gate_grammar.py`, `tests/test_application/test_phone_single_writer_gate.py`,
`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, записи `.planning/`). Инструмент сверки «база ↔ HEAD»
с чужими корпусами живёт в gitignored `.pytest_cache/r9diff/`, а копия чужих входов — в `.pytest_cache/r9-inputs/`
(источник — `/source/broadcaster/.pytest_cache/r9-inputs/`, `MANIFEST.sha256` на 62 файла; расхождение sha256 — остановка);
предпосылкой чужой задачи они не служат: их собирает сама первая задача плана 16-46, а планы 16-47…16-49 — по тому же
договору. Требований волны 0 у партии нет.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): гейт приватности — с
271 до не менее чем 283 (16-46-01: трасер, 9 + 2 строки) и 298 (16-47-01: трасер, 8 + 6 строк), далее 306 (16-49-01: 8
параметров матрицы новых форм); гейт писателя — с 598 до не менее чем 604 (16-48-01: трасер, 4 строки, правило-контроль
счёта мест), 609 (16-48-02: 4 + 1 строки) и 617 (16-49-01: 8 параметров матрицы); правило-паритет — с 22 до 31 (16-49-01: 8
параметров правила на ячейках и правило словаря девятого круга) и 32 (16-49-03: правило летописей меры); три модуля гейтов —
с 891 до не менее чем 955; quick run фазы — с 1295 до не менее чем 1359; плюс строки самопроверок и циклов сверки
исполнителей, если они найдут формы или регрессии. Словарь общего модуля: `BINDING_FORMS` 13 → 21, `REFERENCE_CARRIERS`
20 → 22, значений опознания 6 → 7 у каждого гейта, поля `IdentificationValue.rival` и `.method` — новые; матрицы обоих
гейтов и правило-паритет растут с 1 638 до 3 381 ячейки на гейт. Строки, которые партия СОЗНАТЕЛЬНО меняет (урок «тесты
фазы закрепляют старые дефекты»): трасер 16-42 `test_a_planted_backfill_with_a_methodcaller_read_by_a_getattr_string_reddens_the_gate`
утверждал место `scripts/backfill_descriptor.py:8` (строку связывания) — 16-48-01 меняет его на `:11` (узел получателя,
свойство 5 О-20); правило `test_a_literal_write_form_is_a_write` перестаёт требовать «ровно одну находку» и считает места по
`LITERAL_FORM_PLACES` (16-48-01); ожидание D2 писателя у `methodcaller-receiver` в корпусе сверки — 2 вместо `exact 1`
16-44 (16-46-01, договор r9diff); фраза докстринга `_referenced_calls` «вызов, имя которого само судимо, ссылкой не
разбирается» переписывается (16-48-02); летописи словаря восьмого круга обеих шапок теряют утверждение-итог, опровергнутое
замером (16-49-03, IN-21); имя модуля, связанное с вызываемым журнала, перестаёт читаться членом любого объекта
(16-47-01 — откат механизма `a77263ad` в пользу объекта модуля); цена атрибута, связанного с вызываемым журнала, НЕ
снимается, а называется (О-22 (а)). Строк, которые партия переносит из таблицы в таблицу, нет: прототипы планирования
прогнаны по всем прежним строкам — 259 / 105 гейта писателя и 156 / 53 гейта приватности дают прежний ответ (три модуля
на прототипе всей партии — `890 passed` и одна запланированная смена трасера 16-42). Числа распознанных вызовов журнала в
живом правиле гейта приватности НЕ меняются — `app` 225, `scripts` 68, `max_worker` 93, находок 0 (замер прототипа;
изменение было бы признаком ложного распознавания, разбирается по файлам); живое дерево гейта писателя — ноль судимых
находок в 104 файлах, в модуле-писателе — 6 сырых. Чужие корпуса (29 941 ячейка) на прототипе всей партии расходятся с
ожиданием только в двух названных ценах — `COST-KW` 281 (свойство 8 О-20) и `COST-ATTR` 122 (О-22 (а)); на `1163ae39` —
2 754 неверные ячейки. Перепись запретов получает строки планов 16-46…16-50 штатным засевом (оркестратор после проверки
планов, повтор — 16-50-02).

### Волна 0 партии раунда 10 (16-51…16-56): четыре новых модуля, все заводят сами задачи партии — это замер

Партия заводит два продуктовых модуля (`app/models/phone_guard.py` — защита писателя на исполнении, свойство 3 О-23 (а);
`app/services/log_masking.py` — маска журнала на исполнении, свойство 2 и О-24 (а)) и два тестовых
(`tests/test_application/test_phone_writer_runtime_guard.py`, `tests/test_services/test_log_masking.py`). Каждый создаёт
RED-коммит задачи, которой он нужен (16-51-01, 16-52-01, 16-52-02), — предпосылкой чужой задачи ни один не служит, поэтому
отдельных требований волны 0 у партии нет. Замеры, на которых стоят планы (2026-10-22, HEAD `c9da79b2`; прототипы — в
скретчпаде сессии планирования): события ORM на SQLAlchemy 2.0.46 / greenlet 3.3.1 (переменная контекста видна слушателям
`before_flush` и `do_orm_execute` внутри greenlet; `set_committed_value` и `bulk_update_mappings` событий не дают); прототип
защиты на суитах фазы — `8 failed, 442 passed`, ровно семь правил CHECK и отрицание гонки, и на 55 суитах с
`MessengerAccount` — ноль отказов на законных путях; прототип маски — 25 из 25 «маска», 28 из 28 «видно» О-24 (а); перепись
запрещённых конструкций канала по `app/`, `scripts/`, `max_worker/` — семь мест вычисленного имени атрибута (одно снимает
16-52, шесть — исключения 16-53), прочие восемь видов — ноль.

Правила и числа, которые партия ДВИГАЕТ вместе с предметом (их изменение ожидаемо и запланировано): гейт писателя — с 622 до
не менее чем 625 (16-53-01: правило живых деревьев канала и два параметра подложенного дерева), 636 (16-55-01: трасер и 10
строк), 658 (16-55-02: правило обхода, шесть параметров контроля, 15 строк цены) и 659 (16-55-03: правило шапки); гейт
приватности — с 306 до не менее чем 310 (16-53-01), 329 (16-54-01: трасер и 18 строк), 337 (16-54-02: правило и семь
параметров контроля) и 338 (16-54-03); правило-паритет — с 32 до не менее чем 33 (16-53-01: трасер), 105 (16-53-02: ≥ 50
строк видов, ≥ 20 двойников, правило реестра и контроль) и 106 (16-53-03); новые модули — правила защиты писателя ≥ 35,
маски ≥ 73 (72 и правило шапки) и конвейера журнала 3 → ≥ 17; quick run фазы с модулем защиты — с 1364 до не менее чем
1399 (16-51-03).
Строки, которые партия СОЗНАТЕЛЬНО меняет (урок «тесты фазы закрепляют старые дефекты»): правила CHECK
`test_messenger_account_phone_check.py` строят состояния под разрешением защиты (утверждения прежние);
`read_check_write` теста гонки получает параметр `scope` и исполняет запись под разрешением (утверждения прежние);
`setup_logging` берёт уровень `logging.getLevelNamesMapping()` вместо `getattr(logging, …)`; докстринг `mask_phone` теряет
фразу «В ЖУРНАЛЫ НОМЕР НЕ ПОПАДАЕТ ДАЖЕ МАСКОЙ» (летописью); шапки обоих гейтов получают оговорки к обещаниям полноты
написаний («каждое толкование узла», «поданный ЛЮБОМУ носителю», «Каждое связывание имени судится», «Судится каждое
толкование вызова») и раздел запрета; абзац цены гейта писателя переписан по механизму (фраза о `enqueue` — летописью);
абзац словаря девятого круга докстринга паритета — правдой IN-22. Строк, которые партия переносит из таблицы в таблицу, нет;
предикаты распознавания прежних раундов не правятся (сверка тел с `c9da79b2` — 16-54-03, 16-55-03). Числа распознанных
вызовов журнала в живом правиле гейта приватности могут сдвинуться только в `app/logging_config.py` и
`app/services/log_masking.py` (прототип: 6 → 5 и +1), находок 0; живое дерево гейта писателя — 104 → 106 файлов (два
модуля партии), ноль судимых находок, в модуле-писателе 6 сырых. Перепись запретов получает строки планов 16-51…16-56
штатным засевом (планирование, повтор — 16-56-02).

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

**Партия закрытия гэпа, раунд 6 (16-31…16-35): validated 2026-10-16** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 14 строк партии зелёные на дереве `3a192b53` — `tests/test_application/test_phone_single_writer_gate.py` 555 passed, `tests/test_phone_privacy_gate.py` 222, `tests/test_phone_gates_parity.py` 15 (три модуля вместе — 792), `tests/test_planning` 218 passed / 2 skipped, `scripts/prohibitions_census.py --check` код 0 (837 строк); полная суита на `e5a4492c` (последнее дерево с кодом партии) — 5181 passed, 2 skipped. До валидации — «pending» (строки добавлены планированием 2026-10-16, шестой
прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10
(10 задач), к партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач) и 5 (13 задач). Партия раунда 6
добавляет четырнадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (41 из 41), трёх подряд
задач без машинной проверки нет, новых модулей нет (подраздел волны 0 выше). Что планирование изменило в этом
файле и почему: дописаны подраздел карты партии раунда 6, подраздел её волны 0 и этот абзац; frontmatter
(`status: validated`, `nyquist_compliant: true`), прежние строки, прежние подписи и разделы аудита НЕ тронуты —
шаг 5.5 `/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с
четырнадцатью новыми строками (всего строк станет 84) делает `/gsd-validate-phase 16` после исполнения
партии, а не планировщик.

**Партия закрытия гэпа, раунд 7 (16-36…16-40): validated 2026-10-19** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 14 строк партии зелёные на дереве `969fcd61` — `tests/test_application/test_phone_single_writer_gate.py` 576 passed, `tests/test_phone_privacy_gate.py` 254, `tests/test_phone_gates_parity.py` 17 (три модуля вместе — 847; нижние границы карты 573 / 248 / 17), quick run фазы — 1251 passed, живые деревья приватности 225 / 68 / 93, находок 0, `tests/test_planning` 218 passed / 2 skipped, `scripts/prohibitions_census.py --check` код 0 (856 строк); полная суита на `fdadd46c` (последнее дерево с кодом партии) — 5236 passed, 2 skipped. Команды сверки «база ↔ HEAD» (`bash .pytest_cache/r7diff/run.sh 16-3N`) прогоняли исполнители в своих worktree — инструмент gitignored; их строки `SELFTEST` / `DIFF` / `BASE` / `OPEN_REGRESSIONS=0` (у 16-39 — и `AGAINST 1c243203` и `AGAINST 2f8c1656`, регрессий 0) записаны дословно в `16-36…16-39-SUMMARY.md`. До валидации — «pending» (строки добавлены планированием 2026-10-18, седьмой
прогон `/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10
(10 задач), к партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач), 5 (13 задач) и 6 (14 задач). Партия
раунда 7 добавляет четырнадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (51 из 51), трёх подряд
задач без машинной проверки нет, новых модулей в репозитории нет (подраздел волны 0 выше); новая мера партии —
сверка «база ↔ HEAD» каждого GREEN против родителя — стоит последней командой каждой задачи кода. Что
планирование изменило в этом файле и почему: дописаны подраздел карты партии раунда 7, подраздел её волны 0 и этот
абзац; frontmatter (`status: validated`, `nyquist_compliant: true`), прежние строки, прежние подписи и разделы аудита
НЕ тронуты — шаг 5.5 `/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с
четырнадцатью новыми строками (всего строк станет 98) делает `/gsd-validate-phase 16` после исполнения партии, а не
планировщик.

**Партия закрытия гэпа, раунд 8 (16-41…16-45): validated 2026-10-20** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 12 строк партии зелёные на дереве `f2a0a687` — `tests/test_application/test_phone_single_writer_gate.py` 598 passed, `tests/test_phone_privacy_gate.py` 271, `tests/test_phone_gates_parity.py` 22 (три модуля вместе — 891), quick run фазы — 1295 passed, живые деревья приватности 225 / 68 / 93, находок 0, `tests/test_planning` 218 passed / 2 skipped, `scripts/prohibitions_census.py --check` код 0 (875 строк); полная суита на `e9449db5` (последнее слияние партии; код — как на `0cf35f39`) — 5280 passed, 2 skipped. Команды сверки «база ↔ HEAD» по обеим осям (`bash .pytest_cache/r8diff/run.sh 16-4N`, у 16-44 — и `--against-batch 16-41`, `--against 1c243203`, `--against 2f8c1656`) прогоняли исполнители в своих worktree — инструмент gitignored; их строки `SELFTEST` / `SELFTEST-COUNT` / `DIFF` / `BASE` / `AGAINST` / `HEAD_WRONG=0` / `OPEN_REGRESSIONS=0` записаны дословно в `16-41…16-44-SUMMARY.md`. Оговорка: зелёная строка карты значит, что её команда проходит, а не что гейт верен на всех формах — повторное ревью раунда 8 (`16-REVIEW.md`, `99c9f99c`) нашло своим корпусом регрессию наличия CR-04 (коммит «a77263ad», цикл 1 16-43), которую корпус инструмента сверки не содержал; её судьба — в вердикте верификации, не в этой карте. До валидации — «pending» (строки добавлены планированием 2026-10-19, восьмой прогон
`/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10 (10 задач), к
партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач), 5 (13 задач), 6 (14 задач) и 7 (14 задач). Партия раунда 8
добавляет двенадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (50 из 50), трёх подряд задач без
машинной проверки нет, новых модулей в репозитории нет (подраздел волны 0 выше); мера партии — сверка «база ↔ HEAD»
каждого GREEN против родителя по ОБЕИМ осям, наличию и числу находок, с самопроверкой инструмента на известной
регрессии счёта `51d0d766` — стоит последней командой каждой задачи кода. Что планирование изменило в этом файле и
почему: дописаны подраздел карты партии раунда 8, подраздел её волны 0 и этот абзац; frontmatter (`status: validated`,
`nyquist_compliant: true`), прежние строки, прежние подписи и разделы аудита НЕ тронуты — шаг 5.5 `/gsd-plan-phase`
записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с двенадцатью новыми строками (всего строк станет
110) делает `/gsd-validate-phase 16` после исполнения партии, а не планировщик.

**Партия закрытия гэпа, раунд 9 (16-46…16-50): validated 2026-10-21** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 12 строк партии зелёные на дереве `0f341ea2` (код — как на `c69774cf`) — `tests/test_application/test_phone_single_writer_gate.py` 622 passed, `tests/test_phone_privacy_gate.py` 306, `tests/test_phone_gates_parity.py` 32 (три модуля вместе — 960), quick run фазы — 1364 passed, живые деревья приватности 225 / 68 / 93, находок 0, `cost_evidence.py` код 0 (14 строк `EVIDENCE`, `kw: writes=1 … findings=2`), `tests/test_planning` 218 passed / 2 skipped, `scripts/prohibitions_census.py --check` код 0 (894 строки); сверка «база ↔ HEAD» прогнана оркестратором на HEAD из главной копии инструмента (`.pytest_cache/r9diff/`, перенесён из worktree): `run.sh 16-46` / `16-47` / `16-48` / `16-49` — код 0, `cells=156352 regressions=0 count_regressions=0 HEAD_WRONG=0 OPEN_REGRESSIONS=0` против баз `d31d86db`, `35106de1`, `5c7377cc`, `c51755fc`; цепочку `--against-batch 16-46`, `--against fb8fef72` / `1c243203` / `2f8c1656` и `--dictionary` (строки 16-48-03, 16-49-03) прогоняли исполнители — их строки дословно в `16-48-SUMMARY.md` и `16-49-SUMMARY.md`; полная суита на `c69774cf` (последнее слияние партии) — 5349 passed, 2 skipped. Оговорка: зелёная строка карты значит, что её команда проходит, а не что гейт верен на всех формах — повторное ревью раунда 9 (`16-REVIEW.md`, `150a076d`) нашло своим корпусом регрессию наличия CR-05 (правка WR-29, `16573223`: объект модуля читается только как `sys.modules[__name__]` или прямо связанное с ним имя; `self.me = sys.modules[__name__]; self.me.out(…)` и `import sys as _s; _s.modules[__name__].out(…)` ловились на `d31d86db` и не ловятся на HEAD — воспроизведено оркестратором), которой нет в корпусе r9diff, а значит и в командах этой карты; её судьба — в вердикте верификации, не в этой карте. До валидации — «pending» (строки добавлены планированием 2026-10-21, девятый прогон
`/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10 (10 задач), к
партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач), 5 (13 задач), 6 (14 задач), 7 (14 задач) и 8 (12 задач). Партия
раунда 9 добавляет двенадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (51 из 51), трёх подряд задач без
машинной проверки нет, новых модулей в репозитории нет (подраздел волны 0 выше); мера партии — сверка «база ↔ HEAD»
каждого GREEN против родителя по обеим осям, где чужие корпуса ревьюера и верификатора — обязательный вход целиком
(решение владельца О-21 (а)), с самопроверкой инструмента на четырёх известных регрессиях, в том числе `a77263ad`, —
стоит последней командой каждой задачи кода. Оговорка прежней подписи остаётся в силе: зелёная строка карты значит, что её
команда проходит, а не что гейт верен на всех формах. Что планирование изменило в этом файле и почему: дописаны подраздел
карты партии раунда 9, подраздел её волны 0 и этот абзац; frontmatter (`status: validated`, `nyquist_compliant: true`),
прежние строки, прежние подписи и разделы аудита НЕ тронуты — шаг 5.5 `/gsd-plan-phase` записал бы пустой шаблон поверх
заполненной карты, а переоценку фазы с двенадцатью новыми строками (всего строк станет 122) делает `/gsd-validate-phase
16` после исполнения партии, а не планировщик.

**Партия закрытия гэпа, раунд 10 (16-51…16-56): validated 2026-10-23** (`/gsd-validate-phase 16` из `/gsd-execute-phase 16 --gaps-only`): все 17 строк партии зелёные на дереве `17fd959e` (код — как на `c735d00f`, последнее слияние кода партии): полные суиты после каждой волны — `just test` 5472 / 5586 / 5657 passed, 2 skipped (на `4e5b1f05`, `d97e4aaa`, `c735d00f`; волна 4 — только записи); три модуля гейтов — 1110 passed на итоге 16-55; quick run фазы с модулями партии — 1640 passed; живые деревья приватности 227 / 68 / 93, находок 0; писатель `OK 6 106 offences 0`; канал запрета — 0 находок вне реестра шести исключений; широкий прогон суит с `MessengerAccount` — 2448 passed (16-51); суиты, читающие журнал, — 434 passed с модулями маски (16-52); `tests/test_planning` 218 passed / 2 skipped; `scripts/prohibitions_census.py --check` код 0 (913 строк); гейт TDD — 44 плана, 0 нарушений. Сверка «база ↔ HEAD» по О-23 (а), свойство 4, не требовалась; прежние строки таблиц сверены с `c9da79b2` командами 16-53-01, 16-54-03, 16-55-03 после каждого GREEN — без изменений. Оговорка: зелёная строка карты значит, что её команда проходит, а не что защита полна — повторное ревью раунда 10 (`16-REVIEW.md`, `0125cff6`) нашло своим корпусом CR-06 (маска не стоит на корне журнала воркеров Celery: `setup_logging` на `worker_init` перекрывается собственной настройкой журнала Celery), CR-07 (сверхлинейная цена маски на длинной строке с разбивкой — воспроизведено оркестратором: 1,2 тыс. → 2,4 тыс. символов дают 0,06 → 0,26 с) и CR-08 (`bulk_update_mappings` / `bulk_insert_mappings` со строками из переменной проходят все три рубежа писателя), а также WR-36…WR-39, IN-23…IN-25; это дефекты кода, а не гэпы покрытия карты; их судьба — в вердикте верификации. До валидации — «pending» (строки добавлены планированием 2026-10-22, десятый прогон
`/gsd-plan-phase 16 --gaps`). Подписи выше относятся к первой партии (14 задач), к партии 16-07…16-10 (10 задач), к
партиям раундов 2 (11 задач), 3 (12 задач), 4 (10 задач), 5 (13 задач), 6 (14 задач), 7 (14 задач), 8 (12 задач) и 9 (12
задач). Партия раунда 10 добавляет семнадцать задач: у каждой есть `<automated>` с парным `<fails_when>` (55 из 55), трёх
подряд задач без машинной проверки нет; новых модулей четыре — два продуктовых и два тестовых, все заводят сами задачи
партии (подраздел волны 0 выше). Предмет партии сменило решение владельца О-23 (а): гейты обещают «в коде нет конструкции,
которую гейт не умеет судить» (запрет динамики — общий канал обоих гейтов), а защиту дают и на исполнении — отказ записи
номера вне писателя и маска номера в журнале (О-24 (а)); сверка «база ↔ HEAD» в этой партии не обязательна. Оговорка
прежней подписи остаётся в силе: зелёная строка карты значит, что её команда проходит. Что планирование изменило в этом
файле и почему: дописаны подраздел карты партии раунда 10, подраздел её волны 0 и этот абзац; frontmatter (`status:
validated`, `nyquist_compliant: true`), прежние строки, прежние подписи и разделы аудита НЕ тронуты — шаг 5.5
`/gsd-plan-phase` записал бы пустой шаблон поверх заполненной карты, а переоценку фазы с семнадцатью новыми строками
(всего строк станет 139) делает `/gsd-validate-phase 16` после исполнения партии, а не планировщик.

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

## Validation Audit 2026-10-16 (партия закрытия гэпа, раунд 6: 16-31…16-35)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3–5: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает (`appended: false`, замер этого прогона). Предмет аудита — 14 строк партии раунда 6; все зелёные на `3a192b53`, гэпов нет, аудитор не вызывался.

## Validation Audit 2026-10-19 (партия закрытия гэпа, раунд 7: 16-36…16-40)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3–6: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает (`appended: false`, замер этого прогона). Предмет аудита — 14 строк партии раунда 7; все зелёные на `969fcd61`, гэпов нет, аудитор не вызывался.

## Validation Audit 2026-10-20 (партия закрытия гэпа, раунд 8: 16-41…16-45)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3–7: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает (`appended: false`, замер этого прогона). Предмет аудита — 12 строк партии раунда 8; все зелёные на `f2a0a687`, гэпов покрытия нет, аудитор не вызывался.

## Validation Audit 2026-10-21 (партия закрытия гэпа, раунд 9: 16-46…16-50)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3–8: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает. Предмет аудита — 12 строк партии раунда 9; все зелёные на `0f341ea2`, гэпов покрытия нет, аудитор не вызывался. Регрессия CR-05 — не гэп покрытия карты (у каждой задачи есть команда, и она зелёная), а дефект предиката, найденный ревью; маршрут — через верификацию.

## Validation Audit 2026-10-23 (партия закрытия гэпа, раунд 10: 16-51…16-56)

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Таблица дописана рукой по прецеденту раундов 3–9: последний блок аудита тоже 0/0/0, и `verification.append-audit` такую запись пропускает. Предмет аудита — 17 строк партии раунда 10; все зелёные на `17fd959e`, гэпов покрытия нет, аудитор не вызывался. Находки CR-06…CR-08, WR-36…WR-39, IN-23…IN-25 повторного ревью раунда 10 — не гэпы покрытия карты, а дефекты кода; маршрут — через верификацию.
