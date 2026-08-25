---
phase: 05-tarify
plan: 13
subsystem: billing
tags: [upgrade-only, subscription-period, payment-webhook, tdd, gap-closure, ast-gate]

# Dependency graph
requires:
  - phase: 05-tarify (план 05-11)
    provides: "`switch_is_refused` как ЕДИНСТВЕННОЕ объявление правления рангов, ключ журнала `subscription_plan_preserved`, пять регрессий стадии применения — всё, к чему этот план добавляет недостающий вход"
  - phase: 05-tarify (план 05-10)
    provides: "Чекпойнт семантики `upgrade-only`, `PAYMENT_ERROR_MESSAGES['downgrade']`, `DOWNGRADE_CARD_CAPTION` — две пользовательские строки, чьё обещание вариант A исполняет"
  - phase: 05-tarify (план 05-01)
    provides: "`next_expiry` с правилом D-04 и прохибиция «не сжигать неистраченный остаток» — функция, относительно которой упорядочен признак живости"
  - phase: 05-tarify (план 05-08)
    provides: "`_claim_payment`, savepoint первой вставки и порядок транзакции `handle_webhook` — не тронуты этим планом ни на строку"
provides:
  - "`subscription_is_live(expires_at, now) -> bool` — ЕДИНСТВЕННОЕ объявление признака живости оплаченного срока (`app/application/billing/subscription_period.py`), читаемое ОБЕИМИ стадиями правила"
  - "`switch_is_refused(current_plan, target_plan, *, period_is_live)` — признак стал ОБЯЗАТЕЛЬНЫМ keyword-only входом без значения по умолчанию: спросить правило, не подав признак, поднимает `TypeError`"
  - "`_apply_extension` снимает признак ДО сдвига срока; порядок закреплён тестом по синтаксическому дереву `test_the_liveness_is_sampled_before_the_date_moves`"
  - "Раздел регрессий «СТАДИЯ ПРИМЕНЕНИЯ НА ИСТЁКШЕМ СРОКЕ» + помощник `_seed_expired_subscription` — ветка, не покрытая ни одним тестом до этого плана"
  - "Таблица решений признака живости в `tests/test_application/test_subscription_period.py` (11 → 20 собранных случаев)"
  - "ТРИ докстринга, совпадающих с исполняемым кодом: `_extend_subscription`, `_apply_extension`, `switch_is_refused` — плюс `subscription_is_live`, называющий ловушку порядка"
affects: [05-verification-round-4, phase-06]

# Actuals (#2632)
actuals:
  tokens: 21000
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Расхождение двух стадий по ВХОДАМ лечится не дисциплиной вызывающего, а типом сигнатуры: keyword-only параметр БЕЗ значения по умолчанию превращает забытый аргумент в `TypeError` на импорте теста"
    - "Порядок двух операторов, где первый читает величину, которую второй перезаписывает, закрепляется тестом по ТИПАМ УЗЛОВ AST с вычеркнутым докстрингом — не поиском подстроки: докстринг обязан называть оба имени, и подстрочная проверка падала бы на ВЕРНОМ коде"
    - "Числовой порог срока проверяется ДВУСТОРОННЕ (`> now+27d` И `< now+45d`): односторонняя проверка зеленеет на невыданных днях"
    - "Каждое НОВОЕ утверждение докстринга получает СВОЁ утверждение теста — урок раунда 2, где проверка на два слова зеленела при неверном поведении"

key-files:
  created: []
  modified:
    - app/application/billing/subscription_period.py
    - app/application/billing/plan_switch.py
    - app/pages/billing.py
    - app/services/payment_service.py
    - tests/test_pages/test_billing_payment_errors.py
    - tests/test_application/test_plan_switch.py
    - tests/test_application/test_subscription_period.py

key-decisions:
  - "Ответ владельца — `apply-after-expiry` (вариант A). Истёкший срок снимает отказ на ОБЕИХ стадиях; оплаченное понижение применяется. Ветка `refuse-always` НЕ взята, шесть мест отзыва обещания не тронуты"
  - "Признак живости положен в `subscription_period.py`, а не рядом с `switch_is_refused`, как предлагало ревью (CR-01): `plan_switch.py` держит AST-проверяемый инвариант «единственный импорт — `app.constants`», а признаку нужен `normalize_utc`"
  - "Признак стал ОБЯЗАТЕЛЬНЫМ аргументом, а не остался условием вызывающего: дефект был в том, что проверку МОЖНО было забыть, и умолчание вернуло бы ту же дисциплину под другим именем"
  - "Оба операнда `subscription_is_live` проходят через `normalize_utc` (перенесённая копия нормализовала только `expires_at`) — см. Deviations, Rule 2"
  - "Гард `subscribe_to_plan` схлопнут из конъюнкции двух членов в ОДИН вызов: выражения, которое могло бы разъехаться с выражением второй стадии, не остаётся вовсе"

patterns-established:
  - "Правило — это функция И ЕЁ АРГУМЕНТЫ. Объединение объявления без объединения входов скрывает расхождение ЛУЧШЕ, чем две копии: копии видны грепом, разошедшиеся входы — нет"
  - "RED предъявляется фактическим полученным значением, а не фактом падения: `assert 'pro' == 'basic'` доказывает, что воспроизведён именно тот дефект"

requirements-completed: []

coverage:
  - id: D1
    description: "«Продали, но не выдали» недостижимо: подтверждённый платёж `basic` на ИСТЁКШЕЙ подписке `pro` выдаёт `basic`, а не сохраняет `pro`"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage — RED до правки (`assert 'pro' == 'basic'`), зелёный после"
        status: pass
    human_judgment: false
  - id: D2
    description: "Срок на истёкшем периоде считается ОТ СЕГОДНЯ (D-04) — проверено двусторонним числовым порогом"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "тот же тест: `now+27d < expires_at < now+45d`"
        status: pass
    human_judgment: false
  - id: D3
    description: "Признак живости — ОБЯЗАТЕЛЬНЫЙ keyword-only вход правила без значения по умолчанию"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "test_the_rule_cannot_be_asked_without_the_liveness_term (TypeError); `inspect.signature` → KEYWORD_ONLY + Parameter.empty, код 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "Признак снимается ДО сдвига срока — проверено по ТИПАМ УЗЛОВ AST, а не поведением и не подстрокой"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "test_the_liveness_is_sampled_before_the_date_moves — RED до правки («в теле нет присваивания из вызова subscription_is_live»); AST-гейт критерия: live=0 < move=1"
        status: pass
    human_judgment: false
  - id: D5
    description: "Признак объявлен ОДИН раз и читается обеими стадиями — по объектам модулей, а не по тексту"
    requirement: BILL-05
    verification:
      - kind: other
        ref: "`p.subscription_is_live is f and s.subscription_is_live is f` → код 0; `grep -c 'def _subscription_is_live' app/pages/billing.py` → 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "На истёкшем сроке `subscription_plan_preserved` НЕ пишется — журнал не сообщает о сохранении там, где тариф выдан (T-05-65)"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "test_the_expired_period_writes_no_preserved_plan_warning — RED до правки, зелёный после"
        status: pass
    human_judgment: false
  - id: D7
    description: "ТРИ докстринга совпадают с исполняемым кодом; прежнее утверждение о сдвиге срока первым действием из файла ушло"
    requirement: BILL-05
    verification:
      - kind: other
        ref: "`'истёк' и 'subscription_is_live' в _extend_subscription.__doc__` → 0; индексы в `_apply_extension.__doc__`: 206 < 767 → 0; `'period_is_live' в switch_is_refused.__doc__` → 0; `grep -v '^\\s*#' … | grep -c 'ВСЕГДА и первым'` → 0"
        status: pass
    human_judgment: false
  - id: D8
    description: "Таблица решений признака живости покрывает `None`, прошедший, будущий, оба диалекта времени и границу «ровно сейчас»"
    requirement: BILL-05
    verification:
      - kind: test
        ref: "`--collect-only -q` по файлу: 11 (база `e0038cc`) → 20, прирост 9 при пороге 6"
        status: pass
    human_judgment: false
  - id: D9
    description: "Всё, что закрыл план 05-11, осталось закрытым, и ни один его тест не потребовал правки тела"
    requirement: BILL-05
    verification:
      - kind: other
        ref: "`git diff e0038cc -- tests/test_pages/test_billing_payment_errors.py | grep '^-' | grep -v '^---'` → НИ ОДНОЙ удалённой строки (правка чисто аддитивная)"
        status: pass
    human_judgment: false
  - id: D10
    description: "Разметка, стили, зависимости и ревизии Alembic не тронуты"
    requirement: BILL-06
    verification:
      - kind: other
        ref: "`git diff --name-only e0038cc -- app/templates/ app/static/ .planning/…/05-UI-SPEC.md` → пусто; `--stat -- pyproject.toml uv.lock` → пусто; `--name-only -- alembic/` → пусто"
        status: pass
    human_judgment: false
  - id: D11
    description: "Настоящее уведомление ЮKassa о подтверждённом платеже на ИСТЁКШЕМ сроке ведёт себя так же, как в суите"
    requirement: BILL-05
    verification: []
    human_judgment: true
    rationale: "Backstop-пункт плана (D-26). Боевого доступа к API нет, всё покрытие на моках; на проде путь недостижим — колонок `payments.kind`/`plan` там нет"
  - id: D12
    description: "Человек с истёкшим оплаченным сроком читает экран как согласованный с тем, что произойдёт после оплаты"
    requirement: BILL-05
    verification: []
    human_judgment: true
    rationale: "Backstop-пункт плана. Понятность сочетания подписи карточки, текста отказа и фактического исхода — суждение человека, а не свойство разметки"

# Metrics
duration: ~40min
completed: 2026-08-17
status: complete
---

# Phase 05 Plan 13: Признак живости оплаченного срока доходит туда, где приходят деньги — Summary

**Гэп 1 раунда 3 закрыт по существу: признак живости оплаченного срока объявлен ОДИН раз (`subscription_is_live` в `app/application/billing/subscription_period.py`), стал ОБЯЗАТЕЛЬНЫМ keyword-only входом правила `switch_is_refused` без значения по умолчанию и снимается в `_apply_extension` ДО сдвига срока — так что «продать и не выдать» стало недостижимо ни при каком состоянии подписки, а расхождение двух стадий по входам невозможно по построению (`TypeError`, а не дисциплина вызывающего).**

## Ответ чекпойнта задачи 1 (ДОСЛОВНО)

**`apply-after-expiry`**

Вариант A — «истёкший срок снимает отказ на ОБЕИХ стадиях: оплаченное понижение
применяется».

Ветка `refuse-always` НЕ взята. Перечисление ШЕСТИ мест отзыва обещания (третий
критерий приёмки задачи 1) относится ТОЛЬКО к `refuse-always` и здесь
неприменимо: вариант A исполняет обещание, а не отзывает его. Все шесть мест
проверены и оставлены НАМЕРЕННО дословно теми же:

| # | Место | Состояние |
|---|-------|-----------|
| 1 | `PAYMENT_ERROR_MESSAGES["downgrade"]` (`app/pages/billing.py`) | не тронуто |
| 2 | `DOWNGRADE_CARD_CAPTION` (`app/pages/billing.py`) | не тронуто |
| 3 | докстринг признака живости (переехал целиком, обещание «не запирает пользователя в тарифе навсегда» сохранено дословно) | сохранено |
| 4 | абзац стадии НАМЕРЕНИЯ в докстринге `switch_is_refused` | условие срока поднято на уровень ПРАВИЛА, обещание не отозвано |
| 5 | строка C2, `05-UI-SPEC.md:377` | не тронута (`git diff` по файлу пуст) |
| 6 | `MSG_DOWNGRADE` / `CAPTION_DOWNGRADE` в тестах | не тронуты |
| + | `test_a_downgrade_after_the_period_has_ended_is_accepted` | НЕ удалён, зелёный, тело не правлено |

Машинная проверка: `grep -c 'после окончания оплаченного срока' app/pages/billing.py` → **2** (порог — ровно 2, оба обещания на месте).

**Критерий «задачи 2 и 3 не начаты до ответа»:** на момент чекпойнта
`git log --oneline -1 -- app/services/payment_service.py` называл
`b752c8d docs(05-11): make the _extend_subscription docstring match the code` —
коммит НЕ этой волны.

## RED предъявлен фактическими значениями, а не фактом падения

До единой правки `app/` прогон `uv run pytest tests/test_pages/test_billing_payment_errors.py -q` завершился НЕнулевым кодом: **3 failed, 57 passed**.

| Упавший тест | Фактически получено |
|---|---|
| `test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage` | **`AssertionError: assert 'pro' == 'basic'`** — деньги за `basic` взяты, выдан `pro`. Ровно то значение, которое предсказал план |
| `test_the_expired_period_writes_no_preserved_plan_warning` | список вызовов `warning` с ключом `subscription_plan_preserved` НЕПУСТ — журнал сообщал о «сохранении тарифа» там, где тариф обязан выдаваться |
| `test_the_liveness_is_sampled_before_the_date_moves` | **`AssertionError: в теле нет присваивания из вызова subscription_is_live`** — признака живости в теле `_apply_extension` не существовало вовсе |

Второй RED-прогон, `tests/test_application/test_plan_switch.py` → **9 failed, 3 passed**, все девять с
`TypeError: switch_is_refused() got an unexpected keyword argument 'period_is_live'`.

RED зафиксирован коммитом `b1b8de7` ДО производственной правки — то есть дефект воспроизведён, а не описан.

## Фактические значения ВСЕХ машинных критериев приёмки

Каждая команда прогнана этим агентом; записаны настоящие выводы, а не ожидания.

### Задача 2

| Критерий | Порог | Фактически | Итог |
|---|---|---|---|
| `uv run pytest tests/ -q` | код 0 | **1672 passed, exit 0** (после задачи 2) | ✓ |
| `grep -c 'def subscription_is_live' app/application/billing/subscription_period.py` | == 1 | **1** | ✓ |
| `grep -c 'def _subscription_is_live' app/pages/billing.py` | == 0 | **0** | ✓ |
| `grep -c 'subscription_is_live' app/services/payment_service.py` | >= 2 | **2** | ✓ |
| `grep -c 'subscription_is_live' app/pages/billing.py` | >= 3 | **4** | ✓ |
| `inspect.signature(...)['period_is_live']` — `KEYWORD_ONLY` + `Parameter.empty` | код 0 | **OK keyword-only, no default** | ✓ |
| Вызов двумя позиционными → `TypeError` | код 0 | **OK TypeError raised** | ✓ |
| **AST-гейт порядка в `_apply_extension`** | код 0, `live < move` | **`live=0 < move=1`** | ✓ |
| Единственность по ОБЪЕКТАМ модулей (`p.… is f`, `s.… is f`) | код 0 | **OK single declaration, both stages read it** | ✓ |
| `test_the_only_import_of_the_rule_is_the_declared_plan_order` БЕЗ правки тела | зелёный | **1 passed** (тело не тронуто) | ✓ |
| `git diff --name-only -- app/templates/ app/static/` | пусто | **пусто** | ✓ |
| `git diff --stat -- pyproject.toml uv.lock` | пусто | **пусто** | ✓ |
| `git diff --name-only -- alembic/` | пусто | **пусто** | ✓ |

**AST-гейт `live=0 < move=1` — самое существенное число этой таблицы.** Индекс 0 означает, что снятие признака стоит ПЕРВЫМ оператором тела после вычеркнутого докстринга, индекс 1 — что сдвиг срока идёт сразу за ним. Проверка ищет присваивание, ЗНАЧЕНИЕ которого — вызов с этим именем, поэтому упоминание обоих имён в докстринге (чего требует задача 3) её не задевает, а перестановка двух операторов — роняет.

### Задача 3

| Критерий | Порог | Фактически | Итог |
|---|---|---|---|
| `uv run pytest tests/ -q` | код 0 | **1681 passed, exit 0** | ✓ |
| `_extend_subscription.__doc__`: `upgrade-only`, `05-01`, `subscription_plan_preserved`, `истёк` | код 0 | **OK** | ✓ |
| `_extend_subscription.__doc__` содержит `subscription_is_live` | код 0 | **OK** | ✓ |
| **`_apply_extension.__doc__`: оба имени И их ПОРЯДОК** | `index(live) < index(next_expiry)` | **206 < 767** | ✓ |
| `grep -v '^\s*#' app/services/payment_service.py \| grep -c 'ВСЕГДА и первым'` | == 0 | **0** | ✓ |
| `switch_is_refused.__doc__` содержит `period_is_live` | код 0 | **OK** | ✓ |
| `subscription_is_live.__doc__` содержит `next_expiry` | код 0 | **OK** | ✓ |
| `test_the_switch_semantics_are_named_in_the_place_that_moves_the_date` зелёный с новым утверждением | зелёный | **зелёный**, два новых утверждения | ✓ |
| `--collect-only -q` по `test_subscription_period.py` | прирост >= 6 | **11 → 20, прирост 9** | ✓ |
| Вариант A: `git diff --name-only e0038cc -- app/templates/ 05-UI-SPEC.md` | пусто | **пусто** | ✓ |
| Вариант A: `grep -c 'после окончания оплаченного срока' app/pages/billing.py` | == 2 | **2** | ✓ |
| `graphify update .` | успешно | **exit 0**, 8310 узлов / 17099 рёбер / 488 сообществ | ✓ |
| `git diff --stat e0038cc -- pyproject.toml uv.lock`; `--name-only -- alembic/` | пусто | **пусто / пусто** | ✓ |

Число собранных случаев базы (11) получено не на глаз: файл из `e0038cc` выложен под временным именем в `tests/test_application/`, собран pytest-ом и удалён — иначе «прирост» считался бы от предположения.

## Performance

- **Duration:** ~40 мин (из них ~34 мин — два полных прогона суиты по 17 мин)
- **Tasks:** 3 (1 `checkpoint:decision`, снятый владельцем до запуска; 1 `tdd`; 1 `auto tdd`)
- **Commits:** 4
- **Files modified:** 7 (4 в `app/`, 3 в `tests/`); созданных файлов кода нет
- **Тесты:** 1665 → **1681** (+16: 4 поведенческих регрессии + AST-гейт порядка + 2 в `plan_switch` + 9 случаев таблицы решений)

## Accomplishments

- **Блокер денежного пути закрыт поведенчески, а не декларативно.** Подписка `pro` со сроком, истёкшим вчера, плюс подтверждённый платёж `basic` теперь дают РОВНО ОДНУ строку `subscriptions` с `plan == "basic"` и сроком от сегодня. Асимметрия, названная отчётом дефектной (пользователь БЕЗ строки подписки получал `basic`, пользователь с ИСТЁКШЕЙ строкой получал `pro`), устранена: одно намерение — один исход.
- **Расхождение стадий по входам стало невозможным ПО ПОСТРОЕНИЮ.** `period_is_live` — keyword-only без значения по умолчанию; вызов двумя позиционными аргументами поднимает `TypeError`, и это закреплено именованным тестом. Умолчание вернуло бы дисциплину вызывающего — ровно ту, на которой стадии и разошлись (T-05-64).
- **Ловушка порядка поймана машиной.** Признак, снятый ПОСЛЕ `next_expiry`, всегда отвечал бы «живо» и восстановил бы блокер молча. Порядок держит `test_the_liveness_is_sampled_before_the_date_moves` — разбор по ТИПАМ УЗЛОВ AST с вычеркнутым докстрингом (T-05-63).
- **Приватной копии признака больше нет.** `_subscription_is_live` удалена из `app/pages/billing.py` вместе с комментарным блоком, объяснявшим, почему она не переехала: объяснение перестало быть верным. Та же мера, что план 05-11 применил к сравнению рангов, применена ко второму входу того же правила.
- **Гард `subscribe_to_plan` схлопнут в ОДИН вызов.** Конъюнкции из двух членов, где средний член можно забыть, не осталось вовсе — ни в гарде, ни в множестве `refused_plan_ids`.
- **ТРИ докстринга приведены к исполняемому коду, включая тот, который правка задачи 2 сделала ложным.** `_apply_extension` объявлял сдвиг срока ПЕРВЫМ действием тела; после задачи 2 это стало неправдой, и починка соседнего докстринга без этого открыла бы соседнее направление — ровно то, в чём отчёт раунда 3 упрекнул план 05-11. Прежнее утверждение из файла ушло (`grep` → 0).
- **Ветка истёкшего срока на стадии применения перестала быть непокрытой.** До этого плана КАЖДЫЙ тест раздела стадии применения сеял ЖИВУЮ подписку — потому суита из 1665 тестов и оставалась зелёной при работающем блокере. Новый раздел с `_seed_expired_subscription` называет это отличие в заголовке.
- **Оба диалекта времени закрыты таблицей решений.** naive (SQLite) и aware (PostgreSQL) значения одного момента дают ОДИН ответ; граница «ровно сейчас» — `False` (строгое сравнение).

## Task Commits

1. **Task 1 (checkpoint:decision, gate=blocking): решение владельца** — `6852b8c` (docs), запись ответа `apply-after-expiry` дословно, идентификатором варианта
2. **Task 2 RED (tdd, gate RED): падающие регрессии истёкшего срока** — `b1b8de7` (test), 2 файла, +234/−4 — 3 failed в `test_billing_payment_errors.py`, 9 failed в `test_plan_switch.py`
3. **Task 2 GREEN: признак живости — обязательный вход правила** — `94ca261` (feat), 4 файла, +100/−40
4. **Task 3: три докстринга и таблица решений** — `b9bccf8` (docs), 3 файла, +138/−6

REFACTOR-коммита нет: после GREEN чистить было нечего — правка задачи 2 сводится к переносу объявления, одному новому оператору и трём переписанным вызовам.

**Метаданные плана:** коммит этого SUMMARY (`docs(05-13): complete the liveness-term gap closure plan`).

## Files Created/Modified

- `app/application/billing/subscription_period.py` — новая публичная `subscription_is_live`; докстринг модуля называет, ПОЧЕМУ признак лежит здесь, а не рядом с `switch_is_refused` (инвариант единственного импорта `plan_switch.py`); докстринг функции называет ловушку порядка относительно `next_expiry` и строгость сравнения на границе.
- `app/application/billing/plan_switch.py` — сигнатура получила `*, period_is_live: bool`; первым оператором тела `if not period_is_live: return False` (сравнение рангов до него не доходит); докстринг поднял условие срока на уровень ПРАВИЛА и оставил различием стадий только ЦЕНУ отказа. Инвариант «единственный импорт — `app.constants`» не ослаблен.
- `app/pages/billing.py` — `_subscription_is_live` и комментарный блок удалены; импорт `subscription_is_live`; оба вызова подают признак аргументом; гард схлопнут в один вызов. Пользовательские строки не тронуты.
- `app/services/payment_service.py` — импорт `subscription_is_live`; снятие признака ПЕРВЫМ оператором `_apply_extension` с комментарием, называющим ловушку прямо; два докстринга переписаны. Ветка первой вставки, savepoint, порядок транзакции и ключ `subscription_plan_preserved` не тронуты; оба вызова `_apply_extension` (`:469`, `:498`) получают признак одинаково, потому что он снимается ВНУТРИ функции.
- `tests/test_pages/test_billing_payment_errors.py` — **правка чисто аддитивная, ни одной удалённой строки**: раздел «СТАДИЯ ПРИМЕНЕНИЯ НА ИСТЁКШЕМ СРОКЕ», помощник `_seed_expired_subscription`, четыре поведенческих теста, AST-тест порядка, два новых утверждения в тесте докстринга.
- `tests/test_application/test_plan_switch.py` — четыре существующих вызова получили `period_is_live=True` (правка тел НАМЕРЕННАЯ: сигнатура изменилась); два новых теста — `TypeError` и снятие отказа признаком `False`.
- `tests/test_application/test_subscription_period.py` — таблица решений признака живости: `None`, прошедший/будущий вплотную к границе, оба диалекта времени, граница «ровно сейчас», naive-`now`.

## Decisions Made

- **`apply-after-expiry`** — решение владельца, исполнено ЦЕЛИКОМ: код, тесты, докстринги и пользовательские строки согласованы, смешанного состояния «продажа разрешена — применение отказано» не осталось ни в одной ветке.
- **Место объявления — `subscription_period.py`, вопреки букве CR-01 ревью.** Предложение ревью верно по СУТИ и неверно по МЕСТУ: `plan_switch.py` держит AST-проверяемый инвариант единственного импорта, а признаку нужен `normalize_utc`. `subscription_period.py` уже импортирует его, уже владеет `next_expiry` (функцией, порядок относительно которой и есть ловушка) и уже импортируется обеими стадиями.
- **Признак — аргумент, а не условие вызывающего.** Ценой стала правка четырёх строк существующих тестов, и она осознанная: тела менялись потому, что СИГНАТУРА изменилась намеренно, а не «заодно».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая критичная функциональность] Оба операнда `subscription_is_live` проходят через `normalize_utc`**

- **Найдено при:** задаче 2, шаг 2 (перенос объявления).
- **Что не так:** переносимая копия из `app/pages/billing.py:99-112` нормализовала только `expires_at`, а `now` сравнивала как есть (`normalized > now`). Пока звали её два места, оба передававшие `datetime.now(timezone.utc)`, это было безопасно. Но у функции появился ТРЕТИЙ читатель — `_apply_extension`, который получает `now` параметром `handle_webhook`, а соседняя `next_expiry` того же модуля нормализует ОБА операнда и покрыта тестом `test_next_expiry_accepts_a_naive_now`. Naive-`now` поднял бы `TypeError` на денежном пути.
- **Исправление:** `normalized > normalize_utc(now)`; ловушка закреплена тестом `test_a_naive_now_does_not_break_the_liveness_term` (зеркало теста `next_expiry`).
- **Файлы:** `app/application/billing/subscription_period.py`, `tests/test_application/test_subscription_period.py`.
- **Коммиты:** `94ca261`, `b9bccf8`.
- **Отношение к плану:** план говорил «логика верна и не переписывается». Логика сравнения действительно не переписана — добавлена одна нормализация, приводящая функцию к контракту соседней функции ТОГО ЖЕ модуля.

**2. [Rule 1 — баг, пойманный собственным тестом] Слово «истёк» стояло в докстринге только ЗАГЛАВНЫМИ**

- **Найдено при:** задаче 3, первом прогоне.
- **Что не так:** новый абзац `_extend_subscription` называл исход фразами «КОГДА ОПЛАЧЕННЫЙ СРОК УЖЕ ИСТЁК» и «с ИСТЁКШЕЙ строкой» — заглавными. Критерий приёмки и новое утверждение теста ищут подстроку `истёк` в нижнем регистре, поэтому `test_the_switch_semantics_are_named_in_the_place_that_moves_the_date` упал.
- **Исправление:** абзац переформулирован — «Когда оплаченный срок истёк, отказ снимается на ОБЕИХ стадиях». Тест не ослаблялся и порог не понижался.
- **Файл:** `app/services/payment_service.py`. **Коммит:** `b9bccf8`.
- **Почему записано:** это ровно тот случай, ради которого урок «каждое новое утверждение докстринга получает своё утверждение теста» и применялся. Утверждение поймало реальное расхождение между обещанием критерия и текстом файла на первом же прогоне.

### Границы объёма — соблюдены

Ни одного пакета (`pyproject.toml`/`uv.lock` — пустой дифф), ни одной ревизии Alembic, ни строки в `app/templates/` и `app/static/`, ни правки `05-UI-SPEC.md`. `_active_subscription`, `handle_webhook`, savepoint первой вставки и порядок транзакции плана 05-08 не тронуты. Сигнатура `_apply_extension` не расширена — `payment_data` в неё по-прежнему не передаётся (T-05-68).

**Итого отклонений:** 2 автоисправления (Rule 2 и Rule 1), оба внутри изменяемых планом файлов. Объём не расширен, архитектурных решений (Rule 4) не потребовалось.

## Issues Encountered

- **Полный прогон суиты идёт ~17 минут** и дважды превышал таймаут переднего плана; оба раза запускался фоном с записью вывода в файл. Оба завершились кодом 0 (1672 и 1681).
- **Число собранных случаев базы пришлось измерять, а не оценивать.** `pytest --collect-only` по файлу из `git show`, выложенному вне дерева тестов, падает на сборке (rootdir/conftest). Файл выложен под временным именем в `tests/test_application/`, собран (11) и удалён; `git status` после удаления чист.
- **`graphify update .` записал только в `graphify-out/`**, который в worktree не отслеживается git; после его прогона `git status` не показал новых файлов, коммитить нечего.

## Известные заглушки

Нет. Ни одного `TODO`/`FIXME`, ни одного `skip`/`xfail`, ни одного невыполненного `<verify>`: обе автоматические проверки задач 2 и 3 прогнаны, полная суита прогнана дважды, все машинные критерии приёмки исполнены с записанными фактическими значениями.

## Threat Flags

Новой поверхности не добавлено; из `<threat_model>` плана исполнены митигации:

- **T-05-62** (продали и не выдали на истёкшем сроке) — закрыт поведенчески, регрессия падала до правки.
- **T-05-63** (ловушка порядка) — закрыт AST-гейтом `live=0 < move=1` плюс абзацами в двух докстрингах.
- **T-05-64** (спросить правило без признака) — закрыт keyword-only параметром без умолчания и тестом на `TypeError`.
- **T-05-65** (ложный `subscription_plan_preserved`) — закрыт тестом отсутствия ключа на этом пути.
- **T-05-66** (`is_active` никогда не снимается) — решение о плане больше не опирается на `is_active` вовсе; остаточная часть распоряжена плану 05-14, здесь не чинилась намеренно.
- **T-05-67** (циклический импорт) — не возник: `test_the_only_import_of_the_rule_is_the_declared_plan_order` зелёный без правки тела.
- **T-05-68** (`plan` из ТЕЛА уведомления) — сигнатура `_apply_extension` не расширена, все три входа решения из своей базы.
- **T-05-SC** — ни одного пакета не установлено, дифф `pyproject.toml`/`uv.lock` пуст.

## Перенесённые человеческие проверки — задачами НЕ становились

Дословно из `<verification>` плана, ни один пункт не автоматизирован:

- **Мобильная ширина 375px** (`behavior_unverified: 1`) — браузерного и e2e-харнесса нет, разметка планом не тронута ни на строку.
- Настоящий платёж в тестовом магазине ЮKassa (D-26) и настоящее уведомление на истёкшем сроке — боевого доступа к API нет, на проде путь недостижим (колонок `payments.kind`/`plan` там нет).
- Первое настоящее уведомление после выката проходит гард источника (backstop плана 05-07).
- Статус «отклонён» у отменённого платежа (D-27) — состав событий задаётся вне репозитория.
- Читаемость формулировок «в обработке» и отказа оплаты — суждение человека.
- **Прохибиция `BILL-05`/fairness остаётся `unresolved`/`judgment`:** оба денежных направления теперь закрыты (действующий срок — планом 05-11, истёкший — этим), но половина «слово пользователю ДО нажатия кнопки» судится человеком. Вариант A делает сегодняшнее обещание правдой — достаточность формулировки оценивает владелец. Флаг `unverified-prohibition — human review recommended` сохраняется.
- **Прохибиция `BILL-05`/autonomy остаётся `unresolved`/`judgment`:** при варианте A пользователь уйти вниз МОЖЕТ, и сегодняшний текст стал правдой; достаточно ли этого сказано — суждение владельца.
- **Прохибиция `BILL-06`/transparency остаётся `unresolved`/`judgment`:** после закрытия гэпа 1 она вернулась к ОДНОМУ пути достижения вместо двух (действующий старший тариф плюс платёж младшего — выбранная семантика, а не дефект). Интерфейсной работы план не вёл.
- Три требования фазы (`BILL-05`, `BILL-06`, `BILL-07`) остались `unclassified` у зонда краевых случаев — лексикон классификатора английский, требования написаны по-русски. Наблюдение об инструменте, а не основание снять строку.

## User Setup Required

Нет — новых переменных окружения, ключей конфига, миграций и внешних настроек план не вводит.

## Next Phase Readiness

- **Все четыре пункта `missing:` гэпа 1 закрыты:** признак подаётся в правило на стадии применения тем же способом, что на стадии намерения (задача 2); регрессия истёкшего срока существует и падала до правки (`'pro' == 'basic'`, задача 2); три докстринга описывают исполняемый код, включая докстринг самой `_apply_extension` (задача 3); решение владельца принято чекпойнтом и исполнено целиком (задача 1). Ни один не отложен.
- **Требования НЕ перемечены** и `requirements-completed` оставлен пустым — тем же основанием, что у плана 05-12: `Complete` возвращает повторная верификация, а не план, закрывающий гэп.
- **Открытым остаётся:** остаточная часть T-05-66 (`Subscription.is_active` не снимается по сроку — распоряжена плану 05-14); блокирующий вызов SDK (ревью раунда 2, CR-02); типизированная запись `PLAN_LIMITS` (`WR-10`/`WR-07`); очередь невыкаченных ревизий `0013`…`0018` при боевой базе на `0012`; `graphify update .` в главном каталоге после вливания ветки.
- **STATE.md и ROADMAP.md этим агентом НЕ трогались** — режим worktree, оркестратор пишет их централизованно после волны.

## Self-Check: PASSED

Файлы (7/7 на месте, все изменения закоммичены):
- FOUND: `app/application/billing/subscription_period.py`
- FOUND: `app/application/billing/plan_switch.py`
- FOUND: `app/pages/billing.py`
- FOUND: `app/services/payment_service.py`
- FOUND: `tests/test_pages/test_billing_payment_errors.py`
- FOUND: `tests/test_application/test_plan_switch.py`
- FOUND: `tests/test_application/test_subscription_period.py`

Коммиты (4/4 в истории ветки `worktree-agent-af27b3dd7af324470`):
- FOUND: `6852b8c` — `docs(05-13): record owner checkpoint answer apply-after-expiry`
- FOUND: `b1b8de7` — `test(05-13): add failing regressions for the expired period at the apply stage`
- FOUND: `94ca261` — `feat(05-13): make the liveness term a mandatory input of the switch rule`
- FOUND: `b9bccf8` — `docs(05-13): bring three docstrings in line with the code they describe`

Гейты TDD (плановый тип `tdd`): RED-коммит `b1b8de7` (`test(...)`) → GREEN-коммит `94ca261` (`feat(...)`) → REFACTOR отсутствует намеренно. Последовательность соблюдена; RED предъявлен фактическим значением, а не фактом падения.

Итоговые прогоны:
- `uv run pytest tests/ -q` → **1681 passed, exit 0**
- `<verify>` задачи 2 (5 файлов) → **109 passed**
- `<verify>` задачи 3 (3 файла) → **92 passed**

Фаза `complete` этим агентом НЕ помечена и верификатор НЕ запускался: гейты фазы принадлежат оркестратору.

---
*Phase: 05-tarify*
*Completed: 2026-08-17*
