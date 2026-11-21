# Фаза 18: Ручная правка номера - карта образцов

**Составлено:** 2026-11-21
**Файлов:** 14 (новых 0, изменяемых 14, плюс новые тесты)
**Образцы найдены:** 14 / 14 (все пути проверены как отслеживаемые git; зеркал `.gsd` нет)

## Классификация файлов

| Файл | Роль | Поток данных | Образец | Качество |
|------|------|--------------|---------|----------|
| `app/pages/account_groups.py` (новый `account_phone_post`) | route | request-response, PRG/фрагмент | `app/pages/profile.py::profile_post` + `account_groups_toggle` | точный |
| `app/templates/account_groups/list.html` (шапка `data-acct-head`, якорь `#phone`) | шаблон | request-response | `app/templates/includes/profile_settings.html` | роль |
| новый включаемый шаблон формы номера (`account_groups/includes/phone_form.html`; имя на усмотрение) | шаблон | request-response | `includes/profile_settings.html` | точный |
| новый ответный шаблон успеха (шапка + OOB) | шаблон | фрагмент | `account_groups/partials/toggle_response.html`, `user_actions_response.html:48` | роль |
| `app/pages/notices.py` (`PHONE_SAVED`, `PHONE_CLEARED`) | config | реестр | `PROFILE_SAVED` (стр. 138, 291) | точный |
| `app/services/account_label.py` (`AccountRow`, `AccountLabel`, `row_of`, `label_of`, `build_labels`) | service | transform | он же | точный |
| `app/application/accounts/labels.py::load_account_rows` | service | CRUD (чтение) | он же | точный |
| `app/application/accounts/dto.py::SyncStatusView` | модель/DTO | transform | он же (поле `phone`) | точный |
| `app/templates/components/account_label.html` | компонент | transform | он же | точный |
| `accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html` | шаблон | request-response | соседняя ссылка «Настроить группы» | точный |
| `app/pages/history.py` (карта `account_id -> phone`) | route | CRUD (чтение) | он же | точный |
| `tests/test_pages/test_impersonation_gate.py` (`ALLOWED_ROUTES`, `MUTATING_ROUTE_COUNT` 49 -> 50) | тест | гейт | он же | точный |
| `tests/test_pages/test_htmx_post_pairs.py` (`_PairCase`) | тест | гейт | кейсы `PROFILE_POST` (1670-1695) | точный |
| новый `tests/test_pages/test_account_phone_form.py` | тест | request-response | `tests/test_pages/test_account_groups.py`, `tests/account_label_support.py::seed_account` | роль |

## Назначение образцов

### `app/pages/account_groups.py`, `account_phone_post`

**Образец 1: `app/pages/account_groups.py`** (импорты, стр. 15-42): уже есть `Form`, `respond`, `PostIdPath`, `id_in_column`, `label_of`, `row_of`, `load_account_rows`, `is_same_origin`. Добавить `from app.application.accounts.phone import set_manual_phone`, `from app.services.phone import PhoneError`, `respond_field_error`, `notices`.

**Владение** (стр. 122-132, `_load_owned_account`), вызывать так:
```python
account = await _load_owned_account(db, user, account_id)
if not account:
    # чужой == несуществующий (D-05)
```

**Сверка источника** (стр. 726-727, в `account_groups_delete`), ставить ВЫШЕ выборки аккаунта:
```python
if not is_same_origin(request):
    return Response(status_code=403)
```

**Сигнатура POST** (стр. 440-448, toggle): `request: Request, account_id: PostIdPath, phone: str = Form(""), db=Depends(get_db), settings=Depends(get_settings)`. Параметр `phone` с умолчанием `""` — как `timezone: str = Form("")` в `profile_post`, чтобы отсутствие поля шло веткой ошибки, а не 422 фреймворка. Зависимости `forbid_when_impersonating` НЕ ставить (D-06; в отличие от `profile_post`, стр. 77-84).

**Нет сессии / чужой / `LookupError`**: единый выход, адрес деградации один и тот же:
```python
if not user:
    return await respond(request, redirect="/login")
...
return await respond(request, redirect="/accounts")   # чужой и LookupError
```
ВАЖНО: гейт G-2 (`test_htmx_gates.py::test_no_converted_handler_builds_its_own_redirect`) краснит собственный `RedirectResponse`/литерал статуса 302 в теле обработчика, который зовёт `respond()`. Ни `RedirectResponse(`, ни `302` в теле не писать (ср. докстринг toggle, стр. 450+). `account_groups_page` (стр. 221-226) отвечает RedirectResponse, потому что `respond()` не зовёт; новый обработчик зовёт.

**Успех** (образец `profile_post`, стр. 124-152): коммит, нулярный async `_saved`, затем
```python
await respond(request, redirect=f"/accounts/{account_id}/groups", notice=notices.PHONE_SAVED, fragment=_saved)
```
Код уведомления выбирать по исходу: пустой/пробельный ввод -> `PHONE_CLEARED`, иначе `PHONE_SAVED`. Номер в `redirect` и в текст не класть (D-16).

**422** (стр. 154-190 `profile_post`):
```python
async def _page() -> HTMLResponse: ...   # страница целиком, status 422 через respond_field_error
async def _fragment() -> HTMLResponse: ... # тот же включаемый шаблон формы с error=PhoneError-текст и value=присланное
return await respond_field_error(request, page=_page, fragment=_fragment)
```
`respond_field_error(request, *, page, fragment)` — `app/pages/htmx.py:903`; код ошибки ставит она, адреса деградации нет. Текст ошибки брать из константы `PhoneError` (`app/services/phone.py`), не из присланного значения (D-03, PHONE-21). Контекст `_page` — тот, что строит `account_groups_page` (стр. 234-292); вынести сборку в общий помощник, а не копировать второй раз.

**Запись и перечитывание (D-14)**:
```python
try:
    await set_manual_phone(db, account.id, phone)   # без коммита, исключения: PhoneError, LookupError
except PhoneError: -> ветка 422 (откат не нужен: писатель падает до обращения к базе)
except LookupError: -> respond(request, redirect="/accounts")
await db.commit()
await db.refresh(account)                            # писатель идёт synchronize_session=False
rows = await load_account_rows(db, user.id)
acct_label = label_of(row_of(account), rows)
```
Докстринг обработчика обязан содержать запись: «пустой ввод на этом пути — очистка, не ошибка (D-09 Фазы 18); `PHONE_ERROR_BLANK` форма не показывает».

Журнал: только `account_id` и `phone_set=bool(phone.strip())` (D-16).

### Форма номера (включаемый шаблон)

**Образец: `app/templates/includes/profile_settings.html`** (конец файла):
```jinja
{% from "components/alert.html" import alert %}
{% from "components/button.html" import button %}
{% from "components/field.html" import select_field %}
{% from "components/form_wrapper.html" import form_wrapper %}
{% if error %}{{ alert(error) }}{% endif %}
{% call form_wrapper(action='/profile', target='#profile-settings', swap='innerHTML') %}
  <div data-form>
    {{ select_field(name="timezone", ...) }}
    {{ button('Сохранить', variant='primary') }}
  </div>
{% endcall %}
```
Заменить на `action='/accounts/{{ account_id }}/phone'` (посимвольно одинаков с `hx-post`, делает макрос), цель — контейнер шапки, `swap='innerHTML'`. Вместо `select_field` — поле `type="tel"` из `components/field.html` (посмотреть там текстовый макрос; ошибка под полем по D-03/D-13, а не `alert` сверху, если макрос поля умеет `error`). Ввод подаётся автоэкранированием (T-11-13): без `|safe` и `Markup`, в комментариях шаблона эти приёмы не называть (`test_no_unsafe_escaping` ищет по исходнику). `autocomplete="off"`, `maxlength` не ниже `MANUAL_INPUT_MAX_CHARS`+запас или без него, `id="phone"` как якорь D-12. Значение по умолчанию — `acct_label.phone_text` (форма показа), на 422 — присланное.

### Шапка `list.html` (стр. 50-57)
```jinja
<div data-acct-head>
  <div class="acct-head__id">
    <h2 class="acct-head__name">{{ account_label(acct_label, show_channel=true) }}</h2>
```
Форму вставить внутрь `data-acct-head`, обернув в контейнер с стабильным id для подмены. Успешный ответ с JS: фрагмент шапки + OOB-узел заголовка шелла. Образец OOB: `user_actions_response.html:48` (`<span hx-swap-oob="innerHTML:#…">`); `<title>` во фрагменте — `step_response.html`. Шапка и `<h2>` обновляются обязательно, `<title>` — на усмотрение. Оформление: счётчики `WRITE_FORM_PLACES`, пары `hx-post`/`action` пересчитать (D-08).

### `app/services/account_label.py` и `labels.py` (D-10)

Текущее: `AccountRow(NamedTuple): id, type, phone` (стр. 41-46), `AccountLabel(frozen slots): account_id, channel, phone_text, twin`, `row_of` (стр. 100-102), `label_of`, `build_labels` (стр. 105-131). Добавить в `AccountRow` четвёртое поле с умолчанием (`phone_is_manual: bool = False`), чтобы существующие вызовы `AccountRow(id, type, phone)` и тесты не краснели; в `AccountLabel` — поле с умолчанием в конце. `row_of`: `getattr(account, "phone_is_manual", False)`. `_twin_key` НЕ менять (D-10: признак вне ключа). Номер при `phone_text is None` пометки не несёт (CHECK `ck_messenger_accounts_manual_requires_phone`). `plain`/`plain_with_id` НЕ менять (плоские формы без пометки). Пометка в `AccountLabel.text` не попадает.

`labels.py::load_account_rows` (стр. 40-47):
```python
select(MessengerAccount.id, MessengerAccount.type, MessengerAccount.phone).where(MessengerAccount.user_id == user_id)
... [AccountRow(*row) for row in result.all()]
```
Добавить четвёртую колонку `MessengerAccount.phone_is_manual`; распаковка `*row` подхватит.

### `components/account_label.html` (макрос, стр. 33-39)
```jinja
<span class="acct-label__text mono {{ 'mono--muted' if label.phone_text is none else 'mono--bright' }}">{{ label.text }}</span>
{%- if with_twin_id and label.twin %} {{ account_id_mark(label.account_id) }}{% endif -%}
```
Между ними добавить `{% if label.phone_manual %} <span class="acct-label__manual mono mono--muted">указан вручную</span>{% endif %}`. Только `<span>` (строку воркера админки тест режет по первому `</div>`). Сохранить `data-account-label`. Тест раскладки: `tests/test_pages/test_responsive_markup.py` (17-09). Если новый класс — добавить CSS рядом с `acct-label__id`.

### `SyncStatusView` (`app/application/accounts/dto.py`, поле `phone` на стр. 35)
Рядом добавить `phone_is_manual: bool = False`; заполнитель DTO найти по `SyncStatusView(` (grep) и передать колонку. Подпись карточки опроса — `account_label` с `labels_for`/`row_of`, который читает `getattr`.

### Карточки аккаунтов и ссылка
Рядом с «Настроить группы» (`/accounts/{id}/groups`) на трёх формах добавить `<a href="/accounts/{{ id }}/groups#phone">{{ 'Изменить' if phone else 'Указать номер' }}</a>`. Ссылка GET, форма не создаётся (счётчик `WRITE_FORM_PLACES` её не затрагивает).

### `app/pages/history.py`
Карта `account_id -> phone` (D-18 Фазы 17): расширить выборку признаком в ТОМ ЖЕ запросе, не вторым.

### `app/pages/notices.py`
Код (стр. 137-139) и запись (стр. 291):
```python
PROFILE_SAVED = "profile_saved"
Notice(PROFILE_SAVED, "Настройки сохранены.", "success"),
```
Добавить `PHONE_SAVED = "phone_saved"` («Номер сохранён.»), `PHONE_CLEARED = "phone_cleared"` («Номер удалён.»), `"success"`. Тексты без номера. Реестр имеет собственные гейты полноты — прогнать.

### Тесты

**`test_impersonation_gate.py`**: `ALLOWED_ROUTES` (стр. 217+), формат «ключ -> причина»:
```python
"app/pages/account_groups.py::account_phone_post": "номер — подпись, а не учётные данные; на доставку не влияет",
```
`MUTATING_ROUTE_COUNT` 49 -> 50; `MUTATING_MODULE_COUNT` не меняется (модуль уже считается). Добавить тест, что под имперсонацией правка проходит (D-06).

**`test_htmx_post_pairs.py`**: по образцу `_PairCase` стр. 1670-1695 и `_arrange_profile_save` (стр. 582-590, возвращает `_Arranged(url=..., data={...})`): два кейса — успех (FRAGMENT, `landing="/accounts/{id}/groups?notice=" + notices.PHONE_SAVED`, `fragment_mark`) и нет сессии (`landing="/login"`, LOCATION). POST идёт на литеральный адрес, не на собранный. Обновить `PAIRED_302_ASSERTIONS_DECLARED`, `FRAGMENT_RESPONSE_HANDLERS_DECLARED`, `PUSH_URL_DECISIONS_DECLARED` (у формы нет записи адреса в историю, как у профиля D-13).

**Новый тест**: `tests/account_label_support.py::seed_account(session, user_id, type_, *, phone=..., ...)` (стр. 42-67) — засев. Сценарии: ручной -> очистка -> `fill_reported_phone` даёт `PhoneWrite.WRITTEN` и пометки нет; 422 сохраняет ввод и текст не содержит ввода; чужой аккаунт == несуществующий; `is_same_origin` -> 403; дубликат номера принимается; пометка найдена по `data-account-label`, а не подстрокой; прогнать гейты номера Фазы 16.

## Общие паттерны

- **Чужой == несуществующий:** `_load_owned_account` + единый ответ (стр. 224-226, комментарий о карте идентификаторов).
- **Единый выход ответа:** только `respond()` / `respond_field_error()`, без собственного редиректа (G-2).
- **Приватность (PHONE-21):** номер не в URL, не в уведомлении, не в журнале, не в тексте ошибки.
- **Автоэкранирование:** ввод и подпись только через Jinja, без разметки из Python (`MARKUP_BUILDERS = 0`).
- **Писатель один:** только `set_manual_phone`; присваивания `account.phone = ...` краснят `phone_guard` и гейт единственного писателя.
- **Транзакция:** маршрут коммитит после писателя, затем `refresh`.

## Нет образца

Нет: образец найден для каждого файла. Частично нового: OOB-подмена заголовка шелла и шапки одним ответом (составить из `toggle_response.html` + `user_actions_response.html:48`).

## Метаданные

**Область поиска:** `app/pages`, `app/services`, `app/application/accounts`, `app/templates`, `tests/test_pages`, `tests/account_label_support.py`
**Подход:** graphify query, затем чтение строк
**Дата:** 2026-11-21
