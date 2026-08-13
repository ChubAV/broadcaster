---
phase: 03-gruppy-akkaunta
plan: 09
subsystem: api
tags: [fastapi, sqlalchemy, concurrency, dos, telegram, whatsapp, max]

# Dependency graph
requires:
  - phase: 03-gruppy-akkaunta
    provides: обработчик `accounts_sync_groups` с guard по `account.status`, хелперы `apply_group_resync` / `record_sync_failure`, ограничение `uq_groups_account_external` (ревизия 0015) и ветка `IntegrityError`
provides:
  - Внутрипроцессный реестр `_SYNC_IN_FLIGHT` и хелперы `_claim_sync_slot` / `_release_sync_slot` в `app/pages/accounts.py`
  - Обрамление тела `accounts_sync_groups` внешним `try` с `finally: _release_sync_slot(account_id)` — освобождение на всех четырёх выходах
  - Семь тестов в `tests/test_routes/test_sync_groups.py`: параллельный запуск, независимость аккаунтов, запрет записи `syncing`, четыре точки освобождения
  - Закрытие T-03-15 / T-03-28 и регистрация остаточного риска T-03-36 в `03-SECURITY.md`
affects: [03-12 (раздел Unregistered Findings того же регистра), будущие фазы, трогающие синхронизацию групп или диспетчеризацию отправок]

actuals:
  tokens: 13091
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Заявка на дорогую внешнюю операцию — внутрипроцессный set по идентификатору, а не колонка состояния в БД"
    - "Освобождение заявки в `finally` операцией, которая не может отказать (никаких обращений к БД)"

key-files:
  created: []
  modified:
    - app/pages/accounts.py
    - tests/test_routes/test_sync_groups.py
    - .planning/phases/03-gruppy-akkaunta/03-SECURITY.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Заявка на синхронизацию живёт в памяти процесса, а не в `MessengerAccount.status`: запись статуса потеряла бы подошедшую отправку в двух местах диспетчеризации — молча на use_cases.py:98 и видимо на :280"
  - "Существующий guard по `account.status` сохранён первым по порядку: он закрывает другой случай (страничный запуск поверх фоновой задачи WA/MAX), а заявка — усиление поверх него"
  - "Граница контроля названа явно и зарегистрирована как T-03-36 двумя различёнными направлениями; асимметрия «страничный синк ↔ фоновый синк» записана как РЕАЛЬНАЯ уже сегодня, а не как условие на будущее"

patterns-established:
  - "Мутационная проверка непустоты тестов: перед фиксацией свойства временно ломается реализация, и тесты обязаны покраснеть"
  - "Комментарий, различающий два места с одинаковым условием и РАЗНЫМ поведением, вместо одного описания на оба"

requirements-completed: [GRP-07]

coverage:
  - id: D1
    description: "Второй POST синхронизации, пришедший пока первый внутри мессенджера, до мессенджера не доходит: конструктор адаптера вызывается ровно один раз за цикл"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_second_sync_during_a_running_sync_does_not_reach_the_messenger"
        status: pass
    human_judgment: false
  - id: D2
    description: "Заявка освобождается на каждом из четырёх выходов обработчика: успех, MessengerFetchError, широкий отказ, конфликт уникальности"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_slot_is_released_after_a_successful_sync"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_slot_is_released_after_a_fetch_error"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_slot_is_released_after_an_unexpected_error"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_slot_is_released_after_an_integrity_conflict"
        status: pass
    human_judgment: false
  - id: D3
    description: "Занятая заявка одного аккаунта не мешает синхронизировать другой аккаунт того же пользователя"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_slot_is_per_account"
        status: pass
    human_judgment: false
  - id: D4
    description: "Страничный путь синка не пишет `syncing` в статус аккаунта — диспетчеризация отправок ничего не теряет"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_does_not_persist_syncing_for_the_page_path"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_sync_groups.py#test_sync_while_syncing_does_not_touch_messenger"
        status: pass
    human_judgment: false
  - id: D5
    description: "Регистр угроз описывает реализованный контроль: T-03-15/T-03-28 закрыты с границей синхронного HTTP-пути, остаточный риск зарегистрирован как T-03-36"
    verification: []
    human_judgment: true
    rationale: "Соответствие текста регистра реализованному контролю — суждение аудитора: греп подтверждает наличие подстрок, но не то, что формулировка не переоценивает контроль"

# Metrics
duration: 21min
completed: 2026-08-13
status: complete
---

# Phase 03 Plan 09: Внутрипроцессная заявка на синхронизацию групп Summary

**Guard повторного запуска синхронизации распространён на синхронный HTTP-путь: два одновременных POST-а доходят до мессенджера ровно одним запросом, заявка живёт в памяти процесса и освобождается в `finally` на всех четырёх выходах обработчика.**

## Performance

- **Duration:** 21 min
- **Started:** 2026-08-13T13:46:35Z
- **Completed:** 2026-08-13T14:07:33Z
- **Tasks:** 3
- **Files modified:** 4 (2 кода, 2 планировочных)

## Accomplishments

- Объявленная гарантия «второй запрос не доходит до мессенджера» теперь держится для ВСЕХ трёх синхронных веток обработчика (`tg_user`, `wa`, `max`), а не только для фоновых путей. До правки собственный комментарий обработчика признавал: два одновременных POST-а оба читают `active`, оба проходят guard и оба идут в мессенджер.
- Заявка занимается ПОСЛЕ проверки владения и существующего guard по `account.status`, до конструирования адаптера, и освобождается в `finally`, накрывающем успешный возврат, узкий `except MessengerFetchError`, широкий `except Exception` и ветку `IntegrityError`.
- Диспетчеризация отправок не задета: страничный синк не пишет `syncing` в статус аккаунта, что закреплено негативным тестом с двумя чтениями (внутри запроса и после него).
- Регистр угроз приведён в соответствие с кодом: T-03-15 и T-03-28 закрыты с явной границей синхронного HTTP-пути и перечислением закрепляющих тестов; остаточный риск заведён отдельной строкой T-03-36 двумя различёнными направлениями.

## Task Commits

Each task was committed atomically:

1. **Task 1: Внутрипроцессная заявка и её проверка параллельным запросом** — `0180686` (test, RED) → `02871ee` (feat, GREEN)
2. **Task 2: Освобождение заявки на каждом из четырёх выходов** — `f333263` (test)
3. **Task 3: Регистр угроз описывает реализованный контроль** — `76e1b43` (docs)

_Note: TDD-задачи дают несколько коммитов (test → feat)._

## Files Created/Modified

- `app/pages/accounts.py` — реестр `_SYNC_IN_FLIGHT`, синхронные хелперы `_claim_sync_slot` / `_release_sync_slot`, внешний `try/finally` вокруг тела `accounts_sync_groups`, переписанный комментарий-обоснование
- `tests/test_routes/test_sync_groups.py` — семь новых тестов (было 12, стало 19)
- `.planning/phases/03-gruppy-akkaunta/03-SECURITY.md` — T-03-15/T-03-28 в `closed`, новая строка T-03-36, замещённый раздел Open Threats, новая строка Security Audit Trail
- `.planning/REQUIREMENTS.md` — GRP-07 отмечено выполненным (чекбокс и строка трассируемости)

## Decisions Made

- **Форма заявки задана планом и исполнителем не менялась:** внутрипроцессный реестр вместо записи `status = "syncing"`. Обоснование перенесено в исходный код: запись статуса потеряла бы отправку, подошедшую в окно синхронизации, в двух местах диспетчеризации — на `app/application/scheduling/use_cases.py:98` МОЛЧА (пересчёт `next_run_at` вперёд и `continue`, слот исчезает без следа) и на `:280` ВИДИМО (строка `SendLog` со `status="account_disconnected"`). Оба фрагмента прочитаны перед записью комментария; пересчёт `next_run_at` приписан только первому.
- **Непустота тестов освобождения проверена мутацией.** Все четыре теста задачи 2 прошли сразу после реализации задачи 1 — плановый исход, но зелёный тест, который никогда не краснел, ничего не доказывает. Тело `finally` было временно заменено на `pass`: все четыре покраснели, после чего мутация снята и `accounts.py` побайтово вернулся к зафиксированному состоянию (`git diff --stat` подтвердил). В коммит мутация не попала.
- **Ссылки на файлы раскладки в комментарии и в регистре сверены с файлами, а не взяты из плана:** `Dockerfile:30`, `docker-compose.yml:25`/`:26`/`:61-62`, `docker-compose.prod.yml:78`/`:79`, `justfile:11`, `app/worker/tasks.py:300`/`:331` — все подтверждены гроном перед записью.
- **Ветка `IntegrityError` в тесте вызывается подменой `apply_group_resync`** (первый вызов кладёт строку, нарушающую `uq_groups_account_external`; последующие делегируют настоящей реализации). Способ был оставлен плантом на усмотрение исполнителя; факт прохождения ветки закреплён утверждением о сводке «Синхронизация уже выполнялась — откройте экран заново».

## Deviations from Plan

None — plan executed exactly as written.

Отдельно отмечено, поскольку это предусмотренная планом развилка, а не отклонение: задача 2 не потребовала правок `app/pages/accounts.py` — обрамление задачи 1 уже накрывало все четыре выхода. План называл этот исход штатным («тесты закрепляют свойство, а не добавляют его»), поэтому задача 2 состоит только из тестов.

## Issues Encountered

- **Два теста задачи 1 из трёх зеленели до реализации.** `test_sync_does_not_persist_syncing_for_the_page_path` и `test_sync_slot_is_per_account` — негативные тесты прохибиций: они защищают от НЕПРАВИЛЬНОЙ реализации (запись статуса в БД, глобальный флаг вместо реестра), а не двигают новое поведение. RED-гейт закрыт третьим тестом, `test_second_sync_during_a_running_sync_does_not_reach_the_messenger`, покрасневшим ровно предсказанной формой: `call_count == 2` вместо `1`.
- **Полная суита идёт 13 мин 48 с** — дольше одного окна выполнения команды; прогон выполнен фоново. Результат: 1090 passed, 0 failed.

## Known Stubs

None — заглушек не оставлено.

## Threat Flags

None — новой поверхности сверх зарегистрированной в `<threat_model>` плана не появилось. Остаточный риск оформлен штатной строкой регистра T-03-36, а не флагом.

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- `03-SECURITY.md` открытых угроз выше порога `block_on: high` не содержит: T-03-36 имеет severity `medium`, `threats_open: 0` сохранено без правки.
- Раздел «Unregistered Findings» регистра намеренно не тронут — его закрывает план 03-12 следующей волной.
- `graphify update .` этим планом НЕ выполнялся по прямому указанию плана: планы 03-09, 03-10 и 03-11 идут одной волной, а перестроение пишет в общий каталог `graphify-out/`. Перестроение выполняет задача 3 плана 03-12.
- Остаточный риск T-03-36 направления (б) — фоновый повтор синка, не видимый внутрипроцессной заявкой — остаётся открытым сознательно; кросс-процессным запасом служит `uq_groups_account_external` плюс ветка `IntegrityError`.

## Self-Check: PASSED

- `app/pages/accounts.py`, `tests/test_routes/test_sync_groups.py`, `.planning/phases/03-gruppy-akkaunta/03-SECURITY.md`, `.planning/REQUIREMENTS.md` — присутствуют, изменения зафиксированы.
- Коммиты `0180686`, `02871ee`, `f333263`, `76e1b43` найдены в истории ветки; рабочее дерево чистое.
- `uv run pytest tests/ -q` — **1090 passed**, 0 failed (13 мин 48 с).
- Критерии приёмки всех трёх задач проверены гропом: `_SYNC_IN_FLIGHT` / `_claim_sync_slot` / `_release_sync_slot` — по 2+ вхождения; `finally` со следующим оператором `_release_sync_slot`; существующий guard `account.status == "syncing"` на месте; комментарий содержит `use_cases.py:98`, `use_cases.py:280`, `tasks.py:300`, `T-03-36`; в регистре `T-03-36` — 4 вхождения, `R-03-0` — 8 (журнал принятых рисков не тронут), `threats_open: 0` сохранено, в Security Audit Trail две строки прогонов.

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-13*
