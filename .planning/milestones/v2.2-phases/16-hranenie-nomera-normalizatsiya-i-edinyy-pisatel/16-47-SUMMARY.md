---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 47
subsystem: testing
tags: [privacy-gate, phone, ast, module-object, base-head-diff, foreign-corpora, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт приватности 16-01…16-46 (суд каждого толкования узла 16-46); инструмент r9diff 16-46 (копия оркестратора)"
provides:
  - "помощник _is_module_object и поле ModuleLogNames.module_objects: имя модуля, связанное с вызываемым журнала, — член только объекта модуля (WR-29); член объекта модуля, связанный с получателем, — получатель (WR-30)"
  - "трасер test_a_planted_trace_through_the_module_object_reddens_the_gate_and_a_file_export_does_not; 8 строк NEGATIVE_CONTROLS, 6 строк POSITIVE_CONTROLS"
  - "шапка гейта приватности: чтение через объект модуля в «ПО СВЯЗЫВАНИЮ», названная цена атрибута О-22 (а) рядом с `log.mark_failed(…)` и `other.bum(…)`, уточнение границы, летописи WR-29 и WR-30; правило шапки с новыми местами"
  - "инструмент .pytest_cache/r9diff/ (gitignored): семейство (к8) «одно имя — две роли», самопроверка 16-47 (12 444 формы), cost_evidence.py, cost_ids.py, строки COST-ATTR-IDS и EVIDENCE в run.sh"
affects: [16-48, 16-49, 16-50]

actuals:
  tokens: 16300   # chars/4: отслеживаемый дифф 38 724 знака (≈9 700) + своё в gitignored-инструменте ≈26 600 знаков (≈6 600)
  tasks: 2
  commits: 4      # git rev-list --count 35106de1..7c077803 (до коммита сводки)
plan_head_before: 35106de19dd748ed2c698e3cbe83ebab2e81fdd9
plan_head_after: 7c07780397c535f463993342d3eeb59d378994ed

tech-stack:
  added: []
  patterns:
    - "Член объекта модуля — одна проверка `_is_module_object` для вызываемого журнала и для получателя; атрибут — плоский по владельцу (названная цена)"
    - "Корпус сверки растёт семейством коллизий своей оси до доверия GREEN; самопроверка судится целиком на HEAD и на базе"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Имя вызываемого журнала, связанное на уровне модуля или в функции, в log_function_attributes не идёт (как до a77263ad); чтение getattr-строкой через объект модуля даёт ветка члена _log_function_reference"
  - "Атрибут, связанный с вызываемым журнала, судится у любого объекта — цена О-22 (а) названа в шапке, закреплена строкой log-callable-attribute-called-on-a-parameter и уликой исполнения"
  - "Ожидание своего семейства (к3) у значения partial исправлено по шапке: сам functools.partial(logger.info, \"y\") на строке связывания — вызов журнала; ожидание чужих корпусов не трогалось"

patterns-established:
  - "run.sh печатает рядом со строкой COST перечень id названной цены (COST-ATTR-IDS) и улику исполнения (EVIDENCE attr), а контроль против вакуума перехвата — в stderr"

requirements-completed: []   # PHONE-21 в requirements плана; отметку Complete не ставим — вердикт фазы gaps_found, учёт ведёт оркестратор

coverage:
  - id: D1
    description: "Семь форм WR-30 (получатель журнала модуля через объект модуля) — по одной находке phone; четыре формы WR-29 (fh.write, messages.info, signal.emit, bot.send) — не вызов журнала; двойники верны; матрица 1 638 ячеек — по одной"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (8 новых строк) и #test_a_recommended_form_does_not_redden_the_python_half (6 новых строк)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK 12 6 1638"
        status: pass
    human_judgment: false
  - id: D2
    description: "Трасер: подложенный app/services/phone_trace.py даёт ровно одну находку :8, соседний phone_export.py — ноль находок и ни одного вызова журнала"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_trace_through_the_module_object_reddens_the_gate_and_a_file_export_does_not"
        status: pass
    human_judgment: false
  - id: D3
    description: "Шапка называет чтение через объект модуля, цену атрибута О-22 (а) с замером живого дерева и летописи WR-29 / WR-30; правило шапки держит эти места"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_header.py → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Цена COST-ATTR подтверждена исполнением (номер в файле, журнал пуст; контроль против вакуума перехвата); 122 чужие ячейки — строка COST attr=122"
    verification:
      - kind: other
        ref: "uv run python .pytest_cache/r9diff/cost_evidence.py (10 строк EVIDENCE, 10 CONTROL)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD» r9diff с чужими корпусами и семейством (к8): DIFF по обоим GREEN и BASE — 0 / 0, OPEN_REGRESSIONS=0, HEAD_WRONG — только адресаты 16-48; самопроверка 12 444 формы — 0 неверных на HEAD"
    verification:
      - kind: other
        ref: "bash .pytest_cache/r9diff/run.sh 16-47 (выход 0, 2026-10-21 10:50:08–10:51:10 UTC)"
        status: pass
    human_judgment: false

duration: 72min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 47: объект модуля для имени журнала и получателя (WR-29, WR-30) и названная цена атрибута О-22 (а) — Summary

**Гейт приватности читает имя, связанное в модуле с вызываемым журнала, членом только у объекта модуля (`sys.modules[__name__]` и имени, связанного с ним), а член объекта модуля, связанный с получателем, — получателем. Поэтому `fh.write(account.phone)` при `write = print` больше не ложная находка, а `getattr(sys.modules[__name__], "lg").info(…, account.phone)` и ещё шесть форм WR-30 краснят гейт. Цена атрибута (О-22 (а)) названа в шапке и подтверждена исполнением. На чужих корпусах неверных ячеек вне названных цен 569 → 126 (остаток — WR-31, план 16-48). `HEAD_WRONG` 3 100 → 2 007, все ячейки — у 16-48. Регрессий ни по одной оси нет.**

## Performance

- **Duration:** ~72 мин
- **Started:** 2026-10-21T09:46:18Z
- **Completed:** 2026-10-21T10:58:02Z
- **Tasks:** 2 (у каждой RED и GREEN; циклов самопроверки и дифференциальной регрессии не понадобилось)
- **Files modified:** 1 отслеживаемый (`tests/test_phone_privacy_gate.py`, +383 / −16)

## Accomplishments

- WR-30: семь форм из ревью ловятся по одной находке `phone`: getattr-строка, с умолчанием, атрибут `sys.modules[__name__].lg`, цепочка `r = getattr(…)`, связанный объект модуля `me`, `methodcaller`, подача `asyncio.to_thread`. Контроли `lg.info(…)` и `getattr(self, "lg").info(…)` прежние.
- WR-29: четыре формы ревью — не вызов журнала, ноль находок. Четыре строки цикла 1 плана 16-43 (чтение getattr-строкой через объект модуля) ловятся по-прежнему.
- О-22 (а): атрибут, связанный с вызываемым журнала (тело класса, чужой `__init__`), судится у любого объекта. Цена названа в шапке и закреплена строкой у параметра. `cost_evidence.py` подтверждает исполнением, что номер уходит в файл.
- Трасер с подложенными `app/services/phone_trace.py` и `phone_export.py`.
- Шапка: «ПО СВЯЗЫВАНИЮ», абзац цены строгости, граница, летописи WR-29 и WR-30.
- Инструмент r9diff вырос: семейство (к8) «одно имя — две роли» на оси объекта модуля (1 560 ячеек), самопроверка 16-47 (12 444 формы), улика и перечень `COST-ATTR` в строках запуска.

## Task Commits

1. **Задача 1 (трасер): RED** — `771ed639` (test): трасер, 8 строк `NEGATIVE_CONTROLS`, 6 строк `POSITIVE_CONTROLS`.
2. **Задача 1: GREEN** — `16573223` (feat): `module_objects`, `_is_module_object`, три места чтения, докстринги.
3. **Задача 2: RED** — `850c4a6f` (test): правило шапки с новыми местами.
4. **Задача 2: GREEN** — `7c077803` (feat): тексты шапки.

**Plan metadata:** коммит этой сводки (`docs(16-47)`).

## TDD: RED и GREEN

**RED задачи 1** (`771ed639`). Прогон: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k "through_the_module_object or module-logger or module-object or is-not-a-method" --junit-xml=.pytest_cache/gsd-red/16-47-t1.xml`, начат в 09:58Z.
- Строка `FAILED tests/test_phone_privacy_gate.py::test_a_planted_trace_through_the_module_object_reddens_the_gate_and_a_file_export_does_not` есть.
- Последняя строка сводки: `13 failed, 2 passed, 283 deselected, 1 warning in 1.05s`. Упали трасер, семь строк WR-30, четыре строки WR-29 и двойник `module-logger-read-through-the-module-object-without-a-number`. Plan требовал N ≥ 12; двойник красный сверх этого, потому что база не видела в нём вызова журнала.
- Причинный литерал сообщения трасера есть в выводе (2 вхождения): «журнал модуля, прочитанный через объект модуля, и запись номера в файл гейт приватности судит не так». Фактический выход: `['app/services/phone_export.py:5 — имя — phone (владелец export)']`.
- `gsd check tdd-red-evidence .pytest_cache/gsd-red/16-47-t1.json` → `RED_EVIDENCE_OK` (`target_test_failed`; tests 15, fail 13, pass 2).
- Смысловая оценка: цель исполнилась и упала на запланированном утверждении о списке находок. Строки WR-30 упали на «номер в вызове журнала не найден», строки WR-29 — на «принял за журнал». Ошибок сбора, ввоза и фикстур нет.
- Закрепки, зелёные до GREEN: `non-logger-module-name-read-through-the-module-object` (в выборке `-k`) и `log-callable-attribute-called-on-a-parameter` (отдельный прогон: `1 passed`; закрепка решения О-22 (а)).

**GREEN задачи 1** (`16573223`). Сделано:
- поле `module_objects` и `_module_object_names` — неподвижная точка общей грамматики;
- `_is_module_object`;
- `_bind(target, in_class_body, …)` в ветке вызываемого журнала;
- ветка члена в `_log_function_reference`: имя из `log_functions` — только при владельце-объекте модуля, имя из `log_function_attributes` — у любого владельца;
- в `_is_log_receiver` — условие `attribute in names.receiver_names and _is_module_object(owner, names)` и докстринг.

**RED задачи 2** (`850c4a6f`). Прогон: `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier --junit-xml=.pytest_cache/gsd-red/16-47-t2.xml`, начат в 10:34:49Z.
- Строка `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` есть.
- Последняя строка: `1 failed, 297 deselected, 1 warning in 0.55s`.
- Литерал «шапка гейта приватности не называет носителя ссылки и общую грамматику» есть: 2 вхождения в выводе; в дереве до задачи `grep -c` = 1. Недостающих мест 7: `` `sys.modules[__name__]` ``, «Летопись WR-29», «Летопись WR-30», «О-22 (а)», объект модуля в «ПО СВЯЗЫВАНИЮ», «О-22 (а)» и «`other.bum(…)`» в абзаце цены.
- `RED_EVIDENCE_OK`. Закрепка: место «граница не называет пойманную форму WR-30» зелёное до GREEN.

**GREEN задачи 2** (`7c077803`): тексты шапки. В окне 600 знаков после «`log.mark_failed(…)`» «О-22 (а)» стоит на +264, «`other.bum(…)`» — на +302. Это ровно замер планирования.

## TDD Gate Compliance

В обеих задачах `test(16-47)` стоит перед своим `feat(16-47)`: `771ed639` → `16573223`, `850c4a6f` → `7c077803`. `refactor` нет. Нарушений нет.

## Самопроверка исполнителя — ось «объект модуля и метод чужого объекта» (задача 2; О-20 (а), свойства 3, 4; О-21 (а), свойство 4; О-22 (а))

Генератор — `.pytest_cache/r9diff/selfcheck_1647.py` (gitignored). Суд — `judge.py` в отдельном процессе под общим `flock`. Прогон 2026-10-21 10:14–10:15 UTC; код предикатов — GREEN задачи 1 `16573223` (GREEN задачи 2 предикатов не трогал); база — `35106de1`.

**Часть A — композиция чтения через объект модуля.** Оси:
- 6 чтений: getattr, getattr с умолчанием, атрибут, имя `me`, цепочка имён `me2 = me`, цепочка `r = getattr(…)`;
- 9 значений: получатель `logging.getLogger("x")` и `structlog.get_logger()`; вызываемое — 5 видов; `methodcaller` с номером; обёртка носителя `partial(asyncio.to_thread, logger.info)`;
- 3 места применения: модуль, функция, метод;
- 21 способ: прямо и каждый носитель `REFERENCE_CARRIERS`;
- 3 номера: один, два, двойник `account.name`.

Полный крест — 10 206; из них 10 008 уникальных. Двойник «не журнал» (`lg = make_thing()`) добавляет 756.

**Часть B — метод чужого объекта.** Оси:
- 12 имён × 5 вызываемых;
- 4 места: модуль и функция — ноль находок и не вызов журнала; тело класса и чужой `__init__` — названная цена, одна находка;
- 4 владельца: параметр, имя модуля, `self.fh`, локальное имя.

Это 960 форм. Ещё 120 двойников-находок (атрибут, вызванный у параметра) и 600 чтений имени модуля через объект модуля (5 чтений × номер и двойник).

**Итого 12 444 формы** (≥ 10 000). Полный крест — **12 642**; повторов исходника отброшено 198.

**Ожидание** — число мест генератора: у части A — узлы номера, у части B — 0 у метода чужого объекта и 1 у двойника и у чтения через объект модуля. Названная цена — поле `cost` (`attr`, 1).

| Дерево | Форм | Неверных | Названная цена | Итог |
|--------|------|----------|----------------|------|
| HEAD (`16573223`) | 12 444 | **0** | 480 (часть B: тело класса и чужой `__init__`) | A: 3 384 по одной находке, 3 384 по две, 3 240 двойников — вызов журнала без находки; B-twin 120 по одной; чтение через объект модуля 300 по одной |
| контроль против вакуума: база плана `35106de1` | 12 444 | **2 712** | 480 | A 2 232: получатель через объект модуля (WR-30) — 1 116 для `logging`, 1 116 для `structlog`; B 480: ложная находка у модуля и функции (WR-29) |

**Найдено:** ничего, циклов самопроверки нет. Выборка 3 000 из 12 444 (seed 47) вошла в корпус сверки источником (е) `f-self-check`.

## Улика исполнения названной цены `COST-ATTR` (О-21 (а), свойство 2; О-22 (а))

`.pytest_cache/r9diff/cost_evidence.py` исполняет ячейки класса с настоящим `logging` (перехватчик на корневом журнале, DEBUG) и перехватом stdout (`print`). В роли `fh` — `io.StringIO`, аккаунт — заглушка `account.phone = "+79991234567"`. Места: тело класса и чужой `__init__`; вызываемые — пять видов; имя `write`. Контроль против вакуума перехвата: то же связывание, вызванное у своего владельца (`Z.write(…)`, `Z().write(…)`), кладёт номер в журнал (10 строк `CONTROL attr: file='' log='+79991234567…'`, в stderr `run.sh`).

```
EVIDENCE attr: file='+79991234567' log='' cell=class-body/print
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/partial
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logging.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/print
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/partial
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logging.info
```

Перечень 122 чужих id класса — `.pytest_cache/r9diff/cost_attr_ids.txt`: **122 строки**, sha256 `deaa985492817b71e9c917fa4b79205c3e41de1c9da97d117fcdba0cb000b3da`. Это `x-v9::fp::*:class-body:*` и `x-v9::fp::*:other-init:*` (120), `x-v9h::x::WR29-class-body-base-shape`, `x-r8h::F1-base-shape`. Ни одна из 122 не в `REPAIRED`, не в регрессиях и не в `HEAD_WRONG`: строка `COST kw=281 attr=122`.

## Сверка «база ↔ HEAD» (r9diff; пункт 10 договора `16-46-PLAN.md` `<scope_note>`; свойство 7 О-21 (а))

### Чужие входы

Копия оркестратора: `cp -a` трёх каталогов в `.pytest_cache/`. `sha256sum -c --quiet MANIFEST.sha256` — 62 файла, совпадение (`INPUTS_OK files=62` в каждом прогоне). Корпуса — те же, что у 16-46, вход целиком:

| Файл | Байт | sha256 | Ячеек |
|------|------|--------|-------|
| `verify-r9/corpus.json` | 9 880 738 | `5c6c4527733eef1541fe88f144c1a4fd97e74907cfb401b32c8c32fba6acb7f5` | 20 769 |
| `verify-r9/hand.json` | 13 135 | `9812cb4780a8201c1abb6774ccf652e4d6a2e1e625f165078261600edb7afd69` | 39 |
| `review-r8/corpusK.json` | 2 639 220 | `2ee9e5f2998a3606527efaaf2c80197c631af9e0d058e3afbae843c13a08481b` | 6 600 |
| `review-r8/corpusKC.json` | 654 066 | `5ae59c54cfc0ca5058e3d45c634828397b6da9202860b073a05f4ed7b8c249f7` | 2 106 |
| `review-r8/hand.json` | 37 454 | `b1e6dc9f04c8d80581999488373437405dcf1db0fe28a94d5b6180cea0a8a0a4` | 115 |
| `review-r8/rows.json` | 98 393 | `761690482879a829f2a4da9f8ec8bfbb6402645f0b5909f647b53f428b47766e` | 312 |
| итого | | | **29 941** |

### Корпус итогового прогона

HEAD `7c077803`, **121 249 ячеек**, `corpus.json` sha256 `e466e09ed40c889f63d96fbaf26fd390f0032beeb11f565fe5839772cfd17f9e`. Тот же корпус судил и прогон после GREEN задачи 1: строки таблиц GREEN задачи 2 не менял.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 259, `LEGITIMATE_CASES` 105, `NEGATIVE_CONTROLS` 173, `POSITIVE_CONTROLS` 61 | 598 |
| (б) матрица | `b-matrix` | 3 276 |
| (в) формы ревью | | 106 |
| (г) дифференциал раунда 7 | | 700 |
| (д) выборка самопроверок | 15 семейств по 2 000 (seed 42) | 30 000 |
| (ж) две подачи на одной строке | `g-double` | 3 276 |
| (з) безопасные двойники | `h-safe` | 6 552 |
| (е) `f-self-1644` | 20 000 из 66 690 (seed 42) | 20 000 |
| (е) `f-self-1646` | самопроверка 16-46: 6 000 из 84 750 (seed 46) — прежний `f-self-check` корпуса `af485593…` | 6 000 |
| (е) `f-self-check` | самопроверка 16-47: 3 000 из 12 444 (seed 47) | 3 000 |
| (и) чужие корпуса | шесть файлов целиком | 29 941 |
| (к1)…(к7) | как у 16-46: 3 000, 1 590, 600, 2 050, 3 000, 3 000, 3 000 | 16 240 |
| **(к8) «одно имя — две роли», ось объекта модуля** (новое) | (а) имя вызываемого журнала модуля — и метод чужого объекта, и член объекта модуля в одной функции: 12 имён × 5 вызываемых × 5 чтений × 2 владельца × 2 номера = 1 200; (б) имя получателя модуля — и атрибут чужого объекта (`obj.lg.info(…)`): 3 получателя × 5 чтений × 2 владельца × 3 применения × 2 номера = 180; (в) имя объекта модуля перевязано с получателем: 24; (г) имя объекта модуля — и атрибут чужого объекта (`x.me.lg`): 36; (д) имя модуля и атрибут тела класса или чужого `__init__` с тем же именем — `COST-ATTR`: 120 | 1 560 |

**Не прогнано выборкой:**
- (д) — 11 119 725 форм полного перебора генераторов;
- `f-self-1644` — 46 690;
- `f-self-1646` — 78 750 (самопроверка 16-46 прогнана целиком в 16-46);
- `f-self-check` — 9 444 (самопроверка 16-47 прогнана целиком: 12 444 на HEAD и на базе);
- (к1) 6 000, (к5) 6 000, (к6) 856, (к7) 480.

Строки таблиц, матрица, формы ревью, дифференциал, (ж), (з), чужие корпуса, (к2), (к3), (к4), (к8) — целиком.

### Строки итогового прогона

`bash .pytest_cache/r9diff/run.sh 16-47` под общим `flock`, HEAD `7c077803`, 2026-10-21 10:50:08–10:51:10 UTC, выход 0. Вердикты взяты из кеша по ключу содержимого: тот же код судился в `--precommit` 10:39–10:48. Дословно, без строк `EXTERNAL-CELLS` и `CORPUS` (stderr):

```
INPUTS_OK files=62
CORPUS_SHA256=e466e09ed40c889f63d96fbaf26fd390f0032beeb11f565fe5839772cfd17f9e HEAD=7c07780397c535f463993342d3eeb59d378994ed
SELFTEST 1bebbbf7 -> c6953017: cells=3382 regressions=48 count_regressions=48 fixed=208 repaired_overcount=0 changed=256
SELFTEST 5e32c335 -> 147f5e46: cells=3382 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3616 regressions=831 count_regressions=885 fixed=378 repaired_overcount=354 changed=1317
SELFTEST-CR04 e1d6587e -> a77263ad: cells=18221 regressions=1510 count_regressions=1510 fixed=0 repaired_overcount=0 changed=1510
REPRODUCE fb8fef72 K: cells=6600 mismatch=0
REPRODUCE fb8fef72 KC: cells=2106 mismatch=0
REPRODUCE e1d6587e K: cells=6600 mismatch=0
REPRODUCE e1d6587e KC: cells=2106 mismatch=0
REPRODUCE a77263ad K: cells=6600 mismatch=0
REPRODUCE a77263ad KC: cells=2106 mismatch=0
REPRODUCE 1c243203 K: cells=6600 mismatch=0
REPRODUCE dbc73537 K: cells=6600 mismatch=0
REPRODUCE dbc73537 KC: cells=2106 mismatch=0
DIFF 771ed639 -> 16573223: cells=121249 regressions=0 count_regressions=0 fixed=3157 repaired_overcount=1991 changed=2703
DIFF 850c4a6f -> 7c077803: cells=121249 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE 35106de1 -> HEAD 7c077803: cells=121249 regressions=0 count_regressions=0 fixed=3157 repaired_overcount=1991 changed=2703
EXTERNAL 35106de1: cells=29941 wrong=972 cost_kw=281 cost_attr=122 defects=569
EXTERNAL HEAD 7c077803: cells=29941 wrong=529 cost_kw=281 cost_attr=122 defects=126
COST kw=281 attr=122
COST-OWN kw=203 attr=480 kw_ext=20
COST-ATTR-IDS n=122 sha256=deaa985492817b71e9c917fa4b79205c3e41de1c9da97d117fcdba0cb000b3da
EVIDENCE attr: file='+79991234567' log='' cell=class-body/print
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/partial
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logging.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/print
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/partial
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logging.info
HEAD_WRONG=2007
OPEN_REGRESSIONS=0
```

- `SELFTEST` 48 / 56, `SELFTEST-COUNT` 885 и `SELFTEST-CR04` 1 510 — те же, что у 16-46: на выросшем корпусе инструмент видит прежние регрессии.
- `REPRODUCE` — расхождений 0 во всех девяти строках.
- `fixed=3157` по семействам: `a-negative` 7 (семь строк WR-30), `a-positive` 5 (четыре строки WR-29 и двойник `account.name`), `x-r8-FP` 300, `x-v9-fp` 120 (места модуля и функции), `x-r8-X` 12 и `x-v9-x` 11 (ручные WR-29, WR-30), (к3) 240, (к4) 410, (к8) 1 392, `f-self-check` 660.
- `COST-OWN attr=480`: (к3) 240 + (к8 д) 120 + выборка самопроверки 120.

**Чужие ячейки, расходящиеся с ожиданием** (обе оси):

| Ревизия | wrong | цена `kw` | цена `attr` | defects | по семействам |
|---------|-------|-----------|-------------|---------|---------------|
| база плана `35106de1` (родитель первого GREEN по коду) | 972 | 281 | 122 | 569 | `x-r8-FP` 300, `x-v9-fp` 240, `x-v9-kw` 280, `x-v9-dw` 120, `x-r8-X` 16, `x-v9-x` 16 |
| GREEN задачи 1 `16573223`, GREEN задачи 2 `7c077803` = HEAD | **529** | 281 | 122 | **126** | `x-v9-fp` 120 (цена `attr`), `x-v9-kw` 280 (цена `kw`), `x-v9-dw` 120, `x-r8-X` 4, `x-v9-x` 5 (из них по одной ячейке — цена `attr` и `kw`) |

Ручные `x-r8-X` и `x-v9-x` на HEAD: 3 + 3 — WR-31 (16-48). Ещё по одной на семейство — ручные формы цен (`F1-base-shape`, `WR29-class-body-base-shape`, `KW-partial-setattr-dual`). Каждая неверная на HEAD чужая ячейка вне названных цен — класс WR-31 (`x-v9-dw` 120 и ручные WR-31: 6), адресат 16-48.

**`HEAD_WRONG=2007` по адресатам** (вне названных цен; `UNASSIGNED` нет; адресата 16-47 нет):

| Адресат | Семейства | Ячеек |
|---------|-----------|-------|
| **16-48**, WR-31 (запись через получатель — на узле получателя) | `x-v9-dw` 120; ручные 6 (`x-v9-x` 3, `x-r8-X` 3); `g-double` 252 и `f-self-1644` 493 (ожидание D2 — число узлов колонки); своё (к7) 487 | 1 358 |
| **16-48**, коллизия имени носителя у гейта писателя | своё (к6) 649 | 649 |

До плана было `HEAD_WRONG=3100`. Адресованные 16-47 1 093 ячейки ушли все: WR-29 668 — `x-r8-FP` 300, `x-v9-fp` модуля и функции 120, ручные 8, (к3) 240; WR-30 425 — ручные 15, (к4) 410.

**Регрессировавшие ячейки и закрывшие их коммиты:** нет. Ни один GREEN не дал регрессии ни по наличию, ни по числу; строк `REGRESSED` и `COUNT_REGRESSED` нет.

**`REPAIRED` (`repaired_overcount=1991`, класс WR-29 — снята ложная находка на методе чужого объекта, число стало ровно ожиданием):**
- по семействам: `x-r8K` (FP) 300, `x-v9` (fp модуля и функции) 120, `x-v9h` 4 и `x-r8h` 4 (ручные F1–F4), `a-positive` 4 (строки WR-29), (к3) 240, (к8 а) 1 200, `f-self-check` 119;
- по числу: 1 391 ячейка 1 → 0, 600 ячеек 2 → 1 (у (к8 а) остаётся одна находка — чтение через объект модуля);
- перечень с числами: `.pytest_cache/r9diff/repaired_1647.tsv`, 1 991 строка, sha256 `db7aeeede253d543589b05c79ceeb2a1d4a5f2eec929cfb022d42cbd473545d5`;
- ни одна ячейка группы `COST-ATTR` в `REPAIRED` не попала (0 мест `class-body` / `other-init` / `base-shape`).

**Прогоны:**

| Прогон | HEAD / цель | Время (UTC) | Корпус | Строки | Выход |
|--------|-------------|-------------|--------|--------|-------|
| воспроизведение до правок: `run.sh 16-46` на базе (см. отступление 1) | `35106de1` | 09:46–09:47 | 116 675, `af485593…` | ровно строки 16-46: `SELFTEST` 48 / 56, `SELFTEST-COUNT` 885, `SELFTEST-CR04` 1 510, `REPRODUCE` 0, `EXTERNAL HEAD … wrong=972 cost_kw=281 cost_attr=122 defects=569`, `HEAD_WRONG=3100`, `OPEN_REGRESSIONS=0` | 0 |
| `--precommit` до GREEN задачи 1 | `771ed639` → WORKTREE | 09:58–10:13 | 116 689, `9222384e…` | `DIFF 771ed639 -> WORKTREE` и `BASE`: 0 / 0, `fixed=1057`; `EXTERNAL WORKTREE … defects=126`; `HEAD_WRONG=2055` (48 — флаг (к3) у `partial`, отступление 2); `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-47` после GREEN задачи 1 (корпус вырос: (к8), самопроверка 16-47) | `16573223` | 10:16–10:34 | 121 249, `e466e09e…` | `DIFF 771ed639 -> 16573223` и `BASE`: 0 / 0, `fixed=3157`; `EXTERNAL HEAD … defects=126`; `COST kw=281 attr=122`; `HEAD_WRONG=2007`; `OPEN_REGRESSIONS=0` | 0 |
| `--precommit` до GREEN задачи 2 | `850c4a6f` → WORKTREE | 10:39–10:48 | `e466e09e…` | `DIFF 850c4a6f -> WORKTREE` 0 / 0, `changed=0`; `BASE` 0 / 0; `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-47` после GREEN задачи 2 | `7c077803` | 10:48–10:49 | `e466e09e…` | строки выше, без `COST-ATTR-IDS` / `EVIDENCE` | 0 |
| `run.sh 16-47` итоговый (с уликой в строках, отступление 4) | `7c077803` | 10:50–10:51 | `e466e09e…` | строки выше | 0 |

Инструмент оставлен на месте: `.pytest_cache/r9diff/` (с `trees/`, `judged/`, `corpus.json`, `selfcheck_cells.json` — самопроверка 16-47, `selfcheck_cells_1646.json` — самопроверка 16-46), `.pytest_cache/r9diff-src/`, `.pytest_cache/r9-inputs/` (не правился). 16-48 стартует с этой копии.

## Гейты на итоговом дереве (под общим `flock`)

| Проверка | Итог | База (16-46 / оркестратор) |
|----------|------|----------------------------|
| задача 1, №1: приватность + паритет | 320 passed | 305 |
| задача 1, №2: прежние строки `1163ae39` | `OK 156 53 173 61` | — |
| задача 1, №3: формы, двойники, цена, матрица, реестр | `OK 12 6 1638` | — |
| задача 1, №4: гейт писателя | 598 passed | 598 |
| задача 2, №1: три модуля гейтов | 918 passed | 903 |
| задача 2, №2: места шапки | `OK` | — |
| задача 2, №3: улика `cost_evidence.py` | 10 строк `EVIDENCE attr: file='+79991234567' log=''`, выход 0 | — |
| задача 2, №4: quick run фазы | 1322 passed | 1307 |
| задача 2, №5: сквозные гейты + `test_logging_config` | 576 passed + 3 passed (двумя командами, см. замены) | 576 + 3 |
| реестр исключений / JS-половина | `OK` / `OK 27 0` | — |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| множество распознанных вызовов всех 106 файлов против `35106de1` по строке и столбцу | `LIVE-CALLS base=386 head=386 new=0 removed=0` (после GREEN задачи 1 и на итоговом дереве) | — |
| живое дерево писателя | `OK 6 104` | `OK 6 104` |
| `tests/test_application` | 883 passed | 883 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 894 строк, биекция с переписью — согласие» | 894 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гонится после коммита этой сводки (заметка оркестратора 5) | 218 / 2 skipped |

Полная суита (`just test`, ≈44 мин) не гонялась: её гонит пост-мердж гейт оркестратора. `graphify update .` не запускался — его делает оркестратор после слияния. `graphify query` гонялся с `--graph /source/broadcaster/graphify-out/graph.json`.

## Decisions Made

- Помощник «объект модуля» один на две находки. `_is_module_object` зовут ветка члена `_log_function_reference` (WR-29) и ветка члена `_is_log_receiver` (WR-30). Получатель в `receiver_attributes` не кладётся, поэтому довод 16-43 о `logger.log` к правке не относится.
- Имена объекта модуля — только цели-имена общей грамматики (`me = …`, цепочка). Атрибут `self.me = sys.modules[__name__]` объектом модуля не считается; эта форма вне ревью.
- Ввезённое `from logging import info` теперь читается и членом объекта модуля (`sys.modules[__name__].info(…)`): это тот же объект. Прежнее «только голым именем» сужало поимку без причины. На живом дереве совпадений ноль.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — инструмент] Первый прогон до правок — `run.sh 16-46`, а не `run.sh 16-47`.**
- Найдено: заметка оркестратора 2 требует первым шагом `run.sh 16-47`. Но до первого `test(16-47)` у плана нет базы, а без `feat(16-47)` инструмент выходит с `NO GREEN COMMITS`.
- Исправлено: `run.sh 16-46` на базе `35106de1` (код гейтов = `472e30f6`). Он воспроизвёл итоговые строки 16-46 дословно (таблица прогонов).
- Проверка: `CORPUS_SHA256=af485593…`, все числа совпали.

**2. [Rule 1 — ожидание своего семейства] Флаг вызова журнала (к3) у значения `partial`.**
- Найдено: `--precommit` задачи 1 оставил 48 ячеек (к3) мест «модуль» и «функция» со значением `functools.partial(logger.info, "y")` неверными. Находок там ноль, но `python_log_calls` непуст.
- Причина (замер `.pytest_cache/checks/k3_partial_probe.py`): распознан ровно сам `functools.partial(logger.info, 'y')` на строке связывания. Шапка («ПО ССЫЛКЕ НА МЕТОД ОПОЗНАННОГО ЖУРНАЛА») прямо называет его вызовом журнала. `fh.write(…)` вызовом не распознан.
- Исправлено: генератор 16-46 ставил флаг `False` всем пяти вызываемым; теперь `is_log_call = cid == "partial"`. То же в части B самопроверки 16-47. Ожидание чужих корпусов не трогалось (их `partial`-ячейки верны на HEAD).
- Проверка: `HEAD_WRONG` 2 055 → 2 007; (к3) на HEAD верна вся (240 мест модуля и функции; места цены — `COST-OWN`).

**3. [Rule 2 — заметка оркестратора 8] Семейство (к8) «одно имя — две роли» на оси объекта модуля.**
- Добавлено в `kfam.py` до доверия GREEN задачи 1: 1 560 ячеек, корпус — целиком (`K_CAPS["k8"] = 3000`). Состав — в таблице корпуса.
- На HEAD: 1 440 верны, 120 — цена `COST-ATTR`. На базе неверны (а) 1 200, (б) 180, (г) 12 (`fixed` (к8) 1 392 с учётом двойников).
- Ячейка (к8) без адресата печаталась бы как `UNASSIGNED`; таких нет.

**4. [Rule 3 — инструмент] Корпус и строки запуска.**
- `corpus.py`: самопроверка 16-46 переименована в `selfcheck_cells_1646.json` и судится семейством `f-self-1646` той же выборкой (6 000, seed 46). Имя `selfcheck_cells.json` заняла самопроверка 16-47 (`f-self-check`, 3 000 из 12 444, seed 47). Названная цена ячейки (`cost`) переносится в корпус.
- Корпус — 121 249 ячеек, на 1 249 выше ориентира договора (120 000).
- `run.sh`: после строки `COST` печатаются `COST-ATTR-IDS` (`cost_ids.py`, перечень 122 id) и строки `EVIDENCE attr:` (`cost_evidence.py`). Строки `CONTROL` идут в stderr. Номер не в файле или пустой контроль дают выход 1. Так строка `COST … attr=122` стоит рядом с уликой, как требует критерий успеха.

**5. [План против замера] Улика — 10 ячеек вместо двух.** План просил две представительные ячейки (тело класса и `__init__`). Скрипт исполняет оба места × пять вызываемых — надмножество, у всех 10 `log=''`. Контроль против вакуума перехвата — сверх плана.

### Замены команд (песочница worktree)

- Проверки `python -c` записаны дословно в `.pytest_cache/checks/*.py` и гнались с `PYTHONPATH=.`: `t1_rows.py`, `t1_forms.py`, `t2_header.py`, `t2_registry.py`, `t2_js.py`, `writer_live.py`.
- RED-улика собиралась скриптом `red_record.py` из файла параметров: команда с `uv run pytest …` внутри аргументов отклонена песочницей.
- Составные команды git (`$(cat …)..HEAD`, цепочки с `echo`) отклонены — гнались раздельно. Начальный `cp -a` трёх каталогов — тремя командами.
- Ожидание длинных прогонов — `flock -w 595 <lock> true`.
- Задача 2, `<automated>` №5 (сквозные гейты и `test_logging_config` одной командой) — двумя командами: 576 + 3.

---

**Total deviations:** 5. Это два исправления инструмента и одно ожидание своего семейства (правила 1 и 3), рост корпуса по заметке 8 (правило 2) и одно расхождение плана с замером в сторону надмножества.
**Impact on plan:** гейт, шапка и заявления — по плану; правки инструмента — в gitignored `.pytest_cache/r9diff/`. Объём не расширен: общий модуль `tests/phone_gate_grammar.py`, гейт писателя и модуль паритета не тронуты.

## Issues Encountered

Нет.

## Known Stubs

Нет.

## Threat Flags

Нет: правка — тестовый гейт; новых сетевых точек, путей и схем нет. T-16-108 (WR-30) и T-16-109 (WR-29, цена атрибута) закрыты, как в плане.

## Next Phase Readiness

- 16-48 стартует с копии `.pytest_cache/r9diff/`. Его объём в `HEAD_WRONG`: 2 007 ячеек, из них WR-31 — 1 358, коллизия имени носителя (к6) — 649. Других адресатов нет.
- Флаг (к3) у `partial` исправлен в генераторе (отступление 2). Тот же класс ожидания — «сам `partial(<вызываемое журнала>, …)` на строке связывания — вызов журнала» — стоит проверить в новых семействах 16-48 и 16-49.
- Словарь (16-49): формы чтения через объект модуля и значение-получатель в `BINDING_FORMS` / матрицах / паритете — по плану 16-49, этот план их не вписывал.
- Отметку PHONE-21 и учёт не трогали (заметка оркестратора 5).

## Self-Check: PASSED

- Коммиты `771ed639`, `16573223`, `850c4a6f`, `7c077803` — предки HEAD (`git log 35106de1..HEAD`).
- Файлы на месте: `tests/test_phone_privacy_gate.py`, эта сводка, `.pytest_cache/r9diff/run.sh`, `cost_evidence.py`, `cost_ids.py`, `selfcheck_1647.py`, `cost_attr_ids.txt`, `repaired_1647.tsv`.
- Удалений в коммитах нет (один файл, +383 / −16).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-21*
