---
phase: 05-tarify
plan: 22
subsystem: payments
tags: [yookassa, subscription, billing, decimal, structlog, pytest, tdd]

requires:
  - phase: 05-18
    provides: "`converted_remainder` и верхняя граница переноса в ветке КОНВЕРСИИ (форма `convert-remainder`, D-30)"
  - phase: 05-19
    provides: "AST-ловушка порядка снятия признака живости — правка ветки обязана её не сломать"
  - phase: 05-20
    provides: "гейт порядка выката и сверка модели с головой (`tests/test_migrations/`)"
  - phase: 05-21
    provides: "состояние суиты 1733 зелёных теста, от которого считается прирост"
provides:
  - "`capped_carryover` — правило верхней границы переноса, объявленное ОДИН раз чистой функцией в модуле отсчёта"
  - "верхняя граница предоплаченного горизонта на ОБЕИХ ветках повышения: ветка отката перестала оставлять `base` связанной с `subscription.expires_at`"
  - "две регрессии на оба входа в ветку отката, доказанно КРАСНЫЕ на коде до правки"
  - "поле `stage` у обоих испусканий `subscription_prorating_skipped` — два разных исхода различимы разбирающим обращение"
  - "модульная таблица решений границы: шесть строк, включая проход по каждому дню обычного и високосного года"
affects: [05-25, 05-26, верификация раунда 7]

actuals:
  tokens: 72465
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Каждое правило выбора точки отсчёта объявляется чистой функцией в `subscription_period.py`; денежный путь его ЧИТАЕТ и не вычисляет базу выражением"
    - "Два испускания одного журнального ключа различаются ПОЛЕМ, а не вторым ключом"
    - "Перечень тарифов приезжает в тестовый помощник аргументом с умолчанием `None`; объявление, которое зовут десятки тестов, не трогается"

key-files:
  created: []
  modified:
    - app/application/billing/subscription_period.py
    - app/services/payment_service.py
    - tests/test_pages/test_billing_payment_errors.py
    - tests/test_application/test_subscription_period.py

key-decisions:
  - "Форма верхней границы переноса в ветке отката — `cap-one-month` (ответ владельца на чекпойнт задачи 1, дословно: `cap-one-month`). Номер решения присваивает план 05-26"
  - "Цена формы принята сознательно и названа числом: остаток длиннее календарного месяца сгорает в части сверх месяца (около одиннадцати месяцев у предоплатившего год) — исключение из прохибиции плана 05-01, а не её соблюдение"
  - "Имя поля различения веток и оба его значения взяты из `IN-04` (`05-REVIEW.md:596-601`) дословно: `stage` со значениями `prorate_refused` и `convert_remainder`"
  - "Объявление `_confirm` оставлено ДОСЛОВНЫМ, а перечень тарифов вынесен в новый `_confirm_with_plan_limits`: критерий приёмки задачи 2 запрещает удалять строки с `_confirm(`, и объявление помощника — такая строка"

patterns-established:
  - "Правило выбора базы объявляется в модуле отсчёта, а `_apply_extension` выбирает, какую объявленную функцию позвать (решение `promote` раздела `<assumption_delta_decision>`)"
  - "Инициализация `base = subscription.expires_at` несёт комментарий, называющий ЕДИНСТВЕННЫЙ случай, в котором она доживает до сдвига срока"

requirements-completed: [BILL-05, BILL-07]

coverage:
  - id: D1
    description: "Верхняя граница предоплаченного горизонта стоит в ветке отката при нечитаемой цене ПЛАНА ПЛАТЕЖА (`price_to is None`): горизонт ограничен двумя календарными месяцами вместо 396 дней"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon"
        status: pass
    human_judgment: false
  - id: D2
    description: "Та же граница при нечитаемой цене ДЕЙСТВУЮЩЕГО плана — повышение с подписки `free` с живым горизонтом (`price_from is None`, вход достижим по построению)"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_an_upgrade_from_free_does_not_carry_the_whole_horizon"
        status: pass
    human_judgment: false
  - id: D3
    description: "Два испускания `subscription_prorating_skipped` различимы полем `stage`: разбирающий обращение может назвать ветку"
    requirement: BILL-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_the_refused_branch_names_its_own_stage_in_the_journal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon"
        status: pass
    human_judgment: false
  - id: D4
    description: "Арифметика границы `capped_carryover` покрыта таблицей решений той же формы, что таблицы соседей (шесть строк, проход по каждому дню обычного и високосного года)"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_application/test_subscription_period.py#test_the_capped_carryover_never_exceeds_one_month_on_any_day_of_the_year"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_subscription_period.py#test_a_remainder_shorter_than_a_month_is_carried_whole"
        status: pass
    human_judgment: false
  - id: D5
    description: "Человек, чей горизонт после повышения при нечитаемой цене оказался короче ожидаемого, читает исход как объявленное правило, а не как отнятые дни"
    verification: []
    human_judgment: true
    rationale: "Интерфейсного ответа на конверсию планы фазы сознательно не заводили, и этот план его не заводит тоже — судится человеком (backstop-строка `must_haves`)"

duration: 30min
completed: 2026-08-18
status: complete
---

# Phase 05 Plan 22: Верхняя граница переноса в ветке отката денежного пути

**Ветка отката `_apply_extension` перестала переносить весь предоплаченный горизонт на старший тариф: правило границы `capped_carryover` объявлено один раз в модуле отсчёта и прочитано денежным путём, оба входа в ветку закреплены регрессиями, доказанно красными на коде до правки, а два испускания одного журнального ключа различимы полем `stage`.**

## Performance

- **Duration:** ~30 мин (агент-продолжение; чекпойнт задачи 1 снят предыдущим агентом)
- **Started:** 2026-08-18T06:02:00Z
- **Completed:** 2026-08-18T06:31:40Z
- **Tasks:** 3 (задача 1 — чекпойнт, снят владельцем; задачи 2 и 3 исполнены)
- **Files modified:** 4

## Решение владельца (задача 1)

**Ответ дословно:** `cap-one-month`

**Что он означает.** Верхняя граница переноса оплаченного остатка в ветке, где цену любого из
двух планов прочитать нельзя, — потолок в ОДИН календарный месяц остатка:

```
base = min(countdown_base(expires_at, now), add_one_month(normalize_utc(now)))
```

**Цена решения числами** (посев «подписка `basic` с живым горизонтом 365 дней плюс платёж `pro`
за 4900 ₽», прогон 2026-08-18):

| Величина | До правки | После правки |
|---|---|---|
| Выданный горизонт Pro | 395 дней | 60 дней (два календарных месяца) |
| Уплачено | 22 780 ₽ | 22 780 ₽ |
| Прейскурант выданного | 63 700 ₽ | 9 800 ₽ |
| Остаток 364 дня `basic` | перенесён ЦЕЛИКОМ | перенесён в объёме месяца |

**Что оплачено этим решением.** Остаток КОРОЧЕ календарного месяца переносится целиком и не
сгорает ни на день — защитная семантика 25 дней (D-04) не тронута. Остаток ДЛИННЕЕ месяца
сгорает в части, превышающей месяц: человек, предоплативший год и попавший в ветку из-за правки
окружения, теряет около одиннадцати месяцев оплаченного времени. Это **исключение** из
прохибиции плана `05-01` («MUST NOT сжигать неистраченный остаток уже оплаченного периода»), а
не её соблюдение, и оно допущено сознательно: величина, которой управляет ПОКУПАТЕЛЬ, не имеет
права быть неограниченной ни на одной ветке денежного пути.

**Отвергнутые владельцем формы:** `no-carry` (отнимала бы ВСЕ оплаченные дни и наказывала бы
человека за расхождение нашего конфига с нашей же базой), `refuse-at-intent` (не закрывает
ветку для платежей в полёте и останавливает продажи вместо ограничения выдачи), `accept-risk`
(оставляла бы величину без границы шестой раунд подряд).

**Номер решения этот план не присваивает** — его записывает план `05-26` в `05-CONTEXT.md`
(планировалось как D-31).

## Accomplishments

- **Правило границы объявлено ОДИН раз.** `capped_carryover(current, now) -> datetime` живёт в
  `app/application/billing/subscription_period.py` рядом с `countdown_base`, `next_expiry`,
  `prorated_expiry` и `converted_remainder`. `_apply_extension` его ЧИТАЕТ: `grep -c
  "add_one_month" app/services/payment_service.py` возвращает `0` — второй копии правила
  отсчёта на денежном пути нет.
- **Ветка отката присваивает базу ЯВНО.** Строка 1076 `app/services/payment_service.py`:
  `base = capped_carryover(subscription.expires_at, now)` — внутри `if price_from is None or
  price_to is None:` (строка 1049), сразу после испускания журнала. Инициализация
  `base = subscription.expires_at` (строка 1029) осталась, но получила комментарий, называющий
  ЕДИНСТВЕННЫЙ случай, в котором она доживает до сдвига: «план не меняется либо срок мёртв».
- **Оба входа в ветку закреплены регрессиями, доказанно красными.** `unreadable="paid_plan_price"`
  — значение, которое до этого плана не утверждал ни один тест суиты.
- **Два испускания одного ключа различимы.** Поле `stage`: `prorate_refused` в ветке отказа
  (строка 978), `convert_remainder` в ветке конверсии (строка 1055). Оба значения утверждают
  тесты.
- **Модульная таблица границы** — шесть строк решений в
  `tests/test_application/test_subscription_period.py`, включая параметризованный проход по
  каждому дню обычного (2026) и високосного (2028) года.

## Task Commits

1. **Task 1: Форма верхней границы переноса — решение владельца** — чекпойнт, кода не требует;
   критерий «`git diff --name-only -- app/` пуст на момент чекпойнта» выполнен предыдущим агентом
2. **Task 2: RED — две регрессии ветки отката и модульная таблица границы** — `353c4df` (test)
3. **Task 3: GREEN — правило границы объявлено один раз и прочитано денежным путём** — `e800209` (feat)

## Доказательство RED (задача 2)

Прогон критерия приёмки **до единой правки `app/`**
(`git diff --name-only -- app/` был пуст):

```
$ uv run pytest tests/test_pages/test_billing_payment_errors.py -q \
    -k "unreadable or free_does_not_carry or paid_plan_price"
FF                                                                       [100%]
...
>       assert granted <= ceiling + timedelta(days=2), (
E       AssertionError: уплачено 22780.00 ₽, а выдан горизонт 395 дней на тарифе pro
        при прейскуранте 63700.00 ₽: остаток 364 дней перенесён ЦЕЛИКОМ —
        у ветки отката нет верхней границы
E       assert datetime.datetime(2027, 9, 18, ...) <= (datetime.datetime(2026, 10, 18, ...)
        + datetime.timedelta(days=2))
tests/test_pages/test_billing_payment_errors.py:2562: AssertionError
...
>       assert granted <= ceiling + timedelta(days=2), (
E       AssertionError: уплачено 4900.00 ₽, а выдан горизонт 395 дней на тарифе pro
        при прейскуранте 63700.00 ₽: остаток 364 дней бесплатного тарифа перенесён ЦЕЛИКОМ
E       assert datetime.datetime(2027, 9, 18, ...) <= (datetime.datetime(2026, 10, 18, ...)
        + datetime.timedelta(days=2))
tests/test_pages/test_billing_payment_errors.py:2626: AssertionError

FAILED ...::test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon
FAILED ...::test_an_upgrade_from_free_does_not_carry_the_whole_horizon
2 failed, 79 deselected, 1 warning in 2.70s
```

**Код прогона — ненулевой (`1`).** Оба теста упали на утверждении о ГОРИЗОНТЕ, а не о журнале:
утверждение об `unreadable` на коде до правки проходило — ровно как требует план, иначе тест был
бы зелен от рождения.

Третья регрессия (различимость испусканий) упала отдельно:

```
$ uv run pytest tests/test_pages/test_billing_payment_errors.py -q -k "stage"
>       assert fields.get("stage") == STAGE_PRORATE_REFUSED, (
E       AssertionError: ветка отказа не назвала себя: значение convert_remainder
        принадлежит ветке конверсии, и совпадение сделало бы два разных исхода
        неразличимыми в журнале
E       assert None == 'prorate_refused'
tests/test_pages/test_billing_payment_errors.py:2687: AssertionError
1 failed, 6 passed, 74 deselected
```

Модульная таблица упала ошибкой импорта — допустимая для неё фигура, потому что предмет
утверждения есть арифметика новой функции, а не наблюдаемое состояние:

```
E   ImportError: cannot import name 'capped_carryover' from
    'app.application.billing.subscription_period'
```

**Красный прогон зафиксирован отдельным коммитом `353c4df`** — до задачи 3 `git log --oneline -1`
показывал именно его.

Полный прогон файла на коде до правки: **3 failed, 78 passed** — ни один существующий зелёный
тест не покраснел от инфраструктурной правки помощников.

## Доказательство GREEN (задача 3)

```
$ uv run pytest tests/test_pages/test_billing_payment_errors.py \
    tests/test_application/test_subscription_period.py \
    tests/test_services/test_payment_service.py \
    tests/test_services/test_payment_concurrency.py \
    tests/test_application/test_plan_switch.py -q
161 passed, 20 warnings in 77.53s
```

Код `0`. Те же три теста, что падали в задаче 2, теперь проходят поимённо:

- `test_an_unreadable_paid_plan_price_does_not_carry_the_whole_horizon`
- `test_an_upgrade_from_free_does_not_carry_the_whole_horizon`
- `test_the_refused_branch_names_its_own_stage_in_the_journal`

Плюс девять пунктов модульной таблицы, падавших ошибкой импорта.

**Механические критерии приёмки, прогнанные дословно:**

| Критерий | Ожидание | Факт |
|---|---|---|
| `grep -c "def capped\|def bounded\|def clamped" app/application/billing/subscription_period.py` | `1` | `1` |
| `grep -c "add_one_month" app/services/payment_service.py` | `0` | `0` |
| `grep -c 'subscription_prorating_skipped' app/services/payment_service.py` | `2` | `2` |
| `grep -c 'stage="prorate_refused"' app/services/payment_service.py` | `1` | `1` |
| `grep -c 'stage="convert_remainder"' app/services/payment_service.py` | `1` | `1` |
| `grep -c 'prorate_refused' tests/test_pages/test_billing_payment_errors.py` | `>= 1` | `1` |
| `grep -c 'convert_remainder' tests/test_pages/test_billing_payment_errors.py` | `>= 1` | `1` |
| `grep -c "paid_plan_price" tests/test_pages/test_billing_payment_errors.py` | `>= 1` | `3` |
| `git diff -U0 -- tests/... \| grep -c "^-.*_confirm("` | `0` | `0` |
| `grep -c "float(" app/application/billing/subscription_period.py app/services/payment_service.py` | `0` / `0` | `0` / `0` |
| `git status --porcelain alembic/versions/` | пусто | пусто |
| `git diff --name-only -- pyproject.toml uv.lock` | пусто | пусто |
| `uv run pytest tests/test_migrations/ -q` | код `0` | `63 passed` |
| `uv run pytest ... -k "liveness"` | код `0` | `1 passed` |
| `uv run pytest tests/ -q` | код `0`, не меньше 1733 | **1745 passed** (1733 + 12) |

Две строки утверждений о различимости веток, дословно из
`tests/test_pages/test_billing_payment_errors.py`:

```python
STAGE_PRORATE_REFUSED = "prorate_refused"
STAGE_CONVERT_REMAINDER = "convert_remainder"
...
    assert fields.get("stage") == STAGE_CONVERT_REMAINDER, (   # ветка конверсии
    assert fields.get("stage") == STAGE_PRORATE_REFUSED, (     # ветка отказа
```

Присваивание базы в ветке отката, дословно из `git diff -- app/services/payment_service.py`
(строка 1076):

```python
+            base = capped_carryover(subscription.expires_at, now)
```

## Files Created/Modified

- `app/application/billing/subscription_period.py` — новая чистая функция `capped_carryover`
  (+53 строки): правило верхней границы переноса, объявленное один раз; докстринг называет
  решение владельца, цену формы числом, недопустимость исключения (5xx → цикл повторов ЮKassa) и
  то, что зажим по `now` — работа `countdown_base`, а не вторая копия правила отсчёта
- `app/services/payment_service.py` (+40 строк) — импорт `capped_carryover`; поле `stage` у обоих
  испусканий `subscription_prorating_skipped`; явное присваивание базы в ветке отката;
  комментарий у инициализации `base = subscription.expires_at`
- `tests/test_pages/test_billing_payment_errors.py` (+306 строк) — константа
  `PLAN_LIMITS_WITHOUT_PRO`; параметр перечня тарифов у `_app_settings`; новый помощник
  `_confirm_with_plan_limits`; раздел «ГЭП 1 РАУНДА 6» с тремя регрессиями и константами
  `STAGE_*`
- `tests/test_application/test_subscription_period.py` (+97 строк) — таблица решений
  `capped_carryover`: шесть тестов (девять пунктов с параметризацией)

## Decisions Made

См. раздел «Решение владельца» выше — оно снято чекпойнтом, а не выбрано исполнителем.
Исполнительские решения, принятые в рамках формы:

- **Имя функции — `capped_carryover`.** Соседка `converted_remainder` переносит остаток ПО
  ДЕНЬГАМ, новая — ПО ВРЕМЕНИ; докстринг говорит это прямо, чтобы следующий читатель не «привёл
  её в соответствие» с `converted_remainder` и не завёл вторую арифметику денег.
- **Реализация — одна строка `min(countdown_base(...), add_one_month(normalize_utc(now)))`.**
  Ни `prorated_days`, ни цен функция не касается: сюда денежный путь приходит ровно тогда, когда
  цену прочитать нельзя.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Объявление `_confirm` оставлено дословным; перечень тарифов вынесен в новый помощник

- **Found during:** Task 2
- **Issue:** `<action>` задачи 2 предписывает форму `_confirm(db, payment_id, *, plan_limits:
  str | None = None)`. Критерий приёмки той же задачи требует, чтобы
  `git diff -U0 -- tests/test_pages/test_billing_payment_errors.py | grep -c "^-.*_confirm("`
  возвращал `0`. Любая правка сигнатуры удаляет строку
  `async def _confirm(db: AsyncSession, payment_id: str = "yoo_1") -> bool:`, которая под этот
  шаблон подходит, — то есть предписанная форма механически несовместима с критерием, которым
  она же и проверяется.
- **Fix:** Общий случай вынесен в новый `_confirm_with_plan_limits(db, payment_id, *,
  plan_limits: str | None = None)` — ровно в форме, названной планом; `_confirm` сохранил
  объявление ДОСЛОВНО и стал его частным вызовом. Заявленное намерение критерия («ни один
  существующий ВЫЗОВ не изменён») соблюдено полностью: ни одна из двадцати с лишним строк
  вызова `_confirm` не тронута.
- **Files modified:** `tests/test_pages/test_billing_payment_errors.py`
- **Verification:** `grep -c "^-.*_confirm("` → `0`; 78 существующих тестов файла зелёные на
  коде до правки `app/`
- **Committed in:** `353c4df`

### 2. [Rule 2 — Missing Critical] Третья регрессия: испускание ветки ОТКАЗА называет свою ветку

- **Found during:** Task 2
- **Issue:** Критерий приёмки задачи 3 требует «по одному утверждению на каждую ветку»
  (`prorate_refused` и `convert_remainder`). Обе регрессии, названные планом, проходят веткой
  КОНВЕРСИИ; единственный существующий тест ветки отказа
  (`test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`) план запрещает трогать
  («остаётся дословно»). Без третьего теста утверждение о `prorate_refused` было бы
  тавтологическим (`!= "prorate_refused"` следует из `== "convert_remainder"`), то есть правка,
  поставившая обеим веткам одно значение, осталась бы для суиты зелёной — ровно тот способ
  отказа, который `IN-04` и называет.
- **Fix:** Добавлен `test_the_refused_branch_names_its_own_stage_in_the_journal`. Копией
  существующего теста он не является: вход другой — нечитаемая УПЛАЧЕННАЯ СУММА
  (`unreadable="amount"`, значение, которое до этого коммита не утверждал ни один тест суиты), а
  предмет проверки — значение поля `stage`.
- **Files modified:** `tests/test_pages/test_billing_payment_errors.py`
- **Verification:** тест КРАСНЫЙ на коде до правки (`assert None == 'prorate_refused'`), зелёный
  после
- **Committed in:** `353c4df` (RED), `e800209` (GREEN)
- **Расхождение с разделом `## Artifacts this phase produces`:** перечень называет два новых
  имени тестов в этом файле, фактически заведено три. Названо здесь прямо, чтобы сверка на дрейф
  не приняла третье имя за неизвестное.

---

**Total deviations:** 2 (1 blocking, 1 missing critical)
**Impact on plan:** Обе правки исполняют критерии приёмки плана, а не обходят их. Объём плана не
расширен: ни одного файла сверх `files_modified`, ни одной строки разметки, ни одной ревизии
Alembic.

## Issues Encountered

**Выравнивание диффа пришлось поправить порядком объявлений.** Первая редакция ставила
`_confirm_with_plan_limits` ПЕРЕД `_confirm`, и git выровнял хунк так, что объявление `_confirm`
показалось удалённым (`grep -c "^-.*_confirm("` → `1`), хотя строка в файле сохранена дословно.
Помощники переставлены местами — `_confirm` остался якорем хунка, счётчик вернулся к `0`.
Поведение тестов не изменилось.

## User Setup Required

None — внешних сервисов план не настраивает, переменных окружения не заводит.

## Next Phase Readiness

- **Готово к плану `05-26`:** ответ владельца `cap-one-month` записан дословно вместе с ценой в
  числах — его можно поднимать в `05-CONTEXT.md` номером решения.
- **Готово к плану `05-25`:** инвариант «`_apply_extension` не вычисляет базу сам» теперь верен
  на ВСЕХ трёх ветках — машинный гейт на объявления денежного пути строится на состоянии, а не
  на исключении.
- **Открытым остаётся** (записанный долг фазы, этим планом НЕ вменяется): второе окно потолка
  одновременных намерений, частичный уникальный индекс на незакрытое намерение, невыкаченная
  ревизия `0018`, решение D-26, применение тарифных лимитов (D-08, BILL-02), подписка на
  `payment.canceled` (D-27), мобильная проверка на 375px.
- **Три judgment-tier прохибиции фазы остаются `unresolved`** — право объявить их закрытыми
  принадлежит верификации раунда 7.
- **Настоящий платёж в тестовом магазине ЮKassa** боевым доступом не проверялся: доступа к API у
  исполнителя нет.

## Self-Check: PASSED

- Все четыре изменённых файла и сам SUMMARY существуют на диске
- Оба коммита задач присутствуют в истории: `353c4df` (RED), `e800209` (GREEN)
- `STATE.md` и `ROADMAP.md` не тронуты — их пишет оркестратор после слияния волны

---
*Phase: 05-tarify*
*Completed: 2026-08-18*
