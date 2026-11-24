---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-26T13:21:22Z
depth: standard
review_kind: incremental
diff_base: 0125cff635de07f40b356d0b7aced5e586fb09f1
batch_base: c1d726af
head: b38f0d22
last_code_merge: 9be1215d
files_reviewed: 13
files_reviewed_list:
  - app/application/accounts/phone.py
  - app/logging_config.py
  - app/models/phone_guard.py
  - app/services/log_masking.py
  - app/worker/celery_app.py
  - tests/phone_gate_grammar.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_application/test_phone_writer_runtime_guard.py
  - tests/test_logging_config.py
  - tests/test_phone_gates_parity.py
  - tests/test_phone_privacy_gate.py
  - tests/test_services/test_log_masking.py
  - tests/test_worker/test_celery_log_mask.py
findings:
  critical: 1
  warning: 4
  info: 4
  total: 9
carried_forward: 0
closed_prior: 10
status: issues_found
---

# Phase 16: Code Review Report (инкрементальное ревью партии раунда 11, 16-57…16-64)

**Reviewed:** 2026-10-26T13:21:22Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Ревью инкрементальное. Диапазон кода — `2816cfb2..9be1215d`, база партии — `c1d726af`. Для файлов `app/` база партии совпадает с `2816cfb2`: `git diff --stat` пуст. `HEAD` `b38f0d22` по `app/` и `tests/` совпадает с `9be1215d`. Этот отчёт заменяет прежний `16-REVIEW.md`, где было 10 находок раунда 10. Все десять стоят в таблице диспозиций и все закрыты. Я судил, делает ли каждая защита то, что обещает её шапка, и называет ли шапка свою настоящую границу (О-23 (а), О-25 (а)). Полноту написаний я не судил.

**Чем мерил.** Корпуса мои, лежат в `.pytest_cache/r12review/`. Корпуса исполнителей я не брал. База для сравнения — `git archive c1d726af app` в `.pytest_cache/r12review/base/`. Каждый корпус прогонялся через базу и через `HEAD` в отдельных процессах.

| Семейство | Строк | База | HEAD | OPEN_REGRESSIONS |
|---|---|---|---|---|
| G-A: слушатель `set` после WR-37 — равные значения (`None`/`None`, `False`/`0`, `True`/`1`), подкласс `str`, правка словаря и `set_committed_value` с последующим тем же значением, `merge` над устаревшей identity map, чтение и `None` на новом объекте | 10 | 9 отказов, 1 проход | 8 проходов без чужой записи, 2 отказа (подкласс `str`, новый объект) | 0 — ни одна строка не пишет чужое значение |
| G-B: линия движка — через соединение, `schema="main"`, `RETURNING`, executemany, имя таблицы и колонки в другом регистре, `quote=False`, UPDATE внутри CTE (три написания), SQLite `INSERT OR REPLACE` | 12 | 0 отказов, 7 записей | 4 отказа; 3 записи в другом регистре (**WR-40**); 3 CTE дошли до драйвера без отказа (**CR-09**); `OR REPLACE` прошёл (**IN-29**) | 0 |
| G-C: писатель над строкой, которая ждёт вставки и уже имеет `id` | 3 | `WRITTEN`, `WRITTEN`, номер записан | `MISSING`, `MISSING`, `LookupError`, номер потерян (**WR-43**) | 3 (смена исхода писателя, а не дыра защиты) |
| G-D: формы закрытых CR-08 / WR-36 / WR-37 / IN-23 / IN-24 | 9 | 7 записей | 7 отказов; `merge` проходит; задача несёт разрешение (названо) | 0 |
| S: статический гейт на новых формах (предикат / канал) | 4 | — | CTE со значениями из переменной 0/0, CTE с литералом 1/0, другой регистр 0/0 и 0/0 | — |
| S-38: подложенные конструкции в `BaseRepository.update` | 7 | — | контроль 0; `getattr(self.session, op)(…)`, повтор закреплённого текста, тот же текст над другим получателем, две на строке (2), вычисленная строка, коллизия имени владельца — у каждой находка канала | 0 |
| M1: каждый знак U+0021…U+FFFF (и 5 астральных) в 7 формах: `+7c999c123c45c67`, знак в одной позиции русского номера, номера `+44`/`+49` | 7 × 63 460 | утечки 27/81/67/85/85/81/442 | утечки 9/63/13/67/67/63/80 | 0 |
| M2: два номера в одной строке, 8 форм × 8 форм × 12 разделителей | 768 | 39 утечек на каждом разделителе | 39 утечек только у U+2011 — то же, что ASCII `-` по краю `_LEFT` | 0 |
| M3: номер, прилегающий к краевому знаку (47 знаков × 6 номеров × 5 положений) | 1 440 | маска на 892 | маска на 1 300 | 0 |
| M4: исчерпание бюджета, затем настоящий номер | 4 вида | — | номер получает `+* *** ***-**-**`, утечки нет; бюджет кончается на 9–19 фразах разбивки (**IN-27**) | 0 |
| M5: случайный ASCII длиной 8–36 (`0-9 -()+8.x_/,:`) | 20 000 | — | расхождений с базой 0 | 0 |
| P: стоимость, 11 враждебных форм по 7–8 тыс. знаков (без повторов, с широкими разделителями, NBSP, полноширинные) | 11 | — | от 3,0 до 12,9 мс (лучшее из трёх) | — |

- **Тесты.** Четыре модуля исполнения партии зелёные: `205 passed` (`uv run pytest tests/test_worker/test_celery_log_mask.py tests/test_logging_config.py tests/test_services/test_log_masking.py tests/test_application/test_phone_writer_runtime_guard.py -q -p no:randomly`, под `flock`). Модули гейтов и полную суиту я не гонял.
- **Коммиты.** Все GREEN-коммиты таблицы диспозиций — предки `HEAD` (`git merge-base --is-ancestor`): `d0c777be`, `8e06c203`, `a75f30be`, `f4ee8a3b`, `db8f0d67`, `c278d839`, `39c04a34`, `65f6f5fe`, `06f46a81`, `20dc5717`, `5f3cb073`, `443be2b8`, `c31e077a`, `29caa899`.

**Что партия сделала верно.**
- Все формы CR-08 из моего корпуса отказывают на курсоре: `bulk_update_mappings` из переменной, держатель `staticmethod`, `bulk_insert_mappings` с «ручным», `bulk_save_objects`, upsert с `set_` из переменной, UPDATE через соединение, executemany, `RETURNING`, таблица со схемой.
- Послабление слушателя `set` (WR-37) не открыло чужой записи: проходят только значения, которые ORM сочтёт неизменными (`compare_values`), поэтому UPDATE нет.
- Маска линейна. Ответ на ASCII не изменился: 20 000 случайных строк, 0 расхождений.
- Получатель Celery держит маску в воркере, в `beat` и в дочернем процессе пула. По `celery/app/log.py:98-131` при живом получателе Celery корень не трогает.
- Закрепление реестра канала считает и текст, и число конструкций.

**Главное.** Обещание шапки защиты «отказывает каждая запись, которая проходит через `Session.execute` или курсор конструкцией DML» не держится для DML внутри CTE (**CR-09**). Линия движка выходит на признаке `isupdate`, а у внешнего `SELECT` он ложен. На PostgreSQL `WITH u AS (UPDATE messenger_accounts SET phone=…)` пишет номер мимо всех четырёх линий, и статический гейт на значениях из переменной даёт 0/0. Остальные находки — края свёртки маски, названные шире, чем измерены (**WR-41**, **WR-42**), сравнение имён без учёта регистра идентификаторов (**WR-40**) и смена исхода писателя после `autoflush=False` (**WR-43**).

**Названные границы, которые я проверил и признаю правдивыми.**
- `raw-dbapi-sql-from-a-parameter` названа в шапках защиты (`phone_guard.py:113-116`) и гейта писателя (пункт (6)).
- Формы `8)999)123)45)67` и `(999123) 45 67` нормализатор читает (`+79991234567`), а маска оставляет — так и названо.
- `merge` над истёкшей копией отказывает. Это названная цена, строка `CLOSED_FAILING_WRITES`.
- Задача, порождённая внутри `writer_scope()`, видит `True` (проба `in24_task`). Это названо: IN-24 и строка `GUARD_BOUNDARY_WRITES`.

## Structural Findings (fallow)

Структурный пре-пасс не передан — раздел пуст.

## Prior findings — disposition

| ID | Title | State | Evidence |
|----|-------|-------|----------|
| CR-06 | В воркерах Celery маски номера нет: Celery после `worker_init` заменяет обработчик корня своим и снимает и процессор `mask_numbers_in_event`, и фильтр `NumberMaskingFilter` — номер печатается целиком | closed | GREEN `d0c777be` (16-57) — предок `HEAD`. Получатель `setup_celery_logging` сигнала `celery.signals.setup_logging` — `app/worker/celery_app.py:148-154`. Механизм я сверил по исходнику Celery 5.6.2: `celery/app/log.py:98-131` — при непустом `receivers` ни очистки корня, ни своего обработчика, ни `setup_task_loggers`. `process_initializer` (`celery/concurrency/prefork.py:61-67`) возвращается по `already_setup`. Правила `tests/test_worker/test_celery_log_mask.py` (воркер, `beat`, дочерний процесс, механизм, контроль без получателя) у меня зелёные в составе `205 passed`. |
| CR-07 | Маска разбивки имеет кубическую сложность: строка журнала с путём запроса `/(1)%20(1)%20…` длиной 3,6 КБ блокирует цикл событий веб-процесса на 18 с — отказ в обслуживании без входа в систему | closed | GREEN `8e06c203` (16-60) — предок `HEAD`. Кандидат ограничен 7…15 цифрами (`log_masking.py:317-319`), края считаются один раз на поле (`_last_edges`, `:267-298`), бюджет — `:163`, `:241-264`. Мой корпус P: 11 враждебных форм по 7–8 тыс. знаков, в том числе без повторов (память судов не помогает), с разделителями шириной до 400 знаков, NBSP и полноширинные. Время от 3,0 до 12,9 мс. На базе та же `(1) ` × 2000 была кубической. |
| CR-08 | Свойство 3 О-23 не выполняется для записи мимо событий ORM: `bulk_update_mappings` / `bulk_insert_mappings` / исполнение через соединение с полями из переменной или через держатель (`setattr` с литеральным именем, `staticmethod`, `lambda`) пишут номер и признак «ручной» — не ловит ни предикат, ни канал, ни защита | closed | GREEN `a75f30be`, `f4ee8a3b`, `db8f0d67` (16-58) — предки `HEAD`. Линия движка — `phone_guard.py:403-442`. Семейства G-D и G-B: `bulk_update_mappings` из переменной, держатель `staticmethod` с `phone_is_manual=True`, `bulk_insert_mappings`, `bulk_save_objects`, upsert `set_=fields`, UPDATE через соединение, executemany, `RETURNING`, `schema="main"`. На базе — запись, на `HEAD` — `REFUSED`, строка прежняя. DML внутри CTE и имена в другом регистре — другие механизмы, это новые **CR-09** и **WR-40**, а не повторное открытие. |
| WR-36 | `before_flush` судит только историю атрибута, а INSERT нового объекта пишет его словарь — `set_committed_value(account, "phone", x)` на ещё не сохранённом аккаунте вставляет номер и `phone_is_manual = True`; утверждение шапки «оператора не порождает» ложно | closed | GREEN `f4ee8a3b`, `db8f0d67` — предки `HEAD`. Суд нового объекта по значениям — `phone_guard.py:279-284`, граница в шапке — `:121-123`. Проба `wr36_scv_new` (`set_committed_value` обеих колонок, затем `add` и `commit`): на `HEAD` — `REFUSED`. |
| WR-37 | `session.merge(account)` любого загруженного аккаунта отказывает вне писателя, даже если номер не менялся — ложный отказ на стандартном пути ORM, шапка его не называет | closed | GREEN `c278d839`, `39c04a34` (16-61) — предки `HEAD`. Сравнение с загруженным значением — `phone_guard.py:230-251`. Проба `wr37_merge_same`: на базе `REFUSED`, на `HEAD` — `PASSED` без записи. Семейство G-A (10 строк) чужой записи после послабления не нашло. |
| WR-38 | Исключение реестра канала снимает ВСЕ конструкции своего вида у владельца — новая `getattr(self.session, op)(…)` в `BaseRepository.update` проходит канал и предикат молча; правило реестра проверяет «хотя бы одну», а не число и не текст | closed | GREEN `65f6f5fe`, `06f46a81` (16-59) — предки `HEAD`. Закрепление `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` — `tests/phone_gate_grammar.py:1549-1558`, счётный `exempt_dynamic_constructs` — `:1810-1833`. Семейство S-38 на живом `app/repositories/base.py`: контроль 0. После подлога — 1 (`getattr(self.session, op)(…)`), 1 (повтор закреплённого текста), 1 (тот же текст над `self.session`), 2 (две на одной строке), 1 (вычисленная строка), 1 (второй класс `BaseRepository` — коллизия имени владельца). |
| WR-39 | Маска пропускает записи, которые ручной путь нормализатора читает номером — разбивка через NBSP (`U+00A0`), неразрывный дефис (`U+2011`) и полноширинные цифры; граница шапки их не называет | closed | GREEN `20dc5717`, `5f3cb073`, `443be2b8` (16-60) — предки `HEAD`. Свёртка — `log_masking.py:177-196, 364-378`. Семейство M1, форма F1 (`+7c999c123c45c67`): нормализатор читает 30 знаков. Маска на `HEAD` не маскирует только 9 из них — ровно `MASK_BOUNDARY_CHARACTERS`; на базе таких было 27. Названные в заголовке формы (NBSP, U+2011, полноширинные цифры) маскируются. Остатки, которые измерил я, — другие механизмы: края второго прохода (**WR-41**) и знаки, которые нормализатор читает только в одной позиции (**WR-42**). |
| IN-23 | Автосброс оператора писателя идёт под его разрешением — вторая линия (`before_flush`) на нём выключена, и отложенные изменения колонок номера чужого кода сбрасываются как записи писателя | closed | GREEN `c31e077a`, `39c04a34` (16-61) — предки `HEAD`. `autoflush=False` — `app/application/accounts/phone.py:136, 233`. Проба `in23_dirty_then_writer` (история помечена мимо события, затем `fill_reported_phone`): на базе — запись `('+79990000009', 1)`, на `HEAD` — `REFUSED`. Побочный эффект этой правки — новая **WR-43**. |
| IN-24 | Задача или поток, порождённые внутри `writer_scope()`, уносят разрешение навсегда — `finally` снимает переменную только в текущем контексте | closed | GREEN `39c04a34`, строка таблицы — `29caa899`; оба предки `HEAD`. Находка закрыта тем, что граница названа: `phone_guard.py:72-80, 117-120` и докстринг `writer_scope` (`:207-212`). Проба `in24_task` по-прежнему видит `True`, и это ровно то, что шапка называет. |
| IN-25 | `NumberMaskingFilter` пропускает без маски любую запись со словарём в `msg`, а не только запись structlog — на обработчиках uvicorn такой словарь печатается с номером | closed | GREEN `20dc5717` — предок `HEAD`. Код — `log_masking.py:477-487`, корень ставит фильтр с `True` (`logging_config.py:63`). Моя проба через настоящий `setup_logging`: `uvicorn.error` со словарём в `msg` печатает `{'detail': '+7 *** ***-**-67', 'n': ['+7 *** ***-**-67']}`. Чужая запись со словарём и `exc_info` через корень даёт маску и в `event`, и в `exception`. |

Вне этого прохода — отложенные IN-01, IN-02, IN-03, IN-04, IN-05 (решение владельца О-4) и пропущенная WR-35 (О-23 (а), свойство 4). Их я не пересматривал.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-09: DML внутри CTE пишет колонки номера мимо всех четырёх линий защиты — `select(update(MessengerAccount).values(fields).returning(…).cte())` на PostgreSQL ставит номер, а линия движка выходит на признаке `isupdate` внешнего `SELECT`

**File:** `app/models/phone_guard.py:412-419` (`_refuse_unscoped_cursor`), `:339-345` (`_refuse_unscoped_statement`); обещание — `:12-15`, `:43-56`, `:68-70`; `tests/test_application/test_phone_single_writer_gate.py`, пункт (а) шапки («пути DML через движок … первый рубеж — защита на исполнении»)

**Issue:**
- **Что обещано.** Шапка защиты обещает по механизму: «отказывает каждая запись, которая проходит через … `Session.execute` или курсор `Connection` SQLAlchemy конструкцией DML (UPDATE / INSERT), — со значениями из литерала, переменной, параметра или цикла одинаково». Линия 4 названа так: «скомпилированный `Update` / `Insert` таблицы `messenger_accounts`».
- **Что делает код.** Код судит только оператор верхнего уровня. Сначала идёт `if context is None or not (context.isinsert or context.isupdate): return` (`:412`), затем `compiled.statement` должен быть `Update`/`Insert` (`:418`). У `select(cte)`, где CTE — это `update(...).returning(...)`, признаки `isupdate` и `isinsert` ложны. Шапка сама это и называет: «SELECT … выходят сразу» (`:68-70`). Линия 3 (`do_orm_execute`) выходит по `is_update`/`is_insert`, линии 1–2 к оператору не относятся.
- **Замер.** Компиляция для диалекта PostgreSQL (`pg_compile.py`):
  ```
  WITH u AS (UPDATE messenger_accounts SET phone=%(param_1)s WHERE messenger_accounts.id = %(id_1)s RETURNING messenger_accounts.id) SELECT u.id FROM u | isupdate False isinsert False
  ```
  Это законный SQL PostgreSQL: data-modifying statement в `WITH`, а `update(...).returning(...).cte()` — документированная идиома SQLAlchemy. На SQLite в памяти (`guard_probe.py`: `b_cte_select` через соединение, `b_cte_select_session` через `Session.execute`, `b_cte_insert_other` — CTE на `UPDATE users` через `add_cte`) все три формы на `HEAD` дошли до драйвера без отказа защиты. SQLite ответил `OperationalError: near "UPDATE": syntax error`, потому что DML в CTE не поддерживает. На PostgreSQL та же строка исполняется и пишет. Та же дыра есть у INSERT: `insert(MessengerAccount).values(..., phone=x, phone_is_manual=True).returning(...).cte()` внутри `select` создаёт «ручной» аккаунт (компиляция `WITH i AS (INSERT INTO messenger_accounts (…, phone, phone_is_manual) VALUES …)`).
- **Статический гейт** (`static_probe.py`, `judged_offences` + `dynamic_construct_findings` с `BANNED_GETATTR_NAMES` после реестра). Форма `fields = {"phone": x}; cte = update(MessengerAccount).…values(fields).returning(MessengerAccount.id).cte("u"); await session.execute(select(cte.c.id))` даёт предикат 0 и канал 0. С литералом `values(phone=x)` предикат 1. Значит, пересечение «данные из переменной × оператор, который защита не видит» снова не закрыто ничем — это класс CR-08 в новом написании. Защита при этом обещает судить именно «по механизму, а не по написанию».
- **Охват.** В живом дереве `.cte(` и `add_cte` нет (grep `app/`, `scripts/` — 0). Но адресат защиты — писатели фаз 17–20 (скрипт дозаполнения), и для них шапка утверждает первый рубеж, которого нет. Граница («ГРАНИЦА, НАЗВАННАЯ ПРЯМО») DML в CTE не называет.

**Fix:** судить и вложенный DML — каждую CTE скомпилированного оператора, а не только оператор верхнего уровня. В линии движка:
```python
def _dml_targets(compiled, dml):
    """Оператор верхнего уровня и каждый DML внутри CTE (SELECT / INSERT / UPDATE с `WITH`)."""
    found = [dml] if isinstance(dml, (Update, Insert)) else []
    for cte in getattr(compiled, "ctes", {}) or {}:
        element = getattr(cte, "element", None)
        if isinstance(element, (Update, Insert)):
            found.append(element)
    return found

def _refuse_unscoped_cursor(conn, cursor, statement, parameters, context, executemany):
    if context is None or context.compiled is None:
        return
    compiled = context.compiled
    targets = [d for d in _dml_targets(compiled, compiled.statement)
               if isinstance(_target_table(d.table), TableClause)
               and _target_table(d.table).name == _ACCOUNTS_TABLE_NAME]
    if not targets or _WRITER_ACTIVE.get():
        return
    for dml in targets:
        if dml is not compiled.statement:
            # значения вложенного DML — привязки с анонимными именами: отказ в закрытую
            if _cursor_columns(dml, compiled)[0] & _GUARDED or isinstance(dml, Insert):
                raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
            continue
        ...  # прежний суд оператора верхнего уровня
```
Ранний выход по `isinsert`/`isupdate` стоит оставить только для операторов без `compiled.ctes`, тогда дешевизна сохраняется. Аналогично в `do_orm_execute`: если у оператора есть `_independent_ctes` или CTE с DML по таблице аккаунтов — отказ. Нужна строка `FOREIGN_WRITES`. На SQLite её не исполнить, поэтому правило может судить сам слушатель: собрать `select(cte)` и вызвать линию с контекстом скомпилированного оператора. Ещё нужна строка шапки.

## Warnings

### WR-40: Линия движка сравнивает имя таблицы и колонок с учётом регистра — `table("MESSENGER_ACCOUNTS", column("PHONE"))` пишет номер на SQLite, а `quoted_name(…, quote=False)` — и на PostgreSQL; статический гейт даёт 0/0 даже с литеральным значением

**File:** `app/models/phone_guard.py:354` (`_ACCOUNTS_TABLE_NAME`), `:421` (`table.name != _ACCOUNTS_TABLE_NAME`), `:355`, `:398-399`, `:428` (имена колонок через `_GUARDED`); шапка — `:45-48`

**Issue:** шапка говорит: «Таблица судится по ИМЕНИ … видны лёгкая `sqlalchemy.table(…)`, отражённая таблица и таблица миграции». Сравнение при этом точное, а СУБД складывают регистр идентификаторов. SQLite складывает его всегда, даже в кавычках. PostgreSQL складывает неквотированные идентификаторы. Замер (`guard_probe.py`, SQLite в памяти, UPDATE через соединение):

| Форма | База | HEAD |
|---|---|---|
| `table("MESSENGER_ACCOUNTS", column("id"), column("phone"…))` | WROTE | **WROTE** `(None, 0) → ('+79991234567', 0)` |
| `table(quoted_name("Messenger_Accounts", quote=False), …)` | WROTE | **WROTE** |
| `table("messenger_accounts", column("PHONE"), …)`, `values({"PHONE": x})` | WROTE | **WROTE** |
| `column("Phone_Is_Manual")` = `True` | дошло до CHECK базы | дошло до CHECK базы (защита не отказала) |
| контроль `table("messenger_accounts", …)` | WROTE | REFUSED |

Для PostgreSQL (`pg_compile.py`) форма `quoted_name("MESSENGER_ACCOUNTS", quote=False)` с колонкой `quoted_name("PHONE", quote=False)` компилируется в `UPDATE MESSENGER_ACCOUNTS SET PHONE=%(PHONE)s …`, а PostgreSQL складывает это в `messenger_accounts.phone`. Автоквотированная форма `"MESSENGER_ACCOUNTS"` на PostgreSQL — другая таблица (ошибка), поэтому на боевой базе нужен явный `quote=False`. Статический гейт (`static_probe.py`): `upper_table_literal` с `values(PHONE=x)` даёт предикат 0 и канал 0, у `upper_table_var` тоже 0/0. Это не регресс: на базе линии движка не было. Но обещание «судится по имени» читается как «по имени таблицы», а держится только для одного написания имени. Предупреждение, а не блокер: на PostgreSQL обход требует явного `quote=False`, случайно его не напишут.

**Fix:** сравнивать имена так, как их сравнивает СУБД. Дёшево и в закрытую — без регистра:
```python
_ACCOUNTS_TABLE_NAME = MessengerAccount.__tablename__.lower()
_GUARDED = frozenset(c.lower() for c in GUARDED_COLUMNS)
...
if not isinstance(table, TableClause) or str(table.name).lower() != _ACCOUNTS_TABLE_NAME:
    return
...
names = {_column_name(key).lower() for key in keys}
names.update({k.lower() for k in set(positional) & set(compiled.column_keys or ())})
```
Ключи `row.get("phone")` для INSERT тоже нужно искать без регистра. Отказ в закрытую при квотированном `"MESSENGER_ACCOUNTS"` на PostgreSQL безвреден: такой таблицы нет. Нужны строки `FOREIGN_WRITES` и строка шапки.

### WR-41: Второй проход свёртки «краёв первого прохода не меняет» — номер, у которого голова до Юникод-разделителя сама признаётся номером, маскируется наполовину: `+49 30 123 4567` → `+49 ** *23 4567`

**File:** `app/services/log_masking.py:364-378` (`mask_numbers`: второй проход идёт по `masked`, а не по исходному тексту); шапка — `:29-35`; шапка гейта приватности (`tests/test_phone_privacy_gate.py`, пункт «Защита на исполнении»: «Знаки, которые нормализатор читает внутри номера … судятся свёрнутыми»)

**Issue:** первый проход судит текст как есть. Цепочка разбивки обрывается на NBSP (U+00A0 не входит в `_SPLIT_CHARACTERS`). Если префикс до обрыва — сам номер по нормализатору, его маскируют, и хвост остаётся. Это возможно у переменной длины номеров: DE `+4930123` и подобные. Второй проход идёт уже по маскированному тексту: хвост `4567` за маской номером не становится. Замер M1 (`m1b.py`): у форм `+49 30 123{c}4567`, `+49 30 1234{c}567`, `+49 89 1234{c}5678`, `+39 06 1234{c}5678` на `HEAD` утекают по **17** свёрнутых разделителей каждая. Среди них NBSP, U+2011, U+2010…U+2015, U+2212, U+2053, U+00AD, U+200B, U+2060, то есть ровно те знаки, ради которых делалась свёртка WR-39. Нормализатор читает все эти строки как `+49301234567` / `+498912345678` / `+390612345678`, а маска оставляет видимыми 6 из 10 национальных цифр. Через настоящий `setup_logging` (`structlog.get_logger("x").info("ev", p2="+49 30 123 4567")`) печатается `"p2": "+49 ** *23 4567"`. На ASCII-разбивке `+49 30 123 4567` первый проход судит длинный префикс первым и маскирует номер целиком. Значит, утечку даёт именно двухпроходная схема 16-60. На базе вывод тот же (OPEN_REGRESSIONS = 0). Но шапка и гейт приватности утверждают, что эти знаки «судятся свёрнутыми», а граница этого случая не называет. Правило `test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named` меряет одну форму — русский номер с разделителем во всех позициях, где ни один префикс не признаётся номером. Поэтому он этого не видит. По тяжести это частичная утечка того же класса, что WR-39 (предупреждение).

**Fix:** во втором проходе судить свёрнутую копию ИСХОДНОГО текста, а спан, который строго содержит спан первого прохода, ставить вместо него:
```python
def mask_numbers(text: str) -> str:
    judgments = _Judgments()
    first = _spans_of(text, text, judgments)            # спаны первого прохода на исходном тексте
    folded = text.translate(_NUMBER_FOLD)
    if folded == text:
        return _apply(text, first)
    second = _spans_of(text, folded, judgments)
    # спан второго прохода, накрывающий спан первого, побеждает; прочие спаны первого остаются
    return _apply(text, _merge_preferring_wider(first, second))
```
Края ASCII-номеров первого прохода (`‑+7…` и т. п.) так сохраняются: второй проход только расширяет найденное, но не сужает. Нужны строки таблицы маски (`+49 30 123 4567` → маска целиком) и вторая форма в правиле свёртки: знак в одной позиции номера, у которого префикс признаётся номером.

### WR-42: Знаки, которые нормализатор читает в одной позиции номера, не свёрнуты и не названы — `+7~999 123 45 67`, `8 999 123～45 67`, `8 999 123x45 67` печатаются целиком; правило «каждый знак свёрнут или назван» меряет только форму со знаком во всех позициях

**File:** `app/services/log_masking.py:29-37` (обещание «правило … держит таблицу в согласии с нормализатором»), `:186-196` (`_FOLDED_SEPARATORS`); `tests/test_services/test_log_masking.py:340-377` (единственная форма `f"+7{ch}999{ch}123{ch}45{ch}67"`), `:296` (`MASK_BOUNDARY_CHARACTERS`); шапка гейта приватности (граница маски)

**Issue:** `normalize_manual` отбрасывает одиночный нецифровой знак, если он стоит в одной позиции. С тем же знаком во всех четырёх позициях он номер не читает. Поэтому правило-перебор его не видит. Замер M1 (`m1c.py`, U+0021…U+FFFF, утечки на `HEAD` сверх названных 9 знаков):

| Форма | Утечек | Латиница | Прочие буквы | Прочие знаки |
|---|---|---|---|---|
| `+7 999 123 45{c}67` | 63 | 50 | 4 | — |
| `+7{c}999 123 45 67` | 13 | 2 | 0 | U+007E `~`, U+FF5E `～` |
| `8 999 123{c}45 67` | 67 | 52 | 4 | U+007E, U+FF5E |
| `+7 999{c}123 45 67` | 67 | 52 | 4 | U+007E, U+FF5E |

Проверка: `normalize_manual('+7~999 123 45 67')`, `('8 999 123x45 67')` и `('+7 999 Z123 45 67')` дают `+79991234567`. Через настоящий `setup_logging` значения `phone="+7~999 123 45 67"` и `p3="8 999 123x45 67"` печатаются как есть, все 11 цифр. На базе то же (OPEN_REGRESSIONS = 0). Но шапка утверждает, что правило «перебирает U+0021…U+FFFF … и держит таблицу в согласии с нормализатором», а граница называет букву только краем слева (`id79991234567`, `x+79991234567`). Буквы внутри номера, `~` и `～` (оба — `VALID_PUNCTUATION` библиотеки `phonenumbers`) не названы нигде. По О-24 (а) это номер, и он утекает целиком. Тяжесть та же, что у WR-39.

**Fix:** добавить U+007E и U+FF5E в `_FOLDED_SEPARATORS` (как `-`). Букву внутри разбивки свёрткой не закрыть без ложных масок на хэшах и ID, поэтому назвать её строкой `MASK_BOUNDARY_SUBSTRINGS` («одиночная буква внутри номера: нормализатор её отбрасывает»). В правило свёртки добавить формы со знаком в одной позиции (`+7{ch}999 123 45 67`, `8 999 123{ch}45 67`), чтобы таблица и нормализатор сверялись не на одной форме.

### WR-43: `autoflush=False` у операторов писателя (IN-23) меняет его исход на строке, ждущей вставки с уже известным `id`: на базе `WRITTEN`, на `HEAD` — `MISSING` или `LookupError`, а номер теряется

**File:** `app/application/accounts/phone.py:125-143` (`_fill_if_unknown`), `:199-211` (`record_reported_phone`: сброс только при `account.id is None`), `:229-236` (`set_manual_phone`); абзац «ЗАЩИТА НА ИСПОЛНЕНИИ» — `:40-45`

**Issue:** до 16-61 автосброс перед UPDATE вставлял ожидающую строку, и писатель её видел. Теперь UPDATE идёт мимо отложенной вставки. Проба существования `select(exists().where(...))` тоже ничего не сбросила: на `HEAD` исход `MISSING`, а не `KEPT`. Замер G-C (`guard_probe.py`, объект `MessengerAccount(id=777, …)` добавлен в сессию и не сброшен):

| Вызов | База | HEAD | Строка после `commit` на HEAD |
|---|---|---|---|
| `record_reported_phone(s, n, "79990000003")` | `WRITTEN`, номер записан | **`MISSING`** | `phone = NULL` |
| `fill_reported_phone(s, 778, "79990000004")` | `WRITTEN` | **`MISSING`** | `phone = NULL` |
| `set_manual_phone(s, 779, "+7 999 000-00-05")` | номер записан | **`LookupError`** | `phone = NULL` |

`record_reported_phone` обещает: «Строка без `id` сначала сбрасывается в базу, затем пишется тем же условным оператором». Но условие — `id is None`, а не «объект ещё не вставлен». Абзац писателя называет отсрочку («прочие отложенные изменения … сбрасываются … на его следующем сбросе или коммите»), но не её следствие. Писатель выдаёт живую (ожидающую) строку за удалённую, то есть это класс WR-05 («ни один писатель не выдаёт отсутствие строки за другой исход»). Есть и обратная сторона. Отложенный `session.delete(account)` раньше давал `MISSING`, а теперь даёт `WRITTEN` по строке, которую удалит коммит. В живом дереве явных `id` у `MessengerAccount(...)` нет, вызывающих писателя тоже пока нет, поэтому дефект латентный. Но адресаты — мастер Фазы 19 и скрипт Фазы 20.

**Fix:** сбрасывать сессию ДО входа в разрешение. IN-23 так остаётся закрытой: чужие отложенные изменения номера отказывают второй линией вне `writer_scope()`. А писатель видит ожидающие строки, как до 16-61:
```python
async def _fill_if_unknown(session, account_id, e164):
    await session.flush()            # вне разрешения: чужие правки номера отказывают здесь
    with writer_scope():
        result = await session.execute(
            update(MessengerAccount)....execution_options(synchronize_session=False, autoflush=False)
        )
```
То же нужно в `set_manual_phone`. В `record_reported_phone` условие сброса — `inspect(account).pending`, а не `account.id is None`. При пустой сессии сброс операторов не порождает, поэтому счёт операторов теста гонки не меняется. Нужна строка правила: ожидающая строка с `id` → `WRITTEN`.

## Info

### IN-26: Шапка маски называет «22 разделителя», а список рядом и `_FOLDED_SEPARATORS` держат 18 (плюс U+FF0B)

**File:** `app/services/log_masking.py:31`, `:186-192`
**Issue:** находка известна: её нашёл исполнитель 16-63, подтвердил оркестратор. Я перепроверил: `len(_FOLDED_SEPARATORS) == 19` — это 18 разделителей и полноширинный плюс. Перечень в `:31-33` тоже насчитывает 18: 4 пробела, 12 тире и дефисов, 2 скобки. Четыре знака замера планирования (U+FF0E, U+FF0F, U+FF3B, U+FF3D) — граничные, они не свёрнуты. Сам перечень верен, неверно только число. Поэтому это Info.
**Fix:** «18 разделителей» (или «18 разделителей и полноширинный плюс»). Правило шапки маски может сверять число с `len(_FOLDED_SEPARATORS) - 1`.

### IN-27: Названная цена бюджета — «поле с больше чем 64 разными кандидатами-номерами», а по замеру бюджет кончается на 9–19 фразах разбивки

**File:** `app/services/log_masking.py:44-47, 64-67`, `:159-163`; шапка гейта приватности («судов нормализатора на вызов — не больше `MASK_JUDGMENT_BUDGET` (64)»)
**Issue:** суд тратится на каждый префикс разбивки, а их до 9 на одно начало (`:319`). Замер M4 (`m4b.py`, разные фразы, затем `id 1729500000000 phone +7 999 123-45-67`):

| Вид фраз | Бюджет кончился на |
|---|---|
| `+d d d …` (16 цифр) | 12 |
| `(dd) d …` | 9 |
| `8 d …` | 12 |
| `+d ddd ddd dd dd dd dd` | 19 |
| цепочки из 7 цифр | 63 |

После этого метка времени и номер получают звёзды. Номер не утекает: `+* *** ***-**-**`. Но «патологическое поле» на деле — строка с десятком скобочных групп, например `repr` списка. Это сужает наблюдаемость шире, чем названо.
**Fix:** назвать в шапке единицу бюджета — суд префикса, до 9 на начало разбивки — и замер «9–19 фраз разбивки или 63 цепочки цифр». Либо считать бюджет по кандидатам-началам, а не по префиксам.

### IN-28: Получатель `setup_celery_logging` отбрасывает `loglevel` и `logfile` сигнала — флаг `--loglevel` в `docker-compose.prod.yml` молча перестал действовать

**File:** `app/worker/celery_app.py:148-154`; `docker-compose.prod.yml:119, 127, 135`
**Issue:** Celery передаёт получателю `loglevel=…, logfile=…, format=…, colorize=…` (`celery/app/log.py:98-101`). Получатель берёт уровень из `settings.log_level`. До 16-57 корень ставил Celery с уровнем из CLI. Сегодня оба уровня — `INFO` (`app/config.py:11`, compose `--loglevel=info`), поэтому вреда нет. Но `celery … --loglevel=debug` при отладке ничего не изменит, а шапка блока это не называет.
**Fix:** назвать в шапке («уровень — `LOG_LEVEL`, флаг `--loglevel` Celery не действует») или передавать `kwargs.get("loglevel")`, если он задан явно.

### IN-29: SQLite `INSERT OR REPLACE` с законными значениями стирает ручной номер мимо линии движка — префикс оператора линия не читает

**File:** `app/models/phone_guard.py:431-437` (INSERT судится по значениям), шапка — `:49-53`, `:130-133`
**Issue:** замер (`replace_probe.py`, SQLite). `insert(MessengerAccount.__table__).prefix_with("OR REPLACE").values(id=i, …, phone=None, phone_is_manual=False)` над строкой `('+79991234567', 1)` даёт `(None, 0)`, и на `HEAD` защита это пропускает. Контроль — `update(...).values(phone=None, phone_is_manual=False)` — отказывает. Шапка говорит: «очистка номера тоже запись», а ветку после `VALUES`, которую линия не читает, судит в закрытую. Префикс `OR REPLACE` в обоих местах не учтён. Это только SQLite, то есть база суиты; на PostgreSQL такого префикса нет. Поэтому Info.
**Fix:** у вставки в таблицу аккаунтов с непустым `_prefixes` отказывать в закрытую. Либо назвать это в границе шапки.

---

_Reviewed: 2026-10-26T13:21:22Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
