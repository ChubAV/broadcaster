---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
verified: 2026-10-08T20:54:43Z
status: gaps_found
score: 9/10 must-haves verified
covered_files:
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-01-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-01-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-02-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-02-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-03-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-03-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-04-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-04-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-05-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-05-SUMMARY.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-06-PLAN.md"
  - ".planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-06-SUMMARY.md"
  - "alembic/versions/0023_messenger_account_phone.py"
  - "app/application/accounts/phone.py"
  - "app/models/messenger_account.py"
  - "app/services/phone.py"
  - "pyproject.toml"
  - "scripts/prohibitions_census.py"
  - "tests/test_application/test_account_phone_race.py"
  - "tests/test_application/test_account_phone_writer.py"
  - "tests/test_application/test_phone_single_writer_gate.py"
  - "tests/test_migrations/test_0023_messenger_account_phone.py"
  - "tests/test_migrations/test_model_matches_head.py"
  - "tests/test_models/test_messenger_account_phone_check.py"
  - "tests/test_phone_privacy_gate.py"
  - "tests/test_planning/test_deferred_items_are_idempotent.py"
  - "tests/test_planning/test_plan_prohibitions_census.py"
  - "tests/test_planning/test_requirement_completion_follows_verification.py"
  - "tests/test_planning/test_state_progress_matches_roadmap.py"
  - "tests/test_services/test_phone.py"
  - "uv.lock"
covered_digest: "v3:sha256:1649a7e64fbdc378e82ed3c7a63f8d590d6744ed618f0a76021d847282cecdc4"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Критерий 3 (вторая половина): мусор отвергается, а не становится «номером» (D-06) — ручной путь не сочиняет российский номер, которого не бывает, а автопуть не хранит обрывок цифр как номер"
    status: failed
    reason: >-
      CR-01 воспроизведён: normalize_manual('00 44 7911 123456') = '+700447911123456',
      '00 380 50 123 4567' = '+700380501234567', '050 123 4567' = '+70501234567',
      '8 029 123 45 67' = '+70291234567' — ни отказа, ни верного E.164: сохраняется
      «номер +7 0…», которого не бывает (у +7 национальная часть с 0 не начинается).
      Под признаком phone_is_manual=true его уже не исправит ни один автоисточник (D-07).
      Причина — буква D-05 (parse(text,'RU') → is_possible → E.164): RU-метаданные
      допускают 10 и 14 цифр, международный префикс RU — 810, а не 00. Починка-отказ
      укладывается в D-05 так же, как уже принятые Ф-1 (IS_POSSIBLE вместо голой
      возможности) и Ф-3 (отказ добавочного): is_valid_number не нужен. Вторая, меньшая
      часть — WR-04: автопуть принимает '12345' → '+12345', '4412345' → '+4412345',
      '88812' → '+88812' (REPORTED_MIN_DIGITS = 5 — выбор разведки по STACK.md, а не
      запертое решение), и собственная строка теста фазы закрепляет это как норму.
    artifacts:
      - path: "app/services/phone.py"
        issue: "normalize_manual (строки 130–140): нет отказа для кода страны 7 с национальной частью на 0 (number.italian_leading_zero); REPORTED_MIN_DIGITS = 5 (строка 44) пропускает обрывки из 5–6 цифр"
      - path: "tests/test_services/test_phone.py"
        issue: "в MANUAL_REJECTED нет строк '00…' и местного номера с ведущим 0; строка REPORTED_ACCEPTED id=five_digits_lower_bound (строка 81) утверждает '12345' → '+12345' как верное — правило фазы закрепляет дефект"
    missing:
      - "В normalize_manual отказ PHONE_ERROR_NOT_A_NUMBER, когда number.country_code == 7 и number.italian_leading_zero (без is_valid_number — D-05 соблюдён)"
      - "Строки MANUAL_REJECTED: '00 44 7911 123456', '00 380 50 123 4567', '050 123 4567', '8 029 123 45 67' (или в MANUAL_ACCEPTED с ожиданием '+447911123456' и т. п., если владелец выберет переписывание '00' → '+', см. human_verification 1)"
      - "Поднять REPORTED_MIN_DIGITS до 7 (самые короткие настоящие номера — 7 цифр с кодом страны); строку five_digits_lower_bound перенести в REPORTED_REFUSED ('12345'), границей оставить строку из 7 цифр; летописью назвать прежнее значение 5"
      - "WR-03 (по пути): в mask_phone для разбираемого номера с не более чем двумя цифрами национальной части отдавать head + ' ***'; строка '+88812' в таблицу маски"
human_verification:
  - test: "Решение владельца по CR-01, вариант ввода с префиксом 00: после починки гэпа вызвать uv run python -c \"from app.services.phone import normalize_manual; print(normalize_manual('00 44 7911 123456'))\""
    expected: "Владелец заранее называет один из двух исходов и сверяет вывод: (а) PhoneError с текстом «Не похоже на номер телефона. Пример: +7 999 123-45-67» — умолчание, буква D-05 и прецедент О-1; (б) '+447911123456' — переписывание ведущего '00' в '+', расширение набора принимаемых написаний сверх буквы D-05. В обоих случаях вывод НЕ '+700447911123456'"
    why_human: "Вариант (б) меняет набор написаний, принимаемых ручным путём, сверх буквы запертого D-05; владелец уже однажды отверг особый случай ручного пути (О-1, Fragment). Верификатор не решает за владельца, а исполнитель гэпа по умолчанию делает (а)"
  - test: "Сверка вердиктов запретов: открыть раздел «Запреты (judgment-tier)» этого отчёта — 13 строк планов 16-01…16-06, у каждой вердикт верификатора и улика"
    expected: "Владелец согласен с каждым вердиктом: 12 строк «соблюдён» с названной уликой и одна строка 16-02 №2 («MUST NOT превращать мусор в номер») — «нарушен», это и есть гэп выше"
    why_human: "Все запреты фазы — judgment-tier со статусом flagged-unverified; вердикт LLM-судьи не авторитетен и молча в passed не засчитывается (ADR-550 D4)"
---

# Фаза 16: Хранение номера, нормализация и единый писатель — отчёт верификации

**Цель фазы:** у аккаунта есть место для номера в каноническом виде E.164, записать туда номер можно только через один модуль, который не даёт автоматическому источнику затереть ручное значение — даже в гонке, — и номер не утекает в журналы
**Проверено:** 2026-10-08T20:54:43Z
**Статус:** gaps_found
**Повторная верификация:** нет — первичная

## Достижение цели

### Наблюдаемые истины

| # | Истина | Статус | Улика |
|---|--------|--------|-------|
| 1 | Критерий 1: после `upgrade head` каждый аккаунт «неизвестен» (`phone IS NULL`, `phone_is_manual = false`), `downgrade` до `0022` снимает обе колонки и больше ничего, `0023` строго за `0022`, `test_model_matches_head.py` расширен на `messenger_accounts` | ✓ VERIFIED | `alembic/versions/0023_messenger_account_phone.py`: `down_revision = "0022"`, данных не правит, `copy_from` явного состава. Настоящие upgrade/downgrade на файловой SQLite: `test_after_the_upgrade_every_account_is_unknown`, `test_the_upgrade_changes_no_existing_value`, `test_downgrade_restores_the_exact_table`, `test_the_on_delete_rules_survive_the_recreate`, `test_revision_0023_continues_0022`; `test_every_mapped_messenger_account_column_exists_at_head` с контролем-отрицанием. Всё зелено в моём прогоне (246 passed). Ветка PostgreSQL не исполнялась — она вне объёма, это деплой-гейт владельца D-26 (REQUIREMENTS §Out of Scope) |
| 2 | Критерий 2: два аккаунта с одним номером сосуществуют, «ручной без номера» отвергает CHECK по канону `0021`/`0022` | ✓ VERIFIED | Модель: `MANUAL_REQUIRES_PHONE = "NOT (phone_is_manual AND phone IS NULL)"`, `ck_messenger_accounts_manual_requires_phone` в `__table_args__`; ревизия: `CONDITION` дословно, сверка в `test_the_revision_condition_matches_the_model_word_for_word`. CHECK краснеет на INSERT и на UPDATE с обеих сторон, а три законные пары проходит (модельный и ревизионный тесты). Индекса нет: `test_two_accounts_with_one_number_coexist_and_no_index_exists`, `test_two_accounts_share_one_number` |
| 3 | Критерий 3, первая половина: названные написания (`8 999 123-45-67`, `+7 (999) 123-45-67`, `79991234567`, целое число, `+888…` автопутём, Казахстан) сводятся к одной строке E.164 и показываются как `+7 999 123-45-67` / `+7 701 123 4567` / `+888 01234567` | ✓ VERIFIED | Сам вызвал функции: все названные входы дают `+79991234567` / `+77011234567` / `+88801234567`, а `format_phone` даёт ожидаемую разбивку. Табличный тест `tests/test_services/test_phone.py` содержит все входы поимённо |
| 4 | Критерий 3, вторая половина: мусор и слишком длинный ввод отвергаются, а не становятся «номером» (D-06) | ✗ FAILED | **CR-01 воспроизведён** (см. Гэпы): `'00 44 7911 123456'` → `+700447911123456`, `'050 123 4567'` → `+70501234567`, `'8 029 123 45 67'` → `+70291234567`. Слишком длинный ввод (>32 символов, >15 цифр), местный номер без кода, добавочный, буквы — отвергаются верно. **WR-04**: автопуть `'12345'` → `+12345`, это закреплено строкой `five_digits_lower_bound` |
| 5 | Критерий 3, третья часть: сохранённый, но неразбираемый номер показывается как есть, а не как «неизвестен» | ✓ VERIFIED | `format_phone('+999123456')` → `+999123456`, `format_phone('garbage')` → `garbage` (мой вызов). Ветка `number is None: return stored` в `app/services/phone.py:183-185` |
| 6 | Критерий 4: ручной номер переживает автоматическую запись и последовательно, и в гонке; автоисточник пишет условным `UPDATE … WHERE phone IS NULL AND NOT phone_is_manual`; очистка даёт `(NULL, false)`; контроль-отрицание с чтением-проверкой-записью краснеет | ✓ VERIFIED | `_fill_if_unknown` (`app/application/accounts/phone.py:74-86`) — один условный UPDATE, исход берётся по `rowcount`. Очистка одним оператором пишет обе колонки (`:130-132`). Тест гонки идёт на двух сессиях одной файловой SQLite, с утверждением `manual_fired` против вакуума. **Своя мутация:** подменил боевой `_fill_if_unknown` на чтение-проверку-запись сторонним плагином pytest, файлы репозитория не правил. `test_the_production_writer_keeps_the_manual_number_in_every_position` покраснел: «позиция 2: итог ('+79990000002', True), ручной номер затёрт». Значит, отрицание у этого теста реальное |
| 7 | Критерий 5: номер в строке журнала `app/`, `scripts/`, `wa_worker/`, `max_worker/` краснит гейт приватности; подложенная строка доказывает, что гейт не вакуумен; в журнал уходит только `phone_set=…` | ✓ VERIFIED | `tests/test_phone_privacy_gate.py`: `GATE_TREES` из четырёх деревьев, `test_a_planted_number_line_is_found_in_every_gate_tree`, `test_a_planted_number_line_in_a_synthetic_tree_reddens_the_gate`, на живом дереве зелёный, реестр исключений пуст при потолке 0. Мой вызов предиката: `logger.info("x", phone=account.phone)` даёт нарушение. Предупреждение WR-02: `structlog.contextvars.bind_contextvars(phone=…)` нарушения не даёт (воспроизвёл), а проект этот вызов уже использует (`app/middleware.py:19`, `app/worker/tasks.py:260`) |
| 8 | Цель: записать номер в колонку можно только через один модуль (D-12, D-13) | ✓ VERIFIED | Сам прошёл грепом `app/` и `scripts/`: вне `app/application/accounts/phone.py` записи `phone` / `phone_is_manual` в колонку нет. Остальные `phone=` в `app/pages/accounts.py` уходят в разметку, в `start_session` и в `credentials` MAX. Гейт `test_phone_single_writer_gate.py` зелен на живом дереве и краснеет на подложенной записи, `PHONE_WRITER_EXCEPTIONS` содержит ровно модуль-писатель. Предупреждение WR-01: гейт пропускает executemany `session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])` — воспроизвёл. Это естественная форма скрипта Фазы 20 |
| 9 | Маска для человека D-10: `+79991234567` → `+7 *** ***-**-67`; модуль чистый, ввоза базы нет, `is_valid_number` не зовётся, тексты отказа — закрытые константы без подстановки ввода | ✓ VERIFIED | Мой вызов `mask_phone('+79991234567')` → `+7 *** ***-**-67`. Греп: в `app/services/phone.py` нет ни `is_valid_number`, ни голого `is_possible_number(`. `PhoneError` поднимается только константами `PHONE_ERROR_*`, `from None`. Предупреждение WR-03: `mask_phone('+88812')` → `+888 12`, маска ничего не прячет; достижимо только через дефект WR-04 |
| 10 | План 16-01: суита записей учится старту вехи без ослабления — `tests/test_planning` даёт ноль failed, продуктовый код не тронут | ✓ VERIFIED | Мой прогон: `uv run pytest tests/test_planning -q` → `217 passed, 3 skipped`. В коммитах 16-01 (`f31ccf79`, `2899fcd8`, `e6a83f2e`, `b197e1bb`) файлов `app/`, `alembic/`, `wa_worker/`, `max_worker/`, `main.py` нет |

**Счёт:** 9/10 истин подтверждены (0 — присутствуют, но поведение не проверено)

### Отложенное

Нет. CR-01 не покрывает ни одна поздняя фаза. Фаза 18 (критерий 2) лишь показывает текст отказа, который ей отдаёт нормализатор Фазы 16, а правило нормализации остаётся за Фазой 16.

### Требуемые артефакты

| Артефакт | Ожидается | Статус | Подробности |
|----------|-----------|--------|-------------|
| `alembic/versions/0023_messenger_account_phone.py` | ревизия с ветками диалектов, `CONSTRAINT_NAME`, `CONDITION`, `_accounts` | ✓ VERIFIED | 192 строки; upgrade/downgrade исполнены тестом на SQLite |
| `app/models/messenger_account.py` | `phone String(16)`, `phone_is_manual Boolean NOT NULL default false`, CHECK | ✓ VERIFIED | Подключён: модель читают писатель и тесты; форма колонок утверждена `test_the_column_forms_postgres_would_distinguish` |
| `app/services/phone.py` | `PhoneError`, `normalize_manual`, `normalize_reported`, `format_phone`, `mask_phone` | ⚠️ ЕСТЬ, С ГЭПОМ | Содержателен и подключён (его ввозит писатель), но правило отказа ручного пути неполно (CR-01), нижняя граница автопути пропускает обрывки (WR-04) |
| `app/application/accounts/phone.py` | `PhoneWrite`, `_fill_if_unknown`, `fill_reported_phone`, `record_reported_phone`, `set_manual_phone` | ✓ VERIFIED | Есть потребители в тестах; продуктовых потребителей нет **по замыслу**: их заведут Фазы 18–20 (CONTEXT §Phase Boundary) |
| `tests/test_phone_privacy_gate.py` | сквозной гейт PHONE-21 | ✓ VERIFIED (WR-02) | Пропуск `bind_contextvars` |
| `tests/test_application/test_phone_single_writer_gate.py` | гейт единственного писателя | ✓ VERIFIED (WR-01) | Пропуск пяти литеральных форм записи |
| `tests/test_application/test_account_phone_race.py` | гонка с контролем-отрицанием | ✓ VERIFIED | Мутация боевого кода его краснит |
| `pyproject.toml` / `uv.lock` | `phonenumberslite==9.0.41` | ✓ VERIFIED | Строка 21 `pyproject.toml`; есть в `uv.lock`; ввозит только `app/services/phone.py` |

### Проверка ключевых связей

| Откуда | Куда | Через что | Статус | Подробности |
|--------|------|-----------|--------|-------------|
| `fill_reported_phone` / `record_reported_phone` | `normalize_reported` → `_fill_if_unknown` → колонки | прямой вызов | WIRED | `app/application/accounts/phone.py:95-98, 110-118` |
| `set_manual_phone` | `normalize_manual` → `PhoneError` | прямой вызов до обращения к базе | WIRED | `:134`; отказ поднимается до `session.execute` |
| `MANUAL_REQUIRES_PHONE` (модель) | `CONDITION` (ревизия) | сверка тестом слово в слово | WIRED | `test_the_revision_condition_matches_the_model_word_for_word` |
| `run_interleaved` | боевой писатель и отрицание | один помощник | WIRED | Мутация доказала, что упрощение боевого писателя краснит тест |
| `writer_sources` / `python_sources` / `js_sources` | живое дерево и `tmp_path` | один обход | WIRED | Тесты с подложенной строкой зелены, то есть находят подложенное |

### Трассировка данных (уровень 4)

Неприменима: фаза ничего не отрисовывает. Колонку читают Фазы 17–20. Сквозной путь «автоисточник → нормализация → условный UPDATE → колонка → `format_phone`» прогнан тестом `test_an_automatic_number_fills_an_unknown_account_and_shows_in_display_form`.

### Поведенческие пробы

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Собственные модули фазы | `uv run pytest` по 8 модулям фазы | `246 passed` | ✓ PASS |
| Суита записей (план 16-01) | `uv run pytest tests/test_planning -q` | `217 passed, 3 skipped` | ✓ PASS |
| Отрицание гонки реально (критерий 4) | плагин `-p mutate_rcw` подменяет `_fill_if_unknown` чтением-проверкой-записью; один названный тест | `1 failed`: «позиция 2 … ручной номер затёрт» | ✓ PASS (мутант убит) |
| Названные входы критерия 3 | прямой вызов функций | все дают ожидаемый E.164 и показ | ✓ PASS |
| Мусор ручного пути (CR-01) | `normalize_manual('00 44 7911 123456')` и т. п. | `+700447911123456`, `+700380501234567`, `+70501234567`, `+70291234567` | ✗ FAIL |
| Мусор автопути (WR-04) | `normalize_reported('12345')`, `'4412345'`, `'88812'` | `+12345`, `+4412345`, `+88812` | ✗ FAIL |
| Маска короткого номера (WR-03) | `mask_phone('+88812')` | `+888 12` | ⚠️ WARN |
| Пропуски гейтов (WR-01/WR-02) | предикаты гейтов на синтетике | `bind_contextvars(phone=…)` → `[]`; executemany по списку словарей → `[]` | ⚠️ WARN |

Полный прогон я не повторял: оркестратор замерил `4349 passed, 3 skipped, 0 failed` на дереве `85d65afd`, код которого совпадает с HEAD.

### Пробы

Неприменимо: планы и SUMMARY не объявляют `scripts/*/tests/probe-*.sh`, фаза не миграционно-инструментальная в смысле Step 7c.

### Покрытие требований

| Требование | План-источник | Описание | Статус | Улика |
|------------|---------------|----------|--------|-------|
| PHONE-01 | 16-02, 16-03, 16-05 | номер в каноническом E.164 в отдельном поле, «неизвестен» — отдельное состояние, уникальности нет | ✗ ЧАСТИЧНО | Поле, состояние «неизвестен» и отсутствие уникальности подтверждены (истины 1, 2). Каноничность нарушена: ручной путь кладёт в поле выдуманный `+7 0…` (истина 4, CR-01) |
| PHONE-02 | 16-05, 16-06 | ручной номер не затирается автоисточником, в том числе в гонке, условной записью | ✓ SATISFIED | Истины 6 и 8, мутант убит. PostgreSQL READ COMMITTED и `rowcount` на asyncpg — деплой-гейт D-26, вне объёма |
| PHONE-21 | 16-02, 16-04 | номера не попадают в журналы, только маска или признак | ✓ SATISFIED (WR-02) | Истины 7 и 9; тексты `PhoneError` без ввода |
| `записи-старт-вехи` | 16-01 | псевдо-ID решения владельца 2026-10-08, в REQUIREMENTS.md отсутствует по прецеденту v2.1 (`долг-D-18`) | ✓ SATISFIED | Истина 10 |

Осиротевших требований нет: REQUIREMENTS.md отдаёт Фазе 16 ровно PHONE-01, PHONE-02 и PHONE-21, и каждое заявлено хотя бы одним планом.

### Найденные антипаттерны

| Файл | Строка | Шаблон | Серьёзность | Последствие |
|------|--------|--------|-------------|-------------|
| `app/services/phone.py` | 130–140 | неполное правило отказа (CR-01) | 🛑 Blocker | выдуманный `+7 0…` сохраняется под признаком «ручной» и навсегда закрыт для автоисправления |
| `app/services/phone.py` / `tests/test_services/test_phone.py` | 44 / 81 | граница 5 цифр, закреплённая тестом фазы (WR-04) | 🛑 (в составе гэпа) | обрывок `+12345` становится «номером»; будущая починка выглядела бы поломкой (урок «тесты фазы закрепляют дефекты») |
| `app/services/phone.py` | 211–223 | маска без нижнего порога (WR-03) | ⚠️ Warning | достижимо только через WR-04 |
| `tests/test_application/test_phone_single_writer_gate.py` | 86–89, 175–190 | пять литеральных форм записи не видны (WR-01) | ⚠️ Warning | второй писатель Фазы 20 в форме executemany пройдёт гейт |
| `tests/test_phone_privacy_gate.py` | 114–132, 213–215 | `bind_contextvars` не распознан (WR-02) | ⚠️ Warning | номер, привязанный к контексту structlog, уйдёт в каждую следующую строку журнала |
| `app/application/accounts/phone.py` | 86, 113–115 | `KEPT` при отсутствии строки (WR-05) | ⚠️ Warning | Фаза 20 посчитает удалённый аккаунт «ручным», забытый `session.add` в Фазе 19 пройдёт молча |
| `pyproject.toml` | 21 | точный пин `==9.0.41` (IN-02) | ℹ️ Info | метаданные нумерации заморожены |
| `scripts/prohibitions_census.py` | 1334–1338 | падение на дробных фазах (IN-04, перенесено из 15-15) | ℹ️ Info | — |

Маркеров `TBD`/`FIXME`/`XXX`/`TODO`/`HACK` в изменённых файлах нет.

### Запреты (judgment-tier, вердикт верификатора не авторитетен)

Все 13 запретов планов имеют `status: flagged-unverified`. Ниже вердикт LLM-судьи с уликой. Флаг каждой строки: `unverified-prohibition — human review recommended` (human_verification 2).

| План | Запрет (кратко) | Вердикт | Улика |
|------|-----------------|---------|-------|
| 16-01 №1 | не ослаблять правила записей | соблюдён | `tests/test_planning`: 217 passed, 3 skipped; пропуски с названной причиной |
| 16-01 №2 | не стирать числа без летописи | соблюдён | летописи `REQUIREMENT_ROWS_DECLARED`, `REGISTRY_HEADER` (по SUMMARY и коду теста) |
| 16-01 №3 | не трогать продуктовый код и не заводить живой реестр v2.2 | соблюдён | коммиты 16-01 не касаются `app/`, `alembic/`, воркеров, `main.py` |
| 16-02 №1 | не подставлять ввод в текст `PhoneError` | соблюдён | только константы `PHONE_ERROR_*`, `from None` |
| 16-02 №2 | не превращать мусор в «номер» | **нарушен** | CR-01, WR-04 — гэп |
| 16-03 №1 | нет уникального индекса по номеру | соблюдён | `test_two_accounts_with_one_number_coexist_and_no_index_exists` |
| 16-03 №2 | ревизия не заполняет номер | соблюдён | `test_after_the_upgrade_every_account_is_unknown` (в том числе MAX с номером в `credentials`) |
| 16-04 №1 | номер не попадает в журнал даже маской | соблюдён (с пропуском WR-02) | живое дерево: 0 нарушений |
| 16-04 №2 | реестр исключений не расширяется | соблюдён | `PHONE_LOG_EXCEPTIONS = {}`, потолок 0 |
| 16-05 №1 | автоисточник не затирает ручной номер | соблюдён | мутант убит |
| 16-05 №2 | автономер не помечается ручным | соблюдён | автописатели не пишут `phone_is_manual` (`_fill_if_unknown` пишет только `phone`) |
| 16-06 №1 | нет записи в обход писателя | соблюдён (с пропуском WR-01) | греп и гейт: 0 записей вне модуля |
| 16-06 №2 | реестр писателя — ровно модуль-писатель | соблюдён | `test_the_exception_registry_names_only_the_writer_module` |

### Нужна проверка человеком

#### 1. Решение владельца по префиксу `00` (CR-01, вариант «б»)

**Проверка:** после закрытия гэпа выполнить `uv run python -c "from app.services.phone import normalize_manual; print(normalize_manual('00 44 7911 123456'))"`.
**Ожидается:** исход, который владелец назвал заранее: (а) `PhoneError` «Не похоже на номер телефона. Пример: +7 999 123-45-67» — это умолчание; либо (б) `+447911123456`. В любом случае не `+700447911123456`.
**Почему человек:** вариант (б) расширяет набор принимаемых ручных написаний сверх буквы запертого D-05. Владелец уже отверг один особый случай ручного пути (О-1).

#### 2. Сверка вердиктов запретов

**Проверка:** таблица «Запреты» выше, 13 строк.
**Ожидается:** владелец согласен с каждым вердиктом. Строка 16-02 №2 «нарушен» совпадает с гэпом.
**Почему человек:** запреты judgment-tier, вердикт LLM не авторитетен.

### Сводка гэпов

**Один гэп, одна причина — D-06 «мусор отвергается» соблюдён не полностью.**

1. **CR-01 (блокер).** Ручной ввод с международным префиксом `00` или местный номер с ведущим `0` молча сохраняется как российский номер `+7 0…`, которого не бывает. Под признаком «ручной» автоисточник его уже не исправит (D-07). Дефект следует из буквы D-05: RU-метаданные допускают национальную часть из 10 и 14 цифр, а международный префикс RU — `810`. Это конфликт двух запертых решений: буква D-05 против D-06 и критерия 3 роадмапа. Разрешается он **без пересмотра** запертого. Отказ при `country_code == 7 and italian_leading_zero` не зовёт запрещённый D-05 `is_valid_number` и ужесточает ручной путь так же, как уже принятые в фазе Ф-1 и Ф-3. Поэтому это гэп фазы, а не решение владельца. Решения владельца требует только **расширение** — принимать `00 44…` как `+44…`. Оно вынесено в human_verification 1, по умолчанию — отказ.
2. **WR-04 (часть того же гэпа, меньшей тяжести).** Автопуть хранит `+12345`. Граница `REPORTED_MIN_DIGITS = 5` — выбор разведки, а не запертое решение. Её закрепляет собственное правило фазы `tests/test_services/test_phone.py::REPORTED_ACCEPTED[five_digits_lower_bound]` (`"12345"` → `"+12345"`). Это случай урока «тесты фазы закрепляют дефекты»: починка обязана переписать именно эту строку, иначе будет выглядеть регрессией.

**Предупреждения не блокируют, но планировщик гэпов REVIEW.md не читает, поэтому их нужно передать ему вручную, если владелец захочет закрыть их в том же проходе:** WR-01 (гейт писателя слеп к executemany и ещё четырём литеральным формам — прямой риск для скрипта Фазы 20), WR-02 (гейт приватности слеп к `bind_contextvars`), WR-03 (маска), WR-05 (`KEPT` на отсутствующей строке).

**Вне объёма фазы (не гэп):** ветка PostgreSQL ревизии `0023`, перепроверка READ COMMITTED и `rowcount` на asyncpg. По REQUIREMENTS §Out of Scope это деплой-гейт владельца D-26. `/gsd-secure-phase 16` не запускался, `16-SECURITY.md` нет.

---

_Проверено: 2026-10-08T20:54:43Z_
_Верификатор: Claude (gsd-verifier)_
