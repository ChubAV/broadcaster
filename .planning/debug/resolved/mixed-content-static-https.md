---
slug: mixed-content-static-https
status: resolved
trigger: "после сборки контейнеров не загружаются js и css на страницу Mixed Content: The page at 'https://broadcaster.all-torgi.ru/dashboard' was loaded over HTTPS, but requested an insecure stylesheet 'http://broadcaster.all-torgi.ru/static/css/app.css?v=1786285264'. This request has been blocked; the content must be served over HTTPS. dashboard:1 Mixed Content: ... insecure script 'http://broadcaster.all-torgi.ru/static/js/htmx.min.js?v=1786285264' ... dashboard:1 Mixed Content: ... insecure script 'http://broadcaster.all-torgi.ru/static/js/alpine.min.js?v=1786285264' ..."
created: 2026-08-10
updated: 2026-08-10
---

# Debug Session: mixed-content-static-https

## Symptoms

- **Expected behavior:** Страницы, отданные по HTTPS, ссылаются на статику по HTTPS (`https://broadcaster.all-torgi.ru/static/...`); CSS и JS загружаются, дашборд отрисовывается со стилями и работающими htmx/alpine.
- **Actual behavior:** HTML-страница отдаётся по HTTPS, но URL-ы статики в разметке сгенерированы со схемой `http://`. Браузер блокирует их как Mixed Content — страница без стилей и без JS.
- **Error messages (verbatim, browser console):**
  ```
  Mixed Content: The page at 'https://broadcaster.all-torgi.ru/dashboard' was loaded over HTTPS,
  but requested an insecure stylesheet 'http://broadcaster.all-torgi.ru/static/css/app.css?v=1786285264'.
  This request has been blocked; the content must be served over HTTPS.
  dashboard:1 Mixed Content: ... insecure script 'http://broadcaster.all-torgi.ru/static/js/htmx.min.js?v=1786285264' ...
  dashboard:1 Mixed Content: ... insecure script 'http://broadcaster.all-torgi.ru/static/js/alpine.min.js?v=1786285264' ...
  ```
- **Timeline:** Раньше по HTTPS всё работало. Сломалось после внесения последних изменений в код и последующей пересборки/деплоя контейнеров. Регрессия.
- **Reproduction:** Открыть `https://broadcaster.all-torgi.ru/dashboard` в браузере с открытой консолью → в консоли три Mixed Content ошибки, страница без стилей.

## Environment notes

- TLS терминируется nginx-контейнером из репозитория (`nginx/` — HTTPS template), проксирует на uvicorn/FastAPI.
- Cache-busting query `?v=1786285264` присутствует — значит URL статики генерируется кодом/шаблоном, а не захардкожен.

## Current Focus

- bug_class: Bohrbug (детерминированная — воспроизводится на каждом запросе за TLS-прокси)
- hypothesis: `url_for('static', ...)` строит АБСОЛЮТНЫЙ URL из `scope["scheme"]`.
  `scope["scheme"]` за прокси выставляет `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware`,
  но только если IP клиента входит в `forwarded_allow_ips`. uvicorn запускается без
  `--forwarded-allow-ips`, дефолт — `127.0.0.1`; nginx в Docker подключается с адреса
  bridge-сети (172.x.x.x) → `X-Forwarded-Proto: https` молча отбрасывается →
  scheme остаётся `http` → Mixed Content.
- test: собрать ASGI-стек как в проде (`ProxyHeadersMiddleware` поверх `create_app()`),
  запрос с client=172.20.0.7 и `X-Forwarded-Proto: https`, сравнить рендер при
  `trusted_hosts="127.0.0.1"` и `trusted_hosts="*"`.
- expecting: при `127.0.0.1` — `http://.../static/...` (баг воспроизведён), при `*` — `https://...`.
- next_action: НЕТ — сессия закрыта. Правка применена, guardrail пройден
  (TDD RED→GREEN, 4 мутанта, дельта регрессии 0), пользователь подтвердил работу на проде 2026-08-10.

### reasoning_checkpoint

```yaml
hypothesis: "Статика уезжает на http://, потому что uvicorn не доверяет X-Forwarded-Proto от nginx (forwarded_allow_ips по умолчанию 127.0.0.1, а nginx приходит с docker-bridge IP), и одновременно шаблоны перешли на url_for('static'), который клеит абсолютный URL из scope[scheme]"
confirming_evidence:
  - "nginx/nginx.conf.template:63 — X-Forwarded-Proto $scheme проставлен во ВСЕХ location HTTPS-сервера; на стороне nginx всё корректно"
  - "docker-compose.prod.yml:69 — command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 — ни --proxy-headers, ни --forwarded-allow-ips; grep по FORWARDED_ALLOW_IPS по всему репозиторию не находит ничего"
  - "uvicorn 0.41.0: Config.__init__ → proxy_headers=True, но forwarded_allow_ips=None → os.environ.get('FORWARDED_ALLOW_IPS', '127.0.0.1'); Config.load → ProxyHeadersMiddleware(app, trusted_hosts=self.forwarded_allow_ips)"
  - "app/main.py — своего ProxyHeadersMiddleware / ForwardedProto-мидлвари нет, RequestIdMiddleware схему не трогает"
  - "Хост в битых URL корректный (broadcaster.all-torgi.ru), сломана ТОЛЬКО схема. Это ровно сигнатура работающего proxy_set_header Host + отброшенного X-Forwarded-Proto"
  - "git show 150ea44 -- app/templates/base.html: до коммита ассеты грузились с CDN по ЖЁСТКО зашитым https:// (cdn.tailwindcss.com, unpkg.com, fonts.googleapis.com); коммит заменил их на url_for('static', ...) — то есть на scheme-зависимый абсолютный URL"
falsification_test: "Если при trusted_hosts='*' и том же X-Forwarded-Proto: https рендер всё равно даёт http:// — гипотеза неверна, схема берётся не из ProxyHeadersMiddleware"
fix_rationale: "Чиним причину, а не симптом: возвращаем uvicorn доверие к прокси, после чего верной становится схема во ВСЁМ scope, а не только в трёх тегах base.html. Правка шаблонов на root-relative URL замаскировала бы неверный scope[scheme], который в будущем всплывёт в редиректах, secure-cookie и ссылках в письмах."
blind_spots:
  - "Не проверено на живом проде — подтверждение мидлвари получено локально на том же uvicorn 0.41.0, что и в образе (uv.lock)"
  - "Подсеть docker-сети broadcaster не фиксирована (bridge выдаёт её динамически), поэтому точный CIDR указать нельзя — отсюда выбор '*'"
candidate_causes:
  - "config: uvicorn запущен без --forwarded-allow-ips (категория: конфигурация запуска) — ПОДТВЕРЖДЕНО"
  - "code: base.html/auth_base.html перешли на url_for('static'), scheme-зависимый абсолютный URL (категория: код) — ПОДТВЕРЖДЕНО"
  - "config: nginx не шлёт X-Forwarded-Proto (категория: конфигурация прокси) — ОПРОВЕРГНУТО, заголовок на месте"
  - "environment: TLS терминируется где-то выше nginx и до него доходит http (категория: окружение) — ОПРОВЕРГНУТО, nginx сам слушает 443 ssl с сертификатом Let's Encrypt"
and_gate: "yes — нужны ОБА условия одновременно. Недоверие к X-Forwarded-Proto существовало и раньше, но было латентным: ассеты шли с CDN по зашитому https. Переход на url_for('static') сам по себе тоже безвреден при корректном scope[scheme]. Mixed Content возникает только на пересечении."
```

## Evidence

- checked: `app/templates/base.html:11-13`, `app/templates/auth_base.html:23-25`
  found: ассеты подключаются через `{{ url_for('static', path='...') }}?v={{ asset_version }}`.
  implication: URL генерируется Starlette из ASGI scope, значит схема берётся из `scope["scheme"]`, а не из разметки.

- checked: `git log`/`git show 150ea44 -- app/templates/base.html`
  found: до коммита 150ea44 («feat(01-01): end-to-end shell slice») в `<head>` стояли внешние CDN-ссылки с жёстко зашитым `https://` (cdn.tailwindcss.com, unpkg.com/htmx, unpkg.com/alpinejs, fonts.googleapis.com). Коммит удалил CDN и смонтировал свою статику через `url_for`.
  implication: найден момент регрессии. Раньше схема ассетов не зависела от scope — поэтому баг конфигурации прокси не проявлялся.

- checked: `nginx/nginx.conf.template`
  found: в HTTPS-сервере (`listen 443 ssl`) во всех трёх location проставлены `proxy_set_header Host $host` и `proxy_set_header X-Forwarded-Proto $scheme` (строки 38-41, 53-55, 60-63).
  implication: nginx НЕ виноват — заголовок отправляется. Гипотеза «nginx не шлёт X-Forwarded-Proto» опровергнута.

- checked: `docker-compose.prod.yml:69` и `docker-compose.yml:25`
  found: `command: uv run uvicorn main:app --host 0.0.0.0 --port 8000` — без `--proxy-headers` и без `--forwarded-allow-ips`. `grep -rn "FORWARDED\|proxy-headers\|forwarded"` по yml/sh/Dockerfile/py/toml — ноль совпадений. В `entrypoint.sh` тоже ничего.
  implication: доверенный список прокси остаётся дефолтным.

- checked: uvicorn 0.41.0 (установленная версия), `Config.__init__`, `Config.load`, `ProxyHeadersMiddleware.__init__`
  found: `proxy_headers=True` по умолчанию (мидлварь ПОДКЛЮЧЕНА), но `forwarded_allow_ips=None` → `os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")`; `Config.load` делает `ProxyHeadersMiddleware(app, trusted_hosts=self.forwarded_allow_ips)`; конструктор мидлвари по умолчанию тоже `trusted_hosts="127.0.0.1"`.
  implication: мидлварь работает, но доверяет ТОЛЬКО 127.0.0.1. nginx в Docker — отдельный контейнер в сети `broadcaster`, его адрес 172.x.x.x, а не loopback. Заголовок отбрасывается молча, без единой строчки в логах.

- checked: `app/main.py::create_app`
  found: смонтирован `StaticFiles(..., name="static")`, из мидлварей только `RequestIdMiddleware`; ни `ProxyHeadersMiddleware`, ни собственной обработки `X-Forwarded-Proto` нет.
  implication: перезаписать схему в приложении некому — единственная точка контроля это флаг запуска uvicorn.

- checked: сигнатура битого URL из отчёта: `http://broadcaster.all-torgi.ru/static/css/app.css?v=...`
  found: домен верный, сломана только схема.
  implication: `Host` доходит (nginx `proxy_set_header Host $host`), а `X-Forwarded-Proto` — нет. Ровно то, что предсказывает гипотеза; вариант «TLS терминируется выше и до nginx идёт http» этим же и опровергается (тогда бы и `$scheme` в nginx был http, но nginx сам держит `listen 443 ssl` с сертификатом).

- checked: `grep -rn "url_for\|base_url\|request.url" app/`
  found: `url_for` используется ТОЛЬКО в `base.html` и `auth_base.html` для статики. `return_url` для YooKassa берётся из настроек (`app/services/payment_service.py:39`), а не из запроса.
  implication: радиус поражения сейчас ограничен статикой — это объясняет, почему остальное приложение по HTTPS внешне «работает».

## Eliminated

- hypothesis: nginx не передаёт `X-Forwarded-Proto` в HTTPS-сервере
  evidence: `nginx/nginx.conf.template` — заголовок стоит во всех location (строки 41, 55, 63)
  timestamp: 2026-08-10

- hypothesis: TLS терминируется выше по стеку, и до nginx запрос доходит уже по http
  evidence: nginx сам слушает `443 ssl` с сертификатом Let's Encrypt (`nginx.conf.template:21-25`), то есть `$scheme` внутри HTTPS-сервера равен `https`
  timestamp: 2026-08-10

- hypothesis: uvicorn вообще не подключает ProxyHeadersMiddleware, потому что не передан `--proxy-headers`
  evidence: в uvicorn 0.41.0 `proxy_headers` по умолчанию `True` — мидлварь подключена всегда; проблема не в её отсутствии, а в `trusted_hosts`
  timestamp: 2026-08-10

- hypothesis: схему ломает жёстко зашитый `http://` где-то в разметке или в настройках
  evidence: в шаблонах нет литерала `http://` для статики, URL целиком генерируется `url_for`; cache-buster `?v=` подтверждает генерацию
  timestamp: 2026-08-10

## Resolution

- root_cause: (AND-gate, нужны оба условия)
  1. uvicorn запускается без `--forwarded-allow-ips`, поэтому его `ProxyHeadersMiddleware` доверяет только `127.0.0.1`; nginx приходит с IP docker-сети (172.x.x.x), его `X-Forwarded-Proto: https` молча отбрасывается и `scope["scheme"]` остаётся `http`;
  2. коммит 150ea44 заменил CDN-ссылки с зашитым `https://` на `url_for('static', ...)`, который строит абсолютный URL из этой самой схемы.
- fix: в `docker-compose.prod.yml` команда сервиса `web` дополнена флагом
  `--forwarded-allow-ips=*` (+ комментарий, объясняющий почему это не CIDR и почему это безопасно).
  Шаблоны НЕ трогались: правится причина (неверный `scope["scheme"]`), а не симптом (три тега в `<head>`).
  Значение `*` вместо диапазона — подсеть docker bridge-сети назначается динамически, зашитый CIDR
  однажды разойдётся с реальностью и молча вернёт тот же баг. Безопасно, потому что порт 8000 в проде
  не публикуется (`expose`, не `ports`), единственный вход — nginx, и `grep` подтверждает, что
  `request.client` в `app/` не используется ни для одного решения (нет IP-авторизации и rate-limit по IP).
- verification:
  - автоматическая — см. `### fix_acceptance_guardrail` ниже (5 сигналов, все pass);
  - на живом проде — ПОДТВЕРЖДЕНО пользователем 2026-08-10 после
    `docker compose -f docker-compose.prod.yml up -d web`: статика грузится по `https://`,
    консоль браузера чистая, Mixed Content ушёл, стили и htmx/alpine работают.
    Последний blind spot («не проверено на живом проде») тем самым закрыт.
- files_changed:
  - `docker-compose.prod.yml` — `--forwarded-allow-ips=*` в команде `web`
  - `tests/test_pages/test_https_asset_scheme.py` — новый файл, 6 регрессионных тестов

### tdd_checkpoint

```yaml
test_file: "tests/test_pages/test_https_asset_scheme.py"
red_run: "4 failed, 2 passed"
red_failure_output: |
  AssertionError: Mixed Content: ['http://broadcaster.all-torgi.ru/static/css/app.css?v=1786285264',
  'http://broadcaster.all-torgi.ru/static/js/htmx.min.js?v=1786285264',
  'http://broadcaster.all-torgi.ru/static/js/alpine.min.js?v=1786285264']
red_fidelity: "RED воспроизвёл симптом ДОСЛОВНО — те же три URL и тот же cache-buster ?v=1786285264, что и в консоли браузера у пользователя"
green_run: "6 passed"
status: "green"
```

### fix_acceptance_guardrail

```yaml
signal_1_regression_test_flips:
  result: pass
  detail: "RED 4 failed / 2 passed → GREEN 6 passed. Изменён только docker-compose.prod.yml."
signal_2_mutation_at_fix_site:
  result: pass
  detail: |
    M1 удалить флаг (точный откат)          → KILLED (4 failed)
    M2 сузить до 127.0.0.1                  → KILLED (4 failed)
    M3 правдоподобный, но неверный CIDR 10.0.0.0/8 → KILLED (3 failed: контракт деплоя проходит,
       но три поведенческих теста падают — ради этого доверенный список и читается из компоуза)
    M4 та же величина через пробел (`--forwarded-allow-ips *`) → SURVIVED, и это ВЕРНО:
       эквивалентный мутант, конфигурация семантически идентична (парсер флага в тесте
       обрабатывает обе формы).
signal_3_revert_restores_bug:
  result: pass
  detail: "M1 = точный откат правки, баг возвращается (те же три http://-URL)."
signal_4_regression_suite:
  result: pass
  detail: |
    Полный прогон `uv run pytest tests/` после правки: 624 passed, 25 failed, 3 errors (12m03s).
    Падения ПРЕДСУЩЕСТВУЮЩИЕ и к правке отношения не имеют — проверено прямым сравнением:
    подмножество из четырёх падающих файлов (test_sync_groups, test_tg_user_auth, test_uploads,
    test_wa_sync_status) даёт ОДИН И ТОТ ЖЕ результат «22 failed, 8 passed, 3 errors» и с правкой,
    и на восстановленном чистом дереве (флаг откачен, новый тест-файл убран). Дельта = 0.
    Механизма влияния и нет: правка трогает только docker-compose.prod.yml, который читает
    единственный модуль — новый tests/test_pages/test_https_asset_scheme.py.
signal_5_not_symptom_masking:
  result: pass
  detail: |
    Диff не удаляющий и не маскирующий: добавлен флаг, чинящий scope["scheme"] для ВСЕГО
    приложения. Альтернатива «переписать url_for на root-relative /static/…» отклонена
    осознанно — она убрала бы симптом, оставив scope["scheme"] == "http" и отложив тот же
    дефект до первого редиректа, secure-cookie или абсолютной ссылки в письме.
    Граничный тест test_plain_http_request_still_emits_http_assets страхует от обратной
    крайности — жёстко зашитого https.
guardrail_verdict: accepted
```

### Проверено дополнительно

- `nginx/nginx-http.conf.template` — в HTTP-only режиме `X-Forwarded-Proto $scheme` тоже проставлен; править нечего.
- `docker compose -f docker-compose.prod.yml config` — Compose разбирает команду в отдельный аргумент `--forwarded-allow-ips=*`; звёздочка доезжает литералом (glob не раскрывается: `entrypoint.sh` делает `exec "$@"` уже над готовыми токенами), YAML-алиасом не считается.
- `docker-compose.yml` (dev) намеренно не тронут: в dev-стеке nginx нет вообще, а порт 8000 публикуется на хост — расширять там доверие к прокси незачем. Прод поднимается только через `-f docker-compose.prod.yml` (`justfile:71-125`).
- `grep -rn "request.client\|client.host" app/` — пусто, IP клиента не участвует ни в одном решении; поэтому `*` не открывает вектор через подделку `X-Forwarded-For`.

## Blameless postmortem

**Почему не поймали раньше (без обвинений — вопрос к системе гейтов, а не к людям).**

Гейта для этого класса дефектов **не существовало**. Весь тестовый набор поднимает ASGI-приложение
напрямую через `httpx.AsyncClient`, без `ProxyHeadersMiddleware` и без прокси-топологии прода.
В таком стеке `scope["scheme"]` всегда корректен, поэтому дефект был структурно ненаблюдаем в CI:
никакой объём тестов на `app/` не мог его поймать, потому что ломается не приложение, а граница
«nginx → uvicorn», которую тесты не пересекали. Отсюда и латентность: недоверие к
`X-Forwarded-Proto` жило в конфиге давно, но проявилось только когда коммит `150ea44` сделал
разметку зависимой от схемы.

Второй усилитель — **тишина отказа**. uvicorn отбрасывает недоверенный `X-Forwarded-Proto`
без единой строчки в логах. Ни warning, ни debug: сигнал теряется молча, и обнаружить его
можно было только по симптому в браузере.

**Установленный guard:** `tests/test_pages/test_https_asset_scheme.py` — собирает ASGI-стек
как в проде (`ProxyHeadersMiddleware` поверх `create_app()`) и делает запрос с client-IP из
docker-подсети. Ключевая деталь: доверенный список **читается прямо из `docker-compose.prod.yml`**,
а не дублируется в тесте. Поэтому дрейф деплой-конфига (удаление флага, сужение до `127.0.0.1`,
правдоподобный, но неверный CIDR) валит тест — это подтверждено мутантами M1–M3.
Граничный тест `test_plain_http_request_still_emits_http_assets` страхует от обратной крайности —
жёстко зашитого `https`.

**Prevention (одной строкой):** why not caught: none (no gate existed for this class — tests never
crossed the nginx→uvicorn proxy boundary, and uvicorn drops an untrusted `X-Forwarded-Proto`
silently); guard: `tests/test_pages/test_https_asset_scheme.py`, which asserts asset scheme behind
a simulated prod proxy and reads the trusted-host list from `docker-compose.prod.yml` so deploy-config
drift fails the suite.
