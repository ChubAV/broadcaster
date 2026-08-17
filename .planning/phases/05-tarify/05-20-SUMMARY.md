---
phase: 05-tarify
plan: 20
subsystem: database
tags: [alembic, sqlalchemy, migrations, pytest, docker, entrypoint, yookassa]

requires:
  - phase: 05-tarify
    provides: "Ревизия 0019 (`payments.switch_authorized`), модель `Payment` с колонками `kind`/`plan`/`switch_authorized`, докстринг с местом ревизии в невыкаченной очереди D-26"
  - phase: 05-tarify
    provides: "План 05-18 (волна 15): `converted_remainder` в `subscription_period.py`; схему не менял, ревизий не заводил — головной ревизией репозитория остаётся 0019"
provides:
  - "Машинная сверка отображённых колонок `Payment` со схемой, построенной настоящим Alembic до `head` — ловит класс «отображённая колонка без ревизии»"
  - "Негативный контроль сверки: доказано машиной, что проверка краснеет при недостающей колонке"
  - "Докстринг ревизии 0019 называет ФАКТИЧЕСКИЙ радиус поражения D-26: все читающие пути `payments`, уцелевший `count_payments`, падение до ветвления по предмету покупки, денежный исход и неразделимость выката кода и очереди"
  - "Закреплённое тестом свойство боевого старта: очередь миграций доводится до головы раньше передачи управления приложению, отказ миграции останавливает старт"
affects: [05-21, выкат-D-26, ship]

actuals:
  tokens: 7500
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Сверка модели с головной ревизией репозитория как постоянный тест суиты, а не как ревью-практика"
    - "Негативный контроль рядом с проверкой: зелёная проверка обязана быть отличима от отсутствующей машиной"
    - "Утверждения о сценарии старта по ПОЗИЦИИ строк относительно друг друга, а не по их точному тексту"

key-files:
  created:
    - tests/test_migrations/test_model_matches_head.py
    - tests/test_migrations/test_deploy_applies_migrations_before_serving.py
  modified:
    - alembic/versions/0019_payment_switch_authorized.py

key-decisions:
  - "`entrypoint.sh` НЕ правился: свойство «очередь до головы раньше обслуживания» уже держится (`set -e` → `alembic upgrade head` → `exec \"$@\"`). Второй гейт поверх работающего завёл бы два ответа на один вопрос"
  - "Сверка направлена односторонне: каждая ОТОБРАЖЁННАЯ колонка обязана быть в схеме; обратное включение не требуется — в `SELECT` уезжает перечень модели, а не перечень таблицы"
  - "Головная ревизия читается у `ScriptDirectory`, а не выписана литералом: литерал устарел бы на следующей ревизии и превратил бы утверждение о достижении головы в утверждение о достижении вчерашней головы"
  - "Объём сверки ограничен таблицей `payments` и это названо границей в файле, а не оставлено молчанием"
  - "`graphify update .` не запускался: в графе живёт `app/`, который план не трогает; артефакт не отслеживается git и его регенерация в параллельном worktree создала бы конфликт с агентом 05-19"

patterns-established:
  - "Проверка обязана называть, чего она НЕ доказывает: докстринг `test_model_matches_head.py` прямым текстом запрещает читать свой зелёный цвет как утверждение о боевом стенде"
  - "Однократная проверка зубов на НАСТОЯЩЕЙ ревизии (снятие `op.add_column`, прогон, возврат) с записью результата — рядом с постоянным негативным контролем в суите"

requirements-completed: [BILL-06, BILL-07]

coverage:
  - id: D1
    description: "Машинная сверка отображённых колонок `Payment` со схемой, построенной настоящим Alembic до `head`; недостающие называются поимённо"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_model_matches_head.py#test_every_mapped_payment_column_exists_at_head"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_model_matches_head.py#test_the_upgrade_actually_reached_head"
        status: pass
    human_judgment: false
  - id: D2
    description: "У сверки доказанно есть зубы: негативный контроль краснеет при недостающей колонке"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_model_matches_head.py#test_the_check_names_the_missing_column_by_name"
        status: pass
      - kind: other
        ref: "Однократно: снятие `op.add_column` в 0019 → `test_every_mapped_payment_column_exists_at_head` падает с перечнем ['switch_authorized']; ревизия возвращена в прежний вид"
        status: pass
    human_judgment: false
  - id: D3
    description: "Свойство боевого старта закреплено: очередь миграций доводится до головы раньше передачи управления приложению, отказ миграции останавливает старт, `web` подключён к сценарию"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_migrations/test_deploy_applies_migrations_before_serving.py#test_the_migration_queue_is_drained_before_the_app_serves"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_deploy_applies_migrations_before_serving.py#test_a_failed_migration_stops_the_start"
        status: pass
      - kind: unit
        ref: "tests/test_migrations/test_deploy_applies_migrations_before_serving.py#test_the_service_that_terminates_the_money_paths_starts_through_the_script"
        status: pass
    human_judgment: false
  - id: D4
    description: "Докстринг ревизии 0019 называет фактический радиус поражения решения D-26 вместо прежнего «практического последствия сегодня нет»"
    requirement: BILL-07
    verification:
      - kind: other
        ref: "grep -ci 'практического последствия' alembic/versions/0019_payment_switch_authorized.py → 0; get_payment_history / _open_subscription_intents / handle_webhook присутствуют"
        status: pass
    human_judgment: true
    rationale: "Достаточность формулировки — судейская величина: машина проверяет присутствие имён путей, но не то, что читатель перед выкатом прочтёт последствие верно. Приёмка формулировки принадлежит владельцу решения D-26"
  - id: D5
    description: "Первый настоящий выкат после прохождения очереди ревизий: `web` поднимается только после успешной миграции, раздел «Тарифы» на боевом стенде отвечает 200"
    verification: []
    human_judgment: true
    rationale: "Backstop-пункт плана. Боевого доступа у исполнителя нет; суита строит схему в памяти и о проде не знает ничего. Это решение владельца о выкате (D-26), а не свойство репозитория"

duration: 34min
completed: 2026-08-17
status: complete
---

# Phase 05 Plan 20: Фактическое последствие D-26 и машинная сверка модели с головой — Summary

**Последствие расхождения модели и боевой схемы переписано по фактическому радиусу поражения (ломается приём ПАКЕТНЫХ платежей, а не только подписочная ветка), класс «отображённая колонка без ревизии» ловится теперь настоящим прогоном Alembic с доказанными зубами, а свойство боевого старта проверено и закреплено тестом порядка.**

## Performance

- **Duration:** ~34 min (из них 16 min — финальный прогон полной суиты)
- **Started:** 2026-08-17
- **Completed:** 2026-08-17
- **Tasks:** 2
- **Files modified:** 3 (2 создано, 1 изменён)

## Accomplishments

- **Гэп 2 раунда 5, четвёртое опровергнутое утверждение — кодовая половина закрыта.** Докстринг ревизии `0019` больше не утверждает, что практического последствия у невыкаченной очереди сегодня нет. Он называет механизм (ORM-выборка сущности выписывает ПОЛНЫЙ перечень отображённых колонок), все отказывающие пути поимённо, уцелевший путь, падение ДО ветвления по предмету покупки и денежный исход.
- **Класс дефекта ловится машиной.** `tests/test_migrations/test_model_matches_head.py` строит схему НАСТОЯЩИМ Alembic (штамп `0018` → `command.upgrade` до `head`), утверждает достижение головы и сверяет с ней `Payment.__table__.columns`.
- **У проверки доказанно есть зубы** — постоянный негативный контроль в суите плюс однократная проверка на настоящей ревизии.
- **Свойство боевого старта установлено фактом, а не памятью, и закреплено тестом.** `entrypoint.sh` не потребовал ни одной правки.

## Task Commits

1. **Task 1 (RED): негативный контроль сверки** — `faaddc8` (test)
2. **Task 1 (GREEN): сверка отображённых колонок с головной ревизией** — `d9ee957` (feat)
3. **Task 2: фактический радиус поражения D-26 + закрепление порядка старта** — `fcb8320` (docs)

REFACTOR-коммита нет: после GREEN чистить было нечего — сверка вынесена чистой функцией с самого начала.

## Files Created/Modified

- `tests/test_migrations/test_model_matches_head.py` (создан) — чистая функция `missing_columns`, фикстура файловой базы, доведённой Alembic до `head`, три теста: негативный контроль, достижение головы, подмножество колонок.
- `tests/test_migrations/test_deploy_applies_migrations_before_serving.py` (создан) — три утверждения о сценарии старта по позициям строк.
- `alembic/versions/0019_payment_switch_authorized.py` (изменён) — только докстринг. `upgrade` и `downgrade` не тронуты ни строкой.

## Проверенный механизм: выборка стоит ВЫШЕ ветвления по предмету покупки

Требование плана — не принимать это по отчёту. Проверено чтением `app/services/payment_service.py`:

| Что | Строки | Оператор |
|-----|--------|----------|
| Выборка платежа | **443-448** | `select(Payment).where(...).with_for_update()` → `scalar_one_or_none()` |
| Ветвление: пакетная проверка | **496** | `if db_payment.kind != KIND_SUBSCRIPTION and not db_payment.messages_count:` |
| Ветвление: подписочная ветка | **518** | `if db_payment.kind == KIND_SUBSCRIPTION:` |

443-448 < 496 < 518 — выборка исполняется ДО любого решения о предмете покупки. Значит на схеме `0012` `UndefinedColumn` поднимается и для платежа за ПАКЕТ СООБЩЕНИЙ. Далее `app/routes/billing.py:200-202` превращает необработанное исключение в `HTTPException(500)`.

Отчёт раунда 5 называл `442-447` / `:495` / `:517` — расхождение на одну строку; проверено на текущем коде, в докстринг и SUMMARY попали проверенные номера.

Читающие пути и уцелевший (проверено чтением):

| Путь | Файл:строки | Оператор | Что перестаёт работать |
|------|-------------|----------|------------------------|
| `get_payment_history` | `billing_service.py:230-236` | `select(Payment)` | раздел «Тарифы» целиком отдаёт 500 любому вошедшему |
| `_open_subscription_intents` | `payment_service.py:136-148` | `select(Payment)` | потолок одновременных намерений |
| `handle_webhook` | `payment_service.py:443-448` | `select(Payment).with_for_update()` | приём ПАКЕТНЫХ платежей, работавший до фазы |
| `count_payments` | `billing_service.py:247-251` | `count()` — **уцелеет** | — |

## Три ответа о фактическом поведении боевого старта

Требование плана — сначала установить, потом решать.

1. **Доводится ли очередь миграций до головы ДО передачи управления процессу приложения?** — **ДА.** `entrypoint.sh:5` — `uv run alembic upgrade head`; `entrypoint.sh:8` — `exec "$@"`. Порядок именно этот.
2. **Останавливает ли отказ этого шага старт?** — **ДА.** `entrypoint.sh:2` — `set -e`, включён ДО шага миграции. Падение `alembic upgrade` обрывает сценарий, до `exec` управление не доходит.
3. **Обслуживает ли сценарий ВСЕ сервисы, терминирующие денежные пути?** — **ДА, с названным звеном.** `entrypoint: ["./entrypoint.sh"]` объявлен только у сервиса `web` (`docker-compose.prod.yml:77`). Денежные пути — `POST /api/billing/webhook` и раздел «Тарифы» — терминируются именно web-процессом. Celery-сервисы (`celery-beat`, `celery-worker-telegram`, `celery-worker-default`, `flower`) собственного `entrypoint` не имеют и стартуют по `CMD` образа в обход сценария, **но** каждый объявляет `depends_on: web: condition: service_healthy` (`docker-compose.prod.yml:104-106, 112-114, 122-124, 132-134`), а healthcheck `web` (`:93-98`) проходит только после того, как entrypoint довёл очередь. Обхода нет ни у одного сервиса.

**Вывод: `entrypoint.sh` НЕ ПРАВИЛСЯ, и это проверенный факт, а не пропуск.** `git diff --name-only -- entrypoint.sh` пуст. Вводить второй гейт («отказаться поднимать `web` при `alembic current != head`», как предлагал набросок `CR-02`) поверх уже работающего доведения очереди значило бы завести два ответа на один вопрос. Вместо правки свойство ЗАКРЕПЛЕНО тестом: сегодня оно держится порядком трёх строк, и одна правка сняла бы его молча.

## Доказательство зубов проверки

**Постоянный негативный контроль (в суите навсегда).** RED-коммит `faaddc8` содержал заглушку `missing_columns`, всегда возвращавшую `[]`. Вывод упавшего теста дословно:

```
>       assert missing_columns(mapped, without_one) == ["switch_authorized"]
E       AssertionError: assert [] == ['switch_authorized']
E
E         Right contains one more item: 'switch_authorized'
E         Use -v to get more diff

tests/test_migrations/test_model_matches_head.py:122: AssertionError
```

Падение — на `AssertionError`. Ни `ImportError`, ни `NameError` в выводе нет.

**Однократная проверка на НАСТОЯЩЕЙ ревизии.** `op.add_column` в `alembic/versions/0019_payment_switch_authorized.py` был временно закомментирован; прогон:

```
E       AssertionError: отображены моделью, но не заведены ни одной ревизией до головы: ['switch_authorized']
E       assert not ['switch_authorized']
```

Недостающая названа ПОИМЁННО (строка утверждения — `assert not absent, ("отображены моделью, но не заведены ни одной ревизией до головы: " f"{absent}")`), а не числом. Ревизия возвращена в прежний вид; правка не коммитилась — `git diff --name-only -- alembic/` был пуст на коммите задачи 1, `git show --name-only --format= d9ee957` содержит только файл теста.

## Проверка критериев приёмки

| Критерий | Команда | Результат |
|----------|---------|-----------|
| Прежнее утверждение снято | `grep -ci "практического последствия" alembic/versions/0019_*.py` | `0` |
| Все читающие пути названы | `grep -c` для трёх имён | `1` / `1` / `2` |
| Тело ревизии не тронуто | `git diff -U0 -- alembic/versions/0019_*.py \| grep -E "^[+-]\s*(op\.\|def \|revision\|down_revision)"` | пусто (exit 1) |
| Сверка настоящим Alembic | `grep -c "command.upgrade"` | `2` |
| Достижение головы | `grep -cE "get_current_head\|ScriptDirectory"` | `2` |
| Колонки читаются у модели | `grep -c "Payment.__table__.columns"` | `2` |
| Оговорка о проде | `grep -c "D-26"` + `Base.metadata.create_all` в докстринге | `3` + `1` |
| Тест утверждает ПОРЯДОК | `grep -cE "index\|find\|lineno\|enumerate"` | `12` |
| `app/` и `.planning/` не тронуты коммитами задач | `git show --name-only --format= faaddc8 d9ee957 fcb8320 -- app/ .planning/` | пусто |
| Суита миграций | `uv run pytest tests/test_migrations/ -q` | 63 passed |
| Полная суита | `uv run pytest tests/ -q` | **1731 passed** за 953s |

Цитата утверждения о неразделимости выката из докстринга ревизии: *«ВЫКАТ КОДА И ВЫКАТ ОЧЕРЕДИ МИГРАЦИЙ ОТДЕЛИТЬ ДРУГ ОТ ДРУГА НЕЛЬЗЯ. Не „желательно вместе“ — нельзя: код, приехавший на схему `0012`, отвечает 500 на деньги.»*

## Decisions Made

- **`entrypoint.sh` не правится** — свойство держится; обоснование выше.
- **Сверка направлена односторонне** (`mapped ⊆ actual`): колонка в схеме без отображения в модели ничего не ломает, потому что в `SELECT` уезжает перечень модели.
- **Голова читается у `ScriptDirectory`, а не литералом.**
- **Граница объёма названа в файле:** сверяется одна таблица `payments`; обобщение потребовало бы снимка каждой таблицы в состоянии стартовой ревизии.
- **`graphify update .` не запускался.** Правила `CLAUDE.md` предписывают обновлять граф после изменения кода; здесь изменены только тесты и докстринг ревизии (`app/` не тронут ни строкой), `graphify-out/` не отслеживается git (`git ls-files graphify-out` пуст), а регенерация в параллельном worktree наложилась бы на агента 05-19. Обновление графа отнесено к оркестратору после слияния волны.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Третий тест в файле старта: связь сценария с сервисом**

- **Found during:** Task 2 (часть 3)
- **Issue:** План формулирует три утверждения о САМОМ сценарии (присутствие, порядок, режим остановки). Правильный сценарий, не подключённый к сервису, не защищает ничего: снятие строки `entrypoint: ["./entrypoint.sh"]` из `docker-compose.prod.yml` сняло бы свойство целиком, не уронив ни одного из трёх утверждений. Ответ на третий вопрос плана («обслуживает ли сценарий все сервисы, терминирующие денежные пути») иначе жил бы только прозой SUMMARY — ровно тот способ хранения, который план и называет «держится вниманием читателя».
- **Fix:** Добавлен `test_the_service_that_terminates_the_money_paths_starts_through_the_script`: сервис `web` в боевом артефакте подключён к `entrypoint.sh`. Утверждение узкое — одна подстрока в блоке одного сервиса; блок находится по отступу ключа, а не по имени (первая редакция находила `web:` внутри `depends_on:` соседнего сервиса и падала — исправлено до коммита).
- **Files modified:** `tests/test_migrations/test_deploy_applies_migrations_before_serving.py`
- **Verification:** `uv run pytest tests/test_migrations/ -q` → 63 passed
- **Committed in:** `fcb8320` (коммит задачи 2)

**Осознанно НЕ сделано:** звено `depends_on: web: condition: service_healthy` у Celery-сервисов тестом не закрепляется. Оно принадлежит описанию сервисов, а не сценарию старта, и его разбор потребовал бы разбора YAML — `PyYAML` в `pyproject.toml` не объявлен (только транзитивно), а план запрещает добавлять зависимости. Факт записан прозой выше; тест бы соврал о своей опоре.

**2. [Rule 3 - Blocking] Номера строк механизма разошлись с отчётом на единицу**

- **Found during:** Task 2 (часть 1)
- **Issue:** `05-VERIFICATION.md` и `05-REVIEW.md` называют `payment_service.py:442-447` / `:495` / `:517`. На текущем коде выборка занимает 443-448, ветвления — 496 и 518.
- **Fix:** В докстринг ревизии и в SUMMARY попали номера, проверенные чтением текущего файла, а не переписанные из отчёта. Утверждение «выборка выше ветвления» подтверждено независимо.
- **Files modified:** `alembic/versions/0019_payment_switch_authorized.py`
- **Verification:** чтение `app/services/payment_service.py`
- **Committed in:** `fcb8320`

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** Ни одна правка не расширила объём за границы `files_modified`. `app/` не изменён ни строкой (`git diff --name-only 1e62a71 HEAD -- app/` пуст), схема не изменена, ревизий не заведено, решение D-26 не переоткрыто.

## Issues Encountered

- **Первая редакция теста compose читала чужой блок.** Поиск `web:` по подстроке находил вхождение внутри `depends_on:` сервиса `nginx`, и утверждение об `entrypoint` проверялось на блоке nginx. Исправлено до коммита: ключ сервиса опознаётся по отступу (ровно два пробела), причина записана комментарием в тесте — иначе следующий читатель «упростит» условие обратно.
- **`PyYAML` доступен в окружении, но не объявлен в `pyproject.toml`.** Опора на него в тесте была бы необъявленной зависимостью; от разбора YAML отказались в пользу текстовых утверждений.

## Known Stubs

Их нет. Заглушка `missing_columns` существовала ровно один коммит (`faaddc8`, RED) и заменена настоящей реализацией в `d9ee957`.

## Threat Flags

Новых поверхностей не введено: `app/` не тронут, маршрутов и переменных окружения не добавлено, схема не изменена. Диспозиция `accept` у `T-05-126` (расхождение модели с БОЕВОЙ схемой не ловится ничем, кроме дисциплины) остаётся в силе и записана долгом с форсирующим признаком: первый выкат после D-26 либо второй стенд со своей ревизией.

## User Setup Required

None — внешних сервисов план не конфигурирует.

## Next Phase Readiness

- **Кодовая половина гэпа 2 закрыта.** Документальная половина — строка 88 `.planning/STATE.md`, несущая то же заниженное последствие, — принадлежит плану **05-21** и этим планом не тронута ни строкой (`git diff --name-only 1e62a71 HEAD -- .planning/` содержит только собственный SUMMARY).
- **Перенесённые человеческие проверки:** первый настоящий выкат после прохождения очереди ревизий (backstop, D5 выше); настоящий платёж в тестовом магазине ЮKassa (D-26); первое настоящее уведомление после выката (backstop 05-07). Ни зелёный цвет суиты, ни этот план утверждением о боевом стенде не являются.
- **Три judgment-tier прохибиции фазы** (BILL-05, BILL-06, BILL-07) остаются `unresolved`.
- **Долг, принятый явно:** расхождение модели с БОЕВОЙ схемой машиной не ловится. Форсирующий признак промоции — первый выкат после D-26 либо второй стенд с собственной ревизией.

## Self-Check: PASSED

- `tests/test_migrations/test_model_matches_head.py` — FOUND
- `tests/test_migrations/test_deploy_applies_migrations_before_serving.py` — FOUND
- `alembic/versions/0019_payment_switch_authorized.py` — FOUND (изменён)
- Коммиты `faaddc8`, `d9ee957`, `fcb8320` — FOUND в `git log`
- `git diff --name-only 1e62a71 HEAD` содержит ровно четыре пути: три из `files_modified` плюс собственный SUMMARY. `entrypoint.sh` отсутствует — проверенный факт, а не пропуск. `.planning/STATE.md` и `.planning/ROADMAP.md` не тронуты.

---
*Phase: 05-tarify*
*Completed: 2026-08-17*
