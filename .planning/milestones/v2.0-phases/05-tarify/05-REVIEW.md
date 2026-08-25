---
phase: 05-tarify
reviewed: 2026-08-19T17:55:00Z
depth: standard
round: 9
files_reviewed: 49
files_reviewed_list:
  - alembic/versions/0017_payment_kind_and_plan.py
  - alembic/versions/0018_subscriptions_unique_user.py
  - alembic/versions/0019_payment_switch_authorized.py
  - app/application/analytics/send_analytics.py
  - app/application/billing/__init__.py
  - app/application/billing/plan_switch.py
  - app/application/billing/plan_usage.py
  - app/application/billing/subscription_period.py
  - app/config.py
  - app/constants.py
  - app/models/payment.py
  - app/models/subscription.py
  - app/pages/billing.py
  - app/pages/common.py
  - app/pages/history.py
  - app/routes/billing.py
  - app/services/billing_service.py
  - app/services/payment_service.py
  - app/static/css/app.css
  - app/templates/base.html
  - app/templates/billing/balance.html
  - app/templates/billing/includes/payment_row.html
  - app/templates/billing/includes/plan_card.html
  - app/templates/billing/includes/usage_meters.html
  - docker-compose.prod.yml
  - justfile
  - tests/test_application/declared_invariants_without_witness.txt
  - tests/test_application/test_declared_invariants.py
  - tests/test_application/test_plan_switch.py
  - tests/test_application/test_plan_usage.py
  - tests/test_application/test_subscription_period.py
  - tests/test_migrations/test_0017_payment_kind_and_plan.py
  - tests/test_migrations/test_0018_subscriptions_unique_user.py
  - tests/test_migrations/test_0019_payment_switch_authorized.py
  - tests/test_migrations/test_deploy_applies_migrations_before_serving.py
  - tests/test_migrations/test_model_matches_head.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_section.py
  - tests/test_pages/test_billing_subscription.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_planning/__init__.py
  - tests/test_planning/test_state_progress_matches_roadmap.py
  - tests/test_routes/test_billing.py
  - tests/test_routes/test_billing_webhook_proxy_headers.py
  - tests/test_routes/test_billing_webhook_source.py
  - tests/test_services/test_billing_service.py
  - tests/test_services/test_payment_concurrency.py
  - tests/test_services/test_payment_service.py
findings:
  critical: 2
  warning: 8
  info: 5
  total: 15
status: issues_found
---

# Phase 05: Отчёт код-ревью (раунд 9)

**Проверено:** 2026-08-19T17:55:00Z
**Глубина:** standard
**Файлов в объёме:** 49
**Статус:** issues_found

> Идентификаторы находок принадлежат РАУНДУ 9. Проект переназначает `CR-nn` /
> `WR-nn` / `IN-nn` в каждом раунде — ссылаться следует как на `раунд 9, CR-01`.

## Summary

Основное внимание — волне 25 (план 05-34): перенос классификации конечности и
знака ВНУТРЬ `try` в `app/services/payment_service.py::_plan_price` и его
последствия для `_apply_extension`, `capped_carryover` / `converted_remainder`
и пути вебхука.

**Правка волны 25 корректна и регрессий не вносит.** Проверено перебором классов
входа, а не чтением: для конечных цен новое тело даёт то же значение, что и
прежняя строка `return result if result is not None and result > 0 else None`
(ноль и отрицательные по-прежнему дают `None`), флаг `unreadable` своей
семантики не менял, а последняя строка функции действительно не вычисляет
ничего. Блокер раунда 8 (`CR-01`) закрыт: шесть форм нефинитной цены проходят
через настоящий маршрут уведомления и дают 200. Тавтологичное утверждение
раунда 8 (`WR-01`) снято и заменено на нацеленное в `spy.warning`.

**Но защита закрыта только на ОДНОЙ из двух величин, входящих в ту же
арифметику.** Найдены два блокера, оба воспроизведены ПРОГОНОМ настоящего
`_apply_extension`, а не выведены чтением:

1. `paid = Decimal(db_payment.amount_value)` (`:1251`) разбирается защитой ТОГО
   ЖЕ вида, что стояла у цены до волны 25, — и по той же причине не видит
   `NaN` / `Infinity`. Пять форм поднимают исключение на денежном пути. Это
   ДОСЛОВНО тот класс, ради которого волна 25 существует, на соседнем операнде
   того же деления.
2. Проверка `> 0` у цены названа достаточной, а достаточной не является:
   положительная, но МАЛАЯ цена (`"0.01"` — цена промо- или тестового платежа,
   которую оператор ставит штатно) даёт число дней за пределом `datetime` и
   `OverflowError` на уведомлении. При цене `"0.05"` исключения нет — вместо
   него срок подписки уезжает в **4066 год** за один платёж.

Оба исхода кончаются одинаково и ровно так, как запрещает докстринг того же
модуля («Исключений здесь нет и быть не может: 5xx на уведомлении запустил бы
цикл повторов ЮKassa»): 500 на `POST /api/billing/webhook`, цикл повторов при
том же конфиге, платёж `pending` навсегда при списанных деньгах.

Прохибиция фазы соблюдена: реестр принятого долга
(`declared_invariants_without_witness.txt`, 37 записей при потолке 37) волной 25
НЕ ТРОНУТ. Гейт `tests/test_planning/` на сегодняшнем дереве зелёный.
Прогон `tests/test_pages/test_billing_payment_errors.py tests/test_application/
tests/test_planning/` — 323 passed.

---

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Уплаченная сумма разбирается защитой, которую волна 25 признала недостаточной для цены

**Файл:** `app/services/payment_service.py:1248-1253`
**Классификация:** BLOCKER

**Проблема.** Волна 25 перенесла классификацию конечности внутрь защиты для
ЦЕНЫ и записала причину дословно: «`NaN` и `Infinity` суть ВАЛИДНЫЕ значения
`Decimal`, поэтому `except` вокруг разбора их не видит». Второй операнд того же
деления — уплаченная сумма — остался разобран старым способом:

```python
        price = _plan_price(subscription.plan)      # :1247 — защищено волной 25
        paid = None
        if price is not None:
            try:
                paid = Decimal(db_payment.amount_value)   # :1251
            except (InvalidOperation, TypeError, ValueError):
                paid = None                                # конечность НЕ проверяется
```

`Decimal("NaN")` разбор проходит, `paid is not None` истинно, ветка отката не
исполняется, и значение уезжает в `prorated_expiry` → `prorated_days` →
`int(Decimal(month_days) * paid / price)`
(`app/application/billing/subscription_period.py:152`), где `int()` и поднимает
исключение.

**Воспроизведение (прогон настоящего `_apply_extension`, подписка `pro` с живым
сроком, платёж `basic`, `switch_authorized=NULL`):**

```
RAISE ValueError    : cannot convert NaN to integer          <- amount_value="NaN"
RAISE OverflowError : cannot convert Infinity to integer     <- amount_value="Infinity"
RAISE OverflowError : cannot convert Infinity to integer     <- amount_value="-Infinity"
RAISE InvalidOperation                                        <- amount_value="sNaN"
RAISE OverflowError : Python int too large to convert to C int <- amount_value="1e30"
```

**Достижимость — не догадка, её объявляет сам проект.** `payments.amount_value`
— колонка `String(50)` (`app/models/payment.py:20`), схемой не ограниченная
ничем, и заполняется она значением из `PLAN_LIMITS` без единой проверки
(`app/pages/billing.py:360` → `app/services/payment_service.py:408`). Что в этой
колонке БЫВАЕТ неконечное значение, проект утверждает СВОИМ тестом:
`tests/test_pages/test_billing_section.py:830` — `NON_FINITE_AMOUNTS = ("NaN",
"Infinity", "-Infinity", "sNaN")`, а комментарий над ним (`:816-822`) называет
источник поимённо: «одна непригодная строка в конфиге цен ИЛИ В
`payments.amount_value` роняла весь раздел». То есть путь показа считает эту
форму достижимой и защищается от неё (`format_amount`,
`app/pages/common.py:283`), а денежный путь — нет.

Ветка отказа достижима без всякой гонки: строка платежа со
`switch_authorized IS NULL` (заведённая до ревизии `0019` — а боевая база
решением D-26 стоит на `0012`, то есть ВСЕ боевые строки сегодня такие) плюс
правило, отвергающее переход.

**Цена.** Необработанное исключение доезжает до `app/routes/billing.py:200-202`,
маршрут отвечает 500, ЮKassa запускает цикл повторов, конфиг и строка при
повторе те же, а `_claim_payment` откатывается вместе с транзакцией: платёж
остаётся `pending` НАВСЕГДА при списанных деньгах.

**Исправление.** Тем же приёмом и в том же месте, каким это сделано у цены
волной 25, — классификация ВНУТРИ защиты, а не после неё:

```python
            try:
                candidate = Decimal(db_payment.amount_value)
                # Конечность проверяется ЗДЕСЬ, рядом с разбором, ровно по той
                # причине, которая уже записана у `_plan_price`: `NaN` и
                # `Infinity` разбор проходят, а `int()` в `prorated_days` их не
                # переживает, и вне защиты это уже 500 на уведомлении.
                paid = candidate if candidate.is_finite() else None
            except (InvalidOperation, TypeError, ValueError):
                paid = None
```

Ветка отката (`price is None or paid is None`) при этом сработает сама и
запишет `unreadable="amount"` — поле для этого исхода уже существует
(`:1268`), то есть новой ветки заводить не нужно вовсе.

Регресс своего размера: параметризованный случай по образцу
`test_a_malformed_plan_list_does_not_break_the_notification`, но ломающий
`amount_value`, а не `PLAN_LIMITS`, и идущий через настоящий маршрут
уведомления. Набор форм уже выписан в
`tests/test_pages/test_billing_section.py:830` — брать следует его, а не
придумывать второй.

---

### CR-02: Положительная, но малая цена тарифа роняет уведомление; чуть большая — дарит подписку до 4066 года

**Файл:** `app/application/billing/subscription_period.py:152` (потребители —
`app/services/payment_service.py:1281` и `:1389`, объявление границы —
`app/services/payment_service.py:1028-1032`)
**Классификация:** BLOCKER

**Проблема.** Волна 25 объявила перечень непригодных цен закрытым: «цена,
которой нет, которая не читается как `Decimal`, которая не конечна, и которая
не больше нуля». Четвёртый член перечня — `> 0` — назван защитой от деления на
цену плана Free. Но `> 0` ограничивает ЗНАК, а не ПОРЯДОК, тогда как результат
деления уезжает прямо в `timedelta(days=...)`:

```python
return max(int(Decimal(month_days) * paid / price), 1)   # :152, верхней границы нет
```

Пороговое значение считается в одну строку: при `paid = 4900` исключение
начинается с `price < 30*4900/2.9e6 ≈ 0.05 ₽`.

**Воспроизведение (прогон настоящего `_apply_extension`, подписка `basic` 25
дней, разрешённый переход на `pro`):**

```
PLAN_LIMITS pro="0.01" -> RAISE OverflowError: date value out of range
PLAN_LIMITS pro="0.05" -> OK, expires_at = 4066-06-16
PLAN_LIMITS pro="0.10" -> OK, expires_at = 3046-08-03
PLAN_LIMITS pro="1.00" -> OK, expires_at = 2128-09-14
```

и симметрично в ветке отказа (подписка `pro` по цене `"0.01"`, платёж `basic`
1490 ₽) — `OverflowError: date value out of range`.

**Почему это не теоретический вход.** Цена `0.01 ₽` — не опечатка, а штатное
действие: ровно так проверяют боевой платёжный путь после подключения магазина,
и ровно так делают промо. `PLAN_LIMITS` — строка окружения без схемы
(`app/config.py:120-121`), правит её оператор, и НИ ОДНА проверка проекта
порядок величины не смотрит. Достаточно одного пользователя с живым сроком,
который в этот момент оплатит переход.

**Обе половины исхода плохи, и вторая хуже первой.** `OverflowError` даёт 500 на
уведомлении — тот же цикл повторов и вечный `pending`. Отсутствие исключения при
`0.05 ₽` даёт МОЛЧАЛИВУЮ запись `expires_at = 4066` в строку подписки: платёж
проведён, журнал чист, откатить это нечем, кроме правки БД руками. Это тот же
класс, что «гэп 1 раунда 5» («весь накопленный горизонт переезжает на старший
тариф»), ради которого фаза завела `capped_carryover` и форму `cap-one-month`, —
но `capped_carryover` зажимает только БАЗУ ОТСЧЁТА в ветке нечитаемой цены, а
`prorated_days` не зажат ничем ни в одной ветке.

**Замечание о защите докстрингом.** Докстринг `prorated_days` (`:141-145`)
объявляет отсутствие верхнего потолка РЕШЕНИЕМ: «Сумма больше цены действующего
плана даёт больше месяца — дни выдаются по тому, что УПЛАЧЕНО». Решение это
относится к отношению сумм ОДНОГО порядка и не может распространяться на исход
«исключение на денежном пути»: у `datetime` потолок есть независимо от того,
объявил его проект или нет. Ссылаться на этот абзац как на принятие риска
нельзя — он принимает другой риск.

**Исправление.** Ветка на выбор владельца, но обе половины обязаны закрыться
одной величиной:

```python
# app/application/billing/subscription_period.py
# ВЕРХНЯЯ ГРАНИЦА — НЕ ОТКАЗ В ДНЯХ, А ПРЕДЕЛ КАЛЕНДАРЯ. Ниже неё решение
# «потолка нет» действует дословно; выше — `datetime` кончается, и число дней
# перестаёт быть днями. Закреплено <новым регрессом>.
MAX_PRORATED_DAYS = 366 * 10

def prorated_days(paid: Decimal, price: Decimal, month_days: int) -> int:
    return min(max(int(Decimal(month_days) * paid / price), 1), MAX_PRORATED_DAYS)
```

плюс собственный ключ журнала уровня `warning` при срабатывании границы — иначе
исход «выдано 3660 дней вместо 14 700 000» станет неотличим от штатного, то есть
воспроизведёт ровно ту потерю различимости, за которую фаза уже вводила поле
`stage` (`IN-04` предыдущих раундов).

Альтернатива (или дополнение): нижняя граница на цену в `_plan_price` рядом с
`> 0`, объявленная числом с причиной. Тогда пятый член перечня непригодных цен
обязан появиться и в докстринге — сегодня он обещает закрытый перечень, который
закрытым не является.

---

## Warnings

### WR-01: Флаг `plan_limits_unreadable` по-прежнему зависит от ПОРЯДКА записей — а теперь эту зависимость закрепил новый тест

**Файл:** `app/services/payment_service.py:1003-1046`; закрепление —
`tests/test_pages/test_billing_payment_errors.py:2631-2644`
**Классификация:** WARNING (находка раунда 8 `WR-02` — НЕ ЗАКРЫТА, и приобрела
новое следствие)

**Проблема.** Флаг поднимается при встрече нечитаемого элемента, но цикл выходит
по `break` сразу после совпадения `id`. Прогон на сегодняшнем дереве:

```
'[{"id":"basic","price":NaN},...]'          -> None      error keys=[]
'["junk",{"id":"basic","price":NaN},...]'   -> None      error keys=['plan_limits_unreadable']
'[{"id":"basic","price":"1490.00"},"junk"]' -> 1490.00   error keys=[]
'["junk",{"id":"basic","price":"1490.00"}]' -> 1490.00   error keys=['plan_limits_unreadable']
```

**НОВОЕ следствие волны 25.** Тест
`test_a_malformed_plan_list_does_not_break_the_notification` теперь УТВЕРЖДАЕТ
классификацию: для форм из `PRICE_IS_NOT_FINITE_FORMS` — `assert not
unreadable_calls` («сломана ЦЕНА ОДНОГО ПЛАНА, авария окружения не
объявляется»), для остальных — обратное. Утверждение верно ровно потому, что во
всех шести формах сломанная запись стоит ПЕРВОЙ и совпадает с планом подписки.
Переставь элементы местами — и правило, которое тест выдаёт за классификацию,
поменяет ответ, не изменившись ни в одном значении. То есть закреплено не
свойство кода, а расположение литералов в константе теста.

**Исправление.** Развести две величины — «перечень пригоден» и «цена этого плана
прочитана» — и не выходить из цикла по `break`:

```python
    for plan in get_settings().parsed_plan_limits:
        if not isinstance(plan, dict):
            unreadable = True
            continue
        if plan.get("id") != plan_id or result is not None:
            continue
        ...  # без break: перечень дочитывается, флаг перестаёт зависеть от порядка
```

и добавить в `MALFORMED_PLAN_LIMITS` зеркальные формы (сломанный элемент ПОСЛЕ
искомого плана) — сегодня их нет ни одной, и именно поэтому свойство выглядит
закреплённым, не будучи закреплённым.

---

### WR-02: Нефинитная цена объявлена ШТАТНЫМ исходом, и опечатка оператора перестала оставлять след уровня `error`

**Файл:** `app/services/payment_service.py:1026-1038`, `:1262-1272`
**Классификация:** WARNING (новое следствие волны 25)

**Проблема.** До волны 25 `"price": NaN` кончался исключением; после — попадает
в ту же ветку, что и «цену этого плана прочитать нельзя», о которой комментарий
`:1034-1038` говорит: «штатный исход, а не поломка перечня, и собственного следа
поломки он не оставляет». В результате единственная запись об аварии — ключ
`subscription_prorating_skipped` уровня `warning` с полем `unreadable="price"`
(`:1262-1272`), то есть ТОТ ЖЕ след, который оставляет совершенно штатное
расхождение конфига с базой (план выпал из `PLAN_LIMITS`).

Но `"price": NaN` расхождением не является: план в перечне ЕСТЬ, и объяснить
такую цену нечем, кроме правки окружения. Ключ `plan_limits_unreadable` заведён
планом 05-28 ровно затем, чтобы «авария окружения» и «штатный исход» не
сливались — и волна 25 слила их обратно на форме, для которой этот ключ и
нужнее всего.

**Исправление.** Классифицировать нефинитную цену третьим ответом, а не вторым:

```python
                candidate = Decimal(str(plan.get("price")))
                if not candidate.is_finite():
                    # Цена ЕСТЬ, но она не число. Расхождением конфига с базой
                    # это не объясняется ничем — только правкой окружения,
                    # поэтому исход относится к аварии, а не к штатному.
                    unreadable = True
                    result = None
                else:
                    result = candidate if candidate > 0 else None
```

Утверждение теста (`PRICE_IS_NOT_FINITE_FORMS`) тогда меняет сторону — и это
правильная сторона: сегодня оно утверждает, что опечатки в деньгах быть не
должно слышно.

---

### WR-03: Гейт трекинга считает ЛЮБОЙ чекбокс планом, а его текст отказа зовёт править НЕ ТО

**Файл:** `tests/test_planning/test_state_progress_matches_roadmap.py:61-86`,
`:125-137`
**Классификация:** WARNING (находка раунда 8 `WR-03` — НЕ ЗАКРЫТА, файл волной
25 не тронут)

**Проблема.** `roadmap_plan_counts` считает планом всякую строку, чей `lstrip()`
начинается с `- [x] ` или `- [ ] `, внутри раздела `### Phase `. Понятия «план»
у разбора нет: вложенный чек-лист, критерий UAT, пункт «Blockers» станут планами,
как только окажутся под заголовком фазы. Сегодня это не срабатывает лишь по
расположению перечня фаз ВЫШЕ первого `### Phase `.

Опаснее текст отказа (`:131-137`): он утверждает, что править надо ПОЛЕ в
`STATE.md`. При ложном срабатывании эта инструкция заставит вписать в машинно
читаемое поле НЕВЕРНОЕ число — гейт, заведённый против расхождения, сам его и
внесёт. Отдельно: `ROADMAP_PATH.read_text(...)` (`:181`) не защищён — отсутствие
`.planning/` даёт `FileNotFoundError` вместо объясняющего сообщения.

**Исправление.** Сузить форму до формы плана и оставить отказ объясняющим:

```python
PLAN_LINE = re.compile(r"^- \[([ xX])\] +\d\d-\d\d-PLAN\.md\b")
```

```python
    assert ROADMAP_PATH.exists(), (
        f"источник счёта планов не найден: {ROADMAP_PATH} — гейт не сверяет, "
        "а падает, и по трассировке это неотличимо от расхождения"
    )
```

---

### WR-04: Раздел «Тарифы» отвечает 500 на том же испорченном `PLAN_LIMITS`, который вебхук уже переживает

**Файл:** `app/pages/billing.py:174`, `:229-234`, `:315-319`, `:360`, `:450-451`;
`app/application/billing/plan_usage.py:127`;
`app/templates/billing/includes/plan_card.html:57`
**Классификация:** WARNING (находка раунда 8 `WR-04` — НЕ ЗАКРЫТА; перечень
поверхностей дополнен)

**Проблема.** Планы 05-28 и 05-34 сделали тотальным ОДНО место — `_plan_price`.
Тот же вход ломает раздел целиком:

* `billing_page:174` — `plans = settings.parsed_plan_limits` поднимает
  `JSONDecodeError` на битом JSON;
* `billing_page:229-234` — `plan.get("id")` поднимает `AttributeError` на списке
  строк;
* `subscribe_to_plan:360` — `selected["price"]` поднимает `KeyError` у записи без
  цены;
* `purchase_package:450-451` — `package["name"]` / `package["count"]` поднимают
  `KeyError`;
* **новое:** `axis_percent` (`plan_usage.py:127`) сравнивает `limit <= 0` со
  значением, приехавшим из конфига КАК ЕСТЬ (`plan_axes:200-202`,
  `limits.get(key, UNLIMITED)`). Запись `{"ads": "15"}` — строка вместо числа —
  даёт `TypeError: '<=' not supported between instances of 'str' and 'int'`, то
  есть 500 на `/billing` от одной кавычки в окружении;
* **новое:** `plan_card.html:57` зовёт `plan.get('name')` у элемента перечня;
  строковый элемент даёт `UndefinedError` при отрисовке.

Докстринг `_plan_price` (`:960-972`) обосновывает единственность защиты тем,
что «денежный путь уже считает это место тотальным». Довод верен для уведомления
и неверен для раздела: правка `PLAN_LIMITS`, снявшая 500 с вебхука, оставляет
500 на `/billing` — человек не может ни увидеть тарифы, ни узнать, что
произошло.

**Исправление.** Либо один защищённый читатель конфига тарифов на проект
(`parsed_plan_limits` отдаёт пустой перечень и пишет `plan_limits_unreadable`),
либо явное решение «раздел падает намеренно», записанное там, где сегодня
записан противоположный довод. Сегодня в двух местах одного конфига действуют
две политики, и ни одна из них о другой не знает.

---

### WR-05: План, выпавший из конфига, показывается пользователю как БЕЗЛИМИТНЫЙ

**Файл:** `app/pages/billing.py:179-188`
**Классификация:** WARNING (находка раунда 8 `WR-05` — НЕ ЗАКРЫТА)

**Проблема.** Умолчание поиска — ПУСТОЙ словарь:

```python
    current_plan = next(
        (plan for plan in plans if plan.get("id") == current_plan_id), {}
    )
```

`plan_axes` читает лимиты как `limits.get(key, UNLIMITED)`
(`plan_usage.py:202`), `UNLIMITED is None`, и шаблон рисует `None` как `∞` с
подписью «без ограничений» (`usage_meters.html:30-34`). Пользователь, чей план
исчез из `PLAN_LIMITS` (или чья подписка несёт незнакомый план — путь, который
проект считает достижимым, см. `..._falls_back_to_the_whole_month` с планом
`platinum`), видит НА ЧЕТЫРЁХ ОСЯХ обещание отсутствия лимитов.

Это прямо противоположно принципу соседнего модуля: «ПЛАН, КОТОРОГО ЗДЕСЬ НЕТ,
РАНГА НЕ ПОЛУЧАЕТ, И ЭТО ОТКАЗ, А НЕ ДОГАДКА» (`app/constants.py`). Здесь
отсутствующий план получает САМУЮ ЩЕДРУЮ из возможных догадок.

**Исправление.** Отличить «записи плана нет» от «лимитов нет»:

```python
    current_plan = next(
        (plan for plan in plans if plan.get("id") == current_plan_id), None
    )
    usage = (
        await plan_axes(db, user=user, limits=current_plan, nav_counts=nav_counts)
        if current_plan is not None
        else []
    )
```

плюс подпись в разметке о том, что состав тарифа неизвестен.

---

### WR-06: `return_url` по умолчанию не является адресом

**Файл:** `app/services/payment_service.py:370`
**Классификация:** WARNING (унаследованное — строка коммита `a853082`, не правка
этой волны; названо потому, что файл заявлен в объёме и денежный путь идёт через
неё)

**Проблема.**

```python
"return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
```

`app_name` — ЧЕЛОВЕЧЕСКОЕ ИМЯ приложения, а не база адреса:
`app_name: str = "Broadcaster"` (`app/config.py:8`). Умолчание
`yookassa_return_url` — пустая строка (`app/config.py:84`), а
`docker-compose.prod.yml` эту переменную явно не задаёт (в файле выписан только
`YOOKASSA_WEBHOOK_CLIENT_IP_HEADER`, остальное приезжает из `.env` по
`env_file`). Значит выкат без `YOOKASSA_RETURN_URL` отправляет в ЮKassa
`return_url = "Broadcaster/billing"` — не адрес, а строка; ЮKassa отвергает
запрос, `create_payment` поднимает `PaymentCreationError`, и КАЖДОЕ нажатие
«Оплатить» отвечает «Не удалось начать оплату — попробуйте ещё раз через
минуту». Приём денег выключен целиком, а причина видна только по ключу
`payment_create_failed` в журнале.

**Исправление.** Умолчания, которое не может работать, быть не должно: либо
сделать `yookassa_return_url` обязательным при `yookassa_enabled` (проверка
модели `Settings`, падающая на старте), либо завести отдельный `base_url` и
собирать адрес из него. Запасной вариант из имени приложения обязан исчезнуть —
он маскирует ненастроенность под ошибку ЮKassa.

---

### WR-07: `GET /api/billing/transactions` отдаёт идентификатор платежа ЮKassa, который проект объявил не выходящим наружу

**Файл:** `app/services/billing_service.py:190`, `app/routes/billing.py:30-37`;
запись значения — `app/services/payment_service.py:628`
**Классификация:** WARNING

**Проблема.** `handle_webhook` кладёт `payment_id=yookassa_id` в строку
`balance_transactions` (`:628`), `get_transaction_history` возвращает это поле
в словаре (`:190`), а маршрут `/api/billing/transactions` отдаёт словарь
целиком. Между тем `app/templates/billing/includes/payment_row.html:15-19`
объявляет этот идентификатор «ключом подделки уведомления об оплате» и
запрещает его показ, а докстринг стерегущего теста
(`tests/test_pages/test_billing_section.py:390`) утверждает шире тела:
«Идентификатор платежа не выходит в тело ответа НИ ОДНИМ маршрутом» — при том
что утверждение проверяет РОВНО ОДИН маршрут, `GET /billing` (`:405`).

Это не эскалация привилегий (значение своё), но это ровно та форма, за которую
фаза уже платила раунды: объявление шире исполнения, и следующий читатель,
искавший покрытие по докстрингу, получает ложную уверенность.

Отдельно на том же маршруте: `limit: int = 50` и `offset: int = 0` приезжают из
строки запроса без потолка и без проверки знака, тогда как страница того же
раздела свой потолок имеет (`PAYMENT_LIST_CAP = 200`). `?limit=1000000` — запрос
без границы; `?offset=-1` — `OFFSET -1`, то есть ошибка СУБД и 500 на
PostgreSQL.

**Исправление.** Либо убрать `payment_id` из словаря
`get_transaction_history` (потребителей поля в разметке нет ни одного —
проверено `grep` по `app/templates/`), либо сузить докстринг теста до того, что
он проверяет, и завести второй случай на маршрут API. Первое дешевле и
согласуется с уже принятым решением D-24. Потолок `limit` — тем же числом
`PAYMENT_LIST_CAP`, что и на странице, отрицательный `offset` — зажать нулём.

---

### WR-08: Сокет Docker примонтирован в контейнер, терминирующий интернет-трафик

**Файл:** `docker-compose.prod.yml:92` (и `:121`)
**Классификация:** WARNING (находка раунда 8 `WR-06` — НЕ ЗАКРЫТА; унаследованное,
не правка этой волны)

**Проблема.** Сервис `web` — тот самый, который принимает
`POST /api/billing/webhook` и весь пользовательский трафик, — монтирует
`/var/run/docker.sock` на запись. Доступ к сокету Docker эквивалентен root на
ХОСТЕ: любое исполнение кода внутри `web` перестаёт быть ограниченным
контейнером.

**Исправление (работа своего размера).** Вынести управление контейнерами
воркеров в отдельный сервис (сокет остаётся только у него, `web` ходит к нему по
сети) либо поставить перед сокетом прокси с белым списком операций. Минимум на
сегодня — записать принятый риск там же, где записаны остальные («⚠️ НАЗВАННАЯ
ГРАНИЦА ЗАЩИТЫ» в `is_same_origin` — готовый образец формы).

---

## Info

### IN-01: `STATUS_PENDING` объявлен, не используется, и его значение выписано литералом

**Файл:** `app/services/payment_service.py:36` и `:407`
(находка раунда 8 `IN-01` — НЕ ЗАКРЫТА)

Константа `STATUS_PENDING = "pending"` не читается нигде, а единственное место
записи этого статуса (`create_payment`, `:407`) выписывает литерал
`status="pending"` — приём, который соседний блок того же модуля объявляет
запрещённым (`:40-44`).

**Исправление:** `status=STATUS_PENDING` на строке 407.

---

### IN-02: `AttributeError` в перечне перехвата `_plan_price` недостижим, а объяснение устарело

**Файл:** `app/services/payment_service.py:1040-1046`
(находка раунда 8 `IN-02` — НЕ ЗАКРЫТА)

Комментарий утверждает: «`AttributeError` добавлен ради формы „элемент перечня
не словарь“». Эта форма с плана 05-28 обрабатывается проверкой `isinstance`
внутри цикла (`:1007`), до всякого `plan.get`. Единственный оставшийся источник —
`for plan in <не-итерируемое>`, а он даёт `TypeError`.

**Исправление:** снять `AttributeError` либо переписать объяснение под настоящую
причину. Сегодня комментарий описывает защиту, которой нет.

---

### IN-03: Одна пустая строка между определениями верхнего уровня

**Файл:** `app/services/payment_service.py:1059`
(находка раунда 8 `IN-03` — НЕ ЗАКРЫТА; волна 25 тронула соседние строки и
расхождение сохранила)

Между `return result` (`:1058`) и `def _apply_extension` (`:1060`) стоит одна
пустая строка; остальные определения модуля разделены двумя (PEP 8, E302).

---

### IN-04: `tracking-check` не попал в перечень команд `CLAUDE.md`

**Файл:** `justfile:21-23` (потребитель — `CLAUDE.md`, §Commands)
(находка раунда 8 `IN-04` — НЕ ЗАКРЫТА)

Рецепт `tracking-check` заведён планом 05-31, но раздел «Local development» в
`CLAUDE.md` перечисляет `run`/`test`/`test-cov`/`sync`/`add`/… без него.

---

### IN-05: Идентификатор бесплатного тарифа выписан в разметке второй копией

**Файл:** `app/templates/billing/includes/plan_card.html:76`

`{% if plan.get('id') == 'free' %}` — голый литерал там, где у обработчика живёт
константа `FREE_PLAN_ID` (`app/pages/billing.py:40`), которую тот же раздел уже
умеет доводить до разметки (`free_plan_id` в контексте, `balance.html:119`
использует именно её и объясняет почему). Комментарий макроса расхождение
признаёт («то же решение, что у `FREE_PLAN_ID`»), то есть копия заведена
сознательно — но признание не мешает ей разойтись при переименовании плана.

**Исправление:** передать идентификатор параметром макроса, как уже переданы
`payments_enabled`, `switch_refused` и `refused_caption`.

---

## Проверенное и НЕ ставшее находкой

Записано, чтобы следующий раунд не перепроверял то же самое.

* **Правка волны 25 регрессий не вносит — проверено перебором классов входа.**
  Для конечных значений новое тело эквивалентно прежней строке
  `return result if result is not None and result > 0 else None`: ноль
  (`"0.00"` у плана Free) и отрицательные дают `None`, отсутствующая цена —
  `None` через `InvalidOperation` на `Decimal("None")`, ненайденный план —
  `None` без прохода по ветке. Взаимодействия «флаг `unreadable` + ранний
  `None`» нет: внутренний `except` флага не трогает, а `break` стоит там же, где
  стоял; единственная изменившаяся величина — исход для нефинитной цены (`None`
  вместо исключения), и он объявлен целью плана.
* **Блокер раунда 8 (`CR-01`) закрыт.** Шесть форм нефинитной цены и сквозной
  случай до HTTP-кода настоящего маршрута зелены.
* **Находка раунда 8 `WR-01` (тавтологичное утверждение) закрыта.** Утверждение
  переведено на `spy.warning`, снятие объяснено на месте, и добавлена проверка
  поля `stage`.
* **Находка раунда 8 `CR-02` (`just prod-hard-deploy`) в объём раунда 9 НЕ
  ВХОДИТ** — по прямому указанию инструкции ревизии: правка `justfile`
  (закомментированный `git pull`) не закоммичена и фазе не принадлежит.
  Единственная разница рабочего дерева с `HEAD` — эта строка (`git diff --stat`:
  `justfile | 2 +-`). Отмечено, а не оценено.
* **Реестр принятого долга НЕ РОС.** `declared_invariants_without_witness.txt` —
  37 записей при потолке `WITHOUT_WITNESS_CEILING = 37`
  (`tests/test_application/test_declared_invariants.py:78`); последняя правка
  файла — `04160ce` (план 05-25). Прохибиция фазы соблюдена.
* **Прогон.** `tests/test_pages/test_billing_payment_errors.py`,
  `tests/test_application/`, `tests/test_planning/` — 323 passed. Гейт трекинга
  на сегодняшнем дереве даёт согласие.
* **Ревизии `0017`…`0019` перечитаны.** Односторонность `0018` (данные) и
  `0019` (данные) объявлена в докстрингах и записана в журнал наката;
  несимметричность `downgrade` у `0017` (возврат `NOT NULL` на
  `messages_count`) названа в докстринге `:26-28` — находкой не является.
  Коррелированный подзапрос зачистки `0018` повторяет выбор приложения
  (`ORDER BY expires_at DESC`) и разрывает ничью по `id`.
* **Экранирование разметки раздела** — шаблоны билинга не используют ни `|safe`,
  ни отключение автоэкранирования; `yookassa_payment_id` в разметку не уезжает
  (в JSON уезжает — см. `WR-07`).
* **`_webhook_client_ip` берёт ПОСЛЕДНИЙ элемент заголовка** — для
  `$proxy_add_x_forwarded_for` это значение, дописанное прокси, то есть подделке
  не поддающееся; запрет на дописывающие заголовки объявлен отдельно. Не
  находка.
* **500 при отказе брокера в `history_retry`** (`app/pages/history.py`) — исход
  объявлен решением и закреплён `tests/test_pages/test_history_retry.py`.

---

_Reviewed: 2026-08-19T17:55:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Round: 9_
