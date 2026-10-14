---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 29
subsystem: testing
tags: [ast, phone, privacy-gate, binding-grammar, reference-carrier, methodcaller, parity, tdd, wr-17]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "общий модуль `tests/phone_gate_grammar.py` плана 16-27 (`module_bindings`, `binding_name`, `Binding`, `BINDING_FORMS`, `OUT_OF_GRAMMAR_BINDING_FORMS`, `REFERENCE_KEYWORDS`, `ELEMENTWISE_CARRIERS`, `REFERENCE_CARRIERS`, `IdentificationValue`, `binding_form_source`) и `API_IDENTIFICATION_VALUES` гейта писателя"
provides:
  - "гейт приватности: ссылка на вызываемое журнала, поданная носителю (любой вызов; `to_thread`, `run_in_executor`, `map`, `Context.run`, `run_sync`, `fn=`), — синтетический вызов журнала с аргументами после ссылки (`_carried_log_calls`)"
  - "гейт приватности: `operator.methodcaller`, применённый к опознанному журналу прямо, через связанное имя, носителем, `map`, `fn=` (`_applied_log_methodcaller`); псевдонимы `partial` и `methodcaller` (`_wrapper_aliases`)"
  - "гейт приватности на общей грамматике связывания (`module_log_names` на `module_bindings`, свой `_binding_pairs` снят)"
  - "правило-матрица `test_every_binding_form_of_a_log_reference_is_judged` (270 ячеек) и модуль правила-паритета `tests/test_phone_gates_parity.py` (построение, согласие на 270 ячейках, формы вне грамматики)"
  - "шапка гейта приватности: абзац «ПО НОСИТЕЛЮ ССЫЛКИ», общая грамматика, цена строгости с местами живого дерева, граница со ссылками вне грамматики, летопись WR-17"
affects: [16-30, phase-17, phase-18, phase-19, phase-20]

actuals:
  tokens: 14251
  tasks: 3
  commits: 12
plan_head_before: 922b915ffdceb6c45a9f5de3099e8bb997a591a4
plan_head_after: e2807607

tech-stack:
  added: []
  patterns:
    - "Носитель ссылки — любой вызов: синтетический `ast.Call(<ссылка>, <аргументы после неё>)` на месте носителя судится как вызов журнала"
    - "`methodcaller` судится по получателю применения, а не по имени метода"
    - "Правило-паритет сравнивает вердикты двух гейтов на ячейках одной функции `binding_form_source`; формы вне грамматики — против базы с несвязанным именем"

key-files:
  created:
    - tests/test_phone_gates_parity.py
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Носитель ссылки — любой вызов, а не закрытый перечень; ссылка без аргументов за ней вызовом журнала не считается (определение носителя, убирает 15 из 18 ложных распознаваний наивного правила)"
  - "`fn=` (`REFERENCE_KEYWORDS`): носитель подаёт ссылке все свои позиционные аргументы; у `methodcaller` под `fn=` получатель — первый позиционный (самопроверка, заход 1)"
  - "`functools.partial` и `operator.methodcaller` под псевдонимом ввоза или связывания разрешаются одним помощником `_wrapper_aliases` до опознания журнала (паритет с гейтом писателя, самопроверка, заход 1)"
  - "Правило «формы вне грамматики» сравнивает не сырые находки, а прирост над базой с несвязанным именем (`never_bound_fn`), и для каждой формы — с прямым вызовом и всеми носителями, а не только прямым вызовом"
  - "Ссылка на вызываемое журнала, связанная вызовом или через пространство имён (`setattr`, `globals()`, `vars()`), из контейнера, результатом не-`partial` вызова или `lambda`, названа в «ГРАНИЦЕ СРЕДСТВА» с причиной «поток данных», как пункт (1) гейта писателя"

patterns-established:
  - "Самопроверка гейта приватности — композиция осей «форма связывания × значение опознания × получатель × метод × способ вызова × форма аргумента»; формы вне грамматики сверяются с базой"

requirements-completed: [PHONE-21]

coverage:
  - id: D1
    description: "`await asyncio.to_thread(logger.info, …, account.phone)` в подложенном `app/services/planted_offload.py` синтетического дерева краснит гейт тем же обходом; шесть форм носителя (to_thread, run_in_executor, map, Context.run, emit → to_thread, run_sync) — находки; не-журнальная ссылка и ссылка без аргументов — нет"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_log_reference_handed_to_to_thread_reddens_the_gate"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found"
        status: pass
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_recommended_form_does_not_redden_the_python_half"
        status: pass
    human_judgment: false
  - id: D2
    description: "`methodcaller` над опознанным журналом (прямо, связанным именем, `map`, `fn=`) и `partial` под псевдонимом — находки; `methodcaller` без опознанного получателя — нет"
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
    description: "Правило-матрица гейта приватности: 9 форм × 5 значений × (прямой вызов + 5 носителей) = 270 ячеек, ноль промахов"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_every_binding_form_of_a_log_reference_is_judged"
        status: pass
    human_judgment: false
  - id: D4
    description: "Правило-паритет обоих гейтов: построение (общий модуль ввезён, своих копий нет, объекты те же, id совпадают), согласие на 270 ячейках, формы вне грамматики не разрешены ни одним гейтом (60 ячеек)"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_take_the_binding_grammar_and_carriers_from_one_module"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_agree_on_every_binding_form_identification_and_carrier"
        status: pass
      - kind: unit
        ref: "tests/test_phone_gates_parity.py#test_both_gates_leave_the_same_forms_out_of_the_grammar"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шапка гейта приватности называет носителя ссылки, каждый носитель, `methodcaller`, общую грамматику, правило-паритет, цену строгости местами `app/pages/history.py`, ссылки вне грамматики в границе; летопись WR-17"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
    human_judgment: false
  - id: D6
    description: "Живые деревья: app 100 / 224, scripts 4 / 68, max_worker 2 / 93, находок 0; новые вызовы — ровно `app/pages/history.py` (288, 20), (289, 20), (293, 20); реестр `{}`, потолок 0"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_no_number_reaches_a_python_log_call_in_the_live_trees"
        status: pass
      - kind: other
        ref: "сверка множеств вызовов по 106 файлам против 33a31ee3 (scratchpad 1629_callset_diff.py): added 3, removed 0"
        status: pass
    human_judgment: false

duration: 47min
completed: 2026-10-14
status: complete
---

# Phase 16 Plan 29: Носитель ссылки на журнал, `methodcaller` и правило-паритет гейтов — Summary

**Гейт приватности теперь видит ссылку на метод опознанного журнала, поданную любому вызову с аргументами за ней (`asyncio.to_thread`, `loop.run_in_executor`, `map`, `Context.run`, `run_sync`, `fn=`), и `operator.methodcaller`, применённый к журналу. Связывания он берёт из общей грамматики `tests/phone_gate_grammar.py`, а новое правило-паритет `tests/test_phone_gates_parity.py` краснит любое расхождение двух гейтов. Самопроверка композицией прошла 160 080 форм и нашла три класса пропусков; все три закрыты циклами RED/GREEN. Живые деревья — 224 / 68 / 93 вызова, находок 0.**

## Performance

- **Duration:** ≈47 мин
- **Started:** 2026-10-14T10:14:50Z
- **Completed:** 2026-10-14T11:02:16Z
- **Tasks:** 3 (плюс 3 цикла самопроверки)
- **Files modified:** 2 (1 новый)

## Accomplishments

- **Носитель ссылки (`_carried_log_calls`).** Любой вызов, который сам вызовом журнала не опознан, проверяется так. Ищется ссылка: первый слева позиционный аргумент без `*`, который является вызываемым журнала, или `fn=` с таким значением. Если за ссылкой есть аргументы, на месте носителя возникает синтетический вызов `<ссылка>(<аргументы после неё>, <именованные, кроме fn>)`, и он судится как вызов журнала.
- **`methodcaller` по получателю (`_applied_log_methodcaller`).** Правило ловит прямое применение, вызов имени или атрибута, связанных общей грамматикой, носитель с получателем за ссылкой, элементы литеральной итерируемой у `map` и первый позиционный аргумент у `fn=`. Без опознанного получателя вызова журнала нет.
- **Псевдонимы обёрток (`_wrapper_aliases`).** Помощник разрешает `from functools import partial as bind_`, `bind_ = functools.partial`, `from operator import methodcaller as mc`, `mc = operator.methodcaller` и `K.mc`.
- **Общая грамматика.** `module_log_names` строится на `module_bindings`, а собственный `_binding_pairs` снят. Распаковка со звёздной целью пришла автоматически.
- **Правила.** Добавлены трасер, правило-матрица (9 параметров) и правило шапки. Модуль паритета содержит 3 правила, всего 11 параметров.
- **Строки контроля.** `NEGATIVE_CONTROLS` выросли с 90 до 102, `POSITIVE_CONTROLS` — с 39 до 44. Все прежние строки байт в байт на месте.
- **Шапка.** «ПО СВЯЗЫВАНИЮ» называет общую грамматику и паритет. Добавлены:
  - абзац «ПО НОСИТЕЛЮ ССЫЛКИ»;
  - строка о псевдониме `partial`;
  - цена строгости с местами `app/pages/history.py`;
  - в границе — формы вне общей грамматики и ссылки вне грамматики с причиной;
  - летопись WR-17.

## Task Commits

1. **Задача 1 (трасер): носитель ссылки, общая грамматика.** `e293d1de` (test, RED), `9df72956` (feat, GREEN).
2. **Задача 2: `methodcaller`, правило-матрица, модуль паритета.** `22e1b6bb` (test, RED), `29249009` (feat, GREEN).
3. **Задача 3: шапка.** `5951e6f9` (test, RED), `334b0b9a` (feat, GREEN).
4. **Самопроверка, цикл 1 — `methodcaller` под `fn=`.** `67aed58b` (test), `aff284c9` (feat).
5. **Самопроверка, цикл 2 — псевдонимы `partial` (и `methodcaller` через тот же помощник).** `b20c2af7` (test), `90803f88` (feat).
6. **Самопроверка, цикл 3 (зонд) — ссылки вне грамматики в границе.** `b31e87d6` (test), `e2807607` (feat).

**Plan metadata:** коммит `docs(16-29)` с этой сводкой.

## RED-улики (три совпадения + классификатор)

Каждый RED снят отдельным прогоном `-k <цель>` с `--junit-xml` в gitignored `.pytest_cache/gsd-red/`. Прогон запускает помощник `1629_red.py` из scratchpad; он сохраняет настоящий код выхода. В каждом цикле есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех записях, перечисленных ниже.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_log_reference_handed_to_to_thread_reddens_the_gate` | `1 failed, 179 deselected` (exit 1) | «ссылка на метод журнала, поданная носителю, не опознана» | цель исполнилась; обход нашёл файл, `app: вызовов 0`, находки `[]`. Полный прогон: 8 failed — трасер, 6 строк носителя, строка `SendLog` |
| Задача 2 | `test_both_gates_agree_on_every_binding_form_identification_and_carrier[assign]` и `test_every_binding_form_of_a_log_reference_is_judged[assign]` | `18 failed, 187 deselected` (exit 1) | «расхождение гейтов» (54 вхождения) | промахи — ровно ячейки `methodcaller`, 6 на форму, 54 из 270; раздел «писатель ловит, приватность — нет». Правило построения было зелёным с первого прогона; на дереве `33a31ee3` оно дало бы две проблемы: нет ввоза общего модуля и свой `_binding_pairs` |
| Задача 3 | `test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier` | `1 failed, 194 deselected` (exit 1) | «шапка гейта приватности не называет носителя ссылки» | 12 недостающих мест; прежние пункты границы на месте |
| Цикл 1 | `…_is_found[methodcaller-handed-by-fn-keyword-with-a-logger]` | `1 failed, 195 deselected` (exit 1) | «номер в вызове журнала не найден» | `runner.call(logger, fn=methodcaller(…))` → `[]` |
| Цикл 2 | `…_is_found[partial-import-alias-of-a-log-method]` (+ `partial-assigned-alias-handed-to-to-thread`) | `2 failed, 196 deselected` (exit 1) | «номер в вызове журнала не найден» | `bind_(logger.info, …)(account.phone)` → `[]` |
| Цикл 3 | правило шапки | `1 failed, 197 deselected` (exit 1) | «шапка гейта приватности не называет носителя ссылки» | 5 непоименованных форм ссылки вне грамматики |

Первая попытка RED цикла 1 с `-k fn_keyword` не выбрала ни одного теста: id строки пишется через дефис. Классификатор вернул `INVALID_RED` (`tests: 0`), и GREEN не начинался. Повторный прогон с селектором `-k "keyword and methodcaller and handed"` дал `RED_EVIDENCE_OK`.

## Самопроверка исполнителя (задача 3; урок 16-18, 16-23; О-12 (а))

Скрипт `1629_selfcheck.py` лежит в scratchpad и в репозиторий не коммитится. Он однопроцессный и потоковый, работает под общим `flock`. Ячейку собирает `binding_form_source` общего модуля, с префиксом ввоза или связывания, если значение его требует. Скрипт подаёт `python_log_offences(…, "app/x.py")` композицию осей:

- **Формы связывания (16 + 2).**
  - 9 `BINDING_FORMS`.
  - 7 сверх таблицы: цепочка `g = f`, вложенная распаковка `(f, g), h = …`, список-цель, аннотированное `self.f: object =`, `:=` внутри comprehension, звёздная цель до звезды и после неё.
  - 2 `OUT_OF_GRAMMAR_BINDING_FORMS`.
- **Значения опознания (до 17 видов).**
  - `print`, `builtins.print`.
  - Функции из ввоза: `from logging import info`, `from logging import warning as warn_`.
  - Привязки: `bind_contextvars` полным путём и под псевдонимом.
  - Для каждого получателя и метода — атрибут `R.m`, `getattr(R, "m")`, `partial(R.m)`, `partial(R.m, args)`, `methodcaller("m", args)(R)`.
  - `getattr(logger, "m", None)`.
  - Псевдонимы `partial` (ввоз и присваивание) и `methodcaller` (ввоз, присваивание, атрибут класса).
- **Получатели (7):** `logger`, `self.log`, `logging`, `structlog.get_logger()`, `logger.bind(a=1)`, `logging.getLogger(__name__).getChild("x")`, `logger.parent`.
- **Методы (6):** `info`, `warning`, `ainfo`, `aerror`, `_log`, `bind`.
- **Способы (9):**
  - прямой вызов;
  - каждый из `REFERENCE_CARRIERS` (`run_sync`, `to_thread`, `run_in_executor`, `map`, `Context.run`);
  - `session.run_sync(fn=functools.partial(ref, …))`;
  - `runner.call(…, fn=ref)`;
  - `loop.run_in_executor(None, functools.partial(ref, …))`.
- **Формы аргумента (5):** `phone=account.phone`, `account.phone`, f-строка, ключ словаря `{"phone": v}`, литерал `+79991234567`.

Под заявлением находка обязана называть предмет формы аргумента. Для формы вне грамматики скрипт сравнивает находки «место — вид» с базой, где имя на месте вызова не связано (`never_bound_fn`). Прирост над базой значил бы, что гейт разрешил связывание.

| Заход | HEAD, время (UTC) | Форм под заявлением | `[]` под заявлением | Вне грамматики: подано / разрешено сверх базы | Закрыто коммитами |
|-------|-------------------|---------------------|---------------------|-----------------------------------------------|-------------------|
| 1 | `334b0b9a`, 2026-10-14 10:34 | 153 600 | **4 240** в двух классах: `methodcaller` под `fn=` с получателем среди позиционных (3 520: `runner.call(logger, fn=mc)`) и `functools.partial` под псевдонимом ввоза (720: `bind_(logger.info)`) | 19 200 / 0 | `67aed58b` / `aff284c9`; `b20c2af7` / `90803f88` |
| 2 | `90803f88`, 10:40 | 160 080 (+ псевдоним `partial` присваиванием, `builtins.print`, псевдоним `methodcaller` атрибутом класса, `getattr` с умолчанием) | **0** | 20 010 / 0 | — |
| зонд | `90803f88`, ≈10:43 | 11 форм связывания вне операторов | все `[]`. Уже названы в границе: параметр и умолчание, итерируемая без имени `phone`, получатель-параметр у `methodcaller`. Не названы для ссылки: `setattr(self, "f", …)`, `globals()["f"]`, `vars(obj)["f"]`, контейнер `fns["i"](…)`, `staticmethod(logger.info)`, `attrgetter`, `make_emitter()`, `lambda`-обёртка | — | `b31e87d6` / `e2807607` (названы в «ГРАНИЦЕ СРЕДСТВА» с причиной «поток данных», как пункт (1) гейта писателя) |
| 3 (итог) | `e2807607`, 10:50 | **160 080** | **0** | **20 010 / 0** | — |

**По осям на заходе 3:**
- по 10 005 форм на каждую из 16 форм связывания;
- по 18 160 форм на каждый способ, кроме `runner.call(…, fn=)`; у него 14 800;
- по видам значений:
  - атрибут, `getattr`, `partial`, `methodcaller` — по 30 240;
  - `partial` с привязанными аргументами — 26 880;
  - `getattr` с умолчанием — 4 320;
  - остальные девять видов — по 720.

Пропущено 3 780 ячеек. Это сочетание `partial` с привязанными аргументами и способа `runner.call(…, fn=)`: при пустом списке аргументов шаблон `call(, fn=…)` синтаксически невозможен. Пропуск не связан с предикатом.

Из 20 010 ячеек вне грамматики 16 650 дают `[]`. Остальные 3 360 дают находку, равную базе, то есть связывание не разрешено: значение несёт номер само (`partial(R.m, args)` и `methodcaller("m", args)` с аргументами записи — их вызов сам по себе судится у себя).

## Живые деревья и сверка множеств вызовов

Команда `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -s -k live_trees` печатает:

`Python-половина гейта приватности: app: файлов 100, вызовов 224, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0`

Скрипт `1629_callset_diff.py` сверяет множества распознанных вызовов `(строка, столбец)` по каждому из 106 файлов против гейта на `33a31ee3` (сохранённая копия `.pytest_cache/privacy_gate_33a31ee3.py`). Сверка гонялась после задачи 1, после задачи 2 и после цикла 2:
- **added 3:** `app/pages/history.py` (288, 20), (289, 20), (293, 20);
- **removed 0:** прочие 105 файлов совпадают.

Три новых вызова — цена строгости, названная планом и шапкой: `log` там — запись `SendLog`, и её член, поданный вызову с аргументом за ним, судится как ссылка на метод журнала. Находок на этих вызовах нет. `methodcaller`, псевдонимы и граница числа не сдвинули.

`PHONE_LOG_EXCEPTIONS == {}`, `PHONE_LOG_EXCEPTIONS_CEILING == 0`.

## Files Created/Modified

- **`tests/test_phone_gates_parity.py`** (новый, 232 строки).
  - Шапка-обоснование О-12 (а).
  - `own_grammar_problems`, `_writer_finds`, `_privacy_finds`, `_resolves_binding`.
  - Три правила `test_both_gates_*`; ячейки собирает только `binding_form_source`.
- **`tests/test_phone_privacy_gate.py`** (+660 / −48 по сумме диффа плана).
  - Ввоз общего модуля.
  - `METHODCALLER_NAMES`; поля `methodcaller_names`, `methodcallers`, `partial_names` у `ModuleLogNames`.
  - Новые функции: `_wrapper_aliases`, `_methodcaller_calls`, `_is_identified_log_call`, `_carried_log_calls`, `_iterable_elements`, `_applied_log_methodcaller`, `_grouped`.
  - `module_log_names` на `module_bindings`; `_binding_pairs` снят.
  - `LOG_IDENTIFICATION_VALUES`; три новых правила; 12 строк `NEGATIVE_CONTROLS` и 5 строк `POSITIVE_CONTROLS`; шапка.

`tests/phone_gate_grammar.py` и гейт писателя не правились: самопроверка не нашла формы, которую закрывала бы правка общей грамматики. Гейт писателя прогнан на этом дереве: 456 passed. JS-половина не тронута.

## Decisions Made

Главные решения — в `key-decisions` во frontmatter:
- **Носитель — любой вызов; «за ссылкой есть аргументы» — часть определения носителя.** Это определение, а не граница.
- **`fn=` у вызываемого журнала передаёт все позиционные аргументы.** У `methodcaller` под `fn=` получатель — первый позиционный аргумент.
- **Правило «формы вне грамматики» сравнивает прирост над базой с несвязанным именем.** Это заметка 16-27 о `methodcaller` со всеми аргументами записи. Правило гоняет и носителей: 60 ячеек вместо 10 у прямого вызова.
- **Связывание вызовом или пространством имён, контейнер, не-`partial` вызов и `lambda` для ссылки названы в границе.** Причина та же, что у гейта писателя (паритет О-12 (а)); новых строк `OUT_OF_GRAMMAR_BINDING_FORMS` нет.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — критично для заявления] Два класса пропусков самопроверки и непоименованные формы зонда**
- **Found during:** самопроверка задачи 3, заход 1 и зонд после захода 2.
- **Issue:** формы под заявлением давали `[]` (таблица самопроверки).
- **Fix:** три цикла RED/GREEN:
  - строки `NEGATIVE_CONTROLS` `methodcaller-handed-by-fn-keyword-with-a-logger`, `partial-import-alias-of-a-log-method`, `partial-assigned-alias-handed-to-to-thread`;
  - ветка `fn=` в `_applied_log_methodcaller`;
  - `_wrapper_aliases`;
  - пункт границы и пять новых проверок в правиле шапки.
- **Files modified:** `tests/test_phone_privacy_gate.py`.
- **Verification:** заход 3 — 0 из 160 080.
- **Committed in:** `67aed58b`…`e2807607`.

**2. Правило шапки дополнено в цикле 3 (RED `b31e87d6`)**
- **Причина:** план требует, чтобы граница называла каждую непойманную форму. Зонд нашёл формы, которых шапка для ссылки не называла.
- **Что сделано:** правило теперь требует пять мест. Прежние проверки не ослаблены.

**3. Правило вне грамматики шире плана**
- План: «× прямой вызов». Сделано: прямой вызов и каждый носитель; вердикт — прирост над базой, а не сырые находки.
- **Причина:** заметка 16-27 и указание оркестратора — сравнивать грамматику, а не число находок. Учёт носителей только усиливает правило.

**4. План против замера (замер побеждает, прежние строки не ослаблены)**

| Величина | В плане | Замер |
|----------|---------|-------|
| Гейт приватности после задачи 1 | ≥ 180 passed | 180 ✓ |
| Строки после задачи 1 | `OK 90 39 96 42` | `OK 90 39 96 42` ✓ |
| Живые деревья | 224 / 68 / 93, находок 0 | 224 / 68 / 93, 0 ✓ (после каждой задачи и цикла) |
| Сверка множеств вызовов | history.py 288/289/293 | ровно они, удалённых 0 ✓ |
| После задачи 2 | ≥ 205 (194 + 11) | 205 ✓ |
| Промахи матрицы после задачи 1 | только `methodcaller` | 54 ячейки `methodcaller` ✓ |
| Матрица 270 | `OK 270` | `OK 270` ✓ |
| Гейт приватности итог | ≥ 195 | 198 (195 + 3 строки самопроверки) |
| Строки итог | — | `OK 90 39 102 44` |
| Самопроверка | ≥ 5 000 форм | 160 080 (+ 20 010 вне грамматики) |
| Quick run фазы | 1030 на базе без паритета | 1069 (1030 + 28 приватности + 11 паритета) |

**Total deviations:** 3 цикла самопроверки по плану (Rule 2), расширение правила шапки, более широкое правило вне грамматики.
**Impact:** заявление шапки не сужено, реестр пуст, потолок 0, прежние 90 / 39 строк на месте, общий модуль не правился.

### Подстановки окружения (песочница worktree, указания оркестратора)

- **Третья команда `<verify>` задачи 1.** `git show 33a31ee3:<путь>` из Python-однострочника песочница не пускает. Файл сохранён простой командой в gitignored `.pytest_cache/privacy_gate_33a31ee3.py` (дифф с `33a31ee3` пуст). Та же логика сравнения исполнена над копией (`1629_rows_cmp.py`).
- **Node id с квадратными скобками под `flock` песочница отклоняет.** Помощник RED-улик принимает имя цели с токенами `__LB__` / `__RB__` и раскрывает их сам. Селекторы — через `-k`.
- **Общий scratchpad с параллельным исполнителем 16-28.** Он перезаписал мой `rows_cmp.py` своей проверкой. Его файл я не трогал, свои скрипты переименовал с префиксом `1629_` и проверил, что копии мои.
- **Полная суита (`just test`) не гналась.** Её прогоняет оркестратор после слияния на объединённом дереве.
- **`graphify update .` не запускался:** по указанию оркестратора.

## Issues Encountered

- **INVALID_RED на первой попытке цикла 1:** селектор не выбрал тестов. Классификатор это поймал, GREEN не начинался (см. RED-улики).
- **Синтаксически невозможный шаблон.** `runner.call(, fn=…)` при пустом списке аргументов уронил первый запуск самопроверки (`SyntaxError`). Такие ячейки исключены и посчитаны: 3 780.

## Gates on the final tree (`e2807607`, под общим `flock`)

| Гейт | Итог |
|------|------|
| `tests/test_phone_privacy_gate.py` | 198 passed |
| `tests/test_phone_gates_parity.py` | 11 passed |
| живое правило `-s -k live_trees` | app 100 / 224, scripts 4 / 68, max_worker 2 / 93, находок 0 |
| verify задачи 1 №3 (строки, ввоз, `_binding_pairs` снят) | `OK 90 39 102 44` |
| verify задачи 2 №3 | `OK 270` |
| реестр и потолок | `OK` |
| шапка (критерий задачи 3) | `OK` |
| оба гейта фазы + паритет | 665 passed |
| гейт писателя | 456 passed |
| quick run фазы (8 путей, с модулем паритета) | 1069 passed |
| `tests/test_application` | 741 passed |
| сквозные (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed (как на базе; новый модуль в их обходе `tests/` проходит) |
| `tests/test_logging_config.py` | 3 passed |
| `compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed |
| `tests/test_planning` | после коммита сводки — в итоговом сообщении |

## Notes for the merge with 16-28

- Общий модуль `tests/phone_gate_grammar.py` этим планом не правился, и конфликтов с 16-28 по нему нет.
- Правило-паритет зовёт гейт писателя через `phone_write_offences`, `KIND_SETATTR` и `API_IDENTIFICATION_VALUES`. На объединённом дереве его нужно прогнать вместе с обоими гейтами: 16-28 правит гейт писателя.

## Known Stubs

Нет.

## User Setup Required

Нет.

## Next Phase Readiness

16-30 может ссылаться на WR-17 коммитами `feat(16-29)`:
- `9df72956` — носитель ссылки;
- `29249009` — `methodcaller`;
- `334b0b9a` — шапка;
- `aff284c9`, `90803f88`, `e2807607` — циклы самопроверки.

Отложенных пунктов нет.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-14*
