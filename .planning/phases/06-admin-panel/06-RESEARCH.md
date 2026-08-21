# Phase 6: Админ-панель — Research

**Researched:** 2026-08-21
**Domain:** Server-rendered admin console поверх FastAPI + Jinja2 + HTMX; чтение операционного состояния из Redis, Loki и PostgreSQL; JWT-имперсонация и три свёрнутых долга безопасности.
**Confidence:** HIGH (по внутрипроектным фактам — читаны исходники), MEDIUM (по внешним контрактам Loki/kombu — Context7), LOW (по внешним практикам имперсонации — WebSearch)

---

## Summary

Фаза 6 почти не нуждается в новых технологиях: **ни одной новой зависимости ставить не нужно** — `httpx`, `redis`, `docker`, `structlog`, `jinja2`, `htmx`/`alpine` уже в проекте, и все шесть подразделов собираются из уже отгруженных приёмов Фаз 1–05.1. Настоящая работа фазы — не «выбрать библиотеку», а **не соврать на экране**: подразделы «Воркеры», «Очередь» и «Логи» читают состояние из источников, устройство которых в двух каналах (WA и MAX) **несимметрично**, и наивное чтение даёт правдоподобно выглядящую ложь.

Исследование вскрыло **шесть фактов, каждый из которых меняет план**, и они собраны в §«Вскрытые факты исследования» ниже. Самый дорогой — **Ф-4: решение D-30 («`get_current_user_id` перестаёт пускать по уже выданной cookie») в лоб роняет уже зелёный тест** `test_the_api_authentication_dependency_is_left_untouched`, который читает исходник по AST и явно запрещает параметр `db` у этой зависимости. Планировщик обязан выбрать форму починки CR-01 сознательно, а не обнаружить конфликт на прогоне. Следом идут: у `wa:heartbeat` **нет TTL**, а у `max:heartbeat` он есть (значит «жив» = сравнение возраста, а не `EXISTS`); `_delay_until` у WA хранится в **миллисекундах**, у MAX — в **секундах**; метка `level` в Loki несёт **два разных словаря** (`warning` у Python-контейнеров, `warn` у wa-worker); nginx **сам выбирает HTTP-only шаблон** при отсутствии сертификата, поэтому безусловный `secure=True` на cookie ломает вход; и `collect_due_schedules` живёт **не там**, где его называет CONTEXT.md.

**Primary recommendation:** новых пакетов не ставить; шесть подразделов сделать шестью маршрутами в `app/pages/admin.py` по образцу `app/pages/history.py`; операционное чтение (Redis, Loki) вынести в два новых сервиса `app/services/` с деградацией по таймауту и подменяемых `unittest.mock.patch` в суите; **числа-пороги брать из уже существующих объявлений проекта** (`MAX_HEARTBEAT_STALE_SEC = 90`, `PAYMENT_LIST_CAP = 200`), а не изобретать новые; починку CR-01 делать **соседней зависимостью** по форме `get_current_user_id_with_access`, а не правкой `get_current_user_id`.

---

## User Constraints (from CONTEXT.md)

> ⚠️ **`06-CONTEXT.md` — авторитетный источник. Планировщик обязан прочитать его целиком.** Ниже — индекс решений для сверки покрытия, а не пересказ.

### Locked Decisions (D-01 … D-50)

**Каркас (D-01…D-05):** D-01 шесть настоящих маршрутов `/admin`, `/admin/users`, `/admin/workers`, `/admin/queue`, `/admin/logs`, `/admin/payments`, подсветка через `active_page` · D-02 HTMX только внутри подраздела · D-03 карточка пользователя остаётся отдельной страницей `/admin/users/{id}` · D-04 `/admin/users/{id}/history` остаётся · D-05 `/admin/groups-info` и `/admin/groups-info/{id}` сносятся; **обязательное следствие — частичный вердикт по ADMIN-02 в `REQUIREMENTS.md` отдельной задачей** (reversibility: costly).

**Воркеры (D-06…D-12):** D-06 две независимые колонки «Сессия» (`MessengerAccount.status`) и «Воркер» (heartbeat из Redis) · D-07 **Docker SDK при рендере не вызывается** · D-08 отсутствие heartbeat = «простаивает», «офлайн» честен только при `LLEN > 0` **и** мёртвом heartbeat · D-09 два блока: инфраструктура (`celery-beat`, `celery-worker-telegram`, `celery-worker-default`) и воркеры аккаунтов по каналам · D-10 «живой лог» в строке не делается, строка ведёт в «Логи» с фильтром · D-11 действие только «Перезапустить», через панель подтверждения, **и это единственное место вызова Docker SDK** · D-12 HTMX-опрос 15–30 с без автостопа.

**Очередь (D-13…D-18):** D-13 источник — Redis напрямую (`LRANGE` по `wa:queue:{id}`/`max:queue:{id}`, `LLEN` по Celery-очереди `telegram`); Flower не переиспользуется · D-14 для Telegram только число и лаг, построчный список — WA/MAX · D-15 статуса «в работе» нет · D-16 состояния «ждёт» / «отложена до T» (`_delay_until`) / «ретрай N» (`_retry_count`) · D-17 действие — снять конкретную задачу (`LREM`); «Очистить очередь» не даётся · D-18 снятие не пишет `SendLog`.

**Имперсонация (D-19…D-26):** D-19 claim `act` в том же JWT (reversibility: costly) · D-20 `check_is_admin` при наличии `act` определяет админство по `act` · D-21 отсутствие `act` ведёт себя ровно как сегодня, закреплено тестом · D-22 под чужой учётной записью запрещено необратимое и денежное · D-23 запрет — зависимостью на маршруте плюс **машинный гейт, читающий исходник** · D-24 след — строкой structlog `impersonation_start`/`impersonation_stop`; таблица аудита не заводится · D-25 отдельный короткий `exp` = 60 минут; полоса возврата поднимается в `base.html` · D-26 вход под заблокированным разрешён явным решением.

**Логи (D-27…D-29):** D-27 источник — Loki HTTP API `/loki/api/v1/query_range` · D-28 мониторинг не делается жёсткой зависимостью прода; при недоступном Loki — честная плашка с `just monitoring-start` · D-29 фильтры: уровень и источник — в селектор LogQL, поиск — в `|=`; окно 15 мин / 1 ч / 24 ч, по умолчанию 1 ч; потолок 200 с честной подписью; обновление кнопкой, без опроса.

**Пользователи и блокировка (D-30…D-36):** D-30 блокировка действует на трёх путях: `login_submit`, `get_current_user_id`, `collect_due_schedules` (reversibility: costly) · D-31 кэш вердикта блокировки не заводится · D-32 две группы чипсов — «Доступ» и «Состояние» · D-33 пагинация страницами по 50 с точным `COUNT` · D-34 **поиск, фильтры, пагинация и счётчик — одним выражением** · D-35 колонки: имя/email, доступ, состояние, аккаунтов, регистрация · D-36 ручного продления доступа нет.

**Обзор и Платежи (D-37…D-42):** D-37 четыре плитки: «Пользователей», «Платящих» (+MRR), «Задач в очереди», «Ошибок за сутки» · D-38 «Платящих» без льготных · D-39 **общесистемный вход добавляется В МОДУЛЬ АНАЛИТИКИ**, не в админку · D-40 окно ошибок — сутки · D-41 «Платежи» — MRR и журнал; ARPU и churn выбрасываются, вместо churn — «истекло и не продлено за 30 дней» · D-42 `Payment.plan` в журнале не показывается; проверить греп-гейт.

**Инциденты (D-43…D-48):** D-43 инцидент есть СОСТОЯНИЕ, из БД и Redis; ни таблицы, ни логов · D-44 у каждого признака условие снятия, ручного «закрыть» нет · D-45 признаков пять (воркер не забирает работу; аккаунт отвалился; всплеск отказов; платежи залипли; планировщик не дышит) · D-46 зелёные «восстановлен» не делаются · D-47 время инцидента от последнего СЛЕДА; `status_changed_at` не заводится · D-48 место — блок на «Обзоре», каждая строка — ссылка «куда чинить».

**Безопасность (D-49, D-50):** D-49 все три BLOCKER-долга ревизии 05.1 входят в предмет фазы · D-50 CR-03 (`secure` на cookie) исполняется в порядке: сперва убедиться, что HTTPS жив на всех входах, потом флаг, плюс HSTS в шаблон nginx (reversibility: costly).

### Claude's Discretion (verbatim)

- Числа-пороги: частота опроса воркеров в пределах 15–30 с, порог «всплеска отказов» и его окно, сколько часов делают платёж «залипшим», сколько минут просрочки `next_run_at` означают вставший планировщик, размер страницы пользователей в окрестности 50, потолок логов в окрестности 200.
- Формулировки подписей: «простаивает» / «офлайн» / «в пуле app», текст плашки недоступного Loki, текст строк инцидентов.
- Имена макросов и файлов новых компонентов (строка воркера, строка очереди, строка лога, строка инцидента, вкладки подразделов).
- Форма вкладок на узких ширинах: горизонтальная прокрутка, перенос или выпадающий список. Адаптивность на 375px — критерий приёмки фазы.
- Как проверять Loki, Docker и Redis в суите на SQLite in-memory: подмена клиента, фикстура-двойник или пропуск с явной отметкой. Вопрос к исследователю и планировщику.
- Точная форма расширения `send_metrics` под общесистемный счёт (D-39): необязательный `user_id` либо отдельная функция рядом — важно, что внутри модуля.
- Судьба JSON-роутов админки, если такие обнаружатся мёртвыми, — по образцу решения Фазы 3 (D-14).

### Deferred Ideas (OUT OF SCOPE — verbatim)

- **Автоповтор отправки Telegram** (Ф-1) — докстринг обещает то, чего в коде нет. Отдельный todo; правка боевого пути отправки, не интерфейс.
- **Ручное продление доступа администратором** (D-36) — третий способ управлять сроком рядом с оплатой и льготой; требует ответов про MRR, последующую оплату и взаимодействие с `convert-remainder`. Фаза биллинга.
- **Производитель для `GroupInfo`** (Ф-2, D-05) — писать справочник при синхронизации групп. Новая возможность, а не интерфейс.
- **Таблица событий / аудита** — отклонена в третий раз (Фаза 4 D-05; здесь — инциденты D-43 и след имперсонации D-24). Возвращаться отдельной фазой, если понадобится история состояний, а не их текущий срез.
- **Второй администратор** — `require_admin` держится на совпадении с `settings.admin_email`, колонки `is_admin` нет. Имперсонация с этой моделью живёт, второй администратор в неё не помещается. Новая возможность.
- **Кэш вердикта блокировки** (D-31) — `billing_cache` готов; возвращаться только после измерения.
- **Мониторинг как жёсткая зависимость прода** (D-28) — отвергнуто; вернуться, если плашка «логи недоступны» станет постоянным состоянием.
- **«Очистить очередь целиком»** (D-17) — возвращаться, если появится сценарий, где снятие по одной перестанет справляться.
- **«Остановить воркер»** (D-11) — возвращаться, если найдётся отказ, который перезапуск не лечит.

---

## Phase Requirements

| ID | Описание | Research Support |
|----|----------|------------------|
| **ADMIN-03** | Администратор видит подраздел «Обзор» с ключевыми показателями сервиса | `send_metrics` (`send_analytics.py:138`) отдаёт восемь чисел одним round-trip, включая предыдущее окно → дельта D-37 бесплатна; расширение общесистемным входом — §Pattern 5. `User.created_at` есть (`models/user.py:18-20`). MRR = число платящих × `settings.subscription_price = "3000.00"` (`config.py:77`) |
| **ADMIN-04** | Подраздел «Пользователи» с поиском и фильтрами | `_active_subscriptions_by_user` (`admin.py:47`) + `_access_view` (`admin.py:85`) уже дают ось «Доступ» одним запросом; форма «фильтры+счётчик одним выражением» — `apply_history_filters`/`history_count` (`send_analytics.py:764,797`); `clean_choice` (`history.py:103`) — санация значений; чипсы — `history/includes/filter_chips.html:52` (⚠️ Ф-15) |
| **ADMIN-05** | Заблокировать и разблокировать пользователя | Тумблер уже есть (`admin.py:589`), эффекта нет. Три точки починки: `login_submit` (`auth.py:40-57`), `get_current_user_id` (`dependencies.py:26-41`, ⚠️ **Ф-4**), `collect_due_schedules` (`app/application/scheduling/use_cases.py:129`, ⚠️ **Ф-5**). Страничный путь уже закрыт: `get_user_from_cookie` (`common.py:315-327`) |
| **ADMIN-06** | Войти под пользователем и вернуться | `create_access_token`/`decode_access_token` (`auth_service.py:17,23`) — единственная точка; `check_is_admin` (`common.py:331`); форма `act` — §Pattern 3 и ⚠️ Ф-17. Гейт запретов — образец `tests/test_pages/test_access_gate.py` |
| **ADMIN-07** | Подраздел «Воркеры» с состоянием контейнеров по каналам | Ключи `wa:heartbeat:{id}`/`max:heartbeat:{id}` — §Redis Key Inventory; готовый предикат свежести `_has_fresh_heartbeat` + `MAX_HEARTBEAT_STALE_SEC = 90` (`max_container_manager.py:20,156-164`) — **переиспользовать, а не изобретать 60**. ⚠️ Ф-6 (асимметрия TTL). Действие «Перезапустить» — `start_container`/`stop_container` (`wa_container_manager.py:30,85`) |
| **ADMIN-08** | Подраздел «Очередь» с состоянием очереди по каналам | Форма payload — `dispatch_send_tasks` (`tasks.py:52-180`), одиннадцать полей; `_retry_count`/`_delay_until` дописывают воркеры при ретрае (`wa_worker/index.js:571-583`, `max_worker/main.py:712-720`) — ⚠️ **Ф-7 (единицы времени разные)**. TG: `LLEN telegram`, ⚠️ Ф-13 (kombu priority sub-keys) |
| **ADMIN-09** | Подраздел «Логи» приложения и воркеров | Loki `query_range` — §Code Example 4; метки `container_name`, `level`, `broadcaster_role`, `account_id` (`monitoring/promtail.yml:16-70`); `auth_enabled: false` и `retention_period: 168h` (`monitoring/loki.yml:1,31`) — тенант-заголовок не нужен, окна ≤24 ч укладываются. ⚠️ **Ф-8 (два словаря `level`)**, ⚠️ Ф-16 |
| **ADMIN-10** | Подраздел «Платежи» со сводкой платёжных операций | `Payment` (`models/payment.py`): `status`, `amount_value`, `kind`, `plan`, `created_at`, `confirmed_at`; статусы `pending`/`succeeded`/`canceled` и `TERMINAL_STATUSES` (`payment_service.py:30-38`). `PAYMENT_LIST_CAP = 200` (`constants.py:69`) **уже назван как значение для этого подраздела**. ⚠️ Ф-10 (греп-гейт `plan` не ловит) |
| **ADMIN-11** | Инциденты сервиса | Все пять признаков D-45 покрыты полями, которые существуют: `LLEN`+heartbeat, `MessengerAccount.status`, `SendLog.status` ∈ `FAILED_STATUSES` (`send_analytics.py:65-69`), `Payment.status = pending` + `created_at`, `Schedule.next_run_at`. ⚠️ Ф-14 (`normalize_utc` обязателен) |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Навигация по шести подразделам | Frontend Server (Jinja2 + маршруты) | — | D-01: базовый путь без JS обязан работать; вкладки = ссылки, а не состояние |
| Плитки «Обзора» и дельты | Application (модуль аналитики) | Database | D-39: агрегации живут только в `app/application/analytics/`, админка их зовёт |
| Живость воркеров | Database + Cache (Redis) | — | D-07: Docker SDK при рендере не зовётся; heartbeat отвечает на «работает», `container.status` — только на «процесс не умер» |
| Перезапуск воркера | API/Backend (Docker SDK) | — | D-11: единственный вызов Docker SDK, по кнопке, а не при рендере |
| Состояние очереди | Cache (Redis) | — | D-13: `LRANGE`/`LLEN`; Flower — внешний инструмент |
| Логи | External service (Loki HTTP) | — | D-27: Promtail уже увёз логи мёртвых контейнеров, которых Docker SDK не отдаст |
| Инциденты | Database + Cache | — | D-43: состояние выводится на лету; Loki опционален, инциденты обязаны работать всегда |
| Личность и `act` | API/Backend (`auth_service` + `dependencies`) | — | D-19: одна точка выпуска/чтения токена на весь проект |
| Блокировка | API/Backend (зависимости) + Application (планировщик) | — | D-30: три пути; страничный уже закрыт |
| HSTS и `secure` | CDN/Proxy (nginx) + Backend (cookie) | — | D-50: порядок несущий, ⚠️ Ф-9 |
| Адаптивность 375px | Frontend Server (компоненты) | — | UI-06; критерий приёмки фазы |

---

## Вскрытые факты исследования

> Шесть утверждений, установленных **чтением исходников в этой сессии**. Их нет ни в CONTEXT.md, ни в одном другом документе проекта. Каждое меняет план.

### ⚠️ Ф-4 (BLOCKER для D-30): починка `get_current_user_id` в лоб роняет зелёный тест

`tests/test_pages/test_access_gate.py:291` — `test_the_api_authentication_dependency_is_left_untouched` — читает `app/dependencies.py` по AST и утверждает буквально:

```python
    parameters = {argument.arg for argument in authenticator.args.args}
    assert "db" not in parameters, (
        "зависимость аутентификации получила сессию БД — она обслуживает и "
        "незащищённые пути, и цена запроса на них ничем не оправдана"
    )
```
[VERIFIED: tests/test_pages/test_access_gate.py:291-318]

D-30 требует, чтобы `get_current_user_id` «перестала пускать по уже выданной cookie», то есть читала `User.is_blocked` из базы, то есть получила `db`. **Это прямое противоречие.** Сегодняшняя подпись — `get_current_user_id(request, credentials, settings) -> int`, и в теле нет ни одного обращения к базе (`app/dependencies.py:26-41`).

**Готовая форма обхода в самом проекте:** `get_current_user_id_with_access` (`app/dependencies.py:95-134`) — **соседняя** зависимость, которая зовёт `get_current_user_id` и добавляет свою проверку с `db`, а вешается **пер-роутерно** в `app/main.py`. Её докстринг прямо объясняет, почему проверку не положили внутрь аутентификатора. Рекомендация в §Pattern 2.

### ⚠️ Ф-5: `collect_due_schedules` живёт не там, где его называет CONTEXT.md

CONTEXT.md (§Integration Points) указывает `app/worker/tasks.py collect_due_schedules`. Фактически:

```
app/application/scheduling/use_cases.py:129: async def collect_due_schedules(
```
[VERIFIED: app/application/scheduling/use_cases.py:129-134]

В `app/worker/tasks.py` есть `check_schedules_async` (:188) и задача `check_schedules` (:271), которые его зовут. Сигнатура — `(session, *, now=None, check_limit)`, где `check_limit` — это `check_access_cached` с контрактом `(db, user_id, action) -> tuple[bool, str]` (`app/services/billing_cache.py:46-48`). Внутри цикла уже есть `checked_users: dict[int, tuple[bool, str]]` — мемоизация вердикта на пользователя. Блокировка ложится **ровно туда же**, соседним условием, и не требует ни нового обхода, ни второго запроса на расписание.

### ⚠️ Ф-6: heartbeat WA и MAX несимметричны — у WA нет TTL

| | wa-worker | max-worker |
|---|---|---|
| Ключ | `wa:heartbeat:{ACCOUNT_ID}` [VERIFIED: wa_worker/index.js:41] | `max:heartbeat:{ACCOUNT_ID}` [VERIFIED: max_worker/main.py:78] |
| Значение | `Date.now().toString()` — **миллисекунды** [VERIFIED: wa_worker/index.js:965, 970, 632] | `str(int(time.time() * 1000))` — **миллисекунды** [VERIFIED: max_worker/main.py:792-798] |
| TTL | **отсутствует** — `redis.set(HEARTBEAT_KEY, ...)` без `EX` | `ex=HEARTBEAT_TTL_SEC`, где `HEARTBEAT_INTERVAL_SEC = 30` и `HEARTBEAT_TTL_SEC = HEARTBEAT_INTERVAL_SEC * 3` [VERIFIED: max_worker/main.py:66-67, 796-798] |
| Удаление | `redis.del(HEARTBEAT_KEY)` только при **graceful** shutdown [VERIFIED: wa_worker/index.js:666] | `await redis_cmd.delete(HEARTBEAT_KEY)` там же [VERIFIED: max_worker/main.py:826] |

**Следствие, которого CONTEXT.md не мог знать:** WA-воркер, убитый не gracefully (OOM, `docker kill`, падение хоста), **оставляет ключ `wa:heartbeat` навсегда**. Значит признак «воркер жив» **не имеет права быть `EXISTS` или `MGET is not None`** — это должно быть **сравнение возраста**, иначе подраздел покажет мёртвый воркер живым бессрочно, и именно в аварии, ради которой его открывают.

**У проекта уже есть объявленный предикат и порог:**
```python
MAX_HEARTBEAT_STALE_SEC = 90
...
def _has_fresh_heartbeat(heartbeat: object) -> bool:
    """Accept only recent worker heartbeat timestamps in milliseconds."""
    try:
        heartbeat_ms = int(heartbeat)
    except (TypeError, ValueError):
        return False

    age_ms = int(time.time() * 1000) - heartbeat_ms
    return 0 <= age_ms <= MAX_HEARTBEAT_STALE_SEC * 1000
```
[VERIFIED: app/services/max_container_manager.py:20, 156-164]

**Рекомендация (в разрешение дискреции «порог ~60 с»):** взять **90 секунд** и переиспользовать этот предикат, подняв его в общее место, а не заводить свои 60. Два разных числа для одного вопроса «жив ли воркер» — ровно тот класс расхождения, который проект закрывает в дюжине мест (`WORKER_ONLINE_STATUS`, `ACCESS_SOON_DAYS`, `TRIAL_DAYS`). Нижняя граница `0 <= age_ms` тоже несущая: heartbeat из будущего (расхождение часов) обязан читаться как несвежий, а не как «только что».

**Второе следствие:** сегодня `wa:heartbeat` **не читается ни одной строкой в `app/`** — `manage_wa_containers` решает по `LLEN` и `container.status` (`app/worker/tasks.py:666-680`), тогда как MAX уже читает heartbeat (`ensure_container_for_pending_work`, `max_container_manager.py:167-187`). Админка станет **первым читателем `wa:heartbeat`** — и первым, кто заметит, если WA-воркер перестанет его писать.

### ⚠️ Ф-7: `_delay_until` у WA — миллисекунды, у MAX — секунды

```javascript
task._delay_until = Date.now() + delaySec * 1000;   // wa_worker/index.js:583
```
[VERIFIED: wa_worker/index.js:571-583]
```python
task["_delay_until"] = time.time() + delay_sec       # max_worker/main.py:719
```
[VERIFIED: max_worker/main.py:712-720]

Оба воркера читают своё же значение своей же меркой и потому работают. Но подраздел «Очередь» читает **оба списка одним кодом** (D-16 «отложена до T»), и единая формула `datetime.fromtimestamp(v)` покажет WA-задачу отложенной **до 55-го тысячелетия**, а `fromtimestamp(v/1000)` покажет MAX-задачу отложенной **до 1970 года**. Ни то, ни другое не падает — оба варианта рисуют правдоподобную дату. Разбор обязан быть по каналу, и это обязано быть закреплено тестом на обоих payload-ах.

Ретрайные значения: WA `RETRY_DELAYS` и `MAX_RETRIES` — см. `wa_worker/index.js`; MAX — `RETRY_DELAYS = [15, 60, 180]`, `MAX_RETRIES = len(RETRY_DELAYS)` [VERIFIED: max_worker/main.py:72-73]. Оба поля (`_retry_count`, `_delay_until`) **отсутствуют в свежепоставленной задаче** — их дописывает только воркер при ретрае, значит читатель обязан работать через `.get(...)` с умолчанием, а не через индекс.

### ⚠️ Ф-8: метка `level` в Loki несёт два разных словаря

Python-контейнеры логируются через `structlog.stdlib.add_log_level` [VERIFIED: app/logging_config.py:14-22], который кладёт в `level` **имя метода логгера в нижнем регистре**: `info`, `warning`, `error`. Promtail поднимает это значение в метку как есть [VERIFIED: monitoring/promtail.yml:34-44].

wa-worker логируется Pino числовыми уровнями, и promtail переводит их шаблоном:
```yaml
                template: '{{ if eq .Value "10" }}trace{{ else if eq .Value "20" }}debug{{ else if eq .Value "30" }}info{{ else if eq .Value "40" }}warn{{ else if eq .Value "50" }}error{{ else if eq .Value "60" }}fatal{{ else }}{{ .Value }}{{ end }}'
```
[VERIFIED: monitoring/promtail.yml:46-59]

То есть **`warning` (Python) и `warn` (wa-worker) — две разные метки одного уровня**. Чипс «WARN» из макета, собранный как `{level="warn"}`, покажет логи wa-worker и **скроет предупреждения приложения и celery** — молча, при статусе 200, с пустым списком, читающимся как «предупреждений нет». max-worker разбирает JSON без шаблона [VERIFIED: monitoring/promtail.yml:61-70], то есть отдаёт то, что напечатал Python-логгер.

**Рекомендация:** селектор уровня строить регулярным матчером — `{level=~"warn|warning"}` — и держать соответствие «чипс → набор значений метки» **одним объявленным словарём** на стороне сервера, по образцу `STATUS_CHIPS`/`_values` из `app/pages/history.py:98-103`. Альтернатива (выровнять promtail) трогает эксплуатационный конфиг и не перепишет уже уехавшие в Loki метки.

### ⚠️ Ф-9: nginx сам выбирает HTTP-only шаблон — безусловный `secure=True` ломает вход

Прод-nginx стартует командой, которая **выбирает шаблон на лету**:
```
        if [ -f /etc/letsencrypt/live/$$DOMAIN/fullchain.pem ]; then
          echo 'SSL certificate found, starting with HTTPS';
          TEMPLATE=/etc/nginx/nginx.conf.template;
        else
          echo 'No SSL certificate, starting HTTP-only mode';
          TEMPLATE=/etc/nginx/nginx-http.conf.template;
        fi;
```
[VERIFIED: docker-compose.prod.yml:43-54]

`nginx-http.conf.template` слушает только `listen 80;` и редиректа на HTTPS не делает [VERIFIED: nginx/nginx-http.conf.template:6-8]. `Strict-Transport-Security` отсутствует в **обоих** шаблонах (грепом по `nginx/` — ноль вхождений).

**Следствие для D-50.** «Убедиться, что HTTPS жив на всех входах» — это не разовая проверка перед выкатом: конфигурация **сама** уходит в HTTP-only, если сертификат не продлился. Флаг `secure`, выставленный литералом, в этот момент отменяет вход в продукт целиком — cookie просто не сохранится, и это будет выглядеть как «пароль не подходит».

**Рекомендация:** `secure` берётся из **настройки** (`Settings.cookie_secure: bool = True`, отдаваемой окружением, как это уже сделано с `yookassa_webhook_client_ip_header`), а не из литерала; обе установки cookie (`app/pages/auth.py:56` и `:341`) читают её из одного места; HSTS добавляется **только** в `nginx/nginx.conf.template` (HTTPS-серверный блок), потому что в HTTP-only шаблоне он был бы обещанием, которое сервер не выполняет. Заодно: у обеих установок cookie сегодня нет `max_age`/`expires`, то есть это session cookie — форма при правке не должна измениться молча.

### ⚠️ Ф-10: `Payment.plan` НЕ подпадает под греп-гейт метрической модели

Прямой ответ на вопрос, поставленный D-42. `FORBIDDEN_NAMES` содержит **одиннадцать** записей, и ни одна не совпадает с голым `plan`:
```python
FORBIDDEN_NAMES = (
    ("plan_limits", ...),
    ("parsed_plan_limits", ...),
    ("parsed_packages", ...),
    ("PLAN_ORDER", ...),
    ("plan_axes(", ...),
    ("deduct_message(", ...),
    ("is_unlimited", ...),
    ("MessageBalance", ...),
    ("BalanceTransaction", ...),
    ("get_or_create_balance(", ...),
    ("get_balance_info(", ...),
)
```
[VERIFIED: tests/test_application/test_no_metering_remains.py:54-79]

Гейт проверяет вхождение подстроки в исходники `app/**/*.py`. Ни `payment.plan`, ни `Payment.plan` его не краснят. Значит **D-42 — решение по существу, а не вынужденное подчинение гейту**, и планировщику не нужно ни обходить гейт, ни расширять его. Формулировать задачу как «не показывать, потому что тарифов нет», а не «не показывать, потому что тест упадёт».

---

## Standard Stack

### Core — всё уже установлено, новых пакетов ноль

| Библиотека | Версия (объявленная) | Назначение в фазе | Почему стандарт |
|-----------|---------------------|-------------------|-----------------|
| `fastapi` | `>=0.129.0` | шесть маршрутов подразделов, зависимости-гейты | стек проекта [VERIFIED: pyproject.toml:17] |
| `jinja2` | `>=3.1.6` | все шаблоны подразделов и макросы | стек проекта [VERIFIED: pyproject.toml:19] |
| `httpx` | `>=0.28.1` | **клиент Loki** — официальный пример Loki написан именно на нём | уже в прямых зависимостях [VERIFIED: pyproject.toml:18]; официальный python-пример Loki использует `httpx.get` [CITED: github.com/grafana/loki/docs/sources/reference/python-client-examples.md] |
| `redis` (через `celery[redis]`) | `celery[redis]>=5.6.2` | `redis.asyncio` для чтения очередей и heartbeat из веб-процесса | уже используется так же в `billing_cache` [VERIFIED: app/services/billing_cache.py:19-21] |
| `docker` | `>=7.1.0` | **только** кнопка «Перезапустить» (D-11) | уже используется `wa_container_manager` [VERIFIED: pyproject.toml:14] |
| `structlog` | `>=24.1.0` | след имперсонации (D-24) | форма следа уже отгружена [VERIFIED: app/pages/admin.py:576-581] |
| `python-jose[cryptography]` | `>=3.5.0` | claim `act` в том же JWT | `create_access_token`/`decode_access_token` [VERIFIED: app/services/auth_service.py:2, 17-29] |
| `sqlalchemy[asyncio]` | `>=2.0.46` | пагинация, счётчики, инциденты | стек проекта [VERIFIED: pyproject.toml:24] |

### Supporting — вендоренные фронтовые ассеты

| Ассет | Назначение | Когда применять |
|-------|-----------|-----------------|
| `app/static/js/htmx.min.js` | опрос «Воркеров» (D-12), пагинация внутри подразделов | внутри подраздела; **не** для смены подраздела (D-01) |
| `app/static/js/alpine.min.js` | панель подтверждения (`components/modal.html`), сворачиваемые фильтры (`components/filters.html`) | подтверждение «Перезапустить» (D-11) и «Снять задачу» (D-17) |

### Alternatives Considered

| Вместо | Можно было | Компромисс | Вердикт |
|--------|-----------|-----------|---------|
| Loki HTTP | `docker logs` через Docker SDK | у мёртвого воркера логов уже нет — `cleanup_exited_containers` его удалил (`wa_container_manager.py:119-131`) | отвергнуто D-27 |
| Loki HTTP | своя таблица логов | отвергнуто Фазой 4 (D-05) и здесь | отвергнуто |
| Redis напрямую | Flower API | знает только Celery (1 канал из 3), поднят без аутентификации (`expose: "5555"`, `docker-compose.prod.yml`) | отвергнуто D-13 |
| `redis.asyncio` | синхронный `redis` как в воркерах | синхронный клиент в async-обработчике блокирует event loop; `billing_cache` уже задал асинхронный прецедент в веб-процессе | **`redis.asyncio`** |
| `fakeredis` | новый dev-пакет | `unittest.mock.patch` уже покрывает и Docker (`tests/test_wa_container_manager.py`), и Redis (`tests/test_billing_cache.py`) — нового пакета не нужно | **`patch`**, §Pattern 7 |
| Новый `act`-claim | вторая cookie / таблица сессий | отвергнуто D-19 с обоснованием | claim `act` |

**Installation:** установок нет. `uv sync` достаточно.

**Version verification:** новых пакетов фаза не добавляет, поэтому запрос к реестру не выполнялся — сверять нечего.

---

## Package Legitimacy Audit

**Фаза не устанавливает ни одного внешнего пакета.** Все восемь используемых библиотек объявлены в `pyproject.toml` до начала фазы и отгружены в проде Фазами 1–05.1.

| Package | Registry | Дисposition |
|---------|----------|-------------|
| — | — | Внешних установок нет; аудит беспредметен |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

⚠️ **Правило для планировщика.** Если план всё же захочет пакет (например, `fakeredis`, `python-logql`, `docker-py`-обёртку), задача обязана нести `checkpoint:human-verify` перед установкой: RESEARCH такого пакета не проверял, и любое имя, пришедшее из тренировочной памяти, тегируется `[ASSUMED]` независимо от того, находится ли оно на PyPI.

---

## Architecture Patterns

### System Architecture Diagram

```
                          БРАУЗЕР АДМИНИСТРАТОРА
                                   │
                    (GET /admin/*  ·  POST действия)
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │              nginx (80/443, авто-выбор шаблона)      │
        └──────────────────────────────┬───────────────────────┘
                                       ▼
        ┌──────────────────────────────────────────────────────┐
        │  FastAPI web  ·  app/pages/__init__.py               │
        │  router(dependencies=[load_shell_context])           │
        │        └─ admin_router  (БЕЗ require_access — T-05.1-17)
        └───┬──────────────────────────────────────────────┬───┘
            │                                              │
   ┌────────▼─────────┐                        ┌───────────▼──────────┐
   │ require_admin     │  читает act, если он  │ base.html + компоненты│
   │ (dependencies.py) │  есть → админство по  │ полоса имперсонации   │
   └────────┬──────────┘  act, а не по sub     └───────────────────────┘
            │
   ┌────────▼──────────────────────────────────────────────────────────┐
   │                 app/pages/admin.py — ШЕСТЬ МАРШРУТОВ              │
   │  /admin  /admin/users  /admin/workers  /admin/queue               │
   │          /admin/logs   /admin/payments                            │
   └──┬────────────┬─────────────┬─────────────┬────────────┬──────────┘
      │            │             │             │            │
      │            │             │             │            │
      ▼            ▼             ▼             ▼            ▼
 ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐
 │analytics│ │  users   │ │  ops-read │ │loki-read │ │  payments   │
 │ модуль  │ │ репо +   │ │  (НОВЫЙ   │ │ (НОВЫЙ   │ │  запросы    │
 │ D-39    │ │_access_  │ │  сервис)  │ │  сервис) │ │             │
 │         │ │  view    │ │           │ │          │ │             │
 └────┬────┘ └────┬─────┘ └──┬─────┬──┘ └────┬─────┘ └──────┬──────┘
      │           │          │     │         │              │
      ▼           ▼          ▼     ▼         ▼              ▼
 ┌──────────────────────────────┐ ┌────────────┐   ┌──────────────┐
 │       PostgreSQL             │ │   Redis    │   │  Loki :3100  │
 │ users · subscriptions ·      │ │ wa:queue   │   │ query_range  │
 │ payments · send_logs ·       │ │ wa:heartbeat│  │              │
 │ schedules · messenger_accounts│ │ max:*      │  │ ОПЦИОНАЛЕН — │
 └──────────────────────────────┘ │ celery:    │   │ деградирует  │
                                  │  telegram  │   │ в плашку     │
                                  └────────────┘   └──────────────┘

  ═══ ОТДЕЛЬНАЯ ВЕТКА: только по нажатию кнопки, НЕ при рендере (D-07/D-11) ═══
  POST /admin/workers/{id}/restart ──► wa_container_manager.start_container
                                       max_container_manager.start_container
                                                 │
                                                 ▼
                                        Docker daemon (unix socket)
```

Читать так: **при рендере любого подраздела стрелка в Docker daemon не проводится ни разу**. Она возникает единственный раз — от формы POST перезапуска. Стрелка в Loki — единственная, которая имеет право не дойти: у неё таймаут и деградация в плашку, а не в 500.

### Recommended Project Structure

```
app/
├── pages/
│   └── admin.py                    # шесть маршрутов + действия; groups-info уходит
├── services/
│   ├── ops_state.py                # НОВЫЙ: async-чтение Redis — heartbeat, LLEN, LRANGE, LREM
│   └── loki_client.py              # НОВЫЙ: query_range + деградация по таймауту
├── application/
│   ├── analytics/send_analytics.py # РАСШИРЯЕТСЯ: общесистемный вход (D-39)
│   ├── admin/                      # НОВЫЙ пакет
│   │   ├── users_query.py          # фильтры+счётчик ОДНИМ выражением (D-34)
│   │   ├── incidents.py            # пять признаков D-45, чистые функции над данными
│   │   └── payments_query.py       # журнал + MRR + «истекло и не продлено»
│   └── scheduling/use_cases.py     # ПРАВКА: блокировка в collect_due_schedules (Ф-5)
├── dependencies.py                 # НОВАЯ соседняя зависимость блокировки (Ф-4)
├── services/auth_service.py        # ПРАВКА: claim act (D-19)
├── pages/auth.py                   # ПРАВКА: CR-01, CR-02, CR-03
└── templates/
    ├── base.html                   # ПРАВКА: полоса имперсонации (D-25)
    ├── components/
    │   └── filter_chips.html       # ПЕРЕЕЗД из history/includes/ (Ф-15)
    └── admin/
        ├── includes/_tabs.html     # вкладки шести подразделов
        ├── overview.html  users.html  workers.html
        ├── queue.html     logs.html   payments.html
        └── includes/{worker_row,queue_row,log_row,incident_row}.html
```

Причина, по которой чтение Redis и Loki — **сервисы, а не код в обработчике**: подмена в суите (§Pattern 7) требует именованной точки для `patch`, а обработчик такой точкой быть не может.

### Pattern 1 — Подраздел как настоящий маршрут (D-01)

**Что:** шесть обработчиков в одном роутере, каждый ставит `active_page = "admin"` и передаёт `admin_tab` для подсветки вкладки.
**Когда:** для всех шести подразделов.
**Почему именно так:** `nav_label` (`app/pages/common.py:147-155`) уже возвращает «Админ-панель» для `active_page == "admin"`, значит заголовок шелла корректен для всех шести без правок. Вкладка подсвечивается **вторым** ключом внутри контента.

```python
# app/pages/admin.py — форма повторяет уже отгруженные обработчики раздела
ADMIN_TABS = (
    ("overview", "Обзор",        "/admin"),
    ("users",    "Пользователи", "/admin/users"),
    ("workers",  "Воркеры",      "/admin/workers"),
    ("queue",    "Очередь",      "/admin/queue"),
    ("logs",     "Логи",         "/admin/logs"),
    ("payments", "Платежи",      "/admin/payments"),
)

@router.get("/workers", response_class=HTMLResponse)
async def admin_workers(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return templates.TemplateResponse(
        "admin/workers.html",
        {
            "request": request, "user": admin, "is_admin": True,
            "active_page": "admin",      # подсветка раздела в сайдбаре
            "admin_tab": "workers",      # подсветка вкладки внутри подраздела
            "admin_tabs": ADMIN_TABS,
            ...
        },
    )
```

Вкладки — обычные `<a href>`. Проверяемое утверждение для суиты: **разметка вкладок не содержит ни `hx-`, ни `x-on:`** — по образцу тестов `*_degrades_without_alpine`.

### Pattern 2 — Блокировка соседней зависимостью, а не правкой аутентификатора (D-30, Ф-4)

**Что:** новая зависимость `get_current_user_id_active` рядом с `get_current_user_id_with_access`, вешается пер-роутерно в `app/main.py`, и **перечень роутеров закрепляется третьим множеством в машинном гейте**.
**Когда:** для JSON-поверхности CR-01.
**Почему:** сохраняет зелёным `test_the_api_authentication_dependency_is_left_untouched` (Ф-4) и повторяет ровно тот приём, который проект уже выбрал для гейта доступа.

```python
# app/dependencies.py — форма взята у get_current_user_id_with_access
async def get_current_user_id_active(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> int:
    """Идентификатор вошедшего — при условии, что учётка НЕ ЗАБЛОКИРОВАНА (CR-01).

    ⚠️ ПРОВЕРКА ЖИВЁТ ЗДЕСЬ, А НЕ В `get_current_user_id`, И ЭТО ВЫНУЖДЕННО:
    `test_the_api_authentication_dependency_is_left_untouched` читает исходник
    по AST и запрещает параметру `db` появляться в аутентификаторе.

    ⚠️ АДМИН ПОД ЧУЖОЙ УЧЁТНОЙ ЗАПИСЬЮ ЭТОЙ ПРОВЕРКОЙ НЕ ЗАДЕВАЕТСЯ (D-26):
    при наличии `act` блокировка `sub` не применяется — вход под заблокированным
    и есть тот случай, ради которого имперсонация нужна.
    """
    from app.models.user import User

    token = _read_token(request, credentials)          # общий helper с аутентификатором
    payload = decode_access_token(token, settings.secret_key)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("act") is not None:                 # D-26
        return payload["sub"]

    user = await db.get(User, payload["sub"])
    if user is None or user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")
    return payload["sub"]
```

**Что обязан решить планировщик, а не исполнитель:** вешать ли новую зависимость на `billing_router`. Он сегодня объявлен «открытым НИКОГДА не закрывается» (`OPEN_API_ROUTERS`), и вебхук ЮKassa в нём же — отказ 403 на уведомлении о состоявшемся платеже остановил бы приём денег. Рекомендация: **на `billing_router` не вешать**, а если блокировка обязана закрывать и оплату — закрывать только страничную форму покупки, не вебхук. Это решение владельца, не исполнителя.

Третий путь (`collect_due_schedules`, Ф-5) — соседнее условие в уже существующей ветке:
```python
        # рядом с checked_users[user_id] = await check_limit(...)
        # блокировка спрашивается ОДИН раз на пользователя, как и вердикт доступа
```

### Pattern 3 — Claim `act` (D-19, D-20, D-25)

**Что:** тот же токен, тот же секрет, тот же алгоритм; добавляется claim `act` и отдельный короткий `exp`.
**Когда:** только на входе под пользователем и возврате.

⚠️ **Форма значения — решение планировщика, и у него есть внешний ориентир.** RFC 8693 определяет `act` как **JSON-объект**, а не скаляр: `"act": {"sub": "<admin_id>"}`; вложенный `act` внутри `act` записывает цепочку делегирования, а потребитель токена **обязан учитывать только верхнеуровневые claims и текущего актора** [CITED: rfc-editor.org/rfc/rfc8693] — что в точности и есть D-20. Скалярный `act: 42` работает и проще, но перестаёт быть RFC-формой; выбрать надо явно и записать причину.

```python
# app/services/auth_service.py — обе функции остаются ЕДИНСТВЕННОЙ точкой
IMPERSONATION_EXPIRE_MINUTES = 60          # D-25

def create_access_token(
    user_id: int,
    secret_key: str,
    expires_minutes: int = 1440,
    *,
    actor_id: int | None = None,           # НОВЫЙ keyword-only параметр
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    if actor_id is not None:
        payload["act"] = {"sub": str(actor_id)}    # форма RFC 8693
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)
```

⚠️ **`decode_access_token` приводит `sub` к `int` явно** — `payload["sub"] = int(payload["sub"])` [VERIFIED: app/services/auth_service.py:26]. Значит и `act` обязан пройти то же приведение в том же месте, иначе `check_is_admin` сравнит `"42"` с `42` в одном читателе и `42` с `42` в другом. Приведение обязано жить **внутри** `decode_access_token`, а не у каждого читателя.

⚠️ **D-21 закрепляется тестом, а не аккуратностью:** токен без `act` обязан дать байт-в-байт прежний payload. Утверждение проверяемо на уровне словаря: `set(decode_access_token(old_token, key)) == {"sub", "exp"}`.

### Pattern 4 — Запрет действий под имперсонацией машинным гейтом (D-23)

**Что:** зависимость `forbid_when_impersonating` вешается пер-роутерно, а её перечень закрепляется AST-гейтом по образцу `test_access_gate.py`.
**Почему AST, а не список маршрутов:** тот же довод, что записан в существующем гейте — *«роутер без зависимости в объекте приложения выглядит совершенно обычно: у его маршрутов просто нет одной зависимости, и отличить „забыли“ от „не должно быть“ там нечем. В исходнике же решение записано явным вызовом, и множество вызовов замкнуто»* [VERIFIED: tests/test_pages/test_access_gate.py:23-28].

Готовый разборщик копируется целиком:
```python
def _routers_with_dependency(source: Path, dependency: str) -> dict[str, bool]:
    """Каждый вызов `.include_router(...)` → «висит ли на нём названная зависимость»."""
    tree = ast.parse(source.read_text(encoding="utf-8"))
    ...
```
[VERIFIED: tests/test_pages/test_access_gate.py:97-120]

⚠️ **Тонкость, которую CONTEXT.md не называет:** «отправка и повтор рассылки» (D-22) живут **не в отдельном роутере**. Повтор — `app/pages/history.py` (роутер «История» целиком запрещать нельзя: чтение истории под имперсонацией разрешено D-22), смена пароля и email — внутри `auth_router`, который обязан оставаться открытым для входа. Значит гейт **не может** быть чисто пер-роутерным, как гейт доступа: часть запретов ляжет на **отдельные маршруты**. Форма гейта тогда — «перечень (роутер, маршрут) объявлен здесь, и каждое изменяющее объявление в этих модулях обязано попасть либо в разрешённые, либо в запрещённые», с обходом `@router.post`/`@router.put`/`@router.delete` по AST. Это **самая сложная задача фазы по форме утверждения** — планировать её отдельным планом, а не пунктом.

### Pattern 5 — Расширение модуля аналитики, а не второй запрос (D-39)

Текущая подпись — `send_metrics(session, *, user_id: int, now=None, window=DEFAULT_WINDOW)` [VERIFIED: app/application/analytics/send_analytics.py:138-144]. Общесистемный вход добавляется **внутри модуля**, потому что фильтр по пользователю — одно условие в `WHERE`:
```python
            ).where(
                SendLog.user_id == user_id,        # ← единственная строка, требующая правки
                SendLog.sent_at >= previous_start,
                SendLog.sent_at <= now,
            )
```
[VERIFIED: app/application/analytics/send_analytics.py:196-208]

Рекомендуемая форма — `user_id: int | None = None` с ветвлением при сборке `where`, **а не** отдельная функция: восемь условных агрегатов и защита от `NULL` в `int(... or 0)` тогда не дублируются. Дельта плитки «Ошибок за сутки» (D-37, D-40) достаётся из `failed_prev` бесплатно — `DEFAULT_WINDOW` модуля уже равен суткам (Фаза 4, D-02).

### Pattern 6 — Фильтры, счётчик и страница ОДНИМ выражением (D-33, D-34)

Образец уже отгружен: `apply_history_filters` строит `select`, `history_count` считает по **тому же** выражению [VERIFIED: app/application/analytics/send_analytics.py:764, 797]. Санация значений — `clean_choice(value, allowed)` над замкнутым множеством, полученным из объявления чипсов: `STATUS_VALUES = _values(STATUS_CHIPS)` [VERIFIED: app/pages/history.py:98-103].

⚠️ **Сегодняшний `admin_users` тянет всю таблицу:** `get_all_users()` — `select(User).order_by(User.id)` **без `limit`** [VERIFIED: app/repositories/user.py:17-21], и `search_users` тоже [VERIFIED: app/repositories/user.py:23-30]. D-33 закрывает это. Форма поиска — `or_(User.email.ilike(pattern), User.name.ilike(pattern))` — переносится дословно; **`ilike` на SQLite регистронезависим только для ASCII**, то есть поиск по русскому имени в суите ведёт себя иначе, чем на PostgreSQL. Тест на кириллический поиск обязан это учитывать (см. §Pitfall 6).

### Anti-Patterns to Avoid

- **`EXISTS`/`is not None` как признак живого воркера.** У WA нет TTL (Ф-6) → мёртвый воркер выглядит живым бессрочно. Только сравнение возраста.
- **Единая формула разбора `_delay_until`.** Единицы разные (Ф-7); одна формула тихо врёт на одном из двух каналов.
- **`{level="warn"}` как фильтр «предупреждения».** Скрывает предупреждения приложения (Ф-8).
- **Добавление `db` в `get_current_user_id`.** Роняет зелёный AST-тест (Ф-4).
- **Безусловный `secure=True` на cookie.** Ломает вход в HTTP-only режиме nginx (Ф-9).
- **Docker SDK при рендере любого подраздела.** Прямо запрещено D-07; вдобавок при недоступном демоне подраздел уходит в 500 вместо деградации.
- **Своя копия `access_is_open`.** Единственное объявление правила доступа — `app/application/billing/subscription_period.py:85`, и его порядок веток закреплён AST-тестом.
- **`datetime` без `normalize_utc`.** SQLite отдаёт naive, PostgreSQL — aware (§Pitfall 1).
- **Строковая сборка разметки.** `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` — ноль по проекту, проверяется по исходнику.
- **`confirm()` вместо панели подтверждения.** 13+ мест уже переведены на `components/modal.html`.

---

## Don't Hand-Roll

| Проблема | Не строить | Использовать | Почему |
|----------|-----------|--------------|--------|
| «Свеж ли heartbeat» | своё сравнение с 60 с | `_has_fresh_heartbeat` + `MAX_HEARTBEAT_STALE_SEC = 90` (`max_container_manager.py:20,156`) | второе число на тот же вопрос разойдётся с первым; нижняя граница `0 <= age_ms` уже отсекает heartbeat из будущего |
| «Открыт ли доступ» | второе сравнение дат | `access_is_open` (`subscription_period.py:85`) через `_access_view` (`admin.py:85`) | порядок веток (льгота раньше живости срока) закреплён AST-тестом; своя копия развела бы правило |
| Дни до конца доступа | `(exp - now).days` | `days_left` (`subscription_period.py:151`) | сам приводит оба момента через `normalize_utc`; может быть отрицателен у льготного — учтено D-35 |
| Дата в зоне пользователя | `strftime` в шаблоне | `format_datetime_for_user` (глобал Jinja) | локаль процесса; `SHORT_WEEKDAYS` в модуле аналитики выписан явно ровно по этой причине |
| Денежная подпись | своё форматирование | `format_amount` (`common.py`, глобал Jinja) | `NaN`/`Infinity` — валидные `Decimal` и роняют раздел; проверка конечности уже внутри |
| Склонение числа | `if n == 1` в шаблоне | `plural_ru` (глобал Jinja) | «осталось 1 дней» — дефект контракта |
| Панель подтверждения | `confirm()` | `components/modal.html` `modal(...)` | ловушка фокуса, Esc, возврат фокуса, гард повторной отправки — уже написаны |
| Чипсы фильтров | своя разметка кнопок | `filter_chips(...)` (⚠️ Ф-15 — сначала переезд) | одно состояние = одно слово и один цвет |
| Пустое состояние | свой `<div>` | `components/empty_state.html` | ⚠️ но для недоступного Loki это **`alert(..., variant='warning')`**, а не пустое состояние (D-28) |
| Подсчёт задач Celery | разбор kombu-конверта | `LLEN` по имени очереди | тело задачи — base64 внутри JSON-конверта kombu, внутренняя деталь библиотеки (D-14); ⚠️ Ф-13 про priority-суффиксы |
| Асинхронный Redis | свой пул на обработчик | форма `_get_redis()` из `billing_cache.py:14-25` | ленивая инициализация модульного клиента + `except` вокруг каждого обращения |
| HTTP c таймаутом | `requests`/свой retry | `httpx` с явным `timeout` | официальный python-пример Loki написан на `httpx` |
| Проверка «роутер получил зависимость» | греп по строке | AST-разбор `_routers_with_dependency` (`test_access_gate.py:97`) | греп считает строку и в комментарии, и в докстринге |

**Key insight:** в этом проекте почти каждое число и каждое правило уже объявлены **один раз** с выписанным объяснением, почему копия недопустима. Фаза 6 — это фаза **поиска существующего объявления**, а не написания нового. Три места, где новое объявление действительно нужно, названы явно: клиент Loki, async-чтение Redis из веба и claim `act`.

---

## Runtime State Inventory

> Фаза сносит два экрана (D-05) и переписывает раздел, поэтому инвентаризация обязательна.

| Категория | Найдено | Требуемое действие |
|-----------|---------|--------------------|
| **Хранимые данные** | Таблица `group_info` и ревизия `0011` **остаются нетронутыми** (D-05, явное решение). Писателя у неё нет — `GroupInfoRepository.upsert` не вызывается ниоткуда в `app/` (Ф-2 CONTEXT.md; подтверждено грепом в этой сессии). Миграций фаза не требует: ни `status_changed_at` (D-47), ни таблиц инцидентов/аудита | правка кода, **не** миграция данных |
| **Живая конфигурация служб** | Loki/Promtail/Grafana поднимаются **отдельным** compose и **не** входят в `just prod-start` / `prod-deploy` [VERIFIED: justfile:63-64, 74-76, 116-127]. Сеть монтируется как `broadcaster` `external: true` [VERIFIED: docker-compose.monitoring.yml:55-58] — значит `http://loki:3100` из `web` виден **только когда мониторинг поднят**. Метки promtail (`level`, `container_name`, `broadcaster_role`, `account_id`) настроены в git-файле, не в UI | ничего не менять (D-28); подраздел «Логи» обязан деградировать |
| **OS-регистрируемое состояние** | Контейнеры воркеров создаются Docker API с метками `broadcaster.role` / `broadcaster.account_id` [VERIFIED: app/services/wa_container_manager.py:68-71]. `celery-worker-telegram` — **единственный сервис прод-compose без `container_name`** [VERIFIED: docker-compose.prod.yml:108-113] → его метка `container_name` в Loki генерируется compose-ом, а не совпадает с именем сервиса (⚠️ Ф-16) | перечень источников для «Логов» строить из **фактических** имён, не из имён сервисов; проверить на живом Loki |
| **Секреты и переменные окружения** | Новых секретов фаза не требует. Ф-9 предлагает **одну новую настройку** — флаг `secure` для cookie; форма — как у `YOOKASSA_WEBHOOK_CLIENT_IP_HEADER: ${...:-X-Real-IP}` [VERIFIED: docker-compose.prod.yml:26]: безопасное умолчание в артефакте, переопределение из `.env` | добавить в `.env.example` и в `x-app-base.environment` |
| **Артефакты сборки / установленные пакеты** | Новых пакетов нет → `uv.lock` не двигается. Шаблоны Jinja читаются с диска, кеш Jinja сбрасывается перезапуском `web`. `asset_version` в `base.html` уже версионирует CSS/JS | ничего |

**Ничего не найдено:** не обнаружено ни одного случая, когда снос `/admin/groups-info` оставил бы висящую ссылку **вне** админки — проверено грепом по `app/templates/`: вхождения `groups-info` только в `app/templates/admin/groups_info.html` и `group_info_detail.html` (сносимые) и в `app/pages/admin.py:637,679`. Внешних потребителей нет.

---

## Common Pitfalls

### Pitfall 1 — naive vs aware `datetime`: одна СУБД зелёная, вторая красная

**Что идёт не так:** арифметика над `DateTime(timezone=True)` падает `TypeError: can't subtract offset-naive and offset-aware datetimes` — но **только на одном из двух диалектов**.
**Почему:** *«колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а PostgreSQL — aware, и вычитание без приведения падало бы TypeError ровно на одном из двух диалектов — то есть у пользователя, а не в суите»* [VERIFIED: app/application/billing/subscription_period.py:167-172].
**Как избежать:** каждый момент, приходящий из базы, проводить через `normalize_utc` [VERIFIED: app/application/analytics/send_analytics.py:82]. Фаза 6 добавляет **пять новых мест арифметики над временем**: возраст `pending`-платежа (D-45.4), просрочка `next_run_at` (D-45.5), `sent_at` последнего `account_disconnected` (D-47), `last_synced_at` (D-47), `created_at` пользователя для «+N за неделю» (D-37). Все пять — кандидаты на этот дефект.
**Признак:** суита зелёная, прод падает 500 на «Обзоре».

### Pitfall 2 — «нет heartbeat» ≠ «воркер упал»

**Что идёт не так:** подраздел красит красным штатное состояние.
**Почему:** воркеры самоубиваются через `IDLE_SHUTDOWN_SEC = 300` [VERIFIED: wa_worker/index.js:28, max_worker/main.py:56], а `manage_wa_containers` поднимает контейнер **только при непустой очереди** [VERIFIED: app/worker/tasks.py:670-677]. Отсутствие контейнера — норма.
**Как избежать:** D-08 буквально: «офлайн» ⟺ `LLEN wa:queue:{id} > 0` **И** heartbeat несвеж. Иначе — «простаивает».
**Признак:** админ звонит по каждому «офлайн», и через неделю перестаёт смотреть подраздел вовсе.

### Pitfall 3 — стухший `wa:heartbeat` живёт вечно (Ф-6)

**Что идёт не так:** WA-воркер, убитый `docker kill` или OOM, показан живым бессрочно — потому что при жёстком убийстве `gracefulShutdown` не выполняется, а TTL у ключа нет.
**Как избежать:** сравнение возраста, а не наличия. Порог — `MAX_HEARTBEAT_STALE_SEC = 90`.
**Признак:** «Воркеры» показывают зелёное, «Очередь» растёт, рассылки стоят.

### Pitfall 4 — `LLEN telegram` считает не всё, если однажды появятся приоритеты (Ф-13)

**Что идёт не так:** kombu хранит очередь как Redis-список, но при ненулевом приоритете — в **отдельном ключе с суффиксом**:
```python
    def _q_for_pri(self, queue, pri):
        pri = self.priority(pri)
        if pri:
            return f"{queue}{self.sep}{pri}"
        return queue
```
[VERIFIED: .venv/lib/python3.12/site-packages/kombu/transport/redis.py:1024-1028], где `PRIORITY_STEPS = [0, 3, 6, 9]` и `sep = '\x06\x16'` [VERIFIED: там же:106, 634].
**Сегодня безопасно:** `celery_app.py` приоритетов не назначает [VERIFIED: app/worker/celery_app.py:16-51], `apply_async` вызывается только с `queue="telegram"` [VERIFIED: app/worker/tasks.py:96-100] → все задачи ложатся в ключ `telegram`.
**Как избежать регресса:** считать суммой по `PRIORITY_STEPS` (ровно так делает сам kombu в `_size()`), либо оставить `LLEN telegram` и **закрепить тестом**, что `apply_async` в проекте не передаёт `priority`. Второе дешевле и честнее.

### Pitfall 5 — Loki доступен, но окно шире retention

**Что идёт не так:** запрос за 24 часа возвращает меньше, чем ожидалось, без всякой ошибки.
**Почему:** `retention_period: 168h` и `reject_old_samples_max_age: 168h` [VERIFIED: monitoring/loki.yml:29-31] — семь суток. Все три окна D-29 (15 мин / 1 ч / 24 ч) укладываются, но произвольный диапазон (отвергнут D-29) уткнулся бы в этот потолок.
**Как избежать:** держать окна в пределах отгруженного набора; при добавлении окна >7 суток — говорить об этом словами.
**Плюс:** `auth_enabled: false` [VERIFIED: monitoring/loki.yml:1] → заголовок `X-Scope-OrgID` **не нужен**, и добавлять его не надо.

### Pitfall 6 — `ilike` на SQLite регистронезависим только для ASCII

**Что идёт не так:** тест поиска пользователя по «Иван» проходит, а по «иван» — нет; на PostgreSQL оба работают.
**Почему:** SQLite `LIKE` по умолчанию складывает регистр только для латиницы; PostgreSQL `ILIKE` работает с юникодом.
**Как избежать:** тесты поиска писать на данных, различающих оба поведения, либо приводить обе стороны через `func.lower(...)` явно — тогда поведение одинаково в обеих СУБД. Проект уже требует, чтобы всё работало «и на SQLite, и на PostgreSQL».
**Признак:** «поиск не находит» в проде или в суите, но не в обеих сразу.

### Pitfall 7 — Docker daemon недоступен, и подраздел уходит в 500

**Что идёт не так:** `docker.from_env()` бросает при недоступном сокете, и обработчик отвечает 500 вместо деградации.
**Почему:** сокет смонтирован только в `web` и `celery-worker-default` [VERIFIED: docker-compose.prod.yml:92-93, 118-122], и в dev-окружении может отсутствовать.
**Как избежать:** D-07 снимает вопрос для рендера целиком. Для кнопки «Перезапустить» (D-11) — обёртка `try/except APIError` с редиректом обратно и **именованной строкой в журнале**, по образцу `free_access_toggle_without_subscription` [VERIFIED: app/pages/admin.py:571-576]: молча вернувшая ту же страницу кнопка читается как «кнопка сломана».

### Pitfall 8 — снос экранов без вердикта по требованию

**Что идёт не так:** `/admin/groups-info` исчезает, ADMIN-02 остаётся `Complete (baseline)`, и через месяц никто не может ответить, была ли вторая половина требования выполнена или потеряна.
**Как избежать:** D-05 требует **отдельной задачи** внесения частичного вердикта в `.planning/REQUIREMENTS.md`. Образец формы вердикта — GRP-08: строка прослеживаемости **сохранена** и переведена в `Out of scope v2.0 (D-13, 2026-08-11)` с причиной и датой, *«удалять её нельзя, иначе „отменено“ станет неотличимо от „потеряно“»* [VERIFIED: .planning/REQUIREMENTS.md:296].

### Pitfall 9 — cookie удаляется не тем же набором атрибутов

**Что идёт не так:** возврат из имперсонации (D-25) не срабатывает — старая cookie остаётся.
**Почему:** `response.delete_cookie("access_token")` [VERIFIED: app/pages/auth.py:347] выставляет удаляющую cookie с умолчаниями `path="/"`, без `samesite`/`secure`. Если установка получит `secure=True` (Ф-9), а удаление — нет, браузер может не сопоставить их.
**Как избежать:** возврат из имперсонации **перевыпускает** токен (`sub = act`, без `act`) и **перезаписывает** cookie тем же вызовом `set_cookie` с тем же набором атрибутов — не удаляет и не заводит вторую. Тот же набор атрибутов вынести в одну функцию, чтобы все три места (вход, регистрация, возврат) читали одно объявление.

### Pitfall 10 — `filter_chips` жёстко привязан к `/history` (Ф-15)

**Что идёт не так:** импорт макроса в админку даёт чипсы, ведущие на `/history`.
**Почему:** сигнатура — `filter_chips(options, active, base_params, param_name, base_path='/history')` [VERIFIED: app/templates/history/includes/filter_chips.html:52], и файл лежит в `history/includes/`.
**Как избежать:** перенести в `app/templates/components/filter_chips.html` и обновить три существующих импорта (`history/list.html:8` и соседи), либо всегда передавать `base_path` явно. Первое честнее: чипсы становятся третьим потребителем и перестают быть «деталью истории». Перенос — задача с регрессией на существующие экраны, а не строчка.

### Pitfall 11 — «Платящих» посчитано вместе с льготными

**Что идёт не так:** MRR накручивается административной льготой.
**Почему:** `has_free_access` открывает доступ, но денег не приносит [VERIFIED: app/models/subscription.py:36-47].
**Как избежать:** D-38 буквально — `Subscription.is_active.is_(True)` **И** `Subscription.has_free_access.is_(False)` **И** живой `expires_at`. Три условия, не два.

### Pitfall 12 — залипший `pending` считается от неправильной колонки

**Что идёт не так:** возраст платежа считают от `confirmed_at`, который у `pending` **всегда `NULL`** [VERIFIED: app/models/payment.py:65-67].
**Как избежать:** только `Payment.created_at`; фильтр статуса — через `Payment.status.not_in(TERMINAL_STATUSES)`, а не `== "pending"`, по объявленному в проекте доводу: *«копия в ветке рано или поздно разойдётся с оригиналом — достаточно, чтобы третью ветку добавили, забыв её скопировать»* [VERIFIED: app/services/payment_service.py:34-38].
**Готовое число:** `PENDING_INTENT_TTL_HOURS = 24` [VERIFIED: app/services/payment_service.py:52] — уже объявленный проектом срок давности незакрытого намерения. **Взять его**, а не изобретать своё «сколько часов делают платёж залипшим» (дискреция).

---

## Code Examples

### Пример 1 — клиент Loki с деградацией (D-27, D-28)

```python
# app/services/loki_client.py
import httpx, structlog
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

logger = structlog.get_logger(__name__)

LOKI_URL = "http://loki:3100"        # мониторинг в той же сети broadcaster
LOKI_TIMEOUT_SEC = 3.0
LOG_LINE_CAP = 200                   # D-29


@dataclass(slots=True)
class LogWindow:
    lines: list[tuple[datetime, str, str, str]]   # (ts, level, source, text)
    capped: bool
    unavailable: bool                # ⚠️ ОТДЕЛЬНОЕ ПОЛЕ, А НЕ ПУСТОЙ СПИСОК


async def query_range(logql: str, window: timedelta) -> LogWindow:
    """Строки Loki за окно. Недоступность НАЗЫВАЕТСЯ, а не притворяется пустотой.

    ⚠️ ПУСТОЙ СПИСОК И НЕДОСТУПНЫЙ ИСТОЧНИК — РАЗНЫЕ СОСТОЯНИЯ, И РАЗМЕТКА
    ОБЯЗАНА ИХ РАЗЛИЧАТЬ (D-28). Пустой список читается как «ошибок не было» —
    то есть как ответ на вопрос, ради которого админ в подраздел и пришёл.
    """
    end = datetime.now(timezone.utc)
    start = end - window
    try:
        async with httpx.AsyncClient(timeout=LOKI_TIMEOUT_SEC) as client:
            resp = await client.get(
                f"{LOKI_URL}/loki/api/v1/query_range",
                params={
                    "query": logql,
                    # ⚠️ НАНОСЕКУНДЫ СТРОКОЙ — контракт API, не оформление
                    "start": str(int(start.timestamp() * 1e9)),
                    "end": str(int(end.timestamp() * 1e9)),
                    "limit": LOG_LINE_CAP + 1,   # +1, чтобы УЗНАТЬ о срабатывании потолка
                    "direction": "backward",
                },
            )
            resp.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning("loki_unavailable", error=str(e))
        return LogWindow(lines=[], capped=False, unavailable=True)

    rows = []
    for stream in resp.json()["data"]["result"]:
        labels = stream["stream"]
        source = labels.get("account_id") or labels.get("container_name") or "?"
        level = labels.get("level", "info")
        for ts_ns, line in stream["values"]:
            rows.append((
                datetime.fromtimestamp(int(ts_ns) / 1e9, tz=timezone.utc),
                level, source, line,
            ))
    rows.sort(key=lambda r: r[0], reverse=True)
    return LogWindow(lines=rows[:LOG_LINE_CAP],
                     capped=len(rows) > LOG_LINE_CAP,
                     unavailable=False)
```
Форма запроса и разбора — по официальному python-примеру Loki [CITED: github.com/grafana/loki/blob/main/docs/sources/reference/python-client-examples.md]; форма ответа `{status, data:{resultType, result:[{stream, values:[[ns, line]]}]}}` [CITED: github.com/grafana/loki/blob/main/docs/sources/reference/loki-http-api.md].
Приём «`limit + 1`, чтобы честно назвать потолок» — прецедент Фазы 4 (D-27) и `PAYMENT_LIST_CAP` [VERIFIED: app/constants.py:61-65].

### Пример 2 — сборка селектора LogQL из чипсов (D-29, Ф-8)

```python
# ⚠️ СЛОВАРЬ «ЧИПС → ЗНАЧЕНИЯ МЕТКИ» ОБЪЯВЛЕН ОДИН РАЗ.
# Уровень «предупреждение» приезжает в Loki ДВУМЯ разными словами:
# structlog.stdlib.add_log_level пишет "warning", а promtail переводит
# числовой уровень Pino 40 в "warn" (monitoring/promtail.yml). Один литерал
# в селекторе скрыл бы ровно половину предупреждений — молча, при 200.
LEVEL_CHIPS: dict[str, tuple[str, ...]] = {
    "all":   (),
    "error": ("error", "fatal", "critical"),
    "warn":  ("warn", "warning"),
    "info":  ("info",),
}

def build_logql(level: str, source: str | None, text: str | None) -> str:
    matchers = ['job="docker"'] if not source else []
    if source and source.isdigit():
        matchers.append(f'account_id="{source}"')       # воркер аккаунта
    elif source:
        matchers.append(f'container_name="{source}"')   # сервис
    values = LEVEL_CHIPS.get(level, ())
    if values:
        matchers.append(f'level=~"{"|".join(values)}"')
    selector = "{" + ", ".join(matchers) + "}"
    # ⚠️ ТЕКСТ УХОДИТ В |=, А НЕ В СЕЛЕКТОР: это не метка, и Loki
    # индексирует только метки. Кавычка внутри текста обязана быть
    # экранирована — иначе запрос синтаксически ломается 400-й.
    return f'{selector} |= "{text}"' if text else selector
```
Синтаксис селектора и line-фильтров [CITED: github.com/grafana/loki/blob/main/docs/sources/query/log_queries/_index.md]; словарь-по-чипсам — форма `STATUS_CHIPS`/`_values` [VERIFIED: app/pages/history.py:98-103].

### Пример 3 — живость воркеров одним round-trip (D-06, D-12, Ф-6)

```python
# app/services/ops_state.py
import time
import redis.asyncio as aioredis

MAX_HEARTBEAT_STALE_SEC = 90     # ← ТО ЖЕ число, что max_container_manager.py:20


def _is_fresh(raw: bytes | str | None) -> bool:
    """Форма взята у `_has_fresh_heartbeat` (max_container_manager.py:156).

    ⚠️ ВОЗРАСТ, А НЕ НАЛИЧИЕ. `wa:heartbeat` пишется БЕЗ TTL
    (wa_worker/index.js:965) и удаляется только при graceful shutdown
    (:666) — то есть WA-воркер, убитый жёстко, оставляет ключ навсегда.
    Проверка `is not None` показывала бы мёртвый воркер живым бессрочно.

    ⚠️ НИЖНЯЯ ГРАНИЦА ОБЯЗАТЕЛЬНА: heartbeat из будущего (разошедшиеся
    часы) при проверке только сверху читался бы как «только что».
    """
    try:
        beat_ms = int(raw)
    except (TypeError, ValueError):
        return False
    age_ms = int(time.time() * 1000) - beat_ms
    return 0 <= age_ms <= MAX_HEARTBEAT_STALE_SEC * 1000


async def worker_liveness(r: aioredis.Redis,
                          wa_ids: list[int], max_ids: list[int]) -> dict[int, dict]:
    """Живость и глубина очереди для всех аккаунтов — ОДНИМ pipeline."""
    pipe = r.pipeline()
    for i in wa_ids:
        pipe.get(f"wa:heartbeat:{i}"); pipe.llen(f"wa:queue:{i}")
    for i in max_ids:
        pipe.get(f"max:heartbeat:{i}"); pipe.llen(f"max:queue:{i}")
    flat = await pipe.execute()

    out, pos = {}, 0
    for account_id in [*wa_ids, *max_ids]:
        beat, depth = flat[pos], int(flat[pos + 1] or 0)
        pos += 2
        fresh = _is_fresh(beat)
        # D-08: «офлайн» честен РОВНО при непустой очереди И несвежем heartbeat.
        # Иначе — «простаивает»: воркер уходит сам через IDLE_SHUTDOWN_SEC=300,
        # и отсутствие контейнера есть ШТАТНОЕ состояние.
        out[account_id] = {
            "queue_depth": depth,
            "worker": "online" if fresh else ("offline" if depth > 0 else "idle"),
        }
    return out
```

### Пример 4 — разбор строки очереди с учётом единиц времени (D-16, Ф-7)

```python
from datetime import datetime, timezone

def parse_delay_until(raw, channel: str) -> datetime | None:
    """`_delay_until` из тела задачи → момент. ЕДИНИЦЫ ЗАВИСЯТ ОТ КАНАЛА.

    ⚠️ WA пишет МИЛЛИСЕКУНДЫ (`Date.now() + delaySec * 1000`,
    wa_worker/index.js:583), MAX — СЕКУНДЫ (`time.time() + delay_sec`,
    max_worker/main.py:719). Единая формула не падает — она рисует
    правдоподобную ложь: WA-задача «отложена до 55-го тысячелетия»
    либо MAX-задача «отложена до 1970 года».
    """
    if raw is None:
        return None
    seconds = float(raw) / 1000.0 if channel == "wa" else float(raw)
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def queue_row_state(task: dict, channel: str) -> tuple[str, datetime | None, int]:
    """«ждёт» / «отложена до T» / «ретрай N» (D-16).

    Оба поля читаются через `.get`: в СВЕЖЕЙ задаче их НЕТ вовсе —
    их дописывает только воркер при ретрае (dispatch_send_tasks кладёт
    ровно одиннадцать полей, app/worker/tasks.py:113-127).
    """
    retries = int(task.get("_retry_count", 0))
    until = parse_delay_until(task.get("_delay_until"), channel)
    now = datetime.now(timezone.utc)
    if until and until > now:
        return "delayed", until, retries
    return ("retrying" if retries else "waiting"), None, retries
```

### Пример 5 — снятие задачи `LREM` по точному телу (D-17)

```python
async def drop_task(r, channel: str, account_id: int, raw_body: str) -> bool:
    """Снять ОДНУ задачу из очереди канала по её точному телу.

    ⚠️ `count=1`, А НЕ 0. Ноль удалил бы ВСЕ совпадающие вхождения; тела
    задач содержат `task_id` из uuid4 (app/worker/tasks.py:114) и потому
    уникальны, но правило «снять одну» обязано быть выражено, а не выведено
    из свойства данных.

    ⚠️ ТЕЛО ПРИХОДИТ ИЗ ФОРМЫ, ТО ЕСТЬ ОТ КЛИЕНТА. Совпадение байт-в-байт с
    записанным — единственное условие удаления, поэтому подделать снятие
    ЧУЖОЙ задачи можно только зная её тело целиком; ничего, кроме
    существующей задачи, LREM не удалит. Маршрут за require_admin.

    ⚠️ `SendLog` НЕ ПИШЕТСЯ (D-18): снятая задача попытки отправки не
    совершила, а журнал отражает попытки.
    """
    removed = await r.lrem(f"{channel}:queue:{account_id}", 1, raw_body)
    return bool(removed)
```

### Пример 6 — пять признаков инцидента (D-45)

```python
# app/application/admin/incidents.py — ЧИСТЫЕ функции над уже прочитанными данными.
# Отдельный модуль, потому что признаки должны проверяться в суите БЕЗ Redis,
# Docker и Loki: на вход подаются значения, а не клиенты.

INCIDENT_KIND_WORKER_STUCK   = "worker_stuck"      # D-45.1 → «Воркеры»
INCIDENT_KIND_ACCOUNT_DOWN   = "account_down"      # D-45.2 → карточка пользователя
INCIDENT_KIND_FAILURE_SPIKE  = "failure_spike"     # D-45.3 → «История» с фильтром
INCIDENT_KIND_PAYMENT_STUCK  = "payment_stuck"     # D-45.4 → «Платежи»
INCIDENT_KIND_BEAT_SILENT    = "beat_silent"       # D-45.5 → блок инфраструктуры

# Статусы аккаунта, означающие «отвалился» (D-45.2). Значения — те же строки,
# которые пишет прикладной код: "sync_failed" (app/application/accounts/
# use_cases.py:61) и умолчание модели "disconnected"
# (app/models/messenger_account.py:19).
ACCOUNT_DOWN_STATUSES = frozenset({"disconnected", "sync_failed"})

# Срок давности незакрытого платежа — УЖЕ ОБЪЯВЛЕННОЕ проектом число
# (app/services/payment_service.py:52). Второе число на тот же вопрос
# разошлось бы с первым молча.
from app.services.payment_service import PENDING_INTENT_TTL_HOURS, TERMINAL_STATUSES
```

Порог «всплеска отказов» (D-45.3) считается по уже объявленным статусам:
```python
FAILED_STATUSES = (STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED)
```
[VERIFIED: app/application/analytics/send_analytics.py:65-69], где `STATUS_OK = "ok"`, `STATUS_FAIL = "fail"`, `STATUS_ACCOUNT_DISCONNECTED = "account_disconnected"`.

---

## State of the Art

| Прежний подход в проекте | Текущий подход | Когда сменилось | Что это значит для фазы 6 |
|--------------------------|----------------|-----------------|---------------------------|
| Тарифы Free/Basic/Pro, баланс сообщений | Одна цена 3000 ₽/мес, одна дата окончания | Фаза 05.1 (2026-08-20) | макетные «использовано/квота», ARPU, churn — величины без предмета (D-35, D-41) |
| `is_unlimited` на таблице остатка | `subscriptions.has_free_access` | ревизия `0020`, план 05.1-09 | «Платящих» считается без льготных (D-38); старое имя под греп-гейтом |
| `confirm()` браузера | `components/modal.html` | Фаза 1 (D-18) | «Перезапустить» и «Снять задачу» идут через панель |
| Гейт списком маршрутов | Гейт **пер-роутерной зависимостью** + AST-тест по исходнику | Фаза 05.1 (T-05.1-01, T-05.1-03) | образец для гейта запретов имперсонации (D-23) |
| Агрегации в обработчике страницы | Модуль `app/application/analytics/` | Фаза 4 (D-35) | «Обзор» **зовёт** модуль, а не пишет свои запросы (D-39) |
| Свои `SELECT` на строку списка | Один запрос на страницу с единым `now` | план 05.1-08 | `_active_subscriptions_by_user` — готовая основа D-33 |
| Grafana/Loki как единственный доступ к логам | Loki + операционный срез внутри продукта | эта фаза | Loki остаётся внешним инструментом, подраздел его не заменяет (D-28) |

**Устаревшее / вводящее в заблуждение:**
- Докстринг `send_telegram_message` (`app/worker/tasks.py:251`) обещает «Auto-retries with backoff», которого в теле нет (Ф-1 CONTEXT.md). Подраздел «Очередь» это обнажит. **В фазе 6 не чинится** — отдельный todo.
- `GroupInfoRepository.upsert` не вызывается ниоткуда (Ф-2 CONTEXT.md) — основание D-05.
- Комментарий в `admin_dashboard` (`app/pages/admin.py:145-151`) прямо помечает четыре текущие плитки как **работу под снос** фазой 6: *«показатель, заведённый здесь, будет ею переопределён»*.

---

## Environment Availability

| Зависимость | Нужна для | Доступна | Версия | Fallback |
|-------------|-----------|----------|--------|----------|
| Python | всё | ✓ | 3.14.4 (проект требует `>=3.12`) | — |
| `uv` | сборка, прогон суиты | ✓ | 0.12.1 | — |
| `just` | команды проекта | ✓ | 1.45.0 | прямые `uv run` |
| `pytest` | вся валидация | ✓ | 9.0.2 | — |
| Node.js | чтение `wa_worker/index.js` | ✓ | v22.22.1 | — |
| Docker daemon | «Перезапустить» (D-11) в ручной приёмке | ✓ | 29.7.1 | суита подменяет `_get_docker_client` |
| Redis | «Воркеры», «Очередь», инциденты | ✗ | — | **суита подменяет клиент `patch`-ем** (§Pattern 7); ручная приёмка — на среде с поднятым стеком |
| Loki `:3100` | «Логи» | ✗ | — | **сам продукт обязан деградировать** (D-28); суита подменяет `httpx`-вызов |

**Отсутствующие зависимости без fallback:** нет.

**Отсутствующие зависимости с fallback:** Redis и Loki. Оба недоступны в среде разработки, и **это не блокирует ни планирование, ни исполнение**: вся суита проекта идёт на `sqlite+aiosqlite:///:memory:` без внешних служб, а `test_settings` объявляет `redis_url="redis://localhost:6379/0"` **не подключаясь** [VERIFIED: tests/conftest.py:25-26].

⚠️ **Следствие для приёмки.** Утверждения «строка воркера показывает „простаивает“», «плашка недоступного Loki видна», «вкладки не ломаются на 375px» проверяемы только **человеком на живом стенде**. Планировщик обязан завести их пунктами UAT, а не считать закрытыми зелёной суитой.

---

## Validation Architecture

### Test Framework

| Свойство | Значение |
|----------|----------|
| Framework | `pytest` 9.0.2 + `pytest-asyncio` 1.3.0 [VERIFIED: pyproject.toml:36-37] |
| Конфиг | `pyproject.toml` (`[dependency-groups] dev`); БД суиты — `sqlite+aiosqlite:///:memory:` со схемой на каждый тест [VERIFIED: tests/conftest.py:41-52] |
| Быстрый прогон | `uv run pytest tests/test_pages/test_admin_panel.py -x -q` |
| Полный прогон | `just test` → `uv run pytest tests/ -v` |
| Готовые фикстуры | `client`, `db_session`, `auth_headers`, `authed_client`, `expired_client`, `comped_client`, **`admin_client`** [VERIFIED: tests/conftest.py:245-262], хелпер `seed_group` |

### Phase Requirements → Test Map

| Req ID | Поведение | Тип | Команда | Файл есть? |
|--------|-----------|-----|---------|-----------|
| ADMIN-03 | шесть маршрутов отвечают 200 админу и 403 не-админу | unit | `pytest tests/test_pages/test_admin_panel.py -k tabs -x` | ❌ Wave 0 |
| ADMIN-03 | вкладки — ссылки, работают без JS | unit | `pytest tests/test_pages/test_admin_panel.py -k degrades -x` | ❌ Wave 0 |
| ADMIN-03 | «Обзор» зовёт модуль аналитики, а не свой `SELECT` (AST по `app/pages/admin.py`) | unit | `pytest tests/test_application/test_admin_uses_analytics.py -x` | ❌ Wave 0 |
| ADMIN-04 | фильтры+счётчик+страница одним выражением; «N из M» совпадает с содержимым | unit | `pytest tests/test_pages/test_admin_users.py -k count -x` | ❌ Wave 0 |
| ADMIN-04 | поиск по кириллице (Pitfall 6) | unit | `pytest tests/test_pages/test_admin_users.py -k search -x` | ❌ Wave 0 |
| ADMIN-05 | блокировка закрывает **оба** входа и путь рассылки | integration | `pytest tests/test_pages/test_blocked_user.py -x` | ❌ Wave 0 (переписать `tests/test_admin.py:541`) |
| ADMIN-05 | `get_current_user_id` осталась без `db` (AST) | unit | `pytest tests/test_pages/test_access_gate.py -k untouched -x` | ✅ существует |
| ADMIN-06 | вход под пользователем, `check_is_admin` по `act`, возврат | integration | `pytest tests/test_pages/test_impersonation.py -x` | ❌ Wave 0 |
| ADMIN-06 | токен **без** `act` даёт байт-в-байт прежний payload (D-21) | unit | `pytest tests/test_services/test_auth_token.py -k without_act -x` | ❌ Wave 0 |
| ADMIN-06 | вход под ЗАБЛОКИРОВАННЫМ разрешён (D-26) | integration | `pytest tests/test_pages/test_impersonation.py -k blocked -x` | ❌ Wave 0 |
| ADMIN-06 | машинный гейт запретов: изменяющий маршрут без зависимости краснит | unit | `pytest tests/test_pages/test_impersonation_gate.py -x` | ❌ Wave 0 |
| ADMIN-07 | «нет heartbeat + пустая очередь» = «простаивает», не «офлайн» | unit | `pytest tests/test_services/test_ops_state.py -k idle -x` | ❌ Wave 0 |
| ADMIN-07 | стухший heartbeat **без TTL** читается мёртвым (Ф-6) | unit | `pytest tests/test_services/test_ops_state.py -k stale -x` | ❌ Wave 0 |
| ADMIN-07 | ни один обработчик подраздела не зовёт Docker SDK (AST/греп по `app/pages/`) | unit | `pytest tests/test_pages/test_admin_panel.py -k no_docker_on_render -x` | ❌ Wave 0 |
| ADMIN-08 | `_delay_until` разбирается по каналу: ms для wa, s для max (Ф-7) | unit | `pytest tests/test_application/test_queue_rows.py -k delay -x` | ❌ Wave 0 |
| ADMIN-08 | свежая задача без `_retry_count`/`_delay_until` рисуется «ждёт» | unit | `pytest tests/test_application/test_queue_rows.py -k fresh -x` | ❌ Wave 0 |
| ADMIN-08 | `LREM` снимает ровно одну задачу | unit | `pytest tests/test_services/test_ops_state.py -k drop -x` | ❌ Wave 0 |
| ADMIN-09 | недоступный Loki → плашка, **не** пустой список | unit | `pytest tests/test_services/test_loki_client.py -k unavailable -x` | ❌ Wave 0 |
| ADMIN-09 | чипс WARN покрывает и `warn`, и `warning` (Ф-8) | unit | `pytest tests/test_services/test_loki_client.py -k level -x` | ❌ Wave 0 |
| ADMIN-09 | срабатывание потолка 200 названо, а не тихо обрезано | unit | `pytest tests/test_services/test_loki_client.py -k capped -x` | ❌ Wave 0 |
| ADMIN-10 | MRR не включает льготных (D-38) | unit | `pytest tests/test_application/test_admin_payments.py -k mrr -x` | ❌ Wave 0 |
| ADMIN-10 | `plan` не появляется в разметке журнала (D-42) | unit | `pytest tests/test_pages/test_admin_payments.py -k no_plan -x` | ❌ Wave 0 |
| ADMIN-11 | каждый из пяти признаков поднимается и **снимается** условием снятия (D-44) | unit | `pytest tests/test_application/test_incidents.py -x` | ❌ Wave 0 |
| ADMIN-11 | возраст залипшего платежа считается от `created_at`, не `confirmed_at` | unit | `pytest tests/test_application/test_incidents.py -k payment -x` | ❌ Wave 0 |
| CR-02 | код сброса берётся из `secrets`, а не `random` — **утверждение об ИСТОЧНИКЕ** (AST) | unit | `pytest tests/test_pages/test_reset_code_source.py -x` | ❌ Wave 0 |
| CR-03 | `secure` читается из настройки; в HTTP-режиме вход жив (Ф-9) | unit | `pytest tests/test_pages/test_cookie_flags.py -x` | ❌ Wave 0 |
| D-05 | ни один шаблон и ни один маршрут не ссылается на `groups-info` | unit | `pytest tests/test_pages/test_admin_panel.py -k groups_info_gone -x` | ❌ Wave 0 |

### Sampling Rate

- **На коммит задачи:** `uv run pytest tests/test_pages/test_admin_panel.py tests/test_services/ -x -q`
- **На слияние волны:** `just test` (полная суита, 895+ тестов на момент Фазы 2)
- **Ворота фазы:** полная суита зелёная перед `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_pages/test_admin_panel.py` — каркас шести подразделов, ADMIN-03
- [ ] `tests/test_pages/test_admin_users.py` — ADMIN-04
- [ ] `tests/test_pages/test_blocked_user.py` — ADMIN-05 / CR-01; **заменяет** `tests/test_admin.py:541`, чьё имя утверждает больше, чем тело проверяет
- [ ] `tests/test_pages/test_impersonation.py` + `test_impersonation_gate.py` — ADMIN-06 / D-23
- [ ] `tests/test_services/test_ops_state.py` — ADMIN-07 / ADMIN-08
- [ ] `tests/test_services/test_loki_client.py` — ADMIN-09
- [ ] `tests/test_application/test_queue_rows.py`, `test_incidents.py`, `test_admin_payments.py` — ADMIN-08 / ADMIN-10 / ADMIN-11
- [ ] `tests/test_pages/test_cookie_flags.py`, `test_reset_code_source.py` — CR-02 / CR-03
- [ ] Фикстуры-двойники Redis и Loki — §Pattern 7 ниже
- Установка фреймворка **не требуется**: `pytest`, `pytest-asyncio`, `aiosqlite` уже в dev-группе.

### Pattern 7 — как подменять Redis, Loki и Docker в суите (разрешение дискреции)

Прецеденты в проекте однозначны: **`unittest.mock.patch` по именованной точке модуля**, без новых пакетов.

- **Docker:** `@patch("app.services.wa_container_manager._get_docker_client")` — двадцать применений [VERIFIED: tests/test_wa_container_manager.py:22-23 и далее]. Именно поэтому в сервисе есть тонкая обёртка `_get_docker_client()` вместо прямого `docker.from_env()` в теле.
- **Redis:** `patch("app.services.billing_cache._get_redis", return_value=None)` и `return_value=<AsyncMock>` [VERIFIED: tests/test_billing_cache.py:45-52]. Форма даёт бесплатно и второй тест — «деградация без Redis».
- **Loki:** та же форма — `patch("app.services.loki_client._client")` либо `patch.object(httpx.AsyncClient, "get")`. Предпочесть первое: именованная точка стабильнее чужого API.

**Вывод:** новых dev-зависимостей (`fakeredis`, `respx`, `pytest-docker`) фаза не требует. Три новых сервиса обязаны иметь **ленивую именованную точку получения клиента** — не ради красоты, а ради проверяемости.

---

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1`, `security_block_on: "high"` [VERIFIED: .planning/config.json].

### Applicable ASVS Categories

| ASVS Category | Применима | Стандартный контроль в этой фазе |
|---------------|-----------|----------------------------------|
| **V2 Authentication** | **да** | CR-02: коды сброса из `secrets`, а не `random.randint` — четыре вхождения [VERIFIED: app/pages/auth.py:105, 250, 399, 538], `import random` на строке 1 и **ни одного другого применения `random.` в `app/`**. Утверждение обязано быть об **источнике** (AST: `import random` исчез из модуля), а не о значении: сгенерированное `random` неотличимо от сгенерированного `secrets` при взгляде на результат |
| **V3 Session Management** | **да** | CR-03 (`secure`, Ф-9) + HSTS; D-25 короткий `exp` = 60 мин на имперсонацию; Pitfall 9 — перезапись cookie, а не удаление; сегодня cookie ставится `httponly=True, samesite="lax"` **без** `secure` [VERIFIED: app/pages/auth.py:56, 341] |
| **V4 Access Control** | **да** | `require_admin` на всех шести маршрутах и всех действиях; D-20 `check_is_admin` по `act`; D-23 машинный гейт запретов; CR-01 на трёх путях. ⚠️ V4.2.2 (CSRF) — гард `is_same_origin` (`common.py`) сегодня имеют **ровно три** потребителя (форма покупки ×2 и повтор отправки); **новые изменяющие формы фазы 6 — «Перезапустить» (D-11), «Снять задачу» (D-17), вход под пользователем (D-19), блокировка — обязаны его получить**, иначе принятая граница риска расширяется молча |
| **V5 Input Validation** | **да** | `clean_choice(value, allowed)` над замкнутым множеством для всех фильтров; `Query(ge=…, le=…)` для страниц; ⚠️ **текст поиска в LogQL** — единственный вход фазы, уходящий в **чужой язык запросов**: кавычка внутри `\|= "…"` ломает синтаксис, поэтому экранирование обязательно (Пример 2) |
| **V6 Cryptography** | **да** | `python-jose` HS256 и `passlib[bcrypt]` — не трогать; `secrets` для кодов; **свои токены имперсонации не изобретать** — D-19 явно отверг вторую cookie и таблицу сессий |
| V7 Error Handling & Logging | **да** | D-24: `impersonation_start`/`impersonation_stop` именованными ключами с `admin_id` и `target_user_id`, форма — `free_access_toggled` [VERIFIED: app/pages/admin.py:576-581]. ⚠️ Цена названа: Loki опционален (D-28), при неподнятом мониторинге след остаётся только в stdout контейнера |
| V8 Data Protection | частично | «Логи» отдают строки логов приложения администратору — там могут быть email и идентификаторы. Приемлемо: аудитория — единственный администратор. **Не выводить в разметку `credentials`/`session_data` `MessengerAccount`** ни на одном подразделе |

### Known Threat Patterns

| Паттерн | STRIDE | Стандартная защита |
|---------|--------|--------------------|
| Забытая открытой чужая учётная запись | Spoofing | D-25: `exp` 60 мин + полоса возврата на **каждой** странице (`base.html`) |
| Необратимое действие от чужого имени (отправка, оплата, смена email) | Tampering / Repudiation | D-22 + D-23: зависимость на маршруте + AST-гейт, который краснеет на маршруте, добавленном будущей фазой без неё |
| Потеря следа имперсонации | Repudiation | D-24 structlog; ⚠️ принятый риск — Loki опционален |
| CSRF на новых POST-формах админки | Tampering | `is_same_origin(request)` — тот же гард, что у денежных форм; ⚠️ его названная граница: запрос **без обоих** заголовков (`Sec-Fetch-Site`, `Origin`) пропускается [VERIFIED: app/pages/common.py:333-370] |
| Инъекция в LogQL через поле поиска | Tampering | экранирование кавычки; текст только в `\|=`, не в селектор |
| Перечисление пользователей через админский поиск | Information Disclosure | `require_admin` на маршруте; ограничение страницы 50 (D-33) |
| Отказ раздела при недоступном Loki/Docker/Redis | DoS | таймауты + деградация (Пример 1); D-07 убирает Docker с пути рендера целиком |
| Неограниченный запрос по управляемому пользователем входу | DoS | D-33 (`limit` 50), D-29 (`limit` 200), `PAYMENT_LIST_CAP` = 200; сегодня `get_all_users()` **без предела** — это и есть исправляемый дефект |
| Предсказуемый код сброса пароля | Spoofing | CR-02: `secrets.randbelow` / `secrets.choice` |
| Cookie перехвачена по HTTP | Information Disclosure | CR-03 + HSTS; ⚠️ порядок D-50 и Ф-9 |
| Слепое доверие `X-Forwarded-For` | Spoofing | уже закрыто: `yookassa_webhook_client_ip_header = "X-Real-IP"` с объяснением [VERIFIED: app/config.py:88-107] — **не ослаблять** |

---

## Assumptions Log

| # | Утверждение | Раздел | Риск, если неверно |
|---|-------------|--------|--------------------|
| A1 | `structlog.stdlib.add_log_level` кладёт имя уровня в **нижнем регистре** (`warning`, а не `WARNING`) | Ф-8 | Селектор `{level=~"warn\|warning"}` не найдёт ничего; проверяется одним запросом к живому Loki за минуту |
| A2 | Метка `container_name` для `celery-worker-telegram` — compose-генерируемое имя, а не `celery-worker-telegram` | Ф-16 | Источник в фильтре «Логов» назван неверно; проверяется `docker ps --format '{{.Names}}'` на стенде |
| A3 | В проде `LOG_FORMAT=json` (в `.env` и `.env.example` — да [VERIFIED: .env:41, .env.example:32]); при `console` promtail JSON не разберёт и метки `level` не будет вовсе | Ф-8 | «Логи» без уровней; проверяется на стенде |
| A4 | Redis-сервер, обслуживающий прод, — тот же, что в `REDIS_URL` веб-процесса, то есть очереди воркеров видны из `web` | Pattern 3 | Подразделы «Воркеры»/«Очередь» пустые; проверяется `redis-cli KEYS 'wa:*'` на стенде |
| A5 | `ilike` на SQLite не складывает регистр для кириллицы | Pitfall 6 | Тест поиска ведёт себя иначе, чем предполагает план; проверяется одним тестом |
| A6 | Приоритеты Celery-задач в проекте не используются, поэтому `LLEN telegram` полон | Ф-13 | Недосчёт задач в плитке «Обзора»; закрывается тестом-запретом на `priority=` |
| A7 | Скалярный vs объектный `act` — форма выбирается планировщиком; RFC 8693 предписывает объект | Pattern 3 | Формально не-RFC токен (работать будет); решение записать явно |
| A8 | Один-единственный администратор (`settings.admin_email`) — модель не меняется | Security | Имперсонация на модель второго администратора не рассчитана; явно вынесено в Deferred |
| A9 | Порог «всплеска отказов» (D-45.3) в проекте **не объявлен** — единственная из пяти дискреционных величин, у которой нет готового значения | Pitfall/Discretion | Нужно назначить и объяснить; остальные четыре берутся из существующих объявлений (90 с, 24 ч, 200, 50) |

---

## Open Questions

1. **Куда именно вешать зависимость блокировки (Ф-4, Pattern 2)?**
   - Известно: `get_current_user_id` править нельзя (AST-тест), соседняя зависимость — отгруженный приём, `billing_router` объявлен «никогда не закрывается» и несёт вебхук ЮKassa.
   - Неясно: обязана ли блокировка закрывать оплату. Заблокированный, которому не дают заплатить, не может и разблокироваться самостоятельно — но самостоятельной разблокировки в продукте и нет.
   - **Рекомендация:** повесить на все API-роутеры, **кроме** `billing_router` и `auth_router`; расширить `test_access_gate.py` третьим объявленным множеством `BLOCK_CHECKED_API_ROUTERS`. Решение о `billing_router` вынести владельцу отдельным чекпойнтом — это денежный путь.

2. **Форма гейта запретов имперсонации: роутеры или маршруты (Pattern 4)?**
   - Известно: часть запретов D-22 (повтор отправки, смена пароля/email) живёт в роутерах, которые целиком запрещать нельзя.
   - **Рекомендация:** гибрид — пер-роутерная зависимость там, где роутер запрещён целиком, плюс объявленный перечень (модуль, имя обработчика) с AST-обходом декораторов `@router.post|put|delete` для остальных. Планировать отдельным планом.

3. **Порог «всплеска отказов» и его окно (A9)?**
   - Известно: `DEFAULT_WINDOW` модуля аналитики = сутки; D-45.3 говорит «за час»; `FAILED_STATUSES` объявлены.
   - Неясно: доля или абсолют, и от какого числа.
   - **Рекомендация:** доля `failed / total` за час при `total >= N` (иначе одна неудача из двух даст 50% и вечный инцидент); объявить оба числа константами рядом с признаком и назвать причину нижней границы `N`.

4. **Переносить ли `filter_chips` в `components/` (Ф-15)?**
   - **Рекомендация:** да, отдельной задачей с прогоном существующих тестов истории. Иначе админка получит чипсы, ведущие на `/history`, либо третью копию `base_path` в каждом вызове.

5. **Что показывать в колонке «Воркер» для Telegram (D-09)?**
   - Известно: TG-задачи идут в Celery-очередь `telegram`, отдельного контейнера на аккаунт нет, heartbeat отсутствует по устройству.
   - **Рекомендация (дискреция «в пуле app»):** подпись должна называть **проверяемую** вещь. «в пуле app» ничего не проверяет. Честнее — привязать TG-строку к **живости `celery-worker-telegram`** из верхнего инфраструктурного блока: тогда подпись отвечает на вопрос «есть ли кому забрать мою задачу». Планировщику решить, стоит ли это одной дополнительной величины.

---

## Project Constraints (from CLAUDE.md)

| Директива | Источник | Следствие для фазы |
|-----------|----------|--------------------|
| Стек: Python 3.12, FastAPI + SQLAlchemy async (PostgreSQL) + Celery/Redis + Jinja2 | `CLAUDE.md` §Project Overview | никакого SPA, никакого клиентского роутинга |
| Управление зависимостями — `uv`; команды — `just` | `CLAUDE.md` §Commands | `just add <pkg>`, `just test`, `just migrate`; в отчётах называть `just`-рецепты |
| Слои: `routes/` (JSON), `pages/` (HTML), `repositories/`, `services/`, `application/`, `domain/`, `infrastructure/` | `CLAUDE.md` §Architecture | новый код кладётся по слоям: чтение Redis/Loki → `services/`, вычисление инцидентов → `application/` |
| Тесты: `sqlite+aiosqlite:///:memory:`, полная схема на тест, фикстуры `client`/`db_session`/`auth_headers` | `CLAUDE.md` §Testing | всё, что фаза добавляет, обязано работать без Redis, Docker и Loki |
| Перед грепом по кодовой базе — `graphify query`; после правок — `graphify update .` | `CLAUDE.md` §graphify, `.claude/CLAUDE.md` | исполнителям: ориентироваться графом, `graphify update .` после правок |

---

## Redis Key Inventory

> Полная инвентаризация ключей, которые фаза читает. Собрана грепом по `app/`, `wa_worker/`, `max_worker/` и подтверждена чтением объявлений.

| Ключ | Тип | Писатель | Значение / TTL | Читатель в фазе 6 |
|------|-----|----------|----------------|-------------------|
| `wa:queue:{account_id}` | list | `dispatch_send_tasks` [VERIFIED: app/worker/tasks.py:108, 132] · ретрай `wa_worker` [VERIFIED: wa_worker/index.js:578, 584] | JSON-тело из 11 полей + `_retry_count`/`_delay_until` при ретрае | `LLEN`, `LRANGE`, `LREM` |
| `max:queue:{account_id}` | list | `dispatch_send_tasks` [VERIFIED: app/worker/tasks.py:147, 171] · ретрай `max_worker` [VERIFIED: max_worker/main.py:720] | то же, `_delay_until` **в секундах** | `LLEN`, `LRANGE`, `LREM` |
| `wa:heartbeat:{account_id}` | string | `wa_worker` каждые 30 с [VERIFIED: wa_worker/index.js:32, 965, 970] | epoch ms, **без TTL** | `MGET` + сравнение возраста |
| `max:heartbeat:{account_id}` | string | `max_worker` каждые 30 с [VERIFIED: max_worker/main.py:66-67, 792-798] | epoch ms, TTL 90 с | то же |
| `wa:endpoint:{account_id}` | string | `manage_wa_containers` `ex=420` [VERIFIED: app/worker/tasks.py:676] · `wa_worker` без TTL [VERIFIED: wa_worker/index.js:961] | URL контейнера | не читается фазой (heartbeat информативнее) |
| `max:endpoint:{account_id}` | string | `manage_max_containers` `ex=420` [VERIFIED: app/worker/tasks.py:713] | URL контейнера | не читается фазой |
| `wa:active_accounts` / `max:active_accounts` | set | `dispatch_send_tasks` `SADD`, `manage_*_containers` `SREM` [VERIFIED: app/worker/tasks.py:133, 172, 679, 718] | id аккаунтов с непустой очередью | опционально — перечень аккаунтов «в работе» |
| `wa:results` / `max:results` | list | воркеры `RPUSH`, `process_*_results` `LPOP` [VERIFIED: app/worker/tasks.py:741, 838] | результаты отправок | не читается фазой (D-15) |
| `telegram` | list (kombu) | `apply_async(queue="telegram")` [VERIFIED: app/worker/tasks.py:96-100] | kombu-конверт, base64 body | `LLEN` только (D-14); ⚠️ Ф-13 |
| `access:{user_id}` | string | `check_access_cached` `SETEX` [VERIFIED: app/services/billing_cache.py:68, 85-89] | вердикт доступа, TTL `billing_cache_ttl = 60` | не трогать (D-31) |

---

## Sources

### Primary (HIGH confidence) — исходники, прочитанные в этой сессии

- `app/dependencies.py` · `app/services/auth_service.py` · `app/pages/common.py` · `app/pages/admin.py` · `app/pages/auth.py` · `app/pages/__init__.py` · `app/main.py` · `app/config.py` · `app/constants.py` · `app/logging_config.py`
- `app/models/{user,subscription,payment,send_log,messenger_account}.py` · `app/repositories/user.py`
- `app/application/analytics/send_analytics.py` · `app/application/billing/subscription_period.py` · `app/application/scheduling/use_cases.py` · `app/application/accounts/use_cases.py`
- `app/services/{billing_cache,payment_service,wa_container_manager,max_container_manager,subscription_service}.py` · `app/worker/{tasks,celery_app}.py`
- `wa_worker/index.js` · `max_worker/main.py`
- `app/templates/{base.html,components/*,history/list.html,history/includes/filter_chips.html}`
- `tests/conftest.py` · `tests/test_pages/test_access_gate.py` · `tests/test_billing_cache.py` · `tests/test_wa_container_manager.py` · `tests/test_application/test_no_metering_remains.py`
- `monitoring/{promtail.yml,loki.yml,prometheus.yml}` · `docker-compose.{prod,monitoring}.yml` · `nginx/{nginx.conf.template,nginx-http.conf.template}` · `justfile` · `pyproject.toml`
- `.venv/lib/python3.12/site-packages/kombu/transport/redis.py` (установленная версия — источник истины по `_q_for_pri`)
- `design/new_broadcaster_design.unpacked.html` (строки ~1021–1300 — вкладки, «Обзор», «Пользователи», «Воркеры», «Очередь», «Логи», «Платежи»)
- `.planning/{REQUIREMENTS.md,STATE.md,config.json}` · `.planning/phases/06-admin-panel/06-CONTEXT.md` · `.planning/todos/pending/blocked-user-can-still-log-in.md`

### Secondary (MEDIUM confidence) — Context7, официальные репозитории

- `/grafana/loki` — `GET /loki/api/v1/query_range` (параметры `query`/`start`/`end`/`limit`/`direction`, наносекундные строки), форма ответа `{status, data:{resultType, result:[{stream, values}]}}`, официальный python-пример на `httpx`, синтаксис селекторов и line-фильтров LogQL
- `/redis/redis-py` — `redis.asyncio.from_url`, `decode_responses`, `pipeline()`, `mget`
- `/celery/kombu` — Redis-транспорт: очередь как список, `PRIORITY_STEPS`, `sep`, `_q_for_pri`, `_size()` через сумму `LLEN`

### Tertiary (LOW confidence) — WebSearch, требует подтверждения

- RFC 8693 §4.1 `act` claim: объектная форма, вложенность как цепочка делегирования, правило «потребитель учитывает только верхнеуровневые claims и текущего актора» — [rfc-editor.org/rfc/rfc8693](https://www.rfc-editor.org/info/rfc8693/), [zitadel.com/docs/guides/integrate/token-exchange](https://zitadel.com/docs/guides/integrate/token-exchange)
- OWASP по имперсонации: отсутствие следа даёт скрытые действия и разорванный аудит; сессии уникальны на пользователя — [cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [owasp.org/www-project-citizen-development-top10-security-risks](https://owasp.org/www-project-citizen-development-top10-security-risks/content/2022/en/CD-SEC-02-Account-Impersonation). ⚠️ Прямых предписаний OWASP про короткий `exp` у admin-login-as-user **не найдено** — D-25 остаётся решением владельца, а не отраслевой нормой

---

## Metadata

**Confidence breakdown:**
- Standard Stack: **HIGH** — новых пакетов нет, все восемь читаны в `pyproject.toml`
- Внутрипроектные факты (Ф-4 … Ф-10, Redis Key Inventory, пороги): **HIGH** — каждое утверждение подтверждено чтением исходника с указанием строк
- Loki / kombu / redis-py контракты: **MEDIUM** — Context7 на официальных репозиториях; kombu дополнительно сверен с **установленной** копией в `.venv`
- RFC 8693 и практики имперсонации: **LOW** — WebSearch, официальный текст RFC не открывался построчно
- Pitfalls: **HIGH** для 1–4, 7, 9–12 (из исходников); **MEDIUM** для 5–6, 8 (поведенческие свойства SQLite/Loki, не проверенные прогоном)

**Research date:** 2026-08-21
**Valid until:** 2026-09-20 (30 дней — стек проекта зафиксирован, внешних быстро движущихся зависимостей фаза не добавляет; при выкате мониторинга или смене `promtail.yml` перепроверить Ф-8 и Ф-16)
