---
phase: 05-tarify
plan: 28
subsystem: payments
tags: [yookassa, webhook, structlog, pytest, decimal, config, json]

requires:
  - phase: 05-tarify
    provides: "`_plan_price` и ветки отката `_apply_extension` (план 05-26); `capped_carryover` (план 05-22); гейт объявлений `test_declared_invariants.py`"
provides:
  - "`_plan_price` держит собственный контракт: четыре воспроизведённые формы испорченного `PLAN_LIMITS` дают `None`, а не исключение"
  - "Собственный журнальный ключ `plan_limits_unreadable` уровня `error` — след того, что нечитаем САМ ПЕРЕЧЕНЬ, а не цена в нём"
  - "Параметризованная регрессия `test_a_malformed_plan_list_does_not_break_the_notification` по четырём формам, ПАДАВШАЯ до правки (доказано отдельным RED-коммитом)"
  - "Элемент перечня, не являющийся словарём, пропускается и оставляет след, а не роняет обход целиком"
affects: [05-31, billing, verification-round-8]

actuals:
  tokens: 72900
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Защита читателя конфига стоит в ЕДИНСТВЕННОМ месте, которое денежный путь уже считает тотальным, — не в стартовой валидации"
    - "Флаг `unreadable` вместо второго `logger.error`: ключ журнала назван в модуле РОВНО ОДИН раз"

key-files:
  created: []
  modified:
    - app/services/payment_service.py
    - tests/test_pages/test_billing_payment_errors.py

key-decisions:
  - "Перехват в `_plan_price` оставлен ЗАКРЫТЫМ перечнем типов `(InvalidOperation, TypeError, ValueError, AttributeError)`, а не заменён на `Exception`: иначе опечатка в имени поля отдала бы `None` молча (T-05-190)"
  - "Приведение цены к `Decimal` осталось под ОТДЕЛЬНЫМ внутренним `try`, который следа `plan_limits_unreadable` не оставляет: «цена этого плана не читается» — штатный исход, «перечень сломан целиком» — авария окружения, и смешивать их в одном ключе значило бы вернуть T-05-189"
  - "Ключ `plan_limits_unreadable` испускается ОДИН раз в конце функции по флагу `unreadable`, а не двумя вызовами (в `except` и в ветке пропуска не-словаря): критерий приёмки требует единственного вхождения ключа в модуле"
  - "Элемент перечня, не являющийся словарём, ПРОПУСКАЕТСЯ, но взводит флаг: список, где сломан один элемент из трёх, не отнимает у покупателя дни на его исправном плане и при этом не теряет следа"
  - "Стартовая валидация конфига отвергнута и названа отвергнутой прямо в докстринге (прохибиция BILL-05, category integrity)"

patterns-established:
  - "Инвертированный `<verify>` для RED-задачи: `--collect-only -k <имя>` доказывает, что тест собирается, `! pytest <тест>` — что он падает"
  - "Абзац докстринга, попадающий под гейт объявлений, называет свидетеля по имени в ТОМ ЖЕ абзаце — иначе гейт краснеет справедливо"

requirements-completed: [BILL-05, BILL-06, BILL-07]

coverage:
  - id: D1
    description: "Четыре формы испорченного `PLAN_LIMITS` (битый JSON, объект вместо списка, список строк, `null`) возвращают из `_plan_price` `None` и не поднимают исключения"
    requirement: BILL-05
    verification:
      - kind: unit
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_malformed_plan_list_does_not_break_the_notification"
        status: pass
    human_judgment: false
  - id: D2
    description: "Уведомление ЮKassa переживает испорченный перечень: `handle_webhook` возвращает `True`, платёж доходит до `succeeded`, срок двигается и не превышает двух календарных месяцев от подтверждения"
    requirement: BILL-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_malformed_plan_list_does_not_break_the_notification"
        status: pass
    human_judgment: false
  - id: D3
    description: "Расхождение конфига с базой оставляет собственный след: запись уровня `error` с ключом `plan_limits_unreadable`, отличным от `subscription_prorating_skipped`"
    requirement: BILL-07
    verification:
      - kind: unit
        ref: "tests/test_pages/test_billing_payment_errors.py#test_a_malformed_plan_list_does_not_break_the_notification"
        status: pass
    human_judgment: false
  - id: D4
    description: "Регрессия ПАДАЛА на коде до правки — доказано отдельным RED-коммитом `339fc97` с тремя разными типами исключений в выводе"
    requirement: BILL-05
    verification:
      - kind: other
        ref: "git show 339fc97 --stat; uv run pytest tests/test_pages/test_billing_payment_errors.py::test_a_malformed_plan_list_does_not_break_the_notification -q (на дереве 339fc97 — 4 failed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Объявление `_plan_price` описывает сегодняшнее тело, называет свидетеля и НЕ стирает прежнюю редакцию; гейт объявлений зелен, реестр долга не вырос"
    requirement: BILL-06
    verification:
      - kind: unit
        ref: "tests/test_application/test_declared_invariants.py (18 passed); git diff --name-only -- tests/test_application/declared_invariants_without_witness.txt (пусто)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Человек, у которого правка окружения совпала с подтверждением платежа, получает дни, а не бесконечный `pending`; разбор обращения по журналу отличает «конфиг сломан» от «цена не читается» без чтения кода"
    verification: []
    human_judgment: true
    rationale: "Пригодность журнала к разбору обращения судится человеком — это `backstop` из `must_haves.truths` плана, и автоматика её не измеряет"

duration: 57min
completed: 2026-08-19
status: complete
---

# Phase 05 Plan 28: `_plan_price` подчиняется собственному объявлению — Summary

**Обход `parsed_plan_limits` перенесён внутрь защиты и накрыт `AttributeError`: четыре воспроизведённые формы испорченного `PLAN_LIMITS` больше не дают 5xx на уведомлении ЮKassa, а оставляют собственный след `plan_limits_unreadable` — закреплено параметризованной регрессией, падавшей до правки.**

## Performance

- **Duration:** ~57 min
- **Started:** 2026-08-19T08:36:00Z (приблизительно; прогон предусловия — 08:38)
- **Completed:** 2026-08-19T09:33:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `_plan_price` держит контракт, который объявляет сама: ЧТЕНИЕ И ОБХОД перечня стоят внутри `try`, состав перехвата расширен `AttributeError` (`JSONDecodeError` накрывается `ValueError`).
- Исход T-05-104 («5xx на уведомлении запускает цикл повторов и оставляет платёж `pending` навсегда») на этом входе недостижим: на каждой из четырёх форм `handle_webhook` возвращает `True`, строка платежа доходит до `succeeded`, срок двигается и зажат `capped_carryover`.
- Расхождение конфига с базой оставляет СОБСТВЕННЫЙ след: `logger.error("plan_limits_unreadable", plan_id=...)`, ключ отличен от `subscription_prorating_skipped`, содержимое `PLAN_LIMITS` в журнал не пишется (T-05-193).
- Элемент перечня, не являющийся словарём, пропускается и взводит флаг: список со сломанным одним элементом из трёх не отнимает дни на исправном плане, но следа не теряет.
- Объявление переписано: непригодным назван САМ ПЕРЕЧЕНЬ, прежняя редакция названа (а не стёрта), свидетель назван по имени, стартовая валидация конфига отвергнута прямым текстом.

## Task Commits

1. **Task 1: RED — регрессия по четырём формам испорченного `PLAN_LIMITS`** — `339fc97` (test)
2. **Task 2: GREEN — тотальный читатель перечня и переписанное объявление** — `b73fba0` (fix)

Порядок RED→GREEN подтверждён: `git log --oneline -3` даёт `b73fba0` (fix) поверх `339fc97` (test) поверх `8d4ae8f`.

## Files Created/Modified

- `app/services/payment_service.py` — `_plan_price`: обход перечня внутри защиты, пропуск не-словарного элемента с флагом, единственное испускание `plan_limits_unreadable`, два новых абзаца объявления.
- `tests/test_pages/test_billing_payment_errors.py` — константа `MALFORMED_PLAN_LIMITS` и параметризованная регрессия `test_a_malformed_plan_list_does_not_break_the_notification` (+90 строк, 0 удалённых).

## (1) Красный прогон ДО правки — по КАЖДОЙ из четырёх форм

Коммит `339fc97`, дерево без правки `app/`:

```
FAILED ...::test_a_malformed_plan_list_does_not_break_the_notification[broken_json]
FAILED ...::test_a_malformed_plan_list_does_not_break_the_notification[object_instead_of_list]
FAILED ...::test_a_malformed_plan_list_does_not_break_the_notification[list_of_strings]
FAILED ...::test_a_malformed_plan_list_does_not_break_the_notification[json_null]
4 failed, 1 warning in 4.73s
```

Имена поднятых исключений, снятые с того же прогона (`app/services/payment_service.py:928`, строка `for plan in get_settings().parsed_plan_limits:`):

| Случай `parametrize` | Форма `PLAN_LIMITS` | Поднятое исключение |
|---|---|---|
| `broken_json` | `{not json` | `json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)` |
| `object_instead_of_list` | `{"id": "basic"}` | `AttributeError: 'str' object has no attribute 'get'` |
| `list_of_strings` | `["basic"]` | `AttributeError: 'str' object has no attribute 'get'` |
| `json_null` | `null` | `TypeError: 'NoneType' object is not iterable` |

Три разных типа исключений в выводе — ровно то, что требовал критерий приёмки задачи 1. Собралось при этом ЧЕТЫРЕ случая, а не один:

```
tests/...::test_a_malformed_plan_list_does_not_break_the_notification[broken_json]
tests/...::test_a_malformed_plan_list_does_not_break_the_notification[object_instead_of_list]
tests/...::test_a_malformed_plan_list_does_not_break_the_notification[list_of_strings]
tests/...::test_a_malformed_plan_list_does_not_break_the_notification[json_null]
4/88 tests collected (84 deselected)
```

Инвертированный `<verify>` задачи 1 (`--collect-only -k` && `! pytest`) завершился кодом `0`.

## (2) Зелёный прогон ПОСЛЕ правки

Целевая регрессия:

```
uv run pytest ...::test_a_malformed_plan_list_does_not_break_the_notification -q
....                                                                     [100%]
4 passed, 1 warning in 4.76s
```

`<verify>` задачи 2 (три файла):

```
uv run pytest tests/test_pages/test_billing_payment_errors.py \
              tests/test_services/test_payment_service.py \
              tests/test_application/test_declared_invariants.py -q
121 passed, 20 warnings in 85.31s
```

Вся суита:

```
uv run pytest tests/ -q
1771 passed, 576 warnings in 1037.39s (0:17:17)
```

Прямой прогон `_plan_price` по семи входам поведенческого списка задачи 2 (patch `app.services.payment_service.get_settings` на настоящий `Settings`):

```
broken_json              -> None                 error_keys=['plan_limits_unreadable']
object_instead_of_list   -> None                 error_keys=['plan_limits_unreadable']
list_of_strings          -> None                 error_keys=['plan_limits_unreadable']
json_null                -> None                 error_keys=['plan_limits_unreadable']
healthy/basic            -> Decimal('1490.00')   error_keys=[]
healthy/free             -> None                 error_keys=[]
healthy/unknown          -> None                 error_keys=[]
```

Штатные исходы сохранены дословно: исправный перечень отдаёт прежнюю цену (T-05-190), Free и план, выпавший из перечня, по-прежнему дают `None` БЕЗ записи в журнале.

## (3) Хеши коммитов в порядке

| Порядок | Хеш | Сообщение |
|---|---|---|
| 1 (RED) | `339fc97` | `test(05-28): регрессия на испорченный PLAN_LIMITS` |
| 2 (GREEN) | `b73fba0` | `fix(05-28): _plan_price читает перечень тарифов тотально` |

`git diff --name-only HEAD~2 HEAD` даёт ровно два файла: `app/services/payment_service.py`, `tests/test_pages/test_billing_payment_errors.py`. RED-коммит содержит РОВНО один файл (`tests/...`), правки `app/` в нём нет по построению.

## (4) Что НЕ тронуто

- `test_a_price_that_cannot_be_read_falls_back_to_the_whole_month` — тело не изменено: диф файла тестов даёт `90 insertions(+), 0 deletions`, новый тест вставлен ПОСЛЕ соседа.
- `tests/test_application/declared_invariants_without_witness.txt` — не изменён: `git diff --name-only -- tests/test_application/declared_invariants_without_witness.txt` пуст. Реестр долга не вырос; оба новых абзаца объявления называют свидетеля `test_a_malformed_plan_list_does_not_break_the_notification` и потому в реестр не попадают. Гейт `tests/test_application/test_declared_invariants.py` зелен.
- Схема БД, ревизии Alembic, `pyproject.toml`, `uv.lock` — не тронуты. Пакетов не устанавливалось (T-05-SC неприменим).
- Сигнатура `def _plan_price(plan_id: str | None) -> Decimal | None:` не изменилась, функция осталась синхронной, порядок транзакции плана 05-08 не задет.

## (5) `parsed_message_packages` этим планом НЕ правился

`parsed_message_packages` (`app/config.py:115-117`) имеет ТУ ЖЕ форму отказа — голый `json.loads` строки окружения без схемы — и роняет `GET /api/billing/packages` (`app/routes/billing.py:26-27`) и `POST /billing/purchase` (`app/pages/billing.py:433`). Раунд 7 это назвал («Consider the same treatment») и НЕ вменил вердикту: цена там — страница, а не застрявший платёж. **Здесь он не исполнялся сознательно**; распоряжение по пункту принимает план `05-31` в реестре находок раунда 7, а не молчание.

## Decisions Made

Смотри `key-decisions` во фронтматтере. Одно решение стоит назвать развёрнуто:

**Два уровня защиты вместо одного.** Прямое прочтение задачи 2 («перенести обход внутрь защиты») давало ОДИН `try`, накрывающий и обход, и приведение цены. Так сделать было нельзя: тогда нечитаемая цена конкретного плана писала бы `plan_limits_unreadable` наравне с аварией всего перечня — то есть ровно то смешение двух смыслов в одном ключе, против которого стоит T-05-189 и прохибиция BILL-07. Поэтому внешний `try` накрывает ЧТЕНИЕ И ОБХОД (и только он ведёт к `plan_limits_unreadable`), а приведение цены осталось под собственным внутренним `try`, отдающим `None` молча — как и до плана. Оба уровня названы в коде комментариями со свидетелями.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Пропуск не-словарного элемента терял след поломки**

- **Found during:** Task 2 (GREEN)
- **Issue:** Прямое прочтение действия задачи 2 — «дополнительно пропускать элементы, не являющиеся словарями (`isinstance(plan, dict)`)» — на формах 2 (`{"id": "basic"}`, обход даёт КЛЮЧИ словаря) и 3 (`["basic"]`) уводит выполнение мимо `except` целиком: цикл штатно завершается, функция возвращает `None`, и записи `plan_limits_unreadable` НЕ появляется вовсе. Регрессия задачи 1 на этих двух формах осталась бы красной, а `must_haves.truths` «расхождение конфига оставляет след» — нарушенным на половине входа.
- **Fix:** Введён локальный флаг `unreadable`, который взводится и в `except`, и в ветке пропуска не-словарного элемента; запись испускается ОДИН раз после цикла по флагу. Это же снимает конфликт с критерием «`grep -c 'plan_limits_unreadable'` даёт `1`», который два отдельных `logger.error` нарушили бы.
- **Files modified:** `app/services/payment_service.py`
- **Verification:** 4 из 4 случаев регрессии зелены; прямой прогон `_plan_price` показывает `error_keys=['plan_limits_unreadable']` на всех четырёх формах.
- **Committed in:** `b73fba0` (коммит задачи 2)

**2. [Rule 3 — Blocking] Ключ упоминался в модуле трижды при критерии «ровно 1»**

- **Found during:** Task 2 (GREEN), проверка критериев приёмки
- **Issue:** Первая редакция называла `plan_limits_unreadable` в трёх строках модуля (абзац докстринга, комментарий внутреннего `except`, сам вызов `logger.error`). Критерий приёмки требует `grep -c 'plan_limits_unreadable' app/services/payment_service.py` == `1`.
- **Fix:** Абзац докстринга и комментарий переформулированы без литерала («собственную запись в журнале уровня `error` — ключ назван один раз, в теле ниже»); литерал остался только в `logger.error`. Смысл обеих фраз сохранён.
- **Files modified:** `app/services/payment_service.py`
- **Verification:** `grep -c 'plan_limits_unreadable'` даёт `1`; гейт объявлений и вся суита перепрогнаны после правки и зелены (`1771 passed`).
- **Committed in:** `b73fba0` (коммит задачи 2)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Обе правки нужны для выполнения СОБСТВЕННЫХ критериев плана; объём не расширен, файлы те же два.

## Issues Encountered

- Плановое действие задачи 2 и её же поведенческий список расходились на формах 2 и 3 (см. deviation 1). Разрешено введением флага, а не отказом от `isinstance`-пропуска: пропуск сам по себе — правильное поведение (чужая строка в перечне не должна отнимать дни на исправном плане), недоставало только следа.
- `uv run pytest tests/ -q` идёт ~17 минут; прогонялся дважды — до и после переформулировки докстринга (deviation 2), оба раза `1771 passed`.

## Known Stubs

Нет. Заглушек, пропущенных тестов и неисполненных `<verify>` план не оставил.

## Threat Flags

Нет новой поверхности: план не заводит эндпойнтов, путей аутентификации, файлового доступа и изменений схемы. Все восемь позиций реестра `<threat_model>` плана — `mitigate`, и все реализованы (T-05-104, T-05-188, T-05-189, T-05-190, T-05-191, T-05-192, T-05-193; T-05-SC неприменим — устанавливаемых пакетов ноль).

## Flagged Assumptions — состояние

Три допущения планировщика (E-01 BILL-05, E-02 BILL-06, E-03 BILL-07) остаются `unresolved` и подтверждены исполнением:

- **E-01** — семантика продления не менялась: тронуто только то, поднимается ли исключение вместо `None`; штатные исходы `_plan_price` закреплены прямым прогоном.
- **E-02** — показ осей при плане, выпавшем из `PLAN_LIMITS` (`IN-01`), не тронут; распоряжение принимает план `05-31`.
- **E-03** — состав строки истории платежей не тронут; добавлен только новый ключ журнала.

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- Блокер `CR-01` код-ревью раунда 7 (он же третий пункт `missing:` гэпа 1) закрыт с исполняемым свидетелем и доказанным порядком RED→GREEN.
- Открытым для плана `05-31` остаётся `parsed_message_packages` (та же форма отказа, цена — страница, а не застрявший платёж) и `IN-01` (показ осей при плане, выпавшем из перечня).

## Self-Check: PASSED

- `.planning/phases/05-tarify/05-28-SUMMARY.md` — существует на диске.
- `app/services/payment_service.py`, `tests/test_pages/test_billing_payment_errors.py` — существуют и изменены.
- Коммиты найдены в истории: `339fc97` (test), `b73fba0` (fix), `f91164a` (docs).
- `git status --short` пуст: несохранённых изменений не осталось.
- `STATE.md` и `ROADMAP.md` НЕ трогались — их пишет оркестратор после волны.

---
*Phase: 05-tarify*
*Completed: 2026-08-19*
