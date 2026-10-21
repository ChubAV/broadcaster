---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 46
subsystem: testing
tags: [privacy-gate, phone, ast, methodcaller, base-head-diff, foreign-corpora, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт приватности 16-01…16-45 (дедупликация по узлу 16-41, общий reading_name 16-43); инструмент r8diff-16-44 в r9-inputs"
provides:
  - "python_log_calls судит каждое толкование узла: опознанный вызов журнала не закрывает путь methodcaller и применения обёрток (CR-04, C5–C7)"
  - "трасер test_a_planted_notice_with_a_methodcaller_sharing_a_print_name_reddens_the_gate; 9 строк NEGATIVE_CONTROLS, 2 строки POSITIVE_CONTROLS"
  - "шапка гейта приватности: «каждое толкование узла», «Летопись CR-04»; правило шапки с новыми местами"
  - "инструмент .pytest_cache/r9diff/ (gitignored) — чужие корпуса целиком, SELFTEST-CR04, REPRODUCE, EXTERNAL, COST, COST-OWN, адресаты HEAD_WRONG, режим --precommit"
affects: [16-47, 16-48, 16-49, 16-50]

actuals:
  tokens: 24000   # chars/4: отслеживаемый дифф 22 347 знаков (≈5 600) + инструмент r9diff ≈73 800 знаков (≈18 400, gitignored)
  tasks: 2
  commits: 4      # git rev-list --count d31d86db..472e30f6 (до коммита сводки)
plan_head_before: d31d86db7e3f6ef0ed2561479c8e7b4cc9b23a03
plan_head_after: 472e30f66880bef067229ad123791e9e99681d0f

tech-stack:
  added: []
  patterns:
    - "Каждое толкование узла судится; повтор места снимает дедупликация по узлу (строка, столбец, вид, предмет)"
    - "Сверка «база ↔ HEAD» с обязательным входом чужих корпусов, ожидание — из исходника, названные цены — закрытые группы"
    - "Ключ кеша деревьев и вердиктов — id блобов пяти файлов гейтов, а не ревизия"

key-files:
  created: []
  modified:
    - tests/test_phone_privacy_gate.py

key-decisions:
  - "Правка CR-04 — снять ветку закрытия после опознанного вызова, а не новая дедупликация: путь носителя для опознанного вызова пуст сам, повтор места снимает дедупликация 16-41"
  - "Запрет плана «не коммитить GREEN, не прогнав сверку» исполнен режимом run.sh --precommit: рабочее дерево судится как незакоммиченный GREEN до коммита, затем — штатный прогон после коммита"
  - "Свои семейства (к) взяты ниже потолков договора («до …»), корпус 116 675 ячеек — в пределах ориентира 120 000; полные размеры записаны"

patterns-established:
  - "HEAD_WRONG печатает адресата каждой неверной ячейки; ячейка без адресата — UNASSIGNED (дефект объёма плана)"
  - "REPRODUCE: отпечаток списка находок инструмента против results/*.json ревьюера — против вакуума судьи"

requirements-completed: []   # PHONE-21 в requirements плана; отметку Complete не ставим — вердикт фазы gaps_found, учёт ведёт оркестратор

coverage:
  - id: D1
    description: "Опознанный вызов журнала не закрывает путь methodcaller и обёрток: девять форм CR-04 / C5–C7 — по одной находке phone, двойники — вызов журнала без находки, матрица — 1 638 ячеек по одной"
    requirement: PHONE-21
    verification:
      - kind: unit
        ref: "tests/test_phone_privacy_gate.py#test_a_number_handed_to_a_python_log_call_is_found (9 новых строк)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK 9 2 1638"
        status: pass
    human_judgment: false
  - id: D2
    description: "Трасер: подложенная служба app/services/phone_notify.py находится обходом живого дерева одной находкой :10"
    requirement: PHONE-21
    verification:
      - kind: integration
        ref: "tests/test_phone_privacy_gate.py#test_a_planted_notice_with_a_methodcaller_sharing_a_print_name_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D3
    description: "Шапка называет суд каждого толкования узла и летопись CR-04; правило шапки держит эти места"
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
    description: "Сверка «база ↔ HEAD» r9diff с чужими корпусами: DIFF по обоим GREEN и BASE — 0 / 0, OPEN_REGRESSIONS=0, самопроверка инструмента и REPRODUCE против вакуума"
    verification:
      - kind: other
        ref: "bash .pytest_cache/r9diff/run.sh 16-46 (выход 0, 2026-10-21 08:29–08:30 UTC)"
        status: pass
    human_judgment: false

duration: 80min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 46: суд каждого толкования узла (CR-04, C5–C7) и мера r9diff с чужими корпусами — Summary

**`python_log_calls` больше не закрывает путь `operator.methodcaller` и применения обёрток на узле, уже опознанном вызовом журнала: регрессия `a77263ad` и давний класс C5–C7 закрыты, на чужих корпусах неверных ячеек 2 754 → 972 (ровно замер прототипа), а инструмент `.pytest_cache/r9diff/` судит каждый GREEN на 29 941 ячейке ревьюера и верификатора с нулём регрессий обеих осей.**

## Performance

- **Duration:** ~80 мин
- **Started:** 2026-10-21T07:18:16Z
- **Completed:** 2026-10-21T08:38:00Z
- **Tasks:** 2 (каждая — RED и GREEN; циклов самопроверки и дифференциальной регрессии не понадобилось)
- **Files modified:** 1 отслеживаемый (`tests/test_phone_privacy_gate.py`, +282 / −4)

## Accomplishments

- Каждое толкование узла судится: `self.emit(logger)` при `emit = print` и `self.emit = operator.methodcaller("info", "x %s", account.phone)` даёт одну находку (было `[]` с `a77263ad`); формы C5–C7, которые пропускали все деревья, ловятся.
- Трасер с подложенной службой `app/services/phone_notify.py` — ровно `app/services/phone_notify.py:10 — имя — phone (владелец run)`.
- Девять строк `NEGATIVE_CONTROLS` (C1–C4, KC, C5–C7) и два двойника `POSITIVE_CONTROLS`.
- Шапка: пункт «ПО СВЯЗЫВАНИЮ» называет суд каждого толкования узла; новая «Летопись CR-04»; правило шапки держит обе вещи и докстринг `python_log_calls`.
- Инструмент r9diff: чужие корпуса — вход целиком после `sha256sum -c`, своё семейства (к1)…(к7), самопроверка на четырёх известных регрессиях, `REPRODUCE` против вакуума судьи, названные цены `COST-KW` / `COST-ATTR` закрытыми группами, адресат каждой неверной на HEAD ячейки.

## Task Commits

1. **Задача 1 (трасер): RED** — `2a1ac33d` (test) — трасер, 9 строк `NEGATIVE_CONTROLS`, 2 строки `POSITIVE_CONTROLS`
2. **Задача 1: GREEN** — `cbcf07e1` (feat) — суд каждого толкования в `python_log_calls`, докстринг
3. **Задача 2: RED** — `d5223cb7` (test) — правило шапки с новыми местами
4. **Задача 2: GREEN** — `472e30f6` (feat) — пункт «ПО СВЯЗЫВАНИЮ», «Летопись CR-04»

**Plan metadata:** коммит этой сводки (`docs(16-46)`).

## TDD: RED и GREEN

**RED задачи 1** (`2a1ac33d`). Прогон `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k "notice_with_a_methodcaller or shares-a or rebinds-a-print or share-a-name or carrier-whose-name" --junit-xml=.pytest_cache/gsd-red/16-46-t1.xml`:
- строка `FAILED tests/test_phone_privacy_gate.py::test_a_planted_notice_with_a_methodcaller_sharing_a_print_name_reddens_the_gate`;
- последняя строка сводки — `10 failed, 2 passed, 271 deselected, 1 warning in 0.74s` (трасер и девять строк);
- причинный литерал сообщения трасера в выводе (2 вхождения): «опознанный вызов журнала закрыл путь `methodcaller` на том же узле».
- `gsd check tdd-red-evidence .pytest_cache/gsd-red/16-46-t1.json` → `RED_EVIDENCE_OK` (`target_test_failed`, tests 12, fail 10, pass 2).
- Смысловая оценка: цель исполнена и упала на утверждении о находке (`in_file == []`); девять строк упали на `assert offences`; сбора, импорта, фикстур среди причин нет.
- Закрепки (зелёные до GREEN): `methodcaller-attribute-shares-a-module-print-name-without-a-number`, `methodcaller-handed-to-a-carrier-whose-name-is-print-without-a-number` — вызов журнала без находки уже на базе.

**GREEN задачи 1** (`cbcf07e1`): ветка `continue` после опознанного вызова снята; путь носителя для опознанного вызова не идёт (`elif`), путь `methodcaller` и обёртки — идут; новой дедупликации нет.

**RED задачи 2** (`d5223cb7`). Прогон `uv run pytest tests/test_phone_privacy_gate.py -q -p no:randomly -k test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier --junit-xml=.pytest_cache/gsd-red/16-46-t2.xml`:
- `FAILED tests/test_phone_privacy_gate.py::test_the_privacy_gate_header_names_the_shared_grammar_and_every_carrier`;
- последняя строка — `1 failed, 282 deselected, 1 warning in 0.47s`;
- литерал «шапка гейта приватности не называет носителя ссылки и общую грамматику» (2 вхождения; в дереве до плана `grep -c` = 1), недостающих мест 2: «каждое толкование узла», «Летопись CR-04».
- `RED_EVIDENCE_OK`. Закрепка: место «докстринг `python_log_calls` называет каждое толкование» зелёное до GREEN — его дописал GREEN задачи 1 (так велит действие задачи 1).

**GREEN задачи 2** (`472e30f6`): тексты шапки.

## TDD Gate Compliance

`test(16-46)` стоит перед своим `feat(16-46)` в обеих задачах: `2a1ac33d` → `cbcf07e1`, `d5223cb7` → `472e30f6`. `refactor` нет. Нарушений нет.

## Самопроверка исполнителя — ось коллизии «одно имя — два вида» (задача 2; О-20 (а), О-21 (а), свойство 4)

Генератор — `.pytest_cache/r9diff/selfcheck_1646.py` (gitignored). Суд — `judge.py` в отдельном процессе под общим `flock`. Прогон 2026-10-21 07:55–08:02 UTC, код предикатов — GREEN задачи 1 `cbcf07e1` (рабочее дерево; GREEN задачи 2 предикатов не трогал).

**Оси:**
- **Часть A.** Вызываемое журнала (`print`, `logger.info`, `getattr(logger, "info")`, `functools.partial(logger.info, "y")`, `logging.info`) под последним именем значения в пяти местах (модуль до формы, модуль после неё, функция, тело другого класса, `__init__` другого класса) × 6 значений `LOG_IDENTIFICATION_VALUES` × 13 форм `BINDING_FORMS` × прямой вызов и 20 носителей. Полный крест — **40 950**, без повторов исходника — 39 975.
- **Часть B.** Вызываемое журнала под последним именем вызова носителя (модуль, функция, тело класса; голое имя вызова — без места «модуль») × 5 вызываемых × каждый носитель × 6 значений, связанных с `f` и поданных носителю. Полный крест — **2 430**, без повторов — 2 400.
- **Часть C.** Безопасные двойники A и B (`.phone(s)` → `.name(s)`): 42 375.
- **Итого 84 750 форм** (повторов исходника отброшено 2 010).

**Ожидание:** точное число мест — узлов номера в исходнике (у всех форм A и B — 1); двойник — вызов журнала без находки.

| Дерево | Форм | Неверных | Итог |
|--------|------|----------|------|
| HEAD (`cbcf07e1`, рабочее дерево) | 84 750 | **0** | A — 39 975 по одной находке, B — 2 400 по одной, C — 0 |
| контроль против вакуума: база плана `d31d86db` | 84 750 | **940** | A 540, B 400; все — 1 → 0 |

На базе неверны ровно значения `methodcaller` и `methodcaller-receiver` (по 470): часть A — прямой вызов (540; места модуль до и после, функция, тело другого класса — по 120, чужой `__init__` — 60), часть B — 400 (функция 140, тело класса 140, модуль 120). Генератор видит CR-04 и C5–C7 там, где они были.

**Найдено:** ничего. Циклов самопроверки нет. Выборка 6 000 из 84 750 (seed 46) вошла в корпус сверки источником (е) `f-self-check`.

## Сверка «база ↔ HEAD» (r9diff; пункт 10 договора `<scope_note>`; свойство 7 О-21 (а))

### Чужие входы

`cp -a /source/broadcaster/.pytest_cache/r9-inputs .pytest_cache/r9-inputs`; `sha256sum -c --quiet MANIFEST.sha256` — 62 файла, совпадение (строка `INPUTS_OK files=62` в каждом прогоне). Шесть корпусов — вход целиком:

| Файл | Байт | sha256 | Ячеек |
|------|------|--------|-------|
| `verify-r9/corpus.json` | 9 880 738 | `5c6c4527733eef1541fe88f144c1a4fd97e74907cfb401b32c8c32fba6acb7f5` | 20 769 |
| `verify-r9/hand.json` | 13 135 | `9812cb4780a8201c1abb6774ccf652e4d6a2e1e625f165078261600edb7afd69` | 39 |
| `review-r8/corpusK.json` | 2 639 220 | `2ee9e5f2998a3606527efaaf2c80197c631af9e0d058e3afbae843c13a08481b` | 6 600 |
| `review-r8/corpusKC.json` | 654 066 | `5ae59c54cfc0ca5058e3d45c634828397b6da9202860b073a05f4ed7b8c249f7` | 2 106 |
| `review-r8/hand.json` | 37 454 | `b1e6dc9f04c8d80581999488373437405dcf1db0fe28a94d5b6180cea0a8a0a4` | 115 |
| `review-r8/rows.json` | 98 393 | `761690482879a829f2a4da9f8ec8bfbb6402645f0b5909f647b53f428b47766e` | 312 |
| итого | | | **29 941** |

Основа инструмента — `r8diff/r8diff-16-44.tgz` (sha256 `88bcd23e6e3e2c776c7fe12e48965faf3ebb2c3fb7c395ff9523737aebbbeb57`, 10 974 771 байт), распакован в новый пустой `.pytest_cache/r9diff-src/`.

### Инструмент

- `external.py` — источник (и): ячейки чужих корпусов в формате корпуса, `id` с префиксами `x-v9::`, `x-v9h::`, `x-r8K::`, `x-r8KC::`, `x-r8h::`, `x-r8r::`. Ожидание дословно: у verify-r9 `exp` (`n`, `min`, `subject`, `call`; семантика `verify-r9/tools/compare.py`), у review-r8 `expect` (целое или `null`). Исходник ревьюера — `textwrap.dedent`, путь — как у его `probe.py`.
- Названные цены — закрытые группы по `id`: `COST-KW` 301 (`x-v9::kw::*:partial-setattr:*:receiver` 300 и `x-v9h::x::KW-partial-setattr-dual`), число цены 2; `COST-ATTR` 122 (`x-v9::fp::*:class-body:*`, `x-v9::fp::*:other-init:*` — 120, `x-v9h::x::WR29-class-body-base-shape`, `x-r8h::F1-base-shape`), число цены 1. Свои: `kw` — (к5) пара `functools.partial(setattr, other)` и получатель-колонка; `attr` — (к3) тело класса и чужой `__init__`; `kw_ext` — (к6) значение `methodcaller-receiver` (расширение планирования, 16-48 выносит владельцу).
- `judge.py` — вердикт `[верно, число, отпечаток, двойник, статус ok|cost|wrong]`; смена числа ячейки цены между ожиданием и числом цены — ни регрессия, ни `REPAIRED`; режимы `--external`, `--cost`, `--reproduce`, `--wrong` с адресатом.
- `kfam.py` — источник (к); `corpus.py` — прежний r8diff плюс (и), (к), `f-self-1644`, `f-self-check` и пункт 6 договора (D2 писателя `methodcaller-receiver` — число узлов колонки).
- `run.sh` — строки договора по порядку; режим `--precommit`.

### Корпус итогового прогона

HEAD `472e30f6`, **116 675 ячеек**, `corpus.json` sha256 `af485593145226549e50031fbba1384a28353fa0b07fb4a06c3739d2731533f9`.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 259, `LEGITIMATE_CASES` 105, `NEGATIVE_CONTROLS` 165, `POSITIVE_CONTROLS` 55 | 584 |
| (б) матрица | `b-matrix` 13 форм × 6 значений × 21 способ × 2 гейта | 3 276 |
| (в) формы ревью | раунды 7–8, 16-42, 16-43 | 106 |
| (г) дифференциал раунда 7 | | 700 |
| (д) выборка самопроверок | 15 семейств по 2 000 (seed 42, как у 16-44) | 30 000 |
| (ж) две подачи на одной строке | D1 / D2; у D2 писателя `methodcaller-receiver` — `exact` 2 (пункт 6) | 3 276 |
| (з) безопасные двойники | | 6 552 |
| (е) `f-self-1644` | итоговая самопроверка 16-44: 20 000 из 66 690 (seed 42), D2 `methodcaller-receiver` — число узлов колонки | 20 000 |
| (е) `f-self-check` | самопроверка 16-46: 6 000 из 84 750 (seed 46) | 6 000 |
| (и) чужие корпуса | шесть файлов целиком | 29 941 |
| (к1) коллизия имени `methodcaller`, приватность | 3 000 из 9 000 (seed 46) | 3 000 |
| (к2) вызываемое под последним именем носителя | целиком | 1 590 |
| (к3) метод чужого объекта | 12 имён × 5 вызываемых × 4 места × 2 владельца + 120 двойников-находок | 600 |
| (к4) чтение через объект модуля | 5 чтений × 9 значений × 21 способ × 2 номера + 210 двойников «не журнал» | 2 050 |
| (к5) коллизия имени `methodcaller`, писатель | 3 000 из 9 000 | 3 000 |
| (к6) пишущий API под последним именем носителя | 3 000 из 3 856 | 3 000 |
| (к7) два применения одного значения | 3 000 из 3 480 | 3 000 |

**Не прогнано выборкой:** (д) 11 119 725 форм полного перебора генераторов (как у 16-44); `f-self-1644` — 46 690 (16-44 прогнала самопроверку целиком); `f-self-check` — 78 750 в корпус не вошли, но самопроверка прогнана целиком (84 750 на HEAD и на базе); (к1) 6 000, (к5) 6 000, (к6) 856, (к7) 480. Строки таблиц, матрица, формы ревью, дифференциал, (ж), (з), чужие корпуса, (к2), (к3), (к4) — целиком.

### Строки итогового прогона

`bash .pytest_cache/r9diff/run.sh 16-46` под общим `flock`, HEAD `472e30f6`, 2026-10-21 08:29:40–08:30:23 UTC (вердикты из кеша по ключу содержимого — тот же код судился в `--precommit` 08:02–08:29), выход 0. Дословно, без строки `EXTERNAL-CELLS` (stderr):

```
INPUTS_OK files=62
CORPUS_SHA256=af485593145226549e50031fbba1384a28353fa0b07fb4a06c3739d2731533f9 HEAD=472e30f66880bef067229ad123791e9e99681d0f
SELFTEST 1bebbbf7 -> c6953017: cells=3382 regressions=48 count_regressions=48 fixed=208 repaired_overcount=0 changed=256
SELFTEST 5e32c335 -> 147f5e46: cells=3382 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3602 regressions=831 count_regressions=885 fixed=378 repaired_overcount=354 changed=1317
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
DIFF 2a1ac33d -> cbcf07e1: cells=116675 regressions=0 count_regressions=0 fixed=2150 repaired_overcount=0 changed=2150
DIFF d5223cb7 -> 472e30f6: cells=116675 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE d31d86db -> HEAD 472e30f6: cells=116675 regressions=0 count_regressions=0 fixed=2150 repaired_overcount=0 changed=2150
EXTERNAL d31d86db: cells=29941 wrong=2754 cost_kw=281 cost_attr=122 defects=2351
EXTERNAL HEAD 472e30f6: cells=29941 wrong=972 cost_kw=281 cost_attr=122 defects=569
COST kw=281 attr=122
COST-OWN kw=203 attr=240 kw_ext=20
HEAD_WRONG=3100
OPEN_REGRESSIONS=0
```

- `SELFTEST` 48 / 56 и `SELFTEST-COUNT` 885 — те же, что у 16-44: инструмент на новом корпусе видит прежние регрессии.
- `SELFTEST-CR04` — 1 510 регрессий наличия (ревьюер K / KC 948, верификатор k / kc 400, свои (к1) / (к2) 162): мера видит `a77263ad`, которую мера раунда 8 пропустила.
- `REPRODUCE` — суд инструмента деревьями ревьюера совпал с его `results/<K|KC>.<дерево>.json` в каждой ячейке (отпечаток списка находок); строки `dbc73537` сверяют `*.HEAD.json` ревьюера (`e9449db5`, код гейтов = `dbc73537`).
- `fixed=2150` — `a-negative` 9 (строки плана), `x-v9-k` 560, `x-v9-kc` 260, `x-r8-K` 300, `x-r8-KC` 648, `x-r8-X` 7 (C1–C10 ревьюера), `x-v9-x` 7 (CR-04 и C5 / C7 верификатора), (к1) 93, (к2) 200, `f-self-check` 66. `REPAIRED` — 0, регрессий — 0.

**Чужие ячейки, расходящиеся с ожиданием** (обе оси):

| Ревизия | wrong | цена `kw` | цена `attr` | defects | по семействам |
|---------|-------|-----------|-------------|---------|---------------|
| база плана `d31d86db` (= родитель первого GREEN по коду) | 2 754 | 281 | 122 | 2 351 | `x-v9`: k 560, kc 260, fp 240, kw 280, dw 120, ручные 23; `x-r8`: K 300, KC 648, FP 300, ручные 23 |
| GREEN задачи 1 `cbcf07e1` и HEAD `472e30f6` | **972** | 281 | 122 | **569** | `x-v9`: fp 240, kw 280, dw 120, ручные 16; `x-r8`: FP 300, ручные 16 |

Это ровно замер прототипа планирования (972: `FP` 300, `fp` 240, `dw` 120, `kw` 280 — названная цена, ручные 16 + 16).

**`HEAD_WRONG=3100` по адресатам** (вне названных цен; адреса без `UNASSIGNED`):

| Адресат | Семейства | Ячеек |
|---------|-----------|-------|
| **16-47**, WR-29 (имя вызываемого журнала членом у чужого объекта) | `x-r8-FP` 300, `x-v9-fp` мест модуля и функции 120, ручные 8: `x-v9h::x::WR29-F1-write`…`F4-send`, `x-r8h::F1-write`…`F4-send`; своё (к3) мест модуля и функции 240 | 668 |
| **16-47**, WR-30 (получатель через объект модуля) | ручные 15: `x-v9h::x::WR30-1`…`WR30-7`, `x-r8h::KO-getattr-mod`, `KO-getattr-mod-default`, `KO-modattr`, `KO-mc-receiver`, `KO-carrier`, `KO-named-log`, `KO-chain-mod`, `KO-mod-bound`; своё (к4) 410 | 425 |
| **16-48**, WR-31 (запись через получатель — на узле получателя) | `x-v9-dw` 120; ручные 6: `x-v9h::x::WR31-two-lines`, `WR31-one-line`, `WR31-r8-block`, `x-r8h::WR28-W-block`, `TW4`, `TW5`; D2 писателя `methodcaller-receiver` по пункту 6: `g-double` 252, `f-self-1644` 493; своё (к7) 487 | 1 358 |
| **16-48**, коллизия имени носителя у гейта писателя | своё (к6) 649 | 649 |

`kw` 280 и `x-v9h::x::KW-partial-setattr-dual` — названная цена `COST-KW` (строка `COST`), не `HEAD_WRONG`.

**Промежуточные прогоны:**

| Прогон | HEAD / цель | Время (UTC) | Корпус | Строки | Выход |
|--------|-------------|-------------|--------|--------|-------|
| `--precommit` до GREEN задачи 1 | `2a1ac33d` → WORKTREE | 07:35:50–07:53:30 | 110 675, `7fd449a3…` | `DIFF 2a1ac33d -> WORKTREE` и `BASE d31d86db -> WORKTREE`: 0 / 0, `fixed=2084`; `EXTERNAL WORKTREE … wrong=972 … defects=569`; `HEAD_WRONG=3100`; `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-46` после GREEN задачи 1 | `cbcf07e1` | 07:54 | 110 675, `7fd449a3…` | `DIFF 2a1ac33d -> cbcf07e1` и `BASE … -> HEAD cbcf07e1`: 0 / 0, `fixed=2084`; прочее — как выше | 0 |
| `--precommit` до GREEN задачи 2 | `d5223cb7` → WORKTREE | 08:02:15–08:29:16 | 116 675 (с (е) 16-46), `af485593…` | `DIFF d5223cb7 -> WORKTREE` 0 / 0, `changed=0`; `BASE` 0 / 0; `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-46` итоговый | `472e30f6` | 08:29:40–08:30:23 | `af485593…` | строки выше | 0 |

**Регрессировавшие ячейки и закрывшие их коммиты:** нет — ни один GREEN не дал регрессии ни по наличию, ни по числу. **`REPAIRED`:** нет.

Инструмент оставлен на месте: `.pytest_cache/r9diff/` (с `trees/`, `judged/`, `corpus.json`, `selfcheck_cells.json` = самопроверка 16-46), `.pytest_cache/r9-inputs/`, `.pytest_cache/r9diff-src/`. 16-47…16-49 стартуют с копии оркестратора.

## Гейты на итоговом дереве (под общим `flock`)

| Проверка | Итог | База (оркестратор) |
|----------|------|--------------------|
| задача 1, №1: приватность + паритет | 305 passed | 293 |
| задача 1, №2: прежние строки | `OK 156 53 165 55` | — |
| задача 1, №3: формы, двойники, матрица, реестр | `OK 9 2 1638` | — |
| задача 1, №4: гейт писателя | 598 passed | 598 |
| задача 2, №1: три модуля гейтов | 903 passed | 891 |
| задача 2, №2: места шапки | `OK` | — |
| задача 2, №3: quick run фазы | 1307 passed | 1295 |
| задача 2, №4: сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) + `test_logging_config` | 576 passed + 3 passed | 576 + 3 |
| реестр исключений / JS-половина | `OK` / `OK 27 0` | — |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| живое дерево писателя | `OK 6 104` | `OK 6 104` |
| `tests/test_application` | 883 passed | 883 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 894 строк, биекция с переписью — согласие» | 894 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` (после коммита сводки `789117d3`) | 218 passed, 2 skipped | 218 / 2 skipped |

Полная суита (`just test`, ≈44 мин) не гонялась — её гонит пост-мердж гейт оркестратора. `graphify update .` не запускался — по поручению оркестратора после слияния.

## Decisions Made

- Правка — снять ветку закрытия, а не вводить новую дедупликацию: повтор места снимает дедупликация 16-41 по узлу, путь носителя для опознанного вызова пуст сам (`elif`).
- Запрет «не коммитить GREEN, не прогнав сверку» исполнен режимом `--precommit` до каждого GREEN-коммита и штатным прогоном после.
- Своё (к) — ниже потолков договора («до …»), чтобы корпус уложился в ориентир 120 000 (116 675).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — инструмент] Замыкание зависимостей основы r8diff.**
- Найдено: сборка инструмента, задача 1. `corpus.py` из `r8diff-16-44.tgz` ввозит `fam1639.py` и читает `selfcheck_cells_1641.json`, `selfcheck_cells_1642.json` — их нет в перечне пункта 1 договора.
- Исправлено: скопированы и они. `selfcheck_cells.json` 16-44 переименован в `selfcheck_cells_1644.json` и судится семейством `f-self-1644` той же выборкой (seed 42, 20 000), что у корпуса `fd55d467…`; имя `selfcheck_cells.json` занято самопроверкой 16-46.
- Проверка: `SELFTEST` 48 / 56, `SELFTEST-COUNT` 885 — как у 16-44; прежние источники дали 64 494 = 64 483 + 11 строк плана.

**2. [Rule 3 — инструмент] Ключ кеша — содержимое, а не ревизия; режим `--precommit`.**
- Найдено: запрет плана «MUST NOT коммитить GREEN, не прогнав сверку» против `run.sh`, который ищет GREEN по `^feat(16-46)` в истории.
- Исправлено: деревья и вердикты кешируются по id блобов пяти файлов гейтов; `--precommit` судит рабочее дерево как незакоммиченный GREEN (`DIFF <HEAD> -> WORKTREE`).
- Проверка: оба GREEN измерены до коммита (0 / 0) и после (0 / 0).

**3. [Rule 2 — против вакуума] `REPRODUCE` ещё и на `dbc73537`.** Сверх договора: `*.HEAD.json` ревьюера сняты с `e9449db5`, код гейтов которого = `dbc73537`. Совпадение 0 расхождений.

**4. [Rule 3 — замер] Размеры (к) и (е) ниже потолков договора.** (к1) 3 000 из 9 000, (к5) 3 000 из 9 000, (к6) 3 000 из 3 856, (к7) 3 000 из 3 480; `f-self-check` 6 000 из 84 750. Причина — ориентир «не больше 120 000 ячеек» и время суда (≈3 мс на ячейку). Полные размеры — выше; самопроверка прогнана целиком.

**5. [Находка вне объёма — адресат 16-48] Гейт писателя пропускает запись, когда последнее имя вызова носителя связано с пишущим API.**
- Найдено: семейство (к6), 649 ячеек на HEAD и на базе одинаково (давний класс): `run_sync = setattr` на уровне модуля и `session.run_sync(set_committed_value, account, "phone", x)` → 0 находок; то же для `to_thread`, `run_in_executor`, `run`, `Thread`, `Timer`, `starmap`, `enqueue`, `apply_async` и для API `setattr`, `update`, `set_committed_value`, `functools.partial(setattr, other)` в местах модуль, функция, тело класса.
- Это коллизия имени носителя у гейта писателя — объём 16-48 (строки `carrier-name-bound-to-setattr-…`, `executor-name-bound-to-update-…`, `context-run-name-bound-to-a-partial-…`). Гейт писателя этот план не трогает (заметка оркестратора 0). Сверх строк 16-48 (к6) показывает и API `set_committed_value` / `update` под именами `run_sync`, `to_thread`, `Timer`, `starmap` — 16-48 стоит судить семейство целиком.
- `HEAD_WRONG` относит все 649 к 16-48.

### Замены команд (песочница worktree)

- heredoc и `sed`-конвейеры отклонены — файлы скриптов писались инструментом Write; проверки `python -c` записаны дословно в `.pytest_cache/checks/*.py` и гнались с `PYTHONPATH=.`;
- цикл `for` вокруг `git` отклонён — ключ содержимого считает `run.sh`;
- ожидание длинных прогонов — `flock -w 580 <lock> true` (foreground `sleep` заблокирован);
- `graphify query` — с `--graph /source/broadcaster/graphify-out/graph.json`.

---

**Total deviations:** 4 по правилам 2–3 (инструмент и замер) и 1 находка вне объёма с адресатом 16-48.
**Impact on plan:** гейт и заявления — по плану; правки — в gitignored инструменте. Объём плана не расширен.

## Issues Encountered

- Одна лишняя команда: `uv run pytest tests/application_placeholder` (опечатка, «collected 0 items») — без последствий.

## Known Stubs

Нет.

## Threat Flags

Нет: правка — тестовый гейт; новых путей, сетевых точек и схем нет. T-16-106 и T-16-107 закрыты как в плане.

## Next Phase Readiness

- 16-47 стартует с копии `.pytest_cache/r9diff/`: его объём в `HEAD_WRONG` — 1 093 ячейки (WR-29 668, WR-30 425), плюс `cost_evidence.py` для `COST-ATTR`.
- 16-48: 2 007 ячеек (WR-31 1 358, коллизия имени носителя 649); отступление 5 — давний пропуск записи, шире перечня его строк.
- Отметку PHONE-21 и учёт не трогали (заметка оркестратора 5).

## Self-Check: PASSED

- Коммиты `2a1ac33d`, `cbcf07e1`, `d5223cb7`, `472e30f6` — предки HEAD (`git merge-base --is-ancestor`).
- Файлы на месте: `tests/test_phone_privacy_gate.py`, эта сводка, `.pytest_cache/r9diff/run.sh` (и весь каталог инструмента).
- Удалений в коммитах нет.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-21*
