---
phase: 05-tarify
reviewed: 2026-08-19T12:27:43Z
depth: standard
round: 8
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
  warning: 6
  info: 4
  total: 12
status: issues_found
---

# Phase 05: Отчёт код-ревью (раунд 8)

**Проверено:** 2026-08-19T12:27:43Z
**Глубина:** standard
**Файлов в объёме:** 49
**Статус:** issues_found

> Идентификаторы находок принадлежат РАУНДУ 8. Проект переназначает `CR-nn` / `WR-nn` / `IN-nn` в каждом раунде, поэтому ссылаться на них следует как на `раунд 8, CR-01` и т. д.

## Summary

Основное внимание уделено поверхностям, тронутым волной закрытия гэпов раунда 7:
`_plan_price` в `app/services/payment_service.py` (план 05-28), новый гейт
`tests/test_planning/` и рецепт `tracking-check` в `justfile` (план 05-31).
Документарная правка 05-33 (три абзаца докстрингов) прочитана и расхождений с
исполняемым кодом не даёт — за исключением одного устаревшего обоснования
(`IN-02`).

Найдено две блокирующие находки, и обе воспроизведены прогоном, а не выведены
чтением.

1. Защита `_plan_price`, ради которой существует план 05-28, ПРОПУСКАЕТ пятую
   форму отказа — НЕФИНИТНУЮ цену (`NaN` / `Infinity`). Финальное сравнение
   `result > 0` стоит ВНЕ `try`, а `Decimal('NaN') > 0` поднимает
   `InvalidOperation`. Исход — ровно тот, который план объявляет закрытым: 500 на
   уведомлении ЮKassa, цикл повторов и платёж `pending` навсегда при списанных
   деньгах. Тот же класс дефекта уже был найден и починен в этом же проекте на
   `format_amount` (`app/pages/common.py:270-284`, план 05-09), и его собственный
   докстринг называет причину дословно: «`NaN` и `Infinity` — валидные значения
   `Decimal`, и `except` вокруг разбора их не видит».

2. Рецепт `just prod-hard-deploy` в `justfile` СЕГОДНЯ НЕ ДЕЛАЕТ НИЧЕГО и
   возвращает код 0. Закомментированная строка `#git pull && \` заканчивается
   продолжением строки, а `just` склеивает продолжения ДО передачи оболочке —
   в результате весь рецепт становится одним комментарием оболочки.

Дополнительно: закрепляющий регресс плана 05-28 содержит утверждение, которое не
может покраснеть НИКОГДА (`WR-01`), — то есть половина заявленного свойства не
закреплена ничем, хотя выглядит закреплённой.

Гейт `tests/test_planning/` на сегодняшнем дереве даёт согласие
(derived `(81, 81)` = recorded `(81, 81)`), негативные контроли настоящие, реестр
принятого долга (`declared_invariants_without_witness.txt`, 37 записей при потолке
37) НЕ РОС. Прохибиция фазы соблюдена.

---

## Critical Issues

### CR-01: Нефинитная цена в `PLAN_LIMITS` роняет обработчик уведомления ЮKassa

**Файл:** `app/services/payment_service.py:1023` (защита — `:984-1022`)
**Классификация:** BLOCKER

**Проблема.** Возврат написан так:

```python
    except (InvalidOperation, TypeError, ValueError, AttributeError):
        unreadable = True

    if unreadable:
        logger.error("plan_limits_unreadable", plan_id=plan_id)

    return result if result is not None and result > 0 else None   # ← строка 1023, ВНЕ try
```

`Decimal("NaN")` — ВАЛИДНОЕ значение, и `Decimal(str(...))` его принимает без
исключения. Исключение поднимает СРАВНЕНИЕ `result > 0`, которое стоит ВНЕ `try`:

* `"price": NaN` либо `"price": "nan"` → `InvalidOperation` на строке 1023;
* `"price": Infinity` → сравнение проходит (`Infinity > 0` истинно), цена уезжает
  в `converted_remainder` → `prorated_days` → `int(Decimal('Infinity'))` →
  `OverflowError`.

`json.loads` принимает голые литералы `NaN`, `Infinity` и `-Infinity` ПО
УМОЛЧАНИЮ, поэтому форма достигается штатной правкой переменной окружения
оператором — тем же путём, каким достигаются четыре формы, закреплённые
`test_a_malformed_plan_list_does_not_break_the_notification`.

**Воспроизведение (прогон, не рассуждение).** Вызов настоящего `_apply_extension`
с живой подпиской `basic`, платежом `pro` и `switch_authorized=True`:

```
RAISE InvalidOperation  <- [{"id":"basic","price":NaN},{"id":"pro","price":"4900.00"}]
RAISE InvalidOperation  <- [{"id":"basic","price":"nan"},{"id":"pro","price":"4900.00"}]
RAISE OverflowError     <- [{"id":"basic","price":Infinity},{"id":"pro","price":"4900.00"}]
```

**Цена.** Необработанное исключение доезжает до `app/routes/billing.py:200-202`,
маршрут отвечает 500, ЮKassa запускает цикл повторов, конфиг при повторе тот же —
и `_claim_payment` откатывается вместе с транзакцией, то есть платёж остаётся
`pending` НАВСЕГДА при списанных деньгах. Это дословно тот исход, который
докстринг `_plan_price` (`:938-947`) объявляет недостижимым, и тот, который
докстринг регресса называет «класс отказа, уже стоивший фазе находки `WR-04`
раунда 2».

**Исправление.** Проверка конечности обязана стоять ВНУТРИ той же защиты, что и
разбор, — ровно тем приёмом, каким это уже сделано в `format_amount`
(`app/pages/common.py:283`, «ПРОВЕРКА КОНЕЧНОСТИ СТОИТ ПОСЛЕ РАЗБОРА, А НЕ ВМЕСТО
НЕГО»):

```python
            try:
                candidate = Decimal(str(plan.get("price")))
                # Конечность проверяется ЗДЕСЬ, рядом с разбором: `NaN` и
                # `Infinity` разбор проходят, а сравнение `> 0` поднимает
                # InvalidOperation, и вне try оно уже не защищено ничем.
                result = candidate if candidate.is_finite() else None
            except (InvalidOperation, TypeError, ValueError):
                result = None
            break
```

Регресс, который сегодня краснеет: две новые формы в `MALFORMED_PLAN_LIMITS`
(`tests/test_pages/test_billing_payment_errors.py:2411-2417`) —
`("nan_price", '[{"id":"basic","price":NaN},{"id":"pro","price":"4900.00"}]')` и
`("infinite_price", '[{"id":"basic","price":Infinity},{"id":"pro","price":"4900.00"}]')`.
Формы обязаны идти через настоящий обработчик уведомления, как и четыре уже
закреплённые.

---

### CR-02: `just prod-hard-deploy` не исполняет НИ ОДНОЙ команды и рапортует успех

**Файл:** `justfile:104-113` (строка 105)
**Классификация:** BLOCKER

**Проблема.** В рабочем дереве стоит:

```make
prod-hard-deploy:
    #git pull && \
    docker compose -f docker-compose.prod.yml build --no-cache && \
    ...
```

`just` склеивает строки, оканчивающиеся `\`, В ОДНУ ещё ДО передачи оболочке.
Получившаяся единственная строка начинается с `#`, то есть весь рецепт становится
комментарием оболочки. Проверено настоящим `just` (`/usr/bin/just`) на
минимальном воспроизведении:

```
$ just demo
#echo one && echo two && echo three
exit=0
```

Ни `echo` не исполнился, код возврата — 0.

**Цена.** Оператор, запустивший `just prod-hard-deploy`, получает МОЛЧАЛИВЫЙ
успех: образы не пересобираются, воркеры не останавливаются, `up -d` не
вызывается. На фазе, чья главная неисполненная работа — выкатка очереди ревизий
`0017`…`0019` (D-26), команда выката, тихо рапортующая успех, есть худшая из
возможных форм отказа: следующий шаг («ревизии применены, `entrypoint.sh` довёл
очередь») будет считаться сделанным, не будучи сделанным.

Соседний `prod-deploy` (`:116-125`) не тронут и `git pull` сохраняет, поэтому два
рецепта одного назначения сегодня расходятся не флагом сборки, а тем, что один из
них не работает вовсе.

**Замечание об учёте.** Правка НЕ ЗАКОММИЧЕНА — она видна только в рабочем дереве
(`git diff justfile`). Это не снимает находки: файл заявлен в объёме ревизии, а
незакоммиченная правка боевого выката либо уезжает в коммит следующим шагом, либо
не должна лежать в дереве вовсе.

**Исправление.** Либо вернуть строку, либо снять её целиком вместе с
продолжением — но НЕ оставлять комментарий, оканчивающийся `\`:

```make
# Hard deploy to prod environment (build --no-cache and deploy)
# ⚠️ git pull снят намеренно: <причина>. Комментировать строку с продолжением
# `\` нельзя — just склеивает продолжения, и весь рецепт становится
# комментарием оболочки.
prod-hard-deploy:
    docker compose -f docker-compose.prod.yml build --no-cache && \
    ...
```

Страховочная сетка своего размера: тест по образцу
`tests/test_migrations/test_deploy_applies_migrations_before_serving.py`,
утверждающий, что ни одна строка рецептов выката в `justfile` не является
комментарием, оканчивающимся продолжением.

---

## Warnings

### WR-01: Утверждение регресса 05-28 не может покраснеть никогда

**Файл:** `tests/test_pages/test_billing_payment_errors.py:2487-2493`
**Классификация:** WARNING

**Проблема.** Второе утверждение теста
`test_a_malformed_plan_list_does_not_break_the_notification` ищет ключ
`subscription_prorating_skipped` в `spy.error.call_args_list`. Но этот ключ
пишется УРОВНЕМ `warning` (`app/services/payment_service.py:1227` и `:1321`), а не
`error`. Значит `assert not any(...)` истинно ТОЖДЕСТВЕННО — при любом поведении
кода, включая полностью сломанное.

Хуже: свойство, которое утверждение якобы стережёт, на сегодняшнем дереве НЕ
ВЫПОЛНЯЕТСЯ в том смысле, в каком его формулирует текст отказа. Прогон настоящего
`_apply_extension` на форме `null` даёт:

```
ERROR   calls: ['plan_limits_unreadable', 'plan_limits_unreadable']
WARNING calls: ['subscription_prorating_skipped']
```

То есть авария окружения пишет ОБА ключа. Правильно нацеленное утверждение
(`spy.warning`) покраснело бы немедленно.

**Исправление.** Решить, что именно закрепляется, и нацелить утверждение туда:

```python
    # Оба ключа ДОПУСТИМЫ и означают разное: `plan_limits_unreadable` — авария
    # окружения, `subscription_prorating_skipped` — ветка отката. Закрепляется
    # то, что первый ключ ЕСТЬ, а не то, что второго нет.
    assert not any(
        call.args and call.args[0] == "plan_limits_unreadable"
        for call in spy.warning.call_args_list
    ), "авария окружения записана уровнем warning — в потоке предупреждений она теряется"
```

Если же замысел был именно «второго ключа быть не должно», то краснеть обязан
КОД, а не тест: ветка отката тогда не имеет права писать
`subscription_prorating_skipped` при поднятом флаге `unreadable`.

---

### WR-02: `plan_limits_unreadable` зависит от ПОРЯДКА записей в `PLAN_LIMITS`

**Файл:** `app/services/payment_service.py:986-1004`
**Классификация:** WARNING

**Проблема.** Флаг `unreadable` поднимается при встрече нечитаемого элемента, но
цикл выходит по `break` сразу после совпадения `id`. Значит поломанный элемент,
стоящий ПОСЛЕ искомого плана, не виден вовсе, а стоящий ДО — поднимает аварийный
ключ, хотя цена прочитана успешно. Прогон:

```
'["junk", {"id":"basic","price":"1490.00"}]' -> 1490.00  errors: ['plan_limits_unreadable']
'[{"id":"basic","price":"1490.00"}, "junk"]' -> 1490.00  errors: []
```

Один и тот же испорченный конфиг даёт либо запись уровня `error`, либо тишину — в
зависимости от порядка ключей, который оператор не контролирует осмысленно. Ключ,
чей смысл объявлен как «перечень сломан ЦЕЛИКОМ» (`:1014-1020`), при этом
срабатывает на успешном чтении цены.

**Исправление.** Развести две величины — «перечень пригоден» и «цена этого плана
прочитана»: проверять пригодность перечня ОТДЕЛЬНЫМ проходом до поиска, либо не
выходить по `break`, а дочитывать перечень до конца и брать первое совпадение.
Второе дешевле:

```python
    for plan in get_settings().parsed_plan_limits:
        if not isinstance(plan, dict):
            unreadable = True
            continue
        if plan.get("id") != plan_id or result is not None:
            continue
        ...  # без break: перечень дочитывается, флаг перестаёт зависеть от порядка
```

---

### WR-03: Гейт трекинга считает ЛЮБОЙ чекбокс планом, а его текст отказа зовёт править НЕ ТО

**Файл:** `tests/test_planning/test_state_progress_matches_roadmap.py:61-86`, `:131-137`
**Классификация:** WARNING

**Проблема.** `roadmap_plan_counts` считает планом всякую строку, чей `lstrip()`
начинается с `- [x] ` или `- [ ] `, внутри раздела `### Phase `. Понятия «план» у
разбора нет вовсе: вложенный чек-лист, критерий UAT, пункт «Blockers» — всё это
станет планом, как только окажется под заголовком фазы.

Сегодня это не срабатывает лишь по случайности расположения: перечень фаз
`- [x] **Phase 1: …**` (`.planning/ROADMAP.md:24-29`) лежит ВЫШЕ первого
`### Phase `, и разбор его пропускает по ветке `section is None`. Перенос этого
перечня ниже — правка оформления, а не смысла — молча прибавил бы шесть
«планов».

Опаснее текст отказа (`:131-137`): он утверждает, что править надо ПОЛЕ в
`STATE.md`. При ложном срабатывании эта инструкция заставит автора вписать в
машинно читаемое поле НЕВЕРНОЕ число — то есть гейт, заведённый против
расхождения, сам его и внесёт.

Отдельно: `ROADMAP_PATH.read_text(...)` (`:181`) не защищён ничем — отсутствие
`.planning/` даёт `FileNotFoundError` вместо объясняющего сообщения, которых
модуль в других местах пишет по три строки.

**Исправление.** Сузить форму до формы плана и оставить отказ объясняющим:

```python
PLAN_LINE = re.compile(r"^- \[([ xX])\] +\d\d-\d\d-PLAN\.md\b")
```

и, для читаемого отказа при отсутствующем источнике:

```python
    assert ROADMAP_PATH.exists(), (
        f"источник счёта планов не найден: {ROADMAP_PATH} — гейт не сверяет, "
        "а падает, и по трассировке это неотличимо от расхождения"
    )
```

Синтетические тексты `_synthetic_roadmap` уже пишут строки в форме
`СИНТ-{index}-PLAN.md`, поэтому потребуют лишь приведения к форме `NN-NN`.

---

### WR-04: Раздел «Тарифы» отвечает 500 на том же испорченном `PLAN_LIMITS`, который вебхук уже переживает

**Файл:** `app/pages/billing.py:174`, `:315-317`, `:433-451`
**Классификация:** WARNING

**Проблема.** План 05-28 сделал тотальным ОДНО место — `_plan_price`. Тот же
вход ломает раздел целиком:

* `billing_page:174` — `plans = settings.parsed_plan_limits` поднимает
  `JSONDecodeError` на битом JSON;
* `billing_page:229-234` — `plan.get("id")` поднимает `AttributeError` на списке
  строк;
* `subscribe_to_plan:359-360` — `selected["price"]` поднимает `KeyError` у записи
  без цены;
* `purchase_package:450-451` — `package["name"]` / `package["count"]` поднимают
  `KeyError` у записи без полей.

Докстринг `_plan_price` (`:964-972`) прямо называет причину, по которой защита
живёт «единственным местом»: «денежный путь уже считает это место тотальным».
Довод верен для уведомления и неверен для раздела: правка `PLAN_LIMITS`, снявшая
500 с вебхука, оставляет 500 на `/billing` — то есть человек не может ни увидеть
тарифы, ни узнать, что произошло.

**Исправление.** Ветка на выбор владельца, но не молчание: либо один защищённый
читатель конфига тарифов на проект (`parsed_plan_limits` отдаёт пустой перечень и
пишет `plan_limits_unreadable`), либо явное решение «раздел падает намеренно»,
записанное там, где сегодня записан противоположный довод. Сегодня в двух местах
одного конфига действуют две разные политики, и ни одна из них о другой не знает.

---

### WR-05: План, выпавший из конфига, показывается пользователю как БЕЗЛИМИТНЫЙ

**Файл:** `app/pages/billing.py:179-188`
**Классификация:** WARNING

**Проблема.**

```python
    current_plan = next(
        (plan for plan in plans if plan.get("id") == current_plan_id), {}
    )
    usage = await plan_axes(db, user=user, limits=current_plan, nav_counts=nav_counts)
```

Умолчание — ПУСТОЙ словарь. `plan_axes` читает лимиты как
`limits.get(key, UNLIMITED)` (`app/application/billing/plan_usage.py:202`), а
`UNLIMITED is None`, и шаблон рисует `None` как `∞` и подпись «без ограничений»
(`app/templates/billing/includes/usage_meters.html:30-34`). То есть пользователь,
чей план исчез из `PLAN_LIMITS` (или чья подписка несёт незнакомый план — путь,
который проект считает достижимым, см. `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month`
с планом `platinum`), видит НА ЧЕТЫРЁХ ОСЯХ обещание отсутствия лимитов.

Это прямо противоположно объявленному принципу соседнего модуля:
«ПЛАН, КОТОРОГО ЗДЕСЬ НЕТ, РАНГА НЕ ПОЛУЧАЕТ, И ЭТО ОТКАЗ, А НЕ ДОГАДКА»
(`app/constants.py:61-65`). Здесь отсутствующий план получает САМУЮ ЩЕДРУЮ из
возможных догадок.

**Исправление.** Отсутствие записи плана обязано быть отличимо от безлимита:

```python
    current_plan = next(
        (plan for plan in plans if plan.get("id") == current_plan_id), None
    )
    # Записи плана нет — осей не рисуем вовсе и говорим об этом словами:
    # `∞` на каждой оси обещал бы отсутствие лимитов там, где лимиты просто
    # неизвестны (тот же отказ, что у PLAN_ORDER для плана без ранга).
    usage = (
        await plan_axes(db, user=user, limits=current_plan, nav_counts=nav_counts)
        if current_plan is not None
        else []
    )
```

плюс подпись в разметке о том, что состав тарифа неизвестен.

---

### WR-06: Сокет Docker примонтирован в контейнер, терминирующий интернет-трафик

**Файл:** `docker-compose.prod.yml:91-92` (и `:120-121`)
**Классификация:** WARNING (унаследованное, не правка этой волны)

**Проблема.** Сервис `web` — тот самый, который принимает
`POST /api/billing/webhook` и весь пользовательский трафик, — монтирует
`/var/run/docker.sock` на запись. Доступ к сокету Docker эквивалентен root на
ХОСТЕ: любое исполнение кода внутри `web` (в том числе через десериализацию,
шаблон или зависимость) перестаёт быть ограниченным контейнером.

Находка не принадлежит волне раунда 7 и, судя по составу файла, принята вместе с
`wa_container_manager`. Она названа здесь потому, что файл заявлен в объёме, а
митигации в нём нет ни одной строкой.

**Исправление (работа своего размера, не правка на месте).** Вынести управление
контейнерами воркеров в отдельный сервис (сокет остаётся только у него, `web`
ходит к нему по сети), либо поставить перед сокетом прокси с белым списком
операций. Минимум на сегодня — записать принятый риск там же, где записаны
остальные («⚠️ НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ» в `is_same_origin` — готовый образец
формы).

---

## Info

### IN-01: `STATUS_PENDING` объявлен, не используется, и его значение выписано литералом

**Файл:** `app/services/payment_service.py:36` и `:407`

Константа `STATUS_PENDING = "pending"` не читается НИГДЕ на проекте, а
единственное место записи этого статуса (`create_payment`, `:407`) выписывает
литерал `status="pending"`. Это ровно тот приём, который соседний блок того же
модуля объявляет запрещённым: «защита… написана через это множество, а не через
перечисление в каждой ветке: копия в ветке рано или поздно разойдётся с
оригиналом» (`:40-44`).

**Исправление:** `status=STATUS_PENDING` на строке 407.

---

### IN-02: `AttributeError` в перечне перехвата `_plan_price` недостижим, а объяснение устарело

**Файл:** `app/services/payment_service.py:1005-1011`

Комментарий утверждает: «`AttributeError` добавлен ради формы „элемент перечня не
словарь“». Эта форма с плана 05-28 обрабатывается проверкой `isinstance` внутри
цикла (`:986`), до всякого `plan.get`. Единственный оставшийся источник —
`for plan in <не-итерируемое>`, а он даёт `TypeError`. Итерирование словаря, строки
или списка `AttributeError` не даёт ни при каком содержимом.

**Исправление:** либо снять `AttributeError` из перечня, либо переписать
объяснение под настоящую причину («оставлен страховкой на случай, если
`parsed_plan_limits` перестанет быть свойством»). Сегодня комментарий описывает
защиту, которой нет.

---

### IN-03: Одна пустая строка между определениями верхнего уровня

**Файл:** `app/services/payment_service.py:1024`

Между `return` в `_plan_price` и `def _apply_extension` стоит одна пустая строка;
все остальные определения модуля разделены двумя (PEP 8, E302). Линтера в проекте
нет, поэтому это не отказ прогона — но модуль в остальном оформлен безупречно, и
одиночное расхождение читается как след правки, а не как решение.

---

### IN-04: `tracking-check` не попал в перечень команд `CLAUDE.md`

**Файл:** `justfile:21-23` (потребитель — `CLAUDE.md`, §Commands)

План 05-31 завёл рецепт `tracking-check`, но раздел «Local development» в
`CLAUDE.md` перечисляет `run`/`test`/`test-cov`/`sync`/`add`/… без него. Рецепт,
о котором не сказано там, где читатель ищет команды, запускать будет только его
автор. (`CLAUDE.md` в объёме этой ревизии не числится — находка записана на
`justfile` как на источник расхождения.)

---

## Проверенное и НЕ ставшее находкой

Записано, чтобы следующий раунд не перепроверял то же самое:

* **Реестр принятого долга НЕ РОС.** `declared_invariants_without_witness.txt` — 37
  записей при потолке `WITHOUT_WITNESS_CEILING = 37`
  (`tests/test_application/test_declared_invariants.py:78`); последняя правка файла —
  `04160ce` (план 05-25), волной раунда 7 он не тронут. Прохибиция фазы соблюдена.
* **Ключ `plan_limits_unreadable` встречается в модуле РОВНО ОДИН РАЗ**
  (`app/services/payment_service.py:1021`), в докстринге его литерала нет —
  критерий приёмки плана 05-28 выполнен.
* **Гейт трекинга согласен с деревом:** выведено `(81, 81)`, записано `(81, 81)`;
  негативные контроли (`…round_seven_regression`, `…unchecked_plan_raises_the_total`)
  настоящие — они краснеют на подложенных парах, а не на константах.
* **Порядок старта** (`entrypoint.sh`: `set -e` → `alembic upgrade head` → `exec`)
  и его закрепление в `tests/test_migrations/test_deploy_applies_migrations_before_serving.py`
  проверены — свойство держится, и тест утверждает именно порядок, а не наличие.
* **500 при отказе брокера в `history_retry`** (`app/pages/history.py:1003-1013`) —
  не находка: исход объявлен решением и закреплён
  `tests/test_pages/test_history_retry.py:947-967`.
* **Экранирование разметки раздела** — шаблоны билинга не используют ни `|safe`,
  ни отключение автоэкранирования; `yookassa_payment_id` в разметку не уезжает.

---

_Reviewed: 2026-08-19T12:27:43Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
_Round: 8_
