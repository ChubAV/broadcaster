---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
reviewed: 2026-10-21T21:22:27Z
depth: standard
review_kind: incremental
diff_base: 99c9f99c0490776bbbc5bb9dba6b13e83ecd78a0
batch_base: d31d86db
head: c69774cf
files_reviewed: 4
files_reviewed_list:
  - tests/phone_gate_grammar.py
  - tests/test_application/test_phone_single_writer_gate.py
  - tests/test_phone_gates_parity.py
  - tests/test_phone_privacy_gate.py
findings:
  critical: 1
  warning: 4
  info: 1
  total: 6
carried_forward: 0
closed_prior: 5
status: issues_found
---

# Phase 16: Code Review Report (инкрементальное повторное ревью партии раунда 9, 16-46…16-50)

**Reviewed:** 2026-10-21T21:22:27Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Инкрементальное ревью. Диапазон — `99c9f99c..c69774cf`. База партии — `d31d86db`; код гейтов там совпадает с `e9449db5`, который читал прошлый отчёт. Код четырёх файлов на `HEAD` совпадает с `e5090ac8` (`git diff --stat` пуст). С `99c9f99c` изменились только эти четыре файла. `app/`, `scripts/` и `main.py` не менялись, поэтому решения владельца IN-01…IN-05 (`deferred`) партия не задевает. Отчёт заменяет прежний `16-REVIEW.md`. Пять прежних находок стоят только в таблице диспозиций.

**Что проверено.**
- **Тесты.** Три модуля гейтов зелёные: `960 passed` (`uv run pytest tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly`, под `flock`). Полную суиту я не гонял.
- **Коммиты.** Все десять GREEN-коммитов из таблицы диспозиций — предки `HEAD` (`git merge-base --is-ancestor`): `cbcf07e1`, `472e30f6`, `16573223`, `7c077803`, `36248d38`, `533eb042`, `6d932a97`, `f7948e5b`, `8138ba46`, `e5090ac8`.
- **Живые деревья.** Обход 106 файлов: множество распознанных вызовов журнала на `d31d86db` и на `HEAD` одно и то же — 386 вызовов, новых 0, удалённых 0. Находок 0 у обоих гейтов.
- **Числа летописи словаря девятого круга.** Словарь `HEAD` (3 486 ячеек строк девятого круга, по 1 743 на гейт) я судил предикатами `d31d86db`. Промахов у приватности 153 (80 на носителях с соперником, 73 на формах коллизии и объекта модуля), у писателя 210 (все на носителях с соперником). На `HEAD` промахов 0. Числа шапок воспроизведены.

**Свой корпус** (`review-r9/work/gen.py`, `hand*.py`, `dupmini.py`). Генератор не берёт у `HEAD` ни `BINDING_FORMS`, ни `REFERENCE_CARRIERS`, ни значений опознания: шаблоны форм, носителей и значений у него свои. Ожидание выводится из исходника, а не из выхода гейта: это число узлов подачи. У приватности — узлы `Name` / `Attribute` с `phone`, строковые ключи и именованные аргументы с `phone`; у писателя — `.phone` / `.phone_is_manual` и константа `"phone"`. Каждое дерево (`d31d86db`, `fb8fef72`, `HEAD`) судится в отдельном процессе. Модули гейтов поднимаются из `git show` в scratch.
- **M — 33 075 ячеек.** Матрица «значение × форма × носитель × аргументы × раскладка счёта».
  - Приватность: 9 значений — `logger.info`, `print`, `getattr(logger, "info")`, `partial(logger.info, …)`, `logging.info`, `structlog.get_logger().info`, `methodcaller` над `logger`, `methodcaller` над `structlog.get_logger()`, получатель `logging.getLogger("x")`.
  - Писатель: 9 значений — `setattr`, `set_committed_value`, `flag_modified`, `object.__setattr__`, `partial(setattr, account)`, `methodcaller("__set__")` к `MessengerAccount.phone`, `methodcaller` с колонкой литералом, `methodcaller("__setattr__", "phone", x)`, получатель `account`.
  - 25 форм, из них 14 чтений через объект модуля: getattr-строка, с умолчанием, атрибут, имя, цепочка, `:=`, кортеж, имя в функции, `self.me`, `me` в теле класса, `import sys as _s`, `from sys import modules`, `sys.modules.get(__name__)`, `getattr(sys, "modules")[__name__]`.
  - 17 носителей, в том числе `executor.submit`, `Timer`, `apply_async`, `enqueue`, `starmap` и три вида обёртки.
  - 3 набора аргументов: один узел, два узла, `extra={"phone": …}`.
  - 3 раскладки: одна подача, две строки, две подачи на одной строке через `;`.
- **S — 11 025 безопасных двойников** (`phone` → `name` / `status`).
- **K — 51 300 ячеек: «одно имя — две роли» у обоих гейтов.**
  - Соперник связан под тем же последним именем в 6 местах: модуль до и после, функция, тело другого класса, чужой `__init__`, перевязка.
  - Соперники приватности: `print`, `logger.info`, `partial(logger.info)`, `setattr` (роль писателя), `sys.modules[__name__]`, получатель, обёртка носителя, `methodcaller("noop")`, `methodcaller("__set__")` писателя.
  - Соперники писателя: `setattr`, `update`, `set_committed_value`, `flag_modified`, `partial(setattr, other)`, `print` и `logger.info` (роль приватности), объект модуля, `methodcaller("noop")`, `methodcaller("info")` приватности.
  - Это × все значения × 5 форм × 10 носителей.
- **KC — 6 156 ячеек.** Те же соперники под последним именем вызова носителя в четырёх местах: модуль, функция, тело класса, чужой `__init__`.
- **Итого 101 556 уникальных ячеек.** Генератор выдал 132 336 строк, из них 30 780 — дубли KC по `id` и исходнику.
- **Ручные формы — 487.**
  - 85 — блоки прошлого отчёта (CR-04 C1–C7 и KC, WR-29 ×4 с двойниками через объект модуля, WR-30 ×7, WR-31 ×4), соседи WR-30 и пары писателя, ось счёта (`map` / `starmap` с двумя получателями, держатель-имя), кросс-гейтовые коллизии.
  - 144 — MCC: `methodcaller` под именем носителя.
  - 138 — CN: имя носителя связано с функцией `getattr`, `operator.methodcaller`, `functools.partial` или `operator.attrgetter`.
  - 91 — KWX: границы цены `kw_ext`.
  - 24 — KW: границы цены `COST-KW`.
  - 5 — ячейки правила T11c на деревьях `a6c87597` и `51d0d766`.

**Что мой корпус добавляет к r9diff** (`.pytest_cache/r9diff/corpus.json`, 156 352 ячейки, из них чужих 29 941). Я сверял по подстрокам исходников всего их корпуса. Ни одной ячейки у них нет для следующих осей:
- объект модуля в написании, отличном от `sys.modules[__name__]` и имени, связанного с ним: `self.me = sys.modules[__name__]`, `import sys as`, `from sys import modules`, `sys.modules.get(`, `getattr(sys, "modules")` — 0 вхождений;
- `methodcaller(…)` или функция `getattr` / `operator.methodcaller`, связанная под последним именем носителя, — 0;
- `executor.submit(` — 0;
- имена `user_phone` и `mobilePhone` — 0.

Каждая из этих осей ниже дала находку.

**Сверка по двум осям** (ячейка M/S/K/KC и ручная форма; ожидание — число узлов).

| Против | Регрессий наличия | Регрессий счёта | Исправлено к `HEAD` |
|--------|-------------------|-----------------|---------------------|
| `d31d86db` (база партии) | **4 266** ячеек корпуса + 2 ручные формы — все **CR-05** | 0 | 2 658: K/p 336 (класс CR-04 и C5–C7), KC/p 162, KC/w 936 (коллизия имени носителя), M/p 408 (WR-30), M/w 816 (WR-31) |
| `fb8fef72` (база раунда 8) | 0 | 0 | 14 924 |

Неверных ячеек: на `fb8fef72` — 19 896, на `d31d86db` — 3 424, на `HEAD` — **5 032**. По ячейкам моего корпуса `HEAD` хуже базы своей партии. Разбор неверных на `HEAD`:
- 4 266 — CR-05;
- 306 — получатель через те же написания объекта модуля (корень CR-05, не регрессия: 0 на всех деревьях);
- 112 — WR-32;
- 300 — `COST-KW`, названная цена;
- 48 — `kw_ext`: 36 внутри названного охвата, 12 вне его (WR-34);
- безопасных двойников с находкой — 0.

**Правило T11c инструмента r9diff (пункт 9, `dup_collapse`) несостоятельно** — WR-35. Пол мест считается регулярным выражением `\bphone(?!_set\b)\w*` по тексту, а гейт считает место предикатом `_mentions_phone` без учёта регистра и литералом, похожим на номер. Поэтому настоящее слияние WR-27 (`a6c87597 → 51d0d766`) инструмент записывает в `REPAIRED`, когда номер назван `a.user_phone`, `a.mobilePhone` или `a.PHONE` или стоит литералом: 4 ячейки из 5. Регрессией счёта остаётся только ровное написание `a.phone`.

**Что партия сделала верно.**
- Все пять прежних находок закрыты на собственных формах (таблица ниже).
- CR-04 и давний класс C5–C7 закрыты по всей оси K: 336 ячеек K/p исправлены, ни одной новой ошибки на K/p.
- WR-31: две подачи — две находки на всех раскладках M/w, в том числе `map` / `starmap` с двумя получателями.
- Гейт писателя теперь судит каждое толкование вызова с пишущим API под именем носителя: KC/w — 936 исправлены.

**Новые проблемы.**
- **CR-05** (регрессия наличия против базы партии, номер печатается). Цикл WR-29 (`16573223`) сузил чтение имени журнала до двух написаний объекта модуля. `self.me.out(account.phone)` при `self.me = sys.modules[__name__]` и `_s.modules[__name__].out(…)` при `import sys as _s` ловились на `d31d86db` и не ловятся на `HEAD`. Гейт писателя те же написания ловит.
- **WR-32.** `methodcaller(…)`, связанный под последним именем носителя, закрывает у приватности путь носителя для поданного `methodcaller` над журналом. Гейт писателя ту же форму ловит.
- **WR-33.** Имя носителя, связанное с функцией `getattr` или `operator.methodcaller`, гейт писателя переименовывает в этот носитель опознания и судит только как его (у приватности — для `methodcaller` и обёртки).
- **WR-34.** Цены `COST-KW` и `kw_ext` шире названного в шапке охвата.
- **WR-35.** Правило T11c прячет регрессию счёта класса WR-27.
- **IN-22.** Словарь девятого круга держит одного соперника на гейт и два написания объекта модуля, а докстринг паритета называет класс шире.

## Prior findings — disposition

| ID | Title | State | Evidence |
|----|-------|-------|----------|
| CR-04 | Гейт приватности после цикла 1 16-43 (`a77263ad`) пропускает `methodcaller` над журналом, если его последнее имя где-либо в модуле связано с вызываемым журнала, — регрессия наличия против `fb8fef72` и `1c243203`, номер печатается | closed | GREEN `cbcf07e1`, `472e30f6` (16-46) и `f7948e5b` (16-49) — предки `HEAD`. Ветка `continue` снята (`tests/test_phone_privacy_gate.py:1554-1561`). Формы блоков отчёта через `python_log_offences` на `HEAD`: C1 с `emit = print`, `emit = logger.info` и `def setup(): emit = print` — по **1** находке (`d31d86db` — 0, `fb8fef72` — 1); форма KC `to_thread = print; asyncio.to_thread(f, logger)` — **1** (0 / 1); C2 (getattr-строка), C5, C6, C7 и C7 в теле класса — по **1** (0 / 0). Ось K моего корпуса — 336 ячеек K/p исправлены, неверных K/p на `HEAD` — 0. |
| WR-29 | Та же правка `a77263ad` делает вызовом журнала метод любого чужого объекта с именем, связанным в модуле с вызываемым журнала, — ложные находки на законных формах, цена не названа | closed | GREEN `16573223`, `7c077803` (16-47) — предки `HEAD`. Четыре формы блока (`write = print; fh.write(account.phone)`, `info = logger.info; messages.info(…)`, `emit = logger.info; signal.emit(…)`, `send = print; bot.send(…)`) на `HEAD` дают **0** находок (`d31d86db` — 1). Их двойники через объект модуля (`sys.modules[__name__].write(…)`, `getattr(sys.modules[__name__], "write")(…)`) — **1**. Узость той же правки внесла новую регрессию — **CR-05**. |
| WR-30 | Получатель журнала, связанный с именем модуля и прочитанный через объект модуля (`getattr(sys.modules[__name__], "lg")`, `sys.modules[__name__].lg`), не ловится — шапка заявляет чтение связанного имени getattr-строкой, граница эту форму не называет | closed | GREEN `16573223`, `7c077803` (16-47), `f7948e5b`, `8138ba46` (16-49) — предки `HEAD`. Все семь форм блока на `HEAD` дают по **1** находке (`d31d86db` и `fb8fef72` — 0): getattr-строка, с умолчанием, атрибут, цепочка `r = …`, `me = sys.modules[__name__]`, `emit(getattr(…))`, `asyncio.to_thread(getattr(…).info, …)`. Соседние написания объекта модуля (`self.me`, `import sys as _s` …) по-прежнему 0 — это часть **CR-05**. |
| WR-31 | Гейт писателя сливает два применения `methodcaller` с колонкой в получателе (`f(MessengerAccount.phone)` дважды) в одну находку на строке связывания, а мера 16-44 записала 190 таких ячеек в «REPAIRED» | closed | GREEN `36248d38`, `533eb042`, `6d932a97` (16-48) — предки `HEAD`. Формы блока через `phone_write_offences` на `HEAD`: две строки — **2** (`:5`, `:6`); одна строка — **2**; блок `go` / `go2` — **2** (`:8`, `:10`; `d31d86db` — 1); контроль литерала колонки — **1**. M/w моего корпуса — 816 ячеек раскладок «две подачи» исправлены, неверных M/w на `HEAD` — 0. |
| IN-21 | Летописи словаря восьмого круга обеих шапок утверждают итог меры «число находок у обоих гейтов не меньше, чем у родителя и у базы, кроме исправленного пересчёта одного места — класс WR-24», а замер его опровергает | closed | GREEN `e5090ac8` (16-49) — предок `HEAD`. Фразы-итога нет ни в одной шапке (`grep -c` = 0; в `tests/test_phone_gates_parity.py` она стоит только константой `REFUTED_MEASURE_CLAIM`). Летописи восьмого круга (`tests/test_phone_privacy_gate.py:385-395`, `tests/test_application/test_phone_single_writer_gate.py:595-602`) называют корпус меры: 64 483 ячейки, `fd55d467…`, без k / kc / fp / dw. Правило `test_the_dictionary_chronicles_name_what_the_measure_compared` зелёное. Числа летописи девятого круга (153 / 210) воспроизведены. |

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-05: Гейт приватности после цикла WR-29 плана 16-47 (`16573223`) читает имя вызываемого журнала членом объекта модуля только в двух написаниях — `self.me.out(account.phone)` и `_s.modules[__name__].out(…)` ловились на базе партии `d31d86db`, на `HEAD` — нет, номер печатается, гейт писателя те же формы ловит

**File:**
- `tests/test_phone_privacy_gate.py:882-893` — `_is_module_object`. Объект модуля — `ast.unparse(node) == "sys.modules[__name__]"` или `ast.Name` из `module_objects`.
- `tests/test_phone_privacy_gate.py:896-911` — `_module_object_names` берёт только цели `ast.Name`. Цель `self.me = …` не учитывается. Имя `me` из тела класса учитывается, но чтение `self.me` / `K.me` — атрибут, и `_is_module_object` его не признаёт.
- `tests/test_phone_privacy_gate.py:1005` — ветка (а) `_log_function_reference`. `:1139` — `_bind(target, in_class_body, …)`: до `16573223` здесь стояло `True`, и имя читалось у любого владельца.
- Заявления:
  - шапка `:78-83` — «Связанное имя читается и через объект модуля: … — член `sys.modules[__name__]` и имени, связанного с ним»;
  - граница `:509-512` — «объект самого модуля — `sys.modules[__name__]` и имя, связанное с ним, — чужим объектом не считается: его члены, связанные в модуле, ловятся»;
  - докстринг `ModuleLogNames` `:841-843` — «`module_objects` — имена, связанные в модуле с объектом модуля … **любой формой общей грамматики**»;
  - шапка `:46-47` — «расхождение гейтов краснит правило-паритет».
- Сводка 16-47 («Атрибут `self.me = sys.modules[__name__]` объектом модуля не считается; эта форма вне ревью») это сужение сделала. Ни шапка, ни граница его не называют.

**Issue:** Регрессия наличия против базы своей партии. Исполнено (Python 3.12; модули в scratch `review-r9/exec/`):
```python
import sys
out = print
class K:
    def __init__(self):
        self.me = sys.modules[__name__]
    def go(self, account):
        self.me.out(account.phone)        # d31d86db: 1   HEAD: []   stdout: '+79991234567'
```
```python
import sys as _s
out = print
def go(account):
    _s.modules[__name__].out(account.phone)   # d31d86db: 1   HEAD: []   stdout: '+79991234567'
```
Масштаб в моём корпусе — **4 266 ячеек**. Это шесть написаний объекта модуля: `self.me`, `me` в теле класса через `self.me`, `import sys as _s`, `from sys import modules`, `sys.modules.get(__name__)`, `getattr(sys, "modules")[__name__]`. Они взяты с каждым вызываемым журнала: `logger.info`, `print`, `getattr(logger, "info")`, `partial(logger.info, …)`, `logging.info`, `structlog.get_logger().info` — × 17 носителей × аргументы × раскладки. На `d31d86db` все 4 266 верны, на `HEAD` у всех `[]`.
- На `fb8fef72` эти ячейки тоже 0. Их поймал плоский `a77263ad`, а 16-47 потерял. Поэтому это регрессия против базы партии, а не против базы раунда 8.
- Гейт писателя ловит все шесть написаний у всех своих значений (M/w — 0 неверных), потому что его имя плоское (`reading_name`). Гейты расходятся, и правило-паритет этого не видит: словарь держит только `sys.modules[__name__]` и `me = sys.modules[__name__]`.
- Тот же корень у получателя (продолжение WR-30, не регрессия). `self.me.lg.info("x %s", account.phone)` при `lg = logging.getLogger("x")`: `logging` печатает `LOG x +79991234567`, а гейт даёт 0 на всех трёх деревьях. В корпусе таких ячеек 306.

Мера партии этого не видела по построению: в корпусе r9diff нет ни одного из шести написаний. «REPAIRED» 16-47 (1 991 ячейка, 1 → 0) — только ложные находки на чужих объектах; настоящих вызовов журнала среди них нет. Заодно о прошлом отчёте: его пример помощника для WR-29 (`ast.unparse(node) == "sys.modules[__name__]"  # плюс имена, связанные с этим выражением`) был так же узок. Это не делает потерю названной починкой.

**Fix:** Признавать объект модуля по семантике, а не по одному тексту. Имена брать у цели любой формы общей грамматики (плоско по последнему звену, как у прочих имён гейта):
```python
def _module_object_names(bindings: list[Binding]) -> frozenset[str]:
    found: set[str] = set()
    changed = True
    while changed:
        changed = False
        known = replace(NO_MODULE_LOG_NAMES, module_objects=frozenset(found))
        for target, value, _in_class_body in bindings:
            name = binding_name(target)              # me, self.me → "me"; тело класса тоже
            if name is not None and name not in found and _is_module_object(value, known):
                found.add(name)
                changed = True
    return frozenset(found)


def _is_modules_mapping(node: ast.expr) -> bool:
    # sys.modules, _s.modules (import sys as _s), modules (from sys import modules), getattr(sys, "modules")
    return reading_name(node) == "modules"


def _is_module_object(node: ast.expr, names: ModuleLogNames = NO_MODULE_LOG_NAMES) -> bool:
    name = reading_name(node)
    if name is not None and name in names.module_objects:        # me, self.me, K.me, getattr(self, "me")
        return True
    if isinstance(node, ast.Subscript):                            # <modules>[__name__]
        return ast.unparse(node.slice) == "__name__" and _is_modules_mapping(node.value)
    if isinstance(node, ast.Call) and node.args and ast.unparse(node.args[0]) == "__name__":
        member = _member(node.func)                                # sys.modules.get(__name__)
        return (member is not None and member[1] == "get" and _is_modules_mapping(member[0])) or (
            reading_name(node.func) == "import_module"             # importlib.import_module(__name__)
        )
    return False
```
Добавить в `BINDING_FORMS` строки `module-object-self-attribute` (`self.me = sys.modules[__name__]`, ссылка `self.me.f`) и `module-object-import-alias` (`import sys as _s`, ссылка `_s.modules[__name__].f`), чтобы обе матрицы и паритет держали эти формы. Две формы выше и `self.me.lg.info(…)` вписать в `NEGATIVE_CONTROLS`, а шесть написаний — в корпус меры. Если какое-то написание оставить вне охвата, его надо назвать в границе с доводом и снять «любой формой общей грамматики» из докстринга `ModuleLogNames`.

## Warnings

### WR-32: `methodcaller(…)`, связанный где-либо в модуле под последним именем носителя, закрывает у гейта приватности путь носителя для поданного `methodcaller` над журналом — `asyncio.to_thread(f, logger)` при `to_thread = operator.methodcaller("noop")` не ловит ни одно дерево, гейт писателя ту же форму ловит

**File:**
- `tests/test_phone_privacy_gate.py:1473-1477` — `_applied_log_methodcaller`. `applied = named(call.func)` читает последнее имя носителя (`to_thread`, `run`, `Thread`, `map`) плоско. Если под ним связан ЛЮБОЙ `methodcaller(…)`, ветка `if applied:` берёт вызов только как применение (при одном позиционном аргументе), а `elif as_carrier` с путём носителя не идёт.
- Гейт писателя: `tests/test_application/test_phone_single_writer_gate.py:1903-1914`, `_methodcaller_receivers`. Применение закрывает путь носителя только при одном аргументе (`continue`), иначе путь носителя идёт.
- Заявления: шапка `:60-63` — «каждое толкование узла: вызов, опознанный вызовом журнала, судится и как применение `methodcaller` и обёртки носителя…»; шапка `:179-196` — `methodcaller` «поданный ЛЮБОМУ носителю, — применяется к первому аргументу, который носитель подаст ссылке»; решение владельца О-20 (а), свойство 2 — «гейты по этой оси сходятся».

**Issue:** Тот же класс, что CR-04 («одно толкование закрывает другое»), но в пути `methodcaller`, а не в ветке опознанного вызова. Исполнено:
```python
import asyncio, logging, operator
logger = logging.getLogger("y")
to_thread = operator.methodcaller("noop")      # или run = operator.methodcaller("run"), class A: Thread = …
async def go(account):
    f = operator.methodcaller("info", "x %s", account.phone)
    await asyncio.to_thread(f, logger)         # fb8fef72 / d31d86db / HEAD: []   logging: 'LOG x +79991234567'
```
Ручное семейство MCC — 72 ячейки приватности: 3 значения соперника (`methodcaller("noop")`, `methodcaller("info", "y")`, `methodcaller("__set__", account, x)` писателя) × 4 места × 6 носителей (`to_thread`, `run_in_executor`, `Thread`, `submit`, `Context.run`, `map`). Все дают 0 на трёх деревьях. Их писательские пары — 72 из 72 по одной находке. В корпусе KC неверны ещё 112 ячеек этого класса на 7 носителях: верны только `wrapper-named` и `partial-applied`. Регрессии нет. Словарь девятого круга этой формы не собирает: соперник приватности у каждого значения — только `print` (см. IN-22).

**Fix:** Применение и путь носителя — независимые толкования одного узла. Повтор места снимет дедупликация по узлу 16-41:
```python
applied = named(call.func)
if applied and len(call.args) == 1 and not isinstance(call.args[0], ast.Starred) and not call.keywords:
    candidates = [(methodcaller, call.args[0]) for methodcaller in applied]
if as_carrier and _last_name(call.func) not in names.methodcaller_names:   # было: elif
    for carried in reference_arguments(...):
        ...
```
Вписать форму выше и её вариант с `run = operator.methodcaller("run")` / `ctx.run(f, logger)` в `NEGATIVE_CONTROLS`. Дать словарю второго соперника на носителе (`methodcaller`) — см. IN-22.

### WR-33: Имя носителя, связанное с функцией `getattr` или `operator.methodcaller`, гейт писателя переписывает в этот носитель опознания и судит только как его — `to_thread = getattr; asyncio.to_thread(set_committed_value, account, "phone", x)` не ловит ни одно дерево; у приватности то же для `methodcaller` и обёртки при `to_thread = operator.methodcaller`

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:1168-1170` — `_rename_aliases(tree, carrier)` для `IDENTIFICATION_CARRIERS = ("methodcaller", "getattr")` (`:786`). Переписывает КАЖДОЕ чтение с последним именем псевдонима, в том числе `asyncio.to_thread` → `Name("getattr")`.
- `:2096-2107`, `:2133-2134` — ранние возвраты `_referenced_calls` для `methodcaller` и `getattr`. После переименования вызов носителя попадает в них, и путь носителя не идёт.
- Приватность: `tests/test_phone_privacy_gate.py:1374-1376` (`_not_carriers` включает псевдонимы `methodcaller`) и `:1477` (`_last_name(call.func) not in names.methodcaller_names`).
- Заявления: шапка писателя `:396-408` («ссылка — поданная любому вызову, носители `REFERENCE_CARRIERS` включительно») и `:326-330` («Судится каждое толкование вызова…»). Пункты (1)–(5) границы эту форму не называют. Докстринг `_referenced_calls` (`:2085-2087`) объясняет ранний возврат применением `getattr(…)(…)` и `methodcaller` у себя, а не переименованным носителем.

**Issue:** Ручное семейство CN — 138 форм: 4 соперника × 3 места × 6 способов × 2 гейта. Ноль находок на `fb8fef72`, `d31d86db` и `HEAD` у **39** форм:
- писатель, `getattr` — 15: `to_thread`, `run_in_executor`, `Context.run`, `Thread`, обёртка `partial(asyncio.to_thread, …)(…)`;
- писатель, `operator.methodcaller` — 18: те же пять и поданный `methodcaller("__set__")`;
- приватность, `operator.methodcaller` — 6: поданный `methodcaller` и обёртка.

Те же формы у приватности с `to_thread = getattr` ловятся (`asyncio.to_thread(logger.info, "x %s", account.phone)` — 1), а у писателя нет: гейты расходятся. Регрессии нет. Форма редкая, но это ровно ось «одно имя — две роли» на носителе, которую партия закрывала планом 16-48. Самопроверка (к6) / (к9) брала соперником только пишущий API.

**Fix:** Не переписывать дерево разрушительно. Помнить исходное последнее имя вызова и судить оба толкования:
```python
# _rename_aliases: вместо замены узла — запись в карту id(узла) → каноническое имя
canonical_of: dict[int, str] = {}
...
name = _call_name(call)                         # исходное последнее имя: "to_thread"
canonical = canonical_of.get(id(call.func))     # "getattr" у псевдонима
if canonical == "getattr" or name == "getattr":
    applications += []                          # применение getattr(…)(…) судит внешний вызов
    if name != "getattr":                       # псевдоним под именем носителя — ещё и носитель
        return applications + carried_writes(call)
    return applications
```
Вписать `to_thread = getattr` и `to_thread = operator.methodcaller` с поданной ссылкой в `LITERAL_FORM_CASES`, а форму приватности — в `NEGATIVE_CONTROLS`. Если вне охвата, то назвать в пункте (1) границы обоих гейтов с доводом.

### WR-34: Названные цены `COST-KW` и `kw_ext` шире охвата, который называет шапка писателя: две находки на одном узле колонки дают и `set_attribute`, `object.__setattr__`, `partial(set_committed_value|flag_modified|set_attribute|object.__setattr__, other)`, и носители `executor.submit`, позиционный `enqueue`, `loop.call_soon`, `functools.partial(f, MessengerAccount.phone)()`

**File:**
- `tests/test_application/test_phone_single_writer_gate.py:331-350` — абзац цены. Цена kw: «имя, связанное с `functools.partial(setattr, other)` и с `operator.methodcaller("__set__", account, x)`». `kw_ext`: «пишущий API соперника (`setattr`, `set_committed_value`, `flag_modified`), связанный с последним именем носителя (`to_thread`, `run_sync`, `Context.run`, `to_thread(*[…])`)… носители, у которых ссылка не первым аргументом (`run_in_executor`, `Thread`, `Timer`, `enqueue`, `starmap`, `apply_async`, `map`, обёртки), пары не дают (замер плана 16-48: 156 форм…)».
- `:7568-7576` — комментарий `NAMED_COST_CASES`: «Строка на каждый API соперника, дающий пару (`setattr`, `set_committed_value`, `flag_modified`; …)».
- Решения владельца, которые задают охват: О-20 (а) свойство 8 и «Принять как цену» 2026-10-21 (в постановке ревью — `setattr` / `set_committed_value` / `flag_modified` под `to_thread` / `run_sync` / `Context.run`).

**Issue:** Число находок вне названного охвата. Регрессии нет: на `d31d86db` то же число 2, тогда на двух строках. `HEAD` (путь `scripts/x.py`), находки дословно:
```python
submit = setattr
f = operator.methodcaller("__set__", account, x)
executor.submit(f, MessengerAccount.phone)
# :7 — запись атрибута по имени — setattr(…, MessengerAccount.phone, …)
# :7 — запись атрибута по имени — MessengerAccount.phone.__set__(…)
```
```python
f = functools.partial(set_committed_value, other)
f = operator.methodcaller("__set__", account, x)
f(MessengerAccount.phone)
# :7 — … set_committed_value(…, MessengerAccount.phone, …)
# :7 — … MessengerAccount.phone.__set__(…)
```
Замер:
- **KWX — 28 форм с двумя находками вне охвата.** Соперники `setattr`, `set_committed_value`, `flag_modified` × носители `submit`, позиционный `enqueue(f, C)`, `call_soon`, `partial(f, C)()` — 12. Соперники `set_attribute` и `object.__setattr__` × все 8 носителей с ссылкой первым аргументом — 16. Внутри охвата 12 форм.
- **KW — 15 форм вне охвата.** `partial(set_committed_value | flag_modified | set_attribute | object.__setattr__, other)` и голое `f = object.__setattr__`, каждое в 3 местах. Внутри охвата 3 формы `partial(setattr, other)`.
- **KC корпуса — 12 ячеек.** `partial = <соперник>` и `functools.partial(f, MessengerAccount.phone)()`.

Настоящий охват по механизму — любой API из `NAMED_ATTRIBUTE_WRITERS` под последним именем вызова, у которого ссылка `methodcaller` стоит первым позиционным аргументом. Фраза «`enqueue` … обёртки … пары не дают» верна только для словарной формы `enqueue(job=…)` и обёртки носителя, а не для позиционного `enqueue` и применённого `partial(f, …)()`.

**Fix:** Либо показать владельцу охват по механизму — с этим замером и списком форм — и тогда переписать абзац цены и комментарий `NAMED_COST_CASES` по механизму, а `NAMED_COST_CASES` расширить строкой на каждого соперника (`set_attribute`, `object.__setattr__`) и на каждый вид носителя (`submit`, позиционный `enqueue`, `partial(f, C)()`). Либо свести эти формы к одной находке: толкование соперника не судить, когда «колонка» на месте имени атрибута пришла получателем поданного `methodcaller`. Пока решения нет, абзац должен называть настоящий охват, а не 156 форм самопроверки.

### WR-35: Правило T11c инструмента r9diff (`dup_collapse`, пункт 9) записывает в `REPAIRED` настоящее слияние двух узлов класса WR-27, если номер назван не ровно `phone` — «пол мест» считается регулярным выражением по тексту, а не правилом гейта

**File:**
- `.pytest_cache/r9diff/judge.py:65-82` — инструмент вне git, но на нём стоит итог меры партии. `PHONE_TOKENS = re.compile(r"\bphone(?!_set\b)\w*")`, `place_floor` = число совпадений в исходнике, `dup_collapse` = «то же множество текстов, каждый один раз, число ≥ пола».
- Гейт считает место иначе: `_mentions_phone` (`tests/test_phone_privacy_gate.py:796-797`) берёт `"phone" in name.lower()`, литерал судит `phone_like` (`:785-793`).
- Заявления, которые опираются на меру: летописи словаря девятого круга (`tests/test_phone_privacy_gate.py:424-440`, `tests/test_application/test_phone_single_writer_gate.py:619-635`) и докстринг паритета (`tests/test_phone_gates_parity.py:84-88`) — «сверила … по наличию находки и по их числу».

**Issue:** Контроль 16-49 (`dup_control.sh`) проверял единственное написание `a.phone`, у которого пол равен 2. Мой прогон их же `judge.py` (только чтение) на настоящих деревьях WR-27 — `a6c87597` (до слияния) и `51d0d766` (слияние по тексту). Пять ячеек с `expect: null`:
```
RV a6c87597 -> 51d0d766: cells=5 regressions=0 count_regressions=1 fixed=0 repaired_overcount=4 changed=5
  COUNT_REGRESSED rv::WR27-merge 2 -> 1                                   # logger.info("%s %s", a.phone, b.phone)
  REPAIRED rv::WR27-user_phone 2 -> 1 rule=повтор-текста                  # a.user_phone, b.user_phone   (пол 0: «_p» — не граница \b)
  REPAIRED rv::WR27-mobilePhone 2 -> 1 rule=повтор-текста                 # a.mobilePhone, b.mobilePhone (регистр)
  REPAIRED rv::WR27-PHONE 2 -> 1 rule=повтор-текста                       # a.PHONE, b.PHONE
  REPAIRED rv::WR27-literal 2 -> 1 rule=повтор-текста                     # "+79991234567" дважды (литерал без «phone»)
```
Четыре из пяти настоящих регрессий счёта (`logging` печатает оба номера) правило закрывает как «исправленный пересчёт». В итоговом корпусе 16-49 правило сработало ровно на T11c, поэтому числа партии верны. Но строка `count_regressions=0` будущих прогонов для этих написаний — вакуум. Это ровно класс WR-27, против которого ось счёта и вводилась (свойство 6 О-18 (а)).

**Fix:** Пол мест считать правилом гейта: число узлов, которые судит `_judge_arguments` (имя / атрибут / ключ / именованный аргумент по `_mentions_phone`, литерал по `phone_like`, `mask_phone(…)`), а у писателя — узлы колонки. Надёжнее — хранить в вердикте v3 место со столбцом (`(строка, столбец, вид, предмет)` гейт и так считает) и сжатие признавать только при совпадении множеств мест, а не текстов. Добавить в `dup_control` четыре ячейки выше с ожиданием `COUNT_REGRESSED`.

## Info

### IN-22: Словарь девятого круга держит одного соперника на гейт (`print` / `update`) и только два написания объекта модуля, а докстринг паритета называет класс «толкование псевдонима, закрывающее путь носителя» покрытым целиком

**File:** `tests/test_phone_gates_parity.py:75-88` (особенно `:83-85`: «…и толкование псевдонима, закрывающее путь носителя (коллизия имени носителя), краснят матрицы и правило-паритет»); `:605-622` (`_round_nine_rival_problems` требует соперника приватности только вызываемым журнала, писателя — только пишущим API); `tests/phone_gate_grammar.py:376-382` (три формы `module-object-*` — `sys.modules[__name__]` и `me = sys.modules[__name__]`).

**Issue:** Классы WR-32 (соперник — `methodcaller` под именем носителя), WR-33 (соперник — функция `getattr` / `methodcaller`) и CR-05 (объект модуля в других написаниях) проходят обе матрицы и паритет: `960 passed` при 4 266 + 112 + 39 неверных ячейках моего корпуса. Абзац докстринга утверждает класс шире словаря — тот же вид неправды, который IN-21 снял с летописей.

**Fix:** Либо дать словарю второго соперника на носителе (`methodcaller(…)` у приватности, функцию `getattr` у писателя) и строки объекта модуля из CR-05, либо сузить абзац до «для соперника `print` / `update` и написаний `sys.modules[__name__]`, `me = sys.modules[__name__]`».

---

_Reviewed: 2026-10-21T21:22:27Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard (incremental, diff base `99c9f99c`, batch base `d31d86db`, head `c69774cf`)_
