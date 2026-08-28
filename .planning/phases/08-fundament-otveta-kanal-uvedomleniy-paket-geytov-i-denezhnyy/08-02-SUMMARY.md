---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 02
subsystem: notices
tags: [notices, registry, closed-set, gates, tdd, foundation]
status: complete

requires: []
provides:
  - "app/pages/notices.py::Notice — NamedTuple (code, text, variant)"
  - "app/pages/notices.py::NOTICES — кортеж из 14 записей"
  - "app/pages/notices.py::notice_for(code) -> Notice | None"
  - "app/pages/notices.py::has_code(code) -> bool"
  - "app/pages/notices.py::_index(records) — сборщик с ValueError на дубле кода"
  - "14 модульных констант кода: RETRY_QUEUED … IMPERSONATION_FORBIDDEN"
affects:
  - "план 08-01 (respond(notice=...)) — потребитель кодов"
  - "план 08-04 (Jinja-глобаль notice_for, области #notice / #notice-alert)"
  - "план 08-06 (переписанные обработчики, снятие пяти частных написаний)"

tech-stack:
  added: []
  patterns:
    - "Закрытое множество вместо непустой строки (наследуется у трёх частных реестров)"
    - "Реестр собирается ИЗ ПАР с машинной уникальностью, а не литералом словаря (D-10)"
    - "Код едет КОНСТАНТОЙ, а не литералом (канон history.py)"
    - "Гейт, у которого перечень выписан в тесте, а не выведен из проверяемого (канон test_access_gate.py)"
    - "Зубы гейта доказаны группой -k control (канон test_impersonation_gate.py)"
    - "Границы гейта выписаны в докстринге (WR-08)"

key-files:
  created:
    - app/pages/notices.py
    - tests/test_pages/test_notices_registry.py
  modified: []

key-decisions:
  - "Реестр собран из кортежа записей; _index поднимает ValueError на втором вхождении кода и роняет ИМПОРТ модуля, а не отдельный запрос"
  - "notice_for возвращает None на неизвестном коде — «плашки нет вовсе», а не пустая рамка"
  - "`expired` вне реестра и вне объявленного перечня (D-11) — два независимых утверждения"
  - "Гейт переноса держит одиннадцать КОПИЙ строк у себя, а не читает модули-источники: источники снимает план 08-06, и читающий гейт позеленел бы навсегда"
  - "Контроль на ПРОПАЖУ перенесённой записи добавлен сверх плана: контроль на изменённый текст пропажу не покрывает"
  - "Вариант impersonation_forbidden — warning, а не error: это названное правило с известным выходом, а не поломка"

requirements-completed: [FOUND-05]

coverage:
  - deliverable: "Закрытый реестр уведомлений принимает КОД, а не текст"
    human_judgment: false
    verification:
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_an_unknown_value_draws_nothing_at_all"
        status: pass
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_a_moved_record_carries_its_text_and_variant_unchanged"
        status: pass
  - deliverable: "Дубль кода невозможен молча — сборка падает на импорте"
    human_judgment: false
    verification:
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_control_negative_a_duplicate_code_reddens_the_builder"
        status: pass
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_every_code_is_distinct_and_the_index_loses_nothing"
        status: pass
  - deliverable: "Признак редиректа гейта доступа кодом не является (D-11)"
    human_judgment: false
    verification:
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_the_access_redirect_flag_is_not_a_notice_code"
        status: pass
  - deliverable: "Одиннадцать перенесённых текстов совпадают с источниками посимвольно"
    human_judgment: false
    verification:
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_every_moved_text_matches_its_source_character_for_character"
        status: pass
      - kind: command
        ref: "сверка записей реестра с живыми RETRY_NOTICES / PAYMENT_ERROR_MESSAGES / WORKER_RESTART_ERRORS / SCHEDULE_ERROR_MESSAGE / IMPERSONATION_FORBIDDEN_DETAIL — 0 расхождений"
        status: pass
  - deliverable: "Реестр — ИСТОЧНИК текстов, а не второй читатель модулей-разделов"
    human_judgment: false
    verification:
      - kind: test
        ref: "tests/test_pages/test_notices_registry.py#test_the_registry_module_imports_no_page_module"
        status: pass
  - deliverable: "Формулировки двух новых текстов уместны на своих исходах"
    human_judgment: true
    rationale: "«Настройки сохранены.» и переезд текста отказа под чужой личностью на плашку — предмет UI-суждения; ни один тест не может утверждать, что формулировка хороша, только что она не изменилась"

metrics:
  duration: "51 min"
  completed: "2026-08-28"
  tasks: 2
  commits: 3
  files-created: 2
  files-modified: 0

actuals:
  tokens: 7743
  tasks: 2
  commits: 3
---

# Phase 8 Plan 02: Закрытый реестр уведомлений Summary

Пять частных микро-контрактов обратной связи сведены в один закрытый реестр кодов
`app/pages/notices.py`: четырнадцать записей `код → (текст, вариант)`, собранных из
пар с машинной уникальностью ключа, и четырнадцать гейтов, из которых четыре —
контроли, доказывающие, что гейты краснеют.

## Accomplishments

- **`app/pages/notices.py`** — единственный владелец текстов ИСХОДА ДЕЙСТВИЯ.
  `Notice(NamedTuple)` с полями `code`/`text`/`variant`; на каждую запись — модульная
  константа кода; `NOTICES` кортежем; `_index` сборщиком; `notice_for` и `has_code`
  входами.
- **Четырнадцать кодов** заведены и объявлены машинно: четыре исхода повтора, три
  отказа оплаты, два отказа перезапуска воркера, два отказа расписания, смена пароля,
  сохранение профиля, отказ под чужой учётной записью.
- **Двенадцать текстов перенесены дословно.** Помимо гейта на копиях, перенос сверен
  разово с ЖИВЫМИ источниками (`RETRY_NOTICES`, `PAYMENT_ERROR_MESSAGES`,
  `WORKER_RESTART_ERRORS`, `SCHEDULE_ERROR_MESSAGE`, `IMPERSONATION_FORBIDDEN_DETAIL`) —
  ноль расхождений. Один текст новый (`profile_saved`), и это названо в модуле прямо.
- **Дубль кода невозможен молча.** `_index` поднимает `ValueError` на втором вхождении и
  роняет импорт модуля. Литерал словаря Python перезаписал бы первую запись без единого
  признака — исход, о котором пользователю сообщали, исчез бы вместе со своим текстом.
- **`tests/test_pages/test_notices_registry.py`** — 14 утверждений: перенос текста и
  варианта, «неизвестное значение не рисует ничего», признак закрытого доступа вне
  реестра И вне перечня, равенство состава объявленному перечню, форма `snake_case`,
  знакомый макросу вариант, чистота функции кода, запрет импорта модулей-разделов,
  плюс четыре контроля.

## Task Commits

| Task | Gate | Name | Commit | Files |
|------|------|------|--------|-------|
| 1 | RED | Failing gates for the closed notice registry | `267a0bb` | `tests/test_pages/test_notices_registry.py` |
| 1 | GREEN | Implement the closed notice registry | `085c291` | `app/pages/notices.py` |
| 2 | — | Gate the registry boundaries and prove the gates' teeth | `a4e6325` | `tests/test_pages/test_notices_registry.py` |

## TDD Gate Compliance

| Gate | Commit | Статус |
|------|--------|--------|
| RED | `267a0bb` `test(08-02)` | Пройден — красный по построению (`ImportError`: модуль ещё не существовал) |
| GREEN | `085c291` `feat(08-02)` | Пройден — 8/8 зелёных |
| REFACTOR | — | Не потребовался: реализация минимальна, дублирования не возникло. Гейт необязателен. |

Последовательность `test(...)` → `feat(...)` соблюдена; нарушений нет.

## Verification Results

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_notices_registry.py -v` | 14 passed, exit 0 |
| `uv run pytest tests/test_pages/test_notices_registry.py -k control -v` | 4 selected, 4 passed, exit 0 (требовалось ≥3) |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| Регрессия сверх плана: `uv run pytest tests/test_pages -q` | 1221 passed, exit 0 (21:37) |
| `grep -c 'import app' tests/test_pages/test_notices_registry.py` | 0; единственный импорт приложения — `from app.pages import notices` |
| Пять снимаемых написаний в новых файлах | 0 вхождений (grep exit 1) |

## Success Criteria

- [x] Реестр уведомлений существует одним модулем и принимает КОД, а не текст
- [x] Дубль кода невозможен молча — сборка падает на импорте
- [x] `expired` в реестре отсутствует и объявлен отсутствующим машинно
- [x] Одиннадцать перенесённых текстов совпадают с источниками посимвольно, два новых
      названы новыми

## Deviations from Plan

### 1. [Rule 2 — Missing critical] Добавлен четвёртый контроль: пропажа перенесённой записи

- **Found during:** Task 2
- **Issue:** План называл три контроля. Отрицательные контроли покрывали ИЗМЕНЁННЫЙ
  текст, но не ПРОПАВШУЮ запись, а это второй способ потерять исход — и ровно тот, что
  прямо запрещён прохибицией FOUND-05 («MUST NOT потерять при консолидации ни одного
  исхода»). Гейт переноса, обходящий словарь копий, на снятой записи мог бы промолчать,
  и запрет остался бы недоказанным.
- **Fix:** `test_control_negative_a_missing_record_reddens_the_move_gate` — из реестра
  изымается `payment_pending`, и утверждается, что разборщик гейта переноса это видит.
  `_move_gate_failures` для этого явно различает «записи нет вовсе» и «текст разошёлся».
- **Files modified:** `tests/test_pages/test_notices_registry.py`
- **Verification:** контроль зелёный; группа `-k control` собирает 4 теста вместо 3
  (критерий требовал «не менее трёх»)
- **Commit:** `a4e6325`

### 2. [Организационное] Контроль дубля кода написан в задаче 1, а не в задаче 2

- **Found during:** Task 1
- **Issue:** План перечислял «тест 5: дубль поднимает `ValueError`» в поведении задачи 1
  и `test_control_negative_a_duplicate_code_reddens_the_builder` в группе контроля
  задачи 2 — это одно и то же утверждение, записанное дважды.
- **Fix:** утверждение написано один раз, сразу под именем из группы контроля. Задача 2
  дописала оставшиеся контроли. Дубля тестов в файле нет.
- **Files modified:** `tests/test_pages/test_notices_registry.py`
- **Commit:** `267a0bb` (RED), сохранено в `a4e6325`

**Total deviations:** 2 (1 auto-added по Rule 2, 1 организационная). **Impact:** объём и
границы плана не изменились; покрытие прохибиции FOUND-05 стало доказанным, а не
заявленным.

## Known Stubs

Отсутствуют. Реестр полон на все четырнадцать записей, ни одна не заглушена.

Отдельно названо и НЕ является заглушкой: `profile_saved` сегодня не имеет ни
записывающего обработчика, ни места отрисовки. Это состояние ОЖИДАЕМО и записано планом:
обработчики переводит план 08-06, область отрисовки заводит план 08-04. Реестр в этой
фазе — контракт, а не его потребление.

## Threat Flags

Новой поверхности за пределами `<threat_model>` плана не появилось. Модуль не открывает
ни сетевого входа, ни доступа к файлам, ни изменения схемы; все четырнадцать текстов —
постоянные литералы без подстановок (T-08-11), значение параметра в разметку не уходит
ни одним путём (T-08-08), молчаливая перезапись дублем закрыта сборщиком (T-08-10).
Пакетов не устанавливалось (T-08-SC).

## Issues Encountered

None.

## Authentication Gates

None.

## Next Phase Readiness

Готово для соседей волны и следующих планов фазы:

- план 08-01 может звать `respond(notice=...)` с кодом из констант модуля;
- план 08-04 может вешать `notice_for` Jinja-глобалью на области `#notice` /
  `#notice-alert`;
- план 08-06 может переписывать обработчики на коды и снимать пять частных написаний —
  тексты уже переехали, и гейт переноса переживёт снятие источников.

## Self-Check: PASSED

- `app/pages/notices.py` — существует на диске
- `tests/test_pages/test_notices_registry.py` — существует на диске
- Коммиты `267a0bb`, `085c291`, `a4e6325` — найдены в `git log`
- Все `<acceptance_criteria>` обеих задач перепроверены после завершения работ; все
  команды `<verification>` плана перезапущены и зелёные
