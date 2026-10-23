---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-23T12:33:28Z
depth: standard
review_kind: incremental
diff_base: 150a076dc0104205a514b94ecf93b96d741af203
batch_base: a8fb02c9
head: 2816cfb2
files_reviewed: 16
files_reviewed_list:
  - app/application/accounts/phone.py
  - app/logging_config.py
  - app/models/__init__.py
  - app/models/messenger_account.py
  - app/models/phone_guard.py
  - app/services/log_masking.py
  - app/services/phone.py
  - tests/phone_gate_grammar.py
  - tests/test_application/test_account_phone_race.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_application/test_phone_writer_runtime_guard.py
  - tests/test_logging_config.py
  - tests/test_models/test_messenger_account_phone_check.py
  - tests/test_phone_gates_parity.py
  - tests/test_phone_privacy_gate.py
  - tests/test_services/test_log_masking.py
findings:
  critical: 3
  warning: 4
  info: 3
  total: 10
carried_forward: 0
closed_prior: 6
status: issues_found
---

# Phase 16: Code Review Report (инкрементальное ревью партии раунда 10, 16-51…16-56)

**Reviewed:** 2026-10-23T12:33:28Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Инкрементальное ревью. Диапазон — `150a076d..2816cfb2`, база партии — `a8fb02c9`. В этом раунде впервые за несколько раундов изменился продуктовый код: защита писателя `app/models/phone_guard.py`, маска журнала `app/services/log_masking.py`, правки `app/logging_config.py`, `app/models/__init__.py` и писателя. Отчёт заменяет прежний `16-REVIEW.md`. Шесть находок раунда 9 стоят только в таблице диспозиций. Судил я свойства 1–6 решения О-23 (а), а не полноту написаний.

**Что проверено.** Все корпуса — мои, каталог `review-r10/` в scratchpad. Корпуса исполнителей не брал.
- **Тесты.** Пять малых модулей партии зелёные: `140 passed` (`uv run pytest tests/test_application/test_phone_writer_runtime_guard.py tests/test_services/test_log_masking.py tests/test_logging_config.py tests/test_models/test_messenger_account_phone_check.py tests/test_application/test_account_phone_race.py -q -p no:randomly`, под `flock`). Полную суиту не гонял: оркестратор намерил `5657 passed, 2 skipped`.
- **Коммиты.** Все 14 GREEN-коммитов из таблицы диспозиций — предки `HEAD` (`git merge-base --is-ancestor`): `ec3ef62e`, `0cae6ec4`, `270ad907`, `b758f763`, `535c4f20`, `0e74bf6c`, `e3ab5e03`, `fa3cfdfc`, `6b5ab496`, `d9ea00c2`, `69d73441`, `85af8e2f`, `e1eb00b4`, `03880243`.
- **Защита на исполнении** (`guard_runtime.py`, `scv_probe.py`). SQLite в памяти, async-сессия. 13 законных путей и 16 чужих записей. Законные пути: `BaseRepository.create/update` без колонок номера, UPDATE статуса, групповой UPDATE статуса по ключу, `select … where phone == x`, `refresh` после писателя, `record_reported_phone` и `set_manual_phone` с последующим сбросом, `merge`, `merge(load=False)`, `copy`, `deepcopy`, `pickle`, задача, созданная внутри разрешения.
  - Разрешение после исключения снимается. Номера в тексте отказа нет.
  - Ложный отказ один — `merge` (**WR-37**).
  - Запись проходит все рубежи у `bulk_*_mappings`, у исполнения через соединение и у держателей (**CR-08**), а также у `set_committed_value` на новом объекте (**WR-36**).
- **Маска** (`mask_corpus.py`, `perf_probe.py`, `perf2.py`, `dos_probe.py`, `celery_probe.py`, `dictmsg_probe.py`).
  - Видимым остаётся всё из О-24: ID групп `-100…` (со знаком, без знака и с `+`), JID групп, метки времени, UUID, порты, адреса, дроби, `account_id=42`, `-123456789`, кортеж и список ID групп — 21 форма из 22.
  - Маскируются 22 из 26 форм номера. Не маскируются NBSP, U+2011 и полноширинные цифры — их ручной путь нормализатора читает номером (**WR-39**). Четвёртая форма, `%2B7999…`, — номер, прилегающий к букве; это названный край грамматики.
  - Фильтр не роняет записи и сохраняет типы аргументов `%`.
  - Найдены две блокирующие проблемы. В воркерах Celery маски нет вовсе (**CR-06**). Сложность маски кубическая, и одна строка журнала с путём запроса длиной 3,6 КБ занимает 18 с (**CR-07**).
- **Канал запрета** (`static_writer.py`, `static_privacy.py`, `prior_probe.py`, `registry_probe.py`).
  - Формы прежних находок на `HEAD` красны каналом.
  - Правило реестра проверяет наличие конструкции, но исключение снимает все конструкции своего вида у владельца (**WR-38**).
  - Таблицы видов и двойников согласованы: правила паритета зелёные у оркестратора, в моих формах ложных находок канала нет.

**Открытая находка 16-54 / 16-55 — проверена своим корпусом и измерена (CR-08).** Она шире, чем описано: держатель через `setattr` с литеральным именем не нужен. Самая простая форма без единой динамической конструкции проходит все три рубежа и пишет строку:

```python
rows = [{"id": 1, "phone": x}]
session.bulk_update_mappings(MessengerAccount, rows)
```

Так же ведут себя `bulk_insert_mappings` и `conn.execute(update(MessengerAccount.__table__).values(fields))` с полями из переменной. Варианты `setattr` тоже есть: `setattr(B, "w", staticmethod(ss.bulk_update_mappings))`, `setattr(g, "w", …)` на функции, а без `setattr` — держатель `lambda`. Все дают 0 находок у предиката, 0 у канала и запись в базе, в том числе `phone_is_manual = True`. Это ровно тот «второй писатель — скрипт дозаполнения», ради которого существует D-13.

**Что партия сделала верно.**
- Канал запрета краснит все написания CR-05, WR-32 и WR-33 моего корпуса, включая не названные исполнителями: `from sys import modules as mm`, `sys.modules.get(__name__)`, `operator as op`.
- Защита закрывает все пути ORM: присваивание, конструктор, `setattr`, `del`, `flag_modified`, UPDATE/INSERT сессии, значения из переменной в `values(fields)` через `Session.execute`, а также `instance_dict` с отметкой истории вне писателя.
- Писатель обернул ровно два оператора, гонка зелёная.
- Регистрация последней строкой пакета моделей циклов не даёт. Миграции ORM-сессией не пользуются, поэтому на Alembic защита не влияет.

## Structural Findings (fallow)

Структурный пре-пасс не передан — раздел пуст.

## Prior findings — disposition

| ID | Title | State | Evidence |
|----|-------|-------|----------|
| CR-05 | Гейт приватности после цикла WR-29 плана 16-47 (`16573223`) читает имя вызываемого журнала членом объекта модуля только в двух написаниях — `self.me.out(account.phone)` и `_s.modules[__name__].out(…)` ловились на базе партии `d31d86db`, на `HEAD` — нет, номер печатается, гейт писателя те же формы ловит | closed | GREEN `ec3ef62e`, `0cae6ec4` (16-53), `270ad907`, `b758f763` (16-54), `535c4f20`, `0e74bf6c`, `e3ab5e03` (16-52) — предки `HEAD`. Мои формы на `HEAD` через `dynamic_construct_findings` с `BANNED_GETATTR_NAMES` приватности: `self.me = sys.modules[__name__]` + `self.me.out(…)`, `import sys as _s` + `_s.modules[__name__].emit(…)`, `from sys import modules as mm` + `mm[__name__].emit(…)`, `sys.modules.get(__name__).emit(…)` — у каждой находка вида «объект модуля»; прежний предикат — 0 (не правился, как велит О-23). Половина свойства 2 «маска на исполнении» в воркерах Celery не действует — это новая находка **CR-06**, а не повторное открытие CR-05: свойство 1 закрывает форму запретом. |
| WR-32 | `methodcaller(…)`, связанный где-либо в модуле под последним именем носителя, закрывает у гейта приватности путь носителя для поданного `methodcaller` над журналом — `asyncio.to_thread(f, logger)` при `to_thread = operator.methodcaller("noop")` не ловит ни одно дерево, гейт писателя ту же форму ловит | closed | GREEN `ec3ef62e`, `0cae6ec4`, `270ad907` — предки `HEAD`. Моя форма `import operator as op; to_thread = op.methodcaller('zzz'); g = op.methodcaller('error', '%s', account.phone); await asyncio.to_thread(g, log)` на `HEAD` — 2 находки вида «отложенный вызов по имени». |
| WR-33 | Имя носителя, связанное с функцией `getattr` или `operator.methodcaller`, гейт писателя переписывает в этот носитель опознания и судит только как его — `to_thread = getattr; asyncio.to_thread(set_committed_value, account, "phone", x)` не ловит ни одно дерево; у приватности то же для `methodcaller` и обёртки при `to_thread = operator.methodcaller` | closed | GREEN `ec3ef62e`, `0cae6ec4`, `fa3cfdfc`, `d9ea00c2`, `6b5ab496` (16-55), `69d73441`, `85af8e2f`, `e1eb00b4` (16-51) — предки `HEAD`. Мои формы на `HEAD`: `to_thread = getattr` + `asyncio.to_thread(scv, account, 'phone', x)` (псевдоним `set_committed_value as scv`) — 1 находка «отражение как значение»; `to_thread = operator.methodcaller` + `asyncio.to_thread(setattr, account, 'phone_is_manual', True)` — «отложенный вызов по имени» и «отражение как значение». Открытая находка, приложенная к диспозиции WR-33 (держатель `setattr` + `bulk_update_mappings`), — отдельная новая находка **CR-08**. Она измерена шире исходной формы. |
| WR-34 | Названные цены `COST-KW` и `kw_ext` шире охвата, который называет шапка писателя: две находки на одном узле колонки дают и `set_attribute`, `object.__setattr__`, `partial(set_committed_value\|flag_modified\|set_attribute\|object.__setattr__, other)`, и носители `executor.submit`, позиционный `enqueue`, `loop.call_soon`, `functools.partial(f, MessengerAccount.phone)()` | closed | GREEN `d9ea00c2`, `6b5ab496` — предки `HEAD`. Абзац цены по механизму стоит в шапке гейта писателя (`tests/test_application/test_phone_single_writer_gate.py:360`, `:374`), таблица `NAMED_COST_MECHANISM_CASES` на месте; правило шапки зелёное у оркестратора. О-23 (а), свойство 4: цена называется, а не снимается. |
| WR-35 | Правило T11c инструмента r9diff (`dup_collapse`, пункт 9) записывает в `REPAIRED` настоящее слияние двух узлов класса WR-27, если номер назван не ровно `phone` — «пол мест» считается регулярным выражением по тексту, а не правилом гейта | closed | Закрыта решением владельца О-23 (а), свойство 4: инструмент r9diff больше не мера фазы. Исправляющего коммита нет. Обе шапки называют это (GREEN `b758f763`, `6b5ab496` — предки `HEAD`); `grep -c "не мера фазы"` даёт 1 в `tests/test_phone_privacy_gate.py` и 1 в `tests/test_application/test_phone_single_writer_gate.py`. |
| IN-22 | Словарь девятого круга держит одного соперника на гейт (`print` / `update`) и только два написания объекта модуля, а докстринг паритета называет класс «толкование псевдонима, закрывающее путь носителя» покрытым целиком | closed | GREEN `03880243` — предок `HEAD`. Летопись «до плана 16-53 абзац относил к матрицам весь класс коллизии имени носителя (ревью IN-22)» стоит в `tests/test_phone_gates_parity.py:89`, правило текстов канала — в `:1387`. Прочие написания объекта модуля на `HEAD` красны каналом (см. строку CR-05). |

Примечание к строке WR-34: в заголовке четыре символа `|` внутри кода экранированы как `\|`. Иначе таблица Markdown разрезала бы ячейку. Сам текст заголовка не изменён.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-06: В воркерах Celery маски номера нет: Celery после `worker_init` заменяет обработчик корня своим и снимает и процессор `mask_numbers_in_event`, и фильтр `NumberMaskingFilter` — номер печатается целиком

**File:** `app/logging_config.py:56-69`; `app/services/log_masking.py:39-60`; вызов — `app/worker/celery_app.py:108-114`
**Issue:**
- **Механизм.** `setup_logging` зовётся из обработчика сигнала `worker_init`. В Celery 5 этот сигнал шлёт `WorkController.setup_instance` (`celery/worker/worker.py:127`). Сразу после него идёт `on_init_blueprint()` → `Worker.setup_logging()` → `app.log.setup()` → `setup_logging_subsystem`. У сигнала Celery `setup_logging` в проекте получателей нет, а `worker_hijack_root_logger` по умолчанию `True`. Поэтому Celery выполняет `root.handlers = []` (`celery/app/log.py:106-107`) и ставит свой `StreamHandler` с `ColorFormatter`. Обработчик маски пропадает.
- **Замер** (`celery_probe.py`: тот же порядок сигналов, `Worker(app=…)` из `celery.apps.worker`):
  ```
  AFTER worker_init: root handlers = [('StreamHandler', ['NumberMaskingFilter'], 'ProcessorFormatter')]
  AFTER Worker():    root handlers = [('StreamHandler', [], 'ColorFormatter')]
  [… INFO/MainProcess] {'phone': '+79991234567', 'event': 'wa_phone_reported', …}
  [… WARNING/MainProcess] raw number +79991234567
  ```
- **Охват.** Воркеры Celery — это очереди `telegram` и `default`. Там идут синк, опрос WA и отправки, то есть основной поток номеров от автоисточников. Свойство 2 О-23 («номер, дошедший до вывода журнала любым написанием, маскируется на исполнении») в этих процессах не выполняется. Шапка маски называет границей `scripts/`, `max_worker` и `wa_worker`, а воркеры Celery не называет. Процесс `beat` `setup_logging` не зовёт вовсе.
- **Почему это важно.** Формы, которые по сводкам 16-54 и 16-55 закрывает «только маска», — `setattr(self, "f", logger.info)`, `staticmethod(logger.info)`, держатель `lambda` (замер `static_privacy.py`: предикат 0, канал 0) — в коде задач Celery печатают номер, и ни один рубеж этого не видит.
- **Тесты.** `tests/test_logging_config.py` проверяет только вызов `setup_logging` в процессе pytest. Пути Celery нет ни в одном правиле.

**Fix:** подключить настройку к сигналу Celery `setup_logging`. Тогда Celery не захватывает корень. Это проверено: `celery_fix_probe.py` после `Worker()` оставляет `NumberMaskingFilter` и `ProcessorFormatter` и печатает `"phone": "+7 *** ***-**-67"`.
```python
from celery.signals import setup_logging as celery_setup_logging

@celery_setup_logging.connect
def setup_worker_logging(**kwargs):
    from app.config import get_settings
    from app.logging_config import setup_logging
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)
```
Альтернатива — `worker_hijack_root_logger=False` в `app.conf.update(...)`. Нужно правило, которое строит `celery.apps.worker.Worker` над приложением проекта и утверждает маску в выводе. Ещё нужно назвать `beat` в границе шапки или подключить и его.

### CR-07: Маска разбивки имеет кубическую сложность: строка журнала с путём запроса `/(1)%20(1)%20…` длиной 3,6 КБ блокирует цикл событий веб-процесса на 18 с — отказ в обслуживании без входа в систему

**File:** `app/services/log_masking.py:85` (`_SPACED_NUMBER`), `:129-162` (`_group_ends`, `_mask_spaced`); точка входа — `app/middleware.py:19-23, 41-45`
**Issue:**
- **Механизм.** `_SPACED_NUMBER` не ограничивает длину кандидата: `[0-9 \-()]*[0-9]`. На тексте из повторов `(1) ` каждая `(` — новое начало, и кандидат тянется до конца строки. На каждом кандидате `_mask_spaced` перебирает все концы групп (`_group_ends`), а на каждом префиксе заново считает `_digit_count(prefix)` за O(длины). Если кандидат не признан, поиск сдвигается на `match.start() + 1`. В сумме O(n³) по длине поля.
- **Собственные замеры** (`perf_probe.py`, `perf2.py`):

  | Повтор | Длина | Время |
  |--------|-------|-------|
  | `(1) ` | 1 600 | 5,7 с |
  | `(1) ` | 3 200 | 42,3 с |
  | `8 ` | 1 600 | 2,4 с |
  | `(12)` | 1 605 | 1,4 с |

  Цепочки `+1 ` и одни цифры линейны.
- **Путь атакующего.**
  - `RequestIdMiddleware` на каждом запросе кладёт `path=request.url.path` в контекст structlog и пишет событие `request` уровня INFO.
  - `scope["path"]` раскодирован, поэтому `%20` становится пробелом.
  - Замер через настоящий конвейер `setup_logging` (`dos_probe.py`): URL длиной 1 201 / 2 401 / 3 601 знак даёт `log.info` за 0,79 / 5,66 / **18,06 с**.
  - nginx по умолчанию пропускает строку запроса до 8 КБ. По кубу это около трёх минут на один запрос.
  - Запись журнала синхронна внутри `async dispatch`, поэтому стоит весь цикл событий процесса. В `docker-compose*.yml` uvicorn запущен без `--workers`.
  - Вход в систему не нужен: на несуществующий путь middleware тоже пишет событие.
- **Шапка.** Раздел «ГРАНИЦА» и правила маски о стоимости молчат. Тест на длинный вход отсутствует.

**Fix:** ограничить длину кандидата длиной номера и считать цифры префикса нарастающим итогом.
```python
# не больше E164_MAX_DIGITS цифр и ограниченное число разделителей
_SPACED_NUMBER = re.compile(
    _LEFT + r"(?:\+[0-9]|\([0-9]{1,5}\)|8(?=[ \-(]))(?:[ \-()]{0,3}[0-9]){6,15}" + _RIGHT
)
```
В `_mask_spaced` префиксы надо перебирать по заранее посчитанному массиву числа цифр. Нужно правило-замер: `mask_numbers("(1) " * 2000)` укладывается в, например, 50 мс. Ещё стоит обрезать значения полей журнала, например до 2 КБ, до маски.

### CR-08: Свойство 3 О-23 не выполняется для записи мимо событий ORM: `bulk_update_mappings` / `bulk_insert_mappings` / исполнение через соединение с полями из переменной или через держатель (`setattr` с литеральным именем, `staticmethod`, `lambda`) пишут номер и признак «ручной» — не ловит ни предикат, ни канал, ни защита

**File:** `app/models/phone_guard.py:10-12, 46-59`; `tests/test_application/test_phone_single_writer_gate.py:446-460, 545-551`; `tests/phone_gate_grammar.py:1675-1700` (`_call_kind`)
**Issue:** это открытая находка 16-54 / 16-55, проверенная своим корпусом. Обещание шапки защиты — «отказывает НА ИСПОЛНЕНИИ — в момент записи, каким бы написанием она ни была сделана» (`phone_guard.py:10-12`). Шапка гейта писателя утверждает, что для путей за границей защиты «статический гейт остаётся первым рубежом». Свойство 3 О-23 говорит: «формы в обход событий ORM закрывает свойство 1 запретом конструкции». Но предикат по своему пункту (1) поток данных не судит, а bulk-запись и `connection.execute` — не конструкция канала. Пересечение двух названных границ не закрыто ничем, и динамика для него не нужна.

Замер по трём рубежам: предикат — `judged_offences`, канал — `dynamic_construct_findings` с `BANNED_GETATTR_NAMES` писателя после реестра. «Защита» — исполнение формы на SQLite в памяти; в этой колонке указана строка в базе после `commit`.

| Форма (мой корпус) | Предикат | Канал | Защита: строка в базе |
|---|---|---|---|
| `rows = [{"id": 1, "phone": x}]; ss.bulk_update_mappings(MessengerAccount, rows)` | 0 | 0 | `('+79991234567', 0)` |
| то же, `rows` параметром функции | 0 | 0 | — (тот же путь) |
| `rows = [{…, "phone": x, "phone_is_manual": True}]; ss.bulk_insert_mappings(MessengerAccount, rows)` | 0 | 0 | вставлена строка с номером |
| `fields = {"phone": x}; conn = await s.connection(); await conn.execute(update(MessengerAccount.__table__)….values(fields))` | 0 | 0 | `('+79991234567', 0)` |
| `….values(**fields)` с `**fields` параметром | 0 | 0 | — (тот же путь) |
| `setattr(self, "f", ss.bulk_update_mappings); self.f(MessengerAccount, [{"id": 1, "phone": x}])` (форма 16-55) | 0 | 0 | `('+79991234567', 0)` |
| `setattr(self, "f", ss.bulk_insert_mappings); self.f(…)` | 0 | 0 | — (тот же путь) |
| `setattr(B, "w", staticmethod(ss.bulk_update_mappings)); B.w(MessengerAccount, [{…, "phone_is_manual": True}])` | 0 | 0 | `('+79991234567', 1)` |
| `setattr(g, "w", ss.bulk_update_mappings); g.w(…)` (атрибут функции) | 0 | 0 | — (тот же путь) |
| `w = lambda *a: ss.bulk_update_mappings(*a); w(MessengerAccount, [{"id": 1, "phone": x}])` | 0 | 0 | `('+79991234567', 0)` |
| контроль: `ss.bulk_update_mappings(MessengerAccount, [{'id': 1, 'phone': x}])` | 1 | 0 | `('+79991234567', 0)` |
| контроль: `fields = {"phone": x}; await s.execute(update(MessengerAccount)….values(fields))` | 0 | 0 | REFUSED, строка прежняя |

Другие варианты держателя через `setattr` с литеральным именем есть: держатель на классе через `staticmethod` и держатель на атрибуте функции. Без `setattr` то же даёт держатель `lambda`, а при данных из переменной держатель не нужен вовсе. Upsert `on_conflict_do_update(set_=fields)` с полями из переменной — то же пересечение: ветка `SET` лежит вне защиты, а поток данных — вне предиката. Его я не исполнял, вывод сделан по механизму. Строка с `phone_is_manual = True` — ровно ущерб D-07: автоисточник навсегда лишается права записи. Это не «ещё одно написание динамики» по свойству 5, а невыполненное обещание свойства 3 на самом простом написании. Самый вероятный второй писатель — скрипт дозаполнения Фазы 20 со списком строк — проходит все три рубежа. В живом дереве таких записей нет: правило писателя и канал дают 0.

**Fix:** судить таблицу, а не колонку, на путях, которые защита не видит. В гейте писателя:
- любой вызов `bulk_update_mappings` / `bulk_insert_mappings` / `bulk_save_objects`, у которого первым аргументом названа `MessengerAccount`, вне `PHONE_WRITER_EXCEPTIONS` — находка независимо от строк;
- `update(` / `insert(MessengerAccount.__table__)` с нелитеральными `values(…)` — находка;
- ссылка на `bulk_*_mappings`, связанная или поданная любым способом (`setattr`, `staticmethod`, `lambda`), — конструкция канала;
- на исполнении — слушатель `before_cursor_execute` движка: он видит компилированный UPDATE / INSERT по `messenger_accounts`, задающий `phone` / `phone_is_manual` вне `writer_scope()`. INSERT при этом судится по значениям: неизвестный номер и `phone_is_manual = False` законны.

Шапкам защиты и писателя назвать эти формы и снять «каким бы написанием она ни была сделана».

## Warnings

### WR-36: `before_flush` судит только историю атрибута, а INSERT нового объекта пишет его словарь — `set_committed_value(account, "phone", x)` на ещё не сохранённом аккаунте вставляет номер и `phone_is_manual = True`; утверждение шапки «оператора не порождает» ложно

**File:** `app/models/phone_guard.py:48-49, 123-139`
**Issue:** шапка защиты относит `set_committed_value` к границе с доводом «меняет только объект в памяти, оператора не порождает». Тест `wr33-set-committed-value-handed-to-a-carrier` проверяет это только на сохранённом объекте. Для объекта в `session.new` это неверно. ORM собирает параметры INSERT из `state.dict`, а `_refuse_unscoped_flush` смотрит лишь `history.added`, и после `set_committed_value` она пуста.
- Замер (`scv_probe.py`): `a = MessengerAccount(...)`, затем `set_committed_value(a, "phone", X)` и `set_committed_value(a, "phone_is_manual", True)`, затем `s.add(a)` и `commit`. В базе строка `(2, '+79991234567', 1)`.
- Литеральное написание ловит предикат (1 находка). Держатель `setattr(self, "f", set_committed_value); self.f(a, "phone", x)` даёт предикат 0, канал 0 и вставку в базу.

**Fix:** во второй линии для `session.new` судить значения, а не историю:
```python
state = sa_inspect(instance)
if state.pending or state.transient:
    values = state.dict
    if values.get("phone") is not None or values.get("phone_is_manual") is True:
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
```
Нужна строка теста «новый объект + `set_committed_value` + `add` → отказ». В шапке исправить довод о `set_committed_value`.

### WR-37: `session.merge(account)` любого загруженного аккаунта отказывает вне писателя, даже если номер не менялся — ложный отказ на стандартном пути ORM, шапка его не называет

**File:** `app/models/phone_guard.py:109-120`
**Issue:** `ColumnProperty.merge` при `load=True` переносит каждое загруженное значение через `impl.set(...)`, а это событие `set` колонок `phone` и `phone_is_manual`. `_refuse_attribute_write` отказывает без сравнения значения. Замер (`guard_runtime.py`, `L_merge_detached`): `get`, затем `expunge`, затем `await s.merge(a)` — `REFUSED`, при этом номер `None` и не менялся. `merge(load=False)` проходит. Сегодня в `app/` и `scripts/` `merge` не используется (`grep` — 0). Но это обычный способ перенести отсоединённый объект между сессиями, например в задаче Celery. Отказ придёт исключением `PhoneWriteOutsideWriter` на чтении-переносе, а не на записи. Шапка («ЧТО ОТКАЗЫВАЕТ») о `merge` молчит, `LEGITIMATE_WRITES` его не держит.

**Fix:** в слушателе `set` пропускать запись того же значения — для `set` событие получает `(target, value, oldvalue, initiator)`:
```python
def _refuse_attribute_set(target, value, oldvalue, initiator):
    if not _WRITER_ACTIVE.get() and value != oldvalue:
        raise PhoneWriteOutsideWriter(PHONE_WRITE_OUTSIDE_WRITER)
```
При этом надо регистрировать `set` с `active_history=True`, чтобы `oldvalue` был известен. Есть и другой путь — назвать `merge` в шапке и добавить строку в `LEGITIMATE_WRITES` / `FOREIGN_WRITES` с тем исходом, который решит владелец.

### WR-38: Исключение реестра канала снимает ВСЕ конструкции своего вида у владельца — новая `getattr(self.session, op)(…)` в `BaseRepository.update` проходит канал и предикат молча; правило реестра проверяет «хотя бы одну», а не число и не текст

**File:** `tests/phone_gate_grammar.py:1496-1525, 1777-1779`; `tests/test_phone_gates_parity.py:1271-1304`
**Issue:** ключ `<путь>::<владелец>::<вид>` снимает находки вида целиком (`exempt_dynamic_constructs`). `_dynamic_exception_problems` краснит только устаревшую запись, где конструкций 0. Замер (`registry_probe.py`): в живой `app/repositories/base.py` в тело `BaseRepository.update` вставлена строка `getattr(self.session, kwargs.get('op', 'add'))(type(entity), [kwargs])`. Это вычисленный вызов любого API сессии, включая `bulk_update_mappings`. Сырых находок канала 1 → 2, после реестра 0 → 0, предикат `[]`. Обещание свойства 1 — «в коде нет конструкции, которую гейт не умеет судить». Оно держится у шести владельцев только до первой правки их тела, и шапки этого не называют. Два исключения — `BaseRepository.update` и `update_schedule` — стоят в общих путях записи.

**Fix:** закрепить у записи число и текст конструкций. Пример значения реестра: `("причина", ("setattr(entity, field, value)",))`. Правило должно сверять множество `DynamicConstruct.text` у владельца с закреплённым: лишняя конструкция краснит, недостающая — тоже.

### WR-39: Маска пропускает записи, которые ручной путь нормализатора читает номером — разбивка через NBSP (`U+00A0`), неразрывный дефис (`U+2011`) и полноширинные цифры; граница шапки их не называет

**File:** `app/services/log_masking.py:77-87, 57-58`
**Issue:** О-24 (а) определяет «похожее на номер» как «подстрока, которую нормализатор фазы признаёт номером хотя бы одним путём». Замер (`mask_corpus.py`): `normalize_manual` даёт `+79991234567` на `'+7\xa0999\xa0123-45-67'`, на `'+7 999 123\u201145\u201167'` (U+2011) и на `'＋７９９９１２３４５６７'`. `mask_numbers` все три возвращает без изменений. Грамматика знает только ASCII-цифры и разделители `" -()"`. Шапка называет край «номер, разбитый не пробелом, `-` и скобками (`+7.999.123.45.67`)». NBSP читатель шапки примет за пробел, а неразрывный дефис — за дефис. Полноширинных цифр шапка не называет вовсе. Такие формы дают вставка из веб-страниц и профили мессенджеров.

**Fix:** перед поиском кандидатов приводить копию текста к ASCII (`unicodedata.normalize("NFKC", …)` переводит полноширинные цифры и `U+2011`; `\u00a0`, `\u2009`, `\u202f` отображать в пробел). Маску накладывать на исходные позиции, например через отображение индексов. Либо добавить эти знаки в `_SEPARATORS` и классы регулярных выражений, а полноширинные цифры — в класс цифр. Нужны строки таблицы маски и строки границы в шапке.

## Info

### IN-23: Автосброс оператора писателя идёт под его разрешением — вторая линия (`before_flush`) на нём выключена, и отложенные изменения колонок номера чужого кода сбрасываются как записи писателя

**File:** `app/application/accounts/phone.py:119-129, 221-224`; `app/models/phone_guard.py:131-132`
**Issue:** ORM-UPDATE в `session.execute` сначала делает автосброс. Он идёт внутри `with writer_scope()`, где `_refuse_unscoped_flush` сразу возвращается. Замер (`F_dirty_then_writer_autoflush`): история колонок помечена без события, через `instance_state(a)._modified_event(…)` и `instance_dict(a)[…]`. Затем `fill_reported_phone(…)`. В базе `('+79991234567', 1)`, то есть чужой «ручной» номер. Та же отметка без писателя отказывает (`F_dict_hist`: REFUSED). Нужен приватный API, поэтому это Info.
**Fix:** в писателе сбрасывать сессию до входа в разрешение (`await session.flush()` перед `with writer_scope()`) или исполнять операторы с `execution_options(autoflush=False)`.

### IN-24: Задача или поток, порождённые внутри `writer_scope()`, уносят разрешение навсегда — `finally` снимает переменную только в текущем контексте

**File:** `app/models/phone_guard.py:96-106`
**Issue:** `asyncio.create_task` и `asyncio.to_thread` копируют контекст. Замер (`L_task_inherits`): задача, созданная внутри разрешения и прочитавшая `_WRITER_ACTIVE` после выхода из него, видит `True`. Писатель задач не порождает, поэтому сегодня это не дыра. Но фраза шапки «снимается токеном в `finally`, и после исключения внутри тоже» читается шире, чем верно.
**Fix:** назвать это в шапке. Либо в правиле гейта писателя запретить внутри `with writer_scope():` вызовы, копирующие контекст (`create_task`, `to_thread`, `run_in_executor`, `ensure_future`).

### IN-25: `NumberMaskingFilter` пропускает без маски любую запись со словарём в `msg`, а не только запись structlog — на обработчиках uvicorn такой словарь печатается с номером

**File:** `app/services/log_masking.py:268-271`
**Issue:** признак `isinstance(record.msg, dict)` считает записью structlog любой словарь. На корне это безвредно: `ProcessorFormatter` маскирует `event`. На обработчиках uvicorn (обычный `Formatter`) — нет. Замер (`dictmsg_probe.py`): `logging.getLogger("uvicorn.error").error({"detail": "+79991234567"})` печатает `ERROR:    {'detail': '+79991234567'}`, а строковая запись того же журнала маскируется.
**Fix:** признак structlog — атрибуты записи `_logger` / `_name`, которые ставит `wrap_for_formatter`:
```python
if isinstance(record.msg, dict) and hasattr(record, "_logger"):
    return True
```
Иначе маскировать `record.msg = mask_numbers(str(record.msg))` через общий путь.

---

_Reviewed: 2026-10-23T12:33:28Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
