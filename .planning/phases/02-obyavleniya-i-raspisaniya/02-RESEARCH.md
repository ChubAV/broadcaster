# Phase 2: Объявления и расписания — Research

**Researched:** 2026-08-10
**Domain:** Server-rendered FastAPI + Jinja2 + HTMX редактор объявления, миграция схемы `Ad`, перенос CRUD расписаний, read-mostly сводный список
**Confidence:** HIGH (кодовая база), MEDIUM (внешние лимиты Telegram)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Черновик и статус объявления**

- **D-01:** Черновик не отправляется. Планировщик пропускает расписания объявлений в статусе черновика — статус имеет реальный эффект, а не только визуальный. Затрагивает запрос выбора наступивших расписаний в `app/worker/tasks.py`. — **Reversibility:** costly — условие уходит в боевой пайплайн отправки, откат означает повторную проверку всех тестов диспетчеризации.
- **D-02:** Вводится `Ad.status` (черновик / опубликовано), существующие записи мигрируют в «опубликовано». Поле `Ad.is_active` **удаляется** из модели, формы и миграции — сегодня оно переключается в форме и не проверяется нигде в коде отправки, то есть является мёртвым флагом. Одно состояние — одно поле. — **Reversibility:** one-way — требует миграции схемы (add `status`, drop `is_active`); откат — обратная миграция с восстановлением значений.
- **D-03:** `/ads/new` открывает пустой редактор и **не создаёт запись**. Первое автосохранение создаёт объявление в статусе черновика и подменяет URL на `/ads/{id}/edit`. Пустых записей от случайного захода в раздел не появляется.
- **D-04:** Публикация — это кнопка «Сохранить» из макета. Отдельной кнопки «Опубликовать» нет: макет содержит только «Сохранить» и «Отмена».

**Автосохранение**

- **D-05:** Автосохранение по паузе ввода ~1.5–3 с, штатным HTMX-триггером (`hx-trigger="keyup changed delay:..."`), без собственного JS-таймера и без обработчика ухода со страницы. Продолжает линию Фазы 1: вендоренный htmx 1.9.10, своего JS минимум.
- **D-06:** Ответ автосохранения возвращает обновлённый блок предпросмотра — один запрос закрывает и сохранение, и обновление превью.

**Модель сохранения расписаний в редакторе**

- **D-07:** Каждое расписание сохраняется **сразу и отдельно**, своим HTMX-запросом. Клиентского состояния, которое можно потерять при обрыве связи, нет. Это сознательное отступление от текста макета («сначала создастся объявление, затем привяжутся расписания») — оно возможно потому, что по D-03 объявление к моменту настройки расписаний уже существует как черновик.
- **D-08:** Неполное расписание **сохраняется, но выключенным** (`is_active=false`). Включение тумблера доступно только когда заполнены аккаунт, хотя бы одна группа, хотя бы один день и хотя бы одно время. Макетный бейдж «ЧЕРНОВИК» на карточке расписания и подсказка «Заполните группы, дни и время» означают именно это состояние — незаполненность, а не несохранённость.
- **D-09:** Базовый путь редактора работает **без JS**: сохранение объявления и удаление расписания выполняются обычной формой POST. Автосохранение, живое превью и сворачивание карточек — прогрессивное улучшение поверх работающей формы. Продолжает правило Фазы 1 и даёт тестам проверяемый серверный маршрут.

**Предпросмотр**

- **D-10:** Предпросмотр рендерится **на сервере** и приходит ответом автосохранения (см. D-06). Превью показывает то, что реально лежит в БД, то есть то, что уйдёт в группы. Отставание на паузу автосохранения принято.
- **D-11:** Один вид предпросмотра для всех каналов. Подпись канала показывает, куда уйдёт объявление (по настроенным расписаниям), но визуал единый — все три адаптера (`telegram_user`, `whatsapp`, `max`) принимают один и тот же `text` + `images`. Переключателя каналов с разными рамками нет.

**Вложения**

- **D-12:** Удаление вложения убирает ключ только из `Ad.images`; объект в S3 **остаётся**. Причина: `SendLog` хранит снапшоты отправленного контента, и удаление объекта из хранилища оставило бы историю с битыми картинками. Сироты в хранилище — принятая цена.
- **D-13:** Лимит вложений переносится **на сервер**: сервер отклоняет сохранение объявления с числом вложений сверх лимита. Браузерная проверка остаётся удобством, а не единственной защитой. Ложится в один ряд с CR-01/CR-02/WR-01 — клиентским данным в этой фазе перестают верить.

**Переезд создания расписаний**

- **D-14:** Страницы `/schedules/new` и `/schedules/{id}/edit` и шаблон `app/templates/schedules/form.html` **удаляются целиком**. Один способ настроить расписание, мёртвого кода не остаётся.
- **D-15:** JSON-API `app/routes/schedules.py` (POST / PUT / DELETE / toggle) **остаётся как есть** по составу маршрутов и контракту — фаза меняет страничный слой. Единственная правка API — закрытие дыры владения из D-18.
- **D-16:** Порядок выката задаётся порядком планов: сначала отдельный план доводит расписания в редакторе объявления до рабочего состояния, и только следующий план удаляет `/schedules/new` и `/schedules/{id}/edit`. Между ними оба пути живы — критерий 3 фазы («ни в один момент выката пользователь не остаётся без возможности создать расписание») выполняется структурой планов, а не обещанием. — **Reversibility:** reversible.

**Сводный список расписаний**

- **D-17:** Из макета берутся карточки, поиск по объявлению и фильтры-чипсы; **прогресс-бар отправок не делается** — в макете он показывает выдуманный процент, которому нет источника в данных. Макрос сворачиваемых фильтров существует с Фазы 1 (`01-04-PLAN.md`) и переиспользуется.
- **D-18:** Действия в списке: тумблер включения/паузы на месте плюс переход в редактор объявления к этому расписанию. Удаление расписания живёт **только** в редакторе — так требует ADS-08 и так устроен макет.

**Долги Фазы 1**

- **D-19:** CR-01, CR-02 и WR-01 закрываются **отдельным первым планом** фазы, до того как начнётся переделка редактора. Гейт код-ревью закрывается рано, фиксы ложатся на стабильный код, а не на движущуюся цель.
- **D-20:** Фикс CR-01 покрывает **оба слоя**. Проверено по коду: страничный слой (`app/pages/schedules.py:204-213,314-315`) не проверяет ни `ad_id`, ни `account_id`; JSON-API (`app/routes/schedules.py:67-73`) проверяет владение объявлением через `AdRepository.get_by_id_and_user`, но **не проверяет владение `account_id`** — чужой аккаунт проходит и там. Проверка владения обоими идентификаторами вводится на обоих входах.
- **D-21:** Глобал `s3_public_url` в `app/pages/common.py:38` собирает `Settings()` в обход подмены зависимостей, из-за чего `/ads/new` и `/ads/{id}/edit` не рендерятся ни одним тестом суиты. Чинится **до переделки редактора**, отдельной задачей, вместе с первым рендер-тестом редактора — иначе вся фаза строится на непокрытом тестами экране. Дефект существует на базовом коммите и не внесён Фазой 1.

### Claude's Discretion

- **Расписания черновиков в сводном списке.** Вопрос поднят, но не разобран: черновик не отправляется (D-01), значит его расписания в списке никогда не сработают. Разумный дефолт — показывать их с явной пометкой, что объявление в черновике и отправки не идут; решение за планировщиком, если исследование не покажет иного.
- **Лимиты тарифа и черновики.** Считать ли черновик в лимит объявлений по тарифу — не решено. Дефолт: считать так же, как сейчас считаются объявления, новой оси биллинга не вводить (это Фаза 5).
- Индикатор состояния автосохранения («сохранено» / «сохраняем»), точное значение задержки в пределах 1.5–3 с, раскладка редактора и предпросмотра на мобильных ширинах (брейкпоинт редактора 900px из макета), порядок вложений и необходимость drag-n-drop, состав фильтров сводного списка, таймзона расписания (берётся из профиля пользователя как сейчас, в карточке расписания не выбирается), поведение выбранных групп при смене аккаунта в расписании, потолок числа расписаний на одно объявление.

### Deferred Ideas (OUT OF SCOPE)

- **Фоновая уборка файлов-сирот в S3** — удалённые вложения остаются в хранилище (D-12). Отдельная задача с учётом снапшотов `SendLog`; в v2.0 не входит.
- **Прогресс-бар отправок в карточке расписания** — визуал есть в макете, источника данных нет (D-17). Возвращаться к нему имеет смысл после Фазы 4, где появляются агрегации по `SendLog`.
- **Переключатель канала в предпросмотре** с разными рамками Telegram / WhatsApp / MAX — отклонено в этой фазе (D-11), требует знания реальных ограничений каждого канала.
- **Число вложений как ось тарифа** — новая ось биллинга, относится к Фазе 5.
- **Экран групп аккаунта** (GRP-04…GRP-08) и удаление пункта «Группы» из навигации — Фаза 3.
- **Обновление HTMX до 2.x** — отложено с Фазы 1, отдельная задача после v2.0.

### UI-SPEC (02-UI-SPEC.md, status: approved) — тоже locked

`02-UI-SPEC.md` одобрен (`gsd-ui-checker`, 6/6 dimensions PASS). Его Design System, Spacing Scale, Typography, Color, Copywriting Contract, Component Inventory, Interaction Contract и Responsive Contract — **контракт того же уровня, что D-01…D-21**. Планировщик не пересматривает их; ниже они только дополняются кодовыми фактами. Две вещи UI-SPEC явно отдал планировщику:

1. Порог счётчика длины текста (UI Considerations assumption 1) — см. §Common Pitfalls, Pitfall 6 и §Open Questions Q1.
2. Раскладка 2…10 вложений в предпросмотре (assumption 2) — дефолт «переносящийся ряд миниатюр 120px в порядке отправки»; checker рекомендовал зафиксировать это на планировании, а не переоткрывать.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **ADS-04** | Пользователь может сохранить объявление как черновик, и содержимое черновика сохраняется автоматически во время редактирования. | §Standard Stack (миграция `0013`), §Architecture Patterns Pattern 1 (`Ad.status`), Pattern 2 (OOB-автосохранение), §Code Examples 1–3, §Common Pitfalls 1–5 |
| **ADS-05** | Пользователь может прикреплять к объявлению несколько вложений и удалять их. | §Architecture Patterns Pattern 4 (`Ad.images` + владение ключом), §Code Examples 4, §Security Domain V5/V12, §Common Pitfalls 7 |
| **ADS-06** | Пользователь может видеть предпросмотр объявления в том виде, в каком оно будет отправлено. | §Architecture Patterns Pattern 3 (серверное превью из БД), факт F7 (реального ограничения длины в адаптерах нет), §Open Questions Q1 |
| **ADS-07** | Пользователь может настраивать расписания объявления (группы, дни, время) прямо в редакторе объявления. | §Architecture Patterns Pattern 5 (расписание как самостоятельная под-форма), §Code Examples 5, §Common Pitfalls 8–10 |
| **ADS-08** | Пользователь может удалить расписание объявления из его редактора. | Существующий `POST /schedules/{id}/delete` (`app/pages/schedules.py:365-385`) переиспользуется; §Common Pitfalls 11 (redirect-контракт) |
| **SCH-04** | Пользователь видит сводный список всех своих расписаний с объявлением, каналами, группами, днями и временем. | §Architecture Patterns Pattern 6 (карточный список), факт F11/F17 (группы и member_count — источники данных), §Open Questions Q2 |
| **SCH-05** | Пользователь может включить или поставить на паузу расписание непосредственно из сводного списка. | `POST /schedules/{id}/toggle` уже существует (`app/pages/schedules.py:327-362`), переиспользуется без правки; §Common Pitfalls 12 (issue #35 resume_blocked) |

</phase_requirements>

## Summary

Фаза 2 — это **brownfield-переделка трёх живых экранов** (`/ads/new`, `/ads/{id}/edit`, `/schedules`) плюс единственное изменение схемы за весь milestone (`Ad.status`) плюс одно точечное вторжение в боевой пайплайн отправки (D-01). Кода писать надо немного; опасность здесь не в объёме, а в том, что почти каждое изменение имеет неочевидного второго читателя. Исследование нашло шесть таких читателей, о которых CONTEXT.md не знает, и все шесть роняют работающие экраны, если их пропустить.

Самая важная поправка к CONTEXT.md: **D-01 указывает не на тот файл**. Запрос наступивших расписаний живёт не в `app/worker/tasks.py`, а в `app/application/scheduling/use_cases.py:48-55` (`collect_due_schedules`); `tasks.py:146` только вызывает его. Правка ровно на одну строку `.join(Ad, ...)`/`.where(Ad.status != "draft")` в use-case, и она автоматически покрывается существующими тестами `tests/test_worker_tasks.py` и `tests/test_application/`. Вторая по важности поправка: **`Ad.is_active` читается в восьми местах, включая `app/pages/dashboard.py:33`**, которого нет ни в одном списке CONTEXT.md, и **входит в публичный контракт JSON-API** (`AdResponse.is_active`, `UpdateAdRequest.is_active`) — удаление поля из модели без правки Pydantic-схемы превращает каждый вызов `/api/ads` в 500.

Третья находка сдвигает первый план фазы: **суита не зелёная на базовом коммите — 25 failed + 3 errors из 652 собранных** (проверено прогоном, 12 мин). Причина одна и та же для всех 28: `Settings.model_config = {"env_file": ".env"}` (`app/config.py:77`), и десять тестовых модулей строят `Settings(...)` собственными фикстурами, не переопределяя все поля — локальный `.env` разработчика протекает в тесты (`smtp_host='smtp.timeweb.ru'` → регистрация отвечает `400 Email verification required`). Это тот же дефект, что D-21, только с другой стороны: **на машине с `.env` `/ads/new` рендерится (проверено, 200), а падают 28 тестов; на машине без `.env` `/ads/new` даёт 500, а те 28 зеленеют.** Зелёной суиты, которая при этом трогает редактор объявления, не существует ни в одной конфигурации. Один фикс (`Settings(_env_file=None, ...)` — проверено, изолирует полностью) закрывает обе половины и обязан идти в первом плане вместе с D-19/D-21, иначе фаза не сможет отличить свою регрессию от чужой.

**Primary recommendation:** первый план фазы = «привести базу в проверяемое состояние»: `_env_file=None` во всех тестовых фикстурах + инъекция `s3_public_url` через контекст шаблона вместо глобала + CR-01/CR-02/WR-01. Второй план = миграция `0013` вместе со **всеми восемью** читателями `is_active` за один коммит. Дальше — редактор (автосохранение через `hx-swap="none"` + `hx-swap-oob`, **не** `outerHTML` по форме), затем расписания в редакторе, затем удаление `/schedules/new`, затем сводный список.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Статус объявления (черновик/опубликовано) | Database / Storage | API / Backend | Новая колонка `ads.status` + миграция Alembic; читается страничным слоем, JSON-API и планировщиком отправки |
| Пропуск черновиков при отправке | API / Backend (domain use-case) | — | `collect_due_schedules` — доменная функция без побочных эффектов вне БД; это её ответственность, не Celery-задачи [VERIFIED: app/application/scheduling/use_cases.py:35-56] |
| Автосохранение (дебаунс, повтор, гонки) | Browser / Client (htmx-декларация) | API / Backend (идемпотентный POST) | Дебаунс — атрибут `hx-trigger`, отмена устаревших запросов — `hx-sync`; сервер обязан быть идемпотентным «последняя запись побеждает» |
| Рендер предпросмотра | Frontend Server (Jinja2) | — | D-10 фиксирует серверный рендер; клиент не собирает превью из полей формы |
| Индикатор состояния автосохранения | Browser / Client (CSS по `.htmx-request`) | — | htmx сам вешает класс на инициатора; таймеров и своего состояния нет (D-05) |
| Загрузка файла и построение ключа объекта | API / Backend | CDN / Static (S3) | `POST /api/uploads/image` уже нормализует имя (`safe_filename`); проверка типа обязана переехать на содержимое (CR-02) |
| Проверка владения ключом изображения | API / Backend | — | Ключ имеет вид `{user_id}/{32hex}_{name}` — сервер и только сервер может подтвердить префикс (WR-01) |
| Лимит числа вложений | API / Backend | Browser / Client (удобство) | D-13: клиентская проверка перестаёт быть точкой принуждения |
| CRUD расписания внутри редактора | Frontend Server (страничные POST) | API / Backend (JSON-API не трогаем, D-15) | Каждое расписание — своя форма/свой POST (D-07), базовый путь без JS (D-09) |
| Проверка владения `ad_id` + `account_id` | API / Backend | — | CR-01/D-20: оба входа (страничный и JSON) |
| Включение/пауза расписания из списка | Frontend Server (существующий POST + redirect) | Browser / Client (Alpine `$el.submit()`) | Маршрут не меняется (D-15/SCH-05); Alpine — только удобство, форма работает без него |
| Разрешение имён групп для карточки списка | Database / Storage (доп. запрос) | — | `Schedule.group_ids` — JSON-массив id, имён в нём нет |

## Standard Stack

### Core

Фаза **не добавляет ни одной зависимости**. Весь стек уже в `pyproject.toml` и вендорен в `app/static/js/`.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `>=0.129.0` | Страничные и JSON-маршруты | Зафиксирован в PROJECT.md §Constraints [VERIFIED: pyproject.toml:18] |
| SQLAlchemy (asyncio) | `>=2.0.46` | ORM, `Mapped[]`-модели | Все модели уже в стиле 2.0 `mapped_column` [VERIFIED: pyproject.toml:26, app/models/ad.py:12-22] |
| Alembic | `>=1.18.4` | Миграция `Ad.status` | Единственный механизм схемы в проекте, 12 ревизий [VERIFIED: pyproject.toml:12, alembic/versions/] |
| Jinja2 | `>=3.1.6` | Серверный рендер и макросы | UI-04/UI-06 закрыты макросами Фазы 1 [VERIFIED: pyproject.toml:20] |
| htmx (вендорен) | 1.9.10 | Автосохранение, точечные подмены | Phase 1 D-05; файл `app/static/js/htmx.min.js`, внешних запросов 0 [VERIFIED: app/templates/base.html:12] |
| Alpine (вендорен) | 3.13.3 | Сворачивание карточек, модалки, `$el.submit()` | Phase 1 D-05 [VERIFIED: app/templates/base.html:13] |
| pytest + pytest-asyncio + aiosqlite | `>=9.0.2` / `>=1.3.0` / `>=0.22.1` | Суита | 652 теста собираются [VERIFIED: pyproject.toml:33-38 + `pytest --collect-only`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | 12.1.1 (**транзитивная**, через `qrcode[pil]`) | Декодирование изображений | **Не использовать для фикса CR-02.** Не объявлена прямой зависимостью, а `Image.open()` на пользовательском файле добавляет вектор decompression bomb. См. §Don't Hand-Roll |
| `zoneinfo` (stdlib) | Python 3.12 | Таймзона расписания | Уже используется `compute_next_run_at` [VERIFIED: app/services/schedule_service.py:2] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `hx-swap="none"` + `hx-swap-oob` для автосохранения | `hx-target="#preview"` | `hx-target` в проекте не используется **нигде** — `tests/test_pages/test_htmx_preserved.py:22-23` прямо фиксирует «явной цели подмены в проекте нет нигде». OOB не вводит нового атрибута цели и позволяет одним ответом обновить превью + сводку + индикатор (D-06) [VERIFIED: tests/test_pages/test_htmx_preserved.py:22-23] |
| `hx-swap="none"` + OOB | `hx-swap="outerHTML"` на форме | Заменяет форму целиком → каретка и выделение теряются на каждом автосохранении. Неприемлемо для ADS-04 |
| Строковый `status` + CHECK | `sa.Enum` | `sa.Enum` на PostgreSQL создаёт тип БД, который придётся дропать в `downgrade`; в проекте статусы уже строковые (`MessengerAccount.status`, `SendLog.status`) [VERIFIED: app/models/schedule.py + app/application/scheduling/use_cases.py:68] |
| Магические байты вручную | `python-magic` / `filetype` | Новая зависимость ради четырёх сигнатур (JPEG/PNG/WebP/GIF из UI-SPEC §Error states). См. §Don't Hand-Roll |
| `Settings(_env_file=None, ...)` в фикстурах | `monkeypatch` `.env` пути | `_env_file=None` — штатный параметр pydantic-settings, работает точечно и не зависит от порядка тестов [VERIFIED: проверено в этой сессии, см. §Common Pitfalls 0] |

**Installation:**

```bash
# Ничего устанавливать не нужно — новых пакетов фаза не вводит.
just sync   # uv sync, если окружение не собрано
```

**Version verification:** новые пакеты не рекомендуются, поэтому проверка версий на PyPI не выполнялась. Версии выше прочитаны из `pyproject.toml` и подтверждены импортом в рабочем окружении (`Pillow 12.1.1` — `uv run python -c "import PIL"`).

## Package Legitimacy Audit

Фаза **не устанавливает ни одного внешнего пакета**. `gsd-tools query package-legitimacy check` не запускался, потому что проверять нечего.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | Новых пакетов нет |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

> Если планировщик всё же решит ввести зависимость для фикса CR-02 (`python-magic`, `filetype`), это **новый пакет** и он обязан пройти `gsd-tools query package-legitimacy check --ecosystem pypi <name>` до включения в план. Рекомендация исследования — не вводить (см. §Don't Hand-Roll).

## Architecture Patterns

### System Architecture Diagram

```
                    ┌─────────────────────────── БРАУЗЕР ────────────────────────────┐
                    │                                                                 │
  ввод в поле  ─────┤ htmx: hx-trigger="keyup changed delay:2s, change delay:2s"      │
  (НАЗВАНИЕ/ТЕКСТ)  │       hx-sync="this:replace"   hx-swap="none"                   │
                    │ Alpine: сворачивание карточек, модалки, $el.submit()            │
  выбор файла  ─────┤ fetch POST /api/uploads/image (по файлу)                        │
                    └───────┬──────────────────────────────┬──────────────────────────┘
                            │ POST (form-urlencoded)       │ multipart
                            ▼                              ▼
        ┌───────────────────────────────┐   ┌──────────────────────────────────────┐
        │ app/pages/ads.py              │   │ app/routes/uploads.py                │
        │  GET  /ads/new   (пусто,      │   │  POST /api/uploads/image             │
        │        записи НЕ создаёт D-03)│   │   ├─ safe_filename()  (есть)         │
        │  POST /ads/new   → создаёт    │   │   ├─ CR-02: сниффинг магических      │
        │        черновик, HX-Push-Url  │   │   │   байт вместо client Content-Type│
        │  POST /ads/{id}/edit          │   │   └─ ключ = {user_id}/{32hex}_{name} │
        │   ├─ WR-01: ключи ∈ user      │   └───────────────┬──────────────────────┘
        │   ├─ D-13: len(images) ≤ N    │                   │
        │   └─ ответ: OOB-фрагменты     │                   ▼
        └──────┬────────────────────────┘            ┌──────────────┐
               │                                     │  S3 (объекты │
               │ ответ = 3 OOB-фрагмента:            │  остаются,   │
               │  #ad-preview  #ad-summary           │  D-12)       │
               │  #autosave-indicator                └──────────────┘
               ▼
        ┌──────────────────────────────────────────────────────────┐
        │ Jinja2: ads/form.html + ads/includes/{preview,summary,   │
        │          sched_card}.html                                │
        └──────────────────────────────────────────────────────────┘
               │
               │ каждая карточка расписания — СВОЯ форма/свой POST (D-07)
               ▼
        ┌──────────────────────────────────────────────────────────┐
        │ app/pages/schedules.py                                   │
        │  POST /schedules/... (create/update/delete/toggle)       │
        │   └─ CR-01/D-20: владение ad_id И account_id             │
        │  ─ УДАЛЯЮТСЯ (D-14, ПОСЛЕ того как редактор заработал):  │
        │      GET/POST /schedules/new, GET/POST /schedules/{}/edit│
        └──────────────────────┬───────────────────────────────────┘
                               ▼
        ┌──────────────────────────────────────────────────────────┐
        │ PostgreSQL:  ads(+status, −is_active)   schedules(без    │
        │              изменений схемы)                            │
        └──────────────────────┬───────────────────────────────────┘
                               │ читает
                               ▼
        ┌──────────────────────────────────────────────────────────┐
        │ Celery beat (каждые celery_beat_interval сек)            │
        │   app.worker.tasks.check_schedules                       │
        │     └─ check_schedules_async  (tasks.py:143-156)         │
        │          └─ collect_due_schedules                        │
        │             (application/scheduling/use_cases.py:35)     │
        │             ★ D-01 живёт ЗДЕСЬ, не в tasks.py ★          │
        │             WHERE Schedule.is_active AND next_run_at<=now│
        │                   AND Ad.status != 'draft'   ← добавить  │
        └──────────────────────┬───────────────────────────────────┘
                               ▼
              dispatch_send_tasks → Celery «telegram» / Redis wa:queue / max:queue
                               ▼
                     send_message_once → адаптеры (НЕ ТРОГАЕМ)
```

### Recommended Project Structure

```
app/
├── models/ad.py                       # + status, − is_active  (D-02)
├── pages/ads.py                       # ads_new/create/edit/update переписаны
├── pages/schedules.py                 # new/edit удаляются; list/partial/toggle/delete остаются
├── routes/ads.py                      # AdResponse/UpdateAdRequest: is_active → status
├── routes/uploads.py                  # CR-02
├── routes/schedules.py                # D-20 (только проверка владения account_id)
├── application/scheduling/use_cases.py# ★ D-01
├── templates/
│   ├── ads/form.html                  # переписан; ДОЛЖЕН сохранить inline <script> (см. Pitfall 13)
│   ├── ads/includes/
│   │   ├── ad_card.html               # статус-ячейка: badge Черновик/Опубликовано
│   │   ├── preview.html               #  ← новый, OOB-цель #ad-preview
│   │   ├── summary.html               #  ← новый, OOB-цель #ad-summary
│   │   ├── autosave.html              #  ← новый, OOB-цель #autosave-indicator
│   │   └── sched_card.html            #  ← новый, карточка расписания в редакторе
│   ├── schedules/list.html            # переверстан в карточки
│   ├── schedules/partial_cards.html   # синхронно
│   ├── schedules/includes/schedule_row.html  # → sched_item (карточка, не data-row)
│   └── schedules/form.html            # УДАЛЯЕТСЯ (D-14)
└── static/css/app.css                 # + раздел «8.» в конец (сейчас файл кончается разделом 7 на 1149 строке)
alembic/versions/0013_ad_status.py     # ← новая ревизия
```

### Pattern 1: Строковый статус со значением по умолчанию, а не Enum БД

**What:** `Ad.status: Mapped[str] = mapped_column(String(20), default="published", server_default="published", index=True)`; допустимые значения `"draft"` и `"published"` объявляются одной константой в `app/constants.py` и используются и моделью, и шаблонами.
**When to use:** всегда в этом проекте — так устроены все остальные статусы.

Проект уже пользуется строковыми статусами без `sa.Enum`: `MessengerAccount.status` сравнивается со строкой `"active"` прямо в доменном коде.

```python
# Source: app/application/scheduling/use_cases.py:68 (verbatim)
        if not ad or not account or account.status != "active":
```

`server_default` обязателен: колонка добавляется в populated-таблицу и по D-02 существующие записи должны стать «опубликовано». Это ровно шаблон ревизии `0003`:

```python
# Source: alembic/versions/0003_add_is_blocked_to_users.py:21-24 (verbatim)
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), server_default="0", nullable=False),
    )
```

**Важно:** миграции **не применяются в тестах** — `tests/conftest.py:33` делает `Base.metadata.create_all`. Значит корректность самой ревизии `0013` (особенно `downgrade`) ни одним существующим тестом не проверяется, и план обязан добавить отдельную проверку (см. §Validation Architecture, Wave 0).

### Pattern 2: Автосохранение — `hx-swap="none"` + out-of-band фрагменты

**What:** форма несёт `hx-post`, `hx-trigger="keyup changed delay:2s, change delay:2s"`, `hx-sync="this:replace"` и `hx-swap="none"`. Ответ сервера — три фрагмента с `hx-swap-oob="true"`, каждый со своим `id`. Форма при этом **не перерисовывается никогда**.
**When to use:** ADS-04/ADS-05/ADS-06, то есть везде в редакторе.

Почему не `outerHTML`: любой swap, накрывающий поле ввода, сбрасывает каретку. Почему не `hx-target`: атрибут явной цели в проекте отсутствует по построению, и тест это фиксирует.

```
# Source: tests/test_pages/test_htmx_preserved.py:22-23 (verbatim)
Атрибута явной цели подмены в проекте нет нигде: все взаимодействия — это hx-get
с неявной целью (сам элемент) плюс hx-swap. Утверждать про явную цель нечего.
```

Обе htmx-возможности документированы [CITED: github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-swap-oob.md]:

> The `hx-swap-oob` attribute allows you to specify that some content in a response should be swapped into the DOM somewhere other than the target, that is "Out of Band". This allows you to piggyback updates to other element updates on a response.

и `hx-sync` — штатное средство против гонок при быстром наборе [CITED: github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-sync.md]:

> once a request is made, if the user begins typing again a new request will begin even if the previous one has not finished processing. This example will cancel any in-flight requests and use only the last request.

Индикатор состояния — чистый CSS по классу, который htmx вешает сам [CITED: htmx docs.md]: «When a request is issued, htmx adds the `htmx-request` class to the requesting element». Собственного таймера и собственного состояния нет — ровно то, что требует D-05 и UI-SPEC §Autosave indicator.

### Pattern 3: Предпросмотр читается из БД, а не из тела запроса

**What:** обработчик автосохранения сначала коммитит, затем рендерит `preview.html` из **перечитанного объекта `Ad`**.
**When to use:** ADS-06 («ровно в том виде, в каком уйдёт»).

Это не педантизм: сервер по D-13 может отклонить часть данных (лишние вложения), а по WR-01 — отфильтровать чужие ключи. Превью, собранное из формы, показало бы то, чего в БД нет. Что реально уходит в канал, видно из адаптера:

```python
# Source: app/application/scheduling/use_cases.py:214-218 (verbatim)
    result = await messenger.send_message(
        group_id=group.group_external_id,
        text=ad.text,
        images=images,
    )
```

`images` здесь — `[get_image_url(img, settings.s3_public_url) for img in ad.images]` (`use_cases.py:186-190`). Заголовок `ad.title` **в канал не уходит вообще** — ни один адаптер его не принимает (`send_message(group_id, text, images)` во всех трёх). Это надо учесть в макете превью: `.preview__title` из UI-SPEC — это заголовок карточки предпросмотра, а не часть сообщения.

### Pattern 4: Владение ключом изображения проверяется по префиксу

**What:** ключ имеет строгий вид и валидируется регуляркой при сохранении объявления.

```python
# Source: app/routes/uploads.py:66-67 (verbatim)
    filename = f"{uuid4().hex}_{safe_filename(file.filename)}"
    key = f"{user_id}/{filename}"
```

`safe_filename` уже сводит имя к `[A-Za-z0-9._-]{1,100}` (`uploads.py:16-17,37`). Точный фикс WR-01 выписан в ревью Фазы 1 и должен быть взят оттуда:

```python
# Source: .planning/phases/01-interfeysnyy-fundament/01-REVIEW.md:326-331 (verbatim)
_KEY_RE = re.compile(r"^\d+/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}$")

def _own_image_keys(values: list[str], user_id: int) -> list[str]:
    out = []
    for v in values:
```

Проверка нужна **на четырёх входах**: `app/pages/ads.py:134` (create), `app/pages/ads.py:184` (update), и JSON-API `CreateAdRequest.images` / `UpdateAdRequest.images` (`app/routes/ads.py:16,22`).

### Pattern 5: Расписание в редакторе — самостоятельная форма, не часть формы объявления

**What:** каждая карточка расписания — отдельный `<form method="post" action="/schedules/{id}/edit">` (или `/schedules/new` для новой), физически **вне** формы объявления. Вложенные формы в HTML запрещены; попытка положить карточки внутрь `<form>` объявления даст молча неработающие кнопки.
**When to use:** ADS-07/ADS-08 (D-07 + D-09).

Контракт имён полей менять нельзя — он читается обработчиком:

```python
# Source: app/pages/schedules.py:178-181 (verbatim)
    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]
```

Плюс `Form(...)`-поля `ad_id` и `account_id` (`schedules.py:169-170`, `274-275`).

Отдельный подарок: D-08 («неполное расписание сохраняется, но выключенным») уже поддержан доменом. `compute_next_run_at` возвращает `None`, когда дней или времён нет, а `collect_due_schedules` требует `next_run_at <= now` — значит неполное расписание физически не может быть выбрано к отправке даже если `is_active` кто-то выставит.

```python
# Source: app/services/schedule_service.py:17-18 (verbatim)
    if not days_of_week or not times_of_day:
        return None
```

### Pattern 6: Сводный список — карточки, а не `data-row`

**What:** `/schedules` перестаёт быть таблицей. Триада `list.html` + `partial_cards.html` + `includes/schedule_row.html` правится **синхронно**: `SCHEDULE_COLS`/`SCHEDULE_COLUMNS` и `rowhead(...)` уходят, вместо них `[data-sched-list]` + `.sched-item` из UI-SPEC. Сентинел бесконечной прокрутки остаётся дословно одинаковым в двух файлах.

```jinja
{# Source: app/templates/schedules/list.html:28 и app/templates/schedules/partial_cards.html:6 (идентичны, verbatim) #}
<div hx-get="/schedules/partial?offset={{ next_offset }}&limit=30" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
```

Этот инвариант проверяется `tests/test_pages/test_htmx_preserved.py` на **второй** странице выдачи (`SEED_ROWS = 61`), а не на первой.

### Anti-Patterns to Avoid

- **Замена формы автосохранением (`hx-swap="outerHTML"` на `<form>`).** Каретка и выделение сбрасываются на каждой паузе ввода; пользователь физически не сможет печатать длинный текст.
- **Клиентская сборка предпросмотра из значений полей.** Нарушает ADS-06 и D-10: показывает то, чего в БД может не быть (лишние вложения отклонены D-13, чужие ключи отброшены WR-01).
- **Вложенная `<form>` для карточки расписания.** Браузер молча отбрасывает внутреннюю форму — «Сохранить» на карточке перестанет работать, и без JS, и с ним.
- **Удаление `Ad.is_active` из модели без правки `AdResponse`.** Pydantic `from_attributes`-сериализация упадёт на каждом `/api/ads` — 500 на четырёх маршрутах.
- **Миграция `0013` раньше удаления `/schedules/new`.** Ломает `Ad.is_active == True` в `app/pages/schedules.py:131,240` — то есть ровно тот путь создания расписания, который SC-3 требует держать живым.
- **`sa.Enum` для `status`.** На PostgreSQL создаёт именованный тип, который `downgrade` обязан удалять отдельным шагом; в проекте прецедента нет.
- **`Image.open()` для проверки типа загружаемого файла.** Открывает вектор decompression bomb там, где хватает четырёх сигнатур; Pillow к тому же не объявлена прямой зависимостью.
- **Прогресс-бар в карточке расписания.** UI-SPEC: «Forbidden in this phase: `.progress` inside a schedule card» (D-17).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Дебаунс ввода | `setTimeout`/`clearTimeout` в своём `<script>` | `hx-trigger="... changed delay:2s"` | D-05 прямо запрещает свой таймер; htmx даёт `changed` (не слать, если значение то же) бесплатно [CITED: hx-trigger.md] |
| Отмена устаревших автосохранений | Флаг «идёт запрос» + очередь | `hx-sync="this:replace"` | Документированное средство ровно для active-search/автосохранения [CITED: hx-sync.md] |
| Индикатор «сохраняем…» | Своё состояние + подписка на события htmx | CSS по `.htmx-request` | Класс вешает сам htmx на инициатора запроса — рассинхрон невозможен [CITED: htmx docs.md] |
| Вычисление следующего запуска | Свой обход дней/времён | `compute_next_run_at` | Уже есть, знает про таймзоны и возвращает `None` при неполноте [VERIFIED: app/services/schedule_service.py:5-46] |
| Санитизация имени файла | Свой `replace` | `safe_filename` | Фикс Фазы 1, покрыт `tests/test_routes/test_uploads.py::test_upload_key_stays_inside_user_prefix` [VERIFIED: app/routes/uploads.py:21-38] |
| Подтверждение удаления | `confirm()` | Макрос `modal(...)` | Phase 1 заменил `confirm()` в 13 местах; тесты `*_degrades_without_alpine` [VERIFIED: app/templates/components/modal.html:49] |
| Сворачиваемые фильтры списка | Своя разметка | Макрос `filters(id, action, method, open_on_desktop, label)` | D-17 требует переиспользования [VERIFIED: app/templates/components/filters.html:24] |
| Бейджи, тумблеры, поля, карточки, алерты, пустые состояния | Копипаста разметки | 13 макросов `components/*.html` | UI-SPEC §Component Inventory: «do not fork, do not restyle» |
| Форматирование даты в таймзоне пользователя | `strftime` в шаблоне | `format_datetime_for_user(value, user, fmt)` | Глобал окружения [VERIFIED: app/pages/common.py:102-118] |

**Обратный случай — здесь руками правильно.** Проверка типа файла (CR-02) должна быть **своей проверкой первых байтов на четыре сигнатуры** (JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, GIF `GIF87a`/`GIF89a`, WebP `RIFF….WEBP`), а не библиотекой:

- `python-magic` тянет системный `libmagic` — новая внешняя зависимость в Docker-образе;
- `imghdr` из stdlib удалён в Python 3.13 — тупик;
- `Pillow` присутствует **транзитивно** через `qrcode[pil]` (проверено: 12.1.1), полагаться на транзитивную зависимость нельзя, а `Image.open()` на недоверенном файле добавляет decompression bomb к тому самому эндпоинту, который мы чиним.

**Key insight:** в этом проекте почти всё, что кажется новым, уже написано в Фазе 1 или в домене. Настоящая работа фазы — не изобретение механизмов, а **аккуратный учёт читателей**: кто ещё читает `Ad.is_active`, кто ещё ходит на `/schedules/new`, какой запрос выбирает расписания к отправке. Все три списка ниже, в §Runtime State Inventory и §Common Pitfalls.

## Runtime State Inventory

> Фаза меняет схему и удаляет маршруты — раздел обязателен.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | 1) Колонка `ads.is_active` (значения всех существующих строк) — по D-02 удаляется, а состояние переезжает в новую `ads.status` со значением `published` для всех. 2) `Ad.images` — JSON-массив ключей вида `{user_id}/{32hex}_{name}`; после WR-01 в БД могут уже лежать чужие/внешние значения, внесённые до фикса. 3) `SendLog.ad_images` — снапшоты, **не трогать** (основание D-12). | (1) миграция данных внутри `0013` (`server_default="published"` покрывает backfill). (2) **решить и записать**: фикс WR-01 отсеивает чужие ключи только на записи; уже сохранённые значения останутся. Нужна ли разовая чистка — открытый вопрос Q4. (3) действий нет |
| **Live service config** | Нет. Внешние сервисы (S3, Redis, YooKassa, SMTP) не хранят ни статус объявления, ни конфигурацию расписаний. Проверено: `Ad.status` не существует нигде, кроме планируемой колонки (grep по `app/` — ноль совпадений). | Нет |
| **OS-registered state** | Нет. Celery beat читает расписание задач **из кода** (`app/worker/celery_app.py:29-49`, `beat_schedule={...}`), а не из БД или сохранённого состояния планировщика; имена задач (`app.worker.tasks.check_schedules` и др.) фаза не меняет. Docker-контейнеры воркеров именуются по `account_id`, объявления в имени не участвуют. | Нет |
| **Secrets/env vars** | Нет переименований. **Но:** `.env` разработчика активно протекает в тесты через `Settings.model_config = {"env_file": ".env"}` (`app/config.py:77`) — это причина 28 падающих тестов, см. §Common Pitfalls 0. Сам файл `.env` в git не хранится (`.gitignore:20`). | Изоляция тестовых `Settings` (`_env_file=None`) — задача первого плана |
| **Build artifacts** | Нет. Build-шага у фронтенда нет по Phase 1 D-02; Python-пакет не устанавливается в editable-режиме. Единственный «артефакт» — cache-busting `asset_version` от mtime `app.css` (`app/pages/common.py:41-53`), он пересчитывается сам при импорте после правки CSS. | Нет |

**Пятая, не входящая в стандартные категории, но критичная:** **удаляемые маршруты имеют внешних читателей внутри репозитория.** Полный список ссылок на `/schedules/new` и `/schedules/{id}/edit` (получен grep-ом по `app/` и `tests/`):

| Файл:строка | Что ссылается | Действие |
|---|---|---|
| `app/templates/schedules/list.html:14` | `link_button('Создать', '/schedules/new', icon='plus')` | Удалить (UI-SPEC: вместо неё «К объявлениям») |
| `app/templates/schedules/list.html:35` | `empty_state(..., action_href='/schedules/new')` | Заменить на `/ads` |
| `app/templates/schedules/includes/schedule_row.html:71` | `link_button('Изменить', '/schedules/{id}/edit', ...)` | Заменить на «Открыть объявление» → `/ads/{ad_id}/edit?sched={id}` |
| `app/templates/schedules/form.html:26` | сама форма | Файл удаляется целиком (D-14) |
| `tests/test_pages/test_shell.py:85` | `/schedules/new` в списке страниц шелла | Убрать из списка |
| `tests/test_pages/test_responsive_markup.py:276` | `assert f"/schedules/{schedule.id}/edit" in html` | Переписать на новую ссылку |
| `tests/test_pages/test_schedules_detached_account.py:96` | `await client.get(f"/schedules/{schedule_id}/edit")` | Переписать на редактор объявления |
| `tests/test_routes/test_schedules_toggle_detached.py:171` | `/schedules/{id}/edit` | Переписать |
| `tests/test_routes/test_schedules_profile_timezone.py:28` | `await client.get("/schedules/new")` | Переписать (таймзона теперь только read-only подпись) |

## Common Pitfalls

### Pitfall 0: Суита не зелёная на базовом коммите — 25 failed + 3 errors из 652

**What goes wrong:** план начинается с ложной посылки «все тесты зелёные, любая краснота — моя». Она неверна.
**Why it happens:** `Settings` читает `.env` при **каждом** конструировании, а десять тестовых модулей строят собственные `Settings(...)`, не переопределяя все поля.

```python
# Source: app/config.py:77 (verbatim)
    model_config = {"env_file": ".env", "extra": "ignore"}
```

Единственный модуль, который защищается, — общий conftest:

```python
# Source: tests/conftest.py:21 (verbatim)
        smtp_host="",
```

Все остальные наследуют реальный SMTP разработчика, регистрация начинает требовать подтверждение почты и отвечает `400`. Проверено в этой сессии:

```
smtp_host from .env leak = 'smtp.timeweb.ru'
REGISTER 400 {"detail":"Email verification required"}
```

Полный прогон `uv run pytest tests/ -q` (12 мин 21 с): **25 failed, 624 passed, 3 errors** из 652 собранных. Падают ровно те модули, которые строят свой `Settings`: `test_config_s3.py` (1), `test_e2e.py` (1), `test_routes/test_groups_bulk.py` (1), `test_routes/test_sync_groups.py` (4), `test_routes/test_tg_user_auth.py` (10), `test_routes/test_uploads.py` (1 + 3 errors), `test_routes/test_wa_sync_status.py` (7).

**How to avoid:** `Settings(_env_file=None, ...)` в каждой тестовой фикстуре. Проверено:

```
with .env       smtp_host = 'smtp.timeweb.ru'
_env_file=None  smtp_host = ''
_env_file=None  s3_public_url = ''
```

**Warning signs:** `400 {"detail":"Email verification required"}` в логах теста; `NoResultFound` на `select(User)` сразу после «регистрации».

**Замечание про число 393.** ROADMAP §Phase 1 Cross-cutting constraints требует «все 393 существующих теста остаются зелёными». Фактически суита собирает **652** теста — 393 было до Фазы 1. Планировщику нужно писать 652, иначе критерий формально ничего не проверяет.

### Pitfall 1: D-21 и Pitfall 0 — одна и та же болезнь с двух сторон, и обе нельзя проверить одновременно

**What goes wrong:** план чинит D-21, прогоняет суиту, видит 28 падений и считает, что сломал сам.
**Why it happens:** три шаблонных глобала конструируют настройки в обход подмены зависимостей:

```python
# Source: app/pages/common.py:36-38 (verbatim)
templates.env.globals["get_image_url"] = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["resolve_image_url"] = _resolve_image_url
templates.env.globals["s3_public_url"] = lambda: get_settings().s3_public_url
```

CONTEXT.md D-21 называет только строку 38, но `get_settings()` вызывают **все три** (строка 37 — через `_resolve_image_url`, `common.py:27-33`). `get_settings` — `@lru_cache`-обёртка над `Settings()` (`app/config.py:87-89`).

Проверено экспериментально:

- **С `.env` в рабочем каталоге:** `GET /ads/new` под `authed_client` возвращает **200**. Комментарий `tests/test_pages/test_shell.py:105-112` («`/ads/new` в тестовой среде отдаёт 500») верен только без `.env`.
- **Без `.env` в cwd:** `Settings()` → `ValidationError: 2 validation errors ... database_url Field required ... secret_key Field required`.

Итого: **страница либо рендерится, либо нет — в зависимости от того, лежит ли рядом `.env`; и ровно в той конфигурации, где она рендерится, красные 28 тестов.**

**How to avoid:** оба фикса в **одном** первом плане: (а) `_env_file=None` в фикстурах, (б) `s3_public_url` приходит в шаблон через контекст ответа (или через `request.state`), а не через глобал, вызывающий `get_settings()`. Ревью Фазы 1 отдельно просит и правку контекста экранирования:

```
# Source: .planning/phases/01-interfeysnyy-fundament/01-REVIEW.md:625-626 (verbatim)
escaper/context mismatch class as CR-01. Prefer `{{ s3_public_url() | tojson }}` (no surrounding
quotes), which is correct in JS context.
```

**Warning signs:** тест `/ads/new` зелёный локально и красный в CI (или наоборот).

### Pitfall 2: `Ad.is_active` читают восемь мест, и одного из них нет ни в одном списке CONTEXT.md

**What goes wrong:** миграция дропает колонку, `/dashboard` начинает падать.
**Why it happens:** CONTEXT.md перечисляет `app/pages/ads.py`, `app/pages/schedules.py` и шаблоны, но не дашборд.

Полный список (grep по `app/` и `tests/`):

| Файл:строка | Использование | Судьба |
|---|---|---|
| `app/models/ad.py:19` | `is_active: Mapped[bool] = mapped_column(Boolean, default=True)` | удаляется (D-02) |
| **`app/pages/dashboard.py:33`** | `Ad.user_id == user.id, Ad.is_active == True` — счётчик «объявлений» на дашборде | **не упомянут в CONTEXT.md**; должен стать `Ad.status == "published"` или потерять условие |
| `app/pages/schedules.py:131` | `select(Ad).where(..., Ad.is_active == True)` в `schedules_new` | уходит вместе со страницей (D-14) — **но только если удаление раньше миграции**, см. Pitfall 3 |
| `app/pages/schedules.py:240` | то же в `schedules_edit` | то же |
| `app/pages/ads.py:188` | `ad.is_active = is_active` | переписывается |
| `app/templates/ads/includes/ad_card.html:44` | `{%- if ad.is_active %}{{ badge('Активно','success') }}{% else %}{{ badge('Пауза','neutral') }}{% endif -%}` | → `Черновик`/`Опубликовано` (UI-SPEC E15) |
| `app/templates/ads/form.html:35` | `toggle(name="is_active", checked=ad.is_active, ...)` | удаляется (D-04: только «Сохранить») |
| `tests/test_models/test_ad.py:33,58` | `assert ad.is_active is True` | переписываются |

**How to avoid:** миграция, модель и **все восемь** читателей — один коммит. Проверка: `grep -rn "is_active" app/ tests/ \| grep -i "ad"` должен вернуть только `Group.is_active` и `Schedule.is_active`.

### Pitfall 3: Порядок «миграция ↔ удаление `/schedules/new`» жёстче, чем формулирует D-16

**What goes wrong:** SC-3 («ни в один момент выката пользователь не остаётся без возможности создать расписание») нарушается **не удалением страницы, а миграцией**.
**Why it happens:** страницы `/schedules/new` и `/schedules/{id}/edit` фильтруют объявления по `Ad.is_active`:

```python
# Source: app/pages/schedules.py:131 (verbatim)
            select(Ad).where(Ad.user_id == user.id, Ad.is_active == True)  # noqa: E712
```

D-16 гарантирует, что старый путь жив, пока новый не заработал. Но если миграция `0013` (дроп `is_active`) выкатится, пока страницы ещё живы, обе упадут с ошибкой SQL — и в промежутке пользователь останется без обоих путей.

**How to avoid:** ровно один из двух порядков, и он должен быть записан в плане явно:
- **(A)** миграция → но в том же коммите `schedules.py:131,240` переписаны на `Ad.status == "published"` (страницы живут до своего удаления); **или**
- **(B)** удаление `/schedules/new` и `/schedules/{id}/edit` → затем миграция.
Вариант (B) конфликтует с D-16 (удаление должно идти **после** работающего редактора, а редактор нуждается в `status`). Значит рабочий порядок — **(A)**.

**Warning signs:** `sqlalchemy.exc.ProgrammingError: column ads.is_active does not exist` на `/schedules/new`.

### Pitfall 4: `Ad.is_active` — часть публичного JSON-API

**What goes wrong:** удаление поля из модели даёт 500 на четырёх маршрутах `/api/ads`, потому что ответная схема требует поле, которого больше нет.

```python
# Source: app/routes/ads.py:26-32 (verbatim)
class AdResponse(BaseModel):
    id: int
    title: str
    text: str
    images: list
    is_active: bool
    created_at: datetime
```

и на входе:

```python
# Source: app/routes/ads.py:19-23 (verbatim)
class UpdateAdRequest(BaseModel):
    title: str | None = None
    text: str | None = None
    images: list[str] | None = None
    is_active: bool | None = None
```

`update_ad` делает `repo.update(ad, **data.model_dump(exclude_unset=True))` (`routes/ads.py:83`) — то есть присваивает `is_active` напрямую в модель. После дропа поля вызов с `is_active` упадёт.

**How to avoid:** `is_active` → `status` в обеих схемах в том же коммите; `UpdateAdRequest.status` валидировать `Literal["draft","published"]`, иначе через API можно записать произвольную строку и получить объявление, которое не отфильтруется ни как черновик, ни как опубликованное. UI-SPEC E15 (`error`) на это уже отвечает со стороны рендера: «A status value outside the enum falls back to the «Черновик» badge».

### Pitfall 5: D-01 указывает не на тот файл

**What goes wrong:** исполнитель открывает `app/worker/tasks.py`, ищет там `select(Schedule)`, находит его и правит… не то место (в `tasks.py` действительно есть `from sqlalchemy import select` и импорт `Schedule`, но реальный запрос выбора due-расписаний оттуда давно вынесен).

Настоящий запрос:

```python
# Source: app/application/scheduling/use_cases.py:48-56 (verbatim)
    result = await session.execute(
        select(Schedule)
        .options(joinedload(Schedule.ad), joinedload(Schedule.account))
        .where(
            Schedule.is_active == True,  # noqa: E712
            Schedule.next_run_at <= now,
        )
    )
    schedules = result.unique().scalars().all()
```

`tasks.py` только зовёт его:

```python
# Source: app/worker/tasks.py:146-150 (verbatim)
    tasks: list[DispatchTask] = await collect_due_schedules(
        session,
        now=now,
        check_limit=check_balance_cached,
    )
```

**How to avoid:** правка идёт в `app/application/scheduling/use_cases.py`. Два варианта: добавить `.join(Ad, Schedule.ad_id == Ad.id).where(Ad.status != "draft")` в сам запрос, **или** — предпочтительнее — расширить уже существующую ветку пропуска, которая корректно передвигает `next_run_at` вместо того чтобы оставить расписание «залипшим» в прошлом:

```python
# Source: app/application/scheduling/use_cases.py:68-75 (verbatim)
        if not ad or not account or account.status != "active":
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue
```

Второй вариант сильно лучше: фильтр в `WHERE` оставил бы `next_run_at` в прошлом, и в момент публикации черновика расписание немедленно выстрелило бы всеми пропущенными слотами. Это тихая рассылка задним числом — ровно тот класс аварии, ради которого D-01 помечен «costly».

**Defence in depth:** имеет смысл продублировать проверку в `send_message_once` (`use_cases.py:143-166`), где уже есть каскад «нет объявления / аккаунт не активен → пишем SendLog и выходим». Задача может долететь до воркера уже после того, как объявление вернули в черновик.

### Pitfall 6: Порога длины текста в коде **нет** — UI-SPEC assumption 1 нельзя закрыть чтением репозитория

**What goes wrong:** планировщик, следуя UI-SPEC («The planner must read the real cap from `app/messengers/*`»), ищет константу и не находит; либо берёт 4096 и счётчик врёт для объявлений с вложениями.
**Why it happens:** ограничения там просто нет. Grep по `app/messengers/{telegram_user,whatsapp,max}.py` на `1024|4096|caption|MAX_|limit` даёт только `caption=text` и HTTP-пулы. Текст уходит как есть:

```python
# Source: app/messengers/telegram_user.py:219-222 (verbatim)
                    await self.client.send_file(
                        int(group_id), files, caption=text,
                        force_document=False,
                    )
```

Модель тоже не ограничивает: `text: Mapped[str] = mapped_column(Text)` (`app/models/ad.py:17`) — без длины. Ограничен только заголовок: `String(255)` (`ad.py:16`).

**Внешний факт [CITED: множественные источники, MEDIUM]:** Telegram допускает 4096 символов для обычного текстового сообщения и **1024 для подписи к медиа** у не-Premium аккаунтов; у Premium подпись тоже 4096. Проект шлёт от **userbot-аккаунта пользователя** (Telethon/MTProto), и Premium-статус этого аккаунта приложению неизвестен.

**How to avoid:** порог — продуктовое решение, а не находка в коде. Разумный, честный вариант: 4096 как общий предел, а при наличии хотя бы одного вложения — предупреждение (`--warn`) от 1024, потому что выше этого порога отправка в Telegram без Premium упадёт. Требует подтверждения (см. §Open Questions Q1). Что бы ни выбрали — **счётчик не должен блокировать сохранение**: протоколы отправки не трогаем (жёсткая рамка milestone), и обрезать текст на сохранении нельзя.

**Warning signs:** `MediaCaptionTooLongError` в `SendLog.error_message` — сегодня она попала бы в `except Exception` и вернулась бы как `no_retry` (`telegram_user.py:238-240`).

### Pitfall 7: Лимит вложений уже есть в конфиге — не заводите второй

`Settings.max_images_per_ad: int = 10` (`app/config.py:26`) существует и **нигде не используется** (grep: только объявление). D-13 требует серверного принуждения — это ровно та настройка. Захардкоженная десятка в обработчике создаст второй источник истины, расходящийся с конфигом.

### Pitfall 8: Смена аккаунта в расписании обязана сбрасывать группы, и сервер это уже частично делает

Обработчики валидируют принадлежность групп аккаунту и **молча выбрасывают** несоответствующие:

```python
# Source: app/pages/schedules.py:298-308 (verbatim)
    if group_ids:
        valid_groups = (
            await db.execute(
                select(Group.id).where(
                    Group.id.in_(group_ids),
                    Group.account_id == account_id,
                    Group.user_id == user.id,
                )
            )
        ).scalars().all()
        group_ids = [gid for gid in group_ids if gid in valid_groups]
```

UI-SPEC (Interaction Contract, E5 `partial`) требует того же на UI. Хорошо: контракты сходятся. Плохо: молчаливое отбрасывание означает, что после смены аккаунта расписание может стать неполным (`group_ids == []`) **без сообщения**. По D-08 оно тогда обязано сохраниться выключенным и получить бейдж «НЕ ЗАПОЛНЕНО» — то есть обработчик должен ещё и выставить `is_active=False`, чего он сегодня не делает.

### Pitfall 9: `compute_next_run_at` падает на кривом времени

```python
# Source: app/services/schedule_service.py:27-30 (verbatim)
    parsed_times = []
    for t_str in times_of_day:
        parts = t_str.split(":")
        parsed_times.append(time(int(parts[0]), int(parts[1])))
```

`int(...)` бросает `ValueError`, `parts[1]` — `IndexError`, на любом значении не формата `HH:MM`. Сегодня вход приходит из `input type="time"`, но D-13-логика фазы («клиентским данным не верим») распространяется и сюда: POST можно послать мимо браузера. Обработчик обязан отфильтровать значения по формату **до** вызова, иначе получим 500 вместо валидационной ошибки.

### Pitfall 10: Тесты редактора нельзя писать «как для страницы» — суита фиксирует ИСХОДНИК шаблона

Шесть тестов читают файл `app/templates/ads/form.html` как текст, а не рендер:

```python
# Source: tests/test_templates/test_ads_form_security.py:23-27 (verbatim)
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
ADS_FORM = TEMPLATES_DIR / "ads" / "form.html"


def form_source() -> str:
    return ADS_FORM.read_text(encoding="utf-8")
```

Их утверждения жёсткие: `script_source()` требует **хотя бы один `<script>`-блок в этом файле** (`assert blocks, "в ads/form.html не найдено ни одного блока скрипта"`), а `test_ads_form_uses_property_assignment` требует `createElement` ≥ 3, наличие `textContent` и `replaceChildren` ≥ 2 **в том же файле**. Плюс запреты: `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` = 0, `onclick=` внутри скрипта = 0.

**Следствие:** если переписанный редактор вынесет плитки вложений в отдельный include или в `app/static/js/`, шесть тестов покраснеют, и это будет выглядеть как регрессия безопасности, хотя ею не является. CONTEXT.md прямо говорит «их контракт нельзя ломать». Два честных пути: (а) оставить клиентскую сборку плиток в `ads/form.html`; (б) перенести тесты на новый путь **осознанно, отдельной задачей, с записью в плане** — но не «заодно».

Заметьте: ревью Фазы 1 само считает этот стиль слабым местом («WR-03: The CR-01 regression test asserts on template *source text*, not on behaviour», `01-REVIEW.md:379`). После фикса D-21 появляется возможность заменить проверки исходника настоящими HTTP-тестами — это уместное улучшение именно в этой фазе.

### Pitfall 11: Все страничные обработчики расписаний отвечают редиректом на `/schedules`

`schedules_create`, `schedules_update`, `schedules_toggle`, `schedules_delete` заканчиваются `RedirectResponse(url="/schedules", status_code=302)` (`schedules.py:215,324,362,385`). В редакторе объявления это выкинет пользователя со страницы после каждой правки расписания. Нужен либо параметр возврата, либо HTMX-ответ фрагментом карточки. Маршруты при этом менять нельзя (D-15 — про JSON-API; страничный слой фаза переписывает, но SCH-05 опирается на `POST /schedules/{id}/toggle` как есть).

### Pitfall 12: `toggle` для расписания без аккаунта заблокирован — это не баг

```python
# Source: app/pages/schedules.py:344-350 (verbatim)
    # issue #35: отвязанное расписание нельзя возобновить, пока пользователь не
    # привяжет аккаунт на форме редактирования. Пауза активного не блокируется.
    resume_blocked = (
        schedule is not None
        and not schedule.is_active
        and schedule.account_id is None
    )
```

Комментарий отсылает к «форме редактирования», которая по D-14 исчезает. Текст и путь восстановления надо переписать на редактор объявления, иначе пользователь получит заблокированный тумблер без объяснения, куда идти. UI-SPEC покрывает соседний случай («Включить нельзя: выберите аккаунт…»), но именно этот — отвязанное после удаления аккаунта расписание — в контракте не назван.

### Pitfall 13: Триада шаблонов списка правится синхронно

`SCHEDULE_COLS` и `SCHEDULE_COLUMNS` объявлены в `schedules/includes/schedule_row.html:24-25` и импортируются `list.html:6`. `partial_cards.html:1` импортирует сам макрос. Правка одного файла из трёх даёт страницу, которая отдаёт 200 и рендерит мусор — Jinja не ругается на пропавший параметр макроса. Тест-страховка существует: `tests/test_pages/test_responsive_markup.py:261` (`test_schedules_card_renders_data`), но его утверждения включают `/schedules/{id}/edit` (строка 276) и потому сами требуют правки.

## Code Examples

### 1. Миграция `0013` — добавить `status`, снять `is_active`

```python
# Форма ревизии — по образцу alembic/versions/0012 (dialect-aware) и 0003 (server_default).
"""ads.status (draft|published), drop ads.is_active

Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"


def upgrade():
    op.add_column(
        "ads",
        sa.Column("status", sa.String(20), server_default="published", nullable=False),
    )
    # Backfill не нужен отдельным UPDATE: server_default уже проставил всем строкам
    # "published" — то есть ровно поведение D-02 («существующие записи мигрируют
    # в опубликовано»).
    op.create_index("ix_ads_status", "ads", ["status"])
    op.drop_column("ads", "is_active")


def downgrade():
    # ВНИМАНИЕ: откат необратимо теряет данные — какое объявление было черновиком,
    # восстановить неоткуда. Все строки возвращаются активными.
    op.add_column(
        "ads",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.drop_index("ix_ads_status", table_name="ads")
    op.drop_column("ads", "status")
```

Формат ревизии подтверждён: `revision = "0012"` / `down_revision = "0011"` — строки с ведущими нулями [VERIFIED: alembic/versions/0012_schedules_account_id_nullable_set_null.py:12-13]. Предупреждение про необратимость — принятый в проекте стиль [VERIFIED: там же, строки 49-52].

Если на каком-то диалекте `drop_column` окажется проблемой, штатное средство — `batch_alter_table` [CITED: github.com/sqlalchemy/alembic/blob/main/docs/build/batch.rst]:

```python
with op.batch_alter_table("some_table") as batch_op:
    batch_op.add_column(Column('foo', Integer))
    batch_op.drop_column('bar')
```

На PostgreSQL (прод по `alembic.ini`) обычный `add_column`/`drop_column` достаточен.

### 2. Автосохранение — разметка формы

```jinja
{# app/templates/ads/form.html — форма объявления.
   hx-swap="none": форма НИКОГДА не перерисовывается, каретка не теряется.
   hx-sync: устаревший запрос отменяется при продолжении набора.
   Без htmx форма остаётся обычной POST-формой — базовый путь D-09. #}
<form id="ad-form"
      method="post"
      action="{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}"
      hx-post="{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}"
      hx-trigger="keyup changed delay:2s from:find input, keyup changed delay:2s from:find textarea, change delay:2s"
      hx-sync="this:replace"
      hx-swap="none">
  ...
</form>
```

Дебаунс — штатный модификатор [CITED: github.com/bigskysoftware/htmx/blob/master/www/content/attributes/hx-trigger.md]:

```html
<input name="q" hx-get="/search" hx-trigger="input changed delay:1s" hx-target="#search-results"/>
```

### 3. Автосохранение — ответ сервера (OOB)

```jinja
{# Ответ на POST /ads/{id}/edit при HX-Request. Основного swap нет (hx-swap="none"),
   всё приходит out-of-band по id. #}
<div id="ad-preview" hx-swap-oob="true">{% include "ads/includes/preview.html" %}</div>
<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>
<div id="autosave-indicator" hx-swap-oob="true" aria-live="polite" class="autosave">Сохранено</div>
```

```python
# app/pages/ads.py — обработчик автосохранения (эскиз).
# 1) владение объявлением; 2) владение ключами (WR-01); 3) лимит (D-13);
# 4) КОММИТ; 5) рендер превью из ЗАПИСАННОГО объекта (D-10).
if request.headers.get("HX-Request"):
    resp = templates.TemplateResponse("ads/includes/autosave_response.html", {...})
    if created:                                   # D-03: первое сохранение создало черновик
        resp.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"
    return resp
return RedirectResponse(url="/ads", status_code=302)   # путь без JS не меняется
```

Индикатор «Сохраняем…» — CSS, состояния в Python нет [CITED: htmx docs.md, «htmx adds the `htmx-request` class to the requesting element»]:

```css
/* app/static/css/app.css, раздел 8 */
.autosave__busy { display: none; }
#ad-form.htmx-request .autosave__idle { display: none; }
#ad-form.htmx-request .autosave__busy { display: inline; }
```

### 4. Владение ключом изображения (WR-01) и лимит (D-13)

```python
# app/pages/ads.py — общая функция для create/update и для JSON-API.
import re
from fastapi import HTTPException, status

_KEY_RE = re.compile(r"^\d+/[0-9a-f]{32}_[A-Za-z0-9._-]{1,100}$")


def own_image_keys(values: list[str], user_id: int, max_images: int) -> list[str]:
    """Только ключи, лежащие под префиксом вызывающего, и не больше лимита."""
    prefix = f"{user_id}/"
    keys = [v.strip() for v in values if v.strip()]
    if any(not _KEY_RE.match(k) or not k.startswith(prefix) for k in keys):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Недоступное вложение")
    if len(keys) > max_images:                      # D-13, порог из settings.max_images_per_ad
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Слишком много вложений")
    return keys
```

Регулярка взята из ревью Фазы 1 [VERIFIED: .planning/phases/01-interfeysnyy-fundament/01-REVIEW.md:326]; формат ключа подтверждён кодом загрузки [VERIFIED: app/routes/uploads.py:66-67].

### 5. Проверка типа файла по содержимому (CR-02)

```python
# app/routes/uploads.py — заменяет проверку file.content_type (строки 48-52).
_MAGIC = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)

def sniff_image(content: bytes) -> str | None:
    for sig, mime in _MAGIC:
        if content.startswith(sig):
            return mime
    # WebP: RIFF....WEBP — размер файла в байтах 4..8 произволен
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None
```

Четыре формата — ровно те, что названы в UI-SPEC §Error states («подойдут только изображения JPEG, PNG, WebP или GIF»). `content` уже читается целиком строкой ниже по обработчику [VERIFIED: app/routes/uploads.py:55], так что дополнительного чтения не требуется — надо лишь переставить порядок: сначала прочитать, потом проверить.

### 6. Пропуск черновика в подборе due-расписаний (D-01)

```python
# app/application/scheduling/use_cases.py — расширение существующей ветки пропуска
# (строки 68-75). Именно ветка, а не WHERE: иначе next_run_at застрянет в прошлом
# и публикация черновика вызовет залп пропущенных отправок.
        if (
            not ad
            or ad.status == "draft"          # ← D-01
            or not account
            or account.status != "active"
        ):
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
                now=now,
            )
            continue
```

`schedule.ad` доступен без дополнительного запроса — он уже загружен `joinedload` [VERIFIED: app/application/scheduling/use_cases.py:50].

### 7. Изоляция тестовых настроек (первый план)

```python
# tests/conftest.py и все модульные фикстуры, строящие Settings.
return Settings(
    _env_file=None,                       # ← .env разработчика не протекает в тесты
    database_url="sqlite+aiosqlite:///:memory:",
    secret_key="test-secret-key",
    ...
)
```

Проверено в этой сессии: с `_env_file=None` `smtp_host` и `s3_public_url` дают пустые строки-умолчания вместо значений из `.env`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `Ad.is_active` как «активность» объявления | `Ad.status` (`draft`/`published`) с реальным эффектом на отправку | Эта фаза (D-01/D-02) | Флаг был мёртвым — пайплайн отправки его не читал [VERIFIED: grep `is_active` в `app/application/`, `app/worker/` — только `Schedule.is_active`] |
| Расписания настраиваются на `/schedules/new` | Расписания настраиваются в редакторе объявления | Эта фаза (D-14…D-16) | Список становится read-mostly |
| `confirm()` | Макрос `modal(...)` с настоящей POST-формой | Phase 1 | 13 мест; тесты `*_degrades_without_alpine` |
| Строчная вёрстка + `*_rows.html` | Только `layout=cards`; шесть шаблонов удалены | Phase 1 | `layout` в query принимается и игнорируется [VERIFIED: app/pages/ads.py:46-50] |
| Tailwind CDN | Одна рукописная `app.css` без build-шага | Phase 1 (D-01/D-02) | Внешних запросов 0; файл кончается разделом 7 на строке 1149 |
| `imghdr` (stdlib) для типа изображения | Удалён в Python 3.13 | CPython 3.13 | Для CR-02 не вариант — своя проверка сигнатур |

**Deprecated/outdated:**

- `TemplateResponse(name, {"request": request})` — Starlette просит `TemplateResponse(request, name)`. Предупреждение сыплется на каждом рендере (272 warnings за прогон). Массовая правка вне границы фазы, но **новые** шаблонные ответы стоит писать в новой форме.
- `Ad.is_active` — исчезает в этой фазе.
- `app/templates/schedules/form.html` — исчезает в этой фазе (D-14).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Порог счётчика длины: 4096 общий, предупреждение от 1024 при наличии вложений | Pitfall 6, Open Questions Q1 | Счётчик врёт пользователю: либо пугает там, где всё в порядке (Premium-аккаунт), либо молчит перед гарантированным `MediaCaptionTooLongError`. UI-SPEC прямо просит решить это ДО вёрстки счётчика |
| A2 | В превью 2…10 вложений — переносящийся ряд миниатюр 120px в порядке отправки | §User Constraints (UI-SPEC assumption 2) | Расхождение с макетом; checker рекомендовал зафиксировать на планировании |
| A3 | Расписания объявлений-черновиков **показываются** в сводном списке с пометкой «Объявление в черновике» | Open Questions Q2 | Отдано на усмотрение CONTEXT.md; UI-SPEC E13 `partial` уже описывает эту пометку, значит дефолт согласован. Если скрывать — пользователь потеряет расписания из виду |
| A4 | Черновики считаются в лимит объявлений так же, как обычные объявления | §User Constraints (discretion) | Практически безрисково: лимита на число объявлений **сегодня не существует** — `tests/test_routes/test_limits.py:4-11` (`test_create_ads_no_limit`) явно закрепляет отсутствие [VERIFIED: tests/test_routes/test_limits.py:4-11] |
| A5 | Разумный порядок «миграция вместе с правкой `schedules.py:131,240`» (вариант A из Pitfall 3) | Pitfall 3 | Если планировщик выберет иной порядок, SC-3 нарушается на промежуточном коммите |
| A6 | Значения статуса — строки `"draft"` и `"published"` | Pattern 1, Code Example 1 | Никакого источника истины в репозитории нет — поле не существует. Любые другие литералы одинаково валидны, но должны быть выбраны один раз и вынесены в `app/constants.py` |
| A7 | Индикатор автосохранения реализуем целиком на CSS `.htmx-request` без Python-состояния | Code Example 3 | Состояние «Не сохранено — проверьте соединение» требует обработки ошибки; чистого CSS может не хватить, понадобится `hx-on::response-error` или `htmx:responseError` |
| A8 | 8 читателей `Ad.is_active` — полный список | Pitfall 2 | Получен grep-ом по `app/` и `tests/`; динамического доступа (`getattr`) в проекте не найдено, но grep его и не найдёт |

## Open Questions

1. **Каким должен быть порог счётчика длины текста?**
   - Что известно: в коде проекта ограничения нет вообще (`Ad.text` — `Text` без длины; адаптеры передают `caption=text` как есть). Telegram: 4096 обычный текст, 1024 подпись к медиа у не-Premium [CITED: MEDIUM confidence].
   - Что неясно: Premium-статус подключённого userbot-аккаунта приложению неизвестен; для WhatsApp и MAX лимиты не исследованы (в коде их тоже нет).
   - Рекомендация: **вынести на подтверждение пользователю до вёрстки счётчика** (checker Фазы UI просит того же). Дефолт: 4096 предел, `--warn` от 1024 при непустом `Ad.images`. Счётчик не блокирует сохранение.

2. **Показывать ли расписания объявлений-черновиков в сводном списке?**
   - Что известно: CONTEXT.md отдал вопрос планировщику; UI-SPEC E13 `partial` уже описывает пометку «Объявление в черновике» и «отправок не будет».
   - Что неясно: ничего — контракты согласованы.
   - Рекомендация: показывать с пометкой (A3). Считать закрытым UI-SPEC-ом.

3. **Что показывать в поле «группы» карточки сводного списка — количество или имена?**
   - Что известно: сегодня показывается `{{ s.group_ids|length }} групп` (`schedule_row.html:51`). `Schedule.group_ids` — JSON-массив id, имён в нём нет; `GroupInfo.member_count` живёт в отдельной таблице по ключу `(messenger_type, external_id)` и используется **только** в админке (`admin/groups_info.html:70`, `admin/group_info_detail.html:53`).
   - Что неясно: SCH-04 требует «с … группами»; UI-SPEC E13 `populated` говорит «groups», не уточняя. Имена потребуют дополнительного запроса на страницу.
   - Рекомендация: имена первых N групп + «и ещё K» — это буквальнее читает SCH-04, чем голое число. Один `select(Group.id, Group.name).where(Group.id.in_(все id со страницы))` закрывает всю страницу.

4. **Нужна ли разовая чистка уже сохранённых чужих/внешних значений в `Ad.images`?**
   - Что известно: WR-01 отсекает их только на записи. Ревью Фазы 1 указывает, что внешние `http(s)`-значения рендерятся `<img src>` в истории и админке (`01-REVIEW.md:311-315`), то есть остаточный риск сохраняется и после фикса.
   - Что неясно: есть ли такие значения в проде.
   - Рекомендация: диагностический запрос (`SELECT id FROM ads WHERE images::text LIKE '%http%'`) в плане как задача-проверка; чистка — только если найдётся.

5. **Сохранять ли `/schedules/new` и `/schedules/{id}/edit` как 301-редиректы вместо полного удаления?**
   - Что известно: D-14 требует удалить целиком, «мёртвого кода не остаётся». Но у пользователей есть открытые вкладки и закладки — ровно та причина, по которой `layout` в query-параметре был оставлен как принимаемый и игнорируемый (`app/pages/ads.py:46-50`).
   - Что неясно: считается ли редирект «мёртвым кодом».
   - Рекомендация: не переоткрывать D-14; отметить как возможный follow-up, если после выката появятся 404 в логах.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | всё | ✓ | 3.12 (`requires-python >=3.12`) | — |
| uv | сборка окружения, `just sync` | ✓ | окружение `.venv` собрано | — |
| pytest / pytest-asyncio / aiosqlite | суита (652 теста) | ✓ | `>=9.0.2` / `>=1.3.0` / `>=0.22.1` | — |
| just | команды проекта | ✓ | `justfile:14` (`test`), `:18` (`test-cov`) | `uv run pytest` напрямую |
| Alembic | миграция `0013` | ✓ | `>=1.18.4` | — |
| PostgreSQL | применение миграции | ✗ (не проверялся локально) | — | Тесты идут на `sqlite+aiosqlite:///:memory:` и миграции **не применяют** — корректность `0013` требует отдельной проверки, см. §Validation Architecture |
| Redis | Celery, очереди wa/max | ✗ (в тестах замокан) | — | Тесты не поднимают Redis; правка D-01 проверяется на уровне доменной функции |
| Docker | воркеры wa/max | ✗ | — | `get_shell_context` намеренно не трогает Docker SDK (`app/pages/common.py:150-155`) — рендер страниц от него не зависит |
| S3 | загрузка вложений | ✗ (замокан) | — | `tests/test_routes/test_uploads.py` патчит `upload_file_to_s3` |
| Pillow | (не нужен) | ✓ транзитивно | 12.1.1 | Не использовать — см. §Don't Hand-Roll |

**Missing dependencies with no fallback:** нет — ни одна задача фазы не требует внешнего сервиса для проверки.

**Missing dependencies with fallback:** PostgreSQL (миграция), Redis, Docker, S3 — все замоканы или обойдены в суите. Единственное следствие: **ревизия `0013` не проверяется автоматически ничем**; план обязан завести для неё явную проверку.

## Validation Architecture

`workflow.nyquist_validation: true` [VERIFIED: .planning/config.json].

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=9.0.2` + pytest-asyncio `>=1.3.0` + aiosqlite `>=0.22.1` |
| Config file | нет отдельного `pytest.ini`/`pyproject [tool.pytest]` — конфигурация только в `tests/conftest.py` |
| Quick run command | `uv run pytest tests/test_pages tests/test_routes/test_ads.py tests/test_templates -q` (~5 с) |
| Full suite command | `just test` → `uv run pytest tests/ -v` (**~12 мин**, 652 теста) |

> Полный прогон занимает 12 мин 21 с. Гонять его на каждый коммит задачи не следует — только на слияние волны и на гейт фазы.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **BASE** | Суита зелёная (28 падений Pitfall 0 закрыты) | integration | `uv run pytest tests/test_routes/test_uploads.py tests/test_routes/test_wa_sync_status.py tests/test_routes/test_tg_user_auth.py tests/test_routes/test_sync_groups.py tests/test_config_s3.py tests/test_e2e.py tests/test_routes/test_groups_bulk.py -q` | ✅ существуют, красные — чинятся фикстуры |
| **BASE** | `/ads/new` и `/ads/{id}/edit` рендерятся тестом (D-21) | integration | `uv run pytest tests/test_pages/test_ads_editor.py -q` | ❌ Wave 0 |
| **BASE** | Ревизия `0013` применяется и откатывается | integration | `uv run pytest tests/test_migrations/test_0013_ad_status.py -q` | ❌ Wave 0 |
| ADS-04 | Черновик создаётся первым автосохранением, запись при `GET /ads/new` не появляется (D-03) | integration | `pytest tests/test_pages/test_ads_editor.py::test_get_new_creates_no_row -x` | ❌ Wave 0 |
| ADS-04 | Автосохранение возвращает OOB-фрагменты и `HX-Push-Url`, форма не в ответе (D-05/D-06) | integration | `pytest tests/test_pages/test_ads_editor.py::test_autosave_returns_oob -x` | ❌ Wave 0 |
| ADS-04 | Черновик отличается в списке: `badge('Черновик','warning')` | integration | `pytest tests/test_pages/test_ads_editor.py::test_ad_list_status_badge -x` | ❌ Wave 0 |
| ADS-04 | **Черновик не отправляется** (D-01): `collect_due_schedules` не возвращает задач для draft-объявления и **сдвигает** `next_run_at` | unit | `pytest tests/test_application/test_collect_due_draft.py -x` | ❌ Wave 0 |
| ADS-04 | Сохранение работает без JS: обычный POST → 302 | integration | `pytest tests/test_pages/test_ads_editor.py::test_save_without_js -x` | ❌ Wave 0 |
| ADS-05 | Несколько вложений сохраняются в порядке загрузки; удаление убирает ключ из `Ad.images` | integration | `pytest tests/test_routes/test_ads.py -k image -x` | ✅ частично (`test_create_ad_with_multiple_image_fields`) — расширить |
| ADS-05 | Чужой ключ отклоняется (WR-01) | integration | `pytest tests/test_pages/test_ads_image_ownership.py -x` | ❌ Wave 0 — **и переписать `tests/test_routes/test_ads.py:169-185`**, который сегодня закрепляет обратное |
| ADS-05 | Сервер отклоняет > `max_images_per_ad` вложений (D-13) | integration | `pytest tests/test_pages/test_ads_image_ownership.py::test_over_limit_rejected -x` | ❌ Wave 0 |
| ADS-05 | Загрузка не-изображения с подделанным `Content-Type` отклоняется (CR-02) | integration | `pytest tests/test_routes/test_uploads.py::test_rejects_spoofed_content_type -x` | ❌ Wave 0 |
| ADS-06 | Превью содержит текст и все ключи из БД, а не из формы | integration | `pytest tests/test_pages/test_ads_editor.py::test_preview_reflects_db -x` | ❌ Wave 0 |
| ADS-07 | Расписание создаётся/меняется из редактора, пользователь остаётся в редакторе | integration | `pytest tests/test_pages/test_editor_schedules.py -x` | ❌ Wave 0 |
| ADS-07 | Неполное расписание сохраняется с `is_active=false` (D-08) | integration | `pytest tests/test_pages/test_editor_schedules.py::test_incomplete_saved_disabled -x` | ❌ Wave 0 |
| ADS-07 | Чужой `ad_id`/`account_id` отклоняется на обоих входах (CR-01/D-20) | integration | `pytest tests/test_pages/test_schedule_ownership.py tests/test_routes/test_schedules.py -k ownership -x` | ❌ Wave 0 |
| ADS-08 | Удаление расписания из редактора | integration | `pytest tests/test_pages/test_editor_schedules.py::test_delete_from_editor -x` | ❌ Wave 0 |
| ADS-08 | Путь удаления жив без Alpine (форма POST в разметке) | integration | `pytest tests/test_pages/test_editor_schedules.py::test_delete_degrades_without_alpine -x` | ❌ Wave 0 |
| SCH-04 | Карточка показывает объявление, канал, группы, дни, времена | integration | `pytest tests/test_pages/test_responsive_markup.py::test_schedules_card_renders_data -x` | ✅ существует — **переписать** (строка 276 ждёт `/schedules/{id}/edit`) |
| SCH-04 | Пустое состояние ведёт на `/ads`, не на `/schedules/new` | integration | `pytest tests/test_pages/test_schedules_list.py::test_empty_state_points_to_ads -x` | ❌ Wave 0 |
| SCH-05 | Тумблер из списка меняет `is_active`; чужое расписание не трогается | integration | `pytest tests/test_pages/test_responsive_markup.py::test_schedules_toggle_route_unchanged -x` | ✅ существует, менять не нужно |
| SC-3 (no-gap) | В каждом коммите фазы существует хотя бы один рабочий путь создания расписания | integration | `pytest tests/test_pages/test_schedule_creation_path_exists.py -x` | ❌ Wave 0 — страховочная сетка на всю фазу |
| SC-5 | Адаптивность: редактор — одна колонка ≤900px, список — карточки на всех ширинах | integration | `pytest tests/test_pages/test_responsive_markup.py -k "editor or sched" -x` | ❌ Wave 0 (дописать в существующий файл) |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_pages tests/test_routes/test_ads.py tests/test_routes/test_schedules.py tests/test_templates tests/test_application -q` (~10 с)
- **Per wave merge:** `just test` — полный прогон (12 мин), сравнение с зафиксированным базовым числом
- **Phase gate:** полная суита зелёная перед `/gsd-verify-work`. **Базовое число после первого плана — 652 passed, 0 failed.** До первого плана база — 624 passed / 25 failed / 3 errors, и это надо записать в план как исходную точку, иначе «стало не хуже» нечем измерить.

### Wave 0 Gaps

- [ ] `tests/conftest.py` и 10 модульных фикстур — `_env_file=None` (закрывает 25 failed + 3 errors)
- [ ] `tests/test_pages/test_ads_editor.py` — первый рендер-тест редактора (D-21); покрывает ADS-04, ADS-06
- [ ] `tests/test_migrations/test_0013_ad_status.py` — единственная проверка ревизии: суита миграции не применяет
- [ ] `tests/test_application/test_collect_due_draft.py` — D-01, самая чувствительная правка фазы
- [ ] `tests/test_pages/test_ads_image_ownership.py` — WR-01 + D-13
- [ ] `tests/test_routes/test_uploads.py` — добавить тест подделанного `Content-Type` (CR-02)
- [ ] `tests/test_pages/test_schedule_ownership.py` — CR-01/D-20, оба входа
- [ ] `tests/test_pages/test_editor_schedules.py` — ADS-07/ADS-08
- [ ] `tests/test_pages/test_schedules_list.py` — SCH-04
- [ ] `tests/test_pages/test_schedule_creation_path_exists.py` — страховочная сетка SC-3
- [ ] **Переписать** тесты, ссылающиеся на удаляемые маршруты: `test_responsive_markup.py:276`, `test_schedules_detached_account.py:96`, `test_schedules_toggle_detached.py:171`, `test_schedules_profile_timezone.py:28`, `test_shell.py:85`
- [ ] **Переписать** `tests/test_routes/test_ads.py:169-185` — сегодня закрепляет приём чужих ключей изображений
- [ ] **Переписать** `tests/test_models/test_ad.py:33,58` — `assert ad.is_active is True`
- [ ] Решить судьбу `tests/test_templates/test_ads_form_security.py` (6 тестов на исходник шаблона) — см. Pitfall 10

Framework install: не требуется.

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: high` [VERIFIED: .planning/config.json].

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Фаза не трогает вход, регистрацию и восстановление пароля |
| V3 Session Management | no | JWT в httpOnly-cookie, `get_user_from_cookie` не меняется |
| **V4 Access Control** | **yes** | Владение объектом проверяется в обработчике: `ad_id` **и** `account_id` (CR-01/D-20), ключ изображения по префиксу `{user_id}/` (WR-01). Три находки Фазы 1 — все категории V4 |
| **V5 Input Validation** | **yes** | Число вложений (D-13, `settings.max_images_per_ad`), формат ключа (`_KEY_RE`), формат времени `HH:MM` (Pitfall 9), допустимые значения `status` (`Literal["draft","published"]`), таймзона уже через `VALID_TIMEZONES` |
| V6 Cryptography | no | Новых секретов и подписей фаза не вводит |
| **V12 File Upload** | **yes** | Тип определяется по содержимому, а не по клиентскому `Content-Type` (CR-02); имя нормализуется (`safe_filename`, уже есть); размер ограничен (`max_image_size_mb`, уже есть) |
| **V5.3 Output Encoding** | **yes** | Jinja-автоэкранирование + запрет `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` (0 по проекту, проверяется тестом исходника); `{{ ... | tojson }}` в JS-контексте (`01-REVIEW.md:626`) |

### Known Threat Patterns for FastAPI + Jinja2 + S3

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR по `ad_id` / `account_id` при постановке в расписание — чужое объявление рассылается, `SendLog` пишется с `user_id` жертвы, счёт выставляется жертве (**CR-01, critical**) | Elevation of Privilege / Tampering | Фильтр по владельцу в самом запросе + отказ, а не молчаливое сохранение. Оба входа: `app/pages/schedules.py:204-213,314-315` и `app/routes/schedules.py:67-73` |
| Загрузка `image/svg+xml` под видом картинки, исполнение скрипта на origin хранилища (**CR-02, critical**) | Tampering / Information Disclosure | Проверка первых байтов на 4 разрешённые сигнатуры; SVG в список не входит |
| Подстановка чужого или внешнего значения в `Ad.images` — утечка IP/User-Agent просматривающего админа, отправка чужого контента (**WR-01 / T-10-04, high**) | Information Disclosure / Spoofing | `_KEY_RE` + проверка префикса `{user_id}/` на всех четырёх входах |
| Обход клиентского лимита в 10 вложений прямым POST | Denial of Service | Серверная проверка `len(images) <= settings.max_images_per_ad` (D-13) |
| Хранимый XSS через имя загруженного файла в редакторе | Tampering | Уже закрыт Фазой 1: `safe_filename` + сборка DOM-узлами; **не сломать при переписывании `form.html`** (Pitfall 10) |
| Обход контроля состояния через JSON-API: запись произвольной строки в `Ad.status` | Tampering | `Literal["draft","published"]` в `UpdateAdRequest`; рендер уже деградирует безопасно (UI-SPEC E15: неизвестный статус → «Черновик») |
| Утечка боевых настроек в тестовое окружение (`.env` → `Settings`) | Information Disclosure | `_env_file=None` в тестовых фикстурах. Сегодня тесты запускаются с реальными SMTP-параметрами разработчика |
| Залп пропущенных отправок при публикации черновика | Denial of Service (для групп — спам) | Пропуск через ветку со сдвигом `next_run_at`, а не через `WHERE` (Pitfall 5) |

### Открытый гейт код-ревью

`01-REVIEW.md` — `status: issues_found`, `critical: 2`. CR-01, CR-02 и WR-01/T-10-04 закрываются в этой фазе (D-19, решение UAT 2026-08-10). Пока они открыты, `security_block_on: high` будет держать фазу — значит первый план обязан их закрыть, а не только «начать».

## Project Constraints (from CLAUDE.md)

Из `./CLAUDE.md` и `./.claude/CLAUDE.md`:

| Directive | Как влияет на план |
|-----------|--------------------|
| Стек: Python 3.12, uv, FastAPI + SQLAlchemy async (PostgreSQL) + Celery/Redis + Jinja2 | Никаких новых слоёв; SPA исключён |
| Команды через `just` | `just test`, `just migrate "description"`, `just upgrade`, `just add <package>` — план ссылается на рецепты, а не на голые команды |
| Слои: `app/routes/` (JSON-API), `app/pages/` (HTML), `app/models/`, `app/repositories/`, `app/services/`, `app/templates/` | Новый код кладётся по слоям; доменная правка D-01 — в `app/application/scheduling/` |
| Тесты: `sqlite+aiosqlite:///:memory:`, полная схема на тест, фикстуры `client`/`db_session`/`auth_headers` в `tests/conftest.py` | Новые тесты используют существующие фикстуры (плюс `authed_client`/`admin_client`) |
| **graphify:** для вопросов по кодовой базе сначала `graphify query "..."`; после правок — `graphify update .` | Планы, затрагивающие код, должны включать `graphify update .` в конце фазы (граф уже помечен как устаревший) |
| `graphify-out/` — источник навигации, `GRAPH_REPORT.md` только для широкого обзора | Соблюдено в этом исследовании |

## Sources

### Primary (HIGH confidence)

- **Кодовая база** (прочитана в этой сессии): `app/models/ad.py`, `app/models/schedule.py`, `app/models/group.py`, `app/models/group_info.py`, `app/pages/ads.py`, `app/pages/schedules.py`, `app/pages/common.py`, `app/pages/dashboard.py`, `app/pages/groups.py`, `app/routes/ads.py`, `app/routes/schedules.py`, `app/routes/uploads.py`, `app/application/scheduling/use_cases.py`, `app/worker/tasks.py`, `app/worker/celery_app.py`, `app/services/schedule_service.py`, `app/config.py`, `app/dependencies.py`, `app/messengers/{telegram_user,whatsapp,max}.py`, `app/templates/{base,ads/form,ads/list,ads/partial_cards,ads/includes/ad_card,schedules/list,schedules/partial_cards,schedules/form,schedules/includes/schedule_row}.html`, `app/templates/components/*.html`, `app/static/css/app.css`, `alembic/versions/{0003,0012}*.py`, `alembic/env.py`, `pyproject.toml`, `justfile`
- **Прогоны в этой сессии:** `pytest --collect-only` (652), `pytest tests/ -q` (25 failed / 624 passed / 3 errors / 12:21), точечные прогоны `test_uploads.py`, `test_wa_sync_status.py`, проба рендера `/ads/new` (200), воспроизведение `Settings()` `ValidationError` без `.env`, проверка `Settings(_env_file=None, ...)`
- **Context7 `/bigskysoftware/htmx`** — `hx-trigger` (`changed`, `delay:`), `htmx-request`, `hx-sync`, `hx-swap-oob`
- **Context7 `/sqlalchemy/alembic`** — `batch_alter_table`, add/drop column в одной ревизии
- **Артефакты планирования:** `02-CONTEXT.md`, `02-UI-SPEC.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `01-REVIEW.md`, `01-SECURITY.md`, `.planning/config.json`
- **graphify:** `graphify query "ad editor page routes ads.py create update"`, `"uploads image S3 service ad images storage"`, `"schedules pages list toggle new edit form"` — навели на `collect_due_schedules` до чтения файлов

### Secondary (MEDIUM confidence)

- WebSearch: лимиты Telegram — 4096 символов текст / 1024 подпись к медиа (не-Premium), 4096 подпись у Premium. Несколько независимых источников сходятся; официальной страницей Telegram не подтверждено в этой сессии

### Tertiary (LOW confidence)

- Отсутствуют. Всё, что не подтверждено кодом или документацией, вынесено в §Assumptions Log.

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — новых пакетов нет, версии прочитаны из `pyproject.toml` и подтверждены рабочим окружением
- Architecture: **HIGH** — каждый паттерн привязан к прочитанному файлу и строке; htmx-механизмы подтверждены Context7
- Pitfalls: **HIGH** — Pitfall 0, 1 и точки CR-01/WR-01 воспроизведены прогонами в этой сессии, а не выведены из чтения
- Порог длины текста (Pitfall 6 / A1): **MEDIUM** — внешний факт без официального первоисточника; в коде ограничения нет вовсе (это проверено, HIGH)
- Значения `status`, раскладка превью, судьба тестов на исходник шаблона: **LOW** — источника истины не существует, см. §Assumptions Log и §Open Questions

**Research date:** 2026-08-10
**Valid until:** 2026-09-09 (30 дней — стек стабилен). Раньше — если изменится `.env`/CI-окружение: половина находок §Common Pitfalls 0–1 зависит от наличия `.env` в рабочем каталоге.
