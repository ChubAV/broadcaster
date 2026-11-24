---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 37
subsystem: testing
tags: [ast, phone, privacy-gate, carrier-wrapper, shared-grammar, base-head-differential, tdd, wr-24, wr-26, in-16, in-17]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль после 16-36 (`carrier_wrapper_bindings(…, nested=True)`, `applied_wrapper`, `named_wrappers`, `is_carrier_wrapper`, `wrapper_applications`); гейт писателя 574; инструмент сверки `.pytest_cache/r7diff/` 16-36"
provides:
  - "гейт приватности на общей семантике обёртки носителя: `_carrier_wrappers` — тонкая обёртка над `carrier_wrapper_bindings` с `is_carrier_wrapper`; `python_log_calls` судит каждое применение `wrapper_applications`; своей неподвижной точки, ручного применения и своей рекурсии в модуле гейта нет"
  - "одно место — одна находка: `python_log_offences` не повторяет тройку (строка, вид, предмет); правило строк `NEGATIVE_CONTROLS` это утверждает"
  - "правило-паритет: `REQUIRED_SHARED_NAMES` (11 имён) и `CARRIER_SEMANTICS` требуют `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`, `is_carrier_wrapper`, `wrapper_applications`"
  - "трасер `test_a_planted_log_wrapper_called_through_a_getattr_string_reddens_the_gate`; 9 строк `NEGATIVE_CONTROLS` (126), 1 строка `POSITIVE_CONTROLS` (50)"
  - "шапка гейта приватности правдива: суд обёртки на каждом чтении, getattr-строка, поданная и вложенная обёртка, функции общего модуля, летописи WR-24 / WR-26; IN-16 и IN-17 закрыты"
  - "инструмент сверки `.pytest_cache/r7diff/` для 16-38: seed 37, семейство (д) `e-wrapper-read-1636`, проверка «одно место» у строк, самопроверка (е) `selfcheck_1637.py`"
affects: [16-38, 16-39, 16-40, phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 11211
  tasks: 3
  commits: 6
plan_head_before: df9cea19abac52d6aa564b462298e329665e7867
plan_head_after: 0a4e44110800aadb1313d41747a78b75c0608e31

tech-stack:
  added: []
  patterns:
    - "Оба гейта номера судят обёртку носителя одними функциями общего модуля: гейт даёт только имена `partial` и свой предикат ссылки (`_log_wrapper_reference`: вызываемое журнала или `methodcaller`)"
    - "У гейта приватности находка стоит на узле аргумента, поэтому одно место — одна находка достигается дедупликацией тройки (строка, вид, предмет), а не поглощением; суд на месте связывания остаётся всегда"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py
    - tests/test_phone_gates_parity.py
    - tests/phone_gate_grammar.py

key-decisions:
  - "Дедупликация, а не поглощение: обёртка с аргументами судится и на месте связывания, и на месте применения, но находка в обоих случаях стоит на одном узле аргумента — повтор тройки отбрасывается, первая остаётся"
  - "Комментарий ввоза говорит правду, а не формулу плана: общая `reference_arguments` доходит до `iterable_elements` через `elementwise_arguments` у поэлементного носителя, поэтому фраза «`reference_arguments` её не зовёт» была бы ложной (отступление 2)"
  - "`wrapper_applications` зовётся без `every_reading` (как `reference_arguments` у гейта приватности); вызов `X(…)` в `X(…)(…)` носителем не судится и применений не ищет — как у гейта писателя"

patterns-established:
  - "Самопроверка оси «где прочитано имя обёртки журнала» с контролем против вакуума: тот же генератор на дереве базы плана обязан промахиваться"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "Подложенная служба `app/services/phone_sync.py` с обёрткой журнала в атрибуте, вызванной getattr-строкой, краснит гейт приватности: ровно одна находка `:13 — имя — phone`"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_log_wrapper_called_through_a_getattr_string_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Две формы WR-24 и семь форм WR-26 (поданная литералом и именем, в `partial`, имя поверх имени, глубина три литералом и именем, `methodcaller` в поданной обёртке) — строки `NEGATIVE_CONTROLS` с находкой `phone` и без повтора места; не-журнальная поданная обёртка — строка `POSITIVE_CONTROLS`"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half"
        status: pass
    human_judgment: false
  - id: D3
    description: "Семантика обёртки — функции общего модуля; гейт приватности держит пять имён теми же объектами, правило-паритет их требует; функция применений одна у обоих гейтов, цикл обёрток без журнала не зависает"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_take_the_binding_grammar_and_carriers_from_one_module"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/shared_names_t1.py (OK 10 на задаче 1; 11 после задачи 2) и cycles_t2.py (OK one function, cycles)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка: суд обёртки на каждом чтении, getattr-строка, поданная и вложенная обёртка, функции общего модуля, летописи WR-24 / WR-26, прошедшее время строк 16-34, правдивый комментарий ввоза; заявление прежнее"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/header_t3.py (OK)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Сверка «база ↔ HEAD»: 38 402 ячейки, по каждому из трёх GREEN — `DIFF` без регрессий, `BASE df9cea19 -> HEAD 0a4e4411` без регрессий, `OPEN_REGRESSIONS=0`, `SELFTEST` 43 и 52; самопроверка 16 634 формы — 0 промахов, 0 повторов"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: "bash .pytest_cache/r7diff/run.sh 16-37 (выход 0, HEAD 0a4e4411)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Прежнее не ослаблено: 117 / 49 строк `65e5c692` на месте; живые деревья 225 / 68 / 93, находок 0; реестр `{}`, потолок 0; JS-половина не тронута (27 символов); гейт писателя 574"
    requirement: PHONE-21
    verification:
      - kind: other
        ref: ".pytest_cache/checks/rows_task1.py (OK 117 49 126 50), registry_t3.py (OK), js_t3.py (OK 27 0)"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
    human_judgment: false

duration: 32min
completed: 2026-10-19
status: complete
---

# Phase 16 Plan 37: Гейт приватности на общей семантике обёртки носителя — Summary

**Гейт приватности больше не держит своей копии семантики обёртки носителя. Он зовёт те же функции общего модуля, что и гейт писателя: `carrier_wrapper_bindings`, `is_carrier_wrapper`, `named_wrappers`, `wrapper_applications`. Поэтому обёртка журнала ловится везде, где прочитано её имя: вызванная по имени, через атрибут или getattr-строкой, поданная другому носителю литералом или именем, обёрнутая ещё одним `partial` или вложенная на три уровня. Одно место даёт одну находку: двойной счёт `5e57325d` снят. Правило-паритет требует имена семантики обёртки, и шапка о копиях теперь говорит правду. Сверка «база ↔ HEAD» прогнана после каждого GREEN: `OPEN_REGRESSIONS=0`. Самопроверка — 16 634 формы, промахов нет.**

## Performance

- **Duration:** ≈32 мин
- **Started:** 2026-10-19T08:36:22Z
- **Completed:** 2026-10-19T09:08Z
- **Tasks:** 3 (циклов сверки и самопроверки сверх задач не понадобилось)
- **Files modified:** 3

## Accomplishments

- **Гейт приватности (`tests/test_phone_privacy_gate.py`):**
  - `_carrier_wrappers` — тонкая обёртка над общей `carrier_wrapper_bindings(…, nested=True)` с общим предикатом `is_carrier_wrapper`. Гейт даёт им только `names.partial_names` и предикат ссылки `_log_wrapper_reference` (вызываемое журнала или `methodcaller`). Своей неподвижной точки и своей проверки аргументов в модуле нет;
  - `_log_wrappers_of` — обёртки, которые называет узел, через общую `named_wrappers` (литерал, имя, атрибут, getattr-строка);
  - `python_log_calls` судит каждое применение `wrapper_applications` функциями `_carried_log_calls` и `_applied_log_methodcaller`. Ручная сборка `ast.Call(func=wrapper, …)` ушла. Ветку «вызов имени обёртки» из задачи 1 задача 2 перенесла в ту же общую функцию;
  - `python_log_offences` не повторяет тройку (строка, вид, предмет) — остаётся первая находка.
- **Строки:**
  - трасер;
  - `NEGATIVE_CONTROLS` 117 → 126: две формы WR-24 и семь форм WR-26;
  - `POSITIVE_CONTROLS` 49 → 50;
  - правило строк получило второе утверждение «одно место дало находку дважды».
- **Правило-паритет:** `CARRIER_SEMANTICS` и `REQUIRED_SHARED_NAMES` (6 → 11) называют пять имён семантики обёртки. Комментарий о копии гейта приватности и докстринг паритета обновлены.
- **Общий модуль:** изменился только докстринг `carrier_wrapper_bindings` — теперь он говорит, что функцию зовут оба гейта. Код общего модуля не менялся.
- **Шапка:**
  - абзац «ПО НОСИТЕЛЮ ССЫЛКИ»: суд обёртки на каждом чтении, getattr-строка, поданная и вложенная обёртка, одно место — одна находка, девять функций общего модуля;
  - «своих копий нет» — теперь правда;
  - пункт «ГРАНИЦЫ» о результате не-`partial` вызова уточнён: обёртка носителя — не такой результат, и она ловится;
  - летописи WR-24 и WR-26;
  - строки плана 16-34 — в прошедшем времени (IN-17);
  - комментарий ввоза — без выведенной таблицы, с путём `methodcaller` (IN-16).
- **Инструмент сверки** `.pytest_cache/r7diff/` дополнен и оставлен на месте для 16-38 (подробности — в разделе сверки).

## Task Commits

1. **Задача 1 (трасер): общая семантика обёртки, getattr-строка, одно место — одна находка, паритет** — `a6c87597` (test, RED), `51d0d766` (feat, GREEN).
2. **Задача 2: `wrapper_applications` — поданная, обёрнутая и вложенная обёртка, `methodcaller` в поданной обёртке** — `a53126a7` (test, RED), `2d59adff` (feat, GREEN).
3. **Задача 3: шапка, IN-16, IN-17, летописи** — `fa786d20` (test, RED), `0a4e4411` (feat, GREEN).

**Plan metadata:** коммит `docs(16-37)` с этой сводкой. Первый коммит плана — `a6c87597`, база — `df9cea19`.

Гейт трасера после задачи 1. Режим `end-of-phase`, у трасера только проверки `<automated>`. Все четыре команды `<verify>` прогнаны и зелёные:
- `240 passed`;
- `OK 117 49 119 49`;
- гейт писателя `574 passed`;
- `run.sh 16-37` — выход 0, `OPEN_REGRESSIONS=0`.

После этого план перешёл к задачам 2 и 3.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). По каждому есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех трёх записях (`t1.json`…`t3.json`).

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_log_wrapper_called_through_a_getattr_string_reddens_the_gate` | `4 failed, 236 deselected` | «обёртка журнала, вызванная getattr-строкой, не опознана»; «одно место дало находку дважды»; «гейты номера не делят одну грамматику связывания» | Трасер исполнился: файл найден, находок `[]`. Строка getattr-формы дала `[]`. Строка счёта дала две одинаковые находки `app/x.py:2 — имя — phone`. Паритет назвал четыре недостающих имени. |
| Задача 2 | `test_a_number_handed_to_a_python_log_call_is_found[literal-log-wrapper-handed-to-run-in-executor]` | `8 failed, 137 passed, 103 deselected` | «номер в вызове журнала не найден»; «гейты номера не делят одну грамматику связывания» | Все семь новых строк дали `[]`, паритет назвал `wrapper_applications`. Строка `POSITIVE_CONTROLS` `handed-carrier-wrapper-non-log-reference-is-not-a-log` зелёная до GREEN — это закрепка, а не RED-свидетель. |
| Задача 3 | `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 232 deselected` | «шапка гейта приватности не называет носителя ссылки и общую грамматику» | 11 мест: пять имён и меток шапки, getattr-строка, поданная и вложенная обёртка в абзаце носителя, «впишет» рядом с «16-34», таблица и путь `methodcaller` в комментарии ввоза. |

## Самопроверка исполнителя (задача 3; урок 16-29, 16-32; О-16 (а))

Скрипт `.pytest_cache/r7diff/selfcheck_1637.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный, работает под общим `flock`. Каждая форма подаётся в `python_log_offences(…, "app/x.py")`. Прогон — 2026-10-19 ≈08:52 UTC, HEAD `0a4e4411`.

**Оси:**
- **Представление обёртки (10):**
  - литерал;
  - вложенный в `partial` глубины 1, 2, 3;
  - имя `w`;
  - атрибут `self.w`;
  - цепочка `h = w`;
  - getattr-строка `getattr(self, "w")`;
  - именованная вложенная `w = partial(partial(…))`;
  - имя поверх имени.
- **Носитель обёртки (4):** `asyncio.to_thread`, `contextvars.copy_context().run`, `ctx.run`, `loop.run_in_executor, None`.
- **Где аргументы с номером (2):** в обёртке; у чтения.
- **Способ чтения (13):**
  - вызов;
  - подача позицией, `target=`, `fn=`, выдуманным `job=`;
  - `map`, `call_soon`, `append`, `Thread(target=…)`, `run_in_executor`;
  - чтение вне вызова (список, `return`) вместе с подачей;
  - без использования.
- **Значение опознания (7):** `print`, `from logging import info`, атрибут, getattr-строка, `partial(<журнал>, "x %s")`, `methodcaller` с получателем, `structlog.contextvars.bind_contextvars`.
- **Получатель (4):** `logger`, `self.log`, `logging`, `structlog.get_logger()`.
- **Метод (4):** `info`, `ainfo`, `_log`, `bind`.
- **Форма:** 12 `BINDING_FORMS`.
- **Ротация:** ось (получатель, метод, форма) перебирается ротацией по ядру «представление × носитель × режим × чтение × значение» (7 280 сочетаний), 2 прохода со сдвигом, а не полным крестом.

**Ожидание:**
- под заявлением — находки непусты, каждая называет `phone`, тройка места не повторяется;
- обёртке ничего не подано (без использования, аргументы у чтения) — ноль;
- законные (не-журнальная ссылка `helper.noop` с номером; ссылка на журнал с `account.name`) — ноль.

| Заход | HEAD | Подано (под заявлением / с ожиданием ноль) | Промахов | Повторов места | Ноль с находкой | Итог |
|-------|------|---------------------------------------------|----------|----------------|-----------------|------|
| 1 (итог) | `0a4e4411` | **16 634 (11 904 / 4 730)** | **0** | **0** | **0** | ячейки ушли в корпус (е) |
| контроль против вакуума | дерево базы `df9cea19` | 16 634 | 5 408 | 168 | 0 | генератор видит дефект базы: формы WR-24 / WR-26 и двойной счёт |

**По осям (заход 1):**
- представления — от 1 479 (вложенная глубины 2) до 1 785;
- носители — по ≈4 160;
- режимы — 8 268 / 8 366;
- способы чтения — от 654 (`map`) до 1 494;
- значения — от 2 298 (`bind_contextvars`) до 2 392;
- получатели — по ≈4 160;
- методы — по ≈4 158;
- формы — от 1 036 до 2 089.

**Найдено:** ничего. Циклов самопроверки не было. Полный крест осей без ротации — 7 280 × 4 × 4 × 12 = 1 397 760 ячеек под заявлением; он не прогонялся, прогнана ротация.

## Сверка «база ↔ HEAD» (свойство 7 О-16 (а); пункт 5 договора `16-36-PLAN.md`)

**Инструмент.** За основу взята копия 16-36 (`scratchpad/r7diff-16-36/`). Каждая часть сверена с договором `<scope_note>` 16-36 и этого плана: `corpus.py`, `judge.py`, `run.sh <план>`, git зовётся только из `run.sh`, кеш деревьев и вердиктов, `SELFTEST` на двух парах. Изменения этого плана:
- `SEED = 37`;
- ожидание строк `NEGATIVE_CONTROLS` стало `subject` + `unique`: судья повторяет правило строк «одно место — одна находка»;
- новое семейство (д) `e-wrapper-read-1636` — оси самопроверки 16-36 по её сводке и `selfcheck_1636.py`: представление × носитель × режим × чтение × значение × API × форма × законность, с теми же ожиданиями «одна / 1–2 по месту / ответ значения / ноль»;
- новый вид ожидания `phone_unique` и источник (е) `selfcheck_cells.json`.

`run.sh` уже принимал план аргументом.

**Корпус итогового прогона** (HEAD `0a4e4411`, 38 402 ячейки, `corpus.json` sha256 `90170f026f29762101b1c91c85a19308012c5dfbe71981fe48454a9fd963dc62`):

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 244, `LEGITIMATE_CASES` 98, `NEGATIVE_CONTROLS` 126, `POSITIVE_CONTROLS` 50 | 518 |
| (б) ячейки матриц | 12 `BINDING_FORMS` × 5 значений × (прямой вызов + 11 `REFERENCE_CARRIERS` + 9 кандидатных строк раунда 7) × 2 гейта | 2 520 |
| (в) формы ревью раунда 7 | CR-02 (7 + 3), CR-03 (4 + 3), WR-26 (4 + 3), WR-25 (2 + 1), WR-24 (2 + 1) | 30 |
| (г) дифференциал ревьюера / верификатора | 5 значений × 7 форм аргументов × 10 носителей × 2 гейта | 700 |
| (д) выборка самопроверок 16-27…16-34 и 16-36 | 9 семейств по 2 000 | 18 000 |
| (е) самопроверка этого плана | заход 1 | 16 634 |

**Правило выборки (д):** равномерно, без повторов, `random.Random(37)` (seed — номер плана), ровно 2 000 годных форм на семейство. Индекс раскладывается по осям смешанным основанием, полный перебор не материализуется. Генераторы 16-27…16-34 — реконструкция осей по сводкам (из инструмента 16-36). Генератор 16-36 — его `selfcheck_1636.py` в виде семейства.

| Семейство (план) | Полный перебор генератора | Прогнано |
|------------------|---------------------------|----------|
| ось B (16-27) | 43 120 | 2 000 |
| ось A (16-22, 16-28) | 48 264 | 2 000 |
| ось SQL (16-28) | 11 390 | 2 000 |
| носитель журнала (16-29) | 234 900 | 2 000 |
| кратность связывания (16-31) | 191 160 | 2 000 |
| способ подачи ссылки (16-32, 16-34) | 272 400 | 2 000 |
| лексика SQL (16-33) | 26 940 | 2 000 |
| класс конструктора колонки (16-33) | 154 224 | 2 000 |
| где прочитано имя обёртки (16-36) | 5 765 760 | 2 000 |

**Не прогнано выборкой:** 6 730 158 форм полного перебора генераторов (6 748 158 − 18 000). Кроме того:
- самопроверки 16-27…16-34 в прежнем виде — ≈550 000 форм, замер планирования 16-36;
- (е) 16-36 — 34 243 формы.

Обе вошли в корпус только выборкой. Самопроверка этого плана (е) прогнана целиком.

**Строки итогового прогона** (`bash .pytest_cache/r7diff/run.sh 16-37`, HEAD `0a4e4411`, 2026-10-19 08:54:10–09:01:35 UTC, выход 0) — дословно:

```
SELFTEST 1bebbbf7 -> c6953017: cells=2550 regressions=43 fixed=192 changed=235
SELFTEST 5e32c335 -> 147f5e46: cells=2550 regressions=52 fixed=145 changed=198
DIFF a6c87597 -> 51d0d766: cells=38402 regressions=0 fixed=288 changed=288
DIFF a53126a7 -> 2d59adff: cells=38402 regressions=0 fixed=5542 changed=5542
DIFF fa786d20 -> 0a4e4411: cells=38402 regressions=0 fixed=0 changed=0
BASE df9cea19 -> HEAD 0a4e4411: cells=38402 regressions=0 fixed=5830 changed=5830
OPEN_REGRESSIONS=0
```

**Регрессий нет** ни на одном GREEN, поэтому циклов сверки не было.

**Промежуточные прогоны:**
- после GREEN задачи 1 (HEAD `51d0d766`, корпус 21 760, sha `a6d3365c…`): `DIFF a6c87597 -> 51d0d766: regressions=0 fixed=64`, `BASE df9cea19 -> HEAD 51d0d766: regressions=0`, `OPEN_REGRESSIONS=0`, выход 0;
- после GREEN задачи 2 (HEAD `2d59adff`, корпус 21 768, sha `3bfcd31d…`): `DIFF a53126a7 -> 2d59adff: regressions=0 fixed=190`, `BASE … regressions=0 fixed=254`, `OPEN_REGRESSIONS=0`, выход 0.

**Неверные ячейки на HEAD** — только объём 16-38 (CR-02 и WR-25). Они остались неверными и не регрессии:
- (в): CR-02-1…7 и WR-25-1, WR-25-2;
- (б): приватность `map-named-iterable` — 36, `starmap` — 12;
- (г): 99;
- (д) «способ подачи ссылки»: 42.

Ячейки `named-wrapper-getattr`, `wrapper-handed`, `wrapper-of-wrapper`, `named-wrapper-handed` и формы WR-24 / WR-26 на HEAD верны.

## Files Created/Modified

- `tests/test_phone_privacy_gate.py`:
  - ввоз пяти функций общего модуля;
  - `_log_wrapper_reference`, `_carrier_wrappers` на общей функции, `_log_wrappers_of`;
  - `python_log_calls` по `wrapper_applications`, дедупликация в `python_log_offences`;
  - трасер, 9 + 1 строк, утверждение «одно место» в правиле строк, места проверки в правиле шапки;
  - шапка, комментарий ввоза, комментарий правила шапки.
- `tests/test_phone_gates_parity.py` — `CARRIER_SEMANTICS` (+3), `REQUIRED_SHARED_NAMES` (+5), комментарий и докстринг.
- `tests/phone_gate_grammar.py` — только докстринг `carrier_wrapper_bindings`.

## Decisions Made

См. `key-decisions`. Ещё одно: у гейта приватности, в отличие от писателя, первым позиционным `partial` теперь тоже проверяется предикат ссылки целиком, включая `methodcaller`. `partial(methodcaller(…), logger)` больше не обёртка носителя. Ответ не потерян: такую форму судит место связывания (`_applied_log_methodcaller` на самом `partial`). Сверка: регрессий 0 на 38 402 ячейках.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Комментарий ввоза: формула плана «`reference_arguments` её не зовёт» ложна**
- **Found during:** задача 3, GREEN.
- **Issue:** общая `reference_arguments` → `_carried_by` → `elementwise_arguments` зовёт `iterable_elements` у поэлементного носителя (`tests/phone_gate_grammar.py:480`). При `every_reading` её же зовёт прочтение `starmap` (`:741`).
- **Fix:** комментарий говорит, что гейт зовёт `iterable_elements` и сам — в пути `methodcaller` (`_applied_log_methodcaller`), а общая `reference_arguments` доходит до неё только через `elementwise_arguments` у поэлементного носителя. Выведенная таблица не названа. Обе проверки плана (`header_t3.py`) и правило шапки зелёные.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Committed in:** `0a4e4411`.

**2. Критерий задачи 1 `grep -c "applied_wrapper(" ≥ 1` после задачи 2 даёт 0**
- На GREEN задачи 1 (`51d0d766`) он давал `1`.
- Задача 2 по плану переносит ветку «вызов имени обёртки» в общую `wrapper_applications`, а применение там строит общая `applied_wrapper`. Прямого вызова в модуле гейта больше нет; имя ввезено и держится тем же объектом (`REQUIRED_SHARED_NAMES`, `shared_names_t1.py` — `OK`).
- Искусственный текст ради грепа не добавлялся.

**3. Числа плана и замер (замер правит, строки не тронуты):**

| Что | План | Замер |
|-----|------|-------|
| гейт писателя | ≥ 571 | **574** (прибавка 16-36) |
| три модуля | ≥ 819 | **822** |
| quick run фазы | ≥ 1223 | **1226** |
| `REQUIRED_SHARED_NAMES` | ≥ 10 | **11** (после задачи 2) |

**4. Инструмент сверки (gitignored, коммитов нет):**
- `corpus.py`: seed 37, ожидание `unique` у `NEGATIVE_CONTROLS`, семейство `e-wrapper-read-1636`;
- `judge.py`: `unique_places`, вид `phone_unique`;
- `selfcheck_1637.py`, в том числе аргумент дерева для контроля против вакуума.

---

**Total deviations:** 1 исправлено автоматически (Rule 1). Остальное — расхождение критерия и чисел, описано выше, и правка gitignored-инструмента.
**Impact on plan:** правки только в `files_modified`. Реестр `{}`, потолок 0, заявление шапки, прежние строки и JS-половина не тронуты. Модуль гейта писателя не правился.

## Замены команд (песочница worktree, хост)

- Команды `<automated>` / `acceptance_criteria` с `python -c` записаны дословно в `.pytest_cache/checks/*.py` и запущены с `PYTHONPATH=.`: `rows_task1.py`, `shared_names_t1.py`, `one_place_t1.py`, `cycles_t2.py`, `rows_t2.py`, `header_t3.py`, `registry_t3.py`, `js_t3.py`. Логика та же.
- Heredoc с `cat >` песочница отклонила, файлы записаны инструментом Write.
- `git show 65e5c692:… > .pytest_cache/r7_base_privacy.py` прошёл простой командой. `run.sh` зовёт `git log` / `git archive` из bash, отказов не было.
- Полную суиту (~46 мин) не гнал: её гоняет оркестратор после слияния.
- `graphify update .` не запускал (orchestrator_notes). Ориентация — `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.

## Гейты на итоговом дереве (`0a4e4411`, 2026-10-19, под `flock`)

| Гейт | Итог | До плана |
|------|------|----------|
| `test_phone_privacy_gate.py` + `test_phone_gates_parity.py` + гейт писателя | 822 passed | 811 |
| гейт писателя отдельно | 574 passed | 574 |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| quick run фазы (8 путей) | 1226 passed | 1215 |
| `tests/test_application` | 859 passed | 859 |
| сквозные гейты (htmx_post_pairs, htmx_gates, test_templates, declared_invariants) | 576 passed | 576 |
| `tests/test_logging_config.py` | 3 passed | 3 |
| `compileall -q app main.py tests` | код 0 | код 0 |
| `scripts/prohibitions_census.py --check` | код 0, «реестр: 856 строк, биекция с переписью — согласие» | то же |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| task-1 #2 / acceptance | `OK 117 49 119 49` (задача 1), `OK 117 49 126 50` (итог) / `OK 10`, `OK` | — |
| task-2 #2 / acceptance | `OK one function, cycles` / `OK 126 50` | — |
| task-3 #2 / реестр / JS | `OK` / `OK` / `OK 27 0` | — |
| `run.sh 16-37` | выход 0, `OPEN_REGRESSIONS=0` | — |
| `tests/test_planning` | гонится после коммита сводки (финальное сообщение) | 218 passed, 2 skipped |

## TDD Gate Compliance

- `git log --grep='^test(16-37)'` — 3 коммита: `a6c87597`, `a53126a7`, `fa786d20`.
- `--grep='^feat(16-37)'` — 3 коммита: `51d0d766`, `2d59adff`, `0a4e4411`.
- Каждый `test` стоит перед своим `feat`. REFACTOR-коммитов нет. Нарушений нет.

## Issues Encountered

Нет. Самопроверка и сверка не нашли ни непойманной формы, ни регрессии. Контроль против вакуума — тот же генератор на дереве базы — показал 5 408 промахов и 168 повторов места.

## Остатки и открытое (deferred-items.md не создавался — orchestrator_notes 5)

1. **CR-02 и WR-25 гейта приватности** — объём 16-38. Неверные ячейки на HEAD перечислены выше; это готовый вход его сверки.
2. **Корпус (д) остаётся реконструкцией осей по сводкам** для 16-27…16-34. Семейство 16-36 взято из его собственного генератора.

## Known Stubs

Нет.

## Threat Flags

Нет: правились только тестовые гейты и общий модуль тестов.

## User Setup Required

None — внешней настройки нет.

## Next Phase Readiness

- Вход 16-38: гейт приватности на общих функциях обёртки. `wrapper_applications` зовётся без `every_reading`. Модуль гейта приватности не определяет имён `GRAMMAR_FUNCTIONS`.
- Инструмент сверки лежит в `.pytest_cache/r7diff/` вместе с `trees/`, `judged/`, `selfcheck_cells.json` и `selfcheck_1637.py`.
- Фаза остаётся в `gaps_found` до 16-38…16-40 и повторной верификации. PHONE-21 в REQUIREMENTS.md не отмечался.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-19*

## Self-Check: PASSED

- Файлы на месте: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/phone_gate_grammar.py`, `.pytest_cache/r7diff/{corpus.py,judge.py,run.sh,selfcheck_1637.py}`.
- Коммиты плана в истории ветки: `a6c87597`, `51d0d766`, `a53126a7`, `2d59adff`, `fa786d20`, `0a4e4411`. `git rev-list --count df9cea19..0a4e4411` = 6.
