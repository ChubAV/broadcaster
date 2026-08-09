---
phase: 01-interfeysnyy-fundament
plan: 10
subsystem: ui
tags: [xss, jinja2, dom, uploads, s3, security, fastapi, pytest]

# Dependency graph
requires:
  - phase: 01-interfeysnyy-fundament
    provides: "План 03 — перенос ads/form.html на макросы дизайн-системы; План 08 — реестр отложенных дефектов и решение по CSP"
provides:
  - "safe_filename() в app/routes/uploads.py — нормализация клиентского имени файла перед сборкой ключа объекта"
  - "renderImages() в app/templates/ads/form.html собирает предпросмотр узлами DOM с присваиванием свойств"
  - "tests/test_templates/test_ads_form_security.py — проверки исходника шаблона на закрытый сток разметки"
affects: [ads-editor, uploads, phase-2-ads, security-review]

actuals:
  tokens: 5553
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Проверка ИСХОДНИКА шаблона как способ закрепить свойство способа сборки, когда HTTP-покрытие недоступно"
    - "Чистая функция нормализации на уровне модуля вместо встроенного выражения в обработчике — тестируется напрямую, без HTTP"

key-files:
  created:
    - tests/test_templates/test_ads_form_security.py
  modified:
    - app/routes/uploads.py
    - app/templates/ads/form.html
    - tests/test_routes/test_uploads.py

key-decisions:
  - "Ключ объекта строится по прежнему шаблону user_id/hex_name — меняется только нормализация имени, ни один сохранённый ключ не переименован"
  - "Обрезка длины идёт ПОСЛЕ замены недопустимых символов: усечение до замены могло бы оставить половину заменяемой последовательности"
  - "Закрытие стока проверяется на уровне исходника шаблона, а не через HTTP — страница 500-ит в тестовой среде (WR-06, отложено в Фазу 2 / ADS-07)"
  - "REQUIREMENTS.md намеренно не тронут: UI-02 и UI-04 — требования уровня фазы, их закрывает оркестратор после волны, а не отдельный gap-closure план в worktree"

patterns-established:
  - "Никакого значения из ненадёжного источника в строке разметки: узел создаётся, свойства присваиваются"
  - "Обработчики на созданных узлах навешиваются addEventListener, а не атрибутом события в собранной строке"

requirements-completed: [UI-02, UI-04]

coverage:
  - id: D1
    description: "Ключ объекта хранилища не может выйти за префикс пользователя ни при каком имени файла"
    requirement: "UI-02"
    verification:
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_safe_filename_strips_path_components"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_safe_filename_drops_quotes_and_spaces"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_safe_filename_falls_back_on_empty"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_safe_filename_truncates"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_safe_filename_keeps_plain_name"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_key_stays_inside_user_prefix"
        status: pass
    human_judgment: false
  - id: D2
    description: "Значение из ненадёжного источника не попадает в строку разметки ни в одном месте формы объявления"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_ads_form_security.py#test_ads_form_builds_dom_not_markup"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_ads_form_security.py#test_ads_form_uses_property_assignment"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_ads_form_security.py#test_ads_form_has_no_template_literal_markup"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_ads_form_security.py#test_ads_form_remove_handler_is_listener"
        status: pass
    human_judgment: false
  - id: D3
    description: "Контракт формы сохранён: имя поля images, тип hidden, ограничение в 10 изображений, порядок набора"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_ads_form_security.py#test_ads_form_hidden_input_contract_kept"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py (60 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Живое поведение редактора: миниатюра появляется при загрузке файла с враждебным именем, кнопка «Убрать» работает, ранее загруженные изображения продолжают отображаться при открытии объявления на редактирование"
    verification: []
    human_judgment: true
    rationale: "app/templates/ads/form.html не имеет HTTP-покрытия: страница отдаёт 500 в тестовой среде из-за шаблонных глобалов адреса хранилища, собирающих настройки в обход подмены зависимостей (WR-06, отложено в Фазу 2 / ADS-07). Рендеринг страницы и работа предпросмотра в браузере проверяются вручную. Отдельно требует человека проверка непрерывности доступа к ранее сохранённым ключам — автоматика подтверждает лишь то, что формат ключа не менялся и переименования нет."

# Metrics
duration: 24min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 10: Закрытие CR-01 — хранимый XSS через имя загружаемого файла

**Предпросмотр изображений в редакторе объявления собирается узлами DOM с присваиванием свойств, а клиентское имя файла нормализуется `safe_filename()` перед сборкой ключа объекта — обе половины CR-01 закрыты и закреплены одиннадцатью тестами.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-08-09T16:59:30Z
- **Completed:** 2026-08-09T17:23:20Z
- **Tasks:** 2 (обе TDD)
- **Files modified:** 4 (3 изменено, 1 создан)

## Accomplishments

- **Сток разметки в `ads/form.html` закрыт полностью.** `renderImages()` больше не конкатенирует строку: контейнеры очищаются `replaceChildren()`, каждый элемент набора создаётся `createElement()`, а значения уходят в свойства узлов — `img.src`, `hidden.value`, `label.textContent`. `innerHTML`, `outerHTML`, `insertAdjacentHTML` и `document.write` в файле отсутствуют (`grep -c` == 0 по всем четырём).
- **Второй сток того же класса закрыт вместе с первым.** Обработчик удаления навешивается `addEventListener` с замыканием на индекс — атрибут `onclick`, собранный в строку, из блока скрипта ушёл.
- **Обход через путь в имени файла закрыт на сервере.** `safe_filename()` отбрасывает все сегменты пути (и `/`, и `\`), заменяет всё вне набора `[A-Za-z0-9._-]` на подчёркивание, обрезает до 100 символов и возвращает `"upload"`, если после нормализации ничего не осталось. Без этого исправление в шаблоне оставило бы запись объекта за пределы префикса пользователя.
- **Уже сохранённые ключи не тронуты.** Формат остался прежним — `{user_id}/{hex}_{name}`; изменилась только нормализация вновь создаваемого имени. Миграции нет, переименования нет.
- **Полная суита зелёная:** 583 passed, 0 failed (было 578 до Задачи 2 и 578 после Задачи 1 при базовой линии в этом окружении).

## Task Commits

1. **Задача 1: Санитайзинг клиентского имени файла в ключе объекта** — `07cec21` (test, RED) → `55ab4e7` (fix, GREEN)
2. **Задача 2: Предпросмотр собирается узлами DOM** — `4f6f46e` (test, RED) → `897f426` (fix, GREEN)

Фаза REFACTOR не потребовалась ни в одной задаче: обе реализации сразу вышли в целевой форме, а лишняя перестановка кода после зелёного только увеличила бы диф без изменения поведения.

## Files Created/Modified

- `app/routes/uploads.py` — добавлена чистая функция `safe_filename(filename: str | None) -> str` на уровне модуля плюс константы `MAX_FILENAME_LENGTH = 100` и `FALLBACK_FILENAME = "upload"`; обработчик подставляет её результат в имя. Проверки типа содержимого и размера остались на месте и в прежнем порядке.
- `app/templates/ads/form.html` — `renderImages()` переписана на сборку узлами; комментарий-заголовок блока скрипта переписан (он требовал «сохранить существующий JavaScript» — после этой правки требование обратное и объяснено).
- `tests/test_routes/test_uploads.py` — шесть новых тестов: пять прямых по классам входов `safe_filename` и один поведенческий по маршруту.
- `tests/test_templates/test_ads_form_security.py` — новый файл, пять проверок исходника шаблона в стиле `test_components.py`.

## Итоговые контракты

**Сигнатура и поведение нормализации:**

```python
def safe_filename(filename: str | None) -> str
```

Порядок: последний сегмент пути → замена символов вне `[A-Za-z0-9._-]` на `_` → обрезка до 100 → `"upload"`, если пусто. Обрезка ПОСЛЕ замены — намеренно.

**Шаблон ключа объекта (не изменился):** `{user_id}/{uuid4().hex}_{safe_filename(file.filename)}`, что соответствует `^\d+/[0-9a-f]{32}_[A-Za-z0-9._-]+$`.

**Свойства, которые теперь присваиваются вместо конкатенации:** `img.src`, `img.alt`, `img.className`, `label.textContent`, `label.className`, `btn.type`, `btn.className`, `wrap.className`, `hidden.type`, `hidden.name`, `hidden.value`.

**Подтверждение сохранности данных:** ни один существующий ключ не переименован и не перезаписан; правка действует исключительно на вновь загружаемое. Классы дизайн-системы (`cell`, `avatar`, `btn btn--ghost`, `btn__label`), имя поля `images`, ограничение в 10 изображений, адрес загрузки, базовый адрес хранилища и порядок элементов набора сохранены дословно.

## Decisions Made

- **`safe_filename` вынесена на уровень модуля, а не встроена в обработчик.** У неё определённые вход и выход, поэтому она проверяется напрямую по пяти классам входов без поднятия HTTP — а обработчик остаётся проверенным одним поведенческим тестом.
- **Разделители пути отбрасываются и для `/`, и для `\`.** Обратный слеш и так не входит в допустимый набор и стал бы подчёркиванием, но отбрасывание сегмента целиком точнее выражает намерение: имя `..\..\evil.png` даёт `evil.png`, а не `.._.._evil.png`.
- **Проверка закрытия стока — на уровне исходника.** Уязвимость здесь есть свойство СПОСОБА СБОРКИ, а не конкретного значения, поэтому отсутствие строковой сборки в файле и есть проверяемое утверждение. Подменять шаблонные глобалы в фикстуре тестового клиента план запретил — это та же архитектурная развилка ADS-07, только со стороны тестов.
- **REQUIREMENTS.md не изменялся.** UI-02 и UI-04 — требования уровня фазы, закрываемые совокупностью планов; отметка из отдельного worktree в параллельной волне конфликтовала бы с соседними агентами. Поле `requirements-completed` в этом SUMMARY заполнено — отметку в общем файле делает оркестратор после волны.

## Deviations from Plan

Ни одного отклонения — план исполнен дословно. Правил 1-4 применять не потребовалось: диагноз CR-01 в `01-REVIEW.md` описывал оба стока верно, а предложенный там код сборки узлов совпал с тем, что понадобилось.

**Total deviations:** 0
**Impact on plan:** нет.

## Issues Encountered

- **`httpx` кодирует двойную кавычку в имени файла как `%22`.** Проверено до написания поведенческого теста: сервер получает `../../evil x%22 onerror=%22alert(1)>.png`. Вектор от этого не ослабевает — сегменты пути, пробел, `%`, `>`, скобки в имени остаются, и регулярное выражение ключа их ловит. Прямая проверка кавычки закреплена отдельно, на уровне `safe_filename`, где кодирование транспорта ни при чём.
- **Базовая линия суиты в этом окружении — 578 passed, 0 failed, а не «545 passed + 25 средовых падений».** `SMTP_HOST` в окружении worktree не выставлен, поэтому семь модулей, о которых предупреждает `01-VERIFICATION.md`, проходят и без явного `SMTP_HOST=""`. Все команды проверки всё равно выполнялись с пустым `SMTP_HOST` — так, как записано в плане.

## Observations for Phase 2

Записаны здесь, а не в общий `deferred-items.md`: файл разделяемый, и дозапись из worktree в параллельной волне конфликтовала бы с соседними агентами. Перенос в реестр — за оркестратором.

- **Ограничение в 10 изображений остаётся клиентским** (T-10-05, disposition `accept`). Серверной проверки числа изображений в объявлении нет ни до правки, ни после; усиление — новое поведение, вне границы «новый вид, старые действия».
- **`app/templates/ads/form.html` по-прежнему без HTTP-покрытия** (WR-06 / ADS-07). Это самый большой блок JS в фазе; ничто не заметит, если страница начнёт 500-ить в продакшене.
- **`graphify update .` не выполнялся:** `graphify-out/` в `.gitignore` и в worktree отсутствует. Обновление графа — за оркестратором после слияния, иначе параллельные агенты гонялись бы за один и тот же генерируемый артефакт.

## User Setup Required

Нет — внешняя конфигурация не требуется.

## Next Phase Readiness

- CR-01 закрыт целиком, обе половины закреплены тестами; блокирующая находка severity `high` при пороге `security_block_on: high` снята.
- Открытым остаётся ручной прогон D4: `/ads/new`, загрузка файла с враждебным именем, удаление миниатюры, открытие сохранённого объявления с ранее загруженными изображениями. При `human_verify_mode: end-of-phase` он относится к сквозной проверке фазы.
- Фаза 2 (редактор объявления, ADS-07) получает форму, в которой сборка предпросмотра уже безопасна — переписывать её под черновики можно, не таща за собой прежний сток.

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
