# Phase 17: Показ номера на всех экранах - Pattern Map

**Mapped:** 2026-11-20
**Files analyzed:** 29 (новые и правимые, без шаблонов-однострочников; их перечень — в 17-RESEARCH.md §1, §13)
**Analogs found:** 28 / 29 (у прохода по отрисованным экранам `tests/test_pages/test_account_label_sweep.py` точного аналога нет)

*Ревизия 2026-11-20 (проверка планов, ревизия 1):* прежняя единая запись «адресные тесты по всем
экранам» заменена именами модулей, которые реально создают планы: адресные тесты разнесены по планам
17-02…17-07 (один файл на четыре параллельных плана второй волны пересекался бы по
`files_modified`), проход — отдельный модуль плана 17-09; добавлены строки загрузчика
`app/application/accounts/labels.py`, его теста и общего модуля `tests/account_label_support.py`.

Все названные пути — отслеживаемые git исходники (проверено `git ls-files`; зеркал `.gsd/capabilities` среди них нет). Номера строк сняты с дерева ветки `gsd/phase-16-…`. Перепись мест `#id` (19 мест, 12 шаблонов) и замеры не выводятся заново — см. 17-RESEARCH.md §1–§13.

## File Classification

| Новый/правимый файл | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `app/services/account_label.py` (новый) | utility (чистое правило) | transform | `app/services/schedule_rules.py` (нейтральный модуль, шапка-обоснование) + `app/services/phone.py:391` (`format_phone`) | role-match |
| `app/pages/common.py` (+глобалы `phone_labels` / `phone_label`) | config (глобал Jinja) | request-response | `app/pages/common.py:320-327` (`messenger_labels`) | exact |
| `app/templates/components/account_label.html` (новый) | component (макрос) | transform | `app/templates/components/mono.html` | exact |
| `app/application/accounts/dto.py` (`SyncStatusView`) + `use_cases.py:58-66` | model (DTO) | request-response | сам файл, `dto.py:16-31` | exact |
| `app/pages/accounts.py` (`:137`, `:183`, `:1011`) | controller (страницы) | request-response, polling | `accounts_sync_status` (`:1011-1040`) и `retry_availability` (карта) | exact |
| `app/pages/account_groups.py`, `app/pages/history.py`, `app/pages/admin.py` (контекст подписи, карта по пользователю) | controller | request-response | `app/pages/history.py:456-472` (`retry_availability`) | role-match |
| `app/pages/history.py` (`EXPORT_HEADER`, `export_row`, `history_export`) | utility + controller (CSV) | streaming | сами `export_cell`/`export_row` (`:236`, `:265`) | exact |
| шаблоны `accounts/*`, `account_groups/list.html`, `ads/includes/sched_card.html`, `history/*`, `admin/*` (19 мест) | component (шаблон) | request-response | `sched_card.html:63-82` (макрос подписи + `panel_text`), `mono.html` | role-match |
| `tests/test_services/test_account_label.py` (новый) | test (unit, таблица) | transform | `tests/test_services/test_phone.py` | exact |
| `tests/test_templates/test_account_label_gate.py` (новый) | test (грep-гейт) | batch | `tests/test_templates/test_htmx_markup_security.py` + `test_htmx_markup_gates.py:1073-1125,342-360` | exact |
| `tests/test_pages/test_account_label_accounts.py` (новый, план 17-02) | test (интеграция, адресные) | request-response, polling | `tests/test_pages/test_responsive_markup.py:115-123,1090-1102` | role-match |
| `tests/test_pages/test_account_label_groups.py` (новый, 17-03) | test (интеграция, адресные) | request-response | `tests/test_pages/test_responsive_markup.py:1090-1102`; `tests/test_pages/test_account_groups.py:1815-1845` | role-match |
| `tests/test_pages/test_account_label_history.py` (новый, 17-04) | test (интеграция, адресные) | request-response | `tests/test_pages/test_responsive_markup.py:1090-1102`; `tests/test_pages/test_history.py:79` (`_seed_account_with_group`) | role-match |
| `tests/test_pages/test_account_label_admin.py` (новый, 17-05) | test (интеграция, адресные) | request-response | `test_admin_panel.py:92-112` (`_row_markup`), `:1190-1240` (фальшивки Redis) | role-match |
| `tests/test_pages/test_account_label_admin_history.py` (новый, 17-07) | test (интеграция, адресные) | request-response | `test_admin_panel.py:92-112`; `tests/test_pages/test_history.py:79` | role-match |
| `tests/test_pages/test_account_label_sweep.py` (новый, 17-09) | test (интеграция, проход по результату) | request-response | точного аналога нет — см. «No Analog Found» | none |
| `tests/account_label_support.py` (новый, 17-01) — общий посев аккаунта с номером через писателя и разбор адресов `data-account-label` | test (хелпер) | CRUD + transform | `tests/test_application/test_account_phone_writer.py:46-57` + `fill_reported_phone`; `tests/conftest.py:268-315` (`seed_group` — общий помощник, ввоз `from tests.conftest import …`) | role-match |
| `app/application/accounts/labels.py` (новый, 17-01) — `load_account_rows` | service (загрузчик) | CRUD (чтение) | `app/pages/history.py:456-472` (`retry_availability`) | role-match |
| `tests/test_application/test_account_label_rows.py` (новый, 17-01) | test (интеграция, БД) | CRUD | `tests/test_pages/test_history_retry.py:1742-1776` (счёт запросов `before_cursor_execute`) | role-match |
| `tests/test_pages/test_history_export.py` (правки позиций, ячейка «Номер») | test | streaming | сам файл | exact |
| переписанные утверждения `test_responsive_markup.py:1100`, `test_editor_schedules.py:1336`, `test_admin_panel.py:102,287,387,554,588` | test | request-response | сами строки | exact |
| `app/static/css/app.css` + правила чтения CSS | config + test | — | `test_responsive_markup.py:3440-3460` | role-match |
| артефакт обхода человека (засев D-21) | records | — | обход Фазы 16 (`.planning/phases/16-*`) | см. RESEARCH §10 |

## Pattern Assignments

### `app/services/account_label.py` (utility, transform)

**Аналог:** `app/services/schedule_rules.py` (шапка «модуль нейтрален», чистые функции, без БД и Jinja) и `app/services/phone.py:391-404`.

**Правило, которое нельзя нарушить** — `format_phone` принимает строку, а `None`/`''`/пробелы пропускает как есть (`format_phone(None)` → `None`). Отсечь ДО вызова (RESEARCH «Адресаты», `:398-400` docstring):

```python
def format_phone(stored: str) -> str:
    number = _parse_or_none(stored, None)
    if number is None:
        return stored          # неразбираемое — КАК ЕСТЬ (D-06)
    return phonenumbers.format_number(number, PhoneNumberFormat.INTERNATIONAL)
```

**Источник слов канала** (`app/constants.py:42-46`) — не заводить второй словарь:

```python
MESSENGER_LABELS: dict[str, str] = {"tg_user": "Telegram", "wa": "WhatsApp", "max": "MAX"}
```

**Каркас** (RESEARCH §5): `@dataclass(frozen=True, slots=True) class AccountLabel(account_id, channel, phone_text|None, twin)` + свойства `text`, `plain`, `plain_with_id` (админ, D-17); `build_labels(rows) -> dict[int, AccountLabel]`; ключ двойника — `(type, готовая подпись после format_phone)`; «неизвестен» = `None`, `''`, пробельная строка. Незнакомый `type` — как есть, как в CSV: `MESSENGER_LABELS.get(t, t)`. `Markup` и `|safe` недопустимы (`MARKUP_BUILDERS = 0`).

---

### `app/pages/common.py` (глобал, request-response)

**Аналог:** `app/pages/common.py:320-327` — абзац-обоснование + присваивание в `templates.env.globals`:

```python
# Подписи каналов доезжают до шаблонов тем же способом и по той же причине:
# ... импортированным макросам Jinja контекст вызывающего не передаёт ...
templates.env.globals["messenger_labels"] = MESSENGER_LABELS
```

Копировать форму: абзац «почему глобал» + одна строка присваивания; глобал — тонкая обёртка над чистой функцией, **без сессии БД** (`test_shell.py:973`, `test_impersonation.py:945` стерегут отсутствие чтений в шелле). Имя — **не** `account_label` (затеняется макросом `sched_card.html:63` и `{% set %}` в `account_groups/list.html:15`); брать `phone_label`.

---

### `app/templates/components/account_label.html` (component, transform)

**Аналог:** `app/templates/components/mono.html` (весь файл):

```jinja
{# Mono-метка (D-13, D-14) — ...
   Импорт: {% from "components/mono.html" import mono %} #}

{% macro mono(text, variant='muted', upper=false, title=None) -%}
<span class="mono mono--{{ variant }}{% if upper %} mono--upper{% endif %}"{% if title %} title="{{ title }}"{% endif %}>{{ text }}</span>
{%- endmacro %}
```

Требования `test_components.py` (`:834-861`): файл начинается с `{#`, содержит `{% macro `, без `with context`, без `|safe`/`Markup(`. Разметка — только `<span data-account-label="{{ label.account_id }}">` (не `<div>`: `_row_markup` в `test_admin_panel.py:92-112` режет строку воркера по первому `</div>`). Внутри — `mono(label.text, …)` и при `label.twin` (или `always_id` для админа) `mono('#' ~ label.account_id, 'muted')`. Это единственное разрешённое место печати `#` перед id аккаунта (исключение №3 реестра гейта).

---

### `app/application/accounts/dto.py` + `use_cases.py` (DTO)

**Аналог:** `app/application/accounts/dto.py:16-31` — `@dataclass(slots=True) class SyncStatusView: status: str; messenger_type: str | None = None`; четыре конструктора `use_cases.py:58,61,64,66`:

```python
if account.status == "syncing":
    return SyncStatusView(status="syncing", messenger_type=account.type)
```

Правка: добавить поле `phone: str | None = None` (умолчание — прежние вызовы не ломаются; импортов в `tests/` нет), заполнять `phone=account.phone` в четырёх конструкторах. Докстринг класса уже объясняет, почему лишних полей нет, — дописать причину нового поля тем же тоном. Двойник — по карте пользователя в обработчике, не в DTO.

---

### `app/pages/accounts.py` (controller, request-response + polling)

**Аналог:** сам `accounts_sync_status` (`:1011-1040`); отдельный `.render(...)` без объекта аккаунта — самое опасное место (мягкий `Undefined` печатает пустоту):

```python
view = await get_sync_status_view(db, user.id, account_id)
...
html = templates.env.get_template("accounts/partials/sync_status_card.html").render(
    account_id=account_id, status=view.status, messenger_type=view.messenger_type,
    user=user, stats=stats,
)
```

Правка: передать ОБЪЕКТ подписи (`label=`), а не россыпь переменных — обращение к полю несуществующего объекта падает громко. Карта по пользователю — один запрос (см. ниже). Для `accounts_list`/`accounts_partial` передать в `list.html` и `partial_cards.html` **одно имя ключа** (`test_accounts_three_files_*`, `test_responsive_markup.py:3006-3140`); `components/modal.html` не должен появиться в `sync_status_card.html` (`:3056`). Правки — контекст и ввоз, без перестройки обработчиков (Фаза 18 сходится в тот же файл). Один план правит файл.

---

### Загрузчик карты «аккаунты пользователя»: `app/application/accounts/labels.py` (`load_account_rows`, 17-01; тест — `tests/test_application/test_account_label_rows.py`), вызовы из accounts.py / account_groups.py / history.py / admin.py

**Аналог:** `app/pages/history.py:456-472` (`retry_availability`):

```python
account_ids = {group.account_id for _log, group in candidates if group and group.account_id}
account_status: dict[int, str] = {}
if account_ids:
    account_status = {
        row_id: status
        for row_id, status in (
            await db.execute(
                select(MessengerAccount.id, MessengerAccount.status).where(
                    MessengerAccount.id.in_(account_ids),
                    MessengerAccount.user_id == user_id,
                )
            )
        ).all()
    }
```

Отличие: условие **`user_id == user.id` без `IN (id порции)`** — карта по пользователю, иначе признак двойника у порции будет свой (D-14). Проекция трёх колонок `select(MessengerAccount.id, MessengerAccount.type, MessengerAccount.phone)` (не `list_by_user`: он поднимет `credentials`/`session_data`). **Не расширять `retry_availability`** (`test_history_retry.py:1742-1776`, `len(statements) <= 2`) — отдельная функция. Где все аккаунты уже загружены (`history.py:1115-1118`, `admin.py:1350,1466`, `ads.py:389-405`) — запроса не добавлять, строить `build_labels` по загруженному. Четыре сборщика словаря `logs` (`history.py:606,1103`, `admin.py:1457,1551`) — **одной общей функцией**.

---

### `app/pages/history.py` — CSV (`export_row`, `EXPORT_HEADER`) (streaming)

**Аналог:** `history.py:228-296` — `export_cell` и `export_row`:

```python
return [
    export_cell(format_datetime_for_user(log.sent_at, user)),
    export_cell(MESSENGER_LABELS.get(log.messenger_type, log.messenger_type)),
    export_cell(group.account_id if group else None),
    export_cell(log.group_name),
    ...
]
```

Правка: именованный параметр с умолчанием `export_row(log, group, user, *, phone: str | None = None)` (иначе краснеют 11 прямых вызовов); ячейка: нет группы → `""`, номер неизвестен → `""`, иначе `export_cell(format_phone(stored).removeprefix("+"))` — именно `removeprefix`, не `lstrip` (`++5`). Всё проходит `export_cell` без исключений (D-09). «Номер» ставить **после «Аккаунт»** (индекс 2 не сдвигается; цена — позиции `row[5]` в 3 тестах + `len(EXPORT_HEADER)`). Карта читается **до** `db.stream(query)` и до `StreamingResponse(` (`test_export_cap_is_checked_before_the_streaming_response`, `:693`). Отступления D-09/D-16 записать докстрингом `export_row` — ни один тест их не стережёт.

---

### Шаблоны: подпись в трёх формах приёмника

**Аналог:** `ads/includes/sched_card.html:63-82` — макрос подписи, печатаемый трижды, и `parts.append(…) | trim` с `join(' · ')`:

```jinja
{% macro account_label(account) -%}
{{- {'tg_user': 'Telegram', 'wa': 'WhatsApp', 'max': 'MAX'}.get(account.type, account.type) }} #{{ account.id -}}
{%- endmacro %}
...
{%- if account %}{% set _ = parts.append(account_label(account) | trim) %}{% endif -%}
```

Правило: разметка (`<span data-account-label>`) — чипы, карточки, шапки; **плоская строка** `label.plain` — `<title>`, `<option>` (`account_options` пары `(value, label)`, `history/list.html:46`, `admin/user_history.html:27`), `title=`, `body=` модалки (`components/modal.html:814`), звено `join`. Локальный словарь и макрос `account_label` удалить; двойника в расписании вычислять по списку `accounts` внутри макроса (`_editor_context` не менять). В Alpine/`hx-vals`/`hx-on` подпись не попадает. Админ: `#id` всегда (D-17), `#id` воркера остаётся отдельным `<span>` с текстом ровно `#N` (`test_admin_panel.py:102`) и ссылкой. `history_card` общий для пользователя и админа — явный параметр аудитории. Устаревшую прозу `account_groups/list.html:31-37` («Телефона в строке нет и быть не может») исправить.

---

### `tests/test_services/test_account_label.py` (unit, табличный)

**Аналог:** `tests/test_services/test_phone.py` (чистые функции, `pytest.mark.parametrize`, без БД). Таблица: `None` / `''` / `'   '` / разбираемый / неразбираемый (`abc`, `=1+1`, `<b>x</b>`) / два аккаунта без номера (оба двойники) / два с равным номером в разной записи (`+79991234567` и `+7 999 123-45-67`) / TG+WA с одним номером (не двойники) / уникальный номер (нет `#id`) / незнакомый `type`.

---

### `tests/test_templates/test_account_label_gate.py` (грep-гейт, batch)

**Аналоги:** `test_htmx_markup_security.py:207-261` (источники словарём, `_strip_comments`, ключ `rel#ordinal`) и `test_htmx_markup_gates.py:1073-1125,342-360` (реестр с причинами + отдельная константа числа + `_all_templates(directory)`).

```python
def _template_sources() -> dict[str, str]:
    return {path.relative_to(TEMPLATES_DIR).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(TEMPLATES_DIR.rglob("*.html"))}
...
body = _strip_comments(source)           # из tests/test_templates/test_htmx_inventory.py
for ordinal, (_position, description) in enumerate(sorted(hits)):
    found[f"{rel}#{ordinal}"] = description
```

```python
MACRO_DEFINITION_SITES_DECLARED = 2   # число исключений — ОТДЕЛЬНОЙ литеральной константой с летописью
```

Форма: классы К1 `['"][^'"]*#\s*['"]` и К2 `#\s*\{[{%]` (после вырезания комментариев); реестр исключений с причиной (два `group_external_id` — адресовать **вхождение**, не файл; сам `components/account_label.html`); число объявлено литералом; **контроли подложенной строкой** (`{{ mono('#' ~ account.id) }}`, `Аккаунт #{{ acc.id }}`) и «вселенная непуста»; по образцу `test_pages/test_htmx_gates.py:872` (`NOT_YET_CONVERTED_COUNT`, `test_the_backlog_never_grows`) — реестр «ещё не переведено» убывает по планам до 0 в последнем (выбор «гейт в первой волне с реестром» либо «гейт в последнем плане» — за планировщиком). Урок Фазы 16: запрещать **класс**, остаток закрывает проход по результату, а не перечень написаний.

---

### Адресные модули экранов: `tests/test_pages/test_account_label_accounts.py` (17-02), `test_account_label_groups.py` (17-03), `test_account_label_history.py` (17-04), `test_account_label_admin.py` (17-05), `test_account_label_admin_history.py` (17-07) (адресные, request-response)

**Аналоги (общие для пяти модулей):** `test_responsive_markup.py:115-123` (посев `_seed_account(db, type_)` — в планах заменён общим `seed_account` из `tests/account_label_support.py`), `:1090-1102` (утверждение по `authed_client.get("/accounts")`), `test_admin_panel.py:92-112` (`_row_markup` — адресация ячейки; админские модули ввозят фальшивки Redis из `tests.test_pages.test_admin_panel`, прецедент ввоза — `test_confirmation_panel_settle.py:57`). Разбор — `html.parser` из стандартной библиотеки (функции `label_texts`, `id_mark_texts`, `muted_label_ids`, `element_text`, `option_texts`, `title_text` общего модуля), не подстрока (`#1` входит в `#10`). Для каждого экрана и фрагмента (порция `/accounts/partial`, опрос `/accounts/{id}/sync-status`, группы: `<h1>`, `<h2>`, `<title>`, чипы, модалка `#acc-del-<id>-text`, порция истории, админская порция, `<option>`) сверять **полный** текст `[data-account-label="<id>"]`. Нужные состояния: с номером, без номера, двойники без номера, двойники с равным номером, уникальный номер, запись без аккаунта (D-15). Один модуль на план — а не один на фазу: планы 17-02…17-05 идут одной волной.

### `tests/test_pages/test_account_label_sweep.py` (17-09, проход по результату)

Проход «уникальный id 7311 не встречается в текстовых узлах и текстовых атрибутах вне объявленных адресов» — **аналога нет** (см. «No Analog Found»); идейные опоры — RESEARCH §7 п.6 и разбор `html.parser` общего модуля.

---

### `tests/account_label_support.py` (17-01) — помощник посева аккаунта с номером и разбор адресов (тесты)

**Аналог:** `tests/test_application/test_account_phone_writer.py:46-57` (`_seed_account`) + писатель Фазы 16:

```python
account = MessengerAccount(user_id=user.id, type="tg_user", credentials="creds", status="active")
db_session.add(account); await db_session.commit(); await db_session.refresh(account)
```

Номер ставить **только писателем** `fill_reported_phone(session, account_id, raw)` / `set_manual_phone` (`app/application/accounts/phone.py:148,216`), не прямым присваиванием `account.phone` — иначе краснят гейты `test_phone_single_writer_gate.py` и `test_phone_privacy_gate.py` (D-08: называть их в каждом плане). Одна общая функция в общем модуле тестов вместо пятой копии `_seed_account`.

---

### `tests/test_pages/test_history_export.py` (правки)

Позиции `row[5]` → новый индекс в `:257,:269,:465`, `len(EXPORT_HEADER) == 9` в `:88-91`, дописать `row[4]` в `:200`, ячейку «Номер» в `:130` (`test_export_cell_defuses_a_formula_in_every_value_bearing_column`) — D-05 «без исключений». Новое утверждение: ячейка без `+` и обезвреженное неразбираемое значение (таблица §6).

---

## Shared Patterns

### Данные из глобала, разметка из макроса
**Источник:** `app/pages/common.py:320-327` + `components/mono.html`. **Применять:** все 19 мест. Из Python разметку не отдавать (`MARKUP_BUILDERS = 0` — `test_htmx_markup_security.py:129`; `UNSAFE_MARKERS` — `test_components.py:861`).

### Номер из колонки — недоверенная строка
**Источник:** автоэкранирование окружения (`autoescape=True`) на HTML-приёмниках; `export_cell` (`history.py:236`) на CSV. **Применять:** все приёмники подписи; в `hx-vals`/`hx-on`/Alpine подпись не класть.

### Условие владения в запросе карты
**Источник:** `history.py:456-472` (`MessengerAccount.user_id == user_id`). **Применять:** каждый загрузчик карты (`user_id == user.id`; админская порция — по просматриваемому пользователю).

### Названные гейты в каждом плане
Называть явно: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py` (путь — по `git ls-files`), а также `test_htmx_post_pairs`, `test_responsive_markup`, `test_components`, `test_htmx_markup_security` (память проекта: исполнители пропускают сквозные гейты). Число объявленных констант (`POST_PAIR_CASES_DECLARED = 77` и т.п.) не сдвигается без записи в летопись.

### Порядок волн
`common.py` + `account_label.py` + `components/account_label.html` — первая волна; `accounts.py` — один план; `history.py` — два плана подряд (экран, затем CSV); `history_card.html` — до или вместе с админскими планами истории; `admin/includes/*` параллельно пользовательским; `type: tdd` — правило подписи, ячейка CSV, загрузчик карты, сканер гейта; остальное — `execute` с адресным тестом в том же плане до правки.

## No Analog Found

| Файл | Роль | Поток | Причина |
|---|---|---|---|
| Проход «нет `7311` в текстовых узлах и атрибутах вне объявленных адресов» (`tests/test_pages/test_account_label_sweep.py`, план 17-09) | test | request-response | Подобного прохода по отрисованному результату в дереве нет; идейный аналог — «защита на исполнении» Фазы 16 и `test_the_named_zero_of_the_backlog_is_not_a_broken_scanner` (`test_htmx_gates.py`). Использовать RESEARCH §7 п.6 |

## Metadata

**Analog search scope:** `app/services`, `app/pages`, `app/application/accounts`, `app/templates/components`, `app/templates/ads/includes`, `tests/test_services`, `tests/test_templates`, `tests/test_pages`, `tests/test_application`
**Files scanned:** ~25 (прочитано точечно, большие файлы — по диапазонам)
**Pattern extraction date:** 2026-11-20
