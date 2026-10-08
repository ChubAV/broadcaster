# Phase 7: Обновление htmx до 2.0.10 и блок конфигурации — Pattern Map

**Mapped:** 2026-08-27
**Files analyzed:** 7 (1 бинарная замена, 1 новый шаблон, 2 правки шеллов, 1 правка Python, 2 тестовые поверхности)
**Analogs found:** 6 / 7

⚠️ **Читать первым: §Inventory Corrections.** Числа D-14/D-18 в CONTEXT.md (`revealed` = 10, `every Ns` = 10) не совпадают с кодом. Гейт, написанный по CONTEXT.md, будет красным в момент написания.

## File Classification

| Новый/изменяемый файл | Роль | Data flow | Ближайший аналог | Match |
|---|---|---|---|---|
| `app/static/js/htmx.min.js` | vendored asset | file-I/O (статика) | — (нет аналога: единственная бинарная замена) | none |
| `app/templates/includes/htmx_config.html` | template partial (`{% include %}`) | request-response (рендер) | `app/templates/includes/messenger_icon.html` — **частичный** (это макрос, не include) | partial |
| `app/templates/base.html` (стр. 25) | shell template | request-response | `app/templates/auth_base.html:24` (построчный близнец) | exact |
| `app/templates/auth_base.html` (стр. 24 + инлайн `<script>`) | shell template | request-response | `app/templates/base.html:16-27` | exact |
| `app/pages/common.py::_compute_asset_version()` | utility / config | file-I/O → module-level constant | `app/pages/common.py:142-154` (сам себя: правится на месте) | exact |
| `tests/test_pages/test_shell.py` | test (поведенческий, HTTP) | request-response | `test_shell.py:27-70` + `test_https_asset_scheme.py:63-80` | exact |
| инвентарные гейты D-09 / D-18 | test (source-reading gate) | batch/transform по исходникам | `tests/test_templates/test_components.py:740-1015, 1190-1215` | exact |

---

## Inventory Corrections (снято по коду 2026-08-27)

**D-18 (22 места `hx-get`).** Сумма 22 верна. **Разбивка по механизмам — нет.**

| Механизм | CONTEXT.md | Факт по коду |
|---|---|---|
| `hx-trigger="revealed"` + `hx-swap="outerHTML"` | 10 | **12** |
| `hx-trigger="every Ns"`, атрибуты безусловные | 10 | **8** |
| атрибуты собраны Jinja-условием `{% if status == 'syncing' %}` | 2 | **2** ✔ |
| **Итого** | 22 | **22** ✔ |

Полный перечень (файл:строка), пригодный к дословному переносу в гейт и в `07-UAT.md`:

**Механизм 1 — infinite scroll, `hx-trigger="revealed"` (12):**
```
account_groups/partial_cards.html:17      account_groups/list.html:190
ads/partial_cards.html:7                  ads/list.html:61
schedules/partial_cards.html:7            schedules/list.html:61
history/partial_cards.html:6              history/list.html:121
admin/history_partial_cards.html:7        admin/user_history.html:63
accounts/partial_cards.html:139           accounts/list.html:195
```
Пары «list + partial_cards» — одна и та же разметка в двух местах; UAT по механизму обходит 6 экранов, а не 12 строк.

**Механизм 2 — поллинг, `hx-trigger="every Ns"`, безусловный (8):**
```
dashboard.html:135                 (every {{ feed_poll_seconds }}s, hx-swap по умолчанию)
admin/workers.html:42              (every {{ workers_poll_sec }}s)
accounts/list.html:70              (every 5s, outerHTML)
accounts/partial_cards.html:35     (every 5s, outerHTML)
accounts/connect_wa.html:34, :45   (every 3s, innerHTML — ДВА места в одном файле)
accounts/connect_max.html:47, :58  (every 3s, innerHTML — ДВА места в одном файле)
```

**Механизм 3 — атрибуты внутри Jinja-условия (2):**
```
account_groups/partials/sync_result.html:50    {% if status == 'syncing' %} hx-get … hx-trigger="every 5s" {% endif %}
accounts/partials/sync_status_card.html:47     {% if status == 'syncing' %} hx-get … hx-trigger="every 5s" {% endif %}
```

**Ловушка счёта, которую гейт обязан пережить.** `grep hx-trigger="revealed"` даёт **13** попаданий, а не 12: тринадцатое — комментарий `base.html:241` («View Transitions отключены: при infinite scroll (`hx-trigger="revealed"`) вызывали мерцание»). Гейт обязан считать **места с `hx-get`**, а не вхождения строки `revealed`, иначе он зелен на 13 по совпадению. Прецедент того же класса решения — `_macro_calls()` в `test_components.py:868-875`, где объявление макроса сознательно исключено из счёта вызовов.

**D-09 (охват glob).** Проверено: `app/static/**/*.css` + `app/static/**/*.js` находит сегодня **ровно три** файла — `css/app.css` (159 142 Б), `js/htmx.min.js` (47 755 Б), `js/alpine.min.js` (43 441 Б). Ожидание CONTEXT.md подтверждено.

**Вендоренный файл.** `version:"1.9.10"`, 47 755 Б — исходное состояние критерия 1 подтверждено.

**Мест `{{ asset_version }}` в шаблонах — 6.** Совпадает с CONTEXT.md; правка функции их не трогает.

---

## Pattern Assignments

### `app/templates/includes/htmx_config.html` (NEW, template partial)

**Аналог — частичный.** `app/templates/includes/messenger_icon.html` — единственный житель каталога, но он **макрос** (`{% macro messenger_icon(...) %}`, подключается `{% from %}`), а не include. То есть `htmx_config.html` будет **первым настоящим `{% include %}` проекта**. Копировать оттуда следует не механизм, а **шапку-обоснование**: файл открывается комментарием `{# … #}`, объясняющим ПОЧЕМУ файл существует и как подключается — и последняя строка комментария дословно называет способ подключения:

```jinja
{# Иконка мессенджера. Собственных utility-классов не несёт НИ ОДНА ветка,
   … (обоснование) …
   Импорт: {% from "includes/messenger_icon.html" import messenger_icon %} #}
```
(`app/templates/includes/messenger_icon.html:1-9`)

**Что копировать:** ту же форму шапки, с заменой последней строки на `Подключение: {% include "includes/htmx_config.html" %}`, плюс запись причины единственности блока (D-01) и причины склейки meta+script в один файл (D-02).

**Содержимое блока** берётся дословно из `.planning/research/SUMMARY.md` §«Обязательный блок конфигурации», строки 236-251 — шесть ключей, пять правил `responseHandling` в порядке `204` → `[23]..` → `422` → `[45]..` → `...`.

**Тег htmx, переезжающий в этот файл, копируется байт-в-байт** из `base.html:25` / `auth_base.html:24`:
```jinja
<script src="{{ url_for('static', path='/js/htmx.min.js') }}?v={{ asset_version }}"></script>
```
⚠️ Форма `url_for('static', path=…)` обязательна и не подлежит упрощению до литерала `/static/…`: на ней стоит весь `test_https_asset_scheme.py` (абсолютный URL со схемой из `X-Forwarded-Proto`).

**Совместимость с существующим сборщиком ссылок — проверено.** `ASSET_REF_RE` (`test_https_asset_scheme.py:39`) применяется к **отрендеренному HTML** (`response.text`), а не к исходнику шаблона:
```python
ASSET_REF_RE = re.compile(r'<(?:script|link)\b[^>]*?(?:src|href)="([^"]+)"', re.I)
BLOCKED_ASSETS = ("/static/css/app.css", "/static/js/htmx.min.js", "/static/js/alpine.min.js")

def static_asset_refs(html: str) -> list[str]:
    return [ref for ref in ASSET_REF_RE.findall(html) if "/static/" in ref]
```
(`test_https_asset_scheme.py:39-64`)
Перенос тега в include **не ломает** этот сбор: после рендера тег стоит там же. Единственное реальное условие — include обязан попасть в `<head>` **обоих** шеллов, иначе `assert_assets_use` (:76-80) покраснеет на `/login` или на `/dashboard` с внятным текстом «нет ссылки … среди …». Это бесплатный второй сторож забытого include.

⚠️ Инлайн-`<script>` очистки `localStorage` (D-11) **не несёт `src=`**, поэтому `ASSET_REF_RE` его не видит и в `refs` он не попадает. Безопасно.

---

### `app/templates/base.html:25` и `app/templates/auth_base.html:24` (shell templates)

**Аналог — друг друга.** Два `<head>` совпадают построчно, подтверждено чтением:

`base.html:16-27` (идентично `auth_base.html:14-27`, отличается только комментарной шапкой файла):
```jinja
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#08080b">
    <meta name="color-scheme" content="dark">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>{% block title %}Broadcaster{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', path='/css/app.css') }}?v={{ asset_version }}">
    <script src="{{ url_for('static', path='/js/htmx.min.js') }}?v={{ asset_version }}"></script>
    <script defer src="{{ url_for('static', path='/js/alpine.min.js') }}?v={{ asset_version }}"></script>
</head>
```

**Правка:** строка `<script src=…htmx…>` в обоих файлах заменяется на `{% include "includes/htmx_config.html" %}`. `<link>` на CSS и тег Alpine остаются на месте (D-02). Позиция include — там же, где стоял тег htmx: между `<link>` и Alpine. Это автоматически удовлетворяет требованию «конфиг выше рантайма», потому что внутри include порядок задан.

**Стиль комментария — обязателен, прецедент в этих же файлах.** `base.html:1-11` и `auth_base.html:1-12` открываются развёрнутыми `{# … #}`, объясняющими ПОЧЕМУ, и — важная деталь стиля — **фиксируют отменённые утверждения**: «Прежняя редакция этого объяснения называла импорт единственным — утверждение снято, потому что перестало быть верным» (`base.html:9-11`). Инлайн-`<script>` в `auth_base.html` обязан нести такой же комментарий: это единственный инлайн-JS проекта и названное отступление от рамки вехи (D-11).

**Второй прецедент в `base.html`, который планировщик должен знать (D-16):**
```html
<!-- View Transitions отключены: при infinite scroll (hx-trigger="revealed") вызывали мерцание и рывки скролла -->
```
(`base.html:241`) — проект **уже** ловил каскадное/рывковое поведение на `revealed` и лечил его выключением, а не конфигом. Прямо подтверждает запасной план D-17 и служит записанным прецедентом, если каскад воспроизведётся.

**Почему очистка именно в auth-шелле (D-11) — цепочка подтверждена:**
- `app/pages/auth.py:429-437` — `@router.get("/logout")` → `RedirectResponse(url="/login", 302)` + `clear_session_cookie`.
- Вызовы: `base.html:189` (`<a class="user-logout" href="/logout">ВЫЙТИ</a>`) и `base.html:205` (`<a class="tab-item" href="/logout">Выйти</a>`).
Обе — обычные `<a href>`, то есть полная навигация на `/login` под `auth_base.html`. Строка очистки исполняется гарантированно.

**Единственный сегодняшний источник снимков истории** — `app/pages/ads.py:517-523`:
```python
    if is_htmx:
        response = await _autosave_response(request, db, settings, user, ad)
        if created:
            # D-03: браузер подменяет адрес без перезагрузки — дальнейшие
            # автосохранения уходят уже на маршрут редактирования.
            response.headers["HX-Push-Url"] = f"/ads/{ad.id}/edit"
        return response
```
Фазой не трогается; приведено как обоснование того, что снимки уже лежат у существующих пользователей.

---

### `app/pages/common.py::_compute_asset_version()` (utility, file-I/O)

**Аналог — текущая редакция самой функции**, `app/pages/common.py:142-154`:
```python
def _compute_asset_version() -> str:
    """Return a cache-busting suffix for /static links.

    Хешей в именах файлов нет и build-шаг запрещён (D-02), поэтому версия
    берётся от времени изменения app.css и считается один раз при импорте.
    """
    try:
        return str(int((_static_dir / "css" / "app.css").stat().st_mtime))
    except OSError:
        return "dev"


templates.env.globals["asset_version"] = _compute_asset_version()
```

**Что сохраняется дословно:**
- сигнатура `-> str` и вызов на импорте, значение — строка (D-08);
- `try/except OSError` → `"dev"` (единственная деградация; при переходе на glob+хеш `OSError` по-прежнему возможен на `read_bytes()`);
- докстринг, объясняющий ПОЧЕМУ (build-шаг запрещён), — обязан быть переписан под новое основание, а не оставлен старым;
- `_static_dir` (`common.py:32`) — уже существующая база пути, новый путь не заводится.

**Модульное ограничение, которое нельзя нарушить.** `common.py:137-140`:
```python
# Безопасный дефолт на импорте: имена существуют с пустым базовым URL, и НИ
# ОДНОГО конструирования Settings на импорте модуля не происходит.
_bind_image_url_globals("")
```
Прецедент `bind_image_url_globals(settings)` (:129-135) показывает **разрешённый** способ получить настройки — отложенным вызовом из `create_app`. Для `asset_version` он не нужен (D-08: флаг `debug` недостижим и не используется), но если план соблазнится на dev-режим — это единственная допустимая форма, и она стоит рядом.

**Соседний прецедент регистрации глобала с обоснованием** — `common.py:157-165` (`AD_STATUS_DRAFT` и т.д.): комментарий на 8 строк объясняет, почему значение доезжает глобалом, а не параметром макроса, и заканчивается строкой «Конструирования Settings здесь не происходит: значения — модульные константы». Новая версия `asset_version` обязана нести такую же закрывающую строку.

**Импорт `hashlib` — новый** (`grep hashlib app/pages/common.py` → 0). Ставится в stdlib-блок `common.py:1-5` (`pathlib`, `datetime`, `decimal`, `urllib.parse`, `zoneinfo` — алфавитный порядок соблюдается).

---

### `tests/test_pages/test_shell.py` (behavioural test, request-response)

**Аналог — соседние тесты того же файла**, `test_shell.py:27-70`.

**Идиома «статика отдаётся»** (:36-42) — прямая заготовка для утверждения версии и SHA-384:
```python
@pytest.mark.asyncio
async def test_static_js_served(client: AsyncClient):
    for path in ("/static/js/htmx.min.js", "/static/js/alpine.min.js"):
        response = await client.get(path)
        assert response.status_code == 200, path
        # Вендоренные рантаймы: htmx ~47.7 КБ, Alpine ~43.4 КБ
        assert len(response.content) > 10_000, path
```
⚠️ **Комментарий «htmx ~47.7 КБ» устареет** (47 755 → 51 238). Это не тест, а запись факта — но проект держит комментарии правдивыми (см. `base.html:9-11`), и план обязан его поправить.

**Идиома «файл на диске через `Path` + `parents[2]`»** (:47-55) — форма для D-04 (чтение байтов вендоренного файла и SHA-384), позволяющая не тянуть HTTP:
```python
    fonts_dir = Path(__file__).resolve().parents[2] / "app" / "static" / "fonts"
    files = sorted(fonts_dir.glob("*.woff2"))
    assert len(files) >= 18
    for path in files:
        …
        assert response.content[:4] == b"wOF2", path.name
```
`response.content[:4] == b"wOF2"` — прямой прецедент «утверждаем БАЙТЫ артефакта, а не имя». D-04 — тот же ход, усиленный до полного хеша. Тот же `glob` — прецедент для D-09.

**Идиома «утверждение по содержимому отданного ресурса + отрицательные утверждения»** (:58-69, `test_app_css_declares_fonts`): позитивные `assert token in body, token` в цикле, затем негативные `assert "fonts.googleapis.com" not in body`. Для D-13 (греп-гейт единственности строки очистки) это модель: утверждается наличие **и** отсутствие второй копии — `html.count("removeItem('htmx-history-cache')") == 1`.

**Идиома «отрендеренный HTML под обоими шеллами» (для D-05)** — берётся не отсюда, а из `test_https_asset_scheme.py:152-170`: два теста-близнеца, один на `/login` (auth-шелл), другой на `/dashboard` после `_login()` (основной шелл), с явной подписью-меткой в assert-сообщении:
```python
async def test_auth_page_behind_tls_proxy_emits_https_assets(behind_proxy):
    """auth_base.html: /login отдан по HTTPS → статика тоже по HTTPS."""
    …
async def test_shell_page_behind_tls_proxy_emits_https_assets(behind_proxy):
    """base.html: именно /dashboard из отчёта о баге."""
```
D-05 копирует ровно эту пару: страница под `base.html` + страница под `auth_base.html`, `content=` вытаскивается, `json.loads`, шесть ключей и **индексы** правил `responseHandling`. Для основного шелла в `test_shell.py` уже есть фикстура `authed_client` (:75) — второй логин-хелпер не нужен.

---

### Инвентарные гейты D-09 и D-18 (source-reading tests)

**Аналог — `tests/test_templates/test_components.py`**, а не `test_access_gate.py`. CONTEXT.md называет `ROW_DELETE_PLACES = 12` / `MODAL_PLACES = 16` — обе константы физически живут в `test_components.py` (:755 и :850), и `MODAL_PLACES` сегодня **= 18**, а не 16. `test_access_gate.py` / `test_impersonation_gate.py` — это гейты множеств по AST **Python**; для разметки нужен именно `test_components.py`.

**Помощник обхода шаблонов** (`test_components.py:856-865`) — копируется дословно:
```python
def _all_templates() -> list[tuple[str, str]]:
    """Все шаблоны проекта парами «путь относительно app/templates — исходник»."""
    return [
        (path.relative_to(TEMPLATES_DIR).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    ]
```
⚠️ `rglob`, не `glob` — прецедент рекурсивного обхода записан и в `test_impersonation_gate.py:61-65` как исправленная граница («плоский обход каталогов не увидел бы роутер в подкаталоге»). Для D-18 это критично: 8 из 22 мест живут в подкаталогах `partials/` и `includes/`.

**Помощник счёта, исключающий объявление** (`test_components.py:868-875`) — модель для отсечения комментария `base.html:241`:
```python
def _macro_calls(source: str, macro_name: str) -> int:
    """Число ВЫЗОВОВ макроса. Объявление вызовом не считается.

    Наивный поиск по имени нашёл бы объявление в самом компоненте и объявил бы
    библиотеку своим же потребителем.
    """
```

**Форма записи перечня — именованный кортеж мест с ожидаемым числом на каждое** (`test_components.py:740-755`), это лучшая заготовка для D-18 «числом по трём механизмам»:
```python
ROW_DELETE_SITES = (
    RowDeleteSite("accounts/list.html", r"/accounts/[^\"]+/delete", 3),
    RowDeleteSite("accounts/partial_cards.html", r"/accounts/[^\"]+/delete", 3),
    …
)

ROW_DELETE_PLACES = 12
```
и **двойное утверждение** — сначала перечень против суммы, потом перечень против исходников (`test_components.py:1005-1015`):
```python
    assert sum(site.forms for site in ROW_DELETE_SITES) == ROW_DELETE_PLACES, (
        "перечень строчных удалений разошёлся с числом мест"
    )

    offenders = {}
    for site in ROW_DELETE_SITES:
        source = _template_source(site.template)
        forms = _delete_forms_in(source, site.action_pattern)
        if len(forms) != site.forms:
            offenders[site.template] = (
                f"форм удаления {len(forms)}, ожидалось {site.forms} "
```
Первое утверждение ловит расхождение внутри самого теста, второе — расхождение теста с кодом. D-18 обязан нести оба, иначе перечень механизмов и число 22 разъедутся молча.

**Форма сообщения об отказе** (`test_components.py:1211-1214`) — копируется буквально, вплоть до формулировки:
```python
    assert places == MODAL_PLACES, (
        f"мест подтверждения {places}, ожидалось {MODAL_PLACES} — место молча "
        "исчезло или появилось незаявленное"
    )
```
Для D-09 та же форма: `f"glob охвата нашёл {found}, ожидалось {ASSET_GLOB_FILES} — вендоренный файл появился мимо расчёта версии либо охват опустел"`.

**Комментарий-летопись над константой** (`test_components.py:757-800`) — принятая в проекте форма: каждое изменение числа сопровождается записью «План NN-MM добавил/снял N-е место, потому что …», включая признание не сбывшегося прогноза («Ожидание плана 03-05 “16 → 15” не сбылось… Число проверено счётом по файлам, а не перенесено из прогноза»). D-18 обязан открыть такую летопись — и **первой записью зафиксировать поправку 10/10/2 → 12/8/2** из §Inventory Corrections, а не тихо выписать верные числа.

---

## Shared Patterns

### Комментарий объясняет ПОЧЕМУ, включая отменённые утверждения
**Источник:** `app/templates/base.html:1-11`, `app/pages/common.py:137-140` и `:157-165`, `tests/test_pages/test_access_gate.py:1-27`, `tests/test_templates/test_components.py:757-800`
**Применять к:** всем новым файлам и всем правкам фазы.
Три подформы, все с прецедентом: (1) докстринг файла-гейта выписывает, ЧЕГО гейт не видит (`test_impersonation_gate.py:43-65`); (2) снятое утверждение объявляется снятым, а не удаляется (`base.html:9-11`); (3) число в тесте сопровождается летописью изменений.

### Перечень выписан в тесте, а не выведен из проверяемого
**Источник:** `tests/test_pages/test_access_gate.py:41-52`
```python
# РОУТЕРЫ, КОТОРЫЕ ЗАКРЫВАЕТ ИСТЁКШИЙ ДОСТУП. Перечень выписан ЗДЕСЬ, а не
# выведен из исходника: тест, выводящий ожидание из проверяемого, согласился бы
# с любой правкой. Изменение этого множества обязано быть решением, записанным
# в двух местах сразу.
GATED_ROUTERS = { … }
```
**Применять к:** D-04 (константа SHA-384), D-09 (три имени файлов охвата), D-18 (три числа механизмов). Ни одно из них не вычисляется из проверяемого артефакта.

### Утверждение по байтам, а не по имени
**Источник:** `tests/test_pages/test_shell.py:55` (`assert response.content[:4] == b"wOF2"`)
**Применять к:** D-04. Прецедент того, что проект уже проверяет подлинность вендоренного артефакта содержимым.

### Ссылка на статику строится через `url_for`
**Источник:** `app/templates/base.html:24-26`; сторож — `tests/test_https_asset_scheme.py:63-80`
**Применять к:** тегу htmx внутри нового include. Литерал `/static/…` уронит четыре теста Mixed Content.

---

## No Analog Found

| Файл | Роль | Data flow | Причина |
|---|---|---|---|
| `app/static/js/htmx.min.js` | vendored asset | file-I/O | Замена вендоренного рантайма в проекте происходит впервые; аналога процедуры нет. Единственная опора — числа: 47 755 → 51 238 Б, `version:"1.9.10"` → `version:"2.0.10"`, SHA-384 `H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V`. |
| инлайн-`<script>` в `auth_base.html` (D-11) | shell inline JS | event-driven (исполнение на загрузке) | **Первый инлайн-`<script>` проекта** — прецедента нет ни в одном из 79 шаблонов. Смежное действующее правило v2.0, которому он обязан подчиняться: «сборка узлами DOM, не строкой» (`innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write` = 0) — `removeItem` его не нарушает. Обёртка `try/catch` (приватный режим браузера бросает на `localStorage`) отдана на усмотрение плана (§Claude's Discretion). |
| `07-UAT.md` | документ ручного обхода | — | Артефактов ручного UAT в каталогах фаз нет; форма задаётся планом. Содержимое — три механизма из §Inventory Corrections. |

---

## Metadata

**Область поиска аналогов:** `app/templates/**` (79 шаблонов), `app/pages/common.py`, `app/pages/{ads,auth}.py`, `tests/test_pages/{test_shell,test_access_gate,test_impersonation_gate,test_https_asset_scheme}.py`, `tests/test_templates/test_components.py`, `app/static/**`
**Файлов прочитано целиком или прицельно:** 11
**Дата извлечения:** 2026-08-27
