---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 08
subsystem: testing
tags: [account-label, phone, grep-gate, jinja, ast, tdd, tracer, registry-by-occurrence]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: помощник подписи — макрос account_id_mark (components/account_label.html) и id_mark (app/services/account_label.py): единственные места печати # перед id аккаунта"
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-02…17-07: все экраны пользователя и админки переведены на помощника — на живом дереве остались только законные # (группа, помощник, partition)"
provides:
  - "tests/test_templates/test_account_label_gate.py: hash_id_findings(sources), python_hash_findings(sources), registry_violations(findings, registry), HashException(reason, subject)"
  - "TEMPLATE_HASH_EXCEPTIONS (3 вхождения) + TEMPLATE_HASH_EXCEPTIONS_DECLARED = 3; PYTHON_HASH_EXCEPTIONS (2 вхождения) + PYTHON_HASH_EXCEPTIONS_DECLARED = 2"
  - "18 тестов: контроли подложенными строками (К1, К2, пять двойников знака, Python, возврат Акк # перед группой, второй знак в обоих файлах помощника), вселенная непуста, замкнутость реестра"
affects: [17-09]

actuals:
  tokens: 6100
  tasks: 2
  commits: 4
plan_head_before: dd742c33f9084c58afc11962245945cb5e7c9d10
plan_head_after: 7f8fabc1a3312015d6c5d435fadda09d084b237d

tech-stack:
  added: []
  patterns:
    - "Гейт запрещает КЛАСС конструкции (К1 литерал на #, К2 # перед {{/{%, К3 Python-константа на #), а не перечень написаний; остаток назван границей в шапке и передан проходу по результату (17-09)"
    - "Реестр исключений адресует ВХОЖДЕНИЕ (путь#порядковый номер) и несёт предмет записи: проверка «за # стоит group_external_id / account_id / partition / [id_mark]» не даёт гейту спутать группу с аккаунтом"
    - "Число исключений — отдельные литеральные константы с летописью в шапке"

key-files:
  created:
    - tests/test_templates/test_account_label_gate.py
  modified: []

key-decisions:
  - "Запись реестра — NamedTuple HashException(reason, subject) с первой же задачи, а не dict[str, str] из задачи 1 с последующей перестройкой: предмет нужен контролю «аккаунт перед группой», и один тип на оба реестра проще двух параллельных словарей"
  - "registry_violations — отдельная чистая функция: даёт три названных отказа (вне реестра, устаревшая запись, чужой предмет) и одинаково служит живому дереву и контролям"
  - "Список двойников знака закрыт пятью написаниями плана; &#x23; и прочее названы границей, а не дописаны (урок Фазы 16, О-23)"

patterns-established:
  - "Контроль «возврат»: копия законного шаблона с вставленным прежним местом аккаунта перед законным местом группы краснит оба ключа (#0 — чужой предмет, #1 — вне реестра)"

requirements-completed: [PHONE-03, PHONE-06]

coverage:
  - id: D1
    description: "Сборка # перед идентификатором аккаунта в шаблоне (К1 — литерал на #, К2 — # перед подстановкой, пять форм-двойников) вне реестра краснит суиту; на живом дереве находок вне реестра ноль"
    requirement: "PHONE-03"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_control_a_planted_concatenation_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_control_a_planted_bare_markup_hash_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_every_registry_entry_points_at_its_declared_subject"
        status: pass
    human_judgment: false
  - id: D2
    description: "Реестр по вхождению с предметом: возврат Акк # перед законным # группы в history_card.html названа поимённо; второй знак в любом из двух файлов помощника выходит за реестр"
    requirement: "PHONE-06"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_control_an_account_hash_returned_before_the_group_one_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_control_a_second_mark_in_the_helper_is_named"
        status: pass
    human_judgment: false
  - id: D3
    description: "Python-половина (К3): строковая константа app/**/*.py на # вне реестра краснит гейт; законных два (partition, id_mark); вселенная непуста, числа 3 и 2 объявлены литералами"
    requirement: "PHONE-06"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_control_a_planted_python_hash_is_named"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_account_label_gate.py#test_the_universe_is_not_empty"
        status: pass
    human_judgment: false
  - id: D4
    description: "Граница гейта (идентификатор без #, подпись без литерала #, готовая строка из базы, JS на клиенте) названа в шапке и держится проходом по отрисованным экранам плана 17-09"
    requirement: "PHONE-06"
    verification: []
    human_judgment: true
    rationale: "Остаток по построению вне досягаемости исходного гейта; его закрывает проход 17-09, которого этот план не пишет"

duration: "≈25min (старт не замерён отдельной меткой; коммиты 20:16–20:22 UTC, прогоны гейтов до 20:26)"
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 08: Сквозной гейт подписи аккаунта

**Греп-гейт `tests/test_templates/test_account_label_gate.py` роняет суиту на сборку `#` перед идентификатором аккаунта вне помощника — по двум классам в шаблонах (К1 литерал на `#`, К2 `#` перед `{{`/`{%`), пяти формам-двойникам знака и одному классу в Python (К3, по `ast`); исключения — три шаблонных и два Python-вхождения с причиной и предметом, числа объявлены литералами.**

## Performance

- **Duration:** ≈25 мин (метка старта отдельно не снята; коммиты 20:16–20:22 UTC, гейты до 20:26)
- **Tasks:** 2 (обе `tdd="true"`; задача 1 — `type="tracer"`)
- **Files:** 1 создан (`tests/test_templates/test_account_label_gate.py`), продуктового кода не тронуто
- **Commits:** 4 (RED, GREEN, RED, GREEN)

## Accomplishments

- **Трассер (задача 1).** `hash_id_findings(sources)` принимает словарь исходников, вырезает комментарии `_strip_comments` (ввоз из `test_htmx_inventory`), ключ — `путь#порядковый номер`, нумерация по положению. Подложенный `{{ mono('#' ~ account.id) }}` назван `planted/k1.html#0`; комментарии (`{# '#' ~ … #}`, `<!-- … -->`) не считаются.
- **Класс К2, двойники знака, К3 (задача 2).** К2 `#\s*\{[{%]`; формы `&#35;`, `&num;`, `＃`, `\x23`, `#` — тем же ключом (описание начинается «двойник знака»). `python_hash_findings` — обход `ast` по `app/**/*.py` с именем объемлющей функции; находит и литеральную часть f-строки.
- **Реестр по вхождению, с предметом.** `HashException(reason, subject)`; `registry_violations` называет три отказа: находка вне реестра, устаревшая запись, чужой предмет за `#`. Контроль «аккаунт перед группой» краснит `history_card.html#0` (чужой предмет) и `#1` (вне реестра).
- **Помощник — единственное место.** Второй знак в `components/account_label.html` (`#1`) и в `app/services/account_label.py` (`#1`) выходит за реестр.
- **Граница названа в шапке** (абзац «ЧЕГО ГЕЙТ НЕ ВИДИТ», урок Фазы 16, О-23) и передана проходу 17-09.

## Замер живого дерева (dd742c33, после 17-01…17-07)

| Класс | Находок | Ключи |
|---|---|---|
| К1 (литерал на `#`) | 2 | `history/detail.html#0`, `history/includes/history_card.html#0` — оба `'#' ~ …group_external_id` |
| К2 (`#` перед подстановкой) | 1 | `components/account_label.html#0` — `#{{ account_id }}` (макрос `account_id_mark`) |
| Двойники знака | 0 | — |
| К3 (Python) | 2 | `app/pages/htmx.py#0` (`[_with_notice]`, `redirect.partition("#")`), `app/services/account_label.py#0` (`[id_mark]`, `return f"#{account_id}"`) |

Итого 3 шаблонных и 2 Python-вхождения — **ровно ожидание плана**, порядковые номера (`#0`) совпали; расхождений «план против замера» нет. Вне реестра находок ноль; оставшихся оффендеров в продуктовом коде нет, ни один продуктовый файл не правился.

## RED-улики (три совпадения + классификатор)

**Задача 1.** Команда `uv run pytest tests/test_templates/test_account_label_gate.py -q -p no:randomly --junit-xml=.pytest_cache/gsd-red/t1.xml`:

| Совпадение | Строка |
|---|---|
| `FAILED <путь>::<цель>` | `FAILED tests/test_templates/test_account_label_gate.py::test_control_a_planted_concatenation_is_named` |
| итог с `failed` | `2 failed, 1 passed, 1 warning in 0.34s` |
| причинный литерал | `AssertionError: assert 'planted/k1.html#0' in {}` |

`gsd_run check tdd-red-evidence` (JUnit XML): `RED_EVIDENCE_OK`, `target_test_failed`, 3 теста: 1 прошёл, 2 упали (цель и `test_the_scanner_ignores_comments`). **Семантическая оценка:** цель выполнилась и упала на утверждении плана — заготовка сканера возвращает `{}`, ключа подложенного шаблона нет. Второй красный (`ignores_comments`) падает по той же причине (`[] == ['planted/comments.html#0']`) — сделан невакуумным намеренно. `test_the_live_tree_…outside_the_registry` на заготовке зелёный вакуумом (пустое ⊆ реестра) — ожидаемо; невакуумность его пары даёт `test_every_registry_entry_points_at_its_declared_subject` и `test_the_universe_is_not_empty` задачи 2.

**Задача 2.** Команда та же, отчёт `t2.xml`:

| Совпадение | Строка |
|---|---|
| `FAILED <путь>::<цель>` | `FAILED tests/test_templates/test_account_label_gate.py::test_control_a_planted_bare_markup_hash_is_named` |
| итог с `failed` | `11 failed, 7 passed, 1 warning in 0.57s` |
| причинный литерал | `AssertionError: assert 'planted/k2.html#0' in {'history/detail.html#0': …, 'history/includes/history_card.html#0': …}` (сканер без К2 видит только два К1) |

`gsd_run check tdd-red-evidence`: `RED_EVIDENCE_OK`, `target_test_failed`, 18 тестов: 7 прошли, 11 упали. **Семантическая оценка:** цель выполнилась и упала на планируемом утверждении — К2 в сканере ещё нет. Одиннадцать красных — К2, живая запись компонента, пять двойников (параметры), подложенный Python, живой Python, второй знак, вселенная. Зелёными на RED остались семь, и среди них `test_control_an_account_hash_returned_before_the_group_one_is_named`: его хватает К1 (возврат `Акк #` — литерал) вместе с `registry_violations`, так что он охранник реестра по вхождению, а не цель RED; это разобрано, а не пропущено.

Улики лежат в `.pytest_cache/gsd-red/` (gitignored; на месте `.gsd/tdd-evidence/` — по указанию наряда оркестратора).

## TDD Gate Compliance

`git log -E --grep="^test\(17-08\):"` — 2 коммита (e4221f37, f0b2c829); `^feat\(17-08\):` — 2 (0fea4e35, 7f8fabc1); каждый GREEN — потомок своего RED. `refactor(17-08)` не потребовался. Нарушений нет.

## Task Commits

| Задача | Фаза | Коммит | Что |
|---|---|---|---|
| 1 | RED | `e4221f37` | `test(17-08): add failing control for the account hash gate (class K1)` |
| 1 | GREEN | `0fea4e35` | `feat(17-08): scan template string literals ending in a hash sign (class K1)` |
| 2 | RED | `f0b2c829` | `test(17-08): add failing controls for class K2, hash lookalikes and the Python half` |
| 2 | GREEN | `7f8fabc1` | `feat(17-08): scan bare-markup hash, hash lookalikes and Python constants (K2, K3)` |

`commits: 4` измерено `git rev-list --count dd742c33…HEAD` по леджеру `gsd-plan-head-before-17-08`.

## Verification

Все прогоны — под общим замком `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`, на финальном дереве (после GREEN задачи 2):

| Набор | База (195dccbd) | Итог |
|---|---|---|
| `tests/test_templates/test_account_label_gate.py -p no:randomly` | — (новый) | 18 passed |
| сквозной набор: `tests/test_templates tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_application/test_declared_invariants.py` | 576 | **594 passed** = 576 + 18 |
| вердикт плана: тот же набор + `tests/test_phone_privacy_gate.py` | — | 940 passed |
| три гейта номера: `test_phone_privacy_gate.py test_phone_gates_parity.py test_application/test_phone_single_writer_gate.py` | 1161 | **1161 passed** |
| `uv run python scripts/prohibitions_census.py --check` | exit 0, 953 строки | exit 0, «реестр: 953 строк, биекция с переписью — согласие» |
| `uv run python -m compileall -q app main.py tests` | exit 0 | exit 0 |
| `uv run pytest tests/test_planning -q -p no:randomly` до коммита сводки | 218 passed, 2 skipped | 218 passed, 2 skipped |

Критерии приёмки: `TEMPLATE_HASH_EXCEPTIONS_DECLARED, PYTHON_HASH_EXCEPTIONS_DECLARED == (3, 2)` — выход 0; `set(PYTHON_HASH_EXCEPTIONS) == {'app/pages/htmx.py#0', 'app/services/account_label.py#0'}` — выход 0; `^def hash_id_findings` = 1, `^def python_hash_findings` = 1, `test_htmx_inventory import _strip_comments` = 1, `def test_control_a_second_mark_in_the_helper_is_named` = 1, `ЧЕГО ГЕЙТ НЕ ВИДИТ` = 1, `planted/k2.html` = 2, `planted/k4.html` = 3.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed as written; ниже — выбор формы там, где план оставлял её открытой, и расширения сверх плана.

1. **Форма записи реестра.** План в задаче 1 называет реестр `dict[str, str]` («ключ → причина»), а предмет вводит в задаче 2. Реестр сразу сделан `dict[str, HashException]` (`reason`, `subject`): один тип на оба реестра, ключи те же (`set(g.PYTHON_HASH_EXCEPTIONS)` из приёмки работает как есть). Влияния на must_haves нет.
2. **Сверх плана — тесты:** пять подложенных двойников знака параметризованы по отдельности (план называл один `&#35;`); `test_the_live_python_has_no_account_hash_outside_the_registry` и `test_the_python_registry_declares_its_own_length` вынесены отдельными тестами (план держал их внутри теста 6); `test_the_scanner_ignores_comments` сделан невакуумным (живая склейка рядом с комментариями). Итого 18 тестов вместо 11 перечисленных поведений.
3. **Где лежит `registry_violations`.** Вынесена чистая функция сверки находок с реестром — план описывал те же три проверки внутри тестов; вынос нужен, чтобы живое дерево и контроли судились одним кодом.

**Total deviations:** 0 auto-fixed (три замечания выше — форма, не содержание). **Impact:** нет.

## Подстановки и ограничения среды

- **Полный прогон не делался** (`just test`, ≈5894 тестов, ≈41 мин): его ведёт post-merge гейт оркестратора. Вместо него — именованные наборы таблицы выше.
- **`graphify update .` не запускался** — в worktree нет графа (`graphify-out/` в gitignore); обновление за оркестратором при слиянии. `graphify query` тоже не вызывался: план целиком про один новый тестовый файл по прямым образцам, прочитанным по номерам строк.
- **Heredoc отклонён песочницей** при первой попытке дописать тесты — тот же текст внесён инструментом `Edit`; сборка записей RED-улики и печать находок живого дерева — скриптами `.pytest_cache/checks/mkred.py` и `live_findings.py` (`PYTHONPATH=.`), логика та же. Сборка записи RED: `gsd_run check tdd-red-evidence` принял JUnit XML напрямую.
- Базы, `.env`, alembic, приложение и Redis не трогались. STATE.md, ROADMAP.md, REQUIREMENTS.md, `*-PLAN.md`, CONTEXT/RESEARCH/PATTERNS и реестр запретов не правились; `requirements.mark-complete` и `state.*` не вызывались; `deferred-items.md` не заводился.

## Known Stubs

None. Подложенные строки для самопроверки сканера живут только в тестовых литералах и `tmp`-словарях, как продуктовые файлы они не создаются.

## Threat Flags

None. Новых маршрутов, путей доступа к файлам и границ доверия нет; план читает исходники `app/` и пишет один тестовый модуль. Угрозы плана закрыты: T-17-24 (вакуумный зелёный) — подложенные К1/К2/двойники/Python, `test_the_universe_is_not_empty` (множества находок равны реестрам), литеральные числа; T-17-25 (исключение на файл) — ключ по вхождению, предмет записи, контроль «аккаунт перед группой»; T-17-SC — установок нет.

## Что остаётся за границей гейта (передано плану 17-09)

Идентификатор без `#` (`Акк {{ id }}`), подпись из частей без литерала `#` (`chr(35)`, `'%c' % 35`), готовая строка из базы, текст, вставленный JS на клиенте, написания знака сверх пяти (`&#x23;`) — названы в шапке модуля и закрываются проходом по отрисованным экранам `tests/test_pages/test_account_label_sweep.py` (17-09), который судит результат, а не исходник. `overrides` ради зелёного не писались.

## Next Phase Readiness

План 17-08 закрывает критерий 5 ROADMAP в части «шаблон, пропущенный при замене, роняет суиту». Для 17-09 (проход по отрисованному результату и CSS) блокеров нет; его файлы (`tests/test_pages/test_account_label_sweep.py`, `app/static/css/app.css`, `tests/test_pages/test_responsive_markup.py`) этим планом не затронуты.

## Self-Check: PASSED

- Файл `tests/test_templates/test_account_label_gate.py` — на диске.
- Коммиты `e4221f37`, `0fea4e35`, `f0b2c829`, `7f8fabc1` — предки HEAD (`git merge-base --is-ancestor`).
- Приёмочные greps и два `python -c` критерия задачи 2 — зелёные (см. Verification).
